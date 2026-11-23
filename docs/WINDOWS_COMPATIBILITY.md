# Windows application compatibility in DuckOS

**Status:** PE inspection foundation plus a partial Linux host-runtime integration; not a Wine replacement  
**Updated:** 2026-11-23  
**Project author/developer:** Ivan-VHS

DuckOS now has a read-only PE inspection engine, isolated prefix scaffolding and command-line diagnostics. These parts establish file-format and profile contracts for a future native runtime. They do not load a Windows process or claim that a game can start.

## What is implemented

- Bounded PE32 and PE32+ parsing: DOS/NT signatures, COFF and optional headers, machine type, subsystem, image properties and section records.
- Static import-directory parsing with bounded descriptor and DLL-name reads.
- Local SHA-256 reporting during PE inspection.
- Isolated prefix directory creation, versioned prefix.json metadata and symlink-aware layout validation.
- Static DLL search-path checks and a dry-run launch report with explicit blockers.
- JSON output through the DuckOS CLI and static inspection in the Bridge panel in Mora.
- A separate Linux host adapter for installed Wine, Steam Proton and DOSBox; managed Wine prefixes; an allowlisted Winetricks component installer; safe external-manager launch; and a QEMU path for a user-supplied ReactOS guest.

The native DuckOS PE inspection layer still does not map or launch a Windows executable and does not implement Win32/NT APIs. Actual process launch is delegated to separately installed upstream Wine, Proton or DOSBox from the Linux host CLI. Creating a managed Wine prefix uses Wine's own wineboot; the earlier prefix-create command still creates only the native DuckOS metadata scaffold. Neither path installs host packages automatically or grants administrator rights.

## CLI

Install the project in a Python 3.10+ environment:

~~~sh
python -m pip install -e .
~~~

Inspect a Windows executable:

~~~sh
duckos inspect-pe ./game.exe
~~~

Create and validate an isolated profile:

~~~sh
duckos prefix-create ~/.local/share/duckos/prefixes game --architecture x86_64
duckos prefix-info ~/.local/share/duckos/prefixes/game
~~~

Check static DLL imports and show why launch is currently blocked:

~~~sh
duckos compat-diagnose ./game.exe --prefix ~/.local/share/duckos/prefixes/game
duckos compat-plan ./game.exe --prefix ~/.local/share/duckos/prefixes/game
duckos compat-status
~~~

The compat-plan command is deliberately a report-only command. It never invokes a shell, creates a process or changes the prefix.

## Linux host runtime integration

The additional **compatibility** command group does not replace the PE inspection commands above. It delegates to upstream runtimes already installed on a supported Linux host. Inspect what is present first:

~~~sh
duckos compatibility status
duckos compatibility prefixes
~~~

The host CLI reports discovered executable paths, Linux architecture, Vulkan loader presence and the managed prefix root. Detection only confirms that a command was found; it does not prove that a particular game, driver, Vulkan feature or anti-cheat works.

Create an actual Wine prefix, then install a dependency only when the application requires it:

~~~sh
duckos compatibility create-prefix --name games --arch win64
duckos compatibility install-component --prefix games --component dxvk
duckos compatibility install-component --prefix games --component vcrun2022
duckos compatibility launch --engine wine --prefix games -- /home/user/Games/setup.exe
~~~

