#include "paging.h"

#include <stddef.h>
#include <stdint.h>

typedef struct duckos_x86_paging_context {
    duckos_frame_allocator *frames;
    uint64_t hhdm_offset;
} duckos_x86_paging_context;

static duckos_x86_paging_context active_context;
static int nx_enabled;

static uint64_t allocate_frame(void *opaque) {
    duckos_x86_paging_context *context = (duckos_x86_paging_context *)opaque;
    uint64_t physical_address = 0u;
    if (context == NULL || context->frames == NULL ||
        duckos_frame_allocator_allocate(context->frames, &physical_address) !=
            DUCKOS_FRAME_ALLOCATOR_OK) {
        return 0u;
    }
    return physical_address;
}

static void release_frame(void *opaque, uint64_t physical_address) {
    duckos_x86_paging_context *context = (duckos_x86_paging_context *)opaque;
    if (context == NULL || context->frames == NULL) return;
    (void)duckos_frame_allocator_release(context->frames, physical_address);
}

static uint64_t *map_physical_page(void *opaque, uint64_t physical_address) {
    duckos_x86_paging_context *context = (duckos_x86_paging_context *)opaque;
    if (context == NULL || physical_address > (uint64_t)UINTPTR_MAX ||
        context->hhdm_offset > (uint64_t)UINTPTR_MAX - physical_address) {
        return NULL;
    }
    return (uint64_t *)(uintptr_t)(context->hhdm_offset + physical_address);
}

static void invalidate_page(void *opaque, uint64_t virtual_address) {
    (void)opaque;
    __asm__ volatile ("invlpg (%0)" : : "r"((uintptr_t)virtual_address) : "memory");
}

static void cpuid(uint32_t leaf, uint32_t *a, uint32_t *b,
                  uint32_t *c, uint32_t *d) {
    uint32_t out_a;
    uint32_t out_b;
    uint32_t out_c;
    uint32_t out_d;
    __asm__ volatile (
        "cpuid"
        : "=a"(out_a), "=b"(out_b), "=c"(out_c), "=d"(out_d)
        : "a"(leaf), "c"(0u)
    );
    if (a != NULL) *a = out_a;
    if (b != NULL) *b = out_b;
    if (c != NULL) *c = out_c;
    if (d != NULL) *d = out_d;
}

static uint8_t physical_address_bits(void) {
    uint32_t maximum = 0u;
    cpuid(0x80000000u, &maximum, NULL, NULL, NULL);
    if (maximum >= 0x80000008u) {
        uint32_t bits = 0u;
        cpuid(0x80000008u, &bits, NULL, NULL, NULL);
        const uint8_t width = (uint8_t)(bits & 0xffu);
        if (width >= 32u && width <= 52u) return width;
    }
    return 36u;
}

static int enable_nx(void) {
    uint32_t maximum = 0u;
    uint32_t features = 0u;
    cpuid(0x80000000u, &maximum, NULL, NULL, NULL);
    if (maximum < 0x80000001u) return 0;

    cpuid(0x80000001u, NULL, NULL, NULL, &features);
    if ((features & (1u << 20u)) == 0u) return 0;

    uint32_t low = 0u;
    uint32_t high = 0u;
    __asm__ volatile (
        "rdmsr"
        : "=a"(low), "=d"(high)
        : "c"(0xc0000080u)
    );
    uint64_t efer = ((uint64_t)high << 32u) | low;
    efer |= UINT64_C(1) << 11u;
    __asm__ volatile (
        "wrmsr"
        :
        : "c"(0xc0000080u),
          "a"((uint32_t)efer),
          "d"((uint32_t)(efer >> 32u))
        : "memory"
    );
    return 1;
}

uint64_t duckos_x86_paging_read_cr3(void) {
    uint64_t value;
    __asm__ volatile ("mov %%cr3, %0" : "=r"(value));
    return value;
}

int duckos_x86_paging_nx_enabled(void) {
    return nx_enabled;
}

int duckos_x86_paging_takeover(
    duckos_page_table_space *space,
    duckos_frame_allocator *frames,
    uint64_t hhdm_offset
) {
    uint64_t cr4 = 0u;
    __asm__ volatile ("mov %%cr4, %0" : "=r"(cr4));
    if ((cr4 & (UINT64_C(1) << 12u)) != 0u) return 0; /* Five-level paging is not enabled yet. */
    if (space == NULL || frames == NULL ||
        hhdm_offset > (uint64_t)UINTPTR_MAX) {
        return 0;
    }

    active_context.frames = frames;
    active_context.hhdm_offset = hhdm_offset;

    const duckos_page_table_ops ops = {
        .context = &active_context,
        .allocate_page = allocate_frame,
        .release_page = release_frame,
        .map_page = map_physical_page,
        .invalidate_page = invalidate_page
    };

    nx_enabled = enable_nx();
    const uint8_t physical_bits = physical_address_bits();
    const uint64_t physical_mask =
        ((UINT64_C(1) << physical_bits) - 1u) & ~UINT64_C(0xfff);
    const uint64_t source_root = duckos_x86_paging_read_cr3() & physical_mask;

    if (duckos_page_table_clone(
            space, source_root, physical_bits, nx_enabled, &ops
        ) != DUCKOS_PAGE_TABLE_OK) {
        return 0;
    }

    uint64_t cr0 = 0u;
    __asm__ volatile ("mov %%cr0, %0" : "=r"(cr0));
    cr0 |= UINT64_C(1) << 16u; /* CR0.WP: supervisor writes honor read-only mappings. */
    __asm__ volatile ("mov %0, %%cr0" : : "r"(cr0) : "memory");

    const uint64_t new_cr3 = space->root_physical;
    __asm__ volatile ("mov %0, %%cr3" : : "r"(new_cr3) : "memory");
    space->active = 1u;
    return duckos_x86_paging_read_cr3() == new_cr3;
}

int duckos_x86_paging_protect_range(
    duckos_page_table_space *space,
    uint64_t start,
    uint64_t end,
    uint64_t flags
) {
    if (space == NULL || start > end ||
        (start & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u)) != 0u ||
        (end & (DUCKOS_PAGE_TABLE_PAGE_SIZE - 1u)) != 0u) {
        return 0;
    }
    if (start == end) return 1;

    for (uint64_t address = start; address < end;
         address += DUCKOS_PAGE_TABLE_PAGE_SIZE) {
        if (duckos_page_table_protect(space, address, flags) != DUCKOS_PAGE_TABLE_OK) {
            return 0;
        }
        if (address > UINT64_MAX - DUCKOS_PAGE_TABLE_PAGE_SIZE) return 0;
    }
    return 1;
}
