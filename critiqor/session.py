"""Persistent Critiqor observation sessions for OpenClaw runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

from .backend import BackendConfigurationError, BackendResponseError, backend_configuration_hint, submit_evidence
from .integrity import (
    DIAGNOSIS_SCHEMA_VERSION,
    EVIDENCE_SCHEMA_VERSION,
    evidence_digest,
    object_digest,
    seal_event,
    seal_events,
    sign_manifest,
    verify_events,
)
from .schemas import EvidenceSubmission
from .local_diagnosis import build_local_diagnosis

IDLE = "IDLE"
MONITORING = "MONITORING"
FINALIZING = "FINALIZING"
COMPLETED = "COMPLETED"
ABORTED = "ABORTED"

ACTIVE_STATUSES = {MONITORING, FINALIZING}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class SessionPaths:
    runs_dir: Path

    @property
    def active_path(self) -> Path:
        return self.runs_dir / "active_session.json"

    def run_path(self, run_id: str) -> Path:
        return self.runs_dir / f"{run_id}.json"

    def evidence_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def evidence_summary_path(self, run_id: str) -> Path:
        return self.evidence_dir(run_id) / "session.json"

    def diagnosis_path(self, run_id: str) -> Path:
        return self.evidence_dir(run_id) / "diagnosis.json"

    def playbook_path(self, run_id: str) -> Path:
        return self.evidence_dir(run_id) / "improvement_playbook.md"


def paths_for(runs_dir: str | Path = "runs") -> SessionPaths:
    return SessionPaths(Path(runs_dir))


def ensure_runs_dir(paths: SessionPaths) -> None:
    paths.runs_dir.mkdir(parents=True, exist_ok=True)


@contextmanager
def session_lock(paths: SessionPaths):
    """Cross-process advisory lock for session allocation and event updates."""

    ensure_runs_dir(paths)
    lock_path = paths.runs_dir / ".critiqor-session.lock"
    with lock_path.open("a+b") as lock_file:
        lock_file.seek(0, 2)
        if lock_file.tell() == 0:
            lock_file.write(b"0")
            lock_file.flush()
        lock_file.seek(0)
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def next_run_id(runs_dir: str | Path = "runs") -> str:
    paths = paths_for(runs_dir)
    ensure_runs_dir(paths)
    highest = 0
    for file in paths.runs_dir.glob("run_*.json"):
        stem = file.stem
        try:
            highest = max(highest, int(stem.split("_", 1)[1]))
        except (IndexError, ValueError):
            continue
    return f"run_{highest + 1:03d}"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def load_active_session(runs_dir: str | Path = "runs") -> dict[str, Any] | None:
    paths = paths_for(runs_dir)
    if not paths.active_path.exists():
        return None
    session = read_json(paths.active_path)
    if str(session.get("status")) not in ACTIVE_STATUSES:
        return None
    return session


def create_session(
    *,
    runs_dir: str | Path = "runs",
    agent_id: str = "openclaw_agent",
    tenant_id: str = "default",
    visibility: str = "private",
    benchmark_id: str = "openclaw_runtime_v1",
    difficulty_tier: str = "standard",
    framework: str = "openclaw",
) -> dict[str, Any]:
    paths = paths_for(runs_dir)
    with session_lock(paths):
        active = load_active_session(runs_dir)
        if active:
            raise RuntimeError(f"Active Critiqor monitoring session already exists: {active['run_id']}")

        run_id = next_run_id(runs_dir)
        now = utc_now()
        session = {
        "run_id": run_id,
        "status": MONITORING,
        "lifecycle": [
            {"state": IDLE, "timestamp": now},
            {"state": MONITORING, "timestamp": now},
        ],
        "timestamps": {"created_at": now, "started_at": now, "finalized_at": None},
        "metadata": {
            "agent_id": agent_id,
            "tenant_id": tenant_id,
            "framework": framework,
            "visibility": visibility,
            "benchmark_id": benchmark_id,
            "difficulty_tier": difficulty_tier,
        },
        "event_log": [],
        "diagnosis": None,
        "trust_score": None,
        "confidence_score": None,
        "causal_graph": None,
        "failure_analysis": None,
        "cost_analysis": None,
        }
        append_event(session, "state_transition", {"state": MONITORING, "message": "Runtime observer attached"})
        write_json(paths.run_path(run_id), session)
        write_json(paths.active_path, {"run_id": run_id, "status": MONITORING, "runs_dir": str(paths.runs_dir)})
        return session


def append_event(session: dict[str, Any], event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    event_log = session.setdefault("event_log", [])
    previous_hash = str(event_log[-1].get("event_hash")) if event_log else "0" * 64
    event = seal_event(
        {"event": event_type, "event_type": event_type, "timestamp": utc_now(), **dict(payload or {})},
        len(event_log) + 1,
        previous_hash,
    )
    event_log.append(event)
    return event


def normalize_plugin_event(event: dict[str, Any]) -> dict[str, Any]:
    raw_event_type = str(event.get("event_type") or event.get("event") or "runtime_event")
    payload = event.get("payload")
    event_type = {
        "tool_result": "tool_output",
        "tool_execution_end": "tool_output",
        "memory_search": "memory_event",
        "memory_get": "memory_event",
        "after_provider_response": "token_usage",
    }.get(raw_event_type, raw_event_type)
    normalized = {
        "event": event_type,
        "event_type": event_type,
        "timestamp": event.get("timestamp") or utc_now(),
        "source_layer": event.get("source_layer") or "extension_api",
        "payload": {"openclaw_event_type": raw_event_type, **payload} if isinstance(payload, dict) else {"openclaw_event_type": raw_event_type, "value": payload},
    }
    for key in ("tool_name", "tool_call_id", "status", "duration_ms", "error"):
        if key in event:
            normalized[key] = event[key]
    return normalized


def load_session_evidence_events(runs_dir: str | Path, run_id: str) -> list[dict[str, Any]]:
    paths = paths_for(runs_dir)
    session_path = paths.evidence_summary_path(run_id)
    jsonl_path = paths.evidence_dir(run_id) / "events.jsonl"
    events: list[dict[str, Any]] = []
    if jsonl_path.exists():
        with jsonl_path.open("r", encoding="utf-8") as source:
            for line_number, line in enumerate(source, start=1):
                if not line.strip():
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    events.append(
                        {
                            "event": "evidence_parse_error",
                            "event_type": "evidence_parse_error",
                            "timestamp": utc_now(),
                            "source_layer": "critiqor_finalize",
                            "payload": {"file": "events.jsonl", "line": line_number},
                        }
                    )
                    continue
                if isinstance(event, dict):
                    events.append(normalize_plugin_event(event))
        return events
    if session_path.exists():
        try:
            session_payload = read_json(session_path)
        except json.JSONDecodeError:
            events.append({
                "event": "evidence_parse_error",
                "event_type": "evidence_parse_error",
                "timestamp": utc_now(),
                "source_layer": "critiqor_finalize",
                "payload": {"file": "session.json"},
            })
        else:
            raw_events = session_payload.get("events")
            if isinstance(raw_events, list):
                return [normalize_plugin_event(event) for event in raw_events if isinstance(event, dict)]

    return events


def write_session_evidence_summary(runs_dir: str | Path, run_id: str, events: list[dict[str, Any]]) -> None:
    paths = paths_for(runs_dir)
    by_event_type: dict[str, int] = {}
    by_source_layer: dict[str, int] = {}
    for event in events:
        event_type = str(event.get("event_type") or event.get("event") or "runtime_event")
        source_layer = str(event.get("source_layer") or "unknown")
        by_event_type[event_type] = by_event_type.get(event_type, 0) + 1
        by_source_layer[source_layer] = by_source_layer.get(source_layer, 0) + 1
    integrity = verify_events(events)
    summary = {
        "session_id": run_id,
        "run_id": run_id,
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "events_file": "session.json",
        "events": events,
        "integrity": integrity,
        "evidence_digest": evidence_digest(events),
        "evidence_scope": "events",
        "metrics": {
            "total_events": len(events),
            "by_event_type": by_event_type,
            "by_source_layer": by_source_layer,
        },
    }
    write_json(paths.evidence_summary_path(run_id), summary)


def write_diagnosis_artifact(runs_dir: str | Path, run_id: str, diagnosis: dict[str, Any]) -> None:
    write_json(paths_for(runs_dir).diagnosis_path(run_id), diagnosis)


def _has_webmcp_events(events: list[dict[str, Any]]) -> bool:
    return any(str(event.get("event_type") or event.get("event") or "").startswith("webmcp.") for event in events)


def _generic_playbook(diagnosis: dict[str, Any], session_path: str, diagnosis_path: str) -> str:
    run_id = str(diagnosis.get("run_id") or "unknown_run")
    findings = list(diagnosis.get("findings") or [])
    if not findings:
        causes = diagnosis.get("failure_analysis")
        if isinstance(causes, dict):
            findings = list(causes.get("failure_causes") or [])
    primary = diagnosis.get("primary_diagnosis") if isinstance(diagnosis.get("primary_diagnosis"), dict) else {}
    recs = [str(item) for item in diagnosis.get("recommendations") or [] if item]
    lines = [
        "# Critiqor improvement playbook",
        "",
        f"- Run ID: `{run_id}`",
        f"- Framework: {diagnosis.get('framework') or 'agent'}",
        f"- Generated: {utc_now()}",
        f"- Runtime session: `{session_path}`",
        f"- Diagnosis: `{diagnosis_path}`",
        "",
        "Read the session and diagnosis artifacts before changing code.",
        "",
        "## Observed result",
        "",
        str(primary.get("causal_chain_explanation") or primary.get("description") or "Runtime evidence was finalized."),
        "",
        "## Required improvements",
        "",
    ]
    if recs:
        lines.extend(f"- {item}" for item in recs)
    elif findings:
        lines.append("- Address the recorded finding using the linked runtime evidence.")
    else:
        lines.append("- Preserve current behavior and re-validate representative scenarios.")
    lines.extend([
        "",
        "## Verification",
        "",
        "- Rerun the same task with Critiqor and compare findings against this run.",
        "",
    ])
    return "\n".join(lines)


def complete_run_artifacts(
    runs_dir: str | Path,
    run_id: str,
    events: list[dict[str, Any]],
    diagnosis: dict[str, Any],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    paths = paths_for(runs_dir)
    run_dir = paths.evidence_dir(run_id)
    session_path = str(paths.evidence_summary_path(run_id).resolve())
    diagnosis_path = str(paths.diagnosis_path(run_id).resolve())
    playbook_path = paths.playbook_path(run_id)
    if _has_webmcp_events(events):
        try:
            from private_backend.webmcp import apply_webmcp_finalization

            diagnosis = apply_webmcp_finalization(
                run_dir=run_dir,
                run_id=run_id,
                events=events,
                diagnosis=diagnosis,
                metadata=metadata,
                experiment=diagnosis.get("experiment") if isinstance(diagnosis.get("experiment"), dict) else None,
            )
        except ImportError:
            pass
    artifacts = diagnosis.get("artifacts") if isinstance(diagnosis.get("artifacts"), dict) else {}
    artifacts.update({
        "session": {"path": session_path, "relative_path": "session.json"},
        "diagnosis": {"path": diagnosis_path, "relative_path": "diagnosis.json"},
        "improvement_playbook": {"path": str(playbook_path.resolve()), "relative_path": "improvement_playbook.md"},
    })
    diagnosis["artifacts"] = artifacts
    diagnosis.setdefault("raw_evidence", {})
    diagnosis["raw_evidence"]["session_json"] = session_path
    diagnosis["raw_evidence"]["diagnosis_json"] = diagnosis_path
    diagnosis["raw_evidence"]["improvement_playbook"] = str(playbook_path.resolve())
    if not playbook_path.exists() or not diagnosis.get("improvement_playbook"):
        playbook = diagnosis.get("improvement_playbook") or _generic_playbook(diagnosis, session_path, diagnosis_path)
        playbook_path.parent.mkdir(parents=True, exist_ok=True)
        playbook_path.write_text(str(playbook), encoding="utf-8")
        diagnosis["improvement_playbook"] = str(playbook)
    return diagnosis


def enrich_session_from_diagnosis(runs_dir: str | Path, run_id: str, diagnosis: dict[str, Any]) -> None:
    paths = paths_for(runs_dir)
    session_path = paths.evidence_summary_path(run_id)
    payload = read_json(session_path) if session_path.exists() else {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "run_id": run_id,
        "session_id": run_id,
        "events": [],
    }
    if diagnosis.get("webmcp_audit"):
        try:
            from private_backend.webmcp import enrich_session_payload

            payload = enrich_session_payload(payload, diagnosis)
        except ImportError:
            payload["findings"] = diagnosis.get("findings") or []
            payload["strengths"] = diagnosis.get("strengths") or []
    else:
        payload["findings"] = diagnosis.get("findings") or []
        payload["strengths"] = diagnosis.get("strengths") or []
        payload["audit_summary"] = {
            "framework": diagnosis.get("framework") or "agent",
            "status": "FINDING" if payload["findings"] else "PASSED",
            "finding_count": len(payload["findings"]),
        }
    payload["evidence_scope"] = "events"
    payload["artifacts"] = diagnosis.get("artifacts") or {}
    write_json(session_path, payload)


def append_event_to_run(
    runs_dir: str | Path,
    run_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    paths = paths_for(runs_dir)
    with session_lock(paths):
        session = read_json(paths.run_path(run_id))
        event = append_event(session, event_type, payload)
        write_json(paths.run_path(run_id), session)
        return event


def append_event_to_active(runs_dir: str | Path, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    active = load_active_session(runs_dir)
    if not active:
        raise RuntimeError("No active Critiqor monitoring session found.")
    return append_event_to_run(runs_dir, str(active["run_id"]), event_type, payload)


def abort_session(runs_dir: str | Path, reason: str) -> dict[str, Any] | None:
    paths = paths_for(runs_dir)
    active = load_active_session(runs_dir)
    if not active:
        return None
    run_id = str(active["run_id"])
    session = read_json(paths.run_path(run_id))
    now = utc_now()
    session["status"] = ABORTED
    session["timestamps"] = {**dict(session.get("timestamps") or {}), "finalized_at": now}
    session.setdefault("lifecycle", []).append({"state": ABORTED, "timestamp": now})
    append_event(session, "error_event", {"message": reason, "source": "critiqor_monitor"})
    append_event(session, "state_transition", {"state": ABORTED, "message": reason})
    write_json(paths.run_path(run_id), session)
    if paths.active_path.exists():
        paths.active_path.unlink()
    return session


def monitor_until_finalized(session: dict[str, Any], runs_dir: str | Path = "runs", heartbeat_seconds: float = 2.0) -> None:
    paths = paths_for(runs_dir)
    run_id = str(session["run_id"])
    last_heartbeat = 0.0
    while True:
        if not paths.active_path.exists():
            return
        active = read_json(paths.active_path)
        status = str(active.get("status", ""))
        if status not in ACTIVE_STATUSES:
            return
        if status == FINALIZING:
            while paths.active_path.exists():
                active = read_json(paths.active_path)
                if str(active.get("status")) != FINALIZING:
                    return
                time.sleep(0.2)
            return
        now = time.time()
        if now - last_heartbeat >= heartbeat_seconds:
            current = read_json(paths.run_path(run_id))
            append_event(current, "state_transition", {"state": MONITORING, "message": "Event collection active"})
            write_json(paths.run_path(run_id), current)
            last_heartbeat = now
        time.sleep(0.2)


def request_finalize(runs_dir: str | Path = "runs") -> dict[str, Any] | None:
    paths = paths_for(runs_dir)
    active = load_active_session(runs_dir)
    if not active:
        return None
    run_id = str(active["run_id"])
    session = read_json(paths.run_path(run_id))
    if str(session.get("status")) == COMPLETED:
        return None
    session["status"] = FINALIZING
    session.setdefault("lifecycle", []).append({"state": FINALIZING, "timestamp": utc_now()})
    append_event(session, "state_transition", {"state": FINALIZING, "message": "Finalization requested"})
    write_json(paths.run_path(run_id), session)
    write_json(paths.active_path, {"run_id": run_id, "status": FINALIZING, "runs_dir": str(paths.runs_dir)})
    return session


def finalize_session(runs_dir: str | Path = "runs") -> dict[str, Any] | None:
    paths = paths_for(runs_dir)
    session = request_finalize(runs_dir)
    if not session:
        return None
    run_id = str(session["run_id"])
    metadata = dict(session.get("metadata") or {})
    stored_events = [dict(event) for event in session.get("event_log", [])]
    plugin_events = load_session_evidence_events(runs_dir, run_id)
    append_event(session, "state_transition", {"state": COMPLETED, "message": "Evidence finalized"})
    lifecycle_events = [dict(event) for event in session.get("event_log", [])]
    events = seal_events(
        [*stored_events, *plugin_events, *[event for event in lifecycle_events if event not in stored_events]]
    )
    write_session_evidence_summary(runs_dir, run_id, events)

    submission = EvidenceSubmission(
        run_id=run_id,
        metadata={
            **metadata,
            "framework": metadata.get("framework", "openclaw"),
            "session_json": str(paths.evidence_summary_path(run_id)),
        },
        session={key: value for key, value in session.items() if key != "diagnosis"},
        events=events,
    )
    backend_url = os.environ.get("CRITIQOR_BACKEND_URL", "").strip()
    if backend_url:
        try:
            diagnosis = submit_evidence(submission).to_dict()
        except (BackendConfigurationError, BackendResponseError) as exc:
            if os.environ.get("CRITIQOR_BACKEND_REQUIRED", "").casefold() in {"1", "true", "yes"}:
                session["status"] = FINALIZING
                append_event(session, "error_event", {"source": "critiqor_backend", "message": str(exc)})
                write_json(paths.run_path(run_id), session)
                raise RuntimeError(f"Diagnosis backend unavailable: {exc}. {backend_configuration_hint()}") from exc
            append_event(session, "error_event", {
                "source": "critiqor_backend",
                "message": f"Remote diagnosis unavailable; used local diagnosis: {exc}",
            })
            diagnosis = build_local_diagnosis(
                run_id=run_id, metadata=metadata, events=events,
                session_json=str(paths.evidence_summary_path(run_id)),
            )
            diagnosis["diagnosis_fallback_reason"] = str(exc)
    else:
        diagnosis = build_local_diagnosis(
            run_id=run_id, metadata=metadata, events=events,
            session_json=str(paths.evidence_summary_path(run_id)),
        )
    diagnosis["run_id"] = run_id
    diagnosis["schema_version"] = DIAGNOSIS_SCHEMA_VERSION
    diagnosis = complete_run_artifacts(runs_dir, run_id, events, diagnosis, metadata)
    diagnosis.setdefault("raw_evidence", {})["session_json"] = str(paths.evidence_summary_path(run_id).resolve())
    unsigned = {key: value for key, value in diagnosis.items() if key != "evaluation_manifest"}
    diagnosis["evaluation_manifest"] = sign_manifest(
        {
            "schema_version": DIAGNOSIS_SCHEMA_VERSION,
            "run_id": run_id,
            "agent_id": str(metadata.get("agent_id") or ""),
            "tenant_id": str(metadata.get("tenant_id") or ""),
            "framework": str(diagnosis.get("framework") or metadata.get("framework") or "openclaw"),
            "benchmark_id": str(metadata.get("benchmark_id") or ""),
            "evidence_digest": evidence_digest(events),
            "evidence_event_count": len(events),
            "evidence_status": verify_events(events)["status"],
            "diagnosis_digest": object_digest(unsigned),
            "diagnosis_engine_version": str(
                diagnosis.get("diagnosis_engine_version") or "unversioned"
            ),
        }
    )
    write_diagnosis_artifact(runs_dir, run_id, diagnosis)
    enrich_session_from_diagnosis(runs_dir, run_id, diagnosis)
    finalized_at = utc_now()
    summary = diagnosis.get("executive_summary") if isinstance(diagnosis.get("executive_summary"), dict) else {}
    evidence_panel = diagnosis.get("evidence_panel") if isinstance(diagnosis.get("evidence_panel"), dict) else {}
    session.update(
        {
            "status": COMPLETED,
            "timestamps": {**dict(session.get("timestamps") or {}), "finalized_at": finalized_at},
            "lifecycle": [*list(session.get("lifecycle", [])), {"state": COMPLETED, "timestamp": finalized_at}],
            "event_log": events,
            "diagnosis": diagnosis,
            "trust_score": summary.get("trust_score", diagnosis.get("trust_score")),
            "confidence_score": diagnosis.get("evaluation_confidence", diagnosis.get("confidence_score")),
            "causal_graph": evidence_panel.get("causal_graph", diagnosis.get("causal_graph", {"nodes": [], "edges": []})),
            "failure_analysis": diagnosis.get("failure_analysis", {}),
            "cost_analysis": diagnosis.get("cost_analysis", {}),
        }
    )
    write_json(paths.run_path(run_id), session)
    if paths.active_path.exists():
        paths.active_path.unlink()
    return session


def list_completed_runs(runs_dir: str | Path = "runs") -> list[dict[str, Any]]:
    paths = paths_for(runs_dir)
    if not paths.runs_dir.exists():
        return []
    runs = []
    for file in sorted(paths.runs_dir.glob("run_*.json")):
        try:
            run = read_json(file)
        except json.JSONDecodeError:
            continue
        if str(run.get("status")) == COMPLETED:
            runs.append(run)
    return runs


def latest_completed_run(runs_dir: str | Path = "runs") -> dict[str, Any] | None:
    runs = list_completed_runs(runs_dir)
    if not runs:
        return None
    return runs[-1]
