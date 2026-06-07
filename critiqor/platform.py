"""Hosted Agent Reliability Index platform primitives.

This module models the platform boundary above the SDK: ingestion, system of
record, analytics, leaderboard service, public API facade, and dashboard data.
It is intentionally dependency-free so it can be tested locally before being
backed by a database or web framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from statistics import pstdev
from typing import Any, ClassVar, Sequence
from uuid import uuid4

from .core import (
    AgentProfile,
    CausalGraph,
    compare_runs,
    build_causal_graph,
    generate_insights,
    analyze_trends,
)
from .openclaw import (
    OPENCLAW_EVENT_TYPES,
    OPENCLAW_FAILURE_TAXONOMY,
    build_openclaw_causal_graph,
    default_openclaw_benchmark_spec,
    diagnose_openclaw_events,
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
    sequence_id: int = 0
    schema_version: str = "v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "schema_version": self.schema_version,
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
    difficulty_factors: dict[str, float] = field(default_factory=dict)
    failure_penalties: dict[str, float] = field(default_factory=dict)

    REQUIRED_DIFFICULTY_FACTORS: ClassVar[tuple[str, ...]] = (
        "task_complexity",
        "tool_usage_requirements",
        "multi_step_reasoning",
        "retrieval_dependency",
    )

    def normalize_scores(self, scores: dict[str, Any]) -> int:
        """Normalize dimension scores against this benchmark spec."""

        total_weight = sum(self.weights.values()) or 1.0
        weighted = 0.0
        for dimension, weight in self.weights.items():
            score_key = "tool_reliability" if dimension == "tool_use" else dimension
            weighted += float(scores.get(score_key, scores.get(dimension, 0))) * weight
        return max(0, min(100, round(weighted / total_weight)))

    def difficulty_score(self) -> int:
        """Return a deterministic comparability score for this benchmark."""

        if not self.difficulty_factors:
            return 85
        values = [
            max(0.0, min(100.0, float(self.difficulty_factors.get(factor, 0))))
            for factor in self.REQUIRED_DIFFICULTY_FACTORS
        ]
        return max(0, min(100, round(sum(values) / len(values))))

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "category": self.category,
            "version": self.version,
            "weights": dict(self.weights),
            "difficulty_factors": dict(self.difficulty_factors),
            "failure_penalties": dict(self.failure_penalties),
        }


class EventStream:
    """Deterministic streaming abstraction for platform events."""

    def __init__(self):
        self.events: list[PlatformEvent] = []
        self._subscribers: list[Any] = []
        self._sequence_id = 0

    def subscribe(self, handler: Any) -> None:
        self._subscribers.append(handler)

    def publish(self, event_type: str, payload: dict[str, Any]) -> PlatformEvent:
        self._sequence_id += 1
        event = PlatformEvent(
            event_type=event_type,
            payload=dict(payload),
            timestamp=_now(),
            sequence_id=self._sequence_id,
        )
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
    visibility: str = "private"
    run_hash: str | None = None

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
            "visibility": self.visibility,
            "run_hash": self.run_hash,
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
    difficulty_factors: dict[str, float] = field(default_factory=dict)
    failure_penalties: dict[str, float] = field(default_factory=dict)
    public: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "category": self.category,
            "version": self.version,
            "weights": dict(self.weights),
            "difficulty_factors": dict(self.difficulty_factors),
            "failure_penalties": dict(self.failure_penalties),
            "public": self.public,
            "distribution_stats": dict(self.distribution_stats),
        }


@dataclass(frozen=True)
class LeaderboardScoreBreakdown:
    """Weighted leaderboard components for one agent."""

    reliability: int
    evaluation_confidence: int
    benchmark_normalization: int
    consistency: int
    failure_rate: int
    trend_score: int
    leaderboard_score: int

    def to_dict(self) -> dict[str, int]:
        return {
            "reliability": self.reliability,
            "evaluation_confidence": self.evaluation_confidence,
            "benchmark_normalization": self.benchmark_normalization,
            "consistency": self.consistency,
            "failure_rate": self.failure_rate,
            "trend_score": self.trend_score,
            "leaderboard_score": self.leaderboard_score,
        }


@dataclass(frozen=True)
class ValidationReport:
    """Schema validation result for one ingestion payload."""

    valid: bool
    errors: list[str]
    run_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "run_hash": self.run_hash,
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
    _event_sequence: int = 0

    def append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self.event_log_path:
            return
        target = Path(self.event_log_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._event_sequence += 1
        event = PlatformEvent(
            event_type=event_type,
            payload=payload,
            timestamp=_now(),
            sequence_id=self._event_sequence,
        )
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")

    def replay_event_log(self, path: str | None = None) -> None:
        """Replay an append-only event log into this store."""

        source = Path(path or self.event_log_path or "")
        if not source.exists():
            raise FileNotFoundError(str(source))
        events = []
        with source.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = json.loads(line)
                events.append(event)
        events.sort(key=lambda event: (int(event.get("sequence_id", 0)), event.get("timestamp", "")))
        for event in events:
            self._apply_replayed_event(event)
            self._event_sequence = max(self._event_sequence, int(event.get("sequence_id", 0)))

    def _apply_replayed_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        if event_type == "RunIngested" and isinstance(payload, dict):
            run = RunRecord(
                tenant_id=str(payload.get("tenant_id", "default")),
                run_id=str(payload["run_id"]),
                agent_id=str(payload["agent_id"]),
                trust_score=int(payload.get("trust_score", 0)),
                benchmark_id=payload.get("benchmark_id"),
                benchmark_version=payload.get("benchmark_version"),
                timestamp=str(payload.get("timestamp", _now())),
                public_benchmark=bool(payload.get("public_benchmark", False)),
                visibility=str(payload.get("visibility", "private")),
                run_hash=payload.get("run_hash"),
                payload=dict(payload.get("payload", {})),
            )
            self.runs[run.run_id] = run
            agent_key = _agent_key(run.tenant_id, run.agent_id)
            run_payload = run.payload
            self.tenants.setdefault(
                run.tenant_id,
                TenantRecord(run.tenant_id, run.tenant_id, run.timestamp),
            )
            self.agents.setdefault(
                agent_key,
                AgentRecord(
                    agent_id=run.agent_id,
                    name=str(run_payload.get("agent_name", run.agent_id)),
                    category=str(run_payload.get("category", "general")),
                    created_at=run.timestamp,
                    tenant_id=run.tenant_id,
                    public_benchmark_enabled=run.public_benchmark,
                ),
            )
            if run.run_hash:
                self._dedupe_keys[run.run_hash] = run.run_id
        elif event_type == "FailureDetected" and isinstance(payload, dict):
            self.failures.append(
                FailureRecord(
                    tenant_id=str(payload.get("tenant_id", "default")),
                    run_id=str(payload.get("run_id", "")),
                    failure_type=str(payload.get("failure_type", "unknown")),
                    severity=str(payload.get("severity", "medium")),
                    causal_graph_id=payload.get("causal_graph_id"),
                )
            )
        elif event_type == "CausalGraphGenerated" and isinstance(payload, dict) and "graph_id" in payload:
            self.causal_graphs[str(payload["graph_id"])] = CausalGraphRecord(
                tenant_id=str(payload.get("tenant_id", "default")),
                graph_id=str(payload["graph_id"]),
                nodes=list(payload.get("nodes", [])),
                edges=[dict(edge) for edge in payload.get("edges", [])],
                root_cause=str(payload.get("root_cause", "")),
            )

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
        report = self.validate_run(normalized)
        if not report.valid:
            raise ValueError("Invalid run payload: " + "; ".join(report.errors))
        run_hash = str(report.run_hash)
        dedupe_key = str(normalized.get("idempotency_key", "")) or run_hash
        if dedupe_key in self.store._dedupe_keys:
            return IngestionResult(
                status="duplicate",
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
        normalized["run_hash"] = run_hash
        if benchmark_spec is not None:
            normalized["benchmark_spec_version"] = benchmark_spec.version
        benchmark_id = normalized.get("benchmark_id")
        visibility = str(normalized.get("visibility", "private"))
        public_benchmark = visibility == "public" or bool(normalized.get("public_benchmark", False))
        anonymous_benchmark = visibility in {"anonymous", "public_benchmark_opt_in"} or bool(normalized.get("anonymous_benchmark", False))

        if tenant_id not in self.store.tenants:
            self.store.tenants[tenant_id] = TenantRecord(
                tenant_id=tenant_id,
                name=str(normalized.get("tenant_name", tenant_id)),
                created_at=_now(),
                public_benchmark_enabled=bool(
                    normalized.get("tenant_public_benchmark_enabled", False)
                ),
                anonymized_aggregation_enabled=bool(
                    normalized.get("anonymized_aggregation", False) or anonymous_benchmark
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
            visibility=visibility,
            run_hash=run_hash,
        )
        self._store_failures_and_graphs(run_id, normalized)
        self.store._dedupe_keys[dedupe_key] = run_id
        self.store._dedupe_keys[run_hash] = run_id
        self._emit("RunIngested", {"run_id": run_id, "agent_id": agent_id, "tenant_id": tenant_id})
        self.store.append_event("RunIngested", self.store.runs[run_id].to_dict())
        return IngestionResult(status="accepted", run_id=run_id)

    def validate_run(self, payload: dict[str, Any]) -> ValidationReport:
        """Validate hosted ingestion schema and return a stable run hash."""

        errors: list[str] = []
        if not payload.get("agent_id"):
            errors.append("agent_id is required")
        if not payload.get("benchmark_id"):
            errors.append("benchmark_id is required")
        elif (
            payload.get("benchmark_id") not in self.store.benchmarks
            and not isinstance(payload.get("benchmark_spec"), (dict, BenchmarkSpec))
        ):
            errors.append("benchmark_spec is required for unknown benchmark_id")
        if not isinstance(payload.get("scores", {}), dict):
            errors.append("scores must be an object")
        if not isinstance(payload.get("failure_causes", []), list):
            errors.append("failure_causes must be a list")
        visibility = payload.get("visibility", "private")
        if visibility not in {"private", "public", "shared", "anonymous", "public_benchmark_opt_in"}:
            errors.append("visibility must be private, public, shared, anonymous, or public_benchmark_opt_in")
        if _is_openclaw_payload(payload) and not _trace_from_payload(payload):
            errors.append("OpenClaw ingestion requires runtime trace evidence")
        trust_score = payload.get("trust_score", payload.get("confidence", 0))
        try:
            score = int(trust_score)
            if score < 0 or score > 100:
                errors.append("trust_score must be between 0 and 100")
        except (TypeError, ValueError):
            if "scores" not in payload:
                errors.append("trust_score must be numeric when scores are unavailable")
        return ValidationReport(
            valid=not errors,
            errors=errors,
            run_hash=_run_hash(payload) if not errors else None,
        )

    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)
        agent_id = normalized.get("agent_id")
        normalized.setdefault("tenant_id", "default")
        if "trust_score" not in normalized and "confidence" in normalized:
            normalized["trust_score"] = normalized["confidence"]
        normalized.setdefault("failure_causes", [])
        normalized.setdefault("trace", _trace_from_payload(normalized))
        normalized.setdefault("timestamp", _now())
        normalized.setdefault("category", normalized.get("agent_type", "general"))
        normalized.setdefault("visibility", "public" if normalized.get("public_benchmark") else "private")
        if _is_openclaw_payload(normalized):
            normalized = _normalize_openclaw_payload(normalized)
        return normalized

    def _store_failures_and_graphs(self, run_id: str, payload: dict[str, Any]) -> None:
        trace = _trace_from_payload(payload)
        tenant_id = str(payload.get("tenant_id", "default"))
        for cause in payload.get("failure_causes", []):
            if not isinstance(cause, dict):
                continue
            failure_type = str(cause.get("type", "unknown"))
            graph_id = f"graph_{uuid4().hex[:12]}"
            if _is_openclaw_payload(payload) and isinstance(payload.get("causal_graph"), dict):
                self.store.causal_graphs[graph_id] = _openclaw_graph_record(
                    graph_id, dict(payload["causal_graph"]), cause, tenant_id
                )
            else:
                graph = build_causal_graph(trace, failure_type, run_id=run_id)
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
            failure_payload = {
                "run_id": run_id,
                "failure_type": failure_type,
                "severity": str(cause.get("severity", "medium")),
                "causal_graph_id": graph_id,
                "tenant_id": tenant_id,
            }
            self._emit(
                "FailureDetected",
                failure_payload,
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
                difficulty_factors={
                    str(key): float(value)
                    for key, value in dict(spec_payload.get("difficulty_factors", {})).items()
                },
                failure_penalties={
                    str(key): float(value)
                    for key, value in dict(spec_payload.get("failure_penalties", {})).items()
                },
            )
            self.store.benchmarks[spec.benchmark_id] = BenchmarkRecord(
                benchmark_id=spec.benchmark_id,
                category=spec.category,
                distribution_stats={},
                version=spec.version,
                weights=spec.weights,
                difficulty_factors=spec.difficulty_factors,
                failure_penalties=spec.failure_penalties,
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
                difficulty_factors=record.difficulty_factors,
                failure_penalties=record.failure_penalties,
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
            return {"benchmark_id": benchmark_id, "count": 0, "mean": 0, "drift_detected": False}
        first_half = scores[: max(1, len(scores) // 2)]
        second_half = scores[max(1, len(scores) // 2):] or first_half
        drift = round((sum(second_half) / len(second_half)) - (sum(first_half) / len(first_half)))
        return {
            "benchmark_id": benchmark_id,
            "count": len(scores),
            "mean": round(sum(scores) / len(scores)),
            "min": min(scores),
            "max": max(scores),
            "drift_detected": abs(drift) >= 5,
            "drift": drift,
        }

    def score_agent_for_leaderboard(self, runs: Sequence[RunRecord]) -> LeaderboardScoreBreakdown:
        """Compute the final deterministic leaderboard formula."""

        if not runs:
            return LeaderboardScoreBreakdown(0, 0, 0, 0, 0, 0, 0)
        reliability = round(sum(run.trust_score for run in runs) / len(runs))
        evaluation_confidence = round(
            sum(_evaluation_confidence(run.payload) for run in runs) / len(runs)
        )
        benchmark_normalization = round(
            sum(_benchmark_normalization_score(run, self.store) for run in runs) / len(runs)
        )
        trust_scores = [run.trust_score for run in runs]
        consistency = max(0, min(100, round(100 - (pstdev(trust_scores) * 2))))
        failure_rate = _inverted_failure_rate(runs, self.store.failures)
        trend_score = _trend_score(trust_scores)
        leaderboard_score = round(
            (0.40 * reliability)
            + (0.15 * evaluation_confidence)
            + (0.15 * benchmark_normalization)
            + (0.10 * consistency)
            + (0.10 * failure_rate)
            + (0.10 * trend_score)
        )
        return LeaderboardScoreBreakdown(
            reliability=reliability,
            evaluation_confidence=evaluation_confidence,
            benchmark_normalization=benchmark_normalization,
            consistency=consistency,
            failure_rate=failure_rate,
            trend_score=trend_score,
            leaderboard_score=leaderboard_score,
        )

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
            breakdown = self.analytics.score_agent_for_leaderboard(runs)
            latest_timestamp = max(run.timestamp for run in runs)
            scored.append((agent_key, breakdown, len(runs), latest_timestamp))
        scored.sort(key=lambda item: item[0])
        scored.sort(key=lambda item: item[3], reverse=True)
        scored.sort(key=lambda item: item[1].failure_rate, reverse=True)
        scored.sort(key=lambda item: item[1].trend_score, reverse=True)
        scored.sort(key=lambda item: item[1].evaluation_confidence, reverse=True)
        scored.sort(key=lambda item: item[1].reliability, reverse=True)
        scored.sort(key=lambda item: item[1].leaderboard_score, reverse=True)
        scores = [breakdown.leaderboard_score for _agent_id, breakdown, _count, _ts in scored]

        payload = {
            "category": category,
            "updated_at": _now(),
            "rankings": [
                self._leaderboard_entry(
                    index + 1,
                    agent_key,
                    breakdown,
                    category_runs[agent_key],
                    scores,
                    count,
                )
                for index, (agent_key, breakdown, count, _timestamp) in enumerate(scored)
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

    def _leaderboard_entry(
        self,
        rank: int,
        agent_key: str,
        breakdown: LeaderboardScoreBreakdown,
        runs: Sequence[RunRecord],
        scores: Sequence[int],
        count: int,
    ) -> dict[str, Any]:
        agent = self.store.agents[agent_key]
        return {
            "rank": rank,
            "tenant_id": agent.tenant_id,
            "agent_id": agent.agent_id,
            "leaderboard_score": breakdown.leaderboard_score,
            "trust_score": breakdown.reliability,
            "percentile": _percentile(breakdown.leaderboard_score, scores),
            "trend": analyze_trends([run.payload for run in runs]).trust_trend,
            "run_count": count,
            "score_breakdown": breakdown.to_dict(),
            "evidence": _leaderboard_evidence_summary(runs, self.store),
            "reasoning": _leaderboard_reasoning(breakdown, runs, self.store),
            "impact": _leaderboard_impact(breakdown, runs, self.store),
            "recommendation": _leaderboard_recommendation(breakdown, runs, self.store),
        }


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

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = self.store.runs.get(run_id)
        if run is None:
            return {"run_id": run_id, "status": "not_found"}
        return _run_diagnostic_view(run, self.store)

    def set_run_visibility(self, run_id: str, visibility: str) -> dict[str, Any]:
        if visibility not in {"private", "public", "anonymous", "shared", "public_benchmark_opt_in"}:
            raise ValueError("visibility must be private, public, shared, anonymous, or public_benchmark_opt_in")
        run = self.store.runs.get(run_id)
        if run is None:
            return {"run_id": run_id, "status": "not_found"}
        public_benchmark = visibility == "public"
        payload = dict(run.payload)
        payload["visibility"] = visibility
        payload["public_benchmark"] = public_benchmark
        payload["anonymous_benchmark"] = visibility in {"anonymous", "public_benchmark_opt_in"}
        self.store.runs[run_id] = replace(run, visibility=visibility, public_benchmark=public_benchmark, payload=payload)
        self.store.append_event("VisibilityUpdated", {"run_id": run_id, "tenant_id": run.tenant_id, "agent_id": run.agent_id, "visibility": visibility})
        return {"run_id": run_id, "visibility": visibility, "status": "updated"}


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

    def run_diagnosis_view(self, run_id: str) -> dict[str, Any]:
        return self.api.get_run(run_id)

    def set_run_visibility(self, run_id: str, visibility: str) -> dict[str, Any]:
        return self.api.set_run_visibility(run_id, visibility)

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

    @classmethod
    def from_event_log(cls, event_log_path: str) -> "AgentReliabilityIndex":
        index = cls(event_log_path=event_log_path)
        index.store.replay_event_log(event_log_path)
        return index




def _run_diagnostic_view(run: RunRecord, store: ReliabilityIndexStore) -> dict[str, Any]:
    payload = run.payload
    failure_records = [failure for failure in store.failures if failure.run_id == run.run_id]
    graph_records = [
        store.causal_graphs[failure.causal_graph_id].to_dict()
        for failure in failure_records
        if failure.causal_graph_id and failure.causal_graph_id in store.causal_graphs
    ]
    primary = payload.get("primary_diagnosis") if isinstance(payload.get("primary_diagnosis"), dict) else {}
    cost = payload.get("cost_analysis") if isinstance(payload.get("cost_analysis"), dict) else {}
    evidence = payload.get("evidence_summary") if isinstance(payload.get("evidence_summary"), dict) else {}
    trace = _trace_from_payload(payload)
    failures = [cause for cause in payload.get("failure_causes", []) if isinstance(cause, dict)]
    failure_counts: dict[str, int] = {}
    for failure in failures:
        failure_type = str(failure.get("type", "unknown"))
        failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
    return {
        "run_id": run.run_id,
        "tenant_id": run.tenant_id,
        "agent_id": run.agent_id,
        "framework": payload.get("framework", "generic"),
        "visibility": run.visibility,
        "executive_summary": {
            "trust_score": run.trust_score,
            "readiness_level": payload.get("readiness_level", _readiness_from_score(run.trust_score)),
            "evidence_level": payload.get("evidence_level", "response_only"),
            "event_count": evidence.get("event_count", len(trace)),
        },
        "primary_diagnosis": primary or {
            "root_cause_failure_type": failure_records[0].failure_type if failure_records else None,
            "causal_chain_explanation": "No runtime failure cause was detected.",
        },
        "cost_analysis": cost or {
            "total_tokens": 0,
            "token_waste": 0,
            "duplicate_calls": 0,
            "redundancy_score": 0,
        },
        "failure_analysis": {
            "top_failure_modes": sorted(failure_counts, key=failure_counts.get, reverse=True),
            "frequency_distribution": failure_counts,
            "failure_causes": failures,
        },
        "evidence_panel": {
            "trace": trace,
            "tool_calls": [event for event in trace if event.get("event") == "tool_call"],
            "tool_outputs": [event for event in trace if event.get("event") == "tool_output"],
            "memory_events": [event for event in trace if event.get("event") == "memory_event"],
            "causal_graph": payload.get("causal_graph") or (graph_records[0] if graph_records else {"nodes": [], "edges": []}),
            "stored_causal_graphs": graph_records,
        },
    }


def _readiness_from_score(score: int) -> str:
    if score >= 85:
        return "ready_for_runtime"
    if score >= 65:
        return "review_recommended"
    return "unsafe_for_production"

def _is_openclaw_payload(payload: dict[str, Any]) -> bool:
    return str(payload.get("framework", "")).lower() == "openclaw" or str(payload.get("category", "")).lower() == "openclaw_agents"


def _normalize_openclaw_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    events = _trace_from_payload(normalized)
    normalized["framework"] = "openclaw"
    normalized["category"] = "openclaw_agents"
    normalized.setdefault("benchmark_id", "openclaw_runtime_v1")
    normalized.setdefault(
        "benchmark_spec",
        default_openclaw_benchmark_spec(
            str(normalized.get("benchmark_id", "openclaw_runtime_v1")),
            str(normalized.get("difficulty_tier", "standard")),
        ),
    )
    if events:
        diagnosis = diagnose_openclaw_events(events).to_dict()
        normalized.setdefault("openclaw_diagnosis", diagnosis)
        normalized.setdefault("scores", diagnosis["scores"])
        normalized.setdefault("trust_score", diagnosis["trust_score"])
        normalized.setdefault("readiness_level", diagnosis["readiness_level"])
        normalized.setdefault("failure_causes", diagnosis["failure_causes"])
        normalized.setdefault("causal_graph", diagnosis["causal_graph"])
        normalized.setdefault("cost_analysis", diagnosis["cost_analysis"])
        normalized.setdefault("primary_diagnosis", diagnosis["primary_diagnosis"])
        normalized.setdefault("evidence_summary", diagnosis["evidence_summary"])
        normalized.setdefault("evidence_level", "fully_instrumented")
        normalized.setdefault("evaluation_confidence", 95)
    return normalized


def _openclaw_graph_record(
    graph_id: str,
    graph: dict[str, Any],
    cause: dict[str, Any],
    tenant_id: str,
) -> CausalGraphRecord:
    nodes = []
    seen = set()
    for node in graph.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id", node.get("label", "node")))
        if node_id not in seen:
            nodes.append(node_id)
            seen.add(node_id)
    edges = []
    for edge in graph.get("edges", []):
        if not isinstance(edge, dict):
            continue
        edges.append({
            "from": str(edge.get("from", "")),
            "to": str(edge.get("to", "")),
            "relation": str(edge.get("relation", "causes")),
        })
    return CausalGraphRecord(
        graph_id=graph_id,
        nodes=nodes,
        edges=edges,
        root_cause=str(cause.get("description", cause.get("type", ""))),
        tenant_id=tenant_id,
    )

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


def _run_hash(payload: dict[str, Any]) -> str:
    stable_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"run_id", "timestamp", "idempotency_key"}
    }
    encoded = json.dumps(stable_payload, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


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


def _evaluation_confidence(payload: dict[str, Any]) -> int:
    if "evaluation_confidence" in payload:
        return max(0, min(100, int(payload["evaluation_confidence"])))
    level = str(payload.get("evidence_level", payload.get("evidence", {}).get("evidence_level", "response_only")))
    return {
        "response_only": 45,
        "trace_available": 75,
        "fully_instrumented": 95,
    }.get(level, 50)


def _benchmark_normalization_score(run: RunRecord, store: ReliabilityIndexStore) -> int:
    if not run.benchmark_id or not run.benchmark_version:
        return 35
    benchmark = store.benchmarks.get(run.benchmark_id)
    if benchmark is None:
        return 70
    spec = BenchmarkSpec(
        benchmark_id=benchmark.benchmark_id,
        category=benchmark.category,
        version=benchmark.version,
        weights=benchmark.weights,
        difficulty_factors=benchmark.difficulty_factors,
        failure_penalties=benchmark.failure_penalties,
    )
    return max(0, min(100, round(70 + (spec.difficulty_score() * 0.30))))


def _inverted_failure_rate(runs: Sequence[RunRecord], failures: Sequence[FailureRecord]) -> int:
    run_ids = {run.run_id for run in runs}
    severity_weights = {"critical": 35, "high": 25, "medium": 12, "low": 5}
    penalty = 0
    for failure in failures:
        if failure.run_id in run_ids:
            penalty += severity_weights.get(failure.severity, 12)
    penalty_per_run = penalty / max(1, len(runs))
    return max(0, min(100, round(100 - penalty_per_run)))


def _trend_score(scores: Sequence[int]) -> int:
    if len(scores) < 2:
        return 50
    change = scores[-1] - scores[0]
    return max(0, min(100, round(50 + change)))


def _leaderboard_evidence_summary(
    runs: Sequence[RunRecord],
    store: ReliabilityIndexStore,
) -> dict[str, Any]:
    traces = [_trace_from_payload(run.payload) for run in runs]
    flat_trace = [event for trace in traces for event in trace]
    failure_types = [
        failure.failure_type
        for failure in store.failures
        if failure.run_id in {run.run_id for run in runs}
    ]
    return {
        "run_count": len(runs),
        "tool_calls_observed": sum(
            1 for event in flat_trace if str(event.get("event", "")).startswith("tool_") or "tool" in event
        ),
        "tool_outputs_observed": sum(
            1 for event in flat_trace if "output" in event or str(event.get("event", "")) == "tool_end"
        ),
        "ignored_tool_outputs": failure_types.count("ignored_tool_output"),
        "redundant_tool_calls": failure_types.count("redundant_tool_calls"),
        "runtime_failures": failure_types.count("runtime_failures"),
        "benchmark_metadata": sorted(
            {
                f"{run.benchmark_id}@{run.benchmark_version or 'unknown'}"
                for run in runs
                if run.benchmark_id
            }
        ),
        "evidence_levels": sorted(
            {
                str(run.payload.get("evidence_level", "response_only"))
                for run in runs
            }
        ),
    }


def _leaderboard_reasoning(
    breakdown: LeaderboardScoreBreakdown,
    runs: Sequence[RunRecord],
    store: ReliabilityIndexStore,
) -> str:
    evidence = _leaderboard_evidence_summary(runs, store)
    parts = []
    if breakdown.reliability >= 85:
        parts.append("High reliability is the primary reason this agent ranks well.")
    elif breakdown.reliability < 70:
        parts.append("Lower reliability limits this agent's ranking.")
    if breakdown.evaluation_confidence < 70:
        parts.append("Limited evidence confidence reduces trust in the score.")
    if evidence["ignored_tool_outputs"]:
        parts.append("Ignored tool outputs indicate retrieved evidence may not be consistently incorporated.")
    if evidence["redundant_tool_calls"]:
        parts.append("Repeated tool calls suggest inefficient or uncertain planning.")
    if breakdown.consistency < 75:
        parts.append("Score volatility over time lowers the consistency component.")
    if breakdown.trend_score > 60:
        parts.append("Recent runs show improvement, which lifts the trend component.")
    elif breakdown.trend_score < 40:
        parts.append("Recent regression lowers the trend component.")
    return " ".join(parts) or "The ranking reflects stable benchmarked performance with no dominant failure signal."


def _leaderboard_impact(
    breakdown: LeaderboardScoreBreakdown,
    runs: Sequence[RunRecord],
    store: ReliabilityIndexStore,
) -> list[str]:
    evidence = _leaderboard_evidence_summary(runs, store)
    impact = []
    if breakdown.evaluation_confidence < 70:
        impact.append("Lower evidence coverage makes the reliability estimate less defensible.")
    if evidence["ignored_tool_outputs"]:
        impact.append("Ignored evidence increases hallucination and factual accuracy risk.")
    if evidence["redundant_tool_calls"]:
        impact.append("Redundant execution increases cost and latency.")
    if breakdown.consistency < 75:
        impact.append("Volatile performance makes production behavior harder to predict.")
    if not impact:
        impact.append("Strong evidence and stable scores improve deployment confidence.")
    return impact


def _leaderboard_recommendation(
    breakdown: LeaderboardScoreBreakdown,
    runs: Sequence[RunRecord],
    store: ReliabilityIndexStore,
) -> str:
    evidence = _leaderboard_evidence_summary(runs, store)
    if evidence["ignored_tool_outputs"]:
        return "Improve utilization of tool outputs before generating final responses."
    if evidence["redundant_tool_calls"]:
        return "Reduce repeated tool calls with better planning and stopping criteria."
    if breakdown.evaluation_confidence < 70:
        return "Enable trace capture or full instrumentation to raise evaluation confidence."
    if breakdown.consistency < 75:
        return "Investigate regressions and stabilize prompt, model, or tool behavior across runs."
    return "Maintain benchmark coverage and continue monitoring for regressions."
