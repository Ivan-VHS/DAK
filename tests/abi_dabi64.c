#include "duckos/abi/dabi64.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static void initializes_and_validates_a_zero_argument_call(void) {
    DuckCallFrame frame __attribute__((aligned(16))) = {
        DUCK_DABI64_MAGIC, DUCK_DABI64_MAJOR, DUCK_DABI64_MINOR,
        sizeof(DuckCallFrame), 0U, 0U, 0U, 0U, 0U, NULL, NULL
    };
    DuckCallResult result __attribute__((aligned(16)));
    memset(&result, 0, sizeof result);
    assert(duck_dabi64_validate_call(&frame, &result, 0U) == DUCK_STATUS_OK);
    assert(duck_dabi64_validate_i64_arguments(&frame) == DUCK_STATUS_OK);
}

static void validates_aligned_i64_arguments(void) {
    DuckValue arguments[2] __attribute__((aligned(16))) = {
        { 19U, DUCK_VALUE_I64, 0U },
        { 23U, DUCK_VALUE_I64, 0U }
    };
    DuckCallFrame frame __attribute__((aligned(16))) = {
        DUCK_DABI64_MAGIC, DUCK_DABI64_MAJOR, DUCK_DABI64_MINOR,
        sizeof(DuckCallFrame), 2U, 0U, 0U, 0U, 0U, arguments, NULL
    };
    DuckCallResult result __attribute__((aligned(16))) = {{0U, DUCK_VALUE_UNIT, 0U}};

    assert(duck_dabi64_validate_call(&frame, &result, 2U) == DUCK_STATUS_OK);
    assert(duck_dabi64_validate_i64_arguments(&frame) == DUCK_STATUS_OK);
    arguments[1].kind = DUCK_VALUE_UNIT;
    assert(duck_dabi64_validate_i64_arguments(&frame) == DUCK_STATUS_BAD_ARGUMENT_LAYOUT);
}

static void rejects_invalid_headers_and_layouts(void) {
    DuckCallFrame frame __attribute__((aligned(16))) = {
        DUCK_DABI64_MAGIC, DUCK_DABI64_MAJOR, DUCK_DABI64_MINOR,
        sizeof(DuckCallFrame), 0U, 0U, 0U, 0U, 0U, NULL, NULL
    };
    DuckCallResult result __attribute__((aligned(16))) = {{0U, DUCK_VALUE_UNIT, 0U}};

    frame.magic = 0U;
    assert(duck_dabi64_validate_call(&frame, &result, 0U) == DUCK_STATUS_BAD_MAGIC);

    frame.magic = DUCK_DABI64_MAGIC;
    frame.abi_major = 2U;
    assert(duck_dabi64_validate_call(&frame, &result, 0U) == DUCK_STATUS_VERSION_MISMATCH);

    frame.abi_major = DUCK_DABI64_MAJOR;
    frame.byte_size = sizeof(DuckCallFrame) - 1U;
    assert(duck_dabi64_validate_call(&frame, &result, 0U) == DUCK_STATUS_BAD_FRAME_SIZE);

    frame.byte_size = sizeof(DuckCallFrame);
    frame.flags = 1U;
    assert(duck_dabi64_validate_call(&frame, &result, 0U) == DUCK_STATUS_INVALID_FLAGS);

    frame.flags = 0U;
    frame.argument_count = 1U;
    assert(duck_dabi64_validate_call(&frame, &result, 1U) == DUCK_STATUS_INVALID_POINTER);

    frame.argument_count = 0U;
    frame.arguments = (const DuckValue *)(uintptr_t)16U;
    assert(duck_dabi64_validate_call(&frame, &result, 0U) == DUCK_STATUS_BAD_ARGUMENT_LAYOUT);

    assert(duck_dabi64_validate_call(NULL, &result, 0U) == DUCK_STATUS_INVALID_POINTER);
    assert(duck_dabi64_validate_call(&frame, NULL, 0U) == DUCK_STATUS_INVALID_POINTER);
}

static void stores_results_only_through_the_typed_api(void) {
    DuckCallResult result __attribute__((aligned(16))) = {
        { UINT64_C(0x123456789abcdef), DUCK_VALUE_UNIT, 0U }
    };
    int64_t value = 0;

    assert(duck_dabi64_result_write_i64(&result, -42) == DUCK_STATUS_OK);
    assert(result.value.kind == DUCK_VALUE_I64);
    assert(duck_dabi64_result_read_i64(&result, &value) == DUCK_STATUS_OK);
    assert(value == -42);

    result.value.kind = DUCK_VALUE_UNIT;
    assert(duck_dabi64_result_read_i64(&result, &value) == DUCK_STATUS_BAD_ARGUMENT_LAYOUT);
    duck_dabi64_result_reset(&result);
    assert(result.value.payload == 0U);
    assert(result.value.kind == DUCK_VALUE_UNIT);
}

int main(void) {
    initializes_and_validates_a_zero_argument_call();
    validates_aligned_i64_arguments();
    rejects_invalid_headers_and_layouts();
    stores_results_only_through_the_typed_api();
    puts("DuckOS DABI64 ABI tests: 4 groups passed");
    return 0;
}
