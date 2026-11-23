# Mora Blade Hub

**Project:** DuckOS / Mora  
**Maintainer:** Ivan-VHS  
**Status:** Implemented as a browser-shell navigation layer

## Purpose

Blade Hub adds a controller-friendly, horizontally organised view over the existing Mora application launcher. It is inspired by the general navigation pattern of early console dashboards, while keeping DuckOS identity, project-owned artwork and the existing Mora window manager.

The Hub is optional. The standard Mora desktop remains the default landing surface.

## Navigation model

The four blades are:

| Blade | Contents |
|---|---|
| Live | Local profile view, trust preferences, device links and workspace controls |
| Games | Game library, performance workbench links and compatibility inspectors |
| Media | Audio, photo, budget and personal media collections |
| System | Automation, notes, archive inspection, desktop tools and application catalogue |

Three workspaces (01, 02, 03) store separate view contexts: active blade, semantic VFS node and selected panel. The Hub contains the same 29 built-in panels as the main Mora launcher; it does not create duplicate app implementations.

## Language and semantic paths

The language selector supports RU, UA and RU/UA. Stable node IDs back the labels, so changing the language does not change the underlying navigation identity. The semantic VFS is a local catalogue view with paired Russian and Ukrainian aliases. It is not a mount table, host filesystem browser or native VFS.

The local command field accepts only a small allowlist:

- язык ru|ua|dual / мова ru|ua|dual
- путь <alias or path> / шлях <alias or path>
- blade live|games|media|system
- ws 01|02|03
- audit
- помощь / допомога

No command is passed to a shell, evaluated as JavaScript or executed by the operating system.

## Twenty architecture vectors

The index covers: functional development, capability design, tooling, equipment, enablement, competencies, integrations, subsystems, mechanisms, tools, components, modules, implementation, automation, optimisation, compatibility, performance, scalability, universality and extensibility.

Each vector links to an existing Mora panel as a useful entry point. A vector's presence in this index records architectural scope; it is not a maturity claim about its native subsystem.

## Controller and accessibility

The Hub supports pointer and touch input, keyboard focus navigation, Escape to close, and Alt+Left/Right to change blades. While the overlay is open, a standard Gamepad API controller can use D-pad left/right to move between blades, D-pad up/down to move focus and A to activate the focused control. The polling loop runs only while the Hub is open and is cancelled on close.

Reduced-motion settings disable the Hub's entrance and focus transitions. The layout collapses into a scrollable single-column view on narrow screens.

## Rights, provenance and implementation boundaries

The inspector verifies the visible mapping between Hub entries and built-in Mora launcher tiles and checks that the expected same-origin CSP directives exist. It does not claim to verify package signatures, publisher identity, user ownership, Xbox account state, home-console activation, licence entitlements or DRM. The profile selector is a local UI preference only.

No Xbox or Microsoft logos, screenshots, proprietary fonts, sounds, artwork or source code are bundled. The design borrows only a broad category-blade navigation idea and controller-focus conventions. The Hub is an independent DuckOS interface concept and is not affiliated with Microsoft.

Native package signing, content authorisation, process isolation, capability enforcement and mounted VFS access remain outside the browser shell and require dedicated native services.
