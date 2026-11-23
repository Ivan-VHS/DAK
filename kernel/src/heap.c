#include "duckos/kernel.h"
#include "duckos/arch_x86_64.h"

#include <stdint.h>

#define SLAB_MAGIC UINT32_C(0x44534c42)
#define LARGE_MAGIC UINT32_C(0x444c4152)
#define SLAB_COUNT 8u
#define LARGE_PAGE_SIZE DUCKOS_PAGE_SIZE

typedef struct DuckOsSlab DuckOsSlab;
typedef struct DuckOsFreeBlock {
    struct DuckOsFreeBlock *next;
} DuckOsFreeBlock;

typedef struct {
    uint64_t owner;
    uint32_t magic;
    uint16_t class_index;
    uint16_t reserved;
} DuckOsAllocHeader;

struct DuckOsSlab {
    DuckOsSlab *next;
    DuckOsFreeBlock *free_list;
    uint32_t magic;
    uint16_t class_index;
    uint16_t block_size;
    uint16_t capacity;
    uint16_t free_count;
    uint32_t reserved;
};

static const uint16_t class_payloads[SLAB_COUNT] = {
    16u, 32u, 64u, 128u, 256u, 512u, 1024u, 2048u
};
static DuckOsSlab *slabs[SLAB_COUNT];

static uint64_t align_up(uint64_t value, uint64_t alignment) {
    return (value + alignment - 1u) & ~(alignment - 1u);
}

static DuckOsSlab *new_slab(uint16_t class_index) {
    DuckOsSlab *slab = (DuckOsSlab *)duckos_alloc_page();
    if (slab == NULL) return NULL;
    uint64_t block_size = align_up(
        sizeof(DuckOsAllocHeader) + class_payloads[class_index], 16u);
    uint64_t first = align_up(sizeof(DuckOsSlab), 16u);
    uint64_t capacity = (DUCKOS_PAGE_SIZE - first) / block_size;
    if (capacity == 0u || capacity > UINT16_MAX) {
        duckos_free_page(slab);
        return NULL;
    }

    slab->magic = SLAB_MAGIC;
    slab->class_index = class_index;
    slab->block_size = (uint16_t)block_size;
    slab->capacity = (uint16_t)capacity;
    slab->free_count = (uint16_t)capacity;
    slab->free_list = NULL;

    uint8_t *base = (uint8_t *)slab;
    for (uint64_t i = 0u; i < capacity; ++i) {
        uint8_t *block = base + first + i * block_size;
        DuckOsFreeBlock *free_block = (DuckOsFreeBlock *)block;
        free_block->next = slab->free_list;
        slab->free_list = free_block;
    }
    slab->next = slabs[class_index];
    slabs[class_index] = slab;
    return slab;
}

void *duckos_kmalloc(size_t size) {
    if (size == 0u) return NULL;
    if ((uint64_t)size > UINT64_MAX - sizeof(DuckOsAllocHeader)) return NULL;

    for (uint16_t class_index = 0u; class_index < SLAB_COUNT; ++class_index) {
        if (size > class_payloads[class_index]) continue;
        uint64_t irq_flags = duckos_irq_save();
        DuckOsSlab *slab = slabs[class_index];
        while (slab != NULL && slab->free_list == NULL) slab = slab->next;
        if (slab == NULL) slab = new_slab(class_index);
        if (slab == NULL) {
            duckos_irq_restore(irq_flags);
            return NULL;
        }

        DuckOsFreeBlock *block = slab->free_list;
        slab->free_list = block->next;
        slab->free_count--;
        DuckOsAllocHeader *header = (DuckOsAllocHeader *)block;
        header->owner = (uint64_t)(uintptr_t)slab;
        header->magic = SLAB_MAGIC;
        header->class_index = class_index;
        header->reserved = 0u;
        duckos_irq_restore(irq_flags);
        return (uint8_t *)header + sizeof *header;
    }

    uint64_t bytes = (uint64_t)size + sizeof(DuckOsAllocHeader);
    uint64_t pages = (bytes + DUCKOS_PAGE_SIZE - 1u) / DUCKOS_PAGE_SIZE;
    if (pages == 0u || pages > UINT32_MAX) return NULL;

    uint64_t irq_flags = duckos_irq_save();
    void *base = duckos_alloc_pages(pages);
    if (base == NULL) {
        duckos_irq_restore(irq_flags);
        return NULL;
    }
    DuckOsAllocHeader *header = (DuckOsAllocHeader *)base;
    header->owner = pages;
    header->magic = LARGE_MAGIC;
    header->class_index = UINT16_MAX;
    header->reserved = 0u;
    duckos_irq_restore(irq_flags);
    return (uint8_t *)header + sizeof *header;
}

void duckos_kfree(void *pointer) {
    if (pointer == NULL) return;
    DuckOsAllocHeader *header =
        (DuckOsAllocHeader *)((uint8_t *)pointer - sizeof(DuckOsAllocHeader));

    if (header->magic == LARGE_MAGIC) {
        uint64_t pages = header->owner;
        if (pages == 0u || pages > UINT32_MAX) return;
        uint64_t irq_flags = duckos_irq_save();
        header->magic = 0u;
        duckos_free_pages(header, pages);
        duckos_irq_restore(irq_flags);
        return;
    }

    if (header->magic != SLAB_MAGIC ||
        header->class_index >= SLAB_COUNT) return;
    uint64_t irq_flags = duckos_irq_save();
    DuckOsSlab *slab = (DuckOsSlab *)(uintptr_t)header->owner;
    if (slab == NULL || slab->magic != SLAB_MAGIC ||
        slab->class_index != header->class_index ||
        slab->free_count >= slab->capacity) {
        duckos_irq_restore(irq_flags);
        return;
    }
    header->magic = 0u;
    DuckOsFreeBlock *block = (DuckOsFreeBlock *)header;
    block->next = slab->free_list;
    slab->free_list = block;
    slab->free_count++;

    if (slab->free_count == slab->capacity) {
        uint16_t class_index = slab->class_index;
        DuckOsSlab **link = &slabs[class_index];
        while (*link != NULL && *link != slab) link = &(*link)->next;
        if (*link == slab) {
            *link = slab->next;
            slab->magic = 0u;
            duckos_free_page(slab);
        }
    }
    duckos_irq_restore(irq_flags);
}

void *duckos_kcalloc(size_t count, size_t size) {
    if (count == 0u || size == 0u || count > SIZE_MAX / size) return NULL;
    size_t total = count * size;
    uint8_t *memory = (uint8_t *)duckos_kmalloc(total);
    if (memory == NULL) return NULL;
    for (size_t i = 0u; i < total; ++i) memory[i] = 0u;
    return memory;
}
