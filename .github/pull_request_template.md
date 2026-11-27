This PR describes one coherent change to DAK and the system, desktop or developer-facing behavior it affects.

## What changed
Explain the user-visible or system-level result. Name the affected service, subsystem, application, ABI or workflow.

## Why
Describe the concrete problem and why this change belongs in DAK.

## Implementation
- [ ] Reaper-native code and language boundaries are respected where applicable.
- [ ] Kernel, process, memory, storage, service and device interfaces have explicit contracts.
- [ ] Privileged operations, host integration and external effects are opt-in and bounded.
- [ ] Configuration, manifests and migrations are validated and backward-compatible where required.
- [ ] Planned capabilities are clearly separated from implemented behavior.

## Verification
List exact native build, CTest, Reaper conformance, UI and CI commands that were run. State what is pending; do not claim a bootable OS, driver, syscall or runtime capability without target evidence.

## Compatibility and safety
Explain boot/runtime targets, ABI changes, permissions, resource limits, persistence and unsupported hardware or host behavior.

## Dependencies
Link related DAK and specialist-repository PRs. State the source commit and required merge order for cross-repository work.
