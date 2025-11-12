from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from mindmarionette.agent_framework import BaseAgent
from mindmarionette.visual_verification import VisualVerificationCore, VisualVerificationResult


@dataclass
class ScreenCapture:
    screen_id: str
    pixels: Sequence[Sequence[int]]
    sensitivity_override: Optional[float] = None
    metadata: Dict[str, Any] | None = None


@dataclass
class VisualScenario:
    name: str
    screens: Sequence[ScreenCapture] = field(default_factory=list)


class VisualTestingAgent(BaseAgent):
    def __init__(
        self,
        core: VisualVerificationCore,
        name: str = "visual-testing",
        default_sensitivity: Optional[float] = None,
    ) -> None:
        super().__init__(name=name)
        self._core = core
        self._default_sensitivity = default_sensitivity

    def execute(self, scenario: VisualScenario, context: Dict[str, Any]) -> List[VisualVerificationResult]:
        context.setdefault("visual_artifacts", {})
        results: List[VisualVerificationResult] = []
        for screen in scenario.screens:
            sensitivity = self._resolve_sensitivity(screen)
            result = self._core.verify(screen.screen_id, screen.pixels, sensitivity)
            results.append(result)
            self._record_artifact(screen, result, context)
        return results

    def _resolve_sensitivity(self, screen: ScreenCapture) -> Optional[float]:
        if screen.sensitivity_override is not None:
            return screen.sensitivity_override
        return self._default_sensitivity

    def _record_artifact(self, screen: ScreenCapture, result: VisualVerificationResult, context: Dict[str, Any]) -> None:
        screenshot_path = result.diff_path or result.baseline_path
        context.setdefault("visual_artifacts", {}).setdefault(screen.screen_id, []).append(
            {
                "scenario": screen.metadata.get("scenario") if screen.metadata else None,
                "screenshot": screenshot_path,
                "status": result.status,
            }
        )


__all__ = ["ScreenCapture", "VisualScenario", "VisualTestingAgent"]
