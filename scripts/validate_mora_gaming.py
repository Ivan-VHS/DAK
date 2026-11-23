#!/usr/bin/env python3
"""Validate Mora's OPlague gaming capability contract using only the stdlib."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "mora" / "contracts" / "oplague-gaming.v1.schema.json"
MORA_JS = ROOT / "mora" / "app.js"
MORA_INDEX = ROOT / "mora" / "index.html"
APP_CATALOG = ROOT / "mora" / "apps.json"
WORKER_JS = ROOT / "mora" / "service-worker.js"
INTEGRATION_DOC = ROOT / "docs" / "GAMING_PERFORMANCE_INTEGRATION.md"

CAPABILITIES = {
    "hardware.read",
    "snapshot.create",
    "session.start",
    "session.restore",
    "benchmark.compare",
    "profile.read",
    "profile.write.validated",
}
SCOPES = {
    "hardware.read",
    "snapshot.create",
    "power-plan.temporary",
    "benchmark.read",
    "profile.read",
    "profile.write.validated",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    require(schema.get("$id") == "mora.oplague.gaming.v1", "Unexpected gaming IPC schema ID")
    require(schema.get("type") == "object", "Top-level schema must describe an object")
    require(len(schema.get("oneOf", [])) == 2, "Schema must support request and response envelopes")

    definitions = schema.get("$defs", {})
    request = definitions.get("request", {})
    response = definitions.get("response", {})
    require(request.get("additionalProperties") is False, "Requests must reject unknown fields")
    require(response.get("additionalProperties") is False, "Responses must reject unknown fields")

    request_props = request.get("properties", {})
    payload_props = request_props.get("payload", {}).get("properties", {})
    consent_props = request_props.get("consent", {}).get("properties", {})
    require(
        set(request_props.get("capability", {}).get("enum", [])) == CAPABILITIES,
        "Capability list differs from the approved contract",
    )
    require(
        set(consent_props.get("scope", {}).get("enum", [])) == SCOPES,
        "Consent scopes differ from the approved contract",
    )
    require(consent_props.get("granted", {}).get("const") is True, "User consent must be explicit")
    require(request_props.get("payload", {}).get("additionalProperties") is False, "Payload must reject unknown fields")
    require(
        {"request_id", "nonce", "issued_at", "expires_at", "capability", "consent", "payload"}
        <= set(request.get("required", [])),
        "Request envelope is missing required replay, expiry or consent fields",
    )
    require(
        not {"command", "shell", "executable_path", "registry_path", "driver_url", "raw_path"} & set(payload_props),
        "The IPC payload must not expose arbitrary execution or filesystem fields",
    )

    source = MORA_JS.read_text(encoding="utf-8")
    require('"mora-boost": {' in source, "Mora Boost is missing from the app definitions")
    require("Игровая производительность под контролем" in source, "Mora Boost does not explain its workspace")
    index = MORA_INDEX.read_text(encoding="utf-8")
    require('data-app="mora-boost"' in index, "Mora Boost tile is missing from the current desktop")
    catalog = json.loads(APP_CATALOG.read_text(encoding="utf-8"))
    require(any(item.get("id") == "mora-boost" for item in catalog.get("built_in_apps", [])), "Mora Boost is missing from the versioned app catalogue")
    require("https://github.com/Ivan-VHS/OPlague" in source, "Mora Boost must link to the OPlague project")

    worker = WORKER_JS.read_text(encoding="utf-8")
    cache_match = re.search(r'const CACHE="([^"]+)"', worker)
    require(cache_match is not None, "Mora service-worker cache key is missing")
    require("./app.js" in worker and "./index.html" in worker, "Offline shell assets are not cached")

    require(INTEGRATION_DOC.is_file(), "Gaming integration documentation is missing")
    print("Mora gaming IPC contract and workspace entry point validated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
