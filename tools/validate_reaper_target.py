"""Validate DuckOS's versioned Reaper migration and exact source inventory."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


class MigrationContractError(ValueError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise MigrationContractError(f"cannot read {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise MigrationContractError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise MigrationContractError(f"{path} must contain a JSON object")
    return value


def _validate_shape(data: dict[str, Any]) -> None:
    if data.get("schema") != "duckos.reaper-migration.v1" or data.get("version") != 1:
        raise MigrationContractError("unsupported Reaper migration schema or version")
    if data.get("project") != "DuckOS":
        raise MigrationContractError("migration contract project must be DuckOS")

    dependency = data.get("reaper_dependency")
    if not isinstance(dependency, dict):
        raise MigrationContractError("reaper_dependency must be an object")
    pin = dependency.get("pinned_commit")
    if not isinstance(pin, str) or not re.fullmatch(r"[0-9a-f]{40}", pin):
        raise MigrationContractError("Reaper pinned_commit must be a 40-character lowercase Git SHA")
    if dependency.get("repository") != "Ivan-VHS/Reaper":
        raise MigrationContractError("unexpected Reaper repository")
    if dependency.get("submodule_path") != "projects/reaper":
        raise MigrationContractError("Reaper submodule path must remain projects/reaper")

    target = data.get("boot_target")
    if not isinstance(target, dict):
        raise MigrationContractError("boot_target must be an object")
    if target.get("decision_status") != "approved":
        if any(target.get(key) is not None for key in ("architecture", "boot_protocol", "kernel_abi")):
            raise MigrationContractError(
                "unapproved architecture, boot protocol or kernel ABI must remain unset"
            )
        if target.get("bootable_image") is not False:
            raise MigrationContractError("DuckOS cannot claim a bootable image before target approval")

    profiles = data.get("execution_profiles")
    profile = profiles.get("reaper_native_kernel") if isinstance(profiles, dict) else None
    if not isinstance(profile, dict):
        raise MigrationContractError("reaper_native_kernel execution profile is required")
    if profile.get("status") != "implemented" and profile.get("bootable") is True:
        raise MigrationContractError("an incomplete native kernel profile cannot claim bootability")
    if profile.get("freestanding") is False and profile.get("bootable") is True:
        raise MigrationContractError("a hosted runtime cannot claim a freestanding bootable kernel")

    paths: set[str] = set()
    for entry in data.get("source_inventory", []):
        if not isinstance(entry, dict):
            raise MigrationContractError("source_inventory entries must be objects")
        path = entry.get("path")
        if not isinstance(path, str) or not path.startswith("duckos/") or not path.endswith(".rpr"):
            raise MigrationContractError(f"invalid Reaper source inventory path: {path!r}")
        if path in paths:
            raise MigrationContractError(f"duplicate Reaper source inventory path: {path}")
        paths.add(path)

    gate_ids = [entry.get("id") for entry in data.get("gates", []) if isinstance(entry, dict)]
    if len(gate_ids) != len(set(gate_ids)):
        raise MigrationContractError("migration gate identifiers must be unique")


def _validate_repository(root: Path, data: dict[str, Any], *, verify_git: bool) -> None:
    expected = {entry["path"] for entry in data["source_inventory"]}
    actual = {
        path.relative_to(root).as_posix()
        for path in (root / "duckos").rglob("*.rpr")
        if path.is_file()
    }
    missing = sorted(expected - actual)
    unregistered = sorted(actual - expected)
    if missing or unregistered:
        parts = []
        if missing:
            parts.append("missing inventory files: " + ", ".join(missing))
        if unregistered:
            parts.append("unregistered Reaper sources: " + ", ".join(unregistered))
        raise MigrationContractError("; ".join(parts))

    federation = _read_json(root / "federation" / "repositories.v1.json")
    records = federation.get("repositories")
    if not isinstance(records, list):
        raise MigrationContractError("federation repository registry is malformed")
    reaper = next(
        (item for item in records if isinstance(item, dict) and item.get("id") == "reaper"),
        None,
    )
    if reaper is None:
        raise MigrationContractError("Reaper is missing from the repository federation registry")
    if reaper.get("pinned_commit") != data["reaper_dependency"]["pinned_commit"]:
        raise MigrationContractError(
            "migration manifest and federation registry disagree about the Reaper pin"
        )
    if reaper.get("path") != data["reaper_dependency"]["submodule_path"]:
        raise MigrationContractError("federation registry and migration manifest disagree about submodule path")

    if verify_git:
        command = ["git", "ls-tree", "HEAD", data["reaper_dependency"]["submodule_path"]]
        try:
            result = subprocess.run(
                command, cwd=root, capture_output=True, text=True, check=False, timeout=10
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise MigrationContractError(f"cannot verify Reaper gitlink: {error}") from error
        if result.returncode != 0:
            raise MigrationContractError("cannot inspect the DuckOS Git tree for the Reaper submodule")
        match = re.fullmatch(
            r"160000 commit ([0-9a-f]{40})\tprojects/reaper\s*",
            result.stdout,
        )
        if match is None:
            raise MigrationContractError("projects/reaper is not an exact Git submodule entry")
        if match.group(1) != data["reaper_dependency"]["pinned_commit"]:
            raise MigrationContractError("Reaper submodule gitlink does not match the declared exact pin")


def validate(root: str | Path, *, verify_git: bool = True) -> dict[str, Any]:
    repository = Path(root).expanduser().resolve()
    data = _read_json(repository / "duckos" / "reaper-migration.v1.json")
    schema = _read_json(repository / "schemas" / "reaper-migration.v1.schema.json")
    _validate_shape(data)
    try:
        import jsonschema
    except ImportError:
        # The explicit invariant checks below remain dependency-free; CI and
        # normal development environments also validate the published schema.
        pass
    else:
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as error:
            raise MigrationContractError(f"migration manifest does not satisfy its JSON Schema: {error.message}") from error
        except jsonschema.SchemaError as error:
            raise MigrationContractError(f"migration JSON Schema is invalid: {error.message}") from error
    _validate_repository(repository, data, verify_git=verify_git)
    return {
        "schema": "duckos.reaper-migration-validation.v1",
        "ok": True,
        "repository": str(repository),
        "reaper_commit": data["reaper_dependency"]["pinned_commit"],
        "reaper_sources": len(data["source_inventory"]),
        "migration_gates": len(data["gates"]),
        "bootable_image": data["boot_target"]["bootable_image"],
        "native_kernel_status": data["execution_profiles"]["reaper_native_kernel"]["status"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check DuckOS/Reaper migration manifest, submodule pin and exact .rpr inventory."
    )
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--allow-no-git", action="store_true",
        help="validate files and federation metadata without checking the Git submodule gitlink",
    )
    args = parser.parse_args(argv)
    try:
        report = validate(args.root, verify_git=not args.allow_no_git)
    except (MigrationContractError, OSError, ValueError) as error:
        print(f"DuckOS Reaper migration contract: FAIL: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
