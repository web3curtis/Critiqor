"""Public Critiqor schemas shared by the CLI, integrations, and backend API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Visibility = Literal["private", "public", "anonymous", "shared"]
EvidenceLevel = Literal["response_only", "trace_available", "fully_instrumented"]

OPENCLAW_EVENT_TYPES = {
    "agent_start",
    "agent_end",
    "turn_start",
    "turn_end",
    "session_start",
    "session_end",
    "before_provider_request",
    "after_provider_response",
    "message_received",
    "message_sent",
    "input",
    "user_bash",
    "tool_call",
    "tool_output",
    "memory_event",
    "retry_event",
    "error_event",
    "state_transition",
    "token_usage",
    "context_event",
    "process_output",
    "process_start",
    "process_end",
}


@dataclass(frozen=True)
class RuntimeEvent:
    """Normalized runtime event emitted by a Critiqor observer."""

    event_type: str
    timestamp: str
    source_layer: str = "runtime_observer"
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event": self.event_type,
            "timestamp": self.timestamp,
            "source_layer": self.source_layer,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class EvidenceSubmission:
    """Public request body sent from the client to the private diagnosis backend."""

    run_id: str
    metadata: dict[str, Any]
    session: dict[str, Any]
    events: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "critiqor.evidence_submission.v1",
            "run_id": self.run_id,
            "metadata": dict(self.metadata),
            "session": dict(self.session),
            "events": [dict(event) for event in self.events],
        }


@dataclass(frozen=True)
class DiagnosisResult:
    """Diagnosis payload returned by the private backend."""

    run_id: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        result = dict(self.payload)
        result.setdefault("run_id", self.run_id)
        return result


def validate_score(value: Any, field_name: str) -> list[str]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return [f"{field_name} must be a number"]
    if not 0 <= float(value) <= 100:
        return [f"{field_name} must be between 0 and 100"]
    return []


def validate_diagnosis_payload(payload: Any) -> list[str]:
    """Return strict structural errors for a diagnosis artifact."""

    if not isinstance(payload, dict):
        return ["diagnosis must be a JSON object"]
    errors: list[str] = []
    if not isinstance(payload.get("run_id"), str) or not payload.get("run_id"):
        errors.append("run_id must be a non-empty string")
    summary = payload.get("executive_summary")
    if not isinstance(summary, dict):
        errors.append("executive_summary must be an object")
        return errors
    errors.extend(validate_score(summary.get("trust_score"), "executive_summary.trust_score"))
    confidence = summary.get("evaluation_confidence", payload.get("evaluation_confidence"))
    if confidence is not None:
        errors.extend(validate_score(confidence, "evaluation_confidence"))
    readiness = summary.get("readiness_level")
    if readiness not in {
        "safe_to_deploy",
        "ready_for_runtime",
        "review_recommended",
        "unsafe_for_production",
        "insufficient_evidence",
    }:
        errors.append("executive_summary.readiness_level is invalid")
    return errors
