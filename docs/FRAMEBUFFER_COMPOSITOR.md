# DuckOS software framebuffer compositor

The x86-64 Stage 1 boot path uses a freestanding C11 compositor to present its boot and failure screen through a kernel-owned ARGB8888 surface.

## Contracts

- Scanout is a Limine-provided, validated linear 32-bpp RGB mapping with non-zero dimensions, four-byte-aligned pitch/address, complete mapped-byte extent and non-overlapping color masks.
- Surfaces use kernel-owned ARGB8888 straight-alpha buffers. The compositor checks pointer arithmetic, capacity, dimensions, pitch and source/scanout overlap before registration.
- Surface count is bounded to 16 and each backing buffer is bounded to 16 MiB.
- Presentation clears visible scanout, sorts visible surfaces by ascending z and stable ID, clips signed coordinates and blends pixels into target color masks.
- Surface mutation and presentation are synchronous and externally serialized by the owning kernel service.

## Stage 1 boundary

The boot screen uses one static kernel-owned surface capped at 1280×720. Rectangle/text drawing updates that surface; only the compositor writes to firmware scanout. Boot-failure and CPU-exception overlays reuse the same path. Unsupported framebuffer descriptors leave serial output available.

This is a real software composition path in Stage 1, not a user-process desktop compositor. Application windows, scheduler lifecycle, page-backed surfaces, damage tracking, frame timing and GPU acceleration remain later stages.

## Tests

The CTest target duckos-framebuffer-compositor exercises target validation, alpha blending, stable z-order, clipping, hidden surfaces, invalid resize, source/scanout alias rejection, duplicate surfaces, capacity and removal. The ISO build compiles the same source with -ffreestanding -Werror.
