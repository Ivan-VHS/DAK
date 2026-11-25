# DuckOS

DuckOS is the operating-system project. **Mora** is its visual identity and application catalogue; the live desktop is migrating to a native Qt Widgets runtime.

[Native desktop](docs/NATIVE_DESKTOP.md) · [Release edition](docs/RELEASE_EDITION.md) · [Architecture](docs/ARCHITECTURE.md) · [Implementation status](docs/IMPLEMENTATION_STATUS.md) · [Native roadmap](docs/IMPLEMENTATION_ROADMAP.md)

## Native desktop

The live host desktop is the standalone C++20 / Qt 6 Widgets application in desktop-native/. It creates real OS windows and controls, reads the existing app catalogue, provides native Files, Notes, Calculator, Clock, Settings and status tools, and launches the four available project workbenches through a fixed process allowlist. It does not embed a browser engine or WebView.

Linux:

~~~bash
cmake -S desktop-native -B build/desktop -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build/desktop --parallel 2
ctest --test-dir build/desktop --output-on-failure
./build/desktop/duckos-desktop --root "$PWD"
~~~

Windows 11 (Visual Studio 2022 x64 + Qt 6):

~~~powershell
cmake -S desktop-native -B build/desktop -A x64 -DBUILD_TESTING=ON
cmake --build build/desktop --config Release --parallel
ctest --test-dir build/desktop -C Release --output-on-failure
~~~

The Windows native bundle is published by the DuckOS Native Desktop workflow. Download and extract the bundle, then run scripts/run-duck-desktop.ps1. Python 3 with Tcl/Tk is required for the OPlague workbench. The old Mora browser UI remains as a prototype and reference; it is no longer the default shell launcher.

## Historical application catalogue

The native desktop imports all 30 app identities from Mora and the four current ecosystem workbenches. Native implementations are available for the core shell tools, settings, local notes, file inspection and the current project launchers. Entries that still exist only as design descriptions or browser prototypes are marked NOT PORTED instead of claiming to launch an application that does not exist yet.

## Native shell versus kernel

The Stage 1 kernel still validates the Limine handoff, allocates and clears one early physical frame, prints DUCKOS_BOOT_OK stage=1 and halts. It cannot start user-space processes. Therefore this native desktop currently runs directly on a supported host OS from the DuckOS package; it is not yet launched by the DuckOS kernel. The distinction and next kernel dependencies are documented in docs/NATIVE_DESKTOP.md.

## Federated projects

The four current first-party repositories are pinned by exact commit under projects/, retain their licenses, and are registered in federation/:

- Reaper — C17 user-space language/toolchain foundation.
- Pytyliki — C11 compute and host-inspection tools.
- OPlague — read-only device/driver evidence workbench.
- VentuSample — C++20/C11 offline audio and DSP workbench.

## Release ISO

The reproducible x86_64 hybrid BIOS/UEFI ISO packages the Stage 1 kernel, native Linux host desktop, offline project source, host tools and documentation. The native application is included as a host executable; the kernel does not launch it yet.

~~~bash
bash boot/build-release-iso.sh --work-dir build/release --output dist/DuckOS-Release-x86_64.iso
~~~

The ISO is content-sized and is not padded with empty bytes to target 4 GiB. A genuine multi-gigabyte desktop OS image requires the process, filesystem, driver, service and compositor layers to exist first.
