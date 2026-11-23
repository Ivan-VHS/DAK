"""Read-only game-process discovery using explicit executable profiles.

A process-name match is only a candidate. Window, graphics-context and user
session evidence must be checked before DuckOS activates any gaming policy.
"""
from __future__ import annotations

import csv
import io
import json
import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

PROFILE_SCHEMA = "duckos.game-profile-catalog.v1"
DETECTION_SCHEMA = "duckos.game-process-detection.v1"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
MAX_PROFILE_BYTES = 256 * 1024
MAX_PROFILES = 512
MAX_PROCESSES = 4096
MAX_PROC_ENTRIES = 8192
MAX_COMMAND_OUTPUT = 2 * 1024 * 1024


class GamingDetectionError(ValueError):
    """Raised when a profile catalog or process snapshot is invalid."""


def load_game_profiles(path: str | Path) -> dict[str, Any]:
    """Load a bounded, regular profile file without following a symlink."""
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise GamingDetectionError("game profile catalog must be a regular, non-symlink file")
    if source.stat().st_size > MAX_PROFILE_BYTES:
        raise GamingDetectionError("game profile catalog exceeds the 256 KiB limit")
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GamingDetectionError(f"cannot read game profile catalog: {error}") from error
    _validate_profile_catalog(payload)
    return payload


def _validate_profile_catalog(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict) or payload.get("schema") != PROFILE_SCHEMA:
        raise GamingDetectionError(f"expected a {PROFILE_SCHEMA} object")
    if set(payload) != {"schema", "profiles"}:
        raise GamingDetectionError("profile catalog contains unknown or missing top-level fields")
    profiles = payload.get("profiles")
    if not isinstance(profiles, list) or not profiles or len(profiles) > MAX_PROFILES:
        raise GamingDetectionError(f"profiles must contain 1..{MAX_PROFILES} entries")
    seen_ids: set[str] = set()
    normalized = []
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict) or set(profile) - {"id", "name", "engine", "executables"}:
            raise GamingDetectionError(f"profiles[{index}] contains invalid fields")
        profile_id = profile.get("id")
        name = profile.get("name")
        engine = profile.get("engine", "unknown")
        executables = profile.get("executables")
        if not isinstance(profile_id, str) or not SAFE_ID.fullmatch(profile_id):
            raise GamingDetectionError(f"profiles[{index}].id must be a safe identifier")
        if profile_id in seen_ids:
            raise GamingDetectionError(f"duplicate game profile id: {profile_id}")
        seen_ids.add(profile_id)
        if not isinstance(name, str) or not name.strip() or len(name) > 128 or "\x00" in name:
            raise GamingDetectionError(f"profiles[{index}].name must contain 1..128 characters")
        if not isinstance(engine, str) or not SAFE_ID.fullmatch(engine):
            raise GamingDetectionError(f"profiles[{index}].engine must be a safe identifier")
        if not isinstance(executables, list) or not executables or len(executables) > 32:
            raise GamingDetectionError(f"profiles[{index}].executables must contain 1..32 names")
        cleaned = []
        for executable in executables:
            if (
                not isinstance(executable, str) or not executable.strip()
                or len(executable) > 128 or "\x00" in executable
                or "/" in executable or "\\" in executable
                or executable in {".", ".."}
            ):
                raise GamingDetectionError(f"profiles[{index}] contains an unsafe executable name")
            cleaned.append(executable.strip().casefold())
        if len(cleaned) != len(set(cleaned)):
            raise GamingDetectionError(f"profiles[{index}] contains duplicate executable names")
        normalized.append({
            "id": profile_id,
            "name": name.strip(),
            "engine": engine,
            "executables": set(cleaned),
        })
    return normalized


def _linux_processes() -> list[dict[str, Any]]:
    root = Path("/proc")
    if not root.is_dir():
        raise GamingDetectionError("Linux procfs is not mounted")
    result = []
    try:
        entries = root.iterdir()
        for index, entry in enumerate(entries):
            if index >= MAX_PROC_ENTRIES:
                break
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
                executable = os.readlink(entry / "exe")
                executable_name = Path(executable.removesuffix(" (deleted)")).name
                if not executable_name:
                    executable_name = (entry / "comm").read_text(encoding="utf-8", errors="replace").strip()
            except (OSError, ValueError, UnicodeError):
                continue
            if executable_name:
                result.append({"pid": pid, "executable_name": executable_name, "source": "linux-procfs"})
            if len(result) >= MAX_PROCESSES:
                break
    except OSError as error:
        raise GamingDetectionError(f"cannot enumerate Linux process table: {error}") from error
    return result


