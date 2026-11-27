# DAK Processor Control Plane v1

**Status:** Reaper policy contracts plus bounded native C11 scheduler, x86_64 CPU probe and general-register context-switch primitive. The boot path does not yet run a complete SMP kernel.  
**Primary target:** x86_64, Intel and AMD. Elbrus remains a compatibility track, not a claimed boot target.

## Scope

DAK's processor control plane covers inventory, topology, execution blocks, CPU/core lifecycle, AP startup prerequisites, SMT, threads, affinity, preemption policy, scheduling, interrupts, local timers, cache/NUMA locality, power and thermal policy, PMU, virtualization, security and microcode provenance, debugging, verification, revision control, live update, rollback, telemetry and replay.

The Reaper policy is `duckos/kernel/processor.rpr`, with `duckos/kernel/processor_tests.rpr` as its fixture. Native C11 scheduling is in `kernel/processor/scheduler.[ch]`.

## Native code added

### Bounded scheduler core

The C11 scheduler provides a fixed-capacity kernel-side data model for up to 64 logical CPUs and 256 thread descriptors. It implements:

- bootstrap CPU admission and AP startup readiness gates;
- CPU lifecycle transitions: offline, starting, online, draining, quarantined and failed;
- thread lifecycle transitions and descriptor admission;
- per-CPU current-thread, interrupt, lock, preemption, DMA and quantum accounting;
- affinity filtering and deterministic priority/deadline selection;
- round-robin tie-breaking within equal priority/deadline classes;
- bounded tick accounting and a reschedule-pending signal;
- CPU drain/offline checks which reject outstanding critical sections and threads pinned exclusively to the retiring CPU;
- topology generation increments on successful CPU release.

The scheduler is a bounded native core, not yet a production preemptive SMP scheduler. It still needs per-CPU run queues, inter-processor interrupts, work stealing/load balancing, an interrupt-safe timer entry, wait/wake queues, priority inheritance and integration into the booted runtime.

### x86_64 architecture helpers

- `kernel/arch/x86_64/cpu.[ch]` probes CPUID vendor/family/model/stepping, logical/core counts and feature bits. AVX/AVX2/AVX-512 are reported only when OSXSAVE and the required XCR0 state are present.
- `kernel/arch/x86_64/context.[ch]` builds a bounded initial thread stack frame.
- `kernel/arch/x86_64/context.S` provides a real x86_64 general-register context-switch primitive, saving/restoring the ABI-preserved integer registers and stack pointer.
- Hosted C tests exercise scheduler admission, topology generations, selection, drain and the assembly context-switch primitive.
- The Stage 1 ISO build script compiles and links the scheduler, CPU probe and context-switch objects. CMake exposes a native processor runtime target and corresponding tests.

The context-switch primitive is GPR-only v1. It does not yet save/restore FPU/SSE/AVX state, debug registers, full interrupt frames or address-space state. The scheduler and context-switch primitive are not yet wired into `kernel/boot/entry.c`; compiling them into the ELF is not equivalent to running them.

## Processor ownership

Reaper defines the policy vocabulary and validates descriptors. DAK's native architecture layer owns privileged operations: CPUID and future MSR access, local APIC setup, AP trampoline/SIPI, per-CPU stacks and data, context switch, interrupt routing, TSC/deadline timers, PMU and platform power controls. Pytyliki owns host-side processor discovery and measurements; it is not the DAK kernel driver.

A policy decision is not an instruction to execute. A native backend must check the same target, generation, privilege and capability again at the point of use.

## Canonical descriptors

Processor snapshot:

`[schema, snapshot_id, architecture, vendor, packages, dies, cores, logical_threads, online_threads, generation, features, source]`

Core:

`[core_id, package_id, die_id, cluster_id, class, state, online_threads, thread_ids, revision_id, generation]`

Execution block:

`[block_id, owner_core, class, width_bits, state, revision_id, generation]`

Thread:

`[tid, pid, priority, deadline_ns, stack_bytes, state, affinity, generation]`

The online-CPU count never exceeds discovered logical CPUs. Every affinity ID must resolve inside the same topology generation. Offline-to-online transitions pass through `starting`; online cores enter `draining` before they are released.

## Multiprocessor lifecycle

The target lifecycle is:

`firmware → bootstrap CPU → per-CPU resources → local APIC/timer → AP startup → scheduler admission → SMP operation`

The native scheduler refuses to admit a secondary CPU until the bootstrap CPU is online and its startup evidence includes GDT, IDT, a unique stack, per-CPU data, local controller readiness and an AP trampoline. This is a readiness gate only: the current boot path does not yet discover ACPI MADT processor entries, map/configure the local APIC, send INIT/SIPI or execute a real AP trampoline.

Core removal requires zero runnable/affinity-pinned work, active interrupt handlers, held locks, preemption depth and DMA leases. Hotplug increments the topology generation and invalidates stale snapshots.

## Scheduling and parallel execution

The policy and C11 core implement deterministic priority/deadline selection, affinity filtering, round-robin selection inside equal scheduling classes and bounded quantum accounting. The tick path only sets a reschedule-pending signal. A real timer interrupt, IPI reschedule path, context-switch call site and per-CPU ready queues remain integration work.

## Power, debug and live patching

Frequency caps, power profiles, PMU, thermal control and CPU debug need platform-specific native drivers and explicit capabilities. The Reaper adapter ABI defines those callbacks and bounds requests, but DAK has not yet supplied a real MSR/P-state/thermal driver, hardware debug-register engine or signed live patch engine.

The intended live-update pipeline is immutable build → static/type/IR checks → host simulation → QEMU boot/SMP qualification → differential/stress/fault-injection tests → signature/provenance validation → quiescence → staged deployment → health window → commit or rollback. The current C code supplies staging/rollback policy and context-switch primitives, not a complete kernel text patcher.

## Current implementation boundary

The existing Stage 1 boot path validates Limine handoff data, early memory and bootstrap GDT/TSS/exception gates. The new processor objects are compiled and linked into the x86_64 ELF by the ISO script, but the boot entry still does not initialize the scheduler or start application processors. There is no production SMP execution, preemptive context switching, FPU/XSAVE context preservation, APIC/IPI route, kernel PMU or power driver, hardware debug engine or live kernel patch implementation.

## Acceptance gates

- Descriptor shape, count and generation validation.
- Core/block/thread lifecycle transition tests.
- Affinity uniqueness, pinned-thread drain and bounds.
- Deterministic scheduler selection and work conservation.
- AP startup ordering and failure-path tests.
- Context-frame bounds/alignment and actual GPR switch test.
- Interrupt, lock, preemption, DMA and runnable-thread quiescence tests.
- Scheduler fairness, deadline, starvation and priority-inversion tests.
- Revision monotonicity, ABI and signature rejection.
- Live-update fault injection and rollback recovery.
- QEMU BIOS/UEFI boot, then SMP emulator qualification; physical target matrix before release.

No capability is marked implemented solely because the Reaper policy accepts its descriptor or because a native object file links.
