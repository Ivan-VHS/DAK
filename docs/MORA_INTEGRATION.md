# Mora native desktop

Mora is DuckOS's native user-space desktop application and application launcher. It is implemented with Python's Tk toolkit and is started with `duckos mora gui` or `duckos-mora`.

## Runtime boundary

Mora is a regular host desktop process. It uses native Tk widgets directly and does not contain or load HTML, CSS, browser JavaScript, a WebView, a browser engine, a web manifest or a service worker.

This does not make Mora the DuckOS compositor. The production compositor, window manager, virtual workspaces, system notification service, process manager and kernel-enforced capability broker remain planned system components. The Mora process does not claim to boot DuckOS or replace the host desktop.

## Included native surfaces

- Application launcher with search and category filters, populated from the versioned Mora registry.
- One black, white and yellow Duck palette, with shared JSON design tokens.
- Local shell preferences for focus mode, reduced motion, density and a user-selected preference profile.
- A bounded rule-based intent preview with explicit approval. Only listed local actions are supported; arbitrary command execution is not available.
- Sentinel preference switches. These are local profile values, not device or process permissions.
- Restore export and import of normalized Mora preferences only. It is not an OS updater or partition rollback system.
- Proof SHA-256 for a selected regular local file, with a 512 MiB file-size limit. A digest is not proof of authorship or signature validity.
- Bridge / EXEdotEXE read-only PE and ELF inspection through DuckOS's compatibility parser. Selecting a file does not execute it, load a DLL or install a runtime.
- Mora Commons catalogue search from packaged JSON data.
- Duck Desktop and Reaper Studio entry points to their existing native user-space tools.

## Data and safety

Settings are written to the per-user DuckOS/Mora configuration directory using an atomic JSON replacement. Unknown fields and capability names are discarded during normalization. The settings backup contains only the known preference schema.

The Sentinel panel describes preferences only. The shell cannot enforce device access or process capabilities. Do not treat a checkbox as a kernel permission.

The Bridge panel only inspects file structure. It never launches the selected target. The Proof panel calculates SHA-256 from local bytes and does not establish publisher identity, signing trust or content provenance.

## Visual system

The single Duck palette is black, white and yellow. Yellow is used for primary actions, active navigation and keyboard focus. Reduced-motion and density preferences are persisted, but they do not alter the host window manager or global desktop.

## Build and run

Install the package in the current environment and start the native shell:

```sh
python -m pip install .
duckos mora gui
```

Python must include Tk support. On minimal Linux installations this may require the distribution's `python3-tk` package. No Node.js, browser or web runtime is required.

## Maturity vocabulary

- **Implemented:** the native user-space behavior is present and covered by tests.
- **Partial:** a bounded local panel exists; the complete service or persistent app data layer is absent.
- **Specified:** a design or catalogue entry exists, but no native behavior is claimed.
- **Planned:** implementation is not present.

A native panel does not prove that the corresponding kernel service, driver or bootable OS component exists.
