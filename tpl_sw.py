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
      console.warn('[sm] probe fail',url,e.message);return false;
    }
  }

  async function tryRegister(){
    for(const p of CANDIDATES){
      const ok = await probe(new URL(p,location.href));
      if(!ok) continue;
      try{
        const reg = await navigator.serviceWorker.register(p);
        console.log('[sm] registered',p,'scope:',reg.scope);
        return;
      }catch(e){
        console.warn('[sm] register fail',p,e);
      }
    }
    console.warn('[sm] all candidates failed');
  }

  function start(){ if('requestIdleCallback' in window) requestIdleCallback(tryRegister); else setTimeout(tryRegister,200); }
  window.addEventListener('load',start);
})();
"""

# ================== Service Worker 模板 (核心预缓存 + 页面管理数据桶) ==================
# 对齐 books/sg 模式：
#   - CACHE_NAME 固定 'sm-main'，不注入版本号（SW 运行时缓存，cache.put 覆盖更新）
#   - 全量数据缓存由页面 pwaCache 管理（sm-data-{version} 切换桶方案），SW 不参与
#   - SW activate 零清理：不删除任何缓存（含旧版数据桶），只做 clients.claim()
#   - 首次安装：SW 仅预缓存首屏核心资源；页面 pwaCache 弹进度条全量缓存
#   - 更新：页面检查 version.json 版本变化 → 切换数据桶重新缓存

SERVICE_WORKER_JS_NEW = r"""
/* ============================================================
 * Service Worker – 共读 阅读器
 * 缓存策略（对齐 books/sg 模式，v7.3.0 重构）：
 *   - CACHE_NAME 固定 'sm-main'：SW 运行时缓存（核心预缓存 + 运行时 cache.put 覆盖）
 *   - 全量数据缓存由页面 pwaCache 管理：sm-data-{version} 切换桶方案，SW 不参与生命周期
 *   - SW activate 零清理：不删除任何缓存（含旧版数据桶），只做 clients.claim()
 *   - 首次安装：SW 仅预缓存首屏核心资源；页面 pwaCache 弹进度条全量缓存
 *   - 更新检查：页面读 version.json，版本变化时切换数据桶重新缓存
 * ============================================================ */
const CACHE_NAME = 'sm-main';
const DATA_CACHE_PREFIX = 'sm-data-';
const DEBUG   = false;
const SW_VERSION = /*__SW_VERSION__*/;

const NAV_TIMEOUT = 15000;

// 安装时预缓存的核心资源（仅首屏必需：阻塞启动脚本 + 首屏 CSS + 图标 + 清单）
// 全量资源（页面清单 __SM_CACHE_URLS）由页面 pwaCache 安装/更新时全量缓存。
// 该列表须是 __SM_CACHE_URLS 的子集（构建生成清单时校验）。
const CORE_ASSETS = [
  './',
  './offline.htm',
  './manifest.json',
  './manifest.webmanifest',
  './assets/css/core.css',
  './assets/css/themes.css',
  './assets/css/extra.css',
  './assets/js/reader.js',
  './assets/js/highlight.js',
  './assets/js/tts.js',
  './assets/js/sw-register.js',
  './assets/js/cache-manifest.js',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/pwa-icon-192.png',
  './icons/pwa-icon-512.png'
];

