# Supabase Ecosystem Integration v1

## Status

This repository owns the shared local Supabase schema and the canonical event, artifact and adapter contracts. The hosted deployment is **not configured**. The adapter manifest is `contract-only`; no DuckOS app or kernel component calls Supabase yet.

## Local verification

Requirements: Docker-compatible container runtime and Supabase CLI 3.4.0.

```sh
supabase start
supabase test db
supabase stop --no-backup
```

The GitHub Actions workflow runs the same commands against an isolated local stack. It does not link a project, read hosted secrets, deploy Edge Functions or mutate a hosted database.

## Shared data model

- Organizations and memberships define tenant boundaries.
- Devices are organization-scoped and user-owned. Optional fingerprints are SHA-256 pseudonyms, not anonymous identifiers.
- Sync events are append-only, bounded to 64 KiB and unique by organization/event ID. The database checks the actor and device owner against the authenticated session.
- Artifact metadata is immutable in v1. Private objects use the organization UUID as the first path segment and are bounded to 512 MiB.

## Client security rules

- Clients use only a Supabase URL and publishable key supplied at runtime.
- Never place a service-role key, database password, access token or signing secret in a repository or client.
- Authorization is based on organization membership rows, not user-editable user_metadata.
- No automatic network activity, background upload or telemetry.
- Source code, kernel memory, raw hardware IDs, serial numbers, driver packages and audio assets are excluded unless a project-specific manifest explicitly describes a safe, user-selected artifact.
- Local data remains canonical; offline operation must not depend on account login or network reachability.

## Adapter maturity

- `contract-only`: schema and data allow-list exist; no client implementation is claimed.
- `local-ci-verified`: adapter and local contract tests pass.
- `hosted-verified`: hosted Auth, RLS, Storage, sync, backup and restore tests have passed in a provisioned project.

Do not change adapter maturity without corresponding test and operational evidence.
