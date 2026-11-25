"""Read-only desktop diagnostics and reversible per-user startup management."""
from __future__ import annotations

import csv
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

MAX_DESKTOP_ITEMS = 500
DEFAULT_DESKTOP_LIMIT = 10
TEMP_NAME_PARTS = (
    "untitled", "new document", "new folder", "screenshot", "screen shot",
    "скриншот", "новый документ", "новая папка", "безымянный",
)


def user_home(home: str | Path | None = None) -> Path:
    return Path(home).expanduser() if home is not None else Path.home()


def desktop_path(home: str | Path | None = None) -> Path:
    root = user_home(home)
    for path in (root / "Desktop", root / "Рабочий стол"):
        if path.is_dir():
            return path
    return root / "Desktop"


def list_desktop_items(home: str | Path | None = None, *, max_items: int = MAX_DESKTOP_ITEMS) -> dict[str, Any]:
    if isinstance(max_items, bool) or not isinstance(max_items, int) or not 1 <= max_items <= MAX_DESKTOP_ITEMS:
        raise ValueError(f"max_items must be between 1 and {MAX_DESKTOP_ITEMS}")
    root = desktop_path(home)
    if not root.exists():
        return {"path": str(root), "exists": False, "count": 0, "items": [], "truncated": False}
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Desktop path must be a regular directory")

    children = sorted(root.iterdir(), key=lambda item: item.name.casefold())
    rows = []
    for item in children[:max_items]:
        kind = "symlink" if item.is_symlink() else "folder" if item.is_dir() else "file" if item.is_file() else "other"
        try:
            size = item.lstat().st_size
        except OSError:
            size = None
        lowered = item.name.casefold()
        rows.append({
            "name": item.name,
            "kind": kind,
            "size_bytes": size,
            "looks_temporary": any(part in lowered for part in TEMP_NAME_PARTS),
            "safe_to_move": kind == "file",
        })
    return {
        "path": str(root), "exists": True, "count": len(children),
        "items": rows, "truncated": len(children) > max_items,
    }


def _unique_destination(folder: Path, name: str) -> Path:
    target = folder / name
    if not target.exists() and not target.is_symlink():
        return target
    source = Path(name)
    index = 2
    while True:
        target = folder / f"{source.stem} ({index}){source.suffix}"
        if not target.exists() and not target.is_symlink():
            return target
        index += 1


def move_desktop_items_to_inbox(names: list[str], home: str | Path | None = None) -> dict[str, Any]:
    """Move selected regular files to ~/Inbox, without deleting or overwriting."""
    if not isinstance(names, list) or not names or len(names) > MAX_DESKTOP_ITEMS:
        raise ValueError("Select between 1 and 500 desktop files")
    root, source_root = user_home(home), desktop_path(home)
    inbox = root / "Inbox"
    if source_root.is_symlink() or not source_root.is_dir():
        raise ValueError("Desktop directory is not available")
    inbox.mkdir(parents=True, exist_ok=True)
    if inbox.is_symlink() or not inbox.is_dir():
        raise ValueError("Inbox must be a regular directory")

    moved, rejected, seen = [], [], set()
    for name in names:
        if not isinstance(name, str) or not name or name in {".", ".."}:
            rejected.append({"name": str(name), "reason": "invalid file name"})
            continue
        if Path(name).name != name or "/" in name or "\\" in name:
            rejected.append({"name": name, "reason": "path components are not allowed"})
            continue
        if name in seen:
            continue
        seen.add(name)
        source = source_root / name
        if source.is_symlink() or not source.is_file():
            rejected.append({"name": name, "reason": "only regular files can be moved"})
            continue
        destination = _unique_destination(inbox, name)
        try:
            source.rename(destination)
        except OSError:
            try:
                shutil.move(str(source), str(destination))
            except OSError as error:
                rejected.append({"name": name, "reason": str(error)})
                continue
        moved.append({"name": name, "destination": str(destination)})
    return {
        "schema": "dak.desktop-move.v1", "moved": moved,
        "rejected": rejected, "deleted": 0, "overwritten": 0,
    }


def _linux_memory() -> tuple[int | None, int | None]:
    values: dict[str, int] = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            key, separator, rest = line.partition(":")
            match = re.match(r"\s*(\d+)", rest) if separator else None
            if match:
                values[key] = int(match.group(1)) * 1024
    except OSError:
        return None, None
    return values.get("MemTotal"), values.get("MemAvailable")


