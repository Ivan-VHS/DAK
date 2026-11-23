#include "duckos/kernel.h"
#include "duckos/arch_x86_64.h"

#include <stdint.h>

#define PAGE_COUNT (DUCKOS_MAX_PHYSICAL_ADDRESS / DUCKOS_PAGE_SIZE)
#define BITMAP_SIZE (PAGE_COUNT / 8u)
#define PAGE_PRESENT 0x001u
#define PAGE_WRITE 0x002u
#define PAGE_USER 0x004u
#define PAGE_LARGE 0x080u
#define PAGE_NX (UINT64_C(1) << 63u)
#define PAGE_ADDRESS_MASK UINT64_C(0x000ffffffffff000)

typedef struct {
    uint32_t type;
    uint32_t size;
} MultibootTag;

typedef struct {
    uint32_t type;
    uint32_t size;
    uint32_t entry_size;
    uint32_t entry_version;
} MultibootMemoryMapTag;

typedef struct {
    uint64_t address;
    uint64_t length;
    uint32_t type;
    uint32_t reserved;
} MultibootMemoryMapEntry;

typedef struct {
    uint32_t type;
    uint32_t size;
    uint32_t module_start;
    uint32_t module_end;
} MultibootModuleTag;

extern uint8_t __kernel_start[];
extern uint8_t __kernel_end[];
extern uint64_t boot_pml4[];
extern uint64_t boot_pdpt[];
extern uint64_t boot_pd[];

static uint8_t page_bitmap[BITMAP_SIZE];
static DuckOsMemoryStats memory_stats;

static int page_is_used(uint64_t page) {
    return (page_bitmap[page >> 3u] & (uint8_t)(1u << (page & 7u))) != 0u;
}
static void page_set_used(uint64_t page) {
    page_bitmap[page >> 3u] |= (uint8_t)(1u << (page & 7u));
}
static void page_set_free(uint64_t page) {
    page_bitmap[page >> 3u] &= (uint8_t)~(uint8_t)(1u << (page & 7u));
}
static void reserve_range(uint64_t start, uint64_t end) {
    if (end <= start) return;
    start &= ~(uint64_t)(DUCKOS_PAGE_SIZE - 1u);
    if (end > DUCKOS_MAX_PHYSICAL_ADDRESS) end = DUCKOS_MAX_PHYSICAL_ADDRESS;
    end = (end + DUCKOS_PAGE_SIZE - 1u) &
          ~(uint64_t)(DUCKOS_PAGE_SIZE - 1u);
    if (end > DUCKOS_MAX_PHYSICAL_ADDRESS) end = DUCKOS_MAX_PHYSICAL_ADDRESS;
    for (uint64_t address = start; address < end; address += DUCKOS_PAGE_SIZE) {
        uint64_t page = address / DUCKOS_PAGE_SIZE;
        if (!page_is_used(page)) {
            page_set_used(page);
            if (memory_stats.free_pages != 0u) memory_stats.free_pages--;
            memory_stats.used_pages++;
        }
    }
}
static void release_usable_range(uint64_t start, uint64_t length) {
    uint64_t end;
    if (length == 0u || start >= DUCKOS_MAX_PHYSICAL_ADDRESS ||
        start > UINT64_MAX - length) return;
    end = start + length;
    if (end > DUCKOS_MAX_PHYSICAL_ADDRESS) end = DUCKOS_MAX_PHYSICAL_ADDRESS;
    start = (start + DUCKOS_PAGE_SIZE - 1u) &
            ~(uint64_t)(DUCKOS_PAGE_SIZE - 1u);
    end &= ~(uint64_t)(DUCKOS_PAGE_SIZE - 1u);
    for (uint64_t address = start; address < end; address += DUCKOS_PAGE_SIZE) {
        uint64_t page = address / DUCKOS_PAGE_SIZE;
        if (page_is_used(page)) {
            page_set_free(page);
            memory_stats.free_pages++;
            if (memory_stats.used_pages != 0u) memory_stats.used_pages--;
        }
    }
}

