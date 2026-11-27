#ifndef DAK_IDT_H
#define DAK_IDT_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DAK_IDT_ENTRY_COUNT 256u
#define DAK_X86_EXCEPTION_COUNT 32u
#define DAK_IDT_INTERRUPT_GATE 0x8eu

typedef struct dakos_idt_gate {
    uint16_t offset_low;
    uint16_t selector;
    uint8_t ist;
    uint8_t attributes;
    uint16_t offset_middle;
    uint32_t offset_high;
    uint32_t reserved;
} dakos_idt_gate;

typedef enum dakos_idt_status {
    DAK_IDT_OK = 0,
    DAK_IDT_INVALID_ARGUMENT = -1,
    DAK_IDT_INVALID_HANDLER = -2,
    DAK_IDT_INVALID_SELECTOR = -3,
    DAK_IDT_INVALID_IST = -4
} dakos_idt_status;

/* Construct one 64-bit interrupt gate without executing privileged instructions. */
dakos_idt_status dakos_idt_gate_set(
    dakos_idt_gate *gate,
    uint64_t handler,
    uint16_t code_selector,
    uint8_t ist
);

/* Reassemble a gate target; intended for contract tests and diagnostics. */
uint64_t dakos_idt_gate_target(const dakos_idt_gate *gate);

#ifdef __cplusplus
}
#endif

#endif
