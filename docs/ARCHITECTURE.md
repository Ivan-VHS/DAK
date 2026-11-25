# DuckOS architecture

## Product boundary

DuckOS is a Reaper-first operating-system implementation. Reaper owns the source-language semantics and system policy. Native platform code is a narrow, auditable boundary for operations that require privilege or architecture-specific instructions.

The first milestone is a contract kernel: real Reaper code defines and tests startup ordering, resource limits, scheduling decisions, trust policy and data-flow behavior that a later native backend must preserve.

## Layer model

| Layer | Responsibility | Current state |
|---|---|---|
| Reaper language core | system policy, service logic, deterministic decisions | executable on reference runtime |
| Boot contract | ordered startup phases and recovery transitions | implemented as Reaper contract |
| Memory contract | range validation, 64-byte arenas, frame reset and SoA sizing | implemented as Reaper contract; not a physical allocator |
| Scheduler policy | stable priority/deadline choice and least-loaded worker selection | implemented as Reaper contract; no context switch or work stealing |
| IPC and UDB bus | bounded queues, byte accounting and explicit backpressure | implemented as Reaper contract; no shared-page mapping |
| Capability and trust layer | explicit grants, attenuation, validation and quarantine | implemented as Reaper contract; kernel enforcement pending |
| BAV Security | signed declarative detection bundles, isolated scan worker, policy broker and reversible quarantine | bundle v1 format/schema specified; scanner, verifier, quarantine and enforcement not implemented |
| DuckDriver boundary | driver ABI, package metadata and resource-conflict policy | descriptor policy implemented; signature verifier and device discovery pending |
| Service supervisor | finite restart budget | policy implemented; process manager pending |
| Semantic store | graph-reference checks, journal sequence and deterministic LWW register | contract implemented; BLAKE3 and persistent CRDT graph pending |
| Three media | choose CPU, accelerator or node-mesh policy | deterministic selector implemented; execution backends pending |
| Telemetry | bounded samples and threshold-based alerts | sample policy implemented; sensor collection pending |
| Desktop | Tri-Color Duck palette, reduced-motion and frame-budget policy | design policy implemented; compositor/renderer pending |

## Startup contract

The required sequence is:

`reset → firmware → memory → interrupts → scheduler → ipc → drivers → services → desktop`

An out-of-order transition is rejected. A failed phase enters recovery policy instead of being silently treated as successful. This is a validation contract; it does not yet execute UEFI or initialise physical hardware.

## Memory habitats and SoA

The memory contract uses an exclusive upper bound and validates ranges before a future native allocator may touch memory. The arena model stores:

`[base, cursor, limit, generation]`

A new frame or event transaction reserves aligned spans and resets the cursor as one state transition. The current policy uses a 64-byte alignment boundary, matching the source specification's cache-line target. SoA layout computes padding to a supplied lane width and checks the resulting byte budget.

These are arithmetic and lifecycle contracts, not physical page allocation. Page tables, MMIO mapping, DMA pinning, NUMA allocation, static ownership analysis, FBIP reuse and actual reclamation remain native-backend work.

## Scheduling, flock and flow control

Tasks use `[id, priority, deadline, state]`. The policy chooses the highest-priority runnable task and uses the earliest deadline as a deterministic tie-breaker. A separate flock selector chooses the least-loaded eligible worker by comparing load/capacity ratios without floating-point division. Neither function starts a thread, preempts a task or steals a live stack.

IPC queues have a caller-supplied capacity. A full queue returns `backpressure` and leaves state unchanged. The UDB byte-stream contract accounts capacity, occupied bytes, producer/consumer sequence and a high watermark. It models admission and release only; there is no shared-memory mapping or zero-copy transfer yet.

## Security and DuckDriver

A capability is an explicit string token in the current reference contract. Child grants must be a subset of the parent's grants. External input moves from `untrusted` to `validated` only after an explicit successful validation result; a failed check moves it to `quarantined`. Even validated data still needs the requested capability.