def _linux_processes(limit: int = 8) -> list[dict[str, Any]]:
    rows = []
    try:
        entries = Path("/proc").iterdir()
        for entry in entries:
            if not entry.name.isdigit():
                continue
            try:
                name = (entry / "comm").read_text(encoding="utf-8", errors="replace").strip()
                status = (entry / "status").read_text(encoding="ascii", errors="replace")
            except OSError:
                continue
            match = re.search(r"^VmRSS:\s+(\d+)\s+kB", status, re.MULTILINE)
            if match:
                rows.append({
                    "pid": int(entry.name), "name": name[:100],
                    "memory_bytes": int(match.group(1)) * 1024, "cpu_percent": None,
                })
    except OSError:
        return []
    return sorted(rows, key=lambda item: item["memory_bytes"], reverse=True)[:limit]


def _windows_memory() -> tuple[int | None, int | None]:
    try:
        import ctypes
        from ctypes import wintypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return None, None
        return int(status.ullTotalPhys), int(status.ullAvailPhys)
    except (AttributeError, ImportError, OSError, TypeError):
        return None, None


def _windows_processes(limit: int = 8) -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"], capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=4, shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode:
        return []
    rows = []
    for record in csv.reader(result.stdout.splitlines()):
        if len(record) < 5:
            continue
        try:
            pid = int(record[1].replace(",", ""))
            memory = int(re.sub(r"[^0-9]", "", record[4])) * 1024
        except ValueError:
            continue
        rows.append({"pid": pid, "name": record[0][:100], "memory_bytes": memory, "cpu_percent": None})
    return sorted(rows, key=lambda item: item["memory_bytes"], reverse=True)[:limit]


