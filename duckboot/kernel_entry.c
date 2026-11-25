#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "boot_info.h"
#include "frame_allocator.h"
#include "duckboot/handoff.h"

#define SERIAL_PORT 0x3f8u
#define PAGE_SIZE 4096u

static duckos_memory_region boot_regions[DUCKOS_BOOT_MAX_MEMORY_REGIONS];
static duckos_frame_allocator early_frame_allocator;
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

static void serial_write(const char *value) {
    if (value == NULL) return;
    while (*value != '\0') {
        if (*value == '\n') serial_putc('\r');
        serial_putc(*value++);
    }
}

static void serial_hex(uint64_t value) {
    static const char digits[] = "0123456789abcdef";
    serial_write("0x");
    for (int shift = 60; shift >= 0; shift -= 4) {
        serial_putc(digits[(value >> (uint32_t)shift) & 0x0fu]);
    }
}

static bool is_canonical(uint64_t address) {
    const uint64_t upper = address >> 48u;
    const bool sign = ((address >> 47u) & 1u) != 0u;
    return sign ? upper == 0xffffu : upper == 0u;
}

static void halt_forever(void) __attribute__((noreturn));
static void halt_forever(void) {
    for (;;) __asm__ volatile ("cli; hlt");
}

static void boot_failure(const char *reason) __attribute__((noreturn));
static void boot_failure(const char *reason) {
    serial_write("DUCKOS_BOOT_ERROR loader=duckboot ");
    serial_write(reason);
    serial_write("\n");
    halt_forever();
}

static uint32_t channel_bits(uint8_t channel, uint8_t width, uint8_t shift) {
    if (width == 0u || width > 8u || shift >= 32u ||
        (uint32_t)width + (uint32_t)shift > 32u) return 0u;
    const uint32_t maximum = (1u << width) - 1u;
    const uint32_t scaled = ((uint32_t)channel * maximum + 127u) / 255u;
    return scaled << shift;
}

static void draw_rect(
    volatile uint8_t *framebuffer,
    uint32_t pitch,
    uint32_t width,
    uint32_t height,
    uint32_t bytes_per_pixel,
    uint32_t red_mask_size,
    uint32_t red_mask_shift,
    uint32_t green_mask_size,
    uint32_t green_mask_shift,
    uint32_t blue_mask_size,
    uint32_t blue_mask_shift,
    uint32_t x,
    uint32_t y,
    uint32_t rect_width,
    uint32_t rect_height,
    uint8_t red,
    uint8_t green,
    uint8_t blue
) {
    if (framebuffer == NULL || bytes_per_pixel != 4u || x >= width || y >= height) return;
    if (rect_width > width - x) rect_width = width - x;
    if (rect_height > height - y) rect_height = height - y;
    const uint32_t pixel =
        channel_bits(red, (uint8_t)red_mask_size, (uint8_t)red_mask_shift) |
        channel_bits(green, (uint8_t)green_mask_size, (uint8_t)green_mask_shift) |
        channel_bits(blue, (uint8_t)blue_mask_size, (uint8_t)blue_mask_shift);
    for (uint32_t row = 0u; row < rect_height; ++row) {
        volatile uint32_t *line = (volatile uint32_t *)(framebuffer +
            (uint64_t)(y + row) * pitch + (uint64_t)x * bytes_per_pixel);
        for (uint32_t column = 0u; column < rect_width; ++column) line[column] = pixel;
    }
}

static void draw_boot_screen(const duckboot_handoff_v1 *handoff,
                             const duckos_boot_info_v1 *info) {
    if (handoff->framebuffer_virtual == 0u || info->framebuffer_bpp != 32u) return;
    volatile uint8_t *fb = (volatile uint8_t *)(uintptr_t)handoff->framebuffer_virtual;
    draw_rect(fb, info->framebuffer_pitch, info->framebuffer_width,
        info->framebuffer_height, 4u,
        handoff->red_mask_size, handoff->red_mask_shift,
        handoff->green_mask_size, handoff->green_mask_shift,
        handoff->blue_mask_size, handoff->blue_mask_shift,
        0u, 0u, info->framebuffer_width, info->framebuffer_height, 7u, 7u, 7u);
    draw_rect(fb, info->framebuffer_pitch, info->framebuffer_width,
        info->framebuffer_height, 4u,
        handoff->red_mask_size, handoff->red_mask_shift,
        handoff->green_mask_size, handoff->green_mask_shift,
        handoff->blue_mask_size, handoff->blue_mask_shift,
        0u, 0u, info->framebuffer_width, 72u, 255u, 212u, 0u);
    draw_rect(fb, info->framebuffer_pitch, info->framebuffer_width,
        info->framebuffer_height, 4u,
        handoff->red_mask_size, handoff->red_mask_shift,
        handoff->green_mask_size, handoff->green_mask_shift,
        handoff->blue_mask_size, handoff->blue_mask_shift,
        24u, info->framebuffer_height > 36u ? info->framebuffer_height - 36u : 0u,
        info->framebuffer_width > 48u ? info->framebuffer_width - 48u : 0u,
        3u, 255u, 212u, 0u);
}

