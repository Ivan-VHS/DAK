#include "context.h"

#include <limits.h>

_Static_assert(sizeof(duckos_x86_64_context_frame) == 8U * sizeof(uintptr_t),
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
    if (aligned_top < base || aligned_top - base < 9U * sizeof(uintptr_t))
        return 0;

    const uintptr_t return_slot = aligned_top - sizeof(uintptr_t);
    const uintptr_t frame_address = return_slot - sizeof(duckos_x86_64_context_frame);
    if ((frame_address & (uintptr_t)0x0fU) != (uintptr_t)8U ||
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
    frame->rip = entry;
    *(uintptr_t *)return_slot = exit_trampoline;
    *saved_stack_pointer = frame_address;
    return 1;
}
