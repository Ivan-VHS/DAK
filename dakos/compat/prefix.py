"""Safe, isolated Windows-prefix directory layout for DAKOS tooling."""
from __future__ import annotations

import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "dakos.windows-prefix.v1"
_ARCHITECTURES = {"x86", "x86_64", "aarch64"}
_PREFIX_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
_LAYOUT = (
    "drive_c/windows/system32",
    "drive_c/windows/syswow64",
    "drive_c/users/user/AppData/Local",
    "drive_c/users/user/Documents",
    "drive_c/users/user/Saved Games",
    "dosdevices",
    "registry",
    "logs",
    "cache/shaders",
    "snapshots",
)


class PrefixError(ValueError):
    """Raised when a prefix path or manifest is unsafe or invalid."""


def _prefix_path(base: str | Path, name: str) -> tuple[Path, Path]:
    if not isinstance(name, str) or not _PREFIX_NAME.fullmatch(name) or name in {".", ".."}:
        raise PrefixError("prefix name must be a simple 1..64 character identifier")
    root = Path(base).expanduser()
    try:
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink() or not root.is_dir():
            raise PrefixError("prefix store must be a real directory, not a symbolic link")
        root = root.resolve(strict=True)
    except OSError as error:
        raise PrefixError(f"cannot prepare prefix store: {error}") from error
    target = root / name
    if target.parent != root:
        raise PrefixError("prefix path escapes the selected store")
    return root, target


def create_prefix(base: str | Path, name: str, *, architecture: str = "x86_64") -> dict[str, Any]:
    """Create a fresh prefix skeleton; no Windows DLLs or runtimes are installed."""
    if architecture not in _ARCHITECTURES:
        raise PrefixError(f"architecture must be one of {sorted(_ARCHITECTURES)}")
    _root, target = _prefix_path(base, name)
    if target.exists() or target.is_symlink():
        raise PrefixError(f"prefix already exists: {target}")

    created_target = False
    try:
        target.mkdir()
        created_target = True
        for relative in _LAYOUT:
            (target / relative).mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema": SCHEMA,
            "name": name,
            "architecture": architecture,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "layout": list(_LAYOUT),
            "runtime_state": "metadata_only",
            "windows_api_available": False,
            "execution_enabled": False,
            "copy_on_write_base": None,
            "runtime_components": [],
        }
        temp_manifest = target / ".prefix.json.tmp"
        with temp_manifest.open("x", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        temp_manifest.replace(target / "prefix.json")
        return manifest | {"path": str(target)}
    except Exception:
        if created_target and target.exists() and target.is_dir() and not target.is_symlink():
            shutil.rmtree(target, ignore_errors=True)
        raise


def read_prefix(path: str | Path) -> dict[str, Any]:
    candidate = Path(path).expanduser()
    if candidate.is_symlink() or not candidate.is_dir():
        raise PrefixError("prefix must be an existing real directory")
    root = candidate.resolve(strict=True)
    manifest_path = root / "prefix.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise PrefixError("prefix.json is missing or is a symbolic link")
    try:
        if manifest_path.stat().st_size > 64 * 1024:
            raise PrefixError("prefix manifest exceeds 64 KiB")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PrefixError(f"cannot read prefix manifest: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise PrefixError("unsupported or malformed prefix manifest")
    if manifest.get("name") != root.name or manifest.get("architecture") not in _ARCHITECTURES:
        raise PrefixError("prefix manifest identity or architecture is invalid")
    for relative in _LAYOUT:
        current = root
        for part in Path(relative).parts:
            current = current / part
            if current.is_symlink():
                raise PrefixError(f"prefix layout contains a symbolic link: {relative}")
        if not current.is_dir():
            raise PrefixError(f"prefix directory is missing: {relative}")
    return manifest | {"path": str(root)}
