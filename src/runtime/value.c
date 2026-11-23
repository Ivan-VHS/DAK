#include "duckos/runtime/value.h"

#include <stdatomic.h>
#include <stdint.h>
#include <string.h>

#define DUCK_OBJECT_MAGIC UINT32_C(0x44554B4F)

typedef enum DuckObjectKind {
    DUCK_OBJECT_STRING = 1u,
    DUCK_OBJECT_ARRAY = 2u,
    DUCK_OBJECT_ITERATOR = 3u
} DuckObjectKind;

typedef struct DuckHeapObject {
    uint32_t magic;
    uint32_t object_kind;
    _Atomic uint32_t references;
    uint32_t reserved;
    DuckRuntimeAllocator allocator;
} DuckHeapObject;

typedef struct DuckString {
    DuckHeapObject object;
    size_t length;
    char bytes[];
} DuckString;

typedef struct DuckArray {
    DuckHeapObject object;
    size_t length;
    size_t capacity;
    DuckValue *items;
} DuckArray;

typedef struct DuckIterator {
    DuckHeapObject object;
    DuckValue source;
    size_t index;
} DuckIterator;

static DuckRuntimeStatus allocate_object(
    DuckRuntime *runtime,
    size_t size,
    DuckObjectKind kind,
    DuckHeapObject **out
) {
    DuckHeapObject *object;

    if (runtime == NULL || out == NULL ||
        runtime->allocator.allocate == NULL ||
        runtime->allocator.deallocate == NULL) {
        return DUCK_RUNTIME_INVALID_ARGUMENT;
    }

    object = runtime->allocator.allocate(runtime->allocator.context, size);
    if (object == NULL) return DUCK_RUNTIME_OUT_OF_MEMORY;

    memset(object, 0, size);
    object->magic = DUCK_OBJECT_MAGIC;
    object->object_kind = (uint32_t)kind;
    atomic_init(&object->references, 1U);
    object->allocator = runtime->allocator;
    *out = object;
    return DUCK_RUNTIME_OK;
}

static DuckHeapObject *object_from_value(const DuckValue *value) {
    DuckHeapObject *object;

    if (value == NULL) return NULL;
    if (value->kind != DUCK_VALUE_STRING &&
        value->kind != DUCK_VALUE_ARRAY &&
        value->kind != DUCK_VALUE_ITERATOR) {
        return NULL;
    }

    object = (DuckHeapObject *)(uintptr_t)value->payload;
    if (object == NULL || object->magic != DUCK_OBJECT_MAGIC) return NULL;

    if ((value->kind == DUCK_VALUE_STRING &&
         object->object_kind != DUCK_OBJECT_STRING) ||
        (value->kind == DUCK_VALUE_ARRAY &&
         object->object_kind != DUCK_OBJECT_ARRAY) ||
        (value->kind == DUCK_VALUE_ITERATOR &&
         object->object_kind != DUCK_OBJECT_ITERATOR)) {
        return NULL;
    }

    return object;
}

static DuckRuntimeStatus retain_object(DuckHeapObject *object) {
    uint32_t current;

    if (object == NULL || object->magic != DUCK_OBJECT_MAGIC) {
        return DUCK_RUNTIME_CORRUPT_VALUE;
    }

    current = atomic_load_explicit(&object->references, memory_order_relaxed);
    for (;;) {
        if (current == 0U) return DUCK_RUNTIME_CORRUPT_VALUE;
        if (current == UINT32_MAX) return DUCK_RUNTIME_REFERENCE_OVERFLOW;
        if (atomic_compare_exchange_weak_explicit(
                &object->references,
                &current,
                current + 1U,
                memory_order_relaxed,
                memory_order_relaxed)) {
            return DUCK_RUNTIME_OK;
        }
    }
}

