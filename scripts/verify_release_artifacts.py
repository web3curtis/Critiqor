#!/usr/bin/env python3
"""Check that the built wheel and sdist contain the runnable Critiqor release."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path


REQUIRED_FILES = {
    "critiqor/__init__.py",
    "critiqor/cli.py",
    "critiqor/diagnosis/memory.py",
    "critiqor/webmcp_browser.py",
    "critiqor/clawhub/critiqor-openclaw/index.js",
    "critiqor/core_engine_dashboard/package.json",
    "critiqor/core_engine_dashboard/.output/server/index.mjs",
}


def wheel_contents(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()
                if not name.endswith("/")}


def sdist_contents(path: Path) -> dict[str, bytes]:
    with tarfile.open(path, "r:gz") as archive:
        result = {}
        for member in archive.getmembers():
            if member.isfile():
                stream = archive.extractfile(member)
                if stream:
                    result[member.name.partition("/")[2]] = stream.read()
        return result


def verify(wheel: Path, sdist: Path) -> list[str]:
    wheel_files = wheel_contents(wheel)
    sdist_files = sdist_contents(sdist)
    errors = []
    for label, files in (("wheel", wheel_files), ("sdist", sdist_files)):
        for name in sorted(REQUIRED_FILES - files.keys()):
            errors.append(f"{label} is missing {name}")
        if not any(name.startswith("critiqor/core_engine_dashboard/.output/public/")
                   for name in files):
            errors.append(f"{label} is missing dashboard public assets")
        if any(name.startswith("private_backend/") for name in files):
            errors.append(f"{label} contains private_backend")

    for name, content in wheel_files.items():
        if name.startswith("critiqor/") and name in sdist_files and content != sdist_files[name]:
            errors.append(f"wheel and sdist differ: {name}")

    metadata_name = next((name for name in wheel_files if name.endswith(".dist-info/METADATA")), None)
    entry_name = next((name for name in wheel_files if name.endswith(".dist-info/entry_points.txt")), None)
    metadata = wheel_files.get(metadata_name or "", b"")
    entries = wheel_files.get(entry_name or "", b"")
    if b"Requires-Dist: websocket-client>=1.8" not in metadata:
        errors.append("wheel is missing the WebMCP runtime dependency")
    if b"critiqor = critiqor.cli:main" not in entries:
        errors.append("wheel is missing the critiqor CLI entry point")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    parser.add_argument("sdist", type=Path)
    args = parser.parse_args()
    errors = verify(args.wheel, args.sdist)
    for error in errors:
        print(f"FAIL {error}")
    if not errors:
        print("PASS wheel and sdist include the runnable CLI, WebMCP module, and dashboard")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
