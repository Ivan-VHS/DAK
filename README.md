# 🦆 DAK — Reaper-First Operating-System Project

<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

> **Psychoporter 666** — architectural precision × exploratory energy × traceable evidence. [Shared documentation style](https://github.com/Ivan-VHS/DAK/blob/main/docs/PSYCHOPORTER_DOCUMENTATION_STYLE_V1.md).  
> **Editorial revision · 2026-11-28:** presentation and navigation updated; original authorship, license terms and third-party attribution are retained.


[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/ci.yml?branch=main&label=CI)](https://github.com/Ivan-VHS/DAK/actions/workflows/ci.yml) [![Boot image](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/boot-image.yml?branch=main&label=Boot%20image)](https://github.com/Ivan-VHS/DAK/actions/workflows/boot-image.yml) [![Native DAK](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DAK/native-mora.yml?branch=main&label=Native%20DAK)](https://github.com/Ivan-VHS/DAK/actions/workflows/native-mora.yml)

> **A Reaper-first system foundation, a native host desktop and a federated local-first toolchain — with every boundary visible.**

**State:** Experimental · x86_64 Stage 1 QEMU-verified · **Version:** Stage 1 boot foundation · **README standard:** Psychoporter 666 v1.1 · **Last reviewed:** 2026-11-25 UTC · **Source:** [Ivan-VHS/DAK](https://github.com/Ivan-VHS/DAK)

<p align="center"><img src="assets/readme/dak-overview.svg" alt="DAK system architecture overview" width="100%"></p>

## Quick navigation

[🚀 DAK Desktop HTML demo](desktop/demo/index.html) · [Documentation](docs/README.md) · [Source](https://github.com/Ivan-VHS/DAK) · [Issues](https://github.com/Ivan-VHS/DAK/issues)

## Mission & scope

DAK is an experimental Reaper-first operating-system project. Its current work is intentionally split into a bootable kernel foundation, Reaper policy contracts and a host-native DAK desktop application.

## Capabilities

- The x86_64 Stage 1 path validates the Limine firmware handoff and Boot Info v1, allocates an early 4 KiB frame, emits the Stage 1 serial success marker and halts. QEMU BIOS and UEFI checks pass.
- Reaper provides a reference policy-contract track, including 40 Core Subsystem MVP contracts. Native kernel enforcement remains pending.
- DAK has a Qt 6 Widgets host-native desktop application with host-managed windows and a local app catalogue. It is not launched by the Stage 1 kernel.
- desktop/demo/index.html remains available as a browser reference preview. It is not a native compositor or the kernel desktop.

## DAK Desktop

- The Qt 6 host-native shell opens separate top-level windows managed by the host OS; it is not the DAK kernel compositor.
- Reaper desktop policies validate window actions, geometry, density profiles and versioned session snapshots.
- The [interactive HTML demo](desktop/demo/index.html) runs locally; resource and device values are illustrative demo data.
- Architecture and engineering direction: **Ivan-VHS**. See [DAK Desktop](docs/DAK_DESKTOP.md).

## Contents

- [System map](#system-map)
- [Capabilities](#capabilities)
- [Source federation and integrity](#source-federation-and-integrity)
- [Build native DAK](#build-native-dak)
- [Browser reference preview](#browser-reference-preview)
- [Build the release image](#build-the-release-image)
- [Kernel status and next layers](#kernel-status-and-next-layers)
- [Architecture targets](#architecture-targets)
- [Source federation and integrity](#source-federation-and-integrity)
- [Licensing and attribution](#licensing-and-attribution)
- [Engineering rule](#engineering-rule)

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
  subgraph HOST["DAK host desktop — separate from kernel"]
    Q["Qt 6 Widgets"] --> W["Host-managed windows"]
    H["Browser reference preview"]
  end
  BOOT -.->|"desktop integration pending"| HOST
~~~

## Build native DAK

The release-image path targets Linux x86_64 and requires Git/submodules, GCC/G++, CMake, Python 3 build tooling, Node.js 22, Qt 6 Widgets, xorriso, curl, tar, QEMU and OVMF.

~~~sh
cmake -S . -B build/dak-native -DCMAKE_BUILD_TYPE=Release -DDAK_BUILD_NATIVE_DESKTOP=ON
cmake --build build/dak-native --target dak_desktop_native --parallel
ctest --test-dir build/dak-native --output-on-failure
~~~

The Qt desktop target is optional and is skipped when Qt 6 Widgets is not found. DAK runs as a host-native application; it is not started by the Stage 1 kernel.

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
bash boot/build-release-iso.sh --work-dir build/release --output dist/DAK-Release-x86_64.iso
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

The current kernel stage stops after firmware-handoff validation and early frame allocation. It does not yet provide process isolation, driver loading, storage, networking, a persistent user session or kernel-enforced sandboxing. DAK catalogue entries do not execute manifest commands or grant hardware privileges.

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

## Licensing and attribution

The federated workbenches remain independently licensed. Their declared license identifiers and pinned source revisions are recorded in [the repository federation manifest](federation/repositories.v1.json). Preserve each upstream repository's `LICENSE` file and applicable notices with its source; federation does not relicense or transfer ownership of those components.

The DAK root repository currently has no root-level `LICENSE` file, so this README does not claim a single project-wide license for DAK-owned files or for the federated source. A root-project license remains an explicit governance decision and should be published before a common license grant is claimed.

## Engineering rule

Describe behavior from source, tests, schemas, build output and CI evidence. A catalogue or roadmap is not proof of implementation. Browser preferences are not kernel enforcement; PE inspection is not process execution; a checksum is not proof of authorship.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 UTC</sub></p>

## Contributing

Read the [CONTRIBUTING.md](CONTRIBUTING.md) guide before changing code, contracts or documentation. Keep changes reviewable, run the affected checks and describe implementation evidence accurately.
