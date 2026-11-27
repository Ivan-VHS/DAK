# Duck — Reaper-first operating-system project

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/DAK/actions/workflows/ci.yml) [![Boot image](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/boot-image.yml?branch=main&label=Boot%20image)](https://github.com/Ivan-VHS/DAK/actions/workflows/boot-image.yml) [![Native desktop](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/native-mora.yml?branch=main&label=Native%20desktop)](https://github.com/Ivan-VHS/DAK/actions/workflows/native-mora.yml)

> An experimental x86_64 system foundation: a QEMU-verified Stage 1 boot path, Reaper policy contracts and a separate host-native desktop shell.

**Project record:** Experimental · Stage 1 boot foundation · x86_64 / Limine BIOS+UEFI · Reaper-first architecture direction · host shell C++17 / optional Qt 6 Widgets 6.4+ · no unified OS release version · **Documentation reviewed:** 2026-11-27 UTC

<p align="center"><img src="assets/readme/duckos-overview.svg" alt="Duck system and host desktop architecture overview" width="100%"></p>

## Purpose and scope

Duck is an experimental operating-system project, not yet a complete installable desktop OS. Three execution surfaces must be kept distinct:

1. **Kernel Stage 1:** a freestanding x86_64 boot foundation that validates the Limine handoff and Boot Info v1, exercises early physical-frame allocation and reports its boot marker before halting.
2. **Reaper policy track:** reference subsystem contracts and executable policy tests. Native kernel enforcement and a freestanding Reaper compiler/backend are not yet delivered.
3. **Host desktop:** a separate C++17 / Qt 6 Widgets application whose windows are managed by the host operating system. It is not launched by the Stage 1 kernel.

The current boot bridge is a narrow C11 freestanding platform boundary. Reaper remains the intended first-class language and policy layer; reference-runtime success does not prove native compiler support, kernel privilege or hardware access.

## Current implementation

### Boot and kernel foundation

- x86_64 Stage 1 uses the pinned Limine v12.11.1 BIOS/UEFI path and validates Boot Info v1.
- The early physical-frame allocator selects validated usable memory, allocates and clears one 4 KiB frame through the HHDM, then emits `DUCKOS_BOOT_OK stage=1`.
- The exception foundation includes IDT vectors 0–31, normalized assembly stubs and fatal serial/framebuffer diagnostics. It does not enable maskable interrupts.
- GDT/TSS/IST bootstrap structures and host contract tests are present; per-CPU setup, application-processor startup and complete interrupt/runtime integration remain unfinished.
- Reaper currently provides 40 Core Subsystem MVP reference contracts. Native kernel enforcement is pending.

The boot image has passed QEMU BIOS and UEFI Stage 1 checks. It still halts before starting a process or user session.

### Host-native desktop

- The optional C++17 application uses Qt 6 Widgets 6.4+ and creates real top-level windows owned by the host OS.
- The local catalogue is a discovery surface; the native launcher does not execute manifest command strings or grant device privileges.
- Current surfaces include local draft persistence, a user-selected read-only folder view and a visual-only VentuSample waveform panel. The waveform panel does not play audio or invoke VentuSample DSP.
- The browser preview at [`desktop/demo/index.html`](desktop/demo/index.html) is a reference prototype, not the kernel compositor or a WebView-based implementation.

### Kernel work still pending

| Area | Current boundary |
|---|---|
| Memory | One early frame allocation; reusable allocator/free path and page tables pending |
| Interrupts | Exception diagnostics only; external IRQ routing and timer scheduling pending |
| Processes | Process model, Ring 3 execution and syscall ABI pending |
| Security | Kernel-enforced capabilities and isolated driver runtime pending |
| Storage and services | Filesystem, package manager, init/service supervisor and installer pending |
| Desktop hardware | Kernel-owned compositor, GPU and audio stack pending |

There is no complete scheduler, process isolation, persistent user session, filesystem, networking stack or kernel driver loader. Policy contracts and host application features do not substitute for these OS services.

## Build and verify

The native build is intended for Linux x86_64. The optional host desktop needs a C++17 compiler and Qt 6 Widgets 6.4+. The release-image workflow additionally uses Git/submodules, CMake, C and C++ compilers, Python 3 build tools, Node.js 22, xorriso, curl, tar, QEMU and OVMF.

Build the native desktop when Qt is available:

~~~sh
cmake -S . -B build/dak-native -DCMAKE_BUILD_TYPE=Release -DDAK_BUILD_NATIVE_DESKTOP=ON
cmake --build build/dak-native --target dak_desktop_native --parallel
ctest --test-dir build/dak-native --output-on-failure
~~~

Run the browser reference preview and its tests:

~~~sh
./scripts/run-mora.sh
npm test
npm run validate:ecosystem
npm run test:ecosystem
~~~

Windows PowerShell preview launcher:

~~~powershell
.\scripts\run-mora.ps1
npm test
~~~

Build the federated Stage 1 release image:

~~~sh
bash boot/build-release-iso.sh --work-dir build/release --output dist/Duck-Stage1-x86_64.iso
~~~

The release pipeline validates pinned sources, builds/tests host workbenches, packages source and notices and records SHA-256 checksums. The resulting ISO is a source-and-tools preview, not a complete installable operating system. A checksum is not a publisher signature.

## Ecosystem and interfaces

The repository pins four independent upstream projects as submodules. Initialize the exact recorded revisions:

~~~sh
git submodule update --init --recursive
~~~

- [Reaper](https://github.com/Ivan-VHS/Reaper) — language, reference runtime and policy contracts.
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) — processor inventory, bounded measurements and C ABI v1.
- [OPlague](https://github.com/Ivan-VHS/OPlague) — read-only device/package evidence and versioned telemetry snapshots.
- [VentuSample](https://github.com/Ivan-VHS/VentuSample) — offline audio generation and versioned sample packs.

Reaper consumes Pytyliki C ABI v1 only through an explicit trusted library path and validates OPlague snapshot/report contracts for read-only analysis. A normalized OPlague GPU telemetry policy adapter exists; trusted native JSON ingestion and publisher/build provenance verification remain pending. A VentuSample pack-v1 consumer remains specified-only. Peer workbenches are user-space projects, not kernel modules or programs that Stage 1 can start.

## Documentation and trust boundaries

- [Implementation status](docs/IMPLEMENTATION_STATUS.md) · [Documentation index](docs/README.md)
- [Bootable Stage 1 image](docs/BOOTABLE_IMAGE.md) · [x86_64 exception handling](docs/X86_64_EXCEPTION_HANDLING.md)
- [Core subsystem MVP contracts](docs/CORE_MVP_V1.md) · [Ecosystem integration](docs/ECOSYSTEM_INTEGRATION.md)
- [Desktop architecture](docs/DAK_DESKTOP.md) · [Unified documentation standard](docs/UNIFIED_DOCUMENTATION_STANDARD.md)
- [Project evolution ladder](docs/PROJECT_EVOLUTION_LADDER.md) · [Engineering roadmap](docs/IMPLEMENTATION_ROADMAP.md)

Never treat a reference policy, a host desktop feature or an initialized submodule as kernel enforcement, native OS integration or hardware access. Imported projects keep their own history, maintainers and upstream licenses. The repository root currently has no `LICENSE` file and does not declare redistribution terms; third-party notices do not grant additional rights.

---
<p align="center"><sub>Duck · repository: Ivan-VHS/DAK · README review 2026-11-27 UTC</sub></p>
