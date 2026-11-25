#ifndef DUCKOS_CAPABILITY_BROKER_H
#define DUCKOS_CAPABILITY_BROKER_H

#include <stddef.h>
#include <stdint.h>

#include "reaper/system.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_CAPABILITY_BROKER_MAX_SLOTS 256U
#define DUCKOS_CAPABILITY_BROKER_DELEGATE (UINT64_C(1) << 63)

typedef struct {
    uint64_t task_id;
    uint64_t generation;
} duckos_capability_principal;

typedef enum {
    DUCKOS_CAPABILITY_SCOPE_GLOBAL = 0,
    DUCKOS_CAPABILITY_SCOPE_OBJECT = 1
} duckos_capability_scope;

typedef enum {
    DUCKOS_CAPABILITY_OK = 0,
    DUCKOS_CAPABILITY_INVALID_ARGUMENT = 1,
    DUCKOS_CAPABILITY_INVALID_CAPACITY = 2,
    DUCKOS_CAPABILITY_DENIED = 3,
    DUCKOS_CAPABILITY_UNKNOWN_OPERATION = 4,
    DUCKOS_CAPABILITY_STALE_TOKEN = 5,
    DUCKOS_CAPABILITY_RESOURCE_MISMATCH = 6,
    DUCKOS_CAPABILITY_NOT_DELEGABLE = 7,
    DUCKOS_CAPABILITY_RIGHTS_ESCALATION = 8,
    DUCKOS_CAPABILITY_TABLE_FULL = 9,
    DUCKOS_CAPABILITY_GENERATION_EXHAUSTED = 10,
    DUCKOS_CAPABILITY_REVOKED = 11
} duckos_capability_status;

typedef struct {
    duckos_capability_principal grantor;
    duckos_capability_principal grantee;
    uint64_t rights;
    uint64_t resource_id;
    uint64_t resource_generation;
    uint64_t parent_token;
    uint32_t generation;
    uint16_t resource_domain;
    uint8_t scope;
    uint8_t active;
} duckos_capability_slot;

typedef struct {
    duckos_capability_principal authority;
    duckos_capability_slot *slots;
    uint32_t capacity;
    uint32_t active_count;
    uint64_t root_ceiling;
} duckos_capability_broker;

/*
 * Broker calls are internal kernel/service operations. The caller principal
 * must be resolved from the current kernel task object, never from an IPC
 * payload or a user-supplied PID. The owning service serializes all calls.
 */
duckos_capability_status duckos_capability_broker_init(
    duckos_capability_broker *broker,
    duckos_capability_slot *slots,
    uint32_t capacity,
    duckos_capability_principal authority,
    uint64_t root_ceiling
);

duckos_capability_status duckos_capability_issue(
    duckos_capability_broker *broker,
    const duckos_capability_principal *issuer,
    const duckos_capability_principal *grantee,
    uint64_t rights,
    uint16_t resource_domain,
    duckos_capability_scope scope,
    uint64_t resource_id,
    uint64_t resource_generation,
    uint64_t *token
);

duckos_capability_status duckos_capability_attenuate(
    duckos_capability_broker *broker,
    const duckos_capability_principal *issuer,
    uint64_t parent_token,
    const duckos_capability_principal *grantee,
    uint64_t rights,
    uint16_t resource_domain,
    duckos_capability_scope scope,
    uint64_t resource_id,
    uint64_t resource_generation,
    uint64_t *token
);

duckos_capability_status duckos_capability_authorize(
    const duckos_capability_broker *broker,
    const duckos_capability_principal *caller,
    uint64_t token,
    ReaperSystemOperation operation,
    uint64_t resource_id,
    uint64_t resource_generation
);

duckos_capability_status duckos_capability_revoke(
    duckos_capability_broker *broker,
    const duckos_capability_principal *caller,
    uint64_t token
);

const char *duckos_capability_status_name(duckos_capability_status status);

#ifdef __cplusplus
}
#endif

#endif
