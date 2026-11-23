"""Host-side compatibility runtime for DuckOS.
It manages user-owned Wine prefixes and starts explicitly selected programs.
No command shell is invoked.
"""
from __future__ import annotations

import ctypes.util
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
from typing import Any

STATUS_SCHEMA = "duckos.compatibility.status.v1"
PREFIX_SCHEMA = "duckos.compatibility.prefix.v1"
PREFIX_METADATA = ".duckos-prefix.json"
PREFIX_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,47}$")
COMPONENTS = frozenset({
    "corefonts", "d3dcompiler_47", "dotnet48", "dxvk",
    "vcrun2019", "vcrun2022", "vkd3d",
})


class CompatibilityError(ValueError):
    """Raised when a compatibility operation is unsafe or unavailable."""


def _program(*names: str) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def _proton_program() -> str | None:
    in_path = _program("proton")
    if in_path:
        return in_path

    roots = [
        Path.home() / ".steam" / "steam" / "steamapps" / "common",
        Path.home() / ".local" / "share" / "Steam" / "steamapps" / "common",
    ]
    steam_root = os.environ.get("STEAM_COMPAT_CLIENT_INSTALL_PATH")
    if steam_root:
        roots.insert(0, Path(steam_root).expanduser() / "steamapps" / "common")

    for root in roots:
        if not root.is_dir():
            continue
        for candidate in sorted(root.glob("Proton*/proton"), reverse=True):
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate.resolve())
    return None


def _data_root() -> Path:
    override = os.environ.get("DUCKOS_COMPATIBILITY_HOME")
    if override:
        configured = Path(override).expanduser()
        if not configured.is_absolute():
            raise CompatibilityError("DUCKOS_COMPATIBILITY_HOME must be an absolute path")
        return configured.resolve()
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")).expanduser()
    if not base.is_absolute():
        base = Path.home() / ".local" / "share"
    return (base / "duckos" / "compatibility").resolve()


def _validate_prefix_name(name: str) -> str:
    if not isinstance(name, str) or not PREFIX_NAME.fullmatch(name) or name in {".", ".."}:
        raise CompatibilityError(
            "prefix name must be 1..48 letters, digits, dots, underscores or hyphens"
        )
    return name


def _prefix_path(name: str) -> Path:
    name = _validate_prefix_name(name)
    root = _data_root()
    prefix_root = root / "prefixes"
    if prefix_root.is_symlink():
        raise CompatibilityError("symbolic-link prefix directories are not accepted")
    candidate = prefix_root / name
    if candidate.is_symlink():
        raise CompatibilityError("symbolic-link prefixes are not accepted")
    resolved = candidate.resolve()
    expected_parent = prefix_root.resolve()
    if resolved.parent != expected_parent:
        raise CompatibilityError("prefix path escaped the DuckOS data directory")
    return candidate


