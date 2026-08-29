# -*- coding: utf-8 -*-
"""CSS 模板常量"""

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
  --c-accent2:#5b8dff;
  --c-border:#e3e5e8;
  --c-surface:#f7f9fa;
  --c-surface-high:#ffffff;
  --c-danger:#d61f3a;
  --safe-top:env(safe-area-inset-top);
  --safe-bottom:env(safe-area-inset-bottom);
  --app-bar-height:54px;
  --tts-dock-height:94px;
  --shadow-level:0 4px 22px -6px rgba(0,0,0,.22);
  --shadow-small:0 2px 4px rgba(0,0,0,.06);
  --transition-fast:.25s;
  --c-bar-bg:rgba(255,255,255,.82);
  --c-dock-bg:rgba(255,255,255,.92);
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
blockquote{margin:1.8rem 0;padding:1rem 1.2rem;background:linear-gradient(165deg,var(--c-surface),var(--c-bg));border-left:4px solid var(--c-accent);border-radius:0 8px 8px 0;position:relative;}
blockquote::before{content:"\201C";position:absolute;top:-10px;left:8px;font-size:3.5rem;line-height:1;color:rgba(var(--c-accent-rgb),.25);font-family:Georgia,serif;}
hr{border:none;height:1px;background:linear-gradient(to right,transparent,var(--c-border),transparent);margin:3rem 0;}
.app-bar{position:fixed;top:0;left:0;right:0;padding-top:var(--safe-top);background:var(--c-bar-bg);backdrop-filter:blur(14px) saturate(180%);border-bottom:1px solid rgba(0,0,0,.05);z-index:90;transform:translateY(0);transition:transform .4s,background .4s;}
.app-bar[data-hidden="true"]{transform:translateY(calc(-100% - 6px));}
.nav{max-width:980px;margin:0 auto;height:var(--app-bar-height);display:flex;align-items:center;justify-content:center;padding:0 clamp(14px,4vw,40px);position:relative;}
.nav-buttons{display:flex;align-items:center;gap:.6rem;}
.nav-settings{position:absolute;right:clamp(14px,4vw,40px);top:0;height:100%;display:flex;align-items:center;}
.nav-btn{background:var(--c-surface);border:1px solid var(--c-border);padding:.55rem .95rem;font-size:.85rem;border-radius:999px;color:var(--c-fg);cursor:pointer;font-weight:500;display:inline-flex;align-items:center;gap:.25rem;transition:background var(--transition-fast),border-color var(--transition-fast),color var(--transition-fast);}
.nav-btn.small{padding:.45rem .75rem;font-size:.75rem;}
.nav-btn:hover{background:var(--c-surface-high);border-color:var(--c-accent);color:var(--c-accent);}
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

