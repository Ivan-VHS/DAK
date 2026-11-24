# Mora desktop shell and native system integration

## Role in DuckOS

DuckOS is the operating-system project; Mora is its unified desktop shell. All first-party applications and system tools use the same visual tokens, window behaviour, dock and workspace preferences. Mora is not a separate operating system and the HTML shell is not a native compositor.

Mora uses one fixed DuckOS profile: near-black structure, white content and duck-yellow action/selection, with a deep radial workspace centre and restrained vertical folds. No Amber, Dark or Light theme switching is exposed. The Газета app contains a deliberately scoped newsprint surface; it does not recolor the desktop or other applications.

## Shell components

| Surface | Responsibility | Current boundary |
|---|---|---|
| Desktop | Clock, status bar, app launcher, widgets and dock | Browser-hosted |
| App windows | Focus, move, close, running state and Escape handling | DOM window manager |
| Mora AI | Parse safe local intents, preview plan, request approval | Allowlisted rules, no model or shell |
| Sentinel | Show and store capability preferences | No native process enforcement |
| Restore | Save/restore shell settings and preview an update sequence | No OS image update/rollback |
| Bridge | Inspect PE/ELF file headers and architecture | No executable loading |
| Control | Persist focus, motion and resource-profile choices | No kernel/device scheduler |
| Proof | Calculate local SHA-256 | No signer or C2PA verification |
| Mora Boost | Link to OPlague gaming performance workbench | Browser catalog only; host telemetry and reversible power sessions run in OPlague, not in the page |
| Газета | Search topic-based news, display source metadata and save article bookmarks | Browser fetch to GDELT DOC 2.0; no native service, editorial verification or synchronized account |

The seven original apps remain: Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify. Газета is an eighth core launcher app. Mora Boost is an additional system tool that opens the native OPlague gaming workbench; it does not make the browser a privileged driver or telemetry service.

Mora also contains 13 extended first-party app concepts: Sestem, SetupUP, Orriganize, Abriganza, Olaab, Concrete Thump, Seu-Beu, Love-IL, Poi, Poi-2, Po-2, GameCharager and EXEdotEXE. Their initial roles are working interpretations because the names were supplied without briefs. The panels provide bounded local browser interactions, share the existing window manager and profile storage, and do not claim native service implementations.

## Газета news feed

Газета is a separate newspaper-style app in the Mora launcher and dock. It requests GDELT DOC 2.0 JSON ArtList results for six sections (Ukraine, Dnipro, World, Technology, Economy and Science), limits results to the last 24 hours, accepts a bounded free-text query, and opens only validated HTTPS publisher links. GDELT documents JSON output, browser CORS support and search across 65 translated source languages ([GDELT DOC 2.0 API](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)).

The app fetches on open, section change, search or explicit refresh; it applies a 5.5-second client request interval and a 15-second timeout. It retains up to eight recent result sets and 100 article bookmarks in namespaced `localStorage`. It does not scrape full article bodies, assert source credibility, fact-check claims or synchronize user data. An external GDELT request reveals the selected query and ordinary connection metadata to that provider.

The native DAK `dak.news-feed.v1` service is only proposed in the design catalog. The implemented feature is the Mora browser app and its local state; no native provider or operating-system feed daemon is claimed. Full provider, privacy and validation details are in [the Газета implementation note](NEWS_FEED.md).

## Run and validate

Open **mora/index.html** directly in a modern browser. The static shell assets are local, but opening or refreshing Газета requires network access to GDELT. Some browser APIs such as Web Crypto may require a secure context.

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

## Compatibility boundary

Bridge reads a user-selected local file and inspects PE or ELF headers without executing it or uploading it. Detecting an x86/x64/ARM64 machine value is not evidence that the corresponding ABI or graphics stack can run.

A native compatibility environment still needs PE loading, Win32/NT services, process and memory mapping, API translation, DirectX/Vulkan/OpenGL support, audio, input, prefixes, launchers and a clear anti-cheat compatibility policy. Anti-cheat bypass is not part of this design.

## Provenance

Proof computes SHA-256 through Web Crypto when available. A digest can identify a file for comparison; it does not establish authorship, signer trust, edit history or C2PA provenance. Those require manifest parsing, signature verification, trusted certificate policy and explicit failure reporting.

## Installable web shell

The Mora shell publishes a web manifest for installation in supported browsers. Its service worker is limited to the `mora/` directory, precaches only the shell HTML, CSS, JavaScript (including `news.js` and `news-core.js`), catalogue, policy and icon files, and removes only obsolete caches with the `mora-shell-` prefix. It does not clear other applications' caches or cache cross-origin requests.

The shared palette and design constraints are defined by [Mora Design System](../MORA_DESIGN_SYSTEM.md) and [mora/theme.json](../mora/theme.json). The browser shell provides a persisted light/dark preference; native toolkit adapters must implement the same semantic tokens independently.

## Responsive workspace and accessibility

Mora supports a responsive browser layout and a reduced-motion preference. Its focus and power-profile controls affect only the shell presentation. Native display migration, XR, voice, gesture input, high-contrast profiles, VRR and hardware resource scheduling require dedicated services and accessibility testing.

## Data handling

All legacy photo, budget, game, compass, device and audio content remains clearly identified as fictional demo content. New settings, news result caches and bookmarks are stored in the browser's local storage. The news provider receives user-triggered search requests; cached stories and bookmarks remain local and are not synchronized. Selected executable and provenance files are read locally by the page; the shell does not transmit them.

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


## Duck Desktop integration

Mora exposes Duck Desktop as a system tool, but the browser panel is informational. It gives the user the `duckos desktop gui` launch command and does not request browser access to local directories or claim to manage host processes. The native utility is installed with the DuckOS Python package and owns desktop auditing, safe Inbox moves and reversible current-user startup operations.

Its boundaries and CLI are documented in [Duck Desktop optimization](DESKTOP_OPTIMIZATION.md). It does not replace the native compositor, window manager or system service manager.
