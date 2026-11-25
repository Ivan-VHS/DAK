# DuckOS

**A Reaper-first operating-system project with a local-first desktop shell and a federated native-tooling ecosystem.**

<p align="center">
  <img src="assets/readme/duckos-overview.svg" alt="DuckOS architecture overview: Stage 1 boot, Reaper policy contracts and the separate Mora host shell" width="100%">
</p>

<p align="center">
  <a href="mora/index.html">Open Mora</a> ·
  <a href="docs/RELEASE_EDITION.md">Release edition</a> ·
  <a href="docs/ARCHITECTURE.md">Architecture</a> ·
  <a href="docs/IMPLEMENTATION_STATUS.md">Implementation status</a> ·
  <a href="docs/IMPLEMENTATION_ROADMAP.md">Roadmap</a>
</p>

> **Current release boundary:** DuckOS has an experimental x86_64 Stage 1 kernel image that passes QEMU BIOS and UEFI boot checks. The kernel validates the firmware handoff, allocates and clears an early 4 KiB frame, emits `DUCKOS_BOOT_OK stage=1`, and halts. Mora is a separate host-browser application; it is not started by this kernel.

## System map

The three implementation tracks are deliberately shown separately. A policy contract, host application and bootable kernel stage are different kinds of evidence.

```mermaid
flowchart TB
  subgraph BOOT["DuckOS native boot path — QEMU verified"]
    L["Limine firmware handoff"] --> B["x86_64 Stage 1 entry"]
    B --> V["Boot Info v1 validation"]
    V --> F["Early 4 KiB frame allocation"]
    F --> M["DUCKOS_BOOT_OK stage=1"]
    M --> H["Kernel halts"]
  end

  subgraph POLICY["Reaper policy and contract track"]
    R["Reaper reference runtime"] --> C["Deterministic system contracts"]
    C --> T["Contract tests and CI"]
  end

  subgraph HOST["Mora host application — separate from kernel"]
    W["Local static server / browser"] --> S["Mora shell"]
    S --> A["Launcher, windows, preferences"]
    S --> P["Project workbench panels"]
  end

  BOOT -. "native runtime integration pending" .- POLICY
  HOST -. "not launched by Stage 1" .- BOOT
```

## What is included

| Area | Present today | Boundary |
|---|---|---|
| **Mora desktop shell** | Responsive local browser workspace, launcher, interactive windows, dock, local preferences, reduced-motion mode, local app data and scoped offline cache | Runs on the host browser; not a native kernel compositor |
| **Reaper policy layer** | Startup, memory-range, scheduling, bounded IPC, capabilities, service-restart and other deterministic reference contracts | Reference-runtime policy; not yet a privileged native kernel runtime |
| **x86_64 boot foundation** | Limine handoff, Boot Info v1 validation, early monotonic physical-frame allocation and serial boot marker | Stage 1 only; no process or service session |
| **Ecosystem payload** | Pinned source, documentation, schemas, licenses, Mora assets and tested host tools | Host tools are not DuckOS kernel executables |
| **Release pipeline** | Source-pin validation, project builds/tests, SHA-256 inventory, hybrid BIOS/UEFI ISO and QEMU boot checks | Preview source-and-tools distribution, not a complete installable OS |

## Federated workbenches

The four repositories below are pinned by exact Git commits in `federation/repositories.v1.json`. Their source trees and license notices remain attributable to their own projects.

| Project | Role in the ecosystem | Native foundation |
|---|---|---|
| [Reaper](https://github.com/Ivan-VHS/Reaper) | Language, compiler tooling and system-policy contracts | C17 native track plus reference runtime |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | Processor inspection, bounded analysis and profiling | C11 core, CLI and Windows desktop |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | Read-only device/driver evidence and compatibility workbench | Local user-space inspection tools |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | Procedural samples and offline audio processing | C++20 core and optional Qt 6 desktop |

Mora workbench panels provide local documentation, descriptions and build/test guidance. Browser code does not execute external commands or grant hardware privileges.

## Open Mora

For a browser preview, open `mora/index.html`. For offline assets and the bundled project documentation, run the local server.

**Linux**
```sh
./scripts/run-mora.sh
```

**Windows PowerShell**
```powershell
.\scripts\run-mora.ps1
```

The server binds to `127.0.0.1`. Keep its terminal open while Mora is in use. No cloud service or external CDN is required for the shell itself.

Run the Mora contract suite with Node.js 22+:

```sh
npm test
```

## Build the release ISO

The reproducible release pipeline targets Linux x86_64 and expects Git/submodules, GCC/G++, CMake, Python 3, Node.js 22, Qt 6 Widgets, xorriso, curl, tar, QEMU and OVMF.

```sh
git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git
cd DuckOS
bash boot/build-release-iso.sh --work-dir build/release --output dist/DuckOS-Release-x86_64.iso
```

The pipeline validates repository pins, tests Mora, builds/tests the Reaper and Pytyliki host tools, builds/tests VentuSample, verifies OPlague source and tests, packages source and license notices, checks the SHA-256 inventory, and produces a hybrid BIOS/UEFI ISO. GitHub Actions runs the release pipeline and QEMU boot gates.

The ISO is content-sized. It is not padded to 4 GiB: empty bytes would only increase download size without adding a filesystem, application or operating-system capability. See [Release edition](docs/RELEASE_EDITION.md) for exact payload contents and commands.

## Kernel status and next layers

| Layer | Status |
|---|---|
| Limine firmware handoff and Boot Info v1 validation | Implemented and QEMU-verified |
| Early physical-frame allocation | Implemented for the Stage 1 boot path |
| Reusable memory manager, page tables and address spaces | Pending |
| Interrupts, timers, preemptive scheduler and process model | Pending |
| Syscall ABI, kernel-enforced capabilities and zero-copy IPC | Pending |
| PCI/USB/ACPI discovery and isolated driver runtime | Pending |
| Filesystem, service supervisor, installer and persistent user session | Pending |
| Native compositor, GPU and audio stack | Pending |
| Freestanding native Reaper compiler/backend | Pending |

There is no claim of physical-hardware qualification, Secure Boot support, a disk installer, a native Mora compositor, a general process model or kernel-enforced sandboxing. See [Implementation status](docs/IMPLEMENTATION_STATUS.md) and [Architecture](docs/ARCHITECTURE.md) for the detailed evidence ledger.

## Source federation and integrity

The active source set is defined in `federation/repositories.v1.json`. Initialize the exact pinned sources with:

```sh
git submodule update --init --recursive
```

The pre-release DuckOS repository snapshot is preserved on `archive/pre-release-snapshot-2026-11-25`. That branch preserves this repository's Git state; it does not recreate the histories of external repositories.

## Engineering rule

Describe behavior from source, tests, schemas, build output and CI evidence. A catalogue or roadmap is not proof of implementation. Browser preferences are not kernel enforcement; PE inspection is not process execution; a checksum is not proof of authorship.
