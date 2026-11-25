#include "duckboot/config.h"

#include <stdbool.h>

#define DUCKBOOT_CONFIG_MAX_BYTES 4096u
#define DUCKBOOT_CONFIG_MAX_TIMEOUT 30u

static bool is_space(char value) {
    return value == ' ' || value == '\t';
}

static bool is_label_char(char value) {
    return (value >= 'a' && value <= 'z') ||
        (value >= 'A' && value <= 'Z') ||
        (value >= '0' && value <= '9') || value == '-' || value == '_';
}

static bool path_is_safe(const char *value) {
    size_t length = 0u;
    if (value[0] != '/' && value[0] != '\\') return false;
    while (value[length] != '\0') {
        if (value[length] == ':' || value[length] < 0x20) return false;
        if (value[length] == '.' && value[length + 1u] == '.') return false;
        ++length;
    }
    return length > 1u;
}

static bool copy_value(char *destination, size_t capacity,
                       const char *source, size_t length) {
    if (length == 0u || length >= capacity) return false;
    for (size_t index = 0u; index < length; ++index) {
        if (source[index] < 0x20 || source[index] == 0x7fu) return false;
        destination[index] = source[index];
    }
    destination[length] = '\0';
    return true;
}

static bool parse_timeout(const char *value, size_t length, uint32_t *timeout) {
    uint32_t result = 0u;
    if (length == 0u || timeout == NULL) return false;
    for (size_t index = 0u; index < length; ++index) {
        if (value[index] < '0' || value[index] > '9') return false;
        const uint32_t digit = (uint32_t)(value[index] - '0');
        if (result > (DUCKBOOT_CONFIG_MAX_TIMEOUT - digit) / 10u) return false;
        result = result * 10u + digit;
    }
    *timeout = result;
    return true;
}

duckboot_config_status duckboot_config_parse(
    const char *data,
    size_t length,
    duckboot_config *config
) {
    duckboot_config parsed = {0};
    parsed.timeout_seconds = 5u;
    bool seen_timeout = false;
    bool seen_label = false;
    bool seen_kernel = false;
    bool seen_command_line = false;
    size_t offset = 0u;

    if (data == NULL || config == NULL) return DUCKBOOT_CONFIG_INVALID_ARGUMENT;
    if (length > DUCKBOOT_CONFIG_MAX_BYTES) return DUCKBOOT_CONFIG_TOO_LARGE;

    while (offset < length) {
        size_t line_start = offset;
        size_t line_end;
        size_t first;
        size_t last;
        size_t equal = SIZE_MAX;

        while (offset < length && data[offset] != '\n') ++offset;
        line_end = offset;
        if (offset < length) ++offset;
        if (line_end > line_start && data[line_end - 1u] == '\r') --line_end;

        first = line_start;
        last = line_end;
        while (first < last && is_space(data[first])) ++first;
        while (last > first && is_space(data[last - 1u])) --last;
        if (first == last || data[first] == '#') continue;

        for (size_t index = first; index < last; ++index) {
            if (data[index] == '=') { equal = index; break; }
        }
        if (equal == SIZE_MAX) return DUCKBOOT_CONFIG_SYNTAX_ERROR;
        size_t key_end = equal;
        size_t value_start = equal + 1u;
        while (key_end > first && is_space(data[key_end - 1u])) --key_end;
        while (value_start < last && is_space(data[value_start])) ++value_start;
        size_t value_end = last;
        while (value_end > value_start && is_space(data[value_end - 1u])) --value_end;
        if (key_end == first || value_start == value_end) return DUCKBOOT_CONFIG_SYNTAX_ERROR;

        const size_t key_length = key_end - first;
        const size_t value_length = value_end - value_start;
        if (key_length == 7u && data[first] == 't' &&
            data[first + 1u] == 'i' && data[first + 2u] == 'm' &&
            data[first + 3u] == 'e' && data[first + 4u] == 'o' &&
            data[first + 5u] == 'u' && data[first + 6u] == 't') {
            if (seen_timeout) return DUCKBOOT_CONFIG_DUPLICATE_KEY;
            if (!parse_timeout(data + value_start, value_length, &parsed.timeout_seconds)) {
                return DUCKBOOT_CONFIG_INVALID_VALUE;
            }
            seen_timeout = true;
        } else if (key_length == 5u && data[first] == 'l' &&
                   data[first + 1u] == 'a' && data[first + 2u] == 'b' &&
                   data[first + 3u] == 'e' && data[first + 4u] == 'l') {
            if (seen_label) return DUCKBOOT_CONFIG_DUPLICATE_KEY;
            if (!copy_value(parsed.label, sizeof(parsed.label), data + value_start, value_length)) {
                return DUCKBOOT_CONFIG_INVALID_VALUE;
            }
            for (size_t index = 0u; parsed.label[index] != '\0'; ++index) {
                if (!is_label_char(parsed.label[index])) return DUCKBOOT_CONFIG_INVALID_VALUE;
            }
            seen_label = true;
        } else if (key_length == 6u && data[first] == 'k' &&
                   data[first + 1u] == 'e' && data[first + 2u] == 'r' &&
                   data[first + 3u] == 'n' && data[first + 4u] == 'e' &&
                   data[first + 5u] == 'l') {
            if (seen_kernel) return DUCKBOOT_CONFIG_DUPLICATE_KEY;
            if (!copy_value(parsed.kernel_path, sizeof(parsed.kernel_path),
                            data + value_start, value_length) ||
                !path_is_safe(parsed.kernel_path)) {
                return DUCKBOOT_CONFIG_INVALID_VALUE;
            }
            seen_kernel = true;
        } else if (key_length == 7u && data[first] == 'c' &&
                   data[first + 1u] == 'm' && data[first + 2u] == 'd' &&
                   data[first + 3u] == 'l' && data[first + 4u] == 'i' &&
                   data[first + 5u] == 'n' && data[first + 6u] == 'e') {
            if (seen_command_line) return DUCKBOOT_CONFIG_DUPLICATE_KEY;
            if (!copy_value(parsed.command_line, sizeof(parsed.command_line),
                            data + value_start, value_length)) {
                return DUCKBOOT_CONFIG_INVALID_VALUE;
            }
            seen_command_line = true;
        } else {
            return DUCKBOOT_CONFIG_UNKNOWN_KEY;
        }
    }

    if (!seen_kernel) return DUCKBOOT_CONFIG_MISSING_KERNEL;
    if (!seen_label) {
        const char default_label[] = "DuckOS";
        for (size_t index = 0u; index < sizeof(default_label); ++index) {
            parsed.label[index] = default_label[index];
        }
    }
    *config = parsed;
    return DUCKBOOT_CONFIG_OK;
}

const char *duckboot_config_status_name(duckboot_config_status status) {
    switch (status) {
        case DUCKBOOT_CONFIG_OK: return "ok";
        case DUCKBOOT_CONFIG_INVALID_ARGUMENT: return "invalid-argument";
        case DUCKBOOT_CONFIG_TOO_LARGE: return "too-large";
        case DUCKBOOT_CONFIG_SYNTAX_ERROR: return "syntax-error";
        case DUCKBOOT_CONFIG_UNKNOWN_KEY: return "unknown-key";
        case DUCKBOOT_CONFIG_DUPLICATE_KEY: return "duplicate-key";
        case DUCKBOOT_CONFIG_INVALID_VALUE: return "invalid-value";
        case DUCKBOOT_CONFIG_MISSING_KERNEL: return "missing-kernel";
        default: return "unknown";
    }
}
