# Changelog

## 0.2.3 - 2026-07-14

- Consolidate the local diagnosis engine into the public repository.
- Split diagnosis classification, analysis, recommendations, and assembly into focused modules.
- Remove split-era hosted-backend and private-plugin adapters.
- Generate a new private dashboard access code for each dashboard session.
- Point `critiqor finalize` and `critiqor dashboard` at the current hosted dashboard.
- Upload and verify the selected `diagnosis.json` before opening `/?run_id=<run_id>`.
- Add dashboard and ingest URL overrides for self-hosted deployments and release verification.

## 0.2.2 - 2026-07-13

- Restore offline finalization without requiring a backend URL or API key.
- Preserve private diagnosis plugins as the preferred in-process engine.
- Fall back to a portable dashboard diagnosis when a configured hosted backend is unavailable.
- Always complete valid evidence sessions and write both `session.json` and `diagnosis.json` for the dashboard.
- Preserve framework metadata, runtime errors, supporting evidence, recommendations, and causal graph data in fallback diagnoses.

## 0.1.0 - 2026-05-29

Initial V1 release of Critiqor.

- Added the `Critiqor` wrapper for existing agents.
- Added the `CritiqorResult` result object with `answer`, `confidence`, `trust_level`, and `critique`.
- Added one agent-focused reliability critique pass after the base agent answer.
- Added multi-dimensional scoring for hallucination risk, reasoning, tool use, consistency, and task completion.
- Added trust labels: `High`, `Moderate`, and `Low`.
- Added support for agents with `run`, `invoke`, `generate`, or `__call__`.
- Added README onboarding, simple usage example, sandbox experiment, and focused tests.
# 0.2.1

- Add explicit framework selection with `critiqor agents`.
- Add saved observation-method updates with `critiqor config`.
- Add launch monitoring for OpenClaw, Claude Code, Codex CLI, and custom frameworks.
- Add native runtime log file/folder import and evidence normalization.
- Keep diagnosis generation and dashboard behavior framework-agnostic.
