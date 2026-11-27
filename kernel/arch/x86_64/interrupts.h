#ifndef DAK_X86_64_INTERRUPTS_H
#define DAK_X86_64_INTERRUPTS_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct dakos_x86_exception_frame {
    uint64_t r15;
    uint64_t r14;
    uint64_t r13;
    uint64_t r12;
    uint64_t r11;
    uint64_t r10;
    uint64_t r9;
    uint64_t r8;
    uint64_t rdi;
    uint64_t rsi;
    uint64_t rbp;
    uint64_t rdx;
    uint64_t rcx;
    uint64_t rbx;
    uint64_t rax;
    uint64_t vector;
    uint64_t error_code;
    uint64_t rip;
    uint64_t cs;
    uint64_t rflags;
} dakos_x86_exception_frame;

/* Pure bootstrap routing policy: #DF=IST1, NMI=IST2, #PF=IST3. */
static inline uint8_t dakos_x86_exception_ist(uint32_t vector) {
    switch (vector) {
    case 8u: return 1u;
    case 2u: return 2u;
    case 14u: return 3u;
    default: return 0u;
    }
}

/* Installs exception gates 0..31. CPU maskable interrupts remain disabled. */
int dakos_x86_interrupts_init(void);

void dakos_x86_exception_dispatch(const dakos_x86_exception_frame *frame);

#ifdef __cplusplus
}
#endif


#endif
