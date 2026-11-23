# Windows XP SP3 game launch compatibility

**Project author/developer:** Ivan-VHS  
**Contract:** `duckos.game-launch-profile.v1`

DuckOS models the predictable XP-era game launch chain as a versioned profile and an explicit host-runtime adapter. The profile preserves the old game's working directory, argument vector, display depth/mode and requested DirectX/OpenGL/Glide, DirectSound/WinMM/EAX, DirectInput and network APIs.

## Implemented

- Profile loading with a 1 MiB limit, strict schema/version checks and regular-file path validation.
- Explicit executable, working-directory and argument-vector validation.
- XP SP3 compatibility metadata and bounded display settings, including 8/16/24/32-bit color and refresh rate.
- An allowlist for environment overrides; `PATH`, `LD_PRELOAD`, shell fragments and arbitrary variables cannot be injected through a profile.
- An argv-only launch plan and an explicit Wine launch operation using `subprocess.Popen(..., shell=False)`.
- Optional use of an already-existing prefix. The launcher never creates it, changes its Windows version, installs redistributables or downloads components.

## Honest runtime boundary

The Wine adapter starts an external, already-installed runtime. It is not a native Win32 subsystem and does not recreate XP's XPDM driver model, DirectX 9 device, DirectSound hardware acceleration, EAX, DirectPlay, IPX/SPX or SafeDisc/SecuROM drivers. The requested Windows XP SP3 target is recorded but is **not enforced** by this launcher; the operator must verify the runtime's prefix configuration. Native NT/Win32 execution remains unavailable.

The tool does not bypass DRM, anti-cheat or kernel-driver checks. A missing runtime, invalid PE, unsupported architecture or missing prefix produces an explicit blocker rather than an attempted launch.

## Mapping of the 66 XP-era behaviors

| Area | Profile and adapter coverage |
|---|---|
| 1–12 · Process, shell and environment | Executable path, working directory, argv, constrained environment and explicit external process start; desktop-session and focus behavior remain host-runtime responsibilities. |
| 13–26 · Graphics and drivers | Records DirectDraw/Direct3D/OpenGL/Glide requirements and color/refresh settings; API translation, shader support, XPDM and legacy copy protection are not implemented here. |
| 27–38 · Memory, CPU and stability | Process launch is explicit; affinity, 32-bit address-space semantics, DEP, timer emulation and resource telemetry are separate capabilities. |
| 39–52 · Audio, input and network | Records DirectSound/WinMM/EAX, DirectInput/XInput and network API requirements; actual device bridges and DirectPlay/IPX services are not claimed. |
| 53–66 · Compatibility and operations | Versioned profiles, deterministic launch planning and explicit blockers are implemented; compatibility shims, patches, mods, widescreen fixes and driver installation remain external. |

The machine-readable field contract is in `schemas/game-launch-profile.v1.schema.json`. Use `python -m duckos.compat.game_profile profile.json --validate`, `--plan`, or the explicit `--launch` option. The latter requires a Wine runtime already available on the host.


## Rule-by-rule traceability (66 XP SP3 behaviors)

The labels below distinguish implemented metadata from behavior supplied by an external runtime. A profile field never proves that the underlying Windows API has been reproduced.

