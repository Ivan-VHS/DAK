#include "page_table.h"

#include <stddef.h>

#define ENTRY_ADDRESS_MASK UINT64_C(0x000ffffffffff000)
#define ENTRY_PAT_LARGE    (UINT64_C(1) << 12)
#define ENTRY_PAT_4K       DUCKOS_PAGE_LARGE
#define ENTRY_SOFTWARE_FLAGS (DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | \
    DUCKOS_PAGE_USER | DUCKOS_PAGE_PWT | DUCKOS_PAGE_PCD | \
    DUCKOS_PAGE_GLOBAL | DUCKOS_PAGE_NX)
#define ENTRY_PARENT_FLAGS (DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | \
    DUCKOS_PAGE_USER | DUCKOS_PAGE_PWT | DUCKOS_PAGE_PCD | DUCKOS_PAGE_ACCESSED)

static uint64_t level_index(uint64_t address, uint8_t level) {
    const uint8_t shift = (uint8_t)(12u + 9u * (level - 1u));
    return (address >> shift) & UINT64_C(0x1ff);
}

int duckos_page_table_is_canonical(uint64_t virtual_address) {
    const uint64_t upper = virtual_address >> 48u;
    const uint64_t sign = (virtual_address >> 47u) & 1u;
    return sign != 0u ? upper == UINT64_C(0xffff) : upper == 0u;
}

static int valid_ops(const duckos_page_table_ops *ops) {
    return ops != NULL && ops->allocate_page != NULL && ops->map_page != NULL;
}

static uint64_t address_mask(uint8_t physical_address_bits) {
    return ((UINT64_C(1) << physical_address_bits) - 1u) &
        ~(uint64_t)(DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u);
}

static uint64_t *map_table(
    const duckos_page_table_space *space,
    uint64_t physical_address
) {
    if (space == NULL || space->ops.map_page == NULL ||
        (physical_address & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & ~space->physical_address_mask) != 0u) {
        return NULL;
    }
    return space->ops.map_page(space->ops.context, physical_address);
}

static void zero_table(uint64_t *table) {
    if (table == NULL) return;
    for (uint32_t index = 0u; index < DUCKOS_PAGE_TABLE_ENTRIES; ++index) {
        table[index] = 0u;
    }
}

static duckos_page_table_status allocate_table(
    duckos_page_table_space *space,
    uint64_t *physical_address
) {
    if (space == NULL || physical_address == NULL) {
        return DUCKOS_PAGE_TABLE_INVALID_ARGUMENT;
    }

    const uint64_t page = space->ops.allocate_page(space->ops.context);
    if (page == 0u) return DUCKOS_PAGE_TABLE_OUT_OF_MEMORY;
    if ((page & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u)) != 0u ||
        (page & ~space->physical_address_mask) != 0u) {
        if (space->ops.release_page != NULL) {
            space->ops.release_page(space->ops.context, page);
        }
        return DUCKOS_PAGE_TABLE_CORRUPT;
    }

    uint64_t *table = map_table(space, page);
    if (table == NULL) {
        if (space->ops.release_page != NULL) {
            space->ops.release_page(space->ops.context, page);
        }
        return DUCKOS_PAGE_TABLE_CORRUPT;
    }
    zero_table(table);
    *physical_address = page;
    return DUCKOS_PAGE_TABLE_OK;
}

static int table_is_empty(const uint64_t *table) {
    if (table == NULL) return 0;
    for (uint32_t index = 0u; index < DUCKOS_PAGE_TABLE_ENTRIES; ++index) {
        if ((table[index] & DUCKOS_PAGE_PRESENT) != 0u) return 0;
    }
    return 1;
}

static void destroy_tree(
    const duckos_page_table_space *space,
    uint64_t table_physical,
    uint8_t level
) {
    uint64_t *table = map_table(space, table_physical);
    if (table == NULL) return;

    if (level > 1u) {
        for (uint32_t index = 0u; index < DUCKOS_PAGE_TABLE_ENTRIES; ++index) {
            const uint64_t entry = table[index];
            if ((entry & DUCKOS_PAGE_PRESENT) == 0u) continue;
            if ((entry & DUCKOS_PAGE_LARGE) != 0u) {
                if (level == 4u) continue;
                continue;
            }
            destroy_tree(space, entry & space->physical_address_mask,
                         (uint8_t)(level - 1u));
        }
    }

    if (space->ops.release_page != NULL) {
        space->ops.release_page(space->ops.context, table_physical);
    }
}

