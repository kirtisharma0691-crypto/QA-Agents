from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple
import uuid


@dataclass
class VisualVerificationResult:
    """Outcome of comparing a screenshot against the stored baseline."""

    screen_id: str
    status: str
    diff_ratio: float
    sensitivity: float
    baseline_path: str
    diff_path: Optional[str]
    remediation_suggestions: List[str]


class VisualVerificationError(Exception):
    """Raised when visual verification cannot complete successfully."""


class VisualVerificationCore:
    """Core pixel-diff logic for the visual agent."""

    def __init__(self, storage_dir: Optional[Path] = None, default_sensitivity: float = 0.05) -> None:
        if not (0 <= default_sensitivity <= 1):
            raise ValueError("default_sensitivity must be between 0 and 1")
        self._baselines: Dict[str, List[List[int]]] = {}
        self._storage_dir = Path(storage_dir) if storage_dir else Path.cwd() / "visual_artifacts"
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._default_sensitivity = default_sensitivity

    @property
    def default_sensitivity(self) -> float:
        return self._default_sensitivity

    def verify(
        self,
        screen_id: str,
        image: Sequence[Sequence[int]],
        sensitivity: Optional[float] = None,
    ) -> VisualVerificationResult:
        sensitivity_to_use = sensitivity if sensitivity is not None else self._default_sensitivity
        if not (0 <= sensitivity_to_use <= 1):
            raise ValueError("sensitivity must be between 0 and 1")

        pixels = self._clone_pixels(image)
        if screen_id not in self._baselines:
            path = self._write_matrix(self._baseline_path(screen_id), pixels)
            self._baselines[screen_id] = pixels
            return VisualVerificationResult(
                screen_id=screen_id,
                status="baseline_created",
                diff_ratio=0.0,
                sensitivity=sensitivity_to_use,
                baseline_path=str(path),
                diff_path=None,
                remediation_suggestions=["Baseline created for future comparisons."],
            )

        baseline = self._baselines[screen_id]
        diff_ratio, diff_map = self._compute_diff(baseline, pixels)
        diff_path: Optional[Path] = None
        if diff_map is not None:
            diff_path = self._write_matrix(self._diff_path(screen_id), diff_map)

        status = "pass" if diff_ratio <= sensitivity_to_use else "fail"
        remediation = self._build_suggestions(status, diff_ratio, sensitivity_to_use)
        return VisualVerificationResult(
            screen_id=screen_id,
            status=status,
            diff_ratio=diff_ratio,
            sensitivity=sensitivity_to_use,
            baseline_path=str(self._baseline_path(screen_id)),
            diff_path=str(diff_path) if diff_path else None,
            remediation_suggestions=remediation,
        )

    def _build_suggestions(self, status: str, diff_ratio: float, sensitivity: float) -> List[str]:
        if status == "pass":
            return ["Visual comparison within sensitivity threshold."]
        suggestions = [
            f"Visual deviation of {diff_ratio:.3f} exceeds sensitivity {sensitivity:.3f}. Review UI changes.",
        ]
        if diff_ratio < 0.5:
            suggestions.append("Consider updating baseline if the change is expected.")
        else:
            suggestions.append("Large deviation detected. Investigate asset loading or layout regressions.")
        return suggestions

    def _compute_diff(
        self, baseline: Sequence[Sequence[int]], image: Sequence[Sequence[int]]
    ) -> Tuple[float, Optional[List[List[int]]]]:
        if len(baseline) != len(image) or any(len(b_row) != len(i_row) for b_row, i_row in zip(baseline, image)):
            raise VisualVerificationError("Baseline and image dimensions do not match")

        total_diff = 0
        max_possible = 0
        diff_map: List[List[int]] = []
        for baseline_row, image_row in zip(baseline, image):
            diff_row: List[int] = []
            for base_pixel, new_pixel in zip(baseline_row, image_row):
                if not (0 <= base_pixel <= 255 and 0 <= new_pixel <= 255):
                    raise VisualVerificationError("Pixel values must be between 0 and 255")
                delta = abs(base_pixel - new_pixel)
                diff_row.append(delta)
                total_diff += delta
                max_possible += 255
            diff_map.append(diff_row)

        diff_ratio = total_diff / max_possible if max_possible else 0.0
        return diff_ratio, diff_map

    def _clone_pixels(self, image: Sequence[Sequence[int]]) -> List[List[int]]:
        return [list(row) for row in image]

    def _baseline_path(self, screen_id: str) -> Path:
        filename = f"{screen_id}_baseline.txt"
        return self._storage_dir / filename

    def _diff_path(self, screen_id: str) -> Path:
        filename = f"{screen_id}_diff_{uuid.uuid4().hex}.txt"
        return self._storage_dir / filename

    def _write_matrix(self, path: Path, matrix: Sequence[Sequence[int]]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for row in matrix:
                handle.write(" ".join(str(value) for value in row))
                handle.write("\n")
        return path


__all__ = ["VisualVerificationCore", "VisualVerificationResult", "VisualVerificationError"]
