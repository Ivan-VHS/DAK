#include "duckboot/arena.h"
#include "duckboot/config.h"
#include "duckboot/elf64.h"

#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define CHECK(condition) do { \
    if (!(condition)) { \
        fprintf(stderr, "check failed at %s:%d: %s\n", __FILE__, __LINE__, #condition); \
        exit(1); \
    } \
} while (0)

#pragma pack(push, 1)
typedef struct test_elf_header {
    uint8_t ident[16];
    uint16_t type, machine;
    uint32_t version;
    uint64_t entry, phoff, shoff;
    uint32_t flags;
    uint16_t ehsize, phentsize, phnum, shentsize, shnum, shstrndx;
} test_elf_header;

typedef struct test_program_header {
    uint32_t type, flags;
    uint64_t offset, vaddr, paddr, filesz, memsz, align;
} test_program_header;
#pragma pack(pop)

static void make_elf(uint8_t *file, size_t size) {
    test_elf_header header;
    test_program_header program;
    memset(file, 0, size);
    memset(&header, 0, sizeof(header));
    header.ident[0] = 0x7f;
    header.ident[1] = 'E';
    header.ident[2] = 'L';
    header.ident[3] = 'F';
    header.ident[4] = 2;
    header.ident[5] = 1;
    header.ident[6] = 1;
    header.type = 2;
    header.machine = 62;
    header.version = 1;
    header.entry = UINT64_C(0xffffffff80000000);
    header.phoff = sizeof(header);
    header.ehsize = sizeof(header);
    header.phentsize = sizeof(program);
    header.phnum = 1;
    memcpy(file, &header, sizeof(header));

    memset(&program, 0, sizeof(program));
    program.type = 1;
    program.flags = DUCKBOOT_ELF64_PF_R | DUCKBOOT_ELF64_PF_X;
    program.offset = 0x1000;
    program.vaddr = UINT64_C(0xffffffff80000000);
    program.paddr = 0x200000;
    program.filesz = 16;
    program.memsz = 4096;
    program.align = 0x1000;
    memcpy(file + sizeof(header), &program, sizeof(program));
}

static void test_arena(void) {
    uint8_t storage[128];
    duckboot_arena arena;
    CHECK(duckboot_arena_init(&arena, storage, sizeof(storage)) == DUCKBOOT_ARENA_OK);
    void *first = duckboot_arena_allocate(&arena, 3u, 1u);
    size_t checkpoint = duckboot_arena_checkpoint(&arena);
    void *aligned = duckboot_arena_allocate(&arena, 16u, 16u);
    CHECK(first == storage);
    CHECK(((uintptr_t)aligned & 15u) == 0u);
    CHECK(duckboot_arena_allocate(&arena, 8u, 3u) == NULL);
    CHECK(duckboot_arena_rewind(&arena, checkpoint, true) == DUCKBOOT_ARENA_OK);
    CHECK(arena.used == checkpoint);
    CHECK(duckboot_arena_rewind(&arena, checkpoint + 1u, false) ==
          DUCKBOOT_ARENA_INVALID_CHECKPOINT);
    CHECK(duckboot_arena_allocate(&arena, 200u, 8u) == NULL);
    duckboot_arena_reset(&arena, true);
    CHECK(arena.used == 0u);
}

