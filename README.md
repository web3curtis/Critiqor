<p align="center">
  <img src="assets/Critiqor.png" alt="Critiqor logo" width="120" />
</p>

<h1 align="center">Critiqor</h1>

<p align="center">
  <strong>Runtime Intelligence for AI Agents</strong>
</p>

<p align="center">
  Observe. Diagnose. Improve.
</p>

<p align="center">
  <a href="https://pypi.org/project/critiqor/"><img alt="PyPI" src="https://img.shields.io/pypi/v/critiqor?color=20d6ad"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="Status" src="https://img.shields.io/badge/status-alpha-orange">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

<p align="center">
  <code>pip install critiqor</code>
</p>

Critiqor observes AI agents while they run, captures runtime evidence, and turns that evidence into reliability insight developers can act on.

Instead of relying on model self-reporting, Critiqor helps you see what actually happened during execution: tool use, retries, runtime events, failures, cost signals, and reliability patterns.

---

## Introduction

AI agents are powerful, but final answers do not tell the whole story.

An agent can produce a useful response while hiding execution problems underneath: repeated tool calls, ignored outputs, memory drift, retry loops, unnecessary cost, or unstable runtime behavior.

Critiqor is built for developers who want to evaluate the work, not just the answer.

With Critiqor, you can:

- observe agent execution in real time
- diagnose reliability issues from runtime evidence
- review historical runs
- compare behavior across iterations
- improve agents with measurable feedback

---

## Dashboard Preview

![Critiqor dashboard preview](assets/dashboard-preview.png)

After an observation session, Critiqor opens a dashboard that gives you a clear reliability report.

You can review:

- **Executive Summary** - the fast answer on whether the run looks healthy
- **Trust Assessment** - confidence and readiness signals
- **Primary Diagnosis** - what went wrong, if anything did
- **Runtime Evidence** - observed agent activity behind the conclusion
- **Recommendations** - practical next steps for improvement
- **Historical Runs** - previous observations for comparison

---

## Installation

Install Critiqor from PyPI:

```bash
pip install critiqor
```

Check the CLI:

```bash
critiqor help
```

---

## Quick Start

### 1. Start an observation session

```bash
critiqor monitor openclaw
```

Critiqor starts observing before the agent begins work, then launches OpenClaw in the same terminal.

### 2. Use OpenClaw normally

Work with your agent as usual. Critiqor stays in the background and records runtime evidence.

### 3. Finalize the observation

```bash
critiqor finalize
```

Critiqor completes the observation, generates a reliability report, and opens the dashboard.

### 4. Reopen previous runs

List historical evaluations:

```bash
critiqor runs
```

Open the latest dashboard:

```bash
critiqor dashboard
```

Open a specific run:

```bash
critiqor dashboard run_001
```

---

## Features

### Runtime Observation

Capture what the agent actually did during execution, including tool activity, retries, runtime events, and failures.

### Evidence-Backed Diagnosis

Understand reliability issues through observed behavior rather than generated explanations after the fact.

### Trust Assessment

See whether a run looks healthy, needs review, or should be treated as risky.

### Historical Runs

Review previous observations and track whether reliability is improving over time.

### Cost Awareness

Spot repeated calls, redundant work, and signs of operational waste.

### Dashboard-First Review

Move from terminal execution to a visual report designed for debugging, review, and team communication.

---

## When to Use

Use Critiqor when you need to:

- validate agent changes before release
- debug failed or suspicious runs
- compare prompt iterations
- test new tools or skills
- catch regressions in agent behavior
- measure reliability improvements over time
- explain agent behavior to teammates or stakeholders
- review whether an agent is ready for production workflows

---

## Trust & Privacy

Critiqor is designed around explicit observation.

It focuses on runtime behavior produced by the connected agent session. Developers remain in control of when observation starts, when it ends, and which results they review or share.

Critiqor does **not** aim to replace developer judgment. It provides evidence-backed reliability signals so teams can make better decisions.

Principles:

- observation should be explicit
- conclusions should be backed by runtime evidence
- developers should be able to review what happened
- sensitive workflow data should remain under user control
- reliability reports should support human decision-making, not hide it

---

## Philosophy

Critiqor is built on a simple belief:

> Reliable agents should be evaluated by what they do, not what they say they did.

That means:

- evaluate observable behavior
- prioritize evidence over self-reporting
- make reliability explainable
- improve through measurement
- help developers see the execution trail behind the answer

---

## FAQ

### What is Critiqor?

Critiqor is an AI Agent Runtime Intelligence Platform. It observes agent execution, captures runtime evidence, and helps developers diagnose reliability issues.

### Which frameworks are supported?

Critiqor currently supports OpenClaw-focused observation workflows.

### How do I install Critiqor?

```bash
pip install critiqor
```

### What does the dashboard show?

The dashboard shows an executive summary, trust assessment, primary diagnosis, runtime evidence, recommendations, and historical runs.

### How should I interpret trust levels?

Trust levels are reliability signals based on observed runtime behavior. They help you decide whether a run looks healthy, needs review, or may be risky.

### Can I review previous runs?

Yes. Use:

```bash
critiqor runs
critiqor dashboard run_001
```

### Does Critiqor replace tests?

No. Critiqor complements tests by showing what happened during an agent run. Use it alongside unit tests, integration tests, evals, and human review.

### How do I report bugs?

Open a GitHub issue with:

- your Critiqor version
- your Python version
- the command you ran
- what you expected
- what happened instead

---

## Contributing

Critiqor is early and evolving quickly.

Useful contributions include:

- bug reports
- documentation improvements
- OpenClaw workflow feedback
- dashboard usability feedback
- framework integration requests

If you are proposing a larger change, please open an issue first so the direction can be discussed.

---

## License

Critiqor is released under the MIT License. See [LICENSE](LICENSE) for details.
