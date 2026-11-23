#include "duckos/kernel.h"
#include "duckos/arch_x86_64.h"

#define COM1 0x3f8u

void duckos_serial_init(void) {
    duckos_outb(COM1 + 1u, 0x00u);
    duckos_outb(COM1 + 3u, 0x80u);
    duckos_outb(COM1 + 0u, 0x03u);
    duckos_outb(COM1 + 1u, 0x00u);
    duckos_outb(COM1 + 3u, 0x03u);
    duckos_outb(COM1 + 2u, 0xc7u);
    duckos_outb(COM1 + 4u, 0x0bu);
}

static void serial_char(char value) {
    for (uint32_t retry = 0u; retry < 1000000u; ++retry) {
        if ((duckos_inb(COM1 + 5u) & 0x20u) != 0u) {
            duckos_outb(COM1, (uint8_t)value);
            return;
        }
    }
}

void duckos_serial_write(const char *text) {
    if (text == NULL) return;
    while (*text != '\0') {
        if (*text == '\n') serial_char('\r');
        serial_char(*text++);
    }
}

void duckos_serial_hex(uint64_t value) {
    static const char digits[] = "0123456789abcdef";
    duckos_serial_write("0x");
    for (int shift = 60; shift >= 0; shift -= 4)
        serial_char(digits[(value >> (uint32_t)shift) & 0x0fu]);
}

void duckos_serial_u64(uint64_t value) {
    char digits[21];
    uint32_t length = 0u;
    if (value == 0u) {
        serial_char('0');
        return;
    }
    while (value != 0u && length < sizeof digits) {
        digits[length++] = (char)('0' + (value % 10u));
        value /= 10u;
    }
    while (length != 0u) serial_char(digits[--length]);
}
