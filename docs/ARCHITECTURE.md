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

## Semantic storage and deterministic merge

A graph node is represented as `[content_hash, payload_kind, dependencies]`. The module validates that the new hash is not already present and that dependencies reference known nodes. Event records use monotonically increasing sequence numbers.

The CRDT module currently implements one narrowly defined operation: a last-writer-wins register ordered by Lamport clock, actor ID and deterministic textual tie-break. It is not a complete CRDT hypergraph, and it does not provide durable storage, structural sharing, BLAKE3 hashing or general multi-user synchronization.

## Three execution media and telemetry

- **Land / CPU:** predictable scalar and branch-heavy work.
- **Water / accelerator:** large, dense batches when an accelerator is available.
- **Sky / node mesh:** only when a remote worker is explicitly available.

The selector is policy only. It does not submit GPU work, serialize a graph, open a socket or migrate an executing task. Telemetry validates externally supplied samples, keeps a bounded history and classifies values against caller-supplied warning/critical thresholds. It does not read thermal, power, DPC/ISR or device sensors.

## Tri-Color Duck desktop contract

The UI policy uses the source's 65/25/10 balance: porcelain surface, cobalt navigation and vermilion alerts. Reduced-motion preference overrides animation. A frame-time classifier reports whether a supplied frame duration meets its budget (16 ms by default in the integration tests).

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


## Desktop utilities, launcher and hardware bench

The Mora-facing utility suite has a separate versioned catalogue of fifteen system applications; it does not replace the seven first-party DuckOS products. The catalogue is packaged for the Python host tools and validated against a JSON Schema.

The host-side `duckos.desktop` layer defines bounded state contracts for stable numbered launcher slots, package SHA-256 checks and digest-bound unsigned approvals, an A/B image update state machine, and a profile-bound bench controller. These contracts are testable on ordinary development hosts and do not claim to be kernel services.

Privileged boundaries remain explicit:

- Launcher resolution returns a structured request. A native process manager, executable path resolver and kernel-enforced sandbox must perform the actual launch.
- A/B activation requires a board/image backend and verified signature evidence. The default implementation only reports state and plans; no disk image or boot variable is modified.
- Bench control accepts only a named board profile, checks fresh telemetry and enforces configured voltage/current, PCIe/USB link, GPU/NPU temperature/utilization and calibrated-probe limits before a test. Named rail enable/disable and V/A setpoints are bounded by that profile and read back through the adapter. Without a board-specific native adapter it remains disconnected and fail-closed.
- The serial journal records session, fixture slot, port and redacted line data with a hash chain. A native UART/USB serial adapter must supply the lines.
- PCIe, USB, NPU and probe access remains read-only inventory/telemetry until a real driver and restricted device broker exist. No generic register write interface is exposed.

The system-image A/B pair and hardware fixture A/B pair are independent namespaces. The former selects an OS image for boot; the latter labels the physical test fixture. See [Desktop runtime contracts](DESKTOP_RUNTIME.md) for the application catalogue and CLI workflow.
