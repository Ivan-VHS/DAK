# DuckOS predictive security architecture

**Status:** implemented user-space foundations plus Reaper policy contracts; native enforcement remains gated.  
**Scope:** DuckOS operating-system security services, not a detached antivirus application.

## Architecture

The security capability has four cooperating boundaries:

1. **Reaper policy plane** — deterministic risk scoring, action selection, snapshot requirements, mesh-signal acceptance, recovery authorization and workload-profile decisions.
2. **DuckOS user-space evidence plane** — strict event ingestion, bounded causal correlation, indicator clustering, explainable risk evaluations, in-memory flight recorder, explicit file snapshots, integrity verification and authenticated mesh-alert envelopes.
3. **Native sensor and enforcement plane** — future kernel/system services that collect events and enforce decisions through versioned capabilities. No native hook is claimed by the current user-space implementation.
4. **OS service lifecycle** — duckos/services/security.rpr registers the security service identity, dependencies, startup gates, health/backpressure states, bounded supervisor restart decisions and per-action capability checks. This is a lifecycle contract, not a running native daemon.
5. **Mora presentation plane** — system policy advertises the capability as partial and cannot turn an advisory recommendation into a claim of active protection.

Dependencies point inward to versioned contracts. The analyzer cannot call privileged OS operations. Sensor adapters must produce validated events; they must not pass kernel pointers, secrets, unbounded command lines or arbitrary nested payloads into the policy engine. The kernel security authorization contract consumes trust labels, explicit capability grants, evidence freshness, policy validity, approval state and authenticated snapshot metadata before allowing a privileged action. Telemetry publication and IPC reads have separate least-privilege grants; security-sensor driver descriptors additionally require a verified signer, non-revoked publisher, matching image digest and measured secure-boot state.

## Coverage of the 13 security directions

| Direction | Current DuckOS implementation | Native work still required |
|---|---|---|
| Threat epidemiology | Distinct-host indicator clustering over supplied events with bounded time windows | Global intelligence ingestion, trusted peer inventory, temporal normalization and fleet topology |
| Pre-action snapshots | Explicit bounded snapshots for caller-selected regular files under a managed root | Filesystem filter, pre-write journal, crash consistency and system-level rollback |
| Hardware memory vault | Reaper security trust/capability contracts | VBS/virtualization integration, protected memory, measured boot and platform qualification |
| Causal attack graph | Bounded process-parent/event chain and incident edge export | Kernel event IDs, durable graph store and cross-source causal joins |
| Context-aware sandbox | Risk engine recommends sandbox handling for untrusted context | Isolated process execution, filesystem/network/device namespaces and escape testing |
| Intent and entropy | Supplied entropy delta, file mutation and periodic beacon signals | Native file/network telemetry and calibrated behavioral baselines |
| LOLBins | Context-aware rules for common system tools; names alone are not treated as malicious | Signed image identity, command-line capture, parent provenance and native process callbacks |
| Self-healing | Read-only manifest verification; no repair from untrusted local data | Independently protected signed baseline, transactional repair and recovery tests |
| Session and token shield | Risk rule for sensor-reported unauthorized access to credential material | Browser/OS credential provider integration and least-privilege access telemetry |
| Adaptive resource governor | Workload hints defer deep scan while preserving collection and thresholds | Native scheduler/power/thermal integration and latency budgets |
| Mesh threat sharing | HMAC-SHA256 envelope, bounded lifetime and replay protection | Mutually authenticated transport, secure key provisioning, rotation, peer revocation and scope |
| Flight recorder | Bounded in-memory event ring, secret-key redaction and causal report | Native low-overhead event source, durable protected retention and export controls |
| Explainable verdict | Score, confidence, indicators, causal root, recommended action and advisory status | Evidence provenance, calibrated model validation and privileged decision broker |

## Kernel and telemetry integration

The kernel security contract is deny-by-default. It maps each security operation to a distinct capability and rejects unknown actions, untrusted callers, stale evidence and invalid policy state. File restore additionally requires an authenticated snapshot, verified payload and authorized target. Restore, process isolation/termination, network isolation and driver quarantine require explicit approval. The contract does not itself perform these actions; a native kernel broker must enforce it.

Security telemetry has a fixed tuple contract with a monotonic sequence, event/source/actor identifiers, object/parent references, trusted-source label and monotonic timestamp. The telemetry queue validates event kinds and source authority. IPC provides separate authorized producer and consumer paths so a sensor's publish grant cannot silently become the analysis service's read grant.

The driver ABI adds a stricter security-sensor admission policy requiring verified signature, trusted and non-revoked signer, matching image digest, target architecture, granted sensor capabilities and measured secure-boot state. These are verifier outputs accepted by the policy contract, not cryptographic checks performed by the Reaper interpreter.

## Event contract

An input batch uses duckos.security-events.v1. Each record uses duckos.security-event.v1 and includes event ID, timestamp in milliseconds, host ID, source, kind and actor ID. Optional object, parent-event, correlation and action fields support graph reconstruction. Attributes are limited to 32 scalar values with bounded keys and values. Unsupported event kinds, non-finite numbers, nested objects and oversized batches are rejected.

