"""Self-healing engine for automated recovery, retry policies, and telemetry."""

from .engine import (
    ActionExecutor,
    ActionHistory,
    ContextStateManager,
    ElementLocator,
    FallbackStrategy,
    HealingEvent,
    HealingRequest,
    HealingTelemetry,
    LocatorResult,
    RetryPolicy,
    SelfHealingEngine,
    SelfHealingError,
)

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
