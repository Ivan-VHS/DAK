# DuckOS implementation status

Updated: 2026-11-23

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
- [ ] Audio engine and Wayland-compatible compositor; the native Tk settings panel remains a user-space utility, not a compositor-integrated system settings service.

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

## Deep settings and user-space tool suite — 2026-11-23

- [x] Versioned user-scoped settings store with atomic JSON replacement and validation.
- [x] Four independently configurable starter profiles and active-profile selection.
- [x] Bounded settings snapshots, audit journal, JSON import/export and rollback API.
- [x] Native Duck Desktop Settings tab with network, power, appearance, profile and history pages.
- [x] Searchable setting index with breadcrumb paths, scrollable category pages and live accent preview.
- [x] Draft-versus-saved state, field-group validation, apply/cancel/default actions and unsaved-change prompt.
- [x] IPv4/IPv6, prefix/netmask, gateway, DNS, DoH/DoT, proxy and MTU profile validation.
- [x] Read-only DNS and TCP connectivity test.
- [x] User-space toolbox: CSPRNG secret generation, text statistics, CSV inspection, encoding conversion, JSON/XML conversion, unit conversion, TLS verification, RSS/Atom parsing, SHA-256 and listening TCP-port inventory.
- [x] CLI entry points for settings profiles, export/import, network checks and toolbox utilities.
- [ ] Live host network adapter changes, temporary network apply/rollback and IP conflict detection.
- [ ] Hardware-backed battery health, charge limits, thermal policy, sleep and wake-lock control.
- [ ] Global theme/compositor integration, DPI enforcement and contrast certification.
- [ ] EFI/boot manager, filesystem repair, kernel updates, privileged driver/device control, packet capture, firewall/tunnel management, kernel-enforced sandboxing and secure free-space erase.

These settings are saved as desired user preferences only. The settings-store operation reports system_changes_performed=false. The project does not claim that saving a DHCP/static profile changes the host adapter, that saving a power profile changes the CPU/GPU, or that saved appearance tokens restyle the host compositor. See [Deep settings and user-space tools](DEEP_SETTINGS_AND_USERLAND_TOOLS.md).