static duckos_page_table_status clone_tree(
    duckos_page_table_space *space,
    uint64_t source_physical,
    uint8_t level,
    uint64_t *destination_physical
) {
    uint64_t *source = map_table(space, source_physical);
    if (source == NULL || destination_physical == NULL || level == 0u || level > 4u) {
        return DUCKOS_PAGE_TABLE_CORRUPT;
    }

    uint64_t target_physical = 0u;
    duckos_page_table_status status = allocate_table(space, &target_physical);
    if (status != DUCKOS_PAGE_TABLE_OK) return status;

    uint64_t *target = map_table(space, target_physical);
    if (target == NULL) {
        if (space->ops.release_page != NULL) {
            space->ops.release_page(space->ops.context, target_physical);
        }
        return DUCKOS_PAGE_TABLE_CORRUPT;
    }

    for (uint32_t index = 0u; index < DUCKOS_PAGE_TABLE_ENTRIES; ++index) {
        const uint64_t entry = source[index];
        if ((entry & DUCKOS_PAGE_PRESENT) == 0u) continue;

        if (level == 4u && (entry & DUCKOS_PAGE_LARGE) != 0u) {
            destroy_tree(space, target_physical, level);
            return DUCKOS_PAGE_TABLE_CORRUPT;
        }

        if (level > 1u && (entry & DUCKOS_PAGE_LARGE) == 0u) {
            uint64_t child_copy = 0u;
            status = clone_tree(
                space,
                entry & space->physical_address_mask,
                (uint8_t)(level - 1u),
                &child_copy
            );
            if (status != DUCKOS_PAGE_TABLE_OK) {
                destroy_tree(space, target_physical, level);
                return status;
            }
            target[index] = (entry & ~space->physical_address_mask) |
                (child_copy & space->physical_address_mask);
        } else {
            target[index] = entry;
        }
    }

    *destination_physical = target_physical;
    return DUCKOS_PAGE_TABLE_OK;
}

duckos_page_table_status duckos_page_table_create(
    duckos_page_table_space *space,
    uint8_t physical_address_bits,
    int supports_nx,
    const duckos_page_table_ops *ops
) {
    if (space == NULL || !valid_ops(ops) ||
        physical_address_bits < 32u || physical_address_bits > 52u) {
        return DUCKOS_PAGE_TABLE_INVALID_ARGUMENT;
    }

    space->root_physical = 0u;
    space->physical_address_bits = physical_address_bits;
    space->physical_address_mask = address_mask(physical_address_bits);
    space->supports_nx = supports_nx != 0 ? 1u : 0u;
    space->active = 0u;
    space->reserved = 0u;
    space->ops = *ops;

    return allocate_table(space, &space->root_physical);
}

duckos_page_table_status duckos_page_table_clone(
    duckos_page_table_space *space,
    uint64_t source_root_physical,
    uint8_t physical_address_bits,
    int supports_nx,
    const duckos_page_table_ops *ops
) {
    if (space == NULL || !valid_ops(ops) ||
        physical_address_bits < 32u || physical_address_bits > 52u ||
        source_root_physical == 0u ||
        (source_root_physical & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u)) != 0u) {
        return DUCKOS_PAGE_TABLE_INVALID_ARGUMENT;
    }

    space->root_physical = 0u;
    space->physical_address_bits = physical_address_bits;
    space->physical_address_mask = address_mask(physical_address_bits);
    space->supports_nx = supports_nx != 0 ? 1u : 0u;
    space->active = 0u;
    space->reserved = 0u;
    space->ops = *ops;

    if ((source_root_physical & ~space->physical_address_mask) != 0u) {
        return DUCKOS_PAGE_TABLE_INVALID_ADDRESS;
    }

    return clone_tree(space, source_root_physical, 4u, &space->root_physical);
}