def _read_prefix(name: str) -> dict[str, Any]:
    path = _prefix_path(name)
    metadata = path / PREFIX_METADATA
    if path.is_symlink() or metadata.is_symlink() or not path.is_dir() or not metadata.is_file():
        raise CompatibilityError(f"managed prefix not found: {name}")
    try:
        if metadata.stat().st_size > 16 * 1024:
            raise CompatibilityError("prefix metadata exceeds the size limit")
        record = json.loads(metadata.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise CompatibilityError(f"cannot read prefix metadata: {error}") from error
    if (
        not isinstance(record, dict)
        or record.get("schema") != PREFIX_SCHEMA
        or record.get("name") != name
        or record.get("engine") != "wine"
        or record.get("architecture") not in {"win32", "win64"}
    ):
        raise CompatibilityError("prefix metadata is invalid or unsupported")
    record["path"] = str(path.resolve())
    return record


def list_prefixes() -> dict[str, Any]:
    root = _data_root() / "prefixes"
    prefixes = []
    if root.is_dir():
        for child in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
            try:
                prefixes.append(_read_prefix(child.name))
            except CompatibilityError:
                continue
    return {
        "schema": "duckos.compatibility.prefixes.v1",
        "root": str(root),
        "prefixes": prefixes,
    }


def _tool(name: str, command: str | None, role: str) -> dict[str, Any]:
    return {"id": name, "role": role, "available": command is not None, "path": command}


def compatibility_status() -> dict[str, Any]:
    linux = platform.system() == "Linux"
    wine = _program("wine", "wine64")
    proton = _proton_program()
    dosbox = _program("dosbox-staging", "dosbox")
    winetricks = _program("winetricks")
    qemu = _program("qemu-system-x86_64")
    tools = [
        _tool("wine", wine, "Win32 API compatibility runtime"),
        _tool("proton", proton, "Steam game compatibility runtime"),
        _tool("dosbox", dosbox, "DOS emulator"),
        _tool("winetricks", winetricks, "Wine dependency and graphics-layer installer"),
        _tool("dxvk", winetricks, "DXVK installer via Winetricks"),
        _tool("vkd3d", winetricks, "vkd3d installer via Winetricks"),
        _tool("crossover", _program("cxrun", "crossover", "cxoffice"), "Commercial Wine distribution"),
        _tool("bottles", _program("bottles"), "Prefix manager"),
        _tool("lutris", _program("lutris"), "Game launcher"),
        _tool("heroic", _program("heroic"), "Game launcher"),
        _tool("portproton", _program("portproton"), "Wine/Proton launcher"),
        _tool("playonlinux", _program("playonlinux"), "Wine prefix manager"),
        _tool("qemu", qemu, "Virtual machine monitor for separate guest operating systems"),
    ]
    graphics = {
        "vulkan_loader": ctypes.util.find_library("vulkan"),
        "vulkaninfo": _program("vulkaninfo"),
        "opengl_info": _program("glxinfo"),
    }
    return {
        "schema": STATUS_SCHEMA,
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "linux_runtime_supported": linux,
        },
        "prefix_root": str(_data_root() / "prefixes"),
        "tools": tools,
        "graphics": graphics,
        "limitations": [
            "Wine applications run with the current user's permissions; this is not a security sandbox.",
            "Anti-cheat bypass, kernel-driver loading and Windows kernel emulation are not provided.",
            "Whisky, Kegworks and Apple's Game Porting Toolkit are macOS-only.",
            "ReactOS is a separate operating system and must be run as a virtual machine guest.",
            "A detected executable or launcher is not proof that a particular game is compatible.",
        ],
    }


