# Mora desktop — unified workspace

**Canonical host:** DuckOS / Mora  
**Manifest contract:** mora-app.json, schema version 1  
**Local endpoint:** http://127.0.0.1:43860

Mora is the shared desktop entry point for the DuckOS seven-app prototype and the connected Ivan-VHS native development tools. It provides a common visual language, local home screen, project catalogue, startup theme and allowlisted application launcher. It does not conflate a browser prototype with a native operating-system service.

## Two connected layers

### Seven-app Mora home screen

The default desktop opens prototype/mora-home.html. Its seven app identities remain Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. The prototype uses local browser storage and browser APIs where available. Its capabilities are partial and platform-dependent; the native applications and missing OS services are not claimed as implemented.

| App | Prototype scope | Native gap |
|---|---|---|
| Cockos | Browser microphone capture, local tracks and mixdown | System-wide per-app audio sessions and native recorder service |
| Kavun | Local media library, slices and non-destructive preview/export | Image understanding and automatic location indexing |
| Ka-bon | Local expenses, attached receipts, subscriptions and family records | Receipt OCR, bank integrations and cloud sharing |
| Gloverty | User-authored local rules and manually invoked supported actions | OS scheduling, global gestures and global shortcuts |
| Po | Local tab records, external navigation and reading view | Browser-engine isolation and tracker-blocking network stack |
| Illidia | Local game catalogue, progress, achievements and user-authorized screen clips | Native executable launcher, cloud saves and platform achievement providers |
| Unify | Local device labels, browser clipboard and bounded JSON export/import | Authenticated pairing, live synchronization and phone notification service |

The authoritative maturity and safety specification remains [PREINSTALLED_APPLICATIONS.md](PREINSTALLED_APPLICATIONS.md), with the catalog in catalogs/preinstalled-applications.v1.json. The home screen does not replace or rewrite that catalog.

### Connected native project workspace

The top-bar link **Проекты Ivan-VHS** opens /projects. These entries are independent repositories, not additional members of the seven-app product catalog.

| Project | Repository role | Launch target |
|---|---|---|
| Reaper Studio | MOST/Reaper language tools, IDE, check/run, debugger and LSP/DAP | reaper_desktop.py via the current Python interpreter |
| OPlague | Local read-only device inventory and INF/ZIP/PE inspection | oplague_app.py via Python |
| VentuSample | C++20 / Qt 6 procedural sample workstation and offline DSP | Existing built VentuSample desktop target |
| Pytyliki | C11 processor-systems workbench and Win32 GUI | Existing built pytyliki-gui.exe on Windows |

Mora shows an external project as unavailable when its repository or executable target is missing. It does not create fake windows for unbuilt binaries.

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

The server listens on 127.0.0.1 only. The root URL serves the seven-app home screen; /projects serves the external project catalogue. The /api/launch endpoint accepts only the four fixed project IDs and known entry points.

Python 3.10 or newer is needed for the local host. Native Qt and Windows builds retain their own compiler, toolkit and platform prerequisites.

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

## Shared visual and theme contract

The two workspace surfaces use Mora's dark navy, glass surfaces, blue primary actions and restrained red signal accents. The seven app icons may keep distinct identity colors; this does not change shared layout, typography, focus, spacing or window behavior.

Mora persists a dark or light startup preference. It passes MORA_THEME_MODE=dark or light to new native processes. Reaper, OPlague, VentuSample and Pytyliki read the value before their first theme is applied. Existing application theme controls remain available. The seven-app home screen reads the same preference on page load and when it regains focus.

A theme change does not remotely repaint already-running native processes. Restart an application to apply the current Mora theme to its startup surface.

## Security and product boundaries

- The local HTTP host binds only to 127.0.0.1 and applies same-origin checks to state-changing requests.
- Browser code can request a fixed app ID; it cannot provide a shell command or executable path.
- The launcher has a per-project allowlist and starts apps as separate native processes.
- App manifests supply descriptive metadata. Their entrypoint strings are not executed by the host.
- OPlague remains read-only; Mora does not elevate privileges or install drivers.
- VentuSample remains an offline renderer and DSP workstation, not a DAW or audio-device host.
- Pytyliki does not gain scheduler, affinity, voltage, clock or firmware controls.
- Reaper's language/runtime and compiler tracks remain independent of the desktop shell.
- The seven browser app prototypes retain their own consent, data-retention and capability boundaries; see PREINSTALLED_APPLICATIONS.md and UNIFY_TRANSFER_FORMAT_V1.md.

## Application manifest schema

Each external repository carries mora-app.json using schemas/mora-app.v1.schema.json. The schema describes the app identity, category, capabilities, platform declaration, expected entry point and Mora theme hand-off. It is metadata, not executable configuration.

For safety, the actual native launch command is separately fixed in mora_host.py. To add a new repository, update the schema-compatible manifest, the fixed launcher allowlist, the app catalogue and the associated tests together.

## Verification

    python -m unittest discover -s tests -v
    python tools/validate_app_catalog.py
    python mora_host.py --no-browser

The existing CI validates the seven-app catalog and runs unit tests under Python 3.10, 3.11 and 3.12. Native GUI verification remains platform-specific and must use the actual Qt 6 or Windows build jobs.
