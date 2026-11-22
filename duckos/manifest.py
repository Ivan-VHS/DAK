"""Validation for DuckOS system-build manifests and local component artifacts."""
from __future__ import annotations

import hashlib
from pathlib import Path, PurePosixPath
import re
from typing import Any

SCHEMA = "duckos.system-manifest.v1"
MAX_COMPONENTS = 64
MAX_COMPONENT_BYTES = 8 * 1024 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ARCHITECTURES = {"x86_64", "aarch64", "riscv64", "i686"}
_REQUIRED = {"bootloader", "kernel", "initramfs", "rootfs"}
_TOP_FIELDS = {"schema", "name", "version", "architecture", "kernel_abi", "components"}
_COMPONENT_FIELDS = {"name", "path", "size_bytes", "sha256"}


class ManifestError(ValueError):
    """Raised when a system manifest or a referenced component is invalid."""


def _relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise ManifestError("component path must be non-empty relative text")
    if "\\" in value or value.startswith("/") or ":" in value:
        raise ManifestError(f"unsafe component path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ManifestError(f"unsafe component path: {value!r}")
    if str(path) != value or any(ord(char) < 32 for char in value):
        raise ManifestError(f"non-canonical component path: {value!r}")
    return value


def _hash_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                if size > MAX_COMPONENT_BYTES:
                    raise ManifestError(f"{path.name} exceeds the 8 GiB component limit")
                digest.update(chunk)
    except OSError as error:
        raise ManifestError(f"cannot read component {path.name}: {error}") from error
    return size, digest.hexdigest()


def validate_manifest(manifest: Any, root: str | Path, *, verify_files: bool = True) -> dict[str, Any]:
    if not isinstance(manifest, dict) or set(manifest) != _TOP_FIELDS:
        raise ManifestError(f"manifest fields must be exactly {sorted(_TOP_FIELDS)}")
    if manifest.get("schema") != SCHEMA:
        raise ManifestError(f"schema must be {SCHEMA}")
    name = manifest.get("name")
    version = manifest.get("version")
    kernel_abi = manifest.get("kernel_abi")
    architecture = manifest.get("architecture")
    if not isinstance(name, str) or not name.strip() or len(name) > 80:
        raise ManifestError("system name must contain 1..80 characters")
    if not isinstance(version, str) or not version.strip() or len(version) > 64:
        raise ManifestError("system version must contain 1..64 characters")
    if not isinstance(kernel_abi, str) or not kernel_abi.strip() or len(kernel_abi) > 128:
        raise ManifestError("kernel_abi must be non-empty text of at most 128 characters")
    if architecture not in _ARCHITECTURES:
        raise ManifestError(f"architecture must be one of {sorted(_ARCHITECTURES)}")

    components = manifest.get("components")
    if not isinstance(components, list) or not _REQUIRED <= {
        item.get("name") for item in components if isinstance(item, dict)
    }:
        raise ManifestError("components must include bootloader, kernel, initramfs and rootfs")
    if not 1 <= len(components) <= MAX_COMPONENTS:
        raise ManifestError(f"component count must be between 1 and {MAX_COMPONENTS}")

    supplied_root = Path(root).expanduser()
    if supplied_root.is_symlink():
        raise ManifestError("component root must not be a symlink")
    try:
        base = supplied_root.resolve(strict=True)
    except OSError as error:
        raise ManifestError(f"cannot open component root: {error}") from error
    if not base.is_dir():
        raise ManifestError("component root must be a directory")

    seen = set()
    normalized = []
    total = 0
    for component in components:
        if not isinstance(component, dict) or set(component) != _COMPONENT_FIELDS:
            raise ManifestError("each component must contain name, path, size_bytes and sha256")
        component_name = component.get("name")
        if not isinstance(component_name, str) or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", component_name):
            raise ManifestError("component names must be lowercase identifiers")
        if component_name in seen:
            raise ManifestError(f"duplicate component: {component_name}")
        seen.add(component_name)
        relative = _relative_path(component.get("path"))
        size = component.get("size_bytes")
        digest = component.get("sha256")
        if isinstance(size, bool) or not isinstance(size, int) or not 1 <= size <= MAX_COMPONENT_BYTES:
            raise ManifestError(f"{component_name}: size_bytes must be between 1 and 8 GiB")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ManifestError(f"{component_name}: sha256 must be 64 lowercase hexadecimal characters")
        normalized.append({"name": component_name, "path": relative, "size_bytes": size, "sha256": digest})
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ManifestError("system components exceed the 32 GiB aggregate limit")

        if verify_files:
            candidate = base.joinpath(*PurePosixPath(relative).parts)
            try:
                resolved = candidate.resolve(strict=True)
            except OSError as error:
                raise ManifestError(f"missing component: {relative}") from error
            current = base
            for part in PurePosixPath(relative).parts:
                current = current / part
                if current.is_symlink():
                    raise ManifestError(f"symbolic-link component paths are not allowed: {relative}")
            if not resolved.is_relative_to(base) or not resolved.is_file():
                raise ManifestError(f"component is not a regular file inside root: {relative}")
            actual_size, actual_hash = _hash_file(resolved)
            if actual_size != size:
                raise ManifestError(f"component size mismatch: {relative}")
            if actual_hash != digest:
                raise ManifestError(f"component SHA-256 mismatch: {relative}")

    if not _REQUIRED <= seen:
        raise ManifestError("required boot components are missing")
    return {
        "schema": "duckos.manifest-validation.v1",
        "valid": True,
        "architecture": architecture,
        "kernel_abi": kernel_abi,
        "component_count": len(normalized),
        "total_bytes": total,
        "files_verified": len(normalized) if verify_files else 0,
        "components": normalized,
        "execution_performed": False,
        "disk_writes_performed": False,
    }
