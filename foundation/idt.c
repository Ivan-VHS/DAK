#include "idt.h"

duckos_idt_status duckos_idt_gate_set(
    duckos_idt_gate *gate,
    uint64_t handler,
    uint16_t code_selector,
    uint8_t ist
) {
    if (gate == 0) return DUCKOS_IDT_INVALID_ARGUMENT;
    if (handler == 0u) return DUCKOS_IDT_INVALID_HANDLER;
    if (code_selector == 0u || (code_selector & 0x3u) != 0u) {
        return DUCKOS_IDT_INVALID_SELECTOR;
    }
    if (ist > 7u) return DUCKOS_IDT_INVALID_IST;

    gate->offset_low = (uint16_t)(handler & 0xffffu);
    gate->selector = code_selector;
    gate->ist = ist;
    gate->attributes = DUCKOS_IDT_INTERRUPT_GATE;
    gate->offset_middle = (uint16_t)((handler >> 16u) & 0xffffu);
    gate->offset_high = (uint32_t)(handler >> 32u);
    gate->reserved = 0u;
    return DUCKOS_IDT_OK;
}

uint64_t duckos_idt_gate_target(const duckos_idt_gate *gate) {
    if (gate == 0) return 0u;
    return (uint64_t)gate->offset_low |
        ((uint64_t)gate->offset_middle << 16u) |
        ((uint64_t)gate->offset_high << 32u);
}
