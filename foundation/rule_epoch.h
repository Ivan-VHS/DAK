#ifndef DAK_RULE_EPOCH_H
#define DAK_RULE_EPOCH_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdatomic.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DAK_RULE_MODEL_VERSION 1u
#define DAK_RULE_MODEL_ID_BYTES 32u
#define DAK_RULE_DIGEST_BYTES 32u
#define DAK_RULE_MODEL_MAX_PAYLOAD_BYTES 16384u
#define DAK_RULE_MODEL_FLAG_VERIFIED 0x00000001u
#define DAK_RULE_MODEL_FLAG_IMMUTABLE 0x00000002u
#define DAK_RULE_MODEL_FLAGS_KNOWN (DAK_RULE_MODEL_FLAG_VERIFIED | DAK_RULE_MODEL_FLAG_IMMUTABLE)
#define DAK_RULE_SLOT_COUNT 2u
#define DAK_RULE_SLOT_NONE UINT32_MAX

typedef struct dak_rule_model_v1 {
    uint32_t struct_size;
    uint32_t version;
    uint32_t rule_count;
    uint32_t payload_bytes;
    uint32_t flags;
    uint32_t reserved;
    uint64_t generation;
    uint8_t model_id[DAK_RULE_MODEL_ID_BYTES];
    uint8_t payload_digest[DAK_RULE_DIGEST_BYTES];
    uint8_t schema_digest[DAK_RULE_DIGEST_BYTES];
} dak_rule_model_v1;

typedef enum dak_rule_epoch_status {
    DAK_RULE_EPOCH_OK = 0,
    DAK_RULE_EPOCH_INVALID_ARGUMENT,
    DAK_RULE_EPOCH_INVALID_MODEL,
    DAK_RULE_EPOCH_NOT_INITIALIZED,
    DAK_RULE_EPOCH_BUSY,
    DAK_RULE_EPOCH_VERIFY_FAILED,
    DAK_RULE_EPOCH_STALE_LEASE,
    DAK_RULE_EPOCH_GENERATION_EXHAUSTED
} dak_rule_epoch_status;

typedef enum dak_rule_slot_state {
    DAK_RULE_SLOT_EMPTY = 0,
    DAK_RULE_SLOT_STAGING,
    DAK_RULE_SLOT_ACTIVE,
    DAK_RULE_SLOT_RETIRED
} dak_rule_slot_state;

typedef struct dak_rule_slot {
    dak_rule_model_v1 model;
    uint32_t pin_count;
    uint32_t state;
    uint8_t payload[DAK_RULE_MODEL_MAX_PAYLOAD_BYTES];
} dak_rule_slot;

typedef struct dak_rule_registry {
    atomic_flag guard;
    uint32_t active_slot;
    uint32_t publishing;
    uint64_t generation;
    dak_rule_slot slots[DAK_RULE_SLOT_COUNT];
} dak_rule_registry;

typedef struct dak_rule_lease {
    const dak_rule_model_v1 *model;
    const uint8_t *payload;
    uint32_t payload_bytes;
    uint32_t slot_index;
    uint64_t generation;
    uint32_t held;
} dak_rule_lease;

/*
 * The verifier is a trusted native boundary. Production implementations must
 * verify the payload digest, signer, trust policy and schema before returning
 * true. A test callback is not a production verifier.
 */
typedef bool (*dak_rule_model_verify_fn)(
    const dak_rule_model_v1 *model,
    const uint8_t *payload,
    size_t payload_bytes,
    void *context
);

/* Cold-boot initialization only. Do not reinitialize a live registry. */
void dak_rule_registry_init(dak_rule_registry *registry);

/*
 * Publishes a new immutable model. Publication is rejected while any install
 * transaction holds a lease to the active model. The active snapshot is never
 * modified in place. Verification runs against the registry's private staging
 * copy, not caller-owned mutable memory.
 */
dak_rule_epoch_status dak_rule_registry_publish(
    dak_rule_registry *registry,
    const dak_rule_model_v1 *model,
    const uint8_t *payload,
    size_t payload_bytes,
    dak_rule_model_verify_fn verify,
    void *verify_context
);

/* Pin the current model for the full lifetime of an install transaction. */
dak_rule_epoch_status dak_rule_registry_pin(
    dak_rule_registry *registry,
    dak_rule_lease *lease
);

/* Release only the exact slot/generation originally pinned. */
dak_rule_epoch_status dak_rule_registry_unpin(
    dak_rule_registry *registry,
    dak_rule_lease *lease
);

/* Current generation is observational; it does not pin the returned model. */
dak_rule_epoch_status dak_rule_registry_generation(
    dak_rule_registry *registry,
    uint64_t *generation
);

bool dak_rule_lease_valid(const dak_rule_lease *lease);

#ifdef __cplusplus
}
#endif

#endif
