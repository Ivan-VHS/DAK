"""Native user-space bridge for the independently versioned Reaper toolchain.

DuckOS owns discovery, policy, UI entry points and bounded process supervision.
Reaper owns its language grammar, runtime, compiler, LSP and DAP implementations.
No Reaper interpreter or native code is imported into the DuckOS process.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

MAX_OUTPUT_BYTES = 1_000_000
MAX_SOURCE_BYTES = 4 * 1024 * 1024
COMMAND_TIMEOUT_SECONDS = 30
EXECUTION_TIMEOUT_SECONDS = 60
BUILD_TIMEOUT_SECONDS = 120
SOURCE_SUFFIXES = {".rpr", ".most"}

DEFAULT_EXECUTION_LIMITS = {
    "steps": 1_000_000,
    "items": 100_000,
    "text_length": 1_000_000,
    "heap_bytes": 64 * 1024 * 1024,
    "open_resources": 64,
}
MAX_EXECUTION_LIMITS = {
    "steps": 10_000_000,
    "items": 1_000_000,
    "text_length": 16_000_000,
    "heap_bytes": 512 * 1024 * 1024,
    "open_resources": 256,
}


class ReaperIntegrationError(ValueError):
    """Raised when the Reaper checkout or a selected operation is invalid."""


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
        # An explicit path is authoritative. Do not silently switch checkouts.
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
                "capability_states": {},
                "runtime_boundary": "user-space",
                "execution_is_os_sandboxed": False,
                "message": (
                    "Reaper source checkout was not found. Initialize the "
                    "projects/reaper submodule or set DUCKOS_REAPER_ROOT."
                ),
            }

        cli_file = root / "reaper" / "cli.py"
        try:
            cli_source = cli_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            cli_source = ""

        capabilities = ["reference_runtime", "cli"]
        states = {
            "reference_runtime": "available",
            "cli": "available",
        }

        discovered = (
            ("native_studio", root / "reaper" / "desktop.py", "available"),
            ("static_typecheck", root / "reaper" / "typecheck.py", "available"),
            ("native_aot_subset", root / "reaper" / "native_compiler.py", "experimental"),
            ("language_server", root / "reaper" / "lsp.py", "available"),
            ("debug_adapter", root / "reaper" / "dap.py", "available"),
            ("toolchain_inventory", root / "reaper" / "toolchain_inventory.py", "available"),
            ("embedded_tooling", root / "reaper" / "embedded.py", "partial"),
            ("polyglot_tooling", root / "reaper" / "polyglot.py", "partial"),
            ("qcs_frontend", root / "reaper" / "qcs.py", "partial"),
        )
        for capability, module, maturity in discovered:
            if module.is_file():
                if capability != "static_typecheck" or '"typecheck"' in cli_source:
                    capabilities.append(capability)
                    states[capability] = maturity

        return {
            "schema": "duckos.reaper-workbench.v1",
            "available": True,
            "status": "ready",
            "repository": str(root),
            "python": self.python_executable,
            "capabilities": capabilities,
            "capability_states": states,
            "runtime_boundary": "user-space",
            "execution_is_os_sandboxed": False,
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
            raise ReaperIntegrationError("source files selected for Reaper operations must not be symbolic links")
        try:
            resolved = path.resolve(strict=True)
            info = resolved.stat()
        except OSError as error:
            raise ReaperIntegrationError(f"cannot open Reaper source file: {error}") from error
        if not resolved.is_file() or resolved.suffix.lower() not in SOURCE_SUFFIXES:
            raise ReaperIntegrationError("select an existing .rpr or .most source file")
        if info.st_size > MAX_SOURCE_BYTES:
            raise ReaperIntegrationError(f"Reaper source exceeds the {MAX_SOURCE_BYTES}-byte input limit")
        return resolved

    @staticmethod
    def _output_path(destination: str | Path, source: Path) -> Path:
        path = Path(destination).expanduser()
        if path.is_symlink():
            raise ReaperIntegrationError("build output must not be a symbolic link")
        resolved = path.resolve(strict=False)
        if resolved == source:
            raise ReaperIntegrationError("build output must not overwrite the Reaper source file")
        if resolved.exists() and not resolved.is_file():
            raise ReaperIntegrationError("build output must be a regular file path")
        if not resolved.parent.is_dir():
            raise ReaperIntegrationError("build output directory must already exist")
        return resolved

    def _run_command(
        self,
        command: list[str],
        *,
        timeout: int = COMMAND_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        root = self._require_repository()
        captured = {"stdout": bytearray(), "stderr": bytearray()}
        truncated = {"stdout": False, "stderr": False}

        try:
            process = subprocess.Popen(
                command,
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                shell=False,
            )
        except OSError as error:
            raise ReaperIntegrationError(f"cannot start Reaper: {error}") from error

        def drain(stream: Any, name: str) -> None:
            if stream is None:
                return
            try:
                while True:
                    chunk = stream.read(64 * 1024)
                    if not chunk:
                        return
                    remaining = max(0, MAX_OUTPUT_BYTES - len(captured[name]))
                    if remaining:
                        captured[name].extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        truncated[name] = True
            except OSError:
                # The parent closes a pipe after a timed-out child is killed.
                return

        readers = [
            threading.Thread(target=drain, args=(process.stdout, "stdout"), daemon=True),
            threading.Thread(target=drain, args=(process.stderr, "stderr"), daemon=True),
        ]
        for reader in readers:
            reader.start()

        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            process.wait()
            for reader in readers:
                reader.join(timeout=1)
            raise ReaperIntegrationError(
                f"Reaper command exceeded the {timeout}-second time limit"
            ) from error
        finally:
            for reader in readers:
                reader.join(timeout=2)

        stdout = bytes(captured["stdout"]).decode("utf-8", errors="replace")
        stderr = bytes(captured["stderr"]).decode("utf-8", errors="replace")
        payload: Any = None
        if stdout.strip():
            try:
                payload = json.loads(stdout)
            except json.JSONDecodeError:
                payload = None
        return {
            "ok": exit_code == 0,
            "exit_code": exit_code,
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
            "result": payload,
            "truncated": truncated["stdout"] or truncated["stderr"],
        }

    def _run(self, arguments: list[str], *, timeout: int = COMMAND_TIMEOUT_SECONDS) -> dict[str, Any]:
        command = [self.python_executable, "-m", "reaper", *arguments]
        return self._run_command(command, timeout=timeout)

    def _run_module(
        self,
        module: str,
        arguments: list[str],
        *,
        timeout: int = COMMAND_TIMEOUT_SECONDS,
    ) -> dict[str, Any]:
        command = [self.python_executable, "-m", module, *arguments]
        return self._run_command(command, timeout=timeout)

    def check(self, source: str | Path) -> dict[str, Any]:
        path = self._source_path(source)
        return self._run(["--check", "--json", str(path)])

    def typecheck(self, source: str | Path) -> dict[str, Any]:
        path = self._source_path(source)
        state = self.inspect()
        if "static_typecheck" not in state["capabilities"]:
            raise ReaperIntegrationError(
                "this Reaper checkout does not provide the integrated static type checker; update projects/reaper"
            )
        return self._run(["typecheck", str(path), "--json"])

    def module_graph(self, source: str | Path) -> dict[str, Any]:
        path = self._source_path(source)
        return self._run(["--module-graph", "--json", str(path)])

    def run(
        self,
        source: str | Path,
        *,
        limits: dict[str, int] | None = None,
        engine: str = "treewalk",
        profile: bool = False,
    ) -> dict[str, Any]:
        path = self._source_path(source)
        if engine not in {"treewalk", "vm"}:
            raise ReaperIntegrationError("engine must be 'treewalk' or 'vm'")

        selected = dict(DEFAULT_EXECUTION_LIMITS)
        if limits is not None:
            unknown = set(limits) - set(DEFAULT_EXECUTION_LIMITS)
            if unknown:
                raise ReaperIntegrationError(f"unknown Reaper execution limits: {', '.join(sorted(unknown))}")
            selected.update(limits)
        for name, value in selected.items():
            maximum = MAX_EXECUTION_LIMITS[name]
            if type(value) is not int or not 1 <= value <= maximum:
                raise ReaperIntegrationError(f"{name} must be an integer between 1 and {maximum}")

        arguments = [
            "--steps", str(selected["steps"]),
            "--items", str(selected["items"]),
            "--text-length", str(selected["text_length"]),
            "--heap-bytes", str(selected["heap_bytes"]),
            "--open-resources", str(selected["open_resources"]),
            "--engine", engine,
            "--json",
        ]
        if profile:
            arguments.append("--profile")
        arguments.append(str(path))
        return self._run(arguments, timeout=EXECUTION_TIMEOUT_SECONDS)

    def native_build(
        self,
        source: str | Path,
        output: str | Path,
        *,
        compiler: str | None = None,
        optimization: str = "2",
    ) -> dict[str, Any]:
        path = self._source_path(source)
        destination = self._output_path(output, path)
        if "native_aot_subset" not in self.inspect()["capabilities"]:
            raise ReaperIntegrationError("this Reaper checkout does not provide its experimental native AOT compiler")
        if optimization not in {"0", "1", "2", "3", "s"}:
            raise ReaperIntegrationError("optimization must be one of: 0, 1, 2, 3, s")
        arguments = ["--native", str(destination), "--optimization", optimization, "--json"]
        if compiler:
            if not compiler.strip():
                raise ReaperIntegrationError("compiler path must not be empty")
            arguments.extend(["--cc", compiler])
        arguments.append(str(path))
        return self._run(arguments, timeout=BUILD_TIMEOUT_SECONDS)

    def emit_c(
        self,
        source: str | Path,
        output: str | Path,
    ) -> dict[str, Any]:
        path = self._source_path(source)
        destination = self._output_path(output, path)
        if "native_aot_subset" not in self.inspect()["capabilities"]:
            raise ReaperIntegrationError("this Reaper checkout does not provide its experimental native AOT compiler")
        return self._run(["--emit-c", str(destination), "--json", str(path)], timeout=BUILD_TIMEOUT_SECONDS)

    def toolchain_inventory(self, *, search_path: str | None = None) -> dict[str, Any]:
        if "toolchain_inventory" not in self.inspect()["capabilities"]:
            raise ReaperIntegrationError("this Reaper checkout does not provide toolchain inventory")
        arguments = ["--path", search_path] if search_path is not None else []
        return self._run_module("reaper.toolchain_inventory", arguments)

    def serve_protocol(self, protocol: str) -> int:
        if protocol not in {"lsp", "dap"}:
            raise ReaperIntegrationError("protocol must be 'lsp' or 'dap'")
        state = self.inspect()
        capability = "language_server" if protocol == "lsp" else "debug_adapter"
        if capability not in state["capabilities"]:
            raise ReaperIntegrationError(f"this Reaper checkout does not provide the {protocol.upper()} service")
        root = self._require_repository()
        command = [self.python_executable, "-m", "reaper", protocol]
        try:
            # LSP/DAP are stdio protocols. Preserve the caller's three standard
            # streams exactly; do not capture or decorate protocol traffic.
            completed = subprocess.run(command, cwd=root, shell=False, check=False)
        except OSError as error:
            raise ReaperIntegrationError(f"cannot start Reaper {protocol.upper()} service: {error}") from error
        return completed.returncode

    def repl(self) -> int:
        root = self._require_repository()
        command = [self.python_executable, "-m", "reaper", "--repl"]
        try:
            completed = subprocess.run(command, cwd=root, shell=False, check=False)
        except OSError as error:
            raise ReaperIntegrationError(f"cannot start Reaper REPL: {error}") from error
        return completed.returncode

    def open_studio(self) -> subprocess.Popen[str]:
        root = self._require_repository()
        if "native_studio" not in self.inspect()["capabilities"]:
            raise ReaperIntegrationError("this Reaper checkout does not include Reaper Studio")
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
