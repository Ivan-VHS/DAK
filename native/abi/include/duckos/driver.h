#ifndef DUCKOS_DRIVER_ABI_H
#define DUCKOS_DRIVER_ABI_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define DUCKOS_DRIVER_ABI_MAJOR 1u
#define DUCKOS_DRIVER_ABI_MINOR 0u
#define DUCKOS_DRIVER_NAME_MAX 32u

#define DUCKOS_DRIVER_CAP_BLOCK  (1ull << 0)
#define DUCKOS_DRIVER_CAP_CHAR   (1ull << 1)
#define DUCKOS_DRIVER_CAP_NET    (1ull << 2)
#define DUCKOS_DRIVER_CAP_INPUT  (1ull << 3)
#define DUCKOS_DRIVER_CAP_GPU    (1ull << 4)
#define DUCKOS_DRIVER_CAP_AUDIO  (1ull << 5)

enum duckos_driver_status {
    DUCKOS_DRIVER_OK = 0,
    DUCKOS_DRIVER_E_INVALID = -1,
    DUCKOS_DRIVER_E_UNSUPPORTED = -2,
    DUCKOS_DRIVER_E_BUSY = -3,
    DUCKOS_DRIVER_E_IO = -4,
    DUCKOS_DRIVER_E_TIMEOUT = -5,
    DUCKOS_DRIVER_E_NO_DEVICE = -6
};

struct duckos_device_id {
    uint16_t bus_type;
    uint16_t vendor_id;
    uint16_t device_id;
    uint16_t subsystem_vendor_id;
    uint16_t subsystem_device_id;
    uint32_t class_code;
    uint32_t revision;
};

struct duckos_driver_context {
    uint32_t struct_size;
    uint16_t abi_major;
    uint16_t abi_minor;
    uint64_t device_handle;
    uint64_t capabilities;
    const struct duckos_device_id *device_id;
};

struct duckos_driver_descriptor_v1 {
    uint32_t struct_size;
    uint16_t abi_major;
    uint16_t abi_minor;
    char name[DUCKOS_DRIVER_NAME_MAX];
    uint64_t capabilities;
    int32_t (*probe)(const struct duckos_device_id *device);
    int32_t (*attach)(const struct duckos_driver_context *context);
    void (*detach)(uint64_t device_handle);
};

struct duckos_io_request_v1 {
    uint32_t struct_size;
    uint32_t operation;
    uint64_t offset;
    uint64_t buffer_token;
    uint64_t buffer_length;
    uint32_t flags;
    uint32_t reserved;
};

struct duckos_io_result_v1 {
    uint32_t struct_size;
    int32_t status;
    uint64_t bytes_transferred;
};

typedef const struct duckos_driver_descriptor_v1 *
    (*duckos_driver_entry_v1)(uint32_t requested_major, uint32_t requested_minor);

#ifdef __cplusplus
}
#endif

#endif
