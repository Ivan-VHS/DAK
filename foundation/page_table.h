#ifndef DUCKOS_X86_PAGE_TABLE_H
#define DUCKOS_X86_PAGE_TABLE_H

#include <stdint.h>
#include "frame_allocator.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_X86_PAGE_SIZE 4096ull
#define DUCKOS_X86_LARGE_PAGE_SIZE 0x200000ull
#define DUCKOS_X86_PTE_PRESENT (1ull << 0)
#define DUCKOS_X86_PTE_WRITABLE (1ull << 1)
#define DUCKOS_X86_PTE_USER (1ull << 2)
#define DUCKOS_X86_PTE_WRITE_THROUGH (1ull << 3)
#define DUCKOS_X86_PTE_CACHE_DISABLE (1ull << 4)
#define DUCKOS_X86_PTE_ACCESSED (1ull << 5)
#define DUCKOS_X86_PTE_DIRTY (1ull << 6)
#define DUCKOS_X86_PTE_LARGE (1ull << 7)
#define DUCKOS_X86_PTE_GLOBAL (1ull << 8)
#define DUCKOS_X86_PTE_NO_EXECUTE (1ull << 63)
#define DUCKOS_X86_PTE_ADDRESS_MASK 0x000ffffffffff000ull
#define DUCKOS_X86_LARGE_ADDRESS_MASK 0x000fffffffe00000ull

typedef struct duckos_x86_page_table {
    duckos_frame_allocator *allocator;
    uint64_t hhdm_offset;
    uint64_t root_phys;
    uint64_t table_pages;
} duckos_x86_page_table;

typedef enum duckos_x86_page_table_status {
    DUCKOS_X86_PAGE_TABLE_OK = 0,
    DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT = -1,
    DUCKOS_X86_PAGE_TABLE_INVALID_ADDRESS = -2,
    DUCKOS_X86_PAGE_TABLE_OUT_OF_MEMORY = -3,
    DUCKOS_X86_PAGE_TABLE_ALREADY_MAPPED = -4,
    DUCKOS_X86_PAGE_TABLE_NOT_MAPPED = -5,
    DUCKOS_X86_PAGE_TABLE_UNSUPPORTED_ENTRY = -6,
    DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR = -7
} duckos_x86_page_table_status;

duckos_x86_page_table_status duckos_x86_page_table_init(
    duckos_x86_page_table *page_table,
    duckos_frame_allocator *allocator,
    uint64_t hhdm_offset
);

duckos_x86_page_table_status duckos_x86_page_table_map_4k(
    duckos_x86_page_table *page_table,
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t flags
);

duckos_x86_page_table_status duckos_x86_page_table_map_2m(
    duckos_x86_page_table *page_table,
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t flags
);

duckos_x86_page_table_status duckos_x86_page_table_protect_4k(
    duckos_x86_page_table *page_table,
    uint64_t virtual_address,
    uint64_t flags
);

duckos_x86_page_table_status duckos_x86_page_table_translate(
    const duckos_x86_page_table *page_table,
    uint64_t virtual_address,
    uint64_t *physical_address,
    uint64_t *leaf_flags
);

#ifdef __cplusplus
}
#endif

#endif
