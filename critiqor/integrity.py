"""Evidence privacy, integrity, and validation primitives."""

from __future__ import annotations

import hashlib
import hmac
import base64
import json
import os
import re
from typing import Any, Iterable, Iterator

EVIDENCE_SCHEMA_VERSION = "critiqor.evidence.v2"
DIAGNOSIS_SCHEMA_VERSION = "critiqor.diagnosis.v2"
GENESIS_HASH = "0" * 64
REDACTED = "[REDACTED]"
MAX_STRING_LENGTH = 32_768

_SENSITIVE_KEY = re.compile(
    r"(?:authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|"
    r"client[_-]?secret|password|passwd|private[_-]?key|cookie|session[_-]?token)",
    re.IGNORECASE,
)
_SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{12,}\b"),
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def redact(value: Any, *, key: str = "", depth: int = 0) -> tuple[Any, int, int]:
    """Return a bounded, secret-redacted JSON value and redaction/truncation counts."""

    if _SENSITIVE_KEY.search(key):
        return REDACTED, 1, 0
    if depth > 12:
        return "[DEPTH_LIMIT]", 0, 1
    if value is None or isinstance(value, (bool, int, float)):
        return value, 0, 0
    if isinstance(value, str):
        redactions = 0
        result = value
        for pattern in _SECRET_VALUE_PATTERNS:
            result, count = pattern.subn(REDACTED, result)
            redactions += count
        if len(result) > MAX_STRING_LENGTH:
            return result[:MAX_STRING_LENGTH] + "[TRUNCATED]", redactions, 1
        return result, redactions, 0
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        redactions = truncations = 0
        for raw_key, item in value.items():
            item_key = str(raw_key)
            cleaned, redacted, truncated = redact(item, key=item_key, depth=depth + 1)
            result[item_key] = cleaned
            redactions += redacted
            truncations += truncated
        return result, redactions, truncations
    if isinstance(value, (list, tuple)):
        result = []
        redactions = truncations = 0
        for item in value:
            cleaned, redacted, truncated = redact(item, depth=depth + 1)
            result.append(cleaned)
            redactions += redacted
            truncations += truncated
        return result, redactions, truncations
    return redact(str(value), key=key, depth=depth + 1)


def seal_event(event: dict[str, Any], sequence_id: int, previous_hash: str) -> dict[str, Any]:
    cleaned, redactions, truncations = redact(event)
    payload = dict(cleaned)
    for field in ("sequence_id", "previous_hash", "event_hash"):
        payload.pop(field, None)
    payload["sequence_id"] = sequence_id
    payload["previous_hash"] = previous_hash
    if not isinstance(payload.get("privacy"), dict):
        payload["privacy"] = {}
    existing_redactions = int(payload["privacy"].get("redaction_count", 0) or 0)
    existing_truncations = int(payload["privacy"].get("truncation_count", 0) or 0)
    payload["privacy"].update(
        {
            "redaction_count": existing_redactions + redactions,
            "truncation_count": existing_truncations + truncations,
        }
    )
    digest_input = {key: value for key, value in payload.items() if key != "event_hash"}
    payload["event_hash"] = hashlib.sha256(canonical_json(digest_input)).hexdigest()
    return payload


