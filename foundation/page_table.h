#ifndef DUCKOS_PAGE_TABLE_H
#define DUCKOS_PAGE_TABLE_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_PAGE_TABLE_PAGE_SIZE 4096u
#define DUCKOS_PAGE_TABLE_ENTRIES 512u
#define DUCKOS_PAGE_TABLE_LEVELS 4u

#define DUCKOS_PAGE_PRESENT  (UINT64_C(1) << 0)
#define DUCKOS_PAGE_WRITABLE (UINT64_C(1) << 1)
#define DUCKOS_PAGE_USER     (UINT64_C(1) << 2)
#define DUCKOS_PAGE_PWT      (UINT64_C(1) << 3)
#define DUCKOS_PAGE_PCD      (UINT64_C(1) << 4)
#define DUCKOS_PAGE_ACCESSED (UINT64_C(1) << 5)
#define DUCKOS_PAGE_DIRTY    (UINT64_C(1) << 6)
#define DUCKOS_PAGE_LARGE    (UINT64_C(1) << 7)
#define DUCKOS_PAGE_GLOBAL   (UINT64_C(1) << 8)
#define DUCKOS_PAGE_NX       (UINT64_C(1) << 63)

typedef enum duckos_page_table_status {
    DUCKOS_PAGE_TABLE_OK = 0,
    DUCKOS_PAGE_TABLE_INVALID_ARGUMENT = -1,
    DUCKOS_PAGE_TABLE_INVALID_ADDRESS = -2,
    DUCKOS_PAGE_TABLE_INVALID_FLAGS = -3,
    DUCKOS_PAGE_TABLE_NOT_MAPPED = -4,
    DUCKOS_PAGE_TABLE_ALREADY_MAPPED = -5,
    DUCKOS_PAGE_TABLE_OUT_OF_MEMORY = -6,
    DUCKOS_PAGE_TABLE_UNSUPPORTED = -7,
    DUCKOS_PAGE_TABLE_PERMISSION_CONFLICT = -8,
    DUCKOS_PAGE_TABLE_CORRUPT = -9
} duckos_page_table_status;

typedef uint64_t (*duckos_page_table_allocate_fn)(void *context);
typedef void (*duckos_page_table_release_fn)(void *context, uint64_t physical_address);
typedef uint64_t *(*duckos_page_table_map_fn)(void *context, uint64_t physical_address);
typedef void (*duckos_page_table_invalidate_fn)(void *context, uint64_t virtual_address);

typedef struct duckos_page_table_ops {
    void *context;
    duckos_page_table_allocate_fn allocate_page;
    duckos_page_table_release_fn release_page;
    duckos_page_table_map_fn map_page;
    duckos_page_table_invalidate_fn invalidate_page;
} duckos_page_table_ops;

typedef struct duckos_page_table_space {
    uint64_t root_physical;
    uint64_t physical_address_mask;
    uint8_t physical_address_bits;
    uint8_t supports_nx;
    uint8_t active;
    uint8_t reserved;
    duckos_page_table_ops ops;
} duckos_page_table_space;

/* Four-level, 48-bit canonical x86_64 address-space operations. */
int duckos_page_table_is_canonical(uint64_t virtual_address);

/* Create an empty PML4 or clone the currently active hierarchy into owned pages. */
duckos_page_table_status duckos_page_table_create(
    duckos_page_table_space *space,
    uint8_t physical_address_bits,
    int supports_nx,
    const duckos_page_table_ops *ops
);

duckos_page_table_status duckos_page_table_clone(
    duckos_page_table_space *space,
    uint64_t source_root_physical,
    uint8_t physical_address_bits,
    int supports_nx,
    const duckos_page_table_ops *ops
);

/* Release only page-table pages owned by this space; mapped data pages are untouched. */
void duckos_page_table_destroy(duckos_page_table_space *space);

duckos_page_table_status duckos_page_table_map(
    duckos_page_table_space *space,
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t flags
);

duckos_page_table_status duckos_page_table_unmap(
    duckos_page_table_space *space,
    uint64_t virtual_address
);

duckos_page_table_status duckos_page_table_protect(
    duckos_page_table_space *space,
    uint64_t virtual_address,
    uint64_t flags
);

/* Returns the physical address including the in-page offset and effective leaf flags. */
duckos_page_table_status duckos_page_table_translate(
    const duckos_page_table_space *space,
    uint64_t virtual_address,
    uint64_t *physical_address,
    uint64_t *effective_flags
);

#ifdef __cplusplus
}
#endif

#endif
