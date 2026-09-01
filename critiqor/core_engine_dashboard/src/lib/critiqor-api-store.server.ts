import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  renameSync,
  statSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { createHash, createPublicKey, verify as verifySignature } from "node:crypto";
import path from "node:path";
import type { DiagnosisArtifact, DiagnosisEvidenceRecord } from "./critiqor-diagnosis-model";

type StoredRun = Record<string, unknown>;

type GlobalStore = typeof globalThis & {
  __critiqorRuns?: Map<string, StoredRun>;
};

const store = () => {
  const g = globalThis as GlobalStore;
  if (!g.__critiqorRuns) g.__critiqorRuns = new Map<string, StoredRun>();
  return g.__critiqorRuns;
};

const durableRoot = () =>
  path.resolve(
    process.env.CRITIQOR_DASHBOARD_STATE_DIR ??
      path.join(process.cwd(), ".critiqor-dashboard-state"),
  );

const storageKey = (value: string) => createHash("sha256").update(value, "utf8").digest("hex");

const tenantDirectory = (tenantId: string) => path.join(durableRoot(), storageKey(tenantId));

const durableFile = (tenantId: string, runId: string) =>
  path.join(tenantDirectory(tenantId), `${storageKey(runId)}.json`);

const persistRun = (run: StoredRun, tenantId: string) => {
  const directory = tenantDirectory(tenantId);
  mkdirSync(directory, { recursive: true, mode: 0o700 });
  const destination = durableFile(tenantId, getRunId(run));
  const temporary = `${destination}.${process.pid}.${Date.now()}.tmp`;
  writeFileSync(temporary, `${JSON.stringify(run)}\n`, { encoding: "utf8", mode: 0o600 });
  renameSync(temporary, destination);
};

const durableRuns = (tenantId: string): StoredRun[] => {
  const directory = tenantDirectory(tenantId);
  if (!existsSync(directory)) return [];
  return readdirSync(directory)
    .filter((name) => name.endsWith(".json"))
    .map((name) => readJson(path.join(directory, name)))
    .filter((run): run is StoredRun => Boolean(run))
    .filter((run) => String(run.tenant_id ?? "default") === tenantId);
};

const asRecord = (value: unknown): Record<string, unknown> =>
  value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};

const asArray = (value: unknown): unknown[] => (Array.isArray(value) ? value : []);

const canonicalJson = (value: unknown): string => {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>)
      .filter(([, item]) => item !== undefined)
      .sort(([left], [right]) => left.localeCompare(right));
    return `{${entries
      .map(([key, item]) => `${JSON.stringify(key)}:${canonicalJson(item)}`)
      .join(",")}}`;
  }
  return JSON.stringify(value) ?? "null";
};

const sha256 = (value: unknown) =>
  createHash("sha256").update(canonicalJson(value), "utf8").digest("hex");

const verifyAuthoritativeArtifact = (payload: StoredRun, tenantId: string) => {
  const manifest = asRecord(payload.evaluation_manifest);
  const signature = asRecord(manifest.signature);
  const publicKey = process.env.CRITIQOR_SIGNING_PUBLIC_KEY;
  if (signature.algorithm !== "ed25519" || !publicKey) {
    return { valid: false, error: "ed25519_verifier_not_configured" };
  }
  if (
    String(manifest.run_id ?? "") !== getRunId(payload) ||
    String(manifest.tenant_id ?? "") !== tenantId ||
    String(manifest.evidence_status ?? "") !== "verified"
  ) {
    return { valid: false, error: "manifest_identity_or_evidence_mismatch" };
  }
  const unsigned = { ...manifest };
  delete unsigned.signature;
  const rawPublicKey = Buffer.from(publicKey, "base64");
  const derPrefix = Buffer.from("302a300506032b6570032100", "hex");
  let signatureValid = false;
  try {
    signatureValid = verifySignature(
      null,
      Buffer.from(canonicalJson(unsigned), "utf8"),
      createPublicKey({
        key: Buffer.concat([derPrefix, rawPublicKey]),
        format: "der",
        type: "spki",
      }),
      Buffer.from(String(signature.value ?? ""), "base64"),
    );
  } catch {
    return { valid: false, error: "invalid_ed25519_material" };
  }
  if (!signatureValid) return { valid: false, error: "manifest_signature_mismatch" };

  const diagnosis = { ...payload };
  delete diagnosis.evaluation_manifest;
  if (sha256(diagnosis) !== String(manifest.diagnosis_digest ?? "")) {
    return { valid: false, error: "diagnosis_digest_mismatch" };
  }
  const trace = asArray(payload.trace);
  if (
    sha256(trace) !== String(manifest.evidence_digest ?? "") ||
    trace.length !== Number(manifest.evidence_event_count)
  ) {
    return { valid: false, error: "evidence_digest_mismatch" };
  }
  return { valid: true };
};

