# DuckOS Industrial Glass & Digital Physics

**Normative design contract:** DuckOS / Mora · **Runtime tokens:** `mora/theme.json` v3 · **Identity:** Black / White / #FFD700.

This document turns the two 66-rule families into testable invariants. The goal is Digital Physics: movement has weight, surfaces have depth, and the operating system remains precise rather than theatrical.

## A. DuckOS Motion Language — 66 rules

### Elasticity and weight (1–12)
1. **Elastic press:** deform the hit-surface container by 5–8%; never distort text or glyphs.
2. **Scroll inertia:** bounded momentum, friction and a stable final offset.
3. **Loading stretch:** briefly stretch in the direction of progress, then settle.
4. **Modal overshoot:** small, clamped overshoot; exact final geometry.
5. **Tab travel:** animate the active indicator along the path, then settle.
6. **Drag tension:** subtle directional lean/stretch; keep content legible.
7. **Close anticipation:** slight compression before removal, never delay a critical close.
8. **Elastic boundaries:** bounded list-edge feedback; disabled in Reduced Motion.
9. **Cursor trail:** optional, low-opacity, speed-gated and never needed for precision.
10. **Dynamic shadow:** shadow spread/density responds consistently to lift.
11. **Preserve volume:** text, icons and focus indicators retain their proportions.
12. **Notification origin:** reveal from the owning system anchor, not an arbitrary point.

### Anticipation and intent (13–24)
13. **Pre-hover:** subtle edge-light cue without moving the hit target.
14. **Action readiness:** stable state cues, not distracting vibration.
15. **Counter-motion:** a small opposing cue only when it clarifies the next action.
16. **Geometry preview:** skeleton/outline before expensive content; never fake data.
17. **Drag affordance:** visible handles or cursor cue; no idle wobble.
18. **Sound cue:** optional and user-controlled; never mask warnings.
19. **Focus anticipation:** identify destination without prematurely stealing keyboard focus.
20. **Validation preview:** accessible error feedback; never shake on every keystroke.
21. **Menu release:** short detachment from anchor followed by bounded acceleration.
22. **Image readiness:** preparation cue for deliberate zoom only; routine imagery is immediate.
23. **Pointer magnetism:** optional and forbidden where it harms precision or accessibility.
24. **Toggle phases:** thumb movement and track color settle in stages; logical state changes atomically.

### Staging and attention (25–36)
25. **One hero motion:** avoid simultaneous competing movements at the same hierarchy.
26. **Directional light:** #FFD700 edge light draws attention to the active surface.
27. **Negative space:** preserve breathing room around moving/focused elements.
28. **Speed hierarchy:** primary state changes are calm; secondary feedback is brief.
29. **Reading path:** movement supports the scan path.
30. **Modal isolation:** soften/dim inactive context; keep dialog and focus crisp.
31. **Typography staging:** reveal hierarchy without delaying access to text.
32. **Yellow anchor:** reserve gold for action, focus and important state.
33. **Grouped movement:** related entries may use a bounded 20–40 ms stagger.
34. **Noise reduction:** suppress decorative chrome during complex/critical transitions.
35. **Optical centre:** stage key events where users naturally look.
36. **Reading order:** reveal content in its logical reading order.

### Key poses and procedural motion (37–48)
37. **Pose-to-pose states:** explicit open, closed, success, failure and rest poses.
38. **Procedural in-betweens:** bounded spring/easing interpolation between poses.
39. **Stable endpoints:** a given state always resolves to identical geometry.
40. **Reviewed curves:** spatial motion uses approved curves; linear remains valid for factual progress.
41. **Distance-aware timing:** adapt duration to travel distance while bounding velocity.
42. **Interruptibility:** retarget an active transition without snaps or stale callbacks.
43. **Rest pose:** stable, non-drifting idle state.
44. **Controlled variation:** seeded, bounded variance only for noncritical repetition.
45. **Display sync:** align to host presentation cadence; measure actual frame pacing.
46. **Motion debugger:** developer-only 10× slow mode and intermediate-state inspection.
47. **Fallback pose:** cancelled/skipped animation resolves to the committed state.
48. **Motion tokens:** durations, easing and spring values come from shared tokens.

