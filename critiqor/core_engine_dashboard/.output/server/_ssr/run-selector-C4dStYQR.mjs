import { j as jsxRuntimeExports } from "../_libs/react.mjs";
import { e as useNavigate, d as useRouterState } from "../_libs/tanstack__react-router.mjs";
import { u as useCritiqor } from "./router-Cv4vvrPJ.mjs";
function RunSelector({ label = "Focus run" }) {
  const runs = useCritiqor((state) => state.runs);
  const current = useCritiqor((state) => state.executive.runId);
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  const known = runs.some((run) => run.id === current);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("label", { className: "flex min-w-64 flex-wrap items-center gap-2 text-sm", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "text-xs font-semibold uppercase tracking-widest text-muted-foreground", children: label }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "select",
      {
        "aria-label": label,
        className: "h-9 min-w-56 flex-1 rounded-md border bg-background px-3 text-sm",
        value: current,
        onChange: (event) => {
          const runId = event.target.value;
          if (!runId) return;
          void navigate({
            to: pathname,
            search: { run_id: runId }
          });
        },
        children: [
          !known && current && /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: current, children: [
            current,
            " · not found"
          ] }),
          runs.map((run) => /* @__PURE__ */ jsxRuntimeExports.jsxs("option", { value: run.id, children: [
            run.id,
            run.webmcpStatus ? ` · ${run.webmcpStatus}` : ""
          ] }, run.id)),
          !runs.length && !current && /* @__PURE__ */ jsxRuntimeExports.jsx("option", { value: "", children: "No runs available" })
        ]
      }
    )
  ] });
}
export {
  RunSelector as R
};
