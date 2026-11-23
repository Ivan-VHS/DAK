#include "duckos/kernel.h"
#include "duckos/arch_x86_64.h"

#define MULTIBOOT2_BOOT_MAGIC UINT32_C(0x36d76289)
#define INIT_PATH "/init.txt"
#define SYSCALL_OPEN 3u
#define SYSCALL_READ 2u
#define SYSCALL_WRITE 1u
#define SYSCALL_CLOSE 4u

static void init_process(void *argument) {
    (void)argument;
    static const char path[] = INIT_PATH;
    char buffer[128];

    duckos_serial_write("[DuckOS] init: opening /init.txt through int 0x80\n");
    int64_t descriptor = duckos_syscall_invoke(
        NULL, SYSCALL_OPEN,
        (uint64_t)(uintptr_t)path,
        sizeof path - 1u,
        0u, 0u, 0u, 0u
    );
    if (descriptor < 0) {
        duckos_serial_write("[DuckOS] init: open failed\n");
        return;
    }

    int64_t count = duckos_syscall_invoke(
        NULL, SYSCALL_READ,
        (uint64_t)descriptor,
        (uint64_t)(uintptr_t)buffer,
        sizeof buffer - 1u,
        0u, 0u, 0u
    );
    if (count > 0 && (uint64_t)count < sizeof buffer) {
        buffer[count] = '\0';
        (void)duckos_syscall_invoke(
            NULL, SYSCALL_WRITE, 1u,
            (uint64_t)(uintptr_t)buffer,
            (uint64_t)count,
            0u, 0u, 0u
        );
    }

    (void)duckos_syscall_invoke(
        NULL, SYSCALL_CLOSE, (uint64_t)descriptor,
        0u, 0u, 0u, 0u, 0u
    );

    duckos_serial_write("[DuckOS] init: yielding to scheduler\n");
    duckos_process_yield();
    duckos_serial_write("[DuckOS] init: resumed; exiting\n");
}

void duckos_kernel_main(uint32_t multiboot_magic, uint32_t multiboot_info) {
    duckos_serial_init();
    duckos_serial_write("\nDuckOS x86-64 kernel boot\n");
    duckos_serial_write("[boot] Multiboot2 magic: ");
    duckos_serial_hex(multiboot_magic);
    duckos_serial_write("\n");

    if (multiboot_magic != MULTIBOOT2_BOOT_MAGIC) {
        duckos_serial_write("[boot] invalid Multiboot2 magic\n");
        for (;;) duckos_hlt();
    }
    if (!duckos_memory_init(multiboot_info)) {
        duckos_serial_write("[memory] failed to parse Multiboot2 memory map\n");
        for (;;) duckos_hlt();
    }

    DuckOsMemoryStats stats = duckos_memory_stats();
    duckos_serial_write("[memory] total pages: ");
    duckos_serial_u64(stats.total_pages);
    duckos_serial_write(", free pages: ");
    duckos_serial_u64(stats.free_pages);
    duckos_serial_write("\n");

    duckos_vfs_init();
    duckos_arch_init_interrupts();
    duckos_process_init();

    DuckOsProcess *init = duckos_process_create("init", init_process, NULL);
    if (init == NULL) {
        duckos_serial_write("[process] could not create init process\n");
        for (;;) duckos_hlt();
    }

    duckos_serial_write("[scheduler] running cooperative process queue\n");
    duckos_scheduler_run();
    duckos_serial_write("[scheduler] all runnable processes have exited\n");
    duckos_serial_write("[kernel] boot smoke test completed\n");

    duckos_cli();
    for (;;) duckos_hlt();
}
