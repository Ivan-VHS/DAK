#include "scheduler.h"

#include <limits.h>

typedef struct {
    uint64_t irq_state;
} duckos_sched_lock_state;

static duckos_sched_lock_state scheduler_lock(duckos_scheduler *scheduler) {
    duckos_sched_lock_state state = {0U};
    if (scheduler->platform.irq_save != NULL)
        state.irq_state = scheduler->platform.irq_save(scheduler->platform.irq_context);
    while (atomic_flag_test_and_set_explicit(&scheduler->lock, memory_order_acquire)) {
        atomic_signal_fence(memory_order_seq_cst);
    }
    return state;
}

static void scheduler_unlock(
    duckos_scheduler *scheduler, duckos_sched_lock_state state
) {
    atomic_flag_clear_explicit(&scheduler->lock, memory_order_release);
    if (scheduler->platform.irq_restore != NULL)
        scheduler->platform.irq_restore(scheduler->platform.irq_context, state.irq_state);
}

static void scheduler_unlock_keep_interrupts(duckos_scheduler *scheduler) {
    atomic_flag_clear_explicit(&scheduler->lock, memory_order_release);
}

static uint64_t valid_cpu_mask(uint32_t cpu_count) {
    return cpu_count == 64U ? UINT64_MAX : ((UINT64_C(1) << cpu_count) - UINT64_C(1));
}

static size_t find_thread(const duckos_scheduler *scheduler, uint64_t tid) {
    for (size_t i = 0U; i < scheduler->thread_count; ++i)
        if (scheduler->threads[i].tid == tid) return i;
    return scheduler->thread_count;
}

static uint64_t effective_deadline(uint64_t deadline_ns) {
    return deadline_ns == 0U ? UINT64_MAX : deadline_ns;
}

static int thread_transition_valid(
    duckos_thread_state current, duckos_thread_state next
) {
    switch (current) {
    case DUCKOS_THREAD_CREATED:
        return next == DUCKOS_THREAD_READY;
    case DUCKOS_THREAD_READY:
        return next == DUCKOS_THREAD_RUNNING || next == DUCKOS_THREAD_ZOMBIE;
    case DUCKOS_THREAD_RUNNING:
        return next == DUCKOS_THREAD_READY || next == DUCKOS_THREAD_BLOCKED ||
               next == DUCKOS_THREAD_SLEEPING || next == DUCKOS_THREAD_ZOMBIE;
    case DUCKOS_THREAD_BLOCKED:
    case DUCKOS_THREAD_SLEEPING:
        return next == DUCKOS_THREAD_READY || next == DUCKOS_THREAD_ZOMBIE;
    case DUCKOS_THREAD_ZOMBIE:
    default:
        return 0;
    }
}

static int core_transition_valid(duckos_cpu_state current, duckos_cpu_state next) {
    if (current == DUCKOS_CPU_OFFLINE) return next == DUCKOS_CPU_STARTING;
    if (current == DUCKOS_CPU_STARTING)
        return next == DUCKOS_CPU_ONLINE || next == DUCKOS_CPU_FAILED ||
               next == DUCKOS_CPU_OFFLINE;
    if (current == DUCKOS_CPU_ONLINE)
        return next == DUCKOS_CPU_DRAINING || next == DUCKOS_CPU_QUARANTINED ||
               next == DUCKOS_CPU_FAILED;
    if (current == DUCKOS_CPU_DRAINING)
        return next == DUCKOS_CPU_OFFLINE || next == DUCKOS_CPU_ONLINE ||
               next == DUCKOS_CPU_FAILED;
    if (current == DUCKOS_CPU_QUARANTINED)
        return next == DUCKOS_CPU_OFFLINE || next == DUCKOS_CPU_STARTING;
    return 0;
}

static duckos_cpu_local *cpu_at(duckos_scheduler *scheduler, uint32_t logical_id) {
    if (logical_id >= scheduler->cpu_count) return NULL;
    return &scheduler->cpus[logical_id];
}

