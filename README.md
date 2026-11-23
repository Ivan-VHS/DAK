# DuckOS · Mora Desktop

**Mora** is the unified desktop for the Ivan-VHS application family. The canonical shell lives in [mora/](mora/index.html) and follows the shared [Mora Design System](MORA_DESIGN_SYSTEM.md) and [semantic theme tokens](mora/theme.json).

## One desktop for web and native applications

The home screen presents both application types in one catalogue.

**Seven web applications** — Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify — open their existing browser-based workspaces inside Mora windows. Local browser storage and supported browser APIs remain in use. The web modules retain their current prototype and product-safety boundaries; they are not represented as completed native OS services.

**Four native tools** — Reaper Studio, OPlague, VentuSample and Pytyliki — appear in the same catalogue. Mora discovers local checkouts and built targets, shows their real availability and launches them as separate OS-managed windows through a fixed local allowlist. It does not simulate native windows or run commands supplied by the browser.

## Start the complete workspace

From the DuckOS repository root:

    python mora_host.py

Mora opens at http://127.0.0.1:43860/ and redirects to the canonical PWA shell at /mora/. The same local host serves the embedded web modules, theme API and native launcher. Python 3.10 or newer is required.

For a browser-only preview without native launching, the shell can also be served with:

    python -m http.server 8000

Then open http://localhost:8000/mora/. In this mode the web modules remain available, while native launch controls correctly report that the local launcher is not connected.

Place the application repositories beside DuckOS or set their paths in the user-level Mora workspace configuration. Each native application keeps its own compiler, toolkit, platform and build requirements.

## Shared appearance and behavior

- One home screen, search, category filters and application catalogue.
- One shared dark/light theme defined by mora/theme.json.
- Native startup theme is passed as MORA_THEME_MODE and consumed before each application's widgets are created.
- Embedded web modules receive the active theme from Mora and retain their local browser-based data.
- Native windows stay native; the operating system owns focus, placement, DPI and lifetime.
- The service worker caches the PWA shell but never caches /api responses or native-launch status.

A theme change affects the shell and open web modules immediately. Already-running native processes keep their current appearance; new native windows inherit the current theme.

## Project boundaries

OPlague remains a read-only device and package workbench. VentuSample remains an offline audio renderer/DSP workstation. Pytyliki remains a processor-systems tool and does not gain scheduler, clock, voltage or firmware controls. Reaper's language runtime and compiler tracks remain independent of the desktop shell.

The [Mora integration guide](docs/MORA_DESKTOP.md) documents routes, repository discovery, launch policy and runtime boundaries. The [seven-app specification](docs/PREINSTALLED_APPLICATIONS.md) continues to define the web application identities, capability maturity and consent boundaries. The earlier [seven-app browser prototype](prototype/mora-home.html) is retained as the embedded web-module runtime, not as a competing desktop shell.

Maintained by Ivan-VHS.
