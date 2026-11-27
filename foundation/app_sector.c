#include "app_sector.h"

static void dak_bytes_clear(void *destination, size_t length) {
    uint8_t *bytes = (uint8_t *)destination;
    for (size_t index = 0u; index < length; ++index) bytes[index] = 0u;
}

static void dak_bytes_copy(void *destination, const void *source, size_t length) {
    uint8_t *output = (uint8_t *)destination;
    const uint8_t *input = (const uint8_t *)source;
    for (size_t index = 0u; index < length; ++index) output[index] = input[index];
}

static uint16_t read_u16_le(const uint8_t *bytes) {
    return (uint16_t)((uint16_t)bytes[0] | ((uint16_t)bytes[1] << 8u));
}

static uint32_t read_u32_le(const uint8_t *bytes) {
    return (uint32_t)bytes[0] |
        ((uint32_t)bytes[1] << 8u) |
        ((uint32_t)bytes[2] << 16u) |
        ((uint32_t)bytes[3] << 24u);
}

static uint64_t read_u64_le(const uint8_t *bytes) {
    return (uint64_t)read_u32_le(bytes) |
        ((uint64_t)read_u32_le(bytes + 4u) << 32u);
}

static void write_u16_le(uint8_t *bytes, uint16_t value) {
    bytes[0] = (uint8_t)value;
    bytes[1] = (uint8_t)(value >> 8u);
}

static void write_u32_le(uint8_t *bytes, uint32_t value) {
    bytes[0] = (uint8_t)value;
    bytes[1] = (uint8_t)(value >> 8u);
    bytes[2] = (uint8_t)(value >> 16u);
    bytes[3] = (uint8_t)(value >> 24u);
}

static void write_u64_le(uint8_t *bytes, uint64_t value) {
    write_u32_le(bytes, (uint32_t)value);
    write_u32_le(bytes + 4u, (uint32_t)(value >> 32u));
}

static bool bytes_nonzero(const uint8_t *bytes, size_t length) {
    uint8_t combined = 0u;
    for (size_t index = 0u; index < length; ++index) combined |= bytes[index];
    return combined != 0u;
}

static bool power_of_two(uint32_t value) {
    return value != 0u && (value & (value - 1u)) == 0u;
}

static dak_sector_status permission_model_valid(const dak_app_sector_v1 *sector) {
    const uint32_t permissions = sector->permissions;
    const bool read = (permissions & DAK_SECTOR_PERMISSION_READ) != 0u;
    const bool write = (permissions & DAK_SECTOR_PERMISSION_WRITE) != 0u;
    const bool execute = (permissions & DAK_SECTOR_PERMISSION_EXECUTE) != 0u;

    if ((permissions & ~DAK_SECTOR_PERMISSIONS_KNOWN) != 0u || !read || (write && execute)) {
        return DAK_SECTOR_BAD_PERMISSION_MODEL;
    }

    switch ((dak_sector_kind)sector->kind) {
        case DAK_SECTOR_MANIFEST:
        case DAK_SECTOR_READ_ONLY_DATA:
        case DAK_SECTOR_RESOURCE:
        case DAK_SECTOR_POLICY:
            return (!write && !execute) ? DAK_SECTOR_OK : DAK_SECTOR_BAD_PERMISSION_MODEL;
        case DAK_SECTOR_CODE:
            return (!write && execute) ? DAK_SECTOR_OK : DAK_SECTOR_BAD_PERMISSION_MODEL;
        case DAK_SECTOR_WRITABLE_DATA:
        case DAK_SECTOR_JOURNAL:
            return (write && !execute) ? DAK_SECTOR_OK : DAK_SECTOR_BAD_PERMISSION_MODEL;
        default:
            return DAK_SECTOR_INVALID_DESCRIPTOR;
    }
}

