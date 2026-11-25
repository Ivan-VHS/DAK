#ifndef DUCKBOOT_ARENA_H
#define DUCKBOOT_ARENA_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct duckboot_arena {
    uint8_t *base;
    size_t capacity;
    size_t used;
} duckboot_arena;

typedef enum duckboot_arena_status {
    DUCKBOOT_ARENA_OK = 0,
    DUCKBOOT_ARENA_INVALID_ARGUMENT = -1,
    DUCKBOOT_ARENA_INVALID_ALIGNMENT = -2,
    DUCKBOOT_ARENA_OUT_OF_MEMORY = -3,
    DUCKBOOT_ARENA_INVALID_CHECKPOINT = -4
} duckboot_arena_status;

duckboot_arena_status duckboot_arena_init(
    duckboot_arena *arena,
    void *storage,
    size_t capacity
);

void *duckboot_arena_allocate(
    duckboot_arena *arena,
    size_t size,
    size_t alignment
);

size_t duckboot_arena_checkpoint(const duckboot_arena *arena);

duckboot_arena_status duckboot_arena_rewind(
    duckboot_arena *arena,
    size_t checkpoint,
    bool clear_released_memory
);

void duckboot_arena_reset(duckboot_arena *arena, bool clear_memory);

#endif
