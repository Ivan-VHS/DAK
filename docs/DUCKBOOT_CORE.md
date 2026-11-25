# DuckBoot Core — native UEFI loader foundation

**Target:** x86-64 UEFI, four-level paging, ELF64 ET_EXEC.  
**Project status:** the UEFI loader and kernel handoff are implemented in the feature branch and passed QEMU/OVMF integration. The BIOS fallback also passed in the same run.  
**BIOS status:** the existing Limine BIOS path remains the compatibility fallback. DuckBoot does not yet replace the BIOS boot chain.

## Boot path

The hybrid image carries two independent firmware paths:

- **UEFI:** firmware starts EFI/BOOT/BOOTX64.EFI from the DuckBoot FAT32 EFI System Partition. DuckBoot reads \boot\duckboot.cfg and the kernel through UEFI Simple File System, obtains the framebuffer through GOP, and prints diagnostics through COM1 and the UEFI text console.
- **Legacy BIOS:** the existing pinned Limine v12.11.1 boot path loads boot/duckos-limine.elf. This is intentionally retained until a first-party BIOS Stage 1/Stage 2 implementation passes the same QEMU gates.

The UEFI application is a first-party PE32+ EFI application. It does not chain to GRUB or Limine.

## Implemented components

### Host-tested core

- **BootArena:** caller-owned storage, checked pointer arithmetic, power-of-two alignment, bounded allocation, checkpoint/rewind and optional clearing.
- **Configuration parser:** bounded key/value input, duplicate and unknown-key rejection, path traversal rejection, command-line and label capacity checks, and timeout range 0–30 seconds.
- **ELF64 inspector:** little-endian x86-64 ET_EXEC, checked ELF/program-header bounds, at most 32 PT_LOAD segments, arithmetic-overflow checks, canonical virtual ranges, page-level physical/virtual overlap rejection, executable entry-point coverage and W^X rejection.
- **Handoff v1:** separate DuckBoot envelope that points to the pointer-free DuckOS Boot Info v1 record, normalized memory map, HHDM and optional framebuffer metadata.

### UEFI application and kernel bridge

- UEFI Loaded Image, Simple File System and GOP protocol discovery.
- Bounded configuration and kernel-file reads; the kernel image is validated before use.
- Physical allocation of the kernel's declared load range, PT_LOAD segment copy and BSS zeroing.
- A 64-page kernel stack and newly built four-level x86-64 page tables.
- Identity mapping for the transition trampoline, a direct HHDM mapping, and per-segment kernel mappings honoring read-only, writable, executable and NX permissions.
- CPU NX capability check and explicit rejection of five-level paging mode.
- EFI memory-map normalization to DuckOS memory types, Boot Info v1 validation and ExitBootServices with the exact memory-map key (one bounded retry).
- GOP framebuffer identity and HHDM aliases use uncached PCD/PWT attributes. Existing non-MMIO EFI descriptors overlapping the framebuffer are rejected; only uncovered framebuffer gaps are synthesized as MMIO.
- An assembly transition that loads the new CR3 and kernel stack, then passes the handoff pointer using the x86-64 System V kernel entry convention.
- A separate freestanding kernel entry that validates the handoff and Boot Info, initializes the existing physical-frame allocator, clears one 4 KiB frame through HHDM, paints a basic GOP framebuffer status screen and emits DUCKOS_BOOT_OK stage=1 loader=duckboot.

The ELF inspector and BootArena are host-testable. The UEFI binary is cross-compiled as PE32+; the kernel is linked as a high-half ELF64 executable.

## Build

On Linux x86_64 install:

- GCC and binutils
- Clang and lld-link (lld)
- dosfstools and mtools
- curl, tar, sha256sum, xorriso

Build the hybrid image:

    bash boot/build-iso.sh --work-dir build/duckboot --output build/DuckOS-Stage1-x86_64.iso

The script verifies the pinned Limine archive, builds the BIOS fallback kernel, builds the independent DuckBoot kernel, compiles the EFI application, creates a FAT32 ESP image and produces the hybrid ISO.

Build and run host contracts:

    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
    cmake --build build --parallel
    ctest --test-dir build --output-on-failure

## QEMU verification

Run both firmware paths:

    boot/test-qemu.sh \
      --iso build/DuckOS-Stage1-x86_64.iso \
      --ovmf-code /usr/share/OVMF/OVMF_CODE.fd \
      --ovmf-vars /usr/share/OVMF/OVMF_VARS.fd

The BIOS test accepts the existing Stage 1 marker. The UEFI test specifically requires DUCKOS_BOOT_OK stage=1 loader=duckboot, so an accidental Limine UEFI boot cannot satisfy the DuckBoot test.

Verified evidence: [GitHub Actions run 45640060710](https://github.com/Ivan-VHS/DuckOS/actions/runs/45640060710) completed successfully. Its QEMU logs contain both `BIOS boot: PASS` and `UEFI DuckBoot handoff: PASS`; the UEFI serial stream contains `DUCKBOOT_HANDOFF_READY v1` followed by `DUCKOS_BOOT_OK stage=1 loader=duckboot handoff=v1 frames=1`. The workflow uploaded the bootable ISO, checksum and serial logs as the `DuckOS-Stage1-x86_64-ISO` artifact. This verifies the declared QEMU firmware paths, not physical hardware compatibility.

## Configuration

Default boot/duckboot.cfg:

    timeout=5
    label=DuckOS
    kernel=\boot\duckos.elf
    cmdline=duckos.bootloader=duckboot serial=on

The parser currently validates the timeout and label, and the UEFI loader consumes the kernel path and command line. An interactive selection menu is not implemented yet; the timeout is reserved for that future menu.

## Explicit limits

DuckBoot is not yet a GRUB-class feature-complete replacement. This implementation does not include:

- a first-party BIOS disk reader, BIOS Stage 1/Stage 2, or BIOS long-mode transition;
- an interactive menu, scripting engine, rescue shell or chainloader UI;
- its own FAT32, ext2/3/4, Btrfs, XFS, NTFS or ZFS drivers (UEFI Simple File System is used on the UEFI path);
- Multiboot2 compatibility, ELF PIE relocation or dynamic linking;
- PXE, TFTP, HTTP boot, network drivers or remote configuration;
- Secure Boot signing/enrollment, signature verification, measured boot or TPM integration;
- encrypted-volume unlock, multi-disk discovery, filesystem repair or disk installation;
- arbitrary module loading, third-party driver ABI or authenticated update/rollback.

The UEFI kernel image is a fixed-address x86-64 ET_EXEC linked at physical base 2 MiB. NX support is required. The memory-map contract is bounded to DUCKOS_BOOT_MAX_MEMORY_REGIONS; overflow is treated as a fatal boot error rather than silently truncating firmware state.

## Safety and migration policy

The Limine BIOS path is retained as a rollback route. The UEFI path may only become the default for the UEFI image after OVMF tests prove that the DuckBoot marker is reached. No successful firmware transfer is inferred from documentation, build completion or a PE file existing on disk.

Each additional filesystem, protocol, firmware path or security feature must have its own parser/driver contract, bounds tests, malformed-input tests and firmware integration evidence before being marked implemented.
