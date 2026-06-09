"""Command-line interface for Critiqor workflow integration."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
from urllib import request
from urllib.error import URLError
from urllib.parse import urlencode
import webbrowser

from .core import check_policy, load_evaluations
from .openclaw import monitor_openclaw_process
from .platform import AgentReliabilityIndex
from .session import (
    create_session,
    finalize_session,
    load_active_session,
    monitor_until_finalized,
)


def main(argv: list[str] | None = None) -> int:
    """Run the Critiqor CLI."""

    parser = argparse.ArgumentParser(prog="critiqor")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Run a deployment policy check.")
    check_parser.add_argument(
        "--evaluations",
        default="critiqor_evaluations.jsonl",
        help="Path to Critiqor JSONL evaluations.",
    )
    check_parser.add_argument("--agent-id", default=None, help="Optional agent id filter.")
    check_parser.add_argument("--policy", default=None, help="Path to policy JSON/YAML.")
    check_parser.add_argument(
        "--minimum-trust-score",
        type=int,
        default=None,
        help="Minimum trust score required to pass.",
    )
    check_parser.add_argument(
        "--maximum-hallucination-risk",
        type=int,
        default=None,
        help="Maximum allowed hallucination risk.",
    )

    monitor_parser = subparsers.add_parser("monitor", help="Monitor an agent framework runtime.")
    monitor_subparsers = monitor_parser.add_subparsers(dest="framework")
    openclaw_parser = monitor_subparsers.add_parser("openclaw", help="Observe an OpenClaw agent process.")
    _add_monitor_args(openclaw_parser)

    run_parser = subparsers.add_parser("run", help="Run and observe an agent command.")
    _add_monitor_args(run_parser)

    finalize_parser = subparsers.add_parser("finalize", help="Finalize the active OpenClaw observation session.")
    finalize_parser.add_argument("--runs-dir", default="runs", help="Directory containing Critiqor run artifacts.")
    finalize_parser.add_argument("--host", default="127.0.0.1", help="Dashboard host to launch.")
    finalize_parser.add_argument("--port", type=int, default=8765, help="Dashboard port to launch.")
    finalize_parser.add_argument("--no-dashboard", action="store_true", help="Finalize without launching the dashboard.")

    dashboard_parser = subparsers.add_parser("dashboard", help="Serve a local Critiqor dashboard.")
    dashboard_parser.add_argument("--events", default=".critiqor/events.jsonl", help="Path to Critiqor event log JSONL.")
    dashboard_parser.add_argument("--runs", default="runs", help="Directory containing finalized Critiqor run artifacts.")
    dashboard_parser.add_argument("--host", default="127.0.0.1", help="Dashboard host.")
    dashboard_parser.add_argument("--port", type=int, default=8765, help="Dashboard port.")

    args = parser.parse_args(argv)
    if args.command == "check":
        return _check(args)
    if args.command == "monitor" and args.framework == "openclaw":
        return _monitor_openclaw(args)
    if args.command == "run":
        return _run_openclaw_command(args)
    if args.command == "finalize":
        return _finalize(args)
    if args.command == "dashboard":
        from .dashboard import serve_dashboard

        serve_dashboard(args.events, runs_dir=args.runs, host=args.host, port=args.port)
        return 0

    parser.print_help()
    return 0


def _add_monitor_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("agent_command", nargs=argparse.REMAINDER, help="Optional legacy command to launch after --.")
    parser.add_argument("--agent-id", default="openclaw_agent", help="Agent identifier.")
    parser.add_argument("--tenant-id", default="default", help="Tenant identifier.")
    parser.add_argument("--visibility", default="private", choices=["private", "public", "anonymous", "shared"], help="Dashboard-controlled visibility state to apply at ingestion.")
    parser.add_argument("--events", default=".critiqor/events.jsonl", help="Append-only event log path.")
    parser.add_argument("--evaluation", default=".critiqor/latest_run.json", help="Latest run diagnosis JSON path.")
    parser.add_argument("--benchmark-id", default="openclaw_runtime_v1", help="Versioned benchmark id.")
    parser.add_argument("--difficulty-tier", default="standard", choices=["easy", "standard", "hard", "stress"], help="Benchmark difficulty tier.")
    parser.add_argument("--cwd", default=None, help="Working directory for the agent command.")
    parser.add_argument("--timeout", type=float, default=None, help="Optional process timeout in seconds.")
    parser.add_argument("--runs-dir", default="runs", help="Directory for Critiqor run artifacts.")
    parser.add_argument("--dashboard-url", default=None, help="Dashboard URL to print/open after ingestion. Defaults to CRITIQOR_DASHBOARD_URL.")
    parser.add_argument("--ingest-url", default=None, help="Dashboard API ingest URL. Defaults to <dashboard-url>/api/runs/ingest or CRITIQOR_INGEST_URL.")
    parser.add_argument("--open-dashboard", action="store_true", help="Open the dashboard URL for this run after monitoring completes.")


def _monitor_openclaw(args: argparse.Namespace) -> int:
    command = list(args.agent_command or [])
    if command and command[0] == "--":
        command = command[1:]
    if command:
        return _run_openclaw_command(args)

    active = load_active_session(args.runs_dir)
    if active:
        print(f"Critiqor monitoring is already active for {active['run_id']}.")
        print("Finalize it with:")
        print("critiqor finalize")
        return 1

    try:
        session = create_session(
            runs_dir=args.runs_dir,
            agent_id=args.agent_id,
            tenant_id=args.tenant_id,
            visibility=args.visibility,
            benchmark_id=args.benchmark_id,
            difficulty_tier=args.difficulty_tier,
        )
    except RuntimeError as exc:
        print(str(exc))
        return 1

    print("✓ OpenClaw detected")
    print("✓ Runtime observer attached")
    print("✓ Event collection active")
    print("Write 'critiqor finalize' to stop monitoring and generate a diagnosis report.")
    try:
        monitor_until_finalized(session, args.runs_dir)
    except KeyboardInterrupt:
        print("Monitoring process terminated intentionally.")
        print("Run `critiqor finalize` to generate a diagnosis report from collected evidence.")
        return 130
    return 0


def _run_openclaw_command(args: argparse.Namespace) -> int:
    command = list(args.agent_command or [])
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("Critiqor OpenClaw run requires an agent command after --.")
        return 2

    payload = monitor_openclaw_process(
        command,
        agent_id=args.agent_id,
        tenant_id=args.tenant_id,
        visibility=args.visibility,
        benchmark_id=args.benchmark_id,
        difficulty_tier=args.difficulty_tier,
        cwd=args.cwd,
        timeout=args.timeout,
    )
    index = AgentReliabilityIndex(event_log_path=args.events)
    accepted = index.ingest_run(payload)
    diagnosis = index.dashboard.run_diagnosis_view(accepted.run_id)
    output_path = Path(args.evaluation)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(diagnosis, indent=2, sort_keys=True), encoding="utf-8")

    dashboard_url = _dashboard_url(args.dashboard_url, accepted.run_id)
    ingest_url = _ingest_url(args.ingest_url, args.dashboard_url)
    if ingest_url:
        try:
            _post_dashboard_ingest(ingest_url, diagnosis)
            print(f"dashboard_sync: accepted by {ingest_url}")
        except OSError as exc:
            print(f"dashboard_sync: failed ({exc})")

    print("Critiqor observed OpenClaw execution")
    print(f"run_id: {accepted.run_id}")
    print(f"trust_score: {diagnosis['executive_summary']['trust_score']}")
    print(f"readiness_level: {diagnosis['executive_summary']['readiness_level']}")
    print(f"primary_diagnosis: {diagnosis['primary_diagnosis'].get('root_cause_failure_type')}")
    print(f"event_log: {args.events}")
    print(f"dashboard_json: {output_path}")
    if dashboard_url:
        print(f"dashboard: {dashboard_url}")
        if args.open_dashboard:
            webbrowser.open(dashboard_url)
    else:
        print("dashboard: run `critiqor dashboard --events " + args.events + "` or pass --dashboard-url to sync the web dashboard")
    return 0


def _finalize(args: argparse.Namespace) -> int:
    active = load_active_session(args.runs_dir)
    if not active:
        print("No active Critiqor monitoring session found.")
        print("Start one with:")
        print("critiqor monitor openclaw")
        return 0

    print("Stopping observer...")
    print("Finalizing evidence...")
    print("Generating diagnosis...")
    session = finalize_session(args.runs_dir)
    if session is None:
        print("No active Critiqor monitoring session found.")
        print("Start one with:")
        print("critiqor monitor openclaw")
        return 0
    print("Launching dashboard...")
    if not args.no_dashboard:
        _launch_dashboard(args.runs_dir, args.host, args.port, str(session["run_id"]))
    return 0


def _launch_dashboard(runs_dir: str, host: str, port: int, run_id: str) -> None:
    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "critiqor.cli",
            "dashboard",
            "--runs",
            runs_dir,
            "--host",
            host,
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    webbrowser.open(f"http://{host}:{port}?run_id={run_id}")


def _dashboard_url(raw_url: str | None, run_id: str) -> str | None:
    base = raw_url or os.environ.get("CRITIQOR_DASHBOARD_URL")
    if not base:
        return None
    separator = "&" if "?" in base else "?"
    return f"{base}{separator}{urlencode({'run_id': run_id})}"


def _ingest_url(raw_url: str | None, dashboard_url: str | None) -> str | None:
    explicit = raw_url or os.environ.get("CRITIQOR_INGEST_URL")
    if explicit:
        return explicit
    base = dashboard_url or os.environ.get("CRITIQOR_DASHBOARD_URL")
    if not base:
        return None
    return base.rstrip("/") + "/api/runs/ingest"


def _post_dashboard_ingest(ingest_url: str, diagnosis: dict[str, Any]) -> None:
    body = json.dumps(diagnosis).encode("utf-8")
    req = request.Request(
        ingest_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            if response.status >= 400:
                raise OSError(f"HTTP {response.status}")
    except URLError as exc:
        raise OSError(str(exc)) from exc


def _check(args: argparse.Namespace) -> int:
    policy = _load_policy(args.policy)
    if args.minimum_trust_score is not None:
        policy["minimum_trust_score"] = args.minimum_trust_score
    if args.maximum_hallucination_risk is not None:
        policy["maximum_hallucination_risk"] = args.maximum_hallucination_risk

    evaluations = load_evaluations(args.evaluations, agent_id=args.agent_id, limit=1)
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


def _load_policy(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        policy[key.strip()] = _parse_scalar(value.strip())
    return policy


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        return value


if __name__ == "__main__":
    raise SystemExit(main())
