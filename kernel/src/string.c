#include <stddef.h>
#include <stdint.h>

void *memcpy(void *destination, const void *source, size_t count) {
    uint8_t *out = (uint8_t *)destination;
    const uint8_t *in = (const uint8_t *)source;
    for (size_t i = 0u; i < count; ++i) out[i] = in[i];
    return destination;
}

void *memmove(void *destination, const void *source, size_t count) {
    uint8_t *out = (uint8_t *)destination;
    const uint8_t *in = (const uint8_t *)source;
    if (out <= in) {
        for (size_t i = 0u; i < count; ++i) out[i] = in[i];
    } else {
        while (count != 0u) {
            --count;
            out[count] = in[count];
        }
    }
    return destination;
}

void *memset(void *destination, int value, size_t count) {
    uint8_t *out = (uint8_t *)destination;
    for (size_t i = 0u; i < count; ++i) out[i] = (uint8_t)value;
    return destination;
}

int memcmp(const void *left, const void *right, size_t count) {
    const uint8_t *a = (const uint8_t *)left;
    const uint8_t *b = (const uint8_t *)right;
    for (size_t i = 0u; i < count; ++i) {
        if (a[i] != b[i]) return a[i] < b[i] ? -1 : 1;
    }
    return 0;
}

size_t strlen(const char *text) {
    size_t length = 0u;
    if (text == NULL) return 0u;
    while (text[length] != '\0') ++length;
    return length;
}

int strcmp(const char *left, const char *right) {
    while (*left != '\0' && *left == *right) {
        ++left;
        ++right;
    }
    return (int)(uint8_t)*left - (int)(uint8_t)*right;
}
