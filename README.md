# DuckOS · Mora desktop

DuckOS is the operating-system project. **Mora** is its unified desktop: one home screen, one app catalogue, one visual language and one window workspace for browser-based applications, built-in system tools and native project applications.

## One desktop, three content types

The canonical shell is [mora/index.html](mora/index.html), styled by [mora/styles.css](mora/styles.css) and powered by [mora/app.js](mora/app.js). Its catalogue contains 17 entries:

**Seven first-party web workspaces** — Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. They open inside Mora windows using the maintained local browser module runtime in [prototype/mora-home.html](prototype/mora-home.html). They can work with browser-local data and supported browser APIs. Microphone, camera, screen-capture and clipboard access remain subject to browser permissions. These modules are not native OS services.

**Six Mora system tools** — Mora AI, Sentinel, Restore, Bridge, Control and Proof. They provide the current browser-shell functions: allowlisted intent planning with explicit approval, local permission preferences, shell-settings recovery, PE/ELF header inspection, workspace preferences and SHA-256 hashing. They do not claim to be kernel services, a native capability broker, atomic OS updater or executable loader.

**Four native project applications** — Reaper Studio, OPlague, VentuSample and Pytyliki. They appear in the same catalogue and open a Mora details window with build readiness and a launch action. Mora starts them as separate OS-managed processes using fixed entry points. Native windows are not embedded in browser iframes.

## Start the combined workspace

From the DuckOS repository root:

    python mora_host.py

The local host listens only on 127.0.0.1:43860 and opens the canonical desktop at http://127.0.0.1:43860/mora/. It serves the PWA assets, the seven embedded web modules and the local application-discovery/launch API.

To preview only the browser desktop without native launching, use a static server:

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

## Shared visual system

The authoritative design and semantic tokens are [MORA_DESIGN_SYSTEM.md](MORA_DESIGN_SYSTEM.md) and [mora/theme.json](mora/theme.json). The PWA, embedded web modules and native adapters use the same dark/light palette, typography hierarchy, spacing, focus, motion and surface roles. The local host passes MORA_THEME_MODE=dark|light to new native processes. Existing native windows retain their current appearance until restarted.

The service worker is scoped to /mora/ and caches the PWA shell assets. The local /api/ endpoints are outside that cache scope and are used only when the loopback host is running.

## Safety and maturity

- The browser sends only one of four registered native app IDs. It cannot supply a shell command or executable path.
- The local launcher resolves each native target from a fixed per-app allowlist; manifest entrypoint fields remain descriptive metadata.
- Native programs run as separate user processes; this does not provide process sandboxing or a native capability broker.
- OPlague remains read-only. Mora does not elevate privileges or install drivers.
- VentuSample remains an offline audio renderer and DSP workstation, not a DAW or device host.
- Pytyliki remains a processor-systems tool; Mora adds no scheduler, clock, voltage or firmware controls.
- Reaper's language runtime and compiler tracks remain independent of the desktop shell.
- The seven browser workspaces retain their current prototype limits and consent boundaries, documented in [PREINSTALLED_APPLICATIONS.md](docs/PREINSTALLED_APPLICATIONS.md).

Implementation maturity is described from source and CI evidence, not from the presence of a tile or design specification.

## Validate

    npm test
    python -m pip install jsonschema
    python -m unittest discover -s tests -v
    python tools/validate_app_catalog.py

Maintained by Ivan-VHS.
