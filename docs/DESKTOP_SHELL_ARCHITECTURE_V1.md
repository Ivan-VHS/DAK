# DuckOS Desktop Architecture v1

**Status:** integrated implementation slice under review  
**Primary systems language:** Reaper  
**Host-native adapter:** Qt 6 Widgets / C++17  
**Design reference:** [Figma — 66 desktop material frames](https://www.figma.com/design/RWjphsEdITgECaS8G31o9H/Untitled?node-id=0-1)

## Scope and evidence

This document distinguishes shipped code from policy contracts and future kernel integration. A Reaper contract is executable policy on Reaper's reference runtime; it is not a privileged kernel service.

| Subsystem | Delivered by this change | Still required for a DuckOS kernel session |
|---|---|---|
| Design Foundation | Extended semantic tokens for glass/acrylic/matte surfaces, focus/hover/selected/disabled states and icon rules; six local Figma wallpaper representatives; persistent wallpaper selection in native Mora | Full shared native widget/material library, reusable icon pack, all 66 frames, GPU material compositor, cross-app token consumption |
| Native Shell Core | Native Mora Appearance page, local wallpaper loading, system-status page, existing Dock/navigation and host-native app windows | Kernel-owned desktop scene, compositor, renderer, input/event services and session startup |
| Window Engine | Reaper window/snap/workspace/monitor contracts; host-window grid, columns and focus arrangements for Mora app windows | Kernel Window Manager, native snap engine, real virtual desktops, cross-monitor ownership and persistence |
| System UI | Native host-session status panel; Reaper contracts for notification lifetime, Greeter transitions and explicit power confirmation | Notification daemon, Control Center service integration, authentication/Greeter, power manager and system dialogs |
| Applications | DABI64 manifest, lifecycle, capability-subset and bounded IPC contracts; existing ReaperWorkbench and local catalogue remain in place | Process manager, DABI64 loader/host ABI enforcement, IPC transport, signed package verifier and capability broker |
| Adaptive & Gaming | Input-device/controller/viewport/touch-target/game-profile contracts | Controller and touch event services, runtime mode switching, VRR/frame pacing, GPU and game-session integration |
| Production Quality | Reaper release-gate, accessibility, telemetry-sample and frame-budget contracts; CI executes the new suite with tree-walk and VM engines | Actual measurements on supported hardware, accessibility/platform audits, fault injection, integration evidence and release qualification |

## Figma material library

The Figma file contains 66 frames in six series. This change imports one representative frame from each series as a local PNG under mora/wallpapers:

- folds-of-light.png — frame 2:2
- copper-glass.png — frame 2:13
- quiet-dunes.png — frame 2:24
- light-fields.png — frame 2:35
- shape-study.png — frame 2:46
- amber-night.png — frame 2:57

The original artwork is retained as wallpaper. Mora applies a restrained dark readability scrim at render time; it does not recolor the image. The selected wallpaper is stored in host-local QSettings. Wallpaper selection is independent from the fixed Duck system palette (#080808, #FFFFFF, #FFD400). The other 60 frame variants are inventoried but are not yet bundled as separate selections.

## Native Mora behavior

The Qt 6 host application now exposes an Appearance page with six locally bundled wallpaper choices. Selecting one updates the desktop backdrop and persists appearance/wallpaperId. The page does not contact Figma or any remote asset host at runtime.

The Workspace page can arrange already-open Mora top-level windows in a two-column grid, up to three columns, or a focused maximized window. The host OS still owns window decorations, focus constraints, compositor and final placement. These arrangements are not a DuckOS kernel Window Manager.

The System page reports the current host-native boundary and links to Appearance/Workspace. It does not claim to provide a Greeter, kernel power control or service-backed notification center.

## Reaper modules and tests

The seven policy modules are:

- duckos/ui/appearance.rpr
- duckos/ui/shell.rpr
- duckos/ui/windowing.rpr
- duckos/ui/system.rpr
- duckos/ui/applications.rpr
- duckos/ui/adaptive.rpr
- duckos/ui/quality.rpr

desktop_shell_tests.rpr exercises these contracts. CI checks and runs the suite using both Reaper tree-walk and VM engines. Passing tests demonstrate deterministic policy behavior only; they do not demonstrate real input devices, running services, page tables, process creation, GPU submission or hardware telemetry.

## Follow-on kernel integration order

1. Define versioned Reaper↔native contracts and event ownership.
2. Bring up a kernel session with process lifecycle, memory isolation, IPC and capability enforcement.
3. Implement display discovery, framebuffer/GPU backend, compositor and input routing.
4. Implement Window Manager and virtual workspaces on top of the compositor.
5. Connect system UI, authentication, notifications and power services.
6. Launch application packages through DABI64 and the capability broker.
7. Qualify accessibility, performance, recovery, localization and security on Intel/AMD x86-64; preserve Elbrus as a separately validated compatibility target.

Do not promote any row from partial to delivered without source, tests and target evidence.
