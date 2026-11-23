# DuckOS — Mora desktop workspace

DuckOS is the home of **Mora**, a local desktop shell that brings the Ivan‑VHS application projects into one consistent workspace.

Mora provides the desktop surface, an application catalogue, a shared light/dark theme and a small local launcher. It does not pretend that native programs are embedded web applications: Reaper Studio, OPlague, VentuSample and Pytyliki keep their own executable processes and native windows.

## Included

- index.html — responsive Mora desktop interface.
- mora_host.py — loopback-only host for the app catalogue, settings and allowlisted process launch.
- mora-app.json — DuckOS/Mora application manifest.
- schemas/mora-app.v1.schema.json — shared manifest contract used by the connected repositories.
- docs/MORA_DESKTOP.md — workspace, theme, configuration and security boundaries.

## Start Mora

Place the repositories beside one another, then run from this directory:

    python mora_host.py

The desktop opens at http://127.0.0.1:43860. Python 3.10 or newer is sufficient for the local host; the individual applications keep their own build requirements.

When the repositories are not siblings of DuckOS, set their paths in your local Mora workspace configuration. Mora never executes a command copied from a web page or from an application manifest.

## Connected applications

| Project | Purpose | Native launch |
|---|---|---|
| [Reaper](https://github.com/Ivan-VHS/Reaper) | Programming language and Studio IDE | Python Studio entry point |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | Read-only device and driver workbench | Python desktop entry point |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | Procedural sample workstation | Qt 6 desktop build |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | Processor systems workstation | Windows GUI build |

Unavailable repositories or unbuilt native targets are shown as unavailable instead of being simulated. Apps open in separate OS-managed windows and receive MORA_THEME_MODE=dark or light when launched from Mora.

## Test

    python -m unittest discover -s tests -v
