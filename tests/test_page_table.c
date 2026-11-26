#include "page_table.h"

#include <stdint.h>
#include <stdio.h>

#define CHECK(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "check failed at %s:%d: %s\n", __FILE__, __LINE__, #expression); \
        return 0; \
    } \
} while (0)

static _Alignas(4096) uint8_t memory[16u * 1024u * 1024u];

static int test_four_level_mapping_and_permissions(void) {
    const duckos_memory_region regions[] = {
        {0u, sizeof(memory), DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    duckos_x86_page_table tables;
    uint64_t translated = 0u;
    uint64_t flags = 0u;
    const uint64_t hhdm = (uint64_t)(uintptr_t)memory;

    CHECK(duckos_frame_allocator_init(&allocator, regions, 1u, 0x1000u, hhdm) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_x86_page_table_init(&tables, &allocator, hhdm) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(duckos_x86_page_table_map_4k(&tables, 0xffff800040001000ull, 0x800000ull,
        DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(duckos_x86_page_table_translate(&tables, 0xffff800040001123ull,
        &translated, &flags) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(translated == 0x800123ull);
    CHECK((flags & DUCKOS_X86_PTE_WRITABLE) != 0u);
    CHECK((flags & DUCKOS_X86_PTE_NO_EXECUTE) != 0u);
    CHECK(duckos_x86_page_table_map_4k(&tables, 0xffff800040002000ull, 0x801000ull,
        DUCKOS_X86_PTE_WRITABLE) == DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT);
    CHECK(duckos_x86_page_table_map_4k(&tables, 0xffff800040001000ull, 0x800000ull,
        DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE) == DUCKOS_X86_PAGE_TABLE_ALREADY_MAPPED);
    CHECK(duckos_x86_page_table_protect_4k(&tables, 0xffff800040001000ull,
        DUCKOS_X86_PTE_NO_EXECUTE) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(duckos_x86_page_table_translate(&tables, 0xffff800040001000ull,
        &translated, &flags) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK((flags & DUCKOS_X86_PTE_WRITABLE) == 0u);
    CHECK(duckos_x86_page_table_protect_4k(&tables, 0xffff800040001000ull,
        DUCKOS_X86_PTE_USER | DUCKOS_X86_PTE_NO_EXECUTE) == DUCKOS_X86_PAGE_TABLE_OK);
    uint64_t *pml4 = (uint64_t *)(uintptr_t)(hhdm + tables.root_phys);
    const uint64_t pml4e = pml4[(0xffff800040001000ull >> 39u) & 0x1ffu];
    CHECK((pml4e & DUCKOS_X86_PTE_USER) != 0u);
    uint64_t *pdpt = (uint64_t *)(uintptr_t)(hhdm + (pml4e & DUCKOS_X86_PTE_ADDRESS_MASK));
    const uint64_t pdpte = pdpt[(0xffff800040001000ull >> 30u) & 0x1ffu];
    CHECK((pdpte & DUCKOS_X86_PTE_USER) != 0u);
    uint64_t *pd = (uint64_t *)(uintptr_t)(hhdm + (pdpte & DUCKOS_X86_PTE_ADDRESS_MASK));
    const uint64_t pde = pd[(0xffff800040001000ull >> 21u) & 0x1ffu];
    CHECK((pde & DUCKOS_X86_PTE_USER) != 0u);
    return 1;
}

static int test_huge_page_split_and_neighbor_preservation(void) {
    const duckos_memory_region regions[] = {
        {0u, sizeof(memory), DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    duckos_x86_page_table tables;
    uint64_t translated = 0u;
    uint64_t flags = 0u;
    const uint64_t hhdm = (uint64_t)(uintptr_t)memory;

    CHECK(duckos_frame_allocator_init(&allocator, regions, 1u, 0x1000u, hhdm) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_x86_page_table_init(&tables, &allocator, hhdm) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(duckos_x86_page_table_map_2m(&tables, 0xffff900000200000ull, 0x200000ull,
        DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(duckos_x86_page_table_translate(&tables, 0xffff900000201234ull,
        &translated, &flags) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(translated == 0x201234ull);
    CHECK((flags & DUCKOS_X86_PTE_LARGE) != 0u);
    CHECK(duckos_x86_page_table_protect_4k(&tables, 0xffff900000201000ull,
        DUCKOS_X86_PTE_NO_EXECUTE) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(duckos_x86_page_table_translate(&tables, 0xffff900000201123ull,
        &translated, &flags) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(translated == 0x201123ull);
    CHECK((flags & DUCKOS_X86_PTE_LARGE) == 0u);
    CHECK((flags & DUCKOS_X86_PTE_WRITABLE) == 0u);
    CHECK(duckos_x86_page_table_translate(&tables, 0xffff900000202123ull,
        &translated, &flags) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(translated == 0x202123ull);
    CHECK((flags & DUCKOS_X86_PTE_WRITABLE) != 0u);
    return 1;
}

static int test_rejects_noncanonical_and_misaligned_addresses(void) {
    const duckos_memory_region regions[] = {
        {0u, sizeof(memory), DUCKOS_MEMORY_USABLE, 0u}
    };
    duckos_frame_allocator allocator;
    duckos_x86_page_table tables;
    const uint64_t hhdm = (uint64_t)(uintptr_t)memory;
    CHECK(duckos_frame_allocator_init(&allocator, regions, 1u, 0x1000u, hhdm) ==
        DUCKOS_FRAME_ALLOCATOR_OK);
    CHECK(duckos_x86_page_table_init(&tables, &allocator, hhdm) == DUCKOS_X86_PAGE_TABLE_OK);
    CHECK(duckos_x86_page_table_map_4k(&tables, 0x0000800000000000ull, 0x3000u,
        DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE) == DUCKOS_X86_PAGE_TABLE_INVALID_ADDRESS);
    CHECK(duckos_x86_page_table_map_4k(&tables, 0x4000u, 0x3001u,
        DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE) == DUCKOS_X86_PAGE_TABLE_INVALID_ADDRESS);
    return 1;
}

int main(void) {
    if (!test_four_level_mapping_and_permissions() ||
        !test_huge_page_split_and_neighbor_preservation() ||
        !test_rejects_noncanonical_and_misaligned_addresses()) return 1;
    puts("DuckOS x86_64 page-table tests passed");
    return 0;
}
