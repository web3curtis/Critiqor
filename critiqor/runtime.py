"""Supervised runtime operations for Critiqor OpenClaw sessions."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from typing import Any
from .core import check_policy, load_evaluations
from .openclaw import monitor_openclaw_process
from .platform import AgentReliabilityIndex
from .session import (
    abort_session,
    append_event_to_run,
    create_session,
    finalize_session,
    load_active_session,
    paths_for,
    read_json,
)


@dataclass(frozen=True)
class MonitorOpenClawOptions:
    agent_id: str = "openclaw_agent"
    tenant_id: str = "default"
    visibility: str = "private"
    events: str = ".critiqor/events.jsonl"
    evaluation: str = ".critiqor/latest_run.json"
    benchmark_id: str = "openclaw_runtime_v1"
    difficulty_tier: str = "standard"
    cwd: str | None = None
    timeout: float | None = None
    runs_dir: str = "runs"
    openclaw_command: str = "openclaw chat"
    agent_command: tuple[str, ...] = ()


@dataclass(frozen=True)
class FinalizeOptions:
    runs_dir: str = "runs"
    no_dashboard: bool = False
    host: str = "127.0.0.1"
    port: int = 0


@dataclass(frozen=True)
class DashboardOptions:
    events: str = ".critiqor/events.jsonl"
    runs: str = "runs"
    host: str = "127.0.0.1"
    port: int = 0
    run_id: str | None = None
    open_browser: bool = True


@dataclass(frozen=True)
class RunsOptions:
    runs_dir: str = "runs"


@dataclass(frozen=True)
class PolicyCheckOptions:
    evaluations: str = "critiqor_evaluations.jsonl"
    agent_id: str | None = None
    policy: str | None = None
    minimum_trust_score: int | None = None
    maximum_hallucination_risk: int | None = None


class SupervisedOpenClawRuntime:
    """Operations center for launching and observing OpenClaw."""

    def __init__(self, options: MonitorOpenClawOptions) -> None:
        self.options = options

    def run(self) -> int:
        if self.options.agent_command:
            return run_legacy_openclaw_command(self.options)

        active = load_active_session(self.options.runs_dir)
        if active:
            print(f"Critiqor monitoring is already active for {active['run_id']}.")
            print("Finalize it with:")
            print("critiqor finalize")
            return 1

        launch_command = parse_openclaw_command(self.options.openclaw_command)
        if not launch_command:
            print("OpenClaw launch command is empty.")
            return 2
        if shutil.which(launch_command[0]) is None:
            print(f"OpenClaw command not found: {launch_command[0]}")
            print("Install OpenClaw or pass --openclaw-command with the correct executable path.")
            return 127

        try:
            session = create_session(
                runs_dir=self.options.runs_dir,
                agent_id=self.options.agent_id,
                tenant_id=self.options.tenant_id,
                visibility=self.options.visibility,
                benchmark_id=self.options.benchmark_id,
                difficulty_tier=self.options.difficulty_tier,
            )
        except RuntimeError as exc:
            print(str(exc))
            return 1

        run_id = str(session["run_id"])
        print("✓ OpenClaw detected")
        print("✓ Runtime observer attached")
        print("✓ Event collection active")
        print()
        print("Launching OpenClaw...")

        env = openclaw_environment(self.options, run_id)
        append_event_to_run(
            self.options.runs_dir,
            run_id,
            "state_transition",
            {"state": "MONITORING", "message": "Observer ready before OpenClaw launch"},
        )
        append_event_to_run(
            self.options.runs_dir,
            run_id,
            "state_transition",
            {"state": "MONITORING", "message": "Launching OpenClaw child process"},
        )

        process: subprocess.Popen[Any] | None = None
        try:
            process = subprocess.Popen(launch_command, cwd=self.options.cwd, env=env)
            append_event_to_run(
                self.options.runs_dir,
                run_id,
                "process_start",
                {"command": launch_command, "pid": process.pid, "framework": "openclaw"},
            )
            exit_code = process.wait(timeout=self.options.timeout) if self.options.timeout else process.wait()
            append_event_to_run(
                self.options.runs_dir,
                run_id,
                "process_end",
                {"command": launch_command, "pid": process.pid, "exit_code": exit_code, "framework": "openclaw"},
            )
            if exit_code != 0:
                append_event_to_run(
                    self.options.runs_dir,
                    run_id,
                    "error_event",
                    {"source": "openclaw_process", "message": f"OpenClaw exited with status {exit_code}"},
                )
            print("OpenClaw session ended.")
            print("Run `critiqor finalize` to stop monitoring and generate a diagnosis report.")
            return int(exit_code) if exit_code else 0
        except subprocess.TimeoutExpired:
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                append_event_to_run(
                    self.options.runs_dir,
                    run_id,
                    "error_event",
                    {
                        "source": "openclaw_process",
                        "message": "OpenClaw monitor timed out",
                        "timeout_seconds": self.options.timeout,
                    },
                )
                append_event_to_run(
                    self.options.runs_dir,
                    run_id,
                    "process_end",
                    {"command": launch_command, "pid": process.pid, "exit_code": -1, "framework": "openclaw"},
                )
            print("OpenClaw monitor timed out.")
            print("Run `critiqor finalize` to generate a diagnosis report from collected evidence.")
            return 124
        except KeyboardInterrupt:
            if process is not None and process.poll() is None:
                process.terminate()
                append_event_to_run(
                    self.options.runs_dir,
                    run_id,
                    "error_event",
                    {"source": "critiqor_monitor", "message": "Monitoring process terminated intentionally"},
                )
            print("Monitoring process terminated intentionally.")
            print("Run `critiqor finalize` to generate a diagnosis report from collected evidence.")
            return 130
        except OSError as exc:
            abort_session(self.options.runs_dir, f"Failed to launch OpenClaw: {exc}")
            print(f"Failed to launch OpenClaw: {exc}")
            return 1


def monitor_openclaw(options: MonitorOpenClawOptions) -> int:
    return SupervisedOpenClawRuntime(options).run()


def finalize_observation(options: FinalizeOptions) -> int:
    active = load_active_session(options.runs_dir)
    if not active:
        print("No active Critiqor monitoring session found.")
        print("Start one with:")
        print("critiqor monitor openclaw")
        return 0

    print("Stopping observer...")
    print("Finalizing evidence...")
    print("Generating diagnosis...")
    session = finalize_session(options.runs_dir)
    if session is None:
        print("No active Critiqor monitoring session found.")
        print("Start one with:")
        print("critiqor monitor openclaw")
        return 0
    run_id = str(session["run_id"])
    diagnosis_path = diagnosis_artifact_path(options.runs_dir, run_id)
    print(f"Diagnosis saved: {diagnosis_path}")
    if options.no_dashboard:
        return 0
    if not diagnosis_path.exists():
        print("Diagnosis file not found.")
        print()
        print("Run:")
        print("critiqor finalize")
        return 1

    from .dashboard import load_diagnosis_run, validate_diagnosis

    diagnosis = load_diagnosis_run(options.runs_dir, run_id)
    if not validate_diagnosis(diagnosis):
        print("Diagnosis file invalid. Dashboard launch aborted.")
        return 1

    print("Starting local dashboard...")
    return serve_local_dashboard(DashboardOptions(runs=options.runs_dir, host=options.host, port=options.port, run_id=run_id))


def serve_local_dashboard(options: DashboardOptions) -> int:
    from .dashboard import serve_dashboard

    serve_dashboard(
        options.events,
        runs_dir=options.runs,
        host=options.host,
        port=options.port,
        run_id=options.run_id,
        open_browser=options.open_browser,
    )
    return 0


def list_runs(options: RunsOptions) -> int:
    from .dashboard import list_diagnosis_runs, validate_diagnosis

    runs = [run for run in list_diagnosis_runs(options.runs_dir) if validate_diagnosis(run)]
    if not runs:
        print("No completed Critiqor evaluations found.")
        print("Run:")
        print("critiqor finalize")
        return 0
    print("Available Runs")
    print()
    for run in reversed(runs):
        print(run_summary_line(run))
    return 0


def run_summary_line(run: dict[str, Any]) -> str:
    run_id = str(run.get("run_id", "unknown_run"))
    summary = run.get("executive_summary") if isinstance(run.get("executive_summary"), dict) else {}
    evidence = run.get("evidence_panel") if isinstance(run.get("evidence_panel"), dict) else {}
    diagnosis = run.get("primary_diagnosis") if isinstance(run.get("primary_diagnosis"), dict) else {}
    trust = summary.get("trust_score", run.get("trust_score", "?"))
    tool_calls = evidence.get("tool_calls") if isinstance(evidence.get("tool_calls"), list) else []
    primary = str(diagnosis.get("root_cause_failure_type") or "No major issue").replace("_", " ").title()
    hallucination = "Low" if int(trust or 0) >= 75 else "Review" if int(trust or 0) >= 60 else "High"
    return f"{run_id} | Trust: {trust} | {len(tool_calls)} Tool Calls | Hallucination Risk: {hallucination} | {primary}"


def run_legacy_openclaw_command(options: MonitorOpenClawOptions) -> int:
    command = list(options.agent_command or [])
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("Critiqor OpenClaw run requires an agent command after --.")
        return 2

    payload = monitor_openclaw_process(
        command,
        agent_id=options.agent_id,
        tenant_id=options.tenant_id,
        visibility=options.visibility,
        benchmark_id=options.benchmark_id,
        difficulty_tier=options.difficulty_tier,
        cwd=options.cwd,
        timeout=options.timeout,
    )
    index = AgentReliabilityIndex(event_log_path=options.events)
    accepted = index.ingest_run(payload)
    diagnosis = index.dashboard.run_diagnosis_view(accepted.run_id)
    output_path = Path(options.evaluation)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(diagnosis, indent=2, sort_keys=True), encoding="utf-8")

    print("Critiqor observed OpenClaw execution")
    print(f"run_id: {accepted.run_id}")
    print(f"trust_score: {diagnosis['executive_summary']['trust_score']}")
    print(f"readiness_level: {diagnosis['executive_summary']['readiness_level']}")
    print(f"primary_diagnosis: {diagnosis['primary_diagnosis'].get('root_cause_failure_type')}")
    print(f"event_log: {options.events}")
    print(f"dashboard_json: {output_path}")
    print("dashboard: run `critiqor dashboard` after finalizing a monitored session")
    return 0


def check_deployment_policy(options: PolicyCheckOptions) -> int:
    policy = load_policy(options.policy)
    if options.minimum_trust_score is not None:
        policy["minimum_trust_score"] = options.minimum_trust_score
    if options.maximum_hallucination_risk is not None:
        policy["maximum_hallucination_risk"] = options.maximum_hallucination_risk

    evaluations = load_evaluations(options.evaluations, agent_id=options.agent_id, limit=1)
    if not evaluations:
        print("Deployment blocked")
        print("No Critiqor evaluations found.")
        return 1

    result = check_policy(evaluations[-1], policy)
    if result.passed:
        print("Deployment allowed")
    else:
        print("Deployment blocked")
    for message in result.messages:
        print(message)
    return 0 if result.passed else 1


def parse_openclaw_command(raw_command: str) -> list[str]:
    return shlex.split(raw_command)


def openclaw_environment(options: MonitorOpenClawOptions, run_id: str) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "CRITIQOR_RUN_ID": run_id,
            "CRITIQOR_RUNS_DIR": str(Path(options.runs_dir).resolve()),
            "CRITIQOR_AGENT_ID": str(options.agent_id),
            "CRITIQOR_TENANT_ID": str(options.tenant_id),
            "CRITIQOR_VISIBILITY": str(options.visibility),
            "CRITIQOR_EVENT_SOURCE": "openclaw",
        }
    )
    plugin_dir = critiqor_openclaw_plugin_dir()
    if plugin_dir.exists():
        env["OPENCLAW_BUNDLED_PLUGINS_DIR"] = str(plugin_dir.parent)
    return env


def critiqor_openclaw_plugin_dir() -> Path:
    package_plugin = Path(__file__).resolve().parent / "clawhub" / "critiqor-openclaw"
    if package_plugin.exists():
        return package_plugin
    return Path(__file__).resolve().parent.parent / "clawhub" / "critiqor-openclaw"



def diagnosis_artifact_path(runs_dir: str | Path, run_id: str) -> Path:
    return paths_for(runs_dir).diagnosis_path(run_id)



def load_policy(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    return parse_simple_yaml(text)


def parse_simple_yaml(text: str) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        policy[key.strip()] = parse_scalar(value.strip())
    return policy


def parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        return value
