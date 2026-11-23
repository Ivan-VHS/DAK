from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from duckos import compatibility
from duckos.cli import main as duckos_main


class CompatibilityTests(unittest.TestCase):
    def test_cli_forwards_wine_launch_arguments_to_the_host_runtime(self):
        from contextlib import redirect_stdout
        from io import StringIO

        output = StringIO()
        expected = {
            "schema": "duckos.compatibility.launch.v1",
            "engine": "wine",
            "executable": "/tmp/game.exe",
            "pid": 123,
            "started": True,
            "shell_used": False,
        }
        with patch("duckos.cli.host_compatibility.launch_program", return_value=expected) as launch:
            with redirect_stdout(output):
                result = duckos_main([
                    "compatibility", "launch", "--engine", "wine",
                    "--prefix", "games", "--", "/tmp/game.exe", "--windowed"
                ])

        self.assertEqual(result, 0)
        launch.assert_called_once_with(
            Path("/tmp/game.exe"),
            engine="wine",
            prefix="games",
            compat_data=None,
            arguments=["--windowed"],
        )
        self.assertIn('"started": true', output.getvalue())

    def test_cli_routes_reactos_guest_options_without_shell_execution(self):
        from contextlib import redirect_stdout
        from io import StringIO

        output = StringIO()
        with patch("duckos.cli.host_compatibility.launch_reactos", return_value={
            "schema": "duckos.compatibility.vm-launch.v1",
            "guest": "ReactOS",
            "started": True,
            "network": "disabled",
            "shell_used": False,
        }) as launch:
            with redirect_stdout(output):
                result = duckos_main([
                    "compatibility", "launch-reactos",
                    "--disk", "/tmp/reactos.qcow2",
                    "--iso", "/tmp/reactos.iso",
                    "--memory-mib", "4096",
                    "--cpus", "4",
                ])

        self.assertEqual(result, 0)
        launch.assert_called_once_with(
            Path("/tmp/reactos.qcow2"),
            iso=Path("/tmp/reactos.iso"),
            memory_mib=4096,
            cpus=4,
        )
        self.assertIn('"network": "disabled"', output.getvalue())

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

    def test_open_manager_uses_an_allowlisted_command_without_a_shell(self):
        with patch("duckos.compatibility._program", return_value="/usr/bin/bottles"), \
             patch("duckos.compatibility.subprocess.Popen") as popen:
            popen.return_value.pid = 812
            result = compatibility.open_manager("bottles")

        self.assertEqual(result["manager"], "bottles")
        self.assertFalse(result["shell_used"])
        self.assertEqual(popen.call_args.args[0], ["/usr/bin/bottles"])
        self.assertNotIn("shell", popen.call_args.kwargs)
        with self.assertRaises(compatibility.CompatibilityError):
            compatibility.open_manager("../not-a-manager")

    def test_reactos_vm_uses_qemu_without_network_or_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            disk = Path(directory) / "reactos.qcow2"
            disk.write_bytes(b"qcow2")
            iso = Path(directory) / "ReactOS.iso"
            iso.write_bytes(b"iso")
            with patch("duckos.compatibility.platform.system", return_value="Linux"), \
                 patch("duckos.compatibility._program", return_value="/usr/bin/qemu-system-x86_64"), \
                 patch("duckos.compatibility.subprocess.Popen") as popen:
                popen.return_value.pid = 913
                result = compatibility.launch_reactos(
                    disk, iso=iso, memory_mib=4096, cpus=4
                )

            command = popen.call_args.args[0]
            self.assertTrue(result["started"])
            self.assertEqual(result["network"], "disabled")
            self.assertIn("-nic", command)
            self.assertIn("none", command)
            self.assertEqual(command[0], "/usr/bin/qemu-system-x86_64")
            self.assertNotIn("shell", popen.call_args.kwargs)
            with self.assertRaises(compatibility.CompatibilityError):
                compatibility.launch_reactos(disk, memory_mib=512)

    def test_reactos_disk_creation_uses_qemu_img_and_validates_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "reactos.qcow2"

            def create_disk(argv, **kwargs):
                Path(argv[4]).write_bytes(b"qcow2")
                return type("Completed", (), {"returncode": 0, "stdout": "", "stderr": ""})()

            with patch("duckos.compatibility.platform.system", return_value="Linux"), \
                 patch("duckos.compatibility._program", return_value="/usr/bin/qemu-img"), \
                 patch("duckos.compatibility.subprocess.run", side_effect=create_disk) as run:
                result = compatibility.create_reactos_disk(target, size_gib=32)

            self.assertTrue(result["created"])
            self.assertEqual(result["size_gib"], 32)
            self.assertEqual(run.call_args.args[0][-1], "32G")
            with self.assertRaises(compatibility.CompatibilityError):
                compatibility.create_reactos_disk(target, size_gib=256)

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
