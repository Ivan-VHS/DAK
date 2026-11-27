#ifndef DAKOS_FRAME_ALLOCATOR_H
#define DAKOS_FRAME_ALLOCATOR_H

#include <stdint.h>
#include "boot_info.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DAKOS_FRAME_PAGE_SIZE 4096u
#define DAKOS_FRAME_ALLOCATOR_MAX_RANGES DAKOS_BOOT_MAX_MEMORY_REGIONS

typedef struct dakos_frame_range {
    uint64_t next;
    uint64_t end;
} dakos_frame_range;

typedef struct dakos_frame_allocator {
    uint32_t range_count;
    uint32_t active_range;
    uint64_t total_pages;
    uint64_t allocated_pages;
    dakos_frame_range ranges[DAKOS_FRAME_ALLOCATOR_MAX_RANGES];
} dakos_frame_allocator;

typedef enum dakos_frame_allocator_status {
    DAKOS_FRAME_ALLOCATOR_OK = 0,
    DAKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT,
    DAKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP,
    DAKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY,
    DAKOS_FRAME_ALLOCATOR_EXHAUSTED
} dakos_frame_allocator_status;

/*
 * Initializes a single-core, monotonic bootstrap frame allocator.
 * Only validated USABLE regions are exposed; all other memory types remain
 * reserved. min_address excludes low firmware memory (normally the first MiB).
 * Initialization is transactional: failure leaves the previous allocator intact.
 */
dakos_frame_allocator_status dakos_frame_allocator_init(
    dakos_frame_allocator *allocator,
    const dakos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address
);

/* Returns one aligned 4 KiB physical page. Pages are never returned twice. */
dakos_frame_allocator_status dakos_frame_allocator_allocate(
    dakos_frame_allocator *allocator,
    uint64_t *physical_address
);

#ifdef __cplusplus
}
#endif

#endif