int duckos_memory_init(uint64_t multiboot_info) {
    const uint8_t *info = (const uint8_t *)(uintptr_t)multiboot_info;
    uint32_t total_size;
    uint64_t offset;
    int found_map = 0;

    for (uint64_t i = 0u; i < BITMAP_SIZE; ++i) page_bitmap[i] = 0xffu;
    memory_stats.free_pages = 0u;
    memory_stats.total_pages = PAGE_COUNT;
    memory_stats.used_pages = PAGE_COUNT;

    if (info == NULL || multiboot_info >= DUCKOS_MAX_PHYSICAL_ADDRESS)
        return 0;
    total_size = *(const uint32_t *)info;
    if (total_size < 16u || total_size > 0x100000u ||
        multiboot_info + total_size > DUCKOS_MAX_PHYSICAL_ADDRESS)
        return 0;

    offset = 8u;
    while (offset + sizeof(MultibootTag) <= total_size) {
        const MultibootTag *tag = (const MultibootTag *)(info + offset);
        if (tag->size < sizeof(MultibootTag) || offset + tag->size > total_size)
            return 0;
        if (tag->type == 0u) break;
        if (tag->type == 6u && tag->size >= sizeof(MultibootMemoryMapTag)) {
            const MultibootMemoryMapTag *map =
                (const MultibootMemoryMapTag *)tag;
            if (map->entry_size < sizeof(MultibootMemoryMapEntry) ||
                map->entry_size == 0u) return 0;
            uint64_t entry_offset = sizeof(MultibootMemoryMapTag);
            while (entry_offset + map->entry_size <= tag->size) {
                const MultibootMemoryMapEntry *entry =
                    (const MultibootMemoryMapEntry *)((const uint8_t *)map + entry_offset);
                if (entry->type == 1u)
                    release_usable_range(entry->address, entry->length);
                entry_offset += map->entry_size;
            }
            found_map = 1;
        } else if (tag->type == 3u && tag->size >= sizeof(MultibootModuleTag)) {
            const MultibootModuleTag *module = (const MultibootModuleTag *)tag;
            reserve_range(module->module_start, module->module_end);
        }
        offset = (offset + tag->size + 7u) & ~UINT64_C(7);
    }
    if (!found_map) return 0;

    reserve_range(0u, 0x100000u);
    reserve_range((uint64_t)(uintptr_t)__kernel_start,
                  (uint64_t)(uintptr_t)__kernel_end);
    reserve_range(multiboot_info, multiboot_info + total_size);
    return memory_stats.free_pages != 0u;
}

void *duckos_alloc_page(void) {
    duckos_cli();
    for (uint64_t page = 256u; page < PAGE_COUNT; ++page) {
        if (!page_is_used(page)) {
            page_set_used(page);
            memory_stats.free_pages--;
            memory_stats.used_pages++;
            duckos_sti();
            uint8_t *address = (uint8_t *)(uintptr_t)(page * DUCKOS_PAGE_SIZE);
            for (uint32_t i = 0u; i < DUCKOS_PAGE_SIZE; ++i) address[i] = 0u;
            return address;
        }
    }
    duckos_sti();
    return NULL;
}

void duckos_free_page(void *address) {
    uint64_t physical = (uint64_t)(uintptr_t)address;
    if ((physical & (DUCKOS_PAGE_SIZE - 1u)) != 0u ||
        physical < 0x100000u || physical >= DUCKOS_MAX_PHYSICAL_ADDRESS)
        return;
    uint64_t page = physical / DUCKOS_PAGE_SIZE;
    duckos_cli();
    if (page_is_used(page)) {
        page_set_free(page);
        memory_stats.free_pages++;
        memory_stats.used_pages--;
    }
    duckos_sti();
}

static uint64_t *allocate_table(void) {
    return (uint64_t *)duckos_alloc_page();
}

static int split_large_page(uint64_t *directory_entry) {
    uint64_t old = *directory_entry;
    uint64_t *table = allocate_table();
    if (table == NULL) return 0;
    uint64_t base = old & UINT64_C(0x000fffffffe00000);
    uint64_t flags = old & (UINT64_C(0xfff) | PAGE_NX);
    flags &= ~PAGE_LARGE;
    for (uint64_t i = 0u; i < 512u; ++i)
        table[i] = (base + i * DUCKOS_PAGE_SIZE) | flags;
    *directory_entry = ((uint64_t)(uintptr_t)table & PAGE_ADDRESS_MASK) |
                       PAGE_PRESENT | PAGE_WRITE |
                       ((old & PAGE_USER) != 0u ? PAGE_USER : 0u);
    return 1;
}

static uint64_t *next_level(uint64_t *parent, uint16_t index, int user,
                            int split_large) {
    uint64_t *entry = &parent[index];
    if ((*entry & PAGE_PRESENT) == 0u) {
        uint64_t *table = allocate_table();
        if (table == NULL) return NULL;
        *entry = ((uint64_t)(uintptr_t)table & PAGE_ADDRESS_MASK) |
                 PAGE_PRESENT | PAGE_WRITE | (user ? PAGE_USER : 0u);
        return table;
    }
    if (user) *entry |= PAGE_USER;
    if (split_large && (*entry & PAGE_LARGE) != 0u) {
        if (!split_large_page(entry)) return NULL;
    }
    return (uint64_t *)(uintptr_t)(*entry & PAGE_ADDRESS_MASK);
}

