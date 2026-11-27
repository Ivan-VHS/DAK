"""Validated, explicit game launch profiles for DuckOS.

This adapter can start a Windows executable only through an already-installed
Wine-compatible host runtime. It does not emulate Windows, change a prefix,
install dependencies, or launch anything during inspection or planning.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from .pe import PEFormatError, inspect_pe_file

SCHEMA = "duckos.game-launch-profile.v1"
MAX_PROFILE_BYTES = 1024 * 1024
MAX_ARGUMENTS = 256
MAX_ARGUMENT_LENGTH = 4096
ALLOWED_ENVIRONMENT = {"LANG", "LC_ALL", "LC_CTYPE", "TZ", "WINEDEBUG"}
GRAPHICS_APIS = {"directdraw", "direct3d7", "direct3d8", "direct3d9", "opengl", "glide"}
AUDIO_APIS = {"directsound", "winmm", "eax", "openal"}
INPUT_APIS = {"directinput", "xinput", "win32"}
NETWORK_APIS = {"tcp_ip", "directplay", "ipx_spx"}


class GameProfileError(ValueError):
    """Raised when a game profile is unsafe or malformed."""


def _text(value: Any, field: str, limit: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or "\x00" in value:
        raise GameProfileError(f"{field} must be a non-empty string of at most {limit} characters")
    return value.strip()


def _resolved_path(value: str, base: Path, field: str) -> Path:
    candidate = Path(value).expanduser()
    relative = not candidate.is_absolute()
    if relative:
        candidate = base / candidate
    if candidate.is_symlink():
        raise GameProfileError(f"{field} must not be a symbolic link")
    resolved = candidate.resolve(strict=True)
    if relative:
        try:
            resolved.relative_to(base)
        except ValueError as error:
            raise GameProfileError(f"relative {field} must stay inside the profile directory") from error
    return resolved


def load_game_profile(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise GameProfileError("profile path must be a regular, non-symlink file")
    try:
        if source.stat().st_size > MAX_PROFILE_BYTES:
            raise GameProfileError("profile exceeds the 1 MiB input limit")
        payload = json.loads(source.read_text(encoding="utf-8"))
    except OSError as error:
        raise GameProfileError(f"cannot read profile: {error}") from error
    except json.JSONDecodeError as error:
        raise GameProfileError(f"profile is not valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise GameProfileError("profile root must be a JSON object")
    return validate_game_profile(payload, source.parent)


def validate_game_profile(payload: dict[str, Any], base_directory: str | Path = ".") -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GameProfileError("profile root must be a JSON object")
    if payload.get("schema") != SCHEMA:
        raise GameProfileError(f"profile schema must be {SCHEMA}")
    game_id = _text(payload.get("id"), "id", 128)
    name = _text(payload.get("name"), "name", 128)
    base = Path(base_directory).expanduser().resolve()

    executable_value = _text(payload.get("executable"), "executable", 2048)
    executable = _resolved_path(executable_value, base, "executable")
    if not executable.is_file():
        raise GameProfileError("executable must point to a regular file")
    if executable.suffix.casefold() not in {".exe", ".com"}:
        raise GameProfileError("the current Wine adapter accepts Windows .exe and .com files only")

    working_value = payload.get("working_directory", ".")
    working_value = _text(working_value, "working_directory", 2048)
    working_directory = _resolved_path(working_value, base, "working_directory")
    if not working_directory.is_dir():
        raise GameProfileError("working_directory must point to an existing directory")

    arguments = payload.get("arguments", [])
    if not isinstance(arguments, list) or len(arguments) > MAX_ARGUMENTS:
        raise GameProfileError(f"arguments must be a list with at most {MAX_ARGUMENTS} entries")
    clean_arguments: list[str] = []
    for index, argument in enumerate(arguments):
        if not isinstance(argument, str) or len(argument) > MAX_ARGUMENT_LENGTH or "\x00" in argument:
            raise GameProfileError(f"arguments[{index}] must be text of at most {MAX_ARGUMENT_LENGTH} characters")
        clean_arguments.append(argument)

    runtime = payload.get("runtime")
    if not isinstance(runtime, dict) or runtime.get("backend") != "wine":
        raise GameProfileError("runtime.backend must be 'wine'; native Win32 execution is not implemented")
    runtime_executable = _text(runtime.get("executable", "wine"), "runtime.executable", 2048)
    prefix_value = runtime.get("prefix")
    prefix = None
    if prefix_value is not None:
        prefix_text = _text(prefix_value, "runtime.prefix", 2048)
        prefix = _resolved_path(prefix_text, base, "runtime.prefix")
        if not prefix.is_dir():
            raise GameProfileError("runtime.prefix must point to an existing directory")

    compatibility = payload.get("compatibility")
    if not isinstance(compatibility, dict):
        raise GameProfileError("compatibility must be an object")
    if compatibility.get("windows_version") != "windows-xp" or compatibility.get("service_pack") != 3:
        raise GameProfileError("this profile must explicitly target Windows XP Service Pack 3")
    apis: dict[str, list[str]] = {}
    for field, allowed in (
        ("graphics", GRAPHICS_APIS), ("audio", AUDIO_APIS),
        ("input", INPUT_APIS), ("network", NETWORK_APIS),
    ):
        values = compatibility.get(field, [])
        if not isinstance(values, list) or any(not isinstance(item, str) or item not in allowed for item in values):
            raise GameProfileError(f"compatibility.{field} contains an unsupported API")
        apis[field] = list(dict.fromkeys(values))

    display = compatibility.get("display", {})
    if not isinstance(display, dict):
        raise GameProfileError("compatibility.display must be an object")
    width = display.get("width", 1024)
    height = display.get("height", 768)
    color_depth = display.get("color_depth", 32)
    refresh = display.get("refresh_rate_hz", 60)
    for field, value, lower, upper in (
        ("width", width, 320, 16384), ("height", height, 200, 16384),
        ("color_depth", color_depth, 8, 32), ("refresh_rate_hz", refresh, 30, 360),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or not lower <= value <= upper:
            raise GameProfileError(f"compatibility.display.{field} must be an integer from {lower} to {upper}")
    if color_depth not in {8, 16, 24, 32}:
        raise GameProfileError("compatibility.display.color_depth must be 8, 16, 24 or 32")
    if not isinstance(display.get("windowed", False), bool):
        raise GameProfileError("compatibility.display.windowed must be a boolean")

    environment = payload.get("environment", {})
    if not isinstance(environment, dict):
        raise GameProfileError("environment must be an object")
    clean_environment: dict[str, str] = {}
    for key, value in environment.items():
        if key not in ALLOWED_ENVIRONMENT:
            raise GameProfileError(f"environment variable {key!r} is not allowed")
        if not isinstance(value, str) or len(value) > 1024 or "\x00" in value:
            raise GameProfileError(f"environment.{key} must be text of at most 1024 characters")
        clean_environment[key] = value

    return {
        "schema": SCHEMA,
        "id": game_id,
        "name": name,
        "executable": str(executable),
        "working_directory": str(working_directory),
        "arguments": clean_arguments,
        "runtime": {
            "backend": "wine",
            "executable": runtime_executable,
            "prefix": str(prefix) if prefix else None,
        },
        "compatibility": {
            "windows_version": "windows-xp",
            "service_pack": 3,
            **apis,
            "display": {
                "width": width, "height": height, "color_depth": color_depth,
                "refresh_rate_hz": refresh, "windowed": display.get("windowed", False),
            },
        },
        "environment": clean_environment,
    }


def plan_game_launch(
    profile: dict[str, Any],
    *,
    wine_binary: str | None = None,
) -> dict[str, Any]:
    """Build an argv-only plan; this function never creates a process."""
    clean = validate_game_profile(profile, Path(profile.get("working_directory", ".")).parent)
    executable = Path(clean["executable"])
    runtime_hint = wine_binary or clean["runtime"]["executable"]
    runtime_path = shutil.which(runtime_hint)
    if runtime_path is None and Path(runtime_hint).is_absolute():
        candidate = Path(runtime_hint)
        if candidate.is_file() and os.access(candidate, os.X_OK):
            runtime_path = str(candidate.resolve())
    blockers: list[str] = []
    architecture = "unknown"
    try:
        image = inspect_pe_file(executable)
        architecture = str(image.get("architecture", "unknown"))
        if architecture not in {"x86", "x86_64"}:
            blockers.append("The executable architecture is not supported by the current Wine launch adapter.")
    except (OSError, PEFormatError, ValueError) as error:
        blockers.append(f"PE inspection failed: {error}")
    if runtime_path is None:
        blockers.append(f"Wine runtime '{runtime_hint}' was not found as an executable on PATH.")
    prefix = clean["runtime"]["prefix"]
    if not prefix:
        blockers.append("Select an existing Wine prefix; implicit default-prefix creation is not allowed.")
    else:
        prefix_root = Path(prefix)
        if not (prefix_root / "system.reg").is_file() or not (prefix_root / "drive_c").is_dir():
            blockers.append("The selected directory is not an initialized Wine prefix (system.reg and drive_c are required).")
    argv = [runtime_path, str(executable), *clean["arguments"]] if runtime_path else []
    return {
        "schema": "duckos.game-launch-plan.v1",
        "game_id": clean["id"],
        "game_name": clean["name"],
        "target": "windows-xp-sp3",
        "architecture": architecture,
        "argv": argv,
        "working_directory": clean["working_directory"],
        "environment_overrides": {
            **clean["environment"],
            **({"WINEPREFIX": prefix} if prefix else {}),
        },
        "status": "ready" if not blockers else "blocked",
        "blockers": blockers,
        "execution_performed": False,
        "shell_used": False,
        "runtime_is_external": True,
        "native_win32_runtime": False,
        "target_version_enforced": False,
    }


def launch_game(
    profile: dict[str, Any],
    *,
    wine_binary: str | None = None,
    popen: Callable[..., Any] = subprocess.Popen,
) -> dict[str, Any]:
    """Start an explicit Wine process without a shell or implicit installers."""
    clean = validate_game_profile(profile, Path(profile.get("working_directory", ".")).parent)
    plan = plan_game_launch(clean, wine_binary=wine_binary)
    if plan["status"] != "ready":
        raise GameProfileError("; ".join(plan["blockers"]))
    environment = os.environ.copy()
    environment.update(plan["environment_overrides"])
    process = popen(
        plan["argv"],
        cwd=plan["working_directory"],
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
        close_fds=True,
        start_new_session=(os.name == "posix"),
    )
    return {
        "schema": "duckos.game-launch-result.v1",
        "game_id": clean["id"],
        "pid": int(process.pid),
        "started": True,
        "argv": plan["argv"],
        "working_directory": plan["working_directory"],
        "shell_used": False,
        "runtime_is_external": True,
        "native_win32_runtime": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="duckos-game", description="Inspect and launch games through an installed Wine runtime.")
    parser.add_argument("profile", type=Path, help="versioned DuckOS game profile JSON")
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--validate", action="store_true", help="validate the profile only")
    actions.add_argument("--plan", action="store_true", help="show the argv-only launch plan")
    actions.add_argument("--launch", action="store_true", help="start the game through Wine")
    parser.add_argument("--wine", help="explicit Wine executable; otherwise resolve runtime.executable")
    try:
        args = parser.parse_args(argv)
        profile = load_game_profile(args.profile)
        if args.validate:
            result = {"schema": "duckos.game-profile-validation.v1", "valid": True, "game_id": profile["id"]}
        elif args.plan:
            result = plan_game_launch(profile, wine_binary=args.wine)
        else:
            result = launch_game(profile, wine_binary=args.wine)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("valid") is True or result.get("started") is True:
            return 0
        return 1 if result.get("status") == "blocked" else 0
    except (GameProfileError, OSError, ValueError) as error:
        print(f"duckos-game: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
