"""Context-aware workload hints that never lower active protection."""
from __future__ import annotations

from typing import Any


def recommend_profile(
    *,
    fullscreen: bool = False,
    on_battery: bool = False,
    cpu_load_percent: float = 0.0,
    suspicious_activity: bool = False,
) -> dict[str, Any]:
    if isinstance(cpu_load_percent, bool) or not isinstance(cpu_load_percent, (int, float)) or not 0 <= cpu_load_percent <= 100:
        raise ValueError("cpu_load_percent must be between 0 and 100")
    if suspicious_activity:
        profile = "security_critical"
        deep_scan = "immediate"
    elif fullscreen or on_battery or cpu_load_percent >= 80:
        profile = "quiet"
        deep_scan = "defer_until_idle"
    else:
        profile = "balanced"
        deep_scan = "incremental"
    return {
        "schema": "duckos.security-resource-profile.v1",
        "profile": profile,
        "deep_scan": deep_scan,
        "event_collection": "unchanged",
        "decision_thresholds": "unchanged",
        "protection_suppressed": False,
        "reason": "suspicious_activity_overrides_comfort_profiles" if suspicious_activity else "workload_context",
    }
