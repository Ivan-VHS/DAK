from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from duckos.desktop import (
    ABUpdateError,
    ABUpdateManager,
    AuditLog,
    BenchController,
    BenchError,
    LauncherError,
    LauncherRegistry,
    PackageTrustError,
    PackageTrustStore,
    SerialLogWriter,
    SignatureEvidence,
    load_system_catalog,
    validate_bench_profile,
)
from duckos.desktop.catalog import system_app_ids
from duckos.cli import main


class LauncherTests(unittest.TestCase):
    def test_desktop_catalog_cli_returns_the_versioned_catalogue(self):
        output = StringIO()
        with redirect_stdout(output):
            status = main(["desktop", "catalog"])
        self.assertEqual(status, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["schema"], "duckos.system-applications.v1")
        self.assertEqual(len(report["applications"]), 15)

    def test_launcher_cli_manages_persistent_slot_assignments(self):
        with tempfile.TemporaryDirectory() as temporary:
            state = str(Path(temporary) / "launcher.json")
            output = StringIO()
            with redirect_stdout(output):
                status = main(["desktop", "slots", "--state", state, "assign", "2", "pkg-center"])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(output.getvalue())["shortcut"], "Super+2")
            output = StringIO()
            with redirect_stdout(output):
                status = main(["desktop", "slots", "--state", state, "resolve", "2"])
            self.assertEqual(status, 0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["app_id"], "pkg-center")
            self.assertFalse(report["launch_request"]["process_created"])
    def test_catalog_has_fifteen_stable_unique_system_apps(self):
        catalog = load_system_catalog()
        ids = system_app_ids()
        self.assertEqual(len(catalog["applications"]), 15)
        self.assertEqual(len(ids), 15)
        self.assertEqual(len(set(ids)), 15)
        self.assertEqual(ids[0], "sys-settings")
        self.assertEqual(ids[-1], "term-sysmon")

    def test_numbered_slots_are_stable_and_launch_is_only_a_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "launcher.json"
            registry = LauncherRegistry(path, app_ids=system_app_ids())
            assigned = registry.assign(1, "sys-settings")
            self.assertEqual(assigned["shortcut"], "Super+1")
            self.assertEqual(registry.resolve(1), "sys-settings")
            self.assertIsNone(registry.resolve(2))
            self.assertEqual(registry.list_slots()[1]["slot"], 2)
            with self.assertRaisesRegex(LauncherError, "already assigned"):
                registry.assign(1, "pkg-center")
            with self.assertRaisesRegex(LauncherError, "already assigned"):
                registry.assign(2, "sys-settings")
            request = registry.prepare_launch_request(1)
            self.assertEqual(request["app_id"], "sys-settings")
            self.assertFalse(request["process_created"])
            self.assertFalse(request["shell_command_created"])
            reopened = LauncherRegistry(path, app_ids=system_app_ids())
            self.assertEqual(reopened.resolve(1), "sys-settings")

    def test_slot_replacement_and_unassignment_are_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry = LauncherRegistry(
                Path(temporary) / "launcher.json", app_ids=system_app_ids()
            )
            registry.assign(1, "sys-settings")
            with self.assertRaises(LauncherError):
                registry.assign(1, "pkg-center")
            registry.assign(1, "pkg-center", replace=True)
            self.assertEqual(registry.resolve(1), "pkg-center")
            self.assertTrue(registry.unassign(1))
            self.assertIsNone(registry.resolve(1))


class PackageTrustTests(unittest.TestCase):
    def test_unsigned_binary_requires_explicit_hash_bound_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "tool.bin"
            package.write_bytes(b"unsigned build")
            trust = PackageTrustStore(root / "trust.json")
            initial = trust.verify(package)
            self.assertEqual(initial["status"], "unknown")
            self.assertFalse(initial["launch_allowed"])
            with self.assertRaises(PackageTrustError):
                trust.approve_unsigned(package, confirmed=False)
            approval = trust.approve_unsigned(package, confirmed=True)
            self.assertEqual(approval["approval_scope"], "exact-sha256")
            approved = trust.verify(package)
            self.assertEqual(approved["status"], "local-approved")
            self.assertTrue(approved["launch_allowed"])
            package.write_bytes(b"changed build")
            changed = trust.verify(package, expected_sha256=approval["sha256"])
            self.assertEqual(changed["status"], "blocked")
            self.assertEqual(changed["reason"], "sha256-mismatch")
            self.assertFalse(changed["launch_allowed"])

    def test_symbolic_link_package_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            original = root / "original.bin"
            original.write_bytes(b"payload")
            link = root / "link.bin"
            link.symlink_to(original)
            with self.assertRaises(PackageTrustError):
                PackageTrustStore(root / "trust.json").verify(link)