static void release_object(DuckHeapObject *object) {
    DuckRuntimeAllocator allocator;
    uint32_t previous;

    if (object == NULL || object->magic != DUCK_OBJECT_MAGIC) return;

    previous = atomic_fetch_sub_explicit(
        &object->references,
        1U,
        memory_order_acq_rel
    );
    if (previous != 1U) return;

    allocator = object->allocator;

    if (object->object_kind == DUCK_OBJECT_ARRAY) {
        DuckArray *array = (DuckArray *)object;
        for (size_t i = 0U; i < array->length; ++i) {
            duck_value_drop(&array->items[i]);
        }
        if (array->items != NULL) {
            allocator.deallocate(allocator.context, array->items);
        }
    } else if (object->object_kind == DUCK_OBJECT_ITERATOR) {
        DuckIterator *iterator = (DuckIterator *)object;
        duck_value_drop(&iterator->source);
    }

    object->magic = 0U;
    allocator.deallocate(allocator.context, object);
}

DuckRuntimeStatus duck_runtime_init(
    DuckRuntime *runtime,
    DuckRuntimeAllocator allocator
) {
    if (runtime == NULL || allocator.allocate == NULL ||
        allocator.deallocate == NULL) {
        return DUCK_RUNTIME_INVALID_ARGUMENT;
    }

    runtime->allocator = allocator;
    return DUCK_RUNTIME_OK;
}

DuckValue duck_value_unit(void) {
    DuckValue value = { 0U, DUCK_VALUE_UNIT, 0U };
    return value;
}

DuckValue duck_value_i64(int64_t number) {
    DuckValue value = { (uint64_t)number, DUCK_VALUE_I64, 0U };
    return value;
}

DuckValue duck_value_bool(int boolean) {
    DuckValue value = { boolean != 0 ? 1U : 0U, DUCK_VALUE_BOOL, 0U };
    return value;
}

DuckRuntimeStatus duck_value_as_i64(const DuckValue *value, int64_t *out) {
    if (value == NULL || out == NULL) return DUCK_RUNTIME_INVALID_ARGUMENT;
    if (value->kind != DUCK_VALUE_I64 || value->flags != 0U) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }

    *out = (int64_t)value->payload;
    return DUCK_RUNTIME_OK;
}

DuckRuntimeStatus duck_value_as_bool(const DuckValue *value, int *out) {
    if (value == NULL || out == NULL) return DUCK_RUNTIME_INVALID_ARGUMENT;
    if (value->kind != DUCK_VALUE_BOOL || value->flags != 0U ||
        value->payload > 1U) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }

    *out = value->payload != 0U;
    return DUCK_RUNTIME_OK;
}

DuckRuntimeStatus duck_value_clone(
    const DuckValue *source,
    DuckValue *destination
) {
    DuckHeapObject *object;
    DuckRuntimeStatus status;

    if (source == NULL || destination == NULL) {
        return DUCK_RUNTIME_INVALID_ARGUMENT;
    }
    if (source == destination) return DUCK_RUNTIME_OK;
    if (source->flags != 0U) return DUCK_RUNTIME_CORRUPT_VALUE;

    if (source->kind == DUCK_VALUE_STRING ||
        source->kind == DUCK_VALUE_ARRAY ||
        source->kind == DUCK_VALUE_ITERATOR) {
        object = object_from_value(source);
        if (object == NULL) return DUCK_RUNTIME_CORRUPT_VALUE;
        status = retain_object(object);
        if (status != DUCK_RUNTIME_OK) return status;
    } else if (source->kind != DUCK_VALUE_UNIT &&
               source->kind != DUCK_VALUE_I64 &&
               source->kind != DUCK_VALUE_BOOL) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }

    duck_value_drop(destination);
    *destination = *source;
    return DUCK_RUNTIME_OK;
}

void duck_value_move(DuckValue *source, DuckValue *destination) {
    if (source == NULL || destination == NULL || source == destination) return;

    duck_value_drop(destination);
    *destination = *source;
    *source = duck_value_unit();
}

