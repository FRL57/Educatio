"""Construit la webapp (index.html, manifest, service worker, icônes) à partir de conjugo.html.

conjugo.html reste la source unique : on modifie ce fichier, puis on lance
    python build.py
et on pousse le résultat sur GitHub (Vercel redéploie tout seul).
"""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ICI = Path(__file__).parent
SOURCE = (ICI / "conjugo.html").read_text(encoding="utf-8")

TETE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#f5f7fc" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#10172b" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Conjugo">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">
<style>
  :root { color-scheme: light; -webkit-text-size-adjust: 100%;
    padding: env(safe-area-inset-top, 0px) env(safe-area-inset-right, 0px) env(safe-area-inset-bottom, 0px) env(safe-area-inset-left, 0px); }
  body { margin: 0; }
  [hidden] { display: none !important; }
  button, input, label { touch-action: manipulation; }
  .install { background: var(--accent-soft); color: var(--ink); border-radius: 12px; padding: 12px 14px; font-size: .92rem; display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; }
  .install button { background: none; border: 0; color: var(--accent); font-weight: 700; padding: 0 4px; }
</style>
"""

PIED = """
<script>
  // Hors ligne : enregistre le service worker
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
  // Sur iPhone, dans Safari : explique comment installer l'appli
  (function () {
    const ios = /iphone|ipad|ipod/i.test(navigator.userAgent);
    const installee = window.navigator.standalone || matchMedia('(display-mode: standalone)').matches;
    let vu = false; try { vu = localStorage.getItem('conjugo-install-vu') === '1'; } catch (e) {}
    if (!ios || installee || vu) return;
    const d = document.createElement('div');
    d.className = 'install';
    d.innerHTML = '<span>Pour installer Conjugo sur l\\'iPhone : touche le bouton <b>Partager</b> de Safari, puis <b>Sur l\\'écran d\\'accueil</b>.</span><button type="button" aria-label="Fermer">OK</button>';
    d.querySelector('button').onclick = () => { d.remove(); try { localStorage.setItem('conjugo-install-vu', '1'); } catch (e) {} };
    document.querySelector('.wrap').prepend(d);
  })();
</script>
</body>
</html>
"""

# Tout ce qui précède le contenu (titre, polices, styles) va dans <head>
coupure = SOURCE.index('<div class="wrap">')
index = TETE + SOURCE[:coupure] + "</head>\n<body>\n" + SOURCE[coupure:] + PIED
(ICI / "index.html").write_text(index, encoding="utf-8")

# Icônes : page de cahier bleue, marge rouge, « je » en blanc
(ICI / "icons").mkdir(exist_ok=True)
POLICE = "C:/Windows/Fonts/segoeuib.ttf"


def icone(taille, marge_sure=False):
    img = Image.new("RGB", (taille, taille), "#2c56cf")
    d = ImageDraw.Draw(img)
    pas = taille / 16
    for i in range(1, 16):
        y = round(i * pas)
        d.line([(0, y), (taille, y)], fill="#3d66dc" if i % 4 else "#5277e3", width=max(1, taille // 180))
    x_marge = round(taille * 0.2)
    d.rectangle([x_marge, 0, x_marge + max(2, taille // 60), taille], fill="#ec8f9a")
    echelle = 0.42 if marge_sure else 0.55
    police = ImageFont.truetype(POLICE, round(taille * echelle))
    texte = "je"
    boite = d.textbbox((0, 0), texte, font=police)
    l, h = boite[2] - boite[0], boite[3] - boite[1]
    d.text(((taille - l) / 2 - boite[0] + taille * 0.04, (taille - h) / 2 - boite[1]), texte, font=police, fill="#ffffff")
    return img


icone(180).save(ICI / "icons/apple-touch-icon.png")
icone(192).save(ICI / "icons/icon-192.png")
icone(512).save(ICI / "icons/icon-512.png")
icone(512, marge_sure=True).save(ICI / "icons/icon-maskable-512.png")

manifest = {
    "name": "Conjugo",
    "short_name": "Conjugo",
    "description": "Entraînement à la conjugaison pour la 6e.",
    "lang": "fr",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#f5f7fc",
    "theme_color": "#2c56cf",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
(ICI / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

# Le nom du cache change à chaque version : l'iPhone récupère la mise à jour
version = hashlib.sha1(index.encode("utf-8")).hexdigest()[:10]
sw = (ICI / "sw.template.js").read_text(encoding="utf-8").replace("__VERSION__", version)
(ICI / "sw.js").write_text(sw, encoding="utf-8")
print("Webapp construite, version", version)
