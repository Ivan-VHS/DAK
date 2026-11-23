from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from duckos import compatibility


class CompatibilityTests(unittest.TestCase):
    def test_prefix_names_are_bounded_and_cannot_traverse_directories(self):
        for name in ("", "../escape", "two words", ".hidden/../x", "x" * 49):
            with self.subTest(name=name), self.assertRaises(compatibility.CompatibilityError):
                compatibility._validate_prefix_name(name)
        self.assertEqual(compatibility._validate_prefix_name("games_64"), "games_64")

    def test_status_reports_real_command_discovery_without_claiming_everything_is_ready(self):
        with patch("duckos.compatibility.platform.system", return_value="Linux"), \
             patch("duckos.compatibility.platform.release", return_value="test-kernel"), \
             patch("duckos.compatibility.platform.machine", return_value="x86_64"), \
             patch("duckos.compatibility._program", side_effect=lambda *names: "/usr/bin/" + names[0] if names[0] in {"wine", "winetricks"} else None), \
             patch("duckos.compatibility._proton_program", return_value=None):
            report = compatibility.compatibility_status()

        self.assertEqual(report["schema"], compatibility.STATUS_SCHEMA)
        tools = {item["id"]: item for item in report["tools"]}
        self.assertTrue(tools["wine"]["available"])
        self.assertTrue(tools["winetricks"]["available"])
        self.assertFalse(tools["proton"]["available"])
        self.assertIn("ReactOS is a separate operating system", " ".join(report["limitations"]))

    def test_prefix_creation_uses_wineboot_and_writes_versioned_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"DUCKOS_COMPATIBILITY_HOME": directory}, clear=False), \
                 patch("duckos.compatibility.platform.system", return_value="Linux"), \
                 patch("duckos.compatibility._program", side_effect=lambda *names: "/usr/bin/" + names[0]), \
                 patch("duckos.compatibility.subprocess.run") as run:
                run.return_value.returncode = 0
                created = compatibility.create_prefix("games", "win64")

            self.assertEqual(created["schema"], compatibility.PREFIX_SCHEMA)
            self.assertEqual(created["architecture"], "win64")
            self.assertEqual(run.call_args.args[0], ["/usr/bin/wineboot", "--init"])
            self.assertEqual(run.call_args.kwargs["env"]["WINEARCH"], "win64")
            self.assertTrue((Path(directory) / "prefixes" / "games" / compatibility.PREFIX_METADATA).is_file())

    def test_prefix_creation_rolls_back_when_wineboot_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"DUCKOS_COMPATIBILITY_HOME": directory}, clear=False), \
                 patch("duckos.compatibility.platform.system", return_value="Linux"), \
                 patch("duckos.compatibility._program", side_effect=lambda *names: "/usr/bin/" + names[0]), \
                 patch("duckos.compatibility.subprocess.run") as run:
                run.return_value.returncode = 1
                run.return_value.stderr = "initialization failed"
                with self.assertRaisesRegex(compatibility.CompatibilityError, "wineboot failed"):
                    compatibility.create_prefix("broken")
            self.assertFalse((Path(directory) / "prefixes" / "broken").exists())

    def test_install_component_rejects_unlisted_winetricks_verbs(self):
        with self.assertRaisesRegex(compatibility.CompatibilityError, "unsupported component"):
            compatibility.install_component("../escape", "arbitrary-download")

    def test_launch_passes_an_argument_vector_and_never_uses_a_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            prefix_root = home / "prefixes" / "games"
            prefix_root.mkdir(parents=True)
            (prefix_root / compatibility.PREFIX_METADATA).write_text(
                '{"schema":"duckos.compatibility.prefix.v1","name":"games","engine":"wine","architecture":"win64"}',
                encoding="utf-8",
            )
            executable = home / "A Game.exe"
            executable.write_bytes(b"MZ")
            with patch.dict(os.environ, {"DUCKOS_COMPATIBILITY_HOME": directory}, clear=False), \
                 patch("duckos.compatibility.platform.system", return_value="Linux"), \
                 patch("duckos.compatibility._program", return_value="/usr/bin/wine"), \
                 patch("duckos.compatibility.subprocess.Popen") as popen:
                popen.return_value.pid = 4242
                result = compatibility.launch_program(
                    executable,
                    engine="wine",
                    prefix="games",
                    arguments=["--windowed", "two words"],
                )

            self.assertTrue(result["started"])
            self.assertFalse(result["shell_used"])
            self.assertEqual(popen.call_args.args[0], [
                "/usr/bin/wine", str(executable.resolve()), "--windowed", "two words"
            ])
            self.assertNotIn("shell", popen.call_args.kwargs)

    def test_launch_rejects_missing_managed_prefix_before_starting_process(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "game.exe"
            executable.write_bytes(b"MZ")
            with patch.dict(os.environ, {"DUCKOS_COMPATIBILITY_HOME": directory}, clear=False), \
                 patch("duckos.compatibility.platform.system", return_value="Linux"), \
                 patch("duckos.compatibility._program", return_value="/usr/bin/wine"):
                with self.assertRaisesRegex(compatibility.CompatibilityError, "managed prefix not found"):
                    compatibility.launch_program(executable, engine="wine", prefix="missing")


if __name__ == "__main__":
    unittest.main()
