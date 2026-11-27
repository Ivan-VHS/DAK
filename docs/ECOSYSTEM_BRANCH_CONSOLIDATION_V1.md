# Ecosystem branch consolidation and mainline safety v1

**Snapshot:** 2026-11-26 UTC  
**Coordinator:** DAK ecosystem repository  
**Scope:** the five owner repositories currently visible to the linked GitHub account: DAK, OPlague, Pytyliki, Reaper and VentuSample.  
**Purpose:** consolidate reviewed pull-request work into each repository's own `main` without losing dependency order, provenance, tests or rollback capability.

This is a coordination and execution standard, not a statement that the open pull requests have been reviewed or merged. The snapshot counts and dependency edges below were collected from GitHub branch, pull-request, ruleset and main-branch metadata. A complete code review and green CI result are still required for every PR before it can merge.

## 1. Inventory snapshot

Branch counts include `main`. Open PR counts include only PRs returned with `state=open`; closed and merged PRs are excluded.

| Repository | Main SHA at snapshot | Branches | Open PRs | Draft PRs | PRs based on another branch |
|---|---|---:|---:|---:|---:|
| [DAK](https://github.com/Ivan-VHS/DAK) | `30bd33be646252f0f26745fa01e38e0f3972839f` | 226 | 127 | 1 | 12 |
| [OPlague](https://github.com/Ivan-VHS/OPlague) | `496506c461da84a9a68cc8cae3b5273334fcbbf4` | 158 | 60 | 1 | 0 |
| [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) | `4936685d1cd6f083f315c64e5aaaaa9c29af6aab` | 215 | 81 | 1 | 0 |
| [Reaper](https://github.com/Ivan-VHS/Reaper) | `c0ac1aa2b09866d8c41bd3ff12104000f78d473f` | 344 | 181 | 5 | 23 |
| [VentuSample](https://github.com/Ivan-VHS/VentuSample) | `d2831b1481dcdee07cd1ab2c4e23055314a7bdfb` | 135 | 59 | 1 | 0 |
| **Total** | — | **1,078** | **508** | **9** | **35** |

The inventory is intentionally repository-wide. It is not evidence that all 508 diffs have been inspected. The 35 non-main-base PRs are the first mandatory dependency-graph review set. The remaining 473 main-based PRs still need duplicate/overlap, CI, review and compatibility classification.

The recovery refs have now been created and verified against the exact SHAs in this table:

| Repository | Recovery branch | Verified target SHA |
|---|---|---|
| DAK | [backup/pre-consolidation-main-2026-11-26](https://github.com/Ivan-VHS/DAK/tree/backup/pre-consolidation-main-2026-11-26) | `30bd33be646252f0f26745fa01e38e0f3972839f` |
| OPlague | [backup/pre-consolidation-main-2026-11-26](https://github.com/Ivan-VHS/OPlague/tree/backup/pre-consolidation-main-2026-11-26) | `496506c461da84a9a68cc8cae3b5273334fcbbf4` |
| Pytyliki | [backup/pre-consolidation-main-2026-11-26](https://github.com/Ivan-VHS/Pytyliki/tree/backup/pre-consolidation-main-2026-11-26) | `4936685d1cd6f083f315c64e5aaaaa9c29af6aab` |
| Reaper | [backup/pre-consolidation-main-2026-11-26](https://github.com/Ivan-VHS/Reaper/tree/backup/pre-consolidation-main-2026-11-26) | `c0ac1aa2b09866d8c41bd3ff12104000f78d473f` |
| VentuSample | [backup/pre-consolidation-main-2026-11-26](https://github.com/Ivan-VHS/VentuSample/tree/backup/pre-consolidation-main-2026-11-26) | `d2831b1481dcdee07cd1ab2c4e23055314a7bdfb` |

**Important:** GitHub reports `protected=false` for all five recovery branches. They are verified snapshot refs, but they are not immutable. Before any merge campaign begins, configure protection against force-push/deletion or add independently retained annotated snapshot tags through the repository's release/administration process. Do not rely on these branch names alone as the only recovery mechanism.

## 2. Existing main rulesets

All five repositories have an active ruleset targeted at `refs/heads/main`. The traditional branch-protection endpoint did not report a legacy protection configuration; the active rulesets are the current protection mechanism.

| Repository | Active ruleset | Required status contexts | Merge method | Required approvals |
|---|---|---|---|---:|
| DAK | Auto-Merge Ruleset | Python 3.10, Python 3.11, Python 3.12, Native C | squash only | 0 |
| OPlague | OPlague Main Auto-Merge Ruleset | README, LICENSE | squash only | 0 |
| Pytyliki | Pytyliki Main Auto-Merge Ruleset | Ubuntu, Windows, Linux Sanitizer | squash only | 0 |
| Reaper | Reaper Main Auto-Merge Ruleset | Python 3.10, Python 3.11, Python 3.12, Native C | squash only | 0 |
| VentuSample | Main Auto-Merge Ruleset | Python 3.10, Python 3.11, Python 3.12, Native C | squash only | 0 |

The rulesets use strict status checks and block branch deletion, and require PRs. They currently do **not** require a submitted approval or Code Owner review. OPlague has a material gap: README and LICENSE are not substitutes for compile, unit, security and runtime checks. Before a broad OPlague merge campaign, replace those two contexts with real required assurance jobs and verify that the workflows actually emit those exact check names.

Do not weaken or bypass a ruleset to make a PR merge. If a required check is absent, fix the workflow/ruleset contract in a separate reviewed change.

## 3. Dependency graph: merge parents before children

### DAK

Known open stacked chains:

```text
#1 release/0.1.0-rc.1
  └─ #5 work/native-os-foundation
      ├─ #8 feat/duckos-core-services-v2
      │   └─ #18 feat/evening-courier-newsroom
      └─ #98 feat/predictive-security-native

#161 feat/reaper-first-desktop-policy-core
  ├─ #167 feat/duckos-desktop-dabi64-host-v1
  │   └─ #168 feat/software-framebuffer-compositor-v1
  └─ #175 feat/reaper-industrial-glass-motion-contracts

#177 feat/desktop-dabi64-ipc-foundation
  └─ #178 feat/desktop-kernel-capability-broker
      └─ #179 feat/desktop-framebuffer-compositor

#165 feat/figma-visual-integration-2026-11-25
  └─ #172 feat/industrial-glass-digital-physics-v1

#133 native/mora-desktop-shell-2026-11-25
  └─ #74 feat/mora-native-interaction-quality
```

Two additional current base references need parent resolution before merge: #174 is based on `feat/mora-native-shell`; #74's base is `native-mora-desktop`, which must be confirmed against the intended parent history before restacking. Do not substitute a similarly named branch. Re-check all 12 stacked PRs, not only the edges shown above, immediately before execution.

### Reaper

Known open stacked chains:

```text
#338 feat/selfhosted-statement-parser
  └─ #368 feat/typed-structures-platforms-v1
      ├─ #386 feat/typed-craft-signatures-result-option
      └─ #387 feat/typed-compiler-pipeline-v1

#362 foundations 1–5
  └─ #366 foundations 6–10
      └─ #370 foundations 11–15
          └─ #371 foundations 16–20
              └─ #372 foundations 21–25
                  └─ #373 foundations 26–30
                      └─ #374 foundations 31–35
                          └─ #375 foundations 36–40
                              └─ #376 foundations 41–45
                                  └─ #379 foundations 46–50
                                      └─ #380 foundations 51–55
                                          └─ #383 foundations 56–60
                                              └─ #384 foundations 61–65
                                                  └─ #385 foundation 66 umbrella

#358 PLAGUE foundation
  └─ #364 aesthetic architecture/evolution
      └─ #382 aesthetic native apply engine

#354 RForge product-factory specification
  └─ #357 RForge framework archetypes

#333 framework-federation-20
  └─ #356 federation handlers

#308 System Runtime ABI v1
  └─ #316 Reaper System Runtime bindings
```

#353 DOM foundation targets `feat/native-reaper-frameworks-v1-20261125`, and #367 targets #353. The parent of that base branch must be identified before the chain can be placed in the mainline order. The 23 stacked PRs require a full fresh graph walk; the chains above are the confirmed high-value edges, not a claim that every edge has been resolved.

### OPlague, Pytyliki and VentuSample

The current open PR inventory shows all 60 OPlague, 81 Pytyliki and 59 VentuSample PRs targeting `main`. No stacked base-branch PRs were detected in those snapshots. They still have cross-repository interface dependencies: OPlague's device evidence and read-only adapters, Pytyliki's processor/Win32 and Reaper contracts, and VentuSample's offline DSP/audio format and Reaper consumer contracts must be validated against pinned peer revisions before release.

## 4. Required merge policy

1. **Never merge every Git branch.** Only an open PR with a reviewed, bounded change is a merge candidate. A branch without an open PR must first be classified as active work, stale work, release support or an orphan; do not merge it merely because it exists.
2. **Freeze a snapshot per repository.** Record the exact current `main` SHA and create a protected backup ref before the first merge. Do not reuse the 2026-11-26 snapshot SHA after main advances.
3. **Fetch and inspect.** On the operator workstation run `git fetch --all --prune`, `git status --short --branch`, inspect `git stash list`, and confirm local work is committed or intentionally preserved. Update `main` with `git pull --ff-only`; do not create an incidental merge commit.
4. **Classify every PR.** Record owner, head/base refs and SHAs, draft state, changed files, raw diff size, line/file counts, commit age, dependencies, duplicate scope, labels, requested reviewers, review threads, CI jobs, security checks and runtime evidence.
5. **Build a directed acyclic dependency graph.** An edge A → B means B is based on A. Merge or otherwise resolve A before B. If a parent branch is not represented by a PR, stop and identify its provenance rather than guessing.
6. **Use one PR at a time per dependency chain.** Independent, disjoint PRs may be reviewed in parallel, but only one PR from a stacked chain advances at a time. Do not combine unrelated branches into one giant integration PR.
7. **Respect the repository's squash-only rulesets.** Merge using the PR's squash method only. Do not use merge commits or rebase merges into `main`. After a parent is squashed, rebase the child onto the new parent/`main` with a lease-safe update and rerun all checks.
8. **Never merge on queued, pending, skipped-required, failing or missing checks.** Confirm the exact required contexts from the current ruleset; a green workflow with a different display name does not satisfy the gate.
9. **Review before auto-merge.** Inspect the actual patch and resolved review threads. The rulesets currently require zero approvals, so their presence alone does not prove a code review occurred. Record the review decision and reviewer in the PR before enabling auto-merge.
10. **Test after each merge.** Run the repository's required CI and appropriate integration/runtime smoke tests after every parent or high-risk merge. If a check exposes a regression, stop that chain and revert the offending squash commit with a new revert PR; do not rewrite published main.
11. **Keep PRs reviewable.** Target less than 1 MB raw diff, fewer than 20,000 changed lines and fewer than 300 changed files per PR. Split coherent work into reviewable PRs; use Git LFS or release/CI artifacts for large binaries and generated payloads.
12. **Do not delete branches automatically.** Delete only after the PR is merged, its merge commit is verified, no open PR or downstream branch uses it as a base, and no release or rollback process depends on it. Preserve backup refs and useful release branches.
13. **Do not release by branch-count.** Create a version tag only after the product owner selects the version, compatibility policy is documented, release artifacts are reproducible, checksums are verified and the release matrix passes. No blanket `v2.0` tag is implied by this plan.

## 5. Per-repository acceptance matrix

| Repository | Required build/runtime evidence before a merge batch is called complete |
|---|---|
| DAK | CI contexts above; kernel build, CTest and QEMU BIOS/UEFI smoke for boot/kernel changes; native desktop smoke for Qt changes; federation pin/integrity validation for peer updates |
| OPlague | Real Rust/Slint build and tests, security/read-only policy checks, device snapshot fixture tests, supported platform checks; replace README/LICENSE-only branch contexts |
| Pytyliki | Ubuntu and Windows builds, Linux sanitizer, CTest/processor tests, Win32 UI smoke when affected, Reaper ABI compatibility checks |
| Reaper | Python 3.10/3.11/3.12 compatibility CI, Native C, typed/self-host conformance, IR/Span parity and native-host smoke for compiler/runtime changes |
| VentuSample | Python 3.10/3.11/3.12, Native C/native DSP build, CTest/unit and format-boundary tests, plugin lifecycle/reentrancy tests, offline audio fixture comparisons |

Only run the tests appropriate to a PR's touched subsystems, but required ruleset checks remain mandatory for every merge.

## 6. Execution waves

**Wave A — protection and provenance.** Repair missing/weak required checks (especially OPlague), record current ruleset definitions, ensure PR/branch metadata is complete, resolve every non-main parent and establish immutable backup refs.

**Wave B — roots of stacked chains.** Start with root PRs such as DAK #1/#161/#165/#177/#133 and Reaper #338/#362/#358/#354/#333/#308, but do not treat the examples as approved: each still needs patch review and green CI. Merge only after its child graph and target compatibility are understood.

**Wave C — stacked core descendants.** Advance DAK and Reaper dependency chains strictly topologically. Restack and retest each child after its parent is merged. Do not merge the entire framework series or native desktop chain in one operation.

**Wave D — main-based independent work.** Review and merge domain PRs in bounded batches within each repository: DAK kernel/platform and desktop; OPlague inspection/security; Pytyliki processor/Win32; VentuSample DSP/audio; Reaper language/compiler/runtime. Cross-repository producer/consumer changes must be coordinated by contract version and pinned commit.

**Wave E — documentation, cleanup and release.** Update docs and changelogs after implementation state is verified; remove only proven-obsolete branches; verify mainline CI and artifacts; then prepare a separately reviewed release tag.

## 7. Operator checklist derived from the 50-step plan

- [ ] Backup refs and snapshot SHAs recorded for all five repositories.
- [ ] Local worktree is clean or all intentional local changes are preserved.
- [ ] Full branch and open-PR pagination completed; orphan and stale branches classified.
- [ ] Every open PR has a dependency/overlap entry and a bounded diff.
- [ ] All 35 stacked PRs have complete parent provenance and a topological order.
- [ ] Required checks and review policy gaps are resolved in repository rulesets.
- [ ] One parent PR is merged by squash only; downstream branches are restacked.
- [ ] Required CI and subsystem tests pass after each merge.
- [ ] Conflict resolutions, reverted batches and migration notes are recorded.
- [ ] Full mainline validation, compatibility and release evidence are green.
- [ ] Branch deletion and release tagging are performed only after explicit verification.

## 8. Current execution status

**Inventory and ruleset inspection:** complete for the five owned repositories listed above.  
**Known dependency mapping:** partial; the DAK and Reaper stacks are enumerated above, with explicitly unresolved parent refs noted.  
**Full patch review of all 508 open PRs:** not complete.  
**Campaign-wide passing CI:** not established. Recent sampled workflows were queued, and not every PR's check runs were reviewed.  
**Merges performed by this inventory pass:** none. No PR was merged or branch deleted without its own review and passing required checks.

The next safe action is to finish the 35 stacked-PR graph and review the main-based candidates in small groups, starting with protection/CI gaps. This page must be updated with each merge commit SHA, CI run, restack and branch cleanup so it remains an auditable execution ledger rather than a static promise.
