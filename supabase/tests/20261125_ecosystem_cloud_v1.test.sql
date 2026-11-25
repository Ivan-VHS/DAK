begin;

select plan(36);

select has_table('public', 'organizations', 'organizations table exists');
select has_table('public', 'organization_members', 'organization memberships table exists');
select has_table('public', 'devices', 'device registry exists');
select has_table('public', 'sync_events', 'append-only sync event table exists');
select has_table('public', 'artifacts', 'artifact metadata table exists');

select has_function('public', 'create_organization_v1', array['text', 'text'], 'organization creation RPC is versioned');
select has_function('private', 'is_org_member', array['uuid'], 'organization membership helper is private');
select has_function('private', 'has_org_role', array['uuid', 'text[]'], 'organization role helper is private');

select ok((select relrowsecurity from pg_class where oid = 'public.organizations'::regclass), 'organizations enforce RLS');
select ok((select relrowsecurity from pg_class where oid = 'public.organization_members'::regclass), 'memberships enforce RLS');
select ok((select relrowsecurity from pg_class where oid = 'public.devices'::regclass), 'devices enforce RLS');
select ok((select relrowsecurity from pg_class where oid = 'public.sync_events'::regclass), 'sync events enforce RLS');
select ok((select relrowsecurity from pg_class where oid = 'public.artifacts'::regclass), 'artifacts enforce RLS');
select ok(not has_table_privilege('anon', 'public.organizations', 'SELECT'), 'anon cannot read tenant organizations');
select ok(not has_table_privilege('anon', 'public.sync_events', 'INSERT'), 'anon cannot append sync events');
select ok(not has_function_privilege('anon', 'private.is_org_member(uuid)', 'EXECUTE'), 'anon cannot execute private membership helpers');

select is((select public from storage.buckets where id = 'ecosystem-artifacts'), false, 'artifact bucket is private');
select ok(exists (select 1 from pg_policies where schemaname = 'storage' and tablename = 'objects'
                  and policyname = 'ecosystem_artifacts_read_members'), 'artifact read policy is present');
select ok(exists (select 1 from pg_policies where schemaname = 'storage' and tablename = 'objects'
                  and policyname = 'ecosystem_artifacts_insert_editors'), 'artifact upload policy is present');

insert into auth.users (
  id, instance_id, aud, role, email, encrypted_password,
  email_confirmed_at, created_at, updated_at
) values
  ('10000000-0000-4000-8000-000000000001', '00000000-0000-0000-0000-000000000000',
   'authenticated', 'authenticated', 'alice@example.test', '', now(), now(), now()),
  ('10000000-0000-4000-8000-000000000002', '00000000-0000-0000-0000-000000000000',
   'authenticated', 'authenticated', 'bob@example.test', '', now(), now(), now());

insert into public.organizations (id, name, slug, created_by) values
  ('20000000-0000-4000-8000-000000000001', 'Alpha Workspace', 'alpha-test',
   '10000000-0000-4000-8000-000000000001'),
  ('20000000-0000-4000-8000-000000000002', 'Beta Workspace', 'beta-test',
   '10000000-0000-4000-8000-000000000002');

insert into public.organization_members (org_id, user_id, role) values
  ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 'owner'),
  ('20000000-0000-4000-8000-000000000002', '10000000-0000-4000-8000-000000000002', 'owner');

insert into public.devices (id, org_id, owner_id, label, platform) values
  ('30000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001',
   '10000000-0000-4000-8000-000000000001', 'Alice workstation', 'windows-x86_64'),
  ('30000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000002',
   '10000000-0000-4000-8000-000000000002', 'Bob workstation', 'linux-x86_64');

insert into public.sync_events (
  id, org_id, event_id, device_id, actor_id, source_project,
  schema_id, schema_version, event_type, occurred_at, payload
) values
  ('40000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001',
   '50000000-0000-4000-8000-000000000001', '30000000-0000-4000-8000-000000000001',
   '10000000-0000-4000-8000-000000000001', 'duckos',
   'ivan-vhs.ecosystem-event.v1', 1, 'workspace.snapshot_created', now(), '{"kind":"test"}'),
  ('40000000-0000-4000-8000-000000000002', '20000000-0000-4000-8000-000000000002',
   '50000000-0000-4000-8000-000000000002', '30000000-0000-4000-8000-000000000002',
   '10000000-0000-4000-8000-000000000002', 'duckos',
   'ivan-vhs.ecosystem-event.v1', 1, 'workspace.snapshot_created', now(), '{"kind":"test"}');

set local role authenticated;
select set_config('request.jwt.claim.sub', '10000000-0000-4000-8000-000000000001', true);
select set_config('request.jwt.claim.role', 'authenticated', true);
select set_config('request.jwt.claims',
  '{"sub":"10000000-0000-4000-8000-000000000001","role":"authenticated"}', true);

select is((select count(*)::integer from public.organizations), 1, 'Alice sees only her organization');
select is((select count(*)::integer from public.organization_members), 1, 'Alice sees only her organization memberships');
select is((select count(*)::integer from public.sync_events), 1, 'Alice sees only her organization events');

select lives_ok(
  $$insert into public.artifacts (org_id, created_by, source_project, artifact_kind, storage_key, sha256, byte_size)
    values ('20000000-0000-4000-8000-000000000001',
            '10000000-0000-4000-8000-000000000001', 'duckos', 'user_preferences',
            '20000000-0000-4000-8000-000000000001/settings.json',
            repeat('a', 64), 1)$$,
  'organization owner can register an explicitly selected artifact'
);

