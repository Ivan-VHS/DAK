# DuckOS repository federation

DuckOS keeps the four specialist repositories as pinned Git submodules. This gives the OS workspace a real checkout of every source project while preserving each project's own Git history, release cadence, build system, contributors and licence notices.

## Included repositories

| Workspace path | Upstream project | Domain | License |
|---|---|---|---|
| `projects/pytyliki` | [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | C11 processor and host systems workstation | MIT |
| `projects/reaper` | [Reaper](https://github.com/Ivan-VHS/Reaper) | language, reference runtime, IDE and toolchain | Apache-2.0 |
| `projects/oplague` | [OPlague](https://github.com/Ivan-VHS/OPlague) | read-only device and driver evidence workstation | Apache-2.0 |
| `projects/ventusample` | [VentuSample](https://github.com/Ivan-VHS/VentuSample) | C++20 procedural audio and offline DSP | Apache-2.0 |

## Current reviewed source pins — 2026-11-25

The following Gitlinks and the registry/release manifests advance together. These are exact upstream `main` commits, not floating branch references.

| Project | Upstream pin | Primary native interface | DuckOS-side handling |
|---|---|---|---|
| Reaper | `dd652a77c905eca518873cd28f94550b22de9f11` | C17 System ABI, DABI64 Desktop Host v1 and Reaper FFI v1 | bounded user-space CLI workbench; ABI libraries packaged separately |
| Pytyliki | `455e1c9d397b6dd308a9ce68aa194e686fa4fa1a` | C11 core and Pytyliki C ABI v1 | optional explicit-path metric bridge; host libraries packaged |
| OPlague | `a7b9d6bca778cd0556fd7c0f621e7715ad282063` | versioned read-only device-snapshot JSON | source, tests and evidence schemas packaged; no driver installation or device writes |
| VentuSample | `8363c33138027856ac6cac4821b471e990caeace` | C++20 core, C11 DSP compatibility library and versioned pack manifests | offline host library and optional Qt tool; optional Reaper C17 FFI link |

DuckOS remains the fifth repository and integration host. The four specialist projects remain independently versioned and are included as exact Git submodules.

DuckOS itself is the fifth repository and remains the superproject. It must not add itself as a submodule.

## First checkout

```sh
git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git
cd DuckOS
python tools/federate_repositories.py status
```

For an existing DuckOS clone:

```sh
python tools/federate_repositories.py sync
```

The sync command validates the registry, `.gitmodules` and all four pinned Git links, then runs Git's recursive submodule initialization at the exact commits recorded in the superproject. It does not use `--remote`, so it will not silently advance to whatever happens to be newest on upstream `main`.

## Status and validation

```sh
python tools/federate_repositories.py validate
python tools/federate_repositories.py status --json
python -m unittest tests.test_repository_federation -v
```

The registry is machine-readable at `federation/repositories.v1.json`; its contract is in `schemas/repository-federation.v1.schema.json`. The existing `manifests/ivan-vhs-program-adoption.v1.json` remains the authority for the disjoint 1,000-entry catalogue allocation. The repository federation registry is the authority for source URLs, checkout paths, commit pins, licences and runtime boundaries.

## How projects fit together

- **Pytyliki** provides processor inventory and bounded benchmark/profile evidence. Its C ABI v1 is an optional, explicitly selected native interface used by Reaper and OPlague. It must not silently change clocks, voltage, affinity, fan curves or firmware.
- **Reaper** is the user-space language and toolchain. Duck Desktop and the `duckos reaper` CLI use a bounded subprocess bridge. Its C17 System ABI and DABI64 Desktop Host v1 are source-of-truth contracts; their presence does not mean the Stage 1 kernel already dispatches these operations.
- **OPlague** exports bounded, versioned, read-only device evidence. It can use explicit Reaper C17 and Pytyliki C ABI libraries for optional cross-checks; device matches remain candidates, not permission to install a driver.
- **VentuSample** owns offline audio generation and DSP. Its CMake project can link Reaper's C17 FFI only when `REAPER_SOURCE_DIR` is explicitly set. Real-time audio and device access need a separate service design.

The build/link dependency graph is acyclic: Reaper may optionally consume Pytyliki; OPlague may optionally consume Reaper and Pytyliki; VentuSample may optionally consume Reaper. Reaper's OPlague snapshot reader is a read-only file-format integration, not a build dependency. All native library loads require explicit paths and ABI checks.

## Reproducibility and safety

Every superproject commit pins exact submodule commits. Update pins intentionally in a reviewed change after upstream tests and license/provenance checks. Do not use branch heads as build inputs.

Before syncing, the tool refuses to proceed if an initialized top-level submodule has local modifications or untracked files. Commit or move local work first. Recursive submodules are included if an upstream project adds any later.

Submodule initialization only downloads source. It does not run imported content. `auto_build=false` means no background or implicit build is triggered by discovery; the explicit ecosystem release command builds and tests each project in separate host build directories. `auto_execute=false` remains mandatory. A cloned repository or packaged host library is not thereby a DuckOS kernel module, trusted driver or application executable inside the Stage 1 image.

Each upstream LICENSE and its notices remain in the original checkout. Pytyliki is MIT; Reaper, OPlague and VentuSample are Apache-2.0. Preserve both the top-level notices and any third-party attribution shipped by each project.

## Optional local VentuSample + Reaper CMake integration

VentuSample can be configured against the pinned Reaper checkout when that optional native integration is needed:

```sh
cmake -S projects/ventusample -B build/ventusample \
  -DREAPER_SOURCE_DIR="$PWD/projects/reaper"
cmake --build build/ventusample --parallel
```

This is a developer build of those user-space projects; it is not part of DuckOS's boot chain and is not automatically invoked by the OS build.
