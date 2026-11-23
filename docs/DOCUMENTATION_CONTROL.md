# Documentation control

This standard defines how DuckOS documentation is added and maintained. It does not define product behavior; implementation claims must be supported by this repository's source and tests.

| # | Rule | Acceptance |
|---:|---|---|
| 1 | Evidence | Implemented behavior links to the relevant source, tests or schemas. |
| 2 | Status | Separate implemented, partial, planned and not-applicable behavior. |
| 3 | Ownership | Every page has a clear topic owner and belongs to one primary cluster. |
| 4 | Navigation depth | Important pages remain reachable within three to four clicks from the root README. |
| 5 | No orphan pages | Every important page has at least two useful incoming links: the catalog and its topic hub or equivalent contextual pages. |
| 6 | Contextual links | Cross-link pages only where a real concept, workflow or dependency connects them. |
| 7 | Descriptive anchors | Link text names the destination; avoid vague labels and repeated keyword stuffing. |
| 8 | Breadcrumbs | Deep-level pages identify their parent hub and documentation home. |
| 9 | Canonical paths | Use direct relative paths within this repository and canonical HTTPS links across repositories. |
| 10 | Consistency | README, topic hubs, technical contracts, source and tests agree on terms, status and boundaries. |
| 11 | Maintenance | Update the index and hub in the same change as a new page; audit renamed, removed and broken links. |
| 12 | Accessibility | Keep links descriptive, same-tab by default and usable on small screens. |
| 13 | Measurement | Use navigation analytics only on an available published surface with privacy-respecting instrumentation; do not invent GitHub Markdown telemetry. |

See the [information architecture map](INFORMATION_ARCHITECTURE.md) for the current page graph and cross-repository boundaries.
