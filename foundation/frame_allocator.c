#include "frame_allocator.h"

#include <stdint.h>

static int power_of_two(uint64_t value) {
    return value != 0u && (value & (value - 1u)) == 0u;
}

static int align_up(uint64_t value, uint64_t alignment, uint64_t *out) {
    const uint64_t rem = value % alignment;
    const uint64_t add = rem == 0u ? 0u : alignment - rem;
    if (out == 0 || value > UINT64_MAX - add) return 0;
    *out = value + add;
    return 1;
}

static int range_end(uint64_t base, uint64_t pages, uint64_t *end) {
    if (end == 0 || pages == 0u ||
        (base & (DUCKOS_FRAME_PAGE_SIZE - 1u)) != 0u ||
        pages > UINT64_MAX / DUCKOS_FRAME_PAGE_SIZE) return 0;
    const uint64_t bytes = pages * DUCKOS_FRAME_PAGE_SIZE;
    if (base > UINT64_MAX - bytes) return 0;
    *end = base + bytes;
    return *end > base;
}

static void erase(duckos_frame_range *ranges, uint32_t *count, uint32_t at) {
    for (uint32_t i = at + 1u; i < *count; ++i) ranges[i - 1u] = ranges[i];
    --*count;
}

static uint32_t lower_bound(const duckos_frame_range *ranges, uint32_t count, uint64_t base) {
    uint32_t lo = 0u, hi = count;
    while (lo < hi) {
        const uint32_t mid = lo + (hi - lo) / 2u;
        if (ranges[mid].base < base) lo = mid + 1u;
        else hi = mid;
    }
    return lo;
}

/* Plans a sorted insertion and reports adjacent extents before any mutation. */
static duckos_frame_allocator_status plan_insert(
    const duckos_frame_range *ranges, uint32_t count, uint32_t capacity,
    uint64_t base, uint64_t end, int release, uint32_t *at, int *left, int *right
) {
    const uint32_t pos = lower_bound(ranges, count, base);
    const duckos_frame_range *before = pos ? &ranges[pos - 1u] : 0;
    const duckos_frame_range *after = pos < count ? &ranges[pos] : 0;
    if ((before && before->end > base) || (after && after->base < end))
        return release ? DUCKOS_FRAME_ALLOCATOR_INVALID_RELEASE : DUCKOS_FRAME_ALLOCATOR_CORRUPT_STATE;
    *left = before && before->end == base;
    *right = after && end == after->base;
    if (!*left && !*right && count >= capacity) return DUCKOS_FRAME_ALLOCATOR_METADATA_EXHAUSTED;
    *at = pos;
    return DUCKOS_FRAME_ALLOCATOR_OK;
}

static void insert_range(duckos_frame_range *ranges, uint32_t *count,
                         uint32_t at, uint64_t base, uint64_t end,
                         int merge_left, int merge_right) {
    if (merge_left && merge_right) {
        ranges[at - 1u].end = ranges[at].end;
        erase(ranges, count, at);
    } else if (merge_left) {
        ranges[at - 1u].end = end;
    } else if (merge_right) {
        ranges[at].base = base;
    } else {
        for (uint32_t i = *count; i > at; --i) ranges[i] = ranges[i - 1u];
        ranges[at].base = base;
        ranges[at].end = end;
        ++*count;
    }
}

