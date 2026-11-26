# Documentation control

**Baseline date:** 2026-11-26  
**Applies to:** root README locales, technical documentation, schemas, release notes and repository cross-links.

This document defines the local publication gate. The canonical shared vocabulary and the broader README rules live in [Unified Documentation and Semantics Standard](UNIFIED_DOCUMENTATION_STANDARD.md).

## Publication gates

| Gate | Acceptance criteria |
|---|---|
| Identity | Exact repository/product name, one-line technical purpose, metadata table and current status. |
| Visual evidence | Diagram or screenshot is linked near the top and captioned with truthful version/environment context. |
| Onboarding | Contents, build prerequisites, reproducible commands and first checks are present and tested. |
| Architecture | Data flow, ownership, component boundaries and design trade-offs are explained. |
| Maturity | Specified, planned, partial, implemented and verified behavior are separated. |
| Compatibility | Platform, architecture, ABI/schema versions and breaking changes are explicit. |
| Limitations | Known integration, privilege, safety, performance and environment restrictions are visible. |
| Release history | Dates, tags, revisions and migration notes are sourced from actual Git/release artifacts. |
| Evidence | Capability claims cite source paths, tests, schemas or workflow evidence. |
| Performance | Metrics include hardware, workload, build, sample size, statistic and reproducible method. |
| Security | Untrusted inputs, privilege, secrets, device identifiers and vulnerability reporting boundaries are documented. |
| Licensing | Root license state, third-party notices and attribution are accurate. |
| Localization | EN/RU/UK/ZH-CN README variants share the same technical facts and section structure. |
| Navigation | Every docs page has a catalog entry, topic path and valid relative links. |
| Maintenance | Related docs, contracts, tests and CI are updated in the same pull request. |

## The 50-point README checklist

### Identity and first screen (1–10)
1. Begin with the exact project/repository name and a concise technical positioning statement.
2. Provide a compact specification table with version/stage, stability, license, supported platform and stack.
3. Record significant name, API and architecture transitions in the history section.
4. Put a version- and environment-captioned architecture diagram or real screenshot near the top.
5. State purpose, guarantees and responsibility boundaries within the opening paragraphs.
6. Quantify achievements only with reproducible evidence.
7. List related repositories and show their actual dependency/interface boundaries.
8. Add a contents list when the README is long or multi-subsystem.
9. Keep detailed release chronology out of the introduction.
10. Use a consistent technical tone and avoid unsupported marketing claims.

### Chronology and releases (11–20)
11. Group documented evolution into verifiable milestones.
12. Preserve material pauses, stack changes and rewrites when evidence exists.
13. Link releases to dated tags and revisions; do not invent missing milestones.
14. Distinguish stable, nightly, experimental and archived artifacts only when they exist.
15. Explain compatibility retained or replaced across versions.
16. State branch support lifecycle only when it is maintained.
17. Keep release chronology separate from API reference material.
18. Use explicit version tables for release and compatibility matrices.
19. Remove completed, cancelled or stale plans from current status summaries.
20. Connect architecture milestones to tags, specifications, migration scripts or CI evidence.

### Architecture and contracts (21–30)
21. Document cross-cutting engineering principles in a dedicated architecture section.
22. Explain why a design was selected, its trade-offs and rejected alternatives.
23. Prefer short, precise paragraphs and structured details.
24. Balance prose, tables, diagrams and self-contained code examples.
25. Keep protocol internals and long specifications under `docs/`, linked from README.
26. Separate normative contracts, current implementation and experiments.
27. Keep terminology and section structure synchronized across languages.
28. Use distinct names for modules, packages, services, processes and interfaces.
29. Make every section answer a defined engineering question.
30. Preserve both onboarding speed and sufficient architectural depth.

### Breaking changes and limitations (31–40)
31. Disclose known defects, architectural limits, performance bottlenecks and breaking changes.
32. Highlight changes that risk compatibility, permissions or user data.
33. Explain the reason for each significant compatibility break.
34. Separate repository limitations from OS, compiler and external dependency limits.
35. Compare alternatives only through measurable or architectural properties.
36. List unsupported platforms, CPU architectures and workloads.
37. Provide migration steps and safe workarounds where relevant.
38. Review and retire obsolete limitations when fixes are verified.
39. Keep detailed bug tracking in the issue tracker rather than README.
40. Remove ambiguity around concurrency, memory ownership, privilege and network effects.

### Sources, verification and maintenance (41–50)
41. Supply reproducible methodology, environment and artifacts for performance claims.
42. Separate API, architecture, examples, RFC/design docs and external standards.
43. Check internal and external links before releases.
44. Name standards, specifications and algorithms with exact versions.
45. State audits/certifications only with scope, date and source evidence.
46. Document issue reporting, contribution steps and security disclosure path.
47. Link to the actual LICENSE, CONTRIBUTING and code-of-conduct files when present; state clearly when absent.
48. Attribute external libraries, algorithms and third-party materials with their licenses.
49. Update README with CLI, configuration, API, contract or build changes in the same change.
50. Test all onboarding commands from a clean environment.

## Status vocabulary

- **Specified:** normative contract exists; runtime behavior is not claimed.
- **Planned:** accepted future work is not implemented.
- **Partial:** a bounded slice works; missing behavior is explicit.
- **Implemented:** described behavior exists in source and is connected to a workflow.
- **Verified:** the stated acceptance criteria passed in a named environment and revision.

For DAK, a Reaper reference-policy test does not verify native kernel enforcement. A host desktop or browser preview does not prove a kernel compositor, user session or process boundary.

## Review checklist

- [ ] Root README and all locale variants agree.
- [ ] Commands match current build files and scripts.
- [ ] Every local link resolves in the target branch.
- [ ] All documentation pages appear in the information architecture catalog.
- [ ] Status claims match the implementation ledger, tests and schemas.
- [ ] No version, release, metric, license or security claim is invented.
- [ ] Cross-repository contracts identify their owner and version.
- [ ] Third-party names and notices are preserved.

