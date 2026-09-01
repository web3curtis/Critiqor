import { useSyncExternalStore } from "react";

export type Run = {
  id: string;
  name: string;
  status: "queued" | "running" | "passed" | "failed";
  startedAt: string;
  durationMs: number;
  model?: string;
  trustScore: number;
  hallucinationRisk: number;
  toolReliability: number;
  reasoningConsistency: number;
  webmcpStatus?: string;
  webmcpFindings?: number;
  webmcpEffects?: number;
  webmcpComparison?: string;
};

export type WebMcpStrength = {
  id: string;
  title: string;
  detail: string;
};

export type WebMcpAudit = {
  available: boolean;
  status: string;
  displayStatus: string;
  summary: string;
  scenariosExercised: number;
  findingCount: number;
  duplicateEffectCount: number;
  authoritativeEffectCount: number;
  blindRedispatchCount?: number;
  confidence?: string;
  strengths: WebMcpStrength[];
  comparison?: string;
};

export type Severity = "info" | "low" | "medium" | "high" | "critical";

export type DiagnosisEvidence = {
  id: string;
  type: "tool_call" | "tool_output" | "memory" | "retry" | "log" | "metric" | "judge" | "context";
  message: string;
  at: string;
  payload?: unknown;
};

export type Diagnosis = {
  id: string;
  runId: string;
  findingId?: string;
  title: string;
  severity: Severity;
  summary: string;
  createdAt: string;
  trustImpact: number;
  rootCause: string;
  recommendedInvestigation: string[];
  verificationSteps: string[];
  expectedImprovement: string;
  causalChain?: string[];
  confidence?: string;
  confirmedImpact?: string;
  potentialImpact?: string;
  evidence: DiagnosisEvidence[];
  counterEvidence: DiagnosisEvidence[];
  alternativeHypotheses: string[];
  engineeringExplanation?: string;
  teachingDiagram?: {
    stages: string[];
    highlight: string;
  };
  memoryAnalysis?: MemoryAnalysis;
  graph?: {
    nodes: { id: string; label: string; kind?: string }[];
    edges: { id: string; source: string; target: string; label?: string }[];
  };
};

export type MemoryEvidenceItem = {
  eventType: string;
  action: string;
  message: string;
  memoryId?: string;
  reason: string;
  architectureStage: string;
  confidence?: number | string;
};

export type MemoryAnalysis = {
  score: number;
  confidence: number;
  eventCount: number;
  retrievedCount: number;
  injectedCount: number;
  referencedCount: number;
  unusedCount: number;
  irrelevantCount: number;
  missedCount: number;
  createdCount: number;
  ignoredCount: number;
  tokenCost: number;
  diagnosticSummary: string;
  architectureStage: string;
  evidence: MemoryEvidenceItem[];
};

export type EvidenceEvent = {
  id: string;
  runId?: string;
  type: string;
  message: string;
  at: string;
  payload?: unknown;
};

export type Benchmark = {
  id: string;
  name: string;
  metric: string;
  target: number;
  actual: number;
  unit?: string;
  passed: boolean;
  updatedAt: string;
};

export type TrustLevel = "high" | "medium" | "low";

export type EvidenceSummary = {
  label: string;
  value: string;
  detail: string;
};

export type ScoreExplanation = {
  score: string;
  tier: string;
  value: string;
  why: string;
  evidence: EvidenceSummary[];
};

export type AgentHealth = {
  status: string;
  strengths: string[];
  stableBehaviours: string[];
  recommendedMonitoring: string[];
};

export type RuntimeTimelineItem = {
  id: string;
  label: string;
  at: string;
  detail: string;
  type: string;
};

export type ArtifactMetadata = {
  diagnosisPath?: string;
  sessionPath?: string;
  playbookPath?: string;
  playbookContent?: string;
  eventCount: number;
  toolCallCount: number;
  toolOutputCount: number;
  memoryEventCount: number;
  failureCount: number;
  durationMs: number;
  evidenceStatus: "verified" | "tampered" | "unsigned" | "incomplete" | "unknown";
  evidenceDigest?: string;
  redactionCount: number;
  truncationCount: number;
  integrityErrors: string[];
};

export type ExecutiveSummary = {
  trustScore: number;
  confidence: number;
  verdict: string;
  summary: string;
  runId: string;
  agent: string;
  task: string;
  generatedAt: string;
  trustLevel: TrustLevel;
  evidence: EvidenceSummary[];
  confidenceReasoning: string;
};

export type SyncStatus = {
  loading: boolean;
  source: "live" | "empty" | "error";
  error?: string;
  lastUpdated?: string;
  apiBase?: string;
};

