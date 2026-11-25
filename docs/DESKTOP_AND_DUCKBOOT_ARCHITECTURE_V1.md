# DuckOS native desktop and DuckBoot architecture v1

**Status:** architecture specification; implementation not yet delivered.  
**Target:** x86_64 Intel/AMD first; Elbrus remains a separately qualified compatibility target.  
**Ownership:** DuckOS owns the native desktop, session manager, policy and boot orchestration. Reaper is the canonical system-policy and service language.  
**Current boot provider:** pinned Limine v12.11.1, BIOS/UEFI, Stage 1 only.

## 1. Executive decision

DuckOS will have one native desktop stack with selectable workflow profiles and one boot-management layer with independently qualified backend adapters.

This is deliberately not a plan to bundle twenty unrelated desktop environments or twenty bootloaders into the kernel. The desktop profiles below reproduce interaction models and layout choices on shared DuckOS services; they are not ports, binaries, protocol-compatible sessions or claims of upstream KDE/GNOME/etc. support. The boot list is a compatibility catalogue: some entries are complete bootloaders, while others are firmware paths, image formats, chainload targets or subordinate trust stages. Each adapter must declare which operations it can really perform.

The two products are:

- **Duck Desktop** — native session, display protocol, compositor, window manager, shell, panels, launcher, settings, accessibility and app integration.
- **DuckBoot** — boot-entry discovery, validation, selection, chainloading, recovery and backend adapters. The native boot manager must not replace the known-good Limine path until its own gates pass.

Mora remains the browser-hosted shell and design reference during the transition. Its current windows and preferences are not native compositor, kernel, process isolation or hardware evidence.

## 2. Current baseline and non-negotiable boundaries

At the reviewed baseline (2026-11-25):

- DuckOS has a QEMU-tested x86_64 Stage 1 image using Limine v12.11.1 for BIOS and UEFI.
- The kernel validates Boot Info v1, uses the validated firmware memory map, allocates and clears one early 4 KiB frame through HHDM, prints DUCKOS_BOOT_OK stage=1 and halts.
- Reaper already contains reference-runtime policies for graphics descriptors, display geometry, frame budgets, window states, accessibility profiles, boot sequencing, memory, scheduling, IPC, capabilities and service policies.
- Mora is a separate browser application. It has a DOM window manager, app registry, local preferences and reduced-motion behavior.
- Page-table management, interrupts/timers, process execution, syscall enforcement, device discovery, GPU submission, audio, filesystem-backed user sessions, native compositor and native settings applications are not yet delivered.

A Reaper policy result is not a privileged operation. A browser setting is not a system permission. A registry entry is not a native application. A QEMU Stage 1 boot is not a usable desktop OS. These distinctions remain mandatory in all status reports.

## 3. Native desktop architecture

### 3.1 Service topology

The target runtime is split into explicit services. A service may begin as an in-kernel subsystem for the earliest milestone, but its interface and authority must remain separable so it can move to an isolated process after the process and IPC foundations exist.

| Component | Responsibility | Authority |
|---|---|---|
| DuckSession | Login/session lifecycle, active profile, display topology and session recovery | Owns session transitions; no raw device access |
| DuckDisplay | Display discovery, output modes, buffer admission, presentation and display ownership | Display capability only |
| DuckCompositor | Scene graph, composition, damage tracking, frame pacing, scaling and software fallback | Receives surfaces; cannot inspect arbitrary app memory |
| DuckWindow | Configure/ack lifecycle, placement, stacking/tiling, focus, workspaces and decorations | Window-management capability |
| DuckInput | Keyboard, pointer, touch, tablet, hotplug and input routing | Input-device capability; focused-client routing by default |
| DuckShell | Desktop background, panel, dock, launcher, status area, task switcher and notifications | Shell-owned surfaces and approved system actions |
| DuckSettings | Theme, monitor, input, audio, accessibility, session and boot preferences | Typed settings APIs; no direct disk or firmware writes |
| DuckFiles | Native file browsing, mounts, user paths and file-operation progress | Per-mount and per-path capabilities |
| DuckPortal | Consent-mediated screen capture, file chooser, clipboard, notifications and device handoff | Short-lived scoped grants |
| DuckTheme | Semantic tokens, icons, fonts, density, contrast and motion | Read-only theme packages |
| DuckSessionProfiles | Validates and applies desktop behavior profiles | Profile data only; no executable plugin authority |
| DuckLogind / Power | Lock, suspend, reboot, shutdown and power-state coordination | Explicit power capability |

