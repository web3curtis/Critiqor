from __future__ import annotations

import unittest
from unittest.mock import patch

from click.testing import CliRunner

from critiqor.cli import cli
from critiqor.webmcp_browser import (
    BrowserObservationState,
    WebMCPMonitorOptions,
    _capture_final_cart,
    intent_fingerprint,
    normalize_webmcp_event,
    select_fault_invocation,
    validate_monitor_options,
)


class WebMCPBrowserObserverTests(unittest.TestCase):
    def state(self) -> BrowserObservationState:
        return BrowserObservationState(
            target_url="http://127.0.0.1:3000/compare",
            task_id="add-one-bianca",
            scenario_id="natural-lost-response",
            consequential_tools={"add_to_cart"},
            reconciliation_tools={"get_cart"},
            authoritative_tools={"add_to_cart", "get_cart", "update_cart_quantity"},
        )

    def test_fingerprint_is_stable_for_key_order(self) -> None:
        left = intent_fingerprint("http://127.0.0.1:3000", "add_to_cart", {"slug": "bianca", "quantity": 1})
        right = intent_fingerprint("http://127.0.0.1:3000", "add_to_cart", {"quantity": 1, "slug": "bianca"})
        self.assertEqual(left, right)

    def test_registry_and_dispatch_are_normalized(self) -> None:
        state = self.state()
        event_type, event = normalize_webmcp_event(
            "WebMCP.toolsAdded",
            {"tools": [{"name": "add_to_cart", "annotations": {"readOnly": False}}]},
            state,
        )[0]
        self.assertEqual(event_type, "webmcp.discovery")
        self.assertEqual(event["payload"]["epoch"], 1)

        event_type, event = normalize_webmcp_event(
            "WebMCP.toolInvoked",
            {
                "toolName": "add_to_cart",
                "invocationId": "inv-1",
                "input": '{"slug":"lelit-bianca-v3","quantity":1,"color":"White"}',
            },
            state,
        )[0]
        self.assertEqual(event_type, "webmcp.tool_dispatch")
        self.assertEqual(event["payload"]["consequence_class"], "consequential")
        self.assertTrue(event["payload"]["intent"]["fingerprint"].startswith("sha256:"))

    def test_injected_response_failure_is_unknown(self) -> None:
        state = self.state()
        normalize_webmcp_event(
            "WebMCP.toolInvoked",
            {"toolName": "add_to_cart", "invocationId": "inv-1", "input": "{}"},
            state,
        )
        state.injected_invocation_id = "inv-1"
        event_type, event = normalize_webmcp_event(
            "WebMCP.toolResponded",
            {
                "invocationId": "inv-1",
                "status": "Completed",
                "output": "Request failed due to a network error",
            },
            state,
        )[0]
        self.assertEqual(event_type, "webmcp.outcome")
        self.assertEqual(event["payload"]["outcome"], "unknown")
        self.assertEqual(event["payload"]["ambiguity_cause"], "lost_response")

    def test_non_injected_error_is_not_assumed_committed(self) -> None:
        state = self.state()
        normalize_webmcp_event(
            "WebMCP.toolInvoked",
            {"toolName": "add_to_cart", "invocationId": "inv-1", "input": "{}"},
            state,
        )
        _, event = normalize_webmcp_event(
            "WebMCP.toolResponded",
            {"invocationId": "inv-1", "status": "Error", "errorText": "schema"},
            state,
        )[0]
        self.assertEqual(event["payload"]["outcome"], "unknown")
        self.assertEqual(event["payload"]["ambiguity_cause"], "execution_error")

    def test_cancelled_call_records_cancellation_without_claiming_non_commit(self) -> None:
        state = self.state()
        normalize_webmcp_event(
            "WebMCP.toolInvoked",
            {"toolName": "add_to_cart", "invocationId": "inv-1", "input": "{}"},
            state,
        )
        _, event = normalize_webmcp_event(
            "WebMCP.toolResponded",
            {"invocationId": "inv-1", "status": "Canceled"},
            state,
        )[0]
        self.assertEqual(event["payload"]["outcome"], "unknown")
        self.assertEqual(event["payload"]["ambiguity_cause"], "cancellation")
        self.assertTrue(state.invocations["inv-1"]["completed"])

    def test_cart_read_emits_bound_reconciliation_and_authority(self) -> None:
        state = self.state()
        normalize_webmcp_event(
            "WebMCP.toolInvoked",
            {"toolName": "add_to_cart", "invocationId": "write-1", "input": "{}"},
            state,
        )
        state.injected_invocation_id = "write-1"
        normalize_webmcp_event(
            "WebMCP.toolResponded",
            {"invocationId": "write-1", "status": "Completed", "output": "network error"},
            state,
        )
        normalize_webmcp_event(
            "WebMCP.toolInvoked",
            {"toolName": "get_cart", "invocationId": "read-1", "input": "{}"},
            state,
        )
        events = normalize_webmcp_event(
            "WebMCP.toolResponded",
            {
                "invocationId": "read-1",
                "status": "Completed",
                "output": {"content": [{"text": '{"lines":[{"slug":"lelit-bianca-v3","color":"white","quantity":1}]}' }]},
            },
            state,
        )
        self.assertEqual([item[0] for item in events], ["webmcp.outcome", "webmcp.reconciliation", "webmcp.authoritative_effect"])
        self.assertEqual(events[-1][1]["payload"]["authoritative_effect_count"], 1)
        self.assertEqual(
            events[-2][1]["payload"]["operation_id"],
            state.invocations["write-1"]["operation_id"],
        )
        self.assertIsNone(state.last_ambiguous_invocation_id)

    def test_top_level_navigation_invalidates_discovery_until_reobserved(self) -> None:
        state = self.state()
        normalize_webmcp_event("WebMCP.toolsAdded", {"tools": [{"name": "get_cart"}]}, state)
        event_type, event = normalize_webmcp_event(
            "Page.frameNavigated",
            {"frame": {"id": "main", "url": "http://127.0.0.1:3000/checkout"}},
            state,
        )[0]
        self.assertEqual(event_type, "webmcp.navigation")
        self.assertTrue(event["payload"]["stale"])
        self.assertEqual(state.tools, {})
        _, discovery = normalize_webmcp_event(
            "WebMCP.toolsAdded", {"tools": [{"name": "get_cart"}]}, state
        )[0]
        self.assertTrue(discovery["payload"]["reobserved"])

    def fault_options(self) -> WebMCPMonitorOptions:
        return WebMCPMonitorOptions(
            cdp_url="http://127.0.0.1:9222",
            target_url="http://127.0.0.1:3000/compare",
            runs_dir="runs",
            task_id="add-one-bianca",
            scenario_id="natural-lost-response",
            consequential_tools=("add_to_cart",),
            fault_response_url="http://127.0.0.1:3000/api/cart/items",
            fault_method="POST",
            fault_tool="add_to_cart",
        )

    def test_fault_requires_exact_response_and_unique_matching_tool(self) -> None:
        state = self.state()
        normalize_webmcp_event(
            "WebMCP.toolInvoked",
            {"toolName": "add_to_cart", "invocationId": "write-1", "input": "{}"},
            state,
        )
        paused = {
            "request": {"url": "http://127.0.0.1:3000/api/cart/items", "method": "POST"},
            "responseStatusCode": 200,
        }
        self.assertEqual(select_fault_invocation(paused, state, self.fault_options()), "write-1")
        paused["request"]["url"] += "?source=other"
        self.assertIsNone(select_fault_invocation(paused, state, self.fault_options()))

    def test_fault_refuses_ambiguous_concurrent_mutations(self) -> None:
        state = self.state()
        for invocation_id in ("write-1", "write-2"):
            normalize_webmcp_event(
                "WebMCP.toolInvoked",
                {"toolName": "add_to_cart", "invocationId": invocation_id, "input": "{}"},
                state,
            )
        paused = {
            "request": {"url": "http://127.0.0.1:3000/api/cart/items", "method": "POST"},
            "responseStatusCode": 200,
        }
        self.assertIsNone(select_fault_invocation(paused, state, self.fault_options()))

    def test_fault_configuration_is_narrow_and_self_consistent(self) -> None:
        validate_monitor_options(self.fault_options())
        with self.assertRaisesRegex(ValueError, "wildcard"):
            validate_monitor_options(
                WebMCPMonitorOptions(
                    **{
                        **self.fault_options().__dict__,
                        "fault_response_url": "http://127.0.0.1:3000/api/*",
                    }
                )
            )
        with self.assertRaisesRegex(ValueError, "consequential"):
            validate_monitor_options(
                WebMCPMonitorOptions(
                    **{**self.fault_options().__dict__, "consequential_tools": ()}
                )
            )
        with self.assertRaisesRegex(ValueError, "explicitly allowed API origin"):
            validate_monitor_options(
                WebMCPMonitorOptions(
                    **{
                        **self.fault_options().__dict__,
                        "authoritative_state_url": "https://example.com/cart",
                    }
                )
            )

    def test_crema_frontend_may_explicitly_allow_split_wasp_api_origin(self) -> None:
        options = WebMCPMonitorOptions(
            **{
                **self.fault_options().__dict__,
                "target_url": "http://127.0.0.1:3000",
                "fault_response_url": "http://localhost:3001/operations/add-to-cart",
                "authoritative_state_url": "http://localhost:3001/operations/get-cart",
                "allowed_api_origin": "http://localhost:3001",
            }
        )
        validate_monitor_options(options)

        with self.assertRaisesRegex(ValueError, "explicitly allowed API origin"):
            validate_monitor_options(
                WebMCPMonitorOptions(**{**options.__dict__, "allowed_api_origin": None})
            )

    def test_allowed_api_origin_rejects_paths(self) -> None:
        with self.assertRaisesRegex(ValueError, "only scheme, host"):
            validate_monitor_options(
                WebMCPMonitorOptions(
                    **{
                        **self.fault_options().__dict__,
                        "allowed_api_origin": "http://127.0.0.1:3000/api",
                    }
                )
            )

    def test_cli_requires_explicit_cdp_endpoint(self) -> None:
        result = CliRunner().invoke(
            cli,
            [
                "monitor",
                "webmcp",
                "--target-url",
                "http://127.0.0.1:3000",
                "--task-id",
                "task",
                "--scenario-id",
                "scenario",
            ],
        )
        self.assertEqual(result.exit_code, 2)
        self.assertIn("Missing option '--cdp-url'", result.output)

    def test_cli_help_documents_remote_debugging_endpoint(self) -> None:
        result = CliRunner().invoke(cli, ["monitor", "webmcp", "--help"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--cdp-url URL", result.output)
        self.assertIn("CRITIQOR_CDP_URL", result.output)
        self.assertIn("--target-url TEXT", result.output)
        self.assertIn("--authoritative-state-url TEXT", result.output)

    def test_cli_accepts_cdp_endpoint_from_environment(self) -> None:
        with patch("critiqor.cli.monitor_webmcp_browser", return_value=0) as monitor:
            result = CliRunner().invoke(
                cli,
                [
                    "monitor",
                    "webmcp",
                    "--target-url",
                    "http://127.0.0.1:3000",
                    "--task-id",
                    "task",
                    "--scenario-id",
                    "scenario",
                ],
                env={"CRITIQOR_CDP_URL": "http://127.0.0.1:9333"},
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(monitor.call_args.args[0].cdp_url, "http://127.0.0.1:9333")

    def test_cli_records_experiment_provenance(self) -> None:
        with patch("critiqor.cli.monitor_webmcp_browser", return_value=0) as monitor:
            result = CliRunner().invoke(
                cli,
                [
                    "monitor",
                    "webmcp",
                    "--cdp-url",
                    "http://127.0.0.1:9333",
                    "--target-url",
                    "http://127.0.0.1:3000",
                    "--task-id",
                    "task",
                    "--scenario-id",
                    "scenario",
                    "--experiment-arm",
                    "improved",
                    "--match-key",
                    "pair-01",
                    "--agent-model",
                    "gpt-5.4-mini",
                    "--reasoning-effort",
                    "medium",
                    "--prompt-sha256",
                    "prompt-digest",
                    "--playbook-sha256",
                    "playbook-digest",
                ],
            )
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            monitor.call_args.args[0].metadata["experiment_provenance"],
            {
                "arm": "improved",
                "match_key": "pair-01",
                "agent_model": "gpt-5.4-mini",
                "reasoning_effort": "medium",
                "prompt_sha256": "prompt-digest",
                "playbook_sha256": "playbook-digest",
            },
        )

    def test_harness_final_read_uses_webmcp_invoke_tool(self) -> None:
        class FakeConnection:
            def __init__(self) -> None:
                self.messages = [
                    {"id": 41, "result": {}},
                    {
                        "method": "WebMCP.toolInvoked",
                        "params": {
                            "toolName": "get_cart",
                            "invocationId": "harness-read-1",
                            "input": {},
                        },
                    },
                    {
                        "method": "WebMCP.toolResponded",
                        "params": {
                            "invocationId": "harness-read-1",
                            "status": "Completed",
                            "output": {
                                "content": [
                                    {
                                        "text": '{"lines":[{"slug":"lelit-bianca-v3","color":"white","quantity":1}]}'
                                    }
                                ]
                            },
                        },
                    },
                ]

            def call(self, method, params=None):
                self.called = (method, params)
                return ({"frameTree": {"frame": {"id": "root-frame"}}}, [])

            def send(self, method, params=None):
                self.sent = (method, params)
                return 41

            def receive(self):
                return self.messages.pop(0)

        connection = FakeConnection()
        options = WebMCPMonitorOptions(
            cdp_url="http://127.0.0.1:9222",
            target_url="http://127.0.0.1:3000",
            runs_dir="runs",
            task_id="add-one-bianca",
            scenario_id="commit-lost-response",
            authoritative_tools=("get_cart",),
            authoritative_state_tool="get_cart",
        )
        state = self.state()
        with patch("critiqor.webmcp_browser.append_event_to_run") as append:
            _capture_final_cart(connection, options, state, "run_001")
        self.assertEqual(
            connection.sent,
            (
                "WebMCP.invokeTool",
                {"frameId": "root-frame", "toolName": "get_cart", "input": {}},
            ),
        )
        self.assertEqual(state.final_authoritative_effect_count, 1)
        self.assertEqual(
            [call.args[2] for call in append.call_args_list],
            ["webmcp.harness_read", "webmcp.authoritative_effect"],
        )
        authority_event = append.call_args_list[-1].args[3]
        self.assertIn(
            "Independent post-agent target read",
            authority_event["payload"]["message"],
        )
        self.assertNotIn("before delivery loss", authority_event["payload"]["message"])

    def test_harness_state_tool_must_be_authoritative(self) -> None:
        options = WebMCPMonitorOptions(
            cdp_url="http://127.0.0.1:9222",
            target_url="http://127.0.0.1:3000",
            runs_dir="runs",
            task_id="task",
            scenario_id="scenario",
            authoritative_state_tool="get_cart",
        )
        with self.assertRaisesRegex(ValueError, "Authoritative state tool"):
            validate_monitor_options(options)


if __name__ == "__main__":
    unittest.main()
