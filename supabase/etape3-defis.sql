-- =====================================================================
-- Educatio — étape 3 : les défis entre amis
-- À coller dans Supabase : SQL Editor → New query → Run.
--
-- Un enfant crée un défi (une série de questions fixée) pour un ou
-- plusieurs amis. Chacun la joue une seule fois ; on compare le score,
-- puis le temps. On ne voit les scores des autres qu'après avoir joué.
-- Un défi dure 7 jours. Tout passe par des fonctions qui vérifient qui
-- est connecté et qu'on ne défie que des amis acceptés.
-- =====================================================================

create table public.defis (
  id        bigint generated always as identity primary key,
  createur  uuid not null references public.profils on delete cascade,
  questions jsonb not null,          -- [{ v: verbe, p: personne, t: temps, s: sujet, g: genre, n: nom ? }]
  temps     text[] not null,
  cree_le   timestamptz not null default now(),
  expire_le timestamptz not null default now() + interval '7 days'
);
create table public.defi_joueurs (
  defi_id  bigint not null references public.defis on delete cascade,
  user_id  uuid   not null references public.profils on delete cascade,
  score    integer,                  -- vide tant que l'enfant n'a pas joué
  longueur integer,
  duree    integer,                  -- en secondes
  joue_le  timestamptz,
  primary key (defi_id, user_id)
);
create index defi_joueurs_par_joueur on public.defi_joueurs (user_id);
-- Aucune politique : ces tables ne se lisent et ne s'écrivent que par les fonctions ci-dessous.
alter table public.defis        enable row level security;
alter table public.defi_joueurs enable row level security;

create or replace function public.creer_defi(p_questions jsonb, p_temps text[], p_amis uuid[])
returns bigint language plpgsql security definer set search_path = public as $$
declare
  v_moi uuid := auth.uid();
  v_id  bigint;
  v_ami uuid;
begin
  if v_moi is null then raise exception 'Il faut être connecté'; end if;
  if jsonb_typeof(p_questions) <> 'array' or jsonb_array_length(p_questions) not between 1 and 20 then
    raise exception 'Défi invalide';
  end if;
  if coalesce(array_length(p_amis, 1), 0) not between 1 and 10 then raise exception 'choix_amis'; end if;
  if (select count(*) from defis where createur = v_moi and cree_le > now() - interval '1 day') >= 20 then
    raise exception 'trop_defis';
  end if;
  foreach v_ami in array p_amis loop
    if not exists (select 1 from amities where statut = 'acceptee'
                   and ((demandeur = v_moi and destinataire = v_ami) or (destinataire = v_moi and demandeur = v_ami))) then
      raise exception 'pas_ami';
    end if;
  end loop;
  insert into defis (createur, questions, temps) values (v_moi, p_questions, p_temps) returning id into v_id;
  insert into defi_joueurs (defi_id, user_id)
  select v_id, x from unnest(array_append(p_amis, v_moi)) as x
  on conflict do nothing;
  return v_id;
end $$;

-- Enregistre le résultat, une seule fois par joueur
create or replace function public.enregistrer_defi(p_defi bigint, p_score integer, p_duree integer)
returns void language plpgsql security definer set search_path = public as $$
declare
  v_n integer;
begin
  select jsonb_array_length(questions) into v_n from defis where id = p_defi and expire_le > now();
  if v_n is null then raise exception 'defi_termine'; end if;
  if p_score < 0 or p_score > v_n then raise exception 'Score invalide'; end if;
  update defi_joueurs
  set score = p_score, longueur = v_n, duree = least(greatest(coalesce(p_duree, 0), 0), 86400), joue_le = now()
  where defi_id = p_defi and user_id = auth.uid() and score is null;
  if not found then raise exception 'deja_joue'; end if;
end $$;

-- Mes défis des 30 derniers jours, avec le classement
create or replace function public.mes_defis()
returns table (defi bigint, createur text, est_createur boolean, cree_le timestamptz, expire_le timestamptz,
               temps text[], questions jsonb, mon_score integer, joueurs jsonb)
language sql stable security definer set search_path = public as $$
  select d.id, pc.pseudo, d.createur = auth.uid(), d.cree_le, d.expire_le, d.temps, d.questions, moi.score,
    (select jsonb_agg(jsonb_build_object(
        'pseudo', p.pseudo,
        'moi',    j.user_id = auth.uid(),
        'a_joue', j.score is not null,
        'score',  case when moi.score is not null then j.score end,
        'duree',  case when moi.score is not null then j.duree end)
      order by j.score desc nulls last, j.duree asc nulls last, lower(p.pseudo))
     from defi_joueurs j join profils p on p.id = j.user_id
     where j.defi_id = d.id)
  from defis d
  join defi_joueurs moi on moi.defi_id = d.id and moi.user_id = auth.uid()
  join profils pc on pc.id = d.createur
  where d.cree_le > now() - interval '30 days'
  order by d.cree_le desc
$$;

revoke execute on function public.creer_defi(jsonb, text[], uuid[]), public.enregistrer_defi(bigint, integer, integer),
  public.mes_defis() from public, anon;
grant execute on function public.creer_defi(jsonb, text[], uuid[]), public.enregistrer_defi(bigint, integer, integer),
  public.mes_defis() to authenticated;
