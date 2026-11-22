#include "duckos/runtime.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct FakeKernel {
    DuckSyscallNumber expected_number;
    uint64_t expected_handle;
    const void *expected_buffer;
    size_t expected_length;
    uint64_t response_value;
    DuckValueKind response_kind;
    DuckAbiStatus response_status;
    size_t call_count;
} FakeKernel;

static DuckAbiStatus fake_transport(
    DuckSyscallNumber number,
    const DuckCallFrame *frame,
    DuckCallResult *result,
    void *context
) {
    FakeKernel *kernel = context;
    ++kernel->call_count;
    if (number != kernel->expected_number) return DUCK_STATUS_NOT_FOUND;
    if (frame == NULL || frame->magic != DUCK_ABI_MAGIC ||
        frame->abi_major != DUCK_ABI_MAJOR ||
        frame->abi_minor != DUCK_ABI_MINOR ||
        frame->byte_size != sizeof(DuckCallFrame) ||
        frame->capture_count != 0U || frame->flags != 0U ||
        frame->reserved0 != 0U || frame->reserved1 != 0U) {
        return DUCK_STATUS_BAD_FRAME_SIZE;
    }

    if (number == DUCK_SYS_IO_WRITE || number == DUCK_SYS_IO_READ) {
        if (frame->argument_count != 3U || frame->arguments == NULL)
            return DUCK_STATUS_BAD_ARGUMENT_LAYOUT;
        if (frame->arguments[0].payload != kernel->expected_handle ||
            frame->arguments[1].payload != (uint64_t)(uintptr_t)kernel->expected_buffer ||
            frame->arguments[2].payload != kernel->expected_length) {
            return DUCK_STATUS_BAD_ARGUMENT_LAYOUT;
        }
        if (number == DUCK_SYS_IO_WRITE &&
            (frame->arguments[1].flags & DUCK_VALUE_READ_ONLY) == 0U) {
            return DUCK_STATUS_INVALID_VALUE;
        }
        if (number == DUCK_SYS_IO_READ &&
            (frame->arguments[1].flags & DUCK_VALUE_READ_ONLY) != 0U) {
            return DUCK_STATUS_INVALID_VALUE;
        }
    }

    if (number == DUCK_SYS_CLOCK_MONOTONIC && frame->argument_count != 0U)
        return DUCK_STATUS_BAD_ARGUMENT_LAYOUT;

    if (kernel->response_status != DUCK_STATUS_OK)
        return kernel->response_status;

    DuckValue value = {
        kernel->response_value,
        kernel->response_kind,
        0U
    };
    return duck_abi_result_write(result, value, NULL);
}

static void test_runtime_write_frame_and_result(void) {
    const char message[] = "duck";
    FakeKernel kernel = {
        DUCK_SYS_IO_WRITE, 7U, message, sizeof message - 1U,
        sizeof message - 1U, DUCK_VALUE_U64, DUCK_STATUS_OK, 0U
    };
    DuckRuntime runtime;
    duck_runtime_init_transport(&runtime, fake_transport, &kernel);
    size_t written = 999U;

    assert(duck_runtime_write(
        &runtime, 7U, message, sizeof message - 1U, &written
    ) == DUCK_STATUS_OK);
    assert(written == sizeof message - 1U);
    assert(kernel.call_count == 1U);
}

static void test_runtime_read_and_capacity_checks(void) {
    char buffer[16];
    FakeKernel kernel = {
        DUCK_SYS_IO_READ, 2U, buffer, sizeof buffer,
        4U, DUCK_VALUE_U64, DUCK_STATUS_OK, 0U
    };
    DuckRuntime runtime;
    duck_runtime_init_transport(&runtime, fake_transport, &kernel);
    size_t read_count = 999U;

    assert(duck_runtime_read(&runtime, 2U, buffer, sizeof buffer,
        &read_count) == DUCK_STATUS_OK);
    assert(read_count == 4U);

    kernel.response_value = sizeof buffer + 1U;
    read_count = 999U;
    assert(duck_runtime_read(&runtime, 2U, buffer, sizeof buffer,
        &read_count) == DUCK_STATUS_INVALID_VALUE);
    assert(read_count == 999U);
}

