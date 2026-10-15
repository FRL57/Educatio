-- =====================================================================
-- Educatio — se connecter avec son pseudo (en plus de l'e-mail)
-- À coller dans Supabase : SQL Editor → New query → Run.
--
-- Les comptes Supabase se connectent avec un e-mail. Cette fonction
-- retrouve l'e-mail à partir du pseudo, mais SEULEMENT si le mot de
-- passe est le bon : personne ne peut découvrir l'e-mail d'un autre
-- enfant en connaissant juste son pseudo. Après 5 essais ratés sur un
-- pseudo, il faut attendre 15 minutes (contre les essais au hasard).
-- =====================================================================

create table public.essais_connexion (
  pseudo   text not null,
  essai_le timestamptz not null default now()
);
create index essais_par_pseudo on public.essais_connexion (pseudo, essai_le);
-- Aucune politique : la table est invisible depuis l'appli.
alter table public.essais_connexion enable row level security;

create or replace function public.email_pour_connexion(p_pseudo text, p_mdp text)
returns text language plpgsql security definer set search_path = public, extensions as $$
declare
  v_email text;
  v_hash  text;
begin
  delete from essais_connexion where essai_le < now() - interval '1 day';
  if (select count(*) from essais_connexion
      where pseudo = lower(p_pseudo) and essai_le > now() - interval '15 minutes') >= 5 then
    raise exception 'trop_essais';
  end if;

  select u.email, u.encrypted_password into v_email, v_hash
  from profils p join auth.users u on u.id = p.id
  where lower(p.pseudo) = lower(p_pseudo);

  if v_hash is not null and v_hash = extensions.crypt(p_mdp, v_hash) then
    delete from essais_connexion where pseudo = lower(p_pseudo);
    return v_email;
  end if;

  insert into essais_connexion (pseudo) values (lower(p_pseudo));
  return null;
end $$;

revoke execute on function public.email_pour_connexion(text, text) from public;
grant  execute on function public.email_pour_connexion(text, text) to anon, authenticated;
