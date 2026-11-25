# DuckOS native implementation roadmap

**Reviewed:** 2026-11-25  
**Product:** DuckOS operating-system foundation; Mora has a browser reference preview and a host-native Qt 6 Widgets desktop application.  
**Source of truth:** native source, Reaper contracts, tests, CMake targets, CI and the versioned system-capability profile.

## Product maturity contract

DuckOS currently combines three distinct surfaces. They must never be conflated:

1. **Mora host surfaces:** a Qt 6 Widgets host-native application plus a retained browser reference preview. The native app uses host OS top-level windows but cannot enforce DuckOS kernel privileges or start DuckOS processes.
2. **Reaper reference contracts:** executable policy models for boot sequencing, memory arithmetic, scheduling decisions, IPC admission, capabilities, service restart and telemetry classification. Passing these tests proves policy behavior on the Reaper reference runtime only.
3. **Native foundation:** a host-buildable C11 boot-handoff validation library plus an experimental x86_64 freestanding Stage 1 kernel and reproducible Limine BIOS/UEFI ISO pipeline. The Stage 1 target is not yet a process runtime, scheduler, driver stack or bootable desktop OS.

| Maturity | Required evidence |
|---|---|
| Delivered | Native/source implementation, focused tests and required CI on the supported target |
| Partial | A bounded subset exists; every missing primitive and platform limitation is explicit |
| Planned | No implementation on the target runtime; dependency and measurable acceptance test are recorded |
| Not applicable | A capability is outside the approved product scope, with rationale |

A policy model, browser preference, catalogue entry, manifest, generated archive or host-side unit test cannot be relabelled as a native kernel, driver, boot service or physical-device capability.

## Current delivered foundation

| Area | Delivered scope | Explicit boundary |
|---|---|---|
| C11 build | Host CMake/CTest plus freestanding x86_64 kernel target | The freestanding entry is a narrow C11 platform bridge; Reaper is not yet a freestanding kernel compiler |
| Boot handoff | Versioned Boot Info v1, Limine BIOS/UEFI handoff and native kernel entry | Limine is a pinned third-party bootloader; no in-house UEFI loader or Secure Boot policy |
| Validation and early memory | Boot Info and memory-map validation; bounded single-core 4 KiB physical-frame extent allocator with contiguous alignment, release, coalescing and HHDM allocate/free/reuse smoke test | Page tables, heap, SMP locking, reclaim and virtual-memory manager remain pending |
| Reaper contracts | Boot phases, resource budgets, scheduling/IPC policies, capabilities and service restart decisions | Reference-runtime policy, not kernel enforcement |
| Mora | Qt 6 Widgets host-native shell, local app catalogue, native host windows and a retained browser reference preview | Not yet a kernel-launched DuckOS desktop or privileged shell |
| Release tooling | Deterministic component archive, SHA-256 inventory, optional Ed25519 manifest signature, non-destructive deployment planning and an experimental x86_64 Stage 1 ISO pipeline | No disk installer, production image, verified boot chain or supported hardware matrix |

## Native implementation sequence

### D0 — Boot information and host conformance

**Status: Delivered for the host-side contract.**

- Preserve the v1 boot handoff ABI, fixed widths, record version and structure size.
- Reject malformed kernel/initramfs ranges, overlapping regions, invalid framebuffer extents and unsorted/overlapping memory-map records.
- Keep status codes deterministic and test malformed input boundaries.

**Exit evidence:** CMake build and CTest pass on supported host CI; invalid structures are rejected without out-of-bounds access. This stage does not claim UEFI or physical boot.

### D1 — Freestanding target and firmware handoff

**Status: Partial — experimental x86_64 Limine Stage 1.**