void duck_value_drop(DuckValue *value) {
    DuckHeapObject *object;

    if (value == NULL) return;

    if (value->kind == DUCK_VALUE_STRING ||
        value->kind == DUCK_VALUE_ARRAY ||
        value->kind == DUCK_VALUE_ITERATOR) {
        object = object_from_value(value);
        if (object != NULL) release_object(object);
    }

    *value = duck_value_unit();
}

DuckRuntimeStatus duck_value_string_new(
    DuckRuntime *runtime,
    const char *bytes,
    size_t length,
    DuckValue *out
) {
    DuckString *string;
    DuckHeapObject *object;
    size_t allocation_size;
    DuckRuntimeStatus status;

    if (runtime == NULL || out == NULL || (bytes == NULL && length != 0U)) {
        return DUCK_RUNTIME_INVALID_ARGUMENT;
    }
    if (length > SIZE_MAX - sizeof(DuckString) - 1U) {
        return DUCK_RUNTIME_SIZE_OVERFLOW;
    }

    allocation_size = sizeof(DuckString) + length + 1U;
    status = allocate_object(
        runtime,
        allocation_size,
        DUCK_OBJECT_STRING,
        &object
    );
    if (status != DUCK_RUNTIME_OK) return status;

    string = (DuckString *)object;
    string->length = length;
    if (length != 0U) memcpy(string->bytes, bytes, length);
    string->bytes[length] = '\0';

    duck_value_drop(out);
    out->payload = (uint64_t)(uintptr_t)string;
    out->kind = DUCK_VALUE_STRING;
    out->flags = 0U;
    return DUCK_RUNTIME_OK;
}

DuckRuntimeStatus duck_value_string_view(
    const DuckValue *value,
    const char **bytes,
    size_t *length
) {
    DuckHeapObject *object;
    DuckString *string;

    if (value == NULL || bytes == NULL || length == NULL) {
        return DUCK_RUNTIME_INVALID_ARGUMENT;
    }
    if (value->kind != DUCK_VALUE_STRING || value->flags != 0U) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }

    object = object_from_value(value);
    if (object == NULL) return DUCK_RUNTIME_CORRUPT_VALUE;

    string = (DuckString *)object;
    *bytes = string->bytes;
    *length = string->length;
    return DUCK_RUNTIME_OK;
}

DuckRuntimeStatus duck_value_array_new(
    DuckRuntime *runtime,
    size_t reserve,
    DuckValue *out
) {
    DuckArray *array;
    DuckHeapObject *object;
    size_t bytes = 0U;
    DuckRuntimeStatus status;

    if (runtime == NULL || out == NULL) return DUCK_RUNTIME_INVALID_ARGUMENT;
    if (reserve > SIZE_MAX / sizeof(DuckValue)) {
        return DUCK_RUNTIME_SIZE_OVERFLOW;
    }
    if (reserve != 0U) bytes = reserve * sizeof(DuckValue);

    status = allocate_object(runtime, sizeof(DuckArray), DUCK_OBJECT_ARRAY, &object);
    if (status != DUCK_RUNTIME_OK) return status;

    array = (DuckArray *)object;
    array->length = 0U;
    array->capacity = 0U;
    array->items = NULL;

    if (reserve != 0U) {
        array->items = runtime->allocator.allocate(
            runtime->allocator.context,
            bytes
        );
        if (array->items == NULL) {
            object->magic = 0U;
            runtime->allocator.deallocate(runtime->allocator.context, object);
            return DUCK_RUNTIME_OUT_OF_MEMORY;
        }
        array->capacity = reserve;
    }

    duck_value_drop(out);
    out->payload = (uint64_t)(uintptr_t)array;
    out->kind = DUCK_VALUE_ARRAY;
    out->flags = 0U;
    return DUCK_RUNTIME_OK;
}

