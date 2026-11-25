#ifndef DUCKOS_X86_VIRTUAL_MEMORY_H
#define DUCKOS_X86_VIRTUAL_MEMORY_H

#include <stdint.h>
#include "boot_info.h"
#include "frame_allocator.h"
#include "page_table.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Builds and activates a new four-level kernel address space. */
int duckos_x86_virtual_memory_init(
    duckos_frame_allocator *allocator,
    duckos_x86_page_table *page_tables,
    const duckos_boot_info_v1 *boot_info,
    const duckos_memory_region *memory_regions,
    uint64_t hhdm_offset
);

#ifdef __cplusplus
}
#endif

#endif
