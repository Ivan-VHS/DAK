# DuckOS

DuckOS is the native operating-system project in the Ivan-VHS workspace.

## Current foundation

The first versioned userspace contract is **DABI64 v1**. It is deliberately distinct from the System V AMD64 calling convention and defines:

- typed 16-byte values and a versioned 48-byte call frame;
- the x86-64 function entry registers **R10** (call frame) and **R11** (result slot);
- explicit status returns in **RAX** and write-on-success result semantics;
- a separate syscall register map that accounts for the architectural SYSCALL clobbers;
- ELF64 identity through OSABI 0xD5 and a mandatory .note.duckos.abi.

The C contract, frame validators and host tests are in include/duckos/abi.h, src/abi.c and tests/abi_contract.c.

## Build the ABI contract tests

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

Read the full [DABI64 v1 specification](docs/DABI64_V1.md).

## Current limits

This repository currently provides the ABI data-layout and validation foundation only. It is not yet a bootable kernel, syscall dispatcher, ELF linker or process loader. The stable call numbers are reserved contracts; services return NOT_IMPLEMENTED until their kernel implementation and tests exist.

The ABI is developed together with the Reaper compiler. Reaper's first DABI64 backend emits assembly for checked signed-i64 expressions; it does not yet compile complete Reaper programs or create runnable DuckOS executables.
