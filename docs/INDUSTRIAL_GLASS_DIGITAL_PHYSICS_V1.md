# DuckOS Industrial Glass & Digital Physics v1

**Status:** normative UI contract with a Mora browser-shell implementation and Reaper policy adapters.  
**Palette:** Imperial Noir · White · Gold `#FFD700`.  
**Scope:** system chrome, Mora windows, cards, dock, notifications, controls and shell motion.

This specification adapts the supplied 66 motion rules and 66 glass rules into a desktop interaction language. It does not turn every cinematic effect into a requirement. Accessibility, deterministic input, legibility, latency and power limits outrank visual flourish.

## 1. Material identity

DuckOS glass is industrial acrylic: dark, dense, sharply bounded and readable. It communicates layer order, not decoration.

| Token | Value | Contract |
|---|---:|---|
| Canvas | `#050505` | Base workspace |
| Surface | `#101010` | Opaque material fallback |
| Elevated | `#181818` | Raised opaque fallback |
| Primary text | `#FFFFFF` | Full-strength text |
| Secondary text | `rgba(255,255,255,.70)` | Supporting copy |
| Tertiary text | `rgba(255,255,255,.40)` | Metadata only; never essential instructions |
| Action / active edge | `#FFD700` | One current focal point |
| Hover | `#FFE45C` | Temporary pointer/focus feedback |
| Glass fill | `rgba(7,7,7,.78)` | Dark glass, at least 78% opaque |
| Strong glass fill | `rgba(7,7,7,.86)` | Chrome and modal isolation |
| Glass blur | `18px` | Content surface |
| Strong blur | `22px` | Chrome/modal surface |
| Grain opacity | `0.035` | Monochrome local texture |
| System radius | `8px` | Architectural edge |
| Control radius | `6px` | Solid, tactile controls |

White alpha values form the text hierarchy; don't substitute arbitrary gray hex values. Status colors remain semantic (success, warning, error and information) and always have a textual/icon equivalent. Gold is not used for long paragraphs.

## 2. Glass surface classes

- **Structural glass:** status bar and dock; strong dark fill, 18px blur, subdued rim.
- **Content glass:** widgets/cards; 78% dark fill, 18px blur, restrained grain and a soft top-left specular line.
- **Modal glass:** application windows; 86% dark fill, up to 22px blur, isolated backdrop and clear boundary.
- **Notification glass:** toast surface; compact, high-contrast, short-lived and non-blocking.
- **Hard controls:** buttons, toggles, inputs and draggable handles; no backdrop blur, high-opacity fill, visible border and crisp focus. Glass must never make a control feel soft or uncertain.

The shell uses a local, tiled noise asset. It is a low-amplitude texture, not animated film grain. The light vector is top-left. A warm gold reflection may appear near an actual gold control, but there is no global gold haze.

Only the five high-value material roles above may request backdrop blur. No blur is nested inside another blur. No animated backdrop filters, CPU blur, external texture/CDN, runtime font fetch or remote theme lookup is allowed. Opaque fallbacks are first-class, not error states.

## 3. Digital Physics — 66 motion rules

The numbered rules below are the canonical interpretation of the 66 supplied animation principles. "Use" means the behavior is allowed when it improves comprehension; it does not mean every component must animate.

### I. Elasticity and mass (1–12)

1. **Container compression:** press feedback may compress the surface layer; text and glyph geometry stay undistorted.
2. **Scroll inertia:** preserve native, user-controlled scrolling; bounded overscroll may settle gently, never trap the user.
3. **Progress acceleration:** loading may ease into motion, while its value remains sourced from real work.
4. **Window arrival:** a new window may overshoot by a very small amount, then settle to its fixed pose.
5. **Tab travel:** selection indicators travel between tabs; the selected state changes immediately and semantically.
6. **Drag tension:** a dragged tile may emphasize its surface, but pointer coordinates and drop targets remain exact.
7. **Window departure:** close motion contracts the surface before removal; it must not delay command completion.
8. **Edge resistance:** list boundaries provide restrained feedback and always permit keyboard navigation.
9. **Pointer trail:** disabled by default; no cursor trail may obscure precision work or text.
10. **Lifted shadow:** elevation may change shadow spread/opacity in sync with a surface lift.
11. **Volume integrity:** deform only container/background layers, never text, icons or data visualizations.
12. **Notification origin:** notifications may emerge from their owning status region, not an arbitrary screen point.

### II. Anticipation and action clarity (13–24)

