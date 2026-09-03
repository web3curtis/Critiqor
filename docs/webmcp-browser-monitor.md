# WebMCP Chrome monitor

`critiqor monitor webmcp` observes Chrome's experimental WebMCP DevTools
Protocol domain in real time. It records tool registration, removal,
invocation, completion, navigation invalidation, reconciliation, and
target-owned authoritative state in the existing Critiqor run format.

## Chrome connection contract

Critiqor requires an explicit remote-debugging HTTP endpoint through
`--cdp-url` or `CRITIQOR_CDP_URL`. It queries `<endpoint>/json/list`, requires
exactly one page whose URL starts with `--target-url`, and attaches to that
page's `webSocketDebuggerUrl`.

It does not scan for or silently attach to arbitrary Chrome processes. Start a
dedicated Chrome profile with `--remote-debugging-port` and a non-default
`--user-data-dir`, or use Chrome's user-approved remote-debugging flow where
available. The Chrome build must expose the experimental `WebMCP` domain. The
monitor validates `WebMCP.enable`, `Page.enable`, and optional `Fetch.enable`
before it creates a Critiqor run.

The tip-of-tree CDP WebMCP domain is experimental and does not promise backward
compatibility. A Chrome rejection is therefore a startup error, not evidence
that the audited page has no WebMCP tools.

## Consequential outcome contract

A `Completed` response is recorded as succeeded unless it was hidden by the
configured response-stage fault. `Error`, `Canceled`, and injected lost-response
results for consequential or otherwise non-read-only tools remain `unknown`.
They are never interpreted as proof of non-commit.

After an ambiguous mutation, the safe workflow is:

1. invoke a configured reconciliation tool;
2. inspect target-owned authoritative state;
3. retry only if that state proves `not_committed`.

Critiqor binds the reconciliation event to the ambiguous operation and records
the authoritative effect separately. Repeated reconciliation reads are not
incorrectly rebound after the ambiguity has been resolved.

For the Crema experiment, `--authoritative-state-url` can name the exact
cart-read endpoint. On Ctrl-C, Critiqor performs that independent read before
closing CDP and records either the final cart effect or an explicit measurement
error. The endpoint must use the audited page origin by default. A split-origin
frontend/API deployment must explicitly allow the API origin with
`--allowed-api-origin`; the allowlist accepts an origin only, never a path.

## Controlled Crema fault

Fault injection is external to the page and uses CDP `Fetch` response-stage
interception. It requires all of these options:

- `--fault-response-url`: an exact absolute mutation URL; wildcards are rejected;
- `--fault-method`: the exact HTTP method, normally `POST`;
- `--fault-tool`: the WebMCP tool name, also declared consequential.
- `--allowed-api-origin`: required only when the exact API URL is on a different
  origin from the audited page.

The fault fires at most once per monitor process. Because CDP does not attach a
WebMCP invocation id to `Fetch.requestPaused`, the adapter fires only when the
exact response has exactly one pending invocation of the named tool. If two
matching Crema mutations overlap, it continues the response and refuses to
guess. This makes the injection deterministic without claiming a correlation
that Chrome did not provide.

The pinned Crema setup serves the audited page at `http://127.0.0.1:3000` and
its Wasp API at `http://localhost:3001`. It therefore binds `add_to_cart` to
`POST http://localhost:3001/operations/add-to-cart` and explicitly allows only
the `http://localhost:3001` API origin.

## Stopping and finalizing

Press Ctrl-C after the browser task. The run remains available to the normal
workflow:

```bash
critiqor finalize
```

Unexpected CDP disconnects are reported as monitor failures rather than being
silently treated as idle observation.
