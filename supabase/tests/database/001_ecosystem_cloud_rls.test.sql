begin;

create extension if not exists pgtap with schema extensions;

select plan(14);

select has_table('public', 'ecosystem_organizations', 'organization metadata table exists');
select has_table('public', 'ecosystem_memberships', 'membership table exists');
select has_table('public', 'ecosystem_projects', 'project metadata table exists');
select has_table('public', 'ecosystem_artifacts', 'artifact metadata table exists');
select has_table('public', 'ecosystem_sync_receipts', 'idempotency receipts table exists');
select has_table('public', 'ecosystem_audit_events', 'audit event table exists');

select ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_organizations'::regclass), 'organizations RLS is enabled');
select ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_memberships'::regclass), 'memberships RLS is enabled');
select ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_projects'::regclass), 'projects RLS is enabled');
select ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_artifacts'::regclass), 'artifacts RLS is enabled');
select ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_sync_receipts'::regclass), 'sync receipts RLS is enabled');
select ok((select relrowsecurity from pg_class where oid = 'public.ecosystem_audit_events'::regclass), 'audit events RLS is enabled');

select is(
  (select count(*)::integer from pg_policies where schemaname = 'storage' and tablename = 'objects' and policyname like 'ecosystem_storage_%'),
  3,
  'storage bucket has explicit read, upload and delete policies'
);
select ok(
  exists (select 1 from storage.buckets where id = 'ecosystem-artifacts' and public = false and file_size_limit = 104857600),
  'artifact bucket is private and capped at 100 MiB'
);

select * from finish();
rollback;
