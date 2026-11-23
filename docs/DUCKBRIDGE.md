# DuckBridge

DuckBridge is the runtime discovery and launch-planning front end for DuckOS Windows compatibility. It builds on the existing PE32/PE32+ inspection, prefix metadata and compatibility diagnostics instead of maintaining a second PE parser.

## Commands

Install the build tools in a Python 3.10+ environment:

~~~sh
python -m pip install -e .
~~~

List installed compatibility and CPU-translation entry points:

~~~sh
duckos bridge runtimes
~~~

Inspect a PE or ELF file without running it:

~~~sh
duckos bridge inspect ./game.exe
duckos bridge inspect ./bin/tool
~~~

Prepare a dry-run application plan using Wine:

~~~sh
duckos bridge plan ./setup.exe --purpose application --backend wine
~~~

Prepare a Steam game plan using Proton and a chosen compatibility-data path:

~~~sh
duckos bridge plan ./game.exe --purpose game --compat-data "$HOME/.local/share/duckos/proton/game-id"
~~~

Select an existing Bottles or CrossOver bottle:

~~~sh
duckos bridge plan ./setup.exe --backend bottles --bottle "Work tools"
duckos bridge plan ./setup.exe --backend crossover --bottle "Office"
~~~

Append target arguments as separate values:

~~~sh
duckos bridge plan ./setup.exe --backend wine --arg /quiet --arg "path with spaces"
~~~

All commands return machine-readable JSON. The versioned launch-plan contract is defined in schemas/duckbridge-plan.v1.schema.json.

## Runtime inventory

The local inventory checks for:

- Wine and Wine64 commands in PATH.
- Proton in PATH or common Steam installation roots.
- CrossOver's Linux Wine entry points in the user's CrossOver directory and /opt/cxoffice.
- Bottles CLI in PATH, or an installed Flatpak Bottles application with Flatpak available.
- Box64 and QEMU user-mode CPU translators for supported ELF architectures.

Detection only checks whether a known path exists and is executable. DuckBridge does not invoke --version, call a package manager, connect to the network, install components, populate a prefix or modify the host.

## Architecture and backend policy

PE inspection delegates to the shared duckos.compat.pe parser. The report includes PE32/PE32+ format, machine architecture, sections, imported DLL names and a local SHA-256 digest. Existing compatibility diagnostics and isolated prefix scaffolding remain available through compat-diagnose, prefix-create, prefix-info and compat-plan.

PE runtime planning is currently scoped to x86-64 Linux hosts. Automatic backend preference is Proton then Wine for games, and Wine then CrossOver/Bottles for applications. CrossOver and Bottles require an existing named bottle. Proton requires a caller-selected compatibility-data directory. The planner does not create that directory.

ELF inspection reads only a bounded header and reports class, byte order and machine type. Native plans are prepared only when target and host architectures match and the file has executable permission. On ARM64, Box64 is considered for x86-64 Linux binaries; a matching QEMU user-mode translator may be selected for other supported architectures. A translator does not supply target libraries or a sysroot.

Arguments are represented as a structured argv array; the planner never builds or evaluates a shell command. Environment changes are returned separately. Runtime command templates follow the documented Bottles and CrossOver CLI syntax; the selected binary is never invoked during planning.

## Security and maturity

- Both execution_started and prefix_created are always false in the plan schema.
- The target file is never started, mapped into memory or uploaded.
- The selected runtime is never started.
- The tool does not install packages, drivers, DLLs or graphics components.
- No anti-cheat bypass, DRM circumvention, malware verdict or signer trust is claimed.
- Runtime discovery does not prove ABI, graphics, audio, DRM or per-game compatibility.
- Mora is a browser shell and cannot inspect installed host programs directly; use the native DuckOS CLI.

DuckBridge is an orchestration and planning tool, not a PE loader, NT process manager, Win32 subsystem, Wine replacement, DirectX/Vulkan translation layer, sandbox or production launcher. Those native execution layers remain explicitly unimplemented in the Windows compatibility status report.

## Verification

Run the complete Python suite:

~~~sh
python -m unittest discover -s tests -v
~~~

The DuckBridge tests use synthetic PE/ELF headers and temporary executable stubs. They do not invoke Wine, Proton, CrossOver, Bottles, Box64, QEMU or an inspected application. Existing Windows compatibility tests remain the source of truth for the shared PE parser and prefix tooling.

## Attribution

Project author/developer: **Ivan-VHS**. Existing contributor credits and third-party copyright notices remain unchanged.


## Illidia launcher integration

Illidia consumes DuckBridge runtime discovery and compatibility plans, but owns the game-library model, source adapters, trust review and play-session records. When a game uses `auto`, `wine`, `proton`, `crossover`, `bottles` or `qemu` without an explicit command override, Illidia calls `build_launch_plan`, requires a `ready` result and starts the returned argv with the returned environment after its own trust review. The planner still never executes a runtime or target. The subsequent host-side process launch is performed by Illidia and is not yet protected by kernel-enforced DuckOS sandboxing. See [Illidia universal game library and launcher](ILLIDIA_GAME_LAUNCHER.md).
