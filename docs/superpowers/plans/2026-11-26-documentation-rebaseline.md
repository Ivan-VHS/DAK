# Repository Documentation Rebaseline — Implementation Plan

> **For agentic workers:** Apply this plan repository by repository. Keep the work on `docs/rebaseline-2026-11-26`; do not push directly to `main` or merge without review.

**Goal:** Rebuild the four-language repository entry points and make every documentation page discoverable, evidence-aligned and governed by one engineering documentation standard.

**Architecture:** Replace root README contents in place to preserve paths and Git history. Rebuild the documentation index and information-architecture catalog from each repository's actual Git tree, then align local documentation-control guidance and peer references with the canonical DAK standard.

**Tech Stack:** GitHub Markdown, Mermaid, JSON project contracts, GitHub Actions, CMake, Python/Node/Rust/C++/Reaper project-specific build systems.

**Spec:** User-provided 50 GitHub README engineering rules in the conversation.

## Global Constraints

- Keep the repository and OS name `DAK`; do not use the former product name in new prose.
- Keep all 4 existing README path names; replace their contents rather than deleting paths.
- Do not merge, force-push, alter licenses, or claim CI success without a current run.
- Source, tests, schemas, build files and release workflows outrank documentation and catalogues as evidence.
- Separate specified, planned, partial, implemented and verified capabilities.
- Preserve local-first/offline behavior, explicit trust boundaries, existing author attribution and third-party license notices.
- Do not invent releases, version numbers, support matrices, benchmark measurements, certification or contact addresses.
- DAK has no root LICENSE or SECURITY.md in the current tree; do not invent a license or imply distribution rights.
- Use Reaper as the DAK policy language in architecture documentation; describe existing C11/C++/Python/Node host tooling truthfully as implementation/tooling boundaries.
- Cross-project links must use the current DAK repository URL and versioned interface contracts.

## Review Focus

- README commands that do not match current CMake targets, scripts or entry points — verify against build manifests and workflows.
- Language-runtime and kernel-maturity claims that overstate native Reaper parity or DAK kernel enforcement — compare with project contracts and implementation ledger.
- Read-only/security boundaries for hardware, driver packages, native FFI and offline audio import — compare with source, schemas and tests.
- Relative links in four-language README files, documentation indexes, topic hubs and full catalogs — verify targets against the current tree.
- Version, license, release and performance claims without authoritative metadata — omit or mark explicitly undeclared.

---

## Repository sequence

### Task 1: Reaper
- Replace the four root README files with synchronized, localized, evidence-backed entry points.
- Rebuild `docs/README.md` and `docs/INFORMATION_ARCHITECTURE.md` from the current tree.
- Expand `docs/DOCUMENTATION_CONTROL.md`; correct the shared-standard pointer to DAK.
- Update `docs/UNIFIED_DOCUMENTATION_STANDARD.md` to point to DAK as the canonical policy.

### Task 2: Pytyliki
- Apply the same documentation structure while preserving C11/Win32/CLI boundaries.
- Do not repeat the old 0.8.0 product version unless the current project contract or release metadata verifies it.
- Rebuild the complete documentation catalog and local documentation-control gates.

### Task 3: OPlague
- Preserve read-only PnP and bounded package inspection; do not imply driver installation, quarantine or device mutation.
- Clarify Windows-only live inventory, offline analysis boundaries, unsigned SHA-256 checksum limits and draft-release behavior.
- Rebuild the full documentation catalog and local documentation-control gates.

### Task 4: VentuSample
- Preserve offline deterministic rendering; explicitly exclude real-time playback, DAW hosting and implicit device access.
- Keep pack v1/v2 compatibility, PCM16/WAV limits, optional Qt desktop and Reaper metadata-only consumption precise.
- Rebuild the full documentation catalog and local documentation-control gates.

### Task 5: DAK
- Keep Stage 1 boot evidence separate from a usable OS session and host-native desktop.
- Correct all newly maintained repository links and title language to DAK.
- Expand the canonical documentation standard with the 50 README/documentation rules.
- Add full index/catalog coverage; document missing root license/security policy without inventing either.
- Rebuild the four root README files and DAK implementation/architecture entry points.

## Verification and delivery

- Check every relative Markdown link in changed README/index/map/control files against the branch tree.
- Check every `docs/**/*.md` page has a catalog entry or a documented exclusion.
- Check language variants retain the same section structure and agree on version, status, license, platforms and safety boundaries.
- Compare README claims with `project-contract.json`, CMake/packaging manifests, tests and release workflows.
- Open one pull request per repository; leave merge decisions to the repository owner.
