#include "page_table.h"

#include <stdint.h>

#define PTE_LEAF_FLAGS (DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_USER | \
    DUCKOS_X86_PTE_WRITE_THROUGH | DUCKOS_X86_PTE_CACHE_DISABLE | \
    DUCKOS_X86_PTE_GLOBAL | DUCKOS_X86_PTE_NO_EXECUTE)
#define PTE_SPLIT_FLAGS (DUCKOS_X86_PTE_PRESENT | DUCKOS_X86_PTE_WRITABLE | \
    DUCKOS_X86_PTE_USER | DUCKOS_X86_PTE_WRITE_THROUGH | \
    DUCKOS_X86_PTE_CACHE_DISABLE | DUCKOS_X86_PTE_ACCESSED | \
    DUCKOS_X86_PTE_DIRTY | DUCKOS_X86_PTE_GLOBAL | DUCKOS_X86_PTE_NO_EXECUTE)

static int canonical_48(uint64_t address) {
    const uint64_t upper = address >> 48u;
    const uint64_t sign = (address >> 47u) & 1u;
    return sign != 0u ? upper == 0xffffu : upper == 0u;
}

static int add_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (result == NULL || left > UINT64_MAX - right) return 0;
    *result = left + right;
    return 1;
}

static int valid_leaf_flags(uint64_t flags) {
    return (flags & DUCKOS_X86_PTE_WRITABLE) == 0u ||
        (flags & DUCKOS_X86_PTE_NO_EXECUTE) != 0u;
}

