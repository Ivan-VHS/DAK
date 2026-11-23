# Native transition architecture: Mora to DuckOS

**Status:** architecture baseline and implementation programme  
**Scope:** all eleven native-transition workstreams and their shared system contracts  
**Project author/developer:** Ivan-VHS  
**Implementation rule:** specification, reference-runtime behavior, native implementation and target-hardware validation are separate maturity states.

## 1. Purpose

This document turns the Mora-to-DuckOS transition matrix into one coordinated engineering programme. The eleven workstreams must share identity, capability, IPC, lifecycle, storage, trust, telemetry and recovery contracts. They may be designed in parallel, but implementation must follow dependency gates so that no subsystem invents a private security model, service protocol or notion of system state.

The target is a native operating system with a small privileged kernel and replaceable, capability-scoped user-space services. Mora remains the desktop shell and user-facing control surface. It must not become a substitute for the kernel, device manager, update engine, process sandbox or cryptographic trust service.

This is an architecture and execution plan. It does not assert that the native kernel, boot chain, compositor, driver loader or compatibility runtime already exists.

## 2. Engineering principles

1. Design all eleven workstreams against one architecture and common interface catalogue.
2. Implement dependency-ready vertical slices rather than building eleven disconnected prototypes.
3. Keep privileged code small, explicit, reviewable and isolated from user-interface code.
4. Make capability checks mandatory at every kernel or broker boundary; never infer authority from a UI state or a process name.
5. Use typed, versioned, bounded contracts for system calls, IPC, manifests, configuration and audit events.
6. Make failure behavior part of each API: timeout, cancellation, retry, degraded mode, recovery and data-preservation behavior must be specified.
7. Prefer deterministic policy decisions in the kernel. AI systems may provide bounded hints to user-space policy services, but may not bypass admission rules or control privileged scheduling directly.
8. Treat rollback as a transaction only where the operation is genuinely reversible. For external or irreversible effects, use explicit compensating actions and record their limits.
9. Keep one authoritative representation of desired system state; generate UI, diagnostics and service configuration from the same versioned contracts.
10. Test security boundaries and failure paths before enabling automatic execution.

## 3. Maturity vocabulary

Every feature, API and status report must use one of these states:

| State | Meaning | Evidence required |
|---|---|---|
| Specified | Behavior, interfaces and failure rules are documented | Reviewed design and versioned contract |
| Contract-tested | Policy logic is executable on the reference runtime | Unit, property and contract tests |
| Host-integrated | User-space components communicate on a supported host | Integration tests and reproducible setup |
| Native-implemented | The native backend performs the operation | Native build, code review and target-specific tests |
| Emulator-validated | The native path works in a documented emulator profile | Reproducible boot/run logs and fault tests |
| Hardware-validated | The path works on named physical hardware | Device matrix, logs and recovery evidence |
| Release-ready | Upgrade, recovery, security and regression gates pass | Signed artifact, SBOM, release test report |

A passing Reaper or Python test is evidence for the behavior it actually exercises. It is not evidence of privilege enforcement, hardware access, real-time scheduling or bootability.

## 4. Target system architecture

### 4.1 Layer boundaries

| Layer | Owns | Must not own |
|---|---|---|
| Verified boot and recovery | Firmware hand-off, trust roots, slot selection, boot measurements and recovery | Desktop preferences or application policy |
| Kernel | Address spaces, memory, interrupts, scheduling, process lifecycle, syscall validation, IPC primitives and capability enforcement | AI decisions, application UI or package catalogue policy |
| Hardware abstraction and device manager | Bus enumeration, resource assignment, driver lifecycle, reset and device health | Unreviewed driver code or unrestricted device access |
| Privileged system brokers | Actions, devices, updates, secrets, audit and policy mediation | Arbitrary shell execution or implicit authority |
| System services | Desired-state reconciliation, packages, power, inference, provenance, audio and input services | Direct mutation of kernel internals |
| Compatibility runtimes | Isolated Windows and Linux execution environments and API translation | Kernel privileges or unrestricted host filesystem access |
| Native desktop | Display topology, compositor, window lifecycle, input routing, accessibility and XR session state | Direct privileged hardware configuration |
| Mora | Human-readable controls, previews, status, accessibility and application workspace | Enforcement, signing, device configuration or system rollback |
| Applications | User workflows within granted capabilities | Ambient access to files, devices, network or other processes |