def create_prefix(name: str, architecture: str = "win64") -> dict[str, Any]:
    name = _validate_prefix_name(name)
    if platform.system() != "Linux":
        raise CompatibilityError("managed Wine prefixes are currently supported on Linux hosts only")
    if architecture not in {"win32", "win64"}:
        raise CompatibilityError("architecture must be win32 or win64")
    wineboot = _program("wineboot", "wineboot64")
    if not _program("wine", "wine64") or not wineboot:
        raise CompatibilityError("Wine and wineboot are required; install Wine before creating a prefix")

    root = _data_root() / "prefixes"
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = _prefix_path(name)
    if target.exists():
        raise CompatibilityError(f"prefix already exists: {name}")
    target.mkdir(mode=0o700)
    environment = os.environ.copy()
    environment.update({
        "WINEPREFIX": str(target.resolve()),
        "WINEARCH": architecture,
        "WINEDEBUG": "-all",
    })
    try:
        result = subprocess.run(
            [wineboot, "--init"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "wineboot returned a failure status").strip()
            raise CompatibilityError(f"wineboot failed: {detail[-1200:]}")
        record = {
            "schema": PREFIX_SCHEMA,
            "name": name,
            "engine": "wine",
            "architecture": architecture,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "path": str(target.resolve()),
        }
        temporary = target / (PREFIX_METADATA + ".tmp")
        temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        temporary.replace(target / PREFIX_METADATA)
        return record
    except (OSError, subprocess.TimeoutExpired, CompatibilityError) as error:
        shutil.rmtree(target, ignore_errors=True)
        if isinstance(error, CompatibilityError):
            raise
        raise CompatibilityError(f"could not initialize Wine prefix: {error}") from error


def install_component(prefix: str, component: str) -> dict[str, Any]:
    if component not in COMPONENTS:
        raise CompatibilityError(
            "unsupported component; choose one of: " + ", ".join(sorted(COMPONENTS))
        )
    record = _read_prefix(prefix)
    winetricks = _program("winetricks")
    if not winetricks:
        raise CompatibilityError("winetricks is not installed")
    environment = os.environ.copy()
    environment["WINEPREFIX"] = record["path"]
    environment["WINEARCH"] = record["architecture"]
    try:
        result = subprocess.run(
            [winetricks, "-q", component],
            env=environment,
            capture_output=True,
            text=True,
            timeout=1200,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CompatibilityError(f"Winetricks could not complete {component}: {error}") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "Winetricks returned a failure status").strip()
        raise CompatibilityError(f"Winetricks failed for {component}: {detail[-1200:]}")
    return {
        "schema": "duckos.compatibility.component.v1",
        "prefix": prefix,
        "component": component,
        "installed": True,
        "installer": winetricks,
    }


def _existing_file(value: str | Path) -> Path:
    try:
        path = Path(value).expanduser().resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise CompatibilityError(f"executable path does not exist: {value}") from error
    if not path.is_file():
        raise CompatibilityError("executable must be a regular file")
    return path


def launch_program(
    executable: str | Path,
    *,
    engine: str = "wine",
    prefix: str | None = None,
    compat_data: str | Path | None = None,
    arguments: list[str] | None = None,
) -> dict[str, Any]:
    if platform.system() != "Linux":
        raise CompatibilityError("launching through the DuckOS host runtime currently requires Linux")
    path = _existing_file(executable)
    extra = list(arguments or [])
    if any(not isinstance(item, str) or "\x00" in item for item in extra):
        raise CompatibilityError("program arguments must be ordinary text without NUL bytes")
    environment = os.environ.copy()

    if engine == "wine":
        if not prefix:
            raise CompatibilityError("Wine launch requires --prefix with a managed prefix name")
        record = _read_prefix(prefix)
        runner = _program("wine", "wine64")
        if not runner:
            raise CompatibilityError("Wine is not installed")
        environment["WINEPREFIX"] = record["path"]
        environment["WINEARCH"] = record["architecture"]
        argv = [runner, str(path), *extra]
    elif engine == "proton":
        if not compat_data:
            raise CompatibilityError("Proton launch requires --compat-data pointing to a Steam compatdata directory")
        runner = _proton_program()
        if not runner:
            raise CompatibilityError("Proton was not found in PATH or a standard Steam library")
        data_path = Path(compat_data).expanduser().resolve()
        if not data_path.is_dir():
            raise CompatibilityError("Proton compatdata path must be an existing directory")
        environment["STEAM_COMPAT_DATA_PATH"] = str(data_path)
        if "STEAM_COMPAT_CLIENT_INSTALL_PATH" not in environment:
            for steam_root in (
                Path.home() / ".steam" / "steam",
                Path.home() / ".local" / "share" / "Steam",
            ):
                if steam_root.is_dir():
                    environment["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(steam_root)
                    break
        argv = [runner, "run", str(path), *extra]
    elif engine == "dosbox":
        runner = _program("dosbox-staging", "dosbox")
        if not runner:
            raise CompatibilityError("DOSBox or DOSBox Staging is not installed")
        if path.suffix.lower() not in {".exe", ".com", ".bat"}:
            raise CompatibilityError("DOSBox accepts .exe, .com or .bat programs")
        if not re.fullmatch(r"[A-Za-z0-9_~-]{1,8}(?:\.[A-Za-z0-9_~-]{1,3})?", path.name):
            raise CompatibilityError("DOSBox direct launch requires an 8.3-compatible ASCII file name")
        parent = str(path.parent)
        if any(char in parent for char in '"\r\n\x00&|<>;%'):
            raise CompatibilityError("DOSBox mount path contains unsupported command characters")
        if any(any(char in arg for char in '"\r\n\x00&|<>;%') for arg in extra):
            raise CompatibilityError("DOSBox arguments contain unsupported command characters")
        program_line = path.name + "".join(
            " " + ('"' + arg + '"' if any(char.isspace() for char in arg) else arg)
            for arg in extra
        )
        argv = [
            runner,
            "-c", 'mount c "' + parent + '"',
            "-c", "c:",
            "-c", program_line,
            "-c", "exit",
        ]
    else:
        raise CompatibilityError("engine must be wine, proton or dosbox")

    try:
        process = subprocess.Popen(
            argv,
            cwd=str(path.parent),
            env=environment,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as error:
        raise CompatibilityError(f"could not start {engine}: {error}") from error
    return {
        "schema": "duckos.compatibility.launch.v1",
        "engine": engine,
        "executable": str(path),
        "pid": process.pid,
        "started": True,
        "shell_used": False,
    }
