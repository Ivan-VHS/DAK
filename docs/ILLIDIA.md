# Illidia — DuckOS game library and launcher

Illidia is DuckOS's local game-library experience. DuckBridge supplies executable inspection, runtime discovery and structured launch planning; Illidia adds a persistent game catalogue, per-game compatibility data and explicit process launch.

The current launcher delegates Windows execution to an installed Wine-compatible runtime. It does not implement a native Windows loader or replace Wine, Proton, CrossOver or Bottles.

## Add and launch games

Install the DuckOS build tools in a Python 3.10+ environment:

~~~sh
python -m pip install -e .
~~~

Register an existing local executable:

~~~sh
duckos illidia add "$HOME/Games/My Game/game.exe" --name "My Game" --backend auto
duckos illidia list
~~~

Start the game:

~~~sh
duckos illidia launch my-game
~~~

The generated identifier is based on the game name. Use `duckos illidia list` to see the exact identifier and the runtime selected for each entry.

Use optional wrappers and process control when needed:

~~~sh
duckos illidia launch my-game --gamemode --mangohud
duckos illidia launch my-game --wait
~~~

`--gamemode` requires `gamemoderun` on PATH. `--mangohud` requires `mangohud` on PATH. The wrappers are opt-in and are never downloaded or installed by Illidia.

A game can be removed from the library without deleting its executable or compatibility data:

~~~sh
duckos illidia remove my-game
~~~

## Runtime selection

For Windows PE files on x86-64 Linux, automatic game selection prefers Proton, then Wine, CrossOver and Bottles. CrossOver and Bottles require the name of an existing bottle. Proton and Wine receive a separate per-game data directory under:

~~~text
$XDG_DATA_HOME/duckos/illidia/compatdata/<game-id>
~~~

When `XDG_DATA_HOME` is not set, the default root is `~/.local/share/duckos/illidia/compatdata`. Proton receives that directory as `STEAM_COMPAT_DATA_PATH`; Wine receives it as `WINEPREFIX`. The selected external runtime initializes and manages its own prefix contents. Illidia creates only the per-game directory and does not copy Windows DLLs into it.

Native ELF games are launched directly when the host architecture matches. ARM64 CPU translation remains available through the existing DuckBridge Box64/QEMU planning rules when the corresponding translator is detected.

## Compatibility options

The following Proton-specific options are available:

- `--wined3d`: request Proton's WineD3D fallback instead of the normal DXVK/VKD3D path.
- `--no-esync`: set `PROTON_NO_ESYNC=1`.
- `--no-fsync`: set `PROTON_NO_FSYNC=1`.

They are opt-in, are rejected for non-Proton backends and do not install or replace graphics components. DXVK and VKD3D availability still depends on the selected runtime build, the GPU driver and the game.

For a review-only command plan, use DuckBridge:

~~~sh
duckos bridge plan ./game.exe --purpose game --backend proton --compat-data "$HOME/Games/compat/my-game"
duckos bridge plan ./game.exe --purpose game --backend wine --wine-prefix "$HOME/Games/compat/my-game"
~~~

A plan never starts a process. `duckos illidia launch` is the explicit operation that starts the selected executable/runtime process.

## Library and process boundaries

The library is stored as a versioned JSON document. It records the executable path, display name, backend preference, bottle name, launch arguments and last launch result. Removing an entry does not delete game files.

The launcher:

- validates that the registered target is still a regular local file;
- reuses DuckBridge's PE/ELF inspection and runtime selection;
- passes an argument vector directly to `subprocess.Popen` with `shell=False`;
- starts in the game's containing directory and inherits the user's environment, adding only runtime-specific values;
- starts a new session by default, or waits for the process when `--wait` is supplied;
- records the launch timestamp and, when waited for, the exit code.

A successful process start is not a compatibility verdict. It does not guarantee graphics, audio, input, networking, DRM or anti-cheat support. Illidia does not bypass anti-cheat, DRM, launchers, account checks or platform restrictions.

## Current scope and next native work

Implemented in this repository:

- local game library registration, listing and removal;
- Wine/Proton process launch through detected installations;
- CrossOver/Bottles launch planning for named existing bottles;
- isolated per-game Wine/Proton data directories;
- optional GameMode and MangoHud wrappers;
- opt-in Proton WineD3D, esync and fsync switches;
- structured launch results and synthetic-runtime tests.

Not implemented yet:

- native NT/Win32 process execution inside DuckOS;
- graphical game-store integrations or automatic game downloads;
- cloud-save synchronization, clip recording/sharing, achievement providers or native Do Not Disturb integration;
- a privileged authenticated Mora-to-host process-launch service;
- automatic dependency, driver, DXVK or VKD3D installation;
- game-specific compatibility ratings or anti-cheat guarantees.

Mora's current Illidia panel is a browser shell and cannot start arbitrary host executables. Use the native `duckos illidia` CLI until an authenticated DuckOS host service and UI integration are implemented.

## Verification

Run the Python suite:

~~~sh
python -m unittest discover -s tests -v
~~~

Illidia tests use synthetic PE files and temporary runtime stubs. They verify library operations, argument-safe process creation and per-game prefix setup; they do not prove that any specific commercial game runs successfully.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve existing contributor credits and third-party runtime notices.
