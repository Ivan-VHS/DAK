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
- [ ] GPU command submission, DRM/KMS and accelerated compositor; the initial X11 compositor uses XRender.
- [ ] Freestanding native Reaper compiler/backend and self-hosted compiler.
- [ ] UEFI/BIOS bootloader, kernel entry point and a self-hosted DuckOS kernel image; a Debian Live userspace image recipe is now present.
- [ ] Process model, syscall ABI and kernel-enforced capabilities; userspace process supervision and a privileged UID capability broker are implemented separately.
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


## Illidia game library and launcher — 2026-11-23

- [x] Versioned per-user game library with add, list and remove operations.
- [x] PE/ELF executable validation before a game is registered.
- [x] Real process launch for native matching-architecture ELF targets and detected Wine, Proton, CrossOver or Bottles backends.
- [x] Per-game compatibility-data directories for Wine and Proton, with WINEPREFIX or STEAM_COMPAT_DATA_PATH passed to the runtime.
- [x] Argument-vector process creation with shell execution disabled.
- [x] Optional GameMode and MangoHud wrappers and opt-in Proton WineD3D/esync/fsync switches.
- [x] Launch timestamps, optional exit-code collection and versioned library/launch schemas.
- [ ] Native NT/Win32 process execution, kernel-enforced process isolation and a native authenticated Mora host service.
- [ ] Automatic game/runtime installation, cloud saves, clip capture, achievements and native session Do Not Disturb integration.

Illidia starts external runtimes; it does not replace Wine/Proton or guarantee per-game graphics, DRM or anti-cheat compatibility. The launch tests use synthetic PE files and temporary runtime stubs, not commercial games.


## Mora OS shell integration — 2026-11-23

- [x] Reaper contract for window geometry, lifecycle transitions, workspace visibility, focus and z-order.
- [x] Reaper contract for desktop workspaces, session metadata, capability-gated application launch and allowlisted commands.
- [x] Reaper contract for bounded desktop notifications, monotonic ordering and unread state.
- [x] Mora virtual workspaces, workspace-local window visibility, minimize/maximize/restore controls and persistent local workspace selection.
- [x] Ctrl+K command palette for application search and allowlisted shell commands; arbitrary command/shell execution remains denied.
- [x] Searchable 20-direction engineering matrix with explicit partial/specified/planned maturity labels instead of simulated completion percentages.
- [x] Read-only Python host status, application catalogue validation and shell readiness CLI.
- [x] Python shell host/catalogue/CLI tests and Reaper window/desktop/notification contract assertions.
- [ ] Native Wayland/X11 compositor, display server, native window manager and kernel session manager.
- [ ] Privileged process/capability broker, native lock screen, power management, system terminal and real hardware telemetry providers.

The current Mora user interface is a browser/PWA shell. Reaper scripts define testable OS policy on the reference runtime; the Python adapter only inspects host metadata and the application catalogue. Neither constitutes a native compositor or kernel service. Reaper contract CI tests policy execution on its tree-walk and VM reference engines; separate host/hardware evidence is required for future native bring-up.


## Native Mora compositor, host broker and Live image — 2026-11-23

- [x] Native X11 compositor/window manager in C using X Composite, XDamage, XRender and XFixes; basic frame decorations, focus, title dragging, EWMH client list and close/minimize shortcuts.
- [x] Native compositor build and Xvfb startup/self-test in CI.
- [x] POSIX process supervisor with fixed application registry, independent process groups, UID/GID drop for root-hosted child processes, session listing and bounded stop escalation.
- [x] Capability-checked native host broker using Unix socket peer credentials (SO_PEERCRED), per-UID grants, root ownership/0600 policy checks and a loopback-only bearer-token bridge.
- [x] Controlled diagnostic terminal with fixed argv allowlist, per-command timeout, output cap and caller-UID execution; no generic shell endpoint.
- [x] Linux driver-module inventory/load path for allowlisted graphics, audio, network and device modules, plus the existing read-only PCI/USB inventory.
- [x] Optional live Reaper bridge through `reaper.runtime.Interpreter`, with four allowlisted policy entry points and bounded execution quotas.
- [x] Mora Native Host panel for host status, device/driver inventory, managed sessions, Reaper status and allowlisted diagnostics.
- [x] Debian Live build recipe packaging the X11 compositor, Mora, host service and X session.
- [ ] Wayland compositor, DRM/KMS renderer, GPU command scheduler, modern multi-monitor/resizing/colour management and accelerated rendering.
- [ ] DuckOS-owned graphics/audio/network/USB/NVMe driver source, signing, isolation and hardware qualification; current module operations reuse the Linux host kernel's drivers.
- [ ] Kernel scheduler, address spaces, syscall ABI, kernel-enforced capabilities, cgroups/namespaces sandbox and native process isolation.
- [ ] DuckOS UEFI entry point, freestanding native Reaper backend, physical memory manager and self-hosted kernel; the Live ISO recipe uses a Debian Linux kernel.
- [ ] Actual release ISO/USB image built and boot-tested on target hardware; CI validates the compositor under Xvfb, not a complete hardware boot.

The C compositor is a real X11 userspace window manager/compositor, not a Wayland or DRM/KMS implementation. The host broker is a privileged userspace service with explicit UID policy and process identity dropping; it is not a kernel reference monitor or a general-purpose security sandbox. The image recipe creates a bootable Linux-based DuckOS userspace image, not a new DuckOS kernel image. See [Native runtime](NATIVE_RUNTIME.md) for interfaces, setup and exact limitations.
