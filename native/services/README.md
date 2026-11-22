# DuckOS core services

The seven requested components are implemented as a small Python 3.10+ user-space
service package. It uses the Python standard library only.

Run commands from the repository root:

    PYTHONPATH=native/services python -m duckos_services status
    PYTHONPATH=native/services python -m duckos_services audio ports outputs
    PYTHONPATH=native/services python -m duckos_services theme audit --name high-contrast
    PYTHONPATH=native/services python -m duckos_services snapshot save --label "Before editing"

Run tests:

    make -C native services-test

The default state directory is ~/.local/state/duckos; use the global
--state-dir option to select another directory.

## Component boundaries

- **Cockos** talks to PipeWire through pw-link. It lists ports and creates or
  removes graph links after validating both endpoints. Install PipeWire's command
  line tools to use audio routing. Effects, a DSP host, and a DuckOS kernel audio
  driver are not part of this first adapter.
- **Kavun** calculates bounded logical-pixel rectangles for main/stack, columns,
  grid, and floating layouts. A compositor adapter must still apply those
  rectangles to Wayland surfaces.
- **Ka-bon** normalizes keyboard chords, resolves active-context bindings, and
  rejects actions outside a fixed allow-list. An evdev/libinput seat adapter is
  still required for system-wide input capture.
- **Gloverty** provides semantic dark, light, and high-contrast palettes plus a
  WCAG-style contrast audit. The browser preview still has its own CSS theme.
- **Po** searches registered commands. It never interprets text as a shell
  command, and commands marked destructive require an explicit confirmation.
- **Illidia** atomically stores versioned, SHA-256 checked session snapshots.
  Only an allow-list of UI/session settings is accepted; user documents and
  application data are not copied.
- **Unify** owns the user-space settings file, profile changes, event bus and
  service command registry. The event bus is currently in-process, not a
  cross-process IPC daemon.

These services are not linked into the freestanding kernel. They are an
executable host-side foundation that can later be attached to the native
session manager and compositor through stable adapters.
