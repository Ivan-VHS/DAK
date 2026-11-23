# Mora desktop — unified web and native workspace

**Canonical host:** DuckOS / Mora  
**Manifest contract:** mora-app.json, schema version 1  
**Local endpoint:** http://127.0.0.1:43860

Mora provides one desktop, one app catalogue and one shared theme for two kinds of application content: the seven browser-based DuckOS apps and the four existing native Ivan-VHS project tools. Both groups are visible on the same home screen. Their runtime boundaries remain explicit.

## One home screen, two runtime types

The default route / serves prototype/mora-home.html. The center of the desktop contains the seven browser applications and, immediately below them, the native tools. There is no second desktop or duplicate app launcher.

### Web applications

The seven app identities remain Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. They open inside the browser desktop's own application-window surface and use local browser storage/APIs where available.

| App | Current browser scope | Native/OS integration still missing |
|---|---|---|
| Cockos | Browser microphone capture, local tracks and mixdown | System-wide per-app audio sessions and native recorder service |
| Kavun | Local media library, slices and non-destructive preview/export | Image understanding and automatic location indexing |
| Ka-bon | Local expenses, attached receipts, subscriptions and family records | Receipt OCR, bank integrations and cloud sharing |
| Gloverty | User-authored local rules and manually invoked supported actions | OS scheduling, global gestures and global shortcuts |
| Po | Local tab records, external navigation and reading view | Browser-engine isolation and tracker-blocking network stack |
| Illidia | Local game catalogue, progress, achievements and user-authorized screen clips | Native executable launcher, cloud saves and platform achievement providers |
| Unify | Local device labels, browser clipboard and bounded JSON export/import | Authenticated pairing, live synchronization and phone notification service |

These browser features are prototype behavior, not evidence of fully implemented native DuckOS services. The authoritative maturity and safety specification remains [PREINSTALLED_APPLICATIONS.md](PREINSTALLED_APPLICATIONS.md), with the catalog in catalogs/preinstalled-applications.v1.json.

### Native applications

The same home screen discovers the native application manifests and asks /api/apps for current availability. A native icon is enabled only when the local repository is found and its known entry point exists. Selecting it posts its fixed ID to /api/launch/{id}; the host starts the existing executable as a separate OS-managed process.

| Project | Role | Launch target |
|---|---|---|
| Reaper Studio | MOST/Reaper language, IDE, check/run, debugger and LSP/DAP | reaper_desktop.py via the current Python interpreter |
| OPlague | Read-only device inventory and INF/ZIP/PE inspection | oplague_app.py via Python |
| VentuSample | C++20 / Qt 6 sample workstation and offline DSP | Existing built VentuSample desktop target |
| Pytyliki | C11 processor-systems workbench and Win32 GUI | Existing built pytyliki-gui.exe on Windows |

Mora does not embed native windows in iframes. The browser desktop is the common launcher and design surface; the operating system owns native window placement, focus and lifetime. A missing repository or build is shown as unavailable rather than represented by a mock window.

The /projects route is a details/catalogue page for the native group. It supplements the combined home screen; it is not a separate shell.

## Start

Place DuckOS, Reaper, OPlague, VentuSample and Pytyliki side by side:

    workspace/
    ├── DuckOS/
    ├── Reaper/
    ├── OPlague/
    ├── VentuSample/
    └── Pytyliki/

From DuckOS:

    python mora_host.py

The server listens on 127.0.0.1 only. The root URL serves the combined web/native home screen; /projects serves the native project catalogue. Python 3.10 or newer is required for the local host. Native Qt and Windows builds retain their own compiler, toolkit and platform prerequisites.

## Repository discovery

By default Mora checks sibling repositories, a workspace subdirectory, and Projects directories under the current user's home. For other local layouts, configure paths in workspace.json:

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

The file is stored in the normal per-user configuration directory: %APPDATA%/Ivan-VHS/Mora/workspace.json on Windows, ~/Library/Application Support/Mora/workspace.json on macOS, or $XDG_CONFIG_HOME/mora/workspace.json on Linux. Relative paths resolve from the DuckOS repository root.

## Shared design and theme

Both groups share Mora's dark navy background, translucent surfaces, blue primary actions, restrained red signal accents, typography, focus treatment, spacing and desktop navigation. The seven web apps retain distinct identity colors for their icons. Native application windows retain their native widgets and control layout.

Mora persists one dark or light startup preference. The web home screen reads it from /api/apps and can change it through /api/theme. Before each native launch, the host passes MORA_THEME_MODE=dark or light. Reaper, OPlague, VentuSample and Pytyliki read the value before their first theme is applied. Existing application theme controls remain available.

A theme change does not remotely repaint already-running native processes. New native windows use the current Mora theme; restart an existing native app to apply a changed startup theme.

## Security and product boundaries

- The local HTTP host binds only to 127.0.0.1 and applies same-origin checks to state-changing requests.
- Browser code can request one of four fixed native app IDs; it cannot provide a shell command or executable path.
- The launcher has a per-project allowlist and starts apps as separate native processes.
- App manifests supply descriptive metadata. Their entrypoint strings are not executed by the host.
- OPlague remains read-only; Mora does not elevate privileges or install drivers.
- VentuSample remains an offline renderer and DSP workstation, not a DAW or audio-device host.
- Pytyliki does not gain scheduler, affinity, voltage, clock or firmware controls.
- Reaper's language/runtime and compiler tracks remain independent of the desktop shell.
- The seven browser app prototypes retain their own consent, data-retention and capability boundaries; see PREINSTALLED_APPLICATIONS.md and UNIFY_TRANSFER_FORMAT_V1.md.

## Application manifest schema

Each native repository carries mora-app.json using schemas/mora-app.v1.schema.json. The schema describes app identity, category, capabilities, platform declaration, expected entry point and Mora theme hand-off. It is metadata, not executable configuration.

For safety, the actual native launch command is separately fixed in mora_host.py. To add a project, update the schema-compatible manifest, the fixed launcher allowlist, the desktop catalogue and the associated tests together.

## Verification

    python -m unittest discover -s tests -v
    python tools/validate_app_catalog.py
    python mora_host.py --no-browser

CI validates the seven-app product catalog and the local host. Native GUI verification remains platform-specific and must use the actual Qt 6 or Windows build jobs.
