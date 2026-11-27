ROOT := $(abspath .)
BUILD := $(ROOT)/../build/native
PYTHON ?= python3
CC = clang
LD = ld.lld

.PHONY: all kernel initramfs compositor shell iso test clean
all: kernel initramfs

kernel:
	$(MAKE) -C kernel CC=$(CC) LD=$(LD)
	mkdir -p $(BUILD)
	cp kernel/build/kernel.elf $(BUILD)/kernel.elf

initramfs:
	mkdir -p $(BUILD)
	$(PYTHON) initramfs/mkinitramfs.py --root initramfs/root --output $(BUILD)/initramfs.cpio

compositor:
	if [ -d desktop/compositor/build/meson-private ]; then \
		meson setup --reconfigure desktop/compositor/build desktop/compositor; \
	else \
		meson setup desktop/compositor/build desktop/compositor; \
	fi
	meson compile -C desktop/compositor/build

shell:
	if [ -d desktop/shell/build/meson-private ]; then \
		meson setup --reconfigure desktop/shell/build desktop/shell; \
	else \
		meson setup desktop/shell/build desktop/shell; \
	fi
	meson compile -C desktop/shell/build

iso:
	bash scripts/build-iso.sh

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	$(MAKE) -C kernel clean
	rm -rf $(BUILD) desktop/compositor/build desktop/shell/build
