#include "serial.h"

#define COM1 0x3F8

static inline void outb(uint16_t port, uint8_t value)
{
    __asm__ volatile ("outb %0, %1" : : "a"(value), "Nd"(port));
}

static inline uint8_t inb(uint16_t port)
{
    uint8_t value;
    __asm__ volatile ("inb %1, %0" : "=a"(value) : "Nd"(port));
    return value;
}

static int transmitter_ready(void)
{
    return (inb(COM1 + 5) & 0x20) != 0;
}

void serial_init(void)
{
    outb(COM1 + 1, 0x00);
    outb(COM1 + 3, 0x80);
    outb(COM1 + 0, 0x03);
    outb(COM1 + 1, 0x00);
    outb(COM1 + 3, 0x03);
    outb(COM1 + 2, 0xC7);
    outb(COM1 + 4, 0x0B);
}

static void serial_putc(char ch)
{
    while (!transmitter_ready()) {
        __asm__ volatile ("pause");
    }

    outb(COM1, (uint8_t)ch);
}

void serial_write(const char *text)
{
    if (text == 0) {
        return;
    }

    while (*text != '\0') {
        if (*text == '\n') {
            serial_putc('\r');
        }

        serial_putc(*text++);
    }
}

void serial_write_hex(uint64_t value)
{
    static const char digits[] = "0123456789abcdef";
    char buffer[16];
    unsigned int length = 0;

    do {
        buffer[length++] = digits[value & 0x0f];
        value >>= 4;
    } while (value != 0 && length < sizeof(buffer));

    serial_write("0x");

    while (length > 0) {
        serial_putc(buffer[--length]);
    }
}

void serial_write_dec(uint64_t value)
{
    char buffer[20];
    unsigned int length = 0;

    do {
        buffer[length++] = (char)('0' + (value % 10));
        value /= 10;
    } while (value != 0 && length < sizeof(buffer));

    while (length > 0) {
        serial_putc(buffer[--length]);
    }
}
