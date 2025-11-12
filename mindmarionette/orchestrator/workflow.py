from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Sequence

from mindmarionette.agent_framework import Agent

Hook = Callable[[Dict[str, Any]], None]


@dataclass
class WorkflowOrchestrator:
    """Runs scenarios by coordinating registered agents and the reporting pipeline."""

    agents: Sequence[Agent]
    reporting_pipeline: "ReportingPipeline"
    hooks: Dict[str, List[Hook]] = field(default_factory=lambda: {"before_agent": [], "after_agent": []})

    def register_hook(self, name: str, hook: Hook) -> None:
        if name not in self.hooks:
            raise ValueError(f"Unsupported hook '{name}'")
        self.hooks[name].append(hook)

    def _emit(self, name: str, payload: Dict[str, Any]) -> None:
        for hook in self.hooks.get(name, []):
            hook(payload)

    def run_scenario(self, scenario: Any, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        context = {} if context is None else context
        for agent in self.agents:
            agent.prepare(context)
            self._emit("before_agent", {"agent": agent, "scenario": scenario, "context": context})
            result = None
            try:
                result = agent.execute(scenario, context)
            finally:
                agent.teardown(context)
            self._emit(
                "after_agent",
                {"agent": agent, "scenario": scenario, "context": context, "result": result},
            )
            if result is not None:
                self.reporting_pipeline.append_result(agent.name, result, context)
        return context


class ReportingPipeline:
    def append_result(self, agent_name: str, result: Any, context: Dict[str, Any]) -> None:  # pragma: no cover - interface
        raise NotImplementedError


__all__ = ["WorkflowOrchestrator", "ReportingPipeline"]
