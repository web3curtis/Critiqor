import { appendFileSync, mkdirSync, writeFileSync, existsSync, readFileSync, renameSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

const TIMELINE_EVENTS = [
  "agent_start",
  "agent_end",
  "turn_start",
  "turn_end",
  "session_start",
  "session_end",
  "before_provider_request",
  "after_provider_response",
  "message_received",
  "message_sent",
  "message_start",
  "message_update",
  "message_end",
  "input",
  "user_bash"
];

const TOOL_EVENTS = [
  "tool_call",
  "tool_result",
  "tool_execution_start",
  "tool_execution_update",
  "tool_execution_end"
];

const START_TIME_BY_TOOL_CALL = new Map();

function nowIso() {
  return new Date().toISOString();
}

function resolveRunsDir() {
  return path.resolve(process.env.CRITIQOR_RUNS_DIR || "runs");
}

function resolveRunId() {
  return process.env.CRITIQOR_RUN_ID || `openclaw_${Date.now()}`;
}

function resolveSessionPaths() {
  const runsDir = resolveRunsDir();
  const runId = resolveRunId();
  const sessionDir = path.join(runsDir, runId);
  return {
    runsDir,
    runId,
    sessionDir,
    sessionJson: path.join(sessionDir, "session.json"),
    eventsJsonl: path.join(sessionDir, "events.jsonl")
  };
}

function ensureSessionFile() {
  const paths = resolveSessionPaths();
  mkdirSync(paths.sessionDir, { recursive: true });
  if (!existsSync(paths.sessionJson)) {
    writeFileSync(
      paths.sessionJson,
      JSON.stringify(
        {
          session_id: paths.runId,
          run_id: paths.runId,
          schema_version: "critiqor.session.v1",
          created_at: nowIso(),
          events_file: "events.jsonl",
          metrics: {}
        },
        null,
        2
      ),
      "utf8"
    );
  }
  return paths;
}

function scrub(value, depth = 0) {
  if (depth > 8) return "[depth_limit]";
  if (value === undefined) return null;
  if (typeof value === "string") {
    return value
      .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]{8,}/gi, "[REDACTED]")
      .replace(/\bsk-[A-Za-z0-9_-]{12,}\b/g, "[REDACTED]")
      .slice(0, 32768);
  }
  if (value === null || typeof value === "number" || typeof value === "boolean") {
    return value;
  }
  if (Array.isArray(value)) return value.map((item) => scrub(item, depth + 1));
  if (typeof value === "object") {
    const out = {};
    for (const [key, item] of Object.entries(value)) {
      if (typeof item === "function") continue;
      if (/(authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|password|passwd|private[_-]?key|cookie|session[_-]?token)/i.test(key)) {
        out[key] = "[REDACTED]";
      } else {
        out[key] = scrub(item, depth + 1);
      }
    }
    return out;
  }
  return String(value);
}

function normalizeEvent(eventType, sourceLayer, event) {
  const payload = scrub(event);
  const toolCallId = payload?.toolCallId ?? payload?.tool_call_id ?? null;
  if (eventType === "tool_call" || eventType === "tool_execution_start") {
    if (toolCallId) START_TIME_BY_TOOL_CALL.set(toolCallId, Date.now());
  }

  const normalized = {
    timestamp: nowIso(),
    event_type: eventType,
    source_layer: sourceLayer,
    payload
  };

  if (sourceLayer === "tool_hooks") {
    const startedAt = toolCallId ? START_TIME_BY_TOOL_CALL.get(toolCallId) : null;
    normalized.tool_name = payload?.toolName ?? payload?.tool_name ?? null;
    normalized.tool_call_id = toolCallId;
    normalized.status = payload?.isError === true ? "error" : "ok";
    normalized.error = payload?.isError === true ? payload?.error ?? payload?.result ?? payload?.content ?? true : null;
    normalized.duration_ms = startedAt ? Math.max(0, Date.now() - startedAt) : null;
    if (eventType === "tool_result" || eventType === "tool_execution_end") {
      START_TIME_BY_TOOL_CALL.delete(toolCallId);
    }
  }

  return normalized;
}

function appendEvidence(eventType, sourceLayer, event) {
  const paths = ensureSessionFile();
  const normalized = normalizeEvent(eventType, sourceLayer, event);
  updateSessionSummary(paths, normalized);

  if (sourceLayer === "tool_hooks" && (normalized.tool_name === "memory_search" || normalized.tool_name === "memory_get")) {
    const memoryEvent = {
      ...normalized,
      event_type: normalized.tool_name,
      payload: {
        ...normalized.payload,
        observed_as: normalized.event_type
      }
    };
    updateSessionSummary(paths, memoryEvent);
  }
}

function updateSessionSummary(paths, event) {
  appendFileSync(paths.eventsJsonl, `${JSON.stringify(event)}\n`, { encoding: "utf8", flush: true });
  let session;
  try {
    session = JSON.parse(readFileSync(paths.sessionJson, "utf8"));
  } catch {
    session = {
      session_id: paths.runId,
      run_id: paths.runId,
      schema_version: "critiqor.session.v1",
      created_at: nowIso(),
      events_file: "events.jsonl",
      metrics: {}
    };
  }

  const metrics = session.metrics && typeof session.metrics === "object" ? session.metrics : {};
  metrics.total_events = Number(metrics.total_events || 0) + 1;
  metrics.by_event_type = metrics.by_event_type || {};
  metrics.by_event_type[event.event_type] = Number(metrics.by_event_type[event.event_type] || 0) + 1;
  metrics.by_source_layer = metrics.by_source_layer || {};
  metrics.by_source_layer[event.source_layer] = Number(metrics.by_source_layer[event.source_layer] || 0) + 1;
  if (event.status === "error") metrics.error_events = Number(metrics.error_events || 0) + 1;
  if (event.tool_name) {
    metrics.tool_calls = metrics.tool_calls || {};
    metrics.tool_calls[event.tool_name] = Number(metrics.tool_calls[event.tool_name] || 0) + 1;
  }

  session.metrics = metrics;
  session.updated_at = event.timestamp;
  session.events_file = "events.jsonl";
  delete session.events;
  const tempPath = `${paths.sessionJson}.tmp`;
  writeFileSync(tempPath, JSON.stringify(session, null, 2), "utf8");
  renameSync(tempPath, paths.sessionJson);
}

function safeSubscribe(api, eventType, sourceLayer) {
  try {
    api.on(eventType, async (event) => {
      appendEvidence(eventType, sourceLayer, event);
    });
  } catch {
    // Older OpenClaw builds may not expose every timeline alias. Unsupported
    // event names are intentionally ignored so the collector remains forward-
    // and backward-compatible.
  }
}

export default definePluginEntry({
  id: "critiqor",
  name: "Critiqor Evidence Collector",
  description: "Passive runtime evidence collection for OpenClaw agents.",
  register(api) {
    if (api.registrationMode && api.registrationMode !== "full") return;

    ensureSessionFile();

    for (const eventType of TIMELINE_EVENTS) safeSubscribe(api, eventType, "extension_api");
    for (const eventType of TOOL_EVENTS) safeSubscribe(api, eventType, "tool_hooks");
  }
});

export const __filename = fileURLToPath(import.meta.url);
