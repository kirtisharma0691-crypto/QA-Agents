# Visual Testing Agent

## Overview

The Visual Testing Agent is a specialized component of the MindMarionette QA system that performs visual verification and regression testing. It leverages the visual verification core for baseline creation, pixel-difference analysis, and provides intelligent remediation suggestions.

## Features

- **Baseline Management**: Automatically creates and stores visual baselines for test scenarios
- **Pixel-Diff Analysis**: Performs precise pixel-by-pixel comparison to detect visual regressions
- **Configurable Sensitivity**: Supports global and per-screen sensitivity thresholds
- **Remediation Suggestions**: Provides actionable suggestions for visual deviations
- **Orchestrator Integration**: Seamlessly integrates with the workflow orchestrator
- **Reporting Pipeline**: Appends visual findings to comprehensive test reports

## Architecture

### Core Components

1. **VisualVerificationCore** (`mindmarionette.visual_verification.core`)
   - Manages baseline storage and retrieval
   - Performs pixel-diff calculations
   - Generates diff maps for failed comparisons
   - Configurable sensitivity thresholds (0.0 to 1.0)

2. **VisualTestingAgent** (`mindmarionette.agents.visual`)
   - Implements the Agent protocol
   - Coordinates with the visual verification core
   - Supports per-screen sensitivity overrides
   - Records visual artifacts in the execution context

3. **WorkflowOrchestrator** (`mindmarionette.orchestrator.workflow`)
   - Coordinates agent execution
   - Manages lifecycle hooks (before_agent, after_agent)
   - Routes results to the reporting pipeline

4. **AgentReportingPipeline** (`mindmarionette.reporting.pipeline`)
   - Collects findings from agents
   - Appends visual results to the report context
   - Includes screenshots, status, and remediation suggestions

## Usage

### Basic Setup

```python
from pathlib import Path
from mindmarionette import (
    VisualVerificationCore,
    VisualTestingAgent,
    WorkflowOrchestrator,
    AgentReportingPipeline,
    VisualScenario,
    ScreenCapture,
)

# Initialize the visual verification core
core = VisualVerificationCore(
    storage_dir=Path("./visual_artifacts"),
    default_sensitivity=0.05  # 5% tolerance
)

# Create the visual testing agent
agent = VisualTestingAgent(core=core, name="visual-agent")

# Set up reporting pipeline and orchestrator
pipeline = AgentReportingPipeline()
orchestrator = WorkflowOrchestrator([agent], pipeline)
```

### Creating Baselines

```python
# First run creates baselines
scenario = VisualScenario(
    name="baseline_creation",
    screens=[
        ScreenCapture(screen_id="homepage", pixels=homepage_pixels),
        ScreenCapture(screen_id="profile", pixels=profile_pixels),
    ],
)

context = orchestrator.run_scenario(scenario)

# Check the report
for finding in context["report"]["visual_findings"]:
    print(f"{finding['screen_id']}: {finding['status']}")
    # Output: homepage: baseline_created
    #         profile: baseline_created
```

### Running Visual Comparisons

```python
# Subsequent runs compare against baselines
scenario = VisualScenario(
    name="regression_test",
    screens=[
        ScreenCapture(screen_id="homepage", pixels=updated_homepage_pixels),
        ScreenCapture(
            screen_id="profile", 
            pixels=updated_profile_pixels,
            sensitivity_override=0.1  # More lenient for this screen
        ),
    ],
)

context = orchestrator.run_scenario(scenario)

for finding in context["report"]["visual_findings"]:
    print(f"{finding['screen_id']}: {finding['status']}")
    print(f"  Diff ratio: {finding['diff_ratio']:.4f}")
    print(f"  Sensitivity: {finding['sensitivity']}")
    if finding['status'] == 'fail':
        print("  Suggestions:")
        for suggestion in finding['remediation_suggestions']:
            print(f"    - {suggestion}")
```

### Orchestrator Hooks

```python
def logging_hook(payload):
    agent_name = payload['agent'].name
    print(f"Agent '{agent_name}' executing...")

orchestrator.register_hook("before_agent", logging_hook)
orchestrator.register_hook("after_agent", lambda p: print("Complete!"))

context = orchestrator.run_scenario(scenario)
```

## Configuration

### Sensitivity Thresholds

Sensitivity values range from 0.0 to 1.0:

