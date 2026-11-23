#include "duckos/kernel.h"
#include "duckos/arch_x86_64.h"

#include <string.h>

#define PROCESS_LIMIT 16u
#define PROCESS_NAME_LENGTH 31u
#define PROCESS_STACK_SIZE 8192u

struct DuckOsProcess {
    uint64_t id;
    char name[PROCESS_NAME_LENGTH + 1u];
    DuckOsProcessState state;
    DuckOsProcessEntry entry;
    void *argument;
    void *stack_allocation;
    uint64_t *saved_stack;
    int64_t exit_code;
    struct DuckOsProcess *next;
};

static DuckOsProcess *processes;
static DuckOsProcess *current_process;
static uint64_t next_process_id = 1u;
static uint64_t *scheduler_stack;
static uint8_t scheduler_active;

static void process_bootstrap(void) __attribute__((noreturn));

void duckos_process_init(void) {
    processes = NULL;
    current_process = NULL;
    next_process_id = 1u;
    scheduler_stack = 0u;
    scheduler_active = 0u;
}

DuckOsProcess *duckos_process_create(const char *name,
                                     DuckOsProcessEntry entry, void *argument) {
    if (name == NULL || entry == NULL) return NULL;
    DuckOsProcess *process = (DuckOsProcess *)duckos_kcalloc(1u, sizeof *process);
    if (process == NULL) return NULL;
    process->stack_allocation = duckos_kmalloc(PROCESS_STACK_SIZE);
    if (process->stack_allocation == NULL) {
        duckos_kfree(process);
        return NULL;
    }

    size_t name_length = strlen(name);
    if (name_length > PROCESS_NAME_LENGTH) name_length = PROCESS_NAME_LENGTH;
    memcpy(process->name, name, name_length);
    process->name[name_length] = '\0';
    process->id = next_process_id++;
    process->state = DUCKOS_PROCESS_READY;
    process->entry = entry;
    process->argument = argument;

    uintptr_t stack_top = (uintptr_t)process->stack_allocation + PROCESS_STACK_SIZE;
    stack_top = (stack_top & ~(uintptr_t)15u) - 8u;
    uint64_t *stack = (uint64_t *)(stack_top - 7u * sizeof(uint64_t));
    for (uint32_t i = 0u; i < 6u; ++i) stack[i] = 0u;
    stack[6] = (uint64_t)(uintptr_t)process_bootstrap;
    process->saved_stack = stack;

    process->next = processes;
    processes = process;
    return process;
}

static void reap_zombies(void) {
    DuckOsProcess **link = &processes;
    while (*link != NULL) {
        DuckOsProcess *process = *link;
        if (process->state != DUCKOS_PROCESS_ZOMBIE) {
            link = &process->next;
            continue;
        }
        *link = process->next;
        duckos_serial_write("[DuckOS] process ");
        duckos_serial_u64(process->id);
        duckos_serial_write(" exited with ");
        duckos_serial_u64((uint64_t)process->exit_code);
        duckos_serial_write("\n");
        duckos_kfree(process->stack_allocation);
        duckos_kfree(process);
    }
}

void duckos_process_yield(void) {
    if (current_process == NULL || !scheduler_active) return;
    current_process->state = DUCKOS_PROCESS_READY;
    duckos_context_switch((uint64_t **)&current_process->saved_stack,
                          scheduler_stack);
}

void duckos_process_exit(int64_t exit_code) {
    if (current_process == NULL || !scheduler_active) {
        duckos_cli();
        for (;;) duckos_hlt();
    }
    current_process->exit_code = exit_code;
    current_process->state = DUCKOS_PROCESS_ZOMBIE;
    duckos_context_switch((uint64_t **)&current_process->saved_stack,
                          &scheduler_stack);
    duckos_cli();
    for (;;) duckos_hlt();
}

uint64_t duckos_process_current_id(void) {
    return current_process == NULL ? 0u : current_process->id;
}

static void process_bootstrap(void) {
    DuckOsProcess *process = current_process;
    if (process != NULL && process->entry != NULL)
        process->entry(process->argument);
    duckos_process_exit(0);
}

void duckos_scheduler_run(void) {
    if (scheduler_active) return;
    scheduler_active = 1u;
    for (;;) {
        reap_zombies();
        DuckOsProcess *next = processes;
        while (next != NULL && next->state != DUCKOS_PROCESS_READY)
            next = next->next;
        if (next == NULL) break;
        current_process = next;
        current_process->state = DUCKOS_PROCESS_RUNNING;
        duckos_context_switch(&scheduler_stack, current_process->saved_stack);
        current_process = NULL;
    }
    reap_zombies();
    scheduler_active = 0u;
}
