# Reaper processor and kernel contracts for DuckOS

**Status:** executable policy contracts validated by the Reaper reference runtime; not a native scheduler, interrupt controller, CPU hot-plug service or live patcher.  
**Target:** x86-64 primary, AArch64 and Elbrus explicit architecture tracks.

## Added modules

| Module | Contract surface | Native backend still required |
|---|---|---|
| duckos/kernel/processor.rpr | CPU descriptor/topology validation, ISA feature admission, affinity and deterministic least-loaded CPU selection | ACPI/firmware topology discovery, APIC bring-up, CPU online/offline, run-queue migration and real placement |
| duckos/kernel/timing.rpr | u32 wrap-safe elapsed time, half-range ambiguity, jitter, monotonic deadlines, periodic release catch-up and IRQ budget decisions | Stable architecture timer, TSC/HPET/APIC source calibration, interrupt entry/exit accounting and timer programming |
| duckos/kernel/telemetry.rpr | Saturating pressure score, safe response classification, cooperative quotas and bounded trace FIFO metadata | Atomic multi-core trace publication, scheduler wake/yield, hardware counters and deferred telemetry worker |
| duckos/kernel/patch.rpr | Candidate descriptor validation, integrity/signature/ABI admission, quiescence gate and rollback decision | Trusted cryptographic verifier, protected key store, inactive image storage, executable page policy, atomic bank switch and recovery boot-control |

## Core rules

CPU placement is a deterministic selection decision only. The scheduler backend remains responsible for run queues, context save/restore, preemption, CPU migration and interrupt routing.

Timer arithmetic makes the 32-bit wrap explicit. Samples whose interval exceeds half the counter range are ambiguous and rejected. Periodic tasks advance from the previous release rather than now, so drift is observable and missed releases are counted.

The telemetry policy only sheds diagnostics and other noncritical work. It must not insert a sleep, slow a hard-real-time ISR, or hide a deadline miss. The trace policy retains a bounded number of records and reports drops; it is not lock-free or safe for concurrent writers until a native atomic publication protocol is supplied.

A candidate update is never applied directly to executing code. It must pass checksum, trusted signature, ABI and policy verification, then wait for a safe point with no active IRQ and no device-owned DMA buffers. The contract returns eligibility for a trusted backend only. It does not make a memory write or transfer instruction pointer.

## Verification

system_platform_tests.rpr imports all four modules and covers valid/invalid CPU topologies, feature/affinity denial, deterministic CPU choice, timer wrap, ambiguous intervals, deadlines, IRQ budgets, periodic catch-up, pressure thresholds, quota exhaustion, trace overflow, unsigned/incompatible updates, unsafe quiescence and rollback. CI runs the suite with both Reaper reference tree-walk and VM engines.

A policy assertion is not evidence of physical hardware behavior. Native backend work remains a separate release gate.
