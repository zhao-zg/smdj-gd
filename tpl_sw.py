# -*- coding: utf-8 -*-
"""Service Worker 注册 JS + SW 模板 + 离线页 + 图标"""

# ================== SW 注册 (多候选探测) ==================

SW_REGISTER_JS = r"""
(function(){
  if(localStorage.getItem('disableSW')==='1'){
    console.log('[SW] disabled by user flag');
    return;
  }
  if(!('serviceWorker' in navigator)) return;

  const CANDIDATES = [
    '/sw.js?v=7.3.0',
    './sw.js?v=7.3.0',
    '../sw.js?v=7.3.0'
  ];

  async function probe(url){
    try{
      const res = await fetch(url,{cache:'no-store',method:'GET'});
      if(!res.ok) throw new Error('status '+res.status);
      const ct=(res.headers.get('content-type')||'').toLowerCase();
      if(ct.includes('text/html')) throw new Error('html fallback');
      return true;
    }catch(e){
      console.warn('[SW] probe fail',url,e.message);return false;
    }
  }

  async function tryRegister(){
    for(const p of CANDIDATES){
      const ok = await probe(new URL(p,location.href));
      if(!ok) continue;
      try{
        const reg = await navigator.serviceWorker.register(p);
        console.log('[SW] registered',p,'scope:',reg.scope);
        return;
      }catch(e){
        console.warn('[SW] register fail',p,e);
      }
    }
    console.warn('[SW] all candidates failed');
  }

  function start(){ if('requestIdleCallback' in window) requestIdleCallback(tryRegister); else setTimeout(tryRegister,200); }
  window.addEventListener('load',start);
})();
"""

# ================== Service Worker 模板 (延迟后台刷新) ==================

