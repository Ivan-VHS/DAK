# Cross-repository implementation-gap audit

**Review date:** 2026-11-25  
**Audit owner:** Ivan-VHS  
**Engineering baseline:** Ivan-VHS Engineering Code; Reaper-first system implementation; evidence-led maturity; Conventional Commits; protected mainline.  
**Scope:** DAK, Reaper, Pytyliki, VentuSample and OPlague.

> This is a first-pass evidence ledger, not a declaration that every open PR or every Markdown file has received a line-by-line code review. It inventories every open PR and every tracked Markdown path in the five repositories, deeply checks the current maturity documents and selected high-impact PRs, and records the next review/implementation gates. Remaining PR diffs and individual Markdown pages must be closed out through follow-up review entries.

## 1. Repository inventory

As of the review time, the GitHub API reports **480 open pull requests** across the five repositories and **423 tracked Markdown/MDX files** on their default branches.

| Repository | Open PRs | Draft PRs | PRs based on a non-main branch | Markdown/MDX files |
|---|---:|---:|---:|---:|
| DAK | 132 | 48 | 18 | 50 |
| Reaper | 146 | 59 | 3 | 122 |
| Pytyliki | 82 | 29 | 1 | 88 |
| VentuSample | 60 | 30 | 0 | 79 |
| OPlague | 60 | 33 | 0 | 84 |
| **Total** | **480** | **199** | **22** | **423** |

A non-main base is treated as a dependency/stack indicator, not an error. PRs with stacked bases must be reviewed and merged in dependency order. Draft status is not evidence that implementation is absent; a non-draft PR is not evidence that its checks passed.

## 2. Rules for classifying implementation

Use the narrowest evidence-backed status for every feature:

- **Implemented:** production source exists in the owning runtime, is reachable through the intended entry point, has focused positive and negative tests, and has passing CI for the claimed target.
- **Partial:** a working vertical slice exists, but the exact missing layers/platforms/operations are recorded.
- **Policy/contract only:** schemas, descriptors, admission decisions, state machines, reference-language modules or plan generators exist, but the privileged or production effect is absent.
- **Specified/planned:** Markdown, diagrams, catalogues, TODOs, API descriptions or JSON registries exist without callable implementation in the owning runtime.
- **Unverified:** source may exist, but target build, hardware qualification, required CI or reproducible evidence is unavailable.
- **Not applicable:** the capability is outside the product's declared scope, with an explicit reason.

Do not promote a feature because a README names it, a screen displays it, a schema validates it, an API returns an approval decision, or a catalogue contains a count. A passing reference-runtime test is not evidence of kernel, privileged-service, physical-device or native-compiler behavior.

## 3. Confirmed high-priority gaps

### DAK — native OS foundation and system services

**Current maturity evidence:** `README.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/IMPLEMENTATION_ROADMAP.md`, `docs/CORE_MVP_V1.md` and `docs/SYSTEM_CAPABILITY_PROFILE.md`.

The existing status documentation correctly separates the experimental x86-64 Stage 1 boot path, the host-native Mora application and Reaper reference-policy contracts. Stage 1 validates the firmware handoff, allocates and clears an early frame, emits its boot marker and halts. Mora is a host application; it is not launched by the kernel.

The following capabilities remain incomplete on the current mainline or require additional target evidence:

- GDT/TSS ownership, dedicated IST stacks, PIC/APIC setup, IRQ routing and interrupt-safe scheduling.
- Reusable physical-frame allocation/reclamation, complete page-table lifecycle, address spaces, TLB coordination and memory isolation.
- Preemptive task switching, user process creation, syscall dispatch, DABI64 enforcement and process reaping.
- Kernel-enforced capability checks, authenticated IPC delivery, cancellation and shared-memory lifetime.
- PCI/PCIe/USB/ACPI discovery integration, trusted signature verification, isolated driver loading, IRQ/DMA/IOMMU ownership and safe unload.
- A native VFS/filesystem, persistent package database, archive extraction, crash-safe writes and a physical-disk installer.
- A/B slot writes, boot-entry update, health confirmation, anti-rollback persistence and power-loss-tested recovery.
- Kernel compositor, input service, window manager, user-session startup and native audio service.
- Trusted OPlague JSON ingestion, publisher/build provenance verification and a VentuSample pack-v1 Reaper consumer.

