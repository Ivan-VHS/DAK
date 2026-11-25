# DuckOS interaction and application ergonomics standard

**Document ID:** DUCKOS-UX-STD-001  
**Version:** 1.0  
**Status:** Normative design and acceptance standard  
**Scope:** Mora, native DuckOS applications, native desktop services, system dialogs and developer workbenches  
**Source basis:** OS(2).txt, parts I–X of the application ergonomics standard and the desktop UX/HCI standard  
**Related contracts:** [Mora Design System](../MORA_DESIGN_SYSTEM.md), [native implementation roadmap](IMPLEMENTATION_ROADMAP.md), [unified documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md)

This standard turns the supplied ergonomics material into requirements that can be reviewed and tested. It does not claim that a browser panel, visual mock-up or policy record implements native input, accessibility, window management or compositor behavior.

## 1. Product and implementation boundaries

DuckOS has distinct interaction surfaces. Apply the same human-centered principles to all of them, but verify each at its actual runtime boundary.

| Surface | Owns | Must not claim |
|---|---|---|
| Mora browser shell | Application discovery, browser-local panels, presentation preferences and approved local workflows | Kernel isolation, native window management, host-device control or privileged actions |
| Native Duck Desktop | Host-side workbench, native app launch handoff and user-space maintenance workflows | Kernel scheduling, global input security or compositor behavior unless those services are implemented |
| Native desktop services | Window lifecycle, compositor, input routing, display topology, accessibility bridge and system dialogs | Hardware acceleration, multi-seat or multi-monitor guarantees without target evidence |
| Native applications | Task-specific workflows, data presentation, local persistence and user-facing errors | Unbounded permissions or hidden work outside the declared capabilities |
| Reaper | Primary language and contract layer for new DuckOS-owned system code and policy models | Native enforcement merely because a Reaper reference contract passes |

A feature's maturity is reported per capability, not per product name. Use the canonical states from the unified documentation standard. A browser preference is not an operating-system setting; a reference policy is not kernel enforcement.

## 2. Human-centered design invariants

Every application and system surface MUST:

1. Make the current task, context and next safe action understandable without requiring the user to remember hidden state.
2. Respond visibly to accepted input and distinguish acknowledgement from completion of asynchronous work.
3. Preserve user work across validation errors, navigation, interruption and recoverable failure.
4. Make common actions discoverable and repeatable through consistent controls, keyboard equivalents and contextual commands.
5. Reduce unnecessary movement, visual search, decisions, repeated entry and context switching.
6. Expose errors with a concrete cause, affected object and safe next step; never rely on a bare numeric code as the only explanation.
7. Give the user control over notifications, motion, density, privacy and irreversible operations.
8. Avoid deceptive defaults, disguised opt-outs, forced engagement, fake urgency and other dark patterns.
9. Use bounded resource consumption and graceful degradation rather than freezing, silent truncation or data loss.
10. Keep accessibility behavior in the primary component model; do not create a separate, incomplete accessibility-only interface.

The objective is not to remove useful complexity from professional software. It is to remove complexity that does not help the user's task.

## 3. Motor and input ergonomics

### 3.1 Pointer, touch and target geometry

- Place frequent actions near the object or region they affect. Avoid forcing repeated long diagonal pointer travel.
- Make the complete row, label or control hit area clickable where that is the expected interaction, not just a tiny icon.
- Size targets for their input modality and context. Separate destructive and adjacent actions with enough space to prevent accidental activation.
- Keep primary navigation and frequent actions in predictable, reachable locations. On touch layouts, account for one-handed use and avoid placing critical actions only in remote upper corners.
- Use edge and corner placement deliberately for global desktop affordances. The Fitts's-law advantage of an edge target MUST NOT be used to make destructive actions easy to trigger accidentally.
- Support mouse, keyboard, trackpad, touch and stylus where the platform exposes them. Distinguish discrete wheel input from high-resolution and inertial scrolling.
- Provide horizontal scrolling for wide tables, timelines and canvases without trapping vertical scrolling.
- Zoom MUST be anchored to the user's working context where meaningful, such as the pointer position on a canvas.

### 3.2 Keyboard-first operation

