#include "duckboot/arena.h"

#include <stdint.h>

static bool is_power_of_two(size_t value) {
    return value != 0u && (value & (value - 1u)) == 0u;
}

duckboot_arena_status duckboot_arena_init(
    duckboot_arena *arena,
    void *storage,
    size_t capacity
) {
    if (arena == NULL || storage == NULL || capacity == 0u) {
        return DUCKBOOT_ARENA_INVALID_ARGUMENT;
    }

    arena->base = (uint8_t *)storage;
    arena->capacity = capacity;
    arena->used = 0u;
    return DUCKBOOT_ARENA_OK;
}

void *duckboot_arena_allocate(
    duckboot_arena *arena,
    size_t size,
    size_t alignment
) {
    uintptr_t base_address;
    uintptr_t current_address;
    uintptr_t aligned_address;
    size_t padding;
    size_t remaining;

    if (arena == NULL || arena->base == NULL || size == 0u) return NULL;
    if (!is_power_of_two(alignment)) return NULL;
    if (arena->used > arena->capacity) return NULL;

    base_address = (uintptr_t)arena->base;
    if (base_address > UINTPTR_MAX - arena->used) return NULL;
    current_address = base_address + arena->used;
    if (current_address > UINTPTR_MAX - (alignment - 1u)) return NULL;
    aligned_address = (current_address + alignment - 1u) & ~(uintptr_t)(alignment - 1u);
    if (aligned_address < current_address) return NULL;

    padding = (size_t)(aligned_address - current_address);
    remaining = arena->capacity - arena->used;
    if (padding > remaining || size > remaining - padding) return NULL;

    arena->used += padding + size;
    return (void *)aligned_address;
}

size_t duckboot_arena_checkpoint(const duckboot_arena *arena) {
    if (arena == NULL || arena->base == NULL || arena->used > arena->capacity) {
        return SIZE_MAX;
    }
    return arena->used;
}

duckboot_arena_status duckboot_arena_rewind(
    duckboot_arena *arena,
    size_t checkpoint,
    bool clear_released_memory
) {
    if (arena == NULL || arena->base == NULL) return DUCKBOOT_ARENA_INVALID_ARGUMENT;
    if (checkpoint > arena->used || arena->used > arena->capacity) {
        return DUCKBOOT_ARENA_INVALID_CHECKPOINT;
    }

    if (clear_released_memory) {
        for (size_t index = checkpoint; index < arena->used; ++index) {
            arena->base[index] = 0u;
        }
    }
    arena->used = checkpoint;
    return DUCKBOOT_ARENA_OK;
}

void duckboot_arena_reset(duckboot_arena *arena, bool clear_memory) {
    if (arena == NULL || arena->base == NULL || arena->used > arena->capacity) return;
    if (clear_memory) {
        for (size_t index = 0u; index < arena->used; ++index) arena->base[index] = 0u;
    }
    arena->used = 0u;
}
