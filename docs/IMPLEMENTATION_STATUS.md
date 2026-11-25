# DuckOS implementation status

Updated: 2026-11-25

## Ecosystem source and interface integration — 2026-11-25

- [x] DuckOS pins Reaper, Pytyliki, OPlague and VentuSample as four independent Git submodules with exact commits and preserved upstream licenses.
- [x] Release ISO pipeline builds/tests the four host workbenches and packages source, notices and checksums; host binaries are not kernel executables.
- [x] Reaper consumes Pytyliki C ABI v1 through an explicit absolute library path and checks ABI version before calls.
- [x] Reaper validates OPlague device snapshot v1 and DuckOS hardware inventory v1 for read-only audit workflows.
- [x] Machine-readable integration graph and Node tests verify source pins, licenses, interface artifacts and maturity labels.
- [x] Reaper policy adapter for normalized OPlague GPU telemetry v1 validates provider/mode/bounds and preserves unknown readings as absent.
- [ ] Implement trusted native JSON ingestion that verifies OPlague schema and canonical digest before constructing normalized Reaper records.
- [ ] Add publisher/build provenance verification; SHA-256 is not a signature.
- [ ] Implement a VentuSample pack-v1 Reaper consumer; the current metadata interface remains specified-only.
- [ ] Connect peer workbenches to a native DuckOS process/package service only after scheduler, syscall, filesystem and kernel capability enforcement exist.

Peer applications and host tools remain user-space programs. None is a kernel module or an executable that the Stage 1 kernel can start.

## Kernel Runtime — x86-64 virtual-memory groundwork

- [x] Four-level 48-bit canonical page-table manager for 4 KiB leaves: create intermediate tables, map, unmap and translate.
- [x] User/kernel address split checks, bounded physical-address bits, W^X validation and optional per-page invalidation callback.
- [x] Host C tests cover user and kernel mappings, translation offsets, duplicate-map rejection, unmap, invalid addresses/flags and allocation failure.
- [ ] Connect the frame allocator and HHDM to a live kernel address space and preserve required Limine mappings.
- [ ] Add page-fault recovery, page-table reclamation, active TLB invalidation/shootdown, large pages and per-process address-space activation.
- [ ] No CR3 switch, user-mode entry, process isolation or scheduler is claimed by this groundwork.

## Newly specified contracts — 2026-11-25

- [x] DuckOS interaction and application ergonomics standard: normative requirements for motor/visual/cognitive interaction, keyboard, focus, accessibility, windowing, errors, recovery, privacy and usability evidence. This is a specification, not proof that native desktop services meet it.
- [x] BAV Security Bundle v1 JSON contract and schema: the .bav namespace is reserved for signed declarative antivirus policy bundles; signature verification, scanner execution, quarantine and enforcement are not implemented by the schema.
- [x] .bav / .bufspec namespace collision recorded for separate Reaper registry migration; no extension parser support is claimed.
- [x] Reaper Beelzebul 66-rule repository scanner and defense-context TSV inspected as separate specialist inputs; neither is represented as DuckOS endpoint protection.
- [ ] Re-verify the Java context-classifier source/test paths named in Reaper documentation before claiming that classifier is implemented or using it as a shipped DuckOS dependency.

## Mora host-native shell — 2026-11-25

- [x] Added a Qt 6 Widgets desktop executable as a host-native Mora surface; its windows are real top-level host windows, not HTML elements or WebView content.
- [x] Reused `mora/apps.json` for built-in apps and ecosystem workbench discovery; the native launcher does not execute manifest command strings.
- [x] Added local Poi draft persistence through `QSettings` and a user-selected, read-only folder listing in Abriganza.
- [x] Added an explicitly visual-only VentuSample waveform panel that states audio playback and DSP integration are unavailable.
- [x] Added a CMake target, headless native-window/navigation smoke test and dedicated Qt 6 CI workflow.
- [ ] Obtain a passing Qt 6 build and smoke-test run before marking the host-native shell build gate verified.
- [ ] Launch Mora inside a DuckOS user session after the process model, syscall ABI, filesystem, service supervisor, native input path and compositor exist.

The Qt application is native to the host OS. It is not a kernel-owned DuckOS compositor, window manager, system service or process launcher. The bootable Stage 1 image still halts before a user session.
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

- [x] x86_64 CPU exception IDT: vectors 0–31 have interrupt-gate descriptors, normalized assembly stubs and a fatal serial/framebuffer diagnostic path. Host tests validate descriptor fields and the C/assembly frame offsets; BIOS/UEFI QEMU now verifies the post-`lidt` marker. This does not enable maskable interrupts.
- [ ] Owned GDT, TSS and dedicated IST stacks for double fault/NMI; the current handlers still use the active boot stack.
- [ ] PIC/APIC setup, IRQ remapping, timer/keyboard routing and interrupt-safe scheduling.

- [x] Experimental x86_64 Stage 1 boot image (QEMU BIOS/UEFI verification passed): pinned Limine v12.11.1; DuckOS-owned freestanding entry; Boot Info v1 handoff validation; BIOS and UEFI QEMU boot gates; native monotonic 4 KiB physical-frame allocator over validated USABLE regions. The kernel allocates and clears one frame through HHDM and emits `DUCKOS_BOOT_OK stage=1`. CI run 45527148367 passed host CTests, freestanding ISO build, BIOS and UEFI QEMU boots; both serial logs report `DUCKOS_BOOT_OK stage=1`. This is not yet a running process/service OS session.
- [x] Host-tested frame allocator contract: alignment, reserved-range exclusion, minimum address, malformed/overlapping/overflowing map rejection and exhaustion.
- [ ] Reusable frame allocator/free path, page tables, MMIO and DMA.
- [ ] Actual preemptive scheduler, work stealing, fibers and OS-thread runtime.
- [ ] Shared-memory zero-copy IPC, wakeups and cancellation.
- [ ] PCI/PCIe/USB/ACPI enumeration and driver package parsing.
- [ ] Cryptographic driver signature verification and isolated driver loading.
- [ ] Sensor collection, hardware telemetry and DPC/ISR tracing.
- [ ] BLAKE3 hashing, persistent semantic graph, structural sharing and general CRDT synchronization.
- [ ] GPU command submission and accelerated compositor.
- [ ] Freestanding native Reaper compiler/backend and self-hosted compiler.
- [ ] Production boot chain and usable kernel remain incomplete: no reusable memory manager, interrupts, process model, syscall layer, driver runtime, filesystem, service supervisor or compositor is present.
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
- [ ] Production installer and hybrid USB deployment. The experimental ISO pipeline is documented separately in [BOOTABLE_IMAGE.md](BOOTABLE_IMAGE.md); it does not imply a disk installer or supported hardware matrix.
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
