#include "capability_broker.h"

#include <string.h>

#define TOKEN_INDEX_MASK UINT64_C(0xffffffff)
#define TOKEN_GENERATION_SHIFT 32U
#define CAPABILITY_ALLOWED_MASK (REAPER_SYSTEM_CAP_KNOWN_MASK | DUCKOS_CAPABILITY_BROKER_DELEGATE)

static int principal_valid(const duckos_capability_principal *principal) {
    return principal != NULL && principal->task_id != 0U &&
           principal->generation != 0U;
}

static int principal_equal(const duckos_capability_principal *left,
                           const duckos_capability_principal *right) {
    return left->task_id == right->task_id &&
           left->generation == right->generation;
}

static uint64_t token_encode(uint32_t index, uint32_t generation) {
    return ((uint64_t)generation << TOKEN_GENERATION_SHIFT) |
           ((uint64_t)index + UINT64_C(1));
}

static duckos_capability_slot *token_slot(
    const duckos_capability_broker *broker,
    uint64_t token,
    uint32_t *index_out
) {
    uint64_t raw_index = token & TOKEN_INDEX_MASK;
    uint64_t raw_generation = token >> TOKEN_GENERATION_SHIFT;
    uint32_t index;

    if (broker == NULL || broker->slots == NULL || token == 0U ||
        raw_index == 0U || raw_generation == 0U ||
        raw_index > broker->capacity) {
        return NULL;
    }
    index = (uint32_t)(raw_index - UINT64_C(1));
    if (broker->slots[index].generation != (uint32_t)raw_generation ||
        broker->slots[index].active == 0U) {
        return NULL;
    }
    if (index_out != NULL) *index_out = index;
    return &broker->slots[index];
}

static duckos_capability_status allocate_slot(
    duckos_capability_broker *broker,
    duckos_capability_slot **slot_out,
    uint32_t *index_out
) {
    uint32_t index;

    if (broker->active_count >= broker->capacity) return DUCKOS_CAPABILITY_TABLE_FULL;
    for (index = 0U; index < broker->capacity; ++index) {
        duckos_capability_slot *slot = &broker->slots[index];
        if (slot->active != 0U || slot->generation == UINT32_MAX) continue;
        slot->generation += 1U;
        *slot_out = slot;
        *index_out = index;
        return DUCKOS_CAPABILITY_OK;
    }
    return DUCKOS_CAPABILITY_GENERATION_EXHAUSTED;
}

static int domain_valid(uint16_t domain) {
    return domain >= (uint16_t)REAPER_SYSTEM_DOMAIN_PROCESS &&
           domain <= (uint16_t)REAPER_SYSTEM_DOMAIN_DESKTOP_SHELL;
}

static uint64_t domain_capability_mask(uint16_t domain) {
    switch ((ReaperSystemDomain)domain) {
        case REAPER_SYSTEM_DOMAIN_PROCESS:
            return REAPER_SYSTEM_CAP_PROCESS_INSPECT | REAPER_SYSTEM_CAP_PROCESS_CONTROL;
        case REAPER_SYSTEM_DOMAIN_THREAD:
            return REAPER_SYSTEM_CAP_THREAD_CONTROL;
        case REAPER_SYSTEM_DOMAIN_SYNC:
            return REAPER_SYSTEM_CAP_SYNC;
        case REAPER_SYSTEM_DOMAIN_FILESYSTEM:
            return REAPER_SYSTEM_CAP_FS_HANDLE | REAPER_SYSTEM_CAP_FS_READ |
                   REAPER_SYSTEM_CAP_FS_WRITE;
        case REAPER_SYSTEM_DOMAIN_CLOCK:
            return REAPER_SYSTEM_CAP_CLOCK;
        case REAPER_SYSTEM_DOMAIN_NETWORK:
            return REAPER_SYSTEM_CAP_NETWORK;
        case REAPER_SYSTEM_DOMAIN_CRYPTO:
            return REAPER_SYSTEM_CAP_CRYPTO;
        case REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW:
            return REAPER_SYSTEM_CAP_DESKTOP_WINDOW;
        case REAPER_SYSTEM_DOMAIN_DESKTOP_DISPLAY:
            return REAPER_SYSTEM_CAP_DESKTOP_DISPLAY |
                   REAPER_SYSTEM_CAP_DESKTOP_DISPLAY_ADMIN;
        case REAPER_SYSTEM_DOMAIN_DESKTOP_INPUT:
            return REAPER_SYSTEM_CAP_DESKTOP_INPUT;
        case REAPER_SYSTEM_DOMAIN_DESKTOP_SESSION:
            return REAPER_SYSTEM_CAP_DESKTOP_SESSION |
                   REAPER_SYSTEM_CAP_DESKTOP_SESSION_ADMIN;
        case REAPER_SYSTEM_DOMAIN_DESKTOP_COMPOSITOR:
            return REAPER_SYSTEM_CAP_DESKTOP_COMPOSITOR;
        case REAPER_SYSTEM_DOMAIN_DESKTOP_GPU:
            return REAPER_SYSTEM_CAP_DESKTOP_GPU |
                   REAPER_SYSTEM_CAP_DESKTOP_GPU_ADMIN;
        case REAPER_SYSTEM_DOMAIN_DESKTOP_SHELL:
            return REAPER_SYSTEM_CAP_DESKTOP_SHELL;
        case REAPER_SYSTEM_DOMAIN_INVALID:
            break;
    }
    return 0U;
}

