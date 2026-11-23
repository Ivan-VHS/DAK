from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from duckos.compat.upstream import (
    RuntimeError,
    build_launch_plan,
    create_runtime_environment,
    detect_runtimes,
    launch_application,
    recommend_runtime,
    runtime_status,
)


def runtime(runtime_id: str, command: str, **extra: object) -> dict:
    return {
        "id": runtime_id,
        "name": runtime_id.title(),
        "available": True,
        "command": command,
        "transport": "native",
        **extra,
    }


def inventory(*items: dict) -> dict:
    return {
        "schema": "duckos.compat-runtime-inventory.v1",
        "host": "linux",
        "supported_host": True,
        "runtimes": list(items),
    }


class UpstreamRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.exe = self.root / "sample.exe"
        self.exe.write_bytes(b"MZ\x00\x00")

    def tearDown(self):
        self.temporary.cleanup()

    def test_recommends_the_right_specialist_for_each_scenario(self):
        installed = inventory(
            runtime("proton", "/steam/Proton/proton", steam_root="/steam"),
            runtime("lutris", "/usr/bin/lutris"),
            runtime("bottles", "/usr/bin/bottles-cli"),
            runtime("crossover", "/opt/cxoffice/bin/wine"),
            runtime("wine", "/usr/bin/wine"),
        )
        expected = {
            "steam-game": "proton",
            "multi-store": "lutris",
            "isolated-app": "bottles",
            "commercial-app": "crossover",
        }
        for scenario, expected_id in expected.items():
            with self.subTest(scenario=scenario):
                self.assertEqual(recommend_runtime(scenario, installed)["recommended"]["id"], expected_id)

    def test_missing_tools_and_unknown_scenarios_are_handled(self):
        self.assertIsNone(recommend_runtime("steam-game", inventory())["recommended"])
        with self.assertRaises(RuntimeError):
            recommend_runtime("universal-mode", inventory())

    def test_proton_needs_app_id_and_builds_steam_environment(self):
        installed = inventory(runtime("proton", "/steam/Proton/proton", steam_root="/steam"))
        with self.assertRaises(RuntimeError):
            build_launch_plan("proton", executable=self.exe, inventory=installed)
        plan = build_launch_plan("proton", executable=self.exe, app_id=2026, inventory=installed)
        self.assertEqual(plan["argv"][:3], ["/steam/Proton/proton", "run", str(self.exe.resolve())])
        self.assertEqual(plan["environment"]["STEAM_COMPAT_APP_ID"], "2026")
        self.assertFalse(plan["shell"])

    def test_lutris_uses_a_valid_existing_game_identifier(self):
        installed = inventory(runtime("lutris", "/usr/bin/lutris"))
        plan = build_launch_plan("lutris", game_id="12345", inventory=installed)
        self.assertEqual(plan["argv"], ["/usr/bin/lutris", "lutris:rungameid/12345"])
        with self.assertRaises(RuntimeError):
            build_launch_plan("lutris", game_id="../other", inventory=installed)
        with self.assertRaises(RuntimeError):
            build_launch_plan("lutris", game_id="12345", arguments=["--fps"], inventory=installed)

    def test_bottles_uses_a_named_existing_environment_and_quoted_args(self):
        installed = inventory(runtime("bottles", "/usr/bin/bottles-cli"))
        plan = build_launch_plan(
            "bottles", executable=self.exe, bottle="GameBox",
            arguments=["-windowed", "two words"], inventory=installed,
        )
        self.assertEqual(plan["argv"][:6], [
            "/usr/bin/bottles-cli", "run", "--bottle", "GameBox",
            "--executable", str(self.exe.resolve()),
        ])
        self.assertEqual(plan["argv"][-2:], ["--args", "-windowed 'two words'"])

    def test_flatpak_bottles_uses_its_application_cli(self):
        installed = inventory(runtime(
            "bottles", "/usr/bin/flatpak", transport="flatpak",
            flatpak_app="com.usebottles.bottles",
        ))
        plan = build_launch_plan("bottles", executable=self.exe, bottle="Office", inventory=installed)
        self.assertEqual(plan["argv"][:5], [
            "/usr/bin/flatpak", "run", "--command=bottles-cli",
            "com.usebottles.bottles", "run",
        ])

    def test_crossover_uses_the_documented_bottle_switches(self):
        installed = inventory(runtime("crossover", "/opt/cxoffice/bin/wine"))
        plan = build_launch_plan("crossover", executable=self.exe, bottle="Office", inventory=installed)
        self.assertEqual(plan["argv"], [
            "/opt/cxoffice/bin/wine", "--bottle", "Office", "--cx-app", "sample.exe",
        ])

    def test_wine_uses_a_selected_prefix_without_shell_execution(self):
        installed = inventory(runtime("wine", "/usr/bin/wine"))
        prefix = self.root / "prefix"
        plan = build_launch_plan("wine", executable=self.exe, prefix=prefix, inventory=installed)
        self.assertEqual(plan["environment"]["WINEPREFIX"], str(prefix.resolve()))
        self.assertFalse(plan["shell"])

    def test_unsafe_targets_and_arguments_are_rejected(self):
        installed = inventory(
            runtime("wine", "/usr/bin/wine"),
            runtime("bottles", "/usr/bin/bottles-cli"),
        )
        with self.assertRaises(RuntimeError):
            build_launch_plan("wine", executable=self.root / "missing.exe", inventory=installed)
        with self.assertRaises(RuntimeError):
            build_launch_plan("bottles", executable=self.exe, bottle="../../outside", inventory=installed)
        with self.assertRaises(RuntimeError):
            build_launch_plan("wine", executable=self.exe, arguments=["bad\x00value"], inventory=installed)

    def test_process_launch_is_explicit_and_shell_free(self):
        installed = inventory(runtime("wine", "/usr/bin/wine"))
        fake_process = Mock(pid=4711)
        with patch("duckos.compat.upstream.subprocess.Popen", return_value=fake_process) as popen:
            result = launch_application("wine", executable=self.exe, inventory=installed)
        self.assertTrue(result["started"])
        self.assertEqual(result["pid"], 4711)
        self.assertFalse(popen.call_args.kwargs["shell"])

    def test_runtime_discovery_finds_steam_proton_and_wine(self):
        steam = self.root / "Steam"
        proton = steam / "steamapps" / "common" / "Proton Experimental" / "proton"
        proton.parent.mkdir(parents=True)
        proton.write_text("#!/bin/sh\n")
        proton.chmod(0o700)
        wine = self.root / "wine"
        wine.write_text("#!/bin/sh\n")
        wine.chmod(0o700)

        def which(name: str) -> str | None:
            return str(wine) if name in {"wine", "wine64"} else None

        report = detect_runtimes(home=self.root, environ={"STEAM_DIR": str(steam)}, which=which)
        tools = {entry["id"]: entry for entry in report["runtimes"]}
        self.assertTrue(tools["proton"]["available"])
        self.assertTrue(tools["wine"]["available"])
        self.assertFalse(tools["lutris"]["available"])

    def test_proton_in_a_secondary_library_uses_the_primary_steam_client_root(self):
        steam = self.root / "Steam"
        secondary = self.root / "Library"
        (steam / "steamapps").mkdir(parents=True)
        (steam / "steamapps" / "libraryfolders.vdf").write_text(
            '"libraryfolders" { "1" { "path" "' + str(secondary) + '" } }',
            encoding="utf-8",
        )
        proton = secondary / "steamapps" / "common" / "Proton Experimental" / "proton"
        proton.parent.mkdir(parents=True)
        proton.write_text("#!/bin/sh\n")
        proton.chmod(0o700)

        report = detect_runtimes(home=self.root, environ={"STEAM_DIR": str(steam)}, which=lambda _name: None)
        found = next(entry for entry in report["runtimes"] if entry["id"] == "proton")
        self.assertTrue(found["available"])
        self.assertEqual(found["command"], str(proton.resolve()))
        self.assertEqual(found["steam_root"], str(steam.resolve()))

    def test_bottles_environment_creation_calls_the_upstream_cli(self):
        installed = inventory(runtime("bottles", "/usr/bin/bottles-cli"))
        completed = Mock(returncode=0, stdout="", stderr="")
        with patch("duckos.compat.upstream.subprocess.run", return_value=completed) as run:
            created = create_runtime_environment(
                "bottles", "Gaming", architecture="win64",
                environment="gaming", inventory=installed,
            )
        self.assertTrue(created["created"])
        self.assertEqual(run.call_args.args[0], [
            "/usr/bin/bottles-cli", "new", "--bottle-name", "Gaming",
            "--environment", "gaming", "--arch", "win64",
        ])

    def test_wine_prefix_initialization_is_delegated_to_wineboot(self):
        wine = self.root / "wine"
        wine.write_text("#!/bin/sh\n")
        wineboot = self.root / "wineboot"
        wineboot.write_text("#!/bin/sh\n")
        wineboot.chmod(0o700)
        installed = inventory(runtime("wine", str(wine)))
        completed = Mock(returncode=0, stdout="", stderr="")
        with patch("duckos.compat.upstream.subprocess.run", return_value=completed) as run:
            created = create_runtime_environment(
                "wine", "Office", store=self.root / "prefixes", inventory=installed,
            )
        self.assertTrue(created["created"])
        self.assertEqual(run.call_args.args[0], [str(wineboot), "--init"])
        self.assertTrue(Path(created["path"]).is_dir())
        self.assertEqual(Path(created["path"]).stat().st_mode & 0o777, 0o700)
        self.assertEqual(
            run.call_args.kwargs["env"]["WINEPREFIX"],
            str(self.root / "prefixes" / "Office"),
        )

    def test_runtime_status_does_not_confuse_host_adapters_with_native_loader(self):
        report = runtime_status(inventory(runtime("wine", "/usr/bin/wine")))
        self.assertEqual(report["execution"], "explicit CLI launch only; no Mora browser process bridge")
        self.assertEqual(report["runtimes"][0]["id"], "wine")


if __name__ == "__main__":
    unittest.main()
