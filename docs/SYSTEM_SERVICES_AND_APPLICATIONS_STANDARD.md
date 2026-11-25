# DuckOS system services and application experience standard

**Contract ID:** `duckos.system-services-and-applications.v1`  
**Status:** specified; Reaper policies are reference contracts, not native enforcement.  
**Applies to:** boot and session services, security services, first-party applications, Mora-launched applications and future native desktop applications.

This standard applies the OS architecture, security and human-computer-interaction requirements in the shared `OS(2).txt` reference to DuckOS services and applications. It extends the existing Reaper contracts for service restart, capabilities, recovery, telemetry, command intent, motion and workspaces. It does not promote any planned native subsystem to implemented.

## 1. System boundary and maturity

DuckOS has three distinct execution surfaces:

1. Reaper source contracts define deterministic policy decisions and are exercised by the tree-walk and VM contract suite.
2. Host-side tools and Mora provide user-space utilities and a browser shell; they cannot enforce kernel permissions or manage real native processes.
3. A future native service manager, capability broker, IPC transport, filesystem, notification server and compositor must enforce the same policies at their actual privilege boundaries.

A Reaper policy passing its tests proves the policy behavior only. A catalog entry, UI panel, mock process, manifest or test fixture is not a running system service. Native implementation status changes only with source code, target-specific tests, CI evidence and documentation.

## 2. Service model

### 2.1 Service identity and manifest

Every service must have a stable reverse-domain ID and a versioned manifest. The manifest records:

- executable/component identity, version, digest and trust provenance;
- scope: `system`, `session` or `user`;
- startup phase: `boot`, `core`, `session`, `desktop` or `on-demand`;
- required and optional dependencies, with a validated acyclic dependency graph;
- the exact capability set, service principal and sandbox profile;
- CPU budget, memory ceiling, queue depth, I/O deadline and restart budget;
- health/readiness contract, stop deadline and recovery behavior;
- network policy, persistent-state location and update/rollback policy;
- maturity status and evidence for the claimed implementation.

Unknown fields, unknown capability names, duplicate IDs, dependency cycles, incompatible ABI versions and unsigned or untrusted executable artifacts are rejected before activation. A service may not expand its capabilities by editing its own manifest.

### 2.2 Startup, lifecycle and dependencies

Startup is phased and dependency ordered:

`firmware → memory → interrupts → scheduler → IPC → drivers → core services → session → desktop`

The dependency graph, not lexical name order, determines service start order. A required dependency that is not ready holds the consumer in a visible waiting state. An optional dependency may be absent only when the consumer declares a safe degraded mode. Cycles and ambiguous dependency versions fail validation.

Canonical lifecycle states are `inactive`, `starting`, `ready`, `degraded`, `stopping`, `stopped` and `failed`. Only documented transitions are legal. Readiness requires a successful health check and fresh heartbeat; process existence alone is not readiness.

A clean exit is not restarted. Failed services use a finite retry budget and bounded deterministic backoff. Repeated failure moves the service to a visible terminal state, preserves diagnostic context and prevents an unbounded restart loop. Restarting a service must not silently replay a non-idempotent operation.

Shutdown is cooperative: stop accepting new work, drain or cancel bounded queues, checkpoint durable state when possible, then exit before the deadline. A watchdog may mark a service unresponsive and ask the supervisor to recover it; it must not silently corrupt or discard user data.

### 2.3 Resource fairness and responsiveness

Services declare budgets rather than relying on ambient unlimited resources. Interactive input, audio deadlines, compositor frame work and foreground application actions outrank indexing, prefetch, telemetry compaction and background updates.

- CPU work is scheduled with explicit priority/deadline classes and bounded quanta.
- Memory is quota-limited; allocations and queues have finite upper bounds.
- I/O is asynchronous where possible, cancellable and deadline-aware.
- Producers must honor backpressure; a full queue is a visible result, not permission to allocate without limit.
- Background work yields under pressure and must not starve foreground work.
- Priority inheritance or an equivalent mechanism is required where locks can block a higher-priority task.
- Speculative work is read-only and disposable. It must never perform an authoritative write or trigger a privileged action.

