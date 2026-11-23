#include "duckos/kernel.h"
#include "duckos/arch_x86_64.h"

#include <stdint.h>
#include <string.h>

#define SYS_WRITE 1u
#define SYS_READ 2u
#define SYS_OPEN 3u
#define SYS_CLOSE 4u
#define SYS_YIELD 5u

#define USER_LIMIT UINT64_C(0x40000000)

static int valid_user_range(uint64_t address, uint64_t length) {
    if (length == 0u) return 1;
    return address != 0u && address < USER_LIMIT &&
           length <= USER_LIMIT - address;
}

int64_t duckos_syscall_dispatch(uint64_t number,
                                uint64_t arg0, uint64_t arg1, uint64_t arg2,
                                uint64_t arg3, uint64_t arg4, uint64_t arg5) {
    (void)arg3; (void)arg4; (void)arg5;
    if (number == SYS_WRITE) {
        if (arg2 > DUCKOS_MAX_SYSCALL_TRANSFER ||
            !valid_user_range(arg1, arg2)) return -1;
        return duckos_vfs_write((int64_t)arg0,
                                (const void *)(uintptr_t)arg1, arg2);
    }
    if (number == SYS_READ) {
        if (arg2 > DUCKOS_MAX_SYSCALL_TRANSFER ||
            !valid_user_range(arg1, arg2)) return -1;
        return duckos_vfs_read((int64_t)arg0, (void *)(uintptr_t)arg1, arg2);
    }
    if (number == SYS_OPEN) {
        if (arg1 == 0u || arg1 > DUCKOS_MAX_PATH_LENGTH ||
            !valid_user_range(arg0, arg1)) return -1;
        char path[DUCKOS_MAX_PATH_LENGTH + 1u];
        memcpy(path, (const void *)(uintptr_t)arg0, (size_t)arg1);
        if (memchr(path, '\0', (size_t)arg1) != NULL) return -1;
        path[arg1] = '\0';
        return duckos_vfs_open(path, (uint32_t)arg2);
    }
    if (number == SYS_CLOSE)
        return duckos_vfs_close((int64_t)arg0);
    if (number == SYS_YIELD) {
        duckos_process_yield();
        return 0;
    }
    return -38;
}

int64_t duckos_syscall_invoke(void *context, uint64_t number,
                              uint64_t arg0, uint64_t arg1, uint64_t arg2,
                              uint64_t arg3, uint64_t arg4, uint64_t arg5) {
    (void)context;
    register uint64_t rax __asm__("rax") = number;
    register uint64_t rdi __asm__("rdi") = arg0;
    register uint64_t rsi __asm__("rsi") = arg1;
    register uint64_t rdx __asm__("rdx") = arg2;
    register uint64_t r10 __asm__("r10") = arg3;
    register uint64_t r8 __asm__("r8") = arg4;
    register uint64_t r9 __asm__("r9") = arg5;
    __asm__ volatile (
        "int $0x80"
        : "+a"(rax)
        : "D"(rdi), "S"(rsi), "d"(rdx), "r"(r10), "r"(r8), "r"(r9)
        : "rcx", "r11", "memory"
    );
    return (int64_t)rax;
}
