export type ApiRole = "viewer" | "analyst" | "admin";
import { readFileSync } from "node:fs";
import { join } from "node:path";

export type DashboardVisibility = "private" | "shared" | "anonymous" | "public";
export function dashboardAccess() {
  try {
    const path =
      process.env.CRITIQOR_ACCESS_CONFIG ||
      join(process.env.CRITIQOR_RUNS_DIR || "runs", ".critiqor_dashboard", "access.json");
    const parsed = JSON.parse(readFileSync(path, "utf8"));
    const visibility = (
      ["private", "shared", "anonymous", "public"].includes(parsed.visibility)
        ? parsed.visibility
        : "private"
    ) as DashboardVisibility;
    return { visibility, credential: String(parsed.credential || "") };
  } catch {
    return { visibility: "private" as DashboardVisibility, credential: "" };
  }
}
type ApiIdentity =
  | { ok: true; tenantId: string; role: ApiRole; subject: string }
  | { ok: false; response: Response };

const loopbackHosts = new Set(["127.0.0.1", "::1", "localhost"]);
const roleRank: Record<ApiRole, number> = { viewer: 1, analyst: 2, admin: 3 };

export function corsHeaders(request: Request) {
  const configuredOrigin = process.env.CRITIQOR_DASHBOARD_ORIGIN;
  const origin = request.headers.get("origin");
  const allowOrigin =
    configuredOrigin && origin === configuredOrigin
      ? configuredOrigin
      : loopbackHosts.has(new URL(request.url).hostname) && origin
        ? origin
        : "";
  return {
    ...(allowOrigin ? { "access-control-allow-origin": allowOrigin } : {}),
    "access-control-allow-methods": "GET,POST,DELETE,OPTIONS",
    "access-control-allow-headers": "authorization,content-type,x-critiqor-tenant",
    vary: "Origin",
  };
}

export function authenticateApi(request: Request, requiredRole: ApiRole = "viewer"): ApiIdentity {
  const url = new URL(request.url);
  const authorization = request.headers.get("authorization") ?? "";
  const suppliedToken = authorization.startsWith("Bearer ") ? authorization.slice(7) : "";
  const localOnly = loopbackHosts.has(url.hostname);
  let tenantId = request.headers.get("x-critiqor-tenant")?.trim() || "default";
  let role: ApiRole = "admin";
  let subject = "local-user";
  const access = dashboardAccess();

  if (access.visibility === "private" || access.visibility === "shared") {
    if (!access.credential || suppliedToken !== access.credential) {
      return {
        ok: false,
        response: Response.json(
          { error: "credential_required", visibility: access.visibility },
          { status: 401, headers: corsHeaders(request) },
        ),
      };
    }
    subject = access.visibility === "private" ? "private-owner" : "invited-viewer";
  }

  if (process.env.CRITIQOR_DASHBOARD_TOKENS) {
    let tokens: Record<string, { tenant_id?: string; role?: ApiRole; subject?: string }>;
    try {
      tokens = JSON.parse(process.env.CRITIQOR_DASHBOARD_TOKENS);
    } catch {
      return {
        ok: false,
        response: Response.json({ error: "invalid_server_token_configuration" }, { status: 503 }),
      };
    }
    const identity = tokens[suppliedToken];
    if (!identity) {
      return {
        ok: false,
        response: Response.json(
          { error: "unauthorized" },
          { status: 401, headers: corsHeaders(request) },
        ),
      };
    }
    // A deployed token must never inherit a caller-controlled tenant header.
    // Unscoped tokens are invalid instead of silently becoming cross-tenant.
    if (!identity.tenant_id) {
      return {
        ok: false,
        response: Response.json(
          { error: "token_tenant_binding_required" },
          { status: 503, headers: corsHeaders(request) },
        ),
      };
    }
    tenantId = identity.tenant_id;
    role = identity.role || "viewer";
    subject = identity.subject || "service-token";
  } else if (process.env.CRITIQOR_DASHBOARD_API_TOKEN) {
    if (suppliedToken !== process.env.CRITIQOR_DASHBOARD_API_TOKEN) {
      return {
        ok: false,
        response: Response.json(
          { error: "unauthorized" },
          { status: 401, headers: corsHeaders(request) },
        ),
      };
    }
    subject = "legacy-service-token";
  } else if (!localOnly) {
    return {
      ok: false,
      response: Response.json(
        { error: "dashboard_api_token_required" },
        { status: 503, headers: corsHeaders(request) },
      ),
    };
  }

  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(tenantId)) {
    return {
      ok: false,
      response: Response.json(
        { error: "invalid_tenant" },
        { status: 400, headers: corsHeaders(request) },
      ),
    };
  }
  if (roleRank[role] < roleRank[requiredRole]) {
    return {
      ok: false,
      response: Response.json(
        { error: "forbidden" },
        { status: 403, headers: corsHeaders(request) },
      ),
    };
  }
  return { ok: true, tenantId, role, subject };
}
