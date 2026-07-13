# Critiqor Architecture Separation Audit

Audit date: 2026-07-13
Scope: the complete current `Critiqor` working tree, including tracked source,
untracked source, generated distributions, caches, and runtime artifacts.

The governing rule is that integration, observation, transport, schemas, CLI,
dashboard presentation, and extension surfaces stay public. Any implementation
that computes a diagnosis, score, causal explanation, benchmark, or
recommendation is private. The data types and callable boundary between those
areas stay public.

## PUBLIC

| Path | Reason |
| --- | --- |
| `.gitignore` | Public repository hygiene; prevents generated and sensitive runtime artifacts from being committed. |
| `LICENSE` | Public licensing metadata. The private repository must use its own proprietary license. |
| `README.md`, `CHANGELOG.md` | Public installation, workflow, compatibility, and release documentation. |
| `pyproject.toml`, `MANIFEST.in` | Public package build metadata and distribution allow/exclude rules. |
| `assets/Critiqor.png`, `assets/CritiqorOpenClawBanner.png`, `assets/dashboard-preview.png` | Public branding and documentation imagery; no reliability intelligence. |
| `critiqor/__init__.py` | Public SDK export surface. It must export contracts and client/runtime primitives only. |
| `critiqor/banner.py`, `critiqor/terminal_ui.py` | Public terminal presentation. |
| `critiqor/cli.py` | Public CLI command and UX orchestration. It must call the engine contract, never an implementation. |
| `critiqor/frameworks.py` | Public framework discovery/configuration and extension metadata. |
| `critiqor/runtime.py` | Public process supervision, log import, observation, dashboard orchestration, and export workflows. |
| `critiqor/openclaw.py` | Public OpenClaw process observation and event normalization. It contains no diagnosis decisions. |
| `critiqor/backend.py` | Public HTTP transport adapter for the hosted private engine. It contains no diagnosis decisions. |
| `critiqor/dashboard.py` | Public dashboard launcher and diagnosis artifact reader. UI/presentation remains public; it must not compute diagnosis fields. |
| `critiqor/session.py` | Public session lifecycle and artifact persistence after its direct private implementation import is removed. |
| `clawhub/critiqor-openclaw/index.js`, `openclaw.plugin.json`, `package.json` | Public standalone OpenClaw evidence collector/plugin. |
| `critiqor/clawhub/critiqor-openclaw/index.js`, `openclaw.plugin.json`, `package.json` | Public packaged mirror of the OpenClaw evidence plugin required by the PyPI artifact. |
| `vscode-extension/.vscodeignore`, `README.md`, `extension.js`, `package.json` | Public IDE integration and evidence collection. |
| `docs/pypi-release-0.2.1.md` | Public release procedure/documentation; no algorithms. |
| `demo.py`, `examples/simple_usage.py` | Public developer examples. They exercise integration APIs rather than private intelligence. |
| `tests/test_core.py` | Public-package behavior/contract tests after proprietary expected values and formulas are removed. Tests are excluded from wheels but can remain public for contributor confidence. |

## PRIVATE

| Path | Reason |
| --- | --- |
| `critiqor/local_diagnosis.py` | **Move.** Implements error/retry heuristics, trust and confidence formulas, impact/severity weighting, root-cause and recommendation generation, evidence-level inference, causal graph assembly, and diagnosis assembly. This is precisely Critiqor's proprietary intelligence. |
| `experiments/sandbox_eval.py` | **Move.** Internal evaluator experiment that describes evaluation dimensions, scoring, confidence, findings, and deployment recommendations; it is not a functioning public SDK example against the current exports. |
| Historical `critiqor/core.py` | Keep only in private history/repository. It implemented generic evaluation, scoring, failure detection, benchmarks, and certification logic. |
| Historical `critiqor/platform.py` | Keep only in private history/repository. It implemented ingestion analytics, leaderboards, benchmark distribution, and hosted dashboard data generation. |
| Historical local OpenClaw diagnosis functions (`diagnose_openclaw_events`, `build_openclaw_run_payload`, `build_openclaw_causal_graph`, `default_openclaw_benchmark_spec`) | Keep only in private history/repository. These expose failure detectors, scoring weights, readiness rules, causal analysis, and cost heuristics. |
| `runs/active_session.json`, `runs/run_001.json`, `runs/run_001/session.json`, `runs/run_001/diagnosis.json` (when present) | User/runtime data. Never source-controlled or distributed. These are private to the user, not private-engine source. |
| `clawhub/*/reports/` (when present) | Internal generated inspection/evaluation reports; excluded from distributions. |

## INTERFACES

These remain in the public repository because they define the stable boundary
without exposing implementation details.

| Path/symbol | Reason |
| --- | --- |
| `critiqor/schemas.py`: `RuntimeEvent`, `EvidenceSubmission`, `DiagnosisResult`, schema version strings | Shared request/result contracts used by integrations, the public client, private package, and hosted service. |
| New `critiqor/engine.py`: `DiagnosisEngine` protocol and engine resolver | Stable `generate(submission) -> DiagnosisResult` interface plus plugin/hosted-adapter selection. It contains no algorithm. |
| `critiqor/backend.py`: `BackendConfig`, public exceptions, hosted transport adapter | Stable remote implementation boundary. HTTP serialization is public; server intelligence is private. |
| Diagnosis JSON schema consumed by `critiqor/dashboard.py`, exports, and tests | Shared output contract. Field names and structure remain backward compatible while values are produced privately. |
| OpenClaw/IDE normalized event schema and plugin hook names | Shared evidence contract between public collectors and the private diagnosis engine. |

## GENERATED / DERIVED (DO NOT CLASSIFY AS SOURCE)

| Path | Treatment |
| --- | --- |
| `.git/` | Public repository metadata, not shipped as package content. Existing history may retain old proprietary code; removing it from the current tree does not erase history. A history rewrite is a separate, destructive security/release decision. |
| `critiqor.egg-info/*` | Generated packaging metadata. Rebuild after separation; do not hand-maintain or commit. |
| `dist/critiqor-0.2.1-py3-none-any.whl`, `dist/critiqor-0.2.1.tar.gz` | Existing public release artifacts containing a snapshot of older code. Replace/revoke as part of release operations; never treat them as editable source. |
| `critiqor/__pycache__/*`, `tests/__pycache__/*`, `.pytest_cache/` | Generated caches; exclude from source and packages. |

## Required boundary and compatibility decision

The public workflow remains:

```text
pip install critiqor
  -> critiqor agents
  -> critiqor monitor <framework>
  -> public observation/session artifact
  -> DiagnosisEngine public contract
       -> installed private plugin (internal builds), or
       -> hosted Critiqor HTTP adapter (public installs)
  -> unchanged diagnosis.json contract
  -> unchanged dashboard/export workflow
```

An entry-point/plugin contract plus hosted fallback best preserves the UX. It
lets internal/offline builds install the proprietary implementation while the
public PyPI package transparently uses the hosted engine. The public package
must never fall back to a local heuristic implementation.

## Separation gate

This audit is complete before source movement begins. The implementation phase
must satisfy all of the following:

1. Remove `critiqor.local_diagnosis` and every direct import of it from public source.
2. Add the public `DiagnosisEngine` contract and route finalization through it.
3. Place the moved implementation in a separately initialized, proprietary-licensed `critiqor-infra` repository.
4. Preserve evidence and diagnosis schema versions and CLI command names.
5. Build and inspect both wheel and sdist to prove private modules, tests, experiments, runs, and caches are absent.
6. Test hosted transport and an injected/private engine through the same contract.
