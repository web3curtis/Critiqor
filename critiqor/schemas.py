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
