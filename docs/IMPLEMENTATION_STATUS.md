# DuckOS implementation status

Updated: 2026-11-25

## Implemented in Reaper source

- [x] Boot phase sequence validation and transition validation.
- [x] Signed-address range arithmetic, 64-byte frame arena and SoA budget calculations.
- [x] Deterministic ready-task selection by priority and deadline.
- [x] Deterministic least-loaded worker selection with bounded capacity.
- [x] Bounded FIFO message queue with explicit empty/full/backpressure states.
- [x] Byte-accounted UDB publication/consumption policy and high watermark.
- [x] Capability membership and child-set attenuation.
- [x] Untrusted/validated/quarantined input labels and effect-boundary policy.
- [x] Driver ABI descriptor, package metadata and resource/IRQ conflict policy.
- [x] Service restart decision with finite budget.
- [x] Content-addressed graph-reference shape and dependency validation.
- [x] Monotonic event journal sequence contract.
- [x] Deterministic last-writer-wins register merge.
- [x] CPU / accelerator / node-mesh policy selector and thermal profile.
- [x] Bounded telemetry history and warning/critical classification.
- [x] Tri-Color Duck palette, reduced-motion policy and frame-budget classification.
- [x] Reaper contract suite for tree-walk and VM execution, wired into GitHub Actions.

## Partial or external boundaries

- [ ] Real frame/page allocator, page tables, MMIO and DMA.
- [ ] Actual preemptive scheduler, work stealing, fibers and OS-thread runtime.
- [ ] Shared-memory zero-copy IPC, wakeups and cancellation.
- [ ] PCI/PCIe/USB/ACPI enumeration and driver package parsing.
- [ ] Cryptographic driver signature verification and isolated driver loading.
- [ ] Sensor collection, hardware telemetry and DPC/ISR tracing.
- [ ] BLAKE3 hashing, persistent semantic graph, structural sharing and general CRDT synchronization.
- [ ] GPU command submission and accelerated compositor.
- [ ] Freestanding native Reaper compiler/backend and self-hosted compiler.
- [ ] UEFI/BIOS bootloader, kernel entry point and bootable ISO/USB image.
- [ ] Process model, syscall ABI and kernel-enforced capabilities.
- [ ] Package manager, init process tree, filesystem and installer.
- [ ] Audio engine, Wayland-compatible compositor and native settings applications.

## Evidence policy

A Reaper script passing on the reference runtime proves only that the script and its policy contract work on that runtime. It does not prove native code generation, privilege, device access, hard real-time latency or bootability.


## Windows compatibility foundation — 2026-11-23

- [x] Bounded, read-only PE32/PE32+ parsing for COFF/optional headers, section records, machine type and subsystem.
- [x] Static import-directory parsing with bounds checks and imported DLL inventory.
- [x] Local SHA-256 report for inspected PE files.
- [x] Per-application prefix directory skeleton with versioned manifest and symlink-aware validation.
- [x] Static DLL search-path diagnostics and a machine-readable dry-run launch plan.
- [x] CLI commands for inspection, prefix creation/validation, compatibility diagnostics and capability status.
- [ ] PE image mapping, relocations, import resolution, TLS, SEH/VEH and x86/x64 ABI.
- [ ] Native process manager, NT syscall/object model, Win32 API and kernel-enforced sandbox.
- [ ] DirectX/Vulkan, audio, input, network, device and launcher bridges.

The implemented foundation never executes a Windows binary and does not install drivers or runtime DLLs. See [Windows compatibility](WINDOWS_COMPATIBILITY.md) for the full 66-point traceability table and exact CLI use.


## DuckBridge runtime orchestration — 2026-11-23

- [x] PE inspection reuses the shared PE32/PE32+ parser, including section and import metadata.
- [x] ELF header inspection reports architecture, bitness and endianness.
- [x] Read-only runtime discovery for Wine, Proton, CrossOver, Bottles, Box64 and supported QEMU user-mode tools.
- [x] Purpose-aware backend selection and structured argv/environment planning for supported targets.
- [x] Versioned JSON plan schema and synthetic-file/runtime-stub test coverage.
- [ ] Native target process creation, compatibility-prefix management for third-party runtimes, sandbox enforcement and graphics/audio translation.

