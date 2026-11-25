-- Supabase ecosystem foundation v1.
-- Local-first by design: clients authenticate as end users and never receive service-role credentials.

create schema if not exists private;
revoke all on schema private from public;

create table public.organizations (
    id uuid primary key default gen_random_uuid(),
    name text not null check (length(btrim(name)) between 2 and 120),
    slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$' and length(slug) <= 63),
    created_by uuid not null references auth.users (id) on delete restrict,
    created_at timestamptz not null default now()
);

create table public.organization_members (
    org_id uuid not null references public.organizations (id) on delete cascade,
    user_id uuid not null references auth.users (id) on delete cascade,
    role text not null check (role in ('owner', 'admin', 'editor', 'member', 'viewer')),
    created_at timestamptz not null default now(),
    primary key (org_id, user_id)
);

create index organization_members_user_id_idx
    on public.organization_members (user_id, org_id);

create table public.devices (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organizations (id) on delete cascade,
    owner_id uuid not null references auth.users (id) on delete restrict,
    label text not null check (length(btrim(label)) between 1 and 120),
    platform text not null check (platform ~ '^[a-z0-9][a-z0-9._-]{0,63}$'),
    fingerprint_sha256 text check (
        fingerprint_sha256 is null or fingerprint_sha256 ~ '^[0-9a-f]{64}$'
    ),
    created_at timestamptz not null default now(),
    unique (org_id, fingerprint_sha256)
);

create index devices_owner_org_idx on public.devices (owner_id, org_id);

create table public.sync_events (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organizations (id) on delete cascade,
    event_id uuid not null,
    device_id uuid not null references public.devices (id) on delete restrict,
    actor_id uuid not null references auth.users (id) on delete restrict,
    source_project text not null check (
        source_project in ('duckos', 'reaper', 'pytyliki', 'ventusample', 'oplague')
    ),
    schema_id text not null check (schema_id ~ '^[a-z0-9]+([.-][a-z0-9]+)*$'),
    schema_version smallint not null check (schema_version > 0),
    event_type text not null check (event_type ~ '^[a-z][a-z0-9_.-]{0,127}$'),
    occurred_at timestamptz not null,
    payload jsonb not null check (
        jsonb_typeof(payload) = 'object' and pg_column_size(payload) <= 65536
    ),
    created_at timestamptz not null default now(),
    unique (org_id, event_id)
);

create index sync_events_org_created_idx
    on public.sync_events (org_id, created_at desc);

create table public.artifacts (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references public.organizations (id) on delete cascade,
    created_by uuid not null references auth.users (id) on delete restrict,
    source_project text not null check (
        source_project in ('duckos', 'reaper', 'pytyliki', 'ventusample', 'oplague')
    ),
    artifact_kind text not null check (artifact_kind ~ '^[a-z][a-z0-9_.-]{0,63}$'),
    storage_key text not null check (
        length(storage_key) <= 512
        and storage_key !~ '(^|/)[.][.]?(/|$)'
        and storage_key !~ '[[:cntrl:]]'
    ),
    sha256 text not null check (sha256 ~ '^[0-9a-f]{64}$'),
    byte_size bigint not null check (byte_size between 1 and 536870912),
    metadata jsonb not null default '{}'::jsonb check (
        jsonb_typeof(metadata) = 'object' and pg_column_size(metadata) <= 16384
    ),
    created_at timestamptz not null default now(),
    unique (org_id, storage_key),
    check (storage_key like org_id::text || '/%')
);

create index artifacts_org_created_idx
    on public.artifacts (org_id, created_at desc);

