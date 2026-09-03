"""Chrome DevTools Protocol observer for browser-native WebMCP activity."""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import time
from typing import Any, Callable, Iterable
from urllib.parse import urlparse
from urllib.request import urlopen

import websocket

from .session import append_event_to_run, create_session, paths_for, write_json


def _json(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def intent_fingerprint(origin: str, tool_name: str, value: Any) -> str:
    canonical = json.dumps(
        {"origin": origin, "tool": tool_name, "input": value},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _structured_output(value: Any) -> Any:
    if isinstance(value, dict):
        content = value.get("content")
        if isinstance(content, list) and content and isinstance(content[0], dict):
            return _json(content[0].get("text"))
    parsed = _json(value)
    if isinstance(parsed, dict) and "json" in parsed:
        return parsed.get("json")
    return parsed


def _cart_effect(value: Any) -> tuple[int, list[str]] | None:
    structured = _structured_output(value)
    if not isinstance(structured, dict) or not isinstance(structured.get("lines"), list):
        return None
    count = 0
    effect_ids: list[str] = []
    for line in structured["lines"]:
        if not isinstance(line, dict):
            continue
        quantity = line.get("quantity")
        if not isinstance(quantity, int) or quantity < 0:
            continue
        count += quantity
        identity = f"{line.get('slug', 'unknown')}:{line.get('color', 'default')}"
        effect_ids.extend(f"{identity}#{index}" for index in range(1, quantity + 1))
    return count, effect_ids


@dataclass
class BrowserObservationState:
    target_url: str
    task_id: str
    scenario_id: str
    consequential_tools: set[str] = field(default_factory=set)
    reconciliation_tools: set[str] = field(default_factory=set)
    authoritative_tools: set[str] = field(default_factory=set)
    epoch: int = 0
    tools: dict[str, dict[str, Any]] = field(default_factory=dict)
    invocations: dict[str, dict[str, Any]] = field(default_factory=dict)
    dispatch_count: int = 0
    injected_invocation_id: str | None = None
    last_ambiguous_invocation_id: str | None = None
    fault_count: int = 0
    peak_authoritative_effect_count: int = 0
    final_authoritative_effect_count: int | None = None
    pending_messages: list[dict[str, Any]] = field(default_factory=list)
    navigation_pending: bool = False

    @property
    def origin(self) -> str:
        parsed = urlparse(self.target_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def consequence(self, tool_name: str) -> str:
        if tool_name in self.consequential_tools:
            return "consequential"
        annotations = self.tools.get(tool_name, {}).get("annotations") or {}
        if annotations.get("consequential") is True:
            return "consequential"
        if annotations.get("readOnly") is True:
            return "read_only"
        return "unspecified"


def normalize_webmcp_event(
    method: str, params: dict[str, Any], state: BrowserObservationState
) -> list[tuple[str, dict[str, Any]]]:
    """Map one CDP WebMCP event to Critiqor's public evidence vocabulary."""

    base = {
        "source_layer": "chrome_cdp_webmcp",
        "payload": {
            "schema_version": "critiqor.webmcp.event.v1",
            "task_id": state.task_id,
            "scenario_id": state.scenario_id,
            "target_origin": state.origin,
        },
    }
    payload = base["payload"]

    if method == "WebMCP.toolsAdded":
        state.epoch += 1
        added = []
        for tool in params.get("tools") or []:
            if not isinstance(tool, dict) or not tool.get("name"):
                continue
            observed = {
                key: tool[key]
                for key in ("name", "description", "inputSchema", "outputSchema", "annotations")
                if key in tool
            }
            state.tools[str(tool["name"])] = observed
            added.append(observed)
        payload.update(
            {
                "epoch": state.epoch,
                "fresh": True,
                "reobserved": state.navigation_pending,
                "tools": added,
                "tool_names": sorted(state.tools),
                "message": f"Observed {len(state.tools)} registered WebMCP tool(s).",
            }
        )
        state.navigation_pending = False
        return [("webmcp.discovery", base)]

    if method == "WebMCP.toolsRemoved":
        state.epoch += 1
        removed = []
        for tool in params.get("tools") or []:
            name = str(tool.get("name") or "") if isinstance(tool, dict) else ""
            if name:
                state.tools.pop(name, None)
                removed.append(name)
        payload.update(
            {
                "epoch": state.epoch,
                "fresh": False,
                "removed_tools": removed,
                "tool_names": sorted(state.tools),
                "message": f"WebMCP registry changed; removed {len(removed)} tool(s).",
            }
        )
        return [("webmcp.discovery", base)]

    if method == "WebMCP.toolInvoked":
        tool_name = str(params.get("toolName") or "unknown")
        invocation_id = str(params.get("invocationId") or "")
        value = _json(params.get("input"))
        fingerprint = intent_fingerprint(state.origin, tool_name, value)
        state.dispatch_count += 1
        invocation = {
            "tool_name": tool_name,
            "operation_id": f"cdp:{invocation_id}",
            "intent_fingerprint": fingerprint,
            "input": value,
            "consequence_class": state.consequence(tool_name),
            "dispatch_ordinal": state.dispatch_count,
            "completed": False,
        }
        state.invocations[invocation_id] = invocation
        event_invocation = {key: value for key, value in invocation.items() if key != "completed"}
        payload.update(
            {
                "tool": {"namespace": "document.modelContext", "name": tool_name, "version": "experimental"},
                "intent": {"fingerprint": fingerprint, "normalization_version": "critiqor.webmcp.intent.v1"},
                **event_invocation,
                "collector_event_id": f"cdp:{invocation_id}:dispatch",
                "message": f"Chrome invoked WebMCP tool {tool_name}.",
            }
        )
        return [("webmcp.tool_dispatch", base)]

    if method == "WebMCP.toolResponded":
        invocation_id = str(params.get("invocationId") or "")
        invocation = state.invocations.get(invocation_id, {})
        status = str(params.get("status") or "Error")
        injected = invocation_id == state.injected_invocation_id
        outcome = "unknown" if injected else "succeeded" if status == "Completed" else "unknown"
        if invocation:
            invocation["completed"] = True
        payload.update(
            {
                "tool": {
                    "namespace": "document.modelContext",
                    "name": invocation.get("tool_name", "unknown"),
                    "version": "experimental",
                },
                "intent": {"fingerprint": invocation.get("intent_fingerprint", "")},
                "operation_id": invocation.get("operation_id", f"cdp:{invocation_id}"),
                "consequence_class": invocation.get("consequence_class", "unspecified"),
                "outcome": outcome,
                "browser_status": status,
                "output": params.get("output"),
                "error": params.get("errorText"),
                "collector_event_id": f"cdp:{invocation_id}:outcome",
                "message": f"Chrome reported {status} for {invocation.get('tool_name', 'WebMCP tool')}.",
            }
        )
        if injected:
            state.last_ambiguous_invocation_id = invocation_id
            payload.update(
                {
                    "ambiguity_cause": "lost_response",
                    "fault_injected": True,
                    "message": "The target response reached Chrome, then the configured response-stage fault hid it from the caller.",
                }
            )
        elif status == "Canceled":
            payload["ambiguity_cause"] = "cancellation"
        elif status == "Error" and invocation.get("consequence_class") != "read_only":
            payload["ambiguity_cause"] = "execution_error"
        events = [("webmcp.outcome", base)]
        cart_effect = _cart_effect(params.get("output"))
        tool_name = str(invocation.get("tool_name") or "unknown")
        if status == "Completed" and not injected and tool_name in state.authoritative_tools and cart_effect:
            effect_count, effect_ids = cart_effect
            state.peak_authoritative_effect_count = max(
                state.peak_authoritative_effect_count, effect_count
            )
            authority_payload = {
                "source_layer": "chrome_cdp_webmcp",
                "payload": {
                    "schema_version": "critiqor.webmcp.event.v1",
                    "task_id": state.task_id,
                    "scenario_id": state.scenario_id,
                    "target_origin": state.origin,
                    "operation_id": invocation.get("operation_id", f"cdp:{invocation_id}"),
                    "intent": {"fingerprint": invocation.get("intent_fingerprint", "")},
                    "authoritative_state": "committed" if effect_count else "not_committed",
                    "authoritative_effect_count": effect_count,
                    "authoritative_effect_ids": effect_ids,
                    "authority_source": tool_name,
                    "message": f"Target-owned {tool_name} response reported {effect_count} cart effect(s).",
                },
            }
            if tool_name in state.reconciliation_tools and state.last_ambiguous_invocation_id:
                ambiguous = state.invocations.get(state.last_ambiguous_invocation_id, {})
                reconciliation = {
                    "source_layer": "chrome_cdp_webmcp",
                    "payload": {
                        **authority_payload["payload"],
                        "operation_id": ambiguous.get("operation_id", ""),
                        "intent": {"fingerprint": ambiguous.get("intent_fingerprint", "")},
                        "diagnosis_action": "reconcile",
                        "reconciliation_tool": tool_name,
                    },
                }
                events.append(("webmcp.reconciliation", reconciliation))
                state.last_ambiguous_invocation_id = None
            events.append(("webmcp.authoritative_effect", authority_payload))
        return events

    if method == "Page.frameNavigated":
        frame = params.get("frame") if isinstance(params.get("frame"), dict) else {}
        if frame.get("parentId"):
            return []
        state.epoch += 1
        state.tools.clear()
        state.navigation_pending = True
        payload.update(
            {
                "epoch": state.epoch,
                "epoch_changed": True,
                "stale": True,
                "navigation_url": frame.get("url"),
                "message": "The top-level page navigated; prior WebMCP discovery is stale.",
            }
        )
        return [("webmcp.navigation", base)]

    return []


class CDPConnection:
    def __init__(self, websocket_url: str):
        self.socket = websocket.create_connection(
            websocket_url,
            timeout=1,
            suppress_origin=True,
        )
        self.next_id = 1

    def send(self, method: str, params: dict[str, Any] | None = None) -> int:
        message_id = self.next_id
        self.next_id += 1
        self.socket.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        return message_id

    def receive(self) -> dict[str, Any] | None:
        if hasattr(self, "_pending_messages") and self._pending_messages:
            return self._pending_messages.pop(0)
        try:
            value = self.socket.recv()
        except websocket.WebSocketTimeoutException:
            return None
        except (OSError, websocket.WebSocketException) as exc:
            raise RuntimeError(f"Chrome debugger connection failed: {exc}") from exc
        if not value:
            raise RuntimeError("Chrome closed the debugger connection.")
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Chrome sent an invalid debugger message.") from exc
        return parsed if isinstance(parsed, dict) else None

    def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout_seconds: float = 5,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Call one CDP method without losing interleaved protocol events."""

        message_id = self.send(method, params)
        events: list[dict[str, Any]] = []
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            message = self.receive()
            if message is None:
                continue
            if message.get("id") == message_id:
                error = message.get("error")
                if isinstance(error, dict):
                    detail = error.get("message") or error
                    raise RuntimeError(f"Chrome rejected {method}: {detail}")
                result = message.get("result")
                return (result if isinstance(result, dict) else {}, events)
            if "method" in message:
                events.append(message)
        raise RuntimeError(f"Chrome did not answer {method} within {timeout_seconds:g} seconds")

    def enable_domains(self, commands: Iterable[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
        """Enable observer domains and return events received during handshaking."""

        pending = {self.send(method, params): method for method, params in commands}
        events: list[dict[str, Any]] = []
        deadline = time.monotonic() + 5
        while pending:
            if time.monotonic() >= deadline:
                names = ", ".join(sorted(pending.values()))
                raise RuntimeError(f"Chrome did not acknowledge CDP domain setup within 5 seconds: {names}")
            message = self.receive()
            if message is None:
                continue
            message_id = message.get("id")
            if message_id in pending:
                method = pending.pop(message_id)
                error = message.get("error")
                if isinstance(error, dict):
                    detail = error.get("message") or error
                    raise RuntimeError(f"Chrome rejected {method}: {detail}")
                continue
            if "method" in message:
                events.append(message)
        return events

    def close(self) -> None:
        self.socket.close()


def _validated_http_url(value: str, label: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{label} must be an absolute http(s) URL.")
    if parsed.username or parsed.password:
        raise ValueError(f"{label} must not contain credentials.")
    return value


def discover_page(cdp_url: str, target_url: str) -> dict[str, Any]:
    cdp_url = _validated_http_url(cdp_url, "CDP endpoint")
    _validated_http_url(target_url, "Target URL")
    try:
        with urlopen(cdp_url.rstrip("/") + "/json/list", timeout=3) as response:
            targets = json.load(response)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Could not query the explicit Chrome remote-debugging endpoint. "
            "Start or authorize Chrome remote debugging, then pass its HTTP endpoint."
        ) from exc
    if not isinstance(targets, list):
        raise RuntimeError("Chrome /json/list response was not a target list.")
    candidates = [
        item
        for item in targets
        if item.get("type") == "page" and str(item.get("url") or "").startswith(target_url)
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one Chrome page starting with {target_url!r}; found {len(candidates)}."
        )
    if not candidates[0].get("webSocketDebuggerUrl"):
        raise RuntimeError("Selected Chrome page does not expose a debugger WebSocket URL.")
    return candidates[0]


@dataclass(frozen=True)
class WebMCPMonitorOptions:
    cdp_url: str
    target_url: str
    runs_dir: str
    task_id: str
    scenario_id: str
    consequential_tools: tuple[str, ...] = ()
    reconciliation_tools: tuple[str, ...] = ()
    authoritative_tools: tuple[str, ...] = ()
    fault_response_url: str | None = None
    fault_method: str = "POST"
    authoritative_state_url: str | None = None
    authoritative_state_tool: str | None = None
    allowed_api_origin: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    fault_tool: str | None = None


def _append_cdp_events(
    options: WebMCPMonitorOptions,
    run_id: str,
    state: BrowserObservationState,
    messages: Iterable[dict[str, Any]],
) -> None:
    for message in messages:
        method = str(message.get("method") or "")
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        for event_type, event in normalize_webmcp_event(method, params, state):
            append_event_to_run(options.runs_dir, run_id, event_type, event)


def _collector_authority_event(
    options: WebMCPMonitorOptions,
    state: BrowserObservationState,
    *,
    operation_id: str,
    fingerprint: str,
    authority_source: str,
    cart: tuple[int, list[str]],
    collector_only: bool,
    body_sha256: str,
) -> dict[str, Any]:
    effect_count, effect_ids = cart
    state.peak_authoritative_effect_count = max(state.peak_authoritative_effect_count, effect_count)
    return {
        "source_layer": "chrome_cdp_fetch" if collector_only else "chrome_cdp_runtime",
        "payload": {
            "schema_version": "critiqor.webmcp.event.v1",
            "task_id": options.task_id,
            "scenario_id": options.scenario_id,
            "target_origin": state.origin,
            "operation_id": operation_id,
            "intent": {"fingerprint": fingerprint},
            "authoritative_state": "committed" if effect_count else "not_committed",
            "authoritative_effect_count": effect_count,
            "authoritative_effect_ids": effect_ids,
            "authority_source": authority_source,
            "collector_only": collector_only,
            "response_body_sha256": body_sha256,
            "message": (
                f"Collector-only target response proved {effect_count} cart effect(s) before delivery loss."
                if authority_source == "add_to_cart_response_before_loss"
                else f"Independent post-agent target read reported {effect_count} cart effect(s)."
            ),
        },
    }


def _capture_final_cart(
    connection: CDPConnection,
    options: WebMCPMonitorOptions,
    state: BrowserObservationState,
    run_id: str,
) -> None:
    if not options.authoritative_state_tool:
        return
    frame_result, buffered = connection.call("Page.getFrameTree")
    _append_cdp_events(options, run_id, state, buffered)
    frame_tree = frame_result.get("frameTree") if isinstance(frame_result.get("frameTree"), dict) else {}
    frame = frame_tree.get("frame") if isinstance(frame_tree.get("frame"), dict) else {}
    frame_id = str(frame.get("id") or "")
    if not frame_id:
        raise RuntimeError("Chrome Page.getFrameTree did not return a root frame id.")

    command_id = connection.send(
        "WebMCP.invokeTool",
        {"frameId": frame_id, "toolName": options.authoritative_state_tool, "input": {}},
    )
    deadline = time.monotonic() + 10
    invocation_id = ""
    response_params: dict[str, Any] | None = None
    command_acknowledged = False
    while time.monotonic() < deadline:
        message = connection.receive()
        if message is None:
            continue
        if message.get("id") == command_id:
            command_acknowledged = True
            error = message.get("error")
            if isinstance(error, dict):
                raise RuntimeError(
                    f"Chrome rejected WebMCP.invokeTool: {error.get('message') or error}"
                )
            result = message.get("result") if isinstance(message.get("result"), dict) else {}
            invocation_id = str(result.get("invocationId") or invocation_id)
            continue
        method = str(message.get("method") or "")
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        if method == "WebMCP.toolInvoked" and params.get("toolName") == options.authoritative_state_tool:
            invocation_id = str(params.get("invocationId") or invocation_id)
            continue
        if method == "WebMCP.toolResponded":
            candidate = str(params.get("invocationId") or "")
            if not invocation_id or candidate == invocation_id:
                response_params = params
                invocation_id = candidate or invocation_id
                break
        _append_cdp_events(options, run_id, state, [message])

    if not command_acknowledged or response_params is None:
        raise RuntimeError("Harness-owned WebMCP state read did not produce a matching tool response.")
    status = str(response_params.get("status") or "Error")
    output = response_params.get("output")
    serialized = json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    cart = _cart_effect(output)
    append_event_to_run(
        options.runs_dir,
        run_id,
        "webmcp.harness_read",
        {
            "source_layer": "chrome_cdp_webmcp_harness",
            "payload": {
                "task_id": options.task_id,
                "scenario_id": options.scenario_id,
                "target_origin": state.origin,
                "frame_id": frame_id,
                "invocation_id": invocation_id,
                "tool_name": options.authoritative_state_tool,
                "browser_status": status,
                "response_body_sha256": digest,
                "collector_only": True,
                "message": "Harness invoked the target-owned WebMCP state tool after the agent stopped.",
            },
        },
    )
    if status != "Completed" or cart is None:
        append_event_to_run(
            options.runs_dir,
            run_id,
            "webmcp.measurement_error",
            {
                "source_layer": "chrome_cdp_runtime",
                "payload": {
                    "task_id": options.task_id,
                    "scenario_id": options.scenario_id,
                    "target_origin": state.origin,
                    "browser_status": status,
                    "response_body_sha256": digest,
                    "message": "Independent final cart read did not return a valid cart payload.",
                },
            },
        )
        return
    state.final_authoritative_effect_count = cart[0]
    append_event_to_run(
        options.runs_dir,
        run_id,
        "webmcp.authoritative_effect",
        _collector_authority_event(
            options,
            state,
            operation_id="collector:post-run-cart-read",
            fingerprint="collector:post-run-cart-read",
            authority_source="get_cart_post_run",
            cart=cart,
            collector_only=True,
            body_sha256=digest,
        ),
    )


def validate_monitor_options(options: WebMCPMonitorOptions) -> None:
    _validated_http_url(options.cdp_url, "CDP endpoint")
    _validated_http_url(options.target_url, "Target URL")
    if not options.task_id.strip() or not options.scenario_id.strip():
        raise ValueError("Task and scenario identifiers must not be empty.")
    if (
        options.authoritative_state_tool
        and options.authoritative_state_tool not in options.authoritative_tools
    ):
        raise ValueError(
            "Authoritative state tool must also be declared with --authoritative-tool."
        )
    target_origin = BrowserObservationState(
        options.target_url, options.task_id, options.scenario_id
    ).origin
    allowed_api_origin = target_origin
    if options.allowed_api_origin:
        _validated_http_url(options.allowed_api_origin, "Allowed API origin")
        parsed_api_origin = urlparse(options.allowed_api_origin)
        if parsed_api_origin.path not in {"", "/"} or parsed_api_origin.query or parsed_api_origin.fragment:
            raise ValueError("Allowed API origin must contain only scheme, host, and optional port.")
        allowed_api_origin = BrowserObservationState(
            options.allowed_api_origin, options.task_id, options.scenario_id
        ).origin
    if options.authoritative_state_url:
        _validated_http_url(options.authoritative_state_url, "Authoritative state URL")
        authority_origin = BrowserObservationState(
            options.authoritative_state_url, options.task_id, options.scenario_id
        ).origin
        if authority_origin != allowed_api_origin:
            raise ValueError("Authoritative state URL must use the explicitly allowed API origin.")
    if options.fault_response_url is None:
        if options.fault_tool:
            raise ValueError("--fault-tool requires --fault-response-url.")
        return
    _validated_http_url(options.fault_response_url, "Fault response URL")
    fault_origin = BrowserObservationState(
        options.fault_response_url, options.task_id, options.scenario_id
    ).origin
    if fault_origin != allowed_api_origin:
        raise ValueError("Fault response URL must use the explicitly allowed API origin.")
    if "*" in options.fault_response_url or "?" in options.fault_response_url:
        raise ValueError("Fault response URL must be exact; wildcard patterns are not allowed.")
    if not options.fault_tool:
        raise ValueError("--fault-tool is required with --fault-response-url.")
    if options.fault_tool not in options.consequential_tools:
        raise ValueError("--fault-tool must also be declared with --consequential-tool.")
    if not options.fault_method.strip():
        raise ValueError("Fault method must not be empty.")


def select_fault_invocation(
    params: dict[str, Any],
    state: BrowserObservationState,
    options: WebMCPMonitorOptions,
) -> str | None:
    """Select only an unambiguous exact tool/request response correlation."""

    if not options.fault_response_url or not options.fault_tool:
        return None
    request = params.get("request") if isinstance(params.get("request"), dict) else {}
    at_response = "responseStatusCode" in params or "responseErrorReason" in params
    if not at_response:
        return None
    if str(request.get("url") or "") != options.fault_response_url:
        return None
    if str(request.get("method") or "").upper() != options.fault_method.upper():
        return None
    active = [
        invocation_id
        for invocation_id, item in state.invocations.items()
        if item.get("tool_name") == options.fault_tool and not item.get("completed")
    ]
    # Fetch.requestPaused carries no WebMCP invocation id. If more than one
    # matching mutation is in flight, refusing the fault is safer than guessing.
    return active[0] if len(active) == 1 else None


def monitor_webmcp_browser(
    options: WebMCPMonitorOptions,
    *,
    on_ready: Callable[[str], None] | None = None,
) -> int:
    validate_monitor_options(options)
    target = discover_page(options.cdp_url, options.target_url)
    state = BrowserObservationState(
        target_url=options.target_url,
        task_id=options.task_id,
        scenario_id=options.scenario_id,
        consequential_tools=set(options.consequential_tools),
        reconciliation_tools=set(options.reconciliation_tools),
        authoritative_tools=set(options.authoritative_tools),
    )
    connection = CDPConnection(str(target["webSocketDebuggerUrl"]))
    commands: list[tuple[str, dict[str, Any]]] = [("WebMCP.enable", {}), ("Page.enable", {})]
    if options.fault_response_url:
        commands.append(
            (
                "Fetch.enable",
                {
                    "patterns": [
                        {
                            "urlPattern": options.fault_response_url,
                            "requestStage": "Response",
                        }
                    ]
                },
            )
        )
    try:
        initial_messages = connection.enable_domains(commands)
        session = create_session(
            runs_dir=options.runs_dir,
            agent_id="browser-webmcp-agent",
            framework="webmcp",
            benchmark_id="webmcp_runtime_v1",
            difficulty_tier="advanced",
        )
    except Exception:
        connection.close()
        raise
    run_id = str(session["run_id"])
    session["metadata"] = {
        **dict(session.get("metadata") or {}),
        **options.metadata,
        "browser_observer": {
            "protocol": "Chrome DevTools Protocol",
            "cdp_url": options.cdp_url,
            "target_url": options.target_url,
            "target_id": target.get("id"),
            "fault_response_url": options.fault_response_url,
            "fault_method": options.fault_method if options.fault_response_url else None,
            "fault_tool": options.fault_tool,
            "fault_cardinality": "exactly_once" if options.fault_response_url else None,
            "authoritative_state_url": options.authoritative_state_url,
            "allowed_api_origin": options.allowed_api_origin or state.origin,
        },
        "experiment": {
            "task_id": options.task_id,
            "scenario_id": options.scenario_id,
            "target_origin": state.origin,
            "injected_fault": bool(options.fault_response_url),
        },
    }
    write_json(paths_for(options.runs_dir).run_path(run_id), session)
    append_event_to_run(
        options.runs_dir,
        run_id,
        "webmcp.observer_ready",
        {
            "source_layer": "chrome_cdp_webmcp",
            "payload": {
                "task_id": options.task_id,
                "scenario_id": options.scenario_id,
                "target_origin": state.origin,
                "cdp_url": options.cdp_url,
                "target_id": target.get("id"),
                "message": "Chrome accepted the WebMCP observer domains; live collection is active.",
            },
        },
    )
    _append_cdp_events(options, run_id, state, initial_messages)
    if on_ready:
        on_ready(run_id)

    fault_used = False
    try:
        while True:
            message = connection.receive()
            if not message or "method" not in message:
                continue
            method = str(message["method"])
            params = message.get("params") if isinstance(message.get("params"), dict) else {}
            if method == "Fetch.requestPaused":
                request = params.get("request") if isinstance(params.get("request"), dict) else {}
                invocation_id = None if fault_used else select_fault_invocation(params, state, options)
                if invocation_id:
                    state.injected_invocation_id = invocation_id
                    body_result, buffered = connection.call(
                        "Fetch.getResponseBody", {"requestId": params["requestId"]}
                    )
                    _append_cdp_events(options, run_id, state, buffered)
                    body = str(body_result.get("body") or "")
                    if body_result.get("base64Encoded"):
                        import base64

                        body = base64.b64decode(body).decode("utf-8", errors="replace")
                    body_digest = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
                    cart = _cart_effect(body)
                    invocation = state.invocations[invocation_id]
                    if cart:
                        append_event_to_run(
                            options.runs_dir,
                            run_id,
                            "webmcp.authoritative_effect",
                            _collector_authority_event(
                                options,
                                state,
                                operation_id=str(invocation.get("operation_id") or ""),
                                fingerprint=str(invocation.get("intent_fingerprint") or ""),
                                authority_source="add_to_cart_response_before_loss",
                                cart=cart,
                                collector_only=True,
                                body_sha256=body_digest,
                            ),
                        )
                    append_event_to_run(
                        options.runs_dir,
                        run_id,
                        "webmcp.fault_injection",
                        {
                            "source_layer": "chrome_cdp_fetch",
                            "payload": {
                                "task_id": options.task_id,
                                "scenario_id": options.scenario_id,
                                "target_origin": state.origin,
                                "request_url": request.get("url"),
                                "request_method": request.get("method"),
                                "response_status": params.get("responseStatusCode"),
                                "response_body_sha256": body_digest,
                                "post_commit_proof": bool(cart),
                                "agent_received_response_body": False,
                                "fault_tool": options.fault_tool,
                                "operation_id": state.invocations[invocation_id]["operation_id"],
                                "correlation": "unique_pending_tool_and_exact_response",
                                "ambiguity_cause": "lost_response",
                                "message": "Failed exactly one matching request at Chrome's response stage.",
                            },
                        },
                    )
                    connection.send(
                        "Fetch.failRequest",
                        {"requestId": params["requestId"], "errorReason": "Aborted"},
                    )
                    fault_used = True
                    state.fault_count += 1
                else:
                    # continueRequest is the non-experimental continuation API
                    # and is valid for a request paused at either stage.
                    connection.send("Fetch.continueRequest", {"requestId": params["requestId"]})
                continue
            _append_cdp_events(options, run_id, state, [message])
    except KeyboardInterrupt:
        _capture_final_cart(connection, options, state, run_id)
        append_event_to_run(
            options.runs_dir,
            run_id,
            "webmcp.scenario_end",
            {
                "source_layer": "chrome_cdp_webmcp",
                "payload": {
                    "schema_version": "critiqor.webmcp.event.v1",
                    "task_id": options.task_id,
                    "scenario_id": options.scenario_id,
                    "target_origin": state.origin,
                    "completion_reason": "observer_stopped",
                    "fault_count": state.fault_count,
                    "fault_exactly_once": state.fault_count == 1,
                    "peak_authoritative_effect_count": state.peak_authoritative_effect_count,
                    "final_authoritative_effect_count": state.final_authoritative_effect_count,
                    "coverage_status": "exercised" if state.dispatch_count else "not_exercised",
                    "message": "WebMCP observation window closed after independent final-state capture.",
                },
            },
        )
        return 0
    finally:
        connection.close()
