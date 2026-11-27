#include "frame_allocator.h"

#include <stdint.h>

static int align_up_page(uint64_t value, uint64_t *aligned) {
    const uint64_t mask = (uint64_t)DAKOS_FRAME_PAGE_SIZE - 1u;
    if (aligned == NULL || value > UINT64_MAX - mask) return 0;
    *aligned = (value + mask) & ~mask;
    return 1;
}

static int region_end(const dakos_memory_region *region, uint64_t *end) {
    if (region == NULL || end == NULL || region->length == 0u ||
        region->base > UINT64_MAX - region->length) {
        return 0;
    }
    *end = region->base + region->length;
    return 1;
}

dakos_frame_allocator_status dakos_frame_allocator_init(
    dakos_frame_allocator *allocator,
    const dakos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address
) {
    uint64_t previous_end = 0u;
    dakos_frame_allocator next = {0};

    if (allocator == NULL || regions == NULL || region_count == 0u ||
        region_count > DAKOS_BOOT_MAX_MEMORY_REGIONS) {
        return DAKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }

    for (uint32_t index = 0u; index < region_count; ++index) {
        const dakos_memory_region *region = &regions[index];
        uint64_t end;

        if (region->type < (uint32_t)DAKOS_MEMORY_USABLE ||
            region->type > (uint32_t)DAKOS_MEMORY_BAD ||
            !region_end(region, &end) ||
            (index != 0u && region->base < previous_end)) {
            return DAKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        previous_end = end;

        if (region->type != (uint32_t)DAKOS_MEMORY_USABLE) continue;

        uint64_t begin = region->base > min_address ? region->base : min_address;
        if (!align_up_page(begin, &begin)) {
            return DAKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        const uint64_t aligned_end = end & ~((uint64_t)DAKOS_FRAME_PAGE_SIZE - 1u);
        if (begin >= aligned_end) continue;

        const uint64_t pages = (aligned_end - begin) / DAKOS_FRAME_PAGE_SIZE;
        if (next.total_pages > UINT64_MAX - pages ||
            next.range_count >= DAKOS_FRAME_ALLOCATOR_MAX_RANGES) {
            return DAKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }

        dakos_frame_range *range = &next.ranges[next.range_count++];
        range->next = begin;
        range->end = aligned_end;
        next.total_pages += pages;
    }

    if (next.total_pages == 0u) {
        return DAKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY;
    }

    *allocator = next;
    return DAKOS_FRAME_ALLOCATOR_OK;
}

dakos_frame_allocator_status dakos_frame_allocator_allocate(
    dakos_frame_allocator *allocator,
    uint64_t *physical_address
) {
    if (allocator == NULL || physical_address == NULL) {
        return DAKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }

    while (allocator->active_range < allocator->range_count) {
        dakos_frame_range *range = &allocator->ranges[allocator->active_range];
        if (range->end >= DAKOS_FRAME_PAGE_SIZE &&
            range->next <= range->end - DAKOS_FRAME_PAGE_SIZE) {
            *physical_address = range->next;
            range->next += DAKOS_FRAME_PAGE_SIZE;
            ++allocator->allocated_pages;
            return DAKOS_FRAME_ALLOCATOR_OK;
        }
        ++allocator->active_range;
    }

    return DAKOS_FRAME_ALLOCATOR_EXHAUSTED;
}
