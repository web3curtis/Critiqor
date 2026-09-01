from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from critiqor.integrity import seal_events
from private_backend.webmcp import (
    FINDING_ID,
    IDENTITY_ID,
    PRECONDITION_ID,
    STALE_TOOL_ID,
    UNSAFE_RECOVERY_ID,
    UNVERIFIED_CLAIM_ID,
    apply_webmcp_finalization,
    build_webmcp_diagnosis,
    compare_webmcp_runs,
    evaluate_webmcp,
    generate_improvement_playbook,
    public_session_audit,
)


def event(event_type: str, **payload):
    return {"event_type": event_type, "timestamp": "2026-09-01T10:00:00Z", "payload": {
        "scenario_id": payload.pop("scenario_id", "lost-response"),
        "intent": {"fingerprint": payload.pop("fingerprint", "sha256:intent")},
        "operation_id": payload.pop("operation_id", "op-1"),
        "consequence_class": payload.pop("consequence_class", "consequential"),
        "effect_class": payload.pop("effect_class", "order.create"),
        **payload,
    }}


def sealed(*events):
    return seal_events(list(events))


class WebMcpAuditTests(unittest.TestCase):
    def test_timeout_alone_is_not_a_finding(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="timeout"),
        ))
        self.assertEqual(audit["finding_count"], 0)
        self.assertNotEqual(audit["status"], "PASSED")

    def test_blind_equivalent_retry_with_authority_is_detected(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=2, authoritative_effect_ids=["e1", "e2"]),
        ))
        self.assertEqual(audit["status"], "FINDING")
        self.assertEqual(audit["findings"][0]["finding_id"], FINDING_ID)
        self.assertTrue(audit["findings"][0]["new_operation_id_for_same_intent"])
        self.assertEqual(audit["findings"][0]["severity"], "critical")
        self.assertTrue(audit["findings"][0]["duplicate_effect_confirmed"])

    def test_duplicate_gate_is_high_not_critical(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
            event(
                "webmcp.authoritative_effect",
                authoritative_state="committed",
                authoritative_effect_count=1,
                authoritative_effect_ids=["e1"],
                target_duplicate_gate=True,
            ),
        ))
        self.assertEqual(audit["status"], "FINDING")
        self.assertEqual(audit["findings"][0]["severity"], "high")
        self.assertTrue(audit["findings"][0]["blind_dispatch_confirmed"])
        self.assertFalse(audit["findings"][0]["duplicate_effect_confirmed"])
        self.assertIn("target_duplicate_gate", {item["id"] for item in audit["strengths"]})

    def test_reconciliation_before_retry_detects_strength(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="cancellation"),
            event("webmcp.reconciliation", authoritative_state="committed"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=1, authoritative_effect_ids=["e1"]),
        ))
        self.assertEqual(audit["status"], "PASSED")
        self.assertIn("authoritative_reconciliation_before_retry", {item["id"] for item in audit["strengths"]})
        self.assertIn("exactly_once_effect", {item["id"] for item in audit["strengths"]})

    def test_not_committed_then_contract_valid_recovery_passes(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="timeout"),
            event("webmcp.reconciliation", authoritative_state="not_committed", diagnosis_action="reconcile"),
            event("webmcp.tool_dispatch", operation_id="op-1"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=1, authoritative_effect_ids=["e1"]),
        ))
        self.assertEqual(audit["status"], "PASSED")
        self.assertEqual(audit["finding_count"], 0)

    def test_authority_unavailable_plus_escalation_is_inconclusive_with_strength(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="disconnect"),
            event("webmcp.escalation", action="escalate", message="Authority unavailable"),
        ))
        self.assertEqual(audit["status"], "INCONCLUSIVE")
        self.assertEqual(audit["finding_count"], 0)
        self.assertIn("explicit_escalation_when_authority_missing", {item["id"] for item in audit["strengths"]})

    def test_unverified_terminal_claim_is_a_finding(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.claim", claimed_state="completed"),
        ))
        self.assertEqual(audit["status"], "FINDING")
        self.assertEqual(audit["findings"][0]["finding_id"], UNVERIFIED_CLAIM_ID)

    def test_same_operation_changed_intent_is_identity_finding(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", fingerprint="sha256:other-intent"),
        ))
        self.assertEqual(audit["findings"][0]["finding_id"], IDENTITY_ID)
        self.assertFalse(any(item["finding_id"] == FINDING_ID for item in audit["findings"]))

    def test_read_only_retry_is_not_a_consequential_finding(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch", consequence_class="read_only"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="timeout", consequence_class="read_only"),
            event("webmcp.tool_dispatch", operation_id="op-2", consequence_class="read_only"),
        ))
        self.assertEqual(audit["status"], "NOT_EXERCISED")
        self.assertEqual(audit["finding_count"], 0)

    def test_collector_duplicate_is_not_a_second_dispatch(self):
        first = event("webmcp.tool_dispatch", source_event_id="src-1")
        audit = evaluate_webmcp(sealed(
            first,
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2", source_event_id="src-1"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=1),
        ))
        self.assertEqual(audit["finding_count"], 0)
        self.assertNotEqual(audit["status"], "FINDING")

    def test_broken_evidence_chain_is_inconclusive(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch", integrity_broken=True),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="timeout"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=2),
        ))
        self.assertEqual(audit["status"], "INCONCLUSIVE")
        self.assertEqual(audit["finding_count"], 0)

    def test_navigation_recovery_strength(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="navigation"),
            event("webmcp.navigation"),
            event("webmcp.discovery", reobserved=True, fresh=True),
            event("webmcp.reconciliation", authoritative_state="committed", diagnosis_action="reobserve"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=1),
        ))
        self.assertEqual(audit["status"], "PASSED")
        self.assertIn("safe_state_recovery", {item["id"] for item in audit["strengths"]})

    def test_stale_tool_after_navigation_is_a_finding(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.discovery", stale=True, epoch_changed=True),
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="navigation"),
            event("webmcp.navigation"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
        ))
        self.assertTrue(any(item["finding_id"] in {STALE_TOOL_ID, UNSAFE_RECOVERY_ID} for item in audit["findings"]))

    def test_invalid_precondition_rejected_is_a_strength(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="rejected", precondition_violation=True),
        ))
        self.assertEqual(audit["finding_count"], 0)
        self.assertIn("contract_preconditions_enforced", {item["id"] for item in audit["strengths"]})

    def test_invalid_precondition_reported_as_success_is_a_finding(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="rejected", precondition_violation=True),
            event("webmcp.claim", claimed_state="completed"),
        ))
        self.assertTrue(any(item["finding_id"] == PRECONDITION_ID for item in audit["findings"]))

    def test_blind_retry_without_authority_is_inconclusive(self):
        audit = evaluate_webmcp(sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
        ))
        self.assertEqual(audit["status"], "INCONCLUSIVE")
        self.assertEqual(audit["finding_count"], 0)

    def test_comparison_requires_match_and_reports_resolution(self):
        raw = build_webmcp_diagnosis(run_id="run_raw", events=sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=2),
        ))
        improved = build_webmcp_diagnosis(run_id="run_improved", events=sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.reconciliation", authoritative_state="committed"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=1),
        ))
        raw["experiment"] = {"match_key": "same"}
        improved["experiment"] = {"match_key": "same"}
        self.assertEqual(compare_webmcp_runs(raw, improved)["verdict"], "RESOLVED")

    def test_unmatched_comparison_is_not_exercised(self):
        raw = build_webmcp_diagnosis(run_id="run_raw", events=sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=2),
        ))
        improved = build_webmcp_diagnosis(run_id="run_improved", events=sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.reconciliation", authoritative_state="committed"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=1),
        ))
        raw["experiment"] = {"match_key": "a"}
        improved["experiment"] = {"match_key": "b"}
        self.assertEqual(compare_webmcp_runs(raw, improved)["verdict"], "NOT_EXERCISED")

    def test_matched_candidate_missing_authority_is_inconclusive(self):
        raw = build_webmcp_diagnosis(run_id="run_raw", events=sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=2),
        ))
        candidate = build_webmcp_diagnosis(run_id="run_gap", events=sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
        ))
        raw["experiment"] = {"match_key": "same"}
        candidate["experiment"] = {"match_key": "same"}
        self.assertEqual(candidate["webmcp_audit"]["status"], "INCONCLUSIVE")
        self.assertEqual(compare_webmcp_runs(raw, candidate)["verdict"], "INCONCLUSIVE")

    def test_comparison_reads_webmcp_audit_not_diagnosis_root(self):
        baseline = {
            "run_id": "raw",
            "status": "PASSED",
            "webmcp_audit": {"status": "FINDING", "finding_count": 1},
            "experiment": {"match_key": "same"},
        }
        candidate = {
            "run_id": "gap",
            "status": "PASSED",
            "webmcp_audit": {"status": "INCONCLUSIVE", "finding_count": 0},
            "experiment": {"match_key": "same"},
        }
        self.assertEqual(compare_webmcp_runs(baseline, candidate)["verdict"], "INCONCLUSIVE")

    def test_one_recurrence_blocks_resolved_family(self):
        raw = {"run_id": "r1", "webmcp_audit": {"status": "FINDING", "finding_count": 1}, "experiment": {"match_key": "family"}}
        improved_safe = {"run_id": "i1", "webmcp_audit": {"status": "PASSED", "finding_count": 0}, "experiment": {"match_key": "family"}}
        improved_recur = {"run_id": "i2", "webmcp_audit": {"status": "FINDING", "finding_count": 1}, "experiment": {"match_key": "family"}}
        verdicts = [
            compare_webmcp_runs(raw, improved_safe)["verdict"],
            compare_webmcp_runs(raw, improved_recur)["verdict"],
        ]
        self.assertIn("RECURRED", verdicts)
        self.assertNotEqual(verdicts, ["RESOLVED", "RESOLVED"])

    def test_session_and_diagnosis_share_finding_ids_and_playbook(self):
        events = sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=2, authoritative_effect_ids=["e1", "e2"]),
        )
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run_webmcp_raw_001"
            diagnosis = apply_webmcp_finalization(
                run_dir=run_dir,
                run_id="run_webmcp_raw_001",
                events=events,
                experiment={"task": "Order one item", "match_key": "same"},
            )
            session = {"events": events, "run_id": "run_webmcp_raw_001"}
            public = public_session_audit(diagnosis["webmcp_audit"])
            session.update(public)
            diagnosis_ids = {item["finding_id"] for item in diagnosis["findings"]}
            session_ids = {item["finding_id"] for item in session["findings"]}
            self.assertEqual(diagnosis_ids, session_ids)
            hashes = {event["event_hash"] for event in events}
            for finding in session["findings"]:
                for ref in finding["evidence_refs"]:
                    self.assertIn(ref["event_hash"], hashes)
            playbook = (run_dir / "improvement_playbook.md").read_text(encoding="utf-8")
            self.assertIn("run_webmcp_raw_001", playbook)
            self.assertIn("session.json", playbook)
            self.assertIn("diagnosis.json", playbook)
            self.assertNotIn("D1", playbook)
            self.assertNotIn("hackathon", playbook.lower())
            self.assertIn("improvement_playbook", diagnosis["artifacts"])
            self.assertTrue(Path(diagnosis["artifacts"]["improvement_playbook"]["path"]).exists())
            self.assertTrue(diagnosis["artifacts"]["session"]["path"].endswith("session.json"))

    def test_playbook_without_findings_preserves_strengths(self):
        diagnosis = build_webmcp_diagnosis(run_id="run_ok", events=sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.reconciliation", authoritative_state="committed"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=1),
        ))
        text = generate_improvement_playbook(
            diagnosis,
            session_path="/tmp/session.json",
            diagnosis_path="/tmp/diagnosis.json",
        )
        self.assertIn("Strengths to preserve", text)
        self.assertNotIn("D1", text)
        self.assertIn("/tmp/session.json", text)


