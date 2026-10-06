-- =============================================================================
--  HydroDesk – Datenbank-Schema für Supabase
-- =============================================================================
--  So benutzen:
--    Supabase-Dashboard -> SQL Editor -> "New query" -> ALLES einfügen -> "Run"
--  Das Skript darf mehrfach ausgeführt werden (es legt nichts doppelt an).
--
--  Inhalt:
--    1. Tabellen profiles und drink_entries
--    2. Hilfsfunktion is_admin() (security definer, verhindert RLS-Rekursion)
--    3. Row Level Security (RLS): jeder sieht nur seine eigenen Zeilen,
--       Admins dürfen ALLE Zeilen lesen
--    4. Schutz der Spalte role (nur Admin / Dashboard darf sie ändern)
--    5. Trigger: Profil automatisch bei der Registrierung anlegen
--    6. Views daily_totals (Summe pro Tag) und user_today (Admin-Übersicht)
--    7. Rechte (Grants)
--
--  Admin werden (einmalig im SQL Editor ausführen, E-Mail anpassen):
--    update public.profiles set role = 'admin' where email = 'deine@mail.de';
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. TABELLEN
-- -----------------------------------------------------------------------------

-- Ein Profil pro Nutzer (id = id aus auth.users, also dem Supabase-Login)
create table if not exists public.profiles (
    id            uuid primary key references auth.users (id) on delete cascade,
    name          text,
    email         text,
    weight_kg     numeric(5, 1) check (weight_kg between 30 and 250),
    height_cm     integer       check (height_cm between 120 and 230),
    daily_goal_ml integer not null default 2000 check (daily_goal_ml between 500 and 6000),
    role          text    not null default 'user' check (role in ('user', 'admin')),
    created_at    timestamptz not null default now()
);

comment on table  public.profiles is 'Profil je Nutzer: Körperdaten, Tagesziel, Rolle (user/admin)';
comment on column public.profiles.daily_goal_ml is 'Tagesziel in ml (Mosteller-KOF * 1500 ml, gerundet auf 50, 1500..3500) – berechnet von der App';

-- Ein Eintrag pro erkanntem Schluck. Die id erzeugt die App (UUID),
-- damit mehrfaches Hochladen keine Duplikate erzeugt.
create table if not exists public.drink_entries (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null default auth.uid() references auth.users (id) on delete cascade,
    ts         timestamptz not null default now(),   -- Zeitpunkt des Schlucks
    ml         integer not null check (ml > 0 and ml <= 10000),
    device     text,                                  -- Quelle: 'HydroDesk', 'Demo', ...
    created_at timestamptz not null default now()     -- Zeitpunkt des Hochladens
);

comment on table public.drink_entries is 'Trink-Einträge (ein Schluck = eine Zeile)';

create index if not exists drink_entries_user_ts_idx on public.drink_entries (user_id, ts desc);


-- -----------------------------------------------------------------------------
-- 2. HILFSFUNKTION is_admin()
-- -----------------------------------------------------------------------------
-- "security definer" = läuft mit den Rechten des Erstellers und umgeht dadurch RLS.
-- Ohne das würde die Policy auf profiles beim Prüfen der Rolle wieder profiles
-- lesen -> Endlosschleife ("infinite recursion detected in policy").
create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select exists (
        select 1 from public.profiles
        where id = auth.uid() and role = 'admin'
    );
$$;

revoke all on function public.is_admin() from public, anon;
grant execute on function public.is_admin() to authenticated;


-- -----------------------------------------------------------------------------
-- 3. ROW LEVEL SECURITY
-- -----------------------------------------------------------------------------
alter table public.profiles      enable row level security;
alter table public.drink_entries enable row level security;

-- profiles ---------------------------------------------------------------
drop policy if exists "profiles: eigenes lesen, Admin alle" on public.profiles;
create policy "profiles: eigenes lesen, Admin alle"
    on public.profiles for select to authenticated
    using (id = (select auth.uid()) or (select public.is_admin()));

drop policy if exists "profiles: eigenes anlegen" on public.profiles;
create policy "profiles: eigenes anlegen"
    on public.profiles for insert to authenticated
    with check (id = (select auth.uid()));

drop policy if exists "profiles: eigenes ändern" on public.profiles;
create policy "profiles: eigenes ändern"
    on public.profiles for update to authenticated
    using (id = (select auth.uid()))
    with check (id = (select auth.uid()));

