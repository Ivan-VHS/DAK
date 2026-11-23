from __future__ import annotations

import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from duckos.executable import inspect_executable
from duckos.runtime import (
    AppStore,
    AppStoreError,
    RuntimeManager,
    RuntimePermissionError,
    RuntimeUnavailable,
    _validate_relative_path,
)


def pe_fixture(*, dll: bool = False) -> bytes:
    image = bytearray(256)
    image[0:2] = b"MZ"
    struct.pack_into("<I", image, 0x3C, 64)
    image[64:68] = b"PE\x00\x00"
    struct.pack_into("<H", image, 68, 0x8664)
    struct.pack_into("<H", image, 84, 0xF0)
    struct.pack_into("<H", image, 86, 0x2000 if dll else 0x0022)
    struct.pack_into("<H", image, 88, 0x020B)
    struct.pack_into("<H", image, 88 + 68, 3)
    return bytes(image)


def write_pe(path: Path, *, dll: bool = False) -> Path:
    path.write_bytes(pe_fixture(dll=dll))
    return path


class ExecutableHeaderTests(unittest.TestCase):
    def test_recognizes_pe_architecture_and_subsystem(self):
        with tempfile.TemporaryDirectory() as directory:
            target = write_pe(Path(directory) / "game.exe")
            result = inspect_executable(target)
            self.assertEqual(result["format"], "windows-pe")
            self.assertEqual(result["architecture"], "x86_64")
            self.assertEqual(result["bits"], 64)
            self.assertEqual(result["subsystem"], 3)
            self.assertFalse(result["is_dll"])

    def test_rejects_dll_as_a_launchable_application(self):
        with tempfile.TemporaryDirectory() as directory:
            target = write_pe(Path(directory) / "library.dll", dll=True)
            self.assertTrue(inspect_executable(target)["is_dll"])

    def test_distinguishes_dos_mz_from_windows_pe(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "game.exe"
            image = bytearray(96)
            image[:2] = b"MZ"
            struct.pack_into("<I", image, 0x3C, 80)
            target.write_bytes(image)
            self.assertEqual(inspect_executable(target)["format"], "dos-mz")

    def test_identifies_com_candidate_by_extension(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "GAME.COM"
            target.write_bytes(b"\x90\x90\xCD\x20")
            self.assertEqual(inspect_executable(target)["format"], "dos-com")

    def test_rejects_unknown_and_symlink_images(self):
        with tempfile.TemporaryDirectory() as directory:
            unknown = Path(directory) / "unknown.exe"
            unknown.write_bytes(b"not an executable")
            with self.assertRaises(ValueError):
                inspect_executable(unknown)
            link = Path(directory) / "linked.exe"
            try:
                link.symlink_to(unknown)
            except (OSError, NotImplementedError):
                self.skipTest("symbolic links are unavailable")
            with self.assertRaises(ValueError):
                inspect_executable(link)


class ApplicationStoreTests(unittest.TestCase):
    def test_imports_and_reverifies_a_single_pe_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = write_pe(root / "game.exe")
            store = AppStore(root / "duckos-state")
            app = store.import_source(source, display_name="Example Game")
            self.assertEqual(app["name"], "Example Game")
            self.assertEqual(app["executable"]["format"], "windows-pe")
            self.assertEqual(app["trust_state"], "untrusted")
            verified = store.get_app(app["id"])
            self.assertEqual(verified["entrypoint"], "game.exe")

    def test_tampered_payload_fails_integrity_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = write_pe(root / "game.exe")
            store = AppStore(root / "state")
            app = store.import_source(source)
            payload = store.apps / app["id"] / "game.exe"
            payload.write_bytes(payload.read_bytes() + b"tampered")
            with self.assertRaises(AppStoreError):
                store.get_app(app["id"])

    def test_zip_package_requires_entrypoint_when_multiple_executables_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "game.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("Game/game.exe", pe_fixture())
                bundle.writestr("Game/setup.exe", pe_fixture())
                bundle.writestr("Game/data/config.ini", "quality=high")
            store = AppStore(root / "state")
            with self.assertRaises(AppStoreError):
                store.import_source(archive)
            app = store.import_source(archive, entrypoint="Game/game.exe")
            self.assertEqual(app["entrypoint"], "Game/game.exe")
            self.assertEqual(len(app["files"]), 3)

    def test_zip_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("../escape.exe", pe_fixture())
                bundle.writestr("safe/game.exe", pe_fixture())
            store = AppStore(root / "state")
            with self.assertRaises(AppStoreError):
                store.import_source(archive)

    def test_relative_package_paths_are_bounded_and_canonical(self):
        self.assertEqual(_validate_relative_path("bin/game.exe"), "bin/game.exe")
        for invalid in ("", "../game.exe", "/game.exe", "C:/game.exe", "bin\\game.exe", "bin/../game.exe"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(AppStoreError):
                    _validate_relative_path(invalid)

    def test_registers_guest_disk_with_integrity_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            disk = root / "windows.qcow2"
            disk.write_bytes(b"Q" * (1024 * 1024))
            store = AppStore(root / "state")
            record = store.register_vm("windows-11", disk, memory_mb=4096, cpus=2)
            self.assertEqual(record["name"], "windows-11")
            self.assertEqual(store.get_vm("windows-11")["disk_format"], "qcow2")
            disk.write_bytes(b"X" * (1024 * 1024))
            with self.assertRaises(RuntimeError):
                store.get_vm("windows-11")


class RuntimeManagerTests(unittest.TestCase):
    def test_launch_requires_explicit_user_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = write_pe(root / "game.exe")
            manager = RuntimeManager(AppStore(root / "state"))
            app = manager.import_app(source)
            with self.assertRaises(RuntimePermissionError):
                manager.launch_app(app["id"], approved=False)

    def test_native_pe_adapter_is_only_available_on_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = RuntimeManager(AppStore(Path(directory) / "state"))
            native = next(item for item in manager.detect_runtimes() if item["id"] == "native-pe")
            self.assertEqual(native["available"], __import__("os").name == "nt")
            if __import__("os").name != "nt":
                with self.assertRaises(RuntimeUnavailable):
                    manager._select_runtime(
                        {"format": "windows-pe", "is_dll": False}, "native-pe"
                    )

    def test_process_creation_uses_an_argument_vector_without_a_shell(self):
        class FakeProcess:
            pid = 321
            returncode = None

            @staticmethod
            def poll():
                return None

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = write_pe(root / "game.exe")
            manager = RuntimeManager(AppStore(root / "state"))
            app = manager.import_app(source)
            manager._select_runtime = lambda info, runtime: {
                "id": "native-pe",
                "kind": "windows-pe",
                "available": True,
                "requires_unisolated_approval": True,
                "isolation": "host process",
            }
            calls = {}

            def fake_popen(command, **kwargs):
                calls["command"] = command
                calls.update(kwargs)
                return FakeProcess()

            with patch("duckos.runtime.subprocess.Popen", side_effect=fake_popen):
                result = manager.launch_app(
                    app["id"],
                    approved=True,
                    allow_unisolated=True,
                    arguments=["--windowed", "two words"],
                )
            self.assertFalse(calls["shell"])
            self.assertIsInstance(calls["command"], list)
            self.assertEqual(calls["command"][-2:], ["--windowed", "two words"])
            self.assertEqual(result["host_pid"], 321)

    def test_vm_guest_launch_requires_unisolated_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            disk = root / "guest.qcow2"
            disk.write_bytes(b"Q" * 1024 * 1024)
            manager = RuntimeManager(AppStore(root / "state"))
            manager.store.register_vm("guest", disk)
            with self.assertRaises(RuntimePermissionError):
                manager.launch_vm("guest", approved=True, allow_unisolated=False)


if __name__ == "__main__":
    unittest.main()