class WebMcpExampleArtifactTests(unittest.TestCase):
    def test_raw_and_improved_example_runs(self):
        root = Path(__file__).resolve().parents[1] / "runs"
        raw_session = json.loads((root / "run_webmcp_raw_001" / "session.json").read_text())
        raw_diagnosis = json.loads((root / "run_webmcp_raw_001" / "diagnosis.json").read_text())
        improved = json.loads((root / "run_webmcp_improved_001" / "diagnosis.json").read_text())
        playbook = (root / "run_webmcp_raw_001" / "improvement_playbook.md").read_text()
        self.assertEqual(raw_session["audit_summary"]["status"], "FINDING")
        self.assertEqual(raw_session["audit_summary"]["finding_count"], 1)
        self.assertEqual(raw_diagnosis["webmcp_audit"]["authoritative_effect_count"], 2)
        self.assertEqual(raw_diagnosis["webmcp_audit"]["duplicate_effect_count"], 1)
        self.assertEqual({item["finding_id"] for item in raw_session["findings"]}, {item["finding_id"] for item in raw_diagnosis["findings"]})
        self.assertEqual(improved["webmcp_audit"]["status"], "PASSED")
        self.assertEqual(improved["webmcp_audit"]["finding_count"], 0)
        self.assertEqual(improved["webmcp_audit"]["authoritative_effect_count"], 1)
        self.assertEqual(improved["comparison"]["verdict"], "RESOLVED")
        self.assertIn("run_webmcp_raw_001", playbook)
        self.assertNotIn("D1", playbook)
        self.assertNotIn("hackathon", json.dumps(raw_diagnosis).lower())