duckos_sched_status duckos_scheduler_init(
    duckos_scheduler *scheduler, uint32_t cpu_count,
    uint32_t generation, const duckos_sched_platform *platform
) {
    if (scheduler == NULL || cpu_count == 0U ||
        cpu_count > DUCKOS_PROCESSOR_MAX_CPUS || generation == 0U)
        return DUCKOS_SCHED_INVALID_ARGUMENT;
    if (platform != NULL &&
        ((platform->irq_save == NULL) != (platform->irq_restore == NULL)))
        return DUCKOS_SCHED_INVALID_ARGUMENT;

    unsigned char *storage = (unsigned char *)scheduler;
    for (size_t i = 0U; i < sizeof(*scheduler); ++i) storage[i] = 0U;
    atomic_flag_clear_explicit(&scheduler->lock, memory_order_release);
    if (platform != NULL) scheduler->platform = *platform;
    scheduler->cpu_count = cpu_count;
    scheduler->generation = generation;
    for (uint32_t i = 0U; i < cpu_count; ++i) {
        scheduler->cpus[i].logical_id = i;
        scheduler->cpus[i].generation = generation;
        scheduler->cpus[i].state = DUCKOS_CPU_OFFLINE;
    }
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_bootstrap_cpu(
    duckos_scheduler *scheduler, uint32_t logical_id
) {
    if (scheduler == NULL || logical_id != 0U)
        return DUCKOS_SCHED_INVALID_ARGUMENT;
    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    duckos_cpu_local *cpu = cpu_at(scheduler, logical_id);
    if (cpu == NULL || cpu->state != DUCKOS_CPU_OFFLINE) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_INVALID_STATE;
    }
    cpu->state = DUCKOS_CPU_ONLINE;
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_begin_cpu_start(
    duckos_scheduler *scheduler, uint32_t logical_id
) {
    if (scheduler == NULL) return DUCKOS_SCHED_INVALID_ARGUMENT;
    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    duckos_cpu_local *cpu = cpu_at(scheduler, logical_id);
    if (cpu == NULL || logical_id == 0U ||
        scheduler->cpus[0].state != DUCKOS_CPU_ONLINE ||
        !core_transition_valid(cpu->state, DUCKOS_CPU_STARTING)) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_INVALID_STATE;
    }
    cpu->state = DUCKOS_CPU_STARTING;
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_complete_cpu_start(
    duckos_scheduler *scheduler, uint32_t logical_id,
    const duckos_ap_startup_evidence *evidence
) {
    if (scheduler == NULL || evidence == NULL)
        return DUCKOS_SCHED_INVALID_ARGUMENT;
    if (evidence->gdt_ready == 0U || evidence->idt_ready == 0U ||
        evidence->per_cpu_ready == 0U || evidence->stack_ready == 0U ||
        evidence->local_controller_ready == 0U ||
        evidence->trampoline_ready == 0U)
        return DUCKOS_SCHED_STARTUP_INCOMPLETE;

    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    duckos_cpu_local *cpu = cpu_at(scheduler, logical_id);
    if (cpu == NULL || logical_id == 0U ||
        scheduler->cpus[0].state != DUCKOS_CPU_ONLINE ||
        cpu->state != DUCKOS_CPU_STARTING) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_INVALID_STATE;
    }
    cpu->state = DUCKOS_CPU_ONLINE;
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_begin_cpu_drain(
    duckos_scheduler *scheduler, uint32_t logical_id
) {
    if (scheduler == NULL) return DUCKOS_SCHED_INVALID_ARGUMENT;
    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    duckos_cpu_local *cpu = cpu_at(scheduler, logical_id);
    if (cpu == NULL || logical_id == 0U ||
        !core_transition_valid(cpu->state, DUCKOS_CPU_DRAINING)) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_INVALID_STATE;
    }
    cpu->state = DUCKOS_CPU_DRAINING;
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_update_cpu_critical(
    duckos_scheduler *scheduler, uint32_t logical_id,
    uint32_t interrupt_depth, uint32_t lock_depth,
    uint32_t preempt_depth, uint32_t dma_leases
) {
    if (scheduler == NULL) return DUCKOS_SCHED_INVALID_ARGUMENT;
    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    duckos_cpu_local *cpu = cpu_at(scheduler, logical_id);
    if (cpu == NULL) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_INVALID_ARGUMENT;
    }
    cpu->interrupt_depth = interrupt_depth;
    cpu->lock_depth = lock_depth;
    cpu->preempt_depth = preempt_depth;
    cpu->dma_leases = dma_leases;
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

static int core_offline_allowed_locked(
    const duckos_scheduler *scheduler, uint32_t logical_id
) {
    if (logical_id >= scheduler->cpu_count) return 0;
    const duckos_cpu_local *cpu = &scheduler->cpus[logical_id];
    if (cpu->state != DUCKOS_CPU_DRAINING || cpu->current_tid != 0U ||
        cpu->interrupt_depth != 0U || cpu->lock_depth != 0U ||
        cpu->preempt_depth != 0U || cpu->dma_leases != 0U)
        return 0;

    const uint64_t cpu_bit = UINT64_C(1) << logical_id;
    for (size_t i = 0U; i < scheduler->thread_count; ++i) {
        const duckos_sched_thread *thread = &scheduler->threads[i];
        const int terminal = thread->state == DUCKOS_THREAD_ZOMBIE;
        const int exclusively_pinned =
            (thread->affinity_mask & cpu_bit) != 0U &&
            (thread->affinity_mask & ~cpu_bit) == 0U;
        if (!terminal && exclusively_pinned) return 0;
    }
    return 1;
}

int duckos_scheduler_core_offline_allowed(
    duckos_scheduler *scheduler, uint32_t logical_id
) {
    if (scheduler == NULL || logical_id == 0U || logical_id >= scheduler->cpu_count) return 0;
    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    const int allowed = core_offline_allowed_locked(scheduler, logical_id);
    scheduler_unlock(scheduler, lock_state);
    return allowed;
}

duckos_sched_status duckos_scheduler_release_cpu(
    duckos_scheduler *scheduler, uint32_t logical_id
) {
    if (scheduler == NULL) return DUCKOS_SCHED_INVALID_ARGUMENT;
    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    duckos_cpu_local *cpu = cpu_at(scheduler, logical_id);
    if (cpu == NULL || logical_id == 0U || cpu->state != DUCKOS_CPU_DRAINING) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_INVALID_STATE;
    }
    if (!core_offline_allowed_locked(scheduler, logical_id)) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_CPU_BUSY;
    }
    if (scheduler->generation == UINT32_MAX) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_GENERATION_EXHAUSTED;
    }
    cpu->state = DUCKOS_CPU_OFFLINE;
    ++scheduler->generation;
    for (uint32_t i = 0U; i < scheduler->cpu_count; ++i)
        scheduler->cpus[i].generation = scheduler->generation;
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_register_thread(
    duckos_scheduler *scheduler, const duckos_sched_thread *thread
) {
    if (scheduler == NULL || thread == NULL || thread->tid == 0U ||
        thread->pid == 0U || thread->priority < 0 || thread->priority > 255 ||
        thread->stack_bytes < 16384U || thread->stack_bytes > 16777216U ||
        thread->affinity_mask == 0U ||
        (thread->affinity_mask & ~valid_cpu_mask(scheduler->cpu_count)) != 0U ||
        thread->state != DUCKOS_THREAD_CREATED)
        return DUCKOS_SCHED_INVALID_ARGUMENT;

    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    if (scheduler->thread_count >= DUCKOS_SCHEDULER_MAX_THREADS) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_LIMIT_REACHED;
    }
    if (find_thread(scheduler, thread->tid) != scheduler->thread_count) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_DUPLICATE_ID;
    }
    int online_target = 0;
    for (uint32_t cpu_id = 0U; cpu_id < scheduler->cpu_count; ++cpu_id) {
        if (scheduler->cpus[cpu_id].state == DUCKOS_CPU_ONLINE &&
            (thread->affinity_mask & (UINT64_C(1) << cpu_id)) != 0U) {
            online_target = 1;
            break;
        }
    }
    if (!online_target) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_CPU_NOT_ONLINE;
    }
    scheduler->threads[scheduler->thread_count++] = *thread;
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_transition_thread(
    duckos_scheduler *scheduler, uint64_t tid,
    duckos_thread_state next_state
) {
    if (scheduler == NULL || tid == 0U)
        return DUCKOS_SCHED_INVALID_ARGUMENT;
    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    const size_t index = find_thread(scheduler, tid);
    if (index == scheduler->thread_count) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_INVALID_ARGUMENT;
    }
    duckos_sched_thread *thread = &scheduler->threads[index];
    if (!thread_transition_valid(thread->state, next_state)) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_INVALID_STATE;
    }
    thread->state = next_state;
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_pick_next(
    duckos_scheduler *scheduler, uint32_t logical_id,
    int preempt_current, duckos_sched_thread *selected
) {
    if (scheduler == NULL || selected == NULL)
        return DUCKOS_SCHED_INVALID_ARGUMENT;
    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    duckos_cpu_local *cpu = cpu_at(scheduler, logical_id);
    if (cpu == NULL || cpu->state != DUCKOS_CPU_ONLINE) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_CPU_NOT_ONLINE;
    }

    if (cpu->current_tid != 0U) {
        const size_t current_index = find_thread(scheduler, cpu->current_tid);
        if (current_index != scheduler->thread_count &&
            scheduler->threads[current_index].state == DUCKOS_THREAD_RUNNING) {
            if (preempt_current == 0) {
                *selected = scheduler->threads[current_index];
                scheduler_unlock(scheduler, lock_state);
                return DUCKOS_SCHED_OK;
            }
            scheduler->threads[current_index].state = DUCKOS_THREAD_READY;
        }
        cpu->current_tid = 0U;
    }

    size_t chosen = scheduler->thread_count;
    int32_t best_priority = INT32_MIN;
    uint64_t best_deadline = UINT64_MAX;
    uint64_t after_id = UINT64_MAX;
    uint64_t wrap_id = UINT64_MAX;
    for (size_t i = 0U; i < scheduler->thread_count; ++i) {
        const duckos_sched_thread *thread = &scheduler->threads[i];
        if (thread->state != DUCKOS_THREAD_READY ||
            (thread->affinity_mask & (UINT64_C(1) << logical_id)) == 0U)
            continue;
        const uint64_t deadline = effective_deadline(thread->deadline_ns);
        if (thread->priority > best_priority ||
            (thread->priority == best_priority && deadline < best_deadline)) {
            best_priority = thread->priority;
            best_deadline = deadline;
            chosen = scheduler->thread_count;
            after_id = UINT64_MAX;
            wrap_id = UINT64_MAX;
        }
        if (thread->priority != best_priority || deadline != best_deadline) continue;
        if (thread->tid > scheduler->last_selected_tid[logical_id]) {
            if (thread->tid < after_id) {
                after_id = thread->tid;
                chosen = i;
            }
        } else if (thread->tid < wrap_id) {
            wrap_id = thread->tid;
        }
    }

    if (chosen == scheduler->thread_count && wrap_id != UINT64_MAX) {
        for (size_t i = 0U; i < scheduler->thread_count; ++i) {
            const duckos_sched_thread *thread = &scheduler->threads[i];
            if (thread->tid == wrap_id && thread->state == DUCKOS_THREAD_READY &&
                (thread->affinity_mask & (UINT64_C(1) << logical_id)) != 0U) {
                chosen = i;
                break;
            }
        }
    }
    if (chosen == scheduler->thread_count) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_NO_RUNNABLE_THREAD;
    }

    duckos_sched_thread *thread = &scheduler->threads[chosen];
    thread->state = DUCKOS_THREAD_RUNNING;
    thread->cpu_id = logical_id;
    if (thread->quantum_ticks == 0U) thread->quantum_ticks = 4U;
    cpu->current_tid = thread->tid;
    cpu->quantum_ticks = thread->quantum_ticks;
    cpu->reschedule_pending = 0U;
    scheduler->last_selected_tid[logical_id] = thread->tid;
    *selected = *thread;
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_switch(
    duckos_scheduler *scheduler, uint32_t logical_id,
    duckos_sched_thread *selected
) {
    if (scheduler == NULL || selected == NULL)
        return DUCKOS_SCHED_INVALID_ARGUMENT;
    if (scheduler->platform.context_switch == NULL ||
        scheduler->platform.irq_save == NULL ||
        scheduler->platform.irq_restore == NULL)
        return DUCKOS_SCHED_CONTEXT_UNAVAILABLE;

    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    duckos_cpu_local *cpu = cpu_at(scheduler, logical_id);
    if (cpu == NULL || cpu->state != DUCKOS_CPU_ONLINE) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_CPU_NOT_ONLINE;
    }

    const size_t old_index = cpu->current_tid == 0U
        ? scheduler->thread_count
        : find_thread(scheduler, cpu->current_tid);
    if (old_index == scheduler->thread_count && cpu->current_tid != 0U) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_INVALID_STATE;
    }

    uintptr_t *old_stack_pointer = &cpu->idle_stack_pointer;
    duckos_thread_state old_state = DUCKOS_THREAD_CREATED;
    if (old_index != scheduler->thread_count) {
        duckos_sched_thread *old_thread = &scheduler->threads[old_index];
        old_state = old_thread->state;
        if (old_state == DUCKOS_THREAD_RUNNING) {
            old_thread->state = DUCKOS_THREAD_READY;
        } else if (old_state != DUCKOS_THREAD_BLOCKED &&
                   old_state != DUCKOS_THREAD_SLEEPING &&
                   old_state != DUCKOS_THREAD_ZOMBIE) {
            scheduler_unlock(scheduler, lock_state);
            return DUCKOS_SCHED_INVALID_STATE;
        }
        old_stack_pointer = &old_thread->saved_stack_pointer;
    }

    size_t chosen = scheduler->thread_count;
    int32_t best_priority = INT32_MIN;
    uint64_t best_deadline = UINT64_MAX;
    uint64_t after_id = UINT64_MAX;
    uint64_t wrap_id = UINT64_MAX;
    for (size_t i = 0U; i < scheduler->thread_count; ++i) {
        const duckos_sched_thread *thread = &scheduler->threads[i];
        if (i == old_index || thread->state != DUCKOS_THREAD_READY ||
            (thread->affinity_mask & (UINT64_C(1) << logical_id)) == 0U)
            continue;
        const uint64_t deadline = effective_deadline(thread->deadline_ns);
        if (thread->priority > best_priority ||
            (thread->priority == best_priority && deadline < best_deadline)) {
            best_priority = thread->priority;
            best_deadline = deadline;
            chosen = scheduler->thread_count;
            after_id = UINT64_MAX;
            wrap_id = UINT64_MAX;
        }
        if (thread->priority != best_priority || deadline != best_deadline) continue;
        if (thread->tid > scheduler->last_selected_tid[logical_id]) {
            if (thread->tid < after_id) {
                after_id = thread->tid;
                chosen = i;
            }
        } else if (thread->tid < wrap_id) {
            wrap_id = thread->tid;
        }
    }

    if (chosen == scheduler->thread_count && wrap_id != UINT64_MAX) {
        for (size_t i = 0U; i < scheduler->thread_count; ++i) {
            const duckos_sched_thread *thread = &scheduler->threads[i];
            if (i != old_index && thread->tid == wrap_id &&
                thread->state == DUCKOS_THREAD_READY &&
                (thread->affinity_mask & (UINT64_C(1) << logical_id)) != 0U) {
                chosen = i;
                break;
            }
        }
    }

    uintptr_t new_stack_pointer = 0U;
    if (chosen != scheduler->thread_count) {
        duckos_sched_thread *next = &scheduler->threads[chosen];
        if (next->saved_stack_pointer == 0U) {
            if (old_index != scheduler->thread_count)
                scheduler->threads[old_index].state = old_state;
            scheduler_unlock(scheduler, lock_state);
            return DUCKOS_SCHED_CONTEXT_UNAVAILABLE;
        }
        next->state = DUCKOS_THREAD_RUNNING;
        next->cpu_id = logical_id;
        if (next->quantum_ticks == 0U) next->quantum_ticks = 4U;
        cpu->current_tid = next->tid;
        cpu->quantum_ticks = next->quantum_ticks;
        cpu->reschedule_pending = 0U;
        scheduler->last_selected_tid[logical_id] = next->tid;
        *selected = *next;
        new_stack_pointer = next->saved_stack_pointer;
    } else if (old_index != scheduler->thread_count &&
               cpu->idle_stack_pointer != 0U) {
        cpu->current_tid = 0U;
        cpu->quantum_ticks = 0U;
        cpu->reschedule_pending = 0U;
    } else {
        if (old_index != scheduler->thread_count)
            scheduler->threads[old_index].state = old_state;
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_NO_RUNNABLE_THREAD;
    }

    scheduler_unlock_keep_interrupts(scheduler);
    scheduler->platform.context_switch(
        scheduler->platform.switch_context, old_stack_pointer, new_stack_pointer
    );
    scheduler->platform.irq_restore(
        scheduler->platform.irq_context, lock_state.irq_state
    );
    return DUCKOS_SCHED_OK;
}

