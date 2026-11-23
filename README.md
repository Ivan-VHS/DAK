# DuckOS

DuckOS is the planned native operating system target for Reaper. The repository currently contains the DABI64 v1 host boundary and its mock-kernel contract test; it is **not yet a bootable operating system**.

## Current foundation

- \`include/duckos/reaper_host_v1.h\` adapts a versioned 64-bit syscall interface to Reaper's \`ReaperDabiHostV1\` callbacks.
- Syscall IDs 1–4 define the initial \`write\`, \`read\`, \`open\` and \`close\` surface required by Reaper I/O.
- \`tests/test_reaper_host.c\` verifies the adapter against a mock syscall provider.
- \`docs/DABI64_HOST.md\` records the kernel-side validation and security requirements.

The adapter deliberately does not pretend that a syscall entry point, VFS, page-table manager or scheduler already exists. Those are kernel implementation stages, not properties of this interface.

## Verify the host contract

From a DuckOS checkout with a sibling Reaper checkout:

\`\`\`sh
cmake -S . -B build \\
  -DDUCKOS_BUILD_DABI64_TESTS=ON \\
  -DREAPER_SOURCE_DIR=../Reaper
cmake --build build --parallel
ctest --test-dir build --output-on-failure
\`\`\`

The test links the Reaper DABI64 runtime source directly and uses a mock syscall provider. It does not boot DuckOS or execute a Reaper program inside a kernel.

## Bring-up order

1. Establish a reproducible x86-64 boot path and serial diagnostics.
2. Add physical and virtual memory management, page tables and a kernel heap.
3. Implement the syscall entry/dispatcher and process-owned descriptor table.
4. Add VFS and bounded user-memory copy routines for \`read\`, \`write\`, \`open\` and \`close\`.
5. Add ELF64 validation/loading, process address spaces and userspace entry dispatch.
6. Add process lifecycle and scheduler primitives.
7. Boot a DABI64 runtime test program, then Reaper stage 0 and stage 1.
8. Demonstrate stage-2 self-compilation and reproducible bootstrap before claiming self-hosting.

## Ownership

Project documentation identifies Ivan-VHS as the DuckOS project author/developer. Third-party components and contributors must retain their own notices and attribution when introduced.
