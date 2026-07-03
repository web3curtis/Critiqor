"""Tests for the public Critiqor client package."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from critiqor import EvidenceSubmission, OpenClawRuntimeObserver, create_session, finalize_session
from critiqor.backend import BackendConfig, submit_evidence
from critiqor.cli import main as cli_main
from critiqor.dashboard import validate_diagnosis


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

    def test_cli_help_is_public_client_focused(self) -> None:
        self.assertEqual(cli_main(["help"]), 0)


if __name__ == "__main__":
    unittest.main()
