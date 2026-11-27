#include "idt.h"

#include <stddef.h>

_Static_assert(sizeof(dakos_idt_gate) == 16u, "x86_64 IDT gates must be 16 bytes");
_Static_assert(offsetof(dakos_idt_gate, offset_high) == 8u, "IDT offset-high layout mismatch");
_Static_assert(offsetof(dakos_idt_gate, reserved) == 12u, "IDT reserved-field layout mismatch");

dakos_idt_status dakos_idt_gate_set(
    dakos_idt_gate *gate,
    uint64_t handler,
    uint16_t code_selector,
    uint8_t ist
) {
    if (gate == 0) return DAK_IDT_INVALID_ARGUMENT;
    if (handler == 0u) return DAK_IDT_INVALID_HANDLER;
    if (code_selector == 0u || (code_selector & 0x3u) != 0u) {
        return DAK_IDT_INVALID_SELECTOR;
    }
    if (ist > 7u) return DAK_IDT_INVALID_IST;

    gate->offset_low = (uint16_t)(handler & 0xffffu);
    gate->selector = code_selector;
    gate->ist = ist;
    gate->attributes = DAK_IDT_INTERRUPT_GATE;
    gate->offset_middle = (uint16_t)((handler >> 16u) & 0xffffu);
    gate->offset_high = (uint32_t)(handler >> 32u);
    gate->reserved = 0u;
    return DAK_IDT_OK;
}

uint64_t dakos_idt_gate_target(const dakos_idt_gate *gate) {
    if (gate == 0) return 0u;
    return (uint64_t)gate->offset_low |
        ((uint64_t)gate->offset_middle << 16u) |
        ((uint64_t)gate->offset_high << 32u);
}
