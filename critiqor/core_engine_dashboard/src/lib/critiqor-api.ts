import type {
  AgentHealth,
  ArtifactMetadata,
  Benchmark,
  Diagnosis,
  DiagnosisEvidence,
  EvidenceEvent,
  EvidenceSummary,
  ExecutiveSummary,
  RuntimeTimelineItem,
  Run,
  ScoreExplanation,
  Severity,
  State,
  TrustLevel,
  MemoryAnalysis,
  MemoryEvidenceItem,
  WebMcpAudit,
} from "./critiqor-store";
import { emptyState } from "./critiqor-store";

type Json = Record<string, unknown>;

type DashboardRunView = Json & {
  run_id?: string;
  agent_id?: string;
  framework?: string;
  visibility?: string;
  executive_summary?: Json;
  primary_diagnosis?: Json;
  cost_analysis?: Json;
  failure_analysis?: Json;
  evidence_panel?: Json;
};

const asRecord = (value: unknown): Json =>
  value && typeof value === "object" && !Array.isArray(value) ? (value as Json) : {};
const asArray = (value: unknown): unknown[] => (Array.isArray(value) ? value : []);
const asString = (value: unknown, fallback = "") => (value == null ? fallback : String(value));
const asNumber = (value: unknown, fallback = 0) => {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
};

export function frameworkDisplayName(value: unknown) {
  const framework = asString(value, "agent").trim();
  const known: Record<string, string> = {
    codex: "Codex",
    openclaw: "OpenClaw",
    webmcp: "WebMCP",
    "claude-code": "Claude Code",
    claude_code: "Claude Code",
  };
  const normalized = framework.toLowerCase();
  return (
    known[normalized] ??
    framework
      .split(/[-_\s]+/)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ")
  );
}

export function resolveCritiqorApiBase() {
  if (typeof window === "undefined") return "";
  const url = new URL(window.location.href);
  const queryBase = url.searchParams.get("critiqor_api") ?? url.searchParams.get("api");
  if (queryBase) {
    window.localStorage.setItem("critiqor_api_base", queryBase.replace(/\/$/, ""));
    return queryBase.replace(/\/$/, "");
  }
  return (
    window.localStorage.getItem("critiqor_api_base") ??
    import.meta.env.VITE_CRITIQOR_API_URL ??
    ""
  ).replace(/\/$/, "");
}

export async function fetchCritiqorRuns(
  apiBase = resolveCritiqorApiBase(),
  selectedRunId = resolveSelectedRunId(),
) {
  try {
    const response = await fetch(`${apiBase}/api/runs`, {
      credentials: apiBase ? "omit" : "same-origin",
      headers:
        typeof window !== "undefined" && window.sessionStorage.getItem("critiqor_access_credential")
          ? {
              authorization: `Bearer ${window.sessionStorage.getItem("critiqor_access_credential")}`,
            }
          : {},
    });
    if (!response.ok) throw new Error(`Critiqor API returned ${response.status}`);
    const payload = await response.json();
    const runs = Array.isArray(payload) ? payload : asArray(payload.runs);
    return normalizeDashboardRuns(runs as DashboardRunView[], apiBase, selectedRunId);
  } catch (error) {
    if (import.meta.env.DEV) return developmentFallbackState(apiBase, error);
    throw error;
  }
}

export function resolveSelectedRunId() {
  if (typeof window === "undefined") return "";
  const url = new URL(window.location.href);
  return url.searchParams.get("run_id") ?? url.searchParams.get("run") ?? "";
}

function orderRuns(rawRuns: DashboardRunView[], selectedRunId = "") {
  const sorted = [...rawRuns].sort((a, b) => runTimestamp(b).localeCompare(runTimestamp(a)));
  if (!selectedRunId) return sorted;
  const selected = sorted.find((run) => asString(run.run_id) === selectedRunId);
  if (!selected) return sorted;
  return [selected, ...sorted.filter((run) => asString(run.run_id) !== selectedRunId)];
}

