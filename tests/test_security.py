from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from duckos.security.engine import SecurityEngine
from duckos.security.events import SecurityEvent, SecurityEventError
from duckos.security.forensics import FlightRecorder
from duckos.security.governor import recommend_profile
from duckos.security.integrity import verify_integrity_manifest
from duckos.security.mesh import MeshVerifier, create_alert
from duckos.security.service import analyze_event_document, security_status
from duckos.security.snapshots import SnapshotError, SnapshotStore


def event(event_id: str, kind: str, **kwargs):
    record = {
        "event_id": event_id,
        "timestamp_ms": kwargs.pop("timestamp_ms", 1_800_000_000_000),
        "host_id": kwargs.pop("host_id", "host-a"),
        "source": "test-sensor",
        "kind": kind,
        "actor_id": kwargs.pop("actor_id", "proc-a"),
        "attributes": kwargs.pop("attributes", {}),
    }
    record.update(kwargs)
    return SecurityEvent.from_mapping(record)


class SecurityEventTests(unittest.TestCase):
    def test_rejects_unknown_event_kind_and_unbounded_attributes(self):
        with self.assertRaises(SecurityEventError):
            SecurityEvent.from_mapping({"event_id": "1", "timestamp_ms": 1, "host_id": "h", "source": "s", "kind": "unknown", "actor_id": "p"})
        with self.assertRaises(SecurityEventError):
            SecurityEvent.from_mapping({"event_id": "1", "timestamp_ms": 1, "host_id": "h", "source": "s", "kind": "process.start", "actor_id": "p", "attributes": {"x": {"nested": True}}})


class SecurityEngineTests(unittest.TestCase):
    def test_correlates_ransomware_style_burst_with_causal_parent(self):
        engine = SecurityEngine()
        parent = event("p1", "process.start", attributes={"image_name": "explorer.exe"})
        engine.ingest(parent)
        first = event("f1", "file.modify", parent_event_id="p1", attributes={"entropy_delta": 0.6})
        second = event("f2", "file.modify", timestamp_ms=1_800_000_000_010, parent_event_id="p1", attributes={"entropy_delta": 0.6})
        third = event("f3", "file.modify", timestamp_ms=1_800_000_000_020, parent_event_id="p1", attributes={"entropy_delta": 0.6})
        engine.ingest(first)
        engine.ingest(second)
        result = engine.ingest(third)
        self.assertGreaterEqual(result.risk_score, 35)
        self.assertEqual(result.causal_root, "p1")
        self.assertIn("burst_file_mutation", {item["code"] for item in result.indicators})
        self.assertTrue(result.snapshot_recommended)
        self.assertEqual(result.enforcement, "advisory_only")

    def test_credential_access_is_critical(self):
        result = SecurityEngine().ingest(event(
            "cred1", "identity.access",
            attributes={"target_type": "session_token", "authorized": False},
        ))
        self.assertEqual(result.risk_score, 60)
        self.assertEqual(result.recommendation, "isolate")

    def test_lolbin_context_requires_more_than_binary_name(self):
        engine = SecurityEngine()
        benign = engine.ingest(event("l1", "process.start", attributes={"image_name": "powershell.exe"}))
        suspicious = engine.ingest(event("l2", "process.start", timestamp_ms=1_800_000_000_001, attributes={"image_name": "powershell.exe", "encoded_command": True}))
        self.assertEqual(benign.risk_score, 0)
        self.assertEqual(suspicious.risk_score, 25)
        self.assertTrue(suspicious.sandbox_recommended)

    def test_indicator_cluster_counts_distinct_hosts(self):
        engine = SecurityEngine()
        engine.ingest(event("m1", "network.connect", attributes={"indicator_hash": "sha256:abc"}))
        result = engine.ingest(event("m2", "network.connect", host_id="host-b", timestamp_ms=1_800_000_000_001, attributes={"indicator_hash": "sha256:abc"}))
        self.assertIn("cross_host_threat_cluster", {item["code"] for item in result.indicators})

    def test_duplicate_event_id_is_rejected(self):
        engine = SecurityEngine()
        first = event("same", "process.start")
        engine.ingest(first)
        with self.assertRaises(ValueError):
            engine.ingest(first)


