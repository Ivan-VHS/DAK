# Supabase Local Contract

Supabase is an optional data plane. DuckOS, Reaper and the companion tools remain usable without an account, hosted project or network connection.

## Requirements

- Docker-compatible container runtime
- Supabase CLI 3.4.0
- PostgreSQL 17 (pinned in `config.toml`)

## Local workflow

```sh
supabase start
supabase test db
supabase stop --no-backup
```

`supabase test db` runs the pgTAP suite in `tests/`. The suite covers tenant isolation, least-privilege grants, immutable sync events, idempotency, bounded schema IDs, artifact path validation and the private Storage bucket.

## Security invariants

- RLS is enabled on all public application tables.
- A device row uses a random registration UUID; no serial, raw PnP ID or hardware fingerprint is persisted.
- Events are append-only and authenticated against the event actor, organization and device owner.
- Artifact object keys are organization-scoped and restricted to canonical ASCII path segments.
- Storage is private; uploads are organization-role scoped and must be explicitly selected by the user.
- No client receives a service-role key or database credential.
- No hosted project is linked by this repository's CI workflow.
