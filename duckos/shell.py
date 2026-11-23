"""Read-only host integration for the Mora desktop shell.

The browser shell owns presentation and local workspace preferences. This
module reports facts from the current host and validates the application
catalogue; it does not pretend to be a native compositor or kernel service.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

SHELL_STATUS_SCHEMA = "duckos.shell-host-status.v1"
SHELL_APPS_SCHEMA = "duckos.shell-app-catalog.v1"
SHELL_CHECK_SCHEMA = "duckos.shell-readiness.v1"
MAX_CATALOG_BYTES = 256 * 1024


class ShellError(ValueError):
    """Raised when a shell catalogue or requested inspection is invalid."""


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_memory() -> dict[str, int | None]:
    """Read available host memory counters when the platform exposes them."""
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        values: dict[str, int] = {}
        try:
            for line in meminfo.read_text(encoding="ascii").splitlines():
                name, separator, raw = line.partition(":")
                if not separator:
                    continue
                fields = raw.strip().split()
                if fields and fields[0].isdigit():
                    multiplier = 1024 if len(fields) > 1 and fields[1] == "kB" else 1
                    values[name] = int(fields[0]) * multiplier
            return {
                "total_bytes": values.get("MemTotal"),
                "available_bytes": values.get("MemAvailable"),
            }
        except (OSError, UnicodeError, ValueError):
            pass

    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        pages = os.sysconf("SC_PHYS_PAGES")
        available_pages = os.sysconf("SC_AVPHYS_PAGES")
        if page_size > 0 and pages > 0:
            return {
                "total_bytes": page_size * pages,
                "available_bytes": page_size * available_pages if available_pages > 0 else None,
            }
    except (AttributeError, OSError, ValueError):
        pass

    return {"total_bytes": None, "available_bytes": None}


def _display_backend(environ: dict[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    if env.get("WAYLAND_DISPLAY"):
        return "wayland"
    if env.get("DISPLAY"):
        return "x11"
    if sys.platform == "win32":
        return "windows-desktop"
    if sys.platform == "darwin":
        return "macos-window-server"
    return "not-detected"


def host_status(*, environ: dict[str, str] | None = None) -> dict[str, Any]:
    """Return real read-only host facts and explicit desktop implementation limits."""
    try:
        host = platform.uname()
    except OSError:
        host = None

    return {
        "schema": SHELL_STATUS_SCHEMA,
        "maturity_status": "partial",
        "runtime_state": "ready",
        "host": {
            "system": host.system if host else platform.system(),
            "release": host.release if host else platform.release(),
            "version": host.version if host else platform.version(),
            "machine": host.machine if host else platform.machine(),
            "hostname": host.node if host else platform.node(),
            "python_version": platform.python_version(),
            "logical_cpu_count": os.cpu_count(),
            "memory": _read_memory(),
        },
        "desktop": {
            "presentation": "mora-browser-shell",
            "display_backend": _display_backend(environ),
            "native_compositor": False,
            "native_window_manager": False,
            "kernel_session_manager": False,
            "note": "Mora currently presents the DuckOS desktop in a browser/PWA. Native compositor and kernel session services are not implemented.",
        },
        "available_capabilities": [
            "host.read",
            "shell.catalog.read",
            "shell.session.policy",
        ],
        "unsupported_capabilities": [
            "display.configure",
            "window.native.manage",
            "session.lock.native",
            "power.manage",
            "device.telemetry",
        ],
        "network_access_performed": False,
        "host_writes_performed": False,
    }


def read_app_catalog(path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate the local Mora app catalogue."""
    catalog_path = Path(path).expanduser() if path is not None else _project_root() / "mora" / "apps.json"
    if catalog_path.is_symlink():
        raise ShellError("app catalogue must not be a symbolic link")
    if not catalog_path.is_file():
        raise ShellError(f"app catalogue is missing: {catalog_path}")
    try:
        if catalog_path.stat().st_size > MAX_CATALOG_BYTES:
            raise ShellError("app catalogue exceeds 256 KiB")
        payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ShellError(f"cannot read app catalogue: {error}") from error

    if not isinstance(payload, list):
        raise ShellError("app catalogue must be a JSON array")

    apps: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, entry in enumerate(payload):
        if not isinstance(entry, dict):
            raise ShellError(f"app catalogue entry {index} must be an object")
        app_id = entry.get("id")
        name = entry.get("name")
        category = entry.get("category")
        panel = entry.get("panel")
        if not all(isinstance(value, str) and value.strip() for value in (app_id, name, category, panel)):
            raise ShellError(f"app catalogue entry {index} is missing id, name, category or panel")
        if app_id in seen:
            raise ShellError(f"duplicate app id: {app_id}")
        seen.add(app_id)
        apps.append({
            "id": app_id,
            "name": name,
            "category": category,
            "panel": panel,
            "maturity": entry.get("maturity", "specified"),
        })

    return {
        "schema": SHELL_APPS_SCHEMA,
        "catalogue": str(catalog_path.resolve()),
        "count": len(apps),
        "apps": apps,
    }


def readiness_report(*, project_root: str | Path | None = None,
                     catalogue_path: str | Path | None = None) -> dict[str, Any]:
    """Check source wiring and tool availability without starting host programs."""
    root = Path(project_root).expanduser() if project_root is not None else _project_root()
    required_files = [
        "mora/index.html",
        "mora/app.js",
        "mora/styles.css",
        "mora/shell.js",
        "duckos/ui/window_manager.rpr",
        "duckos/ui/desktop.rpr",
        "duckos/ui/notifications.rpr",
        "contract_tests.rpr",
    ]
    checks = [
        {"id": relative, "available": (root / relative).is_file()}
        for relative in required_files
    ]
    try:
        catalog = read_app_catalog(catalogue_path or (root / "mora" / "apps.json"))
        catalog_check = {"id": "mora/app-catalogue", "available": True, "count": catalog["count"]}
    except ShellError as error:
        catalog_check = {"id": "mora/app-catalogue", "available": False, "error": str(error)}

    checks.append(catalog_check)
    reaper_runtime = shutil.which("reaper")
    return {
        "schema": SHELL_CHECK_SCHEMA,
        "maturity_status": "partial",
        "checks": checks,
        "all_required_sources_present": all(item["available"] for item in checks),
        "reaper_runtime_available": reaper_runtime is not None,
        "reaper_runtime_path": reaper_runtime,
        "reaper_contracts_executed": False,
        "native_compositor_implemented": False,
        "host_processes_started": False,
    }
