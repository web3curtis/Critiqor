import { appendFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import type { ApiRole } from "./api-auth.server";

export function writeAuditEvent(event: {
  action: string;
  tenantId: string;
  subject: string;
  role: ApiRole;
  resource?: string;
  outcome: "allowed" | "denied";
}) {
  const target = process.env.CRITIQOR_AUDIT_LOG;
  if (!target) return;
  mkdirSync(path.dirname(target), { recursive: true });
  appendFileSync(
    target,
    `${JSON.stringify({ schema_version: "critiqor.audit.v1", timestamp: new Date().toISOString(), ...event })}\n`,
    { encoding: "utf8", flush: true },
  );
}
