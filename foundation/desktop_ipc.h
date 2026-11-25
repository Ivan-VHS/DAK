#ifndef DUCKOS_DESKTOP_IPC_H
#define DUCKOS_DESKTOP_IPC_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define DUCKOS_DESKTOP_IPC_HEADER_SIZE 48u
#define DUCKOS_DESKTOP_IPC_MAX_PAYLOAD 65536u
#define DUCKOS_DESKTOP_EVENT_CAPACITY 64u
#define DUCKOS_DESKTOP_EVENT_MAX_BYTES 256u
#define DUCKOS_DESKTOP_FLAG_ACK_REQUIRED 1u
#define DUCKOS_DESKTOP_FLAG_KNOWN_MASK 1u
typedef enum {
 DUCKOS_DESKTOP_MSG_INVALID=0, DUCKOS_DESKTOP_MSG_HELLO=1,
 DUCKOS_DESKTOP_MSG_CREATE_WINDOW=2, DUCKOS_DESKTOP_MSG_CONFIGURE_WINDOW=3,
 DUCKOS_DESKTOP_MSG_CLOSE_WINDOW=4, DUCKOS_DESKTOP_MSG_FOCUS_WINDOW=5,
 DUCKOS_DESKTOP_MSG_CREATE_SURFACE=6, DUCKOS_DESKTOP_MSG_COMMIT_SURFACE=7,
 DUCKOS_DESKTOP_MSG_INPUT_EVENT=8, DUCKOS_DESKTOP_MSG_SWITCH_WORKSPACE=9,
 DUCKOS_DESKTOP_MSG_POST_NOTIFICATION=10, DUCKOS_DESKTOP_MSG_SET_THEME=11,
 DUCKOS_DESKTOP_MSG_ACK=0x8000, DUCKOS_DESKTOP_MSG_ERROR=0x8001
} duckos_desktop_message_type;
typedef enum {
 DUCKOS_DESKTOP_IPC_OK=0, DUCKOS_DESKTOP_IPC_INVALID_ARGUMENT=-1,
 DUCKOS_DESKTOP_IPC_BAD_MAGIC=-2, DUCKOS_DESKTOP_IPC_UNSUPPORTED_VERSION=-3,
 DUCKOS_DESKTOP_IPC_INVALID_HEADER=-4, DUCKOS_DESKTOP_IPC_INVALID_LENGTH=-5,
 DUCKOS_DESKTOP_IPC_UNKNOWN_MESSAGE=-6, DUCKOS_DESKTOP_IPC_INVALID_SEQUENCE=-7,
 DUCKOS_DESKTOP_IPC_SESSION_MISMATCH=-8, DUCKOS_DESKTOP_IPC_INVALID_OBJECT=-9,
 DUCKOS_DESKTOP_IPC_INVALID_PAYLOAD=-10, DUCKOS_DESKTOP_IPC_BACKPRESSURE=-11,
 DUCKOS_DESKTOP_IPC_EMPTY=-12, DUCKOS_DESKTOP_IPC_BUFFER_TOO_SMALL=-13
} duckos_desktop_ipc_status;
typedef struct {
 uint16_t major, minor, header_size, flags;
 uint32_t type, payload_length;
 uint64_t sequence, session_id;
 uint32_t object_id, object_generation;
 const uint8_t *payload;
} duckos_desktop_message;
/* Expected sequence/session are sourced from authenticated connection state. */
duckos_desktop_ipc_status duckos_desktop_message_decode(
 const uint8_t *wire, size_t wire_size, uint64_t expected_sequence,
 uint64_t expected_session_id, duckos_desktop_message *message);
const char *duckos_desktop_ipc_status_name(duckos_desktop_ipc_status status);
typedef struct {
 uint64_t sequence;
 uint32_t length;
 uint8_t bytes[DUCKOS_DESKTOP_EVENT_MAX_BYTES];
} duckos_desktop_event;
typedef struct {
 uint32_t head, tail, count;
 uint64_t last_sequence;
 duckos_desktop_event events[DUCKOS_DESKTOP_EVENT_CAPACITY];
} duckos_desktop_event_queue;
void duckos_desktop_event_queue_init(duckos_desktop_event_queue *queue);
duckos_desktop_ipc_status duckos_desktop_event_queue_push(
 duckos_desktop_event_queue *queue, uint64_t sequence,
 const uint8_t *bytes, size_t length);
duckos_desktop_ipc_status duckos_desktop_event_queue_pop(
 duckos_desktop_event_queue *queue, uint8_t *destination,
 size_t capacity, size_t *written, uint64_t *sequence);
#ifdef __cplusplus
}
#endif
#endif
