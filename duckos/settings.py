"""User-scoped Duck settings, profile validation and reversible configuration history.

This module stores desired settings. It deliberately does not alter host networking,
firmware, device power limits, drivers, display hardware or kernel policy.
"""
from __future__ import annotations

import copy
import ipaddress
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA = "duckos.settings.v1"
MAX_CONFIG_BYTES = 1024 * 1024
MAX_EVENTS = 500
MAX_SNAPSHOTS = 20
PROFILE_NAME = re.compile(r"^[\w .-]{1,40}$", re.UNICODE)
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def default_profile() -> dict[str, Any]:
    return {
        "network": {
            "ipv4_enabled": True,
            "ipv4_method": "dhcp",
            "ipv4_address": "",
            "ipv4_prefix": 24,
            "ipv4_netmask": "255.255.255.0",
            "ipv4_gateway": "",
            "ipv6_enabled": True,
            "ipv6_method": "auto",
            "ipv6_address": "",
            "ipv6_prefix": 64,
            "ipv6_gateway": "",
            "dns_primary": "",
            "dns_secondary": "",
            "doh_url": "",
            "dot_server": "",
            "mtu": 1500,
            "proxy_enabled": False,
            "proxy_url": "",
        },
        "power": {
            "mode": "balanced",
            "eco_threshold": 20,
            "eco_only_on_battery": True,
            "charge_limit": 80,
            "screen_timeout_ac": 10,
            "screen_timeout_battery": 5,
            "sleep_timeout_ac": 30,
            "sleep_timeout_battery": 15,
        },
        "appearance": {
            "theme": "system",
            "accent": "#FFD400",
            "ui_scale": 1.0,
            "icon_scale": 1.0,
            "density": "comfortable",
            "reduced_motion": False,
        },
        "security": {
            "auto_lock_minutes": 5,
            "lock_on_sleep": True,
        },
        "locale": "ru",
    }


def default_settings() -> dict[str, Any]:
    base = default_profile()
    return {
        "schema": SCHEMA,
        "version": 1,
        "active_profile": "Дом",
        "profiles": {
            "Дом": copy.deepcopy(base),
            "Работа": copy.deepcopy(base),
            "Игра": copy.deepcopy(base),
            "Дорога": copy.deepcopy(base),
        },
        "updated_at": int(time.time()),
    }


def settings_directory() -> Path:
    if os.environ.get("XDG_CONFIG_HOME"):
        return Path(os.environ["XDG_CONFIG_HOME"]).expanduser() / "duckos"
    if os.environ.get("LOCALAPPDATA") and os.name == "nt":
        return Path(os.environ["LOCALAPPDATA"]) / "DuckOS"
    return Path.home() / ".config" / "duckos"


def _is_plain_directory(path: Path) -> bool:
    return not path.is_symlink() and (not path.exists() or path.is_dir())


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    if path.is_symlink():
        raise ValueError(f"Refusing to replace symbolic link: {path.name}")
    if not _is_plain_directory(path.parent):
        raise ValueError("Settings directory must be a regular directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".duckos-", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _read_json(path: Path, limit: int = MAX_CONFIG_BYTES) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Not a regular settings file: {path.name}")
    if path.stat().st_size > limit:
        raise ValueError("Settings file exceeds the 1 MiB limit")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Cannot read settings JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ValueError("Settings root must be a JSON object")
    return payload


def _merge_dict(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key].update(copy.deepcopy(value))
        else:
            result[key] = copy.deepcopy(value)
    return result


