#include "security.h"

#ifdef NDEBUG
#undef NDEBUG
#endif

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static duckos_security_event_v1 event_make(
    uint64_t sequence, uint64_t mono, const char *id, const char *host,
    const char *source, const char *actor, uint32_t kind
) {
    duckos_security_event_v1 e;
    (void)memset(&e, 0, sizeof(e));
    e.struct_size = (uint32_t)sizeof(e);
    e.version = DUCKOS_SECURITY_ABI_VERSION;
    e.sequence = sequence;
    e.monotonic_ns = mono;
    e.observed_at_ms = 1800000000000ull + mono / 1000000ull;
    e.kind = kind;
    e.source_trust = DUCKOS_SECURITY_TRUST_TRUSTED;
    (void)snprintf(e.event_id, sizeof(e.event_id), "%s", id);
    (void)snprintf(e.host_id, sizeof(e.host_id), "%s", host);
    (void)snprintf(e.source_id, sizeof(e.source_id), "%s", source);
    (void)snprintf(e.actor_id, sizeof(e.actor_id), "%s", actor);
    return e;
}
static void test_trust_and_validation(void) {
    duckos_security_engine engine;
    duckos_security_evaluation_v1 result;
    duckos_security_engine_init(&engine);
    duckos_security_event_v1 e = event_make(1, 10, "e1", "h1", "s1", "p1",
                                             DUCKOS_SECURITY_PROCESS_START);
    assert(duckos_security_event_validate(&e) == DUCKOS_SECURITY_OK);
    e.source_trust = DUCKOS_SECURITY_TRUST_VALIDATED;
    assert(duckos_security_ingest(&engine, &e, &result) ==
           DUCKOS_SECURITY_UNTRUSTED_SOURCE);
    e.source_trust = DUCKOS_SECURITY_TRUST_TRUSTED;
    e.flags = 0x80000000u;
    assert(duckos_security_event_validate(&e) == DUCKOS_SECURITY_INVALID_EVENT);
}
static void test_file_burst_and_causal_chain(void) {
    duckos_security_engine engine;
    duckos_security_evaluation_v1 result;
    duckos_security_engine_init(&engine);
    duckos_security_event_v1 p = event_make(1, 1000000000ull, "p", "h", "s", "pid",
                                             DUCKOS_SECURITY_PROCESS_START);
    assert(duckos_security_ingest(&engine, &p, &result) == DUCKOS_SECURITY_OK);
    for (uint64_t i = 0; i < 3; ++i) {
        char id[16];
        (void)snprintf(id, sizeof(id), "f%llu", (unsigned long long)i);
        duckos_security_event_v1 f = event_make(i + 2, 1010000000ull + i * 10000000ull,
                                                 id, "h", "s", "pid",
                                                 DUCKOS_SECURITY_FILE_MODIFY);
        (void)snprintf(f.parent_event_id, sizeof(f.parent_event_id), "%s", "p");
        f.entropy_delta_bp = 6000;
        assert(duckos_security_ingest(&engine, &f, &result) == DUCKOS_SECURITY_OK);
    }
    assert(result.risk_score >= 35);
    assert(result.recommendation == DUCKOS_SECURITY_ACTION_RESTRICT);
    assert(result.file_mutations_in_window == 3);
    assert(result.causal_depth == 2);
    assert(strcmp(result.causal_root_event_id, "p") == 0);
    assert((result.indicators & DUCKOS_SECURITY_IND_FILE_MUTATION_BURST) != 0);
    assert((result.indicators & DUCKOS_SECURITY_IND_HIGH_ENTROPY_CHANGE) != 0);
    assert(result.advisory_only == 1);
}
static void test_credential_lolbin_and_mesh_cluster(void) {
    duckos_security_engine engine;
    duckos_security_evaluation_v1 result;
    duckos_security_engine_init(&engine);
    duckos_security_event_v1 e = event_make(1, 100, "cred", "h1", "s1", "stealer",
                                            DUCKOS_SECURITY_IDENTITY_ACCESS);
    e.flags = DUCKOS_SECURITY_FLAG_CREDENTIAL_MATERIAL;
    assert(duckos_security_ingest(&engine, &e, &result) == DUCKOS_SECURITY_OK);
    assert(result.risk_score == 60);
    assert(result.recommendation == DUCKOS_SECURITY_ACTION_ISOLATE);

    duckos_security_engine_init(&engine);
    e = event_make(1, 100, "lol", "h1", "s1", "shell", DUCKOS_SECURITY_PROCESS_START);
    (void)snprintf(e.image_name, sizeof(e.image_name), "%s", "powershell.exe");
    e.flags = DUCKOS_SECURITY_FLAG_ENCODED_COMMAND;
    assert(duckos_security_ingest(&engine, &e, &result) == DUCKOS_SECURITY_OK);
    assert(result.risk_score == 25);
    assert((result.indicators & DUCKOS_SECURITY_IND_LOLBIN_CONTEXT) != 0);

    duckos_security_engine_init(&engine);
    e = event_make(1, 100, "net1", "h1", "s1", "p1", DUCKOS_SECURITY_NETWORK_CONNECT);
    (void)snprintf(e.indicator, sizeof(e.indicator), "%s", "ioc-demo");
    assert(duckos_security_ingest(&engine, &e, &result) == DUCKOS_SECURITY_OK);
    e = event_make(1, 100, "net2", "h2", "s2", "p2", DUCKOS_SECURITY_NETWORK_CONNECT);
    (void)snprintf(e.indicator, sizeof(e.indicator), "%s", "ioc-demo");
    assert(duckos_security_ingest(&engine, &e, &result) == DUCKOS_SECURITY_OK);
    assert(result.distinct_hosts_in_cluster == 2);
    assert((result.indicators & DUCKOS_SECURITY_IND_CROSS_HOST_CLUSTER) != 0);
}
static void test_sequence_and_authorization(void) {
    duckos_security_engine engine;
    duckos_security_evaluation_v1 result;
    duckos_security_engine_init(&engine);
    duckos_security_event_v1 e = event_make(1, 200, "same", "h", "s", "p",
                                             DUCKOS_SECURITY_PROCESS_START);
    assert(duckos_security_ingest(&engine, &e, &result) == DUCKOS_SECURITY_OK);
    assert(duckos_security_ingest(&engine, &e, &result) == DUCKOS_SECURITY_DUPLICATE_EVENT);
    duckos_security_event_v1 older = event_make(2, 199, "older", "h", "s", "p",
                                                 DUCKOS_SECURITY_PROCESS_STOP);
    assert(duckos_security_ingest(&engine, &older, &result) == DUCKOS_SECURITY_OUT_OF_ORDER);

    duckos_security_authorization_request_v1 r;
    (void)memset(&r, 0, sizeof(r));
    r.struct_size = (uint32_t)sizeof(r);
    r.version = DUCKOS_SECURITY_ABI_VERSION;
    r.caller_trust = DUCKOS_SECURITY_TRUST_TRUSTED;
    r.flags = DUCKOS_SECURITY_AUTH_EVIDENCE_FRESH | DUCKOS_SECURITY_AUTH_POLICY_VALID;
    r.action = DUCKOS_SECURITY_OP_OBSERVE;
    r.granted_capabilities = DUCKOS_SECURITY_CAP_OBSERVE;
    assert(duckos_security_authorize(&r));
    r.caller_trust = DUCKOS_SECURITY_TRUST_UNTRUSTED;
    assert(!duckos_security_authorize(&r));
    r.caller_trust = DUCKOS_SECURITY_TRUST_TRUSTED;
    r.action = DUCKOS_SECURITY_OP_PROCESS_TERMINATE;
    r.granted_capabilities = DUCKOS_SECURITY_CAP_PROCESS_TERMINATE;
    assert(!duckos_security_authorize(&r));
    r.flags |= DUCKOS_SECURITY_AUTH_HUMAN_APPROVED;
    assert(duckos_security_authorize(&r));
    r.action = DUCKOS_SECURITY_OP_FILE_RESTORE;
    r.granted_capabilities = DUCKOS_SECURITY_CAP_FILE_RESTORE;
    assert(!duckos_security_authorize(&r));
    r.flags |= DUCKOS_SECURITY_AUTH_SNAPSHOT_AUTHENTICATED |
               DUCKOS_SECURITY_AUTH_CONTENT_VERIFIED |
               DUCKOS_SECURITY_AUTH_TARGET_AUTHORIZED;
    assert(duckos_security_authorize(&r));
    r.action = 999;
    assert(!duckos_security_authorize(&r));
}
int main(void) {
    test_trust_and_validation();
    test_file_burst_and_causal_chain();
    test_credential_lolbin_and_mesh_cluster();
    test_sequence_and_authorization();
    return 0;
}
