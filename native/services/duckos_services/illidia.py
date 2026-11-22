"""Illidia: checksummed snapshots of user-session state, not user files."""

from __future__ import annotations

import hashlib
import hmac
import re
import uuid
from pathlib import Path
from typing import Any

from .common import ServiceError, atomic_write_json, canonical_json, read_json, utc_now


_SNAPSHOT_ID = re.compile(r"^[0-9]{8}T[0-9]{9}Z-[a-f0-9]{8}$")
_ALLOWED_FIELDS = {
    "theme", "profile", "workspace", "layout", "windows",
    "key_bindings", "audio_routing",
}
_SCHEMA_VERSION = 1
_MAX_STATE_BYTES = 512 * 1024


class SnapshotStore:
    """Store versioned session snapshots with atomic writes and integrity checks."""

    def __init__(self, directory: Path, retention: int = 30) -> None:
        if retention < 1:
            raise ValueError("retention must be positive")
        self.directory = directory.expanduser()
        self.retention = retention

    @staticmethod
    def _clean_state(state: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(state, dict):
            raise ServiceError("snapshot state must be an object")
        if any(not isinstance(key, str) for key in state):
            raise ServiceError("snapshot field names must be text")
        unknown = set(state) - _ALLOWED_FIELDS
        if unknown:
            raise ServiceError(f"snapshot contains unsupported fields: {sorted(unknown)}")
        try:
            encoded = canonical_json(state)
        except (TypeError, ValueError) as error:
            raise ServiceError(f"snapshot state is not valid JSON data: {error}") from error
        if len(encoded) > _MAX_STATE_BYTES:
            raise ServiceError("snapshot state exceeds 512 KiB")
        return state

    def save(self, state: dict[str, Any], label: str = "Session checkpoint") -> dict[str, Any]:
        cleaned = self._clean_state(state)
        if not isinstance(label, str) or not label.strip() or len(label) > 80:
            raise ServiceError("snapshot label must contain 1 to 80 characters")

        timestamp = utc_now()
        stamp = timestamp.replace("-", "").replace(":", "").replace(".", "")
        identifier = f"{stamp}-{uuid.uuid4().hex[:8]}"
        digest = hashlib.sha256(canonical_json(cleaned)).hexdigest()
        record = {
            "schema_version": _SCHEMA_VERSION,
            "id": identifier,
            "created_at": timestamp,
            "label": label.strip(),
            "state": cleaned,
            "sha256": digest,
        }

        self.directory.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self.directory / f"{identifier}.json", record)
        self._prune()
        return {key: record[key] for key in ("id", "created_at", "label", "sha256")}

    def _read_record(self, identifier: str) -> dict[str, Any]:
        if not isinstance(identifier, str) or not _SNAPSHOT_ID.fullmatch(identifier):
            raise ServiceError(f"invalid snapshot id: {identifier!r}")
        record = read_json(self.directory / f"{identifier}.json", None)
        if not isinstance(record, dict):
            raise ServiceError(f"snapshot does not exist: {identifier}")
        if record.get("schema_version") != _SCHEMA_VERSION or record.get("id") != identifier:
            raise ServiceError(f"unsupported or malformed snapshot: {identifier}")

        state = self._clean_state(record.get("state"))
        expected = record.get("sha256")
        actual = hashlib.sha256(canonical_json(state)).hexdigest()
        if not isinstance(expected, str) or not hmac.compare_digest(expected, actual):
            raise ServiceError(f"snapshot integrity check failed: {identifier}")
        return record

    def restore(self, identifier: str) -> dict[str, Any]:
        """Return validated state; callers decide when and how to apply it."""
        return dict(self._read_record(identifier)["state"])

    def list(self) -> list[dict[str, Any]]:
        if not self.directory.exists():
            return []
        records = []
        for path in self.directory.glob("*.json"):
            try:
                record = self._read_record(path.stem)
            except ServiceError:
                continue
            records.append({
                "id": record["id"],
                "created_at": record["created_at"],
                "label": record["label"],
            })
        return sorted(records, key=lambda item: item["created_at"], reverse=True)

    def _prune(self) -> None:
        records = self.list()
        for record in records[self.retention:]:
            (self.directory / f"{record['id']}.json").unlink(missing_ok=True)
