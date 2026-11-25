#include "frame_allocator.h"

#include <stdint.h>

static int align_up_page(uint64_t value, uint64_t *aligned) {
    const uint64_t mask = (uint64_t)DAK_FRAME_PAGE_SIZE - 1u;
    if (aligned == NULL || value > UINT64_MAX - mask) return 0;
    *aligned = (value + mask) & ~mask;
    return 1;
}

static int region_end(const dak_memory_region *region, uint64_t *end) {
    if (region == NULL || end == NULL || region->length == 0u ||
        region->base > UINT64_MAX - region->length) {
        return 0;
    }
    *end = region->base + region->length;
    return 1;
}

dak_frame_allocator_status dak_frame_allocator_init(
    dak_frame_allocator *allocator,
    const dak_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address
) {
    uint64_t previous_end = 0u;

    if (allocator == NULL || regions == NULL || region_count == 0u ||
        region_count > DAK_BOOT_MAX_MEMORY_REGIONS) {
        return DAK_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }

    allocator->range_count = 0u;
    allocator->active_range = 0u;
    allocator->total_pages = 0u;
    allocator->allocated_pages = 0u;
    for (uint32_t index = 0u; index < DAK_FRAME_ALLOCATOR_MAX_RANGES; ++index) {
        allocator->ranges[index].next = 0u;
        allocator->ranges[index].end = 0u;
    }

    for (uint32_t index = 0u; index < region_count; ++index) {
        const dak_memory_region *region = &regions[index];
        uint64_t end;

        if (region->type < (uint32_t)DAK_MEMORY_USABLE ||
            region->type > (uint32_t)DAK_MEMORY_BAD ||
            !region_end(region, &end) ||
            (index != 0u && region->base < previous_end)) {
            return DAK_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        previous_end = end;

        if (region->type != (uint32_t)DAK_MEMORY_USABLE) continue;

        uint64_t begin = region->base > min_address ? region->base : min_address;
        if (!align_up_page(begin, &begin)) {
            return DAK_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        const uint64_t aligned_end = end & ~((uint64_t)DAK_FRAME_PAGE_SIZE - 1u);
        if (begin >= aligned_end) continue;

        const uint64_t pages = (aligned_end - begin) / DAK_FRAME_PAGE_SIZE;
        if (allocator->total_pages > UINT64_MAX - pages ||
            allocator->range_count >= DAK_FRAME_ALLOCATOR_MAX_RANGES) {
            return DAK_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }

        dak_frame_range *range = &allocator->ranges[allocator->range_count++];
        range->next = begin;
        range->end = aligned_end;
        allocator->total_pages += pages;
    }

    return allocator->total_pages != 0u ?
        DAK_FRAME_ALLOCATOR_OK : DAK_FRAME_ALLOCATOR_NO_USABLE_MEMORY;
}

dak_frame_allocator_status dak_frame_allocator_allocate(
    dak_frame_allocator *allocator,
    uint64_t *physical_address
) {
    if (allocator == NULL || physical_address == NULL) {
        return DAK_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }

    while (allocator->active_range < allocator->range_count) {
        dak_frame_range *range = &allocator->ranges[allocator->active_range];
        if (range->end >= DAK_FRAME_PAGE_SIZE &&
            range->next <= range->end - DAK_FRAME_PAGE_SIZE) {
            *physical_address = range->next;
            range->next += DAK_FRAME_PAGE_SIZE;
            ++allocator->allocated_pages;
            return DAK_FRAME_ALLOCATOR_OK;
        }
        ++allocator->active_range;
    }

    return DAK_FRAME_ALLOCATOR_EXHAUSTED;
}
