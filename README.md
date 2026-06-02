# Critiqor

![Critiqor](assets/Critiqor.png)

Evidence-first reliability feedback for AI agents.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-alpha-orange)

Critiqor evaluates observable agent behavior instead of relying only on agent
self-reporting. It can score a final response, analyze supplied execution
traces, collect evidence through lightweight SDK instrumentation, explain why a
run failed, recommend fixes, compare releases, rank agents across categories,
debug causal failure chains, run benchmarks, certify reliability, gate
deployments, and track reliability over time.

The core rule: captured execution data is stronger evidence than post-hoc
explanations.

## Quick Start

### Install

From the cloned repo root, run an editable install so local code changes are used immediately:

```bash
python -m pip install -e .
```

After release, install from PyPI instead:

```bash
pip install critiqor-ai
```

### Minimal Example

```python
from critiqor import Critiqor

agent = Critiqor(TheirExistingAgent(model="llama3.2"))  # wrap your existing agent
result = agent.run("Explain vector databases in one paragraph.")

print(result.answer)       # original agent response
print(result.confidence)   # 0-100 evidence-weighted reliability score
print(result.evaluation_confidence)
print(result.failure_causes)
print(result.deployment_recommendation)
print(result.trust_level)  # "High", "Moderate", or "Low"
print(result.critique)     # structured reliability critique
```

### Trace Evaluation

Use this when you already have tool logs from your own runner.

```python
from critiqor import Critiqor

result = Critiqor(evaluator_agent).evaluate(
    prompt="What is the weather in Sydney?",
    response="Sydney is mild today.",
    tool_calls=[
        {"tool": "search", "args": {"query": "Sydney weather"}}
    ],
    tool_outputs=[
        {"tool": "search", "output": "Weather report text"}
    ],
)

print(result.evidence.evidence_level)  # "trace_available"
print(result.critique.tool_reliability)
```

### SDK Instrumentation

Use `monitor()` when you want Critiqor to capture execution data during a run.

```python
from critiqor import Critiqor, monitor

with monitor("Calculate the total.") as recorder:
    add = recorder.wrap_tool("add", lambda a, b: a + b)
    response = f"The total is {add(2, 3)}."
    evidence = recorder.finish(response=response)

result = Critiqor(evaluator_agent).evaluate(**evidence.to_dict())

print(result.evidence.evidence_level)  # "fully_instrumented"
```

### Reliability Intelligence

Use the higher-level helpers when you want to understand changes across runs
instead of manually reading traces.

```python
from critiqor import (
    analyze_trends,
    benchmark_run,
    compare_runs,
    load_evaluations,
    save_evaluation,
)

save_evaluation(result, path="critiqor_evaluations.jsonl", agent_id="support-bot")

history = load_evaluations("critiqor_evaluations.jsonl", agent_id="support-bot")
trend = analyze_trends(history)
percentile = benchmark_run(result, history)

comparison = compare_runs(history[-2], history[-1])

print(trend.summary)
print(percentile)
print(comparison.summary)
```

### Benchmark And Certification

Create reproducible benchmark suites for coding, research, customer support, or
general-purpose agents.

```python
from critiqor import CritiqorBenchmark, certify_run

benchmark = CritiqorBenchmark(
    name="Coding Benchmark",
    agent_type="coding",
)

benchmark_result = benchmark.run(agent)
certification = certify_run(benchmark_result, percentile=benchmark_result.percentile)

print(benchmark_result.trust_score)
print(benchmark_result.percentile)
print(certification.certification_level)
print(certification.markdown_badge)
```

### Cross-Agent Leaderboards

V1.3 adds a networked ranking layer so teams can compare agents across the same
category.

```python
from critiqor import AgentProfile, generate_leaderboard, register_agent, submit_run

register_agent(
    AgentProfile(
        agent_id="agent_123",
        name="Alpha Coder",
        category="coding_agents",
    )
)

submit_run("agent_123", result)

leaderboard = generate_leaderboard(category="coding_agents")

print(leaderboard.to_dict())
```

Leaderboard entries include rank, agent id, trust score, percentile, category,
and run count.

### Causal Failure Graphs

