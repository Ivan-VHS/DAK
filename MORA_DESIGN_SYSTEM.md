# Mora Design System

**Canonical source:** DuckOS / Mora · **Schema:** `mora.theme.v1` · **Maintainer:** Ivan-VHS.

Mora is the shared desktop identity for the Ivan-VHS application family. The shell owns wallpaper, workspace navigation, application catalogue, status area and app presentation. Each native tool keeps its specialist layout and product indicators while sharing semantic surfaces, spacing, typography, focus, motion and a restrained material language.

## Visual direction

Mora uses one fixed DuckOS palette: soft graphite structure, warm white content and a muted duck-yellow accent for selection, focus and primary action. The desktop keeps a quiet radial workspace with low-contrast original folds and a central application grid. The palette is not user-switchable and the shell does not retain alternate Amber, Dark or Light modes.

The target composition is approximately 65% black, 25% white/graphite and 10% yellow. These are visual balance targets, not a requirement to recolor imported media or user content. Application identities share the same yellow accent; application meaning comes from names, glyphs and labels rather than a rainbow of per-app colors.

The standard workspace remains visually stable at the centre. Secondary content and controls are arranged symmetrically around it; decorative treatment never obscures task content.

## Semantic palette

| Token | Value | Role |
|---|---|---|
| Page | `#0E0F0D` | Desktop background |
| Surface | `#191A17` | Primary panel |
| Elevated | `#252721` | Secondary panel |
| Text | `#F5F4EF` | Main copy |
| Secondary | `#E7E5DC` | Supporting copy |
| Muted | `#A6A69D` | Quiet metadata |
| Brand | `#D6BE65` | Primary action and selection |
| Brand hover / focus | `#E6D48B` | Hover and keyboard focus |
| Brand text | `#0E0F0D` | Text on yellow |
| Secondary accent | `#D6BE65` | Shared application accent |
| Border | `#3A3B35` | Structural edge |
| Selection | `#3E3825` | Selected surface |
| Alert | `#D6BE65` | Alert marker, accompanied by text and an icon |

Normal text and controls target WCAG AA contrast (4.5:1); primary body copy targets 7:1 where practical. Meaning is never communicated through hue alone: alert, warning and critical states retain explicit labels, icons and text.

`mora/theme.json` is the canonical, versioned token source. It contains exactly one palette, `duck`. Saved legacy theme preferences are normalized to this profile; the shell has no theme-cycling control.

## Composition and geometry

- Keep the app launcher centred and give it the strongest visual hierarchy; place clock and widgets in quieter side columns.
- Use original low-contrast folds and a restrained radial background; avoid bright gradients behind text.
- Represent applications with consistent, centred glyph tiles and readable labels rather than large promotional cards.
- Use Soft Glass sparingly: translucent graphite surfaces, a subtle border and modest blur, with flat content inside.
- Keep controls crisp and backgrounds quiet; depth comes from light separation, not heavy shadows.
- Keep top controls compact and grouped. Put progress, discrete ticks and critical markers at the lower boundary instead of floating over work content.

## Motion

Use restrained iOS-inspired motion without copying proprietary interface assets: 140–180 ms for direct feedback, 200–240 ms for app interactions and 260–300 ms for window transitions. Prefer a short ease-out curve with a slight spring, small scale/opacity changes and no exaggerated bouncing. Avoid random movement, strobing, flashing gradients and perpetual ambient motion.

A stable centre may frame peripheral markers. Progress uses a linear track and discrete ticks with an explicit position; state must also be represented semantically.

OS reduced-motion preferences and the Mora Reduce Motion setting override decorative movement. Disable nonessential transitions and smooth scrolling when reduced motion is requested. The Eco profile suppresses blur-heavy surfaces and background detail.

## Geometry, scale and interaction

- Spacing follows 4, 8, 12, 16, 24 and 32 px.
- Window corners: 18–24 px; cards: 14–18 px; controls: 9–12 px.
- Interactive targets are at least 44 × 44 px where the platform allows.
- Preserve visible keyboard focus, labels, tab order, Escape handling, native DPI and text scaling.
- Keep the centre stable as layouts reflow; at narrow widths, collapse columns instead of shrinking text or hit areas.

## Integration contract

`mora/theme.json` is the canonical token source. Native adapters may expose toolkit-specific names but must preserve semantic roles and contrast. The shell may read local theme assets; it must not fetch CSS or theme data from a remote server at runtime.

Mora remains a browser desktop shell, not a native process launcher. Native application capabilities and security boundaries remain owned by their respective projects; a permissioned launcher/IPC layer must be implemented and verified separately.



## Rights, provenance and security

The Mora glyphs, wallpaper treatment, layout, CSS and interaction details are maintained as project-authored DuckOS assets. The interface may use familiar motion principles such as easing, spring settling and sheet-like transitions, but it does not reproduce Apple logos, SF Symbols, screenshots, wallpapers or proprietary UI artwork. No external font, script, analytics or image service is loaded by the shell.

The HTML shell carries a same-origin Content Security Policy: scripts, workers, connections, manifests and form targets are restricted to the local origin; object embedding is disabled. Inline styles remain enabled because the current app panels use bounded, project-authored style attributes. A deployed native host should also send response headers for frame policy, MIME sniffing, permissions and transport security. The CSP is a browser-layer defence, not process sandboxing.

Sentinel remains a deny-by-default preference surface. Its toggles do not enforce microphone, camera, file, network or clipboard isolation in native processes until a DuckOS capability broker and sandbox are implemented.


## Blade Hub and console-inspired navigation

Mora includes an optional **Blade Hub** inspired by the broad horizontal category navigation of early console dashboards. It is an original DuckOS interface, not a reproduction of a console dashboard. The shell uses four content blades — Live, Games, Media and System — with three independently remembered workspace contexts. The Hub is opened from the status bar and does not replace the standard central launcher.

The language selector has three modes: Russian (RU), Ukrainian (UA) and paired labels (RU/UA). Each semantic VFS navigation node has a stable internal ID and equivalent Russian/Ukrainian labels. Paths are a navigation model over the Mora catalogue; they are not mounted directories and do not grant access to the host filesystem.

The Hub presents all 29 existing built-in Mora panels and indexes the 20 shared system vectors. A vector is an architectural area and points to a related built-in panel; its presence in the index is not a claim that the corresponding native subsystem is complete. Workspace choices, language and profile view are stored locally in the browser profile.

Keyboard navigation supports Escape, arrow-key movement, and Alt+Left/Right blade switching. A connected standard Gamepad API controller can use the D-pad and A button while the Hub is open. Controller polling stops when the Hub closes. The interface remains usable with pointer and touch input and respects both operating-system and Mora reduced-motion settings.

## Trademark, provenance and trust boundary

The Blade Hub uses only project-maintained DuckOS markup, CSS and glyphs. It does not bundle Xbox or Microsoft logos, console screenshots, proprietary fonts, sounds, artwork or copied source code. The visual reference is limited to the general idea of horizontal category blades and controller-friendly focus movement. The feature is an independent DuckOS concept and is not affiliated with Microsoft.

The inspector audits the correspondence between the built-in Mora catalogue and the visible desktop tiles, and checks for the shell's same-origin CSP. It does **not** validate package signatures, account ownership, console activation, DRM or third-party licences. Profile selection is a local presentation preference, not an Xbox account or an authorization grant. Sentinel and the Hub do not enforce native process permissions.

The semantic VFS is a bilingual shell-level index. It does not expose host paths, mount volumes, read arbitrary files or replace the native DuckOS VFS. Native rights enforcement, package signing and trusted content installation belong to a future permissioned system service.
