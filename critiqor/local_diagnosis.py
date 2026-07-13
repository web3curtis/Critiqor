"""Framework-agnostic local diagnosis generation from normalized runtime evidence."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _event_name(event: dict[str, Any]) -> str:
    return str(event.get("event_type") or event.get("event") or "runtime_event")


def _is_error(event: dict[str, Any]) -> bool:
    if _is_internal_error(event):
        return False
    name = _event_name(event).casefold()
    if name in {"error", "error_event", "failure", "timeout", "evidence_parse_error"}:
        return True
    status = str(event.get("status") or "").casefold()
    return status in {"error", "failed", "failure", "timeout"}


def _is_internal_error(event: dict[str, Any]) -> bool:
    source = str(event.get("source") or event.get("source_layer") or "").casefold()
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    payload_source = str(payload.get("source") or payload.get("source_layer") or "").casefold()
    text = " ".join([
        source,
        payload_source,
        str(event.get("message") or ""),
        str(payload.get("message") or ""),
    ]).casefold()
    return any(
        marker in text
        for marker in (
            "critiqor_backend",
            "hosted diagnosis unavailable",
            "diagnosis backend unavailable",
            "critiqor_dashboard",
            "dashboard launch",
            "core engine dashboard",
        )
    )


def _is_retry(event: dict[str, Any]) -> bool:
    return "retry" in _event_name(event).casefold()


def _event_message(event: dict[str, Any]) -> str:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    for key in ("message", "summary", "error", "status"):
        value = event.get(key) or payload.get(key)
        if value:
            return str(value)
    tool = event.get("tool") or event.get("tool_name") or payload.get("tool") or payload.get("toolName")
    if tool:
        return f"{_event_name(event)}: {tool}"
    return _event_name(event).replace("_", " ")


def _severity_for(event: dict[str, Any]) -> str:
    if _is_error(event):
        return "high"
    if _is_retry(event):
        return "medium"
    return "low"


def _impact_for(event: dict[str, Any]) -> int:
    if _is_error(event):
        return 18
    if _is_retry(event):
        return 8
    return 4


def _recommendation_for(event_name: str) -> str:
    normalized = event_name.casefold()
    if "retry" in normalized:
        return "Inspect repeated requests and add a loop guard or strategy switch."
    if "timeout" in normalized:
        return "Review timeout thresholds and the external dependency involved in the failure."
    if "tool" in normalized:
        return "Inspect the tool call, its arguments, and the corresponding tool output."
    if "memory" in normalized:
        return "Review retrieved memory/context and confirm it was used in the final decision."
    return "Review the supporting runtime evidence around this event."


def _failure_cause(event: dict[str, Any], index: int) -> dict[str, Any]:
    event_name = _event_name(event)
    description = _event_message(event)
    recommendation = _recommendation_for(event_name)
    severity = _severity_for(event)
    impact = _impact_for(event)
    return {
        # Core Engine dashboard contract.
        "type": event_name,
        "severity": severity,
        "impact": impact,
        "impact_score": impact,
        "description": description,
        "root_cause": event_name.replace("_", " "),
        "evidence": [event],
        "causal_chain": [event_name, description, f"-{impact} trust impact"],
        "recommendation": recommendation,
        "recommendations": [recommendation],
        # Legacy/public compatibility.
        "failure_type": event_name,
        "summary": description,
        "evidence_index": index,
    }


def _evidence_level(events: list[dict[str, Any]], tool_calls: list[dict[str, Any]], tool_outputs: list[dict[str, Any]]) -> str:
    if not events:
        return "response_only"
    if tool_calls or tool_outputs or len(events) >= 3:
        return "fully_instrumented"
    return "trace_available"


def build_local_diagnosis(
    *, run_id: str, metadata: dict[str, Any], events: list[dict[str, Any]], session_json: str,
) -> dict[str, Any]:
    """Convert one normalized session into the dashboard diagnosis contract."""
    dashboard_events = [event for event in events if not _is_internal_error(event)]
    names = [_event_name(event) for event in dashboard_events]
    counts = Counter(names)
    errors = [event for event in dashboard_events if _is_error(event)]
    retries = [event for event in dashboard_events if "retry" in _event_name(event).casefold()]
    tool_calls = [event for event in dashboard_events if _event_name(event) in {"tool_call", "tool_start"}]
    tool_outputs = [event for event in dashboard_events if _event_name(event) in {"tool_output", "tool_result", "tool_end"}]
    memory_events = [event for event in dashboard_events if _event_name(event) in {"memory_event", "memory_search", "memory_get"}]
    context_events = [event for event in dashboard_events if _event_name(event) in {"context_event", "before_provider_request", "after_provider_response"}]
    token_events = [event for event in dashboard_events if _event_name(event) == "token_usage"]
    evidence_count = len(dashboard_events)
    penalty = min(70, len(errors) * 15 + len(retries) * 4)
    trust_score = max(0, 100 - penalty)
    confidence = min(98, 55 + min(30, evidence_count * 2) + (10 if tool_calls else 0))
    evidence_level = _evidence_level(events, tool_calls, tool_outputs)
    if errors:
        failure_type = "runtime_error"
        explanation = f"Critiqor observed {len(errors)} runtime error signal(s) in the finalized evidence."
        next_action = "Inspect the highest-impact runtime error and replay the supporting evidence timeline."
    elif retries:
        failure_type = "retry_pressure"
        explanation = f"Critiqor observed {len(retries)} retry signal(s) without a terminal runtime error."
        next_action = "Review repeated requests and add a retry budget or strategy switch."
    else:
        failure_type = None
        explanation = "No major runtime failure signal was detected in the collected evidence."
        next_action = "Continue monitoring future runs for regressions."
    readiness = "ready_for_runtime" if trust_score >= 85 else "review_recommended" if trust_score >= 65 else "unsafe_for_production"
    failure_causes = [_failure_cause(event, index) for index, event in enumerate(events) if _is_error(event)]
    if not failure_causes and retries:
        failure_causes = [_failure_cause(event, index) for index, event in enumerate(events) if _is_retry(event)]
    nodes = [
        {"id": f"event_{index}", "label": _event_name(event), "kind": "error" if _is_error(event) else "runtime"}
        for index, event in enumerate(dashboard_events) if _is_error(event) or "retry" in _event_name(event).casefold()
    ]
    edges = [
        {"id": f"edge_{index}", "source": nodes[index - 1]["id"], "target": nodes[index]["id"], "label": "preceded"}
        for index in range(1, len(nodes))
    ]
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
            "trust_score": trust_score,
            "readiness_level": readiness,
            "evidence_level": evidence_level,
            "evaluation_confidence": confidence,
            "event_count": evidence_count,
            "summary": explanation,
            "run_id": run_id,
        },
        "primary_diagnosis": {
            "root_cause_failure_type": failure_type,
            "causal_chain_explanation": explanation,
            "recommended_next_action": next_action,
        },
        "failure_analysis": {
            "failure_causes": failure_causes,
            "top_failure_modes": [name for name, _count in Counter(_event_name(item) for item in errors).most_common(5)],
            "frequency_distribution": dict(counts),
        },
        "cost_analysis": {
            "retry_count": len(retries),
            "tool_call_count": len(tool_calls),
            "redundant_action_count": len(retries),
            "tool_output_count": len(tool_outputs),
            "token_usage_event_count": len(token_events),
        },
        "recommendations": (
            ["Review the captured runtime errors and their preceding evidence.", "Open the runtime timeline and inspect the first failure event."]
            if errors
            else ["Inspect repeated requests and add retry boundaries."]
            if retries
            else ["Continue monitoring future runs for regressions."]
        ),
        "evidence_panel": {
            "trace": dashboard_events,
            "tool_calls": tool_calls,
            "tool_outputs": tool_outputs,
            "memory_events": memory_events,
            "context_events": context_events,
            "token_usage": token_events,
            "retries": retries,
            "failures": errors,
            "causal_graph": {"nodes": nodes, "edges": edges},
        },
        "raw_evidence": {"session_json": session_json},
    }
