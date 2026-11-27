#ifndef DUCKOS_X86_64_CONTEXT_H
#define DUCKOS_X86_64_CONTEXT_H

#include <stddef.h>
#include <stdint.h>

typedef struct {
    uintptr_t rdi;
    uintptr_t r15;
    uintptr_t r14;
    uintptr_t r13;
    uintptr_t r12;
    uintptr_t rbp;
    uintptr_t rbx;
    uintptr_t rip;
} duckos_x86_64_context_frame;

int duckos_x86_64_context_frame_init(
    void *stack_base, size_t stack_bytes,
    uintptr_t entry, uintptr_t argument, uintptr_t exit_trampoline,
    uintptr_t *saved_stack_pointer
);

#if defined(__x86_64__) || defined(_M_X64)
void duckos_x86_64_context_switch(
    uintptr_t *old_stack_pointer, uintptr_t new_stack_pointer
);
#endif

#endif
