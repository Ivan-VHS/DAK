# Repository-wide Markdown and Roadmap Harmonization Plan

**Document ID:** `DUCKOS-DOCS-EXEC-PLAN-001`  
**Version:** 1.0  
**Date:** 2026-11-23  
**Status:** `specified`  
**Scope:** every maintained Markdown document and engineering plan in the DuckOS repository  
**Normative references:** [Unified Documentation Standard](UNIFIED_DOCUMENTATION_STANDARD.md), [Documentation Control](DOCUMENTATION_CONTROL.md), [Repository-wide Implementation Directives](REPOSITORY_EVOLUTION_DIRECTIVES.md), [Engineering Evolution Framework](ENGINEERING_EVOLUTION_FRAMEWORK.md)

## 1. Purpose

This plan establishes one coordinated lifecycle for the repository's Markdown documentation, technical specifications, implementation records and roadmaps. It applies the 20 canonical engineering directives without duplicating or replacing their definitions.

The objective is to make the documentation set function as one navigable engineering system:

- every page has one primary subject and a clear authority level;
- every implementation claim is traceable to source, schema, tests or a reproducible operation;
- every plan distinguishes intended work from delivered behavior;
- architecture, contracts, user workflows, status records and indexes agree;
- independent work can proceed in parallel while shared interfaces, migrations and releases remain dependency-ordered;
- updates are repeatable, reviewable, reversible and safe.

This is a documentation and planning standard. Creating or updating a specification does not implement the described operating-system capability.

## 2. Scope and inventory

The repository inventory contains **32 Markdown files** on the reviewed default-branch tree. All are governed by this plan. The inventory is a subject map, not a statement that every page needs the same edits in every release.

### 2.1 Project entry points and design

| File | Primary responsibility | Update when |
|---|---|---|
| `README.md` | Product identity, current user-facing entry points, quick start, truthful maturity summary and primary links | A supported workflow, product boundary, build/test command or major capability changes |
| `MORA_DESIGN_SYSTEM.md` | Canonical Mora visual language, semantic tokens, layout, motion and accessibility principles | A design token, visual rule, interaction principle or accessibility contract changes |

### 2.2 Architecture, foundation and runtime contracts

| File | Primary responsibility | Update when |
|---|---|---|
| `docs/ARCHITECTURE.md` | System layers, ownership, data/control flow, trust boundaries and native bring-up gates | A component boundary, dependency, execution path or architecture gate changes |
| `docs/BOOT_INFO_V1.md` | Versioned boot handoff record, field semantics and validation limits | The boot handoff ABI, schema or validator changes |
| `docs/BUILD_CONTRACTS.md` | Supported build inputs, targets, dependencies and build invariants | Build configuration, compiler, platform or CI expectations change |
| `docs/FOUNDATION_ARCHITECTURE.md` | Native foundation scope and division between host-testable contracts and hardware work | Foundation modules, native boundaries or bring-up assumptions change |
| `docs/DEPLOYMENT.md` | Release bundles, signing, verification and non-destructive deployment plans | Packaging formats, signature verification, deployment targets or installer scope changes |
| `docs/DUCKBRIDGE.md` | Runtime discovery, compatibility selection and non-executing launch-plan contract | Runtime support, selection policy, argv/environment planning or execution boundary changes |
| `docs/WINDOWS_COMPATIBILITY.md` | PE inspection, prefix scaffolding, compatibility requirements and traceability | PE support, Windows ABI work, backend status or compatibility tests change |
| `docs/UNIFY_TRANSFER_FORMAT_V1.md` | Versioned manual transfer format and compatibility rules | The transfer contract or its schema changes |

### 2.3 Desktop, applications and user workflows