-- drink_entries ----------------------------------------------------------
drop policy if exists "drinks: eigene lesen, Admin alle" on public.drink_entries;
create policy "drinks: eigene lesen, Admin alle"
    on public.drink_entries for select to authenticated
    using (user_id = (select auth.uid()) or (select public.is_admin()));

drop policy if exists "drinks: eigene anlegen" on public.drink_entries;
create policy "drinks: eigene anlegen"
    on public.drink_entries for insert to authenticated
    with check (user_id = (select auth.uid()));

drop policy if exists "drinks: eigene ändern" on public.drink_entries;
create policy "drinks: eigene ändern"
    on public.drink_entries for update to authenticated
    using (user_id = (select auth.uid()))
    with check (user_id = (select auth.uid()));

drop policy if exists "drinks: eigene löschen" on public.drink_entries;
create policy "drinks: eigene löschen"
    on public.drink_entries for delete to authenticated
    using (user_id = (select auth.uid()));


-- -----------------------------------------------------------------------------
-- 4. SPALTE role SCHÜTZEN
-- -----------------------------------------------------------------------------
-- Die Update-Policy erlaubt das Ändern des EIGENEN Profils. Ohne diesen Trigger
-- könnte sich jeder selbst role = 'admin' setzen!
-- auth.uid() ist im SQL Editor und im Table Editor NULL -> dort ist alles erlaubt.
create or replace function public.profiles_schuetzen()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    if auth.uid() is not null and not public.is_admin() then
        if tg_op = 'INSERT' then
            new.role := 'user';
        else
            new.role  := old.role;    -- Rolle bleibt, wie sie war
            new.email := old.email;   -- E-Mail kommt aus dem Login, nicht vom Nutzer
        end if;
    end if;
    return new;
end;
$$;

drop trigger if exists profiles_schuetzen on public.profiles;
create trigger profiles_schuetzen
    before insert or update on public.profiles
    for each row execute function public.profiles_schuetzen();


-- -----------------------------------------------------------------------------
-- 5. PROFIL AUTOMATISCH BEI DER REGISTRIERUNG ANLEGEN
-- -----------------------------------------------------------------------------
-- Die App schickt bei der Registrierung den Namen als "user metadata" mit.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
    insert into public.profiles (id, name, email)
    values (
        new.id,
        coalesce(nullif(new.raw_user_meta_data ->> 'name', ''), split_part(new.email, '@', 1)),
        new.email
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function public.handle_new_user();

-- Für Nutzer, die sich schon VOR diesem Skript registriert haben:
insert into public.profiles (id, name, email)
select id, coalesce(nullif(raw_user_meta_data ->> 'name', ''), split_part(email, '@', 1)), email
from auth.users
on conflict (id) do nothing;


-- -----------------------------------------------------------------------------
-- 6. VIEWS (Ansichten)
-- -----------------------------------------------------------------------------
-- security_invoker = true: die View prüft die RLS-Regeln des ABFRAGENDEN Nutzers.
-- Normale Nutzer sehen also nur ihre eigenen Summen, Admins alle.
-- Tagesgrenze: deutsche Zeit (Europe/Berlin).

-- Summe pro Nutzer und Tag
create or replace view public.daily_totals
with (security_invoker = true) as
select
    user_id,
    (ts at time zone 'Europe/Berlin')::date as tag,
    sum(ml)::integer                         as total_ml,
    count(*)::integer                        as drinks
from public.drink_entries
group by user_id, (ts at time zone 'Europe/Berlin')::date;

-- Admin-Übersicht: jeder Nutzer mit der heutigen Menge (auch 0 ml)
create or replace view public.user_today
with (security_invoker = true) as
select
    p.id,
    p.name,
    p.email,
    p.role,
    p.daily_goal_ml,
    coalesce(t.total_ml, 0) as heute_ml,
    coalesce(t.drinks, 0)   as drinks
from public.profiles p
left join public.daily_totals t
    on t.user_id = p.id
   and t.tag = (now() at time zone 'Europe/Berlin')::date;


-- -----------------------------------------------------------------------------
-- 7. RECHTE
-- -----------------------------------------------------------------------------
-- Eingeloggte Nutzer ("authenticated") dürfen die Tabellen benutzen – WELCHE
-- Zeilen, bestimmen die RLS-Policies oben. Nicht eingeloggte ("anon") dürfen nichts.
grant select, insert, update         on public.profiles      to authenticated;
grant select, insert, update, delete on public.drink_entries to authenticated;
grant select on public.daily_totals, public.user_today to authenticated;
revoke all on public.profiles, public.drink_entries, public.daily_totals, public.user_today from anon;