.tts-dock{position:fixed;left:0;right:0;bottom:0;padding:10px clamp(14px,4vw,48px) calc(6px + var(--safe-bottom));background:var(--c-dock-bg);backdrop-filter:blur(18px) saturate(180%);border-top:1px solid var(--c-border);box-shadow:0 -8px 24px -10px rgba(0,0,0,.25);z-index:80;display:flex;flex-direction:column;gap:8px;transition:transform .4s,opacity .4s;}
.tts-dock[data-visible="false"]{transform:translateY(110%);opacity:0;pointer-events:none;}
.tts-dock-main{display:flex;align-items:center;gap:10px;justify-content:center;flex-wrap:wrap;}
.dock-btn{background:var(--c-surface);border:1px solid var(--c-border);border-radius:14px;padding:10px 16px;font-size:16px;cursor:pointer;color:var(--c-fg);display:inline-flex;align-items:center;justify-content:center;transition:.25s;min-width:46px;min-height:46px;box-shadow:var(--shadow-small);}
.dock-btn.play{background:linear-gradient(135deg,var(--c-accent),var(--c-accent2));color:#fff;border:none;}
.dock-btn:hover{filter:brightness(1.05);}
.dock-btn.small{padding:8px 12px;font-size:14px;min-width:auto;min-height:42px;}
.tts-rate-wrap{position:relative;}
.tts-rate-btn{background:var(--c-surface);border:1px solid var(--c-border);border-radius:14px;padding:8px 14px;font-size:14px;font-weight:600;color:var(--c-fg);cursor:pointer;min-height:42px;box-shadow:var(--shadow-small);outline:none;}
.tts-rate-menu{position:absolute;bottom:calc(100% + 8px);left:50%;transform:translateX(-50%) translateY(0);background:var(--c-surface);border:1px solid var(--c-border);border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,.18);list-style:none;margin:0;padding:4px;min-width:80px;z-index:200;transition:opacity .15s,transform .15s;transform-origin:bottom center;}
.tts-rate-menu[data-open="false"]{opacity:0;pointer-events:none;transform:translateX(-50%) translateY(6px);}
.tts-rate-menu[data-open="true"]{opacity:1;pointer-events:auto;transform:translateX(-50%) translateY(0);}
.tts-rate-menu li{padding:8px 16px;font-size:14px;font-weight:600;cursor:pointer;border-radius:8px;text-align:center;color:var(--c-fg);}
.tts-rate-menu li:hover{background:var(--c-surface-high);}
.tts-rate-menu li.active{color:var(--c-accent);}
.tts-progress-row{display:flex;align-items:center;gap:14px;}
.tts-progress-bar{position:relative;flex:1;height:10px;background:var(--c-surface);border:1px solid var(--c-border);border-radius:6px;cursor:pointer;overflow:hidden;touch-action:none;}
.tts-progress-fill{position:absolute;left:0;top:0;bottom:0;width:0%;background:linear-gradient(90deg,var(--c-accent),rgba(var(--c-accent-rgb),.55));transition:width .25s linear;}
.tts-progress-handle{position:absolute;top:50%;transform:translate(-50%,-50%);width:18px;height:18px;border-radius:50%;background:var(--c-accent);box-shadow:0 3px 8px -2px rgba(var(--c-accent-rgb),.6);pointer-events:auto;}
.tts-progress-text{font-size:.7rem;font-weight:600;letter-spacing:.5px;color:var(--c-fg-soft);min-width:70px;text-align:right;}
mark.tts-active{background:rgba(var(--c-accent-rgb),.15);color:inherit;border-radius:3px;padding:1px 2px;}
.tts-active{background:rgba(var(--c-accent-rgb),.12);border-radius:4px;padding:2px 3px;}
.toc-list{list-style:none;padding:0;margin:1.8rem 0 4rem;display:grid;gap:.9rem;}
.toc-list li a{display:block;background:var(--c-surface);padding:.95rem 1.2rem;border-radius:10px;border:1px solid var(--c-border);font-weight:500;font-size:.9rem;transition:.3s;letter-spacing:.3px;}
.toc-list li a:hover{background:var(--c-surface-high);border-color:var(--c-accent);color:var(--c-accent);box-shadow:var(--shadow-small);}
.hint{font-size:.75rem;letter-spacing:.5px;color:var(--c-fg-soft);opacity:.75;margin-top:3rem;text-align:center;}

