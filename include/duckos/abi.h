#ifndef DUCKOS_ABI_H
#define DUCKOS_ABI_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCK_ABI_MAJOR 1u
#define DUCK_ABI_MINOR 0u
#define DUCK_ABI_MAGIC UINT32_C(0x49424144)
#define DUCK_ABI_ELF_OSABI 0xD5u
#define DUCK_ABI_NOTE_TYPE UINT32_C(0x44414249)
#define DUCK_ABI_MAX_ARGUMENTS 4096u
#define DUCK_ABI_FRAME_ALIGNMENT 16u
#define DUCK_ABI_VALUE_ALIGNMENT 16u

typedef enum DuckValueKind {
    DUCK_VALUE_UNIT = 0, DUCK_VALUE_I64 = 1, DUCK_VALUE_U64 = 2,
    DUCK_VALUE_BOOL = 3, DUCK_VALUE_F64 = 4, DUCK_VALUE_POINTER = 5,
    DUCK_VALUE_UTF8 = 6, DUCK_VALUE_BYTES = 7, DUCK_VALUE_HANDLE = 8,
    DUCK_VALUE_ERROR = 9
} DuckValueKind;

enum {
    DUCK_VALUE_BORROWED = 1u << 0,
    DUCK_VALUE_OWNED = 1u << 1,
    DUCK_VALUE_READ_ONLY = 1u << 2
};

typedef struct DuckValue {
    uint64_t payload;
    uint32_t kind;
    uint32_t flags;
} DuckValue;

enum {
    DUCK_CALL_HAS_CAPTURES = 1u << 0,
    DUCK_CALL_NO_ALLOC = 1u << 1
};

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
    DUCK_STATUS_TOO_MANY_ARGUMENTS = 6,
    DUCK_STATUS_INVALID_FLAGS = 7,
    DUCK_STATUS_INVALID_VALUE = 8,
    DUCK_STATUS_NOT_IMPLEMENTED = 9,
    DUCK_STATUS_ACCESS_DENIED = 10,
    DUCK_STATUS_OUT_OF_MEMORY = 11,
    DUCK_STATUS_IO_ERROR = 12,
    DUCK_STATUS_NOT_FOUND = 13,
    DUCK_STATUS_CANCELLED = 14,
    DUCK_STATUS_INTERNAL_ERROR = 15,
    DUCK_STATUS_ARITHMETIC_OVERFLOW = 16,
    DUCK_STATUS_DIVISION_BY_ZERO = 17,
    DUCK_STATUS_BAD_ARGUMENT_LAYOUT = 18
} DuckAbiStatus;

typedef enum DuckSyscallNumber {
    DUCK_SYS_PROCESS_EXIT = 1,
    DUCK_SYS_IO_READ = 2,
    DUCK_SYS_IO_WRITE = 3,
    DUCK_SYS_CLOCK_MONOTONIC = 4,
    DUCK_SYS_MEMORY_MAP = 5,
    DUCK_SYS_MEMORY_UNMAP = 6,
    DUCK_SYS_THREAD_CREATE = 7,
    DUCK_SYS_THREAD_JOIN = 8,
    DUCK_SYS_THREAD_YIELD = 9,
    DUCK_SYS_CAPABILITY_QUERY = 10
} DuckSyscallNumber;

typedef struct DuckAbiError {
    DuckAbiStatus status;
    const char *message;
} DuckAbiError;

/*
 * DABI64 function call (x86-64):
 *   R10 = const DuckCallFrame *
 *   R11 = DuckCallResult *
 *   RAX = DuckAbiStatus on return
 *
 * Callee-saved: RBX, RBP, R12-R15 and RSP.
 * Caller-saved: RAX, RCX, RDX, RSI, RDI, R8-R11 and all XMM registers.
 * RSP is 32-byte aligned immediately before CALL; at entry RSP + 8
 * is 32-byte aligned. There is no red zone.
 *
 * DABI64 system call:
 *   RAX = syscall number; RDI = const DuckCallFrame *;
 *   RSI = DuckCallResult *; RAX = DuckAbiStatus on return.
 * SYSCALL clobbers RCX and R11. Kernel code validates all user ranges.
 */
DuckAbiStatus duck_abi_validate_frame(
    const DuckCallFrame *frame, size_t readable_bytes, DuckAbiError *error);
DuckAbiStatus duck_abi_validate_result(
    const DuckCallResult *result, DuckAbiError *error);
DuckAbiStatus duck_abi_result_write(
    DuckCallResult *result, DuckValue value, DuckAbiError *error);
const char *duck_abi_status_name(DuckAbiStatus status);

#if defined(__cplusplus)
static_assert(sizeof(DuckValue) == 16, "DABI64 DuckValue layout changed");
static_assert(sizeof(DuckCallFrame) == 48, "DABI64 DuckCallFrame layout changed");
static_assert(offsetof(DuckCallFrame, arguments) == 32, "DABI64 argument offset changed");
static_assert(offsetof(DuckCallFrame, captures) == 40, "DABI64 capture offset changed");
static_assert(sizeof(DuckCallResult) == 16, "DABI64 result layout changed");
#else
_Static_assert(sizeof(DuckValue) == 16, "DABI64 DuckValue layout changed");
_Static_assert(sizeof(DuckCallFrame) == 48, "DABI64 DuckCallFrame layout changed");
_Static_assert(offsetof(DuckCallFrame, arguments) == 32, "DABI64 argument offset changed");
_Static_assert(offsetof(DuckCallFrame, captures) == 40, "DABI64 capture offset changed");
_Static_assert(sizeof(DuckCallResult) == 16, "DABI64 result layout changed");
#endif

#ifdef __cplusplus
}
#endif
#endif
