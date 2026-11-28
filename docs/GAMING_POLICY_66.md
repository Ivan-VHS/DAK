# DuckOS Gaming Performance Policy — 66 rules

**Project author/developer:** Ivan-VHS

DuckOS owns the canonical versioned catalog `duckos.gaming-rule-catalog.v1` and the session-policy boundary. The catalog preserves all 66 requirements in six domains: game detection, CPU scheduling, memory, graphics, I/O and power/reliability.

## What this implementation does

- Validates a complete, ordered set of 66 unique rule identifiers.
- Builds a per-rule capability assessment from declared providers and their evidence.
- Keeps unavailable or missing providers unavailable; missing telemetry is never fabricated.
- Models the gaming-session lifecycle as explicit, idempotent transitions: idle → starting → active/background → restoring → idle.
- Returns declarative action plans for a trusted native executor instead of invoking shell commands or silently changing system settings.

## Integration boundary

The policy engine does not yet perform kernel context switches, CPU affinity changes, interrupt routing, clock/voltage tuning, fan-curve writes, graphics-driver recovery, network queue changes or process suspension. Those operations require platform-specific providers, permission checks, measurements and tested rollback. The current transition actions are plans only: every result reports `execution_performed=false` and `system_settings_changed=false`.

OPlague supplies the reversible Windows power-plan and NVIDIA telemetry adapter. Pytyliki supplies read-only host measurements. Reaper can validate declarative scheduling plans. VentuSample supplies a bounded audio-workload profile. DuckOS remains the orchestrator and source of the 66-rule catalog.

## API

```python
from duckos.gaming import assess_capabilities, load_rule_catalog, plan_session_transition

catalog = load_rule_catalog()
assessment = assess_capabilities({
    "process_catalog": {"available": True, "provider": "duckos-process-source"},
})
transition = plan_session_transition(
    "idle", "game_detected",
    profile_id="sample-game",
    process_identity="sample.exe",
)
```

Run focused tests with:

```sh
python -m unittest tests.test_gaming_policy -v
```
