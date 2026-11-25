-- Ecosystem Cloud Foundation v1
-- Local-first contract. No client receives a service-role credential.

create schema if not exists private;

create table if not exists public.ecosystem_organizations (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique check (slug ~ '^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$'),
  display_name text not null check (length(trim(display_name)) between 1 and 120),
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now()
);

create table if not exists public.ecosystem_memberships (
  organization_id uuid not null references public.ecosystem_organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'editor', 'contributor', 'viewer')),
  created_at timestamptz not null default now(),
  primary key (organization_id, user_id)
);

create index if not exists ecosystem_memberships_user_org_idx
  on public.ecosystem_memberships (user_id, organization_id);

create or replace function private.attach_ecosystem_creator_as_owner()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.ecosystem_memberships (organization_id, user_id, role)
  values (new.id, new.created_by, 'owner');
  return new;
end;
$$;

revoke all on function private.attach_ecosystem_creator_as_owner() from public, anon, authenticated;

drop trigger if exists ecosystem_organizations_attach_owner on public.ecosystem_organizations;
create trigger ecosystem_organizations_attach_owner
after insert on public.ecosystem_organizations
for each row execute function private.attach_ecosystem_creator_as_owner();

create table if not exists public.ecosystem_projects (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.ecosystem_organizations(id) on delete cascade,
  project_key text not null check (project_key ~ '^[a-z][a-z0-9-]{1,47}$'),
  display_name text not null check (length(trim(display_name)) between 1 and 120),
  repository_full_name text check (repository_full_name is null or repository_full_name ~ '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'),
  created_by uuid not null references auth.users(id) on delete restrict,
  created_at timestamptz not null default now(),
  unique (organization_id, project_key),
  unique (id, organization_id, project_key)
);

create index if not exists ecosystem_projects_org_idx
  on public.ecosystem_projects (organization_id);

create table if not exists public.ecosystem_artifacts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.ecosystem_organizations(id) on delete cascade,
  project_id uuid not null,
  project_key text not null,
  owner_id uuid not null references auth.users(id) on delete restrict,
  artifact_kind text not null check (artifact_kind in ('document', 'manifest', 'report', 'preset-pack', 'release-metadata')),
  visibility text not null check (visibility in ('private', 'organization')),
  object_key text unique,
  content_type text not null check (length(content_type) between 1 and 120),
  sha256 text not null check (sha256 ~ '^[a-f0-9]{64}$'),
  size_bytes bigint not null check (size_bytes between 0 and 104857600),
  created_at timestamptz not null default now(),
  foreign key (project_id, organization_id, project_key)
    references public.ecosystem_projects (id, organization_id, project_key) on delete cascade,
  check (object_key is null or object_key = organization_id::text || '/' || project_key || '/' || id::text)
);

create index if not exists ecosystem_artifacts_org_project_idx
  on public.ecosystem_artifacts (organization_id, project_id);
create index if not exists ecosystem_artifacts_owner_idx
  on public.ecosystem_artifacts (owner_id);

create table if not exists public.ecosystem_sync_receipts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.ecosystem_organizations(id) on delete cascade,
  project_id uuid not null references public.ecosystem_projects(id) on delete cascade,
  actor_id uuid not null references auth.users(id) on delete restrict,
  client_instance_id uuid not null,
  event_id uuid not null,
  payload_sha256 text not null check (payload_sha256 ~ '^[a-f0-9]{64}$'),
  occurred_at timestamptz not null,
  received_at timestamptz not null default now(),
  unique (actor_id, client_instance_id, event_id)
);

create index if not exists ecosystem_sync_receipts_org_received_idx
  on public.ecosystem_sync_receipts (organization_id, received_at desc);

