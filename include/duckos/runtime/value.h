#ifndef DUCKOS_RUNTIME_VALUE_H
#define DUCKOS_RUNTIME_VALUE_H

#include <stddef.h>
#include <stdint.h>

#include "duckos/abi/dabi64.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DUCK_RUNTIME_MAX_ARRAY_GRAPH 128u

typedef enum DuckRuntimeStatus {
    DUCK_RUNTIME_OK = 0,
    DUCK_RUNTIME_INVALID_ARGUMENT = 1,
    DUCK_RUNTIME_TYPE_MISMATCH = 2,
    DUCK_RUNTIME_OUT_OF_MEMORY = 3,
    DUCK_RUNTIME_OUT_OF_BOUNDS = 4,
    DUCK_RUNTIME_SIZE_OVERFLOW = 5,
    DUCK_RUNTIME_REFERENCE_OVERFLOW = 6,
    DUCK_RUNTIME_CYCLIC_VALUE = 7,
    DUCK_RUNTIME_GRAPH_LIMIT = 8,
    DUCK_RUNTIME_CORRUPT_VALUE = 9
} DuckRuntimeStatus;

/* The allocator must provide normal C object alignment. Its context must
 * outlive every value allocated through it. */
typedef void *(*DuckRuntimeAllocateFn)(void *context, size_t size);
typedef void (*DuckRuntimeDeallocateFn)(void *context, void *memory);

typedef struct DuckRuntimeAllocator {
    void *context;
    DuckRuntimeAllocateFn allocate;
    DuckRuntimeDeallocateFn deallocate;
} DuckRuntimeAllocator;

typedef struct DuckRuntime {
    DuckRuntimeAllocator allocator;
} DuckRuntime;

DuckRuntimeStatus duck_runtime_init(
    DuckRuntime *runtime,
    DuckRuntimeAllocator allocator
);

DuckValue duck_value_unit(void);
DuckValue duck_value_i64(int64_t value);
DuckValue duck_value_bool(int value);

DuckRuntimeStatus duck_value_as_i64(const DuckValue *value, int64_t *out);
DuckRuntimeStatus duck_value_as_bool(const DuckValue *value, int *out);

DuckRuntimeStatus duck_value_clone(const DuckValue *source, DuckValue *destination);
void duck_value_move(DuckValue *source, DuckValue *destination);
void duck_value_drop(DuckValue *value);

DuckRuntimeStatus duck_value_string_new(
    DuckRuntime *runtime,
    const char *bytes,
    size_t length,
    DuckValue *out
);
DuckRuntimeStatus duck_value_string_view(
    const DuckValue *value,
    const char **bytes,
    size_t *length
);

DuckRuntimeStatus duck_value_array_new(
    DuckRuntime *runtime,
    size_t reserve,
    DuckValue *out
);
DuckRuntimeStatus duck_value_array_push(DuckValue *array, const DuckValue *item);
DuckRuntimeStatus duck_value_array_get(
    const DuckValue *array,
    size_t index,
    DuckValue *out
);
DuckRuntimeStatus duck_value_array_length(
    const DuckValue *array,
    size_t *length
);

DuckRuntimeStatus duck_value_iterator_new(
    DuckRuntime *runtime,
    const DuckValue *array,
    DuckValue *out
);
/* Returns has_value = 0 at end, or a cloned element with has_value = 1. */
DuckRuntimeStatus duck_value_iterator_next(
    DuckValue *iterator,
    DuckValue *out,
    int *has_value
);

#ifdef __cplusplus
}
#endif

#endif
