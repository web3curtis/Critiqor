# Changelog

## 0.2.19 - 2026-09-03

Chrome/WebMCP live observation release.

- Added `critiqor monitor webmcp` for real-time WebMCP registry, invocation,
  outcome, reconciliation, and authoritative-effect evidence from an explicitly
  configured Chrome remote-debugging endpoint.
- Added externally controlled, one-shot response-stage fault injection bound to
  an exact mutation URL, HTTP method, and consequential tool. Concurrently
  ambiguous correlations are refused.
- Kept consequential errors and cancellations `unknown` until authoritative
  application state reconciles the effect.
- Invalidated stale WebMCP discovery across top-level navigation and surfaced
  unexpected debugger disconnects.
- Added startup validation so unavailable WebMCP/CDP domains fail before a
  Critiqor session is created.
- Added `websocket-client>=1.8` as a package dependency and documented the
  dedicated Chrome profile workflow.

## 0.2.18 - 2026-09-01

WebMCP runtime evaluation and dashboard review release.

- Dashboard pages bind to the selected `run_id` only. Diagnosis, Playbook, and
  Evidence now share the same Focus run dropdown, and sidebar navigation keeps
  that query so another run is never substituted.
- Playbook shows the generated `improvement_playbook.md` plus visual
  recommendation cards from the selected run. Missing fields stay unavailable.
- Engineer Brief, Executive Summary, and Agent Health cards open the same
  keyboard-accessible detail view. Primary Diagnosis no longer renders a
  causal graph.
- Copy Fix Prompt remains a detailed, artifact-backed remediation prompt.
- `critiqor dashboard` prefers the bundled production dashboard build on port
  51703 and stops a leftover dashboard process that occupies that port but
  cannot serve the selected run.

## 0.2.16 - 2026-08-04

Runtime memory evaluation release.

- Added a local Memory Evaluator that analyzes memory behavior from runtime
  evidence already captured during Critiqor observation.
- Added memory utilization findings to the existing Diagnosis workflow,
  including score, confidence, root cause, evidence, runtime impact, and
  engineering explanation.
- Expanded memory evidence handling so retrieved, injected, referenced, unused,
  irrelevant, missed, created, ignored, and not-stored memory events can be
  explained from their underlying runtime telemetry.
- Added memory-specific playbook recommendations, verification steps, expected
  improvement, trade-offs, and alternatives.
- Enriched Copy Fix Prompt output with observed memory behavior, supporting
  evidence, suggested architectural improvement, testing strategy, and success
  criteria.
- Bumped the required Core Engine dashboard version to 0.2.16 so PyPI users see
  the matching memory diagnosis and evidence experience.

## 0.2.11 - 2026-07-31

Runtime diagnosis experience and terminal accessibility release.

- Reframed the dashboard around an immediate production verdict, evidence-backed
  primary diagnosis, run-specific improvement playbook, copyable fix prompt,
  and chronological improvement verification.
- Added current-versus-previous comparisons for trust, hallucination risk, tool
  reliability, and reasoning consistency.
- Moved runtime timelines, tool activity, memory, costs, and session metadata
  into a supporting evidence layer.
- Removed the Trust & Reliability Framework and Security Concerns dashboard
  pages.
- Added automatic light/dark terminal theme inference using `COLORFGBG`, with
  `CRITIQOR_CLI_THEME=light|dark` as a deterministic override.
- Replaced terminal-default and low-contrast greys with explicit semantic
  primary, secondary, success, warning, and error colours for each theme.

## 0.2.7 - 2026-07-29

Quality and production-readiness release. No workflow replacement is required.

- Preserved the `monitor -> finalize -> dashboard` workflow and added
  `critiqor doctor` preflight checks.
- Restored OpenClaw, Claude Code, and Codex CLI framework monitoring
  compatibility.
- Added bounded secret redaction, event hash chains, evidence digests, and
  signed evaluation manifests.
- Added strict backend response validation and fail-closed deployment policy
  checks.
- Prevented incomplete lifecycle-only observations from receiving a
  production-ready verdict.
- Added evidence-linked diagnoses with counterevidence, alternative
  hypotheses, actionable remediation, verification steps, and conditional
  expected improvement.
- Improved crash recovery, concurrent event handling, malformed-log behavior,
  and million-event streaming integrity verification.
- Prepared dashboard support for evidence health, concise Engineer Briefs,
  tenant-scoped durable state, signed ingest verification, audited deletion,
  keyboard navigation, and reduced motion.
- Added 120 deterministic regression cases and a separate 24-case internal
  detector-independent holdout.

The private diagnosis backend remains excluded from the public distribution.

## 0.1.0 - 2026-05-29

Initial V1 release of Critiqor.

- Added the `Critiqor` wrapper for existing agents.
- Added the `CritiqorResult` result object with `answer`, `confidence`, `trust_level`, and `critique`.
- Added one agent-focused reliability critique pass after the base agent answer.
- Added multi-dimensional scoring for hallucination risk, reasoning, tool use, consistency, and task completion.
- Added trust labels: `High`, `Moderate`, and `Low`.
- Added support for agents with `run`, `invoke`, `generate`, or `__call__`.
- Added README onboarding, simple usage example, sandbox experiment, and focused tests.
# 0.2.12 - 2026-08-01

- Restored functional `critiqor agents` and `critiqor config` framework configuration workflows.
- Scoped dashboard diagnoses, causal analysis, evidence, and fix guidance to the selected runtime.
- Added a visible, copyable run-specific fix prompt and higher-contrast color-coded diagnosis sections.
- Simplified dashboard settings and added official Documentation, Website, and Repository links.
- Updated Critiqor dashboard branding and release metadata.
# 0.2.13 - 2026-08-01

- Improved diagnosis contrast by limiting section colours to outer cards and using white nested information cards.
- Fixed collapsed sidebar layout so only navigation icons remain and the active page stays highlighted.
- Updated the public website link to `https://critiqor-runtime-insight.vercel.app/`.
- Made `critiqor finalize` and `critiqor dashboard` require the updated Core Engine dashboard and open it on port 51703 with the selected run.
# 0.2.14 - 2026-08-01

- Finalization now generates a local diagnosis when the optional hosted backend is unavailable.
- Dashboard launch ignores stale server records on other ports and consistently opens port 51703.
- Terminals without a detectable background now default to high-contrast black primary text while retaining orange and grey accents.
# 0.2.15 - 2026-08-01

- Added persistent Private, Shared, Anonymous, and Public visibility configuration.
- Added per-launch private access tokens and shared invite codes with server-side API enforcement.
- Added anonymous artifact and identity redaction in the dashboard API.
- Added dashboard login flow and live visibility details.
- Refined dark-mode surfaces and diagnosis contrast across the dashboard.
