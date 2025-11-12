from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mindmarionette.agents import ScreenCapture, VisualScenario, VisualTestingAgent
from mindmarionette.orchestrator import WorkflowOrchestrator
from mindmarionette.reporting import AgentReportingPipeline
from mindmarionette.visual_verification import VisualVerificationCore


def _matrix(value: int) -> list[list[int]]:
    return [[value, value], [value, value]]


class VisualAgentIntegrationTests(unittest.TestCase):
    def test_visual_agent_appends_findings_to_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = Path(tmp_dir) / "artifacts"
            core = VisualVerificationCore(storage_dir=storage)
            agent = VisualTestingAgent(core=core)
            pipeline = AgentReportingPipeline()
            orchestrator = WorkflowOrchestrator([agent], pipeline)

            scenario = VisualScenario(
                name="smoke",
                screens=[
                    ScreenCapture(screen_id="home", pixels=_matrix(10)),
                    ScreenCapture(screen_id="profile", pixels=_matrix(42)),
                ],
            )

            context: dict = {}
            orchestrator.run_scenario(scenario, context)

            self.assertIn("report", context)
            findings = context["report"].get("visual_findings")
            self.assertIsNotNone(findings)
            self.assertEqual(len(findings), 2)

            for entry in findings:
                self.assertEqual(entry["status"], "baseline_created")
                screenshot_path = Path(entry["screenshot"])
                self.assertTrue(screenshot_path.exists())
                self.assertNotEqual(screenshot_path.read_text(encoding="utf-8").strip(), "")

    def test_visual_sensitivity_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            storage = Path(tmp_dir) / "artifacts"
            core = VisualVerificationCore(storage_dir=storage, default_sensitivity=0.1)

            baseline = [[15, 15, 15], [15, 15, 15]]
            variant = [[15, 255, 15], [15, 255, 15]]

            baseline_result = core.verify("settings", baseline)
            self.assertEqual(baseline_result.status, "baseline_created")

            strict_result = core.verify("settings", variant, sensitivity=0.05)
            self.assertEqual(strict_result.status, "fail")
            self.assertIsNotNone(strict_result.diff_path)
            self.assertTrue(Path(strict_result.diff_path).exists())

            lenient_result = core.verify("settings", variant, sensitivity=0.4)
            self.assertEqual(lenient_result.status, "pass")


if __name__ == "__main__":
    unittest.main()
