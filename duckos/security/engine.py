"""Deterministic correlation and risk policy for DuckOS security events.

This is an advisory policy engine. It never blocks a process, changes a file,
alters a firewall, reads process memory, or invokes a privileged OS API.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .events import SecurityEvent

WINDOW_MS = 30_000
LOLBINS = frozenset({
    "powershell.exe", "pwsh.exe", "cmd.exe", "wscript.exe", "cscript.exe",
    "mshta.exe", "rundll32.exe", "regsvr32.exe", "certutil.exe",
    "bitsadmin.exe", "msiexec.exe", "wmic.exe", "installutil.exe",
})


@dataclass(frozen=True, slots=True)
class RiskEvaluation:
    event_id: str
    risk_score: int
    risk_level: str
    confidence: float
    recommendation: str
    enforcement: str
    indicators: tuple[dict[str, Any], ...]
    causal_root: str
    causal_chain: tuple[str, ...]
    sandbox_recommended: bool
    snapshot_recommended: bool

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["indicators"] = list(self.indicators)
        value["causal_chain"] = list(self.causal_chain)
        return value


class SecurityEngine:
    """Bounded event correlator with deterministic, explainable risk decisions."""

    def __init__(self, *, capacity: int = 4096, window_ms: int = WINDOW_MS) -> None:
        if capacity < 16 or capacity > 100_000:
            raise ValueError("capacity must be between 16 and 100000")
        if window_ms < 1000 or window_ms > 24 * 60 * 60 * 1000:
            raise ValueError("window_ms must be between 1000 and 86400000")
        self.capacity = capacity
        self.window_ms = window_ms
        self._events: deque[SecurityEvent] = deque(maxlen=capacity)
        self._by_id: dict[str, SecurityEvent] = {}
        self._seen: deque[str] = deque(maxlen=capacity * 2)
        self._seen_set: set[str] = set()
        self._last_timestamp: dict[str, int] = {}
        self._indicators: dict[str, deque[tuple[int, str]]] = defaultdict(deque)

    @property
    def event_count(self) -> int:
        return len(self._events)

    def _append(self, event: SecurityEvent) -> None:
        if event.event_id in self._seen_set:
            raise ValueError(f"duplicate event_id: {event.event_id}")
        previous_timestamp = self._last_timestamp.get(event.host_id, 0)
        if event.timestamp_ms < previous_timestamp:
            raise ValueError("events for one host must be ingested in timestamp order")
        self._last_timestamp[event.host_id] = event.timestamp_ms

        if len(self._seen) == self._seen.maxlen:
            self._seen_set.discard(self._seen[0])
        self._seen.append(event.event_id)
        self._seen_set.add(event.event_id)

        if len(self._events) == self.capacity:
            oldest = self._events[0]
            self._by_id.pop(oldest.event_id, None)
            if oldest.host_id != event.host_id and not any(
                item.host_id == oldest.host_id for item in list(self._events)[1:]
            ):
                self._last_timestamp.pop(oldest.host_id, None)
        self._events.append(event)
        self._by_id[event.event_id] = event

    def _causal_chain(self, event: SecurityEvent) -> tuple[str, ...]:
        chain = [event.event_id]
        parent_id = event.parent_event_id
        visited = {event.event_id}
        while parent_id and parent_id not in visited and len(chain) < 32:
            parent = self._by_id.get(parent_id)
            if parent is None or parent.host_id != event.host_id:
                break
            chain.append(parent.event_id)
            visited.add(parent.event_id)
            parent_id = parent.parent_event_id
        chain.reverse()
        return tuple(chain)

    def _cluster_size(self, event: SecurityEvent) -> int:
        attributes = event.attributes or {}
        indicator = attributes.get("indicator_hash") or attributes.get("indicator")
        if not isinstance(indicator, str) or not indicator or len(indicator) > 256:
            return 0
        if indicator not in self._indicators:
            if len(self._indicators) >= self.capacity:
                self._indicators.pop(next(iter(self._indicators)))
            self._indicators[indicator] = deque(maxlen=self.capacity)
        bucket = self._indicators[indicator]
        recent = [
            (timestamp, host) for timestamp, host in bucket
            if 0 <= event.timestamp_ms - timestamp <= 5 * 60 * 1000
        ]
        bucket.clear()
        bucket.extend(recent)
        if not any(host == event.host_id for _, host in bucket):
            bucket.append((event.timestamp_ms, event.host_id))
        return len({host for _, host in bucket})

    def ingest(self, event: SecurityEvent) -> RiskEvaluation:
        if not isinstance(event, SecurityEvent):
            raise TypeError("event must be a validated SecurityEvent")
        self._append(event)
        attributes = event.attributes or {}
        indicators: list[dict[str, Any]] = []
        score = 0

        def signal(code: str, points: int, detail: str) -> None:
            nonlocal score
            score += points
            indicators.append({"code": code, "points": points, "detail": detail})

        if event.kind == "process.inject":
            signal("process_injection", 50, "A process injection event was reported by the source sensor.")

        if event.kind == "memory.read" and attributes.get("sensitive_target") is True and attributes.get("authorized") is not True:
            signal("sensitive_memory_read", 45, "An unapproved process accessed memory marked as sensitive.")

        if event.kind == "identity.access":
            target_type = attributes.get("target_type")
            if target_type in {"session_token", "browser_cookie", "refresh_token", "password_store"} and attributes.get("authorized") is not True:
                signal("credential_material_access", 60, "An unapproved access to session or credential material was reported.")

        if event.kind == "integrity.change" and attributes.get("protected_component") is True:
            signal("security_component_tampering", 60, "A protected system or security component changed unexpectedly.")

        if event.kind == "driver.load" and attributes.get("signature_valid") is not True:
            signal("unverified_driver", 45, "A driver load event did not carry a successful signature-verification result.")

        if event.kind in {"file.modify", "file.delete", "file.rename"}:
            mutations = [
                item for item in self._events
                if item.host_id == event.host_id
                and item.actor_id == event.actor_id
                and item.kind in {"file.modify", "file.delete", "file.rename"}
                and 0 <= event.timestamp_ms - item.timestamp_ms <= self.window_ms
            ]
            if len(mutations) >= 3:
                points = min(30, 10 + (len(mutations) - 3) * 5)
                signal("burst_file_mutation", points, f"{len(mutations)} file mutations by the same actor occurred inside the correlation window.")
            entropy_delta = attributes.get("entropy_delta")
            if isinstance(entropy_delta, (int, float)) and not isinstance(entropy_delta, bool):
                if entropy_delta >= 0.50:
                    signal("high_entropy_change", 25, "Written content has a large measured entropy increase.")
                elif entropy_delta >= 0.25:
                    signal("entropy_change", 12, "Written content has a notable measured entropy increase.")

        if event.kind == "network.connect":
            if attributes.get("destination_reputation") == "malicious":
                signal("known_malicious_destination", 60, "The source sensor marked the destination as malicious.")
            repeat_count = attributes.get("repeat_count", 0)
            if attributes.get("beacon_periodic") is True and isinstance(repeat_count, int) and not isinstance(repeat_count, bool) and repeat_count >= 4:
                signal("periodic_network_beacon", 20, "Repeated periodic network communication was reported.")

        if event.kind == "process.start":
            image_name = str(attributes.get("image_name", "")).lower().replace("/", "\\").rsplit("\\", 1)[-1]
            lolbin_context = any(attributes.get(key) is True for key in (
                "encoded_command", "hidden_window", "launched_from_user_writable", "unexpected_parent", "network_child"
            ))
            if image_name in LOLBINS and lolbin_context:
                signal("living_off_the_land_context", 25, f"{image_name} was launched with a suspicious execution context.")
            if attributes.get("origin_trust") == "untrusted":
                signal("untrusted_execution_origin", 25, "A process start was associated with an untrusted origin.")
            if attributes.get("suspicious_chain") is True:
                signal("suspicious_process_chain", 25, "The source sensor identified a suspicious parent/child process relationship.")

        if event.kind == "mesh.alert" and attributes.get("signature_verified") is True:
            signal("verified_mesh_intelligence", 10, "A signed peer signal was supplied as corroborating evidence.")

        cluster_size = self._cluster_size(event)
        if cluster_size >= 4:
            signal("multi_host_threat_cluster", 25, f"The same indicator was seen on {cluster_size} distinct hosts in five minutes.")
        elif cluster_size >= 2:
            signal("cross_host_threat_cluster", 12, f"The same indicator was seen on {cluster_size} distinct hosts in five minutes.")

        score = min(100, score)
        confidence = min(0.98, 0.55 + 0.07 * len(indicators)) if indicators else 0.25
        if score >= 80:
            level, recommendation = "critical", "block"
        elif score >= 60:
            level, recommendation = "high", "isolate"
        elif score >= 35:
            level, recommendation = "high", "restrict"
        elif score >= 20:
            level, recommendation = "medium", "sandbox"
        else:
            level, recommendation = "low", "monitor"

        chain = self._causal_chain(event)
        destructive = event.kind in {"file.modify", "file.delete", "file.rename", "registry.modify", "service.modify"}
        return RiskEvaluation(
            event_id=event.event_id,
            risk_score=score,
            risk_level=level,
            confidence=round(confidence, 3),
            recommendation=recommendation,
            enforcement="advisory_only",
            indicators=tuple(indicators),
            causal_root=chain[0] if chain else event.event_id,
            causal_chain=chain,
            sandbox_recommended=(
                attributes.get("origin_trust") == "untrusted"
                or (event.kind in {"process.start", "driver.load"} and score >= 20)
            ),
            snapshot_recommended=destructive and (
                score >= 20 or event.kind in {"file.delete", "registry.modify", "service.modify"}
            ),
        )

    def ingest_many(self, events: Iterable[SecurityEvent]) -> list[RiskEvaluation]:
        return [self.ingest(event) for event in events]

    def recent_events(self) -> tuple[SecurityEvent, ...]:
        return tuple(self._events)
