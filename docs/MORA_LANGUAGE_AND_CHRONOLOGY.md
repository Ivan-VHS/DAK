# Mora language, chronology and recovery contracts

**Maintainer:** Ivan-VHS  
**Scope:** DuckOS / Mora desktop shell  
**Status:** browser-layer implementation plus native service specifications

## Product model

The system starts with Russian as the default interface language and offers Ukrainian as an equal, persistent interface locale. The language selection is local to the user profile. It changes presentation and allowlisted command vocabulary; it does not rename package IDs, file paths, application IDs or user-authored content.

The far-future epoch is a separate chronology, not a replacement for the host clock. The example epoch is:

`86452654432564423644` years

It is represented as a decimal string at storage boundaries and a JavaScript `BigInt` for arithmetic and comparison. It must never be converted to `Number` for calculations. File timestamps, event audit times, expiry and cryptographic validation continue to use civil or monotonic clocks.

## The 15 principles and their implementation boundary

| # | Principle | Current implementation |
|---:|---|---|
| 1 | Language symmetry | RU default and persistent UK locale in Mora; Ukrainian command aliases for the local allowlist |
| 2 | Semantic identifiers | Stable ASCII IDs and locale-neutral file/package paths; UI aliases remain presentation metadata |
| 3 | Contextual translation | Reviewed UI dictionary and locale-aware dates; no arbitrary automatic translation of user content |
| 4 | Cyrillic typography | Segoe UI → Noto Sans → Arial → system fallback; required RU/UK glyph coverage recorded in theme tokens |
| 5 | Deep-time chronology | Bounded decimal parsing, BigInt epoch values, comparison and locale-aware display |
| 6 | Storage longevity | Versioned UTF-8 envelope, byte length, generation linkage and bounded payload validation |
| 7 | State branching | Parent-linked, CRC32-checked local Mora settings branches, retaining at most 12 entries |
| 8 | Safe updates | Service worker stages and verifies shell assets before activation; native OS A/B updater remains unimplemented |
| 9 | Quiet interface | Existing single Duck palette and restrained Mora desktop; command search appears only on request |
| 10 | Responsive motion | Reduced-motion handling and bounded command overlay transitions; animation never blocks input handling |
| 11 | Unified entry point | Ctrl+K local search for built-in apps; it does not execute shell commands |
| 12 | Predictable shortcuts | Ctrl+K search, Ctrl+, Control, Ctrl+W close top Mora window, Escape dismisses top layer |
| 13 | Least privilege | Sentinel remains deny-by-default preferences; actual process sandbox/capability enforcement requires native broker |
| 14 | Offline operation | Local locale, search, preferences and app cache; cache is Mora-scoped and keeps one prior generation |
| 15 | Diagnostics | Bounded localized diagnostic record contract; native kernel/event journal and process recovery remain future services |

## Storage envelope

The envelope schema is `duckos.storage-envelope.v1`. It stores a version, monotonically increasing generation, UTF-8 byte length, payload, digest algorithm and optional previous digest.

CRC32 is intentionally labelled as an accidental-corruption detector. It is not a digital signature, keyed MAC or proof of publisher identity. Authentic update bundles require a trusted signing key, signed manifest, algorithm agility, revocation policy and verification before staging.

The shell accepts and restores a legacy plain preference snapshot. The next save writes the snapshot in the envelope format. If an envelope fails validation, Restore must report it as damaged rather than silently accepting modified contents as a valid envelope.

## Branching

A branch contains an identifier, parent branch, revision, creation timestamp, validated state and CRC32 state digest. The browser profile stores the most recent twelve valid branches. This is a settings-history branch, not an immutable filesystem snapshot, volume snapshot or system rollback point.

## A/B update gate

The plan contract has the following required checks:

- Signed metadata and complete payload verification.
- Hardware and ABI compatibility.
- Sufficient capacity on the inactive slot.
- Health checks before selecting the target slot.
- Atomic boot-entry switch.
- Retention of the prior slot until a successful boot is accepted.

The current Mora action only constructs a plan with these gates marked as not verified. It does not fetch, write, install, reboot or change a boot entry.

## Native work still required

1. Versioned native message catalogs, locale-aware diagnostics, input-method integration and full font/glyph QA.
2. Kernel/user-space monotonic clock service and explicit simulation calendar adapters.
3. Signed immutable package and OS image metadata; secure boot integration; inactive-slot writer and health-tested boot rollback.
4. Filesystem snapshots or copy-on-write branches with crash-consistency tests.
5. Capability broker enforcing per-process access to files, network, microphone, camera, clipboard and devices.
6. Native system journal with bounded records, event correlation and recovery actions.

## Verification

Run the browser helper contracts with Node.js 18 or newer:

```sh
npm test
```

These tests verify JavaScript data contracts. They do not prove kernel isolation, filesystem durability, boot atomicity, native clock behavior or a bootable DuckOS image.