13. **Pre-hover:** a subtle edge/light response is permitted; no delayed or predictive hit testing.
14. **Action readiness:** validation and pending state are explicit; don't vibrate a button to manufacture urgency.
15. **Counter-motion:** use only where it clarifies a large spatial transition; never add a twitch to routine controls.
16. **Geometry preview:** heavy asynchronous panels may show a stable skeleton with known dimensions.
17. **Draggable affordance:** handles, cursor and keyboard instructions identify movable surfaces.
18. **Sound anticipation:** no sound is required; audio cues are user-controlled and never play merely to decorate motion.
19. **Focus anticipation:** preserve keyboard focus and announce the destination; do not steal focus before activation.
20. **Validation feedback:** validate at a meaningful boundary; don't shake or recolor a field before its error is known.
21. **Menu release:** menus may use a short directional reveal, with immediate hit-test readiness.
22. **Image preparation:** image expansion may use a restrained scale/fade when it communicates hierarchy.
23. **Cursor magnetism:** disabled for normal desktop controls; don't move the pointer or distort target geometry.
24. **State telegraphing:** toggles expose the pending/selected state with a clear track, thumb and accessible state.

### III. Staging and hierarchy (25–36)

25. **One focal action:** coordinate equal-priority transitions; avoid competing gold pulses.
26. **Light as direction:** gold edge light identifies the current active surface, not every surface.
27. **Negative space:** maintain separation around moving surfaces and important text.
28. **Speed hierarchy:** micro-feedback is fast; spatial changes are slower but remain below 300ms.
29. **Reading path:** stage content in the same order that keyboard and screen-reader users encounter it.
30. **Modal isolation:** dim the workspace and increase backdrop separation without hiding context completely.
31. **Typography staging:** reveal the container first; headings and content may follow with a tiny, bounded stagger.
32. **Color anchors:** reserve gold for the current focus/selection/action; keep surrounding content neutral.
33. **Grouped motion:** related items may move as a coordinated group with small deterministic stagger.
34. **Noise reduction:** do not hide required status, navigation or escape controls during transitions.
35. **Optical centre:** place focal actions by visual balance while retaining predictable layout and focus order.
36. **Reading direction:** content reveal follows the logical reading order, not arbitrary spectacle.

### IV. Determinism and timing (37–48)

37. **State keyframes:** open, closed, selected, disabled, success and error states have explicit end poses.
38. **Procedural interpolation:** physics may interpolate between poses; it never decides application state.
39. **Stable endpoints:** start/end poses are deterministic; no random offsets or unrepeatable layout.
40. **Non-linear easing:** use reviewed spring/snappy curves for motion; progress values and data remain numerically linear.
41. **Distance timing:** distance may influence duration, but the system caps decorative transitions at 280ms.
42. **Interruptibility:** a new input cancels or retargets the current transition without stale callbacks or jumps.
43. **Rest pose:** every component has a static, non-drifting idle state.
44. **Procedural variation:** disabled for system chrome; repeated feedback remains deterministic and testable.
45. **Refresh sync:** native renderers align with the frame scheduler; the browser shell relies on the browser compositor.
46. **Debug scaling:** developer tooling may expose a 10x inspection scale; it is never the shipped user default.
47. **Fallback poses:** reduced motion, cancellation and missed frames land directly on the correct target state.
48. **Motion tokens:** timings, curves, scale and spring constants live in the canonical theme/policy tokens.

### V. Follow-through and layered motion (49–60)

49. **Secondary follow-through:** a specular highlight may settle after the main surface, without delaying input.
50. **List stagger:** list reveal may use a deterministic 20–40ms offset; large lists render without serial animation.
51. **Text stability:** text stays anchored to its readable container; no independent scroll drift.
52. **Depth planes:** background, glass and overlay may use restrained parallax only when it does not affect pointer/focus mapping.
53. **Motion trails:** disabled for OS chrome; blur trails are too expensive and reduce precision.
54. **Secondary surface response:** rims and shadows may react after a window moves; no permanent ambient movement.
55. **Settling:** springs use bounded velocity and settle thresholds; no endless oscillation.
56. **Render isolation:** a native compositor must isolate expensive layers; current Mora CSS makes no claim about independent GPU threads.
57. **Minimize overlap:** content may fade/contract toward an owning task icon only when a stable origin is available.
58. **Liquid boundaries:** disabled in system chrome; resize edges remain geometrically stable.
59. **Completion feedback:** confirmation follows a committed state change, never precedes it or delays it.
60. **Cascade:** dependent UI updates follow the authoritative state in deterministic order.

### VI. Finish and appeal (61–66)