def _windows_processes() -> list[dict[str, Any]]:
    try:
        completed = subprocess.run(
            ["tasklist.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GamingDetectionError(f"Windows process inventory failed: {error}") from error
    if completed.returncode != 0:
        raise GamingDetectionError((completed.stderr or "tasklist.exe returned an error").strip())
    if len(completed.stdout.encode("utf-8", errors="replace")) > MAX_COMMAND_OUTPUT:
        raise GamingDetectionError("Windows process inventory exceeds the output limit")
    result = []
    for row in csv.reader(io.StringIO(completed.stdout)):
        if len(row) < 2:
            continue
        try:
            pid = int(row[1])
        except ValueError:
            continue
        executable_name = row[0].strip()
        if pid > 0 and executable_name:
            result.append({"pid": pid, "executable_name": executable_name, "source": "windows-tasklist"})
        if len(result) >= MAX_PROCESSES:
            break
    return result


def _macos_processes() -> list[dict[str, Any]]:
    try:
        completed = subprocess.run(
            ["ps", "-axo", "pid=,comm="],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GamingDetectionError(f"macOS process inventory failed: {error}") from error
    if completed.returncode != 0:
        raise GamingDetectionError((completed.stderr or "ps returned an error").strip())
    if len(completed.stdout.encode("utf-8", errors="replace")) > MAX_COMMAND_OUTPUT:
        raise GamingDetectionError("macOS process inventory exceeds the output limit")
    result = []
    for line in completed.stdout.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        name = Path(parts[1].strip()).name
        if pid > 0 and name:
            result.append({"pid": pid, "executable_name": name, "source": "macos-ps"})
        if len(result) >= MAX_PROCESSES:
            break
    return result


def enumerate_host_processes() -> list[dict[str, Any]]:
    """Return only PIDs and executable names; never collect command-line arguments."""
    system = platform.system()
    if system == "Linux":
        return _linux_processes()
    if system == "Windows":
        return _windows_processes()
    if system == "Darwin":
        return _macos_processes()
    raise GamingDetectionError(f"process discovery is not supported on {system or 'unknown'}")


def detect_game_processes(
    profile_catalog: dict[str, Any],
    *,
    processes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Match exact executable basenames to explicit profiles; never auto-activate."""
    profiles = _validate_profile_catalog(profile_catalog)
    process_rows = enumerate_host_processes() if processes is None else processes
    if not isinstance(process_rows, list) or len(process_rows) > MAX_PROCESSES:
        raise GamingDetectionError(f"process snapshot must contain at most {MAX_PROCESSES} records")

    matches = []
    for index, process in enumerate(process_rows):
        if not isinstance(process, dict):
            raise GamingDetectionError(f"processes[{index}] must be an object")
        pid = process.get("pid")
        executable = process.get("executable_name")
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            raise GamingDetectionError(f"processes[{index}].pid must be a positive integer")
        if not isinstance(executable, str) or not executable.strip() or len(executable) > 256:
            raise GamingDetectionError(f"processes[{index}].executable_name must be non-empty text")
        executable = Path(executable.strip()).name.casefold()
        if not executable:
            raise GamingDetectionError(f"processes[{index}].executable_name is invalid")
        candidates = [profile for profile in profiles if executable in profile["executables"]]
        for profile in candidates:
            matches.append({
                "game_id": profile["id"],
                "game_name": profile["name"],
                "engine": profile["engine"],
                "pid": pid,
                "executable_name": executable,
                "evidence": ["exact_executable_basename"],
                "confidence": "candidate",
                "ambiguous_profile_match": len(candidates) > 1,
            })

    return {
        "schema": DETECTION_SCHEMA,
        "profile_count": len(profiles),
        "processes_examined": len(process_rows),
        "candidate_count": len(matches),
        "candidates": matches,
        "window_state_checked": False,
        "graphics_context_checked": False,
        "automatic_activation_allowed": False,
        "requires_session_confirmation": True,
        "command_line_arguments_collected": False,
        "system_settings_changed": False,
        "execution_performed": False,
    }
