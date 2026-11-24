"""Process-isolated launcher for the Beelzebub AV Java application."""
from __future__ import annotations

import json
import os
import shutil
import site
import subprocess
import sysconfig
from pathlib import Path
from typing import Any


class BeelzebubIntegrationError(RuntimeError):
    """Raised when the native Beelzebub AV runtime cannot be started safely."""


class BeelzebubWorkbench:
    def __init__(self, root: Path | None = None) -> None:
        repository = Path(__file__).resolve().parents[2]
        configured = root or (Path(os.environ["DUCKOS_BEELZEBUB_ROOT"]) if os.environ.get("DUCKOS_BEELZEBUB_ROOT") else None)
        self.repository_root = (configured or repository).expanduser().resolve()
        source_tree_app = self.repository_root / "apps" / "beelzebub-av"
        packaged_apps = [
            Path(sysconfig.get_path("data")) / "share" / "duckos" / "apps" / "beelzebub-av",
            Path(site.getuserbase()) / "share" / "duckos" / "apps" / "beelzebub-av",
        ]
        if configured is not None:
            self.application_root = source_tree_app
        else:
            self.application_root = next(
                (candidate for candidate in [source_tree_app, *packaged_apps] if candidate.is_dir()),
                source_tree_app,
            )
        cache_override = os.environ.get("DUCKOS_BEELZEBUB_CACHE")
        if cache_override:
            cache_root = Path(cache_override).expanduser()
        elif os.name == "nt":
            cache_root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "DuckOS" / "Cache" / "BeelzebubAV"
        else:
            cache_root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "duckos" / "beelzebub-av"
        self.build_directory = cache_root / "build"
        self.classes_directory = self.build_directory / "classes"
        self.jar_path = self.build_directory / "beelzebub-av.jar"

    def inspect(self) -> dict[str, Any]:
        java, javac, jar = shutil.which("java"), shutil.which("javac"), shutil.which("jar")
        source_root = self.application_root / "src" / "main" / "java"
        sources = sorted(source_root.rglob("*.java")) if source_root.is_dir() and not source_root.is_symlink() else []
        missing = [name for name, executable in (("java", java), ("javac", javac), ("jar", jar)) if not executable]
        if not sources:
            missing.append("Java sources")
        return {
            "schema": "duckos.beelzebub-status.v1",
            "available": not missing,
            "java": java,
            "javac": javac,
            "jar": jar,
            "source_files": len(sources),
            "built": self.jar_path.is_file() and not self.jar_path.is_symlink(),
            "jar_path": str(self.jar_path),
            "repository": str(self.repository_root),
            "application_root": str(self.application_root),
            "build_directory": str(self.build_directory),
            "missing": missing,
            "execution_boundary": "separate-user-space-process",
        }

    def _ensure_built(self) -> None:
        state = self.inspect()
        if not state["available"]:
            raise BeelzebubIntegrationError(
                "Beelzebub AV requires JDK 17+ (java, javac and jar). Missing: " + ", ".join(state["missing"])
            )
        for path in (self.application_root, self.build_directory, self.classes_directory, self.jar_path):
            if path.is_symlink():
                raise BeelzebubIntegrationError(f"Refusing to use a symbolic-link build path: {path}")
        sources = sorted((self.application_root / "src" / "main" / "java").rglob("*.java"))
        resources = self.application_root / "src" / "main" / "resources"
        if resources.is_symlink():
            raise BeelzebubIntegrationError("The resource directory must not be a symbolic link.")
        newest = max((path.stat().st_mtime_ns for path in sources), default=0)
        if (self.application_root / "build.sh").is_file():
            newest = max(newest, (self.application_root / "build.sh").stat().st_mtime_ns)
        if resources.is_dir():
            newest = max(newest, max((path.stat().st_mtime_ns for path in resources.rglob("*") if path.is_file()), default=0))
        if self.jar_path.is_file() and self.jar_path.stat().st_mtime_ns >= newest:
            return
        self.build_directory.mkdir(parents=True, exist_ok=True)
        if self.classes_directory.exists():
            shutil.rmtree(self.classes_directory)
        self.classes_directory.mkdir(parents=True)
        command = [state["javac"], "--release", "17", "-encoding", "UTF-8",
                   "-d", str(self.classes_directory), *map(str, sources)]
        try:
            completed = subprocess.run(command, cwd=self.application_root, capture_output=True,
                                       text=True, timeout=120, check=False, shell=False)
        except subprocess.TimeoutExpired as error:
            raise BeelzebubIntegrationError("Компиляция Beelzebub AV превысила лимит времени.") from error
        if completed.returncode != 0:
            raise BeelzebubIntegrationError("Не удалось собрать Beelzebub AV:\n" + completed.stderr[-6000:])
        if resources.is_dir():
            shutil.copytree(resources, self.classes_directory, dirs_exist_ok=True)
        jar_command = [state["jar"], "--create", "--file", str(self.jar_path),
                       "--main-class", "ai.duckos.beelzebub.Main", "-C", str(self.classes_directory), "."]
        completed = subprocess.run(jar_command, cwd=self.application_root, capture_output=True,
                                    text=True, timeout=60, check=False, shell=False)
        if completed.returncode != 0 or not self.jar_path.is_file():
            raise BeelzebubIntegrationError("Не удалось упаковать Beelzebub AV:\n" + completed.stderr[-6000:])

    def open_gui(self) -> subprocess.Popen[str]:
        self._ensure_built()
        java = shutil.which("java")
        if not java:
            raise BeelzebubIntegrationError("Java runtime не найден.")
        try:
            return subprocess.Popen([java, "-jar", str(self.jar_path)], cwd=self.application_root,
                                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, shell=False, close_fds=True)
        except OSError as error:
            raise BeelzebubIntegrationError(f"Не удалось запустить Beelzebub AV: {error}") from error

    def scan(self, target: Path, timeout: int = 3600) -> dict[str, Any]:
        if timeout < 1 or timeout > 24 * 60 * 60:
            raise ValueError("Scan timeout must be between 1 and 86400 seconds.")
        selected = target.expanduser()
        if selected.is_symlink() or not selected.exists() or not selected.is_dir():
            raise BeelzebubIntegrationError("Для сканирования нужна существующая папка, не символическая ссылка.")
        self._ensure_built()
        java = shutil.which("java")
        if not java:
            raise BeelzebubIntegrationError("Java runtime не найден.")
        try:
            completed = subprocess.run([java, "-jar", str(self.jar_path), "--scan", str(selected.resolve())],
                                        cwd=self.application_root, capture_output=True, text=True,
                                        timeout=timeout, check=False, shell=False)
        except subprocess.TimeoutExpired as error:
            raise BeelzebubIntegrationError("Сканирование остановлено по тайм-ауту.") from error
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as error:
            raise BeelzebubIntegrationError("Java-сканер вернул некорректный JSON: " + completed.stderr[-3000:]) from error
        result["process_exit_code"] = completed.returncode
        result["engine"] = "Beelzebub AV / Java 17"
        return result