static int rights_valid(uint64_t rights) {
    return (rights & REAPER_SYSTEM_CAP_KNOWN_MASK) != 0U &&
           (rights & ~CAPABILITY_ALLOWED_MASK) == 0U;
}

static int rights_fit_domain(uint16_t domain, uint64_t rights) {
    uint64_t allowed = domain_capability_mask(domain);
    return allowed != 0U &&
           (rights & ~(allowed | DUCKOS_CAPABILITY_BROKER_DELEGATE)) == 0U;
}

static int scope_valid(uint16_t domain, duckos_capability_scope scope,
                       uint64_t resource_id, uint64_t resource_generation) {
    if (scope == DUCKOS_CAPABILITY_SCOPE_GLOBAL) {
        return resource_id == 0U && resource_generation == 0U;
    }
    if (scope == DUCKOS_CAPABILITY_SCOPE_OBJECT) {
        return domain_valid(domain) && resource_id != 0U &&
               resource_generation != 0U;
    }
    return 0;
}

static int grant_chain_active(
    const duckos_capability_broker *broker,
    const duckos_capability_slot *slot,
    uint64_t child_token
) {
    uint64_t parent_token = slot->parent_token;
    uint32_t depth = 0U;

    while (parent_token != 0U) {
        const duckos_capability_slot *parent;
        if (++depth > broker->capacity || parent_token == child_token) return 0;
        parent = token_slot(broker, parent_token, NULL);
        if (parent == NULL || parent->grantee.task_id != slot->grantor.task_id ||
            parent->grantee.generation != slot->grantor.generation) {
            return 0;
        }
        child_token = parent_token;
        slot = parent;
        parent_token = parent->parent_token;
    }
    return 1;
}

duckos_capability_status duckos_capability_broker_init(
    duckos_capability_broker *broker,
    duckos_capability_slot *slots,
    uint32_t capacity,
    duckos_capability_principal authority,
    uint64_t root_ceiling
) {
    if (broker == NULL || slots == NULL || !principal_valid(&authority) ||
        capacity == 0U || capacity > DUCKOS_CAPABILITY_BROKER_MAX_SLOTS ||
        root_ceiling == 0U || (root_ceiling & ~CAPABILITY_ALLOWED_MASK) != 0U) {
        return DUCKOS_CAPABILITY_INVALID_ARGUMENT;
    }
    memset(slots, 0, (size_t)capacity * sizeof(*slots));
    memset(broker, 0, sizeof(*broker));
    broker->authority = authority;
    broker->slots = slots;
    broker->capacity = capacity;
    broker->root_ceiling = root_ceiling;
    return DUCKOS_CAPABILITY_OK;
}

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
) {
    duckos_capability_slot *slot;
    uint32_t index;
    duckos_capability_status status;

    if (token != NULL) *token = 0U;
    if (broker == NULL || !principal_valid(issuer) ||
        !principal_valid(grantee) || token == NULL ||
        principal_equal(issuer, grantee) || !rights_valid(rights) ||
        (rights & ~broker->root_ceiling) != 0U ||
        !domain_valid(resource_domain) || !rights_fit_domain(resource_domain, rights) ||
        !scope_valid(resource_domain, scope, resource_id, resource_generation)) {
        return DUCKOS_CAPABILITY_INVALID_ARGUMENT;
    }
    if (!principal_equal(issuer, &broker->authority)) return DUCKOS_CAPABILITY_DENIED;

    status = allocate_slot(broker, &slot, &index);
    if (status != DUCKOS_CAPABILITY_OK) return status;

    slot->grantor = *issuer;
    slot->grantee = *grantee;
    slot->rights = rights;
    slot->resource_domain = resource_domain;
    slot->scope = (uint8_t)scope;
    slot->resource_id = resource_id;
    slot->resource_generation = resource_generation;
    slot->parent_token = 0U;
    slot->active = 1U;
    broker->active_count += 1U;
    *token = token_encode(index, slot->generation);
    return DUCKOS_CAPABILITY_OK;
}

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
) {
    duckos_capability_slot *parent;
    duckos_capability_slot *slot;
    uint32_t index;
    duckos_capability_status status;

    if (token != NULL) *token = 0U;
    if (broker == NULL || !principal_valid(issuer) ||
        !principal_valid(grantee) || token == NULL ||
        principal_equal(issuer, grantee) || !rights_valid(rights) ||
        !domain_valid(resource_domain) || !rights_fit_domain(resource_domain, rights) ||
        !scope_valid(resource_domain, scope, resource_id, resource_generation)) {
        return DUCKOS_CAPABILITY_INVALID_ARGUMENT;
    }
    parent = token_slot(broker, parent_token, NULL);
    if (parent == NULL || !principal_equal(&parent->grantee, issuer) ||
        !grant_chain_active(broker, parent, parent_token)) {
        return DUCKOS_CAPABILITY_STALE_TOKEN;
    }
    if ((parent->rights & DUCKOS_CAPABILITY_BROKER_DELEGATE) == 0U) {
        return DUCKOS_CAPABILITY_NOT_DELEGABLE;
    }
    if ((rights & ~parent->rights) != 0U) {
        return DUCKOS_CAPABILITY_RIGHTS_ESCALATION;
    }
    if (parent->scope == (uint8_t)DUCKOS_CAPABILITY_SCOPE_OBJECT) {
        if (scope != DUCKOS_CAPABILITY_SCOPE_OBJECT ||
            resource_domain != parent->resource_domain ||
            resource_id != parent->resource_id ||
            resource_generation != parent->resource_generation) {
            return DUCKOS_CAPABILITY_RESOURCE_MISMATCH;
        }
    }

    status = allocate_slot(broker, &slot, &index);
    if (status != DUCKOS_CAPABILITY_OK) return status;
    slot->grantor = *issuer;
    slot->grantee = *grantee;
    slot->rights = rights;
    slot->resource_domain = resource_domain;
    slot->scope = (uint8_t)scope;
    slot->resource_id = resource_id;
    slot->resource_generation = resource_generation;
    slot->parent_token = parent_token;
    slot->active = 1U;
    broker->active_count += 1U;
    *token = token_encode(index, slot->generation);
    return DUCKOS_CAPABILITY_OK;
}