export async function ingestCritiqorRun(payload: unknown, apiBase = resolveCritiqorApiBase()) {
  const response = await fetch(`${apiBase}/api/runs/ingest`, {
    method: "POST",
    credentials: apiBase ? "omit" : "same-origin",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Critiqor ingest returned ${response.status}`);
  return response.json();
}

export function normalizeDashboardRuns(
  rawRuns: DashboardRunView[],
  apiBase = "",
  selectedRunId = "",
): State {
  const state = emptyState();
  if (!rawRuns.length) {
    return {
      ...state,
      sync: { loading: false, source: "empty", lastUpdated: new Date().toISOString(), apiBase },
    };
  }

  const ordered = orderRuns(rawRuns, selectedRunId);
  const selected = selectedRunId
    ? rawRuns.find((run) => asString(run.run_id) === selectedRunId)
    : ordered[0];
  if (selectedRunId && !selected) {
    const empty = emptyState();
    return {
      ...empty,
      runs: ordered.map(toRun),
      sync: { loading: false, source: "empty", lastUpdated: new Date().toISOString(), apiBase },
      executive: {
        ...empty.executive,
        runId: selectedRunId,
        summary: "The selected run was not found. Another run was not substituted.",
        confidenceReasoning: "More evidence needed",
      },
    };
  }
  const runs = ordered.map(toRun);
  const diagnoses = ordered.flatMap(toDiagnoses);
  const evidence = ordered.flatMap(toEvidence).slice(0, 500);
  const benchmarks = toBenchmarks(ordered);
  const active = selected ?? ordered[0];
  const artifact = artifactMetadata(active);
  const executive = toExecutive(active, artifact);

  return {
    runs,
    diagnoses,
    evidence,
    benchmarks,
    executive,
    scoreExplanations: scoreExplanations(active, artifact),
    agentHealth: agentHealth(active, diagnoses, artifact),
    timeline: runtimeTimeline(active),
    artifact,
    memoryAnalysis: toMemoryAnalysis(active),
    webmcp: toWebMcpAudit(active),
    sync: { loading: false, source: "live", lastUpdated: new Date().toISOString(), apiBase },
  };
}

function toWebMcpAudit(run: DashboardRunView): WebMcpAudit {
  const raw = asRecord(run.webmcp_audit);
  const comparison = asRecord(run.comparison);
  if (!Object.keys(raw).length) return emptyState().webmcp;
  const matched = comparison.matched === true || Boolean(comparison.match_key);
  return {
    available: true,
    status: asString(raw.status) || "INCONCLUSIVE",
    displayStatus: asString(raw.display_status) || "More evidence needed",
    summary: asString(raw.summary) || "More evidence needed",
    scenariosExercised: presentNumber(raw.scenarios_exercised),
    findingCount: presentNumber(raw.finding_count),
    duplicateEffectCount: presentNumber(raw.duplicate_effect_count),
    authoritativeEffectCount: presentNumber(raw.authoritative_effect_count),
    blindRedispatchCount:
      raw.blind_redispatch_count == null ? undefined : presentNumber(raw.blind_redispatch_count),
    confidence: asString(raw.confidence) || undefined,
    strengths: asArray(raw.strengths).map((item) => {
      const strength = asRecord(item);
      return {
        id: asString(strength.id),
        title: asString(strength.title) || "Not captured",
        detail: asString(strength.detail),
      };
    }),
    comparison: matched ? asString(comparison.verdict) || undefined : undefined,
  };
}

function presentNumber(value: unknown) {
  return value == null || value === "" ? 0 : asNumber(value, 0);
}

function toMemoryAnalysis(run: DashboardRunView): MemoryAnalysis | undefined {
  const raw = asRecord(asRecord(run.evidence_panel).memory_analysis);
  if (!Object.keys(raw).length) return undefined;
  return {
    score: asNumber(raw.score, 100),
    confidence: asNumber(raw.confidence, 0),
    eventCount: asNumber(raw.event_count, 0),
    retrievedCount: asNumber(raw.retrieved_count, 0),
    injectedCount: asNumber(raw.injected_count, 0),
    referencedCount: asNumber(raw.referenced_count, 0),
    unusedCount: asNumber(raw.unused_count, 0),
    irrelevantCount: asNumber(raw.irrelevant_count, 0),
    missedCount: asNumber(raw.missed_count, 0),
    createdCount: asNumber(raw.created_count, 0),
    ignoredCount: asNumber(raw.ignored_count, 0),
    tokenCost: asNumber(raw.token_cost, 0),
    diagnosticSummary: asString(raw.diagnostic_summary, "Memory runtime behavior was captured."),
    architectureStage: asString(raw.architecture_stage, "memory retrieval"),
    evidence: asArray(raw.evidence).map(toMemoryEvidenceItem),
  };
}

function toMemoryEvidenceItem(item: unknown): MemoryEvidenceItem {
  const record = asRecord(item);
  return {
    eventType: asString(record.event_type, "memory_event"),
    action: asString(record.action, "observed"),
    message: asString(record.message, "Memory runtime event captured."),
    memoryId: asString(record.memory_id, ""),
    reason: asString(record.reason, "Critiqor captured this as a memory-related runtime event."),
    architectureStage: asString(record.architecture_stage, "memory retrieval"),
    confidence: record.confidence == null ? undefined : asString(record.confidence),
  };
}

function evidenceSummary(
  run: DashboardRunView,
  artifact = artifactMetadata(run),
): EvidenceSummary[] {
  const failureAnalysis = asRecord(run.failure_analysis);
  const causes = asArray(failureAnalysis.failure_causes);
  const retrievalEvents = traceEvents(run).filter((event) =>
    /retriev|memory|search/i.test(
      asString(
        event.event ?? event.event_type ?? event.type ?? event.tool_name ?? event.tool ?? "",
      ),
    ),
  );
  const memory = toMemoryAnalysis(run);
  const repeatedTools = repeatedToolCalls(run);
  return [
    {
      label: "Runtime events",
      value: String(artifact.eventCount),
      detail: `${artifact.eventCount} observed events support this report.`,
    },
    {
      label: "Tool calls",
      value: String(artifact.toolCallCount),
      detail: `${artifact.toolCallCount} tool calls and ${artifact.toolOutputCount} tool outputs were captured.`,
    },
    {
      label: "Ignored outputs",
      value: String(ignoredOutputCount(run)),
      detail: "Outputs marked unused or skipped contribute to synthesis risk.",
    },
    {
      label: "Repeated requests",
      value: String(repeatedTools),
      detail: "Repeated tool calls indicate possible loop or cost pressure.",
    },
    {
      label: "Retrieval utilisation",
      value: String(memory?.referencedCount || retrievalEvents.length),
      detail: memory?.eventCount
        ? `${memory.referencedCount} referenced, ${memory.unusedCount + memory.irrelevantCount} unused or irrelevant, ${memory.missedCount} missed.`
        : `${retrievalEvents.length} retrieval or memory related events were observed.`,
    },
    {
      label: "Failures observed",
      value: String(Math.max(artifact.failureCount, causes.length)),
      detail: "Failure causes come from Critiqor diagnosis artifacts and runtime error events.",
    },
    {
      label: "Runtime duration",
      value: `${(artifact.durationMs / 1000).toFixed(1)}s`,
      detail: "Duration is estimated from the first and last runtime event timestamps.",
    },
  ];
}

function scoreExplanations(run: DashboardRunView, artifact: ArtifactMetadata): ScoreExplanation[] {
  const summary = asRecord(run.executive_summary);
  const trust = presentNumber(summary.trust_score);
  const confidence = presentNumber(summary.evaluation_confidence ?? run.evaluation_confidence);
  const failures = Math.max(
    artifact.failureCount,
    asArray(asRecord(run.failure_analysis).failure_causes).length,
  );
  const memory = toMemoryAnalysis(run);
  const explanations = [
    {
      score: "Trust Score",
      value: `${trust}/100`,
      tier: scoreTier(trust),
      why: `The trust score reflects runtime evidence quality, failure impact, and observed execution stability. ${failures ? `${failures} failure signal(s) reduced the score.` : "No major failure signals were detected."}`,
      evidence: evidenceSummary(run, artifact).slice(0, 6),
    },
    {
      score: "Evaluation Confidence",
      value: `${confidence}%`,
      tier: scoreTier(confidence),
      why: confidenceReasoning(run, artifact, confidence),
      evidence: evidenceSummary(run, artifact).filter((item) =>
        ["Runtime events", "Tool calls", "Failures observed"].includes(item.label),
      ),
    },
    {
      score: "Operational Stability",
      value: `${Math.max(0, 100 - repeatedToolCalls(run) * 8 - ignoredOutputCount(run) * 6)}/100`,
      tier: scoreTier(Math.max(0, 100 - repeatedToolCalls(run) * 8 - ignoredOutputCount(run) * 6)),
      why: "This score is derived from duplicate actions, ignored tool outputs, runtime errors, and evidence utilisation.",
      evidence: evidenceSummary(run, artifact).filter((item) =>
        ["Ignored outputs", "Repeated requests", "Runtime duration"].includes(item.label),
      ),
    },
  ];
  if (memory?.eventCount) {
    explanations.push({
      score: "Memory Utilization",
      value: `${memory.score}/100`,
      tier: scoreTier(memory.score),
      why: `${memory.diagnosticSummary} Critiqor scored memory from runtime lookup, context injection, and response-use evidence.`,
      evidence: [
        {
          label: "Retrieved",
          value: String(memory.retrievedCount),
          detail: "Memory candidates observed during runtime lookup.",
        },
        {
          label: "Referenced",
          value: String(memory.referencedCount),
          detail: "Retrieved memories supported by response or reasoning evidence.",
        },
        {
          label: "Unused or irrelevant",
          value: String(memory.unusedCount + memory.irrelevantCount),
          detail: "Memories retrieved or injected without supported runtime use.",
        },
      ],
    });
  }
  return explanations;
}

function confidenceReasoning(
  run: DashboardRunView,
  artifact: ArtifactMetadata,
  confidence: number,
) {
  const evidenceLevel = asString(
    asRecord(run.executive_summary).evidence_level ?? run.evidence_level,
    "trace_available",
  );
  const coverage =
    artifact.toolCallCount || artifact.eventCount
      ? "runtime instrumentation captured observable activity"
      : "limited runtime activity was captured";
  return `${confidence}% confidence because evidence level is ${evidenceLevel}, ${artifact.eventCount} runtime events were collected, ${artifact.toolCallCount} tool execution(s) were observed, and ${coverage}.`;
}

function agentHealth(
  run: DashboardRunView,
  diagnoses: Diagnosis[],
  artifact: ArtifactMetadata,
): AgentHealth {
  const webmcp = toWebMcpAudit(run);
  const failures = diagnoses.filter((d) => d.runId === asString(run.run_id) && d.findingId).length;
  const stable = webmcp.available
    ? webmcp.status === "PASSED"
    : failures === 0 || asNumber(asRecord(run.executive_summary).trust_score, 0) >= 85;
  const strengths = webmcp.strengths.map((item) => item.title).filter(Boolean);
  return {
    status: stable ? "Healthy execution profile" : "Needs reliability review",
    strengths: strengths.length
      ? strengths
      : artifact.eventCount
        ? ["Runtime evidence was captured"]
        : ["Not captured"],
    stableBehaviours: [
      artifact.toolCallCount
        ? `${artifact.toolCallCount} tool call(s) captured with ${artifact.toolOutputCount} output event(s).`
        : "No excessive tool activity was observed.",
      ignoredOutputCount(run) === 0
        ? "No ignored tool output signal dominated the run."
        : `${ignoredOutputCount(run)} ignored output signal(s) require review.`,
      repeatedToolCalls(run) === 0
        ? "No repeated API/tool request loop was detected."
        : `${repeatedToolCalls(run)} repeated request pattern(s) were detected.`,
    ],
    recommendedMonitoring: [
      "Track ignored tool outputs across future runs",
      "Watch repeated tool/API calls for loop risk",
      "Compare trust score against bronze, silver, and gold tiers over time",
    ],
  };
}

function artifactMetadata(run: DashboardRunView): ArtifactMetadata {
  const raw = asRecord(run.raw_evidence);
  const artifacts = asRecord(run.artifacts);
  const artifactPayloads = asRecord(run.artifact_payloads);
  const sessionPayload = asRecord(artifactPayloads.session_json);
  const integrity = asRecord(sessionPayload.integrity);
  const manifest = asRecord(run.evaluation_manifest);
  const signature = asRecord(manifest.signature);
  const trace = traceEvents(run);
  const toolCalls = trace.filter((event) =>
    ["tool_call", "webmcp.tool_dispatch"].includes(eventName(event)),
  );
  const toolOutputs = trace.filter((event) =>
    ["tool_output", "tool_result", "webmcp.outcome", "webmcp.reconciliation"].includes(
      eventName(event),
    ),
  );
  const memoryEvents = trace.filter((event) =>
    ["memory_event", "memory_search", "memory_get"].includes(eventName(event)),
  );
  const failureEvents = trace.filter((event) =>
    ["error_event", "failure", "timeout"].includes(eventName(event)),
  );
  const start = trace[0] ? Date.parse(asString(trace[0].timestamp ?? trace[0].at, "")) : Number.NaN;
  const endEvent = trace.at(-1);
  const end = endEvent ? Date.parse(asString(endEvent.timestamp ?? endEvent.at, "")) : Number.NaN;
  const integrityStatus = asString(integrity.status ?? manifest.evidence_status, "unknown");
  const evidenceStatus: ArtifactMetadata["evidenceStatus"] =
    integrityStatus === "verified"
      ? signature.algorithm === "hmac-sha256"
        ? "verified"
        : "unsigned"
      : integrityStatus === "tampered"
        ? "tampered"
        : integrityStatus === "incomplete"
          ? "incomplete"
          : "unknown";
  return {
    diagnosisPath:
      asString(asRecord(artifacts.diagnosis).path) || asString(raw.diagnosis_json) || undefined,
    sessionPath:
      asString(asRecord(artifacts.session).path) || asString(raw.session_json) || undefined,
    playbookPath:
      asString(asRecord(artifacts.improvement_playbook).path) ||
      asString(raw.improvement_playbook) ||
      undefined,
    playbookContent:
      typeof artifactPayloads.improvement_playbook === "string"
        ? artifactPayloads.improvement_playbook
        : undefined,
    eventCount: trace.length,
    toolCallCount: toolCalls.length,
    toolOutputCount: toolOutputs.length,
    memoryEventCount: memoryEvents.length,
    failureCount: failureEvents.length,
    durationMs: Number.isFinite(start) && Number.isFinite(end) ? Math.max(0, end - start) : 0,
    evidenceStatus,
    evidenceDigest: asString(sessionPayload.evidence_digest ?? manifest.evidence_digest, ""),
    redactionCount: asNumber(integrity.redaction_count, 0),
    truncationCount: asNumber(integrity.truncation_count, 0),
    integrityErrors: asArray(integrity.errors)
      .map((error) => asString(error))
      .filter(Boolean),
  };
}

function runtimeTimeline(run: DashboardRunView): RuntimeTimelineItem[] {
  const trace = traceEvents(run);
  if (!trace.length) return [];
  return trace.slice(0, 80).map((event, index) => {
    const type = eventName(event);
    const tool = asString(event.tool_name ?? event.tool ?? asRecord(event.payload).toolName, "");
    return {
      id: `${asString(run.run_id, "run")}_timeline_${index}`,
      label: titleize(type),
      at: asString(event.timestamp ?? event.at, runTimestamp(run)),
      detail: asString(event.message ?? event.summary, tool ? `${type} · ${tool}` : type),
      type,
    };
  });
}

function traceEvents(run: DashboardRunView) {
  return asArray(asRecord(run.evidence_panel).trace).map(asRecord);
}

function eventName(event: Json) {
  return asString(event.event ?? event.event_type ?? event.type, "log");
}

function ignoredOutputCount(run: DashboardRunView) {
  return traceEvents(run).filter((event) => {
    const text = JSON.stringify(event).toLowerCase();
    return text.includes("ignored") || text.includes('"used":false') || text.includes("not used");
  }).length;
}

function repeatedToolCalls(run: DashboardRunView) {
  const counts = new Map<string, number>();
  for (const event of traceEvents(run)) {
    if (eventName(event) !== "tool_call") continue;
    const key = `${asString(event.tool_name ?? event.tool ?? asRecord(event.payload).toolName, "tool")}::${JSON.stringify(event.args ?? asRecord(event.payload).args ?? asRecord(event.payload).input ?? {})}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.values()]
    .filter((count) => count > 1)
    .reduce((sum, count) => sum + count - 1, 0);
}

function scoreTier(score: number) {
  if (score >= 90) return "Gold tier";
  if (score >= 75) return "Silver tier";
  return "Bronze tier";
}

function runTimestamp(run: DashboardRunView) {
  const trace = asArray(asRecord(run.evidence_panel).trace).map(asRecord);
  const first = trace.find((event) => event.timestamp || event.at);
  return asString(first?.timestamp ?? first?.at ?? run.timestamp ?? "1970-01-01T00:00:00.000Z");
}

function trustLevel(score: number): TrustLevel {
  if (score >= 85) return "high";
  if (score >= 65) return "medium";
  return "low";
}

function severityFromImpact(impact: number): Severity {
  if (impact >= 24) return "critical";
  if (impact >= 16) return "high";
  if (impact >= 8) return "medium";
  if (impact > 0) return "low";
  return "info";
}

function readinessLabel(value: unknown) {
  const readiness = asString(value, "review_recommended");
  return readiness
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function toExecutive(run: DashboardRunView, artifact: ArtifactMetadata): ExecutiveSummary {
  const summary = asRecord(run.executive_summary);
  const primary = asRecord(run.primary_diagnosis);
  const webmcp = toWebMcpAudit(run);
  const score = presentNumber(summary.trust_score);
  const level = trustLevel(score);
  const runId = asString(run.run_id) || "Not available";
  const framework = run.framework ? frameworkDisplayName(run.framework) : "Not captured";
  const task =
    asString(asRecord(run.experiment).task) ||
    asString(primary.title) ||
    asString(primary.root_cause_failure_type) ||
    "Not captured";
  const chain =
    asString(summary.summary) ||
    asString(primary.description) ||
    asString(primary.causal_chain_explanation) ||
    "More evidence needed";
  const nextAction = asString(primary.recommended_next_action);
  const evidence = evidenceSummary(run, artifact);
  const confidence = presentNumber(summary.evaluation_confidence ?? run.evaluation_confidence);
  return {
    trustScore: score,
    confidence,
    verdict: summary.readiness_level
      ? readinessLabel(summary.readiness_level)
      : "More evidence needed",
    summary: nextAction ? `${chain} Recommended next action: ${nextAction}` : chain,
    runId,
    agent: framework,
    task,
    generatedAt: runTimestamp(run),
    trustLevel: webmcp.status === "FINDING" ? "low" : webmcp.status === "PASSED" ? "high" : level,
    evidence,
    confidenceReasoning:
      asString(summary.confidence_label) ||
      asString(webmcp.confidence) ||
      confidenceReasoning(run, artifact, confidence),
  };
}

function toRun(run: DashboardRunView): Run {
  const summary = asRecord(run.executive_summary);
  const score = asNumber(summary.trust_score, 0);
  const status: Run["status"] = score >= 85 ? "passed" : "failed";
  const trace = asArray(asRecord(run.evidence_panel).trace).map(asRecord);
  const start = runTimestamp(run);
  const end = asString(trace.at(-1)?.timestamp ?? trace.at(-1)?.at ?? start, start);
  const ignored = ignoredOutputCount(run);
  const repeated = repeatedToolCalls(run);
  const toolCalls = trace.filter((event) => eventName(event) === "tool_call").length;
  const toolOutputs = trace.filter((event) =>
    ["tool_output", "tool_result"].includes(eventName(event)),
  ).length;
  const failures = trace.filter((event) =>
    ["error_event", "failure", "timeout"].includes(eventName(event)),
  ).length;
  const revisions = trace.filter((event) =>
    /retry|revision|replan|strategy_change/i.test(eventName(event)),
  ).length;
  const webmcp = toWebMcpAudit(run);
  return {
    id: asString(run.run_id, "unknown_run"),
    name: `${asString(run.agent_id, "OpenClaw agent")} runtime run`,
    status,
    startedAt: start,
    durationMs: Math.max(0, new Date(end).getTime() - new Date(start).getTime()),
    model: asString(run.framework, "openclaw"),
    trustScore: score,
    hallucinationRisk: Math.min(100, Math.max(0, 100 - score + ignored * 6)),
    toolReliability: toolCalls
      ? Math.max(
          0,
          Math.min(
            100,
            Math.round((Math.min(toolCalls, toolOutputs) / toolCalls) * 100) -
              failures * 8 -
              repeated * 5,
          ),
        )
      : failures
        ? 0
        : 100,
    reasoningConsistency: Math.max(
      0,
      Math.min(100, 100 - revisions * 8 - repeated * 6 - failures * 10),
    ),
    webmcpStatus: webmcp.available ? webmcp.displayStatus : undefined,
    webmcpFindings: webmcp.available ? webmcp.findingCount : undefined,
    webmcpEffects: webmcp.available ? webmcp.authoritativeEffectCount : undefined,
    webmcpComparison: webmcp.comparison,
  };
}

function toDiagnoses(run: DashboardRunView): Diagnosis[] {
  const runId = asString(run.run_id) || "Not available";
  const failureAnalysis = asRecord(run.failure_analysis);
  const primary = asRecord(run.primary_diagnosis);
  const causes = asArray(failureAnalysis.failure_causes).map(asRecord);
  if (!causes.length && asString(primary.title)) {
    causes.push(primary);
  }
  return causes.map((cause, index) => {
    const impact = cause.impact == null ? 0 : Math.abs(asNumber(cause.impact, 0));
    const severity = normalizeSeverity(
      cause.severity,
      impact ? severityFromImpact(impact) : "info",
    );
    const evidence = evidenceFromCause(run, cause, index);
    return {
      id: `${runId}_dx_${index + 1}`,
      runId,
      findingId: asString(cause.finding_id) || undefined,
      title: asString(cause.title ?? cause.display_name) || "Not captured",
      severity,
      summary:
        asString(cause.description) ||
        asString(primary.causal_chain_explanation) ||
        "More evidence needed",
      createdAt: runTimestamp(run),
      trustImpact: impact,
      rootCause: asString(cause.root_cause ?? primary.root_cause_failure_type) || "Not captured",
      recommendedInvestigation: recommendationsFor(asString(cause.type), cause, run),
      verificationSteps: asArray(cause.verification_steps)
        .map((item) => asString(item))
        .filter(Boolean),
      expectedImprovement: asString(cause.expected_improvement) || "Not captured",
      causalChain: asArray(cause.causal_chain)
        .map((item) => asString(item))
        .filter(Boolean),
      confidence: asString(cause.confidence) || undefined,
      confirmedImpact: asString(cause.confirmed_impact) || undefined,
      potentialImpact: asString(cause.potential_impact) || undefined,
      evidence,
      counterEvidence: asArray(cause.counter_evidence).map((item, i) => {
        const event = evidenceItem(item, `${runId}_counter_${index}_${i}`, runId);
        return { ...event, type: evidenceType(event.type) };
      }),
      alternativeHypotheses: asArray(cause.alternative_hypotheses)
        .map((item) => asString(item))
        .filter(Boolean),
      engineeringExplanation: asString(cause.engineering_explanation, ""),
      teachingDiagram: teachingDiagramFromCause(cause),
      memoryAnalysis:
        cause.type === "memory_utilization" ? toMemoryAnalysisFromCause(cause, run) : undefined,
      graph: graphFromRun(run),
    } satisfies Diagnosis;
  });
}

function toMemoryAnalysisFromCause(cause: Json, run: DashboardRunView) {
  const raw = asRecord(cause.memory_analysis);
  if (!Object.keys(raw).length) return toMemoryAnalysis(run);
  return toMemoryAnalysis({ ...run, evidence_panel: { memory_analysis: raw } });
}

function teachingDiagramFromCause(cause: Json) {
  const diagram = asRecord(cause.teaching_diagram);
  const stages = asArray(diagram.stages)
    .map((item) => asString(item))
    .filter(Boolean);
  if (!stages.length) return undefined;
  return {
    stages,
    highlight: asString(diagram.highlight, stages[0]),
  };
}

function normalizeSeverity(value: unknown, fallback: Severity): Severity {
  const text = asString(value).toLowerCase();
  return ["info", "low", "medium", "high", "critical"].includes(text)
    ? (text as Severity)
    : fallback;
}

function evidenceFromCause(run: DashboardRunView, cause: Json, index: number): DiagnosisEvidence[] {
  const runId = asString(run.run_id) || "Not available";
  const explicit = [...asArray(cause.evidence), ...asArray(cause.evidence_refs)];
  if (!explicit.length) return [];
  return explicit.map((item, i) => {
    const event = evidenceItem(item, `${runId}_cause_${index}_${i}`, runId);
    return { ...event, type: evidenceType(event.type) };
  });
}

function toEvidence(run: DashboardRunView): EvidenceEvent[] {
  const runId = asString(run.run_id, "unknown_run");
  const trace = asArray(asRecord(run.evidence_panel).trace);
  return trace.map((item, index) => evidenceItem(item, `${runId}_ev_${index}`, runId));
}

function evidenceItem(item: unknown, id: string, runId: string): EvidenceEvent {
  const event = asRecord(item);
  const type = asString(event.event ?? event.event_type ?? event.type, "log");
  const payload = asRecord(event.payload);
  const tool = asString(event.tool ?? event.tool_name ?? event.name ?? payload.toolName, "");
  const memoryReason = asString(payload.reason, "");
  const memoryAction = asString(payload.action ?? payload.operation ?? payload.status, "");
  const message = asString(
    event.message ?? event.label ?? event.summary,
    type === "memory_event" && memoryReason
      ? `Memory ${memoryAction || "observed"}: ${memoryReason}`
      : tool
        ? `${type}: ${tool}`
        : type,
  );
  return {
    id,
    runId,
    type,
    message,
    at: asString(event.timestamp ?? event.at, new Date().toISOString()),
    payload: event,
  };
}

function evidenceType(type: string): DiagnosisEvidence["type"] {
  if (type === "tool_call") return "tool_call";
  if (type === "tool_output") return "tool_output";
  if (type === "memory_event" || type === "memory") return "memory";
  if (type === "retry_event" || type === "retry") return "retry";
  if (type === "token_usage") return "metric";
  if (type === "context_event") return "context";
  if (type === "failure" || type === "diagnosis") return "judge";
  return "log";
}

function graphFromRun(run: DashboardRunView): Diagnosis["graph"] | undefined {
  const graph = asRecord(asRecord(run.evidence_panel).causal_graph);
  const nodes = asArray(graph.nodes)
    .map(asRecord)
    .map((node, index) => ({
      id: asString(node.id, `node_${index}`),
      label: asString(node.label ?? node.type, `Step ${index + 1}`),
      kind: asString(node.kind ?? node.type, "event"),
    }));
  const edges = asArray(graph.edges)
    .map(asRecord)
    .map((edge, index) => ({
      id: asString(edge.id, `edge_${index}`),
      source: asString(edge.source ?? edge.from, ""),
      target: asString(edge.target ?? edge.to, ""),
      label: asString(edge.label ?? edge.relation, ""),
    }))
    .filter((edge) => edge.source && edge.target);
  return nodes.length ? { nodes, edges } : undefined;
}

function toBenchmarks(runs: DashboardRunView[]): Benchmark[] {
  return runs.slice(0, 8).map((run) => {
    const summary = asRecord(run.executive_summary);
    const score = asNumber(summary.trust_score, 0);
    return {
      id: `${asString(run.run_id, "run")}_trust`,
      name: `${asString(run.agent_id, "OpenClaw")} trust score`,
      metric: "trust_score",
      target: 85,
      actual: score,
      unit: "pts",
      passed: score >= 85,
      updatedAt: runTimestamp(run),
    };
  });
}

function recommendationsFor(_type: string, cause: Json = {}, run: DashboardRunView = {}) {
  return [
    ...asArray(cause.recommendations),
    cause.recommendation,
    ...asArray(run.recommendations),
  ].filter((item): item is string => typeof item === "string" && item.length > 0);
}

export function buildFixPrompt(input: {
  runId: string;
  task: string;
  summary: string;
  severity?: string;
  confidence?: string;
  effectCount?: number;
  duplicateCount?: number;
  sessionPath?: string;
  diagnosisPath?: string;
  playbookPath?: string;
  evidence: { sequence?: unknown; hash?: unknown; message?: string }[];
  rootCause?: string;
  causalChain?: string[];
  recommendations: string[];
  strengths: string[];
  verification: string[];
}) {
  const pathOrMissing = (value?: string) =>
    value || "Not available — use the remaining artifact listed above.";
  return `# Critiqor runtime remediation task

You are improving the agent from Critiqor run ${input.runId}.

Before changing code, read these complete artifacts:
- Runtime session: ${pathOrMissing(input.sessionPath)}
- Diagnosis: ${pathOrMissing(input.diagnosisPath)}
- Improvement playbook: ${pathOrMissing(input.playbookPath)}

Use session.json as the authoritative runtime record. Trace every diagnosis claim to its event sequence_id/event_hash. Use diagnosis.json for the supported causal analysis, counterevidence, alternatives, strengths, and comparison metadata. Follow the playbook, but verify its claims against the runtime yourself.

Task attempted:
${input.task || "Not captured"}

Observed result and primary diagnosis:
${input.summary || "More evidence needed"}
${input.severity ? `Severity: ${input.severity}` : "Severity: Not captured"}
${input.confidence ? `Confidence: ${input.confidence}` : "Confidence: More evidence needed"}
Authoritative effects: ${input.effectCount ?? "Not captured"}
Duplicate effects: ${input.duplicateCount ?? "Not captured"}

Evidence to inspect first:
${
  input.evidence.length
    ? input.evidence
        .map(
          (item) =>
            `- sequence ${item.sequence ?? "Not captured"} hash ${item.hash ?? "Not captured"}${item.message ? ` — ${item.message}` : ""}`,
        )
        .join("\n")
    : "- More evidence needed"
}

Root cause and causal chain:
${input.rootCause || "Not captured"}
${(input.causalChain ?? []).map((step, index) => `${index + 1}. ${step}`).join("\n") || "- Not captured"}

Required improvements:
${input.recommendations.map((step, index) => `${index + 1}. ${step}`).join("\n") || "1. More evidence needed"}

Strengths to preserve:
${input.strengths.map((item) => `- ${item}`).join("\n") || "- Not captured"}

Implementation constraints:
- Treat timeout/cancellation/disconnect/navigation/lost response after a consequential call as unknown, not failed.
- Do not blindly retry an unresolved consequential action.
- Reconcile authoritative state before any effect-equivalent retry.
- Preserve stable operation identity and intent binding.

Verification:
${input.verification.map((step) => `- ${step}`).join("\n") || "- Rerun the same scenario with Critiqor and compare authoritative effects."}

Deliverables:
1. Explain the failure path using cited runtime events.
2. Implement the smallest complete reliability fix.
3. Add or update tests for the exact adversity.
4. Rerun the same scenario with Critiqor.
5. Report before/after findings, authoritative effects, duplicate effects, and any regression.

Do not claim the issue is resolved unless the same scenario is exercised and the target-side authoritative evidence supports the result.
`;
}

function titleize(value: string) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function developmentFallbackState(apiBase: string, error: unknown): State {
  const state = emptyState();
  return {
    ...state,
    executive: {
      trustScore: 0,
      confidence: 0,
      verdict: "Waiting for diagnosis artifact",
      summary:
        "Development fallback: no Critiqor diagnosis API data is available yet. Finalize a run to generate runs/<run_id>/diagnosis.json.",
      evidence: [],
      confidenceReasoning: "No local diagnosis artifact has been loaded.",
      runId: "dev_no_diagnosis",
      agent: "OpenClaw agent",
      task: "No finalized diagnosis loaded",
      generatedAt: new Date().toISOString(),
      trustLevel: "low",
    },
    sync: {
      loading: false,
      source: "error",
      error: error instanceof Error ? error.message : "Unable to load Critiqor diagnosis artifacts",
      lastUpdated: new Date().toISOString(),
      apiBase,
    },
  };
}
