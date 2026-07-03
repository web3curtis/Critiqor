"""Public client for the private Critiqor diagnosis backend.

This module intentionally contains only transport and schema handling. Diagnosis,
scoring, benchmarking, root-cause analysis, and leaderboard logic live behind the
private Critiqor backend and are not distributed in the public PyPI package.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .schemas import DiagnosisResult, EvidenceSubmission

DEFAULT_BACKEND_URL = "https://api.critiqor.ai/v1/diagnoses"


class BackendConfigurationError(RuntimeError):
    """Raised when the public client cannot reach a configured backend."""


class BackendResponseError(RuntimeError):
    """Raised when the backend response is malformed or rejected."""


@dataclass(frozen=True)
class BackendConfig:
    """Connection details for the private diagnosis backend."""

    url: str
    api_key: str | None = None
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "BackendConfig":
        return cls(
            url=os.environ.get("CRITIQOR_BACKEND_URL", DEFAULT_BACKEND_URL),
            api_key=os.environ.get("CRITIQOR_API_KEY"),
            timeout_seconds=float(os.environ.get("CRITIQOR_BACKEND_TIMEOUT", "30")),
        )


def submit_evidence(submission: EvidenceSubmission, config: BackendConfig | None = None) -> DiagnosisResult:
    """Submit runtime evidence to the private backend and return diagnosis JSON."""

    cfg = config or BackendConfig.from_env()
    body = json.dumps(submission.to_dict(), sort_keys=True).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "accept": "application/json",
        "user-agent": "critiqor-public-client",
    }
    if cfg.api_key:
        headers["authorization"] = f"Bearer {cfg.api_key}"

    request = Request(cfg.url, data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=cfg.timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
        raise BackendResponseError(f"backend returned HTTP {exc.code}: {message[:240]}") from exc
    except (OSError, URLError) as exc:
        raise BackendConfigurationError(f"could not reach Critiqor backend at {cfg.url}: {exc}") from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise BackendResponseError("backend returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise BackendResponseError("backend returned a non-object diagnosis payload")

    diagnosis = payload.get("diagnosis") if isinstance(payload.get("diagnosis"), dict) else payload
    run_id = str(diagnosis.get("run_id") or payload.get("run_id") or submission.run_id)
    diagnosis.setdefault("run_id", run_id)
    return DiagnosisResult(run_id=run_id, payload=diagnosis)


def backend_configuration_hint() -> str:
    return (
        "Set CRITIQOR_BACKEND_URL to your Critiqor diagnosis backend and "
        "CRITIQOR_API_KEY when authentication is required."
    )
