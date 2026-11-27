#include "boot_info.h"

#ifdef NDEBUG
#undef NDEBUG
#endif

#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>

_Static_assert(sizeof(dakos_memory_region) == 24u,
               "memory-region v1 size must remain stable");
_Static_assert(_Alignof(dakos_memory_region) == 8u,
               "memory-region v1 alignment must remain stable");
_Static_assert(offsetof(dakos_memory_region, type) == 16u,
               "memory-region type offset must remain stable");
_Static_assert(offsetof(dakos_memory_region, flags) == 20u,
               "memory-region flags offset must remain stable");

_Static_assert(sizeof(dakos_boot_info_v1) == 88u,
               "boot-info v1 size must remain stable");
_Static_assert(_Alignof(dakos_boot_info_v1) == 8u,
               "boot-info v1 alignment must remain stable");
_Static_assert(offsetof(dakos_boot_info_v1, flags) == 8u,
               "boot-info flags offset must remain stable");
_Static_assert(offsetof(dakos_boot_info_v1, kernel_phys_base) == 16u,
               "boot-info kernel base offset must remain stable");
_Static_assert(offsetof(dakos_boot_info_v1, initramfs_phys_base) == 32u,
               "boot-info initramfs base offset must remain stable");
_Static_assert(offsetof(dakos_boot_info_v1, framebuffer_phys_base) == 48u,
               "boot-info framebuffer base offset must remain stable");
_Static_assert(offsetof(dakos_boot_info_v1, framebuffer_width) == 64u,
               "boot-info framebuffer width offset must remain stable");
_Static_assert(offsetof(dakos_boot_info_v1, memory_region_count) == 80u,
               "boot-info memory-map count offset must remain stable");
_Static_assert(offsetof(dakos_boot_info_v1, reserved) == 84u,
               "boot-info reserved offset must remain stable");

typedef struct dakos_boot_info_v1_extended {
    dakos_boot_info_v1 v1;
    uint8_t extension[16];
} dakos_boot_info_v1_extended;

_Static_assert(offsetof(dakos_boot_info_v1_extended, extension) ==
                   sizeof(dakos_boot_info_v1),
               "boot-info v1 extensions must append after the stable prefix");

static const dakos_memory_region valid_regions[] = {
    {0x1000u, 0x9f000u, DAK_MEMORY_USABLE, 0u},
    {0x100000u, 0x700000u, DAK_MEMORY_RESERVED, 0u},
    {0xe0000000u, 0x10000u, DAK_MEMORY_MMIO, 0u},
};

static dakos_boot_info_v1 valid_info(void) {
    dakos_boot_info_v1 info;
    memset(&info, 0, sizeof(info));
    info.struct_size = (uint32_t)sizeof(info);
    info.version = DAK_BOOT_INFO_VERSION;
    info.kernel_phys_base = 0x100000u;
    info.kernel_size = 0x100000u;
    info.initramfs_phys_base = 0x300000u;
    info.initramfs_size = 0x200000u;
    info.memory_region_count = 3u;
    return info;
}

static void test_valid_handoff(void) {
    dakos_boot_info_v1 info = valid_info();

    assert(dakos_boot_info_validate(
        &info, valid_regions, sizeof(valid_regions) / sizeof(valid_regions[0])
    ) == DAK_BOOT_INFO_OK);
    assert(strcmp(dakos_boot_info_status_name(DAK_BOOT_INFO_OK), "ok") == 0);
}

static void test_initramfs_is_optional_but_must_be_consistent(void) {
    dakos_boot_info_v1 info = valid_info();

    info.initramfs_phys_base = 0u;
    info.initramfs_size = 0u;
    assert(dakos_boot_info_validate(
        &info, valid_regions, sizeof(valid_regions) / sizeof(valid_regions[0])
    ) == DAK_BOOT_INFO_OK);

    info.initramfs_size = 4096u;
    assert(dakos_boot_info_validate(
        &info, valid_regions, sizeof(valid_regions) / sizeof(valid_regions[0])
    ) == DAK_BOOT_INFO_INVALID_INITRAMFS_RANGE);
}

static void test_kernel_and_initramfs_ranges_are_checked(void) {
    dakos_boot_info_v1 info = valid_info();

    info.kernel_phys_base = UINT64_MAX - 15u;
    info.kernel_size = 32u;
    assert(dakos_boot_info_validate(
        &info, valid_regions, sizeof(valid_regions) / sizeof(valid_regions[0])
    ) == DAK_BOOT_INFO_INVALID_KERNEL_RANGE);

    info = valid_info();
    info.initramfs_phys_base = 0x180000u;
    info.initramfs_size = 0x100000u;
    assert(dakos_boot_info_validate(
        &info, valid_regions, sizeof(valid_regions) / sizeof(valid_regions[0])
    ) == DAK_BOOT_INFO_OVERLAPPING_IMAGES);
}

static void test_reserved_and_mmio_ownership(void) {
    dakos_boot_info_v1 info = valid_info();
    dakos_memory_region regions[3];

    memcpy(regions, valid_regions, sizeof(regions));
    regions[1].type = DAK_MEMORY_USABLE;
    assert(dakos_boot_info_validate(&info, regions, 3u) ==
           DAK_BOOT_INFO_KERNEL_NOT_RESERVED);

    memcpy(regions, valid_regions, sizeof(regions));
    info = valid_info();
    info.initramfs_phys_base = 0x810000u;
    info.initramfs_size = 0x1000u;
    assert(dakos_boot_info_validate(&info, regions, 3u) ==
           DAK_BOOT_INFO_INITRAMFS_NOT_RESERVED);

    memcpy(regions, valid_regions, sizeof(regions));
    info = valid_info();
    info.framebuffer_phys_base = 0xe0000000u;
    info.framebuffer_size = 160u * 100u;
    info.framebuffer_width = 80u;
    info.framebuffer_height = 100u;
    info.framebuffer_pitch = 160u;
    info.framebuffer_bpp = 16u;
    assert(dakos_boot_info_validate(&info, regions, 3u) == DAK_BOOT_INFO_OK);

    info.framebuffer_phys_base = 0xe0020000u;
    assert(dakos_boot_info_validate(&info, regions, 3u) ==
           DAK_BOOT_INFO_FRAMEBUFFER_NOT_MMIO);
}

