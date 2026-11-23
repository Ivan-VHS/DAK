#include "duckos/runtime/value.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct TestAllocatorState {
    size_t live_allocations;
    size_t allocation_calls;
    size_t fail_on_call;
} TestAllocatorState;

static void *test_allocate(void *context, size_t size) {
    TestAllocatorState *state = context;
    void *memory;

    ++state->allocation_calls;
    if (state->fail_on_call != 0U &&
        state->allocation_calls == state->fail_on_call) {
        return NULL;
    }

    memory = malloc(size);
    if (memory != NULL) ++state->live_allocations;
    return memory;
}

static void test_deallocate(void *context, void *memory) {
    TestAllocatorState *state = context;

    if (memory == NULL) return;
    assert(state->live_allocations != 0U);
    --state->live_allocations;
    free(memory);
}

static DuckRuntime make_runtime(TestAllocatorState *state) {
    DuckRuntime runtime;
    DuckRuntimeAllocator allocator = {
        state,
        test_allocate,
        test_deallocate
    };

    assert(duck_runtime_init(&runtime, allocator) == DUCK_RUNTIME_OK);
    return runtime;
}

static void tagged_scalars_and_clone_are_stable(void) {
    DuckValue number = duck_value_i64(-9223372036854775807LL);
    DuckValue boolean = duck_value_bool(1);
    DuckValue copied = duck_value_unit();
    int64_t number_out = 0;
    int boolean_out = 0;

    assert(duck_value_as_i64(&number, &number_out) == DUCK_RUNTIME_OK);
    assert(number_out == -9223372036854775807LL);
    assert(duck_value_as_bool(&boolean, &boolean_out) == DUCK_RUNTIME_OK);
    assert(boolean_out == 1);
    assert(duck_value_clone(&number, &copied) == DUCK_RUNTIME_OK);
    assert(copied.payload == number.payload);
    assert(copied.kind == DUCK_VALUE_I64);
    assert(duck_value_as_bool(&number, &boolean_out) == DUCK_RUNTIME_TYPE_MISMATCH);

    duck_value_drop(&copied);
    assert(copied.kind == DUCK_VALUE_UNIT);
}

static void strings_preserve_bytes_and_ownership(void) {
    TestAllocatorState state = { 0U, 0U, 0U };
    DuckRuntime runtime = make_runtime(&state);
    const char text[] = { 'd', 'u', 'c', 'k', '\0', 'o', 's' };
    DuckValue string = duck_value_unit();
    DuckValue clone = duck_value_unit();
    DuckValue moved = duck_value_unit();
    const char *view = NULL;
    size_t length = 0U;

    assert(duck_value_string_new(&runtime, text, sizeof text, &string) == DUCK_RUNTIME_OK);
    assert(duck_value_string_view(&string, &view, &length) == DUCK_RUNTIME_OK);
    assert(length == sizeof text);
    assert(memcmp(view, text, sizeof text) == 0);
    assert(view[length] == '\0');

    assert(duck_value_clone(&string, &clone) == DUCK_RUNTIME_OK);
    duck_value_drop(&string);
    assert(duck_value_string_view(&clone, &view, &length) == DUCK_RUNTIME_OK);
    assert(length == sizeof text);

    duck_value_move(&clone, &moved);
    assert(clone.kind == DUCK_VALUE_UNIT);
    assert(duck_value_string_view(&moved, &view, &length) == DUCK_RUNTIME_OK);
    assert(length == sizeof text);

    duck_value_drop(&moved);
    assert(state.live_allocations == 0U);
}

