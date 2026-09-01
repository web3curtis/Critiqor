import { createFileRoute } from "@tanstack/react-router";
import { Clock, Database, FileJson, TerminalSquare } from "lucide-react";
import { PageShell } from "@/components/page-shell";
import { RunSelector } from "@/components/run-selector";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCritiqor } from "@/lib/critiqor-store";

export const Route = createFileRoute("/evidence")({
  head: () => ({ meta: [{ title: "Evidence Explorer — Critiqor" }] }),
  component: EvidencePage,
});

function EvidencePage() {
  const { timeline, evidence, artifact, executive, memoryAnalysis, webmcp } = useCritiqor(
    (state) => state,
  );
  const runEvidence = evidence.filter((event) => event.runId === executive.runId);
  return (
    <PageShell
      title="Evidence Explorer"
      description={`Show me the original evidence for ${executive.runId}.`}
      actions={<RunSelector />}
    >
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat icon={Clock} label="Timeline events" value={timeline.length} />
        <Stat icon={TerminalSquare} label="Tool calls" value={artifact.toolCallCount} />
        <Stat icon={Database} label="Memory events" value={artifact.memoryEventCount} />
        <Stat icon={FileJson} label="Evidence status" value={artifact.evidenceStatus} />
      </div>
      {webmcp.available && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">WebMCP runtime evidence</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Audit status</div>
              <div className="mt-1 font-semibold">{webmcp.displayStatus}</div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Consequential findings</div>
              <div className="mt-1 font-semibold">{webmcp.findingCount}</div>
            </div>
            <div className="rounded-lg border p-3">
              <div className="text-xs text-muted-foreground">Authoritative effects</div>
              <div className="mt-1 font-semibold">{webmcp.authoritativeEffectCount}</div>
            </div>
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Runtime timeline</CardTitle>
        </CardHeader>
        <CardContent className="divide-y rounded-lg border p-0">
          {timeline.map((event) => (
            <div key={event.id} className="grid gap-2 p-3 text-sm md:grid-cols-[160px_180px_1fr]">
              <time className="font-mono text-xs text-muted-foreground">
                {new Date(event.at).toLocaleString()}
              </time>
              <Badge variant="outline" className="w-fit font-mono text-[10px]">
                {event.type}
              </Badge>
              <div>
                <div className="font-medium">{event.label}</div>
                <div className="mt-0.5 text-muted-foreground">{event.detail}</div>
              </div>
            </div>
          ))}
          {timeline.length === 0 && (
            <div className="p-8 text-center text-sm text-muted-foreground">
              No timeline events were included in this run.
            </div>
          )}
        </CardContent>
      </Card>
      {memoryAnalysis?.eventCount ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Memory decisions</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {memoryAnalysis.evidence.map((item, index) => (
              <div key={`${item.eventType}-${index}`} className="rounded-lg border bg-muted/10 p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="secondary" className="font-mono text-[10px]">
                    {item.action}
                  </Badge>
                  <Badge variant="outline" className="font-mono text-[10px]">
                    {item.architectureStage}
                  </Badge>
                  {item.memoryId && (
                    <span className="font-mono text-[10px] text-muted-foreground">
                      {item.memoryId}
                    </span>
                  )}
                </div>
                <p className="mt-2 text-sm font-medium">{item.message}</p>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{item.reason}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Event snapshots</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          {runEvidence.length === 0 && (
            <div className="rounded-lg border p-8 text-center text-sm text-muted-foreground">
              No event snapshots were included for this run.
            </div>
          )}
          {runEvidence.slice(0, 40).map((event) => (
            <div key={event.id} className="rounded-lg border bg-muted/10 p-3">
              <div className="flex items-center justify-between gap-2">
                <Badge variant="secondary" className="font-mono text-[10px]">
                  {event.type}
                </Badge>
                <time className="text-[10px] text-muted-foreground">
                  {new Date(event.at).toLocaleTimeString()}
                </time>
              </div>
              <p className="mt-2 text-sm">{event.message}</p>
              {event.payload != null && (
                <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap rounded bg-background p-2 text-[10px] text-muted-foreground">
                  {JSON.stringify(event.payload, null, 2)}
                </pre>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Complete runtime log</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="max-h-[540px] overflow-auto whitespace-pre-wrap rounded-lg border bg-background p-4 text-xs leading-relaxed">
            {timeline
              .map((event) => `${event.at} [${event.type}] ${event.label}: ${event.detail}`)
              .join("\n") || "No complete runtime log is available for this run."}
          </pre>
        </CardContent>
      </Card>
    </PageShell>
  );
}

function Stat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Clock;
  label: string;
  value: string | number;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <Icon className="size-4 text-primary" />
        <div className="mt-3 text-xs text-muted-foreground">{label}</div>
        <div className="mt-1 text-xl font-semibold capitalize">{value}</div>
      </CardContent>
    </Card>
  );
}
