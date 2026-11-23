# DuckOS runtime and native execution roadmap

This document tracks implementation facts, not aspirational feature claims.
“Implemented” means there is code in the repository with automated host tests;
it does not mean the component is already connected to a booted DuckOS kernel.

## Subsystem status

| Subsystem | State | Current boundary |
|---|---|---|
| DABI64 v1 | Implemented | x86-64 frame/result contract, fixed 16-byte tagged value, ABI note identity and register convention |
| Host ABI validator | Implemented | Frame shape, version, alignment, argument count and typed scalar i64 checks; it cannot validate arbitrary process mappings |
| Scalar DABI64 backend | Working | Reaper compiles the tested scalar i64 program subset, direct calls, checked arithmetic and structured branches/loops |
| ELF relocatable object | Working through host assembler | Reaper emits GNU assembly; host assembler creates ET_REL and the finalizer stamps/checks DuckOS metadata; no native object writer or linker yet |
| Tagged values | Implemented in host runtime | unit, i64, bool, string, array and iterator tags retain the 16-byte value layout |
| Memory and ownership | Implemented in host runtime | injected allocator, strong references, atomic retain/release, clone/move/drop and bounded nested-array cycle rejection; no kernel heap binding |
| String runtime | Implemented baseline | owned byte strings, explicit byte length and NUL-terminated view; UTF-8 validation, normalization and builders remain future work |
| Collection runtime | Implemented baseline | dynamic arrays, typed length/index access and cloned element ownership; maps, slices and byte buffers remain future work |
| Iterator runtime | Implemented baseline | array iterators retain their source and expose a live view; compiler lowering of Reaper each is not yet connected |
| I/O runtime and emit | Not started | no file/console handles, read/write API, syscall bridge or Reaper emit lowering |
| Native ELF writer/linker | Not started | host assembler remains in use; relocation resolution and final executable construction are future work |
| ELF loader and process startup | Not started | no DABI64 image validation/loading, address-space mapping, initial stack or user entry dispatch |
| Kernel, syscall dispatcher and scheduler | Not started | no bootable kernel, memory manager, process model, interrupt path or scheduler |
| Full Reaper self-compilation | Not started | requires a working DuckOS runtime and executable pipeline before the compiler can bootstrap itself |

## Implementation sequence

### Phase 0 — Freeze the call boundary

- Keep DABI64 frame, result and register contracts shared by Reaper and DuckOS.
- Validate structure, scalar argument tags, alignment and failure-result behaviour.
- Preserve cross-repository tests for compiler-generated entry code.

**Exit gate:** the same public header is consumed by the compiler tests and DuckOS ABI tests.

### Phase 1 — Runtime value foundation

- Define stable tags on top of the existing 16-byte DuckValue.
- Provide an injected allocator so the host tests and future kernel heap use one API.
- Implement strong-reference clone, move and drop operations.
- Add owned strings, dynamic arrays and array iterators.
- Test allocation failure, reference lifetime, nested arrays, cycle rejection and iteration.

**Status:** implemented as a host-buildable C17 library. Kernel integration and language-level code generation are deliberately not claimed.

### Phase 2 — Connect Reaper to runtime services

- Define the DABI64 runtime-service table and stable function identifiers.
- Lower string construction, length and comparison to runtime calls.
- Lower array construction, append, index and length to runtime calls.
- Add each lowering through iterator creation/next/drop operations.
- Make ownership transfers explicit in HIR/MIR/LIR and emit drops on every control-flow exit.
- Test normal return, early return, error propagation, nested calls and allocation failure.

**Exit gate:** Reaper-generated programs execute string, array and each examples against the host runtime without leaking owned values.

### Phase 3 — I/O and emit

- Define typed file/console handles and a narrow read/write interface.
- Keep platform services behind DABI64 runtime calls rather than hard-coding Linux APIs.
- Define text-versus-byte semantics, partial writes, EOF and error propagation.
- Implement emit lowering and host-backed tests first, then bind the same interface to DuckOS syscalls.

**Exit gate:** a compiled Reaper program can emit text and bytes, report I/O failures and close owned handles deterministically.

### Phase 4 — Native object and executable toolchain

- Replace the host-assembler dependency with a deterministic ELF64 object writer.
- Implement symbol tables, sections, relocations and DABI64 ABI notes.
- Add a static linker that resolves symbols and rejects unsupported relocation kinds.
- Produce a minimal executable format accepted by the DuckOS loader.

**Exit gate:** the same source produces a verified executable without GNU assembler or a host linker.

### Phase 5 — Kernel execution path

- Build the boot path, early console, physical/virtual memory management and kernel allocator.
- Add address-space creation, user stack setup, ELF segment mapping and DABI64 entry dispatch.
- Add a syscall dispatcher and process lifecycle.
- Add a preemptive scheduler only after the single-process execution path is stable.
- Exercise the flow in an emulator with malformed-image and fault-path tests.

**Exit gate:** DuckOS boots an image, loads a Reaper-produced executable and runs it in user mode using the DABI64 contract.

### Phase 6 — Reaper bootstrap and self-hosting

- Keep a small trusted stage-0 compiler available to build the current Reaper source.
- Use the stage-0 compiler to produce a stage-1 Reaper compiler executable for DuckOS.
- Compile the compiler with itself (stage 2), compare deterministic outputs and test clean rebuilds.
- Gradually move compiler/runtime dependencies off the host and onto DuckOS services.
- Keep a reproducible bootstrap path and a documented recovery compiler.

**Exit gate:** a clean build can rebuild Reaper on DuckOS and the rebuilt compiler passes the same conformance suite.

## Engineering invariants

- The public DABI64 value and frame layouts remain explicit and statically asserted.
- Runtime allocations always have a defined owner and release path.
- Error paths must leave destination values and containers valid.
- Kernel services are reached through documented runtime/syscall interfaces, not host-only shortcuts.
- Every new language feature has parser/IR tests, generated-code tests and runtime execution tests.
- A feature is marked “working” only after automated end-to-end coverage exists.

Project implementation: Ivan-VHS. This attribution does not replace or remove the rights of other contributors or third-party dependencies.
