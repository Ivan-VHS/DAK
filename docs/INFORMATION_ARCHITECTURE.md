# DuckOS documentation information architecture

[Project README](../README.md) · [Documentation index](README.md)

This is the canonical navigation map for DuckOS. At present the repository contains a single root README and no separately published technical specification set. The map records that state rather than inventing architecture or implementation claims.

## Current page hierarchy

- **Entry point:** [README.md](../README.md) — the only existing project document at the time this map was created.
- **Documentation index:** [README.md](README.md) — the entry point for this documentation folder.
- **Topic hub:** [Project overview](clusters/project-overview.md) — status and the route into currently available project material.
- **Policy:** [Documentation control](DOCUMENTATION_CONTROL.md) — rules for new pages and cross-links.

## Cross-repository boundaries

These are separate repositories. The links below provide organizational context only; they do not imply shared source code, ABI compatibility, runtime dependencies or feature parity.

- [Pytyliki documentation map](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/INFORMATION_ARCHITECTURE.md)
- [Reaper documentation map](https://github.com/Ivan-VHS/Reaper/blob/main/docs/INFORMATION_ARCHITECTURE.md)
- [OPlague documentation map](https://github.com/Ivan-VHS/OPlague/blob/main/docs/INFORMATION_ARCHITECTURE.md)
- [VentuSample documentation map](https://github.com/Ivan-VHS/VentuSample/blob/main/docs/INFORMATION_ARCHITECTURE.md)

## Rules for future growth

Every new document must belong to a named topic cluster, appear in this map and the documentation index, link back to its parent hub, and have at least two meaningful incoming links. Keep important pages within three to four clicks of the root README. Use descriptive anchors, direct relative links within this repository and canonical HTTPS links across repositories. Update existing pages when a new contract changes their meaning or dependencies.
