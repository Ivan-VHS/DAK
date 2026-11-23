#!/usr/bin/env python3
"""Validate the Ivan-VHS 1,000-program ownership manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXPECTED_PROJECTS: dict[str, tuple[str, tuple[tuple[int, int], ...]]] = {
    "pytyliki": ("Ivan-VHS/Pytyliki", ((1, 120), (171, 250))),
    "reaper": ("Ivan-VHS/Reaper", ((251, 500),)),
    "oplague": ("Ivan-VHS/OPlague", ((501, 700),)),
    "ventusample": ("Ivan-VHS/VentuSample", ((121, 170), (701, 1000))),
}


def validate_manifest(data: Any) -> list[str]:
    """Return validation errors; an empty list means the allocation is valid."""
    if not isinstance(data, dict):
        return ["manifest root must be a JSON object"]

    errors: list[str] = []
    expected_top_level = {
        "schema_version": "1.0.0",
        "owner": "Ivan-VHS",
        "catalogue_size": 1000,
        "integration_host": "DuckOS",
    }
    for key, expected in expected_top_level.items():
        if data.get(key) != expected:
            errors.append(f"{key}: expected {expected!r}, got {data.get(key)!r}")

    projects = data.get("projects")
    if not isinstance(projects, list):
        return errors + ["projects must be an array"]

    seen_projects: set[str] = set()
    seen_repositories: set[str] = set()
    seen_ids: dict[int, str] = {}
    duckos_found = False

    for project in projects:
        if not isinstance(project, dict):
            errors.append("each project entry must be an object")
            continue

        project_id = project.get("id")
        repository = project.get("repository")
        ranges = project.get("catalogue_ranges")
        declared_count = project.get("entry_count")

        if not isinstance(project_id, str) or not project_id:
            errors.append("each project must have a non-empty id")
            continue
        if project_id in seen_projects:
            errors.append(f"duplicate project id: {project_id}")
        seen_projects.add(project_id)

        if not isinstance(repository, str) or not repository.startswith("Ivan-VHS/"):
            errors.append(f"{project_id}: repository must use the Ivan-VHS/ prefix")
        elif repository in seen_repositories:
            errors.append(f"duplicate repository assignment: {repository}")
        else:
            seen_repositories.add(repository)

        if not isinstance(ranges, list):
            errors.append(f"{project_id}: catalogue_ranges must be an array")
            ranges = []

        normalized: list[tuple[int, int]] = []
        project_count = 0
        for item in ranges:
            if (
                not isinstance(item, list)
                or len(item) != 2
                or type(item[0]) is not int
                or type(item[1]) is not int
            ):
                errors.append(f"{project_id}: each range must contain two integer bounds")
                continue

            start, end = item
            if start < 1 or end > 1000 or start > end:
                errors.append(f"{project_id}: invalid catalogue range {start}-{end}")
                continue

            normalized.append((start, end))
            project_count += end - start + 1
            for catalogue_id in range(start, end + 1):
                previous = seen_ids.get(catalogue_id)
                if previous is not None:
                    errors.append(
                        f"catalogue ID {catalogue_id} assigned to both {previous} and {project_id}"
                    )
                else:
                    seen_ids[catalogue_id] = project_id

        if type(declared_count) is not int or declared_count != project_count:
            errors.append(
                f"{project_id}: entry_count should be {project_count}, got {declared_count!r}"
            )

        if project_id in EXPECTED_PROJECTS:
            expected_repository, expected_ranges = EXPECTED_PROJECTS[project_id]
            if repository != expected_repository:
                errors.append(
                    f"{project_id}: expected repository {expected_repository}, got {repository!r}"
                )
            if tuple(normalized) != expected_ranges:
                errors.append(
                    f"{project_id}: expected ranges {expected_ranges}, got {tuple(normalized)}"
                )
        elif project_id == "duckos":
            duckos_found = True
            if repository != "Ivan-VHS/DuckOS":
                errors.append("duckos: repository must be Ivan-VHS/DuckOS")
            if normalized or project_count != 0 or declared_count != 0:
                errors.append("duckos: integration host must not own catalogue IDs")
        else:
            errors.append(f"unexpected project id: {project_id}")

    for project_id in EXPECTED_PROJECTS:
        if project_id not in seen_projects:
            errors.append(f"missing catalogue owner: {project_id}")
    if not duckos_found:
        errors.append("missing integration host: duckos")

    missing_ids = sorted(set(range(1, 1001)) - set(seen_ids))
    if missing_ids:
        preview = ", ".join(str(item) for item in missing_ids[:12])
        suffix = " ..." if len(missing_ids) > 12 else ""
        errors.append(f"unassigned catalogue IDs: {preview}{suffix}")

    rules = data.get("shared_rules")
    if not isinstance(rules, list) or not rules or not all(
        isinstance(rule, str) and rule.strip() for rule in rules
    ):
        errors.append("shared_rules must be a non-empty array of non-empty strings")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    default_path = (
        Path(__file__).resolve().parents[1]
        / "manifests"
        / "ivan-vhs-program-adoption.v1.json"
    )
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=default_path,
        help="path to the adoption manifest",
    )
    args = parser.parse_args()

    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read manifest: {exc}", file=sys.stderr)
        return 2

    errors = validate_manifest(data)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("Valid adoption manifest: 1,000 IDs assigned exactly once.")
    print("Ownership counts: Pytyliki 200, Reaper 250, OPlague 200, VentuSample 350.")
    print("DuckOS is the integration host and owns no catalogue IDs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
