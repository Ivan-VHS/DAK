#include "virtual_memory.h"

#include <stddef.h>
#include <stdint.h>

extern unsigned char __kernel_start[];
extern unsigned char __limine_requests_start[];
extern unsigned char __limine_requests_end[];
extern unsigned char __kernel_text_start[];
extern unsigned char __kernel_text_end[];
extern unsigned char __kernel_rodata_start[];
extern unsigned char __kernel_rodata_end[];
extern unsigned char __kernel_data_start[];
extern unsigned char __kernel_data_end[];
extern unsigned char __kernel_bss_start[];
extern unsigned char __kernel_bss_end[];

static int align_up_page(uint64_t value, uint64_t *aligned) {
    const uint64_t mask = (uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u;
    if (aligned == NULL || value > UINT64_MAX - mask) return 0;
    *aligned = (value + mask) & ~mask;
    return 1;
}

static int add_address(uint64_t base, uint64_t length, uint64_t *end) {
    if (end == NULL || base > UINT64_MAX - length) return 0;
    *end = base + length;
    return 1;
}

static int map_page_or_confirm(
    duckos_x86_page_table *tables,
    uint64_t virtual_address,
    uint64_t physical_address,
    uint64_t flags
) {
    const duckos_x86_page_table_status status = duckos_x86_page_table_map_4k(
        tables, virtual_address, physical_address, flags
    );
    if (status == DUCKOS_X86_PAGE_TABLE_OK) return 1;
    if (status != DUCKOS_X86_PAGE_TABLE_ALREADY_MAPPED) return 0;

    uint64_t existing;
    return duckos_x86_page_table_translate(
        tables, virtual_address, &existing, NULL
    ) == DUCKOS_X86_PAGE_TABLE_OK && existing == physical_address;
}

static int map_hhdm_memory_region(
    duckos_x86_page_table *tables,
    uint64_t hhdm_offset,
    const duckos_memory_region *region
) {
    uint64_t region_end;
    uint64_t begin;
    uint64_t end;
    if (region == NULL || region->type == (uint32_t)DUCKOS_MEMORY_BAD ||
        region->type == (uint32_t)DUCKOS_MEMORY_MMIO) return 1;
    if (!add_address(region->base, region->length, &region_end) ||
        !align_up_page(region->base, &begin)) return 0;
    end = region_end & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u);

    while (begin < end) {
        uint64_t virtual_address;
        if (!add_address(hhdm_offset, begin, &virtual_address)) return 0;
        const uint64_t remaining = end - begin;
        if ((begin & (DUCKOS_X86_LARGE_PAGE_SIZE - 1u)) == 0u &&
            (virtual_address & (DUCKOS_X86_LARGE_PAGE_SIZE - 1u)) == 0u &&
            remaining >= DUCKOS_X86_LARGE_PAGE_SIZE) {
            const duckos_x86_page_table_status status =
                duckos_x86_page_table_map_2m(
                    tables, virtual_address, begin,
                    DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE
                );
            if (status != DUCKOS_X86_PAGE_TABLE_OK) return 0;
            begin += DUCKOS_X86_LARGE_PAGE_SIZE;
        } else {
            const duckos_x86_page_table_status status =
                duckos_x86_page_table_map_4k(
                    tables, virtual_address, begin,
                    DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE
                );
            if (status != DUCKOS_X86_PAGE_TABLE_OK) return 0;
            begin += DUCKOS_FRAME_PAGE_SIZE;
        }
    }
    return 1;
}

static int map_kernel_section(
    duckos_x86_page_table *tables,
    uint64_t kernel_phys_base,
    const unsigned char *section_start,
    const unsigned char *section_end,
    uint64_t flags
) {
    uint64_t begin = (uint64_t)(uintptr_t)section_start;
    uint64_t end = (uint64_t)(uintptr_t)section_end;
    const uint64_t kernel_virtual = (uint64_t)(uintptr_t)__kernel_start;
    if (end < begin || begin < kernel_virtual) return 0;
    begin &= ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u);
    if (!align_up_page(end, &end)) return 0;

    for (uint64_t address = begin; address < end; address += DUCKOS_FRAME_PAGE_SIZE) {
        uint64_t physical;
        if (!add_address(kernel_phys_base, address - kernel_virtual, &physical)) return 0;
        const duckos_x86_page_table_status status =
            duckos_x86_page_table_map_4k(tables, address, physical, flags);
        if (status != DUCKOS_X86_PAGE_TABLE_OK) return 0;
    }
    return 1;
}