void _start(const duckboot_handoff_v1 *handoff) __attribute__((noreturn));
void _start(const duckboot_handoff_v1 *handoff) {
    serial_init();
    serial_write("\nDUCKOS_BOOT begin loader=duckboot handoff=v1\n");

    if (handoff == NULL ||
        handoff->magic != DUCKBOOT_HANDOFF_MAGIC ||
        handoff->version != DUCKBOOT_HANDOFF_VERSION ||
        handoff->struct_size < (uint32_t)sizeof(*handoff) ||
        !is_canonical((uint64_t)(uintptr_t)handoff) ||
        handoff->boot_info_virtual == 0u ||
        handoff->memory_map_virtual == 0u ||
        handoff->hhdm_offset != UINT64_C(0xffff800000000000) ||
        handoff->hhdm_offset > (uint64_t)UINTPTR_MAX ||
        !is_canonical(handoff->boot_info_virtual) ||
        !is_canonical(handoff->memory_map_virtual)) {
        boot_failure("invalid DuckBoot handoff envelope");
    }

    const duckos_boot_info_v1 *info =
        (const duckos_boot_info_v1 *)(uintptr_t)handoff->boot_info_virtual;
    const duckos_memory_region *regions =
        (const duckos_memory_region *)(uintptr_t)handoff->memory_map_virtual;
    if (info == NULL || regions == NULL ||
        info->memory_region_count == 0u ||
        info->memory_region_count > DUCKOS_BOOT_MAX_MEMORY_REGIONS) {
        boot_failure("invalid Boot Info v1 addresses or memory map size");
    }

    const duckos_boot_info_status validation = duckos_boot_info_validate(
        info, regions, (size_t)info->memory_region_count);
    if (validation != DUCKOS_BOOT_INFO_OK) {
        serial_write("boot-info status=");
        serial_write(duckos_boot_info_status_name(validation));
        serial_write("\n");
        boot_failure("Boot Info v1 validation failed");
    }

    for (uint32_t index = 0u; index < info->memory_region_count; ++index) {
        boot_regions[index] = regions[index];
    }

    if (duckos_frame_allocator_init(
            &early_frame_allocator,
            boot_regions,
            info->memory_region_count,
            0x00100000u) != DUCKOS_FRAME_ALLOCATOR_OK) {
        boot_failure("early physical frame allocator rejected memory map");
    }
    if (duckos_frame_allocator_allocate(
            &early_frame_allocator, &first_frame_phys) != DUCKOS_FRAME_ALLOCATOR_OK) {
        boot_failure("early physical frame allocation failed");
    }
    if (first_frame_phys > UINT64_MAX - handoff->hhdm_offset ||
        handoff->hhdm_offset + first_frame_phys > (uint64_t)UINTPTR_MAX) {
        boot_failure("HHDM frame address overflow");
    }
    volatile uint64_t *page = (volatile uint64_t *)(uintptr_t)(
        handoff->hhdm_offset + first_frame_phys);
    for (size_t index = 0u; index < PAGE_SIZE / sizeof(uint64_t); ++index) page[index] = 0u;

    draw_boot_screen(handoff, info);
    serial_write("kernel_phys=");
    serial_hex(info->kernel_phys_base);
    serial_write(" kernel_bytes=");
    serial_hex(info->kernel_size);
    serial_write(" memory_regions=");
    serial_hex(info->memory_region_count);
    serial_write(" frame_phys=");
    serial_hex(first_frame_phys);
    serial_write("\n");
    serial_write("DUCKOS_BOOT_OK stage=1 loader=duckboot handoff=v1 frames=1\n");
    halt_forever();
}
