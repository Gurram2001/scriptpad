-- Run once in Supabase: SQL Editor > New query > paste > Run (safe to run again)
create table if not exists public.scripts (
  user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  id bigint not null,
  data jsonb not null,
  updated_at timestamptz not null default now(),
  deleted boolean not null default false,
  primary key (user_id, id)
);
alter table public.scripts drop constraint if exists scripts_id_positive;
alter table public.scripts add constraint scripts_id_positive check (id > 0);
alter table public.scripts drop constraint if exists scripts_data_size;
alter table public.scripts add constraint scripts_data_size check (pg_column_size(data) < 2000000);
alter table public.scripts enable row level security;
drop policy if exists "own rows" on public.scripts;
create policy "own rows" on public.scripts for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);
-- defence in depth: signed-out visitors get no access at all; the app never hard-deletes (it uses a "deleted" flag)
revoke all on public.scripts from anon;
revoke all on public.scripts from authenticated;
grant select, insert, update on public.scripts to authenticated;
