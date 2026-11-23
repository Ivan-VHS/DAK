"""Native Mora desktop preferences and small local-only workflows."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PREFERENCES_SCHEMA = "duckos.mora.preferences.v1"
RECOVERY_SCHEMA = "duckos.mora.recovery.v1"
MAX_INTENT_LENGTH = 320
MAX_HASH_FILE_BYTES = 512 * 1024 * 1024

CAPABILITIES = ("microphone", "camera", "location", "files", "network", "clipboard")
POWER_PROFILES = ("saver", "balanced", "performance")

APP_ALIASES = {
    "cockos": ("cockos",),
    "kavun": ("kavun",),
    "kabon": ("kabon", "кабон"),
    "gloverty": ("gloverty",),
    "po": ("po",),
    "illidia": ("illidia",),
    "unify": ("unify",),
    "mora-ai": ("mora ai", "помощник", "агент"),
    "security": ("sentinel", "безопасность"),
    "updates": ("restore", "восстановление", "обновление"),
    "runtime": ("bridge", "совместимость", "runtime"),
    "workspace": ("control", "настройки", "системные"),
    "provenance": ("proof", "подлинность", "проверка файла"),
    "mora-boost": ("mora boost", "игровая лаборатория", "game boost"),
    "desktop": ("duck desktop", "рабочий стол"),
    "mora-commons": ("mora commons", "каталог приложений"),
}


def config_directory() -> Path:
    """Return the per-user configuration directory without requiring extra packages."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "DuckOS" / "Mora"
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "duckos" / "mora"


def default_preferences() -> dict[str, Any]:
    return {
        "version": 1,
        "appearance": {
            "reducedMotion": False,
            "density": "comfortable",
            "theme": "duck",
        },
        "focusMode": False,
        "powerProfile": "balanced",
        "permissions": {name: False for name in CAPABILITIES},
    }


def normalize_preferences(value: Any) -> dict[str, Any]:
    defaults = default_preferences()
    source = value if isinstance(value, dict) else {}
    appearance = source.get("appearance")
    appearance = appearance if isinstance(appearance, dict) else {}
    permissions = source.get("permissions")
    permissions = permissions if isinstance(permissions, dict) else {}

    return {
        "version": 1,
        "appearance": {
            "reducedMotion": appearance.get("reducedMotion") is True,
            "density": "compact" if appearance.get("density") == "compact" else "comfortable",
            "theme": "duck",
        },
        "focusMode": source.get("focusMode") is True,
        "powerProfile": (
            source.get("powerProfile")
            if source.get("powerProfile") in POWER_PROFILES
            else defaults["powerProfile"]
        ),
        "permissions": {name: permissions.get(name) is True for name in CAPABILITIES},
    }


def _atomic_write_json(path: Path, value: dict[str, Any]) -> bool:
    path = path.expanduser()
    parent = path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        if parent.is_symlink() or path.is_symlink():
            return False
        payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        handle_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", newline="\n", dir=parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False,
            ) as handle:
                handle_name = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(handle_name, path)
            return True
        finally:
            if handle_name:
                try:
                    Path(handle_name).unlink(missing_ok=True)
                except OSError:
                    pass
    except (OSError, TypeError, ValueError):
        return False


