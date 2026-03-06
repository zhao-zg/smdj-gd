# -*- coding: utf-8 -*-
"""
前端模板常量：CSS / JS / HTML
"""

# ================== 核心样式 (含页面过渡动画) ==================
CORE_CSS_BASE = r"""
:root {
  --font-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,"Helvetica Neue",Arial,"Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  --font-serif:"Noto Serif SC","Source Serif 4",Georgia,"Times New Roman",serif;
  --font-dyslexic:"OpenDyslexic",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,"Helvetica Neue",Arial,"Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  --font-base:var(--font-sans);
  --fs-base:18px;
  --fs-effective:var(--fs-base);
  --mobile-font-bump:1px;
  --lh-base:1.65;
  --c-bg:#ffffff;
  --c-fg:#222;
  --c-fg-soft:#555;
  --c-accent:#3366ff;
  --c-accent-rgb:51,102,255;
  --c-border:#e3e5e8;
  --c-surface:#f7f9fa;
  --c-danger:#d61f3a;
  --safe-top:env(safe-area-inset-top);
  --safe-bottom:env(safe-area-inset-bottom);
  --app-bar-height:54px;
  --tts-dock-height:94px;
  --shadow-level:0 4px 22px -6px rgba(0,0,0,.22);
  --shadow-small:0 2px 4px rgba(0,0,0,.06);
  --transition-fast:.25s;
}
html[data-font="serif"]{--font-base:var(--font-serif);}
html[data-font="dyslexic"]{--font-base:var(--font-dyslexic);}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%;}
body{
  margin:0;font-family:var(--font-base);font-size:var(--fs-effective);
  line-height:var(--lh-base);background:var(--c-bg);color:var(--c-fg);
  padding:0 clamp(14px,4vw,42px) calc(var(--tts-dock-height) + 40px + var(--safe-bottom));
  max-width:820px;margin-inline:auto;word-break:break-word;
  transition:background .4s,color .4s;
}
@media (max-width:640px){
  :root { --fs-effective:calc(var(--fs-base) + var(--mobile-font-bump)); }
}
.app-bar-spacer{height:calc(var(--app-bar-height) + var(--safe-top));}
h1,h2,h3,h4,h5,h6{scroll-margin-top:calc(var(--app-bar-height) + 14px);font-weight:600;line-height:1.25;margin:2.2em 0 1em;}
h1{font-size:clamp(1.9rem,1.4rem + 1.2vw,2.6rem);}
h2{font-size:clamp(1.55rem,1.3rem + .8vw,2.1rem);}
h3{font-size:clamp(1.3rem,1.2rem + .4vw,1.7rem);}
p{margin:1.05em 0;text-align:justify;}
img,video{max-width:100%;display:block;margin:1.6rem auto;border-radius:10px;box-shadow:var(--shadow-small);}
a{color:var(--c-accent);text-decoration:none;}
a:hover{text-decoration:underline;}
code,pre{font-family:ui-monospace,Menlo,Consolas,"SF Mono","Roboto Mono",monospace;font-size:.9em;}
pre{background:var(--c-surface);padding:1rem 1.2rem;border-radius:10px;overflow-x:auto;box-shadow:var(--shadow-small);}
blockquote{margin:1.8rem 0;padding:1rem 1.2rem;background:linear-gradient(165deg,var(--c-surface),#fff);border-left:4px solid var(--c-accent);border-radius:0 8px 8px 0;position:relative;}
blockquote::before{content:"\201C";position:absolute;top:-10px;left:8px;font-size:3.5rem;line-height:1;color:rgba(var(--c-accent-rgb),.25);font-family:Georgia,serif;}
hr{border:none;height:1px;background:linear-gradient(to right,transparent,var(--c-border),transparent);margin:3rem 0;}
.app-bar{position:fixed;top:0;left:0;right:0;padding-top:var(--safe-top);background:rgba(255,255,255,.82);backdrop-filter:blur(14px) saturate(180%);border-bottom:1px solid rgba(0,0,0,.05);z-index:90;transform:translateY(0);transition:transform .4s,background .4s;}
html.dark .app-bar{background:rgba(15,17,20,.88);border-bottom-color:rgba(255,255,255,.10);}
.app-bar[data-hidden="true"]{transform:translateY(calc(-100% - 6px));}
.nav{max-width:980px;margin:0 auto;height:var(--app-bar-height);display:flex;align-items:center;justify-content:center;padding:0 clamp(14px,4vw,40px);position:relative;}
.nav-buttons{display:flex;align-items:center;gap:.6rem;}
.nav-settings{position:absolute;right:clamp(14px,4vw,40px);top:0;height:100%;display:flex;align-items:center;}
.nav-btn{background:var(--c-surface);border:1px solid var(--c-border);padding:.55rem .95rem;font-size:.85rem;border-radius:999px;color:var(--c-fg);cursor:pointer;font-weight:500;display:inline-flex;align-items:center;gap:.25rem;transition:background var(--transition-fast),border-color var(--transition-fast),color var(--transition-fast);}
.nav-btn.small{padding:.45rem .75rem;font-size:.75rem;}
.nav-btn:hover{background:#fff;border-color:var(--c-accent);color:var(--c-accent);}
.nav-btn.disabled{opacity:.35;pointer-events:none;}
.top-progress{position:absolute;left:0;bottom:0;height:3px;background:linear-gradient(90deg,var(--c-accent),rgba(var(--c-accent-rgb),.35));width:0%;transition:width .12s linear;}



/* 设置面板等 */
.settings-panel{position:fixed;top:0;right:0;height:100dvh;width:min(360px,90vw);background:var(--c-bg);border-left:1px solid var(--c-border);box-shadow:-4px 0 28px -8px rgba(0,0,0,.25);transform:translateX(100%);transition:transform .45s cubic-bezier(.65,.05,.36,1);z-index:120;display:flex;flex-direction:column;}
.settings-panel[data-open="true"]{transform:translateX(0);}
.settings-inner{padding:calc(12px + var(--safe-top)) 20px 32px;overflow-y:auto;}
.settings-inner h2{margin:.2rem 0 1.4rem;font-size:1.1rem;letter-spacing:.4px;}
.setting{display:flex;flex-direction:column;gap:.35rem;margin-bottom:1.2rem;}
.setting label{font-size:.7rem;font-weight:600;letter-spacing:.9px;text-transform:uppercase;color:var(--c-fg-soft);display:flex;justify-content:space-between;}
.setting input[type=range]{width:100%;appearance:none;height:6px;border-radius:4px;background:var(--c-surface);border:1px solid var(--c-border);}
.setting input[type=range]::-webkit-slider-thumb{appearance:none;width:18px;height:18px;border-radius:50%;background:var(--c-accent);box-shadow:0 2px 8px -2px rgba(var(--c-accent-rgb),.7);cursor:pointer;border:2px solid #fff;}
.chips{display:flex;flex-wrap:wrap;gap:.55rem;}
.chip{background:var(--c-surface);border:1px solid var(--c-border);padding:.55rem .85rem;font-size:.75rem;border-radius:999px;letter-spacing:.4px;cursor:pointer;color:var(--c-fg-soft);font-weight:500;transition:.25s;}
.chip:hover{border-color:var(--c-accent);color:var(--c-accent);}
.chip.active{background:var(--c-accent);color:#fff;border-color:var(--c-accent);box-shadow:0 4px 14px -4px rgba(var(--c-accent-rgb),.6);}
.chip.disabled{opacity:.45;pointer-events:none;}
.close-btn{width:100%;background:var(--c-accent);color:#fff;border:none;border-radius:10px;padding:.9rem 1.2rem;font-weight:600;margin-top:.4rem;cursor:pointer;letter-spacing:.5px;font-size:.85rem;box-shadow:var(--shadow-small);}
.fab-top{position:fixed;bottom:calc(var(--tts-dock-height) + 20px + var(--safe-bottom));right:clamp(16px,4vw,42px);width:56px;height:56px;border-radius:50%;background:var(--c-accent);color:#fff;display:none;align-items:center;justify-content:center;font-size:22px;cursor:pointer;border:none;box-shadow:var(--shadow-level);z-index:60;transition:transform .4s;}
.fab-top:hover{transform:translateY(-4px);}
#back-top.show{display:flex;}

.tts-dock{position:fixed;left:0;right:0;bottom:0;padding:10px clamp(14px,4vw,48px) calc(6px + var(--safe-bottom));background:rgba(255,255,255,.92);backdrop-filter:blur(18px) saturate(180%);border-top:1px solid var(--c-border);box-shadow:0 -8px 24px -10px rgba(0,0,0,.25);z-index:80;display:flex;flex-direction:column;gap:8px;transition:transform .4s,opacity .4s;}
html.dark .tts-dock{background:rgba(15,17,20,.94);}
.tts-dock[data-visible="false"]{transform:translateY(110%);opacity:0;pointer-events:none;}
.tts-dock-main{display:flex;align-items:center;gap:10px;justify-content:center;flex-wrap:wrap;}
.dock-btn{background:var(--c-surface);border:1px solid var(--c-border);border-radius:14px;padding:10px 16px;font-size:16px;cursor:pointer;color:var(--c-fg);display:inline-flex;align-items:center;justify-content:center;transition:.25s;min-width:46px;min-height:46px;box-shadow:var(--shadow-small);}
.dock-btn.play{background:linear-gradient(135deg,var(--c-accent),#5b8dff);color:#fff;border:none;}
.dock-btn:hover{filter:brightness(1.05);}
.dock-btn.small{padding:8px 12px;font-size:14px;min-width:auto;min-height:42px;}
.tts-progress-row{display:flex;align-items:center;gap:14px;}
.tts-progress-bar{position:relative;flex:1;height:10px;background:var(--c-surface);border:1px solid var(--c-border);border-radius:6px;cursor:pointer;overflow:hidden;touch-action:none;}
.tts-progress-fill{position:absolute;left:0;top:0;bottom:0;width:0%;background:linear-gradient(90deg,var(--c-accent),rgba(var(--c-accent-rgb),.55));transition:width .25s linear;}
.tts-progress-handle{position:absolute;top:50%;transform:translate(-50%,-50%);width:18px;height:18px;border-radius:50%;background:var(--c-accent);box-shadow:0 3px 8px -2px rgba(var(--c-accent-rgb),.6);pointer-events:auto;}
.tts-progress-text{font-size:.7rem;font-weight:600;letter-spacing:.5px;color:var(--c-fg-soft);min-width:70px;text-align:right;}
.tts-sentence{transition:background .25s,border-radius .25s;}
.tts-active{background:rgba(var(--c-accent-rgb),.25);border-radius:4px;padding:2px 3px;}
.toc-list{list-style:none;padding:0;margin:1.8rem 0 4rem;display:grid;gap:.9rem;}
.toc-list li a{display:block;background:var(--c-surface);padding:.95rem 1.2rem;border-radius:10px;border:1px solid var(--c-border);font-weight:500;font-size:.9rem;transition:.3s;letter-spacing:.3px;}
.toc-list li a:hover{background:#fff;border-color:var(--c-accent);color:var(--c-accent);box-shadow:var(--shadow-small);}
.hint{font-size:.75rem;letter-spacing:.5px;color:var(--c-fg-soft);opacity:.75;margin-top:3rem;text-align:center;}

@media (max-width:640px){
  body{padding:0 18px calc(var(--tts-dock-height) + 34px + var(--safe-bottom));}
  h1{font-size:clamp(1.65rem,1.4rem + 1.6vw,2.15rem);}
  .dock-btn{min-width:42px;min-height:44px;padding:8px 14px;}
  .tts-progress-bar{height:8px;}
  .tts-progress-handle{width:16px;height:16px;}
  .fab-top{width:52px;height:52px;font-size:20px;}
}
html.dark {--c-bg:#0f1114; --c-fg:#f0f3f7; --c-fg-soft:#b0bac6; --c-surface:#1e2329; --c-border:#3a424f; --c-accent:#6b9eff; --c-accent-rgb:107,158,255;}
html.dark #reader-content *{color:var(--c-fg) !important;}
html.dark #reader-content a,html.dark #reader-content a:visited{color:var(--c-accent) !important;}
html.reduce-motion *{animation:none !important;transition:none !important;}
"""