| File | Primary responsibility | Update when |
|---|---|---|
| `docs/DESKTOP_OPTIMIZATION.md` | Native user-space desktop audit, file organization and reversible startup controls | Commands, supported platforms, safety controls or UI behavior change |
| `docs/EXTENDED_TERMINAL.md` | Allowlisted terminal commands, extension boundary, state and diagnostics | Command registry, history/configuration behavior or extension contract changes |
| `docs/GAMING_PERFORMANCE_INTEGRATION.md` | Mora Boost and OPlague telemetry/profile integration | Data exchanged, platform adapters, permissions or verification changes |
| `docs/MORA_COMMONS.md` | Application discovery catalogue and entry-level capability boundaries | App identity, catalogue metadata, discovery or application ownership changes |
| `docs/MORA_INTEGRATION.md` | Browser shell, local tools, native bridges and service maturity boundaries | Mora-to-native workflows, permissions or app integration changes |
| `docs/PREINSTALLED_APPLICATIONS.md` | Product role, application scope, interactions and non-goals | Application scope, capability registration or package proposal changes |
| `docs/PROGRAM_CATALOGUE_INTEGRATION.md` | Programme catalogue allocation and integration rules | Allocation format, catalogue validation or adoption workflow changes |
| `docs/PROGRAM_CATALOG_1000.md` | Human-readable 1,000-entry catalogue record | Catalogue entries or allocation status change |
| `docs/REAPER_INTEGRATION.md` | Process-isolated Reaper workbench and bounded native integration | Launcher behavior, commands, subprocess policy or Reaper integration changes |

### 2.4 Federation, provenance and engineering profile

| File | Primary responsibility | Update when |
|---|---|---|
| `docs/REPOSITORY_FEDERATION.md` | Pinned source repositories, ownership, licenses and integration boundaries | Submodule pins, upstream projects, license metadata or federation tooling change |
| `docs/SOURCE_TRACEABILITY.md` | Mapping from source specification to DuckOS implementation and evidence | Source provenance, mapped modules or acceptance evidence change |
| `docs/IVAN_VHS_ENGINEERING_PROFILE.md` | Project engineering profile and established authoring/implementation practices | The profile's documented standards or project governance changes |
| `docs/clusters/project-overview.md` | Concise subsystem overview and links to authoritative specifications | A topic hub, subsystem boundary or entry-point link changes |

### 2.5 Governance, status and plans

| File | Primary responsibility | Update when |
|---|---|---|
| `docs/DOCUMENTATION_CONTROL.md` | Documentation ownership, quality, navigation and acceptance rules | Documentation workflow, review gates or quality checks change |
| `docs/ENGINEERING_EVOLUTION_FRAMEWORK.md` | Twenty-domain practice model and adoption loop | Canonical practice mapping, checks or machine-readable contract changes |
| `docs/LANGUAGE_QUALITY.md` | Editorial rules and prose diagnostics | Style rules, language checks or supported localization changes |
| `docs/REPOSITORY_EVOLUTION_DIRECTIVES.md` | The 20 requested execution directives and cross-project application | Directive interpretation, repository scope or adoption criteria change |
| `docs/UNIFIED_DOCUMENTATION_STANDARD.md` | Canonical terminology, maturity states, evidence and cross-project documentation semantics | Status vocabulary, evidence policy or normative documentation structure changes |
| `docs/IMPLEMENTATION_STATUS.md` | Dated snapshot of implemented, partial and pending capabilities | Source or test evidence changes the actual capability state |
| `docs/THIRTEEN_WAVES_IMPLEMENTATION.md` | Historical record of the thirteen coordinated delivery waves | A referenced PR, verification outcome or delivery record is corrected |
| `docs/INFORMATION_ARCHITECTURE.md` | Canonical documentation navigation graph and topic ownership | A page is added, moved, renamed, retired or reassigned |
| `docs/README.md` | Maintained human-facing documentation index | Any maintained page or canonical topic entry changes |

## 3. Authority and source-of-truth model

Use this order according to the kind of fact being stated:

1. **Source code and executable configuration** define behavior present in the current revision.
2. **Tests and CI** show which behavior was exercised, and only for the named revision, target and configuration.
3. **Schemas, protocol definitions, ABI declarations and versioned manifests** define machine-readable contracts.
4. **Build and release workflows** define reproducible build, packaging and deployment procedures.
5. **Normative documentation** defines intended contracts, architecture decisions and operating rules, but does not prove implementation.
6. **Status records and plans** summarize evidence or future work; they do not override source, tests or schemas.
7. **Catalogues, diagrams, screenshots and examples** provide navigation or illustration, not independent implementation proof.

