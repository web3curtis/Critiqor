"""Hosted Agent Reliability Index platform primitives.

This module models the platform boundary above the SDK: ingestion, system of
record, analytics, leaderboard service, public API facade, and dashboard data.
It is intentionally dependency-free so it can be tested locally before being
backed by a database or web framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

from .core import (
    AgentProfile,
    CausalGraph,
    compare_runs,
    build_causal_graph,
    generate_insights,
    analyze_trends,
)


@dataclass(frozen=True)
class TenantRecord:
    """Stored tenant identity for isolated organization data."""

    tenant_id: str
    name: str
    created_at: str
    public_benchmark_enabled: bool = False
    anonymized_aggregation_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "created_at": self.created_at,
            "public_benchmark_enabled": self.public_benchmark_enabled,
            "anonymized_aggregation_enabled": self.anonymized_aggregation_enabled,
        }


@dataclass(frozen=True)
class PlatformEvent:
    """Structured event emitted by the hosted platform."""

    event_type: str
    payload: dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class BenchmarkSpec:
    """Versioned benchmark scoring specification."""

    benchmark_id: str
    category: str
    version: str
    weights: dict[str, float]

    def normalize_scores(self, scores: dict[str, Any]) -> int:
        """Normalize dimension scores against this benchmark spec."""

        total_weight = sum(self.weights.values()) or 1.0
        weighted = 0.0
        for dimension, weight in self.weights.items():
            score_key = "tool_reliability" if dimension == "tool_use" else dimension
            weighted += float(scores.get(score_key, scores.get(dimension, 0))) * weight
        return max(0, min(100, round(weighted / total_weight)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "category": self.category,
            "version": self.version,
            "weights": dict(self.weights),
        }


class EventStream:
    """Deterministic streaming abstraction for platform events."""

    def __init__(self):
        self.events: list[PlatformEvent] = []
        self._subscribers: list[Any] = []

    def subscribe(self, handler: Any) -> None:
        self._subscribers.append(handler)

    def publish(self, event_type: str, payload: dict[str, Any]) -> PlatformEvent:
        event = PlatformEvent(event_type=event_type, payload=dict(payload), timestamp=_now())
        self.events.append(event)
        for handler in self._subscribers:
            handler(event)
        return event


@dataclass(frozen=True)
class IngestionResult:
    """Response returned by the hosted ingestion boundary."""

    status: str
    run_id: str

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "run_id": self.run_id}


@dataclass(frozen=True)
class AgentRecord:
    """Stored agent identity."""

    agent_id: str
    name: str
    category: str
    created_at: str
    tenant_id: str = "default"
    public_benchmark_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "name": self.name,
            "category": self.category,
            "created_at": self.created_at,
            "public_benchmark_enabled": self.public_benchmark_enabled,
        }


@dataclass(frozen=True)
class RunRecord:
    """Immutable stored run."""

    run_id: str
    agent_id: str
    trust_score: int
    benchmark_id: str | None
    timestamp: str
    payload: dict[str, Any]
    tenant_id: str = "default"
    benchmark_version: str | None = None
    public_benchmark: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "trust_score": self.trust_score,
            "benchmark_id": self.benchmark_id,
            "benchmark_version": self.benchmark_version,
            "timestamp": self.timestamp,
            "public_benchmark": self.public_benchmark,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True)
class FailureRecord:
    """Stored failure row linked to a run."""

    run_id: str
    failure_type: str
    severity: str
    causal_graph_id: str | None
    tenant_id: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "run_id": self.run_id,
            "failure_type": self.failure_type,
            "severity": self.severity,
            "causal_graph_id": self.causal_graph_id,
        }


@dataclass(frozen=True)
class CausalGraphRecord:
    """Stored causal graph row."""

    graph_id: str
    nodes: list[str]
    edges: list[dict[str, str]]
    root_cause: str
    tenant_id: str = "default"

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "graph_id": self.graph_id,
            "nodes": list(self.nodes),
            "edges": [dict(edge) for edge in self.edges],
            "root_cause": self.root_cause,
        }


@dataclass(frozen=True)
class BenchmarkRecord:
    """Stored benchmark distribution metadata."""

    benchmark_id: str
    category: str
    distribution_stats: dict[str, Any]
    version: str = "v1.0"
    weights: dict[str, float] = field(default_factory=dict)
    public: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "category": self.category,
            "version": self.version,
            "weights": dict(self.weights),
            "public": self.public,
            "distribution_stats": dict(self.distribution_stats),
        }


@dataclass
class ReliabilityIndexStore:
    """System of record for the hosted platform.

    The store keeps in-process indexes for local use and can also append every
    mutation to JSONL for replayable history.
    """

    tenants: dict[str, TenantRecord] = field(default_factory=dict)
    agents: dict[str, AgentRecord] = field(default_factory=dict)
    runs: dict[str, RunRecord] = field(default_factory=dict)
    failures: list[FailureRecord] = field(default_factory=list)
    causal_graphs: dict[str, CausalGraphRecord] = field(default_factory=dict)
    benchmarks: dict[str, BenchmarkRecord] = field(default_factory=dict)
    event_log_path: str | None = None
    _dedupe_keys: dict[str, str] = field(default_factory=dict)

    def append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self.event_log_path:
            return
        target = Path(self.event_log_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        event = PlatformEvent(event_type=event_type, payload=payload, timestamp=_now())
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenants": [tenant.to_dict() for tenant in self.tenants.values()],
            "agents": [agent.to_dict() for agent in self.agents.values()],
            "runs": [run.to_dict() for run in self.runs.values()],
            "failures": [failure.to_dict() for failure in self.failures],
            "causal_graphs": [
                graph.to_dict() for graph in self.causal_graphs.values()
            ],
            "benchmarks": [
                benchmark.to_dict() for benchmark in self.benchmarks.values()
            ],
        }


class IngestionAPI:
    """Stripe-like ingestion boundary for SDK run payloads."""

    def __init__(self, store: ReliabilityIndexStore, event_stream: EventStream | None = None):
        self.store = store
        self.event_stream = event_stream or EventStream()

    def ingest_run(self, payload: dict[str, Any]) -> IngestionResult:
        """Validate, normalize, dedupe, and store one SDK run payload."""

        normalized = self._normalize_payload(payload)
        dedupe_key = str(normalized.get("idempotency_key", "")) or _dedupe_key(
            normalized
        )
        if dedupe_key in self.store._dedupe_keys:
            return IngestionResult(
                status="accepted",
                run_id=self.store._dedupe_keys[dedupe_key],
            )

        run_id = str(normalized.get("run_id") or f"global_run_{uuid4().hex[:12]}")
        if not run_id.startswith("global_run_"):
            run_id = f"global_{run_id}"
        tenant_id = str(normalized.get("tenant_id", "default"))
        agent_id = str(normalized["agent_id"])
        timestamp = str(normalized.get("timestamp") or _now())
        benchmark_spec = self._benchmark_spec_for(normalized)
        trust_score = self._standardize_trust_score(normalized, benchmark_spec)
        normalized["trust_score"] = trust_score
        if benchmark_spec is not None:
            normalized["benchmark_spec_version"] = benchmark_spec.version
        benchmark_id = normalized.get("benchmark_id")
        public_benchmark = bool(normalized.get("public_benchmark", False))

        if tenant_id not in self.store.tenants:
            self.store.tenants[tenant_id] = TenantRecord(
                tenant_id=tenant_id,
                name=str(normalized.get("tenant_name", tenant_id)),
                created_at=_now(),
                public_benchmark_enabled=bool(
                    normalized.get("tenant_public_benchmark_enabled", False)
                ),
                anonymized_aggregation_enabled=bool(
                    normalized.get("anonymized_aggregation", False)
                ),
            )

        agent_key = _agent_key(tenant_id, agent_id)
        if agent_key not in self.store.agents:
            self.store.agents[agent_key] = AgentRecord(
                agent_id=agent_id,
                name=str(normalized.get("agent_name", agent_id)),
                category=str(normalized.get("category", "general")),
                created_at=_now(),
                tenant_id=tenant_id,
                public_benchmark_enabled=public_benchmark,
            )

        self.store.runs[run_id] = RunRecord(
            run_id=run_id,
            agent_id=agent_id,
            trust_score=trust_score,
            benchmark_id=str(benchmark_id) if benchmark_id is not None else None,
            timestamp=timestamp,
            payload=normalized,
            tenant_id=tenant_id,
            benchmark_version=benchmark_spec.version if benchmark_spec is not None else None,
            public_benchmark=public_benchmark,
        )
        self._store_failures_and_graphs(run_id, normalized)
        self.store._dedupe_keys[dedupe_key] = run_id
        self._emit("RunIngested", {"run_id": run_id, "agent_id": agent_id, "tenant_id": tenant_id})
        self.store.append_event("RunIngested", self.store.runs[run_id].to_dict())
        return IngestionResult(status="accepted", run_id=run_id)

    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)
        agent_id = normalized.get("agent_id")
        if not agent_id:
            raise ValueError("Ingested run requires agent_id.")
        normalized.setdefault("tenant_id", "default")
        if "trust_score" not in normalized and "confidence" in normalized:
            normalized["trust_score"] = normalized["confidence"]
        normalized.setdefault("failure_causes", [])
        normalized.setdefault("trace", _trace_from_payload(normalized))
        normalized.setdefault("timestamp", _now())
        normalized.setdefault("category", normalized.get("agent_type", "general"))
        return normalized

    def _store_failures_and_graphs(self, run_id: str, payload: dict[str, Any]) -> None:
        trace = _trace_from_payload(payload)
        tenant_id = str(payload.get("tenant_id", "default"))
        for cause in payload.get("failure_causes", []):
            if not isinstance(cause, dict):
                continue
            failure_type = str(cause.get("type", "unknown"))
            graph = build_causal_graph(trace, failure_type, run_id=run_id)
            graph_id = f"graph_{uuid4().hex[:12]}"
            self.store.causal_graphs[graph_id] = _graph_record(
                graph_id, graph, cause, tenant_id
            )
            self.store.failures.append(
                FailureRecord(
                    run_id=run_id,
                    failure_type=failure_type,
                    severity=str(cause.get("severity", "medium")),
                    causal_graph_id=graph_id,
                    tenant_id=tenant_id,
                )
            )
            self._emit(
                "FailureDetected",
                {"run_id": run_id, "failure_type": failure_type, "tenant_id": tenant_id},
            )
            self._emit(
                "CausalGraphGenerated",
                {"run_id": run_id, "graph_id": graph_id, "tenant_id": tenant_id},
            )
            self.store.append_event(
                "FailureDetected", self.store.failures[-1].to_dict()
            )
            self.store.append_event(
                "CausalGraphGenerated", self.store.causal_graphs[graph_id].to_dict()
            )

    def _benchmark_spec_for(self, payload: dict[str, Any]) -> BenchmarkSpec | None:
        spec_payload = payload.get("benchmark_spec")
        if isinstance(spec_payload, BenchmarkSpec):
            return spec_payload
        if isinstance(spec_payload, dict):
            spec = BenchmarkSpec(
                benchmark_id=str(spec_payload.get("benchmark_id", payload.get("benchmark_id", "benchmark"))),
                category=str(spec_payload.get("category", payload.get("category", "general"))),
                version=str(spec_payload.get("version", "v1.0")),
                weights={
                    str(key): float(value)
                    for key, value in dict(spec_payload.get("weights", {})).items()
                },
            )
            self.store.benchmarks[spec.benchmark_id] = BenchmarkRecord(
                benchmark_id=spec.benchmark_id,
                category=spec.category,
                distribution_stats={},
                version=spec.version,
                weights=spec.weights,
                public=bool(payload.get("public_benchmark", True)),
            )
            self._emit(
                "BenchmarkComputed",
                {
                    "benchmark_id": spec.benchmark_id,
                    "version": spec.version,
                    "category": spec.category,
                },
            )
            return spec
        benchmark_id = payload.get("benchmark_id")
        if benchmark_id and str(benchmark_id) in self.store.benchmarks:
            record = self.store.benchmarks[str(benchmark_id)]
            return BenchmarkSpec(
                benchmark_id=record.benchmark_id,
                category=record.category,
                version=record.version,
                weights=record.weights,
            )
        return None

    def _standardize_trust_score(
        self, payload: dict[str, Any], benchmark_spec: BenchmarkSpec | None
    ) -> int:
        if benchmark_spec is not None and isinstance(payload.get("scores"), dict):
            return benchmark_spec.normalize_scores(dict(payload["scores"]))
        return int(payload.get("trust_score", payload.get("confidence", 0)))

    def _emit(self, event_type: str, payload: dict[str, Any]) -> None:
        self.event_stream.publish(event_type, payload)


class AnalyticsEngine:
    """Truth computation layer for global reliability intelligence."""

    def __init__(self, store: ReliabilityIndexStore):
        self.store = store

    def agent_summary(self, agent_id: str, tenant_id: str = "default") -> dict[str, Any]:
        runs = self._agent_runs(agent_id, tenant_id=tenant_id)
        if not runs:
            return {
                "tenant_id": tenant_id,
                "agent_id": agent_id,
                "agent_percentile": 0,
                "category_rank": None,
                "trend": "insufficient_data",
                "dominant_failure_mode": None,
            }

        agent_key = _agent_key(tenant_id, agent_id)
        category = self.store.agents.get(agent_key).category if agent_key in self.store.agents else "general"
        leaderboard = LeaderboardService(self.store, self).get_leaderboard(
            category, tenant_id=tenant_id
        )
        ranking = next(
            (
                entry
                for entry in leaderboard["rankings"]
                if entry["agent_id"] == agent_id
            ),
            None,
        )
        failures = self.failure_distribution(agent_id=agent_id)
        dominant_failure = failures[0]["failure_type"] if failures else None
        trend = analyze_trends([run.payload for run in runs]).trust_trend
        return {
            "tenant_id": tenant_id,
            "agent_id": agent_id,
            "agent_percentile": ranking["percentile"] if ranking else 0,
            "category_rank": ranking["rank"] if ranking else None,
            "trend": trend,
            "dominant_failure_mode": dominant_failure,
        }

    def failure_distribution(
        self,
        agent_id: str | None = None,
        tenant_id: str | None = None,
        public_only: bool = False,
    ) -> list[dict[str, Any]]:
        run_ids = {
            run.run_id
            for run in self.store.runs.values()
            if (agent_id is None or run.agent_id == agent_id)
            and (tenant_id is None or run.tenant_id == tenant_id)
            and (not public_only or run.public_benchmark)
        }
        counts: dict[str, int] = {}
        for failure in self.store.failures:
            if failure.run_id not in run_ids:
                continue
            counts[failure.failure_type] = counts.get(failure.failure_type, 0) + 1
        total = sum(counts.values()) or 1
        return [
            {
                "failure_type": failure_type,
                "count": count,
                "percentage": round((count / total) * 100),
            }
            for failure_type, count in sorted(
                counts.items(), key=lambda item: item[1], reverse=True
            )
        ]

    def global_distribution(
        self,
        category: str | None = None,
        tenant_id: str | None = None,
        public_only: bool = False,
    ) -> dict[str, Any]:
        scores = [
            run.trust_score
            for run in self.store.runs.values()
            if (tenant_id is None or run.tenant_id == tenant_id)
            and (not public_only or run.public_benchmark)
            and (
                category is None
                or self.store.agents.get(
                    _agent_key(run.tenant_id, run.agent_id),
                    AgentRecord(run.agent_id, run.agent_id, "general", "", tenant_id=run.tenant_id),
                ).category
                == category
            )
        ]
        if not scores:
            return {"count": 0, "mean_trust_score": 0, "min": 0, "max": 0}
        return {
            "count": len(scores),
            "mean_trust_score": round(sum(scores) / len(scores)),
            "min": min(scores),
            "max": max(scores),
        }

    def compare_agents(
        self, agent_a: str, agent_b: str, tenant_id: str = "default"
    ) -> dict[str, Any]:
        runs_a = self._agent_runs(agent_a, tenant_id=tenant_id)
        runs_b = self._agent_runs(agent_b, tenant_id=tenant_id)
        if not runs_a or not runs_b:
            return {"agent_a": agent_a, "agent_b": agent_b, "summary": "Missing run data."}
        return compare_runs(runs_a[-1].payload, runs_b[-1].payload).to_dict()

    def regression_detection(self, agent_id: str, tenant_id: str = "default") -> dict[str, Any]:
        runs = self._agent_runs(agent_id, tenant_id=tenant_id)
        if len(runs) < 2:
            return {"regression_detected": False, "trust_change": 0}
        change = runs[-1].trust_score - runs[-2].trust_score
        return {
            "regression_detected": change <= -5,
            "trust_change": change,
        }

    def benchmark_statistics(self, benchmark_id: str) -> dict[str, Any]:
        scores = [
            run.trust_score
            for run in self.store.runs.values()
            if run.benchmark_id == benchmark_id
        ]
        if not scores:
            return {"benchmark_id": benchmark_id, "count": 0, "mean": 0}
        return {
            "benchmark_id": benchmark_id,
            "count": len(scores),
            "mean": round(sum(scores) / len(scores)),
            "min": min(scores),
            "max": max(scores),
        }

    def _agent_runs(self, agent_id: str, tenant_id: str | None = None) -> list[RunRecord]:
        return [
            run
            for run in sorted(self.store.runs.values(), key=lambda item: item.timestamp)
            if run.agent_id == agent_id and (tenant_id is None or run.tenant_id == tenant_id)
        ]


class LeaderboardService:
    """Public global ranking layer."""

    def __init__(
        self,
        store: ReliabilityIndexStore,
        analytics: AnalyticsEngine,
        event_stream: EventStream | None = None,
    ):
        self.store = store
        self.analytics = analytics
        self.event_stream = event_stream

    def get_leaderboard(
        self,
        category: str = "general",
        tenant_id: str | None = None,
        public_only: bool = False,
        benchmark_id: str | None = None,
    ) -> dict[str, Any]:
        category_runs: dict[str, list[RunRecord]] = {}
        for run in self.store.runs.values():
            if tenant_id is not None and run.tenant_id != tenant_id:
                continue
            if public_only and not run.public_benchmark:
                continue
            if benchmark_id is not None and run.benchmark_id != benchmark_id:
                continue
            agent = self.store.agents.get(_agent_key(run.tenant_id, run.agent_id))
            if agent is None or agent.category != category:
                continue
            category_runs.setdefault(_agent_key(run.tenant_id, run.agent_id), []).append(run)

        scored = []
        for agent_key, runs in category_runs.items():
            trust_score = round(sum(run.trust_score for run in runs) / len(runs))
            scored.append((agent_key, trust_score, len(runs)))
        scored.sort(key=lambda item: item[1], reverse=True)
        scores = [score for _agent_id, score, _count in scored]

        payload = {
            "category": category,
            "updated_at": _now(),
            "rankings": [
                {
                    "rank": index + 1,
                    "tenant_id": self.store.agents[agent_key].tenant_id,
                    "agent_id": self.store.agents[agent_key].agent_id,
                    "trust_score": score,
                    "percentile": _percentile(score, scores),
                    "trend": analyze_trends([run.payload for run in category_runs[agent_key]]).trust_trend,
                    "run_count": count,
                }
                for index, (agent_key, score, count) in enumerate(scored)
            ],
        }
        if self.event_stream is not None:
            self.event_stream.publish(
                "LeaderboardUpdated",
                {
                    "category": category,
                    "tenant_id": tenant_id,
                    "public_only": public_only,
                    "benchmark_id": benchmark_id,
                    "ranking_count": len(payload["rankings"]),
                },
            )
        return payload


class PublicAPILayer:
    """API facade consumed by CI/CD, integrations, and dashboards."""

    def __init__(self, store: ReliabilityIndexStore, analytics: AnalyticsEngine):
        self.store = store
        self.analytics = analytics
        self.leaderboards = LeaderboardService(store, analytics)

    def get_agent(self, agent_id: str, tenant_id: str = "default") -> dict[str, Any]:
        agent = self.store.agents.get(_agent_key(tenant_id, agent_id))
        if agent is None:
            return {"tenant_id": tenant_id, "agent_id": agent_id, "status": "not_found"}
        payload = agent.to_dict()
        payload.update(self.analytics.agent_summary(agent_id, tenant_id=tenant_id))
        return payload

    def get_agent_trends(self, agent_id: str, tenant_id: str = "default") -> dict[str, Any]:
        runs = [run.payload for run in self.analytics._agent_runs(agent_id, tenant_id)]
        return analyze_trends(runs).to_dict()

    def get_agent_failures(self, agent_id: str, tenant_id: str = "default") -> list[dict[str, Any]]:
        return self.analytics.failure_distribution(agent_id=agent_id, tenant_id=tenant_id)

    def compare(self, agent_a: str, agent_b: str, tenant_id: str = "default") -> dict[str, Any]:
        return self.analytics.compare_agents(agent_a, agent_b, tenant_id=tenant_id)

    def get_leaderboard(
        self,
        category: str = "general",
        tenant_id: str | None = None,
        public_only: bool = False,
        benchmark_id: str | None = None,
    ) -> dict[str, Any]:
        return self.leaderboards.get_leaderboard(
            category,
            tenant_id=tenant_id,
            public_only=public_only,
            benchmark_id=benchmark_id,
        )

    def get_benchmark(self, benchmark_id: str) -> dict[str, Any]:
        benchmark = self.store.benchmarks.get(benchmark_id)
        if benchmark is None:
            return {"benchmark_id": benchmark_id, "status": "not_found"}
        payload = benchmark.to_dict()
        payload["distribution_stats"] = self.analytics.benchmark_statistics(benchmark_id)
        return payload


class DashboardDataLayer:
    """Dashboard-ready data composed only from public API outputs."""

    def __init__(self, api: PublicAPILayer):
        self.api = api

    def leaderboard_view(
        self,
        category: str = "general",
        tenant_id: str | None = None,
        public_only: bool = False,
        benchmark_id: str | None = None,
    ) -> dict[str, Any]:
        return self.api.get_leaderboard(
            category,
            tenant_id=tenant_id,
            public_only=public_only,
            benchmark_id=benchmark_id,
        )

    def agent_detail_view(self, agent_id: str, tenant_id: str = "default") -> dict[str, Any]:
        agent = self.api.get_agent(agent_id, tenant_id=tenant_id)
        return {
            "agent": agent,
            "trends": self.api.get_agent_trends(agent_id, tenant_id=tenant_id),
            "failures": self.api.get_agent_failures(agent_id, tenant_id=tenant_id),
        }

    def ecosystem_view(
        self,
        category: str | None = None,
        tenant_id: str | None = None,
        public_only: bool = False,
    ) -> dict[str, Any]:
        runs = [
            run.payload
            for run in self.api.analytics.store.runs.values()
            if (tenant_id is None or run.tenant_id == tenant_id)
            and (not public_only or run.public_benchmark)
        ]
        return {
            "distribution": self.api.analytics.global_distribution(
                category,
                tenant_id=tenant_id,
                public_only=public_only,
            ),
            "failure_distribution": self.api.analytics.failure_distribution(
                tenant_id=tenant_id,
                public_only=public_only,
            ),
            "insights": generate_insights(runs).to_dict(),
        }


class AgentReliabilityIndex:
    """Convenience composition of hosted platform services."""

    def __init__(self, event_log_path: str | None = None):
        self.store = ReliabilityIndexStore(event_log_path=event_log_path)
        self.event_stream = EventStream()
        self.ingestion = IngestionAPI(self.store, self.event_stream)
        self.analytics = AnalyticsEngine(self.store)
        self.leaderboards = LeaderboardService(self.store, self.analytics, self.event_stream)
        self.api = PublicAPILayer(self.store, self.analytics)
        self.api.leaderboards = self.leaderboards
        self.dashboard = DashboardDataLayer(self.api)

    def ingest_run(self, payload: dict[str, Any]) -> IngestionResult:
        return self.ingestion.ingest_run(payload)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dedupe_key(payload: dict[str, Any]) -> str:
    tenant_id = str(payload.get("tenant_id", "default"))
    local_run_id = payload.get("local_run_id")
    if local_run_id:
        return f"{tenant_id}|{payload.get('agent_id', '')}|local|{local_run_id}"
    return "|".join(
        [
            tenant_id,
            str(payload.get("agent_id", "")),
            str(payload.get("local_run_id", payload.get("run_id", ""))),
            str(payload.get("timestamp", "")),
            str(payload.get("trust_score", "")),
        ]
    )


def _trace_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    trace = payload.get("trace")
    if isinstance(trace, list):
        return [dict(event) for event in trace if isinstance(event, dict)]
    evidence = payload.get("evidence")
    if isinstance(evidence, dict) and isinstance(evidence.get("trace"), list):
        return [dict(event) for event in evidence["trace"] if isinstance(event, dict)]
    return []


def _agent_key(tenant_id: str, agent_id: str) -> str:
    return f"{tenant_id}:{agent_id}"


def _graph_record(
    graph_id: str,
    graph: CausalGraph,
    cause: dict[str, Any],
    tenant_id: str = "default",
) -> CausalGraphRecord:
    nodes: list[str] = []
    edges: list[dict[str, str]] = []
    for edge in graph.causal_graph:
        if edge.node not in nodes:
            nodes.append(edge.node)
        if edge.leads_to not in nodes:
            nodes.append(edge.leads_to)
        edges.append({"from": edge.node, "to": edge.leads_to})
    root_cause = ""
    if isinstance(cause.get("root_cause"), dict):
        root_cause = str(cause["root_cause"].get("description", ""))
    return CausalGraphRecord(
        graph_id=graph_id,
        nodes=nodes,
        edges=edges,
        root_cause=root_cause or str(cause.get("description", "")),
        tenant_id=tenant_id,
    )


def _percentile(score: int, scores: Sequence[int]) -> int:
    if not scores:
        return 100
    at_or_below = sum(1 for candidate in scores if candidate <= score)
    return max(0, min(100, round((at_or_below / len(scores)) * 100)))