static void test_runtime_clock_and_capability(void) {
    FakeKernel kernel = {
        DUCK_SYS_CLOCK_MONOTONIC, 0U, NULL, 0U,
        UINT64_C(123456789), DUCK_VALUE_U64, DUCK_STATUS_OK, 0U
    };
    DuckRuntime runtime;
    duck_runtime_init_transport(&runtime, fake_transport, &kernel);
    uint64_t now = 0U;
    assert(duck_runtime_clock_monotonic(&runtime, &now) == DUCK_STATUS_OK);
    assert(now == UINT64_C(123456789));

    kernel.expected_number = DUCK_SYS_CAPABILITY_QUERY;
    kernel.expected_handle = 5U;
    kernel.expected_length = 0U;
    kernel.response_value = 1U;
    kernel.response_kind = DUCK_VALUE_BOOL;
    int available = 0;
    assert(duck_runtime_capability_query(&runtime, 5U, &available) == DUCK_STATUS_OK);
    assert(available == 1);
}

static void test_runtime_memory_and_thread_wrappers(void) {
    FakeKernel kernel = {
        DUCK_SYS_MEMORY_MAP, 0U, NULL, 0U,
        UINT64_C(0x100000), DUCK_VALUE_POINTER, DUCK_STATUS_OK, 0U
    };
    DuckRuntime runtime;
    duck_runtime_init_transport(&runtime, fake_transport, &kernel);

    void *mapped = NULL;
    assert(duck_runtime_memory_map(&runtime, NULL, 4096U, 3U, &mapped) == DUCK_STATUS_OK);
    assert(mapped == (void *)(uintptr_t)UINT64_C(0x100000));

    kernel.expected_number = DUCK_SYS_MEMORY_UNMAP;
    kernel.response_kind = DUCK_VALUE_UNIT;
    assert(duck_runtime_memory_unmap(&runtime, mapped, 4096U) == DUCK_STATUS_OK);

    kernel.expected_number = DUCK_SYS_THREAD_YIELD;
    assert(duck_runtime_thread_yield(&runtime) == DUCK_STATUS_OK);

    kernel.expected_number = DUCK_SYS_THREAD_JOIN;
    kernel.expected_handle = 42U;
    kernel.response_kind = DUCK_VALUE_I64;
    kernel.response_value = 9U;
    int64_t exit_status = 0;
    assert(duck_runtime_thread_join(&runtime, 42U, &exit_status) == DUCK_STATUS_OK);
    assert(exit_status == 9);
}

static void test_failures_never_overwrite_outputs(void) {
    FakeKernel kernel = {
        DUCK_SYS_CLOCK_MONOTONIC, 0U, NULL, 0U,
        77U, DUCK_VALUE_U64, DUCK_STATUS_ACCESS_DENIED, 0U
    };
    DuckRuntime runtime;
    duck_runtime_init_transport(&runtime, fake_transport, &kernel);
    uint64_t now = 123U;
    assert(duck_runtime_clock_monotonic(&runtime, &now) == DUCK_STATUS_ACCESS_DENIED);
    assert(now == 123U);

    kernel.response_status = DUCK_STATUS_OK;
    kernel.response_kind = DUCK_VALUE_STRING;
    assert(duck_runtime_clock_monotonic(&runtime, &now) == DUCK_STATUS_INVALID_VALUE);
    assert(now == 123U);
}

static void test_native_transport_exists_without_claiming_kernel_support(void) {
    DuckRuntime runtime;
    duck_runtime_init_native(&runtime);
    assert(runtime.transport != NULL);
#if !defined(__x86_64__) || defined(_WIN32)
    assert(runtime.transport(
        DUCK_SYS_CLOCK_MONOTONIC, NULL, NULL, NULL
    ) == DUCK_STATUS_NOT_IMPLEMENTED);
#endif
}

int main(void) {
    test_runtime_write_frame_and_result();
    test_runtime_read_and_capacity_checks();
    test_runtime_clock_and_capability();
    test_runtime_memory_and_thread_wrappers();
    test_failures_never_overwrite_outputs();
    test_native_transport_exists_without_claiming_kernel_support();
    puts("DuckOS runtime syscall wrapper tests: 6 groups passed");
    return 0;
}
