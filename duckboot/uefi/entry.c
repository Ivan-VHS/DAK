#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#include "boot_info.h"
#include "duckboot/config.h"
#include "duckboot/elf64.h"
#include "duckboot/handoff.h"

#define EFIAPI __attribute__((ms_abi))
#define EFI_SUCCESS 0u
#define EFI_NOT_FOUND UINT64_C(0x800000000000000e)
#define EFI_ALLOCATE_ANY_PAGES 0u
#define EFI_ALLOCATE_ADDRESS 2u
#define EFI_LOADER_DATA 2u
#define EFI_FILE_MODE_READ UINT64_C(1)
#define EFI_MEMORY_MAPPED_IO 11u
#define EFI_MEMORY_MAPPED_IO_PORT_SPACE 12u
#define EFI_CONVENTIONAL_MEMORY 7u
#define EFI_BOOT_SERVICES_CODE 3u
#define EFI_BOOT_SERVICES_DATA 4u
#define EFI_ACPI_RECLAIM_MEMORY 9u
#define EFI_ACPI_MEMORY_NVS 10u
#define EFI_UNUSABLE_MEMORY 8u
#define EFI_LOADER_CODE 1u
#define EFI_LOADER_DATA_TYPE 2u
#define EFI_RUNTIME_SERVICES_CODE 5u
#define EFI_RUNTIME_SERVICES_DATA 6u
#define EFI_RESERVED_MEMORY_TYPE 0u
#define EFI_PAGE_SIZE UINT64_C(4096)
#define DUCKBOOT_HHDM_OFFSET UINT64_C(0xffff800000000000)
#define DUCKBOOT_MAX_KERNEL_BYTES (32u * 1024u * 1024u)
#define DUCKBOOT_MEMORY_MAP_BYTES (512u * 1024u)
#define DUCKBOOT_STACK_PAGES 64u
#define PTE_PRESENT UINT64_C(0x001)
#define PTE_WRITE UINT64_C(0x002)
#define PTE_PWT UINT64_C(0x008)
#define PTE_PCD UINT64_C(0x010)
#define PTE_LARGE UINT64_C(0x080)
#define PTE_NX (UINT64_C(1) << 63u)
#define PTE_ADDRESS_MASK UINT64_C(0x000ffffffffff000)
#define PAGE_2M UINT64_C(0x200000)
#define EFI_ERROR(status) (((status) & (UINT64_C(1) << 63u)) != 0u)

typedef uint64_t EFI_STATUS;
typedef void *EFI_HANDLE;
typedef uint16_t CHAR16;
typedef uint64_t EFI_PHYSICAL_ADDRESS;
typedef size_t UINTN;

typedef struct EFI_GUID {
    uint32_t data1;
    uint16_t data2;
    uint16_t data3;
    uint8_t data4[8];
} EFI_GUID;

typedef struct EFI_TABLE_HEADER {
    uint64_t signature;
    uint32_t revision;
    uint32_t header_size;
    uint32_t crc32;
    uint32_t reserved;
} EFI_TABLE_HEADER;

typedef struct EFI_MEMORY_DESCRIPTOR {
    uint32_t type;
    uint32_t pad;
    uint64_t physical_start;
    uint64_t virtual_start;
    uint64_t number_of_pages;
    uint64_t attribute;
} EFI_MEMORY_DESCRIPTOR;

typedef struct EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL;
typedef struct EFI_FILE_PROTOCOL EFI_FILE_PROTOCOL;

typedef EFI_STATUS (EFIAPI *EFI_ALLOCATE_PAGES)(uint32_t, uint32_t, UINTN, EFI_PHYSICAL_ADDRESS *);
typedef EFI_STATUS (EFIAPI *EFI_GET_MEMORY_MAP)(UINTN *, EFI_MEMORY_DESCRIPTOR *, UINTN *, UINTN *, uint32_t *);
typedef EFI_STATUS (EFIAPI *EFI_ALLOCATE_POOL)(uint32_t, UINTN, void **);
typedef EFI_STATUS (EFIAPI *EFI_FREE_POOL)(void *);
typedef EFI_STATUS (EFIAPI *EFI_HANDLE_PROTOCOL)(EFI_HANDLE, EFI_GUID *, void **);
typedef EFI_STATUS (EFIAPI *EFI_LOCATE_PROTOCOL)(EFI_GUID *, void *, void **);
typedef EFI_STATUS (EFIAPI *EFI_EXIT_BOOT_SERVICES)(EFI_HANDLE, UINTN);
typedef EFI_STATUS (EFIAPI *EFI_STALL)(UINTN);

typedef struct EFI_BOOT_SERVICES {
    EFI_TABLE_HEADER header;
    void *raise_tpl;
    void *restore_tpl;
    EFI_ALLOCATE_PAGES allocate_pages;
    void *free_pages;
    EFI_GET_MEMORY_MAP get_memory_map;
    EFI_ALLOCATE_POOL allocate_pool;
    EFI_FREE_POOL free_pool;
    void *create_event;
    void *set_timer;
    void *wait_for_event;
    void *signal_event;
    void *close_event;
    void *check_event;
    void *install_protocol_interface;
    void *reinstall_protocol_interface;
    void *uninstall_protocol_interface;
    EFI_HANDLE_PROTOCOL handle_protocol;
    void *reserved;
    void *register_protocol_notify;
    void *locate_handle;
    void *locate_device_path;
    void *install_configuration_table;
    void *load_image;
    void *start_image;
    void *exit;
    void *unload_image;
    EFI_EXIT_BOOT_SERVICES exit_boot_services;
    void *get_next_monotonic_count;
    EFI_STALL stall;
    void *set_watchdog_timer;
    void *connect_controller;
    void *disconnect_controller;
    void *open_protocol;
    void *close_protocol;
    void *open_protocol_information;
    void *protocols_per_handle;
    void *locate_handle_buffer;
    EFI_LOCATE_PROTOCOL locate_protocol;
    void *install_multiple_protocol_interfaces;
    void *uninstall_multiple_protocol_interfaces;
    void *calculate_crc32;
    void *copy_mem;
    void *set_mem;
    void *create_event_ex;
} EFI_BOOT_SERVICES;

typedef struct EFI_SYSTEM_TABLE {
    EFI_TABLE_HEADER header;
    CHAR16 *firmware_vendor;
    uint32_t firmware_revision;
    EFI_HANDLE console_in_handle;
    void *con_in;
    EFI_HANDLE console_out_handle;
    EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *con_out;
    EFI_HANDLE standard_error_handle;
    EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *standard_error;
    void *runtime_services;
    EFI_BOOT_SERVICES *boot_services;
    UINTN number_of_table_entries;
    void *configuration_table;
} EFI_SYSTEM_TABLE;

struct EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL {
    void *reset;
    EFI_STATUS (EFIAPI *output_string)(EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *, CHAR16 *);
    void *test_string;
    void *query_mode;
    void *set_mode;
    void *set_attribute;
    EFI_STATUS (EFIAPI *clear_screen)(EFI_SIMPLE_TEXT_OUTPUT_PROTOCOL *);
    void *set_cursor_position;
    void *enable_cursor;
    void *mode;
};

