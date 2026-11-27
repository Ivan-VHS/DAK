#include "rule_epoch.h"

#include <stdio.h>
#include <string.h>

#define CHECK(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "check failed at %s:%d: %s\n", __FILE__, __LINE__, #expression); \
        return 0; \
    } \
} while (0)

typedef struct verify_context {
    const uint8_t *expected;
    size_t expected_bytes;
    int accept;
    uint32_t calls;
} verify_context;

static bool test_verifier(
    const dak_rule_model_v1 *model,
    const uint8_t *payload,
    size_t payload_bytes,
    void *opaque
) {
    verify_context *context = (verify_context *)opaque;
    if (context == NULL || model == NULL || payload == NULL) return false;
    ++context->calls;
    return context->accept != 0 && payload_bytes == context->expected_bytes &&
        memcmp(payload, context->expected, payload_bytes) == 0 &&
        model->generation != 0u;
}

static dak_rule_model_v1 make_model(uint32_t rule_count, uint32_t payload_bytes, uint8_t seed) {
    dak_rule_model_v1 model = {0};
    model.struct_size = (uint32_t)sizeof(model);
    model.version = DAK_RULE_MODEL_VERSION;
    model.rule_count = rule_count;
    model.payload_bytes = payload_bytes;
    for (size_t index = 0u; index < DAK_RULE_MODEL_ID_BYTES; ++index) {
        model.model_id[index] = (uint8_t)(seed + index + 1u);
        model.payload_digest[index] = (uint8_t)(seed + index + 2u);
        model.schema_digest[index] = (uint8_t)(seed + index + 3u);
    }
    return model;
}

static int test_publish_pin_freeze_and_generation(void) {
    dak_rule_registry registry;
    dak_rule_lease lease = {0};
    const uint8_t payload_a[] = {0x10u, 0x20u, 0x30u, 0x40u};
    const uint8_t payload_b[] = {0x50u, 0x60u, 0x70u, 0x80u};
    dak_rule_model_v1 model_a = make_model(4u, sizeof(payload_a), 1u);
    dak_rule_model_v1 model_b = make_model(5u, sizeof(payload_b), 9u);
    verify_context verifier_a = {payload_a, sizeof(payload_a), 1, 0u};
    verify_context verifier_b = {payload_b, sizeof(payload_b), 1, 0u};
    uint64_t generation = 0u;

    dak_rule_registry_init(&registry);
    CHECK(dak_rule_registry_pin(&registry, &lease) == DAK_RULE_EPOCH_NOT_INITIALIZED);
    CHECK(dak_rule_registry_publish(&registry, &model_a, payload_a, sizeof(payload_a),
        test_verifier, &verifier_a) == DAK_RULE_EPOCH_OK);
    CHECK(verifier_a.calls == 1u);
    CHECK(dak_rule_registry_generation(&registry, &generation) == DAK_RULE_EPOCH_OK);
    CHECK(generation == 1u);

    CHECK(dak_rule_registry_pin(&registry, &lease) == DAK_RULE_EPOCH_OK);
    CHECK(dak_rule_lease_valid(&lease));
    CHECK(lease.generation == 1u);
    CHECK(memcmp(lease.payload, payload_a, sizeof(payload_a)) == 0);

    CHECK(dak_rule_registry_publish(&registry, &model_b, payload_b, sizeof(payload_b),
        test_verifier, &verifier_b) == DAK_RULE_EPOCH_BUSY);
    CHECK(dak_rule_registry_generation(&registry, &generation) == DAK_RULE_EPOCH_OK);
    CHECK(generation == 1u);
    CHECK(memcmp(lease.payload, payload_a, sizeof(payload_a)) == 0);

    CHECK(dak_rule_registry_unpin(&registry, &lease) == DAK_RULE_EPOCH_OK);
    CHECK(!dak_rule_lease_valid(&lease));
    CHECK(dak_rule_registry_publish(&registry, &model_b, payload_b, sizeof(payload_b),
        test_verifier, &verifier_b) == DAK_RULE_EPOCH_OK);
    CHECK(dak_rule_registry_generation(&registry, &generation) == DAK_RULE_EPOCH_OK);
    CHECK(generation == 2u);

    CHECK(dak_rule_registry_pin(&registry, &lease) == DAK_RULE_EPOCH_OK);
    CHECK(lease.generation == 2u);
    CHECK(memcmp(lease.payload, payload_b, sizeof(payload_b)) == 0);
    CHECK(dak_rule_registry_unpin(&registry, &lease) == DAK_RULE_EPOCH_OK);
    return 1;
}

