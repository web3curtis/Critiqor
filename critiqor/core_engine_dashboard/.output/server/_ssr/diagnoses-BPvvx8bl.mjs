import { r as reactExports, j as jsxRuntimeExports } from "../_libs/react.mjs";
import { P as PageShell, C as Card, b as CardHeader, c as CardTitle, B as Badge, a as CardContent } from "./card-CBpR56_E.mjs";
import { R as RunSelector } from "./run-selector-C4dStYQR.mjs";
import { u as useCritiqor, t as trustColor, b as buildFixPrompt, B as Button, I as Input, s as severityColor, c as cn } from "./router-Cv4vvrPJ.mjs";
import { t as toast } from "../_libs/sonner.mjs";
import { C as Checkbox } from "./checkbox-BWLYw1JS.mjs";
import { R as Root, P as Portal, C as Content, a as Close, T as Title, D as Description, O as Overlay } from "../_libs/radix-ui__react-dialog.mjs";
import { c as Copy, r as Sparkles, H as HeartPulse, o as Clock, q as FileBraces, s as Share2, t as Download, M as Mail, e as ChevronDown, u as ChevronRight, i as Search, F as FileSearch, X } from "../_libs/lucide-react.mjs";
import "../_libs/class-variance-authority.mjs";
import "../_libs/clsx.mjs";
import "../_libs/tanstack__react-router.mjs";
import "../_libs/tanstack__router-core.mjs";
import "../_libs/tanstack__history.mjs";
import "../_libs/cookie-es.mjs";
import "../_libs/seroval.mjs";
import "../_libs/seroval-plugins.mjs";
import "node:stream/web";
import "node:stream";
import "../_libs/react-dom.mjs";
import "util";
import "crypto";
import "async_hooks";
import "stream";
import "../_libs/isbot.mjs";
import "../_libs/tanstack__query-core.mjs";
import "../_libs/tanstack__react-query.mjs";
import "../_libs/radix-ui__react-slot.mjs";
import "../_libs/radix-ui__react-compose-refs.mjs";
import "../_libs/tailwind-merge.mjs";
import "../_libs/radix-ui__react-separator.mjs";
import "../_libs/radix-ui__react-primitive.mjs";
import "../_libs/radix-ui__react-tooltip.mjs";
import "../_libs/radix-ui__primitive.mjs";
import "../_libs/radix-ui__react-context.mjs";
import "../_libs/@radix-ui/react-dismissable-layer+[...].mjs";
import "../_libs/@radix-ui/react-use-callback-ref+[...].mjs";
import "../_libs/@radix-ui/react-use-escape-keydown+[...].mjs";
import "../_libs/radix-ui__react-id.mjs";
import "../_libs/@radix-ui/react-use-layout-effect+[...].mjs";
import "../_libs/radix-ui__react-popper.mjs";
import "../_libs/floating-ui__react-dom.mjs";
import "../_libs/floating-ui__dom.mjs";
import "../_libs/floating-ui__core.mjs";
import "../_libs/floating-ui__utils.mjs";
import "../_libs/radix-ui__react-arrow.mjs";
import "../_libs/radix-ui__react-use-size.mjs";
import "../_libs/radix-ui__react-portal.mjs";
import "../_libs/radix-ui__react-presence.mjs";
import "../_libs/@radix-ui/react-use-controllable-state+[...].mjs";
import "../_libs/@radix-ui/react-visually-hidden+[...].mjs";
import "node:fs";
import "node:crypto";
import "node:path";
import "../_libs/radix-ui__react-focus-scope.mjs";
import "../_libs/radix-ui__react-focus-guards.mjs";
import "../_libs/react-remove-scroll.mjs";
import "tslib";
import "../_libs/react-remove-scroll-bar.mjs";
import "../_libs/react-style-singleton.mjs";
import "../_libs/get-nonce.mjs";
import "../_libs/use-sidecar.mjs";
import "../_libs/use-callback-ref.mjs";
import "../_libs/aria-hidden.mjs";
import "../_libs/radix-ui__react-checkbox.mjs";
import "../_libs/radix-ui__react-use-previous.mjs";
const Dialog = Root;
const DialogPortal = Portal;
const DialogOverlay = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  Overlay,
  {
    ref,
    className: cn(
      "fixed inset-0 z-50 bg-black/80  data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    ),
    ...props
  }
));
DialogOverlay.displayName = Overlay.displayName;
const DialogContent = reactExports.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsxs(DialogPortal, { children: [
  /* @__PURE__ */ jsxRuntimeExports.jsx(DialogOverlay, {}),
  /* @__PURE__ */ jsxRuntimeExports.jsxs(
    Content,
    {
      ref,
      className: cn(
        "fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 sm:rounded-lg",
        className
      ),
      ...props,
      children: [
        children,
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Close, { className: "absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background cursor-pointer transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(X, { className: "h-4 w-4" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "sr-only", children: "Close" })
        ] })
      ]
    }
  )
] }));
DialogContent.displayName = Content.displayName;
const DialogHeader = ({ className, ...props }) => /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: cn("flex flex-col space-y-1.5 text-center sm:text-left", className), ...props });
DialogHeader.displayName = "DialogHeader";
const DialogFooter = ({ className, ...props }) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  "div",
  {
    className: cn("flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2", className),
    ...props
  }
);
DialogFooter.displayName = "DialogFooter";
const DialogTitle = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  Title,
  {
    ref,
    className: cn("text-lg font-semibold leading-none tracking-tight", className),
    ...props
  }
));
DialogTitle.displayName = Title.displayName;
const DialogDescription = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  Description,
  {
    ref,
    className: cn("text-sm text-muted-foreground", className),
    ...props
  }
));
DialogDescription.displayName = Description.displayName;
const formats = [
  {
    id: "markdown",
    label: "Markdown (.md)",
    detail: "Optimized for ChatGPT, Claude, Codex, Gemini, and OpenClaw."
  },
  { id: "pdf", label: "PDF Report", detail: "Opens a print-ready executive report." },
  { id: "html", label: "HTML Report", detail: "Standalone report for archiving or sharing." },
  { id: "png", label: "Screenshot (.png)", detail: "Captures the current browser viewport." },
  { id: "diagnosis_json", label: "diagnosis.json", detail: "Exact diagnosis artifact." },
  { id: "session_json", label: "session.json", detail: "Exact session artifact when available." },
  {
    id: "zip",
    label: "ZIP bundle",
    detail: "Downloads diagnosis, session, and Markdown reports for selected runs."
  }
];
const asRecord = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : {};
const asArray = (value) => Array.isArray(value) ? value : [];
const asString = (value, fallback = "") => value == null ? fallback : String(value);
const asNumber = (value, fallback = 0) => {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
};
function ExportShareActions({
  defaultRunId,
  showShare = true
}) {
  const [runs, setRuns] = reactExports.useState([]);
  const [exportOpen, setExportOpen] = reactExports.useState(false);
  const [shareOpen, setShareOpen] = reactExports.useState(false);
  const [selected, setSelected] = reactExports.useState(/* @__PURE__ */ new Set());
  const [format, setFormat] = reactExports.useState("markdown");
  const [email, setEmail] = reactExports.useState("");
  reactExports.useEffect(() => {
    fetch("/api/runs").then((response) => response.json()).then((payload) => {
      const next = (Array.isArray(payload) ? payload : asArray(payload.runs)).filter(
        Boolean
      );
      setRuns(next);
      const defaultSelection = defaultRunId && next.some((run) => runId(run) === defaultRunId) ? [defaultRunId] : next.slice(0, 1).map(runId);
      setSelected(new Set(defaultSelection));
    }).catch(() => setRuns([]));
  }, [defaultRunId]);
  const selectedRuns = reactExports.useMemo(
    () => runs.filter((run) => selected.has(runId(run))),
    [runs, selected]
  );
  const selectedFormat = formats.find((item) => item.id === format) ?? formats[0];
  const toggleRun = (id) => {
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
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
      showShare && /* @__PURE__ */ jsxRuntimeExports.jsxs(Button, { variant: "outline", size: "sm", onClick: () => setShareOpen(true), children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Share2, { className: "size-4" }),
        " Share"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Button, { size: "sm", onClick: () => setExportOpen(true), children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Download, { className: "size-4" }),
        " Export"
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Dialog, { open: exportOpen, onOpenChange: setExportOpen, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(DialogContent, { className: "max-w-3xl", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(DialogHeader, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(DialogTitle, { children: "Export Runs" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(DialogDescription, { children: "Select runs, choose a format, preview the contents, then download." })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid gap-5 md:grid-cols-[1.2fr_.8fr]", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Button,
              {
                variant: "outline",
                size: "sm",
                onClick: () => setSelected(new Set(runs.map(runId))),
                children: "Select All"
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "ghost", size: "sm", onClick: () => setSelected(/* @__PURE__ */ new Set()), children: "Deselect All" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "max-h-[360px] space-y-2 overflow-auto pr-1", children: runs.map((run) => {
            const id = runId(run);
            return /* @__PURE__ */ jsxRuntimeExports.jsx(
              "button",
              {
                onClick: () => toggleRun(id),
                className: "w-full rounded-lg border bg-card p-3 text-left transition-colors hover:bg-accent",
                children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start gap-3", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx(Checkbox, { checked: selected.has(id), "aria-label": `Select ${id}` }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-w-0 flex-1", children: [
                    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "font-mono text-sm font-semibold", children: id }),
                    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-2 grid grid-cols-2 gap-2 text-xs text-muted-foreground", children: [
                      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                        "Trust: ",
                        trustScore(run)
                      ] }),
                      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { children: [
                        "Framework: ",
                        asString(run.framework, "openclaw")
                      ] }),
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: primaryDiagnosis(run) }),
                      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: runDate(run) })
                    ] })
                  ] })
                ] })
              },
              id
            );
          }) })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs font-medium uppercase tracking-widest text-muted-foreground", children: "Format" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-2", children: formats.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsxs(
            "button",
            {
              onClick: () => setFormat(item.id),
              className: `w-full rounded-lg border p-3 text-left text-sm transition-colors ${format === item.id ? "border-primary bg-primary/10" : "bg-card hover:bg-accent"}`,
              children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "font-medium", children: item.label }),
                /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-1 text-xs text-muted-foreground", children: item.detail })
              ]
            },
            item.id
          )) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "rounded-lg border bg-muted/20 p-3 text-sm", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "font-medium", children: "Export Preview" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-2 space-y-1 text-xs text-muted-foreground", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                "Runs Selected: ",
                selectedRuns.length
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                "Export Type: ",
                selectedFormat.label
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
                "Estimated File Size: ",
                estimatedSize(selectedRuns, format)
              ] }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: "Included Sections: Executive Summary, Agent Health, Diagnosis, Evidence, Timeline, Recommendations, Metadata" })
            ] })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(DialogFooter, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { variant: "outline", onClick: () => setExportOpen(false), children: "Cancel" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { onClick: runExport, disabled: !selectedRuns.length, children: "Download" })
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Dialog, { open: shareOpen, onOpenChange: setShareOpen, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(DialogContent, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(DialogHeader, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(DialogTitle, { children: "Sharing is administrator-controlled" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(DialogDescription, { children: "Critiqor does not create client-only links or invitations. Ask an administrator to grant a tenant-scoped viewer identity, then share the authenticated dashboard URL." })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "rounded-lg border bg-card p-4", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between gap-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "font-medium", children: "Public links unavailable" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm text-muted-foreground", children: "A URL alone never grants access to runtime evidence or exported diagnoses." })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "outline", children: "Disabled" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "rounded-lg border bg-card p-4", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "font-medium", children: "Invite by email" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-3 flex gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(
              Input,
              {
                value: email,
                onChange: (event) => setEmail(event.target.value),
                placeholder: "teammate@example.com",
                disabled: true
              }
            ),
            /* @__PURE__ */ jsxRuntimeExports.jsxs(Button, { disabled: true, children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(Mail, { className: "size-4" }),
              " Administrator required"
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-3 flex flex-wrap gap-2", children: /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm text-muted-foreground", children: "Invitations require an external identity provider and server-side audit trail." }) })
        ] })
      ] })
    ] }) })
  ] });
}
function runId(run) {
  return asString(run?.run_id, "");
}
function trustScore(run) {
  return asNumber(asRecord(run.executive_summary).trust_score, 0);
}
function primaryDiagnosis(run) {
  return asString(asRecord(run.primary_diagnosis).root_cause_failure_type, "Healthy Runtime") || "Healthy Runtime";
}
function runDate(run) {
  const trace = asArray(asRecord(run.evidence_panel).trace).map(asRecord);
  const first = trace.find((event) => event.timestamp || event.at);
  const value = asString(first?.timestamp ?? first?.at, "");
  return value ? new Date(value).toLocaleDateString() : "No date";
}
function estimatedSize(runs, format) {
  const bytes = JSON.stringify(runs).length;
  const multiplier = format === "pdf" || format === "html" ? 1.8 : format === "zip" ? 2.2 : 1;
  return `${Math.max(1, Math.round(bytes * multiplier / 1024))} KB`;
}
function buildExport(runs, format) {
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
        2
      )
    };
  if (format === "session_json")
    return {
      filename: "session.json",
      mime: "application/json",
      body: JSON.stringify(
        runs.map((run) => run.artifact_payloads?.session_json ?? {}),
        null,
        2
      )
    };
  return { filename: "Critiqor_Export.zip", mime: "application/zip", body: buildZip(runs) };
}
function renderMarkdown(runs) {
  return runs.map((run) => {
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
      causes.length ? "- Review required based on observed failure causes." : "- Healthy runtime profile. No runtime failure cause was detected.",
      "",
      "## Diagnosis",
      causes.length ? causes.map(
        (cause) => `- ${asString(cause.type, "runtime_failure")}: ${asString(cause.description, "")}`
      ).join("\n") : "- No primary runtime diagnosis.",
      "",
      "## Evidence",
      evidence.slice(0, 30).map(
        (event) => `- ${asString(event.timestamp ?? event.at, "")} ${asString(event.event ?? event.event_type ?? event.type, "log")}: ${asString(event.message ?? event.summary, JSON.stringify(event.payload ?? {}))}`
      ).join("\n") || "- No evidence events.",
      "",
      "## Runtime Timeline",
      evidence.slice(0, 50).map(
        (event) => `- ${asString(event.timestamp ?? event.at, "")}: ${asString(event.event ?? event.event_type ?? event.type, "event")}`
      ).join("\n") || "- No timeline events.",
      "",
      "## Root Cause Analysis",
      causes.map(
        (cause) => `- Root Cause: ${asString(cause.root_cause ?? cause.type, "")}
  - Impact: ${asNumber(cause.impact, 0)}
  - Recommendation: ${asString(cause.recommendation, asArray(cause.recommendations)[0] ?? "")}`
      ).join("\n") || "- No root cause detected.",
      "",
      "## Recommendations",
      asArray(run.recommendations).map((item) => `- ${String(item)}`).join("\n") || "- Continue monitoring future runs.",
      "",
      "## Supporting Metrics",
      `- Event Count: ${evidence.length}`,
      `- Tool Calls: ${asArray(asRecord(run.evidence_panel).tool_calls).length}`,
      `- Tool Outputs: ${asArray(asRecord(run.evidence_panel).tool_outputs).length}`
    ].join("\n");
  }).join("\n\n---\n\n");
}
function renderHtmlReport(runs) {
  const markdown = renderMarkdown(runs).replace(
    /[&<>]/g,
    (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[char] ?? char
  );
  return `<!doctype html><html><head><meta charset="utf-8"><title>Critiqor Report</title><style>body{font-family:Inter,Arial,sans-serif;max-width:900px;margin:48px auto;padding:0 24px;line-height:1.55;color:#0f172a}pre{white-space:pre-wrap;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:24px}</style></head><body><h1>Critiqor Report</h1><pre>${markdown}</pre></body></html>`;
}
function buildZip(runs) {
  const files = runs.flatMap((run) => {
    const id = runId(run);
    return [
      {
        name: `${id}/diagnosis.json`,
        body: JSON.stringify(run.artifact_payloads?.diagnosis_json ?? run, null, 2)
      },
      {
        name: `${id}/session.json`,
        body: JSON.stringify(run.artifact_payloads?.session_json ?? {}, null, 2)
      },
      { name: `${id}/diagnosis.md`, body: renderMarkdown([run]) }
    ];
  });
  return zipFiles(files);
}
function downloadFile(filename, body, mime) {
  const blob = body instanceof Blob ? body : new Blob([body], { type: mime });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
function openReportWindow(html) {
  const win = window.open("", "_blank");
  if (!win) return;
  win.document.write(html);
  win.document.close();
  win.focus();
  win.print();
}
function zipFiles(files) {
  const encoder = new TextEncoder();
  const localParts = [];
  const centralParts = [];
  let offset = 0;
  for (const file of files) {
    const name = encoder.encode(file.name);
    const data = encoder.encode(file.body);
    const crc = crc32(data);
    const local = concat([
      u32(67324752),
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
      data
    ]);
    const central2 = concat([
      u32(33639248),
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
      name
    ]);
    localParts.push(local);
    centralParts.push(central2);
    offset += local.length;
  }
  const central = concat(centralParts);
  const end = concat([
    u32(101010256),
    u16(0),
    u16(0),
    u16(files.length),
    u16(files.length),
    u32(central.length),
    u32(offset),
    u16(0)
  ]);
  return new Blob([concat([...localParts, central, end])], { type: "application/zip" });
}
function concat(parts) {
  const length = parts.reduce((sum, part) => sum + part.length, 0);
  const output = new Uint8Array(length);
  let cursor = 0;
  for (const part of parts) {
    output.set(part, cursor);
    cursor += part.length;
  }
  return output;
}
function u16(value) {
  const bytes = new Uint8Array(2);
  new DataView(bytes.buffer).setUint16(0, value, true);
  return bytes;
}
function u32(value) {
  const bytes = new Uint8Array(4);
  new DataView(bytes.buffer).setUint32(0, value >>> 0, true);
  return bytes;
}
function crc32(data) {
  let crc = 4294967295;
  for (const byte of data) {
    crc ^= byte;
    for (let i = 0; i < 8; i += 1) {
      crc = crc >>> 1 ^ 3988292384 & -(crc & 1);
    }
  }
  return (crc ^ 4294967295) >>> 0;
}
const evidenceTypeColor = {
  tool_call: "border-sky-500/30 text-sky-400 bg-sky-500/10",
  tool_output: "border-emerald-500/30 text-emerald-400 bg-emerald-500/10",
  memory: "border-violet-500/30 text-violet-400 bg-violet-500/10",
  retry: "border-orange-500/30 text-orange-400 bg-orange-500/10",
  log: "border-muted-foreground/30 text-muted-foreground bg-muted/40",
  metric: "border-cyan-500/30 text-cyan-400 bg-cyan-500/10",
  judge: "border-amber-500/30 text-amber-400 bg-amber-500/10",
  context: "border-pink-500/30 text-pink-400 bg-pink-500/10"
};
function DiagnosesPage() {
  const {
    diagnoses,
    executive,
    scoreExplanations,
    agentHealth,
    timeline,
    artifact,
    webmcp
  } = useCritiqor((s) => s);
  const runDiagnoses = reactExports.useMemo(() => diagnoses.filter((diagnosis) => diagnosis.runId === executive.runId), [diagnoses, executive.runId]);
  const [expanded, setExpanded] = reactExports.useState(/* @__PURE__ */ new Set());
  const [openCard, setOpenCard] = reactExports.useState(null);
  const tc = trustColor[executive.trustLevel];
  const primary = runDiagnoses.find((item) => item.findingId) ?? runDiagnoses[0];
  reactExports.useEffect(() => {
    setExpanded(new Set(primary ? [primary.id] : []));
    setOpenCard(null);
  }, [executive.runId, primary]);
  const fixPrompt = reactExports.useMemo(() => buildFixPrompt({
    runId: executive.runId,
    task: executive.task,
    summary: primary?.summary || executive.summary,
    severity: primary?.severity,
    confidence: primary?.confidence || webmcp.confidence,
    effectCount: webmcp.available ? webmcp.authoritativeEffectCount : void 0,
    duplicateCount: webmcp.available ? webmcp.duplicateEffectCount : void 0,
    sessionPath: artifact.sessionPath,
    diagnosisPath: artifact.diagnosisPath,
    playbookPath: artifact.playbookPath,
    evidence: (primary?.evidence ?? []).map((event) => {
      const payload = event.payload && typeof event.payload === "object" ? event.payload : {};
      return {
        sequence: payload.sequence_id,
        hash: payload.event_hash,
        message: event.message
      };
    }),
    rootCause: primary?.rootCause,
    causalChain: primary?.causalChain,
    recommendations: primary?.recommendedInvestigation ?? [],
    strengths: webmcp.strengths.map((item) => item.title).filter(Boolean),
    verification: primary?.verificationSteps ?? []
  }), [artifact, executive, primary, webmcp]);
  const copyFixPrompt = async () => {
    await navigator.clipboard.writeText(fixPrompt);
    toast.success("Run-specific fix prompt copied");
  };
  const toggle = (id) => {
    setExpanded((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(PageShell, { title: "Diagnosis", description: `Reliability assessment of the ${executive.agent} run — root causes, evidence, and causal analysis.`, actions: /* @__PURE__ */ jsxRuntimeExports.jsx(RunSelector, {}), children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex justify-end gap-2", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Button, { size: "sm", variant: "outline", onClick: copyFixPrompt, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Copy, { className: "size-4" }),
        "Copy Fix Prompt"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(ExportShareActions, { defaultRunId: executive.runId, showShare: false })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: `diagnosis-section relative overflow-hidden border border-emerald-300 bg-emerald-50 text-black ${tc.border}`, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `absolute inset-x-0 top-0 h-px ${tc.bg}` }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { className: "pb-3", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between gap-3 flex-wrap", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Sparkles, { className: "size-4 text-primary" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(CardTitle, { className: "text-base", children: "Executive Summary" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "outline", className: `${tc.border} ${tc.text} ${tc.bg}`, children: tc.label })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "grid lg:grid-cols-4 gap-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(SummaryStat, { label: "Trust Score", value: `${executive.trustScore}`, suffix: "/100", level: executive.trustLevel, selected: openCard === "exec-trust", onOpen: () => setOpenCard("exec-trust") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(SummaryStat, { label: "Critiqor Confidence", value: `${executive.confidence}`, suffix: "%", level: "high", selected: openCard === "exec-confidence", onOpen: () => setOpenCard("exec-confidence") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(SummaryStat, { label: "Verdict", value: executive.verdict, level: executive.trustLevel, text: true, selected: openCard === "exec-verdict", onOpen: () => setOpenCard("exec-verdict") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(SummaryStat, { label: "Run", value: executive.runId, sub: executive.agent, level: "high", text: true, selected: openCard === "exec-run", onOpen: () => setOpenCard("exec-run") }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { type: "button", className: `lg:col-span-4 rounded-lg border bg-white p-3 pt-2 text-left transition-colors hover:border-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${openCard === "exec-task" ? "border-emerald-500 ring-2 ring-emerald-300" : ""}`, "aria-expanded": openCard === "exec-task", onClick: () => setOpenCard("exec-task"), children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs uppercase tracking-widest text-muted-foreground mb-1", children: "Agent attempt" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-medium", children: executive.task || "Not captured" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-muted-foreground mt-1", children: executive.summary || "More evidence needed" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "lg:col-span-4 grid md:grid-cols-3 gap-2 pt-2", children: executive.evidence.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsx(EvidenceMetric, { label: item.label, value: item.value, detail: item.detail, selected: openCard === `exec-metric-${item.label}`, onOpen: () => setOpenCard(`exec-metric-${item.label}`) }, item.label)) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { type: "button", className: `lg:col-span-4 rounded-lg border bg-white p-3 text-left transition-colors hover:border-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${openCard === "exec-why" ? "border-emerald-500 ring-2 ring-emerald-300" : ""}`, "aria-expanded": openCard === "exec-why", onClick: () => setOpenCard("exec-why"), children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] uppercase tracking-widest text-muted-foreground mb-1", children: "Why Critiqor is confident" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-muted-foreground", children: executive.confidenceReasoning || "More evidence needed" })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(PrimaryDiagnosisList, { runDiagnoses, expanded, toggle }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("section", { "aria-labelledby": "engineer-brief-title", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: "diagnosis-section border-sky-300 bg-sky-50 text-black", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { className: "pb-3", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-wrap items-center justify-between gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(CardTitle, { id: "engineer-brief-title", className: "text-base", children: "Engineer Brief" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-sm text-muted-foreground", children: "Evidence → conclusion → action, with uncertainty kept visible. Open a card for the selected run's full evidence." })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Badge, { variant: "outline", className: `${tc.border} ${tc.text} ${tc.bg}`, children: [
          "Verdict: ",
          executive.verdict
        ] })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "grid gap-3 md:grid-cols-2 lg:grid-cols-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Primary Diagnosis", value: primary?.title || "Not captured", selected: openCard === "primary", onOpen: () => setOpenCard("primary") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Root Cause", value: primary?.rootCause || "Not captured", selected: openCard === "root", onOpen: () => setOpenCard("root") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Evidence", value: primary?.evidence[0]?.message || (artifact.eventCount ? `${artifact.eventCount} events captured` : "Not captured"), detail: `${primary?.evidence.length ?? 0} linked events · ${artifact.evidenceStatus}`, selected: openCard === "evidence", onOpen: () => setOpenCard("evidence") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Impact", value: primary?.confirmedImpact || (primary ? `${primary.severity} severity` : "Not captured"), selected: openCard === "impact", onOpen: () => setOpenCard("impact") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Improvement Plan", value: primary?.recommendedInvestigation[0] || "Not captured", selected: openCard === "plan", onOpen: () => setOpenCard("plan") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Expected Improvement", value: primary?.expectedImprovement || "Not captured", selected: openCard === "expected", onOpen: () => setOpenCard("expected") })
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: "diagnosis-section border-violet-300 bg-violet-50 text-black", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { className: "pb-3", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(HeartPulse, { className: "size-4 text-emerald-400" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(CardTitle, { className: "text-base", children: "Agent Health" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "grid md:grid-cols-3 gap-4", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Overall Health", value: agentHealth.status || "Not captured", selected: openCard === "health-status", onOpen: () => setOpenCard("health-status") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Strengths", value: agentHealth.strengths[0] || "Not captured", detail: agentHealth.strengths.length ? `${agentHealth.strengths.length} observed` : "Not captured", selected: openCard === "health-strengths", onOpen: () => setOpenCard("health-strengths") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Recommended Monitoring", value: agentHealth.recommendedMonitoring[0] || "Not captured", selected: openCard === "health-monitoring", onOpen: () => setOpenCard("health-monitoring") }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(BriefCard, { label: "Stable Behaviours", value: agentHealth.stableBehaviours[0] || "Not captured", selected: openCard === "health-stable", onOpen: () => setOpenCard("health-stable") })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(SectionDetailDialog, { card: openCard, onClose: () => setOpenCard(null), primary, artifact, runId: executive.runId, executive, agentHealth, webmcp, scoreExplanations }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: "diagnosis-section border-amber-300 bg-amber-50 text-black", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { className: "pb-3", children: /* @__PURE__ */ jsxRuntimeExports.jsx(CardTitle, { className: "text-base", children: "Why Each Score Received Its Value" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardContent, { className: "space-y-3", children: scoreExplanations.map((score) => /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { type: "button", className: `w-full space-y-3 rounded-lg border bg-white p-4 text-left transition-colors hover:border-amber-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 ${openCard === `score-${score.score}` ? "border-amber-500 ring-2 ring-amber-300" : ""}`, "aria-expanded": openCard === `score-${score.score}`, onClick: () => setOpenCard(`score-${score.score}`), children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start justify-between gap-3 flex-wrap", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-semibold", children: score.score }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-muted-foreground mt-1", children: score.why })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-right", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "outline", children: score.tier }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-semibold tabular-nums mt-1", children: score.value })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "grid md:grid-cols-3 gap-2", children: score.evidence.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsx(EvidenceMetric, { label: item.label, value: item.value, detail: item.detail }, `${score.score}-${item.label}`)) })
      ] }, score.score)) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: "diagnosis-section border-cyan-300 bg-cyan-50 text-black", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(CardHeader, { className: "flex-row items-center justify-between gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(CardTitle, { className: "text-base font-bold", children: "Copy Fix Prompt" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-sm text-black/75", children: "Generated from the selected run's diagnosis, evidence, improvements, and verification steps." })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Button, { size: "sm", variant: "outline", onClick: copyFixPrompt, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Copy, { className: "size-4" }),
          " Copy"
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardContent, { children: /* @__PURE__ */ jsxRuntimeExports.jsx("pre", { className: "max-h-[460px] overflow-auto whitespace-pre-wrap rounded-lg border border-slate-300 bg-white p-4 font-mono text-sm leading-relaxed text-black", children: fixPrompt }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid lg:grid-cols-2 gap-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: "diagnosis-section border-rose-300 bg-rose-50 text-black", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { className: "pb-3", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Clock, { className: "size-4 text-sky-400" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(CardTitle, { className: "text-base", children: "Runtime Timeline" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(CardContent, { className: "space-y-2 max-h-[420px] overflow-auto", children: timeline.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-3 rounded-lg border bg-white p-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-1 size-2 rounded-full bg-primary shrink-0" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-w-0", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm font-medium", children: item.label }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-muted-foreground font-mono", children: [
              new Date(item.at).toLocaleString(),
              " · ",
              item.type
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm text-muted-foreground mt-1", children: item.detail })
          ] })
        ] }, item.id)) })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: "diagnosis-section border-indigo-300 bg-indigo-50 text-black", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { className: "pb-3", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(FileBraces, { className: "size-4 text-amber-400" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(CardTitle, { className: "text-base", children: "Diagnosis Artifact & Session Metadata" })
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "space-y-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(InfoBlock, { label: "Diagnosis Artifact", body: /* @__PURE__ */ jsxRuntimeExports.jsx("code", { className: `text-xs break-all ${(artifact.diagnosisPath ?? "").includes("Hidden for anonymous") ? "select-none blur-sm" : ""}`, children: artifact.diagnosisPath || "Not provided" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(InfoBlock, { label: "Session Artifact", body: /* @__PURE__ */ jsxRuntimeExports.jsx("code", { className: `text-xs break-all ${(artifact.sessionPath ?? "").includes("Hidden for anonymous") ? "select-none blur-sm" : ""}`, children: artifact.sessionPath || "Not available" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(InfoBlock, { label: "Improvement Playbook", body: /* @__PURE__ */ jsxRuntimeExports.jsx("code", { className: "text-xs break-all", children: artifact.playbookPath || "Not available" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-2 gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(EvidenceMetric, { label: "Events", value: `${artifact.eventCount}`, detail: "Runtime events in the selected run." }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(EvidenceMetric, { label: "Tools", value: `${artifact.toolCallCount}`, detail: "Tool calls observed." }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(EvidenceMetric, { label: "Outputs", value: `${artifact.toolOutputCount}`, detail: "Tool outputs observed." }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(EvidenceMetric, { label: "Duration", value: `${(artifact.durationMs / 1e3).toFixed(1)}s`, detail: "Observed runtime duration." })
          ] })
        ] })
      ] })
    ] })
  ] });
}
function EvidenceMetric({
  label,
  value,
  detail,
  selected,
  onOpen
}) {
  const className = `rounded-lg border bg-white p-3 text-left ${onOpen ? `transition-colors hover:border-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${selected ? "border-emerald-500 ring-2 ring-emerald-300" : ""}` : ""}`;
  const body = /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] uppercase tracking-widest text-muted-foreground", children: label }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-lg font-semibold tabular-nums mt-1", children: value }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-xs text-muted-foreground mt-1", children: detail || "Not captured" })
  ] });
  if (!onOpen) return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className, children: body });
  return /* @__PURE__ */ jsxRuntimeExports.jsx("button", { type: "button", className: `w-full ${className}`, "aria-expanded": selected, onClick: onOpen, children: body });
}
function BriefCard({
  label,
  value,
  detail,
  selected,
  onOpen
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("button", { type: "button", onClick: onOpen, "aria-expanded": selected, className: `rounded-lg border bg-white p-4 text-left transition-colors hover:border-sky-400 hover:bg-sky-50/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 ${selected ? "border-sky-500 ring-2 ring-sky-300" : ""}`, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "text-[11px] font-semibold uppercase tracking-widest text-muted-foreground", children: label }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-2 text-sm font-medium leading-relaxed", children: value }),
    detail && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-xs text-muted-foreground", children: detail })
  ] });
}
function SectionDetailDialog({
  card,
  onClose,
  primary,
  artifact,
  runId: runId2,
  executive,
  agentHealth,
  webmcp,
  scoreExplanations
}) {
  const titles = {
    primary: "Primary Diagnosis",
    root: "Root Cause",
    evidence: "Evidence",
    impact: "Impact",
    plan: "Improvement Plan",
    expected: "Expected Improvement",
    "exec-trust": "Trust Score",
    "exec-confidence": "Critiqor Confidence",
    "exec-verdict": "Verdict",
    "exec-run": "Run",
    "exec-task": "Agent attempt",
    "exec-why": "Why Critiqor is confident",
    "health-status": "Overall Health",
    "health-strengths": "Strengths",
    "health-monitoring": "Recommended Monitoring",
    "health-stable": "Stable Behaviours"
  };
  const metric = card?.startsWith("exec-metric-") ? executive.evidence.find((item) => `exec-metric-${item.label}` === card) : void 0;
  const scoreCard = card?.startsWith("score-") ? card.slice("score-".length) : "";
  const copy = async (value, label) => {
    await navigator.clipboard.writeText(value);
    toast.success(label);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(Dialog, { open: Boolean(card), onOpenChange: (open) => !open && onClose(), children: /* @__PURE__ */ jsxRuntimeExports.jsxs(DialogContent, { className: "max-h-[85vh] max-w-2xl overflow-auto", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs(DialogHeader, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(DialogTitle, { children: [
        card ? titles[card] ?? metric?.label ?? scoreCard ?? "Diagnosis detail" : "Diagnosis detail",
        " ",
        "· ",
        runId2
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(DialogDescription, { children: "In-depth view for the selected run. Missing fields stay unavailable." })
    ] }),
    card === "primary" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "font-medium", children: primary?.title || "Not captured" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: primary?.summary || "More evidence needed" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Severity: ",
        primary?.severity || "Not captured"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Confidence: ",
        primary?.confidence || "More evidence needed"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Root cause: ",
        primary?.rootCause || "Not captured"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: primary?.causalChain?.length ? primary.causalChain : ["Not captured"] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Counterevidence:",
        " ",
        primary?.counterEvidence.length ? primary.counterEvidence.map((item) => item.message).join("; ") : "None supplied"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Alternatives: ",
        primary?.alternativeHypotheses.join("; ") || "None evaluated"
      ] })
    ] }),
    card === "root" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: primary?.rootCause || "Not captured" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Why alternatives were rejected:",
        " ",
        primary?.alternativeHypotheses.join("; ") || "Not captured"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: primary?.causalChain ?? ["Not captured"] })
    ] }),
    card === "evidence" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      (primary?.evidence ?? []).map((event) => {
        const payload = event.payload && typeof event.payload === "object" ? event.payload : {};
        return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "rounded-md border p-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { children: event.message }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-1 font-mono text-xs text-muted-foreground", children: [
            "sequence ",
            String(payload.sequence_id ?? "Not captured"),
            " · hash",
            " ",
            String(payload.event_hash ?? "Not captured"),
            " · ",
            event.at
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { size: "sm", variant: "outline", className: "mt-2", onClick: () => copy(`sequence ${String(payload.sequence_id ?? "")} ${String(payload.event_hash ?? "")}`, "Evidence reference copied"), children: "Copy evidence reference" })
        ] }, event.id);
      }),
      !primary?.evidence.length && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Not captured" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { size: "sm", variant: "outline", onClick: () => copy(artifact.sessionPath || "", "Session path copied"), children: "Copy session path" })
    ] }),
    card === "impact" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Confirmed: ",
        primary?.confirmedImpact || "Not captured"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Potential: ",
        primary?.potentialImpact || "Not captured"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Trust impact: ",
        primary ? `-${primary.trustImpact}` : "Not captured"
      ] })
    ] }),
    card === "plan" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: primary?.recommendedInvestigation.length ? primary.recommendedInvestigation : ["Not captured"] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Playbook: ",
        artifact.playbookPath || "Not available"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { size: "sm", variant: "outline", onClick: () => copy(artifact.playbookPath || "", "Playbook path copied"), children: "Copy playbook path" })
    ] }),
    card === "expected" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: primary?.expectedImprovement || "Not captured" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: primary?.verificationSteps.length ? primary.verificationSteps : ["Not captured"] })
    ] }),
    card === "exec-trust" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Trust score: ",
        executive.trustScore,
        "/100 · ",
        executive.trustLevel || "Not captured"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "This value comes from the selected run's executive summary, not a dashboard default." }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: executive.evidence.length ? executive.evidence.map((item) => `${item.label}: ${item.value}`) : ["Not captured"] })
    ] }),
    card === "exec-confidence" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Confidence: ",
        executive.confidence || "More evidence needed"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: executive.confidenceReasoning || "More evidence needed" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "WebMCP confidence: ",
        webmcp.confidence || "Not captured"
      ] })
    ] }),
    card === "exec-verdict" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Verdict: ",
        executive.verdict || "More evidence needed"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "WebMCP status: ",
        webmcp.available ? webmcp.displayStatus : "Not exercised"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Findings: ",
        webmcp.available ? webmcp.findingCount : "Not captured",
        " · Duplicate effects: ",
        webmcp.available ? webmcp.duplicateEffectCount : "Not captured"
      ] })
    ] }),
    card === "exec-run" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Run: ",
        executive.runId || "Not available"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Agent: ",
        executive.agent || "Not captured"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Session: ",
        artifact.sessionPath || "Not available"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Diagnosis: ",
        artifact.diagnosisPath || "Not available"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Playbook: ",
        artifact.playbookPath || "Not available"
      ] })
    ] }),
    card === "exec-task" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "font-medium", children: executive.task || "Not captured" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: executive.summary || "More evidence needed" })
    ] }),
    card === "exec-why" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: executive.confidenceReasoning || "More evidence needed" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Evidence status: ",
        artifact.evidenceStatus || "unknown"
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "Events in selected run: ",
        artifact.eventCount
      ] })
    ] }),
    metric && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "font-medium", children: metric.label }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: metric.value || "Not captured" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: metric.detail || "More evidence needed" })
    ] }),
    card === "health-status" && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3 text-sm", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: agentHealth.status || "Not captured" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { children: [
        "This status is derived from the selected run",
        webmcp.available ? ` and WebMCP ${webmcp.displayStatus}` : "",
        "."
      ] })
    ] }),
    card === "health-strengths" && /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: agentHealth.strengths.length ? agentHealth.strengths : ["Not captured"] }),
    card === "health-monitoring" && /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: agentHealth.recommendedMonitoring.length ? agentHealth.recommendedMonitoring : ["Not captured"] }),
    card === "health-stable" && /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: agentHealth.stableBehaviours.length ? agentHealth.stableBehaviours : ["Not captured"] }),
    scoreCard && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-3 text-sm", children: (() => {
      const score = scoreExplanations.find((item) => item.score === scoreCard);
      if (!score) return /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Not captured" });
      return /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "font-medium", children: [
          score.score,
          ": ",
          score.value || "Not captured"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: score.tier || "Not captured" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: score.why || "More evidence needed" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: score.evidence.length ? score.evidence.map((item) => `${item.label}: ${item.value}`) : ["Not captured"] })
      ] });
    })() })
  ] }) });
}
function PrimaryDiagnosisList({
  runDiagnoses,
  expanded,
  toggle
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "space-y-3", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center justify-between", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "text-sm font-semibold uppercase tracking-widest text-muted-foreground", children: "Primary Diagnosis" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "text-xs font-semibold text-black", children: [
        runDiagnoses.length,
        " findings"
      ] })
    ] }),
    runDiagnoses.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { className: "border-dashed", children: /* @__PURE__ */ jsxRuntimeExports.jsx(CardContent, { className: "py-10 text-center text-sm text-muted-foreground", children: "No diagnosis was present in the selected run artifacts." }) }),
    runDiagnoses.map((d) => {
      const sc = severityColor[d.severity];
      const isOpen = expanded.has(d.id);
      return /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: `diagnosis-section relative overflow-hidden border-l-2 bg-orange-50 text-black ${sc.border} transition-all hover:shadow-md`, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `absolute inset-y-0 left-0 w-1 ${sc.dot}` }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: () => toggle(d.id), className: "w-full text-left", "aria-expanded": isOpen, "aria-controls": `diagnosis-${d.id}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { className: "pb-3", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start justify-between gap-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start gap-3 min-w-0", children: [
            isOpen ? /* @__PURE__ */ jsxRuntimeExports.jsx(ChevronDown, { className: "size-4 mt-1 text-muted-foreground" }) : /* @__PURE__ */ jsxRuntimeExports.jsx(ChevronRight, { className: "size-4 mt-1 text-muted-foreground" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-w-0", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(CardTitle, { className: "text-base", children: d.title }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-muted-foreground mt-1", children: d.summary })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex items-center gap-2 shrink-0", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "outline", className: `${sc.border} ${sc.text} ${sc.bg} capitalize`, children: d.severity }) })
        ] }) }) }),
        isOpen && /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { id: `diagnosis-${d.id}`, className: "space-y-5 pt-0", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid md:grid-cols-2 gap-4", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(InfoBlock, { label: "Root Cause Impact", body: d.rootCause }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(InfoBlock, { label: "Recommended Investigation", body: d.recommendedInvestigation.length ? /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { className: "space-y-1.5 text-sm", children: d.recommendedInvestigation.map((r, i) => /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex gap-2", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(Search, { className: "size-3.5 mt-0.5 text-muted-foreground shrink-0" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: r })
            ] }, i)) }) : "Not captured" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(InfoBlock, { label: "Verify the Fix", body: d.verificationSteps.length ? /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: d.verificationSteps }) : "Not captured" })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(SectionLabel, { icon: /* @__PURE__ */ jsxRuntimeExports.jsx(FileSearch, { className: "size-3.5" }), children: "Supporting Evidence" }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "divide-y rounded-lg border bg-white", children: [
              d.evidence.map((e) => /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-start gap-3 p-3", children: [
                /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "outline", className: `${evidenceTypeColor[e.type]} font-mono text-[10px] shrink-0`, children: e.type }),
                /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-w-0 flex-1", children: [
                  /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm", children: e.message }),
                  /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-muted-foreground mt-0.5 font-mono", children: [
                    e.at,
                    " · ",
                    d.runId
                  ] })
                ] })
              ] }, e.id)),
              !d.evidence.length && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "p-3 text-sm text-muted-foreground", children: "Not captured" })
            ] })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid md:grid-cols-2 gap-4", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(InfoBlock, { label: "Counterevidence", body: d.counterEvidence.length ? /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: d.counterEvidence.map((event) => event.message) }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-muted-foreground", children: "No counterevidence was supplied." }) }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(InfoBlock, { label: "Alternative hypotheses", body: d.alternativeHypotheses.length ? /* @__PURE__ */ jsxRuntimeExports.jsx(BulletList, { items: d.alternativeHypotheses }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-muted-foreground", children: "No competing hypothesis was evaluated." }) })
          ] })
        ] })
      ] }, d.id);
    })
  ] });
}
function BulletList({
  items
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { className: "space-y-1 text-sm", children: items.map((item, i) => /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "text-muted-foreground", children: [
    "• ",
    item
  ] }, i)) });
}
function InfoBlock({
  label,
  body
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "rounded-lg border bg-white p-4", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] uppercase tracking-widest text-muted-foreground mb-2", children: label }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm", children: body })
  ] });
}
function SectionLabel({
  children,
  icon
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-[10px] uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-1.5", children: [
    icon,
    children
  ] });
}
function SummaryStat({
  label,
  value,
  suffix,
  sub,
  level,
  text,
  selected,
  onOpen
}) {
  const tc = trustColor[level];
  const className = `rounded-lg border bg-white ${tc.border} p-3 text-left ${onOpen ? `transition-colors hover:border-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${selected ? "ring-2 ring-emerald-300" : ""}` : ""}`;
  const body = /* @__PURE__ */ jsxRuntimeExports.jsxs(jsxRuntimeExports.Fragment, { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] uppercase tracking-widest text-muted-foreground", children: label }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `mt-1 ${text ? "text-base font-semibold" : "text-2xl font-semibold tabular-nums"} ${tc.text}`, children: [
      value || "Not captured",
      suffix && /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-sm text-muted-foreground ml-0.5", children: suffix })
    ] }),
    sub && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[11px] text-muted-foreground mt-0.5 font-mono truncate", children: sub })
  ] });
  if (!onOpen) return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className, children: body });
  return /* @__PURE__ */ jsxRuntimeExports.jsx("button", { type: "button", className, "aria-expanded": selected, onClick: onOpen, children: body });
}
export {
  DiagnosesPage as component
};
