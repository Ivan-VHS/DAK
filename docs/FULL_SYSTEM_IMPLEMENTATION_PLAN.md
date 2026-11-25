# Duck Full System — implementation architecture and release gates

**Target:** a fully native, installable DuckOS for x86_64 Intel/AMD systems, with Elbrus kept as a separately qualified compatibility target.  
**Baseline:** DuckOS main after the x86_64 exception-IDT merge on 2026-11-25.  
**Status:** architecture and implementation contract; this document does not mark the planned kernel facilities as implemented.

## Mission and evidence rule

Duck Full System means the machine boots into a usable native operating-system session: the kernel owns address spaces and scheduling, starts an isolated user process, mounts persistent storage, starts Reaper services, enumerates supported devices, and launches the native Duck Desktop. Installer, update, recovery and Secure Boot claims require their own end-to-end evidence.

A file, JSON schema, policy module, application catalogue, host-side test or UI mockup is not proof of a native OS capability. Every capability moves through the evidence ladder:

1. **Specified** — versioned contract, owner, limits, error model and dependencies exist.
2. **Host-tested** — independent tests validate the contract or parser without claiming privileged behavior.
3. **Native-implemented** — the kernel/runtime code performs the operation.
4. **QEMU-verified** — a booted image demonstrates the operation in an emulator, with serial assertions and negative tests.
5. **Hardware-qualified** — a documented device/firmware matrix passes, including failure and recovery paths.

The machine-readable register is [.architecture/full-system-roadmap.v1.json](../.architecture/full-system-roadmap.v1.json). Its validator rejects missing evidence paths, invalid maturity values, unknown dependencies and dependency cycles.

## Architecture invariants

- **Native language:** Reaper is the system language and owns system policy, services and user-space implementation. C11 and assembly remain a narrow, auditable x86_64 firmware/interrupt entry boundary until the Reaper freestanding backend can replace each bridge with equivalent tested code. No Python implementation or Python test runner is introduced for Duck kernel/runtime work.
- **Primary platform:** one vendor-neutral x86_64 implementation for current Intel and AMD CPUs. Preserve an Elbrus architecture port and its contracts; qualify it separately rather than weakening the primary path.
- **Privilege:** kernel-only mapping, interrupt, scheduler, device and storage authority. User services receive explicit DABI64 capabilities; no ambient device or filesystem access.
- **Local-first:** boot and core desktop work offline. Network is opt-in per service, telemetry stays local by default, and update/package metadata is signed and verifiable.
- **Reproducibility:** pinned toolchains and source commits, deterministic artifacts where feasible, checksums, SBOM/provenance and license notices. Never advance submodules implicitly.
- **Fail closed:** malformed firmware tables, executable images, manifests, driver packages, system calls and update metadata are rejected before side effects.
- **No pretend compatibility:** inspecting PE/ELF files or preparing a launch plan is not execution; a policy contract is not enforcement; a desktop host application is not a kernel-launched compositor.

## Ten implementation domains

### 1. Physical and virtual memory

**Current maturity: native partial.** DuckOS validates the Limine memory map and Boot Info v1 and has a monotonic 4 KiB physical-frame allocator used to allocate and clear one early frame. This is not a reusable memory manager or virtual-memory implementation.

**Required implementation**
- Reusable physical-frame allocator with allocation/free, coalescing, reserved-range exclusion, metadata bounds and exhaustion handling; buddy allocator is the baseline candidate.
- x86_64 page-table manager for 4-level paging initially, with an explicit capability/feature gate for LA57. Map/unmap/protect/query, large pages when safe, kernel/user separation, canonical-address validation and correct TLB invalidation.
- Process address spaces, guarded kernel stacks, demand paging only after fault handling is reliable, copy-on-write only after reference counting and SMP TLB shootdown are proven.
- Explicit MMIO and DMA mapping APIs. Never treat device memory as ordinary RAM; pin pages and enforce W^X and ownership.
- SMP-safe allocator and per-CPU state after AP startup is introduced.

