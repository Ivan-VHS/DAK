#include "page_table.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

#define TEST_PAGE_COUNT 256u
#define TEST_PAGE_BASE 0x1000u

typedef struct test_page_pool {
    uint64_t pages[TEST_PAGE_COUNT][DUCKOS_PAGE_TABLE_ENTRIES];
    uint8_t used[TEST_PAGE_COUNT];
    uint32_t next_page;
    uint32_t invalidations;
} test_page_pool;

static test_page_pool pool;

static void reset_pool(void) {
    for (uint32_t index = 0u; index < TEST_PAGE_COUNT; ++index) {
        pool.used[index] = 0u;
    }
    pool.next_page = 0u;
    pool.invalidations = 0u;
}

static uint64_t test_allocate(void *context) {
    test_page_pool *pool = (test_page_pool *)context;
    for (uint32_t index = pool->next_page; index < TEST_PAGE_COUNT; ++index) {
        if (pool->used[index] == 0u) {
            pool->used[index] = 1u;
            pool->next_page = index + 1u;
            for (uint32_t word = 0u; word < DUCKOS_PAGE_TABLE_ENTRIES; ++word) {
                pool->pages[index][word] = 0u;
            }
            return TEST_PAGE_BASE + (uint64_t)index * DUCKOS_PAGE_TABLE_PAGE_SIZE;
        }
    }
    return 0u;
}

static void test_release(void *context, uint64_t physical_address) {
    test_page_pool *pool = (test_page_pool *)context;
    if (physical_address < TEST_PAGE_BASE ||
        ((physical_address - TEST_PAGE_BASE) % DUCKOS_PAGE_TABLE_PAGE_SIZE) != 0u) {
        return;
    }
    const uint64_t index =
        (physical_address - TEST_PAGE_BASE) / DUCKOS_PAGE_TABLE_PAGE_SIZE;
    if (index < TEST_PAGE_COUNT) pool->used[index] = 0u;
}

static uint64_t *test_map_page(void *context, uint64_t physical_address) {
    test_page_pool *pool = (test_page_pool *)context;
    if (physical_address < TEST_PAGE_BASE ||
        ((physical_address - TEST_PAGE_BASE) % DUCKOS_PAGE_TABLE_PAGE_SIZE) != 0u) {
        return NULL;
    }
    const uint64_t index =
        (physical_address - TEST_PAGE_BASE) / DUCKOS_PAGE_TABLE_PAGE_SIZE;
    if (index >= TEST_PAGE_COUNT || pool->used[index] == 0u) return NULL;
    return pool->pages[index];
}

static void test_invalidate(void *context, uint64_t virtual_address) {
    test_page_pool *pool = (test_page_pool *)context;
    (void)virtual_address;
    ++pool->invalidations;
}

static duckos_page_table_ops test_ops(test_page_pool *pool) {
    duckos_page_table_ops ops = {
        .context = pool,
        .allocate_page = test_allocate,
        .release_page = test_release,
        .map_page = test_map_page,
        .invalidate_page = test_invalidate
    };
    return ops;
}

static uint32_t count_used(const test_page_pool *pool) {
    uint32_t count = 0u;
    for (uint32_t index = 0u; index < TEST_PAGE_COUNT; ++index) {
        if (pool->used[index] != 0u) ++count;
    }
    return count;
}

static void test_canonical_addresses(void) {
    assert(duckos_page_table_is_canonical(0x00007fffffffffffULL));
    assert(duckos_page_table_is_canonical(0xffff800000000000ULL));
    assert(!duckos_page_table_is_canonical(0x0000800000000000ULL));
    assert(!duckos_page_table_is_canonical(0xffff7fffffffffffULL));
}