- Every primary operation MUST have a keyboard path.
- Tab and Shift+Tab order MUST follow the meaningful visual and reading order. Hidden or disabled controls MUST NOT unexpectedly receive focus.
- Focus MUST remain visible in every theme and density profile. Never remove the focus indicator solely for visual cleanliness.
- Dialogs, lists, tables, tabs, trees, menus and splitters MUST expose documented keyboard behavior.
- Global shortcuts MUST be centrally registered and MUST NOT silently shadow platform or application conventions.
- Provide an editable shortcut map and conflict diagnostics for user-remappable commands.
- A command palette SHOULD expose command names, short descriptions, current shortcuts and disabled reasons. A command palette supplements; it does not replace discoverable menus or accessible controls.
- Escape MUST have a predictable cancellation/close behavior where safe. Destructive operations MUST NOT be bound to an accidental default Enter action.

### 3.3 Input state and feedback

Input acknowledgement SHOULD appear in the next available frame. For asynchronous operations, acknowledge immediately, then report progress, completion, cancellation or failure separately. Repeated clicks MUST NOT create duplicate destructive operations.

## 4. Desktop spatial composition and window behavior

- Use a central work area with optional dockable side and lower panels for professional tools.
- Allow panel resizing, hiding and restoring without losing the underlying task state.
- Support named workspaces for distinct tasks such as editing, debugging and analysis.
- Persist window bounds, maximized state, panel layout, column widths and relevant tabs only through a versioned user preference model.
- On display topology changes, validate saved bounds against active displays and move an off-screen window into a visible work area.
- Support mixed display scale and orientation without clipping controls or rendering text at unreadable sizes.
- Use modal dialogs only when a decision blocks the current operation. Prefer inspectors, non-modal panels and concise notifications for ordinary configuration and status.
- Confirmation labels MUST name the actual action. For example, use "Save", "Discard" and "Cancel", not an ambiguous "OK".
- A destructive button MUST be visually distinct and MUST NOT be the unintended default action.
- Restoring a workspace MUST be reversible and MUST NOT reopen untrusted external content automatically.

Mora's browser window model is a design and workflow surface. Native window placement, focus isolation, display migration and compositor guarantees are delivered only by native services with platform tests.

## 5. Visual ergonomics and information density

### 5.1 Hierarchy and scanability

- Establish one primary task/action per surface, with secondary actions grouped by meaning.
- Use spacing, alignment, typography and grouping to create scan paths; do not make every element equally prominent.
- Keep long-form reading columns within a comfortable measure. The supplied desktop guidance uses approximately 60–85 characters as a target range, adjusted for font and viewport.
- Prefer stable layouts that do not jump when content loads, validation appears or a status changes.
- Keep critical status distinguishable by text and icon as well as color.
- Use tables and lists when users need comparison or scanning; use cards only when the card structure adds meaningful context.

### 5.2 Density profiles

Provide three predictable density profiles where the product type benefits from them:

| Profile | Best use | Behavior |
|---|---|---|
| Comfortable | Reading, onboarding, settings and low-frequency tasks | More whitespace, larger targets and less simultaneous detail |
| Standard | General productivity and everyday workflows | Balanced spacing and information volume |
| Compact | IDEs, logs, tables, DAWs, engineering and monitoring tools | More visible rows and controls without sacrificing legibility or focus |

Density MUST NOT shrink text below the product's tested readability floor, remove keyboard focus, hide status text or reduce important hit targets. Changing density MUST NOT destroy user layout preferences; store a profile plus explicit overrides.

### 5.3 Duck visual identity

- The shared DuckOS/Mora shell identity remains black, white and duck-yellow, using the canonical tokens in MORA_DESIGN_SYSTEM.md and mora/theme.json.
- Status colors are semantic and restrained. Green, red and blue may indicate status classes, but color alone MUST never carry meaning.
- App-specific identity is scoped to the application; it MUST NOT fork the system shell palette or interaction rules.
- Typography, spacing, surfaces, border, elevation and motion MUST use semantic tokens rather than scattered literal values.
- Fonts and assets used by the shipped product MUST be local, licensed and versioned. No product-critical external font/CDN dependency is permitted.

### 5.4 Contrast, scaling and environmental variation

- Text, icons, focus rings, control boundaries and disabled states MUST remain distinguishable in supported light, dark, high-contrast and increased-contrast profiles.
- Do not equate dark mode with accessibility. Provide contrast adjustments and a readable light alternative where the product supports both.
- Support text scaling and responsive reflow without overlapping, clipping or losing essential controls.
- Verify screens at common scaling factors and non-default display DPI, not only at the developer's monitor settings.
- Use text labels, shape and icon in addition to color for warnings, success and errors.

