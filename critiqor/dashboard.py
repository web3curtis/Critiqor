"""Local Critiqor Core Engine dashboard launcher."""

from __future__ import annotations

import json
import os
from pathlib import Path
import hashlib
import shutil
import socket
import subprocess
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlencode
import webbrowser

from .backend import BackendConfig, backend_configuration_hint
from .session import list_completed_runs, load_active_session, paths_for, read_json


def serve_dashboard(
    event_log_path: str = ".critiqor/events.jsonl",
    runs_dir: str = "runs",
    host: str = "127.0.0.1",
    port: int = 0,
    run_id: str | None = None,
    open_browser: bool = True,
) -> int:
    """Launch the Critiqor Core Engine dashboard against local diagnosis artifacts."""

    selected_run_id = run_id or latest_diagnosis_run_id(runs_dir)
    if not selected_run_id:
        explain_missing_diagnosis(runs_dir, run_id)
        return 1

    diagnosis = load_diagnosis_run(runs_dir, selected_run_id)
    if diagnosis is None:
        print(f"Run {selected_run_id} not found.")
        return 1
    if not validate_diagnosis(diagnosis):
        print("Diagnosis file invalid. Dashboard launch aborted.")
        return 1

    dashboard_dir = find_core_engine_dashboard()
    if dashboard_dir is None:
        print("Critiqor Core Engine dashboard not found.")
        print("Set CRITIQOR_DASHBOARD_DIR to the local critiqor-core-engine repo.")
        return 1

    resolved_runs = str(Path(runs_dir).resolve())
    existing = reusable_dashboard_server(resolved_runs, host, selected_run_id)
    process: subprocess.Popen[Any] | None = None
    if existing:
        actual_port = int(existing["port"])
    else:
        actual_port = port or find_available_port(host)
        try:
            process = start_core_engine_dashboard(dashboard_dir, resolved_runs, host, actual_port)
        except (OSError, RuntimeError) as exc:
            print(f"Dashboard launch aborted: {exc}")
            return 1
        write_dashboard_server_record(resolved_runs, host, actual_port, process.pid, dashboard_dir)

    url = f"http://{host}:{actual_port}/?{urlencode({'run_id': selected_run_id})}"
    try:
        wait_for_dashboard_run(host, actual_port, selected_run_id)
    except RuntimeError as exc:
        if process is not None:
            terminate_process(process)
            clear_dashboard_server_record(resolved_runs)
        print(f"Dashboard launch aborted: {exc}")
        return 1

    print(f"Dashboard run: {selected_run_id}", flush=True)
    print(f"Critiqor dashboard: {url}", flush=True)
    if open_browser:
        webbrowser.open(url)
    return 0


def diagnosis_path_for(runs_dir: str | Path, run_id: str) -> Path:
    return Path(runs_dir) / run_id / "diagnosis.json"


def explain_missing_diagnosis(runs_dir: str | Path, requested_run_id: str | None = None) -> None:
    """Explain why the dashboard cannot start without creating a finalize loop."""
    root = Path(runs_dir).resolve()
    print("No dashboard-ready diagnosis was found.")
    print(f"Searched: {root}/run_*/diagnosis.json")
    if requested_run_id:
        print(f"Requested run: {requested_run_id}")
    active = load_active_session(runs_dir)
    if active:
        run_id = str(active.get("run_id", "unknown"))
        print(f"Active evidence session: {run_id} ({active.get('status', 'unknown')})")
        run_path = paths_for(runs_dir).run_path(run_id)
        try:
            session = read_json(run_path)
        except (OSError, json.JSONDecodeError):
            session = {}
        errors = [
            event for event in session.get("event_log", [])
            if isinstance(event, dict) and event.get("event") == "error_event"
        ]
        backend_errors = [event for event in errors if event.get("source") == "critiqor_backend"]
        if backend_errors:
            print(f"Latest diagnosis error: {backend_errors[-1].get('message', 'backend unavailable')}")
            print(f"Configured backend: {BackendConfig.from_env().url}")
            print(backend_configuration_hint())
            print("Your evidence is retained. After the backend is reachable, run `critiqor finalize` once, then retry the dashboard.")
            return
        print("This run has evidence but no diagnosis yet. Run `critiqor finalize` once.")
        return
    completed = list_completed_runs(runs_dir)
    if completed:
        print("Completed session records exist, but none contain a valid diagnosis artifact.")
        print("Inspect the run directory above or select the correct directory with `critiqor dashboard --runs PATH`.")
        return
    print("No active or completed sessions exist in this directory.")
    print("If the run was created elsewhere, use `critiqor dashboard --runs PATH`.")


