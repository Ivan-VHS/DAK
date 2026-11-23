# Mora desktop — unified web and native workspace

**Canonical desktop:** mora/index.html  
**Application controller:** mora/app.js  
**Shared design tokens:** mora/theme.json  
**Native launcher:** mora_host.py  
**Local endpoint:** http://127.0.0.1:43860/mora/

Mora is one desktop, not separate web and native launchers. Its 17-entry catalogue contains seven browser workspaces, six Mora system tools and four native project applications. Their different runtime types remain explicit.

## 1. Canonical shell and window model

The canonical PWA shell uses mora/index.html, mora/styles.css, mora/app.js and mora/core.js. It provides the background, status bar, clock, application areas, dock, draggable windows, local preferences and shared dark/light appearance.

The seven first-party web workspaces are opened in Mora's native window surface using the maintained local browser module runtime at prototype/mora-home.html. The shell sends the selected app ID in a fixed app query value, enables only the browser APIs needed by that module and synchronizes the Mora light/dark theme with same-origin messages. Each module retains its browser-local storage and existing prototype behavior.

The six Mora system tools remain implemented by the current app.js and core.js panels. Their maturity boundaries are recorded in mora/system-policy.json and the product README; a control surface is not evidence of a kernel, driver or OS service.

Native projects open a Mora details window, not an iframe. The details window displays availability and a launch control. The local host starts the fixed native entry point in a separate process; the operating system owns the actual native window, focus, DPI and lifetime.

## 2. Application catalogue

| Runtime type | Applications | Count |
|---|---|---:|
| First-party browser workspaces | Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia, Unify | 7 |
| Mora system tools | Mora AI, Sentinel, Restore, Bridge, Control, Proof | 6 |
| External native projects | Reaper Studio, OPlague, VentuSample, Pytyliki | 4 |
| **Total** | **One shared Mora catalogue** | **17** |

The machine-readable registry is mora/apps.json. built_in_apps lists the seven web apps and six system panels; native_apps separately declares the four external projects and their descriptive platform/entry-point information.

## 3. Web workspaces and their limits

| App | Browser content | Boundary |
|---|---|---|
| Cockos | Browser microphone capture, local tracks and mixdown in the maintained module runtime | Per-application system audio sessions require a native audio service |
| Kavun | Local media library, event slices, preview/retouch and export | Image understanding and automatic location indexing are not connected |
| Ka-bon | Local expenses, receipt attachments, subscription tracking and family records | OCR, bank connections and cloud family sharing are not connected |
| Gloverty | User-authored rules and manually invoked supported local actions | OS scheduling, global gestures and global shortcuts are not connected |
| Po | Local tab records, HTTP(S) navigation and reading view | It is not a new browser engine or network-level tracker blocker |
| Illidia | Local game library, progress, achievements and user-authorized screen clips | Native executable launcher and cloud saves are not connected |
| Unify | Local device labels, browser clipboard and bounded manual JSON transfer | Authenticated pairing, live synchronization and phone notifications are not connected |

The browser modules are available in browser-only mode. Microphone, camera, display-capture and clipboard operations depend on browser permissions and support. The default Mora shell does not pretend that these modules are complete native DuckOS applications.

The product roles and prototype maturity are documented in PREINSTALLED_APPLICATIONS.md and catalogs/preinstalled-applications.v1.json.

## 4. Native applications and launch behavior

The home screen checks the local /api/apps endpoint and reads each project's readiness state. A native launch action is enabled only if the repository directory and its known entry point or built binary exist.

| Project | Fixed entry point selected by the host | Platform/build requirement |
|---|---|---|
| Reaper Studio | reaper_desktop.py using the current Python interpreter | Python/Tk desktop environment |
| OPlague | oplague_app.py using the current Python interpreter | Python/Tk desktop environment |
| VentuSample | Existing CMake desktop executable | Built Qt 6 Widgets target |
| Pytyliki | pytyliki-gui.exe | Windows GUI target |

The browser submits only a known application ID to /api/launch/{id}. The host never accepts a command, argument list, path or shell fragment from the browser. The manifest is metadata and is not used as an executable configuration.

The application repository folder may be discovered before its Mora manifest PR merges. Actual launch still depends on the fixed per-app entry point and a present build where applicable.

Mora does not embed native windows in an iframe. The browser window only presents information and invokes the allowlisted launch endpoint; native programs are independent processes.

## 5. Start and configure

Place DuckOS and the project repositories side by side:

    workspace/
    ├── DuckOS/
    ├── Reaper/
    ├── OPlague/
    ├── VentuSample/
    └── Pytyliki/

From DuckOS:

    python mora_host.py

The local host binds to 127.0.0.1 and opens /mora/. It serves the PWA assets, the seven-app web module runtime and the API for theme, application discovery and native launch.

For a browser-only preview:

    python -m http.server 8000

Open /mora/ on localhost. This preview has no native process bridge, so native launch controls remain unavailable instead of pretending a process started.

If projects are stored in other directories, configure repositories in the local workspace.json file. Relative paths resolve from the DuckOS repository root. The configuration is stored in the standard per-user configuration directory on Windows, macOS or Linux.

## 6. Visual and theme integration

MORA_DESIGN_SYSTEM.md and mora/theme.json define the canonical surfaces, palette, typography, spacing, radii, interaction targets, motion and reduced-motion values. The seven embedded web modules receive the current theme from the parent shell. The native host passes MORA_THEME_MODE=dark|light to new Reaper, OPlague, VentuSample and Pytyliki processes.

Already running native processes are not remotely repainted. Restart the process to apply a newly selected startup theme. Native adapters remain implemented in their own repositories and do not share a browser CSS runtime.

## 7. Security boundaries

- Local host binds only to 127.0.0.1.
- State-changing requests are subject to a same-origin check.
- /api/launch/ accepts only four registered IDs.
- Launch commands are fixed in mora_host.py and never assembled from browser or manifest strings.
- App manifests describe identity, capability, platform and expected entry point; they do not authorize execution.
- Native processes are not sandboxed by this shell. OS-level containment and privilege controls require a native process/capability broker.
- OPlague remains read-only; VentuSample remains offline; Pytyliki gains no hardware-control privileges.

## 8. Verification

    npm test
    python -m unittest discover -s tests -v
    python tools/validate_app_catalog.py
    python mora_host.py --no-browser

The CI test suite checks the browser shell, Mora core contracts, application registry, local host routes and the safe fixed-target launcher. Native app readiness/build remains platform-specific and is checked in the respective project repositories.
