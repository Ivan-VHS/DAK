#ifndef DUCKOS_SYSCALL_H
#define DUCKOS_SYSCALL_H

#include <stdint.h>

typedef struct {
    uint64_t r15, r14, r13, r12, r11, r10, r9, r8;
    uint64_t rbp, rdi, rsi, rdx, rcx, rbx, rax;
} DuckOsInt80Frame;

void duckos_int80_entry(void);
void duckos_int80_unhandled(void);
void duckos_int80_handle_frame(DuckOsInt80Frame *frame);

#endif
