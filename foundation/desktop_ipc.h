#ifndef DUCKOS_DESKTOP_IPC_H
#define DUCKOS_DESKTOP_IPC_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define DUCKOS_DESKTOP_IPC_MAX_QUEUE_SLOTS 8U
#define DUCKOS_DESKTOP_IPC_MAX_FRAME_BYTES (40U + 64U * 1024U)
typedef struct { uint64_t task_id; uint64_t generation; } duckos_desktop_ipc_principal;
typedef struct {
    uint8_t *storage;
    uint32_t storage_capacity;
    uint32_t frame_size;
    uint64_t sender_task_id;
    uint64_t sender_generation;
    uint64_t receiver_task_id;
    uint64_t receiver_generation;
    uint64_t sequence;
    uint64_t request_id;
    uint16_t operation;
    uint16_t reserved;
} duckos_desktop_ipc_slot;
typedef struct {
    duckos_desktop_ipc_slot *slots;
    uint32_t capacity, head, tail, count;
} duckos_desktop_ipc_queue;
typedef struct {
    uint64_t endpoint_id;
    duckos_desktop_ipc_principal owner, peer;
    duckos_desktop_ipc_queue outbound[2];
    uint64_t last_sequence[2];
    uint32_t active;
} duckos_desktop_ipc_endpoint;
typedef enum {
    DUCKOS_DESKTOP_IPC_OK = 0,
    DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT = 1,
    DUCKOS_DESKTOP_IPC_INVALID_CAPACITY = 2,
    DUCKOS_DESKTOP_IPC_CLOSED = 3,
    DUCKOS_DESKTOP_IPC_IDENTITY_MISMATCH = 4,
    DUCKOS_DESKTOP_IPC_QUEUE_FULL = 5,
    DUCKOS_DESKTOP_IPC_QUEUE_EMPTY = 6,
    DUCKOS_DESKTOP_IPC_BUFFER_TOO_SMALL = 7,
    DUCKOS_DESKTOP_IPC_MALFORMED_FRAME = 8,
    DUCKOS_DESKTOP_IPC_UNKNOWN_OPERATION = 9,
    DUCKOS_DESKTOP_IPC_NOT_DESKTOP_OPERATION = 10,
    DUCKOS_DESKTOP_IPC_SEQUENCE_MISMATCH = 11,
    DUCKOS_DESKTOP_IPC_SEQUENCE_EXHAUSTED = 12,
    DUCKOS_DESKTOP_IPC_INTERNAL_ERROR = 13
} duckos_desktop_ipc_status;
typedef struct {
    uint64_t sender_task_id, sender_generation;
    uint64_t receiver_task_id, receiver_generation;
    uint64_t sequence, request_id;
    uint16_t operation;
} duckos_desktop_ipc_metadata;
/* Internal-only API. Slot storage and principals must come from kernel-owned
   service/task state, never from a user frame. Callers serialize access. */
duckos_desktop_ipc_status duckos_desktop_ipc_endpoint_init(
    duckos_desktop_ipc_endpoint *endpoint, uint64_t endpoint_id,
    duckos_desktop_ipc_principal owner, duckos_desktop_ipc_principal peer,
    duckos_desktop_ipc_slot *owner_to_peer_slots, uint32_t owner_to_peer_capacity,
    duckos_desktop_ipc_slot *peer_to_owner_slots, uint32_t peer_to_owner_capacity);
duckos_desktop_ipc_status duckos_desktop_ipc_send(
    duckos_desktop_ipc_endpoint *endpoint,
    const duckos_desktop_ipc_principal *caller,
    const void *frame, size_t frame_size);
duckos_desktop_ipc_status duckos_desktop_ipc_receive(
    duckos_desktop_ipc_endpoint *endpoint,
    const duckos_desktop_ipc_principal *caller,
    void *frame, size_t frame_capacity, size_t *frame_size,
    duckos_desktop_ipc_metadata *metadata);
duckos_desktop_ipc_status duckos_desktop_ipc_endpoint_close(
    duckos_desktop_ipc_endpoint *endpoint,
    const duckos_desktop_ipc_principal *caller);
const char *duckos_desktop_ipc_status_name(duckos_desktop_ipc_status status);
#ifdef __cplusplus
}
#endif
#endif