dak_sector_status dak_sector_encode(
    const dak_app_sector_v1 *sector,
    uint8_t output[DAK_SECTOR_WIRE_BYTES]
) {
    if (sector == NULL || output == NULL) return DAK_SECTOR_INVALID_ARGUMENT;
    if (sector->app_id == 0u || sector->sector_id == 0u || sector->generation == 0u ||
        sector->kind < (uint16_t)DAK_SECTOR_MANIFEST ||
        sector->kind > (uint16_t)DAK_SECTOR_JOURNAL ||
        (sector->flags & ~DAK_SECTOR_FLAG_KNOWN) != 0u ||
        (sector->flags & (DAK_SECTOR_FLAG_VERIFIED | DAK_SECTOR_FLAG_SEALED)) !=
            (DAK_SECTOR_FLAG_VERIFIED | DAK_SECTOR_FLAG_SEALED) ||
        sector->length_bytes == 0u || !power_of_two(sector->alignment_bytes) ||
        sector->alignment_bytes > DAK_SECTOR_MAX_ALIGNMENT ||
        sector->offset_bytes % sector->alignment_bytes != 0u ||
        !bytes_nonzero(sector->digest, sizeof(sector->digest)) ||
        permission_model_valid(sector) != DAK_SECTOR_OK) {
        return DAK_SECTOR_INVALID_DESCRIPTOR;
    }

    dak_bytes_clear(output, DAK_SECTOR_WIRE_BYTES);
    output[0] = DAK_SECTOR_MAGIC_0;
    output[1] = DAK_SECTOR_MAGIC_1;
    output[2] = DAK_SECTOR_MAGIC_2;
    output[3] = DAK_SECTOR_MAGIC_3;
    write_u16_le(output + 4u, DAK_SECTOR_WIRE_VERSION);
    write_u16_le(output + 6u, DAK_SECTOR_WIRE_BYTES);
    write_u64_le(output + 8u, sector->app_id);
    write_u32_le(output + 16u, sector->sector_id);
    write_u16_le(output + 20u, sector->kind);
    write_u16_le(output + 22u, sector->flags);
    write_u64_le(output + 24u, sector->offset_bytes);
    write_u64_le(output + 32u, sector->length_bytes);
    write_u32_le(output + 40u, sector->alignment_bytes);
    write_u32_le(output + 44u, sector->permissions);
    dak_bytes_copy(output + 48u, sector->digest, DAK_SECTOR_DIGEST_BYTES);
    write_u64_le(output + 80u, sector->generation);
    /* Bytes 88..95 are reserved and must remain zero in v1. */
    return DAK_SECTOR_OK;
}

dak_sector_status dak_sector_decode(
    const uint8_t input[DAK_SECTOR_WIRE_BYTES],
    dak_app_sector_v1 *sector
) {
    if (input == NULL || sector == NULL) return DAK_SECTOR_INVALID_ARGUMENT;
    if (input[0] != DAK_SECTOR_MAGIC_0 || input[1] != DAK_SECTOR_MAGIC_1 ||
        input[2] != DAK_SECTOR_MAGIC_2 || input[3] != DAK_SECTOR_MAGIC_3 ||
        read_u16_le(input + 4u) != DAK_SECTOR_WIRE_VERSION ||
        read_u16_le(input + 6u) != DAK_SECTOR_WIRE_BYTES) {
        return DAK_SECTOR_BAD_WIRE_FORMAT;
    }
    for (size_t index = 88u; index < DAK_SECTOR_WIRE_BYTES; ++index) {
        if (input[index] != 0u) return DAK_SECTOR_BAD_WIRE_FORMAT;
    }

    dak_app_sector_v1 decoded = {0};
    decoded.app_id = read_u64_le(input + 8u);
    decoded.sector_id = read_u32_le(input + 16u);
    decoded.kind = read_u16_le(input + 20u);
    decoded.flags = read_u16_le(input + 22u);
    decoded.offset_bytes = read_u64_le(input + 24u);
    decoded.length_bytes = read_u64_le(input + 32u);
    decoded.alignment_bytes = read_u32_le(input + 40u);
    decoded.permissions = read_u32_le(input + 44u);
    dak_bytes_copy(decoded.digest, input + 48u, DAK_SECTOR_DIGEST_BYTES);
    decoded.generation = read_u64_le(input + 80u);

    if (decoded.app_id == 0u || decoded.sector_id == 0u || decoded.generation == 0u ||
        decoded.kind < (uint16_t)DAK_SECTOR_MANIFEST ||
        decoded.kind > (uint16_t)DAK_SECTOR_JOURNAL ||
        (decoded.flags & ~DAK_SECTOR_FLAG_KNOWN) != 0u ||
        (decoded.flags & (DAK_SECTOR_FLAG_VERIFIED | DAK_SECTOR_FLAG_SEALED)) !=
            (DAK_SECTOR_FLAG_VERIFIED | DAK_SECTOR_FLAG_SEALED) ||
        decoded.length_bytes == 0u || !power_of_two(decoded.alignment_bytes) ||
        decoded.alignment_bytes > DAK_SECTOR_MAX_ALIGNMENT ||
        decoded.offset_bytes % decoded.alignment_bytes != 0u ||
        !bytes_nonzero(decoded.digest, sizeof(decoded.digest)) ||
        permission_model_valid(&decoded) != DAK_SECTOR_OK) {
        return DAK_SECTOR_INVALID_DESCRIPTOR;
    }

    *sector = decoded;
    return DAK_SECTOR_OK;
}

