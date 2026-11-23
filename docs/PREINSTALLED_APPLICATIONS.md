# DuckOS preinstalled application suite

**Catalog ID:** `duckos.preinstalled-applications.v1`  
**Catalog version:** 1.0  
**Maturity:** `specified`  
**Distribution intent:** seven default applications in the DuckOS product design

This document defines the intended roles, first-scope capabilities and cross-application workflows for 20 DuckOS first-party application concepts. The original seven remain the core suite; 13 additions expand the product catalog and Mora desktop. The names of the additions were provided without functional descriptions, so their initial roles are explicit working interpretations. This is a product specification, not evidence that the applications, services, cloud backends or operating-system integrations have been implemented or shipped.

The machine-readable inventory is maintained in [`preinstalled-applications.v1.json`](../catalogs/preinstalled-applications.v1.json). The separate DAK package-design catalog is [`dak-base-applications.v1.yaml`](../catalogs/dak-base-applications.v1.yaml). Shared terminology and maturity rules come from the [Ivan-VHS Unified Documentation and Semantics Standard](UNIFIED_DOCUMENTATION_STANDARD.md).

## 1. Suite overview

| Application | Domain | Product role |
|---|---|---|
| **Cockos** | Audio and recording | Capture, mix and improve application audio and voice recordings |
| **Kavun** | Photos and memories | Organize media into event- and place-based memory collections called “slices” |
| **Ka-bon** | Money and receipts | Record receipts, categorize spending and track recurring payments and shared budgets |
| **Gloverty** | Automation and gestures | Create no-code rules, shortcuts, gestures and macros |
| **Po** | Web browser | Browse with vertical tabs, reading mode, tracker protection and command-capable address bar |
| **Illidia** | Games | Manage games, saves, clips, achievements and focused play sessions |
| **Unify** | Device connectivity | Connect devices for clipboard, notifications, file transfer and state continuity |
| **Sestem** | System overview | Show documented shell status and subsystem maturity |
| **SetupUP** | First-run setup | Choose Mora theme and record completion of local setup |
| **Orriganize** | Projects and tasks | Keep lightweight local project and task lists |
| **Abriganza** | Archive inspection | Read selected archive name, format and size without extraction |
| **Olaab** | Media collections | Organize local album labels and text references to media |
| **Concrete Thump** | Rhythm planning | Create BPM and swing profiles for later manual use |
| **Seu-Beu** | Sharing review | Check recipient, selected content and retention before a hand-off |
| **Love-IL** | Private journal | Keep personal text notes in the local browser profile |
| **Poi** | Quick capture | Save short notes for later sorting |
| **Poi-2** | Knowledge cards | Collect short reference cards locally |
| **Po-2** | Route planning | Arrange manually entered stops without GPS |
| **GameCharager** | Game library | Track local game profiles and inspect selected executables |
| **EXEdotEXE** | Executable inspection | Inspect PE/ELF metadata and calculate a local SHA-256 digest |

The names are product working names. **Cockos** is flagged for a naming and trademark review before public distribution. No trademark clearance is asserted for Cockos or the other names by this specification.

## 2. Application specifications

### 2.1 Cockos — audio and recording

**Purpose:** a local audio workspace for recording and everyday sound control.

Initial capability scope:

- Per-application system volume mixer.
- Voice recorder with explicit microphone selection and recording controls.
- Simple multi-track recording and editing.
- Noise suppression for supported calls and microphone input paths.

Boundaries and design rules:

- Recording and microphone access require visible user control and permission.
- Recording state must remain obvious; stopping and saving must be predictable.
- Per-application volume control depends on the audio-session capabilities of the host platform.
- Noise suppression must be described as available only for supported input paths; do not imply universal call interception.
- The application is not specified as a full professional DAW or a hidden system-wide recorder.

### 2.2 Kavun — photos and memories

**Purpose:** a personal media library organized around events and places rather than only folders.

Initial capability scope:

