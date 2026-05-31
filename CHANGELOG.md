# Changelog

## 0.1.0 - 2026-05-29

Initial V1 release of Critiqor.

- Added the `Critiqor` wrapper for existing agents.
- Added the `CritiqorResult` result object with `answer`, `confidence`, and `critique`.
- Added one self-critique pass after the base agent answer.
- Added confidence scoring from `0` to `100` using the V1 rubric.
- Added support for agents with `run`, `invoke`, `generate`, or `__call__`.
- Added README onboarding, simple usage example, sandbox experiment, and focused tests.