static void arrays_clone_elements_and_reject_cycles(void) {
    TestAllocatorState state = { 0U, 0U, 0U };
    DuckRuntime runtime = make_runtime(&state);
    DuckValue outer = duck_value_unit();
    DuckValue inner = duck_value_unit();
    DuckValue fetched = duck_value_unit();
    DuckValue number = duck_value_i64(41);
    DuckValue boolean = duck_value_bool(1);
    int64_t number_out = 0;
    size_t length = 0U;

    assert(duck_value_array_new(&runtime, 1U, &outer) == DUCK_RUNTIME_OK);
    assert(duck_value_array_new(&runtime, 0U, &inner) == DUCK_RUNTIME_OK);
    assert(duck_value_array_push(&inner, &number) == DUCK_RUNTIME_OK);
    assert(duck_value_array_push(&outer, &inner) == DUCK_RUNTIME_OK);
    assert(duck_value_array_push(&inner, &outer) == DUCK_RUNTIME_CYCLIC_VALUE);
    assert(duck_value_array_push(&outer, &boolean) == DUCK_RUNTIME_OK);

    assert(duck_value_array_length(&outer, &length) == DUCK_RUNTIME_OK);
    assert(length == 2U);
    assert(duck_value_array_get(&outer, 0U, &fetched) == DUCK_RUNTIME_OK);
    assert(duck_value_array_get(&fetched, 0U, &number) == DUCK_RUNTIME_OK);
    assert(duck_value_as_i64(&number, &number_out) == DUCK_RUNTIME_OK);
    assert(number_out == 41);
    assert(duck_value_array_get(&outer, 9U, &number) == DUCK_RUNTIME_OUT_OF_BOUNDS);

    duck_value_drop(&number);
    duck_value_drop(&fetched);
    duck_value_drop(&inner);
    duck_value_drop(&outer);
    assert(state.live_allocations == 0U);
}

static void iterators_follow_a_live_array_view(void) {
    TestAllocatorState state = { 0U, 0U, 0U };
    DuckRuntime runtime = make_runtime(&state);
    DuckValue array = duck_value_unit();
    DuckValue iterator = duck_value_unit();
    DuckValue item = duck_value_unit();
    DuckValue first = duck_value_i64(5);
    DuckValue second = duck_value_i64(8);
    int has_value = 0;
    int64_t number = 0;

    assert(duck_value_array_new(&runtime, 0U, &array) == DUCK_RUNTIME_OK);
    assert(duck_value_array_push(&array, &first) == DUCK_RUNTIME_OK);
    assert(duck_value_iterator_new(&runtime, &array, &iterator) == DUCK_RUNTIME_OK);
    assert(duck_value_iterator_next(&iterator, &item, &has_value) == DUCK_RUNTIME_OK);
    assert(has_value == 1);
    assert(duck_value_as_i64(&item, &number) == DUCK_RUNTIME_OK);
    assert(number == 5);

    assert(duck_value_array_push(&array, &second) == DUCK_RUNTIME_OK);
    duck_value_drop(&item);
    assert(duck_value_iterator_next(&iterator, &item, &has_value) == DUCK_RUNTIME_OK);
    assert(has_value == 1);
    assert(duck_value_as_i64(&item, &number) == DUCK_RUNTIME_OK);
    assert(number == 8);

    duck_value_drop(&item);
    assert(duck_value_iterator_next(&iterator, &item, &has_value) == DUCK_RUNTIME_OK);
    assert(has_value == 0);
    assert(item.kind == DUCK_VALUE_UNIT);

    duck_value_drop(&iterator);
    duck_value_drop(&array);
    assert(state.live_allocations == 0U);
}

static void allocation_failure_leaves_the_array_unchanged(void) {
    TestAllocatorState state = { 0U, 0U, 0U };
    DuckRuntime runtime = make_runtime(&state);
    DuckValue array = duck_value_unit();
    DuckValue number = duck_value_i64(7);
    size_t length = 0U;

    assert(duck_value_array_new(&runtime, 0U, &array) == DUCK_RUNTIME_OK);
    state.fail_on_call = state.allocation_calls + 1U;
    assert(duck_value_array_push(&array, &number) == DUCK_RUNTIME_OUT_OF_MEMORY);
    assert(duck_value_array_length(&array, &length) == DUCK_RUNTIME_OK);
    assert(length == 0U);

    state.fail_on_call = 0U;
    duck_value_drop(&array);
    assert(state.live_allocations == 0U);
}

int main(void) {
    tagged_scalars_and_clone_are_stable();
    strings_preserve_bytes_and_ownership();
    arrays_clone_elements_and_reject_cycles();
    iterators_follow_a_live_array_view();
    allocation_failure_leaves_the_array_unchanged();
    puts("DuckOS runtime value tests: 5 groups passed");
    return 0;
}
