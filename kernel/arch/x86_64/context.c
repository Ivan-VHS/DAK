#include "context.h"

#include <limits.h>

_Static_assert(sizeof(duckos_x86_64_context_frame) == 9U * sizeof(uintptr_t),
               "context frame must match the x86_64 assembly save order");

int duckos_x86_64_context_frame_init(
    void *stack_base, size_t stack_bytes,
    uintptr_t entry, uintptr_t argument, uintptr_t exit_trampoline,
    uintptr_t *saved_stack_pointer
) {
    if (stack_base == NULL || saved_stack_pointer == NULL ||
        entry == 0U || exit_trampoline == 0U || stack_bytes < 256U)
        return 0;

    const uintptr_t base = (uintptr_t)stack_base;
    if (stack_bytes > (size_t)(UINTPTR_MAX - base)) return 0;
    const uintptr_t end = base + (uintptr_t)stack_bytes;
    const uintptr_t aligned_top = end & ~(uintptr_t)0x0fU;
    if (aligned_top < base || aligned_top - base < 10U * sizeof(uintptr_t))
        return 0;

    const uintptr_t return_slot = aligned_top - sizeof(uintptr_t);
    const uintptr_t frame_address =
        return_slot - sizeof(duckos_x86_64_context_frame);
    if ((frame_address & (uintptr_t)0x0fU) != 0U ||
        frame_address < base)
        return 0;

    duckos_x86_64_context_frame *frame =
        (duckos_x86_64_context_frame *)frame_address;
    frame->rdi = argument;
    frame->r15 = 0U;
    frame->r14 = 0U;
    frame->r13 = 0U;
    frame->r12 = 0U;
    frame->rbp = 0U;
    frame->rbx = 0U;
    frame->rflags = (uintptr_t)0x202U;
    frame->rip = entry;
    *(uintptr_t *)return_slot = exit_trampoline;
    *saved_stack_pointer = frame_address;
    return 1;
}

#if defined(__x86_64__) && (defined(__GNUC__) || defined(__clang__))
void duckos_x86_64_scheduler_context_switch(
    void *context, uintptr_t *old_stack_pointer, uintptr_t new_stack_pointer
) {
    (void)context;
    duckos_x86_64_context_switch(old_stack_pointer, new_stack_pointer);
}

uint64_t duckos_x86_64_irq_save(void *context) {
    (void)context;
#if defined(__x86_64__) && (defined(__GNUC__) || defined(__clang__))
    uint64_t flags;
    __asm__ volatile ("pushfq; popq %0; cli" : "=r"(flags) : : "memory");
    return flags;
#else
    return 0U;
#endif
}

void duckos_x86_64_irq_restore(void *context, uint64_t state) {
    (void)context;
#if (defined(__x86_64__) || defined(__i386__)) && (defined(__GNUC__) || defined(__clang__))
    if ((state & (UINT64_C(1) << 9)) != 0U)
        __asm__ volatile ("sti" : : : "memory");
    else
        __asm__ volatile ("cli" : : : "memory");
#else
    (void)state;
#endif
}

void duckos_x86_64_scheduler_platform(duckos_sched_platform *platform) {
    if (platform == NULL) return;
    platform->irq_context = NULL;
    platform->irq_save = duckos_x86_64_irq_save;
    platform->irq_restore = duckos_x86_64_irq_restore;
    platform->switch_context = NULL;
    platform->context_switch = duckos_x86_64_scheduler_context_switch;
}

#endif
