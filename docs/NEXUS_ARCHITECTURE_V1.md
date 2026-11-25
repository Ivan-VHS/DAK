# NEXUS Architecture Profile v1.0

**Status:** architecture proposal and compatibility profile  
**Owner:** DuckOS  
**Applies to:** DuckOS, Reaper, Pytyliki, OPlague and VentuSample  
**Compatibility:** additive; existing repository, application, API, command, schema and file names remain unchanged.

## 1. Purpose and naming boundary

NEXUS is the engineering vocabulary and integration profile for coordinating independently owned products. It is **not** a new operating-system name, a replacement product family, a monolithic runtime or a mandate to rename existing source symbols.

The Anatidae family identity remains the product-level umbrella. The existing repositories remain canonical:

- **DuckOS** — operating-system project, native host boundary and Mora desktop shell.
- **Reaper** — programming language, compiler/tooling and deterministic system-policy contracts.
- **Pytyliki** — native C11 processor-systems workstation and bounded metrics/analysis.
- **OPlague** — device/driver inspection, compatibility evidence and gaming-performance diagnostics.
- **VentuSample** — C++20 procedural sample workstation and offline audio-processing core.

Names such as `NexusOS`, `KernelCore` as a replacement for Reaper, and genre-derived draft labels are not adopted as repository or product names. A NEXUS application is a new, separate application identifier; it does not supersede an existing Mora or repository application.