def host_snapshot(*, platform_name: str | None = None) -> dict[str, Any]:
    """Read host memory and a bounded process list; psutil is optional."""
    system = platform_name or platform.system()
    total = available = None
    cpu = None
    processes: list[dict[str, Any]] = []
    try:
        import psutil  # type: ignore[import-not-found]
        memory = psutil.virtual_memory()
        total, available = int(memory.total), int(memory.available)
        cpu = float(psutil.cpu_percent(interval=0.05))
        for process in psutil.process_iter(["pid", "name", "memory_info", "cpu_percent"]):
            try:
                info = process.info
                rss = info.get("memory_info")
                processes.append({
                    "pid": int(info.get("pid") or 0),
                    "name": str(info.get("name") or "Unknown")[:100],
                    "memory_bytes": int(rss.rss) if rss else 0,
                    "cpu_percent": float(info.get("cpu_percent") or 0.0),
                })
            except (OSError, ValueError, TypeError):
                continue
        processes.sort(key=lambda item: item["memory_bytes"], reverse=True)
        processes = processes[:8]
    except ImportError:
        if system == "Linux":
            total, available = _linux_memory()
            processes = _linux_processes()
        elif system == "Windows":
            total, available = _windows_memory()
            processes = _windows_processes()

    used = max(0, total - available) if total is not None and available is not None else None
    return {
        "platform": system, "architecture": platform.machine() or "unknown",
        "cpu_percent": round(cpu, 1) if cpu is not None else None,
        "memory_total_bytes": total, "memory_available_bytes": available,
        "memory_used_percent": round(used / total * 100, 1) if total and used is not None else None,
        "top_processes": processes, "collection": "local_read_only",
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".dak-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


class StartupManager:
    """Reversible controls for this user's startup folder and Windows HKCU Run."""

    def __init__(
        self, home: str | Path | None = None, *, platform_name: str | None = None,
        startup_dir: str | Path | None = None, disabled_dir: str | Path | None = None,
        backup_dir: str | Path | None = None,
    ) -> None:
        self.home = user_home(home)
        self.platform = platform_name or platform.system()
        if startup_dir is not None:
            self.startup_dir = Path(startup_dir)
        elif self.platform == "Windows":
            appdata = Path(os.environ.get("APPDATA", self.home / "AppData" / "Roaming"))
            self.startup_dir = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        else:
            self.startup_dir = self.home / ".config" / "autostart"
        self.disabled_dir = Path(disabled_dir) if disabled_dir is not None else self.home / ".config" / "dak" / "disabled-autostart"
        self.backup_dir = Path(backup_dir) if backup_dir is not None else self.home / ".config" / "dak" / "startup-backups"

    @staticmethod
    def _id(kind: str, name: str) -> str:
        return kind + ":" + quote(name, safe="")

    @staticmethod
    def _parse_id(value: str) -> tuple[str, str]:
        if not isinstance(value, str) or ":" not in value:
            raise ValueError("Invalid startup entry identifier")
        kind, encoded = value.split(":", 1)
        name = unquote(encoded)
        if kind not in {"folder", "registry"} or not name or Path(name).name != name or name in {".", ".."}:
            raise ValueError("Invalid startup entry identifier")
        if "/" in name or "\\" in name or "\x00" in name:
            raise ValueError("Invalid startup entry name")
        return kind, name

    def _folder_entries(self, folder: Path, enabled: bool) -> list[dict[str, Any]]:
        if folder.is_symlink() or not folder.is_dir():
            return []
        result = []
        for item in sorted(folder.iterdir(), key=lambda path: path.name.casefold()):
            if item.is_symlink() or not item.is_file():
                continue
            result.append({
                "id": self._id("folder", item.name), "name": item.name,
                "source": "startup_folder", "enabled": enabled, "path": str(item),
                "scope": "current_user", "reversible": True,
            })
        return result

    def _registry_entries(self) -> list[dict[str, Any]]:
        if self.platform != "Windows":
            return []
        try:
            import winreg
        except ImportError:
            return []
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        rows = []
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                index = 0
                while True:
                    try:
                        name, _value, value_type = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    rows.append({
                        "id": self._id("registry", name), "name": name,
                        "source": "user_registry_run", "enabled": True,
                        "path": "HKCU\\" + key_path, "value_type": int(value_type),
                        "scope": "current_user", "reversible": True,
                    })
                    index += 1
        except OSError:
            pass
        if self.backup_dir.is_dir() and not self.backup_dir.is_symlink():
            for backup in sorted(self.backup_dir.glob("registry-*.json")):
                try:
                    entry = json.loads(backup.read_text(encoding="utf-8"))
                    name = entry.get("name")
                    if isinstance(name, str) and name:
                        rows.append({
                            "id": self._id("registry", name), "name": name,
                            "source": "user_registry_run", "enabled": False,
                            "path": "HKCU\\" + key_path, "scope": "current_user", "reversible": True,
                        })
                except (OSError, ValueError, AttributeError):
                    continue
        return rows

    def list_entries(self) -> list[dict[str, Any]]:
        rows = self._folder_entries(self.startup_dir, True)
        rows.extend(self._folder_entries(self.disabled_dir, False))
        rows.extend(self._registry_entries())
        return sorted(rows, key=lambda row: (not row["enabled"], row["name"].casefold(), row["source"]))

    def set_enabled(self, entry_id: str, enabled: bool) -> dict[str, Any]:
        if not isinstance(enabled, bool):
            raise ValueError("enabled must be a boolean")
        kind, name = self._parse_id(entry_id)
        return self._set_folder(name, enabled) if kind == "folder" else self._set_registry(name, enabled)

    def _set_folder(self, name: str, enabled: bool) -> dict[str, Any]:
        source_dir = self.disabled_dir if enabled else self.startup_dir
        target_dir = self.startup_dir if enabled else self.disabled_dir

        for folder in (source_dir, target_dir):
            current = folder
            while current != self.home and current != current.parent:
                if current.exists() and current.is_symlink():
                    raise ValueError("Startup folder path contains a symbolic link")
                current = current.parent

        if source_dir.is_symlink() or target_dir.is_symlink():
            raise ValueError("Startup folders cannot be symbolic links")
        source, target = source_dir / name, target_dir / name
        if source.is_symlink() or not source.is_file():
            raise ValueError("Startup entry is not available in the expected user folder")
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"A startup entry named {name!r} already exists")
        target_dir.mkdir(parents=True, exist_ok=True)
        if target_dir.is_symlink() or not target_dir.is_dir():
            raise ValueError("Startup destination must be a regular directory")
        source.rename(target)
        return {
            "schema": "dak.startup-change.v1", "id": self._id("folder", name),
            "enabled": enabled, "scope": "current_user", "reversible": True, "path": str(target),
        }

    def _set_registry(self, name: str, enabled: bool) -> dict[str, Any]:
        if self.platform != "Windows":
            raise ValueError("Registry startup entries are available only on Windows")
        try:
            import winreg
        except ImportError as error:
            raise RuntimeError("Windows registry support is unavailable") from error
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        backup = self.backup_dir / ("registry-" + quote(name, safe="") + ".json")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        if self.backup_dir.is_symlink() or not self.backup_dir.is_dir():
            raise ValueError("Startup backup folder must be a regular directory")

        if enabled:
            if backup.is_symlink() or not backup.is_file():
                raise ValueError("No reversible backup exists for this startup entry")
            record = json.loads(backup.read_text(encoding="utf-8"))
            if record.get("name") != name or not isinstance(record.get("value"), str):
                raise ValueError("Startup backup identity or value is invalid")
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ) as key:
                    winreg.QueryValueEx(key, name)
            except FileNotFoundError:
                pass
            else:
                raise FileExistsError("A registry value with this name already exists; it will not be overwritten")
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, name, 0, int(record["value_type"]), record["value"])
            backup.unlink()
            return {"schema": "dak.startup-change.v1", "id": self._id("registry", name), "enabled": True, "scope": "current_user", "reversible": True}

        if backup.exists() or backup.is_symlink():
            raise FileExistsError("A startup backup already exists; inspect or restore it first")
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
                value, value_type = winreg.QueryValueEx(key, name)
                if value_type not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ) or not isinstance(value, str):
                    raise ValueError("Only string registry Run values can be backed up safely")
                _atomic_json(backup, {"name": name, "value": value, "value_type": int(value_type)})
                try:
                    winreg.DeleteValue(key, name)
                except OSError:
                    backup.unlink(missing_ok=True)
                    raise
        except FileNotFoundError as error:
            raise ValueError("Startup registry value was not found") from error
        return {"schema": "dak.startup-change.v1", "id": self._id("registry", name), "enabled": False, "scope": "current_user", "reversible": True}


