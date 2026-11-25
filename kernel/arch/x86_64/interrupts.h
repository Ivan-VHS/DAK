#ifndef DUCKOS_X86_64_INTERRUPTS_H
#define DUCKOS_X86_64_INTERRUPTS_H

#include <stdint.h>

#if defined(_MSC_VER)
#define DUCKOS_NORETURN __declspec(noreturn)
#elif defined(__GNUC__) || defined(__clang__)
#define DUCKOS_NORETURN __attribute__((noreturn))
#else
#define DUCKOS_NORETURN
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct duckos_x86_exception_frame {
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
} duckos_x86_exception_frame;

/* Installs exception gates 0..31. CPU maskable interrupts remain disabled. */
int duckos_x86_interrupts_init(void);

void duckos_x86_exception_dispatch(const duckos_x86_exception_frame *frame)
    DUCKOS_NORETURN;

#ifdef __cplusplus
}
#endif

#undef DUCKOS_NORETURN

#endif
