from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from dak.hardware_inventory import HardwareInventoryError, collect_host_inventory


class HardwareInventoryTests(unittest.TestCase):
    def make_sysfs(self, root: Path) -> Path:
        sysfs = root / "sys"
        pci = sysfs / "bus" / "pci" / "devices"
        usb = sysfs / "bus" / "usb" / "devices"
        pci.mkdir(parents=True)
        usb.mkdir(parents=True)

        gpu = pci / "0000:01:00.0"
        gpu.mkdir()
        (gpu / "vendor").write_text("0x10de\n", encoding="ascii")
        (gpu / "device").write_text("0x2f05\n", encoding="ascii")
        (gpu / "class").write_text("0x030000\n", encoding="ascii")
        driver = sysfs / "bus" / "pci" / "drivers" / "nvidia"
        driver.mkdir(parents=True)
        (gpu / "driver").symlink_to(driver, target_is_directory=True)

        unknown = pci / "0000:02:00.0"
        unknown.mkdir()
        (unknown / "vendor").write_text("0x1234\n", encoding="ascii")
        (unknown / "device").write_text("0xabcd\n", encoding="ascii")
        (unknown / "class").write_text("0x020000\n", encoding="ascii")

        usb_device = usb / "1-1"
        usb_device.mkdir()
        (usb_device / "idVendor").write_text("046d\n", encoding="ascii")
        (usb_device / "idProduct").write_text("c548\n", encoding="ascii")
        (usb_device / "bDeviceClass").write_text("00\n", encoding="ascii")
        interface = usb / "1-1:1.0"
        interface.mkdir()
        usb_driver = sysfs / "bus" / "usb" / "drivers" / "usbhid"
        usb_driver.mkdir(parents=True)
        (interface / "driver").symlink_to(usb_driver, target_is_directory=True)
        return sysfs

    def test_linux_collects_pci_and_usb_driver_state_without_raw_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            sysfs = self.make_sysfs(Path(temporary))
            report = collect_host_inventory(
                sysfs_root=sysfs, platform_name="Linux", architecture="x86_64"
            )
        self.assertEqual(report["schema"], "dak.hardware-inventory.v1")
        self.assertEqual(report["summary"], {
            "total_devices": 3, "driver_bound": 2,
            "driver_missing": 1, "device_problem": 0,
        })
        self.assertEqual({item["bus"] for item in report["devices"]}, {"pci", "usb"})
        self.assertEqual({item["status"] for item in report["devices"]}, {
            "driver_bound", "driver_missing"
        })
        encoded = json.dumps(report)
        self.assertNotIn("0000:01:00.0", encoded)
        self.assertNotIn("1-1:1.0", encoded)
        digest = report["snapshot_sha256"]
        payload = {key: value for key, value in report.items() if key != "snapshot_sha256"}
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
        self.assertEqual(digest, hashlib.sha256(canonical).hexdigest())

    @patch("dak.hardware_inventory.shutil.which", return_value="powershell.exe")
    @patch("dak.hardware_inventory.subprocess.run")
    def test_windows_pnp_inventory_hashes_instance_ids(self, run, _which):
        run.return_value = subprocess.CompletedProcess(
            args=["powershell.exe"], returncode=0,
            stdout=json.dumps([{
                "Class": "Display", "FriendlyName": "Example GPU",
                "InstanceId": r"PCI\VEN_10DE&DEV_2F05", "Status": "OK",
                "Driver": "nvlddmkm",
            }]),
            stderr="",
        )
        report = collect_host_inventory(platform_name="Windows", architecture="amd64")
        self.assertEqual(report["summary"]["driver_bound"], 1)
        self.assertEqual(report["devices"][0]["bus"], "pci")
        self.assertEqual(report["devices"][0]["vendor_id"], "0x10de")
        self.assertNotIn("VEN_10DE", json.dumps(report))
        self.assertFalse(run.call_args.kwargs["shell"])

    def test_unsupported_platform_is_reported(self):
        with self.assertRaisesRegex(HardwareInventoryError, "Linux and Windows"):
            collect_host_inventory(platform_name="Darwin")


if __name__ == "__main__":
    unittest.main()
