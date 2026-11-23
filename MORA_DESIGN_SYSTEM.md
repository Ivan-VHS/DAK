# Mora Design System

**Canonical source:** DuckOS / Mora · **Schema:** `mora.theme.v1` · **Maintainer:** Ivan-VHS.

Mora is the shared desktop identity for the Ivan-VHS application family. The shell owns wallpaper, workspace navigation, application catalogue, status area and app presentation. Each native tool keeps its specialist layout and product indicators while sharing semantic surfaces, spacing, typography, focus, motion and a restrained material language.

## Visual direction

The primary desktop profile is **Mora Amber**: warm amber-sand drapery with a repeating vertical fold rhythm, a deep near-black radial centre, graphite and walnut surfaces, muted mauve/grey textiles, subdued olive glass and a single controlled red critical marker. Depth comes from light and shadow, edge highlights and recognizable material response — not neon fill or scattered gradients.

The standard workspace remains visually stable at the centre. Secondary content and controls are arranged symmetrically around it; decorative treatment never obscures task content.

## Semantic palette

| Token | Mora Amber | Role |
|---|---|---|
| Page | `#211913` | Deep walnut workspace |
| Surface | `#33261D` | Primary panel |
| Elevated | `#493326` | Secondary panel |
| Text | `#FFF3E2` | Main copy |
| Secondary | `#E7D2B8` | Supporting copy |
| Muted | `#C4A98A` | Quiet metadata |
| Brand | `#D58B3D` | Normal action and progress |
| Brand hover / focus | `#EAA653` / `#F3C16B` | Hover and keyboard focus |
| Brand text | `#211913` | Text on amber |
| Secondary accent | `#526347` | Subdued olive / glass |
| Border | `#75543A` | Warm structural edge |
| Selection | `#60442E` | Selected content |
| Critical | `#B64A40` | Destructive state / progress marker |
| Critical text | `#FFF3E2` | Text on critical |

Normal text and controls target WCAG AA contrast (4.5:1); primary body copy targets 7:1 where practical. Meaning is never communicated through hue alone. Red is not used for routine emphasis.

Light and Dark remain available as alternate themes. `mora/theme.json` is the portable, versioned source for all three palettes.

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

- Spacing follows 4, 8, 12, 16, 24 and 32 px.
- Window corners: 18–24 px; cards: 14–18 px; controls: 9–12 px.
- Interactive targets are at least 44 × 44 px where the platform allows.
- Preserve visible keyboard focus, labels, tab order, Escape handling, native DPI and text scaling.
- Keep the centre stable as layouts reflow; at narrow widths, collapse columns instead of shrinking text or hit areas.

## Integration contract

`mora/theme.json` is the canonical token source. Native adapters may expose toolkit-specific names but must preserve semantic roles and contrast. The shell may read local theme assets; it must not fetch CSS or theme data from a remote server at runtime.

Mora remains a browser desktop shell, not a native process launcher. Native application capabilities and security boundaries remain owned by their respective projects; a permissioned launcher/IPC layer must be implemented and verified separately.