- First target selected: x86_64 with BIOS and UEFI firmware through the pinned Limine v12.11.1 boot protocol.
- A freestanding GNU x86_64 ELF profile, high-half linker layout, entry symbol, Limine stack request and COM1 diagnostic path are present.
- The kernel receives Limine memory-map, HHDM, executable-address, framebuffer and firmware-type responses, translates the memory map into Boot Info v1 and rejects unsupported or inconsistent handoff data.
- The Limine loader remains an attributed, pinned third-party component; this milestone does not implement an in-house UEFI application or bootloader.
- Secure Boot signing/enrolment, verified boot policy, AP startup and other firmware services remain separate future work.

**Stage-1 boot evidence: passed.** The freestanding kernel and ISO build, host Boot Info and frame-allocator CTests, ISO checksum, and pinned QEMU BIOS plus OVMF UEFI runs all succeeded. Both serial logs contain `DUCKOS_BOOT_OK stage=1`; see [verified workflow run](https://github.com/Ivan-VHS/DuckOS/actions/runs/45527148367). The wider D1 milestone remains partial until reusable memory management, page tables, interrupt/timer setup and a supported freestanding Reaper target are implemented and verified.

### D2 — Physical memory and virtual address spaces

**Status: Partial — reusable single-core physical-frame allocator; virtual memory is pending.**

- Implement a physical page-frame allocator from the validated firmware memory map.
- **Delivered in Stage 1:** bounded freestanding 4 KiB extent allocation from validated USABLE regions, a 1 MiB low-memory floor, power-of-two alignment for contiguous runs, tracked release, adjacent-range coalescing and HHDM allocate/clear/release/reallocate verification. It remains single-core; there is no page-table construction, virtual-memory manager, heap or SMP locking yet.
- Reserve firmware, kernel, initramfs, framebuffer, ACPI and boot-service regions before allocating.
- Add page-table construction, mapping permissions, guard regions, canonical-address checks and safe unmap/free behavior.
- Specify ownership, alignment, overflow, fragmentation and allocation-failure semantics.
- Keep DMA/IOMMU memory separate from ordinary pageable allocations.

**Exit evidence:** allocator invariants under randomized allocation/free sequences; page-table tests in emulator; permission-fault tests; sanitizer/UB checks for host-testable helpers; memory-map fuzzing; no reservation overlap.

### D3 — Interrupts, clocks and execution scheduler

**Status: Planned; policy selector only exists in Reaper contracts.**

- Install exception and interrupt descriptor tables with explicit error-code handling.
- Add a calibrated monotonic timer source and an interrupt-safe event path.
- Implement context save/restore and preemptive scheduling only after stack, address-space and interrupt invariants are validated.
- Define task lifecycle, priority/deadline semantics, bounded run queues, idle behavior and CPU affinity.
- Add work stealing only after single-core scheduling is correct and multicore memory ordering is specified.

**Exit evidence:** emulator tests for timer ticks, task preemption, fault isolation and deterministic scheduler cases; stress tests across multiple runnable tasks; latency measurements with hardware/emulator details.

### D4 — Processes, syscalls and capability enforcement

**Status: Planned; capability policy exists only as a Reaper reference model.**

- Define a versioned syscall ABI and stable userspace calling convention.
- Create process address spaces, isolated stacks, handle tables and bounded resource accounting.
- Enforce capabilities at the kernel boundary, including inheritance attenuation, revocation and audit.
- Validate user pointers and lengths before kernel access; never trust a userspace “validated” flag.
- Implement process lifecycle, exit status, wait/reap and safe cancellation.

**Exit evidence:** negative tests proving denied syscalls cannot cross capability boundaries; user-pointer fuzzing; process isolation tests; resource-exhaustion tests; ABI compatibility fixtures.

### D5 — IPC and service supervision

**Status: Planned; bounded queue/UDB policy is a Reaper contract only.**

- Implement a kernel-owned IPC endpoint and bounded message queues.
- Add sender identity, capability checks, backpressure, cancellation and bounded wait semantics.
- Add shared-memory transport only with explicit mapping ownership, page pinning, lifetime and revocation.
- Implement service supervision with restart budgets, crash-loop backoff and observable terminal failure state.
- Define journal durability requirements before persisting events.

**Exit evidence:** cross-process tests, queue saturation/backpressure tests, malformed message fuzzing, cancellation/race tests and crash/restart integration scenarios.

### D6 — Hardware discovery, drivers and device isolation

**Status: Planned; descriptor and conflict policy only.**

- Implement bounded PCI/PCIe and ACPI enumeration for the first declared target.
- Define driver package format, architecture/ABI compatibility and a cryptographic trust chain.
- Verify package signatures from a pinned trust root; a caller-provided boolean is not verification evidence.
- Load drivers in an isolated address space with explicit device/resource capabilities.
- Add interrupt routing, DMA/IOMMU enforcement and safe device teardown only after the memory and process stages pass.

**Exit evidence:** emulator/device fixtures, signed and invalid package tests, resource-conflict tests, isolation tests, driver crash recovery and hardware qualification for each supported device. No blanket “driver support” claim from inventory alone.

### D7 — Persistent storage, filesystems and package lifecycle

**Status: Planned.**

- Select a first filesystem and define crash-consistency and recovery expectations.
- Implement block-device abstraction, bounded reads/writes, cache flush semantics and error propagation.
- Add a package format with hashes, dependency graph, trust metadata and atomic installation/rollback.
- Use content-addressed storage only after hash algorithm, versioning, integrity and migration contracts are fixed.

**Exit evidence:** filesystem image tests, power-loss/fault injection, corruption detection, package-signature verification, atomic install/rollback tests and recovery from interrupted transactions.

### D8 — Native desktop, input, graphics and audio

**Status: Planned for the DuckOS kernel session. A separate host-native Qt 6 Widgets Mora application now exists; its build gate is pending CI evidence.**

- Keep the host-native Mora application as a separate delivery surface while the kernel session is unavailable. It uses host OS top-level windows and must not be packaged or described as a kernel service.
- Preserve the Figma composition: compact system top bar, left navigation rail, black radial/folded workspace, restrained yellow selection, application catalogue and bottom dock. Application windows remain independently movable and focusable host windows.
- Do not route shell launch actions through manifest command strings. A later DuckOS launcher must resolve installed trusted binaries and obtain capabilities through the native broker.
- Choose a native display and windowing architecture for the initial hardware target.
- Implement graphics buffer ownership, input event routing, focus, accessibility and display-mode failure recovery.
- Add font shaping and text input only with a defined Unicode and fallback policy.
- Treat audio engine/device scheduling as a separate bounded subsystem.
- Apply [DuckOS interaction and ergonomics standard](ERGONOMICS_AND_INTERACTION_STANDARD.md) to Mora and native apps: keyboard-complete primary workflows, visible focus, semantic accessibility tree, text scaling, reduced motion, recoverable dialogs, saved workspace geometry and safe display migration.
- Keep the Mora visual system as a design reference, not as proof of compositor or GPU implementation.

**Exit evidence:** emulator screenshot capture; keyboard and assistive-technology conformance tests; display-loss and DPI-change recovery; touch/pointer target tests; reduced-motion and text-scaling tests; P50/P95/P99 input-to-feedback and frame-time measurements on named targets; supported hardware matrix.

### D9 — Installer, image assembly and release qualification

**Status: Partial — experimental x86_64 hybrid ISO build and emulator boot gate; installer and production qualification remain planned.**

- Build a reproducible x86_64 BIOS/UEFI Stage 1 ISO from the pinned Limine bootloader, DuckOS ELF entry and explicit boot configuration; attach a SHA-256 sidecar.
- Boot-test the image in QEMU BIOS and OVMF UEFI in CI, retaining serial logs and the ISO artifact.
- Add a native installer, disk writes and USB provisioning only behind explicit operator approval and destructive-operation preview.
- Add verified boot only after signing identity, key custody, revocation and recovery policy are implemented.
- Implement A/B slot update, boot-success confirmation and recovery only after filesystem and boot stages are qualified.
- Keep cloud targets out of the release matrix until a real format conversion and target boot test exist.

**Stage-1 image exit evidence: passed.** A reproducible ISO, SHA-256 verification, BIOS and UEFI emulator boot, and QEMU serial logs are published in the [verified Stage 1 workflow run](https://github.com/Ivan-VHS/DuckOS/actions/runs/45527148367). Production release additionally requires USB/installer qualification, a supported hardware matrix, verified signing policy, installation rollback and recovery drill.

### D10 — BAV malware inspection and policy service

**Status: Planned; the .bav v1 bundle contract and JSON Schema are specified only.**

- Reserve the .bav extension exclusively for Beelzebub AV signed declarative security bundles. The earlier OS(2).txt buffer-allocation proposal must use the distinct .bufspec extension; update Reaper's registry only in a separate reviewed change. Reaper's existing duckos.bav.defense-context.v1 identifier and defense-context.v1.tsv file are a metadata vocabulary, not .bav bundle files.
- Preserve Reaper's existing Beelzebul 66-rule read-only repository scanner as a separate developer/supply-chain assurance tool. Its report must not be represented as a host endpoint scan. Sensitive-context tags from the TSV taxonomy must never affect malware verdicts or privileged response actions.
- Implement a trust verifier using a device-owner-controlled trust root, Ed25519 signatures over RFC 8785 canonical JSON, signer revocation, expiry checks and monotonic per-publisher/channel sequence tracking.
- Implement a read-only user-space scan worker with bounded file sizes, parse depth, archive expansion, time, memory and concurrency. Treat unsupported or incomplete inspection as unknown, never as clean.
- Implement deterministic hash/static-rule matching and a separate, versioned interface for future heuristic engines. Do not execute inspected content or rules.
- Add reversible quarantine with object identity, content hash, atomic transaction, ACLs, restore collision handling and explicit user approval.
- Add a policy broker only after D4 capability enforcement, D5 process/IPC supervision and D7 persistent storage provide verified native primitives. On-access scanning and execution/install blocking remain unavailable until that broker and filesystem/process hooks are real.
- Integrate Mora as a status and approval surface only. Do not present a shell control as protection when the scanner, trusted bundle or native enforcement broker is absent.

**Exit evidence:** positive and negative Ed25519 fixtures; invalid/unknown/revoked signer tests; expiry and clock-uncertainty tests; anti-rollback and explicit recovery tests; malformed/oversized bundle fuzzing; deterministic rule fixtures; archive-bomb and parser-timeout tests; path/symlink/TOCTOU tests; quarantine interruption/integrity/restore tests; capability-denial and worker-isolation tests; queue/memory-pressure recovery; and proof of no network egress by default.

D10 depends on the native process, capability, IPC, storage and recovery gates. Shipping the schema alone does not make BAV a working antivirus.

## Cross-cutting engineering gates

Every native stage must have:

- versioned interfaces and migration policy;
- bounded input, memory, CPU and retry budgets;
- unit, property, fuzz and negative-case tests appropriate to the primitive;
- CI build/test and sanitizer coverage where applicable;
- fault-injection and rollback/recovery behavior for state-changing operations;
- security review for privilege, device, package and trust-boundary changes;
- documentation updates tied to the exact implementation commit and CI run.

## Current non-goals

A hosted web service, remote orchestration control plane, automatic driver installation, arbitrary shell execution, unattended destructive disk writes and unsupported cloud deployment are not implied by the current DuckOS product. Add them only through an explicit product decision, threat model, owner and acceptance plan.

## Release rule

Do not claim DuckOS is a complete or usable desktop operating system until D1 through D9 prerequisites for the declared target have passed their target-specific acceptance gates. The x86_64 Stage 1 image now boots in QEMU BIOS and UEFI, but it halts after validated Boot Info v1 handoff and does not yet run a scheduler, processes, services or Mora.
