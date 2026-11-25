#include "duckboot/elf64.h"

#include <stdbool.h>
#include <stdint.h>

#define ELF_HEADER_SIZE 64u
#define ELF_PROGRAM_HEADER_SIZE 56u
#define ELF_CLASS_64 2u
#define ELF_DATA_LSB 1u
#define ELF_VERSION_CURRENT 1u
#define ELF_ET_EXEC 2u
#define ELF_EM_X86_64 62u
#define ELF_PT_LOAD 1u

#pragma pack(push, 1)
typedef struct elf64_header {
    uint8_t ident[16];
    uint16_t type;
    uint16_t machine;
    uint32_t version;
    uint64_t entry;
    uint64_t program_offset;
    uint64_t section_offset;
    uint32_t flags;
    uint16_t header_size;
    uint16_t program_entry_size;
    uint16_t program_count;
    uint16_t section_entry_size;
    uint16_t section_count;
    uint16_t section_names_index;
} elf64_header;

typedef struct elf64_program_header {
    uint32_t type;
    uint32_t flags;
    uint64_t offset;
    uint64_t virtual_address;
    uint64_t physical_address;
    uint64_t file_size;
    uint64_t memory_size;
    uint64_t alignment;
} elf64_program_header;
#pragma pack(pop)

static void copy_bytes(void *destination, const uint8_t *source, size_t count) {
    uint8_t *out = (uint8_t *)destination;
    for (size_t index = 0u; index < count; ++index) out[index] = source[index];
}

static bool add_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (result == NULL || left > UINT64_MAX - right) return false;
    *result = left + right;
    return true;
}

static bool multiply_u64(uint64_t left, uint64_t right, uint64_t *result) {
    if (result == NULL || (right != 0u && left > UINT64_MAX / right)) return false;
    *result = left * right;
    return true;
}

static bool power_of_two_u64(uint64_t value) {
    return value != 0u && (value & (value - 1u)) == 0u;
}

static bool canonical_x86_64(uint64_t address) {
    const uint64_t upper = address >> 48u;
    const bool sign = ((address >> 47u) & 1u) != 0u;
    return sign ? upper == 0xffffu : upper == 0u;
}

static bool canonical_range(uint64_t begin, uint64_t end) {
    if (end <= begin || !canonical_x86_64(begin) ||
        !canonical_x86_64(end - 1u)) {
        return false;
    }
    return ((begin >> 47u) & 1u) == (((end - 1u) >> 47u) & 1u);
}

static bool ranges_overlap(
    uint64_t first_base, uint64_t first_end,
    uint64_t second_base, uint64_t second_end
) {
    return first_base < second_end && second_base < first_end;
}

static bool align_range(
    uint64_t base,
    uint64_t length,
    uint64_t *aligned_base,
    uint64_t *aligned_end
) {
    uint64_t end;
    if (!add_u64(base, length, &end)) return false;
    *aligned_base = base & ~(uint64_t)(DUCKBOOT_ELF64_PAGE_SIZE - 1u);
    if (end > UINT64_MAX - (DUCKBOOT_ELF64_PAGE_SIZE - 1u)) return false;
    *aligned_end = (end + DUCKBOOT_ELF64_PAGE_SIZE - 1u) &
        ~(uint64_t)(DUCKBOOT_ELF64_PAGE_SIZE - 1u);
    return *aligned_end > *aligned_base;
}

