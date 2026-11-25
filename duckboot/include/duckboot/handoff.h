#ifndef DUCKBOOT_HANDOFF_H
#define DUCKBOOT_HANDOFF_H

#include <stdint.h>
#include "boot_info.h"

#define DUCKBOOT_HANDOFF_MAGIC UINT64_C(0x31464f484b434444)
#define DUCKBOOT_HANDOFF_VERSION 1u

typedef struct duckboot_handoff_v1 {
    uint64_t magic;
    uint32_t struct_size;
    uint32_t version;
    uint64_t boot_info_virtual;
    uint64_t memory_map_virtual;
    uint64_t hhdm_offset;
    uint64_t framebuffer_virtual;
    uint64_t command_line_virtual;
    uint32_t red_mask_size;
    uint32_t red_mask_shift;
    uint32_t green_mask_size;
    uint32_t green_mask_shift;
    uint32_t blue_mask_size;
    uint32_t blue_mask_shift;
    uint32_t reserved[4];
} duckboot_handoff_v1;

#endif