function log(...a){ if(DEBUG) console.log('[sm]',...a); }
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
// URL 规范化：/index.html → / 目录补全斜杠（用于导航匹配缓存 key）
function normalizeUrlPathname(pathname){
  try{
    let p = decodeURIComponent(pathname);
    if(p.endsWith('/index.html')) p = p.slice(0, -10);
    if(/\/page_\d{4}\.htm$/.test(p)) return p;
    if(!p.split('/').pop().includes('.') && !p.endsWith('/')) p += '/';
    return p;
  }catch(e){ return pathname; }
}
async function precacheTo(cacheName, assets){
  const cache=await caches.open(cacheName);
  let okCount=0;
  const normalized=uniqueList(assets.map(normalizeAssetPath));
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

// ---- 生命周期 ----
self.addEventListener('install', e=>{
  e.waitUntil((async()=>{
    // 核心预缓存失败不阻塞安装（部分资源缺失时运行时缓存兜底）
    try{ await precacheTo(CACHE_NAME, CORE_ASSETS); }
    catch(_){}
    // 快速激活：缓存版本管理由页面 pwaCache 切换桶方案控制，SW 不参与
    self.skipWaiting();
  })());
});
self.addEventListener('activate', e=>{
  e.waitUntil((async()=>{
    // SW 只管缓存读写，不负责版本管理。
    // 旧缓存切换由页面 pwaCache 的"先建后删"流程控制，activate 零清理，
    // 避免升级中途退出导致离线失效。
    // 不启用 navigationPreload：离线时 event.preloadResponse 可能挂起导致导航失败。
    try{ await self.clients.claim(); }catch(_){}
  })());
});

// ---- 请求拦截 ----
async function handleNavigation(event){
  const request=event.request;
  const url=new URL(request.url);
  // /index.html → / 重定向（保持 URL 干净，不缓存 index.html）
  if(url.pathname.endsWith('/index.html')){
    const dir=url.pathname.slice(0,-'index.html'.length);
    return Response.redirect(url.origin+dir+url.search+url.hash,302);
  }
  const normalizedURL=url.origin + normalizeUrlPathname(url.pathname);
  // 不使用 navigationPreload：离线时 event.preloadResponse 可能挂起导致导航超时。
  // 全局缓存搜索：可命中页面数据桶（sm-data-{version}）或核心桶（sm-main）。
  // 注意：不要用 caches.match('./') 兜底——它会把目录页当作正文页返回，
  // 导致"点目录栏目后地址变成 page_XXXX.htm 但内容仍是目录页"。未缓存的正文页应走网络，网络失败回退 offline。
  const cached=await caches.match(request) || await caches.match(normalizedURL);
  if(cached){
    log('nav cache hit',normalizedURL);
    return cached;
  }
  try{
    const netReq=new Request(normalizedURL,{credentials:request.credentials});
    const res=await networkFetchWithTimeout(netReq);
    if(res && res.ok){
      try{
        const cache=await caches.open(CACHE_NAME);
        await cache.put(normalizedURL,res.clone());
      }catch(_){}
      return res;
    }
  }catch(e){
    log('nav fail',e);
  }
  return (await caches.match('./offline')) ||
         (await caches.match('./offline.htm')) ||
         new Response('<h1>Offline</h1>',{status:503,headers:{'Content-Type':'text/html'}});
}
async function cacheFirstThenRevalidate(req){
  const cache=await caches.open(CACHE_NAME);
  /* 全局搜索（含数据桶），与 precacheTo/cache.put 的绝对 URL key 一致 */
  const absUrl=new URL(req.url,self.location.href).href;
  const cached=await caches.match(req) || await caches.match(absUrl);
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
async function networkFirst(req){
  try{
    const r=await fetch(req);
    if(r && r.ok){
      const cache=await caches.open(CACHE_NAME);
      cache.put(req,r.clone()).catch(()=>{});
    }
    return r;
  }catch(_){
    const hit=await caches.match(req);
    return hit||new Response('/* offline */',{status:503});
  }
}
self.addEventListener('fetch',e=>{
  const req=e.request;
  if(req.method!=='GET') return;
  let url;
  try{ url=new URL(req.url); }catch(_){ return; }
  if(url.origin!==location.origin) return;
  // 页面侧 pwaCache 安装/更新使用 cache:'no-cache' 发起请求并显式 cache.put，
  // SW 不再介入，避免双重写缓存竞争。
  // 但导航请求即使是 no-cache 也必须拦截（离线刷新时导航请求 cache 属性为 no-cache）
  if(req.cache==='no-cache' && req.mode!=='navigate') return;
  if(req.mode==='navigate'){
    e.respondWith(handleNavigation(e));
    return;
  }
  if(/\.(css|js|woff2?|ttf|otf)$/.test(url.pathname)){
    e.respondWith(cacheFirstThenRevalidate(req));return;
  }
  if(/\.(png|jpe?g|gif|webp|svg|avif|ico)$/.test(url.pathname)){
    e.respondWith(cacheFirstThenRevalidate(req));return;
  }
  e.respondWith(networkFirst(req));
});
// ---- 消息接口 ----
self.addEventListener('message', (event) => {
  const data = event.data || {};
  if (!data.type) return;

  if (data.type === 'SKIP_WAITING') { self.skipWaiting(); return; }

  const port = event.ports && event.ports[0];

  if (data.type === 'CACHE_INFO') {
    if (!port) return;
    event.waitUntil((async () => {
      try {
        const keys = await caches.keys();
        const dataBuckets = keys.filter(k => k.indexOf(DATA_CACHE_PREFIX) === 0);
        port.postMessage({
          ok: true,
          available: true,
          cacheName: CACHE_NAME,
          version: SW_VERSION,
          dataBuckets: dataBuckets,
          bucketCount: dataBuckets.length,
          cacheCount: keys.length
        });
      } catch (e) {
        port.postMessage({ ok: false, available: true, error: String(e) });
      }
    })());
    return;
  }

  if (data.type === 'CLEAR_CACHE') {
    if (!port) return;
    event.waitUntil((async () => {
      try {
        const names = await caches.keys();
        await Promise.all(
          names.filter(n => n === CACHE_NAME || n.indexOf(DATA_CACHE_PREFIX) === 0)
               .map(n => caches.delete(n))
        );
        port.postMessage({ ok: true, deleted: names.length });
      } catch (e) {
        port.postMessage({ ok: false, error: String(e) });
      }
    })());
    return;
  }
});
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