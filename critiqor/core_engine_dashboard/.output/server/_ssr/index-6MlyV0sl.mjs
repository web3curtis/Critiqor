import { r as reactExports, j as jsxRuntimeExports } from "../_libs/react.mjs";
import { L as Link } from "../_libs/tanstack__react-router.mjs";
import { P as PageShell, C as Card, a as CardContent, b as CardHeader, c as CardTitle, B as Badge } from "./card-CBpR56_E.mjs";
import { u as useCritiqor } from "./router-Cv4vvrPJ.mjs";
import "../_libs/sonner.mjs";
import { z as TriangleAlert, l as CircleCheck, I as ArrowRight, J as ExternalLink, b as Earth, S as Stethoscope, W as Wrench, n as Gauge, F as FileSearch, K as TrendingUp, N as ClipboardCheck, O as TrendingDown } from "../_libs/lucide-react.mjs";
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
import "../_libs/class-variance-authority.mjs";
import "../_libs/clsx.mjs";
import "../_libs/tanstack__query-core.mjs";
import "../_libs/tanstack__react-query.mjs";
import "../_libs/radix-ui__react-slot.mjs";
import "../_libs/radix-ui__react-compose-refs.mjs";
import "../_libs/tailwind-merge.mjs";
import "../_libs/radix-ui__react-separator.mjs";
import "../_libs/radix-ui__react-primitive.mjs";
import "../_libs/radix-ui__react-dialog.mjs";
import "../_libs/radix-ui__primitive.mjs";
import "../_libs/radix-ui__react-context.mjs";
import "../_libs/radix-ui__react-id.mjs";
import "../_libs/@radix-ui/react-use-layout-effect+[...].mjs";
import "../_libs/@radix-ui/react-use-controllable-state+[...].mjs";
import "../_libs/@radix-ui/react-dismissable-layer+[...].mjs";
import "../_libs/@radix-ui/react-use-callback-ref+[...].mjs";
import "../_libs/@radix-ui/react-use-escape-keydown+[...].mjs";
import "../_libs/radix-ui__react-focus-scope.mjs";
import "../_libs/radix-ui__react-portal.mjs";
import "../_libs/radix-ui__react-presence.mjs";
import "../_libs/radix-ui__react-focus-guards.mjs";
import "../_libs/react-remove-scroll.mjs";
import "tslib";
import "../_libs/react-remove-scroll-bar.mjs";
import "../_libs/react-style-singleton.mjs";
import "../_libs/get-nonce.mjs";
import "../_libs/use-sidecar.mjs";
import "../_libs/use-callback-ref.mjs";
import "../_libs/aria-hidden.mjs";
import "../_libs/radix-ui__react-tooltip.mjs";
import "../_libs/radix-ui__react-popper.mjs";
import "../_libs/floating-ui__react-dom.mjs";
import "../_libs/floating-ui__dom.mjs";
import "../_libs/floating-ui__core.mjs";
import "../_libs/floating-ui__utils.mjs";
import "../_libs/radix-ui__react-arrow.mjs";
import "../_libs/radix-ui__react-use-size.mjs";
import "../_libs/@radix-ui/react-visually-hidden+[...].mjs";
import "node:fs";
import "node:crypto";
import "node:path";
const verdicts = {
  high: {
    title: "Production Ready",
    detail: "Suitable for production deployment.",
    icon: CircleCheck,
    style: "border-emerald-500/35 bg-emerald-500/[0.07]",
    text: "text-emerald-600 dark:text-emerald-400"
  },
  medium: {
    title: "Needs Improvement Before Production",
    detail: "Deploy only after addressing the identified issues.",
    icon: TriangleAlert,
    style: "border-amber-500/35 bg-amber-500/[0.07]",
    text: "text-amber-700 dark:text-amber-400"
  },
  low: {
    title: "Not Ready For Production",
    detail: "Major runtime issues detected. Deployment is not recommended.",
    icon: TriangleAlert,
    style: "border-red-500/35 bg-red-500/[0.07]",
    text: "text-red-700 dark:text-red-400"
  }
};
function Overview() {
  const {
    executive,
    diagnoses,
    runs,
    webmcp
  } = useCritiqor((state) => state);
  const [dashboardUrl, setDashboardUrl] = reactExports.useState("");
  reactExports.useEffect(() => setDashboardUrl(window.location.href), []);
  const primary = diagnoses.find((diagnosis) => diagnosis.runId === executive.runId);
  const current = runs.find((run) => run.id === executive.runId);
  const previous = current?.webmcpComparison ? runs.find((run) => run.id !== current.id && run.webmcpStatus) : current ? runs.filter((run) => Date.parse(run.startedAt) < Date.parse(current.startedAt)).sort((a, b) => b.startedAt.localeCompare(a.startedAt))[0] : void 0;
  const verdict = verdicts[executive.trustLevel];
  const VerdictIcon = verdict.icon;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(PageShell, { title: "Overview", description: "Can I trust my agent in production?", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { className: `overflow-hidden ${verdict.style}`, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "grid gap-6 p-6 xl:grid-cols-[1fr_auto] xl:items-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: `mb-3 flex items-center gap-2 text-sm font-semibold ${verdict.text}`, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(VerdictIcon, { className: "size-5" }),
          " Agent status"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: `text-3xl font-bold tracking-tight ${verdict.text}`, children: verdict.title }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-2 text-sm font-medium", children: verdict.detail }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground", children: executive.summary }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Link, { to: "/diagnoses", search: {
          run_id: executive.runId
        }, className: "mt-4 inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline", children: [
          "Open Primary Diagnosis ",
          /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowRight, { className: "size-4" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid grid-cols-3 gap-5 border-t pt-5 xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Metric, { label: "Trust", value: `${executive.trustScore}/100` }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Metric, { label: "Confidence", value: `${executive.confidence}%` }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Metric, { label: "Run", value: executive.runId, mono: true })
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { className: "bg-card/70", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "flex flex-wrap items-center gap-3 px-4 py-3", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "rounded-md bg-primary/10 p-2 text-primary", children: /* @__PURE__ */ jsxRuntimeExports.jsx(ExternalLink, { className: "size-4" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-w-0", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs font-semibold uppercase tracking-wider text-muted-foreground", children: "Dashboard URL" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("code", { className: "block truncate text-sm", children: dashboardUrl || "Loading current URL…" })
      ] })
    ] }) }),
    webmcp.available && /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: webmcp.status === "FINDING" ? "border-red-500/35" : webmcp.status === "PASSED" ? "border-emerald-500/35" : webmcp.status === "INCONCLUSIVE" ? "border-amber-500/35" : "border-muted", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-wrap items-center justify-between gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(CardTitle, { className: "flex items-center gap-2 text-base", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Earth, { className: "size-4 text-primary" }),
          "WebMCP"
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: webmcp.status === "FINDING" ? "destructive" : "outline", children: webmcp.displayStatus })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm leading-relaxed text-muted-foreground", children: webmcp.summary }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-4 grid gap-3 sm:grid-cols-5", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Metric, { label: "Scenarios", value: String(webmcp.scenariosExercised) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(Metric, { label: "Findings", value: String(webmcp.findingCount) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(Metric, { label: "Authoritative effects", value: String(webmcp.authoritativeEffectCount) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(Metric, { label: "Duplicate effects", value: String(webmcp.duplicateEffectCount) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(Metric, { label: "Strengths", value: String(webmcp.strengths.length) })
        ] }),
        webmcp.strengths.length > 0 && /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-4 flex flex-wrap gap-2", children: webmcp.strengths.map((strength) => /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "secondary", title: strength.detail, children: strength.title }, strength.id)) })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid gap-4 lg:grid-cols-[1.2fr_.8fr]", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardTitle, { className: "flex items-center gap-2 text-base", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Stethoscope, { className: "size-4 text-primary" }),
          "Biggest runtime issue"
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h3", { className: "font-semibold", children: primary?.title ?? "No dominant runtime issue detected" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-2 text-sm leading-relaxed text-muted-foreground", children: primary?.summary ?? "Continue monitoring representative production scenarios to increase confidence." }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-4 flex flex-wrap gap-2", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "outline", children: primary ? `${primary.severity} severity` : "No finding" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "outline", children: primary ? `${primary.evidence.length} linked events` : "Evidence monitored" })
          ] })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardTitle, { className: "flex items-center gap-2 text-base", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Wrench, { className: "size-4 text-primary" }),
          "Next action"
        ] }) }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm leading-relaxed", children: primary?.recommendedInvestigation[0] || "Not captured" }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(Link, { to: "/playbook", search: {
            run_id: executive.runId
          }, className: "mt-4 inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline", children: [
            "Open run-specific Playbook ",
            /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowRight, { className: "size-4" })
          ] })
        ] })
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardTitle, { className: "flex items-center gap-2 text-base", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Gauge, { className: "size-4 text-primary" }),
        "Did the change work?"
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardContent, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(RunComparison, { current, previous }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid gap-3 md:grid-cols-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(GoalLink, { to: "/diagnoses", runId: executive.runId, icon: Stethoscope, title: "Why?", detail: "Review the diagnosis" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(GoalLink, { to: "/evidence", runId: executive.runId, icon: FileSearch, title: "Show me the evidence", detail: "Inspect raw runtime events" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(GoalLink, { to: "/playbook", runId: executive.runId, icon: Wrench, title: "What should I change?", detail: "Follow the implementation plan" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(GoalLink, { to: "/runs", runId: executive.runId, icon: TrendingUp, title: "Did it improve?", detail: "Compare completed runs" })
    ] })
  ] });
}
function Metric({
  label,
  value,
  mono
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] font-semibold uppercase tracking-widest text-muted-foreground", children: label }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `mt-1 max-w-32 truncate text-base font-semibold ${mono ? "font-mono text-xs" : ""}`, title: value, children: value })
  ] });
}
function GoalLink({
  to,
  runId,
  icon: Icon,
  title,
  detail
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(Link, { to, search: runId ? {
    run_id: runId
  } : void 0, className: "group rounded-xl border bg-card p-4 transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(Icon, { className: "size-5 text-primary" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-3 font-semibold", children: title }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-1 text-xs text-muted-foreground", children: detail }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowRight, { className: "mt-3 size-4 text-muted-foreground transition-transform group-hover:translate-x-1" })
  ] });
}
function RunComparison({
  current,
  previous
}) {
  if (!current) return /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "text-sm text-muted-foreground", children: "Finalize a run to begin measuring improvement." });
  if (!previous) return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "rounded-lg border border-dashed p-6 text-center", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(ClipboardCheck, { className: "mx-auto size-5 text-muted-foreground" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-2 font-medium", children: "This is the first recorded observation session." })
  ] });
  if (current.webmcpComparison) return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-wrap items-center gap-4", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-muted-foreground", children: "WebMCP matched rerun" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-1 text-2xl font-semibold", children: current.webmcpComparison }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-1 text-sm text-muted-foreground", children: [
        previous.webmcpFindings ?? 0,
        " finding(s) before · ",
        current.webmcpFindings ?? 0,
        " after"
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "outline", className: "text-emerald-600 dark:text-emerald-400", children: "Same task and response-loss adversity" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/runs", className: "ml-auto text-sm font-semibold text-primary hover:underline", children: "Compare runs" })
  ] });
  const delta = current.trustScore - previous.trustScore;
  const Icon = delta >= 0 ? TrendingUp : TrendingDown;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-wrap items-center gap-4", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-muted-foreground", children: "Trust score" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mt-1 text-2xl font-semibold tabular-nums", children: [
        previous.trustScore,
        " ",
        /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowRight, { className: "mx-2 inline size-4" }),
        " ",
        current.trustScore
      ] })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Badge, { variant: "outline", className: delta >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Icon, { className: "mr-1 size-3" }),
      delta >= 0 ? "+" : "",
      delta,
      " points"
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/runs", className: "ml-auto text-sm font-semibold text-primary hover:underline", children: "Compare runs" })
  ] });
}
export {
  Overview as component
};
