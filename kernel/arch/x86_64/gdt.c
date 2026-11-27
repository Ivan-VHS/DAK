#include "gdt.h"

#include "gdt_descriptor.h"

#include <stddef.h>
#include <stdint.h>

#define KERNEL_STACK_BYTES 32768u
#define EXCEPTION_STACK_BYTES 16384u

static uint64_t gdt_entries[DAKOS_GDT_ENTRY_COUNT] __attribute__((aligned(16)));
static dakos_tss64 tss __attribute__((aligned(16)));
static uint8_t kernel_privilege_stack[KERNEL_STACK_BYTES] __attribute__((aligned(16)));
static uint8_t double_fault_stack[EXCEPTION_STACK_BYTES] __attribute__((aligned(16)));
static uint8_t nmi_stack[EXCEPTION_STACK_BYTES] __attribute__((aligned(16)));
static uint8_t page_fault_stack[EXCEPTION_STACK_BYTES] __attribute__((aligned(16)));
static int gdt_initialized;

typedef struct __attribute__((packed)) dakos_gdtr {
    uint16_t limit;
    uint64_t base;
} dakos_gdtr;

extern void dakos_x86_gdt_load(
    const dakos_gdtr *descriptor,
    uint16_t tss_selector
);

int dakos_x86_gdt_init(void) {
    if (gdt_initialized) return 1;

    tss.rsp0 = (uint64_t)(uintptr_t)(kernel_privilege_stack + sizeof(kernel_privilege_stack));
    tss.ist1 = (uint64_t)(uintptr_t)(double_fault_stack + sizeof(double_fault_stack));
    tss.ist2 = (uint64_t)(uintptr_t)(nmi_stack + sizeof(nmi_stack));
    tss.ist3 = (uint64_t)(uintptr_t)(page_fault_stack + sizeof(page_fault_stack));
    /* An offset equal to the TSS size means that no I/O permission bitmap exists. */
    tss.iomap_base = (uint16_t)sizeof(tss);

    if (dakos_gdt_table_build(
            gdt_entries,
            (uint64_t)(uintptr_t)&tss,
            (uint32_t)(sizeof(tss) - 1u)
        ) != DAKOS_GDT_OK) {
        return 0;
    }

    const dakos_gdtr descriptor = {
        (uint16_t)(sizeof(gdt_entries) - 1u),
        (uint64_t)(uintptr_t)gdt_entries
    };
    dakos_x86_gdt_load(&descriptor, DAKOS_GDT_TSS_SELECTOR);
    gdt_initialized = 1;
    return 1;
}
