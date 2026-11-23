#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdnoreturn.h>

#include <limine.h>

#include "serial.h"
#include "initramfs.h"

__attribute__((used, section(".limine_requests")))
static volatile uint64_t limine_base_revision[] = LIMINE_BASE_REVISION(6);

__attribute__((used, section(".limine_requests_start")))
static volatile uint64_t limine_requests_start[] = LIMINE_REQUESTS_START_MARKER;

__attribute__((used, section(".limine_requests")))
static volatile struct limine_framebuffer_request framebuffer_request = {
    .id = LIMINE_FRAMEBUFFER_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests")))
static volatile struct limine_memmap_request memmap_request = {
    .id = LIMINE_MEMMAP_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests")))
static volatile struct limine_hhdm_request hhdm_request = {
    .id = LIMINE_HHDM_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests")))
static volatile struct limine_bootloader_info_request bootloader_request = {
    .id = LIMINE_BOOTLOADER_INFO_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests")))
static volatile struct limine_module_request module_request = {
    .id = LIMINE_MODULE_REQUEST_ID,
    .revision = 0
};

__attribute__((used, section(".limine_requests_end")))
static volatile uint64_t limine_requests_end[] = LIMINE_REQUESTS_END_MARKER;

static noreturn void halt_forever(void)
{
    __asm__ volatile ("cli");

    for (;;) {
        __asm__ volatile ("hlt");
    }
}

static void draw_boot_screen(void)
{
    if (framebuffer_request.response == NULL ||
        framebuffer_request.response->framebuffer_count == 0) {
        serial_write("[video] no framebuffer supplied\n");
        return;
    }

    struct limine_framebuffer *fb =
        framebuffer_request.response->framebuffers[0];

    if (fb == NULL || fb->memory_model != LIMINE_FRAMEBUFFER_RGB ||
        fb->bpp != 32 || fb->address == NULL ||
        fb->pitch < fb->width * sizeof(uint32_t)) {
        serial_write("[video] unsupported framebuffer layout\n");
        return;
    }

    volatile uint32_t *pixels = fb->address;
    const uint64_t stride = fb->pitch / sizeof(uint32_t);

    for (uint64_t y = 0; y < fb->height; ++y) {
        for (uint64_t x = 0; x < fb->width; ++x) {
            const uint8_t red = (uint8_t)(7 + (x * 7 / (fb->width + 1)));
            const uint8_t green = (uint8_t)(18 + (y * 11 / (fb->height + 1)));
            const uint8_t blue = (uint8_t)(31 + ((x + y) * 17 /
                (fb->width + fb->height + 1)));

            const uint32_t rmax = (1u << fb->red_mask_size) - 1u;
            const uint32_t gmax = (1u << fb->green_mask_size) - 1u;
            const uint32_t bmax = (1u << fb->blue_mask_size) - 1u;

            const uint32_t pixel =
                (((uint32_t)red * rmax / 255u) << fb->red_mask_shift) |
                (((uint32_t)green * gmax / 255u) << fb->green_mask_shift) |
                (((uint32_t)blue * bmax / 255u) << fb->blue_mask_shift);

            pixels[y * stride + x] = pixel;
        }
    }

    serial_write("[video] boot framebuffer painted\n");
}

static void report_memory_map(void)
{
    if (memmap_request.response == NULL ||
        memmap_request.response->entries == NULL) {
        serial_write("[memory] memory map unavailable\n");
        return;
    }

    const struct limine_memmap_response *map = memmap_request.response;
    uint64_t usable_bytes = 0;

    serial_write("[memory] entries: ");
    serial_write_dec(map->entry_count);
    serial_write("\n");

    for (uint64_t i = 0; i < map->entry_count; ++i) {
        const struct limine_memmap_entry *entry = map->entries[i];

        if (entry != NULL && entry->type == LIMINE_MEMMAP_USABLE &&
            UINT64_MAX - usable_bytes >= entry->length) {
            usable_bytes += entry->length;
        }
    }

    serial_write("[memory] usable bytes: ");
    serial_write_dec(usable_bytes);
    serial_write("\n");
}

_Noreturn void kmain(void)
{
    serial_init();
    serial_write("\nDuckOS kernel bring-up\n");
    serial_write("----------------------\n");

    if (!LIMINE_BASE_REVISION_SUPPORTED(limine_base_revision)) {
        serial_write("[boot] unsupported Limine base revision\n");
        halt_forever();
    }

    serial_write("[boot] Limine protocol revision accepted\n");

    if (bootloader_request.response != NULL) {
        serial_write("[boot] loader: ");
        serial_write(bootloader_request.response->name);
        serial_write(" ");
        serial_write(bootloader_request.response->version);
        serial_write("\n");
    }

    if (hhdm_request.response != NULL) {
        serial_write("[memory] HHDM offset: ");
        serial_write_hex(hhdm_request.response->offset);
        serial_write("\n");
    }

    report_memory_map();

    if (module_request.response != NULL) {
        const struct limine_module_response *modules = module_request.response;
        serial_write("[initramfs] boot modules: ");
        serial_write_dec(modules->module_count);
        serial_write("\n");

        if (modules->module_count > 0 && modules->modules != NULL &&
            modules->modules[0] != NULL) {
            const struct limine_file *archive = modules->modules[0];
            uint64_t entry_count = 0;

            if (archive->address != NULL &&
                initramfs_validate(archive->address, archive->size, &entry_count)) {
                serial_write("[initramfs] newc archive validated; entries: ");
                serial_write_dec(entry_count);
                serial_write("\n");
            } else {
                serial_write("[initramfs] first module is not a valid newc archive\n");
            }
        } else {
            serial_write("[initramfs] module list is empty\n");
        }
    } else {
        serial_write("[initramfs] no boot modules supplied\n");
    }

    draw_boot_screen();

    serial_write("[boot] early kernel stage complete; scheduler and userspace are not implemented yet\n");
    halt_forever();
}
