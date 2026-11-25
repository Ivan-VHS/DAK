#ifndef DUCKBOOT_CONFIG_H
#define DUCKBOOT_CONFIG_H

#include <stddef.h>
#include <stdint.h>

#define DUCKBOOT_CONFIG_KERNEL_CAPACITY 128u
#define DUCKBOOT_CONFIG_LABEL_CAPACITY 32u
#define DUCKBOOT_CONFIG_CMDLINE_CAPACITY 256u

typedef enum duckboot_config_status {
    DUCKBOOT_CONFIG_OK = 0,
    DUCKBOOT_CONFIG_INVALID_ARGUMENT = -1,
    DUCKBOOT_CONFIG_TOO_LARGE = -2,
    DUCKBOOT_CONFIG_SYNTAX_ERROR = -3,
    DUCKBOOT_CONFIG_UNKNOWN_KEY = -4,
    DUCKBOOT_CONFIG_DUPLICATE_KEY = -5,
    DUCKBOOT_CONFIG_INVALID_VALUE = -6,
    DUCKBOOT_CONFIG_MISSING_KERNEL = -7
} duckboot_config_status;

typedef struct duckboot_config {
    uint32_t timeout_seconds;
    char label[DUCKBOOT_CONFIG_LABEL_CAPACITY];
    char kernel_path[DUCKBOOT_CONFIG_KERNEL_CAPACITY];
    char command_line[DUCKBOOT_CONFIG_CMDLINE_CAPACITY];
} duckboot_config;

duckboot_config_status duckboot_config_parse(
    const char *data,
    size_t length,
    duckboot_config *config
);

const char *duckboot_config_status_name(duckboot_config_status status);

#endif
