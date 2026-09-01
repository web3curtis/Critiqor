"""Click command-line interface for Critiqor workflow integration."""

from __future__ import annotations

import sys

import click

from .banner import CRITIQOR_ASCII_LOGO
from . import terminal_ui as ui


class BriefHelpCommand(click.Command):
    """Command help that shows the purpose without advanced option noise."""

    def format_options(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        return


class BriefHelpGroup(click.Group):
    """Group help that shows subcommands without advanced option noise."""

    def format_options(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        self.format_commands(ctx, formatter)


from .runtime import (
    DashboardOptions,
    DoctorOptions,
    FinalizeOptions,
    MonitorOpenClawOptions,
    MonitorFrameworkOptions,
    PolicyCheckOptions,
    RunsOptions,
    check_deployment_policy,
    finalize_observation,
    monitor_openclaw,
    monitor_framework,
    list_runs,
    serve_local_dashboard,
    run_doctor,
)
from .frameworks import (
    Framework,
    OFFICIAL_FRAMEWORKS,
    configured_frameworks,
    configured_visibility,
    custom_name_error,
    custom_slug,
    load_config,
    resolve_framework,
    save_framework,
    save_visibility,
    update_framework,
)

_COMMAND_HELP = f"""{CRITIQOR_ASCII_LOGO}

Critiqor CLI

Commands:

critiqor agents
- Choose and configure an AI agent framework

critiqor config
- Change an observation method or custom framework details

critiqor monitor openclaw
- Launch OpenClaw TUI via (openclaw chat) and begin runtime observation

critiqor monitor cc
- Launch Claude Code and begin runtime observation

critiqor monitor codex
- Launch Codex CLI and begin runtime observation

critiqor finalize
- Stop observation session, generate diagnosis, and open the local dashboard

critiqor dashboard [run_id]
- Open the latest or selected local diagnosis dashboard

critiqor runs
- List completed evaluations with summaries

critiqor doctor
- Check collector, backend, dashboard, signing, privacy, and storage readiness

critiqor help
- Show available commands
"""


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True, cls=BriefHelpGroup)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Runtime reliability intelligence for OpenClaw agents."""

    if ctx.invoked_subcommand is None:
        click.echo(CRITIQOR_ASCII_LOGO)
        click.echo()
        click.echo(ctx.get_help())


@cli.command("help", cls=BriefHelpCommand)
def help_command() -> None:
    """Show available commands."""

    click.echo(_COMMAND_HELP.rstrip())


def _choose(title: str, choices: list[str]) -> int:
    """Arrow-key menu with a numbered fallback for redirected input."""
    if not sys.stdin.isatty():
        ui.title(title)
        for index, choice in enumerate(choices, 1):
            click.echo(f"{index}. {choice}")
        return max(0, min(len(choices) - 1, click.prompt("Select", type=int, default=1) - 1))
    selected = 0
    while True:
        click.clear()
        ui.title(title)
        for index, choice in enumerate(choices):
            ui.option(choice, selected=index == selected)
            click.echo()
        ui.navigation_help()
        key = click.getchar()
        if key in ("\r", "\n"):
            return selected
        if key in ("\x1b", "\x03"):
            raise click.Abort()
        if key in ("\x1b[A", "k"):
            selected = (selected - 1) % len(choices)
        elif key in ("\x1b[B", "j"):
            selected = (selected + 1) % len(choices)


def _observation_method() -> str:
    choices = ["Launch Command (Recommended)", "VS Code / Cursor Extension", "Import Log"]
    return ("launch_command", "ide_extension", "import_log")[_choose("Choose Observation Method", choices)]


def _configure_visibility() -> str:
    visibility = ("private", "shared", "anonymous", "public")[_choose(
        "Dashboard Visibility", ["Private", "Shared", "Anonymous", "Public"]
    )]
    save_visibility(visibility)
    ui.success(f"Dashboard visibility set to {visibility.title()}")
    return visibility


def _finish_configuration(framework: Framework, method: str) -> int:
    save_framework(framework, method)
    ui.title("Configuration Complete")
    ui.success("Framework configured")
    ui.section("Framework", framework.name, icon="◈")
    ui.section("Observation Method", method.replace("_", " ").title(), icon="◉")
    if method == "launch_command":
        ui.command(f"critiqor monitor {framework.slug if framework.official else framework.name}")
    elif method == "ide_extension":
        ui.command("critiqor agents", "Rerun after installing the VS Code / Cursor extension")
    else:
        ui.command("critiqor run -- <agent-command>", "Import-log capture is configured")
    return 0


@cli.group(cls=BriefHelpGroup)
def monitor() -> None:
    """Monitor an agent framework runtime."""


@monitor.command(
    "openclaw",
    cls=BriefHelpCommand,
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True, "help_option_names": ["-h", "--help"]},
)
@click.option("--agent-id", default="openclaw_agent", show_default=True, help="Agent identifier.")
@click.option("--tenant-id", default="default", show_default=True, help="Tenant identifier.")
@click.option(
    "--visibility",
    default="private",
    show_default=True,
    type=click.Choice(["private", "public", "anonymous", "shared"]),
    help="Dashboard-controlled visibility state to apply at ingestion.",
)
@click.option("--events", default=".critiqor/events.jsonl", show_default=True, help="Legacy event log path for custom command runs.")
@click.option("--evaluation", default=".critiqor/latest_run.json", show_default=True, help="Latest run diagnosis JSON path.")
@click.option("--benchmark-id", default="openclaw_runtime_v1", show_default=True, help="Versioned benchmark id.")
@click.option(
    "--difficulty-tier",
    default="standard",
    show_default=True,
    type=click.Choice(["easy", "standard", "hard", "stress"]),
    help="Benchmark difficulty tier.",
)
@click.option("--cwd", default=None, help="Working directory for the agent command.")
@click.option("--timeout", type=float, default=None, help="Optional process timeout in seconds.")
@click.option("--runs-dir", default="runs", show_default=True, help="Directory for Critiqor run artifacts.")
@click.option("--openclaw-command", default="openclaw chat", show_default=True, help="OpenClaw launch command.")
@click.argument("agent_command", nargs=-1, type=click.UNPROCESSED)
def monitor_openclaw_command(
    agent_id: str,
    tenant_id: str,
    visibility: str,
    events: str,
    evaluation: str,
    benchmark_id: str,
    difficulty_tier: str,
    cwd: str | None,
    timeout: float | None,
    runs_dir: str,
    openclaw_command: str,
    agent_command: tuple[str, ...],
) -> int:
    """Launch OpenClaw and begin runtime observation."""

    options = MonitorOpenClawOptions(
        agent_id=agent_id,
        tenant_id=tenant_id,
        visibility=visibility,
        events=events,
        evaluation=evaluation,
        benchmark_id=benchmark_id,
        difficulty_tier=difficulty_tier,
        cwd=cwd,
        timeout=timeout,
        runs_dir=runs_dir,
        openclaw_command=openclaw_command,
        agent_command=agent_command,
    )
    return monitor_openclaw(options)


def _monitor_official(slug: str, cwd: str | None, timeout: float | None, runs_dir: str) -> int:
    resolved = resolve_framework(slug)
    if resolved is None:
        raise click.ClickException(f"Unknown framework: {slug}")
    framework, _method = resolved
    return monitor_framework(
        MonitorFrameworkOptions(
            framework=framework, cwd=cwd, timeout=timeout, runs_dir=runs_dir
        )
    )


@monitor.command("cc", cls=BriefHelpCommand)
@click.option("--cwd", default=None)
@click.option("--timeout", type=float, default=None)
@click.option("--runs-dir", default="runs", show_default=True)
def monitor_cc_command(cwd: str | None, timeout: float | None, runs_dir: str) -> int:
    """Launch Claude Code and begin runtime observation."""

    return _monitor_official("cc", cwd, timeout, runs_dir)


@monitor.command("codex", cls=BriefHelpCommand)
@click.option("--cwd", default=None)
@click.option("--timeout", type=float, default=None)
@click.option("--runs-dir", default="runs", show_default=True)
def monitor_codex_command(cwd: str | None, timeout: float | None, runs_dir: str) -> int:
    """Launch Codex CLI and begin runtime observation."""

    return _monitor_official("codex", cwd, timeout, runs_dir)


@cli.command("agents", cls=BriefHelpCommand)
def agents_command() -> int:
    """Choose and configure an agent framework."""
    choices = [framework.name for framework in OFFICIAL_FRAMEWORKS] + ["Configure Custom Framework"]
    selected = _choose("Select Agent Framework", choices)
    if selected < len(OFFICIAL_FRAMEWORKS):
        framework = OFFICIAL_FRAMEWORKS[selected]
    else:
        while True:
            name = click.prompt("\nFramework Name").strip()
            error = custom_name_error(name)
            if not error:
                break
            ui.error(error)
        command = click.prompt("\nLaunch Command (N/A if none)", default="N/A").strip()
        framework = Framework(name, custom_slug(name), "" if command.casefold() == "n/a" else command, official=False)
    result = _finish_configuration(framework, _observation_method())
    _configure_visibility()
    return result


@cli.command("config", cls=BriefHelpCommand)
def config_command() -> int:
    """Change an observation method or custom framework details."""
    if _choose("Critiqor Configuration", ["Visibility Settings", "Framework Settings"]) == 0:
        current_visibility = configured_visibility()
        ui.section("Current Visibility", current_visibility.title(), icon="◉")
        access = load_config().get("active_dashboard_access", {})
        if current_visibility == "shared" and isinstance(access, dict) and access.get("invite_code"):
            ui.section("Active Invite Code", str(access["invite_code"]), icon="◆")
        _configure_visibility()
        return 0
    configured = load_config()["frameworks"]
    frameworks = [
        item for item in list(OFFICIAL_FRAMEWORKS) + configured_frameworks()
        if item.slug.casefold() in configured
    ]
    if not frameworks:
        ui.warning("No configured frameworks.")
        ui.command("critiqor agents", "Start Here")
        return 1
    framework = frameworks[_choose("Select Configured Framework", [item.name for item in frameworks])]
    if not framework.official and _choose("Configure Custom Framework", ["Observation Method", "Framework Details"]) == 1:
        old_slug = framework.slug
        while True:
            name = click.prompt("\nFramework Name", default=framework.name).strip()
            error = custom_name_error(name, exclude_slug=old_slug)
            if not error:
                break
            ui.error(error)
        command = click.prompt("\nLaunch Command", default=framework.launch_command or "N/A").strip()
        updated = Framework(name, custom_slug(name), "" if command.casefold() == "n/a" else command, framework.runtime_environment, False)
        current = resolve_framework(old_slug)
        method = current[1] if current else "launch_command"
        update_framework(old_slug, updated, method)
        ui.success("Framework updated")
        return 0
    return _finish_configuration(framework, _observation_method())


@cli.command("finalize", cls=BriefHelpCommand)
@click.option("--runs-dir", default="runs", show_default=True, help="Directory containing Critiqor run artifacts.")
@click.option("--no-dashboard", is_flag=True, help="Finalize without opening the local dashboard.")
@click.option("--host", default="127.0.0.1", show_default=True, help="Local dashboard host.")
@click.option("--port", type=int, default=0, show_default=True, help="Local dashboard port. Use 0 to choose an available port.")
def finalize_command(runs_dir: str, no_dashboard: bool, host: str, port: int) -> int:
    """Stop observation, generate diagnosis, and open local dashboard."""

    return finalize_observation(FinalizeOptions(runs_dir=runs_dir, no_dashboard=no_dashboard, host=host, port=port))


@cli.command("dashboard", cls=BriefHelpCommand)
@click.argument("run_id", required=False)
@click.option("--events", default=".critiqor/events.jsonl", show_default=True, help="Legacy Critiqor event log path.")
@click.option("--runs", default="runs", show_default=True, help="Directory containing finalized Critiqor run artifacts.")
@click.option("--host", default="127.0.0.1", show_default=True, help="Dashboard host.")
@click.option("--port", type=int, default=0, show_default=True, help="Dashboard port. Use 0 to choose an available port.")
def dashboard_command(run_id: str | None, events: str, runs: str, host: str, port: int) -> int:
    """Open the latest or selected local diagnosis dashboard."""

    return serve_local_dashboard(DashboardOptions(events=events, runs=runs, host=host, port=port, run_id=run_id))


@cli.command("runs", cls=BriefHelpCommand)
@click.option("--runs-dir", default="runs", show_default=True, help="Directory containing Critiqor run artifacts.")
def runs_command(runs_dir: str) -> int:
    """List completed evaluations with diagnosis summaries."""

    return list_runs(RunsOptions(runs_dir=runs_dir))


@cli.command("doctor", cls=BriefHelpCommand)
@click.option("--runs-dir", default="runs", show_default=True, help="Directory used for Critiqor run artifacts.")
@click.option("--framework", default="openclaw", show_default=True, type=click.Choice(["openclaw"]))
def doctor_command(runs_dir: str, framework: str) -> int:
    """Check whether Critiqor is ready to monitor and evaluate an agent."""

    return run_doctor(DoctorOptions(runs_dir=runs_dir, framework=framework))


@cli.command("run", cls=BriefHelpCommand, context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.option("--agent-id", default="openclaw_agent", show_default=True, help="Agent identifier.")
@click.option("--tenant-id", default="default", show_default=True, help="Tenant identifier.")
@click.option("--visibility", default="private", type=click.Choice(["private", "public", "anonymous", "shared"]), show_default=True)
@click.option("--events", default=".critiqor/events.jsonl", show_default=True)
@click.option("--evaluation", default=".critiqor/latest_run.json", show_default=True)
@click.option("--benchmark-id", default="openclaw_runtime_v1", show_default=True)
@click.option("--difficulty-tier", default="standard", type=click.Choice(["easy", "standard", "hard", "stress"]), show_default=True)
@click.option("--cwd", default=None)
@click.option("--timeout", type=float, default=None)
@click.option("--runs-dir", default="runs", show_default=True)
@click.argument("agent_command", nargs=-1, type=click.UNPROCESSED)
def run_command(
    agent_id: str,
    tenant_id: str,
    visibility: str,
    events: str,
    evaluation: str,
    benchmark_id: str,
    difficulty_tier: str,
    cwd: str | None,
    timeout: float | None,
    runs_dir: str,
    agent_command: tuple[str, ...],
) -> int:
    """Run and observe a custom agent command."""

    options = MonitorOpenClawOptions(
        agent_id=agent_id,
        tenant_id=tenant_id,
        visibility=visibility,
        events=events,
        evaluation=evaluation,
        benchmark_id=benchmark_id,
        difficulty_tier=difficulty_tier,
        cwd=cwd,
        timeout=timeout,
        runs_dir=runs_dir,
        agent_command=agent_command,
    )
    return monitor_openclaw(options)


@cli.command("check", cls=BriefHelpCommand)
@click.option("--evaluations", default="critiqor_evaluations.jsonl", show_default=True, help="Path to Critiqor JSONL evaluations.")
@click.option("--agent-id", default=None, help="Optional agent id filter.")
@click.option("--policy", default=None, help="Path to policy JSON/YAML.")
@click.option("--minimum-trust-score", type=int, default=None, help="Minimum trust score required to pass.")
@click.option("--maximum-hallucination-risk", type=int, default=None, help="Maximum allowed hallucination risk.")
def check_command(
    evaluations: str,
    agent_id: str | None,
    policy: str | None,
    minimum_trust_score: int | None,
    maximum_hallucination_risk: int | None,
) -> int:
    """Run a deployment policy check."""

    options = PolicyCheckOptions(
        evaluations=evaluations,
        agent_id=agent_id,
        policy=policy,
        minimum_trust_score=minimum_trust_score,
        maximum_hallucination_risk=maximum_hallucination_risk,
    )
    return check_deployment_policy(options)


def main(argv: list[str] | None = None) -> int:
    """Run the Critiqor CLI and return a process exit code."""

    try:
        result = cli.main(args=argv, prog_name="critiqor", standalone_mode=False)
    except click.exceptions.Exit as exc:
        return int(exc.exit_code or 0)
    except click.ClickException as exc:
        exc.show()
        return int(exc.exit_code)
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())