CORE_CSS_FULL = CORE_CSS_BASE
CORE_CSS_LIGHT = CORE_CSS_BASE \
    .replace("box-shadow:0 -8px 24px -10px rgba(0,0,0,.25);", "box-shadow:none;") \
    .replace("box-shadow:var(--shadow-level);", "box-shadow:none;") \
    .replace("box-shadow:0 4px 14px -4px rgba(var(--c-accent-rgb),.6);", "box-shadow:none;") \
    .replace("box-shadow:var(--shadow-small);", "box-shadow:none;")

THEMES_CSS = "/* 可扩展其它主题 */"

FONTS_CSS_TEMPLATE = r"""/* fonts.css (默认不引入自定义字体)
如需字体:
@font-face {
  font-family: "MySubset";
  src: url("/fonts/MySubset.woff2") format("woff2");
  font-display: swap;
}
html[data-font="sans"] {
  --font-base: "MySubset",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,"Helvetica Neue",Arial,"Microsoft YaHei","Noto Sans CJK SC",sans-serif;
}
*/"""

READER_JS = r"""
/* Reader Core v3.6.7 – smooth transitions + swipe + dynamic nav (toc fix) */
(()=>{const APP_VER='3.6.7';const LS_KEY='reader.settings.v3.6.3';const SCROLL_PREFIX='reader.scroll.';const DEFER_TTS_SEGMENT=/*__DELAY_SEGMENT__*/;
const FONT_FAMILIES={sans:'-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,"Helvetica Neue",Arial,"Microsoft YaHei","Noto Sans CJK SC",sans-serif',serif:'"Noto Serif SC","Source Serif 4",Georgia,"Times New Roman",serif',dyslexic:'"OpenDyslexic",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,"Helvetica Neue",Arial,"Microsoft YaHei","Noto Sans CJK SC",sans-serif'};
const st={fontSize:18,lineHeight:1.65,font:'sans',theme:'auto',ttsVisible:false};
let lastScrollY=0,hideTimer=null,installPromptEvt=null,overrideStyle=null,scrollSaveTimer=null;
const pageCache=new Map();const historyStackLimit=parseInt(localStorage.getItem('historyCacheSize')||'50',10);let currentURL=location.href;
function logNav(...a){if(localStorage.getItem('navDebug')==='1')console.log('[NAV]',...a);}function logSwipe(...a){if(localStorage.getItem('swipeDebug')==='1')console.log('[SWIPE]',...a);}
function loadSettings(){try{Object.assign(st,JSON.parse(localStorage.getItem(LS_KEY)||'{}'));}catch(e){}}function saveSettings(){localStorage.setItem(LS_KEY,JSON.stringify(st));}
function ensureOverrideStyle(){if(!overrideStyle){overrideStyle=document.createElement('style');overrideStyle.id='font-override';document.head.appendChild(overrideStyle);}const ff=FONT_FAMILIES[st.font]||FONT_FAMILIES.sans;overrideStyle.textContent=`body,#reader-content,.tts-sentence,#reader-content *{font-family:${ff} !important;}`;}
function applyTheme(){const html=document.documentElement;html.classList.remove('dark');const prefersDark=window.matchMedia('(prefers-color-scheme: dark)').matches;if(st.theme==='dark'||(st.theme==='auto'&&prefersDark))html.classList.add('dark');html.setAttribute('data-theme',st.theme);}
function syncChips(){document.querySelectorAll('#font-family-choices .chip').forEach(ch=>ch.classList.toggle('active',ch.dataset.font===st.font));document.querySelectorAll('#theme-choices .chip').forEach(ch=>ch.classList.toggle('active',ch.dataset.theme===st.theme));const showBtn=document.querySelector('#tts-toggle-chips [data-tts=show]');const hideBtn=document.querySelector('#tts-toggle-chips [data-tts=hide]');if(showBtn&&hideBtn){showBtn.classList.toggle('active',st.ttsVisible);hideBtn.classList.toggle('active',!st.ttsVisible);}if(window.TTS_SUPPORTED===false){document.querySelectorAll('#tts-toggle-chips .chip').forEach(c=>{c.classList.add('disabled');c.style.opacity='.45';});}const fsLabel=document.getElementById('font-size-label');if(fsLabel)fsLabel.textContent=st.fontSize+'px';const lhLabel=document.getElementById('line-height-label');if(lhLabel)lhLabel.textContent=st.lineHeight.toFixed(2);}
function applySettings(){document.documentElement.style.setProperty('--fs-base',st.fontSize+'px');document.documentElement.style.setProperty('--lh-base',st.lineHeight);document.documentElement.dataset.font=st.font;applyTheme();ensureOverrideStyle();syncChips();toggleTTSVisibility(st.ttsVisible,false);}
function initControls(){const fs=document.getElementById('font-size-range');fs&&fs.addEventListener('input',()=>{st.fontSize=parseInt(fs.value,10);applySettings();saveSettings();});const lh=document.getElementById('line-height-range');lh&&lh.addEventListener('input',()=>{st.lineHeight=parseFloat(lh.value);applySettings();saveSettings();});document.querySelectorAll('#font-family-choices .chip').forEach(ch=>ch.addEventListener('click',()=>{st.font=ch.dataset.font;applySettings();saveSettings();}));document.querySelectorAll('#theme-choices .chip').forEach(ch=>ch.addEventListener('click',()=>{st.theme=ch.dataset.theme;applySettings();saveSettings();}));document.querySelectorAll('#tts-toggle-chips .chip').forEach(ch=>ch.addEventListener('click',()=>{if(window.TTS_SUPPORTED===false){alert('该设备不支持朗读功能');return;}st.ttsVisible=(ch.dataset.tts==='show');toggleTTSVisibility(st.ttsVisible,true);saveSettings();syncChips();if(st.ttsVisible&&DEFER_TTS_SEGMENT)window.dispatchEvent(new CustomEvent('tts-lazy-segment'));}));const panel=document.getElementById('settings-panel');const openBtn=document.getElementById('open-settings');const closeBtn=document.getElementById('close-settings');openBtn&&openBtn.addEventListener('click',()=>{panel.setAttribute('data-open','true');panel.setAttribute('aria-hidden','false');if('serviceWorker' in navigator)navigator.serviceWorker.getRegistration().then(reg=>{if(!reg||!reg.active)return;const ch=new MessageChannel();ch.port1.onmessage=ev=>{const info=ev.data||{};const infoBox=document.getElementById('cache-info');const pctEl=document.getElementById('cache-pct');const fillEl=document.getElementById('cache-progress-fill');const statusBox=document.getElementById('cache-status-box');if(statusBox)statusBox.style.display='block';if(!info.available){if(infoBox)infoBox.textContent='Service Worker 未就绪';return;}const total=(info.pages?.total||0)+(info.statics?.total||0)+(info.others?.total||0);const cached=(info.pages?.cached||0)+(info.statics?.cached||0)+(info.others?.cached||0);const pct=total>0?Math.min(100,Math.round(cached/total*100)):0;if(infoBox)infoBox.textContent=`版本 ${info.version||'-'}  期望 ${total} 个  已缓存 ${cached} 个`;if(pctEl)pctEl.textContent=pct+'%';if(fillEl)fillEl.style.width=pct+'%';};reg.active.postMessage({type:'CACHE_INFO'},[ch.port2]);}).catch(()=>{});});closeBtn&&closeBtn.addEventListener('click',()=>{panel.setAttribute('data-open','false');panel.setAttribute('aria-hidden','true');});document.addEventListener('click',e=>{if(panel&&panel.getAttribute('data-open')==='true'&&!panel.contains(e.target)&&e.target!==openBtn){panel.setAttribute('data-open','false');panel.setAttribute('aria-hidden','true');}});}
function toggleTTSVisibility(show){const dock=document.getElementById('tts-dock');if(!dock)return;if(window.TTS_SUPPORTED===false){dock.setAttribute('data-visible','false');return;}dock.setAttribute('data-visible',show?'true':'false');}
function handleScroll(){const y=window.scrollY||document.documentElement.scrollTop;const appBar=document.querySelector('.app-bar');if(appBar){const goingDown=y>lastScrollY;if(y>120&&goingDown)appBar.setAttribute('data-hidden','true');else appBar.removeAttribute('data-hidden');}lastScrollY=y;updateProgress();toggleBackTop(y);scheduleBarShow();}
function scheduleBarShow(){const appBar=document.querySelector('.app-bar');clearTimeout(hideTimer);hideTimer=setTimeout(()=>appBar&&appBar.removeAttribute('data-hidden'),1600);}
function updateProgress(){const bar=document.getElementById('top-progress');const content=document.getElementById('reader-content');if(!bar||!content)return;const scrolled=window.scrollY||document.documentElement.scrollTop;const h=content.scrollHeight-window.innerHeight;bar.style.width=(h>0?(scrolled/h)*100:0)+'%';}
function toggleBackTop(y){const btn=document.getElementById('back-top');if(!btn)return;if(y>360)btn.classList.add('show');else btn.classList.remove('show');}
function initBackTop(){const btn=document.getElementById('back-top');btn&&btn.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));}
function saveScrollThrottle(){if(scrollSaveTimer)return;scrollSaveTimer=setTimeout(()=>{scrollSaveTimer=null;const pageIndex=document.getElementById('reader-content')?.dataset.pageIndex;if(pageIndex)localStorage.setItem(SCROLL_PREFIX+pageIndex,String(window.scrollY||document.documentElement.scrollTop));},400);}
function saveScrollImmediate(){const pageIndex=document.getElementById('reader-content')?.dataset.pageIndex;if(pageIndex)localStorage.setItem(SCROLL_PREFIX+pageIndex,String(window.scrollY||document.documentElement.scrollTop));}
function restoreScroll(){const pageIndex=document.getElementById('reader-content')?.dataset.pageIndex;if(pageIndex&&pageIndex!=='-1'){const saved=localStorage.getItem(SCROLL_PREFIX+pageIndex);if(saved)setTimeout(()=>window.scrollTo(0,parseInt(saved,10)),30);}}
function initKeys(){document.addEventListener('keydown',e=>{if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName))return;if(e.key==='ArrowLeft'&&window.PAGE_INFO?.prevPage)customNavigate(window.PAGE_INFO.prevPage,'prev');if(e.key==='ArrowRight'&&window.PAGE_INFO?.nextPage)customNavigate(window.PAGE_INFO.nextPage,'next');});}
function motionPref(){if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)document.documentElement.classList.add('reduce-motion');}
function systemThemeWatcher(){const mq=window.matchMedia('(prefers-color-scheme: dark)');mq.addEventListener('change',()=>{if(st.theme==='auto')applyTheme();});}
function initTodayLinks(){document.querySelectorAll('.today-link').forEach(link=>{link.addEventListener('click',e=>{e.preventDefault();const startDate=link.dataset.startDate;const startIndex=parseInt(link.dataset.startIndex||'0',10);const total=parseInt(link.dataset.total||'0',10);if(!startDate||total<=0)return;const parts=startDate.split('-').map(Number);if(parts.length!==3){alert('起始日期配置错误');return;}const sDate=new Date(parts[0],parts[1]-1,parts[2]);const now=new Date();const diff=Math.floor((now-sDate)/(1000*60*60*24));let target=startIndex+diff;if(diff<0){alert('尚未到起始日期');target=startIndex;}else if(target>total-1){alert('超出范围，跳最后一页');target=total-1;}if(target<0)target=0;const prefix=(window.PAGE_INFO&&window.PAGE_INFO.current>=0)?'../':'';const url=prefix+'page_'+String(target).padStart(4,'0')+'/';customNavigate(url,target>(window.PAGE_INFO?.current||0)?'next':'prev');});});}
function initSwipe(){if(localStorage.getItem('disableSwipe')==='1')return;const baseX=Math.round(window.innerWidth*0.14);const THRESHOLD_X=parseInt(localStorage.getItem('swipeThresholdX')||String(Math.max(42,Math.min(88,baseX))),10);const THRESHOLD_Y=parseInt(localStorage.getItem('swipeThresholdY')||'72',10);const ANGLE_RATIO=parseFloat(localStorage.getItem('swipeAngleRatio')||'1.35');const MAX_TIME=850;const MIN_VELOCITY=parseFloat(localStorage.getItem('swipeMinVelocityPxMs')||'0.30');let startX=0,startY=0,startTime=0,tracking=false,multi=false,moved=false;function panelOpen(){return document.getElementById('settings-panel')?.getAttribute('data-open')==='true';}function inTTSDock(yClient){const dock=document.getElementById('tts-dock');if(!dock)return false;const rect=dock.getBoundingClientRect();return yClient>=rect.top;}function onStart(e){if(e.touches&&e.touches.length>1){multi=true;return;}multi=false;if(panelOpen())return;const t=e.touches?e.touches[0]:e;if(inTTSDock(t.clientY))return;tracking=true;moved=false;startX=t.clientX;startY=t.clientY;startTime=Date.now();}function onMove(e){if(!tracking||multi)return;const t=e.touches?e.touches[0]:e;const dx=t.clientX-startX,dy=t.clientY-startY;if(Math.abs(dx)>5||Math.abs(dy)>5)moved=true;}function onEnd(e){if(!tracking||multi){tracking=false;return;}tracking=false;const t=e.changedTouches?e.changedTouches[0]:e;const totalDx=t.clientX-startX,totalDy=t.clientY-startY;const dt=Date.now()-startTime;const absDx=Math.abs(totalDx),absDy=Math.abs(totalDy);const velocity=absDx/Math.max(dt,1);logSwipe('end',{totalDx,totalDy,dt,velocity});if(!moved||dt>MAX_TIME)return;const sel=window.getSelection();if(sel&&sel.toString().length>0)return;if(absDy>THRESHOLD_Y)return;if(absDx<THRESHOLD_X&&velocity<MIN_VELOCITY)return;if(absDx/(absDy+1)<ANGLE_RATIO)return;if(totalDx>0){if(window.PAGE_INFO?.prevPage)customNavigate(window.PAGE_INFO.prevPage,'prev');}else{if(window.PAGE_INFO?.nextPage)customNavigate(window.PAGE_INFO.nextPage,'next');}}document.addEventListener('touchstart',onStart,{passive:true});document.addEventListener('touchmove',onMove,{passive:true});document.addEventListener('touchend',onEnd,{passive:true});document.addEventListener('pointerdown',e=>{if(e.pointerType!=='touch')return;onStart(e);});document.addEventListener('pointerup',e=>{if(e.pointerType!=='touch')return;onEnd(e);});}
document.addEventListener('click',e=>{const a=e.target.closest('a.nav-btn');if(!a)return;const role=a.dataset.nav;if(role==='prev'||role==='next'||role==='toc'){if(a.classList.contains('disabled'))return;const href=a.getAttribute('href');if(!href)return;e.preventDefault();customNavigate(href,role==='next'?'next':'prev');}});
function updateNavBarByPageInfo(pageInfo){if(!pageInfo)return;const nav=document.querySelector('.nav');if(!nav)return;let prevBtn=nav.querySelector('[data-nav="prev"]');let nextBtn=nav.querySelector('[data-nav="next"]');let tocBtn=nav.querySelector('[data-nav="toc"]');if(!prevBtn)prevBtn=[...nav.querySelectorAll('a.nav-btn,span.nav-btn')].find(el=>el.textContent.trim()==='←');if(!nextBtn)nextBtn=[...nav.querySelectorAll('a.nav-btn,span.nav-btn')].find(el=>el.textContent.trim()==='→');if(!tocBtn)tocBtn=[...nav.querySelectorAll('a.nav-btn')].find(el=>el.textContent.trim()==='目录');if(pageInfo.prevPage){if(prevBtn&&prevBtn.tagName==='SPAN'){const a=document.createElement('a');a.className='nav-btn';a.textContent='←';a.dataset.nav='prev';prevBtn.replaceWith(a);prevBtn=a;}if(prevBtn){prevBtn.classList.remove('disabled');prevBtn.dataset.nav='prev';prevBtn.setAttribute('href',pageInfo.prevPage);prevBtn.removeAttribute('aria-hidden');}}else if(prevBtn){prevBtn.classList.add('disabled');prevBtn.removeAttribute('href');prevBtn.setAttribute('aria-hidden','true');prevBtn.dataset.nav='prev';}
if(pageInfo.nextPage){if(nextBtn&&nextBtn.tagName==='SPAN'){const a=document.createElement('a');a.className='nav-btn';a.textContent='→';a.dataset.nav='next';nextBtn.replaceWith(a);nextBtn=a;}if(nextBtn){nextBtn.classList.remove('disabled');nextBtn.dataset.nav='next';nextBtn.setAttribute('href',pageInfo.nextPage);nextBtn.removeAttribute('aria-hidden');}}else if(nextBtn){nextBtn.classList.add('disabled');nextBtn.removeAttribute('href');nextBtn.setAttribute('aria-hidden','true');nextBtn.dataset.nav='next';}
if(tocBtn){const correct=(pageInfo.current===-1)?'index.html':'../index.html';if(tocBtn.getAttribute('href')!=correct)tocBtn.setAttribute('href',correct);tocBtn.dataset.nav='toc';}}
function prefetchLink(url){if(!url)return;if(localStorage.getItem('prefetchDisable')==='1')return;if(pageCache.has(url))return;logNav('prefetch',url);fetch(url,{credentials:'same-origin'}).then(r=>{if(!r.ok)throw new Error(r.status);return r.text();}).then(html=>{const doc=new DOMParser().parseFromString(html,'text/html');const content=doc.querySelector('#reader-content');let pageInfo=null;for(const s of doc.querySelectorAll('script')){const txt=s.textContent||'';if(txt.includes('window.PAGE_INFO')){try{const m=txt.match(/window\.PAGE_INFO\s*=\s*(\{[^;]+});/);if(m){pageInfo=eval('('+m[1]+')');break;}}catch(_){}}}if(content&&pageInfo){pageCache.set(url,{doc,contentHTML:content.innerHTML,title:doc.title,pageInfo});trimCache();}}).catch(()=>{});}
function trimCache(){if(pageCache.size<=historyStackLimit)return;const firstKey=pageCache.keys().next().value;pageCache.delete(firstKey);}
function installInitialPrefetch(){if(!window.PAGE_INFO)return;if(window.PAGE_INFO.prevPage)prefetchLink(new URL(window.PAGE_INFO.prevPage,location.href).href);if(window.PAGE_INFO.nextPage)prefetchLink(new URL(window.PAGE_INFO.nextPage,location.href).href);}
function customNavigate(url,dir){if(!url)return;const abs=new URL(url,location.href).href;smoothTransitionTo(abs,dir,true);}
function smoothTransitionTo(url,dir='next',allowFetch=true){if(pageCache.has(url)){doPageSwap(url,pageCache.get(url),dir);return;}if(!allowFetch){location.href=url;return;}fetch(url,{credentials:'same-origin'}).then(r=>{if(!r.ok)throw new Error(r.status);return r.text();}).then(html=>{const doc=new DOMParser().parseFromString(html,'text/html');const content=doc.querySelector('#reader-content');let pageInfo=null;for(const s of doc.querySelectorAll('script')){const txt=s.textContent||'';if(txt.includes('window.PAGE_INFO')){try{const m=txt.match(/window\.PAGE_INFO\s*=\s*(\{[^;]+});/);if(m){pageInfo=eval('('+m[1]+')');break;}}catch(_){}}}if(content&&pageInfo){const entry={doc,contentHTML:content.innerHTML,title:doc.title,pageInfo};pageCache.set(url,entry);trimCache();doPageSwap(url,entry,dir);}else{location.href=url;}}).catch(()=>location.href=url);}
function doPageSwap(url,entry,dir){saveScrollImmediate();const oldView=document.getElementById('reader-content');if(!oldView){location.href=url;return;}const newNode=oldView.cloneNode(false);newNode.innerHTML=entry.contentHTML;newNode.id='reader-content';newNode.dataset.pageIndex=entry.pageInfo.current;oldView.replaceWith(newNode);document.title=entry.title;window.PAGE_INFO={current:entry.pageInfo.current,total:entry.pageInfo.total,prevPage:entry.pageInfo.prevPage,nextPage:entry.pageInfo.nextPage};updateNavBarByPageInfo(window.PAGE_INFO);if(url!==currentURL){history.pushState({url},"",url);currentURL=url;}afterSwap(url,entry);}
function ensurePageShell(){}
function afterSwap(url,entry){scrollTo(0,0);restoreScroll();updateProgress();installInitialPrefetch();reinitDynamicFeatures();}
function reinitDynamicFeatures(){if(st.ttsVisible&&DEFER_TTS_SEGMENT){window.dispatchEvent(new CustomEvent('tts-lazy-segment'));}}
window.addEventListener('popstate',()=>{const target=location.href;if(pageCache.has(target)){doPageSwap(target,pageCache.get(target),'prev');}else{smoothTransitionTo(target,'prev',true);}});
function initSWDisableCheck(){const urlParams=new URLSearchParams(location.search);if(urlParams.get('no-sw')==='1'){localStorage.setItem('disableSW','1');if('serviceWorker' in navigator){navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>r.unregister()));}console.log('[SW] 已禁用 (参数 no-sw=1)');}}
document.addEventListener('DOMContentLoaded',()=>{initSWDisableCheck();loadSettings();applySettings();initControls();initBackTop();initKeys();motionPref();systemThemeWatcher();restoreScroll();updateProgress();initTodayLinks();initSwipe();installInitialPrefetch();updateNavBarByPageInfo(window.PAGE_INFO);});
window.addEventListener('scroll',()=>{handleScroll();saveScrollThrottle();},{passive:true});
window.addEventListener('beforeunload',()=>saveScrollThrottle());
})();
"""

