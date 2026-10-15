-- =====================================================================
-- Educatio — étape 4 : supprimer son compte (droit à l'effacement)
-- À coller dans Supabase : SQL Editor → New query → Run.
--
-- L'enfant connecté peut effacer son compte depuis « Mon compte ».
-- On supprime sa ligne dans auth.users : grâce aux « on delete cascade »,
-- son profil, ses séries, ses amitiés, ses défis et ses participations
-- aux défis disparaissent avec. La fonction n'efface jamais que le
-- compte de la personne connectée.
-- =====================================================================

create or replace function public.supprimer_mon_compte()
returns void language plpgsql security definer set search_path = public as $$
declare
  v_moi uuid := auth.uid();
begin
  if v_moi is null then raise exception 'Il faut être connecté'; end if;
  -- Essais de code ami ratés : pas reliés au profil, on les efface à part
  delete from essais_code where user_id = v_moi;
  delete from auth.users where id = v_moi;
end $$;

revoke execute on function public.supprimer_mon_compte() from public, anon;
grant  execute on function public.supprimer_mon_compte() to authenticated;
