"""Native launcher and read-only workflow bridge for the Reaper source checkout.

DuckOS does not import Reaper into the OS process. It discovers the pinned
specialist repository and invokes its Python CLI with an explicit argument
vector, bounded output, a timeout and no shell interpretation.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

MAX_OUTPUT_CHARS = 1_000_000
COMMAND_TIMEOUT_SECONDS = 30
SOURCE_SUFFIXES = {".rpr", ".most"}


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


    def build_native(
        self,
        source: str | Path,
        output: str | Path,
        *,
        optimization: str = "2",
    ) -> dict[str, Any]:
        """Build a host executable from Reaper's explicitly supported AOT subset."""
        path = self._source_path(source)
        if optimization not in {"0", "1", "2", "3", "s"}:
            raise ReaperIntegrationError("optimization must be one of 0, 1, 2, 3, or s")

        destination = Path(output).expanduser()
        if destination.is_symlink():
            raise ReaperIntegrationError("native output path must not be a symbolic link")
        try:
            resolved_output = destination.resolve(strict=False)
        except OSError as error:
            raise ReaperIntegrationError(f"cannot resolve native output path: {error}") from error
        if resolved_output == path:
            raise ReaperIntegrationError("native output must not overwrite its Reaper source file")
        if resolved_output.suffix.lower() in {".c", ".h", ".rpr", ".most"}:
            raise ReaperIntegrationError("native output must be an executable path, not a source file")
        return self._run(
            [str(path), "--native", str(resolved_output), "--optimization", optimization],
            timeout=150,
        )

    def check_duckos_target(self) -> dict[str, Any]:
        """Run the fixed DuckOS boot-contract conformance program in both Reaper engines."""
        root = self._require_repository()
        relative = Path("targets") / "duckos" / "boot_contract_v1.rpr"
        source = root / relative
        if source.is_symlink():
            raise ReaperIntegrationError("DuckOS target source must not be a symbolic link")
        try:
            resolved_source = source.resolve(strict=True)
        except OSError as error:
            raise ReaperIntegrationError(
                "this Reaper checkout does not contain the DuckOS boot-info v1 target"
            ) from error
        if root not in resolved_source.parents or not resolved_source.is_file():
            raise ReaperIntegrationError("DuckOS target source is outside the Reaper checkout")

        expected = "0\\n0\\n-2\\n-3\\n-4\\n-5\\n-6\\n-6\\n-7\\n"
        syntax = self._run(
            ["--check", "--syntax-only", str(resolved_source)],
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
        if not syntax["ok"]:
            raise ReaperIntegrationError(
                f"DuckOS Reaper target failed syntax validation: {syntax['stderr'][:2000]}"
            )

        reference = self._run([str(resolved_source)], timeout=COMMAND_TIMEOUT_SECONDS)
        if not reference["ok"] or reference["stdout"] != expected:
            raise ReaperIntegrationError(
                "DuckOS boot target reference output differs from its expected conformance matrix"
            )

        with tempfile.TemporaryDirectory(prefix="duckos-reaper-target-") as folder:
            output = Path(folder) / ("boot-contract.exe" if os.name == "nt" else "boot-contract")
            build = self._run(
                [str(resolved_source), "--native", str(output)],
                timeout=150,
            )
            if not build["ok"] or not output.is_file():
                raise ReaperIntegrationError(
                    f"DuckOS Reaper target native build failed: {build['stderr'][:2000]}"
                )
            try:
                completed = subprocess.run(
                    [str(output)],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=COMMAND_TIMEOUT_SECONDS,
                    shell=False,
                    check=False,
                )
            except subprocess.TimeoutExpired as error:
                raise ReaperIntegrationError("DuckOS native conformance program exceeded its time limit") from error
            except OSError as error:
                raise ReaperIntegrationError(f"cannot run DuckOS conformance executable: {error}") from error

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if len(stdout) > MAX_OUTPUT_CHARS or len(stderr) > MAX_OUTPUT_CHARS:
            raise ReaperIntegrationError("DuckOS conformance output exceeded the configured limit")
        if completed.returncode != 0 or stdout != expected:
            raise ReaperIntegrationError(
                "DuckOS Reaper native output differs from its expected conformance matrix"
            )
        return {
            "schema": "duckos.reaper-boot-target-check.v1",
            "valid": True,
            "target": relative.as_posix(),
            "fixtures": len(expected.splitlines()),
            "reference_runtime": "pass",
            "native_aot": "pass",
            "status_stream": expected.splitlines(),
            "native_program_executed": True,
            "hardware_accessed": False,
            "kernel_or_driver_state_changed": False,
        }

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
