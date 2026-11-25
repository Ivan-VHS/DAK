# Mora Design System — Imperial Noir & Glass

**Canonical source:** DuckOS / Mora · **Theme schema:** mora.theme.v1 · **Version:** 3  
**Normative contract:** [DuckOS Industrial Glass & Digital Physics](docs/DUCKOS_INDUSTRIAL_GLASS_DIGITAL_PHYSICS.md)

Mora is the shared desktop identity for DuckOS and the Ivan-VHS application family. Its visual language is **Imperial Noir & Glass**: architectural black surfaces, white information, semantic duck-gold light and industrial acrylic.

## Identity and semantic palette

| Role | Canonical value | Use |
|---|---|---|
| Canvas | #050505 | Lowest desktop plane |
| Shell / page | #070707 | Structural desktop surfaces |
| Surface | #111111 | Matte and glass panel base |
| Elevated | #1B1B1B | Solid interactive controls |
| Primary text | #FFFFFF / 100% | Main information |
| Secondary text | #FFFFFF / 72% | Supporting copy |
| Tertiary text | #FFFFFF / 42% | Quiet metadata only |
| Accent | #FFD700 | Active state, action, light source |
| Accent hover | #FFE45C | Hover and keyboard focus |
| Border | #333333 or white at 14–24% | Structural edge |
| Selection | #332800 | Restrained warm selection surface |
| Danger | #D32F2F | Critical meaning only, always labelled |

Yellow is a semantic light source, not a background paint bucket. It belongs on focus, selected indicators, primary actions and restrained reflections. Icons on glass are white or yellow except where a critical status must use its semantic status color.

## Material architecture

mora/theme.json is the canonical token source. Each material defines fill, opacity, blur, grain, specular response and border independently.

- **Background glass:** dark base, at least 80% opacity, higher blur and quiet edge light.
- **Content glass:** medium blur and opacity; cards/widgets remain readable.
- **Interactive surface:** dense, high-opacity, zero-backdrop-blur material.
- **Modal glass:** highest isolation with a dark base and controlled specular edge.
- **Fallback:** solid #070707 acrylic, no blur/grain. Reduced Transparency, Saver and unsupported renderers use this path.

Nested backdrop-glass depth is capped at two. Text contrast is checked on the composited surface. Corner radii are architectural: windows/cards 6 px, controls 4 px.

## Digital Physics

Mora uses shared spring/snappy/strict curves. State endpoints are deterministic; transitions are interruptible and driven by committed application state. Direct feedback is about 120 ms, panel motion 180–220 ms and emphasis at most 280 ms. Nonessential motion never exceeds 300 ms.

Reduced Motion removes spatial/ambient movement and commits the final pose immediately. Reduced Transparency removes backdrop filtering and grain. Saver/Eco uses solid surfaces. Essential state feedback remains immediate.

## Native and reference surfaces

- Qt 6 host-native Mora uses dense, high-opacity acrylic-style surfaces, sharp borders and shared colors. QSS alone does not provide true backdrop blur; this adapter uses the deterministic solid/acrylic fallback until a platform compositor adapter exists.
- The browser reference preview uses local CSS backdrop-filter where supported and opaque fallbacks otherwise. It reads theme.json same-origin and keeps static CSS defaults for offline/file previews.
- These are host surfaces, not proof of a kernel-owned compositor. Kernel display/input services, font shaping, accessibility bridge, DABI64/IPC and capability enforcement remain separate implementation gates.

## Quality gates

Ordinary copy targets WCAG AA contrast (4.5:1); primary copy aims for 7:1. Preserve 44 px targets where platform geometry allows, visible keyboard focus, labels, DPI/text scaling and a nonanimated Reduced Motion state. Test the most complex wallpaper, keyboard-only navigation and Reduced Transparency.

60 FPS is a measured floor target, not a promise or ceiling. Record frame pacing, GPU time, memory, blur cache churn, thermal and battery behavior on actual hardware. Do not claim automatic thermal/battery adaptation until a trusted native service supplies those signals.