The kernel should expose a narrow, versioned syscall and IPC surface. Policy-heavy features belong in user space wherever possible. A broker receives only the capabilities necessary for its task, and clients receive handles or scoped responses rather than ambient access to privileged services.

### 4.2 Proposed source layout

The following is a target layout, not a claim that these directories already contain native implementations:

- native/boot: firmware entry, verified boot, slot selection and recovery.
- native/kernel/arch: architecture-specific entry, interrupt and context-switch code.
- native/kernel/mm: physical and virtual memory, page tables, DMA mapping and reclamation.
- native/kernel/process: process model, syscall ABI, handles and lifecycle.
- native/kernel/sched: preemption, timers, priorities, deadlines and CPU placement.
- native/kernel/ipc: bounded IPC, shared-memory grants, wakeups and cancellation.
- native/kernel/security: capability objects, access checks and security-domain transitions.
- native/drivers: driver ABI, isolation boundary and supported bus backends.
- services/device, services/update, services/package, services/policy and services/power: user-space system managers.
- services/inference and services/provenance: optional local model and content-authenticity services.
- desktop/compositor, desktop/input, desktop/audio and desktop/accessibility: native desktop services.
- compat/windows and compat/linux: independent compatibility stacks and launch policy.
- schemas and tests: versioned contracts, conformance fixtures, fuzz corpora and platform test profiles.

Keep the existing Python package duckos as host-side build and diagnostic tooling unless a deliberate migration is reviewed. Do not silently turn a host utility into a privileged daemon.

## 5. Shared system contracts

### 5.1 Process identity and capabilities

Every request crossing a kernel or broker boundary must carry an authenticated caller identity established by the kernel, not caller-supplied text. A capability should identify:

- the object or object class it applies to;
- allowed operations;
- scope constraints such as path prefix, device identity, byte limit or endpoint;
- optional expiry, call quota and resource budget;
- parent/grant lineage so that child capabilities can only be attenuated.

Capabilities must be unforgeable handles or kernel-validated references, not plain strings trusted because they appear in a JSON document. Revocation and handle invalidation must have defined semantics. The current Reaper capability contract remains useful as a policy reference, but native enforcement is a separate deliverable.

### 5.2 IPC and service lifecycle

Every service interface must define a schema version, maximum message size, caller capability, deadline, cancellation behavior, idempotency behavior and error vocabulary. Queues are bounded. Backpressure is explicit. A caller must not be able to allocate unbounded kernel memory by sending faster than a service can consume.

Service states are: starting, ready, degraded, stopping, failed and quarantined. Restart budgets are finite and tracked per service. A supervisor must not repeatedly restart a compromised or consistently crashing privileged service. Dependencies and startup ordering are declared, checked for cycles and exposed in diagnostics.

### 5.3 Intent transaction and approval contract

A system intent uses a fixed transaction lifecycle:

1. Proposed: the client submits a typed operation and immutable parameter set.
2. Canonicalized: the broker validates schema, normalizes paths and resolves target identities.
3. Authorized: the broker checks the caller's live capabilities and policy.
4. Previewed: the UI receives the exact operation, target, scope and material side effects.
5. Approved: the user approves a digest of the canonical operation, not a mutable display string.
6. Prepared: the broker revalidates identity, permissions, preconditions and resource versions.
7. Committed: the operation executes with an idempotency key and audit record.
8. Compensated or aborted: reversible work is undone where safe; irreversible effects are reported rather than falsely labelled rolled back.

The confirmation token must be bound to the session, caller, operation digest, target object, expiry and one-time transaction identifier. Any parameter change invalidates approval. The broker must recheck authorization immediately before commit to prevent time-of-check/time-of-use substitution.

Approval design must be risk-based. Low-risk repeatable operations can use narrowly scoped, expiring grants; destructive, privileged or externally visible operations require explicit confirmation. Grouping approvals must never expand the approved scope. The audit record must capture the decision, policy version, caller, target, outcome and compensation status without unnecessarily recording secrets.

### 5.4 Audit and observability

