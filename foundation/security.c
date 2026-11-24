#include "security.h"

#include <string.h>

static int string_ok(const char *text, size_t capacity, int required) {
    const char *end = (const char *)memchr(text, '\0', capacity);
    return end != NULL && (!required || end != text);
}

static void copy_text(char *destination, size_t capacity, const char *source) {
    size_t length = strlen(source);
    if (length >= capacity) length = capacity - 1u;
    (void)memcpy(destination, source, length);
    destination[length] = '\0';
}
static int same(const char *a, const char *b) { return strcmp(a, b) == 0; }
static int file_kind(uint32_t k) {
    return k == DUCKOS_SECURITY_FILE_MODIFY ||
           k == DUCKOS_SECURITY_FILE_DELETE ||
           k == DUCKOS_SECURITY_FILE_RENAME;
}
static int time_in_window(uint64_t newer, uint64_t older, uint64_t window) {
    return newer >= older && newer - older <= window;
}
static void at(const duckos_security_engine *e, size_t n,
               const duckos_security_event_v1 **out) {
    size_t oldest = (e->next_write + DUCKOS_SECURITY_EVENT_CAPACITY - e->count) %
                    DUCKOS_SECURITY_EVENT_CAPACITY;
    *out = &e->events[(oldest + n) % DUCKOS_SECURITY_EVENT_CAPACITY];
}
static const duckos_security_event_v1 *find_id(
    const duckos_security_engine *e, const char *id) {
    for (size_t i = 0; i < e->count; ++i) {
        const duckos_security_event_v1 *candidate;
        at(e, i, &candidate);
        if (same(candidate->event_id, id)) return candidate;
    }
    return NULL;
}
static void signal(duckos_security_evaluation_v1 *v, uint64_t bit, uint32_t points) {
    v->indicators |= bit;
    v->risk_score = points > 100u - v->risk_score ? 100u : v->risk_score + points;
}
static int is_lolbin(const char *name) {
    static const char *const names[] = {
        "powershell.exe", "pwsh.exe", "cmd.exe", "wscript.exe", "cscript.exe",
        "mshta.exe", "rundll32.exe", "regsvr32.exe", "certutil.exe",
        "bitsadmin.exe", "msiexec.exe", "wmic.exe", "installutil.exe"
    };
    for (size_t i = 0; i < sizeof(names) / sizeof(names[0]); ++i)
        if (same(name, names[i])) return 1;
    return 0;
}

void duckos_security_engine_init(duckos_security_engine *engine) {
    if (engine != NULL) (void)memset(engine, 0, sizeof(*engine));
}

duckos_security_status duckos_security_event_validate(const duckos_security_event_v1 *e) {
    if (e == NULL) return DUCKOS_SECURITY_INVALID_ARGUMENT;
    if (e->struct_size < sizeof(*e) || e->version != DUCKOS_SECURITY_ABI_VERSION)
        return DUCKOS_SECURITY_UNSUPPORTED_VERSION;
    if (e->kind < DUCKOS_SECURITY_PROCESS_START ||
        e->kind > DUCKOS_SECURITY_DRIVER_LOAD ||
        e->source_trust > DUCKOS_SECURITY_TRUST_TRUSTED ||
        (e->flags & ~DUCKOS_SECURITY_KNOWN_EVENT_FLAGS) != 0u ||
        e->sequence == 0u || e->monotonic_ns == 0u || e->entropy_delta_bp > 10000u ||
        !string_ok(e->event_id, sizeof(e->event_id), 1) ||
        !string_ok(e->host_id, sizeof(e->host_id), 1) ||
        !string_ok(e->source_id, sizeof(e->source_id), 1) ||
        !string_ok(e->actor_id, sizeof(e->actor_id), 1) ||
        !string_ok(e->object_id, sizeof(e->object_id), 0) ||
        !string_ok(e->parent_event_id, sizeof(e->parent_event_id), 0) ||
        !string_ok(e->indicator, sizeof(e->indicator), 0) ||
        !string_ok(e->image_name, sizeof(e->image_name), 0))
        return DUCKOS_SECURITY_INVALID_EVENT;
    return DUCKOS_SECURITY_OK;
}

