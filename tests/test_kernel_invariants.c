#include "invariants.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define CHECK(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "check failed at %s:%d: %s\n", __FILE__, __LINE__, #expression); \
        return 0; \
    } \
} while (0)

static int test_accounting_and_monotonic_clock(void) {
    CHECK(duckos_kernel_memory_accounting_valid(100u, 60u, 20u, 20u));
    CHECK(!duckos_kernel_memory_accounting_valid(100u, 60u, 20u, 19u));
    CHECK(!duckos_kernel_memory_accounting_valid(UINT64_MAX, UINT64_MAX, 1u, 0u));
    CHECK(!duckos_kernel_memory_accounting_valid(0u, 0u, 0u, 0u));
    CHECK(duckos_kernel_monotonic_step_valid(10u, 10u));
    CHECK(duckos_kernel_monotonic_step_valid(10u, 11u));
    CHECK(!duckos_kernel_monotonic_step_valid(11u, 10u));
    return 1;
}

static int test_resource_bounds_and_alignment(void) {
    CHECK(duckos_kernel_signed_resource_valid(0, 100u));
    CHECK(duckos_kernel_signed_resource_valid(100, 100u));
    CHECK(!duckos_kernel_signed_resource_valid(-1, 100u));
    CHECK(!duckos_kernel_signed_resource_valid(101, 100u));
    CHECK(duckos_kernel_percent_valid(0u));
    CHECK(duckos_kernel_percent_valid(100u));
    CHECK(!duckos_kernel_percent_valid(101u));
    CHECK(duckos_kernel_ratio_valid(4u, 5u));
    CHECK(!duckos_kernel_ratio_valid(6u, 5u));
    CHECK(!duckos_kernel_ratio_valid(0u, 0u));
    CHECK(duckos_kernel_queue_fits(8u, 8u));
    CHECK(!duckos_kernel_queue_fits(9u, 8u));
    CHECK(!duckos_kernel_queue_fits(0u, 0u));
    CHECK(duckos_kernel_aligned_range_valid(0x1000u, 0x2000u, 0x5000u, 0x1000u));
    CHECK(!duckos_kernel_aligned_range_valid(0x1001u, 0x2000u, 0x5000u, 0x1000u));
    CHECK(!duckos_kernel_aligned_range_valid(0x1000u, 0x5000u, 0x5000u, 0x1000u));
    CHECK(!duckos_kernel_aligned_range_valid(0x1000u, 0x1000u, 0x5000u, 3u));
    CHECK(duckos_kernel_slice_valid(100u, 90u, 10u));
    CHECK(!duckos_kernel_slice_valid(100u, 90u, 11u));
    CHECK(!duckos_kernel_slice_valid(100u, 101u, 0u));
    return 1;
}

static int test_wait_graph_and_retry_budget(void) {
    const duckos_kernel_wait_edge acyclic[] = {{0u, 1u}, {1u, 2u}, {0u, 3u}};
    const duckos_kernel_wait_edge cyclic[] = {{0u, 1u}, {1u, 2u}, {2u, 0u}};
    const duckos_kernel_wait_edge self_cycle[] = {{1u, 1u}};
    const duckos_kernel_wait_edge invalid[] = {{0u, 4u}};

    CHECK(duckos_kernel_wait_graph_acyclic(4u, acyclic, 3u));
    CHECK(!duckos_kernel_wait_graph_acyclic(3u, cyclic, 3u));
    CHECK(!duckos_kernel_wait_graph_acyclic(2u, self_cycle, 1u));
    CHECK(!duckos_kernel_wait_graph_acyclic(4u, invalid, 1u));
    CHECK(duckos_kernel_wait_graph_acyclic(0u, NULL, 0u));
    CHECK(!duckos_kernel_wait_graph_acyclic(65u, NULL, 0u));
    CHECK(!duckos_kernel_wait_graph_acyclic(2u, NULL, 1u));
    CHECK(duckos_kernel_retry_allowed(0u, 3u));
    CHECK(duckos_kernel_retry_allowed(2u, 3u));
    CHECK(!duckos_kernel_retry_allowed(3u, 3u));
    CHECK(!duckos_kernel_retry_allowed(0u, 0u));
    CHECK(duckos_kernel_frequency_slew_valid(100u, 110u, 10u));
    CHECK(!duckos_kernel_frequency_slew_valid(100u, 111u, 10u));
    return 1;
}

