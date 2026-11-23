# Mora desktop shell and native system integration

## Role in DuckOS

DuckOS is the operating-system project; Mora is its unified desktop shell. All first-party applications and system tools use the same visual tokens, window behaviour, dock and workspace preferences. Mora is not a separate operating system and the HTML shell is not a native compositor.

The shell reuses the original indigo, rose and gold sunset wallpaper, layered hills, glass panels, explicit fine borders and compact dock. Existing app IDs remain stable.

## Shell components

| Surface | Responsibility | Current boundary |
|---|---|---|
| Desktop | Clock, status bar, app launcher, widgets and dock | Browser-hosted |
| App windows | Focus, move, close, running state and Escape handling | DOM window manager |
| Mora AI | Parse safe local intents, preview plan, request approval | Allowlisted rules, no model or shell |
| Sentinel | Show and store capability preferences | No native process enforcement |
| Restore | Save/restore shell settings and preview an update sequence | No OS image update/rollback |
| Bridge | Inspect PE/ELF headers; pair with host runtime-agent; import, launch and stop PE/DOS apps and QEMU guests | Real host processes on the OS running the agent; not a DuckOS kernel process ABI |
| Control | Persist focus, motion and resource-profile choices | No kernel/device scheduler |
| Proof | Calculate local SHA-256 | No signer or C2PA verification |

The seven original apps remain: Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify.

## Run and validate

Open **mora/index.html** directly in a modern browser. The desktop itself requires no network request. Some browser APIs such as Web Crypto may require a secure context.

Run **npm test** with Node.js 18 or newer. Contract tests check the static shell, registry and local policy helpers. They do not certify native OS operation or interaction with actual hardware.

## Intent actions and approval

Mora AI accepts only a bounded allowlist of local operations: open a built-in Mora panel, change the shell focus flag, select one of three shell resource profiles, or enable reduced motion. The proposed plan is rendered as text and is not executed until the user presses **Подтвердить план**.

Unsupported text is rejected. The agent cannot run a command line, interpolate a manifest entry point, install packages, edit arbitrary files, change system permissions or make network requests. The current rule engine is not a neural model.

A future agent service must return a typed action plan with versioned schemas, target identities, required capabilities, impact summaries, reversible operations, expiration and an audit record. A native approval broker must reject unrecognized actions and enforce confirmation at the process boundary.

## Permission and isolation model

Sentinel stores only six shell preferences: microphone, camera, location, personal files, network and clipboard. All begin denied. A switch changes the local Mora preference object; it does not grant or revoke permission in the browser, kernel or another process.

The native design must use deny-by-default capabilities, short-lived grants, per-app identity, path and device scoping, revocation, resource limits and audit events. Apps must run inside an actual sandbox before this UI can be represented as an enforcement surface.

## Recovery and atomic updates

Restore can save and restore the normalized Mora preference object using a versioned local snapshot. It does not back up user files, packages, boot metadata or OS partitions.

The future updater should download signed metadata, verify the complete payload, stage an inactive system slot, check capacity and compatibility, run health tests, switch boot selection atomically and preserve the previous slot until first boot is accepted. Recovery must work when an update is interrupted. This flow is currently displayed as an architecture preview only.

## Executable compatibility and host process manager

Bridge keeps its local PE/ELF header inspection and also pairs with the optional Python host service through a loopback-only authenticated API. The host agent imports PE/DOS executables and ZIP game packages into a private application store, records a per-file SHA-256 manifest, detects installed runtimes, creates processes with an argv vector and shell disabled, lists managed process IDs and supports termination.

The available execution paths are deliberately distinct:

- **Windows host:** Windows PE applications are passed to the Windows process-creation API via the host's native process manager. The Windows OS supplies the PE loader, Win32/NT APIs and installed graphics drivers. The child receives the current user's permissions. This is a real host process, not a DuckOS kernel PE/Win32 implementation or an AppContainer sandbox.
- **POSIX host:** Wine supplies the Windows API implementation for PE programs. On Linux, bubblewrap can provide an optional filesystem and network namespace boundary. Without it, launch requires explicit approval for an unisolated host process.
- **DOS:** DOSBox/DOSBox-X runs compatible MZ/COM/legacy DOS applications in an emulator. It is not a modern Windows runtime.
- **QEMU:** a registered Windows guest disk can be booted as a full virtual machine. Snapshot mode and disabled networking are defaults. The current QEMU profile uses virtual VGA and does not configure GPU passthrough.

The host agent accepts only loopback requests with a random bearer token. File imports are bounded, reject symbolic links/path traversal and are re-hashed before launch. Launch requires an explicit approval flag and uses an argument vector, never a shell command string. Windows-native runs are not OS-sandboxed; the current user's Windows permissions and network access remain available. A user must separately approve that unisolated execution.

Graphics translation remains a separate component. DXVK can be installed into a managed Wine prefix from a user-supplied archive after its expected SHA-256 is checked; it covers Direct3D 9/10/11 to Vulkan. Direct3D 12 needs vkd3d-proton and is not enabled. A Vulkan loader/device check is not a benchmark or proof that a game works. No anti-cheat bypass is included.

**Kernel boundary:** DuckOS still has no bootable native kernel process model, syscall ABI, PE image loader, Win32/NT implementation or kernel-enforced capability sandbox. The manager launches on the host OS running Mora. Cross-architecture Windows user-mode binary translation is not integrated. A QEMU guest may use translated guest CPUs inside its VM, but that does not turn QEMU into a host PE API layer.

## Provenance

Proof computes SHA-256 through Web Crypto when available. A digest can identify a file for comparison; it does not establish authorship, signer trust, edit history or C2PA provenance. Those require manifest parsing, signature verification, trusted certificate policy and explicit failure reporting.

## Installable web shell

The Mora shell publishes a web manifest for installation in supported browsers. Its service worker is limited to the `mora/` directory, precaches only the shell HTML, CSS, JavaScript, policy and icon files, and removes only obsolete caches with the `mora-shell-` prefix. It does not clear other applications' caches or cache cross-origin requests.

The shared palette and design constraints are defined by [Mora Design System](../MORA_DESIGN_SYSTEM.md) and [mora/theme.json](../mora/theme.json). The browser shell provides a persisted light/dark preference; native toolkit adapters must implement the same semantic tokens independently.

## Responsive workspace and accessibility

Mora supports a responsive browser layout and a reduced-motion preference. Its focus and power-profile controls affect only the shell presentation. Native display migration, XR, voice, gesture input, high-contrast profiles, VRR and hardware resource scheduling require dedicated services and accessibility testing.

## Data handling

All legacy photo, budget, game, compass, device and audio content remains clearly identified as fictional demo content. New settings are stored in the browser's local storage. Selected executable and provenance files are read locally by the page; the shell does not transmit them.

The local browser profile can be removed by clearing site data. The snapshot is a copy of Mora preferences only and should not be called a system restore point.

## External application integration

External projects may publish **integrations/mora/manifest.json** using **mora/app-manifest.schema.json**. The manifest describes an entry point; it does not install the app, confer trust or grant capabilities.

A native launcher must discover manifests only in trusted installation roots, validate the full schema, resolve paths without traversal, launch with an argument vector rather than a shell, show publisher and requested capabilities, require first-run approval and log failures. The current shell does not launch external processes.

## Maturity vocabulary

- **Implemented:** exercised by this repository's code within the browser shell.
- **Partial:** a bounded part works, but the complete service is absent.
- **Specified:** the contract and policy are documented but not enforced.
- **Planned:** implementation is not present.
- **Verified:** reserved for a feature with repeatable tests and evidence at the layer being claimed.

Never promote a feature to native/verified status because its UI panel exists.