class FakeImageBackend:
    def __init__(self):
        self.written = None
        self.next_boot = None

    def write_slot(self, slot, image_path, expected_sha256):
        self.written = (slot, image_path.read_bytes(), expected_sha256)

    def verify_slot(self, slot, expected_sha256):
        return self.written is not None and self.written[0] == slot and self.written[2] == expected_sha256

    def set_next_boot(self, slot):
        self.next_boot = slot


class ABUpdateTests(unittest.TestCase):
    def make_image(self, root):
        path = root / "duckos.img"
        path.write_bytes(b"verified test image")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return path, digest

    def test_plan_requires_hash_and_verified_signature_and_preserves_active_slot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image, digest = self.make_image(root)
            manager = ABUpdateManager(root / "slots.json")
            with self.assertRaises(ABUpdateError):
                manager.plan_update(
                    image, target_slot="B", image_version="1.1",
                    expected_sha256=digest, signature=None,
                )
            plan = manager.plan_update(
                image, target_slot="B", image_version="1.1",
                expected_sha256=digest,
                signature=SignatureEvidence(True, "release-key-01"),
            )
            self.assertEqual(plan["target_slot"], "B")
            self.assertFalse(plan["write_performed"])
            self.assertFalse(plan["boot_target_changed"])
            self.assertEqual(manager.status()["active_slot"], "A")

    def test_activation_requires_native_backend_and_confirmed_boot_updates_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image, digest = self.make_image(root)
            manager = ABUpdateManager(root / "slots.json")
            evidence = SignatureEvidence(True, "release-key-01")
            with self.assertRaisesRegex(ABUpdateError, "no native"):
                manager.activate(
                    image, target_slot="B", image_version="1.1",
                    expected_sha256=digest, signature=evidence,
                )
            backend = FakeImageBackend()
            manager = ABUpdateManager(root / "slots.json", backend)
            result = manager.activate(
                image, target_slot="B", image_version="1.1",
                expected_sha256=digest, signature=evidence,
            )
            self.assertTrue(result["write_performed"])
            self.assertEqual(backend.next_boot, "B")
            self.assertEqual(manager.status()["pending_slot"], "B")
            confirmed = manager.confirm_boot("B")
            self.assertEqual(confirmed["active_slot"], "B")
            self.assertIsNone(confirmed["pending_slot"])
            self.assertEqual(confirmed["slots"]["B"]["state"], "confirmed")

    def test_boot_failure_selects_previous_confirmed_slot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            image, digest = self.make_image(root)
            backend = FakeImageBackend()
            manager = ABUpdateManager(root / "slots.json", backend)
            manager.activate(
                image, target_slot="B", image_version="1.1",
                expected_sha256=digest,
                signature=SignatureEvidence(True, "release-key-01"),
            )
            failed = manager.record_boot_failure("B")
            self.assertEqual(backend.next_boot, "A")
            self.assertEqual(failed["active_slot"], "A")
            self.assertEqual(failed["slots"]["B"]["state"], "failed")
            self.assertIsNone(failed["pending_slot"])