static int protect_kernel_hhdm_alias(
    duckos_x86_page_table *tables,
    uint64_t hhdm_offset,
    uint64_t kernel_phys_base,
    const unsigned char *section_start,
    const unsigned char *section_end,
    uint64_t flags
) {
    uint64_t begin = (uint64_t)(uintptr_t)section_start;
    uint64_t end = (uint64_t)(uintptr_t)section_end;
    const uint64_t kernel_virtual = (uint64_t)(uintptr_t)__kernel_start;
    if (end < begin || begin < kernel_virtual) return 0;
    begin &= ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u);
    if (!align_up_page(end, &end)) return 0;

    for (uint64_t address = begin; address < end; address += DUCKOS_FRAME_PAGE_SIZE) {
        uint64_t physical;
        uint64_t direct_address;
        if (!add_address(kernel_phys_base, address - kernel_virtual, &physical) ||
            !add_address(hhdm_offset, physical, &direct_address) ||
            duckos_x86_page_table_protect_4k(tables, direct_address, flags) !=
                DUCKOS_X86_PAGE_TABLE_OK) return 0;
    }
    return 1;
}

static int preserve_boot_stack_and_gdt(
    duckos_x86_page_table *tables,
    uint64_t old_root_phys,
    uint64_t hhdm_offset
) {
    duckos_x86_page_table old_tables = {0};
    old_tables.hhdm_offset = hhdm_offset;
    old_tables.root_phys = old_root_phys;

    uint64_t stack_pointer;
    __asm__ volatile ("mov %%rsp, %0" : "=r"(stack_pointer));
    if (stack_pointer > UINT64_MAX - DUCKOS_FRAME_PAGE_SIZE) return 0;
    const uint64_t stack_page =
        stack_pointer & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u);
    const uint64_t stack_end = stack_page + DUCKOS_FRAME_PAGE_SIZE;

    int current_stack_page_mapped = 0;
    for (uint64_t offset = 0u; offset < 0x40000u; offset += DUCKOS_FRAME_PAGE_SIZE) {
        if (stack_page < offset) break;
        const uint64_t address = stack_page - offset;
        uint64_t physical;
        if (duckos_x86_page_table_translate(
                &old_tables, address, &physical, NULL
            ) != DUCKOS_X86_PAGE_TABLE_OK) {
            if (offset == 0u) return 0;
            break;
        }
        if (!map_page_or_confirm(
                tables, address, physical & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u),
                DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE
            )) return 0;
        current_stack_page_mapped = 1;
    }
    if (!current_stack_page_mapped) return 0;

    for (uint64_t address = stack_page + DUCKOS_FRAME_PAGE_SIZE;
         address < stack_end + DUCKOS_FRAME_PAGE_SIZE;
         address += DUCKOS_FRAME_PAGE_SIZE) {
        uint64_t physical;
        if (duckos_x86_page_table_translate(
                &old_tables, address, &physical, NULL
            ) != DUCKOS_X86_PAGE_TABLE_OK ||
            !map_page_or_confirm(
                tables, address, physical & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u),
                DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE
            )) return 0;
    }

    struct __attribute__((packed)) descriptor_table_register {
        uint16_t limit;
        uint64_t base;
    } gdtr;
    __asm__ volatile ("sgdt %0" : "=m"(gdtr));
    uint64_t gdt_end;
    if (!add_address(gdtr.base, (uint64_t)gdtr.limit + 1u, &gdt_end)) return 0;
    const uint64_t gdt_begin_page =
        gdtr.base & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u);
    if (!align_up_page(gdt_end, &gdt_end)) return 0;
    for (uint64_t address = gdt_begin_page; address < gdt_end;
         address += DUCKOS_FRAME_PAGE_SIZE) {
        uint64_t physical;
        if (duckos_x86_page_table_translate(
                &old_tables, address, &physical, NULL
            ) != DUCKOS_X86_PAGE_TABLE_OK ||
            !map_page_or_confirm(
                tables, address, physical & ~((uint64_t)DUCKOS_FRAME_PAGE_SIZE - 1u),
                DUCKOS_X86_PTE_NO_EXECUTE
            ) ||
            duckos_x86_page_table_protect_4k(
                tables, address, DUCKOS_X86_PTE_NO_EXECUTE
            ) != DUCKOS_X86_PAGE_TABLE_OK) return 0;
    }
    return 1;
}

static int enable_nx_and_write_protect(void) {
    uint32_t eax;
    uint32_t ebx;
    uint32_t ecx;
    uint32_t edx;
    __asm__ volatile ("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
        : "a"(0x80000000u), "c"(0u));
    if (eax < 0x80000001u) return 0;
    __asm__ volatile ("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx)
        : "a"(0x80000001u), "c"(0u));
    if ((edx & (1u << 20u)) == 0u) return 0;

    uint32_t efer_low;
    uint32_t efer_high;
    __asm__ volatile ("rdmsr" : "=a"(efer_low), "=d"(efer_high) : "c"(0xc0000080u));
    efer_low |= (1u << 11u);
    __asm__ volatile ("wrmsr" : : "a"(efer_low), "d"(efer_high), "c"(0xc0000080u));

    uint64_t cr0;
    __asm__ volatile ("mov %%cr0, %0" : "=r"(cr0));
    cr0 |= (1ull << 16u);
    __asm__ volatile ("mov %0, %%cr0" : : "r"(cr0) : "memory");
    return 1;
}