| # | XP-era behavior | Current coverage |
|---:|---|---|
| 1 | Direct EXE process start | **Partial:** PE inspection plus optional external Wine dispatch; no native Win32 loader |
| 2 | WinSta0\\Default session | **External:** host desktop/session manager |
| 3 | Resolution and refresh-rate changes | **Metadata:** stored in profile; no global display-mode change |
| 4 | Focus, ClipCursor and DirectInput capture | **External:** game/runtime/window manager |
| 5 | Full-screen shell covering | **External:** no shell suppression |
| 6 | INI/CFG and HKCU/HKLM settings | **Partial:** JSON profile only; no game-specific registry |
| 7 | DLL search order | **Partial:** static PE import inventory; runtime resolution is external |
| 8 | Working directory and environment | **Implemented:** explicit working directory and allow-listed environment |
| 9 | Current-user permissions | **External:** host user permissions; no elevation |
| 10 | DPI scaling | **External:** no DPI shim |
| 11 | Command-line arguments | **Implemented:** bounded argv vector, no shell parsing |
| 12 | Background game services | **External:** no additional services bundled |
| 13 | DirectX 9 baseline | **Metadata:** API requirement can be recorded; no D3D implementation |
| 14 | No native DirectX 10/11/12 on XP | **Documented boundary:** XP target does not add newer APIs |
| 15 | OpenGL ICD | **Audit only:** host ICD/runtime owns the actual GL path |
| 16 | Glide wrappers | **Audit only:** OPlague identifies wrapper dependency; none bundled |
| 17 | XPDM driver model | **Not implemented:** no XP display-driver model |
| 18 | dxdiag and hardware acceleration | **External:** host diagnostic tools |
| 19 | 16/32-bit color depth | **Metadata + audit:** supported values recorded; compositor support not guaranteed |
| 20 | Alt+Tab and Direct3D device loss | **External:** runtime/game responsibility |
| 21 | V-Sync and refresh-dependent timing | **External:** no frame limiter or physics shim |
| 22 | Pixel/Vertex Shader versions | **Not implemented:** no shader negotiation |
| 23 | Software renderer / no WARP | **External:** backend decides fallback |
| 24 | DirectDraw | **Audit only:** requirement recorded; API implementation external |
| 25 | SafeDisc/SecuROM/nProtect | **Not implemented:** no DRM or kernel-driver bypass |
| 26 | MSVC and DirectX redistributables | **Partial:** static imports only; no dependency installer |
| 27 | 32-bit address space and /3GB | **Not implemented:** host/runtime semantics apply |
| 28 | RAM and page-file pressure | **Partial:** Pytyliki whole-host RAM/swap telemetry |
| 29 | SMP and processor affinity | **Not implemented:** no affinity changes |
| 30 | QueryPerformanceCounter and CPU timing | **Not implemented:** no timer emulation |
| 31 | Heap isolation and ASLR | **External:** host/runtime memory policy |
| 32 | DEP | **External:** no DEP exceptions or policy changes |
| 33 | Task Manager process controls | **Partial:** system-wide telemetry; no per-game process control |
| 34 | Memory/resource leaks | **Not implemented:** no external process leak tracker |
| 35 | Display-driver reset behavior | **External:** host graphics driver |
| 36 | Background services and antivirus | **Partial:** whole-host resource pressure only |
| 37 | CD/DVD and disk loading | **External:** host filesystem/runtime |
| 38 | BAT/CMD scripts | **Not implemented:** arbitrary shell scripts are not accepted |
| 39 | DirectSound and WinMM | **Partial:** VentuSample format planner; no Windows API implementation |
| 40 | EAX and spatial audio | **Partial:** explicit host capability report only; no EAX engine |
| 41 | Audio device format/sample rate | **Partial:** VentuSample plans conversion; device bridge external |
| 42 | DirectInput | **Metadata:** requirement can be declared; input bridge external |
| 43 | XInput and gamepads | **Metadata:** requirement can be declared; mapping not implemented |
| 44 | Mouse acceleration and raw input | **External:** host/input runtime |
| 45 | TCP/IP, IPX/SPX and LAN | **Metadata:** network API requirement only; no IPX stack |
| 46 | Windows Firewall and game ports | **External:** no firewall or port changes |
| 47 | DirectPlay | **Not implemented:** OPlague reports this limitation |
| 48 | Save paths and user profiles | **Partial:** working directory recorded; save migration not implemented |
| 49 | CP1251 and legacy fonts | **Not implemented:** no code-page/font shim |
| 50 | OpenAL and DirectShow codecs | **Partial:** OpenAL requirement can be recorded; codec playback external |
| 51 | Windowed mode | **Metadata:** preference stored; runtime/game enforces it |
| 52 | Alt+Enter and minimize/restore | **External:** runtime/window manager |
| 53 | Windows 95/98/Me/2000/NT4 compatibility tabs | **Not implemented:** profile targets XP SP3 only |
| 54 | 256 colors and 640×480 compatibility | **Metadata + audit:** display values stored; no property-sheet shim |
| 55 | Disabling Luna themes | **Not implemented:** no Luna service or toggle |
| 56 | Patches and copy-protection fixes | **External:** operator-managed; no DRM bypass |
| 57 | Mods, texture packs and fan launchers | **External:** no mod installer |
| 58 | Page-file tuning and memory cleanup | **Partial:** telemetry only; no cleanup or page-file mutation |
| 59 | Administrator/user account selection | **External:** current host identity is used |
| 60 | 16:9/16:10 and widescreen HUD | **Audit only:** OPlague warns about non-4:3 modes; no binary patching |
| 61 | Overlay/hook conflicts | **Not implemented:** no automatic hook manipulation |
| 62 | Game logs and dxdiag diagnostics | **Partial:** structured DuckOS/OPlague reports; no universal game-log parser |
| 63 | Driver/DirectX installation order | **External:** no driver/runtime installer |
| 64 | Portable game folders | **Partial:** profile metadata is relocatable; registry/prefix portability not guaranteed |
| 65 | XP SP3 platform boundary | **Documented:** XP-era profile, not an XP kernel or XPDM implementation |
| 66 | Transparent launch chain | **Partial:** validate profile → inspect PE → plan → optional external Wine process |

### Cross-repository responsibilities

- **DuckOS:** shared versioned game profile, PE inspection, launch plan and optional dispatch to an already-installed Wine runtime.
- **OPlague:** read-only legacy graphics/display/audio/input/network findings plus device/driver evidence.
- **Pytyliki:** whole-host CPU/RAM/swap telemetry for the session.
- **Reaper:** validated, non-executing argv task contract for a trusted host executor.
- **VentuSample:** legacy audio sample-rate/sample-format/channel conversion planning.

A passing unit test validates only the code path under test. It does not demonstrate that a named commercial game runs or that DirectX, DirectSound, EAX, DirectInput, DirectPlay, SafeDisc, XPDM or the Windows registry is reproduced.