def sample_profile():
    return {
        "schema": "duckos.bench-profile.v1",
        "board_id": "duckos_fixture_rev_a",
        "fixture_slots": ["A", "B"],
        "serial_ports": ["/dev/ttyUSB0"],
        "max_telemetry_age_seconds": 5,
        "rails": [{
            "id": "main_12v",
            "min_voltage_v": 11.4,
            "max_voltage_v": 12.6,
            "max_current_a": 5.0,
            "max_temperature_c": 75.0,
            "cooldown_temperature_c": 45.0,
        }],
        "buses": [{
            "id": "pcie_root_0", "kind": "pcie", "max_link_width": 16,
            "max_link_speed_gbps": 32.0, "must_be_present": True,
        }],
        "accelerators": [{
            "id": "npu0", "kind": "npu", "max_temperature_c": 80.0,
            "max_utilization_percent": 100.0, "must_be_present": True,
        }],
        "probes": [{
            "id": "probe_temp", "unit": "celsius", "min_value": 0.0,
            "max_value": 70.0, "max_age_seconds": 5.0, "must_be_present": True,
        }],
        "tests": [{"id": "smoke", "max_duration_seconds": 30}],
    }


class FakeBenchAdapter:
    def __init__(
        self, *, board_id="duckos_fixture_rev_a", voltage=12.0, temperature=30.0,
        bus_status="ok", npu_temperature=38.0, probe_value=25.0,
    ):
        self.board_id = board_id
        self.voltage = voltage
        self.temperature = temperature
        self.bus_status = bus_status
        self.npu_temperature = npu_temperature
        self.probe_value = probe_value
        self.connected = True
        self.emergency_calls = 0
        self.started = None
        self.stopped = False

    def is_connected(self):
        return self.connected

    def discover(self):
        return {"board_id": self.board_id}

    def read_telemetry(self):
        return {
            "captured_at": 1000.0,
            "rails": {
                "main_12v": {
                    "voltage_v": self.voltage,
                    "current_a": 1.0,
                    "temperature_c": self.temperature,
                }
            },
            "buses": {
                "pcie_root_0": {
                    "status": self.bus_status,
                    "link_width": 16,
                    "link_speed_gbps": 32.0,
                }
            },
            "accelerators": {
                "npu0": {
                    "present": True,
                    "temperature_c": self.npu_temperature,
                    "utilization_percent": 40.0,
                }
            },
            "probes": {
                "probe_temp": {
                    "value": self.probe_value,
                    "captured_at": 1000.0,
                }
            },
        }

    def start_test(self, test_id, fixture_slot, duration_seconds):
        self.started = (test_id, fixture_slot, duration_seconds)

    def stop_test(self):
        self.stopped = True

    def emergency_disable(self):
        self.emergency_calls += 1


