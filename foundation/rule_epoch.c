#include "rule_epoch.h"

#include <string.h>

static void registry_lock(dak_rule_registry *registry) {
    while (atomic_flag_test_and_set_explicit(&registry->guard, memory_order_acquire)) {
        /* The critical sections are bounded metadata copies; no I/O occurs here. */
    }
}

static void registry_unlock(dak_rule_registry *registry) {
    atomic_flag_clear_explicit(&registry->guard, memory_order_release);
}

static bool bytes_nonzero(const uint8_t *bytes, size_t length) {
    uint8_t combined = 0u;
    for (size_t index = 0u; index < length; ++index) combined |= bytes[index];
    return combined != 0u;
}

static bool model_descriptor_valid(const dak_rule_model_v1 *model, size_t payload_bytes) {
    if (model == NULL || model->struct_size != sizeof(*model) ||
        model->version != DAK_RULE_MODEL_VERSION || model->rule_count == 0u ||
        model->payload_bytes == 0u || model->payload_bytes != payload_bytes ||
        payload_bytes > DAK_RULE_MODEL_MAX_PAYLOAD_BYTES || model->reserved != 0u ||
        (model->flags & ~DAK_RULE_MODEL_FLAGS_KNOWN) != 0u ||
        model->generation != 0u) {
        return false;
    }
    return bytes_nonzero(model->model_id, sizeof(model->model_id)) &&
        bytes_nonzero(model->payload_digest, sizeof(model->payload_digest)) &&
        bytes_nonzero(model->schema_digest, sizeof(model->schema_digest));
}

void dak_rule_registry_init(dak_rule_registry *registry) {
    if (registry == NULL) return;
    memset(registry, 0, sizeof(*registry));
    atomic_flag_clear_explicit(&registry->guard, memory_order_release);
    registry->active_slot = DAK_RULE_SLOT_NONE;
    for (uint32_t index = 0u; index < DAK_RULE_SLOT_COUNT; ++index) {
        registry->slots[index].state = DAK_RULE_SLOT_EMPTY;
    }
}

dak_rule_epoch_status dak_rule_registry_publish(
    dak_rule_registry *registry,
    const dak_rule_model_v1 *model,
    const uint8_t *payload,
    size_t payload_bytes,
    dak_rule_model_verify_fn verify,
    void *verify_context
) {
    if (registry == NULL || model == NULL || payload == NULL || verify == NULL ||
        !model_descriptor_valid(model, payload_bytes)) {
        return DAK_RULE_EPOCH_INVALID_ARGUMENT;
    }

    registry_lock(registry);
    if (registry->publishing != 0u) {
        registry_unlock(registry);
        return DAK_RULE_EPOCH_BUSY;
    }
    if (registry->active_slot != DAK_RULE_SLOT_NONE &&
        registry->slots[registry->active_slot].pin_count != 0u) {
        registry_unlock(registry);
        return DAK_RULE_EPOCH_BUSY;
    }
    if (registry->generation == UINT64_MAX) {
        registry_unlock(registry);
        return DAK_RULE_EPOCH_GENERATION_EXHAUSTED;
    }

    const uint32_t destination = registry->active_slot == DAK_RULE_SLOT_NONE
        ? 0u : (registry->active_slot ^ 1u);
    dak_rule_slot *slot = &registry->slots[destination];
    if (slot->pin_count != 0u || slot->state == DAK_RULE_SLOT_STAGING) {
        registry_unlock(registry);
        return DAK_RULE_EPOCH_BUSY;
    }

    registry->publishing = 1u;
    slot->state = DAK_RULE_SLOT_STAGING;
    slot->model = *model;
    slot->model.generation = registry->generation + 1u;
    slot->model.flags = 0u;
    slot->pin_count = 0u;
    memcpy(slot->payload, payload, payload_bytes);
    if (payload_bytes < DAK_RULE_MODEL_MAX_PAYLOAD_BYTES) {
        memset(slot->payload + payload_bytes, 0,
            DAK_RULE_MODEL_MAX_PAYLOAD_BYTES - payload_bytes);
    }
    registry_unlock(registry);

    /* The staging slot is private and pin() is blocked until this completes. */
    const bool verified = verify(&slot->model, slot->payload, payload_bytes, verify_context);

    registry_lock(registry);
    if (!verified) {
        memset(&slot->model, 0, sizeof(slot->model));
        memset(slot->payload, 0, sizeof(slot->payload));
        slot->state = DAK_RULE_SLOT_EMPTY;
        registry->publishing = 0u;
        registry_unlock(registry);
        return DAK_RULE_EPOCH_VERIFY_FAILED;
    }

    if (registry->publishing == 0u || slot->state != DAK_RULE_SLOT_STAGING ||
        slot->pin_count != 0u || slot->model.generation != registry->generation + 1u) {
        registry->publishing = 0u;
        slot->state = DAK_RULE_SLOT_RETIRED;
        registry_unlock(registry);
        return DAK_RULE_EPOCH_BUSY;
    }

    slot->model.flags = DAK_RULE_MODEL_FLAG_VERIFIED | DAK_RULE_MODEL_FLAG_IMMUTABLE;
    slot->state = DAK_RULE_SLOT_ACTIVE;
    if (registry->active_slot != DAK_RULE_SLOT_NONE) {
        registry->slots[registry->active_slot].state = DAK_RULE_SLOT_RETIRED;
    }
    registry->active_slot = destination;
    registry->generation = slot->model.generation;
    registry->publishing = 0u;
    registry_unlock(registry);
    return DAK_RULE_EPOCH_OK;
}