- Gallery with event- and place-based groups called **slices**.
- Fast, non-destructive retouching.
- Story albums that combine selected media into a browsable event narrative.
- Search by visible image content, subject and scene.

Boundaries and design rules:

- A slice is a logical collection; it does not require moving or duplicating original files.
- Location and image-content indexing must be transparent and user-controllable.
- Private albums, metadata and face/person-related indexing require clear privacy controls.
- Retouching should preserve the original asset or provide a reversible edit history.

### 2.3 Ka-bon — money and receipts

**Purpose:** a personal and family spending ledger centered on receipts and recurring obligations.

Initial capability scope:

- Camera-based receipt capture and field extraction.
- Expense categorization and editable records.
- Subscription register and reminders for recurring payments.
- Shared family budget with clear member-level contribution and visibility rules.

Boundaries and design rules:

- OCR/extraction results are suggestions until the user confirms or edits them.
- The application tracks and reminds; this specification does not authorize automatic transfers, purchases or payment execution.
- Financial records and family membership data require access control, privacy protection and explicit sharing choices.
- Notifications must distinguish an estimated due date from a confirmed bank transaction.

### 2.4 Gloverty — automation and gestures

**Purpose:** a no-code automation workspace for user-defined routines.

Initial capability scope:

- Trigger/action rules in the form “when A happens, do B”.
- Touchpad and touchscreen gesture configuration.
- Global and application-specific keyboard shortcuts.
- No-code macros assembled from supported actions.

Boundaries and design rules:

- Each automation must expose its trigger, actions, scope and enabled state.
- Privileged, destructive or externally visible actions require clear permission and appropriate confirmation.
- Rules must have understandable failure behavior, loop prevention and a way to pause or disable them.
- A configured macro is not proof that every action is supported on every device.

### 2.5 Po — web browser

**Purpose:** a minimalist browser optimized for navigation and reading.

Initial capability scope:

- Vertical tab strip and tab grouping.
- Distraction-reduced reading mode.
- Tracker blocking with understandable controls and site exceptions.
- Smart address bar with navigation and supported browser commands.

Boundaries and design rules:

- Tracker protection must not be described as complete anonymity or a guarantee against all tracking.
- Site permissions, downloads, certificates and private browsing state must be understandable.
- Address-bar commands must be distinguishable from search queries and ordinary URLs.

### 2.6 Illidia — games

**Purpose:** a game library and companion workspace for play sessions.

Initial capability scope:

- Local game library and launch organization.
- Cloud-save support when a compatible provider is configured.
- Game clip recording and user-controlled sharing.
- Achievement profile.
- Do Not Disturb mode for the duration of a play session.

Boundaries and design rules:

- Cloud saves require a compatible provider/account and must expose sync status and conflict handling.
- Clip capture and sharing require explicit user controls and storage/permission indicators.
- Achievement data must distinguish locally observed information from provider-synchronized information.
- Do Not Disturb must be reversible and must not silently suppress critical system alerts.

### 2.7 Unify — device connectivity

**Purpose:** a trusted continuity layer between the user's devices.

Initial capability scope:

- Shared clipboard across paired devices.
- Forwarding selected phone notifications.
- One-touch file transfer.
- Synchronization of user-selected settings and browser tabs.
- Lost-device discovery for supported, paired devices.

Boundaries and design rules:

- Device pairing must be authenticated and revocable.
- Clipboard, notifications, files, tabs and settings require independently configurable sharing permissions.
- Transfers and synchronization must expose progress, errors and conflict behavior.
- Lost-device features depend on device availability and consent; they must not be described as guaranteed live location tracking.
- No background collection or sharing should be inferred from pairing alone.

### 2.8 Extended Mora application concepts

The following scope is intentionally modest because these 13 names arrived without product briefs. Each Mora panel reuses the existing window manager, theme tokens, toast feedback and profile storage. No new native process, filesystem, networking or audio privileges are implied.