class DesktopService:
    def __init__(self, home: str | Path | None = None) -> None:
        self.home = user_home(home)
        self.startup = StartupManager(self.home)

    def audit(self, *, item_limit: int = DEFAULT_DESKTOP_LIMIT) -> dict[str, Any]:
        desktop = list_desktop_items(self.home)
        startup = self.startup.list_entries()
        resources = host_snapshot()
        recommendations = []
        if desktop["count"] > item_limit:
            recommendations.append({
                "id": "desktop-clutter", "severity": "suggestion",
                "title": "Сократите количество элементов на рабочем столе",
                "detail": f"Сейчас {desktop['count']}; ориентир — не более {item_limit}. Ненужные файлы можно перенести в Inbox.",
            })
        temporary = [item["name"] for item in desktop["items"] if item["looks_temporary"]]
        if temporary:
            recommendations.append({
                "id": "temporary-names", "severity": "suggestion",
                "title": "Проверьте временные имена файлов",
                "detail": "Найдены элементы: " + ", ".join(temporary[:5]),
            })
        if desktop["truncated"]:
            recommendations.append({
                "id": "audit-truncated", "severity": "info",
                "title": "Список рабочего стола сокращён",
                "detail": f"В отчёт включены первые {MAX_DESKTOP_ITEMS} элементов.",
            })
        if not startup:
            recommendations.append({
                "id": "startup-empty", "severity": "info",
                "title": "Нет доступных пользовательских записей автозагрузки",
                "detail": "Другие системные механизмы запуска могут не отображаться в этом списке.",
            })
        return {
            "schema": "dak.desktop-audit.v1", "generated_at_unix": int(time.time()),
            "scope": "current_user_read_only", "desktop": desktop,
            "startup": {"count": sum(1 for item in startup if item["enabled"]), "entries": startup},
            "resources": resources, "recommendations": recommendations,
            "operations_performed": {
                "files_moved": 0, "files_deleted": 0, "startup_changed": 0, "processes_terminated": 0,
            },
        }


def audit_desktop(home: str | Path | None = None, *, item_limit: int = DEFAULT_DESKTOP_LIMIT) -> dict[str, Any]:
    if isinstance(item_limit, bool) or not isinstance(item_limit, int) or not 1 <= item_limit <= 100:
        raise ValueError("item_limit must be between 1 and 100")
    return DesktopService(home).audit(item_limit=item_limit)
