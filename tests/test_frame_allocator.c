#include "frame_allocator.h"

#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#define CHECK(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "check failed at %s:%d: %s\n", __FILE__, __LINE__, #expression); \
        return 0; \
    } \
} while (0)

static int test_allocates_only_usable_aligned_pages(void) {
    const duckos_memory_region regions[] = {
        {0x00000000u, 0x00100000u, DUCKOS_MEMORY_RESERVED, 0u},
        {0x00100000u, 0x00003000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x00103000u, 0x00001000u, DUCKOS_MEMORY_RESERVED, 0u},
        {0x00104000u, 0x00002000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    uint64_t page = 0u;

    CHECK(duckos_frame_allocator_init(&allocator, regions, 4u, 0x00100000u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(allocator.total_pages == 5u);

    const uint64_t expected[] = {
        0x00100000u, 0x00101000u, 0x00102000u, 0x00104000u, 0x00105000u
    };
    for (size_t index = 0u; index < sizeof(expected) / sizeof(expected[0]); ++index) {
        CHECK(duckos_frame_allocator_allocate(&allocator, &page) == DUCKOS_FRAME_ALLOCATOR_OK);
        CHECK(page == expected[index]);
        CHECK((page % DUCKOS_FRAME_PAGE_SIZE) == 0u);
    }
    CHECK(allocator.allocated_pages == 5u);
    CHECK(duckos_frame_allocator_allocate(&allocator, &page) == DUCKOS_FRAME_ALLOCATOR_EXHAUSTED);
    return 1;
}

static int test_minimum_address_and_partial_pages(void) {
    const duckos_memory_region regions[] = {
        {0x00000000u, 0x00003001u, DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    uint64_t page = 0u;

    CHECK(duckos_frame_allocator_init(&allocator, regions, 1u, 0x00001001u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(allocator.total_pages == 1u);
    CHECK(duckos_frame_allocator_allocate(&allocator, &page) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(page == 0x00002000u);
    return 1;
}

static int test_rejects_bad_maps(void) {
    duckos_frame_allocator allocator;
    const duckos_memory_region overflow[] = {
        {UINT64_MAX - 0x0fffu, 0x2000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    const duckos_memory_region overlap[] = {
        {0x1000u, 0x3000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x2000u, 0x1000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    const duckos_memory_region reserved[] = {
        {0x100000u, 0x4000u, DUCKOS_MEMORY_RESERVED, 0u}
    };

    CHECK(duckos_frame_allocator_init(&allocator, overflow, 1u, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP);
    CHECK(duckos_frame_allocator_init(&allocator, overlap, 2u, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP);
    CHECK(duckos_frame_allocator_init(&allocator, reserved, 1u, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY);
    CHECK(duckos_frame_allocator_init(NULL, reserved, 1u, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT);
    CHECK(duckos_frame_allocator_init(&allocator, reserved, 0u, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT);
    return 1;
}

static int test_rejects_invalid_allocate_arguments(void) {
    uint64_t page = 0u;
    CHECK(duckos_frame_allocator_allocate(NULL, &page) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT);
    return 1;
}


static int test_contiguous_allocation_and_alignment(void) {
    const duckos_memory_region regions[] = {
        {0x00100000u, 0x00010000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    uint64_t base = 0u;

    CHECK(duckos_frame_allocator_init(&allocator, regions, 1u, 0x00100000u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_allocate_contiguous(&allocator, 3u, 4u, &base) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(base == 0x00100000u);
    CHECK((base % (4u * DUCKOS_FRAME_PAGE_SIZE)) == 0u);
    CHECK(allocator.allocated_pages == 3u);
    CHECK(allocator.free_pages == 13u);
    CHECK(duckos_frame_allocator_allocate_contiguous(&allocator, 2u, 8u, &base) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(base == 0x00108000u);
    CHECK(allocator.allocated_pages == 5u);
    return 1;
}

static int test_release_reuse_and_double_free(void) {
    const duckos_memory_region regions[] = {
        {0x00100000u, 0x00008000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    uint64_t first = 0u, second = 0u, third = 0u, reused = 0u;

    CHECK(duckos_frame_allocator_init(&allocator, regions, 1u, 0x00100000u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_allocate(&allocator, &first) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_allocate(&allocator, &second) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_allocate(&allocator, &third) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(second == first + DUCKOS_FRAME_PAGE_SIZE);
    CHECK(third == second + DUCKOS_FRAME_PAGE_SIZE);
    CHECK(duckos_frame_allocator_release(&allocator, second, 1u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(allocator.allocated_pages == 2u);
    CHECK(allocator.free_pages == 6u);
    CHECK(duckos_frame_allocator_release(&allocator, second, 1u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_RELEASE);
    CHECK(duckos_frame_allocator_allocate(&allocator, &reused) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(reused == second);
    CHECK(allocator.allocated_pages == 3u);
    CHECK(allocator.free_pages == 5u);
    return 1;
}

static int test_release_coalesces_ranges_and_splits_allocations(void) {
    const duckos_memory_region regions[] = {
        {0x00200000u, 0x00010000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    uint64_t base = 0u, reused = 0u;

    CHECK(duckos_frame_allocator_init(&allocator, regions, 1u, 0x00200000u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_allocate_contiguous(&allocator, 8u, 1u, &base) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_release(&allocator, base + 3u * DUCKOS_FRAME_PAGE_SIZE, 2u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(allocator.allocated_range_count == 2u);
    CHECK(allocator.allocated_pages == 6u);
    CHECK(allocator.free_pages == 10u);
    CHECK(duckos_frame_allocator_allocate_contiguous(&allocator, 2u, 1u, &reused) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(reused == base + 3u * DUCKOS_FRAME_PAGE_SIZE);

    CHECK(duckos_frame_allocator_release(&allocator, base, 3u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_release(&allocator, base + 5u * DUCKOS_FRAME_PAGE_SIZE, 3u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_release(&allocator, base + 3u * DUCKOS_FRAME_PAGE_SIZE, 2u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(allocator.allocated_range_count == 0u);
    CHECK(allocator.free_range_count == 1u);
    CHECK(allocator.free_ranges[0].base == 0x00200000u);
    CHECK(allocator.free_ranges[0].end == 0x00210000u);
    CHECK(allocator.free_pages == allocator.total_pages);
    return 1;
}

static int test_rejects_foreign_and_unaligned_releases(void) {
    const duckos_memory_region regions[] = {
        {0x00300000u, 0x00004000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x00304000u, 0x00001000u, DUCKOS_MEMORY_RESERVED, 0u}
    };
    duckos_frame_allocator allocator;
    uint64_t page = 0u;

    CHECK(duckos_frame_allocator_init(&allocator, regions, 2u, 0x00300000u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_release(&allocator, 0x00300000u, 1u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_RELEASE);
    CHECK(duckos_frame_allocator_allocate(&allocator, &page) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_release(&allocator, 0x00304000u, 1u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_RELEASE);
    CHECK(duckos_frame_allocator_release(&allocator, page + 1u, 1u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_RELEASE);
    CHECK(duckos_frame_allocator_release(&allocator, page, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT);
    return 1;
}

int main(void) {
    if (!test_allocates_only_usable_aligned_pages() ||
        !test_minimum_address_and_partial_pages() ||
        !test_rejects_bad_maps() ||
        !test_rejects_invalid_allocate_arguments() ||
        !test_contiguous_allocation_and_alignment() ||
        !test_release_reuse_and_double_free() ||
        !test_release_coalesces_ranges_and_splits_allocations() ||
        !test_rejects_foreign_and_unaligned_releases()) {
        return 1;
    }
    puts("DuckOS frame allocator tests passed");
    return 0;
}