SERVICE_WORKER_JS_NEW = r"""
/* Service Worker – full-site precache after install */
const VERSION = /*__SW_VERSION__*/;
const DEBUG   = false;

const STATIC_CACHE = 'static-' + VERSION;
const PAGE_CACHE   = 'pages-'  + VERSION;
const OTHER_CACHE  = 'other-'  + VERSION;

const CORE_ASSETS = [
  './',
  './offline.htm',
  './manifest.json',
  './manifest.webmanifest',
  './assets/css/core.css',
  './assets/css/themes.css',
  './assets/css/extra.css',
  './assets/js/reader.js',
  './assets/js/tts.js',
  './assets/js/app-update.js',
  './assets/js/sw-register.js'
];

const PAGE_LIST = /*__PAGE_DIRS__*/;
const ALL_ASSETS = /*__ALL_ASSETS__*/;

const NAV_TIMEOUT     = 15000;
const RESCAN_INTERVAL = 1000 * 60 * 60;
const ACTIVATION_DELAY = 3000;
const BATCH_SIZE = 5;
const BATCH_DELAY = 1000;

function log(...a){ if(DEBUG) console.log('[SW]',...a); }
function isHTMLResponse(res){
  if(!res)return false;
  const ct=(res.headers.get('content-type')||'').toLowerCase();
  return ct.includes('text/html');
}
async function networkFetchWithTimeout(req){
  const c=new AbortController();const t=setTimeout(()=>c.abort(),NAV_TIMEOUT);
  try{const r=await fetch(req,{signal:c.signal});clearTimeout(t);return r;}catch(e){clearTimeout(t);throw e;}
}
function uniqueList(list){ return [...new Set(list.filter(Boolean))]; }
function normalizeAssetPath(path){
  if(!path) return '';
  if(path === './' || path === '/') return './';
  const p=String(path).trim().replace(/^\/+/, '');
  const norm = p.startsWith('./') ? p : ('./' + p);
  if(norm === './index.html') return './';
  return norm;
}
function classifyAsset(path){
  const p=normalizeAssetPath(path).toLowerCase();
  if(!p) return 'static';
  if(p==='./') return 'page';
  if(p.endsWith('.apk')) return 'skip';
  if(/\/(?:page_\d{4}\.htm)$/.test(p) || /^\.\/page_\d{4}\.htm$/.test(p)) return 'page';
  if(p.endsWith('/index.html') || p === './index.html' || p === './' || p.endsWith('.htm')) return 'page';
  if(/\.(css|js|woff2?|ttf|otf|json|webmanifest|map)$/i.test(p)) return 'static';
  if(/\.(png|jpe?g|gif|webp|svg|avif|ico)$/i.test(p)) return 'other';
  return 'other';
}
async function precacheTo(cacheName, assets){
  const cache=await caches.open(cacheName);
  let okCount=0;
  const normalized=uniqueList(assets.map(normalizeAssetPath)).filter(a=>a && classifyAsset(a)!=='skip');
  const BATCH=8;
  for(let i=0;i<normalized.length;i+=BATCH){
    const batch=normalized.slice(i,i+BATCH);
    await Promise.all(batch.map(async asset=>{
      try{
        const res=await fetch(new Request(asset,{cache:'no-store'}));
        if(res && res.ok){
          /* 用绝对 URL 字符串作 key，保证 cache.match 时一致 */
          const absUrl=new URL(asset,self.location.href).href;
          await cache.put(absUrl,res.clone());okCount++;
        }
      }catch(_){}
    }));
  }
  return okCount;
}
function splitPrecacheTargets(){
  const pageTargets=[];
  const staticTargets=[];
  const otherTargets=[];

  const pageCandidates=['./', './offline.htm', ...PAGE_LIST.map(p=>'./'+p)];
  const allCandidates=[...CORE_ASSETS,...ALL_ASSETS];

  for(const path of uniqueList([...pageCandidates,...allCandidates])){
    const cls=classifyAsset(path);
    const normalized=normalizeAssetPath(path);
    if(!normalized || cls==='skip') continue;
    if(cls==='page') pageTargets.push(normalized);
    else if(cls==='static') staticTargets.push(normalized);
    else otherTargets.push(normalized);
  }

  return {
    pageTargets: uniqueList(pageTargets),
    staticTargets: uniqueList(staticTargets),
    otherTargets: uniqueList(otherTargets),
  };
}
async function fullPrecache(reason){
  const targets=splitPrecacheTargets();
  const [pc,sc,oc]=await Promise.all([
    precacheTo(PAGE_CACHE,targets.pageTargets),
    precacheTo(STATIC_CACHE,targets.staticTargets),
    precacheTo(OTHER_CACHE,targets.otherTargets),
  ]);
  log('fullPrecache',reason,{page:pc,stat:sc,other:oc});
}
function normalizePagePath(pathname){
  pathname=pathname.replace(/\/index\.html?$/,'/');
  if(/\/page_\d{4}\.htm$/.test(pathname)) return pathname;
  if(/\/page_\d{4}$/.test(pathname)) pathname+='/';
  return pathname;
}
async function putPageCache(key,res){
  if(res && res.ok && isHTMLResponse(res)){
    const cache=await caches.open(PAGE_CACHE);
    const req=(typeof key==='string')?new Request(key):key;
    cache.put(req,res.clone());
  }
}
async function handleNavigation(event){
  const request=event.request;
  const url=new URL(request.url);
  const normalizedPath=normalizePagePath(url.pathname);
  const normalizedURL=url.origin+normalizedPath;
  try{
    const preload=await event.preloadResponse;
    if(preload && preload.ok){
      putPageCache(normalizedURL,preload).catch(()=>{});
      return preload;
    }
  }catch(_){}
  const pageCache=await caches.open(PAGE_CACHE);
  const cached=await pageCache.match(normalizedURL) || await pageCache.match(request);
  if(cached){
    log('nav cache hit',normalizedPath);
    return cached;
  }
  try{
    const netReq=new Request(normalizedURL,{credentials:request.credentials});
    const res=await networkFetchWithTimeout(netReq);
    if(res && res.ok){
      await putPageCache(normalizedURL,res);
      return res;
    }
  }catch(e){
    log('nav fail',e);
  }
  return (await caches.match('./offline')) ||
         (await caches.match('./offline.htm')) ||
         new Response('<h1>Offline</h1>',{status:503,headers:{'Content-Type':'text/html'}});
}
async function cacheFirstRevalidate(req,cacheName){
  const cache=await caches.open(cacheName);
  /* 统一用绝对 URL 字符串查询，与 precacheTo 存储方式一致 */
  const absUrl=new URL(req.url,self.location.href).href;
  const cached=await cache.match(absUrl);
  const fetchPromise=fetch(req).then(r=>{
    if(r && r.ok) cache.put(absUrl,r.clone());
    return r;
  }).catch(()=>null);
  if(cached){
    fetchPromise.catch(()=>{});
    return cached;
  }
  const net=await fetchPromise;
  return net || new Response('/* unavailable */',{status:503});
}
self.addEventListener('install',e=>{
  e.waitUntil((async()=>{
    await fullPrecache('install');
  })());
  self.skipWaiting();
});
self.addEventListener('activate',e=>{
  e.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(k=>![STATIC_CACHE,PAGE_CACHE,OTHER_CACHE].includes(k)).map(k=>caches.delete(k)));
    if(self.registration.navigationPreload){
      try{await self.registration.navigationPreload.enable();}catch(_){}
    }
    await fullPrecache('activate');
    setTimeout(()=>{backgroundRescan().catch(err=>log('initial rescan err',err));},ACTIVATION_DELAY);
  })());
  self.clients.claim();
});
self.addEventListener('fetch',e=>{
  const req=e.request;
  const url=new URL(req.url);
  if(url.origin!==location.origin) return;
  if(req.mode==='navigate'){
    e.respondWith(handleNavigation(e));
    return;
  }
  if(req.method!=='GET') return;
  if(/\.(css|js|woff2?|ttf|otf)$/.test(url.pathname)){
    e.respondWith(cacheFirstRevalidate(req,STATIC_CACHE));return;
  }
  if(/\.(png|jpe?g|gif|webp|svg|avif)$/.test(url.pathname)){
    e.respondWith(cacheFirstRevalidate(req,OTHER_CACHE));return;
  }
  e.respondWith((async()=>{
    try{
      const r=await fetch(req);
      if(r && r.ok){
        const oc=await caches.open(OTHER_CACHE);
        oc.put(req,r.clone());
      }
      return r;
    }catch(_){
      const oc=await caches.open(OTHER_CACHE);
      const hit=await oc.match(req);
      return hit||new Response('/* offline */',{status:503});
    }
  })());
});
async function backgroundRescan(){
  log('backgroundRescan start', PAGE_LIST.length);
  const pc=await caches.open(PAGE_CACHE);
  for(let i=0;i<PAGE_LIST.length;i+=BATCH_SIZE){
    const slice=PAGE_LIST.slice(i,i+BATCH_SIZE);
    await Promise.all(slice.map(async p=>{
      const url='./'+p;
      try{
        const r=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(10000)});
        if(r.ok && isHTMLResponse(r)){
          pc.put(url,r.clone());
          log('refreshed',url);
        }
      }catch(_){}
    }));
    if(i+BATCH_SIZE<PAGE_LIST.length){
      await new Promise(r=>setTimeout(r,BATCH_DELAY));
    }
  }
  // Keep non-page assets warm as well, so the installed PWA can open fully offline.
  const targets=splitPrecacheTargets();
  await Promise.all([
    precacheTo(STATIC_CACHE,targets.staticTargets),
    precacheTo(OTHER_CACHE,targets.otherTargets),
  ]);
  log('backgroundRescan done');
}
self.addEventListener('message', (event) => {
  const data = event.data || {};
  const port = event.ports && event.ports[0];
  if (!port || !data.type) return;

  if (data.type === 'CACHE_INFO') {
    event.waitUntil((async () => {
      try {
        const [pageCache, staticCache, otherCache] = await Promise.all([
          caches.open(PAGE_CACHE),
          caches.open(STATIC_CACHE),
          caches.open(OTHER_CACHE),
        ]);
        const [pageKeys, staticKeys, otherKeys] = await Promise.all([
          pageCache.keys(),
          staticCache.keys(),
          otherCache.keys(),
        ]);
        const targets = splitPrecacheTargets();
        // 统计期望列表里实际已缓存的数量（而非 cache 桶的总条目数）
        const [matchedPages, matchedStatics, matchedOthers] = await Promise.all([
          Promise.all(targets.pageTargets.map(p => {
            const abs=new URL(p,self.location.href).href;
            return pageCache.match(abs);
          })).then(rs => rs.filter(Boolean).length),
          Promise.all(targets.staticTargets.map(p => {
            const abs=new URL(p,self.location.href).href;
            return staticCache.match(abs);
          })).then(rs => rs.filter(Boolean).length),
          Promise.all(targets.otherTargets.map(p => {
            const abs=new URL(p,self.location.href).href;
            return otherCache.match(abs);
          })).then(rs => rs.filter(Boolean).length),
        ]);
        port.postMessage({
          ok: true,
          available: true,
          version: VERSION,
          cacheCount: 3,
          entryCount: pageKeys.length + staticKeys.length + otherKeys.length,
          pages:   { cached: matchedPages,   total: targets.pageTargets.length },
          statics: { cached: matchedStatics, total: targets.staticTargets.length },
          others:  { cached: matchedOthers,  total: targets.otherTargets.length },
        });
      } catch (e) {
        port.postMessage({ ok: false, available: true, error: String(e) });
      }
    })());
    return;
  }

  if (data.type === 'CLEAR_CACHE') {
    event.waitUntil((async () => {
      try {
        const names = await caches.keys();
        await Promise.all(names.map((name) => caches.delete(name)));
        await fullPrecache('clear-cache');
        port.postMessage({ ok: true, deleted: names.length });
      } catch (e) {
        port.postMessage({ ok: false, error: String(e) });
      }
    })());
  }
});
setInterval(()=>backgroundRescan().catch(e=>log('periodic rescan err',e)),RESCAN_INTERVAL);
"""