## 6. Cognitive ergonomics and navigation

- Prefer recognition to recall: show recent items, valid examples, inline format hints, autocomplete and contextual help.
- Preserve the user's entered values and location after a validation error.
- Keep filters, selection, search context and progress visible when navigating into and out of detail views.
- Use meaningful names from the user's task domain; internal module jargon is not a user-facing label.
- Make the current location clear with a section title, selected navigation item or breadcrumbs when useful.
- Keep frequent tasks shallow and provide a reliable route back without losing progress.
- Search MUST tolerate reasonable spelling and formatting variation where the dataset and performance budget allow it. Filters MUST show active conditions, result count where available and a clear reset path.
- Use progressive disclosure: show the useful default path first and put advanced controls in an explicitly named advanced area.
- Use safe defaults, explain meaningful consequences and avoid presenting a large list of equivalent choices without grouping.
- Notifications MUST be grouped and user-controlled. Urgent alerts need a reason and a priority; routine updates MUST NOT interrupt focused work.
- Do not use artificial countdowns, forced subscription choices, disguised opt-outs or other manipulative interaction patterns.

## 7. Interaction states, latency and recovery

Every reusable control and every major screen MUST define the states that apply to it:

- idle, hover, pressed and focused;
- disabled, including a reason where the reason is not obvious;
- pending/running, with progress and cancellation where possible;
- empty and no-results, each with an explanation and a useful next action;
- success, with a concise confirmation;
- validation error and operation failure, with recovery guidance;
- offline, permission-denied, resource-exhausted and degraded dependency states where applicable.

### 7.1 Responsiveness

- Acknowledge local input before starting expensive work.
- Keep long-running work off the UI/event thread.
- Bound queues, retries, memory, file sizes and waiting time. Provide cancellation for operations that can be cancelled safely.
- Prefer event-driven updates and incremental rendering over continuous polling and full-screen redraws.
- Use determinate progress when the amount of work is knowable. Use an inline activity state for short indeterminate work; do not show an indefinite spinner as a substitute for operation state.
- Record frame-time distributions and input-to-visual-feedback latency on declared target hardware. A 60 Hz display has a 16.7 ms frame interval; higher refresh rates have proportionally tighter frame budgets. Do not claim a frame-rate target without measurements.
- The first DuckOS target profile MUST publish P50/P95/P99 interaction and frame-time measurements rather than a universal performance promise.

### 7.2 Undo, drafts and failure recovery

- Prefer Undo for reversible actions over interrupting the user with repeated confirmation dialogs.
- Irreversible actions require a confirmation that names the affected object and consequence.
- Autosave or preserve drafts for user-authored work. The user MUST be able to tell whether a change is saved, pending or only local.
- Recoverable network, device or storage failures MUST NOT silently erase text, filters, selection or in-progress edits.
- Restore operations MUST validate their source and provide a preview of the changes before replacing user data.
- A crash or process restart MUST leave enough state to explain what completed and what remains uncertain.

## 8. Accessibility and universal design

- Provide semantic roles, accessible names, descriptions, reading order and state announcements for assistive technologies.
- Ensure keyboard-only operation and visible focus for all essential workflows.
- Support text scaling, increased contrast, reduced motion and non-color status encoding.
- Provide text alternatives for meaningful graphics and captions/transcripts for audio/video content where those media are part of the product.
- Do not make sound or haptics the only confirmation of an action. Provide simple mute/disable controls and respect platform settings.
- Respect operating-system settings for motion, contrast, focus, text scale and input modality.
- Test with keyboard-only navigation and at least one screen-reader workflow on each declared native desktop platform before calling the relevant accessibility capability verified.
- Touch and pointer targets MUST be measured on actual devices; the smallest supported target and spacing are recorded in the platform profile.

## 9. Context, privacy and user control

- Preserve work through focus changes, app suspension, display changes and intermittent connectivity.
- Work offline for local tasks unless the operation explicitly requires a network resource.
- Explain when an action sends data outside the device and request consent before new data collection or transmission.
- Keep diagnostic telemetry local by default, bounded, inspectable and opt-in for export.
- Make notification categories, schedules and quiet periods user-configurable.
- Do not restart, update, close documents or change system settings without an explicit user-visible policy and appropriate approval.
- Do not make an app dependent on a cloud service for a local operation that can be completed on-device.