No panel, widget, theme or profile is allowed to run arbitrary Reaper source, load a driver or gain device access. Extensions are data-driven first; native executable extensions require signed packages, declared capabilities, resource ceilings and isolation tests.

### 3.2 Display protocol: Duck Display Protocol (DDP) v1

DDP is the native client/compositor contract. It is a new DuckOS-owned protocol, not a claim of Wayland compatibility.

Required objects:

- Display and output: stable identifier, physical dimensions, logical dimensions, scale, transform, refresh capability and hotplug generation.
- Surface: opaque client-owned handle, format, dimensions, buffer generation and lifecycle state.
- Configure transaction: proposed geometry/state, serial, deadline and client acknowledgement.
- Presentation: damage region, acquire/release fence where supported, frame sequence and presentation timestamp.
- Input event: device class, event sequence, monotonic timestamp, seat, focus target and normalized coordinates/key data.
- Clipboard and drag/drop: typed MIME allowlist, bounded payload, ownership and explicit lifetime.
- Portal request: caller identity, purpose, requested scope, expiration, decision and audit reference.

State flow: create → configure → acknowledge → attach buffer → commit → present → release → destroy. Stale serials, reused handles, invalid dimensions, integer overflow, oversized buffers and invalid state transitions are rejected before access to buffer memory.

DDP security rules:

1. A client can access only its own surfaces and explicitly granted shared buffers.
2. Input goes to the focused target unless an explicit system gesture or accessibility route applies.
3. Global keyboard observation, arbitrary screen capture, clipboard scraping and input injection are denied by default.
4. Screen sharing/capture is a portal with a visible indicator, scoped target, revocation and audit event.
5. Drag/drop and clipboard data are untrusted input and pass bounded decoding and validation.
6. The compositor does not execute client-supplied shaders or parse unbounded data in interrupt context.
7. Client death, output removal, lost fences and device reset have defined cleanup and timeout paths.

### 3.3 Rendering pipeline

The initial implementation order is:

1. Firmware framebuffer console and serial diagnostics remain the recovery surface.
2. Native input discovery and a bounded event queue are added after interrupt/timer foundations.
3. A software compositor renders one output and a small fixed window set into a known framebuffer format.
4. Window geometry, focus, stacking, tiled layout, damage regions and frame pacing are implemented against deterministic test buffers.
5. GPU acceleration is an optional backend behind the same presentation contract; it is never required to boot or recover.
6. Multi-monitor, variable refresh, HDR, color management, hardware cursors and GPU reset recovery are added only after baseline correctness.

Software rendering is the mandatory fallback. An unsupported GPU, missing firmware mode or driver crash must not make the boot menu or recovery shell unusable. Frame-budget policies are admission hints; measured frame time is the evidence.

### 3.4 Window and session model

A window has a stable ID, owning process identity, surface handle, role, title, app ID, geometry, state, workspace, output, focus eligibility and capability set. The state machine is:

created → configured → mapped → focused/unfocused ↔ minimized/maximized/tiled/fullscreen → closing → destroyed.

Invalid transitions are rejected. Window title, app ID and role are untrusted metadata. Focus is not an authorization grant. Fullscreen and always-on-top are requests subject to policy.

Session profiles change layout, shortcuts, panel arrangement, launcher behavior, tiling rules, workspace model and visual density. They do not swap kernel drivers, replace the compositor ABI or unload the active session manager. A profile switch is validated, written as a versioned snapshot, applied transactionally and rolled back if required services fail.

Running applications remain alive across a profile switch only when their window roles and DDP versions are compatible. Otherwise DuckSession asks them to save state and restart; it never silently kills work.

### 3.5 Twenty desktop workflow profiles

All profiles use the same DuckDisplay/DDP/DuckCompositor/DuckWindow/DuckShell stack. Profile names identify the workflow being approximated, not upstream source code or binary compatibility.

