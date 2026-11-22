#ifndef DUCKOS_RUNTIME_H
#define DUCKOS_RUNTIME_H

#include "duckos/abi.h"

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef DuckAbiStatus (*DuckRuntimeTransport)(
    DuckSyscallNumber number,
    const DuckCallFrame *frame,
    DuckCallResult *result,
    void *context
);

typedef struct DuckRuntime {
    DuckRuntimeTransport transport;
    void *context;
} DuckRuntime;

/*
 * Use the real DABI64 syscall instruction on supported x86-64 userspace.
 * Unsupported host/target combinations return NOT_IMPLEMENTED.
 */
void duck_runtime_init_native(DuckRuntime *runtime);

/* Inject a transport for tests, emulators or an early boot monitor. */
void duck_runtime_init_transport(
    DuckRuntime *runtime,
    DuckRuntimeTransport transport,
    void *context
);

DuckAbiStatus duck_runtime_write(
    DuckRuntime *runtime,
    uint64_t handle,
    const void *buffer,
    size_t length,
    size_t *written
);

DuckAbiStatus duck_runtime_read(
    DuckRuntime *runtime,
    uint64_t handle,
    void *buffer,
    size_t capacity,
    size_t *read_count
);

DuckAbiStatus duck_runtime_clock_monotonic(
    DuckRuntime *runtime,
    uint64_t *nanoseconds
);

DuckAbiStatus duck_runtime_memory_map(
    DuckRuntime *runtime,
    void *requested_address,
    size_t length,
    uint64_t flags,
    void **mapped_address
);

DuckAbiStatus duck_runtime_memory_unmap(
    DuckRuntime *runtime,
    void *address,
    size_t length
);

DuckAbiStatus duck_runtime_thread_yield(DuckRuntime *runtime);

DuckAbiStatus duck_runtime_thread_join(
    DuckRuntime *runtime,
    uint64_t thread_handle,
    int64_t *exit_status
);

DuckAbiStatus duck_runtime_capability_query(
    DuckRuntime *runtime,
    uint64_t capability_id,
    int *available
);

/*
 * PROCESS_EXIT is normally non-returning in a real kernel. The function
 * returns only so tests/early monitors can report NOT_IMPLEMENTED.
 */
DuckAbiStatus duck_runtime_process_exit(
    DuckRuntime *runtime,
    int64_t exit_status
);

#ifdef __cplusplus
}
#endif

#endif