void duckos_page_table_destroy(duckos_page_table_space *space) {
    if (space == NULL || space->root_physical == 0u) return;
    destroy_tree(space, space->root_physical, 4u);
    space->root_physical = 0u;
    space->active = 0u;
}

static int flags_valid(const duckos_page_table_space *space, uint64_t flags) {
    const uint64_t allowed = ENTRY_SOFTWARE_FLAGS;
    if ((flags & ~allowed) != 0u || (flags & DUCKOS_PAGE_PRESENT) == 0u) return 0;
    if (space->supports_nx != 0u &&
        (flags & DUCKOS_PAGE_WRITABLE) != 0u &&
        (flags & DUCKOS_PAGE_NX) == 0u) return 0;
    if ((flags & DUCKOS_PAGE_NX) != 0u && space->supports_nx == 0u) return 0;
    return 1;
}

static uint64_t parent_flags(uint64_t leaf_flags) {
    uint64_t result = DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE;
    if ((leaf_flags & DUCKOS_PAGE_USER) != 0u) result |= DUCKOS_PAGE_USER;
    return result;
}

static duckos_page_table_status split_large_entry(
    duckos_page_table_space *space,
    uint64_t *parent,
    uint32_t index,
    uint8_t level
) {
    const uint64_t original = parent[index];
    if ((original & DUCKOS_PAGE_PRESENT) == 0u ||
        (original & DUCKOS_PAGE_LARGE) == 0u ||
        (level != 2u && level != 3u)) {
        return DUCKOS_PAGE_TABLE_CORRUPT;
    }

    const uint8_t shift = level == 3u ? 30u : 21u;
    const uint64_t span = UINT64_C(1) << shift;
    const uint64_t physical_base =
        original & space->physical_address_mask & ~(span - 1u);
    const uint64_t large_flags = original &
        (DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_USER |
         DUCKOS_PAGE_PWT | DUCKOS_PAGE_PCD | DUCKOS_PAGE_ACCESSED |
         DUCKOS_PAGE_DIRTY | DUCKOS_PAGE_GLOBAL | DUCKOS_PAGE_NX);
    const int pat = (original & ENTRY_PAT_LARGE) != 0u;

    uint64_t child_physical = 0u;
    duckos_page_table_status status = allocate_table(space, &child_physical);
    if (status != DUCKOS_PAGE_TABLE_OK) return status;

    uint64_t *child = map_table(space, child_physical);
    if (child == NULL) {
        if (space->ops.release_page != NULL) {
            space->ops.release_page(space->ops.context, child_physical);
        }
        return DUCKOS_PAGE_TABLE_CORRUPT;
    }

    if (level == 3u) {
        const uint64_t child_span = UINT64_C(1) << 21u;
        const uint64_t flags = large_flags | DUCKOS_PAGE_LARGE |
            (pat != 0 ? ENTRY_PAT_LARGE : 0u);
        for (uint32_t entry = 0u; entry < DUCKOS_PAGE_TABLE_ENTRIES; ++entry) {
            child[entry] = (physical_base + (uint64_t)entry * child_span) | flags;
        }
    } else {
        const uint64_t child_span = DUCKOS_PAGE_TABLE_PAGE_SIZE;
        uint64_t flags = large_flags;
        if (pat != 0) flags |= ENTRY_PAT_4K;
        for (uint32_t entry = 0u; entry < DUCKOS_PAGE_TABLE_ENTRIES; ++entry) {
            child[entry] = (physical_base + (uint64_t)entry * child_span) | flags;
        }
    }

    /* Permissions live on the leaves after the split; intermediate NX is cleared. */
    parent[index] = child_physical |
        (large_flags & (DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE |
                        DUCKOS_PAGE_USER | DUCKOS_PAGE_PWT | DUCKOS_PAGE_PCD |
                        DUCKOS_PAGE_ACCESSED));
    return DUCKOS_PAGE_TABLE_OK;
}

