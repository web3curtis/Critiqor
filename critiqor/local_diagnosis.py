"""Portable evidence-to-dashboard adapter used when hosted diagnosis is unavailable.

This module does not contain Critiqor's proprietary evaluation engine. It preserves
the public artifact contract so a captured session can always be finalized and
reviewed locally.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


def _name(event: dict[str, Any]) -> str:
    return str(event.get("event_type") or event.get("event") or "runtime_event")


def _payload(event: dict[str, Any]) -> dict[str, Any]:
    return event.get("payload") if isinstance(event.get("payload"), dict) else {}


def _message(event: dict[str, Any]) -> str:
    payload = _payload(event)
    for key in ("message", "summary", "error", "status"):
        value = event.get(key) or payload.get(key)
        if value:
            return str(value)
    tool = event.get("tool") or event.get("tool_name") or payload.get("tool") or payload.get("toolName")
    return f"{_name(event)}: {tool}" if tool else _name(event).replace("_", " ")


def _internal(event: dict[str, Any]) -> bool:
    payload = _payload(event)
    text = " ".join(
        str(value or "") for value in (
            event.get("source"), event.get("source_layer"), event.get("message"),
            payload.get("source"), payload.get("source_layer"), payload.get("message"),
        )
    ).casefold()
    return any(marker in text for marker in (
        "critiqor_backend", "hosted diagnosis unavailable", "diagnosis backend unavailable",
        "critiqor_dashboard", "dashboard launch", "core engine dashboard",
    ))


def _error(event: dict[str, Any]) -> bool:
    if _internal(event):
        return False
    return _name(event).casefold() in {"error", "error_event", "failure", "timeout", "evidence_parse_error"} or str(
        event.get("status") or ""
    ).casefold() in {"error", "failed", "failure", "timeout"}


def _retry(event: dict[str, Any]) -> bool:
    return "retry" in _name(event).casefold()


def _recommendation(event: dict[str, Any]) -> str:
    name = _name(event).casefold()
    if "retry" in name:
        return "Inspect repeated requests and add a loop guard or strategy switch."
    if "timeout" in name:
        return "Review timeout thresholds and the external dependency involved in the failure."
    if "tool" in name:
        return "Inspect the tool call, its arguments, and the corresponding tool output."
    return "Review the supporting runtime evidence around this event."


def _cause(event: dict[str, Any], index: int) -> dict[str, Any]:
    name = _name(event)
    message = _message(event)
    impact = 18 if _error(event) else 8
    recommendation = _recommendation(event)
    return {
        "type": name,
        "failure_type": name,
        "severity": "high" if _error(event) else "medium",
        "impact": impact,
        "impact_score": impact,
        "description": message,
        "summary": message,
        "root_cause": name.replace("_", " "),
        "evidence": [event],
        "evidence_index": index,
        "causal_chain": [name, message, f"-{impact} trust impact"],
        "recommendation": recommendation,
        "recommendations": [recommendation],
    }


def build_local_diagnosis(
    *, run_id: str, metadata: dict[str, Any], events: list[dict[str, Any]], session_json: str,
) -> dict[str, Any]:
    """Create a dashboard-compatible summary without requiring a network backend."""
    trace = [event for event in events if not _internal(event)]
    errors = [event for event in trace if _error(event)]
    retries = [event for event in trace if _retry(event)]
    tool_calls = [event for event in trace if _name(event) in {"tool_call", "tool_start"}]
    tool_outputs = [event for event in trace if _name(event) in {"tool_output", "tool_result", "tool_end"}]
    memory = [event for event in trace if _name(event) in {"memory_event", "memory_search", "memory_get"}]
    context = [event for event in trace if _name(event) in {"context_event", "before_provider_request", "after_provider_response"}]
    tokens = [event for event in trace if _name(event) == "token_usage"]
    causes = [_cause(event, index) for index, event in enumerate(trace) if _error(event)]
    if not causes:
        causes = [_cause(event, index) for index, event in enumerate(trace) if _retry(event)]
    signals = [event for event in trace if _error(event) or _retry(event)]
    nodes = [{"id": f"event_{index}", "label": _name(event), "kind": "error" if _error(event) else "runtime"}
             for index, event in enumerate(signals)]
    edges = [{"id": f"edge_{index}", "source": nodes[index - 1]["id"], "target": nodes[index]["id"], "label": "preceded"}
             for index in range(1, len(nodes))]
    trust = max(0, 100 - min(70, len(errors) * 15 + len(retries) * 4))
    confidence = min(98, 55 + min(30, len(trace) * 2) + (10 if tool_calls else 0))
    failure_type = "runtime_error" if errors else "retry_pressure" if retries else None
    if errors:
        explanation = f"Critiqor observed {len(errors)} runtime error signal(s) in the finalized evidence."
        action = "Inspect the highest-impact runtime error and replay the supporting evidence timeline."
    elif retries:
        explanation = f"Critiqor observed {len(retries)} retry signal(s) without a terminal runtime error."
        action = "Review repeated requests and add a retry budget or strategy switch."
    else:
        explanation = "No major runtime failure signal was detected in the collected evidence."
        action = "Continue monitoring future runs for regressions."
    return {
        "schema_version": "critiqor.diagnosis.v1",
        "run_id": run_id,
        "tenant_id": metadata.get("tenant_id", "default"),
        "agent_id": metadata.get("agent_id", "agent"),
        "framework": metadata.get("framework", "custom"),
        "visibility": metadata.get("visibility", "private"),
        "diagnosis_source": "local_fallback",
        "evaluation_confidence": confidence,
        "executive_summary": {
            "trust_score": trust,
            "readiness_level": "ready_for_runtime" if trust >= 85 else "review_recommended" if trust >= 65 else "unsafe_for_production",
            "evidence_level": "fully_instrumented" if tool_calls or tool_outputs or len(trace) >= 3 else "trace_available" if trace else "response_only",
            "evaluation_confidence": confidence,
            "event_count": len(trace),
            "summary": explanation,
            "run_id": run_id,
        },
        "primary_diagnosis": {
            "root_cause_failure_type": failure_type,
            "causal_chain_explanation": explanation,
            "recommended_next_action": action,
        },
        "failure_analysis": {
            "failure_causes": causes,
            "top_failure_modes": [name for name, _count in Counter(_name(event) for event in errors).most_common(5)],
            "frequency_distribution": dict(Counter(_name(event) for event in trace)),
        },
        "cost_analysis": {
            "retry_count": len(retries), "tool_call_count": len(tool_calls),
            "redundant_action_count": len(retries), "tool_output_count": len(tool_outputs),
            "token_usage_event_count": len(tokens),
        },
        "recommendations": [action],
        "evidence_panel": {
            "trace": trace, "tool_calls": tool_calls, "tool_outputs": tool_outputs,
            "memory_events": memory, "context_events": context, "token_usage": tokens,
            "retries": retries, "failures": errors, "causal_graph": {"nodes": nodes, "edges": edges},
        },
        "raw_evidence": {"session_json": session_json},
    }