duckos_capability_status duckos_capability_authorize(
    const duckos_capability_broker *broker,
    const duckos_capability_principal *caller,
    uint64_t token,
    ReaperSystemOperation operation,
    uint64_t resource_id,
    uint64_t resource_generation
) {
    const ReaperSystemOperationInfo *info;
    duckos_capability_slot *slot;

    if (broker == NULL || !principal_valid(caller) || token == 0U) {
        return DUCKOS_CAPABILITY_INVALID_ARGUMENT;
    }
    info = reaper_system_operation_find(operation);
    if (info == NULL) return DUCKOS_CAPABILITY_UNKNOWN_OPERATION;

    slot = token_slot(broker, token, NULL);
    if (slot == NULL) return DUCKOS_CAPABILITY_STALE_TOKEN;
    if (!principal_equal(&slot->grantee, caller) ||
        !grant_chain_active(broker, slot, token)) {
        return DUCKOS_CAPABILITY_DENIED;
    }
    if (slot->resource_domain != (uint16_t)info->domain ||
        (slot->rights & info->required_capabilities) != info->required_capabilities) {
        return DUCKOS_CAPABILITY_DENIED;
    }
    if (slot->scope == (uint8_t)DUCKOS_CAPABILITY_SCOPE_OBJECT) {
        if (slot->resource_domain != (uint16_t)info->domain ||
            slot->resource_id != resource_id ||
            slot->resource_generation != resource_generation) {
            return DUCKOS_CAPABILITY_RESOURCE_MISMATCH;
        }
    }
    return DUCKOS_CAPABILITY_OK;
}

duckos_capability_status duckos_capability_revoke(
    duckos_capability_broker *broker,
    const duckos_capability_principal *caller,
    uint64_t token
) {
    duckos_capability_slot *slot;

    if (broker == NULL || !principal_valid(caller) || token == 0U) {
        return DUCKOS_CAPABILITY_INVALID_ARGUMENT;
    }
    slot = token_slot(broker, token, NULL);
    if (slot == NULL) return DUCKOS_CAPABILITY_STALE_TOKEN;
    if (!principal_equal(caller, &broker->authority) &&
        !principal_equal(caller, &slot->grantee)) {
        return DUCKOS_CAPABILITY_DENIED;
    }
    slot->active = 0U;
    slot->rights = 0U;
    if (broker->active_count > 0U) broker->active_count -= 1U;
    return DUCKOS_CAPABILITY_OK;
}

const char *duckos_capability_status_name(duckos_capability_status status) {
    switch (status) {
        case DUCKOS_CAPABILITY_OK: return "ok";
        case DUCKOS_CAPABILITY_INVALID_ARGUMENT: return "invalid-argument";
        case DUCKOS_CAPABILITY_INVALID_CAPACITY: return "invalid-capacity";
        case DUCKOS_CAPABILITY_DENIED: return "denied";
        case DUCKOS_CAPABILITY_UNKNOWN_OPERATION: return "unknown-operation";
        case DUCKOS_CAPABILITY_STALE_TOKEN: return "stale-token";
        case DUCKOS_CAPABILITY_RESOURCE_MISMATCH: return "resource-mismatch";
        case DUCKOS_CAPABILITY_NOT_DELEGABLE: return "not-delegable";
        case DUCKOS_CAPABILITY_RIGHTS_ESCALATION: return "rights-escalation";
        case DUCKOS_CAPABILITY_TABLE_FULL: return "table-full";
        case DUCKOS_CAPABILITY_GENERATION_EXHAUSTED: return "generation-exhausted";
        case DUCKOS_CAPABILITY_REVOKED: return "revoked";
    }
    return "unknown-status";
}
