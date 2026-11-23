# Mora OS shell — Reaper policy and host integration

## Purpose

Mora is DuckOS's desktop shell. This implementation connects the existing browser/PWA presentation to explicit Reaper policy contracts and a read-only host inspection layer.

The shell has three distinct parts:

1. **Mora presentation** — HTML, CSS and JavaScript render the desktop, application windows, virtual workspaces, command palette and the 20-direction system matrix.
2. **Reaper OS policy** — .rpr modules define window geometry and lifecycle, workspace/session validation, capability-gated application launch, allowlisted commands and bounded notification history.
3. **Host integration** — Python CLI commands report actual host information and check that the shell's source files and application catalogue are present.

This separation is intentional. Browser JavaScript manages the visible workspace; Reaper owns deterministic policy; privileged or device-specific operations belong to a future native OS service.

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

The browser shell is the current renderer and window host. These contracts do not constitute a native compositor or a kernel window manager.

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

The browser shell currently applies its allowlist in JavaScript. The matching Reaper policy is an independently executable contract checked by the Reaper CI workflow; Mora does not yet invoke the Reaper interpreter or exchange live policy decisions with it. A future authenticated native host broker is required for that runtime connection.

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

The current shell implementation is partial, not a bootable operating system desktop.

Implemented in this repository:

- browser/PWA desktop presentation in Mora;
- virtual workspace switching and local persistence;
- window focus, minimize, maximize/restore and close controls;
- keyboard command palette and allowlisted application/workspace/theme/focus commands;
- searchable 20-direction systems matrix with maturity and boundary descriptions;
- Reaper contracts for window state, workspace/session policy, command authorization and notification records;
- read-only Python host status, application catalogue validation and shell-readiness CLI;
- Python tests for host reporting, catalogue validation and CLI JSON output;
- Reaper contract tests executed in CI on the tree-walk and VM engines.

Not implemented by this change:

- native Wayland/X11 compositor, native window manager or display server;
- kernel session manager, process isolation or capability enforcement;
- native terminal or arbitrary command execution;
- actual screen-lock service, power management or system settings daemon;
- real Wi-Fi, battery, GPU/NPU, temperature, PCIe, USB, frame-time or sensor collection in the browser shell;
- UEFI/boot integration or a bootable DuckOS image.

The repository currently defines **Reaper** as its system policy/source language. The shell presentation is JavaScript/HTML/CSS, while the read-only host adapter is Python. There is no separately implemented “OS language” runtime in this revision. Native privileged services must be added behind versioned interfaces rather than pretending that browser code is kernel code.

## Verification

Run the Python and catalogue tests:

~~~sh
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
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
