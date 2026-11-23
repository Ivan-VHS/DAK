#!/usr/bin/env python3
"""Local launcher and settings host for the Mora desktop workspace.

The listener is bound to loopback. It serves one fixed page and starts a
small, explicit allowlist of applications. Browser input never becomes a
shell command or an executable path.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
DEFAULT_PORT = 43860

APP_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "reaper",
        "repo": "Reaper",
        "fallback": {
            "name": "Reaper Studio",
            "summary": "Язык программирования и IDE",
            "description": "Редактор MOST/Reaper, проверка и запуск программ, отладчик, LSP и локальный toolchain.",
            "category": "developer",
            "capabilities": ["Редактор", "Check / Run", "Debugger", "LSP / DAP"],
            "accent": "#315EE8",
        },
    },
    {
        "id": "oplague",
        "repo": "OPlague",
        "fallback": {
            "name": "OPlague",
            "summary": "Проверка устройств и драйверов",
            "description": "Локальная read-only инвентаризация PnP, инспекция INF/ZIP и PE/COFF, сравнение идентификаторов и отчёты.",
            "category": "system",
            "capabilities": ["PnP inventory", "INF / ZIP", "PE / COFF", "Evidence reports"],
            "accent": "#C52A45",
        },
    },
    {
        "id": "ventusample",
        "repo": "VentuSample",
        "fallback": {
            "name": "VentuSample",
            "summary": "Процедурная аудиостанция",
            "description": "Генерация сэмпл-паков, офлайн-DSP, анализ WAV, пресеты A/B и экспорт локальных файлов.",
            "category": "audio",
            "capabilities": ["Sample generation", "Offline DSP", "WAV / MIDI tools", "Presets"],
            "accent": "#266FC7",
        },
    },
    {
        "id": "pytyliki",
        "repo": "Pytyliki",
        "fallback": {
            "name": "Pytyliki",
            "summary": "Рабочая станция процессорных систем",
            "description": "Инвентаризация CPU, ограниченные измерения, анализ исходников, профилей и системных отчётов.",
            "category": "compute",
            "capabilities": ["CPU inventory", "Local measurements", "Source review", "Reports"],
            "accent": "#386CAA",
        },
    },
)

_processes: dict[str, subprocess.Popen[bytes]] = {}
_process_lock = threading.Lock()


def config_path() -> Path:
    if os.name == "nt" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "Ivan-VHS" / "Mora" / "workspace.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Mora" / "workspace.json"
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "mora" / "workspace.json"


def load_config() -> dict[str, Any]:
    try:
        payload = json.loads(config_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    repositories = payload.get("repositories")
    if not isinstance(repositories, dict):
        repositories = {}
    theme = payload.get("theme")
    return {
        "version": 1,
        "theme": theme if theme in {"dark", "light"} else "dark",
        "repositories": repositories,
    }


def save_config(config: dict[str, Any]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def normalize_theme(value: Any) -> str:
    theme = str(value or "").strip().lower()
    if theme not in {"dark", "light"}:
        raise ValueError("Тема должна быть 'dark' или 'light'.")
    return theme


def resolve_repository(app_id: str, config: dict[str, Any]) -> Path | None:
    spec = next((item for item in APP_SPECS if item["id"] == app_id), None)
    if spec is None:
        return None

    configured = config["repositories"].get(app_id)
    candidates: list[Path] = []
    if isinstance(configured, str) and configured.strip():
        configured_path = Path(configured).expanduser()
        candidates.append(
            configured_path if configured_path.is_absolute()
            else ROOT / configured_path
        )
    candidates.extend((
        ROOT.parent / spec["repo"],
        ROOT / "workspace" / spec["repo"],
        Path.home() / "Projects" / spec["repo"],
        Path.home() / "projects" / spec["repo"],
    ))
    for candidate in candidates:
        if (candidate / "mora-app.json").is_file():
            return candidate.resolve()
    return None


def app_manifest(repo: Path | None, spec: dict[str, Any]) -> dict[str, Any]:
    manifest: dict[str, Any] = {}
    if repo is not None:
        try:
            value = json.loads((repo / "mora-app.json").read_text(encoding="utf-8"))
            if isinstance(value, dict) and value.get("id") == spec["id"]:
                manifest = value
        except (OSError, ValueError):
            pass
    result = dict(spec["fallback"])
    result.update({
        key: manifest[key]
        for key in ("name", "summary", "description", "category", "capabilities", "accent")
        if key in manifest
    })
    return result


def launch_target(app_id: str, repo: Path) -> list[str] | None:
    """Resolve only known project entry points; manifest text is never executable."""
    if app_id == "reaper":
        entry = repo / "reaper_desktop.py"
        return [sys.executable, str(entry)] if entry.is_file() else None
    if app_id == "oplague":
        entry = repo / "oplague_app.py"
        return [sys.executable, str(entry)] if entry.is_file() else None
    if app_id == "ventusample":
        candidates = (
            repo / "build" / "VentuSample.exe",
            repo / "build" / "Release" / "VentuSample.exe",
            repo / "build" / "VentuSample",
            repo / "build" / "Release" / "VentuSample",
            repo / "build" / "VentuSample.app" / "Contents" / "MacOS" / "VentuSample",
        )
        target = next((item for item in candidates if item.is_file()), None)
        return [str(target)] if target else None
    if app_id == "pytyliki":
        if os.name != "nt":
            return None
        candidates = (
            repo / "build" / "Release" / "pytyliki-gui.exe",
            repo / "build" / "pytyliki-gui.exe",
        )
        target = next((item for item in candidates if item.is_file()), None)
        return [str(target)] if target else None
    return None


def describe_apps() -> dict[str, Any]:
    config = load_config()
    rows = []
    with _process_lock:
        for spec in APP_SPECS:
            process = _processes.get(spec["id"])
            running = process is not None and process.poll() is None
            repo = resolve_repository(spec["id"], config)
            command = launch_target(spec["id"], repo) if repo else None
            info = app_manifest(repo, spec)
            status_message = ""
            if repo is None:
                status_message = (
                    "Репозиторий не найден. Разместите его рядом с DuckOS "
                    "или задайте путь в workspace.json."
                )
            elif spec["id"] == "pytyliki" and os.name != "nt":
                status_message = (
                    "Нативная GUI-сборка Pytyliki сейчас реализована только для Windows."
                )
            elif spec["id"] == "ventusample" and command is None:
                status_message = (
                    "Не найдена GUI-сборка. Соберите CMake target VentuSample "
                    "с установленным Qt 6 Widgets."
                )
            elif spec["id"] == "pytyliki" and command is None:
                status_message = (
                    "Не найдена сборка pytyliki-gui.exe. Соберите Windows target через CMake."
                )
            elif command is None:
                status_message = "Не найден заявленный entry point приложения."
            rows.append({
                "id": spec["id"],
                **info,
                "available": command is not None,
                "running": running,
                "status_message": status_message or (
                    "Приложение найдено и готово к запуску." if command else ""
                ),
                "repository": str(repo) if repo else None,
            })
    return {"apps": rows, "theme": config["theme"]}


def launch_app(app_id: str) -> dict[str, Any]:
    config = load_config()
    spec = next((item for item in APP_SPECS if item["id"] == app_id), None)
    if spec is None:
        raise KeyError("Неизвестное приложение Mora.")
    repo = resolve_repository(app_id, config)
    if repo is None:
        raise FileNotFoundError("Репозиторий " + spec["repo"] + " не найден.")
    command = launch_target(app_id, repo)
    if command is None:
        rows = describe_apps()["apps"]
        index = next(i for i, item in enumerate(APP_SPECS) if item["id"] == app_id)
        raise FileNotFoundError(rows[index]["status_message"])

    with _process_lock:
        current = _processes.get(app_id)
        if current is not None and current.poll() is None:
            return {
                "success": True,
                "already_running": True,
                "message": spec["repo"] + " уже запущен.",
            }
        environment = os.environ.copy()
        environment["MORA_DESKTOP"] = "1"
        environment["MORA_THEME_MODE"] = config["theme"]
        creationflags = 0
        if os.name == "nt":
            creationflags = (
                getattr(subprocess, "DETACHED_PROCESS", 0)
                | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            )
        process = subprocess.Popen(
            command,
            cwd=str(repo),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=(os.name != "nt"),
            creationflags=creationflags,
        )
        _processes[app_id] = process
    return {
        "success": True,
        "already_running": False,
        "message": spec["repo"] + " запускается отдельным окном.",
    }


class MoraHandler(BaseHTTPRequestHandler):
    server_version = "MoraLocal/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        print("[Mora] " + (format % args))

    def _send(
        self,
        status: int,
        payload: dict[str, Any] | bytes,
        content_type: str = "application/json; charset=utf-8",
    ) -> None:
        body = payload if isinstance(payload, bytes) else json.dumps(
            payload, ensure_ascii=False
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if content_type.startswith("text/html"):
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self' 'unsafe-inline'; "
                "script-src 'self' 'unsafe-inline'; img-src 'self' data:",
            )
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length < 0 or length > 8192:
            raise ValueError("Слишком большой запрос.")
        raw = self.rfile.read(length) if length else b"{}"
        payload = json.loads(raw.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Ожидался JSON-объект.")
        return payload

    def _origin_allowed(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        parsed = urlsplit(origin)
        return (
            parsed.scheme == "http"
            and parsed.netloc == self.headers.get("Host", "")
        )

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/api/health":
            self._send(200, {"ok": True, "service": "Mora Local Host"})
            return
        if path == "/api/apps":
            self._send(200, describe_apps())
            return
        if path in {"/", "/index.html"}:
            try:
                page = (ROOT / "index.html").read_bytes()
            except OSError:
                self._send(500, {"error": "Не найден index.html."})
                return
            self._send(200, page, "text/html; charset=utf-8")
            return
        self._send(404, {"error": "Страница не найдена."})

    def do_POST(self) -> None:
        if not self._origin_allowed():
            self._send(403, {"error": "Внешний источник запросов запрещён."})
            return
        path = urlsplit(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/theme":
                config = load_config()
                config["theme"] = normalize_theme(payload.get("theme"))
                save_config(config)
                self._send(200, {"success": True, "theme": config["theme"]})
                return
            if path.startswith("/api/launch/"):
                app_id = unquote(path.removeprefix("/api/launch/"))
                self._send(200, launch_app(app_id))
                return
            self._send(404, {"error": "Команда не найдена."})
        except KeyError as error:
            self._send(404, {"error": str(error)})
        except (ValueError, FileNotFoundError, OSError, subprocess.SubprocessError) as error:
            self._send(400, {"error": str(error)})


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Start the local Mora desktop workspace."
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT,
        help="loopback HTTP port (default: %(default)s)",
    )
    parser.add_argument(
        "--no-browser", action="store_true",
        help="do not open the desktop page automatically",
    )
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be between 1024 and 65535")
    server = ThreadingHTTPServer((HOST, args.port), MoraHandler)
    address = "http://" + HOST + ":" + str(args.port) + "/"
    print("Mora desktop: " + address)
    print("Press Ctrl+C to stop the local host.")
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMora desktop stopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
