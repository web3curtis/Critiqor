"""Public OpenClaw runtime observation primitives.

This module is safe to distribute. It records runtime evidence and process
metadata only. It does not score, diagnose, benchmark, or perform root-cause
analysis locally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import subprocess
import time
from typing import Any, Sequence

from .schemas import OPENCLAW_EVENT_TYPES
from .session import utc_now


@dataclass
class OpenClawRuntimeObserver:
    """Non-invasive recorder for OpenClaw agent execution."""

    agent_id: str = "openclaw_agent"
    tenant_id: str = "default"
    benchmark_id: str = "openclaw_runtime_v1"
    difficulty_tier: str = "standard"
    events: list[dict[str, Any]] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    def record(self, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if event_type not in OPENCLAW_EVENT_TYPES:
            event_type = "process_output"
        event = {
            "event": event_type,
            "event_type": event_type,
            "timestamp": utc_now(),
            "source_layer": "runtime_observer",
            "payload": dict(payload or {}),
        }
        self.events.append(event)
        return event


def parse_process_line(line: str) -> dict[str, Any] | None:
    stripped = line.strip()
    if not stripped or not stripped.startswith("{") or not stripped.endswith("}"):
        return None
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def capture_process_stream(observer: OpenClawRuntimeObserver, text: str, stream: str) -> None:
    for line in text.splitlines():
        parsed = parse_process_line(line)
        if parsed is not None:
            event_type = str(parsed.get("event_type") or parsed.get("event") or parsed.get("type") or "process_output")
            observer.record(event_type, parsed)
        else:
            observer.record("process_output", {"stream": stream, "text": line})


def monitor_openclaw_process(
    command: Sequence[str],
    agent_id: str = "openclaw_agent",
    tenant_id: str = "default",
    benchmark_id: str = "openclaw_runtime_v1",
    difficulty_tier: str = "standard",
    cwd: str | None = None,
    timeout: float | None = None,
) -> list[dict[str, Any]]:
    """Run a process and return collected evidence events without diagnosis."""

    observer = OpenClawRuntimeObserver(
        agent_id=agent_id,
        tenant_id=tenant_id,
        benchmark_id=benchmark_id,
        difficulty_tier=difficulty_tier,
    )
    observer.record("process_start", {"command": list(command)})
    started = time.time()
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            timeout=timeout,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except subprocess.TimeoutExpired:
        observer.record("error_event", {"error": "timeout", "timeout": timeout})
        observer.record("process_end", {"exit_code": None, "latency": round(time.time() - started, 4)})
        return observer.events

    capture_process_stream(observer, completed.stdout, "stdout")
    capture_process_stream(observer, completed.stderr, "stderr")
    if completed.returncode != 0:
        observer.record("error_event", {"error": "process_exit", "exit_code": completed.returncode})
    observer.record("process_end", {"exit_code": completed.returncode, "latency": round(time.time() - started, 4)})
    return observer.events
