"""Evidence-driven policy assessment and safe session transitions for DuckOS gaming mode.

This module produces plans and capability reports. It does not set process
priorities, CPU affinity, clocks, voltages, fan curves, driver state or registry
values. Those operations require a separately authenticated native provider.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).with_name("game-performance-rules.v1.json")
CATALOG_SCHEMA = "duckos.gaming-rule-catalog.v1"
ASSESSMENT_SCHEMA = "duckos.gaming-policy-assessment.v1"
MAX_CATALOG_BYTES = 512 * 1024
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
DOMAINS = {"detection", "cpu", "memory", "graphics", "io", "power"}
TRANSITIONS = {
    ("idle", "game_detected"): ("starting", ("capture_baseline",)),
    ("starting", "snapshot_created"): ("active", ("prepare_policy_plan",)),
    ("active", "foreground_lost"): ("background", ("defer_optional_work",)),
    ("background", "foreground_restored"): ("active", ("refresh_policy_plan",)),
    ("active", "game_exited"): ("restoring", ("restore_previous_profile", "release_reservations")),
    ("background", "game_exited"): ("restoring", ("restore_previous_profile", "release_reservations")),
    ("restoring", "restore_confirmed"): ("idle", ()),
}
IDEMPOTENT_EVENTS = {
    ("starting", "game_detected"),
    ("active", "snapshot_created"),
    ("background", "foreground_lost"),
    ("active", "foreground_restored"),
    ("restoring", "game_exited"),
    ("idle", "restore_confirmed"),
}


class GamingPolicyError(ValueError):
    """Raised when a policy catalog, capability set or session event is invalid."""


def _safe_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise GamingPolicyError(f"{field} must be a safe identifier of at most 128 characters")
    return value


def load_rule_catalog(path: str | Path = CATALOG_PATH) -> dict[str, Any]:
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise GamingPolicyError("gaming rule catalog must be a regular, non-symlink file")
    if source.stat().st_size > MAX_CATALOG_BYTES:
        raise GamingPolicyError("gaming rule catalog exceeds the 512 KiB limit")
    try:
        catalog = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GamingPolicyError(f"cannot read gaming rule catalog: {error}") from error
    if not isinstance(catalog, dict) or catalog.get("schema") != CATALOG_SCHEMA:
        raise GamingPolicyError(f"expected {CATALOG_SCHEMA}")
    rules = catalog.get("rules")
    if catalog.get("version") != 1 or catalog.get("rule_count") != 66:
        raise GamingPolicyError("gaming rule catalog must be version 1 with exactly 66 rules")
    if not isinstance(rules, list) or len(rules) != 66:
        raise GamingPolicyError("gaming rule catalog must contain exactly 66 rule records")
    numbers: list[int] = []
    identifiers: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise GamingPolicyError("every gaming rule must be an object")
        number = rule.get("number")
        if isinstance(number, bool) or not isinstance(number, int):
            raise GamingPolicyError("rule number must be an integer")
        if number in numbers or number < 1 or number > 66:
            raise GamingPolicyError("rule numbers must be unique and between 1 and 66")
        numbers.append(number)
        expected_id = f"GPR-{number:02d}"
        if rule.get("id") != expected_id or expected_id in identifiers:
            raise GamingPolicyError(f"rule {number} has an invalid or duplicate identifier")
        identifiers.add(expected_id)
        if rule.get("domain") not in DOMAINS:
            raise GamingPolicyError(f"rule {number} has an unknown domain")
        providers = rule.get("providers")
        if not isinstance(providers, list) or not providers or any(
            not isinstance(name, str) or not SAFE_ID.fullmatch(name) for name in providers
        ):
            raise GamingPolicyError(f"rule {number} must declare safe provider identifiers")
        if rule.get("execution") not in {"observe_or_recommend", "reversible_with_snapshot", "goal"}:
            raise GamingPolicyError(f"rule {number} has an unknown execution class")
        if not isinstance(rule.get("requires_consent"), bool):
            raise GamingPolicyError(f"rule {number} must declare its consent requirement")
    if sorted(numbers) != list(range(1, 67)):
        raise GamingPolicyError("rule numbers must form the complete sequence 1..66")
    return catalog


def _normalize_capabilities(capabilities: dict[str, Any], catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(capabilities, dict):
        raise GamingPolicyError("capabilities must be an object")
    known = {provider for rule in catalog["rules"] for provider in rule["providers"]}
    unknown = set(capabilities) - known
    if unknown:
        raise GamingPolicyError(f"unknown capability providers: {', '.join(sorted(unknown))}")
    normalized: dict[str, dict[str, Any]] = {}
    for name, value in capabilities.items():
        if isinstance(value, bool):
            normalized[name] = {"available": value, "provider": name, "version": None, "reason": None}
            continue
        if not isinstance(value, dict):
            raise GamingPolicyError(f"capability {name} must be a boolean or object")
        if set(value) - {"available", "provider", "version", "reason"}:
            raise GamingPolicyError(f"capability {name} contains unknown fields")
        available = value.get("available")
        if not isinstance(available, bool):
            raise GamingPolicyError(f"capability {name}.available must be a boolean")
        normalized[name] = {
            "available": available,
            "provider": str(value.get("provider") or name)[:128],
            "version": str(value["version"])[:64] if value.get("version") is not None else None,
            "reason": str(value["reason"])[:256] if value.get("reason") is not None else None,
        }
    return normalized


def assess_capabilities(
    capabilities: dict[str, Any] | None = None,
    *,
    catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return per-rule provider readiness without claiming an action was applied."""
    catalog = catalog or load_rule_catalog()
    providers = _normalize_capabilities(capabilities or {}, catalog)
    results = []
    for rule in catalog["rules"]:
        evidence = []
        missing = []
        present = 0
        for provider_name in rule["providers"]:
            provider = providers.get(provider_name)
            if provider is None:
                missing.append(provider_name)
                continue
            present += 1
            evidence.append({
                "provider": provider_name,
                "available": provider["available"],
                "version": provider["version"],
                "reason": provider["reason"],
            })
            if not provider["available"]:
                missing.append(provider_name)
        status = "available" if not missing else ("partial" if present else "unavailable")
        results.append({
            "id": rule["id"],
            "number": rule["number"],
            "domain": rule["domain"],
            "title": rule["title"],
            "status": status,
            "missing_providers": missing,
            "evidence": evidence,
            "execution": rule["execution"],
            "requires_consent": rule["requires_consent"],
            "action_applied": False,
        })
    counts = {
        status: sum(item["status"] == status for item in results)
        for status in ("available", "partial", "unavailable")
    }
    return {
        "schema": ASSESSMENT_SCHEMA,
        "catalog_schema": CATALOG_SCHEMA,
        "catalog_version": catalog["version"],
        "rule_count": len(results),
        "summary": counts,
        "rules": results,
        "execution_performed": False,
        "system_settings_changed": False,
    }