Audit events use a versioned schema and monotonic sequence. Each event records a transaction ID, authenticated principal, operation, target, capability decision, policy version, result, timestamp source and previous-event digest. A hash chain detects accidental or partial tampering; it is not sufficient by itself if the same privileged writer can rewrite the entire store. The native design must therefore define protected append-only storage, signing-key custody and, where appropriate, an external checkpoint.

Telemetry is bounded and privacy-aware. Metrics must not contain file contents, tokens, speech samples or raw personal data. Debug dumps require explicit controls and redaction. Security audit, performance telemetry and user activity history are separate data classes with different retention and access policy.

### 5.5 Desired-state and package contract

System configuration is typed desired state, not a collection of unrelated preferences. Each setting declares its schema version, owner, default, allowed range, precedence, mutability, persistence class and restart requirement.

The reconciler computes a plan before applying changes, checks dependencies, stages changes, validates the result and records a rollback checkpoint. Configuration sources have an explicit precedence order. Local overrides must be visible and must not silently defeat mandatory security policy. Package transactions resolve dependencies before mutation, verify package provenance, stage files, update indexes atomically and support recovery from interruption.

### 5.6 Trust and provenance contract

Integrity and authorship are different claims:

- A cryptographic digest establishes that bytes match a reference digest.
- A valid signature establishes that a signer controlled a key for the signed statement.
- A trust policy establishes whether that signer and signing context are accepted.
- A C2PA assertion may describe provenance and editing history, but it does not make all content truthful or safe.

The provenance service must distinguish valid, invalid, modified, expired, revoked, unknown and unsigned states. It must validate manifest structure, signature chain, certificate policy, revocation data and applicable trust roots. Unknown or unavailable trust information must never be rendered as verified. The service must preserve original evidence and report what could not be checked.

### 5.7 Resource budgets

All background work declares CPU time, memory ceiling, I/O rate, accelerator memory, power class and deadline. Kernel admission policy remains authoritative. A user-space service can request a budget change; it cannot force it. Thermal protection and real-time deadlines outrank user-selected performance preferences and AI optimization hints.

## 6. Eleven coordinated workstreams

### 6.1 Intent UI and privileged action broker

**Target components:** intent broker, approval UI protocol, audit service and transaction coordinator.

**Deliverables:** typed intent catalogue; canonical parameter serializer; per-action authorization policy; digest-bound confirmation; one-time approval token; idempotent execution; compensation interface; audit event stream.

**Acceptance gates:**
- changing a target or parameter after preview invalidates the approval;
- replaying an approval token cannot execute the operation twice;
- expired sessions and revoked capabilities are rejected;
- a process cannot elevate its own permissions by asking Mora to approve a wider action;
- interrupted transactions recover to a documented committed, aborted or needs-reconciliation state;
- tests prove that irreversible actions are reported honestly and are not described as fully rolled back.

### 6.2 Local models and AI-native planning

**Target components:** user-space inference service, accelerator discovery, model registry, resource admission policy and scheduler hint interface.

**Deliverables:** signed or otherwise policy-verified model packages; explicit model sandbox; CPU/GPU/NPU capability discovery; bounded inference queues; memory and power budgets; model unload and cancellation; deterministic fallback when no accelerator is available.

The kernel scheduler must not depend on an AI service for correctness. AI may propose batching, placement or background-priority hints to a policy daemon. The kernel accepts or rejects those hints using deterministic rules and hard resource limits. Interactive input, interrupt handling and real-time work must not wait on model inference.

**Acceptance gates:** model absence does not impair boot; a stalled model can be killed without destabilizing the desktop; budgets are enforced; sensitive inputs remain local unless the user explicitly selects a remote service; AI output cannot grant capabilities or approve privileged actions.

### 6.3 Immutable atomic updates

**Target components:** verified boot manager, signed image format, A/B slot controller, update service and recovery environment.

**Deliverables:** signed component manifest; trusted key rotation and revocation procedure; inactive-slot staging; file and image verification; atomic boot-slot metadata update; boot attempt counter; health confirmation; recovery path; user-data preservation policy.

