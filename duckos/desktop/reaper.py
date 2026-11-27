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
from pathlib import Path
from typing import Any

MAX_OUTPUT_CHARS = 1_000_000
COMMAND_TIMEOUT_SECONDS = 30
SOURCE_SUFFIXES = {".rpr", ".most"}
SYNTAX_SOURCE_SUFFIXES = {
    ".rpr", ".most", ".py", ".pipe", ".ppl", ".lisp", ".lsp", ".scm",
    ".forth", ".fs", ".bf", ".b", ".bf93", ".befunge", ".polyglot",
}
MAX_SYNTAX_STEPS = 10_000_000


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
        if (root / "reaper" / "multisyntax.py").is_file():
            capabilities.extend(("multi_syntax_frontends", "polyglot_runner", "syntax_validation"))

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

    @staticmethod
    def _syntax_source_path(source: str | Path) -> Path:
        path = Path(source).expanduser()
        if path.is_symlink():
            raise ReaperIntegrationError("syntax source files must not be symbolic links")
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise ReaperIntegrationError(f"cannot open syntax source file: {error}") from error
        if not resolved.is_file() or resolved.suffix.casefold() not in SYNTAX_SOURCE_SUFFIXES:
            supported = ", ".join(sorted(SYNTAX_SOURCE_SUFFIXES))
            raise ReaperIntegrationError(f"select an existing source file with a supported syntax extension: {supported}")
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

    def syntax_registry(self) -> dict[str, Any]:
        state = self.inspect()
        if "multi_syntax_frontends" not in state["capabilities"]:
            raise ReaperIntegrationError("this Reaper checkout does not include the multi-syntax frontend registry")
        return self._run(["syntax", "--list", "--json"])

    def check_syntax(
        self,
        source: str | Path,
        *,
        syntax: str = "auto",
        polyglot: bool = False,
    ) -> dict[str, Any]:
        path = self._syntax_source_path(source)
        state = self.inspect()
        if "syntax_validation" not in state["capabilities"]:
            raise ReaperIntegrationError("this Reaper checkout does not include syntax-only validation")
        arguments = ["syntax", "--check", "--json", "--syntax", syntax]
        if polyglot:
            arguments.append("--polyglot")
        arguments.append(str(path))
        return self._run(arguments)

    def run_syntax(
        self,
        source: str | Path,
        *,
        syntax: str = "auto",
        polyglot: bool = False,
        max_steps: int = 1_000_000,
        input_text: str = "",
    ) -> dict[str, Any]:
        path = self._syntax_source_path(source)
        state = self.inspect()
        if "multi_syntax_frontends" not in state["capabilities"]:
            raise ReaperIntegrationError("this Reaper checkout does not include the multi-syntax runtime")
        if isinstance(max_steps, bool) or not isinstance(max_steps, int) or not 1 <= max_steps <= MAX_SYNTAX_STEPS:
            raise ReaperIntegrationError(f"max_steps must be between 1 and {MAX_SYNTAX_STEPS}")
        if not isinstance(input_text, str) or len(input_text) > 1_000_000:
            raise ReaperIntegrationError("input_text must be text no longer than 1,000,000 characters")
        arguments = [
            "syntax", "--json", "--syntax", syntax,
            "--steps", str(max_steps), "--input", input_text,
        ]
        if polyglot:
            arguments.append("--polyglot")
        arguments.append(str(path))
        return self._run(arguments, timeout=COMMAND_TIMEOUT_SECONDS)

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
