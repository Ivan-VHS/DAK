#include "frame_allocator.h"

#include "invariants.h"

#include <stdint.h>

static int add_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (result == NULL || left > UINT64_MAX - right) return 0;
    *result = left + right;
    return 1;
}

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

/* Count only whole pages fully contained in the half-open memory region. */
static int full_page_count(uint64_t base, uint64_t end, uint64_t *pages) {
    uint64_t first;
    if (pages == NULL || end < base) return 0;
    if (!align_up_page(base, &first)) {
        *pages = 0u;
        return 1;
    }
    const uint64_t last = end & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u);
    *pages = first < last ? (last - first) / DUCKOS_FRAME_PAGE_SIZE : 0u;
    return 1;
}

static int memory_type_is_managed_ram(uint32_t type) {
    return type == (uint32_t)DUCKOS_MEMORY_USABLE ||
        type == (uint32_t)DUCKOS_MEMORY_RESERVED ||
        type == (uint32_t)DUCKOS_MEMORY_ACPI_RECLAIMABLE ||
        type == (uint32_t)DUCKOS_MEMORY_ACPI_NVS;
}

int duckos_frame_allocator_accounting_valid(
    const duckos_frame_allocator *allocator
) {
    uint64_t free_pages = 0u;

    if (allocator == NULL ||
        allocator->range_count > DUCKOS_FRAME_ALLOCATOR_MAX_RANGES ||
        allocator->active_range > allocator->range_count ||
        allocator->total_pages == 0u ||
        allocator->allocated_pages > allocator->total_pages) {
        return 0;
    }

    for (uint32_t index = 0u; index < allocator->range_count; ++index) {
        const duckos_frame_range *range = &allocator->ranges[index];
        if (range->next > range->end ||
            range->next % DUCKOS_FRAME_PAGE_SIZE != 0u ||
            range->end % DUCKOS_FRAME_PAGE_SIZE != 0u) {
            return 0;
        }
        if (index < allocator->active_range && range->next != range->end) {
            return 0;
        }
        const uint64_t remaining = (range->end - range->next) / DUCKOS_FRAME_PAGE_SIZE;
        if (!add_u64(free_pages, remaining, &free_pages)) return 0;
    }

    if (free_pages > allocator->total_pages ||
        allocator->allocated_pages != allocator->total_pages - free_pages) {
        return 0;
    }

    return duckos_kernel_memory_accounting_valid(
        allocator->managed_pages,
        free_pages,
        allocator->allocated_pages,
        allocator->reserved_pages
    );
}

duckos_frame_allocator_status duckos_frame_allocator_init(
    duckos_frame_allocator *allocator,
    const duckos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address
) {
    uint64_t previous_end = 0u;
    duckos_frame_allocator next = {0};

    if (allocator == NULL || regions == NULL || region_count == 0u ||
        region_count > DUCKOS_BOOT_MAX_MEMORY_REGIONS) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }

    for (uint32_t index = 0u; index < region_count; ++index) {
        const duckos_memory_region *region = &regions[index];
        uint64_t end;
        uint64_t whole_pages = 0u;

        if (region->type < (uint32_t)DUCKOS_MEMORY_USABLE ||
            region->type > (uint32_t)DUCKOS_MEMORY_BAD ||
            !region_end(region, &end) ||
            (index != 0u && region->base < previous_end)) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        previous_end = end;

        if (!memory_type_is_managed_ram(region->type)) continue;
        if (!full_page_count(region->base, end, &whole_pages) ||
            !add_u64(next.managed_pages, whole_pages, &next.managed_pages)) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }

        if (region->type != (uint32_t)DUCKOS_MEMORY_USABLE) {
            if (!add_u64(next.reserved_pages, whole_pages, &next.reserved_pages)) {
                return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
            }
            continue;
        }

        uint64_t begin = region->base > min_address ? region->base : min_address;
        if (!align_up_page(begin, &begin)) {
            if (!add_u64(next.reserved_pages, whole_pages, &next.reserved_pages)) {
                return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
            }
            continue;
        }

        const uint64_t aligned_end =
            end & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u);
        uint64_t allocatable_pages = 0u;
        if (begin < aligned_end) {
            allocatable_pages = (aligned_end - begin) / DUCKOS_FRAME_PAGE_SIZE;
        }
        if (allocatable_pages > whole_pages ||
            !add_u64(next.total_pages, allocatable_pages, &next.total_pages) ||
            !add_u64(
                next.reserved_pages,
                whole_pages - allocatable_pages,
                &next.reserved_pages
            )) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }

        if (begin < aligned_end) {
            if (next.range_count >= DUCKOS_FRAME_ALLOCATOR_MAX_RANGES) {
                return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
            }
            duckos_frame_range *range = &next.ranges[next.range_count++];
            range->next = begin;
            range->end = aligned_end;
        }
    }

    if (next.total_pages == 0u) {
        return DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY;
    }
    if (!duckos_frame_allocator_accounting_valid(&next)) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
    }

    *allocator = next;
    return DUCKOS_FRAME_ALLOCATOR_OK;
}

duckos_frame_allocator_status duckos_frame_allocator_allocate(
    duckos_frame_allocator *allocator,
    uint64_t *physical_address
) {
    if (allocator == NULL || physical_address == NULL) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }
    if (!duckos_frame_allocator_accounting_valid(allocator)) {
        return DUCKOS_FRAME_ALLOCATOR_CORRUPT_STATE;
    }

    duckos_frame_allocator next = *allocator;
    while (next.active_range < next.range_count) {
        duckos_frame_range *range = &next.ranges[next.active_range];
        if (range->end >= DUCKOS_FRAME_PAGE_SIZE &&
            range->next <= range->end - DUCKOS_FRAME_PAGE_SIZE) {
            const uint64_t allocated_address = range->next;
            range->next += DUCKOS_FRAME_PAGE_SIZE;
            ++next.allocated_pages;

            if (!duckos_frame_allocator_accounting_valid(&next)) {
                return DUCKOS_FRAME_ALLOCATOR_CORRUPT_STATE;
            }

            *allocator = next;
            *physical_address = allocated_address;
            return DUCKOS_FRAME_ALLOCATOR_OK;
        }
        ++next.active_range;
    }

    if (!duckos_frame_allocator_accounting_valid(&next)) {
        return DUCKOS_FRAME_ALLOCATOR_CORRUPT_STATE;
    }
    *allocator = next;
    return DUCKOS_FRAME_ALLOCATOR_EXHAUSTED;
}
