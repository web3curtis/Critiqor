"""Command-line interface for Critiqor workflow integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import check_policy, load_evaluations


def main(argv: list[str] | None = None) -> int:
    """Run the Critiqor CLI."""

    parser = argparse.ArgumentParser(prog="critiqor")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Run a deployment policy check.")
    check_parser.add_argument(
        "--evaluations",
        default="critiqor_evaluations.jsonl",
        help="Path to Critiqor JSONL evaluations.",
    )
    check_parser.add_argument("--agent-id", default=None, help="Optional agent id filter.")
    check_parser.add_argument("--policy", default=None, help="Path to policy JSON/YAML.")
    check_parser.add_argument(
        "--minimum-trust-score",
        type=int,
        default=None,
        help="Minimum trust score required to pass.",
    )
    check_parser.add_argument(
        "--maximum-hallucination-risk",
        type=int,
        default=None,
        help="Maximum allowed hallucination risk.",
    )

    args = parser.parse_args(argv)
    if args.command == "check":
        return _check(args)

    parser.print_help()
    return 0


def _check(args: argparse.Namespace) -> int:
    policy = _load_policy(args.policy)
    if args.minimum_trust_score is not None:
        policy["minimum_trust_score"] = args.minimum_trust_score
    if args.maximum_hallucination_risk is not None:
        policy["maximum_hallucination_risk"] = args.maximum_hallucination_risk

    evaluations = load_evaluations(args.evaluations, agent_id=args.agent_id, limit=1)
    if not evaluations:
        print("Deployment blocked")
        print("No Critiqor evaluations found.")
        return 1

    result = check_policy(evaluations[-1], policy)
    if result.passed:
        print("Deployment allowed")
    else:
        print("Deployment blocked")
    for message in result.messages:
        print(message)
    return 0 if result.passed else 1


def _load_policy(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    text = source.read_text(encoding="utf-8")
    if source.suffix.lower() == ".json":
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    return _parse_simple_yaml(text)


def _parse_simple_yaml(text: str) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        policy[key.strip()] = _parse_scalar(value.strip())
    return policy


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(value)
    except ValueError:
        return value


if __name__ == "__main__":
    raise SystemExit(main())