def validate_profile(profile: Any) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if not isinstance(profile, dict):
        return [{"field": "profile", "message": "Профиль должен быть объектом"}]

    defaults = default_profile()
    for section in defaults:
        if not isinstance(profile.get(section), dict):
            errors.append({"field": section, "message": "Раздел отсутствует или имеет неверный тип"})
    if errors:
        return errors

    network = profile["network"]
    power = profile["power"]
    appearance = profile["appearance"]
    security = profile["security"]

    def fail(field: str, message: str) -> None:
        errors.append({"field": field, "message": message})

    for field in ("ipv4_enabled", "ipv6_enabled", "proxy_enabled"):
        if not isinstance(network.get(field), bool):
            fail(f"network.{field}", "Ожидается логическое значение")

    if network.get("ipv4_method") not in {"dhcp", "static"}:
        fail("network.ipv4_method", "Выберите DHCP или Static")
    if network.get("ipv6_method") not in {"auto", "static"}:
        fail("network.ipv6_method", "Выберите автоматическую или ручную настройку IPv6")

    if network.get("ipv4_method") == "static" and network.get("ipv4_enabled") is True:
        address = network.get("ipv4_address", "")
        prefix = network.get("ipv4_prefix")
        try:
            interface = ipaddress.IPv4Interface(f"{address}/{prefix}")
            if interface.ip.is_unspecified or interface.ip.is_multicast:
                fail("network.ipv4_address", "Используйте обычный unicast IPv4-адрес")
        except (ValueError, TypeError):
            fail("network.ipv4_address", "Введите корректный IPv4-адрес и префикс от 0 до 32")

        mask = network.get("ipv4_netmask", "")
        if mask:
            try:
                mask_prefix = ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
                if isinstance(prefix, bool) or mask_prefix != int(prefix):
                    fail("network.ipv4_netmask", "Маска не соответствует длине префикса")
            except (ValueError, TypeError):
                fail("network.ipv4_netmask", "Введите корректную маску IPv4")

        gateway = network.get("ipv4_gateway", "")
        if gateway:
            try:
                gateway_ip = ipaddress.IPv4Address(gateway)
                if "interface" in locals() and gateway_ip not in interface.network:
                    fail("network.ipv4_gateway", "Шлюз находится вне указанной подсети")
            except ValueError:
                fail("network.ipv4_gateway", "Введите корректный IPv4-адрес шлюза")

    if network.get("ipv6_method") == "static" and network.get("ipv6_enabled") is True:
        try:
            address = network.get("ipv6_address", "")
            prefix = network.get("ipv6_prefix")
            interface6 = ipaddress.IPv6Interface(f"{address}/{prefix}")
            if interface6.ip.is_unspecified or interface6.ip.is_multicast:
                fail("network.ipv6_address", "Используйте обычный unicast IPv6-адрес")
        except (ValueError, TypeError):
            fail("network.ipv6_address", "Введите корректный IPv6-адрес и префикс от 0 до 128")
        gateway6 = network.get("ipv6_gateway", "")
        if gateway6:
            try:
                ipaddress.IPv6Address(gateway6)
            except ValueError:
                fail("network.ipv6_gateway", "Введите корректный IPv6-адрес шлюза")

    for field in ("dns_primary", "dns_secondary"):
        value = network.get(field, "")
        if value:
            if not isinstance(value, str):
                fail(f"network.{field}", "DNS должен быть строкой с IPv4- или IPv6-адресом")
            else:
                try:
                    ipaddress.ip_address(value)
                except ValueError:
                    fail(f"network.{field}", "DNS должен быть IPv4- или IPv6-адресом")

    doh = network.get("doh_url", "")
    if doh:
        if not isinstance(doh, str):
            fail("network.doh_url", "DoH должен быть HTTPS URL")
        else:
            try:
                parsed = urlparse(doh)
                valid_doh = parsed.scheme == "https" and bool(parsed.hostname)
            except ValueError:
                valid_doh = False
            if not valid_doh:
                fail("network.doh_url", "DoH должен использовать HTTPS и содержать имя узла")

    dot = network.get("dot_server", "")
    if dot and (not isinstance(dot, str) or any(char.isspace() for char in dot) or len(dot) > 253):
        fail("network.dot_server", "Укажите имя узла DNS-over-TLS без пробелов")

    mtu = network.get("mtu")
    if isinstance(mtu, bool) or not isinstance(mtu, int) or not 576 <= mtu <= 9000:
        fail("network.mtu", "MTU должен находиться в диапазоне 576–9000")

    if not isinstance(network.get("proxy_url"), str):
        fail("network.proxy_url", "Адрес прокси должен быть строкой")
    elif network.get("proxy_url"):
        try:
            parsed = urlparse(network["proxy_url"])
            valid_proxy = parsed.scheme in {"http", "https", "socks5"} and bool(parsed.hostname)
        except ValueError:
            valid_proxy = False
        if not valid_proxy:
            fail("network.proxy_url", "Поддерживаются адреса http(s):// или socks5://")

    if power.get("mode") not in {"eco", "quiet", "balanced", "performance", "maximum"}:
        fail("power.mode", "Неизвестный профиль питания")
    for field, low, high in (
        ("eco_threshold", 5, 50),
        ("charge_limit", 50, 100),
        ("screen_timeout_ac", 0, 240),
        ("screen_timeout_battery", 0, 240),
        ("sleep_timeout_ac", 0, 1440),
        ("sleep_timeout_battery", 0, 1440),
    ):
        value = power.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            fail(f"power.{field}", f"Допустимое значение: {low}–{high}")
    if not isinstance(power.get("eco_only_on_battery"), bool):
        fail("power.eco_only_on_battery", "Ожидается логическое значение")

    if appearance.get("theme") not in {"system", "light", "dark"}:
        fail("appearance.theme", "Выберите системную, светлую или тёмную тему")
    if not isinstance(appearance.get("accent"), str) or not HEX_COLOR.fullmatch(appearance.get("accent", "")):
        fail("appearance.accent", "Акцент должен быть в формате #RRGGBB")
    for field in ("ui_scale", "icon_scale"):
        value = appearance.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.75 <= value <= 2.0:
            fail(f"appearance.{field}", "Масштаб должен быть от 0.75 до 2.0")
    if appearance.get("density") not in {"compact", "comfortable"}:
        fail("appearance.density", "Выберите компактную или обычную плотность")
    if not isinstance(appearance.get("reduced_motion"), bool):
        fail("appearance.reduced_motion", "Ожидается логическое значение")

    lock_minutes = security.get("auto_lock_minutes")
    if isinstance(lock_minutes, bool) or not isinstance(lock_minutes, int) or not 0 <= lock_minutes <= 120:
        fail("security.auto_lock_minutes", "Автоблокировка: от 0 до 120 минут")
    if not isinstance(security.get("lock_on_sleep"), bool):
        fail("security.lock_on_sleep", "Ожидается логическое значение")
    locale = profile.get("locale")
    if not isinstance(locale, str) or not 2 <= len(locale) <= 16:
        fail("locale", "Укажите короткий код языка, например ru, uk или en")
    return errors


