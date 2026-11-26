# DuckOS paging Stage 2 — PR #162

**Status:** proposed implementation on `feat/x86_64-owned-page-tables-2026-11-25`; not merged and not yet QEMU-verified. The currently merged `main` image remains Stage 1.

## Scope

The branch adds a host-testable four-level x86_64 page-table manager with:
- PML4 creation and deep cloning of the active Limine hierarchy;
- 48-bit canonical virtual-address checks and physical-address-width validation;
- 4 KiB map, unmap, protect and translate operations;
- 1 GiB and 2 MiB huge-page splitting;
- release of empty intermediate page-table pages;
- W^X enforcement when NX is supported.

The frame allocator gains a bounded release/reuse list with duplicate-free and foreign-address rejection.

## Native takeover

The x86_64 bridge clones the active page-table tree into DuckOS-owned frames, switches CR3 to the new PML4, enables EFER.NXE when available and sets CR0.WP. Cloning the active hierarchy is intended to preserve the current kernel, stack, HHDM and framebuffer mappings while the kernel assumes page-table ownership.

Linker symbols delimit page-aligned sections. The boot path attempts to make text executable/read-only, rodata and Limine request pages read-only/NX, and data writable/NX.

A boot-time smoke test attempts a live 4 KiB map, translate, permission change, unmap and frame release.

## Verification gates

The PR adds CTest coverage for canonical addresses, mapping, permissions, clone ownership, huge-page splitting, unmapping and allocator reuse. Its BIOS and UEFI QEMU gate requires:
- the CPU exception IDT marker;
- an owned-CR3 marker;
- a live map/protect/unmap marker;
- `DUCKOS_BOOT_OK stage=2`.

These are required checks, not evidence of a passed run until GitHub Actions reports success on the current PR head.

## Not yet implemented

This is not a complete VM subsystem. The branch does not yet provide a buddy allocator, demand paging, copy-on-write, recoverable page-fault handling, SMP-safe allocator locks, cross-CPU TLB shootdown, per-process address spaces, user-mode memory isolation or an MMIO/DMA mapping policy. Five-level paging is rejected rather than partially supported. IDT/APIC/timer scheduling, processes, Ring 3, DABI64, filesystem, drivers, native desktop and the remaining Full System domains are separate follow-up work.

The privileged bridge uses narrow freestanding C11 and x86_64 Assembly. Reaper remains the intended native system language and policy/runtime direction; the existing Reaper VM/process files are policy contracts, not the privileged paging implementation.