V1.3 also adds directed causal graphs for diagnostic debugging.

```python
from critiqor import build_causal_graph, explain_failure_chain

graph = build_causal_graph(
    trace=[
        {"event": "prompt_ambiguity"},
        {"event": "tool_start", "tool": "search"},
        {"event": "tool_end", "output": "irrelevant data"},
    ],
    failure_event="ignored_tool_output",
    run_id="run_123",
)

print(graph.to_dict())
print(explain_failure_chain("run_123"))
```

Example explanation:

```text
Prompt was ambiguous -> Tool returned evidence -> Agent ignored weak or retrieved evidence -> Final answer hallucinated
```

### Hosted Reliability Index

V2 adds a dependency-free scaffold for the hosted Agent Reliability Index:

```text
SDK -> ingestion -> storage -> analytics -> leaderboard -> API -> dashboard data
```

```python
from critiqor import AgentReliabilityIndex

index = AgentReliabilityIndex()

accepted = index.ingest_run(
    {
        "tenant_id": "tenant_a",
        "agent_id": "agent_123",
        "agent_name": "Alpha Coder",
        "category": "coding_agents",
        "local_run_id": "run_001",
        "trust_score": 91,
        "scores": {"reasoning": 90, "tool_reliability": 92},
        "failure_causes": [],
    }
)

leaderboard = index.api.get_leaderboard("coding_agents")
agent = index.api.get_agent("agent_123")
dashboard = index.dashboard.ecosystem_view("coding_agents")
```

The in-memory platform components model the future hosted product:

- `IngestionAPI`: validates, normalizes, deduplicates, assigns global run ids,
  enforces benchmark spec versioning, emits events, and stores raw + processed
  run data.
- `ReliabilityIndexStore`: stores tenants, agents, immutable runs, failures,
  causal graphs, and benchmark distribution metadata. It can append every
  mutation to JSONL for replayable history.
- `AnalyticsEngine`: computes percentiles, trends, dominant failure modes,
  failure distributions, regressions, global distributions, benchmark stats, and
  cross-agent comparisons.
- `LeaderboardService`: exposes tenant-aware, public, global, and
  benchmark-specific category rankings.
- `PublicAPILayer`: models `GET /agent/{id}`, trends, failures, compare, and
  leaderboard/benchmark calls.
- `DashboardDataLayer`: produces dashboard-ready leaderboard, agent detail, and
  ecosystem views without building UI yet.

V2 also adds:

- `TenantRecord`: multiple organizations with isolated data.
- `EventStream`: deterministic events for `RunIngested`, `FailureDetected`,
  `CausalGraphGenerated`, `LeaderboardUpdated`, and `BenchmarkComputed`.
- `BenchmarkSpec`: versioned weighted benchmark normalization.
- Public benchmark mode: opt-in global leaderboard participation and anonymized
  aggregate comparison.

Backend constraints are explicit: Critiqor returns structured JSON only. It does
not render UI, generate images/charts, or use an LLM for ranking decisions.

## What Critiqor Evaluates

Critiqor keeps the rubric fixed so repeated runs use consistent criteria. When
traces are available, they are prioritized over the final response.

| Dimension | What It Checks |
| --- | --- |
| `hallucination` | Unsupported, fabricated, or overconfident claims |
| `reasoning` | Coherent reasoning and low reasoning drift |
| `tool_reliability` | Correct tool selection, outputs, errors, and ignored evidence |
| `consistency` | Internal contradictions or unstable claims |
| `task_completion` | Whether the answer actually satisfies the prompt |
| `confidence_calibration` | Whether confidence is supported by available evidence |
| `execution_efficiency` | Redundant calls, loops, retries, and avoidable overhead |

`tool_use` remains available as a backward-compatible alias for
`tool_reliability`.

The overall `confidence` is evidence-weighted. Response-only evaluations are
intentionally lower confidence than trace-backed or fully instrumented runs.

## Failure Cause Engine

Every result includes structured causes that explain trust-score penalties:

```python
result.failure_causes
```

Each cause includes root-cause analysis and a fix recommendation:

```json
{
  "type": "redundant_tool_calls",
  "severity": "high",
  "impact": -15,
  "description": "search tool called 2 times with identical arguments.",
  "root_cause": {
    "description": "The agent repeated the same tool request instead of reusing prior results.",
    "impact": "Reduced execution efficiency and increased operational cost.",
    "trust_penalty": -15,
    "recommended_fix": "Cache tool outputs and prevent identical requests within the same execution."
  },
  "recommendation": "Cache tool outputs and prevent identical requests within the same execution."
}
```

Built-in detectors currently cover:

- `redundant_tool_calls`: same tool and same arguments repeated.
- `ignored_tool_output`: tool evidence not reflected in the final response.
- `runtime_failures`: tool errors, timeout events, and retries.
- `unsupported_claims`: specific claims without captured supporting evidence.
- `confidence_mismatch`: high-certainty language with weak or ignored evidence.

## Run Comparison, Trends, And Benchmarking

Compare prompt versions, model upgrades, agent releases, or framework migrations:

```python
comparison = compare_runs(previous_result, current_result)

print(comparison.trust_change)
print(comparison.changes)
print(comparison.summary)
```

Persist evaluations as JSON Lines:

```python
record = save_evaluation(result, path="critiqor_evaluations.jsonl", agent_id="agent-v1")
records = load_evaluations("critiqor_evaluations.jsonl", agent_id="agent-v1")
```

Analyze whether reliability is improving or declining:

```python
trend = analyze_trends(records)

print(trend.trust_trend)
print(trend.hallucination_change)
print(trend.tool_reliability_change)
print(trend.reasoning_change)
```

Benchmark a run against prior evaluations:

```python
percentile = benchmark_run(result, records)
```

`add_benchmark(result, records)` returns a copy of the result with
`benchmark_percentile` populated.

`submit_run(agent_id, evaluation_result)` accepts ordinary evaluations,
benchmark results, persisted records, or compatible dictionaries, so benchmark
and leaderboard workflows can share the same run data.

## Reliability Certification

`certify_run(...)` produces a standardized reliability badge and certification
level.

| Level | Minimum Trust | Minimum Percentile | Minimum Evaluation Confidence | Evidence Requirement | Failure Limit |
| --- | --- | --- | --- | --- | --- |
| `bronze` | `70` | `50` | `55` | response-only or better | no unsafe production recommendation |
| `silver` | `80` | `70` | `70` | trace preferred | no high-severity failures |
| `gold` | `90` | `85` | `80` | trace available or better | no high-severity failures |
| `platinum` | `95` | `95` | `90` | fully instrumented | no high-severity failures |

```python
from critiqor import certification_criteria_table, certify_run

certification = certify_run(result, percentile=88)
criteria = certification_criteria_table()
```

## Deployment Recommendations

Each result includes a decision-oriented recommendation:

```python
result.deployment_recommendation
```

Possible values:

- `safe_to_deploy`
- `review_recommended`
- `unsafe_for_production`

The recommendation considers trust score, evaluation confidence, and severe
failure causes. This turns raw reliability data into an action engineers and
managers can both use.

## CI/CD Checks

The package exposes a CLI entrypoint:

```bash
critiqor check --evaluations critiqor_evaluations.jsonl --minimum-trust-score 80
```

Policy files can be JSON or a simple YAML-style key/value file:

```yaml
minimum_trust_score: 80
maximum_hallucination_risk: 20
minimum_tool_reliability: 75
block_high_severity_failures: true
```

Programmatic policy checks are also available:

```python
from critiqor import check_policy

result = check_policy(evaluation, {"minimum_trust_score": 80})
```

## Evidence Modes

| Mode | Input | Evidence Level | Best For | Limitation |
| --- | --- | --- | --- | --- |
| Response Evaluation | `prompt`, `response` | `response_only` | Basic answer checks | Cannot validate tool behavior or loops |
| Trace Evaluation | `prompt`, `response`, `tool_calls`, `tool_outputs` | `trace_available` | Tool selection, ignored outputs, redundant calls | Requires manual trace collection |
| SDK Instrumentation | Captured runtime events and metrics | `fully_instrumented` | Production-grade reliability evidence | Requires instrumentation setup |

