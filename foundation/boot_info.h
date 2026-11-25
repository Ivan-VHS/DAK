#ifndef DUCKOS_BOOT_INFO_H
#define DUCKOS_BOOT_INFO_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_BOOT_INFO_VERSION 1u
#define DUCKOS_BOOT_INFO_V1_SIZE UINT32_C(88)
#define DUCKOS_MEMORY_REGION_V1_SIZE UINT32_C(24)
#define DUCKOS_BOOT_MAX_MEMORY_REGIONS 256u

typedef enum duckos_memory_type {
    DUCKOS_MEMORY_USABLE = 1u,
    DUCKOS_MEMORY_RESERVED = 2u,
    DUCKOS_MEMORY_ACPI_RECLAIMABLE = 3u,
    DUCKOS_MEMORY_ACPI_NVS = 4u,
    DUCKOS_MEMORY_MMIO = 5u,
    DUCKOS_MEMORY_BAD = 6u
} duckos_memory_type;

typedef struct duckos_memory_region {
    uint64_t base;
    uint64_t length;
    uint32_t type;
    uint32_t flags;
} duckos_memory_region;

/*
 * Versioned, fixed-width handoff record.
 * The memory map is passed separately so this structure contains no native
 * pointers and keeps the bootloader/kernel boundary explicit.
 */
typedef struct duckos_boot_info_v1 {
    uint32_t struct_size;
    uint32_t version;
    uint64_t flags;

    uint64_t kernel_phys_base;
    uint64_t kernel_size;

    uint64_t initramfs_phys_base;
    uint64_t initramfs_size;

    uint64_t framebuffer_phys_base;
    uint64_t framebuffer_size;
    uint32_t framebuffer_width;
    uint32_t framebuffer_height;
    uint32_t framebuffer_pitch;
    uint32_t framebuffer_bpp;

    uint32_t memory_region_count;
    uint32_t reserved;
} duckos_boot_info_v1;

#if defined(__cplusplus)
#define DUCKOS_ABI_STATIC_ASSERT(condition, message) static_assert((condition), message)
#else
#define DUCKOS_ABI_STATIC_ASSERT(condition, message) _Static_assert((condition), message)
#endif

/*
 * v1 is a wire/FFI contract, not a compiler-native object layout.
 * Keep these assertions in the public header so every C11/C++ consumer
 * rejects an incompatible packing or alignment configuration at compile time.
 */
DUCKOS_ABI_STATIC_ASSERT(sizeof(duckos_memory_region) == DUCKOS_MEMORY_REGION_V1_SIZE,
                         "duckos_memory_region v1 size changed");
DUCKOS_ABI_STATIC_ASSERT(offsetof(duckos_memory_region, base) == 0u,
                         "duckos_memory_region.base offset changed");
DUCKOS_ABI_STATIC_ASSERT(offsetof(duckos_memory_region, length) == 8u,
                         "duckos_memory_region.length offset changed");
DUCKOS_ABI_STATIC_ASSERT(offsetof(duckos_memory_region, type) == 16u,
                         "duckos_memory_region.type offset changed");
DUCKOS_ABI_STATIC_ASSERT(offsetof(duckos_memory_region, flags) == 20u,
                         "duckos_memory_region.flags offset changed");

DUCKOS_ABI_STATIC_ASSERT(sizeof(duckos_boot_info_v1) == DUCKOS_BOOT_INFO_V1_SIZE,
                         "duckos_boot_info_v1 size changed");
DUCKOS_ABI_STATIC_ASSERT(offsetof(duckos_boot_info_v1, flags) == 8u,
                         "duckos_boot_info_v1.flags offset changed");
DUCKOS_ABI_STATIC_ASSERT(offsetof(duckos_boot_info_v1, kernel_phys_base) == 16u,
                         "duckos_boot_info_v1.kernel_phys_base offset changed");
DUCKOS_ABI_STATIC_ASSERT(offsetof(duckos_boot_info_v1, framebuffer_phys_base) == 48u,
                         "duckos_boot_info_v1.framebuffer_phys_base offset changed");
DUCKOS_ABI_STATIC_ASSERT(offsetof(duckos_boot_info_v1, memory_region_count) == 80u,
                         "duckos_boot_info_v1.memory_region_count offset changed");

#undef DUCKOS_ABI_STATIC_ASSERT

typedef enum duckos_boot_info_status {
    DUCKOS_BOOT_INFO_OK = 0,
    DUCKOS_BOOT_INFO_INVALID_ARGUMENT = -1,
    DUCKOS_BOOT_INFO_UNSUPPORTED_VERSION = -2,
    DUCKOS_BOOT_INFO_INVALID_KERNEL_RANGE = -3,
    DUCKOS_BOOT_INFO_INVALID_INITRAMFS_RANGE = -4,
    DUCKOS_BOOT_INFO_INVALID_FRAMEBUFFER = -5,
    DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP = -6,
    DUCKOS_BOOT_INFO_OVERLAPPING_IMAGES = -7
} duckos_boot_info_status;

/*
 * Validate a bootloader handoff before the kernel consumes its addresses.
 * The caller must already have mapped the boot-info record and memory-map
 * array into readable memory; this routine validates their contents and
 * never dereferences addresses stored inside the handoff itself.
 */
duckos_boot_info_status duckos_boot_info_validate(
    const duckos_boot_info_v1 *info,
    const duckos_memory_region *regions,
    size_t region_count
);

const char *duckos_boot_info_status_name(duckos_boot_info_status status);

#ifdef __cplusplus
}
#endif

#endif
