"""Strict, bounded event contract for DuckOS security telemetry."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any, Mapping

EVENT_SCHEMA = "duckos.security-event.v1"
_KIND = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_KEY = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
ALLOWED_KINDS = frozenset({
    "process.start", "process.stop", "process.inject",
    "file.modify", "file.delete", "file.rename",
    "network.connect", "network.listen", "network.dns",
    "memory.read", "memory.write", "identity.access",
    "registry.modify", "service.modify", "integrity.change",
    "driver.load", "mesh.alert", "sandbox.result",
})


class SecurityEventError(ValueError):
    """Raised when an event violates the versioned security event contract."""


def _text(value: Any, field: str, limit: int, *, optional: bool = False) -> str:
    if optional and (value is None or value == ""):
        return ""
    if not isinstance(value, str) or not value or len(value) > limit:
        raise SecurityEventError(f"{field} must be a non-empty string of at most {limit} characters")
    if "\x00" in value:
        raise SecurityEventError(f"{field} contains a NUL character")
    return value


def _attributes(value: Any) -> dict[str, str | int | float | bool]:
    if value is None:
        return {}
    if not isinstance(value, Mapping) or len(value) > 32:
        raise SecurityEventError("attributes must be an object containing at most 32 entries")
    result: dict[str, str | int | float | bool] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not _KEY.fullmatch(key):
            raise SecurityEventError("attribute names must be bounded lowercase identifiers")
        if isinstance(item, bool):
            result[key] = item
        elif isinstance(item, int):
            if abs(item) > 2**63 - 1:
                raise SecurityEventError(f"attribute {key} exceeds the signed 64-bit range")
            result[key] = item
        elif isinstance(item, float):
            if not math.isfinite(item):
                raise SecurityEventError(f"attribute {key} must be finite")
            result[key] = item
        elif isinstance(item, str) and len(item) <= 2048 and "\x00" not in item:
            result[key] = item
        else:
            raise SecurityEventError(f"attribute {key} must be a bounded JSON scalar")
    return result


@dataclass(frozen=True, slots=True)
class SecurityEvent:
    event_id: str
    timestamp_ms: int
    host_id: str
    source: str
    kind: str
    actor_id: str
    object_id: str = ""
    parent_event_id: str = ""
    correlation_id: str = ""
    action: str = ""
    attributes: Mapping[str, str | int | float | bool] | None = None

    @classmethod
    def from_mapping(cls, record: Mapping[str, Any]) -> "SecurityEvent":
        if not isinstance(record, Mapping):
            raise SecurityEventError("each event must be an object")
        schema = record.get("schema", EVENT_SCHEMA)
        if schema != EVENT_SCHEMA:
            raise SecurityEventError(f"unsupported event schema: {schema!r}")
        timestamp = record.get("timestamp_ms")
        if isinstance(timestamp, bool) or not isinstance(timestamp, int) or timestamp <= 0:
            raise SecurityEventError("timestamp_ms must be a positive integer")
        kind = _text(record.get("kind"), "kind", 64)
        if not _KIND.fullmatch(kind) or kind not in ALLOWED_KINDS:
            raise SecurityEventError(f"unsupported event kind: {kind!r}")
        return cls(
            event_id=_text(record.get("event_id"), "event_id", 128),
            timestamp_ms=timestamp,
            host_id=_text(record.get("host_id"), "host_id", 128),
            source=_text(record.get("source"), "source", 128),
            kind=kind,
            actor_id=_text(record.get("actor_id"), "actor_id", 256),
            object_id=_text(record.get("object_id", ""), "object_id", 512, optional=True),
            parent_event_id=_text(record.get("parent_event_id", ""), "parent_event_id", 128, optional=True),
            correlation_id=_text(record.get("correlation_id", ""), "correlation_id", 128, optional=True),
            action=_text(record.get("action", ""), "action", 128, optional=True),
            attributes=_attributes(record.get("attributes", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": EVENT_SCHEMA,
            "event_id": self.event_id,
            "timestamp_ms": self.timestamp_ms,
            "host_id": self.host_id,
            "source": self.source,
            "kind": self.kind,
            "actor_id": self.actor_id,
            "object_id": self.object_id,
            "parent_event_id": self.parent_event_id,
            "correlation_id": self.correlation_id,
            "action": self.action,
            "attributes": dict(self.attributes or {}),
        }