duckos_sched_status duckos_scheduler_tick(
    duckos_scheduler *scheduler, uint32_t logical_id,
    int *reschedule_required
) {
    if (scheduler == NULL || reschedule_required == NULL)
        return DUCKOS_SCHED_INVALID_ARGUMENT;
    *reschedule_required = 0;
    duckos_sched_lock_state lock_state = scheduler_lock(scheduler);
    duckos_cpu_local *cpu = cpu_at(scheduler, logical_id);
    if (cpu == NULL || cpu->state != DUCKOS_CPU_ONLINE) {
        scheduler_unlock(scheduler, lock_state);
        return DUCKOS_SCHED_CPU_NOT_ONLINE;
    }
    if (cpu->current_tid != 0U && cpu->quantum_ticks != 0U) {
        --cpu->quantum_ticks;
        if (cpu->quantum_ticks == 0U) {
            cpu->reschedule_pending = 1U;
            *reschedule_required = 1;
        }
    }
    scheduler_unlock(scheduler, lock_state);
    return DUCKOS_SCHED_OK;
}

const char *duckos_sched_status_name(duckos_sched_status status) {
    switch (status) {
    case DUCKOS_SCHED_OK: return "ok";
    case DUCKOS_SCHED_INVALID_ARGUMENT: return "invalid-argument";
    case DUCKOS_SCHED_LIMIT_REACHED: return "limit-reached";
    case DUCKOS_SCHED_DUPLICATE_ID: return "duplicate-id";
    case DUCKOS_SCHED_INVALID_STATE: return "invalid-state";
    case DUCKOS_SCHED_NO_RUNNABLE_THREAD: return "no-runnable-thread";
    case DUCKOS_SCHED_CPU_NOT_ONLINE: return "cpu-not-online";
    case DUCKOS_SCHED_CPU_BUSY: return "cpu-busy";
    case DUCKOS_SCHED_STARTUP_INCOMPLETE: return "startup-incomplete";
    case DUCKOS_SCHED_GENERATION_EXHAUSTED: return "generation-exhausted";
    case DUCKOS_SCHED_CONTEXT_UNAVAILABLE: return "context-unavailable";
    }
    return "unknown";
}
