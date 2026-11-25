# Mora Design System

**Canonical source:** DuckOS / Mora · **Schema:** `mora.theme.v1` · **Maintainer:** Ivan-VHS.

Mora is the shared desktop identity for the Ivan-VHS application family. The shell owns wallpaper, workspace navigation, application catalogue, status area and app presentation. Each native tool keeps its specialist layout and product indicators while sharing semantic surfaces, spacing, typography, focus, motion and a restrained material language.

## Visual direction

Mora uses the Imperial Noir & Glass foundation: near-black structural surfaces, graphite elevation, white content and gold for primary action and focus. The desktop keeps a deep, near-black radial workspace with a restrained vertical fold rhythm; folds use tonal black, graphite, white highlights and yellow edge light. The palette is not user-switchable and the shell does not retain alternate Amber, Dark or Light modes.

The target composition is approximately 65% black, 25% white/graphite and 10% yellow. These are visual balance targets, not a requirement to recolor imported media or user content. Application identities share the same yellow accent; application meaning comes from names, glyphs and labels rather than a rainbow of per-app colors.

The standard workspace remains visually stable at the centre. Secondary content and controls are arranged symmetrically around it; decorative treatment never obscures task content.

## Semantic palette

| Token | Value | Role |
|---|---|---|
| Page | `#050505` | Desktop background |
| Surface | `#101010` | Primary panel |
| Elevated | `#181818` | Secondary panel |
| Text | `#FFFFFF` | Main copy |
| Secondary | `#E5E5E5` | Supporting copy |
| Muted | `#A6A6A6` | Quiet metadata |
| Brand | `#FFD700` | Primary action and selection |
| Brand hover / focus | `#FFE45C` | Hover and keyboard focus |
| Brand text | `#050505` | Text on yellow |
| Secondary accent | `#FFD700` | Shared application accent |
| Border | `#3A3A3A` | Structural edge |
| Selection | `#3A3100` | Selected surface |
| Alert | `#FFD700` | Alert marker, accompanied by text and an icon |

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

- Spacing follows 4, 8, 12, 16, 24 and 32 px.
- Window corners: 18–24 px; cards: 14–18 px; controls: 9–12 px.
- Interactive targets are at least 44 × 44 px where the platform allows.
- Preserve visible keyboard focus, labels, tab order, Escape handling, native DPI and text scaling.
- Keep the centre stable as layouts reflow; at narrow widths, collapse columns instead of shrinking text or hit areas.

## Integration contract

`mora/theme.json` is the canonical token source. Native adapters may expose toolkit-specific names but must preserve semantic roles and contrast. The shell may read local theme assets; it must not fetch CSS or theme data from a remote server at runtime.

Mora remains a browser desktop shell, not a native process launcher. Native application capabilities and security boundaries remain owned by their respective projects; a permissioned launcher/IPC layer must be implemented and verified separately.



## Figma source integration

The supplied source register and per-surface adoption gates live in
[FIGMA_VISUAL_INTEGRATION_2026.md](docs/FIGMA_VISUAL_INTEGRATION_2026.md).
Figma sources are references, not permission to flatten screens or replace
native interaction patterns.


## Industrial Glass & Digital Physics

The shell uses the normative [DuckOS Industrial Glass & Digital Physics v1](docs/INDUSTRIAL_GLASS_DIGITAL_PHYSICS_V1.md) contract. The material uses a 78% dark content fill / 86% modal fill, 18px / 22px blur, local monochrome grain, a shared top-left specular rim and opaque fallbacks. Hard controls remain solid and crisp.

The shared geometry is architectural: system windows/cards use an 8px radius, controls use 6px. Motion is token-driven, interruptible and capped at 280ms for decorative transitions. Reduced Motion and Reduced Transparency preferences resolve to stable poses and opaque materials. Mora browser styling is not a claim of native compositor/GPU implementation; Reaper policy and future native rendering must keep the same contracts.
