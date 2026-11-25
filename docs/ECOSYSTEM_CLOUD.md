# Ecosystem Cloud Integration

**Contract:** [`ivan-vhs.ecosystem-cloud.v1`](../federation/ecosystem-cloud.v1.json)  
**Status:** foundation; hosted deployment is not configured.

DuckOS owns the shared Supabase contract and local migration set. Peer repositories provide adapters; they do not become cloud-dependent applications.

## Operating model

- Local-only is the default. No login, DNS lookup, background upload or cloud request is required to boot or use local features.
- A user explicitly connects an account and enables sync before any remote effect.
- Local changes are committed to the local source of truth first. Network delivery uses a bounded retry queue and stable event IDs.
- Sync receipts record only the event ID, client-instance UUID and payload hash. They do not store event payloads.
- Conflicts are resolved by domain-specific code; the platform does not silently apply last-write-wins to user data.

## Database domains

| Table | Purpose | Client access |
|---|---|---|
| `ecosystem_organizations` | Organization metadata | RLS-scoped read/create/update |
| `ecosystem_memberships` | User-to-organization role | Own membership read only; role changes are privileged |
| `ecosystem_projects` | Non-secret repository/project metadata | RLS-scoped CRUD by role |
| `ecosystem_artifacts` | Hash/type/size/visibility metadata | RLS-scoped metadata |
| `ecosystem_sync_receipts` | Idempotency evidence | Own receipt read/insert |
| `ecosystem_audit_events` | Server-authored audit record | Own events read; no client insert |

The creator's owner membership is inserted by a trigger. A client cannot invite users, edit roles or create audit events. Those operations require a future reviewed Edge Function using least privilege.

## Private artifact storage

The `ecosystem-artifacts` bucket is private and capped at 100 MiB per object. Keys use:

```text
<organization UUID>/<project key>/<artifact UUID>
```

Storage row policies require an artifact metadata record, enforce its private/organization visibility, and scope every object key to its organization and project. Uploads require a pre-existing artifact metadata record owned by the caller; deletion is limited to that artifact's owner or an organization administrator. The application must never create public URLs and must never execute or auto-open stored content. Uploads occur only after an explicit publish/share action.

## Data exclusions

Never upload secrets, service-role keys, private source trees, raw serial numbers, raw hardware IDs, driver binaries, INF payloads, private signing material, plugin binaries or raw telemetry. Audio recordings, project sessions and local files remain local by default.

## Local verification

Install Docker and Supabase CLI 3.4.0, then run:

```sh
supabase start
supabase db reset
supabase test db
supabase stop
```

The GitHub workflow runs this local stack without linking a hosted project or requiring `SUPABASE_ACCESS_TOKEN`.

## Hosted deployment gate

The foundation is not a deployed service. Before hosted use, create a project in a user-selected Supabase organization, confirm any quoted cost, configure private secrets, review backup/retention settings and run the migrations against a staging project first. Production rollout requires a separate reviewed PR and an explicit deployment step.


## DuckOS adapter

`federation/ecosystem-cloud-adapter.v1.json` narrows DuckOS publication to user-selected preferences, application catalog metadata, project references and explicitly published release metadata. Boot, the kernel, Mora shell operation, local files and privileged state remain independent of Supabase.
