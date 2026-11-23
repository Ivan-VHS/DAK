# Mora desktop shell and application integration

## Scope

Mora is the DuckOS desktop home shell. Its first implementation is a self-contained HTML/CSS/JavaScript surface under \`mora/\`. It is intentionally independent of the native windowing backend so the desktop layout, app panels and interaction contract can be exercised before a native compositor or service layer exists.

The shell includes a live local clock/date, seven built-in app panels, two dashboard widgets, a glass dock, running-app indicators, draggable windows, close buttons and Escape-to-close behavior. The photo thumbnails, spending figures, game progress, compass bearings, device states and audio levels are explicitly illustrative; no personal data, sensors, payments, audio devices or hardware are accessed.

## Run locally

Open \`mora/index.html\` in a modern browser, or serve the repository root with any static file server. No network request, package install, build tool or runtime server is required by Mora itself.

Run its contract tests with Node.js 18 or newer:

\`\`\`sh
npm test
\`\`\`

These tests validate the static desktop contract and expected application controls. They do not replace browser-driven interaction testing or prove native OS integration.

## Built-in application registry

\`mora/apps.json\` is the canonical registry for the seven shell panels:

| ID | Application | Purpose |
|---|---|---|
| \`cockos\` | Cockos | Audio controls and a demonstration recording state |
| \`kavun\` | Kavun | Photo tile gallery |
| \`kabon\` | Ka-bon | Spending categories and today's summary |
| \`gloverty\` | Gloverty | Scenario toggles |
| \`po\` | Po | Compass direction tabs |
| \`illidia\` | Illidia | Game cards and progress |
| \`unify\` | Unify | Device list and demonstration connection toggles |

The Ka-bon and Unify dashboard widgets open the same application panels as their launcher tiles. The dock reflects currently open panels.

## External application manifests

Other Ivan-VHS projects may publish an \`integrations/mora/manifest.json\` file using \`mora/app-manifest.schema.json\` as the contract. A manifest describes the product's actual local entry point; it does not install the application, grant permissions or assert that an OS launcher is already connected.

The manifest keeps capability maturity separate from integration policy and verification status. Current manifests in the peer repositories are declarations only (\`maturity_status: specified\`, \`verification_status: not_run\`, \`integration_policy: opt_in\`).

### Launcher security requirements

A native Mora launcher MUST:

1. discover manifests only from trusted, installed application locations;
2. validate the complete manifest against the versioned schema;
3. resolve the entry point beneath the trusted installation root and reject path traversal;
4. invoke a process directly with an argument vector (never through a command shell);
5. show the publisher, executable path and requested capabilities before first launch;
6. require explicit operator confirmation and remember only an intentional trust decision;
7. report unavailable runtimes, rejected manifests and process failures without silently falling back to another command.

The current HTML shell does not launch external operating-system processes. Its external launch policy is therefore \`specified_not_enabled\`. Do not interpret the manifest's \`entrypoint\` as permission to execute code.

## Native integration boundary

The browser implementation is a visual and interaction prototype for the OS shell. A native DuckOS session manager will eventually own process creation, application lifecycle, focus, task switching, display scaling, audio routing, device discovery and persistent user settings. These services are not implemented by this frontend and must not be represented as live merely because a panel has a demo control.

## Contribution and attribution

Keep the seven app IDs stable once external consumers rely on them. Add schema changes through a new manifest version or a backward-compatible extension. Preserve existing contributors' authorship and third-party notices. Project author/developer: Ivan-VHS.