int duckos_vm_map_page(uint64_t virtual_address, uint64_t physical_address,
                       uint32_t flags) {
    if ((virtual_address & (DUCKOS_PAGE_SIZE - 1u)) != 0u ||
        (physical_address & (DUCKOS_PAGE_SIZE - 1u)) != 0u ||
        (flags & ~(DUCKOS_VM_WRITE | DUCKOS_VM_USER | DUCKOS_VM_EXEC)) != 0u)
        return 0;

    int user = (flags & DUCKOS_VM_USER) != 0u;
    uint16_t pml4_index = (uint16_t)((virtual_address >> 39u) & 0x1ffu);
    uint16_t pdpt_index = (uint16_t)((virtual_address >> 30u) & 0x1ffu);
    uint16_t pd_index = (uint16_t)((virtual_address >> 21u) & 0x1ffu);
    uint16_t pt_index = (uint16_t)((virtual_address >> 12u) & 0x1ffu);

    uint64_t *pdpt = next_level(boot_pml4, pml4_index, user, 0);
    if (pdpt == NULL) return 0;
    uint64_t *pd = next_level(pdpt, pdpt_index, user, 0);
    if (pd == NULL) return 0;
    uint64_t *pt = next_level(pd, pd_index, user, 1);
    if (pt == NULL) return 0;
    if ((pt[pt_index] & PAGE_PRESENT) != 0u) return 0;

    uint64_t entry = (physical_address & PAGE_ADDRESS_MASK) | PAGE_PRESENT;
    if ((flags & DUCKOS_VM_WRITE) != 0u) entry |= PAGE_WRITE;
    if (user) entry |= PAGE_USER;
    if ((flags & DUCKOS_VM_EXEC) == 0u) entry |= PAGE_NX;
    pt[pt_index] = entry;
    duckos_invlpg(virtual_address);
    return 1;
}

int duckos_vm_unmap_page(uint64_t virtual_address) {
    if ((virtual_address & (DUCKOS_PAGE_SIZE - 1u)) != 0u) return 0;
    uint16_t pml4_index = (uint16_t)((virtual_address >> 39u) & 0x1ffu);
    uint16_t pdpt_index = (uint16_t)((virtual_address >> 30u) & 0x1ffu);
    uint16_t pd_index = (uint16_t)((virtual_address >> 21u) & 0x1ffu);
    uint16_t pt_index = (uint16_t)((virtual_address >> 12u) & 0x1ffu);
    if ((boot_pml4[pml4_index] & PAGE_PRESENT) == 0u) return 0;
    uint64_t *pdpt = (uint64_t *)(uintptr_t)(boot_pml4[pml4_index] & PAGE_ADDRESS_MASK);
    if ((pdpt[pdpt_index] & PAGE_PRESENT) == 0u) return 0;
    uint64_t *pd = (uint64_t *)(uintptr_t)(pdpt[pdpt_index] & PAGE_ADDRESS_MASK);
    if ((pd[pd_index] & PAGE_PRESENT) == 0u) return 0;
    if ((pd[pd_index] & PAGE_LARGE) != 0u &&
        !split_large_page(&pd[pd_index])) return 0;
    uint64_t *pt = (uint64_t *)(uintptr_t)(pd[pd_index] & PAGE_ADDRESS_MASK);
    if ((pt[pt_index] & PAGE_PRESENT) == 0u) return 0;
    pt[pt_index] = 0u;
    duckos_invlpg(virtual_address);
    return 1;
}

int duckos_vm_create_address_space(uint64_t *root_physical) {
    if (root_physical == NULL) return 0;
    uint64_t *root = allocate_table();
    uint64_t *pdpt = allocate_table();
    if (root == NULL || pdpt == NULL) {
        if (root != NULL) duckos_free_page(root);
        if (pdpt != NULL) duckos_free_page(pdpt);
        return 0;
    }
    root[0] = ((uint64_t)(uintptr_t)pdpt & PAGE_ADDRESS_MASK) |
              PAGE_PRESENT | PAGE_WRITE | PAGE_USER;
    pdpt[0] = boot_pdpt[0];
    *root_physical = (uint64_t)(uintptr_t)root;
    return 1;
}

void duckos_vm_switch(uint64_t root_physical) {
    if ((root_physical & (DUCKOS_PAGE_SIZE - 1u)) == 0u)
        duckos_write_cr3(root_physical);
}

DuckOsMemoryStats duckos_memory_stats(void) {
    return memory_stats;
}
