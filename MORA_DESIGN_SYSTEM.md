# Mora Design System

**Canonical source:** DuckOS / Mora · **Schema:** `mora.theme.v1` · **Maintainer:** Ivan-VHS.

Mora is the shared desktop identity for the Ivan-VHS application family. The shell owns wallpaper, workspace navigation, application catalogue, status area and app presentation. Each native tool keeps its specialist layout and product indicators while sharing semantic surfaces, spacing, typography, focus, motion and a restrained material language.

## Visual direction

The single desktop profile is **DuckOS Black / White / Yellow**: near-black workspace surfaces, bright white text, and a restrained duck-yellow accent for navigation, focus, selection and actions. The wallpaper may use tonal black folds and yellow edge highlights, but no blue, red, green, purple or legacy amber palette remains. Depth comes from light, shadow and subtle grayscale surfaces rather than unrelated hues.

The standard workspace remains visually stable at the centre. Secondary content and controls are arranged symmetrically around it; decorative treatment never obscures task content.

## Semantic palette

The shell has one palette only. Legacy Amber, Dark and Light variants are not retained.

| Token | DuckOS value | Role |
|---|---|---|
| Page | `#080808` | Near-black desktop |
| Surface | `#151515` | Primary panel |
| Elevated | `#242424` | Secondary panel |
| Text | `#FFFFFF` | Main copy |
| Secondary | `#E5E5E5` | Supporting copy |
| Muted | `#A6A6A6` | Quiet metadata |
| Brand | `#FFD400` | Duck-yellow action and progress |
| Brand hover / focus | `#FFE45C` | Hover and keyboard focus |
| Brand text | `#111111` | Text on yellow |
| Secondary accent | `#FFD400` | Shared accent |
| Border | `#3A3A3A` | Neutral structural edge |
| Selection | `#3A3100` | Selected content |
| Critical | `#FFD400` | Critical marker; pair with an icon and label |
| Critical text | `#111111` | Text on yellow |

Only black, white, grayscale neutrals and yellow tones are permitted in the interface. State meaning must remain readable through text, shape and iconography, not hue alone. Normal text and controls target WCAG AA contrast (4.5:1); primary body copy targets 7:1 where practical.

`mora/theme.json` is the portable, versioned source for the sole Duck palette.

## Composition and geometry

- Build a central radial anchor using a stable circular field and concentric edge detail.
- Repeat vertical folds with a consistent interval; align columns, dividers and background texture to that rhythm.
- Balance secondary controls around the core, leaving the working surface open and legible.
- Keep dark surfaces distinguishable through a neutral rim, tonal gradient or yellow highlight.
- Use material cues selectively: black and white surfaces, brushed metal, muted glass and yellow edge details.
- Foreground controls stay crisp; background structure may soften with distance.
- Keep top controls compact and grouped. Put progress, discrete ticks and critical markers at the lower boundary instead of floating over work content.

## Motion

Use predictable low-amplitude transitions with `ease-in-out`: 80–140 ms for focus and direct feedback, 160–240 ms for panel changes and 260–380 ms for context changes. Avoid random movement, strobing, flashing gradients and perpetual ambient motion.

A stable centre may frame peripheral markers. Progress uses a linear track and discrete ticks with an explicit position; state must also be represented semantically.

OS reduced-motion preferences override decorative movement. Disable nonessential transitions and replace smooth scrolling with immediate navigation when reduced motion is requested. The Eco profile suppresses expensive visual effects.

## Geometry, scale and interaction

- Spacing follows 4, 8, 12, 16, 24 and 32 px.
- Window corners: 18–24 px; cards: 14–18 px; controls: 9–12 px.
- Interactive targets are at least 44 × 44 px where the platform allows.
- Preserve visible keyboard focus, labels, tab order, Escape handling, native DPI and text scaling.
- Keep the centre stable as layouts reflow; at narrow widths, collapse columns instead of shrinking text or hit areas.

## Integration contract

`mora/theme.json` is the canonical token source. Native adapters may expose toolkit-specific names but must preserve semantic roles and contrast. The shell may read local theme assets; it must not fetch CSS or theme data from a remote server at runtime.

Mora remains a browser desktop shell, not a native process launcher. Native application capabilities and security boundaries remain owned by their respective projects; a permissioned launcher/IPC layer must be implemented and verified separately.

