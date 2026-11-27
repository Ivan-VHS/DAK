#include "gdt_descriptor.h"

#ifdef NDEBUG
#undef NDEBUG
#endif
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

static void test_tss_layout(void) {
    assert(sizeof(dakos_tss64) == 104u);
    assert(offsetof(dakos_tss64, rsp0) == 4u);
    assert(offsetof(dakos_tss64, ist1) == 36u);
    assert(offsetof(dakos_tss64, ist2) == 44u);
    assert(offsetof(dakos_tss64, ist3) == 52u);
    assert(offsetof(dakos_tss64, ist7) == 84u);
    assert(offsetof(dakos_tss64, iomap_base) == 102u);
}

static void test_segment_descriptors(void) {
    uint64_t entries[DAK_GDT_ENTRY_COUNT] = {0u};
    const uint64_t tss_base = UINT64_C(0xffff800012345000);
    const uint32_t tss_limit = 103u;
    assert(dakos_gdt_table_build(entries, tss_base, tss_limit) == DAK_GDT_OK);
    assert(entries[0] == 0u);
    assert(entries[1] == UINT64_C(0x00af9a000000ffff));
    assert(entries[2] == UINT64_C(0x00cf92000000ffff));
    assert(entries[3] == UINT64_C(0x00cff2000000ffff));
    assert(entries[4] == UINT64_C(0x00affa000000ffff));
    const uint64_t low = entries[5];
    const uint64_t reconstructed_base =
        ((low >> 16u) & UINT64_C(0xffff)) |
        (((low >> 32u) & UINT64_C(0xff)) << 16u) |
        (((low >> 56u) & UINT64_C(0xff)) << 24u) |
        (entries[6] << 32u);
    const uint32_t reconstructed_limit =
        (uint32_t)(low & UINT64_C(0xffff)) |
        (uint32_t)((low >> 32u) & UINT64_C(0x000f0000));
    assert(reconstructed_base == tss_base);
    assert(reconstructed_limit == tss_limit);
    assert(((low >> 40u) & UINT64_C(0xff)) == UINT64_C(0x89));
}

static void test_invalid_descriptor_arguments(void) {
    uint64_t entries[DAK_GDT_ENTRY_COUNT] = {0u};
    assert(dakos_gdt_table_build(NULL, 0x1000u, 103u) == DAK_GDT_INVALID_ARGUMENT);
    assert(dakos_gdt_table_build(entries, 0x1000u, DAK_GDT_TSS_LIMIT_MAX + 1u) ==
        DAK_GDT_INVALID_TSS_LIMIT);
}

int main(void) {
    test_tss_layout();
    test_segment_descriptors();
    test_invalid_descriptor_arguments();
    puts("Dak GDT/TSS descriptor tests passed");
    return 0;
}
