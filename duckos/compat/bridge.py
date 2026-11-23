"""Runtime discovery and dry-run orchestration for DuckOS compatibility tools.

DuckBridge reuses the bounded PE parser in duckos.compat.pe. It can inspect
ELF headers and prepare argument-vector launch plans, but it never executes
an inspected program or starts a compatibility runtime.
"""
from __future__ import annotations

import os
import platform
import shlex
import shutil
from pathlib import Path
from typing import Any, Iterable

from .pe import PEFormatError, inspect_pe_file
from .runtime import host_architecture

SCHEMA_PLAN = "duckos.duckbridge-plan.v1"
SCHEMA_RUNTIMES = "duckos.duckbridge-runtimes.v1"
MAX_ELF_HEADER_BYTES = 4096

_ELF_MACHINES = {
    3: "x86",
    8: "mips",
    20: "ppc",
    21: "ppc64",
    22: "s390x",
    40: "arm",
    62: "x86_64",
    183: "aarch64",
    243: "riscv64",
}
_QEMU_COMMANDS = {
    "x86": "qemu-i386",
    "x86_64": "qemu-x86_64",
    "arm": "qemu-arm",
    "aarch64": "qemu-aarch64",
    "riscv64": "qemu-riscv64",
    "ppc": "qemu-ppc",
    "ppc64": "qemu-ppc64",
    "s390x": "qemu-s390x",
}


class DuckBridgeError(ValueError):
    """Raised when an inspection or launch-plan request is invalid."""


def _find_program(name: str, search_path: str | None) -> str | None:
    value = shutil.which(name, path=search_path)
    if value is None:
        return None
    candidate = Path(value)
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        return None
    return str(candidate.resolve())


def _is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _steam_roots(home: Path) -> tuple[Path, ...]:
    return (
        home / ".steam" / "steam",
        home / ".steam" / "root",
        home / ".local" / "share" / "Steam",
        home / ".var" / "app" / "com.valvesoftware.Steam" / ".local" / "share" / "Steam",
    )


def _find_proton(home: Path, search_path: str | None) -> str | None:
    direct = _find_program("proton", search_path)
    if direct:
        return direct

    candidates: set[Path] = set()
    for root in _steam_roots(home):
        common = root / "steamapps" / "common"
        tools = root / "compatibilitytools.d"
        if common.is_dir():
            candidates.update(common.glob("Proton*/proton"))
        if tools.is_dir():
            candidates.update(tools.glob("GE-Proton*/proton"))
    usable = [path for path in candidates if _is_executable(path)]
    if not usable:
        return None
    newest = max(usable, key=lambda path: path.stat().st_mtime)
    return str(newest.resolve())


def _find_crossover(home: Path) -> str | None:
    candidates = (
        home / "cxoffice" / "bin" / "wine",
        Path("/opt/cxoffice/bin/wine"),
        Path("/opt/cxoffice/bin/wine64"),
    )
    for candidate in candidates:
        if _is_executable(candidate):
            return str(candidate.resolve())
    return None


def _find_bottles(home: Path, search_path: str | None) -> list[str] | None:
    direct = _find_program("bottles-cli", search_path)
    if direct:
        return [direct]

    flatpak = _find_program("flatpak", search_path)
    if flatpak is None:
        return None

    app_roots = (
        home / ".local" / "share" / "flatpak" / "app" / "com.usebottles.bottles",
        Path("/var/lib/flatpak/app/com.usebottles.bottles"),
    )
    if any(root.is_dir() for root in app_roots):
        return [flatpak, "run", "--command=bottles-cli", "com.usebottles.bottles"]
    return None


def _runtime(runtime_id: str, label: str, command: list[str] | None,
             formats: Iterable[str], note: str) -> dict[str, Any]:
    return {
        "id": runtime_id,
        "label": label,
        "available": command is not None,
        "command": command,
        "formats": list(formats),
        "note": note,
    }