def seal_events_iter(events: Iterable[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Seal events lazily so large traces do not require a second full copy."""

    previous_hash = GENESIS_HASH
    for sequence_id, event in enumerate(events, start=1):
        item = seal_event(dict(event), sequence_id, previous_hash)
        yield item
        previous_hash = item["event_hash"]


def seal_events(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return list(seal_events_iter(events))


def verify_events(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    previous_hash = GENESIS_HASH
    errors: list[str] = []
    count = redactions = truncations = 0
    for expected_sequence, raw_event in enumerate(events, start=1):
        count = expected_sequence
        event = dict(raw_event)
        if event.get("sequence_id") != expected_sequence:
            errors.append(
                f"event {expected_sequence}: sequence_id is {event.get('sequence_id')!r}"
            )
        if event.get("previous_hash") != previous_hash:
            errors.append(f"event {expected_sequence}: previous_hash mismatch")
        supplied_hash = event.pop("event_hash", None)
        calculated_hash = hashlib.sha256(canonical_json(event)).hexdigest()
        if not hmac.compare_digest(str(supplied_hash or ""), calculated_hash):
            errors.append(f"event {expected_sequence}: event_hash mismatch")
        previous_hash = str(supplied_hash or "")
        privacy = event.get("privacy") if isinstance(event.get("privacy"), dict) else {}
        redactions += int(privacy.get("redaction_count", 0) or 0)
        truncations += int(privacy.get("truncation_count", 0) or 0)
    return {
        "valid": not errors,
        "status": "verified" if not errors else "tampered",
        "event_count": count,
        "final_event_hash": previous_hash,
        "redaction_count": redactions,
        "truncation_count": truncations,
        "errors": errors,
    }


def evidence_digest(events: Iterable[dict[str, Any]]) -> str:
    return hashlib.sha256(canonical_json(list(events))).hexdigest()


def object_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def sign_manifest(manifest: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    private_key = os.environ.get("CRITIQOR_SIGNING_PRIVATE_KEY")
    signing_key = key if key is not None else os.environ.get("CRITIQOR_SIGNING_KEY")
    result = dict(manifest)
    result.pop("signature", None)
    if private_key and key is None:
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

            signer = Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_key))
            signature = signer.sign(canonical_json(result))
            result["signature"] = {
                "algorithm": "ed25519",
                "value": base64.b64encode(signature).decode("ascii"),
            }
            return result
        except (ImportError, ValueError) as exc:
            raise ValueError("CRITIQOR_SIGNING_PRIVATE_KEY is invalid") from exc
    if not signing_key:
        result["signature"] = {"algorithm": "none", "status": "unsigned"}
        return result
    signature = hmac.new(
        signing_key.encode("utf-8"), canonical_json(result), hashlib.sha256
    ).hexdigest()
    result["signature"] = {"algorithm": "hmac-sha256", "value": signature}
    return result


def verify_manifest(manifest: dict[str, Any], key: str | None = None) -> dict[str, Any]:
    signature = manifest.get("signature")
    if isinstance(signature, dict) and signature.get("algorithm") == "ed25519":
        public_key = os.environ.get("CRITIQOR_SIGNING_PUBLIC_KEY")
        if not public_key:
            return {
                "valid": False,
                "status": "unverifiable",
                "errors": ["CRITIQOR_SIGNING_PUBLIC_KEY is not configured"],
            }
        unsigned = dict(manifest)
        unsigned.pop("signature", None)
        try:
            from cryptography.exceptions import InvalidSignature
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

            verifier = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key))
            verifier.verify(base64.b64decode(str(signature.get("value") or "")), canonical_json(unsigned))
        except (ImportError, ValueError, InvalidSignature):
            return {
                "valid": False,
                "status": "tampered",
                "errors": ["manifest Ed25519 signature mismatch"],
            }
        return {"valid": True, "status": "verified", "errors": []}
    if not isinstance(signature, dict) or signature.get("algorithm") != "hmac-sha256":
        return {"valid": False, "status": "unsigned", "errors": ["manifest is not signed"]}
    supplied = str(signature.get("value") or "")
    unsigned = dict(manifest)
    unsigned.pop("signature", None)
    signing_key = key if key is not None else os.environ.get("CRITIQOR_SIGNING_KEY")
    if not signing_key:
        return {
            "valid": False,
            "status": "unverifiable",
            "errors": ["CRITIQOR_SIGNING_KEY is not configured"],
        }
    expected = hmac.new(
        signing_key.encode("utf-8"), canonical_json(unsigned), hashlib.sha256
    ).hexdigest()
    valid = hmac.compare_digest(supplied, expected)
    return {
        "valid": valid,
        "status": "verified" if valid else "tampered",
        "errors": [] if valid else ["manifest signature mismatch"],
    }


def generate_ed25519_keypair() -> dict[str, str]:
    """Generate raw base64 Ed25519 keys for CI secret configuration."""

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    private = Ed25519PrivateKey.generate()
    public = private.public_key()
    return {
        "private_key": base64.b64encode(
            private.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
        ).decode("ascii"),
        "public_key": base64.b64encode(
            public.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
        ).decode("ascii"),
    }
