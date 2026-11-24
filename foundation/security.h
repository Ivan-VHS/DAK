#ifndef DUCKOS_SECURITY_H
#define DUCKOS_SECURITY_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_SECURITY_ABI_VERSION 1u
#define DUCKOS_SECURITY_EVENT_CAPACITY 128u
#define DUCKOS_SECURITY_CAUSAL_DEPTH 32u
#define DUCKOS_SECURITY_WINDOW_NS 30000000000ull
#define DUCKOS_SECURITY_MESH_WINDOW_MS 300000ull

typedef enum duckos_security_status {
    DUCKOS_SECURITY_OK = 0,
    DUCKOS_SECURITY_INVALID_ARGUMENT = -1,
    DUCKOS_SECURITY_UNSUPPORTED_VERSION = -2,
    DUCKOS_SECURITY_INVALID_EVENT = -3,
    DUCKOS_SECURITY_UNTRUSTED_SOURCE = -4,
    DUCKOS_SECURITY_DUPLICATE_EVENT = -5,
    DUCKOS_SECURITY_OUT_OF_ORDER = -6
} duckos_security_status;

typedef enum duckos_security_event_kind {
    DUCKOS_SECURITY_PROCESS_START = 1,
    DUCKOS_SECURITY_PROCESS_INJECT = 2,
    DUCKOS_SECURITY_FILE_MODIFY = 3,
    DUCKOS_SECURITY_FILE_DELETE = 4,
    DUCKOS_SECURITY_FILE_RENAME = 5,
    DUCKOS_SECURITY_NETWORK_CONNECT = 6,
    DUCKOS_SECURITY_MEMORY_READ = 7,
    DUCKOS_SECURITY_IDENTITY_ACCESS = 8,
    DUCKOS_SECURITY_INTEGRITY_CHANGE = 9,
    DUCKOS_SECURITY_DRIVER_LOAD = 10
} duckos_security_event_kind;

typedef enum duckos_security_trust {
    DUCKOS_SECURITY_TRUST_UNTRUSTED = 0,
    DUCKOS_SECURITY_TRUST_VALIDATED = 1,
    DUCKOS_SECURITY_TRUST_TRUSTED = 2
} duckos_security_trust;

enum duckos_security_event_flags {
    DUCKOS_SECURITY_FLAG_SENSITIVE_TARGET = 1u << 0,
    DUCKOS_SECURITY_FLAG_AUTHORIZED = 1u << 1,
    DUCKOS_SECURITY_FLAG_CREDENTIAL_MATERIAL = 1u << 2,
    DUCKOS_SECURITY_FLAG_PROTECTED_COMPONENT = 1u << 3,
    DUCKOS_SECURITY_FLAG_SIGNATURE_VERIFIED = 1u << 4,
    DUCKOS_SECURITY_FLAG_DESTINATION_MALICIOUS = 1u << 5,
    DUCKOS_SECURITY_FLAG_BEACON_PERIODIC = 1u << 6,
    DUCKOS_SECURITY_FLAG_ENCODED_COMMAND = 1u << 7,
    DUCKOS_SECURITY_FLAG_HIDDEN_WINDOW = 1u << 8,
    DUCKOS_SECURITY_FLAG_USER_WRITABLE_ORIGIN = 1u << 9,
    DUCKOS_SECURITY_FLAG_UNEXPECTED_PARENT = 1u << 10,
    DUCKOS_SECURITY_FLAG_NETWORK_CHILD = 1u << 11,
    DUCKOS_SECURITY_FLAG_ORIGIN_UNTRUSTED = 1u << 12,
    DUCKOS_SECURITY_FLAG_SUSPICIOUS_CHAIN = 1u << 13
};

#define DUCKOS_SECURITY_KNOWN_EVENT_FLAGS ((1u << 14) - 1u)

typedef struct duckos_security_event_v1 {
    uint32_t struct_size;
    uint32_t version;
    uint64_t sequence;
    uint64_t monotonic_ns;
    uint64_t observed_at_ms;
    uint32_t kind;
    uint32_t source_trust;
    uint32_t flags;
    uint16_t entropy_delta_bp;
    uint16_t repeat_count;
    char event_id[64];
    char host_id[64];
    char source_id[64];
    char actor_id[96];
    char object_id[128];
    char parent_event_id[64];
    char indicator[64];
    char image_name[64];
} duckos_security_event_v1;