Critiqor uses this evidence hierarchy:

1. Captured execution traces
2. Tool call logs
3. Tool outputs
4. Runtime metrics
5. Final response
6. Agent self-explanations

## Framework And OpenTelemetry Adapters

`CritiqorTracer` records common agent lifecycle events:

```text
agent_start
agent_step
tool_start
tool_end
llm_call
agent_finish
retry
error
```

It can attach to frameworks that expose `on(event, callback)` or
`subscribe(event, callback)`, and can be mapped to LangGraph, LangChain, OpenAI
Agents SDK, CrewAI, AutoGen, PydanticAI, and Mastra callbacks.

```python
from critiqor import CritiqorTracer

tracer = CritiqorTracer(agent)
```

For observability pipelines, `OpenTelemetryAdapter` can ingest
OpenTelemetry-like span dictionaries and convert LLM calls, tool calls, tool
outputs, retries, errors, latency, and token usage into Critiqor evidence.

For frameworks with event hooks, `attach_critiqor(agent)` is a convenience alias
for `CritiqorTracer(agent)`.

`Critiqor.auto_attach(agent)` also attempts framework detection for LangGraph,
CrewAI, OpenAI Agents SDK, PydanticAI, AutoGen, Mastra, LangChain, and generic
event-based agents.

## Shared Benchmark Dataset

Benchmark contribution is opt-in and anonymized. Critiqor only exports aggregate
metrics:

```python
from critiqor import prepare_benchmark_contribution, save_benchmark_contribution

contribution = prepare_benchmark_contribution(
    result,
    agent_type="coding",
    certification_level="gold",
)

save_benchmark_contribution(contribution)
```

The contribution does not include prompts, private outputs, tool outputs, or
sensitive content.

## Dashboard Data And Insights

V1.2 adds the data layer for a future dashboard without building UI yet:

```python
from critiqor import ReliabilityDashboardData, generate_insights

dashboard = ReliabilityDashboardData(run_history=records, benchmarks=[benchmark_result])

dashboard.get_trends()
dashboard.get_benchmarks()
dashboard.get_failures()

insight = generate_insights(records)
print(insight.summary)
```

## Networked Reliability Intelligence

V1.3 turns Critiqor from a per-run evaluator into a small networked reliability
system:

- `register_agent(...)` stores an `AgentProfile`.
- `submit_run(...)` attaches evaluations to an agent and stores causal graphs
  when run ids and failure causes are available.
- `generate_leaderboard(...)` ranks agents within a category.
- `build_causal_graph(...)` converts traces and failure events into directed
  causal chains.
- `explain_failure_chain(...)` turns a stored causal graph into readable
  debugging text.
- `clear_network_state()` resets the in-memory registry for tests or isolated
  benchmark sessions.

## Platform Flywheel

The hosted architecture is designed around the reliability feedback loop:

```text
SDK emits run
  -> ingestion API stores it
  -> analytics computes intelligence
  -> leaderboard updates rankings
  -> dashboard/API expose results
  -> users improve agents
  -> new runs enter the system
```

The platform moat comes from four structural properties:

- Cross-user benchmark network: global distributions answer “what percentile is
  my agent globally?”
- Persistent global dataset: append-only run history makes behavior replayable
  and hard to replicate.
- Causal intelligence aggregation: ecosystem-level failure distributions reveal
  the dominant ways agents fail.
- CI/CD enforcement adoption: `critiqor check` turns reliability from optional
  feedback into deployment infrastructure.

## V2 Infrastructure Guarantees

Critiqor V2 is designed as data infrastructure:

- Structured event ingestion through `IngestionAPI`.
- Tenant-aware system of record through `ReliabilityIndexStore`.
- Append-only replay support via `AgentReliabilityIndex(event_log_path=...)`.
- Streaming event abstraction through `EventStream`.
- Deterministic analytics only; no model-ranked leaderboards.
- API-driven dashboard data only; frontend visualization remains external.

## Trust Levels

The `trust_level` is derived from the evidence-weighted confidence:

| Confidence | Trust Level |
| --- | --- |
| `75-100` | `High` |
| `50-74` | `Moderate` |
| `0-49` | `Low` |

