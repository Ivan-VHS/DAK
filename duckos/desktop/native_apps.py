"""Safe user-space discovery and launch for DuckOS's specialist projects."""

from __future__ import annotations

import importlib.util
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from .reaper import ReaperIntegrationError, ReaperWorkbench


class NativeApplicationError(RuntimeError):
    """Raised when a registered native application cannot be launched."""


APPLICATIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "reaper",
        "name": "Reaper",
        "repository": "Ivan-VHS/Reaper",
        "directory": "reaper",
        "runtime": "python",
        "platforms": ("windows", "linux", "macos"),
        "kind": "reaper-workbench",
    },
    {
        "id": "pytyliki",
        "name": "Pytyliki",
        "repository": "Ivan-VHS/Pytyliki",
        "directory": "pytyliki",
        "runtime": "native-win32",
        "platforms": ("windows",),
        "kind": "binary",
        "targets": (
            "build/Release/pytyliki-gui.exe",
            "build/pytyliki-gui.exe",
            "dist/pytyliki-gui.exe",
        ),
    },
    {
        "id": "oplague",
        "name": "OPlague",
        "repository": "Ivan-VHS/OPlague",
        "directory": "oplague",
        "runtime": "python-tk",
        "platforms": ("windows", "linux", "macos"),
        "kind": "python-script",
        "target": "oplague_app.py",
    },
    {
        "id": "ventusample",
        "name": "VentuSample",
        "repository": "Ivan-VHS/VentuSample",
        "directory": "ventusample",
        "runtime": "qt6-cxx20",
        "platforms": ("windows", "linux", "macos"),
        "kind": "binary",
        "targets_by_platform": {
            "windows": (
                "build/Release/VentuSample.exe",
                "build/VentuSample.exe",
            ),
            "linux": (
                "build/VentuSample",
            ),
            "macos": (
                "build/VentuSample.app/Contents/MacOS/VentuSample",
                "build/Release/VentuSample.app/Contents/MacOS/VentuSample",
                "build/VentuSample",
            ),
        },
    },
)


def _platform_name(value: str | None = None) -> str:
    raw = (value or platform.system()).strip().lower()
    if raw.startswith("win"):
        return "windows"
    if raw in {"darwin", "mac", "macos", "osx"}:
        return "macos"
    if raw.startswith("linux"):
        return "linux"
    return raw or "unknown"


