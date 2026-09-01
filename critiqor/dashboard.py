"""Local Critiqor Core Engine dashboard launcher."""

from __future__ import annotations

import json
import os
from pathlib import Path
import hashlib
import re
import shutil
import signal
import socket
import subprocess
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen
from urllib.parse import urlencode
import webbrowser
import secrets

from .session import list_completed_runs
from .schemas import validate_diagnosis_payload
from .frameworks import configured_visibility, save_launch_credential

DEFAULT_CORE_ENGINE_PORT = 51703
MINIMUM_CORE_ENGINE_VERSION = (0, 2, 16)


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

    resolved_runs = str(Path(runs_dir).resolve())
    visibility = configured_visibility()
    credential = secrets.token_urlsafe(24) if visibility == "private" else (
        f"CRQ-{secrets.token_hex(3).upper()}" if visibility == "shared" else ""
    )
    write_access_config(resolved_runs, visibility, credential)
    save_launch_credential(visibility, credential)
    configured_port = int(os.environ.get("CRITIQOR_DASHBOARD_PORT", DEFAULT_CORE_ENGINE_PORT))
    requested_port = port or configured_port
    existing = reusable_dashboard_server(resolved_runs, host, requested_port, selected_run_id, credential)
    process: subprocess.Popen[Any] | None = None
    if existing:
        actual_port = int(existing["port"])
    else:
        actual_port = requested_port
        if dashboard_server_has_run(host, actual_port, selected_run_id, credential):
            write_dashboard_server_record(resolved_runs, host, actual_port, 0, dashboard_dir)
        else:
            release_stale_dashboard_port(resolved_runs, host, actual_port, selected_run_id, credential)
            try:
                process = start_core_engine_dashboard(dashboard_dir, resolved_runs, host, actual_port)
            except (OSError, RuntimeError) as exc:
                print(f"Dashboard launch aborted: {exc}")
                return 1
            write_dashboard_server_record(resolved_runs, host, actual_port, process.pid, dashboard_dir)

    url = f"http://{host}:{actual_port}/?{urlencode({'run_id': selected_run_id})}"
    try:
        wait_for_dashboard_run(host, actual_port, selected_run_id, credential=credential)
    except RuntimeError as exc:
        if process is not None:
            terminate_process(process)
            clear_dashboard_server_record(resolved_runs)
        print(f"Dashboard launch aborted: {exc}")
        return 1

    print(f"Dashboard run: {selected_run_id}", flush=True)
    print(f"Visibility: {visibility.title()}", flush=True)
    if visibility == "private":
        print(f"Access token: {credential}", flush=True)
    elif visibility == "shared":
        print(f"Invite code: {credential}", flush=True)
    print(f"Critiqor dashboard: {url}", flush=True)
    if open_browser:
        webbrowser.open(url)
    return 0


