import { r as reactExports, j as jsxRuntimeExports } from "../_libs/react.mjs";
import { t as toast } from "../_libs/sonner.mjs";
import { P as PageShell, C as Card, a as CardContent, B as Badge } from "./card-CBpR56_E.mjs";
import { f as Lock, U as Users, g as EyeOff, h as Globe } from "../_libs/lucide-react.mjs";
import "../_libs/react-dom.mjs";
import "util";
import "crypto";
import "async_hooks";
import "stream";
import "./router-Cv4vvrPJ.mjs";
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
import "../_libs/isbot.mjs";
import "../_libs/radix-ui__react-slot.mjs";
import "../_libs/radix-ui__react-compose-refs.mjs";
import "../_libs/class-variance-authority.mjs";
import "../_libs/clsx.mjs";
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
  id: "private",
  label: "Private",
  detail: "Requires an access token in the terminal.",
  icon: Lock
}, {
  id: "shared",
  label: "Shared",
  detail: "Requires an invite code from the run owner.",
  icon: Users
}, {
  id: "anonymous",
  label: "Anonymous",
  detail: "Does not attach user information to shared evaluation data.",
  icon: EyeOff
}, {
  id: "public",
  label: "Public",
  detail: "Anyone with the URL can access the published evaluation.",
  icon: Globe
}];
function SettingsPage() {
  const [visibility, setVisibility] = reactExports.useState("private");
  const [inviteCode, setInviteCode] = reactExports.useState("");
  reactExports.useEffect(() => {
    const credential = sessionStorage.getItem("critiqor_access_credential") || "";
    fetch("/api/access", {
      method: "POST",
      headers: {
        "content-type": "application/json"
      },
      body: JSON.stringify({
        credential
      })
    }).then(async (response) => response.ok ? response.json() : fetch("/api/access").then((item) => item.json())).then((data) => {
      setVisibility(data.visibility);
      setInviteCode(data.inviteCode || "");
    });
  }, []);
  const select = (id) => {
    toast.info(`Run critiqor config to switch to ${id} and relaunch the dashboard.`);
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(PageShell, { title: "Visibility", description: "Control who can access runtime evaluations and identifying information.", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "grid gap-4 md:grid-cols-2", children: options.map((option) => /* @__PURE__ */ jsxRuntimeExports.jsx("button", { onClick: () => select(option.id), className: "text-left", "aria-pressed": visibility === option.id, children: /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { className: `h-full transition-all hover:border-primary/50 ${visibility === option.id ? "border-primary ring-2 ring-primary/15" : ""}`, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "flex gap-4 p-5", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: `grid size-10 shrink-0 place-items-center rounded-lg ${visibility === option.id ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`, children: /* @__PURE__ */ jsxRuntimeExports.jsx(option.icon, { className: "size-5" }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex items-center gap-2", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "font-semibold", children: option.label }),
          visibility === option.id && /* @__PURE__ */ jsxRuntimeExports.jsx(Badge, { children: "Selected" })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-1 text-sm text-muted-foreground", children: option.detail })
      ] })
    ] }) }) }, option.id)) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(Card, { children: /* @__PURE__ */ jsxRuntimeExports.jsxs(CardContent, { className: "p-5", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx("h2", { className: "font-bold", children: "Active dashboard visibility" }),
      /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "mt-2 text-sm text-muted-foreground", children: [
        "Configured in ",
        /* @__PURE__ */ jsxRuntimeExports.jsx("code", { children: "critiqor config" }),
        ". Relaunch the dashboard after changing it."
      ] }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-4 rounded-lg border bg-muted p-3 font-mono text-sm", children: visibility === "shared" ? `Invite code: ${inviteCode || "Authenticate to reveal"}` : visibility === "private" ? "A new access token was generated for this launch." : `${visibility[0].toUpperCase()}${visibility.slice(1)} access requires no code.` })
    ] }) })
  ] });
}
export {
  SettingsPage as component
};