@media (max-width:640px){
  body{padding:0 18px calc(var(--tts-dock-height) + 34px + var(--safe-bottom));}
  h1{font-size:clamp(1.65rem,1.4rem + 1.6vw,2.15rem);}
  .dock-btn{min-width:42px;min-height:44px;padding:8px 14px;}
  .tts-progress-bar{height:8px;}
  .tts-progress-handle{width:16px;height:16px;}
  .fab-top{width:52px;height:52px;font-size:20px;}
}
html.eyecare {--c-bg:#c7dfc5; --c-surface:#b5d4b3; --c-surface-high:#d8ead6; --c-border:#9dc09b; --c-bar-bg:rgba(199,223,197,.88); --c-dock-bg:rgba(199,223,197,.94); --c-accent:#2e7a52; --c-accent-rgb:46,122,82; --c-accent2:#4da876;}
html.reduce-motion *{animation:none !important;transition:none !important;}
"""

# ============================================================
# 阅读器划线/标记/批注样式（对齐 books 项目，改用 smdj-gd --c-* 变量）
# ============================================================
HIGHLIGHT_CSS = r"""
/* ── 高亮标记基础样式 ────────────────────────────────────── */
.bk-highlight { cursor:pointer; border-radius:2px; transition:opacity .2s; color:inherit !important; text-underline-offset:3px; position:relative; }
.bk-highlight:hover { opacity:.8; }

/* 下划线：用 text-decoration，颜色由 data-color 驱动 */
.bk-highlight[data-underline="true"] {
  text-decoration:underline;
  text-decoration-color:var(--c-accent, #3D8A5A);
  text-decoration-thickness:2px;
  text-underline-offset:2px;
}
[data-theme="dark"] .bk-highlight[data-underline="true"] { text-decoration-color:var(--c-accent2, #5EAE7E); }

/* 有颜色高亮时，下划线跟随高亮色系 */
.bk-highlight[data-underline="true"][data-color="yellow"] { text-decoration-color:#a88530; }
.bk-highlight[data-underline="true"][data-color="green"]  { text-decoration-color:#3f7a50; }
.bk-highlight[data-underline="true"][data-color="blue"]   { text-decoration-color:#3a6d85; }
.bk-highlight[data-underline="true"][data-color="pink"]   { text-decoration-color:#994a4c; }

/* 批注波浪线：::after 伪元素 SVG，不与 text-decoration 冲突 */
.bk-highlight[data-note="true"]::after {
  content:'';
  position:absolute;
  left:0; right:0;
  bottom:-1px;
  height:3px;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='3' viewBox='0 0 8 3'%3E%3Cpath d='M0 1.5 Q2 0 4 1.5 Q6 3 8 1.5' fill='none' stroke='%233D8A5A' stroke-width='1.5'/%3E%3C/svg%3E");
  background-repeat:repeat-x;
  background-size:8px 3px;
  pointer-events:none;
}
[data-theme="dark"] .bk-highlight[data-note="true"]::after {
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='3' viewBox='0 0 8 3'%3E%3Cpath d='M0 1.5 Q2 0 4 1.5 Q6 3 8 1.5' fill='none' stroke='%235EAE7E' stroke-width='1.5'/%3E%3C/svg%3E");
}

/* 下划线+批注共存：波浪线下移避开 text-decoration */
.bk-highlight[data-underline="true"][data-note="true"]::after { bottom:-3px; }

/* ── 选区菜单（选中文字后弹出的颜色选择浮窗） ────────────────── */
.hl-menu{display:none;flex-direction:column;gap:5px;padding:8px;background:var(--c-bg, #FFFFFF);border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,.16);border:1px solid var(--c-border, #E5E2DD);z-index:9999;min-width:min(220px,calc(100vw - 24px));max-width:min(340px,calc(100vw - 24px));-webkit-user-select:none;user-select:none;transition:opacity .15s ease;}
.hl-menu-row{display:flex;gap:6px;flex-wrap:nowrap;align-items:center;width:100%;}
.hl-sel-row{gap:6px;flex-wrap:nowrap;}
.hl-sel-sep{width:1px;height:24px;background:var(--c-border, #E5E2DD);flex-shrink:0;margin:0 2px;}
.hl-sel-note-btn{min-height:34px;padding:4px 10px;font-size:.78rem;flex-shrink:0;white-space:nowrap;}
.hl-menu-btn{flex:1;min-width:0;min-height:34px;padding:5px 10px;background:var(--c-surface, #EDEAE4);border:1px solid var(--c-border, #E5E2DD);border-radius:8px;font-size:.78rem;font-weight:600;color:var(--c-fg, #1A1918);cursor:pointer;white-space:nowrap;-webkit-tap-highlight-color:transparent;touch-action:manipulation;}
.hl-menu-btn:active{transform:scale(.95);background:var(--c-surface-high, #ccc);}
.hl-menu-btn-danger{color:var(--c-danger, #c62828);border-color:#fed7d7;}
.hl-menu-btn-danger:active{background:#fff5f5;}

/* ── 注解菜单：预览气泡 + 工具栏 ─────────────────────── */
.hl-ann-menu{gap:0;padding:0;min-width:min(260px,calc(100vw - 24px));max-width:min(360px,calc(100vw - 24px));overflow:hidden;}
.hl-ann-note-bubble{display:none;border-bottom:1px solid var(--c-border, #E5E2DD);padding:14px 16px 10px;width:100%;box-sizing:border-box;}
.hl-ann-note-body{font-size:.95rem;color:var(--c-fg, #1A1918);line-height:1.75;word-break:break-word;max-height:7em;overflow:hidden;display:-webkit-box;line-clamp:4;-webkit-line-clamp:4;-webkit-box-orient:vertical;white-space:pre-wrap;-webkit-user-select:text;user-select:text;}
.hl-ann-note-expand{display:block;text-align:center;padding:6px 0 0;font-size:.72rem;color:var(--c-accent, #3D8A5A);background:none;border:none;cursor:pointer;width:100%;line-height:1.4;min-height:28px;-webkit-tap-highlight-color:transparent;touch-action:manipulation;opacity:.8;}
.hl-ann-note-expand:active{opacity:1;}
.hl-ann-toolbar{display:flex;gap:0;align-items:stretch;width:100%;padding:4px 6px;box-sizing:border-box;}
.hl-ann-tool{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;flex:1;min-width:0;min-height:44px;padding:4px 2px;background:transparent;border:none;border-radius:8px;font-size:.72rem;color:var(--c-fg, #1A1918);cursor:pointer;-webkit-tap-highlight-color:transparent;touch-action:manipulation;transition:background .12s;}
.hl-ann-tool:active{background:var(--c-surface-high, #ccc);}
.hl-ann-tool-icon{font-size:1.4em;line-height:1;}
.hl-ann-tool-label{font-size:.82rem;font-weight:600;line-height:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%;}
.hl-ann-tool-danger{color:var(--c-danger, #c62828);}
.hl-ann-tool-danger:active{background:#fff5f5;}
.hl-ann-tool-sep{width:1px;align-self:center;height:24px;background:var(--c-border, #E5E2DD);flex-shrink:0;margin:0 2px;}

/* ── 颜色面板（注解菜单中的可折叠面板） ─────────────── */
.hl-color-panel{max-height:0;overflow:hidden;transition:max-height .25s ease;}
.hl-color-panel.open{max-height:60px;}
.hl-color-panel .hl-menu-row{padding-top:4px;}
.hl-color-dot{width:28px;height:28px;border:2px solid transparent;border-radius:50%;cursor:pointer;flex-shrink:0;box-shadow:0 1px 4px rgba(0,0,0,.15);transition:transform .15s;-webkit-tap-highlight-color:transparent;touch-action:manipulation;}
.hl-color-dot:active{transform:scale(.9);}
.hl-color-dot.selected{border-color:var(--c-fg, #1A1918);transform:scale(1.15);box-shadow:0 0 0 1px var(--c-fg, #1A1918);}

/* ── 下划线按钮 ─────────────────────────────────────── */
.hl-underline-btn{min-width:36px;min-height:30px;padding:4px 8px 2px;background:var(--c-surface, #EDEAE4);color:var(--c-fg, #1A1918);border:1px solid var(--c-border, #E5E2DD);border-bottom:2px solid var(--c-accent, #3D8A5A);border-radius:6px;font-size:.78rem;font-weight:700;cursor:pointer;-webkit-tap-highlight-color:transparent;touch-action:manipulation;}
.hl-underline-btn.active{background:var(--c-accent, #3D8A5A);color:#fff;border-color:var(--c-accent, #3D8A5A);border-bottom-color:rgba(255,255,255,.5);}

/* ── 笔记模态框 ──────────────────────────────────────── */
.hl-modal-mask{display:none;position:fixed;inset:0;background:rgba(26,25,23,.4);z-index:10100;align-items:center;justify-content:center;padding:16px;touch-action:none;overscroll-behavior:none;}
.hl-modal-card{background:var(--c-bg, #FFFFFF);border-radius:16px;padding:18px;width:100%;max-width:420px;box-sizing:border-box;display:flex;flex-direction:column;gap:12px;overflow:hidden;}
.hl-modal-title{font-size:1.05rem;font-weight:700;color:var(--c-fg, #1A1918);}
.hl-note-textarea{width:100%;box-sizing:border-box;resize:vertical;overflow-y:auto;border:1px solid var(--c-border, #E5E2DD);border-radius:8px;padding:10px;font-size:.95rem;color:var(--c-fg, #1A1918);background:var(--c-surface, #EDEAE4);font-family:inherit;line-height:1.6;min-height:100px;max-height:60vh;}
.hl-note-textarea:focus{outline:none;border-color:var(--c-accent, #3D8A5A);box-shadow:0 0 0 2px rgba(var(--c-accent-rgb, 61,138,90), .16);}
.hl-modal-actions{display:flex;gap:8px;justify-content:flex-end;}
.hl-modal-btn{min-height:34px;padding:5px 16px;border-radius:8px;font-size:.78rem;font-weight:600;cursor:pointer;border:1px solid var(--c-border, #E5E2DD);flex-shrink:0;white-space:nowrap;}
.hl-modal-cancel{background:var(--c-surface, #EDEAE4);color:var(--c-fg, #1A1918);}
.hl-modal-save{background:var(--c-accent, #3D8A5A);color:#fff;border-color:var(--c-accent, #3D8A5A);}
.hl-modal-save:active{opacity:.85;}

/* ── 划线笔记图标 ─────────────────────────────────────── */
.bk-hl-note-icon{font-size:.72rem;cursor:pointer;vertical-align:super;line-height:1;margin-left:1px;-webkit-user-select:none;user-select:none;}
"""

# 高亮样式合并进核心样式（light 与 full 一致；深色主题由 --c-* 变量自适应）
CORE_CSS_BASE = CORE_CSS_BASE + "\n" + HIGHLIGHT_CSS

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