typedef struct EFI_LOADED_IMAGE_PROTOCOL {
    uint32_t revision;
    EFI_HANDLE parent_handle;
    EFI_SYSTEM_TABLE *system_table;
    EFI_HANDLE device_handle;
    void *file_path;
    void *reserved;
    uint32_t load_options_size;
    void *load_options;
    void *image_base;
    uint64_t image_size;
    uint32_t image_code_type;
    uint32_t image_data_type;
    void *unload;
} EFI_LOADED_IMAGE_PROTOCOL;

typedef struct EFI_SIMPLE_FILE_SYSTEM_PROTOCOL {
    uint64_t revision;
    EFI_STATUS (EFIAPI *open_volume)(struct EFI_SIMPLE_FILE_SYSTEM_PROTOCOL *, EFI_FILE_PROTOCOL **);
} EFI_SIMPLE_FILE_SYSTEM_PROTOCOL;

struct EFI_FILE_PROTOCOL {
    uint64_t revision;
    EFI_STATUS (EFIAPI *open)(EFI_FILE_PROTOCOL *, EFI_FILE_PROTOCOL **, CHAR16 *, uint64_t, uint64_t);
    EFI_STATUS (EFIAPI *close)(EFI_FILE_PROTOCOL *);
    void *delete_file;
    EFI_STATUS (EFIAPI *read)(EFI_FILE_PROTOCOL *, UINTN *, void *);
    void *write;
    void *get_position;
    void *set_position;
    void *get_info;
    void *set_info;
    void *flush;
    void *open_ex;
    void *read_ex;
    void *write_ex;
    void *flush_ex;
};

typedef struct EFI_PIXEL_BITMASK {
    uint32_t red_mask;
    uint32_t green_mask;
    uint32_t blue_mask;
    uint32_t reserved_mask;
} EFI_PIXEL_BITMASK;

typedef struct EFI_GRAPHICS_OUTPUT_MODE_INFORMATION {
    uint32_t version;
    uint32_t horizontal_resolution;
    uint32_t vertical_resolution;
    uint32_t pixel_format;
    EFI_PIXEL_BITMASK pixel_information;
    uint32_t pixels_per_scan_line;
} EFI_GRAPHICS_OUTPUT_MODE_INFORMATION;

typedef struct EFI_GRAPHICS_OUTPUT_PROTOCOL_MODE {
    uint32_t max_mode;
    uint32_t mode;
    EFI_GRAPHICS_OUTPUT_MODE_INFORMATION *info;
    UINTN size_of_info;
    EFI_PHYSICAL_ADDRESS frame_buffer_base;
    UINTN frame_buffer_size;
} EFI_GRAPHICS_OUTPUT_PROTOCOL_MODE;

typedef struct EFI_GRAPHICS_OUTPUT_PROTOCOL {
    void *query_mode;
    void *set_mode;
    void *blt;
    EFI_GRAPHICS_OUTPUT_PROTOCOL_MODE *mode;
} EFI_GRAPHICS_OUTPUT_PROTOCOL;

typedef struct DUCKBOOT_FRAMEBUFFER {
    uint64_t physical_base;
    uint64_t size;
    uint64_t virtual_base;
    uint32_t width;
    uint32_t height;
    uint32_t pitch;
    uint32_t bpp;
    uint32_t red_size;
    uint32_t red_shift;
    uint32_t green_size;
    uint32_t green_shift;
    uint32_t blue_size;
    uint32_t blue_shift;
} DUCKBOOT_FRAMEBUFFER;

static const EFI_GUID gLoadedImageGuid = {
    0x5b1b31a1u, 0x9562u, 0x11d2u,
    {0x8e, 0x3f, 0x00, 0xa0, 0xc9, 0x69, 0x72, 0x3b}
};
static const EFI_GUID gSimpleFileSystemGuid = {
    0x964e5b22u, 0x6459u, 0x11d2u,
    {0x8e, 0x39, 0x00, 0xa0, 0xc9, 0x69, 0x72, 0x3b}
};
static const EFI_GUID gGraphicsOutputGuid = {
    0x9042a9deu, 0x23dcu, 0x4a38u,
    {0x96, 0xfb, 0x7a, 0xde, 0xd0, 0x80, 0x51, 0x6a}
};

static EFI_SYSTEM_TABLE *gSystemTable;
static EFI_BOOT_SERVICES *gBootServices;
static EFI_HANDLE gImageHandle;
static uint8_t gMemoryMapBuffer[DUCKBOOT_MEMORY_MAP_BYTES];
static duckos_memory_region gMemoryRegions[DUCKOS_BOOT_MAX_MEMORY_REGIONS];
static duckos_boot_info_v1 gBootInfo;
static duckboot_handoff_v1 gHandoff;
static char gCommandLine[DUCKBOOT_CONFIG_CMDLINE_CAPACITY];
static uint64_t gPageTableRoot;
static uint64_t gKernelStackTop;
static DUCKBOOT_FRAMEBUFFER gFramebuffer;

extern void duckboot_enter_kernel(uint64_t entry, uint64_t handoff,
                                  uint64_t stack_top, uint64_t cr3)
    __attribute__((ms_abi, noreturn));
extern void duckboot_enter_kernel_end(void);

static void zero_bytes(void *memory, uint64_t length) {
    volatile uint8_t *bytes = (volatile uint8_t *)memory;
    for (uint64_t index = 0u; index < length; ++index) bytes[index] = 0u;
}

static void copy_bytes(void *destination, const void *source, uint64_t length) {
    uint8_t *out = (uint8_t *)destination;
    const uint8_t *in = (const uint8_t *)source;
    for (uint64_t index = 0u; index < length; ++index) out[index] = in[index];
}

static uint64_t align_down(uint64_t value, uint64_t alignment) {
    return value & ~(alignment - 1u);
}

static bool align_up(uint64_t value, uint64_t alignment, uint64_t *result) {
    if (result == NULL || alignment == 0u ||
        (alignment & (alignment - 1u)) != 0u ||
        value > UINT64_MAX - (alignment - 1u)) return false;
    *result = (value + alignment - 1u) & ~(alignment - 1u);
    return true;
}

static void serial_out(uint16_t port, uint8_t value) {
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}

