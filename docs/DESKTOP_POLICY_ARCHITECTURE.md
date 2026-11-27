# DAKOS Reaper-first desktop policy architecture

**Status:** policy core implementation; native desktop execution remains a separate, incomplete milestone.

This document defines the deterministic policy boundary for a future DAKOS desktop session. It does not claim that the kernel currently starts a desktop, that Reaper contracts are enforced by a privileged runtime, or that a compositor, process broker or native app launcher is already present.

## Authority and execution model

The desktop is split into four independently testable layers:

1. **Reaper policy core (dakos/**/*.rpr)** validates descriptors and returns deterministic decisions. It owns window admission, geometry constraints, focus, z-order, workspace state, taskbar visibility, notification priority, app admission and semantic theme tokens.
2. **Native desktop services (not yet delivered)** own window surfaces, input dispatch, frame scheduling, monitor hotplug, session persistence, process lifecycle, notification delivery and capability enforcement. They must treat policy results as inputs to a transaction, not as authority supplied by an app.
3. **Compositor and display backends (not yet delivered)** own buffer lifetime, damage tracking, presentation fences, GPU submission, fallback rendering and recovery from device loss.
4. **Jora (current maturity: scaffold composer)** describes and validates component/dependency graphs. It must not install, execute or grant capabilities to a composed application until a signed package and native broker exist.

Mora now has a Qt 6 Widgets host-native adapter plus a retained browser reference preview. The host adapter uses the host OS window manager and is not the trusted DAKOS window manager; neither host UI nor browser JavaScript can grant kernel privileges. Reaper Studio is the language IDE, not the DAKOS desktop environment.

## Reaper policy modules

| Module | Responsibility | Decision boundary |
|---|---|---|
| dakos/ui/window_manager.rpr | Window records, geometry, modal focus, reserved z layers, resize policy, deterministic tile metrics and stacking-order bounds | allow-policy-only, deny-*, system-layer, user-layer, or tile metrics |
| dakos/ui/taskbar.rpr | Taskbar entry validation, hiding system processes, pinned/running visibility, grouping counts and activation routing | visible, hidden-*, focus-running-app, switch-workspace-and-focus, jora-compose-request |
| dakos/ui/session.rpr | Session descriptor, lifecycle, authorized workspace switching and restore admission | *-policy-only, deny-*, migration-required |
| dakos/ui/notifications.rpr | Bounded notification records, capability admission, anti-spoofing, reserved system priority, expiry and backpressure | admit-policy-only, deny-*, layer name, expiry boolean |
| dakos/security/desktop_sandbox.rpr | App manifest, catalog/signature/sandbox gates, capability attenuation, network broker mode and explicit permission requests | admit-policy-only or deny-* |
| dakos/ui/workspace.rpr | Context layouts, panels, layout modes, descriptor bounds and window caps | selected layout or boolean |
| dakos/ui/theme.rpr | Imperial Noir & Glass semantic tokens, yellow brand accent, green/red/blue status meanings, mode and contrast-pair allowlist | token values and boolean decisions |
| dakos/ui/native_bridge.rpr | Versioned event envelope, monotonic sequence, payload bounds, capability routing, system-notification origin gate and settings validation routing | route-window-manager-policy, route-session-policy, route-notification-policy, route-app-admission-policy, route-theme-policy, route-config-policy, or deny-* |

### Stable record shapes

All numeric identifiers and quotas are bounded before they reach native services.

- Window: [id, owner_pid, workspace_id, mode, x, y, width, height, z, visible, focusable, system].
- Taskbar entry: [app_id, owner_pid, workspace_id, pinned, running, system, window_count, attention].
- Notification: [id, owner_pid, priority, created_us, ttl_us, title, body, system].
- Session: [session_id, user_id, state, active_workspace, workspace_count, started_us, locked].
- Workspace: [id, monitor_id, layout_mode, context, focused_window_id, window_count, revision].
- App manifest: [app_id, version, signer_id, sandbox_id, install_state, memory_limit_bytes, cpu_quota_percent, network_mode, requested_capabilities].