static void test_framebuffer_contract(void) {
    dakos_boot_info_v1 info = valid_info();

    info.framebuffer_phys_base = 0xe0000000u;
    info.framebuffer_size = 160u * 100u;
    info.framebuffer_width = 80u;
    info.framebuffer_height = 100u;
    info.framebuffer_pitch = 160u;
    info.framebuffer_bpp = 16u;
    assert(dakos_boot_info_validate(&info, valid_regions, 3u) ==
           DAK_BOOT_INFO_OK);

    info.framebuffer_pitch = 100u;
    assert(dakos_boot_info_validate(&info, valid_regions, 3u) ==
           DAK_BOOT_INFO_INVALID_FRAMEBUFFER);

    info.framebuffer_pitch = 160u;
    info.framebuffer_size = 100u;
    assert(dakos_boot_info_validate(&info, valid_regions, 3u) ==
           DAK_BOOT_INFO_INVALID_FRAMEBUFFER);
}

static void test_memory_map_order_overlap_and_count(void) {
    dakos_boot_info_v1 info = valid_info();
    const dakos_memory_region ordered[] = {
        {0x1000u, 0x9f000u, DAK_MEMORY_USABLE, 0u},
        {0x100000u, 0x700000u, DAK_MEMORY_RESERVED, 0u},
        {0xe0000000u, 0x10000u, DAK_MEMORY_MMIO, 0u},
    };
    const dakos_memory_region unsorted[] = {
        {0x100000u, 0x1000u, DAK_MEMORY_RESERVED, 0u},
        {0x1000u, 0x1000u, DAK_MEMORY_USABLE, 0u},
        {0xe0000000u, 0x10000u, DAK_MEMORY_MMIO, 0u},
    };
    const dakos_memory_region overlapping[] = {
        {0x1000u, 0x2000u, DAK_MEMORY_USABLE, 0u},
        {0x2000u, 0x1000u, DAK_MEMORY_RESERVED, 0u},
        {0xe0000000u, 0x10000u, DAK_MEMORY_MMIO, 0u},
    };
    const dakos_memory_region bad_type[] = {
        {0x1000u, 0x1000u, 99u, 0u},
        {0x3000u, 0x1000u, DAK_MEMORY_USABLE, 0u},
        {0xe0000000u, 0x10000u, DAK_MEMORY_MMIO, 0u},
    };

    assert(dakos_boot_info_validate(&info, ordered, 3u) == DAK_BOOT_INFO_OK);
    assert(dakos_boot_info_validate(&info, unsorted, 3u) ==
           DAK_BOOT_INFO_INVALID_MEMORY_MAP);
    assert(dakos_boot_info_validate(&info, overlapping, 3u) ==
           DAK_BOOT_INFO_INVALID_MEMORY_MAP);
    assert(dakos_boot_info_validate(&info, bad_type, 3u) ==
           DAK_BOOT_INFO_INVALID_MEMORY_MAP);
    assert(dakos_boot_info_validate(&info, ordered, 257u) ==
           DAK_BOOT_INFO_INVALID_MEMORY_MAP);
}

static void test_version_and_arguments_fail_closed(void) {
    dakos_boot_info_v1 info = valid_info();

    assert(dakos_boot_info_validate(NULL, valid_regions, 3u) ==
           DAK_BOOT_INFO_INVALID_ARGUMENT);
    assert(dakos_boot_info_validate(&info, NULL, 3u) ==
           DAK_BOOT_INFO_INVALID_ARGUMENT);

    info.version = 99u;
    assert(dakos_boot_info_validate(&info, valid_regions, 3u) ==
           DAK_BOOT_INFO_UNSUPPORTED_VERSION);
    info = valid_info();
    info.struct_size = 1u;
    assert(dakos_boot_info_validate(&info, valid_regions, 3u) ==
           DAK_BOOT_INFO_UNSUPPORTED_VERSION);
}


static void test_v1_prefix_accepts_appended_compatible_extension(void) {
    dakos_boot_info_v1_extended extended;
    uint8_t expected_extension[sizeof(extended.extension)];

    memset(&extended, 0xa5, sizeof(extended));
    memset(expected_extension, 0xa5, sizeof(expected_extension));
    extended.v1 = valid_info();
    extended.v1.struct_size = (uint32_t)sizeof(extended);

    assert(dakos_boot_info_validate(
        &extended.v1, valid_regions,
        sizeof(valid_regions) / sizeof(valid_regions[0])
    ) == DAK_BOOT_INFO_OK);
    assert(memcmp(extended.extension, expected_extension,
                  sizeof(expected_extension)) == 0);
}

int main(void) {
    test_valid_handoff();
    test_initramfs_is_optional_but_must_be_consistent();
    test_kernel_and_initramfs_ranges_are_checked();
    test_reserved_and_mmio_ownership();
    test_framebuffer_contract();
    test_memory_map_order_overlap_and_count();
    test_version_and_arguments_fail_closed();
    test_v1_prefix_accepts_appended_compatible_extension();
    return 0;
}
