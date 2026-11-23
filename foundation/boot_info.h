#ifndef DUCKOS_BOOT_INFO_H
#define DUCKOS_BOOT_INFO_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_BOOT_INFO_VERSION 1u
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