static DuckRuntimeStatus array_reaches(
    const DuckArray *current,
    const DuckArray *target,
    const DuckArray **visited,
    size_t *visited_count
) {
    size_t i;

    if (current == target) return DUCK_RUNTIME_CYCLIC_VALUE;

    for (i = 0U; i < *visited_count; ++i) {
        if (visited[i] == current) return DUCK_RUNTIME_OK;
    }
    if (*visited_count >= DUCK_RUNTIME_MAX_ARRAY_GRAPH) {
        return DUCK_RUNTIME_GRAPH_LIMIT;
    }
    visited[*visited_count] = current;
    ++*visited_count;

    for (i = 0U; i < current->length; ++i) {
        const DuckValue *item = &current->items[i];
        DuckRuntimeStatus status;
        DuckHeapObject *child_object;

        if (item->kind != DUCK_VALUE_ARRAY) continue;
        if (item->flags != 0U) return DUCK_RUNTIME_CORRUPT_VALUE;

        child_object = object_from_value(item);
        if (child_object == NULL) return DUCK_RUNTIME_CORRUPT_VALUE;

        status = array_reaches(
            (const DuckArray *)child_object,
            target,
            visited,
            visited_count
        );
        if (status != DUCK_RUNTIME_OK) return status;
    }

    return DUCK_RUNTIME_OK;
}

DuckRuntimeStatus duck_value_array_push(
    DuckValue *value,
    const DuckValue *item
) {
    DuckHeapObject *object;
    DuckArray *array;
    DuckValue copy = { 0U, DUCK_VALUE_UNIT, 0U };
    DuckRuntimeStatus status;
    size_t new_capacity;
    size_t bytes;
    DuckValue *new_items;

    if (value == NULL || item == NULL) return DUCK_RUNTIME_INVALID_ARGUMENT;
    if (value->kind != DUCK_VALUE_ARRAY || value->flags != 0U) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }
    if (item->kind == DUCK_VALUE_ITERATOR) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }

    object = object_from_value(value);
    if (object == NULL) return DUCK_RUNTIME_CORRUPT_VALUE;
    array = (DuckArray *)object;

    if (item->kind == DUCK_VALUE_ARRAY) {
        const DuckArray *visited[DUCK_RUNTIME_MAX_ARRAY_GRAPH];
        size_t visited_count = 0U;
        DuckHeapObject *item_object;

        if (item->flags != 0U) return DUCK_RUNTIME_CORRUPT_VALUE;
        item_object = object_from_value(item);
        if (item_object == NULL) return DUCK_RUNTIME_CORRUPT_VALUE;

        status = array_reaches(
            (const DuckArray *)item_object,
            array,
            visited,
            &visited_count
        );
        if (status != DUCK_RUNTIME_OK) return status;
    }

    status = duck_value_clone(item, &copy);
    if (status != DUCK_RUNTIME_OK) return status;

    if (array->length == array->capacity) {
        if (array->capacity == 0U) {
            new_capacity = 4U;
        } else {
            if (array->capacity > SIZE_MAX / 2U) {
                duck_value_drop(&copy);
                return DUCK_RUNTIME_SIZE_OVERFLOW;
            }
            new_capacity = array->capacity * 2U;
        }

        if (new_capacity > SIZE_MAX / sizeof(DuckValue)) {
            duck_value_drop(&copy);
            return DUCK_RUNTIME_SIZE_OVERFLOW;
        }
        bytes = new_capacity * sizeof(DuckValue);
        new_items = object->allocator.allocate(object->allocator.context, bytes);
        if (new_items == NULL) {
            duck_value_drop(&copy);
            return DUCK_RUNTIME_OUT_OF_MEMORY;
        }

        if (array->length != 0U) {
            memcpy(new_items, array->items, array->length * sizeof(DuckValue));
        }
        if (array->items != NULL) {
            object->allocator.deallocate(object->allocator.context, array->items);
        }

        array->items = new_items;
        array->capacity = new_capacity;
    }

    array->items[array->length] = copy;
    ++array->length;
    return DUCK_RUNTIME_OK;
}

