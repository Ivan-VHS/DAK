# Reaper native Dak Shell bridge contract

**Status:** Reaper policy contract implemented; DABI64 transport, native client adapter and kernel enforcement remain pending.

This contract is the boundary between a native Dak Shell client and the Reaper desktop policy core. It is deliberately separate from the Qt host window lifecycle in Mora and from the kernel-owned Dak desktop that will exist after the process, IPC and display services are implemented.

## Intended topology

```text
Native Dak Shell client
        |
        | bounded DABI64 request (future transport)
        v
Dak desktop IPC endpoint (not implemented)
        |
        | authenticated sender + capability evidence
        v
Reaper native_bridge.rpr
        |
        +--> window_manager.rpr
        +--> session.rpr / workspace.rpr
        +--> notifications.rpr
        +--> desktop_sandbox.rpr / taskbar.rpr
        +--> theme.rpr
        |
        v
Native transaction coordinator (not implemented)
        |
        +--> window service / compositor / input / launcher
```

The Qt 6 Mora application remains the host-native reference adapter. It is not loaded by the Dak kernel, and this Reaper contract does not make it a kernel shell.

## Event envelope v1

`dakos/ui/native_bridge.rpr` defines a bounded eight-field record:

| Index | Field | Constraint |
|---:|---|---|
| 0 | `version` | Exactly `1` |
| 1 | `sequence` | Positive monotonic sequence |
| 2 | `request_id` | Positive correlation identifier |
| 3 | `sender_pid` | Positive authenticated process identifier |
| 4 | `workspace_id` | 0–15 |
| 5 | `event_name` | Explicit allowlist only |
| 6 | `payload_bytes` | 0–65,536 bytes |
| 7 | `timestamp_us` | Positive monotonic timestamp in microseconds |

Allowed operations:

- `window.open`, `window.close`, `window.focus`, `window.resize`
- `workspace.switch`
- `notification.post`, `system.notification.post`
- `launcher.resolve`
- `theme.resolve`
- `settings.validate`

The current module validates the envelope, rejects unknown operations and oversized payloads, enforces monotonic sequence progression, checks a named capability and returns the relevant Reaper policy route. A regular client cannot emit `system.notification.post`; that route additionally requires authenticated system-origin evidence.

## Capability mapping

| Event | Required capability | Reaper destination |
|---|---|---|
| Window lifecycle and geometry | `ui.window.manage` | `window_manager.rpr` |
| Workspace switch | `ui.workspace.switch` | `session.rpr` |
| App notification | `ui.notification.post` | `notifications.rpr` |
| System notification | `ui.notification.system` plus system-origin evidence | `notifications.rpr` |
| Launcher resolve | `ui.app.resolve` | `desktop_sandbox.rpr` and `taskbar.rpr` |
| Semantic theme lookup | `ui.theme.read` | `theme.rpr` |
| Quick-settings schema validation | `ui.settings.validate` | `config.rpr` |

The module accepts authority facts as inputs; it does not authenticate processes or mint capabilities. The future IPC endpoint must derive PID, system identity and grant handles from the kernel's process/capability broker, never from user-supplied payload fields.

## Verification in Reaper

`contract_tests.rpr` covers valid v1 events, required-capability rejection, monotonic sequencing, system-notification spoof rejection, oversized payload rejection and unknown operation rejection. The Reaper contract workflow also syntax-checks each `.rpr` module.

These are deterministic policy tests. They do not prove ABI serialization, process isolation, syscall entry, IPC delivery, compositor integration or kernel authorization.

## Next native implementation gates

1. Specify the fixed-width DABI64 wire representation, endianness, alignment, maximum frame, error envelope and version negotiation.
2. Implement a kernel-owned IPC endpoint with sender identity, capability handles, quotas, cancellation and process-exit cleanup.
3. Build the freestanding/native Reaper runtime needed to evaluate policy modules without Python or browser execution.
4. Add the native transaction coordinator that applies a policy decision atomically and publishes events only after commit.
5. Connect process-backed window/session services, compositor, display/input, persistence and accessibility.
6. Add headless integration tests, malformed-message fuzzing, negative capability tests and QEMU session boot evidence.

Until these gates pass, the desktop bridge remains a policy contract and the Stage 1 kernel still halts before a userspace desktop session.