class BenchTests(unittest.TestCase):
    def test_profile_validation_rejects_unsafe_voltage_limits_and_malformed_slots(self):
        profile = sample_profile()
        self.assertEqual(validate_bench_profile(profile)["board_id"], "duckos_fixture_rev_a")
        profile["rails"][0]["max_voltage_v"] = profile["rails"][0]["min_voltage_v"]
        with self.assertRaises(BenchError):
            validate_bench_profile(profile)
        profile = sample_profile()
        profile["fixture_slots"] = [{}]
        with self.assertRaises(BenchError):
            validate_bench_profile(profile)

    def test_bench_state_machine_requires_fresh_safe_telemetry(self):
        profile = sample_profile()
        adapter = FakeBenchAdapter()
        controller = BenchController(profile, adapter, clock=lambda: 1000.0)
        self.assertEqual(controller.connect()["state"], "safe-idle")
        self.assertEqual(controller.arm()["state"], "armed")
        running = controller.start_test("smoke", duration_seconds=10, fixture_slot="B")
        self.assertEqual(running["state"], "running")
        self.assertEqual(running["fixture_slot"], "B")
        self.assertEqual(adapter.started, ("smoke", "B", 10))
        self.assertEqual(controller.stop_test()["state"], "cooling")
        self.assertEqual(controller.finish_cooling()["state"], "safe-idle")
        self.assertTrue(controller.status()["hardware_connected"])
        self.assertFalse(controller.status()["register_write_api_exposed"])
        self.assertEqual(controller.status()["power_controller_backend"], "adapter")

    def test_cooling_waits_for_the_configured_temperature_without_marking_a_fault(self):
        adapter = FakeBenchAdapter(temperature=50.0)
        controller = BenchController(sample_profile(), adapter, clock=lambda: 1000.0)
        controller.connect()
        controller.arm()
        controller.start_test("smoke", duration_seconds=10, fixture_slot="A")
        controller.stop_test()
        with self.assertRaisesRegex(BenchError, "cooling threshold"):
            controller.finish_cooling()
        self.assertEqual(controller.status()["state"], "cooling")
        self.assertEqual(adapter.emergency_calls, 0)
        adapter.temperature = 30.0
        self.assertEqual(controller.finish_cooling()["state"], "safe-idle")

    def test_bus_npu_and_probe_interlocks_are_checked_before_arming(self):
        cases = [
            (FakeBenchAdapter(bus_status="degraded"), "bus status"),
            (FakeBenchAdapter(npu_temperature=95.0), "accelerator temperature"),
            (FakeBenchAdapter(probe_value=95.0), "probe reading"),
        ]
        for adapter, expected_message in cases:
            with self.subTest(expected_message=expected_message):
                controller = BenchController(sample_profile(), adapter, clock=lambda: 1000.0)
                controller.connect()
                with self.assertRaisesRegex(BenchError, expected_message):
                    controller.arm()
                self.assertEqual(controller.status()["state"], "fault")
                self.assertEqual(adapter.emergency_calls, 1)

    def test_out_of_range_telemetry_faults_and_calls_emergency_disable(self):
        adapter = FakeBenchAdapter(voltage=13.2)
        controller = BenchController(sample_profile(), adapter, clock=lambda: 1000.0)
        controller.connect()
        with self.assertRaisesRegex(BenchError, "voltage"):
            controller.arm()
        self.assertEqual(controller.status()["state"], "fault")
        self.assertEqual(adapter.emergency_calls, 1)

    def test_board_identity_must_match_selected_profile(self):
        adapter = FakeBenchAdapter(board_id="other_board")
        controller = BenchController(sample_profile(), adapter, clock=lambda: 1000.0)
        with self.assertRaisesRegex(BenchError, "does not match"):
            controller.connect()
        self.assertEqual(controller.status()["state"], "fault")
        self.assertEqual(adapter.emergency_calls, 1)

    def test_absent_hardware_adapter_keeps_access_disabled(self):
        controller = BenchController(sample_profile())
        with self.assertRaisesRegex(BenchError, "no native bench adapter"):
            controller.connect()
        self.assertFalse(controller.status()["hardware_connected"])
        self.assertEqual(controller.status()["power_controller_backend"], "unavailable")


class AuditTests(unittest.TestCase):
    def test_audit_cli_verifies_serial_journal(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "audit.jsonl"
            AuditLog(path).append("bench.connected", {"board_id": "duckos_fixture_rev_a"})
            output = StringIO()
            with redirect_stdout(output):
                status = main(["desktop", "audit-verify", str(path)])
            self.assertEqual(status, 0)
            report = json.loads(output.getvalue())
            self.assertTrue(report["valid"])
            self.assertEqual(report["entries"], 1)

    def test_audit_chain_and_serial_log_redact_secrets(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = AuditLog(Path(temporary) / "audit.jsonl")
            log.append("bench.test_started", {"test_id": "smoke"})
            writer = SerialLogWriter(log, allowed_ports=["/dev/ttyUSB0"])
            writer.append(
                session_id="session-01", port="/dev/ttyUSB0",
                fixture_slot="A", line="boot ok password=hunter2 temperature=31",
            )
            with self.assertRaisesRegex(ValueError, "not allowed"):
                writer.append(
                    session_id="session-01", port="/dev/ttyACM0",
                    fixture_slot="A", line="unexpected port",
                )
            report = log.verify()
            self.assertTrue(report["valid"])
            self.assertEqual(report["entries"], 2)
            text = Path(temporary, "audit.jsonl").read_text(encoding="utf-8")
            self.assertIn("password=[REDACTED]", text)
            self.assertNotIn("hunter2", text)

    def test_audit_chain_detects_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "audit.jsonl"
            log = AuditLog(path)
            log.append("bench.connected", {"board_id": "duckos_fixture_rev_a"})
            record = json.loads(path.read_text(encoding="utf-8"))
            record["details"]["board_id"] = "tampered"
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hash chain"):
                log.verify()


if __name__ == "__main__":
    unittest.main()
