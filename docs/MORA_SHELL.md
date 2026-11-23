# Mora OS shell — Reaper policy and host integration

## Purpose

Mora is DuckOS's desktop shell. The browser/PWA surface now connects to an authenticated loopback Native Host broker, while a separate native C executable provides an initial X11 compositor and window manager. Reaper policy is available through a bounded live interpreter bridge when Reaper is installed.

The shell has three distinct parts:

1. **Mora presentation** — HTML, CSS and JavaScript render the desktop, application windows, virtual workspaces, command palette and the 20-direction system matrix.
2. **Reaper OS policy** — .rpr modules define window geometry and lifecycle, workspace/session validation, capability-gated application launch, allowlisted commands and bounded notification history.
3. **Host integration** — a POSIX broker manages registered processes, per-UID sessions, controlled diagnostics, Linux driver-module inspection and allowlisted Reaper policy evaluation. Mora connects to it over authenticated loopback HTTP; local CLI clients can use its Unix socket.

This separation is intentional. Browser JavaScript manages the visible workspace; the C compositor owns X11 top-level windows; Reaper owns deterministic policy; the Python host service mediates privileged userspace operations. Kernel enforcement and device-specific DuckOS drivers remain future work.

## Desktop features

### Virtual workspaces

Mora exposes four local workspaces:

- home — main desktop and everyday applications;
- studio — work and creative tools;
- play — games and Illidia;
- system — system settings and maintenance tools.

The selected workspace is kept in browser-local storage. Windows are associated with a workspace and hidden when the user switches to another one. This is a shell-level workspace model; it does not create kernel sessions or isolate processes.

### Window controls

Application windows support focus ordering, minimize, maximize/restore, close and pointer dragging. Reaper's duckos/ui/window_manager.rpr describes the corresponding policy records and checks:

- valid window identity, geometry, display bounds and state;
- permitted state transitions;
- visibility and focus within the active workspace;
- monotonic z-order assignment;
- an explicit maximum-window count.

Mora still renders its app content in a browser, but top-level desktop windows can now be managed by the separate `duckos-compositor` X11 binary. The C window manager provides basic X11 frames, focus, title dragging, close/minimize shortcuts and compositing through XRender. It is not a Wayland compositor, DRM/KMS renderer, kernel window manager or a complete multi-monitor desktop.

### Command palette

Press **Ctrl+K** to open the command palette. It can find applications by ID, display name or subtitle and accepts a small allowlist of shell commands:

~~~text
/help
/status
/apps
/open illidia
/open workspace
/close
/workspace home
/workspace studio
/workspace play
/workspace system
/theme amber
/theme dark
/theme light
/focus on
/focus off
~~~

Commands are tokenized into arguments and checked against known application IDs, workspace IDs and theme names. The UI does not evaluate JavaScript, launch arbitrary shell commands, or pass user text to a host command interpreter.

The Reaper policy in duckos/ui/desktop.rpr contains the command allowlist and rejects unknown commands, unexpected extra arguments and untrusted application descriptors.

The browser shell still validates its own command palette in JavaScript. The Native Host also exposes a fixed set of Reaper policy calls by loading `reaper.runtime.Interpreter` and evaluating the repository's `.rpr` modules under strict step, heap and resource limits. That live bridge is available only when Reaper is installed in the broker's Python environment; otherwise it reports `not-installed`.

### Twenty-direction engineering matrix

The workspace/settings panel includes the 20 development directions from the supplied OS shell prototype. Search and category filters are retained, as is a detail inspector.

The matrix shows maturity categories rather than synthetic percentages:

- partial — a working subset is present; remaining OS-level work is stated;
- specified — a policy or design contract exists, but connected behavior is not yet implemented;
- planned — a future native capability is not represented as implemented.

Selecting a matrix entry shows its concrete implementation boundary. The matrix is an engineering index, not a task scheduler and not evidence that all 20 directions are complete.

### Notifications and accessibility

The Reaper notification contract uses a bounded history, explicit severity, increasing monotonic timestamps and a read flag. The existing Mora presentation continues to use its toast/status surface. A persistent notification centre and native notification daemon are not claimed by this change.

The desktop keeps its existing theme, local preference, keyboard navigation and reduced-motion behavior. A native accessibility tree, input-method framework and compositor-level display migration remain future work.

