# Upstream Windows compatibility engines

**Status:** host-side adapters implemented; native DuckOS Windows process runtime not implemented  
**Updated:** 2026-11-23  
**Project author/developer:** Ivan-VHS

## Why this layer exists

DuckOS already has its own PE32/PE32+ inspection and isolated prefix metadata foundation. That foundation does not execute Windows binaries. This integration adds a separate Linux host adapter layer that coordinates proven upstream runtimes without pretending they are part of the DuckOS kernel.

The adapters live in duckos/compat/upstream.py and extend the existing duckos.compat package. Each tool retains its own process model, update channel, compatibility database, prefix semantics and license.

| Engine | DuckOS role | Preferred use |
|---|---|---|
| Proton | Steam compatibility tool | Steam games |
| Lutris | Game library and runner orchestrator | Multi-store games and emulator entries |
| Bottles | Isolated Wine environment manager | Independent application and gaming environments |
| CrossOver | Commercial CodeWeavers runtime | Supported desktop applications and games in CrossOver bottles |
| Wine | Generic fallback | One-off programs and dedicated WINEPREFIX environments |

## Runtime selection

Use the new CLI commands after installing the DuckOS Python package:

    duckos runtime-status
    duckos runtime-recommend steam-game
    duckos runtime-recommend multi-store
    duckos runtime-recommend isolated-app
    duckos runtime-recommend commercial-app
    duckos runtime-recommend windows-app

Recommendations are deterministic and only consider tools actually discovered on the host. They do not promise that a specific game or program is compatible.

## Explicit launch

    duckos runtime-launch proton ./game.exe --app-id 123456
    duckos runtime-launch lutris --game-id 123456
    duckos runtime-launch bottles ./tool.exe --bottle Work
    duckos runtime-launch crossover ./word.exe --bottle Office
    duckos runtime-launch wine ./setup.exe --prefix ~/.local/share/duckos/runtime-prefixes/Installer

Each invocation is explicit. The adapter produces an argv list and environment rather than a shell command string; process creation uses shell=False. Lutris uses its configured game ID. Proton requires a Steam App ID and sets the Steam compatibility environment. Bottles requires an existing bottle. CrossOver's --cx-app names an application already installed in the chosen bottle; use CrossOver's own installer workflow to install a new application. For Wine, pass a dedicated prefix for isolation instead of relying on the shared default prefix.

The adapter does not make up Lutris IDs or Steam App IDs and does not silently create missing Bottles or CrossOver environments.

## Creating environments

    duckos runtime-create bottles Games --environment gaming --arch win64
    duckos runtime-create bottles Office --environment application --arch win64
    duckos runtime-create wine LegacyTool --arch win32

Bottles creation is delegated to bottles-cli. Wine creation runs wineboot in a new DuckOS-owned prefix store. Existing prefix directories are never overwritten. Proton compatibility data is managed per App ID, and CrossOver bottles remain managed by CrossOver.

## Discovery and graphics checks

Runtime status searches common Steam installation and library paths, PATH, Flatpak registrations and standard CrossOver locations. It also reports whether common diagnostic tools such as vulkaninfo, nvidia-smi and glxinfo are present and whether /dev/dri exists.

These signals are inventory only. They do not prove that Vulkan works, a discrete GPU is being used, DXVK/VKD3D is configured, or an individual title is playable.

## Security and trust boundaries

- No shell=True or free-form command-string execution.
- Executable paths must resolve to existing local EXE files; Lutris requires a bounded game ID.
- Argument count and size are bounded and NUL bytes are rejected.
- Discovery and recommendation are read-only.
- Runtime launching occurs only through an explicit local CLI command.
- No administrator escalation, unattended package downloads, driver installation, registry patching or anti-cheat bypass.
- CrossOver is detected by executable presence only; DuckOS does not bundle, activate or validate its paid license.
- The Mora browser shell cannot start host processes. A native authenticated process broker and kernel-enforced capability sandbox are future work.

## Relation to the native DuckOS runtime

The upstream adapters let a Linux host use installed Proton, Lutris, Bottles, CrossOver or Wine. They are not the future DuckOS NT/Win32 runtime.

DuckOS still needs its own PE loader, process manager, NT objects and syscalls, Win32 API services, x86/WoW64 support, DirectX/Vulkan and audio/input/network bridges, GPU submission, app-level sandboxing and repeatable per-title tests. The existing native compatibility diagnostics remain deliberately non-executing.

## Upstream references

- [Valve Proton](https://github.com/ValveSoftware/Proton)
- [Lutris](https://github.com/lutris/lutris)
- [Bottles CLI](https://docs.usebottles.com/advanced/cli)
- [CodeWeavers CrossOver Linux guide](https://support.codeweavers.com/en_US/crossover-linux-user-guide)