static void test_map_translate_protect_and_unmap(void) {
    reset_pool();
    const duckos_page_table_ops ops = test_ops(&pool);
    duckos_page_table_space space = {0};
    uint64_t physical = 0u;
    uint64_t flags = 0u;

    assert(duckos_page_table_create(&space, 48u, 1, &ops) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_map(
        &space, 0x4000u, 0x9000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_translate(
        &space, 0x4abcu, &physical, &flags
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(physical == 0x9abcu);
    assert((flags & (DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_NX)) ==
        (DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_NX));

    assert(duckos_page_table_map(
        &space, 0x4000u, 0xa000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_ALREADY_MAPPED);
    assert(duckos_page_table_map(
        &space, 0x8000u, 0xb000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE
    ) == DUCKOS_PAGE_TABLE_INVALID_FLAGS);
    assert(duckos_page_table_map(
        &space, 0x0000800000000000ULL, 0xb000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_INVALID_ADDRESS);

    assert(duckos_page_table_protect(
        &space, 0x4000u, DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_translate(
        &space, 0x4000u, &physical, &flags
    ) == DUCKOS_PAGE_TABLE_OK);
    assert((flags & DUCKOS_PAGE_WRITABLE) == 0u);
    assert((flags & DUCKOS_PAGE_NX) != 0u);

    space.active = 1u;
    assert(duckos_page_table_unmap(&space, 0x4000u) == DUCKOS_PAGE_TABLE_OK);
    assert(pool.invalidations == 1u);
    assert(duckos_page_table_translate(
        &space, 0x4000u, &physical, &flags
    ) == DUCKOS_PAGE_TABLE_NOT_MAPPED);
    assert(count_used(&pool) == 1u);
    duckos_page_table_destroy(&space);
    assert(count_used(&pool) == 0u);
}

static void test_splits_two_megabyte_mapping_before_modifying_one_page(void) {
    reset_pool();
    const duckos_page_table_ops ops = test_ops(&pool);
    duckos_page_table_space space = {0};
    uint64_t *root;
    uint64_t *pdpt;
    uint64_t *pd;
    uint64_t pdpt_physical = 0u;
    uint64_t pd_physical = 0u;
    uint64_t physical = 0u;

    assert(duckos_page_table_create(&space, 48u, 1, &ops) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_translate(&space, 0x401234u, &physical, NULL) ==
        DUCKOS_PAGE_TABLE_NOT_MAPPED);

    root = test_map_page(&pool, space.root_physical);
    pdpt_physical = test_allocate(&pool);
    pd_physical = test_allocate(&pool);
    assert(pdpt_physical != 0u && pd_physical != 0u);
    pdpt = test_map_page(&pool, pdpt_physical);
    pd = test_map_page(&pool, pd_physical);
    assert(pdpt != NULL && pd != NULL);

    root[0] = pdpt_physical | DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE;
    pdpt[0] = pd_physical | DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE;
    pd[2] = 0x800000u | DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE |
        DUCKOS_PAGE_LARGE | DUCKOS_PAGE_NX;

    assert(duckos_page_table_translate(
        &space, 0x401234u, &physical, NULL
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(physical == 0x801234u);

    assert(duckos_page_table_map(
        &space, 0x401000u, 0x900000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_ALREADY_MAPPED);
    assert(duckos_page_table_unmap(&space, 0x401000u) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_map(
        &space, 0x401000u, 0x900000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_translate(
        &space, 0x401000u, &physical, NULL
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(physical == 0x900000u);
    assert(duckos_page_table_translate(
        &space, 0x402000u, &physical, NULL
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(physical == 0x802000u);

    assert(duckos_page_table_unmap(&space, 0x401000u) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_translate(
        &space, 0x402000u, &physical, NULL
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(physical == 0x802000u);
    duckos_page_table_destroy(&space);
    assert(count_used(&pool) == 0u);
}


static void test_splits_one_gigabyte_mapping_before_modifying_one_page(void) {
    reset_pool();
    const duckos_page_table_ops ops = test_ops(&pool);
    duckos_page_table_space space = {0};
    uint64_t *root;
    uint64_t *pdpt;
    uint64_t pdpt_physical = 0u;
    uint64_t physical = 0u;

    assert(duckos_page_table_create(&space, 48u, 1, &ops) == DUCKOS_PAGE_TABLE_OK);
    root = test_map_page(&pool, space.root_physical);
    pdpt_physical = test_allocate(&pool);
    assert(pdpt_physical != 0u);
    pdpt = test_map_page(&pool, pdpt_physical);
    assert(pdpt != NULL);

    root[0] = pdpt_physical | DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE;
    pdpt[1] = 0x40000000u | DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE |
        DUCKOS_PAGE_LARGE | DUCKOS_PAGE_NX;

    assert(duckos_page_table_translate(
        &space, 0x40001234u, &physical, NULL
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(physical == 0x40001234u);

    assert(duckos_page_table_map(
        &space, 0x40001000u, 0x900000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_ALREADY_MAPPED);
    assert(duckos_page_table_unmap(&space, 0x40001000u) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_map(
        &space, 0x40001000u, 0x900000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_translate(
        &space, 0x40001000u, &physical, NULL
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(physical == 0x900000u);
    assert(duckos_page_table_translate(
        &space, 0x40002000u, &physical, NULL
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(physical == 0x40002000u);

    duckos_page_table_destroy(&space);
    assert(count_used(&pool) == 0u);
}

static void test_clones_existing_hierarchy_into_owned_pages(void) {
    reset_pool();
    const duckos_page_table_ops ops = test_ops(&pool);
    duckos_page_table_space source = {0};
    duckos_page_table_space clone = {0};
    uint64_t physical = 0u;

    assert(duckos_page_table_create(&source, 48u, 1, &ops) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_map(
        &source, 0xffff800000001000ULL, 0x300000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_clone(
        &clone, source.root_physical, 48u, 1, &ops
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(clone.root_physical != source.root_physical);
    assert(duckos_page_table_translate(
        &clone, 0xffff800000001234ULL, &physical, NULL
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(physical == 0x300234u);

    duckos_page_table_destroy(&clone);
    duckos_page_table_destroy(&source);
    assert(count_used(&pool) == 0u);
}

static void test_rejects_writable_executable_and_unsupported_nx(void) {
    reset_pool();
    const duckos_page_table_ops ops = test_ops(&pool);
    duckos_page_table_space no_nx = {0};

    assert(duckos_page_table_create(&no_nx, 48u, 0, &ops) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_map(
        &no_nx, 0x1000u, 0x5000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_INVALID_FLAGS);
    assert(duckos_page_table_map(
        &no_nx, 0x1000u, 0x5000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE
    ) == DUCKOS_PAGE_TABLE_OK);
    assert(duckos_page_table_map(
        &no_nx, 0x2000u, 0x6000u,
        DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_NX
    ) == DUCKOS_PAGE_TABLE_INVALID_FLAGS);
    duckos_page_table_destroy(&no_nx);
    assert(count_used(&pool) == 0u);
}

int main(void) {
    test_canonical_addresses();
    test_map_translate_protect_and_unmap();
    test_splits_two_megabyte_mapping_before_modifying_one_page();
    test_splits_one_gigabyte_mapping_before_modifying_one_page();
    test_clones_existing_hierarchy_into_owned_pages();
    test_rejects_writable_executable_and_unsupported_nx();
    puts("DuckOS x86_64 page-table tests passed");
    return 0;
}
