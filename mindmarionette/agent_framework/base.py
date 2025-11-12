from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol


class Agent(Protocol):
    """Protocol describing the minimal behaviour expected from agents."""

    name: str

    def prepare(self, context: Dict[str, Any]) -> None:  # pragma: no cover - default impl
        """Prepare the agent for execution using the orchestrator context."""

    def execute(self, scenario: Any, context: Dict[str, Any]) -> Any:
        """Execute the agent against a scenario and return results."""

    def teardown(self, context: Dict[str, Any]) -> None:  # pragma: no cover - default impl
        """Clean up after execution."""


@dataclass
class BaseAgent:
    """Convenience base class for concrete agents."""

    name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def prepare(self, context: Dict[str, Any]) -> None:
        context.setdefault("agent_state", {})[self.name] = {
            "status": "prepared",
            "metadata": self.metadata,
        }

    def execute(self, scenario: Any, context: Dict[str, Any]) -> Any:  # pragma: no cover - abstract behaviour
        raise NotImplementedError

    def teardown(self, context: Dict[str, Any]) -> None:
        context.setdefault("agent_state", {}).setdefault(self.name, {})["status"] = "completed"