**Acceptance gates:** interruption during download or staging leaves the active slot bootable; corrupt or incorrectly signed images are rejected; a new slot that fails the health gate is not marked successful; repeated boot failure selects a known-good slot or recovery; downgrade and key-rotation policy are tested; user data and encryption keys remain outside the disposable system slot.

Rollback of the system image does not imply rollback of arbitrary user data. Persistent data migrations must be backward-compatible or carry their own explicit migration and recovery strategy.

### 6.4 Sandboxing and zero trust

**Target components:** process address spaces, kernel handles, capability enforcement, syscall validation, device broker and compatibility-runtime isolation.

**Deliverables:** unprivileged process baseline; per-process address-space isolation; non-inheriting capability defaults; explicit handle transfer; syscall argument validation; resource quotas; service-specific security domains; device access mediated by brokers.

**Acceptance gates:** an unprivileged test process cannot read or write another process's memory; capability attenuation cannot be reversed by a child; stale handles fail closed; malformed IPC cannot escape a service boundary; device access without an explicit grant is denied; broker crashes do not grant fallback direct access.

Privileged brokers must be small and use narrow interfaces. Applications and plugins do not receive raw hardware access merely because a feature is visible in Mora.

### 6.5 Provenance and authenticity

**Target components:** C2PA parser, signature verifier, certificate policy service, trust-store manager and file metadata adapter.

**Deliverables:** bounded parser; versioned validation result; signer trust policy; certificate expiry and revocation handling; modified-content detection; user-visible explanation; cache invalidation and trust-store update.

**Acceptance gates:** malformed manifests cannot cause unbounded allocation or parser crashes; invalid and modified content is never marked verified; unsigned and unverifiable content remain distinct; stale trust data is shown as stale; SHA-256-only inspection is explicitly identified as integrity checking rather than authorship verification.

### 6.6 Adaptive workspace and native compositor

**Target components:** display manager, compositor, window manager, graphics backend and session-state service.

**Deliverables:** native surface lifecycle; frame scheduling; multi-display topology; per-output DPI and color management; hot-plug handling; window migration; focus restoration; GPU reset recovery; optional XR session adapter.

**Acceptance gates:** unplugging a display does not lose application state; output changes preserve sensible window geometry and focus; reduced-motion policy applies at the compositor level; GPU reset returns the desktop to a recoverable state; unsupported XR devices degrade without breaking ordinary desktop use.

The compositor must not promise a fixed frame rate independent of hardware, workload and display mode. Frame-time budgets and measured results must be reported per supported profile.

### 6.7 Multimodal input and accessibility

**Target components:** unified input router, speech service, gesture service, accessibility service and privacy-control broker.

**Deliverables:** timestamped input-event schema; focus and seat ownership; keyboard, pointer, touch, pen and controller routing; optional local speech and gesture backends; screen-reader and assistive-device APIs; permission and hardware indicators.

**Acceptance gates:** events retain their source and ordering; microphone and camera access are denied by default until granted; input focus cannot be stolen by background recognition; assistive technologies can query semantic UI state without bypassing application isolation; recognition failure leaves conventional input available.

Raw audio and video should be processed locally by default where the selected backend supports it. Retention, buffering and export behavior must be explicit.

### 6.8 Windows and Linux compatibility

**Target components:** executable loader, ABI layer, compatibility process manager, runtime catalogue, graphics/audio/input bridges and guest sandbox.

**Windows deliverables:** PE image mapping; relocations; import resolution; TLS; exception handling; x86/x64 calling conventions; NT process and object semantics; Win32 APIs; registry and installer behavior; graphics, audio, input and network bridges; Proton/Wine-style runtime integration.

**Linux deliverables:** a clearly chosen and documented model for ELF execution: native Linux syscall ABI compatibility, a Linux user-space/container environment, or both. The project must not treat ELF header inspection as execution compatibility. Filesystem, process, signal, futex, network and graphics semantics require explicit coverage.

**Acceptance gates:** compatibility processes run in separate security domains; host files and devices require brokered grants; unsupported API calls fail predictably; graphics and audio translation have conformance tests; runtime discovery never silently executes a binary; launch requires an explicit user action and a reviewable plan.

DuckBridge's current dry-run planner remains non-executing until process creation, isolation and API translation are independently validated.

### 6.9 Declarative configuration

