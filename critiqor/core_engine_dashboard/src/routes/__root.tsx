import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { Toaster } from "@/components/ui/sonner";
import { CritiqorDataSync } from "@/components/critiqor-data-sync";
import { ThemeManager } from "@/components/theme-manager";
import { UpdateNotice } from "@/components/update-notice";
import { AccessGate } from "@/components/access-gate";

function NotFoundComponent() {
  // Per product spec: no 404 dead ends. Send users to the dashboard.
  if (typeof window !== "undefined") window.location.replace("/");
  return null;
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold text-foreground">Something went wrong</h1>
        <p className="mt-2 text-sm text-muted-foreground">{error.message}</p>
        <div className="mt-6 flex justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Try again
          </button>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Critiqor" },
      { name: "description", content: "Critiqor — agent evaluation, diagnoses, and trust." },
    ],
    links: [{ rel: "stylesheet", href: appCss }],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeManager />
      <AccessGate>
        <CritiqorDataSync />
        <SidebarProvider>
          <a
            href="#main-content"
            className="fixed left-3 top-3 z-50 -translate-y-20 rounded-md bg-background px-3 py-2 text-sm font-medium shadow focus:translate-y-0"
          >
            Skip to diagnosis content
          </a>
          <div className="min-h-screen flex w-full bg-background">
            <AppSidebar />
            <div className="flex-1 flex flex-col min-w-0">
              <UpdateNotice />
              <header className="h-13 flex items-center gap-3 border-b px-4 sticky top-0 bg-background/85 backdrop-blur-xl z-10">
                <SidebarTrigger />
                <div className="text-xs text-muted-foreground">
                  Critiqor <span className="mx-1 opacity-50">/</span> Runtime evaluation
                </div>
              </header>
              <main id="main-content" tabIndex={-1} className="flex-1 min-w-0">
                <Outlet />
              </main>
            </div>
          </div>
          <Toaster />
        </SidebarProvider>
      </AccessGate>
    </QueryClientProvider>
  );
}
