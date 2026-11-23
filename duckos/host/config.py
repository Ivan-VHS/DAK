"""Create protected host capability and HTTP bridge token files."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import secrets
import tempfile
from typing import Any

from .runtime import HostError, SUPPORTED_CAPABILITIES


def _atomic_json(path: Path, payload: dict[str, Any], mode: int = 0o600) -> None:
    path = path.expanduser()
    if path.is_symlink():
        raise HostError(f"refusing to replace symbolic link: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    file_descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
        os.chmod(path, mode)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def write_policy(path: str | Path, uid: int, capabilities: list[str]) -> dict[str, Any]:
    if isinstance(uid, bool) or not isinstance(uid, int) or uid < 0:
        raise HostError("UID must be a non-negative integer")
    if not isinstance(capabilities, list) or len(capabilities) > len(SUPPORTED_CAPABILITIES):
        raise HostError("capabilities must be a bounded list")
    selected = set(capabilities)
    if not all(isinstance(item, str) for item in selected):
        raise HostError("capability names must be text")
    unknown = selected - SUPPORTED_CAPABILITIES
    if unknown:
        raise HostError(f"unsupported capability grants: {', '.join(sorted(unknown))}")
    payload = {
        "schema": "duckos.host-policy.v1",
        "principals": {str(uid): sorted(selected)},
    }
    destination = Path(path)
    _atomic_json(destination, payload, 0o600)
    return {"path": str(destination), "mode": "0600", "uid": uid, "grants": sorted(selected)}


def create_bridge_token(path: str | Path, uid: int) -> dict[str, Any]:
    if isinstance(uid, bool) or not isinstance(uid, int) or uid < 0:
        raise HostError("UID must be a non-negative integer")
    destination = Path(path).expanduser()
    if destination.is_symlink():
        raise HostError(f"refusing to replace symbolic link: {destination}")
    payload: dict[str, Any]
    if destination.exists():
        try:
            if destination.stat().st_mode & 0o077:
                raise HostError("existing bridge token file must have mode 0600")
            payload = json.loads(destination.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise HostError(f"cannot read existing token file: {error}") from error
        if not isinstance(payload, dict) or payload.get("schema") != "duckos.bridge-tokens.v1":
            raise HostError("existing bridge token file uses an unsupported schema")
        if not isinstance(payload.get("tokens"), dict):
            raise HostError("existing bridge token registry is malformed")
        tokens = dict(payload["tokens"])
    else:
        tokens = {}
    if len(tokens) >= 32:
        raise HostError("bridge token limit (32) reached")
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    tokens[digest] = uid
    _atomic_json(destination, {"schema": "duckos.bridge-tokens.v1", "tokens": tokens}, 0o600)
    return {
        "path": str(destination),
        "mode": "0600",
        "uid": uid,
        "token": token,
        "stored_form": "sha256",
        "warning": "Copy the token now. Only its SHA-256 digest is stored on disk.",
    }
