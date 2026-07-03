"""Critiqor public client package.

The public package collects OpenClaw runtime evidence, manages sessions, submits
evidence to a private Critiqor backend, and launches the dashboard. Proprietary
diagnosis, scoring, reliability, benchmark, and leaderboard engines are not
included in this distribution.
"""

from .backend import (
    BackendConfig,
    BackendConfigurationError,
    BackendResponseError,
    DEFAULT_BACKEND_URL,
    backend_configuration_hint,
    submit_evidence,
)
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
    "BackendConfig",
    "BackendConfigurationError",
    "BackendResponseError",
    "COMPLETED",
    "DEFAULT_BACKEND_URL",
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
    "backend_configuration_hint",
    "capture_process_stream",
    "create_session",
    "finalize_session",
    "latest_completed_run",
    "list_completed_runs",
    "load_active_session",
    "monitor_openclaw_process",
    "parse_process_line",
    "paths_for",
    "submit_evidence",
]
