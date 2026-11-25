<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

<h1 align="center"><strong>🦆 Duck — Reaper-First Operating-System Project</strong></h1>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/DAK/actions/workflows/ci.yml) [![Boot image](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/boot-image.yml?branch=main&label=Boot%20image)](https://github.com/Ivan-VHS/DAK/actions/workflows/boot-image.yml) [![Native Mora](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/native-mora.yml?branch=main&label=Native%20Mora)](https://github.com/Ivan-VHS/DAK/actions/workflows/native-mora.yml)

> **A Reaper-first system foundation, a native host desktop and a federated local-first toolchain — with every boundary visible.**

**State:** Experimental · x86_64 Stage 1 QEMU-verified · **Version:** Stage 1 boot foundation · **README standard:** Psychoporter 666 v1.0 · **Last reviewed:** 2026-11-25 UTC · **Source:** [Ivan-VHS/DAK](https://github.com/Ivan-VHS/DAK)

<p align="center"><img src="assets/readme/duckos-overview.svg" alt="Duck system architecture overview" width="100%"></p>

## Quick navigation

[🚀 Demo: Browser reference preview](mora/index.html) · [Documentation](docs/README.md) · [Source](https://github.com/Ivan-VHS/DAK) · [Issues](https://github.com/Ivan-VHS/DAK/issues)

## Mission & scope

Duck is an experimental Reaper-first operating-system project. Its current work is intentionally split into a bootable kernel foundation, Reaper policy contracts and a host-native Mora desktop application.

## Capabilities

- The x86_64 Stage 1 path validates the Limine firmware handoff and Boot Info v1, allocates an early 4 KiB frame, emits DUCKOS_BOOT_OK stage=1 and halts. QEMU BIOS and UEFI checks pass.
- Reaper provides a reference policy-contract track, including 40 Core Subsystem MVP contracts. Native kernel enforcement remains pending.
- Mora has a Qt 6 Widgets host-native desktop application with host-managed windows and a local app catalogue. It is not launched by the Stage 1 kernel.
- mora/index.html remains available as a browser reference preview. It is not a native compositor or the kernel desktop.

## System map

~~~mermaid
flowchart TB
  subgraph BOOT["x86_64 Stage 1 — QEMU verified"]
    L["Limine handoff"] --> B["Boot Info v1"]
    B --> F["Early 4 KiB frame"]
    F --> M["Serial marker / halt"]
  end
  subgraph POLICY["Reaper policy contracts"]
    R["Reference contracts"] --> T["Contract tests"]
    T -.-> N["Native enforcement pending"]
  end
  subgraph HOST["Mora host desktop — separate from kernel"]
    Q["Qt 6 Widgets"] --> W["Host-managed windows"]
    H["Browser reference preview"]
  end
  BOOT -.->|"desktop integration pending"| HOST
~~~

## Build native Mora

The release-image path targets Linux x86_64 and requires Git/submodules, GCC/G++, CMake, Python 3 build tooling, Node.js 22, Qt 6 Widgets, xorriso, curl, tar, QEMU and OVMF.

~~~sh
cmake -S . -B build/mora-native -DCMAKE_BUILD_TYPE=Release -DDUCKOS_BUILD_NATIVE_MORA=ON
cmake --build build/mora-native --target duckos_mora_native --parallel
ctest --test-dir build/mora-native --output-on-failure
~~~

The Qt desktop target is optional and is skipped when Qt 6 Widgets is not found. Mora runs as a host-native application; it is not started by the Stage 1 kernel.

## Browser reference preview

Linux:
~~~sh
./scripts/run-mora.sh
npm test
~~~
Windows PowerShell:
~~~powershell
.\scripts\run-mora.ps1
npm test
~~~

The browser shell is a reference surface. It is not a native compositor and does not imply kernel integration.

## Build the release image

~~~sh
bash boot/build-release-iso.sh --work-dir build/release --output dist/Duck-Release-x86_64.iso
~~~

The release pipeline validates pinned repositories, runs project builds/tests, generates a SHA-256 inventory and assembles a hybrid BIOS/UEFI ISO. This is a source-and-tools preview, not a complete installable OS.

## Kernel status and next layers

| Layer | Status |
|---|---|
| Limine handoff and Boot Info v1 | Implemented; QEMU-verified |
| Early physical-frame allocation | Implemented for Stage 1 |
| Reaper Core Subsystem MVP | 40 reference contracts; native enforcement pending |
| Page tables and address spaces | Pending |
| Interrupts, timers and preemptive scheduler | Pending |
| Process model and syscall ABI | Pending |
| Kernel-enforced capabilities and zero-copy IPC | Pending |
| PCI/USB/ACPI and isolated driver runtime | Pending |
| Filesystem, service supervisor, installer and persistent session | Pending |
| Native compositor, GPU and audio stack | Pending |

The current kernel stage stops after firmware-handoff validation and early frame allocation. It does not yet provide process isolation, driver loading, storage, networking, a persistent user session or kernel-enforced sandboxing. Mora catalogue entries do not execute manifest commands or grant hardware privileges.

## Architecture targets

x86_64 is the primary target for Intel and AMD. Elbrus remains a preserved compatibility track; this does not claim an available Elbrus compiler backend, boot image or physical-hardware test matrix.

## Source federation and integrity

The active source set is pinned in federation/repositories.v1.json. Initialize the exact recorded revisions with:

~~~sh
git submodule update --init --recursive
~~~

The peer projects remain separate repositories with independent ownership, licenses, contracts and release cycles:

- [Reaper](https://github.com/Ivan-VHS/Reaper)
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki)
- [OPlague](https://github.com/Ivan-VHS/OPlague)
- [VentuSample](https://github.com/Ivan-VHS/VentuSample)

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Bootable image](docs/BOOTABLE_IMAGE.md)
- [Core subsystem MVP](docs/CORE_MVP_V1.md)
- [Ecosystem integration](docs/ECOSYSTEM_INTEGRATION.md)
- [Project evolution ladder](docs/PROJECT_EVOLUTION_LADDER.md)
- [Native Reaper integration](docs/REAPER_INTEGRATION.md)
- [Documentation index](docs/README.md)

The implementation-status ledger, bootable-image guide and project evolution ladder are the authoritative records for delivered and pending system layers.

## License and legal status

No LICENSE file or license declaration is present at the repository root. Do not assume MIT, Apache-2.0 or redistribution rights. A license must be selected and approved by the rights holder before distribution.

Do not redistribute bundled or third-party materials outside the applicable license grants. A Git submodule pin records a source revision; it does not change ownership or license terms.

## Engineering rule

Describe behavior from source, tests, schemas, build output and CI evidence. A catalogue or roadmap is not proof of implementation. Browser preferences are not kernel enforcement; PE inspection is not process execution; a checksum is not proof of authorship.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 UTC</sub></p>