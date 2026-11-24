# Mora Commons — единый магазин приложений DuckOS

**Product ID:** ivan-vhs.duckos.mora-commons  
**Catalog module:** `mora/commons-catalog.js`  
**Base application modules:** `mora/base-apps.js`  
**Maturity:** the store interface, 13 categories and 13 local-first application panels are implemented in the Mora browser shell. The earlier 15 product concepts remain catalogue specifications until their own modules are implemented.

## Purpose

Mora Commons is the unified application discovery and launch surface inside the Mora desktop environment for DuckOS. It groups software by task and provides search, category filtering, product details and favourites. Thirteen first-party base applications have a working local browser-shell module and can be launched directly from their store details.

Application brands are independent product identities. The platform name is not prepended to app names: **Deskline, Nuvault, Daymark, Lexora, Voxera, Wayline, Sumora, Pixora, Nexcode, Mnemo, Calcora, Paceforge and Trailmark** are standalone names.

## The 13 foundational categories

| Category | Purpose | First application |
|---|---|---|
| System | Workspace and system entry points | Deskline |
| Files | User-selected file cataloguing | Nuvault |
| Productivity | Tasks and daily planning | Daymark |
| Documents | Text creation and export | Lexora |
| Communication | Personal contacts | Voxera |
| Internet | Web bookmarks | Wayline |
| Finance | Personal income and expense ledger | Sumora |
| Multimedia | Selected image gallery | Pixora |
| Development | Structured data and developer utilities | Nexcode |
| Education | Study cards and recall | Mnemo |
| Utilities | Arithmetic and practical calculations | Calcora |
| Activity and health | Personal activity log | Paceforge |
| Travel | Manual trip and stop planning | Trailmark |

Each category has a stable ID in `MORA_COMMONS_CATEGORIES`. Each first application has a stable product ID, category, display metadata, description, capability list, search keywords and `runtime: "local_browser"` declaration in `MORA_COMMONS_APPS`.

## The first 13 applications

| Application | Working local behavior | Explicit boundary |
|---|---|---|
| **Deskline** | Quick links to Mora system tools and a factual overview of shell capabilities | Does not claim native hardware or kernel health |
| **Nuvault** | Select files and save a local index of names, MIME types, sizes and modification times | Does not copy or upload file contents |
| **Daymark** | Add tasks, mark them complete and remove entries | Browser-profile storage; no OS scheduler or cloud sync |
| **Lexora** | Edit text, count words and characters, save a draft and export TXT | Local browser storage; no cloud document service |
| **Voxera** | Create and remove local contact cards with a contact detail or note | Does not send email, SMS or messenger messages |
| **Wayline** | Save named HTTP/HTTPS bookmarks and open links in a separate tab | No browser engine, tracker blocker or private-network proxy |
| **Sumora** | Record income and expenses and calculate totals and balance | Manual ledger only; no bank connection, transfers or financial advice |
| **Pixora** | Preview selected images and retain a local metadata list | Does not upload or permanently copy original media |
| **Nexcode** | Validate and format JSON with local draft storage | Does not execute code, run a shell or contact a remote service |
| **Mnemo** | Create question/answer study cards and reveal answers | No learning analytics or cloud synchronization |
| **Calcora** | Safely parse arithmetic with parentheses, decimals and operator precedence | Arithmetic only; no JavaScript evaluation or arbitrary expression execution |
| **Paceforge** | Keep an activity log and calculate total recorded minutes | Personal log only, not a medical assessment or training prescription |
| **Trailmark** | Add, annotate and remove route stops in a manual trip plan | No GPS, live maps, route optimization or turn-by-turn navigation |

The modules reuse the Mora window manager, visual tokens, local browser profile and common interaction patterns. Collection-style apps use a per-app storage namespace and enforce a bounded record count. File pickers are user initiated; file metadata is stored rather than file contents.

## Catalogue inventory

The store currently contains **28 products**:

- **13 local-first base applications** listed above. Their panels can be opened from the store. Their maturity is `partial_browser_app_local_data` in the application registry.
- **15 earlier specialist product concepts**: TorqueSpec, Bore & Thread, GarageBay Log, Blade & Edge, RigCheck, IronCadence, RoundTimer Pro, RuckLedger, Grip & Hang, RecoveryLedger, DeadReckon, CampLoad, WatchDesk, MarginLine and ColdStart. These entries retain their descriptions, capability lists and product identities, but are still specifications rather than launched application modules.

The original specialist group remains searchable through its historical category aliases (`workshop`, `training`, `outdoors`, `business`) for compatibility with existing tests and references. The visible store taxonomy is the new set of 13 foundational categories.

## Implemented store behavior

- Search all catalogue products by name, subtitle, description, category, capabilities and keywords.
- Filter products by the 13 foundational categories.
- Open a detail view with the product purpose and capability list.
- Launch the 13 base modules from the product detail view.
- Save and remove favourites in the current browser profile.
- Cache the base module for offline use through the scoped Mora service worker.
- Preserve the same DuckOS black, white and yellow design tokens, responsive layout and keyboard-accessible controls.

The store catalogue and favourites are local to the browser profile. No sign-in, account sync, background telemetry or store-side data upload is introduced.

## Registry and runtime integration

The versioned `mora/apps.json` registry now includes the 13 app IDs and their Mora panel routes. `mora/app.js` merges their definitions into the existing window launcher and delegates panel rendering and initialization to `mora/base-apps.js`. The service worker caches `base-apps.js` with the Mora shell assets.

The modules are browser-local applications within Mora. They are not separate native DuckOS processes, signed OS packages, kernel services or boot-image payloads. The application registry status must not be interpreted as native package installation.

## Privacy, safety and maturity

- Local-first data remains in the current browser profile. Clearing site data can remove it.
- File selection is explicit and bounded. The file index stores metadata rather than reading or transmitting file contents.
- Wayline only renders saved links with `http:` or `https:` protocols.
- Nexcode parses JSON as data. Calcora uses a dedicated arithmetic parser and does not use `eval` or execute JavaScript.
- Sumora does not connect to financial accounts or initiate payments.
- Paceforge records user-entered activity only and does not give medical advice.
- Trailmark is a manual list, not a location service.
- No browser control is described as a native security boundary, permission broker, device service, network filter or system daemon.

Maturity values are evidence-based:
- `specified`: product role and capability scope are documented.
- `partial_browser_app_local_data`: a working subset is available within the Mora browser shell, with browser-profile storage and documented limitations.
- `implemented` or `verified` must not be assigned to a native capability until a real system integration and its acceptance tests exist.

## Accessibility and equal access

- Every user has equal access to every category and application.
- No gender-based categories, pricing, permissions, ranking or recommendations.
- Controls use visible labels, keyboard-operable buttons and readable status messages.
- Responsive layouts support narrow screens; reduced-motion behavior follows the Mora design system.
- Personalization follows explicit user choices, not inferred personal attributes.

## Validation

Run from the DuckOS repository root with Node.js 18 or newer:

```sh
npm test
```

The Mora Commons tests cover catalogue counts, category membership, all 13 launchable modules, safe arithmetic behavior, application registry wiring and offline service-worker caching. Passing browser-shell tests does not prove native package installation, kernel integration or OS-image inclusion.

## Naming and release readiness

All 13 product names are independent working brands and intentionally do not include “Mora” or “DuckOS”. Their trademark, domain, package-name and app-store availability have not been legally verified. Complete those checks before public release.

## Related architecture

- [Mora desktop and native integration](MORA_INTEGRATION.md)
- [Mora Design System](../MORA_DESIGN_SYSTEM.md)
- [Versioned Mora application registry](../mora/apps.json)
- [Preinstalled application specification](PREINSTALLED_APPLICATIONS.md)
