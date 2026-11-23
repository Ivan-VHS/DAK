#!/usr/bin/env python3
"""Validate and initialize DuckOS's pinned Ivan-VHS project submodules."""
from __future__ import annotations

import argparse
import configparser
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

SCHEMA = "duckos.repository-federation.v1"
EXPECTED_PROJECTS = {
    "pytyliki": ("Ivan-VHS/Pytyliki", "MIT"),
    "reaper": ("Ivan-VHS/Reaper", "Apache-2.0"),
    "oplague": ("Ivan-VHS/OPlague", "Apache-2.0"),
    "ventusample": ("Ivan-VHS/VentuSample", "Apache-2.0"),
}
PIN = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class FederationError(ValueError):
    """Invalid repository pin, checkout or federation contract."""


def _is_text(value: Any, limit: int = 4096) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= limit


def validate_manifest(data: Any) -> list[str]:
    """Return validation errors without requiring a Git checkout."""
    if not isinstance(data, dict):
        return ["repository registry must be a JSON object"]
    required = {
        "schema": SCHEMA, "version": 1, "owner": "Ivan-VHS",
        "integration_host": "DuckOS", "checkout_strategy": "git-submodules",
        "projects_root": "projects",
    }
    errors = [f"{key}: expected {value!r}, got {data.get(key)!r}"
              for key, value in required.items() if data.get(key) != value]
    projects = data.get("repositories")
    if not isinstance(projects, list) or len(projects) != len(EXPECTED_PROJECTS):
        return errors + [f"repositories must contain exactly {len(EXPECTED_PROJECTS)} projects"]

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    by_id: dict[str, Mapping[str, Any]] = {}
    for item in projects:
        if not isinstance(item, dict):
            errors.append("each repository entry must be an object")
            continue
        project_id = item.get("id")
        if not isinstance(project_id, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,31}", project_id):
            errors.append("repository id must be a lowercase identifier")
            continue
        if project_id in seen_ids:
            errors.append(f"duplicate repository id: {project_id}")
        seen_ids.add(project_id)
        by_id[project_id] = item
        expected = EXPECTED_PROJECTS.get(project_id)
        if expected is None:
            errors.append(f"unexpected repository id: {project_id}")
        else:
            if item.get("repository") != expected[0]:
                errors.append(f"{project_id}: repository must be {expected[0]}")
            if item.get("license") != expected[1]:
                errors.append(f"{project_id}: expected upstream license {expected[1]}")

        expected_path = f"projects/{project_id}"
        path = item.get("path")
        if path != expected_path:
            errors.append(f"{project_id}: path must be {expected_path}")
        if not isinstance(path, str) or path in seen_paths:
            errors.append(f"{project_id}: duplicate or invalid submodule path")
        else:
            seen_paths.add(path)
            parsed = PurePosixPath(path)
            if parsed.is_absolute() or ".." in parsed.parts or "\\" in path:
                errors.append(f"{project_id}: submodule path is not safe relative text")

        expected_url = f"https://github.com/{expected[0]}.git" if expected else ""
        if item.get("url") != expected_url:
            errors.append(f"{project_id}: clone URL must be the canonical HTTPS GitHub URL")
        if item.get("default_branch") != "main":
            errors.append(f"{project_id}: default_branch must be main")
        if not isinstance(item.get("pinned_commit"), str) or not PIN.fullmatch(item["pinned_commit"]):
            errors.append(f"{project_id}: pinned_commit must be a 40-character lowercase Git SHA")
        if item.get("license_file") != "LICENSE":
            errors.append(f"{project_id}: license_file must preserve upstream LICENSE")
        for field in ("domain", "responsibility", "runtime_boundary", "build_system"):
            if not _is_text(item.get(field)):
                errors.append(f"{project_id}: {field} must be non-empty text")
        modes = item.get("integration_mode")
        if not isinstance(modes, list) or not modes or not all(_is_text(value) for value in modes):
            errors.append(f"{project_id}: integration_mode must be a non-empty text array")
        for field in ("depends_on", "optional_dependencies"):
            values = item.get(field)
            if not isinstance(values, list) or not all(isinstance(x, str) for x in values):
                errors.append(f"{project_id}: {field} must be an array of repository IDs")
            elif len(set(values)) != len(values):
                errors.append(f"{project_id}: {field} contains duplicate IDs")
        expected_status = {
            "reaper": "native-workbench",
            "pytyliki": "native-app-launcher",
            "oplague": "native-app-launcher",
            "ventusample": "native-app-launcher",
        }[project_id]
        if item.get("integration_status") != expected_status:
            errors.append(f"{project_id}: integration_status must be {expected_status!r}")
        if item.get("auto_build") is not False or item.get("auto_execute") is not False:
            errors.append(f"{project_id}: automatic build and execution must remain disabled")

    missing = set(EXPECTED_PROJECTS) - seen_ids
    if missing:
        errors.append(f"missing repositories: {', '.join(sorted(missing))}")
    for project_id, item in by_id.items():
        for field in ("depends_on", "optional_dependencies"):
            dependencies = item.get(field, [])
            if not isinstance(dependencies, list):
                continue
            for dependency in dependencies:
                if dependency == project_id:
                    errors.append(f"{project_id}: a repository cannot depend on itself")
                elif dependency not in EXPECTED_PROJECTS:
                    errors.append(f"{project_id}: unknown dependency {dependency!r}")

    rules = data.get("shared_rules")
    if not isinstance(rules, list) or not rules or not all(_is_text(rule) for rule in rules):
        errors.append("shared_rules must be a non-empty array of non-empty strings")

    if len(seen_ids) == len(EXPECTED_PROJECTS):
        state: dict[str, int] = {}
        def visit(project_id: str) -> None:
            marker = state.get(project_id, 0)
            if marker == 1:
                errors.append(f"dependency cycle detected at {project_id}")
                return
            if marker == 2:
                return
            state[project_id] = 1
            item = by_id.get(project_id, {})
            required = item.get("depends_on", [])
            optional = item.get("optional_dependencies", [])
            dependencies = []
            if isinstance(required, list):
                dependencies.extend(required)
            if isinstance(optional, list):
                dependencies.extend(optional)
            for dependency in dependencies:
                if dependency in by_id:
                    visit(dependency)
            state[project_id] = 2
        for project_id in sorted(by_id):
            visit(project_id)
    return errors


