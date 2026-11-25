#ifndef DUCKOS_IDT_H
#define DUCKOS_IDT_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_IDT_ENTRY_COUNT 256u
#define DUCKOS_X86_EXCEPTION_COUNT 32u
#define DUCKOS_IDT_INTERRUPT_GATE 0x8eu

typedef struct duckos_idt_gate {
    uint16_t offset_low;
    uint16_t selector;
    uint8_t ist;
    uint8_t attributes;
    uint16_t offset_middle;
    uint32_t offset_high;
    uint32_t reserved;
} duckos_idt_gate;

typedef enum duckos_idt_status {
    DUCKOS_IDT_OK = 0,
    DUCKOS_IDT_INVALID_ARGUMENT = -1,
    DUCKOS_IDT_INVALID_HANDLER = -2,
    DUCKOS_IDT_INVALID_SELECTOR = -3,
    DUCKOS_IDT_INVALID_IST = -4
} duckos_idt_status;

/* Construct one 64-bit interrupt gate without executing privileged instructions. */
duckos_idt_status duckos_idt_gate_set(
    duckos_idt_gate *gate,
    uint64_t handler,
    uint16_t code_selector,
    uint8_t ist
);

/* Reassemble a gate target; intended for contract tests and diagnostics. */
uint64_t duckos_idt_gate_target(const duckos_idt_gate *gate);

#ifdef __cplusplus
}
#endif

#endif
