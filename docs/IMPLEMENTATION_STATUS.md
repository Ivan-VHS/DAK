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

## Native transition architecture baseline — 2026-11-23

- [x] One coordinated architecture specification covers all eleven Mora-to-DuckOS workstreams.
- [x] Shared contracts defined for process identity, capabilities, IPC, service lifecycle, intents, approvals, audit, desired state, provenance and resource budgets.
- [x] Dependency-gated implementation programme and per-workstream acceptance criteria documented.
- [x] CI, security testing, emulator/hardware evidence and release requirements documented.
- [ ] Native implementation of the new architecture components.
- [ ] Emulator validation of native boot, process isolation, update/recovery and device paths.
- [ ] Physical-hardware validation and release image.

The architecture baseline is documentation and planning work only. It does not change any subsystem from specified or contract-tested to native-implemented. Existing Reaper policies, Python host tools and browser-shell features retain their previously documented maturity.


## Illidia universal game launcher — 2026-11-23

- [x] Local SQLite library with source-aware records, tags, metadata, launch profile and indexed search fields.
- [x] Read-only Steam appmanifest/library-folder discovery.
- [x] Read-only Epic Games Launcher .item manifest discovery with install-root path containment.
- [x] Read-only GOG goggame-*.info discovery with primary play-task selection.
- [x] User-selected custom executable scanning and manual registration.
- [x] Local JSON library import/export and missing-install detection.
- [x] Per-game argv, working directory, runtime command, prefix and environment profile.
- [x] Automatic and named Wine/Proton/CrossOver/Bottles/QEMU selection through DuckBridge ready plans, with explicit command override.
- [x] Windows Authenticode query; unknown/unavailable signature state on platforms without the verifier.
- [x] SHA-256 fingerprinting and digest-scoped first-run approval for unsigned/unverified direct binaries.
- [x] Direct host process launch with shell=False, separate process group, log capture and stop request.
- [x] Post-hook SHA-256 recheck before process creation; abort when a pre-launch hook replaced the approved executable.
- [x] Store URI handoff is recorded as delegated, not confused with the URI-handler process.
- [x] Official Steam/Epic/GOG launch URI delegation.
- [x] Mora Illidia panel updated to remove fictional demo games and disclose the host-tool boundary.
- [ ] Authenticated native DuckOS Illidia broker and browser IPC integration.
- [ ] Kernel-enforced per-game sandbox, process handles and stable process-generation tracking.
- [ ] Provider-specific Battle.net/EA manifest adapters and session APIs.
- [ ] Cloud-save sync/conflict resolution, achievements and clip-session integration.
- [ ] Native compositor/window-mode integration and validated per-device performance profiles.

The current implementation is a Python host tool, not a native DuckOS daemon. Store-delegated launch sessions are owned by the store client and cannot be fully supervised by the URI opener. Direct process tracking is best effort pending a native process manager. See [Illidia game launcher](ILLIDIA_GAME_LAUNCHER.md) and [tests](../tests/test_illidia.py).
