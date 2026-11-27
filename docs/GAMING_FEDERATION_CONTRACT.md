# Shared DAKOS gaming session contract

**Project author/developer:** Ivan-VHS

DAKOS is the coordinator for the 66-rule gaming policy. The repository adapters exchange narrow, versioned JSON records rather than importing each other's runtime code.

## Provider evidence

- OPlague emits `oplague.dakos-gaming-evidence.v1`. Its `providers` object is accepted directly by `assess_capability_document`.
- Pytyliki emits `dakos.gaming-provider-evidence.v1` from measured Watch counters. It may declare only `cpu_telemetry`, `memory_pressure`, `swap_metrics` and measured `frame_time` availability.
- Missing providers remain unavailable. Telemetry does not imply a write/control capability.

Example:

```python
from dakos.gaming import assess_capability_document

assessment = assess_capability_document(oplage_evidence)
```

## Session profiles for Reaper

`build_session_profile()` returns `dakos.gaming-session-profile.v1`, the input contract consumed by Reaper's `build_gaming_task_plan()`. The record carries a game ID, engine, bounded worker count and whether audio/multithreading are enabled. Reaper returns role hints; neither side changes host scheduling.

## Specialized workload adapters

- Reaper: `reaper.gaming-task-plan.v1`, advisory roles for main/render/audio/worker/background tasks.
- VentuSample: bounded audio buffer recommendation based on sample rate, channel count, latency target and backend buffer size. It reports the measured duration and does not open a device or change scheduling.

## Safety guarantees

All cross-repository payloads are explicit about schema and scope. Each adapter rejects malformed input and reports whether it executed or changed host settings. DAKOS does not activate policy from a process-name match alone; window and graphics-context confirmation remain required.