The arrays are versioned by module path and field order for this first contract slice. A later ABI serializer must add explicit schema versioning, fixed-width encoding, endianness, maximum encoded sizes and forward-compatibility rules before records cross a process boundary.

## Security invariants

- User windows cannot enter reserved system z-order layers. Modal focus blocks unrelated user windows; system windows are handled by a separate trusted host.
- Tiling geometry is deterministic and bounded to 16 windows per workspace. Manual resize is rejected when layout ownership belongs to the tiler unless a valid override token is presented.
- System processes are never exposed as ordinary taskbar applications. Pinned-but-not-running entries request composition; they do not directly execute code.
- Notifications require an explicit capability. Apps cannot claim system origin or request system-only priority.
- App admission fails closed unless the catalog, signature and sandbox readiness checks are supplied as verified host evidence. Requested capabilities must be a subset of grants. Network access requires brokered mode.
- An explicit permission approval is not itself a grant. The native capability broker must commit a separate auditable grant.
- Themes use semantic roles. Arbitrary application colors are not accepted as replacements for system tokens. Motion can be reduced to static behavior.

## Host transaction model

A native host should apply each user action in this order:

1. Decode a bounded IPC request and authenticate the sending process.
2. Validate the request schema/version and resolve the current session/workspace.
3. Call the relevant Reaper policy function with immutable input records.
4. Check the returned decision and native capability grants.
5. Prepare resource changes without publishing partial state.
6. Commit the operation atomically; on failure, retain the old state and emit a bounded diagnostic.
7. Publish a versioned event to the compositor/shell clients only after commit.

Window movement, focus, resize, workspace switching, launcher activation and theme changes must use the same transaction boundary. Client-rendered state is never authoritative.

## Desktop service roadmap

| Stage | Deliverable | Required evidence |
|---|---|---|
| D8.1 Policy core | Reaper records, pure decisions and tree-walk/VM contract tests | contract_tests.rpr and the Reaper contract CI workflow |
| D8.2 Native host ABI | Versioned DABI64/IPC messages, event sequencing, capability handles, crash-safe ownership and cancellation | ABI conformance tests, malformed-message fuzzing, capability-negative tests |
| D8.3 Session and window services | Process-backed windows, modal focus, multi-workspace switching, persistence and hotplug migration | headless integration tests, state recovery tests, keyboard-only flow tests |
| D8.4 Compositor | Software fallback first, then GPU backend, frame pacing and damage tracking | QEMU screenshots, frame-time P50/P95/P99, device-loss and fallback tests |
| D8.5 Shell and applications | Native taskbar, app launcher, notifications, settings, accessibility and localized input | end-to-end session tests on named x86_64 targets |

## Explicitly not claimed

The policy modules do not create windows, switch CPU contexts, map pages, start processes, render pixels, access PCI/GPU devices, persist user profiles, verify cryptographic signatures, isolate an address space or enforce capabilities in the kernel. Current Jora composition is a project scaffold and returns installable: false. Current DAKOS Stage 1 boots, validates Boot Info and halts; it does not start the desktop.

These limits are release gates, not reasons to replace the Reaper policy model with browser JavaScript or to describe a visual mockup as a working operating-system desktop.


## Native shell bridge contract

The Reaper-first event envelope and capability routes are specified in [Native Desktop Bridge](NATIVE_DESKTOP_BRIDGE.md) and implemented as the policy-only module `dakos/ui/native_bridge.rpr`.

The host-native Mora adapter is the current Qt reference surface. Its events are not yet transported through DABI64/IPC and its windows are not kernel-owned. The next step is a freestanding/native Reaper runtime and authenticated IPC endpoint that evaluates the Reaper policy before a kernel transaction commits. No Python runner, browser script or host UI preference may stand in for that runtime or capability enforcement.
