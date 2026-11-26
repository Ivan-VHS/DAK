#ifndef DUCKOS_X86_64_PAGING_H
#define DUCKOS_X86_64_PAGING_H

#include <stdint.h>

#include "frame_allocator.h"
#include "page_table.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Clone Limine's active hierarchy into allocator-owned tables and activate the new CR3. */
int duckos_x86_paging_takeover(
    duckos_page_table_space *space,
    duckos_frame_allocator *frames,
    uint64_t hhdm_offset
);

uint64_t duckos_x86_paging_read_cr3(void);
int duckos_x86_paging_nx_enabled(void);

/* Protect a page-aligned half-open virtual-address range. */
int duckos_x86_paging_protect_range(
    duckos_page_table_space *space,
    uint64_t start,
    uint64_t end,
    uint64_t flags
);

#ifdef __cplusplus
}
#endif

#endif
