#include "capability_broker.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define SLOT_COUNT 8U
static duckos_capability_slot slots[SLOT_COUNT];
static const duckos_capability_principal authority = {1U, 1U};
static const duckos_capability_principal compositor = {2U, 1U};
static const duckos_capability_principal client = {3U, 4U};
static const duckos_capability_principal other_client = {4U, 2U};

static void init(duckos_capability_broker *broker) {
    assert(duckos_capability_broker_init(
        broker, slots, SLOT_COUNT, authority,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW |
        REAPER_SYSTEM_CAP_DESKTOP_DISPLAY |
        REAPER_SYSTEM_CAP_DESKTOP_DISPLAY_ADMIN |
        REAPER_SYSTEM_CAP_DESKTOP_GPU |
        REAPER_SYSTEM_CAP_DESKTOP_GPU_ADMIN |
        REAPER_SYSTEM_CAP_DESKTOP_COMPOSITOR |
        DUCKOS_CAPABILITY_BROKER_DELEGATE) == DUCKOS_CAPABILITY_OK);
}

static void test_issuer_and_subject_identity(void) {
    duckos_capability_broker broker;
    uint64_t token = 99U;
    init(&broker);
    assert(duckos_capability_issue(&broker, &compositor, &client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
        DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &token) == DUCKOS_CAPABILITY_DENIED);
    assert(token == 0U);
    assert(duckos_capability_issue(&broker, &authority, &client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
        DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &token) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, token,
        REAPER_SYSTEM_WINDOW_CREATE, 0U, 0U) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &other_client, token,
        REAPER_SYSTEM_WINDOW_CREATE, 0U, 0U) == DUCKOS_CAPABILITY_DENIED);
}

static void test_domain_and_scope_validation(void) {
    duckos_capability_broker broker;
    uint64_t token = 0U;
    init(&broker);
    assert(duckos_capability_issue(&broker, &authority, &client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_DISPLAY,
        DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &token) ==
        DUCKOS_CAPABILITY_INVALID_ARGUMENT);
    assert(token == 0U);
    assert(duckos_capability_issue(&broker, &authority, &client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_INVALID,
        DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &token) ==
        DUCKOS_CAPABILITY_INVALID_ARGUMENT);
    assert(duckos_capability_issue(&broker, &authority, &client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
        DUCKOS_CAPABILITY_SCOPE_OBJECT, 0U, 0U, &token) ==
        DUCKOS_CAPABILITY_INVALID_ARGUMENT);
}

static void test_object_scope_and_generation(void) {
    duckos_capability_broker broker;
    uint64_t token = 0U;
    init(&broker);
    assert(duckos_capability_issue(&broker, &authority, &client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
        DUCKOS_CAPABILITY_SCOPE_OBJECT, 44U, 3U, &token) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, token,
        REAPER_SYSTEM_WINDOW_FOCUS, 44U, 3U) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, token,
        REAPER_SYSTEM_WINDOW_FOCUS, 45U, 3U) == DUCKOS_CAPABILITY_RESOURCE_MISMATCH);
    assert(duckos_capability_authorize(&broker, &client, token,
        REAPER_SYSTEM_WINDOW_FOCUS, 44U, 4U) == DUCKOS_CAPABILITY_RESOURCE_MISMATCH);
    assert(duckos_capability_authorize(&broker, &client, token,
        REAPER_SYSTEM_GPU_SUBMIT, 44U, 3U) == DUCKOS_CAPABILITY_DENIED);
}

static void test_admin_rights_are_separate(void) {
    duckos_capability_broker broker;
    uint64_t display = 0U, gpu = 0U;
    init(&broker);
    assert(duckos_capability_issue(&broker, &authority, &client,
        REAPER_SYSTEM_CAP_DESKTOP_DISPLAY, REAPER_SYSTEM_DOMAIN_DESKTOP_DISPLAY,
        DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &display) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, display,
        REAPER_SYSTEM_DISPLAY_QUERY, 0U, 0U) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, display,
        REAPER_SYSTEM_DISPLAY_SET_MODE, 0U, 0U) == DUCKOS_CAPABILITY_DENIED);

    assert(duckos_capability_issue(&broker, &authority, &client,
        REAPER_SYSTEM_CAP_DESKTOP_GPU, REAPER_SYSTEM_DOMAIN_DESKTOP_GPU,
        DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &gpu) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, gpu,
        REAPER_SYSTEM_GPU_SUBMIT, 0U, 0U) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, gpu,
        REAPER_SYSTEM_GPU_RESET, 0U, 0U) == DUCKOS_CAPABILITY_DENIED);
}

