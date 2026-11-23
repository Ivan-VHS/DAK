# Mora Design System

**Canonical source:** DuckOS / Mora · **Schema:** `mora.theme.v1` · **Maintainer:** Ivan-VHS.

Mora is the shared desktop identity for the Ivan-VHS application family. The shell owns wallpaper, workspace navigation, application catalogue, status area and app presentation. Each native tool keeps its specialist layout and product indicators while sharing semantic surfaces, spacing, typography, focus, motion and a restrained material language.

## Visual direction

Mora uses one fixed DuckOS palette: black structural surfaces, white content and duck yellow for selection, focus and primary action. The desktop keeps a deep, near-black radial workspace with a restrained vertical fold rhythm; folds use tonal black, graphite, white highlights and yellow edge light. The palette is not user-switchable and the shell does not retain alternate Amber, Dark or Light modes.

The target composition is approximately 65% black, 25% white/graphite and 10% yellow. These are visual balance targets, not a requirement to recolor imported media or user content. Application identities share the same yellow accent; application meaning comes from names, glyphs and labels rather than a rainbow of per-app colors.

The standard workspace remains visually stable at the centre. Secondary content and controls are arranged symmetrically around it; decorative treatment never obscures task content.

## Semantic palette

DuckOS keeps **one fixed palette** with a base triad and 22 role-specific colors. The new colors extend the original black/white/yellow identity; they do not create separate themes, app-specific rainbow accents or user-selectable color modes. Mora, the native Duck Desktop workbench and future native adapters consume the same semantic roles.

### Base triad

| Role | Value | Use |
|---|---|---|
| Structural black | `#080808` | Main desktop canvas and the system's black identity |
| Content white | `#FFFFFF` | Main text and crisp foreground detail |
| Duck yellow | `#FFD400` | Primary action, selection and product identity |

### Neutral depth and typography (10)

| Token | Value | Role |
|---|---|---|
| Coal Abyss | `#040404` | Deepest stage, modal and panel shadow |
| Graphite Layer | `#111111` | Main panels and containers |
| Raised Graphite | `#1A1A1A` | Elevated cards, menus and active surfaces |
| Dark Slate | `#262626` | Recessed controls, tracks and secondary surfaces |
| Technical Gray | `#3A3A3A` | Dividers, borders and quiet grids |
| Muted Steel | `#5E5E5E` | Disabled controls and unavailable actions |
| Cold Ash | `#888888` | Quiet metadata and low-priority labels |
| Light Silver | `#B8B8B8` | Secondary copy and supporting icons |
| Soft Ivory | `#E6E6DF` | Long-form body copy on dark surfaces |
| Warm Milk | `#F5F3E6` | High-priority supporting copy and readable status text |

### Warm focus and alerts (6)

| Token | Value | Role |
|---|---|---|
| Lemon Highlight | `#FFF066` | Focus ring, keyboard focus and hover highlight |
| Sun Amber | `#E6B800` | Secondary brand intensity and warm gradient depth |
| Deep Saffron | `#B38600` | Accent shadow, edge light and depth |
| Dark Ochre | `#5C4400` | Restrained warm selected surfaces and warning backing |
| Warm Honey | `#FFC42E` | Warning, attention and pending states |
| Signal Red | `#FF473A` | Critical error, recording/stop and destructive state |

### Cool diagnostics and separation (6)

| Token | Value | Role |
|---|---|---|
| Neon Lime | `#8CE63C` | Success, ready and confirmed state |
| Deep Pine | `#2E5918` | Background for success badges and safe-state indicators |
| Ice Cyan | `#5CE1E6` | Information, device presence and synchronized state |
| Cobalt Accent | `#3B82F6` | Links, secondary actions and navigable paths |
| Night Sapphire | `#16294A` | Inspector, information and diagnostic surfaces |
| Storm Graphite | `#1F2633` | Cool neutral panels for tools and separation of planes |

### Status and contrast rules

