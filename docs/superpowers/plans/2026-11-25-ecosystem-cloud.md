# Ecosystem Cloud Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a local-first optional Supabase platform contract and safe per-repository adapters for the five Ivan-VHS projects.

**Architecture:** DuckOS owns the versioned ecosystem contract, JSON Schema, Supabase migrations and local database CI. Reaper, Pytyliki, OPlague and VentuSample each own a small adapter manifest that references the same contract and restricts data to approved metadata. Network use remains disabled until explicitly configured.

**Tech Stack:** Supabase CLI 3.4.0, PostgreSQL 17, SQL migrations, pgTAP, JSON Schema 2020-12, Node.js built-in test runner in DuckOS, Python unittest for repository metadata validators.

**Spec:** `docs/superpowers/specs/2026-11-25-ecosystem-cloud-design.md`

## Global Constraints

- Keep DuckOS kernel and desktop behavior local-first; cloud must never be required for boot or core OS operation.
- Use Reaper for DuckOS code and examples; do not add Python implementations or Python test runners to DuckOS.
- Do not add cloud SDK dependencies to native C11/C17/C++20 application cores.
- Use Supabase CLI 3.4.0 in local-only CI; no hosted project link, access token or secrets.
- Do not upload source, secrets, raw device identifiers, driver packages or audio files by default.
- Use private storage, 100 MiB maximum object size, RLS on every exposed table, least-privilege grants and idempotency keys.
- Do not modify existing open PRs or merge unrelated work.

## Review Focus

- Cross-tenant reads: a user must see no organization, project or private artifact belonging to another organization.
- Forged membership: a client must not grant itself admin/owner or invite another user.
- Storage traversal: an object path for another organization must be denied.
- Offline operation: absence of credentials or network must not block local product flows.
- Replay: repeated client/event UUID pairs must not create duplicate sync receipts.

---

### Task 1: Canonical ecosystem cloud contract

**Files:**
- Create: `federation/ecosystem-cloud.v1.json`
- Create: `schemas/ivan-vhs.ecosystem-cloud.v1.schema.json`
- Create: `docs/ECOSYSTEM_CLOUD.md`
- Create: `tests/mora-ecosystem-cloud-contract.test.mjs`
- Modify: `.github/workflows/completeness-check.yml` to run the Node contract test.

**Interfaces:**
- Produces schema ID `ivan-vhs.ecosystem-cloud.v1`, contract version `1`, and the five repository data-boundary declarations.

- [ ] Add a Node test asserting schema ID/version, local-only default, five unique repository IDs and forbidden-data policies.
- [ ] Run the new test against the contract fixture and confirm it fails before the contract is added.
- [ ] Add the JSON contract and JSON Schema; keep the schema closed to unknown top-level fields.
- [ ] Run `npm test` and the existing DuckOS completeness checks.

### Task 2: Local Supabase database foundation

**Files:**
- Create: `supabase/config.toml`
- Create: `supabase/migrations/20261125000000_ecosystem_cloud_foundation.sql`
- Create: `supabase/tests/database/001_ecosystem_cloud_rls.test.sql`
- Create: `.github/workflows/supabase-cloud-contract.yml`

**Interfaces:**
- Tables: `ecosystem_organizations`, `ecosystem_memberships`, `ecosystem_projects`, `ecosystem_artifacts`, `ecosystem_sync_receipts`, `ecosystem_audit_events`.
- Bucket: private `ecosystem-artifacts`; object key format `<organization UUID>/<project key>/<artifact UUID>`.

- [ ] Add pgTAP assertions for RLS enabled on every table and tenant isolation across two users.
- [ ] Run the pgTAP suite against a local Supabase stack and confirm it fails before the migration exists.
- [ ] Add SQL migration with creator-as-owner trigger, explicit grants, RLS policies, private storage policies and bounded metadata.
- [ ] Run `supabase start`, `supabase db reset` and `supabase test db` using CLI 3.4.0.

### Task 3: Reaper cloud adapter contract

**Files:**
- Create: `federation/ecosystem-cloud-adapter.v1.json`
- Create: `docs/ECOSYSTEM_CLOUD.md`
- Create: `tests/test_ecosystem_cloud_contract.py`

**Interfaces:**
- Consumes `ivan-vhs.ecosystem-cloud.v1`; project key `reaper`; local source and build outputs remain local.

- [ ] Add failing assertions for schema, version, local-only default and prohibited data classes.
- [ ] Add adapter manifest and documentation.
- [ ] Run `python -m unittest discover -s tests -p "test_ecosystem_cloud_contract.py" -v`.

### Task 4: Pytyliki cloud adapter contract

**Files:**
- Create: `federation/ecosystem-cloud-adapter.v1.json`
- Create: `docs/ECOSYSTEM_CLOUD.md`
- Create: `tests/test_ecosystem_cloud_contract.py`

**Interfaces:**
- Project key `pytyliki`; upload is limited to explicitly selected aggregate profiles.

- [ ] Add failing assertions including a raw-device-identifier prohibition.
- [ ] Add adapter manifest and documentation.
- [ ] Run the focused unittest and the existing CTest/CI suite.

### Task 5: OPlague cloud adapter contract

**Files:**
- Create: `federation/ecosystem-cloud-adapter.v1.json`
- Create: `docs/ECOSYSTEM_CLOUD.md`
- Create: `tests/test_ecosystem_cloud_contract.py`

**Interfaces:**
- Project key `oplague`; only sanitized report metadata and hashes are eligible for explicit publication.

- [ ] Add failing assertions for driver-binary, INF-payload and raw-identifier exclusions.
- [ ] Add adapter manifest and documentation.
- [ ] Run the focused unittest and existing project validators.

### Task 6: VentuSample cloud adapter contract

**Files:**
- Create: `federation/ecosystem-cloud-adapter.v1.json`
- Create: `docs/ECOSYSTEM_CLOUD.md`
- Create: `tests/test_ecosystem_cloud_contract.py`

**Interfaces:**
- Project key `ventusample`; manifests may be shared by explicit publish action; recordings, sessions and plugin binaries remain local by default.

- [ ] Add failing assertions for audio-source and plugin-binary exclusions.
- [ ] Add adapter manifest and documentation.
- [ ] Run the focused unittest and existing project validators.

### Task 7: Cross-repository verification and sequential integration

**Files:** No additional source files; update only if test evidence requires a focused correction.

- [ ] Verify all five PRs against their current `main` heads.
- [ ] Require local Supabase migration/pgTAP CI on DuckOS and repository-native CI on each consumer.
- [ ] Review diffs for secrets, unwanted data classes, unpinned actions and accidental SDK dependencies.
- [ ] Merge the DuckOS foundation first, then Reaper, Pytyliki, OPlague and VentuSample only after each PR is green; stop on the first failed gate.
- [ ] Verify each merge commit and the final main-branch CI state.

