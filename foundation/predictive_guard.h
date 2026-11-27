#ifndef DAK_PREDICTIVE_GUARD_H
#define DAK_PREDICTIVE_GUARD_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdatomic.h>

#include "rule_epoch.h"

#ifdef __cplusplus
extern "C" {
#endif

#define DAK_PREDICTOR_HISTORY_CAPACITY 32u
#define DAK_PREDICTOR_FINGERPRINT_BYTES 32u
#define DAK_PREDICTOR_REQUEST_MAX_BYTES 65536u
#define DAK_PREDICTOR_DENIAL_THRESHOLD 2u

typedef enum dak_check_outcome {
    DAK_CHECK_ALLOW_COMPLETE = 1,
    DAK_CHECK_DENY_COMPLETE = 2,
    DAK_CHECK_INCOMPLETE = 3,
    DAK_CHECK_INVALID = 4
} dak_check_outcome;

typedef enum dak_prediction_kind {
    DAK_PREDICTION_UNKNOWN = 0,
    DAK_PREDICTION_REPEATED_DENIAL = 1
} dak_prediction_kind;

typedef enum dak_guard_result {
    DAK_GUARD_ALLOW = 0,
    DAK_GUARD_DENY_AUTHORITATIVE,
    DAK_GUARD_DENY_PREDICTIVE,
    DAK_GUARD_DENY_INCOMPLETE,
    DAK_GUARD_INVALID_ARGUMENT
} dak_guard_result;

typedef struct dak_predictor_observation {
    uint8_t fingerprint[DAK_PREDICTOR_FINGERPRINT_BYTES];
    uint64_t generation;
    uint8_t outcome;
} dak_predictor_observation;

typedef struct dak_predictor {
    atomic_flag guard;
    uint32_t count;
    uint32_t next;
    dak_predictor_observation history[DAK_PREDICTOR_HISTORY_CAPACITY];
} dak_predictor;

typedef struct dak_prediction {
    uint32_t kind;
    uint32_t repeated_denials;
    uint64_t generation;
} dak_prediction;

/* The callback must execute the complete authoritative rule set for this request. */
typedef dak_check_outcome (*dak_authoritative_check_fn)(
    const dak_rule_model_v1 *model,
    const uint8_t *model_payload,
    size_t model_payload_bytes,
    const uint8_t *request_fingerprint,
    size_t request_bytes,
    void *context
);

void dak_predictor_init(dak_predictor *predictor);

dak_guard_result dak_predictor_preflight(
    dak_predictor *predictor,
    const dak_rule_lease *lease,
    const uint8_t fingerprint[DAK_PREDICTOR_FINGERPRINT_BYTES],
    size_t request_bytes,
    dak_prediction *prediction
);

/*
 * Prediction is advisory only. The full callback always runs on a valid lease;
 * prediction can add a conservative deny but can never produce an allow.
 */
dak_guard_result dak_predictor_authorize(
    dak_predictor *predictor,
    const dak_rule_lease *lease,
    const dak_prediction *prediction,
    const uint8_t fingerprint[DAK_PREDICTOR_FINGERPRINT_BYTES],
    size_t request_bytes,
    dak_authoritative_check_fn check,
    void *check_context
);

#ifdef __cplusplus
}
#endif

#endif
