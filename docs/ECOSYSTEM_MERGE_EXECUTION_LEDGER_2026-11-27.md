# Full-spectrum integration scan — execution ledger

**Snapshot date:** 2026-11-27  
**Coordinator repository:** `Ivan-VHS/DAK`  
**Scope:** DAK, Reaper, Pytyliki, OPlague and VentuSample.  
**Mode:** read-only inventory and evidence-based triage, followed by a single verified documentation merge. No protection bypass, force-push, destructive cleanup or blind conflict resolution was used.

## 1. Current inventory

The GitHub branch and pull-request collection endpoints were paginated to completion for all five repositories. Branch counts include `main`.

| Repository | Current branches | Open PRs | Draft PRs | PRs based on another branch |
|---|---:|---:|---:|---:|
| DAK | 228 | 128 | 1 | 12 |
| Reaper | 349 | 184 | 7 | 23 |
| Pytyliki | 216 | 81 | 1 | 0 |
| OPlague | 159 | 60 | 1 | 0 |
| VentuSample | 137 | 60 | 1 | 0 |
| **Total** | **1,089** | **513** | **11** | **35** |

Of the 513 open PRs, 478 target `main` and 35 are stacked on another branch. The 35 stacked PRs must be resolved in dependency order; they are not 35 independent merge candidates.

The scan covers branches and open PRs that currently exist on GitHub. It does not recover deleted refs from Git object history, inspect workstation-local branches or stashes, or enumerate all forks. The connector did not permit the GitHub tags or forks collection endpoints in this scan. Releases were readable: DAK had one published release; the other four repositories returned none.

## 2. Mainline snapshot

| Repository | Default branch | Observed main SHA |
|---|---|---|
| DAK | `main` | `549da8190bc372c14606bdc691e9578e47f488d2` |
| Reaper | `main` | `a047a6fb2b721c549709f5e8a30fc2c603fdf0af` |
| Pytyliki | `main` | `4936685d1cd6f083f315c64e5aaaaa9c29af6aab` |
| OPlague | `main` | `496506c461da84a9a68cc8cae3b5273334fcbbf4` |
| VentuSample | `main` | `d2831b1481dcdee07cd1ab2c4e23055314a7bdfb` |

DAK's SHA above is the verified post-merge main head after DAK #208.

## 3. Dependency graph findings

### DAK — 12 stacked PRs

| Child PR | Parent PR / branch | Finding |
|---|---|---|
| #5 | #1 | Parent/head SHA matches |
| #98 | #5 | Parent/head SHA matches |
| #8 | #5 | Base SHA is stale versus current parent head |
| #18 | #8 | Parent/head SHA matches |
| #167 | #161 | Parent/head SHA matches |
| #168 | #167 | Parent/head SHA matches |
| #175 | #161 | Parent/head SHA matches |
| #172 | #165 | Parent/head SHA matches |
| #178 | #177 | Base SHA is stale versus current parent head |
| #179 | #178 | Base SHA is stale versus current parent head |
| #74 | #67 | Base SHA is stale versus current parent head |
| #174 | #159 (merged) | Parent provenance verified; #159 merged to main |

### Reaper — 23 stacked PRs

| Child PR | Parent PR / branch | Finding |
|---|---|---|
| #366 | #362 | Parent #362 is already merged into main; restack child onto current main |
| #370 | #366 | Base SHA is stale versus current parent head |
| #371 | #370 | Parent/head SHA matches |
| #372 | #371 | Parent/head SHA matches |
| #373 | #372 | Parent/head SHA matches |
| #374 | #373 | Parent/head SHA matches |
| #375 | #374 | Parent/head SHA matches |
| #376 | #375 | Parent/head SHA matches |
| #379 | #376 | Parent/head SHA matches |
| #380 | #379 | Parent/head SHA matches |
| #383 | #380 | Parent/head SHA matches |
| #384 | #383 | Base SHA is stale versus current parent head |
| #385 | #384 | Parent/head SHA matches |
| #338 | `main` | Root of typed compiler chain |
| #368 | #338 | Base SHA is stale versus current parent head |
| #386 | #368 | Parent/head SHA matches |
| #387 | #368 | Parent/head SHA matches |
| #358 | `main` | Root of PLAGUE / aesthetic chain |
| #364 | #358 | Parent/head SHA matches |
| #382 | #364 | Parent/head SHA matches |
| #336 | `main` | Parent of DOM foundation chain |
| #353 | #336 | Base SHA is stale versus current parent head |
| #367 | #353 | Parent/head SHA matches |
| #333 | `main` | Parent of federation-handler chain |
| #356 | #333 | Base SHA is stale versus current parent head |
| #354 | `main` | Parent of RForge archetype chain |
| #357 | #354 | Base SHA is stale versus current parent head |
| #308 | `main` | Parent of System Runtime binding chain |
| #316 | #308 | Parent/head SHA matches |

**Stale dependency edges requiring restack/revalidation:** DAK #8, #74, #178 and #179; Reaper #368, #370, #384, #353, #356 and #357.  
**Parent provenance:** DAK #174 is based on #159, which was merged to main on 2026-11-25. Its ancestry is known; restack and revalidate it against current main before merge.

## 4. Review-overlap clusters

These are candidates for semantic consolidation, not automatically confirmed duplicates:

- **DAK framebuffer/compositor:** #168 and #179 both implement software framebuffer composition, but in different source trees and against different parent chains. Review architectural ownership and avoid landing two competing scanout paths.
- **DAK native desktop:** #67 and #133 both replace the browser-oriented desktop experience with native desktop work. Their file sets overlap in catalogs, documentation, build and launch behavior; choose one canonical native path or explicitly divide responsibilities before merge.
- **Reaper source provenance:** #264, #267 and #270 overlap in lexer/parser/source-span/IR files. Define one canonical SourceSpan and semantic-IR contract, then consolidate implementation and tests rather than accepting conflicting versions independently.
- **Cross-repository CLife, security, governance and visual work:** repeated names across repositories are not sufficient evidence of duplication. Keep project-specific implementations, but compare shared contracts and avoid copying incompatible APIs.

## 5. Main branch rulesets

All five repositories have an active ruleset for `main`. All allow squash merges only, require zero approvals, do not require Code Owner review or review-thread resolution, and report no bypass actors.

| Repository | Required status contexts |
|---|---|
| DAK | Python 3.10, Python 3.11, Python 3.12, Native C |
| Reaper | Python 3.10, Python 3.11, Python 3.12, Native C |
| Pytyliki | Ubuntu, Windows, Linux Sanitizer |
| OPlague | README, LICENSE |
| VentuSample | Python 3.10, Python 3.11, Python 3.12, Native C |

**Release blocker:** OPlague's required contexts are documentation checks only. Before its merge campaign, change the ruleset/workflow contract so real Rust/Slint build, unit, security and platform checks are required and the exact emitted check names match the ruleset. Across all five repositories, introduce review assurance and Code Owner requirements through separately verified policy changes; do not disable existing protections to accelerate merging.

## 6. CI failures confirmed in sampled dependency roots and high-impact PRs

The following are observed failures in the latest PR-triggered workflow runs returned for the sampled heads. They are blockers until fixed and rerun successfully.

| Repository / PR | Failed check | Failure evidence |
|---|---|---|
| DAK #5 | DuckOS native bring-up | `wlroots-compositor` build job failed |
| DAK #8 | DuckOS native bring-up | Same native bring-up failure pattern |
| DAK #161, #167, #168 | Reaper contract tests | System contract suite failed in the tree-walk engine |
| DAK #165 | DuckOS CI | Mora shell `npm test` failed |
| DAK #177 | CodeQL / completeness | CodeQL C/C++ autobuild could not find a declared source file; native configure failed |
| DAK #179 | Bootable Stage 1 ISO | Framebuffer compositor assertion failed in blend-order/clip test |
| DAK #133 | Native desktop | Windows bundle assembly failed; Linux native desktop job succeeded |
| Reaper #366 | Reaper CI | `base_find_primitive` lookup raised KeyError in foundations 6–10 test |
| Reaper #368 | Reaper Native C / Reaper CI / typed conformance | Self-hosted parser failed at `selfhost/program_parser.rpr:173:36`; native CTest also failed |
| Reaper #370 | Reaper CI | Unit-test workflow failed |
| Reaper #316 | Reaper Native C | C compile failed on implicit declaration of `test_json_dispatch_and_thread_local_result` |
| VentuSample #183 | Repository Security Assurance | Assurance assertion failed and unified privacy status was reported as failed |

These failures have not been repaired in this scan. No failed workflow was rerun merely to obtain a green result; the source defects or contract failures need diagnosis and a code change first. A cancelled or skipped optional workflow is not counted as a successful required check.

## 7. Execution log

### Completed

- Paginated the current branch inventory across all five repositories.
- Paginated the current open-PR inventory across all five repositories.
- Classified open PRs by repository, Draft state and base branch.
- Built the live dependency edges for all 35 non-main-base PRs and compared child base SHAs to parent head SHAs.
- Read active main rulesets and exact required check contexts.
- Sampled high-impact PR workflow runs and retrieved logs for concrete failing jobs.
- Reviewed changed-file lists for the major DAK desktop/framebuffer and Reaper source-span overlap clusters.
- Merged DAK #208 by squash after reviewing its documentation diff and confirming the four required DAK contexts were successful.
- Verified DAK #208 is merged and verified the new DAK main SHA: `549da8190bc372c14606bdc691e9578e47f488d2`.

### Not complete

- Full file-by-file review of all 513 open PR patches.
- Per-PR CI inspection for every open PR.
- Final duplicate/supersession decisions for all overlap clusters.
- Complete provenance for DAK #174's parent branch.
- Fixes and passing reruns for the failures listed above.
- Integration and regression tests across all five repositories at their new pinned SHAs.
- Fork, tag and local stash inventory.
- Post-merge branch cleanup and final release verification.

## 8. Next execution order

1. Restack the ten stale edges listed above without changing source semantics. DAK #174's parent provenance is verified as merged PR #159.
2. Fix the shared root failures first: DAK native bring-up, DAK tree-walk contract suite, Reaper self-hosted parser/runtime and native C test target.
3. Reconcile the DAK desktop and framebuffer overlap clusters and the Reaper source-span cluster.
4. Repair OPlague required assurance contexts before selecting OPlague merge candidates.
5. Review all remaining main-based PRs in bounded groups, checking file overlap, security scope, diff size, requested reviews, required contexts and test evidence.
6. Merge one dependency chain at a time with squash only; after every parent merge, restack children and rerun checks.
7. Finish with cross-repository contract checks, native builds, regression tests and documented rollback proof.

**Completion status:** campaign is active; full consolidation is not complete. Do not delete source branches or publish an integration-complete release until all twelve acceptance criteria are evidenced.