class NativeApplicationHub:
    """Discover only allowlisted project entry points under DuckOS/projects."""

    def __init__(
        self,
        repository_root: str | Path | None = None,
        *,
        platform_name: str | None = None,
        python_executable: str | None = None,
    ) -> None:
        self.repository_root = Path(repository_root or Path(__file__).resolve().parents[2]).expanduser().resolve()
        self.platform_name = _platform_name(platform_name)
        self.python_executable = python_executable or sys.executable

    def _project_root(self, definition: dict[str, Any]) -> tuple[Path | None, str | None]:
        projects = self.repository_root / "projects"
        project = projects / str(definition["directory"])
        if projects.is_symlink() or project.is_symlink():
            return None, "The project checkout must not be a symbolic link."
        try:
            projects_root = projects.resolve(strict=True)
            project_root = project.resolve(strict=True)
        except OSError:
            return None, "The pinned source checkout is not initialized."
        if not projects_root.is_dir() or not project_root.is_dir():
            return None, "The pinned source checkout is not a directory."
        if not projects_root.is_relative_to(self.repository_root):
            return None, "The projects directory resolves outside the DuckOS workspace."
        if not project_root.is_relative_to(projects_root):
            return None, "The project checkout resolves outside DuckOS/projects."
        return project_root, None

    @staticmethod
    def _verified_file(project_root: Path, relative_path: str) -> Path | None:
        candidate = project_root / relative_path
        if candidate.is_symlink():
            return None
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            return None
        if not resolved.is_file() or not resolved.is_relative_to(project_root):
            return None
        return resolved

    @staticmethod
    def _base_record(definition: dict[str, Any], platform_name: str) -> dict[str, Any]:
        return {
            "schema": "duckos.native-application.v1",
            "id": definition["id"],
            "name": definition["name"],
            "repository": definition["repository"],
            "project_path": f"projects/{definition['directory']}",
            "runtime": definition["runtime"],
            "platform": platform_name,
            "available": False,
            "status": "unknown",
            "launch_target": None,
            "detail": "",
            "automatic_build": False,
        }

    def inspect(self, app_id: str) -> dict[str, Any]:
        definition = next((item for item in APPLICATIONS if item["id"] == app_id), None)
        if definition is None:
            raise NativeApplicationError(f"Unknown native application: {app_id}")

        record = self._base_record(definition, self.platform_name)
        project_root, error = self._project_root(definition)
        if error or project_root is None:
            record.update(status="checkout_missing", detail=error or "Source checkout is unavailable.")
            return record

        if self.platform_name not in definition["platforms"]:
            record.update(
                status="unsupported_platform",
                detail=f"{definition['name']} native GUI is not provided for {self.platform_name}.",
            )
            return record

        if definition["kind"] == "reaper-workbench":
            workbench = ReaperWorkbench(project_root, python_executable=self.python_executable)
            state = workbench.inspect()
            if not state.get("available") or "native_studio" not in state.get("capabilities", []):
                record.update(
                    status="runtime_unavailable",
                    detail=state.get("message", "Reaper Studio entry point is unavailable."),
                )
                return record
            record.update(
                available=True,
                status="ready",
                launch_target="python -m reaper.desktop",
                detail="Reaper Studio is available as a separate user-space process.",
            )
            return record

        if definition["kind"] == "python-script":
            if sys.version_info < (3, 10):
                record.update(
                    status="runtime_unavailable",
                    detail="OPlague requires Python 3.10 or newer.",
                )
                return record
            try:
                tkinter_available = importlib.util.find_spec("tkinter") is not None
            except (ImportError, ValueError):
                tkinter_available = False
            if not tkinter_available:
                record.update(
                    status="runtime_unavailable",
                    detail="OPlague requires Tkinter in the selected Python installation.",
                )
                return record
            target = self._verified_file(project_root, str(definition["target"]))
            if target is None:
                record.update(
                    status="source_incomplete",
                    detail="The OPlague desktop entry point is missing or invalid.",
                )
                return record
            record.update(
                available=True,
                status="ready",
                launch_target=str(target),
                detail="OPlague will open in its own Tk desktop window. Live PnP inventory is Windows-only.",
            )
            return record

        if definition["kind"] == "binary":
            targets = definition.get("targets")
            if targets is None:
                targets = definition.get("targets_by_platform", {}).get(self.platform_name, ())
            for relative_path in targets:
                target = self._verified_file(project_root, relative_path)
                if target is not None:
                    record.update(
                        available=True,
                        status="ready",
                        launch_target=str(target),
                        detail=f"Found the built native application at {relative_path}.",
                    )
                    return record
            record.update(
                status="not_built",
                detail=(
                    "The source is present, but its native GUI binary was not found. "
                    "Build the upstream project with its documented toolchain, then refresh."
                ),
            )
            return record

        record.update(status="unsupported", detail="No launcher is registered for this application.")
        return record

    def inspect_all(self) -> list[dict[str, Any]]:
        return [self.inspect(item["id"]) for item in APPLICATIONS]

    def open(self, app_id: str) -> subprocess.Popen[Any]:
        definition = next((item for item in APPLICATIONS if item["id"] == app_id), None)
        if definition is None:
            raise NativeApplicationError(f"Unknown native application: {app_id}")

        state = self.inspect(app_id)
        if not state["available"]:
            raise NativeApplicationError(state["detail"])

        project_root, error = self._project_root(definition)
        if error or project_root is None:
            raise NativeApplicationError(error or "Source checkout is unavailable.")

        if definition["kind"] == "reaper-workbench":
            try:
                return ReaperWorkbench(
                    project_root,
                    python_executable=self.python_executable,
                ).open_studio()
            except ReaperIntegrationError as exception:
                raise NativeApplicationError(str(exception)) from exception

        target = Path(state["launch_target"])
        if target.is_symlink() or not target.is_file() or not target.resolve(strict=True).is_relative_to(project_root):
            raise NativeApplicationError("The launch target changed after discovery; refresh the app catalogue.")

        if definition["kind"] == "python-script":
            command = [self.python_executable, str(target.resolve(strict=True))]
        else:
            command = [str(target.resolve(strict=True))]

        try:
            return subprocess.Popen(
                command,
                cwd=project_root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
                close_fds=True,
            )
        except OSError as error:
            raise NativeApplicationError(f"Cannot start {definition['name']}: {error}") from error
