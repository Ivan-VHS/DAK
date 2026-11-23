#ifndef DUCKOS_REAPER_HOST_V1_H
#define DUCKOS_REAPER_HOST_V1_H

#include <stdint.h>
#include "reaper/dabi64.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct {
    uint32_t abi_version;
    uint32_t struct_size;
    void *context;
    int64_t (*invoke)(void *context, uint64_t number,
                      uint64_t arg0, uint64_t arg1, uint64_t arg2,
                      uint64_t arg3, uint64_t arg4, uint64_t arg5);
} DuckOsSyscallInterfaceV1;

enum {
    DUCKOS_SYS_WRITE = 1u,
    DUCKOS_SYS_READ = 2u,
    DUCKOS_SYS_OPEN = 3u,
    DUCKOS_SYS_CLOSE = 4u
};

static inline int32_t duckos_dabi_write(void *context, int64_t fd,
                                        const uint8_t *buffer, uint64_t length,
                                        uint64_t *written) {
    const DuckOsSyscallInterfaceV1 *syscalls = (const DuckOsSyscallInterfaceV1 *)context;
    if (syscalls == NULL || syscalls->invoke == NULL || written == NULL ||
        (length != 0u && buffer == NULL)) return -1;
    int64_t result = syscalls->invoke(syscalls->context, DUCKOS_SYS_WRITE,
        (uint64_t)fd, (uint64_t)(uintptr_t)buffer, length, 0u, 0u, 0u);
    if (result < 0 || (uint64_t)result > length) return -1;
    *written = (uint64_t)result;
    return 0;
}

static inline int32_t duckos_dabi_read(void *context, int64_t fd,
                                       uint8_t *buffer, uint64_t capacity,
                                       uint64_t *read_count) {
    const DuckOsSyscallInterfaceV1 *syscalls = (const DuckOsSyscallInterfaceV1 *)context;
    if (syscalls == NULL || syscalls->invoke == NULL || read_count == NULL ||
        (capacity != 0u && buffer == NULL)) return -1;
    int64_t result = syscalls->invoke(syscalls->context, DUCKOS_SYS_READ,
        (uint64_t)fd, (uint64_t)(uintptr_t)buffer, capacity, 0u, 0u, 0u);
    if (result < 0 || (uint64_t)result > capacity) return -1;
    *read_count = (uint64_t)result;
    return 0;
}

static inline int32_t duckos_dabi_open(void *context, const uint8_t *path,
                                       uint64_t path_length, uint32_t mode,
                                       int64_t *fd_out) {
    const DuckOsSyscallInterfaceV1 *syscalls = (const DuckOsSyscallInterfaceV1 *)context;
    if (syscalls == NULL || syscalls->invoke == NULL || fd_out == NULL ||
        (path_length != 0u && path == NULL)) return -1;
    int64_t result = syscalls->invoke(syscalls->context, DUCKOS_SYS_OPEN,
        (uint64_t)(uintptr_t)path, path_length, (uint64_t)mode, 0u, 0u, 0u);
    if (result < 0) return -1;
    *fd_out = result;
    return 0;
}

static inline int32_t duckos_dabi_close(void *context, int64_t fd) {
    const DuckOsSyscallInterfaceV1 *syscalls = (const DuckOsSyscallInterfaceV1 *)context;
    if (syscalls == NULL || syscalls->invoke == NULL) return -1;
    return syscalls->invoke(syscalls->context, DUCKOS_SYS_CLOSE,
        (uint64_t)fd, 0u, 0u, 0u, 0u, 0u) == 0 ? 0 : -1;
}

static inline ReaperDabiStatus duckos_reaper_host_v1_init(
    const DuckOsSyscallInterfaceV1 *syscalls, ReaperDabiHostV1 *host_out) {
    if (syscalls == NULL || host_out == NULL || syscalls->invoke == NULL)
        return REAPER_DABI_INVALID_ARGUMENT;
    if (syscalls->abi_version != REAPER_DABI64_VERSION ||
        syscalls->struct_size < (uint32_t)sizeof *syscalls)
        return REAPER_DABI_ABI_MISMATCH;
    host_out->abi_version = REAPER_DABI64_VERSION;
    host_out->struct_size = (uint32_t)sizeof *host_out;
    host_out->context = (void *)syscalls;
    host_out->write = duckos_dabi_write;
    host_out->read = duckos_dabi_read;
    host_out->open = duckos_dabi_open;
    host_out->close = duckos_dabi_close;
    return REAPER_DABI_OK;
}

#ifdef __cplusplus
}
#endif

#endif
