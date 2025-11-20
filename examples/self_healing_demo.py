#!/usr/bin/env python3
"""
MindMarionette Self-Healing Engine - Comprehensive Demo

This demo showcases the self-healing capabilities:
1. Automated retry policies with configurable delays
2. Historical analysis and UI drift detection
3. Fallback strategies for progressive recovery
4. Dependency restart coordination
5. Audit logging with timestamps
6. Telemetry exposing healing decisions and outcomes
"""

import json
import random
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

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


class SimulatedUILocator:
    """Simulates a locator with intermittent failures and drift scenarios."""
    
    def __init__(self, failure_rate: float = 0.3) -> None:
        self._failure_rate = failure_rate
        self._attempts_by_scenario: Dict[str, int] = {}
    
    def locate(self, request: HealingRequest, attempt: int, context: Dict[str, Any]) -> LocatorResult:
        scenario_id = request.scenario_id
        self._attempts_by_scenario.setdefault(scenario_id, 0)
        self._attempts_by_scenario[scenario_id] += 1
        
        force_success = request.metadata.get("force_success", False)
        if force_success or random.random() > self._failure_rate:
            measurement = request.metadata.get("measurement", random.uniform(0.01, 0.08))
            plan = {
                "locator": "css",
                "selector": request.metadata.get("selector", f"#{request.target}"),
                "attempt": attempt,
                "scenario_id": scenario_id,
            }
            metadata = {
                "locator_type": "css",
                "attempt": attempt,
                "total_attempts": self._attempts_by_scenario[scenario_id],
            }
            return LocatorResult(plan=plan, metadata=metadata, measurement=measurement)
        else:
            raise RuntimeError(f"Locator failed to find '{request.target}' (attempt {attempt})")


