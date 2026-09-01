import { j as jsxRuntimeExports } from "../_libs/react.mjs";
import { P as PageShell, C as Card, b as CardHeader, c as CardTitle, a as CardContent, B as Badge } from "./card-BmZ5vFfw.mjs";
import { R as RunSelector } from "./run-selector-B1FO_3mB.mjs";
import { u as useCritiqor, B as Button } from "./router-ByJJYtQN.mjs";
import { t as toast } from "../_libs/sonner.mjs";
import { k as FileText, c as Copy, l as CircleCheck, T as Target, m as ListChecks, n as Gauge, W as Wrench } from "../_libs/lucide-react.mjs";
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
function PlaybookPage() {
  const {
    artifact,
    executive,
    webmcp,
    diagnoses
  } = useCritiqor((state) => state);
  const content = artifact.playbookContent?.trim() || "";
  const path = artifact.playbookPath || "";
  const items = diagnoses.filter((diagnosis) => diagnosis.runId === executive.runId);
  const copy = async (value, label) => {
    if (!value) {
      toast.error("Not available");
      return;
    }
    await navigator.clipboard.writeText(value);
    toast.success(label);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(PageShell, { title: "Playbook", description: `What should I change for ${executive.runId}?`, actions: /* @__PURE__ */ jsxRuntimeExports.jsx(RunSelector, {}), children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs(CardHeader, { className: "flex-row items-start justify-between gap-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs(CardTitle, { className: "flex items-center gap-2 text-base", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(FileText, { className: "size-4 text-primary" }),
            "Run-specific improvement playbook"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-sm text-muted-foreground", children: "Copied from the selected run artifact. Generic advice is not substituted." })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsxs(Button, { size: "sm", variant: "outline", onClick: () => copy(path, "Playbook path copied"), children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Copy, { className: "size-4" }),
            "Copy path"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(Button, { size: "sm", variant: "outline", onClick: () => copy(content, "Playbook copied"), children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Copy, { className: "size-4" }),
            "Copy playbook"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(Button, { size: "sm", onClick: () => copy(path ? `Read the Critiqor improvement playbook at ${path} and apply only the controls supported by that run's session.json and diagnosis.json.` : "", "Agent instruction copied"), children: "Copy agent instruction" })
        ] })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "space-y-3", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "rounded-lg border bg-muted/20 p-3", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] font-semibold uppercase tracking-widest text-muted-foreground", children: "Playbook file" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("code", { className: "mt-1 block break-all text-sm", children: path || "Not available" })
        ] }),
        content ? /* @__PURE__ */ jsxRuntimeExports.jsx("pre", { className: "max-h-[640px] overflow-auto whitespace-pre-wrap rounded-lg border bg-card p-4 font-mono text-sm leading-relaxed", children: content }) : /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { className: "border-dashed", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "py-12 text-center", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(CircleCheck, { className: "mx-auto size-7 text-muted-foreground" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "mt-3 font-semibold", children: "Playbook not available" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-sm text-muted-foreground", children: "The selected run does not include improvement_playbook.md." })
        ] }) }),
        webmcp.available && /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-wrap gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "outline", children: webmcp.displayStatus }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(Badge, { variant: "secondary", children: [
            webmcp.findingCount,
            " finding(s) in this run"
          ] })
        ] })
      ] })
    ] }),
    items.length === 0 ? /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { className: "border-dashed", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "py-12 text-center", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(CircleCheck, { className: "mx-auto size-7 text-emerald-500" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "mt-3 font-semibold", children: "No visual recommendation cards" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-sm text-muted-foreground", children: "The selected run has no diagnosis recommendations to explain visually." })
    ] }) }) : /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "space-y-4", children: items.map((diagnosis, index) => /* @__PURE__ */ jsxRuntimeExports.jsx(PlaybookItem, { diagnosis, index }, diagnosis.id)) })
  ] });
}
function PlaybookItem({
  diagnosis,
  index
}) {
  const priority = diagnosis.severity === "critical" || diagnosis.severity === "high" ? "High" : diagnosis.severity === "medium" ? "Medium" : diagnosis.severity === "info" ? "Info" : "Low";
  const steps = diagnosis.recommendedInvestigation.filter(Boolean);
  const verification = diagnosis.verificationSteps.filter(Boolean);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: "overflow-hidden", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { className: "border-b bg-muted/15", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-wrap items-start justify-between gap-3", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs font-semibold uppercase tracking-widest text-muted-foreground", children: [
          "Visual card ",
          index + 1
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(CardTitle, { className: "mt-1 text-lg", children: steps[0] || diagnosis.title || "Not captured" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs(Badge, { variant: "outline", children: [
          priority,
          " priority"
        ] }),
        diagnosis.findingId && /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: "secondary", children: diagnosis.findingId })
      ] })
    ] }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "grid gap-5 p-5 lg:grid-cols-4", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Block, { icon: Target, label: "Reason", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: diagnosis.rootCause || "Not captured" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Block, { icon: ListChecks, label: "Implementation steps", children: steps.length ? /* @__PURE__ */ jsxRuntimeExports.jsx("ol", { className: "list-inside list-decimal space-y-1", children: steps.map((step) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { children: step }, step)) }) : /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Not captured" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Block, { icon: Gauge, label: "Expected impact", children: /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: diagnosis.expectedImprovement || "Not captured" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(Block, { icon: Wrench, label: "Verification checklist", children: verification.length ? /* @__PURE__ */ jsxRuntimeExports.jsx("ul", { className: "space-y-1", children: verification.map((step) => /* @__PURE__ */ jsxRuntimeExports.jsxs("li", { className: "flex gap-2", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(CircleCheck, { className: "mt-0.5 size-3.5 shrink-0 text-emerald-500" }),
        step
      ] }, step)) }) : /* @__PURE__ */ jsxRuntimeExports.jsx("p", { children: "Not captured" }) })
    ] })
  ] });
}
function Block({
  icon: Icon,
  label,
  children
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "rounded-lg border bg-card p-4", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Icon, { className: "size-4 text-primary" }),
      label
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-sm leading-relaxed", children })
  ] });
}
export {
  PlaybookPage as component
};
