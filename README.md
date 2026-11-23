# DuckOS

DuckOS is the target operating-system project for the Reaper language toolchain. Its first concrete integration artifact is the versioned DABI64 user-entry contract.

## Current implementation boundary

- DABI64 v1 defines the x86-64 DuckOS function-entry registers, typed value layout, call frame, result object, status codes and ELF ABI-note identity.
- src/abi/dabi64.c provides a host-buildable reference validator and typed result helpers.
- CTest checks structure offsets, alignment, header validation, scalar argument tags and result handling.
- The Reaper native compiler has a DABI64 LIR backend for a scalar subset: i64 locals and parameters, direct craft calls, checked arithmetic, when, loop while and :: pipe calls.

This is not yet a bootable operating system. There is no kernel, scheduler, syscall dispatcher, ELF loader, user-space allocator, I/O service or collection runtime in this repository. The reference validator cannot validate arbitrary virtual-memory mappings. Those capabilities must be implemented and tested separately.

## Build the ABI contract tests

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

See docs/abi/DABI64.md for the binary contract and src/abi/dabi64.c for its reference implementation.
