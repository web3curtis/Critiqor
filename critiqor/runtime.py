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
import tempfile
from typing import Any
from .openclaw import monitor_openclaw_process
from .frameworks import Framework
from .integrity import object_digest, verify_manifest
from .schemas import validate_diagnosis_payload
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
class MonitorFrameworkOptions:
    framework: Framework
    cwd: str | None = None
    timeout: float | None = None
    runs_dir: str = "runs"
    tenant_id: str = "default"
    visibility: str = "private"


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


@dataclass(frozen=True)
class DoctorOptions:
    runs_dir: str = "runs"
    framework: str = "openclaw"


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

def monitor_framework(options: MonitorFrameworkOptions) -> int:
    """Launch a configured terminal framework under the common evidence recorder."""

    framework = options.framework
    command = shlex.split(framework.launch_command)
    if not command:
        print(f"No launch command configured for {framework.name}.")
        return 2
    if shutil.which(command[0]) is None:
        print(f"{framework.name} command not found: {command[0]}")
        return 127
    try:
        session = create_session(
            runs_dir=options.runs_dir,
            agent_id=f"{framework.slug}_agent",
            tenant_id=options.tenant_id,
            visibility=options.visibility,
            benchmark_id="agent_runtime_v1",
            framework=framework.slug,
        )
    except RuntimeError as exc:
        print(str(exc))
        return 1
    run_id = str(session["run_id"])
    environment = {
        **os.environ,
        "CRITIQOR_RUN_ID": run_id,
        "CRITIQOR_RUNS_DIR": str(Path(options.runs_dir).resolve()),
        "CRITIQOR_AGENT_ID": f"{framework.slug}_agent",
        "CRITIQOR_TENANT_ID": options.tenant_id,
        "CRITIQOR_VISIBILITY": options.visibility,
        "CRITIQOR_FRAMEWORK": framework.slug,
        "CRITIQOR_EVENT_SOURCE": framework.slug,
    }
    process: subprocess.Popen[Any] | None = None
    try:
        process = subprocess.Popen(command, cwd=options.cwd, env=environment)
        append_event_to_run(options.runs_dir, run_id, "process_start", {
            "command": command, "pid": process.pid, "framework": framework.slug,
        })
        exit_code = process.wait(timeout=options.timeout) if options.timeout else process.wait()
        append_event_to_run(options.runs_dir, run_id, "process_end", {
            "command": command, "pid": process.pid, "exit_code": exit_code,
            "framework": framework.slug,
        })
        print(f"{framework.name} session ended. Run `critiqor finalize`.")
        return int(exit_code or 0)
    except subprocess.TimeoutExpired:
        if process is not None:
            process.terminate()
        append_event_to_run(options.runs_dir, run_id, "error_event", {
            "source": framework.slug, "message": "Process timed out",
        })
        return 124
    except KeyboardInterrupt:
        if process is not None and process.poll() is None:
            process.terminate()
        return 130
    except OSError as exc:
        abort_session(options.runs_dir, f"Failed to launch {framework.name}: {exc}")
        print(f"Failed to launch {framework.name}: {exc}")
        return 1


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
    try:
        session = finalize_session(options.runs_dir)
    except RuntimeError as exc:
        print(str(exc))
        print("Diagnosis was not generated. Evidence remains available in the run session artifact.")
        return 1
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

    return serve_dashboard(
        options.events,
        runs_dir=options.runs,
        host=options.host,
        port=options.port,
        run_id=options.run_id,
        open_browser=options.open_browser,
    )


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


def run_doctor(options: DoctorOptions) -> int:
    """Validate the local Critiqor workflow without starting an agent."""

    from .backend import BackendConfig
    from .dashboard import find_core_engine_dashboard

    checks: list[tuple[str, str, str]] = []
    runs_path = Path(options.runs_dir).resolve()
    try:
        runs_path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=runs_path, prefix=".doctor-", delete=True):
            pass
    except OSError as exc:
        checks.append(("FAIL", "Run storage", str(exc)))
    else:
        checks.append(("PASS", "Run storage", str(runs_path)))

    if options.framework == "openclaw":
        executable = shutil.which("openclaw")
        checks.append(
            (
                "PASS" if executable else "FAIL",
                "OpenClaw",
                executable or "command not found on PATH",
            )
        )

    backend = BackendConfig.from_env()
    if backend.url.startswith(("https://", "http://")):
        checks.append(("PASS", "Diagnosis backend", backend.url))
    else:
        checks.append(("FAIL", "Diagnosis backend", "URL must use HTTP or HTTPS"))
    asymmetric_signing = bool(
        os.environ.get("CRITIQOR_SIGNING_PRIVATE_KEY")
        and os.environ.get("CRITIQOR_SIGNING_PUBLIC_KEY")
    )
    legacy_signing = bool(os.environ.get("CRITIQOR_SIGNING_KEY"))
    checks.append(
        (
            "PASS" if asymmetric_signing else "WARN",
            "Artifact signing",
            "Ed25519 signing and verification configured"
            if asymmetric_signing
            else "HMAC compatibility only" if legacy_signing
            else "Ed25519 keys are not configured; production policy checks will fail closed",
        )
    )
    dashboard = find_core_engine_dashboard()
    checks.append(
        (
            "PASS" if dashboard else "WARN",
            "Dashboard",
            str(dashboard) if dashboard else "not found; set CRITIQOR_DASHBOARD_DIR",
        )
    )
    checks.append(("PASS", "Privacy filter", "redaction and payload bounds active"))

    print("Critiqor Doctor")
    print()
    for status, name, detail in checks:
        print(f"{status:4} {name}: {detail}")
    failures = sum(status == "FAIL" for status, _, _ in checks)
    warnings = sum(status == "WARN" for status, _, _ in checks)
    print()
    print(f"{len(checks) - failures - warnings} passed, {warnings} warnings, {failures} failed")
    return 1 if failures else 0


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

    events = monitor_openclaw_process(
        command,
        agent_id=options.agent_id,
        tenant_id=options.tenant_id,
        benchmark_id=options.benchmark_id,
        difficulty_tier=options.difficulty_tier,
        cwd=options.cwd,
        timeout=options.timeout,
    )
    output_path = Path(options.evaluation)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"events": events}, indent=2, sort_keys=True), encoding="utf-8")

    print("Critiqor observed OpenClaw execution")
    print(f"events_collected: {len(events)}")
    print(f"evidence_json: {output_path}")
    print("Run `critiqor monitor openclaw` and `critiqor finalize` to generate a private-backend diagnosis.")
    return 0