The initial Reaper contracts model restart decisions, bounded IPC, resource selection, recovery and telemetry. They do not yet preempt threads, allocate physical pages, map shared memory or enforce CPU/memory quotas.

## 3. Service security and trust

### 3.1 Least authority

Each service has a dedicated principal and the smallest capability set needed for its role. Capabilities are explicit, scoped, auditable and attenuated across child processes. There is no ambient administrator token for ordinary daemons.

Sensitive operations such as firmware writes, driver loading, system-wide configuration, microphone/camera access, screen capture, network listening and user-data export require a dedicated capability and an explicit policy path. A client-supplied boolean such as `signature_valid=true` is not cryptographic verification.

### 3.2 IPC and event bus

All service-to-service communication uses versioned, typed messages over bounded channels. Each request carries an authenticated sender identity, capability context, schema version, deadline and correlation/request ID. Receivers validate lengths, ownership and schema before use.

Events are published only after the originating state transition succeeds. Delivery semantics are documented per message type: at-most-once, at-least-once or idempotent replay. Consumers must deduplicate where retries can occur. Queue saturation applies backpressure and produces bounded diagnostics. Shared memory/zero-copy is added only with explicit mapping ownership, lifetime, revocation and pinning rules.

### 3.3 Network and secrets

The default service network policy is no listener and no outbound connection. Egress is granted per service and destination/purpose; inbound listeners require explicit enablement and a firewall policy. Services expose no debug port by default.

Credentials live in a protected credential service, not command-line arguments, logs, world-readable configuration or application storage. Logs redact secrets and sensitive personal content. Local-only operation is the default; synchronization and telemetry export are opt-in and visible.

### 3.4 Configuration, updates and recovery

Configuration layers are ordered and explainable: shipped defaults, administrator overrides, service drop-ins and per-user preferences. A candidate configuration is parsed and validated before activation. Risky changes require a rollback point or a time-limited confirmation path.

Updates follow `download/obtain → verify signature and digest → stage → validate dependencies and schema → commit atomically → confirm health`. A failed validation or failed health check rolls back to the last known-good version. No system update may interrupt active work or reboot without user policy and clear notice.

Persistent service state is isolated by service identity. Logs and caches have independent quotas and rotation. Recovery must preserve user data, quarantine corrupt snapshots and never execute untrusted recovery payloads.

## 4. Observability and operations

Every service emits bounded structured events with service ID, version, process identity, severity, wall-clock and monotonic timestamp, event code, request/correlation ID and a redacted context. Logs are rotated and quota-limited; telemetry retention and export are user-controllable.

The system service view must expose, without requiring a terminal:

- service state, startup phase, dependency blockers and last transition;
- CPU, memory, I/O, queue depth and restart count;
- capability grants, network listeners/connections and package provenance;
- last health check, recent diagnostics and update/rollback state;
- controls allowed to the current user, and why a control is denied.

Read-only inspection is the default. Start/stop, restart, permission, update and recovery actions require an explicit action and appropriate privilege. Destructive controls are separated from ordinary navigation.

## 5. Application manifest and sandbox contract

Every application declares an ID, publisher, version, content digest, ABI, entry point, sandbox type, resource budgets, data locations, network policy, requested capabilities, permission rationale and maturity/evidence.

Applications are denied access by default to arbitrary home-directory content, other applications' memory, global clipboard history, raw input events, microphones, cameras, location, screen capture, device nodes and system configuration. File and folder access is mediated by user-visible portals or narrowly scoped grants.

A manifest is not itself a sandbox. The application is considered sandboxed only when a native process or component host enforces memory isolation, syscall/host API filtering, handle ownership, resource quotas and capability checks. Unsandboxed compatibility modes must be clearly labelled and opt-in.

### 5.1 Capability decisions

