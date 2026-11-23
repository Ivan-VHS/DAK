# Mora native desktop

Mora is DuckOS's native user-space desktop application and application launcher. Its primary GUI is **PySide6 / Qt 6 Widgets** and it starts with `duckos mora gui` or `duckos-mora`.

## Runtime boundary

Mora is a normal host desktop process. It uses Qt Widgets directly and does not create or load HTML, CSS browser documents, JavaScript, a WebView, a browser engine, a web manifest or a service worker. Tkinter has been removed from the Mora runtime. Optional GPU and terminal utilities are separate processes, not embedded widget families.

This does not make Mora the DuckOS compositor. The production compositor, window manager, virtual workspaces, system notification service, process manager and kernel-enforced capability broker remain separate system components. Mora does not claim to boot DuckOS or replace the host desktop.



## Native interaction and materials

- App panels are independent, non-modal top-level Qt windows. The host window manager owns dragging, resize, minimize, maximize, activation and z-order; Mora re-activates an existing panel instead of opening duplicates. Window content is bounded to the active screen, and a failed panel build is reported inside its own window.
- All range controls should use the shared `MoraSlider` from `duckos.mora.controls`. It combines a draggable Qt slider with an exact numeric field, bounded values, wheel movement, coarse arrow steps and Shift-modified fine steps. Numeric output reserves a fixed width to avoid layout jitter.
- The shared surface material uses a high-opacity translucent fill and a thin border. An opaque surface is declared first as the rendering fallback. Cross-platform backdrop blur is not claimed: Qt Widgets does not provide a consistent native blur-behind-window API across supported compositors, so the UI remains legible without it.
- Interface scale is a persisted user preference from 80% through 140%; it previews live and is normalized when loaded. Intent input accepts the supported Russian and Ukrainian phrases. Enter prepares a preview; applying it still requires explicit approval.

## Included native surfaces

- PySide6 launcher with search, category filtering, responsive app cards and dedicated app dialogs.
- One black, white and yellow Duck palette, with shared JSON design tokens.
- Local shell preferences for focus mode, reduced motion, density and a user-selected profile.
- Bounded intent preview with explicit approval. Only allowlisted local actions are supported.
- Sentinel preference switches. These are local profile values, not device or process permissions.
- Restore export/import of normalized Mora preferences only, not an OS updater or partition rollback system.
- Proof SHA-256 for a selected regular local file, with a 512 MiB size limit.
- Bridge / EXEdotEXE read-only PE and ELF inspection; selected targets are never executed.
- Mora Commons search from packaged JSON data.
- Duck Desktop and Reaper Studio process entry points.

## Optional toolkit adapters

The primary desktop dependency is installed separately:

```sh
python -m pip install '.[native-ui]'
duckos mora gui
```

Optional capabilities are isolated behind extras and entry points:

| Extra | Command | Function |
|---|---|---|
| `terminal-ui` | `duckos mora tui` | Textual terminal dashboard with searchable app registry |
| `gpu-tools` | `duckos mora gpu` | Separate Dear PyGui GPU-accelerated read-only diagnostic window |
| `plots` | `duckos mora plot` | PyQtGraph numeric CSV viewer in a native Qt window |
| `native-ui` | `duckos mora scene` | Qt Quick / QML native declarative scene preview |
| `windows-native` | `duckos mora bridges` | Optional PyWin32 functions on Windows |
| `macos-native` | `duckos mora bridges` | PyObjC availability detection on macOS; no app-control API is claimed |
| `native-ffi` | `duckos mora bridges` | CFFI availability for explicit native plugin contracts |

Install only the profiles that are needed:

```sh
python -m pip install '.[native-ui,terminal-ui,plots]'
python -m pip install '.[gpu-tools]'
python -m pip install '.[windows-native]'  # Windows
python -m pip install '.[macos-native]'    # macOS
```

The 66-item toolkit evaluation is maintained in [GUI framework architecture](GUI_FRAMEWORK_ARCHITECTURE.md) and [gui-toolkits.json](../duckos/mora/data/gui-toolkits.json). It is a review matrix, not a requirement to install all 66 frameworks. Tk-based packages are retired, web-first/HTML/WebView stacks are excluded, game engines remain application renderers, and optional adapters run in separate processes or behind explicit extras.

## Data and safety

Preferences are written to the per-user DuckOS/Mora configuration directory using an atomic JSON replacement. Unknown fields and capability names are discarded during normalization. Backups contain only the known preference schema.

The Sentinel panel does not enforce device access or process capabilities. The Bridge panel inspects file structure and does not launch targets. Proof calculates SHA-256 and does not establish publisher identity, signing trust or content provenance. Native FFI is restricted to reviewed function signatures and validated handles.

## Build and validation

Python 3.10+ is required. PySide6 wheels are installed with the `native-ui` extra. On CI, the Qt desktop is smoke-tested with the offscreen Qt platform plugin.

```sh
python -m pip install -e '.[native-ui]'
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -p 'test_mora_qt.py' -v
python -m unittest discover -s tests -v
```

## Maturity

- **Implemented:** native Mora Qt shell, launcher, settings and documented local panels.
- **Partial:** bounded diagnostic and platform-adapter entry points.
- **Specified:** product concepts and optional toolkit adapters that have not been installed or implemented as app services.
- **Planned:** compositor, boot shell, native window manager, process manager, notifications, capability broker and per-application native services.

A native panel does not prove that the corresponding kernel service, driver, bootloader or bootable OS image exists.
