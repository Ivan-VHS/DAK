"""Unify: the shared configuration, event and command layer for DuckOS."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from .cockos import PipeWireAudioBus
from .common import ServiceError, atomic_write_json, read_json
from .events import EventBus
from .gloverty import PALETTES, palette
from .illidia import SnapshotStore
from .kabon import InputRouter
from .kavun import compute_layout
from .po import CommandRegistry
from .news import NewsService


PROFILES = {
    "balanced": {"theme": "dark", "layout": "main-stack", "audio_policy": "manual"},
    "creator": {"theme": "dark", "layout": "main-stack", "audio_policy": "manual"},
    "focus": {
        "theme": "high-contrast",
        "layout": "columns",
        "audio_policy": "notifications-muted-by-policy",
    },
    "low-power": {"theme": "dark", "layout": "grid", "audio_policy": "manual"},
}

_DEFAULT_SETTINGS = {
    "profile": "balanced",
    "theme": "dark",
    "layout": "main-stack",
    "workspace": 1,
    "windows": [],
    "key_bindings": None,
    "audio_routing": {"mode": "manual"},
}


class DuckOSHub:
    """Coordinates service APIs without pretending to be a kernel supervisor."""

    def __init__(self, state_directory: Path | None = None) -> None:
        default_directory = Path.home() / ".local" / "state" / "duckos"
        self.state_directory = (state_directory or default_directory).expanduser()
        self.state_directory.mkdir(parents=True, exist_ok=True)

        self.events = EventBus()
        self.audio = PipeWireAudioBus()
        self.news = NewsService(self.state_directory)
        self.snapshots = SnapshotStore(self.state_directory / "snapshots")
        self.input = InputRouter()
        self.commands = CommandRegistry()
        self.settings = self._load_settings()
        self._register_commands()

    def _load_settings(self) -> dict[str, Any]:
        settings = read_json(self.state_directory / "settings.json", {})
        if not isinstance(settings, dict):
            raise ServiceError("DuckOS settings must be a JSON object")

        merged = dict(_DEFAULT_SETTINGS)
        merged.update({key: value for key, value in settings.items() if key in _DEFAULT_SETTINGS})
        if merged["theme"] not in PALETTES:
            merged["theme"] = "dark"
        if merged["profile"] not in PROFILES:
            merged["profile"] = "balanced"
        if merged["layout"] not in {"main-stack", "columns", "grid", "floating"}:
            merged["layout"] = "main-stack"
        if isinstance(merged["workspace"], bool) or not isinstance(merged["workspace"], int):
            merged["workspace"] = 1
        if merged["workspace"] < 1 or merged["workspace"] > 32:
            merged["workspace"] = 1
        if not isinstance(merged["windows"], list):
            merged["windows"] = []
        if not isinstance(merged["audio_routing"], dict):
            merged["audio_routing"] = {"mode": "manual"}

        saved_bindings = merged.get("key_bindings")
        if isinstance(saved_bindings, dict):
            try:
                self.input = InputRouter(saved_bindings)
            except ServiceError:
                self.input = InputRouter()
        merged["key_bindings"] = self.input.export()
        return merged

    def _save_settings(self) -> None:
        atomic_write_json(self.state_directory / "settings.json", self.settings)

    def _register_commands(self) -> None:
        self.commands.register(
            "system.status", "Состояние DuckOS",
            "Проверить доступность пользовательских системных служб",
            lambda _args: self.status(),
        )
        self.commands.register(
            "audio.ports", "Аудиопорты",
            "Показать входы и выходы графа PipeWire",
            lambda args: self.audio.list(args.get("direction", "outputs")),
        )
        self.commands.register(
            "news.status", "Состояние новостной ленты",
            "Показать кэш, источники и время последнего обновления",
            lambda _args: self.news.status(),
        )
        self.commands.register(
            "news.refresh", "Обновить новостную ленту",
            "Получить материалы из доверенных публичных RSS/Atom-источников",
            lambda _args: self.refresh_news(),
        )
        self.commands.register(
            "snapshot.create", "Сохранить сессию",
            "Создать контрольную точку настроек и окон",
            lambda args: self.create_snapshot(args.get("label", "Po checkpoint")),
        )
        self.commands.register(
            "snapshot.restore", "Восстановить сессию",
            "Вернуть настройки из проверенной контрольной точки",
            lambda args: self.restore_snapshot(args["id"]),
            destructive=True,
        )
        self.commands.register(
            "theme.set", "Сменить тему",
            "Применить семантическую палитру Gloverty",
            lambda args: self.set_theme(args["theme"]),
        )
        self.commands.register(
            "profile.set", "Переключить профиль",
            "Согласованно изменить профиль рабочего пространства",
            lambda args: self.switch_profile(args["profile"]),
        )
        self.commands.register(
            "layout.compute", "Рассчитать раскладку",
            "Получить геометрию окон Kavun для заданного экрана",
            lambda args: compute_layout(
                args["width"], args["height"], args["windows"],
                mode=args.get("mode", self.settings["layout"]),
                ratio=args.get("ratio", 0.62),
            ),
        )

    def status(self) -> dict[str, Any]:
        audio_installed = shutil.which(self.audio.executable) is not None
        return {
            "platform": os.name,
            "state_directory": str(self.state_directory),
            "active_profile": self.settings["profile"],
            "services": {
                "Cockos": {
                    "status": "dependency-present" if audio_installed else "dependency-missing",
                    "backend": "PipeWire pw-link",
                    "capability": "port discovery and link management",
                },
                "Kavun": {
                    "status": "user-space-ready",
                    "capability": "deterministic window geometry plans",
                    "compositor_binding": "pending",
                },
                "Ka-bon": {
                    "status": "user-space-ready",
                    "capability": "contextual shortcut routing",
                    "evdev_binding": "pending",
                },
                "Gloverty": {
                    "status": "user-space-ready",
                    "capability": "semantic palettes and contrast audit",
                },
                "Po": {
                    "status": "user-space-ready",
                    "capability": "registered commands with confirmation gates",
                },
                "Illidia": {
                    "status": "user-space-ready",
                    "capability": "checksummed session snapshots",
                },
                "Unify": {
                    "status": "user-space-ready",
                    "capability": "settings, event bus and service command registry",
                },
                "Newsroom": {
                    **self.news.status(),
                    "backend": "trusted HTTPS RSS/Atom feeds",
                    "api": "loopback JSON API; start with duckos news serve",
                },
            },
            "wayland_session": bool(os.environ.get("WAYLAND_DISPLAY")),
            "pipewire_cli": audio_installed,
        }

    def refresh_news(self) -> dict[str, Any]:
        result = self.news.refresh()
        self.events.publish("news.updated", "newsroom", result)
        return result

    def set_theme(self, theme: str) -> dict[str, Any]:
        colors = palette(theme)
        previous = self.settings["theme"]
        self.settings["theme"] = theme
        self._save_settings()
        self.events.publish("theme.changed", "gloverty", {
            "previous": previous, "theme": theme,
        })
        return {"theme": theme, "colors": colors}

    def switch_profile(self, profile: str) -> dict[str, Any]:
        if profile not in PROFILES:
            raise ServiceError(f"unknown profile: {profile}")
        previous = self.settings["profile"]
        selected = PROFILES[profile]
        self.settings.update({
            "profile": profile,
            "theme": selected["theme"],
            "layout": selected["layout"],
            "audio_routing": {"mode": selected["audio_policy"]},
        })
        self._save_settings()
        self.events.publish("profile.changed", "unify", {
            "previous": previous,
            "profile": profile,
            "settings": {
                "theme": self.settings["theme"],
                "layout": self.settings["layout"],
                "audio_routing": self.settings["audio_routing"],
            },
        })
        return {
            "profile": profile,
            "theme": self.settings["theme"],
            "layout": self.settings["layout"],
            "audio_routing": self.settings["audio_routing"],
        }

    def create_snapshot(self, label: str = "Session checkpoint") -> dict[str, Any]:
        state = {key: self.settings[key] for key in (
            "theme", "profile", "workspace", "layout", "windows",
            "key_bindings", "audio_routing",
        )}
        record = self.snapshots.save(state, label)
        self.events.publish("snapshot.created", "illidia", record)
        return record

    def restore_snapshot(self, identifier: str) -> dict[str, Any]:
        restored = self.snapshots.restore(identifier)
        previous_profile = self.settings["profile"]
        saved_bindings = restored.get("key_bindings")
        if isinstance(saved_bindings, dict):
            self.input = InputRouter(saved_bindings)
        self.settings.update(restored)
        self.settings["key_bindings"] = self.input.export()
        self._save_settings()
        self.events.publish("session.restored", "illidia", {
            "snapshot_id": identifier,
            "previous_profile": previous_profile,
            "profile": self.settings["profile"],
        })
        return dict(self.settings)

    def bind_shortcut(self, context: str, chord: str, action: str) -> None:
        self.input.bind(context, chord, action)
        self.settings["key_bindings"] = self.input.export()
        self._save_settings()
        self.events.publish("input.binding.changed", "kabon", {
            "context": context, "chord": chord, "action": action,
        })

    def dispatch_shortcut(self, chord: str, context: str = "global") -> str | None:
        action = self.input.dispatch(chord, context)
        if action is not None:
            self.events.publish("input.action", "kabon", {
                "chord": chord, "context": context, "action": action,
            })
        return action

    def run_command(
        self,
        identifier: str,
        arguments: dict[str, Any] | None = None,
        *,
        confirmed: bool = False,
    ) -> Any:
        result = self.commands.execute(identifier, arguments, confirmed=confirmed)
        self.events.publish("command.executed", "po", {
            "command": identifier,
            "confirmation_required": isinstance(result, dict)
            and result.get("status") == "confirmation-required",
        })
        return result
