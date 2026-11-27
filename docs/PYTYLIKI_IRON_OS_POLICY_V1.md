# DuckOS policy contract for Pytyliki Iron Syntax v1

**Canonical syntax owner:** Pytyliki  
**AST schema:** `pytyliki.iron-syntax-ast.v1`  
**Version:** `1.0.0`

DuckOS treats an Iron parse result as untrusted, read-only source metadata. The policy fixture in `duckos/security/iron_syntax_policy.rpr` accepts only the expected schema/version/owner, a record count from 1 through 4,096, and an AST with `execution_performed == false`.

The separate effect policy is default-deny: only `metadata_read` is permitted. MMIO, DMA, driver installation, firmware writes, privilege changes, device writes and process-control actions are not granted by an Iron syntax record. A successful parse or metadata admission is not an OS capability.

## Integration boundary

This PR adds a Reaper policy contract fixture. It does **not** yet connect this predicate to the live kernel capability broker or system-call admission path. The existing Reaper subprocess boundary remains authoritative: no shell interpolation, bounded execution, bounded output and explicit admission by the OS service that owns the requested capability.

The DAK Reaper contract workflow's recursive `.rpr` syntax validation discovers this file. Runtime/kernel wiring requires a separate change with direct capability-broker integration tests and must preserve default-deny behavior.