static void test_attenuation_and_parent_revocation(void) {
    duckos_capability_broker broker;
    uint64_t parent = 0U, child = 0U, denied_child = 0U;
    init(&broker);
    assert(duckos_capability_issue(&broker, &authority, &compositor,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW | DUCKOS_CAPABILITY_BROKER_DELEGATE,
        REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW, DUCKOS_CAPABILITY_SCOPE_GLOBAL,
        0U, 0U, &parent) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_attenuate(&broker, &compositor, parent, &client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
        DUCKOS_CAPABILITY_SCOPE_OBJECT, 44U, 3U, &child) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, child,
        REAPER_SYSTEM_WINDOW_FOCUS, 44U, 3U) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, child,
        REAPER_SYSTEM_WINDOW_FOCUS, 45U, 3U) == DUCKOS_CAPABILITY_RESOURCE_MISMATCH);

    assert(duckos_capability_attenuate(&broker, &client, child, &other_client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
        DUCKOS_CAPABILITY_SCOPE_OBJECT, 44U, 3U, &denied_child) == DUCKOS_CAPABILITY_NOT_DELEGABLE);

    assert(duckos_capability_revoke(&broker, &authority, parent) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, child,
        REAPER_SYSTEM_WINDOW_FOCUS, 44U, 3U) == DUCKOS_CAPABILITY_DENIED);
}

static void test_rights_escalation_and_stale_tokens(void) {
    duckos_capability_broker broker;
    uint64_t parent = 0U, child = 0U;
    init(&broker);
    assert(duckos_capability_issue(&broker, &authority, &compositor,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW | DUCKOS_CAPABILITY_BROKER_DELEGATE,
        REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW, DUCKOS_CAPABILITY_SCOPE_GLOBAL,
        0U, 0U, &parent) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_attenuate(&broker, &compositor, parent, &client,
        REAPER_SYSTEM_CAP_DESKTOP_GPU, REAPER_SYSTEM_DOMAIN_DESKTOP_GPU,
        DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &child) ==
        DUCKOS_CAPABILITY_RIGHTS_ESCALATION);
    assert(child == 0U);
    assert(duckos_capability_revoke(&broker, &authority, parent) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &compositor, parent,
        REAPER_SYSTEM_WINDOW_CREATE, 0U, 0U) == DUCKOS_CAPABILITY_STALE_TOKEN);
    {
        uint64_t replacement = 0U;
        assert(duckos_capability_issue(&broker, &authority, &compositor,
            REAPER_SYSTEM_CAP_DESKTOP_WINDOW,
            REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
            DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &replacement) ==
            DUCKOS_CAPABILITY_OK);
        assert(replacement != parent);
        assert(duckos_capability_authorize(&broker, &compositor, parent,
            REAPER_SYSTEM_WINDOW_CREATE, 0U, 0U) == DUCKOS_CAPABILITY_STALE_TOKEN);
        assert(duckos_capability_authorize(&broker, &compositor, replacement,
            REAPER_SYSTEM_WINDOW_CREATE, 0U, 0U) == DUCKOS_CAPABILITY_OK);
    }
}

static void test_unknown_operation_and_capacity(void) {
    duckos_capability_broker broker;
    uint64_t token = 0U;
    uint32_t index;
    init(&broker);
    assert(duckos_capability_issue(&broker, &authority, &client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
        DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &token) == DUCKOS_CAPABILITY_OK);
    assert(duckos_capability_authorize(&broker, &client, token,
        (ReaperSystemOperation)0x7fff, 0U, 0U) == DUCKOS_CAPABILITY_UNKNOWN_OPERATION);
    for (index = 1U; index < SLOT_COUNT; ++index) {
        assert(duckos_capability_issue(&broker, &authority, &other_client,
            REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
            DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &token) == DUCKOS_CAPABILITY_OK);
    }
    assert(duckos_capability_issue(&broker, &authority, &other_client,
        REAPER_SYSTEM_CAP_DESKTOP_WINDOW, REAPER_SYSTEM_DOMAIN_DESKTOP_WINDOW,
        DUCKOS_CAPABILITY_SCOPE_GLOBAL, 0U, 0U, &token) == DUCKOS_CAPABILITY_TABLE_FULL);
}

int main(void) {
    test_issuer_and_subject_identity();
    test_domain_and_scope_validation();
    test_object_scope_and_generation();
    test_admin_rights_are_separate();
    test_attenuation_and_parent_revocation();
    test_rights_escalation_and_stale_tokens();
    test_unknown_operation_and_capacity();
    assert(strcmp(duckos_capability_status_name(DUCKOS_CAPABILITY_DENIED),
                  "denied") == 0);
    puts("DuckOS capability broker tests passed");
    return 0;
}
