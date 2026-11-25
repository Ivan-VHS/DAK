# Supabase Ecosystem Foundation v1

**Status:** proposed implementation baseline  
**Date:** 2026-11-25  
**Owner:** DuckOS ecosystem control plane

## Intent

Establish one optional Supabase data plane for the Ivan-VHS ecosystem without making the cloud a runtime dependency of DuckOS, Reaper, Pytyliki, VentuSample or OPlague. Each project keeps its native domain model and local data as the authority. Cloud exchange is explicit, versioned, auditable and safe to leave disabled.

## Goals

- Provide a single, versioned PostgreSQL model for organizations, memberships, pseudonymous devices, append-only sync events and artifact metadata.
- Enforce tenant isolation in PostgreSQL with Row Level Security (RLS), least-privilege grants and immutable event/artifact records.
- Use an authenticated RPC to create an organization and its first owner atomically.
- Provide a private artifact bucket with organization-scoped access.
- Define common event and artifact envelopes and project-specific adapter contracts.
- Run migrations and pgTAP security tests against a local Supabase stack in GitHub Actions.
- Keep all hosted credentials outside source control and keep cloud features disabled by default.

## Non-goals

- Creating or billing a hosted Supabase project.
- Deploying Edge Functions, Auth providers, secrets or production migrations.
- Moving local application data or user audio/source/driver binaries into the cloud automatically.
- Turning Supabase into a kernel service, compiler dependency, driver runtime or required application service.
- Claiming hosted connectivity, real-world RLS enforcement or production readiness before a hosted environment is configured and tested.

## Constraints

- DuckOS native implementation and examples remain Reaper-first; this foundation is a SQL/data contract, not a Python DuckOS runtime.
- Local-first/offline-first remains the default; no background uploads or telemetry.
- No service-role key or database password may appear in clients, manifests, workflows or repository files.
- Every table exposed through the Data API must have RLS enabled and explicit grants/policies.
- Client-provided actor IDs are never trusted; the database derives the actor from auth.uid().
- Sync events are append-only and idempotent per organization through a unique event identifier.
- Device identifiers are pseudonymous and must not contain serial numbers or raw Plug-and-Play identifiers.
- Artifact objects are private and use organization-scoped object paths.
- A schema, interface or adapter is not marked implemented until tests and runtime evidence support the claim.

## Approaches considered

1. **One central data plane with project-owned adapters — selected.** DuckOS owns the shared data plane and canonical envelopes; each repository defines its own bounded adapter contract. This avoids schema drift while preserving domain ownership and offline operation.
2. **One Supabase project per repository — rejected for v1.** It fragments identity, policy and observability, creates duplicated migrations and complicates cross-project organization/device relationships.
3. **Direct Supabase SDK calls from every application — rejected for v1.** It spreads credentials and network concerns into unrelated runtime layers, couples offline tools to hosted SDKs and makes security boundaries harder to audit.

## Architecture

DuckOS owns the canonical SQL migrations, local Supabase configuration, pgTAP tests and adapter/event/artifact schemas. Reaper, Pytyliki, VentuSample and OPlague publish project-specific adapter manifests that declare what data may be exported and what is excluded. Adapters remain contract-only and offline-only until native clients are implemented and verified.

The v1 database contains:

- `organizations` and `organization_members` for tenant membership;
- `devices` for user-owned, pseudonymous device registrations;
- `sync_events` for append-only, idempotent event ingestion;
- `artifacts` for immutable, bounded artifact metadata;
- private Storage bucket `ecosystem-artifacts` with organization-folder policies.

## Security model

- RLS is enabled on all public data tables.
- Private SECURITY DEFINER helpers use an empty search_path, fixed SQL, and execute grants only for authenticated users.
- `create_organization_v1` validates input and atomically creates the organization and owner membership.
- Organizations and memberships are not directly writable by client roles.
- Events can only be inserted by their authenticated actor from a device they own in the same organization; no update/delete grant is provided.
- Artifacts are insert-only for owner/admin/editor roles; private Storage reads and uploads are organization-scoped.
- No user_metadata claim is used for authorization; authorization comes from membership rows.
- No service-role key is exposed to browser, desktop or native clients.

## Data and sync semantics

- Local application state remains authoritative.
- Cloud records are optional replicas, not a prerequisite for opening or using an app.
- Events use stable schema IDs and positive schema versions; duplicate event IDs within one organization are rejected.
- Server recorded time is authoritative for ingestion ordering; source occurred_at is retained as untrusted event metadata.
- Event payloads are bounded to 64 KiB and must be JSON objects.
- Artifact uploads are explicit, bounded to 512 MiB in v1, and identified by SHA-256 metadata.
- Conflict resolution for replicated state is not silently inferred from arrival order. Domain-specific merge rules must be versioned before state sync is enabled.

## Rollout and evidence

1. Land the DuckOS local schema, migrations, pgTAP tests and local-only CI gate.
2. Land one adapter-contract PR per repository, with data allow-lists and explicit exclusions.
3. Run all five repository CI pipelines and the DuckOS local Supabase database suite.
4. Merge only green, reviewed PRs in dependency order.
5. Configure a hosted project separately; then run migrations and end-to-end RLS, Storage, backup/restore and observability tests before setting any adapter to hosted-verified.

## Acceptance criteria

- The local schema can be started and tested without a Supabase account or project ID.
- pgTAP proves RLS is enabled, tenant rows are isolated, cross-tenant writes are denied, duplicate events are rejected and immutable tables cannot be updated.
- The adapter schema rejects unknown fields, enabled-by-default networking and client service-role access.
- Each repository declares its data allow-list and sensitive exclusions.
- All workflows are read-only with respect to hosted Supabase; none contains a project token or performs hosted deployment.