### Follow-through and overlap (49–60)
49. **Layered settling:** content, frame and reflection may settle at different bounded times.
50. **List cascade:** restrained wave; never delay access to critical entries.
51. **Text stability:** no independent text drift that impairs reading.
52. **Plane separation:** subtle, optional background/content/overlay parallax.
53. **Motion trails:** fast noncritical movement only; disabled in Reduced Motion/Eco.
54. **Secondary response:** shadows, highlights and borders react with damped overlap.
55. **Elastic settling:** at most one or two tiny, clamped oscillations.
56. **Render isolation:** background decoration must not block foreground input.
57. **Minimize overlap:** content may fold toward its dock anchor; retain direct fallback.
58. **Boundary stability:** stable glass edges; distortion is optional and quality-gated.
59. **Confirmation weight:** optional 50–100 ms secondary acknowledgement; never delay command/error state.
60. **Cascade budget:** dependent transitions are bounded and cancellable together.

### Timing, arcs and appeal (61–66)
61. **Cubic easing:** use shared spring/snappy/strict curves; no arbitrary per-widget curves.
62. **Arcs:** subtle curved paths where they aid continuity; never bend precision/alignment operations.
63. **Proportional emphasis:** important actions get clearer feedback, not longer theatrics.
64. **Light volume:** controlled specular highlights communicate acrylic thickness.
65. **Solid geometry:** icons preserve perspective, proportion and crispness.
66. **Appeal:** visual finish is clarity, contrast, spacing and restraint.

## B. DuckOS Industrial Glass — 66 rules

### Material and light (1–12)
1. **Layered blur:** background, content and modal have independent blur values.
2. **Fine grain:** static monochrome texture at 2–4%; remove in fallback modes.
3. **Fresnel edge:** subtle brighter rim/inner edge than panel centre.
4. **Perceived thickness:** one-pixel rim, restrained highlight and black shadow.
5. **One light vector:** reflections/shadows share a top-left/top-centre source.
6. **Environmental tint:** slight warm reflection near yellow; base remains black.
7. **Independent controls:** fill, opacity, blur, grain and highlight are distinct tokens.
8. **Gold reflection:** #FFD700 can tint nearby rim; never wash out copy.
9. **Distortion gate:** pixel displacement is optional and off on constrained hardware.
10. **Matte/semigloss roles:** system chrome matte; content/modal slightly glossier.
11. **Backdrop invalidation:** refresh cached blur only when its source changes.
12. **No haze:** preserve silhouettes and large shapes behind glass.

### Contrast and reading (13–24)
13. **WCAG contrast:** ordinary copy ≥4.5:1, primary copy targets 7:1 on the composited surface.
14. **Local scrim:** add a dark text underlay over noisy or moving backdrops.
15. **Legible weight:** Medium/Semibold or stronger for core glass text.
16. **Line rhythm:** generous line-height and spacing.
17. **Line length:** glass text blocks remain easy to scan.
18. **Status meaning:** labels/icons accompany semantic status colors.
19. **Icon outlines:** crisp monochrome icons; filled glyphs need adequate contrast.
20. **Small detail:** core text/controls should not be below 12 px without an accessibility reason.
21. **Gold restraint:** yellow only for active labels, state, focus and key values.
22. **Worst-case backdrop:** test over complex wallpaper, video and documents.
23. **Adaptive opacity:** expose Reduced Transparency and system preference handling.
24. **Dark priority:** dark glass is default; light glass is a tested exception.

### Depth and hierarchy (25–36)
25. **Z-order semantics:** priority uses position, border, shadow and blur role together.
26. **Background glass:** taskbar/sidebar is dark, restrained and low-priority.
27. **Content glass:** widgets/cards use medium blur and legible high-opacity fill.
28. **Interactive glass:** controls are dense solid surfaces with zero backdrop blur.
29. **Modal isolation:** dark overlay, high-opacity pane and crisp focus edge.
30. **Tooltip island:** compact, opaque, high-contrast and fast.
31. **Material grouping:** distinguish groups with density/spacing before decoration.
32. **Black shadow:** translucent black, never a grey haze.
33. **Parallax restraint:** tiny, optional and removable depth offsets.
34. **Focus light:** contained gold accent plus crisp border.
35. **Negative space:** empty dark surface is intentional.
36. **Context adaptation:** stronger scrim for video/high entropy; lighter for stable docs.

### States and interaction (37–48)
37. **Hover:** raise fill or specular edge; glow alone is insufficient.
38. **Press:** reduce shadow, move down ~1 px and increase density.
39. **Focus ring:** crisp 1–2 px gold edge without blur.
40. **Disabled:** remove active specular but preserve readable labels/contrast.
41. **Loading:** honest progress/skeleton; pulsing removed in Reduced Motion.
42. **Drag:** dragged item becomes more opaque than its drop target.
43. **Scroll cue:** high-contrast scroll position/edge feedback.
44. **Notification:** bounded fade/blur reveal and dismissal.
45. **Micro-interaction:** small container-only deformation; never deform text.
46. **Pointer light:** optional, low energy and off in precision/reduced-motion modes.
47. **State persistence:** preserve panel/window state without restore jumps.
48. **Haptic sync:** where native haptics exist, sync with the committed state transition.

