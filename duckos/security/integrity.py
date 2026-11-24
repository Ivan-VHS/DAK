"""Read-only SHA-256 inventory verification for managed component trees."""
from __future__ import annotations

import hashlib
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _safe_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or len(relative) > 1024:
        raise ValueError("manifest path must be a bounded relative path")
    path = PurePosixPath(relative.replace("\\", "/"))
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("manifest path must not contain absolute or dot segments")
    current = root
    for part in path.parts:
        current = current / part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError("manifest paths must not traverse symbolic links")
    if not stat.S_ISREG(current.stat().st_mode):
        raise ValueError("manifest entries must refer to regular files")
    return current


def verify_integrity_manifest(root: str | Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    base = Path(root).expanduser()
    if base.is_symlink() or not base.is_dir():
        raise ValueError("integrity root must be an existing non-symlink directory")
    base = base.resolve(strict=True)
    if not isinstance(manifest, Mapping) or manifest.get("schema") != "duckos.integrity-manifest.v1":
        raise ValueError("unsupported integrity manifest schema")
    files = manifest.get("files")
    if not isinstance(files, list) or not files or len(files) > 4096:
        raise ValueError("manifest files must contain between 1 and 4096 entries")

    results = []
    seen = set()
    for item in files:
        if not isinstance(item, Mapping):
            raise ValueError("manifest file entries must be objects")
        relative = item.get("path")
        expected = item.get("sha256")
        if not isinstance(relative, str):
            raise ValueError("manifest path must be a string")
        if not isinstance(expected, str) or not DIGEST.fullmatch(expected):
            raise ValueError("manifest sha256 values must be lowercase SHA-256 digests")
        if relative in seen:
            raise ValueError(f"duplicate manifest path: {relative}")
        seen.add(relative)
        try:
            path = _safe_file(base, relative)
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            actual = digest.hexdigest()
            status = "match" if actual == expected else "mismatch"
        except (OSError, ValueError) as error:
            actual = None
            status = "unreadable"
            detail = str(error)
        else:
            detail = ""
        results.append({"path": relative, "status": status, "expected_sha256": expected, "actual_sha256": actual, "detail": detail})

    return {
        "schema": "duckos.integrity-report.v1",
        "root": str(base),
        "verified": all(item["status"] == "match" for item in results),
        "repair_performed": False,
        "files_checked": len(results),
        "results": results,
    }
