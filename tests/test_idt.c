#include "idt.h"
#include "interrupts.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

static void test_gate_layout_and_round_trip(void) {
    duckos_idt_gate gate = {0};
    const uint64_t handler = UINT64_C(0x123456789abcdef0);

    assert(sizeof(duckos_idt_gate) == 16u);
    assert(offsetof(duckos_idt_gate, offset_low) == 0u);
    assert(offsetof(duckos_idt_gate, selector) == 2u);
    assert(offsetof(duckos_idt_gate, ist) == 4u);
    assert(offsetof(duckos_idt_gate, attributes) == 5u);
    assert(offsetof(duckos_idt_gate, offset_middle) == 6u);
    assert(offsetof(duckos_idt_gate, offset_high) == 8u);
    assert(offsetof(duckos_idt_gate, reserved) == 12u);

    assert(duckos_idt_gate_set(&gate, handler, 0x08u, 0u) == DUCKOS_IDT_OK);
    assert(gate.offset_low == 0xdef0u);
    assert(gate.offset_middle == 0x9abcu);
    assert(gate.offset_high == 0x12345678u);
    assert(gate.selector == 0x08u);
    assert(gate.ist == 0u);
    assert(gate.attributes == DUCKOS_IDT_INTERRUPT_GATE);
    assert(gate.reserved == 0u);
    assert(duckos_idt_gate_target(&gate) == handler);
}

static void test_exception_frame_matches_assembly_layout(void) {
    assert(sizeof(duckos_x86_exception_frame) == 160u);
    assert(offsetof(duckos_x86_exception_frame, r15) == 0u);
    assert(offsetof(duckos_x86_exception_frame, rax) == 112u);
    assert(offsetof(duckos_x86_exception_frame, vector) == 120u);
    assert(offsetof(duckos_x86_exception_frame, error_code) == 128u);
    assert(offsetof(duckos_x86_exception_frame, rip) == 136u);
    assert(offsetof(duckos_x86_exception_frame, cs) == 144u);
    assert(offsetof(duckos_x86_exception_frame, rflags) == 152u);
}

static void test_exception_ist_routing(void) {
    assert(duckos_x86_exception_ist(8u) == 1u);
    assert(duckos_x86_exception_ist(2u) == 2u);
    assert(duckos_x86_exception_ist(14u) == 3u);
    assert(duckos_x86_exception_ist(0u) == 0u);
    assert(duckos_x86_exception_ist(13u) == 0u);
}

static void test_ist_is_bounded(void) {
    duckos_idt_gate gate = {0};

    assert(duckos_idt_gate_set(&gate, 0x1000u, 0x08u, 7u) == DUCKOS_IDT_OK);
    assert(gate.ist == 7u);
    assert(duckos_idt_gate_set(&gate, 0x1000u, 0x08u, 8u) == DUCKOS_IDT_INVALID_IST);
}

static void test_invalid_inputs_fail_closed(void) {
    duckos_idt_gate gate = {0};

    assert(duckos_idt_gate_set(NULL, 0x1000u, 0x08u, 0u) ==
           DUCKOS_IDT_INVALID_ARGUMENT);
    assert(duckos_idt_gate_set(&gate, 0u, 0x08u, 0u) ==
           DUCKOS_IDT_INVALID_HANDLER);
    assert(duckos_idt_gate_set(&gate, 0x1000u, 0u, 0u) ==
           DUCKOS_IDT_INVALID_SELECTOR);
    assert(duckos_idt_gate_set(&gate, 0x1000u, 0x09u, 0u) ==
           DUCKOS_IDT_INVALID_SELECTOR);
    assert(duckos_idt_gate_target(NULL) == 0u);
}

int main(void) {
    test_gate_layout_and_round_trip();
    test_exception_frame_matches_assembly_layout();
    test_exception_ist_routing();
    test_ist_is_bounded();
    test_invalid_inputs_fail_closed();
    puts("DuckOS IDT contract tests passed");
    return 0;
}
