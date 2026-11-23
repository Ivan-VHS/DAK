# Mora Amber — visual system

**Maintainer:** Ivan-VHS  
**Scope:** Mora desktop shell and the shared interface language used by Ivan-VHS desktop projects.

Mora Amber is a warm, material-led interface profile: amber drapery, a dark radial workspace, restrained graphite and walnut surfaces, natural-wood highlights, muted mauve/grey support tones and a single restrained red signal. The composition uses light and shadow rather than neon fills.

## Core palette

| Role | Token | Value |
|---|---|---|
| Deep workspace | `bg` | `#211913` |
| Raised surface | `surface` | `#33261D` |
| Secondary surface | `elevated` | `#493326` |
| Primary text | `fg` | `#FFF3E2` |
| Supporting text | `secondary` | `#E7D2B8` |
| Quiet metadata | `muted` | `#C4A98A` |
| Main action | `accent` | `#D58B3D` |
| Action hover / focus | `accent-hover` | `#EAA653` |
| Critical signal | `red` | `#B64A40` |
| Structure / border | `border` | `#75543A` |
| Selection | `selection` | `#60442E` |
| Wood highlight | `wood` | `#8A6242` |

Normal text must maintain at least 4.5:1 contrast; primary body text should aim for 7:1. Amber is for ordinary actions and focus; red is reserved for destructive or critical states. State meaning must remain visible in labels or icons, not hue alone.

## Geometry and composition

- Keep a stable central workspace with concentric circles and a quiet radial edge.
- Establish vertical rhythm with repeated folds, aligned columns and evenly spaced dividers.
- Balance secondary controls around the core; do not cover the working area with decorative panels.
- Keep surfaces dark but distinguishable through warm edges, soft highlights and tonal separation.
- Use material cues sparingly: draped fabric, walnut, brushed metal, frosted glass and paper.
- Keep foreground controls crisp; soften only the distant background.

## Motion

Use predictable, low-amplitude movement with `ease-in-out`. Typical feedback is 80–140 ms, pane changes 160–240 ms, and context changes 260–380 ms. Avoid flashes, random movement and perpetual ambient motion. A stable centre may frame peripheral markers; progress indicators use a linear track and discrete ticks. Respect OS reduced-motion preferences and remove nonessential transitions when reduced motion is enabled.

## Implementation in DuckOS

`prototype/mora-home.html` applies the palette, vertical folded-cloth SVG backdrop, radial application stage, grounded app tiles, restrained dock and reduced-motion behavior. Application data and local persistence remain independent of the presentation layer.

The file remains a browser prototype, not a native compositor or a bootable DuckOS desktop. Native shell integration, monitor-by-monitor visual validation and real-service wiring remain separate engineering work.

## Acceptance

- Check text and focus contrast for every interactive state.
- Test narrow, wide and high-DPI layouts at 100%, 125%, 150% and 200%.
- Confirm keyboard focus and touch targets remain visible.
- Confirm reduced-motion mode removes spatial movement without hiding state changes.
