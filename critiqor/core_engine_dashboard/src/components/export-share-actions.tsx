import { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Download, Mail, Share2 } from "lucide-react";

type Json = Record<string, unknown>;
type ExportFormat = "markdown" | "pdf" | "html" | "png" | "diagnosis_json" | "session_json" | "zip";

type ExportRun = Json & {
  run_id?: string;
  agent_id?: string;
  framework?: string;
  executive_summary?: Json;
  primary_diagnosis?: Json;
  artifact_payloads?: {
    diagnosis_json?: Json;
    session_json?: Json;
  };
};

const formats: { id: ExportFormat; label: string; detail: string }[] = [
  {
    id: "markdown",
    label: "Markdown (.md)",
    detail: "Optimized for ChatGPT, Claude, Codex, Gemini, and OpenClaw.",
  },
  { id: "pdf", label: "PDF Report", detail: "Opens a print-ready executive report." },
  { id: "html", label: "HTML Report", detail: "Standalone report for archiving or sharing." },
  { id: "png", label: "Screenshot (.png)", detail: "Captures the current browser viewport." },
  { id: "diagnosis_json", label: "diagnosis.json", detail: "Exact diagnosis artifact." },
  { id: "session_json", label: "session.json", detail: "Exact session artifact when available." },
  {
    id: "zip",
    label: "ZIP bundle",
    detail: "Downloads diagnosis, session, and Markdown reports for selected runs.",
  },
];

const asRecord = (value: unknown): Json =>
  value && typeof value === "object" && !Array.isArray(value) ? (value as Json) : {};
const asArray = (value: unknown): unknown[] => (Array.isArray(value) ? value : []);
const asString = (value: unknown, fallback = "") => (value == null ? fallback : String(value));
const asNumber = (value: unknown, fallback = 0) => {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
};

