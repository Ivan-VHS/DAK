# Figma visual source register and adoption gates — 2026

**Implementation baseline:** Imperial Noir & Glass for DuckOS shell surfaces.  
**Audit status:** partial. Figma Starter MCP reached its tool-call limit during source inventory.  
**Important:** page names are not a visual inspection; uninspected files must be reopened before extracting detailed components or assets.

## Supplied sources

| Source | Link | Available inspection |
|---|---|---|
| REVOLUTION | [Open design](https://www.figma.com/design/SqYrXchYGeSMXpJ9NUMgKE/REVOLUTION--Copy-?node-id=0-1&t=XAOR3S3g4hRSaw5A-1) | Page 1; layers not inspected |
| Ocean | [Open design](https://www.figma.com/design/D3eY1RfC4TKRmgq130NsqE/Ocean--Copy-?m=auto&t=CvUfhwIhHUxqnmYW-6) | Page names inventoried; visual content not inspected |
| VFXaddDuck | [Open design](https://www.figma.com/design/UxNfwNJ1HyBb7t9ckLxAyK/VFXaddDuck?m=auto&t=CvUfhwIhHUxqnmYW-6) | Page names inventoried; visual content not inspected |
| Untitled vector source | [Open design](https://www.figma.com/design/3PVK5mGSrIXFIYYZMnYjZa/Untitled?m=auto&t=mrpojYg1dIirQk6b-6) | Page 1; selected layer reported as svg-142; vector geometry not inspected |
| Mora prototype | [Open prototype](https://www.figma.com/proto/M9M3Tkzi1Ecr6HOeU6b5Vg?node-id=0-1&t=mrpojYg1dIirQk6b-6) | Link registered; prototype not inspected |
| Untitled design | [Open design](https://www.figma.com/design/S5Ii85OontEVEHYMs9Ba05/Untitled?m=auto&t=mrpojYg1dIirQk6b-6) | Page 1; layers not inspected |
| Test assignment | [Open design](https://www.figma.com/design/HGFvp3Klm7zMwgBb3xpF7t/%D0%A2%D0%B5%D1%81%D1%82%D0%BE%D0%B2%D0%B5-%D0%B7%D0%B0%D0%B2%D0%B4%D0%B0%D0%BD%D0%BD%D1%8F--%D0%92-%D1%8E%D0%BD%D0%B5%D0%BD%D0%BA%D0%BE?m=auto&t=mrpojYg1dIirQk6b-6) | Registered; call quota prevented inspection |
| Redbubble | [Open design](https://www.figma.com/design/4Jr0n3tlcNmqzgs6oTrEyY/Redbubble?m=auto&t=mrpojYg1dIirQk6b-6) | Registered; call quota prevented inspection |
| Etsy | [Open design](https://www.figma.com/design/YGxNWskby7w1jlo0k20FkJ/Etsy?m=auto&t=mrpojYg1dIirQk6b-6) | Registered; call quota prevented inspection |

## Shared design principles

- Canvas and chrome: near-black `#050505` / `#070707`, working surface `#101010`, elevated graphite `#181818`.
- White and neutral grey carry content hierarchy. Gold `#FFD700` is the single DuckOS action/focus accent; `#FFE45C` is reserved for hover and focus.
- Glass uses dark translucent layers, a fine neutral rim and blur only where supported. Opaque fallbacks must remain legible and functional.
- Status semantics are distinct: green success, gold warning, red error, blue information. Each status also has text/icon/accessible naming; hue alone never carries meaning.
- Use the 4/8/12/16/24/32 px rhythm, 44 px preferred controls, visible keyboard focus, Reduced Motion and Eco behavior.
- Keep products' logos, editorial imagery and specialist data colors. Do not force the DuckOS accent onto waveform, DSP, telemetry or diagnostic measurements.
- Local-first and offline-safe: do not add remote fonts, CDN CSS/JS, remote telemetry or runtime Figma fetches.

## DuckOS surface map

| Surface | Direction |
|---|---|
| Desktop canvas | Near-black workspace with subtle graphite depth and very restrained gold edge light |
| Status bar and dock | Compact chrome, keyboard focus, stable hit targets |
| App tiles and widgets | Dark glass grouping with opaque fallback and readable labels |
| Windows and panels | Shared radius, spacing, borders and clear elevation |
| Motion | Brief feedback and panel transitions; reduced motion removes nonessential spatial movement |
| Assets | Local first-party SVG/PNG; keep editable vector sources where practical |

## Acceptance gates

1. Re-open all nine Figma sources after quota reset and identify concrete frames, variants and assets before detailed visual adoption.
2. Map each selected component/token to the corresponding native project component; do not use a flattened whole-screen image as implementation.
3. Verify contrast, keyboard-only navigation, reduced motion, narrow layouts and 100–200% DPI/text scaling.
4. Run `npm test` in DuckOS and manually inspect the rendered shell before claiming visual parity.
