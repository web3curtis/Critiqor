export type DiagnosisArtifact = {
  run_id?: string;
  tenant_id?: string;
  agent_id?: string;
  framework?: string;
  visibility?: string;
  evaluation_confidence?: number;
  executive_summary?: {
    trust_score?: number;
    readiness_level?: string;
    evidence_level?: string;
    evaluation_confidence?: number;
    event_count?: number;
    [key: string]: unknown;
  };
  primary_diagnosis?: {
    root_cause_failure_type?: string;
    causal_chain_explanation?: string;
    recommended_next_action?: string;
    [key: string]: unknown;
  };
  cost_analysis?: Record<string, unknown>;
  failure_analysis?: {
    failure_causes?: DiagnosisFailureCause[];
    top_failure_modes?: unknown[];
    frequency_distribution?: Record<string, unknown>;
    [key: string]: unknown;
  };
  evidence_panel?: {
    trace?: DiagnosisEvidenceRecord[];
    causal_graph?: DiagnosisCausalGraph;
    tool_calls?: DiagnosisEvidenceRecord[];
    tool_outputs?: DiagnosisEvidenceRecord[];
    memory_events?: DiagnosisEvidenceRecord[];
    [key: string]: unknown;
  };
  recommendations?: string[];
  raw_evidence?: {
    session_jsonl?: string;
    session_json?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

export type DiagnosisFailureCause = {
  type?: string;
  severity?: string;
  impact?: number;
  impact_score?: number;
  description?: string;
  root_cause?: string;
  evidence?: DiagnosisEvidenceRecord[];
  causal_chain?: string[];
  recommendation?: string;
  recommendations?: string[];
  [key: string]: unknown;
};

export type DiagnosisEvidenceRecord = {
  event?: string;
  event_type?: string;
  type?: string;
  timestamp?: string;
  at?: string;
  message?: string;
  label?: string;
  summary?: string;
  tool?: string;
  tool_name?: string;
  payload?: unknown;
  [key: string]: unknown;
};

export type DiagnosisCausalGraph = {
  nodes?: { id?: string; label?: string; type?: string; kind?: string; [key: string]: unknown }[];
  edges?: {
    id?: string;
    source?: string;
    target?: string;
    from?: string;
    to?: string;
    label?: string;
    relation?: string;
    [key: string]: unknown;
  }[];
  [key: string]: unknown;
};
