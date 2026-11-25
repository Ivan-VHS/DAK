# Reaper-native Duck Desktop policy v1

**Status:** executable Reaper policy contracts; native desktop services remain separately gated.  
**Owner:** DuckOS.  
**Policy language:** Reaper.  
**Display contract:** Duck Display Protocol (DDP) v1.

## Scope

This change adds a Reaper-first policy layer for the native Duck Desktop. It extends the existing DuckOS UI and security contracts rather than introducing a second window protocol or a browser-owned desktop runtime.

The policy modules cover DDP surface descriptors, ownership, buffer bounds, configure serials, damage rectangles and focused input routing; window ownership, lifecycle, geometry, focus eligibility, stacking layers, notification-safe placement, tiling and fullscreen capability checks; taskbar visibility, application grouping and Jora launch admission; app-manifest trust, resource ceilings, opaque per-app VFS roots, filesystem/network grants and child capability attenuation; Jora workspace graph validation, profile-switch preconditions and semantic theme tokens.

The source is actual Reaper language: export craft, when, yield, each, make, vary, change and array descriptors. It does not introduce an invented contract/struct/enum syntax. The Reaper reference runtime remains the authoritative executor for these contracts; the limited native compiler is not claimed to compile the whole UI policy surface.

## Policy modules

| Module | Responsibility |
|---|---|
| duckos/ui/ddp.rpr | DDP v1 surfaces, state transitions, serial acknowledgement, damage and input routes |
| duckos/ui/window_manager.rpr | Window lifecycle/geometry, owner-surface binding, stacking/focus, notification area and tile cells |
| duckos/ui/taskbar.rpr | User-visible app entries, grouped window counts and consented Jora composition requests |
| duckos/security/app_sandbox.rpr | Signed manifest admission, capability attenuation, resource budgets and per-app VFS-root decisions |
| duckos/ui/workspace.rpr | Task-oriented layouts plus validated Jora workspace graph and profile-switch gates |
| duckos/ui/theme.rpr | Semantic noir/gold palette, status tokens, contrast-pair allowlist and theme-change admission |

## DDP and window rules

A surface handle is treated as an opaque owner-bound object. The client cannot claim another process's surface. Buffer size, stride, dimensions, pixel format and damage rectangles are checked before a native provider is allowed to touch backing memory.

Configure serials must match the latest server-issued serial and be acknowledged before the deadline. The client lifecycle is explicit: created → configured → acknowledged → attached → committed → presented → released. Invalid jumps and stale acknowledgements are rejected.

Window metadata and requested roles are not trusted merely because an app supplied them. System-only roles (desktop, panel, notification and lock) require a system-owned descriptor. Focus eligibility is separate from authorization. Ordinary applications stay in the normal stacking layer; system and notification layers are reserved. Fullscreen requires an explicit window.fullscreen capability. Tiling geometry is derived from the selected output grid, and manual resize in tiling mode needs an explicit override token.

These rules follow the existing Duck Display Protocol v1 architecture in [PR #148](https://github.com/Ivan-VHS/DuckOS/pull/148). They do not claim Wayland compatibility.

## Taskbar, Jora and workspace composition

The taskbar shows user-scope trusted/validated applications only. System processes and untrusted/quarantined entries are hidden. Running windows are grouped by app ID; the count is UI metadata, not a process handle.

A launch request is accepted only when the catalogue entry is published, its signature state is verified, the user has consented and every requested capability is already granted. The result is jora-compose-request-ready: the caller must still invoke the Jora service through its native service boundary. This policy does not start a process or compose a package.

Workspace requests contain a bounded component list and directed dependency edges. The component list is the declared topological order: each edge must point from a lower index to a higher index. This rejects self-edges, unknown endpoints and back edges, and makes a directed cycle impossible without unbounded graph traversal. Components must be trusted and their capability requests must be a subset of caller grants. Jora remains responsible for final package composition and dependency resolution.

Profile changes require valid profile data, saved application state and ready target services before the host begins a transaction. The policy decision is not itself a commit.

## App security boundary

App manifests bind a package identity to a verified signature state, trust label, resource limits, an opaque VFS root ID and requested capabilities. File access is checked against that root ID and requires separate fs.read or fs.write grants. Network access requires both explicit user consent and network.client.

A permission request never silently mutates the grant set. Even after consent is recorded, the native permission broker must persist a scoped grant before access can be allowed. A child app context must receive a distinct opaque VFS root ID, and only a subset of its parent's capabilities and resource limits. The native VFS broker remains responsible for proving that the child's root is a valid derived scope.

The execution-boundary contract always returns policy-only-no-execution. This is intentional: a Reaper allow value is not a kernel sandbox. Native enforcement still requires process address spaces, validated syscalls/handles, a privileged capability broker, filesystem enforcement and a real isolated application runtime.

## Theme tokens

The visual policy uses the Duck noir/gold direction:

- canvas #050505, shell #070707, surfaces #101010 / #181818;
- primary text white, muted text #B8B8B8;
- one semantic gold accent #FFD700;
- reserved status colors: green success, red error, blue information; warning remains gold.

Color roles are semantic. The contract permits known foreground/background role pairings; it does not claim a measured WCAG contrast ratio for arbitrary runtime colors. The native settings/theme service must calculate or validate actual rendered contrast and publish changes transactionally. Reduced-motion preference remains part of the existing policy.

## Verification and maturity

The existing .github/workflows/reaper-contracts.yml already checks every .rpr source under duckos/ and executes contract_tests.rpr using both the Reaper tree-walk and VM engines. This change extends that exact suite; no parallel runner is introduced.

The following remain **not implemented by this policy PR**:

- a native compositor, display server or rendered desktop session;
- input device drivers and actual DDP transport;
- kernel process isolation, syscall validation or privileged MAC enforcement;
- a native app permission broker and VFS enforcement boundary;
- Jora service invocation and actual application process launch;
- a complete native taskbar, launcher, settings UI or shell process;
- GPU presentation, multi-monitor hotplug and physical-hardware qualification.

Mora remains a browser-hosted design/reference surface during the transition; these contracts do not make HTML/CSS/JS the native desktop implementation. The existing native Duck Desktop maintenance panel is not promoted to a full DE by this change.

Do not mark a capability as native/implemented until its provider, negative tests, CI evidence and target behavior exist. The service topology and DDP ownership model remain governed by [the native desktop architecture proposal](https://github.com/Ivan-VHS/DuckOS/pull/148).
