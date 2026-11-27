"""Compatibility diagnostics and dry-run launch planning.

The current milestone deliberately stops before process creation. This keeps a
PE file from being mistaken for a loadable Windows process until Dak has a
real NT/Win32 runtime and kernel process ABI.
"""
from __future__ import annotations

import platform
from pathlib import Path
from typing import Any

from .pe import inspect_pe_file
from .prefix import read_prefix

SCHEMA = "dakos.windows-compat-report.v1"

_NATIVE_REQUIREMENTS = [
    "pe-image-loader",
    "nt-process-manager",
    "ntdll-and-win32-api",
    "wow64-and-x86-abi",
    "seh-veh-and-tls",
    "win32-handle-table",
    "registry-and-windows-installer",
    "directx-to-vulkan-backends",
    "wasapi-xaudio2-audio-bridge",
    "raw-input-xinput-bridge",
    "winsock2-and-iocp-bridge",
    "process-sandbox-and-device-broker",
]


def host_architecture(machine: str | None = None) -> str:
    value = (machine or platform.machine()).casefold()
    aliases = {
        "amd64": "x86_64", "x86_64": "x86_64", "x64": "x86_64",
        "i386": "x86", "i486": "x86", "i586": "x86", "i686": "x86", "x86": "x86",
        "aarch64": "aarch64", "arm64": "aarch64",
    }
    return aliases.get(value, "unknown")


def _has_casefolded_name(folder: Path, file_name: str) -> bool:
    try:
        return any(entry.name.casefold() == file_name.casefold() and entry.is_file()
                   for entry in folder.iterdir())
    except OSError:
        return False


def diagnose_binary(binary: str | Path, prefix_path: str | Path | None = None) -> dict[str, Any]:
    pe = inspect_pe_file(binary)
    prefix: dict[str, Any] | None = None
    search_dirs: list[Path] = [Path(binary).resolve().parent]
    if prefix_path is not None:
        prefix = read_prefix(prefix_path)
        prefix_root = Path(prefix["path"])
        search_dirs.extend([
            prefix_root / "drive_c/windows/system32",
            prefix_root / "drive_c/windows/syswow64",
            prefix_root / "drive_c/windows",
        ])

    available: list[str] = []
    missing: list[str] = []
    api_sets: list[str] = []
    for imported in pe["imports"]:
        normalized = imported.casefold()
        if normalized.startswith(("api-ms-win-", "ext-ms-win-")):
            api_sets.append(imported)
        elif any(
            (folder / imported).is_file() or _has_casefolded_name(folder, imported)
            for folder in search_dirs
        ):
            available.append(imported)
        else:
            missing.append(imported)

    host = host_architecture()
    architecture_matches = pe["architecture"] == host
    return {
        "schema": SCHEMA,
        "binary": pe,
        "prefix": prefix,
        "host_architecture": host,
        "architecture_matches_host": architecture_matches,
        "imports": {
            "available_in_search_paths": sorted(available, key=str.casefold),
            "missing_from_search_paths": sorted(missing, key=str.casefold),
            "api_set_contracts": sorted(api_sets, key=str.casefold),
        },
        "native_runtime": {
            "state": "not_implemented",
            "missing_components": list(_NATIVE_REQUIREMENTS),
        },
        "verdict": "inspectable_not_runnable",
        "launch_performed": False,
    }


def plan_launch(binary: str | Path, prefix_path: str | Path | None = None) -> dict[str, Any]:
    """Describe blockers for a future launch without ever starting the file."""
    report = diagnose_binary(binary, prefix_path)
    blockers = ["Dak does not yet contain a native NT/Win32 process runtime."]
    if report["binary"]["architecture"] == "unknown":
        blockers.append("The PE machine type is not supported by the compatibility profile.")
    if report["imports"]["missing_from_search_paths"]:
        blockers.append("One or more imported DLLs are not present in the inspected search paths.")
    if report["prefix"] is None:
        blockers.append("No isolated application prefix was selected.")
    else:
        binary_arch = report["binary"]["architecture"]
        prefix_arch = report["prefix"]["architecture"]
        compatible_prefix = prefix_arch == binary_arch or (binary_arch == "x86" and prefix_arch == "x86_64")
        if not compatible_prefix:
            blockers.append("The selected prefix architecture does not match the executable.")
    return {
        "schema": "dakos.windows-launch-plan.v1",
        "binary": str(Path(binary).expanduser()),
        "prefix": report["prefix"]["path"] if report["prefix"] else None,
        "status": "blocked_native_runtime_unavailable",
        "blockers": blockers,
        "next_step": "Implement and validate the native NT/Win32 runtime before enabling process creation.",
        "execution_performed": False,
        "disk_writes_performed": False,
    }


def compatibility_status() -> dict[str, Any]:
    return {
        "schema": "dakos.windows-compat-status.v1",
        "implemented": [
            "bounded PE32/PE32+ header and section inspection",
            "static import-DLL inventory",
            "file SHA-256 during local inspection",
            "isolated per-prefix directory creation and manifest validation",
            "static DLL search-path diagnostics",
            "dry-run launch blocker report",
        ],
        "not_implemented": list(_NATIVE_REQUIREMENTS),
        "launch_enabled": False,
        "kernel_integration": False,
        "driver_installation": False,
        "automatic_downloads": False,
    }
