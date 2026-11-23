#include "duckos/reaper_host_v1.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <string.h>

typedef struct {
    uint8_t output[128];
    uint64_t output_length;
    uint8_t file[128];
    uint64_t file_length;
    uint64_t position;
    int opened;
} MockKernel;

static int64_t mock_syscall(void *context, uint64_t number,
                            uint64_t a0, uint64_t a1, uint64_t a2,
                            uint64_t a3, uint64_t a4, uint64_t a5) {
    (void)a3; (void)a4; (void)a5;
    MockKernel *kernel = (MockKernel *)context;
    if (number == DUCKOS_SYS_WRITE) {
        if (a0 != 1u && (a0 != 7u || !kernel->opened)) return -1;
        uint8_t *target = a0 == 1u ? kernel->output : kernel->file;
        uint64_t *used = a0 == 1u ? &kernel->output_length : &kernel->file_length;
        uint64_t cap = 128u - *used;
        uint64_t count = a2 < cap ? a2 : cap;
        if (count != 0u) memcpy(target + (size_t)*used,
                                (const void *)(uintptr_t)a1, (size_t)count);
        *used += count;
        return (int64_t)count;
    }
    if (number == DUCKOS_SYS_READ) {
        if (a0 != 7u || !kernel->opened) return -1;
        uint64_t remaining = kernel->file_length - kernel->position;
        uint64_t count = remaining < a2 ? remaining : a2;
        if (count != 0u) memcpy((void *)(uintptr_t)a1,
                                kernel->file + (size_t)kernel->position,
                                (size_t)count);
        kernel->position += count;
        return (int64_t)count;
    }
    if (number == DUCKOS_SYS_OPEN) {
        if (a1 != 8u || memcmp((const void *)(uintptr_t)a0, "file.txt", 8u) != 0)
            return -1;
        kernel->opened = 1;
        kernel->position = 0u;
        if (a2 == REAPER_DABI_OPEN_WRITE) kernel->file_length = 0u;
        return 7;
    }
    if (number == DUCKOS_SYS_CLOSE) {
        if (a0 != 7u || !kernel->opened) return -1;
        kernel->opened = 0;
        return 0;
    }
    return -1;
}

int main(void) {
    MockKernel kernel = {0};
    DuckOsSyscallInterfaceV1 syscalls = {
        REAPER_DABI64_VERSION, (uint32_t)sizeof(DuckOsSyscallInterfaceV1),
        &kernel, mock_syscall
    };
    ReaperDabiHostV1 host;
    assert(duckos_reaper_host_v1_init(&syscalls, &host) == REAPER_DABI_OK);

    ReaperDabiRuntime runtime;
    assert(reaper_dabi_runtime_init(&runtime, &host, NULL) == REAPER_DABI_OK);
    ReaperDabiValue message = reaper_dabi_unit();
    ReaperDabiValue path = reaper_dabi_unit();
    ReaperDabiValue fd = reaper_dabi_unit();
    assert(reaper_dabi_string_new(&runtime, (const uint8_t *)"ready", 5u,
                                  &message) == REAPER_DABI_OK);
    assert(reaper_dabi_string_new(&runtime, (const uint8_t *)"file.txt", 8u,
                                  &path) == REAPER_DABI_OK);
    assert(reaper_dabi_open(&runtime, &path, REAPER_DABI_OPEN_WRITE, &fd) == REAPER_DABI_OK);
    uint64_t written = 0u;
    assert(reaper_dabi_file_write(&runtime, &fd, &message, &written) == REAPER_DABI_OK);
    assert(written == 5u);
    assert(reaper_dabi_close(&runtime, &fd) == REAPER_DABI_OK);
    assert(reaper_dabi_emit(&runtime, &message) == REAPER_DABI_OK);
    assert(kernel.output_length == 6u && memcmp(kernel.output, "ready\n", 6u) == 0);

    assert(reaper_dabi_open(&runtime, &path, REAPER_DABI_OPEN_READ, &fd) == REAPER_DABI_OK);
    uint8_t buffer[8] = {0};
    uint64_t read_count = 0u;
    assert(reaper_dabi_read(&runtime, &fd, buffer, sizeof buffer,
                            &read_count) == REAPER_DABI_OK);
    assert(read_count == 5u && memcmp(buffer, "ready", 5u) == 0);
    assert(reaper_dabi_close(&runtime, &fd) == REAPER_DABI_OK);

    reaper_dabi_value_drop(&runtime, &message);
    reaper_dabi_value_drop(&runtime, &path);
    assert(runtime.live_objects == 0u);
    assert(reaper_dabi_runtime_destroy(&runtime) == REAPER_DABI_OK);
    return 0;
}