create table if not exists public.ecosystem_audit_events (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references public.ecosystem_organizations(id) on delete cascade,
  actor_id uuid references auth.users(id) on delete set null,
  project_key text not null,
  action text not null check (action ~ '^[a-z][a-z0-9_.-]{1,63}$'),
  subject_type text not null check (length(subject_type) between 1 and 64),
  subject_id text check (subject_id is null or length(subject_id) <= 128),
  request_id uuid,
  occurred_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb check (
    jsonb_typeof(metadata) = 'object' and octet_length(metadata::text) <= 4096
  )
);

create index if not exists ecosystem_audit_events_org_time_idx
  on public.ecosystem_audit_events (organization_id, occurred_at desc);
create index if not exists ecosystem_audit_events_actor_time_idx
  on public.ecosystem_audit_events (actor_id, occurred_at desc);

create or replace function private.append_ecosystem_audit_event()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
declare
  row_data jsonb;
  v_organization_id uuid;
  v_project_key text;
  v_subject_type text;
begin
  if tg_op = 'DELETE' then
    row_data := to_jsonb(old);
  else
    row_data := to_jsonb(new);
  end if;

  if tg_table_name = 'ecosystem_organizations' then
    v_organization_id := (row_data ->> 'id')::uuid;
    v_project_key := 'ecosystem';
    v_subject_type := 'organization';
  elsif tg_table_name = 'ecosystem_projects' then
    v_organization_id := (row_data ->> 'organization_id')::uuid;
    v_project_key := row_data ->> 'project_key';
    v_subject_type := 'project';
  elsif tg_table_name = 'ecosystem_artifacts' then
    v_organization_id := (row_data ->> 'organization_id')::uuid;
    v_project_key := row_data ->> 'project_key';
    v_subject_type := 'artifact';
  else
    raise exception 'Unsupported ecosystem audit source: %', tg_table_name;
  end if;

  insert into public.ecosystem_audit_events (
    organization_id,
    actor_id,
    project_key,
    action,
    subject_type,
    subject_id,
    metadata
  )
  values (
    v_organization_id,
    auth.uid(),
    v_project_key,
    lower(tg_table_name || '.' || tg_op),
    v_subject_type,
    row_data ->> 'id',
    jsonb_build_object('source_table', tg_table_name, 'operation', tg_op)
  );

  return null;
end;
$$;

revoke all on function private.append_ecosystem_audit_event() from public, anon, authenticated;

drop trigger if exists ecosystem_organizations_audit on public.ecosystem_organizations;
create trigger ecosystem_organizations_audit
after insert or update or delete on public.ecosystem_organizations
for each row execute function private.append_ecosystem_audit_event();

drop trigger if exists ecosystem_projects_audit on public.ecosystem_projects;
create trigger ecosystem_projects_audit
after insert or update or delete on public.ecosystem_projects
for each row execute function private.append_ecosystem_audit_event();

drop trigger if exists ecosystem_artifacts_audit on public.ecosystem_artifacts;
create trigger ecosystem_artifacts_audit
after insert or update or delete on public.ecosystem_artifacts
for each row execute function private.append_ecosystem_audit_event();

alter table public.ecosystem_organizations enable row level security;
alter table public.ecosystem_memberships enable row level security;
alter table public.ecosystem_projects enable row level security;
alter table public.ecosystem_artifacts enable row level security;
alter table public.ecosystem_sync_receipts enable row level security;
alter table public.ecosystem_audit_events enable row level security;

revoke all on public.ecosystem_organizations from anon, authenticated;
revoke all on public.ecosystem_memberships from anon, authenticated;
revoke all on public.ecosystem_projects from anon, authenticated;
revoke all on public.ecosystem_artifacts from anon, authenticated;
revoke all on public.ecosystem_sync_receipts from anon, authenticated;
revoke all on public.ecosystem_audit_events from anon, authenticated;