61. **Slow-in/out:** use approved easing curves; avoid default linear interpolation for spatial movement.
62. **Meaningful arcs:** curved trajectories are optional for large, spatially meaningful transitions only.
63. **Functional emphasis:** destructive or consequential actions are visually explicit and still require their normal confirmation/authorization.
64. **Light-built volume:** volume comes from rim, specular highlight and shadow, not excessive blur.
65. **Geometric integrity:** icons, text and hitboxes keep their proportions and exact bounds.
66. **Appeal:** clean contrast, crisp edges, low visual noise and reliable interaction define the DuckOS character.

## 4. Industrial Glass — 66 material rules

### I. Material and light (1–12)

1. **Layered material:** blur, local grain and a rim are separate controls; never collapse them into a single blur value.
2. **Grain:** use a local monochrome texture at 3.5% opacity; no animated noise.
3. **Fresnel rim:** brighten edges with a restrained inner border/specular line.
4. **Thickness:** imply thickness with a 1–2px edge and layered shadow, not a thick bevel.
5. **One light vector:** highlights and shadows share the top-left light direction.
6. **Ambient tint:** the dark material may carry a subtle warm reflection; it remains predominantly black.
7. **Opacity/blur separation:** tune fill opacity independently from blur radius.
8. **Accent reflection:** gold reflection is local to a real gold element and remains low amplitude.
9. **Distortion:** geometric refraction is deferred until a native compositor can bound it safely.
10. **Matte/gloss roles:** structural chrome is matte; modal surfaces may be slightly more specular.
11. **Live response:** move/resize may update blur only within the compositor's measured frame budget.
12. **No smear:** retain background silhouettes and large color regions; opaque surfaces are preferred over muddy blur.

### II. Reading and contrast (13–24)

13. **WCAG:** normal text targets at least 4.5:1 against the effective surface; primary text aims for 7:1.
14. **Local backing:** put a darker local backing behind text when imagery is busy.
15. **Weight:** primary labels use readable medium/semibold weights; avoid hairline text.
16. **Line height:** preserve comfortable line height on translucent surfaces.
17. **Line length:** constrain long copy; do not stretch text across busy backdrops.
18. **Status:** status colors are contrast-checked and accompanied by icon/label.
19. **Icons:** use crisp white/gold monochrome icons on shell chrome; product data colors remain meaningful.
20. **Small text:** essential labels must not fall below 12 CSS px in the shell.
21. **Gold text:** use gold for concise labels, active actions and key values, not long body copy.
22. **Worst-case background:** review against high-detail wallpaper/media as well as the default dark desktop.
23. **Adaptive transparency:** expose an explicit reduced-transparency preference and an opaque OS-preference fallback.
24. **Dark-first:** the canonical shell is dark; light glass is not a second theme.

### III. Elevation and composition (25–36)

25. **Z-order:** importance is conveyed by fill, edge, shadow and layer order together.
26. **Structural glass:** status bar/dock use strong fill and low visual emphasis.
27. **Content glass:** cards/widgets use medium blur and a dark base.
28. **Hard controls:** buttons/inputs/toggles use minimal or no blur and firm boundaries.
29. **Modal isolation:** dim and soften the workspace; keep the active window crisp.
30. **Tooltips:** use compact high-contrast opaque/strong-glass islands and short entry timing.
31. **Grouping:** separate sections with material density and spacing before adding divider lines.
32. **Shadow:** use dark, ambient shadows, not flat grey halos.
33. **Parallax:** optional and disabled under reduced motion/Eco; never changes hit testing.
34. **Focus light:** gold glow is optional; the crisp focus border is mandatory.
35. **Space:** leave empty glass areas; do not fill every panel with widgets.
36. **Content adaptation:** video/document backdrops may select a stronger opaque fill; no expensive live scene analysis.

### IV. Interaction (37–48)

37. **Hover:** raise the edge/light slightly, not the opacity of every object at once.
38. **Press:** reduce shadow and shift the surface by at most 1px; text remains stable.
39. **Keyboard focus:** use a crisp, high-contrast gold outline with a visible offset.
40. **Disabled:** lower contrast/opacity and remove active shine while keeping state legible.
41. **Loading:** use stable skeletons/progress based on real work; no decorative indefinite spinner over blur.
42. **Drag:** make the dragged item more opaque and preserve exact coordinates.
43. **Scroll:** keep scrollbars and position feedback visible on glass.
44. **Notifications:** reveal with a short opacity/position transition; remove the reverse transition without trapping focus.
45. **Micro-interaction:** use bounded surface translation/overlay compression; avoid warping text.
46. **Cursor light:** optional and off by default; no persistent pointer trail.
47. **Persistence:** save user material preferences locally and normalize unknown values.
48. **Haptics:** not assumed on desktop; when hardware feedback exists, state and motion must remain synchronized.

