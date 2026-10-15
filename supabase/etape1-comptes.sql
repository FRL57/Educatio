-- =====================================================================
-- Educatio — étape 1 : comptes et progression en ligne
-- À coller dans Supabase : SQL Editor → New query → Run.
--
-- Principe de sécurité : chaque enfant ne lit que ses propres données
-- (Row Level Security). Les écritures passent par des fonctions qui
-- vérifient qui est connecté. Les autres ne verront que le pseudo,
-- et seulement quand le suivi entre amis existera (étape 2).
-- =====================================================================

-- Profil public minimal + compteurs de progression
create table public.profils (
  id            uuid primary key references auth.users on delete cascade,
  pseudo        text not null check (pseudo ~ '^[A-Za-z0-9_-]{3,20}$'),
  code_ami      text not null unique,
  series_jouees integer not null default 0,
  reponses      integer not null default 0,
  bonnes        integer not null default 0,
  record        integer not null default 0,
  fautes        jsonb   not null default '{}'::jsonb,   -- verbes ratés, pour les faire revenir plus souvent
  cree_le       timestamptz not null default now()
);
create unique index profils_pseudo_unique on public.profils (lower(pseudo));

-- Une ligne par série terminée
create table public.series (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references public.profils on delete cascade,
  temps      text[]  not null,
  exceptions boolean not null default false,
  score      integer not null,
  longueur   integer not null,
  erreurs    jsonb   not null default '[]'::jsonb,
  joue_le    timestamptz not null default now()
);
create index series_par_joueur on public.series (user_id, joue_le desc);

alter table public.profils enable row level security;
alter table public.series  enable row level security;

create policy "Je vois mon profil" on public.profils
  for select to authenticated using (auth.uid() = id);
create policy "Je vois mes séries" on public.series
  for select to authenticated using (auth.uid() = user_id);
-- Pas de politique d'écriture : on écrit uniquement via les fonctions ci-dessous.

-- Code ami : 6 caractères faciles à lire (pas de 0/O ni de 1/I)
create or replace function public.code_ami_aleatoire()
returns text language sql volatile as $$
  select string_agg(substr('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', 1 + floor(random() * 32)::int, 1), '')
  from generate_series(1, 6)
$$;

-- À l'inscription, crée le profil avec le pseudo choisi
create or replace function public.nouveau_profil()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  c text;
begin
  loop
    c := public.code_ami_aleatoire();
    exit when not exists (select 1 from public.profils where code_ami = c);
  end loop;
  insert into public.profils (id, pseudo, code_ami)
  values (new.id, new.raw_user_meta_data ->> 'pseudo', c);
  return new;
end $$;

create trigger apres_inscription
  after insert on auth.users
  for each row execute function public.nouveau_profil();

-- Le pseudo est-il libre ? (appelé avant l'inscription)
create or replace function public.pseudo_disponible(p text)
returns boolean language sql stable security definer set search_path = public as $$
  select not exists (select 1 from public.profils where lower(pseudo) = lower(p))
$$;
grant execute on function public.pseudo_disponible(text) to anon, authenticated;

-- Enregistre une série terminée et met à jour les compteurs du profil
create or replace function public.enregistrer_serie(
  p_temps text[], p_exceptions boolean, p_score integer, p_longueur integer,
  p_record integer, p_erreurs jsonb, p_fautes jsonb)
returns void language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then
    raise exception 'Il faut être connecté';
  end if;
  if p_longueur < 1 or p_longueur > 50 or p_score < 0 or p_score > p_longueur then
    raise exception 'Série invalide';
  end if;
  insert into public.series (user_id, temps, exceptions, score, longueur, erreurs)
  values (auth.uid(), p_temps, coalesce(p_exceptions, false), p_score, p_longueur, coalesce(p_erreurs, '[]'::jsonb));
  update public.profils set
    series_jouees = series_jouees + 1,
    reponses      = reponses + p_longueur,
    bonnes        = bonnes + p_score,
    record        = greatest(record, least(coalesce(p_record, 0), 1000)),
    fautes        = coalesce(p_fautes, fautes)
  where id = auth.uid();
end $$;
revoke execute on function public.enregistrer_serie(text[], boolean, integer, integer, integer, jsonb, jsonb) from public, anon;
grant  execute on function public.enregistrer_serie(text[], boolean, integer, integer, integer, jsonb, jsonb) to authenticated;
