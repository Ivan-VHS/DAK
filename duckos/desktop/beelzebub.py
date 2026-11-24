"""Process-isolated launcher for the Beelzebub AV Java application."""
from __future__ import annotations

import json
import os
import ipaddress
import time
import shutil
import site
import subprocess
import urllib.error
import urllib.request
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
        self.bridge_root = self.application_root / "bridge"
        self.bridge_binary = self.build_directory / ("bav-bridge.exe" if os.name == "nt" else "bav-bridge")

    def inspect(self) -> dict[str, Any]:
        java, javac, jar = shutil.which("java"), shutil.which("javac"), shutil.which("jar")
        source_root = self.application_root / "src" / "main" / "java"
        sources = sorted(source_root.rglob("*.java")) if source_root.is_dir() and not source_root.is_symlink() else []
        missing = [name for name, executable in (("java", java), ("javac", javac), ("jar", jar)) if not executable]
        if not sources:
            missing.append("Java sources")
        go = shutil.which("go")
        bridge_sources = sorted(self.bridge_root.rglob("*.go")) if self.bridge_root.is_dir() and not self.bridge_root.is_symlink() else []
        return {
            "schema": "duckos.beelzebub-status.v1",
            "available": not missing,
            "java": java,
            "javac": javac,
            "jar": jar,
            "go": go,
            "bridge_source_files": len(bridge_sources),
            "bridge_built": self.bridge_binary.is_file() and not self.bridge_binary.is_symlink(),
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

    def _ensure_bridge_built(self) -> None:
        go = shutil.which("go")
        if not go:
            raise BeelzebubIntegrationError("Для Go event bridge требуется Go 1.23+.")
        if self.bridge_root.is_symlink() or not (self.bridge_root / "go.mod").is_file():
            raise BeelzebubIntegrationError("Исходники BAV Go bridge не найдены.")
        sources = sorted(self.bridge_root.rglob("*.go"))
        if not sources:
            raise BeelzebubIntegrationError("В BAV Go bridge нет исходников.")
        for source in sources:
            if source.is_symlink():
                raise BeelzebubIntegrationError(f"Refusing symbolic link in bridge source tree: {source}")
        if self.bridge_binary.is_symlink() or self.build_directory.is_symlink():
            raise BeelzebubIntegrationError("Путь сборки BAV bridge не должен быть символической ссылкой.")
        newest = max([ (self.bridge_root / "go.mod").stat().st_mtime_ns ] +
                     [path.stat().st_mtime_ns for path in sources])
        if self.bridge_binary.is_file() and self.bridge_binary.stat().st_mtime_ns >= newest:
            return
        self.build_directory.mkdir(parents=True,exist_ok=True)
        command = [go,"build","-trimpath","-o",str(self.bridge_binary),"./cmd/bav-bridge"]
        env = dict(os.environ); env["GOTOOLCHAIN"]="local"
        try:
            result=subprocess.run(command,cwd=self.bridge_root,env=env,capture_output=True,
                                  text=True,timeout=240,check=False,shell=False)
        except subprocess.TimeoutExpired as error:
            raise BeelzebubIntegrationError("Сборка Go event bridge превысила лимит времени.") from error
        if result.returncode != 0 or not self.bridge_binary.is_file():
            raise BeelzebubIntegrationError("Не удалось собрать BAV Go bridge:\n"+result.stderr[-6000:])

    def start_ingest_bridge(self) -> dict[str, Any]:
        address = os.environ.get("BAV_EVENT_ADDR", "127.0.0.1:9777")
        host = address[1:address.index("]")] if address.startswith("[") and "]" in address else address.rsplit(":", 1)[0]
        try:
            loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            loopback = False
        if not loopback:
            raise BeelzebubIntegrationError("BAV_EVENT_ADDR must use a loopback IP address.")
        health_url = "http://" + address + "/healthz"

        def read_health() -> dict[str, Any] | None:
            try:
                request = urllib.request.Request(health_url, method="GET")
                with urllib.request.urlopen(request, timeout=0.25) as response:
                    status = json.loads(response.read(4096).decode("utf-8"))
                return status if response.status == 200 and status.get("schema") == "duckos.beelzebub-av-bridge-health.v1" else None
            except (OSError, ValueError, urllib.error.URLError):
                return None

        already_running = read_health()
        if already_running is not None:
            return {"schema": "duckos.beelzebub-bridge-launch.v1", "started": False,
                    "already_running": True, "health": already_running}
        self._ensure_bridge_built()

        data_dir = Path(os.environ["BAV_DATA_DIR"]).expanduser() if os.environ.get("BAV_DATA_DIR") else None
        if data_dir is None:
            if os.name == "nt":
                base = os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local")
                data_dir = Path(base) / "DuckOS" / "BeelzebubAV"
            else:
                base = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
                data_dir = Path(base) / "duckos" / "beelzebub-av"
        data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        if data_dir.is_symlink():
            raise BeelzebubIntegrationError("Каталог BAV данных не должен быть символической ссылкой.")
        if os.name != "nt":
            os.chmod(data_dir, 0o700)
        log_path = data_dir / "bridge.log"
        if log_path.is_symlink():
            raise BeelzebubIntegrationError("Файл BAV bridge log не должен быть символической ссылкой.")
        env = dict(os.environ)
        env["BAV_DATA_DIR"] = str(data_dir.resolve())
        env["BAV_EVENT_ADDR"] = address
        try:
            with log_path.open("a", encoding="utf-8") as output:
                if os.name != "nt":
                    os.chmod(log_path, 0o600)
                process = subprocess.Popen([str(self.bridge_binary), "serve"], cwd=self.bridge_root, env=env,
                                            stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                            shell=False, close_fds=True, start_new_session=(os.name != "nt"))
        except OSError as error:
            raise BeelzebubIntegrationError(f"Не удалось запустить BAV Go bridge: {error}") from error

        ready = None
        for _ in range(30):
            if process.poll() is not None:
                break
            ready = read_health()
            if ready is not None:
                break
            time.sleep(0.05)
        if ready is None:
            if process.poll() is None:
                process.terminate()
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-3000:] if log_path.is_file() else ""
            raise BeelzebubIntegrationError("BAV event bridge не подтвердил готовность. " + tail)

        return {"schema": "duckos.beelzebub-bridge-launch.v1", "started": True, "pid": process.pid,
                "endpoint": "http://" + address + "/v1/events", "health": ready,
                "data_directory": str(data_dir), "token_file": str(data_dir / "ingest.token"),
                "logs": str(log_path), "shell": False}

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
