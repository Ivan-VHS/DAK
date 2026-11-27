#ifndef DUCKOS_X86_64_PAGE_TABLE_H
#define DUCKOS_X86_64_PAGE_TABLE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_X86_64_PAGE_SIZE UINT64_C(4096)
#define DUCKOS_X86_64_PAGE_ENTRIES 512u
#define DUCKOS_X86_64_PHYSICAL_ADDRESS_MASK UINT64_C(0x000ffffffffff000)
#define DUCKOS_X86_64_USER_ADDRESS_MAX UINT64_C(0x00007fffffffffff)

#define DUCKOS_X86_64_PTE_PRESENT UINT64_C(0x001)
#define DUCKOS_X86_64_PTE_WRITABLE UINT64_C(0x002)
#define DUCKOS_X86_64_PTE_USER UINT64_C(0x004)
#define DUCKOS_X86_64_PTE_WRITE_THROUGH UINT64_C(0x008)
#define DUCKOS_X86_64_PTE_CACHE_DISABLE UINT64_C(0x010)
#define DUCKOS_X86_64_PTE_HUGE UINT64_C(0x080)
#define DUCKOS_X86_64_PTE_GLOBAL UINT64_C(0x100)
#define DUCKOS_X86_64_PTE_NO_EXECUTE (UINT64_C(1) << 63)

#define DUCKOS_X86_64_PTE_LEAF_FLAGS ( \
    DUCKOS_X86_64_PTE_PRESENT | DUCKOS_X86_64_PTE_WRITABLE | \
    DUCKOS_X86_64_PTE_USER | DUCKOS_X86_64_PTE_WRITE_THROUGH | \
    DUCKOS_X86_64_PTE_CACHE_DISABLE | DUCKOS_X86_64_PTE_GLOBAL | \
    DUCKOS_X86_64_PTE_NO_EXECUTE)

typedef enum duckos_x86_64_page_table_status {
    DUCKOS_X86_64_PAGE_TABLE_OK = 0,
    DUCKOS_X86_64_PAGE_TABLE_INVALID_ARGUMENT,
    DUCKOS_X86_64_PAGE_TABLE_NON_CANONICAL_ADDRESS,
    DUCKOS_X86_64_PAGE_TABLE_MISALIGNED_ADDRESS,
    DUCKOS_X86_64_PAGE_TABLE_INVALID_PHYSICAL_ADDRESS,
    DUCKOS_X86_64_PAGE_TABLE_INVALID_FLAGS,
    DUCKOS_X86_64_PAGE_TABLE_WRITE_EXECUTE,
    DUCKOS_X86_64_PAGE_TABLE_USER_RANGE_VIOLATION,
    DUCKOS_X86_64_PAGE_TABLE_ALREADY_MAPPED,
    DUCKOS_X86_64_PAGE_TABLE_NOT_MAPPED,
    DUCKOS_X86_64_PAGE_TABLE_NO_MEMORY,
    DUCKOS_X86_64_PAGE_TABLE_MEMORY_ACCESS_FAILED,
    DUCKOS_X86_64_PAGE_TABLE_HUGE_PAGE_UNSUPPORTED
} duckos_x86_64_page_table_status;

typedef uint64_t (*duckos_x86_64_page_allocate_fn)(void *context);
typedef uint64_t *(*duckos_x86_64_page_resolve_fn)(void *context, uint64_t physical_address);
typedef void (*duckos_x86_64_page_invalidate_fn)(void *context, uint64_t virtual_address);

typedef struct duckos_x86_64_page_table_ops {
    void *context;
    duckos_x86_64_page_allocate_fn allocate_page;
    duckos_x86_64_page_resolve_fn resolve_page;
    duckos_x86_64_page_invalidate_fn invalidate_page;
} duckos_x86_64_page_table_ops;

typedef struct duckos_x86_64_page_table {
    uint64_t root_physical_address;
    duckos_x86_64_page_table_ops ops;
} duckos_x86_64_page_table;

/*
 * Manages four-level 4 KiB page-table structures for 48-bit canonical
 * addresses. The root must be an allocated, zeroed physical page.
 *
 * resolve_page must return a writable kernel mapping of the complete page.
 * The API does not load CR3, enable paging or change the active address space.
 * Callers must serialize mutations and provide invalidation only when the
 * target address space is active.
 */
duckos_x86_64_page_table_status duckos_x86_64_page_table_init(
    duckos_x86_64_page_table *table,
    uint64_t root_physical_address,
    const duckos_x86_64_page_table_ops *ops
);

duckos_x86_64_page_table_status duckos_x86_64_page_map_4k(
    duckos_x86_64_page_table *table,
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t leaf_flags
);

duckos_x86_64_page_table_status duckos_x86_64_page_unmap_4k(
    duckos_x86_64_page_table *table,
    uint64_t virtual_address
);

duckos_x86_64_page_table_status duckos_x86_64_page_translate(
    const duckos_x86_64_page_table *table,
    uint64_t virtual_address,
    uint64_t *physical_address,
    uint64_t *leaf_flags
);

int duckos_x86_64_address_is_canonical(uint64_t address);
const char *duckos_x86_64_page_table_status_name(duckos_x86_64_page_table_status status);

#ifdef __cplusplus
}
#endif

#endif
