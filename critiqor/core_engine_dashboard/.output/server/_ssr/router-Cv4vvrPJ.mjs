import { b as QueryClient } from "../_libs/tanstack__query-core.mjs";
import { Q as QueryClientProvider, u as useQuery } from "../_libs/tanstack__react-query.mjs";
import { c as createRouter, a as createRootRouteWithContext, u as useRouter, O as Outlet, H as HeadContent, S as Scripts, b as createFileRoute, l as lazyRouteComponent, d as useRouterState, L as Link } from "../_libs/tanstack__react-router.mjs";
import { r as reactExports, j as jsxRuntimeExports } from "../_libs/react.mjs";
import { S as Slot } from "../_libs/radix-ui__react-slot.mjs";
import { c as cva } from "../_libs/class-variance-authority.mjs";
import { c as clsx } from "../_libs/clsx.mjs";
import { t as twMerge } from "../_libs/tailwind-merge.mjs";
import { R as Root$1 } from "../_libs/radix-ui__react-separator.mjs";
import { R as Root, P as Portal, C as Content, a as Close, T as Title, D as Description, O as Overlay } from "../_libs/radix-ui__react-dialog.mjs";
import { P as Provider, R as Root3, T as Trigger, a as Portal$1, C as Content2 } from "../_libs/radix-ui__react-tooltip.mjs";
import { T as Toaster$1, t as toast } from "../_libs/sonner.mjs";
import { readFileSync, mkdirSync, appendFileSync, existsSync, unlinkSync, writeFileSync, renameSync, readdirSync, statSync } from "node:fs";
import { verify, createPublicKey, createHash } from "node:crypto";
import path, { join } from "node:path";
import { L as LockKeyhole, a as LayoutDashboard, C as CirclePlay, S as Stethoscope, W as Wrench, F as FileSearch, E as Eye, P as Palette, B as BookOpen, b as Earth, G as Github, c as Copy, X, d as PanelLeft, e as ChevronDown } from "../_libs/lucide-react.mjs";
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
import "../_libs/radix-ui__react-compose-refs.mjs";
import "../_libs/radix-ui__react-primitive.mjs";
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
import "../_libs/radix-ui__react-popper.mjs";
import "../_libs/floating-ui__react-dom.mjs";
import "../_libs/floating-ui__dom.mjs";
import "../_libs/floating-ui__core.mjs";
import "../_libs/floating-ui__utils.mjs";
import "../_libs/radix-ui__react-arrow.mjs";
import "../_libs/radix-ui__react-use-size.mjs";
import "../_libs/@radix-ui/react-visually-hidden+[...].mjs";
const appCss = "/assets/styles-CPOj_Ctq.css";
function reportLovableError(error, context = {}) {
  if (typeof window === "undefined") return;
  window.__lovableEvents?.captureException?.(
    error,
    {
      source: "react_error_boundary",
      route: window.location.pathname,
      ...context
    },
    {
      mechanism: "react_error_boundary",
      handled: false,
      severity: "error"
    }
  );
}
const MOBILE_BREAKPOINT = 768;
function useIsMobile() {
  const [isMobile, setIsMobile] = reactExports.useState(void 0);
  reactExports.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`);
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    };
    mql.addEventListener("change", onChange);
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT);
    return () => mql.removeEventListener("change", onChange);
  }, []);
  return !!isMobile;
}
function cn(...inputs) {
  return twMerge(clsx(inputs));
}
const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground shadow hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        outline: "border border-input bg-background shadow-sm hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground shadow-sm hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline"
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-md px-8",
        icon: "h-9 w-9"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
);
const Button = reactExports.forwardRef(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return /* @__PURE__ */ jsxRuntimeExports.jsx(Comp, { className: cn(buttonVariants({ variant, size, className })), ref, ...props });
  }
);
Button.displayName = "Button";
const Input = reactExports.forwardRef(
  ({ className, type, ...props }, ref) => {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "input",
      {
        type,
        className: cn(
          "flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className
        ),
        ref,
        ...props
      }
    );
  }
);
Input.displayName = "Input";
const Separator = reactExports.forwardRef(({ className, orientation = "horizontal", decorative = true, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  Root$1,
  {
    ref,
    decorative,
    orientation,
    className: cn(
      "shrink-0 bg-border",
      orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
      className
    ),
    ...props
  }
));
Separator.displayName = Root$1.displayName;
const Sheet = Root;
const SheetPortal = Portal;
const SheetOverlay = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  Overlay,
  {
    className: cn(
      "fixed inset-0 z-50 bg-black/80  data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    ),
    ...props,
    ref
  }
));
SheetOverlay.displayName = Overlay.displayName;
const sheetVariants = cva(
  "fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out data-[state=closed]:duration-300 data-[state=open]:duration-500 data-[state=open]:animate-in data-[state=closed]:animate-out",
  {
    variants: {
      side: {
        top: "inset-x-0 top-0 border-b data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top",
        bottom: "inset-x-0 bottom-0 border-t data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom",
        left: "inset-y-0 left-0 h-full w-3/4 border-r data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left sm:max-w-sm",
        right: "inset-y-0 right-0 h-full w-3/4 border-l data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-sm"
      }
    },
    defaultVariants: {
      side: "right"
    }
  }
);
const SheetContent = reactExports.forwardRef(({ side = "right", className, children, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsxs(SheetPortal, { children: [
  /* @__PURE__ */ jsxRuntimeExports.jsx(SheetOverlay, {}),
  /* @__PURE__ */ jsxRuntimeExports.jsxs(Content, { ref, className: cn(sheetVariants({ side }), className), ...props, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Close, { className: "absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background cursor-pointer transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-secondary", children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(X, { className: "h-4 w-4" }),
      /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "sr-only", children: "Close" })
    ] }),
    children
  ] })
] }));
SheetContent.displayName = Content.displayName;
const SheetHeader = ({ className, ...props }) => /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: cn("flex flex-col space-y-2 text-center sm:text-left", className), ...props });
SheetHeader.displayName = "SheetHeader";
const SheetTitle = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  Title,
  {
    ref,
    className: cn("text-lg font-semibold text-foreground", className),
    ...props
  }
));
SheetTitle.displayName = Title.displayName;
const SheetDescription = reactExports.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
  Description,
  {
    ref,
    className: cn("text-sm text-muted-foreground", className),
    ...props
  }
));
SheetDescription.displayName = Description.displayName;
function Skeleton({ className, ...props }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: cn("animate-pulse rounded-md bg-primary/10", className), ...props });
}
const TooltipProvider = Provider;
const Tooltip = Root3;
const TooltipTrigger = Trigger;
const TooltipContent = reactExports.forwardRef(({ className, sideOffset = 4, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(Portal$1, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
  Content2,
  {
    ref,
    sideOffset,
    className: cn(
      "z-50 overflow-hidden rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 origin-(--radix-tooltip-content-transform-origin)",
      className
    ),
    ...props
  }
) }));
TooltipContent.displayName = Content2.displayName;
const SIDEBAR_COOKIE_NAME = "sidebar_state";
const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7;
const SIDEBAR_WIDTH = "16rem";
const SIDEBAR_WIDTH_MOBILE = "18rem";
const SIDEBAR_WIDTH_ICON = "3rem";
const SIDEBAR_KEYBOARD_SHORTCUT = "b";
const SidebarContext = reactExports.createContext(null);
function useSidebar() {
  const context = reactExports.useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider.");
  }
  return context;
}
const SidebarProvider = reactExports.forwardRef(
  ({
    defaultOpen = true,
    open: openProp,
    onOpenChange: setOpenProp,
    className,
    style,
    children,
    ...props
  }, ref) => {
    const isMobile = useIsMobile();
    const [openMobile, setOpenMobile] = reactExports.useState(false);
    const [_open, _setOpen] = reactExports.useState(defaultOpen);
    const open = openProp ?? _open;
    const setOpen = reactExports.useCallback(
      (value) => {
        const openState = typeof value === "function" ? value(open) : value;
        if (setOpenProp) {
          setOpenProp(openState);
        } else {
          _setOpen(openState);
        }
        document.cookie = `${SIDEBAR_COOKIE_NAME}=${openState}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`;
      },
      [setOpenProp, open]
    );
    const toggleSidebar = reactExports.useCallback(() => {
      return isMobile ? setOpenMobile((open2) => !open2) : setOpen((open2) => !open2);
    }, [isMobile, setOpen, setOpenMobile]);
    reactExports.useEffect(() => {
      const handleKeyDown = (event) => {
        if (event.key === SIDEBAR_KEYBOARD_SHORTCUT && (event.metaKey || event.ctrlKey)) {
          event.preventDefault();
          toggleSidebar();
        }
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }, [toggleSidebar]);
    const state2 = open ? "expanded" : "collapsed";
    const contextValue = reactExports.useMemo(
      () => ({
        state: state2,
        open,
        setOpen,
        isMobile,
        openMobile,
        setOpenMobile,
        toggleSidebar
      }),
      [state2, open, setOpen, isMobile, openMobile, setOpenMobile, toggleSidebar]
    );
    return /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarContext.Provider, { value: contextValue, children: /* @__PURE__ */ jsxRuntimeExports.jsx(TooltipProvider, { delayDuration: 0, children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        style: {
          "--sidebar-width": SIDEBAR_WIDTH,
          "--sidebar-width-icon": SIDEBAR_WIDTH_ICON,
          ...style
        },
        className: cn(
          "group/sidebar-wrapper flex min-h-svh w-full has-[[data-variant=inset]]:bg-sidebar",
          className
        ),
        ref,
        ...props,
        children
      }
    ) }) });
  }
);
SidebarProvider.displayName = "SidebarProvider";
const Sidebar = reactExports.forwardRef(
  ({
    side = "left",
    variant = "sidebar",
    collapsible = "offcanvas",
    className,
    children,
    ...props
  }, ref) => {
    const { isMobile, state: state2, openMobile, setOpenMobile } = useSidebar();
    if (collapsible === "none") {
      return /* @__PURE__ */ jsxRuntimeExports.jsx(
        "div",
        {
          className: cn(
            "flex h-full w-(--sidebar-width) flex-col bg-sidebar text-sidebar-foreground",
            className
          ),
          ref,
          ...props,
          children
        }
      );
    }
    if (isMobile) {
      return /* @__PURE__ */ jsxRuntimeExports.jsx(Sheet, { open: openMobile, onOpenChange: setOpenMobile, ...props, children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        SheetContent,
        {
          "data-sidebar": "sidebar",
          "data-mobile": "true",
          className: "w-(--sidebar-width) bg-sidebar p-0 text-sidebar-foreground [&>button]:hidden",
          style: {
            "--sidebar-width": SIDEBAR_WIDTH_MOBILE
          },
          side,
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsxs(SheetHeader, { className: "sr-only", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(SheetTitle, { children: "Sidebar" }),
              /* @__PURE__ */ jsxRuntimeExports.jsx(SheetDescription, { children: "Displays the mobile sidebar." })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex h-full w-full flex-col", children })
          ]
        }
      ) });
    }
    return /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "div",
      {
        ref,
        className: "group peer hidden text-sidebar-foreground md:block",
        "data-state": state2,
        "data-collapsible": state2 === "collapsed" ? collapsible : "",
        "data-variant": variant,
        "data-side": side,
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: cn(
                "relative w-(--sidebar-width) bg-transparent transition-[width] duration-200 ease-linear",
                "group-data-[collapsible=offcanvas]:w-0",
                "group-data-[side=right]:rotate-180",
                variant === "floating" || variant === "inset" ? "group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)_+_theme(spacing.4))]" : "group-data-[collapsible=icon]:w-(--sidebar-width-icon)"
              )
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "div",
            {
              className: cn(
                "fixed inset-y-0 z-10 hidden h-svh w-(--sidebar-width) transition-[left,right,width] duration-200 ease-linear md:flex",
                side === "left" ? "left-0 group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)]" : "right-0 group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)]",
                // Adjust the padding for floating and inset variants.
                variant === "floating" || variant === "inset" ? "p-2 group-data-[collapsible=icon]:w-[calc(var(--sidebar-width-icon)_+_theme(spacing.4)_+2px)]" : "group-data-[collapsible=icon]:w-(--sidebar-width-icon) group-data-[side=left]:border-r group-data-[side=right]:border-l",
                className
              ),
              ...props,
              children: /* @__PURE__ */ jsxRuntimeExports.jsx(
                "div",
                {
                  "data-sidebar": "sidebar",
                  className: "flex h-full w-full flex-col bg-sidebar group-data-[variant=floating]:rounded-lg group-data-[variant=floating]:border group-data-[variant=floating]:border-sidebar-border group-data-[variant=floating]:shadow",
                  children
                }
              )
            }
          )
        ]
      }
    );
  }
);
Sidebar.displayName = "Sidebar";
const SidebarTrigger = reactExports.forwardRef(({ className, onClick, ...props }, ref) => {
  const { toggleSidebar } = useSidebar();
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    Button,
    {
      ref,
      "data-sidebar": "trigger",
      variant: "ghost",
      size: "icon",
      className: cn("h-7 w-7", className),
      onClick: (event) => {
        onClick?.(event);
        toggleSidebar();
      },
      ...props,
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(PanelLeft, {}),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "sr-only", children: "Toggle Sidebar" })
      ]
    }
  );
});
SidebarTrigger.displayName = "SidebarTrigger";
const SidebarRail = reactExports.forwardRef(
  ({ className, ...props }, ref) => {
    const { toggleSidebar } = useSidebar();
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "button",
      {
        ref,
        "data-sidebar": "rail",
        "aria-label": "Toggle Sidebar",
        tabIndex: -1,
        onClick: toggleSidebar,
        title: "Toggle Sidebar",
        className: cn(
          "absolute inset-y-0 z-20 hidden w-4 -translate-x-1/2 transition-all ease-linear after:absolute after:inset-y-0 after:left-1/2 after:w-[2px] hover:after:bg-sidebar-border group-data-[side=left]:-right-4 group-data-[side=right]:left-0 sm:flex",
          "[[data-side=left]_&]:cursor-w-resize [[data-side=right]_&]:cursor-e-resize",
          "[[data-side=left][data-state=collapsed]_&]:cursor-e-resize [[data-side=right][data-state=collapsed]_&]:cursor-w-resize",
          "group-data-[collapsible=offcanvas]:translate-x-0 group-data-[collapsible=offcanvas]:after:left-full group-data-[collapsible=offcanvas]:hover:bg-sidebar",
          "[[data-side=left][data-collapsible=offcanvas]_&]:-right-2",
          "[[data-side=right][data-collapsible=offcanvas]_&]:-left-2",
          className
        ),
        ...props
      }
    );
  }
);
SidebarRail.displayName = "SidebarRail";
const SidebarInset = reactExports.forwardRef(
  ({ className, ...props }, ref) => {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "main",
      {
        ref,
        className: cn(
          "relative flex w-full flex-1 flex-col bg-background",
          "md:peer-data-[variant=inset]:m-2 md:peer-data-[state=collapsed]:peer-data-[variant=inset]:ml-2 md:peer-data-[variant=inset]:ml-0 md:peer-data-[variant=inset]:rounded-xl md:peer-data-[variant=inset]:shadow",
          className
        ),
        ...props
      }
    );
  }
);
SidebarInset.displayName = "SidebarInset";
const SidebarInput = reactExports.forwardRef(({ className, ...props }, ref) => {
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Input,
    {
      ref,
      "data-sidebar": "input",
      className: cn(
        "h-8 w-full bg-background shadow-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
        className
      ),
      ...props
    }
  );
});
SidebarInput.displayName = "SidebarInput";
const SidebarHeader = reactExports.forwardRef(
  ({ className, ...props }, ref) => {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref,
        "data-sidebar": "header",
        className: cn("flex flex-col gap-2 p-2", className),
        ...props
      }
    );
  }
);
SidebarHeader.displayName = "SidebarHeader";
const SidebarFooter = reactExports.forwardRef(
  ({ className, ...props }, ref) => {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref,
        "data-sidebar": "footer",
        className: cn("flex flex-col gap-2 p-2", className),
        ...props
      }
    );
  }
);
SidebarFooter.displayName = "SidebarFooter";
const SidebarSeparator = reactExports.forwardRef(({ className, ...props }, ref) => {
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Separator,
    {
      ref,
      "data-sidebar": "separator",
      className: cn("mx-2 w-auto bg-sidebar-border", className),
      ...props
    }
  );
});
SidebarSeparator.displayName = "SidebarSeparator";
const SidebarContent = reactExports.forwardRef(
  ({ className, ...props }, ref) => {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref,
        "data-sidebar": "content",
        className: cn(
          "flex min-h-0 flex-1 flex-col gap-2 overflow-auto group-data-[collapsible=icon]:overflow-hidden",
          className
        ),
        ...props
      }
    );
  }
);
SidebarContent.displayName = "SidebarContent";
const SidebarGroup = reactExports.forwardRef(
  ({ className, ...props }, ref) => {
    return /* @__PURE__ */ jsxRuntimeExports.jsx(
      "div",
      {
        ref,
        "data-sidebar": "group",
        className: cn("relative flex w-full min-w-0 flex-col p-2", className),
        ...props
      }
    );
  }
);
SidebarGroup.displayName = "SidebarGroup";
const SidebarGroupLabel = reactExports.forwardRef(({ className, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "div";
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Comp,
    {
      ref,
      "data-sidebar": "group-label",
      className: cn(
        "flex h-8 shrink-0 items-center rounded-md px-2 text-xs font-medium text-sidebar-foreground/70 outline-none ring-sidebar-ring transition-[margin,opacity] duration-200 ease-linear focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0",
        "group-data-[collapsible=icon]:-mt-8 group-data-[collapsible=icon]:opacity-0",
        className
      ),
      ...props
    }
  );
});
SidebarGroupLabel.displayName = "SidebarGroupLabel";
const SidebarGroupAction = reactExports.forwardRef(({ className, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button";
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Comp,
    {
      ref,
      "data-sidebar": "group-action",
      className: cn(
        "absolute right-3 top-3.5 flex aspect-square w-5 items-center justify-center rounded-md p-0 text-sidebar-foreground outline-none ring-sidebar-ring cursor-pointer transition-transform hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0",
        // Increases the hit area of the button on mobile.
        "after:absolute after:-inset-2 after:md:hidden",
        "group-data-[collapsible=icon]:hidden",
        className
      ),
      ...props
    }
  );
});
SidebarGroupAction.displayName = "SidebarGroupAction";
const SidebarGroupContent = reactExports.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      ref,
      "data-sidebar": "group-content",
      className: cn("w-full text-sm", className),
      ...props
    }
  )
);
SidebarGroupContent.displayName = "SidebarGroupContent";
const SidebarMenu = reactExports.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    "ul",
    {
      ref,
      "data-sidebar": "menu",
      className: cn("flex w-full min-w-0 flex-col gap-1", className),
      ...props
    }
  )
);
SidebarMenu.displayName = "SidebarMenu";
const SidebarMenuItem = reactExports.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    "li",
    {
      ref,
      "data-sidebar": "menu-item",
      className: cn("group/menu-item relative", className),
      ...props
    }
  )
);
SidebarMenuItem.displayName = "SidebarMenuItem";
const sidebarMenuButtonVariants = cva(
  "peer/menu-button flex w-full items-center gap-2 overflow-hidden rounded-md p-2 text-left text-sm outline-none ring-sidebar-ring cursor-pointer transition-[width,height,padding] hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed group-has-[[data-sidebar=menu-action]]/menu-item:pr-8 aria-disabled:pointer-events-none aria-disabled:opacity-50 data-[active=true]:bg-sidebar-accent data-[active=true]:font-medium data-[active=true]:text-sidebar-accent-foreground data-[state=open]:hover:bg-sidebar-accent data-[state=open]:hover:text-sidebar-accent-foreground group-data-[collapsible=icon]:!size-8 group-data-[collapsible=icon]:!p-2 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0",
  {
    variants: {
      variant: {
        default: "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
        outline: "bg-background shadow-[0_0_0_1px_var(--sidebar-border)] hover:bg-sidebar-accent hover:text-sidebar-accent-foreground hover:shadow-[0_0_0_1px_var(--sidebar-accent)]"
      },
      size: {
        default: "h-8 text-sm",
        sm: "h-7 text-xs",
        lg: "h-12 text-sm group-data-[collapsible=icon]:!p-0"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
);
const SidebarMenuButton = reactExports.forwardRef(
  ({
    asChild = false,
    isActive = false,
    variant = "default",
    size = "default",
    tooltip,
    className,
    ...props
  }, ref) => {
    const Comp = asChild ? Slot : "button";
    const { isMobile, state: state2 } = useSidebar();
    const button = /* @__PURE__ */ jsxRuntimeExports.jsx(
      Comp,
      {
        ref,
        "data-sidebar": "menu-button",
        "data-size": size,
        "data-active": isActive,
        className: cn(sidebarMenuButtonVariants({ variant, size }), className),
        ...props
      }
    );
    if (!tooltip) {
      return button;
    }
    if (typeof tooltip === "string") {
      tooltip = {
        children: tooltip
      };
    }
    return /* @__PURE__ */ jsxRuntimeExports.jsxs(Tooltip, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(TooltipTrigger, { asChild: true, children: button }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(
        TooltipContent,
        {
          side: "right",
          align: "center",
          hidden: state2 !== "collapsed" || isMobile,
          ...tooltip
        }
      )
    ] });
  }
);
SidebarMenuButton.displayName = "SidebarMenuButton";
const SidebarMenuAction = reactExports.forwardRef(({ className, asChild = false, showOnHover = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button";
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Comp,
    {
      ref,
      "data-sidebar": "menu-action",
      className: cn(
        "absolute right-1 top-1.5 flex aspect-square w-5 items-center justify-center rounded-md p-0 text-sidebar-foreground outline-none ring-sidebar-ring cursor-pointer transition-transform hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 peer-hover/menu-button:text-sidebar-accent-foreground [&>svg]:size-4 [&>svg]:shrink-0",
        // Increases the hit area of the button on mobile.
        "after:absolute after:-inset-2 after:md:hidden",
        "peer-data-[size=sm]/menu-button:top-1",
        "peer-data-[size=default]/menu-button:top-1.5",
        "peer-data-[size=lg]/menu-button:top-2.5",
        "group-data-[collapsible=icon]:hidden",
        showOnHover && "group-focus-within/menu-item:opacity-100 group-hover/menu-item:opacity-100 data-[state=open]:opacity-100 peer-data-[active=true]/menu-button:text-sidebar-accent-foreground md:opacity-0",
        className
      ),
      ...props
    }
  );
});
SidebarMenuAction.displayName = "SidebarMenuAction";
const SidebarMenuBadge = reactExports.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    "div",
    {
      ref,
      "data-sidebar": "menu-badge",
      className: cn(
        "pointer-events-none absolute right-1 flex h-5 min-w-5 select-none items-center justify-center rounded-md px-1 text-xs font-medium tabular-nums text-sidebar-foreground",
        "peer-hover/menu-button:text-sidebar-accent-foreground peer-data-[active=true]/menu-button:text-sidebar-accent-foreground",
        "peer-data-[size=sm]/menu-button:top-1",
        "peer-data-[size=default]/menu-button:top-1.5",
        "peer-data-[size=lg]/menu-button:top-2.5",
        "group-data-[collapsible=icon]:hidden",
        className
      ),
      ...props
    }
  )
);
SidebarMenuBadge.displayName = "SidebarMenuBadge";
const SidebarMenuSkeleton = reactExports.forwardRef(({ className, showIcon = false, ...props }, ref) => {
  const width = reactExports.useMemo(() => {
    return `${Math.floor(Math.random() * 40) + 50}%`;
  }, []);
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "div",
    {
      ref,
      "data-sidebar": "menu-skeleton",
      className: cn("flex h-8 items-center gap-2 rounded-md px-2", className),
      ...props,
      children: [
        showIcon && /* @__PURE__ */ jsxRuntimeExports.jsx(Skeleton, { className: "size-4 rounded-md", "data-sidebar": "menu-skeleton-icon" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          Skeleton,
          {
            className: "h-4 max-w-(--skeleton-width) flex-1",
            "data-sidebar": "menu-skeleton-text",
            style: {
              "--skeleton-width": width
            }
          }
        )
      ]
    }
  );
});
SidebarMenuSkeleton.displayName = "SidebarMenuSkeleton";
const SidebarMenuSub = reactExports.forwardRef(
  ({ className, ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx(
    "ul",
    {
      ref,
      "data-sidebar": "menu-sub",
      className: cn(
        "mx-3.5 flex min-w-0 translate-x-px flex-col gap-1 border-l border-sidebar-border px-2.5 py-0.5",
        "group-data-[collapsible=icon]:hidden",
        className
      ),
      ...props
    }
  )
);
SidebarMenuSub.displayName = "SidebarMenuSub";
const SidebarMenuSubItem = reactExports.forwardRef(
  ({ ...props }, ref) => /* @__PURE__ */ jsxRuntimeExports.jsx("li", { ref, ...props })
);
SidebarMenuSubItem.displayName = "SidebarMenuSubItem";
const SidebarMenuSubButton = reactExports.forwardRef(({ asChild = false, size = "md", isActive, className, ...props }, ref) => {
  const Comp = asChild ? Slot : "a";
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Comp,
    {
      ref,
      "data-sidebar": "menu-sub-button",
      "data-size": size,
      "data-active": isActive,
      className: cn(
        "flex h-7 min-w-0 -translate-x-px items-center gap-2 overflow-hidden rounded-md px-2 text-sidebar-foreground outline-none ring-sidebar-ring cursor-pointer hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 active:bg-sidebar-accent active:text-sidebar-accent-foreground disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed aria-disabled:pointer-events-none aria-disabled:opacity-50 [&>span:last-child]:truncate [&>svg]:size-4 [&>svg]:shrink-0 [&>svg]:text-sidebar-accent-foreground",
        "data-[active=true]:bg-sidebar-accent data-[active=true]:text-sidebar-accent-foreground",
        size === "sm" && "text-xs",
        size === "md" && "text-sm",
        "group-data-[collapsible=icon]:hidden",
        className
      ),
      ...props
    }
  );
});
SidebarMenuSubButton.displayName = "SidebarMenuSubButton";
const logo = "/assets/critiqor-logo-v-ZKSU2V.png";
const emptyExecutive = () => ({
  trustScore: 0,
  confidence: 0,
  verdict: "Waiting for run data",
  summary: "Finalize a Critiqor observation session to populate this dashboard from local diagnosis artifacts.",
  runId: "no_run_selected",
  agent: "OpenClaw agent",
  task: "No monitored execution yet",
  generatedAt: (/* @__PURE__ */ new Date()).toISOString(),
  trustLevel: "low",
  evidence: [],
  confidenceReasoning: "No runtime evidence has been loaded yet."
});
const emptyState = () => ({
  executive: emptyExecutive(),
  runs: [],
  diagnoses: [],
  evidence: [],
  benchmarks: [],
  sync: { loading: true, source: "empty" },
  scoreExplanations: [],
  agentHealth: {
    status: "Waiting for diagnosis",
    strengths: [],
    stableBehaviours: [],
    recommendedMonitoring: ["Finalize a Critiqor observation session to load local evidence."]
  },
  timeline: [],
  artifact: {
    eventCount: 0,
    toolCallCount: 0,
    toolOutputCount: 0,
    memoryEventCount: 0,
    failureCount: 0,
    durationMs: 0,
    evidenceStatus: "unknown",
    redactionCount: 0,
    truncationCount: 0,
    integrityErrors: []
  },
  webmcp: {
    available: false,
    status: "NOT_EXERCISED",
    displayStatus: "Not exercised",
    summary: "No WebMCP activity was included in this run.",
    scenariosExercised: 0,
    findingCount: 0,
    duplicateEffectCount: 0,
    authoritativeEffectCount: 0,
    strengths: []
  }
});
let state = emptyState();
const listeners = /* @__PURE__ */ new Set();
const emit = () => listeners.forEach((l) => l());
const critiqorStore = {
  getState: () => state,
  subscribe: (fn) => {
    listeners.add(fn);
    return () => listeners.delete(fn);
  },
  replace: (next) => {
    state = {
      ...state,
      ...next,
      executive: next.executive ?? state.executive,
      sync: next.sync ? { ...state.sync, ...next.sync } : state.sync
    };
    emit();
  },
  setSyncStatus: (sync) => {
    state = { ...state, sync: { ...state.sync, ...sync } };
    emit();
  },
  addRun: (r) => {
    state = { ...state, runs: [r, ...state.runs] };
    emit();
  },
  addDiagnosis: (d) => {
    state = { ...state, diagnoses: [d, ...state.diagnoses] };
    emit();
  },
  addEvidence: (e) => {
    state = { ...state, evidence: [e, ...state.evidence].slice(0, 500) };
    emit();
  },
  upsertBenchmark: (b) => {
    const existing = state.benchmarks.findIndex((x) => x.id === b.id);
    const next = existing >= 0 ? state.benchmarks.map((x, i) => i === existing ? b : x) : [b, ...state.benchmarks];
    state = { ...state, benchmarks: next };
    emit();
  },
  setExecutive: (e) => {
    state = { ...state, executive: { ...state.executive, ...e } };
    emit();
  }
};
if (typeof window !== "undefined") {
  window.critiqor = critiqorStore;
}
const serverSnapshot = emptyState();
function useCritiqor(selector) {
  const snapshot = reactExports.useSyncExternalStore(
    critiqorStore.subscribe,
    critiqorStore.getState,
    () => serverSnapshot
  );
  return selector(snapshot);
}
const severityColor = {
  info: {
    bg: "bg-sky-500/10",
    text: "text-sky-400",
    border: "border-sky-500/30",
    ring: "ring-sky-500/30",
    dot: "bg-sky-400"
  },
  low: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
    ring: "ring-emerald-500/30",
    dot: "bg-emerald-400"
  },
  medium: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
    ring: "ring-amber-500/30",
    dot: "bg-amber-400"
  },
  high: {
    bg: "bg-orange-500/10",
    text: "text-orange-400",
    border: "border-orange-500/30",
    ring: "ring-orange-500/30",
    dot: "bg-orange-400"
  },
  critical: {
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/30",
    ring: "ring-red-500/30",
    dot: "bg-red-400"
  }
};
const trustColor = {
  high: {
    bg: "bg-emerald-500/10",
    text: "text-emerald-400",
    border: "border-emerald-500/30",
    label: "Healthy"
  },
  medium: {
    bg: "bg-amber-500/10",
    text: "text-amber-400",
    border: "border-amber-500/30",
    label: "Needs Attention"
  },
  low: {
    bg: "bg-red-500/10",
    text: "text-red-400",
    border: "border-red-500/30",
    label: "Critical"
  }
};
const groups = [
  {
    title: "Overview",
    items: [{ title: "Overview", url: "/", icon: LayoutDashboard }]
  },
  {
    title: "Workspace",
    items: [
      { title: "Runs", url: "/runs", icon: CirclePlay },
      { title: "Diagnosis", url: "/diagnoses", icon: Stethoscope },
      { title: "Playbook", url: "/playbook", icon: Wrench }
    ]
  },
  {
    title: "Settings",
    items: [
      { title: "Evidence Explorer", url: "/evidence", icon: FileSearch },
      { title: "Visibility", url: "/settings", icon: Eye },
      { title: "Appearance", url: "/appearance", icon: Palette }
    ]
  }
];
function NavigationGroup({ group, runId }) {
  const [open, setOpen] = reactExports.useState(true);
  const pathname = useRouterState({ select: (router2) => router2.location.pathname });
  const active = (url) => url === "/" ? pathname === "/" : pathname.startsWith(url);
  const search = runId ? { run_id: runId } : void 0;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(SidebarGroup, { className: "py-1 group-data-[collapsible=icon]:px-0", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs(
      "button",
      {
        type: "button",
        onClick: () => setOpen((value) => !value),
        className: "flex w-full items-center justify-between rounded-md px-2 py-1 text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-sidebar-foreground/55 hover:bg-sidebar-accent hover:text-sidebar-foreground group-data-[collapsible=icon]:hidden",
        "aria-expanded": open,
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: group.title }),
          /* @__PURE__ */ jsxRuntimeExports.jsx(ChevronDown, { className: `size-3.5 transition-transform ${open ? "" : "-rotate-90"}` })
        ]
      }
    ),
    open && /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarGroupContent, { className: "mt-1", children: /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarMenu, { children: group.items.map((item) => /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarMenuItem, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      SidebarMenuButton,
      {
        asChild: true,
        isActive: active(item.url),
        tooltip: item.title,
        className: "h-9 rounded-lg transition-colors hover:bg-sidebar-accent data-[active=true]:bg-primary data-[active=true]:text-primary-foreground group-data-[collapsible=icon]:mx-auto",
        children: /* @__PURE__ */ jsxRuntimeExports.jsxs(Link, { to: item.url, search, children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(item.icon, { className: "size-4" }),
          /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: item.title })
        ] })
      }
    ) }, `${group.title}-${item.title}`)) }) })
  ] });
}
function AppSidebar() {
  const runId = useCritiqor((state2) => state2.executive.runId);
  const search = runId ? { run_id: runId } : void 0;
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(Sidebar, { collapsible: "icon", className: "border-r border-sidebar-border/70", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarHeader, { className: "px-3 py-4 group-data-[collapsible=icon]:p-2", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
      Link,
      {
        to: "/",
        search,
        className: "flex items-center gap-2.5 rounded-lg p-1 hover:bg-sidebar-accent",
        children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(
            "img",
            {
              src: logo,
              alt: "Critiqor",
              className: "size-10 shrink-0 scale-110 rounded-lg border border-sidebar-border bg-black object-cover group-data-[collapsible=icon]:size-8 group-data-[collapsible=icon]:scale-100"
            }
          ),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-w-0 group-data-[collapsible=icon]:hidden", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "font-semibold tracking-tight leading-tight", children: "Critiqor" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "text-[10px] uppercase tracking-widest text-sidebar-foreground/50", children: "Runtime evaluation" })
          ] })
        ]
      }
    ) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarContent, { className: "px-2 group-data-[collapsible=icon]:px-1", children: groups.map((group) => /* @__PURE__ */ jsxRuntimeExports.jsx(NavigationGroup, { group, runId }, group.title)) }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarFooter, { className: "border-t border-sidebar-border/70 p-2", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(SidebarMenu, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarMenuItem, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarMenuButton, { asChild: true, tooltip: "Documentation", className: "h-9 rounded-lg", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "a",
        {
          href: "https://critiqor-71f5274a.mintlify.site/introduction",
          target: "_blank",
          rel: "noreferrer",
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(BookOpen, { className: "size-4" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Documentation" })
          ]
        }
      ) }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarMenuItem, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarMenuButton, { asChild: true, tooltip: "Website", className: "h-9 rounded-lg", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
        "a",
        {
          href: "https://critiqor-runtime-insight.vercel.app/",
          target: "_blank",
          rel: "noreferrer",
          children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(Earth, { className: "size-4" }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Website" })
          ]
        }
      ) }) }),
      /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarMenuItem, { children: /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarMenuButton, { asChild: true, tooltip: "Repository", className: "h-9 rounded-lg", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("a", { href: "https://github.com/web3curtis/Critiqor", target: "_blank", rel: "noreferrer", children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(Github, { className: "size-4" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("span", { children: "Repo" })
      ] }) }) })
    ] }) })
  ] });
}
const Toaster = ({ ...props }) => {
  return /* @__PURE__ */ jsxRuntimeExports.jsx(
    Toaster$1,
    {
      className: "toaster group",
      toastOptions: {
        classNames: {
          toast: "group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg",
          description: "group-[.toast]:text-muted-foreground",
          actionButton: "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
          cancelButton: "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground"
        }
      },
      ...props
    }
  );
};
const asRecord$1 = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : {};
const asArray$1 = (value) => Array.isArray(value) ? value : [];
const asString = (value, fallback = "") => value == null ? fallback : String(value);
const asNumber = (value, fallback = 0) => {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
};
function frameworkDisplayName(value) {
  const framework = asString(value, "agent").trim();
  const known = {
    codex: "Codex",
    openclaw: "OpenClaw",
    webmcp: "WebMCP",
    "claude-code": "Claude Code",
    claude_code: "Claude Code"
  };
  const normalized = framework.toLowerCase();
  return known[normalized] ?? framework.split(/[-_\s]+/).filter(Boolean).map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}
function resolveCritiqorApiBase() {
  if (typeof window === "undefined") return "";
  const url = new URL(window.location.href);
  const queryBase = url.searchParams.get("critiqor_api") ?? url.searchParams.get("api");
  if (queryBase) {
    window.localStorage.setItem("critiqor_api_base", queryBase.replace(/\/$/, ""));
    return queryBase.replace(/\/$/, "");
  }
  return (window.localStorage.getItem("critiqor_api_base") ?? void 0 ?? "").replace(/\/$/, "");
}
async function fetchCritiqorRuns(apiBase = resolveCritiqorApiBase(), selectedRunId = resolveSelectedRunId()) {
  try {
    const response = await fetch(`${apiBase}/api/runs`, {
      credentials: apiBase ? "omit" : "same-origin",
      headers: typeof window !== "undefined" && window.sessionStorage.getItem("critiqor_access_credential") ? {
        authorization: `Bearer ${window.sessionStorage.getItem("critiqor_access_credential")}`
      } : {}
    });
    if (!response.ok) throw new Error(`Critiqor API returned ${response.status}`);
    const payload = await response.json();
    const runs = Array.isArray(payload) ? payload : asArray$1(payload.runs);
    return normalizeDashboardRuns(runs, apiBase, selectedRunId);
  } catch (error) {
    throw error;
  }
}
function resolveSelectedRunId() {
  if (typeof window === "undefined") return "";
  const url = new URL(window.location.href);
  return url.searchParams.get("run_id") ?? url.searchParams.get("run") ?? "";
}
function orderRuns(rawRuns, selectedRunId = "") {
  const sorted = [...rawRuns].sort((a, b) => runTimestamp(b).localeCompare(runTimestamp(a)));
  if (!selectedRunId) return sorted;
  const selected = sorted.find((run) => asString(run.run_id) === selectedRunId);
  if (!selected) return sorted;
  return [selected, ...sorted.filter((run) => asString(run.run_id) !== selectedRunId)];
}
function normalizeDashboardRuns(rawRuns, apiBase = "", selectedRunId = "") {
  const state2 = emptyState();
  if (!rawRuns.length) {
    return {
      ...state2,
      sync: { loading: false, source: "empty", lastUpdated: (/* @__PURE__ */ new Date()).toISOString(), apiBase }
    };
  }
  const ordered = orderRuns(rawRuns, selectedRunId);
  const selected = selectedRunId ? rawRuns.find((run) => asString(run.run_id) === selectedRunId) : ordered[0];
  if (selectedRunId && !selected) {
    const empty = emptyState();
    return {
      ...empty,
      runs: ordered.map(toRun),
      sync: { loading: false, source: "empty", lastUpdated: (/* @__PURE__ */ new Date()).toISOString(), apiBase },
      executive: {
        ...empty.executive,
        runId: selectedRunId,
        summary: "The selected run was not found. Another run was not substituted.",
        confidenceReasoning: "More evidence needed"
      }
    };
  }
  const runs = ordered.map(toRun);
  const diagnoses = ordered.flatMap(toDiagnoses);
  const evidence = ordered.flatMap(toEvidence).slice(0, 500);
  const benchmarks = toBenchmarks(ordered);
  const active = selected ?? ordered[0];
  const artifact = artifactMetadata(active);
  const executive = toExecutive(active, artifact);
  return {
    runs,
    diagnoses,
    evidence,
    benchmarks,
    executive,
    scoreExplanations: scoreExplanations(active, artifact),
    agentHealth: agentHealth(active, diagnoses, artifact),
    timeline: runtimeTimeline(active),
    artifact,
    memoryAnalysis: toMemoryAnalysis(active),
    webmcp: toWebMcpAudit(active),
    sync: { loading: false, source: "live", lastUpdated: (/* @__PURE__ */ new Date()).toISOString(), apiBase }
  };
}
function toWebMcpAudit(run) {
  const raw = asRecord$1(run.webmcp_audit);
  const comparison = asRecord$1(run.comparison);
  if (!Object.keys(raw).length) return emptyState().webmcp;
  const matched = comparison.matched === true || Boolean(comparison.match_key);
  return {
    available: true,
    status: asString(raw.status) || "INCONCLUSIVE",
    displayStatus: asString(raw.display_status) || "More evidence needed",
    summary: asString(raw.summary) || "More evidence needed",
    scenariosExercised: presentNumber(raw.scenarios_exercised),
    findingCount: presentNumber(raw.finding_count),
    duplicateEffectCount: presentNumber(raw.duplicate_effect_count),
    authoritativeEffectCount: presentNumber(raw.authoritative_effect_count),
    blindRedispatchCount: raw.blind_redispatch_count == null ? void 0 : presentNumber(raw.blind_redispatch_count),
    confidence: asString(raw.confidence) || void 0,
    strengths: asArray$1(raw.strengths).map((item) => {
      const strength = asRecord$1(item);
      return {
        id: asString(strength.id),
        title: asString(strength.title) || "Not captured",
        detail: asString(strength.detail)
      };
    }),
    comparison: matched ? asString(comparison.verdict) || void 0 : void 0
  };
}
function presentNumber(value) {
  return value == null || value === "" ? 0 : asNumber(value, 0);
}
function toMemoryAnalysis(run) {
  const raw = asRecord$1(asRecord$1(run.evidence_panel).memory_analysis);
  if (!Object.keys(raw).length) return void 0;
  return {
    score: asNumber(raw.score, 100),
    confidence: asNumber(raw.confidence, 0),
    eventCount: asNumber(raw.event_count, 0),
    retrievedCount: asNumber(raw.retrieved_count, 0),
    injectedCount: asNumber(raw.injected_count, 0),
    referencedCount: asNumber(raw.referenced_count, 0),
    unusedCount: asNumber(raw.unused_count, 0),
    irrelevantCount: asNumber(raw.irrelevant_count, 0),
    missedCount: asNumber(raw.missed_count, 0),
    createdCount: asNumber(raw.created_count, 0),
    ignoredCount: asNumber(raw.ignored_count, 0),
    tokenCost: asNumber(raw.token_cost, 0),
    diagnosticSummary: asString(raw.diagnostic_summary, "Memory runtime behavior was captured."),
    architectureStage: asString(raw.architecture_stage, "memory retrieval"),
    evidence: asArray$1(raw.evidence).map(toMemoryEvidenceItem)
  };
}
function toMemoryEvidenceItem(item) {
  const record = asRecord$1(item);
  return {
    eventType: asString(record.event_type, "memory_event"),
    action: asString(record.action, "observed"),
    message: asString(record.message, "Memory runtime event captured."),
    memoryId: asString(record.memory_id, ""),
    reason: asString(record.reason, "Critiqor captured this as a memory-related runtime event."),
    architectureStage: asString(record.architecture_stage, "memory retrieval"),
    confidence: record.confidence == null ? void 0 : asString(record.confidence)
  };
}
function evidenceSummary(run, artifact = artifactMetadata(run)) {
  const failureAnalysis = asRecord$1(run.failure_analysis);
  const causes = asArray$1(failureAnalysis.failure_causes);
  const retrievalEvents = traceEvents(run).filter(
    (event) => /retriev|memory|search/i.test(
      asString(
        event.event ?? event.event_type ?? event.type ?? event.tool_name ?? event.tool ?? ""
      )
    )
  );
  const memory = toMemoryAnalysis(run);
  const repeatedTools = repeatedToolCalls(run);
  return [
    {
      label: "Runtime events",
      value: String(artifact.eventCount),
      detail: `${artifact.eventCount} observed events support this report.`
    },
    {
      label: "Tool calls",
      value: String(artifact.toolCallCount),
      detail: `${artifact.toolCallCount} tool calls and ${artifact.toolOutputCount} tool outputs were captured.`
    },
    {
      label: "Ignored outputs",
      value: String(ignoredOutputCount(run)),
      detail: "Outputs marked unused or skipped contribute to synthesis risk."
    },
    {
      label: "Repeated requests",
      value: String(repeatedTools),
      detail: "Repeated tool calls indicate possible loop or cost pressure."
    },
    {
      label: "Retrieval utilisation",
      value: String(memory?.referencedCount || retrievalEvents.length),
      detail: memory?.eventCount ? `${memory.referencedCount} referenced, ${memory.unusedCount + memory.irrelevantCount} unused or irrelevant, ${memory.missedCount} missed.` : `${retrievalEvents.length} retrieval or memory related events were observed.`
    },
    {
      label: "Failures observed",
      value: String(Math.max(artifact.failureCount, causes.length)),
      detail: "Failure causes come from Critiqor diagnosis artifacts and runtime error events."
    },
    {
      label: "Runtime duration",
      value: `${(artifact.durationMs / 1e3).toFixed(1)}s`,
      detail: "Duration is estimated from the first and last runtime event timestamps."
    }
  ];
}
function scoreExplanations(run, artifact) {
  const summary = asRecord$1(run.executive_summary);
  const trust = presentNumber(summary.trust_score);
  const confidence = presentNumber(summary.evaluation_confidence ?? run.evaluation_confidence);
  const failures = Math.max(
    artifact.failureCount,
    asArray$1(asRecord$1(run.failure_analysis).failure_causes).length
  );
  const memory = toMemoryAnalysis(run);
  const explanations = [
    {
      score: "Trust Score",
      value: `${trust}/100`,
      tier: scoreTier(trust),
      why: `The trust score reflects runtime evidence quality, failure impact, and observed execution stability. ${failures ? `${failures} failure signal(s) reduced the score.` : "No major failure signals were detected."}`,
      evidence: evidenceSummary(run, artifact).slice(0, 6)
    },
    {
      score: "Evaluation Confidence",
      value: `${confidence}%`,
      tier: scoreTier(confidence),
      why: confidenceReasoning(run, artifact, confidence),
      evidence: evidenceSummary(run, artifact).filter(
        (item) => ["Runtime events", "Tool calls", "Failures observed"].includes(item.label)
      )
    },
    {
      score: "Operational Stability",
      value: `${Math.max(0, 100 - repeatedToolCalls(run) * 8 - ignoredOutputCount(run) * 6)}/100`,
      tier: scoreTier(Math.max(0, 100 - repeatedToolCalls(run) * 8 - ignoredOutputCount(run) * 6)),
      why: "This score is derived from duplicate actions, ignored tool outputs, runtime errors, and evidence utilisation.",
      evidence: evidenceSummary(run, artifact).filter(
        (item) => ["Ignored outputs", "Repeated requests", "Runtime duration"].includes(item.label)
      )
    }
  ];
  if (memory?.eventCount) {
    explanations.push({
      score: "Memory Utilization",
      value: `${memory.score}/100`,
      tier: scoreTier(memory.score),
      why: `${memory.diagnosticSummary} Critiqor scored memory from runtime lookup, context injection, and response-use evidence.`,
      evidence: [
        {
          label: "Retrieved",
          value: String(memory.retrievedCount),
          detail: "Memory candidates observed during runtime lookup."
        },
        {
          label: "Referenced",
          value: String(memory.referencedCount),
          detail: "Retrieved memories supported by response or reasoning evidence."
        },
        {
          label: "Unused or irrelevant",
          value: String(memory.unusedCount + memory.irrelevantCount),
          detail: "Memories retrieved or injected without supported runtime use."
        }
      ]
    });
  }
  return explanations;
}
function confidenceReasoning(run, artifact, confidence) {
  const evidenceLevel = asString(
    asRecord$1(run.executive_summary).evidence_level ?? run.evidence_level,
    "trace_available"
  );
  const coverage = artifact.toolCallCount || artifact.eventCount ? "runtime instrumentation captured observable activity" : "limited runtime activity was captured";
  return `${confidence}% confidence because evidence level is ${evidenceLevel}, ${artifact.eventCount} runtime events were collected, ${artifact.toolCallCount} tool execution(s) were observed, and ${coverage}.`;
}
function agentHealth(run, diagnoses, artifact) {
  const webmcp = toWebMcpAudit(run);
  const failures = diagnoses.filter((d) => d.runId === asString(run.run_id) && d.findingId).length;
  const stable = webmcp.available ? webmcp.status === "PASSED" : failures === 0 || asNumber(asRecord$1(run.executive_summary).trust_score, 0) >= 85;
  const strengths = webmcp.strengths.map((item) => item.title).filter(Boolean);
  return {
    status: stable ? "Healthy execution profile" : "Needs reliability review",
    strengths: strengths.length ? strengths : artifact.eventCount ? ["Runtime evidence was captured"] : ["Not captured"],
    stableBehaviours: [
      artifact.toolCallCount ? `${artifact.toolCallCount} tool call(s) captured with ${artifact.toolOutputCount} output event(s).` : "No excessive tool activity was observed.",
      ignoredOutputCount(run) === 0 ? "No ignored tool output signal dominated the run." : `${ignoredOutputCount(run)} ignored output signal(s) require review.`,
      repeatedToolCalls(run) === 0 ? "No repeated API/tool request loop was detected." : `${repeatedToolCalls(run)} repeated request pattern(s) were detected.`
    ],
    recommendedMonitoring: [
      "Track ignored tool outputs across future runs",
      "Watch repeated tool/API calls for loop risk",
      "Compare trust score against bronze, silver, and gold tiers over time"
    ]
  };
}
function artifactMetadata(run) {
  const raw = asRecord$1(run.raw_evidence);
  const artifacts = asRecord$1(run.artifacts);
  const artifactPayloads = asRecord$1(run.artifact_payloads);
  const sessionPayload = asRecord$1(artifactPayloads.session_json);
  const integrity = asRecord$1(sessionPayload.integrity);
  const manifest = asRecord$1(run.evaluation_manifest);
  const signature = asRecord$1(manifest.signature);
  const trace = traceEvents(run);
  const toolCalls = trace.filter(
    (event) => ["tool_call", "webmcp.tool_dispatch"].includes(eventName(event))
  );
  const toolOutputs = trace.filter(
    (event) => ["tool_output", "tool_result", "webmcp.outcome", "webmcp.reconciliation"].includes(
      eventName(event)
    )
  );
  const memoryEvents = trace.filter(
    (event) => ["memory_event", "memory_search", "memory_get"].includes(eventName(event))
  );
  const failureEvents = trace.filter(
    (event) => ["error_event", "failure", "timeout"].includes(eventName(event))
  );
  const start = trace[0] ? Date.parse(asString(trace[0].timestamp ?? trace[0].at, "")) : Number.NaN;
  const endEvent = trace.at(-1);
  const end = endEvent ? Date.parse(asString(endEvent.timestamp ?? endEvent.at, "")) : Number.NaN;
  const integrityStatus = asString(integrity.status ?? manifest.evidence_status, "unknown");
  const evidenceStatus = integrityStatus === "verified" ? signature.algorithm === "hmac-sha256" ? "verified" : "unsigned" : integrityStatus === "tampered" ? "tampered" : integrityStatus === "incomplete" ? "incomplete" : "unknown";
  return {
    diagnosisPath: asString(asRecord$1(artifacts.diagnosis).path) || asString(raw.diagnosis_json) || void 0,
    sessionPath: asString(asRecord$1(artifacts.session).path) || asString(raw.session_json) || void 0,
    playbookPath: asString(asRecord$1(artifacts.improvement_playbook).path) || asString(raw.improvement_playbook) || void 0,
    playbookContent: typeof artifactPayloads.improvement_playbook === "string" ? artifactPayloads.improvement_playbook : void 0,
    eventCount: trace.length,
    toolCallCount: toolCalls.length,
    toolOutputCount: toolOutputs.length,
    memoryEventCount: memoryEvents.length,
    failureCount: failureEvents.length,
    durationMs: Number.isFinite(start) && Number.isFinite(end) ? Math.max(0, end - start) : 0,
    evidenceStatus,
    evidenceDigest: asString(sessionPayload.evidence_digest ?? manifest.evidence_digest, ""),
    redactionCount: asNumber(integrity.redaction_count, 0),
    truncationCount: asNumber(integrity.truncation_count, 0),
    integrityErrors: asArray$1(integrity.errors).map((error) => asString(error)).filter(Boolean)
  };
}
function runtimeTimeline(run) {
  const trace = traceEvents(run);
  if (!trace.length) return [];
  return trace.slice(0, 80).map((event, index) => {
    const type = eventName(event);
    const tool = asString(event.tool_name ?? event.tool ?? asRecord$1(event.payload).toolName, "");
    return {
      id: `${asString(run.run_id, "run")}_timeline_${index}`,
      label: titleize(type),
      at: asString(event.timestamp ?? event.at, runTimestamp(run)),
      detail: asString(event.message ?? event.summary, tool ? `${type} · ${tool}` : type),
      type
    };
  });
}
function traceEvents(run) {
  return asArray$1(asRecord$1(run.evidence_panel).trace).map(asRecord$1);
}
function eventName(event) {
  return asString(event.event ?? event.event_type ?? event.type, "log");
}
function ignoredOutputCount(run) {
  return traceEvents(run).filter((event) => {
    const text = JSON.stringify(event).toLowerCase();
    return text.includes("ignored") || text.includes('"used":false') || text.includes("not used");
  }).length;
}
function repeatedToolCalls(run) {
  const counts = /* @__PURE__ */ new Map();
  for (const event of traceEvents(run)) {
    if (eventName(event) !== "tool_call") continue;
    const key = `${asString(event.tool_name ?? event.tool ?? asRecord$1(event.payload).toolName, "tool")}::${JSON.stringify(event.args ?? asRecord$1(event.payload).args ?? asRecord$1(event.payload).input ?? {})}`;
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.values()].filter((count) => count > 1).reduce((sum, count) => sum + count - 1, 0);
}
function scoreTier(score) {
  if (score >= 90) return "Gold tier";
  if (score >= 75) return "Silver tier";
  return "Bronze tier";
}
function runTimestamp(run) {
  const trace = asArray$1(asRecord$1(run.evidence_panel).trace).map(asRecord$1);
  const first = trace.find((event) => event.timestamp || event.at);
  return asString(first?.timestamp ?? first?.at ?? run.timestamp ?? "1970-01-01T00:00:00.000Z");
}
function trustLevel(score) {
  if (score >= 85) return "high";
  if (score >= 65) return "medium";
  return "low";
}
function severityFromImpact(impact) {
  if (impact >= 24) return "critical";
  if (impact >= 16) return "high";
  if (impact >= 8) return "medium";
  if (impact > 0) return "low";
  return "info";
}
function readinessLabel(value) {
  const readiness = asString(value, "review_recommended");
  return readiness.split("_").map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(" ");
}
function toExecutive(run, artifact) {
  const summary = asRecord$1(run.executive_summary);
  const primary = asRecord$1(run.primary_diagnosis);
  const webmcp = toWebMcpAudit(run);
  const score = presentNumber(summary.trust_score);
  const level = trustLevel(score);
  const runId = asString(run.run_id) || "Not available";
  const framework = run.framework ? frameworkDisplayName(run.framework) : "Not captured";
  const task = asString(asRecord$1(run.experiment).task) || asString(primary.title) || asString(primary.root_cause_failure_type) || "Not captured";
  const chain = asString(summary.summary) || asString(primary.description) || asString(primary.causal_chain_explanation) || "More evidence needed";
  const nextAction = asString(primary.recommended_next_action);
  const evidence = evidenceSummary(run, artifact);
  const confidence = presentNumber(summary.evaluation_confidence ?? run.evaluation_confidence);
  return {
    trustScore: score,
    confidence,
    verdict: summary.readiness_level ? readinessLabel(summary.readiness_level) : "More evidence needed",
    summary: nextAction ? `${chain} Recommended next action: ${nextAction}` : chain,
    runId,
    agent: framework,
    task,
    generatedAt: runTimestamp(run),
    trustLevel: webmcp.status === "FINDING" ? "low" : webmcp.status === "PASSED" ? "high" : level,
    evidence,
    confidenceReasoning: asString(summary.confidence_label) || asString(webmcp.confidence) || confidenceReasoning(run, artifact, confidence)
  };
}
function toRun(run) {
  const summary = asRecord$1(run.executive_summary);
  const score = asNumber(summary.trust_score, 0);
  const status = score >= 85 ? "passed" : "failed";
  const trace = asArray$1(asRecord$1(run.evidence_panel).trace).map(asRecord$1);
  const start = runTimestamp(run);
  const end = asString(trace.at(-1)?.timestamp ?? trace.at(-1)?.at ?? start, start);
  const ignored = ignoredOutputCount(run);
  const repeated = repeatedToolCalls(run);
  const toolCalls = trace.filter((event) => eventName(event) === "tool_call").length;
  const toolOutputs = trace.filter(
    (event) => ["tool_output", "tool_result"].includes(eventName(event))
  ).length;
  const failures = trace.filter(
    (event) => ["error_event", "failure", "timeout"].includes(eventName(event))
  ).length;
  const revisions = trace.filter(
    (event) => /retry|revision|replan|strategy_change/i.test(eventName(event))
  ).length;
  const webmcp = toWebMcpAudit(run);
  return {
    id: asString(run.run_id, "unknown_run"),
    name: `${asString(run.agent_id, "OpenClaw agent")} runtime run`,
    status,
    startedAt: start,
    durationMs: Math.max(0, new Date(end).getTime() - new Date(start).getTime()),
    model: asString(run.framework, "openclaw"),
    trustScore: score,
    hallucinationRisk: Math.min(100, Math.max(0, 100 - score + ignored * 6)),
    toolReliability: toolCalls ? Math.max(
      0,
      Math.min(
        100,
        Math.round(Math.min(toolCalls, toolOutputs) / toolCalls * 100) - failures * 8 - repeated * 5
      )
    ) : failures ? 0 : 100,
    reasoningConsistency: Math.max(
      0,
      Math.min(100, 100 - revisions * 8 - repeated * 6 - failures * 10)
    ),
    webmcpStatus: webmcp.available ? webmcp.displayStatus : void 0,
    webmcpFindings: webmcp.available ? webmcp.findingCount : void 0,
    webmcpEffects: webmcp.available ? webmcp.authoritativeEffectCount : void 0,
    webmcpComparison: webmcp.comparison
  };
}
function toDiagnoses(run) {
  const runId = asString(run.run_id) || "Not available";
  const failureAnalysis = asRecord$1(run.failure_analysis);
  const primary = asRecord$1(run.primary_diagnosis);
  const causes = asArray$1(failureAnalysis.failure_causes).map(asRecord$1);
  if (!causes.length && asString(primary.title)) {
    causes.push(primary);
  }
  return causes.map((cause, index) => {
    const impact = cause.impact == null ? 0 : Math.abs(asNumber(cause.impact, 0));
    const severity = normalizeSeverity(
      cause.severity,
      impact ? severityFromImpact(impact) : "info"
    );
    const evidence = evidenceFromCause(run, cause, index);
    return {
      id: `${runId}_dx_${index + 1}`,
      runId,
      findingId: asString(cause.finding_id) || void 0,
      title: asString(cause.title ?? cause.display_name) || "Not captured",
      severity,
      summary: asString(cause.description) || asString(primary.causal_chain_explanation) || "More evidence needed",
      createdAt: runTimestamp(run),
      trustImpact: impact,
      rootCause: asString(cause.root_cause ?? primary.root_cause_failure_type) || "Not captured",
      recommendedInvestigation: recommendationsFor(asString(cause.type), cause, run),
      verificationSteps: asArray$1(cause.verification_steps).map((item) => asString(item)).filter(Boolean),
      expectedImprovement: asString(cause.expected_improvement) || "Not captured",
      causalChain: asArray$1(cause.causal_chain).map((item) => asString(item)).filter(Boolean),
      confidence: asString(cause.confidence) || void 0,
      confirmedImpact: asString(cause.confirmed_impact) || void 0,
      potentialImpact: asString(cause.potential_impact) || void 0,
      evidence,
      counterEvidence: asArray$1(cause.counter_evidence).map((item, i) => {
        const event = evidenceItem(item, `${runId}_counter_${index}_${i}`, runId);
        return { ...event, type: evidenceType(event.type) };
      }),
      alternativeHypotheses: asArray$1(cause.alternative_hypotheses).map((item) => asString(item)).filter(Boolean),
      engineeringExplanation: asString(cause.engineering_explanation, ""),
      teachingDiagram: teachingDiagramFromCause(cause),
      memoryAnalysis: cause.type === "memory_utilization" ? toMemoryAnalysisFromCause(cause, run) : void 0,
      graph: graphFromRun(run)
    };
  });
}
function toMemoryAnalysisFromCause(cause, run) {
  const raw = asRecord$1(cause.memory_analysis);
  if (!Object.keys(raw).length) return toMemoryAnalysis(run);
  return toMemoryAnalysis({ ...run, evidence_panel: { memory_analysis: raw } });
}
function teachingDiagramFromCause(cause) {
  const diagram = asRecord$1(cause.teaching_diagram);
  const stages = asArray$1(diagram.stages).map((item) => asString(item)).filter(Boolean);
  if (!stages.length) return void 0;
  return {
    stages,
    highlight: asString(diagram.highlight, stages[0])
  };
}
function normalizeSeverity(value, fallback) {
  const text = asString(value).toLowerCase();
  return ["info", "low", "medium", "high", "critical"].includes(text) ? text : fallback;
}
function evidenceFromCause(run, cause, index) {
  const runId = asString(run.run_id) || "Not available";
  const explicit = [...asArray$1(cause.evidence), ...asArray$1(cause.evidence_refs)];
  if (!explicit.length) return [];
  return explicit.map((item, i) => {
    const event = evidenceItem(item, `${runId}_cause_${index}_${i}`, runId);
    return { ...event, type: evidenceType(event.type) };
  });
}
function toEvidence(run) {
  const runId = asString(run.run_id, "unknown_run");
  const trace = asArray$1(asRecord$1(run.evidence_panel).trace);
  return trace.map((item, index) => evidenceItem(item, `${runId}_ev_${index}`, runId));
}
function evidenceItem(item, id, runId) {
  const event = asRecord$1(item);
  const type = asString(event.event ?? event.event_type ?? event.type, "log");
  const payload = asRecord$1(event.payload);
  const tool = asString(event.tool ?? event.tool_name ?? event.name ?? payload.toolName, "");
  const memoryReason = asString(payload.reason, "");
  const memoryAction = asString(payload.action ?? payload.operation ?? payload.status, "");
  const message = asString(
    event.message ?? event.label ?? event.summary,
    type === "memory_event" && memoryReason ? `Memory ${memoryAction || "observed"}: ${memoryReason}` : tool ? `${type}: ${tool}` : type
  );
  return {
    id,
    runId,
    type,
    message,
    at: asString(event.timestamp ?? event.at, (/* @__PURE__ */ new Date()).toISOString()),
    payload: event
  };
}
function evidenceType(type) {
  if (type === "tool_call") return "tool_call";
  if (type === "tool_output") return "tool_output";
  if (type === "memory_event" || type === "memory") return "memory";
  if (type === "retry_event" || type === "retry") return "retry";
  if (type === "token_usage") return "metric";
  if (type === "context_event") return "context";
  if (type === "failure" || type === "diagnosis") return "judge";
  return "log";
}
function graphFromRun(run) {
  const graph = asRecord$1(asRecord$1(run.evidence_panel).causal_graph);
  const nodes = asArray$1(graph.nodes).map(asRecord$1).map((node, index) => ({
    id: asString(node.id, `node_${index}`),
    label: asString(node.label ?? node.type, `Step ${index + 1}`),
    kind: asString(node.kind ?? node.type, "event")
  }));
  const edges = asArray$1(graph.edges).map(asRecord$1).map((edge, index) => ({
    id: asString(edge.id, `edge_${index}`),
    source: asString(edge.source ?? edge.from, ""),
    target: asString(edge.target ?? edge.to, ""),
    label: asString(edge.label ?? edge.relation, "")
  })).filter((edge) => edge.source && edge.target);
  return nodes.length ? { nodes, edges } : void 0;
}
function toBenchmarks(runs) {
  return runs.slice(0, 8).map((run) => {
    const summary = asRecord$1(run.executive_summary);
    const score = asNumber(summary.trust_score, 0);
    return {
      id: `${asString(run.run_id, "run")}_trust`,
      name: `${asString(run.agent_id, "OpenClaw")} trust score`,
      metric: "trust_score",
      target: 85,
      actual: score,
      unit: "pts",
      passed: score >= 85,
      updatedAt: runTimestamp(run)
    };
  });
}
function recommendationsFor(_type, cause = {}, run = {}) {
  return [
    ...asArray$1(cause.recommendations),
    cause.recommendation,
    ...asArray$1(run.recommendations)
  ].filter((item) => typeof item === "string" && item.length > 0);
}
function buildFixPrompt(input) {
  const pathOrMissing = (value) => value || "Not available — use the remaining artifact listed above.";
  return `# Critiqor runtime remediation task

You are improving the agent from Critiqor run ${input.runId}.

Before changing code, read these complete artifacts:
- Runtime session: ${pathOrMissing(input.sessionPath)}
- Diagnosis: ${pathOrMissing(input.diagnosisPath)}
- Improvement playbook: ${pathOrMissing(input.playbookPath)}

Use session.json as the authoritative runtime record. Trace every diagnosis claim to its event sequence_id/event_hash. Use diagnosis.json for the supported causal analysis, counterevidence, alternatives, strengths, and comparison metadata. Follow the playbook, but verify its claims against the runtime yourself.

Task attempted:
${input.task || "Not captured"}

Observed result and primary diagnosis:
${input.summary || "More evidence needed"}
${input.severity ? `Severity: ${input.severity}` : "Severity: Not captured"}
${input.confidence ? `Confidence: ${input.confidence}` : "Confidence: More evidence needed"}
Authoritative effects: ${input.effectCount ?? "Not captured"}
Duplicate effects: ${input.duplicateCount ?? "Not captured"}

Evidence to inspect first:
${input.evidence.length ? input.evidence.map(
    (item) => `- sequence ${item.sequence ?? "Not captured"} hash ${item.hash ?? "Not captured"}${item.message ? ` — ${item.message}` : ""}`
  ).join("\n") : "- More evidence needed"}

Root cause and causal chain:
${input.rootCause || "Not captured"}
${(input.causalChain ?? []).map((step, index) => `${index + 1}. ${step}`).join("\n") || "- Not captured"}

Required improvements:
${input.recommendations.map((step, index) => `${index + 1}. ${step}`).join("\n") || "1. More evidence needed"}

Strengths to preserve:
${input.strengths.map((item) => `- ${item}`).join("\n") || "- Not captured"}

Implementation constraints:
- Treat timeout/cancellation/disconnect/navigation/lost response after a consequential call as unknown, not failed.
- Do not blindly retry an unresolved consequential action.
- Reconcile authoritative state before any effect-equivalent retry.
- Preserve stable operation identity and intent binding.

Verification:
${input.verification.map((step) => `- ${step}`).join("\n") || "- Rerun the same scenario with Critiqor and compare authoritative effects."}

Deliverables:
1. Explain the failure path using cited runtime events.
2. Implement the smallest complete reliability fix.
3. Add or update tests for the exact adversity.
4. Rerun the same scenario with Critiqor.
5. Report before/after findings, authoritative effects, duplicate effects, and any regression.

Do not claim the issue is resolved unless the same scenario is exercised and the target-side authoritative evidence supports the result.
`;
}
function titleize(value) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}
function runIdFromSearch(search) {
  if (typeof search === "string") {
    const params = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
    return params.get("run_id") ?? params.get("run") ?? "";
  }
  if (search && typeof search === "object") {
    const record = search;
    const value = record.run_id ?? record.run;
    return value == null ? "" : String(value);
  }
  return "";
}
function CritiqorDataSync() {
  const apiBase = resolveCritiqorApiBase();
  const search = useRouterState({ select: (state2) => state2.location.search });
  const selectedRunId = runIdFromSearch(search) || resolveSelectedRunId();
  const query = useQuery({
    queryKey: ["critiqor-runs", apiBase, selectedRunId],
    queryFn: () => fetchCritiqorRuns(apiBase, selectedRunId),
    refetchInterval: 5e3,
    retry: 1
  });
  reactExports.useEffect(() => {
    const current = critiqorStore.getState();
    if (!selectedRunId || current.executive.runId === selectedRunId) return;
    critiqorStore.replace({
      diagnoses: current.diagnoses.filter((item) => item.runId === selectedRunId),
      evidence: current.evidence.filter((item) => item.runId === selectedRunId),
      timeline: [],
      memoryAnalysis: void 0,
      artifact: {
        ...current.artifact,
        sessionPath: "",
        diagnosisPath: "",
        playbookPath: "",
        playbookContent: "",
        evidenceStatus: "unknown",
        eventCount: 0,
        toolCallCount: 0,
        toolOutputCount: 0,
        memoryEventCount: 0
      },
      executive: {
        ...current.executive,
        runId: selectedRunId,
        task: "",
        summary: "Loading selected run..."
      },
      webmcp: {
        available: false,
        status: "NOT_EXERCISED",
        displayStatus: "Loading",
        summary: "Loading selected run...",
        scenariosExercised: 0,
        findingCount: 0,
        duplicateEffectCount: 0,
        authoritativeEffectCount: 0,
        strengths: []
      }
    });
  }, [selectedRunId]);
  reactExports.useEffect(() => {
    critiqorStore.setSyncStatus({ loading: query.isLoading, apiBase });
  }, [apiBase, query.isLoading]);
  reactExports.useEffect(() => {
    if (query.data) critiqorStore.replace(query.data);
  }, [query.data]);
  reactExports.useEffect(() => {
    if (query.error) {
      critiqorStore.setSyncStatus({
        loading: false,
        source: "error",
        error: query.error instanceof Error ? query.error.message : "Unable to reach Critiqor API",
        apiBase
      });
    }
  }, [apiBase, query.error]);
  return null;
}
const storageKey$1 = "critiqor-theme";
function applyTheme(mode) {
  const dark = mode === "dark" || mode === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches;
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.dataset.theme = mode;
  window.localStorage.setItem(storageKey$1, mode);
}
function savedTheme() {
  const value = window.localStorage.getItem(storageKey$1);
  return value === "light" || value === "dark" ? value : "system";
}
function ThemeManager() {
  reactExports.useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const update = () => applyTheme(savedTheme());
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  return null;
}
const currentVersion = "0.2.19";
const newerThan = (next, current) => {
  const left = next.split(".").map(Number);
  const right = current.split(".").map(Number);
  return left.some(
    (value, index) => value > (right[index] ?? 0) && left.slice(0, index).every((part, i) => part === right[i])
  );
};
function UpdateNotice() {
  const [latest, setLatest] = reactExports.useState();
  const [dismissed, setDismissed] = reactExports.useState(false);
  reactExports.useEffect(() => {
    fetch("https://pypi.org/pypi/critiqor/json").then((response) => response.json()).then((payload) => {
      const version = String(payload?.info?.version ?? "");
      if (version && newerThan(version, currentVersion)) setLatest(version);
    }).catch(() => void 0);
  }, []);
  if (!latest || dismissed) return null;
  const update = async () => {
    await navigator.clipboard.writeText("python3 -m pip install --upgrade critiqor");
    toast.success("Update command copied. Run it in your terminal, then restart Critiqor.");
  };
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex flex-wrap items-center gap-3 border-b border-amber-500/20 bg-amber-500/10 px-4 py-2 text-sm", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsxs("span", { className: "font-medium", children: [
      "Critiqor ",
      latest,
      " is available."
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(Button, { size: "sm", variant: "outline", onClick: update, children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(Copy, { className: "size-3.5" }),
      "Update Now"
    ] }),
    /* @__PURE__ */ jsxRuntimeExports.jsx(
      "button",
      {
        className: "ml-auto rounded p-1 hover:bg-amber-500/10",
        onClick: () => setDismissed(true),
        "aria-label": "Dismiss update",
        children: /* @__PURE__ */ jsxRuntimeExports.jsx(X, { className: "size-4" })
      }
    )
  ] });
}
function AccessGate({ children }) {
  const [mode, setMode] = reactExports.useState("");
  const [allowed, setAllowed] = reactExports.useState(false);
  const [credential, setCredential] = reactExports.useState("");
  const [error, setError] = reactExports.useState("");
  reactExports.useEffect(() => {
    fetch("/api/access").then((r) => r.json()).then((data) => {
      setMode(data.visibility);
      if (!data.requiresCredential) setAllowed(true);
      else if (sessionStorage.getItem("critiqor_access_credential"))
        verify2(sessionStorage.getItem("critiqor_access_credential") || "");
    });
  }, []);
  const verify2 = async (value) => {
    const response = await fetch("/api/access", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ credential: value })
    });
    if (!response.ok) {
      setError(mode === "shared" ? "Invalid invite code." : "Invalid access token.");
      return;
    }
    sessionStorage.setItem("critiqor_access_credential", value);
    setAllowed(true);
  };
  if (allowed) return /* @__PURE__ */ jsxRuntimeExports.jsx(jsxRuntimeExports.Fragment, { children });
  if (!mode)
    return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "grid min-h-screen place-items-center bg-background text-foreground", children: "Loading access policy…" });
  return /* @__PURE__ */ jsxRuntimeExports.jsx("main", { className: "grid min-h-screen place-items-center bg-background p-6 text-foreground", children: /* @__PURE__ */ jsxRuntimeExports.jsxs(
    "form",
    {
      className: "w-full max-w-md rounded-2xl border bg-card p-8 shadow-xl",
      onSubmit: (event) => {
        event.preventDefault();
        verify2(credential);
      },
      children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mb-5 grid size-12 place-items-center rounded-xl bg-primary/15 text-primary", children: /* @__PURE__ */ jsxRuntimeExports.jsx(LockKeyhole, {}) }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-2xl font-bold", children: mode === "shared" ? "Shared dashboard" : "Private dashboard" }),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("p", { className: "mt-2 text-sm text-muted-foreground", children: [
          "Enter the ",
          mode === "shared" ? "invite code" : "new access token",
          " printed by the Critiqor CLI for this launch."
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("label", { className: "mt-6 block text-sm font-semibold", children: mode === "shared" ? "Invite code" : "Access token" }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "input",
          {
            autoFocus: true,
            value: credential,
            onChange: (event) => setCredential(event.target.value),
            className: "mt-2 w-full rounded-lg border bg-background px-3 py-2.5 font-mono"
          }
        ),
        error && /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-2 text-sm text-red-500", children: error }),
        /* @__PURE__ */ jsxRuntimeExports.jsx("button", { className: "mt-5 w-full rounded-lg bg-primary px-4 py-2.5 font-semibold text-primary-foreground", children: "Open dashboard" })
      ]
    }
  ) });
}
function NotFoundComponent() {
  if (typeof window !== "undefined") window.location.replace("/");
  return null;
}
function ErrorComponent({ error, reset }) {
  const router2 = useRouter();
  reactExports.useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);
  return /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "flex min-h-screen items-center justify-center bg-background px-4", children: /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "max-w-md text-center", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("h1", { className: "text-xl font-semibold text-foreground", children: "Something went wrong" }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("p", { className: "mt-2 text-sm text-muted-foreground", children: error.message }),
    /* @__PURE__ */ jsxRuntimeExports.jsx("div", { className: "mt-6 flex justify-center gap-2", children: /* @__PURE__ */ jsxRuntimeExports.jsx(
      "button",
      {
        onClick: () => {
          router2.invalidate();
          reset();
        },
        className: "rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90",
        children: "Try again"
      }
    ) })
  ] }) });
}
const Route$b = createRootRouteWithContext()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Critiqor" },
      { name: "description", content: "Critiqor — agent evaluation, diagnoses, and trust." }
    ],
    links: [{ rel: "stylesheet", href: appCss }]
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent
});
function RootShell({ children }) {
  return /* @__PURE__ */ jsxRuntimeExports.jsxs("html", { lang: "en", children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx("head", { children: /* @__PURE__ */ jsxRuntimeExports.jsx(HeadContent, {}) }),
    /* @__PURE__ */ jsxRuntimeExports.jsxs("body", { children: [
      children,
      /* @__PURE__ */ jsxRuntimeExports.jsx(Scripts, {})
    ] })
  ] });
}
function RootComponent() {
  const { queryClient } = Route$b.useRouteContext();
  return /* @__PURE__ */ jsxRuntimeExports.jsxs(QueryClientProvider, { client: queryClient, children: [
    /* @__PURE__ */ jsxRuntimeExports.jsx(ThemeManager, {}),
    /* @__PURE__ */ jsxRuntimeExports.jsxs(AccessGate, { children: [
      /* @__PURE__ */ jsxRuntimeExports.jsx(CritiqorDataSync, {}),
      /* @__PURE__ */ jsxRuntimeExports.jsxs(SidebarProvider, { children: [
        /* @__PURE__ */ jsxRuntimeExports.jsx(
          "a",
          {
            href: "#main-content",
            className: "fixed left-3 top-3 z-50 -translate-y-20 rounded-md bg-background px-3 py-2 text-sm font-medium shadow focus:translate-y-0",
            children: "Skip to diagnosis content"
          }
        ),
        /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "min-h-screen flex w-full bg-background", children: [
          /* @__PURE__ */ jsxRuntimeExports.jsx(AppSidebar, {}),
          /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "flex-1 flex flex-col min-w-0", children: [
            /* @__PURE__ */ jsxRuntimeExports.jsx(UpdateNotice, {}),
            /* @__PURE__ */ jsxRuntimeExports.jsxs("header", { className: "h-13 flex items-center gap-3 border-b px-4 sticky top-0 bg-background/85 backdrop-blur-xl z-10", children: [
              /* @__PURE__ */ jsxRuntimeExports.jsx(SidebarTrigger, {}),
              /* @__PURE__ */ jsxRuntimeExports.jsxs("div", { className: "text-xs text-muted-foreground", children: [
                "Critiqor ",
                /* @__PURE__ */ jsxRuntimeExports.jsx("span", { className: "mx-1 opacity-50", children: "/" }),
                " Runtime evaluation"
              ] })
            ] }),
            /* @__PURE__ */ jsxRuntimeExports.jsx("main", { id: "main-content", tabIndex: -1, className: "flex-1 min-w-0", children: /* @__PURE__ */ jsxRuntimeExports.jsx(Outlet, {}) })
          ] })
        ] }),
        /* @__PURE__ */ jsxRuntimeExports.jsx(Toaster, {})
      ] })
    ] })
  ] });
}
const $$splitComponentImporter$6 = () => import("./settings-DBIel2GU.mjs");
const Route$a = createFileRoute("/settings")({
  head: () => ({
    meta: [{
      title: "Visibility — Critiqor"
    }]
  }),
  component: lazyRouteComponent($$splitComponentImporter$6, "component")
});
const $$splitComponentImporter$5 = () => import("./runs-D-PIEdl2.mjs");
const Route$9 = createFileRoute("/runs")({
  head: () => ({
    meta: [{
      title: "Runs — Critiqor"
    }]
  }),
  component: lazyRouteComponent($$splitComponentImporter$5, "component")
});
const $$splitComponentImporter$4 = () => import("./playbook-rCmZY5ut.mjs");
const Route$8 = createFileRoute("/playbook")({
  head: () => ({
    meta: [{
      title: "Playbook — Critiqor"
    }]
  }),
  component: lazyRouteComponent($$splitComponentImporter$4, "component")
});
const $$splitComponentImporter$3 = () => import("./evidence-BNrfe_56.mjs");
const Route$7 = createFileRoute("/evidence")({
  head: () => ({
    meta: [{
      title: "Evidence Explorer — Critiqor"
    }]
  }),
  component: lazyRouteComponent($$splitComponentImporter$3, "component")
});
const $$splitComponentImporter$2 = () => import("./diagnoses-BPvvx8bl.mjs");
const Route$6 = createFileRoute("/diagnoses")({
  head: () => ({
    meta: [{
      title: "Diagnosis — Critiqor"
    }]
  }),
  component: lazyRouteComponent($$splitComponentImporter$2, "component")
});
const $$splitComponentImporter$1 = () => import("./appearance-6Pv8vKmY.mjs");
const Route$5 = createFileRoute("/appearance")({
  head: () => ({
    meta: [{
      title: "Appearance — Critiqor"
    }]
  }),
  component: lazyRouteComponent($$splitComponentImporter$1, "component")
});
const $$splitComponentImporter = () => import("./index-6MlyV0sl.mjs");
const Route$4 = createFileRoute("/")({
  head: () => ({
    meta: [{
      title: "Overview — Critiqor"
    }]
  }),
  component: lazyRouteComponent($$splitComponentImporter, "component")
});
const store = () => {
  const g = globalThis;
  if (!g.__critiqorRuns) g.__critiqorRuns = /* @__PURE__ */ new Map();
  return g.__critiqorRuns;
};
const durableRoot = () => path.resolve(
  process.env.CRITIQOR_DASHBOARD_STATE_DIR ?? path.join(process.cwd(), ".critiqor-dashboard-state")
);
const storageKey = (value) => createHash("sha256").update(value, "utf8").digest("hex");
const tenantDirectory = (tenantId) => path.join(durableRoot(), storageKey(tenantId));
const durableFile = (tenantId, runId) => path.join(tenantDirectory(tenantId), `${storageKey(runId)}.json`);
const persistRun = (run, tenantId) => {
  const directory = tenantDirectory(tenantId);
  mkdirSync(directory, { recursive: true, mode: 448 });
  const destination = durableFile(tenantId, getRunId(run));
  const temporary = `${destination}.${process.pid}.${Date.now()}.tmp`;
  writeFileSync(temporary, `${JSON.stringify(run)}
`, { encoding: "utf8", mode: 384 });
  renameSync(temporary, destination);
};
const durableRuns = (tenantId) => {
  const directory = tenantDirectory(tenantId);
  if (!existsSync(directory)) return [];
  return readdirSync(directory).filter((name) => name.endsWith(".json")).map((name) => readJson(path.join(directory, name))).filter((run) => Boolean(run)).filter((run) => String(run.tenant_id ?? "default") === tenantId);
};
const asRecord = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : {};
const asArray = (value) => Array.isArray(value) ? value : [];
const canonicalJson = (value) => {
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  if (value && typeof value === "object") {
    const entries = Object.entries(value).filter(([, item]) => item !== void 0).sort(([left], [right]) => left.localeCompare(right));
    return `{${entries.map(([key, item]) => `${JSON.stringify(key)}:${canonicalJson(item)}`).join(",")}}`;
  }
  return JSON.stringify(value) ?? "null";
};
const sha256 = (value) => createHash("sha256").update(canonicalJson(value), "utf8").digest("hex");
const verifyAuthoritativeArtifact = (payload, tenantId) => {
  const manifest = asRecord(payload.evaluation_manifest);
  const signature = asRecord(manifest.signature);
  const publicKey = process.env.CRITIQOR_SIGNING_PUBLIC_KEY;
  if (signature.algorithm !== "ed25519" || !publicKey) {
    return { valid: false, error: "ed25519_verifier_not_configured" };
  }
  if (String(manifest.run_id ?? "") !== getRunId(payload) || String(manifest.tenant_id ?? "") !== tenantId || String(manifest.evidence_status ?? "") !== "verified") {
    return { valid: false, error: "manifest_identity_or_evidence_mismatch" };
  }
  const unsigned = { ...manifest };
  delete unsigned.signature;
  const rawPublicKey = Buffer.from(publicKey, "base64");
  const derPrefix = Buffer.from("302a300506032b6570032100", "hex");
  let signatureValid = false;
  try {
    signatureValid = verify(
      null,
      Buffer.from(canonicalJson(unsigned), "utf8"),
      createPublicKey({
        key: Buffer.concat([derPrefix, rawPublicKey]),
        format: "der",
        type: "spki"
      }),
      Buffer.from(String(signature.value ?? ""), "base64")
    );
  } catch {
    return { valid: false, error: "invalid_ed25519_material" };
  }
  if (!signatureValid) return { valid: false, error: "manifest_signature_mismatch" };
  const diagnosis = { ...payload };
  delete diagnosis.evaluation_manifest;
  if (sha256(diagnosis) !== String(manifest.diagnosis_digest ?? "")) {
    return { valid: false, error: "diagnosis_digest_mismatch" };
  }
  const trace = asArray(payload.trace);
  if (sha256(trace) !== String(manifest.evidence_digest ?? "") || trace.length !== Number(manifest.evidence_event_count)) {
    return { valid: false, error: "evidence_digest_mismatch" };
  }
  return { valid: true };
};
const getRunId = (payload) => {
  const direct = payload.run_id ?? payload.runId;
  if (direct) return String(direct);
  const nested = payload.executive_summary;
  if (nested && typeof nested === "object" && "run_id" in nested)
    return String(nested.run_id);
  return "run_" + Date.now().toString(36);
};
const artifactRoots = () => {
  const configured = [
    process.env.CRITIQOR_DIAGNOSIS_DIR,
    process.env.CRITIQOR_RUNS_DIR,
    process.env.VITE_CRITIQOR_RUNS_DIR
  ].filter(Boolean);
  return [...configured, path.resolve(process.cwd(), "runs")];
};
const readJson = (file) => {
  try {
    return JSON.parse(readFileSync(file, "utf8"));
  } catch {
    return null;
  }
};
const readSessionEvents = (file) => {
  if (!existsSync(file)) return [];
  const payload = readJson(file);
  const events = Array.isArray(payload?.events) ? payload.events : [];
  return events.filter(
    (event) => Boolean(event) && typeof event === "object"
  );
};
const findDiagnosisFiles = () => {
  const files = [];
  for (const root of artifactRoots()) {
    if (!existsSync(root)) continue;
    const stat = statSync(root);
    if (stat.isFile() && path.basename(root) === "diagnosis.json") {
      files.push(root);
      continue;
    }
    if (!stat.isDirectory()) continue;
    for (const name of readdirSync(root)) {
      const candidate = path.join(root, name);
      if (!statSync(candidate).isDirectory()) continue;
      const diagnosis = path.join(candidate, "diagnosis.json");
      if (existsSync(diagnosis)) files.push(diagnosis);
    }
  }
  return Array.from(new Set(files));
};
const attachArtifactEvidence = (diagnosis, diagnosisPath) => {
  const runDir = path.dirname(diagnosisPath);
  const rawEvidence = asRecord(diagnosis.raw_evidence);
  const artifacts = asRecord(diagnosis.artifacts);
  const explicitSession = typeof asRecord(artifacts.session).path === "string" ? String(asRecord(artifacts.session).path) : typeof rawEvidence.session_json === "string" ? rawEvidence.session_json : "";
  const evidencePath = explicitSession && path.isAbsolute(explicitSession) ? explicitSession : path.join(runDir, explicitSession || "session.json");
  const playbookPath = typeof asRecord(artifacts.improvement_playbook).path === "string" ? String(asRecord(artifacts.improvement_playbook).path) : typeof rawEvidence.improvement_playbook === "string" ? rawEvidence.improvement_playbook : path.join(runDir, "improvement_playbook.md");
  const playbookContent = existsSync(playbookPath) ? readFileSync(playbookPath, "utf8") : "";
  const trace = readSessionEvents(evidencePath);
  const sessionPayload = readJson(evidencePath);
  const evidencePanel = asRecord(diagnosis.evidence_panel);
  const existingTrace = asArray(evidencePanel.trace);
  const mergedTrace = existingTrace.length ? existingTrace : trace;
  return ensureDashboardView({
    ...diagnosis,
    artifacts: {
      ...artifacts,
      session: { path: evidencePath, relative_path: "session.json" },
      diagnosis: { path: diagnosisPath, relative_path: "diagnosis.json" },
      improvement_playbook: { path: playbookPath, relative_path: "improvement_playbook.md" }
    },
    raw_evidence: {
      ...rawEvidence,
      diagnosis_json: diagnosisPath,
      session_json: evidencePath,
      improvement_playbook: playbookPath
    },
    artifact_payloads: {
      diagnosis_json: diagnosis,
      session_json: sessionPayload,
      improvement_playbook: playbookContent
    },
    evidence_panel: {
      ...evidencePanel,
      trace: mergedTrace,
      tool_calls: asArray(evidencePanel.tool_calls).length ? evidencePanel.tool_calls : mergedTrace.filter(
        (event) => event.event === "tool_call" || event.event_type === "tool_call"
      ),
      tool_outputs: asArray(evidencePanel.tool_outputs).length ? evidencePanel.tool_outputs : mergedTrace.filter(
        (event) => event.event === "tool_output" || event.event_type === "tool_result" || event.event_type === "tool_output"
      ),
      memory_events: asArray(evidencePanel.memory_events).length ? evidencePanel.memory_events : mergedTrace.filter(
        (event) => event.event === "memory_event" || event.event_type === "memory_search" || event.event_type === "memory_get"
      ),
      causal_graph: evidencePanel.causal_graph ?? diagnosis.causal_graph ?? { nodes: [], edges: [] }
    }
  });
};
const artifactRuns = () => findDiagnosisFiles().map((file) => {
  const payload = readJson(file);
  return payload ? attachArtifactEvidence(payload, file) : null;
}).filter(Boolean);
const ensureDashboardView = (payload) => {
  if (payload.executive_summary && payload.evidence_panel) {
    const view = { ...payload };
    view.run_id = getRunId(view);
    return view;
  }
  const summary = asRecord(payload.executive_summary);
  const trustScore = Number(payload.trust_score ?? payload.trustScore ?? summary.trust_score ?? 0) || 0;
  const runId = getRunId(payload);
  const trace = Array.isArray(payload.trace) ? payload.trace : [];
  return {
    ...payload,
    run_id: runId,
    tenant_id: payload.tenant_id ?? "default",
    agent_id: payload.agent_id ?? "openclaw_agent",
    framework: payload.framework ?? "openclaw",
    visibility: payload.visibility ?? "private",
    executive_summary: {
      ...summary,
      trust_score: trustScore,
      readiness_level: payload.readiness_level ?? summary.readiness_level ?? (trustScore >= 85 ? "ready_for_runtime" : trustScore >= 65 ? "review_recommended" : "unsafe_for_production"),
      evidence_level: payload.evidence_level ?? summary.evidence_level ?? "trace_available",
      evaluation_confidence: payload.evaluation_confidence ?? summary.evaluation_confidence,
      event_count: trace.length
    },
    primary_diagnosis: payload.primary_diagnosis ?? {
      root_cause_failure_type: "runtime_observed",
      causal_chain_explanation: "Critiqor loaded this run from a local diagnosis artifact."
    },
    cost_analysis: payload.cost_analysis ?? {},
    recommendations: payload.recommendations ?? [],
    failure_analysis: {
      failure_causes: Array.isArray(payload.failure_causes) ? payload.failure_causes : [],
      top_failure_modes: [],
      frequency_distribution: {}
    },
    evidence_panel: {
      trace,
      causal_graph: payload.causal_graph ?? { nodes: [], edges: [] },
      tool_calls: trace.filter(
        (event) => typeof event === "object" && event && event.event === "tool_call"
      ),
      tool_outputs: trace.filter(
        (event) => typeof event === "object" && event && event.event === "tool_output"
      ),
      memory_events: trace.filter(
        (event) => typeof event === "object" && event && event.event === "memory_event"
      )
    }
  };
};
function listRuns(tenantId = "default") {
  const byId = /* @__PURE__ */ new Map();
  for (const run of artifactRuns()) byId.set(getRunId(run), run);
  for (const run of durableRuns(tenantId)) byId.set(getRunId(run), run);
  for (const [runId, run] of store()) byId.set(runId, run);
  return Array.from(byId.values()).filter((run) => String(run.tenant_id ?? "default") === tenantId).sort((a, b) => String(b.run_id ?? "").localeCompare(String(a.run_id ?? "")));
}
function getRun(runId, tenantId = "default") {
  const stored = store().get(runId);
  if (stored && String(stored.tenant_id ?? "default") === tenantId) return stored;
  return listRuns(tenantId).find((run) => getRunId(run) === runId) ?? null;
}
function ingestRun(payload, tenantId = "default") {
  if (payload.tenant_id != null && String(payload.tenant_id) !== tenantId) {
    return { status: "tenant_mismatch", run_id: "", error: "tenant_mismatch" };
  }
  const verification = verifyAuthoritativeArtifact(payload, tenantId);
  if (!verification.valid) {
    return {
      status: "integrity_rejected",
      run_id: "",
      error: verification.error
    };
  }
  const view = ensureDashboardView({ ...payload, tenant_id: tenantId });
  const runId = getRunId(view);
  view.run_id = runId;
  store().set(runId, view);
  persistRun(view, tenantId);
  return { status: "accepted", run_id: runId, run: view };
}
function setVisibility(runId, visibility, tenantId = "default") {
  if (!["private", "organization", "public", "anonymous"].includes(visibility)) {
    return { status: "invalid_visibility", run_id: runId };
  }
  const run = getRun(runId, tenantId);
  if (!run) return { status: "not_found", run_id: runId };
  const next = { ...run, visibility };
  store().set(runId, next);
  persistRun(next, tenantId);
  return { status: "updated", run_id: runId, visibility };
}
function deleteRun(runId, tenantId = "default") {
  const run = getRun(runId, tenantId);
  if (!run) return { status: "not_found", run_id: runId };
  store().delete(runId);
  const destination = durableFile(tenantId, runId);
  if (existsSync(destination)) unlinkSync(destination);
  return { status: "deleted", run_id: runId };
}
function dashboardAccess() {
  try {
    const path2 = process.env.CRITIQOR_ACCESS_CONFIG || join(process.env.CRITIQOR_RUNS_DIR || "runs", ".critiqor_dashboard", "access.json");
    const parsed = JSON.parse(readFileSync(path2, "utf8"));
    const visibility = ["private", "shared", "anonymous", "public"].includes(parsed.visibility) ? parsed.visibility : "private";
    return { visibility, credential: String(parsed.credential || "") };
  } catch {
    return { visibility: "private", credential: "" };
  }
}
const loopbackHosts = /* @__PURE__ */ new Set(["127.0.0.1", "::1", "localhost"]);
const roleRank = { viewer: 1, analyst: 2, admin: 3 };
function corsHeaders(request) {
  const configuredOrigin = process.env.CRITIQOR_DASHBOARD_ORIGIN;
  const origin = request.headers.get("origin");
  const allowOrigin = configuredOrigin && origin === configuredOrigin ? configuredOrigin : loopbackHosts.has(new URL(request.url).hostname) && origin ? origin : "";
  return {
    ...allowOrigin ? { "access-control-allow-origin": allowOrigin } : {},
    "access-control-allow-methods": "GET,POST,DELETE,OPTIONS",
    "access-control-allow-headers": "authorization,content-type,x-critiqor-tenant",
    vary: "Origin"
  };
}
function authenticateApi(request, requiredRole = "viewer") {
  const url = new URL(request.url);
  const authorization = request.headers.get("authorization") ?? "";
  const suppliedToken = authorization.startsWith("Bearer ") ? authorization.slice(7) : "";
  const localOnly = loopbackHosts.has(url.hostname);
  let tenantId = request.headers.get("x-critiqor-tenant")?.trim() || "default";
  let role = "admin";
  let subject = "local-user";
  const access = dashboardAccess();
  if (access.visibility === "private" || access.visibility === "shared") {
    if (!access.credential || suppliedToken !== access.credential) {
      return {
        ok: false,
        response: Response.json(
          { error: "credential_required", visibility: access.visibility },
          { status: 401, headers: corsHeaders(request) }
        )
      };
    }
    subject = access.visibility === "private" ? "private-owner" : "invited-viewer";
  }
  if (process.env.CRITIQOR_DASHBOARD_TOKENS) {
    let tokens;
    try {
      tokens = JSON.parse(process.env.CRITIQOR_DASHBOARD_TOKENS);
    } catch {
      return {
        ok: false,
        response: Response.json({ error: "invalid_server_token_configuration" }, { status: 503 })
      };
    }
    const identity = tokens[suppliedToken];
    if (!identity) {
      return {
        ok: false,
        response: Response.json(
          { error: "unauthorized" },
          { status: 401, headers: corsHeaders(request) }
        )
      };
    }
    if (!identity.tenant_id) {
      return {
        ok: false,
        response: Response.json(
          { error: "token_tenant_binding_required" },
          { status: 503, headers: corsHeaders(request) }
        )
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
          { status: 401, headers: corsHeaders(request) }
        )
      };
    }
    subject = "legacy-service-token";
  } else if (!localOnly) {
    return {
      ok: false,
      response: Response.json(
        { error: "dashboard_api_token_required" },
        { status: 503, headers: corsHeaders(request) }
      )
    };
  }
  if (!/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(tenantId)) {
    return {
      ok: false,
      response: Response.json(
        { error: "invalid_tenant" },
        { status: 400, headers: corsHeaders(request) }
      )
    };
  }
  if (roleRank[role] < roleRank[requiredRole]) {
    return {
      ok: false,
      response: Response.json(
        { error: "forbidden" },
        { status: 403, headers: corsHeaders(request) }
      )
    };
  }
  return { ok: true, tenantId, role, subject };
}
function writeAuditEvent(event) {
  const target = process.env.CRITIQOR_AUDIT_LOG;
  if (!target) return;
  mkdirSync(path.dirname(target), { recursive: true });
  appendFileSync(
    target,
    `${JSON.stringify({ schema_version: "critiqor.audit.v1", timestamp: (/* @__PURE__ */ new Date()).toISOString(), ...event })}
`,
    { encoding: "utf8", flush: true }
  );
}
const json$2 = (request, payload, init) => Response.json(payload, {
  ...init,
  headers: {
    ...corsHeaders(request),
    ...init?.headers ?? {}
  }
});
const Route$3 = createFileRoute("/api/runs")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const identity = authenticateApi(request, "viewer");
        return identity.ok ? json$2(request, { runs: listRuns(identity.tenantId).map((run) => redactAnonymous$1(run)) }) : identity.response;
      },
      POST: async ({ request }) => {
        const identity = authenticateApi(request, "analyst");
        if (!identity.ok) return identity.response;
        const payload = await request.json().catch(() => ({}));
        const result = ingestRun(payload, identity.tenantId);
        writeAuditEvent({
          action: "run.ingest",
          tenantId: identity.tenantId,
          subject: identity.subject,
          role: identity.role,
          resource: result.run_id,
          outcome: result.status === "tenant_mismatch" ? "denied" : "allowed"
        });
        const status = result.status === "tenant_mismatch" ? 403 : result.status === "integrity_rejected" ? 422 : 200;
        return json$2(request, result, { status });
      },
      OPTIONS: async ({ request }) => json$2(request, { ok: true })
    }
  }
});
function redactAnonymous$1(run) {
  if (dashboardAccess().visibility !== "anonymous") return run;
  const copy = redactPrivatePaths$1(structuredClone(run));
  copy.agent_id = "anonymous-agent";
  copy.tenant_id = "anonymous";
  copy.visibility = "anonymous";
  const raw = copy.raw_evidence;
  if (raw) for (const key of Object.keys(raw)) raw[key] = "Hidden for anonymous access";
  return copy;
}
function redactPrivatePaths$1(value) {
  if (Array.isArray(value)) return value.map(redactPrivatePaths$1);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, redactPrivatePaths$1(item)])
    );
  }
  if (typeof value !== "string") return value;
  return value.replace(/(?:file:\/\/)?\/(?:Users|home)\/.*$/gi, "Hidden for anonymous access").replace(/(?:file:\/\/)?\/(?:private\/)?var\/folders\/.*$/gi, "Hidden for anonymous access").replace(/[A-Z]:[\\/]Users[\\/].*$/gi, "Hidden for anonymous access").replace(/\bBearer\s+[A-Za-z0-9._~+/=-]{8,}/gi, "[REDACTED]").replace(/\bsk-[A-Za-z0-9_-]{12,}\b/g, "[REDACTED]").replace(/\b(?:ghp|github_pat)_[A-Za-z0-9_]{12,}\b/g, "[REDACTED]");
}
const Route$2 = createFileRoute("/api/access")({
  server: {
    handlers: {
      GET: async () => {
        const access = dashboardAccess();
        return Response.json({
          visibility: access.visibility,
          requiresCredential: ["private", "shared"].includes(access.visibility)
        });
      },
      POST: async ({ request }) => {
        const access = dashboardAccess();
        const body = await request.json().catch(() => ({}));
        const supplied = String(body.credential || "");
        const ok = !["private", "shared"].includes(access.visibility) || !!access.credential && supplied === access.credential;
        return Response.json(
          {
            ok,
            visibility: access.visibility,
            ...ok && access.visibility === "shared" ? { inviteCode: access.credential } : {}
          },
          { status: ok ? 200 : 401 }
        );
      }
    }
  }
});
const json$1 = (request, payload, init) => Response.json(payload, {
  ...init,
  headers: {
    ...corsHeaders(request),
    ...init?.headers ?? {}
  }
});
const Route$1 = createFileRoute("/api/runs/ingest")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const identity = authenticateApi(request, "analyst");
        if (!identity.ok) return identity.response;
        const payload = await request.json().catch(() => ({}));
        const result = ingestRun(payload, identity.tenantId);
        writeAuditEvent({
          action: "run.ingest",
          tenantId: identity.tenantId,
          subject: identity.subject,
          role: identity.role,
          resource: result.run_id,
          outcome: result.status === "tenant_mismatch" ? "denied" : "allowed"
        });
        const status = result.status === "tenant_mismatch" ? 403 : result.status === "integrity_rejected" ? 422 : 200;
        return json$1(request, result, { status });
      },
      OPTIONS: async ({ request }) => json$1(request, { ok: true })
    }
  }
});
const json = (request, payload, init) => Response.json(payload, {
  ...init,
  headers: {
    ...corsHeaders(request),
    ...init?.headers ?? {}
  }
});
const Route = createFileRoute("/api/runs/$runId")({
  server: {
    handlers: {
      GET: async ({ params, request }) => {
        const identity = authenticateApi(request, "viewer");
        if (!identity.ok) return identity.response;
        const run = getRun(params.runId, identity.tenantId);
        return run ? json(request, redactAnonymous(run)) : json(request, { error: "run_not_found" }, { status: 404 });
      },
      POST: async ({ params, request }) => {
        const identity = authenticateApi(request, "admin");
        if (!identity.ok) return identity.response;
        const body = await request.json().catch(() => ({}));
        if (typeof body.visibility === "string") {
          writeAuditEvent({
            action: "run.visibility.update",
            tenantId: identity.tenantId,
            subject: identity.subject,
            role: identity.role,
            resource: params.runId,
            outcome: "allowed"
          });
          const result = setVisibility(params.runId, body.visibility, identity.tenantId);
          return json(request, result, {
            status: result.status === "invalid_visibility" ? 400 : 200
          });
        }
        return json(request, { error: "unsupported_update" }, { status: 400 });
      },
      DELETE: async ({ params, request }) => {
        const identity = authenticateApi(request, "admin");
        if (!identity.ok) return identity.response;
        const result = deleteRun(params.runId, identity.tenantId);
        writeAuditEvent({
          action: "run.delete",
          tenantId: identity.tenantId,
          subject: identity.subject,
          role: identity.role,
          resource: params.runId,
          outcome: result.status === "deleted" ? "allowed" : "denied"
        });
        return json(request, result, {
          status: result.status === "not_found" ? 404 : 200
        });
      },
      OPTIONS: async ({ request }) => json(request, { ok: true })
    }
  }
});
function redactAnonymous(run) {
  if (dashboardAccess().visibility !== "anonymous") return run;
  const copy = redactPrivatePaths(structuredClone(run));
  copy.agent_id = "anonymous-agent";
  copy.tenant_id = "anonymous";
  copy.visibility = "anonymous";
  const raw = copy.raw_evidence;
  if (raw) for (const key of Object.keys(raw)) raw[key] = "Hidden for anonymous access";
  return copy;
}
function redactPrivatePaths(value) {
  if (Array.isArray(value)) return value.map(redactPrivatePaths);
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, redactPrivatePaths(item)])
    );
  }
  return typeof value === "string" ? value.replace(/\/Users\/[^`\n]+/g, "Hidden for anonymous access") : value;
}
const SettingsRoute = Route$a.update({
  id: "/settings",
  path: "/settings",
  getParentRoute: () => Route$b
});
const RunsRoute = Route$9.update({
  id: "/runs",
  path: "/runs",
  getParentRoute: () => Route$b
});
const PlaybookRoute = Route$8.update({
  id: "/playbook",
  path: "/playbook",
  getParentRoute: () => Route$b
});
const EvidenceRoute = Route$7.update({
  id: "/evidence",
  path: "/evidence",
  getParentRoute: () => Route$b
});
const DiagnosesRoute = Route$6.update({
  id: "/diagnoses",
  path: "/diagnoses",
  getParentRoute: () => Route$b
});
const AppearanceRoute = Route$5.update({
  id: "/appearance",
  path: "/appearance",
  getParentRoute: () => Route$b
});
const IndexRoute = Route$4.update({
  id: "/",
  path: "/",
  getParentRoute: () => Route$b
});
const ApiRunsRoute = Route$3.update({
  id: "/api/runs",
  path: "/api/runs",
  getParentRoute: () => Route$b
});
const ApiAccessRoute = Route$2.update({
  id: "/api/access",
  path: "/api/access",
  getParentRoute: () => Route$b
});
const ApiRunsIngestRoute = Route$1.update({
  id: "/ingest",
  path: "/ingest",
  getParentRoute: () => ApiRunsRoute
});
const ApiRunsRunIdRoute = Route.update({
  id: "/$runId",
  path: "/$runId",
  getParentRoute: () => ApiRunsRoute
});
const ApiRunsRouteChildren = {
  ApiRunsRunIdRoute,
  ApiRunsIngestRoute
};
const ApiRunsRouteWithChildren = ApiRunsRoute._addFileChildren(ApiRunsRouteChildren);
const rootRouteChildren = {
  IndexRoute,
  AppearanceRoute,
  DiagnosesRoute,
  EvidenceRoute,
  PlaybookRoute,
  RunsRoute,
  SettingsRoute,
  ApiAccessRoute,
  ApiRunsRoute: ApiRunsRouteWithChildren
};
const routeTree = Route$b._addFileChildren(rootRouteChildren)._addFileTypes();
const getRouter = () => {
  const queryClient = new QueryClient();
  const router2 = createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    defaultPreloadStaleTime: 0
  });
  return router2;
};
const router = /* @__PURE__ */ Object.freeze(/* @__PURE__ */ Object.defineProperty({
  __proto__: null,
  getRouter
}, Symbol.toStringTag, { value: "Module" }));
export {
  Button as B,
  Input as I,
  savedTheme as a,
  buildFixPrompt as b,
  cn as c,
  applyTheme as d,
  router as r,
  severityColor as s,
  trustColor as t,
  useCritiqor as u
};