- **0.0**: No tolerance (pixel-perfect match required)
- **0.05**: Default (5% tolerance) - Recommended for most cases
- **0.1**: Lenient (10% tolerance) - For screens with dynamic content
- **0.5+**: Very lenient - For highly variable screens

Sensitivity can be configured at three levels:

1. **Core level**: Default for all screens
   ```python
   core = VisualVerificationCore(default_sensitivity=0.05)
   ```

2. **Agent level**: Override for all screens in the agent
   ```python
   agent = VisualTestingAgent(core=core, default_sensitivity=0.1)
   ```

3. **Screen level**: Override for individual screens
   ```python
   ScreenCapture(
       screen_id="dynamic_page",
       pixels=pixels,
       sensitivity_override=0.15
   )
   ```

Priority: Screen level > Agent level > Core level

## Data Structures

### ScreenCapture

```python
@dataclass
class ScreenCapture:
    screen_id: str  # Unique identifier for the screen
    pixels: Sequence[Sequence[int]]  # 2D array of grayscale pixel values (0-255)
    sensitivity_override: Optional[float] = None  # Per-screen sensitivity
    metadata: Dict[str, Any] | None = None  # Additional metadata
```

### VisualScenario

```python
@dataclass
class VisualScenario:
    name: str  # Scenario name
    screens: Sequence[ScreenCapture]  # List of screens to verify
```

### VisualVerificationResult

```python
@dataclass
class VisualVerificationResult:
    screen_id: str  # Screen identifier
    status: str  # "baseline_created", "pass", or "fail"
    diff_ratio: float  # Normalized difference ratio (0.0 to 1.0)
    sensitivity: float  # Sensitivity threshold used
    baseline_path: str  # Path to baseline image file
    diff_path: Optional[str]  # Path to diff map (if failed)
    remediation_suggestions: List[str]  # Actionable suggestions
```

## Report Structure

The visual agent appends findings to the context under `context["report"]["visual_findings"]`:

```python
{
    "report": {
        "visual_findings": [
            {
                "agent": "visual-agent",
                "screen_id": "homepage",
                "status": "pass",
                "diff_ratio": 0.023,
                "sensitivity": 0.05,
                "screenshot": "/path/to/baseline.txt",
                "remediation_suggestions": [
                    "Visual comparison within sensitivity threshold."
                ]
            },
            {
                "agent": "visual-agent",
                "screen_id": "profile",
                "status": "fail",
                "diff_ratio": 0.187,
                "sensitivity": 0.05,
                "screenshot": "/path/to/diff.txt",
                "remediation_suggestions": [
                    "Visual deviation of 0.187 exceeds sensitivity 0.050. Review UI changes.",
                    "Consider updating baseline if the change is expected."
                ]
            }
        ]
    }
}
```

## Testing

Run the test suite:

```bash
pytest tests/test_visual_agent.py -v
pytest tests/test_visual_verification_core.py -v
pytest tests/test_orchestrator_integration.py -v
```

Run the example:

```bash
python examples/visual_agent_example.py
```

## Best Practices

1. **Baseline Management**
   - Create baselines in a controlled environment
   - Version control baselines alongside code
   - Review baseline changes during code reviews

2. **Sensitivity Tuning**
   - Start with the default 0.05 threshold
   - Adjust per-screen for dynamic content
   - Use stricter thresholds for critical UI components

3. **Integration Testing**
   - Run visual tests as part of CI/CD pipeline
   - Use hooks to log execution details
   - Store visual artifacts for debugging

4. **Troubleshooting**
   - Review diff maps for failed comparisons
   - Check remediation suggestions for guidance
   - Validate pixel data dimensions match baselines

## Error Handling

The visual agent handles the following error scenarios:

- **Dimension Mismatch**: Raises `VisualVerificationError` if baseline and image dimensions differ
- **Invalid Pixel Values**: Raises `VisualVerificationError` for values outside 0-255 range
- **Invalid Sensitivity**: Raises `ValueError` for sensitivity outside 0.0-1.0 range

## Performance Considerations

- Pixel comparisons are O(n*m) where n=height, m=width
- Baseline files are stored as text for human readability
- Consider using lower resolution images for faster processing
- Diff maps are only generated when comparisons fail

## Future Enhancements

- Support for color images (RGB/RGBA)
- Perceptual diff algorithms (e.g., SSIM)
- Screenshot capture integration with Playwright
- Baseline management UI
- Parallel execution for multiple screens