The current Reaper modules in DAK PR [#202](https://github.com/Ivan-VHS/DAK/pull/202) are real Reaper source and should be tested as such, but they are **policy-only**. Installer admission, partition validation, driver admission/unload, package dependency/path checks and update anti-rollback return plan-only decisions. They do not write disks, verify signatures cryptographically, extract packages, map drivers, control DMA/IRQ or switch boot slots.

The ten native service gates in [docs/DAK_SYSTEM_SERVICES_V1.md on PR #202](https://github.com/Ivan-VHS/DAK/pull/202) remain prerequisites: trusted cryptographic provider; kernel-enforced DABI64/capabilities; memory/process isolation; crash-safe storage; verified installer writes and recovery; isolated driver lifecycle; safe package extraction/transactions; A/B boot integration; target/hardware qualification; and native/reference conformance plus corruption/power-loss tests.

**Migration dependency:** DAK PR [#190](https://github.com/Ivan-VHS/DAK/pull/190) and Reaper PR [#344](https://github.com/Ivan-VHS/Reaper/pull/344) are the coordinated product/registry naming migration. DAK PR #202 is based on the DAK migration branch and must not be merged ahead of the corresponding Reaper contract/name reconciliation.

### Reaper — native compiler, self-hosting and service runtime

**Current maturity evidence:** `README.md`, `docs/FEATURES.md`, `docs/IMPLEMENTATION_ROADMAP.md` and `docs/SELF_HOSTING_BOOTSTRAP.md`.

The README and feature matrix correctly identify the Python reference runtime, local developer tools and partial native C17 track. The native C17 frontend/IR/lowering is not full language parity. Reaper is not yet a complete native compiler, freestanding kernel compiler or privileged hardware runtime.

Confirmed boundaries in the reviewed PRs:

- PR [#313](https://github.com/Ivan-VHS/Reaper/pull/313) is documentation/registry work: all 20 named system-service entries remain `planned`; it does not add callable service handlers.
- PR [#333](https://github.com/Ivan-VHS/Reaper/pull/333) registers 120 operation contract keys, but the registered operations are explicitly not implemented as built-in handlers.
- PRs [#326](https://github.com/Ivan-VHS/Reaper/pull/326) and [#330](https://github.com/Ivan-VHS/Reaper/pull/330) are cloud adapter contracts; they do not add a Supabase client, transport, background sync or hosted execution.
- Self-hosting work in PRs [#339](https://github.com/Ivan-VHS/Reaper/pull/339), [#340](https://github.com/Ivan-VHS/Reaper/pull/340), [#343](https://github.com/Ivan-VHS/Reaper/pull/343) and [#345](https://github.com/Ivan-VHS/Reaper/pull/345) must be reviewed as one dependency-aware compiler progression. The reviewed documentation still marks statement grammar, complete AST parity, VM integration and native code generation as incomplete. Running Reaper source in the Python reference host is not a self-hosted compiler.

Required closure evidence: one canonical parser/IR implementation path; differential golden-corpus tests against the reference runtime; complete statement grammar; verified IR; VM execution; native code generation/linking; reproducible bootstrap; and target-native CI. Merge overlapping branches only after their file overlap and parent/child relationships have been reconciled.

### Pytyliki — processor and diagnostics workstation

**Current maturity evidence:** `README.md`, `docs/FEATURES.md` and `docs/ENGINEERING_BASELINE.md`.

The declared product boundary is read-only discovery/source review, bounded local workloads and a versioned C ABI. The feature matrix explicitly labels catalogue counts as inventory, not certification. The README does not advertise unsupported REST/GraphQL, WebSocket, OAuth or cloud features.

Cloud adapter PRs [#254](https://github.com/Ivan-VHS/Pytyliki/pull/254) and [#258](https://github.com/Ivan-VHS/Pytyliki/pull/258) are contract-only. They do not add a cloud SDK/client, network path, background telemetry or cloud synchronization.

Elbrus E2K support in PR [#152](https://github.com/Ivan-VHS/Pytyliki/pull/152) includes an architecture profile, cross-toolchain configuration, tests and an opt-in native workflow. The workflow requires a configured self-hosted `linux, e2k` runner. The reviewed PR is a draft and not mergeable; host-side tests passing does not prove native E2K build or hardware execution. Keep E2K in the compatibility matrix until native-run evidence is attached.

### VentuSample — offline audio workstation

**Current maturity evidence:** `README.md`, `docs/FEATURES.md` and `docs/NEXUS_AUDIO_PROFILE_V1.md`.

The declared product is a procedural sample workstation with offline DSP, file-based WAV/MIDI workflows and bounded processing. It is not a real-time DAW, VST/AU host, cloud rendering service or hardware audio driver. The NEXUS audio profile correctly requires a separate real-time design for device ownership, callback safety, scheduling, underrun recovery, clock drift and measured latency.

Cloud adapter PRs [#171](https://github.com/Ivan-VHS/VentuSample/pull/171) and [#175](https://github.com/Ivan-VHS/VentuSample/pull/175) are contract-only. Reaper integration PR [#178](https://github.com/Ivan-VHS/VentuSample/pull/178) adds a deterministic audio-policy contract and CI consumer, not a real-time audio service or kernel audio path.

Before claiming all 133 Quantum Audio Engine catalogue entries as independently implemented modules, maintain a source-to-test registry mapping every public module ID to its actual DSP kernel, parameter bounds, processing path and regression test. Catalogue size alone is not implementation evidence.

### OPlague — read-only device and package inspection

**Current maturity evidence:** `README.md`, `docs/FEATURES.md` and `docs/DRIVER_TARGET_ARCHITECTURE.md`.

The current product boundary is read-only device discovery, bounded package/metadata inspection, compatibility evidence and optional read-only telemetry. The feature matrix correctly states that no feature certifies a driver or changes device state.

The original native-driver-manager foundation PR [#5](https://github.com/Ivan-VHS/OPlague/pull/5) explicitly leaves Windows SetupAPI/Configuration Manager inventory, privileged service/IPC, driver install/remove, ETW and write-capable hardware adapters unimplemented. Do not describe OPlague as a driver installer or driver loader.

Reaper integration PR [#216](https://github.com/Ivan-VHS/OPlague/pull/216) adds executable Reaper policy validation in CI; it does not change the OPlague read-only boundary or add kernel driver operations. Cloud PRs [#209](https://github.com/Ivan-VHS/OPlague/pull/209) and [#213](https://github.com/Ivan-VHS/OPlague/pull/213) remain contract-only.

The E2K/Windows/driver compatibility statements must distinguish host platform detection, static INF/PE metadata matching, actual PnP inventory, signature verification and real driver loading. These are separate acceptance gates.

## 4. PR queue and verification findings

- The 480-PR inventory contains 199 drafts and 22 PRs based on a non-main branch. Preserve stack order; do not merge all open PRs as a batch.
- DAK #202 depends on DAK #190; Reaper #344 is its coordinated naming/registry partner.
- DAK federation refresh PRs #183 → #184 → #185 → #192 form a sequence of source-pin/integration work; validate exact pins and consumer tests at each step.
- DAK desktop/graphics PRs include stacked IPC, capability and compositor stages. A framebuffer renderer or policy broker does not prove a kernel desktop, user-session process manager or hardware compositor.
- Current PR workflow snapshots showed queued/pending checks for DAK #190/#198/#200 and Reaper #344/#345. OPlague #216 and VentuSample #178 reported `action_required`. Pytyliki #152 had passing host-side checks, but no successful native E2K runner evidence was established. These PRs were not treated as merge-ready by this audit.

## 5. Documentation correction policy

For each reviewed Markdown page:

1. Link every delivered claim to the owning source file, public entry point, focused test and CI workflow.
2. Label contracts, policy models, schemas, catalogues, mockups, screenshots and plans according to what they actually prove.
3. Replace unsupported present-tense claims with `Partial`, `Policy/contract only`, `Specified`, `Planned` or `Unverified`.
4. Record explicit non-goals and missing dependencies next to the feature, not only in a distant roadmap.
5. Keep README capability tables, `docs/FEATURES.md`, implementation status, roadmap, schemas/registries and release notes synchronized in the same PR.
6. Never delete a limitation merely to improve presentation. Remove a limitation only when implementation and the required evidence have landed.
7. Preserve third-party ownership, source attribution, licenses and clean-room boundaries.

## 6. Execution order

1. Reconcile and verify the DAK #190 + Reaper #344 naming pair; wait for all required CI and review gates.
2. Review DAK foundation PRs in dependency order (interrupt/descriptor state, frame allocator, page tables, IPC/capability, compositor); merge only after target tests and branch ancestry are proven.
3. Consolidate Reaper self-hosting PRs into one coherent parser → semantic analysis → canonical IR → VM → native code-generation path; prevent competing branches from claiming the same stage.
4. Keep the four DAK system-service modules plan-only until their cryptographic, kernel, memory, storage, driver and recovery dependencies are real and tested. Implement privileged effects only behind explicit Reaper contracts and kernel-enforced authority.
5. Complete each peer integration with producer, consumer, versioned schema, malformed-input tests, provenance, offline behavior and cross-repository CI.
6. Audit every remaining open PR diff and each of the 423 Markdown/MDX paths. For each item record its implementation evidence, CI result, overlap/dependency, required code/doc action and disposition (merge, revise, split, close or supersede).
7. Update project maturity only from accepted source/test/target evidence; never from the PR title or roadmap wording.

## 7. Audit completion checklist

- [x] Enumerate all five repositories and their default branches.
- [x] Enumerate all 480 open PRs, draft counts and non-main-base counts.
- [x] Inventory 423 Markdown/MDX paths.
- [x] Inspect the primary README/feature/status/roadmap documents in each repository.
- [x] Inspect selected high-impact migration, system-service, self-hosting and federation PRs and their changed-file lists.
- [x] Record selected workflow status snapshots and do not infer merge readiness from PR state alone.
- [ ] Review every remaining PR diff and review thread.
- [ ] Read and evidence-check every remaining Markdown/MDX file.
- [ ] Verify every public feature claim against implementation, tests and target CI.
- [ ] Create implementation PRs for dependencies that can safely be completed now; retain explicit planned status for capabilities blocked by missing kernel/runtime prerequisites.
- [ ] Re-run cross-repository tests and update all source-backed maturity records after accepted changes.

**Current conclusion:** the repositories contain substantial real source and test infrastructure, but the open PR queue and documentation catalogue are much larger than the set of verified production capabilities. The system is not feature-complete. The accurate next step is dependency-aware implementation and evidence-backed documentation correction—not blanket merging or promotion of contract-only work to delivered status.
