from __future__ import annotations

import unittest
from dataclasses import replace
from typing import Any, Dict

from mindmarionette import (
    ActionHistory,
    ContextStateManager,
    FallbackStrategy,
    HealingRequest,
    LocatorResult,
    RetryPolicy,
    SelfHealingEngine,
    SelfHealingError,
)


class FlakyLocator:
    def locate(self, request: HealingRequest, attempt: int, context: Dict[str, Any]) -> LocatorResult:
        measurement = request.metadata.get("measurement", 0.02)
        plan = {
            "attempt": attempt,
            "force_failure": request.metadata.get("force_failure", False),
        }
        metadata = {"attempt": attempt, "source": "flaky"}
        return LocatorResult(plan=plan, metadata=metadata, measurement=measurement)


class FlakyExecutor:
    def __init__(self) -> None:
        self.calls: list[Dict[str, Any]] = []

    def execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append(plan)
        if plan.get("force_failure"):
            raise RuntimeError("simulated executor failure")
        return {"status": "ok", "attempt": plan["attempt"]}


class DriftAwareLocator:
    def __init__(self, measurement: float) -> None:
        self._measurement = measurement

    def locate(self, request: HealingRequest, attempt: int, context: Dict[str, Any]) -> LocatorResult:
        metadata = {"attempt": attempt, "source": "drift"}
        plan = {"attempt": attempt}
        return LocatorResult(plan=plan, metadata=metadata, measurement=self._measurement)


class AlwaysFailExecutor:
    def execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> None:
        raise RuntimeError("persistent failure")


class AlwaysSucceedsExecutor:
    def execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "ok", "attempt": plan["attempt"]}


class SelfHealingEngineTests(unittest.TestCase):
    def test_recovers_with_fallback_and_dependency_restart(self) -> None:
        history = ActionHistory()
        context_manager = ContextStateManager()
        executor = FlakyExecutor()
        restart_sequence: list[str] = []
        engine = SelfHealingEngine(
            locator=FlakyLocator(),
            executor=executor,
            context_manager=context_manager,
            retry_policy=RetryPolicy(max_attempts=3),
            history=history,
            dependency_restarters={"ui-service": lambda: restart_sequence.append("ui-service")},
        )

        def relax_strategy(request: HealingRequest, *_: Any) -> HealingRequest:
            metadata = dict(request.metadata)
            metadata["force_failure"] = False
            return replace(request, metadata=metadata)

        request = HealingRequest(
            scenario_id="scenario-A",
            target="button",
            metadata={"force_failure": True, "measurement": 0.01},
            fallback_strategies=[FallbackStrategy(name="relax", handler=relax_strategy)],
            dependencies=("ui-service",),
        )

        result = engine.run(request)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(restart_sequence, ["ui-service"])
        self.assertGreaterEqual(len(executor.calls), 2)

        telemetry_kinds = [entry["kind"] for entry in engine.telemetry.as_dict()]
        self.assertIn("fallback_applied", telemetry_kinds)
        self.assertIn("healing_success", telemetry_kinds)
        self.assertIn("dependency_restarted", telemetry_kinds)

        audit_events = [entry["event"] for entry in context_manager.context["self_healing"]["audit_log"]]
        self.assertIn("fallback_applied", audit_events)
        self.assertIn("dependency_restarted", audit_events)
        self.assertIn("healing_success", audit_events)

        measurements = history.recent_measurements("scenario-A", limit=5)
        self.assertTrue(measurements)

    def test_ui_drift_detection_records_telemetry(self) -> None:
        history = ActionHistory()
        history.record_outcome("scenario-B", "success", 0.02, {})
        history.record_outcome("scenario-B", "success", 0.03, {})

        context_manager = ContextStateManager()
        engine = SelfHealingEngine(
            locator=DriftAwareLocator(measurement=0.12),
            executor=AlwaysSucceedsExecutor(),
            context_manager=context_manager,
            history=history,
            retry_policy=RetryPolicy(max_attempts=1),
        )

        request = HealingRequest(scenario_id="scenario-B", target="panel")
        engine.run(request)

        telemetry_kinds = [entry["kind"] for entry in engine.telemetry.as_dict()]
        self.assertIn("ui_drift_detected", telemetry_kinds)

        audit_events = [entry["event"] for entry in context_manager.context["self_healing"]["audit_log"]]
        self.assertIn("ui_drift_detected", audit_events)

    def test_exhausted_retries_raise_and_record_failure(self) -> None:
        history = ActionHistory()
        context_manager = ContextStateManager()
        engine = SelfHealingEngine(
            locator=DriftAwareLocator(measurement=0.05),
            executor=AlwaysFailExecutor(),
            context_manager=context_manager,
            history=history,
            retry_policy=RetryPolicy(max_attempts=2),
        )

        request = HealingRequest(scenario_id="scenario-C", target="menu")

        with self.assertRaises(SelfHealingError) as captured:
            engine.run(request)

        error = captured.exception
        self.assertEqual(error.scenario_id, "scenario-C")
        self.assertIsNotNone(error.last_error)

        telemetry_kinds = [entry["kind"] for entry in engine.telemetry.as_dict()]
        self.assertIn("recovery_failed", telemetry_kinds)
        self.assertIn("replan_applied", telemetry_kinds)

        audit_events = [entry["event"] for entry in context_manager.context["self_healing"]["audit_log"]]
        self.assertIn("recovery_failed", audit_events)
        self.assertIn("replan_applied", audit_events)

        measurements = history.recent_measurements("scenario-C", limit=5)
        self.assertEqual(measurements, [0.05, 0.05])


if __name__ == "__main__":
    unittest.main()
