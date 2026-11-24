"""Offline security analysis service and versioned report builder."""
from __future__ import annotations

from typing import Any, Mapping

from .engine import SecurityEngine
from .events import EVENT_SCHEMA, SecurityEvent
from .forensics import FlightRecorder

DOCUMENT_SCHEMA = "duckos.security-events.v1"
MAX_EVENTS_PER_DOCUMENT = 4096


def analyze_event_document(document: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(document, Mapping) or document.get("schema") != DOCUMENT_SCHEMA:
        raise ValueError(f"input must use schema {DOCUMENT_SCHEMA}")
    records = document.get("events")
    if not isinstance(records, list) or len(records) > MAX_EVENTS_PER_DOCUMENT:
        raise ValueError(f"events must be an array of at most {MAX_EVENTS_PER_DOCUMENT} records")

    engine = SecurityEngine(capacity=max(16, min(100_000, len(records) + 16)))
    recorder = FlightRecorder(capacity=max(16, min(100_000, len(records) + 16)))
    evaluations: list[dict[str, Any]] = []
    for raw in records:
        event = SecurityEvent.from_mapping(raw)
        evaluation = engine.ingest(event).to_dict()
        recorder.record(event.to_dict(), evaluation)
        evaluations.append(evaluation)

    high_risk = [item for item in evaluations if item["risk_score"] >= 35]
    report = recorder.export()
    return {
        "schema": "duckos.security-analysis.v1",
        "mode": "offline_event_replay",
        "collection": "caller_supplied_events",
        "enforcement": "advisory_only",
        "event_schema": EVENT_SCHEMA,
        "events_analyzed": len(evaluations),
        "incidents_detected": len(high_risk),
        "highest_risk_score": max((item["risk_score"] for item in evaluations), default=0),
        "evaluations": evaluations,
        "forensic_context": report,
        "limitations": [
            "No live kernel, filesystem, process, memory, network or browser sensor is connected by this service.",
            "Recommendations are advisory and do not block, isolate, restore or terminate host resources.",
            "A sensor-provided signature or reputation field is evidence input, not cryptographic verification performed here.",
        ],
    }


def security_status() -> dict[str, Any]:
    return {
        "schema": "duckos.security-status.v1",
        "product": "DuckOS Predictive Security",
        "status": "user_space_policy_engine_available",
        "event_analysis": "available",
        "causal_correlation": "available_for_supplied_events",
        "flight_recorder": "bounded_in_memory",
        "file_snapshots": "explicit_managed_root_api",
        "mesh": "hmac_envelope_api_no_network_transport",
        "integrity": "sha256_manifest_verification",
        "live_sensor_collection": "not_connected",
        "kernel_enforcement": "not_implemented",
        "driver_isolation": "not_implemented",
        "hardware_memory_vault": "not_implemented",
        "browser_token_protection": "not_connected",
        "sandbox_execution": "not_implemented",
        "automatic_repair": "not_implemented",
    }
