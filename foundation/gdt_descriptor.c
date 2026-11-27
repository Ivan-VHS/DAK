#include "gdt_descriptor.h"

#include <stddef.h>

_Static_assert(sizeof(dakos_tss64) == 104u, "x86_64 TSS must be 104 bytes");
_Static_assert(offsetof(dakos_tss64, rsp0) == 4u, "TSS RSP0 offset mismatch");
_Static_assert(offsetof(dakos_tss64, ist1) == 36u, "TSS IST1 offset mismatch");
_Static_assert(offsetof(dakos_tss64, ist7) == 84u, "TSS IST7 offset mismatch");
_Static_assert(offsetof(dakos_tss64, iomap_base) == 102u, "TSS I/O map offset mismatch");

dakos_gdt_status dakos_gdt_table_build(
    uint64_t entries[DAK_GDT_ENTRY_COUNT],
    uint64_t tss_base,
    uint32_t tss_limit
) {
    if (entries == NULL) return DAK_GDT_INVALID_ARGUMENT;
    if (tss_limit > DAK_GDT_TSS_LIMIT_MAX) return DAK_GDT_INVALID_TSS_LIMIT;

    entries[0] = UINT64_C(0x0000000000000000);
    entries[1] = UINT64_C(0x00af9a000000ffff); /* ring 0 long-mode code */
    entries[2] = UINT64_C(0x00cf92000000ffff); /* ring 0 data */
    entries[3] = UINT64_C(0x00cff2000000ffff); /* ring 3 data */
    entries[4] = UINT64_C(0x00affa000000ffff); /* ring 3 long-mode code */

    entries[5] =
        ((uint64_t)tss_limit & UINT64_C(0xffff)) |
        ((tss_base & UINT64_C(0xffff)) << 16u) |
        (((tss_base >> 16u) & UINT64_C(0xff)) << 32u) |
        (UINT64_C(0x89) << 40u) |
        (((uint64_t)tss_limit & UINT64_C(0x000f0000)) << 32u) |
        (((tss_base >> 24u) & UINT64_C(0xff)) << 56u);
    entries[6] = tss_base >> 32u;
    return DAK_GDT_OK;
}