| App | Implemented in the Mora panel | Boundary |
|---|---|---|
| Sestem | Project-status summary and shortcuts to system tools | Reads documented shell maturity; no native sensor collection |
| SetupUP | Theme selection and local setup-completion marker | Not an OS installer or bootloader configurator |
| Orriganize | Add and remove project/task text entries | Browser-profile storage only; no system scheduler or sync |
| Abriganza | Inspect selected archive filename, extension and size | No extraction, malware scanning or execution |
| Olaab | Local album and media-collection labels | Stores text references, not media files |
| Concrete Thump | BPM and swing controls with saved local profiles | No audio synthesis, recording or device routing |
| Seu-Beu | Manual checklist before sharing selected material | Not encryption, recipient authentication or OS security |
| Love-IL | Local personal text entries | No cloud sync or secure-vault claim |
| Poi | Quick text capture | No system-wide search or global shortcut |
| Poi-2 | Local knowledge-card list | No semantic index or external knowledge backend |
| Po-2 | Manually ordered route-stop list | No GPS, live map or navigation service |
| GameCharager | Local game list and read-only executable inspection | Does not launch games or install drivers |
| EXEdotEXE | PE/ELF inspection and SHA-256 report for a selected file | Not an antivirus, signature verifier or executable runtime |

Entries are namespaced by app in the Mora browser profile. Each text collection is limited to 100 entries and 160 characters per entry. File inspection is user initiated and remains local to the browser. The mora/apps.json registry and core.js app ID list are updated together so the launcher and panel router share one inventory.

## 3. Cross-application workflows

These workflows define intended product behavior and future integration contracts. They are not claims that the connectors or event bus are implemented.

| Workflow | Trigger and flow | Expected result |
|---|---|---|
| Weekly spending summary | Gloverty schedule/trigger → Ka-bon report action | Ka-bon prepares a weekly budget summary and presents it to the user |
| Event memory assembly | Cockos recording/media item → Kavun event slice | User-selected recordings and related media can be grouped into one event memory |
| Cross-device browser continuity | Po selected tabs → Unify → paired device | Selected tabs become available on the paired device |
| Cross-device game clips | Illidia selected clip → Unify → paired device | User-selected clip is transferred to the paired device |

### 3.1 Integration contract rules

Every workflow MUST eventually define:

- A stable event or action identifier and contract version.
- The sending application, receiving application and data direction.
- The minimum payload and any referenced files.
- Explicit opt-in, user consent and permission checks.
- Delivery, retry, cancellation and duplicate-handling behavior.
- A visible success or failure result.
- Data retention and privacy behavior.

The receiving application must validate incoming data as untrusted input. Cross-application integration must not bypass the receiving app's own permissions or confirmation steps.

### 3.2 Proposed interaction examples

- Gloverty may schedule a weekly trigger and invoke a Ka-bon summary action. Ka-bon remains responsible for selecting, calculating and presenting financial data.
- Cockos may offer a user-selected recording to Kavun. Kavun remains responsible for event grouping, media indexing and album presentation.
- Unify may transfer only the Po tabs and Illidia clips selected by the user. Pairing does not imply unrestricted access to either application's data.

## 4. Shared platform expectations

The seven applications should use consistent OS-level conventions:

- One application identity, icon, version and capability declaration per app.
- Consistent permission prompts and an accessible permissions/settings surface.
- Consistent notifications, background-activity indicators and error reporting.
- Predictable open, close, suspend and restore behavior.
- Keyboard navigation, screen-reader labels, scalable UI and reduced-motion support.
- Shared file-picker, export, sharing and confirmation patterns where appropriate.
- Clear offline behavior; cloud-dependent features must disclose when a network or account is required.
- No application may silently expand another application's access to user data.

A common application lifecycle should use the shared runtime vocabulary only where meaningful: `uninitialized`, `initializing`, `ready`, `running`, `degraded`, `stopping`, `stopped`, `failed` and `unknown`. App-specific states may extend this lifecycle when their transitions are documented.

