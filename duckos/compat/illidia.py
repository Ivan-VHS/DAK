"""Illidia game library and safe process launcher for DuckOS.

Illidia stores local game entries and delegates Windows execution to an
installed Wine-compatible runtime discovered by DuckBridge. It never builds
shell commands and does not download, patch or bypass game protections.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .bridge import DuckBridgeError, build_launch_plan, inspect_binary

SCHEMA_LIBRARY = "duckos.illidia-library.v1"
SCHEMA_LAUNCH = "duckos.illidia-launch.v1"
MAX_LIBRARY_BYTES = 4 * 1024 * 1024
_GAME_ID = re.compile(r"[a-z0-9][a-z0-9-]{0,47}\\Z")
_BACKENDS = {"auto", "wine", "proton", "crossover", "bottles"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _data_home() -> Path:
    configured = os.environ.get("XDG_DATA_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".local" / "share"


def default_library_path() -> Path:
    """Return the per-user Illidia library location."""
    return _data_home() / "duckos" / "illidia" / "library.v1.json"


def default_compatibility_root() -> Path:
    return _data_home() / "duckos" / "illidia" / "compatdata"


def _library_file(path: str | Path | None) -> Path:
    return Path(path).expanduser() if path is not None else default_library_path()


def _empty_library() -> dict[str, Any]:
    return {"schema": SCHEMA_LIBRARY, "games": []}


def _read_library(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise DuckBridgeError("Illidia library must not be a symbolic link")
    if not path.exists():
        return _empty_library()
    if not path.is_file():
        raise DuckBridgeError("Illidia library path is not a regular file")
    try:
        if path.stat().st_size > MAX_LIBRARY_BYTES:
            raise DuckBridgeError("Illidia library exceeds 4 MiB")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise DuckBridgeError(f"cannot read Illidia library: {error}") from error

    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA_LIBRARY:
        raise DuckBridgeError("unsupported or malformed Illidia library")
    games = payload.get("games")
    if not isinstance(games, list):
        raise DuckBridgeError("Illidia library has no valid games list")

    seen: set[str] = set()
    for game in games:
        if not isinstance(game, dict):
            raise DuckBridgeError("Illidia library contains a malformed game entry")
        game_id = game.get("id")
        if not isinstance(game_id, str) or not _GAME_ID.fullmatch(game_id):
            raise DuckBridgeError("Illidia library contains an invalid game identifier")
        if game_id in seen:
            raise DuckBridgeError("Illidia library contains duplicate game identifiers")
        seen.add(game_id)
        if not isinstance(game.get("name"), str) or not isinstance(game.get("executable"), str):
            raise DuckBridgeError("Illidia library contains an incomplete game entry")
        if game.get("backend") not in _BACKENDS:
            raise DuckBridgeError("Illidia library contains an unsupported backend")
        arguments = game.get("arguments", [])
        if not isinstance(arguments, list) or any(not isinstance(item, str) for item in arguments):
            raise DuckBridgeError("Illidia library contains invalid launch arguments")
    return payload


def _write_library(path: Path, payload: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent.is_symlink() or not path.parent.is_dir():
            raise DuckBridgeError("Illidia library directory must be a real directory")
        if path.is_symlink():
            raise DuckBridgeError("Illidia library must not be a symbolic link")

        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
    except OSError as error:
        raise DuckBridgeError(f"cannot save Illidia library: {error}") from error


def _make_game_id(value: str) -> str:
    game_id = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")[:48]
    if not game_id:
        game_id = f"game-{uuid.uuid4().hex[:12]}"
    if not _GAME_ID.fullmatch(game_id):
        raise DuckBridgeError("game id must use lowercase letters, numbers and hyphens")
    return game_id


def list_games(*, library_path: str | Path | None = None) -> dict[str, Any]:
    """Return the local library without scanning or modifying the filesystem."""
    path = _library_file(library_path)
    payload = _read_library(path)
    games = sorted(payload["games"], key=lambda item: item["name"].casefold())
    return {
        "schema": SCHEMA_LIBRARY,
        "library": str(path),
        "count": len(games),
        "games": games,
    }


def add_game(
    executable: str | Path,
    *,
    name: str | None = None,
    game_id: str | None = None,
    backend: str = "auto",
    bottle: str | None = None,
    arguments: Iterable[str] | None = None,
    library_path: str | Path | None = None,
) -> dict[str, Any]:
    """Register an existing local PE or ELF executable in the game library."""
    if backend not in _BACKENDS:
        raise DuckBridgeError(f"backend must be one of {sorted(_BACKENDS)}")
    launch_arguments = list(arguments or [])
    if any(not isinstance(item, str) for item in launch_arguments):
        raise DuckBridgeError("all saved launch arguments must be strings")

    target = Path(executable).expanduser()
    if target.is_symlink():
        raise DuckBridgeError("game executable must not be a symbolic link")
    try:
        target = target.resolve(strict=True)
    except OSError as error:
        raise DuckBridgeError(f"cannot resolve game executable: {error}") from error
    if not target.is_file():
        raise DuckBridgeError("game executable must be a regular file")

    binary = inspect_binary(target)
    if not binary.get("valid"):
        raise DuckBridgeError("game executable is not a supported PE or ELF file")

    display_name = (name or target.stem).strip()
    if not display_name or len(display_name) > 128:
        raise DuckBridgeError("game name must contain 1 to 128 characters")
    identifier = _make_game_id(game_id or display_name)

    path = _library_file(library_path)
    payload = _read_library(path)
    if any(item["id"] == identifier for item in payload["games"]):
        raise DuckBridgeError(f"a game with id '{identifier}' is already registered")

    game = {
        "id": identifier,
        "name": display_name,
        "executable": str(target),
        "format": binary["format"],
        "architecture": binary["architecture"],
        "backend": backend,
        "bottle": bottle,
        "arguments": launch_arguments,
        "added_at": _now(),
        "last_launched_at": None,
        "last_exit_code": None,
    }
    payload["games"].append(game)
    _write_library(path, payload)
    return {"schema": SCHEMA_LIBRARY, "library": str(path), "game": game}


def remove_game(
    game_id: str,
    *,
    library_path: str | Path | None = None,
) -> dict[str, Any]:
    """Remove a library entry. Game files and compatibility data are retained."""
    if not _GAME_ID.fullmatch(game_id):
        raise DuckBridgeError("invalid game id")
    path = _library_file(library_path)
    payload = _read_library(path)
    remaining = [item for item in payload["games"] if item["id"] != game_id]
    if len(remaining) == len(payload["games"]):
        raise DuckBridgeError(f"game '{game_id}' is not registered")
    payload["games"] = remaining
    _write_library(path, payload)
    return {
        "schema": SCHEMA_LIBRARY,
        "removed": game_id,
        "game_files_deleted": False,
        "compatibility_data_deleted": False,
    }


def _find_game(game_id: str, library_path: str | Path | None) -> dict[str, Any]:
    if not _GAME_ID.fullmatch(game_id):
        raise DuckBridgeError("invalid game id")
    payload = _read_library(_library_file(library_path))
    game = next((item for item in payload["games"] if item["id"] == game_id), None)
    if game is None:
        raise DuckBridgeError(f"game '{game_id}' is not registered")
    return game


def _managed_prefix(game_id: str, root: str | Path | None) -> Path:
    base = Path(root).expanduser() if root is not None else default_compatibility_root()
    if base.is_symlink():
        raise DuckBridgeError("compatibility-data root must not be a symbolic link")
    try:
        base.mkdir(parents=True, exist_ok=True)
        if not base.is_dir() or base.is_symlink():
            raise DuckBridgeError("compatibility-data root must be a real directory")
        prefix = base / game_id
        if prefix.is_symlink():
            raise DuckBridgeError("game compatibility data must not be a symbolic link")
        prefix.mkdir(mode=0o700, exist_ok=True)
        if not prefix.is_dir() or prefix.is_symlink():
            raise DuckBridgeError("game compatibility data is not a safe directory")
        return prefix.resolve(strict=True)
    except OSError as error:
        raise DuckBridgeError(f"cannot prepare game compatibility data: {error}") from error


def _record_launch(
    game_id: str,
    *,
    exit_code: int | None,
    library_path: str | Path | None,
) -> None:
    path = _library_file(library_path)
    payload = _read_library(path)
    for game in payload["games"]:
        if game["id"] == game_id:
            game["last_launched_at"] = _now()
            game["last_exit_code"] = exit_code
            _write_library(path, payload)
            return
    raise DuckBridgeError(f"game '{game_id}' disappeared from the library during launch")


def launch_game(
    game_id: str,
    *,
    backend: str | None = None,
    bottle: str | None = None,
    arguments: Iterable[str] | None = None,
    library_path: str | Path | None = None,
    compatibility_root: str | Path | None = None,
    search_path: str | None = None,
    home: str | Path | None = None,
    host_machine: str | None = None,
    use_gamemode: bool = False,
    use_mangohud: bool = False,
    use_wined3d: bool = False,
    disable_esync: bool = False,
    disable_fsync: bool = False,
    wait: bool = False,
) -> dict[str, Any]:
    """Launch a registered game with an installed runtime using argv, never a shell."""
    game = _find_game(game_id, library_path)
    selected_backend = backend or game["backend"]
    if selected_backend not in _BACKENDS:
        raise DuckBridgeError(f"backend must be one of {sorted(_BACKENDS)}")
    selected_bottle = bottle if bottle is not None else game.get("bottle")
    extra_arguments = list(game.get("arguments", [])) + list(arguments or [])
    if any(not isinstance(item, str) for item in extra_arguments):
        raise DuckBridgeError("all launch arguments must be strings")

    target = Path(game["executable"]).expanduser()
    if target.is_symlink() or not target.is_file():
        raise DuckBridgeError("registered game executable is missing or is a symbolic link")

    plan = build_launch_plan(
        target,
        purpose="game",
        backend=selected_backend,
        bottle=selected_bottle,
        arguments=extra_arguments,
        search_path=search_path,
        home=home,
        host_machine=host_machine,
    )
    if plan["status"] != "ready" and plan["backend"] not in {"wine", "proton"}:
        raise DuckBridgeError(
            "game cannot be launched: " + "; ".join(plan.get("warnings", []))
        )

    prefix_path: Path | None = None
    if plan["backend"] in {"wine", "proton"}:
        prefix_path = _managed_prefix(game_id, compatibility_root)
        plan = build_launch_plan(
            target,
            purpose="game",
            backend=plan["backend"],
            bottle=selected_bottle,
            compat_data=prefix_path if plan["backend"] == "proton" else None,
            wine_prefix=prefix_path if plan["backend"] == "wine" else None,
            arguments=extra_arguments,
            search_path=search_path,
            home=home,
            host_machine=host_machine,
        )

    if plan["status"] != "ready":
        raise DuckBridgeError(
            "game cannot be launched: " + "; ".join(plan.get("warnings", []))
        )
    if (use_wined3d or disable_esync or disable_fsync) and plan["backend"] != "proton":
        raise DuckBridgeError("WinED3D, esync and fsync launch switches currently require Proton")

    environment = os.environ.copy()
    environment.update(plan["environment"])
    if use_wined3d:
        environment["PROTON_USE_WINED3D"] = "1"
    if disable_esync:
        environment["PROTON_NO_ESYNC"] = "1"
    if disable_fsync:
        environment["PROTON_NO_FSYNC"] = "1"

    command = list(plan["argv"])
    if use_gamemode:
        gamemode = shutil.which("gamemoderun", path=search_path)
        if gamemode is None:
            raise DuckBridgeError("GameMode was requested but gamemoderun was not found")
        command.insert(0, gamemode)
    if use_mangohud:
        mangohud = shutil.which("mangohud", path=search_path)
        if mangohud is None:
            raise DuckBridgeError("MangoHud was requested but the mangohud command was not found")
        command.insert(0, mangohud)

    started_at = _now()
    try:
        process = subprocess.Popen(
            command,
            cwd=target.parent,
            env=environment,
            shell=False,
            start_new_session=not wait,
        )
    except OSError as error:
        raise DuckBridgeError(f"could not start game runtime: {error}") from error

    result: dict[str, Any] = {
        "schema": SCHEMA_LAUNCH,
        "status": "started",
        "game_id": game_id,
        "game_name": game["name"],
        "target": str(target),
        "backend": plan["backend"],
        "pid": process.pid,
        "started_at": started_at,
        "compatibility_data": str(prefix_path) if prefix_path else None,
        "waited_for_exit": wait,
        "exit_code": None,
        "execution_started": True,
        "warnings": [
            "Launching an external runtime does not guarantee game compatibility, graphics support, DRM or anti-cheat operation."
        ],
    }
    try:
        _record_launch(game_id, exit_code=None, library_path=library_path)
    except DuckBridgeError as error:
        result["warnings"].append(f"game started, but library history was not updated: {error}")

    if wait:
        result["exit_code"] = process.wait()
        result["status"] = "finished"
        try:
            _record_launch(game_id, exit_code=result["exit_code"], library_path=library_path)
        except DuckBridgeError as error:
            result["warnings"].append(f"game exited, but its exit status was not saved: {error}")
    return result
