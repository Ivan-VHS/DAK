from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from duckos.gaming import (
    GamingPolicyError,
    assess_capabilities,
    load_rule_catalog,
    plan_session_transition,
)


class GamingPolicyTests(unittest.TestCase):
    def test_catalog_contains_exactly_66_ordered_rules(self):
        catalog = load_rule_catalog()
        self.assertEqual(catalog["rule_count"], 66)
        self.assertEqual([rule["number"] for rule in catalog["rules"]], list(range(1, 67)))
        self.assertEqual(len({rule["id"] for rule in catalog["rules"]}), 66)

    def test_package_catalog_matches_the_repository_catalog(self):
        root = Path(__file__).resolve().parents[1] / "catalogs" / "game-performance-rules.v1.json"
        packaged = Path(__file__).resolve().parents[1] / "duckos" / "gaming" / "game-performance-rules.v1.json"
        self.assertEqual(packaged.read_bytes(), root.read_bytes())

    def test_rejects_duplicate_or_missing_rule_numbers(self):
        catalog = load_rule_catalog()
        catalog["rules"][-1]["number"] = 65
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "rules.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            with self.assertRaises(GamingPolicyError):
                load_rule_catalog(path)

    def test_missing_providers_are_never_reported_as_supported(self):
        report = assess_capabilities({})
        self.assertEqual(report["rule_count"], 66)
        self.assertEqual(report["summary"]["available"], 0)
        self.assertEqual(report["summary"]["unavailable"], 66)
        self.assertFalse(report["system_settings_changed"])

    def test_accepts_federated_oplage_evidence_document(self):
        from duckos.gaming import assess_capability_document
        report = assess_capability_document({
            "schema": "oplague.duckos-gaming-evidence.v1",
            "system_mutations_performed": False,
            "providers": {
                "process_catalog": {
                    "available": True,
                    "provider": "OPlague",
                    "version": "read-only",
                    "reason": None,
                }
            },
        })
        self.assertEqual(report["rules"][0]["status"], "partial")
        self.assertFalse(report["system_settings_changed"])

    def test_accepts_pytyliki_provider_evidence_document(self):
        from duckos.gaming import assess_capability_document
        report = assess_capability_document({
            "schema": "duckos.gaming-provider-evidence.v1",
            "system_mutations_performed": False,
            "evidence_scope": "whole_host",
            "capabilities": {
                "cpu_telemetry": {
                    "available": True, "provider": "Pytyliki", "version": "measured", "reason": None
                }
            },
        })
        cpu_rule = next(item for item in report["rules"] if item["domain"] == "cpu")
        self.assertEqual(cpu_rule["status"], "partial")

    def test_provider_evidence_controls_readiness(self):
        catalog = load_rule_catalog()
        required = catalog["rules"][0]["providers"]
        report = assess_capabilities({name: True for name in required}, catalog=catalog)
        first = report["rules"][0]
        self.assertEqual(first["status"], "available")
        self.assertTrue(all(item["available"] for item in first["evidence"]))
        self.assertFalse(first["action_applied"])

    def test_rejects_unknown_provider_and_malformed_availability(self):
        with self.assertRaises(GamingPolicyError):
            assess_capabilities({"invented_control": True})
        with self.assertRaises(GamingPolicyError):
            assess_capabilities({"process_catalog": {"available": "yes"}})

    def test_builds_the_session_profile_expected_by_reaper(self):
        from duckos.gaming import build_session_profile
        profile = build_session_profile(
            "sample-game", engine="directx12", worker_count=8,
            multithreaded=True, audio_enabled=True,
        )
        self.assertEqual(profile["schema"], "duckos.gaming-session-profile.v1")
        self.assertEqual(profile["worker_count"], 8)
        self.assertFalse(profile["execution_performed"])
        self.assertIn("GPR-13", profile["source_rules"])

    def test_session_profile_builder_rejects_unsafe_inputs(self):
        from duckos.gaming import build_session_profile
        with self.assertRaises(GamingPolicyError):
            build_session_profile("../escape")
        with self.assertRaises(GamingPolicyError):
            build_session_profile("sample", worker_count=1000)

    def test_session_lifecycle_is_explicit_and_non_executing(self):
        starting = plan_session_transition(
            "idle", "game_detected", profile_id="sample-game", process_identity="sample.exe"
        )
        self.assertEqual(starting["to"], "starting")
        active = plan_session_transition("starting", "snapshot_created", snapshot_id="snapshot-1")
        self.assertEqual(active["to"], "active")
        background = plan_session_transition("active", "foreground_lost")
        self.assertEqual(background["to"], "background")
        restoring = plan_session_transition("background", "game_exited")
        self.assertEqual(restoring["to"], "restoring")
        restored = plan_session_transition("restoring", "restore_confirmed")
        self.assertEqual(restored["to"], "idle")
        self.assertFalse(restored["execution_performed"])

    def test_duplicate_events_are_idempotent(self):
        result = plan_session_transition("background", "foreground_lost")
        self.assertTrue(result["idempotent"])
        self.assertEqual(result["actions"], [])

    def test_rejects_out_of_order_restore_and_unsafe_identity(self):
        with self.assertRaises(GamingPolicyError):
            plan_session_transition("idle", "game_exited")
        with self.assertRaises(GamingPolicyError):
            plan_session_transition("idle", "game_detected", profile_id="../escape", process_identity="game.exe")


if __name__ == "__main__":
    unittest.main()
