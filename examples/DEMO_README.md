# MindMarionette QA Agent - Comprehensive Demo

## Overview

This comprehensive demo showcases the full capabilities of the MindMarionette visual testing agent system. It demonstrates real-world usage patterns for automated visual regression testing of web applications.

## What This Demo Does

The demo simulates a complete visual testing workflow for a web application with multiple UI components:

1. **Baseline Creation** - Establishes visual baselines for 5 different UI components
2. **Regression Testing** - Runs visual comparisons against baselines with various types of changes
3. **Intelligent Detection** - Identifies visual regressions with configurable sensitivity
4. **Actionable Reporting** - Generates comprehensive HTML and JSON reports
5. **Visual Diff Maps** - Creates diff artifacts for failed comparisons

## Features Demonstrated

### 🧪 Sample Application Mockup

The file [`sample_app.html`](sample_app.html) provides a static HTML mockup of the sample web application used for the demo. It illustrates the key UI components (header, login form, dashboard, product grid, settings page) that the visual agent simulates during baseline creation and regression checks.

### ✨ Visual Testing Capabilities

- **Multiple UI Components**: Tests different page types (headers, forms, dashboards, grids, settings)
- **Baseline Management**: Automatically creates and stores visual baselines
- **Pixel-Perfect Comparison**: Detects even subtle visual changes
- **Configurable Sensitivity**: Demonstrates global and per-screen sensitivity thresholds
- **Visual Regression Detection**: Identifies various types of UI changes:
  - No changes (perfect match)
  - Minor noise (subtle variations)
  - Color/brightness shifts
  - Layout modifications
  - Content changes

### 📊 Reporting & Analysis

- **Comprehensive HTML Report**: Beautiful, easy-to-read visual report with:
  - Summary statistics (total, passed, failed)
  - Detailed test results with metrics
  - Color-coded status indicators
  - Remediation suggestions
- **JSON Output**: Structured data for programmatic analysis
- **Visual Artifacts**: Baseline images and diff maps saved to disk
- **Progress Tracking**: Real-time console output during execution

### 🎯 Agent System Features

- **Workflow Orchestration**: Demonstrates the orchestrator coordinating agents
- **Execution Hooks**: Shows lifecycle hooks (before_agent, after_agent)
- **Reporting Pipeline**: Illustrates how findings are collected and aggregated
- **Context Management**: Shows how execution context flows through the system

## Prerequisites

- Python 3.8 or higher
- MindMarionette package installed

## Installation

If you haven't installed MindMarionette yet:

```bash
# From the project root
pip install -e .
```

## Running the Demo

### Quick Start

```bash
# From the project root
python examples/comprehensive_demo.py
```

Or from the examples directory:

```bash
cd examples
python comprehensive_demo.py
```

### What to Expect

The demo will:

1. **Initialize the system** - Set up the visual verification core and agent
2. **Create baselines** - Generate and save baselines for 5 UI components
3. **Run regression tests** - Compare modified versions against baselines
4. **Display results** - Show detailed console output with:
   - Test execution progress
   - Pass/fail status for each test
   - Diff ratios and sensitivity thresholds
   - Remediation suggestions
5. **Generate reports** - Create HTML and JSON reports
6. **Save artifacts** - Store all visual artifacts to disk

### Output Files

The demo creates the following output:

```
examples/
├── demo_visual_artifacts/           # Visual artifacts directory (git-ignored)
│   ├── homepage_header_baseline.txt
│   ├── login_form_baseline.txt
│   ├── dashboard_baseline.txt
│   ├── dashboard_diff_<uuid>.txt   # Diff map (if test failed)
│   ├── product_grid_baseline.txt
│   ├── product_grid_diff_<uuid>.txt
│   └── settings_page_baseline.txt
│
├── demo_sample_output/              # Reports directory (git-ignored)
│   ├── demo_report.html             # Interactive HTML report
│   └── demo_results.json            # Structured JSON results
│
└── demo_reference_output/           # Reference samples (committed)
    ├── demo_report.html             # Sample HTML report
    ├── demo_results.json            # Sample JSON results
    ├── dashboard_baseline_sample.txt
    ├── dashboard_diff_sample.txt
    └── README.md
```

**Note**: The `demo_visual_artifacts/` and `demo_sample_output/` directories are git-ignored. A set of reference output files is provided in `demo_reference_output/` for those who want to see expected outputs without running the demo.


## Viewing Results

### HTML Report

Open the generated HTML report in your browser:

```bash
# On macOS
open examples/demo_sample_output/demo_report.html

# On Linux
xdg-open examples/demo_sample_output/demo_report.html

# On Windows
start examples/demo_sample_output/demo_report.html
```

The HTML report includes:
- 📊 Summary dashboard with test statistics
- 📋 Detailed test results for each component
- 🎨 Color-coded status indicators
- 💡 Remediation suggestions
- 📸 Artifact references

### JSON Results

View the structured JSON output:

```bash
cat examples/demo_sample_output/demo_results.json
```

Or process it programmatically:

```python
import json

with open("examples/demo_sample_output/demo_results.json") as f:
    results = json.load(f)
    
for finding in results["visual_findings"]:
    print(f"{finding['screen_id']}: {finding['status']}")
```

### Visual Artifacts

The baseline and diff files are stored as text matrices:

```bash
# View a baseline
cat examples/demo_visual_artifacts/homepage_header_baseline.txt

# View a diff map (if generated)
ls examples/demo_visual_artifacts/*_diff_*.txt
```