select throws_ok(
  $$insert into public.artifacts (org_id, created_by, source_project, artifact_kind, storage_key, sha256, byte_size)
    values ('20000000-0000-4000-8000-000000000001',
            '10000000-0000-4000-8000-000000000001', 'duckos', 'user_preferences',
            '20000000-0000-4000-8000-000000000001//settings.json',
            repeat('b', 64), 1)$$,
  '23514', null, 'artifact keys reject empty path segments'
);

select throws_ok(
  $$insert into public.artifacts (org_id, created_by, source_project, artifact_kind, storage_key, sha256, byte_size)
    values ('20000000-0000-4000-8000-000000000001',
            '10000000-0000-4000-8000-000000000001', 'duckos', 'user_preferences',
            '20000000-0000-4000-8000-000000000001/settings/',
            repeat('c', 64), 1)$$,
  '23514', null, 'artifact keys reject trailing path separators'
);

select throws_ok(
  $$insert into public.sync_events (
      org_id, event_id, device_id, actor_id, source_project,
      schema_id, schema_version, event_type, occurred_at, payload
    ) values (
      '20000000-0000-4000-8000-000000000001',
      '50000000-0000-4000-8000-000000000004',
      '30000000-0000-4000-8000-000000000001',
      '10000000-0000-4000-8000-000000000001',
      'duckos', repeat('a', 129), 1, 'workspace.invalid_schema', now(), '{}'::jsonb
    )$$,
  '23514', null, 'event schema identifiers are bounded to 128 characters'
);

select lives_ok(
  $$insert into public.sync_events (
      org_id, event_id, device_id, actor_id, source_project,
      schema_id, schema_version, event_type, occurred_at, payload
    ) values (
      '20000000-0000-4000-8000-000000000001',
      '50000000-0000-4000-8000-000000000003',
      '30000000-0000-4000-8000-000000000001',
      '10000000-0000-4000-8000-000000000001',
      'duckos', 'ivan-vhs.ecosystem-event.v1', 1,
      'workspace.preference_changed', now(), '{"setting":"theme"}'
    )$$,
  'Alice can append an event from her own device'
);

select throws_ok(
  $$insert into public.sync_events (
      org_id, event_id, device_id, actor_id, source_project,
      schema_id, schema_version, event_type, occurred_at, payload
    ) values (
      '20000000-0000-4000-8000-000000000001',
      '50000000-0000-4000-8000-000000000001',
      '30000000-0000-4000-8000-000000000001',
      '10000000-0000-4000-8000-000000000001',
      'duckos', 'ivan-vhs.ecosystem-event.v1', 1,
      'workspace.replayed', now(), '{"replay":true}'
    )$$,
  '23505',
  null,
  'duplicate event identifiers are rejected'
);

select throws_ok(
  $$insert into public.sync_events (
      org_id, event_id, device_id, actor_id, source_project,
      schema_id, schema_version, event_type, occurred_at, payload
    ) values (
      '20000000-0000-4000-8000-000000000002',
      '50000000-0000-4000-8000-000000000003',
      '30000000-0000-4000-8000-000000000002',
      '10000000-0000-4000-8000-000000000001',
      'duckos', 'ivan-vhs.ecosystem-event.v1', 1,
      'workspace.cross_tenant', now(), '{"attempt":"denied"}'
    )$$,
  '42501',
  null,
  'Alice cannot write events into Bob organization'
);

select throws_ok(
  $$update public.sync_events set event_type = 'workspace.tampered'
    where event_id = '50000000-0000-4000-8000-000000000001'$$,
  '42501',
  null,
  'sync events are immutable for client roles'
);

select set_config('request.jwt.claim.sub', '10000000-0000-4000-8000-000000000002', true);
select set_config('request.jwt.claims',
  '{"sub":"10000000-0000-4000-8000-000000000002","role":"authenticated"}', true);
select is((select count(*)::integer from public.organizations), 1, 'Bob sees only his organization');
select is((select count(*)::integer from public.sync_events), 1, 'Bob cannot read Alice events');

select set_config('request.jwt.claim.sub', '10000000-0000-4000-8000-000000000001', true);
select set_config('request.jwt.claims',
  '{"sub":"10000000-0000-4000-8000-000000000001","role":"authenticated"}', true);
select lives_ok(
  $$select public.create_organization_v1('Reaper Team', 'reaper-team-test')$$,
  'authenticated user can create an organization through the RPC'
);
select is(
  (select count(*)::integer from public.organization_members
   where user_id = '10000000-0000-4000-8000-000000000001'
     and role = 'owner'
     and org_id in (select id from public.organizations where slug = 'reaper-team-test')),
  1,
  'organization creation atomically assigns the creator as owner'
);
select throws_ok(
  $$select public.create_organization_v1('Invalid slug', 'bad slug')$$,
  '22023',
  null,
  'organization RPC rejects malformed slugs'
);

select throws_ok(
  $$insert into public.artifacts (org_id, created_by, source_project, artifact_kind, storage_key, sha256, byte_size)
    values ('20000000-0000-4000-8000-000000000001',
            '10000000-0000-4000-8000-000000000001', 'duckos', 'user_preferences',
            '20000000-0000-4000-8000-000000000001/file name.json',
            repeat('d', 64), 1)$$,
  '23514', null, 'artifact keys reject spaces and non-canonical characters'
);

select * from finish();
rollback;