This profile extends the existing [Anatidae Naming Canon](https://github.com/Ivan-VHS/Reaper/blob/main/federation/ANATIDAE_NAMING_CANON.md), [OCTA-8 federation](https://github.com/Ivan-VHS/Reaper/blob/main/docs/OCTA_PYRAMID_FEDERATION.md) and [DuckOS shared standards](SHARED_STANDARDS.md). It does not replace them.

## 2. Correct system model

The architecture is a **federation of independent products with explicit adapters**, not a single process that owns every subsystem.

| Layer | Responsibility | Authoritative owner | Current boundary |
|---|---|---|---|
| Language and policy | Reaper syntax, reference semantics, deterministic system-policy evaluation and toolchain | Reaper | Reference/runtime and native compiler maturity are tracked separately |
| OS and native host | Boot, privileged operations, process/service lifecycle, native IPC, device access and desktop host | DuckOS | Stage 1 boot foundation; many native services remain planned |
| Processor diagnostics | Read-only topology/inventory, bounded measurements, C ABI metrics | Pytyliki | Native C11 workstation; no OS tuning or hardware writes |
| Device evidence | PnP inventory, package/signature inspection, GPU telemetry snapshots, gaming diagnostics | OPlague | Read-only by default; user-confirmed reversible host sessions are separate operations |
| Audio processing | Procedural sample generation, offline DSP, file conversion and plugin/pack metadata | VentuSample | Offline by default; not a kernel audio driver or real-time DAW host |
| Desktop presentation | Mora shell, launcher, workspaces, consent surfaces and future native UI | DuckOS | Browser-hosted Mora and native kernel are distinct execution environments |

Reaper is not renamed to KernelCore. Reaper supplies language and policy semantics; DuckOS owns the OS boundary. Mora is not treated as a privileged kernel service.

## 3. NEXUS concepts

These terms describe interfaces and roles. They do not require a specific language, object model or runtime implementation.

| Concept | Meaning | Required invariant |
|---|---|---|
| **Agent** | A named service or autonomous capability-bearing component | Has a stable identity, owner, declared capabilities, lifecycle and health semantics |
| **Nexus** | Logical coordination plane for discovery, compatibility and policy metadata | May be implemented by versioned manifests and local adapters; it is not a mandatory central daemon |
| **Worker** | A bounded unit of task execution | Has explicit input, limits, cancellation and result semantics |
| **WorkerPool** | A resource-bounded execution policy for a set of workers | Declares queue policy, concurrency ceiling, affinity policy and overload behavior |
| **Capability** | A narrowly scoped permission to perform an operation | Deny by default; grant only to the authenticated caller and requested scope |
| **Contract** | A versioned machine-readable or documented interface | Names owner, consumer, version, validation, failure mode and maturity evidence |

Do not add a universal `Agent` base class or public `Worker` ABI merely to match the vocabulary. Use the smallest abstraction that fits the owning project.

## 4. Coordination and transport

1. Preserve the existing OCTA-8 peer topology and repository ownership. There is no central executable gateway and no shared monolithic runtime.
2. Prefer existing contracts: `ivan-vhs.report.v1`, `oplage.device-snapshot.v1`, `oplage.gpu-telemetry.v1`, `pytyliki.c-abi.v1`, `ventusample.pack.v1` and the existing Mora/OPlague gaming contract.
3. Reuse JSON artifacts for bounded evidence exchange. Use native C ABI only through an explicit trusted library path. Do not introduce implicit dynamic loading.
4. Use the DuckOS/Reaper IPC and UDB contracts as policy definitions only until a native transport is actually implemented and tested.
5. No project may silently advance another repository's source pin, build, launch, install, mutate or load its payload.
6. Every optional peer must be allowed to be absent. A missing provider is reported as unavailable, never replaced with invented or estimated data.
7. All cross-project requests carry correlation identity, schema version, bounded payload size, deadline/expiry where applicable and an explicit error result. Do not create a second generic event bus until a concrete consumer requires one.

## 5. Engineering vocabulary

The following mapping applies to architecture prose and new internal concepts only. It is not a bulk source-code rename.

| Legacy concept or label | Engineering term | Migration rule |
|---|---|---|
| Sprite | Agent | Use for a named capability-bearing component; preserve any existing public symbol until a dedicated compatibility migration is approved |
| Moon | Nexus | Use for the logical coordination/registry plane; do not imply one mandatory daemon |
| Bunny | Worker | Use for one bounded execution unit |
| Rabbits | WorkerPool | Use for a bounded set of workers and its queue/concurrency policy |
| Reaper (as a kernel label) | Reaper language/toolchain | Keep the product name Reaper; it is not renamed to KernelCore |
| DuckOS (as a generic shell label) | DuckOS operating system | Keep the product name DuckOS; it is not renamed to NexusOS |
| Thunderous / genre-derived audio labels | Audio processing domain | Route audio ownership to VentuSample where applicable; do not invent an audio-driver repository |
| Imperial / genre-derived security labels | Trust and security domain | Keep security services under their actual owner and capability boundary |
| UK / genre-derived network labels | Network services domain | Treat as a DuckOS subsystem proposal, not a repository or dependency |
| Luxury / genre-derived visual labels | Desktop design system | Keep Mora and DuckOS visual identity; use specific UI/asset tool names for new applications |
| Studio / mastering studio | Developer workbench | Use for language, diagnostics and authoring environments |
| Mixing desk / mixer | Resource and policy console | Use for resource inspection and policy configuration |
| Production pipeline | Build and validation pipeline | Use for reproducible build, test, package and release stages |
| Musical track / stage metaphor | Workstream / lifecycle stage | Use Stage 0.x, Stage 1.x and explicit exit criteria |
| Rhythm / tempo (scheduler metaphor) | Scheduling policy / deadline / period | Do not imply timing guarantees without measurements |
| Mastering (release metaphor) | Packaging, verification and release | Use evidence-backed release terminology |

Use precise engineering language in new architecture documents and UI copy:

| Replace this metaphor | Use this term |
|---|---|
| Studio / mastering studio | Developer workbench |
| Mixing desk / mixer | Resource and policy console |
| Production pipeline | Build and validation pipeline |
| Track / musical stage | Workstream / lifecycle stage |
| Rhythm / tempo (scheduler metaphor) | Scheduling policy / deadline / period |
| Mastering (release metaphor) | Packaging, verification and release |
| Music-driven theme | User-selected theme or explicit system state |

Do not rename legitimate audio-domain terminology in VentuSample: DSP, sample, PCM, MIDI, sample rate, WAV and offline render remain technically correct. The existing product names and the product-specific audio vocabulary are outside this terminology migration.

## 6. Corrections to the initial concept list

### GPU and memory

Do not bypass the GPU driver or expose arbitrary VRAM mappings to desktop applications. Use a reviewed native graphics API/driver boundary, validated resource handles, explicit ownership, fences and bounded mappings. GPU telemetry from OPlague is evidence, not a memory-access capability.

### Real-time audio

VentuSample currently owns offline processing. A real-time audio service would be a separate DuckOS capability with its own device ownership, buffer model, priority-inversion analysis, underrun behavior and hardware test matrix. Do not promise end-to-end latency below 1 ms without measurements on named hardware and workloads.

### Secure boot and signing

Use a verifiable boot manifest and public-key signature chain. Keep private signing keys out of source repositories and runtime images. Distinguish hashing, signature verification, measured boot, secure boot and key provisioning; they are not interchangeable.

### Network shaping

Network scheduling belongs in a future DuckOS network service with explicit queue classes, rate limits and observability. A UI profile cannot claim to prioritize packets until the native network path exists. Never bypass anti-cheat or security controls.

### Compression, snapshots and deduplication

Compression must be bounded by input size, output size, CPU time and memory; preserve checksums and format/version metadata. Snapshot/restore requires crash-consistent storage semantics and a tested recovery path. Memory deduplication requires copy-on-write correctness, tenant isolation and side-channel review before adoption.

### Sandboxing and privilege

A sandbox is only real when process/address-space isolation and kernel-enforced capabilities exist. Reaper policy checks and UI toggles alone are not a security boundary. Use least privilege, explicit user consent, authenticated local IPC and auditable rollback.

### AI and hardware control

Prediction models belong in user space and may provide advisory output. They must not run in interrupt context or become a kernel dependency. CPU frequency, voltage and fan changes remain unsupported unless a separately reviewed, hardware-specific control path exists and the user approves each applicable operation.

## 7. Delivery stages

The stages are lifecycle labels, not calendar promises.

| Stage | Deliverable | Exit evidence |
|---|---|---|
| **Stage 0.1 — Inventory** | Ownership map, existing contract inventory, duplicate detection | Every capability maps to one authoritative repository and current status |
| **Stage 0.2 — Contract alignment** | Compatibility matrix and schema/version rules | Existing schemas validate; no duplicate envelope or hidden runtime dependency |
| **Stage 0.3 — Read-only adapters** | Mora views for existing OPlague/Pytyliki/Reaper/VentuSample evidence | Valid, invalid, absent and stale provider fixtures are handled correctly |
| **Stage 1.0 — Native host bridge** | Authenticated, capability-scoped native service boundary | Replay/expiry tests, consent tests, schema tests, process isolation and audit |
| **Stage 2.0 — Native subsystem integration** | Only the OS services that have real implementations | Hardware-backed tests, failure recovery, security review and measurable performance |

A stage is complete only when code, tests, reproducible commands and evidence exist in the owning repository.

## 8. Acceptance criteria

- Existing repository identities, app names, public APIs and serialized formats are unchanged.
- The NEXUS profile does not create a mandatory central runtime or a hidden dependency between products.
- Existing federation contracts remain the source of truth for their domains.
- Every proposed capability is labelled `implemented`, `partial`, `planned` or `not_applicable` with repository-local evidence.
- Mora distinguishes live provider data from examples, cached values and unavailable capabilities.
- Hardware mutation, driver installation, firmware changes and privileged execution remain opt-in, separately authorized and reversible.
- Performance claims include device, provider, build, workload, units, sampling interval and before/after measurements.

## 9. Current implementation status

This document establishes the architecture profile only. It does not claim that native process isolation, a production scheduler, GPU compositor, audio driver, TCP/IP stack, secure boot chain, hardware power control or system restore implementation is complete. Use the repository-local implementation status documents as the authority for each capability.