OFFLINE_HTML = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"/><meta name="viewport"content="width=device-width,initial-scale=1"/><title>离线模式</title><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,"Helvetica Neue",Arial,sans-serif;margin:0;padding:40px 24px;background:#f2f5f8;color:#333;display:flex;flex-direction:column;align-items:center;text-align:center}h1{margin:0 0 16px;font-size:1.6rem}p{line-height:1.55;margin:0 0 10px}.card{background:#fff;padding:32px 30px;max-width:460px;border-radius:18px;box-shadow:0 8px 30px -10px rgba(0,0,0,.15)}a.btn{display:inline-block;background:#3366ff;color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none;font-weight:600;letter-spacing:.5px;margin-top:18px;box-shadow:0 4px 18px -6px rgba(51,102,255,.5)}a.btn:hover{filter:brightness(1.05)}</style></head><body><div class="card"><h1>离线不可用</h1><p>该页面尚未缓存或当前网络不可用。</p><a class="btn" href="./index.html">返回目录</a></div></body></html>"""

BASE64_ICON_192 = (
    "iVBORw0KGgoAAAANSUhEUgAAAMAAAADACAYAAABlApwJAAAAAklEQVR4AewaftIAAABTSURBVO3BQRAAAAjD"
    "sP1f4w0hAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD4BxoAAdYg9r0AAAAA"
    "SUVORK5CYII="
)

BASE64_ICON_512 = (
    "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAIAAADTED8xAAAAAklEQVR4AewaftIAAABTSURBVO3BQRAAAAjD"
    "sP1f4w0hAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD4BxoAAdYg9r0AAAAA"
    "SUVORK5CYII="
)