## 10. Ergonomics verification and release gates

Ergonomics is measured as task performance and error recovery, not only visual preference.

For each significant application workflow, maintain a test record containing the task, target device/platform, viewport/display scale, input modality, locale, density profile, test data, observed result and issue reference.

Minimum evidence for a release candidate:

| Gate | Required evidence |
|---|---|
| Task clarity | A new user can identify the screen purpose and primary action without relying on hidden developer knowledge |
| Keyboard | Every primary workflow can be completed without a pointer; focus order and shortcuts are tested |
| Pointer/touch | Hit areas, spacing, scroll, zoom and accidental-action protection are tested on declared devices |
| Visual | Contrast, scaling, text measure, density and non-color status encoding are checked |
| State coverage | Empty, loading, success, validation, failure, offline and permission-denied states are covered where applicable |
| Data safety | Draft retention, Undo, cancellation and restore are tested |
| Multi-display | Saved geometry, unplug/replug and DPI changes are tested for native multi-display claims |
| Motion | Reduced Motion suppresses non-essential movement and does not remove information |
| Accessibility | Semantics, reading order, focus, text scaling and assistive-technology workflow have recorded evidence |
| Performance | Input acknowledgement, P50/P95/P99 frame times, idle CPU and memory are recorded on a named target |
| Privacy | Network, telemetry, permission and export behavior are documented and tested |

Track time-to-completion, successful completion on first attempt, error/retry rate, accidental activation, navigation depth, recovery success, input-to-feedback latency and frame-time percentiles. Collect only data needed for the stated measurement, and do not silently upload usability telemetry.

## 11. Implementation mapping

| Workstream | Required work | Dependency / acceptance |
|---|---|---|
| Mora and app panels | Apply shared tokens, states, keyboard paths, responsive layouts, preserved drafts and error recovery | Browser contract tests; no claim of native accessibility enforcement |
| Native Duck Desktop | Focus model, keyboard command routing, panel resizing, workspace persistence and display-safe geometry | Host UI tests and multi-display tests |
| Native compositor | Isolated surfaces, damage tracking, frame scheduling, output management and safe display-loss recovery | Native rendering and compositor integration tests |
| Input service | Device event normalization, focus routing, hotplug, pointer/touch/stylus and secure input boundaries | Device fixtures and native hardware tests |
| Accessibility service | Semantic tree, screen-reader bridge, focus announcements and platform settings | Per-platform assistive-technology verification |
| Kernel and services | Scheduling priority classes, IPC backpressure, capability checks and resource quotas that protect interactive work | Kernel/service tests; UI responsiveness cannot be inferred from policy-only models |
| Reaper | Typed interaction contracts, diagnostics and deterministic policy modules for native DuckOS services | Reaper compiler/runtime tests and native ABI conformance |
| BAV | Clear alerts, explainable actions, reviewable quarantine and reversible restore | BAV-specific UX and security gates in BAV_SECURITY_BUNDLE_V1.md |

## 12. Source traceability

This standard consolidates, without silently replacing, the supplied source's main areas:

- Application ergonomics parts I–X: physical/sensorimotor interaction, cognition, navigation, states/errors, accessibility, context/ethics, measurement, response latency, scanning, memory, mobile/desktop/web/data workflows and screen checklist.
- Desktop UX/HCI standard: Fitts's law, keyboard-first operation, command palette, scrolling/zoom, large displays, docking/workspaces, window restoration, modal restraint, density, typography, color, Undo/Redo, responsiveness and OS integration.
- Correct operating-system rules: fault containment, deterministic behavior, observability, minimal trusted base, isolation, memory protection, resource limits, network hygiene, integrity, recovery and user sovereignty.
- Reaper sections: contract discipline, deterministic stream processing, bounded buffers, backpressure, diagnostics and verified self-host evolution. The Python and C examples in the source are references to review, not production-ready DuckOS implementations.

## 13. Change control

Changes to this standard MUST preserve the distinction between specification, implementation and verification. New requirements need an owner, identifier, applicable surface, measurable acceptance evidence and migration impact. Changes to global visual tokens or keyboard conventions require an impact review across Mora and native applications.
