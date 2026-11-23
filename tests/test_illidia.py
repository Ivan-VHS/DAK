from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from duckos.illidia.library import (
    IllidiaError,
    IllidiaLibrary,
    SteamAdapter,
    EpicAdapter,
    GogAdapter,
    scan_custom_directories,
)
from duckos.illidia import launcher


class IllidiaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.library = IllidiaLibrary(self.root / "illidia.sqlite3")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def executable(self, path: Path, body: str = "#!/bin/sh\nexit 0\n") -> Path:
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)
        return path

    def test_library_add_filter_export_and_import(self) -> None:
        binary = self.executable(self.root / "My Game")
        first = self.library.add_game(
            name="My Game",
            source="custom",
            executable_path=binary,
            arguments=["--safe", "value with spaces"],
            working_directory=self.root,
            tags=["custom", "favourite"],
        )

        self.assertTrue(first.installed)
        self.assertEqual(self.library.get_game(first.id).arguments, ["--safe", "value with spaces"])
        filtered = self.library.list_games(search="my game", source="custom", installed=True)
        self.assertEqual([item.id for item in filtered], [first.id])
        self.assertEqual(self.library.list_games(tag="favourite")[0].id, first.id)

        payload = self.library.export_library()
        second_library = IllidiaLibrary(self.root / "second.sqlite3")
        imported = second_library.import_library(payload)

        self.assertEqual(imported, 1)
        self.assertEqual(second_library.list_games()[0].name, "My Game")
        self.assertEqual(second_library.list_games()[0].arguments, ["--safe", "value with spaces"])

    def test_custom_scanner_only_finds_candidates(self) -> None:
        root = self.root / "selected"
        root.mkdir()
        binary = self.executable(root / "run-me")
        (root / "notes.txt").write_text("not an executable", encoding="utf-8")

        candidates = scan_custom_directories([root])

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["executable_path"], str(binary.resolve()))

    def test_launch_profile_rejects_invalid_environment_names(self) -> None:
        with self.assertRaises(IllidiaError):
            self.library.add_game(
                name="Broken profile",
                source="custom",
                executable_path=self.root / "missing",
                launch_profile={"environment": {"bad-name": "value"}},
            )

    def test_steam_adapter_reads_local_app_manifest(self) -> None:
        root = self.root / "Steam"
        apps = root / "steamapps"
        apps.mkdir(parents=True)
        (apps / "appmanifest_123.acf").write_text(
            '"AppState" {\n"appid" "123"\n"name" "Example Steam Game"\n"installdir" "Example Game"\n}',
            encoding="utf-8",
        )
        with patch.dict(os.environ, {"STEAM_DIR": str(root)}):
            records = SteamAdapter().discover()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "Example Steam Game")
        self.assertEqual(records[0]["external_id"], "123")
        self.assertEqual(records[0]["metadata"]["store_uri"], "steam://rungameid/123")

    def test_epic_adapter_rejects_manifest_path_traversal(self) -> None:
        manifests = self.root / "manifests"
        manifests.mkdir()
        install = self.root / "installed"
        install.mkdir()
        (manifests / "bad.item").write_text(json.dumps({
            "AppName": "ExampleApp",
            "DisplayName": "Example Epic Game",
            "InstallLocation": str(install),
            "LaunchExecutable": "../../outside.exe",
        }), encoding="utf-8")
        with patch.dict(os.environ, {"EPIC_MANIFEST_DIR": str(manifests)}):
            records = EpicAdapter().discover()

        self.assertEqual(len(records), 1)
        self.assertIsNone(records[0]["executable_path"])
        self.assertTrue(records[0]["metadata"]["store_uri"].startswith("com.epicgames.launcher://"))

    def test_gog_adapter_reads_primary_play_task(self) -> None:
        install = self.root / "GOG Games" / "Example"
        install.mkdir(parents=True)
        game_exe = self.executable(install / "game.exe")
        (install / "goggame-456.info").write_text(json.dumps({
            "gameId": 456,
            "name": "Example GOG Game",
            "playTasks": [
                {"isPrimary": False, "path": "other.exe"},
                {"isPrimary": True, "path": game_exe.name, "arguments": ["--fullscreen"]},
            ],
        }), encoding="utf-8")
        with patch.dict(os.environ, {"GOG_GAMES_DIR": str(install.parent)}):
            records = GogAdapter().discover()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["executable_path"], str(game_exe.resolve()))
        self.assertEqual(records[0]["arguments"], ["--fullscreen"])

    def test_unverified_direct_launch_needs_explicit_first_confirmation(self) -> None:
        binary = self.executable(self.root / "unsigned-game")
        game = self.library.add_game(name="Unsigned game", source="custom", executable_path=binary)
        verifier = {"status": "not_checked", "signer": None, "detail": "test verifier"}
        with patch.object(launcher, "signature_report", return_value=verifier):
            review = launcher.inspect_game(self.library, game)
            self.assertTrue(review["first_run_confirmation_required"])
            with self.assertRaises(launcher.LaunchError):
                launcher.launch_game(self.library, game.id, wait=True)

            result = launcher.launch_game(self.library, game.id, confirm_unverified=True, wait=True)

        self.assertEqual(result["status"], "exited")
        self.assertEqual(result["exit_code"], 0)
        self.assertTrue(self.library.has_approval(game.id, launcher.sha256_file(binary)))

    def test_changed_hash_is_reported_but_does_not_block_launch(self) -> None:
        binary = self.executable(self.root / "mutable-game")
        game = self.library.add_game(name="Mutable game", source="custom", executable_path=binary)
        verifier = {"status": "not_checked", "signer": None, "detail": "test verifier"}
        with patch.object(launcher, "signature_report", return_value=verifier):
            launcher.launch_game(
                self.library, game.id, confirm_unverified=True,
                update_fingerprint=True, wait=True,
            )
            old_digest = self.library.fingerprint(game.id)
            self.executable(binary, "#!/bin/sh\nexit 0\n# user updated this binary\n")

            review = launcher.inspect_game(self.library, game)
            self.assertTrue(review["hash_changed"])
            self.assertFalse(review["first_run_confirmation_required"])

            result = launcher.launch_game(self.library, game.id, wait=True)

        self.assertEqual(result["status"], "exited")
        self.assertTrue(result["hash_changed"])
        self.assertEqual(self.library.fingerprint(game.id), old_digest)

    def test_command_arguments_are_passed_as_literal_arguments(self) -> None:
        binary = self.executable(self.root / "literal-args")
        game = self.library.add_game(
            name="Literal args",
            source="custom",
            executable_path=binary,
            arguments=["one;two", "$(do-not-run)", "space value"],
        )

        command = launcher._runtime_command(game)

        self.assertEqual(command, [str(binary.resolve()), "one;two", "$(do-not-run)", "space value"])

    def test_auto_runtime_uses_duckbridge_plan_without_executing_it(self) -> None:
        binary = self.executable(self.root / "runtime-game.exe")
        game = self.library.add_game(
            name="Runtime game",
            source="custom",
            executable_path=binary,
            runtime="auto",
            runtime_prefix=self.root / "prefix",
        )
        expected = {
            "status": "ready",
            "argv": ["/usr/bin/wine", str(binary.resolve()), "--test"],
            "environment": {"WINEPREFIX": str(self.root / "prefix")},
            "warnings": ["test runtime plan"],
            "execution_started": False,
            "prefix_created": False,
        }
        with patch("duckos.compat.bridge.build_launch_plan", return_value=expected) as build_plan:
            command, environment, warnings = launcher._execution_plan(game)

        self.assertEqual(command, expected["argv"])
        self.assertEqual(environment, expected["environment"])
        self.assertEqual(warnings, expected["warnings"])
        self.assertEqual(build_plan.call_args.kwargs["purpose"], "game")
        self.assertEqual(build_plan.call_args.kwargs["backend"], "auto")
        self.assertFalse(expected["execution_started"])
        self.assertFalse(expected["prefix_created"])

    def test_unsupported_store_uri_is_rejected(self) -> None:
        with self.assertRaises(launcher.LaunchError):
            launcher._open_store_uri("file:///etc/passwd")


if __name__ == "__main__":
    unittest.main()