**Acceptance gate:** host tests for overflow, alignment, overlap, fragmentation, exhaustion and ownership; QEMU tests that map/unmap pages, enforce user/supervisor and W^X permissions, recover from expected page faults, reject invalid canonical addresses and verify TLB changes on more than one CPU. The boot path must no longer rely on a single-frame demonstration.

### 2. CPU tables, interrupts, timers and scheduler

**Current maturity: native partial.** The main branch installs a 256-entry IDT with diagnostic handlers for CPU exceptions 0–31. External/maskable interrupts remain disabled. The active bootloader GDT is retained; TSS/IST, APIC and timer routing are not implemented.

**Required implementation**
- Owned GDT, TSS and dedicated IST stacks for double fault, NMI and machine-check paths; validate stack guards and selector layout.
- Complete IDT and assembly entry/exit ABI, interrupt nesting rules, register/segment preservation, bounded top halves and deferred work queues.
- ACPI MADT discovery; Local APIC and IOAPIC initialization, interrupt-source override handling, EOI and legacy PIC masking. Add x2APIC only behind a verified feature path.
- Monotonic clock abstraction and timer source selection. Start with a virtualized APIC timer; add HPET/TSC-deadline only after calibration, invariance and fallback rules are tested.
- Bootstrap and application processors, per-CPU run queues, preemptive context switch, bounded interrupt-disabled critical sections, priorities, deadlines, sleep/wakeup and CPU affinity.

**Acceptance gate:** QEMU injects exceptions and device IRQs; tests prove vector/error-code frame layout, IST stack selection, APIC routing/EOI, monotonic timer behavior, preemption, wakeups and no lost/duplicated ticks. Run with one and multiple virtual CPUs. Interrupt storms and invalid routes must fail safely.

### 3. Processes, threads, Ring 3 and DABI64

**Current maturity: policy only.** Reaper process/scheduler/VM/IPC policy files exist, but they do not switch contexts, create processes, map user pages or cross a privilege boundary.

**Required implementation**
- A kernel task model with generation-safe handles, process/thread lifecycle, per-process address space, kernel/user stacks, scheduler integration, wait/exit and cancellation.
- First executable format: bounded ELF64 loader with validated headers, segments, relocations supported by the selected ABI, stack construction and entry-point checks. Do not execute arbitrary host binaries.
- Ring 3 transition, SYSCALL/SYSRET entry, versioned DABI64 register/stack/calling convention, stable syscall numbers, feature negotiation and error/result rules.
- Safe user-memory copy-in/copy-out, pointer/length overflow checks, capability checks, handle validation and syscall quotas. No kernel pointer is returned to user space.
- IPC with bounded messages and explicit ownership; shared memory only after page mapping and revocation semantics are proven.

**Acceptance gate:** a kernel-launched Reaper-built user program enters Ring 3, prints through a capability-gated service, creates and joins a thread, opens an authorized file, exchanges an IPC message and exits. Negative tests cover invalid pointers, stale handles, privilege escalation, W^X violations and syscall fuzz cases.

### 4. Native filesystem and persistent user profiles

**Current maturity: policy only.** VFS, history and CRDT policy modules exist. The kernel does not mount a disk filesystem, persist users or provide a native profile session.

**Required implementation**
- VFS with stable vnode/file-handle semantics, mount namespaces, permissions, link/path rules, quotas, locking, error codes and bounded directory iteration.
- Initial boot filesystem/initramfs plus devfs, procfs and tmpfs. Keep boot-critical recovery tools available even when user storage is damaged.
- Separate EFI System Partition, system slots, recovery area and user-data area. Select the first writable persistent filesystem through a format ADR that compares crash consistency, repair tooling, checksums, permissions, complexity and interoperability.
- User identity/profile service with atomic settings writes, per-user ownership, ACL/capability mapping, quotas, encrypted-home integration only after key lifecycle and recovery are designed.
- Journaling or copy-on-write transaction semantics, fsck/repair, crash/power-loss tests, free-space accounting and safe unmount.