**Target components:** system-state schema, package manager, reconciler, policy resolver and rollback journal.

**Deliverables:** versioned desired-state documents; dependency solver; source precedence; preview and diff; staged application; drift detection; rollback; policy-owned immutable settings; export and reproducibility report.

**Acceptance gates:** applying the same desired state twice is idempotent; a failed transaction preserves the last valid state; conflicting sources produce a visible deterministic result; security policy cannot be overridden by a user preference; package and configuration changes are committed as one recoverable transaction where their dependencies require it.

### 6.10 Energy awareness

**Target components:** power policy service, CPU scheduler hooks, GPU/NPU runtime adapters, thermal manager and display refresh controller.

**Deliverables:** named energy/performance profiles; thermal sensors and validated limits; CPU placement and frequency requests; accelerator power coordination; display refresh and VRR negotiation; workload classification; battery and AC policy.

**Acceptance gates:** thermal limits override performance mode; failed sensors move the system to a safe policy; background indexing yields to interactive and real-time tasks; unsupported VRR is reported rather than simulated; policy changes are measured on supported devices and do not cause repeated frequency oscillation.

Hardware-specific controls stay behind drivers and device-specific capability checks. One generic control path must not assume that every CPU, GPU, NPU or display implements the same power interface.

### 6.11 Hardware inventory and recovery

**Target components:** PCI/PCIe, USB and ACPI discovery; device graph; resource manager; signed driver package verifier; driver host/isolation and recovery manager.

**Deliverables:** stable device identity; bus and topology enumeration; resource ownership; driver ABI compatibility; package signature and policy verification; staged bind/unbind; device reset; dependency-aware recovery; unified inventory snapshots.

**Acceptance gates:** repeated enumeration is stable and does not duplicate devices; malformed device descriptors are rejected; resource conflicts prevent driver activation; unsupported hardware is reported without crashing boot; a recoverable device fault can restart the driver or reset the device without requiring a full system reboot; the inventory is consistent across device, power and scheduling services.

The current read-only host inventory remains a diagnostic collector. It must not be upgraded into a driver installer without a privileged native device-management path.

## 7. Dependency order and parallel execution

All workstreams are designed together. Implementation proceeds through the following dependency gates:

| Gate | Work that can proceed | Exit condition |
|---|---|---|
| A. Shared contracts | Identity, capability model, IPC schemas, error model, audit schema, build and test conventions | Interfaces reviewed and versioned |
| B. Native boot substrate | Firmware hand-off, serial output, physical memory, interrupts, timer and recovery entry | Reproducible emulator boot and fault evidence |
| C. Process and security core | Address spaces, process lifecycle, syscall ABI, capability handles, bounded IPC | Isolation and denial tests pass |
| D. Device foundation | Bus enumeration, device graph, driver ABI, signed packages and recovery | Supported devices enumerate and recover in emulator/hardware |
| E. System transactions | Persistent storage, package manager, desired-state reconciler, A/B update and audit | Power-loss and rollback matrix passes |
| F. Native desktop | Graphics backend, compositor, display manager, input, audio and accessibility | Multi-display and device-reset scenarios pass |
| G. Optional advanced services | Inference/NPU, C2PA provenance, XR and compatibility runtimes | Independent sandbox, resource and conformance gates pass |
| H. Release integration | Installer, image assembly, update signing, recovery media and documentation | Release evidence and hardware matrix accepted |

Teams may work in parallel inside a gate after the shared interfaces are stable. A downstream task may be prototyped against mocks, but it cannot be marked native-implemented until its upstream dependency is real.

## 8. Cross-system verification programme

### 8.1 Continuous integration

Every change must run the existing Python and Mora suites plus the relevant Reaper contract tests. Native targets, once introduced, must add:

- compiler warnings as errors for owned native code, static analysis and formatting;
- address, undefined-behavior and thread sanitizers where the target supports them;
- schema compatibility checks and generated-interface consistency;
- deterministic and reproducible build checks;
- unit, integration, property-based and mutation tests for boundary parsers;
- fuzzing for PE, ELF, C2PA, ACPI, USB descriptors, package manifests and IPC framing;
- QEMU/UEFI boot tests and injected power-loss, bad-signature, corrupt-slot and service-crash scenarios;
- signed artifact verification, SBOM generation and dependency/license review.

