import { createFileRoute } from "@tanstack/react-router";
import { PageShell } from "@/components/page-shell";
import { RunSelector } from "@/components/run-selector";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  useCritiqor,
  severityColor,
  trustColor,
  type AgentHealth,
  type ArtifactMetadata,
  type Diagnosis,
  type DiagnosisEvidence,
  type ExecutiveSummary,
  type ScoreExplanation,
  type WebMcpAudit,
} from "@/lib/critiqor-store";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { toast } from "sonner";
import {
  ChevronDown,
  ChevronRight,
  FileSearch,
  Sparkles,
  Search,
  HeartPulse,
  FileJson,
  Clock,
  Copy,
} from "lucide-react";
import { ExportShareActions } from "@/components/export-share-actions";
import { buildFixPrompt } from "@/lib/critiqor-api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export const Route = createFileRoute("/diagnoses")({
  head: () => ({ meta: [{ title: "Diagnosis — Critiqor" }] }),
  component: DiagnosesPage,
});

const evidenceTypeColor: Record<DiagnosisEvidence["type"], string> = {
  tool_call: "border-sky-500/30 text-sky-400 bg-sky-500/10",
  tool_output: "border-emerald-500/30 text-emerald-400 bg-emerald-500/10",
  memory: "border-violet-500/30 text-violet-400 bg-violet-500/10",
  retry: "border-orange-500/30 text-orange-400 bg-orange-500/10",
  log: "border-muted-foreground/30 text-muted-foreground bg-muted/40",
  metric: "border-cyan-500/30 text-cyan-400 bg-cyan-500/10",
  judge: "border-amber-500/30 text-amber-400 bg-amber-500/10",
  context: "border-pink-500/30 text-pink-400 bg-pink-500/10",
};

