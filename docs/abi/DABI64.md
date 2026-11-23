# DuckOS DABI64 v1

DABI64 is the first explicit 64-bit DuckOS user-entry calling convention. It is intentionally separate from the x86-64 System V ABI. Reaper emits GNU assembly that uses the DABI64 registers and frame layout; the host assembler translates that assembly text into an ELF relocatable object.

## Target identity

| Property | Value |
|---|---|
| Architecture | x86-64 |
| ELF class / byte order | ELF64 / little-endian |
| ELF EI_OSABI | 0xD5 (DuckOS-reserved) |
| ABI note section | .note.duckos.abi |
| Note owner | DUCKOS |
| Note type | 0x44414249 |
| ABI version | major 1, minor 0 |
| Required data alignment | 16 bytes |
| Maximum scalar arguments | 64 |
| Captures | unsupported in v1 |

The backend is x86-64 only. The EI_OSABI value is part of this project contract and must be reserved consistently by a future DuckOS ELF loader.

## Entry register contract

Immediately before calling a DABI64 entry, a caller must place:

- R10 = pointer to a DuckCallFrame;
- R11 = pointer to a DuckCallResult;
- RSP aligned down to 32 bytes before CALL.

On return, RAX contains a DuckAbiStatus. A successful scalar function writes its tagged result into the result object. A failed function must leave the caller's result payload unchanged.

This is a custom DuckOS convention. It does not use the System V argument registers RDI, RSI, and so on. Every externally visible DABI64 function entry obeys the R10/R11/RAX contract.

## Stable data structures

DuckValue is 16 bytes:

| Offset | Width | Field |
|---:|---:|---|
| 0 | 8 | payload |
| 8 | 4 | kind |
| 12 | 4 | flags |

Runtime tag values are stable in DABI64 v1:

| Tag | Kind | Payload meaning |
|---:|---|---|
| 0 | DUCK_VALUE_UNIT | zero |
| 1 | DUCK_VALUE_I64 | two's-complement integer bits |
| 2 | DUCK_VALUE_BOOL | zero or one |
| 3 | DUCK_VALUE_STRING | managed runtime string handle/pointer |
| 4 | DUCK_VALUE_ARRAY | managed runtime array handle/pointer |
| 5 | DUCK_VALUE_ITERATOR | managed runtime iterator handle/pointer |

The 16-byte layout is unchanged. Runtime object payloads are valid only inside the address space and lifetime governed by the DuckOS runtime. Flags are zero in this initial implementation. The current Reaper native entry backend and host ABI validator intentionally accept scalar i64 arguments only; tags 2 through 5 do not yet imply compiler support for bool, strings, collections, or iterator expressions.

DuckCallFrame is 48 bytes:

| Offset | Width | Field |
|---:|---:|---|
| 0 | 4 | magic (0x49424144) |
| 4 | 2 | ABI major |
| 6 | 2 | ABI minor |
| 8 | 4 | byte size (at least 48) |
| 12 | 4 | argument count |
| 16 | 4 | capture count (must be zero) |
| 20 | 4 | flags (must be zero) |
| 24 | 4 | reserved0 (must be zero) |
| 28 | 4 | reserved1 (must be zero) |
| 32 | 8 | pointer to aligned argument array, or null for zero arguments |
| 40 | 8 | captures pointer (must be null in v1) |

DuckCallResult contains one DuckValue and is 16 bytes. Frame, result and non-empty argument array addresses are 16-byte aligned. The byte-size field allows compatible future extension; major version changes indicate an incompatible contract.

## Status codes

| Code | Meaning |
|---:|---|
| 0 | success |
| 1 | invalid frame/result pointer |
| 2 | bad magic |
| 3 | ABI version mismatch |
| 4 | frame too small |
| 5 | bad pointer alignment |
| 7 | unsupported flags or non-zero reserved field |
| 16 | signed i64 arithmetic overflow |
| 17 | integer division by zero |
| 18 | argument, capture or scalar value layout mismatch |

Statuses 16 and 17 are language execution failures. The other values are call-boundary validation failures.

## Runtime reference implementation

The C17 implementation in src/abi/dabi64.c is a host-buildable reference validator and typed result helper. It checks structural properties and scalar i64 tags. It cannot prove that an arbitrary non-null pointer maps to readable or writable memory; that belongs to a future DuckOS process/address-space layer.

The C17 runtime library in src/runtime/value.c adds owned values, strings, dynamic arrays and iterators on the stable tagged-value representation. Its allocator is injected so that the host tests can use malloc/free and a future kernel can bind the same value API to its heap. See [runtime ownership](../runtime/OWNERSHIP.md) for the exact rules and current limits.

Build and run the contract and runtime tests:

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

This repository currently contains the ABI contract, host validator and a host-buildable value runtime, not a bootable kernel, ELF loader, scheduler, syscall dispatcher or complete user-space process runtime. Those components must consume this same header and pass cross-component ABI tests before DABI64 can be called a full OS runtime.
