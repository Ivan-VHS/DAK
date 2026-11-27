#include "app_sector.h"

#include <stdio.h>
#include <string.h>

#define CHECK(expression) do { \
    if (!(expression)) { \
        fprintf(stderr, "check failed at %s:%d: %s\n", __FILE__, __LINE__, #expression); \
        return 0; \
    } \
} while (0)

static dak_app_sector_v1 make_sector(
    uint64_t app_id,
    uint32_t sector_id,
    uint16_t kind,
    uint64_t offset,
    uint64_t length,
    uint32_t alignment,
    uint32_t permissions,
    uint8_t seed
) {
    dak_app_sector_v1 sector = {0};
    sector.app_id = app_id;
    sector.sector_id = sector_id;
    sector.kind = kind;
    sector.flags = DAK_SECTOR_FLAG_VERIFIED | DAK_SECTOR_FLAG_SEALED;
    sector.offset_bytes = offset;
    sector.length_bytes = length;
    sector.alignment_bytes = alignment;
    sector.permissions = permissions;
    sector.generation = 1u;
    for (size_t i = 0u; i < DAK_SECTOR_DIGEST_BYTES; ++i) {
        sector.digest[i] = (uint8_t)(seed + i + 1u);
    }
    return sector;
}

static void valid_table(dak_app_sector_v1 sectors[3]) {
    sectors[0] = make_sector(0x44414b0000000001ull, 1u, DAK_SECTOR_MANIFEST,
        0u, 512u, 8u, DAK_SECTOR_PERMISSION_READ, 1u);
    sectors[1] = make_sector(0x44414b0000000001ull, 2u, DAK_SECTOR_CODE,
        4096u, 4096u, 4096u,
        DAK_SECTOR_PERMISSION_READ | DAK_SECTOR_PERMISSION_EXECUTE, 2u);
    sectors[2] = make_sector(0x44414b0000000001ull, 3u, DAK_SECTOR_WRITABLE_DATA,
        8192u, 2048u, 4096u,
        DAK_SECTOR_PERMISSION_READ | DAK_SECTOR_PERMISSION_WRITE, 3u);
}

static int test_wire_round_trip_is_canonical(void) {
    dak_app_sector_v1 original = make_sector(42u, 7u, DAK_SECTOR_CODE, 4096u, 2048u,
        4096u, DAK_SECTOR_PERMISSION_READ | DAK_SECTOR_PERMISSION_EXECUTE, 11u);
    dak_app_sector_v1 decoded = {0};
    uint8_t wire[DAK_SECTOR_WIRE_BYTES];
    CHECK(dak_sector_encode(&original, wire) == DAK_SECTOR_OK);
    CHECK(wire[0] == 'D' && wire[1] == 'A' && wire[2] == 'K' && wire[3] == 'S');
    CHECK(wire[4] == 1u && wire[5] == 0u);
    CHECK(wire[6] == DAK_SECTOR_WIRE_BYTES && wire[7] == 0u);
    for (size_t i = 88u; i < DAK_SECTOR_WIRE_BYTES; ++i) CHECK(wire[i] == 0u);
    CHECK(dak_sector_decode(wire, &decoded) == DAK_SECTOR_OK);
    CHECK(memcmp(&decoded, &original, sizeof(original)) == 0);
    wire[95] = 1u;
    CHECK(dak_sector_decode(wire, &decoded) == DAK_SECTOR_BAD_WIRE_FORMAT);
    return 1;
}

static int test_valid_table_has_manifest_code_and_non_executable_data(void) {
    dak_app_sector_v1 sectors[3];
    valid_table(sectors);
    CHECK(dak_sector_table_validate(sectors[0].app_id, sectors, 3u, 12288u) == DAK_SECTOR_OK);
    CHECK(dak_sector_validate(&sectors[1], 12288u) == DAK_SECTOR_OK);
    return 1;
}

static int test_rejects_wx_misalignment_and_range_overflow(void) {
    dak_app_sector_v1 sector = make_sector(42u, 2u, DAK_SECTOR_CODE, 4096u, 1024u,
        4096u, DAK_SECTOR_PERMISSION_READ | DAK_SECTOR_PERMISSION_WRITE |
            DAK_SECTOR_PERMISSION_EXECUTE, 8u);
    CHECK(dak_sector_validate(&sector, 8192u) == DAK_SECTOR_BAD_PERMISSION_MODEL);

    sector.permissions = DAK_SECTOR_PERMISSION_READ | DAK_SECTOR_PERMISSION_EXECUTE;
    sector.offset_bytes = 4097u;
    CHECK(dak_sector_validate(&sector, 8192u) == DAK_SECTOR_OUT_OF_RANGE);

    sector.offset_bytes = UINT64_MAX - 255u;
    sector.length_bytes = 512u;
    sector.alignment_bytes = 1u;
    CHECK(dak_sector_validate(&sector, UINT64_MAX) == DAK_SECTOR_OUT_OF_RANGE);
    return 1;
}

static int test_rejects_overlap_duplicate_and_missing_mandatory_sectors(void) {
    dak_app_sector_v1 sectors[3];
    valid_table(sectors);
    sectors[2].offset_bytes = 4096u;
    CHECK(dak_sector_table_validate(sectors[0].app_id, sectors, 3u, 12288u) == DAK_SECTOR_OVERLAP);

    valid_table(sectors);
    sectors[2].sector_id = sectors[1].sector_id;
    CHECK(dak_sector_table_validate(sectors[0].app_id, sectors, 3u, 12288u) == DAK_SECTOR_DUPLICATE_ID);

    valid_table(sectors);
    sectors[1].kind = DAK_SECTOR_READ_ONLY_DATA;
    sectors[1].permissions = DAK_SECTOR_PERMISSION_READ;
    CHECK(dak_sector_table_validate(sectors[0].app_id, sectors, 3u, 12288u) ==
        DAK_SECTOR_MISSING_REQUIRED_KIND);
    return 1;
}

static int test_rejects_wrong_owner_and_unverified_sector(void) {
    dak_app_sector_v1 sectors[3];
    valid_table(sectors);
    sectors[2].app_id = 999u;
    CHECK(dak_sector_table_validate(sectors[0].app_id, sectors, 3u, 12288u) ==
        DAK_SECTOR_INVALID_DESCRIPTOR);

    valid_table(sectors);
    sectors[2].flags = DAK_SECTOR_FLAG_SEALED;
    CHECK(dak_sector_table_validate(sectors[0].app_id, sectors, 3u, 12288u) ==
        DAK_SECTOR_OUT_OF_RANGE);
    return 1;
}

int main(void) {
    if (!test_wire_round_trip_is_canonical() ||
        !test_valid_table_has_manifest_code_and_non_executable_data() ||
        !test_rejects_wx_misalignment_and_range_overflow() ||
        !test_rejects_overlap_duplicate_and_missing_mandatory_sectors() ||
        !test_rejects_wrong_owner_and_unverified_sector()) {
        return 1;
    }
    puts("DAK application sector tests passed");
    return 0;
}
