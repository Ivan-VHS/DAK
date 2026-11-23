const CACHE = "mora-shell-v8-bilingual-platform";
const REQUIRED_ASSETS = [
  "./",
  "./index.html",
  "./styles.css",
  "./app.js",
  "./i18n.js",
  "./chrono.js",
  "./platform-contracts.js",
  "./commons-catalog.js",
  "./core.js",
  "./apps.json",
  "./system-policy.json",
  "./theme.json",
  "./manifest.webmanifest",
  "./icon.svg"
];
const SCOPE_PATH = new URL("./", self.location.href).pathname;

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    try {
      await cache.addAll(REQUIRED_ASSETS);
      const checks = await Promise.all(REQUIRED_ASSETS.map((asset) => cache.match(asset)));
      if (checks.some((response) => !response || !response.ok)) {
        throw new Error("The staged Mora shell cache is incomplete.");
      }
    } catch (error) {
      await caches.delete(CACHE);
      throw error;
    }
    self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = (await caches.keys())
      .filter((key) => key.startsWith("mora-shell-"))
      .sort()
      .reverse();
    // Keep the active cache and one known-good predecessor for recovery.
    await Promise.all(keys.slice(2).map((key) => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin ||
      !url.pathname.startsWith(SCOPE_PATH)) return;

  if (request.mode === "navigate") {
    event.respondWith((async () => {
      try {
        return await fetch(request);
      } catch {
        return (await caches.match("./index.html")) ||
          new Response("Mora is not available offline.", {
            status: 503,
            headers: { "Content-Type": "text/plain; charset=utf-8" }
          });
      }
    })());
    return;
  }

  event.respondWith((async () => {
    const cached = await caches.match(request);
    if (cached) {
      event.waitUntil(fetch(request).then(async (response) => {
        if (response.ok && response.type === "basic") {
          const copy = response.clone();
          await (await caches.open(CACHE)).put(request, copy);
        }
      }).catch(() => {}));
      return cached;
    }
    const response = await fetch(request);
    if (response.ok && response.type === "basic") {
      await (await caches.open(CACHE)).put(request, response.clone());
    }
    return response;
  })());
});
