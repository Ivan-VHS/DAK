# DuckOS Boot Handoff Contract v1

**Author / project direction:** Ivan-VHS  
**Implementation status:** host-testable C11 contract and experimental x86_64 Limine stage-0 adapter. The image is firmware-bootable when the BIOS/UEFI QEMU gate passes; it is not a complete kernel or usable desktop OS.

## Purpose

The first foundation component defines the data boundary between a future bootloader and the DuckOS kernel. The handoff uses fixed-width integer fields and carries a version and structure size. The physical memory map is passed separately so the record contains no native pointer whose width or layout changes across targets.

Implemented files:

- `foundation/boot_info.h` — v1 structures, memory-region types and validation status codes.
- `foundation/boot_info.c` — range, memory-map, image-overlap and framebuffer validation.
- `tests/test_boot_info.c` — host-side positive and negative fixtures.
- `kernel/boot/entry.c` — freestanding x86_64 Limine entry, COM1 diagnostics and basic 32-bit RGB framebuffer output.
- `kernel/linker.ld` — high-half ELF layout with separate read-only, executable and writable load segments.
- `boot/build-iso.sh` — pinned hybrid BIOS/UEFI ISO build; `boot/test-qemu.sh` — serial-marker boot test.

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
9. unknown memory-region types;
10. a kernel or initramfs range not fully covered by reserved memory-map entries;
11. a framebuffer range not fully covered by MMIO memory-map entries.

Memory-map entries must be sorted by ascending base and must not overlap. Gaps are allowed. The caller must map the handoff record and array before calling the validator; stored physical addresses are validated but never dereferenced by this routine.

## Compatibility policy

The version identifies the semantics of the record. `struct_size` allows a future compatible extension to append fields while retaining the v1 prefix. An incompatible change requires a new version and explicit negotiation in the boot protocol. The public record must not contain compiler-private pointers, C++ objects or kernel-private handles.

## Deliberate non-goals

This v1 handoff and stage-0 entry do not yet:

- build or manage kernel page tables or a physical/virtual page allocator;
- install an interrupt descriptor table, APIC or timer;
- allocate general-purpose kernel memory;
- start a scheduler, process, thread or syscall runtime;
- mount an initramfs or filesystem;
- provide a production framebuffer console, compositor or display driver;
- probe and initialise PCI/USB/ACPI devices or load drivers.

The boot protocol and initial CPU target are now selected for stage 0. The listed runtime, allocator, interrupt, process and device subsystems remain subsequent native implementation gates.

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


## Bootable stage-0 image

The native adapter is built into the experimental x86_64 ISO using the instructions in [BOOTABLE_IMAGE.md](BOOTABLE_IMAGE.md). Limine is pinned by version and SHA-256, and the upstream protocol header retains its 0BSD notice. The adapter rejects unsupported Limine base revision, missing required responses, malformed map data, reserved-range violations and framebuffer/MMIO inconsistencies. It reports the handoff and then halts; it does not transfer into an init process or claim that the remaining kernel subsystems exist.


## DuckBoot handoff boundary

DuckBoot defines a separate versioned handoff envelope in duckboot/include/duckboot/handoff.h. The envelope carries virtual addresses for the validated Boot Info v1 record, memory-map array, HHDM base, framebuffer and command line, plus framebuffer channel masks. The Boot Info v1 record itself remains pointer-free.

The DuckBoot feature branch now contains both sides of the UEFI contract:

- duckboot/uefi/entry.c produces the envelope after validating the ELF64 kernel, mapping its PT_LOAD segments, building page tables and normalizing the EFI memory map.
- duckboot/kernel_entry.c consumes the envelope, validates Boot Info v1 and initializes the early physical-frame allocator.
- duckboot/uefi/enter.S switches to the new CR3 and kernel stack, then enters the high-half kernel using the documented x86-64 System V entry convention.

The active main-branch image remains unchanged until the feature branch passes the UEFI QEMU/OVMF gate. The image builder retains a separate Limine BIOS fallback. The UEFI handoff must be verified by the exact serial marker DUCKOS_BOOT_OK stage=1 loader=duckboot; a PE32+ link alone does not count as a successful transfer.
