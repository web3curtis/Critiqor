import { createFileRoute } from "@tanstack/react-router";
import { ingestRun, listRuns } from "@/lib/critiqor-api-store.server";
import { authenticateApi, corsHeaders, dashboardAccess } from "@/lib/api-auth.server";
import { writeAuditEvent } from "@/lib/audit-log.server";

const json = (request: Request, payload: unknown, init?: ResponseInit) =>
  Response.json(payload, {
    ...init,
    headers: {
      ...corsHeaders(request),
      ...(init?.headers ?? {}),
    },
  });

export const Route = createFileRoute("/api/runs")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const identity = authenticateApi(request, "viewer");
        return identity.ok
          ? json(request, { runs: listRuns(identity.tenantId).map((run) => redactAnonymous(run)) })
          : identity.response;
      },
      POST: async ({ request }) => {
        const identity = authenticateApi(request, "analyst");
        if (!identity.ok) return identity.response;
        const payload = await request.json().catch(() => ({}));
        const result = ingestRun(payload, identity.tenantId);
        writeAuditEvent({
          action: "run.ingest",
          tenantId: identity.tenantId,
          subject: identity.subject,
          role: identity.role,
          resource: result.run_id,
          outcome: result.status === "tenant_mismatch" ? "denied" : "allowed",
        });
        const status =
          result.status === "tenant_mismatch"
            ? 403
            : result.status === "integrity_rejected"
              ? 422
              : 200;
        return json(request, result, { status });
      },
      OPTIONS: async ({ request }) => json(request, { ok: true }),
    },
  },
});

function redactAnonymous(run: unknown) {
  if (dashboardAccess().visibility !== "anonymous") return run;
  const copy = structuredClone(run) as Record<string, unknown>;
  copy.agent_id = "anonymous-agent";
  copy.tenant_id = "anonymous";
  copy.visibility = "anonymous";
  const raw = copy.raw_evidence as Record<string, unknown> | undefined;
  if (raw) for (const key of Object.keys(raw)) raw[key] = "Hidden for anonymous access";
  return copy;
}
