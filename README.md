# DuckOS

DuckOS is the operating-system project. **Mora** is its unified desktop environment: the home screen, application launcher, dock, window workspace and system control surface use one visual language and interaction model.

## Product direction

The product catalog now defines **20 first-party application concepts**: the original seven (Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify) plus 13 additions (Sestem, SetupUP, Orriganize, Abriganza, Olaab, Concrete Thump, Seu-Beu, Love-IL, Poi, Poi-2, Po-2, GameCharager and EXEdotEXE). The new names were supplied without role descriptions, so their first-scope meanings are documented as working product interpretations. Their Mora panels are partial browser-local tools, not native system services. Product boundaries and proposed integrations remain in the [preinstalled application specification](docs/PREINSTALLED_APPLICATIONS.md) and [versioned application catalog](catalogs/preinstalled-applications.v1.json). A product specification is not evidence that an app ships in a bootable image.

The separate DAK foundational package proposal contains the existing 15 system and everyday apps plus these 13 additions. It remains a design catalog: proposed API and capability identifiers must be registered before production packaging ([DAK base application catalog](catalogs/dak-base-applications.v1.yaml)).

## Federated source workspace

DuckOS keeps the four specialist Ivan-VHS projects as independent, commit-pinned Git submodules under `projects/`: [Pytyliki](https://github.com/Ivan-VHS/Pytyliki), [Reaper](https://github.com/Ivan-VHS/Reaper), [OPlague](https://github.com/Ivan-VHS/OPlague) and [VentuSample](https://github.com/Ivan-VHS/VentuSample). The checked-in registry records their source pins, licenses, roles and integration boundaries.

Clone the complete source workspace with `git clone --recurse-submodules https://github.com/Ivan-VHS/DuckOS.git`. For an existing checkout, run `python tools/federate_repositories.py sync`; it initializes only the commits pinned by DuckOS and refuses to overwrite local submodule changes. Imported projects are source checkouts, not automatically built, launched, loaded as drivers or claimed as boot-ready OS services. See [Repository federation](docs/REPOSITORY_FEDERATION.md).
## Mora desktop

**Start here:** [Mora desktop shell](mora/index.html).

Mora Amber is the default visual profile: walnut surfaces, amber-sand highlights, muted olive glass and a controlled vertical fold rhythm around a deep radial centre. Dark and Light remain available alternatives. The [Mora Design System](MORA_DESIGN_SYSTEM.md) supplies shared semantic tokens; the shell adds an installable web manifest, persistent Amber/Dark/Light theme and a scoped offline cache. It brings 20 application identities and the existing eight system tools, including Mora Commons and the fifteen-entry System Apps catalogue, into one workspace. The browser shell includes draggable windows, live clock, dashboard widgets, responsive layout, local preferences and keyboard navigation.

The system tools are:

- **Mora AI:** allowlisted local intent planning, readable action preview and explicit approval. No free-form shell execution or connected LLM is claimed.
- **Sentinel:** deny-by-default capability preferences for microphone, camera, location, files, network and clipboard. A native capability broker is still needed for process enforcement.
- **Restore:** versioned backup and restore of Mora preferences, with an A/B update workflow preview. This is not an OS-image updater or boot rollback.
- **Bridge:** local PE/ELF inspection in Mora; the native DuckBridge CLI discovers compatibility runtimes and prepares reviewable launch plans. It still does not launch targets.
- **Control:** persistent shell preferences for focus, reduced motion and a selectable resource profile. These do not change kernel scheduling or hardware power.
- **Proof:** local SHA-256 calculation. It does not verify C2PA manifests or signer identity.
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

The existing Python validation remains available:

```sh
python -m pip install jsonschema
python -m unittest discover -s tests -v
python tools/validate_app_catalog.py
python tools/validate_system_apps.py
```

The tests cover the browser-shell contracts and local helper logic; they do not prove kernel, driver, compositor or boot-image behavior.

## Release packaging and deployment planning

The native Python toolchain now provides deterministic, optionally Ed25519-signed component bundles, SHA-256 inventory and verification, plus non-destructive GPT A/B/recovery/data layout planning for USB, PXE, UEFI HTTP Boot/iPXE and cloud deployment targets.

See [Release and deployment tooling](docs/DEPLOYMENT.md). These commands produce a verified component archive or deployment plan; they do not yet build a bootable ISO/USB image, install to a physical disk, convert cloud images, or implement firmware Secure Boot and boot rollback.

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

## Fifteen system utilities and hardware bench contracts

The additional system utility catalogue is kept separate from the twenty first-party Mora application identities: [catalogue](catalogs/system-applications.v1.json), [JSON Schema](schemas/system-applications.v1.schema.json) and [runtime guide](docs/DESKTOP_RUNTIME.md). Mora exposes a System Apps entry with all fifteen identities. The host-side `duckos.desktop` package provides numbered launcher slots, exact-hash unsigned approvals, A/B image state transitions, board-profile interlocks and hash-chained audit/serial records.

Useful commands:

```sh
duckos desktop catalog
duckos desktop slots --state ~/.local/state/duckos/launcher.json list
duckos desktop package-verify ./candidate.pkg --trust-store ~/.local/state/duckos/trust.json
duckos desktop bench-profile ./bench/board-rev-a.json
```

The launcher currently creates structured requests rather than processes. Image activation and bench operation require explicit native adapters; the repository does not yet provide physical power switching, PCIe/NPU register access, probe sampling or UART device drivers.

## Windows application compatibility

DuckOS now includes a read-only PE32/PE32+ inspection engine, isolated prefix scaffolding and dry-run launch diagnostics. This is the first compatibility layer, not yet a Wine replacement; native Windows process execution remains blocked until the NT/Win32 runtime and graphics/audio backends exist. See [Windows compatibility](docs/WINDOWS_COMPATIBILITY.md) for the PE foundation and [DuckBridge](docs/DUCKBRIDGE.md) for Wine/Proton/CrossOver/Bottles discovery and non-executing command plans.

## Documentation

Start with the [DuckOS documentation index](docs/README.md). The [unified documentation and semantics standard](docs/UNIFIED_DOCUMENTATION_STANDARD.md) defines terminology, maturity states, runtime claims and evidence requirements.

- [Mora Commons unified application catalogue](docs/MORA_COMMONS.md)
- [Preinstalled application suite](docs/PREINSTALLED_APPLICATIONS.md)
- [Mora shell and native integration](docs/MORA_INTEGRATION.md)
- [DuckBridge runtime discovery and launch planning](docs/DUCKBRIDGE.md)
- [Mora Boost and OPlague gaming integration](docs/GAMING_PERFORMANCE_INTEGRATION.md)
- [Mora machine-readable system policy](mora/system-policy.json)
- [Fifteen system utilities and bench runtime](docs/DESKTOP_RUNTIME.md)
- [System utility catalogue](catalogs/system-applications.v1.json)

Implementation maturity, supported platforms and subsystem behavior must be stated from the current source, build configuration and tests.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve the authorship, contributions and license notices of existing contributors and dependencies.