grant select, insert, update on public.ecosystem_organizations to authenticated;
grant select on public.ecosystem_memberships to authenticated;
grant select, insert, update, delete on public.ecosystem_projects to authenticated;
grant select, insert, update, delete on public.ecosystem_artifacts to authenticated;
grant select, insert on public.ecosystem_sync_receipts to authenticated;
grant select on public.ecosystem_audit_events to authenticated;\ngrant select, insert on public.ecosystem_audit_events to service_role;
grant all on public.ecosystem_organizations, public.ecosystem_memberships,
  public.ecosystem_projects, public.ecosystem_artifacts,
  public.ecosystem_sync_receipts, public.ecosystem_audit_events to service_role;

create policy ecosystem_organizations_select_member
on public.ecosystem_organizations for select to authenticated
using (exists (
  select 1 from public.ecosystem_memberships m
  where m.organization_id = id and m.user_id = (select auth.uid())
));

create policy ecosystem_organizations_insert_creator
on public.ecosystem_organizations for insert to authenticated
with check (created_by = (select auth.uid()));

create policy ecosystem_organizations_update_owner
on public.ecosystem_organizations for update to authenticated
using (exists (
  select 1 from public.ecosystem_memberships m
  where m.organization_id = id and m.user_id = (select auth.uid()) and m.role in ('owner', 'admin')
))
with check (exists (
  select 1 from public.ecosystem_memberships m
  where m.organization_id = ecosystem_organizations.id
    and m.user_id = (select auth.uid()) and m.role in ('owner', 'admin')
));

create policy ecosystem_memberships_select_self
on public.ecosystem_memberships for select to authenticated
using (user_id = (select auth.uid()));

create policy ecosystem_projects_select_member
on public.ecosystem_projects for select to authenticated
using (exists (
  select 1 from public.ecosystem_memberships m
  where m.organization_id = ecosystem_projects.organization_id and m.user_id = (select auth.uid())
));

create policy ecosystem_projects_insert_contributor
on public.ecosystem_projects for insert to authenticated
with check (
  created_by = (select auth.uid())
  and exists (
    select 1 from public.ecosystem_memberships m
    where m.organization_id = ecosystem_projects.organization_id and m.user_id = (select auth.uid())
      and m.role in ('owner', 'admin', 'editor', 'contributor')
  )
);

create policy ecosystem_projects_update_editor
on public.ecosystem_projects for update to authenticated
using (exists (
  select 1 from public.ecosystem_memberships m
  where m.organization_id = ecosystem_projects.organization_id and m.user_id = (select auth.uid())
    and m.role in ('owner', 'admin', 'editor')
))
with check (exists (
  select 1 from public.ecosystem_memberships m
  where m.organization_id = ecosystem_projects.organization_id and m.user_id = (select auth.uid())
    and m.role in ('owner', 'admin', 'editor')
));

create policy ecosystem_projects_delete_admin
on public.ecosystem_projects for delete to authenticated
using (exists (
  select 1 from public.ecosystem_memberships m
  where m.organization_id = ecosystem_projects.organization_id and m.user_id = (select auth.uid())
    and m.role in ('owner', 'admin')
));

create policy ecosystem_artifacts_select_member
on public.ecosystem_artifacts for select to authenticated
using (
  exists (
    select 1 from public.ecosystem_memberships m
    where m.organization_id = ecosystem_artifacts.organization_id and m.user_id = (select auth.uid())
  )
  and (visibility = 'organization' or owner_id = (select auth.uid()))
);

create policy ecosystem_artifacts_insert_contributor
on public.ecosystem_artifacts for insert to authenticated
with check (
  owner_id = (select auth.uid())
  and exists (
    select 1 from public.ecosystem_projects p
    where p.id = project_id and p.organization_id = ecosystem_artifacts.organization_id
  )
  and exists (
    select 1 from public.ecosystem_memberships m
    where m.organization_id = ecosystem_artifacts.organization_id and m.user_id = (select auth.uid())
      and m.role in ('owner', 'admin', 'editor', 'contributor')
  )
);

