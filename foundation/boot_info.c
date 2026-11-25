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
    return type >= (uint32_t)DAK_MEMORY_USABLE &&
        type <= (uint32_t)DAK_MEMORY_BAD;
}


static int range_covered_by_type(
    const dak_memory_region *regions,
    size_t region_count,
    uint64_t begin,
    uint64_t end,
    uint32_t expected_type
) {
    uint64_t cursor = begin;

    for (size_t index = 0u; index < region_count; ++index) {
        const dak_memory_region *region = &regions[index];
        uint64_t region_end;

        if (region->type != expected_type) continue;
        if (!range_end(region->base, region->length, &region_end)) return 0;
        if (region_end <= cursor) continue;
        if (region->base > cursor) return 0;

        cursor = region_end;
        if (cursor >= end) return 1;
    }
    return 0;
}

static int validate_framebuffer(const dak_boot_info_v1 *info) {
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

dak_boot_info_status dak_boot_info_validate(
    const dak_boot_info_v1 *info,
    const dak_memory_region *regions,
    size_t region_count
) {
    uint64_t kernel_end;
    uint64_t initramfs_end = 0u;
    uint64_t previous_end = 0u;
    uint64_t framebuffer_end = 0u;

    if (info == NULL || regions == NULL) {
        return DAK_BOOT_INFO_INVALID_ARGUMENT;
    }
    if (info->struct_size < (uint32_t)sizeof(*info) ||
        info->version != DAK_BOOT_INFO_VERSION) {
        return DAK_BOOT_INFO_UNSUPPORTED_VERSION;
    }
    if (info->memory_region_count != region_count ||
        region_count == 0u ||
        region_count > DAK_BOOT_MAX_MEMORY_REGIONS) {
        return DAK_BOOT_INFO_INVALID_MEMORY_MAP;
    }
    if (!range_end(info->kernel_phys_base, info->kernel_size, &kernel_end)) {
        return DAK_BOOT_INFO_INVALID_KERNEL_RANGE;
    }

    if ((info->initramfs_phys_base == 0u) != (info->initramfs_size == 0u)) {
        return DAK_BOOT_INFO_INVALID_INITRAMFS_RANGE;
    }
    if (info->initramfs_size != 0u &&
        !range_end(info->initramfs_phys_base, info->initramfs_size, &initramfs_end)) {
        return DAK_BOOT_INFO_INVALID_INITRAMFS_RANGE;
    }
    if (!validate_framebuffer(info)) {
        return DAK_BOOT_INFO_INVALID_FRAMEBUFFER;
    }

    for (size_t index = 0u; index < region_count; ++index) {
        const dak_memory_region *region = &regions[index];
        uint64_t current_end;

        if (region->length == 0u ||
            !memory_type_valid(region->type) ||
            !range_end(region->base, region->length, &current_end)) {
            return DAK_BOOT_INFO_INVALID_MEMORY_MAP;
        }
        if (index != 0u && region->base < previous_end) {
            return DAK_BOOT_INFO_INVALID_MEMORY_MAP;
        }
        previous_end = current_end;
    }

    if (!range_covered_by_type(
            regions, region_count,
            info->kernel_phys_base, kernel_end,
            (uint32_t)DAK_MEMORY_RESERVED)) {
        return DAK_BOOT_INFO_KERNEL_NOT_RESERVED;
    }

    if (info->initramfs_size != 0u &&
        ranges_overlap(
            info->kernel_phys_base, kernel_end,
            info->initramfs_phys_base, initramfs_end
        )) {
        return DAK_BOOT_INFO_OVERLAPPING_IMAGES;
    }

    if (info->initramfs_size != 0u &&
        !range_covered_by_type(
            regions, region_count,
            info->initramfs_phys_base, initramfs_end,
            (uint32_t)DAK_MEMORY_RESERVED)) {
        return DAK_BOOT_INFO_INITRAMFS_NOT_RESERVED;
    }

    if (info->framebuffer_size != 0u) {
        if (!range_end(
                info->framebuffer_phys_base,
                info->framebuffer_size,
                &framebuffer_end) ||
            !range_covered_by_type(
                regions, region_count,
                info->framebuffer_phys_base, framebuffer_end,
                (uint32_t)DAK_MEMORY_MMIO)) {
            return DAK_BOOT_INFO_FRAMEBUFFER_NOT_MMIO;
        }
    }

    return DAK_BOOT_INFO_OK;
}

const char *dak_boot_info_status_name(dak_boot_info_status status) {
    switch (status) {
        case DAK_BOOT_INFO_OK: return "ok";
        case DAK_BOOT_INFO_INVALID_ARGUMENT: return "invalid argument";
        case DAK_BOOT_INFO_UNSUPPORTED_VERSION: return "unsupported boot-info version";
        case DAK_BOOT_INFO_INVALID_KERNEL_RANGE: return "invalid kernel range";
        case DAK_BOOT_INFO_INVALID_INITRAMFS_RANGE: return "invalid initramfs range";
        case DAK_BOOT_INFO_INVALID_FRAMEBUFFER: return "invalid framebuffer description";
        case DAK_BOOT_INFO_INVALID_MEMORY_MAP: return "invalid memory map";
        case DAK_BOOT_INFO_OVERLAPPING_IMAGES: return "kernel and initramfs overlap";
        case DAK_BOOT_INFO_KERNEL_NOT_RESERVED: return "kernel range is not reserved";
        case DAK_BOOT_INFO_INITRAMFS_NOT_RESERVED: return "initramfs range is not reserved";
        case DAK_BOOT_INFO_FRAMEBUFFER_NOT_MMIO: return "framebuffer range is not MMIO";
        default: return "unknown boot-info status";
    }
}
