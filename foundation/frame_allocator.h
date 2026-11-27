#ifndef DUCKOS_FRAME_ALLOCATOR_H
#define DUCKOS_FRAME_ALLOCATOR_H

#include <stdint.h>
#include "boot_info.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_FRAME_PAGE_SIZE 4096u
#define DUCKOS_FRAME_ALLOCATOR_MAX_RANGES DUCKOS_BOOT_MAX_MEMORY_REGIONS

typedef struct duckos_frame_range {
    uint64_t next;
    uint64_t end;
} duckos_frame_range;

typedef struct duckos_frame_allocator {
    uint32_t range_count;
    uint32_t active_range;
    uint64_t total_pages;
    uint64_t allocated_pages;
    uint64_t reserved_pages;
    uint64_t managed_pages;
    duckos_frame_range ranges[DUCKOS_FRAME_ALLOCATOR_MAX_RANGES];
} duckos_frame_allocator;

typedef enum duckos_frame_allocator_status {
    DUCKOS_FRAME_ALLOCATOR_OK = 0,
    DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT,
    DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP,
    DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY,
    DUCKOS_FRAME_ALLOCATOR_EXHAUSTED,
    DUCKOS_FRAME_ALLOCATOR_CORRUPT_STATE
} duckos_frame_allocator_status;

/*
 * Builds a single-core bootstrap frame allocator transactionally.
 * total_pages counts only allocatable complete 4 KiB pages.
 * reserved_pages counts complete RAM pages unavailable to this allocator,
 * including firmware memory and usable pages below min_address.
 * managed_pages is exactly total_pages + reserved_pages.
 * MMIO and BAD memory are not counted as managed RAM.
 */
duckos_frame_allocator_status duckos_frame_allocator_init(
    duckos_frame_allocator *allocator,
    const duckos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address
);

/* Verify free + allocated + reserved == managed for complete physical pages. */
int duckos_frame_allocator_accounting_valid(
    const duckos_frame_allocator *allocator
);

/* Returns one aligned 4 KiB physical page. Pages are never returned twice. */
duckos_frame_allocator_status duckos_frame_allocator_allocate(
    duckos_frame_allocator *allocator,
    uint64_t *physical_address
);

#ifdef __cplusplus
}
#endif

#endif