static duckos_page_table_status find_leaf(
    duckos_page_table_space *space,
    uint64_t virtual_address,
    int split_large,
    uint64_t **leaf_table,
    uint32_t *leaf_index,
    uint64_t *path_tables[4],
    uint32_t path_indices[3]
) {
    if (space == NULL || space->root_physical == 0u || leaf_table == NULL ||
        leaf_index == NULL || path_tables == NULL || path_indices == NULL ||
        !duckos_page_table_is_canonical(virtual_address)) {
        return DUCKOS_PAGE_TABLE_INVALID_ADDRESS;
    }

    path_tables[0] = map_table(space, space->root_physical);
    if (path_tables[0] == NULL) return DUCKOS_PAGE_TABLE_CORRUPT;

    uint64_t current_physical = space->root_physical;
    for (uint8_t level = 4u; level > 1u; --level) {
        uint64_t *table = map_table(space, current_physical);
        if (table == NULL) return DUCKOS_PAGE_TABLE_CORRUPT;
        const uint32_t index = (uint32_t)level_index(virtual_address, level);
        path_indices[4u - level] = index;
        uint64_t entry = table[index];
        if ((entry & DUCKOS_PAGE_PRESENT) == 0u) return DUCKOS_PAGE_TABLE_NOT_MAPPED;

        if ((entry & DUCKOS_PAGE_LARGE) != 0u) {
            if (level == 4u) return DUCKOS_PAGE_TABLE_CORRUPT;
            if (split_large == 0) {
                *leaf_table = table;
                *leaf_index = index;
                return DUCKOS_PAGE_TABLE_OK;
            }
            duckos_page_table_status status =
                split_large_entry(space, table, index, level);
            if (status != DUCKOS_PAGE_TABLE_OK) return status;
            entry = table[index];
        }

        current_physical = entry & space->physical_address_mask;
        path_tables[5u - level] = map_table(space, current_physical);
        if (path_tables[5u - level] == NULL) return DUCKOS_PAGE_TABLE_CORRUPT;
    }

    *leaf_table = map_table(space, current_physical);
    *leaf_index = (uint32_t)level_index(virtual_address, 1u);
    return *leaf_table != NULL ? DUCKOS_PAGE_TABLE_OK : DUCKOS_PAGE_TABLE_CORRUPT;
}

duckos_page_table_status duckos_page_table_map(
    duckos_page_table_space *space,
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t flags
) {
    if (space == NULL || space->root_physical == 0u) {
        return DUCKOS_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!duckos_page_table_is_canonical(virtual_address) ||
        (virtual_address & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & ~space->physical_address_mask) != 0u) {
        return DUCKOS_PAGE_TABLE_INVALID_ADDRESS;
    }
    if (!flags_valid(space, flags)) return DUCKOS_PAGE_TABLE_INVALID_FLAGS;

    uint64_t current_physical = space->root_physical;
    for (uint8_t level = 4u; level > 1u; --level) {
        uint64_t *table = map_table(space, current_physical);
        if (table == NULL) return DUCKOS_PAGE_TABLE_CORRUPT;

        const uint32_t index = (uint32_t)level_index(virtual_address, level);
        uint64_t entry = table[index];
        if ((entry & DUCKOS_PAGE_PRESENT) == 0u) {
            uint64_t child_physical = 0u;
            duckos_page_table_status status = allocate_table(space, &child_physical);
            if (status != DUCKOS_PAGE_TABLE_OK) return status;
            table[index] = child_physical | parent_flags(flags);
            current_physical = child_physical;
            continue;
        }

        if ((entry & DUCKOS_PAGE_LARGE) != 0u) {
            if (level == 4u) return DUCKOS_PAGE_TABLE_CORRUPT;
            duckos_page_table_status status =
                split_large_entry(space, table, index, level);
            if (status != DUCKOS_PAGE_TABLE_OK) return status;
            entry = table[index];
        }

        if ((entry & DUCKOS_PAGE_NX) != 0u &&
            (flags & DUCKOS_PAGE_NX) == 0u) {
            return DUCKOS_PAGE_TABLE_PERMISSION_CONFLICT;
        }
        if ((flags & DUCKOS_PAGE_USER) != 0u) {
            table[index] |= DUCKOS_PAGE_USER;
        }
        if ((flags & DUCKOS_PAGE_WRITABLE) != 0u) {
            table[index] |= DUCKOS_PAGE_WRITABLE;
        }

        current_physical = entry & space->physical_address_mask;
    }

    uint64_t *leaf = map_table(space, current_physical);
    if (leaf == NULL) return DUCKOS_PAGE_TABLE_CORRUPT;
    const uint32_t index = (uint32_t)level_index(virtual_address, 1u);
    if ((leaf[index] & DUCKOS_PAGE_PRESENT) != 0u) {
        return DUCKOS_PAGE_TABLE_ALREADY_MAPPED;
    }

    leaf[index] = (physical_address & space->physical_address_mask) | flags;
    if (space->active != 0u && space->ops.invalidate_page != NULL) {
        space->ops.invalidate_page(space->ops.context, virtual_address);
    }
    return DUCKOS_PAGE_TABLE_OK;
}

