#ifndef DUCKOS_PROCESSOR_SCHEDULER_H
#define DUCKOS_PROCESSOR_SCHEDULER_H

#include <stdatomic.h>
#include <stddef.h>
#include <stdint.h>

#define DUCKOS_PROCESSOR_MAX_CPUS 64U
#define DUCKOS_SCHEDULER_MAX_THREADS 256U

typedef enum {
    DUCKOS_CPU_OFFLINE = 0,
    DUCKOS_CPU_STARTING,
    DUCKOS_CPU_ONLINE,
    DUCKOS_CPU_DRAINING,
    DUCKOS_CPU_QUARANTINED,
    DUCKOS_CPU_FAILED
} duckos_cpu_state;

typedef enum {
    DUCKOS_THREAD_CREATED = 0,
    DUCKOS_THREAD_READY,
    DUCKOS_THREAD_RUNNING,
    DUCKOS_THREAD_BLOCKED,
    DUCKOS_THREAD_SLEEPING,
    DUCKOS_THREAD_ZOMBIE
} duckos_thread_state;

typedef enum {
    DUCKOS_SCHED_OK = 0,
    DUCKOS_SCHED_INVALID_ARGUMENT,
    DUCKOS_SCHED_LIMIT_REACHED,
    DUCKOS_SCHED_DUPLICATE_ID,
    DUCKOS_SCHED_INVALID_STATE,
    DUCKOS_SCHED_NO_RUNNABLE_THREAD,
    DUCKOS_SCHED_CPU_NOT_ONLINE,
    DUCKOS_SCHED_CPU_BUSY,
    DUCKOS_SCHED_STARTUP_INCOMPLETE,
    DUCKOS_SCHED_GENERATION_EXHAUSTED,
    DUCKOS_SCHED_CONTEXT_UNAVAILABLE
} duckos_sched_status;

typedef struct {
    uint8_t gdt_ready;
    uint8_t idt_ready;
    uint8_t per_cpu_ready;
    uint8_t stack_ready;
    uint8_t local_controller_ready;
    uint8_t trampoline_ready;
} duckos_ap_startup_evidence;

typedef struct {
    uint32_t logical_id;
    uint32_t generation;
    duckos_cpu_state state;
    uint64_t current_tid;
    uint32_t interrupt_depth;
    uint32_t lock_depth;
    uint32_t preempt_depth;
    uint32_t dma_leases;
    uint32_t quantum_ticks;
    uintptr_t idle_stack_pointer;
    uint8_t reschedule_pending;
} duckos_cpu_local;

typedef struct {
    uint64_t tid;
    uint64_t pid;
    uint64_t deadline_ns;
    uint64_t affinity_mask;
    uint32_t stack_bytes;
    uint32_t quantum_ticks;
    int32_t priority;
    uint32_t cpu_id;
    uintptr_t saved_stack_pointer;
    duckos_thread_state state;
} duckos_sched_thread;

typedef uint64_t (*duckos_irq_save_fn)(void *context);
typedef void (*duckos_irq_restore_fn)(void *context, uint64_t state);
typedef void (*duckos_context_switch_fn)(
    void *context, uintptr_t *old_stack_pointer, uintptr_t new_stack_pointer
);

typedef struct {
    void *irq_context;
    duckos_irq_save_fn irq_save;
    duckos_irq_restore_fn irq_restore;
    void *switch_context;
    duckos_context_switch_fn context_switch;
} duckos_sched_platform;

typedef struct {
    atomic_flag lock;
    duckos_sched_platform platform;
    duckos_cpu_local cpus[DUCKOS_PROCESSOR_MAX_CPUS];
    duckos_sched_thread threads[DUCKOS_SCHEDULER_MAX_THREADS];
    uint64_t last_selected_tid[DUCKOS_PROCESSOR_MAX_CPUS];
    uint32_t cpu_count;
    uint32_t generation;
    size_t thread_count;
} duckos_scheduler;

duckos_sched_status duckos_scheduler_init(
    duckos_scheduler *scheduler, uint32_t cpu_count,
    uint32_t generation, const duckos_sched_platform *platform
);

duckos_sched_status duckos_scheduler_bootstrap_cpu(
    duckos_scheduler *scheduler, uint32_t logical_id
);

duckos_sched_status duckos_scheduler_begin_cpu_start(
    duckos_scheduler *scheduler, uint32_t logical_id
);

duckos_sched_status duckos_scheduler_complete_cpu_start(
    duckos_scheduler *scheduler, uint32_t logical_id,
    const duckos_ap_startup_evidence *evidence
);

duckos_sched_status duckos_scheduler_begin_cpu_drain(
    duckos_scheduler *scheduler, uint32_t logical_id
);

duckos_sched_status duckos_scheduler_update_cpu_critical(
    duckos_scheduler *scheduler, uint32_t logical_id,
    uint32_t interrupt_depth, uint32_t lock_depth,
    uint32_t preempt_depth, uint32_t dma_leases
);

duckos_sched_status duckos_scheduler_release_cpu(
    duckos_scheduler *scheduler, uint32_t logical_id
);

duckos_sched_status duckos_scheduler_register_thread(
    duckos_scheduler *scheduler, const duckos_sched_thread *thread
);

duckos_sched_status duckos_scheduler_transition_thread(
    duckos_scheduler *scheduler, uint64_t tid,
    duckos_thread_state next_state
);

duckos_sched_status duckos_scheduler_pick_next(
    duckos_scheduler *scheduler, uint32_t logical_id,
    int preempt_current, duckos_sched_thread *selected
);

duckos_sched_status duckos_scheduler_switch(
    duckos_scheduler *scheduler, uint32_t logical_id,
    duckos_sched_thread *selected
);

duckos_sched_status duckos_scheduler_tick(
    duckos_scheduler *scheduler, uint32_t logical_id,
    int *reschedule_required
);

int duckos_scheduler_core_offline_allowed(
    duckos_scheduler *scheduler, uint32_t logical_id
);

const char *duckos_sched_status_name(duckos_sched_status status);

#endif
