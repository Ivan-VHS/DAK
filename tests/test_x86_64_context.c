#include "context.h"

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

int main(void) {
    _Alignas(16) unsigned char stack[4096];
    uintptr_t saved = 0U;
    assert(duckos_x86_64_context_frame_init(
        stack, sizeof(stack), (uintptr_t)task_entry,
        (uintptr_t)&task_argument, (uintptr_t)task_exit, &saved));
    duckos_x86_64_context_frame *frame = (duckos_x86_64_context_frame *)saved;
    assert(frame->rdi == (uintptr_t)&task_argument);
    assert(frame->rip == (uintptr_t)task_entry);
    assert(((uintptr_t)frame & 0x0fU) == 8U);
    assert(*(uintptr_t *)(saved + sizeof(*frame)) == (uintptr_t)task_exit);

    task_argument = 7U;
    duckos_x86_64_context_switch(&main_stack_pointer, saved);
    assert(task_stage == 1U);
    assert(task_argument == 7U);
    duckos_x86_64_context_switch(&main_stack_pointer, task_stack_pointer);
    assert(task_stage == 2U);
    puts("DAK x86_64 context switch passed");
    return 0;
}