static int test_interrupt_security_and_identifiers(void) {
    const uint64_t ids[] = {7u, 11u, 19u};
    CHECK(duckos_kernel_interrupt_may_block(0, 1));
    CHECK(duckos_kernel_interrupt_may_block(1, 0));
    CHECK(!duckos_kernel_interrupt_may_block(1, 1));
    CHECK(!duckos_kernel_interrupt_may_block(2, 0));
    CHECK(duckos_kernel_rights_subset(0x03u, 0x07u));
    CHECK(!duckos_kernel_rights_subset(0x08u, 0x07u));
    CHECK(duckos_kernel_user_range_valid(0x1000u, 0x1000u, 0x8000u));
    CHECK(!duckos_kernel_user_range_valid(0x7000u, 0x2000u, 0x8000u));
    CHECK(!duckos_kernel_user_range_valid(0u, 1u, 0x8000u));
    CHECK(duckos_kernel_id_unique(23u, ids, 3u));
    CHECK(!duckos_kernel_id_unique(11u, ids, 3u));
    CHECK(!duckos_kernel_id_unique(0u, ids, 3u));
    CHECK(!duckos_kernel_id_unique(23u, NULL, 1u));
    CHECK(duckos_kernel_cacheline_separated(0x1000u, 0x1040u, 64u));
    CHECK(!duckos_kernel_cacheline_separated(0x1000u, 0x103fu, 64u));
    CHECK(!duckos_kernel_cacheline_separated(0x1000u, 0x2000u, 48u));
    return 1;
}

static int test_idempotent_transition_and_watchdog(void) {
    uint32_t state = 1u;
    CHECK(duckos_kernel_apply_transition(&state, 1u, 2u) ==
        DUCKOS_KERNEL_TRANSITION_APPLIED);
    CHECK(state == 2u);
    CHECK(duckos_kernel_apply_transition(&state, 1u, 2u) ==
        DUCKOS_KERNEL_TRANSITION_ALREADY_APPLIED);
    CHECK(state == 2u);
    CHECK(duckos_kernel_apply_transition(&state, 1u, 3u) ==
        DUCKOS_KERNEL_TRANSITION_INVALID);
    CHECK(duckos_kernel_apply_transition(NULL, 1u, 2u) ==
        DUCKOS_KERNEL_TRANSITION_INVALID);

    CHECK(duckos_kernel_watchdog_decide(100u, 110u, 20u, 0u, 3u) ==
        DUCKOS_KERNEL_WATCHDOG_HEALTHY);
    CHECK(duckos_kernel_watchdog_decide(100u, 120u, 20u, 0u, 3u) ==
        DUCKOS_KERNEL_WATCHDOG_RESTART);
    CHECK(duckos_kernel_watchdog_decide(100u, 120u, 20u, 3u, 3u) ==
        DUCKOS_KERNEL_WATCHDOG_ISOLATE);
    CHECK(duckos_kernel_watchdog_decide(120u, 100u, 20u, 0u, 3u) ==
        DUCKOS_KERNEL_WATCHDOG_CLOCK_ERROR);
    CHECK(duckos_kernel_watchdog_decide(100u, 120u, 0u, 0u, 3u) ==
        DUCKOS_KERNEL_WATCHDOG_CLOCK_ERROR);
    return 1;
}

static int test_smoothing_and_integrity(void) {
    uint64_t average = 0u;
    const char sample[] = "123456789";

    CHECK(duckos_kernel_average_step(100u, 0u, 10u, &average));
    CHECK(average == 90u);
    CHECK(duckos_kernel_average_step(90u, 100u, 10u, &average));
    CHECK(average == 91u);
    CHECK(!duckos_kernel_average_step(1u, 2u, 0u, &average));
    CHECK(!duckos_kernel_average_step(1u, 2u, 1u, NULL));
    CHECK(duckos_kernel_crc32(sample, strlen(sample)) == 0xcbf43926u);
    CHECK(duckos_kernel_crc32(NULL, 0u) == 0u);
    CHECK(duckos_kernel_crc32(NULL, 1u) == 0u);
    return 1;
}

int main(void) {
    if (!test_accounting_and_monotonic_clock() ||
        !test_resource_bounds_and_alignment() ||
        !test_wait_graph_and_retry_budget() ||
        !test_interrupt_security_and_identifiers() ||
        !test_idempotent_transition_and_watchdog() ||
        !test_smoothing_and_integrity()) {
        return 1;
    }
    puts("DuckOS kernel invariant tests passed");
    return 0;
}