The runtime inventory and plan generator do not invoke a discovered runtime or target. Both execution_started and prefix_created are false in the versioned plan.


## Release packaging and deployment planning — 2026-11-23

- [x] Deterministic release component-bundle packaging from a validated system manifest.
- [x] Component files are copied and re-hashed during packaging to detect changes in the source tree.
- [x] SHA-256 inventory for release metadata and component payloads.
- [x] Optional Ed25519 signing of release metadata with OpenSSL.
- [x] Archive verifier for canonical paths, unsupported links, duplicate files, expanded-size limits, manifest digest, component hashes and checksum inventory.
- [x] Optional Ed25519 signature verification against an externally supplied public key.
- [x] Non-destructive GPT deployment layout planner with EFI, two system slots, recovery and user data.
- [x] USB, PXE, UEFI HTTP Boot/iPXE and cloud deployment plan targets.
- [x] CLI entry points: `build-release`, `verify-release` and `deployment-plan`.
- [x] JSON schemas for release metadata and deployment plans.
- [ ] Real ISO and hybrid USB image assembly, including an actual firmware-compatible EFI bootloader.
- [ ] PXE/HTTP boot server provisioning, DHCP/TFTP configuration, native boot handoff and boot-chain signature enforcement.
- [ ] Physical disk installer and safe destructive-write workflow.
- [ ] Native A/B slot selection, boot-success confirmation and automatic rollback.
- [ ] Cloud disk-image conversion and validation.
- [ ] Firmware, VM and hardware boot qualification.

The release bundle is a component archive, not a bootable image. Deployment plans are dry-run descriptions and do not write disks. HTTPS transport does not by itself establish UEFI Secure Boot. The Secure Boot plan therefore remains `ready: false`, and the cloud-format list records intended targets rather than completed conversions. See [DEPLOYMENT.md](DEPLOYMENT.md) for commands, boundaries and signing-key handling.


## Mora extended application suite — 2026-11-23

- [x] Register 13 additional app identities in the Mora launcher, app registry and shared panel router.
- [x] Provide local profile lists with safe text rendering and bounded entries for Orriganize, Olaab, Love-IL, Poi, Poi-2, Po-2 and GameCharager.
- [x] Provide SetupUP theme onboarding and a local completion marker.
- [x] Provide Abriganza archive filename/size inspection without extraction.
- [x] Provide Concrete Thump BPM/swing profile controls without audio playback or synthesis.
- [x] Provide Seu-Beu's user-operated sharing checklist without claiming encryption or identity verification.
- [x] Reuse local PE/ELF header inspection and SHA-256 helpers in GameCharager and EXEdotEXE without executing targets.
- [ ] Native implementations of the proposed DAK services, system-wide persistent storage, archive extraction, native audio, GPS/navigation, game process creation, OS installation and kernel-enforced capabilities.

These are partial browser-shell features. The new DAK package catalog remains at design maturity and does not indicate that the corresponding native services ship in an OS image.


## Duck Desktop optimizer — 2026-11-23