def load_preferences(path: str | Path | None = None) -> dict[str, Any]:
    target = Path(path).expanduser() if path is not None else config_directory() / "preferences.json"
    try:
        if target.is_symlink() or target.stat().st_size > 1024 * 1024:
            return default_preferences()
        return normalize_preferences(json.loads(target.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        return default_preferences()


def save_preferences(
    value: Any,
    path: str | Path | None = None,
) -> bool:
    target = Path(path).expanduser() if path is not None else config_directory() / "preferences.json"
    return _atomic_write_json(target, normalize_preferences(value))


def create_recovery_snapshot(
    preferences: Any,
    created_at: str | None = None,
) -> dict[str, Any]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema": RECOVERY_SCHEMA,
        "createdAt": timestamp,
        "preferences": normalize_preferences(preferences),
    }


def validate_recovery_snapshot(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict) or value.get("schema") != RECOVERY_SCHEMA:
        return None
    created_at = value.get("createdAt")
    if not isinstance(created_at, str) or len(created_at) > 64:
        return None
    try:
        datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if not isinstance(value.get("preferences"), dict):
        return None
    return {
        "schema": RECOVERY_SCHEMA,
        "createdAt": created_at,
        "preferences": normalize_preferences(value["preferences"]),
    }


def build_intent_plan(raw_input: Any) -> dict[str, Any]:
    """Create a preview for a tiny allowlist; never returns shell commands."""
    text = str(raw_input if raw_input is not None else "").strip()
    if not text:
        return {"ok": False, "message": "Введите действие."}
    if len(text) > MAX_INTENT_LENGTH:
        return {"ok": False, "message": f"Запрос длиннее {MAX_INTENT_LENGTH} символов."}

    normalized = text.casefold()
    actions: list[dict[str, Any]] = []

    if re.search(r"(включи|активируй|запусти).{0,24}(фокус|не беспокоить)|режим фокуса", normalized):
        actions.append({"type": "set", "setting": "focusMode", "value": True})
    if re.search(r"(выключи|отключи).{0,24}(фокус|не беспокоить)", normalized):
        actions.append({"type": "set", "setting": "focusMode", "value": False})
    if re.search(r"(эконом|сбереж).{0,24}(энерг|питан)|режим экономии", normalized):
        actions.append({"type": "set", "setting": "powerProfile", "value": "saver"})
    elif re.search(r"(максимальн|производительност).{0,24}(энерг|питан)|режим производительности", normalized):
        actions.append({"type": "set", "setting": "powerProfile", "value": "performance"})
    elif re.search(r"сбалансированн.{0,24}(профил|режим)|обычный режим", normalized):
        actions.append({"type": "set", "setting": "powerProfile", "value": "balanced"})
    if re.search(r"(уменьши|отключи|сократи).{0,24}(анимац|движен)|без анимац", normalized):
        actions.append({"type": "set", "setting": "reducedMotion", "value": True})

    for app_id, aliases in APP_ALIASES.items():
        if app_id == "po":
            matched = bool(re.search(r"(?<!\\w)po(?!\\w)", normalized))
        else:
            matched = any(alias in normalized for alias in aliases)
        if matched:
            actions.append({"type": "open-app", "appId": app_id})
            break

    if not actions:
        return {
            "ok": False,
            "message": "Это действие не входит в локальный список Mora. Команды и запуск программ недоступны.",
        }
    return {"ok": True, "message": "План подготовлен. Изменения не применены.", "actions": actions}


def filter_commons_apps(
    apps: list[dict[str, Any]],
    query: str = "",
    category: str = "all",
) -> list[dict[str, Any]]:
    normalized = str(query).strip().casefold()
    result = []
    for app in apps:
        if category != "all" and app.get("category") != category:
            continue
        if normalized:
            fields = [
                str(app.get("name", "")),
                str(app.get("subtitle", "")),
                str(app.get("description", "")),
                *[str(item) for item in app.get("capabilities", [])],
                *[str(item) for item in app.get("keywords", [])],
            ]
            if normalized not in " ".join(fields).casefold():
                continue
        result.append(app)
    return result


def calculate_sha256(path: str | Path) -> dict[str, Any]:
    """Hash a regular local file; never follow a symbolic link or execute it."""
    target = Path(path).expanduser()
    if target.is_symlink():
        raise ValueError("Символические ссылки для проверки не принимаются.")
    try:
        info = target.stat()
    except OSError as error:
        raise ValueError(f"Не удалось прочитать файл: {error}") from error
    if not target.is_file():
        raise ValueError("Выберите обычный файл.")
    if info.st_size > MAX_HASH_FILE_BYTES:
        raise ValueError("Файл превышает безопасный лимит 512 МиБ.")
    digest = hashlib.sha256()
    try:
        with target.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as error:
        raise ValueError(f"Не удалось прочитать файл: {error}") from error
    return {
        "path": str(target.resolve()),
        "size_bytes": info.st_size,
        "algorithm": "SHA-256",
        "digest": digest.hexdigest(),
        "executed": False,
    }