static uint8_t serial_in(uint16_t port) {
    uint8_t value;
    __asm__ volatile ("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}

static void serial_init(void) {
    serial_out(0x3f9u, 0u);
    serial_out(0x3fbu, 0x80u);
    serial_out(0x3f8u, 1u);
    serial_out(0x3f9u, 0u);
    serial_out(0x3fbu, 3u);
    serial_out(0x3fau, 0xc7u);
    serial_out(0x3fcu, 0x0bu);
}

static void serial_write(const char *text) {
    if (text == NULL) return;
    while (*text != '\0') {
        for (uint32_t spin = 0u; spin < 1000000u; ++spin) {
            if ((serial_in(0x3fdu) & 0x20u) != 0u) break;
        }
        serial_out(0x3f8u, (uint8_t)*text++);
    }
}

static void serial_hex(uint64_t value) {
    static const char digits[] = "0123456789abcdef";
    serial_write("0x");
    for (int shift = 60; shift >= 0; shift -= 4) {
        char digit[2];
        digit[0] = digits[(value >> (uint32_t)shift) & 0x0fu];
        digit[1] = '\0';
        serial_write(digit);
    }
}

static void console_ascii(const char *text) {
    CHAR16 buffer[128];
    if (gSystemTable == NULL || gSystemTable->con_out == NULL || text == NULL) return;
    while (*text != '\0') {
        size_t count = 0u;
        while (*text != '\0' && count + 1u < (sizeof(buffer) / sizeof(buffer[0]))) {
            buffer[count++] = (CHAR16)(uint8_t)*text++;
        }
        buffer[count] = 0u;
        if (gSystemTable->con_out->output_string != NULL) {
            gSystemTable->con_out->output_string(gSystemTable->con_out, buffer);
        }
    }
}

static void fail(const char *message) __attribute__((noreturn));
static void fail(const char *message) {
    serial_write("DUCKBOOT_ERROR ");
    serial_write(message);
    serial_write("\r\n");
    for (;;) __asm__ volatile ("cli; hlt");
}

static bool get_nx_support(void) {
    uint32_t eax = 0x80000000u;
    uint32_t ebx = 0u;
    uint32_t ecx = 0u;
    uint32_t edx = 0u;
    __asm__ volatile ("cpuid" : "+a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx));
    if (eax < 0x80000001u) return false;
    eax = 0x80000001u;
    __asm__ volatile ("cpuid" : "+a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx));
    return (edx & (1u << 20u)) != 0u;
}

static bool four_level_paging_active(void) {
    uint64_t cr4;
    __asm__ volatile ("mov %%cr4, %0" : "=r"(cr4));
    return (cr4 & (UINT64_C(1) << 12u)) == 0u;
}

static bool mask_info(uint32_t mask, uint32_t *size, uint32_t *shift) {
    uint32_t first = 0u;
    uint32_t bits = 0u;
    if (mask == 0u || size == NULL || shift == NULL) return false;
    while (first < 32u && (mask & (1u << first)) == 0u) ++first;
    uint32_t value = mask >> first;
    while ((value & 1u) != 0u) {
        ++bits;
        value >>= 1u;
    }
    if (value != 0u || bits == 0u || bits > 8u) return false;
    *size = bits;
    *shift = first;
    return true;
}

static bool discover_framebuffer(void) {
    EFI_GRAPHICS_OUTPUT_PROTOCOL *gop = NULL;
    EFI_STATUS status = gBootServices->locate_protocol(
        (EFI_GUID *)&gGraphicsOutputGuid, NULL, (void **)&gop);
    if (EFI_ERROR(status) || gop == NULL || gop->mode == NULL || gop->mode->info == NULL) {
        return true;
    }

    EFI_GRAPHICS_OUTPUT_MODE_INFORMATION *info = gop->mode->info;
    if (info->horizontal_resolution == 0u || info->vertical_resolution == 0u ||
        info->pixels_per_scan_line < info->horizontal_resolution ||
        info->pixels_per_scan_line > UINT32_MAX / 4u) {
        return false;
    }
    uint32_t red_mask = 0u;
    uint32_t green_mask = 0u;
    uint32_t blue_mask = 0u;
    if (info->pixel_format == 0u) {
        red_mask = 0x000000ffu;
        green_mask = 0x0000ff00u;
        blue_mask = 0x00ff0000u;
    } else if (info->pixel_format == 1u) {
        red_mask = 0x00ff0000u;
        green_mask = 0x0000ff00u;
        blue_mask = 0x000000ffu;
    } else if (info->pixel_format == 2u) {
        red_mask = info->pixel_information.red_mask;
        green_mask = info->pixel_information.green_mask;
        blue_mask = info->pixel_information.blue_mask;
    } else {
        return true;
    }

    if ((red_mask & green_mask) != 0u || (red_mask & blue_mask) != 0u ||
        (green_mask & blue_mask) != 0u ||
        !mask_info(red_mask, &gFramebuffer.red_size, &gFramebuffer.red_shift) ||
        !mask_info(green_mask, &gFramebuffer.green_size, &gFramebuffer.green_shift) ||
        !mask_info(blue_mask, &gFramebuffer.blue_size, &gFramebuffer.blue_shift)) {
        return false;
    }
    const uint64_t pitch = (uint64_t)info->pixels_per_scan_line * 4u;
    if (pitch > UINT32_MAX || info->vertical_resolution > UINT64_MAX / pitch) return false;
    const uint64_t required = pitch * info->vertical_resolution;
    if (gop->mode->frame_buffer_base == 0u || gop->mode->frame_buffer_size < required ||
        gop->mode->frame_buffer_base > UINT64_MAX - required) return false;

    gFramebuffer.physical_base = gop->mode->frame_buffer_base;
    gFramebuffer.size = required;
    gFramebuffer.width = info->horizontal_resolution;
    gFramebuffer.height = info->vertical_resolution;
    gFramebuffer.pitch = (uint32_t)pitch;
    gFramebuffer.bpp = 32u;
    return true;
}

static EFI_STATUS read_file(EFI_FILE_PROTOCOL *root, CHAR16 *path,
                            uint32_t maximum_bytes, void **data, UINTN *length) {
    EFI_FILE_PROTOCOL *file = NULL;
    EFI_STATUS status;
    void *buffer = NULL;
    UINTN bytes_read;
    if (root == NULL || path == NULL || data == NULL || length == NULL) {
        return UINT64_C(0x8000000000000002);
    }
    status = root->open(root, &file, path, EFI_FILE_MODE_READ, 0u);
    if (EFI_ERROR(status) || file == NULL) return status;
    status = gBootServices->allocate_pool(EFI_LOADER_DATA, maximum_bytes, &buffer);
    if (EFI_ERROR(status) || buffer == NULL) {
        file->close(file);
        return EFI_ERROR(status) ? status : UINT64_C(0x8000000000000002);
    }
    bytes_read = maximum_bytes;
    status = file->read(file, &bytes_read, buffer);
    file->close(file);
    if (EFI_ERROR(status) || bytes_read == maximum_bytes || bytes_read == 0u) {
        gBootServices->free_pool(buffer);
        return EFI_ERROR(status) ? status : UINT64_C(0x8000000000000002);
    }
    *data = buffer;
    *length = bytes_read;
    return EFI_SUCCESS;
}

static bool ascii_to_efi_path(const char *path, CHAR16 *destination, size_t capacity) {
    size_t length = 0u;
    if (path == NULL || destination == NULL || capacity == 0u) return false;
    while (path[length] != '\0') {
        if (length + 1u >= capacity || (uint8_t)path[length] < 0x20u) return false;
        destination[length] = path[length] == '/' ? (CHAR16)'\\' : (CHAR16)(uint8_t)path[length];
        ++length;
    }
    destination[length] = 0u;
    return length != 0u;
}

static bool load_config(EFI_FILE_PROTOCOL *root, duckboot_config *config) {
    static CHAR16 config_path[] = {
        '\\','b','o','o','t','\\','d','u','c','k','b','o','o','t','.','c','f','g',0
    };
    void *data = NULL;
    UINTN length = 0u;
    EFI_STATUS status = read_file(root, config_path, 4096u, &data, &length);
    if (EFI_ERROR(status)) {
        if (status != EFI_NOT_FOUND) return false;
        static const char default_config[] =
            "kernel=\\boot\\duckos.elf\ncmdline=duckos.bootloader=duckboot\n";
        return duckboot_config_parse(
            default_config, sizeof(default_config) - 1u, config) == DUCKBOOT_CONFIG_OK;
    }
    const duckboot_config_status parse_status =
        duckboot_config_parse((const char *)data, (size_t)length, config);
    gBootServices->free_pool(data);
    return parse_status == DUCKBOOT_CONFIG_OK;
}

static EFI_STATUS allocate_physical(uint64_t physical_base, uint64_t size) {
    uint64_t end;
    uint64_t aligned_end;
    if (size == 0u || physical_base > UINT64_MAX - size) {
        return UINT64_C(0x8000000000000002);
    }
    end = physical_base + size;
    if (!align_up(end, EFI_PAGE_SIZE, &aligned_end)) {
        return UINT64_C(0x8000000000000002);
    }
    const uint64_t base = align_down(physical_base, EFI_PAGE_SIZE);
    const UINTN pages = (UINTN)((aligned_end - base) / EFI_PAGE_SIZE);
    EFI_PHYSICAL_ADDRESS address = base;
    EFI_STATUS status = gBootServices->allocate_pages(
        EFI_ALLOCATE_ADDRESS, EFI_LOADER_DATA, pages, &address);
    if (EFI_ERROR(status) || address != base) {
        return EFI_ERROR(status) ? status : UINT64_C(0x8000000000000002);
    }
    return EFI_SUCCESS;
}

static EFI_STATUS allocate_any_pages(UINTN pages, uint64_t *physical_address) {
    EFI_PHYSICAL_ADDRESS address = 0u;
    EFI_STATUS status;
    if (physical_address == NULL || pages == 0u) return UINT64_C(0x8000000000000002);
    status = gBootServices->allocate_pages(
        EFI_ALLOCATE_ANY_PAGES, EFI_LOADER_DATA, pages, &address);
    if (EFI_ERROR(status)) return status;
    *physical_address = address;
    zero_bytes((void *)(uintptr_t)address, (uint64_t)pages * EFI_PAGE_SIZE);
    return EFI_SUCCESS;
}

static EFI_STATUS load_kernel(EFI_FILE_PROTOCOL *root, const duckboot_config *config,
                              duckboot_elf_image *image) {
    CHAR16 path[DUCKBOOT_CONFIG_KERNEL_CAPACITY];
    void *file_data = NULL;
    UINTN file_length = 0u;
    EFI_STATUS status;
    if (!ascii_to_efi_path(config->kernel_path, path,
                           sizeof(path) / sizeof(path[0]))) {
        return UINT64_C(0x8000000000000002);
    }
    status = read_file(root, path, DUCKBOOT_MAX_KERNEL_BYTES, &file_data, &file_length);
    if (EFI_ERROR(status)) return status;

    const duckboot_elf_status elf_status =
        duckboot_elf64_inspect(file_data, (size_t)file_length, image);
    if (elf_status != DUCKBOOT_ELF_OK) {
        gBootServices->free_pool(file_data);
        serial_write("ELF_REJECT ");
        serial_write(duckboot_elf_status_name(elf_status));
        serial_write("\r\n");
        return UINT64_C(0x8000000000000002);
    }
    status = allocate_physical(image->physical_base,
                               image->physical_end - image->physical_base);
    if (EFI_ERROR(status)) {
        gBootServices->free_pool(file_data);
        return status;
    }
    for (size_t index = 0u; index < image->segment_count; ++index) {
        const duckboot_elf_segment *segment = &image->segments[index];
        uint8_t *destination = (uint8_t *)(uintptr_t)segment->physical_address;
        if (segment->file_size != 0u) {
            copy_bytes(destination,
                (const uint8_t *)file_data + (size_t)segment->file_offset,
                segment->file_size);
        }
        if (segment->memory_size > segment->file_size) {
            zero_bytes(destination + segment->file_size,
                       segment->memory_size - segment->file_size);
        }
    }
    gBootServices->free_pool(file_data);
    return EFI_SUCCESS;
}

static bool append_memory_region(uint64_t base, uint64_t length, uint32_t type) {
    if (length == 0u) return true;
    if (gBootInfo.memory_region_count != 0u) {
        duckos_memory_region *previous =
            &gMemoryRegions[gBootInfo.memory_region_count - 1u];
        if (previous->base <= UINT64_MAX - previous->length &&
            previous->base + previous->length == base && previous->type == type &&
            previous->flags == 0u && previous->length <= UINT64_MAX - length) {
            previous->length += length;
            return true;
        }
    }
    if (gBootInfo.memory_region_count >= DUCKOS_BOOT_MAX_MEMORY_REGIONS) return false;
    duckos_memory_region *region = &gMemoryRegions[gBootInfo.memory_region_count++];
    region->base = base;
    region->length = length;
    region->type = type;
    region->flags = 0u;
    return true;
}

static uint32_t duckos_memory_type_from_efi(uint32_t efi_type) {
    switch (efi_type) {
        case EFI_CONVENTIONAL_MEMORY:
        case EFI_BOOT_SERVICES_CODE:
        case EFI_BOOT_SERVICES_DATA:
            return DUCKOS_MEMORY_USABLE;
        case EFI_ACPI_RECLAIM_MEMORY:
            return DUCKOS_MEMORY_ACPI_RECLAIMABLE;
        case EFI_ACPI_MEMORY_NVS:
            return DUCKOS_MEMORY_ACPI_NVS;
        case EFI_UNUSABLE_MEMORY:
            return DUCKOS_MEMORY_BAD;
        case EFI_MEMORY_MAPPED_IO:
        case EFI_MEMORY_MAPPED_IO_PORT_SPACE:
            return DUCKOS_MEMORY_MMIO;
        case EFI_RESERVED_MEMORY_TYPE:
        case EFI_LOADER_CODE:
        case EFI_LOADER_DATA_TYPE:
        case EFI_RUNTIME_SERVICES_CODE:
        case EFI_RUNTIME_SERVICES_DATA:
        default:
            return DUCKOS_MEMORY_RESERVED;
    }
}

static bool append_split_region(uint64_t base, uint64_t length, uint32_t type) {
    uint64_t end;
    uint64_t framebuffer_end;
    if (length == 0u || base > UINT64_MAX - length) return false;
    end = base + length;
    if (gFramebuffer.size == 0u) return append_memory_region(base, length, type);
    if (gFramebuffer.physical_base > UINT64_MAX - gFramebuffer.size) return false;
    framebuffer_end = gFramebuffer.physical_base + gFramebuffer.size;
    if (end <= gFramebuffer.physical_base || base >= framebuffer_end) {
        return append_memory_region(base, length, type);
    }
    if (base < gFramebuffer.physical_base &&
        !append_memory_region(base, gFramebuffer.physical_base - base, type)) return false;
    const uint64_t overlap_begin =
        base > gFramebuffer.physical_base ? base : gFramebuffer.physical_base;
    const uint64_t overlap_end = end < framebuffer_end ? end : framebuffer_end;
    if (overlap_end > overlap_begin) {
        if (type != DUCKOS_MEMORY_MMIO) return false;
        if (!append_memory_region(
                overlap_begin, overlap_end - overlap_begin,
                DUCKOS_MEMORY_MMIO)) {
            return false;
        }
    }
    if (end > framebuffer_end &&
        !append_memory_region(framebuffer_end, end - framebuffer_end, type)) return false;
    return true;
}

static void sort_and_validate_memory_map(void) {
    const uint32_t count = gBootInfo.memory_region_count;
    for (uint32_t index = 1u; index < count; ++index) {
        duckos_memory_region value = gMemoryRegions[index];
        uint32_t position = index;
        while (position > 0u && gMemoryRegions[position - 1u].base > value.base) {
            gMemoryRegions[position] = gMemoryRegions[position - 1u];
            --position;
        }
        gMemoryRegions[position] = value;
    }
    for (uint32_t index = 1u; index < count; ++index) {
        const duckos_memory_region *previous = &gMemoryRegions[index - 1u];
        const duckos_memory_region *current = &gMemoryRegions[index];
        if (previous->base > UINT64_MAX - previous->length ||
            current->base < previous->base + previous->length) {
            fail("firmware memory map contains an overlap");
        }
    }
}

/*
 * GOP framebuffers are not guaranteed to have a covering EFI memory
 * descriptor. Preserve all firmware-described ranges, but add only the
 * framebuffer portions that are true gaps as explicit MMIO regions.
 * Existing EFI descriptors intersecting the framebuffer were already split
 * and classified as MMIO by append_split_region().
 */
static void ensure_framebuffer_mmio_coverage(void) {
    uint64_t framebuffer_end;
    uint64_t cursor;
    const uint32_t original_count = gBootInfo.memory_region_count;

    if (gFramebuffer.size == 0u) return;
    if (gFramebuffer.physical_base > UINT64_MAX - gFramebuffer.size) {
        fail("framebuffer physical range overflow");
    }
    framebuffer_end = gFramebuffer.physical_base + gFramebuffer.size;
    cursor = gFramebuffer.physical_base;

    for (uint32_t index = 0u; index < original_count && cursor < framebuffer_end; ++index) {
        const duckos_memory_region *region = &gMemoryRegions[index];
        uint64_t region_end;
        if (region->base > UINT64_MAX - region->length) {
            fail("memory region overflow while covering framebuffer");
        }
        region_end = region->base + region->length;
        if (region_end <= cursor) continue;

        if (region->base > cursor) {
            const uint64_t gap_end =
                region->base < framebuffer_end ? region->base : framebuffer_end;
            if (!append_memory_region(cursor, gap_end - cursor, DUCKOS_MEMORY_MMIO)) {
                fail("DuckOS Boot Info memory-map capacity exceeded by framebuffer MMIO");
            }
            cursor = gap_end;
            if (cursor >= framebuffer_end) break;
        }

        if (region->base <= cursor && region_end > cursor) {
            if (region->type != DUCKOS_MEMORY_MMIO) {
                fail("framebuffer overlaps a non-MMIO EFI memory descriptor");
            }
            cursor = region_end < framebuffer_end ? region_end : framebuffer_end;
        }
    }

    if (cursor < framebuffer_end &&
        !append_memory_region(cursor, framebuffer_end - cursor, DUCKOS_MEMORY_MMIO)) {
        fail("DuckOS Boot Info memory-map capacity exceeded by framebuffer MMIO");
    }

    sort_and_validate_memory_map();
}

static uint64_t read_max_physical_end(const EFI_MEMORY_DESCRIPTOR *descriptors,
                                      UINTN map_size, UINTN descriptor_size) {
    uint64_t maximum = 0u;
    if (descriptor_size < sizeof(EFI_MEMORY_DESCRIPTOR) || descriptor_size == 0u ||
        map_size % descriptor_size != 0u) return 0u;
    const UINTN count = map_size / descriptor_size;
    for (UINTN index = 0u; index < count; ++index) {
        const EFI_MEMORY_DESCRIPTOR *descriptor = (const EFI_MEMORY_DESCRIPTOR *)
            ((const uint8_t *)descriptors + index * descriptor_size);
        const bool mapped_ram = descriptor->type == EFI_CONVENTIONAL_MEMORY ||
            descriptor->type == EFI_BOOT_SERVICES_CODE ||
            descriptor->type == EFI_BOOT_SERVICES_DATA ||
            descriptor->type == EFI_LOADER_CODE ||
            descriptor->type == EFI_LOADER_DATA_TYPE ||
            descriptor->type == EFI_RUNTIME_SERVICES_CODE ||
            descriptor->type == EFI_RUNTIME_SERVICES_DATA ||
            descriptor->type == EFI_ACPI_RECLAIM_MEMORY ||
            descriptor->type == EFI_ACPI_MEMORY_NVS;
        if (!mapped_ram || descriptor->number_of_pages == 0u ||
            descriptor->number_of_pages > UINT64_MAX / EFI_PAGE_SIZE ||
            descriptor->physical_start >
                UINT64_MAX - descriptor->number_of_pages * EFI_PAGE_SIZE) {
            continue;
        }
        const uint64_t end = descriptor->physical_start +
            descriptor->number_of_pages * EFI_PAGE_SIZE;
        if (end > maximum) maximum = end;
    }
    return maximum;
}

static void build_memory_map(const EFI_MEMORY_DESCRIPTOR *descriptors,
                             UINTN map_size, UINTN descriptor_size) {
    gBootInfo.memory_region_count = 0u;
    if (descriptor_size < sizeof(EFI_MEMORY_DESCRIPTOR) || descriptor_size == 0u ||
        map_size % descriptor_size != 0u) {
        fail("invalid EFI memory map descriptor layout");
    }
    const UINTN count = map_size / descriptor_size;
    for (UINTN index = 0u; index < count; ++index) {
        const EFI_MEMORY_DESCRIPTOR *descriptor = (const EFI_MEMORY_DESCRIPTOR *)
            ((const uint8_t *)descriptors + index * descriptor_size);
        if (descriptor->number_of_pages == 0u ||
            descriptor->number_of_pages > UINT64_MAX / EFI_PAGE_SIZE) continue;
        const uint64_t length = descriptor->number_of_pages * EFI_PAGE_SIZE;
        if (descriptor->physical_start > UINT64_MAX - length) {
            fail("EFI memory range overflow");
        }
        if (!append_split_region(descriptor->physical_start, length,
                                 duckos_memory_type_from_efi(descriptor->type))) {
            fail("DuckOS Boot Info memory-map capacity exceeded");
        }
    }
    sort_and_validate_memory_map();
    ensure_framebuffer_mmio_coverage();
}

static uint64_t allocate_table_page(void) {
    uint64_t physical = 0u;
    EFI_STATUS status = allocate_any_pages(1u, &physical);
    if (EFI_ERROR(status)) fail("could not allocate page-table page");
    return physical;
}

static uint64_t *ensure_child_table(uint64_t *parent, uint32_t index) {
    const uint64_t entry = parent[index];
    if ((entry & PTE_PRESENT) == 0u) {
        const uint64_t child = allocate_table_page();
        parent[index] = child | PTE_PRESENT | PTE_WRITE;
        return (uint64_t *)(uintptr_t)child;
    }
    if ((entry & PTE_LARGE) != 0u) fail("page-table hierarchy collision");
    return (uint64_t *)(uintptr_t)(entry & PTE_ADDRESS_MASK);
}

static bool map_2m(uint64_t *root, uint64_t virtual_address,
                   uint64_t physical_address, uint64_t flags) {
    if (((virtual_address | physical_address) & (PAGE_2M - 1u)) != 0u) return false;
    const uint32_t pml4_index = (uint32_t)((virtual_address >> 39u) & 0x1ffu);
    const uint32_t pdpt_index = (uint32_t)((virtual_address >> 30u) & 0x1ffu);
    const uint32_t pd_index = (uint32_t)((virtual_address >> 21u) & 0x1ffu);
    uint64_t *pdpt = ensure_child_table(root, pml4_index);
    uint64_t *pd = ensure_child_table(pdpt, pdpt_index);
    if ((pd[pd_index] & PTE_PRESENT) != 0u) return false;
    pd[pd_index] = (physical_address & UINT64_C(0x000fffffffe00000)) |
        PTE_PRESENT | PTE_LARGE | flags;
    return true;
}

static bool split_2m_mapping(uint64_t *root, uint64_t virtual_address) {
    if ((virtual_address & (PAGE_2M - 1u)) != 0u) return false;
    const uint32_t pml4_index = (uint32_t)((virtual_address >> 39u) & 0x1ffu);
    const uint32_t pdpt_index = (uint32_t)((virtual_address >> 30u) & 0x1ffu);
    const uint32_t pd_index = (uint32_t)((virtual_address >> 21u) & 0x1ffu);
    uint64_t *pdpt = ensure_child_table(root, pml4_index);
    uint64_t *pd = ensure_child_table(pdpt, pdpt_index);
    const uint64_t large_entry = pd[pd_index];
    if ((large_entry & PTE_PRESENT) == 0u) return false;
    if ((large_entry & PTE_LARGE) == 0u) return true;

    const uint64_t physical_base = large_entry & UINT64_C(0x000fffffffe00000);
    const uint64_t leaf_flags = large_entry & (PTE_PRESENT | PTE_WRITE | PTE_NX);
    const uint64_t table_physical = allocate_table_page();
    uint64_t *table = (uint64_t *)(uintptr_t)table_physical;
    for (uint32_t index = 0u; index < 512u; ++index) {
        table[index] = (physical_base + (uint64_t)index * EFI_PAGE_SIZE) | leaf_flags;
    }
    pd[pd_index] = table_physical | PTE_PRESENT | PTE_WRITE;
    return true;
}

static bool set_4k_mapping(uint64_t *root, uint64_t virtual_address,
                           uint64_t physical_address, uint64_t flags) {
    if (((virtual_address | physical_address) & (EFI_PAGE_SIZE - 1u)) != 0u ||
        !split_2m_mapping(root, align_down(virtual_address, PAGE_2M))) return false;
    const uint32_t pml4_index = (uint32_t)((virtual_address >> 39u) & 0x1ffu);
    const uint32_t pdpt_index = (uint32_t)((virtual_address >> 30u) & 0x1ffu);
    const uint32_t pd_index = (uint32_t)((virtual_address >> 21u) & 0x1ffu);
    const uint32_t pt_index = (uint32_t)((virtual_address >> 12u) & 0x1ffu);
    uint64_t *pdpt = ensure_child_table(root, pml4_index);
    uint64_t *pd = ensure_child_table(pdpt, pdpt_index);
    uint64_t *pt = ensure_child_table(pd, pd_index);
    const uint64_t previous = pt[pt_index];
    if ((previous & PTE_PRESENT) == 0u ||
        (previous & PTE_ADDRESS_MASK) != (physical_address & PTE_ADDRESS_MASK)) return false;
    pt[pt_index] = (physical_address & PTE_ADDRESS_MASK) | PTE_PRESENT | flags;
    return true;
}

static bool map_4k(uint64_t *root, uint64_t virtual_address,
                   uint64_t physical_address, uint64_t flags) {
    if (((virtual_address | physical_address) & (EFI_PAGE_SIZE - 1u)) != 0u) return false;
    const uint32_t pml4_index = (uint32_t)((virtual_address >> 39u) & 0x1ffu);
    const uint32_t pdpt_index = (uint32_t)((virtual_address >> 30u) & 0x1ffu);
    const uint32_t pd_index = (uint32_t)((virtual_address >> 21u) & 0x1ffu);
    const uint32_t pt_index = (uint32_t)((virtual_address >> 12u) & 0x1ffu);
    uint64_t *pdpt = ensure_child_table(root, pml4_index);
    uint64_t *pd = ensure_child_table(pdpt, pdpt_index);
    uint64_t *pt = ensure_child_table(pd, pd_index);
    if ((pt[pt_index] & PTE_PRESENT) != 0u) return false;
    pt[pt_index] = (physical_address & PTE_ADDRESS_MASK) | PTE_PRESENT | flags;
    return true;
}

static bool map_hhdm_and_identity(uint64_t *root, uint64_t maximum_physical_end) {
    uint64_t end;
    if (!align_up(maximum_physical_end, PAGE_2M, &end) ||
        end >= UINT64_C(0x0000800000000000) ||
        DUCKBOOT_HHDM_OFFSET > UINT64_MAX - end) return false;
    for (uint64_t physical = 0u; physical < end; physical += PAGE_2M) {
        if (!map_2m(root, physical, physical, PTE_NX)) return false;
        if (!map_2m(root, DUCKBOOT_HHDM_OFFSET + physical, physical,
                    PTE_WRITE | PTE_NX)) return false;
    }
    return true;
}

static bool map_trampoline(uint64_t *root) {
    const uint64_t begin = (uint64_t)(uintptr_t)duckboot_enter_kernel;
    const uint64_t end = (uint64_t)(uintptr_t)duckboot_enter_kernel_end;
    if (end <= begin || end - begin > 4096u) return false;
    const uint64_t page = align_down(begin, EFI_PAGE_SIZE);
    if (align_down(end - 1u, EFI_PAGE_SIZE) != page) return false;
    return set_4k_mapping(root, page, page, 0u) &&
        set_4k_mapping(root, DUCKBOOT_HHDM_OFFSET + page, page, PTE_NX);
}

static bool map_kernel_segments(uint64_t *root, const duckboot_elf_image *image) {
    for (size_t index = 0u; index < image->segment_count; ++index) {
        const duckboot_elf_segment *segment = &image->segments[index];
        uint64_t virtual_end;
        uint64_t aligned_virtual_end;
        uint64_t virtual_page;
        uint64_t physical_page;
        uint64_t flags = 0u;
        if (segment->virtual_address > UINT64_MAX - segment->memory_size) return false;
        virtual_end = segment->virtual_address + segment->memory_size;
        if (!align_up(virtual_end, EFI_PAGE_SIZE, &aligned_virtual_end)) return false;
        virtual_page = align_down(segment->virtual_address, EFI_PAGE_SIZE);
        physical_page = align_down(segment->physical_address, EFI_PAGE_SIZE);
        if ((segment->flags & DUCKBOOT_ELF64_PF_W) != 0u) flags |= PTE_WRITE;
        if ((segment->flags & DUCKBOOT_ELF64_PF_X) == 0u) flags |= PTE_NX;
        while (virtual_page < aligned_virtual_end) {
            if (!map_4k(root, virtual_page, physical_page, flags)) return false;
            if ((segment->flags & DUCKBOOT_ELF64_PF_W) == 0u &&
                !set_4k_mapping(root, DUCKBOOT_HHDM_OFFSET + physical_page,
                                physical_page, PTE_NX)) return false;
            virtual_page += EFI_PAGE_SIZE;
            physical_page += EFI_PAGE_SIZE;
        }
    }
    return true;
}

static bool map_framebuffer_uncached(uint64_t *root) {
    uint64_t framebuffer_end;
    uint64_t aligned_end;
    uint64_t physical_page;
    const uint64_t cache_flags = PTE_NX | PTE_PCD | PTE_PWT;

    if (gFramebuffer.size == 0u) return true;
    if (gFramebuffer.physical_base > UINT64_MAX - gFramebuffer.size) return false;
    framebuffer_end = gFramebuffer.physical_base + gFramebuffer.size;
    if (!align_up(framebuffer_end, EFI_PAGE_SIZE, &aligned_end) ||
        DUCKBOOT_HHDM_OFFSET > UINT64_MAX - aligned_end) return false;

    physical_page = align_down(gFramebuffer.physical_base, EFI_PAGE_SIZE);
    while (physical_page < aligned_end) {
        if (!set_4k_mapping(
                root, physical_page, physical_page, cache_flags)) return false;
        if (!set_4k_mapping(
                root, DUCKBOOT_HHDM_OFFSET + physical_page, physical_page,
                cache_flags | PTE_WRITE)) return false;
        physical_page += EFI_PAGE_SIZE;
    }
    return true;
}

EFI_STATUS EFIAPI efi_main(EFI_HANDLE image_handle, EFI_SYSTEM_TABLE *system_table) {
    EFI_LOADED_IMAGE_PROTOCOL *loaded_image = NULL;
    EFI_SIMPLE_FILE_SYSTEM_PROTOCOL *simple_fs = NULL;
    EFI_FILE_PROTOCOL *root = NULL;
    duckboot_config config;
    duckboot_elf_image kernel_image;
    EFI_STATUS status;
    uint64_t maximum_physical_end;
    uint64_t kernel_stack_base;
    uint64_t *page_table_root;

    gSystemTable = system_table;
    gBootServices = system_table != NULL ? system_table->boot_services : NULL;
    gImageHandle = image_handle;
    if (gBootServices == NULL || gBootServices->handle_protocol == NULL ||
        gBootServices->allocate_pool == NULL || gBootServices->allocate_pages == NULL ||
        gBootServices->get_memory_map == NULL || gBootServices->exit_boot_services == NULL) {
        fail("required UEFI Boot Services are unavailable");
    }

    serial_init();
    serial_write("\r\nDUCKBOOT_START version=0.1.0 platform=uefi-x64\r\n");
    console_ascii("\r\nDuckBoot Core 0.1.0\r\nPreparing DuckOS...\r\n");

    if (!get_nx_support()) fail("CPU does not report NX support");
    if (!four_level_paging_active()) fail("UEFI entered with unsupported five-level paging");

    status = gBootServices->handle_protocol(
        image_handle, (EFI_GUID *)&gLoadedImageGuid, (void **)&loaded_image);
    if (EFI_ERROR(status) || loaded_image == NULL || loaded_image->device_handle == NULL) {
        fail("could not locate the loaded-image device");
    }
    status = gBootServices->handle_protocol(
        loaded_image->device_handle, (EFI_GUID *)&gSimpleFileSystemGuid, (void **)&simple_fs);
    if (EFI_ERROR(status) || simple_fs == NULL || simple_fs->open_volume == NULL) {
        fail("boot volume does not expose the UEFI Simple File System protocol");
    }
    status = simple_fs->open_volume(simple_fs, &root);
    if (EFI_ERROR(status) || root == NULL || root->open == NULL || root->read == NULL) {
        fail("could not open the boot volume root directory");
    }

    if (!load_config(root, &config)) fail("duckboot.cfg is invalid or incomplete");
    copy_bytes(gCommandLine, config.command_line, sizeof(gCommandLine));
    gCommandLine[sizeof(gCommandLine) - 1u] = '\0';
    status = load_kernel(root, &config, &kernel_image);
    if (EFI_ERROR(status)) fail("kernel image could not be loaded");
    serial_write("ELF64_OK segments=validated loaded=physical\r\n");
    console_ascii("ELF64 kernel loaded\r\n");

    if (!discover_framebuffer()) fail("UEFI GOP returned invalid framebuffer metadata");
    status = allocate_any_pages(DUCKBOOT_STACK_PAGES, &kernel_stack_base);
    if (EFI_ERROR(status)) fail("could not allocate the DuckOS kernel stack");
    gKernelStackTop = kernel_stack_base + DUCKBOOT_STACK_PAGES * EFI_PAGE_SIZE;

    UINTN map_size = sizeof(gMemoryMapBuffer);
    UINTN map_key = 0u;
    UINTN descriptor_size = 0u;
    uint32_t descriptor_version = 0u;
    status = gBootServices->get_memory_map(
        &map_size, (EFI_MEMORY_DESCRIPTOR *)gMemoryMapBuffer,
        &map_key, &descriptor_size, &descriptor_version);
    if (EFI_ERROR(status)) fail("initial GetMemoryMap failed");
    if (descriptor_version != 1u) fail("unsupported EFI memory descriptor version");
    maximum_physical_end = read_max_physical_end(
        (const EFI_MEMORY_DESCRIPTOR *)gMemoryMapBuffer, map_size, descriptor_size);
    if (maximum_physical_end == 0u) fail("firmware memory map contains no mappable RAM");
    if (gFramebuffer.size != 0u &&
        gFramebuffer.physical_base <= UINT64_MAX - gFramebuffer.size &&
        gFramebuffer.physical_base + gFramebuffer.size > maximum_physical_end) {
        maximum_physical_end = gFramebuffer.physical_base + gFramebuffer.size;
    }
    if (maximum_physical_end >= UINT64_C(0x0000800000000000)) {
        fail("physical address range exceeds the DuckOS HHDM window");
    }

    status = allocate_any_pages(1u, &gPageTableRoot);
    if (EFI_ERROR(status)) fail("could not allocate the top-level page table");
    page_table_root = (uint64_t *)(uintptr_t)gPageTableRoot;
    if (!map_hhdm_and_identity(page_table_root, maximum_physical_end)) {
        fail("could not construct identity and HHDM mappings");
    }
    if (!map_trampoline(page_table_root)) {
        fail("could not isolate the executable transition trampoline");
    }
    if (!map_kernel_segments(page_table_root, &kernel_image)) {
        fail("could not map ELF64 kernel segments with requested permissions");
    }
    if (!map_framebuffer_uncached(page_table_root)) {
        fail("could not create a consistent uncached GOP framebuffer mapping");
    }

    zero_bytes(&gBootInfo, sizeof(gBootInfo));
    gBootInfo.struct_size = (uint32_t)sizeof(gBootInfo);
    gBootInfo.version = DUCKOS_BOOT_INFO_VERSION;
    gBootInfo.flags = 1u;
    gBootInfo.kernel_phys_base = kernel_image.physical_base;
    gBootInfo.kernel_size = kernel_image.physical_end - kernel_image.physical_base;
    gBootInfo.framebuffer_phys_base = gFramebuffer.physical_base;
    gBootInfo.framebuffer_size = gFramebuffer.size;
    gBootInfo.framebuffer_width = gFramebuffer.width;
    gBootInfo.framebuffer_height = gFramebuffer.height;
    gBootInfo.framebuffer_pitch = gFramebuffer.pitch;
    gBootInfo.framebuffer_bpp = gFramebuffer.bpp;

    zero_bytes(&gHandoff, sizeof(gHandoff));
    gHandoff.magic = DUCKBOOT_HANDOFF_MAGIC;
    gHandoff.struct_size = (uint32_t)sizeof(gHandoff);
    gHandoff.version = DUCKBOOT_HANDOFF_VERSION;
    gHandoff.boot_info_virtual =
        DUCKBOOT_HHDM_OFFSET + (uint64_t)(uintptr_t)&gBootInfo;
    gHandoff.memory_map_virtual =
        DUCKBOOT_HHDM_OFFSET + (uint64_t)(uintptr_t)gMemoryRegions;
    gHandoff.hhdm_offset = DUCKBOOT_HHDM_OFFSET;
    gHandoff.command_line_virtual =
        DUCKBOOT_HHDM_OFFSET + (uint64_t)(uintptr_t)gCommandLine;
    if (gFramebuffer.size != 0u) {
        gHandoff.framebuffer_virtual =
            DUCKBOOT_HHDM_OFFSET + gFramebuffer.physical_base;
        gHandoff.red_mask_size = gFramebuffer.red_size;
        gHandoff.red_mask_shift = gFramebuffer.red_shift;
        gHandoff.green_mask_size = gFramebuffer.green_size;
        gHandoff.green_mask_shift = gFramebuffer.green_shift;
        gHandoff.blue_mask_size = gFramebuffer.blue_size;
        gHandoff.blue_mask_shift = gFramebuffer.blue_shift;
    }

    map_size = sizeof(gMemoryMapBuffer);
    status = gBootServices->get_memory_map(
        &map_size, (EFI_MEMORY_DESCRIPTOR *)gMemoryMapBuffer,
        &map_key, &descriptor_size, &descriptor_version);
    if (EFI_ERROR(status)) fail("final GetMemoryMap failed");
    if (descriptor_version != 1u) fail("unsupported EFI memory descriptor version");
    build_memory_map((EFI_MEMORY_DESCRIPTOR *)gMemoryMapBuffer, map_size, descriptor_size);
    const duckos_boot_info_status boot_info_status =
        duckos_boot_info_validate(&gBootInfo, gMemoryRegions,
                                  gBootInfo.memory_region_count);
    if (boot_info_status != DUCKOS_BOOT_INFO_OK) {
        serial_write("DUCKBOOT_BOOTINFO_REJECT status=");
        serial_write(duckos_boot_info_status_name(boot_info_status));
        serial_write(" regions=");
        serial_hex(gBootInfo.memory_region_count);
        serial_write(" kernel_phys=");
        serial_hex(gBootInfo.kernel_phys_base);
        serial_write(" kernel_bytes=");
        serial_hex(gBootInfo.kernel_size);
        serial_write(" framebuffer_phys=");
        serial_hex(gBootInfo.framebuffer_phys_base);
        serial_write(" framebuffer_bytes=");
        serial_hex(gBootInfo.framebuffer_size);
        serial_write("\r\n");
        for (uint32_t index = 0u; index < gBootInfo.memory_region_count; ++index) {
            serial_write("DUCKBOOT_MEMORY_REGION type=");
            serial_hex(gMemoryRegions[index].type);
            serial_write(" base=");
            serial_hex(gMemoryRegions[index].base);
            serial_write(" size=");
            serial_hex(gMemoryRegions[index].length);
            serial_write("\r\n");
        }
        fail("constructed DuckOS Boot Info v1 did not validate");
    }

    status = gBootServices->exit_boot_services(gImageHandle, map_key);
    if (EFI_ERROR(status)) {
        map_size = sizeof(gMemoryMapBuffer);
        status = gBootServices->get_memory_map(
            &map_size, (EFI_MEMORY_DESCRIPTOR *)gMemoryMapBuffer,
            &map_key, &descriptor_size, &descriptor_version);
        if (EFI_ERROR(status)) fail("GetMemoryMap retry failed");
        if (descriptor_version != 1u) fail("unsupported EFI memory descriptor version");
        build_memory_map((EFI_MEMORY_DESCRIPTOR *)gMemoryMapBuffer, map_size, descriptor_size);
        if (duckos_boot_info_validate(&gBootInfo, gMemoryRegions,
                                      gBootInfo.memory_region_count) != DUCKOS_BOOT_INFO_OK) {
            fail("Boot Info v1 invalid after memory-map refresh");
        }
        status = gBootServices->exit_boot_services(gImageHandle, map_key);
        if (EFI_ERROR(status)) fail("ExitBootServices retry failed");
    }

    serial_write("DUCKBOOT_HANDOFF_READY v1\r\n");
    duckboot_enter_kernel(
        kernel_image.entry,
        DUCKBOOT_HHDM_OFFSET + (uint64_t)(uintptr_t)&gHandoff,
        DUCKBOOT_HHDM_OFFSET + gKernelStackTop,
        gPageTableRoot);
}
