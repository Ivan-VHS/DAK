from __future__ import annotations

import json
import struct
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from duckos.cli import main
from duckos.compat.bridge import (
    DuckBridgeError, build_launch_plan, detect_runtimes, inspect_binary,
)
from duckos.compat.illidia import add_game, launch_game, list_games, remove_game


def make_pe64(path: Path) -> Path:
    data = bytearray(0x400)
    data[:2] = b"MZ"
    data[0x3C:0x40] = (0x80).to_bytes(4, "little")
    data[0x80:0x84] = b"PE\0\0"
    coff = 0x84
    data[coff:coff + 2] = (0x8664).to_bytes(2, "little")
    data[coff + 2:coff + 4] = (1).to_bytes(2, "little")
    data[coff + 16:coff + 18] = (0xF0).to_bytes(2, "little")
    data[coff + 18:coff + 20] = (0x0002).to_bytes(2, "little")
    optional = coff + 20
    data[optional:optional + 2] = (0x20B).to_bytes(2, "little")
    data[optional + 16:optional + 20] = (0x1000).to_bytes(4, "little")
    data[optional + 24:optional + 32] = (0x140000000).to_bytes(8, "little")
    data[optional + 56:optional + 60] = (0x2000).to_bytes(4, "little")
    data[optional + 60:optional + 64] = (0x200).to_bytes(4, "little")
    data[optional + 68:optional + 70] = (3).to_bytes(2, "little")
    data[optional + 108:optional + 112] = (16).to_bytes(4, "little")
    data[optional + 120:optional + 128] = (0x1000).to_bytes(4, "little") + (40).to_bytes(4, "little")
    section = optional + 0xF0
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
    path.write_bytes(data)
    return path


def make_elf(path: Path, machine: int = 62, bits: int = 64, endian: str = "little") -> Path:
    data = bytearray(64)
    data[:4] = b"\x7fELF"
    data[4] = 2 if bits == 64 else 1
    data[5] = 1 if endian == "little" else 2
    data[6] = 1
    data[16:18] = (2).to_bytes(2, endian)
    data[18:20] = machine.to_bytes(2, endian)
    path.write_bytes(data)
    path.chmod(0o755)
    return path


def make_program(directory: Path, name: str) -> Path:
    program = directory / name
    program.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    program.chmod(0o755)
    return program.resolve()


