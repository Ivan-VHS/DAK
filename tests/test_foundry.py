from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.foundry import build_runbook, collect_foundry_snapshot, write_snapshot


def desktop_fixture(memory: float = 42.0, cpu: float = 18.0) -> dict:
    return {
        "schema": "duckos.desktop-audit.v1",
        "desktop": {"count": 2, "items": []},
        "startup": {"count": 1, "entries": []},
        "resources": {
            "memory_used_percent": memory,
            "cpu_percent": cpu,
            "memory_total_bytes": 16_000,
            "memory_available_bytes": 8_000,
        },
        "recommendations": [],
    }


class FoundrySnapshotTests(unittest.TestCase):
    @patch("duckos.foundry.detect_runtimes", return_value={
        "schema": "duckos.duckbridge-runtimes.v1",
        "runtimes": [{"id": "wine", "available": True}],
    })
    @patch("duckos.foundry.collect_host_inventory", return_value={
        "schema": "duckos.hardware-inventory.v1",
        "summary": {
            "total_devices": 3,
            "driver_bound": 2,
            "driver_missing": 1,
            "device_problem": 0,
        },
        "devices": [{"identity_sha256": "a" * 64, "status": "driver_missing"}],
    })
    @patch("duckos.foundry.DesktopService")
    def test_snapshot_correlates_existing_read_only_sources(self, desktop, _inventory, _runtimes):
        desktop.return_value.audit.return_value = desktop_fixture()
        snapshot = collect_foundry_snapshot()
        self.assertEqual(snapshot["schema"], "duckos.foundry.snapshot.v1")
        self.assertEqual(snapshot["state"], "nominal")
        self.assertEqual(snapshot["metrics"]["devices_total"], 3)
        self.assertEqual(snapshot["metrics"]["compatibility_runtimes"], 1)
        self.assertTrue(snapshot["execution_policy"]["read_only"])
        self.assertFalse(snapshot["execution_policy"]["network_access"])
        self.assertFalse(snapshot["execution_policy"]["arbitrary_user_commands_started"])
        self.assertFalse(snapshot["execution_policy"]["processes_terminated"])
        self.assertFalse(snapshot["execution_policy"]["drivers_changed"])
        self.assertFalse(snapshot["execution_policy"]["external_machinery_control"])

    @patch("duckos.foundry.detect_runtimes", return_value={"runtimes": []})
    @patch("duckos.foundry.collect_host_inventory", return_value={
        "summary": {"total_devices": 1, "driver_missing": 0, "device_problem": 1},
        "devices": [],
    })
    @patch("duckos.foundry.DesktopService")
    def test_snapshot_raises_attention_for_pressure_and_device_faults(self, desktop, _inventory, _runtimes):
        desktop.return_value.audit.return_value = desktop_fixture(memory=96.0, cpu=99.0)
        snapshot = collect_foundry_snapshot()
        self.assertEqual(snapshot["state"], "critical")
        ids = {item["id"] for item in snapshot["findings"]}
        self.assertIn("memory-pressure", ids)
        self.assertIn("cpu-pressure", ids)
        self.assertIn("device-problems", ids)

    @patch("duckos.foundry.detect_runtimes", side_effect=OSError("not available"))
    @patch("duckos.foundry.collect_host_inventory", side_effect=OSError("no sysfs"))
    @patch("duckos.foundry.DesktopService")
    def test_unavailable_optional_sources_are_reported_without_failing(self, desktop, _inventory, _runtimes):
        desktop.return_value.audit.return_value = desktop_fixture()
        snapshot = collect_foundry_snapshot()
        self.assertEqual(snapshot["state"], "nominal")
        self.assertEqual(len(snapshot["collection_errors"]), 2)
        self.assertEqual(snapshot["modules"][2]["state"], "unavailable")
        self.assertEqual(snapshot["modules"][3]["state"], "unavailable")

    @patch("duckos.foundry.detect_runtimes", side_effect=AssertionError("must not run"))
    @patch("duckos.foundry.collect_host_inventory", side_effect=AssertionError("must not run"))
    @patch("duckos.foundry.DesktopService")
    def test_optional_collectors_can_be_skipped(self, desktop, _inventory, _runtimes):
        desktop.return_value.audit.return_value = desktop_fixture()
        snapshot = collect_foundry_snapshot(include_devices=False, include_runtimes=False)
        self.assertEqual(snapshot["modules"][2]["state"], "not_requested")
        self.assertEqual(snapshot["modules"][3]["state"], "not_requested")

    def test_runbook_is_a_manual_checklist_not_an_execution_plan(self):
        runbook = build_runbook("incident", {
            "captured_at": "2026-11-23T21:00:00Z",
            "findings": [{"id": "memory-pressure"}],
        })
        self.assertEqual(runbook["schema"], "duckos.foundry.runbook.v1")
        self.assertEqual(runbook["linked_snapshot"], "2026-11-23T21:00:00Z")
        self.assertIn("memory-pressure", runbook["open_findings"])
        self.assertTrue(all(step["execution"] == "manual_only" for step in runbook["steps"]))
        self.assertTrue(all(step["destructive"] is False for step in runbook["steps"]))
        self.assertFalse(runbook["execution_policy"]["automatic_execution"])
        with self.assertRaises(ValueError):
            build_runbook("unknown")

    def test_report_export_uses_exclusive_create_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "report.json"
            snapshot = {"schema": "duckos.foundry.snapshot.v1", "value": 7}
            result = write_snapshot(target, snapshot)
            self.assertEqual(result["overwritten"], False)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), snapshot)
            with self.assertRaises(FileExistsError):
                write_snapshot(target, snapshot)
            if hasattr(target, "symlink_to"):
                link = Path(temporary) / "report-link.json"
                try:
                    link.symlink_to(target)
                except (OSError, NotImplementedError):
                    pass
                else:
                    with self.assertRaises(ValueError):
                        write_snapshot(link, snapshot)


if __name__ == "__main__":
    unittest.main()
