"""Profile-bound hardware bench controller with fail-safe adapter boundaries."""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import time
from typing import Any, Protocol

SCHEMA = "duckos.bench-profile.v1"
MAX_PROFILE_BYTES = 1024 * 1024
_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_-]{0,47}$")


class BenchError(ValueError):
    """Raised when a bench request violates its board profile or safety state."""


class BenchAdapter(Protocol):
    def is_connected(self) -> bool: ...
    def discover(self) -> dict[str, Any]: ...
    def read_telemetry(self) -> dict[str, Any]: ...
    def set_rail_power(
        self, rail_id: str, enabled: bool,
        voltage_v: float | None, current_limit_a: float | None,
    ) -> None: ...
    def start_test(self, test_id: str, fixture_slot: str, duration_seconds: int) -> None: ...
    def stop_test(self) -> None: ...
    def emergency_disable(self) -> None:
        """Disable every controlled power output using the board's safe path."""
        ...


def _number(value: Any, name: str, *, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise BenchError(f"{name} must be a finite number")
    result = float(value)
    if not minimum <= result <= maximum:
        raise BenchError(f"{name} must be between {minimum} and {maximum}")
    return result


def validate_bench_profile(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise BenchError(f"bench profile must use {SCHEMA}")
    required = {
        "schema", "board_id", "fixture_slots", "serial_ports",
        "max_telemetry_age_seconds", "rails", "buses", "accelerators", "probes", "tests",
    }
    if set(payload) != required:
        raise BenchError(f"bench profile fields must be exactly {sorted(required)}")
    board_id = payload["board_id"]
    if not isinstance(board_id, str) or not _IDENTIFIER.fullmatch(board_id):
        raise BenchError("board_id must be a lowercase identifier")

    fixture_slots = payload["fixture_slots"]
    if (
        not isinstance(fixture_slots, list)
        or not fixture_slots
        or len(fixture_slots) > 2
        or any(not isinstance(item, str) or item not in {"A", "B"} for item in fixture_slots)
        or len(set(fixture_slots)) != len(fixture_slots)
    ):
        raise BenchError("fixture_slots must contain A, B or both without duplicates")

    serial_ports = payload["serial_ports"]
    if (
        not isinstance(serial_ports, list)
        or len(serial_ports) > 16
        or any(not isinstance(port, str) or not port.strip() or len(port) > 128 for port in serial_ports)
        or len(set(serial_ports)) != len(serial_ports)
    ):
        raise BenchError("serial_ports must be a unique list of at most 16 port names")

    freshness = _number(
        payload["max_telemetry_age_seconds"], "max_telemetry_age_seconds",
        minimum=1, maximum=30,
    )
    rails = payload["rails"]
    if not isinstance(rails, list) or not 1 <= len(rails) <= 32:
        raise BenchError("rails must contain 1..32 configured power rails")
    normalized_rails = []
    rail_ids = set()
    for rail in rails:
        if not isinstance(rail, dict) or set(rail) != {
            "id", "min_voltage_v", "max_voltage_v", "max_current_a",
            "max_temperature_c", "cooldown_temperature_c",
        }:
            raise BenchError("each rail must have the exact documented fields")
        rail_id = rail["id"]
        if not isinstance(rail_id, str) or not _IDENTIFIER.fullmatch(rail_id) or rail_id in rail_ids:
            raise BenchError("rail IDs must be unique lowercase identifiers")
        rail_ids.add(rail_id)
        minimum = _number(rail["min_voltage_v"], rail_id + ".min_voltage_v", minimum=0, maximum=1000)
        maximum = _number(rail["max_voltage_v"], rail_id + ".max_voltage_v", minimum=0.001, maximum=1000)
        current = _number(rail["max_current_a"], rail_id + ".max_current_a", minimum=0.001, maximum=10000)
        temperature = _number(rail["max_temperature_c"], rail_id + ".max_temperature_c", minimum=-40, maximum=200)
        cooldown = _number(rail["cooldown_temperature_c"], rail_id + ".cooldown_temperature_c", minimum=-40, maximum=200)
        if maximum <= minimum or cooldown >= temperature:
            raise BenchError(f"{rail_id}: voltage range or cooldown threshold is invalid")
        normalized_rails.append({
            "id": rail_id,
            "min_voltage_v": minimum,
            "max_voltage_v": maximum,
            "max_current_a": current,
            "max_temperature_c": temperature,
            "cooldown_temperature_c": cooldown,
        })


    buses = payload["buses"]
    if not isinstance(buses, list) or len(buses) > 32:
        raise BenchError("buses must contain at most 32 configured bus links")
    normalized_buses = []
    bus_ids = set()
    for bus in buses:
        if not isinstance(bus, dict) or set(bus) != {
            "id", "kind", "max_link_width", "max_link_speed_gbps", "must_be_present",
        }:
            raise BenchError("each bus profile must have the exact documented fields")
        bus_id = bus["id"]
        if not isinstance(bus_id, str) or not _IDENTIFIER.fullmatch(bus_id) or bus_id in bus_ids:
            raise BenchError("bus IDs must be unique lowercase identifiers")
        if not isinstance(bus["kind"], str) or bus["kind"] not in {"pcie", "usb", "i2c", "spi"}:
            raise BenchError(f"{bus_id}: unsupported bus kind")
        width = bus["max_link_width"]
        if isinstance(width, bool) or not isinstance(width, int) or not 1 <= width <= 64:
            raise BenchError(f"{bus_id}: max_link_width must be 1..64")
        speed = _number(bus["max_link_speed_gbps"], bus_id + ".max_link_speed_gbps", minimum=0.001, maximum=256)
        if not isinstance(bus["must_be_present"], bool):
            raise BenchError(f"{bus_id}: must_be_present must be boolean")
        bus_ids.add(bus_id)
        normalized_buses.append({
            "id": bus_id, "kind": bus["kind"], "max_link_width": width,
            "max_link_speed_gbps": speed, "must_be_present": bus["must_be_present"],
        })

    accelerators = payload["accelerators"]
    if not isinstance(accelerators, list) or len(accelerators) > 8:
        raise BenchError("accelerators must contain at most 8 configured GPU/NPU devices")
    normalized_accelerators = []
    accelerator_ids = set()
    for accelerator in accelerators:
        if not isinstance(accelerator, dict) or set(accelerator) != {
            "id", "kind", "max_temperature_c", "max_utilization_percent", "must_be_present",
        }:
            raise BenchError("each accelerator profile must have the exact documented fields")
        accelerator_id = accelerator["id"]
        if (
            not isinstance(accelerator_id, str)
            or not _IDENTIFIER.fullmatch(accelerator_id)
            or accelerator_id in accelerator_ids
        ):
            raise BenchError("accelerator IDs must be unique lowercase identifiers")
        if not isinstance(accelerator["kind"], str) or accelerator["kind"] not in {"gpu", "npu"}:
            raise BenchError(f"{accelerator_id}: kind must be gpu or npu")
        temperature = _number(
            accelerator["max_temperature_c"], accelerator_id + ".max_temperature_c",
            minimum=-40, maximum=200,
        )
        utilization = _number(
            accelerator["max_utilization_percent"], accelerator_id + ".max_utilization_percent",
            minimum=1, maximum=100,
        )
        if not isinstance(accelerator["must_be_present"], bool):
            raise BenchError(f"{accelerator_id}: must_be_present must be boolean")
        accelerator_ids.add(accelerator_id)
        normalized_accelerators.append({
            "id": accelerator_id, "kind": accelerator["kind"],
            "max_temperature_c": temperature,
            "max_utilization_percent": utilization,
            "must_be_present": accelerator["must_be_present"],
        })

    probes = payload["probes"]
    if not isinstance(probes, list) or len(probes) > 32:
        raise BenchError("probes must contain at most 32 configured measurement probes")
    normalized_probes = []
    probe_ids = set()
    for probe in probes:
        if not isinstance(probe, dict) or set(probe) != {
            "id", "unit", "min_value", "max_value", "max_age_seconds", "must_be_present",
        }:
            raise BenchError("each probe profile must have the exact documented fields")
        probe_id = probe["id"]
        if not isinstance(probe_id, str) or not _IDENTIFIER.fullmatch(probe_id) or probe_id in probe_ids:
            raise BenchError("probe IDs must be unique lowercase identifiers")
        unit = probe["unit"]
        if not isinstance(unit, str) or not unit.strip() or len(unit) > 16:
            raise BenchError(f"{probe_id}: unit must contain 1..16 characters")
        minimum = _number(probe["min_value"], probe_id + ".min_value", minimum=-1e9, maximum=1e9)
        maximum = _number(probe["max_value"], probe_id + ".max_value", minimum=-1e9, maximum=1e9)
        max_age = _number(probe["max_age_seconds"], probe_id + ".max_age_seconds", minimum=1, maximum=30)
        if maximum <= minimum or not isinstance(probe["must_be_present"], bool):
            raise BenchError(f"{probe_id}: range or must_be_present setting is invalid")
        probe_ids.add(probe_id)
        normalized_probes.append({
            "id": probe_id, "unit": unit, "min_value": minimum, "max_value": maximum,
            "max_age_seconds": max_age, "must_be_present": probe["must_be_present"],
        })

    tests = payload["tests"]
    if not isinstance(tests, list) or not 1 <= len(tests) <= 64:
        raise BenchError("tests must contain 1..64 named test profiles")
    normalized_tests = []
    test_ids = set()
    for test in tests:
        if not isinstance(test, dict) or set(test) != {"id", "max_duration_seconds"}:
            raise BenchError("each test must contain id and max_duration_seconds only")
        test_id = test["id"]
        if not isinstance(test_id, str) or not _IDENTIFIER.fullmatch(test_id) or test_id in test_ids:
            raise BenchError("test IDs must be unique lowercase identifiers")
        test_ids.add(test_id)
        duration = test["max_duration_seconds"]
        if isinstance(duration, bool) or not isinstance(duration, int) or not 1 <= duration <= 3600:
            raise BenchError(f"{test_id}: max_duration_seconds must be 1..3600")
        normalized_tests.append({"id": test_id, "max_duration_seconds": duration})

    return {
        "schema": SCHEMA,
        "board_id": board_id,
        "fixture_slots": list(fixture_slots),
        "serial_ports": list(serial_ports),
        "max_telemetry_age_seconds": freshness,
        "rails": normalized_rails,
        "buses": normalized_buses,
        "accelerators": normalized_accelerators,
        "probes": normalized_probes,
        "tests": normalized_tests,
    }


def load_bench_profile(path: str | Path) -> dict[str, Any]:
    target = Path(path).expanduser()
    if target.is_symlink() or not target.is_file() or target.stat().st_size > MAX_PROFILE_BYTES:
        raise BenchError("bench profile must be a regular file no larger than 1 MiB")
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BenchError(f"cannot read bench profile: {error}") from error
    return validate_bench_profile(payload)


class BenchController:
    def __init__(
        self,
        profile: dict[str, Any],
        adapter: BenchAdapter | None = None,
        *,
        clock=time.time,
        audit_log=None,
    ) -> None:
        self.profile = validate_bench_profile(profile)
        self.adapter = adapter
        self.clock = clock
        self.audit_log = audit_log
        self.state = "disconnected"
        self.session_id: str | None = None
        self.fixture_slot: str | None = None

    def _audit(self, event: str, details: dict[str, Any]) -> None:
        if self.audit_log is not None:
            self.audit_log.append(event, details)

    def _disable_and_fault(self, message: str) -> None:
        disable_error = None
        if self.adapter is not None:
            try:
                self.adapter.emergency_disable()
            except Exception as error:
                disable_error = str(error)
        self.state = "fault"
        self._audit("bench.fault", {
            "board_id": self.profile["board_id"],
            "reason": message[:512],
            "emergency_disable_error": disable_error,
        })

    def connect(self) -> dict[str, Any]:
        if self.adapter is None or not self.adapter.is_connected():
            self.state = "disconnected"
            raise BenchError("no native bench adapter is connected; hardware access remains disabled")
        self.state = "discovering"
        try:
            device = self.adapter.discover()
            if not isinstance(device, dict) or device.get("board_id") != self.profile["board_id"]:
                raise BenchError("connected board does not match the selected hardware profile")
            self.state = "safe-idle"
            self._audit("bench.connected", {"board_id": self.profile["board_id"]})
            return self.status()
        except Exception as error:
            self._disable_and_fault(str(error))
            if isinstance(error, BenchError):
                raise
            raise BenchError(f"bench discovery failed: {error}") from error

    def _read_telemetry(self) -> dict[str, Any]:
        if self.adapter is None or not self.adapter.is_connected():
            raise BenchError("bench adapter disconnected")
        sample = self.adapter.read_telemetry()
        if not isinstance(sample, dict) or not isinstance(sample.get("rails"), dict):
            raise BenchError("telemetry payload is malformed")
        captured = _number(sample.get("captured_at"), "telemetry.captured_at", minimum=0, maximum=1e12)
        age = self.clock() - captured
        if age < -1 or age > self.profile["max_telemetry_age_seconds"]:
            raise BenchError("telemetry is stale or timestamped in the future")
        for rail in self.profile["rails"]:
            reading = sample["rails"].get(rail["id"])
            if not isinstance(reading, dict):
                raise BenchError(f"telemetry is missing rail {rail['id']}")
            voltage = _number(reading.get("voltage_v"), rail["id"] + ".voltage_v", minimum=0, maximum=1000)
            current = _number(reading.get("current_a"), rail["id"] + ".current_a", minimum=0, maximum=10000)
            temperature = _number(reading.get("temperature_c"), rail["id"] + ".temperature_c", minimum=-100, maximum=300)
            enabled = reading.get("enabled")
            if not isinstance(enabled, bool):
                raise BenchError(f"{rail['id']}: rail power state is missing or invalid")
            if enabled and not rail["min_voltage_v"] <= voltage <= rail["max_voltage_v"]:
                raise BenchError(f"{rail['id']}: voltage is outside the configured safe range")
            if not enabled and (voltage > 0.5 or current > 0.1):
                raise BenchError(f"{rail['id']}: disabled rail still reports voltage or current")
            if current > rail["max_current_a"]:
                raise BenchError(f"{rail['id']}: current exceeds the configured limit")
            if temperature > rail["max_temperature_c"]:
                raise BenchError(f"{rail['id']}: temperature exceeds the configured limit")

        bus_samples = sample.get("buses", {})
        if not isinstance(bus_samples, dict):
            raise BenchError("bus telemetry section is malformed")
        for bus in self.profile["buses"]:
            reading = bus_samples.get(bus["id"])
            if reading is None:
                if bus["must_be_present"]:
                    raise BenchError(f"{bus['id']}: required bus telemetry is missing")
                continue
            if not isinstance(reading, dict):
                raise BenchError(f"{bus['id']}: bus telemetry record is malformed")
            if reading.get("status") != "ok":
                if bus["must_be_present"]:
                    raise BenchError(f"{bus['id']}: bus status is not healthy")
                continue
            width = reading.get("link_width")
            if isinstance(width, bool) or not isinstance(width, int) or not 1 <= width <= bus["max_link_width"]:
                raise BenchError(f"{bus['id']}: negotiated bus link width exceeds the profile")
            speed = _number(
                reading.get("link_speed_gbps"), bus["id"] + ".link_speed_gbps",
                minimum=0.001, maximum=256,
            )
            if speed > bus["max_link_speed_gbps"]:
                raise BenchError(f"{bus['id']}: negotiated bus speed exceeds the profile")

        accelerator_samples = sample.get("accelerators", {})
        if not isinstance(accelerator_samples, dict):
            raise BenchError("accelerator telemetry section is malformed")
        for accelerator in self.profile["accelerators"]:
            reading = accelerator_samples.get(accelerator["id"])
            if reading is None or (isinstance(reading, dict) and reading.get("present") is False):
                if accelerator["must_be_present"]:
                    raise BenchError(f"{accelerator['id']}: required accelerator is not present")
                continue
            if not isinstance(reading, dict) or reading.get("present") is not True:
                raise BenchError(f"{accelerator['id']}: accelerator presence state is invalid")
            temperature = _number(
                reading.get("temperature_c"), accelerator["id"] + ".temperature_c",
                minimum=-100, maximum=300,
            )
            utilization = _number(
                reading.get("utilization_percent"), accelerator["id"] + ".utilization_percent",
                minimum=0, maximum=100,
            )
            if temperature > accelerator["max_temperature_c"]:
                raise BenchError(f"{accelerator['id']}: accelerator temperature exceeds profile limit")
            if utilization > accelerator["max_utilization_percent"]:
                raise BenchError(f"{accelerator['id']}: accelerator utilization exceeds profile limit")

        probe_samples = sample.get("probes", {})
        if not isinstance(probe_samples, dict):
            raise BenchError("probe telemetry section is malformed")
        for probe in self.profile["probes"]:
            reading = probe_samples.get(probe["id"])
            if reading is None:
                if probe["must_be_present"]:
                    raise BenchError(f"{probe['id']}: required probe reading is missing")
                continue
            if not isinstance(reading, dict):
                raise BenchError(f"{probe['id']}: probe reading is malformed")
            value = _number(reading.get("value"), probe["id"] + ".value", minimum=-1e9, maximum=1e9)
            probe_captured = _number(
                reading.get("captured_at"), probe["id"] + ".captured_at",
                minimum=0, maximum=1e12,
            )
            probe_age = self.clock() - probe_captured
            if probe_age < -1 or probe_age > probe["max_age_seconds"]:
                raise BenchError(f"{probe['id']}: probe reading is stale or timestamped in the future")
            if not probe["min_value"] <= value <= probe["max_value"]:
                raise BenchError(f"{probe['id']}: probe reading is outside the configured profile range")
        return sample

    def set_rail_power(
        self,
        rail_id: str,
        *,
        enabled: bool,
        voltage_v: float | None = None,
        current_limit_a: float | None = None,
    ) -> dict[str, Any]:
        """Set one named power rail using board-profile-limited setpoints."""
        if self.state not in {"safe-idle", "armed"}:
            raise BenchError("rail power can only be changed while the bench is safe-idle or armed")
        if self.adapter is None or not self.adapter.is_connected():
            raise BenchError("a connected native power-control adapter is required")
        if not isinstance(enabled, bool):
            raise BenchError("enabled must be a boolean")

        rail = next((item for item in self.profile["rails"] if item["id"] == rail_id), None)
        if rail is None:
            raise BenchError(f"power rail {rail_id} is not allowed by the board profile")

        if enabled:
            voltage = _number(
                voltage_v, rail_id + ".voltage_v",
                minimum=rail["min_voltage_v"], maximum=rail["max_voltage_v"],
            )
            current_limit = _number(
                current_limit_a, rail_id + ".current_limit_a",
                minimum=0.001, maximum=rail["max_current_a"],
            )
            try:
                self._read_telemetry()
                self.adapter.set_rail_power(rail_id, True, voltage, current_limit)
                sample = self._read_telemetry()
                reading = sample["rails"][rail_id]
                if reading.get("enabled") is not True:
                    raise BenchError(f"{rail_id}: adapter did not confirm that the rail is enabled")
                measured_voltage = float(reading["voltage_v"])
                measured_current = float(reading["current_a"])
                if not rail["min_voltage_v"] <= measured_voltage <= rail["max_voltage_v"]:
                    raise BenchError(f"{rail_id}: measured voltage is outside the configured range")
                if measured_current > current_limit:
                    raise BenchError(f"{rail_id}: measured current exceeds the requested current limit")
            except Exception as error:
                self._disable_and_fault(str(error))
                if isinstance(error, BenchError):
                    raise
                raise BenchError(f"{rail_id}: power enable failed: {error}") from error
        else:
            try:
                self.adapter.set_rail_power(rail_id, False, None, None)
                sample = self._read_telemetry()
                reading = sample["rails"][rail_id]
                if reading.get("enabled") is not False:
                    raise BenchError(f"{rail_id}: adapter did not confirm that the rail is disabled")
            except Exception as error:
                self._disable_and_fault(str(error))
                if isinstance(error, BenchError):
                    raise
                raise BenchError(f"{rail_id}: power disable failed: {error}") from error
            voltage = None
            current_limit = None

        self._audit("bench.power-rail-changed", {
            "board_id": self.profile["board_id"],
            "rail_id": rail_id,
            "enabled": enabled,
            "voltage_v": voltage if enabled else None,
            "current_limit_a": current_limit if enabled else None,
        })
        return {
            "schema": "duckos.bench-power-command.v1",
            "board_id": self.profile["board_id"],
            "rail_id": rail_id,
            "enabled": enabled,
            "voltage_v": voltage if enabled else None,
            "current_limit_a": current_limit if enabled else None,
            "hardware_command_sent": True,
            "hardware_state_confirmed": True,
        }

    def arm(self) -> dict[str, Any]:
        if self.state != "safe-idle":
            raise BenchError("bench must be connected and in safe-idle before arming")
        try:
            self._read_telemetry()
        except Exception as error:
            self._disable_and_fault(str(error))
            if isinstance(error, BenchError):
                raise
            raise BenchError(f"cannot arm bench: {error}") from error
        self.state = "armed"
        self._audit("bench.armed", {"board_id": self.profile["board_id"]})
        return self.status()

    def start_test(self, test_id: str, *, duration_seconds: int, fixture_slot: str) -> dict[str, Any]:
        if self.state != "armed" or self.adapter is None:
            raise BenchError("bench must be armed before starting a test")
        test = next((item for item in self.profile["tests"] if item["id"] == test_id), None)
        if test is None:
            raise BenchError(f"test {test_id} is not allowed by the hardware profile")
        if isinstance(duration_seconds, bool) or not isinstance(duration_seconds, int):
            raise BenchError("duration_seconds must be an integer")
        if not 1 <= duration_seconds <= test["max_duration_seconds"]:
            raise BenchError(f"duration_seconds must be between 1 and {test['max_duration_seconds']}")
        if fixture_slot not in self.profile["fixture_slots"]:
            raise BenchError("fixture slot is not enabled in the hardware profile")
        try:
            self._read_telemetry()
            self.session_id = __import__("uuid").uuid4().hex
            self.fixture_slot = fixture_slot
            self.adapter.start_test(test_id, fixture_slot, duration_seconds)
            self.state = "running"
            self._audit("bench.test-started", {
                "board_id": self.profile["board_id"],
                "test_id": test_id,
                "fixture_slot": fixture_slot,
                "session_id": self.session_id,
                "duration_seconds": duration_seconds,
            })
            return self.status()
        except Exception as error:
            self._disable_and_fault(str(error))
            if isinstance(error, BenchError):
                raise
            raise BenchError(f"bench test could not start: {error}") from error

    def stop_test(self) -> dict[str, Any]:
        if self.state != "running" or self.adapter is None:
            raise BenchError("there is no running bench test")
        try:
            self.adapter.stop_test()
            self.state = "cooling"
            self._audit("bench.test-stopped", {
                "board_id": self.profile["board_id"],
                "fixture_slot": self.fixture_slot,
                "session_id": self.session_id,
            })
            return self.status()
        except Exception as error:
            self._disable_and_fault(str(error))
            raise BenchError(f"bench test stop failed: {error}") from error

    def finish_cooling(self) -> dict[str, Any]:
        if self.state != "cooling":
            raise BenchError("bench is not in the cooling state")
        try:
            sample = self._read_telemetry()
        except Exception as error:
            self._disable_and_fault(str(error))
            if isinstance(error, BenchError):
                raise
            raise BenchError(f"cooling telemetry failed: {error}") from error

        for rail in self.profile["rails"]:
            temperature = float(sample["rails"][rail["id"]]["temperature_c"])
            if temperature > rail["cooldown_temperature_c"]:
                raise BenchError(f"{rail['id']}: cooling threshold has not been reached")
        self.state = "safe-idle"
        self.session_id = None
        self.fixture_slot = None
        self._audit("bench.cooling-complete", {"board_id": self.profile["board_id"]})
        return self.status()

    def emergency_shutdown(self, reason: str = "operator-request") -> dict[str, Any]:
        self._disable_and_fault(reason)
        return self.status()

    def reset_fault(self) -> dict[str, Any]:
        if self.state != "fault":
            raise BenchError("bench is not in fault state")
        if self.adapter is None or not self.adapter.is_connected():
            raise BenchError("a connected adapter is required to reset a bench fault")
        try:
            device = self.adapter.discover()
            if not isinstance(device, dict) or device.get("board_id") != self.profile["board_id"]:
                raise BenchError("connected board does not match the selected hardware profile")
            self._read_telemetry()
        except Exception as error:
            self._disable_and_fault(str(error))
            if isinstance(error, BenchError):
                raise
            raise BenchError(f"bench fault cannot be reset: {error}") from error
        self.state = "safe-idle"
        self._audit("bench.fault-reset", {"board_id": self.profile["board_id"]})
        return self.status()

    def status(self) -> dict[str, Any]:
        connected = bool(self.adapter and self.adapter.is_connected())
        return {
            "schema": "duckos.bench-status.v1",
            "board_id": self.profile["board_id"],
            "state": self.state,
            "hardware_connected": connected,
            "fixture_slots": list(self.profile["fixture_slots"]),
            "serial_ports": list(self.profile["serial_ports"]),
            "bus_ids": [item["id"] for item in self.profile["buses"]],
            "accelerators": [item["id"] for item in self.profile["accelerators"]],
            "probe_ids": [item["id"] for item in self.profile["probes"]],
            "session_id": self.session_id,
            "fixture_slot": self.fixture_slot,
            "register_write_api_exposed": False,
            "power_controller_backend": "adapter" if self.adapter is not None else "unavailable",
        }
