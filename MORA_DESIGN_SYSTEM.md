# Mora Design System

**Canonical source:** DuckOS / Mora · **Schema:** `mora.theme.v1` · **Maintainer:** Ivan-VHS.  
**Palette set:** Solar, Amber, Arctic, Amethyst and Jade.

Mora is the shared desktop identity for the Ivan-VHS application family. The shell owns wallpaper, workspace navigation, application catalogue, status area and app presentation. Each native tool keeps its specialist layout and product indicators while sharing semantic surfaces, spacing, typography, focus, motion and a restrained material language.

## Visual direction

The default desktop palette is **Obsidian Solar**: near-black graphite, clean white and a focused solar-yellow action accent. **Mora Amber** remains the warm signature option: amber-sand drapery with a repeating vertical fold rhythm, a deep near-black radial centre, graphite and walnut surfaces, subdued olive glass and a single controlled red critical marker. Depth comes from light and shadow, edge highlights and recognizable material response — not neon fill or scattered gradients.

The standard workspace remains visually stable at the centre. Secondary content and controls are arranged symmetrically around it; decorative treatment never obscures task content.

## Semantic palettes

`mora/theme.json` is the canonical source for five complete semantic palettes. Users can change the active palette in **Control → Цветовая палитра**; the choice is applied immediately and persisted in the local preference profile. The compact palette control in the status bar cycles through the same five presets.

| Palette | Core colors | Visual role |
|---|---|---|
| **Obsidian Solar** | Graphite black · clean white · solar yellow | High-contrast, focused desktop; default palette |
| **Mora Amber** | Walnut · sand · copper · muted olive | Warm signature material palette |
| **Arctic Glass** | Ice white · slate · deep cyan · teal | Bright, calm workspace |
| **Amethyst Night** | Deep plum · lavender · mint | Creative, low-glare night palette |
| **Forest Jade** | Pine graphite · cream · jade · soft gold | Natural, restrained green palette |

Each palette defines the same roles: page, surface, elevated surface, primary/secondary/muted text, brand and hover colors, on-brand text, secondary accent and its foreground, border, selection, danger and on-danger foreground. Components must consume semantic roles rather than hard-coded palette colors.

Normal text and controls target WCAG AA contrast (4.5:1); primary body copy targets 7:1 or higher. The automated design-system contract checks every palette's text, secondary text, muted text, main action, secondary action and danger contrast. Meaning is never communicated through hue alone. Red is reserved for destructive or critical states.

Legacy saved values migrate safely: `dark` maps to **Amethyst Night** and `light` maps to **Arctic Glass**. Existing `amber` preferences remain unchanged.

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

