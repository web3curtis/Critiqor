#!/usr/bin/env python3
"""Fail a release when its wheel or sdist contains private paths or secrets."""

from __future__ import annotations

import argparse
import re
import tarfile
import zipfile
from pathlib import Path


TEXT_SUFFIXES = {
    ".cfg", ".cjs", ".css", ".html", ".ini", ".js", ".json", ".jsx",
    ".md", ".mjs", ".py", ".toml", ".ts", ".tsx", ".txt", ".xml", ".yaml", ".yml",
}
FORBIDDEN_NAMES = re.compile(r"(?:^|/)(?:\.env(?:\..*)?|id_(?:rsa|dsa|ecdsa|ed25519)|.*\.(?:key|pem|p12))$", re.I)
PATTERNS = {
    "macOS home path": re.compile(rb"/Users/(?!user(?:name)?/)[^/\s]+/"),
    "Linux home path": re.compile(rb"/home/(?!user(?:name)?/)[^/\s]+/"),
    "Windows home path": re.compile(rb"[A-Z]:[\\/]Users[\\/](?!user(?:name)?[\\/])", re.I),
    "macOS temporary path": re.compile(rb"/(?:private/)?var/folders/[A-Za-z0-9_/-]+"),
    "OpenAI-style secret": re.compile(rb"\bsk-(?!image(?:-|\b))[A-Za-z0-9_-]{20,}\b"),
    "GitHub token": re.compile(rb"\b(?:gh[pousr]|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "AWS access key": re.compile(rb"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "Slack token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    "private key": re.compile(rb"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY"),
    "bearer credential": re.compile(rb"Authorization:\s*Bearer\s+[A-Za-z0-9._~+/-]{20,}", re.I),
}


def members(path: Path):
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if not info.is_dir():
                    yield info.filename, archive.read(info)
        return
    with tarfile.open(path, "r:*") as archive:
        for info in archive.getmembers():
            if info.isfile():
                source = archive.extractfile(info)
                if source is not None:
                    yield info.name, source.read()


def audit(path: Path) -> list[str]:
    findings: list[str] = []
    for name, data in members(path):
        if FORBIDDEN_NAMES.search(name):
            findings.append(f"forbidden credential file: {name}")
        if Path(name).suffix.lower() not in TEXT_SUFFIXES:
            continue
        for label, pattern in PATTERNS.items():
            if pattern.search(data):
                findings.append(f"{label}: {name}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()
    failed = False
    for artifact in args.artifacts:
        findings = audit(artifact)
        if findings:
            failed = True
            print(f"FAIL {artifact.name}")
            for finding in findings:
                print(f"  {finding}")
        else:
            print(f"PASS {artifact.name}: no private paths or credential signatures found")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
