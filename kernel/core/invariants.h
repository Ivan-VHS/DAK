#ifndef DUCKOS_KERNEL_INVARIANTS_H
#define DUCKOS_KERNEL_INVARIANTS_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_KERNEL_MAX_WAIT_NODES 64u
#define DUCKOS_KERNEL_MAX_WAIT_EDGES 256u
#define DUCKOS_KERNEL_MAX_IDS 512u
#define DUCKOS_KERNEL_CACHE_LINE_BYTES 64u

typedef struct duckos_kernel_wait_edge {
    uint16_t from;
    uint16_t to;
} duckos_kernel_wait_edge;

typedef enum duckos_kernel_watchdog_action {
    DUCKOS_KERNEL_WATCHDOG_HEALTHY = 0,
    DUCKOS_KERNEL_WATCHDOG_CLOCK_ERROR,
    DUCKOS_KERNEL_WATCHDOG_RESTART,
    DUCKOS_KERNEL_WATCHDOG_ISOLATE
} duckos_kernel_watchdog_action;

typedef enum duckos_kernel_transition_result {
    DUCKOS_KERNEL_TRANSITION_INVALID = 0,
    DUCKOS_KERNEL_TRANSITION_APPLIED,
    DUCKOS_KERNEL_TRANSITION_ALREADY_APPLIED
} duckos_kernel_transition_result;

/* Exact page/resource conservation: free + allocated + reserved == total. */
int duckos_kernel_memory_accounting_valid(
    uint64_t total,
    uint64_t free_pages,
    uint64_t allocated_pages,
    uint64_t reserved_pages
);

/* A monotonic counter may stay equal or advance, but must never go backwards. */
int duckos_kernel_monotonic_step_valid(uint64_t previous, uint64_t current);

int duckos_kernel_signed_resource_valid(int64_t value, uint64_t maximum);
int duckos_kernel_percent_valid(uint32_t percent);
int duckos_kernel_ratio_valid(uint64_t numerator, uint64_t denominator);
int duckos_kernel_queue_fits(uint64_t length, uint64_t capacity);

/* Validate an exclusive-upper-bound range and its required alignment. */
int duckos_kernel_aligned_range_valid(
    uint64_t base,
    uint64_t bytes,
    uint64_t limit,
    uint64_t alignment
);

int duckos_kernel_slice_valid(uint64_t total_bytes, uint64_t offset, uint64_t length);
int duckos_kernel_retry_allowed(uint32_t attempts, uint32_t maximum_attempts);
int duckos_kernel_frequency_slew_valid(
    uint64_t current_value,
    uint64_t requested_value,
    uint64_t maximum_step
);

/* Kahn topological check. Node identifiers are dense values in [0, node_count). */
int duckos_kernel_wait_graph_acyclic(
    uint16_t node_count,
    const duckos_kernel_wait_edge *edges,
    uint16_t edge_count
);

int duckos_kernel_interrupt_may_block(int in_interrupt, int operation_may_block);
int duckos_kernel_rights_subset(uint64_t requested_rights, uint64_t available_rights);
int duckos_kernel_user_range_valid(uint64_t base, uint64_t bytes, uint64_t user_limit);
int duckos_kernel_id_unique(
    uint64_t candidate,
    const uint64_t *active_ids,
    size_t active_count
);

int duckos_kernel_cacheline_separated(
    uintptr_t left_address,
    uintptr_t right_address,
    size_t cache_line_bytes
);

duckos_kernel_transition_result duckos_kernel_apply_transition(
    uint32_t *current_state,
    uint32_t expected_state,
    uint32_t next_state
);

duckos_kernel_watchdog_action duckos_kernel_watchdog_decide(
    uint64_t last_heartbeat,
    uint64_t now,
    uint64_t timeout,
    uint32_t restart_count,
    uint32_t restart_limit
);

/* Deterministic integer smoothing. Returns zero for an invalid window. */
int duckos_kernel_average_step(
    uint64_t previous,
    uint64_t sample,
    uint64_t window,
    uint64_t *result
);

/* CRC-32/ISO-HDLC for accidental corruption detection, not authentication. */
uint32_t duckos_kernel_crc32(const void *data, size_t length);

#ifdef __cplusplus
}
#endif

#endif
