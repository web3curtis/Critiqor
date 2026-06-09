"""Persistent Critiqor observation sessions for OpenClaw runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any

from .openclaw import build_openclaw_run_payload, diagnose_openclaw_events
from .platform import AgentReliabilityIndex

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


def paths_for(runs_dir: str | Path = "runs") -> SessionPaths:
    return SessionPaths(Path(runs_dir))


def ensure_runs_dir(paths: SessionPaths) -> None:
    paths.runs_dir.mkdir(parents=True, exist_ok=True)


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
) -> dict[str, Any]:
    paths = paths_for(runs_dir)
    ensure_runs_dir(paths)
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
            "framework": "openclaw",
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
    event = {"event": event_type, "timestamp": utc_now(), **dict(payload or {})}
    session.setdefault("event_log", []).append(event)
    return event


def append_event_to_run(
    runs_dir: str | Path,
    run_id: str,
    event_type: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    paths = paths_for(runs_dir)
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
    events = [dict(event) for event in session.get("event_log", [])]
    append_event(session, "state_transition", {"state": COMPLETED, "message": "Evidence finalized"})
    events = [dict(event) for event in session.get("event_log", [])]
    diagnosis = diagnose_openclaw_events(events)
    payload = build_openclaw_run_payload(
        agent_id=str(metadata.get("agent_id", "openclaw_agent")),
        tenant_id=str(metadata.get("tenant_id", "default")),
        events=events,
        diagnosis=diagnosis,
        benchmark_id=str(metadata.get("benchmark_id", "openclaw_runtime_v1")),
        difficulty_tier=str(metadata.get("difficulty_tier", "standard")),
        visibility=str(metadata.get("visibility", "private")),
    )
    index = AgentReliabilityIndex()
    accepted = index.ingest_run(payload)
    dashboard_view = index.dashboard.run_diagnosis_view(accepted.run_id)
    dashboard_view["run_id"] = run_id
    finalized_at = utc_now()
    session.update(
        {
            "status": COMPLETED,
            "timestamps": {**dict(session.get("timestamps") or {}), "finalized_at": finalized_at},
            "lifecycle": [*list(session.get("lifecycle", [])), {"state": COMPLETED, "timestamp": finalized_at}],
            "event_log": events,
            "diagnosis": dashboard_view,
            "trust_score": dashboard_view["executive_summary"]["trust_score"],
            "confidence_score": payload.get("evaluation_confidence", 0),
            "causal_graph": dashboard_view["evidence_panel"].get("causal_graph", {"nodes": [], "edges": []}),
            "failure_analysis": dashboard_view.get("failure_analysis", {}),
            "cost_analysis": dashboard_view.get("cost_analysis", {}),
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
