# DuckOS architecture

## Product boundary

DuckOS is a Reaper-first operating-system implementation. Reaper owns the source-language semantics and system policy. Native platform code is a narrow, auditable boundary for operations that require privilege or architecture-specific instructions.

The first milestone is deliberately a contract kernel: real Reaper code defines and tests the ordering, limits and decisions that a later native backend must preserve.

## Layer model

| Layer | Responsibility | Current state |
|---|---|---|
| Reaper language core | system policy, service logic, deterministic decisions | executable on reference runtime |
| Boot contract | ordered startup phases and recovery transitions | implemented as Reaper contract |
| Memory contract | range validation, alignment and bounded arena reservation | implemented as Reaper contract; not a physical allocator |
| Scheduler policy | stable priority then deadline selection | implemented as Reaper contract; no context switch |
| IPC | bounded queues, empty/full results and backpressure | implemented as Reaper contract; process transport pending |
| Capability forge | explicit grants and attenuation | implemented as Reaper contract; kernel enforcement pending |
| Driver boundary | ABI version, bus allowlist and required capabilities | descriptor validation implemented; device discovery/loading pending |
| Service supervisor | finite restart budget | policy implemented; process manager pending |
| Semantic store | externally supplied content hashes, dependency validation and ordered journal | contract implemented; BLAKE3/CRDT storage pending |
| Three media | choose CPU, accelerator or node-mesh policy | deterministic selector implemented; backends pending |
| Desktop | palette and motion policy | design tokens implemented; compositor/renderer pending |

## Startup contract

The required sequence is:

`reset → firmware → memory → interrupts → scheduler → ipc → drivers → services → desktop`

An out-of-order transition is rejected. A failed phase enters recovery policy instead of being silently treated as successful. This is a validation contract; it does not yet execute UEFI or initialise physical hardware.

## Memory contract

The initial memory model exposes three operations:

- align a requested address without allowing invalid alignment;
- check that a range is positive, aligned and contained in the declared limit;
- reserve an aligned span from a bounded linear arena.

The contract uses an exclusive upper bound. Arithmetic and ranges are validated before a future native allocator is allowed to touch memory. Page tables, MMIO mapping, DMA pinning, NUMA allocation and real reclamation remain native-backend work.

## Scheduling and flow control

Tasks are represented as `[id, priority, deadline, state]`. The policy chooses the highest priority runnable task and uses the earliest deadline as a deterministic tie-breaker. This is not a preemptive scheduler.

IPC queues have a caller-supplied capacity. A full queue returns `backpressure` and leaves the queue unchanged. The sender never grows the queue implicitly. Future process IPC must preserve this contract while adding ownership, wakeups and cancellation.

## Security and drivers

A capability is an explicit string token in the current contract model. A child capability set is valid only when every requested capability is already held by the parent. Driver descriptors declare:

`[driver_id, abi_version, bus, required_capabilities]`

A descriptor is accepted only when its identity is present, its ABI matches, its bus is allowlisted and every required capability is granted. The check does not load code or install a driver.

## Storage and determinism

A graph node is represented as:

`[content_hash, payload_kind, dependencies]`

The hash must be supplied by a trusted hashing boundary; this Reaper slice does not pretend to implement BLAKE3. Dependencies must point to already-known nodes and may not point to the node itself. Event records carry monotonically increasing sequence numbers. Durable persistence, merge semantics, cryptographic verification and crash recovery are future stages.

## Three execution media

- **Land / CPU:** predictable scalar and branch-heavy work.
- **Water / accelerator:** large, dense batches when an accelerator is available.
- **Sky / node mesh:** only when a remote worker is explicitly available.

The selector is policy only. It does not submit GPU work, serialize a graph, open a socket or migrate an executing task.

## Desktop contract

Tri-Color Duck UI uses the specification's 65/25/10 balance: porcelain surface, cobalt navigation and vermilion alerts. The current Reaper module defines tokens and motion preference only. It is not a window manager, compositor or GPU renderer.

## Native bring-up gates

1. Reaper freestanding target specification and stable calling convention.
2. Native code generation for the required Reaper subset.
3. UEFI application and serial-console boot target.
4. Page allocator, interrupt descriptors and timer source.
5. Context-switching scheduler and process address spaces.
6. Capability-enforced IPC and driver isolation.
7. Block device and verified package store.
8. Graphics backend and compositor.
9. Reproducible installer and bootable image.

Each gate needs a conformance suite and target hardware or emulator evidence. Do not skip a gate by relabelling a reference-runtime test as a hardware test.
