#include "boot_info.h"

#ifdef NDEBUG
#undef NDEBUG
#endif

#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

static void test_v1_abi_layout(void) {
    assert(sizeof(duckos_memory_region) == DUCKOS_MEMORY_REGION_V1_SIZE);
    assert(offsetof(duckos_memory_region, base) == 0u);
    assert(offsetof(duckos_memory_region, length) == 8u);
    assert(offsetof(duckos_memory_region, type) == 16u);
    assert(offsetof(duckos_memory_region, flags) == 20u);

    assert(sizeof(duckos_boot_info_v1) == DUCKOS_BOOT_INFO_V1_SIZE);
    assert(offsetof(duckos_boot_info_v1, struct_size) == 0u);
    assert(offsetof(duckos_boot_info_v1, version) == 4u);
    assert(offsetof(duckos_boot_info_v1, flags) == 8u);
    assert(offsetof(duckos_boot_info_v1, kernel_phys_base) == 16u);
    assert(offsetof(duckos_boot_info_v1, framebuffer_phys_base) == 48u);
    assert(offsetof(duckos_boot_info_v1, memory_region_count) == 80u);
}

static duckos_boot_info_v1 valid_info(void) {
    duckos_boot_info_v1 info;
    memset(&info, 0, sizeof(info));
    info.struct_size = (uint32_t)sizeof(info);
    info.version = DUCKOS_BOOT_INFO_VERSION;
    info.kernel_phys_base = 0x100000u;
    info.kernel_size = 0x100000u;
    info.initramfs_phys_base = 0x300000u;
    info.initramfs_size = 0x200000u;
    info.memory_region_count = 2u;
    return info;
}

static void test_valid_handoff(void) {
    const duckos_memory_region regions[] = {
        {0x1000u, 0x9f000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x100000u, 0x700000u, DUCKOS_MEMORY_USABLE, 0u},
    };
    duckos_boot_info_v1 info = valid_info();

    assert(duckos_boot_info_validate(&info, regions, 2u) == DUCKOS_BOOT_INFO_OK);
    assert(strcmp(duckos_boot_info_status_name(DUCKOS_BOOT_INFO_OK), "ok") == 0);
}

static void test_initramfs_is_optional_but_must_be_consistent(void) {
    const duckos_memory_region regions[] = {
        {0x1000u, 0x9f000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x100000u, 0x700000u, DUCKOS_MEMORY_USABLE, 0u},
    };
    duckos_boot_info_v1 info = valid_info();

    info.initramfs_phys_base = 0u;
    info.initramfs_size = 0u;
    assert(duckos_boot_info_validate(&info, regions, 2u) == DUCKOS_BOOT_INFO_OK);

    info.initramfs_size = 4096u;
    assert(duckos_boot_info_validate(&info, regions, 2u) ==
           DUCKOS_BOOT_INFO_INVALID_INITRAMFS_RANGE);
}

static void test_kernel_and_initramfs_ranges_are_checked(void) {
    const duckos_memory_region regions[] = {
        {0x1000u, 0x9f000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x100000u, 0x700000u, DUCKOS_MEMORY_USABLE, 0u},
    };
    duckos_boot_info_v1 info = valid_info();

    info.kernel_phys_base = UINT64_MAX - 15u;
    info.kernel_size = 32u;
    assert(duckos_boot_info_validate(&info, regions, 2u) ==
           DUCKOS_BOOT_INFO_INVALID_KERNEL_RANGE);

    info = valid_info();
    info.initramfs_phys_base = 0x180000u;
    info.initramfs_size = 0x100000u;
    assert(duckos_boot_info_validate(&info, regions, 2u) ==
           DUCKOS_BOOT_INFO_OVERLAPPING_IMAGES);
}

static void test_framebuffer_contract(void) {
    const duckos_memory_region regions[] = {
        {0x1000u, 0x9f000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x100000u, 0x700000u, DUCKOS_MEMORY_USABLE, 0u},
    };
    duckos_boot_info_v1 info = valid_info();

    info.framebuffer_phys_base = 0xe0000000u;
    info.framebuffer_size = 160u * 100u;
    info.framebuffer_width = 80u;
    info.framebuffer_height = 100u;
    info.framebuffer_pitch = 160u;
    info.framebuffer_bpp = 16u;
    assert(duckos_boot_info_validate(&info, regions, 2u) == DUCKOS_BOOT_INFO_OK);

    info.framebuffer_pitch = 100u;
    assert(duckos_boot_info_validate(&info, regions, 2u) ==
           DUCKOS_BOOT_INFO_INVALID_FRAMEBUFFER);

    info.framebuffer_pitch = 160u;
    info.framebuffer_size = 100u;
    assert(duckos_boot_info_validate(&info, regions, 2u) ==
           DUCKOS_BOOT_INFO_INVALID_FRAMEBUFFER);
}

static void test_memory_map_order_overlap_and_count(void) {
    duckos_boot_info_v1 info = valid_info();
    const duckos_memory_region ordered[] = {
        {0x1000u, 0x9f000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x100000u, 0x700000u, DUCKOS_MEMORY_USABLE, 0u},
    };
    const duckos_memory_region unsorted[] = {
        {0x100000u, 0x1000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x1000u, 0x1000u, DUCKOS_MEMORY_USABLE, 0u},
    };
    const duckos_memory_region overlapping[] = {
        {0x1000u, 0x2000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x2000u, 0x1000u, DUCKOS_MEMORY_RESERVED, 0u},
    };
    const duckos_memory_region bad_type[] = {
        {0x1000u, 0x1000u, 99u, 0u},
        {0x3000u, 0x1000u, DUCKOS_MEMORY_USABLE, 0u},
    };

    assert(duckos_boot_info_validate(&info, ordered, 1u) ==
           DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP);
    assert(duckos_boot_info_validate(&info, unsorted, 2u) ==
           DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP);
    assert(duckos_boot_info_validate(&info, overlapping, 2u) ==
           DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP);
    assert(duckos_boot_info_validate(&info, bad_type, 2u) ==
           DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP);
    assert(duckos_boot_info_validate(&info, ordered, 257u) ==
           DUCKOS_BOOT_INFO_INVALID_MEMORY_MAP);
}

static void test_version_and_arguments_fail_closed(void) {
    const duckos_memory_region regions[] = {
        {0x1000u, 0x9f000u, DUCKOS_MEMORY_USABLE, 0u},
        {0x100000u, 0x700000u, DUCKOS_MEMORY_USABLE, 0u},
    };
    duckos_boot_info_v1 info = valid_info();

    assert(duckos_boot_info_validate(NULL, regions, 2u) ==
           DUCKOS_BOOT_INFO_INVALID_ARGUMENT);
    assert(duckos_boot_info_validate(&info, NULL, 2u) ==
           DUCKOS_BOOT_INFO_INVALID_ARGUMENT);

    info.version = 99u;
    assert(duckos_boot_info_validate(&info, regions, 2u) ==
           DUCKOS_BOOT_INFO_UNSUPPORTED_VERSION);
    info = valid_info();
    info.struct_size = 1u;
    assert(duckos_boot_info_validate(&info, regions, 2u) ==
           DUCKOS_BOOT_INFO_UNSUPPORTED_VERSION);
}

int main(void) {
    test_v1_abi_layout();
    test_valid_handoff();
    test_initramfs_is_optional_but_must_be_consistent();
    test_kernel_and_initramfs_ranges_are_checked();
    test_framebuffer_contract();
    test_memory_map_order_overlap_and_count();
    test_version_and_arguments_fail_closed();
    return 0;
}
