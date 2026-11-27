"""Small, dependable helpers shared by the DuckOS user-space services."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ServiceError(Exception):
    """A request that a DuckOS service cannot safely complete."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (OSError, json.JSONDecodeError) as error:
        raise ServiceError(f"cannot read {path}: {error}") from error


def atomic_write_json(path: Path, value: Any) -> None:
    """Replace a JSON file atomically and flush both file and parent directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(temporary_path, path)
        temporary_path = None

        try:
            directory_fd = os.open(path.parent, os.O_RDONLY)
        except OSError:
            return

        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def require_text(value: Any, label: str, limit: int = 256) -> str:
    if not isinstance(value, str):
        raise ServiceError(f"{label} must be text")
    cleaned = value.strip()
    if not cleaned or len(cleaned) > limit or "\0" in cleaned:
        raise ServiceError(f"{label} must contain 1 to {limit} characters")
    return cleaned
