# DuckOS Core Services

## Why these services exist

Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify form the first shared
user-space service layer. Each module has a narrow contract, a testable API and
a clear boundary to the unfinished native kernel and Wayland session.

    Desktop shell / future Wayland session
                     |
              Unify settings + events
           /     /     |     \       \
       Cockos  Kavun  Ka-bon  Gloverty  Po
                                  |
                               Illidia

The Python package lives in native/services/duckos_services. Its only runtime
dependency is the Python standard library. PipeWire is optional and is detected
at runtime.

## Implemented contracts

| Component | Implemented now | Remaining native integration |
|---|---|---|
| Cockos | PipeWire output/input discovery, validated port connect/disconnect | DSP/effects graph, policy UI, persistent session restore, kernel audio drivers |
| Kavun | main-stack, columns, grid and floating geometry planner | Wayland surface arrangement, monitor hotplug, focus policy |
| Ka-bon | chord normalization, context-first routing, action allow-list | evdev/libinput seat, key repeat, touchpad/gamepad gesture adapters |
| Gloverty | dark/light/high-contrast tokens and contrast audit | one shared theme provider for every native client |
| Po | command registry, ranked search, confirmation gate | live desktop index, app lifecycle API, undoable privileged operations |
| Illidia | atomic, versioned session snapshots with checksums and retention | crash/session hooks and application-owned restore providers |
| Unify | persisted profiles, in-process events, central command registry | authenticated cross-process IPC and service supervision |

### Cockos

The PipeWire adapter uses pw-link to enumerate output/input ports and manage
links. A link is a graph connection, not an effects processor. Actual latency
depends on the PipeWire graph, device, driver, period size and workload; the
service does not promise literal zero latency or bit-perfect behavior through
arbitrary mixers and DSP.

### Kavun and Ka-bon

Kavun returns logical-pixel rectangles and does not move surfaces by itself.
Ka-bon resolves normalized chords into a small set of registered actions; it
does not capture global input until a trusted seat adapter is connected. Both
contracts are intentionally independent of a particular compositor.

### Gloverty and Po

Gloverty checks foreground/background pairs against explicit contrast
thresholds and returns machine-readable results. Po only executes handlers
registered by trusted code. There is no shell fallback, dynamic evaluation or
implicit privilege escalation.

### Illidia and Unify

Illidia saves only session metadata from an explicit allow-list. Snapshots are
written via a temporary file, fsync and atomic rename; a SHA-256 checksum is
verified before restore. This does not create filesystem snapshots or protect
unsaved application documents.

Unify persists user preferences and profile changes and publishes in-process
events. Its current event bus is not a multi-process IPC transport; the future
native session should expose the same event envelope over an authenticated,
versioned local socket.

## Run and test

From the repository root:

    PYTHONPATH=native/services python -m duckos_services status
    PYTHONPATH=native/services python -m duckos_services audio ports outputs
    PYTHONPATH=native/services python -m duckos_services theme audit --name high-contrast
    PYTHONPATH=native/services python -m duckos_services layout --width 1920 --height 1080 --windows '[{"id":"editor","role":"primary"},{"id":"terminal"}]'
    make -C native services-test

By default, state is stored under ~/.local/state/duckos. The CLI accepts a
global --state-dir override for test runs and portable development setups.

## Release gates

Before calling this a complete native desktop integration, the project still
needs a working compositor and seat, authenticated IPC, service lifecycle
management, integration tests on real PipeWire devices, audio latency
measurements, multi-monitor tests, accessibility testing and a booted hardware
matrix. The current branch provides the service contracts and user-space
prototype, not those missing kernel or device layers.