def validate_settings(payload: Any) -> list[dict[str, str]]:
    if not isinstance(payload, dict):
        return [{"field": "root", "message": "Настройки должны быть JSON-объектом"}]
    if payload.get("schema") != SCHEMA:
        return [{"field": "schema", "message": f"Ожидается схема {SCHEMA}"}]
    if payload.get("version") != 1:
        return [{"field": "version", "message": "Неподдерживаемая версия настроек"}]
    profiles = payload.get("profiles")
    if not isinstance(profiles, dict) or not 1 <= len(profiles) <= 32:
        return [{"field": "profiles", "message": "Нужно от 1 до 32 профилей"}]
    active = payload.get("active_profile")
    if active not in profiles:
        return [{"field": "active_profile", "message": "Активный профиль отсутствует"}]

    errors: list[dict[str, str]] = []
    for name, profile in profiles.items():
        if not isinstance(name, str) or not PROFILE_NAME.fullmatch(name):
            errors.append({"field": "profiles", "message": f"Недопустимое имя профиля: {name!r}"})
            continue
        errors.extend(
            {"field": f"profiles.{name}.{item['field']}", "message": item["message"]}
            for item in validate_profile(profile)
        )
    return errors


class SettingsStore:
    """Atomic, user-scoped configuration with snapshots and a bounded audit journal."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else settings_directory() / "settings.json"
        self.snapshots_dir = self.path.parent / "snapshots"
        self.events_path = self.path.parent / "settings-events.json"
        if self.path.is_symlink():
            raise ValueError("Settings file cannot be a symbolic link")
        if not _is_plain_directory(self.path.parent):
            raise ValueError("Settings path must be inside a regular directory")

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return default_settings()
        payload = _read_json(self.path)
        if payload.get("version") == 1 and payload.get("schema") == SCHEMA:
            errors = validate_settings(payload)
            if errors:
                raise ValueError("Stored settings are invalid: " + "; ".join(
                    f"{item['field']}: {item['message']}" for item in errors[:8]
                ))
            return payload
        raise ValueError("Unsupported settings schema or version; original file was preserved")

    def active_profile(self) -> tuple[str, dict[str, Any]]:
        payload = self.load()
        name = payload["active_profile"]
        return name, copy.deepcopy(payload["profiles"][name])

    def list_profiles(self) -> list[str]:
        return sorted(self.load()["profiles"], key=str.casefold)

    def _write_snapshot(self, current: dict[str, Any]) -> str | None:
        if not self.path.exists():
            return None
        if not _is_plain_directory(self.snapshots_dir):
            raise ValueError("Snapshot directory must be a regular directory")
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        name = f"settings-{time.time_ns()}.json"
        _atomic_json(self.snapshots_dir / name, current)
        files = sorted(
            (item for item in self.snapshots_dir.glob("settings-*.json")
             if item.is_file() and not item.is_symlink()),
            key=lambda item: item.stat().st_mtime_ns,
            reverse=True,
        )
        for old in files[MAX_SNAPSHOTS:]:
            old.unlink(missing_ok=True)
        return name

    def _append_event(self, action: str, details: dict[str, Any]) -> None:
        if self.events_path.is_symlink():
            raise ValueError("Settings journal cannot be a symbolic link")
        events: list[dict[str, Any]] = []
        if self.events_path.exists():
            data = _read_json(self.events_path)
            rows = data.get("events", [])
            if isinstance(rows, list):
                events = [row for row in rows if isinstance(row, dict)][-MAX_EVENTS:]
        events.append({
            "time_unix": int(time.time()),
            "action": action,
            "details": details,
            "system_changes_performed": False,
        })
        _atomic_json(self.events_path, {"schema": "duckos.settings-events.v1", "events": events[-MAX_EVENTS:]})

    def _commit(self, new_state: dict[str, Any], action: str, details: dict[str, Any]) -> dict[str, Any]:
        errors = validate_settings(new_state)
        if errors:
            raise ValueError("; ".join(f"{item['field']}: {item['message']}" for item in errors[:12]))
        current = self.load()
        snapshot = self._write_snapshot(current)
        new_state = copy.deepcopy(new_state)
        new_state["updated_at"] = int(time.time())
        _atomic_json(self.path, new_state)
        self._append_event(action, {**details, "snapshot": snapshot})
        return {
            "schema": SCHEMA,
            "active_profile": new_state["active_profile"],
            "profiles": len(new_state["profiles"]),
            "snapshot": snapshot,
            "system_changes_performed": False,
        }

    def update_profile(self, name: str, section: str, values: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(name, str) or name not in self.load()["profiles"]:
            raise ValueError("Unknown profile")
        if section not in {"network", "power", "appearance", "security"}:
            raise ValueError("Unknown settings section")
        if not isinstance(values, dict):
            raise ValueError("Section values must be an object")
        state = self.load()
        state["profiles"][name][section] = _merge_dict(state["profiles"][name][section], values)
        return self._commit(state, "profile.update", {"profile": name, "section": section})

    def create_profile(self, name: str, clone_from: str | None = None) -> dict[str, Any]:
        if not isinstance(name, str) or not PROFILE_NAME.fullmatch(name):
            raise ValueError("Profile name must contain 1–40 letters, digits, spaces, dots or hyphens")
        state = self.load()
        if name in state["profiles"] or len(state["profiles"]) >= 32:
            raise ValueError("Profile already exists or the 32-profile limit was reached")
        source = clone_from or state["active_profile"]
        if source not in state["profiles"]:
            raise ValueError("Source profile does not exist")
        state["profiles"][name] = copy.deepcopy(state["profiles"][source])
        return self._commit(state, "profile.create", {"profile": name, "cloned_from": source})

    def activate_profile(self, name: str) -> dict[str, Any]:
        state = self.load()
        if name not in state["profiles"]:
            raise ValueError("Unknown profile")
        state["active_profile"] = name
        return self._commit(state, "profile.activate", {"profile": name})

    def save(self) -> dict[str, Any]:
        """Create the initial settings file without touching an existing one."""
        if self.path.exists():
            return {"schema": SCHEMA, "created": False, "path": str(self.path)}
        state = default_settings()
        errors = validate_settings(state)
        if errors:
            raise ValueError("Internal defaults failed validation")
        _atomic_json(self.path, state)
        self._append_event("settings.initialize", {"schema": SCHEMA})
        return {"schema": SCHEMA, "created": True, "path": str(self.path)}

    def export_to(self, destination: str | Path) -> dict[str, Any]:
        target = Path(destination)
        if target.is_symlink():
            raise ValueError("Export destination cannot be a symbolic link")
        state = self.load()
        _atomic_json(target, state)
        return {"schema": SCHEMA, "exported": True, "path": str(target), "system_changes_performed": False}

    def import_from(self, source: str | Path) -> dict[str, Any]:
        candidate = _read_json(Path(source))
        errors = validate_settings(candidate)
        if errors:
            raise ValueError("Import rejected: " + "; ".join(
                f"{item['field']}: {item['message']}" for item in errors[:12]
            ))
        return self._commit(candidate, "settings.import", {"source_name": Path(source).name})

    def snapshots(self) -> list[dict[str, Any]]:
        if not self.snapshots_dir.exists():
            return []
        if self.snapshots_dir.is_symlink() or not self.snapshots_dir.is_dir():
            raise ValueError("Snapshot path must be a regular directory")
        rows = []
        for path in sorted(self.snapshots_dir.glob("settings-*.json"), reverse=True):
            if path.is_symlink() or not path.is_file():
                continue
            rows.append({"id": path.name, "modified": int(path.stat().st_mtime), "size_bytes": path.stat().st_size})
        return rows[:MAX_SNAPSHOTS]

    def rollback(self, snapshot_id: str) -> dict[str, Any]:
        if not isinstance(snapshot_id, str) or Path(snapshot_id).name != snapshot_id or not snapshot_id.startswith("settings-") or not snapshot_id.endswith(".json"):
            raise ValueError("Invalid snapshot identifier")
        snapshot_path = self.snapshots_dir / snapshot_id
        candidate = _read_json(snapshot_path)
        errors = validate_settings(candidate)
        if errors:
            raise ValueError("Snapshot is invalid; current settings were not changed")
        return self._commit(candidate, "settings.rollback", {"snapshot": snapshot_id})

    def events(self, limit: int = 100) -> list[dict[str, Any]]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_EVENTS:
            raise ValueError(f"limit must be between 1 and {MAX_EVENTS}")
        if not self.events_path.exists():
            return []
        data = _read_json(self.events_path)
        rows = data.get("events", [])
        if not isinstance(rows, list):
            return []
        return [row for row in rows if isinstance(row, dict)][-limit:]


def settings_search(query: str) -> list[dict[str, str]]:
    """Search visible setting names, aliases and full breadcrumb paths."""
    items = [
        ("Сеть", "Сеть → Интерфейсы → IPv4 / DHCP", "IPv4 DHCP Static адрес маска CIDR gateway шлюз", "network"),
        ("DNS", "Сеть → DNS → Основной и резервный серверы", "DNS DoH DoT resolver домен", "network"),
        ("MTU", "Сеть → Интерфейсы → Дополнительно", "MTU размер пакета маршрут", "network"),
        ("Прокси", "Сеть → Прокси и VPN", "proxy tunnel socks5 VPN туннель", "network"),
        ("Экономия энергии", "Питание → Профили", "battery power eco экономия тихий сбалансированный", "power"),
        ("Порог батареи", "Питание → Автоматизация", "battery threshold percent заряд", "power"),
        ("Лимит заряда", "Питание → Аккумулятор", "charge cap 80 health здоровье", "power"),
        ("Тема", "Внешний вид → Цвета", "dark light system theme тёмная светлая", "appearance"),
        ("Акцентный цвет", "Внешний вид → Палитра", "accent hex цвет палитра", "appearance"),
        ("Масштаб интерфейса", "Внешний вид → Размеры", "DPI scale масштаб иконки density", "appearance"),
        ("Профили", "Профили → Окружения", "home office game travel дом работа игра дорога", "profiles"),
        ("Автоблокировка", "Безопасность → Сеанс", "lock timeout блокировка пароль", "security"),
        ("Снимки настроек", "Диагностика → Восстановление", "snapshot backup rollback откат", "history"),
        ("Журнал изменений", "Диагностика → События", "audit log журнал", "history"),
    ]
    needle = query.casefold().strip()
    if not needle:
        return [{"title": item[0], "path": item[1], "section": item[3]} for item in items]
    return [
        {"title": title, "path": path, "section": section}
        for title, path, aliases, section in items
        if needle in title.casefold() or needle in path.casefold()
        or needle in aliases.casefold()
    ]


def network_probe(host: str, port: int = 443, timeout: float = 3.0) -> dict[str, Any]:
    """Resolve a host and optionally open a TCP connection; no configuration is changed."""
    import socket

    if not isinstance(host, str) or not host.strip() or len(host) > 253 or any(char.isspace() for char in host):
        raise ValueError("Enter a valid host name or IP address")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0.2 <= timeout <= 10:
        raise ValueError("Timeout must be between 0.2 and 10 seconds")
    started = time.monotonic()
    try:
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as error:
        return {"ok": False, "stage": "dns", "host": host, "error": str(error), "system_changes_performed": False}
    dns_ms = (time.monotonic() - started) * 1000
    target = addresses[0]
    connected = time.monotonic()
    sock = socket.socket(target[0], target[1], target[2])
    sock.settimeout(float(timeout))
    try:
        sock.connect(target[4])
        connect_ms = (time.monotonic() - connected) * 1000
        return {
            "ok": True, "stage": "tcp", "host": host, "port": port,
            "resolved_addresses": sorted({row[4][0] for row in addresses}),
            "dns_ms": round(dns_ms, 2), "connect_ms": round(connect_ms, 2),
            "system_changes_performed": False,
        }
    except OSError as error:
        return {
            "ok": False, "stage": "tcp", "host": host, "port": port,
            "resolved_addresses": sorted({row[4][0] for row in addresses}),
            "dns_ms": round(dns_ms, 2), "error": str(error),
            "system_changes_performed": False,
        }
    finally:
        sock.close()
