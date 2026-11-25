# Supabase Ecosystem Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a secure local-first Supabase foundation to DuckOS and versioned offline adapter contracts to the four companion repositories.

**Architecture:** DuckOS owns the shared PostgreSQL schema, private Storage bucket, common event/artifact JSON Schemas and local database test workflow. Reaper, Pytyliki, VentuSample and OPlague each add a domain-specific adapter manifest and validate it in their existing contract-validation path. Hosted deployment remains out of scope until a project is provisioned.

**Tech Stack:** Supabase CLI 3.4.0, PostgreSQL 17 local stack, SQL migrations, pgTAP, JSON Schema 2020-12, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-25-supabase-ecosystem-design.md`

## Global Constraints

- Local data remains authoritative; network access is disabled by default.
- Never add a service-role key, database password or hosted project token to source control.
- Do not deploy or mutate a hosted Supabase project.
- Use RLS on every public application table.
- Event and artifact writes are append-only in v1.
- All adapter manifests remain `contract-only` until real client and hosted verification exists.
- Preserve each repository's established language, CI and safety boundaries.

## Review Focus

- A user without a session cannot create an organization or access tenant rows.
- A member of organization A cannot read or write organization B data.
- An actor cannot insert events for a device owned by another user or organization.
- Duplicate event IDs cannot be replayed inside one organization.
- Malformed object paths, oversized payloads and unexpected adapter fields are rejected.

---

### Task 1: DuckOS canonical contracts and local schema

**Files:**
- Create: `supabase/config.toml`
- Create: `supabase/migrations/20261125184500_ecosystem_cloud_v1.sql`
- Create: `supabase/schemas/supabase-adapter.v1.schema.json`
- Create: `supabase/schemas/ecosystem-event.v1.schema.json`
- Create: `supabase/schemas/ecosystem-artifact.v1.schema.json`
- Create: `supabase/adapters/duckos.v1.json`

**Interfaces:**
- Produces: `public.create_organization_v1(text, text) -> uuid`
- Produces: `ivan-vhs.ecosystem-event.v1`
- Produces: `ivan-vhs.ecosystem-artifact.v1`
- Produces: `ivan-vhs.supabase-adapter.v1`

- [x] Add SQL migration with organizations, memberships, devices, sync events, artifact metadata, RLS, private authorization helpers and private Storage bucket.
- [x] Add JSON Schemas and a DuckOS control-plane adapter manifest.
- [x] Validate JSON and SQL syntax through repository CI and local Supabase CLI (local Supabase/pgTAP workflow passed; follow-up hardening revision is being re-run).

### Task 2: Database security regression suite

**Files:**
- Create: `supabase/tests/20261125_ecosystem_cloud_v1.test.sql`
- Create: `.github/workflows/supabase-contract.yml`

**Interfaces:**
- Consumes: Task 1 tables, policies and RPC.
- Produces: deterministic local pgTAP evidence on every relevant PR.

- [x] Add pgTAP assertions for schema shape, RLS flags, private bucket and policy presence.
- [x] Add two-tenant fixtures and prove isolation, valid event insertion, cross-tenant denial, idempotency and append-only behavior.
- [x] Run only local Supabase CLI 3.4.0 in CI; do not link or deploy a hosted project.

### Task 3: Reaper adapter contract

**Files:**
- Create: `federation/supabase-adapter.v1.json`
- Create: `federation/schemas/supabase-adapter.v1.schema.json`
- Modify: `tools/validate_project_contract.py`

- [x] Declare compiler/build summaries and diagnostic aggregates as opt-in data.
- [x] Exclude source text, local paths, credentials and tokens.
- [x] Extend the existing stdlib validator to reject invalid adapter fields and insecure defaults.

### Task 4: Pytyliki adapter contract

**Files:**
- Create: `federation/supabase-adapter.v1.json`
- Create: `federation/schemas/supabase-adapter.v1.schema.json`
- Modify: `tools/validate_project_contract.py`

- [x] Declare bounded profile and benchmark summaries as opt-in data.
- [x] Exclude raw hardware identifiers, serial numbers and unbounded traces.
- [x] Validate the adapter using the existing CI contract gate.

### Task 5: VentuSample adapter contract

**Files:**
- Create: `federation/supabase-adapter.v1.json`
- Create: `federation/schemas/supabase-adapter.v1.schema.json`
- Modify: `tools/validate_project_contract.py`

- [x] Declare sample-pack manifests, preset metadata and render summaries as opt-in data.
- [x] Keep audio payloads local unless a user explicitly selects an artifact for upload.
- [ ] Validate the adapter using the existing VentuSample contract gate.

### Task 6: OPlague adapter contract

**Files:**
- Create: `federation/supabase-adapter.v1.json`
- Create: `federation/schemas/supabase-adapter.v1.schema.json`
- Modify: `tools/validate_project_contract.py`

- [x] Declare read-only inspection summaries and pseudonymous device evidence as opt-in data.
- [x] Exclude raw PnP IDs, driver binaries, credentials and executable content; preserve no-install/no-driver-action boundaries.
- [x] Validate the adapter using the existing CI contract gate.

### Task 7: Documentation, verification and merge order

**Files:**
- Create: `docs/integrations/SUPABASE_ECOSYSTEM_V1.md`
- Modify: `README.md` only if the repository's current navigation requires a link.

- [x] Document local setup, security boundaries, status semantics and hosted rollout blockers.
- [ ] Run the full project test suites and inspect every changed file.
- [ ] Request review and merge PRs sequentially only after all required checks pass.
