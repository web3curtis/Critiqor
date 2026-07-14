"""Tests for the public Critiqor client package."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from critiqor import OpenClawRuntimeObserver, create_session, finalize_session, generate_diagnosis, load_active_session
from critiqor.cli import main as cli_main
from critiqor.dashboard import validate_diagnosis
from critiqor.dashboard import create_dashboard_access, dashboard_access_path
from critiqor.frameworks import Framework, custom_name_error, load_config, resolve_framework, save_framework
from critiqor.runtime import (
    MonitorFrameworkOptions,
    dashboard_ingest_url,
    dashboard_run_url,
    monitor_framework,
)


class PublicClientTests(unittest.TestCase):
    def test_hosted_dashboard_urls_target_current_run_api(self) -> None:
        base = "https://dashboard.example/current/"
        self.assertEqual(
            dashboard_ingest_url(None, base),
            "https://dashboard.example/current/api/runs/ingest",
        )
        self.assertEqual(
            dashboard_run_url(base, "run_123"),
            "https://dashboard.example/current/?run_id=run_123",
        )
        self.assertEqual(
            dashboard_run_url(base, "run_123", private=True),
            "https://dashboard.example/current/access/run_123?mode=private",
        )

    def test_public_package_exports_local_diagnosis_without_split_wrappers(self) -> None:
        import critiqor
        self.assertTrue(callable(critiqor.generate_diagnosis))
        self.assertFalse(hasattr(critiqor, "HostedDiagnosisEngine"))
        self.assertFalse(hasattr(critiqor, "submit_evidence"))

    def test_observer_records_public_runtime_events(self) -> None:
        observer = OpenClawRuntimeObserver()
        event = observer.record("tool_call", {"tool": "bash", "args": {"cmd": "echo ok"}})

        self.assertEqual(event["event"], "tool_call")
        self.assertEqual(event["event_type"], "tool_call")
        self.assertEqual(event["source_layer"], "runtime_observer")
        self.assertEqual(observer.events[0]["payload"]["tool"], "bash")

    def test_finalize_saves_local_diagnosis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = create_session(runs_dir=tmp)
            run_id = session["run_id"]
            finalized = finalize_session(tmp)

            self.assertIsNotNone(finalized)
            saved = Path(tmp) / run_id / "diagnosis.json"
            self.assertTrue(saved.exists())
            payload = json.loads(saved.read_text())
            self.assertEqual(payload["diagnosis_source"], "local")
            self.assertTrue(validate_diagnosis(payload))

    def test_default_finalize_creates_local_dashboard_artifacts_without_backend_setup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = create_session(runs_dir=tmp, framework="codex")
            finalized = finalize_session(tmp)

            self.assertIsNone(load_active_session(tmp))
            self.assertEqual(finalized["status"], "COMPLETED")
            diagnosis_path = Path(tmp) / session["run_id"] / "diagnosis.json"
            self.assertTrue(diagnosis_path.exists())
            diagnosis = json.loads(diagnosis_path.read_text())
            self.assertEqual(diagnosis["diagnosis_source"], "local")
            self.assertEqual(diagnosis["framework"], "codex")
            self.assertTrue(validate_diagnosis(diagnosis))

    def test_local_diagnosis_uses_only_recorded_errors(self) -> None:
        diagnosis = generate_diagnosis(
            run_id="run_001", metadata={}, session_json="session.json",
            events=[{"event": "retry_event", "message": "Retried once"}],
        )
        self.assertEqual(diagnosis["evidence_panel"]["failures"], [])
        self.assertEqual(diagnosis["failure_analysis"]["failure_causes"][0]["type"], "retry_event")

    def test_private_dashboard_code_changes_for_each_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = create_dashboard_access(tmp, "run_001")
            second = create_dashboard_access(tmp, "run_001")
            self.assertNotEqual(first, second)
            payload = json.loads(dashboard_access_path(tmp).read_text())
            self.assertEqual(payload["code"], second)

    def test_cli_help_is_public_client_focused(self) -> None:
        self.assertEqual(cli_main(["help"]), 0)

    def test_help_lists_each_multi_agent_monitor_command(self) -> None:
        runner = CliRunner()
        result = runner.invoke(__import__("critiqor.cli", fromlist=["cli"]).cli, ["help"])
        self.assertEqual(result.exit_code, 0)
        for command in (
            "critiqor agents", "critiqor config", "critiqor monitor openclaw",
            "critiqor monitor cc", "critiqor monitor codex", "critiqor monitor <custom-framework>",
        ):
            self.assertIn(command, result.output)

    def test_framework_configuration_is_saved_and_reused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            framework = Framework("MyAgent", "myagent", "my-agent chat", official=False)
            save_framework(framework, "launch_command", path)
            resolved = resolve_framework("MyAgent", path)

            self.assertIsNotNone(resolved)
            self.assertEqual(resolved[0], framework)
            self.assertEqual(resolved[1], "launch_command")
            self.assertEqual(load_config(path)["selected_framework"], "myagent")

    def test_reserved_and_duplicate_custom_names_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            self.assertIn("reserved", custom_name_error("Codex", path) or "")
            save_framework(Framework("MyAgent", "myagent", "agent", official=False), "launch_command", path)
            self.assertEqual(custom_name_error("myagent", path), "Framework name already exists.")

    def test_official_monitor_aliases_do_not_require_setup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            resolved = resolve_framework("cc", path)
            self.assertEqual(resolved[0].name, "Claude Code")
            self.assertEqual(resolved[0].launch_command, "claude")

    def test_generic_monitor_launches_framework_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch("critiqor.runtime.shutil.which", return_value="/bin/agent"), patch(
            "critiqor.runtime.subprocess.Popen"
        ) as popen:
            process = popen.return_value
            process.pid = 42
            process.wait.return_value = 0
            framework = Framework("Claude Code", "cc", "claude")
            result = monitor_framework(MonitorFrameworkOptions(framework=framework, runs_dir=tmp))

            self.assertEqual(result, 0)
            popen.assert_called_once()
            self.assertEqual(popen.call_args.args[0], ["claude"])

    def test_agents_noninteractive_flow_configures_codex(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem(), patch.dict("os.environ", {"CRITIQOR_CONFIG_PATH": str(Path.cwd() / "config.json")}):
            result = runner.invoke(__import__("critiqor.cli", fromlist=["cli"]).cli, ["agents"], input="3\n1\n")
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("critiqor monitor codex", result.output)

    def test_config_can_modify_custom_framework_details(self) -> None:
        runner = CliRunner()
        with runner.isolated_filesystem():
            config = Path.cwd() / "config.json"
            with patch.dict("os.environ", {"CRITIQOR_CONFIG_PATH": str(config)}):
                save_framework(Framework("MyAgent", "myagent", "old-agent", official=False), "launch_command")
                result = runner.invoke(
                    __import__("critiqor.cli", fromlist=["cli"]).cli,
                    ["config"],
                    input="1\n2\nNewAgent\nnew-agent tui\n",
                )
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertIsNone(resolve_framework("MyAgent"))
                updated = resolve_framework("NewAgent")
                self.assertIsNotNone(updated)
                self.assertEqual(updated[0].launch_command, "new-agent tui")
                self.assertEqual(updated[1], "launch_command")


if __name__ == "__main__":
    unittest.main()
