# DuckOS

DuckOS is the operating-system project. **Mora** is its unified desktop environment: the home screen, application launcher, dock, window workspace and system control surface use one visual language and interaction model.

## Product direction

The default application suite contains seven first-party apps: Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. Their roles, data boundaries and proposed integrations remain defined by the [preinstalled application specification](docs/PREINSTALLED_APPLICATIONS.md) and the [versioned application catalog](catalogs/preinstalled-applications.v1.json). A product specification is not evidence that an app ships in a bootable image.

## Mora desktop

**Start here:** [Mora desktop shell](mora/index.html).

Mora retains the established indigo-to-rose sunset, layered hills, warm translucent panels and compact dock. The [Mora Design System](MORA_DESIGN_SYSTEM.md) supplies shared semantic tokens; the shell adds an installable web manifest, persistent dark/light theme and a scoped offline cache. It brings the seven application identities and six system tools into one workspace. The browser shell includes draggable windows, live clock, dashboard widgets, responsive layout, local preferences and keyboard navigation.

The system tools are:

- **Mora AI:** allowlisted local intent planning, readable action preview and explicit approval. No free-form shell execution or connected LLM is claimed.
- **Sentinel:** deny-by-default capability preferences for microphone, camera, location, files, network and clipboard. A native capability broker is still needed for process enforcement.
- **Restore:** versioned backup and restore of Mora preferences, with an A/B update workflow preview. This is not an OS-image updater or boot rollback.
- **Bridge:** local PE/ELF header inspection plus a host runtime manager for importing and launching real Windows PE/DOS applications through Windows native PE, Wine or DOSBox, with QEMU guest management.
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

The tests cover the browser-shell contracts, runtime package/integrity policy, argument-vector process creation and a real Windows-host PE process in the Windows CI job. They do not prove native DuckOS kernel, driver, compositor or boot-image behavior.

## Host executable runtime

The current real launcher is a host service, not a pretend browser execution button and not yet a kernel PE loader. Install the project in an editable Python environment:

```powershell
py -3 -m pip install -e .
duckos runtime list
duckos runtime bridge
```

Keep that terminal open. The command prints a random pairing token; paste it into Mora → Bridge. Serve the desktop from another terminal so the browser origin is an allowed loopback origin:

```powershell
py -m http.server 8000
```

Open `http://localhost:8000/mora/`. Select an EXE or ZIP game package in Bridge, import it, select its runtime and approve the launch. The pairing token stays only in the current Mora window's memory.

Examples for command-line import:

```powershell
duckos runtime import "C:\Games\Example\game.exe" --name "Example Game"
duckos runtime import "C:\Games\Example\game.zip" --entrypoint "Example\game.exe"
duckos runtime apps
duckos runtime launch APP_ID --adapter native-pe --allow-unisolated
```

On Windows, PE applications are created as real host processes through the Windows process API via Python's argument-vector process creation. They run with the current user's Windows permissions; this is not an AppContainer or DuckOS kernel sandbox. The first launch requires explicit approval for an unisolated host process.

On Linux/macOS/POSIX hosts, Windows PE requires an installed Wine runtime. On Linux, optional bubblewrap isolation restricts the filesystem view and can isolate the network namespace. DOS MZ/COM programs require DOSBox or DOSBox-X. QEMU can boot an existing registered guest disk; it does not run an arbitrary host EXE by itself. The guest disk defaults to snapshot mode and its virtual network adapter is disabled.

```sh
duckos runtime list
duckos runtime import ~/Games/game.zip --entrypoint "Game/game.exe"
duckos runtime launch APP_ID --adapter wine --allow-unisolated
duckos runtime vm-register windows-guest ~/VMs/windows.qcow2 --memory 8192 --cpus 4
duckos runtime vm-launch windows-guest --allow-unisolated
```

Install host dependencies using the package manager for the selected distribution. Wine is not bundled. DOSBox and QEMU are separate optional packages; unavailable runtimes are shown as unavailable rather than simulated.

DXVK can be installed into one managed Wine prefix only from an archive supplied by the user with its expected SHA-256 digest:

```sh
duckos runtime dxvk-install APP_ID dxvk.tar.gz --sha256 YOUR_64_CHARACTER_SHA256
```

DXVK covers Direct3D 9/10/11 to Vulkan. Direct3D 12 is **not** implemented by DXVK and currently has no vkd3d-proton adapter in this launcher. QEMU uses virtual VGA; GPU passthrough and gaming-grade 3D acceleration are not configured.

The host bridge binds only to `127.0.0.1`, uses a random bearer token, accepts local browser origins, and never accepts shell command strings. Imported packages are stored privately, checked against their per-file SHA-256 manifest before launch, and treated as untrusted. No Windows network sandbox is claimed; host-native Windows applications retain the current user's normal network permissions.

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
| Windows/DOS execution | Mora inspection plus host-native process manager, Wine and DOSBox adapters, managed imports and QEMU guest launcher | Native DuckOS kernel PE/Win32 ABI, cross-architecture user-mode translation, native graphics/audio stack and GPU passthrough |
| Declarative configuration | Versioned shell preference object | system-wide desired-state and package manager |
| Energy awareness | UI profile preference | CPU/GPU/NPU scheduler, thermal policy and VRR |

No browser control is described as a native kernel, driver, sandbox, updater or hardware implementation. In particular, PE inspection is not Windows program execution, settings snapshots are not atomic OS rollback, and SHA-256 does not authenticate a file's author.

## Documentation

Start with the [DuckOS documentation index](docs/README.md). The [unified documentation and semantics standard](docs/UNIFIED_DOCUMENTATION_STANDARD.md) defines terminology, maturity states, runtime claims and evidence requirements.

- [Preinstalled application suite](docs/PREINSTALLED_APPLICATIONS.md)
- [Mora shell and native integration](docs/MORA_INTEGRATION.md)
- [Mora machine-readable system policy](mora/system-policy.json)

Implementation maturity, supported platforms and subsystem behavior must be stated from the current source, build configuration and tests. Architecture proposals and roadmap entries are not implementation evidence.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve the authorship, contributions and license notices of existing contributors and dependencies.
