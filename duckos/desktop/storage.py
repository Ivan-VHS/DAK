"""Small, atomic JSON state helpers used by DuckOS desktop services."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any

MAX_STATE_BYTES = 4 * 1024 * 1024


class StateError(ValueError):
    """Raised when persisted service state is unsafe or malformed."""


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise StateError(f"state contains a non-JSON value: {error}") from error


def read_json_state(path: str | Path, default: dict[str, Any]) -> dict[str, Any]:
    target = Path(path).expanduser()
    if target.is_symlink():
        raise StateError(f"state path must not be a symlink: {target}")
    if not target.exists():
        return json.loads(json.dumps(default))
    if not target.is_file():
        raise StateError(f"state path must be a regular file, not a symlink: {target}")
    try:
        if target.stat().st_size > MAX_STATE_BYTES:
            raise StateError(f"state file exceeds {MAX_STATE_BYTES} bytes")
        value = json.loads(target.read_text(encoding="utf-8"))
    except OSError as error:
        raise StateError(f"cannot read state file {target}: {error}") from error
    except json.JSONDecodeError as error:
        raise StateError(f"invalid JSON state in {target}: {error}") from error
    if not isinstance(value, dict):
        raise StateError("state root must be a JSON object")
    return value


def write_json_state(path: str | Path, value: dict[str, Any]) -> None:
    target = Path(path).expanduser()
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink():
        raise StateError(f"state directory must not be a symlink: {parent}")
    if target.is_symlink():
        raise StateError(f"state file must not be a symlink: {target}")

    encoded = canonical_json(value) + b"\n"
    if len(encoded) > MAX_STATE_BYTES:
        raise StateError(f"state exceeds {MAX_STATE_BYTES} bytes")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".tmp", dir=str(parent)
    )
    temporary = Path(temporary_name)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        try:
            directory_fd = os.open(parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            except OSError:
                pass
            finally:
                os.close(directory_fd)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