When sources disagree, record the discrepancy and resolve it against the appropriate authority. Do not silently choose the most optimistic statement. Preserve provenance and record the affected pages in the same change.

One subject must have one canonical specification. Other pages summarize it and link to it; they do not copy a second editable version of the same contract.

## 4. Canonical status model

Keep four dimensions separate:

| Dimension | Canonical values | Meaning |
|---|---|---|
| Capability maturity | `not_assessed`, `specified`, `planned`, `partial`, `implemented`, `verified`, `deprecated`, `unsupported`, `not_applicable` | How far an individually stated capability has progressed |
| Runtime state | `uninitialized`, `initializing`, `ready`, `running`, `degraded`, `stopping`, `stopped`, `failed`, `unknown` | What a running component is doing now |
| Verification result | `not_run`, `passed`, `failed`, `blocked`, `skipped`, `not_applicable` | Outcome of a named check |
| Integration policy | `required`, `optional`, `opt_in`, `disabled`, `not_applicable` | Whether and how an integration is enabled |

Rules:

- `verified` implies `implemented` and needs a named passing verification result.
- `partial` must state both the working subset and the missing behavior.
- `specified` is a contract; `planned` is accepted future work.
- An unavailable integration does not automatically mean its underlying capability is unimplemented.
- A passing unit test does not prove native hardware, firmware, boot, driver or process behavior unless the test actually exercises that target.
- Do not convert a plan checkbox into an implementation status without source and verification evidence.

## 5. Required structure for engineering plans

Every new or materially revised plan must answer the following, using only sections relevant to its scope:

1. **Purpose and outcome:** user or engineering problem, target result and explicit non-goals.
2. **Current baseline:** existing source paths, behavior, tests, constraints and known defects.
3. **Capability inventory:** atomic capabilities with maturity and evidence, not one blanket status for a whole subsystem.
4. **Architecture:** module ownership, public interfaces, data flow, trust boundaries and failure domains.
5. **Dependencies:** prerequisite tasks, external projects, schemas, ABI/API versions and blocking decisions.
6. **Work packages:** bounded tasks that can be reviewed independently, with a named owner or owning component.
7. **Parallelization:** independent tasks that may proceed concurrently, plus shared files, interfaces and state that require serialization.
8. **Compatibility and migration:** supported platforms, version negotiation, backward compatibility and migration path.
9. **Security and privacy:** permissions, input limits, least privilege, data handling and destructive-action safeguards.
10. **Performance:** measured baseline, workload, units, environment, target budget and regression threshold, where performance is in scope.
11. **Verification:** positive, negative, boundary, regression and platform-specific tests, including what each test cannot prove.
12. **Acceptance criteria:** observable conditions for declaring each work package complete.
13. **Recovery:** failure handling, rollback, cancellation and preservation of user data.
14. **Documentation impact:** exact pages, schemas, examples, indexes and localized copies that must change with the implementation.
15. **Delivery record:** branch/PR/commit references and actual CI outcomes; never infer merge or verification from submission alone.

A plan may use a smaller layout for a narrow change, but must not omit dependencies, acceptance criteria or evidence when those affect correctness.

## 6. Unified execution lifecycle

Use the same lifecycle for documentation work and implementation work:

### Stage A — Inventory

- Enumerate relevant Markdown, plans, schemas, manifests, code and tests.
- Identify canonical documents, duplicate claims, stale links and undocumented behavior.
- Record the reviewed branch/revision and the scope of the audit.
- Mark unknown information as `not_assessed`; do not fill gaps with optimistic assumptions.

**Exit gate:** scope and sources are known; every affected document has an owner and a reason to change or remain unchanged.

### Stage B — Model

- Define the desired outcome, affected capabilities and non-goals.
- Map dependencies, shared interfaces, data ownership and failure modes.
- Decide which work is parallel-safe and which operations must remain sequential.
- Define measurable acceptance conditions before implementation.

**Exit gate:** contracts and acceptance checks are reviewable and do not conflict with existing source-of-truth documents.

### Stage C — Design and prepare

