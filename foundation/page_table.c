#include "page_table.h"

#include <stddef.h>

#define INDEX_MASK UINT64_C(0x1ff)
#define PARENT_FLAGS (DUCKOS_X86_64_PTE_PRESENT | DUCKOS_X86_64_PTE_WRITABLE)

static int physical_page_valid(uint64_t address) {
    return (address & (DUCKOS_X86_64_PAGE_SIZE - 1u)) == 0u &&
        (address & ~DUCKOS_X86_64_PHYSICAL_ADDRESS_MASK) == 0u;
}

static uint16_t page_index(uint64_t address, unsigned int shift) {
    return (uint16_t)((address >> shift) & INDEX_MASK);
}

int duckos_x86_64_address_is_canonical(uint64_t address) {
    const uint64_t upper = address >> 48u;
    const uint64_t sign = (address >> 47u) & UINT64_C(1);
    return sign != 0u ? upper == UINT64_C(0xffff) : upper == 0u;
}

static duckos_x86_64_page_table_status validate_mapping(
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t flags
) {
    if (!duckos_x86_64_address_is_canonical(virtual_address)) {
        return DUCKOS_X86_64_PAGE_TABLE_NON_CANONICAL_ADDRESS;
    }
    if ((virtual_address & (DUCKOS_X86_64_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & (DUCKOS_X86_64_PAGE_SIZE - 1u)) != 0u) {
        return DUCKOS_X86_64_PAGE_TABLE_MISALIGNED_ADDRESS;
    }
    if (!physical_page_valid(physical_address)) {
        return DUCKOS_X86_64_PAGE_TABLE_INVALID_PHYSICAL_ADDRESS;
    }
    if ((flags & ~DUCKOS_X86_64_PTE_LEAF_FLAGS) != 0u ||
        (flags & DUCKOS_X86_64_PTE_PRESENT) == 0u) {
        return DUCKOS_X86_64_PAGE_TABLE_INVALID_FLAGS;
    }
    if ((flags & DUCKOS_X86_64_PTE_WRITABLE) != 0u &&
        (flags & DUCKOS_X86_64_PTE_NO_EXECUTE) == 0u) {
        return DUCKOS_X86_64_PAGE_TABLE_WRITE_EXECUTE;
    }
    if ((flags & DUCKOS_X86_64_PTE_USER) != 0u &&
        virtual_address > DUCKOS_X86_64_USER_ADDRESS_MAX) {
        return DUCKOS_X86_64_PAGE_TABLE_USER_RANGE_VIOLATION;
    }
    return DUCKOS_X86_64_PAGE_TABLE_OK;
}

duckos_x86_64_page_table_status duckos_x86_64_page_table_init(
    duckos_x86_64_page_table *table,
    uint64_t root_physical_address,
    const duckos_x86_64_page_table_ops *ops
) {
    if (table == NULL || ops == NULL || ops->allocate_page == NULL ||
        ops->resolve_page == NULL) {
        return DUCKOS_X86_64_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!physical_page_valid(root_physical_address)) {
        return (root_physical_address & (DUCKOS_X86_64_PAGE_SIZE - 1u)) != 0u
            ? DUCKOS_X86_64_PAGE_TABLE_MISALIGNED_ADDRESS
            : DUCKOS_X86_64_PAGE_TABLE_INVALID_PHYSICAL_ADDRESS;
    }
    if (ops->resolve_page(ops->context, root_physical_address) == NULL) {
        return DUCKOS_X86_64_PAGE_TABLE_MEMORY_ACCESS_FAILED;
    }
    table->root_physical_address = root_physical_address;
    table->ops = *ops;
    return DUCKOS_X86_64_PAGE_TABLE_OK;
}

static duckos_x86_64_page_table_status walk_leaf(
    const duckos_x86_64_page_table *table,
    uint64_t virtual_address,
    uint64_t **leaf_entry
) {
    static const unsigned int shifts[3] = {39u, 30u, 21u};
    uint64_t current_physical = table->root_physical_address;

    for (unsigned int level = 0u; level < 3u; ++level) {
        uint64_t *entries = table->ops.resolve_page(table->ops.context, current_physical);
        if (entries == NULL) return DUCKOS_X86_64_PAGE_TABLE_MEMORY_ACCESS_FAILED;
        const uint64_t entry = entries[page_index(virtual_address, shifts[level])];
        if ((entry & DUCKOS_X86_64_PTE_PRESENT) == 0u) {
            return DUCKOS_X86_64_PAGE_TABLE_NOT_MAPPED;
        }
        if ((entry & DUCKOS_X86_64_PTE_HUGE) != 0u) {
            return DUCKOS_X86_64_PAGE_TABLE_HUGE_PAGE_UNSUPPORTED;
        }
        current_physical = entry & DUCKOS_X86_64_PHYSICAL_ADDRESS_MASK;
    }

    uint64_t *entries = table->ops.resolve_page(table->ops.context, current_physical);
    if (entries == NULL) return DUCKOS_X86_64_PAGE_TABLE_MEMORY_ACCESS_FAILED;
    *leaf_entry = &entries[page_index(virtual_address, 12u)];
    return DUCKOS_X86_64_PAGE_TABLE_OK;
}

duckos_x86_64_page_table_status duckos_x86_64_page_map_4k(
    duckos_x86_64_page_table *table,
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t leaf_flags
) {
    static const unsigned int shifts[3] = {39u, 30u, 21u};
    uint64_t current_physical;

    if (table == NULL || table->ops.allocate_page == NULL ||
        table->ops.resolve_page == NULL) {
        return DUCKOS_X86_64_PAGE_TABLE_INVALID_ARGUMENT;
    }

    const duckos_x86_64_page_table_status validation = validate_mapping(
        virtual_address, physical_address, leaf_flags
    );
    if (validation != DUCKOS_X86_64_PAGE_TABLE_OK) return validation;

    current_physical = table->root_physical_address;
    for (unsigned int level = 0u; level < 3u; ++level) {
        uint64_t *entries = table->ops.resolve_page(table->ops.context, current_physical);
        if (entries == NULL) return DUCKOS_X86_64_PAGE_TABLE_MEMORY_ACCESS_FAILED;
        uint64_t *slot = &entries[page_index(virtual_address, shifts[level])];

        if ((*slot & DUCKOS_X86_64_PTE_PRESENT) == 0u) {
            const uint64_t child_physical = table->ops.allocate_page(table->ops.context);
            if (child_physical == 0u) return DUCKOS_X86_64_PAGE_TABLE_NO_MEMORY;
            if (!physical_page_valid(child_physical)) {
                return DUCKOS_X86_64_PAGE_TABLE_INVALID_PHYSICAL_ADDRESS;
            }
            uint64_t *child = table->ops.resolve_page(table->ops.context, child_physical);
            if (child == NULL) return DUCKOS_X86_64_PAGE_TABLE_MEMORY_ACCESS_FAILED;
            for (uint32_t entry_index = 0u; entry_index < DUCKOS_X86_64_PAGE_ENTRIES; ++entry_index) {
                child[entry_index] = 0u;
            }
            *slot = child_physical | PARENT_FLAGS;
        } else if ((*slot & DUCKOS_X86_64_PTE_HUGE) != 0u) {
            return DUCKOS_X86_64_PAGE_TABLE_HUGE_PAGE_UNSUPPORTED;
        }

        if ((leaf_flags & DUCKOS_X86_64_PTE_USER) != 0u) {
            *slot |= DUCKOS_X86_64_PTE_USER;
        }
        if ((leaf_flags & DUCKOS_X86_64_PTE_WRITABLE) != 0u) {
            *slot |= DUCKOS_X86_64_PTE_WRITABLE;
        }
        current_physical = *slot & DUCKOS_X86_64_PHYSICAL_ADDRESS_MASK;
    }

    uint64_t *entries = table->ops.resolve_page(table->ops.context, current_physical);
    if (entries == NULL) return DUCKOS_X86_64_PAGE_TABLE_MEMORY_ACCESS_FAILED;
    uint64_t *leaf = &entries[page_index(virtual_address, 12u)];
    if ((*leaf & DUCKOS_X86_64_PTE_PRESENT) != 0u) {
        return DUCKOS_X86_64_PAGE_TABLE_ALREADY_MAPPED;
    }

    *leaf = physical_address | leaf_flags;
    if (table->ops.invalidate_page != NULL) {
        table->ops.invalidate_page(table->ops.context, virtual_address);
    }
    return DUCKOS_X86_64_PAGE_TABLE_OK;
}

duckos_x86_64_page_table_status duckos_x86_64_page_unmap_4k(
    duckos_x86_64_page_table *table,
    uint64_t virtual_address
) {
    uint64_t *leaf = NULL;
    if (table == NULL || table->ops.resolve_page == NULL) {
        return DUCKOS_X86_64_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!duckos_x86_64_address_is_canonical(virtual_address)) {
        return DUCKOS_X86_64_PAGE_TABLE_NON_CANONICAL_ADDRESS;
    }
    if ((virtual_address & (DUCKOS_X86_64_PAGE_SIZE - 1u)) != 0u) {
        return DUCKOS_X86_64_PAGE_TABLE_MISALIGNED_ADDRESS;
    }

    const duckos_x86_64_page_table_status status =
        walk_leaf(table, virtual_address, &leaf);
    if (status != DUCKOS_X86_64_PAGE_TABLE_OK) return status;
    if ((*leaf & DUCKOS_X86_64_PTE_PRESENT) == 0u) {
        return DUCKOS_X86_64_PAGE_TABLE_NOT_MAPPED;
    }
    *leaf = 0u;
    if (table->ops.invalidate_page != NULL) {
        table->ops.invalidate_page(table->ops.context, virtual_address);
    }
    return DUCKOS_X86_64_PAGE_TABLE_OK;
}

duckos_x86_64_page_table_status duckos_x86_64_page_translate(
    const duckos_x86_64_page_table *table,
    uint64_t virtual_address,
    uint64_t *physical_address,
    uint64_t *leaf_flags
) {
    uint64_t *leaf = NULL;
    if (table == NULL || physical_address == NULL || table->ops.resolve_page == NULL) {
        return DUCKOS_X86_64_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!duckos_x86_64_address_is_canonical(virtual_address)) {
        return DUCKOS_X86_64_PAGE_TABLE_NON_CANONICAL_ADDRESS;
    }
    const duckos_x86_64_page_table_status status =
        walk_leaf(table, virtual_address, &leaf);
    if (status != DUCKOS_X86_64_PAGE_TABLE_OK) return status;
    if ((*leaf & DUCKOS_X86_64_PTE_PRESENT) == 0u) {
        return DUCKOS_X86_64_PAGE_TABLE_NOT_MAPPED;
    }
    *physical_address = (*leaf & DUCKOS_X86_64_PHYSICAL_ADDRESS_MASK) |
        (virtual_address & (DUCKOS_X86_64_PAGE_SIZE - 1u));
    if (leaf_flags != NULL) *leaf_flags = *leaf & DUCKOS_X86_64_PTE_LEAF_FLAGS;
    return DUCKOS_X86_64_PAGE_TABLE_OK;
}

const char *duckos_x86_64_page_table_status_name(duckos_x86_64_page_table_status status) {
    switch (status) {
    case DUCKOS_X86_64_PAGE_TABLE_OK: return "ok";
    case DUCKOS_X86_64_PAGE_TABLE_INVALID_ARGUMENT: return "invalid-argument";
    case DUCKOS_X86_64_PAGE_TABLE_NON_CANONICAL_ADDRESS: return "non-canonical-address";
    case DUCKOS_X86_64_PAGE_TABLE_MISALIGNED_ADDRESS: return "misaligned-address";
    case DUCKOS_X86_64_PAGE_TABLE_INVALID_PHYSICAL_ADDRESS: return "invalid-physical-address";
    case DUCKOS_X86_64_PAGE_TABLE_INVALID_FLAGS: return "invalid-flags";
    case DUCKOS_X86_64_PAGE_TABLE_WRITE_EXECUTE: return "write-execute";
    case DUCKOS_X86_64_PAGE_TABLE_USER_RANGE_VIOLATION: return "user-range-violation";
    case DUCKOS_X86_64_PAGE_TABLE_ALREADY_MAPPED: return "already-mapped";
    case DUCKOS_X86_64_PAGE_TABLE_NOT_MAPPED: return "not-mapped";
    case DUCKOS_X86_64_PAGE_TABLE_NO_MEMORY: return "no-memory";
    case DUCKOS_X86_64_PAGE_TABLE_MEMORY_ACCESS_FAILED: return "memory-access-failed";
    case DUCKOS_X86_64_PAGE_TABLE_HUGE_PAGE_UNSUPPORTED: return "huge-page-unsupported";
    }
    return "unknown-status";
}
