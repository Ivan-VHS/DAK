#ifndef DUCKOS_ARCH_X86_64_H
#define DUCKOS_ARCH_X86_64_H

#include <stdint.h>

static inline void duckos_outb(uint16_t port, uint8_t value) {
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}
static inline uint8_t duckos_inb(uint16_t port) {
    uint8_t value;
    __asm__ volatile ("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}
static inline void duckos_io_wait(void) {
    duckos_outb(0x80u, 0u);
}
static inline void duckos_cli(void) {
    __asm__ volatile ("cli" : : : "memory");
}
static inline void duckos_sti(void) {
    __asm__ volatile ("sti" : : : "memory");
}
static inline void duckos_hlt(void) {
    __asm__ volatile ("hlt");
}
static inline void duckos_invlpg(uint64_t address) {
    __asm__ volatile ("invlpg (%0)" : : "r"((void *)(uintptr_t)address) : "memory");
}
static inline uint64_t duckos_read_cr3(void) {
    uint64_t value;
    __asm__ volatile ("mov %%cr3, %0" : "=r"(value));
    return value;
}
static inline void duckos_write_cr3(uint64_t value) {
    __asm__ volatile ("mov %0, %%cr3" : : "r"(value) : "memory");
}

void duckos_context_switch(uint64_t **old_stack, uint64_t *new_stack);
void duckos_arch_init_interrupts(void);
void duckos_arch_set_syscall_gate(void (*handler)(void));

#endif
