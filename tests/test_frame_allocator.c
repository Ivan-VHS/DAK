#include "frame_allocator.h"

#include <stdint.h>
#include <stdio.h>

#define CHECK(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "check failed at %s:%d: %s\n", __FILE__, __LINE__, #expression); \
        return 0; \
    } \
} while (0)

static _Alignas(4096) uint8_t memory[128u * 1024u];

static int test_allocate_free_and_reuse(void) {
    const duckos_memory_region regions[] = {
        {0u, 0x1000u, DUCKOS_MEMORY_RESERVED, 0u},
        {0x1000u, 0x7000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x8000u, 0x1000u, DUCKOS_MEMORY_RESERVED, 0u},
        {0x9000u, 0x7000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    uint64_t pages[14];
    CHECK(duckos_frame_allocator_init(&allocator, regions, 4u, 0u,
        (uint64_t)(uintptr_t)memory) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(allocator.total_pages == 14u && allocator.free_pages == 14u);
    for (unsigned i = 0u; i < 14u; ++i) {
        CHECK(duckos_frame_allocator_allocate(&allocator, &pages[i]) == DUCKOS_FRAME_ALLOCATOR_OK);
        CHECK((pages[i] & 0xfffu) == 0u);
    }
    CHECK(allocator.free_pages == 0u && allocator.allocated_pages == 14u);
    uint64_t ignored = 0u;
    CHECK(duckos_frame_allocator_allocate(&allocator, &ignored) == DUCKOS_FRAME_ALLOCATOR_EXHAUSTED);
    CHECK(duckos_frame_allocator_free(&allocator, pages[4], 1u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_free(&allocator, pages[3], 1u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_free(&allocator, pages[5], 1u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(allocator.free_pages == 3u && allocator.allocated_pages == 11u);
    uint64_t run = 0u;
    CHECK(duckos_frame_allocator_allocate_pages(&allocator, 3u, 1u, &run) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(run == pages[3]);
    CHECK(allocator.free_pages == 0u && allocator.allocated_pages == 14u);
    return 1;
}

static int test_alignment_and_extent_coalescing(void) {
    const duckos_memory_region regions[] = {
        {0x1000u, 0x1f000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    uint64_t run = 0u;
    CHECK(duckos_frame_allocator_init(&allocator, regions, 1u, 0x1000u,
        (uint64_t)(uintptr_t)memory - 0x1000u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_allocate_pages(&allocator, 3u, 4u, &run) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK((run & 0x3fffu) == 0u);
    CHECK(duckos_frame_allocator_free(&allocator, run, 3u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(allocator.free_pages == allocator.total_pages);
    CHECK(allocator.allocated_pages == 0u);
    CHECK(duckos_frame_allocator_allocate_pages(&allocator, 31u, 1u, &run) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_free(&allocator, run, 31u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(allocator.free_pages == allocator.total_pages);
    return 1;
}

static int test_rejects_double_free_and_invalid_ranges(void) {
    const duckos_memory_region regions[] = {
        {0x1000u, 0x7000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x8000u, 0x1000u, DUCKOS_MEMORY_RESERVED, 0u}
    };
    duckos_frame_allocator allocator;
    uint64_t page = 0u;
    CHECK(duckos_frame_allocator_init(&allocator, regions, 2u, 0x1000u,
        (uint64_t)(uintptr_t)memory - 0x1000u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_allocate(&allocator, &page) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_free(&allocator, page, 1u) == DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_frame_allocator_free(&allocator, page, 1u) == DUCKOS_FRAME_ALLOCATOR_ALREADY_FREE);
    CHECK(duckos_frame_allocator_free(&allocator, 0x8000u, 1u) == DUCKOS_FRAME_ALLOCATOR_OUT_OF_RANGE);
    CHECK(duckos_frame_allocator_free(&allocator, 0x1001u, 1u) == DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT);
    CHECK(duckos_frame_allocator_allocate_pages(&allocator, 1u, 3u, &page) == DUCKOS_FRAME_ALLOCATOR_INVALID_ALIGNMENT);
    return 1;
}

static int test_rejects_bad_maps(void) {
    duckos_frame_allocator allocator;
    const duckos_memory_region overflow[] = {
        {UINT64_MAX - 0xfffu, 0x2000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    const duckos_memory_region overlap[] = {
        {0x1000u, 0x3000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x2000u, 0x1000u, DUCKOS_MEMORY_USABLE, 0u}
    };
    const duckos_memory_region reserved[] = {
        {0x1000u, 0x4000u, DUCKOS_MEMORY_RESERVED, 0u}
    };
    CHECK(duckos_frame_allocator_init(&allocator, overflow, 1u, 0u,
        (uint64_t)(uintptr_t)memory) == DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP);
    CHECK(duckos_frame_allocator_init(&allocator, overlap, 2u, 0u,
        (uint64_t)(uintptr_t)memory - 0x1000u) == DUCKOS_FRAME_ALLOCATOR_INVALID_MEMORY_MAP);
    CHECK(duckos_frame_allocator_init(&allocator, reserved, 1u, 0u,
        (uint64_t)(uintptr_t)memory - 0x1000u) == DUCKOS_FRAME_ALLOCATOR_NO_USABLE_MEMORY);
    CHECK(duckos_frame_allocator_init(NULL, reserved, 1u, 0u, 0u) ==
        DUCKOS_FRAME_ALLOCATOR_INVALID_ARGUMENT);
    return 1;
}

int main(void) {
    if (!test_allocate_free_and_reuse() ||
        !test_alignment_and_extent_coalescing() ||
        !test_rejects_double_free_and_invalid_ranges() ||
        !test_rejects_bad_maps()) return 1;
    puts("DuckOS frame allocator tests passed");
    return 0;
}
