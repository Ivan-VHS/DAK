# DuckOS Native Desktop

**Desktop runtime:** Qt 6 Widgets / C++20  
**UI technology:** native operating-system widgets and windows; no browser engine, WebView, HTML renderer or remote UI.  
**Shell maturity:** first native host desktop milestone.  
**Kernel boundary:** the native host desktop is not yet started by the DuckOS Stage 1 kernel.

## What is native now

The desktop-native target builds duckos-desktop, a standalone Qt Widgets desktop process. It provides a live application grid, text search, categories, a clock/status panel, dock, fullscreen toggle (F11), keyboard quit (Ctrl+Q), native dialogs and persistent per-user settings.

The native desktop currently has 31 built-in modules/tools: Files, Notes, Calculator, Clock, SetupUP settings, Sestem/Control status, basic file metadata, SHA-256 verification, read-only PE/ELF header inspection, rhythm profiles, task lists, journals, quick capture, knowledge cards, manual route notes, album/media labels, text expense records, game-library metadata, sharing checklists and automation-rule drafts. Local collection modules store per-app JSON in the host user's application-data directory with atomic save and limits of 500 entries, 2,000 characters per entry and 1 MiB per collection. These are bounded native local tools, not claims that corresponding cloud, audio, payment, device-pairing or automation engines are complete.

The native catalog imports all existing Mora application identities and the four versioned ecosystem workbenches. It does not load Mora HTML or JavaScript. Historical identities remain visible in the catalogue. Cockos recording/audio, Po browser and Mora AI remain NOT PORTED. Illidia and GameCharager currently manage local game metadata only; Unify is a local transfer checklist; Gloverty stores automation drafts without executing them; Kavun stores album/media labels rather than editing images; Ka-bon stores text records without payment integrations. The native file inspector reads PE/ELF headers but never executes inspected binaries.

## Launching federated applications

catalogs/native-launchers.v1.json is the allowlist for Reaper, Pytyliki, OPlague and VentuSample user-space tools. A launch requires a direct click in the desktop. The process is started with QProcess using a fixed program, argument list and working directory; no shell interpreter is involved.

Before launch, program and working directory must resolve to files/directories inside the DuckOS package root. Path traversal and package-external symlink resolution are rejected. The shell does not request administrator rights or install drivers.

- **Reaper:** launches the native C17 CLI capability registry in a native output window. This is a developer workbench, not the complete Reaper compiler/runtime.
- **Pytyliki:** launches the Windows native GUI when present; on Unix it opens the native C11 CLI profile report in an output window.
- **OPlague:** opens the existing read-only Python/Tk workbench with the host Python runtime.
- **VentuSample:** opens its native Qt 6 desktop application.

These applications remain independent host processes. Dock/compositor integration, IPC, system-wide permissions and native DuckOS ABI services are not claimed yet.

## Build on Linux

Requirements: CMake 3.21+, C++20 compiler and Qt 6.4+ Widgets.

~~~bash
cmake -S desktop-native -B build/desktop -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build build/desktop --parallel 2
ctest --test-dir build/desktop --output-on-failure
./build/desktop/duckos-desktop --root "$PWD"
~~~

In a packaged release tree:

~~~bash
./scripts/run-duck-desktop.sh
~~~

## Build on Windows 11

Use Visual Studio 2022 x64, CMake 3.21+ and Qt 6.4+ Widgets.

~~~powershell
cmake -S desktop-native -B build/desktop -A x64 -DBUILD_TESTING=ON
cmake --build build/desktop --config Release --parallel
ctest --test-dir build/desktop -C Release --output-on-failure
.\build\desktop\Release\duckos-desktop.exe --root $PWD
~~~

The Windows Native Desktop workflow publishes a portable bundle containing the shell, deployed Qt runtime, supported host app binaries and pinned project payload. Run scripts/run-duck-desktop.ps1 from the extracted package root. Python 3 with Tcl/Tk is needed only for OPlague.

## Catalog maturity

The app registries contain 30 named Mora identities and 20 DAK base-suite specifications. These are not all separate repositories or executable programs. The currently accessible GitHub source projects are DuckOS, Reaper, Pytyliki, OPlague and VentuSample. The four project launchers are real; the remaining catalog items need their own native implementations, service contracts and tests before they can be marked launchable.

## What is still required for a native DuckOS boot session

The current kernel halts after the Stage 1 boot marker. It has no userspace ELF loader, address spaces, process creation, syscall ABI, service supervisor, filesystem-backed package layout, native input/display runtime or compositor. As a result, duckos-desktop currently runs as a normal native application on Linux/Windows host systems; it is not launched from the kernel after boot.

The next kernel milestones are page tables and memory manager, exception/interrupt/timer runtime, scheduler/context switching, process and syscall ABI, filesystem/init/service manager, framebuffer/input/compositor, and only then a native desktop session started by DuckOS itself.