Wine prefixes are stored in **$XDG_DATA_HOME/duckos/compatibility/prefixes/** or **~/.local/share/duckos/compatibility/prefixes/** when XDG_DATA_HOME is unset. Separate prefixes are recommended for unrelated titles. The allowlist is intentionally bounded to **corefonts**, **d3dcompiler_47**, **dotnet48**, **dxvk**, **vcrun2019**, **vcrun2022** and **vkd3d**. Winetricks may fetch third-party redistributables after you explicitly request an install.

For a Steam title, specify an existing Steam compatdata directory and an executable:

~~~sh
duckos compatibility launch --engine proton --compat-data /home/user/.local/share/Steam/steamapps/compatdata/APPID -- /home/user/Games/game.exe
~~~

DOSBox direct launch is limited to DOS **.exe**, **.com** and **.bat** files with an 8.3-compatible ASCII filename:

~~~sh
duckos compatibility launch --engine dosbox -- /home/user/DOS/GAME.EXE
~~~

For complex DOS installations, configure mounts and drives using DOSBox's own configuration workflow.

### External managers and macOS-only projects

| Project | DuckOS integration |
|---|---|
| CrossOver | Detect and open an installed manager; its bottles and compatibility recipes remain managed by CrossOver |
| Bottles | Detect and open the installed prefix manager; its own bottle state remains external |
| Lutris | Detect and open the launcher; game scripts and runner versions remain managed by Lutris |
| Heroic Games Launcher | Detect and open the launcher; account/store integration remains managed by Heroic |
| PortProton | Detect and open the installed launcher; its own configuration remains external |
| PlayOnLinux | Detect and open the installed Linux manager |
| PlayOnMac | macOS-only variant; not part of a Linux DuckOS build |
| Whisky | macOS-only Wine frontend; not part of a Linux DuckOS build |
| Kegworks / Wineskin | macOS wrapper tooling; not part of a Linux DuckOS build |
| Apple Game Porting Toolkit | macOS and Metal-specific; not a Linux DirectX translation backend |
| DXVK | Winetricks may install DXVK in a selected Wine prefix (Direct3D 8–11 over Vulkan) |
| vkd3d | Winetricks verb installs upstream vkd3d; this is not the same thing as vkd3d-proton |
| vkd3d-proton | Normally supplied by Proton's runtime; the Winetricks vkd3d verb must not be described as vkd3d-proton |
| DOSBox / DOSBox Staging | Direct DOS executable launch from the host CLI |
| ReactOS | A separately installed guest OS, not a Wine layer or DLL pack |

To open an installed Linux manager:

~~~sh
duckos compatibility open-manager --name bottles
duckos compatibility open-manager --name lutris
~~~

The recognised manager names are **crossover**, **bottles**, **lutris**, **heroic**, **portproton** and **playonlinux**. The command starts the existing application; it does not import libraries, migrate prefixes or silently change its runtime configuration.

### ReactOS as a separate QEMU guest

ReactOS is handled as a guest operating system. DuckOS can create a qcow2 virtual disk and start a user-supplied installation ISO:

~~~sh
duckos compatibility create-reactos-disk --path /home/user/VM/reactos.qcow2 --size-gib 16
duckos compatibility launch-reactos --disk /home/user/VM/reactos.qcow2 --iso /home/user/Downloads/ReactOS.iso --memory-mib 2048 --cpus 2
~~~

The destination directory must already exist. The default VM configuration disables networking with **-nic none**. After installation, start the guest using the disk without the **--iso** option. This is a QEMU launch path; it does not certify ReactOS driver or application compatibility. QEMU and qemu-img must be installed separately.

### Host security and support limits

- The host adapter requires Linux. macOS-only applications and Apple's Metal translation stack are not presented as Linux features.
- Wine and Proton processes run with the current user's host permissions. This integration is not a security sandbox; do not run untrusted EXE files.
- Mora does not invoke host processes. It prepares and copies a command; the user explicitly runs it in a terminal.
- DXVK/vkd3d need a working Vulkan driver and compatible hardware features. A Vulkan loader library alone is not sufficient validation.
- Anti-cheat bypass, arbitrary Windows kernel-driver loading, kernel-mode Windows emulation, automatic driver patching and universal game compatibility are not provided.
- The host package manager and game-specific runtime dependencies are not modified automatically. Install trusted distro packages for Wine, Winetricks, DOSBox, QEMU and Proton through the relevant distribution or Steam installation.

## Prefix layout

Each prefix has its own drive_c, user data folders, dosdevices, registry placeholder, logs, shader-cache placeholder and snapshots directory. The manifest records architecture and current runtime maturity. The directory names establish the future application boundary; they do not imply that NTFS semantics, a Windows registry, copy-on-write overlays or snapshot restore already exist.

The manifest contract is defined in schemas/windows-prefix.v1.schema.json.

## Runtime boundary

A working Windows compatibility runtime still needs at least:

1. PE image mapping, relocations, import resolution, TLS and a correct x86/x64 ABI.
2. A process manager, address spaces, NT object/handle model, syscalls, timers, synchronization, SEH/VEH and WoW64.
3. Meaningful implementations of ntdll, kernel32, user32, gdi32, registry, COM/OLE and Windows installer behavior.
4. DirectX 9–12 translation and legacy graphics paths, shader/pipeline caches, swapchain/frame pacing, VRR and HDR.
5. WASAPI/DirectSound/XAudio2, Raw Input/DirectInput/XInput, USB/HID and clipboard bridges.
6. Winsock2/IOCP, TLS and certificate integration, launcher protocols and documented anti-cheat compatibility checks.
7. A capability-enforced process sandbox, device broker, structured crash logs, per-game version pinning and reproducible tests.

DXVK/VKD3D, QEMU/CPU translation or other upstream components may be evaluated as separate backends. This repository does not bundle or silently install them. Kernel anti-cheat drivers are not emulated or bypassed.

## Traceability against the 66-point specification

| Rule(s) | Current state |
|---|---|
| 1 | **Partial:** validates PE32/PE32+ headers, sections and imported DLL names; no image loader or relocations |
| 2–12 | **Planned:** Win32 ABI, WoW64, TLS/SEH, NT handles, synchronization, timers, API DLLs, DLL overrides, virtual memory and IPC are not implemented |
| 13 | **Partial:** each prefix has its own directory tree and manifest |
| 14–24 | **Planned:** overlay layers, Windows path semantics, case-insensitive filesystem, registry, runtime installation, sandbox enforcement, MSI/installer support and snapshots are not implemented |
| 25–36 | **Planned:** DirectX/Vulkan translation, legacy APIs, shader cache, scaling, frame pacing, HDR, multi-monitor, GDI/DirectWrite, VRAM budgeting and video decode are not implemented |
| 37–46 | **Planned:** audio, surround/HRTF, MIDI/EAX, device switching, gamepad/input, cursor capture, scan-code mapping, pointer devices, clipboard bridge and USB passthrough are not implemented |
| 47–55 | **Planned:** Winsock2/IOCP, TLS integration, IPX/LAN, browser runtimes, anti-cheat diagnostics, network policy, DNS fallback and URI handlers are not implemented |
| 56 | **Partial:** the prefix uses a versioned JSON manifest; a full per-game launch manifest is not implemented |
| 57 | **Planned:** no recipe database or automatic dependency download |
| 58 | **Partial:** reports missing imported DLL files in inspected search paths; does not resolve missing functions or diagnose crashes |
| 59 | **Partial:** CLI emits structured JSON; subsystem trace logs are not implemented |
| 60–62 | **Planned:** process-tree termination, background resource policy and portable prefix export are not implemented |
| 63 | **Partial:** Bridge provides PE inspection and a separate Compatibility panel copies Linux host CLI commands; Mora is not a native runtime manager |
| 64–66 | **Partial/Planned:** the host CLI can delegate launch to installed Wine/Proton/DOSBox; native DuckOS runtime pinning, built-in one-click process launch, A/B compatibility benchmark and per-game verification remain unimplemented |

## Verification

The focused Python tests cover valid and malformed PE metadata, import enumeration, prefix creation and validation, DLL search diagnostics, non-executing launch plans and CLI status output. They do not prove native ABI compatibility, graphics performance, anti-cheat support or game execution.
