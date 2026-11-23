# DuckOS kernel audio subsystem

DuckOS owns the system audio boundary. This repository provides the initial PCM device ABI in `kernel/include/duckos/audio.h` and a kernel registry in `kernel/src/audio.c`.

The v1 contract supports U8, signed 16/24/32-bit little-endian PCM and F32 little-endian PCM, 1–8 channels and sample rates from 8 kHz through 192 kHz. Drivers provide open/submit/pause/close callbacks. The kernel bounds buffers to 256 KiB per submission and does not interpret hardware-specific DMA structures in the generic audio API.

No concrete HDA, AC'97 or USB Audio driver is included yet. A hardware driver must register itself and own its DMA/ring-buffer implementation, interrupt completion and device-specific recovery. Audio is not part of Reaper, Pytyliki or OPlague. Creative sample playback remains in VentuSample; the DuckOS API is for operating-system devices and applications.
