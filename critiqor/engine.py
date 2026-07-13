"""Stable public contract for Critiqor diagnosis implementations."""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Protocol, runtime_checkable

from .backend import BackendConfig, submit_evidence
from .schemas import DiagnosisResult, EvidenceSubmission

ENGINE_ENTRY_POINT_GROUP = "critiqor.diagnosis_engines"


@runtime_checkable
class DiagnosisEngine(Protocol):
    """Generate a diagnosis from normalized evidence without exposing its algorithm."""

    def generate(self, submission: EvidenceSubmission) -> DiagnosisResult:
        ...


class HostedDiagnosisEngine:
    """Public transport adapter for Critiqor's hosted private engine."""

    def __init__(self, config: BackendConfig | None = None) -> None:
        self.config = config

    def generate(self, submission: EvidenceSubmission) -> DiagnosisResult:
        return submit_evidence(submission, self.config)


def resolve_diagnosis_engine() -> DiagnosisEngine:
    """Load an installed private plugin, otherwise use the hosted engine."""

    candidates = entry_points().select(group=ENGINE_ENTRY_POINT_GROUP)
    for candidate in sorted(candidates, key=lambda item: item.name):
        implementation = candidate.load()
        engine = implementation() if isinstance(implementation, type) else implementation
        if isinstance(engine, DiagnosisEngine):
            return engine
        raise TypeError(f"Diagnosis engine entry point {candidate.name!r} does not satisfy DiagnosisEngine")
    return HostedDiagnosisEngine()
