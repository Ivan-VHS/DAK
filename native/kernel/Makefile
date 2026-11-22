CC ?= clang
LD ?= ld.lld
BUILD_DIR := build
INCLUDES := -Iinclude
CFLAGS := --target=x86_64-unknown-none-elf -std=c11 -O2 -Wall -Wextra -Werror \
	-ffreestanding -fno-stack-protector -fno-pic -fno-pie \
	-fno-asynchronous-unwind-tables -fno-unwind-tables \
	-mno-red-zone -mcmodel=kernel -mno-mmx -mno-sse -mno-sse2
LDFLAGS := -nostdlib -static -no-pie -z max-page-size=0x1000 -T linker.ld

SOURCES := src/kernel.c src/serial.c
OBJECTS := $(patsubst src/%.c,$(BUILD_DIR)/%.o,$(SOURCES))

.PHONY: all clean
all: $(BUILD_DIR)/kernel.elf

$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/%.o: src/%.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

$(BUILD_DIR)/kernel.elf: $(OBJECTS) linker.ld
	$(LD) $(LDFLAGS) $(OBJECTS) -o $@

clean:
	rm -rf $(BUILD_DIR)
