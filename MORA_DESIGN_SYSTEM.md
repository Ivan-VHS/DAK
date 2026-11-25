# Mora Design System

**Canonical source:** DuckOS / Mora · **Schema:** `mora.theme.v1` · **Maintainer:** Ivan-VHS.

Mora is the shared desktop identity for the Ivan-VHS application family. The shell owns wallpaper, workspace navigation, application catalogue, status area and app presentation. Each native tool keeps its specialist layout and product indicators while sharing semantic surfaces, spacing, typography, focus, motion and a restrained material language.

## Visual direction

Mora follows **Imperial Noir & Glass**: near-black architectural structure, white/graphite content and one semantic gold accent. The supplied Figma library contains six material families—Складки света, Медное стекло, Тихие дюны, Световые поля, Пластика форм and Янтарная ночь. These are material studies, not finished application screens or reusable UI widgets. Mora adapts their geometry and lighting into shell surfaces instead of placing full-frame imagery behind controls.

The shell uses a black canvas (`#050505`) and structural shell (`#070707`). Surfaces are layered charcoal acrylic; depth comes from restrained translucency, thin edge light, overlapping curves and local highlights. Gold `#FFD700` replaces the former `#FFD400` and acts only as the selection, focus and primary-action colour. Copper and amber tones from the source become low-opacity gold reflections, never additional product accent colours.

The composition remains content-first: dark material structure frames the work area, a narrow glint marks the active plane, and cards/windows retain readable text and predictable boundaries. The browser reference may use CSS backdrop filtering; the Qt host adapter uses translucent native widget surfaces and painted highlights. Neither claims a compositor-level blur effect.

Application identity comes from names, glyphs and labels rather than per-app rainbow colours. Imported media and user content are not recoloured. Status meaning stays semantic: success green, danger red, information blue, warning gold—with labels and icons in addition to colour.

## Semantic palette

| Token | Value | Role |
|---|---|---|
| Canvas | `#050505` | Deep workspace outside the shell |
| Page / shell | `#070707` | Structural desktop surface |
| Surface | `#111315` | Primary panel and window content |
| Elevated | `#1A1C20` | Raised surface and active group |
| Text | `#F5F5F5` | Main copy |
| Secondary | `#D8DADF` | Supporting copy |
| Muted | `#979BA4` | Secondary metadata |
| Brand | `#FFD700` | Selection, focus and primary action |
| Brand hover / focus | `#FFE36A` | Interactive highlight |
| Brand text | `#070707` | Text on gold |
| Border | `#34373D` | Structural edge |
| Selection | `#332A00` | Gold-tinted selected surface |
| Success | `#22C55E` | Positive system status |
| Danger | `#EF4444` | Error or critical state |
| Information | `#3B82F6` | Informational state |
| Warning | `#FFD700` | Warning state |

Normal text and controls target WCAG AA contrast (4.5:1); primary body copy targets 7:1 where practical. Meaning is never communicated through hue alone: status and alert states retain explicit labels, icons and text.

`mora/theme.json` is the canonical, versioned token source. It contains exactly one palette, `duck`; browser preview, Qt host adapter and installed web manifest use the same values. Saved legacy theme preferences normalise to this profile. The shell has no theme-cycling control.

## Composition and geometry

- Build depth from layered charcoal planes, a soft radial field and a restrained asymmetrical gold reflection.
- Translate vertical cloth folds into a few low-contrast, curved structural lines; keep them behind the content layer.
- Use ring and quarter-circle geometry as clipped panel accents, progress tracks, compact app glyph containers and window overview thumbnails—not as oversized decorative controls.
- Use dune-like curves only as broad workspace transitions or empty-state separators; preserve straight alignment for toolbars, tables and data entry.
- Put a single thin gold glint on the active surface edge. Do not outline every card in bright gold.
- Keep the foreground crisp; background highlights may soften with distance. Material effects never obscure focus rings, text or hit targets.
- Maintain a stable work area and compact groups. Progress and critical markers sit at clear boundaries rather than floating over task content.

## Figma material-to-shell mapping

| Reference family | Adapted shell form |
|---|---|
| Складки света | Low-contrast curved desktop folds and directional edge reflections |
| Медное стекло | Translucent charcoal planes, ring-like clipping and a fine gold rim |
| Тихие дюны | Quiet workspace separators and empty-state silhouettes |
| Световые поля | Local radial illumination for active panels and launcher surfaces |
| Пластика форм | Quarter-circles and overlapping geometry in app tiles and window overview cards |
| Янтарная ночь | A single thin gold edge on the active surface |

The source is [a Figma material library](https://www.figma.com/design/RWjphsEdITgECaS8G31o9H/Untitled?node-id=0-1), not a completed UI kit. Its compositions are translated as local CSS/SVG and Qt-painted primitives, not imported as full-frame image backgrounds. Copper/amber reflections are recoloured as low-opacity gold and do not create a second accent palette.

## Motion

Use predictable low-amplitude transitions with `ease-in-out`: 80–140 ms for focus and direct feedback, 160–240 ms for panel changes and 260–380 ms for context changes. Avoid random movement, strobing, flashing gradients and perpetual ambient motion.

A stable centre may frame peripheral markers. Progress uses a linear track and discrete ticks with an explicit position; state must also be represented semantically.

OS reduced-motion preferences override decorative movement. Disable nonessential transitions and replace smooth scrolling with immediate navigation when reduced motion is requested. The Eco profile suppresses expensive visual effects.

## Geometry, scale and interaction

- Spacing follows 4, 8, 12, 16, 24 and 32 px.
- Window corners: 18 px; cards: 14 px; controls: 8 px. Use 4/8/12/16/24/32 px spacing.
- Interactive targets are at least 44 × 44 px where the platform allows.
- Preserve visible keyboard focus, labels, tab order, Escape handling, native DPI and text scaling.
- Keep the centre stable as layouts reflow; at narrow widths, collapse columns instead of shrinking text or hit areas.

## Integration contract

`mora/theme.json` is the canonical token source. Native adapters may expose toolkit-specific names but must preserve semantic roles and contrast. The shell may read local theme assets; it must not fetch CSS or theme data from a remote server at runtime. Browser backdrop filters are progressive enhancement; native Qt panels use translucent fills and painted edge lighting rather than claiming compositor blur.

The primary Mora desktop surface is a host-native Qt 6 Widgets application. Its application windows are real top-level host windows managed by the host operating system; the shell does not embed Qt WebEngine, WebView, HTML or browser-rendered application windows. The native shell reads the shared local catalogue and never executes manifest-provided command strings.

The browser implementation remains available as a reference/compatibility preview, not as the native desktop. The Qt host adapter is still distinct from the DuckOS kernel desktop: Stage 1 does not launch user processes, and a kernel-owned compositor, input service, font stack, accessibility bridge and capability broker remain separate D8 work.

