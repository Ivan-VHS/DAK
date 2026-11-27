#include "invariants.h"

#include <stdint.h>

static int add_overflow_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (result == NULL || left > UINT64_MAX - right) return 1;
    *result = left + right;
    return 0;
}

int duckos_kernel_memory_accounting_valid(
    uint64_t total,
    uint64_t free_pages,
    uint64_t allocated_pages,
    uint64_t reserved_pages
) {
    uint64_t accounted = 0u;
    if (total == 0u) return 0;
    if (add_overflow_u64(free_pages, allocated_pages, &accounted)) return 0;
    if (add_overflow_u64(accounted, reserved_pages, &accounted)) return 0;
    return accounted == total;
}

int duckos_kernel_monotonic_step_valid(uint64_t previous, uint64_t current) {
    return current >= previous;
}

int duckos_kernel_signed_resource_valid(int64_t value, uint64_t maximum) {
    return value >= 0 && (uint64_t)value <= maximum;
}

int duckos_kernel_percent_valid(uint32_t percent) {
    return percent <= 100u;
}

int duckos_kernel_ratio_valid(uint64_t numerator, uint64_t denominator) {
    return denominator != 0u && numerator <= denominator;
}

int duckos_kernel_queue_fits(uint64_t length, uint64_t capacity) {
    return capacity != 0u && length <= capacity;
}

int duckos_kernel_aligned_range_valid(
    uint64_t base,
    uint64_t bytes,
    uint64_t limit,
    uint64_t alignment
) {
    if (bytes == 0u || alignment == 0u) return 0;
    if ((alignment & (alignment - 1u)) != 0u) return 0;
    if ((base & (alignment - 1u)) != 0u) return 0;
    if (base > limit) return 0;
    if (bytes > limit - base) return 0;
    return 1;
}

int duckos_kernel_slice_valid(uint64_t total_bytes, uint64_t offset, uint64_t length) {
    if (offset > total_bytes) return 0;
    return length <= total_bytes - offset;
}

int duckos_kernel_retry_allowed(uint32_t attempts, uint32_t maximum_attempts) {
    return maximum_attempts != 0u && attempts < maximum_attempts;
}

int duckos_kernel_frequency_slew_valid(
    uint64_t current_value,
    uint64_t requested_value,
    uint64_t maximum_step
) {
    const uint64_t difference = current_value >= requested_value
        ? current_value - requested_value
        : requested_value - current_value;
    return difference <= maximum_step;
}

int duckos_kernel_wait_graph_acyclic(
    uint16_t node_count,
    const duckos_kernel_wait_edge *edges,
    uint16_t edge_count
) {
    uint16_t indegree[DUCKOS_KERNEL_MAX_WAIT_NODES] = {0u};
    uint16_t ready[DUCKOS_KERNEL_MAX_WAIT_NODES];
    uint16_t ready_head = 0u;
    uint16_t ready_tail = 0u;
    uint16_t processed = 0u;

    if (node_count > DUCKOS_KERNEL_MAX_WAIT_NODES ||
        edge_count > DUCKOS_KERNEL_MAX_WAIT_EDGES) {
        return 0;
    }
    if (edge_count != 0u && edges == NULL) return 0;
    if (node_count == 0u) return edge_count == 0u;

    for (uint16_t index = 0u; index < edge_count; ++index) {
        if (edges[index].from >= node_count || edges[index].to >= node_count) {
            return 0;
        }
        if (indegree[edges[index].to] == UINT16_MAX) return 0;
        ++indegree[edges[index].to];
    }

    for (uint16_t node = 0u; node < node_count; ++node) {
        if (indegree[node] == 0u) ready[ready_tail++] = node;
    }

    while (ready_head < ready_tail) {
        const uint16_t node = ready[ready_head++];
        ++processed;

        for (uint16_t index = 0u; index < edge_count; ++index) {
            if (edges[index].from != node) continue;
            const uint16_t target = edges[index].to;
            if (indegree[target] == 0u) return 0;
            --indegree[target];
            if (indegree[target] == 0u) {
                if (ready_tail >= DUCKOS_KERNEL_MAX_WAIT_NODES) return 0;
                ready[ready_tail++] = target;
            }
        }
    }

    return processed == node_count;
}

