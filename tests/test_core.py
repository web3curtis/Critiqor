"""Tests for the public Critiqor client package."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from critiqor import EvidenceSubmission, OpenClawRuntimeObserver, create_session, finalize_session
from critiqor.backend import BackendConfig, BackendResponseError, submit_evidence
from critiqor.cli import main as cli_main
from critiqor.dashboard import validate_diagnosis
from critiqor.integrity import (
    generate_ed25519_keypair,
    object_digest,
    seal_events,
    sign_manifest,
    verify_events,
    verify_manifest,
)
from critiqor.runtime import PolicyCheckOptions, check_deployment_policy
from critiqor.terminal_ui import semantic_palette, terminal_theme


class PublicClientTests(unittest.TestCase):
    def test_terminal_theme_override_and_colorfgbg_detection(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(terminal_theme(), "light")
        with patch.dict("os.environ", {"CRITIQOR_CLI_THEME": "light"}, clear=True):
            self.assertEqual(terminal_theme(), "light")
        with patch.dict("os.environ", {"CRITIQOR_CLI_THEME": "dark"}, clear=True):
            self.assertEqual(terminal_theme(), "dark")
        with patch.dict("os.environ", {"COLORFGBG": "0;15"}, clear=True):
            self.assertEqual(terminal_theme(), "light")
        with patch.dict("os.environ", {"COLORFGBG": "15;0"}, clear=True):
            self.assertEqual(terminal_theme(), "dark")
        with patch.dict("os.environ", {"COLORFGBG": "15;8"}, clear=True):
            self.assertEqual(terminal_theme(), "dark")

    def test_terminal_semantic_palettes_are_explicit_and_contrasting(self) -> None:
        with patch.dict("os.environ", {"TERM": "xterm-256color"}, clear=True):
            light = semantic_palette("light")
            dark = semantic_palette("dark")
        self.assertEqual(light["primary"], 235)
        self.assertEqual(light["secondary"], 94)
        self.assertEqual(dark["primary"], 255)
        self.assertEqual(dark["secondary"], 250)
        self.assertNotEqual(light["primary"], dark["primary"])
        self.assertNotEqual(light["secondary"], dark["secondary"])

    def test_v026_framework_command_compatibility(self) -> None:
        from critiqor.cli import cli
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem():
            with patch.dict("os.environ", {"CRITIQOR_CONFIG_PATH": "config.json"}):
                result = runner.invoke(cli, ["agents"], input="1\n1\n1\n")
                self.assertEqual(result.exit_code, 0)
                self.assertIn("Framework configured", result.output)
                self.assertIn("OpenClaw", result.output)
                configured = runner.invoke(cli, ["config"], input="2\n1\n1\n")
                self.assertEqual(configured.exit_code, 0)
                self.assertIn("Framework configured", configured.output)
        monitor = next(command for command in cli.commands.values() if command.name == "monitor")
        self.assertTrue({"openclaw", "cc", "codex"}.issubset(monitor.commands))

    def test_visibility_configuration_is_persisted(self) -> None:
        from critiqor.cli import cli
        from critiqor.frameworks import configured_visibility
        from click.testing import CliRunner
        runner = CliRunner()
        with runner.isolated_filesystem():
            with patch.dict("os.environ", {"CRITIQOR_CONFIG_PATH": "config.json"}):
                result = runner.invoke(cli, ["config"], input="1\n2\n")
                self.assertEqual(result.exit_code, 0)
                self.assertEqual(configured_visibility(), "shared")
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

    def test_finalize_uses_local_diagnosis_without_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = create_session(runs_dir=tmp)
            with patch.dict("os.environ", {"CRITIQOR_BACKEND_URL": ""}, clear=False):
                with patch("critiqor.session.submit_evidence") as mocked:
                    finalized = finalize_session(tmp)
            mocked.assert_not_called()
            self.assertEqual(finalized["status"], "COMPLETED")
            payload = json.loads((Path(tmp) / session["run_id"] / "diagnosis.json").read_text())
            self.assertEqual(payload["diagnosis_source"], "local")

    def test_local_diagnosis_includes_memory_utilization_from_runtime_evidence(self) -> None:
        from critiqor.diagnosis import generate_diagnosis

        diagnosis = generate_diagnosis(
            run_id="run_memory",
            metadata={"agent_id": "agent", "framework": "openclaw"},
            session_json="session.json",
            events=[
                {
                    "event_type": "memory_event",
                    "timestamp": "2026-08-04T00:00:00+00:00",
                    "payload": {
                        "action": "retrieved",
                        "memory_id": "mem_a",
                        "score": 0.91,
                        "used": True,
                        "reason": "Referenced project currently under discussion.",
                    },
                },
                {
                    "event_type": "memory_event",
                    "timestamp": "2026-08-04T00:00:01+00:00",
                    "payload": {
                        "action": "retrieved",
                        "memory_id": "mem_b",
                        "score": 0.22,
                        "used": False,
                        "reason": "Similarity admitted an irrelevant candidate.",
                    },
                },
            ],
        )

        causes = diagnosis["failure_analysis"]["failure_causes"]
        self.assertIn("memory_utilization", {cause["type"] for cause in causes})
        memory = diagnosis["evidence_panel"]["memory_analysis"]
        self.assertEqual(memory["retrieved_count"], 2)
        self.assertEqual(memory["referenced_count"], 1)
        self.assertEqual(memory["unused_count"], 1)
        self.assertEqual(memory["irrelevant_count"], 1)
        self.assertTrue(memory["evidence"][0]["reason"])

    def test_backend_failure_falls_back_to_local_diagnosis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            session = create_session(runs_dir=tmp)
            with patch.dict("os.environ", {"CRITIQOR_BACKEND_URL": "https://unavailable.example", "CRITIQOR_BACKEND_REQUIRED": ""}, clear=False):
                with patch("critiqor.session.submit_evidence", side_effect=BackendResponseError("offline")):
                    finalized = finalize_session(tmp)
            self.assertEqual(finalized["status"], "COMPLETED")
            payload = json.loads((Path(tmp) / session["run_id"] / "diagnosis.json").read_text())
            self.assertEqual(payload["diagnosis_source"], "local")
            self.assertIn("offline", payload["diagnosis_fallback_reason"])

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
                        "executive_summary": {
                            "trust_score": 91,
                            "readiness_level": "review_recommended",
                        },
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
            with patch.dict("os.environ", {"CRITIQOR_BACKEND_URL": "https://backend.example"}, clear=False):
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

    def test_cli_help_is_public_client_focused(self) -> None:
        self.assertEqual(cli_main(["help"]), 0)

    def test_evidence_chain_detects_tampering_and_redacts_secrets(self) -> None:
        events = seal_events([
            {
                "event": "tool_call",
                "payload": {
                    "authorization": "Bearer secret-value",
                    "command": "safe",
                },
            },
            {"event": "tool_output", "payload": {"result": "ok"}},
        ])
        self.assertEqual(events[0]["payload"]["authorization"], "[REDACTED]")
        self.assertTrue(verify_events(events)["valid"])
        events[0]["payload"]["command"] = "forged"
        report = verify_events(events)
        self.assertFalse(report["valid"])
        self.assertEqual(report["status"], "tampered")

    def test_backend_rejects_malformed_trust_score(self) -> None:
        submission = EvidenceSubmission(
            run_id="run_001", metadata={}, session={}, events=[]
        )

        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *_args):
                return None
            def read(self):
                return json.dumps({
                    "run_id": "run_001",
                    "executive_summary": {
                        "trust_score": 1_000_000,
                        "readiness_level": "safe_to_deploy",
                    },
                }).encode()

        with patch("critiqor.backend.urlopen", return_value=Response()):
            with self.assertRaises(BackendResponseError):
                submit_evidence(submission, BackendConfig(url="https://backend.example"))

    def test_ed25519_manifest_signing_detects_mutation(self) -> None:
        keys = generate_ed25519_keypair()
        with patch.dict(
            "os.environ",
            {
                "CRITIQOR_SIGNING_PRIVATE_KEY": keys["private_key"],
                "CRITIQOR_SIGNING_PUBLIC_KEY": keys["public_key"],
            },
            clear=False,
        ):
            manifest = sign_manifest({"run_id": "run_001", "evidence_status": "verified"})
            self.assertEqual(manifest["signature"]["algorithm"], "ed25519")
            self.assertTrue(verify_manifest(manifest)["valid"])
            manifest["evidence_status"] = "tampered"
            self.assertFalse(verify_manifest(manifest)["valid"])

    def test_policy_enforces_risk_identity_integrity_and_signature(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            artifact = {
                "run_id": "run_001",
                "agent_id": "expected-agent",
                "executive_summary": {
                    "trust_score": 95,
                    "hallucination_risk": 5,
                    "readiness_level": "safe_to_deploy",
                },
            }
            artifact["evaluation_manifest"] = sign_manifest(
                {
                    "run_id": "run_001",
                    "agent_id": "expected-agent",
                    "evidence_status": "verified",
                    "diagnosis_digest": object_digest(artifact),
                },
                key="test-signing-key",
            )
            path = Path(tmp) / "diagnosis.json"
            path.write_text(json.dumps(artifact))
            with patch.dict("os.environ", {"CRITIQOR_SIGNING_KEY": "test-signing-key"}):
                self.assertEqual(
                    check_deployment_policy(
                        PolicyCheckOptions(
                            evaluations=str(path),
                            agent_id="expected-agent",
                            minimum_trust_score=90,
                            maximum_hallucination_risk=10,
                        )
                    ),
                    0,
                )
                artifact["executive_summary"]["hallucination_risk"] = 100
                path.write_text(json.dumps(artifact))
                self.assertEqual(
                    check_deployment_policy(
                        PolicyCheckOptions(
                            evaluations=str(path),
                            agent_id="expected-agent",
                            minimum_trust_score=90,
                            maximum_hallucination_risk=10,
                        )
                    ),
                    1,
                )


if __name__ == "__main__":
    unittest.main()
