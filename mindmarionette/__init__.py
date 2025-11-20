"""MindMarionette - Autonomous QA Agent System"""

__version__ = "0.1.0"

from .agents import ScreenCapture, VisualScenario, VisualTestingAgent
from .orchestrator import WorkflowOrchestrator
from .reporting import AgentReportingPipeline
from .self_healing import (
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
from .visual_verification import VisualVerificationCore, VisualVerificationError, VisualVerificationResult

__all__ = [
    "__version__",
    "ActionExecutor",
    "ActionHistory",
    "AgentReportingPipeline",
    "ContextStateManager",
    "ElementLocator",
    "FallbackStrategy",
    "HealingEvent",
    "HealingRequest",
    "HealingTelemetry",
    "LocatorResult",
    "RetryPolicy",
    "ScreenCapture",
    "SelfHealingEngine",
    "SelfHealingError",
    "VisualScenario",
    "VisualTestingAgent",
    "VisualVerificationCore",
    "VisualVerificationError",
    "VisualVerificationResult",
    "WorkflowOrchestrator",
]