Supported event kinds cover process start/stop/injection, file mutation, network connect/listen/DNS, memory reads/writes, identity access, registry/service changes, integrity changes, driver-load observations, mesh alerts and sandbox results. Exact shape is defined in security-events.v1.schema.json.

Sensor adapters must explicitly classify source trust and collection scope. The analyzer treats sensor-provided reputation and signature fields as evidence, not as cryptographic proof.

## Service lifecycle and authority

The Reaper service contract declares the security service in the normal services boot phase. Startup requires dependencies, policy state and audit readiness. Queue saturation or event loss is surfaced as backpressure; missing policy or audit support yields a degraded state. Restart decisions reuse the existing finite service supervisor.

The action gate denies untrusted callers and stale or invalid evidence. Observe, snapshot creation and integrity verification have distinct capabilities. File restore, process isolation, process termination and network isolation require both their own explicit capability and explicit approval. This is only policy logic: the future native service manager and kernel capability broker must enforce the same checks at the privileged boundary.

The CLI's security status distinguishes this registered policy contract from a native service process or boot-time activation; those are not yet implemented.

## Decision semantics

The user-space engine calculates an integer score from 0 to 100, an independent confidence estimate, a risk label, evidence indicators and a recommendation. Recommendations are monitor, sandbox, restrict, isolate or block. The analyzer never executes these recommendations.

A high confidence score is not the same as high risk. A native Decision Broker must validate actor identity, capability, freshness, policy version and evidence before any enforcement action. Unknown or stale evidence should never grant authority.

## Snapshot and restore boundary

SnapshotStore operates only inside an explicitly selected existing directory. It rejects absolute paths, dot segments, symbolic links, non-regular files and files beyond the configured limit. Payloads are SHA-256 checked on restore and written by a temporary-file plus atomic-replace sequence. The snapshot store has a bounded count.

This API is useful for managed files and controlled test fixtures. It is not a filesystem minifilter, block-device journal or pre-write interception service. It cannot preserve a write that occurs before it is called, and it cannot promise a complete system rollback. Native implementation requires an OS-supported pre-operation filter, crash-safe journal, quota management, metadata policy and fault-injection tests.

## Mesh trust boundary

Mesh messages contain only indicator metadata and severity, never executable commands or automatic block instructions. HMAC authentication requires a provisioned shared key of at least 256 bits. Verification checks the signature, timestamp window, maximum lifetime, required fields and replay cache. The current code does not open sockets, distribute keys or establish a secure network. A production mesh needs mutually authenticated transport, key rotation, peer revocation and tenant/network scoping.

## Integrity and recovery boundary

The integrity service compares regular files against a caller-supplied SHA-256 manifest and reports mismatches without repair. SHA-256 proves byte equality to the supplied digest; it does not authenticate who supplied the digest. Production self-healing requires a separately protected, signed baseline, verified update channel, monotonic version policy and recovery-tested replacement transaction.

## CLI

- duckos security status
- duckos security analyze EVENTS.json [--output REPORT.json]
- duckos security snapshot create ROOT RELATIVE_PATH
- duckos security snapshot restore ROOT SNAPSHOT_ID
- duckos security integrity ROOT MANIFEST.json

The analyze command is offline replay only. The status output is the authoritative machine-readable statement of current implementation maturity.

## Native implementation gates

1. Define a stable versioned kernel-to-user event ABI with caller identity, monotonic sequence, bounded payload and loss accounting.
2. Add read-only kernel/process/filesystem/network sensors behind platform-specific adapters, retaining graceful degradation when unavailable.
3. Add a capability-enforced Decision Broker and audit log; ensure deny/contain actions are reversible and race-safe.
4. Implement the filesystem pre-operation journal and recovery transaction before claiming ransomware rollback.
5. Implement driver signature verification using a trusted key store and isolated loading; remove caller-supplied boolean signature claims from privileged paths.
6. Implement hardware-backed isolation only for supported CPU/firmware configurations, with measured boot and explicit unsupported state.
7. Implement a real OS process sandbox with filesystem, network, IPC and device capability confinement.
8. Add browser/session integration through supported browser or OS credential-provider interfaces; avoid broad process-memory scraping.
9. Build mesh transport, peer enrollment, key rotation, replay protection and revocation protocol.
10. Integrate signed-baseline repair, package rollback and boot recovery only after end-to-end crash/fault tests.
11. Connect Mora status views to the native service over an authenticated local IPC contract; browser preferences are never enforcement.
12. Run native emulator and hardware tests, stress tests, fault injection, performance regression tests and adversarial parser tests.

## Acceptance invariants

- All externally supplied data is bounded and schema-versioned.
- Event IDs are unique within the retained analysis window.
- Causal walks are cycle-safe and depth-bounded.
- Risk scoring is deterministic for the same ordered event stream.
- Mesh signals are authenticated, time-bounded and replay-resistant.
- Snapshots remain inside the managed root and restores verify content digests.
- Integrity verification never repairs without authenticated provenance.
- Quiet mode never suppresses event collection or lowers decision thresholds.
- Advisory recommendations cannot become privileged actions without a separate broker.
- Documentation, CLI status, tests and capability policy report the same maturity.
