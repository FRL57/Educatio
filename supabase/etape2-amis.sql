-- =====================================================================
-- Educatio — étape 2 : se faire des amis avec le code ami
-- À coller dans Supabase : SQL Editor → New query → Run.
--
-- Un enfant envoie une demande avec le code ami d'un copain ; le copain
-- l'accepte ou la refuse. Une fois amis, chacun voit le pseudo et les
-- scores de l'autre (jamais son e-mail). Tout passe par des fonctions qui
-- vérifient qui est connecté. Après 10 codes faux en une heure, il faut
-- attendre (contre les essais au hasard).
-- =====================================================================

create table public.amities (
  id           bigint generated always as identity primary key,
  demandeur    uuid not null references public.profils on delete cascade,
  destinataire uuid not null references public.profils on delete cascade,
  statut       text not null default 'attente' check (statut in ('attente', 'acceptee')),
  cree_le      timestamptz not null default now(),
  check (demandeur <> destinataire)
);
-- Un seul lien par paire d'enfants, dans un sens ou dans l'autre
create unique index amities_paire on public.amities (least(demandeur, destinataire), greatest(demandeur, destinataire));
alter table public.amities enable row level security;
create policy "Je vois mes amitiés" on public.amities
  for select to authenticated using (auth.uid() in (demandeur, destinataire));

create table public.essais_code (
  user_id  uuid not null,
  essai_le timestamptz not null default now()
);
alter table public.essais_code enable row level security; -- invisible depuis l'appli

-- Envoie une demande. Renvoie « etat:pseudo », par exemple « envoyee:Leo_12 ».
create or replace function public.demander_ami(p_code text)
returns text language plpgsql security definer set search_path = public as $$
declare
  v_moi    uuid := auth.uid();
  v_ami    uuid;
  v_pseudo text;
  v_lien   public.amities%rowtype;
begin
  if v_moi is null then raise exception 'Il faut être connecté'; end if;
  delete from essais_code where essai_le < now() - interval '1 day';
  if (select count(*) from essais_code where user_id = v_moi and essai_le > now() - interval '1 hour') >= 10 then
    return 'trop_essais:';
  end if;

  select id, pseudo into v_ami, v_pseudo from profils where code_ami = upper(trim(p_code));
  if v_ami is null then
    insert into essais_code (user_id) values (v_moi);
    return 'introuvable:';
  end if;
  if v_ami = v_moi then return 'soi_meme:'; end if;

  select * into v_lien from amities
  where least(demandeur, destinataire) = least(v_moi, v_ami)
    and greatest(demandeur, destinataire) = greatest(v_moi, v_ami);
  if found then
    if v_lien.statut = 'acceptee' then return 'deja_amis:' || v_pseudo; end if;
    if v_lien.destinataire = v_moi then
      -- Il m'avait déjà demandé : on devient amis tout de suite
      update amities set statut = 'acceptee' where id = v_lien.id;
      return 'acceptee:' || v_pseudo;
    end if;
    return 'deja_demandee:' || v_pseudo;
  end if;

  insert into amities (demandeur, destinataire) values (v_moi, v_ami);
  return 'envoyee:' || v_pseudo;
end $$;

-- Accepter ou refuser une demande reçue
create or replace function public.repondre_ami(p_lien bigint, p_accepter boolean)
returns void language plpgsql security definer set search_path = public as $$
begin
  if p_accepter then
    update amities set statut = 'acceptee' where id = p_lien and destinataire = auth.uid() and statut = 'attente';
  else
    delete from amities where id = p_lien and destinataire = auth.uid() and statut = 'attente';
  end if;
end $$;

-- Retirer un ami, ou annuler une demande envoyée
create or replace function public.retirer_ami(p_lien bigint)
returns void language sql security definer set search_path = public as $$
  delete from amities where id = p_lien and auth.uid() in (demandeur, destinataire);
$$;

-- Mes amis et mes demandes ; les scores ne sont donnés que pour les amis acceptés
create or replace function public.mes_amis()
returns table (lien bigint, ami uuid, pseudo text, etat text, series_jouees integer, reponses integer,
               bonnes integer, record integer, derniere_serie timestamptz, series_7j integer)
language sql stable security definer set search_path = public as $$
  select a.id, p.id, p.pseudo,
    case when a.statut = 'acceptee' then 'ami' when a.destinataire = auth.uid() then 'recue' else 'envoyee' end,
    case when a.statut = 'acceptee' then p.series_jouees end,
    case when a.statut = 'acceptee' then p.reponses end,
    case when a.statut = 'acceptee' then p.bonnes end,
    case when a.statut = 'acceptee' then p.record end,
    case when a.statut = 'acceptee' then (select max(s.joue_le) from series s where s.user_id = p.id) end,
    case when a.statut = 'acceptee' then (select count(*)::int from series s where s.user_id = p.id and s.joue_le > now() - interval '7 days') end
  from amities a
  join profils p on p.id = case when a.demandeur = auth.uid() then a.destinataire else a.demandeur end
  where auth.uid() in (a.demandeur, a.destinataire)
  order by lower(p.pseudo)
$$;

-- Les 10 dernières séries d'un ami (seulement si on est amis)
create or replace function public.series_ami(p_ami uuid)
returns table (temps text[], exceptions boolean, score integer, longueur integer, joue_le timestamptz)
language sql stable security definer set search_path = public as $$
  select s.temps, s.exceptions, s.score, s.longueur, s.joue_le
  from series s
  where s.user_id = p_ami
    and exists (select 1 from amities a where a.statut = 'acceptee'
                and ((a.demandeur = auth.uid() and a.destinataire = p_ami) or (a.destinataire = auth.uid() and a.demandeur = p_ami)))
  order by s.joue_le desc
  limit 10
$$;

revoke execute on function public.demander_ami(text), public.repondre_ami(bigint, boolean), public.retirer_ami(bigint),
  public.mes_amis(), public.series_ami(uuid) from public, anon;
grant execute on function public.demander_ami(text), public.repondre_ami(bigint, boolean), public.retirer_ami(bigint),
  public.mes_amis(), public.series_ami(uuid) to authenticated;
