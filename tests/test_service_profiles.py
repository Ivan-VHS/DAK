from __future__ import annotations

import unittest

from duckos.service_profiles import (
    PLAN_SCHEMA,
    SCHEMA,
    ServicePlanLimits,
    ServiceProfileError,
    plan_service_startup,
    validate_service_profile,
)


def profile(service_id: str, dependencies: list[str] | None = None) -> dict:
    return {
        "schema": SCHEMA,
        "id": service_id,
        "version": "1.2.3",
        "runtime": "python",
        "execution": {
            "model": "worker-pool",
            "max_concurrency": 4,
            "queue_capacity": 32,
            "timeout_ms": 5000,
            "max_input_bytes": 1024 * 1024,
            "max_output_bytes": 2 * 1024 * 1024,
            "max_memory_bytes": 64 * 1024 * 1024,
        },
        "health": {
            "liveness_enabled": True,
            "readiness_enabled": True,
            "startup_grace_ms": 1000,
            "probe_timeout_ms": 1000,
        },
        "restart": {
            "max_retries": 4,
            "base_delay_ms": 100,
            "max_delay_ms": 1000,
            "multiplier": 2.0,
        },
        "resilience": {
            "circuit_breaker_enabled": True,
            "failure_threshold": 5,
            "open_state_ms": 30000,
            "half_open_max_calls": 2,
        },
        "dependencies": dependencies or [],
        "capabilities": ["storage.read", "metrics.publish"],
    }


class ServiceProfileTests(unittest.TestCase):
    def test_validates_and_normalizes_profile(self):
        item = validate_service_profile(profile("telemetry"))
        self.assertEqual(item["id"], "telemetry")
        self.assertEqual(item["capabilities"], ["metrics.publish", "storage.read"])
        self.assertTrue(item["health"]["readiness_enabled"])

    def test_plan_is_deterministic_and_dependency_first(self):
        services = [
            profile("telemetry", ["storage"]),
            profile("ui", ["telemetry"]),
            profile("storage"),
        ]
        first = plan_service_startup(services)
        second = plan_service_startup(list(reversed(services)))
        self.assertEqual(first, second)
        self.assertEqual(first["schema"], PLAN_SCHEMA)
        self.assertEqual(first["startup_order"], ["storage", "telemetry", "ui"])
        self.assertFalse(first["services_started"])
        self.assertFalse(first["processes_spawned"])
        self.assertEqual(
            first["services"][0]["retry_schedule_ms"],
            [100, 200, 400, 800],
        )

    def test_rejects_duplicate_missing_and_cyclic_services(self):
        with self.assertRaisesRegex(ServiceProfileError, "duplicate service"):
            plan_service_startup([profile("storage"), profile("storage")])
        with self.assertRaisesRegex(ServiceProfileError, "missing dependencies"):
            plan_service_startup([profile("telemetry", ["storage"])])
        with self.assertRaisesRegex(ServiceProfileError, "cycle"):
            plan_service_startup([
                profile("alpha", ["beta"]),
                profile("beta", ["alpha"]),
            ])

    def test_rejects_invalid_execution_and_health_bounds(self):
        item = profile("bad")
        item["execution"]["max_concurrency"] = True
        with self.assertRaises(ServiceProfileError):
            validate_service_profile(item)
        item = profile("bad")
        item["health"]["readiness_enabled"] = False
        with self.assertRaisesRegex(ServiceProfileError, "readiness"):
            validate_service_profile(item)
        item = profile("bad")
        item["health"]["probe_timeout_ms"] = 6000
        with self.assertRaisesRegex(ServiceProfileError, "must not exceed"):
            validate_service_profile(item)

    def test_rejects_invalid_circuit_breaker_and_retry_configuration(self):
        item = profile("bad")
        item["resilience"]["open_state_ms"] = 0
        with self.assertRaisesRegex(ServiceProfileError, "open_state_ms"):
            validate_service_profile(item)
        item = profile("bad")
        item["restart"]["max_delay_ms"] = 99
        with self.assertRaisesRegex(ServiceProfileError, "at least"):
            validate_service_profile(item)

    def test_aggregate_resource_limits_are_enforced(self):
        services = [profile("one"), profile("two")]
        with self.assertRaisesRegex(ServiceProfileError, "concurrency"):
            plan_service_startup(
                services,
                limits=ServicePlanLimits(max_total_concurrency=4),
            )
        with self.assertRaisesRegex(ServiceProfileError, "memory"):
            plan_service_startup(
                services,
                limits=ServicePlanLimits(max_total_memory_bytes=100),
            )

    def test_rejects_unknown_fields_and_unbounded_collections(self):
        item = profile("extra")
        item["spring_magic"] = True
        with self.assertRaisesRegex(ServiceProfileError, "exactly"):
            validate_service_profile(item)
        with self.assertRaises(ServiceProfileError):
            plan_service_startup([profile("one")] * 1025)


if __name__ == "__main__":
    unittest.main()
