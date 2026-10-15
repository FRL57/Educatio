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

# Comptes en ligne : l'adresse du projet Supabase et sa clé publique (« anon »), si elles existent.
# Cette clé est faite pour être visible dans une page web ; la sécurité vient des règles de la base.
CONFIG = ICI / "supabase.json"
if CONFIG.exists():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    vide = "const SUPABASE_URL = '', SUPABASE_CLE = '';"
    assert vide in SOURCE, "configuration Supabase introuvable dans educatio.html"
    SOURCE = SOURCE.replace(vide, f"const SUPABASE_URL = {json.dumps(cfg['url'])}, SUPABASE_CLE = {json.dumps(cfg['cle'])};")

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

# Icônes : dégradé bleu → violet, grand « E » d'Educatio en blanc,
# souligné des 6 couleurs des personnes (je, tu, il, nous, vous, ils) comme dans l'appli
(ICI / "icons").mkdir(exist_ok=True)
POLICE = "C:/Windows/Fonts/seguibl.ttf"
COULEURS_PERSONNES = ["#ef476f", "#ff9f1c", "#ffd23f", "#06d6a0", "#4cc9f0", "#c77dff"]
CONFETTIS = [(0.16, 0.17, "#ffd23f"), (0.85, 0.15, "#ef476f"), (0.86, 0.62, "#06d6a0"), (0.14, 0.60, "#ff9f1c")]


def icone(taille, marge_sure=False):
    T = taille * 4  # dessin en grand puis réduit : bords lisses
    haut, bas = (58, 109, 240), (142, 68, 236)
    img = Image.new("RGB", (T, T))
    d = ImageDraw.Draw(img)
    for y in range(T):
        t = y / (T - 1)
        d.line([(0, y), (T, y)], fill=tuple(round(a + (b - a) * t) for a, b in zip(haut, bas)))
    k = 0.8 if marge_sure else 1.0  # icône « maskable » : tout tient dans la zone centrale
    if not marge_sure:
        for x, y, c in CONFETTIS:
            r = T * 0.03
            d.ellipse([x * T - r, y * T - r, x * T + r, y * T + r], fill=c)
    police = ImageFont.truetype(POLICE, round(T * 0.58 * k))
    boite = d.textbbox((0, 0), "E", font=police)
    l, h = boite[2] - boite[0], boite[3] - boite[1]
    barre_h, ecart = T * 0.075 * k, T * 0.06 * k
    total = h + ecart + barre_h
    x0, y0 = (T - l) / 2 - boite[0], (T - total) / 2 - boite[1]
    d.text((x0, y0), "E", font=police, fill="#ffffff")
    # six petites barres de couleur sous la lettre
    yb = (T - total) / 2 + h + ecart
    largeur = T * 0.62 * k
    pas = largeur / 6
    xb = (T - largeur) / 2
    for i, c in enumerate(COULEURS_PERSONNES):
        d.rounded_rectangle([xb + i * pas + pas * 0.08, yb, xb + (i + 1) * pas - pas * 0.08, yb + barre_h], radius=barre_h / 2, fill=c)
    return img.resize((taille, taille), Image.LANCZOS)


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
