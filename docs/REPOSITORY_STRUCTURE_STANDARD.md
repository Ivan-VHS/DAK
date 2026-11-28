# Ivan-VHS Repository Structure Standard

**Document ID:** `IVAN-VHS-REPO-STRUCTURE-STD-001`  
**Version:** 1.0.0  
**Scope:** all repositories in the Ivan-VHS engineering and research ecosystem  
**Normative language:** MUST, SHOULD and MAY have their ordinary standards meaning.

## 1. Purpose and governing rule

This standard defines a common logical architecture for repository contents. It deliberately does **not** require every repository to have an identical physical directory tree.

A repository MUST reflect its actual domain, implementation language, build system, verification method and delivery model. The sample layout in a proposal is a taxonomy, not permission to add placeholder directories, duplicate canonical documents or introduce an unrelated runtime.

Each repository MUST maintain a local `docs/REPOSITORY_STRUCTURE_PROFILE.md` that maps this standard to its real canonical paths. A profile describes the current repository; it does not claim that optional or planned components already exist.

## 2. Authority and source of truth

When repository artifacts disagree, use the authority appropriate to the claim:

1. Source code defines behavior that is currently implemented.
2. Tests and CI results show which behavior was exercised, on which revision and under which limits.
3. Versioned schemas, protocol definitions, language specifications and ABI declarations define machine-readable or externally visible contracts.
4. Build files and release workflows define supported build and packaging procedures.
5. Documentation explains behavior, boundaries, status and reproducible workflows; it MUST agree with the higher-authority evidence.
6. Roadmaps, catalogues, mock-ups and diagrams explain intent or organization. They do not prove implementation.

Do not upgrade a status because a directory, schema, README section or registry entry exists. Record missing evidence as missing, partial or not verified.

## 3. Logical repository layers

| Logical layer | Expected responsibility | Physical layout |
|---|---|---|
| Project identity | Scope, usage, license, contributions and security contact | Root README, LICENSE, CONTRIBUTING and SECURITY files |
| Automation | Build, test, documentation, security and release gates | `.github/workflows/` |
| Documentation | Architecture, domain specifications, decisions, operations, status and roadmap | `docs/` with a maintained index |
| Implementation | Product/runtime/library source | Existing language- and product-specific source roots |
| Contracts | Schemas, public interfaces, ABI, manifests and compatibility rules | `schemas/`, `contracts/`, interface declarations and owned registries |
| Verification | Unit, integration, property, regression, conformance and fixture-based checks | `tests/`, `fixtures/`, `vectors/` or native equivalents |
| Reproducible tooling | Build helpers, validators, generators and maintenance automation | `scripts/`, `tools/` or build-system-native targets |
| Supporting material | Examples, test inputs, licensed media, diagrams and benchmark results | `examples/`, `fixtures/`, `assets/`, `benchmarks/` as applicable |
| Research provenance | Citation metadata, sources, assumptions, hypotheses and proof/evidence records | `CITATION.*`, research documentation and formal-proof sources where applicable |

The absence of an optional layer is not a defect when the local profile marks it as not applicable and explains why.

## 4. Documentation taxonomy

Documentation MUST have a navigable index and stable ownership. Repositories MAY use subdirectories or topic clusters according to domain and scale.

The mathematical-research taxonomy is:

- foundations: definitions, notation, axioms/postulates, assumptions and scope boundaries;
- theory: structures, operations, invariants and semantic rules;
- proofs: theorem statements, lemmas, proof dependencies and proof status;
- extensions: decompositions, completions and explicitly typed extensions;
- classical links: equivalences, prior results, attribution and novelty analysis;
- open problems: hypotheses, unresolved questions and counterexamples;
- applied models: mappings from the theory to bounded external domains;
- status and roadmap: maturity, limitations, milestones and next evidence.

Software/product repositories SHOULD organize documentation around their actual domains: architecture, language/runtime, API/ABI, security, UI, operations, integration, test evidence and release. They MUST NOT create empty mathematical categories merely to imitate a research repository.

Existing flat documentation libraries MAY remain flat when their index or topic-cluster pages provide equivalent navigation. A mass move is a separate migration and must update every relative link, generator, contract, CI filter and external reference in the same reviewed change.

## 5. Implementation layout

Source directories are language-specific. The generic names `src/core`, `src/algorithms` and `src/io` are examples, not mandatory names.

A project MUST preserve clear boundaries between:
- product/runtime implementation;
- language frontends, interpreters, compilers and toolchains;
- native interfaces and platform adapters;
- generated or vendored inputs;
- test-only helpers and production code.

A system repository MUST distinguish kernel/native system code from host-side management utilities. A language repository MUST distinguish canonical language artifacts from implementation conveniences. A media/audio repository MUST distinguish processing code from creative assets and pack metadata.

## 6. Formal proofs and verification

`docs/proofs/` contains human-readable mathematical statements and arguments. `formal/` contains source files for an actual formal verification system and its reproducible build/check entry point.