duckboot_elf_status duckboot_elf64_inspect(
    const void *file_data,
    size_t file_size,
    duckboot_elf_image *image
) {
    const uint8_t *bytes = (const uint8_t *)file_data;
    elf64_header header;
    duckboot_elf_image parsed = {0};
    uint64_t program_table_size;
    uint64_t program_table_end;
    uint64_t physical_base = UINT64_MAX;
    uint64_t physical_end = 0u;
    bool entry_is_executable = false;

    if (file_data == NULL || image == NULL) return DUCKBOOT_ELF_INVALID_ARGUMENT;
    if (file_size < ELF_HEADER_SIZE) return DUCKBOOT_ELF_TRUNCATED;

    copy_bytes(&header, bytes, sizeof(header));
    if (header.ident[0] != 0x7fu || header.ident[1] != 'E' ||
        header.ident[2] != 'L' || header.ident[3] != 'F') {
        return DUCKBOOT_ELF_BAD_MAGIC;
    }
    if (header.ident[4] != ELF_CLASS_64) return DUCKBOOT_ELF_UNSUPPORTED_CLASS;
    if (header.ident[5] != ELF_DATA_LSB || header.ident[6] != ELF_VERSION_CURRENT) {
        return DUCKBOOT_ELF_UNSUPPORTED_ENDIANNESS;
    }
    if (header.machine != ELF_EM_X86_64) return DUCKBOOT_ELF_UNSUPPORTED_MACHINE;
    if (header.type != ELF_ET_EXEC) return DUCKBOOT_ELF_UNSUPPORTED_TYPE;
    if (header.version != ELF_VERSION_CURRENT || header.header_size < ELF_HEADER_SIZE ||
        header.header_size > file_size ||
        header.program_entry_size < ELF_PROGRAM_HEADER_SIZE ||
        header.program_count == 0u) {
        return DUCKBOOT_ELF_INVALID_HEADER;
    }
    if (!multiply_u64(header.program_entry_size, header.program_count,
                      &program_table_size) ||
        !add_u64(header.program_offset, program_table_size, &program_table_end) ||
        program_table_end > (uint64_t)file_size) {
        return DUCKBOOT_ELF_INVALID_PROGRAM_TABLE;
    }
    if (!canonical_x86_64(header.entry)) return DUCKBOOT_ELF_INVALID_ENTRY;

    parsed.entry = header.entry;

    for (uint16_t index = 0u; index < header.program_count; ++index) {
        elf64_program_header program;
        const uint64_t offset = header.program_offset +
            (uint64_t)index * header.program_entry_size;
        uint64_t file_end;
        uint64_t virtual_end;
        uint64_t physical_segment_end;
        uint64_t virtual_page_base;
        uint64_t virtual_page_end;
        uint64_t physical_page_base;
        uint64_t physical_page_end;

        copy_bytes(&program, bytes + (size_t)offset, sizeof(program));
        if (program.type != ELF_PT_LOAD) continue;
        if (parsed.segment_count >= DUCKBOOT_ELF64_MAX_SEGMENTS) {
            return DUCKBOOT_ELF_TOO_MANY_SEGMENTS;
        }
        if (program.memory_size == 0u || program.file_size > program.memory_size ||
            (program.flags & DUCKBOOT_ELF64_PF_R) == 0u ||
            ((program.flags & (DUCKBOOT_ELF64_PF_W | DUCKBOOT_ELF64_PF_X)) ==
                (DUCKBOOT_ELF64_PF_W | DUCKBOOT_ELF64_PF_X))) {
            return (program.flags & (DUCKBOOT_ELF64_PF_W | DUCKBOOT_ELF64_PF_X)) ==
                (DUCKBOOT_ELF64_PF_W | DUCKBOOT_ELF64_PF_X) ?
                DUCKBOOT_ELF_WRITABLE_EXECUTABLE : DUCKBOOT_ELF_INVALID_SEGMENT;
        }
        if (!add_u64(program.offset, program.file_size, &file_end) ||
            file_end > (uint64_t)file_size ||
            !add_u64(program.virtual_address, program.memory_size, &virtual_end) ||
            !add_u64(program.physical_address, program.memory_size, &physical_segment_end) ||
            !canonical_range(program.virtual_address, virtual_end) ||
            program.physical_address == 0u) {
            return DUCKBOOT_ELF_INVALID_SEGMENT;
        }
        if (program.alignment > 1u) {
            if (!power_of_two_u64(program.alignment) ||
                (program.virtual_address % program.alignment) !=
                    (program.offset % program.alignment) ||
                (program.physical_address % program.alignment) !=
                    (program.offset % program.alignment)) {
                return DUCKBOOT_ELF_INVALID_SEGMENT;
            }
        }
        if ((program.virtual_address & (DUCKBOOT_ELF64_PAGE_SIZE - 1u)) !=
            (program.physical_address & (DUCKBOOT_ELF64_PAGE_SIZE - 1u))) {
            return DUCKBOOT_ELF_INVALID_SEGMENT;
        }
        if (!align_range(program.virtual_address, program.memory_size,
                         &virtual_page_base, &virtual_page_end) ||
            !align_range(program.physical_address, program.memory_size,
                         &physical_page_base, &physical_page_end)) {
            return DUCKBOOT_ELF_INVALID_SEGMENT;
        }

        for (size_t prior = 0u; prior < parsed.segment_count; ++prior) {
            const duckboot_elf_segment *existing = &parsed.segments[prior];
            uint64_t existing_virtual_base;
            uint64_t existing_virtual_end;
            uint64_t existing_physical_base;
            uint64_t existing_physical_end;
            if (!align_range(existing->virtual_address, existing->memory_size,
                             &existing_virtual_base, &existing_virtual_end) ||
                !align_range(existing->physical_address, existing->memory_size,
                             &existing_physical_base, &existing_physical_end)) {
                return DUCKBOOT_ELF_INVALID_SEGMENT;
            }
            if (ranges_overlap(virtual_page_base, virtual_page_end,
                               existing_virtual_base, existing_virtual_end) ||
                ranges_overlap(physical_page_base, physical_page_end,
                               existing_physical_base, existing_physical_end)) {
                return DUCKBOOT_ELF_OVERLAPPING_SEGMENTS;
            }
        }

        duckboot_elf_segment *segment = &parsed.segments[parsed.segment_count++];
        segment->file_offset = program.offset;
        segment->virtual_address = program.virtual_address;
        segment->physical_address = program.physical_address;
        segment->file_size = program.file_size;
        segment->memory_size = program.memory_size;
        segment->alignment = program.alignment;
        segment->flags = program.flags;

        if (program.physical_address < physical_base) physical_base = program.physical_address;
        if (physical_segment_end > physical_end) physical_end = physical_segment_end;
        if ((program.flags & DUCKBOOT_ELF64_PF_X) != 0u &&
            header.entry >= program.virtual_address && header.entry < virtual_end) {
            entry_is_executable = true;
        }
    }

    if (parsed.segment_count == 0u || !entry_is_executable ||
        physical_base == UINT64_MAX || physical_end <= physical_base) {
        return DUCKBOOT_ELF_INVALID_ENTRY;
    }

    parsed.physical_base = physical_base;
    parsed.physical_end = physical_end;
    *image = parsed;
    return DUCKBOOT_ELF_OK;
}

