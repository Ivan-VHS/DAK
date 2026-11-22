#include "duckos/abi.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

#if defined(_MSC_VER)
#define TEST_ALIGN16 __declspec(align(16))
#else
#define TEST_ALIGN16 __attribute__((aligned(16)))
#endif

static void valid_frame_is_accepted(void) {
    TEST_ALIGN16 DuckValue arguments[2] = {
        { 40, DUCK_VALUE_I64, 0 }, { 2, DUCK_VALUE_I64, 0 }
    };
    TEST_ALIGN16 DuckCallFrame frame = {
        DUCK_ABI_MAGIC, DUCK_ABI_MAJOR, DUCK_ABI_MINOR,
        sizeof(DuckCallFrame), 2, 0, 0, 0, 0, arguments, NULL
    };
    DuckAbiError error;
    assert(duck_abi_validate_frame(&frame, sizeof frame, &error) == DUCK_STATUS_OK);
    assert(error.status == DUCK_STATUS_OK);
}

static void rejects_wrong_version_and_magic(void) {
    TEST_ALIGN16 DuckCallFrame frame = {
        DUCK_ABI_MAGIC, DUCK_ABI_MAJOR + 1u, 0,
        sizeof(DuckCallFrame), 0, 0, 0, 0, 0, NULL, NULL
    };
    DuckAbiError error;
    assert(duck_abi_validate_frame(&frame, sizeof frame, &error) ==
        DUCK_STATUS_VERSION_MISMATCH);
    frame.abi_major = DUCK_ABI_MAJOR;
    frame.magic = 0;
    assert(duck_abi_validate_frame(&frame, sizeof frame, &error) == DUCK_STATUS_BAD_MAGIC);
}

static void rejects_bad_lengths_and_reserved_fields(void) {
    TEST_ALIGN16 DuckCallFrame frame = {
        DUCK_ABI_MAGIC, DUCK_ABI_MAJOR, DUCK_ABI_MINOR,
        sizeof(DuckCallFrame), 0, 0, 0, 1, 0, NULL, NULL
    };
    DuckAbiError error;
    assert(duck_abi_validate_frame(&frame, sizeof frame, &error) ==
        DUCK_STATUS_INVALID_FLAGS);
    frame.reserved0 = 0;
    frame.byte_size = sizeof(DuckCallFrame) + 1u;
    assert(duck_abi_validate_frame(&frame, sizeof frame, &error) ==
        DUCK_STATUS_BAD_FRAME_SIZE);
    assert(duck_abi_validate_frame(&frame, sizeof frame - 1u, &error) ==
        DUCK_STATUS_BAD_FRAME_SIZE);
}

static void validates_typed_result_writes(void) {
    TEST_ALIGN16 DuckCallResult result = { { 99, DUCK_VALUE_U64, 0 } };
    DuckAbiError error;
    DuckValue value = { 42, DUCK_VALUE_I64, DUCK_VALUE_READ_ONLY };
    assert(duck_abi_result_write(&result, value, &error) == DUCK_STATUS_OK);
    assert(result.value.payload == 42 && result.value.kind == DUCK_VALUE_I64);
    value.flags = DUCK_VALUE_OWNED | DUCK_VALUE_BORROWED;
    assert(duck_abi_result_write(&result, value, &error) == DUCK_STATUS_INVALID_VALUE);
    assert(result.value.payload == 42);
}

static void capture_contract_is_explicit(void) {
    TEST_ALIGN16 DuckValue capture = { 7, DUCK_VALUE_I64, DUCK_VALUE_READ_ONLY };
    TEST_ALIGN16 DuckCallFrame frame = {
        DUCK_ABI_MAGIC, DUCK_ABI_MAJOR, DUCK_ABI_MINOR,
        sizeof(DuckCallFrame), 0, 1, DUCK_CALL_HAS_CAPTURES,
        0, 0, NULL, &capture
    };
    DuckAbiError error;
    assert(duck_abi_validate_frame(&frame, sizeof frame, &error) == DUCK_STATUS_OK);
    frame.flags = 0;
    assert(duck_abi_validate_frame(&frame, sizeof frame, &error) == DUCK_STATUS_INVALID_FLAGS);
}

int main(void) {
    valid_frame_is_accepted();
    rejects_wrong_version_and_magic();
    rejects_bad_lengths_and_reserved_fields();
    validates_typed_result_writes();
    capture_contract_is_explicit();
    puts("DuckOS DABI64 tests: 5 groups passed");
    return 0;
}
