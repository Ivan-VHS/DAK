# Windows compatibility on DuckOS

## Scope and design

The compatibility centre combines the native host-side CLI with Mora's command builder. The browser shell does not execute host processes, inspect arbitrary host paths or grant itself filesystem access. Mora builds a bounded command and copies it to the user's terminal; the DuckOS CLI performs the operation after the user runs it.

The current backend targets Linux hosts. It detects installed tools, maintains user-owned Wine prefixes, installs a small allowlist of Winetricks components and launches an explicitly selected executable through Wine, Proton or DOSBox. The backend uses argument arrays and never invokes a command shell.

## Current integration matrix

| Project | Role | DuckOS integration |
|---|---|---|
| Wine | Win32 API compatibility runtime | Managed prefixes, status detection and process launch |
| Proton | Wine-based Steam compatibility runtime | Detects Steam Proton and launches with an explicit compatdata directory |
| CrossOver | Commercial Wine distribution | Detects and opens the installed manager; its own bottles remain externally managed |
| Bottles | Prefix manager | Detects and opens the installed manager; its own bottles remain externally managed |
| Lutris | Game launcher | Detects and opens the installed launcher |
| Heroic Games Launcher | Game launcher | Detects and opens the installed launcher |
| PortProton | Wine/Proton launcher | Detects and opens the installed launcher |
| Winetricks | Runtime dependency installer | Runs only the allowlisted component verbs below |
| PlayOnLinux | Prefix manager | Detects and opens the installed manager |
| Whisky | macOS Wine frontend | macOS-only; not supported on Linux |
| Kegworks | macOS wrapper builder | macOS-only; not supported on Linux |
| Game Porting Toolkit | Apple/Metal translation toolkit | macOS-only; not supported on Linux |
| DXVK | Direct3D 8–11 to Vulkan | Installable into a managed prefix through Winetricks |
| vkd3d-proton | Direct3D 12 to Vulkan | Installable into a managed prefix through Winetricks; Proton may also supply its own version |
| DOSBox / DOSBox Staging | DOS emulator | Direct launch for DOS-compatible 8.3 executable names |
| ReactOS | Separate NT-like operating system | Documented as a VM guest, not a compatibility layer; no guest image is bundled |

The Mora catalogue distinguishes an executable backend from an external manager, an installable graphics component, a macOS-only project and a separate guest operating system. A detection result means only that a command was found on the host.

## Install host packages

Install Wine, Winetricks, DOSBox or Steam/Proton using the package source supported by the target Linux distribution. DuckOS does not silently install host packages or download third-party runtime binaries. CrossOver, Bottles, Lutris, Heroic, PortProton and PlayOnLinux remain separately maintained applications.

After installation, inspect the host:

~~~sh
duckos compatibility status
duckos compatibility prefixes
~~~

The status output includes host architecture, detected runtime/launcher commands, Vulkan loader presence and the managed prefix root. It does not certify that a particular graphics driver, game or anti-cheat is compatible. The six external manager frontends can be opened by DuckOS without taking over their own library or prefix formats:

~~~sh
duckos compatibility open-manager --name bottles
duckos compatibility open-manager --name lutris
~~~

## Create and use a Wine prefix

~~~sh
duckos compatibility create-prefix --name games --arch win64
duckos compatibility prefixes
duckos compatibility launch --engine wine --prefix games -- /home/user/Games/setup.exe
~~~

Use **--arch win32** for a 32-bit prefix. Prefixes are stored under:

~~~text
$XDG_DATA_HOME/duckos/compatibility/prefixes/
~~~

When **XDG_DATA_HOME** is not set, the default is **~/.local/share/duckos/compatibility/prefixes/**. Each managed prefix includes versioned DuckOS metadata. Prefix names are restricted to safe ASCII identifiers and symbolic-link escapes are rejected.

## Proton and DOSBox

Proton needs an existing Steam compatdata directory for the selected title:

~~~sh
duckos compatibility launch --engine proton --compat-data /home/user/.local/share/Steam/steamapps/compatdata/APPID -- /home/user/Games/game.exe
~~~

DOSBox direct launch supports **.exe**, **.com** and **.bat** files with an 8.3-compatible ASCII filename:

~~~sh
duckos compatibility launch --engine dosbox -- /home/user/DOS/GAME.EXE
~~~

For complex DOS installs, use DOSBox's own configuration and mount workflow. The simple DuckOS launcher is deliberately narrower.

## ReactOS as a separate QEMU guest

ReactOS is not a Wine prefix or a Win32 translation library. DuckOS can create a qcow2 virtual disk and start a separately supplied guest installation through QEMU:

~~~sh
duckos compatibility create-reactos-disk --path /home/user/VM/reactos.qcow2 --size-gib 16
duckos compatibility launch-reactos --disk /home/user/VM/reactos.qcow2 --iso /home/user/Downloads/ReactOS.iso --memory-mib 2048 --cpus 2
~~~

The disk's parent directory must already exist. The VM has networking disabled by default, and the installer ISO must be supplied by the user. Once installed, start the guest without the `--iso` option. This provides a QEMU launch path, not a promise that every ReactOS driver or Windows application will work.

## Install graphics/runtime components

The following Winetricks verbs are accepted by the CLI: **dxvk**, **vkd3d**, **vcrun2019**, **vcrun2022**, **corefonts**, **d3dcompiler_47** and **dotnet48**.

~~~sh
duckos compatibility install-component --prefix games --component dxvk
duckos compatibility install-component --prefix games --component vkd3d
duckos compatibility install-component --prefix games --component vcrun2022
~~~

Winetricks may download upstream redistributables and requires network access. Only run it when you explicitly choose to install that component. DLL installation can affect application compatibility; use separate prefixes for separate games when appropriate.

## Security and compatibility boundaries

- Wine and Proton programs normally run as the current user. This backend does not provide a process sandbox; do not run untrusted executables.
- The browser shell cannot call the CLI. Commands are copied to a terminal and are not executed on button click.
- Anti-cheat bypass, Windows kernel-driver loading, arbitrary driver patching, Windows NT kernel emulation and universal game compatibility are not provided.
- DirectX translation requires suitable host Vulkan drivers and compatible GPU features. A detected Vulkan loader is not a complete driver validation.
- ReactOS must be acquired and booted as a separate guest OS through an independently configured virtualization stack. It is not bundled or automatically launched by this subsystem.
- Whisky, Kegworks and Apple's Game Porting Toolkit target macOS/Metal and are not components of a Linux DuckOS build.

## Verification

Run the Python suite and Mora browser contract tests:

~~~sh
python -m unittest discover -s tests -v
npm test
~~~

The tests exercise validation, prefix lifecycle rollback, safe process argument construction and command generation. They do not replace testing with real Wine/Proton builds, physical GPUs, game launchers or individual games.
