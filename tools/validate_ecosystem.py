#!/usr/bin/env python3
"""Validate DuckOS project ownership and immutable submodule references."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "ecosystem" / "registry.v1.json"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def validate_registry(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        data: Any = json.loads((root / "ecosystem" / "registry.v1.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read registry: {exc}"]

    if data.get("schema") != "duckos.ecosystem.v1":
        errors.append("unsupported registry schema")
    if not isinstance(data.get("system"), dict) or data["system"].get("id") != "duckos":
        errors.append("system.id must be duckos")

    try:
        gitmodules = (root / ".gitmodules").read_text(encoding="utf-8")
    except OSError as exc:
        gitmodules = ""
        errors.append(f"cannot read .gitmodules: {exc}")

    projects = data.get("projects")
    if not isinstance(projects, list):
        errors.append("projects must be an array")
        projects = []
    ids: set[str] = set()
    for item in projects:
        if not isinstance(item, dict):
            errors.append("project entries must be objects")
            continue
        ident = item.get("id")
        if not isinstance(ident, str) or not ident:
            errors.append("project id is missing")
            continue
        if ident in ids:
            errors.append(f"duplicate project id: {ident}")
        ids.add(ident)
        if item.get("status") == "integrated_submodule":
            path, commit = item.get("path"), item.get("commit")
            if not isinstance(path, str) or not path.startswith("ecosystem/") or path not in gitmodules:
                errors.append(f"{ident}: invalid or unregistered submodule path")
            if not isinstance(commit, str) or not COMMIT_RE.fullmatch(commit):
                errors.append(f"{ident}: commit must be an immutable 40-character SHA")

    required = {"duckos", "pytyliki", "reaper", "oplague", "ventusample", "beelzebul"}
    missing = required - ids
    if missing:
        errors.append("missing projects: " + ", ".join(sorted(missing)))

    interfaces = data.get("interfaces")
    if not isinstance(interfaces, list):
        errors.append("interfaces must be an array")
        interfaces = []
    interface_ids = [entry.get("id") for entry in interfaces if isinstance(entry, dict)]
    if len(interface_ids) != len(set(interface_ids)):
        errors.append("interface IDs must be unique")
    if not isinstance(data.get("policies"), list) or not data["policies"]:
        errors.append("policies must be a non-empty array")
    return errors


def main() -> int:
    errors = validate_registry()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("DuckOS ecosystem registry: valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
