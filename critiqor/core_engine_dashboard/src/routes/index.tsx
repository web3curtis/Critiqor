import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ClipboardCheck,
  ExternalLink,
  FileSearch,
  Gauge,
  Globe2,
  Stethoscope,
  TrendingDown,
  TrendingUp,
  Wrench,
} from "lucide-react";
import { PageShell } from "@/components/page-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCritiqor, type Run } from "@/lib/critiqor-store";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [{ title: "Overview — Critiqor" }] }),
  component: Overview,
});

const verdicts = {
  high: {
    title: "Production Ready",
    detail: "Suitable for production deployment.",
    icon: CheckCircle2,
    style: "border-emerald-500/35 bg-emerald-500/[0.07]",
    text: "text-emerald-600 dark:text-emerald-400",
  },
  medium: {
    title: "Needs Improvement Before Production",
    detail: "Deploy only after addressing the identified issues.",
    icon: AlertTriangle,
    style: "border-amber-500/35 bg-amber-500/[0.07]",
    text: "text-amber-700 dark:text-amber-400",
  },
  low: {
    title: "Not Ready For Production",
    detail: "Major runtime issues detected. Deployment is not recommended.",
    icon: AlertTriangle,
    style: "border-red-500/35 bg-red-500/[0.07]",
    text: "text-red-700 dark:text-red-400",
  },
} as const;

