# DuckOS

DuckOS is the planned operating-system integration target for the Ivan-VHS project family.

> **Current repository status:** bootstrap/documentation stage. This repository currently does not contain an executable kernel, bootloader, initramfs, device-driver stack, compositor, package manager or installation image. This README and the integration contract describe intended boundaries; they are not a claim that an operating system is already bootable.

## Project-family integration

The 1,000-item adoption catalogue is divided by responsibility across four specialist repositories. DuckOS is the future host for selected user-space services; it does not absorb or duplicate their implementations.

| Project | Catalogue IDs | Responsibility | Intended OS boundary |
|---|---:|---|---|
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | 1–120, 171–250 | CPU/host inventory, bounded benchmarks, profiling evidence, static analysis and embedded reference tools | Read-only system-inspection service and versioned C ABI |
| [Reaper](https://github.com/Ivan-VHS/Reaper) | 251–500 | Language, runtime, compiler tooling, Studio, LSP/DAP and build/test adapters | Quota-limited user-space tools and optional sandboxed extensions |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | 501–700 | Device/driver inventory, package inspection, signatures, hashes and SBOM evidence | Read-only package and device-evidence service |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | 121–170, 701–1000 | DSP, sample generation, WAV/MIDI, synthesis, effects and audio analysis | Offline audio/render service; real-time audio is a separate future capability |

The sound-processing range 121–170 belongs to VentuSample, not Pytyliki. This avoids two competing owners for DSP and audio code.

## Integration contract

The cross-project contract is in [docs/PROGRAM_CATALOGUE_INTEGRATION.md](docs/PROGRAM_CATALOGUE_INTEGRATION.md). Its machine-readable allocation is [manifests/ivan-vhs-program-adoption.v1.json](manifests/ivan-vhs-program-adoption.v1.json), validated against [schemas/ivan-vhs-program-adoption.v1.schema.json](schemas/ivan-vhs-program-adoption.v1.schema.json).

Core rules:

- Keep the kernel independent of Python, Qt, desktop applications and optional project runtimes.
- Communicate across project boundaries through narrow, versioned C ABIs or versioned data/IPC contracts.
- Run Reaper and OPlague tools in user space with explicit capabilities and resource limits.
- Keep driver/package inspection read-only. Inspection does not imply installation, trust or compatibility.
- Keep VentuSample offline and deterministic by default. An audio server or real-time device path requires its own scheduling, permission and latency design.
- Do not copy upstream implementation code. Reimplement ideas independently or add only license-reviewed dependencies.

## Development order

1. Establish kernel/user-space, IPC, package and service contracts.
2. Build a minimal bootable target and test it in an emulator before adding hardware-specific paths.
3. Add read-only host/device discovery adapters.
4. Add isolated language/tooling and offline audio services.
5. Connect the services to a compositor and installer only after their interfaces and failure modes are tested.

## Evidence and status

A catalogue entry is an adoption idea, not a shipped feature. A capability can be called implemented only when its source, build integration, tests, permissions, resource limits and documented failure behavior are present. Until then it remains proposed or in development.

See the four specialist repositories for their own code, feature matrices and adoption maps.