const getRunId = (payload: StoredRun) => {
  const direct = payload.run_id ?? payload.runId;
  if (direct) return String(direct);
  const nested = payload.executive_summary;
  if (nested && typeof nested === "object" && "run_id" in nested)
    return String((nested as Record<string, unknown>).run_id);
  return "run_" + Date.now().toString(36);
};

const artifactRoots = () => {
  const configured = [
    process.env.CRITIQOR_DIAGNOSIS_DIR,
    process.env.CRITIQOR_RUNS_DIR,
    process.env.VITE_CRITIQOR_RUNS_DIR,
  ].filter(Boolean) as string[];
  return [...configured, path.resolve(process.cwd(), "runs")];
};

const readJson = (file: string): StoredRun | null => {
  try {
    return JSON.parse(readFileSync(file, "utf8")) as StoredRun;
  } catch {
    return null;
  }
};

const readSessionEvents = (file: string): DiagnosisEvidenceRecord[] => {
  if (!existsSync(file)) return [];
  const payload = readJson(file);
  const events = Array.isArray(payload?.events) ? payload.events : [];
  return events.filter(
    (event): event is DiagnosisEvidenceRecord => Boolean(event) && typeof event === "object",
  );
};

const findDiagnosisFiles = () => {
  const files: string[] = [];
  for (const root of artifactRoots()) {
    if (!existsSync(root)) continue;
    const stat = statSync(root);
    if (stat.isFile() && path.basename(root) === "diagnosis.json") {
      files.push(root);
      continue;
    }
    if (!stat.isDirectory()) continue;
    for (const name of readdirSync(root)) {
      const candidate = path.join(root, name);
      if (!statSync(candidate).isDirectory()) continue;
      const diagnosis = path.join(candidate, "diagnosis.json");
      if (existsSync(diagnosis)) files.push(diagnosis);
    }
  }
  return Array.from(new Set(files));
};

const attachArtifactEvidence = (diagnosis: DiagnosisArtifact, diagnosisPath: string): StoredRun => {
  const runDir = path.dirname(diagnosisPath);
  const rawEvidence = asRecord(diagnosis.raw_evidence);
  const artifacts = asRecord((diagnosis as StoredRun).artifacts);
  const explicitSession =
    typeof asRecord(artifacts.session).path === "string"
      ? String(asRecord(artifacts.session).path)
      : typeof rawEvidence.session_json === "string"
        ? rawEvidence.session_json
        : "";
  const evidencePath =
    explicitSession && path.isAbsolute(explicitSession)
      ? explicitSession
      : path.join(runDir, explicitSession || "session.json");
  const playbookPath =
    typeof asRecord(artifacts.improvement_playbook).path === "string"
      ? String(asRecord(artifacts.improvement_playbook).path)
      : typeof rawEvidence.improvement_playbook === "string"
        ? rawEvidence.improvement_playbook
        : path.join(runDir, "improvement_playbook.md");
  const playbookContent = existsSync(playbookPath) ? readFileSync(playbookPath, "utf8") : "";
  const trace = readSessionEvents(evidencePath);
  const sessionPayload = readJson(evidencePath);
  const evidencePanel = asRecord(diagnosis.evidence_panel);
  const existingTrace = asArray(evidencePanel.trace) as DiagnosisEvidenceRecord[];
  const mergedTrace = existingTrace.length ? existingTrace : trace;
  return ensureDashboardView({
    ...diagnosis,
    artifacts: {
      ...artifacts,
      session: { path: evidencePath, relative_path: "session.json" },
      diagnosis: { path: diagnosisPath, relative_path: "diagnosis.json" },
      improvement_playbook: { path: playbookPath, relative_path: "improvement_playbook.md" },
    },
    raw_evidence: {
      ...rawEvidence,
      diagnosis_json: diagnosisPath,
      session_json: evidencePath,
      improvement_playbook: playbookPath,
    },
    artifact_payloads: {
      diagnosis_json: diagnosis,
      session_json: sessionPayload,
      improvement_playbook: playbookContent,
    },
    evidence_panel: {
      ...evidencePanel,
      trace: mergedTrace,
      tool_calls: asArray(evidencePanel.tool_calls).length
        ? evidencePanel.tool_calls
        : mergedTrace.filter(
            (event) => event.event === "tool_call" || event.event_type === "tool_call",
          ),
      tool_outputs: asArray(evidencePanel.tool_outputs).length
        ? evidencePanel.tool_outputs
        : mergedTrace.filter(
            (event) =>
              event.event === "tool_output" ||
              event.event_type === "tool_result" ||
              event.event_type === "tool_output",
          ),
      memory_events: asArray(evidencePanel.memory_events).length
        ? evidencePanel.memory_events
        : mergedTrace.filter(
            (event) =>
              event.event === "memory_event" ||
              event.event_type === "memory_search" ||
              event.event_type === "memory_get",
          ),
      causal_graph: evidencePanel.causal_graph ??
        diagnosis.causal_graph ?? { nodes: [], edges: [] },
    },
  } as StoredRun);
};

