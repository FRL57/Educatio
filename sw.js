// Service worker d'Educatio : l'appli marche aussi sans connexion.
// Fichier généré par build.py à partir de sw.template.js : ne pas modifier sw.js à la main.
const CACHE = 'educatio-27a684162d';
const FICHIERS = ['./', 'index.html', 'manifest.webmanifest', 'icons/apple-touch-icon.png', 'icons/icon-192.png', 'icons/icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FICHIERS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(cles => Promise.all(cles.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  // Polices Google et bibliothèque Supabase : depuis le cache d'abord
  if (url.hostname.endsWith('fonts.googleapis.com') || url.hostname.endsWith('fonts.gstatic.com') || url.hostname === 'cdn.jsdelivr.net') {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request).then(rep => {
      const copie = rep.clone();
      caches.open(CACHE).then(c => c.put(e.request, copie));
      return rep;
    })));
    return;
  }
  if (url.origin !== location.origin) return;
  // Fichiers de l'appli : réseau d'abord (pour avoir la dernière version), cache si hors ligne
  e.respondWith(fetch(e.request).then(rep => {
    const copie = rep.clone();
    caches.open(CACHE).then(c => c.put(e.request, copie));
    return rep;
  }).catch(() => caches.match(e.request).then(r => r || caches.match('index.html'))));
});
