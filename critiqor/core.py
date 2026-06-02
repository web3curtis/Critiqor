"""Core Critiqor reliability wrapper implementation."""

from __future__ import annotations

from contextlib import AbstractContextManager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from typing import Any, Callable, Literal, Protocol, Sequence, runtime_checkable
from uuid import uuid4


TrustLevel = Literal["High", "Moderate", "Low"]
EvidenceLevel = Literal["response_only", "trace_available", "fully_instrumented"]
FailureSeverity = Literal["low", "medium", "high"]
DeploymentRecommendation = Literal[
    "safe_to_deploy", "review_recommended", "unsafe_for_production"
]
TrendDirection = Literal["improving", "stable", "declining", "insufficient_data"]
AgentType = Literal["coding", "research", "customer_support", "general"]
CertificationLevel = Literal["none", "bronze", "silver", "gold", "platinum"]


_CURRENT_RECORDER: ContextVar["EvidenceRecorder | None"] = ContextVar(
    "critiqor_current_recorder", default=None
)
_AGENT_REGISTRY: dict[str, "AgentProfile"] = {}
_AGENT_RUNS: dict[str, list[Any]] = {}
_CAUSAL_GRAPHS: dict[str, "CausalGraph"] = {}


@runtime_checkable
class RunnableAgent(Protocol):
    """Protocol for agents that expose a run method."""

    def run(self, prompt: str, *args: Any, **kwargs: Any) -> Any:
        """Run the agent for a prompt."""


@dataclass(frozen=True)
class ToolCall:
    """Observed tool call supplied by a trace or instrumentation adapter."""

    tool: str
    args: dict[str, Any] = field(default_factory=dict)
    id: str | None = None
    timestamp: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        payload: dict[str, Any] = {"tool": self.tool, "args": dict(self.args)}
        if self.id is not None:
            payload["id"] = self.id
        if self.timestamp is not None:
            payload["timestamp"] = self.timestamp
        return payload


@dataclass(frozen=True)
class ToolOutput:
    """Observed tool output supplied by a trace or instrumentation adapter."""

    tool: str
    output: Any
    call_id: str | None = None
    error: str | None = None
    timestamp: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        payload: dict[str, Any] = {"tool": self.tool, "output": self.output}
        if self.call_id is not None:
            payload["call_id"] = self.call_id
        if self.error is not None:
            payload["error"] = self.error
        if self.timestamp is not None:
            payload["timestamp"] = self.timestamp
        return payload


@dataclass(frozen=True)
class RuntimeMetrics:
    """Runtime metrics captured from an observed agent execution."""

    latency: float | None = None
    token_usage: dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "latency": self.latency,
            "token_usage": dict(self.token_usage),
            "retries": self.retries,
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class EvaluationEvidence:
    """Evidence used by Critiqor to evaluate observable agent behavior."""

    prompt: str
    response: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_outputs: list[ToolOutput] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    metrics: RuntimeMetrics = field(default_factory=RuntimeMetrics)
    evidence_level: EvidenceLevel = "response_only"

    @classmethod
    def from_payload(
        cls,
        prompt: str,
        response: str,
        tool_calls: list[Any] | None = None,
        tool_outputs: list[Any] | None = None,
        trace: list[dict[str, Any]] | None = None,
        metrics: dict[str, Any] | RuntimeMetrics | None = None,
        evidence_level: EvidenceLevel | None = None,
    ) -> "EvaluationEvidence":
        """Build evidence from the three supported acquisition modes."""

        normalized_calls = [_coerce_tool_call(call) for call in tool_calls or []]
        normalized_outputs = [
            _coerce_tool_output(output) for output in tool_outputs or []
        ]
        normalized_trace = [dict(event) for event in trace or []]
        normalized_metrics = _coerce_metrics(metrics)

        if evidence_level is None:
            if normalized_trace or normalized_metrics.latency is not None:
                evidence_level = "fully_instrumented"
            elif normalized_calls or normalized_outputs:
                evidence_level = "trace_available"
            else:
                evidence_level = "response_only"

        return cls(
            prompt=prompt,
            response=response,
            tool_calls=normalized_calls,
            tool_outputs=normalized_outputs,
            trace=normalized_trace,
            metrics=normalized_metrics,
            evidence_level=evidence_level,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "prompt": self.prompt,
            "response": self.response,
            "tool_calls": [call.to_dict() for call in self.tool_calls],
            "tool_outputs": [output.to_dict() for output in self.tool_outputs],
            "trace": [dict(event) for event in self.trace],
            "metrics": self.metrics.to_dict(),
            "evidence_level": self.evidence_level,
        }


@dataclass(frozen=True)
class ReliabilityCritique:
    """Structured reliability critique returned by Critiqor.

    Attributes:
        hallucination: Reliability score for unsupported or fabricated claims.
        reasoning: Reliability score for coherent task reasoning.
        tool_reliability: Reliability score for observed tool behavior.
        consistency: Reliability score for internal consistency.
        task_completion: Reliability score for satisfying the user's request.
        confidence_calibration: Score for confidence supported by evidence.
        execution_efficiency: Score for redundant or wasteful execution.
        evidence_level: Quality level of evidence used for the evaluation.
        summary: Short agent-reliability critique.
        findings: Brief reliability findings.
    """

    hallucination: int
    reasoning: int
    tool_reliability: int
    consistency: int
    task_completion: int
    confidence_calibration: int
    execution_efficiency: int
    evidence_level: EvidenceLevel
    summary: str
    findings: list[str] = field(default_factory=list)

    @property
    def tool_use(self) -> int:
        """Backward-compatible alias for the renamed tool reliability score."""

        return self.tool_reliability

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation for logging or automation."""

        return {
            "hallucination": self.hallucination,
            "reasoning": self.reasoning,
            "tool_reliability": self.tool_reliability,
            "tool_use": self.tool_reliability,
            "consistency": self.consistency,
            "task_completion": self.task_completion,
            "confidence_calibration": self.confidence_calibration,
            "execution_efficiency": self.execution_efficiency,
            "evidence_level": self.evidence_level,
            "summary": self.summary,
            "findings": list(self.findings),
        }


@dataclass(frozen=True)
class RootCause:
    """Detailed explanation for why a failure cause occurred."""

    description: str
    impact: str
    trust_penalty: int
    recommended_fix: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "description": self.description,
            "impact": self.impact,
            "trust_penalty": self.trust_penalty,
            "recommended_fix": self.recommended_fix,
        }


@dataclass(frozen=True)
class FailureCause:
    """Structured explanation for a trust-score penalty."""

    type: str
    severity: FailureSeverity
    impact: int
    description: str
    root_cause: RootCause | None = None
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        payload: dict[str, Any] = {
            "type": self.type,
            "severity": self.severity,
            "impact": self.impact,
            "description": self.description,
        }
        if self.root_cause is not None:
            payload["root_cause"] = self.root_cause.to_dict()
        if self.recommendation:
            payload["recommendation"] = self.recommendation
        return payload


@dataclass(frozen=True)
class RunComparison:
    """Comparison between two Critiqor evaluations."""

    trust_change: int
    changes: dict[str, int]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "trust_change": self.trust_change,
            "changes": dict(self.changes),
            "summary": self.summary,
        }


@dataclass(frozen=True)
class TrendAnalysis:
    """Historical reliability trend summary."""

    trust_trend: TrendDirection
    trust_change: int
    hallucination_change: int
    tool_reliability_change: int
    reasoning_change: int
    summary: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "trust_trend": self.trust_trend,
            "trust_change": self.trust_change,
            "hallucination_change": self.hallucination_change,
            "tool_reliability_change": self.tool_reliability_change,
            "reasoning_change": self.reasoning_change,
            "summary": self.summary,
        }


@dataclass(frozen=True)
class EvaluationRecord:
    """Persisted representation of one Critiqor evaluation."""

    run_id: str
    agent_id: str
    timestamp: str
    scores: dict[str, int]
    failure_causes: list[FailureCause]
    trust_score: int
    evidence_level: EvidenceLevel
    evaluation_confidence: int
    deployment_recommendation: DeploymentRecommendation

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "scores": dict(self.scores),
            "failure_causes": [cause.to_dict() for cause in self.failure_causes],
            "trust_score": self.trust_score,
            "evidence_level": self.evidence_level,
            "evaluation_confidence": self.evaluation_confidence,
            "deployment_recommendation": self.deployment_recommendation,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvaluationRecord":
        """Build a record from persisted JSON data."""

        return cls(
            run_id=str(payload.get("run_id", "")),
            agent_id=str(payload.get("agent_id", "")),
            timestamp=str(payload.get("timestamp", "")),
            scores={
                key: int(value)
                for key, value in dict(payload.get("scores", {})).items()
                if isinstance(value, (int, float))
            },
            failure_causes=[
                FailureCause(
                    type=str(cause.get("type", "unknown")),
                    severity=_coerce_severity(cause.get("severity")),
                    impact=int(cause.get("impact", 0) or 0),
                    description=str(cause.get("description", "")),
                    root_cause=_coerce_root_cause(cause.get("root_cause")),
                    recommendation=str(cause.get("recommendation", "")),
                )
                for cause in payload.get("failure_causes", [])
                if isinstance(cause, dict)
            ],
            trust_score=int(payload.get("trust_score", 0) or 0),
            evidence_level=_coerce_evidence_level(payload.get("evidence_level")),
            evaluation_confidence=int(payload.get("evaluation_confidence", 0) or 0),
            deployment_recommendation=_coerce_deployment_recommendation(
                payload.get("deployment_recommendation")
            ),
        )


@dataclass(frozen=True)
class AgentProfile:
    """Registered agent identity for cross-agent ranking."""

    agent_id: str
    name: str
    category: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "category": self.category,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AgentProfile":
        """Build an agent profile from a dictionary."""

        return cls(
            agent_id=str(payload.get("agent_id", "")),
            name=str(payload.get("name", payload.get("agent_id", ""))),
            category=str(payload.get("category", "general")),
            metadata=dict(payload.get("metadata", {}))
            if isinstance(payload.get("metadata", {}), dict)
            else {},
        )


@dataclass(frozen=True)
class LeaderboardEntry:
    """One ranked agent in a leaderboard."""

    rank: int
    agent_id: str
    trust_score: int
    percentile: int
    name: str = ""
    category: str = "general"
    run_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "rank": self.rank,
            "agent_id": self.agent_id,
            "name": self.name,
            "category": self.category,
            "trust_score": self.trust_score,
            "percentile": self.percentile,
            "run_count": self.run_count,
        }


@dataclass(frozen=True)
class Leaderboard:
    """Cross-agent ranking for one category."""

    category: str
    rankings: list[LeaderboardEntry]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "category": self.category,
            "rankings": [entry.to_dict() for entry in self.rankings],
        }


@dataclass(frozen=True)
class CausalGraphEdge:
    """Directed causal relationship between two failure nodes."""

    node: str
    leads_to: str
    evidence: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        payload = {"node": self.node, "leads_to": self.leads_to}
        if self.evidence:
            payload["evidence"] = self.evidence
        return payload


@dataclass(frozen=True)
class CausalGraph:
    """Structured causal graph for a failure event."""

    failure_event: str
    causal_graph: list[CausalGraphEdge]
    run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        payload: dict[str, Any] = {
            "failure_event": self.failure_event,
            "causal_graph": [edge.to_dict() for edge in self.causal_graph],
        }
        if self.run_id is not None:
            payload["run_id"] = self.run_id
        return payload

    def explain(self) -> str:
        """Return the causal chain as readable text."""

        if not self.causal_graph:
            return _human_dimension(self.failure_event)
        nodes = [self.causal_graph[0].node]
        nodes.extend(edge.leads_to for edge in self.causal_graph)
        return " -> ".join(_causal_node_text(node) for node in nodes)


@dataclass(frozen=True)
class BenchmarkCase:
    """One reproducible benchmark prompt."""

    prompt: str
    name: str = ""
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "name": self.name,
            "prompt": self.prompt,
            "category": self.category,
        }


@dataclass(frozen=True)
class BenchmarkResult:
    """Result returned by a Critiqor benchmark suite."""

    name: str
    agent_type: AgentType
    trust_score: int
    percentile: int
    run_count: int
    scores: dict[str, int]
    results: list["CritiqorResult"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "name": self.name,
            "agent_type": self.agent_type,
            "trust_score": self.trust_score,
            "percentile": self.percentile,
            "run_count": self.run_count,
            "scores": dict(self.scores),
            "results": [result.to_dict() for result in self.results],
        }


@dataclass(frozen=True)
class ReliabilityCertification:
    """Standardized certification output for a run or benchmark."""

    certification_level: CertificationLevel
    trust_score: int
    percentile: int
    markdown_badge: str
    criteria: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "certification_level": self.certification_level,
            "trust_score": self.trust_score,
            "percentile": self.percentile,
            "markdown_badge": self.markdown_badge,
            "criteria": dict(self.criteria),
        }


@dataclass(frozen=True)
class BenchmarkContribution:
    """Opt-in anonymized benchmark contribution without prompts or outputs."""

    scores: dict[str, int]
    failure_types: list[str]
    agent_type: AgentType
    trust_score: int
    evidence_level: EvidenceLevel
    certification_level: CertificationLevel = "none"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "scores": dict(self.scores),
            "failure_types": list(self.failure_types),
            "agent_type": self.agent_type,
            "trust_score": self.trust_score,
            "evidence_level": self.evidence_level,
            "certification_level": self.certification_level,
        }


@dataclass(frozen=True)
class ReliabilityInsight:
    """Executive summary generated from historical reliability data."""

    summary: str
    primary_drivers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "summary": self.summary,
            "primary_drivers": list(self.primary_drivers),
        }


@dataclass(frozen=True)
class PolicyCheckResult:
    """CI/CD policy gate result."""

    passed: bool
    deployment_recommendation: DeploymentRecommendation
    messages: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "passed": self.passed,
            "deployment_recommendation": self.deployment_recommendation,
            "messages": list(self.messages),
        }


@dataclass(frozen=True)
class CritiqorResult:
    """The result returned by Critiqor.

    Attributes:
        answer: The original answer from the wrapped agent.
        confidence: Overall integer reliability score from 0 to 100.
        trust_level: Trust label derived from the confidence score.
        critique: Structured reliability critique.
    """

    answer: str
    confidence: int
    trust_level: TrustLevel
    critique: ReliabilityCritique
    evidence: EvaluationEvidence
    failure_causes: list[FailureCause] = field(default_factory=list)
    evaluation_confidence: int = 0
    deployment_recommendation: DeploymentRecommendation = "review_recommended"
    benchmark_percentile: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation."""

        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "trust_score": self.confidence,
            "trust_level": self.trust_level,
            "critique": self.critique.to_dict(),
            "evidence": self.evidence.to_dict(),
            "failure_causes": [cause.to_dict() for cause in self.failure_causes],
            "evaluation_confidence": self.evaluation_confidence,
            "evidence_level": self.evidence.evidence_level,
            "deployment_recommendation": self.deployment_recommendation,
            "benchmark_percentile": self.benchmark_percentile,
        }

    def to_record(
        self, agent_id: str = "default", run_id: str | None = None
    ) -> EvaluationRecord:
        """Convert this result into a persistable evaluation record."""

        return EvaluationRecord(
            run_id=run_id or str(uuid4()),
            agent_id=agent_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            scores=_score_dict(self),
            failure_causes=list(self.failure_causes),
            trust_score=self.confidence,
            evidence_level=self.evidence.evidence_level,
            evaluation_confidence=self.evaluation_confidence,
            deployment_recommendation=self.deployment_recommendation,
        )


