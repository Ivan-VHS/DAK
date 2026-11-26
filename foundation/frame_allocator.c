#include "frame_allocator.h"

#include <stdint.h>

static int align_up_page(uint64_t value, uint64_t *aligned) {
    const uint64_t mask = (uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u;
    if (aligned == NULL || value > UINT64_MAX - mask) return 0;
    *aligned = (value + mask) & ~mask;
    return 1;
}

static int region_end(const duckos_memory_region *region, uint64_t *end) {
    if (region == NULL || end == NULL || region->length == 0u ||
        region->base > UINT64_MAX - region->length) {
        return 0;
    }
    *end = region->base + region->length;
    return 1;
}

duckos_frame_allocator_status duckos_frame_allocator_init(
    duckos_frame_allocator *allocator,
    const duckos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address
) {
    uint64_t previous_end = 0u;

    if (allocator == NULL || regions == NULL || region_count == 0u ||
        region_count > DUCKOS_BOOT_MAX_MEMORY_REGIONS) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }

    allocator->range_count = 0u;
    allocator->active_range = 0u;
    allocator->total_pages = 0u;
    allocator->allocated_pages = 0u;
    allocator->free_count = 0u;
    allocator->reserved = 0u;
    for (uint32_t index = 0u; index < DUCKOS_FRAME_ALLOCATOR_MAX_RANGES; ++index) {
        allocator->ranges[index].start = 0u;
        allocator->ranges[index].next = 0u;
        allocator->ranges[index].end = 0u;
    }

    for (uint32_t index = 0u; index < region_count; ++index) {
        const duckos_memory_region *region = &regions[index];
        uint64_t end;

        if (region->type < (uint32_t)DUCKOS_MEMORY_USABLE ||
            region->type > (uint32_t)DUCKOS_MEMORY_BAD ||
            !region_end(region, &end) ||
            (index != 0u && region->base < previous_end)) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        previous_end = end;

        if (region->type != (uint32_t)DUCKOS_MEMORY_USABLE) continue;

        uint64_t begin = region->base > min_address ? region->base : min_address;
        if (!align_up_page(begin, &begin)) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        const uint64_t aligned_end = end & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u);
        if (begin >= aligned_end) continue;

        const uint64_t pages = (aligned_end - begin) / DUCKOS_FRAME_PAGE_SIZE;
        if (allocator->total_pages > UINT64_MAX - pages ||
            allocator->range_count >= DUCKOS_FRAME_ALLOCATOR_MAX_RANGES) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }

        duckos_frame_range *range = &allocator->ranges[allocator->range_count++];
        range->start = begin;
        range->next = begin;
        range->end = aligned_end;
        allocator->total_pages += pages;
    }

    return allocator->total_pages != 0u ?
        DUCKOS_FRAME_ALLOCATOR_OK : DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY;
}

duckos_frame_allocator_status duckos_frame_allocator_allocate(
    duckos_frame_allocator *allocator,
    uint64_t *physical_address
) {
    if (allocator == NULL || physical_address == NULL) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }

    if (allocator->free_count != 0u) {
        *physical_address = allocator->free_pages[--allocator->free_count];
        ++allocator->allocated_pages;
        return DUCKOS_FRAME_ALLOCATOR_OK;
    }

    while (allocator->active_range < allocator->range_count) {
        duckos_frame_range *range = &allocator->ranges[allocator->active_range];
        if (range->end >= DUCKOS_FRAME_PAGE_SIZE &&
            range->next <= range->end - DUCKOS_FRAME_PAGE_SIZE) {
            *physical_address = range->next;
            range->next += DUCKOS_FRAME_PAGE_SIZE;
            ++allocator->allocated_pages;
            return DUCKOS_FRAME_ALLOCATOR_OK;
        }
        ++allocator->active_range;
    }

    return DUCKOS_FRAME_ALLOCATOR_EXHAUSTED;
}


duckos_frame_allocator_status duckos_frame_allocator_release(
    duckos_frame_allocator *allocator,
    uint64_t physical_address
) {
    if (allocator == NULL ||
        (physical_address & ((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u)) != 0u) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }
    if (allocator->allocated_pages == 0u) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_FREE;
    }

    int was_allocated = 0;
    for (uint32_t index = 0u; index < allocator->range_count; ++index) {
        const duckos_frame_range *range = &allocator->ranges[index];
        if (physical_address >= range->start && physical_address < range->next) {
            was_allocated = 1;
            break;
        }
    }
    if (was_allocated == 0) return DUCKOS_FRAME_ALLOCATOR_INVALID_FREE;

    for (uint32_t index = 0u; index < allocator->free_count; ++index) {
        if (allocator->free_pages[index] == physical_address) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_FREE;
        }
    }
    if (allocator->free_count >= DUCKOS_FRAME_ALLOCATOR_FREE_CAPACITY) {
        return DUCKOS_FRAME_ALLOCATOR_FREE_LIST_FULL;
    }

    allocator->free_pages[allocator->free_count++] = physical_address;
    --allocator->allocated_pages;
    return DUCKOS_FRAME_ALLOCATOR_OK;
}