APP_UPDATE_JS = r"""
/* APK self-update for Capacitor Android */
(() => {
  const REMOTE_ENDPOINTS = [
    'https://smdj-gd.zhaozg.cloudns.org/version.json',
    'https://smdj-gd.07170501.xyz/version.json',
  ];
  // 原生 APK 直接访问远端；PWA/浏览器先读本地缓存版
  const UPDATE_ENDPOINTS = isNative()
    ? REMOTE_ENDPOINTS
    : [new URL('version.json', window.location.href).href, './version.json', ...REMOTE_ENDPOINTS];
  const APK_PATH_FALLBACK = 'downloads/smdj-gd-latest.apk';
  const CHUNK_SIZE = 256 * 1024;

  function log(...args) {
    if (localStorage.getItem('updateDebug') === '1') console.log('[APP-UPDATE]', ...args);
  }

  function isNative() {
    return !!(window.Capacitor && typeof window.Capacitor.isNativePlatform === 'function' && window.Capacitor.isNativePlatform());
  }

  function cmpVer(a, b) {
    const pa = String(a || '0').split('.').map((x) => parseInt(x, 10) || 0);
    const pb = String(b || '0').split('.').map((x) => parseInt(x, 10) || 0);
    const n = Math.max(pa.length, pb.length);
    for (let i = 0; i < n; i++) {
      const da = pa[i] || 0;
      const db = pb[i] || 0;
      if (da > db) return 1;
      if (da < db) return -1;
    }
    return 0;
  }

  function bytesToBase64(uint8) {
    let binary = '';
    const step = 0x8000;
    for (let i = 0; i < uint8.length; i += step) {
      const sub = uint8.subarray(i, i + step);
      binary += String.fromCharCode.apply(null, sub);
    }
    return btoa(binary);
  }

  async function fetchJsonNoStore(url) {
    const r = await fetch(url, { cache: 'no-store' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    return { data, sourceUrl: r.url || url };
  }

  async function fetchVersionInfo() {
    let lastErr = null;
    for (const ep of UPDATE_ENDPOINTS) {
      try {
        const abs = new URL(ep, window.location.href).href;
        const out = await fetchJsonNoStore(abs);
        return out;
      } catch (e) {
        lastErr = e;
      }
    }
    throw lastErr || new Error('version fetch failed');
  }

  async function getLocalVersion() {
    try {
      const app = window.Capacitor?.Plugins?.App;
      if (app && typeof app.getInfo === 'function') {
        const info = await app.getInfo();
        if (info && info.version) return String(info.version);
      }
    } catch (_) {}
    // 由构建时注入的版本号作为兜底（优先于 localStorage）
    if (window.APP_VERSION) return String(window.APP_VERSION);
    return localStorage.getItem('app.localVersion') || '0.0.0';
  }

  function toAbsolute(url, baseUrl) {
    return new URL(url, baseUrl || window.location.href).href;
  }

  function buildUrlCandidates(remote, sourceUrl) {
    const candidates = [];
    const files = [];
    if (remote.apk_file) files.push(String(remote.apk_file));
    if (!files.length) files.push(APK_PATH_FALLBACK);
    const direct = [];
    if (remote.apk_url) direct.push(String(remote.apk_url));
    if (Array.isArray(remote.apk_urls)) {
      remote.apk_urls.forEach((u) => u && direct.push(String(u)));
    }
    files.forEach((f) => direct.push(toAbsolute(f, sourceUrl)));

    direct.forEach((u) => {
      if (/^https?:\/\//i.test(u)) candidates.push(u);
    });
    return [...new Set(candidates)];
  }

  async function tryDownloadToFile(urls, path, onProgress) {
    const fs = window.Capacitor?.Plugins?.Filesystem;
    if (!fs) throw new Error('Filesystem plugin unavailable');

    let lastErr = null;
    for (const u of urls) {
      try {
        log('download try', u);
        const res = await fetch(u, { cache: 'no-store' });
        if (!res.ok || !res.body) throw new Error(`download failed ${res.status}`);
        const total = parseInt(res.headers.get('content-length') || '0', 10) || 0;

        await fs.writeFile({ path, data: '', directory: 'CACHE', recursive: true });
        const reader = res.body.getReader();
        let received = 0;
        let pending = new Uint8Array(0);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          if (!value) continue;

          const merged = new Uint8Array(pending.length + value.length);
          merged.set(pending, 0);
          merged.set(value, pending.length);

          let offset = 0;
          while (merged.length - offset >= CHUNK_SIZE) {
            const chunk = merged.subarray(offset, offset + CHUNK_SIZE);
            await fs.appendFile({ path, data: bytesToBase64(chunk), directory: 'CACHE' });
            offset += CHUNK_SIZE;
          }
          pending = merged.subarray(offset);

          received += value.length;
          if (onProgress) onProgress(received, total);
        }

        if (pending.length > 0) {
          await fs.appendFile({ path, data: bytesToBase64(pending), directory: 'CACHE' });
        }

        const uriObj = await fs.getUri({ path, directory: 'CACHE' });
        return { url: u, uri: uriObj?.uri || '', path };
      } catch (e) {
        lastErr = e;
        log('download failed', u, String(e));
      }
    }
    throw lastErr || new Error('all download URLs failed');
  }

  async function installApkByPlugin(fileInfo) {
    const p = window.Capacitor?.Plugins || {};
    const installer = p.ApkInstaller || p.APKInstaller || p.ApkUpdate;
    if (!installer) throw new Error('ApkInstaller plugin unavailable');

    // 优先使用 content URI；Java 插件能直接识别 content:// scheme
    const effectivePath = fileInfo.uri || fileInfo.path;
    const methods = ['install', 'installApk', 'openApk', 'openInstaller'];
    let lastErr = null;
    for (const m of methods) {
      if (typeof installer[m] !== 'function') continue;
      try {
        await installer[m]({
          path: effectivePath,
          filePath: effectivePath,
          uri: fileInfo.uri,
          apkPath: effectivePath,
        });
        return true;
      } catch (e) {
        lastErr = e;
        log('installer method', m, 'failed:', String(e));
      }
    }
    throw lastErr || new Error('No supported installer method');
  }

  async function checkForUpdates(silent = false) {
    if (!isNative()) {
      return { ok: false, skipped: true, reason: 'not-native' };
    }
    const fetched = await fetchVersionInfo();
    const remote = fetched.data || {};
    const sourceUrl = fetched.sourceUrl;
    const localVersion = await getLocalVersion();
    const remoteVersion = String(remote.apk_version || remote.version || '0.0.0');
    const hasNew = cmpVer(remoteVersion, localVersion) > 0;

    if (!hasNew) {
      if (!silent) alert(`已是最新版本 (${localVersion})`);
      return { ok: true, update: false, localVersion, remoteVersion };
    }

    const confirmInstall = confirm(`发现新版本 ${remoteVersion}，是否立即下载并安装？`);
    if (!confirmInstall) return { ok: true, update: true, canceled: true, remoteVersion };

    const urls = buildUrlCandidates(remote, sourceUrl);
    if (!urls.length) throw new Error('No APK URL candidates');

    const savePath = `updates/smdj-gd-${remoteVersion}.apk`;
    const progressEl = document.getElementById('cache-info');
    const onProgress = (loaded, total) => {
      if (!progressEl) return;
      if (total > 0) {
        const p = ((loaded / total) * 100).toFixed(1);
        progressEl.textContent = `更新下载中: ${p}% (${Math.floor(loaded / 1024)}KB / ${Math.floor(total / 1024)}KB)`;
      } else {
        progressEl.textContent = `更新下载中: ${Math.floor(loaded / 1024)}KB`;
      }
    };

    const fileInfo = await tryDownloadToFile(urls, savePath, onProgress);
    await installApkByPlugin(fileInfo);
    if (progressEl) progressEl.textContent = '已触发安装器，请在系统安装界面确认安装';
    return { ok: true, update: true, installed: true, remoteVersion };
  }

  window.AppUpdate = {
    checkForUpdates,
  };
})();
"""

