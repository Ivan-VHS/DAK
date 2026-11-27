#ifndef DAKOS_BOOT_INFO_H
#define DAKOS_BOOT_INFO_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DAKOS_BOOT_INFO_VERSION 1u
#define DAKOS_BOOT_MAX_MEMORY_REGIONS 256u

typedef enum dakos_memory_type {
    DAKOS_MEMORY_USABLE = 1u,
    DAKOS_MEMORY_RESERVED = 2u,
    DAKOS_MEMORY_ACPI_RECLAIMABLE = 3u,
    DAKOS_MEMORY_ACPI_NVS = 4u,
    DAKOS_MEMORY_MMIO = 5u,
    DAKOS_MEMORY_BAD = 6u
} dakos_memory_type;

typedef struct dakos_memory_region {
    uint64_t base;
    uint64_t length;
    uint32_t type;
    uint32_t flags;
} dakos_memory_region;

/*
 * Versioned, fixed-width handoff record.
 * The memory map is passed separately so this structure contains no native
 * pointers and keeps the bootloader/kernel boundary explicit.
 */
typedef struct dakos_boot_info_v1 {
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
} dakos_boot_info_v1;

typedef enum dakos_boot_info_status {
    DAKOS_BOOT_INFO_OK = 0,
    DAKOS_BOOT_INFO_INVALID_ARGUMENT = -1,
    DAKOS_BOOT_INFO_UNSUPPORTED_VERSION = -2,
    DAKOS_BOOT_INFO_INVALID_KERNEL_RANGE = -3,
    DAKOS_BOOT_INFO_INVALID_INITRAMFS_RANGE = -4,
    DAKOS_BOOT_INFO_INVALID_FRAMEBUFFER = -5,
    DAKOS_BOOT_INFO_INVALID_MEMORY_MAP = -6,
    DAKOS_BOOT_INFO_OVERLAPPING_IMAGES = -7,
    DAKOS_BOOT_INFO_KERNEL_NOT_RESERVED = -8,
    DAKOS_BOOT_INFO_INITRAMFS_NOT_RESERVED = -9,
    DAKOS_BOOT_INFO_FRAMEBUFFER_NOT_MMIO = -10
} dakos_boot_info_status;

/*
 * Validate a bootloader handoff before the kernel consumes its addresses.
 * The caller must already have mapped the boot-info record and memory-map
 * array into readable memory; this routine validates their contents and
 * never dereferences addresses stored inside the handoff itself.
 */
dakos_boot_info_status dakos_boot_info_validate(
    const dakos_boot_info_v1 *info,
    const dakos_memory_region *regions,
    size_t region_count
);

const char *dakos_boot_info_status_name(dakos_boot_info_status status);

#ifdef __cplusplus
}
#endif

#endif
