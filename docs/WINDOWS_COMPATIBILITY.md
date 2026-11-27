# Windows application compatibility in DAKOS

**Status:** compatibility foundation, not a Wine replacement  
**Updated:** 2026-11-23  
**Project author/developer:** Ivan-VHS

DAKOS now has a read-only PE inspection engine, isolated prefix scaffolding and command-line diagnostics. These parts establish file-format and profile contracts for a future native runtime. They do not load a Windows process or claim that a game can start.

## What is implemented

- Bounded PE32 and PE32+ parsing: DOS/NT signatures, COFF and optional headers, machine type, subsystem, image properties and section records.
- Static import-directory parsing with bounded descriptor and DLL-name reads.
- Local SHA-256 reporting during PE inspection.
- Isolated prefix directory creation, versioned prefix.json metadata and symlink-aware layout validation.
- Static DLL search-path checks and a dry-run launch report with explicit blockers.
- JSON output through the DAKOS CLI and the Bridge panel in Mora.

No executable image is mapped, no Windows API is implemented by this milestone, and no EXE or DLL is launched. Prefix creation does not download DLLs, install redistributables, populate the registry or grant host administrator rights.

## CLI

Install the project in a Python 3.10+ environment:

~~~sh
python -m pip install -e .
~~~

Inspect a Windows executable:

~~~sh
dakos inspect-pe ./game.exe
~~~

Create and validate an isolated profile:

~~~sh
dakos prefix-create ~/.local/share/dakos/prefixes game --architecture x86_64
dakos prefix-info ~/.local/share/dakos/prefixes/game
~~~

Check static DLL imports and show why launch is currently blocked:

~~~sh
dakos compat-diagnose ./game.exe --prefix ~/.local/share/dakos/prefixes/game
dakos compat-plan ./game.exe --prefix ~/.local/share/dakos/prefixes/game
dakos compat-status
~~~

The compat-plan command is deliberately a report-only command. It never invokes a shell, creates a process or changes the prefix.

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
| 63 | **Partial:** Bridge is available in Mora; it is a browser-shell panel, not a native runtime manager |
| 64–66 | **Planned:** runtime version pinning, A/B game benchmark and actual one-click Windows process launch are not implemented |

## Verification

The focused Python tests cover valid and malformed PE metadata, import enumeration, prefix creation and validation, DLL search diagnostics, non-executing launch plans and CLI status output. They do not prove native ABI compatibility, graphics performance, anti-cheat support or game execution.