def load_diagnosis_run(runs_dir: str | Path, run_id: str | None) -> dict[str, Any] | None:
    if not run_id:
        return None
    path = diagnosis_path_for(runs_dir, run_id)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def validate_diagnosis(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    run_id = payload.get("run_id")
    if not run_id:
        return False
    summary = payload.get("executive_summary")
    has_summary_score = isinstance(summary, dict) and "trust_score" in summary
    return has_summary_score or "trust_score" in payload


def list_diagnosis_runs(runs_dir: str | Path = "runs") -> list[dict[str, Any]]:
    root = Path(runs_dir)
    runs: list[dict[str, Any]] = []
    if root.exists():
        for path in sorted(root.glob("run_*/diagnosis.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and validate_diagnosis(payload):
                runs.append(payload)
    if not runs:
        artifacts = list_completed_runs(runs_dir)
        runs = [dict(run.get("diagnosis") or {}) for run in artifacts if isinstance(run.get("diagnosis"), dict)]
    return sorted(runs, key=lambda item: str(item.get("run_id", "")))


def latest_diagnosis_run_id(runs_dir: str | Path = "runs") -> str | None:
    runs = list_diagnosis_runs(runs_dir)
    if not runs:
        return None
    return str(runs[-1].get("run_id"))


def find_core_engine_dashboard() -> Path | None:
    configured = [
        os.environ.get("CRITIQOR_DASHBOARD_DIR"),
        os.environ.get("CRITIQOR_CORE_ENGINE_DASHBOARD_DIR"),
    ]
    candidates = [Path(value).expanduser() for value in configured if value]
    here = Path(__file__).resolve()
    home = Path.home()
    bundled = here.parent / "core_engine_dashboard"
    candidates.extend([
        bundled,
        Path.cwd(),
        Path.cwd() / "critiqor-core-engine",
        Path.cwd().parent / "critiqor-core-engine",
        home / "Code" / "critiqor-core-engine",
        home / "Code" / "Critiqor Core Engine",
        home / ".critiqor" / "core-engine-dashboard",
        Path(os.sys.prefix) / "share" / "critiqor-core-engine",
        here.parents[2] / "critiqor-core-engine" if len(here.parents) > 2 else here.parent,
        here.parents[1] / "critiqor-core-engine" if len(here.parents) > 1 else here.parent,
    ])
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if is_core_engine_dashboard(resolved):
            return resolved
    return None


def is_core_engine_dashboard(path: Path) -> bool:
    return (
        path.exists()
        and (path / "package.json").exists()
        and (path / "src" / "routes" / "index.tsx").exists()
        and (path / "src" / "lib" / "critiqor-api-store.server.ts").exists()
    )


def start_core_engine_dashboard(dashboard_dir: Path, runs_dir: str | Path, host: str, port: int) -> subprocess.Popen[Any]:
    command = dashboard_command(dashboard_dir, host, port)
    env = os.environ.copy()
    resolved_runs = str(Path(runs_dir).resolve())
    env.update({
        "CRITIQOR_RUNS_DIR": resolved_runs,
        "CRITIQOR_DIAGNOSIS_DIR": resolved_runs,
        "VITE_CRITIQOR_RUNS_DIR": resolved_runs,
        "BROWSER": "none",
    })
    log_path = dashboard_log_path(resolved_runs)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("ab")
    return subprocess.Popen(
        command,
        cwd=str(dashboard_dir),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )


def dashboard_command(dashboard_dir: Path, host: str, port: int) -> list[str]:
    if (dashboard_dir / "bun.lock").exists() and shutil.which("bun"):
        return ["bun", "run", "dev", "--host", host, "--port", str(port)]
    if shutil.which("npm"):
        return ["npm", "run", "dev", "--", "--host", host, "--port", str(port)]
    raise RuntimeError("Neither bun nor npm is available to launch the Core Engine dashboard.")




def dashboard_state_dir(runs_dir: str | Path) -> Path:
    return Path(runs_dir) / ".critiqor_dashboard"


def dashboard_server_record_path(runs_dir: str | Path) -> Path:
    return dashboard_state_dir(runs_dir) / "server.json"


def dashboard_log_path(runs_dir: str | Path) -> Path:
    digest = hashlib.sha1(str(Path(runs_dir).resolve()).encode("utf-8")).hexdigest()[:12]
    return Path(os.environ.get("TMPDIR", "/tmp")) / f"critiqor-dashboard-{digest}.log"


def read_dashboard_server_record(runs_dir: str | Path) -> dict[str, Any] | None:
    path = dashboard_server_record_path(runs_dir)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def write_dashboard_server_record(runs_dir: str | Path, host: str, port: int, pid: int, dashboard_dir: Path) -> None:
    path = dashboard_server_record_path(runs_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "host": host,
        "port": port,
        "pid": pid,
        "runs_dir": str(Path(runs_dir).resolve()),
        "dashboard_dir": str(dashboard_dir.resolve()),
        "updated_at": time.time(),
    }, indent=2, sort_keys=True), encoding="utf-8")


def clear_dashboard_server_record(runs_dir: str | Path) -> None:
    path = dashboard_server_record_path(runs_dir)
    if path.exists():
        path.unlink()


def reusable_dashboard_server(runs_dir: str | Path, host: str, run_id: str) -> dict[str, Any] | None:
    record = read_dashboard_server_record(runs_dir)
    if not record or str(record.get("host")) != host:
        return None
    try:
        port = int(record.get("port", 0))
    except (TypeError, ValueError):
        return None
    if port <= 0:
        return None
    try:
        wait_for_dashboard_run(host, port, run_id, timeout_seconds=1.0)
    except RuntimeError:
        clear_dashboard_server_record(runs_dir)
        return None
    return record

def find_available_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def wait_for_dashboard_run(host: str, port: int, run_id: str, timeout_seconds: float = 30.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error = "dashboard did not respond"
    url = f"http://{host}:{port}/api/runs/{run_id}"
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1.5) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, dict) and str(payload.get("run_id")) == run_id:
                return
            last_error = "dashboard API returned the wrong run"
        except (OSError, URLError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(0.25)
    raise RuntimeError(f"Core Engine dashboard could not load {run_id}: {last_error}")


def terminate_process(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
