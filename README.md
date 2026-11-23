# DuckOS

DuckOS is the operating-system project. **Mora** is its unified desktop environment: the home screen, application launcher, dock, window workspace and system control surface use one visual language and interaction model.

## Product direction

The default application suite contains seven first-party apps: Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. Their roles, data boundaries and proposed integrations remain defined by the [preinstalled application specification](docs/PREINSTALLED_APPLICATIONS.md) and the [versioned application catalog](catalogs/preinstalled-applications.v1.json). A product specification is not evidence that an app ships in a bootable image.

## Mora desktop

**Start here:** [Mora desktop shell](mora/index.html).

Mora uses the Amber drapery identity: folded ochre fabric around a dark radial work area, walnut/graphite surfaces and restrained amber highlights. The [Mora Design System](MORA_DESIGN_SYSTEM.md) supplies shared semantic tokens; the shell keeps the installable web manifest, persistent light/dark theme and scoped offline cache. It brings seven first-party apps, six system tools, Newsroom and Horizon into one workspace: 15 built-in entries in the same launcher and window model. The shell includes draggable windows, live clock, widgets, responsive layout, local preferences, keyboard navigation and reduced-motion support.

The system tools are:

- **Mora AI:** allowlisted local intent planning, readable action preview and explicit approval. No free-form shell execution or connected LLM is claimed.
- **Sentinel:** deny-by-default capability preferences for microphone, camera, location, files, network and clipboard. A native capability broker is still needed for process enforcement.
- **Restore:** versioned backup and restore of Mora preferences, with an A/B update workflow preview. This is not an OS-image updater or boot rollback.
- **Bridge:** local PE/ELF header inspection plus a documented native `os-run` route. The C++ tool can launch Windows programs through a separately installed Wine runtime on a POSIX host; the browser panel itself never executes files.
- **Control:** persistent shell preferences for focus, reduced motion and a selectable resource profile. These do not change kernel scheduling or hardware power.
- **Proof:** local SHA-256 calculation. It does not verify C2PA manifests or signer identity.

The **Вечерний курьер** panel reads the local RSS/Atom service at `127.0.0.1:8765`; it displays publisher-attributed headlines, and opens full stories on publisher sites. **Horizon** shows an implementation-maturity map, distinguishing working user-space services from partial native bring-up and future capabilities. The previous one-file [Mora seven-app prototype](prototype/mora-home.html) is retained as a reference implementation.

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

## Documentation

Start with the [DuckOS documentation index](docs/README.md). The [unified documentation and semantics standard](docs/UNIFIED_DOCUMENTATION_STANDARD.md) defines terminology, maturity states, runtime claims and evidence requirements.

- [Preinstalled application suite](docs/PREINSTALLED_APPLICATIONS.md)
- [Mora shell and native integration](docs/MORA_INTEGRATION.md)
- [Mora Amber design system](docs/MORA_AMBER_DESIGN_SYSTEM.md)
- [2026 feature and maturity matrix](docs/OS_2026_FEATURE_MATRIX.md)
- [Windows compatibility runtime](docs/WINDOWS_COMPATIBILITY.md)
- [Mora machine-readable system policy](mora/system-policy.json)

Implementation maturity, supported platforms and subsystem behavior must be stated from the current source, build configuration and tests. Architecture proposals and roadmap entries are not implementation evidence.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve the authorship, contributions and license notices of existing contributors and dependencies.

## Integrated native and compatibility work

The unified branch also consolidates the existing native platform and user-space service work:

- Limine x86-64 boot bring-up, initramfs builder and validator, wlroots/EGL desktop preview, a local staged package store, driver ABI headers and a fail-closed Bubblewrap host wrapper.
- Seven Python user-space services: Cockos (PipeWire routing), Kavun (window geometry), Ka-bon (shortcuts), Gloverty (palettes and contrast), Po (safe command registry), Illidia (session snapshots) and Unify (profiles/events).
- Newsroom RSS/Atom service with a fixed HTTPS source list, cache, bounded loopback API and feed safety limits.
- Windows compatibility utility under `native/compat`: PE32/PE32+ inspection, per-app Wine prefixes and argv-based `os-run` without shell interpolation.
- Reaper kernel/flow/trust/device contracts and the `duckos` build-manifest, image-layout and driver-module validators remain available alongside the native C/C++ work.

The browser Newsroom uses a fixed local endpoint. Start it from the repository root in another terminal:

```sh
PYTHONPATH=native/services python -m duckos_services news serve
```

For local desktop development use `python -m http.server 4173`, then open `http://127.0.0.1:4173/mora/`. The desktop remains usable without Newsroom; it reports when the local service is unavailable.

Build and test the host Windows compatibility utility:

```sh
make -C native compat-test
build/compat/os-run doctor
build/compat/os-run inspect ./application.exe
build/compat/os-run prefix create app --arch win64 --profile modern
build/compat/os-run run ./application.exe --prefix app --profile modern
```

Wine is an external host dependency; DXVK/VKD3D are not bundled. A Wine prefix is not a security sandbox, and kernel-mode anti-cheat is unsupported.

The native kernel is still an early boot foundation rather than a daily-driver OS: scheduler, process ABI, syscall layer, VFS, complete driver model and native GPU stack remain to be implemented. User-space service prototypes are not kernel modules. Signed A/B OS updates, kernel-enforced capabilities, C2PA signer verification, local model/NPU runtime, voice/XR input and hardware resource scheduling remain planned. The [2026 feature matrix](docs/OS_2026_FEATURE_MATRIX.md) and Horizon panel label these boundaries explicitly.
