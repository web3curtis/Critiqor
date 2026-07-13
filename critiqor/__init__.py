"""Critiqor public client package.

Critiqor collects runtime evidence, generates local diagnoses, and launches the
dashboard without requiring an external service.
"""

from .diagnosis import generate_diagnosis
from .openclaw import (
    OpenClawRuntimeObserver,
    capture_process_stream,
    monitor_openclaw_process,
    parse_process_line,
)
from .schemas import (
    DiagnosisResult,
    EvidenceLevel,
    EvidenceSubmission,
    OPENCLAW_EVENT_TYPES,
    RuntimeEvent,
    Visibility,
)
from .session import (
    ABORTED,
    COMPLETED,
    FINALIZING,
    IDLE,
    MONITORING,
    SessionPaths,
    append_event_to_active,
    append_event_to_run,
    create_session,
    finalize_session,
    latest_completed_run,
    list_completed_runs,
    load_active_session,
    paths_for,
)

__all__ = [
    "ABORTED",
    "COMPLETED",
    "DiagnosisResult",
    "EvidenceLevel",
    "EvidenceSubmission",
    "FINALIZING",
    "IDLE",
    "MONITORING",
    "OPENCLAW_EVENT_TYPES",
    "OpenClawRuntimeObserver",
    "RuntimeEvent",
    "SessionPaths",
    "Visibility",
    "append_event_to_active",
    "append_event_to_run",
    "capture_process_stream",
    "create_session",
    "finalize_session",
    "latest_completed_run",
    "list_completed_runs",
    "load_active_session",
    "monitor_openclaw_process",
    "parse_process_line",
    "paths_for",
    "generate_diagnosis",
]
