# Mora desktop — unified web and native workspace

**Canonical shell:** mora/index.html  
**Canonical theme:** mora/theme.json · schema mora.theme.v1  
**Design contract:** MORA_DESIGN_SYSTEM.md  
**Local host:** http://127.0.0.1:43860

Mora is one desktop for two runtime types: seven browser-based applications and four native project tools. The canonical PWA shell supplies the home screen, app catalogue, category navigation, search, shared theme, application details and native launch controls. Both groups are visible in the same workspace.

## Canonical routes and runtime

| Route | Purpose |
|---|---|
| / | Redirect to /mora/ |
| /mora/ | Canonical Mora PWA desktop |
| /projects | Detailed native project catalogue |
| /prototype/mora-home.html | Existing seven-app browser workspace; also used as the embedded module runtime |
| /api/apps | Local app discovery, availability and current theme |
| /api/theme | Persist the dark/light preference |
| /api/launch/{id} | Launch one fixed native app ID |

The full experience runs with:

    python mora_host.py

The host binds to 127.0.0.1, serves the PWA and its embedded web-module runtime, persists the desktop theme and exposes the allowlisted native launcher. Opening mora/index.html through a static web server still gives the web catalogue and embedded browser apps, but native-launch controls remain unavailable because no local process bridge exists.

## Web applications inside Mora

The seven product identities remain Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. Clicking a web-app card opens its current working browser surface inside a Mora application window. The module content comes from the maintained seven-app prototype at prototype/mora-home.html; it is loaded in embedded mode rather than copied into a second implementation.

| App | Current browser scope | Native/OS integration still missing |
|---|---|---|
| Cockos | Browser microphone capture, local tracks and mixdown | System-wide per-app audio sessions and native recorder service |
| Kavun | Local media library, slices and non-destructive preview/export | Image understanding and automatic location indexing |
| Ka-bon | Local expenses, attached receipts, subscriptions and family records | Receipt OCR, bank integrations and cloud sharing |
| Gloverty | User-authored local rules and manually invoked supported actions | OS scheduling, global gestures and global shortcuts |
| Po | Local tab records, external navigation and reading view | Browser-engine isolation and tracker-blocking network stack |
| Illidia | Local game catalogue, progress, achievements and user-authorized screen clips | Native executable launcher, cloud saves and platform achievement providers |
| Unify | Local device labels, browser clipboard and bounded JSON export/import | Authenticated pairing, live synchronization and phone notification service |

These are existing browser-prototype capabilities, not claims that the corresponding native DuckOS services are complete. Browser permissions such as microphone, camera, display capture and clipboard remain controlled by the browser and require user permission. Local application data stays in the same browser origin.

The authoritative product maturity and safety specification remains PREINSTALLED_APPLICATIONS.md, with its machine-readable catalog in catalogs/preinstalled-applications.v1.json.

## Native applications in the same catalogue

Mora queries /api/apps and matches each known app ID to its repository and build target. It enables launch only when the directory and expected entry point are present. Selecting an available app posts a fixed ID to /api/launch/{id}; the host uses a per-app launch allowlist and starts the program as a separate native process.

| Project | Role | Launch target |
|---|---|---|
| Reaper Studio | MOST/Reaper language, IDE, check/run, debugger and LSP/DAP | reaper_desktop.py through the current Python interpreter |
| OPlague | Read-only device inventory and INF/ZIP/PE inspection | oplague_app.py through Python |
| VentuSample | C++20 / Qt 6 sample workstation and offline DSP | Existing built VentuSample desktop target |
| Pytyliki | C11 processor-systems workstation and Win32 GUI | Existing built pytyliki-gui.exe on Windows |

A local repository checkout can be discovered by its expected directory even if its descriptive mora-app.json has not yet merged. The manifest is used for metadata, never as executable configuration. The actual launch target remains fixed in mora_host.py. Missing folders or unbuilt executables are shown as unavailable, not simulated.

Mora does not embed native windows in iframes. The browser shell is the common desktop and launch surface; the operating system owns native window placement, focus, DPI, privileges and lifetime.

## Repository discovery

Place the repositories beside DuckOS:

    workspace/
    ├── DuckOS/
    ├── Reaper/
    ├── OPlague/
    ├── VentuSample/
    └── Pytyliki/

Mora also checks a workspace subdirectory and Projects directories in the current user's home. For other layouts, configure paths in workspace.json:

    {
      "version": 1,
      "theme": "dark",
      "repositories": {
        "reaper": "../Reaper",
        "oplague": "../OPlague",
        "ventusample": "../VentuSample",
        "pytyliki": "../Pytyliki"
      }
    }

The file is stored under %APPDATA%/Ivan-VHS/Mora/workspace.json on Windows, ~/Library/Application Support/Mora/workspace.json on macOS, or $XDG_CONFIG_HOME/mora/workspace.json on Linux. Relative paths resolve from the DuckOS repository root.

## One shared design and theme contract

MORA_DESIGN_SYSTEM.md and mora/theme.json define the canonical palette, spacing, shapes, typography, focus, reduced-motion and motion tokens. The PWA shell and its embedded web modules share the indigo/purple foundation, teal secondary accent, translucent surfaces and semantic danger color.

VentuSample and Pytyliki already consume the Mora light/dark tokens in their native theme adapters. Reaper and OPlague map their Tk palettes to the same canonical light/dark roles. The host passes MORA_THEME_MODE=dark or light before the native UI starts.

The theme API is persisted locally. A theme change immediately updates the shell and open browser modules. Existing native windows are not remotely repainted; restart them to apply the current startup theme.

## Security and product boundaries

- The local host binds only to 127.0.0.1 and applies same-origin checks to state-changing requests.
- The browser sends a fixed native app ID only; it cannot supply a shell command or executable path.
- Launch targets are a per-app allowlist in mora_host.py. Manifest entrypoint strings are metadata and are never executed.
- Browser app permissions remain explicit and user-controlled.
- The service worker skips /api responses so cached state cannot misrepresent native availability or theme changes.
- OPlague remains read-only; Mora does not elevate privileges or install drivers.
- VentuSample remains an offline renderer and DSP workstation, not a DAW or audio-device host.
- Pytyliki does not gain scheduler, affinity, voltage, clock or firmware controls.
- Reaper's language/runtime and compiler tracks remain independent of the desktop shell.

## Manifest and verification

Each native repository carries mora-app.json following schemas/mora-app.v1.schema.json. The schema describes identity, capabilities, platforms and theme integration. The host still resolves the actual executable through fixed code.

Run:

    python -m unittest discover -s tests -v
    python tools/validate_app_catalog.py
    python mora_host.py --no-browser

The CI checks Python tests, the seven-app catalog and JavaScript syntax. Native GUI builds remain platform-specific and must use the actual Qt 6 or Windows build jobs.