duckos_page_table_status duckos_page_table_translate(
    const duckos_page_table_space *space,
    uint64_t virtual_address,
    uint64_t *physical_address,
    uint64_t *effective_flags
) {
    if (space == NULL || space->root_physical == 0u ||
        physical_address == NULL || !duckos_page_table_is_canonical(virtual_address)) {
        return DUCKOS_PAGE_TABLE_INVALID_ARGUMENT;
    }

    uint64_t current_physical = space->root_physical;
    uint64_t combined_flags = DUCKOS_PAGE_PRESENT |
        DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_USER;
    for (uint8_t level = 4u; level > 1u; --level) {
        uint64_t *table = map_table(space, current_physical);
        if (table == NULL) return DUCKOS_PAGE_TABLE_CORRUPT;

        const uint64_t entry = table[level_index(virtual_address, level)];
        if ((entry & DUCKOS_PAGE_PRESENT) == 0u) return DUCKOS_PAGE_TABLE_NOT_MAPPED;
        combined_flags &= entry | ~(DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_USER);
        if ((entry & DUCKOS_PAGE_NX) != 0u) combined_flags |= DUCKOS_PAGE_NX;

        if ((entry & DUCKOS_PAGE_LARGE) != 0u) {
            if (level == 4u) return DUCKOS_PAGE_TABLE_CORRUPT;
            const uint8_t shift = level == 3u ? 30u : 21u;
            const uint64_t offset_mask = (UINT64_C(1) << shift) - 1u;
            const uint64_t base =
                entry & space->physical_address_mask & ~offset_mask;
            *physical_address = base | (virtual_address & offset_mask);
            combined_flags = (entry & ~(space->physical_address_mask |
                DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_USER | DUCKOS_PAGE_NX)) |
                (combined_flags & (DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE |
                                   DUCKOS_PAGE_USER | DUCKOS_PAGE_NX));
            if (effective_flags != NULL) *effective_flags = combined_flags;
            return DUCKOS_PAGE_TABLE_OK;
        }
        current_physical = entry & space->physical_address_mask;
    }

    uint64_t *leaf = map_table(space, current_physical);
    if (leaf == NULL) return DUCKOS_PAGE_TABLE_CORRUPT;
    const uint64_t entry = leaf[level_index(virtual_address, 1u)];
    if ((entry & DUCKOS_PAGE_PRESENT) == 0u) return DUCKOS_PAGE_TABLE_NOT_MAPPED;

    combined_flags &= entry | ~(DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_USER);
    if ((entry & DUCKOS_PAGE_NX) != 0u) combined_flags |= DUCKOS_PAGE_NX;
    combined_flags = (entry & ~(space->physical_address_mask |
        DUCKOS_PAGE_WRITABLE | DUCKOS_PAGE_USER | DUCKOS_PAGE_NX)) |
        (combined_flags & (DUCKOS_PAGE_PRESENT | DUCKOS_PAGE_WRITABLE |
                           DUCKOS_PAGE_USER | DUCKOS_PAGE_NX));
    *physical_address = (entry & space->physical_address_mask) |
        (virtual_address & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u));
    if (effective_flags != NULL) *effective_flags = combined_flags;
    return DUCKOS_PAGE_TABLE_OK;
}