static uint64_t *table_at(
    const duckos_x86_page_table *page_table,
    uint64_t physical_address
) {
    uint64_t virtual_address;
    if (page_table == NULL ||
        (physical_address & (DUCKOS_X86_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & ~DUCKOS_X86_PTE_ADDRESS_MASK) != 0u ||
        !add_u64(page_table->hhdm_offset, physical_address, &virtual_address) ||
        virtual_address > (uint64_t)UINTPTR_MAX) {
        return NULL;
    }
    return (uint64_t *)(uintptr_t)virtual_address;
}

static void zero_table(uint64_t *table) {
    for (uint32_t index = 0u; index < 512u; ++index) table[index] = 0u;
}

static duckos_x86_page_table_status allocate_table(
    duckos_x86_page_table *page_table,
    uint64_t *physical_address,
    uint64_t **virtual_address
) {
    uint64_t physical;
    if (page_table == NULL || page_table->allocator == NULL ||
        physical_address == NULL || virtual_address == NULL) {
        return DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (duckos_frame_allocator_allocate(page_table->allocator, &physical) !=
        DUCKOS_FRAME_ALLOCATOR_OK) {
        return DUCKOS_X86_PAGE_TABLE_OUT_OF_MEMORY;
    }
    uint64_t *table = table_at(page_table, physical);
    if (table == NULL) {
        (void)duckos_frame_allocator_free(page_table->allocator, physical, 1u);
        return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;
    }
    zero_table(table);
    ++page_table->table_pages;
    *physical_address = physical;
    *virtual_address = table;
    return DUCKOS_X86_PAGE_TABLE_OK;
}

static duckos_x86_page_table_status child_table(
    duckos_x86_page_table *page_table,
    uint64_t *parent,
    uint32_t index,
    int user_access,
    uint64_t **child
) {
    uint64_t entry = parent[index];
    if ((entry & DUCKOS_X86_PTE_PRESENT) == 0u) {
        uint64_t child_phys;
        uint64_t *child_virtual;
        duckos_x86_page_table_status status =
            allocate_table(page_table, &child_phys, &child_virtual);
        if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;
        parent[index] = child_phys | DUCKOS_X86_PTE_PRESENT |
            DUCKOS_X86_PTE_WRITABLE |
            (user_access ? DUCKOS_X86_PTE_USER : 0u);
        *child = child_virtual;
        return DUCKOS_X86_PAGE_TABLE_OK;
    }
    if ((entry & DUCKOS_X86_PTE_LARGE) != 0u) {
        return DUCKOS_X86_PAGE_TABLE_UNSUPPORTED_ENTRY;
    }
    if (user_access) parent[index] |= DUCKOS_X86_PTE_USER;
    *child = table_at(page_table, entry & DUCKOS_X86_PTE_ADDRESS_MASK);
    return *child != NULL ? DUCKOS_X86_PAGE_TABLE_OK :
        DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;
}

static duckos_x86_page_table_status split_2m(
    duckos_x86_page_table *page_table,
    uint64_t *directory,
    uint32_t index
) {
    const uint64_t old_entry = directory[index];
    uint64_t table_phys;
    uint64_t *table;
    if ((old_entry & (DUCKOS_X86_PTE_PRESENT | DUCKOS_X86_PTE_LARGE)) !=
        (DUCKOS_X86_PTE_PRESENT | DUCKOS_X86_PTE_LARGE)) {
        return DUCKOS_X86_PAGE_TABLE_NOT_MAPPED;
    }
    duckos_x86_page_table_status status =
        allocate_table(page_table, &table_phys, &table);
    if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;

    const uint64_t physical_base = old_entry & DUCKOS_X86_LARGE_ADDRESS_MASK;
    const uint64_t leaf_flags = old_entry & PTE_SPLIT_FLAGS;
    for (uint32_t page = 0u; page < 512u; ++page) {
        table[page] = (physical_base + (uint64_t)page * DUCKOS_X86_PAGE_SIZE) |
            leaf_flags;
    }
    directory[index] = table_phys | DUCKOS_X86_PTE_PRESENT |
        (old_entry & (DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_USER));
    return DUCKOS_X86_PAGE_TABLE_OK;
}

duckos_x86_page_table_status duckos_x86_page_table_init(
    duckos_x86_page_table *page_table,
    duckos_frame_allocator *allocator,
    uint64_t hhdm_offset
) {
    uint64_t root_phys;
    uint64_t *root;
    if (page_table == NULL || allocator == NULL ||
        allocator->hhdm_offset != hhdm_offset ||
        (hhdm_offset & (DUCKOS_X86_PAGE_SIZE - 1u)) != 0u) {
        return DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT;
    }
    page_table->allocator = allocator;
    page_table->hhdm_offset = hhdm_offset;
    page_table->root_phys = 0u;
    page_table->table_pages = 0u;
    duckos_x86_page_table_status status =
        allocate_table(page_table, &root_phys, &root);
    if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;
    page_table->root_phys = root_phys;
    return DUCKOS_X86_PAGE_TABLE_OK;
}

duckos_x86_page_table_status duckos_x86_page_table_map_4k(
    duckos_x86_page_table *page_table,
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t flags
) {
    uint64_t *pml4;
    uint64_t *pdpt;
    uint64_t *pd;
    uint64_t *pt;
    if (page_table == NULL || page_table->root_phys == 0u) {
        return DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!valid_leaf_flags(flags)) return DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT;
    if (!canonical_48(virtual_address) ||
        (virtual_address & (DUCKOS_X86_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & (DUCKOS_X86_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & ~DUCKOS_X86_PTE_ADDRESS_MASK) != 0u) {
        return DUCKOS_X86_PAGE_TABLE_INVALID_ADDRESS;
    }
    pml4 = table_at(page_table, page_table->root_phys);
    if (pml4 == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;

    duckos_x86_page_table_status status = child_table(
        page_table, pml4, (uint32_t)((virtual_address >> 39u) & 0x1ffu),
        (flags & DUCKOS_X86_PTE_USER) != 0u, &pdpt);
    if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;
    status = child_table(page_table, pdpt,
        (uint32_t)((virtual_address >> 30u) & 0x1ffu),
        (flags & DUCKOS_X86_PTE_USER) != 0u, &pd);
    if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;

    const uint32_t pd_index = (uint32_t)((virtual_address >> 21u) & 0x1ffu);
    if ((pd[pd_index] & (DUCKOS_X86_PTE_PRESENT | DUCKOS_X86_PTE_LARGE)) ==
        (DUCKOS_X86_PTE_PRESENT | DUCKOS_X86_PTE_LARGE)) {
        status = split_2m(page_table, pd, pd_index);
        if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;
    }
    status = child_table(page_table, pd, pd_index,
        (flags & DUCKOS_X86_PTE_USER) != 0u, &pt);
    if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;

    uint64_t *slot = &pt[(virtual_address >> 12u) & 0x1ffu];
    if ((*slot & DUCKOS_X86_PTE_PRESENT) != 0u) {
        return DUCKOS_X86_PAGE_TABLE_ALREADY_MAPPED;
    }
    *slot = physical_address | DUCKOS_X86_PTE_PRESENT | (flags & PTE_LEAF_FLAGS);
    return DUCKOS_X86_PAGE_TABLE_OK;
}

duckos_x86_page_table_status duckos_x86_page_table_map_2m(
    duckos_x86_page_table *page_table,
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t flags
) {
    uint64_t *pml4;
    uint64_t *pdpt;
    uint64_t *pd;
    if (page_table == NULL || page_table->root_phys == 0u) {
        return DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!valid_leaf_flags(flags)) return DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT;
    if (!canonical_48(virtual_address) ||
        (virtual_address & (DUCKOS_X86_LARGE_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & (DUCKOS_X86_LARGE_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & ~DUCKOS_X86_LARGE_ADDRESS_MASK) != 0u) {
        return DUCKOS_X86_PAGE_TABLE_INVALID_ADDRESS;
    }
    pml4 = table_at(page_table, page_table->root_phys);
    if (pml4 == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;
    duckos_x86_page_table_status status = child_table(
        page_table, pml4, (uint32_t)((virtual_address >> 39u) & 0x1ffu),
        (flags & DUCKOS_X86_PTE_USER) != 0u, &pdpt);
    if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;
    status = child_table(page_table, pdpt,
        (uint32_t)((virtual_address >> 30u) & 0x1ffu),
        (flags & DUCKOS_X86_PTE_USER) != 0u, &pd);
    if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;

    const uint32_t index = (uint32_t)((virtual_address >> 21u) & 0x1ffu);
    if ((pd[index] & DUCKOS_X86_PTE_PRESENT) != 0u) {
        return DUCKOS_X86_PAGE_TABLE_ALREADY_MAPPED;
    }
    pd[index] = physical_address | DUCKOS_X86_PTE_PRESENT |
        DUCKOS_X86_PTE_LARGE | (flags & PTE_LEAF_FLAGS);
    return DUCKOS_X86_PAGE_TABLE_OK;
}

duckos_x86_page_table_status duckos_x86_page_table_protect_4k(
    duckos_x86_page_table *page_table,
    uint64_t virtual_address,
    uint64_t flags
) {
    uint64_t *pml4;
    uint64_t *pdpt;
    uint64_t *pd;
    uint64_t *pt;
    if (page_table == NULL || page_table->root_phys == 0u) {
        return DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!valid_leaf_flags(flags)) return DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT;
    if (!canonical_48(virtual_address) ||
        (virtual_address & (DUCKOS_X86_PAGE_SIZE - 1u)) != 0u) {
        return DUCKOS_X86_PAGE_TABLE_INVALID_ADDRESS;
    }
    pml4 = table_at(page_table, page_table->root_phys);
    if (pml4 == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;
    const uint32_t pml4_index = (uint32_t)((virtual_address >> 39u) & 0x1ffu);
    uint64_t entry = pml4[pml4_index];
    if ((entry & DUCKOS_X86_PTE_PRESENT) == 0u) return DUCKOS_X86_PAGE_TABLE_NOT_MAPPED;
    if ((flags & DUCKOS_X86_PTE_USER) != 0u) pml4[pml4_index] |= DUCKOS_X86_PTE_USER;
    pdpt = table_at(page_table, entry & DUCKOS_X86_PTE_ADDRESS_MASK);
    if (pdpt == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;
    const uint32_t pdpt_index = (uint32_t)((virtual_address >> 30u) & 0x1ffu);
    entry = pdpt[pdpt_index];
    if ((entry & DUCKOS_X86_PTE_PRESENT) == 0u) return DUCKOS_X86_PAGE_TABLE_NOT_MAPPED;
    if ((flags & DUCKOS_X86_PTE_USER) != 0u) pdpt[pdpt_index] |= DUCKOS_X86_PTE_USER;
    if ((entry & DUCKOS_X86_PTE_LARGE) != 0u) return DUCKOS_X86_PAGE_TABLE_UNSUPPORTED_ENTRY;
    pd = table_at(page_table, entry & DUCKOS_X86_PTE_ADDRESS_MASK);
    if (pd == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;

    const uint32_t pd_index = (uint32_t)((virtual_address >> 21u) & 0x1ffu);
    if ((pd[pd_index] & DUCKOS_X86_PTE_PRESENT) == 0u) return DUCKOS_X86_PAGE_TABLE_NOT_MAPPED;
    if ((pd[pd_index] & DUCKOS_X86_PTE_LARGE) != 0u) {
        duckos_x86_page_table_status status = split_2m(page_table, pd, pd_index);
        if (status != DUCKOS_X86_PAGE_TABLE_OK) return status;
    }
    if ((flags & DUCKOS_X86_PTE_USER) != 0u) pd[pd_index] |= DUCKOS_X86_PTE_USER;
    pt = table_at(page_table, pd[pd_index] & DUCKOS_X86_PTE_ADDRESS_MASK);
    if (pt == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;
    uint64_t *slot = &pt[(virtual_address >> 12u) & 0x1ffu];
    if ((*slot & DUCKOS_X86_PTE_PRESENT) == 0u) return DUCKOS_X86_PAGE_TABLE_NOT_MAPPED;
    *slot = (*slot & DUCKOS_X86_PTE_ADDRESS_MASK) |
        DUCKOS_X86_PTE_PRESENT | (flags & PTE_LEAF_FLAGS);
    return DUCKOS_X86_PAGE_TABLE_OK;
}

duckos_x86_page_table_status duckos_x86_page_table_translate(
    const duckos_x86_page_table *page_table,
    uint64_t virtual_address,
    uint64_t *physical_address,
    uint64_t *leaf_flags
) {
    uint64_t *pml4;
    if (page_table == NULL || page_table->root_phys == 0u || physical_address == NULL) {
        return DUCKOS_X86_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!canonical_48(virtual_address)) return DUCKOS_X86_PAGE_TABLE_INVALID_ADDRESS;
    pml4 = table_at(page_table, page_table->root_phys);
    if (pml4 == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;

    uint64_t entry = pml4[(virtual_address >> 39u) & 0x1ffu];
    if ((entry & DUCKOS_X86_PTE_PRESENT) == 0u) return DUCKOS_X86_PAGE_TABLE_NOT_MAPPED;
    uint64_t *pdpt = table_at(page_table, entry & DUCKOS_X86_PTE_ADDRESS_MASK);
    if (pdpt == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;

    entry = pdpt[(virtual_address >> 30u) & 0x1ffu];
    if ((entry & DUCKOS_X86_PTE_PRESENT) == 0u) return DUCKOS_X86_PAGE_TABLE_NOT_MAPPED;
    if ((entry & DUCKOS_X86_PTE_LARGE) != 0u) {
        *physical_address = (entry & 0x000fffffc0000000ull) |
            (virtual_address & 0x3fffffffull);
        if (leaf_flags != NULL) *leaf_flags = entry & ~0x000fffffc0000000ull;
        return DUCKOS_X86_PAGE_TABLE_OK;
    }
    uint64_t *pd = table_at(page_table, entry & DUCKOS_X86_PTE_ADDRESS_MASK);
    if (pd == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;

    entry = pd[(virtual_address >> 21u) & 0x1ffu];
    if ((entry & DUCKOS_X86_PTE_PRESENT) == 0u) return DUCKOS_X86_PAGE_TABLE_NOT_MAPPED;
    if ((entry & DUCKOS_X86_PTE_LARGE) != 0u) {
        *physical_address = (entry & DUCKOS_X86_LARGE_ADDRESS_MASK) |
            (virtual_address & 0x1fffffull);
        if (leaf_flags != NULL) *leaf_flags = entry & ~DUCKOS_X86_LARGE_ADDRESS_MASK;
        return DUCKOS_X86_PAGE_TABLE_OK;
    }
    uint64_t *pt = table_at(page_table, entry & DUCKOS_X86_PTE_ADDRESS_MASK);
    if (pt == NULL) return DUCKOS_X86_PAGE_TABLE_ADDRESS_ERROR;

    entry = pt[(virtual_address >> 12u) & 0x1ffu];
    if ((entry & DUCKOS_X86_PTE_PRESENT) == 0u) return DUCKOS_X86_PAGE_TABLE_NOT_MAPPED;
    *physical_address = (entry & DUCKOS_X86_PTE_ADDRESS_MASK) |
        (virtual_address & 0xfffu);
    if (leaf_flags != NULL) *leaf_flags = entry & ~DUCKOS_X86_PTE_ADDRESS_MASK;
    return DUCKOS_X86_PAGE_TABLE_OK;
}
