# DuckOS system implementation — progress and gates

**Updated:** 2026-11-25  
**Implementation branch:** `feat/kernel-syscall-process-contracts-v1`  
**Mainline status:** none of the changes in this branch is merged yet.

## Current scope of this branch

This branch adds executable Reaper policy/state contracts and wires the existing integration suite into CI. The contracts are deliberately below the level of real kernel execution.

| Subsystem | Added source | What is now checked | What is still absent |
|---|---|---|---|
| Boot protocol adapter | `duckos/kernel/limine_map.rpr` | known Limine memory types, split-u64 range overflow, sorted/non-overlapping map validation, deferred loader-memory reclamation | native Limine pointer/response validation, validated boot-info construction, loader response lifetime and actual boot entry |
| Process identity | `duckos/kernel/process.rpr` | PID/generation handles, descriptor validation, state transitions, parent relation, capability attenuation | kernel stacks, page-table roots, context switch, scheduling/preemption, user-mode execution |
| Syscall boundary | `duckos/kernel/syscall.rpr` | ABI version, call IDs, argument/payload bounds, stale-handle rejection, user-buffer metadata, BAV decision | CPU syscall entry/return, privilege transition, safe copy-in/out, native handler table |
| Virtual memory | `duckos/kernel/vm.rpr` | 4 KiB alignment, owner/address-space scope, no W+X, overlap, permission-aware translation policy | physical frame allocator, page-table edits, TLB shootdown, fault handler |
| Interrupts | `duckos/kernel/interrupts.rpr` | vector/route shape, priority, mask, nesting and handler acknowledgement policy | GDT/IDT, ISR assembly, APIC/PIC programming, timer source and EOI hardware operation |
| IPC | `duckos/kernel/ipc_endpoint.rpr` | bounded endpoints, sender/receiver identity, capability checks and sequence order | shared pages, cross-process copy, wakeups, blocking, cancellation and concurrency |
| BAV | `duckos/security/bav.rpr` | deny-by-default capability/resource/operation checks, trust state, payload budgets and sequence audit model | kernel enforcement hooks, trusted identity broker, tamper-resistant persistent audit service, real sandbox |
| Service manager | `duckos/services/lifecycle.rpr` | dependency readiness, finite restart budget and health transitions | init process, actual process supervision, IPC lifecycle and restart execution |
| Native desktop | `duckos/desktop/window_manager.rpr` | display/window descriptors, display fallback, bounds, keyboard movement and focus ordering | native window handles, input backend, compositor, GPU, hotplug and multi-monitor hardware enumeration |
| Packages/Jora | `duckos/packages/transaction.rpr` | manifest admission, capability attenuation, inactive-slot transaction, health gate and rollback decision | cryptographic signature verification, archive extraction, atomic filesystem switch, boot-slot integration and application launch |

The new root `contract_tests.rpr` fixtures exercise the added behavior through both Reaper tree-walk and VM modes. The workflow job installs the pinned Reaper submodule and runs syntax, tree-walk and VM checks. CI results on the exact PR head are still required before this source is considered verified.

## Important existing foundation

- `foundation/boot_info.h/.c` already provides a fixed-size 88-byte C11 boot-info v1 contract and a host-testable validator. It is not a bootloader or a kernel entry point.
- `duckos/kernel/boot.rpr`, `memory.rpr`, `arena.rpr`, `scheduler.rpr`, `flock.rpr`, `ipc.rpr` and `zero_copy_bus.rpr` already model several policies. Their own comments correctly state that they do not perform hardware page allocation, CPU context switching or physical shared-memory transport.
- Reaper's current native AOT compiler is a scalar hosted C17 subset. The current compiler does not implement direct ELF output, DABI64, a freestanding runtime or full language parity.
- Mora is a browser-hosted shell. Its windows and settings are not a native compositor, kernel permission enforcement or process isolation.
- OPlague's hardware/driver inspection is read-only; it must not silently become a driver installer or a privileged device broker.

## Seven workstreams and dependency order

### 1. Kernel and boot

**Next:** finalize the first x86-64 boot target; implement bootloader-response validation and the minimal serial-only kernel entry; then page-frame allocation, IDT/exception reporting, timer, page tables, context switch, syscall entry and a first user process.

**Blocker:** Reaper cannot yet emit a complete freestanding kernel image. Keep boot-info v1 host tests separate from any future QEMU boot test.

### 2. Reaper native compiler

**Next:** versioned typed IR and source maps; fixed-width unsigned integers; typed records and bounded collections; explicit ownership/drop rules; freestanding startup/runtime profile; target object emission and relocation handling; DABI64 v1 layout/conformance.

New language features must pass reference-runtime/native differential fixtures. No "native" status from syntax registry entries alone.

### 3. Native desktop

**Next:** native input/display abstraction, hotplug events, software framebuffer compositor, window manager and accessibility tree. Add GPU acceleration only after CPU fallback is stable. Mora stays a preview/user-facing shell until it can talk to native services through a permissioned protocol.

### 4. BAV and isolation

**Next:** define canonical app identity and capability tokens, make kernel syscall/service dispatch consult BAV, use short-lived scoped grants and revocation, then add per-process address-space isolation. Audit events must include request ID, actor and policy hash without storing document/source payloads.

### 5. System services

**Next:** init/service supervisor, bounded IPC with real wait/wakeup/cancel semantics, VFS/block layer, read-only first storage driver, network service, audio service and graphics/input providers. Keep each service behind versioned contracts and a native fallback path.

### 6. Jora, packages and applications

**Next:** signed package metadata, package/content hashes, trusted publisher key policy, capability manifest, safe staging, atomic activation, health confirmation and rollback. Jora is the catalog/planner; it must not bypass the package manager or execute manifest strings through a shell.

### 7. Continuous engineering

**Next:** keep the pinned cross-repository source federation read-only; build each project in its own toolchain; run contract compatibility checks, CTest/builds, Reaper tree-walk+VM parity, security analysis, supply-chain checks and emulator boot tests as their prerequisites appear. Pin moves remain explicit reviewed PRs; no automatic submodule advance or auto-execution of imported sources.

## Rules for promoting maturity

- `specified`: contract and owner exist.
- `modelled`: executable Reaper policy tests exist, but no native operation is claimed.
- `implemented`: actual code performs the feature in its declared runtime with positive, negative, boundary and failure tests.
- `verified`: reproducible evidence exists on the declared target, including CI artifacts where applicable.
- `partial`: use when only one layer or scenario is operational.
- `not_applicable`: only with a product-scope reason.

No policy model, host-side test, GUI control or catalog row can promote a kernel, compositor, native sandbox, device driver, installer or boot image to implemented.
