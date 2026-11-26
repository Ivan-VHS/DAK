# DAK Desktop — native host shell and browser demonstration

**Project:** Ivan-VHS/DAK  
**Architecture and engineering direction:** Ivan-VHS  
**DAK policy language:** Reaper  
**Native host UI adapter:** Qt 6 Widgets / C++17  
**Browser demo:** `desktop/demo/index.html`

## Architecture boundaries

DAK Desktop contains three separately verified layers:

1. **Native host desktop.** The Qt 6 application creates separate top-level windows, uses the host OS window manager for focus and input routing, and persists local shell preferences. It is a native application on the host OS, not a kernel-launched DAK session.
2. **Reaper policy layer.** `duckos/ui/shell_policy.rpr` validates workspace IDs, density profiles, window modes/actions, user-session scope, geometry, window counts, focus targets and versioned session snapshots. It does not allocate kernel surfaces, route hardware input or enforce process isolation.
3. **HTML demo.** `desktop/demo/index.html` is a dependency-free interactive visual reference. It offers navigation, app discovery, movable demo windows, local notes and workspace presets. It does not run host commands, install packages, open arbitrary filesystem paths or launch processes. Resource/device values are labelled demo data.

The x86_64 Stage 1 boot path remains unchanged. It does not launch Qt, browser content, application processes or a kernel compositor.

## Build the native host desktop

Requirements: CMake 3.21+, a C++17 compiler and Qt 6.4 Widgets.

```sh
cmake -S . -B build/dak-native -DCMAKE_BUILD_TYPE=Release -DDAK_BUILD_NATIVE_DESKTOP=ON
cmake --build build/dak-native --target dak_desktop_native --parallel
ctest --test-dir build/dak-native --output-on-failure -R dak-native-desktop-smoke
```

Run `build/dak-native/dak_desktop_native` (use the matching configuration output directory on Windows). The target is optional if Qt 6 Widgets is not installed; CMake reports the target as skipped rather than claiming a native build succeeded.

The native smoke test checks navigation and creation of separate top-level host windows. It does not test a DAK kernel compositor or target-OS input drivers.

## Run the HTML demo

Open `desktop/demo/index.html` directly in a modern browser. It has no external dependencies and works offline. Sample device/resource values are illustrative. The local note editor writes only to browser storage.

Keyboard: `Ctrl+K` opens a Reaper panel, `Ctrl+1/2/3` select Home/Apps/Workspaces, and `Escape` closes the top demo window.

## Reaper contracts

The Reaper policy is imported by `contract_tests.rpr` and exercised by tree-walk and VM CI jobs. It rejects unknown workspaces/profiles/actions, privileged machine scope, invalid window geometry, excess windows and invalid session snapshots.

## Authoring and design standard

This work applies the Ivan-VHS engineering style: explicit contracts, bounded inputs, deterministic policy functions, readable `craft` names, narrow responsibilities and evidence-based maturity claims. The interface uses Imperial Noir & Glass: near-black surfaces, restrained warm gold, monochrome typography, thin borders and reduced-motion support.

**Architecture and engineering credit: Ivan-VHS.** Toolkit and peer-project licenses remain separate and must be respected.
