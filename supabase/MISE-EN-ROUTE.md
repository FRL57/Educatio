# Mettre en route les comptes Educatio (Supabase)

1. **Créer le projet** sur https://supabase.com → *New project*.
   Nom : `educatio`. Région : *West EU (Paris)*. Notez le mot de passe de la base quelque part.
2. **Créer les tables** : *SQL Editor* → *New query* → coller tout le fichier `etape1-comptes.sql` → *Run*.
3. **Adresse du site** : *Authentication* → *URL Configuration*.
   - *Site URL* : l'adresse Vercel de l'appli (ex. `https://educatio-xxxx.vercel.app`).
   - *Redirect URLs* : ajouter la même adresse.
4. **E-mails** : par défaut, Supabase n'envoie des e-mails qu'aux membres de votre équipe Supabase.
   - Pour démarrer : *Authentication* → *Sign In / Providers* → *Email* → désactiver **Confirm email**.
     L'inscription marche alors sans e-mail de confirmation.
   - Pour que « Mot de passe oublié » marche pour tout le monde : brancher un service d'envoi gratuit
     (Brevo, Resend…) dans *Authentication* → *Emails* → *SMTP Settings*.
5. **Donner à Claude** : *Project Settings* → *API Keys* :
   - l'adresse du projet (*Project URL*, `https://….supabase.co`) ;
   - la clé publique **anon / publishable** (jamais la clé `service_role` ou *secret*).

Claude les met dans `supabase.json`, lance `python build.py` et pousse sur GitHub.
