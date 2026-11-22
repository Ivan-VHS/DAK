# DuckOS

**DuckOS is an operating-system project bootstrap and ecosystem workspace.**

This integration attaches four specialist repositories as pinned Git submodules, installs the Beelzebul read-only security gate, and defines versioned project and interface contracts.

> **Current state: bootstrap, not a bootable OS.** Before this integration, DuckOS contained only a minimal README. This commit does not add a bootable kernel, bootloader, initramfs, compositor, package manager or installer.

## Integrated source projects

| Project | Responsibility | Location |
|---|---|---|
| Pytyliki | Processor inventory and bounded analysis | `ecosystem/Pytyliki` |
| Reaper | Language and developer tooling | `ecosystem/Reaper` |
| OPlague | Read-only device/driver package inspection | `ecosystem/OPlague` |
| VentuSample | Offline audio and DSP | `ecosystem/VentuSample` |
| Веельзевул / Beelzebul | 66-rule repository security gate | root-level policy, scanner, tests and workflow |

Each submodule is pinned to an immutable commit. Histories, licenses, builds and specialist ownership remain separate.

## Project map

- `ecosystem/registry.v1.json` — machine-readable project and interface registry.
- `security/beelzebul.v1.json` — Beelzebul security policy.
- `tools/beelzebul.py` — read-only repository scanner.
- `schemas/` — security and ecosystem schemas.
- `docs/ARCHITECTURE.md` — target OS architecture.
- `docs/ECOSYSTEM_INTEGRATION.md` — project boundaries and interfaces.
- `docs/IMPLEMENTATION_STATUS.md` — implemented vs. planned work.
- `docs/CHAT_BACKLOG.md` — requirements recovered from available project conversations.

## Validate

Requires Python 3.10+ and Git:

```sh
python3 tools/validate_ecosystem.py
python3 -m unittest discover -s tests -v
python3 tools/beelzebul.py --json
```

Beelzebul scans source files read-only. It is a development-time security gate, not a kernel monitor or runtime sandbox.

## Ownership boundaries

DuckOS owns the operating system. Reaper owns language tooling, Pytyliki owns processor analysis, OPlague owns driver inspection, and VentuSample owns sound/DSP. Cross-project communication uses explicit versioned interfaces, not an amalgamated binary.
