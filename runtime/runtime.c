#include "duckos/runtime.h"

#include <limits.h>
#include <stdint.h>
#include <string.h>

#if defined(__x86_64__) && !defined(_WIN32)
static DuckAbiStatus native_transport(
    DuckSyscallNumber number,
    const DuckCallFrame *frame,
    DuckCallResult *result,
    void *context
) {
    (void)context;
    register uint64_t status __asm__("rax") = (uint64_t)number;
    register const DuckCallFrame *frame_register __asm__("rdi") = frame;
    register DuckCallResult *result_register __asm__("rsi") = result;

    __asm__ volatile(
        "syscall"
        : "+a"(status)
        : "D"(frame_register), "S"(result_register)
        : "rcx", "r11", "memory"
    );
    return (DuckAbiStatus)status;
}
#else
static DuckAbiStatus native_transport(
    DuckSyscallNumber number,
    const DuckCallFrame *frame,
    DuckCallResult *result,
    void *context
) {
    (void)number;
    (void)frame;
    (void)result;
    (void)context;
    return DUCK_STATUS_NOT_IMPLEMENTED;
}
#endif

void duck_runtime_init_native(DuckRuntime *runtime) {
    if (runtime == NULL) return;
    runtime->transport = native_transport;
    runtime->context = NULL;
}

void duck_runtime_init_transport(
    DuckRuntime *runtime,
    DuckRuntimeTransport transport,
    void *context
) {
    if (runtime == NULL) return;
    runtime->transport = transport;
    runtime->context = context;
}

static DuckValue unsigned_value(uint64_t value) {
    return (DuckValue){ value, DUCK_VALUE_U64, 0U };
}

static DuckValue borrowed_buffer(const void *buffer, int read_only) {
    uint32_t flags = buffer == NULL ? 0U : DUCK_VALUE_BORROWED;
    if (read_only && buffer != NULL) flags |= DUCK_VALUE_READ_ONLY;
    return (DuckValue){
        (uint64_t)(uintptr_t)buffer,
        DUCK_VALUE_POINTER,
        flags
    };
}

static DuckAbiStatus runtime_call(
    DuckRuntime *runtime,
    DuckSyscallNumber number,
    const DuckValue *arguments,
    size_t argument_count,
    DuckCallResult *result
) {
    if (runtime == NULL || runtime->transport == NULL || result == NULL)
        return DUCK_STATUS_INVALID_POINTER;
    if (argument_count > UINT32_MAX ||
        (argument_count != 0U && arguments == NULL))
        return DUCK_STATUS_BAD_ARGUMENT_LAYOUT;

    DuckCallFrame frame __attribute__((aligned(16)));
    memset(&frame, 0, sizeof frame);
    frame.magic = DUCK_ABI_MAGIC;
    frame.abi_major = DUCK_ABI_MAJOR;
    frame.abi_minor = DUCK_ABI_MINOR;
    frame.byte_size = (uint32_t)sizeof frame;
    frame.argument_count = (uint32_t)argument_count;
    frame.arguments = arguments;

    DuckCallResult local_result __attribute__((aligned(16)));
    memset(&local_result, 0, sizeof local_result);
    local_result.value.kind = DUCK_VALUE_UNIT;

    DuckAbiError error;
    DuckAbiStatus status = duck_abi_validate_frame(
        &frame, sizeof frame, &error
    );
    if (status != DUCK_STATUS_OK) return status;

    status = runtime->transport(number, &frame, &local_result, runtime->context);
    if (status != DUCK_STATUS_OK) return status;

    status = duck_abi_validate_result(&local_result, &error);
    if (status != DUCK_STATUS_OK) return status;
    if ((local_result.value.flags & ~(DUCK_VALUE_BORROWED |
            DUCK_VALUE_OWNED | DUCK_VALUE_READ_ONLY)) != 0U ||
        ((local_result.value.flags & DUCK_VALUE_BORROWED) != 0U &&
         (local_result.value.flags & DUCK_VALUE_OWNED) != 0U)) {
        return DUCK_STATUS_INVALID_VALUE;
    }

    *result = local_result;
    return DUCK_STATUS_OK;
}

