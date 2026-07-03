# Critiqor Public Package Boundary Audit

## Goal

The public PyPI package must let users run Critiqor while ensuring proprietary diagnosis, scoring, reliability, benchmark, root-cause, and leaderboard logic is not distributed.

## Classification

| Path | Classification | Reason |
| --- | --- | --- |
| `critiqor/cli.py` | Public | Command routing only. Parses CLI input and calls public runtime functions. |
| `critiqor/runtime.py` | Public | Supervises OpenClaw process, creates sessions, persists evidence, calls private backend, launches dashboard. |
| `critiqor/session.py` | Public | Session lifecycle and evidence artifact persistence. No local scoring after refactor. |
| `critiqor/openclaw.py` | Public | Evidence collection primitives only. No local diagnosis or benchmark logic. |
| `critiqor/backend.py` | Public | HTTP client for private Critiqor diagnosis backend. Contains transport only. |
| `critiqor/schemas.py` | Public | Stable public schemas for events and backend submissions. |
| `critiqor/dashboard.py` | Public | Local dashboard launcher and diagnosis artifact reader. Does not compute scores. |
| `critiqor/banner.py` | Public | CLI branding. |
| `critiqor/clawhub/critiqor-openclaw/*` | Public | Lightweight OpenClaw evidence plugin. Does not evaluate or score. |
| former `critiqor/core.py` | Private | Legacy generic evaluator, scoring, failure detectors, benchmark and certification logic. Removed from public package and should live only in a private backend repo/service. |
| former `critiqor/platform.py` | Private | Hosted index, ingestion, analytics, leaderboard, benchmark distribution and dashboard data generation. Removed from public package and should live only in a private backend repo/service. |
| former local OpenClaw diagnosis implementation | Private | OpenClaw diagnosis engine, failure taxonomy detectors, scoring, causal graph and benchmark logic. Removed from public package and should live only in a private backend repo/service. |
| `experiments/sandbox_eval.py` | Private | Experimental evaluation logic. Must not ship. |
| `tests/*` | Private/Internal | Internal tests can reference private implementation history. Not included in PyPI sdist/wheel. |
| `runs/*`, `.critiqor/*`, `critiqor-test/*` | Private/User Data | Local runtime artifacts and generated reports. Must never ship. |
| `clawhub/critiqor-openclaw/reports/*` | Private/Internal | Plugin inspection reports. Must not ship. |

## Modules Removed From The Public PyPI Package

The following modules were removed from `critiqor/` or excluded from the distribution:

- `critiqor.core` -> moved to `private_backend/core.py`
- `critiqor.platform` -> moved to `private_backend/platform.py`
- local OpenClaw diagnosis functions from `critiqor.openclaw` -> copied to `private_backend/openclaw_engine.py`
- `diagnose_openclaw_events`
- `build_openclaw_run_payload`
- `build_openclaw_causal_graph`
- `default_openclaw_benchmark_spec`
- local failure detectors, scoring weights, readiness rules, and cost analysis heuristics
- local leaderboard, analytics, certification, trend, and benchmark implementation

## New Package Boundary

```text
User
  -> public critiqor CLI
  -> OpenClaw runtime observer
  -> runs/<run_id>/session.json
  -> private Critiqor backend API
  -> runs/<run_id>/diagnosis.json
  -> local dashboard launcher
```

The public client sends evidence to the configured backend using `CRITIQOR_BACKEND_URL` and optional `CRITIQOR_API_KEY`. The backend returns dashboard-ready `diagnosis.json`.

## Packaging Controls

`MANIFEST.in` prunes tests, local run artifacts, experiments, generated plugin reports, and any local `private_backend/` working copy from source distributions. `setuptools` only packages the `critiqor` public client package.

## Failure Mode

If no backend is configured or reachable, `critiqor finalize` does not run local proprietary logic. It prints a backend configuration error and leaves collected evidence available in the run artifact.
