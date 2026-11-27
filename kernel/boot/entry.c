#include <stddef.h>
#include <stdint.h>

#include "boot_info.h"
#include "idt.h"
#include "frame_allocator.h"
#include "limine.h"
#include "interrupts.h"
#include "gdt.h"
#include "rule_epoch.h"
#include "predictive_guard.h"
#include "app_sector.h"

#define SERIAL_PORT 0x3f8u
#define MAX_BOOT_REGIONS DUCKOS_BOOT_MAX_MEMORY_REGIONS

extern unsigned char __kernel_start[];
extern unsigned char __kernel_end[];

__attribute__((used, section(".limine_requests_start"), aligned(8)))
static volatile uint64_t requests_start[4] = LIMINE_REQUESTS_START_MARKER;

__attribute__((used, section(".limine_requests"), aligned(8)))
static volatile uint64_t base_revision[3] = LIMINE_BASE_REVISION(6);

__attribute__((used, section(".limine_requests"), aligned(8)))
static volatile struct limine_bootloader_info_request bootloader_request = {
    .id = LIMINE_BOOTLOADER_INFO_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests"), aligned(8)))
static volatile struct limine_firmware_type_request firmware_request = {
    .id = LIMINE_FIRMWARE_TYPE_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests"), aligned(8)))
static volatile struct limine_hhdm_request hhdm_request = {
    .id = LIMINE_HHDM_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests"), aligned(8)))
static volatile struct limine_framebuffer_request framebuffer_request = {
    .id = LIMINE_FRAMEBUFFER_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests"), aligned(8)))
static volatile struct limine_memmap_request memory_map_request = {
    .id = LIMINE_MEMMAP_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests"), aligned(8)))
static volatile struct limine_executable_address_request executable_address_request = {
    .id = LIMINE_EXECUTABLE_ADDRESS_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests"), aligned(8)))
static volatile struct limine_stack_size_request stack_size_request = {
    .id = LIMINE_STACK_SIZE_REQUEST_ID,
    .revision = 0,
    .stack_size = 0x40000
};

__attribute__((used, section(".limine_requests_end"), aligned(8)))
static volatile uint64_t requests_end[2] = LIMINE_REQUESTS_END_MARKER;

static duckos_memory_region boot_regions[MAX_BOOT_REGIONS];
static struct limine_framebuffer *active_framebuffer;
static duckos_frame_allocator early_frame_allocator;
static dak_rule_registry active_rule_models;
static dak_predictor install_predictor;
static uint64_t first_frame_phys;

static inline void port_out8(uint16_t port, uint8_t value) {
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}

static inline uint8_t port_in8(uint16_t port) {
    uint8_t value;
    __asm__ volatile ("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}

static void serial_init(void) {
    port_out8((uint16_t)(SERIAL_PORT + 1u), 0x00u);
    port_out8((uint16_t)(SERIAL_PORT + 3u), 0x80u);
    port_out8((uint16_t)(SERIAL_PORT + 0u), 0x01u);
    port_out8((uint16_t)(SERIAL_PORT + 1u), 0x00u);
    port_out8((uint16_t)(SERIAL_PORT + 3u), 0x03u);
    port_out8((uint16_t)(SERIAL_PORT + 2u), 0xc7u);
    port_out8((uint16_t)(SERIAL_PORT + 4u), 0x0bu);
}

static void serial_putc(char value) {
    for (uint32_t spin = 0u; spin < 1000000u; ++spin) {
        if ((port_in8((uint16_t)(SERIAL_PORT + 5u)) & 0x20u) != 0u) {
            port_out8((uint16_t)SERIAL_PORT, (uint8_t)value);
            return;
        }
    }
}

static void serial_write(const char *text) {
    if (text == NULL) return;
    while (*text != '\0') {
        if (*text == '\n') serial_putc('\r');
        serial_putc(*text++);
    }
}

static void serial_hex(uint64_t value) {
    static const char digits[] = "0123456789abcdef";
    serial_write("0x");
    for (int shift = 60; shift >= 0; shift -= 4) {
        serial_putc(digits[(value >> (uint32_t)shift) & 0x0fu]);
    }
}

static void serial_decimal(uint64_t value) {
    char buffer[21];
    size_t length = 0u;
    do {
        buffer[length++] = (char)('0' + (value % 10u));
        value /= 10u;
    } while (value != 0u && length < sizeof(buffer));
    while (length != 0u) serial_putc(buffer[--length]);
}

static void halt_forever(void) __attribute__((noreturn));
static void halt_forever(void) {
    for (;;) __asm__ volatile ("cli; hlt");
}

static uint32_t channel_bits(uint8_t channel, uint8_t width, uint8_t shift) {
    if (width == 0u || width > 8u || shift >= 32u ||
        (uint32_t)width + (uint32_t)shift > 32u) {
        return 0u;
    }
    const uint32_t maximum = (1u << width) - 1u;
    const uint32_t scaled = ((uint32_t)channel * maximum + 127u) / 255u;
    return scaled << shift;
}

static uint32_t pack_rgb(
    const struct limine_framebuffer *fb,
    uint8_t red,
    uint8_t green,
    uint8_t blue
) {
    return channel_bits(red, fb->red_mask_size, fb->red_mask_shift) |
        channel_bits(green, fb->green_mask_size, fb->green_mask_shift) |
        channel_bits(blue, fb->blue_mask_size, fb->blue_mask_shift);
}

static void draw_pixel(uint64_t x, uint64_t y, uint8_t r, uint8_t g, uint8_t b) {
    struct limine_framebuffer *fb = active_framebuffer;
    if (fb == NULL || fb->bpp != 32u || x >= fb->width || y >= fb->height) return;
    const uint64_t offset = y * fb->pitch + x * 4u;
    volatile uint32_t *pixel =
        (volatile uint32_t *)((volatile uint8_t *)fb->address + offset);
    *pixel = pack_rgb(fb, r, g, b);
}

static void draw_rect(
    uint64_t x,
    uint64_t y,
    uint64_t width,
    uint64_t height,
    uint8_t r,
    uint8_t g,
    uint8_t b
) {
    struct limine_framebuffer *fb = active_framebuffer;
    if (fb == NULL || x >= fb->width || y >= fb->height) return;
    if (width > fb->width - x) width = fb->width - x;
    if (height > fb->height - y) height = fb->height - y;

    for (uint64_t row = 0u; row < height; ++row) {
        for (uint64_t column = 0u; column < width; ++column) {
            draw_pixel(x + column, y + row, r, g, b);
        }
    }
}

static uint8_t glyph_row(char value, uint8_t row) {
    static const uint8_t alphabet[26][7] = {
        {14,17,17,31,17,17,17}, {30,17,17,30,17,17,30},
        {14,17,16,16,16,17,14}, {30,17,17,17,17,17,30},
        {31,16,16,30,16,16,31}, {31,16,16,30,16,16,16},
        {14,17,16,23,17,17,15}, {17,17,17,31,17,17,17},
        {14,4,4,4,4,4,14}, {7,2,2,2,18,18,12},
        {17,18,20,24,20,18,17}, {16,16,16,16,16,16,31},
        {17,27,21,21,17,17,17}, {17,25,21,19,17,17,17},
        {14,17,17,17,17,17,14}, {30,17,17,30,16,16,16},
        {14,17,17,17,21,18,13}, {30,17,17,30,20,18,17},
        {15,16,16,14,1,1,30}, {31,4,4,4,4,4,4},
        {17,17,17,17,17,17,14}, {17,17,17,17,17,10,4},
        {17,17,17,21,21,21,10}, {17,17,10,4,10,17,17},
        {17,17,10,4,4,4,4}, {31,1,2,4,8,16,31}
    };
    static const uint8_t zero[7] = {14,17,19,21,25,17,14};
    if (value >= 'a' && value <= 'z') value = (char)(value - 'a' + 'A');
    if (value >= 'A' && value <= 'Z') return alphabet[(uint8_t)value - (uint8_t)'A'][row];
    if (value == '0') return zero[row];
    return 0u;
}

static void draw_text(
    uint64_t x,
    uint64_t y,
    const char *text,
    uint64_t scale,
    uint8_t r,
    uint8_t g,
    uint8_t b
) {
    if (text == NULL || scale == 0u) return;
    while (*text != '\0') {
        for (uint8_t row = 0u; row < 7u; ++row) {
            const uint8_t bits = glyph_row(*text, row);
            for (uint8_t column = 0u; column < 5u; ++column) {
                if ((bits & (uint8_t)(1u << (4u - column))) == 0u) continue;
                draw_rect(
                    x + (uint64_t)column * scale,
                    y + (uint64_t)row * scale,
                    scale,
                    scale,
                    r, g, b
                );
            }
        }
        x += 6u * scale;
        ++text;
    }
}

static void draw_centered(
    uint64_t y,
    const char *text,
    uint64_t scale,
    uint8_t r,
    uint8_t g,
    uint8_t b
) {
    if (active_framebuffer == NULL || text == NULL) return;
    size_t length = 0u;
    while (text[length] != '\0') ++length;
    const uint64_t width = (uint64_t)length * 6u * scale;
    const uint64_t x = active_framebuffer->width > width ?
        (active_framebuffer->width - width) / 2u : 8u;
    draw_text(x, y, text, scale, r, g, b);
}

static void draw_boot_screen(void) {
    struct limine_framebuffer *fb = active_framebuffer;
    if (fb == NULL || fb->bpp != 32u) return;

    draw_rect(0u, 0u, fb->width, fb->height, 7u, 7u, 7u);
    draw_rect(0u, 0u, fb->width, 92u, 255u, 212u, 0u);
    draw_text(28u, 29u, "DUCK OS", 4u, 7u, 7u, 7u);

    const uint64_t body_y = fb->height > 140u ? fb->height / 2u - 70u : 8u;
    draw_centered(body_y, "NATIVE MEMORY READY", 3u, 255u, 212u, 0u);
    draw_centered(body_y + 70u, "MEMORY MAP VALIDATED", 2u, 90u, 220u, 120u);
    draw_centered(body_y + 112u, "FRAME ALLOCATOR READY", 2u, 255u, 212u, 0u);
    if (fb->width > 64u && fb->height > 45u) {
        draw_rect(32u, fb->height - 42u, fb->width - 64u, 3u, 255u, 212u, 0u);
    }
}

static int memory_type_from_limine(uint64_t source, uint32_t *destination) {
    if (destination == NULL) return 0;
    switch (source) {
        case LIMINE_MEMMAP_USABLE:
            *destination = DUCKOS_MEMORY_USABLE;
            return 1;
        case LIMINE_MEMMAP_RESERVED:
        case LIMINE_MEMMAP_BOOTLOADER_RECLAIMABLE:
        case LIMINE_MEMMAP_EXECUTABLE_AND_MODULES:
        case LIMINE_MEMMAP_RESERVED_MAPPED:
            *destination = DUCKOS_MEMORY_RESERVED;
            return 1;
        case LIMINE_MEMMAP_ACPI_RECLAIMABLE:
            *destination = DUCKOS_MEMORY_ACPI_RECLAIMABLE;
            return 1;
        case LIMINE_MEMMAP_ACPI_NVS:
            *destination = DUCKOS_MEMORY_ACPI_NVS;
            return 1;
        case LIMINE_MEMMAP_BAD_MEMORY:
            *destination = DUCKOS_MEMORY_BAD;
            return 1;
        case LIMINE_MEMMAP_FRAMEBUFFER:
            *destination = DUCKOS_MEMORY_MMIO;
            return 1;
        default:
            return 0;
    }
}

static int prepare_boot_info(duckos_boot_info_v1 *info) {
    struct limine_memmap_response *map = memory_map_request.response;
    struct limine_executable_address_response *image = executable_address_request.response;
    struct limine_hhdm_response *hhdm = hhdm_request.response;

    if (info == NULL || map == NULL || image == NULL || hhdm == NULL) {
        serial_write("DUCKOS_BOOT_ERROR missing required Limine response\n");
        return 0;
    }
    if (map->entry_count == 0u || map->entry_count > MAX_BOOT_REGIONS ||
        map->entries == NULL) {
        serial_write("DUCKOS_BOOT_ERROR memory map exceeds v1 capacity\n");
        return 0;
    }
    if (image->virtual_base != (uint64_t)(uintptr_t)__kernel_start) {
        serial_write("DUCKOS_BOOT_ERROR kernel virtual base mismatch\n");
        return 0;
    }

    for (uint64_t index = 0u; index < map->entry_count; ++index) {
        const struct limine_memmap_entry *source = map->entries[index];
        if (source == NULL ||
            !memory_type_from_limine(source->type, &boot_regions[index].type)) {
            serial_write("DUCKOS_BOOT_ERROR unsupported memory-map entry\n");
            return 0;
        }
        boot_regions[index].base = source->base;
        boot_regions[index].length = source->length;
        boot_regions[index].flags = 0u;
    }

    info->struct_size = (uint32_t)sizeof(*info);
    info->version = DUCKOS_BOOT_INFO_VERSION;
    info->flags = 0u;
    info->kernel_phys_base = image->physical_base;
    info->kernel_size =
        (uint64_t)(uintptr_t)__kernel_end - (uint64_t)(uintptr_t)__kernel_start;
    info->initramfs_phys_base = 0u;
    info->initramfs_size = 0u;
    info->framebuffer_phys_base = 0u;
    info->framebuffer_size = 0u;
    info->framebuffer_width = 0u;
    info->framebuffer_height = 0u;
    info->framebuffer_pitch = 0u;
    info->framebuffer_bpp = 0u;
    info->memory_region_count = (uint32_t)map->entry_count;
    info->reserved = 0u;

    struct limine_firmware_type_response *firmware = firmware_request.response;
    if (firmware != NULL) info->flags = firmware->firmware_type;

    struct limine_framebuffer_response *fb_response = framebuffer_request.response;
    if (fb_response != NULL && fb_response->framebuffer_count != 0u &&
        fb_response->framebuffers != NULL && fb_response->framebuffers[0] != NULL) {
        active_framebuffer = fb_response->framebuffers[0];
        const struct limine_framebuffer *fb = active_framebuffer;
        if (fb->address == NULL || (uint64_t)(uintptr_t)fb->address < hhdm->offset ||
            fb->width == 0u || fb->height == 0u ||
            fb->width > UINT32_MAX || fb->height > UINT32_MAX ||
            fb->pitch == 0u || fb->pitch > UINT32_MAX ||
            (fb->bpp != 16u && fb->bpp != 24u && fb->bpp != 32u) ||
            fb->memory_model != LIMINE_FRAMEBUFFER_RGB ||
            fb->height > UINT64_MAX / fb->pitch) {
            serial_write("DUCKOS_BOOT_ERROR invalid framebuffer response\n");
            return 0;
        }

        info->framebuffer_phys_base =
            (uint64_t)(uintptr_t)fb->address - hhdm->offset;
        info->framebuffer_size = fb->pitch * fb->height;
        info->framebuffer_width = (uint32_t)fb->width;
        info->framebuffer_height = (uint32_t)fb->height;
        info->framebuffer_pitch = (uint32_t)fb->pitch;
        info->framebuffer_bpp = fb->bpp;
    }
    return 1;
}

static int initialize_early_memory(uint32_t memory_region_count) {
    struct limine_hhdm_response *hhdm = hhdm_request.response;
    if (hhdm == NULL) return 0;

    if (duckos_frame_allocator_init(
            &early_frame_allocator,
            boot_regions,
            memory_region_count,
            0x00100000u
        ) != DUCKOS_FRAME_ALLOCATOR_OK) {
        return 0;
    }

    if (duckos_frame_allocator_allocate(
            &early_frame_allocator,
            &first_frame_phys
        ) != DUCKOS_FRAME_ALLOCATOR_OK) {
        return 0;
    }

    if (hhdm->offset > (uint64_t)UINTPTR_MAX ||
        first_frame_phys > (uint64_t)UINTPTR_MAX - hhdm->offset) {
        return 0;
    }

    const uintptr_t mapped_address =
        (uintptr_t)(hhdm->offset + first_frame_phys);
    volatile uint64_t *page = (volatile uint64_t *)mapped_address;
    for (size_t index = 0u;
         index < (size_t)(DUCKOS_FRAME_PAGE_SIZE / sizeof(uint64_t));
         ++index) {
        page[index] = 0u;
    }
    return 1;
}


static int initialize_kernel_integrity_core(void) {
    /* No model is active at cold boot; install remains denied until verified publication. */
    dak_rule_registry_init(&active_rule_models);
    dak_predictor_init(&install_predictor);
    return 1;
}

static void boot_failure(const char *reason) __attribute__((noreturn));
static void boot_failure(const char *reason) {
    serial_write("DUCKOS_BOOT_ERROR ");
    serial_write(reason);
    serial_write("\n");
    if (active_framebuffer != NULL && active_framebuffer->bpp == 32u) {
        draw_rect(0u, 0u, active_framebuffer->width, 12u, 180u, 30u, 30u);
    }
    halt_forever();
}


static const char *exception_name(uint64_t vector) {
    static const char *const names[DUCKOS_X86_EXCEPTION_COUNT] = {
        "DIVIDE ERROR", "DEBUG", "NON-MASKABLE INTERRUPT", "BREAKPOINT",
        "OVERFLOW", "BOUND RANGE", "INVALID OPCODE", "DEVICE NOT AVAILABLE",
        "DOUBLE FAULT", "COPROCESSOR OVERRUN", "INVALID TSS",
        "SEGMENT NOT PRESENT", "STACK FAULT", "GENERAL PROTECTION",
        "PAGE FAULT", "RESERVED", "X87 FLOATING POINT", "ALIGNMENT CHECK",
        "MACHINE CHECK", "SIMD FLOATING POINT", "VIRTUALIZATION",
        "CONTROL PROTECTION", "RESERVED", "RESERVED", "RESERVED",
        "RESERVED", "RESERVED", "RESERVED", "HYPERVISOR INJECTION",
        "VMM COMMUNICATION", "SECURITY EXCEPTION", "RESERVED"
    };
    return vector < DUCKOS_X86_EXCEPTION_COUNT ? names[vector] : "UNKNOWN";
}

void duckos_x86_exception_dispatch(const duckos_x86_exception_frame *frame) {
    __asm__ volatile ("cli");
    serial_write("\nDUCKOS_EXCEPTION ");
    if (frame == NULL) {
        serial_write("frame=null\n");
    } else {
        serial_write("vector=");
        serial_decimal(frame->vector);
        serial_write(" name=");
        serial_write(exception_name(frame->vector));
        serial_write(" error=");
        serial_hex(frame->error_code);
        if (frame->vector == 14u) {
            uint64_t fault_address;
            __asm__ volatile ("mov %%cr2, %0" : "=r"(fault_address));
            serial_write(" cr2=");
            serial_hex(fault_address);
        }
        serial_write(" rip=");
        serial_hex(frame->rip);
        serial_write(" cs=");
        serial_hex(frame->cs);
        serial_write(" rflags=");
        serial_hex(frame->rflags);
        serial_write("\n");
    }

    if (active_framebuffer != NULL && active_framebuffer->bpp == 32u) {
        draw_rect(0u, 0u, active_framebuffer->width, 84u, 150u, 22u, 22u);
        draw_text(24u, 20u, "KERNEL EXCEPTION", 3u, 255u, 255u, 255u);
        draw_text(24u, 52u, "SYSTEM HALTED", 2u, 255u, 212u, 0u);
    }
    halt_forever();
}

void _start(void) __attribute__((noreturn));
void _start(void) {
    __asm__ volatile ("cli");
    serial_init();
    if (!duckos_x86_gdt_init()) {
        boot_failure("could not install owned x86_64 GDT/TSS");
    }
    serial_write("gdt=owned tss=loaded rsp0=bootstrap ist=df,nmi,pf\n");
    if (!duckos_x86_interrupts_init()) {
        boot_failure("could not install CPU exception IDT");
    }
    serial_write("exceptions=0..31 idt=loaded maskable_interrupts=disabled\n");
    serial_write("exception_ist=double-fault:1 nmi:2 page-fault:3\n");
    serial_write("\nDUCKOS_BOOT begin protocol=limine base_revision=6\n");

    if (!LIMINE_BASE_REVISION_SUPPORTED(base_revision)) {
        boot_failure("bootloader does not support required Limine base revision 6");
    }

    struct limine_bootloader_info_response *bootloader = bootloader_request.response;
    if (bootloader != NULL) {
        serial_write("bootloader=");
        serial_write(bootloader->name);
        serial_write(" version=");
        serial_write(bootloader->version);
        serial_write("\n");
    }

    duckos_boot_info_v1 info;
    if (!prepare_boot_info(&info)) {
        boot_failure("could not construct the v1 boot handoff");
    }

    const duckos_boot_info_status validation =
        duckos_boot_info_validate(
            &info,
            boot_regions,
            (size_t)info.memory_region_count
        );
    if (validation != DUCKOS_BOOT_INFO_OK) {
        serial_write("boot-info status=");
        serial_write(duckos_boot_info_status_name(validation));
        serial_write("\n");
        boot_failure("boot handoff validation rejected firmware state");
    }

    if (!initialize_early_memory(info.memory_region_count)) {
        boot_failure("bootstrap physical frame allocation failed");
    }
    if (!initialize_kernel_integrity_core()) {
        boot_failure("native kernel-integrity core initialization failed");
    }

    serial_write("firmware=");
    serial_decimal(info.flags);
    serial_write(" memory_regions=");
    serial_decimal(info.memory_region_count);
    serial_write(" kernel_phys=");
    serial_hex(info.kernel_phys_base);
    serial_write(" kernel_bytes=");
    serial_decimal(info.kernel_size);
    serial_write("\n");

    serial_write("dak-kernel-integrity=initialized rule-model=empty predictor=ready DAKS=v1\n");

    serial_write("memory=early-frame-allocator page_size=4096 usable_pages=");
    serial_decimal(early_frame_allocator.total_pages);
    serial_write(" allocated_pages=");
    serial_decimal(early_frame_allocator.allocated_pages);
    serial_write(" first_frame_phys=");
    serial_hex(first_frame_phys);
    serial_write("\n");

    if (active_framebuffer != NULL) {
        draw_boot_screen();
        serial_write("framebuffer=");
        serial_decimal(info.framebuffer_width);
        serial_putc('x');
        serial_decimal(info.framebuffer_height);
        serial_putc('x');
        serial_decimal(info.framebuffer_bpp);
        serial_write("\n");
    } else {
        serial_write("framebuffer=unavailable; serial console remains active\n");
    }

    serial_write("DUCKOS_BOOT_OK stage=1 handoff=v1 frames=1 reaper_policy=reference-only\n");
    halt_forever();
}
