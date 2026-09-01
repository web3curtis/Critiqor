"""Small terminal presentation helpers for the Critiqor CLI."""

from __future__ import annotations

import click
import os
from typing import Literal

RULE = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


Theme = Literal["light", "dark"]
Color = str | int | None


def _ansi_luminance(index: int) -> float:
    """Return an approximate relative luminance for an ANSI 0-255 colour."""

    base = [
        (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
        (0, 0, 128), (128, 0, 128), (0, 128, 128), (192, 192, 192),
        (128, 128, 128), (255, 0, 0), (0, 255, 0), (255, 255, 0),
        (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255),
    ]
    if index < 16:
        red, green, blue = base[max(0, index)]
    elif index < 232:
        value = index - 16
        levels = (0, 95, 135, 175, 215, 255)
        red = levels[value // 36]
        green = levels[(value % 36) // 6]
        blue = levels[value % 6]
    else:
        red = green = blue = 8 + (min(index, 255) - 232) * 10
    return (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255


def terminal_theme() -> Theme:
    """Infer the terminal background, with an explicit override for opaque terminals."""

    override = os.environ.get("CRITIQOR_CLI_THEME", "").casefold()
    if override in {"light", "dark"}:
        return override  # type: ignore[return-value]
    colorfgbg = os.environ.get("COLORFGBG", "")
    if colorfgbg:
        try:
            background = int(colorfgbg.split(";")[-1])
        except ValueError:
            pass
        else:
            return "light" if _ansi_luminance(background) >= 0.55 else "dark"
    configured = os.environ.get("TERM_BACKGROUND", "").casefold()
    if configured in {"light", "dark"}:
        return configured  # type: ignore[return-value]
    # Most terminals do not expose their background. Prefer readable black text
    # on the common light default; dark-terminal users can set the explicit
    # CRITIQOR_CLI_THEME=dark override when no capability signal is available.
    return "light"


def _supports_extended_color() -> bool:
    term = os.environ.get("TERM", "").casefold()
    colorterm = os.environ.get("COLORTERM", "").casefold()
    return "256color" in term or colorterm in {"truecolor", "24bit"}


def semantic_palette(theme: Theme | None = None) -> dict[str, Color]:
    """Return contrast-safe colours by semantic role for the active theme."""

    active_theme = theme or terminal_theme()
    extended = _supports_extended_color()
    if active_theme == "light":
        return {
            "primary": 235 if extended else "black",
            "secondary": 94 if extended else "yellow",
            "heading": 166 if extended else "yellow",
            "success": 28 if extended else "green",
            "warning": 130 if extended else "yellow",
            "error": 160 if extended else "red",
        }
    return {
        "primary": 255 if extended else "bright_white",
        "secondary": 250 if extended else "bright_black",
        "heading": 208 if extended else "bright_yellow",
        "success": 40 if extended else "bright_green",
        "warning": 214 if extended else "bright_yellow",
        "error": 203 if extended else "bright_red",
    }


def _palette() -> dict[str, Color]:
    return semantic_palette()


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