### 8.2 Security test matrix

At minimum, test capability forgery, stale-handle reuse, privilege escalation, path traversal, symlink races, approval replay, parameter substitution, audit truncation, signature mismatch, expired/revoked certificates, malformed manifests, IPC exhaustion, driver resource conflicts, device-reset loops and compatibility escape attempts.

Every test must identify the layer under test and the evidence it produces. A mocked device, simulated signature or host-only parser test must be labelled accordingly.

### 8.3 Release evidence

A release candidate must include:
- target architecture and hardware support matrix;
- exact boot and image hashes;
- verified signing and key-rotation procedure;
- test report with emulator and physical-device results separated;
- known compatibility gaps;
- upgrade, downgrade and recovery instructions;
- SBOM and third-party attribution;
- reproducible build instructions and rollback limitations.

## 9. Repository integration and current baseline

The current repository already has useful foundations:

| Existing path | Current role | Next engineering step |
|---|---|---|
| duckos/kernel/*.rpr | Reference contracts for boot, memory, scheduling, IPC and allocation policy | Preserve semantics while implementing native architecture-specific backends |
| duckos/security/*.rpr | Capability attenuation and trust-label policy | Replace descriptive tokens with kernel-enforced capability handles |
| duckos/drivers/*.rpr | Driver ABI and resource-conflict policy | Add real bus discovery, cryptographic package verification and isolated driver lifecycle |
| duckos/hardware_inventory.py | Bounded read-only Linux/Windows host inventory | Keep diagnostic-only; create a native device graph and broker |
| duckos/compat/*.py | PE/ELF inspection, runtime discovery and dry-run plans | Implement a separate process ABI and sandbox before launch is enabled |
| duckos/manifest.py and image_layout.py | Host-side manifest verification and image-layout planning | Add signed release metadata and a native boot/update consumer |
| mora/system-policy.json | Machine-readable description of Mora feature maturity | Generate UI status from authoritative service capability reports |
| mora/* | Browser desktop shell and local preference controls | Connect via authenticated IPC adapters after native service APIs exist |
| tests/* and .github/workflows/* | Existing reference and host-tool validation | Add native build, emulator, fuzz, failure-injection and hardware jobs |

The repository's architecture, implementation status and README remain authoritative for what is currently implemented. This plan does not change a feature's maturity state.

## 10. Definition of done

A workstream is not complete merely because its UI exists or its policy function returns the expected value. It is complete only when:

1. its contract is versioned and reviewed;
2. its native implementation exists for a named target;
3. all callers cross the defined authenticated boundary;
4. positive, negative, adversarial and recovery tests pass;
5. resource use and privacy behavior are bounded and documented;
6. failure cannot silently fall back to broader privilege;
7. diagnostics expose actual service capability and health;
8. emulator and physical-hardware evidence are labelled separately;
9. documentation and support matrices match the tested implementation.

The system-wide transition is complete only when all mandatory boot, memory, process, IPC, security, storage, device, package, update and desktop gates are satisfied. AI, XR and broad compatibility remain optional capabilities that must degrade cleanly when absent.

## 11. Engineering execution policy

The requested principles of simultaneous design, comprehensive implementation, parallel automation, systemic refactoring and synchronized optimization are applied as engineering controls:

- **One design baseline:** all eleven workstreams share the same architecture, schemas and security assumptions.
- **Parallel discovery, gated implementation:** interface design and independent prototypes can proceed in parallel; integration follows explicit dependency gates.
- **Vertical completion:** each slice includes API, implementation, tests, diagnostics, documentation and recovery behavior.
- **Centralized automation:** CI validates contracts, source quality, security tests, build reproducibility and release evidence from one pipeline.
- **Systematic refactoring:** changes preserve compatibility or include an explicit schema/ABI migration and regression suite.
- **Measured optimization:** performance changes require before/after measurements on named hardware; no optimization may bypass capability, memory or thermal policy.
- **No false completion:** specification, mocks, host tools, emulator results and physical-hardware support remain separate maturity states.

This programme optimizes for a coherent, maintainable and verifiable DuckOS rather than an untestable claim that every native subsystem can be completed in one indivisible change.
