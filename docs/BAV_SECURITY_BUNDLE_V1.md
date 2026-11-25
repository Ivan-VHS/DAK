# BAV Security Bundle and Service Architecture

**Document ID:** DUCKOS-BAV-SEC-001  
**Version:** 1.0  
**Status:** Specified; scanner and enforcement are planned  
**Scope:** Beelzebub AV (BAV) for DuckOS  
**Canonical bundle extension:** .bav  
**Machine-readable contract:** ../schemas/bav-security-bundle.v1.schema.json  
**Related standards:** ERGONOMICS_AND_INTERACTION_STANDARD.md, IMPLEMENTATION_ROADMAP.md, UNIFIED_DOCUMENTATION_STANDARD.md

## 1. Purpose and maturity boundary

BAV is the planned local-first security suite for malware inspection, policy decisions, quarantine, recovery and signed detection-content updates in DuckOS.

This document specifies the package contract and service boundaries. It does not claim that DuckOS currently contains a malware scanner, on-access filesystem filter, kernel execution blocker, quarantine engine, signature updater or cryptographic trust-store implementation.

| Capability | Maturity | Boundary |
|---|---|---|
| .bav bundle format v1 | specified | JSON contract and schema only |
| Bundle signature verification | planned | Requires a native verifier and pinned trust store |
| Offline file hashing and static inspection | planned | No scanner implementation is introduced by this contract |
| Heuristic analysis | planned | Must be separately versioned, bounded and explainable |
| User-space scan worker | planned | Requires a supported Reaper execution target and service supervisor |
| Quarantine and restore | planned | Requires persistent storage, atomic operations and access controls |
| On-access protection | planned | Requires filesystem event integration and kernel-enforced capabilities |
| Execution/install blocking | planned | Requires a trusted native policy broker; Mora UI cannot enforce it |
| Mora BAV panel | planned | Presentation and user approval only; no privileged enforcement |

The canonical maturity vocabulary in the unified documentation standard applies. Schema validation proves structural validity only; it does not prove a signature, malware verdict or enforcement.

## 2. Product principles

BAV MUST be:

- Local-first and offline-first. A scan of local files MUST NOT require a network connection.
- Deny-by-default at privileged boundaries, with narrowly scoped capabilities.
- Deterministic for a fixed engine version, ruleset, configuration and input.
- Observable through bounded local event records and human-readable reason codes.
- Reversible: quarantine MUST preserve a verifiable route to restore unless an explicit, separately approved retention policy removes the item.
- Conservative about uncertainty: an unavailable scanner, expired bundle or malformed rule MUST be reported as an error or degraded state, not silently treated as clean.
- Transparent: show the file, rule, verdict, action, source and confidence that produced a result.
- Quiet by default: notifications are grouped and configurable; no deceptive warnings or false urgency.
- Safe under resource pressure: explicit byte, time, memory, queue and retry budgets.
- Network-quiet by default: bundle import may be manual/offline; any online update transport is a separate opt-in capability.

BAV MUST NOT silently delete user files, upload samples, install drivers, change firmware, disable system protections or execute content from a detection bundle.

## 3. Threat model and trust boundaries

Treat all scanned files, archives, metadata, imported bundles, plugins, model files and removable-media contents as untrusted.

Primary threats include:

1. Malformed or oversized bundle input intended to exhaust memory or CPU.
2. Forged, expired, revoked or downgraded detection bundles.
3. Path traversal, symlink substitution and time-of-check/time-of-use races during scan or quarantine.
4. Archive bombs, recursive containers, decompression bombs and parser exploits.
5. False positives that could make a user lose access to legitimate work.
6. A compromised scanner worker attempting to read unrelated user data or modify system state.
7. A compromised update source or publisher key attempting to distribute malicious or obsolete rules.
8. An unavailable scanner being misrepresented as a successful clean scan.

The trust chain MUST begin with a locally provisioned DuckOS trust root or a key explicitly approved by the device owner. A bundle MUST NOT be allowed to introduce or replace its own trusted signing key. Trust-store updates and key revocation require their own authenticated, versioned contract and approval policy.

### 3.1 Explicit non-goals

BAV v1 does not claim behavioral sandboxing, kernel rootkit detection, memory forensics, exploit prevention, cloud reputation, machine-learning detection, universal archive support or parity with commercial antivirus products. These may be evaluated as separate capabilities with their own threat models and evidence.

## 4. Service architecture

The intended service is split into small, independently testable components:

