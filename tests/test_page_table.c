#include "page_table.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define MOCK_BASE UINT64_C(0x01000000)
#define MOCK_PAGE_COUNT 64u

typedef struct mock_memory {
    uint64_t pages[MOCK_PAGE_COUNT][DUCKOS_X86_64_PAGE_ENTRIES] __attribute__((aligned(4096)));
    uint32_t next_page;
    uint32_t allocations;
    uint32_t invalidations;
    uint64_t last_invalidated;
    uint32_t fail_allocation_after;
} mock_memory;

static uint64_t mock_allocate(void *context) {
    mock_memory *memory = (mock_memory *)context;
    if (memory->fail_allocation_after != 0u &&
        memory->allocations >= memory->fail_allocation_after) return 0u;
    if (memory->next_page >= MOCK_PAGE_COUNT) return 0u;
    const uint64_t address = MOCK_BASE + (uint64_t)memory->next_page * DUCKOS_X86_64_PAGE_SIZE;
    ++memory->next_page;
    ++memory->allocations;
    return address;
}

static uint64_t *mock_resolve(void *context, uint64_t physical_address) {
    mock_memory *memory = (mock_memory *)context;
    if (physical_address < MOCK_BASE ||
        ((physical_address - MOCK_BASE) % DUCKOS_X86_64_PAGE_SIZE) != 0u) return NULL;
    const uint64_t index = (physical_address - MOCK_BASE) / DUCKOS_X86_64_PAGE_SIZE;
    if (index >= memory->next_page) return NULL;
    return memory->pages[index];
}

static void mock_invalidate(void *context, uint64_t virtual_address) {
    mock_memory *memory = (mock_memory *)context;
    ++memory->invalidations;
    memory->last_invalidated = virtual_address;
}

static void setup(mock_memory *memory, duckos_x86_64_page_table *table) {
    memset(memory, 0, sizeof(*memory));
    memory->next_page = 1u;
    duckos_x86_64_page_table_ops ops = {
        memory, mock_allocate, mock_resolve, mock_invalidate
    };
    assert(duckos_x86_64_page_table_init(table, MOCK_BASE, &ops) ==
        DUCKOS_X86_64_PAGE_TABLE_OK);
}

static void test_user_mapping_round_trip_and_unmap(void) {
    mock_memory memory;
    duckos_x86_64_page_table table;
    uint64_t physical = 0u;
    uint64_t flags = 0u;
    const uint64_t virtual_address = UINT64_C(0x0000000040203000);
    const uint64_t physical_address = UINT64_C(0x0000000002400000);
    const uint64_t permissions = DUCKOS_X86_64_PTE_PRESENT |
        DUCKOS_X86_64_PTE_WRITABLE | DUCKOS_X86_64_PTE_USER |
        DUCKOS_X86_64_PTE_NO_EXECUTE;

    setup(&memory, &table);
    assert(duckos_x86_64_page_map_4k(&table, virtual_address, physical_address, permissions) ==
        DUCKOS_X86_64_PAGE_TABLE_OK);
    assert(memory.invalidations == 1u);
    assert(memory.last_invalidated == virtual_address);
    assert(duckos_x86_64_page_translate(&table, virtual_address + 0x237u, &physical, &flags) ==
        DUCKOS_X86_64_PAGE_TABLE_OK);
    assert(physical == physical_address + 0x237u);
    assert(flags == permissions);
    assert(duckos_x86_64_page_map_4k(&table, virtual_address, physical_address, permissions) ==
        DUCKOS_X86_64_PAGE_TABLE_ALREADY_MAPPED);
    assert(duckos_x86_64_page_unmap_4k(&table, virtual_address) ==
        DUCKOS_X86_64_PAGE_TABLE_OK);
    assert(memory.invalidations == 2u);
    assert(duckos_x86_64_page_translate(&table, virtual_address, &physical, NULL) ==
        DUCKOS_X86_64_PAGE_TABLE_NOT_MAPPED);
    assert(duckos_x86_64_page_unmap_4k(&table, virtual_address) ==
        DUCKOS_X86_64_PAGE_TABLE_NOT_MAPPED);
}

