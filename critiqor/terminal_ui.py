"""Small terminal presentation helpers for the Critiqor CLI."""

from __future__ import annotations

import click
import os

RULE = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


def _is_light_terminal() -> bool:
    override = os.environ.get("CRITIQOR_CLI_THEME", "").casefold()
    if override in {"light", "dark"}:
        return override == "light"
    colorfgbg = os.environ.get("COLORFGBG", "")
    if colorfgbg:
        try:
            background = int(colorfgbg.split(";")[-1])
        except ValueError:
            pass
        else:
            return background in {7, 15} or background >= 8
    return False


def _palette() -> dict[str, str | int | None]:
    if _is_light_terminal():
        return {
            "primary": None,
            "secondary": "bright_black",
            "heading": 166,
            "success": "green",
            "warning": "yellow",
            "error": "red",
        }
    return {
        "primary": None,
        "secondary": "bright_black",
        "heading": 208,
        "success": "green",
        "warning": "yellow",
        "error": "red",
    }


def line(text: str = "", *, fg: str | int | None = None, bold: bool = False, dim: bool = False) -> None:
    click.secho(text, fg=fg, bold=bold, dim=dim)


def primary(text: str = "", *, bold: bool = False) -> None:
    line(text, fg=_palette()["primary"], bold=bold)


def secondary(text: str = "") -> None:
    line(text, fg=_palette()["secondary"])


def title(text: str) -> None:
    click.echo()
    line(text, fg=_palette()["heading"], bold=True)
    secondary(RULE)
    click.echo()


def muted(text: str) -> None:
    secondary(text)


def success(text: str) -> None:
    line(f"✓ {text}", fg=_palette()["success"], bold=True)


def warning(text: str) -> None:
    line(f"⚠ {text}", fg=_palette()["warning"], bold=True)


def error(text: str) -> None:
    line(f"✕ {text}", fg=_palette()["error"], bold=True)


def section(label: str, value: str | None = None, *, icon: str = "▲") -> None:
    line(f"▲ {label}", fg=_palette()["success"], bold=True)
    if value is not None:
        secondary("│")
        primary(f"└─ {value}", bold=True)
    click.echo()


def command(command_text: str, heading: str = "Next Command") -> None:
    secondary(heading)
    primary(command_text, bold=True)
    click.echo()


def navigation_help() -> None:
    secondary(RULE)
    click.echo()
    secondary("↑ ↓ Navigate")
    click.echo()
    secondary("Enter Select")
    click.echo()
    secondary("Esc Cancel")


def option(label: str, *, selected: bool = False) -> None:
    if selected:
        click.secho("● ", fg=_palette()["success"], bold=True, nl=False)
        primary(label, bold=True)
    else:
        primary(f"  {label}")
