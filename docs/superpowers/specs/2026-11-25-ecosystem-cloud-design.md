# Ecosystem Cloud Foundation v1 — Design

**Status:** approved by the implementation request; deployment remains pending a Supabase project.
**Owner:** Ivan-VHS/DAKOS
**Date:** 2026-11-25

## Intent

Introduce one optional Supabase-backed identity and synchronization plane for DAKOS, Reaper, Pytyliki, OPlague and VentuSample. The cloud is an additional collaboration and backup boundary; local operation remains complete when the network, Auth or cloud database is unavailable.

## Goals

- Define one versioned ecosystem contract and repository-specific adapter contracts.
- Provide organization membership, role-gated project metadata, artifact metadata, private object storage, idempotency receipts and an append-only audit record.
- Keep all remote effects explicit, opt-in, bounded and attributable to a user action.
- Verify migrations and tenant isolation against a local Supabase stack in CI.
- Preserve each repository's native language and build system.

## Non-goals

- No mandatory Supabase SDK in native applications.
- No cloud requirement for boot, compilation, device inspection, audio rendering or local projects.
- No upload of source code, secrets, raw device identifiers, driver packages, audio by default or unrestricted telemetry.
- No production project creation, hosted migration or deployment in this phase.
- No replacement of existing repository-to-repository file/ABI contracts.

## Architecture decisions

### Approaches considered

1. **One central optional cloud plane (selected).** DAKOS owns the shared contract and database migrations; each repository owns a small adapter declaration and maps only approved metadata. This avoids schema drift while preserving domain boundaries.
2. **One Supabase project per repository.** Stronger database isolation, but duplicates identity, membership and operations and adds cross-project synchronization complexity.
3. **Supabase SDK embedded in every application.** Rejected because it couples native C/C++/Reaper applications to a cloud vendor and encourages network assumptions in core workflows.

### Authority and data boundaries

- Supabase Auth is the identity authority only when a user explicitly connects an account. Local anonymous operation does not create a cloud identity.
- PostgreSQL RLS is the authorization boundary for all exposed application tables.
- An organization membership row is scoped to one authenticated user. The initial creator becomes owner through a database trigger. Member invitations and role changes are reserved for a future privileged Edge Function; clients cannot self-assign roles.
- Project records contain repository identity and non-secret descriptive metadata, not source trees.
- Artifact records contain hashes, size, content type, visibility and optional private object keys. Raw artifact content is not mirrored automatically.
- Sync receipts contain random client/event UUIDs and a payload hash, never the payload itself. Client instance IDs must be random and must not be derived from hardware identifiers.
- Audit events are append-only from the client perspective. Direct client inserts are denied.

## Repository-specific boundaries

| Repository | Permitted cloud metadata | Never upload automatically |
|---|---|---|
| DAKOS | Account preferences explicitly selected for sync, app catalog metadata, project references | Local files, credentials, boot secrets, kernel memory or logs |
| Reaper | Published package/contract metadata and user-selected documentation artifacts | Private source, tokens, local build outputs |
| Pytyliki | User-selected summary profiles and aggregate reports | Serial numbers, raw device IDs, full hardware inventory |
| OPlague | Sanitized report metadata and hashes | Driver binaries, INF payloads, signatures' private material, raw identifiers |
| VentuSample | Pack/preset manifests and user-published artifact metadata | Audio recordings, source sessions and plugin binaries by default |

## Security and privacy invariants

- Cloud network access is disabled until the user configures and enables it.
- No service-role key or secret appears in a client, repository, log, fixture or public artifact.
- Every exposed table has RLS enabled; grants are explicit and least-privilege.
- Organization isolation is enforced by database policy, not UI filtering.
- The storage bucket is private, size-limited and membership-gated. Public object URLs are not used.
- Object paths are organization-scoped and cannot be used to cross tenant boundaries.
- User-controlled metadata is bounded and validated. Audit metadata excludes secrets, raw tokens, personal data and unbounded payloads.
- Offline writes remain local until explicit synchronization; retries use stable idempotency keys.
- No automatic merge of conflicting user content. Conflicts require a domain-specific resolution policy.

## Migration and rollout

1. Add the canonical JSON contract, JSON Schema, SQL migrations and local pgTAP tests to DAKOS.
2. Add repository-local adapter manifests, data policies and validation tests to each peer project.
3. Run the local Supabase stack in CI with Supabase CLI 3.4.0; do not link CI to a hosted project.
4. Review and merge the DAKOS foundation PR first, then the four consumer PRs in dependency order.
5. Create a hosted Supabase project only after the user connects/chooses an organization and approves any costs. Hosted migrations remain a distinct deployment step.

## Acceptance

- Canonical contract and each adapter validate against the documented v1 shape.
- Local migrations create all tables, grants, RLS policies and the private storage bucket.
- pgTAP proves that two users in separate organizations cannot read each other's organizations, projects or private artifact metadata.
- CI runs local database reset and pgTAP with no cloud credential.
- Documentation clearly distinguishes schema-ready, locally tested and hosted-deployed states.