create or replace function private.is_org_member(target_org_id uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $function$
    select exists (
        select 1
        from public.organization_members as membership
        where membership.org_id = target_org_id
          and membership.user_id = (select auth.uid())
    );
$function$;

create or replace function private.has_org_role(target_org_id uuid, allowed_roles text[])
returns boolean
language sql
stable
security definer
set search_path = ''
as $function$
    select exists (
        select 1
        from public.organization_members as membership
        where membership.org_id = target_org_id
          and membership.user_id = (select auth.uid())
          and membership.role = any (allowed_roles)
    );
$function$;

revoke all on function private.is_org_member(uuid) from public;
revoke all on function private.has_org_role(uuid, text[]) from public;
grant usage on schema private to authenticated;
grant execute on function private.is_org_member(uuid) to authenticated;
grant execute on function private.has_org_role(uuid, text[]) to authenticated;

create or replace function public.create_organization_v1(p_name text, p_slug text)
returns uuid
language plpgsql
security definer
set search_path = ''
as $function$
declare
    actor_id uuid := auth.uid();
    new_org_id uuid;
begin
    if actor_id is null then
        raise exception 'authentication required' using errcode = '28000';
    end if;

    if p_name is null or length(btrim(p_name)) not between 2 and 120 then
        raise exception 'organization name must contain 2 to 120 characters'
            using errcode = '22023';
    end if;

    if p_slug is null
       or length(p_slug) > 63
       or p_slug !~ '^[a-z0-9]+(-[a-z0-9]+)*$' then
        raise exception 'organization slug is invalid' using errcode = '22023';
    end if;

    insert into public.organizations (name, slug, created_by)
    values (btrim(p_name), p_slug, actor_id)
    returning id into new_org_id;

    insert into public.organization_members (org_id, user_id, role)
    values (new_org_id, actor_id, 'owner');

    return new_org_id;
end;
$function$;

revoke all on function public.create_organization_v1(text, text) from public;
grant execute on function public.create_organization_v1(text, text) to authenticated;

alter table public.organizations enable row level security;
alter table public.organization_members enable row level security;
alter table public.devices enable row level security;
alter table public.sync_events enable row level security;
alter table public.artifacts enable row level security;

revoke all on public.organizations from anon, authenticated;
revoke all on public.organization_members from anon, authenticated;
revoke all on public.devices from anon, authenticated;
revoke all on public.sync_events from anon, authenticated;
revoke all on public.artifacts from anon, authenticated;

grant select on public.organizations to authenticated;
grant select on public.organization_members to authenticated;
grant select, insert, delete on public.devices to authenticated;
grant select, insert on public.sync_events to authenticated;
grant select, insert on public.artifacts to authenticated;

create policy organizations_read_members
    on public.organizations
    for select
    to authenticated
    using (private.is_org_member(id));

create policy organization_members_read_members
    on public.organization_members
    for select
    to authenticated
    using (private.is_org_member(org_id));

create policy devices_read_members
    on public.devices
    for select
    to authenticated
    using (private.is_org_member(org_id));

create policy devices_insert_self
    on public.devices
    for insert
    to authenticated
    with check (
        owner_id = (select auth.uid())
        and private.is_org_member(org_id)
    );

create policy devices_delete_owner
    on public.devices
    for delete
    to authenticated
    using (
        owner_id = (select auth.uid())
        and private.is_org_member(org_id)
    );

create policy sync_events_read_members
    on public.sync_events
    for select
    to authenticated
    using (private.is_org_member(org_id));

create policy sync_events_insert_owned_device
    on public.sync_events
    for insert
    to authenticated
    with check (
        actor_id = (select auth.uid())
        and private.is_org_member(org_id)
        and exists (
            select 1
            from public.devices as device
            where device.id = sync_events.device_id
              and device.org_id = sync_events.org_id
              and device.owner_id = (select auth.uid())
        )
    );

create policy artifacts_read_members
    on public.artifacts
    for select
    to authenticated
    using (private.is_org_member(org_id));

create policy artifacts_insert_editors
    on public.artifacts
    for insert
    to authenticated
    with check (
        created_by = (select auth.uid())
        and private.has_org_role(org_id, array['owner', 'admin', 'editor']::text[])
    );

insert into storage.buckets (id, name, public, file_size_limit)
values ('ecosystem-artifacts', 'ecosystem-artifacts', false, 536870912)
on conflict (id) do update
set public = false,
    file_size_limit = excluded.file_size_limit;

create policy ecosystem_artifacts_read_members
    on storage.objects
    for select
    to authenticated
    using (
        bucket_id = 'ecosystem-artifacts'
        and case
            when split_part(name, '/', 1) ~
                '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            then private.is_org_member(split_part(name, '/', 1)::uuid)
            else false
        end
    );

create policy ecosystem_artifacts_insert_editors
    on storage.objects
    for insert
    to authenticated
    with check (
        bucket_id = 'ecosystem-artifacts'
        and case
            when split_part(name, '/', 1) ~
                '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            then private.has_org_role(
                split_part(name, '/', 1)::uuid,
                array['owner', 'admin', 'editor']::text[]
            )
            else false
        end
    );