function DiagnosesPage() {
  const { diagnoses, executive, scoreExplanations, agentHealth, timeline, artifact, webmcp } =
    useCritiqor((s) => s);
  const runDiagnoses = useMemo(
    () => diagnoses.filter((diagnosis) => diagnosis.runId === executive.runId),
    [diagnoses, executive.runId],
  );
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [openCard, setOpenCard] = useState<string | null>(null);
  const tc = trustColor[executive.trustLevel];
  const primary = runDiagnoses.find((item) => item.findingId) ?? runDiagnoses[0];

  useEffect(() => {
    setExpanded(new Set(primary ? [primary.id] : []));
    setOpenCard(null);
  }, [executive.runId, primary]);

  const fixPrompt = useMemo(
    () =>
      buildFixPrompt({
        runId: executive.runId,
        task: executive.task,
        summary: primary?.summary || executive.summary,
        severity: primary?.severity,
        confidence: primary?.confidence || webmcp.confidence,
        effectCount: webmcp.available ? webmcp.authoritativeEffectCount : undefined,
        duplicateCount: webmcp.available ? webmcp.duplicateEffectCount : undefined,
        sessionPath: artifact.sessionPath,
        diagnosisPath: artifact.diagnosisPath,
        playbookPath: artifact.playbookPath,
        evidence: (primary?.evidence ?? []).map((event) => {
          const payload =
            event.payload && typeof event.payload === "object"
              ? (event.payload as Record<string, unknown>)
              : {};
          return {
            sequence: payload.sequence_id,
            hash: payload.event_hash,
            message: event.message,
          };
        }),
        rootCause: primary?.rootCause,
        causalChain: primary?.causalChain,
        recommendations: primary?.recommendedInvestigation ?? [],
        strengths: webmcp.strengths.map((item) => item.title).filter(Boolean),
        verification: primary?.verificationSteps ?? [],
      }),
    [artifact, executive, primary, webmcp],
  );

  const copyFixPrompt = async () => {
    await navigator.clipboard.writeText(fixPrompt);
    toast.success("Run-specific fix prompt copied");
  };

  const toggle = (id: string) => {
    setExpanded((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
  };

  return (
    <PageShell
      title="Diagnosis"
      description={`Reliability assessment of the ${executive.agent} run — root causes, evidence, and causal analysis.`}
      actions={<RunSelector />}
    >
      <div className="flex justify-end gap-2">
        <Button size="sm" variant="outline" onClick={copyFixPrompt}>
          <Copy className="size-4" />
          Copy Fix Prompt
        </Button>
        <ExportShareActions defaultRunId={executive.runId} showShare={false} />
      </div>

      {/* Executive Summary */}
      <Card
        className={`diagnosis-section relative overflow-hidden border border-emerald-300 bg-emerald-50 text-black ${tc.border}`}
      >
        <div className={`absolute inset-x-0 top-0 h-px ${tc.bg}`} />
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <Sparkles className="size-4 text-primary" />
              <CardTitle className="text-base">Executive Summary</CardTitle>
            </div>
            <Badge variant="outline" className={`${tc.border} ${tc.text} ${tc.bg}`}>
              {tc.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="grid lg:grid-cols-4 gap-4">
          <SummaryStat
            label="Trust Score"
            value={`${executive.trustScore}`}
            suffix="/100"
            level={executive.trustLevel}
            selected={openCard === "exec-trust"}
            onOpen={() => setOpenCard("exec-trust")}
          />
          <SummaryStat
            label="Critiqor Confidence"
            value={`${executive.confidence}`}
            suffix="%"
            level="high"
            selected={openCard === "exec-confidence"}
            onOpen={() => setOpenCard("exec-confidence")}
          />
          <SummaryStat
            label="Verdict"
            value={executive.verdict}
            level={executive.trustLevel}
            text
            selected={openCard === "exec-verdict"}
            onOpen={() => setOpenCard("exec-verdict")}
          />
          <SummaryStat
            label="Run"
            value={executive.runId}
            sub={executive.agent}
            level="high"
            text
            selected={openCard === "exec-run"}
            onOpen={() => setOpenCard("exec-run")}
          />
          <button
            type="button"
            className={`lg:col-span-4 rounded-lg border bg-white p-3 pt-2 text-left transition-colors hover:border-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
              openCard === "exec-task" ? "border-emerald-500 ring-2 ring-emerald-300" : ""
            }`}
            aria-expanded={openCard === "exec-task"}
            onClick={() => setOpenCard("exec-task")}
          >
            <div className="text-xs uppercase tracking-widest text-muted-foreground mb-1">
              Agent attempt
            </div>
            <div className="text-sm font-medium">{executive.task || "Not captured"}</div>
            <p className="text-sm text-muted-foreground mt-1">
              {executive.summary || "More evidence needed"}
            </p>
          </button>
          <div className="lg:col-span-4 grid md:grid-cols-3 gap-2 pt-2">
            {executive.evidence.map((item) => (
              <EvidenceMetric
                key={item.label}
                label={item.label}
                value={item.value}
                detail={item.detail}
                selected={openCard === `exec-metric-${item.label}`}
                onOpen={() => setOpenCard(`exec-metric-${item.label}`)}
              />
            ))}
          </div>
          <button
            type="button"
            className={`lg:col-span-4 rounded-lg border bg-white p-3 text-left transition-colors hover:border-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
              openCard === "exec-why" ? "border-emerald-500 ring-2 ring-emerald-300" : ""
            }`}
            aria-expanded={openCard === "exec-why"}
            onClick={() => setOpenCard("exec-why")}
          >
            <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">
              Why Critiqor is confident
            </div>
            <p className="text-sm text-muted-foreground">
              {executive.confidenceReasoning || "More evidence needed"}
            </p>
          </button>
        </CardContent>
      </Card>

      <PrimaryDiagnosisList runDiagnoses={runDiagnoses} expanded={expanded} toggle={toggle} />

      <section aria-labelledby="engineer-brief-title">
        <Card className="diagnosis-section border-sky-300 bg-sky-50 text-black">
          <CardHeader className="pb-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle id="engineer-brief-title" className="text-base">
                  Engineer Brief
                </CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">
                  Evidence → conclusion → action, with uncertainty kept visible. Open a card for the
                  selected run's full evidence.
                </p>
              </div>
              <Badge variant="outline" className={`${tc.border} ${tc.text} ${tc.bg}`}>
                Verdict: {executive.verdict}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            <BriefCard
              label="Primary Diagnosis"
              value={primary?.title || "Not captured"}
              selected={openCard === "primary"}
              onOpen={() => setOpenCard("primary")}
            />
            <BriefCard
              label="Root Cause"
              value={primary?.rootCause || "Not captured"}
              selected={openCard === "root"}
              onOpen={() => setOpenCard("root")}
            />
            <BriefCard
              label="Evidence"
              value={
                primary?.evidence[0]?.message ||
                (artifact.eventCount ? `${artifact.eventCount} events captured` : "Not captured")
              }
              detail={`${primary?.evidence.length ?? 0} linked events · ${artifact.evidenceStatus}`}
              selected={openCard === "evidence"}
              onOpen={() => setOpenCard("evidence")}
            />
            <BriefCard
              label="Impact"
              value={
                primary?.confirmedImpact ||
                (primary ? `${primary.severity} severity` : "Not captured")
              }
              selected={openCard === "impact"}
              onOpen={() => setOpenCard("impact")}
            />
            <BriefCard
              label="Improvement Plan"
              value={primary?.recommendedInvestigation[0] || "Not captured"}
              selected={openCard === "plan"}
              onOpen={() => setOpenCard("plan")}
            />
            <BriefCard
              label="Expected Improvement"
              value={primary?.expectedImprovement || "Not captured"}
              selected={openCard === "expected"}
              onOpen={() => setOpenCard("expected")}
            />
          </CardContent>
        </Card>
      </section>

      <Card className="diagnosis-section border-violet-300 bg-violet-50 text-black">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <HeartPulse className="size-4 text-emerald-400" />
            <CardTitle className="text-base">Agent Health</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="grid md:grid-cols-3 gap-4">
          <BriefCard
            label="Overall Health"
            value={agentHealth.status || "Not captured"}
            selected={openCard === "health-status"}
            onOpen={() => setOpenCard("health-status")}
          />
          <BriefCard
            label="Strengths"
            value={agentHealth.strengths[0] || "Not captured"}
            detail={
              agentHealth.strengths.length
                ? `${agentHealth.strengths.length} observed`
                : "Not captured"
            }
            selected={openCard === "health-strengths"}
            onOpen={() => setOpenCard("health-strengths")}
          />
          <BriefCard
            label="Recommended Monitoring"
            value={agentHealth.recommendedMonitoring[0] || "Not captured"}
            selected={openCard === "health-monitoring"}
            onOpen={() => setOpenCard("health-monitoring")}
          />
          <BriefCard
            label="Stable Behaviours"
            value={agentHealth.stableBehaviours[0] || "Not captured"}
            selected={openCard === "health-stable"}
            onOpen={() => setOpenCard("health-stable")}
          />
        </CardContent>
      </Card>
      <SectionDetailDialog
        card={openCard}
        onClose={() => setOpenCard(null)}
        primary={primary}
        artifact={artifact}
        runId={executive.runId}
        executive={executive}
        agentHealth={agentHealth}
        webmcp={webmcp}
        scoreExplanations={scoreExplanations}
      />

      <Card className="diagnosis-section border-amber-300 bg-amber-50 text-black">
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Why Each Score Received Its Value</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {scoreExplanations.map((score) => (
            <button
              key={score.score}
              type="button"
              className={`w-full space-y-3 rounded-lg border bg-white p-4 text-left transition-colors hover:border-amber-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 ${
                openCard === `score-${score.score}` ? "border-amber-500 ring-2 ring-amber-300" : ""
              }`}
              aria-expanded={openCard === `score-${score.score}`}
              onClick={() => setOpenCard(`score-${score.score}`)}
            >
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div>
                  <div className="text-sm font-semibold">{score.score}</div>
                  <p className="text-sm text-muted-foreground mt-1">{score.why}</p>
                </div>
                <div className="text-right">
                  <Badge variant="outline">{score.tier}</Badge>
                  <div className="text-lg font-semibold tabular-nums mt-1">{score.value}</div>
                </div>
              </div>
              <div className="grid md:grid-cols-3 gap-2">
                {score.evidence.map((item) => (
                  <EvidenceMetric
                    key={`${score.score}-${item.label}`}
                    label={item.label}
                    value={item.value}
                    detail={item.detail}
                  />
                ))}
              </div>
            </button>
          ))}
        </CardContent>
      </Card>

      <Card className="diagnosis-section border-cyan-300 bg-cyan-50 text-black">
        <CardHeader className="flex-row items-center justify-between gap-3">
          <div>
            <CardTitle className="text-base font-bold">Copy Fix Prompt</CardTitle>
            <p className="mt-1 text-sm text-black/75">
              Generated from the selected run's diagnosis, evidence, improvements, and verification
              steps.
            </p>
          </div>
          <Button size="sm" variant="outline" onClick={copyFixPrompt}>
            <Copy className="size-4" /> Copy
          </Button>
        </CardHeader>
        <CardContent>
          <pre className="max-h-[460px] overflow-auto whitespace-pre-wrap rounded-lg border border-slate-300 bg-white p-4 font-mono text-sm leading-relaxed text-black">
            {fixPrompt}
          </pre>
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-2 gap-4">
        <Card className="diagnosis-section border-rose-300 bg-rose-50 text-black">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <Clock className="size-4 text-sky-400" />
              <CardTitle className="text-base">Runtime Timeline</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 max-h-[420px] overflow-auto">
            {timeline.map((item) => (
              <div key={item.id} className="flex gap-3 rounded-lg border bg-white p-3">
                <div className="mt-1 size-2 rounded-full bg-primary shrink-0" />
                <div className="min-w-0">
                  <div className="text-sm font-medium">{item.label}</div>
                  <div className="text-xs text-muted-foreground font-mono">
                    {new Date(item.at).toLocaleString()} · {item.type}
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">{item.detail}</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="diagnosis-section border-indigo-300 bg-indigo-50 text-black">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <FileJson className="size-4 text-amber-400" />
              <CardTitle className="text-base">Diagnosis Artifact & Session Metadata</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <InfoBlock
              label="Diagnosis Artifact"
              body={
                <code
                  className={`text-xs break-all ${(artifact.diagnosisPath ?? "").includes("Hidden for anonymous") ? "select-none blur-sm" : ""}`}
                >
                  {artifact.diagnosisPath || "Not provided"}
                </code>
              }
            />
            <InfoBlock
              label="Session Artifact"
              body={
                <code
                  className={`text-xs break-all ${(artifact.sessionPath ?? "").includes("Hidden for anonymous") ? "select-none blur-sm" : ""}`}
                >
                  {artifact.sessionPath || "Not available"}
                </code>
              }
            />
            <InfoBlock
              label="Improvement Playbook"
              body={
                <code className="text-xs break-all">
                  {artifact.playbookPath || "Not available"}
                </code>
              }
            />
            <div className="grid grid-cols-2 gap-2">
              <EvidenceMetric
                label="Events"
                value={`${artifact.eventCount}`}
                detail="Runtime events in the selected run."
              />
              <EvidenceMetric
                label="Tools"
                value={`${artifact.toolCallCount}`}
                detail="Tool calls observed."
              />
              <EvidenceMetric
                label="Outputs"
                value={`${artifact.toolOutputCount}`}
                detail="Tool outputs observed."
              />
              <EvidenceMetric
                label="Duration"
                value={`${(artifact.durationMs / 1000).toFixed(1)}s`}
                detail="Observed runtime duration."
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}

function EvidenceMetric({
  label,
  value,
  detail,
  selected,
  onOpen,
}: {
  label: string;
  value: string;
  detail: string;
  selected?: boolean;
  onOpen?: () => void;
}) {
  const className = `rounded-lg border bg-white p-3 text-left ${
    onOpen
      ? `transition-colors hover:border-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
          selected ? "border-emerald-500 ring-2 ring-emerald-300" : ""
        }`
      : ""
  }`;
  const body = (
    <>
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className="text-lg font-semibold tabular-nums mt-1">{value}</div>
      <p className="text-xs text-muted-foreground mt-1">{detail || "Not captured"}</p>
    </>
  );
  if (!onOpen) return <div className={className}>{body}</div>;
  return (
    <button
      type="button"
      className={`w-full ${className}`}
      aria-expanded={selected}
      onClick={onOpen}
    >
      {body}
    </button>
  );
}

function BriefCard({
  label,
  value,
  detail,
  selected,
  onOpen,
}: {
  label: string;
  value: string;
  detail?: string;
  selected: boolean;
  onOpen: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onOpen}
      aria-expanded={selected}
      className={`rounded-lg border bg-white p-4 text-left transition-colors hover:border-sky-400 hover:bg-sky-50/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 ${
        selected ? "border-sky-500 ring-2 ring-sky-300" : ""
      }`}
    >
      <h3 className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground">
        {label}
      </h3>
      <p className="mt-2 text-sm font-medium leading-relaxed">{value}</p>
      {detail && <p className="mt-1 text-xs text-muted-foreground">{detail}</p>}
    </button>
  );
}

function SectionDetailDialog({
  card,
  onClose,
  primary,
  artifact,
  runId,
  executive,
  agentHealth,
  webmcp,
  scoreExplanations,
}: {
  card: string | null;
  onClose: () => void;
  primary?: Diagnosis;
  artifact: ArtifactMetadata;
  runId: string;
  executive: ExecutiveSummary;
  agentHealth: AgentHealth;
  webmcp: WebMcpAudit;
  scoreExplanations: ScoreExplanation[];
}) {
  const titles: Record<string, string> = {
    primary: "Primary Diagnosis",
    root: "Root Cause",
    evidence: "Evidence",
    impact: "Impact",
    plan: "Improvement Plan",
    expected: "Expected Improvement",
    "exec-trust": "Trust Score",
    "exec-confidence": "Critiqor Confidence",
    "exec-verdict": "Verdict",
    "exec-run": "Run",
    "exec-task": "Agent attempt",
    "exec-why": "Why Critiqor is confident",
    "health-status": "Overall Health",
    "health-strengths": "Strengths",
    "health-monitoring": "Recommended Monitoring",
    "health-stable": "Stable Behaviours",
  };
  const metric = card?.startsWith("exec-metric-")
    ? executive.evidence.find((item) => `exec-metric-${item.label}` === card)
    : undefined;
  const scoreCard = card?.startsWith("score-") ? card.slice("score-".length) : "";
  const copy = async (value: string, label: string) => {
    await navigator.clipboard.writeText(value);
    toast.success(label);
  };
  return (
    <Dialog open={Boolean(card)} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[85vh] max-w-2xl overflow-auto">
        <DialogHeader>
          <DialogTitle>
            {card
              ? (titles[card] ?? metric?.label ?? scoreCard ?? "Diagnosis detail")
              : "Diagnosis detail"}{" "}
            · {runId}
          </DialogTitle>
          <DialogDescription>
            In-depth view for the selected run. Missing fields stay unavailable.
          </DialogDescription>
        </DialogHeader>
        {card === "primary" && (
          <div className="space-y-3 text-sm">
            <p className="font-medium">{primary?.title || "Not captured"}</p>
            <p>{primary?.summary || "More evidence needed"}</p>
            <p>Severity: {primary?.severity || "Not captured"}</p>
            <p>Confidence: {primary?.confidence || "More evidence needed"}</p>
            <p>Root cause: {primary?.rootCause || "Not captured"}</p>
            <BulletList
              items={primary?.causalChain?.length ? primary.causalChain : ["Not captured"]}
            />
            <p>
              Counterevidence:{" "}
              {primary?.counterEvidence.length
                ? primary.counterEvidence.map((item) => item.message).join("; ")
                : "None supplied"}
            </p>
            <p>Alternatives: {primary?.alternativeHypotheses.join("; ") || "None evaluated"}</p>
          </div>
        )}
        {card === "root" && (
          <div className="space-y-3 text-sm">
            <p>{primary?.rootCause || "Not captured"}</p>
            <p>
              Why alternatives were rejected:{" "}
              {primary?.alternativeHypotheses.join("; ") || "Not captured"}
            </p>
            <BulletList items={primary?.causalChain ?? ["Not captured"]} />
          </div>
        )}
        {card === "evidence" && (
          <div className="space-y-3 text-sm">
            {(primary?.evidence ?? []).map((event) => {
              const payload =
                event.payload && typeof event.payload === "object"
                  ? (event.payload as Record<string, unknown>)
                  : {};
              return (
                <div key={event.id} className="rounded-md border p-3">
                  <div>{event.message}</div>
                  <div className="mt-1 font-mono text-xs text-muted-foreground">
                    sequence {String(payload.sequence_id ?? "Not captured")} · hash{" "}
                    {String(payload.event_hash ?? "Not captured")} · {event.at}
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="mt-2"
                    onClick={() =>
                      copy(
                        `sequence ${String(payload.sequence_id ?? "")} ${String(payload.event_hash ?? "")}`,
                        "Evidence reference copied",
                      )
                    }
                  >
                    Copy evidence reference
                  </Button>
                </div>
              );
            })}
            {!primary?.evidence.length && <p>Not captured</p>}
            <Button
              size="sm"
              variant="outline"
              onClick={() => copy(artifact.sessionPath || "", "Session path copied")}
            >
              Copy session path
            </Button>
          </div>
        )}
        {card === "impact" && (
          <div className="space-y-3 text-sm">
            <p>Confirmed: {primary?.confirmedImpact || "Not captured"}</p>
            <p>Potential: {primary?.potentialImpact || "Not captured"}</p>
            <p>Trust impact: {primary ? `-${primary.trustImpact}` : "Not captured"}</p>
          </div>
        )}
        {card === "plan" && (
          <div className="space-y-3 text-sm">
            <BulletList
              items={
                primary?.recommendedInvestigation.length
                  ? primary.recommendedInvestigation
                  : ["Not captured"]
              }
            />
            <p>Playbook: {artifact.playbookPath || "Not available"}</p>
            <Button
              size="sm"
              variant="outline"
              onClick={() => copy(artifact.playbookPath || "", "Playbook path copied")}
            >
              Copy playbook path
            </Button>
          </div>
        )}
        {card === "expected" && (
          <div className="space-y-3 text-sm">
            <p>{primary?.expectedImprovement || "Not captured"}</p>
            <BulletList
              items={
                primary?.verificationSteps.length ? primary.verificationSteps : ["Not captured"]
              }
            />
          </div>
        )}
        {card === "exec-trust" && (
          <div className="space-y-3 text-sm">
            <p>
              Trust score: {executive.trustScore}/100 · {executive.trustLevel || "Not captured"}
            </p>
            <p>
              This value comes from the selected run's executive summary, not a dashboard default.
            </p>
            <BulletList
              items={
                executive.evidence.length
                  ? executive.evidence.map((item) => `${item.label}: ${item.value}`)
                  : ["Not captured"]
              }
            />
          </div>
        )}
        {card === "exec-confidence" && (
          <div className="space-y-3 text-sm">
            <p>Confidence: {executive.confidence || "More evidence needed"}</p>
            <p>{executive.confidenceReasoning || "More evidence needed"}</p>
            <p>WebMCP confidence: {webmcp.confidence || "Not captured"}</p>
          </div>
        )}
        {card === "exec-verdict" && (
          <div className="space-y-3 text-sm">
            <p>Verdict: {executive.verdict || "More evidence needed"}</p>
            <p>WebMCP status: {webmcp.available ? webmcp.displayStatus : "Not exercised"}</p>
            <p>
              Findings: {webmcp.available ? webmcp.findingCount : "Not captured"} · Duplicate
              effects: {webmcp.available ? webmcp.duplicateEffectCount : "Not captured"}
            </p>
          </div>
        )}
        {card === "exec-run" && (
          <div className="space-y-3 text-sm">
            <p>Run: {executive.runId || "Not available"}</p>
            <p>Agent: {executive.agent || "Not captured"}</p>
            <p>Session: {artifact.sessionPath || "Not available"}</p>
            <p>Diagnosis: {artifact.diagnosisPath || "Not available"}</p>
            <p>Playbook: {artifact.playbookPath || "Not available"}</p>
          </div>
        )}
        {card === "exec-task" && (
          <div className="space-y-3 text-sm">
            <p className="font-medium">{executive.task || "Not captured"}</p>
            <p>{executive.summary || "More evidence needed"}</p>
          </div>
        )}
        {card === "exec-why" && (
          <div className="space-y-3 text-sm">
            <p>{executive.confidenceReasoning || "More evidence needed"}</p>
            <p>Evidence status: {artifact.evidenceStatus || "unknown"}</p>
            <p>Events in selected run: {artifact.eventCount}</p>
          </div>
        )}
        {metric && (
          <div className="space-y-3 text-sm">
            <p className="font-medium">{metric.label}</p>
            <p>{metric.value || "Not captured"}</p>
            <p>{metric.detail || "More evidence needed"}</p>
          </div>
        )}
        {card === "health-status" && (
          <div className="space-y-3 text-sm">
            <p>{agentHealth.status || "Not captured"}</p>
            <p>
              This status is derived from the selected run
              {webmcp.available ? ` and WebMCP ${webmcp.displayStatus}` : ""}.
            </p>
          </div>
        )}
        {card === "health-strengths" && (
          <BulletList
            items={agentHealth.strengths.length ? agentHealth.strengths : ["Not captured"]}
          />
        )}
        {card === "health-monitoring" && (
          <BulletList
            items={
              agentHealth.recommendedMonitoring.length
                ? agentHealth.recommendedMonitoring
                : ["Not captured"]
            }
          />
        )}
        {card === "health-stable" && (
          <BulletList
            items={
              agentHealth.stableBehaviours.length ? agentHealth.stableBehaviours : ["Not captured"]
            }
          />
        )}
        {scoreCard && (
          <div className="space-y-3 text-sm">
            {(() => {
              const score = scoreExplanations.find((item) => item.score === scoreCard);
              if (!score) return <p>Not captured</p>;
              return (
                <>
                  <p className="font-medium">
                    {score.score}: {score.value || "Not captured"}
                  </p>
                  <p>{score.tier || "Not captured"}</p>
                  <p>{score.why || "More evidence needed"}</p>
                  <BulletList
                    items={
                      score.evidence.length
                        ? score.evidence.map((item) => `${item.label}: ${item.value}`)
                        : ["Not captured"]
                    }
                  />
                </>
              );
            })()}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

function PrimaryDiagnosisList({
  runDiagnoses,
  expanded,
  toggle,
}: {
  runDiagnoses: Diagnosis[];
  expanded: Set<string>;
  toggle: (id: string) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">
          Primary Diagnosis
        </h2>
        <span className="text-xs font-semibold text-black">{runDiagnoses.length} findings</span>
      </div>
      {runDiagnoses.length === 0 && (
        <Card className="border-dashed">
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            No diagnosis was present in the selected run artifacts.
          </CardContent>
        </Card>
      )}
      {runDiagnoses.map((d) => {
        const sc = severityColor[d.severity];
        const isOpen = expanded.has(d.id);
        return (
          <Card
            key={d.id}
            className={`diagnosis-section relative overflow-hidden border-l-2 bg-orange-50 text-black ${sc.border} transition-all hover:shadow-md`}
          >
            <div className={`absolute inset-y-0 left-0 w-1 ${sc.dot}`} />
            <button
              onClick={() => toggle(d.id)}
              className="w-full text-left"
              aria-expanded={isOpen}
              aria-controls={`diagnosis-${d.id}`}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0">
                    {isOpen ? (
                      <ChevronDown className="size-4 mt-1 text-muted-foreground" />
                    ) : (
                      <ChevronRight className="size-4 mt-1 text-muted-foreground" />
                    )}
                    <div className="min-w-0">
                      <CardTitle className="text-base">{d.title}</CardTitle>
                      <p className="text-sm text-muted-foreground mt-1">{d.summary}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge
                      variant="outline"
                      className={`${sc.border} ${sc.text} ${sc.bg} capitalize`}
                    >
                      {d.severity}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
            </button>
            {isOpen && (
              <CardContent id={`diagnosis-${d.id}`} className="space-y-5 pt-0">
                <div className="grid md:grid-cols-2 gap-4">
                  <InfoBlock label="Root Cause Impact" body={d.rootCause} />
                  <InfoBlock
                    label="Recommended Investigation"
                    body={
                      d.recommendedInvestigation.length ? (
                        <ul className="space-y-1.5 text-sm">
                          {d.recommendedInvestigation.map((r, i) => (
                            <li key={i} className="flex gap-2">
                              <Search className="size-3.5 mt-0.5 text-muted-foreground shrink-0" />
                              <span>{r}</span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        "Not captured"
                      )
                    }
                  />
                  <InfoBlock
                    label="Verify the Fix"
                    body={
                      d.verificationSteps.length ? (
                        <BulletList items={d.verificationSteps} />
                      ) : (
                        "Not captured"
                      )
                    }
                  />
                </div>
                <div>
                  <SectionLabel icon={<FileSearch className="size-3.5" />}>
                    Supporting Evidence
                  </SectionLabel>
                  <div className="divide-y rounded-lg border bg-white">
                    {d.evidence.map((e) => (
                      <div key={e.id} className="flex items-start gap-3 p-3">
                        <Badge
                          variant="outline"
                          className={`${evidenceTypeColor[e.type]} font-mono text-[10px] shrink-0`}
                        >
                          {e.type}
                        </Badge>
                        <div className="min-w-0 flex-1">
                          <div className="text-sm">{e.message}</div>
                          <div className="text-xs text-muted-foreground mt-0.5 font-mono">
                            {e.at} · {d.runId}
                          </div>
                        </div>
                      </div>
                    ))}
                    {!d.evidence.length && (
                      <div className="p-3 text-sm text-muted-foreground">Not captured</div>
                    )}
                  </div>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <InfoBlock
                    label="Counterevidence"
                    body={
                      d.counterEvidence.length ? (
                        <BulletList items={d.counterEvidence.map((event) => event.message)} />
                      ) : (
                        <span className="text-muted-foreground">
                          No counterevidence was supplied.
                        </span>
                      )
                    }
                  />
                  <InfoBlock
                    label="Alternative hypotheses"
                    body={
                      d.alternativeHypotheses.length ? (
                        <BulletList items={d.alternativeHypotheses} />
                      ) : (
                        <span className="text-muted-foreground">
                          No competing hypothesis was evaluated.
                        </span>
                      )
                    }
                  />
                </div>
              </CardContent>
            )}
          </Card>
        );
      })}
    </div>
  );
}

function BulletList({ items }: { items: string[] }) {
  return (
    <ul className="space-y-1 text-sm">
      {items.map((item, i) => (
        <li key={i} className="text-muted-foreground">
          • {item}
        </li>
      ))}
    </ul>
  );
}

function InfoBlock({ label, body }: { label: string; body: ReactNode }) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-2">
        {label}
      </div>
      <div className="text-sm">{body}</div>
    </div>
  );
}

function SectionLabel({ children, icon }: { children: ReactNode; icon?: ReactNode }) {
  return (
    <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-2 flex items-center gap-1.5">
      {icon}
      {children}
    </div>
  );
}

function SummaryStat({
  label,
  value,
  suffix,
  sub,
  level,
  text,
  selected,
  onOpen,
}: {
  label: string;
  value: string;
  suffix?: string;
  sub?: string;
  level: "high" | "medium" | "low";
  text?: boolean;
  selected?: boolean;
  onOpen?: () => void;
}) {
  const tc = trustColor[level];
  const className = `rounded-lg border bg-white ${tc.border} p-3 text-left ${
    onOpen
      ? `transition-colors hover:border-emerald-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 ${
          selected ? "ring-2 ring-emerald-300" : ""
        }`
      : ""
  }`;
  const body = (
    <>
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div
        className={`mt-1 ${text ? "text-base font-semibold" : "text-2xl font-semibold tabular-nums"} ${tc.text}`}
      >
        {value || "Not captured"}
        {suffix && <span className="text-sm text-muted-foreground ml-0.5">{suffix}</span>}
      </div>
      {sub && (
        <div className="text-[11px] text-muted-foreground mt-0.5 font-mono truncate">{sub}</div>
      )}
    </>
  );
  if (!onOpen) return <div className={className}>{body}</div>;
  return (
    <button type="button" className={className} aria-expanded={selected} onClick={onOpen}>
      {body}
    </button>
  );
}
