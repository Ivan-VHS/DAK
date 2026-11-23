# Mora Design System

**Canonical source:** DuckOS / Mora  
**Schema:** `mora.theme.v1`  
**Maintainer:** Ivan-VHS

Mora is the single desktop identity for DuckOS. The shell owns the wallpaper, launcher, workspace, window presentation, dock, status area and system-control surfaces. First-party apps keep their specialist function while sharing window behavior, semantic colors, spacing, focus and motion rules.

## Visual direction

Mora Amber uses a dark walnut/graphite work area surrounded by deep amber fabric folds. The curtain-like drapery remains on the left and right edges; a softly shaded radial center preserves clear space behind desktop controls. Warm sand and ochre highlights live on raised surfaces, not over the full working text area. Critical states use muted red and must also carry a text/icon label.

The light palette is a warm parchment variation of the same material language, not a separate theme.

## Semantic palette

| Token | Dark | Light |
|---|---|---|
| Page | `#211913` | `#FBF5EC` |
| Surface | `#33261D` | `#FFF9F0` |
| Elevated | `#493326` | `#F2E3D1` |
| Text | `#FFF3E2` | `#241B14` |
| Secondary | `#E7D2B8` | `#5C4632` |
| Muted | `#C4A98A` | `#765E47` |
| Brand | `#D58B3D` | `#8A4F1C` |
| Brand hover | `#EAA653` | `#704018` |
| Secondary accent | `#8A6242` | `#385B49` |
| Border | `#75543A` | `#C8AE90` |
| Selection | `#60442E` | `#F4DEC0` |
| Danger | `#B64A40` | `#A4352E` |

Text and interactive foreground/background pairs should meet WCAG AA 4.5:1. Never use color alone to communicate status.

## Geometry and typography

- Standard spacing: 4, 8, 12, 16, 24 and 32 px.
- Window radius: 18–22 px; cards: 13–18 px; controls: 9–12 px.
- Interactive targets should be at least 44 × 44 px.
- UI font: Segoe UI or platform sans-serif; display font: Unbounded where installed; code: Cascadia Mono/Consolas.
- Use tabular numerals for clocks, metrics and numeric columns.

## Motion and accessibility

Standard transitions are 140–220 ms. Respect the saved reduced-motion preference and the browser's `prefers-reduced-motion` setting. Keyboard focus remains visible, Escape closes transient windows, and touch layouts must retain reachable controls.

## Integration contract

`mora/theme.json` is the portable semantic token source. `mora/amber.css` maps those tokens to browser surfaces; native adapters may add toolkit-specific aliases but must preserve semantic values and contrast. Desktop applications must not fetch CSS or theme data from the network at runtime.