dak_rule_epoch_status dak_rule_registry_pin(
    dak_rule_registry *registry,
    dak_rule_lease *lease
) {
    if (registry == NULL || lease == NULL) return DAK_RULE_EPOCH_INVALID_ARGUMENT;
    memset(lease, 0, sizeof(*lease));

    registry_lock(registry);
    if (registry->publishing != 0u) {
        registry_unlock(registry);
        return DAK_RULE_EPOCH_BUSY;
    }
    if (registry->active_slot == DAK_RULE_SLOT_NONE) {
        registry_unlock(registry);
        return DAK_RULE_EPOCH_NOT_INITIALIZED;
    }

    dak_rule_slot *slot = &registry->slots[registry->active_slot];
    if (slot->state != DAK_RULE_SLOT_ACTIVE ||
        (slot->model.flags & (DAK_RULE_MODEL_FLAG_VERIFIED | DAK_RULE_MODEL_FLAG_IMMUTABLE)) !=
            (DAK_RULE_MODEL_FLAG_VERIFIED | DAK_RULE_MODEL_FLAG_IMMUTABLE) ||
        slot->pin_count == UINT32_MAX) {
        registry_unlock(registry);
        return DAK_RULE_EPOCH_INVALID_MODEL;
    }

    ++slot->pin_count;
    lease->model = &slot->model;
    lease->payload = slot->payload;
    lease->payload_bytes = slot->model.payload_bytes;
    lease->slot_index = registry->active_slot;
    lease->generation = slot->model.generation;
    lease->held = 1u;
    registry_unlock(registry);
    return DAK_RULE_EPOCH_OK;
}

dak_rule_epoch_status dak_rule_registry_unpin(
    dak_rule_registry *registry,
    dak_rule_lease *lease
) {
    if (registry == NULL || lease == NULL || lease->held != 1u ||
        lease->slot_index >= DAK_RULE_SLOT_COUNT || lease->model == NULL) {
        return DAK_RULE_EPOCH_INVALID_ARGUMENT;
    }

    registry_lock(registry);
    dak_rule_slot *slot = &registry->slots[lease->slot_index];
    if (slot->pin_count == 0u || slot->model.generation != lease->generation ||
        &slot->model != lease->model) {
        registry_unlock(registry);
        return DAK_RULE_EPOCH_STALE_LEASE;
    }

    --slot->pin_count;
    if (slot->pin_count == 0u && slot->state == DAK_RULE_SLOT_RETIRED) {
        slot->state = DAK_RULE_SLOT_EMPTY;
        memset(&slot->model, 0, sizeof(slot->model));
        memset(slot->payload, 0, sizeof(slot->payload));
    }
    registry_unlock(registry);
    memset(lease, 0, sizeof(*lease));
    return DAK_RULE_EPOCH_OK;
}

dak_rule_epoch_status dak_rule_registry_generation(
    dak_rule_registry *registry,
    uint64_t *generation
) {
    if (registry == NULL || generation == NULL) return DAK_RULE_EPOCH_INVALID_ARGUMENT;
    registry_lock(registry);
    if (registry->active_slot == DAK_RULE_SLOT_NONE) {
        registry_unlock(registry);
        return DAK_RULE_EPOCH_NOT_INITIALIZED;
    }
    *generation = registry->generation;
    registry_unlock(registry);
    return DAK_RULE_EPOCH_OK;
}

bool dak_rule_lease_valid(const dak_rule_lease *lease) {
    return lease != NULL && lease->held == 1u && lease->model != NULL &&
        lease->payload != NULL && lease->payload_bytes != 0u &&
        lease->generation != 0u && lease->model->generation == lease->generation &&
        (lease->model->flags & (DAK_RULE_MODEL_FLAG_VERIFIED | DAK_RULE_MODEL_FLAG_IMMUTABLE)) ==
            (DAK_RULE_MODEL_FLAG_VERIFIED | DAK_RULE_MODEL_FLAG_IMMUTABLE);
}