static int test_failed_verification_is_transactional(void) {
    dak_rule_registry registry;
    const uint8_t good_payload[] = {1u, 3u, 5u, 7u};
    const uint8_t bad_payload[] = {2u, 4u, 6u, 8u};
    dak_rule_model_v1 good = make_model(2u, sizeof(good_payload), 2u);
    dak_rule_model_v1 bad = make_model(3u, sizeof(bad_payload), 12u);
    verify_context good_verifier = {good_payload, sizeof(good_payload), 1, 0u};
    verify_context bad_verifier = {good_payload, sizeof(good_payload), 0, 0u};
    uint64_t generation = 0u;

    dak_rule_registry_init(&registry);
    CHECK(dak_rule_registry_publish(&registry, &good, good_payload, sizeof(good_payload),
        test_verifier, &good_verifier) == DAK_RULE_EPOCH_OK);
    CHECK(dak_rule_registry_publish(&registry, &bad, bad_payload, sizeof(bad_payload),
        test_verifier, &bad_verifier) == DAK_RULE_EPOCH_VERIFY_FAILED);
    CHECK(dak_rule_registry_generation(&registry, &generation) == DAK_RULE_EPOCH_OK);
    CHECK(generation == 1u);
    return 1;
}

static int test_model_is_copied_before_verification(void) {
    dak_rule_registry registry;
    const uint8_t payload[] = {0xabu, 0xcdu, 0xefu};
    uint8_t mutable_payload[] = {0xabu, 0xcdu, 0xefu};
    dak_rule_model_v1 model = make_model(1u, sizeof(payload), 6u);
    verify_context verifier = {payload, sizeof(payload), 1, 0u};
    dak_rule_lease lease = {0};

    dak_rule_registry_init(&registry);
    CHECK(dak_rule_registry_publish(&registry, &model, mutable_payload, sizeof(mutable_payload),
        test_verifier, &verifier) == DAK_RULE_EPOCH_OK);
    memset(mutable_payload, 0, sizeof(mutable_payload));
    CHECK(dak_rule_registry_pin(&registry, &lease) == DAK_RULE_EPOCH_OK);
    CHECK(memcmp(lease.payload, payload, sizeof(payload)) == 0);
    CHECK(dak_rule_registry_unpin(&registry, &lease) == DAK_RULE_EPOCH_OK);
    return 1;
}

static int test_invalid_model_is_rejected_without_publication(void) {
    dak_rule_registry registry;
    const uint8_t payload[] = {1u};
    dak_rule_model_v1 model = make_model(1u, sizeof(payload), 3u);
    verify_context verifier = {payload, sizeof(payload), 1, 0u};
    uint64_t generation = 99u;

    dak_rule_registry_init(&registry);
    model.payload_bytes = 0u;
    CHECK(dak_rule_registry_publish(&registry, &model, payload, sizeof(payload),
        test_verifier, &verifier) == DAK_RULE_EPOCH_INVALID_ARGUMENT);
    CHECK(dak_rule_registry_generation(&registry, &generation) == DAK_RULE_EPOCH_NOT_INITIALIZED);
    CHECK(generation == 99u);
    CHECK(dak_rule_registry_publish(NULL, &model, payload, sizeof(payload),
        test_verifier, &verifier) == DAK_RULE_EPOCH_INVALID_ARGUMENT);
    return 1;
}

int main(void) {
    if (!test_publish_pin_freeze_and_generation() ||
        !test_failed_verification_is_transactional() ||
        !test_model_is_copied_before_verification() ||
        !test_invalid_model_is_rejected_without_publication()) {
        return 1;
    }
    puts("DAK immutable rule-epoch tests passed");
    return 0;
}
