# Dak Ecosystem Release Edition

**Edition:** ecosystem  
**Version:** 1.0.0-preview.1  
**Target:** x86_64, hybrid BIOS/UEFI  
**Release state:** preview, source-and-tools distribution; not yet a complete desktop operating system.

## What is on the ISO

The image contains two deliberately separate layers:

1. The bootable Dak Stage 1 firmware image: Limine handoff, Boot Info v1 validation, early physical-frame allocator and serial/framebuffer boot marker.
2. The offline ecosystem payload under /dakos/: the complete Dak source tree, Mora shell assets and local catalogue, documentation, manifests, schemas, licenses/notices, all four currently federated source repositories, tested Linux x86_64 host tools and a SHA-256 inventory.

Mora includes launcher panels for Reaper, Pytyliki, OPlague and VentuSample. These panels open descriptions and local documentation; they do not run a command or launch an external process from browser code.

## Open Mora from the release media

Mount or extract the ISO on a Linux desktop and run:

    cd /path/to/dakos
    ./scripts/run-mora.sh

The script serves the local tree on 127.0.0.1:8765 and opens http://127.0.0.1:8765/mora/ when a desktop browser launcher is available. Keep the terminal open while using the shell. Press Ctrl+C to stop the local server.

On Windows, with Python 3 installed, run scripts/run-mora.ps1 from PowerShell. Alternatively:

    cd X:\dakos
    py -m http.server 8765 --bind 127.0.0.1
    start http://127.0.0.1:8765/mora/

Mora is a static, local-first browser shell. It supports the local UI, window interactions, local preferences, its built-in panels and the project workbench panels. The panels do not provide kernel privileges or real hardware access. Some app panels continue to show clearly labelled demo data.

## Project payload and build evidence

| Project | Packaged source | Tested host build | Boundary |
|---|---|---|---|
| Reaper | projects/reaper/ | C17 native CLI/FFI and project tests | User-space toolchain |
| Pytyliki | projects/pytyliki/ | C11 CLI/FFI and project tests | User-space compute and read-only host inspection |
| OPlague | projects/oplague/ | Python compile and unit tests | Read-only user-space inspection |
| VentuSample | projects/ventusample/ | C++20/C11 DSP, Qt 6 desktop where available | Offline-by-default audio tools |

The exact checked-out commits are recorded in federation/repositories.v1.json and the image-side release/BUILD-INFO.txt. Each source repository retains its own license and notice files. Host executables are kept under release/bin/ and are built for Linux x86_64; they are not Dak kernel modules or executables that the current kernel can run.

The payload checksum list is SHA256SUMS at the root of the payload. Verify it after mounting or extracting:

    cd /path/to/dakos
    sha256sum --check SHA256SUMS

The ISO itself also has a .sha256 sidecar next to the downloaded image.

## Build and verify

On Ubuntu 24.04 x86_64 install GCC/G++, CMake, Python 3.12, Node.js 22, Qt 6 Widgets, QEMU x86, OVMF, xorriso, curl, tar and standard build tools. Then:

    git clone --recurse-submodules https://github.com/Ivan-VHS/Dak.git
    cd Dak
    npm test
    bash boot/build-release-iso.sh --work-dir build/release --output dist/Dak-Release-x86_64.iso

The release workflow performs the same source-pin validation, project builds/tests, Mora tests, ISO build and QEMU BIOS/UEFI boot checks.

## Size and why this is not padded

The ISO size is determined by the source, documentation, assets and built host tools actually included. This release script does not append empty bytes or dummy files to make a 4 GiB download. Doing so would only inflate the download and would not add a filesystem, applications or operating-system functionality.

A genuine multi-gigabyte install/live image needs the missing runtime layers to exist first: a reusable physical/virtual memory manager, page tables and address spaces, interrupt/timer handling, scheduler, process and syscall model, filesystem and persistent user profile, driver stack, service manager and a native Mora compositor/window system. Adding filler cannot substitute for those components.

## Current kernel limits

The ISO boots the Stage 1 kernel through BIOS or UEFI in QEMU. After validating the handoff and allocating/clearing an early 4 KiB frame, the kernel prints DAK_BOOT_OK stage=1 and halts. The kernel does not start a browser, Mora, Reaper, the native workbenches or a service session. The Mora desktop is opened from the payload by the host operating system using a browser.

No physical hardware qualification, Secure Boot support, installer, disk partitioner, kernel-enforced sandbox, native GPU/audio stack or process execution model is claimed by this preview.

## Release source archive

The branch archive/pre-release-snapshot-2026-11-25 preserves the Dak repository state before this release integration work. It is a Git snapshot of the Dak repository only; it does not pretend to recreate histories of inaccessible external repositories.