int duckos_kernel_interrupt_may_block(int in_interrupt, int operation_may_block) {
    if (in_interrupt != 0 && in_interrupt != 1) return 0;
    if (operation_may_block != 0 && operation_may_block != 1) return 0;
    return in_interrupt == 0 || operation_may_block == 0;
}

int duckos_kernel_rights_subset(uint64_t requested_rights, uint64_t available_rights) {
    return (requested_rights & ~available_rights) == 0u;
}

int duckos_kernel_user_range_valid(uint64_t base, uint64_t bytes, uint64_t user_limit) {
    if (base == 0u || bytes == 0u || base > user_limit) return 0;
    return bytes <= user_limit - base;
}

int duckos_kernel_id_unique(
    uint64_t candidate,
    const uint64_t *active_ids,
    size_t active_count
) {
    if (candidate == 0u || active_count > DUCKOS_KERNEL_MAX_IDS) return 0;
    if (active_count != 0u && active_ids == NULL) return 0;

    for (size_t index = 0u; index < active_count; ++index) {
        if (active_ids[index] == candidate) return 0;
    }
    return 1;
}

int duckos_kernel_cacheline_separated(
    uintptr_t left_address,
    uintptr_t right_address,
    size_t cache_line_bytes
) {
    if (cache_line_bytes == 0u ||
        (cache_line_bytes & (cache_line_bytes - 1u)) != 0u) {
        return 0;
    }
    return (left_address / cache_line_bytes) != (right_address / cache_line_bytes);
}

duckos_kernel_transition_result duckos_kernel_apply_transition(
    uint32_t *current_state,
    uint32_t expected_state,
    uint32_t next_state
) {
    if (current_state == NULL) return DUCKOS_KERNEL_TRANSITION_INVALID;
    if (*current_state == next_state) return DUCKOS_KERNEL_TRANSITION_ALREADY_APPLIED;
    if (*current_state != expected_state) return DUCKOS_KERNEL_TRANSITION_INVALID;
    *current_state = next_state;
    return DUCKOS_KERNEL_TRANSITION_APPLIED;
}

duckos_kernel_watchdog_action duckos_kernel_watchdog_decide(
    uint64_t last_heartbeat,
    uint64_t now,
    uint64_t timeout,
    uint32_t restart_count,
    uint32_t restart_limit
) {
    if (now < last_heartbeat || timeout == 0u) {
        return DUCKOS_KERNEL_WATCHDOG_CLOCK_ERROR;
    }
    if (now - last_heartbeat < timeout) {
        return DUCKOS_KERNEL_WATCHDOG_HEALTHY;
    }
    if (restart_count < restart_limit) return DUCKOS_KERNEL_WATCHDOG_RESTART;
    return DUCKOS_KERNEL_WATCHDOG_ISOLATE;
}

int duckos_kernel_average_step(
    uint64_t previous,
    uint64_t sample,
    uint64_t window,
    uint64_t *result
) {
    if (result == NULL || window == 0u) return 0;
    if (sample >= previous) {
        *result = previous + (sample - previous) / window;
    } else {
        *result = previous - (previous - sample) / window;
    }
    return 1;
}

uint32_t duckos_kernel_crc32(const void *data, size_t length) {
    if (data == NULL && length != 0u) return 0u;

    const uint8_t *bytes = (const uint8_t *)data;
    uint32_t crc = 0xffffffffu;
    for (size_t index = 0u; index < length; ++index) {
        crc ^= bytes[index];
        for (uint8_t bit = 0u; bit < 8u; ++bit) {
            const uint32_t mask = (uint32_t)-(int32_t)(crc & 1u);
            crc = (crc >> 1u) ^ (0xedb88320u & mask);
        }
    }
    return ~crc;
}
