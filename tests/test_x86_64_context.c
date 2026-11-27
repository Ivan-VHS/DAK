#include "context.h"
#include "scheduler.h"

#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uintptr_t main_stack_pointer;
static uintptr_t task_stack_pointer;
static unsigned task_stage;
static unsigned task_argument;

static void task_exit(void) {
    for (;;) {
#if defined(__x86_64__)
        __asm__ volatile ("pause");
#else
        break;
#endif
    }
}

static void task_entry(void *argument) {
    task_argument = *(const unsigned *)argument;
    task_stage = 1U;
    duckos_x86_64_context_switch(&task_stack_pointer, main_stack_pointer);
    task_stage = 2U;
    duckos_x86_64_context_switch(&task_stack_pointer, main_stack_pointer);
    task_exit();
}


static duckos_scheduler integrated_scheduler;
static unsigned integrated_task_stage;

static uint64_t hosted_irq_save(void *context) {
    (void)context;
    return UINT64_C(0x202);
}

static void hosted_irq_restore(void *context, uint64_t state) {
    (void)context;
    assert(state == UINT64_C(0x202));
}

static void integrated_task_entry(void *argument) {
    (void)argument;
    integrated_task_stage = 1U;
    duckos_sched_thread selected;
    assert(duckos_scheduler_switch(
        &integrated_scheduler, 0U, &selected
    ) == DUCKOS_SCHED_OK);
    integrated_task_stage = 2U;
    assert(duckos_scheduler_transition_thread(
        &integrated_scheduler, 901U, DUCKOS_THREAD_ZOMBIE
    ) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_switch(
        &integrated_scheduler, 0U, &selected
    ) == DUCKOS_SCHED_OK);
    integrated_task_stage = 3U;
}

static void test_scheduler_context_end_to_end(void) {
    _Alignas(16) unsigned char task_stack[16384];
    uintptr_t saved_stack = 0U;
    integrated_task_stage = 0U;

    duckos_sched_platform platform = {
        .irq_context = NULL,
        .irq_save = hosted_irq_save,
        .irq_restore = hosted_irq_restore,
        .switch_context = NULL,
        .context_switch = duckos_x86_64_scheduler_context_switch
    };
    assert(duckos_scheduler_init(
        &integrated_scheduler, 1U, 1U, &platform
    ) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_bootstrap_cpu(
        &integrated_scheduler, 0U
    ) == DUCKOS_SCHED_OK);
    assert(duckos_x86_64_context_frame_init(
        task_stack, sizeof(task_stack),
        (uintptr_t)integrated_task_entry, 0U,
        (uintptr_t)task_exit, &saved_stack
    ));

    duckos_sched_thread task;
    memset(&task, 0, sizeof(task));
    task.tid = 901U;
    task.pid = 1U;
    task.affinity_mask = UINT64_C(1);
    task.stack_bytes = sizeof(task_stack);
    task.priority = 20;
    task.saved_stack_pointer = saved_stack;
    task.state = DUCKOS_THREAD_CREATED;
    assert(duckos_scheduler_register_thread(
        &integrated_scheduler, &task
    ) == DUCKOS_SCHED_OK);
    assert(duckos_scheduler_transition_thread(
        &integrated_scheduler, 901U, DUCKOS_THREAD_READY
    ) == DUCKOS_SCHED_OK);

    duckos_sched_thread selected;
    assert(duckos_scheduler_switch(
        &integrated_scheduler, 0U, &selected
    ) == DUCKOS_SCHED_OK);
    assert(selected.tid == 901U);
    assert(integrated_task_stage == 1U);
    assert(integrated_scheduler.cpus[0].current_tid == 0U);

    assert(duckos_scheduler_switch(
        &integrated_scheduler, 0U, &selected
    ) == DUCKOS_SCHED_OK);
    assert(selected.tid == 901U);
    assert(integrated_task_stage == 2U);
    assert(integrated_scheduler.cpus[0].current_tid == 0U);
}

int main(void) {
    _Alignas(16) unsigned char stack[4096];
    uintptr_t saved = 0U;
    assert(duckos_x86_64_context_frame_init(
        stack, sizeof(stack), (uintptr_t)task_entry,
        (uintptr_t)&task_argument, (uintptr_t)task_exit, &saved));
    duckos_x86_64_context_frame *frame = (duckos_x86_64_context_frame *)saved;
    assert(frame->rdi == (uintptr_t)&task_argument);
    assert(frame->rip == (uintptr_t)task_entry);
    assert((frame->rflags & (uintptr_t)(1U << 9)) != 0U);
    assert(((uintptr_t)frame & 0x0fU) == 0U);
    assert(*(uintptr_t *)(saved + sizeof(*frame)) == (uintptr_t)task_exit);

    task_argument = 7U;
    duckos_x86_64_context_switch(&main_stack_pointer, saved);
    assert(task_stage == 1U);
    assert(task_argument == 7U);
    duckos_x86_64_context_switch(&main_stack_pointer, task_stack_pointer);
    assert(task_stage == 2U);
    test_scheduler_context_end_to_end();
    puts("DAK x86_64 scheduler/context integration passed");
    return 0;
}