class Critiqor:
    """Evidence-first reliability wrapper for existing AI agents.

    Critiqor prioritizes captured traces and runtime metrics when available.
    Response-only scoring still works, but it is marked as lower-confidence
    evidence.
    """

    def __init__(self, agent: Any | None = None):
        """Create a Critiqor wrapper.

        Args:
            agent: Any object that can be called via ``run(prompt)``,
                ``invoke(prompt)``, ``generate(prompt)``, or ``agent(prompt)``.
        """

        self.agent = agent

    @staticmethod
    def auto_attach(agent: Any) -> "CritiqorTracer":
        """Automatically attach Critiqor tracing to a supported agent framework."""

        return attach_critiqor(agent)

    def run(self, prompt: str, *args: Any, **kwargs: Any) -> CritiqorResult:
        """Run the wrapped agent and return an answer with reliability scoring.

        Args:
            prompt: The user's prompt.
            *args: Extra positional arguments forwarded to the base agent for
                the answer-generation call.
            **kwargs: Extra keyword arguments forwarded to the base agent for
                the answer-generation call.

        Returns:
            CritiqorResult containing the answer, confidence, trust level, and critique.
        """

        if self.agent is None:
            raise TypeError("Critiqor.run() requires an agent.")

        raw_answer = self._call_agent(prompt, *args, **kwargs)
        answer = self._extract_text(raw_answer)

        current_recorder = _CURRENT_RECORDER.get()
        if current_recorder is not None:
            current_recorder.prompt = prompt
            current_recorder.response = answer

        return self.evaluate(prompt=prompt, response=answer)

    def evaluate(
        self,
        prompt: str,
        response: str,
        tool_calls: list[Any] | None = None,
        tool_outputs: list[Any] | None = None,
        trace: list[dict[str, Any]] | None = None,
        metrics: dict[str, Any] | RuntimeMetrics | None = None,
        evidence_level: EvidenceLevel | None = None,
    ) -> CritiqorResult:
        """Evaluate a known agent run using the best available evidence.

        This supports the three acquisition modes:

        1. ``prompt`` + ``response`` only.
        2. ``prompt`` + ``response`` + tool calls/outputs.
        3. Fully instrumented traces with runtime metrics.
        """

        evidence = EvaluationEvidence.from_payload(
            prompt=prompt,
            response=response,
            tool_calls=tool_calls,
            tool_outputs=tool_outputs,
            trace=trace,
            metrics=metrics,
            evidence_level=evidence_level,
        )

        current_recorder = _CURRENT_RECORDER.get()
        if current_recorder is not None and evidence.tool_calls == []:
            evidence = current_recorder.finish(response=response, prompt=prompt)

        critique_prompt = self._build_critique_prompt(evidence)
        raw_critique = self._call_agent(critique_prompt)
        critique_text = self._extract_text(raw_critique)

        failure_causes = detect_failure_causes(evidence)
        critique = self._parse_critique(critique_text, evidence)
        critique = self._apply_observed_adjustments(
            critique, evidence, failure_causes
        )
        confidence = self._calculate_confidence(critique, evidence)
        trust_level = self._trust_level(confidence)
        evaluation_confidence = calculate_evaluation_confidence(
            evidence, failure_causes
        )
        deployment_recommendation = recommend_deployment(
            confidence, evaluation_confidence, failure_causes
        )

        return CritiqorResult(
            answer=response,
            confidence=confidence,
            trust_level=trust_level,
            critique=critique,
            evidence=evidence,
            failure_causes=failure_causes,
            evaluation_confidence=evaluation_confidence,
            deployment_recommendation=deployment_recommendation,
        )

    def _call_agent(self, prompt: str, *args: Any, **kwargs: Any) -> Any:
        """Call a broad range of common agent interfaces."""

        if self.agent is None:
            raise TypeError("Critiqor requires an evaluator agent for this operation.")
        if hasattr(self.agent, "run"):
            return self.agent.run(prompt, *args, **kwargs)
        if hasattr(self.agent, "invoke"):
            return self.agent.invoke(prompt, *args, **kwargs)
        if hasattr(self.agent, "generate"):
            return self.agent.generate(prompt, *args, **kwargs)
        if callable(self.agent):
            return self.agent(prompt, *args, **kwargs)

        raise TypeError(
            "Critiqor requires an agent with run(), invoke(), generate(), or __call__()."
        )

    @staticmethod
    def _extract_text(value: Any) -> str:
        """Extract text from common agent response shapes."""

        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()

        for attribute in ("content", "text", "answer", "output"):
            if hasattr(value, attribute):
                return str(getattr(value, attribute)).strip()

        if isinstance(value, dict):
            for key in ("content", "text", "answer", "output", "response"):
                if key in value:
                    return str(value[key]).strip()

        return str(value).strip()

    @staticmethod
    def _build_critique_prompt(evidence: EvaluationEvidence) -> str:
        """Build the evidence-first evaluator prompt used by Critiqor."""

        return f"""You are Critiqor, a specialized reliability layer for AI agents.

Evaluate observable behavior rather than agent self-reporting. Prioritize
captured execution data whenever available:
1. Captured execution traces
2. Tool call logs
3. Tool outputs
4. Runtime metrics
5. Final response
6. Agent self-explanations

Each score must be an integer from 0 to 100:
- hallucination: higher means fewer unsupported or fabricated claims
- reasoning: higher means clearer, more coherent reasoning
- tool_reliability: higher means observed tools were selected and used well
- consistency: higher means fewer contradictions or unstable claims
- task_completion: higher means the answer satisfies the user's request
- confidence_calibration: higher means confidence is supported by evidence
- execution_efficiency: higher means fewer redundant calls, loops, and wasted steps

Return only this format:
Hallucination: <integer 0-100>
Reasoning: <integer 0-100>
Tool Reliability: <integer 0-100>
Consistency: <integer 0-100>
Task Completion: <integer 0-100>
Confidence Calibration: <integer 0-100>
Execution Efficiency: <integer 0-100>
Evidence Level: {evidence.evidence_level}
Summary: <one short reliability critique>
Findings:
- <short finding focused on observed behavior, trace quality, or answer quality>

User prompt:
{evidence.prompt}

Answer:
{evidence.response}

Evidence:
{evidence.to_dict()}
"""

    @classmethod
    def _parse_critique(
        cls, critique_text: str, evidence: EvaluationEvidence
    ) -> ReliabilityCritique:
        """Parse structured reliability critique from model text."""

        tool_reliability = cls._parse_score(
            critique_text, "tool reliability", "tool_use", "tool use"
        )
        return ReliabilityCritique(
            hallucination=cls._parse_score(critique_text, "hallucination"),
            reasoning=cls._parse_score(critique_text, "reasoning"),
            tool_reliability=tool_reliability,
            consistency=cls._parse_score(critique_text, "consistency"),
            task_completion=cls._parse_score(
                critique_text, "task completion", "task_completion"
            ),
            confidence_calibration=cls._parse_score(
                critique_text, "confidence calibration", "calibration"
            ),
            execution_efficiency=cls._parse_score(
                critique_text, "execution efficiency", "efficiency"
            ),
            evidence_level=evidence.evidence_level,
            summary=cls._parse_summary(critique_text),
            findings=cls._parse_findings(critique_text),
        )

    @staticmethod
    def _parse_score(text: str, *labels: str) -> int:
        """Parse a 0-100 score for one reliability dimension."""

        for label in labels:
            pattern = rf"{re.escape(label).replace(r'\ ', r'[\s_-]+')}\s*:\s*(\d{{1,3}})"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return _clamp_score(int(match.group(1)))

        return 50

    @staticmethod
    def _parse_summary(text: str) -> str:
        """Parse the short summary from critique text."""

        summary_match = re.search(r"summary\s*:\s*(.+)", text, re.IGNORECASE)
        if summary_match:
            return _single_line(summary_match.group(1))

        critique_match = re.search(r"critique\s*:\s*(.+)", text, re.IGNORECASE)
        if critique_match:
            return _single_line(critique_match.group(1))

        return "Unable to parse summary; review the dimension scores before trusting this result."

    @staticmethod
    def _parse_findings(text: str) -> list[str]:
        """Parse short findings from bullet lines."""

        findings_section = re.search(
            r"findings\s*:\s*(.+)", text, re.IGNORECASE | re.DOTALL
        )
        if not findings_section:
            return []

        findings: list[str] = []
        for line in findings_section.group(1).splitlines():
            cleaned = re.sub(r"^\s*[-*]\s*", "", line).strip()
            if cleaned:
                findings.append(_single_line(cleaned))

        return findings

    @staticmethod
    def _apply_observed_adjustments(
        critique: ReliabilityCritique,
        evidence: EvaluationEvidence,
        failure_causes: list[FailureCause] | None = None,
    ) -> ReliabilityCritique:
        """Apply deterministic trace checks before calculating confidence."""

        tool_reliability = critique.tool_reliability
        execution_efficiency = critique.execution_efficiency
        findings = list(critique.findings)
        failure_causes = failure_causes or []

        if any(cause.type == "missing_tool_outputs" for cause in failure_causes):
            tool_reliability = min(tool_reliability, 60)
            findings.append("Tool calls were supplied without matching tool outputs.")

        if any(cause.type == "redundant_tool_calls" for cause in failure_causes):
            worst_impact = min(
                cause.impact
                for cause in failure_causes
                if cause.type == "redundant_tool_calls"
            )
            execution_efficiency = min(execution_efficiency, max(20, 85 + worst_impact))
            findings.append("Repeated tool calls suggest avoidable execution overhead.")

        if any(cause.type == "runtime_failures" for cause in failure_causes):
            worst_impact = min(
                cause.impact
                for cause in failure_causes
                if cause.type == "runtime_failures"
            )
            execution_efficiency = min(execution_efficiency, max(20, 90 + worst_impact))
            findings.append("Retries reduced execution efficiency.")
            tool_reliability = min(tool_reliability, 65)
            findings.append("Runtime errors were captured in the execution evidence.")

        if any(cause.type == "ignored_tool_output" for cause in failure_causes):
            task_completion = min(critique.task_completion, 72)
        else:
            task_completion = critique.task_completion

        if any(cause.type == "confidence_mismatch" for cause in failure_causes):
            confidence_calibration = min(critique.confidence_calibration, 65)
        else:
            confidence_calibration = critique.confidence_calibration

        if any(cause.type == "unsupported_claims" for cause in failure_causes):
            hallucination = min(critique.hallucination, 68)
        else:
            hallucination = critique.hallucination

        return ReliabilityCritique(
            hallucination=hallucination,
            reasoning=critique.reasoning,
            tool_reliability=tool_reliability,
            consistency=critique.consistency,
            task_completion=task_completion,
            confidence_calibration=confidence_calibration,
            execution_efficiency=execution_efficiency,
            evidence_level=critique.evidence_level,
            summary=critique.summary,
            findings=findings,
        )

    @staticmethod
    def _calculate_confidence(
        critique: ReliabilityCritique, evidence: EvaluationEvidence
    ) -> int:
        """Calculate an evidence-weighted confidence score."""

        scores = (
            critique.hallucination,
            critique.reasoning,
            critique.tool_reliability,
            critique.consistency,
            critique.task_completion,
            critique.confidence_calibration,
            critique.execution_efficiency,
        )
        raw_score = sum(scores) / len(scores)
        multiplier = {
            "response_only": 0.85,
            "trace_available": 0.95,
            "fully_instrumented": 1.0,
        }[evidence.evidence_level]
        return round(raw_score * multiplier)

    @staticmethod
    def _trust_level(confidence: int) -> TrustLevel:
        """Map confidence to a simple trust label."""

        if confidence >= 75:
            return "High"
        if confidence >= 50:
            return "Moderate"
        return "Low"


