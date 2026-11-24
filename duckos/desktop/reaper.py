"""Native launcher and read-only workflow bridge for the Reaper source checkout.

DuckOS does not import Reaper into the OS process. It discovers the pinned
specialist repository and invokes its Python CLI with an explicit argument
vector, bounded output, a timeout and no shell interpretation.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

MAX_OUTPUT_CHARS = 1_000_000
MAX_APP_INPUT_BYTES = 4 * 1024 * 1024
COMMAND_TIMEOUT_SECONDS = 30
SOURCE_SUFFIXES = {".rpr", ".most"}
APP_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")


class ReaperIntegrationError(ValueError):
    """Raised when the Reaper checkout or a selected source file is invalid."""


class ReaperWorkbench:
    def __init__(
        self,
        repository_root: str | Path | None = None,
        *,
        python_executable: str | None = None,
    ) -> None:
        self.python_executable = python_executable or sys.executable
        self.repository_root = self._find_repository(repository_root)

    @staticmethod
    def _is_repository(path: Path) -> bool:
        return (
            path.is_dir()
            and (path / "pyproject.toml").is_file()
            and (path / "reaper" / "__main__.py").is_file()
            and (path / "reaper" / "cli.py").is_file()
        )

    @classmethod
    def _validated_repository(cls, candidate: str | Path) -> Path | None:
        try:
            resolved = Path(candidate).expanduser().resolve(strict=True)
        except OSError:
            return None
        return resolved if cls._is_repository(resolved) else None

    @classmethod
    def _find_repository(cls, explicit: str | Path | None) -> Path | None:
        # Explicit configuration is authoritative. Never silently switch to a
        # different checkout when a caller supplied a missing or invalid path.
        if explicit is not None:
            return cls._validated_repository(explicit)

        configured = os.environ.get("DUCKOS_REAPER_ROOT")
        if configured:
            return cls._validated_repository(configured)

        package_root = Path(__file__).resolve().parents[2]
        candidates = (
            package_root / "projects" / "reaper",
            Path.cwd() / "projects" / "reaper",
            Path.cwd(),
        )

        seen: set[Path] = set()
        for candidate in candidates:
            try:
                resolved = candidate.resolve(strict=True)
            except OSError:
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            if cls._is_repository(resolved):
                return resolved
        return None

    @property
    def available(self) -> bool:
        return self.repository_root is not None

    def inspect(self) -> dict[str, Any]:
        root = self.repository_root
        if root is None:
            return {
                "schema": "duckos.reaper-workbench.v1",
                "available": False,
                "status": "not_found",
                "repository": None,
                "python": self.python_executable,
                "capabilities": [],
                "message": (
                    "Reaper source checkout was not found. Initialize the "
                    "projects/reaper submodule or set DUCKOS_REAPER_ROOT."
                ),
            }

        typecheck_file = root / "reaper" / "typecheck.py"
        cli_file = root / "reaper" / "cli.py"
        try:
            cli_source = cli_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            cli_source = ""

        capabilities = ["reference_runtime", "cli"]
        if (root / "reaper" / "desktop.py").is_file():
            capabilities.append("native_studio")
        if typecheck_file.is_file() and '"typecheck"' in cli_source:
            capabilities.append("static_typecheck")
        if (root / "reaper" / "native_compiler.py").is_file():
            capabilities.append("native_aot_subset")
        if (
            (root / "reaper" / "apps" / "__init__.py").is_file()
            and (root / "reaper" / "apps" / "manifest.json").is_file()
            and (root / "reaper" / "apps_cli.py").is_file()
            and 'arguments[0] == "apps"' in cli_source
        ):
            capabilities.append("application_suite")

        return {
            "schema": "duckos.reaper-workbench.v1",
            "available": True,
            "status": "ready",
            "repository": str(root),
            "python": self.python_executable,
            "capabilities": capabilities,
            "message": "Reaper is available as a local DuckOS developer tool.",
        }

    def _require_repository(self) -> Path:
        if self.repository_root is None or not self._is_repository(self.repository_root):
            raise ReaperIntegrationError(
                "Reaper checkout is unavailable; initialize projects/reaper or set DUCKOS_REAPER_ROOT"
            )
        return self.repository_root

    @staticmethod
    def _source_path(source: str | Path) -> Path:
        path = Path(source).expanduser()
        if path.is_symlink():
            raise ReaperIntegrationError("source files selected for checking must not be symbolic links")
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise ReaperIntegrationError(f"cannot open Reaper source file: {error}") from error
        if not resolved.is_file() or resolved.suffix.lower() not in SOURCE_SUFFIXES:
            raise ReaperIntegrationError("select an existing .rpr or .most source file")
        return resolved

    def _run(self, arguments: list[str], *, timeout: int = COMMAND_TIMEOUT_SECONDS) -> dict[str, Any]:
        root = self._require_repository()
        command = [self.python_executable, "-m", "reaper", *arguments]
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise ReaperIntegrationError(
                f"Reaper command exceeded the {timeout}-second time limit"
            ) from error
        except OSError as error:
            raise ReaperIntegrationError(f"cannot start Reaper: {error}") from error

        stdout = (completed.stdout or "")[:MAX_OUTPUT_CHARS]
        stderr = (completed.stderr or "")[:MAX_OUTPUT_CHARS]
        payload: Any = None
        if stdout.strip():
            try:
                payload = json.loads(stdout)
            except json.JSONDecodeError:
                payload = None
        return {
            "ok": completed.returncode == 0,
            "exit_code": completed.returncode,
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "result": payload,
            "truncated": len(completed.stdout or "") > MAX_OUTPUT_CHARS
            or len(completed.stderr or "") > MAX_OUTPUT_CHARS,
        }

    def check(self, source: str | Path) -> dict[str, Any]:
        path = self._source_path(source)
        return self._run(["--check", "--json", str(path)])

    def typecheck(self, source: str | Path) -> dict[str, Any]:
        path = self._source_path(source)
        state = self.inspect()
        if "static_typecheck" not in state["capabilities"]:
            raise ReaperIntegrationError(
                "this Reaper checkout predates the integrated static type checker; update the projects/reaper submodule"
            )
        return self._run(["typecheck", str(path), "--json"])

    def _require_application_suite(self) -> None:
        if "application_suite" not in self.inspect()["capabilities"]:
            raise ReaperIntegrationError(
                "this Reaper checkout does not contain the first-party application suite; update projects/reaper"
            )

    @staticmethod
    def _json_input_path(source: str | Path) -> Path:
        path = Path(source).expanduser()
        if path.is_symlink():
            raise ReaperIntegrationError("application JSON input must not be a symbolic link")
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise ReaperIntegrationError(f"cannot open application JSON input: {error}") from error
        if not resolved.is_file() or resolved.suffix.lower() != ".json":
            raise ReaperIntegrationError("application input must be an existing regular .json file")
        if resolved.stat().st_size > MAX_APP_INPUT_BYTES:
            raise ReaperIntegrationError(f"application JSON input exceeds {MAX_APP_INPUT_BYTES} bytes")
        return resolved

    @staticmethod
    def _json_output_path(destination: str | Path, source: Path) -> Path:
        path = Path(destination).expanduser()
        if path.is_symlink():
            raise ReaperIntegrationError("application JSON output must not be a symbolic link")
        if path.suffix.lower() != ".json":
            raise ReaperIntegrationError("application output must use the .json extension")
        if not path.parent.is_dir():
            raise ReaperIntegrationError("application output directory must already exist")
        if path.exists() and path.is_dir():
            raise ReaperIntegrationError("application output path must not be a directory")
        resolved = path.resolve()
        if resolved == source:
            raise ReaperIntegrationError("application output must not overwrite its input")
        return resolved

    def list_apps(self) -> dict[str, Any]:
        self._require_application_suite()
        return self._run(["apps", "list"])

    def describe_app(self, app_id: str) -> dict[str, Any]:
        self._require_application_suite()
        if not isinstance(app_id, str) or not APP_ID_PATTERN.fullmatch(app_id):
            raise ReaperIntegrationError("application ID must contain lowercase ASCII letters, digits and underscores")
        return self._run(["apps", "describe", app_id])

    def run_app(
        self,
        app_id: str,
        input_file: str | Path,
        output_file: str | Path | None = None,
    ) -> dict[str, Any]:
        self._require_application_suite()
        if not isinstance(app_id, str) or not APP_ID_PATTERN.fullmatch(app_id):
            raise ReaperIntegrationError("application ID must contain lowercase ASCII letters, digits and underscores")
        source = self._json_input_path(input_file)
        arguments = ["apps", "run", app_id, "--input", str(source)]
        if output_file is not None:
            destination = self._json_output_path(output_file, source)
            arguments.extend(["--output", str(destination)])
        return self._run(arguments)

    def open_studio(self) -> subprocess.Popen[str]:
        root = self._require_repository()
        command = [self.python_executable, "-m", "reaper.desktop"]
        try:
            return subprocess.Popen(
                command,
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=False,
                text=True,
            )
        except OSError as error:
            raise ReaperIntegrationError(f"cannot open Reaper Studio: {error}") from error
