/* Offline app shell and notification-click deep links. No background alarm claim. */
const PREFIX='offline-local-life-planner-',CACHE=PREFIX+'v5';const SHELL=['./','./index.html','./styles.css','./model.js','./config.js','./app.js','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png'];
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith(PREFIX)&&k!==CACHE).map(k=>caches.delete(k)))),self.clients.claim()])));
self.addEventListener('fetch',event=>{if(event.request.method!=='GET'||new URL(event.request.url).origin!==self.location.origin)return;
if(event.request.mode==='navigate'){event.respondWith(fetch(event.request).catch(()=>caches.match('./index.html')));return}
event.respondWith(caches.match(event.request).then(hit=>hit||fetch(event.request)));});
self.addEventListener('notificationclick',event=>{event.notification.close();const target=event.notification.data?.url||new URL('./index.html',self.location.href).href;
event.waitUntil((async()=>{const windows=await self.clients.matchAll({type:'window',includeUncontrolled:true});const preferred=windows.find(w=>new URL(w.url).pathname===new URL(target).pathname);if(preferred){try{await preferred.focus();preferred.postMessage({type:'OPEN_ITEM',url:target});return}catch(e){}}if(self.clients.openWindow)await self.clients.openWindow(target)})());});
