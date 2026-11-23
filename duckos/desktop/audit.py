"""Append-only, hash-chained audit and serial-session journal."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import threading
from typing import Any

from .storage import canonical_json

_EVENT = re.compile(r"^[a-z][a-z0-9.-]{1,95}$")
MAX_LOG_BYTES = 32 * 1024 * 1024
MAX_DETAILS_BYTES = 16 * 1024
_LOCK = threading.Lock()


class AuditError(ValueError):
    """Raised when an audit journal cannot be safely read or extended."""


class AuditLog:
    """Single-writer JSONL journal with a verifiable SHA-256 hash chain."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()

    def verify(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"valid": True, "entries": 0, "last_sha256": None}
        if self.path.is_symlink() or not self.path.is_file():
            raise AuditError("audit journal must be a regular file, not a symlink")
        if self.path.stat().st_size > MAX_LOG_BYTES:
            raise AuditError("audit journal exceeds the configured size limit")

        previous = None
        sequence = 0
        try:
            with self.path.open("r", encoding="utf-8") as stream:
                for line_number, line in enumerate(stream, 1):
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise AuditError(f"record {line_number} is not an object")
                    digest = record.get("entry_sha256")
                    payload = {key: value for key, value in record.items() if key != "entry_sha256"}
                    expected = hashlib.sha256(canonical_json(payload)).hexdigest()
                    if (
                        record.get("schema") != "duckos.audit-entry.v1"
                        or record.get("sequence") != sequence + 1
                        or record.get("previous_sha256") != previous
                        or digest != expected
                    ):
                        raise AuditError(f"audit hash chain is invalid at line {line_number}")
                    previous = digest
                    sequence += 1
        except (OSError, json.JSONDecodeError) as error:
            raise AuditError(f"cannot verify audit journal: {error}") from error
        return {"valid": True, "entries": sequence, "last_sha256": previous}

    def append(self, event: str, details: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(event, str) or not _EVENT.fullmatch(event):
            raise AuditError("event must be a lowercase dotted identifier")
        if not isinstance(details, dict) or len(canonical_json(details)) > MAX_DETAILS_BYTES:
            raise AuditError("audit details must be an object no larger than 16 KiB")

        with _LOCK:
            state = self.verify()
            record = {
                "schema": "duckos.audit-entry.v1",
                "sequence": state["entries"] + 1,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "details": details,
                "previous_sha256": state["last_sha256"],
            }
            record["entry_sha256"] = hashlib.sha256(canonical_json(record)).hexdigest()
            encoded = canonical_json(record) + b"\n"
            if self.path.exists() and self.path.stat().st_size + len(encoded) > MAX_LOG_BYTES:
                raise AuditError("audit journal reached its size limit; archive it before writing")
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.parent.is_symlink() or self.path.is_symlink():
                raise AuditError("audit journal paths must not be symbolic links")
            flags = os.O_CREAT | os.O_APPEND | os.O_WRONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                descriptor = os.open(self.path, flags, 0o600)
                try:
                    view = memoryview(encoded)
                    while view:
                        written = os.write(descriptor, view)
                        view = view[written:]
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
            except OSError as error:
                raise AuditError(f"cannot append audit event: {error}") from error
            return record


_SECRET = re.compile(
    r"(?i)\b(password|passwd|token|secret|authorization|api[_-]?key)\b\s*[:=]\s*[^\s,;]+"
)


class SerialLogWriter:
    """Store serial lines as audit events after basic secret redaction."""

    def __init__(self, audit_log: AuditLog, *, allowed_ports: list[str] | tuple[str, ...] | None = None) -> None:
        self.audit_log = audit_log
        if allowed_ports is not None and (
            not isinstance(allowed_ports, (list, tuple))
            or any(not isinstance(port, str) or not port.strip() or len(port) > 128 for port in allowed_ports)
            or len(set(allowed_ports)) != len(allowed_ports)
        ):
            raise AuditError("allowed_ports must be a unique list of bounded port names")
        self.allowed_ports = None if allowed_ports is None else frozenset(allowed_ports)

    def append(
        self,
        *,
        session_id: str,
        port: str,
        fixture_slot: str,
        line: str,
    ) -> dict[str, Any]:
        if not isinstance(session_id, str) or not session_id or len(session_id) > 128:
            raise AuditError("session_id must contain 1..128 characters")
        if not isinstance(port, str) or not port or len(port) > 128:
            raise AuditError("port must contain 1..128 characters")
        if fixture_slot not in {"A", "B"}:
            raise AuditError("fixture_slot must be A or B")
        if self.allowed_ports is not None and port not in self.allowed_ports:
            raise AuditError("serial port is not allowed by the selected bench profile")
        if not isinstance(line, str) or len(line) > 4096:
            raise AuditError("serial line must be text no longer than 4096 characters")
        cleaned = line.replace("\r", "").replace("\x00", "")
        cleaned = _SECRET.sub(lambda match: match.group(1) + "=[REDACTED]", cleaned)
        return self.audit_log.append("bench.serial-line", {
            "session_id": session_id,
            "port": port,
            "fixture_slot": fixture_slot,
            "line": cleaned,
        })
