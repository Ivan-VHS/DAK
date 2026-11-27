# Reaper-driven DAK Shell implementation roadmap

**Target:** a desktop session started and owned by DAKOS, with Reaper as the native policy/UI language.
**Current baseline:** experimental x86_64 Stage 1 kernel; host-native Qt 6 Mora adapter; Reaper desktop policy and event-envelope contracts.
**Release rule:** a Figma frame, host-native window or policy-only contract is not proof of a kernel-owned desktop feature.

## Current state

| Layer | Evidence today | Remaining boundary |
|---|---|---|
| Host-native shell | Qt 6 Widgets Mora with native host windows, local catalogue, window overview, notification center, quick settings and launcher changes under PRs #159/#166 | Runs as a host application; host OS owns the windows |
| Reaper policy | `window_manager.rpr`, `workspace.rpr`, `session.rpr`, `taskbar.rpr`, `notifications.rpr`, `desktop_sandbox.rpr`, `theme.rpr` | Pure deterministic decisions, not privileged execution |
| Native bridge contract | `native_bridge.rpr` v1 event envelope and Reaper contract assertions | No DABI64 serializer, IPC endpoint, Reaper-native runtime or kernel transaction |
| Kernel boot | x86_64 Stage 1 handoff and early memory evidence | No userspace process/session, user syscall path, display/input services or desktop launch |

## Ordered implementation phases

### D8.2 — Freestanding Reaper runtime and DABI64 bridge

**Deliverables**
- A native/freestanding Reaper runtime that can load and evaluate the required compiled policy modules without Python, browser JavaScript or network access.
- A fixed-width DABI64 wire representation for event v1: version, size, operation, sequence, request ID, sender identity, capability handle and bounded payload.
- Explicit alignment, endianness, maximum sizes, version negotiation, error envelope, timeout, cancellation and process-exit semantics.
- A kernel-owned IPC endpoint that derives sender PID and capabilities from trusted process state.
- A native adapter that marshals the host-neutral event envelope and calls Reaper policy before asking a service to commit an operation.

**Acceptance gates**
- ABI golden vectors and encode/decode round trips.
- Malformed, oversized, truncated, stale-sequence and unknown-version negative tests.
- Capability spoofing, cross-process identity and unauthorized system-notification tests.
- Tree-walk/VM and native-runtime policy parity for the same golden cases.
- No Python runtime dependency in the shipped DAKOS session.

### D8.3 — Process-backed desktop session and window service

**Deliverables**
- Session supervisor and user-profile bootstrap.
- Window service with kernel-issued window IDs, owner PID, workspace, geometry, z-order, focus and lifecycle state.
- Transactional focus, resize, close and workspace operations using Reaper policy decisions.
- Bounded event queue, crash cleanup, restart behavior and local session persistence.
- Capability broker for app launch, window management, notifications, files and device access.

**Acceptance gates**
- Two or more isolated user processes can create and own windows.
- A process cannot focus, close, resize or enumerate another process's windows without a grant.
- Modal and reserved system-window invariants hold under adversarial event ordering.
- Session restore rejects malformed snapshots and cross-user restore attempts.
- Process exit reclaims window descriptors and notification ownership.

### D8.4 — Display, input and compositor

**Deliverables**
- Native display discovery and a software framebuffer/compositor fallback.
- Input service with keyboard, pointer and touch event routing.
- Damage tracking, frame pacing, clipping, scaling, DPI and multiple-display migration.
- GPU backend behind a stable renderer interface, with software fallback and device-loss recovery.
- Font shaping, text input, accessibility tree and reduced-motion integration.

**Acceptance gates**
- QEMU BIOS/UEFI screenshots from a kernel-started desktop process.
- Deterministic headless tests for damage, clipping, resize and focus.
- Input ownership and capability-negative tests.
- Frame-time P50/P95/P99 and idle CPU/memory measurements on named hardware.
- GPU failure returns to software rendering without losing the session.

### D8.5 — Reaper-driven DAK Shell

**Deliverables**
- Reaper UI/runtime as the source of shell composition and policy, not a Qt or browser app embedded in the kernel.
- Native shell surfaces: workspace overview, taskbar/dock, launcher, notification center, quick settings and system settings.
- Application lifecycle connected to the native package catalogue, signature verification, sandbox and capability broker.
- Local-first profiles and settings with atomic writes, migration and crash-safe restore.
- Localization, keyboard navigation, accessibility semantics and reduced-motion behavior across the whole shell.

**Acceptance gates**
- DAKOS boots directly into a user-owned Reaper desktop session.
- Shell panels communicate only through versioned DABI64/IPC contracts.
- No browser engine, remote CDN, hidden network dependency or host-window dependency.
- App launch and device actions are denied without a broker-issued capability.
- Full end-to-end tests run from kernel boot to process-backed UI interactions.

## Integration order

1. Merge the Qt host-native foundation (#159) after its required checks pass.
2. Rebase and merge the Figma-derived native panels (#166) on the updated `main`.
3. Merge the Reaper policy and bridge contracts (#161), resolving the shared architecture/status documentation against the merged Mora state.
4. Start a separate D8.2 implementation PR for the native Reaper runtime and DABI64/IPC endpoint.
5. Only then migrate the shell from the host adapter to the kernel-owned DAKOS desktop session.

## Non-goals for the transition

- Do not treat Qt host windows as DAKOS kernel windows.
- Do not route privileged operations through browser JavaScript or local preference files.
- Do not execute app-manifest command strings from the launcher.
- Do not claim a compositor, scheduler, process model, VFS or device control merely because its policy contract exists.
- Do not ship a Python test/runtime dependency as the native DAKOS Reaper execution path.