| # | Profile ID | Inspired workflow | Native Duck behavior |
|---:|---|---|---|
| 1 | plasma-workspace | KDE Plasma | Configurable panels, widgets, activities, global shortcuts and rich settings |
| 2 | gnome-overview | GNOME | Overview-first navigation, search-centric launcher and focused workspaces |
| 3 | xfce-classic | Xfce | Low-overhead classic panel/menu, minimal animation and conservative effects |
| 4 | cinnamon-traditional | Cinnamon | Familiar menu, task list, tray and desktop applets |
| 5 | lxqt-light | LXQt | Compact Qt-oriented visual density and low-resource defaults |
| 6 | budgie-clean | Budgie | Restrained panel, notification sidebar and simple app navigation |
| 7 | cosmic-dock | COSMIC | Dock, keyboard search, tiling toggle and independent workspace controls |
| 8 | mate-dual-panel | MATE | Traditional dual-panel layout, menu hierarchy and simple window controls |
| 9 | deepin-control | Deepin DDE | Full-height launcher and centralized visual control center |
| 10 | pantheon-focus | Pantheon | Focused top bar, dock and opinionated application navigation |
| 11 | ukui-classic | UKUI | Traditional desktop layout and compact settings surfaces |
| 12 | enlightenment-flex | Enlightenment | Keyboard-driven virtual desktops, edge actions and configurable effects |
| 13 | trinity-retro | Trinity Desktop | Dense classic menus, taskbar and low-motion behavior |
| 14 | lxde-minimal | LXDE | Minimal panel, low memory footprint and simple stacking windows |
| 15 | moksha-modular | Moksha | Modular shelves, gadgets and workspace-oriented controls |
| 16 | lumina-clean | Lumina | Lightweight, straightforward desktop and file-first navigation |
| 17 | lomiri-touch | Lomiri | Touch-first shell, edge navigation and adaptive application surfaces |
| 18 | unity-dash | Unity | Searchable dash, global navigation and persistent launcher |
| 19 | hyprland-dynamic | Hyprland | Dynamic tiling, configurable gestures and animated transitions |
| 20 | sway-i3-tiling | Sway/i3 | Keyboard-first tiling tree, explicit workspaces and deterministic focus |

Profile schema requirements: stable ID, schema version, display name, base profile, panel layout, launcher mode, window policy, workspace policy, shortcut map, motion policy, density, accessibility overrides and required Duck services. Profiles cannot declare arbitrary executables, URLs, scripts, drivers or filesystem paths.

Profile compatibility is versioned. Unknown keys are rejected or retained only in a bounded, explicitly marked extension bag; they are never interpreted as commands. Each profile ships with a minimal-resources fallback and a reset-to-default operation.

### 3.6 Visual and accessibility contract

The native default follows the current Duck visual direction: near-black canvas and surfaces, one semantic gold accent, restrained glass/depth, clear borders and status colors reserved for state. All colors are semantic tokens rather than hardcoded widget values. Native and Mora surfaces share token names and behavior, not an implementation runtime.

Required behavior:

- keyboard-only operation for every core task;
- visible focus and deterministic focus restoration;
- high-DPI scaling without clipped controls;
- text scaling and contrast modes;
- reduced motion removes nonessential spatial animation while preserving state feedback;
- touch targets and pointer targets meet declared minimum sizes;
- screen-reader names, roles, values and state-change announcements;
- no color-only status;
- localization with dynamic text expansion;
- no network dependency for login, desktop startup, file browsing or settings;
- no cloud fonts, proprietary CDN or remote theme requirement.

### 3.7 Native GUI application contract

First-party applications use a versioned Duck UI API over DDP, typed system portals and shared semantic tokens. A GUI app cannot call a kernel function by name or bypass DuckPortal. Each app manifest declares app ID, ABI, DDP version, required capabilities, resource limits, localized metadata and recovery behavior.

Native application work begins only after process address spaces, syscall validation, handles, IPC, filesystem paths, capability enforcement and application lifecycle are in place.

## 4. DuckBoot architecture

### 4.1 Boot phases

DuckBoot is a boot manager and adapter orchestrator, not a replacement for firmware or every upstream loader.

Target sequence:

firmware → selected trusted first-stage loader → DuckBoot menu/policy → validated kernel + initramfs + command line → Boot Info handoff → DuckOS kernel → verified startup services → desktop session.

On the current branch, Limine directly loads the experimental kernel and DuckBoot does not yet execute. The first DuckBoot milestone is therefore an offline catalog, parser, inspection and dry-run planner, not a new firmware executable.

DuckBoot modules:

- DuckBoot Core: entry model, policy, state machine and selection logic.
- DuckBoot Discover: enumerate firmware entries, ESP paths and known loader configuration locations without modifying them.
- DuckBoot Parse: bounded readers for supported entry formats.
- DuckBoot Verify: kernel/initramfs hashes, signed manifest and trust metadata; no caller-supplied boolean is accepted as proof.
- DuckBoot Menu: keyboard-accessible boot selection and recovery.
- DuckBoot Chain: explicit chainload requests to firmware/other loaders where the platform permits.
- DuckBoot Install: separate, explicit, confirmed installer; disabled until write safety and rollback gates pass.
- DuckBoot Recovery: known-good entry, rescue payload, diagnostic export and rollback.
- DuckBoot Adapters: feature-negotiated providers with exact format and firmware limitations.

### 4.2 Common boot-entry contract

A boot entry contains: stable ID, source adapter, firmware type, architecture, title, loader path, kernel path or image, initramfs path, command-line source, filesystem identity, trust state, signature evidence, slot identity, version, timeout policy and recovery target.

An adapter exposes only supported operations from this set:

- discover: enumerate entries without writes;
- inspect: parse and validate an entry;
- plan: produce a deterministic proposed change;
- verify: validate hashes/signatures against configured trust roots;
- chainload: transfer control when supported and explicitly selected;
- install: create or update an entry only after explicit approval;
- set_default: change persistent default only when supported;
- set_once: change one-shot selection only when supported;
- rollback: restore a verified prior configuration;
- remove: remove only adapter-owned files after explicit confirmation.

Every adapter advertises capabilities per firmware, architecture, filesystem, cryptographic policy and operation. Unsupported actions return a typed unsupported result; no adapter silently emulates a missing operation.

### 4.3 Twenty boot integration targets

The following catalogue is intentionally typed. It is not a promise that DuckBoot can install, configure or chainload all twenty today.

| # | Target | Kind | Intended integration boundary |
|---:|---|---|---|
| 1 | Limine | BIOS/UEFI bootloader | Current Stage 0 provider; preserve pinned binary and protocol attribution |
| 2 | GNU GRUB 2 | BIOS/UEFI bootloader | Config discovery, menu-entry inspection and later chainload/install adapter |
| 3 | GRUB Legacy | Legacy bootloader | Read-only config inspection and explicitly limited migration guidance |
| 4 | systemd-boot | UEFI boot manager | ESP/XBOOTLDR entry inspection and supported default/one-shot operations |
| 5 | rEFInd | UEFI boot manager | Discovery and chainload integration; preserve its own driver/config model |
| 6 | SYSLINUX | BIOS bootloader family | Config and module-aware discovery |
| 7 | ISOLINUX | ISO bootloader | Live-media and ISO entry inspection |
| 8 | EXTLINUX | Filesystem bootloader | ext-family entry inspection where format support is qualified |
| 9 | PXELINUX | Network bootloader | PXE menu discovery; no DHCP/TFTP server provisioning implied |
| 10 | iPXE | Network boot firmware | Explicit network-chain policy and local trust requirements |
| 11 | UEFI EFI-stub | Firmware kernel path | Direct firmware launch when the kernel has a qualified EFI entry point |
| 12 | Unified Kernel Image (UKI) | Signed boot artifact format | Verify and select a single signed image; not a separate bootloader |
| 13 | Windows Boot Manager | External chainload target | Discover and chainload only; never rewrite Windows-owned files |
| 14 | shim | Secure Boot trust stage | Record trust-chain state and chain into a compatible next-stage loader; not a complete menu manager |
| 15 | U-Boot | Embedded bootloader | Separate board/firmware adapter; not a default x86 desktop dependency |
| 16 | Barebox | Embedded bootloader | Separate embedded adapter with board-specific capability declaration |
| 17 | Petitboot | Firmware/boot manager environment | Discovery/chainload integration where the platform supplies Petitboot |
| 18 | OpenCore | UEFI boot manager | External chainload target with strict ownership and platform limitations |
| 19 | Clover | UEFI boot manager | External chainload target; no assumption of Apple firmware support |
| 20 | LILO | Legacy BIOS bootloader | Read-only legacy inspection and migration path; no new default installation |

BOOTBOOT is kept as a research candidate, not silently counted as a supported adapter. Coreboot/SeaBIOS are firmware or firmware payload layers, not peers of OS boot-entry adapters; integration is through the firmware handoff boundary.

