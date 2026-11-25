#ifndef DUCKOS_FRAME_ALLOCATOR_H
#define DUCKOS_FRAME_ALLOCATOR_H

#include <stdint.h>
#include "boot_info.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_FRAME_PAGE_SIZE 4096u
#define DUCKOS_FRAME_ALLOCATOR_MAX_RANGES DUCKOS_BOOT_MAX_MEMORY_REGIONS
#define DUCKOS_FRAME_ALLOCATOR_FREE_CAPACITY 4096u

typedef struct duckos_frame_range {
    uint64_t start;
    uint64_t next;
    uint64_t end;
} duckos_frame_range;

typedef struct duckos_frame_allocator {
    uint32_t range_count;
    uint32_t active_range;
    uint64_t total_pages;
    uint64_t allocated_pages;
    uint32_t free_count;
    uint32_t reserved;
    uint64_t free_pages[DUCKOS_FRAME_ALLOCATOR_FREE_CAPACITY];
    duckos_frame_range ranges[DUCKOS_FRAME_ALLOCATOR_MAX_RANGES];
} duckos_frame_allocator;

typedef enum duckos_frame_allocator_status {
    DUCKOS_FRAME_ALLOCATOR_OK = 0,
    DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT,
    DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP,
    DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY,
    DUCKOS_FRAME_ALLOCATOR_EXHAUSTED,
    DUCKOS_FRAME_ALLOCATOR_INVALID_FREE,
    DUCKOS_FRAME_ALLOCATOR_FREE_LIST_FULL
} duckos_frame_allocator_status;

/*
 * Initializes a single-core, monotonic bootstrap frame allocator.
 * Only validated USABLE regions are exposed; all other memory types remain
 * reserved. min_address excludes low firmware memory (normally the first MiB).
 */
duckos_frame_allocator_status duckos_frame_allocator_init(
    duckos_frame_allocator *allocator,
    const duckos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address
);

/* Returns one aligned 4 KiB physical page. A released page is reused before the bump frontier. */
duckos_frame_allocator_status duckos_frame_allocator_allocate(
    duckos_frame_allocator *allocator,
    uint64_t *physical_address
);

/* Releases a page previously returned by allocate; duplicate and foreign frees are rejected. */
duckos_frame_allocator_status duckos_frame_allocator_release(
    duckos_frame_allocator *allocator,
    uint64_t physical_address
);

#ifdef __cplusplus
}
#endif

#endif