create policy ecosystem_artifacts_update_owner
on public.ecosystem_artifacts for update to authenticated
using (
  owner_id = (select auth.uid())
  or exists (
    select 1 from public.ecosystem_memberships m
    where m.organization_id = ecosystem_artifacts.organization_id and m.user_id = (select auth.uid())
      and m.role in ('owner', 'admin', 'editor')
  )
)
with check (
  exists (
    select 1 from public.ecosystem_memberships m
    where m.organization_id = ecosystem_artifacts.organization_id and m.user_id = (select auth.uid())
      and (owner_id = (select auth.uid()) or m.role in ('owner', 'admin'))
  )
);

create policy ecosystem_artifacts_delete_owner
on public.ecosystem_artifacts for delete to authenticated
using (
  owner_id = (select auth.uid())
  or exists (
    select 1 from public.ecosystem_memberships m
    where m.organization_id = ecosystem_artifacts.organization_id and m.user_id = (select auth.uid())
      and m.role in ('owner', 'admin')
  )
);

create policy ecosystem_sync_receipts_select_actor
on public.ecosystem_sync_receipts for select to authenticated
using (actor_id = (select auth.uid()));

create policy ecosystem_sync_receipts_insert_actor
on public.ecosystem_sync_receipts for insert to authenticated
with check (
  actor_id = (select auth.uid())
  and exists (
    select 1 from public.ecosystem_memberships m
    where m.organization_id = ecosystem_sync_receipts.organization_id and m.user_id = (select auth.uid())
  )
  and exists (
    select 1 from public.ecosystem_projects p
    where p.id = project_id and p.organization_id = ecosystem_sync_receipts.organization_id
  )
);

create policy ecosystem_audit_events_select_actor
on public.ecosystem_audit_events for select to authenticated
using (actor_id = (select auth.uid()));

insert into storage.buckets (id, name, public, file_size_limit)
values ('ecosystem-artifacts', 'ecosystem-artifacts', false, 104857600)
on conflict (id) do nothing;

create policy ecosystem_storage_select_artifact
on storage.objects for select to authenticated
using (
  bucket_id = 'ecosystem-artifacts'
  and array_length(storage.foldername(name), 1) = 2
  and exists (
    select 1
    from public.ecosystem_artifacts a
    where a.object_key = name
      and a.organization_id::text = (storage.foldername(name))[1]
      and a.project_key = (storage.foldername(name))[2]
      and (a.visibility = 'organization' or a.owner_id = (select auth.uid()))
  )
);

create policy ecosystem_storage_insert_owned_artifact
on storage.objects for insert to authenticated
with check (
  bucket_id = 'ecosystem-artifacts'
  and array_length(storage.foldername(name), 1) = 2
  and exists (
    select 1
    from public.ecosystem_artifacts a
    where a.object_key = name
      and a.organization_id::text = (storage.foldername(name))[1]
      and a.project_key = (storage.foldername(name))[2]
      and a.owner_id = (select auth.uid())
      and exists (
        select 1 from public.ecosystem_memberships m
        where m.organization_id = a.organization_id
          and m.user_id = (select auth.uid())
          and m.role in ('owner', 'admin', 'editor', 'contributor')
      )
  )
);

create policy ecosystem_storage_delete_owner_or_admin
on storage.objects for delete to authenticated
using (
  bucket_id = 'ecosystem-artifacts'
  and array_length(storage.foldername(name), 1) = 2
  and (
    exists (
      select 1 from public.ecosystem_artifacts a
      where a.object_key = name
        and a.organization_id::text = (storage.foldername(name))[1]
        and a.project_key = (storage.foldername(name))[2]
        and a.owner_id = (select auth.uid())
    )
    or exists (
      select 1 from public.ecosystem_memberships m
      where m.organization_id::text = (storage.foldername(name))[1]
        and m.user_id = (select auth.uid())
        and m.role in ('owner', 'admin')
    )
  )
);
