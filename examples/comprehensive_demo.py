#!/usr/bin/env python3
"""
MindMarionette QA Agent - Comprehensive Demo

This demo showcases the full capabilities of the MindMarionette visual testing agent:
1. Baseline creation for multiple UI components
2. Visual regression detection with various severity levels
3. Sensitivity threshold configuration
4. Comprehensive reporting with actionable insights
5. Visual diff generation for failed comparisons

The demo simulates testing different UI components of a web application:
- Homepage with header and navigation
- Login form
- Dashboard with data panels
- Product card grid
- Settings page
"""

import json
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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


class DemoImageGenerator:
    """Generates realistic UI mockup images for demo purposes."""
    
    @staticmethod
    def create_header(width: int = 80, height: int = 10, brightness: int = 200) -> List[List[int]]:
        """Create a header-like image with gradient effect."""
        image = []
        for y in range(height):
            row = []
            for x in range(width):
                pixel = min(255, brightness - (x // 4) % 50)
                row.append(pixel)
            image.append(row)
        return image
    
    @staticmethod
    def create_form(width: int = 60, height: int = 40) -> List[List[int]]:
        """Create a form-like image with input fields."""
        image = [[240] * width for _ in range(height)]
        
        # Title area
        for y in range(3):
            for x in range(width):
                image[y][x] = 180
        
        # Input field boxes
        field_positions = [(8, 12), (15, 19), (22, 26), (29, 33)]
        for start_y, end_y in field_positions:
            for y in range(start_y, end_y):
                for x in range(5, width - 5):
                    if y == start_y or y == end_y - 1:
                        image[y][x] = 100
                    else:
                        image[y][x] = 255
        
        # Submit button
        for y in range(36, 39):
            for x in range(20, 40):
                image[y][x] = 120
        
        return image
    
    @staticmethod
    def create_dashboard(width: int = 100, height: int = 80) -> List[List[int]]:
        """Create a complex dashboard-like layout."""
        image = [[240] * width for _ in range(height)]
        
        # Header section
        for y in range(10):
            for x in range(width):
                image[y][x] = 190
        
        # Sidebar
        for y in range(10, height):
            for x in range(20):
                image[y][x] = 210
        
        # Panels
        panels = [(25, 15, 45, 35), (55, 15, 40, 35), (25, 55, 70, 20)]
        for px, py, pw, ph in panels:
            for y in range(py, min(py + ph, height)):
                for x in range(px, min(px + pw, width)):
                    if y == py or y == py + ph - 1 or x == px or x == px + pw - 1:
                        image[y][x] = 120
                    else:
                        image[y][x] = 250
        
        return image
    
    @staticmethod
    def create_card_grid(width: int = 90, height: int = 60) -> List[List[int]]:
        """Create a grid of card-like elements."""
        image = [[245] * width for _ in range(height)]
        
        cards_per_row = 3
        card_width = 25
        card_height = 25
        gap = 5
        
        for i in range(6):
            row = i // cards_per_row
            col = i % cards_per_row
            
            start_x = gap + col * (card_width + gap)
            start_y = gap + row * (card_height + gap)
            
            if start_y + card_height >= height:
                break
            
            for y in range(start_y, min(start_y + card_height, height)):
                for x in range(start_x, min(start_x + card_width, width)):
                    if y == start_y or y == start_y + card_height - 1 or x == start_x or x == start_x + card_width - 1:
                        image[y][x] = 150
                    elif y < start_y + 10:
                        image[y][x] = 200
                    else:
                        image[y][x] = 250
        
        return image
    
    @staticmethod
    def create_settings_page(width: int = 70, height: int = 50) -> List[List[int]]:
        """Create a settings page with sections."""
        image = [[235] * width for _ in range(height)]
        
        # Title
        for y in range(5):
            for x in range(width):
                image[y][x] = 180
        
        # Settings sections
        sections = [(10, 20), (25, 35), (40, 47)]
        for start_y, end_y in sections:
            for y in range(start_y, end_y):
                for x in range(5, width - 5):
                    if y == start_y:
                        image[y][x] = 160
                    else:
                        image[y][x] = 245
        
        return image
    
    @staticmethod
    def add_noise(image: List[List[int]], intensity: float = 0.02) -> List[List[int]]:
        """Add subtle noise to simulate minor visual changes."""
        noisy_image = []
        for row in image:
            noisy_row = []
            for pixel in row:
                if random.random() < intensity:
                    noise = random.randint(-15, 15)
                    noisy_pixel = max(0, min(255, pixel + noise))
                else:
                    noisy_pixel = pixel
                noisy_row.append(noisy_pixel)
            noisy_image.append(noisy_row)
        return noisy_image
    
    @staticmethod
    def modify_region(image: List[List[int]], x: int, y: int, w: int, h: int, value: int) -> List[List[int]]:
        """Modify a region to simulate a visual change."""
        modified = [row[:] for row in image]
        height = len(image)
        width = len(image[0]) if height > 0 else 0
        
        for dy in range(h):
            for dx in range(w):
                py = y + dy
                px = x + dx
                if 0 <= py < height and 0 <= px < width:
                    modified[py][px] = value
        
        return modified
    
    @staticmethod
    def shift_brightness(image: List[List[int]], shift: int) -> List[List[int]]:
        """Shift all pixel values by a constant amount."""
        shifted = []
        for row in image:
            shifted_row = [max(0, min(255, pixel + shift)) for pixel in row]
            shifted.append(shifted_row)
        return shifted


class DemoReportGenerator:
    """Generates a comprehensive HTML report for the demo."""
    
    @staticmethod
    def generate_html_report(context: Dict[str, Any], output_path: Path) -> None:
        """Generate an HTML report with visual findings."""
        findings = context.get("report", {}).get("visual_findings", [])
        
        total = len(findings)
        passed = sum(1 for f in findings if f["status"] == "pass")
        failed = sum(1 for f in findings if f["status"] == "fail")
        baseline_created = sum(1 for f in findings if f["status"] == "baseline_created")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindMarionette Visual Testing Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 40px;
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 32px;
        }}
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 16px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .summary-card {{
            padding: 20px;
            border-radius: 6px;
            text-align: center;
        }}
        .summary-card.total {{ background: #3498db; color: white; }}
        .summary-card.passed {{ background: #2ecc71; color: white; }}
        .summary-card.failed {{ background: #e74c3c; color: white; }}
        .summary-card.baseline {{ background: #f39c12; color: white; }}
        .summary-card h3 {{ font-size: 36px; margin-bottom: 5px; }}
        .summary-card p {{ opacity: 0.9; }}
        .finding {{
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            margin-bottom: 30px;
            overflow: hidden;
        }}
        .finding-header {{
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e0e0e0;
        }}
        .finding-header.pass {{ background: #d4edda; }}
        .finding-header.fail {{ background: #f8d7da; }}
        .finding-header.baseline {{ background: #fff3cd; }}
        .finding-title {{
            font-size: 20px;
            font-weight: 600;
            color: #2c3e50;
        }}
        .status-badge {{
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .status-badge.pass {{ background: #2ecc71; color: white; }}
        .status-badge.fail {{ background: #e74c3c; color: white; }}
        .status-badge.baseline {{ background: #f39c12; color: white; }}
        .finding-body {{
            padding: 20px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .metric {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
        }}
        .metric-label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .metric-value {{
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
        }}
        .suggestions {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #3498db;
        }}
        .suggestions h4 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 16px;
        }}
        .suggestions ul {{
            list-style: none;
            padding-left: 0;
        }}
        .suggestions li {{
            padding: 5px 0;
            color: #555;
        }}
        .suggestions li:before {{
            content: "→ ";
            color: #3498db;
            font-weight: bold;
        }}
        .screenshot-info {{
            margin-top: 15px;
            padding: 10px;
            background: #e9ecef;
            border-radius: 4px;
            font-size: 14px;
            color: #495057;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
        }}
        .agent-info {{
            display: inline-block;
            padding: 4px 12px;
            background: #6c757d;
            color: white;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 MindMarionette Visual Testing Report</h1>
        <p class="subtitle">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary">
            <div class="summary-card total">
                <h3>{total}</h3>
                <p>Total Tests</p>
            </div>
            <div class="summary-card passed">
                <h3>{passed}</h3>
                <p>Passed</p>
            </div>
            <div class="summary-card failed">
                <h3>{failed}</h3>
                <p>Failed</p>
            </div>
            <div class="summary-card baseline">
                <h3>{baseline_created}</h3>
                <p>Baselines Created</p>
            </div>
        </div>
        
        <h2 style="margin-bottom: 20px; color: #2c3e50;">Test Results</h2>
"""
        
        for finding in findings:
            status = finding["status"]
            screen_id = finding["screen_id"]
            diff_ratio = finding["diff_ratio"]
            sensitivity = finding["sensitivity"]
            agent = finding["agent"]
            suggestions = finding["remediation_suggestions"]
            screenshot = finding["screenshot"]
            
            status_class = "pass" if status == "pass" else ("fail" if status == "fail" else "baseline")
            
            html += f"""
        <div class="finding">
            <div class="finding-header {status_class}">
                <div>
                    <span class="agent-info">{agent}</span>
                    <span class="finding-title">{screen_id}</span>
                </div>
                <span class="status-badge {status_class}">{status}</span>
            </div>
            <div class="finding-body">
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Diff Ratio</div>
                        <div class="metric-value">{diff_ratio:.4f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Sensitivity</div>
                        <div class="metric-value">{sensitivity:.4f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Status</div>
                        <div class="metric-value">{status.replace('_', ' ').title()}</div>
                    </div>
                </div>
                
                <div class="suggestions">
                    <h4>💡 Remediation Suggestions</h4>
                    <ul>
"""
            for suggestion in suggestions:
                html += f"                        <li>{suggestion}</li>\n"
            
            html += f"""                    </ul>
                </div>
                
                <div class="screenshot-info">
                    📸 Artifact: <code>{Path(screenshot).name}</code>
                </div>
            </div>
        </div>
"""
        
        html += """
        <div class="footer">
            <p><strong>MindMarionette QA Agent System</strong> - Autonomous Visual Testing</p>
            <p style="margin-top: 5px;">Powered by pixel-perfect diff analysis and intelligent remediation</p>
        </div>
    </div>
</body>
</html>
"""
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)


def print_banner(text: str, char: str = "=") -> None:
    """Print a formatted banner."""
    width = 80
    print(f"\n{char * width}")
    print(f"{text:^{width}}")
    print(f"{char * width}\n")


def print_section(text: str) -> None:
    """Print a section header."""
    print(f"\n{'─' * 80}")
    print(f"  {text}")
    print(f"{'─' * 80}\n")


def main() -> None:
    """Run the comprehensive MindMarionette demo."""
    
    random.seed(42)
    
    print_banner("🎭 MindMarionette QA Agent - Comprehensive Demo", "=")
    
    print("This demo will showcase the full capabilities of the MindMarionette")
    print("visual testing agent by simulating a complete test suite for a web application.\n")
    
    # Setup
    demo_root = Path(__file__).resolve().parent
    artifacts_dir = demo_root / "demo_visual_artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    report_output = demo_root / "demo_sample_output" / "demo_report.html"
    json_output = demo_root / "demo_sample_output" / "demo_results.json"
    
    def format_path(path: Path) -> str:
        try:
            return str(path.relative_to(PROJECT_ROOT))
        except ValueError:
            return str(path)
    
    print(f"📁 Artifacts directory: {format_path(artifacts_dir)}")
    print(f"📄 HTML report will be saved to: {format_path(report_output)}")
    print(f"📄 JSON results will be saved to: {format_path(json_output)}")
    
    sample_app_path = demo_root / "sample_app.html"
    if sample_app_path.exists():
        print(f"🧪 Sample application mockup: {format_path(sample_app_path)}")
    
    # Initialize the system
    print_section("🔧 Initializing MindMarionette System")
    
    core = VisualVerificationCore(
        storage_dir=artifacts_dir,
        default_sensitivity=0.05,
    )
    print(f"✓ Visual verification core initialized")
    print(f"  - Storage: {artifacts_dir}")
    print(f"  - Default sensitivity: {core.default_sensitivity}")
    
    agent = VisualTestingAgent(core=core, name="visual-qa-agent")
    print(f"✓ Visual testing agent created: '{agent.name}'")
    
    pipeline = AgentReportingPipeline()
    orchestrator = WorkflowOrchestrator([agent], pipeline)
    print(f"✓ Workflow orchestrator configured with reporting pipeline")
    
    # Register hooks for progress tracking
    def progress_hook(payload: Dict[str, Any]) -> None:
        agent_name = payload.get("agent").name if "agent" in payload else "unknown"
        if "result" in payload:
            print(f"  ✓ Agent '{agent_name}' completed execution")
        else:
            print(f"  → Agent '{agent_name}' starting execution")
    
    orchestrator.register_hook("before_agent", progress_hook)
    orchestrator.register_hook("after_agent", progress_hook)
    print(f"✓ Execution hooks registered\n")
    
    gen = DemoImageGenerator()
    
    # Phase 1: Baseline Creation
    print_banner("📸 PHASE 1: Creating Baselines", "=")
    print("Creating visual baselines for 5 different UI components...\n")
    
    baseline_scenario = VisualScenario(
        name="baseline_creation",
        screens=[
            ScreenCapture(
                screen_id="homepage_header",
                pixels=gen.create_header(),
                metadata={"description": "Application header with navigation"}
            ),
            ScreenCapture(
                screen_id="login_form",
                pixels=gen.create_form(),
                metadata={"description": "User login form"}
            ),
            ScreenCapture(
                screen_id="dashboard",
                pixels=gen.create_dashboard(),
                metadata={"description": "Main dashboard with data panels"}
            ),
            ScreenCapture(
                screen_id="product_grid",
                pixels=gen.create_card_grid(),
                metadata={"description": "Product card grid layout"}
            ),
            ScreenCapture(
                screen_id="settings_page",
                pixels=gen.create_settings_page(),
                metadata={"description": "User settings page"}
            ),
        ],
    )
    
    context_baseline = orchestrator.run_scenario(baseline_scenario)
    
    print(f"\n✓ Baseline creation complete!")
    print(f"  Total findings: {len(context_baseline['report']['visual_findings'])}\n")
    
    for finding in context_baseline["report"]["visual_findings"]:
        print(f"  📸 {finding['screen_id']:<20} → {finding['status'].upper()}")
    
    # Phase 2: Regression Testing
    print_banner("🔍 PHASE 2: Visual Regression Testing", "=")
    print("Running regression tests with various types of visual changes...\n")
    print("Test scenarios:")
    print("  1. homepage_header: No changes (should PASS)")
    print("  2. login_form: Minor noise added (should PASS with default sensitivity)")
    print("  3. dashboard: Moderate brightness shift (should FAIL)")
    print("  4. product_grid: Region modified (should FAIL)")
    print("  5. settings_page: Subtle changes with lenient sensitivity (should PASS)\n")
    
    # Create modified versions
    header_unchanged = gen.create_header()
    form_with_noise = gen.add_noise(gen.create_form(), intensity=0.01)
    dashboard_shifted = gen.shift_brightness(gen.create_dashboard(), shift=30)
    grid_modified = gen.modify_region(gen.create_card_grid(), x=40, y=20, w=20, h=15, value=100)
    settings_subtle = gen.add_noise(gen.create_settings_page(), intensity=0.03)
    
    regression_scenario = VisualScenario(
        name="regression_testing",
        screens=[
            ScreenCapture(
                screen_id="homepage_header",
                pixels=header_unchanged,
            ),
            ScreenCapture(
                screen_id="login_form",
                pixels=form_with_noise,
            ),
            ScreenCapture(
                screen_id="dashboard",
                pixels=dashboard_shifted,
            ),
            ScreenCapture(
                screen_id="product_grid",
                pixels=grid_modified,
            ),
            ScreenCapture(
                screen_id="settings_page",
                pixels=settings_subtle,
                sensitivity_override=0.15,  # More lenient for this screen
            ),
        ],
    )
    
    context_regression = orchestrator.run_scenario(regression_scenario)
    
    print(f"\n✓ Regression testing complete!")
    print(f"  Total findings: {len(context_regression['report']['visual_findings'])}\n")
    
    # Display detailed results
    print_section("📊 Detailed Test Results")
    
    passed = 0
    failed = 0
    
    for finding in context_regression["report"]["visual_findings"]:
        status = finding["status"]
        screen_id = finding["screen_id"]
        diff_ratio = finding["diff_ratio"]
        sensitivity = finding["sensitivity"]
        
        if status == "pass":
            icon = "✅"
            passed += 1
        else:
            icon = "❌"
            failed += 1
        
        print(f"{icon} {screen_id}")
        print(f"   Status: {status.upper()}")
        print(f"   Diff Ratio: {diff_ratio:.6f}")
        print(f"   Sensitivity: {sensitivity:.6f}")
        print(f"   Threshold: {'WITHIN' if status == 'pass' else 'EXCEEDED'}")
        
        if finding["remediation_suggestions"]:
            print(f"   💡 Suggestions:")
            for suggestion in finding["remediation_suggestions"]:
                print(f"      → {suggestion}")
        print()
    
    # Summary
    print_section("📈 Test Summary")
    total = passed + failed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"  Total Tests: {total}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📊 Pass Rate: {pass_rate:.1f}%")
    print(f"  📦 Pipeline Entries: {len(pipeline.entries)}")
    
    # Generate reports
    print_section("📄 Generating Reports")
    
    DemoReportGenerator.generate_html_report(context_regression, report_output)
    print(f"✓ HTML report generated: {format_path(report_output)}")
    
    # Save JSON results
    json_output.parent.mkdir(parents=True, exist_ok=True)
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(context_regression["report"], f, indent=2)
    print(f"✓ JSON results saved: {format_path(json_output)}")
    
    # Artifacts info
    print_section("📁 Visual Artifacts")
    artifacts = list(artifacts_dir.glob("*.txt"))
    print(f"Total artifacts saved: {len(artifacts)}")
    print(f"Location: {format_path(artifacts_dir)}")
    print(f"\nArtifact types:")
    baselines = [a for a in artifacts if "baseline" in a.name]
    diffs = [a for a in artifacts if "diff" in a.name]
    print(f"  - Baselines: {len(baselines)}")
    print(f"  - Diff maps: {len(diffs)}")
    
    # Final banner
    print_banner("🎉 Demo Complete!", "=")
    print("The MindMarionette QA agent has successfully demonstrated:")
    print("  ✓ Baseline creation for multiple UI components")
    print("  ✓ Visual regression detection with varying sensitivity levels")
    print("  ✓ Intelligent remediation suggestions")
    print("  ✓ Comprehensive reporting with HTML and JSON outputs")
    print("  ✓ Visual diff generation for failed comparisons")
    print(f"\n📄 Open {format_path(report_output)} in your browser to view the detailed report!")
    print(f"📁 Check {format_path(artifacts_dir)} for visual artifacts and diff maps.")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