| State | Foreground | Surface |
|---|---|---|
| Success / ready | `#8CE63C` | `#2E5918` |
| Warning / pending | `#FFC42E` | `#5C4400` |
| Critical / error | `#FF473A` | `#040404` or a restrained red-tinted overlay |
| Information / connected | `#5CE1E6` | `#16294A` |
| Link / navigation | `#3B82F6` | `#080808` |

The selected foreground/background pairs meet WCAG AA for normal text: yellow on page 13.99:1, honey on ochre 5.78:1, signal red on page 5.93:1, lime on pine 5.28:1, cyan on sapphire 9.22:1 and cobalt on page 5.45:1. Disabled steel is intentionally reserved for disabled controls, not normal body copy.

Hue is never the only state signal: warnings, errors, success and information retain a word label, icon or explicit status copy. Primary actions and application identity remain Duck yellow; semantic colors are used only where their meaning is clear.

`mora/theme.json` is the canonical versioned source. Its `colorScale` records the 3 base colors and all 22 additions; `palettes.duck` resolves those values into named interface roles. There is still exactly one palette, `duck`. The same tokens are mirrored in CSS custom properties and the native Tk palette; native toolkit adapters must preserve the semantic names and contrast pairs.
  
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



## Blade launcher and dashboard interaction

The Mora desktop uses a horizontal, focus-led application rail inspired by console blade navigation. Channel buttons filter the existing application registry: all apps, local favorites, creation, games, media, tools and system utilities. The selected card grows slightly and receives the Duck-yellow focus surface; neighboring cards remain graphite. This is a navigation treatment over the existing Mora panels, not a second application catalogue.

The rail supports pointer, touch scrolling and keyboard operation. Left/Right move between cards, Home/End jump to the first/last card, **A** opens the selected panel, **X** toggles its local favorite state and **Y** opens accessible details. Enter activates the focused native button. Escape closes the details dialog or the top Mora window. The shell honors reduced-motion preferences when scrolling.

The profile tile is deliberately a local session summary: it shows the number of currently open Mora windows and opens Control. It does not imply an authenticated Duck account, online presence, hardware health, achievements or a gamerscore. Favorites are stored in the browser's local profile under a versioned key; they are not synced to a remote account.

App cards open the existing panel by its registered app ID. They do not launch arbitrary executables or claim native operating-system process control. Any native launch path must remain separately permissioned and implemented by an appropriate Duck service.


## Screen and viewport targets

The desktop is responsive to CSS viewport size rather than assuming one fixed monitor resolution. The current layout profiles cover:

| Class | Target examples | Layout behavior |
|---|---|---|
| 8K / 5K | 7680×4320, 5120×2880 | Wider centered workspace, larger type, launcher cards, dock and windows |
| 4K / UHD | 3840×2160, 4096×2160 | Expanded three-column desktop, wider app rail and native-size panel surfaces |
| QHD / WQHD | 2560×1440, 3440×1440 | Fluid desktop width with a larger central workspace |
| Full HD | 1920×1080, 1920×1200 | Standard three-column desktop and readable floating application windows |
| Compact desktop / laptop | 1366×768, 1440×900 | Two-column layout, independently scrollable app region and reduced vertical chrome |
| Tablet | 1024×768, 1180×820 | Touch-sized controls and reflowed workspace |
| Phone | 390×844, 360×800, 320×568 | Single-column document flow, horizontal launcher rail and safe-area-aware dock |

Wide desktop layouts use three columns; 16:10, 3:2 and 4:3 workspaces use a two-column composition to protect the central content width. Short landscape viewports reduce vertical spacing instead of clipping the launcher or dock. The shell uses dynamic/small viewport units where browser chrome can change the visible height, and includes safe-area insets for notched devices.

The 8K profile intentionally caps the centered working surface rather than stretching controls across the entire wall. Typography and cards grow with resolution but stop at readable maximum sizes. Application windows remain bounded by both viewport width and height. On small screens, the page becomes scrollable, while app windows and dialogs stay within the visible viewport.

Touch-first devices keep their primary controls at or above 44 CSS pixels. When seven dock shortcuts cannot fit in a narrow viewport, the dock scrolls horizontally instead of shrinking the hit areas.
