# Ivan-VHS Project Evolution Ladder

**Document ID:** `IVAN-VHS-PROJECT-LADDER-001`  
**Version:** 1.0  
**Applies to:** every active Ivan-VHS repository and cross-repository integration  
**Machine-readable record:** `.github/project-ladder.v1.json`  
**Schema:** `schemas/project-ladder.v1.schema.json`

## Purpose

The Project Evolution Ladder gives every repository one shared, evidence-led progression from a defined project to a mature, independently reproducible product and ecosystem. It complements, but does not replace, capability maturity in [the Unified Documentation and Semantics Standard](UNIFIED_DOCUMENTATION_STANDARD.md).

A rung is the **highest cumulative gate supported by evidence at the recorded revision**. Names communicate progression; they are not a score, a feature count or a marketing claim.

## The ten rungs

| Rung | Name | Entry and exit gate |
|---:|---|---|
| 01 | **Genesis** | Purpose, users, intended runtime, supported targets, non-goals, risks and ownership are explicit. Exit: reviewed scope and dependency map. |
| 02 | **Foundation** | Architecture boundaries, core contracts, repository policy, reproducible bootstrap/build, baseline tests and CI exist. Exit: clean baseline checks and contributor/security guidance. |
| 03 | **Evolution** | At least one bounded vertical slice works in the actual supported runtime; success, invalid-input and failure paths have regression checks; limits are stated. Exit: source paths, repeatable tests and truthful implementation status. |
| 04 | **Ascension** | Multiple real modules or project boundaries work together through explicit, versioned interfaces. Error, resource and compatibility behavior is defined. Exit: contract/integration tests and CI exercise the connected path. |
| 05 | **Vanguard** | The primary delivery path is implemented on its declared target runtime (native when promised), not only as a mock, catalogue or host-side policy model. Reproducible target builds, initial platform coverage and measurable resource/performance budgets exist. |
| 06 | **Frontier** | Declared platform/architecture coverage is exercised; threat model and privilege boundaries are tested; relevant fuzz/property/fault-injection and accessibility checks exist. Hardware claims require named device or emulator evidence. |
| 07 | **Dominion** | All accepted P0/core capabilities in the versioned product scope meet their acceptance criteria. Compatibility and migration behavior is defined; critical/high-risk gaps have owners and closure evidence. |
| 08 | **Apex** | A release candidate is produced through a repeatable pipeline. Artifact provenance/integrity, security gates, compatibility and performance matrices, plus install/upgrade/rollback or equivalent recovery tests are recorded. |
| 09 | **Zenith** | A stable supported release has a maintenance/support policy, recovery and operational documentation, sustained release-branch regression evidence and controlled deprecation. No release-blocking critical defect is hidden by the rung. |
| 10 | **Singularity** | The product and its relevant ecosystem can be rebuilt and validated end-to-end from declared inputs, with an auditable evidence chain and independently repeatable integration. Self-hosting/native self-integration is required only when it is part of the declared product design. |

## Promotion rules

1. **Cumulative gates:** no rung can be skipped; later rungs include all earlier gates.
2. **Evidence wins:** roadmap text, mock-ups, schemas, catalogues, badges and planned APIs do not prove implementation. Link source, tests, workflows, artifacts or review records.
3. **Assessment modes:** `provisional` means the record was assessed from repository evidence but relevant checks were not re-run during that assessment; `verified` means the gate was checked at a named revision and environment.
4. **Highest complete rung:** `current_rung` is the highest gate fully supported. Aspirational work belongs in `next_rung` and `next_gate`.
5. **Reassess regressions:** if a required gate stops passing, downgrade the rung or mark the assessment provisional until evidence is restored.
6. **Not applicable is explicit:** explain why a genuinely irrelevant gate does not fit. Do not silently waive applicable requirements.
7. **Capability statuses stay separate:** individual capabilities continue to use the maturity identifiers in the Unified Documentation Standard.
8. **No version-number collision:** this ladder is not SemVer, a release channel, a Git branch or a boot/runtime sequence. Preserve domain-specific terms such as DuckOS **Stage 1** boot. Use `Rung 04 — Ascension` or `Ladder 04/10` for project maturity.

## Repository record

Each repository owns `.github/project-ladder.v1.json` and a short `docs/PROJECT_LADDER.md` page (DuckOS owns this canonical page). The record identifies project, rung, assessment mode, date, evidence paths and next gate.

Initial cross-repository baseline — 25 November 2026:

| Repository | Current rung | Assessment | Next rung |
|---|---|---|---|
| [DuckOS](https://github.com/Ivan-VHS/DuckOS) | **03 — Evolution** | Provisional; native Stage 1 boot slice and tested Reaper policy contracts are documented, but this is not a usable process/service OS session. | 04 — Ascension |
| [Reaper](https://github.com/Ivan-VHS/Reaper) | **04 — Ascension** | Provisional; reference runtime, CLI/REPL, Studio, LSP/DAP and partial native C17 track are documented. Native parity is not claimed. | 05 — Vanguard |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | **04 — Ascension** | Provisional; bounded C11 core, portable CLI, Windows GUI, versioned ABI and test/build workflows are documented. | 05 — Vanguard |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | **04 — Ascension** | Provisional; device inventory, bounded package inspection, compatibility evidence and local reporting form a documented read-only workflow. | 05 — Vanguard |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | **04 — Ascension** | Provisional; native offline renderer, DSP routing, plugin lifecycle, manifest exchange and desktop integration are documented. | 05 — Vanguard |

These are **documentation-review snapshots**, not new CI certifications. No tests were executed as part of initial ladder adoption. Each next promotion requires a fresh source/test/CI review and an updated record.

## Initial next gates

| Repository | 05 — Vanguard promotion focus |
|---|---|
| DuckOS | Move beyond the experimental boot slice: deliver and test further native kernel/runtime primitives and establish a versioned native boundary to Reaper without conflating reference policy with kernel enforcement. |
| Reaper | Compile and execute a declared `.rpr` subset through the native path; add reference/native parity fixtures, ABI checks and reproducible target CI. |
| Pytyliki | Exercise the declared C11 core/ABI target matrix in CI, preserve bounded behavior across compilers and record repeatable performance/failure baselines. |
| OPlague | Exercise the end-to-end inspection/report path in the declared Windows CI target; add adversarial/fuzz coverage for untrusted PE, INF, ZIP and UDRV inputs while preserving read-only behavior. |
| VentuSample | Verify deterministic golden renders across declared platforms; stress plugin lifecycle and invalid-input handling; record DSP resource/performance budgets and compatibility evidence. |

## Cross-repository change control

DuckOS maintains the canonical ladder text and schema. Product repositories own their implementation and evidence. Shared changes that affect several repositories should be proposed in coordinated, separately reviewable PRs. Update each local record in the same PR as a material change to scope, runtime, integration boundary or acceptance evidence. A project-level rung never upgrades the maturity of an individual capability.
