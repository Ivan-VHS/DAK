# Psychoporter 666 — Documentation Style v1.1

> **Editorial revision · 2026-11-28:** New shared documentation style guide. It governs presentation and editorial voice only; it does not replace project contracts, source evidence, licenses or contributor attribution.

**Document ID:** IVAN-VHS-PSYCHOPORTER-DOCS-001  
**Version:** 1.1  
**Scope:** README files, technical documentation, indexes, diagrams, release notes and research records across the Ivan-VHS repository ecosystem  
**Language baseline:** English, Ukrainian, Russian and Simplified Chinese where a localized entry point exists

## 1. Purpose and character

Psychoporter 666 is the shared editorial and visual language for a multi-project engineering ecosystem. Its purpose is to make dense systems work readable, memorable and verifiable without flattening the distinct identity of each repository.

The style has three complementary modes:

| Mode | Editorial role | What it contributes |
|---|---|---|
| **The Architect — Jade Order** | Structure, precision and accountability | Clear hierarchy, exact terminology, definitions, contracts, evidence and explicit boundaries |
| **The Pathfinder — Ruin Atlas** | Curiosity, investigation and discovery | Maps, questions, alternatives, open questions, exploratory notes, cross-links and controlled visual energy |
| **The Synthesis — Psychoporter** | A disciplined union of both | A complete narrative from purpose to implementation, verification, limitations and next steps |

Kai and Ging Friks are used here as fictional design archetypes drawn from the supplied visual concept. They are not claims about a real person's identity, mental state, diagnosis or clinical profile. Persona references may shape the rhythm of a page; they must never replace engineering evidence.

**Editorial principle:** structure without rigidity; exploration without noise; confidence without unsupported claims.

## 2. Voice and writing rules

1. Begin with a direct statement of what the project or document actually covers.
2. Write with calm authority. Prefer strong verbs and concrete nouns to inflated adjectives.
3. Let the Architect voice govern definitions, interfaces, algorithms, safety boundaries and acceptance criteria.
4. Let the Pathfinder voice govern research routes, alternatives, open questions and explanatory navigation.
5. Use the Synthesis voice for the overall flow: why it exists → how it works → how to verify it → what it does not claim.
6. Keep metaphors in headings, short epigraphs or visual captions. Technical meaning must remain explicit in ordinary prose.
7. Do not invent quotations or attribute newly written lines to real people.
8. Do not use threats, intimidation or hostile language as a substitute for a strong visual identity.
9. Distinguish facts, measurements, interpretations, recommendations, hypotheses and planned work.
10. Use the shortest explanation that preserves the conditions, exceptions and evidence a reader needs.

## 3. Visual grammar

### 3.1 Shared visual motifs

The supplied Jade Realm / Dark Continent concept contributes four motifs:

- **Obsidian field:** quiet dark surfaces and clear contrast.
- **Jade signal:** structure, stable interfaces and verified paths.
- **Amber clue:** navigation, caution, open questions and research context.
- **Magenta / violet anomaly:** exceptional or exploratory material, used sparingly.

The reference palette is obsidian #090B0F, jade #34D399, amber #F59E0B, magenta #FF0055 and violet #BD00FF. These are documentation accents, not a command to recolor each product.

### 3.2 Preserve product identity

Each repository keeps its established product palette, logos, icons, screenshots and terminology. The shared standard governs composition and meaning, not identical branding.

| Repository | Editorial lens | Visual direction |
|---|---|---|
| **Pytyliki** | Instrument panel and evidence ledger | Graphite, jade for observed capabilities, amber for interpretation and constraints |
| **Reaper** | Language codex and compiler atlas | Precise grids, restrained technical accents, readable code and syntax diagrams |
| **OPlague** | Forensic evidence atlas | Dark steel, measured status accents, explicit provenance and trust boundaries |
| **VentuSample** | Audio laboratory and production notebook | Studio-like hierarchy, waveform / spectrum motifs and restrained signal accents |
| **DAK** | System atlas and command surface | Preserve the established black, white and yellow identity; status colors remain semantic |
| **Kaskad** | Mathematical manuscript and positional number atlas | Obsidian, jade and amber accents; equations, indices, zero positions and proof structure |

A repository may adopt a different accent after an explicit design decision. Do not silently mutate shared UI tokens while styling documentation.

### 3.3 Page composition

- Put project identity, one factual sentence, language navigation and the most useful links near the top.
- Use one principal visual asset per entry page where a suitable, verified asset already exists.
- Use a compact table of contents for long documents.
- Separate major sections with whitespace and meaningful headings rather than ornamental separators everywhere.
- Use tables for comparisons and structured facts, not for ordinary paragraphs.
- Use Mermaid for editable architecture and process diagrams where GitHub supports the diagram type.
- Use <code>&lt;details&gt;</code> for optional proofs, extended examples, migration notes or secondary reasoning.
- Keep badges limited to real workflows, real releases and existing license files. A badge is not a substitute for evidence.
- Every image needs useful alternative text. Label screenshots as screenshots and diagrams as diagrams.

## 4. GitHub Markdown and asset constraints

GitHub README rendering is not a general-purpose web application. The supplied HTML concept includes elements that do not belong in a repository README.

**Allowed direction:** native Markdown, simple supported HTML such as <code>&lt;div align="center"&gt;</code>, <code>&lt;picture&gt;</code>, accessible self-contained SVGs, Mermaid, tables, blockquotes and collapsible sections.

