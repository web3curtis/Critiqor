from __future__ import annotations

from typing import Any

from .events import event_message, event_name, is_error, is_retry
from .recommendations import recommendation_for


def failure_cause(event: dict[str, Any], index: int) -> dict[str, Any]:
    name = event_name(event)
    message = event_message(event)
    impact = 18 if is_error(event) else 8
    recommendation = recommendation_for(name)
    return {
        "type": name,
        "failure_type": name,
        "severity": "high" if is_error(event) else "medium",
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


def causal_graph(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    signals = [event for event in events if is_error(event) or is_retry(event)]
    nodes = [
        {"id": f"event_{index}", "label": event_name(event), "kind": "error" if is_error(event) else "runtime"}
        for index, event in enumerate(signals)
    ]
    edges = [
        {"id": f"edge_{index}", "source": nodes[index - 1]["id"], "target": nodes[index]["id"], "label": "preceded"}
        for index in range(1, len(nodes))
    ]
    return {"nodes": nodes, "edges": edges}


def scores(event_count: int, errors: int, retries: int, has_tools: bool) -> tuple[int, int]:
    trust = max(0, 100 - min(70, errors * 15 + retries * 4))
    confidence = min(98, 55 + min(30, event_count * 2) + (10 if has_tools else 0))
    return trust, confidence