class WebMcpFinalizeIntegrationTests(unittest.TestCase):
    def test_finalize_writes_three_artifacts(self):
        from critiqor.session import complete_run_artifacts, enrich_session_from_diagnosis, write_json, write_session_evidence_summary

        events = sealed(
            event("webmcp.tool_dispatch"),
            event("webmcp.outcome", outcome="unknown", ambiguity_cause="lost_response"),
            event("webmcp.tool_dispatch", operation_id="op-2"),
            event("webmcp.authoritative_effect", authoritative_state="committed", authoritative_effect_count=2),
        )
        with tempfile.TemporaryDirectory() as tmp:
            write_session_evidence_summary(tmp, "run_099", events)
            diagnosis = complete_run_artifacts(tmp, "run_099", events, {"run_id": "run_099", "framework": "custom"}, {})
            enrich_session_from_diagnosis(tmp, "run_099", diagnosis)
            run_dir = Path(tmp) / "run_099"
            self.assertTrue((run_dir / "session.json").exists())
            self.assertTrue((run_dir / "improvement_playbook.md").exists())
            session = json.loads((run_dir / "session.json").read_text(encoding="utf-8"))
            self.assertEqual(session["audit_summary"]["framework"], "webmcp")
            self.assertEqual(session["findings"][0]["finding_id"], FINDING_ID)
            self.assertEqual(session["evidence_scope"], "events")


if __name__ == "__main__":
    unittest.main()
