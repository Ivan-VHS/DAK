# DABI64 v1 kernel-facing contract

DuckOS implements \`DuckOsSyscallInterfaceV1\` in \`include/duckos/reaper_host_v1.h\` as the narrow bridge between the Reaper runtime and the kernel syscall entry.

| ID | Operation | Arguments | Return |
|---:|---|---|---|
| 1 | write | descriptor, user pointer, byte length | bytes written or negative error |
| 2 | read | descriptor, user pointer, capacity | bytes read or negative error |
| 3 | open | user path pointer, path length, mode | descriptor or negative error |
| 4 | close | descriptor | zero or negative error |

The adapter takes six 64-bit arguments and returns a signed 64-bit result. Architecture-specific entry code must normalize register arguments into this interface.

## Kernel obligations

- Validate the full user-memory range, permissions and integer-overflow boundaries before copying.
- Copy path bytes to bounded kernel-owned storage before lookup; no NUL terminator is assumed.
- Apply per-process descriptor ownership and reject stale or foreign descriptors.
- Permit short reads/writes, return the exact byte count and never write beyond the supplied range.
- Bound every transfer and path length.
- Return stable negative errors without exposing kernel addresses.
- Apply explicit file policy; no implicit process, shell, network or device capabilities are granted.

This contract is not a syscall implementation. A kernel entry point, VFS, process model and memory manager must exist and pass their own tests before the adapter can run in DuckOS.