const artifactRuns = () =>
  findDiagnosisFiles()
    .map((file) => {
      const payload = readJson(file);
      return payload ? attachArtifactEvidence(payload as DiagnosisArtifact, file) : null;
    })
    .filter(Boolean) as StoredRun[];

const ensureDashboardView = (payload: StoredRun): StoredRun => {
  if (payload.executive_summary && payload.evidence_panel) {
    const view = { ...payload };
    view.run_id = getRunId(view);
    return view;
  }
  const summary = asRecord(payload.executive_summary);
  const trustScore =
    Number(payload.trust_score ?? payload.trustScore ?? summary.trust_score ?? 0) || 0;
  const runId = getRunId(payload);
  const trace = Array.isArray(payload.trace) ? payload.trace : [];
  return {
    ...payload,
    run_id: runId,
    tenant_id: payload.tenant_id ?? "default",
    agent_id: payload.agent_id ?? "openclaw_agent",
    framework: payload.framework ?? "openclaw",
    visibility: payload.visibility ?? "private",
    executive_summary: {
      ...summary,
      trust_score: trustScore,
      readiness_level:
        payload.readiness_level ??
        summary.readiness_level ??
        (trustScore >= 85
          ? "ready_for_runtime"
          : trustScore >= 65
            ? "review_recommended"
            : "unsafe_for_production"),
      evidence_level: payload.evidence_level ?? summary.evidence_level ?? "trace_available",
      evaluation_confidence: payload.evaluation_confidence ?? summary.evaluation_confidence,
      event_count: trace.length,
    },
    primary_diagnosis: payload.primary_diagnosis ?? {
      root_cause_failure_type: "runtime_observed",
      causal_chain_explanation: "Critiqor loaded this run from a local diagnosis artifact.",
    },
    cost_analysis: payload.cost_analysis ?? {},
    recommendations: payload.recommendations ?? [],
    failure_analysis: {
      failure_causes: Array.isArray(payload.failure_causes) ? payload.failure_causes : [],
      top_failure_modes: [],
      frequency_distribution: {},
    },
    evidence_panel: {
      trace,
      causal_graph: payload.causal_graph ?? { nodes: [], edges: [] },
      tool_calls: trace.filter(
        (event) =>
          typeof event === "object" &&
          event &&
          (event as Record<string, unknown>).event === "tool_call",
      ),
      tool_outputs: trace.filter(
        (event) =>
          typeof event === "object" &&
          event &&
          (event as Record<string, unknown>).event === "tool_output",
      ),
      memory_events: trace.filter(
        (event) =>
          typeof event === "object" &&
          event &&
          (event as Record<string, unknown>).event === "memory_event",
      ),
    },
  };
};

export function listRuns(tenantId = "default") {
  const byId = new Map<string, StoredRun>();
  for (const run of artifactRuns()) byId.set(getRunId(run), run);
  for (const run of durableRuns(tenantId)) byId.set(getRunId(run), run);
  for (const [runId, run] of store()) byId.set(runId, run);
  return Array.from(byId.values())
    .filter((run) => String(run.tenant_id ?? "default") === tenantId)
    .sort((a, b) => String(b.run_id ?? "").localeCompare(String(a.run_id ?? "")));
}

export function getRun(runId: string, tenantId = "default") {
  const stored = store().get(runId);
  if (stored && String(stored.tenant_id ?? "default") === tenantId) return stored;
  return listRuns(tenantId).find((run) => getRunId(run) === runId) ?? null;
}

export function ingestRun(payload: StoredRun, tenantId = "default") {
  if (payload.tenant_id != null && String(payload.tenant_id) !== tenantId) {
    return { status: "tenant_mismatch", run_id: "", error: "tenant_mismatch" };
  }
  const verification = verifyAuthoritativeArtifact(payload, tenantId);
  if (!verification.valid) {
    return {
      status: "integrity_rejected",
      run_id: "",
      error: verification.error,
    };
  }
  const view = ensureDashboardView({ ...payload, tenant_id: tenantId });
  const runId = getRunId(view);
  view.run_id = runId;
  store().set(runId, view);
  persistRun(view, tenantId);
  return { status: "accepted", run_id: runId, run: view };
}

export function setVisibility(runId: string, visibility: string, tenantId = "default") {
  if (!["private", "organization", "public", "anonymous"].includes(visibility)) {
    return { status: "invalid_visibility", run_id: runId };
  }
  const run = getRun(runId, tenantId);
  if (!run) return { status: "not_found", run_id: runId };
  const next = { ...run, visibility };
  store().set(runId, next);
  persistRun(next, tenantId);
  return { status: "updated", run_id: runId, visibility };
}

export function deleteRun(runId: string, tenantId = "default") {
  const run = getRun(runId, tenantId);
  if (!run) return { status: "not_found", run_id: runId };
  store().delete(runId);
  const destination = durableFile(tenantId, runId);
  if (existsSync(destination)) unlinkSync(destination);
  return { status: "deleted", run_id: runId };
}
