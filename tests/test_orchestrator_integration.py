from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

from mindmarionette.agents import ScreenCapture, VisualScenario, VisualTestingAgent
from mindmarionette.orchestrator import WorkflowOrchestrator
from mindmarionette.reporting import AgentReportingPipeline
from mindmarionette.visual_verification import VisualVerificationCore


class OrchestratorIntegrationTests(unittest.TestCase):
    def test_orchestrator_invokes_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir))
            agent = VisualTestingAgent(core=core)
            pipeline = AgentReportingPipeline()
            orchestrator = WorkflowOrchestrator([agent], pipeline)

            hook_calls: list[str] = []

            def before_hook(payload: Dict[str, Any]) -> None:
                hook_calls.append("before")

            def after_hook(payload: Dict[str, Any]) -> None:
                hook_calls.append("after")

            orchestrator.register_hook("before_agent", before_hook)
            orchestrator.register_hook("after_agent", after_hook)

            scenario = VisualScenario(
                name="test",
                screens=[ScreenCapture(screen_id="home", pixels=[[10, 20]])],
            )
            orchestrator.run_scenario(scenario)

            self.assertEqual(hook_calls, ["before", "after"])

    def test_orchestrator_integrates_reporting_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir))
            agent = VisualTestingAgent(core=core)
            pipeline = AgentReportingPipeline()
            orchestrator = WorkflowOrchestrator([agent], pipeline)

            scenario = VisualScenario(
                name="integration_test",
                screens=[
                    ScreenCapture(screen_id="login", pixels=[[100, 100], [100, 100]]),
                    ScreenCapture(screen_id="dashboard", pixels=[[150, 150], [150, 150]]),
                ],
            )
            context = orchestrator.run_scenario(scenario)

            self.assertIn("report", context)
            self.assertIn("visual_findings", context["report"])
            self.assertEqual(len(context["report"]["visual_findings"]), 2)
            self.assertTrue(
                all(entry["status"] == "baseline_created" for entry in context["report"]["visual_findings"])
            )

    def test_orchestrator_handles_multiple_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            core = VisualVerificationCore(storage_dir=Path(tmp_dir))
            agent1 = VisualTestingAgent(core=core, name="agent-1")
            agent2 = VisualTestingAgent(core=core, name="agent-2")
            pipeline = AgentReportingPipeline()
            orchestrator = WorkflowOrchestrator([agent1, agent2], pipeline)

            scenario = VisualScenario(
                name="multi_agent",
                screens=[ScreenCapture(screen_id="screen", pixels=[[50, 50]])],
            )
            context = orchestrator.run_scenario(scenario)

            self.assertIn("visual_findings", context["report"])
            findings = context["report"]["visual_findings"]
            agents = {entry["agent"] for entry in findings}
            self.assertEqual(agents, {"agent-1", "agent-2"})


if __name__ == "__main__":
    unittest.main()
