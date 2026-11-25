# NEXUS System Components and Internal Services v1

**Architecture:** NEXUS  
**Operating system:** DuckOS  
**Systems language:** Reaper  
**Status:** component ownership and service contracts specified; all six service runtimes are not implemented.

This profile defines the component names and six internal service identities. It is additive to the existing DuckOS, Reaper, Mora and federation contracts. It does not rename repositories, public APIs or existing applications.

## 1. Ownership model

| Repository | Canonical responsibility | NEXUS relationship |
|---|---|---|
| **DuckOS** | OS implementation, privileged native boundary and Mora desktop | Owns KernelCore, NexusShell and OS-level system-service contracts |
| **Reaper** | Systems language, compiler/toolchain and deterministic policy | Owns BuildToolchain and Reaper-native policy logic |
| **Pytyliki** | C11 processor-systems workstation and bounded measurements | Supplies read-only processor and memory evidence |
| **OPlague** | Device/driver inspection and compatibility evidence | Supplies read-only device, package, signature and GPU telemetry evidence |
| **VentuSample** | C++20 procedural sample workstation and offline DSP | Supplies offline rendering and asset metadata; it is not a DuckOS audio driver |

## 2. Component registry

| Component | Owner | Maturity | Current boundary |
|---|---|---|---|
| **KernelCore** | DuckOS | Partial | Stage 1 firmware handoff, Boot Info v1 validation and early physical-frame allocation. Memory manager, interrupts, scheduler, processes, syscalls and driver runtime remain incomplete. |
| **NexusShell** | DuckOS | Partial | Mora browser-host desktop, launcher, windows, preferences and panels. Not a native kernel-launched shell or compositor. |
| **AudioSubsys** | DuckOS; VentuSample provider | Specified | VentuSample supplies offline DSP and render metadata. DuckOS has no native audio device service, driver or real-time callback path. |
| **SecurityModule** | DuckOS; Reaper/OPlague providers | Partial | Reaper capability policies, BAV schema and OPlague read-only evidence exist. Kernel-enforced MAC, native verification, scanning and quarantine do not. |
| **NetworkStack** | DuckOS | Specified | Reference policies only. Packet path, NIC drivers, TCP/IP, sockets, routing, firewall, VPN and resolver remain unimplemented. |
| **GraphicsEngine** | DuckOS | Partial | Mora host rendering and desktop policy exist. Native GPU driver, resource handles, window server and compositor remain unimplemented. |
| **BuildToolchain** | Reaper | Partial | Language frontend, diagnostics, reference runtime and developer tools exist with an experimental native C17 track. Full native compiler parity and a freestanding DuckOS backend remain incomplete. |
| **AILayer** | Unassigned | Reserved | Extension point only. No model runtime, inference contract, model provenance, data policy or resource governor is assigned. |

The machine-readable component and service registry is `catalogs/nexus-system-services.v1.json`; its structural contract is `schemas/nexus-system-services.v1.schema.json`.

## 3. Internal system-service identities

These six identities are system services, not Mora launcher applications or new repositories. A descriptor does not create a runnable process. All six remain `specified` and `not_implemented` until process isolation, service lifecycle, authenticated IPC, kernel-enforced capabilities, implementation source and tests exist.

| Service | Purpose | Dependencies | Maturity |
|---|---|---|---|
| **KERNEL_SENTINEL** | Read-only integrity measurement and policy reporting | KernelCore, SecurityModule | Specified; not implemented |
| **MEMORY_FORGE** | Memory inventory, accounting and bounded diagnostics | KernelCore | Specified; not implemented |
| **VECTOR_GATEWAY** | Network visibility, filtering policy and future encrypted transport | NetworkStack, SecurityModule | Specified; not implemented |
| **PIXEL_PIPELINE** | Native window composition, display presentation and frame diagnostics | GraphicsEngine, KernelCore | Specified; not implemented |
| **DATA_ORCHESTRATOR** | Process/task lifecycle and bounded scheduling coordination | KernelCore, NexusShell | Specified; not implemented |
| **BUILD_VANGUARD** | Explicit build, test and artifact-provenance orchestration | BuildToolchain | Specified; not implemented |

### 3.1 KERNEL_SENTINEL

Start with read-only integrity measurement for trusted system artifacts. Each result must identify the object, digest, measurement provider, trust-root version, timestamp and verification outcome. Implementation requires a kernel-backed measurement source, authenticated event channel, local trust store with rotation/revocation, isolated bounded scanner and auditable evidence. Active remediation also requires kernel-enforced containment.

TPM 2.0 may be an optional provider after a DuckOS driver and trust chain exist. Linux IMA and eBPF are Linux host facilities, not native DuckOS APIs. No process-memory scanning, injection prevention, quarantine or execution blocking is claimed.

