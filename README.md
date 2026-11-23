# DuckOS

DuckOS is the operating-system project. **Mora** is its unified desktop environment: the home screen, application launcher, dock, window workspace and system control surface use one visual language and interaction model.

## Product direction

The default application suite contains seven first-party apps: Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. Their roles, data boundaries and proposed integrations remain defined by the [preinstalled application specification](docs/PREINSTALLED_APPLICATIONS.md) and the [versioned application catalog](catalogs/preinstalled-applications.v1.json). A product specification is not evidence that an app ships in a bootable image.

## Mora desktop

**Start here:** [Mora desktop shell](mora/index.html).

Mora Amber is the default visual profile: walnut surfaces, amber-sand highlights, muted olive glass and a controlled vertical fold rhythm around a deep radial centre. Dark and Light remain available alternatives. The [Mora Design System](MORA_DESIGN_SYSTEM.md) supplies shared semantic tokens; the shell adds an installable web manifest, persistent Amber/Dark/Light theme and a scoped offline cache. It brings the seven application identities and seven system tools into one workspace. The browser shell includes draggable windows, live clock, dashboard widgets, responsive layout, local preferences and keyboard navigation.

The shell also includes four virtual workspaces (Home, Studio, Play and System), movable/minimizable/maximizable windows and a Ctrl+K command palette with an explicit allowlist. The system settings panel contains the searchable 20-direction engineering matrix from the OS prototype; each row is marked partial, specified or planned rather than assigned a fictional completion percentage. These are browser-shell features backed by Reaper policy contracts, not a native compositor. See [Mora shell implementation](docs/MORA_SHELL.md).

The system tools are:

- **Mora AI:** allowlisted local intent planning, readable action preview and explicit approval. No free-form shell execution or connected LLM is claimed.
- **Sentinel:** deny-by-default capability preferences for microphone, camera, location, files, network and clipboard. A native capability broker is still needed for process enforcement.
- **Restore:** versioned backup and restore of Mora preferences, with an A/B update workflow preview. This is not an OS-image updater or boot rollback.
- **Bridge:** local PE/ELF inspection in Mora; the native DuckBridge CLI discovers runtimes and prepares reviewable plans. Its Illidia game launcher can start registered native games or invoke installed Wine-compatible runtimes.
- **Control:** persistent shell preferences for focus, reduced motion and a selectable resource profile. These do not change kernel scheduling or hardware power.
- **Proof:** local SHA-256 calculation. It does not verify C2PA manifests or signer identity.
- **Illidia:** local game library and CLI launcher with per-game Wine/Proton data, optional GameMode/MangoHud and structured process results. The Mora browser shell cannot launch host executables directly.
- **Mora Boost:** a single entry point to OPlague's Windows gaming lab for hardware snapshots, NVIDIA telemetry, Windows reliability events, reversible power sessions, frametime benchmarking and validated per-device profiles. It does not claim browser-side driver or kernel control.

The previous one-file [Mora seven-app prototype](prototype/mora-home.html) is retained as a reference implementation while the unified shell evolves.

## Visual system and offline support

The portable palette and geometry tokens are maintained in [mora/theme.json](mora/theme.json). The service worker is scoped to the Mora directory, caches only Mora shell assets and removes only older caches named with the `mora-shell-` prefix.

## Hardware inventory and driver audit

Collect a bounded, read-only snapshot of PCI/USB devices on Linux or present Plug-and-Play devices on Windows:

```sh
duckos hardware-inventory --output hardware-inventory.json
```

The versioned [hardware inventory contract](schemas/hardware-inventory.v1.schema.json) records detected bus IDs, driver binding state and privacy-preserving per-snapshot identity hashes. It does not install, update, enable or unload drivers. Use Reaper's read-only audit command to validate the snapshot and produce a diagnostic report; actual device support, signed driver packages and kernel enforcement remain native DuckOS work.

## Run and validate