static void activate_page_table(uint64_t root_phys) {
    uint64_t cr4;
    __asm__ volatile ("mov %0, %%cr3" : : "r"(root_phys) : "memory");
    __asm__ volatile ("mov %%cr4, %0" : "=r"(cr4));
    if ((cr4 & (1ull << 7u)) != 0u) {
        const uint64_t without_pge = cr4 & ~(1ull << 7u);
        __asm__ volatile ("mov %0, %%cr4" : : "r"(without_pge) : "memory");
        __asm__ volatile ("mov %0, %%cr4" : : "r"(cr4) : "memory");
    }
}

int duckos_x86_virtual_memory_init(
    duckos_frame_allocator *allocator,
    duckos_x86_page_table *page_tables,
    const duckos_boot_info_v1 *boot_info,
    const duckos_memory_region *memory_regions,
    uint64_t hhdm_offset
) {
    if (allocator == NULL || page_tables == NULL || boot_info == NULL ||
        memory_regions == NULL || (hhdm_offset & 0xfffu) != 0u) return 0;

    uint64_t cr4;
    __asm__ volatile ("mov %%cr4, %0" : "=r"(cr4));
    if ((cr4 & (1ull << 12u)) != 0u) return 0;

    uint64_t old_cr3;
    __asm__ volatile ("mov %%cr3, %0" : "=r"(old_cr3));
    old_cr3 &= DUCKOS_X86_PTE_ADDRESS_MASK;

    if (duckos_x86_page_table_init(page_tables, allocator, hhdm_offset) !=
        DUCKOS_X86_PAGE_TABLE_OK) return 0;

    for (uint32_t index = 0u; index < boot_info->memory_region_count; ++index) {
        if (!map_hhdm_memory_region(page_tables, hhdm_offset, &memory_regions[index])) {
            return 0;
        }
    }

    if (!map_kernel_section(
            page_tables, boot_info->kernel_phys_base,
            __limine_requests_start, __limine_requests_end,
            DUCKOS_X86_PTE_NO_EXECUTE
        ) ||
        !map_kernel_section(
            page_tables, boot_info->kernel_phys_base,
            __kernel_text_start, __kernel_text_end, 0u
        ) ||
        !map_kernel_section(
            page_tables, boot_info->kernel_phys_base,
            __kernel_rodata_start, __kernel_rodata_end,
            DUCKOS_X86_PTE_NO_EXECUTE
        ) ||
        !map_kernel_section(
            page_tables, boot_info->kernel_phys_base,
            __kernel_data_start, __kernel_data_end,
            DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE
        ) ||
        !map_kernel_section(
            page_tables, boot_info->kernel_phys_base,
            __kernel_bss_start, __kernel_bss_end,
            DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE
        )) return 0;

    if (!protect_kernel_hhdm_alias(
            page_tables, hhdm_offset, boot_info->kernel_phys_base,
            __limine_requests_start, __limine_requests_end,
            DUCKOS_X86_PTE_NO_EXECUTE
        ) ||
        !protect_kernel_hhdm_alias(
            page_tables, hhdm_offset, boot_info->kernel_phys_base,
            __kernel_text_start, __kernel_text_end, 0u
        ) ||
        !protect_kernel_hhdm_alias(
            page_tables, hhdm_offset, boot_info->kernel_phys_base,
            __kernel_rodata_start, __kernel_rodata_end,
            DUCKOS_X86_PTE_NO_EXECUTE
        ) ||
        !protect_kernel_hhdm_alias(
            page_tables, hhdm_offset, boot_info->kernel_phys_base,
            __kernel_data_start, __kernel_data_end,
            DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE
        ) ||
        !protect_kernel_hhdm_alias(
            page_tables, hhdm_offset, boot_info->kernel_phys_base,
            __kernel_bss_start, __kernel_bss_end,
            DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE
        )) return 0;

    if (boot_info->framebuffer_size != 0u) {
        uint64_t framebuffer_end;
        if (!add_address(boot_info->framebuffer_phys_base,
                         boot_info->framebuffer_size, &framebuffer_end)) return 0;
        const uint64_t begin = boot_info->framebuffer_phys_base & ~0xfffull;
        if (!align_up_page(framebuffer_end, &framebuffer_end)) return 0;
        for (uint64_t physical = begin; physical < framebuffer_end; physical += 0x1000u) {
            uint64_t virtual_address;
            if (!add_address(hhdm_offset, physical, &virtual_address) ||
                duckos_x86_page_table_map_4k(
                    page_tables, virtual_address, physical,
                    DUCKOS_X86_PTE_WRITABLE | DUCKOS_X86_PTE_NO_EXECUTE |
                    DUCKOS_X86_PTE_WRITE_THROUGH | DUCKOS_X86_PTE_CACHE_DISABLE
                ) != DUCKOS_X86_PAGE_TABLE_OK) return 0;
        }
    }

    if (!preserve_boot_stack_and_gdt(page_tables, old_cr3, hhdm_offset) ||
        !enable_nx_and_write_protect()) return 0;

    activate_page_table(page_tables->root_phys);
    return 1;
}