function Overview() {
  const { executive, diagnoses, runs, webmcp } = useCritiqor((state) => state);
  const [dashboardUrl, setDashboardUrl] = useState("");
  useEffect(() => setDashboardUrl(window.location.href), []);
  const primary = diagnoses.find((diagnosis) => diagnosis.runId === executive.runId);
  const current = runs.find((run) => run.id === executive.runId);
  const previous = current?.webmcpComparison
    ? runs.find((run) => run.id !== current.id && run.webmcpStatus)
    : current
      ? runs
          .filter((run) => Date.parse(run.startedAt) < Date.parse(current.startedAt))
          .sort((a, b) => b.startedAt.localeCompare(a.startedAt))[0]
      : undefined;
  const verdict = verdicts[executive.trustLevel];
  const VerdictIcon = verdict.icon;

  return (
    <PageShell title="Overview" description="Can I trust my agent in production?">
      <Card className={`overflow-hidden ${verdict.style}`}>
        <CardContent className="grid gap-6 p-6 xl:grid-cols-[1fr_auto] xl:items-center">
          <div>
            <div className={`mb-3 flex items-center gap-2 text-sm font-semibold ${verdict.text}`}>
              <VerdictIcon className="size-5" /> Agent status
            </div>
            <h2 className={`text-3xl font-bold tracking-tight ${verdict.text}`}>{verdict.title}</h2>
            <p className="mt-2 text-sm font-medium">{verdict.detail}</p>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
              {executive.summary}
            </p>
            <Link
              to="/diagnoses"
              search={{ run_id: executive.runId }}
              className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline"
            >
              Open Primary Diagnosis <ArrowRight className="size-4" />
            </Link>
          </div>
          <div className="grid grid-cols-3 gap-5 border-t pt-5 xl:border-l xl:border-t-0 xl:pl-6 xl:pt-0">
            <Metric label="Trust" value={`${executive.trustScore}/100`} />
            <Metric label="Confidence" value={`${executive.confidence}%`} />
            <Metric label="Run" value={executive.runId} mono />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-card/70">
        <CardContent className="flex flex-wrap items-center gap-3 px-4 py-3">
          <div className="rounded-md bg-primary/10 p-2 text-primary">
            <ExternalLink className="size-4" />
          </div>
          <div className="min-w-0">
            <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Dashboard URL
            </div>
            <code className="block truncate text-sm">{dashboardUrl || "Loading current URL…"}</code>
          </div>
        </CardContent>
      </Card>

      {webmcp.available && (
        <Card
          className={
            webmcp.status === "FINDING"
              ? "border-red-500/35"
              : webmcp.status === "PASSED"
                ? "border-emerald-500/35"
                : webmcp.status === "INCONCLUSIVE"
                  ? "border-amber-500/35"
                  : "border-muted"
          }
        >
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Globe2 className="size-4 text-primary" />
                WebMCP
              </CardTitle>
              <Badge variant={webmcp.status === "FINDING" ? "destructive" : "outline"}>
                {webmcp.displayStatus}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed text-muted-foreground">{webmcp.summary}</p>
            <div className="mt-4 grid gap-3 sm:grid-cols-5">
              <Metric label="Scenarios" value={String(webmcp.scenariosExercised)} />
              <Metric label="Findings" value={String(webmcp.findingCount)} />
              <Metric
                label="Authoritative effects"
                value={String(webmcp.authoritativeEffectCount)}
              />
              <Metric label="Duplicate effects" value={String(webmcp.duplicateEffectCount)} />
              <Metric label="Strengths" value={String(webmcp.strengths.length)} />
            </div>
            {webmcp.strengths.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {webmcp.strengths.map((strength) => (
                  <Badge key={strength.id} variant="secondary" title={strength.detail}>
                    {strength.title}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-[1.2fr_.8fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Stethoscope className="size-4 text-primary" />
              Biggest runtime issue
            </CardTitle>
          </CardHeader>
          <CardContent>
            <h3 className="font-semibold">
              {primary?.title ?? "No dominant runtime issue detected"}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {primary?.summary ??
                "Continue monitoring representative production scenarios to increase confidence."}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge variant="outline">
                {primary ? `${primary.severity} severity` : "No finding"}
              </Badge>
              <Badge variant="outline">
                {primary ? `${primary.evidence.length} linked events` : "Evidence monitored"}
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Wrench className="size-4 text-primary" />
              Next action
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-relaxed">
              {primary?.recommendedInvestigation[0] || "Not captured"}
            </p>
            <Link
              to="/playbook"
              search={{ run_id: executive.runId }}
              className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-primary hover:underline"
            >
              Open run-specific Playbook <ArrowRight className="size-4" />
            </Link>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Gauge className="size-4 text-primary" />
            Did the change work?
          </CardTitle>
        </CardHeader>
        <CardContent>
          <RunComparison current={current} previous={previous} />
        </CardContent>
      </Card>

      <div className="grid gap-3 md:grid-cols-4">
        <GoalLink
          to="/diagnoses"
          runId={executive.runId}
          icon={Stethoscope}
          title="Why?"
          detail="Review the diagnosis"
        />
        <GoalLink
          to="/evidence"
          runId={executive.runId}
          icon={FileSearch}
          title="Show me the evidence"
          detail="Inspect raw runtime events"
        />
        <GoalLink
          to="/playbook"
          runId={executive.runId}
          icon={Wrench}
          title="What should I change?"
          detail="Follow the implementation plan"
        />
        <GoalLink
          to="/runs"
          runId={executive.runId}
          icon={TrendingUp}
          title="Did it improve?"
          detail="Compare completed runs"
        />
      </div>
    </PageShell>
  );
}

function Metric({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        {label}
      </div>
      <div
        className={`mt-1 max-w-32 truncate text-base font-semibold ${mono ? "font-mono text-xs" : ""}`}
        title={value}
      >
        {value}
      </div>
    </div>
  );
}

function GoalLink({
  to,
  runId,
  icon: Icon,
  title,
  detail,
}: {
  to: "/runs" | "/diagnoses" | "/playbook" | "/evidence";
  runId?: string;
  icon: typeof Gauge;
  title: string;
  detail: string;
}) {
  return (
    <Link
      to={to}
      search={runId ? { run_id: runId } : undefined}
      className="group rounded-xl border bg-card p-4 transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
    >
      <Icon className="size-5 text-primary" />
      <div className="mt-3 font-semibold">{title}</div>
      <div className="mt-1 text-xs text-muted-foreground">{detail}</div>
      <ArrowRight className="mt-3 size-4 text-muted-foreground transition-transform group-hover:translate-x-1" />
    </Link>
  );
}

function RunComparison({ current, previous }: { current?: Run; previous?: Run }) {
  if (!current)
    return (
      <p className="text-sm text-muted-foreground">
        Finalize a run to begin measuring improvement.
      </p>
    );
  if (!previous)
    return (
      <div className="rounded-lg border border-dashed p-6 text-center">
        <ClipboardCheck className="mx-auto size-5 text-muted-foreground" />
        <p className="mt-2 font-medium">This is the first recorded observation session.</p>
      </div>
    );
  if (current.webmcpComparison)
    return (
      <div className="flex flex-wrap items-center gap-4">
        <div>
          <div className="text-xs text-muted-foreground">WebMCP matched rerun</div>
          <div className="mt-1 text-2xl font-semibold">{current.webmcpComparison}</div>
          <div className="mt-1 text-sm text-muted-foreground">
            {previous.webmcpFindings ?? 0} finding(s) before · {current.webmcpFindings ?? 0} after
          </div>
        </div>
        <Badge variant="outline" className="text-emerald-600 dark:text-emerald-400">
          Same task and response-loss adversity
        </Badge>
        <Link to="/runs" className="ml-auto text-sm font-semibold text-primary hover:underline">
          Compare runs
        </Link>
      </div>
    );
  const delta = current.trustScore - previous.trustScore;
  const Icon = delta >= 0 ? TrendingUp : TrendingDown;
  return (
    <div className="flex flex-wrap items-center gap-4">
      <div>
        <div className="text-xs text-muted-foreground">Trust score</div>
        <div className="mt-1 text-2xl font-semibold tabular-nums">
          {previous.trustScore} <ArrowRight className="mx-2 inline size-4" /> {current.trustScore}
        </div>
      </div>
      <Badge
        variant="outline"
        className={
          delta >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"
        }
      >
        <Icon className="mr-1 size-3" />
        {delta >= 0 ? "+" : ""}
        {delta} points
      </Badge>
      <Link to="/runs" className="ml-auto text-sm font-semibold text-primary hover:underline">
        Compare runs
      </Link>
    </div>
  );
}