def _clamp_score(score: int) -> int:
    """Clamp a score to the required 0-100 range."""

    return max(0, min(100, score))


def _single_line(text: str) -> str:
    """Normalize generated text into a compact single-line critique."""

    return " ".join(text.strip().split())


class EvidenceRecorder(AbstractContextManager["EvidenceRecorder"]):
    """Context manager that captures execution evidence for SDK-style use."""

    def __init__(self, prompt: str = ""):
        self.prompt = prompt
        self.response = ""
        self.tool_calls: list[ToolCall] = []
        self.tool_outputs: list[ToolOutput] = []
        self.trace: list[dict[str, Any]] = []
        self.token_usage: dict[str, Any] = {}
        self.errors: list[str] = []
        self.retries = 0
        self._start = 0.0
        self._token = None

    def __enter__(self) -> "EvidenceRecorder":
        self._start = time.perf_counter()
        self._token = _CURRENT_RECORDER.set(self)
        self.record_event("agent_start")
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> bool:
        if exc_value is not None:
            self.errors.append(str(exc_value))
            self.record_event("error", error=str(exc_value))
        self.record_event("agent_finish")
        if self._token is not None:
            _CURRENT_RECORDER.reset(self._token)
        return False

    def record_event(self, name: str, **payload: Any) -> None:
        """Record a generic framework event."""

        event = {"event": name, "timestamp": time.time()}
        event.update(payload)
        self.trace.append(event)

    def record_tool_call(
        self, tool: str, args: dict[str, Any] | None = None, call_id: str | None = None
    ) -> None:
        """Record the start of a tool call."""

        self.tool_calls.append(
            ToolCall(tool=tool, args=args or {}, id=call_id, timestamp=time.time())
        )
        self.record_event("tool_start", tool=tool, args=args or {}, call_id=call_id)

    def record_tool_output(
        self,
        tool: str,
        output: Any,
        call_id: str | None = None,
        error: str | None = None,
    ) -> None:
        """Record the end of a tool call."""

        self.tool_outputs.append(
            ToolOutput(
                tool=tool,
                output=output,
                call_id=call_id,
                error=error,
                timestamp=time.time(),
            )
        )
        if error is not None:
            self.errors.append(error)
        self.record_event(
            "tool_end", tool=tool, output=output, call_id=call_id, error=error
        )

    def record_llm_call(
        self, model: str | None = None, token_usage: dict[str, Any] | None = None
    ) -> None:
        """Record an LLM invocation from a framework adapter."""

        if token_usage:
            self.token_usage.update(token_usage)
        self.record_event("llm_call", model=model, token_usage=token_usage or {})

    def finish(self, response: str = "", prompt: str | None = None) -> EvaluationEvidence:
        """Return captured evidence in Critiqor's normalized shape."""

        if prompt is not None:
            self.prompt = prompt
        if response:
            self.response = response

        latency = time.perf_counter() - self._start if self._start else None
        return EvaluationEvidence.from_payload(
            prompt=self.prompt,
            response=self.response,
            tool_calls=self.tool_calls,
            tool_outputs=self.tool_outputs,
            trace=self.trace,
            metrics=RuntimeMetrics(
                latency=latency,
                token_usage=self.token_usage,
                retries=self.retries,
                errors=self.errors,
            ),
            evidence_level="fully_instrumented",
        )

    def wrap_tool(self, name: str, func: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a callable tool and automatically capture call/output evidence."""

        def wrapped(*args: Any, **kwargs: Any) -> Any:
            call_id = f"{name}-{len(self.tool_calls) + 1}"
            self.record_tool_call(
                name, {"args": list(args), "kwargs": dict(kwargs)}, call_id=call_id
            )
            try:
                output = func(*args, **kwargs)
            except Exception as exc:
                self.record_tool_output(name, "", call_id=call_id, error=str(exc))
                raise
            self.record_tool_output(name, output, call_id=call_id)
            return output

        return wrapped


def monitor(prompt: str = "") -> EvidenceRecorder:
    """Create an instrumentation context manager for automatic evidence capture."""

    return EvidenceRecorder(prompt=prompt)


def attach_critiqor(agent: Any) -> "CritiqorTracer":
    """Attach Critiqor evidence auto-discovery to a framework agent."""

    return CritiqorTracer(agent, framework_name=detect_framework(agent))


def detect_failure_causes(evidence: EvaluationEvidence) -> list[FailureCause]:
    """Run deterministic detectors that explain trust-score penalties."""

    causes: list[FailureCause] = []
    causes.extend(_detect_redundant_tool_calls(evidence))
    causes.extend(_detect_ignored_tool_outputs(evidence))
    causes.extend(_detect_runtime_failures(evidence))
    causes.extend(_detect_unsupported_claims(evidence))
    causes.extend(_detect_confidence_mismatch(evidence))
    if evidence.tool_calls and not evidence.tool_outputs:
        causes.append(
            FailureCause(
                type="missing_tool_outputs",
                severity="medium",
                impact=-8,
                description="Tool calls were observed, but no matching tool outputs were supplied.",
            )
        )
    return [_enrich_failure_cause(cause) for cause in causes]


def compare_runs(run_a: Any, run_b: Any) -> RunComparison:
    """Compare two evaluations, records, or result dictionaries."""

    score_a = _scores_from_run(run_a)
    score_b = _scores_from_run(run_b)
    trust_change = _trust_score_from_run(run_b) - _trust_score_from_run(run_a)
    dimensions = sorted(set(score_a) | set(score_b))
    changes = {
        dimension: score_b.get(dimension, 0) - score_a.get(dimension, 0)
        for dimension in dimensions
    }

    improved = [name for name, change in changes.items() if change >= 5]
    declined = [name for name, change in changes.items() if change <= -5]
    if improved and declined:
        summary = (
            f"{_human_dimension(improved[0])} improved while "
            f"{_human_dimension(declined[0])} declined."
        )
    elif improved:
        summary = f"{_human_dimension(improved[0])} improved."
    elif declined:
        summary = f"{_human_dimension(declined[0])} declined."
    else:
        summary = "Reliability remained broadly stable."

    return RunComparison(
        trust_change=trust_change,
        changes=changes,
        summary=summary,
    )


def save_evaluation(
    evaluation: CritiqorResult | EvaluationRecord | dict[str, Any],
    path: str | Path = "critiqor_evaluations.jsonl",
    agent_id: str = "default",
    run_id: str | None = None,
) -> EvaluationRecord:
    """Persist one evaluation result as JSON Lines and return the stored record."""

    record = _record_from_evaluation(evaluation, agent_id=agent_id, run_id=run_id)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")
    return record


def load_evaluations(
    path: str | Path = "critiqor_evaluations.jsonl",
    agent_id: str | None = None,
    limit: int | None = None,
) -> list[EvaluationRecord]:
    """Load persisted Critiqor evaluations from JSON Lines storage."""

    source = Path(path)
    if not source.exists():
        return []

    records: list[EvaluationRecord] = []
    with source.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            payload = json.loads(line)
            record = EvaluationRecord.from_dict(payload)
            if agent_id is None or record.agent_id == agent_id:
                records.append(record)

    if limit is not None:
        return records[-limit:]
    return records


def analyze_trends(
    evaluations: Sequence[Any],
    window: int | None = None,
) -> TrendAnalysis:
    """Analyze reliability direction across historical evaluations."""

    runs = list(evaluations)
    if window is not None:
        runs = runs[-window:]
    if len(runs) < 2:
        return TrendAnalysis(
            trust_trend="insufficient_data",
            trust_change=0,
            hallucination_change=0,
            tool_reliability_change=0,
            reasoning_change=0,
            summary="At least two evaluations are required to calculate a trend.",
        )

    first = runs[0]
    last = runs[-1]
    first_scores = _scores_from_run(first)
    last_scores = _scores_from_run(last)
    trust_change = _trust_score_from_run(last) - _trust_score_from_run(first)
    direction: TrendDirection
    if trust_change >= 5:
        direction = "improving"
    elif trust_change <= -5:
        direction = "declining"
    else:
        direction = "stable"

    summary = (
        f"Trust has {direction} by {abs(trust_change)} points over the last "
        f"{len(runs)} runs."
    )
    return TrendAnalysis(
        trust_trend=direction,
        trust_change=trust_change,
        hallucination_change=last_scores.get("hallucination", 0)
        - first_scores.get("hallucination", 0),
        tool_reliability_change=last_scores.get("tool_reliability", 0)
        - first_scores.get("tool_reliability", 0),
        reasoning_change=last_scores.get("reasoning", 0)
        - first_scores.get("reasoning", 0),
        summary=summary,
    )


def recommend_deployment(
    trust_score: int,
    evaluation_confidence: int,
    failure_causes: Sequence[FailureCause] | None = None,
) -> DeploymentRecommendation:
    """Translate reliability intelligence into a deployment action."""

    failure_causes = list(failure_causes or [])
    has_high_severity = any(cause.severity == "high" for cause in failure_causes)
    has_runtime_failure = any(cause.type == "runtime_failures" for cause in failure_causes)
    if trust_score < 50 or evaluation_confidence < 45 or has_runtime_failure:
        return "unsafe_for_production"
    if trust_score < 75 or evaluation_confidence < 70 or has_high_severity:
        return "review_recommended"
    return "safe_to_deploy"


def benchmark_run(
    current_run: Any,
    historical_runs: Sequence[Any],
) -> int:
    """Return the percentile for the current run against historical trust scores."""

    historical_scores = [_trust_score_from_run(run) for run in historical_runs]
    if not historical_scores:
        return 100
    current_score = _trust_score_from_run(current_run)
    at_or_below = sum(1 for score in historical_scores if score <= current_score)
    return _clamp_score(round((at_or_below / len(historical_scores)) * 100))


def add_benchmark(
    result: CritiqorResult,
    historical_runs: Sequence[Any],
) -> CritiqorResult:
    """Return a copy of a result with benchmark percentile populated."""

    return CritiqorResult(
        answer=result.answer,
        confidence=result.confidence,
        trust_level=result.trust_level,
        critique=result.critique,
        evidence=result.evidence,
        failure_causes=list(result.failure_causes),
        evaluation_confidence=result.evaluation_confidence,
        deployment_recommendation=result.deployment_recommendation,
        benchmark_percentile=benchmark_run(result, historical_runs),
    )


def register_agent(agent_profile: AgentProfile | dict[str, Any]) -> AgentProfile:
    """Register an agent profile for cross-agent ranking."""

    profile = (
        agent_profile
        if isinstance(agent_profile, AgentProfile)
        else AgentProfile.from_dict(agent_profile)
    )
    if not profile.agent_id:
        raise ValueError("Agent profile requires a non-empty agent_id.")
    _AGENT_REGISTRY[profile.agent_id] = profile
    _AGENT_RUNS.setdefault(profile.agent_id, [])
    return profile


def submit_run(agent_id: str, evaluation_result: Any) -> Any:
    """Submit one evaluation or benchmark result to an agent leaderboard profile."""

    if agent_id not in _AGENT_REGISTRY:
        register_agent(
            AgentProfile(
                agent_id=agent_id,
                name=agent_id,
                category=_category_from_run(evaluation_result),
            )
        )
    _AGENT_RUNS.setdefault(agent_id, []).append(evaluation_result)

    run_id = _run_id_from_run(evaluation_result)
    if run_id:
        graph = build_causal_graph(
            _trace_from_run(evaluation_result),
            _primary_failure_event(evaluation_result),
            run_id=run_id,
        )
        _CAUSAL_GRAPHS[run_id] = graph
    return evaluation_result


def generate_leaderboard(category: str = "general") -> Leaderboard:
    """Generate global rankings for registered agents in one category."""

    agent_scores: list[tuple[AgentProfile, int, int]] = []
    for agent_id, profile in _AGENT_REGISTRY.items():
        if _normalize_category(profile.category) != _normalize_category(category):
            continue
        runs = _AGENT_RUNS.get(agent_id, [])
        if not runs:
            continue
        trust_score = round(
            sum(_trust_score_from_run(run) for run in runs) / max(1, len(runs))
        )
        agent_scores.append((profile, trust_score, len(runs)))

    sorted_scores = sorted(agent_scores, key=lambda item: item[1], reverse=True)
    all_scores = [score for _profile, score, _run_count in sorted_scores]
    rankings = [
        LeaderboardEntry(
            rank=index + 1,
            agent_id=profile.agent_id,
            name=profile.name,
            category=profile.category,
            trust_score=score,
            percentile=_percentile_from_scores(score, all_scores),
            run_count=run_count,
        )
        for index, (profile, score, run_count) in enumerate(sorted_scores)
    ]
    return Leaderboard(category=category, rankings=rankings)


def build_causal_graph(
    trace: Sequence[dict[str, Any]] | EvaluationEvidence | Any,
    failure_event: str | FailureCause | dict[str, Any],
    run_id: str | None = None,
) -> CausalGraph:
    """Build a directed causal graph from trace evidence and a failure event."""

    evidence = trace if isinstance(trace, EvaluationEvidence) else None
    trace_events = evidence.trace if evidence is not None else _coerce_trace(trace)
    failure_type = _failure_type(failure_event)
    nodes = _infer_causal_nodes(trace_events, failure_type, evidence)
    edges = [
        CausalGraphEdge(
            node=nodes[index],
            leads_to=nodes[index + 1],
            evidence=_evidence_for_causal_edge(nodes[index], trace_events),
        )
        for index in range(len(nodes) - 1)
    ]
    graph = CausalGraph(
        failure_event=failure_type,
        causal_graph=edges,
        run_id=run_id,
    )
    if run_id:
        _CAUSAL_GRAPHS[run_id] = graph
    return graph


def explain_failure_chain(run_id: str) -> str:
    """Explain a previously submitted failure chain step by step."""

    graph = _CAUSAL_GRAPHS.get(run_id)
    if graph is None:
        return "No causal graph found for this run."
    return graph.explain()


def clear_network_state() -> None:
    """Clear in-memory agent and causal graph registries."""

    _AGENT_REGISTRY.clear()
    _AGENT_RUNS.clear()
    _CAUSAL_GRAPHS.clear()


class CritiqorBenchmark:
    """Reproducible benchmark suite for a category of agents."""

    DEFAULT_CASES: dict[AgentType, list[BenchmarkCase]] = {
        "coding": [
            BenchmarkCase(
                name="coding_correctness",
                prompt="Explain how you would fix a failing unit test.",
                category="correctness",
            ),
            BenchmarkCase(
                name="coding_tool_usage",
                prompt="Describe the tool evidence you would inspect before changing code.",
                category="tool_usage",
            ),
        ],
        "research": [
            BenchmarkCase(
                name="research_grounding",
                prompt="Summarize a claim and state what evidence would support it.",
                category="evidence_quality",
            ),
            BenchmarkCase(
                name="research_hallucination_risk",
                prompt="Answer cautiously when source evidence is missing.",
                category="source_grounding",
            ),
        ],
        "customer_support": [
            BenchmarkCase(
                name="support_resolution",
                prompt="Resolve a customer issue consistently and accurately.",
                category="resolution_quality",
            ),
            BenchmarkCase(
                name="support_consistency",
                prompt="Give a policy-safe response to a refund request.",
                category="consistency",
            ),
        ],
        "general": [
            BenchmarkCase(
                name="general_trust",
                prompt="Complete a task reliably and explain uncertainty.",
                category="overall_trust",
            ),
            BenchmarkCase(
                name="general_efficiency",
                prompt="Solve a small task with minimal redundant steps.",
                category="efficiency",
            ),
        ],
    }

    def __init__(
        self,
        name: str,
        agent_type: AgentType = "general",
        cases: Sequence[BenchmarkCase | dict[str, Any] | str] | None = None,
        historical_runs: Sequence[Any] | None = None,
    ):
        self.name = name
        self.agent_type = agent_type
        raw_cases = list(cases) if cases is not None else self.DEFAULT_CASES[agent_type]
        self.cases = [_coerce_benchmark_case(case) for case in raw_cases]
        self.historical_runs = list(historical_runs or [])

    def run(self, agent: Any) -> BenchmarkResult:
        """Run the benchmark against an agent and return aggregate reliability."""

        results = [Critiqor(agent).run(case.prompt) for case in self.cases]
        trust_score = round(
            sum(result.confidence for result in results) / max(1, len(results))
        )
        scores = _average_scores(results)
        percentile = benchmark_run({"trust_score": trust_score}, self.historical_runs)
        return BenchmarkResult(
            name=self.name,
            agent_type=self.agent_type,
            trust_score=trust_score,
            percentile=percentile,
            run_count=len(results),
            scores=scores,
            results=results,
        )


class ReliabilityDashboardData:
    """Data layer for future dashboard or hosted product surfaces."""

    def __init__(
        self,
        run_history: Sequence[Any] | None = None,
        benchmarks: Sequence[BenchmarkResult | dict[str, Any]] | None = None,
    ):
        self.run_history = list(run_history or [])
        self.benchmarks = list(benchmarks or [])

    def get_trends(self) -> TrendAnalysis:
        """Return trend analysis for the stored run history."""

        return analyze_trends(self.run_history)

    def get_benchmarks(self) -> list[dict[str, Any]]:
        """Return benchmark summaries."""

        benchmark_payloads: list[dict[str, Any]] = []
        for benchmark in self.benchmarks:
            if isinstance(benchmark, BenchmarkResult):
                benchmark_payloads.append(benchmark.to_dict())
            elif isinstance(benchmark, dict):
                benchmark_payloads.append(dict(benchmark))
        return benchmark_payloads

    def get_failures(self) -> list[dict[str, Any]]:
        """Return flattened failure causes across stored runs."""

        failures: list[dict[str, Any]] = []
        for run in self.run_history:
            for cause in _failure_causes_from_run(run):
                failures.append(cause.to_dict())
        return failures

    def to_dict(self) -> dict[str, Any]:
        """Return dashboard-ready data without building a UI."""

        return {
            "run_history": [_run_to_dict(run) for run in self.run_history],
            "benchmarks": self.get_benchmarks(),
            "failure_causes": self.get_failures(),
            "trends": self.get_trends().to_dict(),
        }


def certification_criteria_table() -> list[dict[str, Any]]:
    """Return the criteria for each Critiqor certification level."""

    return [
        {
            "level": "bronze",
            "minimum_trust_score": 70,
            "minimum_percentile": 50,
            "minimum_evaluation_confidence": 55,
            "evidence_requirement": "response_only or better",
            "failure_limit": "no unsafe production recommendation",
        },
        {
            "level": "silver",
            "minimum_trust_score": 80,
            "minimum_percentile": 70,
            "minimum_evaluation_confidence": 70,
            "evidence_requirement": "trace_available or better preferred",
            "failure_limit": "no high-severity failure causes",
        },
        {
            "level": "gold",
            "minimum_trust_score": 90,
            "minimum_percentile": 85,
            "minimum_evaluation_confidence": 80,
            "evidence_requirement": "trace_available or better",
            "failure_limit": "no high-severity failure causes",
        },
        {
            "level": "platinum",
            "minimum_trust_score": 95,
            "minimum_percentile": 95,
            "minimum_evaluation_confidence": 90,
            "evidence_requirement": "fully_instrumented",
            "failure_limit": "no high-severity failure causes",
        },
    ]


def certify_run(
    run: Any,
    percentile: int | None = None,
) -> ReliabilityCertification:
    """Generate a standardized Critiqor reliability certification."""

    trust_score = _trust_score_from_run(run)
    evaluation_confidence = _evaluation_confidence_from_run(run)
    evidence_level = _evidence_level_from_run(run)
    failure_causes = _failure_causes_from_run(run)
    has_high_failure = any(cause.severity == "high" for cause in failure_causes)
    deployment = _deployment_from_run(run)
    percentile = benchmark_run(run, []) if percentile is None else percentile

    level: CertificationLevel = "none"
    for criteria in certification_criteria_table():
        candidate = str(criteria["level"])
        if trust_score < int(criteria["minimum_trust_score"]):
            continue
        if percentile < int(criteria["minimum_percentile"]):
            continue
        if evaluation_confidence < int(criteria["minimum_evaluation_confidence"]):
            continue
        if candidate == "platinum" and evidence_level != "fully_instrumented":
            continue
        if has_high_failure:
            continue
        if deployment == "unsafe_for_production":
            continue
        level = _coerce_certification_level(candidate)

    badge_label = "Critiqor Certified" if level != "none" else "Critiqor Reviewed"
    markdown_badge = (
        f"![{badge_label}: {level} | Trust Score {trust_score} | "
        f"Top {100 - percentile}%](https://img.shields.io/badge/"
        f"Critiqor-{level}-{_badge_color(level)})"
    )
    return ReliabilityCertification(
        certification_level=level,
        trust_score=trust_score,
        percentile=percentile,
        markdown_badge=markdown_badge,
        criteria={
            "evaluation_confidence": evaluation_confidence,
            "evidence_level": evidence_level,
            "high_severity_failures": has_high_failure,
            "deployment_recommendation": deployment,
        },
    )


def prepare_benchmark_contribution(
    evaluation: CritiqorResult | EvaluationRecord | dict[str, Any],
    agent_type: AgentType = "general",
    certification_level: CertificationLevel = "none",
) -> BenchmarkContribution:
    """Create an opt-in anonymized contribution with no prompts or outputs."""

    return BenchmarkContribution(
        scores=_scores_from_run(evaluation),
        failure_types=[cause.type for cause in _failure_causes_from_run(evaluation)],
        agent_type=agent_type,
        trust_score=_trust_score_from_run(evaluation),
        evidence_level=_evidence_level_from_run(evaluation),
        certification_level=certification_level,
    )


def save_benchmark_contribution(
    contribution: BenchmarkContribution,
    path: str | Path = "critiqor_benchmark_contributions.jsonl",
) -> BenchmarkContribution:
    """Persist one opt-in anonymized benchmark contribution."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(contribution.to_dict(), sort_keys=True) + "\n")
    return contribution


def check_policy(
    evaluation: CritiqorResult | EvaluationRecord | dict[str, Any],
    policy: dict[str, Any] | None = None,
) -> PolicyCheckResult:
    """Evaluate a deployment policy for CI/CD workflows."""

    policy = dict(policy or {})
    trust_score = _trust_score_from_run(evaluation)
    scores = _scores_from_run(evaluation)
    causes = _failure_causes_from_run(evaluation)
    evaluation_confidence = _evaluation_confidence_from_run(evaluation)

    messages: list[str] = []
    minimum_trust = int(policy.get("minimum_trust_score", 0) or 0)
    if trust_score < minimum_trust:
        messages.append(
            f"Trust score {trust_score} is below threshold {minimum_trust}."
        )

    hallucination_risk = 100 - scores.get("hallucination", 100)
    max_hallucination_risk = policy.get("maximum_hallucination_risk")
    if max_hallucination_risk is not None and hallucination_risk > int(
        max_hallucination_risk
    ):
        messages.append(
            "Hallucination risk "
            f"{hallucination_risk} exceeds threshold {max_hallucination_risk}."
        )

    minimum_tool_reliability = policy.get("minimum_tool_reliability")
    if minimum_tool_reliability is not None and scores.get(
        "tool_reliability", 100
    ) < int(minimum_tool_reliability):
        messages.append("Tool reliability below threshold.")

    if policy.get("block_high_severity_failures", True) and any(
        cause.severity == "high" for cause in causes
    ):
        messages.append("High-severity failure cause detected.")

    minimum_eval_confidence = policy.get("minimum_evaluation_confidence")
    if minimum_eval_confidence is not None and evaluation_confidence < int(
        minimum_eval_confidence
    ):
        messages.append(
            "Evaluation confidence "
            f"{evaluation_confidence} is below threshold {minimum_eval_confidence}."
        )

    passed = not messages
    return PolicyCheckResult(
        passed=passed,
        deployment_recommendation="safe_to_deploy"
        if passed
        else "unsafe_for_production",
        messages=messages or ["Deployment allowed."],
    )


def generate_insights(evaluations: Sequence[Any]) -> ReliabilityInsight:
    """Generate an executive reliability summary."""

    runs = list(evaluations)
    if not runs:
        return ReliabilityInsight(
            summary="No reliability data is available yet.",
            primary_drivers=[],
        )

    trend = analyze_trends(runs)
    failures: dict[str, int] = {}
    for run in runs:
        for cause in _failure_causes_from_run(run):
            failures[cause.type] = failures.get(cause.type, 0) + 1

    primary_drivers = [
        failure_type
        for failure_type, _count in sorted(
            failures.items(), key=lambda item: item[1], reverse=True
        )[:3]
    ]
    if primary_drivers:
        driver_text = " and ".join(_human_dimension(driver) for driver in primary_drivers[:2])
        summary = (
            f"Trust has {trend.trust_trend} by {abs(trend.trust_change)} points. "
            f"The primary driver is {driver_text}."
        )
    else:
        summary = trend.summary

    return ReliabilityInsight(summary=summary, primary_drivers=primary_drivers)


class CritiqorTracer:
    """Framework adapter that records common agent lifecycle events.

    The adapter can subscribe to frameworks exposing ``on(event, callback)`` or
    ``subscribe(event, callback)``. It intentionally uses common event names so
    LangGraph, LangChain, OpenAI Agents SDK, CrewAI, AutoGen, PydanticAI, and
    Mastra integrations can map their native callbacks into Critiqor evidence.
    """

    EVENTS = (
        "agent_start",
        "agent_step",
        "tool_start",
        "tool_end",
        "llm_call",
        "agent_finish",
        "retry",
        "error",
    )

    def __init__(
        self,
        agent: Any | None = None,
        recorder: EvidenceRecorder | None = None,
        framework_name: str | None = None,
    ):
        self.agent = agent
        self.recorder = recorder or EvidenceRecorder()
        self.framework_name = framework_name or (
            detect_framework(agent) if agent is not None else "generic"
        )
        if agent is not None:
            self.attach(agent)

    def attach(self, agent: Any) -> None:
        """Subscribe to a framework agent if it exposes event hooks."""

        subscriber = getattr(agent, "on", None) or getattr(agent, "subscribe", None)
        if subscriber is None:
            return
        for event_name in self.EVENTS:
            subscriber(event_name, self._handler(event_name))

    def _handler(self, event_name: str) -> Callable[..., None]:
        def handle(*args: Any, **kwargs: Any) -> None:
            payload = dict(kwargs)
            if args:
                payload["args"] = list(args)
            self.record(event_name, payload)

        return handle

    def record(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        """Record one framework event into Critiqor evidence."""

        payload = payload or {}
        if event_name == "tool_start":
            self.recorder.record_tool_call(
                str(payload.get("tool", payload.get("name", "tool"))),
                dict(payload.get("args", {})) if isinstance(payload.get("args", {}), dict) else {"args": payload.get("args")},
                payload.get("call_id"),
            )
            return
        if event_name == "tool_end":
            self.recorder.record_tool_output(
                str(payload.get("tool", payload.get("name", "tool"))),
                payload.get("output", payload.get("result", "")),
                payload.get("call_id"),
                payload.get("error"),
            )
            return
        if event_name == "llm_call":
            token_usage = payload.get("token_usage")
            self.recorder.record_llm_call(
                model=payload.get("model"),
                token_usage=token_usage if isinstance(token_usage, dict) else None,
            )
            return
        if event_name == "retry":
            self.recorder.retries += 1
        if event_name == "error" and "error" in payload:
            self.recorder.errors.append(str(payload["error"]))
        self.recorder.record_event(event_name, **payload)


class OpenTelemetryAdapter:
    """Convert OpenTelemetry-like span dictionaries into Critiqor evidence."""

    def __init__(self, recorder: EvidenceRecorder | None = None):
        self.recorder = recorder or EvidenceRecorder()

    def ingest_span(self, span: dict[str, Any]) -> None:
        """Record one span shaped like an OpenTelemetry export payload."""

        attributes = dict(span.get("attributes", {}))
        name = str(span.get("name", attributes.get("event", "span")))
        kind = attributes.get("critiqor.kind", attributes.get("span.kind", name))

        if kind in {"tool", "tool_call", "tool_start"}:
            self.recorder.record_tool_call(
                str(attributes.get("tool.name", name)),
                dict(attributes.get("tool.args", {}))
                if isinstance(attributes.get("tool.args", {}), dict)
                else {},
                attributes.get("tool.call_id"),
            )
        elif kind in {"tool_end", "tool_output"}:
            self.recorder.record_tool_output(
                str(attributes.get("tool.name", name)),
                attributes.get("tool.output", ""),
                attributes.get("tool.call_id"),
                attributes.get("error"),
            )
        elif kind in {"llm", "llm_call"}:
            token_usage = attributes.get("llm.token_usage")
            self.recorder.record_llm_call(
                model=attributes.get("llm.model"),
                token_usage=token_usage if isinstance(token_usage, dict) else None,
            )
        else:
            self.recorder.record_event(name, **attributes)


def _detect_redundant_tool_calls(evidence: EvaluationEvidence) -> list[FailureCause]:
    grouped: dict[tuple[str, tuple[tuple[str, str], ...]], int] = {}
    for call in evidence.tool_calls:
        signature = (
            call.tool,
            tuple(sorted((str(key), str(value)) for key, value in call.args.items())),
        )
        grouped[signature] = grouped.get(signature, 0) + 1

    causes: list[FailureCause] = []
    for (tool, _args), count in grouped.items():
        if count <= 1:
            continue
        repeats = count - 1
        severity: FailureSeverity = "high" if count >= 4 else "medium"
        impact = max(-30, -15 * repeats)
        causes.append(
            FailureCause(
                type="redundant_tool_calls",
                severity=severity,
                impact=impact,
                description=f"{tool} tool called {count} times with identical arguments.",
            )
        )
    return causes


def _detect_ignored_tool_outputs(evidence: EvaluationEvidence) -> list[FailureCause]:
    if not evidence.tool_outputs or not evidence.response.strip():
        return []

    ignored = 0
    for output in evidence.tool_outputs:
        if output.error:
            continue
        output_text = _normalize_text(str(output.output))
        if not output_text:
            continue
        if not _text_overlap(output_text, evidence.response):
            ignored += 1

    if ignored == 0:
        return []

    severity: FailureSeverity = "high" if ignored >= 3 else "medium"
    impact = max(-20, -7 * ignored)
    return [
        FailureCause(
            type="ignored_tool_output",
            severity=severity,
            impact=impact,
            description=(
                f"{ignored} tool output"
                f"{'s were' if ignored != 1 else ' was'} not reflected in the final response."
            ),
        )
    ]


def _detect_runtime_failures(evidence: EvaluationEvidence) -> list[FailureCause]:
    errors = list(evidence.metrics.errors)
    errors.extend(
        str(output.error)
        for output in evidence.tool_outputs
        if output.error is not None and str(output.error)
    )
    timeout_events = [
        event
        for event in evidence.trace
        if "timeout" in _normalize_text(str(event.get("event", "")))
        or "timeout" in _normalize_text(str(event.get("error", "")))
    ]
    retry_count = evidence.metrics.retries + sum(
        1 for event in evidence.trace if str(event.get("event", "")).lower() == "retry"
    )

    if not errors and not timeout_events and retry_count == 0:
        return []

    severity: FailureSeverity = "high" if errors or timeout_events else "medium"
    impact = max(-30, -(10 * len(errors) + 8 * len(timeout_events) + 5 * retry_count))
    pieces = []
    if errors:
        pieces.append(f"{len(errors)} error(s)")
    if timeout_events:
        pieces.append(f"{len(timeout_events)} timeout event(s)")
    if retry_count:
        pieces.append(f"{retry_count} retry event(s)")
    return [
        FailureCause(
            type="runtime_failures",
            severity=severity,
            impact=impact,
            description="Runtime evidence captured " + ", ".join(pieces) + ".",
        )
    ]


def _detect_unsupported_claims(evidence: EvaluationEvidence) -> list[FailureCause]:
    response = evidence.response.strip()
    if not response:
        return []

    has_evidence = bool(evidence.tool_outputs or evidence.trace)
    factual_markers = re.findall(
        r"\b(?:\d+(?:\.\d+)?%?|\$?\d{2,}|today|yesterday|latest|current|according to|source|study|report)\b",
        response,
        flags=re.IGNORECASE,
    )
    if has_evidence:
        evidence_text = " ".join(str(output.output) for output in evidence.tool_outputs)
        if factual_markers and not _text_overlap(evidence_text, response):
            return [
                FailureCause(
                    type="unsupported_claims",
                    severity="medium",
                    impact=-9,
                    description="Response contains factual claims that are weakly supported by supplied evidence.",
                )
            ]
        return []

    if factual_markers:
        return [
            FailureCause(
                type="unsupported_claims",
                severity="medium",
                impact=-8,
                description="Response contains specific factual claims without captured supporting evidence.",
            )
        ]
    return []


def _detect_confidence_mismatch(evidence: EvaluationEvidence) -> list[FailureCause]:
    response = evidence.response.lower()
    certainty_terms = (
        "certainly",
        "definitely",
        "guaranteed",
        "without a doubt",
        "100%",
        "always",
        "never",
    )
    high_certainty = any(term in response for term in certainty_terms)
    weak_evidence = evidence.evidence_level == "response_only" or (
        not evidence.tool_outputs and not evidence.trace
    )
    ignored_evidence = bool(_detect_ignored_tool_outputs(evidence))
    if high_certainty and (weak_evidence or ignored_evidence):
        return [
            FailureCause(
                type="confidence_mismatch",
                severity="medium",
                impact=-10,
                description="Response uses high-certainty language without strong supporting evidence.",
            )
        ]
    return []


def calculate_evaluation_confidence(
    evidence: EvaluationEvidence,
    failure_causes: Sequence[FailureCause] | None = None,
) -> int:
    """Score how much Critiqor trusts its own assessment."""

    base = {
        "response_only": 55,
        "trace_available": 78,
        "fully_instrumented": 93,
    }[evidence.evidence_level]
    if evidence.tool_outputs:
        base += 4
    if evidence.metrics.latency is not None:
        base += 3
    if evidence.trace:
        base += 3
    high_causes = sum(1 for cause in failure_causes or [] if cause.severity == "high")
    base -= high_causes * 4
    return _clamp_score(base)


def detect_framework(agent: Any) -> str:
    """Best-effort framework detection for evidence auto-discovery."""

    if agent is None:
        return "generic"
    module_name = getattr(agent.__class__, "__module__", "").lower()
    class_name = agent.__class__.__name__.lower()
    combined = f"{module_name}.{class_name}"
    framework_markers = {
        "langgraph": "langgraph",
        "crewai": "crewai",
        "openai": "openai_agents_sdk",
        "pydantic_ai": "pydanticai",
        "pydanticai": "pydanticai",
        "autogen": "autogen",
        "mastra": "mastra",
        "langchain": "langchain",
    }
    for marker, framework in framework_markers.items():
        if marker in combined:
            return framework
    if hasattr(agent, "graph") or hasattr(agent, "compile"):
        return "langgraph"
    if hasattr(agent, "crew") or hasattr(agent, "kickoff"):
        return "crewai"
    if hasattr(agent, "handoffs") or hasattr(agent, "instructions"):
        return "openai_agents_sdk"
    if hasattr(agent, "on") or hasattr(agent, "subscribe"):
        return "generic_event_agent"
    return "generic"


def _enrich_failure_cause(cause: FailureCause) -> FailureCause:
    if cause.root_cause is not None and cause.recommendation:
        return cause

    root_cause = _root_cause_for_failure(cause)
    return FailureCause(
        type=cause.type,
        severity=cause.severity,
        impact=cause.impact,
        description=cause.description,
        root_cause=root_cause,
        recommendation=cause.recommendation or root_cause.recommended_fix,
    )


def _root_cause_for_failure(cause: FailureCause) -> RootCause:
    root_cause_map = {
        "redundant_tool_calls": RootCause(
            description="The agent repeated the same tool request instead of reusing prior results.",
            impact="Reduced execution efficiency and increased operational cost.",
            trust_penalty=cause.impact,
            recommended_fix="Cache tool outputs and prevent identical requests within the same execution.",
        ),
        "ignored_tool_output": RootCause(
            description="Tool evidence was retrieved successfully but not reflected in the final response.",
            impact="Increased hallucination risk and reduced tool reliability.",
            trust_penalty=cause.impact,
            recommended_fix="Incorporate retrieved evidence into reasoning before generating conclusions.",
        ),
        "runtime_failures": RootCause(
            description="The execution trace captured retries, errors, or timeout-like events.",
            impact="Reduced production reliability and lowered confidence in task completion.",
            trust_penalty=cause.impact,
            recommended_fix="Add error handling, retry limits, timeout controls, and fallback behavior for failing tools.",
        ),
        "unsupported_claims": RootCause(
            description="The final response included specific claims without strong supporting evidence.",
            impact="Increased hallucination risk and weakened factual grounding.",
            trust_penalty=cause.impact,
            recommended_fix="Require source-backed claims or lower certainty when supporting evidence is unavailable.",
        ),
        "confidence_mismatch": RootCause(
            description="The response expressed more certainty than the available evidence supports.",
            impact="Reduced confidence calibration and increased user trust risk.",
            trust_penalty=cause.impact,
            recommended_fix="Calibrate language to evidence strength and explicitly state uncertainty when evidence is weak.",
        ),
        "missing_tool_outputs": RootCause(
            description="Tool calls were captured without corresponding outputs.",
            impact="Prevents Critiqor from validating whether tool evidence was used correctly.",
            trust_penalty=cause.impact,
            recommended_fix="Capture tool_end events and persist outputs for each observed tool_start event.",
        ),
    }
    return root_cause_map.get(
        cause.type,
        RootCause(
            description=cause.description,
            impact="Reduced reliability signal quality.",
            trust_penalty=cause.impact,
            recommended_fix="Inspect the trace and add a targeted guardrail for this failure type.",
        ),
    )


def _record_from_evaluation(
    evaluation: CritiqorResult | EvaluationRecord | dict[str, Any],
    agent_id: str,
    run_id: str | None,
) -> EvaluationRecord:
    if isinstance(evaluation, EvaluationRecord):
        return evaluation
    if isinstance(evaluation, CritiqorResult):
        return evaluation.to_record(agent_id=agent_id, run_id=run_id)
    if isinstance(evaluation, dict):
        if "scores" in evaluation:
            record_payload = dict(evaluation)
            record_payload.setdefault("run_id", run_id or str(uuid4()))
            record_payload.setdefault("agent_id", agent_id)
            record_payload.setdefault(
                "timestamp", datetime.now(timezone.utc).isoformat()
            )
            record_payload.setdefault("trust_score", record_payload.get("confidence", 0))
            record_payload.setdefault("failure_causes", [])
            record_payload.setdefault("evidence_level", "response_only")
            record_payload.setdefault("evaluation_confidence", 0)
            record_payload.setdefault(
                "deployment_recommendation", "review_recommended"
            )
            return EvaluationRecord.from_dict(record_payload)
    raise TypeError("Expected CritiqorResult, EvaluationRecord, or record dictionary.")


def _score_dict(result: CritiqorResult) -> dict[str, int]:
    return {
        "hallucination": result.critique.hallucination,
        "reasoning": result.critique.reasoning,
        "tool_reliability": result.critique.tool_reliability,
        "consistency": result.critique.consistency,
        "task_completion": result.critique.task_completion,
        "confidence_calibration": result.critique.confidence_calibration,
        "execution_efficiency": result.critique.execution_efficiency,
    }


def _scores_from_run(run: Any) -> dict[str, int]:
    if isinstance(run, CritiqorResult):
        return _score_dict(run)
    if isinstance(run, EvaluationRecord):
        return dict(run.scores)
    if isinstance(run, dict):
        if "scores" in run and isinstance(run["scores"], dict):
            return {
                key: int(value)
                for key, value in run["scores"].items()
                if isinstance(value, (int, float))
            }
        critique = run.get("critique")
        if isinstance(critique, dict):
            return {
                key: int(value)
                for key, value in critique.items()
                if key
                in {
                    "hallucination",
                    "reasoning",
                    "tool_reliability",
                    "consistency",
                    "task_completion",
                    "confidence_calibration",
                    "execution_efficiency",
                }
                and isinstance(value, (int, float))
            }
    return {}


def _trust_score_from_run(run: Any) -> int:
    if isinstance(run, CritiqorResult):
        return run.confidence
    if isinstance(run, EvaluationRecord):
        return run.trust_score
    if isinstance(run, dict):
        for key in ("trust_score", "confidence"):
            if key in run and isinstance(run[key], (int, float)):
                return int(run[key])
    scores = _scores_from_run(run)
    if scores:
        return round(sum(scores.values()) / len(scores))
    return 0


def _evaluation_confidence_from_run(run: Any) -> int:
    if isinstance(run, CritiqorResult):
        return run.evaluation_confidence
    if isinstance(run, EvaluationRecord):
        return run.evaluation_confidence
    if isinstance(run, dict):
        value = run.get("evaluation_confidence", 0)
        if isinstance(value, (int, float)):
            return int(value)
    return 0


def _evidence_level_from_run(run: Any) -> EvidenceLevel:
    if isinstance(run, CritiqorResult):
        return run.evidence.evidence_level
    if isinstance(run, EvaluationRecord):
        return run.evidence_level
    if isinstance(run, dict):
        if "evidence_level" in run:
            return _coerce_evidence_level(run["evidence_level"])
        evidence = run.get("evidence")
        if isinstance(evidence, dict):
            return _coerce_evidence_level(evidence.get("evidence_level"))
    return "response_only"


def _deployment_from_run(run: Any) -> DeploymentRecommendation:
    if isinstance(run, CritiqorResult):
        return run.deployment_recommendation
    if isinstance(run, EvaluationRecord):
        return run.deployment_recommendation
    if isinstance(run, dict):
        return _coerce_deployment_recommendation(run.get("deployment_recommendation"))
    return "review_recommended"


def _failure_causes_from_run(run: Any) -> list[FailureCause]:
    if isinstance(run, CritiqorResult):
        return list(run.failure_causes)
    if isinstance(run, EvaluationRecord):
        return list(run.failure_causes)
    if isinstance(run, dict):
        causes = run.get("failure_causes", [])
        if isinstance(causes, list):
            return [
                FailureCause(
                    type=str(cause.get("type", "unknown")),
                    severity=_coerce_severity(cause.get("severity")),
                    impact=int(cause.get("impact", 0) or 0),
                    description=str(cause.get("description", "")),
                    root_cause=_coerce_root_cause(cause.get("root_cause")),
                    recommendation=str(cause.get("recommendation", "")),
                )
                for cause in causes
                if isinstance(cause, dict)
            ]
    return []


def _run_to_dict(run: Any) -> dict[str, Any]:
    if isinstance(run, CritiqorResult):
        return run.to_dict()
    if isinstance(run, EvaluationRecord):
        return run.to_dict()
    if isinstance(run, dict):
        return dict(run)
    return {"trust_score": _trust_score_from_run(run), "scores": _scores_from_run(run)}


def _run_id_from_run(run: Any) -> str:
    if isinstance(run, EvaluationRecord):
        return run.run_id
    if isinstance(run, dict):
        return str(run.get("run_id", ""))
    return ""


def _trace_from_run(run: Any) -> list[dict[str, Any]]:
    if isinstance(run, CritiqorResult):
        return [dict(event) for event in run.evidence.trace]
    if isinstance(run, dict):
        evidence = run.get("evidence")
        if isinstance(evidence, dict):
            return _coerce_trace(evidence.get("trace", []))
        return _coerce_trace(run.get("trace", []))
    return []


def _category_from_run(run: Any) -> str:
    if isinstance(run, BenchmarkResult):
        return run.agent_type
    if isinstance(run, dict):
        return str(run.get("agent_type", run.get("category", "general")))
    return "general"


def _primary_failure_event(run: Any) -> str:
    causes = _failure_causes_from_run(run)
    if causes:
        return sorted(causes, key=lambda cause: cause.impact)[0].type
    scores = _scores_from_run(run)
    if scores:
        weakest = min(scores.items(), key=lambda item: item[1])[0]
        if weakest == "hallucination":
            return "unsupported_claims"
        if weakest == "tool_reliability":
            return "tool_misuse"
        if weakest == "confidence_calibration":
            return "confidence_mismatch"
    return "unknown_failure"


def _normalize_category(category: str) -> str:
    normalized = category.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "coding_agents": "coding",
        "research_agents": "research",
        "support": "customer_support",
        "support_agents": "customer_support",
        "customer_support_agents": "customer_support",
        "general_purpose_agents": "general",
        "general_agents": "general",
    }
    return aliases.get(normalized, normalized)


def _percentile_from_scores(score: int, scores: Sequence[int]) -> int:
    if not scores:
        return 100
    at_or_below = sum(1 for candidate in scores if candidate <= score)
    return _clamp_score(round((at_or_below / len(scores)) * 100))


def _average_scores(results: Sequence[CritiqorResult]) -> dict[str, int]:
    if not results:
        return {}
    dimensions = sorted({dimension for result in results for dimension in _score_dict(result)})
    return {
        dimension: round(
            sum(_score_dict(result).get(dimension, 0) for result in results)
            / len(results)
        )
        for dimension in dimensions
    }


def _coerce_benchmark_case(value: BenchmarkCase | dict[str, Any] | str) -> BenchmarkCase:
    if isinstance(value, BenchmarkCase):
        return value
    if isinstance(value, dict):
        return BenchmarkCase(
            prompt=str(value.get("prompt", "")),
            name=str(value.get("name", "")),
            category=str(value.get("category", "general")),
        )
    return BenchmarkCase(prompt=str(value))


def _coerce_trace(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [dict(event) for event in value if isinstance(event, dict)]
    if isinstance(value, tuple):
        return [dict(event) for event in value if isinstance(event, dict)]
    return []


def _failure_type(value: str | FailureCause | dict[str, Any]) -> str:
    if isinstance(value, FailureCause):
        return value.type
    if isinstance(value, dict):
        return str(value.get("type", value.get("failure_event", "unknown_failure")))
    return str(value or "unknown_failure")


def _infer_causal_nodes(
    trace_events: Sequence[dict[str, Any]],
    failure_type: str,
    evidence: EvaluationEvidence | None = None,
) -> list[str]:
    event_names = {_normalize_text(str(event.get("event", ""))) for event in trace_events}
    tool_events = [event for event in trace_events if "tool" in str(event.get("event", ""))]

    nodes: list[str] = []
    if any("prompt ambiguity" in _normalize_text(str(event)) for event in trace_events):
        nodes.append("prompt_ambiguity")
    elif failure_type in {"ignored_tool_output", "unsupported_claims", "tool_misuse"}:
        nodes.append("prompt_or_task_uncertainty")
    else:
        nodes.append("agent_execution_started")

    if failure_type in {"tool_misuse", "wrong_tool_selection"}:
        nodes.extend(["wrong_tool_selection", "irrelevant_tool_output", "missing_evidence"])
    elif failure_type == "ignored_tool_output":
        if tool_events or (evidence is not None and evidence.tool_outputs):
            nodes.append("tool_returned_evidence")
        nodes.extend(["evidence_not_integrated", "hallucinated_answer"])
    elif failure_type == "redundant_tool_calls":
        nodes.extend(["execution_loop", "redundant_tool_calls", "efficiency_loss"])
    elif failure_type == "runtime_failures":
        nodes.extend(["tool_failure", "retry_or_timeout", "incomplete_execution"])
    elif failure_type == "confidence_mismatch":
        nodes.extend(["weak_evidence", "overconfident_language", "trust_miscalibration"])
    elif failure_type == "unsupported_claims":
        nodes.extend(["missing_evidence", "unsupported_claims", "hallucinated_answer"])
    elif failure_type == "missing_tool_outputs":
        nodes.extend(["tool_call_without_output", "missing_evidence", "low_evaluation_confidence"])
    else:
        if "tool_start" in event_names:
            nodes.append("tool_execution")
        nodes.extend(["unclassified_failure", "reduced_trust"])

    deduped: list[str] = []
    for node in nodes:
        if not deduped or deduped[-1] != node:
            deduped.append(node)
    return deduped if len(deduped) >= 2 else [failure_type, "reduced_trust"]


def _evidence_for_causal_edge(node: str, trace_events: Sequence[dict[str, Any]]) -> str:
    for event in trace_events:
        event_text = _normalize_text(str(event))
        if any(term in event_text for term in _normalize_text(node).split()):
            return str(event.get("event", "")) or str(event)
    return ""


def _causal_node_text(node: str) -> str:
    labels = {
        "prompt_ambiguity": "Prompt was ambiguous",
        "prompt_or_task_uncertainty": "Prompt or task context was uncertain",
        "agent_execution_started": "Agent execution started",
        "wrong_tool_selection": "Agent selected incorrect tool",
        "irrelevant_tool_output": "Tool returned irrelevant data",
        "tool_returned_evidence": "Tool returned evidence",
        "evidence_not_integrated": "Agent ignored weak or retrieved evidence",
        "missing_evidence": "Evidence was missing",
        "hallucinated_answer": "Final answer hallucinated",
        "execution_loop": "Execution entered a loop",
        "redundant_tool_calls": "Agent repeated identical tool calls",
        "efficiency_loss": "Execution efficiency declined",
        "tool_failure": "Tool failed during execution",
        "retry_or_timeout": "Agent retried or timed out",
        "incomplete_execution": "Execution became incomplete",
        "weak_evidence": "Evidence was weak",
        "overconfident_language": "Agent used overconfident language",
        "trust_miscalibration": "Trust calibration failed",
        "unsupported_claims": "Agent made unsupported claims",
        "tool_call_without_output": "Tool call had no captured output",
        "low_evaluation_confidence": "Evaluation confidence declined",
        "tool_execution": "Tool execution occurred",
        "unclassified_failure": "Unclassified failure occurred",
        "reduced_trust": "Trust score declined",
    }
    return labels.get(node, _human_dimension(node))


def _normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _text_overlap(source: str, target: str) -> bool:
    source_terms = {
        term
        for term in _normalize_text(source).split()
        if len(term) > 3 and not term.isdigit()
    }
    target_terms = {
        term
        for term in _normalize_text(target).split()
        if len(term) > 3 and not term.isdigit()
    }
    if not source_terms or not target_terms:
        return False
    overlap = source_terms & target_terms
    required_overlap = 1 if len(source_terms) <= 3 else 2
    return len(overlap) >= required_overlap


def _human_dimension(name: str) -> str:
    return name.replace("_", " ").capitalize()


def _coerce_severity(value: Any) -> FailureSeverity:
    if value in {"low", "medium", "high"}:
        return value
    return "medium"


def _coerce_evidence_level(value: Any) -> EvidenceLevel:
    if value in {"response_only", "trace_available", "fully_instrumented"}:
        return value
    return "response_only"


def _coerce_deployment_recommendation(value: Any) -> DeploymentRecommendation:
    if value in {
        "safe_to_deploy",
        "review_recommended",
        "unsafe_for_production",
    }:
        return value
    return "review_recommended"


def _coerce_root_cause(value: Any) -> RootCause | None:
    if not isinstance(value, dict):
        return None
    return RootCause(
        description=str(value.get("description", "")),
        impact=str(value.get("impact", "")),
        trust_penalty=int(value.get("trust_penalty", 0) or 0),
        recommended_fix=str(value.get("recommended_fix", "")),
    )


def _coerce_certification_level(value: Any) -> CertificationLevel:
    if value in {"none", "bronze", "silver", "gold", "platinum"}:
        return value
    return "none"


def _badge_color(level: CertificationLevel) -> str:
    return {
        "none": "lightgrey",
        "bronze": "cd7f32",
        "silver": "c0c0c0",
        "gold": "gold",
        "platinum": "blueviolet",
    }[level]


def _coerce_tool_call(value: Any) -> ToolCall:
    if isinstance(value, ToolCall):
        return value
    if isinstance(value, dict):
        return ToolCall(
            tool=str(value.get("tool", value.get("name", "tool"))),
            args=dict(value.get("args", {}))
            if isinstance(value.get("args", {}), dict)
            else {"args": value.get("args")},
            id=value.get("id") or value.get("call_id"),
            timestamp=value.get("timestamp"),
        )
    return ToolCall(tool=str(value))


def _coerce_tool_output(value: Any) -> ToolOutput:
    if isinstance(value, ToolOutput):
        return value
    if isinstance(value, dict):
        return ToolOutput(
            tool=str(value.get("tool", value.get("name", "tool"))),
            output=value.get("output", value.get("result", "")),
            call_id=value.get("call_id") or value.get("id"),
            error=value.get("error"),
            timestamp=value.get("timestamp"),
        )
    return ToolOutput(tool="tool", output=value)


def _coerce_metrics(value: dict[str, Any] | RuntimeMetrics | None) -> RuntimeMetrics:
    if isinstance(value, RuntimeMetrics):
        return value
    if isinstance(value, dict):
        errors = value.get("errors", [])
        if isinstance(errors, str):
            errors = [errors]
        return RuntimeMetrics(
            latency=value.get("latency"),
            token_usage=dict(value.get("token_usage", {}))
            if isinstance(value.get("token_usage", {}), dict)
            else {},
            retries=int(value.get("retries", 0) or 0),
            errors=[str(error) for error in errors],
        )
    return RuntimeMetrics()
