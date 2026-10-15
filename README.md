# Educatio

Entraînement à la conjugaison pour la 6e, installable sur iPhone comme une appli (webapp).

## Modifier l'appli

1. Modifier `educatio.html` (c'est la source unique).
2. Lancer `python build.py` : cela régénère `index.html`, `sw.js`, le manifeste et les icônes.
3. Committer et pousser sur GitHub : Vercel redéploie tout seul.

## Installer sur l'iPhone

Ouvrir l'adresse Vercel dans **Safari**, toucher **Partager**, puis **Sur l'écran d'accueil**.
L'appli fonctionne ensuite aussi sans connexion.
