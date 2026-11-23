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

## Shared design language

[MORA_DESIGN_SYSTEM.md](MORA_DESIGN_SYSTEM.md) defines the canonical palette, shapes, spacing, typography, motion and accessibility contract. Each native repository keeps its own specialist layout and adopts the shared semantic tokens through its native toolkit.

Maintained by Ivan-VHS.
