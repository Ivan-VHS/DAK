# DuckOS Application Binary Interface — DABI64 v1

**Status:** proposed and implemented as a versioned C contract in this repository. Kernel entry, process loader and linker integration are separate milestones.

DABI is DuckOS's own function and system-call ABI. It does not inherit the System V AMD64 calling convention. The first concrete target is little-endian x86-64; other architectures need a separately specified register map while preserving the typed frame contract.

## 1. Target identity

| Property | DABI64 v1 |
|---|---|
| Target triple | duckos-x86_64-unknown-dabi1 |
| Machine | x86-64 |
| Endianness | little-endian |
| Data model | LP64 |
| Pointer width | 64 bits |
| ABI major/minor | 1.0 |
| Frame/value alignment | 16 bytes |
| Stack alignment | 32 bytes immediately before CALL |
| Red zone | none |
| Variadic functions | unsupported in v1 |

An unsupported major version is a hard load/call error. A newer minor version is rejected by a v1 runtime.

## 2. Typed values

Every argument is a 16-byte DuckValue: payload (u64), kind (u32), flags (u32). Kinds identify unit, signed/unsigned 64-bit integer, boolean, float64, pointer, UTF-8 view, byte view, handle or error. Flags distinguish borrowed, owned and read-only values; owned and borrowed are mutually exclusive.

## 3. Function-call convention

A native function is entered with:

| Register | Entry value |
|---|---|
| R10 | const DuckCallFrame pointer |
| R11 | DuckCallResult pointer |

The function returns DuckAbiStatus in RAX. On success only, the callee writes one typed DuckValue to the result slot. On failure the result slot remains unchanged. All arguments and captures are typed arrays, giving every function the same machine-level calling convention.

The 48-byte call frame layout is:

| Offset | Size | Field |
|---:|---:|---|
| 0 | 4 | DABI magic |
| 4 | 2 | ABI major |
| 6 | 2 | ABI minor |
| 8 | 4 | total frame byte size |
| 12 | 4 | argument count |
| 16 | 4 | capture count |
| 20 | 4 | flags |
| 24 | 4 | reserved, zero |
| 28 | 4 | reserved, zero |
| 32 | 8 | argument-array pointer |
| 40 | 8 | capture-array pointer |

Frame and non-empty value-array addresses are 16-byte aligned. The caller owns the storage until return. The callee may not retain a pointer unless ownership transfer is explicit.

Callee-saved registers are RBX, RBP and R12–R15. Caller-saved registers are RAX, RCX, RDX, RSI, RDI, R8–R11 and XMM registers. RSP is 32-byte aligned immediately before CALL and RSP + 8 is 32-byte aligned at entry. There is no red zone.

This is intentionally not SysV: arguments/results use R10/R11, the stack boundary is 32-byte aligned and status/result semantics are explicit.

## 4. System-call convention

The x86-64 SYSCALL entry uses RAX for syscall number, RDI for DuckCallFrame pointer and RSI for DuckCallResult pointer. RAX returns DuckAbiStatus; RCX and R11 are clobbered. Kernel services must validate and copy user memory against the process address space before acting.

Stable syscall numbers:

| Number | Name |
|---:|---|
| 1 | PROCESS_EXIT |
| 2 | IO_READ |
| 3 | IO_WRITE |
| 4 | CLOCK_MONOTONIC |
| 5 | MEMORY_MAP |
| 6 | MEMORY_UNMAP |
| 7 | THREAD_CREATE |
| 8 | THREAD_JOIN |
| 9 | THREAD_YIELD |
| 10 | CAPABILITY_QUERY |

Reserved calls keep their numbers; an unavailable service returns NOT_IMPLEMENTED.

## 5. Object identity

DABI v1 uses ELF64 as a container, not as the System V calling convention. DuckOS-linked files use EM_X86_64, EI_OSABI 0xD5 and a mandatory .note.duckos.abi record containing ABI version, architecture and required features. The linker and loader reject missing or incompatible notes.

The first static linker relocation subset is R_X86_64_64, R_X86_64_PC32, R_X86_64_PLT32, R_X86_64_32 and R_X86_64_32S. Unsupported relocations are errors.

## 6. Runtime boundary

The language entry point is duck_main. A DuckOS startup object validates the process frame, calls duck_main and invokes PROCESS_EXIT with its final status. The minimal runtime will provide ABI/value helpers, ownership-aware allocation, process/thread entry, capability-gated I/O, clock wrappers and panic reporting without requiring a hosted libc.

The kernel owns address-space validation, mapping, scheduling, handle permissions and syscall dispatch. User-space runtime code cannot grant itself capabilities.

## 7. Implemented status and acceptance

This repository currently contains the DABI64 v1 layout header, status codes, frame/result validators and host-buildable C tests. These validate C layout and malformed-frame handling. They do not implement a kernel, syscall dispatcher, static linker or executable loader.

Next gates are: (1) independent layout probes, (2) Reaper R10/R11 codegen and ABI note, (3) static DuckOS linker, (4) loader note/relocation validation, (5) process startup and syscall dispatch, and (6) a cross-component Reaper-to-DuckOS execution test.