export type State = {
  runs: Run[];
  diagnoses: Diagnosis[];
  evidence: EvidenceEvent[];
  benchmarks: Benchmark[];
  executive: ExecutiveSummary;
  sync: SyncStatus;
  scoreExplanations: ScoreExplanation[];
  agentHealth: AgentHealth;
  timeline: RuntimeTimelineItem[];
  artifact: ArtifactMetadata;
  memoryAnalysis?: MemoryAnalysis;
  webmcp: WebMcpAudit;
};

const emptyExecutive = (): ExecutiveSummary => ({
  trustScore: 0,
  confidence: 0,
  verdict: "Waiting for run data",
  summary:
    "Finalize a Critiqor observation session to populate this dashboard from local diagnosis artifacts.",
  runId: "no_run_selected",
  agent: "OpenClaw agent",
  task: "No monitored execution yet",
  generatedAt: new Date().toISOString(),
  trustLevel: "low",
  evidence: [],
  confidenceReasoning: "No runtime evidence has been loaded yet.",
});

export const emptyState = (): State => ({
  executive: emptyExecutive(),
  runs: [],
  diagnoses: [],
  evidence: [],
  benchmarks: [],
  sync: { loading: true, source: "empty" },
  scoreExplanations: [],
  agentHealth: {
    status: "Waiting for diagnosis",
    strengths: [],
    stableBehaviours: [],
    recommendedMonitoring: ["Finalize a Critiqor observation session to load local evidence."],
  },
  timeline: [],
  artifact: {
    eventCount: 0,
    toolCallCount: 0,
    toolOutputCount: 0,
    memoryEventCount: 0,
    failureCount: 0,
    durationMs: 0,
    evidenceStatus: "unknown",
    redactionCount: 0,
    truncationCount: 0,
    integrityErrors: [],
  },
  webmcp: {
    available: false,
    status: "NOT_EXERCISED",
    displayStatus: "Not exercised",
    summary: "No WebMCP activity was included in this run.",
    scenariosExercised: 0,
    findingCount: 0,
    duplicateEffectCount: 0,
    authoritativeEffectCount: 0,
    strengths: [],
  },
});

let state: State = emptyState();
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((l) => l());

export const critiqorStore = {
  getState: () => state,
  subscribe: (fn: () => void) => {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },
  replace: (next: Partial<State>) => {
    state = {
      ...state,
      ...next,
      executive: next.executive ?? state.executive,
      sync: next.sync ? { ...state.sync, ...next.sync } : state.sync,
    };
    emit();
  },
  setSyncStatus: (sync: Partial<SyncStatus>) => {
    state = { ...state, sync: { ...state.sync, ...sync } };
    emit();
  },
  addRun: (r: Run) => {
    state = { ...state, runs: [r, ...state.runs] };
    emit();
  },
  addDiagnosis: (d: Diagnosis) => {
    state = { ...state, diagnoses: [d, ...state.diagnoses] };
    emit();
  },
  addEvidence: (e: EvidenceEvent) => {
    state = { ...state, evidence: [e, ...state.evidence].slice(0, 500) };
    emit();
  },
  upsertBenchmark: (b: Benchmark) => {
    const existing = state.benchmarks.findIndex((x) => x.id === b.id);
    const next =
      existing >= 0
        ? state.benchmarks.map((x, i) => (i === existing ? b : x))
        : [b, ...state.benchmarks];
    state = { ...state, benchmarks: next };
    emit();
  },
  setExecutive: (e: Partial<ExecutiveSummary>) => {
    state = { ...state, executive: { ...state.executive, ...e } };
    emit();
  },
};

if (typeof window !== "undefined") {
  (window as unknown as { critiqor: typeof critiqorStore }).critiqor = critiqorStore;
}

const serverSnapshot = emptyState();

export function useCritiqor<T>(selector: (s: State) => T): T {
  const snapshot = useSyncExternalStore(
    critiqorStore.subscribe,
    critiqorStore.getState,
    () => serverSnapshot,
  );
  return selector(snapshot);
}

export const severityColor: Record<
  Severity,
  { bg: string; text: string; border: string; ring: string; dot: string }
> = {
  info: {
    bg: "bg-sky-500/10",
    text: "text-sky-400",
    border: "border-sky-500/30",
    ring: "ring-sky-500/30",
    dot: "bg-sky-400",
  },
  low: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
    ring: "ring-emerald-500/30",
    dot: "bg-emerald-400",
  },
  medium: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
    ring: "ring-amber-500/30",
    dot: "bg-amber-400",
  },
  high: {
    bg: "bg-orange-500/10",
    text: "text-orange-400",
    border: "border-orange-500/30",
    ring: "ring-orange-500/30",
    dot: "bg-orange-400",
  },
  critical: {
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/30",
    ring: "ring-red-500/30",
    dot: "bg-red-400",
  },
};

export const trustColor: Record<
  TrustLevel,
  { bg: string; text: string; border: string; label: string }
> = {
  high: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
    label: "Healthy",
  },
  medium: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
    label: "Needs Attention",
  },
  low: {
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/30",
    label: "Critical",
  },
};
