#ifndef DUCKOS_FRAME_ALLOCATOR_H
#define DUCKOS_FRAME_ALLOCATOR_H

#include <stdint.h>
#include "boot_info.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_FRAME_PAGE_SIZE UINT64_C(4096)
#define DUCKOS_FRAME_ALLOCATOR_MAX_RANGES DUCKOS_BOOT_MAX_MEMORY_REGIONS
#define DUCKOS_FRAME_ALLOCATOR_MAX_ALLOCATED_RANGES 1024u

typedef struct duckos_frame_range {
    uint64_t base;
    uint64_t end;
} duckos_frame_range;

typedef struct duckos_frame_allocator {
    uint32_t free_range_count;
    uint32_t allocated_range_count;
    uint64_t total_pages;
    uint64_t free_pages;
    uint64_t allocated_pages;
    duckos_frame_range free_ranges[DUCKOS_FRAME_ALLOCATOR_MAX_RANGES];
    duckos_frame_range allocated_ranges[DUCKOS_FRAME_ALLOCATOR_MAX_ALLOCATED_RANGES];
} duckos_frame_allocator;

typedef enum duckos_frame_allocator_status {
    DUCKOS_FRAME_ALLOCATOR_OK = 0,
    DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT,
    DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP,
    DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY,
    DUCKOS_FRAME_ALLOCATOR_EXHAUSTED,
    DUCKOS_FRAME_ALLOCATOR_INVALID_ALIGNMENT,
    DUCKOS_FRAME_ALLOCATOR_INVALID_RELEASE,
    DUCKOS_FRAME_ALLOCATOR_METADATA_EXHAUSTED,
    DUCKOS_FRAME_ALLOCATOR_CORRUPT_STATE
} duckos_frame_allocator_status;

duckos_frame_allocator_status duckos_frame_allocator_init(
    duckos_frame_allocator *allocator,
    const duckos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address
);

duckos_frame_allocator_status duckos_frame_allocator_allocate(
    duckos_frame_allocator *allocator,
    uint64_t *physical_address
);

duckos_frame_allocator_status duckos_frame_allocator_allocate_contiguous(
    duckos_frame_allocator *allocator,
    uint64_t page_count,
    uint64_t alignment_pages,
    uint64_t *physical_address
);

duckos_frame_allocator_status duckos_frame_allocator_release(
    duckos_frame_allocator *allocator,
    uint64_t physical_address,
    uint64_t page_count
);

#ifdef __cplusplus
}
#endif
#endif