def diagnosis_path_for(runs_dir: str | Path, run_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", run_id):
        raise ValueError("Invalid run id.")
    return Path(runs_dir) / run_id / "diagnosis.json"


def load_diagnosis_run(runs_dir: str | Path, run_id: str | None) -> dict[str, Any] | None:
    if not run_id:
        return None
    try:
        path = diagnosis_path_for(runs_dir, run_id)
    except ValueError:
        return None
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def validate_diagnosis(payload: dict[str, Any] | None) -> bool:
    return not validate_diagnosis_payload(payload)


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
    if not (
        path.exists()
        and (path / "package.json").exists()
        and (
            (
                (path / "src" / "routes" / "index.tsx").exists()
                and (path / "src" / "lib" / "critiqor-api-store.server.ts").exists()
            )
            or (path / ".output" / "server" / "index.mjs").exists()
        )
    ):
        return False
    try:
        package = json.loads((path / "package.json").read_text(encoding="utf-8"))
        version = tuple(int(part) for part in str(package.get("version", "0.0.0")).split(".")[:3])
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False
    return version >= MINIMUM_CORE_ENGINE_VERSION


def start_core_engine_dashboard(dashboard_dir: Path, runs_dir: str | Path, host: str, port: int) -> subprocess.Popen[Any]:
    command = dashboard_command(dashboard_dir, host, port)
    env = os.environ.copy()
    resolved_runs = str(Path(runs_dir).resolve())
    env.update({
        "CRITIQOR_RUNS_DIR": resolved_runs,
        "CRITIQOR_DIAGNOSIS_DIR": resolved_runs,
        "VITE_CRITIQOR_RUNS_DIR": resolved_runs,
        "CRITIQOR_ACCESS_CONFIG": str(access_config_path(resolved_runs)),
        "BROWSER": "none",
        "HOST": host,
        "PORT": str(port),
        "NITRO_HOST": host,
        "NITRO_PORT": str(port),
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
    production_server = dashboard_dir / ".output" / "server" / "index.mjs"
    if production_server.exists() and shutil.which("node"):
        return ["node", str(production_server)]
    if (dashboard_dir / "bun.lock").exists() and shutil.which("bun"):
        return ["bun", "run", "dev", "--host", host, "--port", str(port), "--strictPort"]
    if shutil.which("npm"):
        return ["npm", "run", "dev", "--", "--host", host, "--port", str(port), "--strictPort"]
    raise RuntimeError("Neither bun nor npm is available to launch the Core Engine dashboard.")




def dashboard_state_dir(runs_dir: str | Path) -> Path:
    return Path(runs_dir) / ".critiqor_dashboard"


def access_config_path(runs_dir: str | Path) -> Path:
    return dashboard_state_dir(runs_dir) / "access.json"


def write_access_config(runs_dir: str | Path, visibility: str, credential: str) -> None:
    path = access_config_path(runs_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"visibility": visibility, "credential": credential}, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


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


def reusable_dashboard_server(runs_dir: str | Path, host: str, requested_port: int, run_id: str, credential: str = "") -> dict[str, Any] | None:
    record = read_dashboard_server_record(runs_dir)
    if not record or str(record.get("host")) != host:
        return None
    try:
        port = int(record.get("port", 0))
    except (TypeError, ValueError):
        return None
    if port <= 0 or port != requested_port:
        clear_dashboard_server_record(runs_dir)
        return None
    try:
        wait_for_dashboard_run(host, port, run_id, timeout_seconds=1.0, credential=credential)
    except RuntimeError:
        clear_dashboard_server_record(runs_dir)
        return None
    return record

def find_available_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def port_is_listening(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        try:
            sock.connect((host, port))
        except OSError:
            return False
    return True


def listener_pids(port: int) -> list[int]:
    try:
        output = subprocess.check_output(
            ["lsof", f"-iTCP:{port}", "-sTCP:LISTEN", "-n", "-P", "-t"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    pids: list[int] = []
    for line in output.split():
        try:
            pids.append(int(line))
        except ValueError:
            continue
    return pids


def process_command(pid: int) -> str:
    try:
        return subprocess.check_output(["ps", "-p", str(pid), "-o", "command="], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def terminate_pid(pid: int) -> None:
    if pid <= 0:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        return
    deadline = time.time() + 3
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except OSError:
            return
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        return


def release_stale_dashboard_port(
    runs_dir: str | Path,
    host: str,
    port: int,
    run_id: str,
    credential: str = "",
) -> None:
    """Stop a leftover dashboard that occupies the CLI port but cannot serve this run."""
    if dashboard_server_has_run(host, port, run_id, credential) or not port_is_listening(host, port):
        return
    pids = set(listener_pids(port))
    record = read_dashboard_server_record(runs_dir)
    recorded = 0
    if record:
        try:
            recorded = int(record.get("pid") or 0)
        except (TypeError, ValueError):
            recorded = 0
        if recorded:
            pids.add(recorded)
    for pid in pids:
        command = process_command(pid)
        if recorded == pid or "core_engine_dashboard" in command or ".output/server/index.mjs" in command:
            terminate_pid(pid)
    clear_dashboard_server_record(runs_dir)
    time.sleep(0.4)


def dashboard_server_has_run(host: str, port: int, run_id: str, credential: str = "") -> bool:
    try:
        wait_for_dashboard_run(host, port, run_id, timeout_seconds=1.0, credential=credential)
    except RuntimeError:
        return False
    return True


def wait_for_dashboard_run(host: str, port: int, run_id: str, timeout_seconds: float = 30.0, credential: str = "") -> None:
    deadline = time.time() + timeout_seconds
    last_error = "dashboard did not respond"
    url = f"http://{host}:{port}/api/runs/{run_id}"
    while time.time() < deadline:
        try:
            from urllib.request import Request
            request = Request(url, headers={"Authorization": f"Bearer {credential}"} if credential else {})
            with urlopen(request, timeout=1.5) as response:
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
