"""Local Critiqor Core Engine dashboard launcher."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlencode
import webbrowser

from .session import list_completed_runs


@dataclass(frozen=True)
class DashboardProcess:
    process: subprocess.Popen[Any]
    url: str
    run_id: str


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
        print("Diagnosis file not found.")
        print()
        print("Run:")
        print("critiqor finalize")
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

    actual_port = port or find_available_port(host)
    try:
        process = start_core_engine_dashboard(dashboard_dir, runs_dir, host, actual_port)
    except (OSError, RuntimeError) as exc:
        print(f"Dashboard launch aborted: {exc}")
        return 1
    url = f"http://{host}:{actual_port}/?{urlencode({'run_id': selected_run_id})}"
    try:
        wait_for_dashboard_run(host, actual_port, selected_run_id)
    except RuntimeError as exc:
        terminate_process(process)
        print(f"Dashboard launch aborted: {exc}")
        return 1

    print(f"Dashboard run: {selected_run_id}", flush=True)
    print(f"Critiqor dashboard: {url}", flush=True)
    if open_browser:
        webbrowser.open(url)

    try:
        return int(process.wait() or 0)
    except KeyboardInterrupt:
        terminate_process(process)
        return 130


def diagnosis_path_for(runs_dir: str | Path, run_id: str) -> Path:
    return Path(runs_dir) / run_id / "diagnosis.json"


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
    candidates.extend([
        Path.cwd(),
        Path.cwd() / "critiqor-core-engine",
        Path.cwd().parent / "critiqor-core-engine",
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
    return subprocess.Popen(
        command,
        cwd=str(dashboard_dir),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def dashboard_command(dashboard_dir: Path, host: str, port: int) -> list[str]:
    if (dashboard_dir / "bun.lock").exists() and shutil.which("bun"):
        return ["bun", "run", "dev", "--host", host, "--port", str(port)]
    if shutil.which("npm"):
        return ["npm", "run", "dev", "--", "--host", host, "--port", str(port)]
    raise RuntimeError("Neither bun nor npm is available to launch the Core Engine dashboard.")


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
