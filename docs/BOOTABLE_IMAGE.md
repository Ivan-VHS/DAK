# DuckOS x86_64 bootable stage-0 image

**Status:** experimental bootable foundation, not a complete operating system.  
**Architecture:** x86_64, Limine protocol v12.11.1, BIOS and UEFI hybrid ISO.  
**Kernel ownership:** DuckOS owns the freestanding entry point, memory-map adapter, boot-info validation and stage-0 framebuffer/serial output. Limine is a separately licensed third-party bootloader.

## What this image actually boots

The image starts a native DuckOS ELF kernel through Limine. The entry point checks protocol base revision 6, receives bootloader and firmware identity, HHDM offset, executable physical/virtual base, framebuffer and memory map, converts those values into DuckOS Boot Info v1, validates reserved kernel/initramfs ranges and MMIO framebuffer ownership, writes serial diagnostics, and draws a small native screen when a 32-bit RGB framebuffer is available. It stops after reporting DUCKOS_BOOT_OK stage=0.

The existing .rpr kernel files remain the policy/reference layer. Reaper's current native compiler is not yet a freestanding kernel compiler, so this first privileged entry bridge is C11. The current Reaper AOT slice is not claimed to compile the kernel.

## Build

On Linux x86_64 install gcc, binutils, curl, tar, xorriso and sha256sum.

    boot/build-iso.sh

The script downloads the pinned Limine binary release, checks its SHA-256 before use, compiles the freestanding kernel, validates ELF class/architecture/request section, creates a hybrid BIOS/UEFI ISO and writes a SHA-256 sidecar.

    boot/build-iso.sh --work-dir build/duckos-boot --output build/DuckOS-Stage0-x86_64.iso

CMake integration:

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --target duckos-boot-iso

## Verify in QEMU

Install qemu-system-x86 and OVMF firmware, then run:

    boot/test-qemu.sh --iso build/DuckOS-Stage0-x86_64.iso --ovmf-code /usr/share/OVMF/OVMF_CODE.fd --ovmf-vars /usr/share/OVMF/OVMF_VARS.fd

The test boots through BIOS and UEFI and requires the serial marker DUCKOS_BOOT_OK stage=0. The kernel halts after the marker by design; QEMU is stopped by the test timeout.

GitHub Actions builds the same ISO, runs both emulator checks and uploads the ISO and checksum as the DuckOS-Stage0-x86_64-ISO workflow artifact.

## Pinned third-party input and attribution

The build pins Limine v12.11.1 binary archive by SHA-256 in boot/limine-toolchain.lock. The protocol header is a byte-for-byte copy of limine-protocol/include/limine.h, pinned to the protocol repository commit recorded in the lock file. Its upstream SPDX 0BSD notice is retained. The Limine COPYING terms are placed inside the ISO.

Upstream references: https://github.com/Limine-Bootloader/limine-protocol/blob/trunk/PROTOCOL.md ; https://github.com/Limine-Bootloader/Limine/blob/v12.11.1/INSTALL.md ; https://github.com/Limine-Bootloader/Limine/blob/v12.11.1/USAGE.md

## Deliberate stage-0 limits

This image does not yet provide a physical/virtual page allocator, page-table manager or kernel heap; IDT, APIC/PIC, interrupt handlers, timer or preemptive context switching; processes, threads, syscalls, user mode, scheduler execution or IPC runtime; ACPI/PCI/USB drivers, DMA or production driver manager; filesystem, init/service supervisor, package manager or persistence; native Mora compositor, window manager, GPU acceleration, audio stack or user applications; Secure Boot signing/enrolment, authenticated updates, rollback, installer or production recovery.

The existing duckos/kernel/*.rpr files describe policies/contracts; they do not execute those mechanisms. This is a real firmware-bootable stage-0 milestone, not a finished desktop OS.