## Reaper modules

| Module | Responsibility | Current maturity |
|---|---|---|
| duckos/ui/window_manager.rpr | Window validation, geometry, state transitions, visibility and focus | Reaper contract |
| duckos/ui/desktop.rpr | Palette/workspace/session policy, app capability requirements and command allowlist | Reaper contract |
| duckos/ui/notifications.rpr | Valid notification records, bounded history and unread count | Reaper contract |
| duckos/ui/theme.rpr | DuckOS palette and reduced-motion policy | Reaper contract |
| duckos/ui/motion.rpr | Frame-time budget classification | Reaper contract |

contract_tests.rpr covers these modules on both the Reaper tree-walk and VM engines in the dedicated GitHub Actions workflow. Passing those tests verifies the policy functions on the reference Reaper runtime; it does not prove native compositor, display-driver or kernel execution.

## Host commands

Install the Python build tools from the repository root:

~~~sh
python -m pip install -e .
~~~

Inspect the current host without changing it:

~~~sh
duckos shell status
~~~

List the versioned Mora application catalogue:

~~~sh
duckos shell apps
~~~

Check that the shell source, Reaper policy files and catalogue are present:

~~~sh
duckos shell verify
~~~

The host report uses platform information and available memory counters exposed by the host. Display backend detection is based on the current process environment. Missing providers remain unavailable; the report does not invent Wi-Fi connectivity, battery percentage, NPU load, temperature, PCIe devices or frame rate.

All three commands are read-only. They do not install packages, change power settings, enumerate hardware buses, start applications or run Reaper contracts.

## Implementation boundary

The Mora UI and native X11 backend are a working desktop layer, but they are not a self-hosted DuckOS kernel or a standalone OS image by themselves. The repository now includes a Debian Live build recipe that packages the userspace and boots with the Debian Linux kernel.

Implemented in this repository:

- browser/PWA desktop presentation in Mora;
- virtual workspace switching and local persistence;
- window focus, minimize, maximize/restore and close controls;
- keyboard command palette and allowlisted application/workspace/theme/focus commands;
- searchable 20-direction systems matrix with maturity and boundary descriptions;
- Reaper contracts for window state, workspace/session policy, command authorization and notification records;
- native C/X11 compositor and window manager with Xvfb CI self-test;
- UID-aware POSIX process/session supervisor and capability-checked Unix-socket/loopback HTTP host broker;
- allowlisted diagnostic terminal, Linux driver-module inspection/loader and live Reaper policy bridge;
- Mora Native Host panel and browser client tests;
- Debian Live image build recipe and X11 session entry;
- Reaper contract tests executed in CI on the tree-walk and VM engines.

Not implemented by this change:

- native Wayland compositor, DRM/KMS and accelerated GPU rendering; the implemented compositor is X11/XRender only;
- kernel scheduler/session manager, namespaces/cgroups, process isolation or kernel-enforced capabilities;
- generic interactive shell, arbitrary command execution, power management or native lock-screen service;
- DuckOS-owned graphics/audio/network/USB/NVMe driver sources, signed driver packages and isolation; module inventory and load operations reuse the Linux kernel's drivers;
- UEFI entry point, freestanding DuckOS kernel and a bootable image using a DuckOS-owned kernel; the Live recipe is based on Debian Linux.

The repository currently defines **Reaper** as its system policy/source language. The Mora presentation is JavaScript/HTML/CSS, the native X11 desktop binary is C, and the host broker is Python. Reaper is executed through its reference interpreter when installed; its C17 compiler subset is not a freestanding OS compiler. The userspace broker is not a kernel reference monitor.

## Verification

Run the Python and catalogue tests:

~~~sh
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
xvfb-run -a ./build/duckos-compositor --check
xvfb-run -a ./build/duckos-compositor --self-test
~~~

Run the browser-shell tests:

~~~sh
npm test
node --check mora/app.js
node --check mora/shell.js
~~~

Run the Reaper contracts through the pinned Reaper runtime as defined in .github/workflows/reaper-contracts.yml. That workflow checks every .rpr source file and executes contract_tests.rpr with both supported reference engines.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve the existing authorship and copyright notices of contributors and third-party components.