static DuckAbiStatus require_result_kind(
    const DuckCallResult *result,
    DuckValueKind expected
) {
    if (result->value.kind != (uint32_t)expected)
        return DUCK_STATUS_INVALID_VALUE;
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_runtime_write(
    DuckRuntime *runtime,
    uint64_t handle,
    const void *buffer,
    size_t length,
    size_t *written
) {
    if (written == NULL || (length != 0U && buffer == NULL))
        return DUCK_STATUS_INVALID_POINTER;

    DuckValue arguments[3] __attribute__((aligned(16))) = {
        unsigned_value(handle),
        borrowed_buffer(buffer, 1),
        unsigned_value((uint64_t)length)
    };
    DuckCallResult result __attribute__((aligned(16)));
    DuckAbiStatus status = runtime_call(
        runtime, DUCK_SYS_IO_WRITE, arguments, 3U, &result
    );
    if (status != DUCK_STATUS_OK) return status;
    status = require_result_kind(&result, DUCK_VALUE_U64);
    if (status != DUCK_STATUS_OK) return status;
    if (result.value.payload > SIZE_MAX) return DUCK_STATUS_INVALID_VALUE;

    *written = (size_t)result.value.payload;
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_runtime_read(
    DuckRuntime *runtime,
    uint64_t handle,
    void *buffer,
    size_t capacity,
    size_t *read_count
) {
    if (read_count == NULL || (capacity != 0U && buffer == NULL))
        return DUCK_STATUS_INVALID_POINTER;

    DuckValue arguments[3] __attribute__((aligned(16))) = {
        unsigned_value(handle),
        borrowed_buffer(buffer, 0),
        unsigned_value((uint64_t)capacity)
    };
    DuckCallResult result __attribute__((aligned(16)));
    DuckAbiStatus status = runtime_call(
        runtime, DUCK_SYS_IO_READ, arguments, 3U, &result
    );
    if (status != DUCK_STATUS_OK) return status;
    status = require_result_kind(&result, DUCK_VALUE_U64);
    if (status != DUCK_STATUS_OK) return status;
    if (result.value.payload > capacity || result.value.payload > SIZE_MAX)
        return DUCK_STATUS_INVALID_VALUE;

    *read_count = (size_t)result.value.payload;
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_runtime_clock_monotonic(
    DuckRuntime *runtime,
    uint64_t *nanoseconds
) {
    if (nanoseconds == NULL) return DUCK_STATUS_INVALID_POINTER;
    DuckCallResult result __attribute__((aligned(16)));
    DuckAbiStatus status = runtime_call(
        runtime, DUCK_SYS_CLOCK_MONOTONIC, NULL, 0U, &result
    );
    if (status != DUCK_STATUS_OK) return status;
    status = require_result_kind(&result, DUCK_VALUE_U64);
    if (status != DUCK_STATUS_OK) return status;
    *nanoseconds = result.value.payload;
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_runtime_memory_map(
    DuckRuntime *runtime,
    void *requested_address,
    size_t length,
    uint64_t flags,
    void **mapped_address
) {
    if (mapped_address == NULL || length == 0U)
        return DUCK_STATUS_INVALID_POINTER;

    DuckValue arguments[3] __attribute__((aligned(16))) = {
        {
            (uint64_t)(uintptr_t)requested_address,
            DUCK_VALUE_POINTER,
            requested_address == NULL ? 0U : DUCK_VALUE_BORROWED
        },
        unsigned_value((uint64_t)length),
        unsigned_value(flags)
    };
    DuckCallResult result __attribute__((aligned(16)));
    DuckAbiStatus status = runtime_call(
        runtime, DUCK_SYS_MEMORY_MAP, arguments, 3U, &result
    );
    if (status != DUCK_STATUS_OK) return status;
    status = require_result_kind(&result, DUCK_VALUE_POINTER);
    if (status != DUCK_STATUS_OK) return status;
    if (result.value.payload == 0U) return DUCK_STATUS_INVALID_VALUE;

    *mapped_address = (void *)(uintptr_t)result.value.payload;
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_runtime_memory_unmap(
    DuckRuntime *runtime,
    void *address,
    size_t length
) {
    if (address == NULL || length == 0U)
        return DUCK_STATUS_INVALID_POINTER;
    DuckValue arguments[2] __attribute__((aligned(16))) = {
        { (uint64_t)(uintptr_t)address, DUCK_VALUE_POINTER, DUCK_VALUE_BORROWED },
        unsigned_value((uint64_t)length)
    };
    DuckCallResult result __attribute__((aligned(16)));
    DuckAbiStatus status = runtime_call(
        runtime, DUCK_SYS_MEMORY_UNMAP, arguments, 2U, &result
    );
    if (status != DUCK_STATUS_OK) return status;
    return require_result_kind(&result, DUCK_VALUE_UNIT);
}

DuckAbiStatus duck_runtime_thread_yield(DuckRuntime *runtime) {
    DuckCallResult result __attribute__((aligned(16)));
    DuckAbiStatus status = runtime_call(
        runtime, DUCK_SYS_THREAD_YIELD, NULL, 0U, &result
    );
    if (status != DUCK_STATUS_OK) return status;
    return require_result_kind(&result, DUCK_VALUE_UNIT);
}

DuckAbiStatus duck_runtime_thread_join(
    DuckRuntime *runtime,
    uint64_t thread_handle,
    int64_t *exit_status
) {
    if (exit_status == NULL) return DUCK_STATUS_INVALID_POINTER;
    DuckValue arguments[1] __attribute__((aligned(16))) = {
        unsigned_value(thread_handle)
    };
    DuckCallResult result __attribute__((aligned(16)));
    DuckAbiStatus status = runtime_call(
        runtime, DUCK_SYS_THREAD_JOIN, arguments, 1U, &result
    );
    if (status != DUCK_STATUS_OK) return status;
    status = require_result_kind(&result, DUCK_VALUE_I64);
    if (status != DUCK_STATUS_OK) return status;
    *exit_status = (int64_t)result.value.payload;
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_runtime_capability_query(
    DuckRuntime *runtime,
    uint64_t capability_id,
    int *available
) {
    if (available == NULL) return DUCK_STATUS_INVALID_POINTER;
    DuckValue arguments[1] __attribute__((aligned(16))) = {
        unsigned_value(capability_id)
    };
    DuckCallResult result __attribute__((aligned(16)));
    DuckAbiStatus status = runtime_call(
        runtime, DUCK_SYS_CAPABILITY_QUERY, arguments, 1U, &result
    );
    if (status != DUCK_STATUS_OK) return status;
    status = require_result_kind(&result, DUCK_VALUE_BOOL);
    if (status != DUCK_STATUS_OK) return status;
    if (result.value.payload > 1U) return DUCK_STATUS_INVALID_VALUE;
    *available = result.value.payload != 0U;
    return DUCK_STATUS_OK;
}

DuckAbiStatus duck_runtime_process_exit(
    DuckRuntime *runtime,
    int64_t exit_status
) {
    DuckValue arguments[1] __attribute__((aligned(16))) = {
        { (uint64_t)exit_status, DUCK_VALUE_I64, 0U }
    };
    DuckCallResult result __attribute__((aligned(16)));
    DuckAbiStatus status = runtime_call(
        runtime, DUCK_SYS_PROCESS_EXIT, arguments, 1U, &result
    );
    if (status != DUCK_STATUS_OK) return status;
    return require_result_kind(&result, DUCK_VALUE_UNIT);
}