dak_sector_status dak_sector_validate(
    const dak_app_sector_v1 *sector,
    uint64_t image_bytes
) {
    if (sector == NULL || image_bytes == 0u) return DAK_SECTOR_INVALID_ARGUMENT;
    if (sector->app_id == 0u || sector->sector_id == 0u || sector->generation == 0u ||
        sector->length_bytes == 0u || !power_of_two(sector->alignment_bytes) ||
        sector->alignment_bytes > DAK_SECTOR_MAX_ALIGNMENT ||
        sector->offset_bytes % sector->alignment_bytes != 0u ||
        sector->offset_bytes > image_bytes ||
        sector->length_bytes > image_bytes - sector->offset_bytes ||
        (sector->flags & ~DAK_SECTOR_FLAG_KNOWN) != 0u ||
        (sector->flags & (DAK_SECTOR_FLAG_VERIFIED | DAK_SECTOR_FLAG_SEALED)) !=
            (DAK_SECTOR_FLAG_VERIFIED | DAK_SECTOR_FLAG_SEALED) ||
        !bytes_nonzero(sector->digest, sizeof(sector->digest))) {
        return DAK_SECTOR_OUT_OF_RANGE;
    }
    return permission_model_valid(sector);
}

dak_sector_status dak_sector_table_validate(
    uint64_t app_id,
    const dak_app_sector_v1 *sectors,
    size_t sector_count,
    uint64_t image_bytes
) {
    if (app_id == 0u || sectors == NULL || sector_count == 0u ||
        sector_count > DAK_SECTOR_MAX_COUNT || image_bytes == 0u) {
        return DAK_SECTOR_INVALID_ARGUMENT;
    }

    size_t manifest_count = 0u;
    size_t code_count = 0u;
    for (size_t index = 0u; index < sector_count; ++index) {
        const dak_app_sector_v1 *sector = &sectors[index];
        if (sector->app_id != app_id) return DAK_SECTOR_INVALID_DESCRIPTOR;
        const dak_sector_status status = dak_sector_validate(sector, image_bytes);
        if (status != DAK_SECTOR_OK) return status;
        if (sector->kind == (uint16_t)DAK_SECTOR_MANIFEST) ++manifest_count;
        if (sector->kind == (uint16_t)DAK_SECTOR_CODE) ++code_count;

        for (size_t prior = 0u; prior < index; ++prior) {
            const dak_app_sector_v1 *other = &sectors[prior];
            if (sector->sector_id == other->sector_id) return DAK_SECTOR_DUPLICATE_ID;
            const uint64_t sector_end = sector->offset_bytes + sector->length_bytes;
            const uint64_t other_end = other->offset_bytes + other->length_bytes;
            if (sector->offset_bytes < other_end && other->offset_bytes < sector_end) {
                return DAK_SECTOR_OVERLAP;
            }
        }
    }

    if (manifest_count != 1u || code_count == 0u) {
        return DAK_SECTOR_MISSING_REQUIRED_KIND;
    }
    return DAK_SECTOR_OK;
}
