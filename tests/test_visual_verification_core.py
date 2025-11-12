from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mindmarionette.visual_verification import (
    VisualVerificationCore,
    VisualVerificationError,
)


class VisualVerificationCoreTests(unittest.TestCase):
    def test_verify_creates_baseline_on_first_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir))
            pixels = [[10, 20], [30, 40]]

            result = core.verify("home", pixels)

            self.assertEqual(result.status, "baseline_created")
            self.assertEqual(result.screen_id, "home")
            self.assertEqual(result.diff_ratio, 0.0)
            self.assertIsNone(result.diff_path)
            self.assertTrue(Path(result.baseline_path).exists())

    def test_verify_passes_when_images_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir))
            pixels = [[50, 50], [50, 50]]

            core.verify("page", pixels)
            result = core.verify("page", pixels)

            self.assertEqual(result.status, "pass")
            self.assertEqual(result.diff_ratio, 0.0)

    def test_verify_fails_when_images_differ_above_sensitivity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir), default_sensitivity=0.1)
            baseline = [[100, 100], [100, 100]]
            changed = [[200, 200], [200, 200]]

            core.verify("page", baseline)
            result = core.verify("page", changed)

            self.assertEqual(result.status, "fail")
            self.assertGreater(result.diff_ratio, 0.1)
            self.assertIsNotNone(result.diff_path)
            self.assertTrue(Path(result.diff_path).exists())

    def test_verify_respects_custom_sensitivity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir))
            baseline = [[0, 0, 0], [0, 0, 0]]
            slightly_changed = [[10, 10, 10], [10, 10, 10]]

            core.verify("page", baseline)
            strict_result = core.verify("page", slightly_changed, sensitivity=0.01)
            lenient_result = core.verify("page", slightly_changed, sensitivity=0.2)

            self.assertEqual(strict_result.status, "fail")
            self.assertEqual(lenient_result.status, "pass")

    def test_verify_raises_on_dimension_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir))
            baseline = [[10, 10], [10, 10]]
            different_size = [[10, 10, 10], [10, 10, 10]]

            core.verify("page", baseline)

            with self.assertRaisesRegex(VisualVerificationError, "dimensions do not match"):
                core.verify("page", different_size)

    def test_verify_raises_on_invalid_sensitivity(self) -> None:
        core = VisualVerificationCore()

        with self.assertRaisesRegex(ValueError, "sensitivity must be between 0 and 1"):
            core.verify("page", [[10]], sensitivity=-0.1)

        with self.assertRaisesRegex(ValueError, "sensitivity must be between 0 and 1"):
            core.verify("page", [[10]], sensitivity=1.5)

    def test_verify_raises_on_invalid_default_sensitivity(self) -> None:
        with self.assertRaisesRegex(ValueError, "default_sensitivity must be between 0 and 1"):
            VisualVerificationCore(default_sensitivity=2.0)

    def test_verify_raises_on_invalid_pixel_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir))
            baseline = [[100, 100]]
            invalid = [[300, 300]]

            core.verify("page", baseline)

            with self.assertRaisesRegex(VisualVerificationError, "Pixel values must be between 0 and 255"):
                core.verify("page", invalid)

    def test_verify_writes_diff_map_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir), default_sensitivity=0.05)
            baseline = [[0, 50, 100], [150, 200, 250]]
            changed = [[255, 255, 255], [255, 255, 255]]

            core.verify("screenshot", baseline)
            result = core.verify("screenshot", changed)

            self.assertEqual(result.status, "fail")
            self.assertIsNotNone(result.diff_path)

            diff_path = Path(result.diff_path)
            self.assertTrue(diff_path.exists())
            content = diff_path.read_text(encoding="utf-8")
            self.assertGreater(len(content.strip()), 0)

    def test_verify_produces_remediation_suggestions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir), default_sensitivity=0.01)
            baseline = [[100, 100, 100], [100, 100, 100]]
            small_change = [[120, 120, 120], [120, 120, 120]]
            large_change = [[250, 250, 250], [250, 250, 250]]

            core.verify("page", baseline)

            small_result = core.verify("page", small_change)
            self.assertGreater(len(small_result.remediation_suggestions), 0)
            self.assertTrue(
                any("updating baseline" in suggestion.lower() for suggestion in small_result.remediation_suggestions)
            )

            large_result = core.verify("page", large_change)
            self.assertTrue(
                any("large deviation" in suggestion.lower() for suggestion in large_result.remediation_suggestions)
            )

    def test_default_sensitivity_property(self) -> None:
        core = VisualVerificationCore(default_sensitivity=0.25)
        self.assertEqual(core.default_sensitivity, 0.25)


if __name__ == "__main__":
    unittest.main()
