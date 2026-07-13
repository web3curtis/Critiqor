from __future__ import annotations

from typing import Any


def event_name(event: dict[str, Any]) -> str:
    return str(event.get("event_type") or event.get("event") or "runtime_event")


def payload(event: dict[str, Any]) -> dict[str, Any]:
    return event.get("payload") if isinstance(event.get("payload"), dict) else {}


def event_message(event: dict[str, Any]) -> str:
    data = payload(event)
    for key in ("message", "summary", "error", "status"):
        value = event.get(key) or data.get(key)
        if value:
            return str(value)
    tool = event.get("tool") or event.get("tool_name") or data.get("tool") or data.get("toolName")
    return f"{event_name(event)}: {tool}" if tool else event_name(event).replace("_", " ")


def is_internal(event: dict[str, Any]) -> bool:
    data = payload(event)
    text = " ".join(str(value or "") for value in (
        event.get("source"), event.get("source_layer"), event.get("message"),
        data.get("source"), data.get("source_layer"), data.get("message"),
    )).casefold()
    return any(marker in text for marker in (
        "critiqor_backend", "hosted diagnosis unavailable", "diagnosis backend unavailable",
        "critiqor_dashboard", "dashboard launch", "core engine dashboard",
    ))


def is_error(event: dict[str, Any]) -> bool:
    if is_internal(event):
        return False
    name = event_name(event).casefold()
    status = str(event.get("status") or payload(event).get("status") or "").casefold()
    return name in {"error", "error_event", "failure", "timeout", "evidence_parse_error", "exception"} or status in {
        "error", "failed", "failure", "timeout",
    }


def is_retry(event: dict[str, Any]) -> bool:
    return "retry" in event_name(event).casefold()


def select(events: list[dict[str, Any]], *names: str) -> list[dict[str, Any]]:
    accepted = set(names)
    return [event for event in events if event_name(event) in accepted]