def load_registry(root: Path) -> dict[str, Any]:
    path = root / "federation" / "repositories.v1.json"
    try:
        if path.stat().st_size > 2 * 1024 * 1024:
            raise FederationError("repository registry exceeds the 2 MiB limit")
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise FederationError(f"cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise FederationError(f"invalid JSON in {path}: {error}") from error
    errors = validate_manifest(data)
    if errors:
        raise FederationError("\n".join(errors))
    return data


def parse_gitmodules(content: str) -> dict[str, dict[str, str]]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str.lower
    try:
        parser.read_string(content)
    except configparser.Error as error:
        raise FederationError(f"invalid .gitmodules: {error}") from error
    result: dict[str, dict[str, str]] = {}
    for section in parser.sections():
        match = re.fullmatch(r'submodule "([^"]+)"', section)
        if not match:
            raise FederationError(f"unexpected .gitmodules section: {section}")
        path = match.group(1)
        if path in result:
            raise FederationError(f"duplicate .gitmodules entry: {path}")
        result[path] = {
            "path": parser.get(section, "path", fallback=""),
            "url": parser.get(section, "url", fallback=""),
            "branch": parser.get(section, "branch", fallback=""),
        }
    return result


def validate_gitmodules(root: Path, projects: Sequence[Mapping[str, Any]]) -> list[str]:
    try:
        found = parse_gitmodules((root / ".gitmodules").read_text(encoding="utf-8"))
    except OSError as error:
        return [f"cannot read .gitmodules: {error}"]
    except FederationError as error:
        return [str(error)]
    errors = []
    expected = {item["path"]: item for item in projects}
    if set(found) != set(expected):
        errors.append(".gitmodules entries do not exactly match the pinned repository registry")
    for project_path, project in expected.items():
        entry = found.get(project_path)
        if entry is None:
            errors.append(f"missing .gitmodules entry for {project_path}")
            continue
        if entry["path"] != project_path:
            errors.append(f"{project_path}: .gitmodules path does not match")
        if entry["url"] != project["url"]:
            errors.append(f"{project_path}: .gitmodules URL differs from the registry")
        if entry["branch"] not in ("", project["default_branch"]):
            errors.append(f"{project_path}: .gitmodules branch differs from the registry")
    return errors


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=300, check=False,
        )
    except FileNotFoundError as error:
        raise FederationError("Git is required to validate or initialize repository submodules") from error
    except subprocess.TimeoutExpired as error:
        raise FederationError(f"Git command timed out: {' '.join(args)}") from error
    if check and result.returncode:
        detail = (result.stderr or result.stdout or "unknown Git error").strip()
        raise FederationError(f"git {' '.join(args)} failed: {detail[:2000]}")
    return result


