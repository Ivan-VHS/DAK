#include "predictive_guard.h"

#include <stdio.h>
#include <string.h>

#define CHECK(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "check failed at %s:%d: %s\n", __FILE__, __LINE__, #expression); \
        return 0; \
    } \
} while (0)

typedef struct check_context {
    dak_check_outcome outcome;
    uint32_t calls;
} check_context;

static bool accept_model(
    const dak_rule_model_v1 *model,
    const uint8_t *payload,
    size_t payload_bytes,
    void *context
) {
    (void)context;
    return model != NULL && payload != NULL && payload_bytes == 3u && model->generation != 0u;
}

static dak_check_outcome full_check(
    const dak_rule_model_v1 *model,
    const uint8_t *payload,
    size_t payload_bytes,
    const uint8_t *fingerprint,
    size_t request_bytes,
    void *opaque
) {
    check_context *context = (check_context *)opaque;
    if (model == NULL || payload == NULL || payload_bytes != 3u ||
        fingerprint == NULL || request_bytes == 17u || context == NULL) {
        return DAK_CHECK_INVALID;
    }
    ++context->calls;
    return context->outcome;
}

static dak_rule_model_v1 model(void) {
    dak_rule_model_v1 value = {0};
    value.struct_size = (uint32_t)sizeof(value);
    value.version = DAK_RULE_MODEL_VERSION;
    value.rule_count = 2u;
    value.payload_bytes = 3u;
    for (size_t i = 0u; i < DAK_RULE_MODEL_ID_BYTES; ++i) {
        value.model_id[i] = (uint8_t)(i + 1u);
        value.payload_digest[i] = (uint8_t)(i + 2u);
        value.schema_digest[i] = (uint8_t)(i + 3u);
    }
    return value;
}

static int test_prediction_never_authorizes_or_skips_full_check(void) {
    dak_rule_registry registry;
    dak_rule_lease lease = {0};
    dak_predictor predictor;
    dak_prediction prediction = {0};
    const uint8_t payload[] = {0x11u, 0x22u, 0x33u};
    uint8_t fingerprint[DAK_PREDICTOR_FINGERPRINT_BYTES] = {0};
    dak_rule_model_v1 descriptor = model();
    check_context context = {DAK_CHECK_DENY_COMPLETE, 0u};

    fingerprint[0] = 0x4au;
    dak_rule_registry_init(&registry);
    CHECK(dak_rule_registry_publish(&registry, &descriptor, payload, sizeof(payload),
        accept_model, NULL) == DAK_RULE_EPOCH_OK);
    CHECK(dak_rule_registry_pin(&registry, &lease) == DAK_RULE_EPOCH_OK);
    dak_predictor_init(&predictor);

    CHECK(dak_predictor_preflight(&predictor, &lease, fingerprint, 100u, &prediction) == DAK_GUARD_ALLOW);
    CHECK(prediction.kind == DAK_PREDICTION_UNKNOWN);
    CHECK(dak_predictor_authorize(&predictor, &lease, &prediction, fingerprint, 100u,
        full_check, &context) == DAK_GUARD_DENY_AUTHORITATIVE);
    CHECK(context.calls == 1u);

    CHECK(dak_predictor_preflight(&predictor, &lease, fingerprint, 100u, &prediction) == DAK_GUARD_ALLOW);
    CHECK(dak_predictor_authorize(&predictor, &lease, &prediction, fingerprint, 100u,
        full_check, &context) == DAK_GUARD_DENY_AUTHORITATIVE);
    CHECK(context.calls == 2u);

    context.outcome = DAK_CHECK_ALLOW_COMPLETE;
    CHECK(dak_predictor_preflight(&predictor, &lease, fingerprint, 100u, &prediction) == DAK_GUARD_ALLOW);
    CHECK(prediction.kind == DAK_PREDICTION_REPEATED_DENIAL);

    /* A caller cannot downgrade or forge the advice record to evade a deny. */
    dak_prediction forged = prediction;
    forged.kind = DAK_PREDICTION_UNKNOWN;
    CHECK(dak_predictor_authorize(&predictor, &lease, &forged, fingerprint, 100u,
        full_check, &context) == DAK_GUARD_INVALID_ARGUMENT);
    CHECK(context.calls == 2u);

    CHECK(dak_predictor_authorize(&predictor, &lease, &prediction, fingerprint, 100u,
        full_check, &context) == DAK_GUARD_DENY_PREDICTIVE);
    CHECK(context.calls == 3u);

    context.outcome = DAK_CHECK_INCOMPLETE;
    CHECK(dak_predictor_preflight(&predictor, &lease, fingerprint, 101u, &prediction) == DAK_GUARD_ALLOW);
    CHECK(dak_predictor_authorize(&predictor, &lease, &prediction, fingerprint, 101u,
        full_check, &context) == DAK_GUARD_DENY_INCOMPLETE);
    CHECK(context.calls == 4u);

    CHECK(dak_rule_registry_unpin(&registry, &lease) == DAK_RULE_EPOCH_OK);
    return 1;
}

static int test_invalid_preflight_is_closed(void) {
    dak_predictor predictor;
    dak_prediction prediction = {0};
    uint8_t fingerprint[DAK_PREDICTOR_FINGERPRINT_BYTES] = {0};
    dak_rule_lease empty = {0};

    dak_predictor_init(&predictor);
    CHECK(dak_predictor_preflight(&predictor, &empty, fingerprint, 1u, &prediction) ==
        DAK_GUARD_INVALID_ARGUMENT);
    fingerprint[0] = 1u;
    CHECK(dak_predictor_preflight(&predictor, &empty, fingerprint, 0u, &prediction) ==
        DAK_GUARD_INVALID_ARGUMENT);
    return 1;
}

int main(void) {
    if (!test_prediction_never_authorizes_or_skips_full_check() ||
        !test_invalid_preflight_is_closed()) {
        return 1;
    }
    puts("DAK predictive guard tests passed");
    return 0;
}
