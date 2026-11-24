"""Validated, bounded service profiles and deterministic startup planning.

This is a control-plane contract inspired by mature Java service ecosystems:
Spring Boot health/configuration, Quarkus/Micronaut build-time resource planning,
Vert.x execution models, and standard circuit-breaker/retry policies.

It validates and plans only. It does not spawn processes, load modules, bind
sockets, or claim to implement a production service supervisor.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
import re
from typing import Any


SCHEMA = "duckos.service-profile.v1"
PLAN_SCHEMA = "duckos.service-plan.v1"
MAX_SERVICES = 1024
MAX_DEPENDENCIES = 4096
MAX_CAPABILITIES = 128

_ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
_CAPABILITY = re.compile(r"^[a-z][a-z0-9_.-]{0,95}$")
_RUNTIME_MODELS = {
    "native-c11", "native-cxx", "python", "node", "jvm", "jvm-native", "reaper"
}
_EXECUTION_MODELS = {"blocking", "worker-pool", "event-loop", "stream", "batch"}


class ServiceProfileError(ValueError):
    """A service profile or aggregate startup plan violates its contract."""


@dataclass(frozen=True, slots=True)
class ServicePlanLimits:
    max_total_concurrency: int = 4096
    max_total_queued_jobs: int = 65536
    max_total_memory_bytes: int = 16 * 1024 * 1024 * 1024
    max_profile_bytes: int = 256 * 1024

    def __post_init__(self) -> None:
        for name, value, maximum in (
            ("max_total_concurrency", self.max_total_concurrency, 1_000_000),
            ("max_total_queued_jobs", self.max_total_queued_jobs, 10_000_000),
            ("max_total_memory_bytes", self.max_total_memory_bytes, 1 << 50),
            ("max_profile_bytes", self.max_profile_bytes, 4 * 1024 * 1024),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
                raise ServiceProfileError(f"{name} must be an integer in [1, {maximum}]")


def _integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ServiceProfileError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def _object(value: Any, name: str, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ServiceProfileError(f"{name} fields must be exactly {sorted(fields)}")
    return value


def validate_service_profile(profile: Any) -> dict[str, Any]:
    required = {
        "schema", "id", "version", "runtime", "execution", "health",
        "restart", "resilience", "dependencies", "capabilities",
    }
    item = _object(profile, "service profile", required)
    if item["schema"] != SCHEMA:
        raise ServiceProfileError(f"schema must be {SCHEMA}")
    service_id = item["id"]
    if not isinstance(service_id, str) or not _ID.fullmatch(service_id):
        raise ServiceProfileError("id must be a lowercase service identifier")
    if not isinstance(item["version"], str) or not _VERSION.fullmatch(item["version"]):
        raise ServiceProfileError("version must use MAJOR.MINOR.PATCH semantic form")
    runtime = item["runtime"]
    if not isinstance(runtime, str) or runtime not in _RUNTIME_MODELS:
        raise ServiceProfileError(f"runtime must be one of {sorted(_RUNTIME_MODELS)}")

    execution = _object(item["execution"], "execution", {
        "model", "max_concurrency", "queue_capacity", "timeout_ms",
        "max_input_bytes", "max_output_bytes", "max_memory_bytes",
    })
    if not isinstance(execution["model"], str) or execution["model"] not in _EXECUTION_MODELS:
        raise ServiceProfileError(f"execution.model must be one of {sorted(_EXECUTION_MODELS)}")
    concurrency = _integer(execution["max_concurrency"], "execution.max_concurrency", 1, 65536)
    queue_capacity = _integer(execution["queue_capacity"], "execution.queue_capacity", 0, 1_000_000)
    timeout_ms = _integer(execution["timeout_ms"], "execution.timeout_ms", 1, 24 * 60 * 60 * 1000)
    input_bytes = _integer(execution["max_input_bytes"], "execution.max_input_bytes", 1, 1 << 40)
    output_bytes = _integer(execution["max_output_bytes"], "execution.max_output_bytes", 1, 1 << 40)
    memory_bytes = _integer(execution["max_memory_bytes"], "execution.max_memory_bytes", 1, 1 << 50)

    health = _object(item["health"], "health", {
        "liveness_enabled", "readiness_enabled", "startup_grace_ms", "probe_timeout_ms",
    })
    for name in ("liveness_enabled", "readiness_enabled"):
        if not isinstance(health[name], bool):
            raise ServiceProfileError(f"health.{name} must be boolean")
    if not health["liveness_enabled"] or not health["readiness_enabled"]:
        raise ServiceProfileError("liveness and readiness probes must both be enabled")
    startup_grace = _integer(health["startup_grace_ms"], "health.startup_grace_ms", 0, 24 * 60 * 60 * 1000)
    probe_timeout = _integer(health["probe_timeout_ms"], "health.probe_timeout_ms", 1, 300_000)
    if probe_timeout > timeout_ms:
        raise ServiceProfileError("health.probe_timeout_ms must not exceed execution.timeout_ms")

    restart = _object(item["restart"], "restart", {
        "max_retries", "base_delay_ms", "max_delay_ms", "multiplier",
    })
    retries = _integer(restart["max_retries"], "restart.max_retries", 0, 100)
    base_delay = _integer(restart["base_delay_ms"], "restart.base_delay_ms", 0, 3_600_000)
    max_delay = _integer(restart["max_delay_ms"], "restart.max_delay_ms", 0, 86_400_000)
    multiplier = restart["multiplier"]
    if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)) or not math.isfinite(multiplier) or not 1.0 <= multiplier <= 10.0:
        raise ServiceProfileError("restart.multiplier must be finite and within [1.0, 10.0]")
    if max_delay < base_delay:
        raise ServiceProfileError("restart.max_delay_ms must be at least base_delay_ms")

    resilience = _object(item["resilience"], "resilience", {
        "circuit_breaker_enabled", "failure_threshold", "open_state_ms", "half_open_max_calls",
    })
    if not isinstance(resilience["circuit_breaker_enabled"], bool):
        raise ServiceProfileError("resilience.circuit_breaker_enabled must be boolean")
    failure_threshold = _integer(resilience["failure_threshold"], "resilience.failure_threshold", 1, 1000)
    open_state_ms = _integer(resilience["open_state_ms"], "resilience.open_state_ms", 0, 24 * 60 * 60 * 1000)
    half_open = _integer(resilience["half_open_max_calls"], "resilience.half_open_max_calls", 1, 1000)
    if resilience["circuit_breaker_enabled"] and open_state_ms == 0:
        raise ServiceProfileError("enabled circuit breaker requires open_state_ms > 0")

    dependencies = item["dependencies"]
    if not isinstance(dependencies, list) or len(dependencies) > MAX_DEPENDENCIES:
        raise ServiceProfileError(f"dependencies must be a list of at most {MAX_DEPENDENCIES} items")
    if any(not isinstance(dep, str) or not _ID.fullmatch(dep) for dep in dependencies):
        raise ServiceProfileError("dependencies must contain lowercase service identifiers")
    if len(set(dependencies)) != len(dependencies):
        raise ServiceProfileError("dependencies must be unique")
    if service_id in dependencies:
        raise ServiceProfileError("service cannot depend on itself")

    capabilities = item["capabilities"]
    if not isinstance(capabilities, list) or len(capabilities) > MAX_CAPABILITIES:
        raise ServiceProfileError(f"capabilities must contain at most {MAX_CAPABILITIES} items")
    if any(not isinstance(cap, str) or not _CAPABILITY.fullmatch(cap) for cap in capabilities):
        raise ServiceProfileError("capabilities must be lowercase capability identifiers")
    if len(set(capabilities)) != len(capabilities):
        raise ServiceProfileError("capabilities must be unique")

    # Normalize to a stable, JSON-safe representation.
    return {
        "schema": SCHEMA,
        "id": service_id,
        "version": item["version"],
        "runtime": runtime,
        "execution": {
            "model": execution["model"],
            "max_concurrency": concurrency,
            "queue_capacity": queue_capacity,
            "timeout_ms": timeout_ms,
            "max_input_bytes": input_bytes,
            "max_output_bytes": output_bytes,
            "max_memory_bytes": memory_bytes,
        },
        "health": {
            "liveness_enabled": True,
            "readiness_enabled": True,
            "startup_grace_ms": startup_grace,
            "probe_timeout_ms": probe_timeout,
        },
        "restart": {
            "max_retries": retries,
            "base_delay_ms": base_delay,
            "max_delay_ms": max_delay,
            "multiplier": float(multiplier),
        },
        "resilience": {
            "circuit_breaker_enabled": resilience["circuit_breaker_enabled"],
            "failure_threshold": failure_threshold,
            "open_state_ms": open_state_ms,
            "half_open_max_calls": half_open,
        },
        "dependencies": sorted(dependencies),
        "capabilities": sorted(capabilities),
    }


def _retry_schedule(profile: dict[str, Any]) -> list[int]:
    policy = profile["restart"]
    result = []
    delay = float(policy["base_delay_ms"])
    for _ in range(policy["max_retries"]):
        result.append(min(int(delay), policy["max_delay_ms"]))
        delay = min(delay * policy["multiplier"], policy["max_delay_ms"])
    return result


def plan_service_startup(
    profiles: list[dict[str, Any]],
    *,
    limits: ServicePlanLimits | None = None,
) -> dict[str, Any]:
    """Validate every profile and return a deterministic, non-executing plan."""
    policy = limits if limits is not None else ServicePlanLimits()
    if not isinstance(policy, ServicePlanLimits):
        raise ServiceProfileError("limits must be a ServicePlanLimits instance")
    if not isinstance(profiles, list) or len(profiles) > MAX_SERVICES:
        raise ServiceProfileError(f"profiles must be a list of at most {MAX_SERVICES} entries")

    validated = [validate_service_profile(item) for item in profiles]
    by_id: dict[str, dict[str, Any]] = {}
    for profile in validated:
        if profile["id"] in by_id:
            raise ServiceProfileError(f"duplicate service id: {profile['id']}")
        by_id[profile["id"]] = profile

    edge_count = sum(len(item["dependencies"]) for item in validated)
    if edge_count > MAX_DEPENDENCIES:
        raise ServiceProfileError("service graph exceeds its dependency edge limit")
    for profile in validated:
        missing = sorted(set(profile["dependencies"]) - by_id.keys())
        if missing:
            raise ServiceProfileError(f"{profile['id']} has missing dependencies: {missing}")

    incoming = {name: len(profile["dependencies"]) for name, profile in by_id.items()}
    dependents = {name: [] for name in by_id}
    for name, profile in by_id.items():
        for dep in profile["dependencies"]:
            dependents[dep].append(name)
    ready = [name for name, count in incoming.items() if count == 0]
    heapq.heapify(ready)
    order: list[str] = []
    while ready:
        current = heapq.heappop(ready)
        order.append(current)
        for dependent in sorted(dependents[current]):
            incoming[dependent] -= 1
            if incoming[dependent] == 0:
                heapq.heappush(ready, dependent)
    if len(order) != len(by_id):
        cycle_members = sorted(name for name, count in incoming.items() if count > 0)
        raise ServiceProfileError(f"service dependency cycle detected among {cycle_members}")

    total_concurrency = sum(item["execution"]["max_concurrency"] for item in validated)
    total_queue = sum(item["execution"]["queue_capacity"] for item in validated)
    total_memory = sum(item["execution"]["max_memory_bytes"] for item in validated)
    if total_concurrency > policy.max_total_concurrency:
        raise ServiceProfileError("aggregate service concurrency exceeds the configured plan limit")
    if total_queue > policy.max_total_queued_jobs:
        raise ServiceProfileError("aggregate service queue capacity exceeds the configured plan limit")
    if total_memory > policy.max_total_memory_bytes:
        raise ServiceProfileError("aggregate service memory reservations exceed the configured plan limit")

    return {
        "schema": PLAN_SCHEMA,
        "valid": True,
        "startup_order": order,
        "services": [
            {
                "id": name,
                "runtime": by_id[name]["runtime"],
                "execution": by_id[name]["execution"],
                "health": by_id[name]["health"],
                "restart": by_id[name]["restart"],
                "retry_schedule_ms": _retry_schedule(by_id[name]),
                "resilience": by_id[name]["resilience"],
                "dependencies": by_id[name]["dependencies"],
                "capabilities": by_id[name]["capabilities"],
            }
            for name in order
        ],
        "aggregate": {
            "service_count": len(validated),
            "max_concurrency": total_concurrency,
            "queue_capacity": total_queue,
            "reserved_memory_bytes": total_memory,
        },
        "services_started": False,
        "processes_spawned": False,
        "network_ports_bound": False,
    }
