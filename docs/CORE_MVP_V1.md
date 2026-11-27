# Dak core subsystem MVP v1

Updated: 2026-11-25

## Purpose

This change adds forty deterministic Reaper contracts across the ten core subsystem groups requested for Dak. It gives the project a consistent, testable policy boundary before those decisions are wired to privileged kernel mechanisms.

The contracts run on Reaper's reference runtime. They validate descriptors, enforce deterministic admission decisions, reject invalid state transitions and bound resource requests. They do **not** create processes, map pages, mount filesystems, encrypt blocks, send packets, load drivers, submit GPU work, schedule audio interrupts or enforce MAC from ring 0.

## Delivery matrix

| Area | Reaper contract module | MVP coverage |
|---|---|---|
| Process lifecycle | `dakos/kernel/process.rpr` | Descriptor validation, child capability attenuation, lifecycle transitions, CPU/RAM limits, graceful-stop deadline |
| Virtual memory | `dakos/kernel/vm.rpr` | User address bounds, page mapping permissions, demand-fault action, swap-slot metadata, safe deduplication candidate |
| VFS and snapshots | `dakos/storage/vfs.rpr` | Path traversal rejection, FAT32/ext4/NTFS mount metadata, capability-gated access, snapshot record validation |
| Network | `dakos/network/stack.rpr` | TCP/UDP endpoint metadata, deny-by-default firewall rule evaluation, DNS query bounds, VPN profile validation |
| Graphics | `dakos/graphics/compositor.rpr` | Framebuffer geometry, monitor bounds/scaling, Vulkan/OpenGL/framebuffer preference, frame-budget decision |
| Audio | `dakos/audio/pipeline.rpr` | Sample-rate/format/period validation, MIDI channel event bounds, spatial-mix budget |
| Security | `dakos/security/mac.rpr` | MAC rule evaluation, trust-label transitions, fail-closed secure-boot gate, TPM evidence shape, AES-256 profile metadata |
| Platform and device classes | `dakos/platform/targets.rpr` | Architecture recognition, primary/compatibility track, package architecture matching, PCI/USB-C/Bluetooth/Wi-Fi/NVMe/GPU/audio class taxonomy |
| System services | `dakos/services/init.rpr` | Service-unit limits, dependency-aware start decision, graceful shutdown deadline, bounded cron fields |
| Windowing and accessibility | `dakos/ui/accessibility.rpr` | Tiled/floating/maximized/fullscreen geometry, scale/reduced-motion/contrast/screen-reader/keyboard profile |

The forty exported functions are exercised by `core_mvp_tests.rpr` in both the Reaper tree-walk and VM CI runs.

## Platform policy

- `x86_64` is the primary native development, build, emulator and release target for both Intel and AMD processors. The target is vendor-neutral within the x86-64 ISA.
- `elbrus` remains a recognised compatibility track. It is not removed from architecture policy or package metadata.
- A package for a different ISA is rejected unless an explicit translation layer exists. No translation layer is implied by this contract.
- The current boot image remains the existing experimental x86_64 Limine Stage 1 image. No Elbrus boot image, compiler backend or physical-hardware qualification is claimed by this change.

## Explicit implementation boundaries

| Requested feature | What this MVP delivers | What remains native work |
|---|---|---|
| Processes and sandboxing | Process metadata/lifecycle contract, capability attenuation and resource limits | Ring-3 address spaces, syscall ABI, scheduler context switch, kernel-enforced sandbox and reaping |
| Paging and swap | Address/mapping checks, fault routing and swap-slot metadata | Page tables, page allocator free path, TLB shootdown, swap I/O, page deduplication engine |
| Filesystems and encryption | Mount/access/snapshot contracts and AES-256 key-reference profile | FAT32/ext4/NTFS implementations, journaling, block I/O, cryptographic engine, key storage and rotation |
| TCP/IP, DNS, firewall and VPN | Bounded transport/DNS descriptors, ordered firewall policy and VPN metadata | NIC drivers, Ethernet/IP/TCP/UDP code, DNS wire parser/resolver, firewall hooks, WireGuard/IKEv2 engine |
| Graphics | Framebuffer geometry, monitor layout and backend selection policy | Native compositor, input stack, OpenGL/Vulkan loader, GPU drivers, presentation and hotplug |
| Audio | Format/period/MIDI/spatial admission | Device drivers, mixer, ALSA/PulseAudio compatibility, realtime scheduling, MIDI transport |
| Security and TPM | MAC decisions and evidence/profile validation | Ring-0 MAC hooks, signature verification, authenticated measured boot, TPM command transport and key sealing |
| Drivers | Device-class catalogue and resource contracts | PCI/USB/ACPI discovery, IOMMU/DMA, signed driver loading, hardware-specific USB-C/Bluetooth/Wi-Fi/NVMe/GPU/audio drivers |
| Services | Unit/dependency/restart/time policy | Native init process, timers, logging daemon, persistent journal and package manager |
| UI | Window/accessibility descriptor contracts | Native window manager, assistive-technology APIs, localization runtime and compositor integration |

An `allow` result from a Reaper contract is a policy decision only. Privileged operations must independently revalidate inputs and capabilities at the native kernel boundary.

## Verification

The CI workflow:

1. Runs `reaper --check` on every Reaper subsystem source file.
2. Runs the existing system contract suite with the Reaper tree-walk engine and VM.
3. Checks and executes `core_mvp_tests.rpr` with both engines.
4. Keeps the x86_64 Stage 1 BIOS/UEFI boot workflow as a separate native evidence gate.

The core suite deliberately uses the Reaper language and current Reaper CLI. This change adds no Python implementation and no Python test code.

## Next native milestones

1. x86_64 IDT, timer and page-table foundation with QEMU permission-fault tests.
2. Ring-3 process address spaces, syscall validation, preemptive context switching and process teardown.
3. First read-only FAT32 mount path, then writable filesystem support with crash-consistency tests; NTFS remains read-only until qualified.
4. PCI/ACPI enumeration, NVMe block I/O, USB host-controller framework, DMA/IOMMU and device teardown.
5. Network interfaces and a minimal IPv4/IPv6 + UDP/TCP stack before DNS, firewall hooks and VPN protocols.
6. Framebuffer console/input first, then a native compositor and separately qualified GPU/audio backends.
7. Kernel-enforced MAC, signed driver/package verification, TPM transport and a verifiable Secure Boot chain.

Do not move a feature to `implemented-native` until source, negative tests, CI evidence and the target hardware/emulator behavior all support that exact claim.