const char *duckboot_elf_status_name(duckboot_elf_status status) {
    switch (status) {
        case DUCKBOOT_ELF_OK: return "ok";
        case DUCKBOOT_ELF_INVALID_ARGUMENT: return "invalid-argument";
        case DUCKBOOT_ELF_TRUNCATED: return "truncated";
        case DUCKBOOT_ELF_BAD_MAGIC: return "bad-magic";
        case DUCKBOOT_ELF_UNSUPPORTED_CLASS: return "unsupported-class";
        case DUCKBOOT_ELF_UNSUPPORTED_ENDIANNESS: return "unsupported-endianness";
        case DUCKBOOT_ELF_UNSUPPORTED_MACHINE: return "unsupported-machine";
        case DUCKBOOT_ELF_UNSUPPORTED_TYPE: return "unsupported-type";
        case DUCKBOOT_ELF_INVALID_HEADER: return "invalid-header";
        case DUCKBOOT_ELF_INVALID_PROGRAM_TABLE: return "invalid-program-table";
        case DUCKBOOT_ELF_INVALID_SEGMENT: return "invalid-segment";
        case DUCKBOOT_ELF_TOO_MANY_SEGMENTS: return "too-many-segments";
        case DUCKBOOT_ELF_OVERLAPPING_SEGMENTS: return "overlapping-segments";
        case DUCKBOOT_ELF_INVALID_ENTRY: return "invalid-entry";
        case DUCKBOOT_ELF_WRITABLE_EXECUTABLE: return "writable-executable";
        default: return "unknown";
    }
}
