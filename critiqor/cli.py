"""Click command-line interface for Critiqor workflow integration."""

from __future__ import annotations

import click
from pathlib import Path
import subprocess
import sys

from .banner import CRITIQOR_ASCII_LOGO


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
    FinalizeOptions,
    MonitorFrameworkOptions,
    PolicyCheckOptions,
    RunsOptions,
    check_deployment_policy,
    finalize_observation,
    monitor_framework,
    import_runtime_logs,
    list_runs,
    serve_local_dashboard,
)
from .frameworks import (
    Framework, OFFICIAL_FRAMEWORKS, configured_frameworks, custom_name_error,
    custom_slug, load_config, resolve_framework, save_framework,
)

_COMMAND_HELP = f"""{CRITIQOR_ASCII_LOGO}

Critiqor CLI

Commands:

critiqor agents
- Choose and configure an AI agent framework

critiqor config
- Change the observation method for a configured framework

critiqor monitor <framework>
- Launch and observe OpenClaw, Claude Code, Codex CLI, or a custom framework

critiqor finalize
- Stop observation session, generate diagnosis, and open the local dashboard

critiqor dashboard [run_id]
- Open the latest or selected local diagnosis dashboard

critiqor runs
- List completed evaluations with summaries

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
    """Arrow-key menu with a numbered fallback for non-interactive input."""
    if not sys.stdin.isatty():
        click.echo(title + "\n")
        for index, choice in enumerate(choices, 1):
            click.echo(f"{index}. {choice}")
        return max(0, min(len(choices) - 1, click.prompt("Select", type=int, default=1) - 1))
    selected = 0
    while True:
        click.clear()
        click.echo(title + "\n")
        for index, choice in enumerate(choices):
            click.echo(("> " if index == selected else "  ") + choice + "\n")
        click.echo("↑ ↓ Navigate\n\nSelect via Enter")
        key = click.getchar()
        if key in ("\r", "\n"):
            return selected
        if key in ("\x1b[A", "k"):
            selected = (selected - 1) % len(choices)
        elif key in ("\x1b[B", "j"):
            selected = (selected + 1) % len(choices)


def _observation_method() -> str:
    choices = ["Launch Command (Recommended)", "VS Code / Cursor Extension", "Import Log"]
    return ("launch_command", "ide_extension", "import_log")[_choose("Choose Observation Method", choices)]


def _extension_instructions() -> None:
    click.echo("\nInstall the Critiqor extension inside:\n\n• VS Code\n\nor\n\n• Cursor\n\nThen rerun this in your IDE:\n\ncritiqor agents")


def _pick_log() -> Path | None:
    """Open the operating system's native file picker."""
    try:
        choose_folder = _choose("Import Runtime Log", ["Select Log File", "Select Log Folder"]) == 1
        if sys.platform == "darwin":
            target = "folder" if choose_folder else "file"
            script = f'POSIX path of (choose {target} with prompt "Select agent runtime logs")'
            selected = subprocess.run(["osascript", "-e", script], check=False, capture_output=True, text=True)
            return Path(selected.stdout.strip()) if selected.returncode == 0 and selected.stdout.strip() else None
        if sys.platform == "win32":
            script = "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; if($d.ShowDialog() -eq 'OK'){$d.FileName}"
            selected = subprocess.run(["powershell", "-NoProfile", "-Command", script], check=False, capture_output=True, text=True)
            return Path(selected.stdout.strip()) if selected.stdout.strip() else None
        arguments = ["zenity", "--file-selection", "--title=Select agent runtime logs"]
        if choose_folder:
            arguments.append("--directory")
        selected = subprocess.run(arguments, check=False, capture_output=True, text=True)
        return Path(selected.stdout.strip()) if selected.returncode == 0 and selected.stdout.strip() else None
    except OSError:
        return None


def _finish_configuration(framework: Framework, method: str) -> int:
    save_framework(framework, method)
    if method == "ide_extension":
        _extension_instructions()
    elif method == "import_log":
        path = _pick_log()
        if path:
            click.echo(f"\nRuntime log selected: {path}")
            return import_runtime_logs(path, framework)
        else:
            click.echo("\nNo runtime log selected.")
    else:
        click.echo(f"\nConfiguration Complete.\n\nRun:\n\ncritiqor monitor {framework.slug if framework.official else framework.name}")
    return 0


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
            click.echo(f"\nError\n\n{error}\n\nPlease choose another name.")
        command = click.prompt("\nLaunch Command (N/A if none)", default="N/A").strip()
        framework = Framework(name, custom_slug(name), "" if command.casefold() == "n/a" else command, official=False)
    return _finish_configuration(framework, _observation_method())


@cli.command("config", cls=BriefHelpCommand)
def config_command() -> int:
    """Change a configured framework's observation method."""
    frameworks = list(OFFICIAL_FRAMEWORKS) + configured_frameworks()
    configured = load_config()["frameworks"]
    frameworks = [item for item in frameworks if item.slug.casefold() in configured]
    if not frameworks:
        click.echo("No configured frameworks. Run `critiqor agents` first.")
        return 1
    framework = frameworks[_choose("Select Configured Framework", [item.name for item in frameworks])]
    return _finish_configuration(framework, _observation_method())


@cli.command("monitor", cls=BriefHelpCommand)
@click.argument("framework_name")
@click.option("--cwd", default=None)
@click.option("--timeout", type=float, default=None)
@click.option("--runs-dir", default="runs", show_default=True)
def monitor_command(framework_name: str, cwd: str | None, timeout: float | None, runs_dir: str) -> int:
    """Launch and observe a configured agent framework."""
    resolved = resolve_framework(framework_name)
    if resolved is None:
        click.echo(f'Framework "{framework_name}" is not configured. Run `critiqor agents`.')
        return 2
    framework, method = resolved
    if method == "ide_extension":
        _extension_instructions()
        return 0
    if method == "import_log":
        path = _pick_log()
        if not path:
            click.echo("No runtime log selected.")
            return 0
        return import_runtime_logs(path, framework, runs_dir)
    return monitor_framework(MonitorFrameworkOptions(framework=framework, cwd=cwd, timeout=timeout, runs_dir=runs_dir))


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
