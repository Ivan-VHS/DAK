#include <stddef.h>

void *memset(void *destination, int value, size_t count) {
    unsigned char *bytes = (unsigned char *)destination;
    for (size_t index = 0u; index < count; ++index) bytes[index] = (unsigned char)value;
    return destination;
}

void *memcpy(void *destination, const void *source, size_t count) {
    unsigned char *out = (unsigned char *)destination;
    const unsigned char *in = (const unsigned char *)source;
    for (size_t index = 0u; index < count; ++index) out[index] = in[index];
    return destination;
}

void *memmove(void *destination, const void *source, size_t count) {
    unsigned char *out = (unsigned char *)destination;
    const unsigned char *in = (const unsigned char *)source;
    if (out < in) {
        for (size_t index = 0u; index < count; ++index) out[index] = in[index];
    } else if (out > in) {
        while (count != 0u) {
            --count;
            out[count] = in[count];
        }
    }
    return destination;
}

int memcmp(const void *left, const void *right, size_t count) {
    const unsigned char *a = (const unsigned char *)left;
    const unsigned char *b = (const unsigned char *)right;
    for (size_t index = 0u; index < count; ++index) {
        if (a[index] != b[index]) return a[index] < b[index] ? -1 : 1;
    }
    return 0;
}
