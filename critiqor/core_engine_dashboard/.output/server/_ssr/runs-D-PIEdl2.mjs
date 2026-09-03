import { r as reactExports, j as jsxRuntimeExports } from "../_libs/react.mjs";
import { L as Link } from "../_libs/tanstack__react-router.mjs";
import { P as PageShell, C as Card, b as CardHeader, c as CardTitle, a as CardContent, B as Badge } from "./card-CBpR56_E.mjs";
import { C as Checkbox } from "./checkbox-BWLYw1JS.mjs";
import { u as useCritiqor, I as Input, c as cn } from "./router-Cv4vvrPJ.mjs";
import "../_libs/sonner.mjs";
import { i as Search, A as ArrowDownUp, j as GitCompareArrows } from "../_libs/lucide-react.mjs";
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
import "../_libs/radix-ui__react-checkbox.mjs";
import "../_libs/radix-ui__react-compose-refs.mjs";
import "../_libs/radix-ui__react-context.mjs";
import "../_libs/radix-ui__primitive.mjs";
import "../_libs/@radix-ui/react-use-controllable-state+[...].mjs";
import "../_libs/@radix-ui/react-use-layout-effect+[...].mjs";
import "../_libs/radix-ui__react-use-previous.mjs";
import "../_libs/radix-ui__react-use-size.mjs";
import "../_libs/radix-ui__react-presence.mjs";
import "../_libs/radix-ui__react-primitive.mjs";
import "../_libs/radix-ui__react-slot.mjs";
import "../_libs/tanstack__query-core.mjs";
import "../_libs/tanstack__react-query.mjs";
import "../_libs/tailwind-merge.mjs";
import "../_libs/radix-ui__react-separator.mjs";
import "../_libs/radix-ui__react-dialog.mjs";
import "../_libs/radix-ui__react-id.mjs";
import "../_libs/@radix-ui/react-dismissable-layer+[...].mjs";
import "../_libs/@radix-ui/react-use-callback-ref+[...].mjs";
import "../_libs/@radix-ui/react-use-escape-keydown+[...].mjs";
import "../_libs/radix-ui__react-focus-scope.mjs";
import "../_libs/radix-ui__react-portal.mjs";
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
import "../_libs/@radix-ui/react-visually-hidden+[...].mjs";
import "node:fs";
import "node:crypto";
import "node:path";
const Table = reactExports.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "relative w-full overflow-auto", children: /* @__PURE__ */ jsxRuntimeExports.jsx("table", { ref, className: cn("w-full caption-bottom text-sm", className), ...props }) })
);
Table.displayName = "Table";
const TableHeader = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx("thead", { ref, className: cn("[&_tr]:border-b", className), ...props }));
TableHeader.displayName = "TableHeader";
const TableBody = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx("tbody", { ref, className: cn("[&_tr:last-child]:border-0", className), ...props }));
TableBody.displayName = "TableBody";
const TableFooter = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  "tfoot",
  {
    ref,
    className: cn("border-t bg-muted/50 font-medium [&>tr]:last:border-b-0", className),
    ...props
  }
));
TableFooter.displayName = "TableFooter";
const TableRow = reactExports.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    "tr",
    {
      ref,
      className: cn(
        "border-b transition-colors hover:bg-muted/50 data-[state=selected]:bg-muted",
        className
      ),
      ...props
    }
  )
);
TableRow.displayName = "TableRow";
const TableHead = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  "th",
  {
    ref,
    className: cn(
      "h-10 px-2 text-left align-middle font-medium text-muted-foreground [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
      className
    ),
    ...props
  }
));
TableHead.displayName = "TableHead";
const TableCell = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  "td",
  {
    ref,
    className: cn(
      "p-2 align-middle [&:has([role=checkbox])]:pr-0 [&>[role=checkbox]]:translate-y-[2px]",
      className
    ),
    ...props
  }
));
TableCell.displayName = "TableCell";
const TableCaption = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx("caption", { ref, className: cn("mt-4 text-sm text-muted-foreground", className), ...props }));
TableCaption.displayName = "TableCaption";
function RunsPage() {
  const runs = useCritiqor((state) => state.runs);
  const [query, setQuery] = reactExports.useState("");
  const [status, setStatus] = reactExports.useState("all");
  const [sort, setSort] = reactExports.useState("newest");
  const [selected, setSelected] = reactExports.useState(/* @__PURE__ */ new Set());
  const filtered = reactExports.useMemo(() => runs.filter((run) => `${run.id} ${run.name} ${run.model ?? ""}`.toLowerCase().includes(query.toLowerCase()) && (status === "all" || run.status === status)).sort((a, b) => sort === "newest" ? b.startedAt.localeCompare(a.startedAt) : sort === "oldest" ? a.startedAt.localeCompare(b.startedAt) : sort === "trust-high" ? b.trustScore - a.trustScore : a.trustScore - b.trustScore), [runs, query, status, sort]);
  const compared = runs.filter((run) => selected.has(run.id));
  const toggle = (id) => setSelected((current) => {
    const next = new Set(current);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    return next;
  });
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(PageShell, { title: "Runs", description: "Did my changes improve the agent? Search, sort, filter, and compare observations.", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-wrap gap-2", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "relative min-w-64 flex-1", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Search, { className: "absolute left-3 top-2.5 size-4 text-muted-foreground" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Input, { value: query, onChange: (event) => setQuery(event.target.value), placeholder: "Search run, agent, or framework…", className: "pl-9" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("select", { value: status, onChange: (event) => setStatus(event.target.value), className: "h-9 rounded-md border bg-background px-3 text-sm", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "all", children: "All statuses" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "passed", children: "Passed" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "failed", children: "Failed" })
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex h-9 items-center gap-2 rounded-md border bg-background px-3 text-sm", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(ArrowDownUp, { className: "size-4" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("select", { value: sort, onChange: (event) => setSort(event.target.value), className: "bg-transparent outline-none", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "newest", children: "Newest first" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "oldest", children: "Oldest first" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "trust-high", children: "Highest trust" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "trust-low", children: "Lowest trust" })
        ] })
      ] })
    ] }),
    compared.length >= 2 && /* @__PURE__ */ jsxRuntimeExports.jsxs(Card, { className: "border-primary/25", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardHeader, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardTitle, { className: "flex items-center gap-2 text-base", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(GitCompareArrows, { className: "size-4 text-primary" }),
        "Run comparison"
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(CardContent, { className: "overflow-x-auto", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "grid min-w-[640px] gap-3", style: {
        gridTemplateColumns: `160px repeat(${compared.length}, minmax(150px, 1fr))`
      }, children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: "Metric", strong: true }),
        compared.map((run) => /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: run.id, strong: true }, run.id)),
        /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: "Trust score" }),
        compared.map((run) => /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: `${run.trustScore}/100` }, `${run.id}-trust`)),
        /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: "Hallucination risk" }),
        compared.map((run) => /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: `${run.hallucinationRisk}%` }, `${run.id}-risk`)),
        /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: "Tool reliability" }),
        compared.map((run) => /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: `${run.toolReliability}%` }, `${run.id}-tools`)),
        /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: "Reasoning consistency" }),
        compared.map((run) => /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: `${run.reasoningConsistency}%` }, `${run.id}-reasoning`)),
        /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: "WebMCP" }),
        compared.map((run) => /* @__PURE__ */ jsxRuntimeExports.jsx(CompareCell, { label: run.webmcpComparison ?? run.webmcpStatus ?? "Not exercised" }, `${run.id}-webmcp`))
      ] }) })
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { className: "overflow-hidden", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Table, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(TableHeader, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(TableRow, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(TableHead, { className: "w-12", children: "Compare" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(TableHead, { children: "Run" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(TableHead, { children: "Status" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(TableHead, { children: "Framework" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(TableHead, { className: "text-right", children: "Trust" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(TableHead, { className: "text-right", children: "Risk" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(TableHead, { children: "WebMCP" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(TableHead, { children: "Started" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(TableHead, { className: "text-right", children: "Report" })
      ] }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(TableBody, { children: [
        filtered.map((run) => /* @__PURE__ */ jsxRuntimeExports.jsxs(TableRow, { children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(TableCell, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(Checkbox, { checked: selected.has(run.id), onCheckedChange: () => toggle(run.id), "aria-label": `Compare ${run.id}` }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(TableCell, { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "font-mono text-xs font-semibold", children: run.id }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs text-muted-foreground", children: run.name })
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(TableCell, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { variant: run.status === "passed" ? "default" : "destructive", children: run.status }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(TableCell, { className: "text-muted-foreground", children: run.model ?? "—" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(TableCell, { className: "text-right font-semibold tabular-nums", children: run.trustScore }),
          /* @__PURE__ */ jsxRuntimeExports.jsxs(TableCell, { className: "text-right tabular-nums", children: [
            run.hallucinationRisk,
            "%"
          ] }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(TableCell, { children: run.webmcpStatus ? /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-xs font-medium", children: run.webmcpComparison ?? run.webmcpStatus }),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-[10px] text-muted-foreground", children: [
              run.webmcpFindings ?? 0,
              " finding(s) · ",
              run.webmcpEffects ?? 0,
              " effect(s)"
            ] })
          ] }) : /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-muted-foreground", children: "—" }) }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(TableCell, { className: "text-muted-foreground", children: new Date(run.startedAt).toLocaleString() }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(TableCell, { className: "text-right", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Link, { to: "/diagnoses", search: {
            run_id: run.id
          }, className: "font-semibold text-primary hover:underline", children: "Open" }) })
        ] }, run.id)),
        filtered.length === 0 && /* @__PURE__ */ jsxRuntimeExports.jsx(TableRow, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(TableCell, { colSpan: 9, className: "py-10 text-center text-muted-foreground", children: "No runs match the current filters." }) })
      ] })
    ] }) })
  ] });
}
function CompareCell({
  label,
  strong
}) {
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `rounded-md border bg-muted/15 p-2 text-sm ${strong ? "font-semibold" : ""}`, children: label });
}
export {
  RunsPage as component
};
