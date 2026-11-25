# DAK Engineering Maturity Ladder

**Document ID:** `DAK-PROJECT-MATURITY-001`  
**Version:** 1.1  
**Applies to:** DAK and the Reaper, Pytyliki, OPlague and VentuSample repositories  
**Machine-readable record:** `.github/project-ladder.v1.json` in each repository  
**Canonical schema:** `schemas/project-ladder.v1.schema.json`

## Purpose

The DAK Engineering Maturity Ladder is a cumulative, evidence-led model for assessing a project from a defined scope to a reproducible, independently validated ecosystem. It is a delivery gate, not a score, feature count, release number or marketing badge.

A project’s current stage is the highest consecutive stage whose exit criteria are supported by repository evidence. Stage names and ordering are fixed. Project-specific work may differ, but the required evidence classes do not.

## The ten stages

| Stage | Name | Entry and exit criteria |
|---:|---|---|
| 01 | **Genesis** | Purpose, users, intended runtime, supported targets, non-goals, risks and ownership are explicit. Exit: reviewed scope and dependency map. |
| 02 | **Foundation** | Architecture boundaries, core contracts, repository policy, reproducible bootstrap/build, baseline tests and CI exist. Exit: clean baseline checks and contributor/security guidance. |
| 03 | **Evolution** | At least one bounded vertical slice works in the actual supported runtime; success, invalid-input and failure paths have regression checks; limits are stated. Exit: source paths, repeatable tests and truthful implementation status. |
| 04 | **Ascension** | Multiple real modules or project boundaries work together through explicit, versioned interfaces. Error, resource and compatibility behavior is defined. Exit: contract/integration tests and CI exercise the connected path. |
| 05 | **Vanguard** | The primary delivery path is implemented on its declared target runtime (native when promised), not only as a mock, catalogue or host-side policy model. Reproducible target builds, initial platform coverage and measurable resource/performance budgets exist. |
| 06 | **Frontier** | Declared platform/architecture coverage is exercised; threat model and privilege boundaries are tested; relevant fuzz/property/fault-injection and accessibility checks exist. Hardware claims require named device or emulator evidence. |
| 07 | **Dominion** | All accepted P0/core capabilities in the versioned product scope meet their acceptance criteria. Compatibility and migration behavior is defined; critical/high-risk gaps have owners and closure evidence. |
| 08 | **Apex** | A release candidate is produced through a repeatable pipeline. Artifact provenance/integrity, security gates, compatibility and performance matrices, plus install/upgrade/rollback or equivalent recovery tests are recorded. |
| 09 | **Zenith** | A stable supported release has a maintenance/support policy, recovery and operational documentation, sustained release-branch regression evidence and controlled deprecation. No release-blocking critical defect is hidden by the stage. |
| 10 | **Singularity** | The product and its relevant ecosystem can be rebuilt and validated end-to-end from declared inputs, with an auditable evidence chain and independently repeatable integration. Self-hosting/native self-integration is required only when it is part of the declared product design. |

## Machine-readable stage states

Every repository owns `.github/project-ladder.v1.json`. The record contains ten ordered stage entries:

- `met`: all required evidence categories for that stage are present and point to existing repository artifacts.
- `pending`: the stage is not complete. Later stages cannot be marked complete across a pending stage.
- `not_applicable`: the stage has a documented, reviewable rationale; it is not a silent waiver.

`current_stage` must equal the highest consecutive `met` or justified `not_applicable` stage. The record also stores the next stage and actionable acceptance work.

Evidence paths must be repository-relative, resolve inside the repository, and point to an existing file or directory. The validator rejects missing paths, path traversal, escaping symlinks, stage reordering, missing evidence classes and skipped gates.

## Evidence classes by stage