These layers are not interchangeable:
- unit or property tests are executable checks, not automatically mathematical proofs;
- finite exhaustive verification proves only the declared finite domain;
- numerical experiments and benchmarks are observations, not proofs;
- a theorem is not machine-checked until a named checker successfully processes the corresponding source at a recorded revision.

A proof-assistant directory is REQUIRED only when the repository has adopted a formal system. Otherwise the profile MUST say that formalization is not configured or not applicable. Never create placeholder proof files to make a tree look complete.

## 7. Tests, schemas and reproducibility

Tests SHOULD be classified by the project’s real test framework: unit, integration, property/fuzz, conformance, regression, platform and end-to-end. Keep stable input vectors and fixtures versioned where reproducibility requires them.

Schemas MUST be versioned and tested against representative valid and invalid examples. A schema documents a boundary; it does not show that every producer and consumer conforms to it.

Scripts and CI jobs MUST be deterministic where practical, bounded, least-privileged and safe to rerun. Validation MUST be read-only unless the task explicitly declares a mutation. CI MUST NOT install drivers, flash hardware, run untrusted payloads or access production credentials as an incidental structure check.

## 8. Citations, rights and assets

Research repositories SHOULD provide citation metadata (`CITATION.cff` and/or BibTeX) and maintain source attribution. Citation files are mandatory where the project publishes a citable mathematical or scientific work.

Assets and example data MUST have documented provenance and applicable license/usage terms. Fixtures MUST not silently include secrets, private user data or copyrighted material without permission.

## 9. Cross-repository changes

A change that moves or renames a file MUST be assessed against the entire dependency graph, including:
- import paths, build targets and package manifests;
- schemas, versioned contracts, ABI consumers and generated registries;
- test discovery, fixtures, CI path filters and release packaging;
- documentation links, localized READMEs and reference indexes;
- downstream repository evidence and compatibility declarations.

Keep one canonical source for each contract. Other repositories should link to or consume the canonical contract rather than copy divergent versions.

## 10. Repository-specific profiles

The current implementation maps the logical layers as follows:

| Repository | Implementation roots | Verification and contracts | Domain-specific documentation |
|---|---|---|---|
| Pytyliki | `src/`, `include/`, `cmake/` | `tests/`, `fixtures/`, `schemas/`, `contracts/` | C11 processor systems, native ABI and hardware-reference boundaries |
| Reaper | `reaper/`, `language/`, `src/`, `include/`, `stdlib/`, `frameworks/` | `tests/`, `schemas/`, versioned language registries | Language semantics, canonical IR, VM/compiler, DABI64 and tooling |
| OPlague | `oplague/`, `crates/`, `tools/` | `tests/`, `schemas/`, package/device fixtures | Read-only inspection, device/package evidence, security and federation |
| VentuSample | `src/`, `src/compat/` | `tests/`, `schemas/`, `examples/` | Offline audio, DSP, presets, pack exchange and asset provenance |
| DAK | `duckos/`, `kernel/`, `boot/`, `foundation/`, `desktop/` | `tests/`, `schemas/`, `catalogs/`, `manifests/` | Reaper-native system contracts, boot/kernel, native desktop and application boundaries |
| Kaskad | `src/kaskad_k3/` for supporting exact computation; mathematical canon in `docs/` | `tests/vectors/`, `schemas/`, `CITATION.*`; formal checker only when adopted | Vyunenko Theory, K3 foundations, proofs/evidence, extensions and applied mathematical models |

Each repository's local profile is authoritative for precise paths and exceptions:
- [Pytyliki](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/REPOSITORY_STRUCTURE_PROFILE.md)
- [Reaper](https://github.com/Ivan-VHS/Reaper/blob/main/docs/REPOSITORY_STRUCTURE_PROFILE.md)
- [OPlague](https://github.com/Ivan-VHS/OPlague/blob/main/docs/REPOSITORY_STRUCTURE_PROFILE.md)
- [VentuSample](https://github.com/Ivan-VHS/VentuSample/blob/main/docs/REPOSITORY_STRUCTURE_PROFILE.md)
- [DAK](https://github.com/Ivan-VHS/DAK/blob/main/docs/REPOSITORY_STRUCTURE_PROFILE.md)
- [Kaskad](https://github.com/Ivan-VHS/Kaskad/blob/main/docs/REPOSITORY_STRUCTURE_PROFILE.md)

## 11. Acceptance checklist

A repository adopts this standard when:

- [ ] its local structure profile maps the real source, docs, contracts, tests, automation and assets;
- [ ] required root metadata and documentation navigation are present;
- [ ] the build and test layout matches the actual toolchain;
- [ ] optional layers such as formal proofs and benchmarks are accurately marked;
- [ ] a CI check validates the mandatory repository paths without mutating project state;
- [ ] all path migrations update references and downstream contracts in the same PR;
- [ ] claims of implementation and verification are tied to evidence.

The structure validator checks only the existence of declared paths. It does not replace compilation, unit tests, schema validation, security review or mathematical proof.