## 5. Implementation and release tracking

The catalog maturity `specified` means the product roles and initial scope are written down. Each capability must receive its own maturity value when implementation work begins:

- `specified`: contract exists, implementation is not claimed.
- `planned`: accepted future work, not implemented.
- `partial`: an evidenced working subset exists.
- `implemented`: connected behavior exists in a real application workflow.
- `verified`: stated acceptance criteria passed on a named revision and environment.

Do not mark an entire application `implemented` because its shell, icon, launcher entry or placeholder window exists. Track each capability separately and cite source, tests and platform limits.

Before an application is described as preinstalled in a release, verify its package is included in the image/build, its launcher entry resolves, its dependencies are present and its first-run/permission behavior has been tested on the target image.

## 6. Naming and product identity

Names in this catalog are working product names. Cockos requires an explicit naming/legal review before public distribution due to the potential association with the existing Cockos/REAPER audio-software brand. Other names also require ordinary trademark, package-name, domain and platform-store checks before publication. This document does not make a legal availability determination.

## 7. Related documents

- [Unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md)
- [DuckOS documentation index](README.md)
- [Machine-readable application catalog](../catalogs/preinstalled-applications.v1.json)

## 8. Native Mora shell and application maturity

Mora is now a native Tk user-space application. The former browser prototype has been retired and its HTML, CSS, DOM-driven JavaScript and browser storage layer have been removed. The native launcher reads packaged JSON registry data and opens individual application panels without a WebView or embedded browser.

The following maturity values remain separate:

- `maturity_status: specified` describes the intended native DuckOS applications. A registry entry does not mean that a complete application package, system service or bootable distribution exists.
- `native_shell_status: implemented` describes the native Mora launcher, local preferences, selected diagnostic tools and system-panel entry points.
- Individual product features remain partial or specified until their own native services and persistent data layers are implemented and tested.

### Current native shell surfaces

| Area | Native behavior | Boundary |
|---|---|---|
| Launcher | Application grid, search, category filters and native app windows | Does not replace the host window manager |
| Control | Local focus, density, reduced-motion and preference profile | Does not change kernel scheduling, hardware power or global desktop settings |
| Sentinel | Persisted preference flags for listed capabilities | Does not grant or enforce process/device permissions |
| Restore | JSON export and import of normalized Mora settings | Not a system updater, image backup or boot rollback |
| Proof | SHA-256 for a selected local file | Does not verify a signer or prove authorship |
| Bridge | Read-only PE/ELF inspection | Does not execute targets or install compatibility runtimes |
| Duck Desktop | Opens the existing native maintenance utility | User-space tool, not the compositor |
| Reaper Studio | Opens the separate Reaper workbench process | No embedded language runtime or kernel privilege |
| Mora Commons | Local application catalogue from packaged JSON | Catalogue entries are not installed services |

### Product concepts awaiting native implementation

Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify remain product concepts with defined responsibilities and integration requirements. Their previous browser demonstration is not shipped as an alternate runtime. The native Mora shell may display their registry cards, but this does not imply that audio capture, image processing, finance storage, automation scheduling, browser tabs, game launching or device pairing are implemented.

The thirteen additional application identities are likewise catalogue entries with partial or specified maturity. Their panels must not claim access to devices, archives, audio engines, navigation sensors, system installation or network synchronization unless a dedicated native service has been delivered.

## 9. Unify transfer package specification

The versioned [`unify.transfer.v1`](UNIFY_TRANSFER_FORMAT_V1.md) JSON-file contract describes a user-mediated hand-off format for selected Po tabs, Illidia clips and selected settings. The format is validated by [`schemas/unify.transfer.v1.schema.json`](../schemas/unify.transfer.v1.schema.json).

The transfer schema is a specification and validation surface. The retired browser prototype's localStorage and IndexedDB behavior is not part of the native application, and authenticated pairing or live synchronization is not currently implemented.