class SimulatedActionExecutor:
    """Simulates action execution with occasional failures."""
    
    def __init__(self, success_rate: float = 0.7) -> None:
        self._success_rate = success_rate
        self._execution_history: List[Dict[str, Any]] = []
    
    def execute(self, plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        self._execution_history.append(plan)
        
        if random.random() < self._success_rate:
            return {
                "status": "executed",
                "selector": plan.get("selector"),
                "attempt": plan.get("attempt"),
                "scenario_id": plan.get("scenario_id"),
            }
        else:
            raise RuntimeError(f"Executor failed on selector {plan.get('selector')}")
    
    @property
    def execution_count(self) -> int:
        return len(self._execution_history)


def create_relaxed_selector_strategy() -> FallbackStrategy:
    """Strategy that relaxes the CSS selector to a more generic form."""
    
    def handler(request: HealingRequest, history: ActionHistory, context: Dict[str, Any]) -> HealingRequest:
        metadata = dict(request.metadata)
        current_selector = metadata.get("selector", f"#{request.target}")
        
        if "#" in current_selector:
            metadata["selector"] = f".{request.target}"
        elif "." in current_selector:
            metadata["selector"] = request.target
        else:
            metadata["selector"] = "*"
        
        return replace(request, metadata=metadata)
    
    return FallbackStrategy(name="relax_selector", handler=handler)


def create_force_success_strategy() -> FallbackStrategy:
    """Strategy that forces success after previous failures."""
    
    def handler(request: HealingRequest, history: ActionHistory, context: Dict[str, Any]) -> HealingRequest:
        metadata = dict(request.metadata)
        metadata["force_success"] = True
        return replace(request, metadata=metadata)
    
    return FallbackStrategy(name="force_success", handler=handler)


def print_banner(text: str) -> None:
    print(f"\n{'=' * 80}")
    print(f"{text:^80}")
    print(f"{'=' * 80}\n")


def print_section(text: str) -> None:
    print(f"\n{'-' * 80}")
    print(f"  {text}")
    print(f"{'-' * 80}\n")


def demo_basic_retry_with_recovery() -> None:
    """Demonstrate basic retry with eventual success."""
    
    print_section("Demo 1: Basic Retry with Recovery")
    
    random.seed(42)
    locator = SimulatedUILocator(failure_rate=0.6)
    executor = SimulatedActionExecutor(success_rate=0.9)
    context_manager = ContextStateManager()
    history = ActionHistory()
    
    engine = SelfHealingEngine(
        locator=locator,
        executor=executor,
        context_manager=context_manager,
        retry_policy=RetryPolicy(max_attempts=5, delays=(0.1, 0.2, 0.5)),
        history=history,
    )
    
    request = HealingRequest(
        scenario_id="login_button",
        target="login-btn",
        metadata={"selector": "#login-btn", "measurement": 0.02},
    )
    
    try:
        result = engine.run(request)
        print(f"✓ Successfully executed action: {result}")
        print(f"  Total executor calls: {executor.execution_count}")
    except SelfHealingError as e:
        print(f"✗ Recovery failed: {e}")
    
    print("\nTelemetry Summary:")
    telemetry = engine.telemetry.as_dict()
    for event in telemetry[-5:]:
        print(f"  [{event['kind']}] {event['details']}")


def demo_fallback_strategies() -> None:
    """Demonstrate fallback strategies with progressive relaxation."""
    
    print_section("Demo 2: Fallback Strategies")
    
    random.seed(123)
    locator = SimulatedUILocator(failure_rate=0.8)
    executor = SimulatedActionExecutor(success_rate=0.6)
    context_manager = ContextStateManager()
    history = ActionHistory()
    
    engine = SelfHealingEngine(
        locator=locator,
        executor=executor,
        context_manager=context_manager,
        retry_policy=RetryPolicy(max_attempts=4),
        history=history,
    )
    
    request = HealingRequest(
        scenario_id="submit_form",
        target="submit",
        metadata={"selector": "#submit-button", "measurement": 0.03},
        fallback_strategies=[
            create_relaxed_selector_strategy(),
            create_force_success_strategy(),
        ],
    )
    
    try:
        result = engine.run(request)
        print(f"✓ Successfully executed with fallback: {result}")
    except SelfHealingError as e:
        print(f"✗ All fallbacks exhausted: {e}")
    
    audit_log = context_manager.context["self_healing"]["audit_log"]
    print(f"\nAudit Log ({len(audit_log)} entries):")
    for entry in audit_log[-6:]:
        print(f"  [{entry['event']}] {entry.get('strategy', entry.get('scenario_id', 'N/A'))}")


def demo_ui_drift_detection() -> None:
    """Demonstrate UI drift detection with historical analysis."""
    
    print_section("Demo 3: UI Drift Detection")
    
    history = ActionHistory()
    history.record_outcome("dashboard_panel", "success", 0.02, {"component": "panel"})
    history.record_outcome("dashboard_panel", "success", 0.025, {"component": "panel"})
    history.record_outcome("dashboard_panel", "success", 0.03, {"component": "panel"})
    
    class DriftLocator:
        def locate(self, request: HealingRequest, attempt: int, context: Dict[str, Any]) -> LocatorResult:
            measurement = request.metadata.get("measurement", 0.15)
            plan = {"selector": "#dashboard", "attempt": attempt}
            metadata = {"drift_test": True}
            return LocatorResult(plan=plan, metadata=metadata, measurement=measurement)
    
    context_manager = ContextStateManager()
    executor = SimulatedActionExecutor(success_rate=1.0)
    
    engine = SelfHealingEngine(
        locator=DriftLocator(),
        executor=executor,
        context_manager=context_manager,
        retry_policy=RetryPolicy(max_attempts=1),
        history=history,
    )
    
    request = HealingRequest(
        scenario_id="dashboard_panel",
        target="panel",
        metadata={"measurement": 0.15},
    )
    
    result = engine.run(request)
    print(f"✓ Execution completed: {result}")
    
    drift_events = [e for e in engine.telemetry.as_dict() if e["kind"] == "ui_drift_detected"]
    if drift_events:
        print(f"\n⚠ UI Drift Detected:")
        for event in drift_events:
            print(f"  Measurement: {event['details']['measurement']:.4f}")
            print(f"  Recent baseline: ~0.025")
            print(f"  Deviation threshold exceeded!")
    
    measurements = history.recent_measurements("dashboard_panel", limit=10)
    print(f"\nHistorical measurements: {[f'{m:.4f}' for m in measurements]}")


def demo_dependency_restarts() -> None:
    """Demonstrate dependency restart coordination."""
    
    print_section("Demo 4: Dependency Restarts")
    
    restart_log: List[str] = []
    
    def restart_ui_service() -> None:
        restart_log.append("ui-service restarted")
    
    def restart_database() -> None:
        restart_log.append("database connection reset")
    
    random.seed(999)
    locator = SimulatedUILocator(failure_rate=0.9)
    executor = SimulatedActionExecutor(success_rate=0.5)
    context_manager = ContextStateManager()
    history = ActionHistory()
    
    engine = SelfHealingEngine(
        locator=locator,
        executor=executor,
        context_manager=context_manager,
        retry_policy=RetryPolicy(max_attempts=4),
        history=history,
        dependency_restarters={
            "ui-service": restart_ui_service,
            "database": restart_database,
        },
    )
    
    request = HealingRequest(
        scenario_id="user_profile",
        target="profile-btn",
        metadata={"selector": "#profile", "force_success": True, "measurement": 0.04},
        dependencies=("ui-service", "database"),
        fallback_strategies=[create_force_success_strategy()],
    )
    
    try:
        result = engine.run(request)
        print(f"✓ Execution successful: {result}")
    except SelfHealingError as e:
        print(f"✗ Recovery failed: {e}")
    
    print(f"\nDependency Restart Log:")
    for entry in restart_log:
        print(f"  - {entry}")
    
    summary = engine.telemetry_summary()
    print(f"\nRestart counts: {summary['dependency_restarts']}")


def demo_exhaustive_failure() -> None:
    """Demonstrate exhaustive failure with full telemetry."""
    
    print_section("Demo 5: Exhaustive Failure")
    
    class AlwaysFailLocator:
        def locate(self, request: HealingRequest, attempt: int, context: Dict[str, Any]) -> LocatorResult:
            raise RuntimeError("Locator consistently fails")
    
    context_manager = ContextStateManager()
    history = ActionHistory()
    executor = SimulatedActionExecutor(success_rate=1.0)
    
    engine = SelfHealingEngine(
        locator=AlwaysFailLocator(),
        executor=executor,
        context_manager=context_manager,
        retry_policy=RetryPolicy(max_attempts=3),
        history=history,
    )
    
    request = HealingRequest(
        scenario_id="broken_element",
        target="missing",
        metadata={"measurement": 0.0},
    )
    
    try:
        engine.run(request)
        print("✗ Unexpected success")
    except SelfHealingError as e:
        print(f"✓ Expected failure caught: {e.scenario_id}")
        print(f"  Last error: {type(e.last_error).__name__}: {e.last_error}")
    
    print("\nFull Telemetry:")
    for event in engine.telemetry.as_dict():
        print(f"  [{event['timestamp']}] {event['kind']}: {event['details']}")
    
    audit_log = context_manager.context["self_healing"]["audit_log"]
    print(f"\nAudit Log ({len(audit_log)} entries):")
    for entry in audit_log:
        print(f"  [{entry['timestamp']}] {entry['event']}")


def export_telemetry_report(output_dir: Path) -> None:
    """Export comprehensive telemetry report."""
    
    print_section("Exporting Telemetry Report")
    
    random.seed(777)
    locator = SimulatedUILocator(failure_rate=0.5)
    executor = SimulatedActionExecutor(success_rate=0.8)
    context_manager = ContextStateManager()
    history = ActionHistory()
    
    engine = SelfHealingEngine(
        locator=locator,
        executor=executor,
        context_manager=context_manager,
        retry_policy=RetryPolicy(max_attempts=3, delays=(0.5, 1.0)),
        history=history,
    )
    
    scenarios = [
        HealingRequest(
            scenario_id=f"scenario_{i}",
            target=f"element-{i}",
            metadata={"selector": f"#elem-{i}", "measurement": random.uniform(0.01, 0.05)},
            fallback_strategies=[create_relaxed_selector_strategy()],
        )
        for i in range(5)
    ]
    
    results = []
    for request in scenarios:
        try:
            result = engine.run(request)
            results.append({"scenario": request.scenario_id, "status": "success", "result": result})
        except SelfHealingError as e:
            results.append({"scenario": request.scenario_id, "status": "failed", "error": str(e)})
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    telemetry_file = output_dir / "self_healing_telemetry.json"
    with open(telemetry_file, "w") as f:
        json.dump(engine.telemetry_summary(), f, indent=2)
    
    audit_file = output_dir / "self_healing_audit_log.json"
    audit_log = context_manager.context["self_healing"]["audit_log"]
    with open(audit_file, "w") as f:
        json.dump(audit_log, f, indent=2)
    
    results_file = output_dir / "self_healing_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Telemetry exported to: {telemetry_file}")
    print(f"✓ Audit log exported to: {audit_file}")
    print(f"✓ Results exported to: {results_file}")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\nSummary: {success_count}/{len(results)} scenarios succeeded")


def main() -> None:
    print_banner("🔧 MindMarionette Self-Healing Engine - Comprehensive Demo")
    
    print("This demo showcases automated recovery with:")
    print("  • Retry policies with configurable delays")
    print("  • Historical analysis and UI drift detection")
    print("  • Fallback strategies for progressive recovery")
    print("  • Dependency restart coordination")
    print("  • Comprehensive audit logging")
    print("  • Full telemetry of healing decisions and outcomes")
    
    demo_basic_retry_with_recovery()
    demo_fallback_strategies()
    demo_ui_drift_detection()
    demo_dependency_restarts()
    demo_exhaustive_failure()
    
    output_dir = Path(__file__).resolve().parent / "demo_self_healing_output"
    export_telemetry_report(output_dir)
    
    print_banner("Demo Complete!")
    print("\nAll simulated failure scenarios demonstrated self-healing capabilities.")
    print("Telemetry and audit logs document all healing decisions and outcomes.")


if __name__ == "__main__":
    main()
