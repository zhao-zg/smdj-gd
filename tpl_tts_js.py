# -*- coding: utf-8 -*-
"""TTS JS（Capacitor 原生 + Web Speech API）"""

# ================== TTS JS – native Capacitor TTS + Web Speech API fallback ==================
TTS_JS = r"""
/* 句级 TTS v6.0 – 句子朗读 + Range 句级高亮（不预改 DOM） */

/* ---- 语音引擎适配器 ---- */
class WebSpeechEngine {
  constructor() {
    this.synth = window.speechSynthesis;
    this.voice = null;
    this._retry = 0;
    const load = () => {
      const vs = this.synth.getVoices();
      if (vs && vs.length) {
        this.voice = vs.find(v => /^zh/i.test(v.lang)) || vs.find(v => /Chinese/i.test(v.name)) || vs[0];
      } else {
        this._retry++;
        setTimeout(load, Math.min(5000, 500 + this._retry * 250));
      }
    };
    if ('onvoiceschanged' in this.synth) this.synth.onvoiceschanged = load;
    load();
  }
  speak(text, rate, pitch, volume) {
    return new Promise((resolve, reject) => {
      const u = new SpeechSynthesisUtterance(text);
      u.lang = 'zh-CN';
      if (this.voice) u.voice = this.voice;
      u.rate = rate; u.pitch = pitch; u.volume = volume;
      u.onend = () => resolve();
      u.onerror = e => {
        if (e.error === 'interrupted' || e.error === 'canceled') resolve();
        else reject(e);
      };
      this.synth.speak(u);
    });
  }
  stop()   { this.synth.cancel(); }
  pause()  { this.synth.pause(); }
  resume() { this.synth.resume(); }
  get supportsPause() { return true; }
}

class NativeEngine {
  constructor(p) { this.p = p; }
  speak(text, rate, pitch, volume) {
    return this.p.speak({ text, lang: 'zh-CN', rate, pitch, volume, category: 'ambient' });
  }
  stop()   { return this.p.stop().catch(() => {}); }
  pause()  { return this.stop(); }
  resume() {}
  get supportsPause() { return false; }
}

function createEngine() {
  const cap = window.Capacitor;
  if (cap && typeof cap.isNativePlatform === 'function' && cap.isNativePlatform()) {
    const p = cap.Plugins?.TextToSpeech;
    if (p && typeof p.speak === 'function') { console.log('[TTS] 使用原生 Capacitor TTS'); return new NativeEngine(p); }
    console.warn('[TTS] Capacitor 已检测但找不到 TextToSpeech 插件');
  }
  if ('speechSynthesis' in window) { console.log('[TTS] 使用 Web Speech API'); return new WebSpeechEngine(); }
  return null;
}

/* ---- TTSDock ---- */
class TTSDock {
  constructor() {
    this.engine = createEngine();
    if (!this.engine) {
      window.TTS_SUPPORTED = false;
      setTimeout(() => {
        if ('speechSynthesis' in window) {
          this.engine = new WebSpeechEngine();
          window.TTS_SUPPORTED = true;
          document.querySelectorAll('#tts-toggle-chips .chip').forEach(c => { c.classList.remove('disabled'); c.style.opacity = ''; });
        }
      }, 1500);
      document.getElementById('tts-dock')?.setAttribute('data-visible', 'false');
      return;
    }
    window.TTS_SUPPORTED = true;
    this.units = [];   /* { el, text } – 句子单元 */
    this.index = 0;
    this.playing = false;
    this.paused  = false;
    this.rate = 1; this.pitch = 1; this.volume = 1;
    this._dragging = false;
    this._activeMark = null;  /* 当前高亮的 <mark> 元素 */
    this._tok = null;        /* 当前播放 token，用于取消旧协程 */
    this.restore();
    this.cache();
    this.bind();
    this.collectUnits();
    this.updateAll();
  }

  /* 将块级元素文本拆成句子，每句作为一个朗读单元 */
  collectUnits() {
    const root = document.getElementById('reader-content');
    if (!root) return;
    this.units = [];
    const RE = /[^。！？!?；;…\n]+[。！？!?；;…]?/g;
    root.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, blockquote, td, th').forEach(el => {
      const full = el.textContent.trim();
      if (!full) return;
      const parts = full.match(RE) || [full];
      parts.forEach(s => { s = s.trim(); if (s) this.units.push({ el, text: s }); });
    });
    this.updateProgress();
  }

  /* 用 Range 在 el 内包住 text，插入 <mark class="tts-active"> */
  _wrapSentence(el, text) {
    try {
      /* 在 el.textContent 全文中定位句子的字符偏移 */
      const full = el.textContent;
      const start = full.indexOf(text);
      if (start === -1) { el.classList.add('tts-active'); return null; }
      const end = start + text.length;

      /* 将字符偏移映射回具体的文本节点 */
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      const range = document.createRange();
      let node, off = 0, startSet = false;
      while ((node = walker.nextNode())) {
        const len = node.textContent.length;
        if (!startSet && off + len > start) {
          range.setStart(node, start - off);
          startSet = true;
        }
        if (startSet && off + len >= end) {
          range.setEnd(node, end - off);
          break;
        }
        off += len;
      }
      if (!startSet) { el.classList.add('tts-active'); return null; }

      /* extractContents + insertNode 支持跨内联元素的 range，不会抛异常 */
      const mark = document.createElement('mark');
      mark.className = 'tts-active';
      mark.appendChild(range.extractContents());
      range.insertNode(mark);
      this._activeMark = mark;
      return mark;
    } catch (_) {
      el.classList.add('tts-active');
      return null;
    }
  }

  /* 拆除 <mark>，把子节点原地还原 */
  _unwrapMark() {
    if (!this._activeMark) return;
    const children = [...this._activeMark.childNodes];
    this._activeMark.replaceWith(...children);
    this._activeMark = null;
  }

  restore() {
    try {
      const s = JSON.parse(localStorage.getItem('tts.dock.settings') || '{}');
      this.rate = s.rate ?? 1; this.pitch = s.pitch ?? 1; this.volume = s.volume ?? 1;
    } catch (e) {}
  }
  save() {
    localStorage.setItem('tts.dock.settings', JSON.stringify({ rate: this.rate, pitch: this.pitch, volume: this.volume }));
  }

  cache() {
    this.dock     = document.getElementById('tts-dock');
    this.btnPlay  = document.getElementById('tts-btn-play');
    this.btnRate  = document.getElementById('tts-rate-btn');
    this.menuRate  = document.getElementById('tts-rate-menu');
    this.btnClose = document.getElementById('tts-btn-close');
    this.bar    = document.getElementById('tts-progress-bar');
    this.fill   = document.getElementById('tts-progress-fill');
    this.handle = document.getElementById('tts-progress-handle');
    this.text   = document.getElementById('tts-progress-text');
  }

  bind() {
    this.btnPlay?.addEventListener('click', () => this.togglePlay());
    this.btnRate?.addEventListener('click', e => {
      e.stopPropagation();
      const open = this.menuRate.dataset.open === 'true';
      this.menuRate.dataset.open = open ? 'false' : 'true';
    });
    this.menuRate?.querySelectorAll('li').forEach(li => {
      li.addEventListener('click', () => {
        this.rate = parseFloat(li.dataset.val);
        this.menuRate.dataset.open = 'false';
        this.save();
        this.updateRate();
        if (this.playing || this.paused) {
          this._tok = {};
          this.engine.stop();
          this._unwrapMark();
          this.playing = true; this.paused = false;
          this.updateAll();
          setTimeout(() => this.speakCurrent(), 60);
        } else { this.updateProgress(); }
      });
    });
    document.addEventListener('click', () => { if (this.menuRate) this.menuRate.dataset.open = 'false'; });
    this.btnClose?.addEventListener('click', () => {
      this.stop();
      this.dock.setAttribute('data-visible', 'false');
      try {
        const r = JSON.parse(localStorage.getItem('reader.settings.v3.6.3') || '{}');
        r.ttsVisible = false;
        localStorage.setItem('reader.settings.v3.6.3', JSON.stringify(r));
        document.querySelectorAll('#tts-toggle-chips .chip').forEach(ch => {
          if (ch.dataset.tts === 'show') ch.classList.remove('active');
          if (ch.dataset.tts === 'hide') ch.classList.add('active');
        });
      } catch (e) {}
    });

    this.bar?.addEventListener('click', e => { if (!this._dragging) this._seek(e, true); });

    const startDrag = e => {
      if (!this.units.length) return;
      this._dragging = true;
      if (this.playing || this.paused) { this._tok = {}; this.engine.stop(); this._unwrapMark(); this.playing = false; this.paused = false; this.updateAll(); }
      this._seek(e, false);
      document.addEventListener('mousemove',  moveDrag);
      document.addEventListener('mouseup',    endDrag);
      document.addEventListener('touchmove',  moveDrag, { passive: false });
      document.addEventListener('touchend',   endDrag);
    };
    const moveDrag = e => { if (!this._dragging) return; e.preventDefault(); this._seek(e, false); };
    const endDrag  = () => {
      if (!this._dragging) return;
      this._dragging = false;
      document.removeEventListener('mousemove',  moveDrag);
      document.removeEventListener('mouseup',    endDrag);
      document.removeEventListener('touchmove',  moveDrag);
      document.removeEventListener('touchend',   endDrag);
      this._tok = {}; this.playing = true; this.paused = false; this.updateAll(); this.speakCurrent();
    };
    this.bar?.addEventListener('mousedown',    startDrag);
    this.handle?.addEventListener('mousedown', startDrag);
    this.bar?.addEventListener('touchstart',    startDrag, { passive: false });
    this.handle?.addEventListener('touchstart', startDrag, { passive: false });

    document.addEventListener('keydown', e => {
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return;
      if (e.key === ' ')           { e.preventDefault(); this.togglePlay(); }
      else if (e.key === 'Escape') { this.stop(); }
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden && this.playing) this.pause(); });
    window.addEventListener('beforeunload', () => { this._tok = {}; this.engine?.stop(); });
    window.addEventListener('pagehide',     () => { this._tok = {}; this.engine?.stop(); });
  }

  _clientX(e) { return e.touches && e.touches.length ? e.touches[0].clientX : e.clientX; }

  _seek(e, play) {
    if (!this.units.length) return;
    const rect = this.bar.getBoundingClientRect();
    let pct = (this._clientX(e) - rect.left) / rect.width;
    pct = Math.min(1, Math.max(0, pct));
    this.index = Math.round(pct * (this.units.length - 1));
    if (play && (this.playing || this.paused)) { this._tok = {}; this.engine.stop(); this._unwrapMark(); this.updateAll(); setTimeout(() => this.speakCurrent(), 60); }
    else { this.updateProgress(); }
  }

  togglePlay() { this.playing ? this.pause() : this.play(); }

  play() {
    if (!this.units.length) return;
    if (this.paused && this.engine.supportsPause) {
      this.engine.resume(); this.paused = false; this.playing = true; this.updateAll(); return;
    }
    this.playing = true; this.paused = false; this.updateAll(); this.speakCurrent();
  }

  pause() {
    if (!this.playing) return;
    this.engine.pause();
    this.playing = false; this.paused = true; this.updateAll();
  }

  stop() {
    this._tok = {};  /* 使任何正在运行的 speakCurrent 失效 */
    this.engine.stop();
    this.playing = false; this.paused = false; this.index = 0;
    this.clearHighlight();
    this.updateAll();
  }

  async speakCurrent() {
    if (!this.units.length) { this.stop(); return; }
    if (this.index >= this.units.length) {
      if (window.PAGE_INFO?.nextPage) {
        setTimeout(() => window.location.href = window.PAGE_INFO.nextPage, 600);
      } else {
        this.stop();
      }
      return;
    }

    const tok = (this._tok = {});  /* 每次启动生成新 token */
    const myIndex = this.index;
    const unit = this.units[myIndex];

    this.clearHighlight();
    const mark = this._wrapSentence(unit.el, unit.text);

    /* 滚动高亮区入视野 */
    const scrollEl = mark || unit.el;
    const r = scrollEl.getBoundingClientRect(), vh = window.innerHeight;
    if (r.top < 80 || r.bottom > vh - 120) {
      scrollEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    this.updateProgress();

    try {
      await this.engine.speak(unit.text, this.rate, this.pitch, this.volume);
    } catch (e) {
      this._unwrapMark();
      if (tok !== this._tok || !this.playing) return;
      this.index++;
      setTimeout(() => this.speakCurrent(), 120);
      return;
    }

    if (tok !== this._tok || !this.playing) { this._unwrapMark(); return; }

    this._unwrapMark();
    this.index++;
    setTimeout(() => this.speakCurrent(), 40);
  }

  clearHighlight() {
    this._unwrapMark();
    document.querySelectorAll('mark.tts-active').forEach(e => {
      const children = [...e.childNodes]; e.replaceWith(...children);
    });
    document.querySelectorAll('.tts-active').forEach(e => e.classList.remove('tts-active'));
  }

  _fmt(sec) {
    sec = Math.max(0, Math.round(sec));
    const m = Math.floor(sec / 60), s = sec % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  updateProgress() {
    const n = this.units.length;
    if (!n) {
      this.fill   && (this.fill.style.width  = '0%');
      this.handle && (this.handle.style.left = '0%');
      this.text   && (this.text.textContent  = '0:00 / 0:00');
      return;
    }
    const pct = n === 1 ? 100 : (this.index / (n - 1)) * 100;
    this.fill   && (this.fill.style.width  = pct + '%');
    this.handle && (this.handle.style.left = pct + '%');
    const CPS = 4.5;  /* 汉字/秒（rate=1 基准） */
    const elapsed = this.units.slice(0, this.index).reduce((s, u) => s + u.text.length, 0) / (CPS * this.rate);
    const total   = this.units.reduce((s, u) => s + u.text.length, 0) / (CPS * this.rate);
    this.text   && (this.text.textContent  = `${this._fmt(elapsed)} / ${this._fmt(total)}`);
  }

  updateRate() {
    if (this.btnRate) this.btnRate.textContent = this.rate + '×';
    if (this.menuRate) this.menuRate.querySelectorAll('li').forEach(li => {
      li.classList.toggle('active', parseFloat(li.dataset.val) === this.rate);
    });
  }
  updateButtons() {
    const disabled = window.TTS_SUPPORTED === false;
    [this.btnPlay, this.btnRate].forEach(b => { if (b) b.disabled = disabled; });
  }
  updateAll() {
    if (this.btnPlay) this.btnPlay.textContent = this.playing ? '⏸️' : '▶️';
    this.updateRate(); this.updateProgress(); this.updateButtons();
  }
}

document.addEventListener('DOMContentLoaded', () => { window._ttsDock = new TTSDock(); });
"""
