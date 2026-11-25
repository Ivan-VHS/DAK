# Imperial Noir & Glass — material language transfer

**Source:** [Figma reference library](https://www.figma.com/design/RWjphsEdITgECaS8G31o9H/Untitled?node-id=0-1)  
**Target:** DuckOS Mora host-native Qt shell and browser reference shell  
**Token source:** `mora/theme.json`

## Reading the source

The Figma file contains full-frame material compositions rather than ready-made interface components. Its six families are:

- **Складки света** — curved metallic folds and narrow reflected edges.
- **Медное стекло** — translucent ring and layered glass forms.
- **Тихие дюны** — broad, soft, layered curves.
- **Световые поля** — dark space with a local radial light source.
- **Пластика форм** — overlapping circles, semicircles and quarter-circles.
- **Янтарная ночь** — a dark field defined by one fine luminous edge.

The implementation does not use those image fills as app backgrounds. It converts their spatial properties into local CSS/SVG and Qt drawing primitives so text, focus, contrast, motion settings and window controls stay functional.

## Adaptation matrix

| Figma visual | Mora shell surface | Adaptation |
|---|---|---|
| Folded reflective planes | Desktop backdrop | Low-contrast curved lines with a single gold reflection |
| Translucent ring | Panel and app tile layers | Charcoal acrylic planes and ring-like edge accents |
| Soft dunes | Workspace layout | Quiet separators and empty-state silhouettes |
| Radial light field | Active panel / launcher | Local illumination instead of a full-screen coloured wash |
| Modular circle geometry | App glyphs / window overview | Quarter-circles and rounded-rect primitives on an 8 px grid |
| Night edge highlight | Focus / selected edge | Thin `#FFD700` line with a subdued glow |

## Canonical palette

| Role | Value |
|---|---|
| Canvas | `#050505` |
| Shell | `#070707` |
| Surface | `#111315` |
| Elevated | `#1A1C20` |
| Main text | `#F5F5F5` |
| Secondary text | `#D8DADF` |
| Muted text | `#979BA4` |
| Primary gold | `#FFD700` |
| Gold hover / focus | `#FFE36A` |
| Border | `#34373D` |
| Selection | `#332A00` |
| Success | `#22C55E` |
| Danger | `#EF4444` |
| Information | `#3B82F6` |

The source contains copper and amber illumination. DuckOS recolours those lighting cues as low-opacity gold reflections. Copper/orange is not introduced as a new system token. Application identity and user-provided media are not recoloured.

## Shell mapping

- **Desktop canvas:** near-black with a soft radial field and restrained folds.
- **System bar and dock:** translucent charcoal acrylic with a clear edge and adequate contrast.
- **App catalogue:** dark cards with a small gold glyph/active state, not gold fills on every tile.
- **Window overview:** compact cards with repeated modular geometry and explicit active/focus states.
- **Notification center:** neutral surfaces; semantic status glyph and text identify event type.
- **Quick settings:** distinct toggle and unavailable-service states; no fake hardware control.
- **Application launcher:** high-contrast search and results, keyboard-first and visually quiet.
- **Native app windows:** host-managed Qt windows retain their specialist content layouts.

## Implementation constraints

- CSS blur is progressive enhancement. Without backdrop filtering, surfaces become more opaque and keep the same contrast.
- Qt windows use translucent widget fills, painted material highlights and crisp controls; this does not claim true compositor blur.
- Reduced-motion preferences suppress nonessential transitions. Static material geometry remains legible.
- The material layer adds no runtime network access, CDN, web font or external image dependency.
- Focus rings, keyboard navigation, 44 px minimum targets where applicable, DPI scaling and contrast take precedence over decoration.
- The system palette stays fixed. Gold `#FFD700` replaces legacy `#FFD400`.

## Maturity boundary

These changes style the Qt host-native Mora adapter and retained browser reference surface. They do not turn either one into a kernel-launched DuckOS desktop session. Reaper policy contracts, DABI64/IPC, process-backed window services, display/input services, a native compositor and a capability broker remain separate integration gates.