static void test_elf(void) {
    uint8_t file[8192];
    duckboot_elf_image image;
    make_elf(file, sizeof(file));
    CHECK(duckboot_elf64_inspect(file, sizeof(file), &image) == DUCKBOOT_ELF_OK);
    CHECK(image.entry == UINT64_C(0xffffffff80000000));
    CHECK(image.physical_base == 0x200000u);
    CHECK(image.physical_end == 0x201000u);
    CHECK(image.segment_count == 1u);

    file[0] = 0u;
    CHECK(duckboot_elf64_inspect(file, sizeof(file), &image) == DUCKBOOT_ELF_BAD_MAGIC);
    make_elf(file, sizeof(file));
    CHECK(duckboot_elf64_inspect(file, 32u, &image) == DUCKBOOT_ELF_TRUNCATED);

    make_elf(file, sizeof(file));
    test_program_header bad;
    memcpy(&bad, file + sizeof(test_elf_header), sizeof(bad));
    bad.offset = UINT64_MAX - 8u;
    bad.filesz = 64u;
    memcpy(file + sizeof(test_elf_header), &bad, sizeof(bad));
    CHECK(duckboot_elf64_inspect(file, sizeof(file), &image) == DUCKBOOT_ELF_INVALID_SEGMENT);

    make_elf(file, sizeof(file));
    memcpy(&bad, file + sizeof(test_elf_header), sizeof(bad));
    bad.flags |= DUCKBOOT_ELF64_PF_W;
    memcpy(file + sizeof(test_elf_header), &bad, sizeof(bad));
    CHECK(duckboot_elf64_inspect(file, sizeof(file), &image) ==
          DUCKBOOT_ELF_WRITABLE_EXECUTABLE);

    make_elf(file, sizeof(file));
    test_elf_header header;
    memcpy(&header, file, sizeof(header));
    header.phnum = 2u;
    memcpy(file, &header, sizeof(header));
    memcpy(&bad, file + sizeof(test_elf_header), sizeof(bad));
    test_program_header overlap = bad;
    overlap.vaddr += 0x2000u;
    overlap.offset = 0x2000u;
    overlap.filesz = 0u;
    memcpy(file + sizeof(test_elf_header) + sizeof(test_program_header),
           &overlap, sizeof(overlap));
    CHECK(duckboot_elf64_inspect(file, sizeof(file), &image) ==
          DUCKBOOT_ELF_OVERLAPPING_SEGMENTS);

    make_elf(file, sizeof(file));
    memcpy(&header, file, sizeof(header));
    header.phnum = 33u;
    memcpy(file, &header, sizeof(header));
    for (uint16_t index = 1u; index < 33u; ++index) {
        test_program_header extra;
        memset(&extra, 0, sizeof(extra));
        extra.type = 1u;
        extra.flags = DUCKBOOT_ELF64_PF_R;
        extra.vaddr = UINT64_C(0xffffffff80000000) + (uint64_t)index * 0x1000u;
        extra.paddr = 0x200000u + (uint64_t)index * 0x1000u;
        extra.memsz = 0x1000u;
        extra.align = 0x1000u;
        memcpy(file + sizeof(test_elf_header) + (size_t)index * sizeof(test_program_header),
               &extra, sizeof(extra));
    }
    CHECK(duckboot_elf64_inspect(file, sizeof(file), &image) ==
          DUCKBOOT_ELF_TOO_MANY_SEGMENTS);
}

static void test_config(void) {
    const char valid[] =
        "# DuckBoot configuration\r\n"
        "timeout=5\n"
        "label=duckos-main\n"
        "kernel=\\boot\\duckos.elf\n"
        "cmdline=quiet serial=on\n";
    duckboot_config config;
    CHECK(duckboot_config_parse(valid, sizeof(valid) - 1u, &config) == DUCKBOOT_CONFIG_OK);
    CHECK(config.timeout_seconds == 5u);
    CHECK(strcmp(config.label, "duckos-main") == 0);
    CHECK(strcmp(config.kernel_path, "\\boot\\duckos.elf") == 0);
    CHECK(strcmp(config.command_line, "quiet serial=on") == 0);

    const char traversal[] = "kernel=\\boot\\..\\evil.elf\n";
    CHECK(duckboot_config_parse(traversal, sizeof(traversal) - 1u, &config) ==
          DUCKBOOT_CONFIG_INVALID_VALUE);
    const char duplicate[] = "kernel=\\boot\\a.elf\nkernel=\\boot\\b.elf\n";
    CHECK(duckboot_config_parse(duplicate, sizeof(duplicate) - 1u, &config) ==
          DUCKBOOT_CONFIG_DUPLICATE_KEY);
    const char unknown[] = "kernel=\\boot\\a.elf\nscript=run\n";
    CHECK(duckboot_config_parse(unknown, sizeof(unknown) - 1u, &config) ==
          DUCKBOOT_CONFIG_UNKNOWN_KEY);
    const char excessive_timeout[] = "timeout=31\nkernel=\\boot\\a.elf\n";
    CHECK(duckboot_config_parse(excessive_timeout, sizeof(excessive_timeout) - 1u, &config) ==
          DUCKBOOT_CONFIG_INVALID_VALUE);
    const char default_timeout[] = "kernel=\\boot\\a.elf\n";
    CHECK(duckboot_config_parse(default_timeout, sizeof(default_timeout) - 1u, &config) ==
          DUCKBOOT_CONFIG_OK);
    CHECK(config.timeout_seconds == 5u);
}

int main(void) {
    test_arena();
    test_elf();
    test_config();
    puts("DuckBoot core tests: PASS");
    return 0;
}
