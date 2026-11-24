#!/usr/bin/env python3
"""Validate the DuckOS application catalog and its versioned transfer contract."""
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    with (ROOT / path).open(encoding="utf-8") as stream:
        return json.load(stream)


def main() -> int:
    catalog = read_json("catalogs/preinstalled-applications.v1.json")
    catalog_schema = read_json("schemas/preinstalled-applications.v1.schema.json")
    transfer_schema = read_json("schemas/unify.transfer.v1.schema.json")

    Draft202012Validator.check_schema(catalog_schema)
    Draft202012Validator.check_schema(transfer_schema)
    Draft202012Validator(
        catalog_schema, format_checker=FormatChecker()
    ).validate(catalog)

    expected = {
        "cockos", "kavun", "ka-bon", "gloverty", "po", "illidia", "unify",
        "sestem", "setupup", "orriganize", "abriganza", "olaab", "concrete-thump",
        "seu-beu", "love-il", "poi", "poi-2", "po-2", "gamecharager", "exedotexe",
        "beelzebub-av",
    }
    actual = {app["id"] for app in catalog["applications"]}
    if actual != expected or len(actual) != 21:
        raise SystemExit(f"Unexpected app catalog IDs: {sorted(actual)}")

    for app in catalog["applications"]:
        expected_maturity = "partial" if app["id"] == "beelzebub-av" else "specified"
        if app["maturity_status"] != expected_maturity:
            raise SystemExit(
                f"{app['id']}: native app maturity must be {expected_maturity}"
            )
        if app["prototype_status"] != "partial":
            raise SystemExit(
                f"{app['id']}: browser prototype status must remain partial"
            )
        expected_evidence = (
            "prototype/mora-home.html"
            if app["id"] in {"cockos", "kavun", "ka-bon", "gloverty", "po", "illidia", "unify"}
            else "mora/index.html"
        )
        if expected_evidence not in app["prototype_evidence"]:
            raise SystemExit(
                f"{app['id']}: missing browser-prototype evidence path {expected_evidence}"
            )

    if len(catalog["workflows"]) != 10:
        raise SystemExit("Expected four core, five extended and one security workflow")

    for workflow in catalog["workflows"]:
        if workflow["source"] not in actual or workflow["target"] not in actual:
            raise SystemExit(f"Unknown application in workflow {workflow['id']}")
        if not workflow["user_consent_required"]:
            raise SystemExit(f"Workflow {workflow['id']} must require consent")

    transfer = next(
        (item for item in catalog["interfaces"]
         if item["id"] == "unify.transfer.v1"),
        None,
    )
    if not transfer:
        raise SystemExit("unify.transfer.v1 is missing from the app catalog")
    if transfer["max_package_bytes"] != 20 * 1024 * 1024:
        raise SystemExit("Unexpected Unify package size limit")
    if transfer["max_clip_bytes"] != 12 * 1024 * 1024:
        raise SystemExit("Unexpected Unify clip size limit")

    print(
        f"Validated {len(actual)} applications, "
        f"{len(catalog['workflows'])} workflows and "
        f"{len(catalog['interfaces'])} interfaces."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