def detect_runtimes(*, search_path: str | None = None,
                    home: str | Path | None = None,
                    host_machine: str | None = None) -> dict[str, Any]:
    """Find installed entry points without invoking them or accessing the network."""
    home_path = Path(home).expanduser() if home is not None else Path.home()
    path_value = os.environ.get("PATH", "") if search_path is None else search_path
    host = host_architecture(host_machine or platform.machine())

    wine = _find_program("wine", path_value) or _find_program("wine64", path_value)
    proton = _find_proton(home_path, path_value)
    crossover = _find_crossover(home_path)
    bottles = _find_bottles(home_path, path_value)
    box64 = _find_program("box64", path_value)

    runtimes = [
        _runtime("wine", "Wine", [wine] if wine else None, ["pe"],
                 "Windows compatibility runtime; installed components, architecture and prefixes determine coverage."),
        _runtime("proton", "Proton", [proton] if proton else None, ["pe"],
                 "Steam-oriented Wine distribution; requires a caller-selected compatibility-data directory."),
        _runtime("crossover", "CrossOver", [crossover] if crossover else None, ["pe"],
                 "Commercial Wine-based runtime; requires the name of an existing CrossOver bottle."),
        _runtime("bottles", "Bottles", bottles, ["pe"],
                 "Bottle manager; requires the name of an existing bottle. Flatpak discovery does not start Flatpak."),
        _runtime("box64", "Box64", [box64] if box64 else None, ["elf-x86_64"],
                 "Can translate x86-64 Linux applications on supported ARM64 hosts."),
    ]

    for architecture, name in _QEMU_COMMANDS.items():
        executable = _find_program(name, path_value)
        runtimes.append(_runtime(
            f"qemu-{architecture}", f"QEMU user mode ({architecture})",
            [executable] if executable else None, [f"elf-{architecture}"],
            "CPU/ABI translation only; the target libraries and sysroot must be supplied separately.",
        ))

    return {
        "schema": SCHEMA_RUNTIMES,
        "host_architecture": host,
        "runtimes": runtimes,
        "discovery_performed_network_access": False,
        "runtime_processes_started": False,
    }