**Do not embed:** JavaScript, Tailwind runtime scripts, remote CSS frameworks, Google Fonts imports, external font CDNs, arbitrary inline CSS, interactive iframes or external code execution in a README.

SVG and raster assets should be stored in the repository. SVG files must be self-contained and accessible; do not rely on remote images, fonts or scripts. Prefer light/dark variants through <code>&lt;picture&gt;</code> when both approved assets exist. Do not replace a real screenshot with a conceptual rendering or a conceptual diagram with a fake screenshot.

Avoid animation that makes reading difficult. A single short decorative accent is enough; all essential information must remain available in static form and with reduced motion.

## 5. Standard document anatomy

Use only the sections needed for the document's purpose, but preserve this information flow where relevant:

1. **Identity:** title, short purpose, owner or responsible project, version and review date where known.
2. **Scope:** what the document covers and what it explicitly does not cover.
3. **Model:** definitions, inputs, outputs, invariants, data flow or mathematical objects.
4. **Implementation:** current source paths, interfaces, configuration and real workflows.
5. **Verification:** exact tests, build commands, CI workflows, supported platforms and revision where available.
6. **Limitations:** unsupported cases, partial behavior, failure modes and dependencies.
7. **Connections:** related documents, schemas, contracts and neighboring repositories.
8. **Governance:** contribution, security, licensing, attribution and change history where applicable.

Do not add empty headings merely to imitate a template. A short focused specification is better than a long generic document.

## 6. Evidence and implementation maturity

The style must never make an implementation claim stronger than its evidence.

Use the shared status dimensions distinctly:

- **Maturity:** not_assessed, specified, planned, partial, implemented, verified, deprecated, unsupported or not_applicable.
- **Runtime state:** describes what a running component is doing now.
- **Verification result:** not_run, passed, failed, blocked, skipped or not_applicable.
- **Integration policy:** required, optional, opt_in, disabled or not_applicable.

A roadmap, catalogue, screenshot, design mock-up or contract does not prove that a capability is implemented. Performance claims require workload, hardware, OS, build mode, measurement method and provenance. Unknown values remain unknown; do not fill them with attractive guesses.

The authority order is: source code and executable behavior; tests and CI evidence; versioned schemas, protocols and ABI definitions; build and release configuration; explanatory documentation; then diagrams and catalogues.

## 7. Domain-specific precision

### Systems and software engineering

Document ownership, inputs, outputs, resource limits, errors, side effects, permissions, platform support and compatibility. Distinguish host applications from kernel components, reference contracts from native enforcement, inspection from modification, and offline processing from real-time execution.

### Mathematical and scientific writing

Keep definitions, axioms, lemmas, theorems, proofs, conjectures and research plans visibly distinct. State assumptions and domains. Preserve notation exactly where its position carries meaning.

For Kaskad / K3 in particular, a cascade is positional: radix B=1000, coefficient indices, separators and zero positions are semantic data. Never remove, move or normalize a zero or separator as a cosmetic edit. Demonstrate equivalence before changing a canonical expression.

### Audio and measurement work

Name units, sample formats, channel count, sample rate, numeric range and offline/real-time status. Mark synthetic or illustrative data. Keep source assets, licenses and provenance visible.

## 8. Copyright, authorship and third-party materials

This style guide grants no license and changes no ownership.

- Keep every existing LICENSE, NOTICE, copyright line, trademark notice, author credit, citation and upstream attribution intact.
- Do not replace an Apache-2.0, MIT or other project license with a common ecosystem license.
- Do not imply that federation, dependency, submodule pinning or integration transfers ownership or grants additional rights.
- Preserve source attribution for adapted text, diagrams, examples, screenshots, datasets and code.
- Do not add an "All rights reserved" statement unless the rights holder has explicitly chosen it.
- Do not infer a repository-wide license where no root license has been published. DAK currently has no root LICENSE; this guide does not create one.
- When modifying a file governed by Apache-2.0, include a visible change notice in that file as required by the license. Keep the original notices and the full license text.
- If an asset's author, source or reuse permission is unknown, do not silently present it as original or approved for redistribution.

An editorial refresh is not a relicense, assignment, waiver or authorship transfer.

## 9. Localization

Where localized README files exist, keep their purpose, scope, maturity, commands, limitations, navigation and legal information aligned. Translate prose, not canonical identifiers, CLI flags, API names, schema keys, file paths or code symbols. Preserve mathematical notation and source references. When a language variant is incomplete, state that clearly rather than implying full translation parity.

## 10. Review checklist

- [ ] The title and opening sentence say what the document actually covers.
- [ ] The Architect, Pathfinder and Synthesis modes are balanced; metaphor never replaces meaning.
- [ ] The repository's existing product identity and palette remain intact.
- [ ] Markdown, HTML, SVG and Mermaid render on GitHub without remote runtime dependencies.
- [ ] Every screenshot, illustration, metric and status claim is labelled accurately.
- [ ] Commands and file links match the current repository.
- [ ] Implemented, partial, specified and planned behavior are separated.
- [ ] Mathematical symbols, indices, separators and zero positions are preserved.
- [ ] Localized entry points agree on facts and commands.
- [ ] Copyright, license, NOTICE, contributor and upstream attribution statements are preserved.
- [ ] Modified Apache-2.0 files carry a visible modification notice.
- [ ] No new license grant, ownership claim or certification is implied.

**Closing rule:** make the page striking at first glance, navigable on the second, and technically trustworthy after a full read.
