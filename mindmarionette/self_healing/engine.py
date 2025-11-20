from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Callable, Deque, Dict, List, Mapping, Optional, Protocol, Sequence


class SelfHealingError(RuntimeError):
    """Raised when the self-healing engine exhausts all recovery attempts."""

    def __init__(self, scenario_id: str, last_error: Exception | None) -> None:
        message = f"Self-healing exhausted for '{scenario_id}'"
        if last_error is not None:
            message = f"{message}: {last_error}"
        super().__init__(message)
        self.scenario_id = scenario_id
        self.last_error = last_error


@dataclass(frozen=True)
class LocatorResult:
    """Represents the outcome of a locator pass prior to executing an action."""

    plan: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    measurement: Optional[float] = None


class ElementLocator(Protocol):
    """Protocol for components capable of resolving locator plans."""

    def locate(self, request: "HealingRequest", attempt: int, context: Dict[str, Any]) -> LocatorResult:
        ...


class ActionExecutor(Protocol):
    """Protocol for components capable of executing action plans."""

    def execute(self, plan: Any, context: Dict[str, Any]) -> Any:
        ...


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration controlling automated retry behaviour."""

    max_attempts: int = 3
    delays: Sequence[float] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("RetryPolicy.max_attempts must be at least 1")

    def should_retry(self, attempt: int) -> bool:
        """Return True when another attempt should be scheduled after ``attempt``."""

        return attempt < self.max_attempts

    def delay_for(self, next_attempt: int) -> Optional[float]:
        """Return the delay (if any) that should precede ``next_attempt``."""

        if not self.delays:
            return None
        # The first retry happens at attempt 2, hence ``next_attempt - 2``.
        index = max(0, min(next_attempt - 2, len(self.delays) - 1))
        return self.delays[index]


@dataclass(frozen=True)
class FallbackStrategy:
    """Fallback strategy invoked between attempts when recovery is required."""

    name: str
    handler: Callable[["HealingRequest", "ActionHistory", Dict[str, Any]], "HealingRequest" | None]

    def apply(
        self,
        request: "HealingRequest",
        history: "ActionHistory",
        context: Dict[str, Any],
    ) -> "HealingRequest":
        updated = self.handler(request, history, context)
        return request if updated is None else updated


@dataclass
class HealingRequest:
    """Encapsulates a recovery job executed by the self-healing engine."""

    scenario_id: str
    target: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    fallback_strategies: Sequence[FallbackStrategy] = field(default_factory=tuple)
    dependencies: Sequence[str] = field(default_factory=tuple)


@dataclass(frozen=True)
class HistoryEntry:
    status: str
    measurement: Optional[float]
    metadata: Dict[str, Any]
    timestamp: datetime


class ActionHistory:
    """Tracks historical outcomes to support drift detection and re-planning."""

    def __init__(self, max_entries: int = 50) -> None:
        self._max_entries = max_entries
        self._records: Dict[str, Deque[HistoryEntry]] = defaultdict(self._deque_factory)

    def _deque_factory(self) -> Deque[HistoryEntry]:
        return deque(maxlen=self._max_entries)

    def record_outcome(
        self,
        scenario_id: str,
        status: str,
        measurement: Optional[float],
        metadata: Dict[str, Any],
    ) -> None:
        entry = HistoryEntry(
            status=status,
            measurement=self._coerce_measurement(measurement),
            metadata=dict(metadata),
            timestamp=datetime.now(timezone.utc),
        )
        self._records[scenario_id].append(entry)

    def recent_measurements(self, scenario_id: str, limit: int) -> List[float]:
        measurements: List[float] = []
        for entry in reversed(self._records.get(scenario_id, [])):
            if entry.measurement is not None:
                measurements.append(entry.measurement)
            if len(measurements) >= limit:
                break
        return list(reversed(measurements))

    def detect_ui_drift(
        self,
        scenario_id: str,
        measurement: Optional[float],
        *,
        window: int = 3,
        tolerance: float = 0.05,
    ) -> bool:
        value = self._coerce_measurement(measurement)
        if value is None or window < 2:
            return False

        history = self.recent_measurements(scenario_id, limit=window - 1)
        if len(history) < window - 1:
            return False

        baseline = sum(history) / len(history)
        if baseline == 0:
            return value > tolerance
        return value > baseline + tolerance

    def _coerce_measurement(self, measurement: Optional[float]) -> Optional[float]:
        if measurement is None:
            return None
        try:
            return float(measurement)
        except (TypeError, ValueError):
            return None


@dataclass(frozen=True)
class HealingEvent:
    timestamp: datetime
    kind: str
    details: Dict[str, Any]


class HealingTelemetry:
    """Captures decisions and outcomes produced by the self-healing engine."""

    def __init__(self) -> None:
        self._events: List[HealingEvent] = []

    def record(self, kind: str, **details: Any) -> None:
        event = HealingEvent(datetime.now(timezone.utc), kind, dict(details))
        self._events.append(event)

    def as_dict(self) -> List[Dict[str, Any]]:
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "kind": event.kind,
                "details": event.details,
            }
            for event in self._events
        ]


class ContextStateManager:
    """Maintains orchestrator context with audit logging support."""

    def __init__(self, context: Optional[Dict[str, Any]] = None) -> None:
        self._context: Dict[str, Any] = context if context is not None else {}
        self._context.setdefault("self_healing", {"audit_log": [], "telemetry": {}})

    @property
    def context(self) -> Dict[str, Any]:
        return self._context

    def append_audit_log(self, entry: Dict[str, Any]) -> None:
        payload = dict(entry)
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        self._context.setdefault("self_healing", {}).setdefault("audit_log", []).append(payload)

    def set_telemetry(self, telemetry: Mapping[str, Any]) -> None:
        self._context.setdefault("self_healing", {})["telemetry"] = dict(telemetry)


class DependencyManager:
    """Coordinates restart hooks for dependent components."""

    def __init__(self, restarters: Mapping[str, Callable[[], None]] | None = None) -> None:
        self._restarters: Dict[str, Callable[[], None]] = dict(restarters or {})
        self._restart_counts: Dict[str, int] = defaultdict(int)

    def restart(self, name: str) -> bool:
        self._restart_counts[name] += 1
        callback = self._restarters.get(name)
        if callback is None:
            return False
        callback()
        return True

    def counts(self) -> Dict[str, int]:
        return dict(self._restart_counts)


class SelfHealingEngine:
    """Coordinates locator, executor, and context for resilient scenario execution."""

    def __init__(
        self,
        locator: ElementLocator,
        executor: ActionExecutor,
        *,
        context_manager: Optional[ContextStateManager] = None,
        retry_policy: Optional[RetryPolicy] = None,
        history: Optional[ActionHistory] = None,
        telemetry: Optional[HealingTelemetry] = None,
        dependency_restarters: Mapping[str, Callable[[], None]] | None = None,
    ) -> None:
        self._locator = locator
        self._executor = executor
        self._context_manager = context_manager or ContextStateManager()
        self._retry_policy = retry_policy or RetryPolicy()
        self._history = history or ActionHistory()
        self._telemetry = telemetry or HealingTelemetry()
        self._dependencies = DependencyManager(dependency_restarters)

    @property
    def telemetry(self) -> HealingTelemetry:
        return self._telemetry

    @property
    def history(self) -> ActionHistory:
        return self._history

    @property
    def context(self) -> Dict[str, Any]:
        return self._context_manager.context

    @property
    def retry_policy(self) -> RetryPolicy:
        return self._retry_policy

    def telemetry_summary(self) -> Dict[str, Any]:
        return {
            "events": self._telemetry.as_dict(),
            "dependency_restarts": self._dependencies.counts(),
        }

    def run(self, request: HealingRequest) -> Any:
        fallback_queue: Deque[FallbackStrategy] = deque(request.fallback_strategies)
        current_request = request
        last_error: Optional[Exception] = None

        for attempt in range(1, self._retry_policy.max_attempts + 1):
            self._telemetry.record(
                "attempt_started",
                scenario_id=current_request.scenario_id,
                attempt=attempt,
            )
            locator_result: Optional[LocatorResult] = None
            try:
                locator_result = self._locator.locate(current_request, attempt, self._context_manager.context)
            except Exception as exc:  # pragma: no cover - defensive branching
                last_error = exc
                self._telemetry.record(
                    "locator_failed",
                    scenario_id=current_request.scenario_id,
                    attempt=attempt,
                    error=repr(exc),
                )
                self._history.record_outcome(
                    current_request.scenario_id,
                    status="failure",
                    measurement=None,
                    metadata={"stage": "locator", "attempt": attempt},
                )
                self._context_manager.append_audit_log(
                    {
                        "event": "locator_failed",
                        "scenario_id": current_request.scenario_id,
                        "attempt": attempt,
                        "error": str(exc),
                    }
                )
                if self._retry_policy.should_retry(attempt):
                    current_request = self._prepare_next_request(current_request, attempt, fallback_queue)
                    self._update_context_telemetry()
                    continue
                break

            measurement = locator_result.measurement
            metadata = dict(locator_result.metadata)
            if self._history.detect_ui_drift(current_request.scenario_id, measurement):
                self._telemetry.record(
                    "ui_drift_detected",
                    scenario_id=current_request.scenario_id,
                    attempt=attempt,
                    measurement=measurement,
                )
                self._context_manager.append_audit_log(
                    {
                        "event": "ui_drift_detected",
                        "scenario_id": current_request.scenario_id,
                        "attempt": attempt,
                        "measurement": measurement,
                    }
                )

            try:
                execution_result = self._executor.execute(locator_result.plan, self._context_manager.context)
            except Exception as exc:  # pragma: no cover - defensive branching
                last_error = exc
                failure_metadata = dict(metadata)
                failure_metadata.update({"stage": "executor", "attempt": attempt})
                self._telemetry.record(
                    "executor_failed",
                    scenario_id=current_request.scenario_id,
                    attempt=attempt,
                    error=repr(exc),
                )
                self._history.record_outcome(
                    current_request.scenario_id,
                    status="failure",
                    measurement=measurement,
                    metadata=failure_metadata,
                )
                self._context_manager.append_audit_log(
                    {
                        "event": "executor_failed",
                        "scenario_id": current_request.scenario_id,
                        "attempt": attempt,
                        "error": str(exc),
                    }
                )
                if self._retry_policy.should_retry(attempt):
                    current_request = self._prepare_next_request(current_request, attempt, fallback_queue)
                    self._update_context_telemetry()
                    continue
                break

            success_metadata = dict(metadata)
            success_metadata.update({"stage": "executor", "attempt": attempt})
            self._history.record_outcome(
                current_request.scenario_id,
                status="success",
                measurement=measurement,
                metadata=success_metadata,
            )
            self._telemetry.record(
                "healing_success",
                scenario_id=current_request.scenario_id,
                attempt=attempt,
            )
            self._context_manager.append_audit_log(
                {
                    "event": "healing_success",
                    "scenario_id": current_request.scenario_id,
                    "attempt": attempt,
                }
            )
            self._update_context_telemetry()
            return execution_result

        self._telemetry.record(
            "recovery_failed",
            scenario_id=request.scenario_id,
            attempts=self._retry_policy.max_attempts,
            error=repr(last_error) if last_error else None,
        )
        self._context_manager.append_audit_log(
            {
                "event": "recovery_failed",
                "scenario_id": request.scenario_id,
                "attempts": self._retry_policy.max_attempts,
                "error": str(last_error) if last_error else None,
            }
        )
        self._update_context_telemetry()
        raise SelfHealingError(request.scenario_id, last_error)

    def _prepare_next_request(
        self,
        request: HealingRequest,
        attempt: int,
        fallback_queue: Deque[FallbackStrategy],
    ) -> HealingRequest:
        next_attempt = attempt + 1
        self._maybe_restart_dependencies(request, next_attempt)

        delay = self._retry_policy.delay_for(next_attempt)
        if delay is not None:
            self._telemetry.record(
                "retry_scheduled",
                scenario_id=request.scenario_id,
                attempt=next_attempt,
                delay=delay,
            )
            self._context_manager.append_audit_log(
                {
                    "event": "retry_scheduled",
                    "scenario_id": request.scenario_id,
                    "attempt": next_attempt,
                    "delay": delay,
                }
            )

        if fallback_queue:
            strategy = fallback_queue.popleft()
            self._telemetry.record(
                "fallback_considered",
                scenario_id=request.scenario_id,
                attempt=next_attempt,
                strategy=strategy.name,
            )
            updated_request = strategy.apply(request, self._history, self._context_manager.context)
            self._telemetry.record(
                "fallback_applied",
                scenario_id=request.scenario_id,
                attempt=next_attempt,
                strategy=strategy.name,
            )
            self._context_manager.append_audit_log(
                {
                    "event": "fallback_applied",
                    "scenario_id": request.scenario_id,
                    "attempt": next_attempt,
                    "strategy": strategy.name,
                }
            )
            return updated_request

        replanned = self._replan(request, next_attempt)
        return replanned

    def _replan(self, request: HealingRequest, next_attempt: int) -> HealingRequest:
        metadata = dict(request.metadata)
        adjustments = metadata.setdefault("healing_plans", [])
        adjustments.append(
            {
                "type": "replan",
                "attempt": next_attempt,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        replanned = replace(request, metadata=metadata)
        self._telemetry.record(
            "replan_applied",
            scenario_id=request.scenario_id,
            attempt=next_attempt,
        )
        self._context_manager.append_audit_log(
            {
                "event": "replan_applied",
                "scenario_id": request.scenario_id,
                "attempt": next_attempt,
            }
        )
        return replanned

    def _maybe_restart_dependencies(self, request: HealingRequest, next_attempt: int) -> None:
        if not request.dependencies:
            return
        for dependency in request.dependencies:
            restarted = self._dependencies.restart(dependency)
            self._telemetry.record(
                "dependency_restarted",
                scenario_id=request.scenario_id,
                attempt=next_attempt,
                dependency=dependency,
                restarted=restarted,
            )
            self._context_manager.append_audit_log(
                {
                    "event": "dependency_restarted",
                    "scenario_id": request.scenario_id,
                    "attempt": next_attempt,
                    "dependency": dependency,
                    "restarted": restarted,
                }
            )

    def _update_context_telemetry(self) -> None:
        self._context_manager.set_telemetry(self.telemetry_summary())


__all__ = [
    "ActionExecutor",
    "ActionHistory",
    "ContextStateManager",
    "ElementLocator",
    "FallbackStrategy",
    "HealingEvent",
    "HealingRequest",
    "HealingTelemetry",
    "LocatorResult",
    "RetryPolicy",
    "SelfHealingEngine",
    "SelfHealingError",
]
