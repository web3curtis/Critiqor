"""Tests for the public Critiqor client package."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from critiqor import EvidenceSubmission, OpenClawRuntimeObserver, create_session, finalize_session, load_active_session
from critiqor.backend import BackendConfig, BackendConfigurationError, submit_evidence
from critiqor.cli import main as cli_main
from critiqor.dashboard import validate_diagnosis
from critiqor.frameworks import Framework, custom_name_error, load_config, resolve_framework, save_framework
from critiqor.runtime import MonitorFrameworkOptions, monitor_framework


class PublicClientTests(unittest.TestCase):
    def test_public_package_does_not_export_private_engines(self) -> None:
        import critiqor

        forbidden = {
            "Critiqor",
            "AgentReliabilityIndex",
            "diagnose_openclaw_events",
            "build_openclaw_run_payload",
            "generate_leaderboard",
            "benchmark_run",
        }
        for name in forbidden:
            self.assertFalse(hasattr(critiqor, name), name)

    def test_observer_records_public_runtime_events(self) -> None:
        observer = OpenClawRuntimeObserver()
        event = observer.record("tool_call", {"tool": "bash", "args": {"cmd": "echo ok"}})

        self.assertEqual(event["event"], "tool_call")
        self.assertEqual(event["event_type"], "tool_call")
        self.assertEqual(event["source_layer"], "runtime_observer")
        self.assertEqual(observer.events[0]["payload"]["tool"], "bash")

    def test_backend_client_accepts_wrapped_diagnosis_response(self) -> None:
        submission = EvidenceSubmission(
            run_id="run_001",
            metadata={"framework": "openclaw"},
            session={"run_id": "run_001"},
            events=[],
        )

        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                return None
            def read(self):
                return json.dumps({
                    "diagnosis": {
                        "run_id": "run_001",
                        "executive_summary": {"trust_score": 91},
                    }
                }).encode()

        with patch("critiqor.backend.urlopen", return_value=Response()):
            result = submit_evidence(submission, BackendConfig(url="https://backend.example/v1/diagnoses"))

        self.assertEqual(result.run_id, "run_001")
        self.assertEqual(result.to_dict()["executive_summary"]["trust_score"], 91)

    def test_finalize_submits_evidence_and_saves_backend_diagnosis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = create_session(runs_dir=tmp)
            run_id = session["run_id"]
            diagnosis = {
                "run_id": run_id,
                "executive_summary": {"trust_score": 88, "readiness_level": "review_recommended"},
                "primary_diagnosis": {"root_cause_failure_type": "backend_generated"},
                "evidence_panel": {"causal_graph": {"nodes": [], "edges": []}},
            }
            with patch("critiqor.session.submit_evidence") as mocked:
                mocked.return_value.to_dict.return_value = dict(diagnosis)
                finalized = finalize_session(tmp)

            self.assertIsNotNone(finalized)
            mocked.assert_called_once()
            saved = Path(tmp) / run_id / "diagnosis.json"
            self.assertTrue(saved.exists())
            payload = json.loads(saved.read_text())
            self.assertEqual(payload["executive_summary"]["trust_score"], 88)
            self.assertTrue(validate_diagnosis(payload))

    def test_failed_backend_keeps_session_retryable_not_finalizing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = create_session(runs_dir=tmp, framework="codex")
            with patch("critiqor.session.submit_evidence", side_effect=BackendConfigurationError("offline")):
                with self.assertRaises(RuntimeError):
                    finalize_session(tmp)

            active = load_active_session(tmp)
            self.assertIsNotNone(active)
            self.assertEqual(active["status"], "MONITORING")
            saved = json.loads((Path(tmp) / f"{session['run_id']}.json").read_text())
            self.assertEqual(saved["metadata"]["framework"], "codex")
            self.assertEqual(saved["status"], "MONITORING")

    def test_dashboard_explains_backend_failure_without_finalize_loop(self) -> None:
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmp:
            create_session(runs_dir=tmp)
            with patch("critiqor.session.submit_evidence", side_effect=BackendConfigurationError("offline")):
                with self.assertRaises(RuntimeError):
                    finalize_session(tmp)
            result = runner.invoke(
                __import__("critiqor.cli", fromlist=["cli"]).cli,
                ["dashboard", "--runs", tmp],
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Latest diagnosis error: offline", result.output)
            self.assertIn("evidence is retained", result.output)
            self.assertNotIn("Run:\ncritiqor finalize", result.output)

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