| Component | Responsibility | Required boundary |
|---|---|---|
| BAV Control | User-facing scan requests, policy display and result summaries | No direct privilege escalation |
| BAV Scanner Worker | Bounded file inspection and deterministic rule evaluation | Separate process and restricted filesystem capabilities |
| BAV Bundle Verifier | Schema, signature, signer trust, expiry and anti-rollback validation | Uses pinned trust material; never trusts bundle-provided keys |
| BAV Context Classifier | Optional descriptive tags from the Reaper defense-context vocabulary | Metadata-only channel; never contributes to a malware verdict or enforcement action |
| BAV Policy Broker | Converts verdicts into approved actions | Native capability checks; no UI-only enforcement |
| BAV Quarantine Store | Reversible isolation, manifest, integrity checks and restore | Dedicated storage namespace, atomic state transitions and strict ACLs |
| BAV Update Manager | Explicit import or opt-in retrieval of signed bundles | Verify before activation; retain last-known-good bundle |
| BAV Audit | Bounded local decision and action records | Redaction, rotation, export only by explicit user action |

The BAV Scanner Worker MUST NOT run as an unrestricted administrator/root process. It receives a read-only handle or narrowly scoped file capability for each scan request, a bounded output channel and no ambient network permission. A separate broker performs approved state-changing operations.

### 4.1 Existing Reaper security components

The Reaper repository already contains a Beelzebul 66-rule **repository scanner** (`tools/beelzebul.py`, `security/beelzebul.v1.json`, its regression tests and CI workflow). It audits tracked repository files, source patterns, paths and workflow metadata in read-only mode. Its `beelzebul.report.v1` output is useful for developer/repository assurance, but it is not an endpoint scanner: it does not provide general file-on-access protection, process-memory scanning, behavior monitoring or kernel enforcement. Preserve it as a distinct specialist tool; do not relabel its results as an antivirus scan of the host.

Reaper also defines `duckos.bav.defense-context.v1` and `security/defense-context.v1.tsv`, a 60-term descriptive vocabulary grouped into WMD/CBRN, Chinese military-platform and air-defence context. A match means only that content discusses a listed subject. It MUST NOT raise malware confidence, create a malicious verdict, block execution/builds, trigger quarantine or revoke capabilities. Keep these context tags separate from malware evidence and the detection-rule engine.

The Reaper defensive-security doctrine describes a Java context-classification library and self-test. The named Java source paths were not independently retrievable from the current default-branch file view during this integration audit; therefore the DuckOS integration MUST treat the TSV taxonomy as the confirmed data contract and the Java classifier implementation as requiring source/CI re-verification before it is called delivered.

DuckOS may later ingest Beelzebul reports and context tags only through explicit versioned, bounded schemas. Do not import Reaper Python modules into a native DuckOS service or use a context-tag result as a privileged decision.

### 4.2 Scan worker trust boundary

The scanner MUST not execute a file to inspect it. Parsers for executable formats and archives must be memory-safe where possible, bounded, fuzzed and isolated. Unsupported or truncated formats produce an explicit unsupported/incomplete result.

### 4.3 Reaper integration

Reaper is the primary language and contract layer for new DuckOS-owned system services. BAV policy, bundle parsing and deterministic rule evaluation SHOULD be expressed in Reaper as the native compiler and runtime gain the necessary capabilities.

The current Reaper reference runtime and partial native compiler are not a kernel service or a security boundary. A production BAV worker MUST NOT claim native isolation, hard real-time behavior or privileged enforcement until the target Reaper runtime, ABI and DuckOS process/capability services are implemented and verified.

No Python implementation is prescribed for DuckOS-owned BAV system services. Existing specialist repositories keep their own established languages and roles.

## 5. Canonical .bav bundle v1

A .bav file is a UTF-8 JSON document validated against ../schemas/bav-security-bundle.v1.schema.json.

The root schema identifier is duckos.bav.security-bundle.v1. A bundle contains:

- bundle identity, monotonically increasing sequence, creation and expiry times, and release channel;
- publisher key identifier and display label;
- target OS, supported architectures and minimum compatible engine version;
- bounded scan policy and explicit unknown-result behavior;
- declarative rules with stable IDs, severity, confidence, verdict and action;
- an Ed25519 signature descriptor.

### 5.1 Signature construction

The signature MUST cover the canonical JSON representation produced by RFC 8785 (JSON Canonicalization Scheme) after removing the root signature property entirely. All other fields, including schema ID, bundle identity, publisher key ID, sequence, timestamps, policy, target list and rules, are covered.

