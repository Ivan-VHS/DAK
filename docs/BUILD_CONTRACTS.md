# DuckOS build contracts

## System manifest

A manifest uses `duckos.system-manifest.v1` and requires four components: `bootloader`, `kernel`, `initramfs` and `rootfs`. Each component record has a canonical relative path, exact byte length and lowercase SHA-256 digest. Verification compares the manifest against staged local files.

The target architecture is one of x86_64, aarch64, riscv64 or i686. The kernel ABI is an explicit version string; it is not inferred from a filename.

## Image layout

The planner uses byte offsets and exclusive end positions. Default partition alignment is 1 MiB with 512-byte sectors. Every region is aligned, non-overlapping and bounded by the 64 GiB planner limit. The result is metadata only and cannot write to a disk. The output contract is `duckos.image-layout.v1`, described by `schemas/image-layout.v1.schema.json`.

## Driver module ABI

A module descriptor specifies the exact target architecture and kernel ABI. Dependency ordering is deterministic and rejects missing modules and cycles. Capabilities are descriptive strings; validation does not grant them to code or load a module.

## Boundaries

This build library is not a kernel, UEFI executable, driver loader, package installer or bootable image creator. Each of those deliverables requires native implementation and independent emulator/hardware tests.