## Result Shape

```python
result.answer
result.confidence
result.trust_level
result.critique.hallucination
result.critique.reasoning
result.critique.tool_reliability
result.critique.tool_use  # compatibility alias
result.critique.consistency
result.critique.task_completion
result.critique.confidence_calibration
result.critique.execution_efficiency
result.critique.evidence_level
result.critique.summary
result.critique.findings
result.evidence.evidence_level
result.failure_causes
result.evaluation_confidence
result.deployment_recommendation
result.benchmark_percentile
```

For logging or automation:

```python
payload = result.to_dict()
```

## Supported Agents

Critiqor can wrap objects that expose one of these interfaces:

- `run(prompt)`
- `invoke(prompt)`
- `generate(prompt)`
- `__call__(prompt)`

The base agent only needs to accept a prompt and return a text-like response.
Critiqor can extract text from strings, common response objects, and dictionaries
with keys such as `content`, `text`, `answer`, `output`, or `response`.

## When To Use

Use Critiqor when:

- You want consistent, machine-readable reliability scores.
- You have traces, tool logs, or runtime metrics and want them reflected in the score.
- You care about tool misuse, ignored outputs, retries, loops, calibration, and task completion.
- You need to know why a run failed without manually reading traces.
- You want immediate fix recommendations for reliability failures.
- You want to compare prompt versions, model upgrades, or deployments.
- You need reproducible benchmark suites and reliability percentiles.
- You need to rank agents against peers in the same category.
- You want step-by-step causal debugging instead of flat failure labels.
- You want certification badges or CI/CD policy gates.
- You need trend and deployment-safety signals for release decisions.
- You want a lightweight path toward production observability without building a full eval platform first.

Use a generic LLM instead when:

- You only need one-off feedback.
- You want the fastest possible critique with no install step.
- You do not have execution traces and do not need evidence-weighted confidence.
- You do not need structured output, repeatable scoring criteria, or automation hooks.
- You need a full dashboard or audited enterprise collector today.

## Philosophy / Non-Goals

Critiqor V1 is a reliability layer, not an autonomous judge.

It does:

- Run your existing agent once for an answer.
- Evaluate response-only, trace-backed, or fully instrumented evidence.
- Return structured scores, evidence level, evaluation confidence, failure causes,
  a deployment recommendation, a trust label, and a short critique.
- Capture tool calls and outputs with `monitor()` or adapter events.
- Persist evaluations, compare runs, analyze historical trends, and benchmark
  against prior runs.
- Run benchmark suites, generate certification badges, check deployment policy,
  prepare anonymized benchmark contributions, and expose dashboard-ready data.
- Register agents, submit runs, generate cross-agent leaderboards, and explain
  failures as causal chains.

It does not:

- Retry or repair the answer.
- Generate improvement suggestions.
- Run benchmark datasets.
- Provide a dashboard.
- Replace human review for high-stakes work.
- Automatically observe arbitrary third-party frameworks unless they are wired
  through `CritiqorTracer`, `monitor()`, or an OpenTelemetry-compatible adapter.

## Local Verification

Run the example:

```bash
python examples/simple_usage.py
```

Run the smoke experiment:

```bash
python experiments/sandbox_eval.py
```

Run focused regression checks:

```bash
python -m unittest discover -s tests -v
```

## Status

Critiqor is currently `0.1.0` alpha. V1.3 supports response-only evaluation,
trace evaluation, SDK instrumentation, root-cause analysis, fix recommendations,
failure-cause detection, run comparison, historical storage, trend analysis,
deployment recommendations, benchmark suites, reliability percentiles,
certification badges, CI/CD policy checks, opt-in aggregate benchmark
contributions, dashboard data APIs, cross-agent leaderboards, causal failure
graphs, evidence confidence levels, and `High` / `Moderate` / `Low` trust
labels.

## Included Files

- `critiqor/core.py`: Core wrapper and result objects
- `examples/simple_usage.py`: Minimal copy-paste example
- `experiments/sandbox_eval.py`: End-to-end smoke demo
- `tests/test_core.py`: Focused regression checks
