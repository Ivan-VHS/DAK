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


static int same_allocator(
    const duckos_frame_allocator *left,
    const duckos_frame_allocator *right
) {
    if (left->range_count != right->range_count ||
        left->active_range != right->active_range ||
        left->total_pages != right->total_pages ||
        left->allocated_pages != right->allocated_pages) {
        return 0;
    }
    for (uint32_t index = 0u; index < DUCKOS_FRAME_ALLOCATOR_MAX_RANGES; ++index) {
        if (left->ranges[index].next != right->ranges[index].next ||
            left->ranges[index].end != right->ranges[index].end) {
            return 0;
        }
    }
    return 1;
}

static int test_failed_reinitialization_preserves_existing_allocator(void) {
    const duckos_memory_region valid[] = {
        {0x00100000u, 0x00003000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    const duckos_memory_region invalid_after_usable[] = {
        {0x00200000u, 0x00004000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x00202000u, 0x00001000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    const duckos_memory_region no_usable[] = {
        {0x00100000u, 0x00004000u, DUCKOS_MEMORY_RESERVED, 0u}
    };
    duckos_frame_allocator allocator;
    duckos_frame_allocator before;
    uint64_t page = 0u;

    CHECK(duckos_frame_allocator_init(&allocator, valid, 1u, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_allocate(&allocator, &page) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(page == 0x00100000u);

    before = allocator;
    CHECK(duckos_frame_allocator_init(&allocator, invalid_after_usable, 2u, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP);
    CHECK(same_allocator(&allocator, &before));

    CHECK(duckos_frame_allocator_allocate(&allocator, &page) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(page == 0x00101000u);

    before = allocator;
    CHECK(duckos_frame_allocator_init(&allocator, no_usable, 1u, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY);
    CHECK(memcmp(&allocator, &before, sizeof(allocator)) == 0);
    return 1;
}

int main(void) {
    if (!test_failed_reinitialization_preserves_existing_allocator() ||
        !test_allocates_only_usable_aligned_pages() ||
        !test_minimum_address_and_partial_pages() ||
        !test_rejects_bad_maps() ||
        !test_rejects_invalid_allocate_arguments()) {
        return 1;
    }
    puts("DuckOS frame allocator tests passed");
    return 0;
}