# ================== TTS JS – native Capacitor TTS + Web Speech API fallback ==================
TTS_JS = r"""
/* 句级 TTS v4.0 – Capacitor 原生 TTS (APK) / Web Speech API (PWA/浏览器) */

/* ---- 语音引擎适配器 ---- */
class WebSpeechEngine{
  constructor(){
    this.synth=window.speechSynthesis;this.voice=null;this._retry=0;this._timer=null;
    const load=()=>{const vs=this.synth.getVoices();if(vs&&vs.length){this.voice=vs.find(v=>/^zh/i.test(v.lang))||vs.find(v=>/Chinese/i.test(v.name))||vs[0];}else{this._retry++;this._timer=setTimeout(load,Math.min(5000,500+this._retry*250));}};
    if('onvoiceschanged' in this.synth)this.synth.onvoiceschanged=load;
    load();
  }
  speak(text,rate,pitch,volume){
    return new Promise((resolve,reject)=>{
      const u=new SpeechSynthesisUtterance(text);
      u.lang='zh-CN';if(this.voice)u.voice=this.voice;
      u.rate=rate;u.pitch=pitch;u.volume=volume;
      u.onend=()=>resolve();u.onerror=e=>reject(e);
      this.synth.speak(u);
    });
  }
  stop(){this.synth.cancel();}
  pause(){this.synth.pause();}
  resume(){this.synth.resume();}
  get supportsPause(){return true;}
}

class NativeEngine{
  constructor(p){this.p=p;}
  speak(text,rate,pitch,volume){return this.p.speak({text,lang:'zh-CN',rate,pitch,volume,category:'ambient'});}
  stop(){return this.p.stop().catch(()=>{});}
  pause(){return this.stop();}  /* 原生 TTS 无 pause，停止后保留位置 */
  resume(){}
  get supportsPause(){return false;}
}

function createEngine(){
  const cap=window.Capacitor;
  if(cap&&typeof cap.isNativePlatform==='function'&&cap.isNativePlatform()){
    const p=cap.Plugins?.TextToSpeech;
    if(p&&typeof p.speak==='function'){console.log('[TTS] 使用原生 Capacitor TTS');return new NativeEngine(p);}
    console.warn('[TTS] Capacitor 已检测但找不到 TextToSpeech 插件');
  }
  if('speechSynthesis' in window){console.log('[TTS] 使用 Web Speech API');return new WebSpeechEngine();}
  return null;
}

/* ---- TTSDock ---- */
class TTSDock{
  constructor(){
    this.engine=createEngine();
    if(!this.engine){
      window.TTS_SUPPORTED=false;
      setTimeout(()=>{if('speechSynthesis' in window){this.engine=new WebSpeechEngine();window.TTS_SUPPORTED=true;document.querySelectorAll('#tts-toggle-chips .chip').forEach(c=>{c.classList.remove('disabled');c.style.opacity='';});}},1500);
      document.getElementById('tts-dock')?.setAttribute('data-visible','false');
      return;
    }
    window.TTS_SUPPORTED=true;
    this.sentences=[];this.index=0;
    this.playing=false;this.paused=false;this.continuous=false;
    this.rate=1;this.pitch=1;this.volume=1;
    this._dragging=false;this._lastSpokenIndex=-1;
    this._segmented=false;this._wasPlayingBeforeDrag=false;
    this.presegment=document.getElementById('reader-content')?.dataset.presegment==='true';
    this.restore();this.cache();this.bind();
    if(this.presegment){this.segmentDocument();this.collect();}
    else{window.addEventListener('tts-lazy-segment',()=>this.lazySegment(),{once:true});}
    this.updateAll();
  }
  lazySegment(){if(this._segmented)return;this.segmentDocument();this.collect();}
  restore(){try{const s=JSON.parse(localStorage.getItem('tts.dock.settings')||'{}');this.rate=s.rate??1;this.pitch=s.pitch??1;this.volume=s.volume??1;this.continuous=s.continuous??false;}catch(e){}}
  save(){localStorage.setItem('tts.dock.settings',JSON.stringify({rate:this.rate,pitch:this.pitch,volume:this.volume,continuous:this.continuous}));}
  cache(){this.dock=document.getElementById('tts-dock');this.btnPrev=document.getElementById('tts-btn-prev');this.btnPlay=document.getElementById('tts-btn-play');this.btnNext=document.getElementById('tts-btn-next');this.btnStop=document.getElementById('tts-btn-stop');this.btnMode=document.getElementById('tts-btn-mode');this.btnClose=document.getElementById('tts-btn-close');this.bar=document.getElementById('tts-progress-bar');this.fill=document.getElementById('tts-progress-fill');this.handle=document.getElementById('tts-progress-handle');this.text=document.getElementById('tts-progress-text');}
  bind(){
    this.btnPlay?.addEventListener('click',()=>this.togglePlay());
    this.btnPrev?.addEventListener('click',()=>this.previous());
    this.btnNext?.addEventListener('click',()=>this.next());
    this.btnStop?.addEventListener('click',()=>this.stop());
    this.btnMode?.addEventListener('click',()=>{this.continuous=!this.continuous;this.updateMode();this.save();});
    this.btnClose?.addEventListener('click',()=>{this.stop();this.dock.setAttribute('data-visible','false');try{const r=JSON.parse(localStorage.getItem('reader.settings.v3.6.3')||'{}');r.ttsVisible=false;localStorage.setItem('reader.settings.v3.6.3',JSON.stringify(r));document.querySelectorAll('#tts-toggle-chips .chip').forEach(ch=>{if(ch.dataset.tts==='show')ch.classList.remove('active');if(ch.dataset.tts==='hide')ch.classList.add('active');});}catch(e){}});
    this.bar?.addEventListener('click',e=>{if(this._dragging)return;this._seek(e,true);});
    const startDrag=e=>{if(!this.sentences.length)return;this._dragging=true;this._wasPlayingBeforeDrag=this.playing;if(this.playing||this.paused){this.engine.stop();this.playing=false;this.paused=false;}this._seek(e,false);document.addEventListener('mousemove',moveDrag);document.addEventListener('mouseup',endDrag);document.addEventListener('touchmove',moveDrag,{passive:false});document.addEventListener('touchend',endDrag);};
    const moveDrag=e=>{if(!this._dragging)return;e.preventDefault();this._seek(e,false);};
    const endDrag=()=>{if(!this._dragging)return;this._dragging=false;document.removeEventListener('mousemove',moveDrag);document.removeEventListener('mouseup',endDrag);document.removeEventListener('touchmove',moveDrag);document.removeEventListener('touchend',endDrag);if(this._wasPlayingBeforeDrag){this.playing=true;this.paused=false;this.speakCurrent();}else{this.highlightCurrent();this.updateProgress();}};
    this.bar?.addEventListener('mousedown',startDrag);this.handle?.addEventListener('mousedown',startDrag);
    this.bar?.addEventListener('touchstart',startDrag,{passive:false});this.handle?.addEventListener('touchstart',startDrag,{passive:false});
    document.addEventListener('keydown',e=>{if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName))return;if(e.key===' '){e.preventDefault();this.togglePlay();}else if(e.key==='Escape'){this.stop();}});
    document.addEventListener('visibilitychange',()=>{if(document.hidden&&this.playing)this.pause();});
  }
  _clientX(e){return e.touches&&e.touches.length?e.touches[0].clientX:e.clientX;}
  _seek(e,play){
    if(!this.sentences.length)return;
    const rect=this.bar.getBoundingClientRect();
    let pct=(this._clientX(e)-rect.left)/rect.width;pct=Math.min(1,Math.max(0,pct));
    this.index=Math.round(pct*(this.sentences.length-1));
    if(play&&(this.playing||this.paused)){this.engine.stop();setTimeout(()=>this.speakCurrent(),60);}
    else{this.highlightCurrent();this.updateProgress();}
  }
  segmentDocument(){
    const root=document.getElementById('reader-content');if(!root||root.dataset.ttsSegmented==='true')return;
    const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:n=>{if(!n.parentElement)return NodeFilter.FILTER_REJECT;if(['SCRIPT','STYLE','NOSCRIPT'].includes(n.parentElement.tagName))return NodeFilter.FILTER_REJECT;if(!n.textContent.trim())return NodeFilter.FILTER_REJECT;return NodeFilter.FILTER_ACCEPT;}});
    let node;const nodes=[];while(node=walker.nextNode())nodes.push(node);
    const splitter=/([^。！？!?；;…]*[。！？!?；;…]|[^。！？!?；;…]+$)/g;let idx=0;
    nodes.forEach(tn=>{const parts=tn.textContent.match(splitter);if(!parts)return;const frag=document.createDocumentFragment();parts.forEach(p=>{const s=p.trim();if(!s)return;const sp=document.createElement('span');sp.className='tts-sentence';sp.dataset.ttsIndex=String(idx++);sp.textContent=s;frag.appendChild(sp);});tn.parentNode.replaceChild(frag,tn);});
    root.dataset.ttsSegmented='true';this._segmented=true;
  }
  collect(){this.sentences=[...document.querySelectorAll('#reader-content .tts-sentence')].map(sp=>({el:sp,text:sp.textContent}));this.updateProgress();}
  togglePlay(){this.playing?this.pause():this.play();}
  play(){
    if(!this._segmented){this.segmentDocument();this.collect();}
    if(!this.sentences.length)return;
    if(this.paused&&this.engine.supportsPause){this.engine.resume();this.paused=false;this.playing=true;this.updateAll();return;}
    this.playing=true;this.paused=false;this.updateAll();this.speakCurrent();
  }
  pause(){
    if(!this.playing)return;
    this.engine.pause();
    this.playing=false;this.paused=true;this.updateAll();
  }
  stop(){this.engine.stop();this.playing=false;this.paused=false;this.index=0;this._lastSpokenIndex=-1;this.clearHighlight();this.updateAll();}
  previous(){this.index=Math.max(0,this.index-1);if(this.playing||this.paused){this.engine.stop();this.playing=true;this.paused=false;setTimeout(()=>this.speakCurrent(),60);}else{this.highlightCurrent();this.updateProgress();}}
  next(){this.index=Math.min(this.sentences.length-1,this.index+1);if(this.playing||this.paused){this.engine.stop();this.playing=true;this.paused=false;setTimeout(()=>this.speakCurrent(),60);}else{this.highlightCurrent();this.updateProgress();}}
  async speakCurrent(){
    if(!this.sentences.length){this.stop();return;}
    if(this.index>=this.sentences.length){
      if(this.continuous&&window.PAGE_INFO?.nextPage){setTimeout(()=>window.location.href=window.PAGE_INFO.nextPage,600);}else{this.stop();}
      return;
    }
    const myIndex=this.index;
    const seg=this.sentences[myIndex];
    this.highlightElement(seg.el);this.updateProgress();
    this._lastSpokenIndex=myIndex;
    try{
      await this.engine.speak(seg.text,this.rate,this.pitch,this.volume);
    }catch(e){
      if(!this.playing)return;
      this.index++;setTimeout(()=>this.speakCurrent(),120);return;
    }
    if(!this.playing||this.index!==myIndex)return;
    this.index++;setTimeout(()=>this.speakCurrent(),40);
  }
  highlightElement(el){this.clearHighlight();if(!el)return;el.classList.add('tts-active');const r=el.getBoundingClientRect(),vh=window.innerHeight;if(r.top<80||r.bottom>vh-120){el.scrollIntoView({behavior:'smooth',block:'center'});}}
  highlightCurrent(){const seg=this.sentences[this.index];if(seg)this.highlightElement(seg.el);}
  clearHighlight(){document.querySelectorAll('.tts-active').forEach(e=>e.classList.remove('tts-active'));}
  updateProgress(){if(!this.sentences.length){this.fill&&(this.fill.style.width='0%');this.handle&&(this.handle.style.left='0%');this.text&&(this.text.textContent='0 / 0');return;}if(this.sentences.length===1){this.fill&&(this.fill.style.width='100%');this.handle&&(this.handle.style.left='100%');this.text&&(this.text.textContent='1 / 1');return;}const pct=(this.index/(this.sentences.length-1))*100;this.fill&&(this.fill.style.width=pct+'%');this.handle&&(this.handle.style.left=pct+'%');this.text&&(this.text.textContent=`${this.index+1} / ${this.sentences.length}`);}
  updateMode(){if(this.btnMode)this.btnMode.textContent=this.continuous?'🔁':'🔂';}
  updateButtons(){const disabled=window.TTS_SUPPORTED===false;[this.btnPrev,this.btnPlay,this.btnNext,this.btnStop,this.btnMode].forEach(b=>{if(b)b.disabled=disabled;});}
  updateAll(){if(this.btnPlay)this.btnPlay.textContent=this.playing?'⏸️':'▶️';this.updateMode();this.updateProgress();this.updateButtons();}
}
document.addEventListener('DOMContentLoaded',()=>{window._ttsDock=new TTSDock();});
"""

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
        if(res && res.ok){await cache.put(new Request(asset),res.clone());okCount++;}
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
  const cached=await cache.match(req);
  const fetchPromise=fetch(req).then(r=>{
    if(r && r.ok) cache.put(req,r.clone());
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
          Promise.all(targets.pageTargets.map(p => pageCache.match(p))).then(rs => rs.filter(Boolean).length),
          Promise.all(targets.staticTargets.map(p => staticCache.match(p))).then(rs => rs.filter(Boolean).length),
          Promise.all(targets.otherTargets.map(p => otherCache.match(p))).then(rs => rs.filter(Boolean).length),
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
