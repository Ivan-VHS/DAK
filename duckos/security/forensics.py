"""Bounded, secret-aware incident recorder and evidence export."""
from __future__ import annotations

from collections import deque
from typing import Any, Mapping

SENSITIVE_PARTS = ("password", "token", "cookie", "secret", "credential", "authorization", "private_key")


def redact(value: Any, key: str = "") -> Any:
    normalized = key.lower()
    if any(part in normalized for part in SENSITIVE_PARTS):
        return "[REDACTED]"
    if isinstance(value, Mapping):
        return {str(child_key): redact(child_value, str(child_key)) for child_key, child_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value[:256]]
    if isinstance(value, str):
        return value[:2048]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return "[UNSUPPORTED]"


class FlightRecorder:
    """A bounded in-memory recorder; persistence is an explicit caller decision."""

    def __init__(self, capacity: int = 4096) -> None:
        if capacity < 16 or capacity > 100_000:
            raise ValueError("capacity must be between 16 and 100000")
        self._records: deque[dict[str, Any]] = deque(maxlen=capacity)

    def record(self, event: Mapping[str, Any], evaluation: Mapping[str, Any]) -> None:
        self._records.append({
            "event": redact(event),
            "evaluation": redact(evaluation),
        })

    def export(self, *, incident_event_id: str | None = None) -> dict[str, Any]:
        records = list(self._records)
        selected = records
        if incident_event_id is not None:
            matched = next((index for index, record in enumerate(records)
                            if record["event"].get("event_id") == incident_event_id), None)
            if matched is None:
                raise ValueError("incident event is outside the retained flight-recorder window")
            selected = records[max(0, matched - 64):min(len(records), matched + 65)]
        events = [record["event"] for record in selected]
        edges = []
        known = {event.get("event_id") for event in events}
        for event in events:
            parent = event.get("parent_event_id")
            if parent and parent in known:
                edges.append({"from": parent, "to": event["event_id"], "relationship": "parent_process_or_cause"})
        return {
            "schema": "duckos.security-incident.v1",
            "mode": "local_forensic_export",
            "enforcement": "not_performed",
            "event_count": len(events),
            "events": events,
            "evaluations": [record["evaluation"] for record in selected],
            "causal_edges": edges,
            "redaction": "sensitive-key-based",
        }