duckos_frame_allocator_status duckos_frame_allocator_init(
    duckos_frame_allocator *allocator,
    const duckos_memory_region *regions,
    uint32_t region_count,
    uint64_t min_address
) {
    uint64_t previous_end = 0u;
    if (!allocator || !regions || region_count == 0u || region_count > DUCKOS_BOOT_MAX_MEMORY_REGIONS)
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;

    allocator->free_range_count = 0u;
    allocator->allocated_range_count = 0u;
    allocator->total_pages = 0u;
    allocator->free_pages = 0u;
    allocator->allocated_pages = 0u;

    for (uint32_t i = 0u; i < region_count; ++i) {
        const duckos_memory_region *region = &regions[i];
        if (region->length == 0u || region->base > UINT64_MAX - region->length ||
            region->type < DUCKOS_MEMORY_USABLE || region->type > DUCKOS_MEMORY_BAD ||
            (i && region->base < previous_end)) return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        const uint64_t end = region->base + region->length;
        previous_end = end;
        if (region->type != DUCKOS_MEMORY_USABLE) continue;

        uint64_t base;
        if (!align_up(region->base > min_address ? region->base : min_address,
                      DUCKOS_FRAME_PAGE_SIZE, &base)) return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        const uint64_t aligned_end = end & ~(DUCKOS_FRAME_PAGE_SIZE - 1u);
        if (base >= aligned_end) continue;
        const uint64_t pages = (aligned_end - base) / DUCKOS_FRAME_PAGE_SIZE;
        if (allocator->total_pages > UINT64_MAX - pages) return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;

        if (allocator->free_range_count) {
            duckos_frame_range *last = &allocator->free_ranges[allocator->free_range_count - 1u];
            if (last->end == base) {
                last->end = aligned_end;
                allocator->total_pages += pages;
                continue;
            }
        }
        if (allocator->free_range_count >= DUCKOS_FRAME_ALLOCATOR_MAX_RANGES)
            return DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP;
        duckos_frame_range *slot = &allocator->free_ranges[allocator->free_range_count++];
        slot->base = base;
        slot->end = aligned_end;
        allocator->total_pages += pages;
    }

    if (allocator->total_pages == 0u) return DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY;
    allocator->free_pages = allocator->total_pages;
    return DUCKOS_FRAME_ALLOCATOR_OK;
}

duckos_frame_allocator_status duckos_frame_allocator_allocate_contiguous(
    duckos_frame_allocator *allocator,
    uint64_t page_count,
    uint64_t alignment_pages,
    uint64_t *physical_address
) {
    if (!allocator || !physical_address || page_count == 0u) return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    if (!power_of_two(alignment_pages) || alignment_pages > UINT64_MAX / DUCKOS_FRAME_PAGE_SIZE)
        return DUCKOS_FRAME_ALLOCATOR_INVALID_ALIGNMENT;
    if (page_count > UINT64_MAX / DUCKOS_FRAME_PAGE_SIZE) return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    if (allocator->free_pages > allocator->total_pages ||
        allocator->allocated_pages != allocator->total_pages - allocator->free_pages ||
        allocator->free_range_count > DUCKOS_FRAME_ALLOCATOR_MAX_RANGES ||
        allocator->allocated_range_count > DUCKOS_FRAME_ALLOCATOR_MAX_ALLOCATED_RANGES)
        return DUCKOS_FRAME_ALLOCATOR_CORRUPT_STATE;
    if (page_count > allocator->free_pages) return DUCKOS_FRAME_ALLOCATOR_EXHAUSTED;

    const uint64_t bytes = page_count * DUCKOS_FRAME_PAGE_SIZE;
    const uint64_t alignment = alignment_pages * DUCKOS_FRAME_PAGE_SIZE;
    for (uint32_t i = 0u; i < allocator->free_range_count; ++i) {
        duckos_frame_range *free_range = &allocator->free_ranges[i];
        uint64_t base;
        if (!align_up(free_range->base, alignment, &base) || base > free_range->end ||
            bytes > free_range->end - base) continue;
        const uint64_t end = base + bytes;
        uint32_t alloc_at;
        int alloc_left, alloc_right;
        duckos_frame_allocator_status status = plan_insert(
            allocator->allocated_ranges, allocator->allocated_range_count,
            DUCKOS_FRAME_ALLOCATOR_MAX_ALLOCATED_RANGES, base, end, 0,
            &alloc_at, &alloc_left, &alloc_right);
        if (status != DUCKOS_FRAME_ALLOCATOR_OK) return status;

        const uint64_t old_end = free_range->end;
        const int keep_left = free_range->base < base;
        const int keep_right = end < old_end;
        if (keep_left && keep_right && allocator->free_range_count >= DUCKOS_FRAME_ALLOCATOR_MAX_RANGES)
            return DUCKOS_FRAME_ALLOCATOR_METADATA_EXHAUSTED;
        if (keep_left && keep_right) {
            for (uint32_t j = allocator->free_range_count; j > i + 1u; --j)
                allocator->free_ranges[j] = allocator->free_ranges[j - 1u];
            allocator->free_ranges[i].end = base;
            allocator->free_ranges[i + 1u].base = end;
            allocator->free_ranges[i + 1u].end = old_end;
            ++allocator->free_range_count;
        } else if (keep_left) free_range->end = base;
        else if (keep_right) free_range->base = end;
        else erase(allocator->free_ranges, &allocator->free_range_count, i);

        insert_range(allocator->allocated_ranges, &allocator->allocated_range_count,
                     alloc_at, base, end, alloc_left, alloc_right);
        allocator->free_pages -= page_count;
        allocator->allocated_pages += page_count;
        *physical_address = base;
        return DUCKOS_FRAME_ALLOCATOR_OK;
    }
    return DUCKOS_FRAME_ALLOCATOR_EXHAUSTED;
}