### V. Performance and implementation (49–60)

49. **GPU path:** use the platform/browser compositor backdrop path; do not implement CPU blur.
50. **Static caching:** reuse stable material textures where the renderer supports it; invalidate on content/size changes.
51. **Resolution scaling:** half-resolution blur is a native-renderer optimization, not a CSS promise.
52. **Nested glass:** never blur a glass child inside a glass parent; no more than two material planes.
53. **Masks:** prefer simple rectangular/rounded-rect clipping over complex blur masks.
54. **Fallback:** use opaque `#101010`/`#070707` surfaces when blur is unavailable or disallowed.
55. **Native mapping:** map to native backdrop APIs only when the target OS adapter supports and verifies them.
56. **Lifetime:** release native textures/backdrop resources when hidden or destroyed.
57. **Power:** reduce blur for the explicit saver profile; hardware battery detection remains a native-service responsibility.
58. **Thermal:** thermal-driven quality reduction requires real sensor telemetry; never fabricate it.
59. **Reduced transparency:** the OS preference and explicit Mora setting immediately select opaque surfaces.
60. **Benchmark:** target 60fps on declared hardware; record a measured result before claiming a pass.

### VI. DuckOS identity (61–66)

61. **Gold light:** `#FFD700` behaves as a local warm light source, not a background wash.
62. **Black density:** glass fill remains at least 70% opaque; canonical fills are 78%/86%.
63. **White hierarchy:** primary/secondary/tertiary text use white at 100%/70%/40%.
64. **Active edge:** active/focused glass receives a crisp 1px gold inner edge plus accessible focus outline.
65. **Monochrome shell glyphs:** shell icons are white or gold; specialist content retains its functional colors.
66. **Brutalist glass:** use 4–8px radii, architectural edges, strong contrast and no candy-like bloom.

## 5. Motion tokens and safety limits

| Token | Default |
|---|---:|
| Instant | 0ms |
| Micro | 100ms |
| Fast | 140ms |
| Standard | 180ms |
| Spatial | 220ms |
| Emphasis | 280ms |
| Maximum decorative transition | 280ms |
| Spring curve | `cubic-bezier(0.34, 1.12, 0.64, 1)` |
| Strict curve | `cubic-bezier(0.65, 0, 0.35, 1)` |

The distance-based timing rule is bounded: a short 10px movement resolves in about 150ms; a 500px movement is capped at 280ms. The supplied 400ms example is not used for routine OS interaction because it conflicts with the 300ms responsiveness limit.

System reduced-motion preference overrides local settings. Reduced motion removes spatial transforms, parallax, trails, stagger, continuous effects and spring settling; essential state changes remain immediate (or at most 80ms where an acknowledgement is needed). Reduced transparency disables backdrop blur, noise and translucent fills immediately. Eco/saver disables optional material texture and halves blur. Neither setting may suppress required status, keyboard focus or task completion.

The spring solver is deterministic, finite, cancellable and frame-delta-bounded. No random procedural variation, cursor magnetism, pre-validation shaking, blur trails or liquid borders are enabled in system chrome.

## 6. Implementation and maturity

- **Implemented in Mora:** dark layered glass on the five shell material roles; local grain; top-left rim/highlight; opaque fallbacks; responsive blur budget; reduced-transparency preference; reduced-motion and Eco fallbacks; keyboard focus; short open/close/press transitions.
- **Defined in Reaper policy:** canonical glass roles/blur decisions, motion token durations/easing, bounded spring integration and frame-budget state.
- **Not claimed as implemented:** native GPU compositor, independent render threads, half-resolution native blur, battery/thermal sensor adaptation, live distortion/refraction, haptic output, cursor magnetism/trails or native DWM appearance. Those require their own runtime adapters and evidence.

Mora is currently a browser-based desktop shell. This implementation improves its actual UI and establishes the contracts for the future native shell; it does not claim the browser implementation is already a kernel compositor.

## 7. Acceptance gates

1. Run the Mora Node test suite and verify token/schema compatibility.
2. Verify blur-supported and no-blur browsers; the opaque state must remain readable.
3. Verify explicit reduced transparency, system reduced transparency, forced-colors and reduced motion.
4. Verify keyboard-only focus, 44px targets, Escape and window close behavior.
5. Test the default wallpaper and a high-detail background; retain at least 4.5:1 normal-text contrast.
6. Measure the five material roles at 60fps on target hardware before publishing a performance claim.
7. Review 100%, 150% and 200% scaling plus mobile/narrow layouts.
8. Mark unrun visual/native checks as pending; don't infer success from unit tests.
