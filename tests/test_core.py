"""Stdlib tests for the minimal Critiqor wrapper."""

from __future__ import annotations

import tempfile
import unittest

from critiqor import (
    AgentReliabilityIndex,
    AgentProfile,
    BenchmarkCase,
    BenchmarkSpec,
    Critiqor,
    CritiqorBenchmark,
    CritiqorTracer,
    OpenTelemetryAdapter,
    ReliabilityDashboardData,
    add_benchmark,
    analyze_trends,
    attach_critiqor,
    benchmark_run,
    build_causal_graph,
    certification_criteria_table,
    certify_run,
    check_policy,
    clear_network_state,
    compare_runs,
    detect_failure_causes,
    explain_failure_chain,
    generate_insights,
    generate_leaderboard,
    load_evaluations,
    monitor,
    prepare_benchmark_contribution,
    register_agent,
    recommend_deployment,
    save_benchmark_contribution,
    save_evaluation,
    submit_run,
)
from critiqor.cli import main as cli_main


class RunAgent:
    def run(self, prompt: str) -> str:
        if "Hallucination:" in prompt:
            return (
                "Hallucination: 95\n"
                "Reasoning: 90\n"
                "Tool Reliability: 100\n"
                "Consistency: 92\n"
                "Task Completion: 88\n"
                "Confidence Calibration: 90\n"
                "Execution Efficiency: 94\n"
                "Evidence Level: response_only\n"
                "Summary: Reliable answer with no visible agent failures.\n"
                "Findings:\n"
                "- No obvious hallucination or task completion issue."
            )
        return "Paris is the capital of France."


class InvokeAgent:
    def invoke(self, prompt: str) -> dict[str, str]:
        if "Hallucination:" in prompt:
            return {
                "text": (
                    "Hallucination: 64\n"
                    "Reasoning: 70\n"
                    "Tool Reliability: 72\n"
                    "Consistency: 66\n"
                    "Task Completion: 68\n"
                    "Confidence Calibration: 61\n"
                    "Execution Efficiency: 73\n"
                    "Evidence Level: response_only\n"
                    "Summary: Useful, but it makes a couple of unsupported assumptions."
                )
            }
        return {"text": "This is an answer from invoke()."}


class UnstructuredCritiqueAgent:
    def run(self, prompt: str) -> str:
        if "Hallucination:" in prompt:
            return "Reasoning: 81\nSummary: Clear overall, but missing most dimension scores."
        return "An otherwise decent answer."


class UnsupportedAgent:
    pass


class TraceJudge:
    def run(self, prompt: str) -> str:
        return (
            "Hallucination: 90\n"
            "Reasoning: 86\n"
            "Tool Reliability: 92\n"
            "Consistency: 88\n"
            "Task Completion: 84\n"
            "Confidence Calibration: 82\n"
            "Execution Efficiency: 91\n"
            "Evidence Level: trace_available\n"
            "Summary: Trace-backed answer with adequate observed tool behavior.\n"
            "Findings:\n"
            "- Tool evidence supports the final response."
        )