class DuckBridgeTests(unittest.TestCase):
    def test_pe_inspection_reuses_shared_windows_parser(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = make_pe64(Path(temporary) / "sample.exe")
            report = inspect_binary(target)
        self.assertEqual(report["format"], "PE32+")
        self.assertEqual(report["architecture"], "x86_64")
        self.assertEqual(report["bits"], 64)
        self.assertIn("KERNEL32.dll", report["imports"])
        self.assertEqual(report["sha256"], report["pe_report"]["sha256"])
        self.assertTrue(report["pe_report"]["inspection_only"])

    def test_elf_inspection_reports_class_endianness_and_machine(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = make_elf(Path(temporary) / "tool", machine=21, bits=64, endian="big")
            report = inspect_binary(target)
        self.assertTrue(report["valid"])
        self.assertEqual(report["format"], "ELF")
        self.assertEqual(report["architecture"], "ppc64")
        self.assertEqual(report["endianness"], "big")
        self.assertEqual(report["bits"], 64)

    def test_unknown_file_is_reported_without_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "notes.txt"
            target.write_text("not an executable", encoding="utf-8")
            report = inspect_binary(target)
        self.assertFalse(report["valid"])
        self.assertEqual(report["format"], "unknown")

    def test_missing_and_symbolic_link_inputs_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(DuckBridgeError):
                inspect_binary(root / "missing.exe")
            target = make_pe64(root / "target.exe")
            link = root / "linked.exe"
            link.symlink_to(target)
            with self.assertRaises(DuckBridgeError):
                inspect_binary(link)

    def test_runtime_discovery_finds_wine_and_installed_proton(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            bindir = home / "bin"
            bindir.mkdir()
            wine = make_program(bindir, "wine")
            proton_dir = home / ".local/share/Steam/steamapps/common/Proton Experimental"
            proton_dir.mkdir(parents=True)
            proton = make_program(proton_dir, "proton")
            report = detect_runtimes(
                search_path=str(bindir), home=home, host_machine="x86_64"
            )
        found = {item["id"]: item for item in report["runtimes"]}
        self.assertEqual(found["wine"]["command"], [str(wine)])
        self.assertEqual(found["proton"]["command"], [str(proton)])
        self.assertFalse(report["runtime_processes_started"])
        self.assertFalse(report["discovery_performed_network_access"])

    def test_runtime_discovery_finds_crossover_and_flatpak_bottles(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            bindir = home / "bin"
            bindir.mkdir()
            flatpak = make_program(bindir, "flatpak")
            cx_dir = home / "cxoffice/bin"
            cx_dir.mkdir(parents=True)
            crossover = make_program(cx_dir, "wine")
            (home / ".local/share/flatpak/app/com.usebottles.bottles").mkdir(parents=True)
            report = detect_runtimes(search_path=str(bindir), home=home)
        found = {item["id"]: item for item in report["runtimes"]}
        self.assertEqual(found["crossover"]["command"], [str(crossover)])
        self.assertEqual(found["bottles"]["command"], [
            str(flatpak), "run", "--command=bottles-cli", "com.usebottles.bottles"
        ])

    def test_application_prefers_wine_and_preserves_argv_boundaries(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            bindir = home / "bin"
            bindir.mkdir()
            wine = make_program(bindir, "wine")
            target = make_pe64(home / "editor.exe")
            plan = build_launch_plan(
                target, search_path=str(bindir), home=home, host_machine="x86_64",
                arguments=["--profile", "folder with spaces"],
            )
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["backend"], "wine")
        self.assertEqual(plan["argv"], [
            str(wine), str(target), "--profile", "folder with spaces"
        ])
        self.assertFalse(plan["execution_started"])
        self.assertFalse(plan["prefix_created"])

    def test_game_prefers_proton_and_requires_compatibility_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            bindir = home / "bin"
            bindir.mkdir()
            proton = make_program(bindir, "proton")
            target = make_pe64(home / "game.exe")
            missing = build_launch_plan(
                target, purpose="game", search_path=str(bindir),
                home=home, host_machine="x86_64",
            )
            ready = build_launch_plan(
                target, purpose="game", compat_data=home / "compat-data",
                search_path=str(bindir), home=home, host_machine="x86_64",
            )
        self.assertEqual(missing["status"], "needs_configuration")
        self.assertEqual(missing["required_configuration"], ["--compat-data"])
        self.assertEqual(ready["backend"], "proton")
        self.assertEqual(ready["argv"][:3], [str(proton), "run", str(target)])
        self.assertEqual(
            ready["environment"]["STEAM_COMPAT_DATA_PATH"],
            str((home / "compat-data").resolve()),
        )
        self.assertFalse(ready["execution_started"])

    def test_bottles_plan_requires_existing_bottle_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            bindir = home / "bin"
            bindir.mkdir()
            bottles = make_program(bindir, "bottles-cli")
            target = make_pe64(home / "installer.exe")
            missing = build_launch_plan(
                target, backend="bottles", search_path=str(bindir),
                home=home, host_machine="x86_64",
            )
            ready = build_launch_plan(
                target, backend="bottles", bottle="Work tools",
                search_path=str(bindir), home=home, host_machine="x86_64",
            )
        self.assertEqual(missing["status"], "needs_configuration")
        self.assertEqual(ready["argv"], [
            str(bottles), "run", "-b", "Work tools", "-e", str(target)
        ])

    def test_crossover_plan_uses_existing_named_bottle(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            cx_dir = home / "cxoffice/bin"
            cx_dir.mkdir(parents=True)
            crossover = make_program(cx_dir, "wine")
            target = make_pe64(home / "editor.exe")
            plan = build_launch_plan(
                target, backend="crossover", bottle="Office",
                search_path="", home=home, host_machine="x86_64",
            )
        self.assertEqual(plan["argv"], [
            str(crossover), "--bottle", "Office", "--cx-app", str(target)
        ])

    def test_native_elf_plan_requires_executable_permission(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            target = make_elf(home / "native-tool")
            target.chmod(0o644)
            plan = build_launch_plan(
                target, search_path="", home=home, host_machine="x86_64"
            )
        self.assertEqual(plan["status"], "needs_configuration")
        self.assertIn("executable-permission", plan["required_configuration"])

    def test_native_elf_and_qemu_plans_do_not_start_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            native = make_elf(home / "native-tool")
            native_plan = build_launch_plan(
                native, search_path="", home=home, host_machine="x86_64"
            )
            bindir = home / "bin"
            bindir.mkdir()
            qemu = make_program(bindir, "qemu-x86_64")
            foreign = make_elf(home / "foreign-tool", machine=62)
            foreign_plan = build_launch_plan(
                foreign, search_path=str(bindir), home=home, host_machine="aarch64"
            )
        self.assertEqual(native_plan["backend"], "native")
        self.assertEqual(native_plan["argv"], [str(native)])
        self.assertEqual(foreign_plan["backend"], "qemu-x86_64")
        self.assertEqual(foreign_plan["argv"], [str(qemu), str(foreign)])
        self.assertFalse(native_plan["execution_started"])
        self.assertFalse(foreign_plan["execution_started"])

    def test_pe_plans_refuse_unsupported_host_architectures(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            bindir = home / "bin"
            bindir.mkdir()
            make_program(bindir, "wine")
            target = make_pe64(home / "tool.exe")
            plan = build_launch_plan(
                target, search_path=str(bindir), home=home, host_machine="aarch64"
            )
        self.assertEqual(plan["status"], "unsupported")
        self.assertIn("x86-64", plan["warnings"][0])

    def test_pe_plans_reject_non_x86_machine_types(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            bindir = home / "bin"
            bindir.mkdir()
            make_program(bindir, "wine")
            target = make_pe64(home / "arm64.exe")
            image = bytearray(target.read_bytes())
            image[0x84:0x86] = (0xAA64).to_bytes(2, "little")
            target.write_bytes(image)
            plan = build_launch_plan(
                target, search_path=str(bindir), home=home, host_machine="x86_64"
            )
        self.assertEqual(plan["status"], "unsupported")
        self.assertIn("PE machine type", plan["warnings"][0])

    def test_wine_launch_plan_accepts_an_isolated_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bindir = root / "bin"
            bindir.mkdir()
            make_program(bindir, "wine")
            target = make_pe64(root / "game.exe")
            prefix = root / "prefix"
            plan = build_launch_plan(
                target, purpose="game", backend="wine", wine_prefix=prefix,
                search_path=str(bindir), home=root, host_machine="x86_64",
            )
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["environment"]["WINEPREFIX"], str(prefix.resolve()))

    def test_illidia_library_registers_lists_and_removes_a_game(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = make_pe64(root / "A game.exe")
            library = root / "library.json"
            added = add_game(target, name="A Game", library_path=library)
            games = list_games(library_path=library)
            removed = remove_game(added["game"]["id"], library_path=library)
            empty = list_games(library_path=library)

        self.assertEqual(added["game"]["id"], "a-game")
        self.assertEqual(games["count"], 1)
        self.assertEqual(games["games"][0]["executable"], str(target))
        self.assertEqual(removed["game_files_deleted"], False)
        self.assertEqual(empty["count"], 0)

    def test_illidia_launches_through_wine_with_an_isolated_prefix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bindir = root / "bin"
            bindir.mkdir()
            wine = make_program(bindir, "wine")
            target = make_pe64(root / "A game.exe")
            library = root / "library.json"
            compatibility_root = root / "compatdata"
            added = add_game(target, name="A Game", library_path=library)

            result = launch_game(
                added["game"]["id"],
                library_path=library,
                compatibility_root=compatibility_root,
                search_path=str(bindir),
                home=root,
                host_machine="x86_64",
                arguments=["argument with spaces"],
                wait=True,
            )
            stored = list_games(library_path=library)["games"][0]

        self.assertEqual(result["status"], "finished")
        self.assertEqual(result["backend"], "wine")
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(result["execution_started"])
        self.assertTrue(Path(result["compatibility_data"]).is_dir())
        self.assertEqual(stored["last_exit_code"], 0)
        self.assertIsNotNone(stored["last_launched_at"])

    def test_cli_exposes_illidia_library_commands_as_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = make_pe64(root / "game.exe")
            library = root / "library.json"
            output = StringIO()
            with redirect_stdout(output):
                status = main(["illidia", "add", str(target), "--library", str(library)])
            self.assertEqual(status, 0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["game"]["name"], "game")

            output = StringIO()
            with redirect_stdout(output):
                status = main(["illidia", "list", "--library", str(library)])
            self.assertEqual(status, 0)
            listing = json.loads(output.getvalue())
        self.assertEqual(listing["count"], 1)

    def test_cli_exposes_duckbridge_commands_as_json(self):
        output = StringIO()
        with redirect_stdout(output):
            status = main(["bridge", "runtimes"])
        self.assertEqual(status, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["schema"], "duckos.duckbridge-runtimes.v1")


if __name__ == "__main__":
    unittest.main()
