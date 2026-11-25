# DuckOS software framebuffer compositor v1

**Status:** host-testable CPU presentation core; kernel framebuffer wiring, surface page ownership, input routing and GPU acceleration remain separate gates.

## Scope

This component provides a deterministic CPU renderer for a mapped 32-bpp RGB display target. It validates output dimensions, pitch, mapped byte length, pointer alignment and non-overlapping channel masks before writing. It supports clipped rectangles, RGBA/BGRA app surfaces, source-over alpha blending, stable Z-order (ascending Z, then surface ID) and a hard limit of 32 surfaces per composition.

Surface memory must already be owned or pinned by the caller and remain readable for the duration of composition. This module does not map pages, allocate surfaces, import client pointers or grant surface access. Visible surface buffers must not overlap the output target; aliasing is rejected before the first write so a clear operation cannot destroy source pixels. The caller must keep surface descriptors and buffers stable for the duration of a compose call. The native host must validate DABI64 object ownership/generation and surface capability before constructing a descriptor.

## Pixel formats

App buffers use RGBA8888 or BGRA8888, four bytes per pixel, with explicit pitch and total buffer size. The output target supplies red/green/blue mask sizes and shifts; overlapping/out-of-range masks are rejected. The initial output backend requires 32-bpp mapped memory. Other framebuffer modes require a separate conversion backend.

## Frame transaction

1. Validate the output target and every surface descriptor.
2. Reject duplicate surface IDs and surface-count overflow before drawing.
3. Derive stable order from Z-index and surface ID.
4. Clear the target to the requested background.
5. Clip and composite visible surfaces in that order.
6. Return a bounded status; no untrusted allocation or implicit buffer growth occurs.

This is a full-frame CPU fallback. Damage tracking, double buffering, vblank pacing, monitor hotplug, GPU submission/fences and recovery from device loss remain future compositor-service work.

## Verification

CTest covers target bounds, clipped drawing, surface-buffer bounds, alpha blending, deterministic Z-order, duplicate IDs and surface-count limits.
