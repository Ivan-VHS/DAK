# Mora Design System

**Canonical source:** DuckOS / Mora · **Schema:** `mora.theme.v1` · **Maintainer:** Ivan-VHS.

Mora is the shared desktop identity for the Ivan-VHS application family. The shell owns wallpaper, workspace navigation, application catalogue, status area and app presentation. Each native tool keeps its specialist layout and product indicators while sharing semantic surfaces, spacing, typography, focus, motion and a restrained material language.

## Visual direction

Mora uses one fixed DuckOS palette: black structural surfaces, white content and duck yellow for selection, focus and primary action. The desktop keeps a deep, near-black radial workspace with a restrained vertical fold rhythm; folds use tonal black, graphite, white highlights and yellow edge light. The palette is not user-switchable and the shell does not retain alternate Amber, Dark or Light modes.

The target composition is approximately 65% black, 25% white/graphite and 10% yellow. These are visual balance targets, not a requirement to recolor imported media or user content. Application identities share the same yellow accent; application meaning comes from names, glyphs and labels rather than a rainbow of per-app colors.

The standard workspace remains visually stable at the centre. Secondary content and controls are arranged symmetrically around it; decorative treatment never obscures task content.

## Semantic palette

| Token | Value | Role |
|---|---|---|
| Page | `#080808` | Desktop background |
| Surface | `#151515` | Primary panel |
| Elevated | `#242424` | Secondary panel |
| Text | `#FFFFFF` | Main copy |
| Secondary | `#E5E5E5` | Supporting copy |
| Muted | `#A6A6A6` | Quiet metadata |
| Brand | `#FFD400` | Primary action and selection |
| Brand hover / focus | `#FFE45C` | Hover and keyboard focus |
| Brand text | `#080808` | Text on yellow |
| Secondary accent | `#FFD400` | Shared application accent |
| Border | `#3A3A3A` | Structural edge |
| Selection | `#3A3100` | Selected surface |
| Alert | `#FFD400` | Alert marker, accompanied by text and an icon |

Normal text and controls target WCAG AA contrast (4.5:1); primary body copy targets 7:1 where practical. Meaning is never communicated through hue alone: alert, warning and critical states retain explicit labels, icons and text.

`mora/theme.json` is the canonical, versioned token source. It contains exactly one palette, `duck`. Saved legacy theme preferences are normalized to this profile; the shell has no theme-cycling control.

## Composition and geometry

- Build a central radial anchor using a stable circular field and concentric edge detail.
- Repeat vertical folds with a consistent interval; align columns, dividers and background texture to that rhythm.
- Balance secondary controls around the core, leaving the working surface open and legible.
- Keep dark surfaces distinguishable through a warm rim, tonal gradient or controlled highlight.
- Use material cues selectively: draped fabric, natural wood, brushed metal, muted glass and paper.
- Foreground controls stay crisp; background structure may soften with distance.
- Keep top controls compact and grouped. Put progress, discrete ticks and critical markers at the lower boundary instead of floating over work content.

## Motion

Use predictable low-amplitude transitions with `ease-in-out`: 80–140 ms for focus and direct feedback, 160–240 ms for panel changes and 260–380 ms for context changes. Avoid random movement, strobing, flashing gradients and perpetual ambient motion.

A stable centre may frame peripheral markers. Progress uses a linear track and discrete ticks with an explicit position; state must also be represented semantically.

OS reduced-motion preferences override decorative movement. Disable nonessential transitions and replace smooth scrolling with immediate navigation when reduced motion is requested. The Eco profile suppresses expensive visual effects.

## Geometry, scale and interaction

Mora's browser workspace uses a searchable start menu, three local workspaces, a bottom dock, system quick controls, notifications and draggable application windows. Windows support focus/z-order, minimize, maximize/restore and close. File operations and terminal commands remain scoped to the virtual workspace until DuckOS supplies a permissioned native filesystem and process service.

Quick-panel indicators for Wi-Fi and Bluetooth are presentation-only; they do not toggle physical radios. The System Overview bars are simulated demo values, not kernel telemetry. Browser-side settings remain preferences, not hardware or kernel controls. See [Interactive Mora workspace](docs/MORA_INTERACTIVE_WORKSPACE.md) for the complete behavior and validation boundaries.

- Spacing follows 4, 8, 12, 16, 24 and 32 px.
- Window corners: 18–24 px; cards: 14–18 px; controls: 9–12 px.
- Interactive targets are at least 44 × 44 px where the platform allows.
- Preserve visible keyboard focus, labels, tab order, Escape handling, native DPI and text scaling.
- Keep the centre stable as layouts reflow; at narrow widths, collapse columns instead of shrinking text or hit areas.

## Typography

Mora keeps **Inter / Segoe UI / system sans-serif** for the main interface. The calligraphic set is an accent layer, not a replacement for controls, dense text or system status.

- Display / brand: **Lobster**, then **Pacifico** as an optional local fallback.
- Cyrillic handwritten accents: **Caveat**, **Marck Script** and **Bad Script**.
- Large expressive lettering: **Comforter** and **Comforter Brush**; use sparingly.
- Latin-only ornament: **Great Vibes**, **Alex Brush**, **Allura**, **Pinyon Script**, **Italianno**, **Parisienne** and **Herr Von Muellerhoff**. Apply only to Latin text.
- Code and numeric content keep their existing monospace/tabular treatment.

The CSS stacks reference locally installed font families and do not fetch Google Fonts at runtime. This preserves Mora's offline behavior. Until licensed font files are bundled with their original notices, missing families fall back to the browser's local generic fonts. The complete approved set and redistribution rules are in [Calligraphic Typography](docs/CALLIGRAPHIC_TYPOGRAPHY.md).

## Integration contract

`mora/theme.json` is the canonical token source. Native adapters may expose toolkit-specific names but must preserve semantic roles and contrast. The shell may read local theme assets; it must not fetch CSS or theme data from a remote server at runtime.

Mora remains a browser desktop shell, not a native process launcher. Native application capabilities and security boundaries remain owned by their respective projects; a permissioned launcher/IPC layer must be implemented and verified separately.

