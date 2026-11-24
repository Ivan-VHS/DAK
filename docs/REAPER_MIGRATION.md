# DuckOS migration to Reaper: evidence-based engineering plan

## Executive state

DuckOS is already **Reaper-first at the policy-contract layer**. Nineteen .rpr modules describe boot ordering, memory arithmetic, scheduler decisions, bounded IPC, driver metadata, trust, services, storage, telemetry and desktop policy. The Reaper contract-tests workflow checks every .rpr file and executes the integration suite with both the tree-walk reference runtime and the VM.

That is a meaningful language/system co-design baseline, but it is not yet a Reaper-native operating system. The current CMake project builds a host-testable C11 boot-information validator. No bootloader, privileged kernel entry, page tables, physical allocator, interrupt controller, preemptive scheduler, syscall boundary, VFS, process model or bootable image is present. The Python package supplies host-side tools and user-space integrations; Mora is a browser-hosted JavaScript/HTML/CSS desktop shell.

This plan treats source, tests, CI and emulator/hardware evidence as the capability boundary. A policy function that returns a scheduling decision is not a context switch. A queue model is not a shared-page IPC transport. A driver descriptor is not a loaded device driver. A valid boot-info structure is not a bootloader.

## 1. Repository baseline and exact dependency

The Reaper source dependency is the projects/reaper Git submodule. Its exact pin is recorded in federation/repositories.v1.json and in the superproject gitlink; duckos/reaper-migration.v1.json mirrors that pin and the validator rejects drift. Reproducible builds must use the recorded commit, never git submodule update --remote.

The current integration path is deliberately process-isolated:

- duckos.desktop.reaper.ReaperWorkbench locates the checkout, invokes fixed argument vectors with shell=False, bounds timeout/output and exposes static check/typecheck/Studio launch in the native Duck Desktop tool.
- .github/workflows/reaper-contracts.yml checks every source in duckos/**/*.rpr.
- contract_tests.rpr imports the subsystem contracts and is run using both the reference tree-walk interpreter and VM.
- DuckOS does not embed Reaper's Python interpreter into the OS process and does not grant source programs ambient host, kernel, FFI or device privileges.

The pin is a language-toolchain dependency, not proof that native Reaper object code is linked into DuckOS.

## 2. Actual source and ownership map

| Current source | Current responsibility | Migration status |
|---|---|---|
| duckos/kernel/*.rpr | boot sequence, bounded arenas, memory range arithmetic, scheduling and IPC policy | Reaper reference contracts; no privileged execution |
| duckos/drivers/*.rpr | descriptor validation, capabilities, range/IRQ conflict policy | Reaper policy; no bus enumeration or driver loading |
| duckos/security/*.rpr | capability attenuation and input-trust policy | Reaper policy; no hardware-enforced isolation |
| duckos/services/*.rpr | bounded restart decisions | Reaper policy; no process supervisor |
| duckos/storage/*.rpr | graph references, journal ordering and LWW register | Reaper policy; no persistent VFS or full database |
| duckos/system/*.rpr | execution-medium selection and telemetry classification | Reaper policy; no accelerator dispatch or sensor driver |
| duckos/ui/*.rpr | theme, motion and desktop policy | Reaper policy; no compositor or renderer |
| foundation/boot_info.c/.h | versioned fixed-width boot handoff validation | C11 host-tested foundation; no boot protocol implementation |
| duckos/**/*.py | packaging, deployment planning, read-only host inventory, CLI, compatibility inspection, native workbench and desktop maintenance | host tools/user-space; not kernel implementation |
| mora/**/* | browser-local Mora shell and app surfaces | web runtime; requires an explicit decision before calling it part of the Reaper-native userland |

The duckos/reaper-migration.v1.json file is the machine-readable inventory. Adding, removing or renaming a .rpr file requires updating that inventory and passing tools/validate_reaper_target.py.

## 3. Reaper capability gap: reference semantics versus native target