| Stage | Required evidence kinds |
|---:|---|
| Genesis | `scope` |
| Foundation | `architecture`, `policy`, `build`, `ci` |
| Evolution | `source`, `tests`, `runtime` |
| Ascension | `integration`, `contract_tests`, `ci` |
| Vanguard | `target_build`, `resource_budget` |
| Frontier | `platform_coverage`, `threat_model`, `security_tests`, `fuzz_or_fault_tests`, `accessibility` |
| Dominion | `core_acceptance`, `compatibility`, `migration` |
| Apex | `release_candidate`, `provenance`, `recovery` |
| Zenith | `support_policy`, `operations`, `release_regression`, `deprecation` |
| Singularity | `reproducible_rebuild`, `audit_chain`, `independent_integration` |

## Assessment modes

- `provisional`: repository evidence has been reviewed, but the relevant checks were not re-run as part of that assessment. It is not a new CI certification.
- `verified`: the record identifies an exact commit, workflow, environment and CI run URL. Test and CI evidence must be present. Vanguard or higher also requires verified target-artifact evidence.

A change in source, tests, CI, target support or acceptance criteria requires reassessment. If a required gate regresses, lower the current stage or return the assessment to provisional until evidence is restored.

## Initial repository baseline — 25 November 2026

| Repository | Current stage | Assessment | Next stage |
|---|---:|---|---|
| [DAK](https://github.com/Ivan-VHS/DAK) | **03 — Evolution** | Provisional; the experimental x86-64 Stage 1 boot slice is distinct from a usable process/service OS session. | 04 — Ascension |
| [Reaper](https://github.com/Ivan-VHS/Reaper) | **04 — Ascension** | Provisional; the reference runtime, CLI/REPL, Studio, language services and versioned project contracts are documented. Native compiler parity is not claimed. | 05 — Vanguard |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | **04 — Ascension** | Provisional; the bounded C11 core, portable CLI, Windows desktop, versioned C ABI and test/build workflows are documented. | 05 — Vanguard |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | **04 — Ascension** | Provisional; read-only device/package inspection, structured evidence and the optional versioned Reaper boundary are documented. | 05 — Vanguard |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | **04 — Ascension** | Provisional; the native offline renderer, DSP modules, plugin/manifest boundaries and optional Reaper integration are documented. | 05 — Vanguard |

These are provisional documentation/source-path assessments. The complete product test matrices and target workflows were not re-run during ladder adoption. No repository is promoted to Vanguard or beyond by this change.

## Initial promotion focus

| Repository | 05 — Vanguard promotion focus |
|---|---|
| DAK | Move beyond the experimental boot slice: deliver and test further native kernel/runtime primitives and establish a versioned native boundary to Reaper without conflating reference policy with kernel enforcement. |
| Reaper | Compile and execute a declared `.rpr` subset through the native path; add reference/native parity fixtures, ABI checks and reproducible target CI. |
| Pytyliki | Exercise the declared C11 core/ABI target matrix in CI, preserve bounded behavior across compilers and record repeatable performance/failure baselines. |
| OPlague | Exercise the end-to-end inspection/report path in the declared Windows CI target; add adversarial/fuzz coverage for untrusted PE, INF, ZIP and UDRV inputs while preserving read-only behavior. |
| VentuSample | Verify deterministic golden renders across declared platforms; stress plugin lifecycle and invalid-input handling; record DSP resource/performance budgets and compatibility evidence. |

## CI and promotion procedure

Each repository runs:

```sh
node tools/validate_project_ladder.mjs
node --test tests/project-ladder.test.mjs
```

The dedicated `.github/workflows/project-ladder.yml` executes these checks on pull requests, pushes and manual dispatch. It validates the canonical schema identifier, exact stage order, cumulative status, required evidence categories and repository-local evidence paths.

Update the local record in the same pull request as a material implementation or scope change. Keep stage evidence tied to source, tests, workflows, target artifacts and operational records. Do not mark a stage complete because its name, API, mock-up, catalogue entry or roadmap item exists.

## Release and version boundaries

This ladder is independent of SemVer, release channels, branch names, boot stages and runtime lifecycle states. Use `Stage 04 — Ascension` or `Maturity 04/10` for project maturity; preserve domain-specific terms such as the DAK **Stage 1** boot sequence.