**Acceptance gate:** create/mount/read/write/rename/unlink/sync across reboot; power-cut injection at every transaction boundary; corrupted metadata is detected and repaired or mounted read-only; users cannot traverse another profile without an explicit grant. Verify disk images in QEMU and preserve a recovery path.

### 5. ACPI, PCI, USB and driver architecture

**Current maturity: policy only.** Driver ABI and resource-conflict policy files exist. There is no native PCI/USB/ACPI enumeration or driver loader.

**Required implementation**
- Bounded ACPI discovery and checksum validation for RSDP/RSDT/XSDT, FADT, MADT and MCFG. Reject malformed lengths, duplicate tables and address overflow.
- PCI/PCIe enumeration, config-space access, BAR sizing/mapping, bridge traversal, capability parsing and device identity registry.
- Driver model with versioned ABI, lifecycle, dependency graph, resource ownership, interrupt and DMA descriptors, capability manifest, signed package validation and audit trail.
- Driver isolation: untrusted or third-party drivers must not run in ring 0 by default. Define a user-mode driver path and a minimal, reviewed kernel driver set. IOMMU/DMA isolation is required where platform support exists before granting bus-mastering devices broad memory access.
- First device targets: QEMU virtio block/net/gpu/input and a conservative xHCI/USB HID path. Real hardware qualification follows an explicit Intel/AMD chipset and device matrix.

**Acceptance gate:** malformed ACPI/PCI structures are rejected; QEMU enumerates expected devices; BARs, IRQs and DMA mappings remain within assigned ranges; driver crash/timeout can be contained; a device can be reset without corrupting unrelated services. No auto-load of unsigned modules.

### 6. Reaper Runtime and native system services

**Current maturity: host/policy only.** Reaper language, reference execution and partial native tooling exist in the federated project. Reaper policy files and host ABI proposals do not yet form a freestanding DuckOS runtime or privileged syscall layer.

**Required implementation**
- Reaper freestanding target profile, canonical typed IR, source maps and deterministic diagnostics; fixed-width integer, memory, borrowing/region and no-allocation guarantees required by kernel code.
- Native compiler/backend capable of emitting a documented ELF64/DABI64 object and linking/loading a minimal system image. The existing host compiler subset must not be called feature-complete.
- Runtime primitives for startup, stack/unwind policy, allocation policy, synchronization, clocks, file/process handles and bounded IPC; kernel calls only through DABI64.
- Capability-gated Reaper System Runtime adapter mapped to real kernel syscalls. The adapter must validate payloads, handles, sizes, timeouts and grants; reference runtime behavior remains separate.
- PID 1 / service supervisor, dependency ordering, readiness/health checks, finite restart budgets, structured logs with request/correlation IDs and recovery behavior.

**Acceptance gate:** compile a Reaper kernel service without a hosted runtime, verify ELF and relocation metadata, launch it as an isolated user process, exercise allowed/denied system operations, restart it after a controlled crash and reproduce the same build/test result from pinned sources.

### 7. Native Duck Desktop, compositor and window system

**Current maturity: host only.** Mora is a separate browser-hosted desktop shell. Native UI and Reaper desktop policy work do not make it a kernel-launched compositor.

**Required implementation**
- User-space compositor and window manager launched by the service manager, not embedded into the kernel.
- Framebuffer/GOP fallback first; then a render backend with explicit buffer ownership, damage tracking, vsync/frame pacing and recoverable display reset.
- Input service for keyboard, pointer and touch, focus/input routing, clipboard permissions, workspace/window lifecycle and multi-monitor capability negotiation.
- Native settings, file manager, launcher, notifications and accessibility tree. Reaper owns application/service policy; no Electron or WebView2 dependency in the OS product canon.
- Shared Imperial Noir & Glass tokens, gold semantic accent, accessible contrast, keyboard-first operation and reduced-motion behavior.