### Performance and implementation (49–60)
49. **GPU/native path:** prefer host compositor/backdrop API over CPU blur.
50. **Backdrop cache:** reuse unchanged surfaces and invalidate precisely.
51. **Downsample:** lower-resolution blur only after edge/quality validation.
52. **Nested glass cap:** no more than two backdrop-glass layers.
53. **Simple masks:** rounded rectangles and simple clip paths first.
54. **Solid fallback:** unsupported/constrained devices use opaque #070707.
55. **Platform adapter:** CSS backdrop-filter in preview; native acrylic/vibrancy only where genuinely supported.
56. **Texture lifetime:** release blur buffers when surfaces hide/close.
57. **Battery policy:** reduce blur only when a trusted native power signal reports saver mode.
58. **Thermal policy:** degrade effects only when a trusted native thermal service supplies state.
59. **Reduced Transparency:** obey system and user preference immediately.
60. **Frame budget:** 60 FPS floor target; preserve higher refresh rates where available and measure GPU/memory/frame pacing.

### DuckOS identity (61–66)
61. **Gold as light:** #FFD700 is semantic light/reflection, not generic fill.
62. **Black base:** glass keeps ≥80% dark base opacity.
63. **White hierarchy:** white at 100/72/42% for primary/secondary/tertiary text.
64. **Active border:** crisp 1 px gold edge; 2 px for keyboard focus.
65. **Monochrome icons:** white or yellow except critical status indicators.
66. **Brutalist acrylic:** 4–8 px corners, architectural edges, high contrast; no candy glass.

## C. Runtime mapping

| Token | Value |
|---|---|
| Canvas / shell / surface / raised | #050505 / #070707 / #111111 / #1B1B1B |
| Accent / focus | #FFD700 / #FFE45C |
| Text opacity | 100% / 72% / 42% white |
| Radius | Window/card 6 px; control 4 px |
| Glass opacity | Background 88%; content 88%; modal 94% |
| Blur | Background 28 px; content 18 px; modal 32 px; interactive 0 px |
| Nested blur | Maximum 2 layers |
| Motion | 120 / 180 / 220 / 280 ms; nonessential maximum 300 ms |
| Reduced Motion | No spatial/ambient motion; commit final pose immediately |
| Reduced Transparency | No backdrop blur/grain; solid #070707 fallback |
| Saver/Eco | Zero blur/grain and reduced nonessential movement |

Runtime values are versioned in `mora/theme.json`. The browser preview reads the file same-origin and has static CSS defaults for offline/file previews. Native Qt styling uses the same palette, but QSS does not provide backdrop blur; until a host-compositor adapter exists, native Mora uses a high-opacity acrylic surface rather than claiming pixel blur.

## D. Implemented scope and explicit limits

- **Implemented in the associated UI PR:** v3 material/motion tokens; browser preview token loading; layered browser backdrop materials; zero-blur interactive controls; spring open/close poses; interruptible close/reopen; Reduced Transparency user/system fallback; Reduced Motion and Saver fallback; sharp native Qt acrylic styling and regression checks.
- **Not claimed:** kernel-owned compositor; DWM/Vibrancy/Wayland backdrop backend; Qt backdrop capture; automatic battery/thermal sensors; GPU blur cache; refresh-rate-aware compositor scheduler; full pointer/drag/cursor physics; runtime motion debugger.
- **Reaper follow-up:** material roles, two-layer cap, motion profile and frame-budget invariants belong in Reaper contract modules on the desktop-policy branch, separate from renderer implementation.

## E. Acceptance checklist

- [ ] Measure WCAG contrast on the final composited worst-case wallpaper.
- [ ] Verify keyboard-only focus, 44 px targets, DPI and text scaling.
- [ ] Test OS and Mora Reduced Motion during open/close/reopen.
- [ ] Test OS and Mora Reduced Transparency; verify zero blur/grain.
- [ ] Test Saver/Eco and unsupported-backdrop fallback.
- [ ] Exercise close → reopen interruption; no stale removal callback.
- [ ] Measure 60 Hz and available 120/144/240 Hz pacing on actual hardware.
- [ ] Record GPU time, memory, blur invalidation, thermal and battery before enabling native effects.
- [ ] Keep native Qt fallback labelled acrylic, not true backdrop blur.
