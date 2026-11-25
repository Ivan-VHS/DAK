# DuckOS Ecosystem Release Edition

**Edition:** ecosystem  
**Version:** 1.1.0-preview.1  
**Target:** x86_64, hybrid BIOS/UEFI  
**Desktop:** native C++20 / Qt 6 Widgets host application  
**Release state:** bootable Stage 1 kernel foundation plus a native host desktop and offline ecosystem payload; not yet a complete userspace operating system.

## What is on the ISO

The image contains two distinct layers:

1. The bootable DuckOS Stage 1 image: Limine handoff, Boot Info v1 validation, early physical-frame allocator and serial/framebuffer boot marker.
2. The offline DuckOS package under /duckos/: complete DuckOS source, all four pinned project source trees and their licenses, Mora app catalogue and manifests, native launcher allowlist, documentation, compiled Linux x86_64 host tools and the native Qt desktop executable at release/bin/duckos-desktop.

The native desktop is not a web page. It is compiled C++20 and Qt 6 Widgets. It creates real host OS windows and controls and does not embed a browser engine, WebView, HTML renderer or remote UI. The former Mora HTML/JavaScript shell remains as a prototype/reference surface and its Node.js checks are not evidence of native UI operation.

## Start the native desktop from the Linux package

Mount or extract the image, enter the package root and run:

    cd /path/to/duckos/duckos
    ./scripts/run-duck-desktop.sh

The Linux host must have the Qt 6 Widgets runtime and a platform plugin installed. On Ubuntu 24.04:

    sudo apt-get install -y libqt6widgets6 libqt6gui6 libqt6core6t64 qt6-qpa-plugins

The desktop also needs a running graphical session (Wayland or X11). It listens only to local host input and does not start a local web server.

The shell opens as a normal desktop application. Press F11 for full-screen and Ctrl+Q to quit. Its search field and category filter navigate the application catalogue; the dock opens Files, Notes, Calculator, Settings and Sestem.

## Windows 11 native desktop

The DuckOS Native Desktop workflow publishes DuckOS-Native-Desktop-Windows-x64.zip.

1. Extract the archive to a writable folder.
2. Install Python 3 with Tcl/Tk only if you intend to use OPlague.
3. Run scripts/run-duck-desktop.ps1.

The native desktop itself requires no browser. The archive includes the Qt 6 runtime for the shell and VentuSample, plus supported native project binaries.

## Applications and maturity

The native launcher imports all 30 existing Mora application identities and the four current first-party workbenches. It provides 31 native built-in modules/tools: system status, settings, Files, Notes, Calculator, Clock, file metadata, SHA-256, read-only PE/ELF header inspection, rhythm profiles and bounded local collections for tasks, journals, quick capture, knowledge cards, manual route notes, album/media labels, expense text records, game-library metadata, sharing checklists and automation drafts.

Local collection modules use the host user's application-data directory; writes are atomic and limited to 500 records, 2,000 characters per record and 1 MiB per collection.

A few larger historical products remain incomplete: Cockos does not record audio; Po is not a native browser; Mora AI is not a local AI agent; Illidia and GameCharager currently manage metadata only; Unify is a local transfer checklist; Gloverty stores automation drafts but does not execute them; Kavun stores album/media labels rather than editing images; Ka-bon stores text records without payment integrations. These entries are not represented as fully completed products.

## First-party workbench launch

catalogs/native-launchers.v1.json is the allowlist for Reaper, Pytyliki, OPlague and VentuSample.

| Workbench | Native host entry | Capability boundary |
|---|---|---|
| Reaper | C17 native CLI | Compiler/toolchain capability listing; not the complete language runtime |
| Pytyliki | C11 CLI on Linux; Win32 GUI on Windows | Read-only host inspection and bounded compute |
| OPlague | Existing Python/Tk desktop workbench | Read-only device and driver-package evidence; no driver installation |
| VentuSample | C++20 / Qt 6 desktop | Offline sample/DSP tool; not a kernel audio driver or realtime DAW |

A launch requires a direct user click. The desktop uses QProcess with a fixed executable, explicit argument vector and declared working directory. It does not invoke a shell. Before starting, it resolves the target and working directory canonically and rejects paths outside the DuckOS package root. It does not request elevation, write firmware or install drivers.

These remain independent host user-space processes. The native desktop has not yet been connected to a DuckOS kernel process manager, userspace ABI, IPC broker or compositor.

## Build and test the native desktop on Linux

Requirements: Ubuntu 24.04 x86_64, CMake 3.21+, GCC/G++ with C++20 support, Qt 6.4+ Widgets, and the project sources initialized recursively.

    git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git
    cd DuckOS
    cmake -S desktop-native -B build/desktop -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
    cmake --build build/desktop --parallel 2
    ctest --test-dir build/desktop --output-on-failure
    ./build/desktop/duckos-desktop --validate-catalog --root "$PWD"
    ./build/desktop/duckos-desktop --root "$PWD"

The top-level Linux CMake project also exposes:

    cmake --build build --target duckos-native-desktop

The native desktop CI separately builds on Ubuntu and Windows 2022. Its Linux job validates the catalog, creates the Qt window offscreen and runs CTest. Its Windows job builds supported native project binaries, deploys the Qt runtime and publishes a portable x64 package.

## Build the complete Linux release ISO

The reproducible release build validates source pins, tests the legacy browser prototype contracts, builds/tests Reaper, Pytyliki and VentuSample, tests OPlague, builds/tests the native Qt desktop, packages sources/licences/host tools, validates that all four external launchers resolve inside the payload, verifies the payload SHA-256 inventory and creates a hybrid BIOS/UEFI ISO.

    bash boot/build-release-iso.sh --work-dir build/release --output dist/DuckOS-Release-x86_64.iso

The release workflow verifies BIOS and UEFI QEMU boot, runs a Chromium regression check for the retained browser prototype and publishes the ISO, payload checksums, build information and serial logs.

## Image size

The image is content-sized. No empty padding is appended to target 4 GiB. Padding a filesystem image does not add applications, a desktop runtime or OS services. A genuinely multi-gigabyte install/live image should contain qualified drivers, system libraries, service binaries, media and application content—not arbitrary filler.

## Current kernel boundary

The ISO boots the Stage 1 kernel through BIOS or UEFI in QEMU. After validating the firmware handoff, allocating and clearing an early 4 KiB frame, the kernel prints DUCKOS_BOOT_OK stage=1 and halts. It does not start the native desktop.

The desktop executable currently runs as a normal host application on Linux or Windows. To make the desktop start after boot directly from DuckOS, the kernel still needs page tables and reusable memory management, exceptions/interrupts/timer, scheduler and context switching, userspace ELF loader, address spaces, syscalls and process model, filesystem and init/service manager, input/display services and a native compositor. This release does not claim those layers are finished.

No physical DuckOS hardware qualification, Secure Boot support, installer, disk partitioner, on-device driver manager, kernel-enforced sandbox, kernel graphics/audio stack or userspace process ABI is claimed by this preview.