- [x] Read-only Desktop/Рабочий стол inventory, item count and temporary-name hints.
- [x] Ten-item default clutter threshold and machine-readable audit report.
- [x] Explicitly confirmed move-to-Inbox operation for regular files, with collision-safe names and no deletion.
- [x] Current-user startup-folder inventory and reversible disable/restore on Windows and Linux.
- [x] Windows HKCU Run inventory and backup-before-disable / restore behavior.
- [x] Bounded process and memory snapshot; optional psutil enrichment.
- [x] Native Tk user-space maintenance window and `duckos desktop` CLI.
- [x] Reaper desktop policy contract for allowed actions and clutter threshold.
- [ ] Production Duck compositor, native window manager, true virtual workspaces and shell integration.
- [ ] Native process manager, tray/notification services, capability broker and kernel-enforced resource scheduling.
- [ ] MacOS LaunchAgents integration and machine-wide/service startup management (intentionally outside this module's scope).

The native Tk tool is a user-space utility. It is not a compositor, a boot-time shell, a kernel service or proof of a bootable DuckOS image. The Mora panel only links to the native command; it does not access host resources from browser JavaScript. See [Duck Desktop optimization](DESKTOP_OPTIMIZATION.md).


## Unified capability completeness gate — 2026-11-23

The shared [Engineering Evolution and Capability Completeness Standard](ENGINEERING_EVOLUTION_FRAMEWORK.md) applies to every Mora and DuckOS capability. A feature is complete only for its explicitly declared scope and only when source, tests, CI and documentation agree.

- Mora browser-shell behavior, local preferences and catalog entries are tracked separately from native DuckOS services.
- User-space maintenance utilities are not kernel services, a compositor, a bootloader, a driver manager or proof of a bootable operating-system image.
- Catalogued applications and proposed DAK services remain specifications until executable implementations and integration tests exist.
- Kernel, boot, process, filesystem, compositor, driver and capability-enforcement work stays partial or planned until the relevant native code and target-platform tests are present.
- Each release review must trace requirement → design → source → tests → CI → documentation → versioned contract and retain rollback or recovery evidence for risky changes.

The existing implemented/partial boundary list above remains authoritative. This standard does not promote any partial or planned subsystem automatically.


## First native-systems implementation slice — 2026-11-25

The branch `feat/kernel-syscall-process-contracts-v1` adds Reaper-authored, executable policy/state contracts for process identity, syscall admission, W^X virtual mappings, interrupt routing, process-bound IPC endpoints, BAV policy, service lifecycle, native-window state, package transactions and Limine memory-map type translation.

- [x] Process descriptor and generation-handle validation, lifecycle transitions and child capability attenuation model.
- [x] Versioned syscall descriptor table, caller-handle validation, bounded argument/payload metadata and BAV admission model.
- [x] Virtual mapping metadata validation with 4 KiB alignment and W^X policy.
- [x] Interrupt route, mask, priority and nesting policy.
- [x] Capability-gated bounded IPC endpoint and sequence model.
- [x] BAV deny-by-default rule matching, trust-state checks and sequence audit model.
- [x] Service dependency, health and finite restart policy.
- [x] Native desktop window/display state, keyboard movement and focus-order policy.
- [x] Package admission and reversible inactive-slot transaction model.
- [x] Limine memory-map type conversion with conservative treatment of loader/module ranges.
- [x] Reaper contract fixtures for the new models and CI invocation through tree-walk and VM.
- [ ] Execute the updated Reaper suite on the exact PR head and retain successful CI evidence.
- [ ] Implement a freestanding Limine entry point and serial boot marker.
- [ ] Implement a physical page-frame allocator, page tables and TLB management.
- [ ] Implement GDT/IDT/exception entry, timer and interrupt-controller operations.
- [ ] Implement actual context switching, process address spaces and syscall entry/return.
- [ ] Implement real cross-process IPC memory/wakeup/cancellation.
- [ ] Enforce BAV in a native syscall/service broker and add actual process sandboxing.
- [ ] Implement init/service process supervision, VFS/block/network/audio/graphics services.
- [ ] Implement native window/input/display compositor and package installation/runtime.
- [ ] Extend Reaper's native compiler to records, bounded collections, unsigned target types, freestanding runtime and direct object/ELF output.

**Scope warning:** the checked Reaper modules in this branch are deterministic contract models. They do not install IDT/GDT, change CR3, write page tables, allocate physical pages, enter kernel privilege, switch CPU contexts, access devices, create native processes, launch applications or build a bootable image. Do not promote the existing `[ ]` native milestones until those operations and their target tests exist.
