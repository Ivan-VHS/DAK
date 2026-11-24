# DuckOS

DuckOS is an operating-system engineering project that combines a Reaper-first system contract, native developer tools and Mora — a browser-based desktop shell for the current user-space experience.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="mora/icon.svg">
  <img src="mora/icon-light.svg" alt="Mora and DuckOS mark: a circular yellow and dark geometric emblem" width="112">
</picture>

[![CI](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/DuckOS/ci.yml?branch=main&style=flat-square&label=CI)](https://github.com/Ivan-VHS/DuckOS/actions/workflows/ci.yml) [![Last commit](https://img.shields.io/github/last-commit/Ivan-VHS/DuckOS?style=flat-square)](https://github.com/Ivan-VHS/DuckOS/commits/main)

[Quick Start](#quick-start) · [Mora Preview](#mora-desktop-preview) · [Architecture](#architecture) · [Applications](#application-catalogue) · [Roadmap](#roadmap) · [Documentation](docs/README.md) · [Commits](https://github.com/Ivan-VHS/DuckOS/commits/main)

> **Status:** Active development. The browser-based Mora shell, Node.js shell tests, Python build/integration tools and a native C11 boot-contract library with CTest coverage are present. DuckOS is **not yet a bootable general-purpose operating-system image**; hardware enforcement and several native backend services remain future work.
>
> **Toolchain:** Node.js 18+ for Mora tests (CI uses Node 22); Python 3.10+ for the CLI and engineering tools; CMake 3.21+ and a C11 compiler for the native contract library. A modern browser is needed for Mora.

## Quick Start

Clone DuckOS with the four pinned specialist repositories:

~~~sh
git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git
cd DuckOS
npm test
~~~

Serve the Mora shell locally:

~~~sh
python -m http.server 8000
~~~

Open [http://localhost:8000/mora/](http://localhost:8000/mora/) in a browser. The shell is a local browser application; it does not acquire native process, kernel or driver privileges.

Install the DuckOS CLI and run its validation tools:

~~~sh
python -m pip install -e .
python -m pip install jsonschema pyyaml
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
python tools/validate_engineering_evolution.py
~~~

Build and test the native C11 boot-contract library:

~~~sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
~~~

## What is implemented

| Component | Current behavior | Boundary |
|---|---|---|
| Mora shell | Browser desktop, application launcher, dock, draggable windows, dashboard, local preferences, keyboard navigation and service-worker cache | Browser-local UI; not a native compositor |
| Mora applications | Application catalogue and local panels for selected workflows | A catalogue entry or concept is not proof of a packaged/native service |
| Mora system tools | Local intent preview, capability preferences, settings backup, PE/ELF inspection, UI resource preferences and SHA-256 hashing | No connected LLM, OS-image rollback, target launch, kernel scheduling or C2PA signer verification |
| Mora Boost | Entry point to OPlague's Windows gaming lab and local evidence workflow | Does not tune a browser host's drivers or kernel |
| DuckOS CLI | Python 3.10+ command-line tools, repository federation, hardware inventory and Reaper integration commands | User-space tooling; no driver installation or privileged host changes |
| Reaper workbench | Discovers the pinned submodule, launches the native Studio process and delegates checks to Reaper | Process-isolated integration; does not embed the runtime into the browser shell |
| Native foundation | C11 startup/boot-info contract library with a CTest suite | No UEFI loader, kernel image, scheduler or hardware backend is produced by this CMake project |
| Hardware inventory | Bounded, read-only PCI/USB inventory and structured report | No install/update/enable/unload operations |

The source distinguishes executable behavior from contract-only or proposed system functions. See [Architecture](docs/ARCHITECTURE.md) for the current implementation boundary.

## Mora desktop preview

[Open the Mora shell source](mora/index.html) or follow the local preview steps above.

Mora currently uses one DuckOS black/white/yellow visual profile: near-black surfaces, white content and a shared duck-yellow accent. The adaptive logo in this README only adapts to GitHub's page theme; it does **not** imply that Mora has separate Light and Dark application modes.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="mora/icon.svg">
  <img src="mora/icon-light.svg" alt="Mora emblem used by the DuckOS desktop shell" width="160">
</picture>

> [!NOTE]
> The repository does not currently contain a captured Mora desktop screenshot. The logo above is branding, not a product screenshot. A real current-state capture should be added to the repository before the README claims visual screenshot coverage.

## Application catalogue

The versioned catalogue contains **20 first-party application concepts**. The Mora shell also exposes system tools and partial browser-local panels. The catalogue is a product/planning contract, not a boot-image manifest or evidence that every concept is a complete native application.

Current system-tool boundaries:

| Tool | Present behavior | Not claimed |
|---|---|---|
| Mora AI | Allowlisted local intent plan, action preview and explicit approval | No connected LLM or arbitrary host shell |
| Sentinel | Capability preference states | Native process enforcement still requires a broker |
| Restore | Backup/restore of Mora preferences | No OS image restore or boot rollback |
| Bridge | Local PE/ELF inspection and reviewable dry-run plans | Does not launch inspected targets |
| Control | Shell focus, reduced-motion and resource-profile preferences | Does not control kernel scheduling or hardware power |
| Proof | Local SHA-256 hashing | Does not verify C2PA manifests or signer identity |
| Mora Boost | OPlague Windows gaming-lab entry point | No browser-side driver or kernel tuning |

The canonical records are [Preinstalled applications](docs/PREINSTALLED_APPLICATIONS.md), the [versioned application catalogue](catalogs/preinstalled-applications.v1.json) and its [JSON Schema](schemas/preinstalled-applications.v1.schema.json). Proposed extensions in the [base application catalogue](catalogs/dak-base-applications.v1.yaml) remain specifications until registered and implemented.

## Federated source workspace

DuckOS pins four specialist repositories as independent Git submodules under projects/:

| Project | Role in the workspace |
|---|---|
| [Reaper](https://github.com/Ivan-VHS/Reaper) | Systems language, reference runtime and native developer workbench |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | Processor inspection and bounded systems utilities |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | Read-only device and driver evidence workbench |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | Procedural sample generation and offline DSP |

To initialize the exact commits pinned by DuckOS in an existing checkout:

~~~sh
python tools/federate_repositories.py sync
~~~

The federation tool validates repository identity, pin and checkout state. It refuses to overwrite local submodule changes. Imported projects are source checkouts, not automatically built, executed, loaded as drivers or promoted to OS services.

## Native Reaper workbench

The Duck Desktop maintenance workspace discovers the pinned projects/reaper checkout, launches Reaper Studio as a separate process and delegates static checks to Reaper's own CLI:

~~~sh
git submodule update --init projects/reaper
duckos reaper status
duckos reaper studio
duckos reaper check ./examples/program.rpr
duckos reaper typecheck ./examples/program.rpr
~~~

These commands belong to the installed DuckOS CLI/native Duck Desktop workflow. The browser-only Mora shell does not launch host processes. See [Native Reaper integration](docs/REAPER_INTEGRATION.md).

## Architecture

~~~mermaid
flowchart TB
    A[Browser] --> B[Mora shell]
    B --> C[Local UI state and shell cache]
    D[DuckOS CLI and native Duck Desktop] --> E[User-space tools]
    E --> F[Reaper / OPlague / Pytyliki integrations]
    G[C11 foundation library] --> H[Boot contract tests]
~~~

| Path | Responsibility |
|---|---|
| mora/ | Browser shell, CSS, modules, manifest, service worker and local theme tokens |
| duckos/ | Python CLI and user-space engineering tools |
| foundation/ | Native C11 boot information and contract library |
| projects/ | Commit-pinned Git submodules for the four specialist repositories |
| catalogs/ and schemas/ | Versioned product, integration and data contracts |
| tools/ and tests/ | Federation, validation, inventory and regression tests |
| docs/ | Architecture, application boundaries and integration contracts |

## Compatibility and safety

| Layer | Requirement / current scope |
|---|---|
| Mora shell | Modern browser; serve repository root over HTTP for service-worker behavior |
| Mora shell tests | Node.js 18+; CI uses Node.js 22 |
| DuckOS CLI and tools | Python 3.10+ |
| Native boot-contract library | CMake 3.21+ and C11 compiler |
| Live hardware inventory | Linux PCI/USB or Windows Plug and Play paths as implemented |
| Bootable OS image / native kernel | Not yet supplied by the current repository build |

DuckOS tools use bounded, read-only inspection by default. A SHA-256 digest proves byte identity only; a matching device ID is not a compatibility certification; and a policy contract is not kernel enforcement.

## Revival highlights

- The opening now describes the actual product boundary and puts clone, preview, test and native build commands first.
- The Mora logo is theme-aware on GitHub, with equal-size local SVG assets.
- The application catalogue, browser shell, native Duck Desktop and future OS services are described separately.
- A missing screenshot and missing license file are stated openly instead of being represented by placeholders or false badges.
- The former seven-app/20-concept wording is reconciled: catalogue concepts and implemented shell panels are different maturity levels.

| Previous README flow | Updated README flow |
|---|---|
| OS, desktop and product catalogue mixed together | Browser shell, native tools and OS foundation separated |
| Roadmap concepts could read like shipped apps | Catalogue maturity is explicit |
| Long descriptions before a runnable entry | Clone, preview and tests at the top |
| Screenshot/license status unclear | Missing artifacts called out honestly |

## Roadmap

- [x] Mora browser shell and local user-space interaction model.
- [x] Node.js Mora test suite and Python engineering/validation CLI.
- [x] Native C11 boot-contract library and CTest target.
- [x] Four specialist repositories pinned as independent submodules.
- [x] Native Reaper launcher and static-check delegation through Duck Desktop/CLI.
- [ ] Add a reproducible current Mora desktop screenshot to assets/screenshots/.
- [ ] Implement privileged capability enforcement and native system-service backends.
- [ ] Add a verifiable bootloader/kernel image pipeline before describing DuckOS as bootable.

## Contributing and project policy

Before opening a pull request, run the Mora tests, Python unit tests, catalogue/evolution validators and native CTest commands shown above. Changes to a versioned catalogue must update its schema/validator and must preserve the rule that submodules are pinned source dependencies, not automatically executed components.

Useful entry points: [documentation index](docs/README.md), [architecture](docs/ARCHITECTURE.md), [Mora design system](MORA_DESIGN_SYSTEM.md), [repository federation](docs/REPOSITORY_FEDERATION.md), [issues](https://github.com/Ivan-VHS/DuckOS/issues) and [commit history](https://github.com/Ivan-VHS/DuckOS/commits/main).

**License:** no LICENSE file is currently present in this repository. Redistribution terms are therefore not specified here; add and review a license before publishing reusable packages or binaries.
