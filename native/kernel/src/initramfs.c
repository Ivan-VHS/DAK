#include "initramfs.h"

static bool has_magic(const uint8_t *header)
{
    static const char magic[] = "070701";

    for (uint64_t i = 0; i < sizeof(magic) - 1; ++i) {
        if (header[i] != (uint8_t)magic[i]) {
            return false;
        }
    }

    return true;
}

static bool parse_hex32(const uint8_t *text, uint64_t *value)
{
    uint64_t result = 0;

    for (uint64_t i = 0; i < 8; ++i) {
        const uint8_t ch = text[i];
        uint64_t digit;

        if (ch >= '0' && ch <= '9') {
            digit = ch - '0';
        } else if (ch >= 'a' && ch <= 'f') {
            digit = ch - 'a' + 10;
        } else if (ch >= 'A' && ch <= 'F') {
            digit = ch - 'A' + 10;
        } else {
            return false;
        }

        result = (result << 4) | digit;
    }

    *value = result;
    return true;
}


static bool safe_archive_name(const uint8_t *name, uint64_t name_size)
{
    if (name_size < 2 || name[0] == '/' || name[name_size - 1] != 0) {
        return false;
    }

    uint64_t component_start = 0;

    for (uint64_t i = 0; i < name_size; ++i) {
        const bool at_end = i == name_size - 1;
        const uint8_t ch = name[i];

        if (ch == '\\') {
            return false;
        }

        if (ch != '/' && !at_end) {
            continue;
        }

        const uint64_t component_length = i - component_start;
        if (component_length == 0 ||
            (component_length == 1 && name[component_start] == '.') ||
            (component_length == 2 && name[component_start] == '.' &&
             name[component_start + 1] == '.')) {
            return false;
        }

        component_start = i + 1;
    }

    return true;
}

static bool align4(uint64_t value, uint64_t *aligned)
{
    if (value > UINT64_MAX - 3) {
        return false;
    }

    *aligned = (value + 3) & ~3ull;
    return true;
}

static bool is_trailer(const uint8_t *name, uint64_t name_size)
{
    static const char trailer[] = "TRAILER!!!";

    if (name_size != sizeof(trailer)) {
        return false;
    }

    for (uint64_t i = 0; i < sizeof(trailer) - 1; ++i) {
        if (name[i] != (uint8_t)trailer[i]) {
            return false;
        }
    }

    return name[sizeof(trailer) - 1] == 0;
}

bool initramfs_validate(const void *archive, uint64_t archive_size,
                        uint64_t *entry_count)
{
    if (archive == 0 || entry_count == 0) {
        return false;
    }

    const uint8_t *bytes = archive;
    uint64_t offset = 0;
    uint64_t entries = 0;

    while (offset <= archive_size && archive_size - offset >= 110) {
        const uint8_t *header = bytes + offset;
        uint64_t file_size;
        uint64_t name_size;
        uint64_t mode;

        if (!has_magic(header) ||
            !parse_hex32(header + 14, &mode) ||
            !parse_hex32(header + 54, &file_size) ||
            !parse_hex32(header + 94, &name_size) ||
            name_size == 0 || name_size > 4096) {
            return false;
        }

        const uint64_t name_offset = offset + 110;
        if (name_size > archive_size - name_offset) {
            return false;
        }

        const uint8_t *name = bytes + name_offset;
        if (name[name_size - 1] != 0) {
            return false;
        }

        uint64_t data_offset;
        if (!align4(name_offset + name_size, &data_offset) ||
            data_offset > archive_size ||
            file_size > archive_size - data_offset) {
            return false;
        }

        const bool trailer = is_trailer(name, name_size);
        if (trailer) {
            if (file_size != 0) {
                return false;
            }

            *entry_count = entries;
            return true;
        }

        const uint64_t file_type = mode & 0170000u;
        if (!safe_archive_name(name, name_size) ||
            (file_type != 0100000u && file_type != 0040000u &&
             file_type != 0120000u)) {
            return false;
        }

        if (entries == UINT64_MAX) {
            return false;
        }
        ++entries;

        if (!align4(data_offset + file_size, &offset)) {
            return false;
        }
    }

    return false;
}