def validate_gitlinks(root: Path, projects: Sequence[Mapping[str, Any]]) -> list[str]:
    if _git(root, "rev-parse", "--show-toplevel", check=False).returncode:
        return ["DuckOS source directory is not a Git working tree"]
    errors = []
    for project in projects:
        result = _git(root, "ls-tree", "HEAD", project["path"], check=False)
        if result.returncode:
            errors.append(f"cannot inspect pinned Git entry for {project['path']}")
            continue
        fields = result.stdout.strip().split(None, 3)
        if len(fields) < 4:
            errors.append(f"missing submodule Git entry: {project['path']}")
            continue
        mode, object_type, sha, path = fields
        if mode != "160000" or object_type != "commit":
            errors.append(f"{project['path']} must be a Git submodule entry (mode 160000)")
        if sha != project["pinned_commit"]:
            errors.append(f"{project['path']} pin differs: registry={project['pinned_commit']} Git tree={sha}")
        if path != project["path"]:
            errors.append(f"unexpected Git tree path for {project['path']}")
    return errors


def _submodule_states(root: Path, projects: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result = _git(root, "submodule", "status", "--recursive", check=False)
    lines = result.stdout.splitlines() if result.returncode == 0 else []
    by_path: dict[str, tuple[str, str]] = {}
    for line in lines:
        if len(line) < 42:
            continue
        marker = line[0]
        parts = line[1:].split(None, 2)
        if len(parts) >= 2:
            by_path[parts[1]] = (marker, parts[0])
    states = []
    for project in projects:
        marker, actual = by_path.get(project["path"], ("-", ""))
        label = {" ": "ready", "-": "not_initialized", "+": "checkout_differs_from_pin",
                 "U": "merge_conflict"}.get(marker, "unknown")
        states.append({
            "id": project["id"], "path": project["path"],
            "repository": project["repository"],
            "expected_commit": project["pinned_commit"],
            "actual_commit": actual or None, "state": label,
        })
    return states


def status_report(root: Path, registry: Mapping[str, Any]) -> dict[str, Any]:
    result = _git(root, "submodule", "status", "--recursive", check=False)
    return {
        "schema": "duckos.repository-federation-status.v1",
        "root": str(root),
        "repositories": _submodule_states(root, registry["repositories"]),
        "recursive_submodule_status": result.stdout.splitlines(),
    }


def _refuse_dirty_submodules(root: Path, projects: Sequence[Mapping[str, Any]]) -> None:
    for project in projects:
        checkout = root / project["path"]
        if not checkout.exists():
            continue
        probe = _git(checkout, "rev-parse", "--show-toplevel", check=False)
        if probe.returncode or Path(probe.stdout.strip()).resolve() != checkout.resolve():
            continue
        dirty = _git(checkout, "status", "--porcelain", "--untracked-files=all", check=False)
        if dirty.stdout.strip():
            raise FederationError(
                f"{project['path']} has local changes. Commit or move them before syncing; "
                "no submodule was updated."
            )


def run_action(root: Path, action: str, *, jobs: int = 4) -> dict[str, Any]:
    root = root.expanduser().resolve()
    registry = load_registry(root)
    projects = registry["repositories"]
    errors = validate_gitmodules(root, projects) + validate_gitlinks(root, projects)
    if errors:
        raise FederationError("\n".join(errors))
    if action == "sync":
        if not 1 <= jobs <= 16:
            raise FederationError("jobs must be between 1 and 16")
        _refuse_dirty_submodules(root, projects)
        _git(root, "submodule", "sync", "--recursive")
        _git(root, "submodule", "update", "--init", "--recursive", "--jobs", str(jobs))
    report = status_report(root, registry)
    report["validated"] = True
    report["action"] = action
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "status", "sync"))
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="DuckOS checkout root")
    parser.add_argument("--jobs", type=int, default=4, help="parallel submodule jobs for sync (1..16)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        report = run_action(args.root, args.action, jobs=args.jobs)
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"DuckOS repository federation: {args.action}")
            for item in report["repositories"]:
                print(f"{item['state']:28} {item['id']:12} {item['actual_commit'] or 'not cloned'}")
            print("Pinned-source validation: passed")
        incomplete = any(item["state"] != "ready" for item in report["repositories"])
        return 1 if args.action == "status" and incomplete else 0
    except (FederationError, OSError, ValueError) as error:
        if args.json:
            print(json.dumps({"schema": "duckos.repository-federation-error.v1", "error": str(error)},
                             ensure_ascii=False, indent=2), file=sys.stderr)
        else:
            print(f"DuckOS repository federation: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
