# Reaper Native System Platform for DAK

**Status:** first executable Reaper system-contract tranche added; privileged backend and freestanding Reaper code generation remain open gates.  
**Primary target:** Intel/AMD x86-64.  
**Architecture seams:** AArch64 and Elbrus remain explicit targets; they are not declared hardware-qualified by this contract layer.

## Goal

DAK adopts the OS-relevant capabilities represented by the supplied Swift system-programming references through original Reaper source modules. No Swift implementation, copied source file, copied test fixture, or upstream implementation detail is embedded in DAK. The references inform the capability map only; their licenses remain relevant to any future code reuse, which requires a separate license and attribution review.

The implementation is split into three enforceable boundaries:

1. **Reaper policy and algorithms.** Deterministic validation, protocol parsing, state machines, resource bounds, dependency checks and transaction decisions live in `.rpr`.
2. **Kernel and trusted service adapters.** Privileged instructions, physical mappings, context switches, durable storage, network device I/O, cryptographic signature verification and process identity are supplied by audited DAK backends.
3. **Userland services.** Installer, package manager, updater, dispatch queues and system utilities call versioned kernel/service contracts; they never gain ambient authority.

A contract returning an admission decision does not itself perform the privileged operation.

## Adopted capability map
| CPU topology and scheduling | kernel/processor.rpr, existing kernel/scheduler.rpr and kernel/threads.rpr | ACPI/APIC topology, run queues, preemption, context switch and CPU migration |
| Timebase and pressure response | kernel/timing.rpr and kernel/telemetry.rpr | Stable timer source, ISR accounting, atomic multi-core trace publication and deferred telemetry worker |
| Verified update admission | kernel/patch.rpr | Trusted signature verification, inactive image storage, safe executable mapping, atomic switch and rollback backend |

| Capability family | Reaper implementation | Boundary still required |
|---|---|---|
| Boot and architecture | `kernel/arch/x86_64.rpr`, `kernel/arch/aarch64.rpr`, existing boot contract | Firmware handoff, early memory, IDT/PIC/APIC/GIC setup and real platform bring-up |
| Memory and virtual memory | Existing range/arena and VM policy plus architecture page checks | Physical frame allocator, page-table mutation, TLB invalidation/shootdown, swap I/O and reclamation |
| Atomics and synchronization | `kernel/atomic.rpr`, `kernel/synchronization.rpr` | Compiler atomics, CPU instructions, scheduler-aware blocking and SMP stress tests |
| Processes, threads and handles | Existing process policy plus `kernel/threads.rpr`, `kernel/handles.rpr` | Address-space construction, privilege transitions, context switch, handle table and process reaping |
| System-call boundary | `kernel/syscall.rpr` | Trap entry/return, register ABI, user-copy fault handling, identity derivation and live handler table |
| Device access | `drivers/mmio.rpr`, `drivers/dma.rpr`, existing driver ABI | Mapping, IOMMU, cache maintenance, interrupt routing, bus enumeration and real device drivers |
| Networking | `network/ipv4.rpr`, `udp.rpr`, `tcp.rpr`, `dns.rpr`, existing firewall policy | Ethernet/NIC queues, IPv6 extension processing, TCP serial-number wrap handling, congestion control, retransmission, sockets and live integration tests |
| Storage and Foundation-like primitives | `storage/path.rpr`, `storage/journal.rpr`, `runtime/foundation.rpr`, `runtime/data.rpr`, `runtime/clock.rpr` | Filesystem drivers, block I/O, durable flush ordering, Unicode normalization, locale/time-zone database and production clock source |
| Concurrent dispatch | Existing scheduler/flock policy plus `services/dispatch.rpr` | Worker creation, wakeups, cancellation points, work stealing and priority-inversion control |
| Installer and packages | `system/installer.rpr`, `system/package_manager.rpr` | Trusted signature verifier, archive parser, sandboxed extraction, partition backend and crash-safe durable commit |
| Updates and rollback | `system/updater.rpr` | A/B boot-control storage, verified boot integration, watchdog health evidence and power-loss testing |
| Build and system utilities | `system/build.rpr`, `system/utilities.rpr` | Pinned compiler/linker execution, artifact signing, reproducible binary comparison and audited process service |

## Relation to the supplied Swift references

- The bare-metal OS examples (asaptf/swift-os, kkebo/swift_os, mweinbach/swift-os, spevans/swift-project1, bastie/SOS, MAGIos and BetaOS) are represented as architecture, boot, interrupt, memory, process, driver and networking capability requirements. Their Swift source is not ported.
- swift-system informs the explicit system-call/host-adapter boundary.
- swift-atomics informs memory-order validation and the requirement for architecture-backed atomic primitives.
- swift-corelibs-foundation informs bounded data, path, time and storage primitives; this is a deliberately small OS foundation, not Foundation API compatibility.
- swift-corelibs-libdispatch informs bounded concurrent queues, QoS selection, cancellation and worker-capacity contracts.
- rules_swift informs reproducible target/build-graph contracts; DAK does not adopt Bazel or Swift build rules.
- SwiftletUtilities informs safe command and local-system utility contracts.
- awesome-swift, Wolg/awesome-swift and awesome-macOS are discovery/catalogue resources, not singular runtime components. They are not copied or treated as a specification to reimplement every app or package.
- SwiftOS proposal is treated as architectural context only, not an executable upstream implementation.

The goal is an OS-oriented Reaper-native capability set, not binary, API or source compatibility with Swift.

## Execution and verification

The new `system_platform_tests.rpr` exercises the system contracts through Reaper. The dedicated workflow checks every DAK `.rpr` source, then runs the suite with both the reference tree-walk engine and the VM engine.

The workflow uses the existing Reaper CLI as a test harness. It does not turn the reference runtime into a freestanding kernel compiler. Current Reaper documentation identifies the Python reference runtime as the broad compatibility implementation and the native C17/compiler track as partial. The DAK integration therefore remains explicit about the current execution boundary.

## Release gates — do not mark complete before evidence exists

- [ ] Reaper typed IR supports fixed-width integers, pointers, aggregates, address spaces and explicit effects required by kernel code.
- [ ] Reaper native backend emits freestanding x86-64 objects and a linkable DAK kernel image without a Python host runtime.
- [ ] DABI64 syscall entry/return is implemented and tested from user mode.
- [ ] Real x86-64 page tables, physical allocator, TLB shootdown, interrupt routing and SMP context switching pass QEMU tests.
- [ ] Atomic operations map to target instructions and pass memory-model/SMP stress tests.
- [ ] MMIO/DMA adapters run with IOMMU and cache-coherency enforcement on qualified hardware or faithful emulators.
- [ ] Network packets pass protocol conformance and adversarial parser tests; a live NIC path is verified.
- [ ] VFS, journal and installer survive forced power-loss tests on disposable virtual disks.
- [ ] Package/update signature verification uses a maintained cryptographic implementation and a protected trust store.
- [ ] A/B update rollback is verified across interrupted writes, failed boots and watchdog timeouts.
- [ ] x86-64 Intel/AMD is qualified first; AArch64 and Elbrus require their own build, boot and hardware evidence.

Until those gates pass, the new source files are executable contracts and deterministic algorithms, not a claim that all corresponding hardware services are already running inside DAK.


See [Reaper Processor and Kernel Contracts v1](REAPER_PROCESSOR_KERNEL_V1.md) for the implementation matrix and verification boundaries.
