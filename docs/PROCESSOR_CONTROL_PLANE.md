# DAK Processor Control Plane v1

**Status:** Reaper kernel-policy contracts; x86_64 multiprocessor execution remains native implementation work.  
**Primary target:** x86_64, Intel and AMD. Elbrus remains a compatibility track, not a claimed boot target.

## Scope

DAK receives a complete processor policy surface covering inventory, topology, execution blocks, CPU/core lifecycle, AP startup, SMT, threads, affinity, preemption, scheduling, interrupts, local timers, cache/NUMA locality, power and thermal policy, PMU, virtualization, security and microcode provenance, debugging, verification, revision control, live update, rollback, telemetry and replay.

The executable contract is `duckos/kernel/processor.rpr`. Its fixture is `duckos/kernel/processor_tests.rpr`.

## Processor ownership

Reaper defines the policy vocabulary and validates descriptors. DAK's native architecture layer owns privileged operations: CPUID and MSR access, local APIC setup, AP trampoline, per-CPU stacks and data, context switch, interrupt routing, TSC/deadline timers, PMU and platform power controls. Pytyliki owns host-side processor discovery and measurements; it is not the DAK kernel driver.

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

An AP is not admitted until the bootstrap path is stable, the local controller is configured, stack and per-CPU data are mapped, and the required descriptor tables and interrupt gates are installed. Each AP receives a unique stack, CPU-local state, scheduler queue and interrupt accounting.

Core removal requires zero runnable threads, active interrupt handlers, held locks and DMA leases. Work must be migrated before the core enters the offline state. Hotplug increments the topology generation and invalidates stale affinity and scheduler snapshots.

## Scheduling and parallel execution

The policy exposes deterministic least-loaded CPU choice with stable CPU-ID tie-breaking, bounded work partitioning, thread priority/deadline metadata and explicit affinity. Native implementation must add preemption, context switching, work stealing, load balancing, priority-inversion control, interrupt affinity and CPU isolation. The policy fixture does not start threads.

## Verification, versions and live development

Kernel and core revisions use semantic version, ABI major, source digest, parent reference, monotonic generation and a lifecycle state. Candidate activation requires passing evidence, a valid signature, ABI compatibility, quiescence and a tested rollback artifact.

The update pipeline is: immutable build → static/type/IR checks → host simulation → QEMU boot and SMP tests → differential/stress/fault-injection tests → signature/provenance validation → quiescence → staged deployment → health window → commit or rollback.

The Reaper contract returns `admit-stage-only`, not an instruction patch. Real live patching requires an architecture-specific implementation with interrupt and stack safety, relocation validation, unwind metadata and recovery support.

## Current implementation boundary

The existing boot path validates Limine handoff data, early memory and bootstrap GDT/TSS/exception gates. It does not yet establish a fully operational APIC, start application processors, perform a scheduler context switch, run a preemptive SMP workload, or provide kernel-enforced CPU power and PMU controls. These remain explicit native milestones.

## Acceptance gates

- Descriptor shape, count and generation validation.
- Core/block/thread lifecycle transition tests.
- Affinity uniqueness and bounds.
- Deterministic least-loaded selection and work conservation.
- AP startup prerequisite and failure-path tests.
- Interrupt destination and vector validation.
- Core drain, interrupt, lock and DMA quiescence tests.
- Scheduler fairness, deadline, starvation and priority-inversion tests.
- Revision monotonicity, ABI and signature rejection.
- Live-update fault injection and rollback recovery.
- QEMU BIOS/UEFI boot and SMP qualification; physical target matrix before release.

No capability is marked implemented solely because the Reaper policy accepts its descriptor.
