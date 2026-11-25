begin;

create extension if not exists pgtap with schema extensions;

select plan(28);

select extensions.has_table('public', 'ecosystem_organizations', 'organization metadata table exists');
select extensions.has_table('public', 'ecosystem_memberships', 'membership table exists');
select extensions.has_table('public', 'ecosystem_projects', 'project metadata table exists');
select extensions.has_table('public', 'ecosystem_artifacts', 'artifact metadata table exists');
select extensions.has_table('public', 'ecosystem_sync_receipts', 'idempotency receipts table exists');
select extensions.has_table('public', 'ecosystem_audit_events', 'audit event table exists');

select extensions.ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_organizations'::regclass), 'organizations RLS is enabled');
select extensions.ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_memberships'::regclass), 'memberships RLS is enabled');
select extensions.ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_projects'::regclass), 'projects RLS is enabled');
select extensions.ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_artifacts'::regclass), 'artifacts RLS is enabled');
select extensions.ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_sync_receipts'::regclass), 'sync receipts RLS is enabled');
select extensions.ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_audit_events'::regclass), 'audit events RLS is enabled');

select extensions.is(
  (select count(*)::integer from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname like 'ecosystem_storage_%'),
  3,
  'storage bucket has explicit read, upload and delete policies'
);
select extensions.ok(
  exists (select 1 from storage.buckets where id = 'ecosystem-artifacts' and public = false and file_size_limit = 104857600),
  'artifact bucket is private and capped at 100 MiB'
);

select extensions.ok(
  (select qual like '%ecosystem_artifacts%' and qual like '%visibility%'
   from pg_policies where schemaname = 'storage' and tablename = 'objects'
     and policyname = 'ecosystem_storage_select_artifact'),
  'storage reads follow artifact visibility metadata'
);
select extensions.ok(
  (select with_check like '%ecosystem_artifacts%' and with_check like '%owner_id%' and with_check like '%ecosystem_memberships%' and with_check like '%contributor%'
   from pg_policies where schemaname = 'storage' and tablename = 'objects'
     and policyname = 'ecosystem_storage_insert_owned_artifact'),
  'storage uploads require a pre-existing artifact owned by the caller'
);
select extensions.ok(
  (select qual like '%ecosystem_artifacts%' and qual like '%ecosystem_memberships%'
   from pg_policies where schemaname = 'storage' and tablename = 'objects'
     and policyname = 'ecosystem_storage_delete_owner_or_admin'),
  'storage deletion is restricted to artifact owners or organization admins'
);
select extensions.ok(
  not has_table_privilege('authenticated', 'public.ecosystem_audit_events', 'INSERT'),
  'authenticated clients cannot forge audit events'
);
select extensions.ok(
  has_table_privilege('service_role', 'public.ecosystem_audit_events', 'INSERT'),
  'trusted server role can append audit events'
);
select extensions.is(
  (select count(*)::integer
   from pg_trigger
   where not tgisinternal
     and tgname in ('ecosystem_organizations_audit', 'ecosystem_memberships_audit', 'ecosystem_projects_audit', 'ecosystem_artifacts_audit')),
  4,
  'organization, project and artifact mutations have audit triggers'
);

insert into auth.users (id, aud, role, email, encrypted_password, email_confirmed_at, created_at, updated_at)
values
  ('10000000-0000-4000-8000-000000000001', 'authenticated', 'authenticated', 'cloud-a@example.invalid', '', now(), now(), now()),
  ('20000000-0000-4000-8000-000000000002', 'authenticated', 'authenticated', 'cloud-b@example.invalid', '', now(), now(), now());

select set_config('request.jwt.claim.sub', '10000000-0000-4000-8000-000000000001', true);
select set_config('request.jwt.claims', '{"sub":"10000000-0000-4000-8000-000000000001","role":"authenticated"}', true);

insert into public.ecosystem_organizations (id, slug, display_name, created_by)
values ('10000000-0000-4000-8000-000000000010', 'cloud-a', 'Cloud A', '10000000-0000-4000-8000-000000000001');

insert into public.ecosystem_projects (id, organization_id, project_key, display_name, created_by)
values ('10000000-0000-4000-8000-000000000011', '10000000-0000-4000-8000-000000000010', 'reaper', 'Reaper A', '10000000-0000-4000-8000-000000000001');

insert into public.ecosystem_artifacts (
  id, organization_id, project_id, project_key, owner_id,
  artifact_kind, visibility, content_type, sha256, size_bytes
)
values (
  '10000000-0000-4000-8000-000000000012', '10000000-0000-4000-8000-000000000010',
  '10000000-0000-4000-8000-000000000011', 'reaper',
  '10000000-0000-4000-8000-000000000001', 'report', 'organization',
  'application/json', repeat('a', 64), 128
);

select set_config('request.jwt.claim.sub', '20000000-0000-4000-8000-000000000002', true);
select set_config('request.jwt.claims', '{"sub":"20000000-0000-4000-8000-000000000002","role":"authenticated"}', true);

insert into public.ecosystem_organizations (id, slug, display_name, created_by)
values ('20000000-0000-4000-8000-000000000020', 'cloud-b', 'Cloud B', '20000000-0000-4000-8000-000000000002');

insert into public.ecosystem_projects (id, organization_id, project_key, display_name, created_by)
values ('20000000-0000-4000-8000-000000000021', '20000000-0000-4000-8000-000000000020', 'oplague', 'OPlague B', '20000000-0000-4000-8000-000000000002');

insert into public.ecosystem_artifacts (
  id, organization_id, project_id, project_key, owner_id,
  artifact_kind, visibility, content_type, sha256, size_bytes
)
values (
  '20000000-0000-4000-8000-000000000022', '20000000-0000-4000-8000-000000000020',
  '20000000-0000-4000-8000-000000000021', 'oplague',
  '20000000-0000-4000-8000-000000000002', 'report', 'organization',
  'application/json', repeat('b', 64), 256
);

set local role authenticated;

select set_config('request.jwt.claim.sub', '10000000-0000-4000-8000-000000000001', true);
select set_config('request.jwt.claims', '{"sub":"10000000-0000-4000-8000-000000000001","role":"authenticated"}', true);
select extensions.is((select count(*)::integer from public.ecosystem_organizations), 1, 'user A sees only organization A');
select extensions.is((select count(*)::integer from public.ecosystem_projects), 1, 'user A sees only project A');
select extensions.is((select count(*)::integer from public.ecosystem_artifacts), 1, 'user A sees only artifact A');
select extensions.ok((select count(*) > 0 from public.ecosystem_audit_events), 'user A can read audit events created by their own changes');

select set_config('request.jwt.claim.sub', '20000000-0000-4000-8000-000000000002', true);
select set_config('request.jwt.claims', '{"sub":"20000000-0000-4000-8000-000000000002","role":"authenticated"}', true);
select extensions.is((select count(*)::integer from public.ecosystem_organizations), 1, 'user B sees only organization B');
select extensions.is((select count(*)::integer from public.ecosystem_projects), 1, 'user B sees only project B');
select extensions.is((select count(*)::integer from public.ecosystem_artifacts), 1, 'user B sees only artifact B');
select extensions.ok((select count(*) > 0 from public.ecosystem_audit_events), 'user B can read audit events created by their own changes');

select * from extensions.finish();
rollback;