The signature descriptor MUST declare Ed25519 and RFC 8785. The signature is Base64-encoded Ed25519 output. The descriptor key ID and publisher key ID MUST match. The verifier MUST resolve that ID only through the locally trusted key store and verify the signature before activating the bundle.

JSON Schema validation is not cryptographic verification. A structurally valid package with an invalid, missing, expired or untrusted signature MUST be rejected.

### 5.2 Anti-rollback and expiry

For each trusted publisher, bundle identity and release channel, the verifier persists the highest successfully activated sequence. Lower sequences MUST be rejected unless an explicit owner-approved recovery operation restores a previously recorded last-known-good state.

The verifier MUST reject:
- a bundle created in the future beyond the configured clock-skew allowance;
- an expired bundle;
- a sequence lower than the stored high-water mark;
- a revoked, unknown or incompatible signer;
- a bundle whose engine-version requirement is not met;
- an unsupported target architecture or OS;
- a signature whose canonical payload does not match the received document.

The clock source and permitted skew are part of the verifier policy and audit event. A system with an untrusted or unavailable clock MUST report that the expiry decision cannot be verified; it MUST NOT silently accept the bundle as current.

### 5.3 Rule language

Rules are declarative data, not programs. Version 1 permits a deliberately narrow match vocabulary:

- SHA-256 equality for a complete file within the configured scan bound;
- exact bounded byte-sequence matching with an optional offset and maximum inspection range.

Rules MAY return suspicious or malicious verdicts and request alert, quarantine or deny-execution actions. The policy broker decides whether the requested action is available and authorized on the current runtime.

The format MUST NOT support embedded scripts, shell commands, dynamic libraries, executable payloads, arbitrary regular expressions, network URLs as executable instructions or runtime code generation.

A rule ID is stable and unique inside the bundle. Conflicting duplicate IDs MUST reject the bundle. Rule order and tie-breaking MUST be deterministic. When more than one rule matches, the engine MUST retain all matching rule IDs and apply a documented severity/action precedence; it MUST not silently discard evidence.

### 5.4 Policy safety

The bundle policy declares limits, not a grant of authority. The local administrator policy may impose stricter limits and MUST take precedence over less restrictive bundle values.

Audit mode reports decisions without blocking or quarantining. Protect mode may request enforcement but does not itself create enforcement capability. If the policy broker is unavailable, BAV MUST report degraded/unavailable status and must not imply that a requested block was enforced.

Unknown or unsupported files MUST be reported as not fully inspected. The action for an unknown execution request is an explicit local policy choice; BAV v1 MUST NOT silently label unknown content as clean.

## 6. Scan pipeline and resource governance

The intended pipeline is:

1. Validate the request, caller identity, file handle and declared scan budget.
2. Resolve the target without following untrusted path substitutions; pin the object identity where the platform permits.
3. Capture bounded metadata and a stable content identity.
4. Inspect using bounded readers; reject unsupported or excessive nesting/decompression.
5. Evaluate the active verified bundle deterministically.
6. Return verdict, matched rule IDs, coverage, omitted regions, engine/bundle versions and reason codes.
7. Ask the policy broker to perform only an action permitted by local policy and available capabilities.
8. Persist a bounded audit record and report the final action state.

Default budgets must be selected from measured target hardware and declared in the engine profile. They include maximum file bytes, archive depth, expanded bytes, ratio, parser time, memory, concurrent scans, queue depth and retry count. A scan timeout or budget exhaustion is incomplete, not clean.

The user must be able to cancel a scan. Cancellation must stop new work, release handles and report whether any file action had already completed.

## 7. Quarantine, restore and evidence

Quarantine is a reversible, transactional state change, not file deletion.

A quarantine record SHOULD contain:
- opaque item ID and original file identity/path metadata;
- content SHA-256 and byte length;
- detection bundle ID, sequence and matching rule IDs;
- engine version, verdict, confidence and timestamps;
- action state, storage object identity and restore history.

The quarantine store MUST:
- use an access-controlled location separated from ordinary application data;
- avoid executing, indexing or previewing quarantined payloads;
- verify content digest before restore;
- prevent path traversal and symlink replacement on restore;
- use atomic move or copy-and-verify semantics appropriate to the filesystem;
- preserve the original item when the quarantine transaction fails;
- expose a clear restore workflow and log the result;
- never permanently delete an item as an automatic consequence of a detection rule.

Restore to the original path is allowed only after the user reviews the risk and the destination identity is revalidated. Conflicts must restore to a user-selected safe destination or remain quarantined; do not overwrite an unrelated file.

## 8. Privacy, telemetry and notifications