static void test_kernel_mapping_and_user_boundary(void) {
    mock_memory memory;
    duckos_x86_64_page_table table;
    uint64_t physical = 0u;
    const uint64_t kernel_address = UINT64_C(0xffff800000001000);
    const uint64_t permissions = DUCKOS_X86_64_PTE_PRESENT |
        DUCKOS_X86_64_PTE_NO_EXECUTE | DUCKOS_X86_64_PTE_WRITABLE;

    setup(&memory, &table);
    assert(duckos_x86_64_page_map_4k(&table, kernel_address, 0x300000u, permissions) ==
        DUCKOS_X86_64_PAGE_TABLE_OK);
    assert(duckos_x86_64_page_translate(&table, kernel_address, &physical, NULL) ==
        DUCKOS_X86_64_PAGE_TABLE_OK);
    assert(physical == 0x300000u);
    assert(duckos_x86_64_page_map_4k(&table, kernel_address + 0x1000u, 0x301000u,
        permissions | DUCKOS_X86_64_PTE_USER) ==
        DUCKOS_X86_64_PAGE_TABLE_USER_RANGE_VIOLATION);
}

static void test_fail_closed_validation(void) {
    mock_memory memory;
    duckos_x86_64_page_table table;
    setup(&memory, &table);

    assert(duckos_x86_64_page_map_4k(&table, UINT64_C(0x0000800000000000), 0x200000u,
        DUCKOS_X86_64_PTE_PRESENT | DUCKOS_X86_64_PTE_NO_EXECUTE) ==
        DUCKOS_X86_64_PAGE_TABLE_NON_CANONICAL_ADDRESS);
    assert(duckos_x86_64_page_map_4k(&table, 0x400001u, 0x200000u,
        DUCKOS_X86_64_PTE_PRESENT | DUCKOS_X86_64_PTE_NO_EXECUTE) ==
        DUCKOS_X86_64_PAGE_TABLE_MISALIGNED_ADDRESS);
    assert(duckos_x86_64_page_map_4k(&table, 0x400000u, 0x200000u,
        DUCKOS_X86_64_PTE_PRESENT | DUCKOS_X86_64_PTE_WRITABLE) ==
        DUCKOS_X86_64_PAGE_TABLE_WRITE_EXECUTE);
    assert(duckos_x86_64_page_map_4k(&table, 0x400000u, 0x200000u,
        DUCKOS_X86_64_PTE_PRESENT | DUCKOS_X86_64_PTE_HUGE | DUCKOS_X86_64_PTE_NO_EXECUTE) ==
        DUCKOS_X86_64_PAGE_TABLE_INVALID_FLAGS);
    assert(duckos_x86_64_page_map_4k(&table, 0x400000u, 0x200000u,
        DUCKOS_X86_64_PTE_PRESENT | DUCKOS_X86_64_PTE_NO_EXECUTE | (UINT64_C(1) << 60)) ==
        DUCKOS_X86_64_PAGE_TABLE_INVALID_FLAGS);
    assert(duckos_x86_64_page_map_4k(&table, 0x400000u, 0x10000000000000u,
        DUCKOS_X86_64_PTE_PRESENT | DUCKOS_X86_64_PTE_NO_EXECUTE) ==
        DUCKOS_X86_64_PAGE_TABLE_INVALID_PHYSICAL_ADDRESS);
    assert(duckos_x86_64_address_is_canonical(UINT64_C(0xffff800000000000)));
    assert(!duckos_x86_64_address_is_canonical(UINT64_C(0x0000800000000000)));
}

static void test_allocation_failure_is_reported(void) {
    mock_memory memory;
    duckos_x86_64_page_table table;
    setup(&memory, &table);
    memory.fail_allocation_after = 1u;
    assert(duckos_x86_64_page_map_4k(&table, 0x400000u, 0x200000u,
        DUCKOS_X86_64_PTE_PRESENT | DUCKOS_X86_64_PTE_NO_EXECUTE) ==
        DUCKOS_X86_64_PAGE_TABLE_NO_MEMORY);
}

int main(void) {
    test_user_mapping_round_trip_and_unmap();
    test_kernel_mapping_and_user_boundary();
    test_fail_closed_validation();
    test_allocation_failure_is_reported();
    puts("DuckOS x86_64 page-table tests passed");
    return 0;
}