export function ExportShareActions({
  defaultRunId,
  showShare = true,
}: {
  defaultRunId?: string;
  showShare?: boolean;
}) {
  const [runs, setRuns] = useState<ExportRun[]>([]);
  const [exportOpen, setExportOpen] = useState(false);
  const [shareOpen, setShareOpen] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [format, setFormat] = useState<ExportFormat>("markdown");
  const [email, setEmail] = useState("");

  useEffect(() => {
    fetch("/api/runs")
      .then((response) => response.json())
      .then((payload) => {
        const next = (Array.isArray(payload) ? payload : asArray(payload.runs)).filter(
          Boolean,
        ) as ExportRun[];
        setRuns(next);
        const defaultSelection =
          defaultRunId && next.some((run) => runId(run) === defaultRunId)
            ? [defaultRunId]
            : next.slice(0, 1).map(runId);
        setSelected(new Set(defaultSelection));
      })
      .catch(() => setRuns([]));
  }, [defaultRunId]);

  const selectedRuns = useMemo(
    () => runs.filter((run) => selected.has(runId(run))),
    [runs, selected],
  );
  const selectedFormat = formats.find((item) => item.id === format) ?? formats[0];

  const toggleRun = (id: string) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const runExport = async () => {
    if (!selectedRuns.length) return;
    if (format === "png") {
      window.print();
      return;
    }
    if (format === "pdf") {
      openReportWindow(renderHtmlReport(selectedRuns));
      return;
    }
    const { body, mime, filename } = buildExport(selectedRuns, format);
    downloadFile(filename, body, mime);
  };

  return (
    <>
      <div className="flex items-center gap-2">
        {showShare && (
          <Button variant="outline" size="sm" onClick={() => setShareOpen(true)}>
            <Share2 className="size-4" /> Share
          </Button>
        )}
        <Button size="sm" onClick={() => setExportOpen(true)}>
          <Download className="size-4" /> Export
        </Button>
      </div>

      <Dialog open={exportOpen} onOpenChange={setExportOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Export Runs</DialogTitle>
            <DialogDescription>
              Select runs, choose a format, preview the contents, then download.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-5 md:grid-cols-[1.2fr_.8fr]">
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelected(new Set(runs.map(runId)))}
                >
                  Select All
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setSelected(new Set())}>
                  Deselect All
                </Button>
              </div>
              <div className="max-h-[360px] space-y-2 overflow-auto pr-1">
                {runs.map((run) => {
                  const id = runId(run);
                  return (
                    <button
                      key={id}
                      onClick={() => toggleRun(id)}
                      className="w-full rounded-lg border bg-card p-3 text-left transition-colors hover:bg-accent"
                    >
                      <div className="flex items-start gap-3">
                        <Checkbox checked={selected.has(id)} aria-label={`Select ${id}`} />
                        <div className="min-w-0 flex-1">
                          <div className="font-mono text-sm font-semibold">{id}</div>
                          <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                            <span>Trust: {trustScore(run)}</span>
                            <span>Framework: {asString(run.framework, "openclaw")}</span>
                            <span>{primaryDiagnosis(run)}</span>
                            <span>{runDate(run)}</span>
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-3">
              <div className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
                Format
              </div>
              <div className="space-y-2">
                {formats.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => setFormat(item.id)}
                    className={`w-full rounded-lg border p-3 text-left text-sm transition-colors ${format === item.id ? "border-primary bg-primary/10" : "bg-card hover:bg-accent"}`}
                  >
                    <div className="font-medium">{item.label}</div>
                    <div className="mt-1 text-xs text-muted-foreground">{item.detail}</div>
                  </button>
                ))}
              </div>
              <div className="rounded-lg border bg-muted/20 p-3 text-sm">
                <div className="font-medium">Export Preview</div>
                <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                  <div>Runs Selected: {selectedRuns.length}</div>
                  <div>Export Type: {selectedFormat.label}</div>
                  <div>Estimated File Size: {estimatedSize(selectedRuns, format)}</div>
                  <div>
                    Included Sections: Executive Summary, Agent Health, Diagnosis, Evidence,
                    Timeline, Recommendations, Metadata
                  </div>
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setExportOpen(false)}>
              Cancel
            </Button>
            <Button onClick={runExport} disabled={!selectedRuns.length}>
              Download
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={shareOpen} onOpenChange={setShareOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Sharing is administrator-controlled</DialogTitle>
            <DialogDescription>
              Critiqor does not create client-only links or invitations. Ask an administrator to
              grant a tenant-scoped viewer identity, then share the authenticated dashboard URL.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="rounded-lg border bg-card p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="font-medium">Public links unavailable</div>
                  <div className="text-sm text-muted-foreground">
                    A URL alone never grants access to runtime evidence or exported diagnoses.
                  </div>
                </div>
                <Badge variant="outline">Disabled</Badge>
              </div>
            </div>

            <div className="rounded-lg border bg-card p-4">
              <div className="font-medium">Invite by email</div>
              <div className="mt-3 flex gap-2">
                <Input
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="teammate@example.com"
                  disabled
                />
                <Button disabled>
                  <Mail className="size-4" /> Administrator required
                </Button>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <span className="text-sm text-muted-foreground">
                  Invitations require an external identity provider and server-side audit trail.
                </span>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function runId(run: ExportRun | undefined) {
  return asString(run?.run_id, "");
}

function trustScore(run: ExportRun) {
  return asNumber(asRecord(run.executive_summary).trust_score, 0);
}

function primaryDiagnosis(run: ExportRun) {
  return (
    asString(asRecord(run.primary_diagnosis).root_cause_failure_type, "Healthy Runtime") ||
    "Healthy Runtime"
  );
}

function runDate(run: ExportRun) {
  const trace = asArray(asRecord(run.evidence_panel).trace).map(asRecord);
  const first = trace.find((event) => event.timestamp || event.at);
  const value = asString(first?.timestamp ?? first?.at, "");
  return value ? new Date(value).toLocaleDateString() : "No date";
}

function estimatedSize(runs: ExportRun[], format: ExportFormat) {
  const bytes = JSON.stringify(runs).length;
  const multiplier = format === "pdf" || format === "html" ? 1.8 : format === "zip" ? 2.2 : 1;
  return `${Math.max(1, Math.round((bytes * multiplier) / 1024))} KB`;
}

function buildExport(runs: ExportRun[], format: ExportFormat) {
  if (format === "markdown")
    return { filename: "Critiqor_Diagnosis.md", mime: "text/markdown", body: renderMarkdown(runs) };
  if (format === "html")
    return { filename: "Critiqor_Report.html", mime: "text/html", body: renderHtmlReport(runs) };
  if (format === "diagnosis_json")
    return {
      filename: "diagnosis.json",
      mime: "application/json",
      body: JSON.stringify(
        runs.map((run) => run.artifact_payloads?.diagnosis_json ?? run),
        null,
        2,
      ),
    };
  if (format === "session_json")
    return {
      filename: "session.json",
      mime: "application/json",
      body: JSON.stringify(
        runs.map((run) => run.artifact_payloads?.session_json ?? {}),
        null,
        2,
      ),
    };
  return { filename: "Critiqor_Export.zip", mime: "application/zip", body: buildZip(runs) };
}

function renderMarkdown(runs: ExportRun[]) {
  return runs
    .map((run) => {
      const summary = asRecord(run.executive_summary);
      const primary = asRecord(run.primary_diagnosis);
      const evidence = asArray(asRecord(run.evidence_panel).trace).map(asRecord);
      const causes = asArray(asRecord(run.failure_analysis).failure_causes).map(asRecord);
      return [
        `# Critiqor Diagnosis: ${runId(run)}`,
        "",
        "## Executive Summary",
        `- Trust Score: ${trustScore(run)}/100`,
        `- Confidence: ${asNumber(summary.evaluation_confidence, 0)}%`,
        `- Framework: ${asString(run.framework, "openclaw")}`,
        `- Summary: ${asString(summary.summary ?? primary.causal_chain_explanation, "No summary provided.")}`,
        "",
        "## Agent Health",
        causes.length
          ? "- Review required based on observed failure causes."
          : "- Healthy runtime profile. No runtime failure cause was detected.",
        "",
        "## Diagnosis",
        causes.length
          ? causes
              .map(
                (cause) =>
                  `- ${asString(cause.type, "runtime_failure")}: ${asString(cause.description, "")}`,
              )
              .join("\n")
          : "- No primary runtime diagnosis.",
        "",
        "## Evidence",
        evidence
          .slice(0, 30)
          .map(
            (event) =>
              `- ${asString(event.timestamp ?? event.at, "")} ${asString(event.event ?? event.event_type ?? event.type, "log")}: ${asString(event.message ?? event.summary, JSON.stringify(event.payload ?? {}))}`,
          )
          .join("\n") || "- No evidence events.",
        "",
        "## Runtime Timeline",
        evidence
          .slice(0, 50)
          .map(
            (event) =>
              `- ${asString(event.timestamp ?? event.at, "")}: ${asString(event.event ?? event.event_type ?? event.type, "event")}`,
          )
          .join("\n") || "- No timeline events.",
        "",
        "## Root Cause Analysis",
        causes
          .map(
            (cause) =>
              `- Root Cause: ${asString(cause.root_cause ?? cause.type, "")}\n  - Impact: ${asNumber(cause.impact, 0)}\n  - Recommendation: ${asString(cause.recommendation, asArray(cause.recommendations)[0] ?? "")}`,
          )
          .join("\n") || "- No root cause detected.",
        "",
        "## Recommendations",
        asArray(run.recommendations)
          .map((item) => `- ${String(item)}`)
          .join("\n") || "- Continue monitoring future runs.",
        "",
        "## Supporting Metrics",
        `- Event Count: ${evidence.length}`,
        `- Tool Calls: ${asArray(asRecord(run.evidence_panel).tool_calls).length}`,
        `- Tool Outputs: ${asArray(asRecord(run.evidence_panel).tool_outputs).length}`,
      ].join("\n");
    })
    .join("\n\n---\n\n");
}

function renderHtmlReport(runs: ExportRun[]) {
  const markdown = renderMarkdown(runs).replace(
    /[&<>]/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[char] ?? char,
  );
  return `<!doctype html><html><head><meta charset="utf-8"><title>Critiqor Report</title><style>body{font-family:Inter,Arial,sans-serif;max-width:900px;margin:48px auto;padding:0 24px;line-height:1.55;color:#0f172a}pre{white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:24px}</style></head><body><h1>Critiqor Report</h1><pre>${markdown}</pre></body></html>`;
}

function buildZip(runs: ExportRun[]) {
  const files = runs.flatMap((run) => {
    const id = runId(run);
    return [
      {
        name: `${id}/diagnosis.json`,
        body: JSON.stringify(run.artifact_payloads?.diagnosis_json ?? run, null, 2),
      },
      {
        name: `${id}/session.json`,
        body: JSON.stringify(run.artifact_payloads?.session_json ?? {}, null, 2),
      },
      { name: `${id}/diagnosis.md`, body: renderMarkdown([run]) },
    ];
  });
  return zipFiles(files);
}

function downloadFile(filename: string, body: string | Blob, mime: string) {
  const blob = body instanceof Blob ? body : new Blob([body], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function openReportWindow(html: string) {
  const win = window.open("", "_blank");
  if (!win) return;
  win.document.write(html);
  win.document.close();
  win.focus();
  win.print();
}

function zipFiles(files: { name: string; body: string }[]) {
  const encoder = new TextEncoder();
  const localParts: Uint8Array[] = [];
  const centralParts: Uint8Array[] = [];
  let offset = 0;

  for (const file of files) {
    const name = encoder.encode(file.name);
    const data = encoder.encode(file.body);
    const crc = crc32(data);
    const local = concat([
      u32(0x04034b50),
      u16(20),
      u16(0),
      u16(0),
      u16(0),
      u16(0),
      u32(crc),
      u32(data.length),
      u32(data.length),
      u16(name.length),
      u16(0),
      name,
      data,
    ]);
    const central = concat([
      u32(0x02014b50),
      u16(20),
      u16(20),
      u16(0),
      u16(0),
      u16(0),
      u16(0),
      u32(crc),
      u32(data.length),
      u32(data.length),
      u16(name.length),
      u16(0),
      u16(0),
      u16(0),
      u16(0),
      u32(0),
      u32(offset),
      name,
    ]);
    localParts.push(local);
    centralParts.push(central);
    offset += local.length;
  }

  const central = concat(centralParts);
  const end = concat([
    u32(0x06054b50),
    u16(0),
    u16(0),
    u16(files.length),
    u16(files.length),
    u32(central.length),
    u32(offset),
    u16(0),
  ]);
  return new Blob([concat([...localParts, central, end])], { type: "application/zip" });
}

function concat(parts: Uint8Array[]) {
  const length = parts.reduce((sum, part) => sum + part.length, 0);
  const output = new Uint8Array(length);
  let cursor = 0;
  for (const part of parts) {
    output.set(part, cursor);
    cursor += part.length;
  }
  return output;
}

function u16(value: number) {
  const bytes = new Uint8Array(2);
  new DataView(bytes.buffer).setUint16(0, value, true);
  return bytes;
}

function u32(value: number) {
  const bytes = new Uint8Array(4);
  new DataView(bytes.buffer).setUint32(0, value >>> 0, true);
  return bytes;
}

function crc32(data: Uint8Array) {
  let crc = 0xffffffff;
  for (const byte of data) {
    crc ^= byte;
    for (let i = 0; i < 8; i += 1) {
      crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}
