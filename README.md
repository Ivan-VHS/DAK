# DuckOS — Mora unified desktop

**DuckOS** is the operating-system project. **Mora** is its unified desktop shell and visual language: one home screen, one app surface, one control center and one consistent interaction model.

The desktop keeps the existing indigo-to-rose sunset, layered hills, warm glass panels and compact dock. The seven original first-party apps remain in place; six system tools extend the same environment.

## What is implemented in the shell

- **Mora desktop:** live local clock, status bar, responsive workspace, wallpaper, app grid, widgets, dock, draggable windows and running indicators.
- **Seven applications:** Cockos, Kavun, Ka-bon, Gloverty, Po, Illidia and Unify.
- **Mora AI:** an offline intent planner for a small allowlist of local settings and app-opening actions. It previews the plan and waits for explicit approval. It is not an LLM and does not execute shell commands.
- **Sentinel:** deny-by-default capability preferences for microphone, camera, location, files, network and clipboard. They are stored in the shell profile; a native capability broker is still required to enforce them for OS processes.
- **Restore:** versioned local snapshot and restore of Mora preferences, plus an A/B update plan preview. It does not update or roll back the OS image.
- **Bridge:** local PE and ELF header inspection, including common x86, x64 and ARM64 machine identifiers. It never executes the selected file.
- **Control:** persistent Mora focus, motion and resource-profile preferences. These do not change kernel scheduling or hardware power states.
- **Proof:** local SHA-256 calculation for a selected file. C2PA signatures and provenance manifests are not yet verified.
- **Keyboard access:** Ctrl+K opens Mora AI; Escape closes the top window.

## Start and test

Open **mora/index.html** in a modern browser. No network service or package install is required for the shell.

Run **npm test** with Node.js 18 or newer. Tests cover the desktop contract, preference validation, intent allowlisting, recovery snapshots and PE header inspection. They are not a substitute for browser automation, kernel tests or boot-image validation.

## System direction

The shell presents the 2026 OS design directions as explicit service contracts, not as fictional hardware access. The status of each capability is recorded in **mora/system-policy.json**.

| Area | Current shell state | Native work still required |
|---|---|---|
| AI-native scheduling and local NPU models | Not connected | model runtime, hardware discovery and kernel resource scheduler |
| Intent UI and approval zones | Limited local planner with preview/approval | privileged action broker, policy audit and rollback |
| Immutable updates | Local settings snapshot only | signed image pipeline, A/B slots, boot verification and recovery |
| Sandboxing and zero trust | Shell preference profile only | process isolation, capabilities, syscall policy and device broker |
| Provenance | SHA-256 only | C2PA parsing, signer trust and verification chain |
| Adaptive workspace | Responsive browser layout | native compositor, display migration and XR runtime |
| Multimodal input | Keyboard, pointer and touch | speech, gesture, accessibility and permission services |
| Compatibility | PE/ELF inspection | Win32/NT, graphics translation, audio, anti-cheat and launcher integration |
| Declarative configuration | Versioned shell preference object | package, service and system desired-state engine |
| Energy awareness | Selectable UI profile | CPU/GPU/NPU scheduling, thermal policy and VRR |

No browser feature is described as a kernel, driver or hardware implementation. In particular, EXE inspection is not EXE execution, a visual permission switch is not process isolation, and a settings snapshot is not an immutable OS rollback.

## Project structure

| Path | Responsibility |
|---|---|
| mora/index.html | Desktop structure and app launchers |
| mora/styles.css | Mora visual system and responsive layout |
| mora/app.js | Window manager, app panels and shell interactions |
| mora/core.js | Validated preferences, intent allowlist, PE/ELF inspection and hashing |
| mora/apps.json | First-party app and system-tool registry |
| mora/system-policy.json | Capability maturity and native-service boundaries |
| mora/app-manifest.schema.json | External app manifest contract |
| docs/MORA_INTEGRATION.md | Security and native integration requirements |
| tests/ | Dependency-free contract and core tests |

## Native integration sequence

1. Bind Mora windows to the DuckOS session manager and compositor.
2. Implement the capability broker and per-process sandbox before granting native app permissions.
3. Connect signed package metadata, an immutable system slot and a tested recovery path.
4. Connect the compatibility runtime only after Win32, graphics, audio and prefix contracts pass.
5. Attach local inference and resource scheduling through versioned kernel/service APIs.
6. Add C2PA verification and device-level power controls with auditable provider results.

## Attribution

Project author/developer: **Ivan-VHS**. Preserve the authorship and license notices of all existing contributors and dependencies.