DuckRuntimeStatus duck_value_array_get(
    const DuckValue *value,
    size_t index,
    DuckValue *out
) {
    DuckHeapObject *object;
    DuckArray *array;

    if (value == NULL || out == NULL) return DUCK_RUNTIME_INVALID_ARGUMENT;
    if (value->kind != DUCK_VALUE_ARRAY || value->flags != 0U) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }

    object = object_from_value(value);
    if (object == NULL) return DUCK_RUNTIME_CORRUPT_VALUE;
    array = (DuckArray *)object;
    if (index >= array->length) return DUCK_RUNTIME_OUT_OF_BOUNDS;

    return duck_value_clone(&array->items[index], out);
}

DuckRuntimeStatus duck_value_array_length(
    const DuckValue *value,
    size_t *length
) {
    DuckHeapObject *object;

    if (value == NULL || length == NULL) return DUCK_RUNTIME_INVALID_ARGUMENT;
    if (value->kind != DUCK_VALUE_ARRAY || value->flags != 0U) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }

    object = object_from_value(value);
    if (object == NULL) return DUCK_RUNTIME_CORRUPT_VALUE;

    *length = ((DuckArray *)object)->length;
    return DUCK_RUNTIME_OK;
}

DuckRuntimeStatus duck_value_iterator_new(
    DuckRuntime *runtime,
    const DuckValue *source,
    DuckValue *out
) {
    DuckHeapObject *object;
    DuckIterator *iterator;
    DuckRuntimeStatus status;

    if (runtime == NULL || source == NULL || out == NULL) {
        return DUCK_RUNTIME_INVALID_ARGUMENT;
    }
    if (source->kind != DUCK_VALUE_ARRAY || source->flags != 0U) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }

    status = allocate_object(
        runtime,
        sizeof(DuckIterator),
        DUCK_OBJECT_ITERATOR,
        &object
    );
    if (status != DUCK_RUNTIME_OK) return status;

    iterator = (DuckIterator *)object;
    iterator->source = duck_value_unit();
    iterator->index = 0U;

    status = duck_value_clone(source, &iterator->source);
    if (status != DUCK_RUNTIME_OK) {
        object->magic = 0U;
        runtime->allocator.deallocate(runtime->allocator.context, object);
        return status;
    }

    duck_value_drop(out);
    out->payload = (uint64_t)(uintptr_t)iterator;
    out->kind = DUCK_VALUE_ITERATOR;
    out->flags = 0U;
    return DUCK_RUNTIME_OK;
}

DuckRuntimeStatus duck_value_iterator_next(
    DuckValue *value,
    DuckValue *out,
    int *has_value
) {
    DuckHeapObject *object;
    DuckIterator *iterator;
    DuckHeapObject *source_object;
    DuckArray *array;
    DuckRuntimeStatus status;

    if (value == NULL || out == NULL || has_value == NULL || value == out) {
        return DUCK_RUNTIME_INVALID_ARGUMENT;
    }
    if (value->kind != DUCK_VALUE_ITERATOR || value->flags != 0U) {
        return DUCK_RUNTIME_TYPE_MISMATCH;
    }

    object = object_from_value(value);
    if (object == NULL) return DUCK_RUNTIME_CORRUPT_VALUE;
    iterator = (DuckIterator *)object;

    source_object = object_from_value(&iterator->source);
    if (source_object == NULL ||
        iterator->source.kind != DUCK_VALUE_ARRAY) {
        return DUCK_RUNTIME_CORRUPT_VALUE;
    }
    array = (DuckArray *)source_object;

    if (iterator->index >= array->length) {
        duck_value_drop(out);
        *has_value = 0;
        return DUCK_RUNTIME_OK;
    }

    status = duck_value_clone(&array->items[iterator->index], out);
    if (status != DUCK_RUNTIME_OK) return status;

    ++iterator->index;
    *has_value = 1;
    return DUCK_RUNTIME_OK;
}
