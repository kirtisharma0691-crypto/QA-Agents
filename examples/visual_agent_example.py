#!/usr/bin/env python3
"""
Example demonstrating the Visual Testing Agent with orchestrator integration.

This example shows how to:
1. Create a visual verification core
2. Set up the visual testing agent
3. Configure the orchestrator with hooks
4. Run scenarios with custom sensitivity thresholds
5. Generate reports with visual findings
"""

from pathlib import Path
import sys
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mindmarionette import (
    AgentReportingPipeline,
    ScreenCapture,
    VisualScenario,
    VisualTestingAgent,
    VisualVerificationCore,
    WorkflowOrchestrator,
)


def logging_hook(payload: Dict[str, Any]) -> None:
    """Sample hook that logs agent execution."""
    agent_name = payload.get("agent").name if "agent" in payload else "unknown"
    if "result" in payload:
        print(f"✓ Agent '{agent_name}' completed execution")
    else:
        print(f"→ Agent '{agent_name}' starting execution")


def create_sample_image(seed: int, width: int = 10, height: int = 10) -> list[list[int]]:
    """Generate a simple test image matrix."""
    return [[(seed + i + j) % 256 for j in range(width)] for i in range(height)]


def main() -> None:
    artifacts_dir = Path("./visual_artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    print("=== Visual Testing Agent Example ===\n")

    core = VisualVerificationCore(
        storage_dir=artifacts_dir,
        default_sensitivity=0.05,
    )
    print(f"✓ Visual verification core initialized (sensitivity: {core.default_sensitivity})")

    agent = VisualTestingAgent(core=core, name="visual-agent")
    print(f"✓ Visual testing agent created: '{agent.name}'\n")

    pipeline = AgentReportingPipeline()
    orchestrator = WorkflowOrchestrator([agent], pipeline)

    orchestrator.register_hook("before_agent", logging_hook)
    orchestrator.register_hook("after_agent", logging_hook)
    print("✓ Orchestrator hooks registered\n")

    print("--- Running Scenario 1: Baseline Creation ---")
    scenario_baseline = VisualScenario(
        name="baseline_run",
        screens=[
            ScreenCapture(screen_id="homepage", pixels=create_sample_image(10)),
            ScreenCapture(screen_id="profile", pixels=create_sample_image(50)),
            ScreenCapture(screen_id="settings", pixels=create_sample_image(100)),
        ],
    )
    context1 = orchestrator.run_scenario(scenario_baseline)
    print(f"✓ Scenario complete. Findings: {len(context1['report']['visual_findings'])}\n")

    for finding in context1["report"]["visual_findings"]:
        print(f"  - {finding['screen_id']}: {finding['status']} (screenshot: {Path(finding['screenshot']).name})")

    print("\n--- Running Scenario 2: Visual Comparison ---")
    scenario_comparison = VisualScenario(
        name="comparison_run",
        screens=[
            ScreenCapture(screen_id="homepage", pixels=create_sample_image(10)),
            ScreenCapture(screen_id="profile", pixels=create_sample_image(55), sensitivity_override=0.1),
            ScreenCapture(screen_id="settings", pixels=create_sample_image(200), sensitivity_override=0.01),
        ],
    )
    context2 = orchestrator.run_scenario(scenario_comparison)
    print(f"✓ Scenario complete. Findings: {len(context2['report']['visual_findings'])}\n")

    for finding in context2["report"]["visual_findings"]:
        status_icon = "✓" if finding["status"] == "pass" else "✗"
        print(
            f"  {status_icon} {finding['screen_id']}: {finding['status']} "
            f"(diff: {finding['diff_ratio']:.4f}, threshold: {finding['sensitivity']})"
        )
        if finding["remediation_suggestions"]:
            for suggestion in finding["remediation_suggestions"]:
                print(f"     → {suggestion}")

    print(f"\n✓ Visual artifacts saved to: {artifacts_dir}")
    print(f"✓ Total entries in reporting pipeline: {len(pipeline.entries)}")


if __name__ == "__main__":
    main()
