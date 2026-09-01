from __future__ import annotations

from typing import Any

from .events import event_message, event_name, payload


def memory_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        event
        for event in events
        if event_name(event) in {"memory_event", "memory_search", "memory_get", "memory_create", "memory_store"}
    ]


def memory_analysis(events: list[dict[str, Any]]) -> dict[str, Any]:
    observed = memory_events(events)
    retrieved = [event for event in observed if memory_action(event) in {"retrieved", "search", "get"}]
    ignored = [event for event in observed if memory_action(event) in {"ignored", "skipped", "not_stored"}]
    created = [event for event in observed if memory_action(event) in {"created", "stored", "store"}]
    injected = [event for event in observed if memory_action(event) in {"injected", "context_injected"}]
    referenced = [event for event in observed if memory_action(event) in {"referenced", "used"} or is_marked_used(event)]
    unused = [event for event in retrieved if is_marked_unused(event)]
    irrelevant = [event for event in retrieved if is_marked_irrelevant(event)]
    missed = [event for event in observed if memory_action(event) in {"missed", "not_retrieved"}]
    token_cost = sum(memory_tokens(event) for event in observed)
    harmful = len(unused) + len(irrelevant) + len(missed)
    helpful = len(referenced)
    score = max(0, min(100, 100 - harmful * 14 - max(0, len(injected) - helpful) * 6 - min(18, token_cost // 250)))
    if not observed:
        score = 100
    confidence = min(
        96,
        45
        + min(25, len(observed) * 5)
        + (12 if retrieved else 0)
        + (12 if injected else 0)
        + (12 if referenced or unused or irrelevant or missed else 0),
    )
    return {
        "score": score,
        "confidence": confidence if observed else 0,
        "event_count": len(observed),
        "retrieved_count": len(retrieved),
        "injected_count": len(injected),
        "referenced_count": len(referenced),
        "unused_count": len(unused),
        "irrelevant_count": len(irrelevant),
        "missed_count": len(missed),
        "created_count": len(created),
        "ignored_count": len(ignored),
        "token_cost": token_cost,
        "diagnostic_summary": diagnostic_summary(len(retrieved), len(referenced), len(unused), len(irrelevant), len(missed)),
        "architecture_stage": architecture_stage(observed),
        "evidence": memory_evidence(observed),
    }


def memory_failure_cause(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    analysis = memory_analysis(events)
    if not analysis["event_count"]:
        return None
    harmful = analysis["unused_count"] + analysis["irrelevant_count"] + analysis["missed_count"]
    if harmful == 0 and analysis["score"] >= 80:
        return None
    impact = max(8, min(28, 100 - int(analysis["score"])))
    evidence = memory_events(events)[:8]
    issue = "memory_utilization"
    return {
        "type": issue,
        "failure_type": issue,
        "severity": "high" if impact >= 20 else "medium",
        "impact": impact,
        "impact_score": impact,
        "description": analysis["diagnostic_summary"],
        "summary": analysis["diagnostic_summary"],
        "root_cause": "Memory behavior reduced runtime quality based on retrieved, injected, referenced, unused, or missed memory evidence.",
        "evidence": evidence,
        "causal_chain": [
            "memory lookup",
            analysis["architecture_stage"],
            analysis["diagnostic_summary"],
            f"-{impact} trust impact",
        ],
        "recommendation": memory_recommendation(analysis),
        "recommendations": memory_recommendations(analysis),
        "verification_steps": [
            "Rerun the same task with Critiqor monitoring and confirm irrelevant or unused memory evidence no longer appears.",
            "Compare retrieved memory ids against response references and verify memory utilization improves without lower task completion.",
        ],
        "expected_improvement": f"Up to {impact} trust points may be recovered after a verified rerun shows memory retrieval improves runtime quality.",
        "memory_analysis": analysis,
        "engineering_explanation": engineering_explanation(analysis),
        "teaching_diagram": teaching_diagram(analysis),
    }


def memory_action(event: dict[str, Any]) -> str:
    data = payload(event)
    raw = str(data.get("action") or data.get("operation") or data.get("status") or data.get("memory_action") or "").casefold()
    name = event_name(event).casefold()
    text = f"{name} {raw} {event_message(event)}".casefold()
    if "not stored" in text or "temporary" in text:
        return "not_stored"
    if "not retrieved" in text or "missed" in text:
        return "missed"
    if "irrelevant" in text:
        return "retrieved"
    if "unused" in text or "not used" in text:
        return "retrieved"
    if "inject" in text or "context" in text:
        return "injected"
    if "referenc" in text or "used" in text:
        return "referenced"
    if "creat" in text or "stor" in text:
        return "created"
    if "ignor" in text or "skip" in text:
        return "ignored"
    if "search" in name:
        return "search"
    if "get" in name:
        return "get"
    return raw or "retrieved"


def is_marked_used(event: dict[str, Any]) -> bool:
    data = payload(event)
    return data.get("used") is True or data.get("referenced") is True or data.get("influenced_response") is True


def is_marked_unused(event: dict[str, Any]) -> bool:
    data = payload(event)
    text = f"{event_message(event)} {data}".casefold()
    return data.get("used") is False or data.get("referenced") is False or "unused" in text or "not used" in text


def is_marked_irrelevant(event: dict[str, Any]) -> bool:
    data = payload(event)
    relevance = data.get("relevance") or data.get("quality")
    if isinstance(relevance, str) and relevance.casefold() in {"irrelevant", "low", "bad"}:
        return True
    score = data.get("score") or data.get("similarity") or data.get("relevance_score")
    if isinstance(score, (int, float)) and float(score) < 0.35:
        return True
    return "irrelevant" in f"{event_message(event)} {data}".casefold()


def memory_tokens(event: dict[str, Any]) -> int:
    data = payload(event)
    value = data.get("tokens") or data.get("token_count") or data.get("context_tokens")
    return int(value) if isinstance(value, (int, float)) and value > 0 else 0


def diagnostic_summary(retrieved: int, referenced: int, unused: int, irrelevant: int, missed: int) -> str:
    if missed:
        return f"Critiqor observed {missed} memory item(s) that should have been retrieved but were absent from runtime context."
    if irrelevant or unused:
        return (
            f"The agent retrieved {retrieved} memory item(s), but {unused + irrelevant} were unused or irrelevant "
            f"and only {referenced} were supported by response evidence."
        )
    return f"The agent retrieved {retrieved} memory item(s), with {referenced} supported use signal(s) in runtime evidence."


def architecture_stage(events: list[dict[str, Any]]) -> str:
    text = " ".join(f"{event_name(event)} {event_message(event)} {payload(event)}" for event in events).casefold()
    if "rerank" in text:
        return "retrieval ranking"
    if "inject" in text or "context" in text:
        return "context injection"
    if "embed" in text or "similarity" in text or "vector" in text:
        return "vector similarity"
    if "stor" in text or "creat" in text:
        return "memory update"
    return "memory retrieval"


def memory_evidence(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for event in events[:20]:
        data = payload(event)
        items.append(
            {
                "event_type": event_name(event),
                "action": memory_action(event),
                "message": event_message(event),
                "memory_id": data.get("memory_id") or data.get("id"),
                "reason": data.get("reason") or memory_reason(event),
                "architecture_stage": architecture_stage([event]),
                "confidence": data.get("confidence"),
                "runtime_event": event,
            }
        )
    return items


def memory_reason(event: dict[str, Any]) -> str:
    data = payload(event)
    if is_marked_irrelevant(event):
        return "Runtime evidence marked the retrieved memory as low relevance or irrelevant."
    if is_marked_unused(event):
        return "The memory was retrieved or injected but runtime evidence did not show response use."
    if is_marked_used(event):
        return "Runtime evidence linked the memory to the response or reasoning path."
    score = data.get("score") or data.get("similarity") or data.get("relevance_score")
    if isinstance(score, (int, float)):
        return f"Retrieval score was {float(score):.2f}."
    return "Critiqor captured this as a memory-related runtime event."


def memory_recommendation(analysis: dict[str, Any]) -> str:
    return memory_recommendations(analysis)[0]


def memory_recommendations(analysis: dict[str, Any]) -> list[str]:
    if analysis["missed_count"]:
        return [
            "Add retrieval recall checks for task-critical context before final response synthesis.",
            "Log candidate memories rejected by threshold so future Critiqor runs can compare missed versus retrieved context.",
            "Add a fallback query rewrite when no high-confidence memory is retrieved for recurring project or user state.",
        ]
    if analysis["irrelevant_count"] or analysis["unused_count"]:
        return [
            "Introduce a reranking stage after vector search and inject only memories with supported task relevance.",
            "Limit retrieved memories and log retrieved-versus-referenced ids for future Critiqor evaluations.",
            "Tune similarity thresholds against reruns where memory evidence improves response quality without extra token pressure.",
        ]
    return [
        "Keep memory telemetry enabled and compare retrieved-versus-referenced memory across future runs.",
        "Preserve memory ids in context injection logs so Diagnosis can trace memory impact.",
    ]


def engineering_explanation(analysis: dict[str, Any]) -> str:
    stage = analysis["architecture_stage"]
    if stage == "context injection":
        return "The memory system selected retrieved records for the prompt context. Runtime quality dropped when injected memories consumed tokens without supported response use."
    if stage == "retrieval ranking":
        return "The memory system ranked candidates after lookup. Runtime evidence suggests ranking did not separate useful memory from irrelevant or unused context."
    if stage == "vector similarity":
        return "The memory system used embedding similarity to retrieve candidates. Similarity alone can admit semantically nearby but task-irrelevant memories."
    if stage == "memory update":
        return "The memory system attempted to create or skip persistent memory. Runtime evidence should distinguish durable preferences from temporary turn details."
    return "The memory system retrieved runtime context that Critiqor evaluated by comparing lookup, injection, and response-use evidence."


def teaching_diagram(analysis: dict[str, Any]) -> dict[str, Any]:
    stages = [
        "Conversation",
        "Memory Lookup",
        "Retrieved Memories",
        "Context Construction",
        "LLM Response",
        "Critiqor Runtime Evaluation",
        "Memory Analysis",
        "Diagnosis",
    ]
    highlighted = {
        "memory retrieval": "Memory Lookup",
        "vector similarity": "Memory Lookup",
        "retrieval ranking": "Retrieved Memories",
        "context injection": "Context Construction",
        "memory update": "Memory Analysis",
    }.get(str(analysis["architecture_stage"]), "Memory Analysis")
    return {"stages": stages, "highlight": highlighted}