Open **mora/index.html** in a modern browser. The shell has no external runtime dependencies. A secure browser context may be needed for Web Crypto file hashing.

Run the JavaScript contract tests with Node.js 18 or newer:

```sh
npm test
```

The Reaper policy source files are syntax-checked and exercised by the separate Reaper contract workflow. The browser shell modules can also be syntax-checked directly:

```sh
node --check mora/app.js
node --check mora/shell.js
```

The existing Python validation remains available:

```sh
python -m pip install jsonschema
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
```

The tests cover the browser-shell contracts and local helper logic; they do not prove kernel, driver, compositor or boot-image behavior.

## System architecture and maturity

The 2026 OS design directions are tracked as service contracts in [Mora system policy](mora/system-policy.json) and in the [Mora integration guide](docs/MORA_INTEGRATION.md).

| Area | Current Mora shell | Native DuckOS work still required |
|---|---|---|
| Intent UI and approvals | Limited allowlisted local actions with review | privileged action broker, audit and rollback |
| Local models and AI-native scheduling | Not connected | local inference runtime, NPU discovery and kernel scheduler |
| Immutable atomic updates | Local settings snapshot only | signed images, A/B slots, boot verification and recovery |
| Sandboxing and zero trust | Preferences only | per-process isolation, capability checks and device broker |
| Provenance | SHA-256 only | C2PA parsing, signer trust and signature validation |
| Adaptive workspace | Responsive browser layout, reduced motion | native compositor, display migration and XR runtime |
| Multimodal input | Keyboard, pointer and touch | speech, gesture and accessibility services |
| Windows/Linux compatibility | PE32/PE32+ header, section and import inspection; prefix scaffolding and CLI diagnostics | native executable loader, Win32/NT APIs, graphics/audio translation and launcher integration |
| Declarative configuration | Versioned shell preference object | system-wide desired-state and package manager |
| Energy awareness | UI profile preference | CPU/GPU/NPU scheduler, thermal policy and VRR |
| Hardware inventory | Read-only PCI/USB (Linux) and PnP (Windows) snapshot | PCI/USB/ACPI enumeration in kernel, signed driver installation and device recovery |

No browser control is described as a native kernel, driver, sandbox, updater or hardware implementation. In particular, PE inspection is not Windows program execution, settings snapshots are not atomic OS rollback, and SHA-256 does not authenticate a file's author.

## Windows application compatibility

DuckOS includes a read-only PE32/PE32+ inspection engine, isolated prefix scaffolding and structured runtime planning. **Illidia** adds a real local game library and can launch native matching-architecture ELF games or start installed Wine/Proton/CrossOver/Bottles runtimes for Windows games. It is not a Wine replacement: native NT/Win32 process execution, graphics/audio translation inside DuckOS and kernel-enforced sandboxing remain future work. See [Windows compatibility](docs/WINDOWS_COMPATIBILITY.md), [DuckBridge](docs/DUCKBRIDGE.md) and [Illidia](docs/ILLIDIA.md) for supported workflows and boundaries.

## Documentation

Start with the [DuckOS documentation index](docs/README.md). The [unified documentation and semantics standard](docs/UNIFIED_DOCUMENTATION_STANDARD.md) defines terminology, maturity states, runtime claims and evidence requirements.

- [Preinstalled application suite](docs/PREINSTALLED_APPLICATIONS.md)
- [Mora shell and native integration](docs/MORA_INTEGRATION.md)
- [DuckBridge runtime discovery and launch planning](docs/DUCKBRIDGE.md)
- [Illidia game library and launcher](docs/ILLIDIA.md)
- [Mora Boost and OPlague gaming integration](docs/GAMING_PERFORMANCE_INTEGRATION.md)
- [Mora machine-readable system policy](mora/system-policy.json)

Implementation maturity, supported platforms and subsystem behavior must be stated from the current source, build configuration and tests.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve the authorship, contributions and license notices of existing contributors and dependencies.
