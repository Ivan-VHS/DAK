# Native Reaper integration

**Project:** Dak  
**Specialist runtime:** Reaper  
**Maintainer:** Ivan-VHS  
**Status:** implemented user-space launcher, source-check bridge and native Dak Desktop panel

## Architecture

Dak treats Reaper as its canonical systems-language and policy implementation while keeping the two repositories independently versioned. The Reaper source remains the pinned Git submodule at `projects/reaper`; the federation registry records the reviewed integration commit and the native-workbench status.

The integration is intentionally a process boundary:

```text
Dak Desktop native window / dakos CLI
                 |
                 v
       dakos.desktop.reaper
       ReaperWorkbench
                 |
       explicit argument vector
       shell=False, bounded timeout
                 |
                 v
      projects/reaper Python package
       ├── Reaper CLI / static checker
       └── Reaper Studio (separate process)
```

Dak does not import the Reaper interpreter, AST or Python modules into its own process. Reaper owns its language grammar, runtime, compiler and diagnostics. Dak provides discovery, native UI entry points and a bounded host process bridge.

## Initialize the source checkout

From an existing Dak clone:

```sh
git submodule update --init projects/reaper
python -m pip install -e .
```

The Dak package installs the `dakos` command. The Reaper submodule is an independent Python project and keeps its own editable install and dependency contract.

When the source checkout is outside the standard `projects/reaper` location, set `DAK_REAPER_ROOT` to its absolute path or pass `--root` to the CLI.

## Native shell entry points

Open the native Dak Desktop window:

```sh
dakos desktop gui
```

The **Reaper** tab offers:

- checkout discovery and an evidence-based capability summary;
- opening the Reaper Studio desktop application as a separate process;
- selecting a local `.rpr` or `.most` file;
- running the normal parser and static-check command;
- running focused type diagnostics when the selected Reaper checkout contains that capability.

The panel's source-check operations run on a worker thread, so a large local source file does not block the native window. The result is returned to the UI as bounded text/JSON diagnostics.

## Command shell

```sh
dakos reaper status
dakos reaper studio
dakos reaper check ./examples/program.rpr
dakos reaper typecheck ./examples/program.rpr
```

Use an alternate checkout explicitly:

```sh
dakos reaper --root /path/to/Reaper status
dakos reaper --root /path/to/Reaper check ./program.rpr
```

The `check` command delegates to Reaper's `--check --json` path. The focused `typecheck` command is enabled only when the located checkout contains both the type-checking module and its CLI dispatch. Older pinned checkouts are reported as lacking that capability rather than being treated as if it were present.

## Process and trust boundaries

- Every process is started with a fixed argument list and `shell=False`.
- The Reaper checkout is discovered from the Dak submodule path, `DAK_REAPER_ROOT`, an explicit `--root`, or the current working directory.
- A selected source must be an existing regular `.rpr` or `.most` file. Symbolic-link sources are rejected by the bridge.
- Check and typecheck are static operations; they do not execute the selected source program.
- Check commands have a 30-second timeout and captured output is limited to one million characters per stream.
- Opening Reaper Studio starts a separate user-space process. Studio's own Run/Debug actions remain explicit user actions.
- Dak does not silently grant Reaper FFI, device access, administrator rights, driver installation, kernel access or filesystem-wide permissions.
- The browser-based Mora shell is not used as a host-process launcher. The actual launch path is the native Dak Desktop panel or the `dakos reaper` command.

This is a native user-space integration surface, not a claim that the Dak kernel has already implemented process isolation, a privileged application broker or a hardware compositor.

## Verification

Run the focused tests:

```sh
python -m unittest tests.test_reaper_integration tests.test_reaper_cli -v
```

The tests use temporary fake Reaper checkouts and mocked subprocess boundaries. They verify discovery, capability detection, argument-vector construction, JSON result handling, timeouts, source validation and the native Studio launch handoff. They do not run Reaper source or claim kernel-level process isolation.
