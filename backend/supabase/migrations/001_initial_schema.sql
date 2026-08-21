-- ConsentShield initial schema.
-- Table definitions copied verbatim from the API contract (Section 11);
-- RLS policies implement Section 12's requirement that every policy
-- restrict access using the authenticated user identity (auth.uid()).

create table privacy_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  mode text not null check (mode in ('strict','balanced','functional','custom','manual')),
  categories jsonb not null,
  auto_apply boolean not null default false,
  require_confirmation_for_unknown boolean not null default true,
  allow_network_observation boolean not null default true,
  save_scan_history boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table scans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  origin text not null,
  target_url text not null,
  scan_mode text not null,
  execution_mode text not null,
  status text not null,
  workflow_mode text,
  result jsonb,
  limitations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);

create table scan_events (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid not null references scans(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  event_type text not null,
  hostname text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table workflow_commands (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  site_key text not null,
  command_name text not null,
  version integer not null default 1,
  workflow jsonb not null,
  output_schema jsonb not null,
  safety_policy jsonb not null,
  last_verified_at timestamptz,
  created_at timestamptz not null default now(),
  unique(user_id, site_key, command_name, version)
);

create table execution_plans (
  id uuid primary key default gen_random_uuid(),
  scan_id uuid not null references scans(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  hostname text not null,
  page_instance_hash text not null,
  action text not null,
  plan jsonb not null,
  status text not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);

-- Row Level Security: every user-owned table is restricted to auth.uid().

alter table privacy_preferences enable row level security;
alter table scans enable row level security;
alter table scan_events enable row level security;
alter table workflow_commands enable row level security;
alter table execution_plans enable row level security;

create policy "Users manage their own preferences"
  on privacy_preferences for all
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy "Users manage their own scans"
  on scans for all
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy "Users manage their own scan events"
  on scan_events for all
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy "Users manage their own workflow commands"
  on workflow_commands for all
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy "Users manage their own execution plans"
  on execution_plans for all
  using (user_id = auth.uid())
  with check (user_id = auth.uid());
