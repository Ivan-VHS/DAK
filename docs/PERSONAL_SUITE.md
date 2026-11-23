# Mora Personal Suite

**Project:** DuckOS  
**Desktop:** Mora  
**Catalog:** `duckos.personal-suite.v1`  
**Applications:** 15  
**Current maturity:** partial browser-shell implementation

Mora Personal Suite adds fifteen personal-life applications to the existing DuckOS desktop. Every application has its own launcher tile, Mora window, form and record list. The applications share one local profile and a versioned record store while retaining separate collections and workflows.

This is an extension of Mora, not a second desktop or a replacement for the seven existing DuckOS applications and seven system tools.

## Application map

| Area | Application | Local capability |
|---|---|---|
| Health and recovery | LuminaCycle | Cycle-date journal, self-reported energy and approximate calendar view |
| Health and recovery | NuraCalm | Mood journal, stress self-rating and optional breathing timer |
| Health and recovery | VerbaRest | Rest and break journal |
| Health and recovery | SoraGlow | Skin and hair routine notes and personal reaction log |
| Style and wardrobe | KoraCloset | Wardrobe catalogue with category, color and season tags |
| Style and wardrobe | MirraFit | Dated measurement and garment-fit notes |
| Style and wardrobe | TaliaPalette | Saved color swatches with HEX values |
| Style and wardrobe | ZaraLoom | Manual maker directory with material notes and links |
| Creativity and learning | BelaNotes | Local notes, tags and search |
| Creativity and learning | RinaCraft | Craft projects, materials and stages |
| Creativity and learning | OleaKitchen | Recipe book and ingredient lists |
| Creativity and learning | VedaBloom | Goals, reading and learning without streak penalties |
| Home and community | MilaNest | Household task list, due dates and manual assignment |
| Home and community | DariaLedger | Local income, expense and savings entries |
| Home and community | EldaCircle | Local meeting and book-club planner |

## Shared platform behavior

- Each application is a separate Mora window and uses existing shell controls and design tokens.
- One versioned profile contains separate record collections for all fifteen applications.
- Records can be exported and imported one application at a time using a versioned JSON format.
- User-triggered cross-app actions connect NuraCalm to VerbaRest and OleaKitchen to MilaNest. Other links open the related application.
- A shared record counter exposes counts only, not the contents of personal records.
- Form values are bounded and validated. User text is rendered as text rather than interpreted as HTML.
- No background jobs, contact uploads, messages, payments or network requests are created.

## Storage and privacy

The suite stores its state under `mora.personal-suite.v1` in the current browser profile. It is not synchronized to another device. Clearing site data can remove it.

Cycle records, body measurements, notes, financial entries and private social plans are sensitive. This browser module does **not** encrypt localStorage at rest and is not a substitute for an OS-level encrypted user vault. Use a protected operating-system account and browser profile. Exported files may contain private information; review them before sharing.

Imports are limited to the selected application's JSON export format and 1 MiB per file. Data is normalized, duplicate record identifiers are ignored, and each application is limited to 500 records.

## Implementation maturity

| Capability | Current browser implementation | Native DuckOS work still required |
|---|---|---|
| App launch | Mora windows and launcher tiles | Native packages and process identities |
| Shared profile | Browser localStorage | Encrypted user-data service and account integration |
| Cross-app workflows | Explicit same-window actions | Native event broker, typed IPC and capability checks |
| Data portability | Per-app JSON export/import | Signed backup metadata and OS recovery |
| Reminders | Visible records and in-app state | Native notification service and scheduler |
| Device continuity | Not connected | Authenticated pairing and conflict-safe sync |
| Health and finance providers | Not connected | Explicit consent, provider adapters and security review |

A launcher tile or browser panel is not a native application package. No kernel service, background scheduler, cloud account, encryption-at-rest guarantee, medical advice, banking connection, marketplace validation or real-time device sync is claimed.

## Verification

Run the Mora test suite with Node.js 18 or newer:

    npm test

The Personal Suite contract tests cover stable application identifiers, catalogue and launcher consistency, privacy boundaries, state normalization, shared counters and offline asset registration. Passing these tests verifies the browser-shell contract only; it does not certify a native DuckOS image.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve the authorship, contributions and license notices of existing contributors and dependencies.