enum duckos_security_indicator {
    DUCKOS_SECURITY_IND_PROCESS_INJECTION = 1ull << 0,
    DUCKOS_SECURITY_IND_SENSITIVE_MEMORY_READ = 1ull << 1,
    DUCKOS_SECURITY_IND_CREDENTIAL_ACCESS = 1ull << 2,
    DUCKOS_SECURITY_IND_PROTECTED_TAMPERING = 1ull << 3,
    DUCKOS_SECURITY_IND_UNVERIFIED_DRIVER = 1ull << 4,
    DUCKOS_SECURITY_IND_FILE_MUTATION_BURST = 1ull << 5,
    DUCKOS_SECURITY_IND_ENTROPY_CHANGE = 1ull << 6,
    DUCKOS_SECURITY_IND_HIGH_ENTROPY_CHANGE = 1ull << 7,
    DUCKOS_SECURITY_IND_MALICIOUS_DESTINATION = 1ull << 8,
    DUCKOS_SECURITY_IND_PERIODIC_BEACON = 1ull << 9,
    DUCKOS_SECURITY_IND_LOLBIN_CONTEXT = 1ull << 10,
    DUCKOS_SECURITY_IND_UNTRUSTED_ORIGIN = 1ull << 11,
    DUCKOS_SECURITY_IND_SUSPICIOUS_CHAIN = 1ull << 12,
    DUCKOS_SECURITY_IND_CROSS_HOST_CLUSTER = 1ull << 13,
    DUCKOS_SECURITY_IND_MULTI_HOST_CLUSTER = 1ull << 14
};

typedef enum duckos_security_recommendation {
    DUCKOS_SECURITY_ACTION_MONITOR = 0,
    DUCKOS_SECURITY_ACTION_SANDBOX = 1,
    DUCKOS_SECURITY_ACTION_RESTRICT = 2,
    DUCKOS_SECURITY_ACTION_ISOLATE = 3,
    DUCKOS_SECURITY_ACTION_BLOCK = 4
} duckos_security_recommendation;

typedef struct duckos_security_evaluation_v1 {
    uint32_t struct_size;
    uint32_t version;
    uint32_t risk_score;
    uint32_t confidence_milli;
    uint32_t recommendation;
    uint32_t advisory_only;
    uint32_t file_mutations_in_window;
    uint32_t distinct_hosts_in_cluster;
    uint32_t causal_depth;
    uint64_t indicators;
    char event_id[64];
    char causal_root_event_id[64];
} duckos_security_evaluation_v1;

typedef struct duckos_security_engine {
    duckos_security_event_v1 events[DUCKOS_SECURITY_EVENT_CAPACITY];
    size_t next_write;
    size_t count;
} duckos_security_engine;

typedef enum duckos_security_capability {
    DUCKOS_SECURITY_CAP_OBSERVE = 1ull << 0,
    DUCKOS_SECURITY_CAP_SNAPSHOT_CREATE = 1ull << 1,
    DUCKOS_SECURITY_CAP_INTEGRITY_VERIFY = 1ull << 2,
    DUCKOS_SECURITY_CAP_FILE_RESTORE = 1ull << 3,
    DUCKOS_SECURITY_CAP_PROCESS_ISOLATE = 1ull << 4,
    DUCKOS_SECURITY_CAP_PROCESS_TERMINATE = 1ull << 5,
    DUCKOS_SECURITY_CAP_NETWORK_ISOLATE = 1ull << 6,
    DUCKOS_SECURITY_CAP_DRIVER_QUARANTINE = 1ull << 7
} duckos_security_capability;

enum duckos_security_authorization_flags {
    DUCKOS_SECURITY_AUTH_EVIDENCE_FRESH = 1u << 0,
    DUCKOS_SECURITY_AUTH_POLICY_VALID = 1u << 1,
    DUCKOS_SECURITY_AUTH_HUMAN_APPROVED = 1u << 2,
    DUCKOS_SECURITY_AUTH_SNAPSHOT_AUTHENTICATED = 1u << 3,
    DUCKOS_SECURITY_AUTH_CONTENT_VERIFIED = 1u << 4,
    DUCKOS_SECURITY_AUTH_TARGET_AUTHORIZED = 1u << 5
};

typedef enum duckos_security_action {
    DUCKOS_SECURITY_OP_OBSERVE = 1,
    DUCKOS_SECURITY_OP_SNAPSHOT_CREATE = 2,
    DUCKOS_SECURITY_OP_INTEGRITY_VERIFY = 3,
    DUCKOS_SECURITY_OP_FILE_RESTORE = 4,
    DUCKOS_SECURITY_OP_PROCESS_ISOLATE = 5,
    DUCKOS_SECURITY_OP_PROCESS_TERMINATE = 6,
    DUCKOS_SECURITY_OP_NETWORK_ISOLATE = 7,
    DUCKOS_SECURITY_OP_DRIVER_QUARANTINE = 8
} duckos_security_action;

typedef struct duckos_security_authorization_request_v1 {
    uint32_t struct_size;
    uint32_t version;
    uint32_t action;
    uint32_t caller_trust;
    uint32_t flags;
    uint32_t reserved;
    uint64_t granted_capabilities;
} duckos_security_authorization_request_v1;

void duckos_security_engine_init(duckos_security_engine *engine);
duckos_security_status duckos_security_event_validate(const duckos_security_event_v1 *event);
duckos_security_status duckos_security_ingest(
    duckos_security_engine *engine,
    const duckos_security_event_v1 *event,
    duckos_security_evaluation_v1 *evaluation
);

/* Authorization decision only; a native kernel broker must enforce it. */
int duckos_security_authorize(const duckos_security_authorization_request_v1 *request);
const char *duckos_security_status_name(duckos_security_status status);

#ifdef __cplusplus
}
#endif
#endif
