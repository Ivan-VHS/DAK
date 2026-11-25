# ADR 0001 — First freestanding bring-up target

- **Status:** Proposed for the first implementation wave
- **Date:** 2026-11-25
- **Owner:** DuckOS architecture
- **Scope:** first bootable x86-64 development target only

## Context

DuckOS currently has a host-testable C11 boot-info v1 data contract and Reaper-authored models for boot phases, memory arithmetic, task selection, IPC backpressure and capability policy. It does not yet contain a freestanding kernel entry point, an interrupt table, real page tables, a context switch, an init process or a bootable image. The existing boot-info contract is not a boot protocol.

The first implementation target must make early boot reproducible in CI, provide a stable handoff to the kernel, and allow deterministic serial/debug output before any storage, network, graphics or driver complexity is introduced.

## Decision

Use **x86-64 as the first PC architecture**, the **Limine boot protocol** as the first loader-to-kernel handoff, and **QEMU full-system emulation** as the first automated hardware environment.

The target profile is:

- little-endian x86-64, ELF64 kernel image;
- Limine protocol with an explicitly pinned base revision and versioned requests;
- Limine's memory-map, framebuffer, HHDM and multiprocessor responses are consumed only through validated descriptors;
- the existing DuckOS `boot-info v1` record remains the internal, fixed-size kernel handoff for fields it can represent;
- memory-map entries that cannot be represented safely in v1 are conservatively mapped to reserved, not silently marked usable;
- bootloader-reclaimable memory remains reserved until all bootloader response and module references have been released;
- serial output and a deterministic boot marker are the first acceptance target;
- QEMU system emulation is the mandatory CI target; physical hardware is a later qualification tier.

Limine is a third-party bootloader, not DuckOS kernel code. Pin an exact release or commit, record its BSD-2-Clause notice, and keep the protocol specification's 0BSD notice. Do not copy implementation code into DuckOS. The boot protocol's current specification describes 64-bit pointers, request/response features, memory-map entries, framebuffer metadata and an HHDM whose base must be discovered rather than hard-coded.

Direct UEFI API implementation is not part of this first slice. The UEFI Forum's specification access page states that the documents are made available for reading and that implementation/distribution rights require the adopter agreement. Using a separately licensed boot protocol avoids silently assuming those rights. Revisit direct UEFI implementation only after its license/implementation permission has been explicitly cleared.

## Why this target

1. It gives DuckOS one deterministic CPU and executable format rather than an unbounded multi-architecture target.
2. Limine separates the loader protocol from the kernel and already exposes the memory map and framebuffer needed for the first kernel entry.
3. QEMU provides full-system emulation and an x86-64 guest target suitable for unattended boot, serial capture and GDB debugging.
4. It keeps the bootloader replaceable: DuckOS owns its internal boot-info representation and can add other protocol adapters later.
5. It allows the first kernel milestones to be written and tested without installing drivers, flashing firmware or mutating a host disk.

## Boot handoff and memory policy

The Limine adapter must validate every pointer/count/region before dereferencing it. The kernel must not assume a fixed HHDM offset, that every memory-map type is mapped, or that a framebuffer is present.

Initial Limine memory-type mapping to DuckOS boot-info v1:

| Limine type | DuckOS v1 type | Initial policy |
|---|---|---|
| Usable | Usable | Eligible for early allocator after range validation |
| Reserved | Reserved | Never allocate |
| ACPI reclaimable | ACPI reclaimable | Retain until ACPI consumers finish |
| ACPI NVS | ACPI NVS | Never treat as ordinary RAM |
| Bad memory | Bad | Never allocate |
| Bootloader reclaimable | Reserved | Reclaim only after all boot responses/modules are released |
| Executable and modules | Reserved | Retain until ownership/copy policy is explicit |
| Framebuffer | MMIO | Map with device-appropriate cache policy |
| Reserved mapped | Reserved | Preserve mapping metadata; do not allocate |

The current `duckos/kernel/limine_map.rpr` module validates this *type translation policy only*. It does not parse protocol pointers, construct a boot-info record from native memory, map pages or free bootloader memory.

## Dependency order

1. Reaper native target support: fixed-width unsigned integers, records/arrays, source-mapped diagnostics, freestanding runtime profile and target-aware code generation.
2. Limine-to-DuckOS boot adapter and a minimal x86-64 entry shim.
3. Serial logging, panic path, validated boot-info and emulator boot marker.
4. Physical page-frame allocator with reserved-range exclusion and allocator invariants.
5. GDT, IDT, exception reporting, timer and interrupt-controller ownership.
6. Virtual memory and page tables with W^X, per-address-space isolation and TLB invalidation.
7. Context switching, kernel stacks, preemption and process lifecycle.
8. Syscall entry/return and copy-in/copy-out validation.
9. Initramfs, ELF loader, user-mode first process and capability checks.
10. VFS, IPC transport, service supervisor and device discovery.
11. Framebuffer console, input, compositor and user desktop.

No later stage may be labelled complete because an earlier policy model or simulator passes.

## Required acceptance evidence

- Reproducible cross-build with compiler/linker/tool versions recorded.
- ELF header, load-segment, alignment and relocation validation.
- QEMU full-system boot with a bounded timeout and a required serial marker.
- Memory-map fixtures covering unsorted, overlapping, empty, unknown, overflowing and reserved ranges.
- Fault-injection cases for missing boot responses and invalid framebuffer metadata.
- AddressSanitizer/UndefinedBehaviorSanitizer for host validators; emulator tests for privileged paths.
- A retained image digest and serial log for each qualifying CI build.

## Rejected alternatives

- **Build a full UEFI loader first:** out of scope for the initial kernel milestone and introduces direct UEFI specification implementation obligations before the kernel can demonstrate value.
- **Use multiple CPU architectures immediately:** multiplies ABI, page-table, interrupt and CI paths before one vertical boot path is proven.
- **Treat Reaper's current scalar AOT as a freestanding kernel compiler:** its documented backend emits a limited hosted C17 subset; it is not yet an ELF writer or freestanding runtime.
- **Treat policy modules as hardware operations:** choosing a task is not a context switch; mapping metadata is not a page-table write; interrupt policy is not an IDT/ISR; IPC queue state is not cross-process transport.

## Licensing and provenance

Pin Limine and its protocol source independently. Preserve the bootloader's BSD-2-Clause notice and the protocol repository's 0BSD notice. Keep the DuckOS boot-info v1 implementation independently authored and do not copy Limine source structures wholesale into the kernel's public ABI.
