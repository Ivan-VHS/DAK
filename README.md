# DuckOS

DuckOS is the operating-system project. **Mora** is its unified desktop shell and application workspace.

[Open Mora](mora/index.html) · [Release edition](docs/RELEASE_EDITION.md) · [Architecture](docs/ARCHITECTURE.md) · [Implementation status](docs/IMPLEMENTATION_STATUS.md) · [Native roadmap](docs/IMPLEMENTATION_ROADMAP.md)

## Included in the ecosystem edition

- **Mora desktop shell:** responsive browser workspace, app launcher, interactive windows, dock, local preferences, reduced-motion mode, local app data and scoped offline cache.
- **Reaper:** native C17 command-line compiler/toolchain foundation and its reference runtime/tooling.
- **Pytyliki:** native C11 compute, profiling, diagnostics and host-inspection tools.
- **OPlague:** read-only user-space device/driver evidence and compatibility workbench.
- **VentuSample:** native C++20 audio/DSP workbench with optional Qt 6 desktop.
- **DuckOS kernel foundation:** x86_64 firmware boot through Limine, Boot Info v1 validation and an early monotonic physical-frame allocator.

The four project sources are pinned by exact Git commits, retain their individual licenses and are included under projects/. The release pipeline builds/tests their host tools and packages those results with the full source and Mora assets. Host binaries are not kernel binaries. The Mora workbench panels provide documentation and build/test guidance; browser code does not execute external commands.

## Run the desktop shell

For a quick preview in a browser, open mora/index.html. For offline install/cache support and to view the bundled project documentation, use the local static server.

Linux:

    ./scripts/run-mora.sh

Windows PowerShell:

    .\scripts\run-mora.ps1

The local server listens only on 127.0.0.1. No cloud service or external CDN is required for the shell itself. Keep the terminal open while Mora is in use.

Run the shell contract suite with Node.js 18+:

    npm test

## Build the release ISO

The reproducible release build expects Linux x86_64, Git/submodules, GCC/G++, CMake, Python 3, Node.js/npm, Qt 6 Widgets, xorriso, curl, tar, QEMU and OVMF. Then:

    git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git
    cd DuckOS
    bash boot/build-release-iso.sh --work-dir build/release --output dist/DuckOS-Release-x86_64.iso

The build validates repository pins, tests Mora, builds/tests the Reaper and Pytyliki native tools, builds/tests VentuSample, verifies OPlague source and unit tests, packages source/licences/host tools, checks the payload SHA-256 inventory, and builds a hybrid BIOS/UEFI ISO. GitHub Actions runs the same pipeline and QEMU boot checks. See Release edition in docs/RELEASE_EDITION.md.

The ISO is content-sized. It is not artificially padded to 4 GiB: empty padding would only enlarge the download and would not add a filesystem, applications or missing OS functionality. A true multi-gigabyte desktop OS image depends on the native runtime layers still on the roadmap.

## Boot status — important boundary

Stage 1 has passed QEMU BIOS and UEFI boot verification. The kernel validates the firmware handoff, initializes one 4 KiB physical frame, prints DUCKOS_BOOT_OK stage=1 and halts. It does not yet start processes, a service manager, filesystem, user mode or the Mora compositor. The bundled Mora shell runs separately in the host browser from the ISO payload; it is not launched by the current kernel.

This release is therefore a bootable kernel foundation plus an offline ecosystem payload, not yet a complete installable desktop operating system. No physical hardware qualification or Secure Boot claim is made.

## Source federation

The active ecosystem is defined in federation/repositories.v1.json. Build checkouts use:

    git submodule update --init --recursive

Mora's four ecosystem panels are registered in federation/mora-workbenches.v1.json. Each project is user-space scoped: hardware tools remain read-only, audio processing is offline by default, and external process execution remains disabled in the browser shell.

A pre-release Git snapshot is preserved on branch archive/pre-release-snapshot-2026-11-25.

## Engineering rule

Describe behavior from current source, tests, schemas and CI. A catalogue or roadmap is not proof of implementation. Browser preferences are not kernel enforcement; PE inspection is not Windows process execution; SHA-256 is not proof of authorship.
