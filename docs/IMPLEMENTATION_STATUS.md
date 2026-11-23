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

## Implemented host-side executable runtime

- [x] Bounded PE/DOS/ELF/Mach-O header inspection and architecture classification.
- [x] Private imported application store with ZIP path/size limits, per-file SHA-256 manifests and pre-launch integrity verification.
- [x] Windows host PE process creation, plus installed Wine and DOSBox adapter discovery on POSIX hosts.
- [x] Direct argv-based process creation with shell disabled, explicit launch approval, PID tracking and process termination.
- [x] Optional Linux bubblewrap filesystem/network namespace isolation for Wine/DOSBox; unisolated host launches require explicit approval.
- [x] QEMU guest disk registration with SHA-256 verification, snapshot-by-default boot and networking disabled by default.
- [x] Optional user-supplied DXVK archive installation into managed Wine prefixes with expected archive digest and installed-file verification.
- [x] Authenticated loopback API used by Mora Bridge; Windows CI executes a real PE host process.

These are host-side integrations. They do not provide kernel-level process isolation or prove that the DuckOS image boots.

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
- [ ] Native DuckOS process model, address spaces, syscall ABI, PE image loader and kernel-enforced capabilities.
- [ ] Package manager, init process tree, filesystem and installer.
- [ ] Audio engine, Wayland-compatible compositor, native settings applications and GPU-accelerated game compositor.
- [ ] Cross-architecture Windows user-mode binary translation; native Win32/NT runtime inside DuckOS.
- [ ] Direct3D 12 via vkd3d-proton and QEMU GPU passthrough.

## Evidence policy

A Reaper script passing on the reference runtime proves only that the script and its policy contract work on that runtime. It does not prove native code generation, privilege, device access, hard real-time latency or bootability.
