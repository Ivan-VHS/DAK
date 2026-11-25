#include "frame_allocator.h"

#include <stddef.h>
#include <stdint.h>

typedef struct duckos_frame_extent {
    uint64_t page_count;
    uint64_t next_phys;
} duckos_frame_extent;

_Static_assert(sizeof(duckos_frame_extent) <= DUCKOS_FRAME_PAGE_SIZE,
    "free-extent metadata must fit inside one physical page");

static int add_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (result == NULL || left > UINT64_MAX - right) return 0;
    *result = left + right;
    return 1;
}

static int align_up(uint64_t value, uint64_t alignment, uint64_t *result) {
    uint64_t remainder;
    if (alignment == 0u || result == NULL) return 0;
    remainder = value % alignment;
    if (remainder == 0u) {
        *result = value;
        return 1;
    }
    return add_u64(value, alignment - remainder, result);
}

static duckos_frame_extent *extent_at(
    const duckos_frame_allocator *allocator,
    uint64_t physical_address
) {
    uint64_t virtual_address;
    if (allocator == NULL ||
        (physical_address & (DUCKOS_FRAME_PAGE_SIZE - 1u)) != 0u ||
        !add_u64(allocator->hhdm_offset, physical_address, &virtual_address) ||
        virtual_address > (uint64_t)UINTPTR_MAX) {
        return NULL;
    }
    return (duckos_frame_extent *)(uintptr_t)virtual_address;
}

static int extent_size_bytes(const duckos_frame_extent *extent, uint64_t *bytes) {
    if (extent == NULL || bytes == NULL || extent->page_count == 0u ||
        extent->page_count > UINT64_MAX / DUCKOS_FRAME_PAGE_SIZE) {
        return 0;
    }
    *bytes = extent->page_count * DUCKOS_FRAME_PAGE_SIZE;
    return 1;
}

static int managed_range_contains(
    const duckos_frame_allocator *allocator,
    uint64_t base,
    uint64_t end
) {
    if (allocator == NULL || base >= end) return 0;
    for (uint32_t index = 0u; index < allocator->range_count; ++index) {
        const duckos_frame_managed_range *range = &allocator->ranges[index];
        if (base >= range->base && end <= range->end) return 1;
    }
    return 0;
}

static void write_extent(
    const duckos_frame_allocator *allocator,
    uint64_t physical_address,
    uint64_t page_count,
    uint64_t next_phys
) {
    duckos_frame_extent *extent = extent_at(allocator, physical_address);
    extent->page_count = page_count;
    extent->next_phys = next_phys;
}

duckos_frame_allocator_status duckos_frame_allocator_init(
    duckos_frame_allocator *allocator,
    const duckos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address,
    uint64_t hhdm_offset
) {
    uint64_t previous_end = 0u;
    uint64_t tail_phys = 0u;

    if (allocator == NULL || regions == NULL || region_count == 0u ||
        region_count > DUCKOS_BOOT_MAX_MEMORY_REGIONS) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }

    allocator->hhdm_offset = hhdm_offset;
    allocator->free_head_phys = 0u;
    allocator->total_pages = 0u;
    allocator->free_pages = 0u;
    allocator->allocated_pages = 0u;
    allocator->range_count = 0u;

    for (uint32_t index = 0u; index < region_count; ++index) {
        const duckos_memory_region *region = &regions[index];
        uint64_t region_end;

        if (region->type < (uint32_t)DUCKOS_MEMORY_USABLE ||
            region->type > (uint32_t)DUCKOS_MEMORY_BAD ||
            region->length == 0u ||
            !add_u64(region->base, region->length, &region_end) ||
            (index != 0u && region->base < previous_end)) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        previous_end = region_end;

        if (region->type != (uint32_t)DUCKOS_MEMORY_USABLE) continue;

        uint64_t begin = region->base > min_address ? region->base : min_address;
        uint64_t end = region_end & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u);
        if (!align_up(begin, DUCKOS_FRAME_PAGE_SIZE, &begin)) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        if (begin >= end) continue;

        uint64_t mapped_end;
        if (!add_u64(hhdm_offset, end - 1u, &mapped_end) ||
            mapped_end > (uint64_t)UINTPTR_MAX) {
            return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
        }

        if (allocator->range_count != 0u) {
            duckos_frame_managed_range *previous =
                &allocator->ranges[allocator->range_count - 1u];
            if (previous->end == begin) {
                previous->end = end;
                const uint64_t extra_pages = (end - begin) / DUCKOS_FRAME_PAGE_SIZE;
                if (allocator->total_pages > UINT64_MAX - extra_pages) {
                    return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
                }
                allocator->total_pages += extra_pages;
                allocator->free_pages += extra_pages;
                duckos_frame_extent *tail = extent_at(allocator, tail_phys);
                if (tail == NULL || tail->page_count > UINT64_MAX - extra_pages) {
                    return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
                }
                tail->page_count += extra_pages;
                continue;
            }
        }

        if (allocator->range_count >= DUCKOS_FRAME_ALLOCATOR_MAX_RANGES) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }

        const uint64_t pages = (end - begin) / DUCKOS_FRAME_PAGE_SIZE;
        if (allocator->total_pages > UINT64_MAX - pages) {
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        }
        allocator->ranges[allocator->range_count].base = begin;
        allocator->ranges[allocator->range_count].end = end;
        ++allocator->range_count;
        allocator->total_pages += pages;
        allocator->free_pages += pages;

        write_extent(allocator, begin, pages, 0u);
        if (allocator->free_head_phys == 0u) {
            allocator->free_head_phys = begin;
        } else {
            duckos_frame_extent *tail = extent_at(allocator, tail_phys);
            if (tail == NULL) return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
            tail->next_phys = begin;
        }
        tail_phys = begin;
    }

    return allocator->total_pages != 0u ?
        DUCKOS_FRAME_ALLOCATOR_OK : DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY;
}

