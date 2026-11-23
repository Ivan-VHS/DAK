# Unify manual transfer format v1

**Interface ID:** `unify.transfer.v1`  
**Transport:** user-selected JSON file  
**Status:** `partial` in the Mora browser prototype; no live device transport is claimed

Unify v1 is a manual export/import package for moving selected browser tabs, game clips and a small settings snapshot between browser profiles. A user must explicitly export the file, move it to the target device and import it there.

## 1. Schema

The canonical schema is [`schemas/unify.transfer.v1.schema.json`](../schemas/unify.transfer.v1.schema.json).

Top-level fields:

| Field | Requirement | Meaning |
|---|---|---|
| `schema` | Required; exact value `unify.transfer.v1` | Format identifier |
| `createdAt` | Required ISO date-time | Export time |
| `tabs` | Required array, up to 1,000 entries | HTTP(S) tab records |
| `clips` | Required array, up to 100 entries | Embedded user-selected clips |
| `settings` | Optional object | Selected local UI preferences |

A clip stores a name, MIME type and base64 data URL. The prototype limits each clip to 12 MiB and each imported JSON package to 20 MiB. Oversized clips are skipped during multi-clip export or rejected during import. Tabs are data records; importing them does not automatically navigate to them.

## 2. Trust and validation

Treat every transfer file as untrusted input:

- Accept only the exact schema identifier and HTTP(S) tab URLs.
- Enforce package, entry-count and per-clip size bounds before storing data.
- Do not execute script, launch applications or follow URLs during import.
- Keep the import action user-initiated and show the result.
- Preserve receiver-side permissions; importing a package does not grant device-pairing or background access.

## 3. Current limitations

This contract currently supports a manual file hand-off. It does not define authenticated device pairing, encryption in transit, live clipboard synchronization, background file transfer, phone notification forwarding, conflict-free settings merge or lost-device discovery.

The browser prototype stores imported data in the local browser profile. A future native Unify service must define authenticated peer identity, transport security, replay/duplicate handling, cancellation, retention and revocation before claiming live cross-device synchronization.

## 4. Related material

- [Mora preinstalled application suite](PREINSTALLED_APPLICATIONS.md)
- [Mora browser prototype](../prototype/mora-home.html)
- [Unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md)
