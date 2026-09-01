import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowDownUp, GitCompareArrows, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { PageShell } from "@/components/page-shell";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useCritiqor } from "@/lib/critiqor-store";

export const Route = createFileRoute("/runs")({
  head: () => ({ meta: [{ title: "Runs — Critiqor" }] }),
  component: RunsPage,
});

type Sort = "newest" | "oldest" | "trust-high" | "trust-low";

function RunsPage() {
  const runs = useCritiqor((state) => state.runs);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [sort, setSort] = useState<Sort>("newest");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const filtered = useMemo(
    () =>
      runs
        .filter(
          (run) =>
            `${run.id} ${run.name} ${run.model ?? ""}`
              .toLowerCase()
              .includes(query.toLowerCase()) &&
            (status === "all" || run.status === status),
        )
        .sort((a, b) =>
          sort === "newest"
            ? b.startedAt.localeCompare(a.startedAt)
            : sort === "oldest"
              ? a.startedAt.localeCompare(b.startedAt)
              : sort === "trust-high"
                ? b.trustScore - a.trustScore
                : a.trustScore - b.trustScore,
        ),
    [runs, query, status, sort],
  );
  const compared = runs.filter((run) => selected.has(run.id));
  const toggle = (id: string) =>
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  return (
    <PageShell
      title="Runs"
      description="Did my changes improve the agent? Search, sort, filter, and compare observations."
    >
      <div className="flex flex-wrap gap-2">
        <div className="relative min-w-64 flex-1">
          <Search className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search run, agent, or framework…"
            className="pl-9"
          />
        </div>
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          className="h-9 rounded-md border bg-background px-3 text-sm"
        >
          <option value="all">All statuses</option>
          <option value="passed">Passed</option>
          <option value="failed">Failed</option>
        </select>
        <label className="flex h-9 items-center gap-2 rounded-md border bg-background px-3 text-sm">
          <ArrowDownUp className="size-4" />
          <select
            value={sort}
            onChange={(event) => setSort(event.target.value as Sort)}
            className="bg-transparent outline-none"
          >
            <option value="newest">Newest first</option>
            <option value="oldest">Oldest first</option>
            <option value="trust-high">Highest trust</option>
            <option value="trust-low">Lowest trust</option>
          </select>
        </label>
      </div>
      {compared.length >= 2 && (
        <Card className="border-primary/25">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <GitCompareArrows className="size-4 text-primary" />
              Run comparison
            </CardTitle>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <div
              className="grid min-w-[640px] gap-3"
              style={{
                gridTemplateColumns: `160px repeat(${compared.length}, minmax(150px, 1fr))`,
              }}
            >
              <CompareCell label="Metric" strong />
              {compared.map((run) => (
                <CompareCell key={run.id} label={run.id} strong />
              ))}
              <CompareCell label="Trust score" />
              {compared.map((run) => (
                <CompareCell key={`${run.id}-trust`} label={`${run.trustScore}/100`} />
              ))}
              <CompareCell label="Hallucination risk" />
              {compared.map((run) => (
                <CompareCell key={`${run.id}-risk`} label={`${run.hallucinationRisk}%`} />
              ))}
              <CompareCell label="Tool reliability" />
              {compared.map((run) => (
                <CompareCell key={`${run.id}-tools`} label={`${run.toolReliability}%`} />
              ))}
              <CompareCell label="Reasoning consistency" />
              {compared.map((run) => (
                <CompareCell key={`${run.id}-reasoning`} label={`${run.reasoningConsistency}%`} />
              ))}
              <CompareCell label="WebMCP" />
              {compared.map((run) => (
                <CompareCell
                  key={`${run.id}-webmcp`}
                  label={run.webmcpComparison ?? run.webmcpStatus ?? "Not exercised"}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      <Card className="overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">Compare</TableHead>
              <TableHead>Run</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Framework</TableHead>
              <TableHead className="text-right">Trust</TableHead>
              <TableHead className="text-right">Risk</TableHead>
              <TableHead>WebMCP</TableHead>
              <TableHead>Started</TableHead>
              <TableHead className="text-right">Report</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((run) => (
              <TableRow key={run.id}>
                <TableCell>
                  <Checkbox
                    checked={selected.has(run.id)}
                    onCheckedChange={() => toggle(run.id)}
                    aria-label={`Compare ${run.id}`}
                  />
                </TableCell>
                <TableCell>
                  <div className="font-mono text-xs font-semibold">{run.id}</div>
                  <div className="text-xs text-muted-foreground">{run.name}</div>
                </TableCell>
                <TableCell>
                  <Badge variant={run.status === "passed" ? "default" : "destructive"}>
                    {run.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">{run.model ?? "—"}</TableCell>
                <TableCell className="text-right font-semibold tabular-nums">
                  {run.trustScore}
                </TableCell>
                <TableCell className="text-right tabular-nums">{run.hallucinationRisk}%</TableCell>
                <TableCell>
                  {run.webmcpStatus ? (
                    <div>
                      <div className="text-xs font-medium">
                        {run.webmcpComparison ?? run.webmcpStatus}
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        {run.webmcpFindings ?? 0} finding(s) · {run.webmcpEffects ?? 0} effect(s)
                      </div>
                    </div>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {new Date(run.startedAt).toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  <Link
                    to="/diagnoses"
                    search={{ run_id: run.id }}
                    className="font-semibold text-primary hover:underline"
                  >
                    Open
                  </Link>
                </TableCell>
              </TableRow>
            ))}
            {filtered.length === 0 && (
              <TableRow>
                <TableCell colSpan={9} className="py-10 text-center text-muted-foreground">
                  No runs match the current filters.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Card>
    </PageShell>
  );
}

function CompareCell({ label, strong }: { label: string; strong?: boolean }) {
  return (
    <div className={`rounded-md border bg-muted/15 p-2 text-sm ${strong ? "font-semibold" : ""}`}>
      {label}
    </div>
  );
}
