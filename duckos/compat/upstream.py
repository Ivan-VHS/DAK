"""Adapters for established Linux Windows-compatibility runtimes.

This layer discovers and coordinates upstream tools. PE loading, Win32 APIs,
graphics translation and Windows process semantics remain the responsibility
of those runtimes, not this module.
"""
from __future__ import annotations

import builtins
import os
import platform
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Sequence


SCHEMA = "duckos.compat-runtime-inventory.v1"
PREFIX_STORE = Path.home() / ".local" / "share" / "duckos" / "runtime-prefixes"
_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_GAME_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_MAX_ARGS = 128
_MAX_ARG_LENGTH = 4096


class RuntimeError(ValueError):
    """Raised when an upstream compatibility runtime cannot be used safely."""


def _executable(path: Path) -> bool:
    try:
        return path.is_file() and os.access(path, os.X_OK)
    except OSError:
        return False


def _existing_directories(paths: Sequence[Path]) -> list[Path]:
    found: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        try:
            resolved = path.expanduser().resolve()
        except (OSError, builtins.RuntimeError):
            continue
        key = str(resolved)
        if resolved.is_dir() and key not in seen:
            found.append(resolved)
            seen.add(key)
    return found


def _steam_libraries(home: Path, environ: dict[str, str]) -> list[Path]:
    candidates = [
        Path(environ[key])
        for key in ("STEAM_DIR", "STEAM_COMPAT_CLIENT_INSTALL_PATH")
        if environ.get(key)
    ]
    candidates.extend((
        home / ".steam" / "root",
        home / ".steam" / "steam",
        home / ".local" / "share" / "Steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / "data" / "Steam",
    ))
    roots = _existing_directories(candidates)
    libraries = list(roots)

    for root in roots:
        manifest = root / "steamapps" / "libraryfolders.vdf"
        try:
            if manifest.stat().st_size > 1024 * 1024:
                continue
            content = manifest.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for value in re.findall(r'"path"\s*"([^"]+)"', content):
            libraries.append(Path(value.replace("\\\\", "\\")))
    return _existing_directories(libraries)


def _find_proton(libraries: Sequence[Path]) -> tuple[Path | None, Path | None]:
    candidates: list[tuple[Path, Path]] = []
    for library in libraries:
        for folder in (
            library / "steamapps" / "common",
            library / "compatibilitytools.d",
            library / "steamapps" / "compatibilitytools.d",
        ):
            try:
                children = list(folder.iterdir())
            except OSError:
                continue
            for child in children:
                proton = child / "proton"
                if _executable(proton):
                    try:
                        resolved = proton.resolve(strict=True)
                    except (OSError, builtins.RuntimeError):
                        continue
                    candidates.append((resolved, library))
    if not candidates:
        return None, None
    candidates.sort(key=lambda entry: entry[0].parent.name.casefold(), reverse=True)
    return candidates[0]


