"""Framework-agnostic local diagnosis generation from normalized runtime evidence."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _event_name(event: dict[str, Any]) -> str:
    return str(event.get("event_type") or event.get("event") or "runtime_event")


def _is_error(event: dict[str, Any]) -> bool:
    name = _event_name(event).casefold()
    if name in {"error", "error_event", "failure", "timeout", "evidence_parse_error"}:
        return True
    status = str(event.get("status") or "").casefold()
    return status in {"error", "failed", "failure", "timeout"}


def build_local_diagnosis(
    *, run_id: str, metadata: dict[str, Any], events: list[dict[str, Any]], session_json: str,
) -> dict[str, Any]:
    """Convert one normalized session into the dashboard diagnosis contract."""
    names = [_event_name(event) for event in events]
    counts = Counter(names)
    errors = [event for event in events if _is_error(event)]
    retries = [event for event in events if "retry" in _event_name(event).casefold()]
    tool_calls = [event for event in events if _event_name(event) in {"tool_call", "tool_start"}]
    tool_outputs = [event for event in events if _event_name(event) in {"tool_output", "tool_result", "tool_end"}]
    memory_events = [event for event in events if _event_name(event) in {"memory_event", "memory_search", "memory_get"}]
    evidence_count = len(events)
    penalty = min(70, len(errors) * 15 + len(retries) * 4)
    trust_score = max(0, 100 - penalty)
    confidence = min(98, 55 + min(30, evidence_count * 2) + (10 if tool_calls else 0))
    if errors:
        failure_type = "runtime_error"
        explanation = f"Critiqor observed {len(errors)} runtime error signal(s) in the finalized evidence."
    elif retries:
        failure_type = "retry_pressure"
        explanation = f"Critiqor observed {len(retries)} retry signal(s) without a terminal runtime error."
    else:
        failure_type = "no_major_failure_detected"
        explanation = "No major runtime failure signal was detected in the collected evidence."
    readiness = "ready_for_runtime" if trust_score >= 85 else "review_recommended" if trust_score >= 65 else "unsafe_for_production"
    failure_causes = [
        {
            "failure_type": _event_name(event),
            "severity": "high" if _is_error(event) else "medium",
            "summary": str(event.get("message") or event.get("payload") or _event_name(event)),
            "evidence_index": index,
        }
        for index, event in enumerate(events) if _is_error(event)
    ]
    nodes = [
        {"id": f"event_{index}", "label": _event_name(event), "kind": "error" if _is_error(event) else "runtime"}
        for index, event in enumerate(events) if _is_error(event) or "retry" in _event_name(event).casefold()
    ]
    edges = [
        {"id": f"edge_{index}", "source": nodes[index - 1]["id"], "target": nodes[index]["id"], "label": "preceded"}
        for index in range(1, len(nodes))
    ]
    return {
        "run_id": run_id,
        "tenant_id": metadata.get("tenant_id", "default"),
        "agent_id": metadata.get("agent_id", "agent"),
        "framework": metadata.get("framework", "custom"),
        "visibility": metadata.get("visibility", "private"),
        "diagnosis_source": "local",
        "executive_summary": {
            "trust_score": trust_score,
            "readiness_level": readiness,
            "evidence_level": "trace_available" if events else "response_only",
            "evaluation_confidence": confidence,
            "event_count": evidence_count,
            "summary": explanation,
        },
        "primary_diagnosis": {
            "root_cause_failure_type": failure_type,
            "causal_chain_explanation": explanation,
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
        },
        "recommendations": (["Review the captured runtime errors and their preceding evidence."] if errors else ["Continue monitoring future runs for regressions."]),
        "evidence_panel": {
            "trace": events,
            "tool_calls": tool_calls,
            "tool_outputs": tool_outputs,
            "memory_events": memory_events,
            "causal_graph": {"nodes": nodes, "edges": edges},
        },
        "raw_evidence": {"session_json": session_json},
    }
