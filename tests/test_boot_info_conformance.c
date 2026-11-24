#include "boot_info.h"

#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static duckos_boot_info_v1 valid_info(void) {
    duckos_boot_info_v1 info;
    memset(&info, 0, sizeof(info));
    info.struct_size = (uint32_t)sizeof(info);
    info.version = DUCKOS_BOOT_INFO_VERSION;
    info.kernel_phys_base = UINT64_C(0x100000);
    info.kernel_size = UINT64_C(0x100000);
    info.initramfs_phys_base = UINT64_C(0x300000);
    info.initramfs_size = UINT64_C(0x200000);
    info.memory_region_count = 2u;
    return info;
}

static void print_status(
    const duckos_boot_info_v1 *info,
    const duckos_memory_region *regions,
    size_t region_count
) {
    printf("%d\n", (int)duckos_boot_info_validate(info, regions, region_count));
}

int main(void) {
    const duckos_memory_region valid_regions[] = {
        {UINT64_C(0x1000), UINT64_C(0x9f000), DUCKOS_MEMORY_USABLE, 0u},
        {UINT64_C(0x100000), UINT64_C(0x700000), DUCKOS_MEMORY_USABLE, 0u},
    };
    duckos_boot_info_v1 info = valid_info();

    /* Valid handoff with the optional framebuffer left empty. */
    print_status(&info, valid_regions, 2u);

    /* Valid RGB565 framebuffer: 80x100, 160-byte pitch, 16,000-byte extent. */
    info = valid_info();
    info.framebuffer_phys_base = UINT64_C(0xe0000000);
    info.framebuffer_size = UINT64_C(16000);
    info.framebuffer_width = 80u;
    info.framebuffer_height = 100u;
    info.framebuffer_pitch = 160u;
    info.framebuffer_bpp = 16u;
    print_status(&info, valid_regions, 2u);

    /* Unsupported structure size. */
    info = valid_info();
    info.struct_size = 1u;
    print_status(&info, valid_regions, 2u);

    /* Kernel physical range overflows UINT64_MAX. */
    info = valid_info();
    info.kernel_phys_base = UINT64_MAX - UINT64_C(15);
    info.kernel_size = UINT64_C(32);
    print_status(&info, valid_regions, 2u);

    /* An initramfs size without a physical base is invalid. */
    info = valid_info();
    info.initramfs_phys_base = 0u;
    info.initramfs_size = UINT64_C(4096);
    print_status(&info, valid_regions, 2u);

    /* Framebuffer pitch is smaller than width * bytes-per-pixel. */
    info = valid_info();
    info.framebuffer_phys_base = UINT64_C(0xe0000000);
    info.framebuffer_size = UINT64_C(16000);
    info.framebuffer_width = 80u;
    info.framebuffer_height = 100u;
    info.framebuffer_pitch = 100u;
    info.framebuffer_bpp = 16u;
    print_status(&info, valid_regions, 2u);

    /* Declared memory-region count does not match the supplied map. */
    info = valid_info();
    info.memory_region_count = 1u;
    print_status(&info, valid_regions, 2u);

    /* The two memory regions overlap. */
    {
        const duckos_memory_region overlapping[] = {
            {UINT64_C(0x1000), UINT64_C(0x2000), DUCKOS_MEMORY_USABLE, 0u},
            {UINT64_C(0x2000), UINT64_C(0x1000), DUCKOS_MEMORY_USABLE, 0u},
        };
        info = valid_info();
        print_status(&info, overlapping, 2u);
    }

    /* Kernel and initramfs overlap. */
    info = valid_info();
    info.initramfs_phys_base = UINT64_C(0x180000);
    info.initramfs_size = UINT64_C(0x100000);
    print_status(&info, valid_regions, 2u);

    return 0;
}
