# DuckOS

DuckOS is being built as a standalone operating-system project with a versioned
native calling convention for Reaper-generated programs.

## Current foundations

- DABI64 v1 defines the x86-64 call-frame contract and a 16-byte tagged value.
- The host ABI validator checks frame shape, alignment, version, argument count,
  and the scalar \`i64\` calling path.
- The runtime library provides owned values, strings, dynamic arrays, and
  iterators through an injected allocator.
- The DABI64 contract and runtime are host-buildable C17 components with tests.

The current compiler integration is still a scalar \`i64\` subset. Runtime value
tags do not yet mean that the Reaper native backend can generate string,
collection, iterator, or I/O operations.

## Build and test

\`\`\`sh
cmake -S . -B build -DBUILD_TESTING=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
\`\`\`

## Runtime boundary

The runtime currently has no kernel heap binding, syscall dispatcher, console or
file I/O, scheduler, ELF linker/loader, process startup, or bootable image.
See [DABI64](docs/abi/DABI64.md) and
[Runtime ownership](docs/runtime/OWNERSHIP.md) for the current contracts.