duckos_frame_allocator_status duckos_frame_allocator_allocate_pages(
    duckos_frame_allocator *allocator,
    uint64_t page_count,
    uint64_t alignment_pages,
    uint64_t *physical_address
) {
    uint64_t allocation_bytes;
    uint64_t alignment_bytes;
    uint64_t previous_phys = 0u;
    uint64_t current_phys;

    if (allocator == NULL || physical_address == NULL || page_count == 0u ||
        alignment_pages == 0u) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }
    if ((alignment_pages & (alignment_pages - 1u)) != 0u ||
        page_count > UINT64_MAX / DUCKOS_FRAME_PAGE_SIZE ||
        alignment_pages > UINT64_MAX / DUCKOS_FRAME_PAGE_SIZE) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ALIGNMENT;
    }
    allocation_bytes = page_count * DUCKOS_FRAME_PAGE_SIZE;
    alignment_bytes = alignment_pages * DUCKOS_FRAME_PAGE_SIZE;
    if (page_count > allocator->free_pages) return DUCKOS_FRAME_ALLOCATOR_EXHAUSTED;

    current_phys = allocator->free_head_phys;
    while (current_phys != 0u) {
        duckos_frame_extent *extent = extent_at(allocator, current_phys);
        uint64_t extent_bytes;
        uint64_t extent_end;
        uint64_t allocation_begin;
        uint64_t allocation_end;
        uint64_t next_phys;
        uint64_t prefix_pages;
        uint64_t suffix_pages;

        if (extent == NULL || !extent_size_bytes(extent, &extent_bytes) ||
            !add_u64(current_phys, extent_bytes, &extent_end)) {
            return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
        }
        next_phys = extent->next_phys;
        if (!align_up(current_phys, alignment_bytes, &allocation_begin) ||
            !add_u64(allocation_begin, allocation_bytes, &allocation_end)) {
            return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
        }

        if (allocation_begin >= current_phys && allocation_end <= extent_end) {
            prefix_pages = (allocation_begin - current_phys) / DUCKOS_FRAME_PAGE_SIZE;
            suffix_pages = (extent_end - allocation_end) / DUCKOS_FRAME_PAGE_SIZE;

            if (prefix_pages != 0u && suffix_pages != 0u) {
                write_extent(allocator, allocation_end, suffix_pages, next_phys);
                extent->page_count = prefix_pages;
                extent->next_phys = allocation_end;
            } else if (prefix_pages != 0u) {
                extent->page_count = prefix_pages;
            } else if (suffix_pages != 0u) {
                write_extent(allocator, allocation_end, suffix_pages, next_phys);
                if (previous_phys == 0u) allocator->free_head_phys = allocation_end;
                else {
                    duckos_frame_extent *previous = extent_at(allocator, previous_phys);
                    if (previous == NULL) return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
                    previous->next_phys = allocation_end;
                }
            } else {
                if (previous_phys == 0u) allocator->free_head_phys = next_phys;
                else {
                    duckos_frame_extent *previous = extent_at(allocator, previous_phys);
                    if (previous == NULL) return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
                    previous->next_phys = next_phys;
                }
            }

            allocator->free_pages -= page_count;
            allocator->allocated_pages += page_count;
            *physical_address = allocation_begin;
            return DUCKOS_FRAME_ALLOCATOR_OK;
        }

        previous_phys = current_phys;
        current_phys = next_phys;
    }

    return DUCKOS_FRAME_ALLOCATOR_EXHAUSTED;
}

