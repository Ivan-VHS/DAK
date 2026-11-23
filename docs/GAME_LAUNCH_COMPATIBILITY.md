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
