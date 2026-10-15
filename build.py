"""Construit la webapp (index.html, manifest, service worker, icônes) à partir de educatio.html.

educatio.html reste la source unique : on modifie ce fichier, puis on lance
    python build.py
et on pousse le résultat sur GitHub (Vercel redéploie tout seul).
"""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ICI = Path(__file__).parent
SOURCE = (ICI / "educatio.html").read_text(encoding="utf-8")

TETE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#eef3ff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#14163a" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Educatio">
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
  .install { background: var(--sun-soft); color: var(--ink); border: 2px solid var(--sun); border-radius: 16px; padding: 12px 14px; font-size: .92rem; display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; }
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
    let vu = false; try { vu = localStorage.getItem('educatio-install-vu') === '1'; } catch (e) {}
    if (!ios || installee || vu) return;
    const d = document.createElement('div');
    d.className = 'install';
    d.innerHTML = '<span>Pour installer Educatio sur l\\'iPhone : touche le bouton <b>Partager</b> de Safari, puis <b>Sur l\\'écran d\\'accueil</b>.</span><button type="button" aria-label="Fermer">OK</button>';
    d.querySelector('button').onclick = () => { d.remove(); try { localStorage.setItem('educatio-install-vu', '1'); } catch (e) {} };
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

# Icônes : dégradé bleu → violet, confettis, « je » en blanc avec le « e » en jaune
(ICI / "icons").mkdir(exist_ok=True)
POLICE = "C:/Windows/Fonts/segoeuib.ttf"
CONFETTIS = [(0.14, 0.16, "#ffd23f"), (0.84, 0.13, "#ef476f"), (0.88, 0.80, "#06d6a0"), (0.12, 0.84, "#ff9f1c"), (0.50, 0.09, "#06d6a0"), (0.90, 0.47, "#ffd23f")]


def icone(taille, marge_sure=False):
    haut, bas = (58, 109, 240), (142, 68, 236)
    img = Image.new("RGB", (taille, taille))
    d = ImageDraw.Draw(img)
    for y in range(taille):
        t = y / (taille - 1)
        d.line([(0, y), (taille, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(haut, bas)))
    if not marge_sure:
        for x, y, c in CONFETTIS:
            r = taille * 0.035
            d.ellipse([x * taille - r, y * taille - r, x * taille + r, y * taille + r], fill=c)
    echelle = 0.44 if marge_sure else 0.56
    police = ImageFont.truetype(POLICE, round(taille * echelle))
    boite = d.textbbox((0, 0), "je", font=police)
    l, h = boite[2] - boite[0], boite[3] - boite[1]
    x0, y0 = (taille - l) / 2 - boite[0], (taille - h) / 2 - boite[1]
    d.text((x0, y0), "j", font=police, fill="#ffffff")
    d.text((x0 + d.textlength("j", font=police), y0), "e", font=police, fill="#ffd23f")
    return img


icone(180).save(ICI / "icons/apple-touch-icon.png")
icone(192).save(ICI / "icons/icon-192.png")
icone(512).save(ICI / "icons/icon-512.png")
icone(512, marge_sure=True).save(ICI / "icons/icon-maskable-512.png")

manifest = {
    "name": "Educatio",
    "short_name": "Educatio",
    "description": "Entraînement à la conjugaison pour la 6e.",
    "lang": "fr",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#eef3ff",
    "theme_color": "#3a6df0",
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