class MeshTests(unittest.TestCase):
    def test_signed_alert_is_verified_once_and_replay_is_rejected(self):
        key = b"k" * 32
        alert = create_alert(origin_host="host-a", indicators=["sha256:abc"], severity="high", key=key, now_ms=100_000, alert_id="alert_123456789012345")
        verifier = MeshVerifier(key)
        self.assertEqual(verifier.verify(alert, now_ms=110_000), (True, "verified"))
        self.assertEqual(verifier.verify(alert, now_ms=110_000), (False, "replay"))

    def test_tampered_or_expired_mesh_alert_is_rejected(self):
        key = b"m" * 32
        alert = create_alert(origin_host="host-a", indicators=["ioc"], severity="medium", key=key, now_ms=100_000)
        changed = dict(alert)
        changed["severity"] = "critical"
        self.assertEqual(MeshVerifier(key).verify(changed, now_ms=101_000), (False, "signature_mismatch"))
        self.assertEqual(MeshVerifier(key).verify(alert, now_ms=400_000), (False, "expired_or_invalid_ttl"))


class SnapshotTests(unittest.TestCase):
    def test_snapshot_and_restore_are_atomic_and_hash_verified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "document.txt"
            target.write_text("original", encoding="utf-8")
            store = SnapshotStore(root)
            metadata = store.create("document.txt")
            target.write_text("damaged", encoding="utf-8")
            result = store.restore(metadata["snapshot_id"])
            self.assertTrue(result["restored"])
            self.assertEqual(target.read_text(encoding="utf-8"), "original")

    def test_rejects_parent_traversal_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "outside.txt"
            target.write_text("safe", encoding="utf-8")
            (root / "link.txt").symlink_to(target)
            store = SnapshotStore(root)
            with self.assertRaises(SnapshotError):
                store.create("../outside.txt")
            with self.assertRaises(SnapshotError):
                store.create("link.txt")


class IntegrityAndForensicsTests(unittest.TestCase):
    def test_integrity_manifest_checks_digest_without_repair(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            item = root / "component.bin"
            item.write_bytes(b"known")
            report = verify_integrity_manifest(root, {
                "schema": "duckos.integrity-manifest.v1",
                "files": [{"path": "component.bin", "sha256": hashlib.sha256(b"known").hexdigest()}],
            })
            self.assertTrue(report["verified"])
            self.assertFalse(report["repair_performed"])

    def test_flight_recorder_redacts_secrets_and_bounds_context(self):
        recorder = FlightRecorder(capacity=16)
        recorder.record(
            {"event_id": "e1", "attributes": {"session_token": "do-not-leak", "image_name": "safe.exe"}},
            {"risk_score": 0, "recommendation": "monitor"},
        )
        report = recorder.export()
        serialized = json.dumps(report)
        self.assertNotIn("do-not-leak", serialized)
        self.assertIn("[REDACTED]", serialized)


class GovernorAndServiceTests(unittest.TestCase):
    def test_suspicious_activity_overrides_quiet_context_without_suppressing_protection(self):
        result = recommend_profile(fullscreen=True, on_battery=True, suspicious_activity=True)
        self.assertEqual(result["profile"], "security_critical")
        self.assertFalse(result["protection_suppressed"])
        self.assertEqual(result["event_collection"], "unchanged")

    def test_offline_analysis_produces_causal_evidence_and_discloses_limits(self):
        payload = {
            "schema": "duckos.security-events.v1",
            "events": [
                {"event_id": "p1", "timestamp_ms": 1_800_000_000_000, "host_id": "host-a", "source": "sensor", "kind": "process.start", "actor_id": "p1", "attributes": {"image_name": "powershell.exe", "encoded_command": True}},
                {"event_id": "f1", "timestamp_ms": 1_800_000_000_001, "host_id": "host-a", "source": "sensor", "kind": "file.modify", "actor_id": "p1", "parent_event_id": "p1", "attributes": {"entropy_delta": 0.6}},
                {"event_id": "f2", "timestamp_ms": 1_800_000_000_002, "host_id": "host-a", "source": "sensor", "kind": "file.modify", "actor_id": "p1", "parent_event_id": "p1", "attributes": {"entropy_delta": 0.6}},
                {"event_id": "f3", "timestamp_ms": 1_800_000_000_003, "host_id": "host-a", "source": "sensor", "kind": "file.modify", "actor_id": "p1", "parent_event_id": "p1", "attributes": {"entropy_delta": 0.6}}
            ],
        }
        report = analyze_event_document(payload)
        self.assertEqual(report["events_analyzed"], 4)
        self.assertEqual(report["incidents_detected"], 1)
        self.assertEqual(report["enforcement"], "advisory_only")
        self.assertTrue(any("No live kernel" in item for item in report["limitations"]))

    def test_status_does_not_claim_kernel_enforcement(self):
        status = security_status()
        self.assertEqual(status["kernel_enforcement"], "not_implemented")
        self.assertEqual(status["live_sensor_collection"], "not_connected")
        self.assertEqual(status["system_service_policy"], "registered_in_reaper_service_lifecycle_contract")
        self.assertEqual(status["native_service_process"], "not_implemented")


if __name__ == "__main__":
    unittest.main()
