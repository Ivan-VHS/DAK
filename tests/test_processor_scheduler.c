#include "scheduler.h"

#include <assert.h>
#include <stdio.h>
#include <string.h>

static void test_scheduler_lifecycle_and_startup(void) {
    duckos_scheduler scheduler;
    assert(duckos_scheduler_init(&scheduler, 4U, 1U, NULL) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_bootstrap_cpu(&scheduler, 0U) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_begin_cpu_start(&scheduler, 1U) == DUCKOS_SCHED_OK);
    duckos_ap_startup_evidence missing = {1U, 1U, 1U, 1U, 0U, 1U};
    assert(duckos_scheduler_complete_cpu_start(&scheduler, 1U, &missing) == DUCKOS_SCHED_STARTUP_INCOMPLETE);
    duckos_ap_startup_evidence ready = {1U, 1U, 1U, 1U, 1U, 1U};
    assert(duckos_scheduler_complete_cpu_start(&scheduler, 1U, &ready) == DUCKOS_SCHED_OK);
    assert(scheduler.cpus[1].state == DUCKOS_CPU_ONLINE);
}

static duckos_sched_thread make_thread(
    uint64_t tid, int32_t priority, uint64_t deadline,
    uint64_t affinity, duckos_thread_state state
) {
    duckos_sched_thread thread;
    memset(&thread, 0, sizeof(thread));
    thread.tid = tid;
    thread.pid = 1U;
    thread.priority = priority;
    thread.deadline_ns = deadline;
    thread.affinity_mask = affinity;
    thread.stack_bytes = 32768U;
    thread.quantum_ticks = 2U;
    thread.state = state;
    return thread;
}

static void test_scheduling_affinity_deadline_and_round_robin(void) {
    duckos_scheduler scheduler;
    assert(duckos_scheduler_init(&scheduler, 2U, 1U, NULL) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_bootstrap_cpu(&scheduler, 0U) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_begin_cpu_start(&scheduler, 1U) == DUCKOS_SCHED_OK);
    duckos_ap_startup_evidence ready = {1U, 1U, 1U, 1U, 1U, 1U};
    assert(duckos_scheduler_complete_cpu_start(&scheduler, 1U, &ready) == DUCKOS_SCHED_OK);

    duckos_sched_thread a = make_thread(11U, 20, 0U, 3U, DUCKOS_THREAD_CREATED);
    duckos_sched_thread b = make_thread(12U, 20, 10U, 1U, DUCKOS_THREAD_CREATED);
    duckos_sched_thread c = make_thread(13U, 20, 10U, 1U, DUCKOS_THREAD_CREATED);
    duckos_sched_thread d = make_thread(14U, 30, 5U, 2U, DUCKOS_THREAD_CREATED);
    assert(duckos_scheduler_register_thread(&scheduler, &a) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_register_thread(&scheduler, &b) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_register_thread(&scheduler, &c) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_register_thread(&scheduler, &d) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_transition_thread(&scheduler, 11U, DUCKOS_THREAD_READY) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_transition_thread(&scheduler, 12U, DUCKOS_THREAD_READY) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_transition_thread(&scheduler, 13U, DUCKOS_THREAD_READY) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_transition_thread(&scheduler, 14U, DUCKOS_THREAD_READY) == DUCKOS_SCHED_OK);

    duckos_sched_thread selected;
    assert(duckos_scheduler_pick_next(&scheduler, 0U, 0, &selected) == DUCKOS_SCHED_OK);
    assert(selected.tid == 12U);
    int reschedule = 0;
    assert(duckos_scheduler_tick(&scheduler, 0U, &reschedule) == DUCKOS_SCHED_OK && !reschedule);
    assert(duckos_scheduler_tick(&scheduler, 0U, &reschedule) == DUCKOS_SCHED_OK && reschedule);
    assert(duckos_scheduler_pick_next(&scheduler, 0U, 1, &selected) == DUCKOS_SCHED_OK);
    assert(selected.tid == 13U);
    assert(duckos_scheduler_pick_next(&scheduler, 1U, 0, &selected) == DUCKOS_SCHED_OK);
    assert(selected.tid == 14U);
}

static void test_core_drain_and_topology_generation(void) {
    duckos_scheduler scheduler;
    assert(duckos_scheduler_init(&scheduler, 2U, 7U, NULL) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_bootstrap_cpu(&scheduler, 0U) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_begin_cpu_start(&scheduler, 1U) == DUCKOS_SCHED_OK);
    duckos_ap_startup_evidence ready = {1U, 1U, 1U, 1U, 1U, 1U};
    assert(duckos_scheduler_complete_cpu_start(&scheduler, 1U, &ready) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_begin_cpu_drain(&scheduler, 1U) == DUCKOS_SCHED_OK);
    assert(!duckos_scheduler_core_offline_allowed(&scheduler, 1U));
    assert(duckos_scheduler_update_cpu_critical(&scheduler, 1U, 0U, 0U, 0U, 0U) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_core_offline_allowed(&scheduler, 1U));
    assert(duckos_scheduler_release_cpu(&scheduler, 1U) == DUCKOS_SCHED_OK);
    assert(scheduler.generation == 8U);
    assert(scheduler.cpus[0].generation == 8U);
}

int main(void) {
    test_scheduler_lifecycle_and_startup();
    test_scheduling_affinity_deadline_and_round_robin();
    test_core_drain_and_topology_generation();
    puts("DAK bounded SMP scheduler tests passed");
    return 0;
}