DuckDriver device descriptors record a device identity, bus, resource range, IRQ and IRQ sharing policy. The orchestrator rejects overlapping resource ranges and conflicting exclusive IRQ assignments. Driver packages are approved only when metadata matches the device bus, target architecture, ABI and granted capabilities.

**Signature boundary:** the current package record contains a boolean supplied by the caller to represent a signature-verification result. DuckOS does not yet perform cryptographic verification, scan PCI/USB/ACPI, parse platform driver packages, load modules or modify the host driver store.

## BAV Security boundary

The .bav suffix is reserved for Beelzebub AV declarative detection bundles. Version 1 is specified in [BAV_SECURITY_BUNDLE_V1.md](BAV_SECURITY_BUNDLE_V1.md) and structurally described by [bav-security-bundle.v1.schema.json](../schemas/bav-security-bundle.v1.schema.json). The signature is intended to cover the RFC 8785 canonical JSON document with the signature property removed; actual verification requires a pinned local trust store and native Ed25519 verifier.

The planned scanner is a restricted user-space worker. It will inspect file handles using bounded parsers and deterministic declarative rules. It will not execute content or rules. A separate broker will own quarantine, execution/install denial and any on-access enforcement. These actions require kernel-enforced capabilities and real filesystem/process hooks; a Mora panel, Reaper reference policy or JSON schema cannot provide that enforcement. No current malware scanner, signature verifier, quarantine engine or real-time protection is claimed.

The Reaper proposal that used .bav for Buffer Allocation & Validation conflicts with this ownership. The buffer specification is renamed .bufspec and must be reflected in a separate Reaper registry/schema change before being advertised as supported.

## Semantic storage and deterministic merge

A graph node is represented as `[content_hash, payload_kind, dependencies]`. The module validates that the new hash is not already present and that dependencies reference known nodes. Event records use monotonically increasing sequence numbers.

The CRDT module currently implements one narrowly defined operation: a last-writer-wins register ordered by Lamport clock, actor ID and deterministic textual tie-break. It is not a complete CRDT hypergraph, and it does not provide durable storage, structural sharing, BLAKE3 hashing or general multi-user synchronization.

## Three execution media and telemetry

- **Land / CPU:** predictable scalar and branch-heavy work.
- **Water / accelerator:** large, dense batches when an accelerator is available.
- **Sky / node mesh:** only when a remote worker is explicitly available.

The selector is policy only. It does not submit GPU work, serialize a graph, open a socket or migrate an executing task. Telemetry validates externally supplied samples, keeps a bounded history and classifies values against caller-supplied warning/critical thresholds. It does not read thermal, power, DPC/ISR or device sensors.

## Mora visual and interaction contract

The shared DuckOS/Mora shell uses the black/white/yellow product identity and semantic status colors defined by the current Mora design tokens. Reduced Motion suppresses non-essential transitions. UI policy and a frame-time classifier are design/reference behavior, not evidence of native rendering performance.

The [interaction and ergonomics standard](ERGONOMICS_AND_INTERACTION_STANDARD.md) is normative for browser and native surfaces. It covers keyboard-first operation, focus, pointer/touch targets, window and workspace behavior, density, text scaling, accessible semantics, asynchronous feedback, drafts, Undo, error recovery, privacy and measurable usability. The native implementation must be verified separately for each supported platform.

This is not a window manager, Wayland compositor, Vulkan renderer or 240-FPS guarantee. Rendering, input handling, font shaping and accessibility integration require native desktop modules.

## Native bring-up gates

1. Reaper freestanding target specification and stable calling convention.
2. Native code generation for the required Reaper subset.
3. UEFI application and serial-console boot target.
4. Page allocator, interrupt descriptors and timer source.
5. Context-switching scheduler and process address spaces.
6. Capability-enforced IPC, shared-page transport and driver isolation.
7. Device enumeration, signature verification and verified package store.
8. Persistent semantic graph and crash-safe event journal.
9. Graphics backend and compositor.
10. Reproducible installer and bootable image.

Each gate needs a conformance suite and target hardware or emulator evidence. Do not skip a gate by relabelling a reference-runtime test as a hardware test.
