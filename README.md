# DuckOS

DuckOS is the operating-system project. **Mora** is its unified desktop environment: the home screen, application launcher, dock, window workspace and system control surface use one visual language and interaction model.

## Product direction

The default application suite contains seven first-party apps: Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. Their roles, data boundaries and proposed integrations remain defined by the [preinstalled application specification](docs/PREINSTALLED_APPLICATIONS.md) and the [versioned application catalog](catalogs/preinstalled-applications.v1.json). A product specification is not evidence that an app ships in a bootable image.

## Mora desktop

**Start here:** [Mora desktop shell](mora/index.html).

Mora retains the established indigo-to-rose sunset, layered hills, warm translucent panels and compact dock. The [Mora Design System](MORA_DESIGN_SYSTEM.md) supplies shared semantic tokens; the shell adds an installable web manifest, persistent dark/light theme and a scoped offline cache. It brings the seven application identities and seven system tools into one workspace. The browser shell includes draggable windows, live clock, dashboard widgets, responsive layout, local preferences and keyboard navigation.

The system tools are:

- **Mora AI:** allowlisted local intent planning, readable action preview and explicit approval. No free-form shell execution or connected LLM is claimed.
- **Sentinel:** deny-by-default capability preferences for microphone, camera, location, files, network and clipboard. A native capability broker is still needed for process enforcement.
- **Restore:** versioned backup and restore of Mora preferences, with an A/B update workflow preview. This is not an OS-image updater or boot rollback.
- **Bridge:** local PE/ELF header inspection. It does not load or launch executables.
- **Control:** persistent shell preferences for focus, reduced motion and a selectable resource profile. These do not change kernel scheduling or hardware power.
- **Proof:** local SHA-256 calculation. It does not verify C2PA manifests or signer identity.

The previous one-file [Mora seven-app prototype](prototype/mora-home.html) is retained as a reference implementation while the unified shell evolves.

## Visual system and offline support

The portable palette and geometry tokens are maintained in [mora/theme.json](mora/theme.json). The service worker is scoped to the Mora directory, caches only Mora shell assets and removes only older caches named with the `mora-shell-` prefix.

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
| Windows/Linux compatibility | PE/ELF header inspection | executable loader, Win32/NT, graphics/audio translation and launcher integration |
| Declarative configuration | Versioned shell preference object | system-wide desired-state and package manager |
| Energy awareness | UI profile preference | CPU/GPU/NPU scheduler, thermal policy and VRR |

No browser control is described as a native kernel, driver, sandbox, updater or hardware implementation. In particular, PE inspection is not Windows program execution, settings snapshots are not atomic OS rollback, and SHA-256 does not authenticate a file's author.

## Katyuhen ecosystem

**Katyuhen** unifies the project directory and cross-repository contracts for DuckOS/Mora, Reaper, OPlague, Pytyliki and VentuSample. Open the [Katyuhen hub in Mora](mora/index.html) or read the [ecosystem architecture](docs/KATYUHEN_ECOSYSTEM.md) and [versioned registry](ecosystem/katyuhen.v1.json).

## Documentation

Start with the [DuckOS documentation index](docs/README.md). The [unified documentation and semantics standard](docs/UNIFIED_DOCUMENTATION_STANDARD.md) defines terminology, maturity states, runtime claims and evidence requirements.

- [Preinstalled application suite](docs/PREINSTALLED_APPLICATIONS.md)
- [Mora shell and native integration](docs/MORA_INTEGRATION.md)
- [Mora machine-readable system policy](mora/system-policy.json)

Implementation maturity, supported platforms and subsystem behavior must be stated from the current source, build configuration and tests. Architecture proposals and roadmap entries are not implementation evidence.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve the authorship, contributions and license notices of existing contributors and dependencies.
