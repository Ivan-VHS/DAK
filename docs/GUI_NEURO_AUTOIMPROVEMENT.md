# GUI Neuro-Autoimprovement — Ivan-VHS/DAK

## Purpose

This profile covers DAK's Reaper policy layer and the host-native Qt 6 desktop. The browser demo is reference material, not the compositor. Keep the kernel, boot, driver and security layers outside GUI-only changes. Use Reaper `.rpr` for DAK policy and examples; Qt/C++ is reserved for the existing host-native shell.

## Closed-loop engineering cycle

1. **Observe:** inspect repository contracts, the actual UI entry points, tests, platform constraints and recent regressions.
2. **Measure:** record reproducible baselines for responsiveness, accessibility, startup, memory and visual consistency where the project exposes those measurements.
3. **Diagnose:** connect each proposed change to a concrete defect or measurable opportunity; do not invent a requirement from aesthetic preference alone.
4. **Propose:** describe expected benefit, affected files, compatibility impact, risk and rollback before editing.
5. **Sandbox:** keep generated patches in a feature branch and a bounded worktree; never run untrusted scripts or install external packages as part of an analysis pass.
6. **Validate:** run the relevant local checks and let repository CI verify platform-specific behavior.
7. **Review:** require human review before merge; no autonomous main-branch writes or automatic merge.
8. **Learn:** keep evidence-backed lessons and update the profile only through a reviewed change.

## Repository-specific surfaces

- `duckos/ui/desktop.rpr`
- `duckos/ui/accessibility.rpr`
- `duckos/ui/theme.rpr`
- `duckos/graphics/compositor.rpr`
- `mora/native/main.cpp`
- `mora/theme.json`
- `tests/test_desktop.py`

## Allowed and protected scope

The machine-readable source of truth is `gui-neuro-profile.v1.json`. Changes outside `allowed_write_paths` are rejected by the profile gate. `protected_write_paths` always win over allow rules.

## Acceptance gates

- Reaper policy checks for .rpr changes
- Qt 6 native desktop build and offscreen smoke test
- Desktop unit tests
- Contrast, focus visibility, keyboard traversal and high-DPI review

## Success measures

- keyboard reachability of all native actions
- visible focus state under all supported themes
- no regression in host-window lifecycle
- no new kernel or privileged behavior from UI-only changes

## Safety and privacy

- The validator is a policy gate, not an AI model. It does not train, call or claim to execute a neural network.
- A model may be used only through an explicitly configured operator-approved runtime. External transfer of source, user data, audio, driver packages or secrets is denied by default.
- Telemetry is disabled. Local logs must omit secrets and personal data.
- Keep user-facing state reversible. Never silently rewrite project data, presets, packages, firmware, drivers or settings.
- No generated patch bypasses tests, code review, ownership rules or CI.
- If a profile surface is unavailable or a required check cannot run, report the limitation instead of treating it as a pass.

## Running the gate

```sh
node tools/validate_gui_neuro_profile.mjs
```

For pull requests, CI also checks every changed path against the repository's allowlist and protected-path list.
