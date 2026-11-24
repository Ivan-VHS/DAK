from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
REAPER_ROOT = ROOT / "projects" / "reaper"
if str(REAPER_ROOT) not in sys.path:
    sys.path.insert(0, str(REAPER_ROOT))

try:
    from reaper.duckos_bridge import REPORT_SCHEMA, audit_snapshot
except ImportError:
    REPORT_SCHEMA = None
    audit_snapshot = None

from duckos.hardware_inventory import collect_host_inventory


@unittest.skipIf(audit_snapshot is None, "the pinned Reaper submodule is not initialized")
class ReaperHardwareContractTests(unittest.TestCase):
    def test_duckos_producer_snapshot_is_accepted_by_reaper_consumer(self):
        with tempfile.TemporaryDirectory() as temporary:
            sysfs = Path(temporary) / "sys"
            pci = sysfs / "bus" / "pci" / "devices"
            usb = sysfs / "bus" / "usb" / "devices"
            pci.mkdir(parents=True)
            usb.mkdir(parents=True)

            device = pci / "0000:01:00.0"
            device.mkdir()
            (device / "vendor").write_text("0x10de\n", encoding="ascii")
            (device / "device").write_text("0x2f05\n", encoding="ascii")
            (device / "class").write_text("0x030000\n", encoding="ascii")

            snapshot = collect_host_inventory(
                sysfs_root=sysfs,
                platform_name="Linux",
                architecture="x86_64",
                captured_at=datetime(2026, 11, 24, 0, 0, tzinfo=timezone.utc),
            )

        report = audit_snapshot(snapshot)

        self.assertEqual(snapshot["schema"], "duckos.hardware-inventory.v1")
        self.assertEqual(report["schema"], REPORT_SCHEMA)
        self.assertTrue(report["valid"])
        self.assertEqual(report["summary"]["total_devices"], 1)
        self.assertEqual(report["summary"]["driver_missing"], 1)
        self.assertEqual(report["summary"]["findings"], 1)
        self.assertFalse(report["execution_performed"])
        self.assertFalse(report["disk_writes_performed"])
        self.assertFalse(report["drivers_changed"])


if __name__ == "__main__":
    unittest.main()