**Acceptance gate:** QEMU boots to a real native login/session process and launches the compositor without a host browser. Window creation, input, focus, resize, multiple clients, app crash recovery and accessibility semantics are tested. Frame-time metrics are reported, not advertised as guaranteed FPS.

### 8. GPU, audio, network and power

**Current maturity: policy only.** Graphics, audio, networking and platform Reaper modules describe policies and boundaries; they are not hardware stacks.

**Required implementation**
- Graphics: software framebuffer renderer, then virtio-gpu as the first virtual target; define a stable GPU service ABI and memory ownership before vendor backends. Intel/AMD GPU support is a staged hardware program, not a generic “all GPUs” claim.
- Audio: device discovery, clocked audio service, buffer scheduling, mixer and permission model. Start with virtio-snd or a supported HDA profile; VentuSample remains offline DSP until a real-time service is qualified.
- Networking: virtio-net and a conservative emulated adapter first; Ethernet, DHCP, IPv4/IPv6, DNS, routing, firewall and socket APIs before Wi-Fi. Network remains disabled by default for system services unless granted.
- Power: ACPI power buttons, reboot/shutdown/sleep states, CPU idle and thermal reporting with safe fallbacks. Firmware writes, voltage and frequency overclocking are out of scope.
- Telemetry from Pytyliki/OPlague is read-only evidence; it does not become a privileged tuning or driver installation path.

**Acceptance gate:** virtual GPU/audio/network devices are tested under load and disconnect/reconnect; malformed device input cannot corrupt kernel state; audio underruns, network loss and GPU reset are observable and recoverable. Physical Intel/AMD support is listed per device and firmware revision.

### 9. Jora Store, DuckBridge, BAV and system applications

**Current maturity: host only.** Jora/catalogue, DuckBridge inspection/planning and BAV declarative/security policy work exist at host or specification level. They are not an in-kernel package store, executable compatibility runtime or endpoint protection system.

**Required implementation**
- Jora packages use signed manifests, provenance, dependency constraints, architecture/ABI compatibility, content hashes, offline cache and atomic install/upgrade/remove transactions.
- Package execution is a separate step from package inspection. No package post-install script runs with ambient privilege; lifecycle hooks run with explicit capabilities and rollback.
- DuckBridge remains a compatibility broker: static PE/ELF inspection first, then isolated Wine/Proton/QEMU-style backends only when the native process, graphics, audio, input and filesystem boundaries are ready. No promise to run every Windows executable.
- BAV scanner runs as a restricted user-space worker with bounded parsers, signed rule bundles, local quarantine and audit. Kernel enforcement requires real file/process hooks and capability revocation; context classification is never a malware verdict.
- System apps and store UI are native Reaper/user-space clients of the package and security services.

**Acceptance gate:** install, upgrade, reject, uninstall and rollback signed offline packages in a disposable image; fuzz manifest/archive/PE parsers; run BAV scans without executing inspected files; prove that untrusted packages cannot gain capabilities or write outside their transaction.

### 10. Installer, Secure Boot, updates, recovery and rollback

**Current maturity: host only.** DuckOS has release/deployment plans and archive/signature helpers. The current ISO is not a disk installer, Secure Boot chain or A/B update system.

**Required implementation**
- UEFI installer with explicit disk selection, clear destructive-operation preview, confirmation, partition validation, cancellation and post-write verification. Never auto-format or infer the target disk.
- EFI, A/B system slots, recovery and persistent user-data layout with versioned metadata.
- Secure Boot chain: signed bootloader/kernel and approved modules, reproducible release provenance, revocation/rotation process and documented key enrollment. No embedded private signing keys.
- Signed update metadata, content-addressed chunks, atomic inactive-slot installation, health-confirmed activation, boot-attempt counter and automatic rollback to the last known-good slot.
- Recovery environment can verify, repair or restore the system without overwriting user data by default.