- Prefer existing project components and interfaces over duplicated implementations.
- Introduce schemas or versioned contracts when data crosses a stable module or repository boundary.
- Prepare migration notes, test fixtures, rollback steps and documentation changes.
- Keep design-only proposals explicitly at `specified` or `planned`.

**Exit gate:** the smallest useful, reversible implementation path is defined.

### Stage D — Implement in coordinated work packages

- Develop independent work packages in parallel only after their contracts are stable.
- Serialize edits to shared schemas, state migrations, central registries and common build files.
- Keep changes bounded, idiomatic, human-readable and aligned with the owning project's existing conventions.
- Integrate capabilities through narrow adapters; do not copy another repository's internals merely to make integration appear complete.
- Keep automation deterministic, idempotent, observable and least-privileged.

**Exit gate:** source changes are complete for the stated scope and no unreviewed dependency or destructive action is hidden in automation.

### Stage E — Verify

- Run focused tests first, then the relevant full repository test/build suite.
- Cover normal, malformed, boundary, failure and rollback cases.
- Compare optimized paths to a trusted reference implementation where applicable.
- Validate schemas, manifests, paths, links, commands and version references.
- Record exact revision, environment and actual results.

**Exit gate:** all required checks pass on the reviewed change, or any blocked/skipped check is disclosed and the capability remains below `verified`.

### Stage F — Integrate and document

- Update source-facing technical documentation, capability status and all affected indexes in the same delivery.
- Keep examples and commands executable on the stated platform.
- Update cross-project consumers when a public contract changes.
- Preserve existing authorship, license, trademark and third-party notices.
- Review the complete diff for contradictions, duplicated authority and accidental scope expansion.

**Exit gate:** documentation and code describe the same revision and supported behavior.

### Stage G — Adopt and measure

- Merge only through the repository's established review and CI policy.
- Record the resulting commit and the actual CI state.
- Measure the outcome against the baseline when the change makes a performance or reliability claim.
- Reopen the plan when a dependency, platform or acceptance assumption changes.

**Exit gate:** delivery state is recorded honestly, with no claim of merge, release or production readiness without evidence.

## 7. Interpretation of the 20 execution directives

The canonical wording and detailed engineering outcomes remain in [Repository-wide Implementation Directives](REPOSITORY_EVOLUTION_DIRECTIVES.md). This plan applies them as one operating model:

| Directive family | Operational meaning | Required control |
|---|---|---|
| Complete delivery: 1, 3, 4, 5 | Deliver a coherent end-to-end capability slice, including its tools, integration and operator guidance | Explicit scope, prerequisites, acceptance criteria and evidence |
| Parallel design and integration: 2, 6, 7, 9, 14, 15 | Coordinate independent design and automation, then integrate through stable interfaces | Dependency graph, ownership, versioned contracts and serialized shared-state changes |
| Systematic improvement: 8, 10, 11, 17 | Improve subsystems and tools using measured baselines and preserved behavior | Reproducible metrics, reference behavior and regression checks |
| Bounded scale and adaptation: 12, 13, 16, 18, 19 | Expand capacity and platform compatibility through staged, testable changes | Resource budgets, explicit platform matrix, compatibility checks and rollback |
| Coordinated extensibility refactor: 20 | Refactor extension points without breaking existing callers | Compatibility fixtures, migration notes and reviewable changes |

Interpretation safeguards:

- “Immediately”, “at once” and “without stopping” express priority; they never bypass review, tests, release gates or recovery.
- “All at once” means a complete coherent deliverable, not unlimited simultaneous changes to shared state.
- “Automatically” means predictable and bounded automation, not unrestricted execution or automatic installation.
- “Massively” and “batch” require an inventoried set of applicable modules and per-module regression checks.
- “Universal” means supported and evidenced portability, not an unsupported promise of compatibility with every platform.
- A direction that does not fit a component must be recorded as `not_applicable` with a concise reason.

## 8. Documentation update matrix

A code or contract change must trigger a targeted documentation review:

