# Native specialist applications in DuckOS

DuckOS keeps Reaper, Pytyliki, OPlague and VentuSample as independent, commit-pinned projects. Mora provides one native Qt launcher, while each specialist opens in its own application window and keeps its upstream runtime, build system, tests, source history and licence.

## Application catalogue

| Application | Native interface | Supported host | Readiness rule |
|---|---|---|---|
| Reaper | Python Studio / reference workbench | Windows, Linux, macOS | The pinned checkout must contain the Reaper package and Studio entry point |
| Pytyliki | Win32 GUI backed by its C11 core | Windows | A built `pytyliki-gui.exe` must exist in a registered build output |
| OPlague | Python 3.10+ / Tkinter | Windows, Linux, macOS | The pinned checkout, `oplague_app.py`, Python and Tkinter must be present; live PnP inventory remains Windows-only |
| VentuSample | Qt 6 Widgets / C++20 | Windows, Linux, macOS | A built platform-native VentuSample executable or macOS app bundle must exist |

A source checkout is not the same as an installed or built application. Mora and the CLI report a project as unavailable when the required runtime or binary is missing. They do not compile, download, install or execute project content automatically.

## Open the native Mora desktop

Install the native UI extra and open Mora:

```sh
python -m pip install -e '.[native-ui]'
duckos mora gui
```

The four specialist projects appear as first-class application cards. Selecting a card opens a readiness panel with the repository, platform, runtime and launch state. The launch action is enabled only when the allowlisted entry point is available.

The existing Reaper Studio control is preserved. Mora Boost now opens the local OPlague workbench instead of navigating to a repository web page.

## Command-line discovery and launch

List project readiness:

```sh
duckos apps list
```

Open one application after checking its readiness:

```sh
duckos apps open reaper
duckos apps open pytyliki
duckos apps open oplague
duckos apps open ventusample
```

The command returns a JSON launch record with the application ID, PID and `shell=false`. An unavailable project returns a non-zero CLI error with a reason rather than attempting a fallback command.

## Build the native interfaces

Builds are explicit developer actions. The launcher never triggers these commands on the user's behalf.

### Pytyliki on Windows

```powershell
cmake -S projects/pytyliki -B projects/pytyliki/build -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON
cmake --build projects/pytyliki/build --config Release --parallel
ctest --test-dir projects/pytyliki/build -C Release --output-on-failure
```

The launcher checks for `projects/pytyliki/build/Release/pytyliki-gui.exe` and the documented non-Release layout. The portable C11 library and CLI remain usable independently; the native GUI is Windows-only.

### OPlague

```sh
python projects/oplague/oplague_app.py
python -m unittest discover -s projects/oplague/tests -v
```

The native app is a separate Tk window. On Windows it can read local Plug and Play inventory. On Linux and macOS, saved package inspection remains available but Windows PnP inventory does not.

### VentuSample

```sh
cmake -S projects/ventusample -B projects/ventusample/build -DCMAKE_BUILD_TYPE=Release
cmake --build projects/ventusample/build --config Release --parallel
ctest --test-dir projects/ventusample/build -C Release --output-on-failure
```

Qt 6 Widgets must be available when configuring the desktop target. The app stays an offline sample-generation and DSP workstation. Optional Reaper C17 integration must still be enabled explicitly with `-DREAPER_SOURCE_DIR=projects/reaper`.

### Reaper

```sh
python -m pip install -e projects/reaper
duckos reaper status
duckos reaper studio
```

Reaper uses the existing bounded subprocess workbench. Static checks continue to use the Reaper CLI; no Reaper source is imported into the DuckOS process.

## Runtime safety and source ownership

The launcher is a fixed registry, not a shell or manifest-command interpreter:

- Project paths are resolved under the DuckOS `projects/` directory. Symlinked project roots and file entry points are rejected.
- Only the four registered application IDs can be opened.
- Python projects use the configured DuckOS Python executable and a fixed script or module.
- Native projects launch only the expected executable files inside their own checkout.
- Every child process is created with an argument vector, `shell=False`, and a project-specific working directory.
- Missing native binaries are reported as `not_built`; the launcher never invokes CMake or downloads dependencies.
- No administrator elevation, driver loading, service mutation or kernel execution is requested.

Upstream source is not copied into DuckOS. Each project retains its own Git submodule pin, tests, contributors, `LICENSE` and third-party notices.

## Interoperability boundaries

The native windows are integrated into Mora's application catalogue, but their domain data is not merged into one shared database. Use the interfaces each project already publishes:

- Pytyliki: versioned C ABI and structured processor/report outputs.
- OPlague: bounded local evidence reports and read-only device/package inspection.
- VentuSample: native C++ core, offline render output and versioned JSON manifests.
- Reaper: CLI JSON results and the bounded workbench bridge.

Cross-project jobs must add a reviewed, versioned contract with ownership, input validation, limits, cancellation, error handling and provenance. Never infer that an app card grants device, filesystem, process or kernel privileges.

## Verification

The native launcher tests cover missing checkouts, platform gating, unbuilt binaries, entry-point validation, symlink rejection and no-shell process creation:

```sh
python -m unittest tests.test_native_apps -v
python -m unittest tests.test_repository_federation -v
```

These tests verify the user-space discovery and launch boundary. They do not claim that native binaries have been built on every platform or that DuckOS is a bootable operating-system image.
