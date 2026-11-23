from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from duckos.illidia.library import (
    IllidiaError,
    IllidiaLibrary,
    SteamAdapter,
    EpicAdapter,
    GogAdapter,
    scan_custom_directories,
)
from duckos.illidia import launcher


def make_library(tmp_path: Path) -> IllidiaLibrary:
    return IllidiaLibrary(tmp_path / "illidia.sqlite3")


def executable(path: Path, body: str = "#!/bin/sh\nexit 0\n") -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_library_add_filter_export_and_import(tmp_path: Path) -> None:
    library = make_library(tmp_path)
    binary = executable(tmp_path / "My Game")
    first = library.add_game(
        name="My Game",
        source="custom",
        executable_path=binary,
        arguments=["--safe", "value with spaces"],
        working_directory=tmp_path,
        tags=["custom", "favourite"],
    )

    assert first.installed is True
    assert library.get_game(first.id).arguments == ["--safe", "value with spaces"]
    assert [item.id for item in library.list_games(search="my game", source="custom", installed=True)] == [first.id]
    assert library.list_games(tag="favourite")[0].id == first.id

    export_file = tmp_path / "library.json"
    export_file.write_text(json.dumps(library.export_library()), encoding="utf-8")
    second_library = IllidiaLibrary(tmp_path / "second.sqlite3")
    imported = second_library.import_library(json.loads(export_file.read_text(encoding="utf-8")))

    assert imported == 1
    assert second_library.list_games()[0].name == "My Game"
    assert second_library.list_games()[0].arguments == ["--safe", "value with spaces"]


def test_custom_scanner_only_finds_candidates_and_does_not_launch(tmp_path: Path) -> None:
    root = tmp_path / "selected"
    root.mkdir()
    binary = executable(root / "run-me")
    (root / "notes.txt").write_text("not an executable", encoding="utf-8")

    candidates = scan_custom_directories([root])

    assert len(candidates) == 1
    assert candidates[0]["executable_path"] == str(binary.resolve())


def test_launch_profile_rejects_invalid_environment_names(tmp_path: Path) -> None:
    library = make_library(tmp_path)
    with pytest.raises(IllidiaError):
        library.add_game(
            name="Broken profile",
            source="custom",
            executable_path=tmp_path / "missing",
            launch_profile={"environment": {"bad-name": "value"}},
        )


def test_steam_adapter_reads_local_app_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "Steam"
    apps = root / "steamapps"
    apps.mkdir(parents=True)
    (apps / "appmanifest_123.acf").write_text(
        '"AppState" {\n"appid" "123"\n"name" "Example Steam Game"\n"installdir" "Example Game"\n}',
        encoding="utf-8",
    )
    monkeypatch.setenv("STEAM_DIR", str(root))

    records = SteamAdapter().discover()

    assert len(records) == 1
    assert records[0]["name"] == "Example Steam Game"
    assert records[0]["external_id"] == "123"
    assert records[0]["metadata"]["store_uri"] == "steam://rungameid/123"


def test_epic_adapter_rejects_manifest_path_traversal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifests = tmp_path / "manifests"
    manifests.mkdir()
    install = tmp_path / "installed"
    install.mkdir()
    (manifests / "bad.item").write_text(json.dumps({
        "AppName": "ExampleApp",
        "DisplayName": "Example Epic Game",
        "InstallLocation": str(install),
        "LaunchExecutable": "../../outside.exe",
    }), encoding="utf-8")
    monkeypatch.setenv("EPIC_MANIFEST_DIR", str(manifests))

    records = EpicAdapter().discover()

    assert len(records) == 1
    assert records[0]["executable_path"] is None
    assert records[0]["metadata"]["store_uri"].startswith("com.epicgames.launcher://")


def test_gog_adapter_reads_primary_play_task(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    install = tmp_path / "GOG Games" / "Example"
    install.mkdir(parents=True)
    game_exe = executable(install / "game.exe")
    (install / "goggame-456.info").write_text(json.dumps({
        "gameId": 456,
        "name": "Example GOG Game",
        "playTasks": [
            {"isPrimary": False, "path": "other.exe"},
            {"isPrimary": True, "path": game_exe.name, "arguments": ["--fullscreen"]},
        ],
    }), encoding="utf-8")
    monkeypatch.setenv("GOG_GAMES_DIR", str(install.parent))

    records = GogAdapter().discover()

    assert len(records) == 1
    assert records[0]["executable_path"] == str(game_exe.resolve())
    assert records[0]["arguments"] == ["--fullscreen"]


def test_unverified_direct_launch_needs_explicit_first_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    library = make_library(tmp_path)
    binary = executable(tmp_path / "unsigned-game")
    game = library.add_game(name="Unsigned game", source="custom", executable_path=binary)
    monkeypatch.setattr(launcher, "signature_report", lambda _path: {
        "status": "not_checked", "signer": None, "detail": "test verifier"
    })

    review = launcher.inspect_game(library, game)
    assert review["first_run_confirmation_required"] is True

    with pytest.raises(launcher.LaunchError, match="explicit approval"):
        launcher.launch_game(library, game.id, wait=True)

    result = launcher.launch_game(library, game.id, confirm_unverified=True, wait=True)
    assert result["status"] == "exited"
    assert result["exit_code"] == 0
    assert library.has_approval(game.id, result["command"][0] and launcher.sha256_file(binary))


def test_changed_hash_is_reported_but_does_not_block_launch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    library = make_library(tmp_path)
    binary = executable(tmp_path / "mutable-game")
    game = library.add_game(name="Mutable game", source="custom", executable_path=binary)
    monkeypatch.setattr(launcher, "signature_report", lambda _path: {
        "status": "not_checked", "signer": None, "detail": "test verifier"
    })

    launcher.launch_game(library, game.id, confirm_unverified=True, update_fingerprint=True, wait=True)
    old_digest = library.fingerprint(game.id)
    executable(binary, "#!/bin/sh\nexit 0\n# user updated this binary\n")

    review = launcher.inspect_game(library, game)
    assert review["hash_changed"] is True
    assert review["first_run_confirmation_required"] is True

    result = launcher.launch_game(library, game.id, confirm_unverified=True, wait=True)
    assert result["status"] == "exited"
    assert result["hash_changed"] is True
    assert library.fingerprint(game.id) == old_digest


def test_command_arguments_are_passed_without_a_shell(tmp_path: Path) -> None:
    library = make_library(tmp_path)
    binary = executable(tmp_path / "literal-args")
    game = library.add_game(
        name="Literal args",
        source="custom",
        executable_path=binary,
        arguments=["one;two", "$(do-not-run)", "space value"],
    )

    command = launcher._runtime_command(game)

    assert command == [str(binary.resolve()), "one;two", "$(do-not-run)", "space value"]


def test_store_scheme_must_be_known(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(launcher.LaunchError, match="Unsupported store URI"):
        launcher._open_store_uri("file:///etc/passwd")
