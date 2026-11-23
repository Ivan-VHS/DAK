# DuckOS · Mora Desktop

DuckOS now contains **Mora**, the unified desktop shell for the Ivan-VHS application family.

## Run Mora

Open [mora/index.html](mora/index.html) in a browser. For installable offline-shell behavior, serve the repository through HTTPS or localhost:

```sh
python -m http.server 8000
``

Then open `http://localhost:8000/mora/`.

## Connected native workspaces

| Project | Role | Desktop technology |
| --- | --- | --- |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | Processor diagnostics and metrics | Win32 |
| [Reaper](https://github.com/Ivan-VHS/Reaper) | Programming language and Studio IDE | Tk |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | Device and driver inspection | Tk |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | Procedural audio workstation | Qt |
| DuckOS | OS and desktop shell | Mora web shell prototype |

Mora shows the real desktop captures published by the native projects and links to their repositories/releases. It does **not** claim to execute native binaries in a browser. A permissioned OS launcher/IPC bridge is a separate integration layer and is not part of this web shell.

## Existing OS specification

Mora is the updated shared workspace, not a replacement for the operating-system specifications. Keep the earlier material alongside it:

- [Documentation index](docs/README.md)
- [Preinstalled application specification](docs/PREINSTALLED_APPLICATIONS.md)
- [Unified documentation standard](docs/UNIFIED_DOCUMENTATION_STANDARD.md)
- [Original seven-app home-screen prototype](prototype/mora-home.html)

The original prototype and product specifications remain useful references for the seven built-in applications. The new `mora/` directory is the integrated DuckOS shell that brings those modules and the five native project workspaces into one desktop catalogue.

## Shared design language

[MORA_DESIGN_SYSTEM.md](MORA_DESIGN_SYSTEM.md) defines the canonical palette, shapes, spacing, typography, motion and accessibility contract. Each native repository keeps its own specialist layout and adopts the shared semantic tokens through its native toolkit.

Maintained by Ivan-VHS.
