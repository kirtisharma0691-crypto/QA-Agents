from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from mindmarionette.visual_verification import VisualVerificationResult


@dataclass
class ReportEntry:
    agent: str
    screen_id: str
    status: str
    diff_ratio: float
    sensitivity: float
    screenshot: str
    remediation_suggestions: Sequence[str]


@dataclass
class AgentReportingPipeline:
    """Collects findings from agents and aggregates them into the report context."""

    entries: List[ReportEntry] = field(default_factory=list)

    def append_result(self, agent_name: str, result: Any, context: Dict[str, Any]) -> None:
        context.setdefault("report", {})
        context["report"].setdefault("visual_findings", [])

        if isinstance(result, Sequence) and not isinstance(result, (str, bytes)):
            for item in result:
                self._append_single(agent_name, item, context)
        else:
            self._append_single(agent_name, result, context)

    def _append_single(self, agent_name: str, item: Any, context: Dict[str, Any]) -> None:
        if not isinstance(item, VisualVerificationResult):
            raise TypeError("Visual reporting pipeline expects VisualVerificationResult instances")

        screenshot = item.diff_path or item.baseline_path
        entry = ReportEntry(
            agent=agent_name,
            screen_id=item.screen_id,
            status=item.status,
            diff_ratio=item.diff_ratio,
            sensitivity=item.sensitivity,
            screenshot=screenshot,
            remediation_suggestions=item.remediation_suggestions,
        )
        self.entries.append(entry)
        context["report"]["visual_findings"].append(entry.__dict__)


__all__ = ["AgentReportingPipeline", "ReportEntry"]
