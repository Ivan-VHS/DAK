#ifndef DAK_GDT_DESCRIPTOR_H
#define DAK_GDT_DESCRIPTOR_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DAK_GDT_ENTRY_COUNT 7u
#define DAK_GDT_KERNEL_CODE_SELECTOR UINT16_C(0x08)
#define DAK_GDT_KERNEL_DATA_SELECTOR UINT16_C(0x10)
#define DAK_GDT_USER_DATA_SELECTOR UINT16_C(0x1b)
#define DAK_GDT_USER_CODE_SELECTOR UINT16_C(0x23)
#define DAK_GDT_TSS_SELECTOR UINT16_C(0x28)
#define DAK_GDT_TSS_LIMIT_MAX UINT32_C(0x000fffff)

typedef struct __attribute__((packed)) dakos_tss64 {
    uint32_t reserved0;
    uint64_t rsp0;
    uint64_t rsp1;
    uint64_t rsp2;
    uint64_t reserved1;
    uint64_t ist1;
    uint64_t ist2;
    uint64_t ist3;
    uint64_t ist4;
    uint64_t ist5;
    uint64_t ist6;
    uint64_t ist7;
    uint64_t reserved2;
    uint16_t reserved3;
    uint16_t iomap_base;
} dakos_tss64;

typedef enum dakos_gdt_status {
    DAK_GDT_OK = 0,
    DAK_GDT_INVALID_ARGUMENT,
    DAK_GDT_INVALID_TSS_LIMIT
} dakos_gdt_status;

/* Build null, ring-0/ring-3 flat segments and a 64-bit available-TSS descriptor. */
dakos_gdt_status dakos_gdt_table_build(
    uint64_t entries[DAK_GDT_ENTRY_COUNT],
    uint64_t tss_base,
    uint32_t tss_limit
);

#ifdef __cplusplus
}
#endif

#endif
