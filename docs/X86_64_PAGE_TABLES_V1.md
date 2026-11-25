# x86-64 page-table manager v1

**Status:** implemented and host-tested page-table structure management. The active kernel address space is not replaced.

## Scope

The native boundary manages four-level x86-64 page tables with 48-bit canonical virtual addresses and 4 KiB leaf mappings. It can create missing intermediate tables, map and unmap pages, and translate virtual addresses through the supplied resolver.

The mapper is deliberately separate from Reaper policy. Reaper decides whether a mapping request is admissible; this native module constructs the hardware-defined page-table entries after the kernel supplies an allocator and a writable mapping of each table page.

## Contract

- The root is an allocated, zeroed, page-aligned physical page.
- The allocator returns one page-aligned physical address at a time.
- The resolver returns a writable kernel mapping of that physical page.
- The optional invalidation callback is invoked for a changed leaf address. A caller must only bind it to a privileged TLB operation when this address space is active.
- Mutation must be serialized by the caller; this first version is not SMP-safe.
- Only 4 KiB leaf pages are supported. A present huge-page entry in an intermediate level is rejected.
- User mappings must be in the lower canonical half and carry the USER bit.
- Writable mappings must also carry NO_EXECUTE. Executable mappings are read-only.
- Leaf flags are explicitly allowlisted. Unknown/reserved bits are rejected.
- No raw page-table pointer or physical address is exposed through a user ABI.

## API

duckos_x86_64_page_table_init binds the root and callbacks.

duckos_x86_64_page_map_4k creates missing intermediate levels and installs one leaf entry. Duplicate mappings are rejected rather than overwritten.

duckos_x86_64_page_translate resolves the physical address, preserving the page offset, and optionally returns leaf flags.

duckos_x86_64_page_unmap_4k removes the leaf entry and requests invalidation through the optional callback.

## Deliberate non-claims

This module does not load CR3, turn on paging, create a ring-3 task, copy data to/from user memory, handle page faults, flush remote CPU TLBs, free empty page-table levels, implement 2 MiB/1 GiB pages, or manage MMIO/DMA. The current Limine-provided address space remains active.

Those features require explicit architecture gates and QEMU coverage before the kernel can claim a running user process.