def _inspect_elf_file(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise DuckBridgeError("ELF input must be a regular file, not a symbolic link")
    try:
        size = path.stat().st_size
        with path.open("rb") as stream:
            data = stream.read(MAX_ELF_HEADER_BYTES)
    except OSError as error:
        raise DuckBridgeError(f"cannot read {path}: {error}") from error

    if len(data) < 20 or data[:4] != b"\x7fELF":
        raise DuckBridgeError("ELF identification or machine header is missing or incomplete")
    elf_class, encoding, version = data[4], data[5], data[6]
    if elf_class not in (1, 2):
        raise DuckBridgeError("unsupported ELF class")
    if encoding not in (1, 2):
        raise DuckBridgeError("invalid ELF byte order")
    if version != 1:
        raise DuckBridgeError("unsupported ELF identification version")

    byte_order = "little" if encoding == 1 else "big"
    file_type = int.from_bytes(data[16:18], byte_order)
    machine = int.from_bytes(data[18:20], byte_order)
    architecture = _ELF_MACHINES.get(machine, "unknown")
    if file_type not in (2, 3):
        raise DuckBridgeError("ELF file type is not an executable or position-independent executable")

    return {
        "format": "ELF",
        "architecture": architecture,
        "bits": 32 if elf_class == 1 else 64,
        "endianness": byte_order,
        "file_type": "ET_EXEC" if file_type == 2 else "ET_DYN",
        "machine": machine,
        "file_size_bytes": size,
    }


def inspect_binary(path: str | Path) -> dict[str, Any]:
    """Inspect a PE image via the shared parser or parse a bounded ELF header."""
    target = Path(path).expanduser()
    try:
        resolved = target.resolve(strict=True)
    except OSError as error:
        raise DuckBridgeError(f"cannot resolve {target}: {error}") from error
    if not resolved.is_file() or target.is_symlink():
        raise DuckBridgeError("input must be a regular file, not a symbolic link")

    try:
        with resolved.open("rb") as stream:
            magic = stream.read(4)
    except OSError as error:
        raise DuckBridgeError(f"cannot read {resolved}: {error}") from error

    if magic[:2] == b"MZ":
        try:
            pe = inspect_pe_file(resolved)
        except PEFormatError as error:
            raise DuckBridgeError(str(error)) from error
        return {
            "path": str(resolved),
            "format": pe["format"],
            "architecture": pe["architecture"],
            "bits": 64 if pe["format"] == "PE32+" else 32,
            "file_size_bytes": pe["file_size_bytes"],
            "sha256": pe["sha256"],
            "imports": pe["imports"],
            "pe_report": pe,
            "valid": True,
        }

    if magic == b"\x7fELF":
        report = _inspect_elf_file(resolved)
        return {"path": str(resolved), **report, "valid": True, "imports": []}

    return {
        "path": str(resolved),
        "format": "unknown",
        "architecture": "unknown",
        "bits": None,
        "file_size_bytes": resolved.stat().st_size,
        "valid": False,
        "reason": "file is neither a recognized PE nor ELF executable",
    }


def _runtime_by_id(inventory: dict[str, Any], runtime_id: str) -> dict[str, Any]:
    return next(
        (item for item in inventory["runtimes"] if item["id"] == runtime_id),
        {"id": runtime_id, "available": False, "command": None},
    )


def _base_plan(target: Path, binary: dict[str, Any], host: str, purpose: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA_PLAN,
        "status": "unsupported",
        "purpose": purpose,
        "target": str(target),
        "format": binary["format"],
        "architecture": binary["architecture"],
        "bits": binary["bits"],
        "host_architecture": host,
        "backend": None,
        "backend_available": False,
        "argv": [],
        "environment": {},
        "required_configuration": [],
        "execution_started": False,
        "prefix_created": False,
        "warnings": [],
        "binary_sha256": binary.get("sha256"),
        "imports": binary.get("imports", []),
    }


def _needs_configuration(plan: dict[str, Any], runtime: dict[str, Any],
                         required: list[str], warning: str) -> dict[str, Any]:
    plan.update({
        "status": "needs_configuration",
        "backend": runtime["id"],
        "backend_available": runtime["available"],
        "required_configuration": required,
        "warnings": [warning],
    })
    return plan


def build_launch_plan(path: str | Path, *, purpose: str = "application",
                      backend: str = "auto", bottle: str | None = None,
                      compat_data: str | Path | None = None,
                      wine_prefix: str | Path | None = None,
                      arguments: list[str] | None = None,
                      search_path: str | None = None,
                      home: str | Path | None = None,
                      host_machine: str | None = None) -> dict[str, Any]:
    """Prepare a reviewable argv/env plan. Does not start a runtime or target."""
    if purpose not in {"application", "game"}:
        raise DuckBridgeError("purpose must be 'application' or 'game'")
    if backend not in {"auto", "wine", "proton", "crossover", "bottles"}:
        raise DuckBridgeError("backend must be auto, wine, proton, crossover or bottles")
    extra_args = arguments or []
    if any(not isinstance(value, str) for value in extra_args):
        raise DuckBridgeError("all target arguments must be strings")

    target = Path(path).expanduser()
    try:
        resolved = target.resolve(strict=True)
    except OSError as error:
        raise DuckBridgeError(f"cannot resolve {target}: {error}") from error
    if not resolved.is_file() or target.is_symlink():
        raise DuckBridgeError("target must be a regular file, not a symbolic link")

    binary = inspect_binary(resolved)
    host = host_architecture(host_machine or platform.machine())
    plan = _base_plan(resolved, binary, host, purpose)
    if not binary["valid"]:
        plan["warnings"] = [binary.get("reason", "binary format is not supported")]
        return plan
    if binary["architecture"] == "unknown":
        plan["warnings"] = ["binary header is valid, but its CPU architecture is not supported"]
        return plan

    home_path = Path(home).expanduser() if home is not None else Path.home()
    inventory = detect_runtimes(
        search_path=search_path, home=home_path, host_machine=host
    )

    if binary["format"] == "ELF":
        architecture = binary["architecture"]
        if architecture == host:
            if not os.access(resolved, os.X_OK):
                plan["status"] = "needs_configuration"
                plan["required_configuration"] = ["executable-permission"]
                plan["warnings"] = ["target file is not marked executable"]
                return plan
            plan.update({
                "status": "ready", "backend": "native", "backend_available": True,
                "argv": [str(resolved), *extra_args],
                "warnings": ["Plan only: DuckBridge does not execute native ELF files."],
            })
            return plan

        if host == "aarch64" and architecture == "x86_64":
            box64 = _runtime_by_id(inventory, "box64")
            if box64["available"]:
                plan.update({
                    "status": "ready", "backend": "box64", "backend_available": True,
                    "argv": [*box64["command"], str(resolved), *extra_args],
                    "warnings": [box64["note"]],
                })
                return plan

        qemu = _runtime_by_id(inventory, f"qemu-{architecture}")
        if qemu["available"]:
            plan.update({
                "status": "ready", "backend": qemu["id"], "backend_available": True,
                "argv": [*qemu["command"], str(resolved), *extra_args],
                "warnings": [qemu["note"]],
            })
            return plan
        plan["warnings"] = [
            f"no native or detected user-mode translator is available for {architecture} on {host}"
        ]
        return plan

    if host != "x86_64":
        plan["warnings"] = [
            "PE runtime planning is currently scoped to x86-64 hosts; ARM64 requires a validated Wine/Box64 integration."
        ]
        return plan
    if binary["architecture"] not in {"x86", "x86_64"}:
        plan["warnings"] = [
            "The PE machine type is not supported by the current x86/x86-64 Wine backend profile."
        ]
        return plan

    order = (
        ["proton", "wine", "crossover", "bottles"]
        if purpose == "game"
        else ["wine", "crossover", "bottles", "proton"]
    )
    if backend == "auto":
        selected = next((
            _runtime_by_id(inventory, runtime_id)
            for runtime_id in order
            if _runtime_by_id(inventory, runtime_id)["available"]
        ), None)
    else:
        selected = _runtime_by_id(inventory, backend)
        if not selected["available"]:
            selected = None
    if selected is None:
        plan["warnings"] = ["no requested or suitable PE compatibility runtime was detected"]
        return plan

    runtime_id = selected["id"]
    command = selected["command"] or []
    if runtime_id == "proton":
        if not compat_data:
            return _needs_configuration(
                plan, selected, ["--compat-data"],
                "Proton requires a caller-selected compatibility-data directory.",
            )
        compat_path = Path(compat_data).expanduser().resolve()
        environment = {"STEAM_COMPAT_DATA_PATH": str(compat_path)}
        steam_root = next((root.resolve() for root in _steam_roots(home_path) if root.is_dir()), None)
        if steam_root:
            environment["STEAM_COMPAT_CLIENT_INSTALL_PATH"] = str(steam_root)
        argv = [*command, "run", str(resolved), *extra_args]
    elif runtime_id == "crossover":
        if not bottle:
            return _needs_configuration(
                plan, selected, ["--bottle"],
                "CrossOver requires the name of an existing bottle.",
            )
        environment = {}
        argv = [*command, "--bottle", bottle, "--cx-app", str(resolved), *extra_args]
    elif runtime_id == "bottles":
        if not bottle:
            return _needs_configuration(
                plan, selected, ["--bottle"],
                "Bottles CLI requires the name of an existing bottle.",
            )
        environment = {}
        argv = [*command, "run", "-b", bottle, "-e", str(resolved)]
        if extra_args:
            argv.extend(["-a", shlex.join(extra_args)])
    else:
        environment = {}
        if runtime_id == "wine" and wine_prefix is not None:
            environment["WINEPREFIX"] = str(Path(wine_prefix).expanduser().resolve())
        argv = [*command, str(resolved), *extra_args]

    plan.update({
        "status": "ready",
        "backend": runtime_id,
        "backend_available": True,
        "argv": argv,
        "environment": environment,
        "required_configuration": [],
        "warnings": [
            "Plan only: DuckBridge does not execute the command or create a compatibility prefix.",
            "Runtime presence does not guarantee Win32 API, graphics, DRM or anti-cheat compatibility.",
        ],
    })
    return plan