def plan_session_transition(
    current_state: str,
    event: str,
    *,
    profile_id: str | None = None,
    process_identity: str | None = None,
    snapshot_id: str | None = None,
) -> dict[str, Any]:
    """Build an idempotent, non-executing transition for a gaming session."""
    if current_state not in {"idle", "starting", "active", "background", "restoring"}:
        raise GamingPolicyError("unknown gaming session state")
    event = _safe_id(event, "event")
    key = (current_state, event)
    if key in IDEMPOTENT_EVENTS:
        return {
            "schema": "duckos.gaming-session-transition.v1",
            "from": current_state,
            "to": current_state,
            "event": event,
            "actions": [],
            "idempotent": True,
            "execution_performed": False,
        }
    transition = TRANSITIONS.get(key)
    if transition is None:
        raise GamingPolicyError(f"event {event!r} is not valid while session state is {current_state!r}")
    next_state, actions = transition
    identity: dict[str, str] = {}
    if event == "game_detected":
        identity = {
            "profile_id": _safe_id(profile_id, "profile_id"),
            "process_identity": _safe_id(process_identity, "process_identity"),
        }
    elif event == "snapshot_created":
        identity = {"snapshot_id": _safe_id(snapshot_id, "snapshot_id")}
    return {
        "schema": "duckos.gaming-session-transition.v1",
        "from": current_state,
        "to": next_state,
        "event": event,
        "identity": identity,
        "actions": list(actions),
        "requires_authenticated_executor": bool(actions),
        "execution_performed": False,
        "system_settings_changed": False,
    }