- Public, non-sensitive read-only capabilities are still granted explicitly by package policy.
- Camera, microphone, location, screen capture, clipboard read and personal-data export require an understandable prompt and a visible active-use indicator.
- Microphone/camera access must be revocable while the application is running.
- Firmware, kernel, driver, credential-store and system-wide mutation capabilities are not ordinary application permissions. They require a separate privileged broker and operator confirmation.
- A permission decision records the app identity, capability, purpose, scope, decision time and revocation path.

## 6. Application experience and accessibility

### 6.1 Interaction model

First-party and native desktop applications use a shared, predictable interaction vocabulary: clear labels, consistent navigation, visible focus, stable shortcuts, standard undo/redo, contextual actions near the object being edited and a searchable command palette for complex workspaces.

All primary operations are keyboard accessible. Tab order follows visual reading order; focus never disappears into hidden controls. System shortcuts have priority over app shortcuts. A command palette complements menus; it does not replace discoverability.

Interactive targets must be comfortably operable with mouse, keyboard, touch or assistive technology. Never encode a critical state using color alone. Controls need accessible names, roles, values, state announcements and logical grouping.

### 6.2 Visual ergonomics and adaptive layout

The shared design system preserves readable contrast, clear typographic hierarchy and the Duck black/white/yellow visual identity. Status colors remain supplementary signals. Light/dark appearance, system text scaling, HiDPI/fractional scaling, reduced motion and high-contrast preferences are respected.

Desktop applications offer at least three density modes—comfortable, balanced and compact—without hiding essential state. Dockable panels and saved workspaces are appropriate for professional applications. Window geometry is restored only when the target display still exists; otherwise the window is moved into the visible work area.

### 6.3 Focus, notifications and interruption control

The OS owns the notification policy and Do Not Disturb state. Notifications do not steal keyboard focus, move windows or cover destructive controls. Non-critical alerts are queued during DND; critical system alerts use a distinct, accessible, non-focus-stealing presentation. Apps cannot bypass the global policy by creating their own notification loop.

### 6.4 Latency, long-running work and background behavior

The interface acknowledges input immediately, even when the requested operation continues asynchronously:

| Elapsed time | Required feedback |
|---|---|
| up to 100 ms | direct visual state change; no blocking wait |
| 100 ms–1 s | subtle status feedback without interrupting work |
| 1–2.5 s | visible activity/status and current phase |
| over 2.5 s | progress, meaningful phase/step, cancellation when safe, and a useful failure result |

The UI thread does not perform network, disk, indexing, compilation or large-data work. Long tasks accept cancellation and define what happens to partial output. Progress is based on measured work where possible; unknown duration is reported as unknown, not fabricated.

When minimized, hidden or idle, applications reduce rendering, polling and animation. Reduced-motion mode suppresses non-essential motion. Battery/power policies may pause optional background work; they must not interrupt an active recording, user-approved export or other declared critical task without a clear user decision.

### 6.5 Data safety and recovery

Apps use autosave or a recoverable journal for meaningful user-created work. Mutations that can lose data have undo/redo or a clearly disclosed irreversible boundary. Save, export, sync and close behavior is explicit. A crash recovery prompt identifies the recovery source and offers restore, inspect or discard; it does not overwrite the original automatically.

Native file pickers, clipboard formats, drag-and-drop, recent-item providers and sharing portals are used when available. Access is limited to user-selected objects, not broad filesystem scanning. Sync is local-first; remote sync is opt-in and exposes conflict resolution.

## 7. First-party service/application integration

First-party applications consume shared system services instead of privately recreating privileged behavior:

| Shared service | Applications use it for | Security/UX invariant |
|---|---|---|
| Session and identity | user session, lock state, app identity | no app impersonation or ambient admin |
| Capability broker and portals | files, devices, clipboard, screen capture | explicit scope, revocation and audit |
| Notification/focus service | alerts, DND, focus modes | no focus stealing or DND bypass |
| Storage and recovery | app data, autosave, snapshots | quotas, isolation, atomic writes and restore |
| IPC/event bus | device, power, network and session events | typed bounded messages and backpressure |
| Audio service | Cockos and communication audio | visible device/microphone state and revocation |
| Network service | Po and explicitly networked apps | no inbound listener by default |
| Update/package service | apps, drivers and system components | provenance, signature, staged update and rollback |
| BAV security service | scanning, quarantine and threat reports | local-first, least privilege, reversible isolation |

