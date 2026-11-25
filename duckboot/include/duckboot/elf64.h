#ifndef DUCKBOOT_ELF64_H
#define DUCKBOOT_ELF64_H

#include <stddef.h>
#include <stdint.h>

#define DUCKBOOT_ELF64_MAX_SEGMENTS 32u
#define DUCKBOOT_ELF64_PAGE_SIZE 4096u
#define DUCKBOOT_ELF64_PF_X 0x1u
#define DUCKBOOT_ELF64_PF_W 0x2u
#define DUCKBOOT_ELF64_PF_R 0x4u

typedef enum duckboot_elf_status {
    DUCKBOOT_ELF_OK = 0,
    DUCKBOOT_ELF_INVALID_ARGUMENT = -1,
    DUCKBOOT_ELF_TRUNCATED = -2,
    DUCKBOOT_ELF_BAD_MAGIC = -3,
    DUCKBOOT_ELF_UNSUPPORTED_CLASS = -4,
    DUCKBOOT_ELF_UNSUPPORTED_ENDIANNESS = -5,
    DUCKBOOT_ELF_UNSUPPORTED_MACHINE = -6,
    DUCKBOOT_ELF_UNSUPPORTED_TYPE = -7,
    DUCKBOOT_ELF_INVALID_HEADER = -8,
    DUCKBOOT_ELF_INVALID_PROGRAM_TABLE = -9,
    DUCKBOOT_ELF_INVALID_SEGMENT = -10,
    DUCKBOOT_ELF_TOO_MANY_SEGMENTS = -11,
    DUCKBOOT_ELF_OVERLAPPING_SEGMENTS = -12,
    DUCKBOOT_ELF_INVALID_ENTRY = -13,
    DUCKBOOT_ELF_WRITABLE_EXECUTABLE = -14
} duckboot_elf_status;

typedef struct duckboot_elf_segment {
    uint64_t file_offset;
    uint64_t virtual_address;
    uint64_t physical_address;
    uint64_t file_size;
    uint64_t memory_size;
    uint64_t alignment;
    uint32_t flags;
} duckboot_elf_segment;

typedef struct duckboot_elf_image {
    uint64_t entry;
    uint64_t physical_base;
    uint64_t physical_end;
    size_t segment_count;
    duckboot_elf_segment segments[DUCKBOOT_ELF64_MAX_SEGMENTS];
} duckboot_elf_image;

duckboot_elf_status duckboot_elf64_inspect(
    const void *file_data,
    size_t file_size,
    duckboot_elf_image *image
);

const char *duckboot_elf_status_name(duckboot_elf_status status);

#endif
