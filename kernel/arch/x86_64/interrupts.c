#include "duckos/arch_x86_64.h"
#include "duckos/syscall.h"

#include <stddef.h>
#include <stdint.h>

typedef struct __attribute__((packed)) {
    uint16_t offset_low;
    uint16_t selector;
    uint8_t ist;
    uint8_t attributes;
    uint16_t offset_middle;
    uint32_t offset_high;
    uint32_t reserved;
} DuckOsIdtGate;

typedef struct __attribute__((packed)) {
    uint16_t limit;
    uint64_t base;
} DuckOsIdtr;

static DuckOsIdtGate idt[256];

static void set_gate(uint8_t vector, void (*handler)(void), uint8_t attributes) {
    uint64_t address = (uint64_t)(uintptr_t)handler;
    DuckOsIdtGate *gate = &idt[vector];
    gate->offset_low = (uint16_t)address;
    gate->selector = 0x08u;
    gate->ist = 0u;
    gate->attributes = attributes;
    gate->offset_middle = (uint16_t)(address >> 16u);
    gate->offset_high = (uint32_t)(address >> 32u);
    gate->reserved = 0u;
}

void duckos_arch_set_syscall_gate(void (*handler)(void)) {
    if (handler != NULL) set_gate(0x80u, handler, 0x8eu);
}

void duckos_arch_init_interrupts(void) {
    for (uint32_t i = 0u; i < 256u; ++i)
        set_gate((uint8_t)i, duckos_int80_unhandled, 0x8eu);

    duckos_arch_set_syscall_gate(duckos_int80_entry);

    /* This first kernel stage is cooperative; mask legacy PIC interrupts. */
    duckos_outb(0x21u, 0xffu);
    duckos_outb(0xa1u, 0xffu);

    DuckOsIdtr descriptor = {
        (uint16_t)(sizeof idt - 1u),
        (uint64_t)(uintptr_t)idt
    };
    __asm__ volatile ("lidt %0" : : "m"(descriptor) : "memory");
}