### 4.4 Safe switching and recovery

A bootloader switch is a high-risk system operation. The UI must never expose a simple “replace bootloader” toggle.

Required sequence:

1. Discover current firmware mode, disk layout, ESP identity, active entry and Secure Boot state.
2. Produce a read-only compatibility report; identify unsupported filesystems, encrypted volumes, RAID/LVM and architecture limits.
3. Verify the target loader package and all referenced kernel/initramfs artifacts against pinned hashes and trust policy.
4. Build a dry-run plan listing every path, NVRAM variable and boot-order operation.
5. Save a byte-exact backup of adapter-owned files and a separate recovery record. Never overwrite foreign files.
6. Install to a separate vendor path or separate ESP only when supported; keep the current loader intact.
7. Register a temporary one-shot boot entry rather than permanently changing the default.
8. Reboot only after explicit confirmation. Require a successful kernel boot marker and a health-service confirmation before accepting the new default.
9. If confirmation is missing or startup fails, retain or restore the known-good path and expose recovery instructions.
10. Make uninstall idempotent and restrict it to files and variables created by DuckBoot.

No disk formatting, partition resizing, Secure Boot enrollment, key replacement or firmware variable deletion is part of the initial adapter MVP. Those require separate UX, recovery media and destructive-operation approval.

### 4.5 Secure Boot and update model

Secure Boot is not equivalent to “the loader supports UEFI.” DuckBoot must model firmware Secure Boot state, shim/loader signature policy, kernel signature, initramfs/UKI integrity, trust-root identity, revocation and anti-rollback version.

A caller-provided trusted flag is never evidence. Verification must occur in a native cryptographic boundary using pinned local trust roots and a documented key-rotation and revocation plan. If verification is unavailable, the entry is marked unverified and policy may refuse automatic boot; it is not silently promoted.

Future A/B updates use an inactive slot, signed manifest, complete payload verification, atomic selection, boot-attempt count and post-boot health confirmation. The previous slot remains available until acceptance. The first DuckBoot delivery only specifies and tests this state machine; it does not write disks.

## 5. Reaper contracts and ownership

Reaper owns deterministic decisions and service logic. The initial Reaper contract groups are:

| Contract group | Required decisions |
|---|---|
| duckos.desktop.session | profile validation, activation plan, compatibility and rollback |
| duckos.desktop.output | geometry, mode, scale, output-generation and hotplug transitions |
| duckos.desktop.surface | buffer limits, configure serials, lifecycle and presentation admission |
| duckos.desktop.window | focus, placement, tiling, workspace and state transitions |
| duckos.desktop.input | event ordering, focus routing and device capability checks |
| duckos.desktop.portal | short-lived scoped requests, approval, expiration and revocation |
| duckos.desktop.accessibility | keyboard, contrast, motion, scaling and assistive profile validation |
| duckos.boot.entry | boot-entry descriptor and cross-field validation |
| duckos.boot.adapter | adapter capability negotiation and unsupported-operation results |
| duckos.boot.plan | deterministic dry-run changes and affected-resource inventory |
| duckos.boot.trust | verification evidence shape, signer policy and anti-rollback decision |
| duckos.boot.recovery | known-good entry, boot-attempt budget and rollback transition |

These names are proposed contract namespaces, not a claim that the modules or exports already exist. Do not generate placeholder Reaper source with unverified syntax. Implement the contracts in the canonical Reaper language, add tree-walk and VM tests, then connect them to native code only through a versioned ABI with explicit bounds and ownership.

The native boundary must independently revalidate pointers, buffer lengths, capabilities, firmware data and privileged operations. A Reaper “allow” result is not authority to touch a device, write an ESP or change NVRAM.

## 6. Implementation program

### DSK-0 — Specification and catalogs

Deliver: this architecture, versioned profile and boot-entry schemas, profile catalog, backend capability matrix and traceability tests. No privileged operations.  
Exit: strict schema validation, unknown-key rejection, stable IDs, catalog uniqueness and documentation review.

### DSK-1 — Native display recovery

Deliver: framebuffer text/diagnostic surface, output descriptor contract, software renderer fixtures and input event contract.  
Depends on: reusable memory management, IDT/interrupts, timer and safe framebuffer mapping.  
Exit: malformed framebuffer and geometry tests, deterministic render fixtures, keyboard navigation, QEMU BIOS/UEFI recovery.

