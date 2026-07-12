# Changelog

## 0.1.0 - 2026-05-29

Initial V1 release of Critiqor.

- Added the `Critiqor` wrapper for existing agents.
- Added the `CritiqorResult` result object with `answer`, `confidence`, `trust_level`, and `critique`.
- Added one agent-focused reliability critique pass after the base agent answer.
- Added multi-dimensional scoring for hallucination risk, reasoning, tool use, consistency, and task completion.
- Added trust labels: `High`, `Moderate`, and `Low`.
- Added support for agents with `run`, `invoke`, `generate`, or `__call__`.
- Added README onboarding, simple usage example, sandbox experiment, and focused tests.
# 0.2.0

- Add explicit framework selection with `critiqor agents`.
- Add saved observation-method updates with `critiqor config`.
- Add launch monitoring for OpenClaw, Claude Code, Codex CLI, and custom frameworks.
- Add native runtime log file/folder import and evidence normalization.
- Keep diagnosis generation and dashboard behavior framework-agnostic.
