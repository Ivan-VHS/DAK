#ifndef DUCKOS_ABI_DABI64_H
#define DUCKOS_ABI_DABI64_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCK_DABI64_MAJOR 1u
#define DUCK_DABI64_MINOR 0u
#define DUCK_DABI64_MAGIC UINT32_C(0x49424144)
#define DUCK_DABI64_NOTE_TYPE UINT32_C(0x44414249)
#define DUCK_DABI64_ELF_OSABI 0xD5u
#define DUCK_DABI64_ARCH_X86_64 1u
#define DUCK_DABI64_MAX_ARGUMENTS 64u
#define DUCK_DABI64_REQUIRED_ALIGNMENT 16u

typedef enum DuckValueKind {
    DUCK_VALUE_UNIT = 0u,
    DUCK_VALUE_I64 = 1u,
    DUCK_VALUE_BOOL = 2u,
    DUCK_VALUE_STRING = 3u,
    DUCK_VALUE_ARRAY = 4u,
    DUCK_VALUE_ITERATOR = 5u
} DuckValueKind;

typedef struct DuckValue {
    uint64_t payload;
    uint32_t kind;
    uint32_t flags;
} DuckValue;

typedef struct DuckCallFrame {
    uint32_t magic;
    uint16_t abi_major;
    uint16_t abi_minor;
    uint32_t byte_size;
    uint32_t argument_count;
    uint32_t capture_count;
    uint32_t flags;
    uint32_t reserved0;
    uint32_t reserved1;
    const DuckValue *arguments;
    const DuckValue *captures;
} DuckCallFrame;

typedef struct DuckCallResult {
    DuckValue value;
} DuckCallResult;

typedef enum DuckAbiStatus {
    DUCK_STATUS_OK = 0,
    DUCK_STATUS_INVALID_POINTER = 1,
    DUCK_STATUS_BAD_MAGIC = 2,
    DUCK_STATUS_VERSION_MISMATCH = 3,
    DUCK_STATUS_BAD_FRAME_SIZE = 4,
    DUCK_STATUS_BAD_ALIGNMENT = 5,
    DUCK_STATUS_INVALID_FLAGS = 7,
    DUCK_STATUS_ARITHMETIC_OVERFLOW = 16,
    DUCK_STATUS_DIVISION_BY_ZERO = 17,
    DUCK_STATUS_BAD_ARGUMENT_LAYOUT = 18
} DuckAbiStatus;

/*
 * DABI64 is an x86-64 DuckOS calling convention, not System V.
 * Entry registers: R10 = call frame, R11 = result; RAX = status on return.
 * The caller aligns RSP to 32 bytes before CALL. Data pointers are 16-byte
 * aligned. Captures and non-zero frame flags are reserved in v1.
 *
 * Value tags 0..5 are stable runtime tags. The initial machine-code entry
 * path accepts scalar i64 arguments only; runtime tags do not by themselves
 * extend the compiler backend's supported source-language types.
 */
DuckAbiStatus duck_dabi64_validate_call(
    const DuckCallFrame *frame,
    const DuckCallResult *result,
    uint32_t expected_argument_count
);
DuckAbiStatus duck_dabi64_validate_i64_arguments(const DuckCallFrame *frame);
void duck_dabi64_result_reset(DuckCallResult *result);
DuckAbiStatus duck_dabi64_result_write_i64(DuckCallResult *result, int64_t value);
DuckAbiStatus duck_dabi64_result_read_i64(const DuckCallResult *result, int64_t *value);

#if !defined(__cplusplus)
_Static_assert(sizeof(void *) == 8, "DABI64 requires 64-bit pointers");
_Static_assert(sizeof(DuckValue) == 16, "DABI64 value size mismatch");
_Static_assert(offsetof(DuckValue, payload) == 0, "DABI64 payload offset mismatch");
_Static_assert(offsetof(DuckValue, kind) == 8, "DABI64 kind offset mismatch");
_Static_assert(offsetof(DuckValue, flags) == 12, "DABI64 value flags offset mismatch");
_Static_assert(sizeof(DuckCallFrame) == 48, "DABI64 call frame size mismatch");
_Static_assert(offsetof(DuckCallFrame, magic) == 0, "DABI64 magic offset mismatch");
_Static_assert(offsetof(DuckCallFrame, abi_major) == 4, "DABI64 major offset mismatch");
_Static_assert(offsetof(DuckCallFrame, byte_size) == 8, "DABI64 byte size offset mismatch");
_Static_assert(offsetof(DuckCallFrame, argument_count) == 12, "DABI64 argument count offset mismatch");
_Static_assert(offsetof(DuckCallFrame, arguments) == 32, "DABI64 arguments offset mismatch");
_Static_assert(offsetof(DuckCallFrame, captures) == 40, "DABI64 captures offset mismatch");
_Static_assert(sizeof(DuckCallResult) == 16, "DABI64 result size mismatch");
#endif

#ifdef __cplusplus
}
#endif

#endif