**Acceptance gate:** install into a disposable QEMU disk from both supported boot modes; reject tampered signatures and downgrade attempts; interrupt update at every phase; prove boot fallback and rollback; verify recovery while user-data hashes remain unchanged. Secure Boot claims require a real OVMF Secure Boot test with controlled enrolled keys and a separate physical firmware matrix.

## Dependency order and delivery waves

These domains are not ten independent parallel features. The critical path is:

**Wave A — kernel base:** (1) memory and (2) descriptor/interrupt/timer foundation. Establish owned GDT/TSS/IST, reliable page mapping, APIC and time before enabling preemption.

**Wave B — execution and persistence:** (3) Ring 3/process/DABI64, (4) VFS/profiles and (5) device discovery/driver isolation. The order may overlap after stable page mapping and IRQ routing, but user-mode drivers depend on processes and capabilities.

**Wave C — native language and services:** (6) freestanding Reaper Runtime, syscall adapters, init and service supervision. Reaper compiler/runtime and kernel ABI changes must be coordinated with the Reaper repository through versioned contracts and pinned submodule updates.

**Wave D — usable machine:** (8) minimum input/display/storage/network/audio/power services, then (7) native compositor and desktop session. The first graphical release can use the framebuffer backend; GPU acceleration is not a boot prerequisite.

**Wave E — product and trustworthy release:** (9) Jora/DuckBridge/BAV system integration, then (10) installer, signed boot chain, A/B updates and recovery. Release engineering must never make security depend on a browser shell or host-only tool.

## ISO release gates

| Image | Required evidence | What it may claim |
|---|---|---|
| Developer Preview (current family) | BIOS/UEFI QEMU boot, early handoff, one-frame allocator, exception IDT, offline source/tools payload | Experimental boot foundation and host ecosystem bundle |
| Kernel Alpha | reusable allocator, page tables, GDT/TSS/IST, APIC/timer, SMP scheduling, fault tests | Native kernel services demonstrated in QEMU |
| System Alpha | Ring 3, DABI64, Reaper service manager, VFS and persistent profile, device registry | Multi-process OS session with persistent storage |
| Desktop Alpha | native compositor, input, display, native Reaper apps, minimum GPU/audio/network/power services | Interactive native Duck Desktop |
| Installer Preview | disk installer, A/B layout, recovery and interrupted-update tests | Installable preview with tested rollback |
| Release Candidate | Secure Boot, signed updates/modules, SBOM/provenance, physical qualification matrix | Only the exact devices, firmware and capabilities tested |

No release is padded with empty data. ISO size follows actual bootable kernel, filesystem, applications, drivers, recovery and testable content.

## Cross-repository ownership

| Repository | Owns | DuckOS integration boundary |
|---|---|---|
| Reaper | language, native compiler, typed IR, DABI64 and system-runtime contracts | kernel/service source language and versioned ABI |
| Pytyliki | processor/system profiling and bounded measurements | read-only benchmark and evidence service |
| OPlague | read-only device/driver inspection, signatures, SBOM metadata | inventory and package-evidence service; never automatic driver mutation |
| VentuSample | offline audio/DSP engine | library and render-job boundary first; real-time audio only after service qualification |
| DuckOS | boot, kernel, memory, process, filesystem, driver manager, compositor, installer and release | integration owner and platform security boundary |

Submodule revisions move only in dedicated PRs after upstream compatibility tests. Any cross-repository ABI change includes owner, version, compatibility policy, tests and a migration note.

## Completion rule

A domain is complete only when its native implementation, negative tests, QEMU boot/runtime evidence, resource limits, security boundary and documentation agree. Hardware claims additionally require reproducible device/firmware test records. The roadmap status is an evidence index, not a substitute for code or test results.