### DSK-2 — Native compositor and single-window session

Deliver: software DuckCompositor, DDP v1 local transport, DuckWindow and DuckSession with one output and bounded windows.  
Depends on: process model, syscall ABI, IPC, filesystem and capability enforcement.  
Exit: isolation tests, surface lifecycle fuzzing, input-routing tests, client crash cleanup, frame-time evidence and recovery without GPU acceleration.

### DSK-3 — Shell and first three profiles

Deliver: DuckShell, launcher, panel, settings, file manager and plasma-workspace, gnome-overview, xfce-classic profiles.  
Exit: core tasks keyboard-accessible, profile rollback, offline startup, localization, accessibility audit and resource budget.

### DSK-4 — Remaining desktop profiles

Deliver: all twenty data-driven workflow profiles using the shared services.  
Exit: schema conformance, feature coverage matrix, profile switching test, memory/frame budget measurements and no profile-specific privilege.

### DBT-0 — Boot catalog and parser

Deliver: read-only discovery for current Limine config and the first selected external formats; versioned entry model and dry-run planner.  
Exit: parser bounds/fuzz tests, read-only filesystem guarantees, exact adapter capability report and deterministic plans.

### DBT-1 — DuckBoot menu on Limine

Deliver: a Duck-owned boot menu/policy stage launched through the existing Limine path, without changing the firmware loader or disk layout.  
Exit: BIOS/UEFI QEMU tests, timeout/default/recovery tests, malformed entry rejection and serial evidence.

### DBT-2 — Independent UEFI application

Deliver: DuckBoot as a separate UEFI executable and a separately qualified BIOS path only if required. Keep Limine as fallback.  
Exit: OVMF tests, memory-map handoff conformance, Secure Boot trust tests, bad-signature rejection and recovery entry validation.

### DBT-3 — External adapter expansion

Deliver: GRUB 2, systemd-boot and rEFInd discovery/chainload adapters first; then Syslinux family, network and embedded providers only when target hardware/firmware is supported.  
Exit: adapter-specific fixtures and test matrices; no unsupported operation reported as available.

### DBT-4 — Installer, A/B and rollback

Deliver: explicit installer, signed updates, one-shot boot trial and health-confirmed rollback.  
Exit: fault injection at every write boundary, power-loss simulation, corrupt signature/hash tests, foreign-file preservation, NVRAM rollback and recovery media qualification.

## 7. Build, test and release gates

All implementation changes must include:

- Reaper source contracts and tree-walk plus VM tests for policy behavior;
- native host tests for parsers, serialization, geometry and state-machine boundaries;
- QEMU BIOS and OVMF UEFI boot gates for boot-path changes;
- fuzzing for DDP, configuration parsers, boot-entry descriptors and image metadata;
- static analysis and memory/undefined-behavior checks for native components;
- negative tests for invalid capabilities, stale serials, malformed paths, overflow, resource exhaustion and failed verification;
- deterministic fixtures with exact input, expected output and version;
- CI artifact provenance, SHA-256 inventory and pinned third-party inputs;
- license and attribution review for every imported project or protocol;
- release notes that distinguish specification, host-tested behavior, emulator-tested behavior and physical-hardware qualification.

Primary native target is x86_64 Intel/AMD. Elbrus remains a separate architecture backend with its own compiler, ABI, CI and hardware evidence; it is not removed and is not marked supported by x86_64 tests.

No third-party desktop environment, loader, driver or firmware payload is copied into DuckOS without a license, provenance, security and maintenance review. Adapters must use upstream formats and APIs without pretending that the upstream project is part of DuckOS.

## 8. Definition of done

The desktop is delivered only when a user can boot into a native session, open/close/move/tile windows, switch among all shipped profiles, manage files and settings, use accessibility features, recover from a compositor/client failure and work offline without the browser.

DuckBoot is delivered only when firmware can reach a tested Duck-owned selection menu, entries are verified according to policy, a failed trial returns to a known-good boot path, and installation/uninstall preserve unrelated EFI files and firmware entries.

Until these gates pass, the accurate status remains: **specified**, **partially implemented**, or **planned**—never “native KDE support,” “GRUB replacement,” “twenty bootloaders implemented,” or “complete desktop OS.”