duckos_security_status duckos_security_ingest(
    duckos_security_engine *engine,
    const duckos_security_event_v1 *e,
    duckos_security_evaluation_v1 *out
) {
    if (engine == NULL || e == NULL || out == NULL)
        return DUCKOS_SECURITY_INVALID_ARGUMENT;
    duckos_security_status status = duckos_security_event_validate(e);
    if (status != DUCKOS_SECURITY_OK) return status;
    if (e->source_trust != DUCKOS_SECURITY_TRUST_TRUSTED)
        return DUCKOS_SECURITY_UNTRUSTED_SOURCE;

    for (size_t i = 0; i < engine->count; ++i) {
        const duckos_security_event_v1 *prev;
        at(engine, i, &prev);
        if (same(prev->event_id, e->event_id)) return DUCKOS_SECURITY_DUPLICATE_EVENT;
        if (same(prev->host_id, e->host_id)) {
            if (e->monotonic_ns < prev->monotonic_ns ||
                (same(prev->source_id, e->source_id) && e->sequence <= prev->sequence))
                return DUCKOS_SECURITY_OUT_OF_ORDER;
        }
    }

    duckos_security_evaluation_v1 v;
    (void)memset(&v, 0, sizeof(v));
    v.struct_size = (uint32_t)sizeof(v);
    v.version = DUCKOS_SECURITY_ABI_VERSION;
    v.advisory_only = 1u;
    copy_text(v.event_id, sizeof(v.event_id), e->event_id);

    engine->events[engine->next_write] = *e;
    engine->next_write = (engine->next_write + 1u) % DUCKOS_SECURITY_EVENT_CAPACITY;
    if (engine->count < DUCKOS_SECURITY_EVENT_CAPACITY) ++engine->count;

    if (e->kind == DUCKOS_SECURITY_PROCESS_INJECT)
        signal(&v, DUCKOS_SECURITY_IND_PROCESS_INJECTION, 50u);
    if (e->kind == DUCKOS_SECURITY_MEMORY_READ &&
        (e->flags & DUCKOS_SECURITY_FLAG_SENSITIVE_TARGET) != 0u &&
        (e->flags & DUCKOS_SECURITY_FLAG_AUTHORIZED) == 0u)
        signal(&v, DUCKOS_SECURITY_IND_SENSITIVE_MEMORY_READ, 45u);
    if (e->kind == DUCKOS_SECURITY_IDENTITY_ACCESS &&
        (e->flags & DUCKOS_SECURITY_FLAG_CREDENTIAL_MATERIAL) != 0u &&
        (e->flags & DUCKOS_SECURITY_FLAG_AUTHORIZED) == 0u)
        signal(&v, DUCKOS_SECURITY_IND_CREDENTIAL_ACCESS, 60u);
    if (e->kind == DUCKOS_SECURITY_INTEGRITY_CHANGE &&
        (e->flags & DUCKOS_SECURITY_FLAG_PROTECTED_COMPONENT) != 0u)
        signal(&v, DUCKOS_SECURITY_IND_PROTECTED_TAMPERING, 60u);
    if (e->kind == DUCKOS_SECURITY_DRIVER_LOAD &&
        (e->flags & DUCKOS_SECURITY_FLAG_SIGNATURE_VERIFIED) == 0u)
        signal(&v, DUCKOS_SECURITY_IND_UNVERIFIED_DRIVER, 45u);

    if (file_kind(e->kind)) {
        uint32_t mutations = 0u;
        for (size_t i = 0; i < engine->count; ++i) {
            const duckos_security_event_v1 *candidate;
            at(engine, i, &candidate);
            if (file_kind(candidate->kind) && same(candidate->host_id, e->host_id) &&
                same(candidate->actor_id, e->actor_id) &&
                time_in_window(e->monotonic_ns, candidate->monotonic_ns,
                               DUCKOS_SECURITY_WINDOW_NS))
                ++mutations;
        }
        v.file_mutations_in_window = mutations;
        if (mutations >= 3u) {
            uint32_t points = mutations >= 7u ? 30u : 10u + (mutations - 3u) * 5u;
            signal(&v, DUCKOS_SECURITY_IND_FILE_MUTATION_BURST, points);
        }
        if (e->entropy_delta_bp >= 5000u)
            signal(&v, DUCKOS_SECURITY_IND_HIGH_ENTROPY_CHANGE, 25u);
        else if (e->entropy_delta_bp >= 2500u)
            signal(&v, DUCKOS_SECURITY_IND_ENTROPY_CHANGE, 12u);
    }

    if (e->kind == DUCKOS_SECURITY_NETWORK_CONNECT) {
        if ((e->flags & DUCKOS_SECURITY_FLAG_DESTINATION_MALICIOUS) != 0u)
            signal(&v, DUCKOS_SECURITY_IND_MALICIOUS_DESTINATION, 60u);
        if ((e->flags & DUCKOS_SECURITY_FLAG_BEACON_PERIODIC) != 0u && e->repeat_count >= 4u)
            signal(&v, DUCKOS_SECURITY_IND_PERIODIC_BEACON, 20u);
    }

    if (e->kind == DUCKOS_SECURITY_PROCESS_START) {
        const uint32_t context = DUCKOS_SECURITY_FLAG_ENCODED_COMMAND |
            DUCKOS_SECURITY_FLAG_HIDDEN_WINDOW | DUCKOS_SECURITY_FLAG_USER_WRITABLE_ORIGIN |
            DUCKOS_SECURITY_FLAG_UNEXPECTED_PARENT | DUCKOS_SECURITY_FLAG_NETWORK_CHILD;
        if (is_lolbin(e->image_name) && (e->flags & context) != 0u)
            signal(&v, DUCKOS_SECURITY_IND_LOLBIN_CONTEXT, 25u);
        if ((e->flags & DUCKOS_SECURITY_FLAG_ORIGIN_UNTRUSTED) != 0u)
            signal(&v, DUCKOS_SECURITY_IND_UNTRUSTED_ORIGIN, 25u);
        if ((e->flags & DUCKOS_SECURITY_FLAG_SUSPICIOUS_CHAIN) != 0u)
            signal(&v, DUCKOS_SECURITY_IND_SUSPICIOUS_CHAIN, 25u);
    }

    if (e->indicator[0] != '\0' && e->observed_at_ms != 0u) {
        char hosts[DUCKOS_SECURITY_EVENT_CAPACITY][64];
        size_t host_count = 0u;
        for (size_t i = 0; i < engine->count; ++i) {
            const duckos_security_event_v1 *candidate;
            at(engine, i, &candidate);
            if (candidate->indicator[0] == '\0' || !same(candidate->indicator, e->indicator))
                continue;
            uint64_t low = e->observed_at_ms < candidate->observed_at_ms ?
                e->observed_at_ms : candidate->observed_at_ms;
            uint64_t high = e->observed_at_ms < candidate->observed_at_ms ?
                candidate->observed_at_ms : e->observed_at_ms;
            if (high - low > DUCKOS_SECURITY_MESH_WINDOW_MS) continue;
            int found = 0;
            for (size_t j = 0; j < host_count; ++j)
                if (same(hosts[j], candidate->host_id)) found = 1;
            if (!found && host_count < DUCKOS_SECURITY_EVENT_CAPACITY) {
                copy_text(hosts[host_count], sizeof(hosts[host_count]), candidate->host_id);
                ++host_count;
            }
        }
        int found_current = 0;
        for (size_t j = 0; j < host_count; ++j)
            if (same(hosts[j], e->host_id)) found_current = 1;
        if (!found_current && host_count < DUCKOS_SECURITY_EVENT_CAPACITY) ++host_count;
        v.distinct_hosts_in_cluster = (uint32_t)host_count;
        if (host_count >= 4u)
            signal(&v, DUCKOS_SECURITY_IND_MULTI_HOST_CLUSTER, 25u);
        else if (host_count >= 2u)
            signal(&v, DUCKOS_SECURITY_IND_CROSS_HOST_CLUSTER, 12u);
    }

    copy_text(v.causal_root_event_id, sizeof(v.causal_root_event_id), e->event_id);
    v.causal_depth = 1u;
    const duckos_security_event_v1 *cursor = e;
    char visited[DUCKOS_SECURITY_CAUSAL_DEPTH][64];
    copy_text(visited[0], sizeof(visited[0]), e->event_id);
    while (cursor->parent_event_id[0] != '\0' && v.causal_depth < DUCKOS_SECURITY_CAUSAL_DEPTH) {
        const duckos_security_event_v1 *parent = find_id(engine, cursor->parent_event_id);
        if (parent == NULL || !same(parent->host_id, e->host_id) ||
            parent->monotonic_ns > cursor->monotonic_ns ||
            !time_in_window(cursor->monotonic_ns, parent->monotonic_ns,
                            DUCKOS_SECURITY_WINDOW_NS))
            break;
        int cycle = 0;
        for (size_t j = 0; j < v.causal_depth; ++j)
            if (same(visited[j], parent->event_id)) cycle = 1;
        if (cycle) break;
        copy_text(visited[v.causal_depth], sizeof(visited[v.causal_depth]), parent->event_id);
        ++v.causal_depth;
        copy_text(v.causal_root_event_id, sizeof(v.causal_root_event_id), parent->event_id);
        cursor = parent;
    }

    unsigned indicators = 0u;
    for (uint64_t bits = v.indicators; bits != 0u; bits >>= 1u)
        if ((bits & 1u) != 0u) ++indicators;
    v.confidence_milli = indicators == 0u ? 250u :
        (550u + indicators * 70u > 980u ? 980u : 550u + indicators * 70u);

    if (v.risk_score >= 80u) {
        v.risk_level = DUCKOS_SECURITY_RISK_CRITICAL;
        v.recommendation = DUCKOS_SECURITY_ACTION_BLOCK;
    } else if (v.risk_score >= 60u) {
        v.risk_level = DUCKOS_SECURITY_RISK_HIGH;
        v.recommendation = DUCKOS_SECURITY_ACTION_ISOLATE;
    } else if (v.risk_score >= 35u) {
        v.risk_level = DUCKOS_SECURITY_RISK_HIGH;
        v.recommendation = DUCKOS_SECURITY_ACTION_RESTRICT;
    } else if (v.risk_score >= 20u) {
        v.risk_level = DUCKOS_SECURITY_RISK_MEDIUM;
        v.recommendation = DUCKOS_SECURITY_ACTION_SANDBOX;
    } else {
        v.risk_level = DUCKOS_SECURITY_RISK_LOW;
        v.recommendation = DUCKOS_SECURITY_ACTION_MONITOR;
    }
    v.sandbox_recommended =
        (e->flags & DUCKOS_SECURITY_FLAG_ORIGIN_UNTRUSTED) != 0u ||
        ((e->kind == DUCKOS_SECURITY_PROCESS_START ||
          e->kind == DUCKOS_SECURITY_DRIVER_LOAD) && v.risk_score >= 20u);
    v.snapshot_recommended =
        (file_kind(e->kind) &&
         (v.risk_score >= 20u || e->kind != DUCKOS_SECURITY_FILE_MODIFY));

    *out = v;
    return DUCKOS_SECURITY_OK;
}

