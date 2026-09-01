import { useQuery } from "@tanstack/react-query";
import { useRouterState } from "@tanstack/react-router";
import { useEffect } from "react";
import {
  fetchCritiqorRuns,
  resolveCritiqorApiBase,
  resolveSelectedRunId,
} from "@/lib/critiqor-api";
import { critiqorStore } from "@/lib/critiqor-store";

function runIdFromSearch(search: unknown) {
  if (typeof search === "string") {
    const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
    return params.get("run_id") ?? params.get("run") ?? "";
  }
  if (search && typeof search === "object") {
    const record = search as Record<string, unknown>;
    const value = record.run_id ?? record.run;
    return value == null ? "" : String(value);
  }
  return "";
}

export function CritiqorDataSync() {
  const apiBase = resolveCritiqorApiBase();
  const search = useRouterState({ select: (state) => state.location.search as unknown });
  const selectedRunId = runIdFromSearch(search) || resolveSelectedRunId();
  const query = useQuery({
    queryKey: ["critiqor-runs", apiBase, selectedRunId],
    queryFn: () => fetchCritiqorRuns(apiBase, selectedRunId),
    refetchInterval: 5000,
    retry: 1,
  });

  useEffect(() => {
    const current = critiqorStore.getState();
    if (!selectedRunId || current.executive.runId === selectedRunId) return;
    critiqorStore.replace({
      diagnoses: current.diagnoses.filter((item) => item.runId === selectedRunId),
      evidence: current.evidence.filter((item) => item.runId === selectedRunId),
      timeline: [],
      memoryAnalysis: undefined,
      artifact: {
        ...current.artifact,
        sessionPath: "",
        diagnosisPath: "",
        playbookPath: "",
        playbookContent: "",
        evidenceStatus: "unknown",
        eventCount: 0,
        toolCallCount: 0,
        toolOutputCount: 0,
        memoryEventCount: 0,
      },
      executive: {
        ...current.executive,
        runId: selectedRunId,
        task: "",
        summary: "Loading selected run...",
      },
      webmcp: {
        available: false,
        status: "NOT_EXERCISED",
        displayStatus: "Loading",
        summary: "Loading selected run...",
        scenariosExercised: 0,
        findingCount: 0,
        duplicateEffectCount: 0,
        authoritativeEffectCount: 0,
        strengths: [],
      },
    });
  }, [selectedRunId]);

  useEffect(() => {
    critiqorStore.setSyncStatus({ loading: query.isLoading, apiBase });
  }, [apiBase, query.isLoading]);

  useEffect(() => {
    if (query.data) critiqorStore.replace(query.data);
  }, [query.data]);

  useEffect(() => {
    if (query.error) {
      critiqorStore.setSyncStatus({
        loading: false,
        source: "error",
        error: query.error instanceof Error ? query.error.message : "Unable to reach Critiqor API",
        apiBase,
      });
    }
  }, [apiBase, query.error]);

  return null;
}
