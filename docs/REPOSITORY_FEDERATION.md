# DuckOS repository federation

DuckOS keeps the four specialist repositories as pinned Git submodules. This gives the OS workspace a real checkout of every source project while preserving each project's own Git history, release cadence, build system, contributors and licence notices.

## Included repositories

| Workspace path | Upstream project | Domain | License |
|---|---|---|---|
| `projects/pytyliki` | [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | C11 processor and host systems workstation | MIT |
| `projects/reaper` | [Reaper](https://github.com/Ivan-VHS/Reaper) | language, reference runtime, IDE and toolchain | Apache-2.0 |
| `projects/oplague` | [OPlague](https://github.com/Ivan-VHS/OPlague) | read-only device and driver evidence workstation | Apache-2.0 |
| `projects/ventusample` | [VentuSample](https://github.com/Ivan-VHS/VentuSample) | C++20 procedural audio and offline DSP | Apache-2.0 |

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

- **Pytyliki** provides processor inventory and bounded benchmark/profile evidence. Its Win32 GUI is launched as a separate native window when the pinned checkout contains the built target. DuckOS consumes only reviewed versioned interfaces or JSON reports; it must not silently change clocks, voltage, affinity, fan curves or firmware.
- **Reaper** is the user-space language and toolchain. Its federation status is `native-workbench`: Mora, Duck Desktop and the `duckos reaper` CLI can launch Studio or request static checks through a bounded subprocess bridge. Imported interpreters, plugins and programs never become kernel code.
- **OPlague** provides read-only device, package and driver evidence. Its Python/Tk workbench has a native launcher; live Plug and Play inventory remains Windows-only. Device matches are candidates, not permission to install a driver.
- **VentuSample** owns audio generation and offline DSP. Its Qt 6 / C++20 workstation is launched when a built native target is available. Its CMake project supports an optional local Reaper source path; this is recorded as an optional dependency, not a mandatory boot dependency. Real-time audio and device access need a separate service design.

Preferred integration order is versioned JSON first, narrow C ABI second, and IPC only after DuckOS has a process model, capabilities, resource quotas, cancellation and audit. Keep the upstream projects separate; use adapters under DuckOS rather than copying source files into kernel or Mora directories.

## Native application launcher

The native Mora Qt shell lists all four specialist projects in the same searchable application catalogue. A fixed DuckOS launcher resolves the registered project paths under `projects/`, checks the platform and documented entry point, then starts a separate user-space process only after the user selects Open. The CLI exposes the same registry through `duckos apps list` and `duckos apps open <id>`.

The registry distinguishes source checkout, runtime readiness and native build availability. Pytyliki is Windows-only; OPlague requires Python 3.10+ and Tkinter; VentuSample requires a platform-specific Qt 6 build; Reaper uses its existing Studio bridge. A missing executable is reported as unavailable instead of triggering an implicit build. See [Native specialist applications](NATIVE_PROJECT_APPLICATIONS.md) for commands, build instructions, platform limitations and verification.

## Reproducibility and safety

Every superproject commit pins exact submodule commits. Update pins intentionally in a reviewed change after upstream tests and license/provenance checks. Do not use branch heads as build inputs.

Before syncing, the tool refuses to proceed if an initialized top-level submodule has local modifications or untracked files. Commit or move local work first. Recursive submodules are included if an upstream project adds any later.

Submodule initialization only downloads source. The federation tool never compiles or runs imported content. All entries have `auto_build=false` and `auto_execute=false`. A cloned repository is not thereby a DuckOS app, kernel driver, trusted package or bootable OS feature.

Each upstream LICENSE and its notices remain in the original checkout. Pytyliki is MIT; Reaper, OPlague and VentuSample are Apache-2.0. Preserve both the top-level notices and any third-party attribution shipped by each project.

## Optional local VentuSample + Reaper CMake integration

VentuSample can be configured against the pinned Reaper checkout when that optional native integration is needed:

```sh
cmake -S projects/ventusample -B build/ventusample \
  -DREAPER_SOURCE_DIR="$PWD/projects/reaper"
cmake --build build/ventusample --parallel
```

This is a developer build of those user-space projects; it is not part of DuckOS's boot chain and is not automatically invoked by the OS build.