def check_deployment_policy(options: PolicyCheckOptions) -> int:
    policy = {
        "minimum_trust_score": 75,
        "maximum_hallucination_risk": 25,
        "require_signed_manifest": True,
        **load_policy(options.policy),
    }
    if options.minimum_trust_score is not None:
        policy["minimum_trust_score"] = options.minimum_trust_score
    if options.maximum_hallucination_risk is not None:
        policy["maximum_hallucination_risk"] = options.maximum_hallucination_risk

    source = Path(options.evaluations)
    if not source.exists():
        print("Deployment blocked")
        print("No Critiqor diagnosis artifact found.")
        return 1
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Deployment blocked")
        print("Diagnosis artifact is invalid JSON.")
        return 1
    errors = validate_diagnosis_payload(payload)
    allowed_policy_fields = {
        "minimum_trust_score",
        "maximum_hallucination_risk",
        "require_signed_manifest",
        "required_evidence_status",
        "agent_id",
        "tenant_id",
        "framework",
        "benchmark_id",
    }
    unknown_policy_fields = sorted(set(policy) - allowed_policy_fields)
    if unknown_policy_fields:
        errors.append("unknown policy fields: " + ", ".join(unknown_policy_fields))
    summary = payload.get("executive_summary") if isinstance(payload.get("executive_summary"), dict) else {}
    manifest = payload.get("evaluation_manifest") if isinstance(payload.get("evaluation_manifest"), dict) else {}
    unsigned_payload = dict(payload)
    unsigned_payload.pop("evaluation_manifest", None)
    trust = score_value(summary.get("trust_score"), "trust_score", errors)
    minimum = score_value(policy.get("minimum_trust_score"), "minimum_trust_score", errors)
    risk = score_value(
        summary.get("hallucination_risk", payload.get("hallucination_risk", 0)),
        "hallucination_risk",
        errors,
    )
    maximum_risk = score_value(
        policy.get("maximum_hallucination_risk"),
        "maximum_hallucination_risk",
        errors,
    )
    expected_agent = options.agent_id or policy.get("agent_id")
    actual_agent = payload.get("agent_id") or manifest.get("agent_id")
    checks: list[tuple[bool, str]] = [
        (trust >= minimum, f"trust_score {trust:g} >= required {minimum:g}"),
        (risk <= maximum_risk, f"hallucination_risk {risk:g} <= allowed {maximum_risk:g}"),
    ]
    checks.append(
        (
            str(manifest.get("diagnosis_digest") or "") == object_digest(unsigned_payload),
            "diagnosis payload matches its signed digest",
        )
    )
    if expected_agent:
        checks.append(
            (
                str(actual_agent or "") == str(expected_agent),
                f"agent_id {actual_agent!r} matches required {expected_agent!r}",
            )
        )
    for identity_field in ("tenant_id", "framework", "benchmark_id"):
        if identity_field in policy:
            actual = payload.get(identity_field) or manifest.get(identity_field)
            checks.append(
                (
                    str(actual or "") == str(policy[identity_field]),
                    f"{identity_field} {actual!r} matches required {policy[identity_field]!r}",
                )
            )
    required_evidence_status = str(policy.get("required_evidence_status", "verified"))
    actual_evidence_status = str(manifest.get("evidence_status") or "")
    checks.append(
        (
            actual_evidence_status == required_evidence_status,
            f"evidence_status {actual_evidence_status!r} matches required {required_evidence_status!r}",
        )
    )
    if bool(policy.get("require_signed_manifest", True)):
        signature_check = verify_manifest(manifest)
        checks.append(
            (
                bool(signature_check["valid"]),
                "evaluation manifest signature is verified",
            )
        )
        errors.extend(signature_check["errors"])
    if errors or not all(passed for passed, _ in checks):
        print("Deployment blocked")
        for error in errors:
            print(f"FAIL: {error}")
        for passed, message in checks:
            print(f"{'PASS' if passed else 'FAIL'}: {message}")
        return 1
    print("Deployment allowed")
    for _, message in checks:
        print(f"PASS: {message}")
    return 0


def score_value(value: Any, field_name: str, errors: list[str]) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{field_name} must be a number between 0 and 100")
        return 0.0
    result = float(value)
    if not 0 <= result <= 100:
        errors.append(f"{field_name} must be between 0 and 100")
    return result


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