duckos_frame_allocator_status duckos_frame_allocator_free(
    duckos_frame_allocator *allocator,
    uint64_t physical_address,
    uint64_t page_count
) {
    uint64_t bytes;
    uint64_t end;
    uint64_t previous_phys = 0u;
    uint64_t next_phys;
    uint64_t merged_base;
    duckos_frame_extent *previous = NULL;
    duckos_frame_extent *next = NULL;

    if (allocator == NULL || page_count == 0u) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }
    if ((physical_address & (DUCKOS_FRAME_PAGE_SIZE - 1u)) != 0u ||
        page_count > UINT64_MAX / DUCKOS_FRAME_PAGE_SIZE) {
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    }
    bytes = page_count * DUCKOS_FRAME_PAGE_SIZE;
    if (!add_u64(physical_address, bytes, &end)) {
        return DUCKOS_FRAME_ALLOCATOR_OUT_OF_RANGE;
    }
    if (!managed_range_contains(allocator, physical_address, end)) {
        return DUCKOS_FRAME_ALLOCATOR_OUT_OF_RANGE;
    }

    next_phys = allocator->free_head_phys;
    while (next_phys != 0u && next_phys < physical_address) {
        duckos_frame_extent *candidate = extent_at(allocator, next_phys);
        uint64_t candidate_bytes;
        uint64_t candidate_end;
        if (candidate == NULL || !extent_size_bytes(candidate, &candidate_bytes) ||
            !add_u64(next_phys, candidate_bytes, &candidate_end)) {
            return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
        }
        previous_phys = next_phys;
        previous = candidate;
        next_phys = candidate->next_phys;
    }

    if (previous != NULL) {
        uint64_t previous_bytes;
        uint64_t previous_end;
        if (!extent_size_bytes(previous, &previous_bytes) ||
            !add_u64(previous_phys, previous_bytes, &previous_end)) {
            return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
        }
        if (previous_end > physical_address) return DUCKOS_FRAME_ALLOCATOR_ALREADY_FREE;
    }
    if (next_phys != 0u) {
        next = extent_at(allocator, next_phys);
        if (next == NULL) return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
        if (end > next_phys) return DUCKOS_FRAME_ALLOCATOR_ALREADY_FREE;
    }

    if (page_count > allocator->allocated_pages ||
        page_count > allocator->total_pages - allocator->free_pages) {
        return DUCKOS_FRAME_ALLOCATOR_COUNTER_ERROR;
    }

    merged_base = physical_address;
    if (previous != NULL) {
        uint64_t previous_bytes;
        uint64_t previous_end;
        if (!extent_size_bytes(previous, &previous_bytes) ||
            !add_u64(previous_phys, previous_bytes, &previous_end)) {
            return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
        }
        if (previous_end == physical_address) {
            if (previous->page_count > UINT64_MAX - page_count) {
                return DUCKOS_FRAME_ALLOCATOR_COUNTER_ERROR;
            }
            previous->page_count += page_count;
            merged_base = previous_phys;
        } else {
            write_extent(allocator, physical_address, page_count, next_phys);
            previous->next_phys = physical_address;
        }
    } else {
        write_extent(allocator, physical_address, page_count, next_phys);
        allocator->free_head_phys = physical_address;
    }

    duckos_frame_extent *merged = extent_at(allocator, merged_base);
    if (merged == NULL) return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
    if (next != NULL) {
        uint64_t merged_bytes;
        uint64_t merged_end;
        if (!extent_size_bytes(merged, &merged_bytes) ||
            !add_u64(merged_base, merged_bytes, &merged_end)) {
            return DUCKOS_FRAME_ALLOCATOR_ADDRESS_ERROR;
        }
        if (merged_end == next_phys) {
            if (merged->page_count > UINT64_MAX - next->page_count) {
                return DUCKOS_FRAME_ALLOCATOR_COUNTER_ERROR;
            }
            merged->page_count += next->page_count;
            merged->next_phys = next->next_phys;
        }
    }

    allocator->free_pages += page_count;
    allocator->allocated_pages -= page_count;
    return DUCKOS_FRAME_ALLOCATOR_OK;
}
