#include "boot_info.h"

#include <limits.h>

static int range_end(uint64_t base, uint64_t length, uint64_t *end) {
    if (length == 0u || end == NULL || base > UINT64_MAX - length) {
        return 0;
    }
    *end = base + length;
    return 1;
}

static int ranges_overlap(
    uint64_t first_begin,
    uint64_t first_end,
    uint64_t second_begin,
    uint64_t second_end
) {
    return first_begin < second_end && second_begin < first_end;
}

static int memory_type_valid(uint32_t type) {
    return type >= (uint32_t)DUCKOS_MEMORY_USABLE &&
        type <= (uint32_t)DUCKOS_MEMORY_BAD;
}

static int validate_framebuffer(const duckos_boot_info_v1 *info) {
    const int any_field =
        info->framebuffer_phys_base != 0u ||
        info->framebuffer_size != 0u ||
        info->framebuffer_width != 0u ||
        info->framebuffer_height != 0u ||
        info->framebuffer_pitch != 0u ||
        info->framebuffer_bpp != 0u;
    uint64_t bytes_per_pixel;
    uint64_t minimum_pitch;
    uint64_t required_size;
    uint64_t end;

    if (!any_field) return 1;

    if (info->framebuffer_phys_base == 0u ||
        info->framebuffer_size == 0u ||
        info->framebuffer_width == 0u ||
        info->framebuffer_height == 0u ||
        info->framebuffer_pitch == 0u ||
        (info->framebuffer_bpp != 16u &&
         info->framebuffer_bpp != 24u &&
         info->framebuffer_bpp != 32u)) {
        return 0;
    }

    bytes_per_pixel = (uint64_t)info->framebuffer_bpp / 8u;
    minimum_pitch = (uint64_t)info->framebuffer_width * bytes_per_pixel;
    if ((uint64_t)info->framebuffer_pitch < minimum_pitch) return 0;

    required_size = (uint64_t)info->framebuffer_pitch *
        (uint64_t)info->framebuffer_height;
    if (required_size > info->framebuffer_size) return 0;

    return range_end(
        info->framebuffer_phys_base,
        info->framebuffer_size,
        &end
    );
}

duckos_boot_info_status duckos_boot_info_validate(
    const duckos_boot_info_v1 *info,
    const duckos_memory_region *regions,
    size_t region_count
) {
    uint64_t kernel_end;
    uint64_t initramfs_end = 0u;
    uint64_t previous_end = 0u;

    if (info == NULL || regions == NULL) {
        return DUCKOS_BOOT_INFO_INVALID_ARGUMENT;
    }
    if (info->struct_size < (uint32_t)sizeof(*info) ||
        info->version != DUCKOS_BOOT_INFO_VERSION) {
        return DUCKOS_BOOT_INFO_UNSUPPORTED_VERSION;
    }
    if (info->memory_region_count != region_count ||
        region_count == 0u ||
        region_count > DUCKOS_BOOT_MAX_MEMORY_REGIONS) {
        return DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP;
    }
    if (!range_end(info->kernel_phys_base, info->kernel_size, &kernel_end)) {
        return DUCKOS_BOOT_INFO_INVALID_KERNEL_RANGE;
    }

    if ((info->initramfs_phys_base == 0u) != (info->initramfs_size == 0u)) {
        return DUCKOS_BOOT_INFO_INVALID_INITRAMFS_RANGE;
    }
    if (info->initramfs_size != 0u &&
        !range_end(info->initramfs_phys_base, info->initramfs_size, &initramfs_end)) {
        return DUCKOS_BOOT_INFO_INVALID_INITRAMFS_RANGE;
    }
    if (!validate_framebuffer(info)) {
        return DUCKOS_BOOT_INFO_INVALID_FRAMEBUFFER;
    }

    for (size_t index = 0u; index < region_count; ++index) {
        const duckos_memory_region *region = &regions[index];
        uint64_t current_end;

        if (region->length == 0u ||
            !memory_type_valid(region->type) ||
            !range_end(region->base, region->length, &current_end)) {
            return DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP;
        }
        if (index != 0u && region->base < previous_end) {
            return DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP;
        }
        previous_end = current_end;
    }

    if (info->initramfs_size != 0u &&
        ranges_overlap(
            info->kernel_phys_base, kernel_end,
            info->initramfs_phys_base, initramfs_end
        )) {
        return DUCKOS_BOOT_INFO_OVERLAPPING_IMAGES;
    }

    return DUCKOS_BOOT_INFO_OK;
}

const char *duckos_boot_info_status_name(duckos_boot_info_status status) {
    switch (status) {
        case DUCKOS_BOOT_INFO_OK: return "ok";
        case DUCKOS_BOOT_INFO_INVALID_ARGUMENT: return "invalid argument";
        case DUCKOS_BOOT_INFO_UNSUPPORTED_VERSION: return "unsupported boot-info version";
        case DUCKOS_BOOT_INFO_INVALID_KERNEL_RANGE: return "invalid kernel range";
        case DUCKOS_BOOT_INFO_INVALID_INITRAMFS_RANGE: return "invalid initramfs range";
        case DUCKOS_BOOT_INFO_INVALID_FRAMEBUFFER: return "invalid framebuffer description";
        case DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP: return "invalid memory map";
        case DUCKOS_BOOT_INFO_OVERLAPPING_IMAGES: return "kernel and initramfs overlap";
        default: return "unknown boot-info status";
    }
}
