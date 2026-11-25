# DuckOS DABI64 Desktop Host v1

**Status:** host-side IPC framing and capability-broker core implemented; kernel transport, process isolation and window/display services remain separate implementation gates.

## Boundary

DuckOS owns privileged transport and enforcement. Reaper supplies deterministic policy decisions and the capability-gated System Runtime operation catalogue. This library is a C11 protocol/broker core that a trusted kernel or native desktop host can embed. It does not create kernel tasks, map user pages, open a device, render a frame or start an external process.

The C library is independent of Qt and browser code. Mora can become a client of the same wire contract after the native host is present; its current Qt application remains a host-OS desktop app.

## DABI64 Desktop IPC v1 wire header

All fields are little-endian and fixed-width. Untrusted bytes must never be cast directly to a C structure.

| Offset | Width | Field |
|---:|---:|---|
| 0 | 4 | Magic DIPC |
| 4 | 2 | Major version (1) |
| 6 | 2 | Minor version (0) |
| 8 | 2 | Header size (48) |
| 10 | 2 | Flags (only ACK_REQUIRED is defined) |
| 12 | 4 | Message type |
| 16 | 4 | Payload length (maximum 64 KiB) |
| 20 | 8 | Per-connection sequence |
| 28 | 8 | Authenticated session ID |
| 36 | 4 | Object ID |
| 40 | 4 | Object generation |
| 44 | 4 | Reserved; must be zero |

The receiver supplies expected sequence and session ID from authenticated connection state. The parser rejects replays, gaps, stale sessions, unknown versions, unknown flags, nonzero reserved bits, malformed object generations and type-specific payload-size violations. It does not allocate memory and returns a borrowed payload view into caller input.

Window/surface object IDs are allocated by the host, never selected by an untrusted client. Object messages carry a generation so a stale handle cannot alias a later object that reuses an ID.

## Bounded event queue

The event queue is a fixed 64-entry ring with 256-byte event payloads, monotonic sequence validation and explicit backpressure. A failed push leaves queue state unchanged. A pop with an undersized destination does not consume the event. There is no unbounded heap growth.

## Capability broker

The broker binds grants to the transport-authenticated tuple of process ID, process generation and session ID. A transport adapter supplies the peer lookup callback using a trusted kernel IPC endpoint or operating-system peer credentials. The protocol payload never supplies a PID, role, trust bit or authority mask. Only an authenticated system peer with administrative desktop authority can issue or revoke grants.

Each grant has narrow rights, optional exact resource ID/generation scope, bounded expiry (maximum 24 hours), process-generation/session binding and explicit revocation. Expired slots are reclaimed during the next authorized grant issue, so abandoned leases cannot permanently exhaust the fixed grant table. The broker fails closed for unknown connections, stale process generations, cross-session use, expired grants, insufficient rights and resource mismatches. A token ID is not a cryptographic bearer credential; authorization always rechecks authenticated connection identity.

The broker is single-dispatch-thread state; the containing service must serialize mutations. The identity callback is part of the trusted computing base. Passing a fake identity provider or exposing the broker issuer API to an untrusted client invalidates the security boundary.

## Verification

- duckos-desktop-ipc: valid frame decode, exact sequence/session checks, malformed header rejection, object-generation validation, payload shape checks, event queue order and backpressure.
- duckos-desktop-capability-broker: system-only issue/revoke, least-rights decisions, process-generation binding, session binding, exact resource scope, expiry and revocation.

## Remaining native integration gates

1. Wire transport into a process-owned kernel endpoint after DABI64 process/handle ABI exists.
2. Implement a kernel-authoritative peer identity provider and store grants in the trusted broker service; do not accept caller-supplied identity fields.
3. Connect Reaper desktop System Runtime operations to this host using versioned typed payloads and policy decisions.
4. Implement transactional window/surface state and a native software compositor; add display/input providers behind narrow driver interfaces.
5. Add user-mode process isolation before exposing input, notification, surface or session capabilities to applications.

This PR is the message and grant core only. It is not claimed to be kernel-enforced until identity provider, IPC endpoint and process boundary are implemented and target-tested.
