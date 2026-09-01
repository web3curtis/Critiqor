"""Framework selection and persisted observation configuration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class Framework:
    name: str
    slug: str
    launch_command: str
    runtime_environment: str = "terminal"
    official: bool = True


OFFICIAL_FRAMEWORKS = (
    Framework("OpenClaw", "openclaw", "openclaw chat"),
    Framework("Claude Code", "cc", "claude"),
    Framework("Codex CLI", "codex", "codex"),
)

RESERVED_NAMES = {"openclaw", "claude code", "claude", "codex", "codex cli", "cc"}
OBSERVATION_METHODS = ("launch_command", "ide_extension", "import_log")
VISIBILITY_OPTIONS = ("private", "shared", "anonymous", "public")


def config_path() -> Path:
    override = os.environ.get("CRITIQOR_CONFIG_PATH")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".critiqor" / "config.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    source = path or config_path()
    if not source.exists():
        return {"version": 1, "frameworks": {}}
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "frameworks": {}}
    if not isinstance(payload, dict) or not isinstance(payload.get("frameworks", {}), dict):
        return {"version": 1, "frameworks": {}}
    payload.setdefault("version", 1)
    payload.setdefault("frameworks", {})
    return payload


def save_framework(framework: Framework, observation_method: str, path: Path | None = None) -> None:
    if observation_method not in OBSERVATION_METHODS:
        raise ValueError(f"Unsupported observation method: {observation_method}")
    destination = path or config_path()
    payload = load_config(destination)
    item = asdict(framework)
    item["observation_method"] = observation_method
    payload["frameworks"][framework.slug.casefold()] = item
    payload["selected_framework"] = framework.slug
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)


def configured_visibility(path: Path | None = None) -> str:
    value = str(load_config(path).get("visibility", "private")).casefold()
    return value if value in VISIBILITY_OPTIONS else "private"


def save_visibility(visibility: str, path: Path | None = None) -> None:
    value = visibility.casefold()
    if value not in VISIBILITY_OPTIONS:
        raise ValueError(f"Unsupported visibility: {visibility}")
    destination = path or config_path()
    payload = load_config(destination)
    payload["visibility"] = value
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)


def save_launch_credential(visibility: str, credential: str, path: Path | None = None) -> None:
    destination = path or config_path()
    payload = load_config(destination)
    payload["active_dashboard_access"] = {
        "visibility": visibility,
        "invite_code": credential if visibility == "shared" else "",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)


def update_framework(old_slug: str, framework: Framework, observation_method: str, path: Path | None = None) -> None:
    """Replace a custom framework, including its configuration key after a rename."""
    destination = path or config_path()
    payload = load_config(destination)
    payload["frameworks"].pop(old_slug.casefold(), None)
    item = asdict(framework)
    item["observation_method"] = observation_method
    payload["frameworks"][framework.slug.casefold()] = item
    payload["selected_framework"] = framework.slug
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(destination)


def configured_frameworks(path: Path | None = None) -> list[Framework]:
    result: list[Framework] = []
    for item in load_config(path)["frameworks"].values():
        if isinstance(item, dict) and not item.get("official", False):
            result.append(Framework(
                name=str(item.get("name", "")), slug=str(item.get("slug", "")),
                launch_command=str(item.get("launch_command", "")),
                runtime_environment=str(item.get("runtime_environment", "terminal")), official=False,
            ))
    return result


def resolve_framework(identifier: str, path: Path | None = None) -> tuple[Framework, str] | None:
    key = identifier.casefold()
    aliases = {"claude": "cc", "claude code": "cc", "codex cli": "codex"}
    key = aliases.get(key, key)
    payload = load_config(path)
    for framework in OFFICIAL_FRAMEWORKS:
        if key in {framework.slug.casefold(), framework.name.casefold()}:
            saved = payload["frameworks"].get(framework.slug.casefold(), {})
            return framework, str(saved.get("observation_method", "launch_command"))
    for item in payload["frameworks"].values():
        if isinstance(item, dict) and key in {str(item.get("slug", "")).casefold(), str(item.get("name", "")).casefold()}:
            framework = Framework(
                str(item["name"]), str(item["slug"]), str(item.get("launch_command", "")),
                str(item.get("runtime_environment", "terminal")), bool(item.get("official", False)),
            )
            return framework, str(item.get("observation_method", "launch_command"))
    return None


def custom_name_error(name: str, path: Path | None = None, exclude_slug: str | None = None) -> str | None:
    normalized = " ".join(name.split()).casefold()
    if not normalized:
        return "Framework name is required."
    if normalized in RESERVED_NAMES:
        return f'"{name.strip()}" is already a reserved framework.'
    if any(
        framework.slug.casefold() != (exclude_slug or "").casefold() and framework.name.casefold() == normalized
        for framework in configured_frameworks(path)
    ):
        return "Framework name already exists."
    return None


def custom_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    return slug or "custom-agent"
