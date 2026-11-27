#ifndef DAK_APP_SECTOR_H
#define DAK_APP_SECTOR_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DAK_SECTOR_WIRE_VERSION 1u
#define DAK_SECTOR_WIRE_BYTES 96u
#define DAK_SECTOR_DIGEST_BYTES 32u
#define DAK_SECTOR_MAX_COUNT 64u
#define DAK_SECTOR_MAX_ALIGNMENT 1048576u
#define DAK_SECTOR_MAGIC_0 ((uint8_t)'D')
#define DAK_SECTOR_MAGIC_1 ((uint8_t)'A')
#define DAK_SECTOR_MAGIC_2 ((uint8_t)'K')
#define DAK_SECTOR_MAGIC_3 ((uint8_t)'S')

typedef enum dak_sector_kind {
    DAK_SECTOR_MANIFEST = 1,
    DAK_SECTOR_CODE = 2,
    DAK_SECTOR_READ_ONLY_DATA = 3,
    DAK_SECTOR_WRITABLE_DATA = 4,
    DAK_SECTOR_RESOURCE = 5,
    DAK_SECTOR_POLICY = 6,
    DAK_SECTOR_JOURNAL = 7
} dak_sector_kind;

enum {
    DAK_SECTOR_PERMISSION_READ = 0x00000001u,
    DAK_SECTOR_PERMISSION_WRITE = 0x00000002u,
    DAK_SECTOR_PERMISSION_EXECUTE = 0x00000004u,
    DAK_SECTOR_PERMISSIONS_KNOWN = 0x00000007u
};

enum {
    DAK_SECTOR_FLAG_VERIFIED = 0x0001u,
    DAK_SECTOR_FLAG_SEALED = 0x0002u,
    DAK_SECTOR_FLAG_OPTIONAL = 0x0004u,
    DAK_SECTOR_FLAG_KNOWN = 0x0007u
};

typedef struct dak_app_sector_v1 {
    uint64_t app_id;
    uint32_t sector_id;
    uint16_t kind;
    uint16_t flags;
    uint64_t offset_bytes;
    uint64_t length_bytes;
    uint32_t alignment_bytes;
    uint32_t permissions;
    uint8_t digest[DAK_SECTOR_DIGEST_BYTES];
    uint64_t generation;
} dak_app_sector_v1;

typedef enum dak_sector_status {
    DAK_SECTOR_OK = 0,
    DAK_SECTOR_INVALID_ARGUMENT,
    DAK_SECTOR_BAD_WIRE_FORMAT,
    DAK_SECTOR_INVALID_DESCRIPTOR,
    DAK_SECTOR_OUT_OF_RANGE,
    DAK_SECTOR_DUPLICATE_ID,
    DAK_SECTOR_OVERLAP,
    DAK_SECTOR_MISSING_REQUIRED_KIND,
    DAK_SECTOR_BAD_PERMISSION_MODEL
} dak_sector_status;

/* Canonical little-endian codec. No compiler-specific packed struct is used. */
dak_sector_status dak_sector_encode(
    const dak_app_sector_v1 *sector,
    uint8_t output[DAK_SECTOR_WIRE_BYTES]
);

dak_sector_status dak_sector_decode(
    const uint8_t input[DAK_SECTOR_WIRE_BYTES],
    dak_app_sector_v1 *sector
);

dak_sector_status dak_sector_validate(
    const dak_app_sector_v1 *sector,
    uint64_t image_bytes
);

dak_sector_status dak_sector_table_validate(
    uint64_t app_id,
    const dak_app_sector_v1 *sectors,
    size_t sector_count,
    uint64_t image_bytes
);

#ifdef __cplusplus
}
#endif

#endif
