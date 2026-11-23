"""Load and validate the versioned DuckOS system-app catalogue."""
from __future__ import annotations

import json
import re
from importlib.resources import files
from pathlib import Path
from typing import Any

SCHEMA = "duckos.system-applications.v1"
APP_ID = re.compile(r"^[a-z][a-z0-9-]{1,63}$")


class CatalogError(ValueError):
    """Raised when the system application catalogue is invalid."""


def load_system_catalog(path: str | Path | None = None) -> dict[str, Any]:
    try:
        if path is None:
            resource = files(__package__).joinpath("system-applications.v1.json")
            raw = resource.read_text(encoding="utf-8")
        else:
            target = Path(path).expanduser()
            if target.is_symlink() or not target.is_file() or target.stat().st_size > 1024 * 1024:
                raise CatalogError("catalogue path must be a regular file no larger than 1 MiB")
            raw = target.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except CatalogError:
        raise
    except (OSError, json.JSONDecodeError) as error:
        raise CatalogError(f"cannot load system application catalogue: {error}") from error

    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise CatalogError(f"catalogue must use {SCHEMA}")
    applications = payload.get("applications")
    if not isinstance(applications, list) or len(applications) != 15:
        raise CatalogError("system application catalogue must contain exactly 15 applications")

    seen: set[str] = set()
    for app in applications:
        if not isinstance(app, dict):
            raise CatalogError("each application must be an object")
        app_id = app.get("id")
        if not isinstance(app_id, str) or not APP_ID.fullmatch(app_id):
            raise CatalogError("application IDs must be lowercase stable identifiers")
        if app_id in seen:
            raise CatalogError(f"duplicate application ID: {app_id}")
        seen.add(app_id)
        for field in ("name", "category", "role"):
            if not isinstance(app.get(field), str) or not app[field].strip():
                raise CatalogError(f"{app_id}: {field} must be non-empty text")
        for field in ("capabilities", "system_apis", "permissions"):
            values = app.get(field)
            if not isinstance(values, list) or not values or any(
                not isinstance(value, str) or not value.strip() for value in values
            ):
                raise CatalogError(f"{app_id}: {field} must be a non-empty string list")
        if app.get("maturity_status") not in {"specified", "partial", "implemented", "verified"}:
            raise CatalogError(f"{app_id}: invalid maturity_status")

    return payload


def system_app_ids(path: str | Path | None = None) -> tuple[str, ...]:
    catalog = load_system_catalog(path)
    return tuple(app["id"] for app in catalog["applications"])
