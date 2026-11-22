#include "initramfs.h"

#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

static uint8_t archive[4096];
static uint64_t used;

static void write_hex32(uint8_t *destination, uint32_t value)
{
    static const char digits[] = "0123456789abcdef";

    for (int shift = 28; shift >= 0; shift -= 4) {
        *destination++ = (uint8_t)digits[(value >> shift) & 0x0f];
    }
}

static void align_archive(void)
{
    while ((used & 3u) != 0) {
        archive[used++] = 0;
    }
}

static bool append_entry(const uint8_t *name, uint32_t name_size,
                         uint32_t mode, const uint8_t *data,
                         uint32_t data_size)
{
    const uint32_t fields[13] = {
        1, mode, 0, 0, 1, 0, data_size,
        0, 0, 0, 0, name_size, 0
    };

    if (used + 110 + name_size + data_size + 8 > sizeof(archive)) {
        return false;
    }

    memcpy(archive + used, "070701", 6);
    used += 6;

    for (size_t i = 0; i < 13; ++i) {
        write_hex32(archive + used, fields[i]);
        used += 8;
    }

    memcpy(archive + used, name, name_size);
    used += name_size;
    align_archive();

    if (data_size != 0) {
        memcpy(archive + used, data, data_size);
        used += data_size;
    }
    align_archive();

    return true;
}

static bool finish_archive(void)
{
    static const uint8_t trailer[] = "TRAILER!!!";
    return append_entry(trailer, sizeof(trailer), 0, NULL, 0);
}

static bool validate_one(const uint8_t *name, uint32_t name_size,
                         uint32_t mode, bool expected)
{
    static const uint8_t payload[] = "ok";
    uint64_t entries = 0;
    used = 0;

    if (!append_entry(name, name_size, mode, payload, sizeof(payload) - 1) ||
        !finish_archive()) {
        return false;
    }

    const bool actual = initramfs_validate(archive, used, &entries);
    return actual == expected && (!actual || entries == 1);
}

int main(void)
{
    static const uint8_t regular_name[] = "init";
    static const uint8_t traversal_name[] = "../escape";
    static const uint8_t absolute_name[] = "/etc/passwd";
    static const uint8_t repeated_slash_name[] = "etc//passwd";
    static const uint8_t embedded_nul_name[] = {'i', 'n', 0, 'i', 't', 0};

    if (!validate_one(regular_name, sizeof(regular_name), 0100755u, true)) {
        fputs("valid regular-file archive was rejected\n", stderr);
        return 1;
    }

    if (!validate_one(traversal_name, sizeof(traversal_name), 0100644u, false)) {
        fputs("path traversal was accepted\n", stderr);
        return 1;
    }

    if (!validate_one(absolute_name, sizeof(absolute_name), 0100644u, false)) {
        fputs("absolute archive path was accepted\n", stderr);
        return 1;
    }

    if (!validate_one(repeated_slash_name, sizeof(repeated_slash_name), 0100644u, false)) {
        fputs("empty path component was accepted\n", stderr);
        return 1;
    }

    if (!validate_one(embedded_nul_name, sizeof(embedded_nul_name), 0100644u, false)) {
        fputs("embedded NUL in archive path was accepted\n", stderr);
        return 1;
    }

    if (!validate_one(regular_name, sizeof(regular_name), 0020600u, false)) {
        fputs("character/block device entry was accepted\n", stderr);
        return 1;
    }

    used = 0;
    if (!append_entry(regular_name, sizeof(regular_name), 0100644u, NULL, 0)) {
        fputs("could not construct truncated-archive fixture\n", stderr);
        return 1;
    }

    uint64_t entries = 0;
    if (initramfs_validate(archive, used, &entries)) {
        fputs("archive without trailer was accepted\n", stderr);
        return 1;
    }

    puts("initramfs validator: all tests passed");
    return 0;
}
