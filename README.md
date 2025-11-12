# MindMarionette

## Project Overview

MindMarionette is a fully autonomous QA agent that revolutionizes web application testing through AI-driven automation. By leveraging advanced language models and intelligent test orchestration, MindMarionette transforms the way QA teams approach quality assurance, enabling comprehensive, adaptive, and self-healing test scenarios that evolve with your application.

## System Overview

MindMarionette is built on a modular, agent-based architecture that harnesses the power of AutoGen as its foundational framework. This architecture enables seamless coordination between specialized agents, each optimized for specific testing domains. The system employs a sophisticated workflow orchestrator that manages complex test scenarios, intelligently coordinates multiple agents, and generates comprehensive reports—all while maintaining the flexibility to adapt to evolving application behavior.

## Specialized Agents

### Visual Testing Agent
Analyzes visual elements and layout consistency across the application, ensuring that UI components render correctly and maintain design integrity throughout the testing lifecycle.

### Accessibility Agent
Ensures compliance with WCAG 2.2 AA standards, identifying accessibility barriers and recommending remediation strategies to create inclusive web experiences for all users.

### Performance Agent
Monitors Core Web Vitals and leverages Lighthouse analysis to identify performance bottlenecks, optimize load times, and ensure applications meet modern performance benchmarks.

### Security Agent
Integrates ZAP Proxy and OWASP vulnerability scanning to identify security weaknesses, validate secure configurations, and provide detailed remediation guidance for discovered vulnerabilities.

### Cross-Browser Agent
Tests application compatibility across Chromium, Firefox, and WebKit engines, ensuring consistent behavior and visual rendering across diverse browser environments.

## Core Modules

### Comprehensive Workflow Orchestrator
Utilizes AutoGen agent coordination to manage complex test scenarios, route tasks to specialized agents, aggregate results, and maintain coherent test execution flows across multiple testing domains.

### DOM Analyzer
Performs deep analysis of the Document Object Model to extract element properties, identify interactive components, and build comprehensive models of page structure for intelligent test execution.

### Goal-Based Action Executor
Translates high-level test objectives into precise, executable actions on web elements, managing state transitions and validating expected outcomes throughout test execution.

### Test Data Generator
Creates realistic and comprehensive test data sets tailored to application requirements, supporting scenario generation, edge case testing, and data-driven test execution.

### Visual Verification
Performs pixel-perfect visual comparisons, captures baseline images, detects visual regressions, and validates UI consistency across test runs and browser environments.

### Report Generator
Produces comprehensive, actionable test reports with detailed metrics, visual evidence, failure analysis, and recommendations for continuous improvement.

## Key Capabilities

- **Natural Language Understanding**: Interprets test requirements in natural language and autonomously translates them into executable test scenarios
- **Intelligent Element Location**: Automatically discovers and interacts with dynamic UI elements without brittle XPath or CSS selectors
- **Smart Test Data Generation**: Creates contextually appropriate test data that covers normal use cases, edge cases, and boundary conditions
- **Visual Verification**: Performs regression detection through intelligent visual comparison and baseline management
- **GDS Compliance Testing**: Validates adherence to Government Digital Service (GDS) design principles and standards
- **Self-Healing**: Automatically adapts to minor UI changes, reducing flaky tests and maintenance overhead
- **Comprehensive Reporting**: Generates detailed reports with metrics, screenshots, and actionable insights for stakeholders
- **Performance Optimization**: Continuously monitors and analyzes application performance metrics for optimization opportunities

## Operating Modes

### Goal-Based Mode
Define high-level testing objectives and let MindMarionette autonomously determine the optimal testing strategy, navigate the application, and validate outcomes.

### Exploratory Mode
Enable the agent to explore the application freely, discovering edge cases, potential issues, and unusual behaviors while documenting findings in real-time.

### Test Case Mode
Provide explicit step-by-step test scenarios that MindMarionette executes with precision, maintaining detailed execution logs and validating each assertion.

## External Integrations

- **Playwright**: Cross-browser automation and interaction with web applications
- **Google Gemini AI**: Advanced language model powering natural language understanding and intelligent decision-making
- **Axe-Core**: Comprehensive accessibility analysis and WCAG compliance validation
- **ZAP Proxy**: Security vulnerability scanning and OWASP compliance testing
- **Lighthouse**: Performance metrics analysis and web vitals measurement

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    MindMarionette System                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Natural Language Interface                     │ │
│  │          (Test Requirements & Specifications)              │ │
│  └────────────────────────────────────────────────────────────┘ │
│                            ▲                                     │
│                            │                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │            Workflow Orchestrator (AutoGen)                 │ │
│  │         (Agent Coordination & Task Management)             │ │
│  └────────────────────────────────────────────────────────────┘ │
│         ▲              ▲              ▲              ▲           │
│         │              │              │              │           │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐ │
│  │   Visual     │Accessibility │ Performance  │   Security   │ │
│  │   Testing    │    Agent     │    Agent     │    Agent     │ │
│  │    Agent     │  (WCAG 2.2)  │  (Web Vitals)│ (ZAP/OWASP) │ │
│  └──────────────┴──────────────┴──────────────┴──────────────┘ │
│         │              │              │              │           │
│         ▼              ▼              ▼              ▼           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Cross-Browser Agent                            │ │
│  │      (Chromium, Firefox, WebKit)                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │                                                        │
│         ▼                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │             Core Execution Modules                          │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │ • DOM Analyzer                                             │ │
│  │ • Goal-Based Action Executor                              │ │
│  │ • Test Data Generator                                     │ │
│  │ • Visual Verification                                     │ │
│  │ • Report Generator                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │                                                        │
│         ▼                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │         External Integrations & Tools                       │ │
│  ├────────────────────────────────────────────────────────────┤ │
│  │ • Playwright (Browser Automation)                          │ │
│  │ • Google Gemini AI (Language Understanding)                │ │
│  │ • Axe-Core (Accessibility)                                │ │
│  │ • ZAP Proxy (Security)                                    │ │
│  │ • Lighthouse (Performance)                                │ │
│  └────────────────────────────────────────────────────────────┘ │
│         │                                                        │
│         ▼                                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                  Target Web Application                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Getting Started

To begin using MindMarionette for your QA automation needs, ensure you have the following prerequisites installed:

- Node.js (v16 or higher)
- Playwright browsers
- Python 3.8+ (for AI agent components)

Refer to the project documentation for detailed setup instructions, configuration options, and usage examples specific to your testing requirements.

## Contributing

We welcome contributions to MindMarionette! Please review the contribution guidelines in our CONTRIBUTING.md file before submitting pull requests.

## License

MindMarionette is licensed under the MIT License. See LICENSE file for details.
