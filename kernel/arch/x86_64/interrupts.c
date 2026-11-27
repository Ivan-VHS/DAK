#include "interrupts.h"

#include "idt.h"

#include <stddef.h>
#include <stdint.h>

typedef void (*dakos_exception_stub)(void);

_Static_assert(sizeof(dakos_x86_exception_frame) == 160u,
               "x86_64 exception frame must match the assembly stack layout");
_Static_assert(offsetof(dakos_x86_exception_frame, vector) == 120u,
               "x86_64 exception vector offset mismatch");
_Static_assert(offsetof(dakos_x86_exception_frame, rip) == 136u,
               "x86_64 exception RIP offset mismatch");

#define DECLARE_STUB(number) extern void dakos_x86_isr_##number(void)
DECLARE_STUB(0);  DECLARE_STUB(1);  DECLARE_STUB(2);  DECLARE_STUB(3);
DECLARE_STUB(4);  DECLARE_STUB(5);  DECLARE_STUB(6);  DECLARE_STUB(7);
DECLARE_STUB(8);  DECLARE_STUB(9);  DECLARE_STUB(10); DECLARE_STUB(11);
DECLARE_STUB(12); DECLARE_STUB(13); DECLARE_STUB(14); DECLARE_STUB(15);
DECLARE_STUB(16); DECLARE_STUB(17); DECLARE_STUB(18); DECLARE_STUB(19);
DECLARE_STUB(20); DECLARE_STUB(21); DECLARE_STUB(22); DECLARE_STUB(23);
DECLARE_STUB(24); DECLARE_STUB(25); DECLARE_STUB(26); DECLARE_STUB(27);
DECLARE_STUB(28); DECLARE_STUB(29); DECLARE_STUB(30); DECLARE_STUB(31);
#undef DECLARE_STUB

static dakos_idt_gate exception_idt[DAKOS_IDT_ENTRY_COUNT]
    __attribute__((aligned(16)));

static dakos_exception_stub const exception_stubs[DAKOS_X86_EXCEPTION_COUNT] = {
    dakos_x86_isr_0,  dakos_x86_isr_1,  dakos_x86_isr_2,  dakos_x86_isr_3,
    dakos_x86_isr_4,  dakos_x86_isr_5,  dakos_x86_isr_6,  dakos_x86_isr_7,
    dakos_x86_isr_8,  dakos_x86_isr_9,  dakos_x86_isr_10, dakos_x86_isr_11,
    dakos_x86_isr_12, dakos_x86_isr_13, dakos_x86_isr_14, dakos_x86_isr_15,
    dakos_x86_isr_16, dakos_x86_isr_17, dakos_x86_isr_18, dakos_x86_isr_19,
    dakos_x86_isr_20, dakos_x86_isr_21, dakos_x86_isr_22, dakos_x86_isr_23,
    dakos_x86_isr_24, dakos_x86_isr_25, dakos_x86_isr_26, dakos_x86_isr_27,
    dakos_x86_isr_28, dakos_x86_isr_29, dakos_x86_isr_30, dakos_x86_isr_31
};

typedef struct __attribute__((packed)) dakos_idtr {
    uint16_t limit;
    uint64_t base;
} dakos_idtr;

static uint16_t current_code_selector(void) {
    uint16_t selector;
    __asm__ volatile ("mov %%cs, %0" : "=r"(selector));
    return selector;
}

int dakos_x86_interrupts_init(void) {
    const uint16_t code_selector = current_code_selector();
    if (code_selector == 0u) return 0;

    for (uint32_t vector = 0u; vector < DAKOS_X86_EXCEPTION_COUNT; ++vector) {
        const uint64_t handler = (uint64_t)(uintptr_t)exception_stubs[vector];
        if (dakos_idt_gate_set(
                &exception_idt[vector], handler, code_selector, dakos_x86_exception_ist(vector)
            ) != DAKOS_IDT_OK) {
            return 0;
        }
    }

    const dakos_idtr descriptor = {
        (uint16_t)(sizeof(exception_idt) - 1u),
        (uint64_t)(uintptr_t)exception_idt
    };
    __asm__ volatile ("lidt %0" : : "m"(descriptor) : "memory");
    return 1;
}
