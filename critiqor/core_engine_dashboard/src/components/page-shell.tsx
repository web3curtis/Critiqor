import type { ReactNode } from "react";
import { useCritiqor } from "@/lib/critiqor-store";
import { Badge } from "@/components/ui/badge";

export function PageShell({
  title,
  description,
  actions,
  children,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  const sync = useCritiqor((s) => s.sync);
  const label = sync.loading
    ? "Loading"
    : sync.source === "live"
      ? "Local diagnosis"
      : sync.source === "error"
        ? "Diagnosis unavailable"
        : "Waiting for data";
  const badgeClass =
    sync.source === "live"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-500"
      : sync.source === "error"
        ? "border-red-500/30 bg-red-500/10 text-red-500"
        : "border-muted-foreground/25 bg-muted/40 text-muted-foreground";

  return (
    <div className="p-6 space-y-6 max-w-[1400px] mx-auto w-full">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            <Badge variant="outline" className={badgeClass}>
              {label}
            </Badge>
          </div>
          {description && <p className="text-sm text-muted-foreground mt-1">{description}</p>}
          {sync.error && <p className="text-xs text-red-500 mt-1">{sync.error}</p>}
          {sync.source === "live" && sync.lastUpdated && (
            <p className="text-xs text-muted-foreground mt-1">
              Loaded {new Date(sync.lastUpdated).toLocaleTimeString()}
              {sync.apiBase ? ` from ${sync.apiBase}` : " from local diagnosis artifacts"}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
      {children}
    </div>
  );
}
