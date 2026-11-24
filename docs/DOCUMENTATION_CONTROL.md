# Documentation control

**Scope:** DuckOS README, documentation entry points, visual assets, system contracts and cross-project references.

## Acceptance rules

| Gate | Requirement | Evidence |
|---|---|---|
| Evidence before claims | Implemented behavior points to source, schema, tests or CI | Source path and reproducible check |
| Explicit maturity | Separate implemented, partial, specified, planned and verified | Implementation status ledger |
| Product boundary | Mora browser shell is not described as native compositor/kernel | Architecture and shell code |
| Native boundary | Reaper reference contracts are not described as privileged OS execution | Reaper integration and native source evidence |
| Federation | Pinned repositories are not described as automatically built OS services | Submodule pins and federation tool |
| Release accuracy | Bundle, checksum and deployment plan are not described as bootable image/install | Deployment tooling and schemas |
| Catalog accuracy | Application concepts are not described as shipped native apps without packaging evidence | Catalog and application implementation |
| Visual provenance | Screenshots are real captures; authored drawings are labelled schematics | Asset source and caption |
| Adaptive hero | Light/dark SVGs share dimensions and accessible fallback exists | SVG pair and README picture block |
| Privacy and security | No private identifiers, credentials or local paths in public examples | Diff and fixture review |
| Navigation | Important documents are indexed and reachable | docs/README and topic hubs |
| Review hygiene | Links, Mermaid, commands and SVGs are checked | CI/local checks and git diff --check |

## Maturity vocabulary

- **Implemented:** behavior exists in the named source layer.
- **Partial:** only a defined subset exists.
- **Specified:** a contract or design is documented, but native implementation may not exist.
- **Planned:** future work with no current implementation.
- **Verified:** a named check passed on a stated revision and environment; this is separate from implementation maturity.

Always name the layer: browser shell, Reaper reference runtime, Python tooling, submodule integration or native platform code.

## Publication checklist

Update the root README and the owning contract document when behavior changes. Link source, schema and tests. Do not infer kernel readiness, driver availability, hardware privilege, application delivery, bootability or rollback from a successful browser test or contract check.
