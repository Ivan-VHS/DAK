#!/usr/bin/env python3
"""Validate the separate 15-app DuckOS system utility catalogue."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "sys-settings", "pkg-center", "web-browser", "mail-client", "contacts-dir",
    "file-manager", "quick-notes", "todo-tasks", "os-calendar", "clocks-timers",
    "os-calc", "text-doc-view", "media-gallery", "av-player", "term-sysmon",
}


def read_json(path: Path):
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def main() -> int:
    catalogue_path = ROOT / "catalogs/system-applications.v1.json"
    package_catalogue_path = ROOT / "duckos/desktop/system-applications.v1.json"
    schema_path = ROOT / "schemas/system-applications.v1.schema.json"
    catalogue = read_json(catalogue_path)
    schema = read_json(schema_path)
    bench_schema = read_json(ROOT / "schemas/bench-profile.v1.schema.json")
    packaged = read_json(package_catalogue_path)

    Draft202012Validator.check_schema(schema)
    Draft202012Validator.check_schema(bench_schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(catalogue)
    if catalogue != packaged:
        raise SystemExit("Packaged and repository system-app catalogues differ")

    ids = [app["id"] for app in catalogue["applications"]]
    if len(ids) != 15 or set(ids) != EXPECTED:
        raise SystemExit(f"Expected exactly 15 stable system app IDs, received: {ids}")
    if any(app["maturity_status"] != "specified" for app in catalogue["applications"]):
        raise SystemExit("Catalogue maturity must remain specified until native app packages ship")

    mora_apps = read_json(ROOT / "mora/apps.json")
    if not any(app.get("id") == "system-apps" for app in mora_apps.get("built_in_apps", [])):
        raise SystemExit("Mora does not expose the System Apps launcher entry")
    shell_source = (ROOT / "mora/app.js").read_text(encoding="utf-8")
    missing_ui = [app_id for app_id in ids if app_id not in shell_source]
    if missing_ui:
        raise SystemExit(f"Mora is missing utility identities: {missing_ui}")

    print(f"Validated {len(ids)} system utility apps, Mora entry points and both JSON Schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
