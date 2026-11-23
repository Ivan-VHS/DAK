const CACHE="mora-shell-v1";
const FILES=["./","./index.html","./mora.css","./mora.js","./manifest.webmanifest"];
self.addEventListener("install",e=>{e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)));self.skipWaiting()});
self.addEventListener("activate",e=>{e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))));self.clients.claim()});
self.addEventListener("fetch",e=>{const r=e.request;if(r.method!=="GET"||new URL(r.url).origin!==self.location.origin)return;e.respondWith(caches.match(r).then(c=>c||fetch(r).then(res=>{if(res.ok){const copy=res.clone();caches.open(CACHE).then(cache=>cache.put(r,copy))}return res})))});
