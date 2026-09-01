from __future__ import annotations

from collections import Counter
from typing import Any

from .analysis import causal_graph, failure_cause, scores
from .events import event_name, is_error, is_internal, is_retry, select
from .memory import memory_analysis, memory_failure_cause, memory_events


def generate_diagnosis(
    *, run_id: str, metadata: dict[str, Any], events: list[dict[str, Any]], session_json: str,
) -> dict[str, Any]:
    trace = [event for event in events if not is_internal(event)]
    errors = [event for event in trace if is_error(event)]
    retries = [event for event in trace if is_retry(event)]
    tool_calls = select(trace, "tool_call", "tool_start")
    tool_outputs = select(trace, "tool_output", "tool_result", "tool_end")
    memory = memory_events(trace)
    memory_signal = memory_analysis(trace)
    context = select(trace, "context_event", "before_provider_request", "after_provider_response")
    tokens = select(trace, "token_usage")
    trust, confidence = scores(len(trace), len(errors), len(retries), bool(tool_calls))
    causes = [failure_cause(event, index) for index, event in enumerate(trace) if is_error(event)]
    if not causes:
        causes = [failure_cause(event, index) for index, event in enumerate(trace) if is_retry(event)]
    memory_cause = memory_failure_cause(trace)
    if memory_cause is not None:
        causes.append(memory_cause)
        trust = max(0, trust - int(memory_cause["impact"]))
        confidence = min(98, max(confidence, int(memory_signal["confidence"])))
    if errors:
        failure_type = "runtime_error"
        explanation = f"Critiqor observed {len(errors)} runtime error signal(s) in the finalized evidence."
        action = "Inspect the highest-impact runtime error and replay the supporting evidence timeline."
    elif retries:
        failure_type = "retry_pressure"
        explanation = f"Critiqor observed {len(retries)} retry signal(s) without a terminal runtime error."
        action = "Review repeated requests and add a retry budget or strategy switch."
    elif memory_cause is not None:
        failure_type = "memory_utilization"
        explanation = str(memory_cause["description"])
        action = str(memory_cause["recommendation"])
    else:
        failure_type = None
        explanation = "No major runtime failure signal was detected in the collected evidence."
        action = "Continue monitoring future runs for regressions."
    return {
        "schema_version": "critiqor.diagnosis.v1",
        "run_id": run_id,
        "tenant_id": metadata.get("tenant_id", "default"),
        "agent_id": metadata.get("agent_id", "agent"),
        "framework": metadata.get("framework", "custom"),
        "visibility": metadata.get("visibility", "private"),
        "diagnosis_source": "local",
        "evaluation_confidence": confidence,
        "executive_summary": {
            "trust_score": trust,
            "readiness_level": "ready_for_runtime" if trust >= 85 else "review_recommended" if trust >= 65 else "unsafe_for_production",
            "evidence_level": "fully_instrumented" if tool_calls or tool_outputs or len(trace) >= 3 else "trace_available" if trace else "response_only",
            "evaluation_confidence": confidence,
            "event_count": len(trace), "summary": explanation, "run_id": run_id,
        },
        "primary_diagnosis": {
            "root_cause_failure_type": failure_type,
            "causal_chain_explanation": explanation,
            "recommended_next_action": action,
        },
        "failure_analysis": {
            "failure_causes": causes,
            "top_failure_modes": [name for name, _count in Counter(event_name(event) for event in errors).most_common(5)],
            "frequency_distribution": dict(Counter(event_name(event) for event in trace)),
        },
        "cost_analysis": {
            "retry_count": len(retries), "tool_call_count": len(tool_calls), "redundant_action_count": len(retries),
            "tool_output_count": len(tool_outputs), "token_usage_event_count": len(tokens),
            "memory_event_count": len(memory), "memory_token_cost": memory_signal["token_cost"],
            "unused_memory_count": memory_signal["unused_count"],
            "irrelevant_memory_count": memory_signal["irrelevant_count"],
            "missed_memory_count": memory_signal["missed_count"],
        },
        "recommendations": [action],
        "evidence_panel": {
            "trace": trace, "tool_calls": tool_calls, "tool_outputs": tool_outputs, "memory_events": memory,
            "context_events": context, "token_usage": tokens, "retries": retries, "failures": errors,
            "memory_analysis": memory_signal,
            "causal_graph": causal_graph(trace),
        },
        "raw_evidence": {"session_json": session_json},
    }