duckos_frame_allocator_status duckos_frame_allocator_allocate(
    duckos_frame_allocator *allocator, uint64_t *physical_address
) {
    return duckos_frame_allocator_allocate_contiguous(allocator, 1u, 1u, physical_address);
}

duckos_frame_allocator_status duckos_frame_allocator_release(
    duckos_frame_allocator *allocator, uint64_t physical_address, uint64_t page_count
) {
    uint64_t end;
    if (!allocator || page_count == 0u) return DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT;
    if (allocator->free_pages > allocator->total_pages ||
        allocator->allocated_pages != allocator->total_pages - allocator->free_pages ||
        allocator->free_range_count > DUCKOS_FRAME_ALLOCATOR_MAX_RANGES ||
        allocator->allocated_range_count > DUCKOS_FRAME_ALLOCATOR_MAX_ALLOCATED_RANGES ||
        !range_end(physical_address, page_count, &end) ||
        page_count > allocator->total_pages - allocator->free_pages)
        return DUCKOS_FRAME_ALLOCATOR_INVALID_RELEASE;

    uint32_t allocated_at = UINT32_MAX;
    for (uint32_t i = 0u; i < allocator->allocated_range_count; ++i) {
        const duckos_frame_range *r = &allocator->allocated_ranges[i];
        if (physical_address >= r->base && end <= r->end) { allocated_at = i; break; }
        if (r->base > physical_address) break;
    }
    if (allocated_at == UINT32_MAX) return DUCKOS_FRAME_ALLOCATOR_INVALID_RELEASE;

    uint32_t free_at;
    int free_left, free_right;
    duckos_frame_allocator_status status = plan_insert(
        allocator->free_ranges, allocator->free_range_count,
        DUCKOS_FRAME_ALLOCATOR_MAX_RANGES, physical_address, end, 1,
        &free_at, &free_left, &free_right);
    if (status != DUCKOS_FRAME_ALLOCATOR_OK) return status;

    const duckos_frame_range allocated = allocator->allocated_ranges[allocated_at];
    const int keep_alloc_left = allocated.base < physical_address;
    const int keep_alloc_right = end < allocated.end;
    if (keep_alloc_left && keep_alloc_right &&
        allocator->allocated_range_count >= DUCKOS_FRAME_ALLOCATOR_MAX_ALLOCATED_RANGES)
        return DUCKOS_FRAME_ALLOCATOR_METADATA_EXHAUSTED;

    insert_range(allocator->free_ranges, &allocator->free_range_count,
                 free_at, physical_address, end, free_left, free_right);
    if (keep_alloc_left && keep_alloc_right) {
        for (uint32_t i = allocator->allocated_range_count; i > allocated_at + 1u; --i)
            allocator->allocated_ranges[i] = allocator->allocated_ranges[i - 1u];
        allocator->allocated_ranges[allocated_at].end = physical_address;
        allocator->allocated_ranges[allocated_at + 1u].base = end;
        allocator->allocated_ranges[allocated_at + 1u].end = allocated.end;
        ++allocator->allocated_range_count;
    } else if (keep_alloc_left) allocator->allocated_ranges[allocated_at].end = physical_address;
    else if (keep_alloc_right) allocator->allocated_ranges[allocated_at].base = end;
    else erase(allocator->allocated_ranges, &allocator->allocated_range_count, allocated_at);

    allocator->free_pages += page_count;
    allocator->allocated_pages -= page_count;
    return DUCKOS_FRAME_ALLOCATOR_OK;
}
