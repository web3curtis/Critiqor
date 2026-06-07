"""OpenClaw runtime observation and diagnosis primitives.

Critiqor vNext observes OpenClaw execution like a process-mounted recorder: it
captures runtime events, detects OpenClaw-native failure modes, builds causal
structures, and emits structured diagnostics. No LLM judgment is used here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Sequence
from uuid import uuid4

OPENCLAW_EVENT_TYPES = {
    "tool_call",
    "tool_output",
    "memory_event",
    "retry_event",
    "error_event",
    "state_transition",
    "decision",
    "skill_event",
    "token_usage",
    "context_event",
    "process_output",
    "process_start",
    "process_end",
}

OPENCLAW_FAILURE_TAXONOMY = {
    "infinite_tool_loop": "Repeated tool calls or retries without progress.",
    "memory_degradation": "Stored or retrieved memory is lost, ignored, or fails recall.",
    "ignoring_tool_outputs": "Tool outputs are available but not incorporated into decisions.",
    "context_pollution": "Context growth, saturation, or compaction causes useful state loss.",
    "cost_explosion": "Token or call waste grows without matching progress.",
    "skill_failure": "Relevant OpenClaw skill is ignored, mis-selected, or fails invocation.",
}

OPENCLAW_BENCHMARK_WEIGHTS = {
    "loop_control": 0.20,
    "memory_integrity": 0.15,
    "tool_output_utilization": 0.20,
    "context_health": 0.15,
    "cost_efficiency": 0.15,
    "skill_adherence": 0.15,
}


@dataclass(frozen=True)
class OpenClawFailureCause:
    """OpenClaw-native failure cause bound to observed evidence."""

    type: str
    severity: str
    evidence: list[dict[str, Any]]
    causal_chain: list[str]
    impact_score: int
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "severity": self.severity,
            "evidence": [dict(item) for item in self.evidence],
            "causal_chain": list(self.causal_chain),
            "impact_score": self.impact_score,
            "impact": self.impact_score,
            "description": self.description,
        }


@dataclass(frozen=True)
class OpenClawDiagnosis:
    """Structured diagnostic truth produced from runtime events."""

    trust_score: int
    readiness_level: str
    scores: dict[str, int]
    failure_causes: list[OpenClawFailureCause]
    causal_graph: dict[str, Any]
    cost_analysis: dict[str, Any]
    primary_diagnosis: dict[str, Any]
    evidence_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "trust_score": self.trust_score,
            "readiness_level": self.readiness_level,
            "scores": dict(self.scores),
            "failure_causes": [cause.to_dict() for cause in self.failure_causes],
            "causal_graph": {
                "nodes": [dict(node) for node in self.causal_graph.get("nodes", [])],
                "edges": [dict(edge) for edge in self.causal_graph.get("edges", [])],
            },
            "cost_analysis": dict(self.cost_analysis),
            "primary_diagnosis": dict(self.primary_diagnosis),
            "evidence_summary": dict(self.evidence_summary),
        }


@dataclass
class OpenClawRuntimeObserver:
    """Non-invasive recorder for local OpenClaw agent execution."""

    agent_id: str = "openclaw_agent"
    tenant_id: str = "default"
    benchmark_id: str = "openclaw_runtime_v1"
    difficulty_tier: str = "standard"
    events: list[dict[str, Any]] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    def record(self, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if event_type not in OPENCLAW_EVENT_TYPES:
            event_type = "process_output"
        event = {
            "event": event_type,
            "timestamp": _now(),
            **dict(payload or {}),
        }
        self.events.append(event)
        return event

    def payload(self, visibility: str = "private") -> dict[str, Any]:
        diagnosis = diagnose_openclaw_events(self.events)
        return build_openclaw_run_payload(
            agent_id=self.agent_id,
            tenant_id=self.tenant_id,
            events=self.events,
            diagnosis=diagnosis,
            benchmark_id=self.benchmark_id,
            difficulty_tier=self.difficulty_tier,
            visibility=visibility,
            latency=round(time.time() - self.started_at, 4),
        )


def monitor_openclaw_process(
    command: Sequence[str],
    agent_id: str = "openclaw_agent",
    tenant_id: str = "default",
    visibility: str = "private",
    benchmark_id: str = "openclaw_runtime_v1",
    difficulty_tier: str = "standard",
    cwd: str | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    """Run an agent process and convert observed output into OpenClaw evidence."""

    observer = OpenClawRuntimeObserver(
        agent_id=agent_id,
        tenant_id=tenant_id,
        benchmark_id=benchmark_id,
        difficulty_tier=difficulty_tier,
    )
    observer.record("process_start", {"command": list(command)})
    started = time.time()
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            timeout=timeout,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        observer.record("error_event", {"error": "timeout", "timeout": timeout})
        observer.record("process_end", {"exit_code": None, "latency": round(time.time() - started, 4)})
        diagnosis = diagnose_openclaw_events(observer.events)
        return build_openclaw_run_payload(agent_id, tenant_id, observer.events, diagnosis, benchmark_id, difficulty_tier, visibility)

    _capture_process_stream(observer, completed.stdout, "stdout")
    _capture_process_stream(observer, completed.stderr, "stderr")
    if completed.returncode != 0:
        observer.record("error_event", {"error": "process_exit", "exit_code": completed.returncode})
    observer.record(
        "process_end",
        {"exit_code": completed.returncode, "latency": round(time.time() - started, 4)},
    )
    diagnosis = diagnose_openclaw_events(observer.events)
    return build_openclaw_run_payload(agent_id, tenant_id, observer.events, diagnosis, benchmark_id, difficulty_tier, visibility)


def default_openclaw_benchmark_spec(
    benchmark_id: str = "openclaw_runtime_v1",
    difficulty_tier: str = "standard",
) -> dict[str, Any]:
    difficulty_scores = {"easy": 45, "standard": 70, "hard": 85, "stress": 95}
    difficulty = difficulty_scores.get(difficulty_tier, 70)
    return {
        "benchmark_id": benchmark_id,
        "category": "openclaw_agents",
        "version": "vNext.1",
        "weights": dict(OPENCLAW_BENCHMARK_WEIGHTS),
        "difficulty_tier": difficulty_tier,
        "difficulty_factors": {
            "task_complexity": difficulty,
            "tool_usage_requirements": difficulty,
            "multi_step_reasoning": difficulty,
            "retrieval_dependency": max(40, difficulty - 10),
        },
        "failure_penalties": {
            "infinite_tool_loop": 0.35,
            "memory_degradation": 0.25,
            "ignoring_tool_outputs": 0.30,
            "context_pollution": 0.20,
            "cost_explosion": 0.25,
            "skill_failure": 0.25,
        },
    }


def build_openclaw_run_payload(
    agent_id: str,
    tenant_id: str,
    events: Sequence[dict[str, Any]],
    diagnosis: OpenClawDiagnosis | None = None,
    benchmark_id: str = "openclaw_runtime_v1",
    difficulty_tier: str = "standard",
    visibility: str = "private",
    latency: float | None = None,
) -> dict[str, Any]:
    diagnosis = diagnosis or diagnose_openclaw_events(events)
    payload = diagnosis.to_dict()
    return {
        "tenant_id": tenant_id,
        "agent_id": agent_id,
        "agent_name": agent_id,
        "framework": "openclaw",
        "category": "openclaw_agents",
        "benchmark_id": benchmark_id,
        "benchmark_spec": default_openclaw_benchmark_spec(benchmark_id, difficulty_tier),
        "difficulty_tier": difficulty_tier,
        "visibility": visibility,
        "public_benchmark": visibility == "public",
        "anonymous_benchmark": visibility == "anonymous",
        "trace": [dict(event) for event in events],
        "runtime_metrics": {"latency": latency} if latency is not None else {},
        "evidence_level": "fully_instrumented" if events else "response_only",
        "evaluation_confidence": 95 if events else 0,
        **payload,
    }


def diagnose_openclaw_events(events: Sequence[dict[str, Any]]) -> OpenClawDiagnosis:
    normalized = [_normalize_event(event, index) for index, event in enumerate(events)]
    causes: list[OpenClawFailureCause] = []
    causes.extend(_detect_infinite_tool_loop(normalized))
    causes.extend(_detect_memory_degradation(normalized))
    causes.extend(_detect_ignored_tool_outputs(normalized))
    causes.extend(_detect_context_pollution(normalized))
    causes.extend(_detect_cost_explosion(normalized))
    causes.extend(_detect_skill_failure(normalized))

    scores = _openclaw_scores(normalized, causes)
    trust_score = _weighted_score(scores)
    causal_graph = build_openclaw_causal_graph(normalized, causes)
    cost_analysis = _cost_analysis(normalized, causes)
    primary = _primary_diagnosis(causes)
    evidence_summary = _evidence_summary(normalized)
    return OpenClawDiagnosis(
        trust_score=trust_score,
        readiness_level=_readiness_level(trust_score, causes),
        scores=scores,
        failure_causes=causes,
        causal_graph=causal_graph,
        cost_analysis=cost_analysis,
        primary_diagnosis=primary,
        evidence_summary=evidence_summary,
    )


def build_openclaw_causal_graph(
    events: Sequence[dict[str, Any]],
    causes: Sequence[OpenClawFailureCause],
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    previous_id: str | None = None
    for event in events:
        event_id = str(event.get("event_id", f"event_{len(nodes)}"))
        label = str(event.get("event", "event"))
        nodes.append({"id": event_id, "type": label, "label": _event_label(event)})
        if previous_id:
            edges.append({"from": previous_id, "to": event_id, "relation": "precedes"})
        previous_id = event_id

    for cause in causes:
        failure_id = f"failure_{cause.type}"
        nodes.append({"id": failure_id, "type": "failure", "label": cause.type})
        for evidence in cause.evidence:
            source = str(evidence.get("event_id", ""))
            if source:
                edges.append({"from": source, "to": failure_id, "relation": "causes"})
        chain_ids = [str(item.get("event_id", "")) for item in cause.evidence if item.get("event_id")]
        for left, right in zip(chain_ids, chain_ids[1:]):
            edges.append({"from": left, "to": right, "relation": "reinforces"})
    return {"nodes": nodes, "edges": edges}


def _capture_process_stream(observer: OpenClawRuntimeObserver, text: str, stream: str) -> None:
    for line in text.splitlines():
        parsed = _parse_event_line(line)
        if parsed is not None:
            observer.record(str(parsed.get("event", parsed.get("type", "process_output"))), parsed)
        else:
            observer.record("process_output", {"stream": stream, "text": line})


def _parse_event_line(line: str) -> dict[str, Any] | None:
    stripped = line.strip()
    if not stripped:
        return None
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return None


def _normalize_event(event: dict[str, Any], index: int) -> dict[str, Any]:
    normalized = dict(event)
    normalized.setdefault("event", normalized.get("type", "process_output"))
    normalized.setdefault("timestamp", _now())
    normalized.setdefault("event_id", f"event_{index}")
    return normalized


def _detect_infinite_tool_loop(events: Sequence[dict[str, Any]]) -> list[OpenClawFailureCause]:
    calls = [event for event in events if event.get("event") == "tool_call"]
    retries = [event for event in events if event.get("event") == "retry_event"]
    counts: dict[str, list[dict[str, Any]]] = {}
    for call in calls:
        key = json.dumps({"tool": call.get("tool"), "args": call.get("args", call.get("arguments", {}))}, sort_keys=True, default=str)
        counts.setdefault(key, []).append(call)
    failures = []
    for repeated in counts.values():
        if len(repeated) >= 3:
            severity = "critical" if len(repeated) >= 5 or len(retries) >= 3 else "high"
            failures.append(OpenClawFailureCause(
                type="infinite_tool_loop",
                severity=severity,
                evidence=repeated + retries[:3],
                causal_chain=["tool_call", "tool_failure_or_no_progress", "retry_same_action", "loop_flagged"],
                impact_score=-min(30, 8 + len(repeated) * 4 + len(retries) * 3),
                description=f"Tool call repeated {len(repeated)} times with matching arguments.",
            ))
    return failures


def _detect_memory_degradation(events: Sequence[dict[str, Any]]) -> list[OpenClawFailureCause]:
    bad_memory = [
        event for event in events
        if event.get("event") == "memory_event"
        and str(event.get("action", event.get("status", ""))).lower() in {"recall_failed", "ignored", "lost", "miss"}
    ]
    if not bad_memory:
        return []
    return [OpenClawFailureCause(
        type="memory_degradation",
        severity="high" if len(bad_memory) >= 3 else "medium",
        evidence=bad_memory,
        causal_chain=["memory_stored", "recall_failed_or_ignored", "state_reconstruction_failed"],
        impact_score=-min(25, 8 + len(bad_memory) * 5),
        description="Memory events show failed recall, ignored memory, or lost context.",
    )]


def _detect_ignored_tool_outputs(events: Sequence[dict[str, Any]]) -> list[OpenClawFailureCause]:
    ignored = [
        event for event in events
        if event.get("event") == "tool_output"
        and (event.get("used") is False or event.get("referenced") is False or str(event.get("status", "")).lower() == "ignored")
    ]
    if not ignored:
        return []
    return [OpenClawFailureCause(
        type="ignoring_tool_outputs",
        severity="high" if len(ignored) >= 2 else "medium",
        evidence=ignored,
        causal_chain=["tool_call", "tool_output", "decision_skipped_output", "unsupported_agent_step"],
        impact_score=-min(30, 10 + len(ignored) * 7),
        description="Tool outputs were observed but marked unused, unreferenced, or ignored.",
    )]


def _detect_context_pollution(events: Sequence[dict[str, Any]]) -> list[OpenClawFailureCause]:
    polluted = [
        event for event in events
        if event.get("event") == "context_event"
        and (int(event.get("saturation", event.get("saturation_score", 0)) or 0) >= 85 or str(event.get("action", "")).lower() == "compaction")
    ]
    if not polluted:
        return []
    return [OpenClawFailureCause(
        type="context_pollution",
        severity="high" if any(int(event.get("saturation", event.get("saturation_score", 0)) or 0) >= 95 for event in polluted) else "medium",
        evidence=polluted,
        causal_chain=["context_growth", "saturation_or_compaction", "key_state_risk"],
        impact_score=-min(22, 7 + len(polluted) * 5),
        description="Context events show saturation or compaction that can hide important state.",
    )]


def _detect_cost_explosion(events: Sequence[dict[str, Any]]) -> list[OpenClawFailureCause]:
    token_total = _token_total(events)
    calls = [event for event in events if event.get("event") == "tool_call"]
    duplicate_actions = max(0, len(calls) - len({_event_label(call) for call in calls}))
    if token_total < 12000 and duplicate_actions < 3:
        return []
    evidence = [event for event in events if event.get("event") in {"token_usage", "tool_call"}]
    return [OpenClawFailureCause(
        type="cost_explosion",
        severity="critical" if token_total >= 30000 else "high",
        evidence=evidence[:12],
        causal_chain=["repeated_reasoning_or_calls", "token_waste", "cost_spike"],
        impact_score=-min(30, 10 + duplicate_actions * 4 + token_total // 6000),
        description="Runtime evidence shows high token usage or redundant tool execution.",
    )]


def _detect_skill_failure(events: Sequence[dict[str, Any]]) -> list[OpenClawFailureCause]:
    failed = [
        event for event in events
        if event.get("event") == "skill_event"
        and (event.get("invoked") is False or str(event.get("status", "")).lower() in {"ignored", "mismatch", "failed"})
    ]
    if not failed:
        return []
    return [OpenClawFailureCause(
        type="skill_failure",
        severity="high" if len(failed) >= 2 else "medium",
        evidence=failed,
        causal_chain=["skill_available", "skill_not_selected_or_failed", "generic_execution"],
        impact_score=-min(24, 8 + len(failed) * 6),
        description="A relevant OpenClaw skill was ignored, mismatched, or failed invocation.",
    )]


def _openclaw_scores(events: Sequence[dict[str, Any]], causes: Sequence[OpenClawFailureCause]) -> dict[str, int]:
    penalties = {cause.type: abs(cause.impact_score) for cause in causes}
    return {
        "loop_control": max(0, 100 - penalties.get("infinite_tool_loop", 0)),
        "memory_integrity": max(0, 100 - penalties.get("memory_degradation", 0)),
        "tool_output_utilization": max(0, 100 - penalties.get("ignoring_tool_outputs", 0)),
        "context_health": max(0, 100 - penalties.get("context_pollution", 0)),
        "cost_efficiency": max(0, 100 - penalties.get("cost_explosion", 0)),
        "skill_adherence": max(0, 100 - penalties.get("skill_failure", 0)),
    }


def _weighted_score(scores: dict[str, int]) -> int:
    total = 0.0
    for key, weight in OPENCLAW_BENCHMARK_WEIGHTS.items():
        total += scores.get(key, 0) * weight
    return max(0, min(100, round(total)))


def _cost_analysis(events: Sequence[dict[str, Any]], causes: Sequence[OpenClawFailureCause]) -> dict[str, Any]:
    token_total = _token_total(events)
    calls = [event for event in events if event.get("event") == "tool_call"]
    duplicate_actions = max(0, len(calls) - len({_event_label(call) for call in calls}))
    redundancy_score = max(0, min(100, round((duplicate_actions / max(1, len(calls))) * 100)))
    token_waste = min(token_total, duplicate_actions * 1000 + sum(abs(cause.impact_score) for cause in causes if cause.type == "cost_explosion") * 120)
    return {
        "total_tokens": token_total,
        "token_waste": token_waste,
        "duplicate_calls": duplicate_actions,
        "redundancy_score": redundancy_score,
        "cost_efficiency": max(0, 100 - redundancy_score),
    }


def _primary_diagnosis(causes: Sequence[OpenClawFailureCause]) -> dict[str, Any]:
    if not causes:
        return {
            "root_cause_failure_type": None,
            "causal_chain_explanation": "No OpenClaw failure mode was detected from runtime evidence.",
        }
    primary = sorted(causes, key=lambda cause: abs(cause.impact_score), reverse=True)[0]
    return {
        "root_cause_failure_type": primary.type,
        "causal_chain_explanation": " -> ".join(primary.causal_chain),
        "severity": primary.severity,
        "description": primary.description,
    }


def _evidence_summary(events: Sequence[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for event in events:
        key = str(event.get("event", "unknown"))
        counts[key] = counts.get(key, 0) + 1
    return {
        "event_count": len(events),
        "event_counts": counts,
        "tool_calls": counts.get("tool_call", 0),
        "tool_outputs": counts.get("tool_output", 0),
        "memory_events": counts.get("memory_event", 0),
        "retries": counts.get("retry_event", 0),
        "errors": counts.get("error_event", 0),
        "state_transitions": counts.get("state_transition", 0),
    }


def _token_total(events: Sequence[dict[str, Any]]) -> int:
    total = 0
    for event in events:
        if event.get("event") != "token_usage":
            continue
        usage = event.get("usage", event)
        if isinstance(usage, dict):
            total += int(usage.get("total", usage.get("total_tokens", 0)) or 0)
        else:
            total += int(event.get("tokens", 0) or 0)
    return total


def _event_label(event: dict[str, Any]) -> str:
    tool = event.get("tool") or event.get("name") or event.get("skill") or event.get("event")
    args = event.get("args", event.get("arguments", ""))
    if args:
        return f"{tool}:{json.dumps(args, sort_keys=True, default=str)}"
    return str(tool)


def _readiness_level(trust_score: int, causes: Sequence[OpenClawFailureCause]) -> str:
    if any(cause.severity == "critical" for cause in causes) or trust_score < 60:
        return "unsafe_for_production"
    if trust_score < 80 or any(cause.severity == "high" for cause in causes):
        return "review_recommended"
    return "ready_for_runtime"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
