# DuckOS — Mora desktop shell

Mora is the first desktop home screen for DuckOS: a quiet, glass-styled workspace with seven built-in app panels, desktop widgets and a dock.

## Current implementation

The initial shell is a self-contained HTML/CSS/JavaScript application under \`mora/\`.

- Sunset-over-hills wallpaper with an indigo, rose and gold palette.
- Live local clock and date, desktop status row and glass dock.
- Seven app launchers: Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify.
- Ka-bon spending and Unify device-status widgets that open their corresponding apps.
- Movable app windows, close controls, Escape-to-close and running indicators in the dock.
- Working demo controls: audio sliders and recording state, photo selection, expense bars, scenario switches, compass tabs, game progress and device toggles.
- Responsive desktop/tablet/mobile layout and reduced-motion support.

**Data boundary:** all balances, photos, progress values, device records, connection states and audio levels are fictional demo data. The frontend does not connect to payment accounts, external APIs, sensors, audio hardware or real device services.

## Run

Open \`mora/index.html\` directly in a modern browser. The shell has no external runtime dependencies, package installation step or network requirement.

Run the contract tests with Node.js 18 or newer:

\`\`\`sh
npm test
\`\`\`

The tests check the shell markup, seven-app registry, expected interactive controls and self-contained asset policy. They are not a substitute for browser automation or native OS testing.

## Project structure

| Path | Purpose |
|---|---|
| \`mora/index.html\` | Desktop structure and launch surfaces |
| \`mora/styles.css\` | Wallpaper, glass surfaces, app windows and responsive layout |
| \`mora/app.js\` | Clock, window manager, panels and demo interactions |
| \`mora/apps.json\` | Canonical seven-app and widget registry |
| \`mora/app-manifest.schema.json\` | External application manifest contract |
| \`docs/MORA_INTEGRATION.md\` | Architecture, security boundary and native integration requirements |
| \`tests/mora-contract.test.mjs\` | Dependency-free contract checks |

## Integration with the other Ivan-VHS projects

Reaper, Pytyliki, OPlague and VentuSample can each publish an \`integrations/mora/manifest.json\` file. It records the real project entry point and platform requirements. These manifests are opt-in declarations only: the current browser shell does not launch native processes.

A future native launcher must validate the manifest, resolve paths under a trusted installation root, start a process without shell interpolation and request explicit user approval before first launch. See [Mora integration contract](docs/MORA_INTEGRATION.md).

## Implementation status

| Capability | Maturity | Boundary |
|---|---|---|
| Desktop layout and seven built-in panels | \`implemented\` | Browser-hosted first shell |
| Clock, movable windows and Escape handling | \`implemented\` | Local frontend state |
| Dashboard widgets and dock indicators | \`implemented\` | Fictional data |
| External app manifest | \`specified\` | Schema and declarations only |
| Native process launcher / OS session manager | \`planned\` | Not present in this repository yet |
| Hardware, audio and payment integrations | \`not_applicable\` to this demo UI | No live access is attempted |

## Attribution

Project author/developer: **Ivan-VHS**. Existing contributor and third-party attributions must remain intact as the project grows.