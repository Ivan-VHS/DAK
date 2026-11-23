# DuckOS Boot Handoff Contract v1

**Author / project direction:** Ivan-VHS  
**Implementation status:** host-testable C11 contract. It is not a bootloader, kernel or bootable image.

## Purpose

The first foundation component defines the data boundary between a future bootloader and the DuckOS kernel. The handoff uses fixed-width integer fields and carries a version and structure size. The physical memory map is passed separately so the record contains no native pointer whose width or layout changes across targets.

Implemented files:

- `foundation/boot_info.h` — v1 structures, memory-region types and validation status codes.
- `foundation/boot_info.c` — range, memory-map, image-overlap and framebuffer validation.
- `tests/test_boot_info.c` — host-side positive and negative fixtures.

## Handoff record

The v1 record contains:

- structure size and interface version;
- boot flags;
- kernel physical base and byte length;
- optional initramfs physical base and byte length;
- optional framebuffer address, size, dimensions, pitch and bits per pixel;
- memory-map entry count.

Each memory-map entry contains a 64-bit base, 64-bit length, typed region kind and flags.

## Validation rules

The validator rejects:

1. null record or memory-map pointer;
2. unsupported version or a record shorter than the v1 structure;
3. zero-length or overflowing kernel ranges;
4. half-specified, zero-length or overflowing initramfs ranges;
5. kernel/initramfs overlap;
6. partially populated or inconsistent framebuffer metadata;
7. unsupported framebuffer depth, undersized pitch or undersized framebuffer extent;
8. empty, oversized, unsorted, overlapping or malformed memory maps;
9. unknown memory-region types.

Memory-map entries must be sorted by ascending base and must not overlap. Gaps are allowed. The caller must map the handoff record and array before calling the validator; stored physical addresses are validated but never dereferenced by this routine.

## Compatibility policy

The version identifies the semantics of the record. `struct_size` allows a future compatible extension to append fields while retaining the v1 prefix. An incompatible change requires a new version and explicit negotiation in the boot protocol. The public record must not contain compiler-private pointers, C++ objects or kernel-private handles.

## Deliberate non-goals

This contract does not yet:

- enter long mode or establish CPU page tables;
- install an interrupt descriptor table;
- allocate physical or virtual memory;
- start a scheduler or process;
- mount an initramfs;
- draw to the framebuffer;
- probe or initialize hardware.

Those steps require a selected boot protocol and CPU target, recorded as architecture decisions before the kernel entry implementation.

## Build and test

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

For a GCC/Clang host build with address and undefined-behavior sanitizers:

```sh
cmake -S . -B build-sanitize -DDUCKOS_ENABLE_SANITIZERS=ON
cmake --build build-sanitize --parallel
ctest --test-dir build-sanitize --output-on-failure
```
