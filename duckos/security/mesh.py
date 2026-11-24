"""Authenticated, replay-resistant mesh alert envelopes (transport excluded)."""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from collections import deque
from typing import Any, Mapping

ALERT_SCHEMA = "duckos.mesh-threat-alert.v1"
ALERT_ID = re.compile(r"^[A-Za-z0-9_-]{16,96}$")


def _canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def create_alert(
    *,
    origin_host: str,
    indicators: list[str],
    severity: str,
    key: bytes,
    ttl_ms: int = 60_000,
    now_ms: int | None = None,
    alert_id: str | None = None,
) -> dict[str, Any]:
    if not isinstance(key, bytes) or len(key) < 32:
        raise ValueError("mesh HMAC key must contain at least 32 bytes")
    if not isinstance(origin_host, str) or not origin_host or len(origin_host) > 128:
        raise ValueError("origin_host must be a bounded non-empty identifier")
    if severity not in {"low", "medium", "high", "critical"}:
        raise ValueError("unsupported severity")
    if not isinstance(indicators, list) or len(indicators) > 32:
        raise ValueError("indicators must contain at most 32 entries")
    if any(not isinstance(item, str) or not item or len(item) > 256 for item in indicators):
        raise ValueError("each indicator must be a bounded non-empty string")
    if isinstance(ttl_ms, bool) or not isinstance(ttl_ms, int) or ttl_ms < 1000 or ttl_ms > 300_000:
        raise ValueError("ttl_ms must be between 1000 and 300000")
    issued = int(time.time() * 1000) if now_ms is None else now_ms
    identifier = alert_id or hashlib.sha256(f"{origin_host}:{issued}:{','.join(indicators)}".encode()).hexdigest()[:32]
    if not isinstance(identifier, str) or not ALERT_ID.fullmatch(identifier):
        raise ValueError("alert_id must be a bounded identifier")
    unsigned = {
        "schema": ALERT_SCHEMA,
        "alert_id": identifier,
        "origin_host": origin_host,
        "issued_at_ms": issued,
        "expires_at_ms": issued + ttl_ms,
        "severity": severity,
        "indicators": list(dict.fromkeys(indicators)),
    }
    unsigned["signature"] = hmac.new(key, _canonical(unsigned), hashlib.sha256).hexdigest()
    return unsigned


class MeshVerifier:
    def __init__(self, key: bytes, *, max_seen: int = 8192, max_skew_ms: int = 30_000) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("mesh HMAC key must contain at least 32 bytes")
        if max_seen < 16 or max_seen > 100_000:
            raise ValueError("max_seen must be between 16 and 100000")
        self._key = key
        self._max_skew_ms = max_skew_ms
        self._seen: deque[str] = deque(maxlen=max_seen)
        self._seen_set: set[str] = set()

    def verify(self, alert: Mapping[str, Any], *, now_ms: int | None = None) -> tuple[bool, str]:
        if not isinstance(alert, Mapping) or alert.get("schema") != ALERT_SCHEMA:
            return False, "invalid_schema"
        required = {"schema", "alert_id", "origin_host", "issued_at_ms", "expires_at_ms", "severity", "indicators", "signature"}
        if set(alert) != required:
            return False, "invalid_fields"
        identifier = alert.get("alert_id")
        if not isinstance(identifier, str) or not ALERT_ID.fullmatch(identifier):
            return False, "invalid_alert_id"
        if identifier in self._seen_set:
            return False, "replay"
        issued = alert.get("issued_at_ms")
        expires = alert.get("expires_at_ms")
        current = int(time.time() * 1000) if now_ms is None else now_ms
        if any(isinstance(value, bool) or not isinstance(value, int) for value in (issued, expires)):
            return False, "invalid_timestamps"
        ttl = expires - issued
        if ttl < 1000 or ttl > 300_000 or issued > current + self._max_skew_ms or expires <= current:
            return False, "expired_or_invalid_ttl"
        if alert.get("severity") not in {"low", "medium", "high", "critical"}:
            return False, "invalid_severity"
        if not isinstance(alert.get("origin_host"), str) or not alert["origin_host"] or len(alert["origin_host"]) > 128:
            return False, "invalid_origin"
        indicators = alert.get("indicators")
        if not isinstance(indicators, list) or len(indicators) > 32 or any(not isinstance(item, str) or not item or len(item) > 256 for item in indicators):
            return False, "invalid_indicators"
        signature = alert.get("signature")
        if not isinstance(signature, str) or not re.fullmatch(r"[0-9a-f]{64}", signature):
            return False, "invalid_signature"
        unsigned = dict(alert)
        unsigned.pop("signature")
        expected = hmac.new(self._key, _canonical(unsigned), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False, "signature_mismatch"
        if len(self._seen) == self._seen.maxlen:
            self._seen_set.discard(self._seen[0])
        self._seen.append(identifier)
        self._seen_set.add(identifier)
        return True, "verified"
