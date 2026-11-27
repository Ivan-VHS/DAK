#include "predictive_guard.h"

static void dak_bytes_clear(void *destination, size_t length) {
    uint8_t *bytes = (uint8_t *)destination;
    for (size_t index = 0u; index < length; ++index) bytes[index] = 0u;
}

static void dak_bytes_copy(void *destination, const void *source, size_t length) {
    uint8_t *output = (uint8_t *)destination;
    const uint8_t *input = (const uint8_t *)source;
    for (size_t index = 0u; index < length; ++index) output[index] = input[index];
}

static int dak_bytes_equal(const uint8_t *left, const uint8_t *right, size_t length) {
    uint8_t difference = 0u;
    for (size_t index = 0u; index < length; ++index) difference |= (uint8_t)(left[index] ^ right[index]);
    return difference == 0u;
}

static void predictor_lock(dak_predictor *predictor) {
    while (atomic_flag_test_and_set_explicit(&predictor->guard, memory_order_acquire)) {
        /* History operations are bounded; callbacks never run while this lock is held. */
    }
}

static void predictor_unlock(dak_predictor *predictor) {
    atomic_flag_clear_explicit(&predictor->guard, memory_order_release);
}

static bool fingerprint_valid(const uint8_t *fingerprint) {
    uint8_t combined = 0u;
    if (fingerprint == NULL) return false;
    for (size_t index = 0u; index < DAK_PREDICTOR_FINGERPRINT_BYTES; ++index) {
        combined |= fingerprint[index];
    }
    return combined != 0u;
}

void dak_predictor_init(dak_predictor *predictor) {
    if (predictor == NULL) return;
    dak_bytes_clear(predictor, sizeof(*predictor));
    atomic_flag_clear_explicit(&predictor->guard, memory_order_release);
}

dak_guard_result dak_predictor_preflight(
    dak_predictor *predictor,
    const dak_rule_lease *lease,
    const uint8_t fingerprint[DAK_PREDICTOR_FINGERPRINT_BYTES],
    size_t request_bytes,
    dak_prediction *prediction
) {
    if (predictor == NULL || !dak_rule_lease_valid(lease) || prediction == NULL ||
        !fingerprint_valid(fingerprint) || request_bytes == 0u ||
        request_bytes > DAK_PREDICTOR_REQUEST_MAX_BYTES) {
        return DAK_GUARD_INVALID_ARGUMENT;
    }

    dak_bytes_clear(prediction, sizeof(*prediction));
    prediction->generation = lease->generation;
    predictor_lock(predictor);
    if (predictor->count > DAK_PREDICTOR_HISTORY_CAPACITY ||
        predictor->next >= DAK_PREDICTOR_HISTORY_CAPACITY) {
        predictor_unlock(predictor);
        return DAK_GUARD_INVALID_ARGUMENT;
    }
    for (uint32_t index = 0u; index < predictor->count; ++index) {
        const dak_predictor_observation *observation = &predictor->history[index];
        if (observation->generation == lease->generation &&
            observation->outcome == DAK_CHECK_DENY_COMPLETE &&
            dak_bytes_equal(observation->fingerprint, fingerprint, DAK_PREDICTOR_FINGERPRINT_BYTES)) {
            ++prediction->repeated_denials;
        }
    }

    prediction->kind = prediction->repeated_denials >= DAK_PREDICTOR_DENIAL_THRESHOLD
        ? DAK_PREDICTION_REPEATED_DENIAL : DAK_PREDICTION_UNKNOWN;
    predictor_unlock(predictor);
    return DAK_GUARD_ALLOW;
}

dak_guard_result dak_predictor_authorize(
    dak_predictor *predictor,
    const dak_rule_lease *lease,
    const dak_prediction *prediction,
    const uint8_t fingerprint[DAK_PREDICTOR_FINGERPRINT_BYTES],
    size_t request_bytes,
    dak_authoritative_check_fn check,
    void *check_context
) {
    if (predictor == NULL || !dak_rule_lease_valid(lease) || prediction == NULL ||
        !fingerprint_valid(fingerprint) || request_bytes == 0u ||
        request_bytes > DAK_PREDICTOR_REQUEST_MAX_BYTES || check == NULL) {
        return DAK_GUARD_INVALID_ARGUMENT;
    }

    /* Recompute caller-visible advice so it cannot be forged or downgraded. */
    dak_prediction current_prediction = {0};
    if (dak_predictor_preflight(predictor, lease, fingerprint, request_bytes,
            &current_prediction) != DAK_GUARD_ALLOW ||
        prediction->generation != current_prediction.generation ||
        prediction->kind != current_prediction.kind ||
        prediction->repeated_denials != current_prediction.repeated_denials) {
        return DAK_GUARD_INVALID_ARGUMENT;
    }

    /* Never short-circuit: every valid request reaches the authoritative check. */
    const dak_check_outcome outcome = check(
        lease->model, lease->payload, lease->payload_bytes,
        fingerprint, request_bytes, check_context
    );

    if (outcome != DAK_CHECK_ALLOW_COMPLETE && outcome != DAK_CHECK_DENY_COMPLETE) {
        return DAK_GUARD_DENY_INCOMPLETE;
    }

    predictor_lock(predictor);
    dak_predictor_observation *observation = &predictor->history[predictor->next];
    dak_bytes_copy(observation->fingerprint, fingerprint, DAK_PREDICTOR_FINGERPRINT_BYTES);
    observation->generation = lease->generation;
    observation->outcome = (uint8_t)outcome;
    predictor->next = (predictor->next + 1u) % DAK_PREDICTOR_HISTORY_CAPACITY;
    if (predictor->count < DAK_PREDICTOR_HISTORY_CAPACITY) ++predictor->count;
    predictor_unlock(predictor);

    if (prediction->kind == DAK_PREDICTION_REPEATED_DENIAL) {
        return DAK_GUARD_DENY_PREDICTIVE;
    }
    return outcome == DAK_CHECK_ALLOW_COMPLETE
        ? DAK_GUARD_ALLOW : DAK_GUARD_DENY_AUTHORITATIVE;
}
