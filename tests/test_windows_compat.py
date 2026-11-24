from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from duckos.cli import main
from duckos.compat import (
    PEFormatError, PrefixError, compatibility_status, create_prefix,
    diagnose_binary, inspect_pe_bytes, plan_launch, read_prefix,
)


def minimal_pe64() -> bytes:
    data = bytearray(0x400)
    data[:2] = b"MZ"
    data[0x3C:0x40] = (0x80).to_bytes(4, "little")
    data[0x80:0x84] = b"PE\0\0"
    coff = 0x84
    data[coff:coff + 2] = (0x8664).to_bytes(2, "little")
    data[coff + 2:coff + 4] = (1).to_bytes(2, "little")
    data[coff + 16:coff + 18] = (0xF0).to_bytes(2, "little")
    data[coff + 18:coff + 20] = (0x0002).to_bytes(2, "little")
    opt = coff + 20
    data[opt:opt + 2] = (0x20B).to_bytes(2, "little")
    data[opt + 16:opt + 20] = (0x1000).to_bytes(4, "little")
    data[opt + 24:opt + 32] = (0x140000000).to_bytes(8, "little")
    data[opt + 56:opt + 60] = (0x2000).to_bytes(4, "little")
    data[opt + 60:opt + 64] = (0x200).to_bytes(4, "little")
    data[opt + 68:opt + 70] = (3).to_bytes(2, "little")
    data[opt + 108:opt + 112] = (16).to_bytes(4, "little")
    data[opt + 120:opt + 128] = (0x1000).to_bytes(4, "little") + (40).to_bytes(4, "little")
    section = opt + 0xF0
    data[section:section + 8] = b".rdata\0\0"
    data[section + 8:section + 12] = (0x200).to_bytes(4, "little")
    data[section + 12:section + 16] = (0x1000).to_bytes(4, "little")
    data[section + 16:section + 20] = (0x200).to_bytes(4, "little")
    data[section + 20:section + 24] = (0x200).to_bytes(4, "little")
    data[section + 36:section + 40] = (0x40000040).to_bytes(4, "little")
    data[0x200:0x204] = (0x1080).to_bytes(4, "little")
    data[0x20C:0x210] = (0x1040).to_bytes(4, "little")
    data[0x210:0x214] = (0x1080).to_bytes(4, "little")
    data[0x240:0x24D] = b"KERNEL32.dll\0"
    return bytes(data)


class WindowsCompatibilityTests(unittest.TestCase):
    def test_inspects_pe64_and_import_table_without_execution(self):
        report = inspect_pe_bytes(minimal_pe64(), file_name="sample.exe")
        self.assertEqual(report["format"], "PE32+")
        self.assertEqual(report["architecture"], "x86_64")
        self.assertEqual(report["subsystem"], "windows_console")
        self.assertEqual(report["imports"], ["KERNEL32.dll"])
        self.assertTrue(report["inspection_only"])
        self.assertFalse(report["execution_performed"])

    def test_rejects_truncated_and_invalid_images(self):
        with self.assertRaises(PEFormatError):
            inspect_pe_bytes(b"MZ" + bytes(40))
        broken = bytearray(minimal_pe64())
        broken[0x3C:0x40] = (0x3FFFFFFF).to_bytes(4, "little")
        with self.assertRaises(PEFormatError):
            inspect_pe_bytes(bytes(broken))

    def test_pe_file_reader_rejects_symlink_and_special_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.exe"
            source.write_bytes(minimal_pe64())
            linked = root / "linked.exe"
            try:
                linked.symlink_to(source)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are not available on this host")
            with self.assertRaisesRegex(PEFormatError, "symbolic link"):
                from duckos.compat.pe import inspect_pe_file
                inspect_pe_file(linked)

            if hasattr(os, "mkfifo"):
                fifo = root / "named-pipe.exe"
                os.mkfifo(fifo)
                with self.assertRaisesRegex(PEFormatError, "regular file"):
                    inspect_pe_file(fifo)

    def test_pe_file_reader_enforces_limit_during_read(self):
        from duckos.compat import pe as pe_module
        from duckos.compat.pe import inspect_pe_file

        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / "oversized.exe"
            candidate.write_bytes(b"MZ" + bytes(128))
            previous_limit = pe_module.MAX_FILE_BYTES
            pe_module.MAX_FILE_BYTES = 64
            try:
                with self.assertRaisesRegex(PEFormatError, "64-byte inspection limit"):
                    inspect_pe_file(candidate)
            finally:
                pe_module.MAX_FILE_BYTES = previous_limit

    def test_creates_isolated_prefix_and_validates_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            manifest = create_prefix(temporary, "sample-game", architecture="x86_64")
            root = Path(manifest["path"])
            self.assertTrue((root / "drive_c/windows/system32").is_dir())
            self.assertTrue((root / "drive_c/users/user/Saved Games").is_dir())
            self.assertFalse(manifest["execution_enabled"])
            self.assertEqual(read_prefix(root)["architecture"], "x86_64")
            with self.assertRaises(PrefixError):
                create_prefix(temporary, "sample-game")
            with self.assertRaises(PrefixError):
                create_prefix(temporary, "../escape")

    def test_diagnostics_and_launch_plan_are_explicitly_non_executing(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            binary = base / "sample.exe"
            binary.write_bytes(minimal_pe64())
            prefix = create_prefix(base / "prefixes", "game")
            report = diagnose_binary(binary, prefix["path"])
            self.assertIn("KERNEL32.dll", report["imports"]["missing_from_search_paths"])
            plan = plan_launch(binary, prefix["path"])
            self.assertEqual(plan["status"], "blocked_native_runtime_unavailable")
            self.assertFalse(plan["execution_performed"])
            self.assertTrue(any("native" in item.lower() for item in plan["blockers"]))

    def test_status_does_not_claim_a_runtime(self):
        status = compatibility_status()
        self.assertFalse(status["launch_enabled"])
        self.assertIn("nt-process-manager", status["not_implemented"])

    def test_cli_exposes_compatibility_commands(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(["compat-status"]), 0)
        self.assertIn('"launch_enabled": false', output.getvalue())


if __name__ == "__main__":
    unittest.main()
