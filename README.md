# DuckOS · Mora desktop

DuckOS is the operating-system project. **Mora** is its unified desktop: one home screen, one application catalogue, one visual language and one window workspace for browser content, system tools and native project applications.

## One desktop, three content types

The canonical shell is [mora/index.html](mora/index.html), styled by [mora/styles.css](mora/styles.css) and powered by [mora/app.js](mora/app.js). Its catalogue contains 17 entries:

**Seven first-party web workspaces** — Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. They open inside Mora windows using the maintained local browser module runtime in [prototype/mora-home.html](prototype/mora-home.html). They use browser-local data and supported browser APIs. Microphone, camera, screen-capture and clipboard access remain subject to browser permissions. These modules are not native OS services.

**Six Mora system tools** — Mora AI, Sentinel, Restore, Bridge, Control and Proof. They provide the current browser-shell functions: allowlisted intent planning with explicit approval, local permission preferences, shell-settings recovery, PE/ELF header inspection, workspace preferences and SHA-256 hashing. They do not claim to be kernel services, a native capability broker, atomic OS updater or executable loader.

**Four native project applications** — Reaper Studio, OPlague, VentuSample and Pytyliki. They appear in the same catalogue and open a Mora details window with build readiness and a launch action. Mora starts them as separate OS-managed processes using fixed entry points. Native windows are not embedded in browser iframes.

## The 1,000-program ecosystem contract

The 1,000-entry catalogue is an **ownership and integration plan**, not a request to bundle 1,000 applications or copy their source code. The four specialist repositories own their domains:

| Repository | Assigned entries | Responsibility |
|---|---:|---|
| Pytyliki | 200 | CPU/host inventory, bounded benchmarks and system evidence |
| Reaper | 250 | Language/runtime, compiler, IDE and developer tooling |
| OPlague | 200 | Device/driver inspection, package and provenance evidence |
| VentuSample | 350 | DSP, audio analysis, sampling, synthesis and offline rendering |
| DuckOS | 0 catalogue IDs | OS integration, IPC, system services and packaging |

The versioned ownership allocation is in [manifests/ivan-vhs-program-adoption.v1.json](manifests/ivan-vhs-program-adoption.v1.json). Its interfaces, safety rules and adoption order are described in [PROGRAM_CATALOGUE_INTEGRATION.md](docs/PROGRAM_CATALOGUE_INTEGRATION.md). These are integration contracts, not proof that every listed capability is implemented. Hardware inspection stays read-only, Reaper runs in user space, OPlague never installs inspected packages, and VentuSample remains an offline DSP owner unless a separately reviewed audio service exists.

## Start the combined workspace

From the DuckOS repository root:

    python mora_host.py

The local host listens only on 127.0.0.1:43860 and opens the canonical desktop at http://127.0.0.1:43860/mora/. It serves the PWA assets, the seven embedded web modules and the local application-discovery/launch API.

For a browser-only preview without native launching:

    python -m http.server 8000

Open http://localhost:8000/mora/. The web modules and Mora system tools remain available, while native applications correctly report that the local launcher is not connected.

Python 3.10 or newer is required for the local launcher. Place the four application repositories beside DuckOS or configure their local paths in the user-level Mora workspace settings. Each project retains its own compiler, toolkit, platform and build requirements.

## Native launch readiness

| Application | Existing entry point | Availability requirement |
|---|---|---|
| Reaper Studio | reaper_desktop.py | Reaper checkout and Python/Tk desktop dependencies |
| OPlague | oplague_app.py | OPlague checkout and Python/Tk desktop dependencies |
| VentuSample | CMake target VentuSample | Built Qt 6 Widgets desktop target |
| Pytyliki | pytyliki-gui.exe | Built Windows GUI target |

A card is not marked ready merely because a repository is listed. Mora checks the local checkout and expected executable target. Unbuilt targets remain disabled with an explanatory status.

## Shared design and maturity

The authoritative visual and semantic tokens are [MORA_DESIGN_SYSTEM.md](MORA_DESIGN_SYSTEM.md) and [mora/theme.json](mora/theme.json). The PWA, embedded web modules and native adapters use the same dark/light palette, typography hierarchy, spacing, focus, motion and surface roles. The local host passes MORA_THEME_MODE=dark or light to newly started native processes. Existing native windows retain their current appearance until restarted.

The service worker is scoped to /mora/ and caches the current modular shell assets. The local /api/ endpoints are not used as cached availability or launch state.

Browser and native capability boundaries remain explicit. The presence of a card, specification or policy toggle does not establish that a kernel, driver, compositor, updater, sandbox or hardware service is implemented. Current maturity is described in [Mora integration](docs/MORA_INTEGRATION.md), [the detailed desktop integration guide](docs/MORA_DESKTOP.md) and the [system policy](mora/system-policy.json).

## Validate

    npm test
    python -m pip install jsonschema
    python -m unittest discover -s tests -v
    python tools/validate_app_catalog.py
    python tools/validate_program_adoption.py

Maintained by Ivan-VHS. Preserve the authorship, contributions and license notices of existing contributors and dependencies.