The companion target contract is being proposed upstream in [Reaper PR #273](https://github.com/Ivan-VHS/Reaper/pull/273). It defines the required freestanding-kernel profile and its promotion rules. The DuckOS submodule is intentionally still pinned to its reviewed existing commit, so that profile is recorded as not yet present in the pinned checkout; it becomes an available integration input only after the Reaper change is accepted and DuckOS advances its submodule pin deliberately.

Reaper's Python reference runtime and VM support materially more of the current DuckOS .rpr contract language than its experimental native AOT backend.

| Required feature | Reference runtime / VM | Native AOT or freestanding kernel |
|---|---|---|
| named functions, declarations, conditionals, loops | used by DuckOS contracts | scalar subset only; each is unsupported |
| lists, indexing, collection built-ins and imports | used by DuckOS contracts | not supported by native AOT |
| :: collection pipelines | supported by reference runtime/VM | not supported by native AOT |
| fixed-width u8..u64, usize, pointers and references | not a complete statically checked source type system | not implemented as a complete target ABI |
| struct/enum layout, align, packed, field access | not complete in the source grammar/runtime | not implemented |
| ownership, borrow/lifetime rules and deterministic drop | not a complete static guarantee | not implemented |
| unsafe regions and typed effect/capability checking | capability policy exists as application logic | not compiler-enforced |
| freestanding/no-host-library startup and panic | no DuckOS kernel runtime | not implemented |
| volatile MMIO, atomic memory orders, fences and DMA lifecycle | C adapter contracts exist in Reaper; not general .rpr operations | not a Reaper source-to-object path |
| interrupt declarations, naked functions and inline assembly | external/native boundary only | no end-to-end compiler support |
| target object emission, relocation, linker sections and DWARF | external toolchains used by existing embedded paths | not an x86_64 DuckOS kernel backend |
| QEMU boot and hardware qualification | current tests exercise host reference semantics | not present |

**Consequence:** the current DuckOS .rpr modules cannot simply be passed to reaper --native. The native AOT slice rejects lists, indexing, each, imports/exports and collection pipelines. The first compiler milestone is to close those semantic/native-lowering gaps without changing the Python reference semantics; the next is a real freestanding object path with verified ABI and startup.

## 4. Architecture decisions before privileged code

The initial CPU target, boot protocol, kernel ABI, virtual address map, interrupt controller, timer source, page-table layout, filesystem, and user/kernel calling convention remain decisions—not implicit defaults. docs/FOUNDATION_ARCHITECTURE.md requires Architecture Decision Records for these subjects.

The first proposed qualification environment is a version-pinned QEMU machine profile and serial console because it allows deterministic headless boot testing. This is a proposal, not a selected machine/boot protocol. Select one CPU target and one boot protocol in an ADR before producing architecture-specific entry code. The current duckos.boot-info.v1 record is a host-tested C11 contract; its validator never dereferences the physical addresses stored in the record.

## 5. Migration phases and acceptance gates

### G0 — reproducible reference-contract baseline (implemented)

- Pin the exact Reaper submodule commit and reconcile it with the federation registry.
- Track every DuckOS .rpr file.
- Parse/check every Reaper file and execute the suite under both the tree-walk interpreter and VM.
- Preserve separate status for host tools, reference contracts, native code and target hardware.

### G1 — architecture, boot and ABI decisions (planned)

- Approve a CPU target, boot protocol and emulator machine profile.
- Specify the boot handoff, entry register/stack convention, calling convention, structure layout, symbol policy and error/panic ABI.
- Specify memory ranges, reserved regions, kernel image sections and initramfs placement.
- Define serial output and a deterministic QEMU pass/fail exit path.
- Keep the boot-info structure versioned; no ABI changes without compatibility fixtures.

### G2 — Reaper systems-language and compiler foundation (planned)

Implement each source feature only together with parser/AST support, static type/effect rule, reference runtime behavior, native IR/lowering, negative tests, generated-object inspection and differential fixtures:

1. fixed-width signed/unsigned integers, checked/wrapping/saturating arithmetic and target usize;
2. pointers, references, slices, arrays, structs, enums, function pointers and target-aware layout;
3. explicit align/packed, field offsets, ABI layout tests and compile-time layout assertions;
4. freestanding/no_std runtime profile, deterministic startup, panic, allocator hooks and no implicit libc;
5. ownership/borrowing/lifetime checks, initialization, drop/defer and audited unsafe boundaries;
6. typed effects/capabilities for memory, MMIO, IRQ, DMA, I/O and privileged operations;
7. volatile load/store, atomics, fences, DMA cache synchronization and checked MMIO adapters;
8. architecture-specific intrinsics, interrupt ABI, minimal assembly stubs and context-switch boundary;
9. source-mapped HIR/MIR/CFG, verified lowering, target object emission, relocations, linker sections and debug information;
10. pinned cross-toolchain, reproducible build fingerprint and QEMU differential tests.

### G3 — minimal Reaper kernel bring-up (planned)

- Keep only the minimum reviewed boot assembly/firmware handoff outside Reaper.
- Compile a freestanding Reaper entry point and serial output.
- Link the kernel with the approved memory map and entry symbol.
- Boot the image under the selected QEMU profile and require an exact serial marker plus deterministic shutdown.
- Inspect the binary, sections, relocations, undefined symbols, stack usage and linker map. No CPython, host libc or reference VM may be present in the boot image.

### G4 — kernel core (planned)

- Parse/validate the boot memory map in Reaper and build the physical frame allocator.
- Add virtual page mapping, permissions, TLB invalidation and kernel heap with overflow-safe boundaries.
- Install exception/interrupt descriptors, panic register capture and timer ticks.
- Add atomic/spinlock contracts and a real context-switch path.
- Promote the current scheduler policy only after preemptive one-core and then SMP tests pass.

### G5 — system services (planned)

- Define syscall ABI, user pointer validation and copy-in/copy-out.
- Add process/address-space model, cancellation, handles and capability enforcement.
- Add device discovery, bus and driver lifecycle contracts, DMA-safe buffers and mock hardware adapters before real devices.
- Add VFS, initramfs reader, one read-only filesystem first, then transactional writes.
- Add IPC with bounded queues, shared-page mapping, wakeups, cancellation and backpressure.
- Add networking only after packet-buffer ownership and endianness are verified.

### G6 — userland and desktop (planned)

- Build a first Reaper user executable and launch it through the DuckOS process/syscall path.
- Port core init/service manager, shell and utilities using a defined Reaper userland runtime.
- Decide whether Mora remains an explicitly separate web UI or gains a Reaper/native client path; do not claim JavaScript assets have been migrated merely because their policy is represented in .rpr.
- Keep native Duck Desktop host maintenance tools distinct from target userland.

### G7 — deprecation and release qualification (planned)

- Remove a legacy executable component only after an equivalent Reaper implementation has passed contract, differential, emulator and recovery tests.
- Keep unavoidable boot/interrupt assembly behind a small reviewed boundary.
- Run clean reproducible cross-builds, QEMU boot and fault injection.
- Compare performance and memory footprint against recorded baselines.
- Publish target support, threat model, release artifacts and recovery evidence.

## 6. Cross-repository development loop

A DuckOS blocker becomes a Reaper issue with a minimal reproducer and a named target acceptance test. A Reaper change is not promoted until all of the following pass:

1. Reaper parser, typechecker, runtime/VM and native compiler tests.
2. Differential tests against the Reaper reference runtime.
3. DuckOS .rpr source checks and contract_tests.rpr on both engines.
4. Relevant native build and QEMU boot tests once that backend exists.
5. Both repositories' schemas, pin registry, docs and maturity labels are updated.

Use exact reviewed Reaper commits in DuckOS. Never advance a submodule to an unreviewed branch head or silently change a source-language contract.

## 7. Completion definition

"100% migrated" means all in-scope executable kernel, driver, service, filesystem, process, syscall and userland system code is built from Reaper for the selected target, and all retained non-Reaper code is listed as a narrow boot/assembly/firmware or web boundary with a technical reason. It additionally requires a bootable, reproducible image, end-to-end QEMU tests, negative/fault-injection coverage, native ABI conformance, no host runtime dependency in the kernel, and a documented recovery route.

The current repository is at G0. No bootable image or Reaper-native kernel is claimed.
