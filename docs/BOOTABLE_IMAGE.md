# DuckOS x86_64 bootable Stage 1 image

**Status:** experimental native kernel foundation, not a complete operating system.  
**Architecture:** x86_64, Limine protocol v12.11.1, BIOS and UEFI hybrid ISO.  
**Kernel ownership:** DuckOS owns the freestanding entry point, memory-map adapter, Boot Info validation, early physical-frame allocator and framebuffer/serial output. Limine is a separately licensed third-party bootloader.

## What this image actually boots

The image starts a native DuckOS ELF kernel through Limine. Early in the entry path, DuckOS disables maskable interrupts and installs an IDT for CPU exception vectors 0–31 using the active code selector. The entry point then validates protocol base revision 6, firmware identity, HHDM, executable physical/virtual base, framebuffer and memory map. It converts firmware memory regions to DuckOS Boot Info v1 and verifies that the kernel and framebuffer are covered by the expected reserved/MMIO ranges.

After that validation, the kernel initializes a native, freestanding, single-core bootstrap physical-frame allocator. It exposes only page-aligned 4 KiB frames from memory-map regions typed **USABLE**, excludes addresses below 1 MiB, allocates one frame and clears that frame through the Limine-provided HHDM mapping. Reserved, ACPI, MMIO and bad-memory ranges are never allocator inputs. The kernel reports available/allocated page counts and emits the `exceptions=0..31 idt=loaded maskable_interrupts=disabled` marker followed by `DUCKOS_BOOT_OK stage=1`. CPU exceptions are logged to COM1 with their vector, error code, RIP and (for page faults) CR2; when a 32-bit RGB framebuffer is available, a fatal banner is drawn before the kernel halts.

This allocator is intentionally monotonic: it does not free pages, merge ranges, reclaim memory, construct page tables or provide a heap. It is a first native memory primitive, not a finished virtual-memory subsystem.

The existing .rpr kernel files remain the policy/reference layer. Reaper's current native compiler is not yet a freestanding kernel compiler, so the privileged platform entry bridge is C11. The current Reaper AOT slice is not claimed to compile the kernel.

## Build

On Linux x86_64 install gcc, binutils, curl, tar, xorriso and sha256sum.

    boot/build-iso.sh

The script downloads the pinned Limine binary release, checks its SHA-256 before use, compiles the freestanding DuckOS kernel and allocator, validates the ELF class/architecture/request section, creates a hybrid BIOS/UEFI ISO and writes a SHA-256 sidecar.

    boot/build-iso.sh --work-dir build/duckos-boot --output build/DuckOS-Stage1-x86_64.iso

CMake integration:

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
    cmake --build build --target duckos-boot-iso
    ctest --test-dir build --output-on-failure

## Verify in QEMU

Install qemu-system-x86 and OVMF firmware, then run:

    boot/test-qemu.sh --iso build/DuckOS-Stage1-x86_64.iso --ovmf-code /usr/share/OVMF/OVMF_CODE.fd --ovmf-vars /usr/share/OVMF/OVMF_VARS.fd

The test boots through BIOS and UEFI and requires both the IDT-installed marker and `DUCKOS_BOOT_OK stage=1` in the serial log. This verifies that `lidt` was reached; it does not inject a fault to exercise every exception handler. The kernel halts after the marker by design; QEMU is stopped by the test timeout.

GitHub Actions builds the same ISO, runs Boot Info and frame-allocator CTests, boots the image in BIOS and OVMF UEFI, and uploads the ISO, checksum and serial logs.

## Allocator contract and tests

The host-testable Boot Info, frame allocator and IDT descriptor contracts are compiled by CMake and run through CTest. The IDT tests verify descriptor size/offsets, a full 64-bit handler round trip, IST bounds and exact exception-frame offsets. The host-testable allocator accepts only a sorted, non-overlapping memory map with bounded region count and non-overflowing ranges. It checks page alignment and arithmetic, trims partial pages, respects a caller-supplied minimum physical address, never returns a frame twice, skips all non-USABLE regions and reports exhaustion. Tests cover usable/reserved gaps, alignment, address clamping, partial pages, malformed/overlapping/overflowing maps, no-usable-memory and exhaustion.

The kernel uses the same allocator source compiled with freestanding x86_64 flags and no hosted runtime dependency.

## Pinned third-party input and attribution

The build pins Limine v12.11.1 binary archive by SHA-256 in boot/limine-toolchain.lock. The protocol header is a byte-for-byte copy of limine-protocol/include/limine.h, pinned to the protocol repository commit recorded in the lock file. Its upstream SPDX 0BSD notice is retained. The Limine COPYING terms are placed inside the ISO.

Upstream references: https://github.com/Limine-Bootloader/limine-protocol/blob/trunk/PROTOCOL.md ; https://github.com/Limine-Bootloader/Limine/blob/v12.11.1/INSTALL.md ; https://github.com/Limine-Bootloader/Limine/blob/v12.11.1/USAGE.md

## Verified Stage 1 build

GitHub Actions run [45527148367](https://github.com/Ivan-VHS/DuckOS/actions/runs/45527148367) passed the host contracts, freestanding ELF/ISO build and QEMU BIOS plus OVMF UEFI tests. Both serial logs contain exactly one `DUCKOS_BOOT_OK stage=1` marker. The ISO is 4,376,576 bytes; SHA-256: `7b5bb3c29c0eeeb13b6e0a4514c15fe7df941969353287dac8d225f741f054f7`.

Observed emulator memory:
- BIOS: 18 map regions, 65,061 allocatable 4 KiB pages, one page allocated and cleared at physical address `0x00100000`.
- UEFI: 32 map regions, 53,041 allocatable 4 KiB pages, one page allocated and cleared at physical address `0x00100000`.

These figures describe the QEMU configurations in that workflow, not a minimum hardware requirement or a promise for every machine.

## Deliberate Stage 1 limits

This image does not yet provide a reusable allocator/free path, page-table manager, virtual-memory heap or address-space isolation; an owned GDT/TSS/IST stack, PIC/APIC, timer/IRQ routing or preemptive context switching; processes, threads, syscalls, user mode, scheduler execution or IPC runtime; ACPI/PCI/USB drivers, DMA or production driver manager; filesystem, init/service supervisor, package manager or persistence; native Mora compositor, window manager, GPU acceleration, audio stack or user applications; Secure Boot signing/enrolment, authenticated updates, rollback, installer or production recovery.

It is not tested on physical hardware. The current QEMU BIOS/UEFI tests prove only the declared x86_64 firmware path in the emulator. No blanket device or laptop compatibility claim is made.