## Understanding the Test Scenarios

The demo includes 5 test scenarios with different outcomes:

### 1. Homepage Header (PASS)
- **Change**: None (identical to baseline)
- **Expected**: PASS
- **Demonstrates**: Perfect match detection

### 2. Login Form (PASS)
- **Change**: Minor noise added (1% pixel variation)
- **Sensitivity**: 0.05 (default)
- **Expected**: PASS
- **Demonstrates**: Tolerance for minor variations

### 3. Dashboard (FAIL)
- **Change**: Brightness shift (+30 levels)
- **Sensitivity**: 0.05 (default)
- **Expected**: FAIL
- **Demonstrates**: Detection of color/brightness changes

### 4. Product Grid (FAIL)
- **Change**: Region modified (20x15 pixel area changed)
- **Sensitivity**: 0.05 (default)
- **Expected**: FAIL
- **Demonstrates**: Layout modification detection

### 5. Settings Page (PASS)
- **Change**: Subtle noise (3% pixel variation)
- **Sensitivity**: 0.15 (lenient override)
- **Expected**: PASS
- **Demonstrates**: Per-screen sensitivity configuration

## Customizing the Demo

### Adjust Sensitivity Thresholds

Edit `comprehensive_demo.py` to change sensitivity levels:

```python
# Global sensitivity
core = VisualVerificationCore(
    storage_dir=artifacts_dir,
    default_sensitivity=0.10,  # More lenient (was 0.05)
)

# Per-screen sensitivity
ScreenCapture(
    screen_id="settings_page",
    pixels=settings_subtle,
    sensitivity_override=0.20,  # Even more lenient
)
```

### Add More Test Cases

Add additional UI components to test:

```python
baseline_scenario = VisualScenario(
    name="baseline_creation",
    screens=[
        # ... existing screens ...
        ScreenCapture(
            screen_id="my_custom_component",
            pixels=gen.create_header(width=100, height=20),
            metadata={"description": "Custom component"}
        ),
    ],
)
```

### Modify Visual Changes

Adjust the types of changes introduced:

```python
# More aggressive brightness shift
dashboard_shifted = gen.shift_brightness(gen.create_dashboard(), shift=50)

# Larger region modification
grid_modified = gen.modify_region(
    gen.create_card_grid(), 
    x=20, y=10, w=40, h=30, value=80
)
```

## Integration Examples

### CI/CD Pipeline

```yaml
# .github/workflows/visual-tests.yml
name: Visual Regression Tests

on: [push, pull_request]

jobs:
  visual-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -e .
      - name: Run visual tests
        run: python examples/comprehensive_demo.py
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: visual-test-results
          path: examples/demo_sample_output/
```

### Custom Test Suite

```python
from pathlib import Path
from mindmarionette import (
    VisualVerificationCore,
    VisualTestingAgent,
    VisualScenario,
    ScreenCapture,
    WorkflowOrchestrator,
    AgentReportingPipeline,
)

# Your custom test
def test_my_app():
    core = VisualVerificationCore(
        storage_dir=Path("./my_test_artifacts"),
        default_sensitivity=0.05,
    )
    
    agent = VisualTestingAgent(core=core, name="my-agent")
    pipeline = AgentReportingPipeline()
    orchestrator = WorkflowOrchestrator([agent], pipeline)
    
    scenario = VisualScenario(
        name="my_test",
        screens=[
            ScreenCapture(
                screen_id="my_screen",
                pixels=my_captured_pixels,
            ),
        ],
    )
    
    context = orchestrator.run_scenario(scenario)
    
    # Assert results
    findings = context["report"]["visual_findings"]
    assert all(f["status"] == "pass" for f in findings)
```

## Troubleshooting

### Demo Doesn't Run

**Issue**: `ModuleNotFoundError: No module named 'mindmarionette'`

**Solution**: Install the package:
```bash
pip install -e .
```

### No Output Files Generated

**Issue**: Output directories don't exist

**Solution**: The demo creates directories automatically, but ensure you have write permissions:
```bash
chmod +w examples/
```

### Understanding Diff Ratios

**Diff Ratio** represents the normalized difference between baseline and actual images:
- `0.0` = Perfect match (no differences)
- `0.05` = 5% of pixels differ (typical threshold)
- `0.5` = 50% different (major changes)
- `1.0` = Complete difference (every pixel changed)

The diff ratio is compared against the sensitivity threshold:
- `diff_ratio <= sensitivity` → PASS
- `diff_ratio > sensitivity` → FAIL

## Learn More

- **Main Documentation**: See [README_VISUAL_AGENT.md](../README_VISUAL_AGENT.md)
- **API Reference**: Check docstrings in source code
- **Simple Example**: See [visual_agent_example.py](visual_agent_example.py)
- **Test Suite**: Review [tests/](../tests/) for more examples

## Next Steps

After running the demo, you can:

1. **Integrate with Playwright**: Capture real browser screenshots
2. **Build a Custom Report Generator**: Create your own report formats
3. **Add to CI/CD**: Automate visual testing in your pipeline
4. **Extend the Agent**: Add custom verification logic
5. **Create Baseline Management**: Build tools to update/version baselines

## Support

For questions or issues:
- Check the main README.md
- Review the test suite in tests/
- Examine the visual agent documentation

---

**MindMarionette** - Autonomous QA Agent System
