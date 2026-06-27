"""Stdlib tests for the minimal Critiqor wrapper."""

from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

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
    monitor_openclaw_process,
    diagnose_openclaw_events,
    default_openclaw_benchmark_spec,
    build_openclaw_run_payload,
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


def benchmark_spec(benchmark_id: str = "general_v1", category: str = "general") -> dict:
    return BenchmarkSpec(
        benchmark_id=benchmark_id,
        category=category,
        version="v1.0",
        weights={
            "hallucination": 0.25,
            "reasoning": 0.25,
            "tool_use": 0.25,
            "confidence_calibration": 0.25,
        },
        difficulty_factors={
            "task_complexity": 70,
            "tool_usage_requirements": 70,
            "multi_step_reasoning": 70,
            "retrieval_dependency": 70,
        },
    ).to_dict()


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
                "benchmark_id": "coding_v1",
                "benchmark_spec": benchmark_spec("coding_v1", "coding_agents"),
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
                "benchmark_id": "coding_v1",
                "benchmark_spec": benchmark_spec("coding_v1", "coding_agents"),
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
                "benchmark_id": "coding_v1",
                "benchmark_spec": benchmark_spec("coding_v1", "coding_agents"),
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
        self.assertEqual(duplicate.status, "duplicate")
        self.assertEqual(first.run_id, duplicate.run_id)
        self.assertEqual(leaderboard["rankings"][0]["agent_id"], "agent_a")
        self.assertIn("score_breakdown", leaderboard["rankings"][0])
        self.assertIn("evidence", leaderboard["rankings"][0])
        self.assertIn("reasoning", leaderboard["rankings"][0])
        self.assertIn("impact", leaderboard["rankings"][0])
        self.assertIn("recommendation", leaderboard["rankings"][0])
        self.assertEqual(summary["category_rank"], 1)
        self.assertEqual(failures[0]["failure_type"], "ignored_tool_output")

    def test_public_api_and_dashboard_views_read_from_platform_services(self) -> None:
        index = AgentReliabilityIndex()
        index.ingest_run(
            {
                "agent_id": "agent_a",
                "agent_name": "Agent A",
                "category": "research",
                "benchmark_id": "research_v1",
                "benchmark_spec": benchmark_spec("research_v1", "research"),
                "trust_score": 90,
                "scores": {
                    "hallucination": 95,
                    "reasoning": 90,
                    "tool_reliability": 90,
                    "confidence_calibration": 90,
                },
                "failure_causes": [],
            }
        )
        index.ingest_run(
            {
                "agent_id": "agent_a",
                "agent_name": "Agent A",
                "category": "research",
                "benchmark_id": "research_v1",
                "benchmark_spec": benchmark_spec("research_v1", "research"),
                "trust_score": 72,
                "scores": {
                    "hallucination": 70,
                    "reasoning": 72,
                    "tool_reliability": 70,
                    "confidence_calibration": 70,
                },
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
                "benchmark_id": "research_v1",
                "benchmark_spec": benchmark_spec("research_v1", "research"),
                "trust_score": 76,
                "scores": {
                    "hallucination": 78,
                    "reasoning": 80,
                    "tool_reliability": 76,
                    "confidence_calibration": 76,
                },
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
                "benchmark_id": "coding_v1",
                "benchmark_spec": benchmark_spec("coding_v1", "coding_agents"),
                "trust_score": 92,
                "visibility": "public",
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
                "benchmark_id": "coding_v1",
                "benchmark_spec": benchmark_spec("coding_v1", "coding_agents"),
                "trust_score": 70,
                "visibility": "private",
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
                    difficulty_factors={
                        "task_complexity": 80,
                        "tool_usage_requirements": 60,
                        "multi_step_reasoning": 70,
                        "retrieval_dependency": 90,
                    },
                ).to_dict(),
                "scores": {
                    "reasoning": 80,
                    "tool_reliability": 60,
                    "hallucination": 100,
                },
                "failure_causes": [],
                "public_benchmark": True,
                "visibility": "public",
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
                    "benchmark_id": "general_v1",
                    "benchmark_spec": benchmark_spec("general_v1", "general"),
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

    def test_v2_ingestion_rejects_malformed_or_unversioned_runs(self) -> None:
        index = AgentReliabilityIndex()

        with self.assertRaisesRegex(ValueError, "agent_id is required"):
            index.ingest_run(
                {
                    "benchmark_id": "general_v1",
                    "benchmark_spec": benchmark_spec("general_v1", "general"),
                    "trust_score": 80,
                }
            )

        with self.assertRaisesRegex(ValueError, "benchmark_id is required"):
            index.ingest_run(
                {
                    "agent_id": "agent_missing_benchmark",
                    "trust_score": 80,
                }
            )

        with self.assertRaisesRegex(ValueError, "benchmark_spec is required"):
            index.ingest_run(
                {
                    "agent_id": "agent_unversioned",
                    "benchmark_id": "unknown_v1",
                    "trust_score": 80,
                }
            )

    def test_v2_run_hash_deduplicates_without_relying_on_self_reported_run_id(self) -> None:
        index = AgentReliabilityIndex()
        payload = {
            "tenant_id": "tenant_a",
            "agent_id": "agent_hash",
            "category": "general",
            "benchmark_id": "general_v1",
            "benchmark_spec": benchmark_spec("general_v1", "general"),
            "trust_score": 88,
            "scores": {"reasoning": 88},
            "failure_causes": [],
            "visibility": "private",
        }

        first = index.ingest_run({**payload, "run_id": "local-a"})
        duplicate = index.ingest_run({**payload, "run_id": "local-b"})

        self.assertEqual(duplicate.status, "duplicate")
        self.assertEqual(first.run_id, duplicate.run_id)
        self.assertEqual(len(index.store.runs), 1)

    def test_v2_event_log_replay_restores_rankings_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = f"{temp_dir}/events.jsonl"
            index = AgentReliabilityIndex(event_log_path=path)
            index.ingest_run(
                {
                    "tenant_id": "tenant_a",
                    "agent_id": "agent_replay_a",
                    "category": "coding_agents",
                    "benchmark_id": "coding_v1",
                    "benchmark_spec": benchmark_spec("coding_v1", "coding_agents"),
                    "trust_score": 91,
                    "scores": {"reasoning": 91},
                    "failure_causes": [],
                    "visibility": "public",
                }
            )
            index.ingest_run(
                {
                    "tenant_id": "tenant_a",
                    "agent_id": "agent_replay_b",
                    "category": "coding_agents",
                    "benchmark_id": "coding_v1",
                    "trust_score": 72,
                    "scores": {"reasoning": 72},
                    "failure_causes": [],
                    "visibility": "public",
                }
            )

            sequence_ids = [event.sequence_id for event in index.event_stream.events]
            replayed = AgentReliabilityIndex.from_event_log(path)

        leaderboard = replayed.api.get_leaderboard(
            "coding_agents",
            tenant_id="tenant_a",
        )

        self.assertEqual(sequence_ids, sorted(sequence_ids))
        self.assertEqual(leaderboard["rankings"][0]["agent_id"], "agent_replay_a")
        self.assertEqual(len(replayed.store.runs), 2)

    def test_v2_leaderboard_uses_weighted_formula_and_deterministic_tiebreaks(self) -> None:
        index = AgentReliabilityIndex()
        common = {
            "tenant_id": "tenant_a",
            "category": "coding_agents",
            "benchmark_id": "coding_v1",
            "benchmark_spec": benchmark_spec("coding_v1", "coding_agents"),
            "trust_score": 85,
            "scores": {"reasoning": 85, "tool_reliability": 85},
            "failure_causes": [],
            "evaluation_confidence": 90,
            "evidence_level": "trace_available",
            "visibility": "public",
        }
        index.ingest_run({**common, "agent_id": "agent_z", "timestamp": "2026-01-01T00:00:00+00:00"})
        index.ingest_run({**common, "agent_id": "agent_a", "timestamp": "2026-01-01T00:00:00+00:00"})

        leaderboard = index.api.get_leaderboard(
            "coding_agents",
            tenant_id="tenant_a",
        )
        first = leaderboard["rankings"][0]

        self.assertEqual(first["agent_id"], "agent_a")
        self.assertEqual(first["leaderboard_score"], first["score_breakdown"]["leaderboard_score"])
        self.assertEqual(set(first["score_breakdown"]), {
            "reliability",
            "evaluation_confidence",
            "benchmark_normalization",
            "consistency",
            "failure_rate",
            "trend_score",
            "leaderboard_score",
        })

    def test_dashboard_launcher_opens_core_engine_after_run_is_readable(self) -> None:
        from critiqor.dashboard import serve_dashboard

        opened: list[str] = []
        started: dict[str, object] = {}

        class FakeProcess:
            pid = 12345

            def poll(self) -> None:
                return None

            def wait(self, timeout: float | None = None) -> int:
                return 0

        with tempfile.TemporaryDirectory() as tmp:
            dashboard_dir = Path(tmp) / "core"
            dashboard_dir.mkdir()
            (dashboard_dir / "package.json").write_text("{}", encoding="utf-8")
            (dashboard_dir / "src" / "routes").mkdir(parents=True)
            (dashboard_dir / "src" / "routes" / "index.tsx").write_text("", encoding="utf-8")
            (dashboard_dir / "src" / "lib").mkdir(parents=True)
            (dashboard_dir / "src" / "lib" / "critiqor-api-store.server.ts").write_text("", encoding="utf-8")
            run_dir = Path(tmp) / "runs" / "run_008"
            run_dir.mkdir(parents=True)
            (run_dir / "diagnosis.json").write_text(json.dumps({"run_id": "run_008", "executive_summary": {"trust_score": 84}}), encoding="utf-8")

            def fake_start(found_dir: Path, runs_dir: str, host: str, port: int) -> FakeProcess:
                started.update({"dashboard_dir": found_dir, "runs_dir": runs_dir, "host": host, "port": port})
                return FakeProcess()

            with patch.dict(os.environ, {"CRITIQOR_DASHBOARD_DIR": str(dashboard_dir)}), \
                patch("critiqor.dashboard.start_core_engine_dashboard", fake_start), \
                patch("critiqor.dashboard.wait_for_dashboard_run") as wait, \
                patch("critiqor.dashboard.webbrowser.open", opened.append):
                exit_code = serve_dashboard(runs_dir=str(Path(tmp) / "runs"), host="127.0.0.1", port=4123, run_id="run_008")

        self.assertEqual(exit_code, 0)
        self.assertEqual(started["dashboard_dir"], dashboard_dir.resolve())
        wait.assert_called_once_with("127.0.0.1", 4123, "run_008")
        self.assertEqual(opened, ["http://127.0.0.1:4123/?run_id=run_008"])


    def test_dashboard_launcher_reuses_existing_server(self) -> None:
        from critiqor.dashboard import serve_dashboard, write_dashboard_server_record

        opened: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            dashboard_dir = Path(tmp) / "core"
            dashboard_dir.mkdir()
            (dashboard_dir / "package.json").write_text("{}", encoding="utf-8")
            (dashboard_dir / "src" / "routes").mkdir(parents=True)
            (dashboard_dir / "src" / "routes" / "index.tsx").write_text("", encoding="utf-8")
            (dashboard_dir / "src" / "lib").mkdir(parents=True)
            (dashboard_dir / "src" / "lib" / "critiqor-api-store.server.ts").write_text("", encoding="utf-8")
            runs_dir = Path(tmp) / "runs"
            run_dir = runs_dir / "run_009"
            run_dir.mkdir(parents=True)
            (run_dir / "diagnosis.json").write_text(json.dumps({"run_id": "run_009", "executive_summary": {"trust_score": 90}}), encoding="utf-8")
            write_dashboard_server_record(runs_dir, "127.0.0.1", 4444, 12345, dashboard_dir)

            with patch.dict(os.environ, {"CRITIQOR_DASHBOARD_DIR": str(dashboard_dir)}),                 patch("critiqor.dashboard.wait_for_dashboard_run") as wait,                 patch("critiqor.dashboard.start_core_engine_dashboard") as start,                 patch("critiqor.dashboard.webbrowser.open", opened.append):
                exit_code = serve_dashboard(runs_dir=str(runs_dir), host="127.0.0.1", run_id="run_009")

        self.assertEqual(exit_code, 0)
        self.assertFalse(start.called)
        wait.assert_called_with("127.0.0.1", 4444, "run_009")
        self.assertEqual(opened, ["http://127.0.0.1:4444/?run_id=run_009"])

    def test_dashboard_launcher_aborts_when_run_is_missing(self) -> None:
        from critiqor.dashboard import serve_dashboard

        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(output), patch("critiqor.dashboard.start_core_engine_dashboard") as start:
            exit_code = serve_dashboard(runs_dir=tmp, run_id="run_008")

        self.assertEqual(exit_code, 1)
        self.assertFalse(start.called)
        self.assertIn("Run run_008 not found.", output.getvalue())

    def test_openclaw_diagnosis_detects_runtime_failure_taxonomy(self) -> None:
        events = [
            {"event": "tool_call", "tool": "search", "args": {"q": "alpha"}},
            {"event": "tool_output", "tool": "search", "output": "alpha evidence", "used": False},
            {"event": "tool_call", "tool": "search", "args": {"q": "alpha"}},
            {"event": "retry_event", "tool": "search"},
            {"event": "tool_call", "tool": "search", "args": {"q": "alpha"}},
            {"event": "memory_event", "action": "recall_failed", "key": "plan"},
            {"event": "context_event", "saturation": 91},
            {"event": "token_usage", "usage": {"total": 16000}},
            {"event": "skill_event", "skill": "retrieve", "status": "ignored"},
        ]

        diagnosis = diagnose_openclaw_events(events).to_dict()
        cause_types = {cause["type"] for cause in diagnosis["failure_causes"]}

        self.assertIn("infinite_tool_loop", cause_types)
        self.assertIn("ignoring_tool_outputs", cause_types)
        self.assertIn("memory_degradation", cause_types)
        self.assertIn("context_pollution", cause_types)
        self.assertIn("cost_explosion", cause_types)
        self.assertIn("skill_failure", cause_types)
        self.assertEqual(diagnosis["readiness_level"], "review_recommended")
        self.assertTrue(diagnosis["causal_graph"]["edges"])

    def test_openclaw_ingestion_generates_backend_run_diagnosis_view(self) -> None:
        index = AgentReliabilityIndex()
        payload = build_openclaw_run_payload(
            agent_id="openclaw_a",
            tenant_id="tenant_a",
            visibility="anonymous",
            events=[
                {"event": "tool_call", "tool": "browser", "args": {"url": "x"}},
                {"event": "tool_output", "tool": "browser", "output": "result", "used": False},
            ],
        )

        accepted = index.ingest_run(payload)
        view = index.dashboard.run_diagnosis_view(accepted.run_id)
        update = index.dashboard.set_run_visibility(accepted.run_id, "public")

        self.assertEqual(view["framework"], "openclaw")
        self.assertEqual(view["executive_summary"]["evidence_level"], "fully_instrumented")
        self.assertEqual(view["primary_diagnosis"]["root_cause_failure_type"], "ignoring_tool_outputs")
        self.assertEqual(len(view["evidence_panel"]["tool_outputs"]), 1)
        self.assertEqual(update["visibility"], "public")
        self.assertTrue(index.store.runs[accepted.run_id].public_benchmark)

    def test_openclaw_process_monitor_parses_jsonl_runtime_events(self) -> None:
        payload = monitor_openclaw_process(
            [
                "python3",
                "-c",
                "import json; print(json.dumps({'event':'tool_call','tool':'search','args':{'q':'a'}})); print(json.dumps({'event':'tool_output','tool':'search','output':'a','used':False}))",
            ],
            agent_id="openclaw_cli",
        )

        self.assertEqual(payload["framework"], "openclaw")
        self.assertEqual(payload["evidence_summary"]["tool_calls"], 1)
        self.assertEqual(payload["primary_diagnosis"]["root_cause_failure_type"], "ignoring_tool_outputs")

    def test_cli_monitor_openclaw_writes_event_log_and_dashboard_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            events = f"{temp_dir}/events.jsonl"
            evaluation = f"{temp_dir}/latest.json"
            exit_code = cli_main([
                "monitor",
                "openclaw",
                "--events",
                events,
                "--evaluation",
                evaluation,
                "--agent-id",
                "openclaw_cli",
                "--",
                "python3",
                "-c",
                "import json; print(json.dumps({'event':'tool_call','tool':'search','args':{'q':'a'}})); print(json.dumps({'event':'tool_output','tool':'search','output':'a','used':False}))",
            ])

            with open(evaluation, encoding="utf-8") as handle:
                payload = __import__("json").load(handle)

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["framework"], "openclaw")
        self.assertTrue(payload["evidence_panel"]["causal_graph"]["nodes"])

    def test_session_finalize_persists_completed_run_artifact(self) -> None:
        from critiqor.session import create_session, finalize_session, load_active_session

        with tempfile.TemporaryDirectory() as tmp:
            session = create_session(runs_dir=tmp, agent_id="openclaw_test")
            self.assertEqual(session["status"], "MONITORING")
            self.assertIsNotNone(load_active_session(tmp))

            completed = finalize_session(tmp)
            self.assertIsNotNone(completed)
            assert completed is not None
            self.assertEqual(completed["status"], "COMPLETED")
            self.assertEqual(completed["run_id"], "run_001")
            self.assertIsNone(load_active_session(tmp))
            self.assertIn("diagnosis", completed)
            self.assertIn("event_log", completed)
            self.assertIn("trust_score", completed)
            self.assertIn("confidence_score", completed)
            self.assertIn("causal_graph", completed)
            self.assertIn("failure_analysis", completed)
            self.assertIn("cost_analysis", completed)

    def test_finalize_without_active_session_is_user_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cli_main(["finalize", "--runs-dir", tmp, "--no-dashboard"]), 0)

    def test_finalize_launches_local_dashboard_with_generated_diagnosis(self) -> None:
        from critiqor.session import create_session

        served: dict[str, object] = {}

        def fake_serve(events: str, runs_dir: str, host: str, port: int, run_id: str | None, open_browser: bool) -> None:
            served.update({"events": events, "runs_dir": runs_dir, "host": host, "port": port, "run_id": run_id, "open_browser": open_browser})

        with tempfile.TemporaryDirectory() as tmp:
            create_session(runs_dir=tmp, agent_id="openclaw_test")
            with patch("critiqor.dashboard.serve_dashboard", fake_serve):
                exit_code = cli_main(["finalize", "--runs-dir", tmp])

            diagnosis_path = Path(tmp) / "run_001" / "diagnosis.json"
            session_path = Path(tmp) / "run_001" / "session.json"
            self.assertTrue(diagnosis_path.exists())
            self.assertTrue(session_path.exists())
            session_payload = json.loads(session_path.read_text(encoding="utf-8"))

            self.assertEqual(served["runs_dir"], tmp)

        self.assertEqual(exit_code, 0)
        self.assertEqual(served["run_id"], "run_001")
        self.assertEqual(served["port"], 0)
        self.assertTrue(served["open_browser"])
        self.assertIn("events", session_payload)

    def test_finalize_aborts_dashboard_when_diagnosis_is_invalid(self) -> None:
        from critiqor.session import create_session

        output = io.StringIO()

        def invalid_run(runs_dir: str, run_id: str) -> dict[str, object]:
            return {"run_id": run_id}

        with tempfile.TemporaryDirectory() as tmp:
            create_session(runs_dir=tmp, agent_id="openclaw_test")
            with patch("critiqor.dashboard.load_diagnosis_run", invalid_run), patch("critiqor.dashboard.serve_dashboard") as serve, contextlib.redirect_stdout(output):
                exit_code = cli_main(["finalize", "--runs-dir", tmp])

        self.assertEqual(exit_code, 1)
        self.assertFalse(serve.called)
        self.assertIn("Diagnosis file invalid. Dashboard launch aborted.", output.getvalue())

    def test_runs_command_lists_completed_diagnosis_summaries(self) -> None:
        from critiqor.session import create_session, finalize_session

        output = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            create_session(runs_dir=tmp, agent_id="openclaw_test")
            finalize_session(tmp)
            with contextlib.redirect_stdout(output):
                exit_code = cli_main(["runs", "--runs-dir", tmp])

        text = output.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("Available Runs", text)
        self.assertIn("run_001 | Trust:", text)
        self.assertIn("Tool Calls", text)

    def test_dashboard_command_opens_specific_local_run(self) -> None:
        served: dict[str, object] = {}

        def fake_serve(events: str, runs_dir: str, host: str, port: int, run_id: str | None, open_browser: bool) -> None:
            served.update({"run_id": run_id, "runs_dir": runs_dir, "port": port, "open_browser": open_browser})

        with patch("critiqor.dashboard.serve_dashboard", fake_serve):
            exit_code = cli_main(["dashboard", "run_008", "--runs", "runs"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(served["run_id"], "run_008")
        self.assertEqual(served["port"], 0)

    def test_cli_help_lists_available_critiqor_commands(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exit_code = cli_main(["help"])

        help_text = output.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn("Critiqor CLI", help_text)
        self.assertIn("critiqor monitor openclaw", help_text)
        self.assertIn("critiqor finalize", help_text)
        self.assertIn("critiqor dashboard", help_text)
        self.assertIn("critiqor help", help_text)

    def test_monitor_openclaw_launches_child_after_session_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            command = f"{sys.executable} -c 'import os; assert os.environ.get(\"CRITIQOR_RUN_ID\")'"
            monitor_code = cli_main(
                [
                    "monitor",
                    "openclaw",
                    "--runs-dir",
                    temp_dir,
                    "--openclaw-command",
                    command,
                ]
            )
            finalize_code = cli_main(["finalize", "--runs-dir", temp_dir, "--no-dashboard"])
            run_path = f"{temp_dir}/run_001.json"
            with open(run_path, encoding="utf-8") as handle:
                run = json.load(handle)

        events = run["event_log"]
        event_names = [event["event"] for event in events]
        process_start_index = event_names.index("process_start")
        launch_ready_index = next(
            index
            for index, event in enumerate(events)
            if event["event"] == "state_transition"
            and event.get("message") == "Observer ready before OpenClaw launch"
        )

        self.assertEqual(monitor_code, 0)
        self.assertEqual(finalize_code, 0)
        self.assertEqual(run["status"], "COMPLETED")
        self.assertLess(launch_ready_index, process_start_index)
        self.assertIn("process_end", event_names)
        self.assertIsNotNone(run["diagnosis"])



    def test_openclaw_plugin_files_are_packaged(self) -> None:
        from critiqor.runtime import critiqor_openclaw_plugin_dir

        plugin_dir = critiqor_openclaw_plugin_dir()

        self.assertTrue((plugin_dir / "index.js").exists())
        self.assertTrue((plugin_dir / "openclaw.plugin.json").exists())
        manifest = json.loads((plugin_dir / "openclaw.plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["id"], "critiqor")
        self.assertTrue(manifest["activation"]["onStartup"])

    def test_finalize_prefers_plugin_session_json_evidence(self) -> None:
        from critiqor.session import create_session, finalize_session

        with tempfile.TemporaryDirectory() as tmp:
            session = create_session(runs_dir=tmp, agent_id="openclaw_test")
            run_id = session["run_id"]
            evidence_dir = Path(tmp) / run_id
            evidence_dir.mkdir(parents=True, exist_ok=True)
            evidence_path = evidence_dir / "session.json"
            evidence_path.write_text(
                json.dumps(
                    {
                        "session_id": run_id,
                        "run_id": run_id,
                        "schema_version": "critiqor.session.v1",
                        "events_file": "session.json",
                        "events": [
                            {
                                "timestamp": "2026-06-20T00:00:00Z",
                                "event_type": "tool_call",
                                "source_layer": "tool_hooks",
                                "tool_name": "memory_search",
                                "tool_call_id": "call_1",
                                "payload": {"toolName": "memory_search", "input": {"query": "prior decision"}},
                            },
                            {
                                "timestamp": "2026-06-20T00:00:01Z",
                                "event_type": "tool_result",
                                "source_layer": "tool_hooks",
                                "tool_name": "memory_search",
                                "tool_call_id": "call_1",
                                "status": "ok",
                                "duration_ms": 22,
                                "payload": {"toolName": "memory_search", "content": [{"type": "text", "text": "Found prior decision"}]},
                            },
                            {
                                "timestamp": "2026-06-20T00:00:01Z",
                                "event_type": "memory_search",
                                "source_layer": "tool_hooks",
                                "tool_name": "memory_search",
                                "tool_call_id": "call_1",
                                "payload": {"toolName": "memory_search", "observed_as": "tool_output"},
                            },
                        ],
                        "metrics": {},
                    }
                ),
                encoding="utf-8",
            )

            completed = finalize_session(tmp)
            assert completed is not None
            diagnosis_path = evidence_dir / "diagnosis.json"
            summary_path = evidence_dir / "session.json"

            self.assertEqual(completed["status"], "COMPLETED")
            self.assertTrue(diagnosis_path.exists())
            self.assertTrue(summary_path.exists())
            event_names = [event["event"] for event in completed["event_log"]]
            self.assertIn("tool_call", event_names)
            self.assertIn("tool_output", event_names)
            self.assertIn("memory_event", event_names)
            diagnosis = json.loads(diagnosis_path.read_text(encoding="utf-8"))
            self.assertEqual(diagnosis["run_id"], run_id)
            self.assertIn("raw_evidence", diagnosis)


if __name__ == "__main__":
    unittest.main()