duckos_page_table_status duckos_page_table_protect(
    duckos_page_table_space *space,
    uint64_t virtual_address,
    uint64_t flags
) {
    if (space == NULL || space->root_physical == 0u) {
        return DUCKOS_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!duckos_page_table_is_canonical(virtual_address) ||
        (virtual_address & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u)) != 0u) {
        return DUCKOS_PAGE_TABLE_INVALID_ADDRESS;
    }
    if (!flags_valid(space, flags)) return DUCKOS_PAGE_TABLE_INVALID_FLAGS;

    uint64_t *path_tables[4] = {0};
    uint32_t path_indices[3] = {0};
    uint64_t *leaf = NULL;
    uint32_t leaf_index = 0u;
    duckos_page_table_status status = find_leaf(
        space, virtual_address, 1, &leaf, &leaf_index, path_tables, path_indices);
    if (status != DUCKOS_PAGE_TABLE_OK) return status;

    const uint64_t current = leaf[leaf_index];
    if ((current & DUCKOS_PAGE_PRESENT) == 0u) return DUCKOS_PAGE_TABLE_NOT_MAPPED;

    for (uint32_t depth = 0u; depth < 3u; ++depth) {
        uint64_t *parent = path_tables[depth];
        if (parent == NULL) return DUCKOS_PAGE_TABLE_CORRUPT;
        const uint32_t index = path_indices[depth];
        const uint64_t entry = parent[index];
        if ((entry & DUCKOS_PAGE_NX) != 0u &&
            (flags & DUCKOS_PAGE_NX) == 0u) {
            return DUCKOS_PAGE_TABLE_PERMISSION_CONFLICT;
        }
        if ((flags & DUCKOS_PAGE_USER) != 0u) parent[index] |= DUCKOS_PAGE_USER;
        if ((flags & DUCKOS_PAGE_WRITABLE) != 0u) parent[index] |= DUCKOS_PAGE_WRITABLE;
    }
    leaf[leaf_index] = (current & space->physical_address_mask) | flags;
    if (space->active != 0u && space->ops.invalidate_page != NULL) {
        space->ops.invalidate_page(space->ops.context, virtual_address);
    }
    return DUCKOS_PAGE_TABLE_OK;
}

duckos_page_table_status duckos_page_table_unmap(
    duckos_page_table_space *space,
    uint64_t virtual_address
) {
    if (space == NULL || space->root_physical == 0u) {
        return DUCKOS_PAGE_TABLE_INVALID_ARGUMENT;
    }
    if (!duckos_page_table_is_canonical(virtual_address) ||
        (virtual_address & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u)) != 0u) {
        return DUCKOS_PAGE_TABLE_INVALID_ADDRESS;
    }

    uint64_t *path_tables[4] = {0};
    uint32_t path_indices[3] = {0};
    uint64_t *leaf = NULL;
    uint32_t leaf_index = 0u;
    duckos_page_table_status status = find_leaf(
        space, virtual_address, 1, &leaf, &leaf_index, path_tables, path_indices);
    if (status != DUCKOS_PAGE_TABLE_OK) return status;
    if ((leaf[leaf_index] & DUCKOS_PAGE_PRESENT) == 0u) return DUCKOS_PAGE_TABLE_NOT_MAPPED;

    leaf[leaf_index] = 0u;
    if (space->active != 0u && space->ops.invalidate_page != NULL) {
        space->ops.invalidate_page(space->ops.context, virtual_address);
    }

    /* Reclaim empty PT, PD and PDPT pages; the PML4 root and data frames stay owned. */
    for (int depth = 2; depth >= 0; --depth) {
        uint64_t *parent = path_tables[depth];
        if (parent == NULL) break;
        const uint32_t index = path_indices[depth];
        const uint64_t child_physical =
            parent[index] & space->physical_address_mask;
        uint64_t *child = map_table(space, child_physical);
        if (child == NULL || !table_is_empty(child)) break;

        parent[index] = 0u;
        if (space->ops.release_page != NULL) {
            space->ops.release_page(space->ops.context, child_physical);
        }
    }
    return DUCKOS_PAGE_TABLE_OK;
}
