# -*- coding: utf-8 -*-
"""Reader Core JS"""

READER_JS = r"""
/* Reader Core v3.6.7 – smooth transitions + swipe + dynamic nav (toc fix) */
(() => {

const APP_VER = '3.6.7';
const LS_KEY = 'reader.settings.v3.6.3';
const SCROLL_PREFIX = 'reader.scroll.';

const FONT_FAMILIES = {
  sans:     '-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,"Helvetica Neue",Arial,"Microsoft YaHei","Noto Sans CJK SC",sans-serif',
  serif:    '"Noto Serif SC","Source Serif 4",Georgia,"Times New Roman",serif',
  dyslexic: '"OpenDyslexic",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,"Helvetica Neue",Arial,"Microsoft YaHei","Noto Sans CJK SC",sans-serif',
};

const st = { fontSize: 18, lineHeight: 1.65, font: 'sans', theme: 'auto', ttsVisible: false };

let lastScrollY = 0, hideTimer = null, installPromptEvt = null,
    overrideStyle = null, scrollSaveTimer = null;

const pageCache = new Map();
const historyStackLimit = parseInt(localStorage.getItem('historyCacheSize') || '50', 10);
let currentURL = location.href;
const LAST_PAGE_KEY = 'reader.lastPage.v1';
const SESSION_SEEN_KEY = 'reader.session.seen.v1';

function getCurrentPageFile() {
  const cur = window.PAGE_INFO?.current;
  if (typeof cur !== 'number' || cur < 0) return null;
  return 'page_' + String(cur).padStart(4, '0') + '.htm';
}

function saveLastReadPage(explicitHref) {
  try {
    const href = explicitHref || getCurrentPageFile();
    if (!href) return;
    localStorage.setItem(LAST_PAGE_KEY, href);
  } catch (_) {}
}

function bindLastReadPagePersistence() {
  const persist = () => saveLastReadPage();
  window.addEventListener('pagehide', persist);
  window.addEventListener('beforeunload', persist);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') persist();
  });
}

function markSessionSeenAndCheckFirst() {
  try {
    const seen = sessionStorage.getItem(SESSION_SEEN_KEY) === '1';
    if (!seen) sessionStorage.setItem(SESSION_SEEN_KEY, '1');
    return !seen;
  } catch (_) {
    return true;
  }
}

function resumeLastReadPageIfNeeded(firstInSession) {
  const p = location.pathname;
  const isIndex = p === '/' || p.endsWith('/index.html') || p.endsWith('/index.htm');
  if (!isIndex) return false;

  // 同一会话中，从正文页点“目录”会带 from 参数，此时不自动跳回，避免打断看目录。
  const qs = new URLSearchParams(location.search);
  if (!firstInSession && qs.has('from')) return false;

  try {
    const last = localStorage.getItem(LAST_PAGE_KEY);
    if (!last || !/^page_\d{4}\.htm$/.test(last)) return false;
    const currentFile = (p.split('/').pop() || '').toLowerCase();
    if (currentFile === last.toLowerCase()) return false;
    location.replace(last);
    return true;
  } catch (_) {
    return false;
  }
}

/* ---- 调试日志 ---- */
function logNav(...a)   { if (localStorage.getItem('navDebug')   === '1') console.log('[NAV]',   ...a); }
function logSwipe(...a) { if (localStorage.getItem('swipeDebug') === '1') console.log('[SWIPE]', ...a); }

/* ---- 设置存取 ---- */
function loadSettings() {
  try { Object.assign(st, JSON.parse(localStorage.getItem(LS_KEY) || '{}')); } catch (e) {}
}
function saveSettings() {
  localStorage.setItem(LS_KEY, JSON.stringify(st));
}

/* ---- 字体覆盖（含 EPUB 内联样式） ---- */
function ensureOverrideStyle() {
  if (!overrideStyle) {
    overrideStyle = document.createElement('style');
    overrideStyle.id = 'font-override';
    document.head.appendChild(overrideStyle);
  }
  const ff = FONT_FAMILIES[st.font] || FONT_FAMILIES.sans;
  overrideStyle.textContent = `body,#reader-content,.tts-sentence,#reader-content *{font-family:${ff} !important;}`;
}

/* ---- 主题切换 ---- */
function applyTheme() {
  const html = document.documentElement;
  html.classList.remove('eyecare');
  if (st.theme === 'eyecare') html.classList.add('eyecare');
  html.setAttribute('data-theme', st.theme);
  /* 沉浸式状态栏：让系统状态栏与页面背景同色 */
  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) metaTheme.setAttribute('content', st.theme === 'eyecare' ? '#c7dfc5' : '#ffffff');
}

/* ---- 同步 chip 选中状态 ---- */
function syncChips() {
  document.querySelectorAll('#font-family-choices .chip').forEach(ch =>
    ch.classList.toggle('active', ch.dataset.font === st.font));
  document.querySelectorAll('#theme-choices .chip').forEach(ch =>
    ch.classList.toggle('active', ch.dataset.theme === st.theme));

  const showBtn = document.querySelector('#tts-toggle-chips [data-tts=show]');
  const hideBtn = document.querySelector('#tts-toggle-chips [data-tts=hide]');
  if (showBtn && hideBtn) {
    showBtn.classList.toggle('active',  st.ttsVisible);
    hideBtn.classList.toggle('active', !st.ttsVisible);
  }
  if (window.TTS_SUPPORTED === false) {
    document.querySelectorAll('#tts-toggle-chips .chip').forEach(c => {
      c.classList.add('disabled');
      c.style.opacity = '.45';
    });
  }

  const fsLabel = document.getElementById('font-size-label');
  if (fsLabel) fsLabel.textContent = st.fontSize + 'px';
  const lhLabel = document.getElementById('line-height-label');
  if (lhLabel) lhLabel.textContent = st.lineHeight.toFixed(2);
}

/* ---- 应用所有设置 ---- */
function applySettings() {
  document.documentElement.style.setProperty('--fs-base', st.fontSize + 'px');
  document.documentElement.style.setProperty('--lh-base', st.lineHeight);
  document.documentElement.dataset.font = st.font;
  applyTheme();
  ensureOverrideStyle();
  syncChips();
  toggleTTSVisibility(st.ttsVisible, false);
}

/* ---- 设置面板控件绑定 ---- */
function initControls() {
  // 字号滑块
  const fs = document.getElementById('font-size-range');
  fs && fs.addEventListener('input', () => {
    st.fontSize = parseInt(fs.value, 10);
    applySettings(); saveSettings();
  });

  // 行高滑块
  const lh = document.getElementById('line-height-range');
  lh && lh.addEventListener('input', () => {
    st.lineHeight = parseFloat(lh.value);
    applySettings(); saveSettings();
  });

  // 字体 chips
  document.querySelectorAll('#font-family-choices .chip').forEach(ch =>
    ch.addEventListener('click', () => { st.font = ch.dataset.font; applySettings(); saveSettings(); }));

  // 主题 chips
  document.querySelectorAll('#theme-choices .chip').forEach(ch =>
    ch.addEventListener('click', () => { st.theme = ch.dataset.theme; applySettings(); saveSettings(); }));

  // TTS 显示 chips
  document.querySelectorAll('#tts-toggle-chips .chip').forEach(ch =>
    ch.addEventListener('click', () => {
      if (window.TTS_SUPPORTED === false) { alert('该设备不支持朗读功能'); return; }
      st.ttsVisible = (ch.dataset.tts === 'show');
      toggleTTSVisibility(st.ttsVisible, true);
      saveSettings(); syncChips();
    }));

  // 设置面板开关
  const panel   = document.getElementById('settings-panel');
  const openBtn = document.getElementById('open-settings');
  const closeBtn = document.getElementById('close-settings');

  let _cachePoller = null;

  function queryCacheInfo() {
    if (!('serviceWorker' in navigator)) return;
    navigator.serviceWorker.getRegistration().then(reg => {
      if (!reg || !reg.active) return;
      const ch = new MessageChannel();
      ch.port1.onmessage = ev => {
        const info      = ev.data || {};
        const infoBox   = document.getElementById('cache-info');
        const pctEl     = document.getElementById('cache-pct');
        const fillEl    = document.getElementById('cache-progress-fill');
        const statusBox = document.getElementById('cache-status-box');
        if (statusBox) statusBox.style.display = 'block';
        if (!info.available) {
          if (infoBox) infoBox.textContent = 'Service Worker 未就绪';
          return;
        }
        const total  = (info.pages?.total  || 0) + (info.statics?.total  || 0) + (info.others?.total  || 0);
        const cached = (info.pages?.cached || 0) + (info.statics?.cached || 0) + (info.others?.cached || 0);
        const pct    = total > 0 ? Math.min(100, Math.round(cached / total * 100)) : 0;
        if (infoBox) infoBox.textContent = `版本 ${info.version || '-'}  缓存 ${cached}/${total}`;
        if (pctEl)   pctEl.textContent   = pct + '%';
        if (fillEl)  fillEl.style.width  = pct + '%';
      };
      reg.active.postMessage({ type: 'CACHE_INFO' }, [ch.port2]);
    }).catch(() => {});
  }

  function startCachePoller() {
    queryCacheInfo();
    _cachePoller = setInterval(queryCacheInfo, 2000);
  }

  function stopCachePoller() {
    if (_cachePoller) { clearInterval(_cachePoller); _cachePoller = null; }
  }

  function closePanel() {
    panel.setAttribute('data-open',   'false');
    panel.setAttribute('aria-hidden', 'true');
    stopCachePoller();
  }

  openBtn && openBtn.addEventListener('click', () => {
    panel.setAttribute('data-open',   'true');
    panel.setAttribute('aria-hidden', 'false');
    startCachePoller();
  });

  closeBtn && closeBtn.addEventListener('click', () => closePanel());

  document.addEventListener('click', e => {
    if (panel && panel.getAttribute('data-open') === 'true'
        && !panel.contains(e.target) && e.target !== openBtn) {
      closePanel();
    }
  });
}

/* ---- TTS Dock 可见性 ---- */
function isPageView() {
  /* 只有 page_XXXX.htm 正文页的 current >= 0，目录页为 -1 */
  return !!(window.PAGE_INFO && typeof window.PAGE_INFO.current === 'number' && window.PAGE_INFO.current >= 0);
}
function toggleTTSVisibility(show) {
  const dock = document.getElementById('tts-dock');
  if (!dock) return;
  if (window.TTS_SUPPORTED === false || !isPageView()) { dock.setAttribute('data-visible', 'false'); return; }
  dock.setAttribute('data-visible', show ? 'true' : 'false');
}

/* ---- 滚动处理 ---- */
function handleScroll() {
  const y = window.scrollY || document.documentElement.scrollTop;
  const appBar = document.querySelector('.app-bar');
  if (appBar) {
    const goingDown = y > lastScrollY;
    if (y > 120 && goingDown) appBar.setAttribute('data-hidden', 'true');
    else                      appBar.removeAttribute('data-hidden');
  }
  lastScrollY = y;
  updateProgress();
  toggleBackTop(y);
  scheduleBarShow();
}

function scheduleBarShow() {
  const appBar = document.querySelector('.app-bar');
  clearTimeout(hideTimer);
  hideTimer = setTimeout(() => appBar && appBar.removeAttribute('data-hidden'), 1600);
}

function updateProgress() {
  const bar     = document.getElementById('top-progress');
  const content = document.getElementById('reader-content');
  if (!bar || !content) return;
  const scrolled = window.scrollY || document.documentElement.scrollTop;
  const h = content.scrollHeight - window.innerHeight;
  bar.style.width = (h > 0 ? (scrolled / h) * 100 : 0) + '%';
}

function toggleBackTop(y) {
  const btn = document.getElementById('back-top');
  if (!btn) return;
  if (y > 360) btn.classList.add('show');
  else         btn.classList.remove('show');
}

function initBackTop() {
  const btn = document.getElementById('back-top');
  btn && btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

/* ---- 滚动位置保存/恢复（已禁用） ---- */
function saveScrollThrottle() {}
function saveScrollImmediate() {}
function restoreScroll() {}

/* ---- 键盘导航 ---- */
function initKeys() {
  document.addEventListener('keydown', e => {
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
    if (e.key === 'ArrowLeft'  && window.PAGE_INFO?.prevPage) customNavigate(window.PAGE_INFO.prevPage, 'prev');
    if (e.key === 'ArrowRight' && window.PAGE_INFO?.nextPage) customNavigate(window.PAGE_INFO.nextPage, 'next');
  });
}

/* ---- 杂项初始化 ---- */
function motionPref() {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches)
    document.documentElement.classList.add('reduce-motion');
}

function systemThemeWatcher() {
  const mq = window.matchMedia('(prefers-color-scheme: dark)');
  mq.addEventListener('change', () => { if (st.theme === 'auto') applyTheme(); });
}

/* ---- "今天读到"链接 ---- */
function initTodayLinks() {
  function toLocalDateText(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  function pickByTitleDate(mapObj, todayText) {
    const keys = Object.keys(mapObj || {}).filter(k => /^\d{4}-\d{2}-\d{2}$/.test(k)).sort();
    if (!keys.length) return null;
    if (Number.isFinite(Number(mapObj[todayText]))) {
      return Number(mapObj[todayText]);
    }
    // 若当天无匹配，回退到不晚于今天的最近日期
    let picked = null;
    for (const k of keys) {
      if (k <= todayText) picked = k;
      else break;
    }
    if (picked && Number.isFinite(Number(mapObj[picked]))) {
      return Number(mapObj[picked]);
    }
    return null;
  }

  document.querySelectorAll('.today-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const startDate  = link.dataset.startDate;
      const startIndex = parseInt(link.dataset.startIndex || '0', 10);
      const total      = parseInt(link.dataset.total || '0', 10);
      if (total <= 0) return;

      const todayText = toLocalDateText(new Date());
      const titleDateTarget = pickByTitleDate(window.PAGE_DATE_MAP || {}, todayText);
      if (Number.isInteger(titleDateTarget)) {
        let target = titleDateTarget;
        if (target < 0) target = 0;
        if (target > total - 1) target = total - 1;
        const url = 'page_' + String(target).padStart(4, '0') + '.htm';
        customNavigate(url, target > (window.PAGE_INFO?.current || 0) ? 'next' : 'prev');
        return;
      }

      if (!startDate) {
        alert('未找到标题日期映射，且未配置起始日期');
        return;
      }
      const parts = startDate.split('-').map(Number);
      if (parts.length !== 3) { alert('起始日期配置错误'); return; }
      const sDate = new Date(parts[0], parts[1] - 1, parts[2]);
      const now   = new Date();
      const diff  = Math.floor((now - sDate) / (1000 * 60 * 60 * 24));
      let target  = startIndex + diff;
      if (diff < 0) {
        alert('尚未到起始日期'); target = startIndex;
      } else if (target > total - 1) {
        alert('超出范围，跳最后一页'); target = total - 1;
      }
      if (target < 0) target = 0;
      const url = 'page_' + String(target).padStart(4, '0') + '.htm';
      customNavigate(url, target > (window.PAGE_INFO?.current || 0) ? 'next' : 'prev');
    });
  });
}

/* ---- 滑动翻页 ---- */
function initSwipe() {
  if (localStorage.getItem('disableSwipe') === '1') return;

  const baseX      = Math.round(window.innerWidth * 0.14);
  const THRESHOLD_X = parseInt(localStorage.getItem('swipeThresholdX') || String(Math.max(42, Math.min(88, baseX))), 10);
  const THRESHOLD_Y = parseInt(localStorage.getItem('swipeThresholdY') || '72', 10);
  const ANGLE_RATIO = parseFloat(localStorage.getItem('swipeAngleRatio') || '2.0');
  const MAX_TIME    = 850;
  const MIN_VELOCITY = parseFloat(localStorage.getItem('swipeMinVelocityPxMs') || '0.30');

  let startX = 0, startY = 0, startTime = 0, tracking = false, multi = false, moved = false;

  function panelOpen() {
    return document.getElementById('settings-panel')?.getAttribute('data-open') === 'true';
  }
  function inTTSDock(yClient) {
    const dock = document.getElementById('tts-dock');
    if (!dock) return false;
    return yClient >= dock.getBoundingClientRect().top;
  }
  function onStart(e) {
    if (e.touches && e.touches.length > 1) { multi = true; return; }
    multi = false;
    if (panelOpen()) return;
    const t = e.touches ? e.touches[0] : e;
    if (inTTSDock(t.clientY)) return;
    tracking = true; moved = false;
    startX = t.clientX; startY = t.clientY; startTime = Date.now();
  }
  function onMove(e) {
    if (!tracking || multi) return;
    const t = e.touches ? e.touches[0] : e;
    const dx = t.clientX - startX, dy = t.clientY - startY;
    if (Math.abs(dx) > 5 || Math.abs(dy) > 5) moved = true;
  }
  function onEnd(e) {
    if (!tracking || multi) { tracking = false; return; }
    tracking = false;
    const t       = e.changedTouches ? e.changedTouches[0] : e;
    const totalDx = t.clientX - startX, totalDy = t.clientY - startY;
    const dt      = Date.now() - startTime;
    const absDx   = Math.abs(totalDx), absDy = Math.abs(totalDy);
    const velocity = absDx / Math.max(dt, 1);
    logSwipe('end', { totalDx, totalDy, dt, velocity });
    if (!moved || dt > MAX_TIME) return;
    const sel = window.getSelection();
    if (sel && sel.toString().length > 0) return;
    if (absDy > THRESHOLD_Y) return;
    if (absDx < THRESHOLD_X && velocity < MIN_VELOCITY) return;
    if (absDx / (absDy + 1) < ANGLE_RATIO) return;
    if (totalDx > 0) { if (window.PAGE_INFO?.prevPage) customNavigate(window.PAGE_INFO.prevPage, 'prev'); }
    else             { if (window.PAGE_INFO?.nextPage) customNavigate(window.PAGE_INFO.nextPage, 'next'); }
  }

  document.addEventListener('touchstart',  onStart, { passive: true });
  document.addEventListener('touchmove',   onMove,  { passive: true });
  document.addEventListener('touchend',    onEnd,   { passive: true });
  document.addEventListener('pointerdown', e => { if (e.pointerType !== 'touch') return; onStart(e); });
  document.addEventListener('pointerup',   e => { if (e.pointerType !== 'touch') return; onEnd(e); });
}

/* ---- nav 按钮点击拦截 ---- */
document.addEventListener('click', e => {
  const a = e.target.closest('a.nav-btn');
  if (!a) return;
  const role = a.dataset.nav;
  if (role === 'prev' || role === 'next' || role === 'toc') {
    if (a.classList.contains('disabled')) return;
    const href = a.getAttribute('href');
    if (!href) return;
    e.preventDefault();
    customNavigate(href, role === 'next' ? 'next' : 'prev');
  }
});

/* ---- 更新导航栏按钮 ---- */
function updateNavBarByPageInfo(pageInfo) {
  if (!pageInfo) return;
  const nav = document.querySelector('.nav');
  if (!nav) return;

  let prevBtn = nav.querySelector('[data-nav="prev"]');
  let nextBtn = nav.querySelector('[data-nav="next"]');
  let tocBtn  = nav.querySelector('[data-nav="toc"]');
  if (!prevBtn) prevBtn = [...nav.querySelectorAll('a.nav-btn,span.nav-btn')].find(el => el.textContent.trim() === '←');
  if (!nextBtn) nextBtn = [...nav.querySelectorAll('a.nav-btn,span.nav-btn')].find(el => el.textContent.trim() === '→');
  if (!tocBtn)  tocBtn  = [...nav.querySelectorAll('a.nav-btn')].find(el => el.textContent.trim() === '目录');

  if (pageInfo.prevPage) {
    if (prevBtn && prevBtn.tagName === 'SPAN') {
      const a = document.createElement('a');
      a.className = 'nav-btn'; a.textContent = '←'; a.dataset.nav = 'prev';
      prevBtn.replaceWith(a); prevBtn = a;
    }
    if (prevBtn) {
      prevBtn.classList.remove('disabled');
      prevBtn.dataset.nav = 'prev';
      prevBtn.setAttribute('href', pageInfo.prevPage);
      prevBtn.removeAttribute('aria-hidden');
    }
  } else if (prevBtn) {
    prevBtn.classList.add('disabled');
    prevBtn.removeAttribute('href');
    prevBtn.setAttribute('aria-hidden', 'true');
    prevBtn.dataset.nav = 'prev';
  }

  if (pageInfo.nextPage) {
    if (nextBtn && nextBtn.tagName === 'SPAN') {
      const a = document.createElement('a');
      a.className = 'nav-btn'; a.textContent = '→'; a.dataset.nav = 'next';
      nextBtn.replaceWith(a); nextBtn = a;
    }
    if (nextBtn) {
      nextBtn.classList.remove('disabled');
      nextBtn.dataset.nav = 'next';
      nextBtn.setAttribute('href', pageInfo.nextPage);
      nextBtn.removeAttribute('aria-hidden');
    }
  } else if (nextBtn) {
    nextBtn.classList.add('disabled');
    nextBtn.removeAttribute('href');
    nextBtn.setAttribute('aria-hidden', 'true');
    nextBtn.dataset.nav = 'next';
  }

  if (tocBtn) {
    const correct = (pageInfo.current === -1) ? 'index.html' : ('index.html?from=' + pageInfo.current);
    if (tocBtn.getAttribute('href') != correct) tocBtn.setAttribute('href', correct);
    tocBtn.dataset.nav = 'toc';
  }
}

/* ---- 预取相邻页面 ---- */
function prefetchLink(url) {
  if (!url) return;
  if (localStorage.getItem('prefetchDisable') === '1') return;
  if (pageCache.has(url)) return;
  logNav('prefetch', url);
  fetch(url, { credentials: 'same-origin' })
    .then(r => { if (!r.ok) throw new Error(r.status); return r.text(); })
    .then(html => {
      const doc     = new DOMParser().parseFromString(html, 'text/html');
      const content = doc.querySelector('#reader-content');
      let pageInfo  = null;
      for (const s of doc.querySelectorAll('script')) {
        const txt = s.textContent || '';
        if (txt.includes('window.PAGE_INFO')) {
          try {
            const m = txt.match(/window\.PAGE_INFO\s*=\s*(\{[^;]+});/);
            if (m) { pageInfo = eval('(' + m[1] + ')'); break; }
          } catch (_) {}
        }
      }
      if (content && pageInfo) {
        pageCache.set(url, { doc, contentHTML: content.innerHTML, title: doc.title, pageInfo });
        trimCache();
      }
    })
    .catch(() => {});
}

function trimCache() {
  if (pageCache.size <= historyStackLimit) return;
  const firstKey = pageCache.keys().next().value;
  pageCache.delete(firstKey);
}

function installInitialPrefetch() {
  if (!window.PAGE_INFO) return;
  if (window.PAGE_INFO.prevPage) prefetchLink(new URL(window.PAGE_INFO.prevPage, location.href).href);
  if (window.PAGE_INFO.nextPage) prefetchLink(new URL(window.PAGE_INFO.nextPage, location.href).href);
}

/* ---- 页面导航 ---- */
function customNavigate(url, dir) {
  if (!url) return;
  const abs = new URL(url, location.href).href;
  smoothTransitionTo(abs, dir, true);
}

function smoothTransitionTo(url, dir = 'next', allowFetch = true) {
  if (pageCache.has(url)) { doPageSwap(url, pageCache.get(url), dir); return; }
  if (!allowFetch) { location.href = url; return; }
  fetch(url, { credentials: 'same-origin' })
    .then(r => { if (!r.ok) throw new Error(r.status); return r.text(); })
    .then(html => {
      const doc     = new DOMParser().parseFromString(html, 'text/html');
      const content = doc.querySelector('#reader-content');
      let pageInfo  = null;
      for (const s of doc.querySelectorAll('script')) {
        const txt = s.textContent || '';
        if (txt.includes('window.PAGE_INFO')) {
          try {
            const m = txt.match(/window\.PAGE_INFO\s*=\s*(\{[^;]+});/);
            if (m) { pageInfo = eval('(' + m[1] + ')'); break; }
          } catch (_) {}
        }
      }
      if (content && pageInfo) {
        const entry = { doc, contentHTML: content.innerHTML, title: doc.title, pageInfo };
        pageCache.set(url, entry); trimCache();
        doPageSwap(url, entry, dir);
      } else {
        location.href = url;
      }
    })
    .catch(() => location.href = url);
}

function doPageSwap(url, entry, dir) {
  saveScrollImmediate();
  /* 换页前停止 TTS，避免继续朗读旧页内容 */
  if (window._ttsDock && (window._ttsDock.playing || window._ttsDock.paused)) {
    window._ttsDock.stop();
  }
  const oldView = document.getElementById('reader-content');
  if (!oldView) { location.href = url; return; }

  const newNode = oldView.cloneNode(false);
  newNode.innerHTML      = entry.contentHTML;
  newNode.id             = 'reader-content';
  newNode.dataset.pageIndex = entry.pageInfo.current;
  oldView.replaceWith(newNode);

  document.title   = entry.title;
  window.PAGE_INFO = {
    current:  entry.pageInfo.current,
    total:    entry.pageInfo.total,
    prevPage: entry.pageInfo.prevPage,
    nextPage: entry.pageInfo.nextPage,
  };
  updateNavBarByPageInfo(window.PAGE_INFO);
  saveLastReadPage();
  if (url !== currentURL) { history.pushState({ url }, '', url); currentURL = url; }
  afterSwap(url, entry);
}

function ensurePageShell() {}

function afterSwap(url, entry) {
  scrollTo(0, 0);
  restoreScroll();
  updateProgress();
  installInitialPrefetch();
  reinitDynamicFeatures();
  /* 换页后重新扫描新页面的句子，并同步 TTS 栏可见性（仅正文页显示） */
  toggleTTSVisibility(st.ttsVisible);
  if (window._ttsDock) {
    window._ttsDock.index = 0;
    window._ttsDock.collectUnits();
  }
}

function reinitDynamicFeatures() {}

/* ---- History 后退 ---- */
window.addEventListener('popstate', () => {
  const target = location.href;
  if (pageCache.has(target)) doPageSwap(target, pageCache.get(target), 'prev');
  else                       smoothTransitionTo(target, 'prev', true);
});

/* ---- SW 禁用检测 ---- */
function initSWDisableCheck() {
  const urlParams = new URLSearchParams(location.search);
  if (urlParams.get('no-sw') === '1') {
    localStorage.setItem('disableSW', '1');
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.getRegistrations().then(rs => rs.forEach(r => r.unregister()));
    }
    console.log('[SW] 已禁用 (参数 no-sw=1)');
  }
}

/* ---- Android 后退键 ---- */
function isIndexPage() {
  const p = location.pathname;
  return p === '/' || p.endsWith('/index.html') || p.endsWith('/index.htm');
}

function initAndroidBack() {
  const cap = window.Capacitor;
  if (!cap || typeof cap.isNativePlatform !== 'function' || !cap.isNativePlatform()) return;
  const App = cap.Plugins && cap.Plugins.App;
  if (!App || typeof App.addListener !== 'function') return;

  App.addListener('backButton', () => {
    if (isIndexPage() || (window.PAGE_INFO && window.PAGE_INFO.current === -1)) {
      App.exitApp && App.exitApp();
    } else if (window.PAGE_INFO && window.PAGE_INFO.prevPage) {
      customNavigate(window.PAGE_INFO.prevPage, 'prev');
    } else {
      App.exitApp && App.exitApp();
    }
  });
}

/* ---- 入口 ---- */
document.addEventListener('DOMContentLoaded', () => {
  const firstInSession = markSessionSeenAndCheckFirst();
  if (resumeLastReadPageIfNeeded(firstInSession)) return;
  initSWDisableCheck();
  bindLastReadPagePersistence();
  loadSettings();
  applySettings();
  initControls();
  initBackTop();
  initKeys();
  motionPref();
  systemThemeWatcher();
  restoreScroll();
  updateProgress();
  initTodayLinks();
  initSwipe();
  installInitialPrefetch();
  updateNavBarByPageInfo(window.PAGE_INFO);
  saveLastReadPage();
  initAndroidBack();
});

window.addEventListener('scroll', () => { handleScroll(); }, { passive: true });

})();
"""
