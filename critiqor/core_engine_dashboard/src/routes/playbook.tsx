import { createFileRoute } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { CheckCircle2, Copy, FileText, Gauge, ListChecks, Target, Wrench } from "lucide-react";
import { PageShell } from "@/components/page-shell";
import { RunSelector } from "@/components/run-selector";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCritiqor, type Diagnosis } from "@/lib/critiqor-store";
import { toast } from "sonner";

export const Route = createFileRoute("/playbook")({
  head: () => ({ meta: [{ title: "Playbook — Critiqor" }] }),
  component: PlaybookPage,
});

function PlaybookPage() {
  const { artifact, executive, webmcp, diagnoses } = useCritiqor((state) => state);
  const content = artifact.playbookContent?.trim() || "";
  const path = artifact.playbookPath || "";
  const items = diagnoses.filter((diagnosis) => diagnosis.runId === executive.runId);
  const copy = async (value: string, label: string) => {
    if (!value) {
      toast.error("Not available");
      return;
    }
    await navigator.clipboard.writeText(value);
    toast.success(label);
  };

  return (
    <PageShell
      title="Playbook"
      description={`What should I change for ${executive.runId}?`}
      actions={<RunSelector />}
    >
      <Card>
        <CardHeader className="flex-row items-start justify-between gap-3">
          <div>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="size-4 text-primary" />
              Run-specific improvement playbook
            </CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              Copied from the selected run artifact. Generic advice is not substituted.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={() => copy(path, "Playbook path copied")}>
              <Copy className="size-4" />
              Copy path
            </Button>
            <Button size="sm" variant="outline" onClick={() => copy(content, "Playbook copied")}>
              <Copy className="size-4" />
              Copy playbook
            </Button>
            <Button
              size="sm"
              onClick={() =>
                copy(
                  path
                    ? `Read the Critiqor improvement playbook at ${path} and apply only the controls supported by that run's session.json and diagnosis.json.`
                    : "",
                  "Agent instruction copied",
                )
              }
            >
              Copy agent instruction
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="rounded-lg border bg-muted/20 p-3">
            <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
              Playbook file
            </div>
            <code className="mt-1 block break-all text-sm">{path || "Not available"}</code>
          </div>
          {content ? (
            <pre className="max-h-[640px] overflow-auto whitespace-pre-wrap rounded-lg border bg-card p-4 font-mono text-sm leading-relaxed">
              {content}
            </pre>
          ) : (
            <Card className="border-dashed">
              <CardContent className="py-12 text-center">
                <CheckCircle2 className="mx-auto size-7 text-muted-foreground" />
                <h2 className="mt-3 font-semibold">Playbook not available</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  The selected run does not include improvement_playbook.md.
                </p>
              </CardContent>
            </Card>
          )}
          {webmcp.available && (
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{webmcp.displayStatus}</Badge>
              <Badge variant="secondary">{webmcp.findingCount} finding(s) in this run</Badge>
            </div>
          )}
        </CardContent>
      </Card>

      {items.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-12 text-center">
            <CheckCircle2 className="mx-auto size-7 text-emerald-500" />
            <h2 className="mt-3 font-semibold">No visual recommendation cards</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              The selected run has no diagnosis recommendations to explain visually.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {items.map((diagnosis, index) => (
            <PlaybookItem key={diagnosis.id} diagnosis={diagnosis} index={index} />
          ))}
        </div>
      )}
    </PageShell>
  );
}

function PlaybookItem({ diagnosis, index }: { diagnosis: Diagnosis; index: number }) {
  const priority =
    diagnosis.severity === "critical" || diagnosis.severity === "high"
      ? "High"
      : diagnosis.severity === "medium"
        ? "Medium"
        : diagnosis.severity === "info"
          ? "Info"
          : "Low";
  const steps = diagnosis.recommendedInvestigation.filter(Boolean);
  const verification = diagnosis.verificationSteps.filter(Boolean);
  return (
    <Card className="overflow-hidden">
      <CardHeader className="border-b bg-muted/15">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Visual card {index + 1}
            </div>
            <CardTitle className="mt-1 text-lg">
              {steps[0] || diagnosis.title || "Not captured"}
            </CardTitle>
          </div>
          <div className="flex gap-2">
            <Badge variant="outline">{priority} priority</Badge>
            {diagnosis.findingId && <Badge variant="secondary">{diagnosis.findingId}</Badge>}
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-5 p-5 lg:grid-cols-4">
        <Block icon={Target} label="Reason">
          <p>{diagnosis.rootCause || "Not captured"}</p>
        </Block>
        <Block icon={ListChecks} label="Implementation steps">
          {steps.length ? (
            <ol className="list-inside list-decimal space-y-1">
              {steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          ) : (
            <p>Not captured</p>
          )}
        </Block>
        <Block icon={Gauge} label="Expected impact">
          <p>{diagnosis.expectedImprovement || "Not captured"}</p>
        </Block>
        <Block icon={Wrench} label="Verification checklist">
          {verification.length ? (
            <ul className="space-y-1">
              {verification.map((step) => (
                <li key={step} className="flex gap-2">
                  <CheckCircle2 className="mt-0.5 size-3.5 shrink-0 text-emerald-500" />
                  {step}
                </li>
              ))}
            </ul>
          ) : (
            <p>Not captured</p>
          )}
        </Block>
      </CardContent>
    </Card>
  );
}

function Block({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof Target;
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        <Icon className="size-4 text-primary" />
        {label}
      </div>
      <div className="text-sm leading-relaxed">{children}</div>
    </div>
  );
}