class CritiqorTests(unittest.TestCase):
    def test_run_returns_structured_result(self) -> None:
        result = Critiqor(RunAgent()).run("What is the capital of France?")

        self.assertEqual(result.answer, "Paris is the capital of France.")
        self.assertEqual(result.confidence, 79)
        self.assertEqual(result.trust_level, "High")
        self.assertEqual(result.critique.hallucination, 95)
        self.assertEqual(result.critique.task_completion, 88)
        self.assertEqual(result.critique.tool_reliability, 100)
        self.assertEqual(result.critique.tool_use, 100)
        self.assertEqual(result.critique.evidence_level, "response_only")
        self.assertEqual(
            result.critique.summary,
            "Reliable answer with no visible agent failures.",
        )
        self.assertEqual(
            result.critique.findings,
            ["No obvious hallucination or task completion issue."],
        )

    def test_invoke_agents_are_supported(self) -> None:
        result = Critiqor(InvokeAgent()).run("Say something helpful.")

        self.assertEqual(result.answer, "This is an answer from invoke().")
        self.assertEqual(result.confidence, 58)
        self.assertEqual(result.trust_level, "Moderate")
        self.assertEqual(result.critique.reasoning, 70)
        self.assertEqual(
            result.critique.summary,
            "Useful, but it makes a couple of unsupported assumptions.",
        )

    def test_unstructured_critique_still_parses(self) -> None:
        result = Critiqor(UnstructuredCritiqueAgent()).run("Try a fuzzy task.")

        self.assertEqual(result.confidence, 46)
        self.assertEqual(result.trust_level, "Low")
        self.assertEqual(result.critique.reasoning, 81)
        self.assertEqual(result.critique.hallucination, 50)
        self.assertEqual(
            result.critique.summary,
            "Clear overall, but missing most dimension scores.",
        )

    def test_unsupported_agents_raise_a_clear_error(self) -> None:
        with self.assertRaises(TypeError):
            Critiqor(UnsupportedAgent()).run("Hello")

    def test_trace_evaluation_sets_trace_available_level(self) -> None:
        result = Critiqor(TraceJudge()).evaluate(
            prompt="Check Sydney weather.",
            response="Sydney is mild today.",
            tool_calls=[{"tool": "search", "args": {"query": "Sydney weather"}}],
            tool_outputs=[{"tool": "search", "output": "Mild weather report"}],
        )

        self.assertEqual(result.evidence.evidence_level, "trace_available")
        self.assertEqual(result.critique.evidence_level, "trace_available")
        self.assertEqual(result.confidence, 83)

    def test_duplicate_tool_calls_reduce_execution_efficiency(self) -> None:
        result = Critiqor(TraceJudge()).evaluate(
            prompt="Check Sydney weather.",
            response="Sydney is mild today.",
            tool_calls=[
                {"tool": "search", "args": {"query": "Sydney weather"}},
                {"tool": "search", "args": {"query": "Sydney weather"}},
            ],
            tool_outputs=[{"tool": "search", "output": "Mild weather report"}],
        )

        self.assertLessEqual(result.critique.execution_efficiency, 70)
        self.assertIn(
            "Repeated tool calls suggest avoidable execution overhead.",
            result.critique.findings,
        )

    def test_monitor_records_fully_instrumented_evidence(self) -> None:
        with monitor("Use a tool.") as recorder:
            tool = recorder.wrap_tool("double", lambda value: value * 2)
            response = f"Result: {tool(3)}"
            evidence = recorder.finish(response=response)

        self.assertEqual(evidence.evidence_level, "fully_instrumented")
        self.assertEqual(evidence.tool_calls[0].tool, "double")
        self.assertEqual(evidence.tool_outputs[0].output, 6)
        self.assertIsNotNone(evidence.metrics.latency)

    def test_tracer_and_opentelemetry_adapter_record_events(self) -> None:
        tracer = CritiqorTracer()
        tracer.record("tool_start", {"tool": "search", "args": {"q": "weather"}})
        tracer.record("tool_end", {"tool": "search", "output": "sunny"})

        otel = OpenTelemetryAdapter(tracer.recorder)
        otel.ingest_span(
            {
                "name": "llm",
                "attributes": {
                    "critiqor.kind": "llm",
                    "llm.model": "example-model",
                    "llm.token_usage": {"total": 12},
                },
            }
        )

        evidence = tracer.recorder.finish("Done", prompt="Prompt")
        self.assertEqual(evidence.tool_calls[0].tool, "search")
        self.assertEqual(evidence.metrics.token_usage["total"], 12)

    def test_failure_cause_engine_detects_observable_failures(self) -> None:
        evidence = Critiqor(TraceJudge()).evaluate(
            prompt="Use evidence.",
            response="Definitely safe. The answer is 99%.",
            tool_calls=[
                {"tool": "search", "args": {"query": "alpha"}},
                {"tool": "search", "args": {"query": "alpha"}},
                {"tool": "search", "args": {"query": "alpha"}},
                {"tool": "search", "args": {"query": "alpha"}},
            ],
            tool_outputs=[
                {"tool": "search", "output": "Beta evidence says review is needed."}
            ],
            metrics={"retries": 2, "errors": ["tool timeout"]},
        ).evidence

        causes = detect_failure_causes(evidence)
        cause_types = {cause.type for cause in causes}

        self.assertIn("redundant_tool_calls", cause_types)
        self.assertIn("ignored_tool_output", cause_types)
        self.assertIn("runtime_failures", cause_types)
        self.assertIn("unsupported_claims", cause_types)
        self.assertIn("confidence_mismatch", cause_types)

    def test_result_includes_failure_causes_and_action_fields(self) -> None:
        result = Critiqor(TraceJudge()).evaluate(
            prompt="Use evidence.",
            response="Definitely safe. The answer is 99%.",
            tool_calls=[
                {"tool": "search", "args": {"query": "alpha"}},
                {"tool": "search", "args": {"query": "alpha"}},
            ],
            tool_outputs=[
                {"tool": "search", "output": "Beta evidence says review is needed."}
            ],
        )

        payload = result.to_dict()

        self.assertTrue(payload["failure_causes"])
        self.assertIn("evaluation_confidence", payload)
        self.assertEqual(payload["evidence_level"], "trace_available")
        self.assertIn(
            payload["deployment_recommendation"],
            {"safe_to_deploy", "review_recommended", "unsafe_for_production"},
        )

    def test_compare_runs_summarizes_score_changes(self) -> None:
        run_a = {
            "trust_score": 70,
            "scores": {
                "reasoning": 70,
                "tool_reliability": 90,
                "consistency": 80,
            },
        }
        run_b = {
            "trust_score": 78,
            "scores": {
                "reasoning": 82,
                "tool_reliability": 86,
                "consistency": 80,
            },
        }

        comparison = compare_runs(run_a, run_b)

        self.assertEqual(comparison.trust_change, 8)
        self.assertEqual(comparison.changes["reasoning"], 12)
        self.assertEqual(comparison.changes["tool_reliability"], -4)
        self.assertEqual(
            comparison.summary,
            "Reasoning improved.",
        )

    def test_save_load_trends_and_benchmarking(self) -> None:
        first = {
            "trust_score": 80,
            "scores": {
                "hallucination": 90,
                "reasoning": 70,
                "tool_reliability": 85,
            },
            "failure_causes": [],
            "evidence_level": "trace_available",
            "evaluation_confidence": 78,
            "deployment_recommendation": "review_recommended",
        }
        second = {
            "trust_score": 68,
            "scores": {
                "hallucination": 76,
                "reasoning": 74,
                "tool_reliability": 76,
            },
            "failure_causes": [],
            "evidence_level": "trace_available",
            "evaluation_confidence": 78,
            "deployment_recommendation": "review_recommended",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            path = f"{temp_dir}/evals.jsonl"
            save_evaluation(first, path=path, agent_id="agent-a", run_id="run-1")
            save_evaluation(second, path=path, agent_id="agent-a", run_id="run-2")
            records = load_evaluations(path=path, agent_id="agent-a")

        trend = analyze_trends(records)

        self.assertEqual(len(records), 2)
        self.assertEqual(trend.trust_trend, "declining")
        self.assertEqual(trend.hallucination_change, -14)
        self.assertEqual(trend.tool_reliability_change, -9)
        self.assertEqual(trend.reasoning_change, 4)
        self.assertEqual(benchmark_run(second, records), 50)

    def test_deployment_recommendation_and_add_benchmark(self) -> None:
        self.assertEqual(
            recommend_deployment(88, 92, []),
            "safe_to_deploy",
        )
        self.assertEqual(
            recommend_deployment(66, 78, []),
            "review_recommended",
        )
        self.assertEqual(
            recommend_deployment(42, 78, []),
            "unsafe_for_production",
        )

        result = Critiqor(TraceJudge()).evaluate(
            prompt="Check Sydney weather.",
            response="Sydney is mild today.",
            tool_calls=[{"tool": "search", "args": {"query": "Sydney weather"}}],
            tool_outputs=[{"tool": "search", "output": "Mild weather report"}],
        )
        benchmarked = add_benchmark(
            result,
            [
                {"trust_score": 60, "scores": {}},
                {"trust_score": 80, "scores": {}},
                {"trust_score": 90, "scores": {}},
            ],
        )

        self.assertEqual(benchmarked.benchmark_percentile, 67)

    def test_attach_critiqor_subscribes_to_agent_events(self) -> None:
        class EventAgent:
            def __init__(self) -> None:
                self.handlers = {}

            def on(self, event_name: str, handler) -> None:
                self.handlers[event_name] = handler

        agent = EventAgent()
        tracer = attach_critiqor(agent)
        agent.handlers["tool_start"](tool="search", args={"q": "weather"})
        agent.handlers["tool_end"](tool="search", output="weather")

        evidence = tracer.recorder.finish("weather", prompt="weather")

        self.assertEqual(evidence.tool_calls[0].tool, "search")
        self.assertEqual(evidence.tool_outputs[0].output, "weather")

    def test_failure_causes_include_root_cause_and_recommendation(self) -> None:
        result = Critiqor(TraceJudge()).evaluate(
            prompt="Use evidence.",
            response="Definitely safe. The answer is 99%.",
            tool_calls=[
                {"tool": "search", "args": {"query": "alpha"}},
                {"tool": "search", "args": {"query": "alpha"}},
            ],
            tool_outputs=[
                {"tool": "search", "output": "Beta evidence says review is needed."}
            ],
        )

        redundant = next(
            cause for cause in result.failure_causes if cause.type == "redundant_tool_calls"
        )
        payload = redundant.to_dict()

        self.assertIn("root_cause", payload)
        self.assertIn("recommended_fix", payload["root_cause"])
        self.assertIn("recommendation", payload)

    def test_benchmark_framework_runs_reproducible_cases(self) -> None:
        benchmark = CritiqorBenchmark(
            name="Coding Benchmark",
            agent_type="coding",
            cases=[BenchmarkCase(prompt="Fix a test.", name="case-1")],
            historical_runs=[{"trust_score": 60}, {"trust_score": 75}],
        )

        result = benchmark.run(TraceJudge())

        self.assertEqual(result.name, "Coding Benchmark")
        self.assertEqual(result.agent_type, "coding")
        self.assertEqual(result.run_count, 1)
        self.assertEqual(result.trust_score, 72)
        self.assertEqual(result.percentile, 50)

    def test_certification_levels_and_criteria_table(self) -> None:
        run = {
            "trust_score": 92,
            "evaluation_confidence": 85,
            "evidence_level": "trace_available",
            "deployment_recommendation": "safe_to_deploy",
            "scores": {"hallucination": 95},
            "failure_causes": [],
        }

        certification = certify_run(run, percentile=88)
        criteria = certification_criteria_table()

        self.assertEqual(certification.certification_level, "gold")
        self.assertIn("Critiqor Certified", certification.markdown_badge)
        self.assertEqual(criteria[-1]["level"], "platinum")

    def test_policy_check_and_cli_block_deployments(self) -> None:
        evaluation = {
            "trust_score": 70,
            "scores": {"hallucination": 70, "tool_reliability": 60},
            "failure_causes": [],
            "evidence_level": "trace_available",
            "evaluation_confidence": 78,
            "deployment_recommendation": "review_recommended",
        }

        policy_result = check_policy(
            evaluation,
            {
                "minimum_trust_score": 80,
                "maximum_hallucination_risk": 20,
                "minimum_tool_reliability": 75,
            },
        )

        self.assertFalse(policy_result.passed)
        self.assertIn("Tool reliability below threshold.", policy_result.messages)

        with tempfile.TemporaryDirectory() as temp_dir:
            eval_path = f"{temp_dir}/evals.jsonl"
            save_evaluation(evaluation, path=eval_path, agent_id="agent-a")
            exit_code = cli_main(
                [
                    "check",
                    "--evaluations",
                    eval_path,
                    "--agent-id",
                    "agent-a",
                    "--minimum-trust-score",
                    "80",
                ]
            )

        self.assertEqual(exit_code, 1)

    def test_opt_in_benchmark_contribution_omits_prompt_and_output(self) -> None:
        result = Critiqor(TraceJudge()).evaluate(
            prompt="Private prompt",
            response="Private output",
            tool_calls=[{"tool": "search", "args": {"query": "private"}}],
            tool_outputs=[{"tool": "search", "output": "Private evidence"}],
        )
        contribution = prepare_benchmark_contribution(
            result,
            agent_type="research",
            certification_level="silver",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            saved = save_benchmark_contribution(
                contribution,
                path=f"{temp_dir}/contrib.jsonl",
            )

        payload = saved.to_dict()

        self.assertEqual(payload["agent_type"], "research")
        self.assertNotIn("prompt", payload)
        self.assertNotIn("response", payload)
        self.assertNotIn("tool_outputs", payload)

    def test_auto_attach_detects_framework_shape(self) -> None:
        class LangGraphLikeAgent:
            def __init__(self) -> None:
                self.handlers = {}
                self.graph = object()

            def on(self, event_name: str, handler) -> None:
                self.handlers[event_name] = handler

        tracer = Critiqor.auto_attach(LangGraphLikeAgent())

        self.assertEqual(tracer.framework_name, "langgraph")

    def test_dashboard_data_layer_and_insights(self) -> None:
        runs = [
            {
                "trust_score": 90,
                "scores": {"hallucination": 95, "tool_reliability": 90, "reasoning": 90},
                "failure_causes": [],
                "evidence_level": "trace_available",
                "evaluation_confidence": 80,
                "deployment_recommendation": "safe_to_deploy",
            },
            {
                "trust_score": 74,
                "scores": {"hallucination": 80, "tool_reliability": 72, "reasoning": 86},
                "failure_causes": [
                    {
                        "type": "ignored_tool_output",
                        "severity": "medium",
                        "impact": -7,
                        "description": "Tool output ignored.",
                    }
                ],
                "evidence_level": "trace_available",
                "evaluation_confidence": 80,
                "deployment_recommendation": "review_recommended",
            },
        ]
        dashboard = ReliabilityDashboardData(run_history=runs)
        data = dashboard.to_dict()
        insight = generate_insights(runs)

        self.assertEqual(data["trends"]["trust_trend"], "declining")
        self.assertEqual(len(data["failure_causes"]), 1)
        self.assertIn("ignored_tool_output", insight.primary_drivers)

    def test_cross_agent_leaderboard_ranks_agents_by_category(self) -> None:
        clear_network_state()
        register_agent(
            AgentProfile(
                agent_id="agent_123",
                name="Alpha Coder",
                category="coding_agents",
            )
        )
        register_agent(
            {
                "agent_id": "agent_456",
                "name": "Beta Coder",
                "category": "coding_agents",
            }
        )

        submit_run(
            "agent_123",
            {
                "trust_score": 92,
                "scores": {"reasoning": 90},
                "failure_causes": [],
                "agent_type": "coding",
            },
        )
        submit_run(
            "agent_456",
            {
                "trust_score": 89,
                "scores": {"reasoning": 88},
                "failure_causes": [],
                "agent_type": "coding",
            },
        )

        leaderboard = generate_leaderboard(category="coding_agents")
        payload = leaderboard.to_dict()

        self.assertEqual(payload["category"], "coding_agents")
        self.assertEqual(payload["rankings"][0]["rank"], 1)
        self.assertEqual(payload["rankings"][0]["agent_id"], "agent_123")
        self.assertEqual(payload["rankings"][0]["trust_score"], 92)
        self.assertGreater(payload["rankings"][0]["percentile"], payload["rankings"][1]["percentile"])

    def test_causal_graph_builds_and_explains_failure_chain(self) -> None:
        trace = [
            {"event": "prompt_ambiguity", "detail": "User intent unclear."},
            {"event": "tool_start", "tool": "search"},
            {"event": "tool_end", "tool": "search", "output": "irrelevant data"},
        ]

        graph = build_causal_graph(
            trace,
            {"type": "ignored_tool_output"},
            run_id="run-causal-1",
        )
        payload = graph.to_dict()
        explanation = explain_failure_chain("run-causal-1")

        self.assertEqual(payload["failure_event"], "ignored_tool_output")
        self.assertEqual(payload["causal_graph"][0]["node"], "prompt_ambiguity")
        self.assertIn("leads_to", payload["causal_graph"][0])
        self.assertIn("Prompt was ambiguous", explanation)
        self.assertIn("Agent ignored weak or retrieved evidence", explanation)

    def test_submit_run_stores_causal_graph_for_record_failures(self) -> None:
        clear_network_state()
        register_agent({"agent_id": "agent_diag", "name": "Diagnostic", "category": "research"})
        submit_run(
            "agent_diag",
            {
                "run_id": "run-unsupported",
                "trust_score": 61,
                "scores": {"hallucination": 55},
                "failure_causes": [
                    {
                        "type": "unsupported_claims",
                        "severity": "medium",
                        "impact": -8,
                        "description": "Specific claim lacked evidence.",
                    }
                ],
                "trace": [{"event": "agent_step", "detail": "No evidence found."}],
            },
        )

        explanation = explain_failure_chain("run-unsupported")

        self.assertIn("Evidence was missing", explanation)
        self.assertIn("Final answer hallucinated", explanation)

    def test_hosted_reliability_index_ingests_and_ranks_agents(self) -> None:
        index = AgentReliabilityIndex()
        first = index.ingest_run(
            {
                "agent_id": "agent_a",
                "agent_name": "Agent A",
                "category": "coding_agents",
                "local_run_id": "local-1",
                "trust_score": 91,
                "scores": {"reasoning": 90, "tool_reliability": 92},
                "failure_causes": [],
            }
        )
        duplicate = index.ingest_run(
            {
                "agent_id": "agent_a",
                "agent_name": "Agent A",
                "category": "coding_agents",
                "local_run_id": "local-1",
                "trust_score": 91,
                "scores": {"reasoning": 90, "tool_reliability": 92},
                "failure_causes": [],
            }
        )
        index.ingest_run(
            {
                "agent_id": "agent_b",
                "agent_name": "Agent B",
                "category": "coding_agents",
                "trust_score": 84,
                "scores": {"reasoning": 84, "tool_reliability": 80},
                "failure_causes": [
                    {
                        "type": "ignored_tool_output",
                        "severity": "medium",
                        "impact": -7,
                        "description": "Evidence ignored.",
                    }
                ],
                "trace": [{"event": "tool_end", "output": "retrieved evidence"}],
            }
        )

        leaderboard = index.leaderboards.get_leaderboard("coding_agents")
        summary = index.analytics.agent_summary("agent_a")
        failures = index.analytics.failure_distribution()

        self.assertEqual(first.status, "accepted")
        self.assertEqual(first.run_id, duplicate.run_id)
        self.assertEqual(leaderboard["rankings"][0]["agent_id"], "agent_a")
        self.assertEqual(summary["category_rank"], 1)
        self.assertEqual(failures[0]["failure_type"], "ignored_tool_output")

    def test_public_api_and_dashboard_views_read_from_platform_services(self) -> None:
        index = AgentReliabilityIndex()
        index.ingest_run(
            {
                "agent_id": "agent_a",
                "agent_name": "Agent A",
                "category": "research",
                "trust_score": 90,
                "scores": {"hallucination": 95, "reasoning": 90},
                "failure_causes": [],
            }
        )
        index.ingest_run(
            {
                "agent_id": "agent_a",
                "agent_name": "Agent A",
                "category": "research",
                "trust_score": 82,
                "scores": {"hallucination": 85, "reasoning": 88},
                "failure_causes": [
                    {
                        "type": "unsupported_claims",
                        "severity": "medium",
                        "impact": -8,
                        "description": "Claim lacked evidence.",
                    }
                ],
            }
        )
        index.ingest_run(
            {
                "agent_id": "agent_b",
                "agent_name": "Agent B",
                "category": "research",
                "trust_score": 76,
                "scores": {"hallucination": 78, "reasoning": 80},
                "failure_causes": [],
            }
        )

        agent = index.api.get_agent("agent_a")
        trends = index.api.get_agent_trends("agent_a")
        comparison = index.api.compare("agent_a", "agent_b")
        dashboard = index.dashboard.ecosystem_view("research")

        self.assertEqual(agent["agent_id"], "agent_a")
        self.assertEqual(trends["trust_trend"], "declining")
        self.assertIn("trust_change", comparison)
        self.assertEqual(dashboard["distribution"]["count"], 3)
        self.assertIn("insights", dashboard)

    def test_v2_tenant_isolation_and_public_leaderboard_mode(self) -> None:
        index = AgentReliabilityIndex()
        index.ingest_run(
            {
                "tenant_id": "tenant_a",
                "tenant_name": "Tenant A",
                "agent_id": "agent_shared",
                "agent_name": "Public Agent",
                "category": "coding_agents",
                "trust_score": 92,
                "public_benchmark": True,
                "tenant_public_benchmark_enabled": True,
                "anonymized_aggregation": True,
                "scores": {"reasoning": 92},
                "failure_causes": [],
            }
        )
        index.ingest_run(
            {
                "tenant_id": "tenant_b",
                "tenant_name": "Tenant B",
                "agent_id": "agent_shared",
                "agent_name": "Private Agent",
                "category": "coding_agents",
                "trust_score": 70,
                "public_benchmark": False,
                "scores": {"reasoning": 70},
                "failure_causes": [],
            }
        )

        tenant_a_board = index.api.get_leaderboard(
            "coding_agents",
            tenant_id="tenant_a",
        )
        public_board = index.api.get_leaderboard(
            "coding_agents",
            public_only=True,
        )

        self.assertEqual(tenant_a_board["rankings"][0]["tenant_id"], "tenant_a")
        self.assertEqual(len(public_board["rankings"]), 1)
        self.assertEqual(public_board["rankings"][0]["agent_id"], "agent_shared")
        self.assertEqual(index.store.tenants["tenant_a"].anonymized_aggregation_enabled, True)

    def test_v2_benchmark_specs_normalize_scores_and_api_exposes_benchmark(self) -> None:
        index = AgentReliabilityIndex()
        accepted = index.ingest_run(
            {
                "tenant_id": "tenant_a",
                "agent_id": "agent_bench",
                "category": "research",
                "benchmark_id": "research_v1",
                "benchmark_spec": BenchmarkSpec(
                    benchmark_id="research_v1",
                    category="research",
                    version="v1.0",
                    weights={
                        "reasoning": 0.25,
                        "tool_use": 0.25,
                        "hallucination": 0.5,
                    },
                ).to_dict(),
                "scores": {
                    "reasoning": 80,
                    "tool_reliability": 60,
                    "hallucination": 100,
                },
                "failure_causes": [],
                "public_benchmark": True,
            }
        )

        run = index.store.runs[accepted.run_id]
        benchmark = index.api.get_benchmark("research_v1")
        benchmark_board = index.api.get_leaderboard(
            "research",
            public_only=True,
            benchmark_id="research_v1",
        )

        self.assertEqual(run.trust_score, 85)
        self.assertEqual(run.benchmark_version, "v1.0")
        self.assertEqual(benchmark["version"], "v1.0")
        self.assertEqual(benchmark["distribution_stats"]["count"], 1)
        self.assertEqual(benchmark_board["rankings"][0]["trust_score"], 85)

    def test_v2_streaming_events_and_append_only_event_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = f"{temp_dir}/events.jsonl"
            index = AgentReliabilityIndex(event_log_path=path)
            observed_events = []
            index.event_stream.subscribe(lambda event: observed_events.append(event.event_type))
            index.ingest_run(
                {
                    "tenant_id": "tenant_a",
                    "agent_id": "agent_stream",
                    "category": "general",
                    "local_run_id": "stream-1",
                    "trust_score": 64,
                    "scores": {"hallucination": 60},
                    "failure_causes": [
                        {
                            "type": "unsupported_claims",
                            "severity": "medium",
                            "impact": -8,
                            "description": "Claim lacked evidence.",
                        }
                    ],
                    "trace": [{"event": "agent_step", "detail": "No evidence."}],
                }
            )
            index.api.get_leaderboard("general", tenant_id="tenant_a")

            with open(path, encoding="utf-8") as handle:
                lines = [line.strip() for line in handle if line.strip()]

        self.assertIn("RunIngested", observed_events)
        self.assertIn("FailureDetected", observed_events)
        self.assertIn("CausalGraphGenerated", observed_events)
        self.assertIn("LeaderboardUpdated", observed_events)
        self.assertGreaterEqual(len(lines), 3)


if __name__ == "__main__":
    unittest.main()
