# DuckOS x86_64 bootable Stage 1 image

**Status:** experimental native kernel foundation with a first-party DuckBoot UEFI path under integration verification. This is not a complete operating system.  
**Architecture:** x86-64; UEFI starts DuckBoot Core, legacy BIOS retains the pinned Limine fallback.  
**Kernel ownership:** DuckOS owns the DuckBoot EFI application, ELF64 inspection/loading, page-table setup, versioned handoff and kernel entry. Limine remains a separately licensed BIOS fallback.

## Firmware paths

The image carries both routes to preserve a known rollback path.

### UEFI — DuckBoot

UEFI loads EFI/BOOT/BOOTX64.EFI from the image's FAT32 EFI System Partition. DuckBoot uses UEFI Simple File System to read \boot\duckboot.cfg and \boot\duckos.elf, GOP for framebuffer metadata and COM1 for diagnostics.

DuckBoot validates the ELF64 x86-64 ET_EXEC header and all loadable segments before copying them to their declared physical ranges. It creates a kernel stack, an identity mapping for the transition code, an HHDM mapping and per-segment kernel mappings with W^X/NX permissions. It then normalizes the EFI memory map, validates DuckOS Boot Info v1, exits UEFI Boot Services with the exact map key and transfers to the kernel through DuckBoot handoff v1.

The kernel validates the handoff, initializes the early physical-frame allocator, clears one 4 KiB frame and emits:

    DUCKOS_BOOT_OK stage=1 loader=duckboot handoff=v1 frames=1

The OVMF test requires the loader=duckboot field, so a Limine boot cannot masquerade as a successful DuckBoot run.

### Legacy BIOS — Limine fallback

The BIOS route still loads boot/duckos-limine.elf through pinned Limine v12.11.1. It validates Limine responses, adapts them to Boot Info v1, initializes the same early physical-frame allocator and emits the existing DUCKOS_BOOT_OK stage=1 marker.

A first-party BIOS Stage 1/Stage 2 implementation is not yet present. Limine remains in the image until the native BIOS route is independently implemented and verified.

## Kernel boundary

Both entry routes lead to the same bounded Stage 1 memory foundation, but use different firmware contracts:

- The BIOS fallback receives Limine protocol responses and adapts them to Boot Info v1.
- DuckBoot UEFI produces DuckBoot handoff v1 plus Boot Info v1 directly; the DuckBoot kernel entry does not include Limine request sections.

Boot Info v1 contains fixed-width fields and a separately supplied memory map. The DuckBoot envelope contains the mapped virtual addresses and HHDM metadata required by the x86-64 kernel entry.

The allocator remains monotonic and single-core. It exposes only page-aligned 4 KiB frames from validated USABLE regions, excludes addresses below 1 MiB, allocates one frame and clears that frame. It does not free pages, build page tables after boot, reclaim regions or provide a heap.

The existing .rpr files remain Reaper policy/reference material. The freestanding platform entry bridge is C11 because the current Reaper native compiler is not yet a freestanding kernel compiler; no claim is made that Reaper currently compiles the kernel.

## Build

On Linux x86_64 install GCC, binutils, Clang, lld-link, dosfstools, mtools, curl, tar, xorriso and sha256sum.

    boot/build-iso.sh

The build pins and verifies the Limine archive used by the BIOS fallback, compiles both ELF kernels, cross-compiles the EFI application as PE32+, builds a FAT32 ESP and creates a hybrid BIOS/UEFI ISO.

    boot/build-iso.sh --work-dir build/duckboot --output build/DuckOS-Stage1-x86_64.iso

CMake integration:

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
    cmake --build build --target duckos-boot-iso
    ctest --test-dir build --output-on-failure

## Verify in QEMU

Install qemu-system-x86 and OVMF firmware, then run:

    boot/test-qemu.sh --iso build/DuckOS-Stage1-x86_64.iso --ovmf-code /usr/share/OVMF/OVMF_CODE.fd --ovmf-vars /usr/share/OVMF/OVMF_VARS.fd

The script verifies the BIOS fallback marker and separately requires the DuckBoot-specific UEFI marker. GitHub Actions builds the same image and runs both firmware tests.

The DuckBoot UEFI application has been cross-compiled and linked as a PE32+ EFI application; the DuckBoot kernel has been linked as a high-half ELF64 executable and accepted by the ELF inspector. These build checks are necessary but do not replace the OVMF handoff test.

## Deliberate limits

DuckBoot UEFI uses the firmware's Simple File System interface rather than shipping its own filesystem drivers. There is no own BIOS reader, interactive menu, scripting engine, Multiboot2 loader, Ext/Btrfs/XFS/NTFS/ZFS driver, PXE/TFTP/HTTP path, Secure Boot trust chain, disk installer or automatic rollback yet.

The current kernel still has no reusable memory manager, page-table manager, interrupt subsystem, process model, syscall layer, driver runtime, filesystem, service supervisor or compositor. The image is not qualified on physical hardware.
