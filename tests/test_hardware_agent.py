from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent import duckos_hardware_agent as hardware


class LinuxSnapshotTests(unittest.TestCase):
    def _write(self, root: Path, relative: str, content: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_snapshot_collects_platform_evidence_without_guessing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sys_root = root / "sys"
            proc_root = root / "proc"
            self._write(sys_root, "class/dmi/id/bios_vendor", "Example Firmware")
            self._write(sys_root, "class/dmi/id/bios_version", "1.2.3")
            self._write(sys_root, "class/dmi/id/board_name", "Example Board")
            self._write(sys_root, "devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq", "4800000")
            self._write(sys_root, "devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "3600000")
            self._write(sys_root, "devices/system/cpu/cpu0/cpufreq/scaling_governor", "schedutil")
            self._write(proc_root, "cpuinfo", "processor : 0\nmodel name : Example CPU\n")
            self._write(proc_root, "meminfo", "MemTotal:       16384000 kB\nMemAvailable:    8192000 kB\nSwapTotal:       1024 kB\n")

            pci = sys_root / "devices/pci0000:00/0000:01:00.0"
            self._write(pci, "vendor", "0x10de")
            self._write(pci, "device", "0x2684")
            self._write(pci, "class", "0x030000")
            self._write(pci, "label", "Test graphics adapter")
            driver_dir = sys_root / "bus/pci/drivers/nvidia"
            driver_dir.mkdir(parents=True)
            module_dir = sys_root / "module/nvidia"
            module_dir.mkdir(parents=True)
            self._write(module_dir, "version", "555.1")
            (pci / "driver").symlink_to(driver_dir, target_is_directory=True)
            (driver_dir / "module").symlink_to(module_dir, target_is_directory=True)
            pci_bus = sys_root / "bus/pci/devices"
            pci_bus.mkdir(parents=True)
            (pci_bus / "0000:01:00.0").symlink_to(pci, target_is_directory=True)

            usb = sys_root / "devices/platform/usb1/1-1"
            self._write(usb, "idVendor", "046d")
            self._write(usb, "idProduct", "c548")
            self._write(usb, "product", "Test USB receiver")
            usb_bus = sys_root / "bus/usb/devices"
            usb_bus.mkdir(parents=True)
            (usb_bus / "1-1").symlink_to(usb, target_is_directory=True)

            disk = sys_root / "devices/pci0000:00/0000:02:00.0/block/nvme0n1"
            self._write(disk, "size", "2000000")
            self._write(disk, "device/model", "Example NVMe")
            self._write(disk, "removable", "0")
            block_root = sys_root / "block"
            block_root.mkdir(parents=True)
            (block_root / "nvme0n1").symlink_to(disk, target_is_directory=True)

            thermal = sys_root / "devices/virtual/thermal/thermal_zone0"
            self._write(thermal, "type", "cpu-thermal")
            self._write(thermal, "temp", "52500")
            thermal_root = sys_root / "class/thermal"
            thermal_root.mkdir(parents=True)
            (thermal_root / "thermal_zone0").symlink_to(thermal, target_is_directory=True)

            report = hardware.collect_snapshot(sys_root=sys_root, proc_root=proc_root, system="Linux")

            self.assertEqual(report["schema"], hardware.SNAPSHOT_SCHEMA)
            self.assertEqual(report["firmware"]["vendor"], "Example Firmware")
            self.assertEqual(report["cpu"]["name"], "Example CPU")
            self.assertEqual(report["cpu"]["max_clock_mhz"], 4800)
            self.assertEqual(report["memory"]["total_bytes"], 16384000 * 1024)
            self.assertEqual(len(report["gpu"]), 1)
            self.assertIn("PCI\\VEN_10DE&DEV_2684", report["gpu"][0]["hardware_ids"])
            self.assertEqual(report["gpu"][0]["driver"], "nvidia")
            self.assertEqual(report["devices"][-1]["bus"], "USB")
            self.assertEqual(report["storage"][0]["size_bytes"], 2000000 * 512)
            self.assertEqual(report["sensors"][0]["value"], 52.5)

    def test_sysfs_device_links_must_resolve_inside_sys_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            sys_root = root / "sys"
            proc_root = root / "proc"
            outside = root / "outside-device"
            self._write(outside, "vendor", "0x10de")
            self._write(outside, "device", "0x2684")
            self._write(outside, "class", "0x030000")
            bus = sys_root / "bus/pci/devices"
            bus.mkdir(parents=True)
            (bus / "0000:01:00.0").symlink_to(outside, target_is_directory=True)

            report = hardware.collect_snapshot(sys_root=sys_root, proc_root=proc_root, system="Linux")

            self.assertEqual(report["devices"], [])
            self.assertEqual(report["gpu"], [])

    def test_missing_secure_boot_is_unknown_not_false(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = hardware.collect_snapshot(sys_root=root / "sys", proc_root=root / "proc", system="Linux")
            self.assertIsNone(report["firmware"].get("secure_boot"))
            self.assertTrue(any("unknown" in note.lower() for note in report["notes"]))

    def test_non_linux_platform_is_explicitly_limited(self) -> None:
        with mock.patch.object(hardware.platform, "platform", return_value="Test OS"), \
             mock.patch.object(hardware.platform, "release", return_value="1"), \
             mock.patch.object(hardware.platform, "machine", return_value="test"):
            report = hardware.collect_snapshot(system="Darwin")
        self.assertEqual(report["platform"], "Darwin")
        self.assertEqual(report["devices"], [])
        self.assertIn("not implemented", report["notes"][0])


class GuardrailTests(unittest.TestCase):
    def test_driver_export_is_not_available_on_non_windows(self) -> None:
        with mock.patch.object(hardware, "IS_WINDOWS", False):
            with self.assertRaisesRegex(RuntimeError, "only on Windows"):
                hardware.export_windows_driver_store("C:/backup")

    def test_driver_export_refuses_relative_destination(self) -> None:
        with mock.patch.object(hardware, "IS_WINDOWS", True):
            with self.assertRaisesRegex(ValueError, "absolute destination"):
                hardware.export_windows_driver_store("relative-backup")

    def test_driver_export_never_overwrites_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "backup"
            target.mkdir()
            (target / "keep.txt").write_text("keep", encoding="utf-8")
            with mock.patch.object(hardware, "IS_WINDOWS", True):
                with self.assertRaisesRegex(ValueError, "must be empty"):
                    hardware.export_windows_driver_store(target)

    def test_update_guid_is_validated_before_native_operations(self) -> None:
        with mock.patch.object(hardware, "IS_WINDOWS", False):
            with self.assertRaisesRegex(ValueError, "valid Windows Update GUID"):
                hardware.install_windows_driver_update("not-a-guid", "C:/backup")

    def test_windows_driver_installer_never_accepts_eula_automatically(self) -> None:
        self.assertNotIn("AcceptEula", hardware.WINDOWS_INSTALL_SCRIPT)
        self.assertIn("EulaAccepted", hardware.WINDOWS_INSTALL_SCRIPT)

    def test_snapshot_export_is_valid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "snapshot.json"
            hardware._write_json({"schema": hardware.SNAPSHOT_SCHEMA, "value": "ok"}, target)
            parsed = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(parsed["schema"], hardware.SNAPSHOT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
