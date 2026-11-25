#ifndef DUCKOS_FRAME_ALLOCATOR_H
#define DUCKOS_FRAME_ALLOCATOR_H

#include <stdint.h>
#include "boot_info.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_FRAME_PAGE_SIZE 4096u
#define DUCKOS_FRAME_ALLOCATOR_MAX_RANGES DUCKOS_BOOT_MAX_MEMORY_REGIONS

typedef struct duckos_frame_managed_range {
    uint64_t base;
    uint64_t end;
} duckos_frame_managed_range;

typedef struct duckos_frame_allocator {
    uint64_t hhdm_offset;
    uint64_t free_head_phys;
    uint64_t total_pages;
    uint64_t free_pages;
    uint64_t allocated_pages;
    uint32_t range_count;
    duckos_frame_managed_range ranges[DUCKOS_FRAME_ALLOCATOR_MAX_RANGES];
} duckos_frame_allocator;

typedef enum duckos_frame_allocator_status {
    DUCKOS_FRAME_ALLOCATOR_OK = 0,
    DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT = -1,
    DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP = -2,
    DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY = -3,
    DUCKOS_FRAME_ALLOCATOR_EXHAUSTED = -4,
    DUCKOS_FRAME_ALLOCATOR_INVALID_ALIGNMENT = -5,
    DUCKOS_FRAME_ALLOCATOR_OUT_OF_RANGE = -6,
    DUCKOS_FRAME_ALLOCATOR_ALREADY_FREE = -7,
    DUCKOS_FRAME_ALLOCATOR_COUNTER_ERROR = -8,
    DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR = -9
} duckos_frame_allocator_status;

/*
 * Initializes an intrusive, coalescing physical-page allocator.
 * Free-extent metadata lives in the first page of each free extent and is
 * reached through HHDM. The caller must keep that direct map accessible.
 */
duckos_frame_allocator_status duckos_frame_allocator_init(
    duckos_frame_allocator *allocator,
    const duckos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address,
    uint64_t hhdm_offset
);

/* Allocates a contiguous run whose physical base satisfies alignment_pages. */
duckos_frame_allocator_status duckos_frame_allocator_allocate_pages(
    duckos_frame_allocator *allocator,
    uint64_t page_count,
    uint64_t alignment_pages,
    uint64_t *physical_address
);

static inline duckos_frame_allocator_status duckos_frame_allocator_allocate(
    duckos_frame_allocator *allocator,
    uint64_t *physical_address
) {
    return duckos_frame_allocator_allocate_pages(allocator, 1u, 1u, physical_address);
}

/* Releases a run previously returned by this allocator and coalesces neighbors. */
duckos_frame_allocator_status duckos_frame_allocator_free(
    duckos_frame_allocator *allocator,
    uint64_t physical_address,
    uint64_t page_count
);

#ifdef __cplusplus
}
#endif

#endif
