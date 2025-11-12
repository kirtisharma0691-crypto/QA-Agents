"""MindMarionette - Autonomous QA Agent System"""

__version__ = "0.1.0"

from .agents import ScreenCapture, VisualScenario, VisualTestingAgent
from .orchestrator import WorkflowOrchestrator
from .reporting import AgentReportingPipeline
from .visual_verification import VisualVerificationCore, VisualVerificationError, VisualVerificationResult

__all__ = [
    "__version__",
    "AgentReportingPipeline",
    "ScreenCapture",
    "VisualScenario",
    "VisualTestingAgent",
    "VisualVerificationCore",
    "VisualVerificationError",
    "VisualVerificationResult",
    "WorkflowOrchestrator",
]