All scan metadata and audit events remain local by default. BAV MUST NOT upload files, hashes, paths, telemetry or quarantine records without a separate, explicit user action and a clear preview of the exported data.

Logs MUST be bounded, rotated and redact secrets. File paths may reveal private information and must not be sent to external services by default.

Notifications are grouped by severity and user-configurable. Routine scan completion is quiet. Critical alerts state what was detected, what action actually occurred and what remains unprotected. No alert may claim “blocked” when the broker only recorded a recommendation.

## 9. Mora interaction contract

The future BAV panel in Mora or Native Duck Desktop is a control surface, not the security boundary. It should present:

- protection state with separate labels for scanner readiness, bundle trust and broker enforcement;
- scan scope, progress, cancellation and explicit incomplete/unsupported results;
- matched rule, severity, confidence, file identity and the reason for the verdict;
- quarantine contents, restore action, integrity result and history;
- bundle publisher, key ID, sequence, channel, expiry and verification result;
- permission and data-export controls.

A single green “protected” badge is not acceptable when any required subsystem is missing or degraded. Use readable status text and a symbol in addition to color. The UX standard requires keyboard operation, visible focus, reduced motion, recoverable actions and meaningful empty/error states.

## 10. Verification plan

Before any BAV capability can be marked implemented or verified, add target-specific evidence for:

| Area | Required tests |
|---|---|
| Schema | Valid/invalid fixtures, unknown fields, duplicate rule IDs, missing fields and all bounds |
| Cryptography | Valid signature, altered payload, wrong key, unknown key, revoked key and malformed Base64 |
| Time/rollback | Expired/future bundle, clock uncertainty, sequence downgrade and explicit recovery |
| Parser safety | Fuzzed JSON, oversized input, excessive rule count, deeply nested input and invalid encodings |
| Rule engine | Positive/negative fixtures, deterministic order, duplicate matches and boundary offsets |
| Archive handling | Depth/expanded-size/ratio limits, truncated archives and parser timeout |
| Filesystem safety | Symlink/path traversal, TOCTOU substitution, permission denial and short reads |
| Quarantine | Atomicity, interrupted transaction, integrity mismatch, restore collision and rollback |
| Isolation | Worker cannot read arbitrary files, change system settings, access devices or use network without a capability |
| Broker | Denied capability, unavailable broker, audit-only mode and action-result accuracy |
| Resilience | Queue saturation, memory pressure, service crash, restart budget and recovery |
| Privacy | No network egress by default; redaction and explicit export only |

A schema-only test proves the schema accepts or rejects JSON. It does not verify the cryptographic signature, scan a file or enforce a policy.

## 11. Extension and namespace ownership

The .bav suffix is reserved exclusively for Beelzebub AV signed security bundles. In the uploaded OS(2).txt proposal, the same suffix was also assigned to Buffer Allocation & Validation. That creates an ambiguous file type and MUST NOT be carried into implementation.

The buffer layout/allocation specification is renamed to .bufspec. Its schema and parser are separate contracts and are not implemented by this BAV document.

Do not confuse the file suffix with Reaper's existing policy identifier duckos.bav.defense-context.v1 or its security/defense-context.v1.tsv catalog. Those are a policy namespace and a plain-text context vocabulary, not .bav files and not malware signatures.

The Reaper extension registry, examples, validators, IDE syntax, content-type detection and DuckOS package registry must be updated in separate, reviewable changes before either extension is advertised as supported. Until then, .bav and .bufspec are specified formats only; no parser or runtime support is implied.

## 12. Delivery stages

1. **BAV-0 — Contract:** this document, schema, immutable fixtures and ownership of the .bav namespace.
2. **BAV-1 — Trust verifier:** pinned trust store, signature verification, expiry, sequence high-water mark and revocation.
3. **BAV-2 — Read-only scanner:** isolated user-space worker, bounded hash/static inspection and deterministic findings.
4. **BAV-3 — Quarantine:** transactional store and integrity-checked restore.
5. **BAV-4 — Policy broker:** capability-checked deny/quarantine actions and audit trail.
6. **BAV-5 — On-access integration:** filesystem events and execution/install mediation after the native kernel/process/file-system gates pass.
7. **BAV-6 — Mora UX and operations:** accessible control panel, status, recovery, bundle management and release qualification.

Each stage is delivered in a separate reviewable change and cannot skip its dependency gates.

## 13. Change control

Any new rule kind, signature algorithm, trust metadata field, action or bundle limit requires a versioned schema/contract change, compatibility fixtures, parser review and security review. A new action MUST have a clear capability requirement, safe failure behavior and reversible path where possible.
