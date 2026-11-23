# Documentation control

**Scope:** DuckOS repository documentation, Markdown entry points, machine-readable contracts, plans and cross-links.  
**Repository-wide execution plan:** [Markdown and Roadmap Execution Plan](MARKDOWN_AND_ROADMAP_EXECUTION_PLAN.md).

This policy governs information quality; it does not define product behavior. Implementation claims must be supported by current source, schemas, tests or reproducible CI evidence.

## Acceptance rules

| Rule | Requirement | Evidence of compliance |
|---|---|---|
| Evidence before claims | Distinguish source code, contract, prototype and proposal. | Link to source files, schemas, tests or CI runs. |
| Explicit maturity | Use `implemented`, `partial`, `specified`, `planned` and `verified` consistently. | State the layer at which a capability works. |
| Topic ownership | Every document belongs to one primary subject cluster. | Listed in the documentation map and relevant topic hub. |
| Navigation depth | Important pages stay within three to four clicks of the root README. | Root entry → documentation index → topic hub → detail page. |
| No orphan pages | Important pages have at least two contextual incoming links. | Root/index or cluster hub plus a relevant neighbouring specification. |
| Descriptive links | Link text identifies its destination and purpose. | No vague “here” anchors or keyword stuffing. |
| Canonical paths | Use relative links inside DuckOS and canonical HTTPS links across repositories. | No machine-specific paths or duplicate local copies. |
| Consistent terminology | README, topic hubs, schemas, code and tests agree on names and status. | Update dependent pages in the same change. |
| Lifecycle maintenance | Update indexes when adding, renaming or removing documents. | Broken-link and stale-reference review. |
| Accessibility | Keep heading order, link labels and navigation understandable on narrow screens and with assistive technology. | Keyboard and text-only review. |
| Honest measurement | Do not claim GitHub Markdown telemetry or invented usage analytics. | Only report measurements from an available, privacy-respecting published surface. |

## Maturity vocabulary

- **Implemented:** behavior exists in source at the stated layer.
- **Partial:** a bounded subset works; the complete system capability does not.
- **Specified:** contract or design exists, but runtime enforcement is absent.
- **Planned:** implementation is not present.
- **Verified:** repeatable tests or platform evidence demonstrate the stated behavior.

A working browser control does not prove a kernel service, native process boundary, driver, compositor or hardware integration.

## Change checklist

Before merging documentation changes:

1. Check the current source and tests; remove claims made obsolete by implementation changes.
2. Add the page to its topic hub and the central [information architecture](INFORMATION_ARCHITECTURE.md).
3. Add meaningful links from the root entry or the nearest relevant specification.
4. Run the Markdown quality diagnostic and repository validation workflows where applicable.
5. Preserve existing author, contributor, trademark and third-party license notices.

## Coordinated execution and plan control

The [Markdown and Roadmap Execution Plan](MARKDOWN_AND_ROADMAP_EXECUTION_PLAN.md) is the canonical repository-wide lifecycle for all 32 maintained Markdown files and the plans they describe. Apply it together with the [Unified Documentation Standard](UNIFIED_DOCUMENTATION_STANDARD.md) and the 20 [repository-wide implementation directives](REPOSITORY_EVOLUTION_DIRECTIVES.md).

Every plan must distinguish the current source-backed baseline from intended work, identify dependencies and ownership, define parallel-safe work packages, preserve serialized ordering for shared contracts and state, and provide acceptance criteria, verification, migration and recovery notes. A plan is not an implementation record.

Parallel work is permitted only for independent tasks with stable interfaces. Shared schemas, registries, migrations, build configuration, release branches and other shared state must be changed in dependency order. "Immediately", "at once" and similar wording never removes review, security, compatibility, test or rollback gates.

For changes that affect more than one document, update the canonical specification first, then its summaries and indexes in the same reviewed change. Do not copy a normative contract into several files. Unchanged pages remain governed by the standard; do not add repetitive boilerplate solely to create the appearance of a mass rewrite.

See the [DuckOS documentation index](README.md) and [project overview](clusters/project-overview.md) for current navigation.
