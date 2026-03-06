# -*- coding: utf-8 -*-
"""APK 自更新 JS"""

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