### 3.2 MEMORY_FORGE

Start with read-only RAM and process-memory inventory, explicit units, provenance, bounds and unknown states. Implementation requires reusable frame allocation, page tables, address-space accounting, process identity and explicit RAM/swap/accelerator-memory providers.

Pytyliki can supply bounded processor/memory measurements; it is not the kernel allocator. malloc/mmap hooks are not kernel accounting. Zstd/LZ4 page compression requires page ownership, backing storage, recovery semantics and resource budgets. VRAM values must come from a supported GPU provider; arbitrary device-memory mapping is prohibited.

### 3.3 VECTOR_GATEWAY

Implementation requires a real NIC driver, packet-buffer model, network data path, socket API, routing and packet-filter contracts, queue/rate limits and packet-path tests.

nftables and XDP are Linux-host adapter options, not DuckOS kernel APIs. WireGuard requires a separately reviewed protocol and cryptographic implementation. DoH/DoT require a supported resolver and trust policy. A rule editor must not claim DDoS mitigation or firewall enforcement.

### 3.4 PIXEL_PIPELINE

Implementation requires a native window/session manager, input routing, GPU discovery and driver ABI, validated resource handles, compositor interface, display-mode discovery and presentation/recovery tests.

Vulkan may be used after a supported DuckOS backend and driver exist. Wayland is a possible protocol compatibility layer. DRM/KMS is a Linux host boundary, not an assumed DuckOS subsystem. Applications receive validated graphics resources, not unrestricted VRAM mappings.

### 3.5 DATA_ORCHESTRATOR

Implementation requires a process/thread model, address-space isolation, syscall ABI, preemptive scheduler, cancellation semantics, authenticated IPC, kernel-enforced capabilities and resource accounting.

cgroups v2, Linux namespaces and systemd are not native DuckOS dependencies. A Linux compatibility adapter may be developed independently. No process creation, priority mutation, container isolation or service supervision is exposed before the corresponding OS primitives are implemented and verified.

### 3.6 BUILD_VANGUARD

This is a user-space build and validation coordinator. Its first contract covers explicit build targets, pinned toolchains, bounded resource budgets, test results, artifact hashes, SBOM/provenance and signed-release metadata.

Existing GitHub Actions workflows remain the actual CI execution mechanism until an executable service exists. Reaper native compiler maturity is partial; external compilers may be used only through explicit project build contracts. Do not silently execute shell strings, download dependencies, access signing keys, build untrusted inputs or publish releases.

## 4. Cross-project invariants

1. DuckOS and Reaper remain canonical OS and language names. Component labels never rename repositories, public APIs or product IDs.
2. Reaper owns language and policy semantics; DuckOS owns privileged kernel operations, lifecycle and native enforcement.
3. No service is runnable until process isolation, service lifecycle, authenticated IPC and kernel-enforced capabilities exist.
4. Reuse existing versioned contracts before introducing a new ABI or transport. Every payload needs source, schema version, bounds, validity and typed failure states.
5. Missing, stale, unsupported or invalid providers stay explicit. Never invent measurements or execution results.
6. Default behavior is local-first and read-only. Network access, process execution and hardware mutation require scoped authorization.
7. Linux-specific facilities are optional host adapters and never become implicit DuckOS kernel dependencies.
8. Source, tests, CI output and target verification determine maturity. A catalog or architecture document is not implementation evidence.

## 5. Acceptance gates

| Gate | Required evidence |
|---|---|
| Service descriptor | Stable ID, owner, dependencies, capabilities, inputs/outputs and failure states |
| User-space service | Executable implementation, bounded request handling, lifecycle tests, cancellation and health |
| IPC integration | Authenticated peer identity, schema/version validation, payload limits, replay/expiry handling and negative tests |
| Privileged integration | Syscall/driver ABI, kernel-enforced authorization, audit events and target-backed tests |
| Resource control | Quotas, overload behavior, rollback and recovery tests |
| Release | Reproducible build, provenance, license inventory, artifact digest and CI evidence |

All six service descriptors and their prerequisites are recorded in this batch. Their executable runtime implementations are not claimed.
## 6. Executable Reaper policy contract

DuckOS now carries the policy-only Reaper module `duckos/nexus/services.rpr`. It recognizes the canonical component and service IDs, validates the declared service owner/state/dependency set, bounds descriptor payload/deadline values and rejects dependency mismatches. Its activation gate remains closed until process model, service supervisor, authenticated IPC, kernel-enforced capabilities and implementation tests are all present.

The assertions are integrated into `core_mvp_tests.rpr`, which is already exercised by the repository's Reaper contract workflow on its reference engines. This code validates metadata and admission policy only: it does not create a process, start a service or grant a capability.

