// Service Worker — caches the app shell for offline use.
// Bump the version string any time you deploy an update.
const VERSION = 'purpose-app-v7';
const PHOTO_CACHE = 'purpose-photos-v1';
const SHELL = [
  './',
  './index.html',
  './manifest.json',
  './content.json'
];

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(VERSION).then(function (cache) {
      return cache.addAll(SHELL);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', function (event) {
  // Remove old caches on update (keep the current shell + photo caches)
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.filter(function (k) { return k !== VERSION && k !== PHOTO_CACHE; })
            .map(function (k) { return caches.delete(k); })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', function (event) {
  // Network-first for navigations, cache-first for assets
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(function () {
        return caches.match('./index.html');
      })
    );
    return;
  }

  // Photos: stale-while-revalidate. Serve instantly from cache on repeat
  // visits, refresh in the background so CMS updates still come through.
  if (/\/photos\//.test(event.request.url)) {
    event.respondWith(
      caches.open(PHOTO_CACHE).then(function (cache) {
        return cache.match(event.request).then(function (cached) {
          var network = fetch(event.request).then(function (res) {
            if (res && res.ok) cache.put(event.request, res.clone());
            return res;
          }).catch(function () { return cached; });
          return cached || network;
        });
      })
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(function (cached) {
      return cached || fetch(event.request);
    })
  );
});