def _flatpak_has(flatpak: str | None, app_id: str) -> bool:
    if not flatpak:
        return False
    try:
        result = subprocess.run(
            [flatpak, "info", app_id],
            capture_output=True,
            text=True,
            check=False,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _entry(runtime_id: str, title: str, command: str | Path | None, *,
           transport: str = "native", app_id: str | None = None,
           steam_root: Path | None = None, note: str) -> dict[str, Any]:
    return {
        "id": runtime_id,
        "name": title,
        "available": command is not None,
        "command": str(command) if command else None,
        "transport": transport,
        "flatpak_app": app_id,
        "steam_root": str(steam_root) if steam_root else None,
        "note": note,
    }


def detect_runtimes(*, home: Path | None = None,
                    environ: dict[str, str] | None = None,
                    which: Callable[[str], str | None] | None = None) -> dict[str, Any]:
    """Build a read-only inventory of the five supported host-side engines."""
    home = (home or Path.home()).expanduser()
    environ = dict(os.environ if environ is None else environ)
    find = which or shutil.which
    libraries = _steam_libraries(home, environ)
    proton, _proton_library = _find_proton(libraries)
    # Proton may live in a secondary Steam library. The client-install path
    # must still point at the actual Steam installation, not that library.
    client_root = environ.get("STEAM_COMPAT_CLIENT_INSTALL_PATH") or environ.get("STEAM_DIR")
    steam_root = Path(client_root).expanduser().resolve() if client_root else (
        libraries[0] if libraries else None
    )

    lutris = find("lutris")
    bottles = find("bottles-cli")
    flatpak = find("flatpak")
    lutris_flatpak = not lutris and _flatpak_has(flatpak, "net.lutris.Lutris")
    bottles_flatpak = not bottles and _flatpak_has(flatpak, "com.usebottles.bottles")
    if lutris_flatpak:
        lutris = flatpak
    if bottles_flatpak:
        bottles = flatpak

    crossover_paths = (
        Path("/opt/cxoffice/bin/wine"),
        home / "cxoffice" / "bin" / "wine",
    )
    crossover = next((path for path in crossover_paths if _executable(path)), None)
    wine = find("wine64") or find("wine")

    runtimes = [
        _entry("proton", "Proton", proton, transport="proton", steam_root=steam_root,
               note="Steam game runtime; launch planning requires a Steam App ID."),
        _entry("lutris", "Lutris", lutris,
               transport="flatpak" if lutris_flatpak else "native",
               app_id="net.lutris.Lutris" if lutris_flatpak else None,
               note="Game library and runner manager; launch an existing Lutris game ID."),
        _entry("bottles", "Bottles", bottles,
               transport="flatpak" if bottles_flatpak else "native",
               app_id="com.usebottles.bottles" if bottles_flatpak else None,
               note="Isolated Wine environments; each launch targets an existing bottle."),
        _entry("crossover", "CrossOver", crossover,
               note="Commercial CodeWeavers runtime; DuckOS does not inspect license status."),
        _entry("wine", "Wine", wine,
               note="General-purpose Wine runtime with optional WINEPREFIX isolation."),
    ]
    return {
        "schema": SCHEMA,
        "host": platform.system().lower(),
        "supported_host": platform.system().lower() == "linux",
        "steam_libraries": [str(path) for path in libraries],
        "runtimes": runtimes,
        "graphics_tools": {
            "vulkaninfo": bool(find("vulkaninfo")),
            "nvidia_smi": bool(find("nvidia-smi")),
            "glxinfo": bool(find("glxinfo")),
            "dri_devices": Path("/dev/dri").is_dir(),
        },
        "notes": [
            "Discovery is read-only; no packages, drivers, prefixes or settings are changed.",
            "Executable presence does not prove GPU acceleration, title compatibility or CrossOver activation.",
            "Anti-cheat support remains title-specific. DuckOS does not bypass or emulate kernel anti-cheat drivers.",
        ],
    }


_PREFERENCE: dict[str, tuple[str, ...]] = {
    "steam-game": ("proton", "lutris", "wine"),
    "multi-store": ("lutris", "bottles", "proton", "wine"),
    "isolated-app": ("bottles", "crossover", "wine", "proton"),
    "commercial-app": ("crossover", "bottles", "wine"),
    "windows-app": ("bottles", "wine", "crossover", "proton", "lutris"),
}


def recommend_runtime(scenario: str, inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    """Recommend the best installed engine for a bounded scenario."""
    if scenario not in _PREFERENCE:
        raise RuntimeError("Unknown scenario. Choose one of: " + ", ".join(_PREFERENCE))
    inventory = inventory or detect_runtimes()
    available = {
        item["id"]: item for item in inventory.get("runtimes", [])
        if item.get("available") is True
    }
    ranked = [runtime_id for runtime_id in _PREFERENCE[scenario] if runtime_id in available]
    return {
        "scenario": scenario,
        "recommended": available[ranked[0]] if ranked else None,
        "fallbacks": [available[runtime_id] for runtime_id in ranked[1:]],
    }


def _arguments(values: Sequence[str]) -> list[str]:
    if isinstance(values, (str, bytes)) or len(values) > _MAX_ARGS:
        raise RuntimeError("Provide at most 128 separate application arguments.")
    result: list[str] = []
    for value in values:
        if not isinstance(value, str) or len(value) > _MAX_ARG_LENGTH or "\x00" in value:
            raise RuntimeError("Arguments must be strings of at most 4096 characters without NUL bytes.")
        result.append(value)
    return result


def _name(value: str | None, label: str = "bottle") -> str:
    if not value or not _NAME.fullmatch(value) or value in {".", ".."}:
        raise RuntimeError(f"{label} must be a safe 1–64 character identifier.")
    return value


def _exe(value: str | Path | None) -> Path:
    if value is None:
        raise RuntimeError("Select an existing Windows .exe file.")
    try:
        path = Path(value).expanduser().resolve(strict=True)
    except (OSError, builtins.RuntimeError) as error:
        raise RuntimeError(f"Cannot resolve executable path: {error}") from error
    if not path.is_file() or path.suffix.casefold() != ".exe":
        raise RuntimeError("Launch target must be an existing .exe file.")
    return path


def build_launch_plan(runtime_id: str, *, executable: str | Path | None = None,
                      arguments: Sequence[str] = (), prefix: str | Path | None = None,
                      bottle: str | None = None, app_id: int | None = None,
                      game_id: str | None = None,
                      inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build an argv/environment plan without starting the selected program."""
    inventory = inventory or detect_runtimes()
    if inventory.get("supported_host") is not True:
        raise RuntimeError("Upstream compatibility launch adapters currently require a Linux host.")
    runtimes = {entry["id"]: entry for entry in inventory.get("runtimes", [])}
    runtime = runtimes.get(runtime_id)
    if not runtime or runtime.get("available") is not True:
        raise RuntimeError(f"{runtime_id} was not found on this host.")

    args = _arguments(arguments)
    command = runtime["command"]
    transport = runtime.get("transport", "native")
    env: dict[str, str] = {}
    cwd: str | None = None

    if runtime_id == "lutris":
        if args:
            raise RuntimeError("Set launch arguments in the Lutris game configuration.")
        if not game_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", game_id):
            raise RuntimeError("Lutris requires an installed game ID (letters, digits, underscore and dash).")
        uri = f"lutris:rungameid/{game_id}"
        argv = ([command, "run", runtime["flatpak_app"], uri]
                if transport == "flatpak" else [command, uri])
    else:
        target = _exe(executable)
        cwd = str(target.parent)
        if runtime_id == "wine":
            argv = [command, str(target), *args]
            if prefix:
                prefix_path = Path(prefix).expanduser().resolve()
                if prefix_path.exists() and not prefix_path.is_dir():
                    raise RuntimeError("WINEPREFIX must be a directory.")
                env["WINEPREFIX"] = str(prefix_path)
        elif runtime_id == "proton":
            if not isinstance(app_id, int) or isinstance(app_id, bool) or not 1 <= app_id <= 2147483647:
                raise RuntimeError("Proton launch requires a positive Steam App ID.")
            steam_root = runtime.get("steam_root")
            if not steam_root:
                raise RuntimeError("Could not resolve the Steam library root for Proton.")
            compat_data = Path(prefix).expanduser().resolve() if prefix else (
                Path.home() / ".local" / "share" / "duckos" / "proton-compatdata" / str(app_id)
            )
            if compat_data.exists() and not compat_data.is_dir():
                raise RuntimeError("Proton compatibility data path must be a directory.")
            env.update({
                "STEAM_COMPAT_CLIENT_INSTALL_PATH": str(steam_root),
                "STEAM_COMPAT_DATA_PATH": str(compat_data),
                "STEAM_COMPAT_APP_ID": str(app_id),
                "SteamAppId": str(app_id),
            })
            argv = [command, "run", str(target), *args]
        elif runtime_id == "bottles":
            bottle_name = _name(bottle)
            if transport == "flatpak":
                argv = [command, "run", "--command=bottles-cli", runtime["flatpak_app"],
                        "run", "--bottle", bottle_name, "--executable", str(target)]
            else:
                argv = [command, "run", "--bottle", bottle_name, "--executable", str(target)]
            if args:
                argv.extend(["--args", shlex.join(args)])
        elif runtime_id == "crossover":
            bottle_name = _name(bottle)
            # CrossOver's --cx-app interface expects the application executable
            # name as it is registered inside the selected bottle.
            argv = [command, "--bottle", bottle_name, "--cx-app", target.name, *args]
        else:
            raise RuntimeError(f"No launch adapter is implemented for {runtime_id}.")

    return {
        "schema": "duckos.upstream-launch-plan.v1",
        "runtime": runtime_id,
        "argv": argv,
        "environment": env,
        "working_directory": cwd,
        "shell": False,
        "requires_explicit_cli_action": True,
    }


def launch_application(runtime_id: str, **options: Any) -> dict[str, Any]:
    """Launch through an upstream runtime after an explicit CLI request."""
    plan = build_launch_plan(runtime_id, **options)
    environment = os.environ.copy()
    environment.update(plan["environment"])
    try:
        process = subprocess.Popen(
            plan["argv"],
            cwd=plan["working_directory"],
            env=environment,
            shell=False,
            close_fds=True,
            start_new_session=True,
        )
    except OSError as error:
        raise RuntimeError(f"Could not start {runtime_id}: {error}") from error
    return {**plan, "pid": process.pid, "started": True}


def create_runtime_environment(runtime_id: str, name: str, *,
                                architecture: str = "win64",
                                environment: str = "application",
                                store: str | Path | None = None,
                                inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a Bottles environment or a real Wine prefix; never overwrite one."""
    name = _name(name, "environment name")
    if architecture not in {"win32", "win64"}:
        raise RuntimeError("Architecture must be win32 or win64.")
    if environment not in {"application", "gaming"}:
        raise RuntimeError("Environment must be application or gaming.")
    inventory = inventory or detect_runtimes()
    runtimes = {entry["id"]: entry for entry in inventory.get("runtimes", [])}
    runtime = runtimes.get(runtime_id)
    if not runtime or runtime.get("available") is not True:
        raise RuntimeError(f"{runtime_id} was not found on this host.")

    if runtime_id == "bottles":
        command = runtime["command"]
        args = ["new", "--bottle-name", name, "--environment", environment, "--arch", architecture]
        if runtime.get("transport") == "flatpak":
            argv = [command, "run", "--command=bottles-cli", runtime["flatpak_app"], *args]
        else:
            argv = [command, *args]
        try:
            result = subprocess.run(argv, capture_output=True, text=True, check=False, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError(f"Bottles environment creation failed: {error}") from error
        if result.returncode:
            detail = (result.stderr or result.stdout or "unknown error").strip()[:1000]
            raise RuntimeError(f"Bottles environment creation failed: {detail}")
        return {"runtime": runtime_id, "name": name, "architecture": architecture,
                "environment": environment, "created": True, "argv": argv}

    if runtime_id == "wine":
        store_path = Path(store).expanduser() if store else PREFIX_STORE
        try:
            store_path.mkdir(parents=True, exist_ok=True)
            if store_path.is_symlink() or not store_path.is_dir():
                raise RuntimeError("Wine prefix store must be a real directory.")
            store_path = store_path.resolve(strict=True)
        except OSError as error:
            raise RuntimeError(f"Cannot prepare Wine prefix store: {error}") from error
        target = store_path / name
        if target.exists() or target.is_symlink():
            raise RuntimeError(f"Refusing to overwrite existing prefix: {target}")

        wineboot = Path(runtime["command"]).with_name("wineboot")
        if not _executable(wineboot):
            located = shutil.which("wineboot")
            if not located:
                raise RuntimeError("wineboot was not found next to Wine or on PATH.")
            wineboot = Path(located)
        created = False
        try:
            # Claim the path before handing it to wineboot so another process
            # cannot replace it with a symlink between our check and launch.
            target.mkdir(mode=0o700)
            created = True
            result = subprocess.run(
                [str(wineboot), "--init"],
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
                env={**os.environ, "WINEPREFIX": str(target), "WINEARCH": architecture},
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            if created:
                shutil.rmtree(target, ignore_errors=True)
            raise RuntimeError(f"Wine prefix initialization failed: {error}") from error
        if result.returncode:
            detail = (result.stderr or result.stdout or "unknown error").strip()[:1000]
            shutil.rmtree(target, ignore_errors=True)
            raise RuntimeError(f"Wine prefix initialization failed: {detail}")
        return {"runtime": runtime_id, "name": name, "architecture": architecture,
                "path": str(target), "created": True}

    raise RuntimeError("Only Wine and Bottles create environments through the current adapter API.")


def runtime_status(inventory: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return an install report without starting tools."""
    inventory = inventory or detect_runtimes()
    return {
        **inventory,
        "policy": {
            "steam-game": "Proton first",
            "multi-store": "Lutris first",
            "isolated-app": "Bottles first",
            "commercial-app": "CrossOver first",
        },
        "execution": "explicit CLI launch only; no Mora browser process bridge",
    }


__all__ = [
    "RuntimeError",
    "build_launch_plan",
    "create_runtime_environment",
    "detect_runtimes",
    "launch_application",
    "recommend_runtime",
    "runtime_status",
]
