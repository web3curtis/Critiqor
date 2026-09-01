import { useNavigate, useRouterState } from "@tanstack/react-router";
import { useCritiqor } from "@/lib/critiqor-store";

export function RunSelector({ label = "Focus run" }: { label?: string }) {
  const runs = useCritiqor((state) => state.runs);
  const current = useCritiqor((state) => state.executive.runId);
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const known = runs.some((run) => run.id === current);

  return (
    <label className="flex min-w-64 flex-wrap items-center gap-2 text-sm">
      <span className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        {label}
      </span>
      <select
        aria-label={label}
        className="h-9 min-w-56 flex-1 rounded-md border bg-background px-3 text-sm"
        value={current}
        onChange={(event) => {
          const runId = event.target.value;
          if (!runId) return;
          void navigate({
            to: pathname,
            search: { run_id: runId },
          } as never);
        }}
      >
        {!known && current && <option value={current}>{current} · not found</option>}
        {runs.map((run) => (
          <option key={run.id} value={run.id}>
            {run.id}
            {run.webmcpStatus ? ` · ${run.webmcpStatus}` : ""}
          </option>
        ))}
        {!runs.length && !current && <option value="">No runs available</option>}
      </select>
    </label>
  );
}