| Change type | Mandatory review |
|---|---|
| Public API, ABI, schema or serialized format | Owning contract document, schema, examples, tests, consumer docs and migration notes |
| Architecture or module boundary | Architecture, foundation architecture, information architecture, affected topic hub and implementation status |
| User-facing Mora behavior | Mora integration, application catalogue/specification, design system if visual behavior changes, root README where user workflow changes |
| CLI, terminal or native desktop operation | Relevant tool guide, command examples, tests, supported-platform notes and docs index |
| Runtime, driver, boot or hardware boundary | Architecture, boot/foundation contracts, implementation status, evidence and safety limitations |
| Repository federation or upstream pin | Federation registry, federation guide, submodule metadata, license/provenance review and CI |
| Catalogue or product identity | Machine-readable catalogue, schema, validator, catalogue documentation and launcher registry |
| Build, packaging, signing or deployment | Build contracts, deployment guide, schemas, CI and release/status records |
| Engineering or editorial policy | Canonical standard, control document, validators/tests and all directly dependent guidance |
| Documentation-only change | Relevant topic hub, documentation index, information architecture and Markdown quality checks |

Do not edit unrelated pages simply to create the appearance of a repository-wide rewrite. Every document must be reviewed against its subject; only relevant content is changed. Unchanged pages remain governed by the standard.

## 9. Quality and automation gates

The documentation workflow must remain compatible with existing project tooling and CI:

- Markdown prose diagnostics run through the repository's existing prose-quality workflow.
- Engineering-evolution JSON and its schema are validated by the canonical validator and tests.
- Repository federation and program-adoption contracts are validated by their existing tools.
- Internal relative links, headings, code fences and referenced paths are checked for each changed page.
- Commands are checked against the current CLI or build configuration before publication.
- No new dependency is added merely to duplicate an existing validator.
- Automated fixes must be deterministic, reviewable and safe to rerun; they must not rewrite unrelated files.

A green documentation check proves only the checks it ran. It does not prove that a described OS capability is implemented.

## 10. Localization, naming and authorship

- English technical identifiers, paths, command names, schema keys, enums and version IDs remain stable.
- Ukrainian and Russian localizations must carry the same meaning, maturity, warnings, non-goals and evidence strength as the canonical text.
- Do not translate a machine identifier or silently create competing localized values for the same contract.
- Project naming must remain consistent: the operating system is **Duck** / **DuckOS** according to the context; the programming language is **Reaper**.
- Attribute **Ivan-VHS** as project author/developer where appropriate. Preserve other contributors' authorship, copyright, licenses, trademarks and third-party notices.

## 11. Completion criteria for this plan

The documentation system may be marked as harmonized only when all of the following are true:

- [ ] All 32 Markdown files have been inventoried against the current repository tree.
- [ ] Every file has one primary topic owner and one clear authority level.
- [ ] The root README, documentation index and information architecture describe the same current navigation.
- [ ] Every plan distinguishes baseline, intended work, dependencies, acceptance, verification and delivery state.
- [ ] Every implementation claim uses the canonical maturity vocabulary and points to relevant evidence.
- [ ] No roadmap or catalogue entry is presented as proof of a shipped capability.
- [ ] Duplicate normative definitions have been consolidated into canonical documents.
- [ ] Internal links, referenced paths, commands, schemas and examples are checked.
- [ ] Localized documentation, where present, matches the canonical scope and warnings.
- [ ] The documentation CI checks pass on the exact reviewed revision.
- [ ] The final PR/commit and remaining exceptions are recorded.

The checklist tracks this documentation program. It must not be copied into product implementation status as proof of kernel, desktop, driver, boot or other system functionality.

## 12. Change control

This plan is subordinate to the Unified Documentation Standard and complements the canonical 20 execution directives. If the documents conflict, resolve the conflict in this order:

1. preserve source, schema and ABI/API compatibility;
2. preserve the canonical terminology and evidence requirements;
3. preserve the original project-specific scope and safety boundary;
4. update the affected canonical document, then its summaries and indexes;
5. record migration and review the full affected-document set.

Changes to this plan must identify the reason, affected documents, migration implications and verification performed. Do not create a second plan that redefines the same lifecycle.

---

**Attribution:** Ivan-VHS, where appropriate to project authorship. Existing contributor, copyright and license notices remain intact.