App-specific implications:
- **Cockos:** microphone and audio-session permissions are scoped and visibly active; recording state is never hidden.
- **Kavun:** media indexing is user-controlled and non-destructive; private metadata stays private.
- **Ka-bon:** extraction is a proposal until confirmed; no payment execution is implied.
- **Gloverty:** automation rules declare triggers, scope and effects; destructive or privileged actions require confirmation and loop protection.
- **Po:** site permissions are isolated per site/profile; tracker protection is not described as anonymity.
- **Illidia:** game capture, sharing and DND are user-controlled and reversible.
- **Unify:** cross-device sharing is explicit, with clear device identity and selected-item scope.
- **Sestem / SetupUP:** system facts are read-only unless a separate privileged service grants a documented action.
- **Orriganize and other local productivity apps:** user data remains locally owned, recoverable and exportable.

## 8. BAV antivirus service and `.bav` artifact

BAV is a security service and user-facing Security Center, not a privileged monolith. Its scanner, signature updater, quarantine store and UI are separate components. The scanning service receives only the filesystem access required by the approved scan mode; its UI does not receive kernel authority.

The default scan path is local and read-only. Network access is disabled unless the user enables a signed intelligence update source. Detection results include engine/version, signature-set version, object digest, detection ID, confidence, timestamp, action and evidence. Unknown or malformed content is treated as untrusted.

A high-confidence malicious verdict may request reversible quarantine. BAV never silently deletes an object, edits a source executable in place or runs a sample to “test” it. Quarantine preserves original bytes and metadata in an access-controlled store, records the reason and allows a verified restore path. Low-confidence or suspicious results are surfaced for review rather than silently destroyed.

DuckOS reserves the `.bav` extension for a **BAV signed report/evidence bundle**, media type `application/vnd.duckos.bav+json;version=1`, with the `DUCKBAV1` magic header, schema version, payload digest, engine identity, signature state and bounded record count. It is metadata/evidence, not an executable, driver, live signature database or auto-run package. The reader verifies schema, digest, signature and provenance before displaying or importing it; invalid bundles are quarantined.

**Extension collision to resolve across repositories:** the Reaper proposal in the source document also assigns `.bav` to Buffer Allocation & Validation. A global file association cannot safely infer two unrelated formats from the same suffix. DuckOS uses `.bav` for the BAV evidence bundle; the Reaper buffer descriptor must be renamed (for example, `.rbuf`) or remain an explicitly Reaper-private format before cross-repository integration. This DuckOS change does not silently rewrite the Reaper repository.

## 9. Verification and release gates

The Reaper suite must test service descriptor validation, startup dependency gating, lifecycle transitions, restart/backoff bounds, readiness, configuration/update rollback decisions, application manifest admission, capability decisions, latency feedback, notification/focus policy, background throttling and BAV artifact/verdict handling.

A native release additionally requires:
- real process creation/exit/wait and restart supervision;
- kernel-enforced capabilities, isolation and resource quotas;
- authenticated IPC, bounded queues and cancellation;
- persistent storage, atomic update and tested rollback;
- native notification/focus/portal APIs and compositor/input integration;
- end-to-end tests proving one app cannot access another app's data or steal input;
- signed BAV engine/signature updates, quarantine/restore fault tests and no-execution scanning;
- accessibility, keyboard-only, scaling, reduced-motion and multi-monitor qualification.

Until those gates pass, label these additions as **specified/reference-policy**. Do not claim that a service is running, an app is sandboxed, antivirus protection is active or a kernel policy is enforced merely because a Reaper contract or Mora panel exists.
