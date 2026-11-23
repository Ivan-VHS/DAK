#ifndef DUCKOS_KERNEL_H
#define DUCKOS_KERNEL_H

#include <stddef.h>
#include <stdint.h>

#define DUCKOS_PAGE_SIZE 4096u
#define DUCKOS_MAX_PHYSICAL_ADDRESS UINT64_C(0x40000000)
#define DUCKOS_MAX_SYSCALL_TRANSFER 65536u
#define DUCKOS_MAX_PATH_LENGTH 255u

typedef struct {
    uint64_t free_pages;
    uint64_t total_pages;
    uint64_t used_pages;
} DuckOsMemoryStats;

typedef enum {
    DUCKOS_VM_WRITE = 1u,
    DUCKOS_VM_USER = 2u,
    DUCKOS_VM_EXEC = 4u
} DuckOsVmFlags;

typedef enum {
    DUCKOS_PROCESS_READY = 0,
    DUCKOS_PROCESS_RUNNING,
    DUCKOS_PROCESS_BLOCKED,
    DUCKOS_PROCESS_ZOMBIE
} DuckOsProcessState;

typedef void (*DuckOsProcessEntry)(void *argument);

typedef struct DuckOsProcess DuckOsProcess;

typedef struct {
    uint64_t number;
    uint64_t argument0;
    uint64_t argument1;
    uint64_t argument2;
    uint64_t argument3;
    uint64_t argument4;
    uint64_t argument5;
} DuckOsSyscallArguments;

void duckos_serial_init(void);
void duckos_serial_write(const char *text);
void duckos_serial_hex(uint64_t value);
void duckos_serial_u64(uint64_t value);
void duckos_kernel_main(uint32_t multiboot_magic, uint32_t multiboot_info);

int duckos_memory_init(uint64_t multiboot_info);
void *duckos_alloc_page(void);
void duckos_free_page(void *address);
void *duckos_alloc_pages(uint64_t count);
void duckos_free_pages(void *address, uint64_t count);
int duckos_vm_map_page(uint64_t virtual_address, uint64_t physical_address,
                       uint32_t flags);
int duckos_vm_unmap_page(uint64_t virtual_address);
int duckos_vm_create_address_space(uint64_t *root_physical);
void duckos_vm_switch(uint64_t root_physical);
DuckOsMemoryStats duckos_memory_stats(void);

void *duckos_kmalloc(size_t size);
void duckos_kfree(void *pointer);
void *duckos_kcalloc(size_t count, size_t size);

void duckos_vfs_init(void);
int64_t duckos_vfs_open(const char *path, uint32_t mode);
int64_t duckos_vfs_read(int64_t descriptor, void *buffer, uint64_t capacity);
int64_t duckos_vfs_write(int64_t descriptor, const void *buffer, uint64_t length);
int64_t duckos_vfs_close(int64_t descriptor);

int64_t duckos_syscall_dispatch(uint64_t number,
                                uint64_t arg0, uint64_t arg1, uint64_t arg2,
                                uint64_t arg3, uint64_t arg4, uint64_t arg5);
int64_t duckos_syscall_invoke(void *context, uint64_t number,
                              uint64_t arg0, uint64_t arg1, uint64_t arg2,
                              uint64_t arg3, uint64_t arg4, uint64_t arg5);

void duckos_process_init(void);
DuckOsProcess *duckos_process_create(const char *name,
                                     DuckOsProcessEntry entry, void *argument);
void duckos_process_yield(void);
void duckos_process_exit(int64_t exit_code);
void duckos_scheduler_run(void);
uint64_t duckos_process_current_id(void);

#endif
