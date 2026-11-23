# Mora Design System

Canonical source: DuckOS / Mora · Schema: `mora.theme.v1` · Maintainer: Ivan-VHS.

Mora is the common desktop identity for the Ivan-VHS application family. The shell owns wallpaper, workspace navigation, catalogue, status area and app presentation. Each native tool keeps its specialist layout and product indicators while sharing surfaces, spacing, typography, focus and motion.

## Visual direction

Layered sunset landscape, translucent surfaces and a deep indigo foundation are retained from the Mora home-screen concept. Purple is the shared brand accent; teal is the secondary accent. Existing blue, red, waveform and hardware indicators remain semantic where recolouring would make information less clear.

## Semantic palette

| Token | Dark | Light |
|---|---|---|
| Page | `#10142A` | `#F5F3FA` |
| Surface | `#191E39` | `#FFFFFF` |
| Elevated | `#252B4B` | `#ECE9F5` |
| Text | `#F5F4FF` | `#211F31` |
| Secondary | `#D5D6EB` | `#4E4B63` |
| Muted | `#A8ADC8` | `#66627A` |
| Brand | `#A78BFA` | `#5B43B5` |
| Brand hover | `#C1AEFF` | `#49359D` |
| Brand text | `#1D1730` | `#FFFFFF` |
| Secondary accent | `#38D4B7` | `#006F68` |
| Border | `#3B4262` | `#D6D0E7` |
| Selection | `#353054` | `#E6E0F7` |
| Danger | `#FF8EAC` | `#A91F49` |

Normal text and action foreground/background pairs must meet WCAG AA 4.5:1. Status meaning must also be expressed in a label or icon, never color alone.

## Geometry and typography

- Standard spacing scale: 4, 8, 12, 16, 24, 32 px.
- Window radius: 18–24 px; cards: 14–18 px; controls: 9–12 px.
- Interactive target: at least 44 × 44 px.
- UI font: Segoe UI or platform sans-serif; display font: Unbounded where installed; code: Cascadia Mono/Consolas.
- Use tabular numerals for clocks, metrics and numeric columns.

## Motion and accessibility

Standard transitions are 160–220 ms. Respect native reduced-motion settings; Eco Visuals disables nonessential effects. Keyboard focus remains visible, Escape closes transient windows, and native DPI/accessibility behavior must be preserved.

## Integration contract

`mora/theme.json` is the portable token source. Native adapters may expose toolkit-specific aliases, but must preserve the same semantic values and contrast. Applications must not fetch CSS or theme data from a network at runtime.
