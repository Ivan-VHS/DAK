#include "duckos/abi.h"

#include <stdint.h>

static DuckAbiStatus fail(DuckAbiError *error, DuckAbiStatus status, const char *message) {
    if (error != NULL) {
        error->status = status;
        error->message = message;
    }
    return status;
}

static int aligned_pointer(const void *pointer, uintptr_t alignment) {
    return ((uintptr_t)pointer & (alignment - 1u)) == 0u;
}

DuckAbiStatus duck_abi_validate_frame(
    const DuckCallFrame *frame, size_t readable_bytes, DuckAbiError *error
) {
    if (error != NULL) {
        error->status = DUCK_STATUS_OK;
        error->message = "";
    }
    if (frame == NULL)
        return fail(error, DUCK_STATUS_INVALID_POINTER, "call frame is null");
    if (!aligned_pointer(frame, DUCK_ABI_FRAME_ALIGNMENT))
        return fail(error, DUCK_STATUS_BAD_ALIGNMENT, "call frame must be 16-byte aligned");
    if (readable_bytes < sizeof *frame)
        return fail(error, DUCK_STATUS_BAD_FRAME_SIZE, "readable region is smaller than the ABI frame");
    if (frame->magic != DUCK_ABI_MAGIC)
        return fail(error, DUCK_STATUS_BAD_MAGIC, "call frame magic does not identify DABI");
    if (frame->abi_major != DUCK_ABI_MAJOR || frame->abi_minor > DUCK_ABI_MINOR)
        return fail(error, DUCK_STATUS_VERSION_MISMATCH, "call frame ABI version is not supported");
    if (frame->byte_size < sizeof *frame || frame->byte_size > readable_bytes)
        return fail(error, DUCK_STATUS_BAD_FRAME_SIZE, "call frame byte_size is outside the readable region");
    if (frame->argument_count > DUCK_ABI_MAX_ARGUMENTS ||
        frame->capture_count > DUCK_ABI_MAX_ARGUMENTS)
        return fail(error, DUCK_STATUS_TOO_MANY_ARGUMENTS, "call frame exceeds the argument or capture limit");
    if ((frame->flags & ~(DUCK_CALL_HAS_CAPTURES | DUCK_CALL_NO_ALLOC)) != 0u)
        return fail(error, DUCK_STATUS_INVALID_FLAGS, "call frame contains unknown flags");
    if (frame->reserved0 != 0u || frame->reserved1 != 0u)
        return fail(error, DUCK_STATUS_INVALID_FLAGS, "reserved call frame fields must be zero");
    if ((frame->argument_count == 0u) != (frame->arguments == NULL))
        return fail(error, DUCK_STATUS_INVALID_POINTER, "argument pointer does not match argument_count");
    if ((frame->capture_count == 0u) != (frame->captures == NULL))
        return fail(error, DUCK_STATUS_INVALID_POINTER, "capture pointer does not match capture_count");
    if (frame->argument_count != 0u &&
        !aligned_pointer(frame->arguments, DUCK_ABI_VALUE_ALIGNMENT))
        return fail(error, DUCK_STATUS_BAD_ALIGNMENT, "argument array must be 16-byte aligned");
    if (frame->capture_count != 0u &&
        !aligned_pointer(frame->captures, DUCK_ABI_VALUE_ALIGNMENT))
        return fail(error, DUCK_STATUS_BAD_ALIGNMENT, "capture array must be 16-byte aligned");
    if (((frame->flags & DUCK_CALL_HAS_CAPTURES) != 0u) !=
        (frame->capture_count != 0u))
        return fail(error, DUCK_STATUS_INVALID_FLAGS, "capture flag and capture_count disagree");
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_abi_validate_result(
    const DuckCallResult *result, DuckAbiError *error
) {
    if (error != NULL) {
        error->status = DUCK_STATUS_OK;
        error->message = "";
    }
    if (result == NULL)
        return fail(error, DUCK_STATUS_INVALID_POINTER, "result pointer is null");
    if (!aligned_pointer(result, DUCK_ABI_VALUE_ALIGNMENT))
        return fail(error, DUCK_STATUS_BAD_ALIGNMENT, "result slot must be 16-byte aligned");
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_abi_result_write(
    DuckCallResult *result, DuckValue value, DuckAbiError *error
) {
    DuckAbiStatus status = duck_abi_validate_result(result, error);
    if (status != DUCK_STATUS_OK) return status;
    if (value.kind > DUCK_VALUE_ERROR)
        return fail(error, DUCK_STATUS_INVALID_VALUE, "result contains an unknown value kind");
    if ((value.flags & ~(DUCK_VALUE_BORROWED | DUCK_VALUE_OWNED | DUCK_VALUE_READ_ONLY)) != 0u)
        return fail(error, DUCK_STATUS_INVALID_VALUE, "result contains unknown value flags");
    if ((value.flags & DUCK_VALUE_BORROWED) != 0u &&
        (value.flags & DUCK_VALUE_OWNED) != 0u)
        return fail(error, DUCK_STATUS_INVALID_VALUE, "a value cannot be both owned and borrowed");
    result->value = value;
    return DUCK_STATUS_OK;
}

const char *duck_abi_status_name(DuckAbiStatus status) {
    switch (status) {
    case DUCK_STATUS_OK: return "ok";
    case DUCK_STATUS_INVALID_POINTER: return "invalid-pointer";
    case DUCK_STATUS_BAD_MAGIC: return "bad-magic";
    case DUCK_STATUS_VERSION_MISMATCH: return "version-mismatch";
    case DUCK_STATUS_BAD_FRAME_SIZE: return "bad-frame-size";
    case DUCK_STATUS_BAD_ALIGNMENT: return "bad-alignment";
    case DUCK_STATUS_TOO_MANY_ARGUMENTS: return "too-many-arguments";
    case DUCK_STATUS_INVALID_FLAGS: return "invalid-flags";
    case DUCK_STATUS_INVALID_VALUE: return "invalid-value";
    case DUCK_STATUS_NOT_IMPLEMENTED: return "not-implemented";
    case DUCK_STATUS_ACCESS_DENIED: return "access-denied";
    case DUCK_STATUS_OUT_OF_MEMORY: return "out-of-memory";
    case DUCK_STATUS_IO_ERROR: return "io-error";
    case DUCK_STATUS_NOT_FOUND: return "not-found";
    case DUCK_STATUS_CANCELLED: return "cancelled";
    case DUCK_STATUS_INTERNAL_ERROR: return "internal-error";
    default: return "unknown-status";
    }
}
