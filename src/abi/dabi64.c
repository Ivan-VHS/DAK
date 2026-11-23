#include "duckos/abi/dabi64.h"

#include <stdint.h>

static int is_aligned(const void *pointer, uintptr_t alignment) {
    return ((uintptr_t)pointer & (alignment - 1U)) == 0U;
}

DuckAbiStatus duck_dabi64_validate_call(
    const DuckCallFrame *frame,
    const DuckCallResult *result,
    uint32_t expected_argument_count
) {
    if (frame == NULL || result == NULL) return DUCK_STATUS_INVALID_POINTER;
    if (!is_aligned(frame, DUCK_DABI64_REQUIRED_ALIGNMENT) ||
        !is_aligned(result, DUCK_DABI64_REQUIRED_ALIGNMENT)) {
        return DUCK_STATUS_BAD_ALIGNMENT;
    }
    if (frame->magic != DUCK_DABI64_MAGIC) return DUCK_STATUS_BAD_MAGIC;
    if (frame->abi_major != DUCK_DABI64_MAJOR ||
        frame->abi_minor != DUCK_DABI64_MINOR) {
        return DUCK_STATUS_VERSION_MISMATCH;
    }
    if (frame->byte_size < sizeof(DuckCallFrame)) return DUCK_STATUS_BAD_FRAME_SIZE;
    if (frame->flags != 0U || frame->reserved0 != 0U || frame->reserved1 != 0U) {
        return DUCK_STATUS_INVALID_FLAGS;
    }
    if (frame->argument_count != expected_argument_count ||
        frame->argument_count > DUCK_DABI64_MAX_ARGUMENTS ||
        frame->capture_count != 0U || frame->captures != NULL) {
        return DUCK_STATUS_BAD_ARGUMENT_LAYOUT;
    }
    if (frame->argument_count == 0U) {
        if (frame->arguments != NULL) return DUCK_STATUS_BAD_ARGUMENT_LAYOUT;
    } else if (frame->arguments == NULL) {
        return DUCK_STATUS_INVALID_POINTER;
    } else if (!is_aligned(frame->arguments, DUCK_DABI64_REQUIRED_ALIGNMENT)) {
        return DUCK_STATUS_BAD_ALIGNMENT;
    }
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_dabi64_validate_i64_arguments(const DuckCallFrame *frame) {
    if (frame == NULL) return DUCK_STATUS_INVALID_POINTER;
    if (frame->argument_count > DUCK_DABI64_MAX_ARGUMENTS ||
        (frame->argument_count != 0U && frame->arguments == NULL)) {
        return DUCK_STATUS_BAD_ARGUMENT_LAYOUT;
    }
    if (frame->argument_count != 0U &&
        !is_aligned(frame->arguments, DUCK_DABI64_REQUIRED_ALIGNMENT)) {
        return DUCK_STATUS_BAD_ALIGNMENT;
    }
    for (uint32_t i = 0U; i < frame->argument_count; ++i) {
        if (frame->arguments[i].kind != DUCK_VALUE_I64 ||
            frame->arguments[i].flags != 0U) {
            return DUCK_STATUS_BAD_ARGUMENT_LAYOUT;
        }
    }
    return DUCK_STATUS_OK;
}

void duck_dabi64_result_reset(DuckCallResult *result) {
    if (result == NULL || !is_aligned(result, DUCK_DABI64_REQUIRED_ALIGNMENT)) return;
    result->value.payload = 0U;
    result->value.kind = DUCK_VALUE_UNIT;
    result->value.flags = 0U;
}

DuckAbiStatus duck_dabi64_result_write_i64(DuckCallResult *result, int64_t value) {
    if (result == NULL) return DUCK_STATUS_INVALID_POINTER;
    if (!is_aligned(result, DUCK_DABI64_REQUIRED_ALIGNMENT)) return DUCK_STATUS_BAD_ALIGNMENT;
    result->value.payload = (uint64_t)value;
    result->value.kind = DUCK_VALUE_I64;
    result->value.flags = 0U;
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_dabi64_result_read_i64(
    const DuckCallResult *result,
    int64_t *value
) {
    if (result == NULL || value == NULL) return DUCK_STATUS_INVALID_POINTER;
    if (!is_aligned(result, DUCK_DABI64_REQUIRED_ALIGNMENT)) return DUCK_STATUS_BAD_ALIGNMENT;
    if (result->value.kind != DUCK_VALUE_I64 || result->value.flags != 0U) {
        return DUCK_STATUS_BAD_ARGUMENT_LAYOUT;
    }
    *value = (int64_t)result->value.payload;
    return DUCK_STATUS_OK;
}
