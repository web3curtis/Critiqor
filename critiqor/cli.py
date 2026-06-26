"""Click command-line interface for Critiqor workflow integration."""

from __future__ import annotations

import click


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
    MonitorOpenClawOptions,
    PolicyCheckOptions,
    RunsOptions,
    check_deployment_policy,
    finalize_observation,
    monitor_openclaw,
    list_runs,
    serve_local_dashboard,
)

_COMMAND_HELP = """Critiqor CLI

Commands:

critiqor monitor openclaw
- Launch OpenClaw TUI via (openclaw chat) and begin runtime observation

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
        click.echo(ctx.get_help())


@cli.command("help", cls=BriefHelpCommand)
def help_command() -> None:
    """Show available commands."""

    click.echo(_COMMAND_HELP.rstrip())


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
