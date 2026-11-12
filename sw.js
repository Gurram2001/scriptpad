// Network-first for this site's own files, so updates arrive without bumping a version number.
// Offline: falls back to the cached copy. Cloud-sync calls (Supabase) are never cached.
const V='scriptpad-cache';
const CORE=['./','index.html','styles.css','app.js','config.js','manifest.webmanifest','icon.svg'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
 const r=e.request,u=new URL(r.url);
 if(r.method!=='GET'||u.origin!==location.origin||/\/(rest|auth)\/v1\//.test(u.pathname))return;
 e.respondWith(netFirst(r));
});
async function netFirst(r){
 const c=await caches.open(V);
 try{
  const n=await Promise.race([fetch(r,{cache:'no-cache'}),new Promise((_,j)=>setTimeout(j,4000))]);
  if(n&&n.ok)c.put(r,n.clone());
  return n;
 }catch(e){
  return (await c.match(r))||(r.mode==='navigate'?await c.match('index.html'):Response.error());
 }
}
