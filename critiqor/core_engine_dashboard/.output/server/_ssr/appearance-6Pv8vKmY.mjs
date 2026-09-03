import { r as reactExports, j as jsxRuntimeExports } from "../_libs/react.mjs";
import { P as PageShell, C as Card, a as CardContent } from "./card-CBpR56_E.mjs";
import { a as savedTheme, d as applyTheme } from "./router-Cv4vvrPJ.mjs";
import "../_libs/sonner.mjs";
import { w as Laptop, x as Sun, y as Moon } from "../_libs/lucide-react.mjs";
import "../_libs/class-variance-authority.mjs";
import "../_libs/clsx.mjs";
import "../_libs/tanstack__query-core.mjs";
import "../_libs/tanstack__react-query.mjs";
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
const options = [{
  id: "system",
  label: "System",
  detail: "Follow your operating system.",
  icon: Laptop
}, {
  id: "light",
  label: "Light",
  detail: "Bright surfaces with dark high-contrast text.",
  icon: Sun
}, {
  id: "dark",
  label: "Dark",
  detail: "Low-glare surfaces with soft-white text.",
  icon: Moon
}];
function AppearancePage() {
  const [mode, setMode] = reactExports.useState("system");
  reactExports.useEffect(() => setMode(savedTheme()), []);
  const select = (next) => {
    setMode(next);
    applyTheme(next);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsx(PageShell, { title: "Appearance", description: "Choose how Critiqor looks on this device.", children: /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "grid gap-4 md:grid-cols-3", children: options.map((option) => /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: () => select(option.id), className: "text-left", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { className: `h-full transition-all hover:border-primary/50 ${mode === option.id ? "border-primary ring-2 ring-primary/15" : ""}`, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "p-5", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `grid size-10 place-items-center rounded-lg ${mode === option.id ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(option.icon, { className: "size-5" }) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "mt-4 font-semibold", children: option.label }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-sm text-muted-foreground", children: option.detail })
  ] }) }) }, option.id)) }) });
}
export {
  AppearancePage as component
};