static uint64_t capability_for(uint32_t action) {
    switch (action) {
        case DUCKOS_SECURITY_OP_OBSERVE: return DUCKOS_SECURITY_CAP_OBSERVE;
        case DUCKOS_SECURITY_OP_SNAPSHOT_CREATE: return DUCKOS_SECURITY_CAP_SNAPSHOT_CREATE;
        case DUCKOS_SECURITY_OP_INTEGRITY_VERIFY: return DUCKOS_SECURITY_CAP_INTEGRITY_VERIFY;
        case DUCKOS_SECURITY_OP_FILE_RESTORE: return DUCKOS_SECURITY_CAP_FILE_RESTORE;
        case DUCKOS_SECURITY_OP_PROCESS_ISOLATE: return DUCKOS_SECURITY_CAP_PROCESS_ISOLATE;
        case DUCKOS_SECURITY_OP_PROCESS_TERMINATE: return DUCKOS_SECURITY_CAP_PROCESS_TERMINATE;
        case DUCKOS_SECURITY_OP_NETWORK_ISOLATE: return DUCKOS_SECURITY_CAP_NETWORK_ISOLATE;
        case DUCKOS_SECURITY_OP_DRIVER_QUARANTINE: return DUCKOS_SECURITY_CAP_DRIVER_QUARANTINE;
        default: return 0u;
    }
}
int duckos_security_authorize(const duckos_security_authorization_request_v1 *r) {
    if (r == NULL || r->struct_size < sizeof(*r) ||
        r->version != DUCKOS_SECURITY_ABI_VERSION ||
        r->caller_trust != DUCKOS_SECURITY_TRUST_TRUSTED || r->reserved != 0u ||
        (r->flags & ~((1u << 6) - 1u)) != 0u)
        return 0;
    const uint32_t must = DUCKOS_SECURITY_AUTH_EVIDENCE_FRESH |
                          DUCKOS_SECURITY_AUTH_POLICY_VALID;
    if ((r->flags & must) != must) return 0;
    uint64_t cap = capability_for(r->action);
    if (cap == 0u || (r->granted_capabilities & cap) == 0u) return 0;
    if (r->action == DUCKOS_SECURITY_OP_FILE_RESTORE) {
        const uint32_t restore = DUCKOS_SECURITY_AUTH_SNAPSHOT_AUTHENTICATED |
            DUCKOS_SECURITY_AUTH_CONTENT_VERIFIED | DUCKOS_SECURITY_AUTH_TARGET_AUTHORIZED;
        if ((r->flags & restore) != restore) return 0;
    }
    if ((r->action == DUCKOS_SECURITY_OP_FILE_RESTORE ||
         r->action == DUCKOS_SECURITY_OP_PROCESS_ISOLATE ||
         r->action == DUCKOS_SECURITY_OP_PROCESS_TERMINATE ||
         r->action == DUCKOS_SECURITY_OP_NETWORK_ISOLATE ||
         r->action == DUCKOS_SECURITY_OP_DRIVER_QUARANTINE) &&
        (r->flags & DUCKOS_SECURITY_AUTH_HUMAN_APPROVED) == 0u)
        return 0;
    return 1;
}

const char *duckos_security_status_name(duckos_security_status status) {
    switch (status) {
        case DUCKOS_SECURITY_OK: return "ok";
        case DUCKOS_SECURITY_INVALID_ARGUMENT: return "invalid argument";
        case DUCKOS_SECURITY_UNSUPPORTED_VERSION: return "unsupported version";
        case DUCKOS_SECURITY_INVALID_EVENT: return "invalid event";
        case DUCKOS_SECURITY_UNTRUSTED_SOURCE: return "untrusted source";
        case DUCKOS_SECURITY_DUPLICATE_EVENT: return "duplicate event";
        case DUCKOS_SECURITY_OUT_OF_ORDER: return "out of order";
        default: return "unknown security status";
    }
}
