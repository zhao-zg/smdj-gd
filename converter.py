# -*- coding: utf-8 -*-
"""
EPUB → HTML 多页阅读器转换器核心类
"""

import zipfile
import os
import re
import shutil
import tempfile
import html
import json
from pathlib import Path
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET
from datetime import datetime, timedelta

from templates import (
    CORE_CSS_FULL, CORE_CSS_LIGHT, THEMES_CSS, FONTS_CSS_TEMPLATE,
    READER_JS, TTS_JS, APP_UPDATE_JS, SW_REGISTER_JS, SERVICE_WORKER_JS_NEW, OFFLINE_HTML,
)
from icon_generator import (
    generate_icon, _safe_b64_decode, BASE64_ICON_192, BASE64_ICON_512,
)


class EPUBToHTMLConverter:
    def __init__(
        self,
        epub_path: str,
        output_dir: Optional[str]=None,
        auto_start_date: Optional[str]=None,
        auto_start_page: int=0,
        light_ui: bool=False,
        presegment_tts: bool=False,
        mobile_font_bump: int=1,
        no_fonts_css: bool=False,
        keep_epub_toc: bool=False,
        icon_text: Optional[str]=None,
        icon_bg: str="#3366ff",
        icon_fg: str="#ffffff",
        icon_font_size: int=96,
        icon_radius: int=32,
        no_generate_icons: bool=False,
        force_regen_icons: bool=False,
        icon_font_file: Optional[str]=None,
        icon_auto_scale: bool=True,
        icon_padding: int=8,
        icon_center_mode: str="bbox",
        icon_optical_adjust: float=0.02,
    ):
        self.epub_path=Path(epub_path)
        self.output_dir=Path(output_dir or (self.epub_path.stem+"_html"))
        self.temp_dir:Optional[Path]=None
        self.images_dir=self.output_dir/"images"
        self.assets_css_dir=self.output_dir/"assets"/"css"
        self.assets_js_dir=self.output_dir/"assets"/"js"
        self.icons_dir=self.output_dir/"icons"
        self.spine_items:List[str]=[]
        self.toc_items:List[Dict[str,str]]=[]
        self.opf_dir:Optional[Path]=None

        self.auto_start_date_str=auto_start_date
        self.auto_start_page_index=auto_start_page
        self.enable_today=bool(auto_start_date)

        self.light_ui=light_ui
        self.presegment_tts=presegment_tts
        self.mobile_font_bump=mobile_font_bump
        self.no_fonts_css=no_fonts_css
        self.keep_epub_toc=keep_epub_toc

        self.icon_text_input=icon_text
        self.icon_bg=icon_bg
        self.icon_fg=icon_fg
        self.icon_font_size=icon_font_size
        self.icon_radius=icon_radius
        self.no_generate_icons=no_generate_icons
        self.force_regen_icons=force_regen_icons
        self.icon_font_file=icon_font_file
        self.icon_auto_scale=icon_auto_scale
        self.icon_padding=icon_padding
        self.icon_center_mode=icon_center_mode
        self.icon_optical_adjust=icon_optical_adjust

        self._toc_filename_set={'nav.xhtml','toc.xhtml','navigation.xhtml','toc.html','nav.html','contents.html','content.html'}
        self._link_map={}

        # 读取应用版本（用于注入 window.APP_VERSION）
        try:
            import json as _json
            _cfg = Path(__file__).resolve().parent / "app_config.json"
            self.app_version = _json.loads(_cfg.read_text(encoding="utf-8")).get("version", "1.0.0")
        except Exception:
            self.app_version = "1.0.0"

    def convert(self):
        try:
            print("🚀 开始转换:", self.epub_path)
            self._validate()
            self.temp_dir=Path(tempfile.mkdtemp(prefix="epub2html_"))
            self._extract()
            self._parse_structure()
            self._build_link_map()
            self._prepare_dirs()
            self._write_assets()
            self._merge_epub_css()
            self._generate_content_pages()
            self._generate_index_page()
            self._copy_images()
            self._write_pwa()
            print("\n✅ 完成! 输出目录:", self.output_dir)
        finally:
            if self.temp_dir and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir,ignore_errors=True)

    # ---------- 解析 ----------
    def _validate(self):
        if not self.epub_path.exists():
            raise FileNotFoundError("EPUB 文件不存在")
        if self.auto_start_date_str:
            datetime.strptime(self.auto_start_date_str,"%Y-%m-%d")

    def _extract(self):
        with zipfile.ZipFile(self.epub_path,'r') as zf:
            zf.extractall(self.temp_dir)
        print("📂 解压完成")

    def _parse_structure(self):
        container=self.temp_dir/"META-INF"/"container.xml"
        if not container.exists():
            raise RuntimeError("缺少 container.xml")
        tree=ET.parse(container)
        root=tree.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
        if root is None:
            raise RuntimeError("container.xml 无 rootfile")
        opf_rel=root.get('full-path')
        opf_path=self.temp_dir/opf_rel
        if not opf_path.exists():
            raise RuntimeError("未找到 OPF: "+opf_rel)
        self.opf_dir=opf_path.parent
        self._parse_opf(opf_path)
        self._parse_toc()

    def _parse_opf(self,opf_path:Path):
        ns={"opf":"http://www.idpf.org/2007/opf"}
        tree=ET.parse(opf_path)
        manifest={}
        for it in tree.findall(".//opf:item",ns):
            manifest[it.get("id")]={"href":it.get("href"),"media":it.get("media-type")}
        for ref in tree.findall(".//opf:itemref",ns):
            rid=ref.get("idref")
            if rid in manifest:
                media=manifest[rid]["media"]
                if media in ("application/xhtml+xml","application/html+xml","text/html"):
                    self.spine_items.append(manifest[rid]["href"])
        print("📄 正文文件数量:", len(self.spine_items))

    def _parse_toc(self):
        for ncx in self.opf_dir.glob("*.ncx"):
            try:
                t=ET.parse(ncx)
                ns={"ncx":"http://www.daisy.org/z3986/2005/ncx/"}
                for np in t.findall(".//ncx:navPoint",ns):
                    tx=np.find(".//ncx:text",ns); c=np.find(".//ncx:content",ns)
                    if tx is not None and c is not None:
                        src=c.get("src","").split("#")[0]
                        if src:
                            self.toc_items.append({"title":(tx.text or '').strip() or "无标题","href":src})
                if self.toc_items:
                    self._adjust_toc_weekday_by_start_date()
                    print("📚 TOC (NCX)", len(self.toc_items))
                    return
            except Exception as e:
                print("⚠️ NCX 解析失败:", e)
        for name in ("nav.xhtml","toc.xhtml","navigation.xhtml"):
            p=self.opf_dir/name
            if p.exists():
                try:
                    raw=p.read_text(encoding="utf-8",errors="ignore")
                    links=re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',raw,re.I|re.S)
                    for href,inner in links:
                        if not href.lower().endswith((".xhtml",".html")): continue
                        title=re.sub("<.*?>","",inner).strip()
                        self.toc_items.append({"title":title or "无标题","href":href.split("#")[0]})
                    if self.toc_items:
                        self._adjust_toc_weekday_by_start_date()
                        print("📚 TOC (HTML NAV)", len(self.toc_items))
                        return
                except Exception as e:
                    print("⚠️ TOC HTML 解析失败:", e)
        if not self.toc_items:
            for i,h in enumerate(self.spine_items,1):
                self.toc_items.append({"title":f"第 {i} 部分","href":h})
            print("🪄 TOC 回退: 使用 spine 顺序")

    def _adjust_toc_weekday_by_start_date(self):
        if not self.auto_start_date_str or not self.toc_items:
            return
        try:
            start_date=datetime.strptime(self.auto_start_date_str, "%Y-%m-%d").date()
        except Exception:
            return

        day_pat=re.compile(r"第\s*(\d+)\s*天")
        weekday_pat=re.compile(r"(周[一二三四五六日天]|主日)")
        first_day_num=None
        for item in self.toc_items:
            m=day_pat.search(item.get("title", ""))
            if m:
                first_day_num=int(m.group(1))
                break
        if first_day_num is None:
            return

        changed=0
        labels=["周一","周二","周三","周四","周五","周六","主日"]
        for item in self.toc_items:
            title=item.get("title", "")
            m=day_pat.search(title)
            if not m:
                continue
            day_num=int(m.group(1))
            d=start_date + timedelta(days=day_num - first_day_num)
            new_weekday=labels[d.weekday()]
            date_text=d.strftime("%Y-%m-%d")
            # 先去掉可能已有的日期标注，避免重复叠加
            new_title=re.sub(
                r"(第\s*\d+\s*天)\s*(?:[\(（\[]\d{4}-\d{2}-\d{2}[\)）\]])?",
                r"\1",
                title,
                count=1,
            )
            new_title=re.sub(r"(第\s*\d+\s*天)", rf"\1({date_text})", new_title, count=1)
            new_title=weekday_pat.sub(new_weekday, new_title, count=1)
            if new_title != title:
                item["title"]=new_title
                changed+=1
        if changed:
            print(f"🗓 已按开始日期重算周几并补日期: {changed} 条")

    def _build_link_map(self):
        self._link_map.clear()
        for idx, rel in enumerate(self.spine_items):
            norm=rel.split('?')[0].split('#')[0].lstrip('./')
            self._link_map[norm]=idx
            self._link_map[os.path.basename(norm)]=idx

    # ---------- 输出准备 ----------
    def _prepare_dirs(self):
        for d in (self.output_dir,self.images_dir,self.assets_css_dir,self.assets_js_dir,self.icons_dir):
            d.mkdir(parents=True,exist_ok=True)

    def _write_assets(self):
        core_css=(CORE_CSS_LIGHT if self.light_ui else CORE_CSS_FULL)\
            .replace("--mobile-font-bump:1px;",f"--mobile-font-bump:{self.mobile_font_bump}px;")
        self.assets_css_dir.joinpath("core.css").write_text(core_css,encoding="utf-8")
        self.assets_css_dir.joinpath("themes.css").write_text(THEMES_CSS,encoding="utf-8")
        if not self.no_fonts_css:
            self.assets_css_dir.joinpath("fonts.css").write_text(FONTS_CSS_TEMPLATE,encoding="utf-8")
        self.assets_css_dir.joinpath("extra.css").write_text("/* EPUB 内置 CSS 合并后写入 */",encoding="utf-8")
        reader_js = READER_JS
        self.assets_js_dir.joinpath("reader.js").write_text(reader_js, encoding="utf-8")
        self.assets_js_dir.joinpath("tts.js").write_text(TTS_JS,encoding="utf-8")
        self.assets_js_dir.joinpath("app-update.js").write_text(APP_UPDATE_JS,encoding="utf-8")
        self.assets_js_dir.joinpath("sw-register.js").write_text(SW_REGISTER_JS,encoding="utf-8")
        print("🧩 静态资源写入完成")

    def _merge_epub_css(self):
        css_files=list(self.opf_dir.glob("**/*.css"))
        parts=[]
        for f in css_files:
            try:
                txt=f.read_text(encoding="utf-8",errors="ignore")
                txt=re.sub(r"/\*.*?\*/","",txt,flags=re.S)
                parts.append(f"/* {f.name} */\n{txt}")
            except Exception as e:
                print("⚠️ 读取 CSS 失败:",f,e)
        merged="\n\n".join(parts) if parts else "/* (无 EPUB CSS) */"
        self.assets_css_dir.joinpath("extra.css").write_text(merged,encoding="utf-8")
        print("🎨 合并 EPUB CSS 数量:", len(css_files))

    # ---------- 内容清理 ----------
    def _extract_body(self,content:str)->str:
        m=re.search(r"<body[^>]*>(.*?)</body>",content,re.I|re.S)
        return m.group(1) if m else content

    def _replace_first_heading(self, body: str, title: str) -> str:
        escaped_title = html.escape(title)
        patterns = [r"<h1\b[^>]*>.*?</h1>", r"<h2\b[^>]*>.*?</h2>", r"<h3\b[^>]*>.*?</h3>"]
        for pat in patterns:
            if re.search(pat, body, flags=re.I | re.S):
                return re.sub(pat, f'<h1 class="chapter-title">{escaped_title}</h1>', body, count=1, flags=re.I | re.S)
        return body

    def _clean_body(self, body: str, is_content: bool) -> str:
        prefix=''
        body=re.sub(r'\sstyle=["\'][^"\']*["\']','',body)

        def repl_img(m):
            orig=m.group(1)
            fname=os.path.basename(orig.split('?')[0].split('#')[0])
            return f'src="{prefix}images/{fname}" loading="lazy"'
        body=re.sub(r'src=["\']([^"\']+)["\']',repl_img,body,flags=re.I)

        link_pattern=re.compile(r'(<a\b[^>]*?\shref=["\'])([^"\']+)(["\'])',re.I)
        def repl_link(m):
            pre,url,suf=m.groups()
            low=url.lower()
            if low.startswith(('http://','https://','mailto:','data:')) or low.startswith('#'):
                return m.group(0)
            if re.match(r'(\.\./)?page_\d{4}\.htm',url):
                return m.group(0)
            if '#' in url:
                main,frag=url.split('#',1)
            else:
                main,frag=url,None
            main_clean=main.split('?')[0].lstrip('./')
            target=None
            if main_clean in self._link_map:
                target=self._link_map[main_clean]
            else:
                for k,v in self._link_map.items():
                    if k.endswith(main_clean):
                        target=v;break
            if target is None:
                return m.group(0)
            new_href=f'{prefix}page_{target:04d}.htm'
            if frag: new_href+=f'#{frag}'
            return f'{pre}{new_href}{suf}'
        body=link_pattern.sub(repl_link,body)
        return body

    def _generate_content_pages(self):
        print("📝 生成正文页 ...")
        total=len(self.spine_items)
        for idx,href in enumerate(self.spine_items):
            src=self.opf_dir/href
            page_file=self.output_dir/f"page_{idx:04d}.htm"
            filename=href.lower().split('/')[-1]
            if (filename in self._toc_filename_set) and not self.keep_epub_toc:
                redirect_html=self._build_redirect_page(idx,total)
                page_file.write_text(redirect_html,encoding="utf-8")
                print(f"➡️ TOC 重定向 page_{idx:04d}.htm")
                continue
            if not src.exists():
                print("⚠️ 缺失:",href);continue
            raw=src.read_text(encoding="utf-8",errors="ignore")
            body=self._extract_body(raw)
            body=self._clean_body(body,True)
            html_out=self._build_content_page(body,idx,total)
            page_file.write_text(html_out,encoding="utf-8")
            print(f"✅ page_{idx:04d}.htm")

    def _build_redirect_page(self,idx:int,total:int)->str:
        return f"""<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="utf-8"/>
<title>目录重定向</title>
<meta http-equiv="refresh" content="0;url=index.html">
<script>location.replace('index.html');</script>
<link rel="stylesheet" href="assets/css/core.css">
<link rel="stylesheet" href="assets/css/themes.css">
<link rel="stylesheet" href="assets/css/extra.css">
</head><body>
<p>跳转到目录... <a href="index.html">若未跳转点击</a></p>
</body></html>"""

    def _build_content_page(self,body:str,idx:int,total:int)->str:
        prev=f"page_{idx-1:04d}.htm" if idx>0 else None
        next=f"page_{idx+1:04d}.htm" if idx<total-1 else None
        page_title=self._toc_title_by_index(idx) or f"第 {idx+1} 页"
        body=self._replace_first_heading(body, page_title)
        today_btn=""
        if self.enable_today:
            today_btn=(f'<a class="nav-btn today-link" href="#" data-start-date="{self.auto_start_date_str}" '
                       f'data-start-index="{self.auto_start_page_index}" data-total="{total}">今日</a>')
        prefetch=[]
        if prev: prefetch.append(f'<link rel="prefetch" href="{prev}" as="document">')
        if next: prefetch.append(f'<link rel="prefetch" href="{next}" as="document">')
        prefetch_html="\n".join(prefetch)
        fonts_link='' if self.no_fonts_css else '<link rel="stylesheet" href="assets/css/fonts.css" />'
        prev_btn=(f'<a class="nav-btn" data-nav="prev" href="{prev}">←</a>'
                  if prev else '<a class="nav-btn disabled" data-nav="prev" aria-hidden="true">←</a>')
        next_btn=(f'<a class="nav-btn" data-nav="next" href="{next}">→</a>'
                  if next else '<a class="nav-btn disabled" data-nav="next" aria-hidden="true">→</a>')
        return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="auto" data-font="sans">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
<title>{html.escape(page_title)}</title>
<link rel="manifest" href="manifest.json" />
<meta name="theme-color" content="#ffffff" />
<link rel="stylesheet" href="assets/css/core.css" />
<link rel="stylesheet" href="assets/css/themes.css" />
<link rel="stylesheet" href="assets/css/extra.css" />
{fonts_link}
{prefetch_html}
</head>
<body>
<header class="app-bar">
  <nav class="nav">
    <div class="nav-buttons">
      {prev_btn}
        <a class="nav-btn" data-nav="toc" href="index.html?from={idx}">目录</a>
      {today_btn}
      {next_btn}
    </div>
    <div class="nav-settings"><button class="nav-btn small" id="open-settings" title="设置">⚙️</button></div>
  </nav>
  <div class="top-progress" id="top-progress"></div>
</header>
<div class="app-bar-spacer"></div>
{self._settings_panel_html()}
<main id="reader-content" class="page-view" data-page-index="{idx}" data-presegment="{str(self.presegment_tts).lower()}">
{body}
</main>
{self._tts_dock_html()}
<button id="back-top" class="fab-top" aria-label="回到顶部">↑</button>
<script>
window.PAGE_INFO={{current:{idx},total:{total},prevPage:{f'"{prev}"' if prev else 'null'},nextPage:{f'"{next}"' if next else 'null'}}};window.APP_VERSION="{self.app_version}";</script>
<script src="assets/js/tts.js" defer></script>
<script src="assets/js/reader.js" defer></script>
<script src="assets/js/sw-register.js" defer></script>
{self._app_update_loader_script()}
{self._pwa_actions_script()}
</body>
</html>"""

    def _settings_panel_html(self)->str:
        return """<aside class="settings-panel" id="settings-panel" aria-hidden="true">
  <div class="settings-inner">
    <h2>阅读设置</h2>
    <div class="setting">
      <label for="font-size-range">字号 <span id="font-size-label"></span></label>
      <input type="range" id="font-size-range" min="15" max="24" value="18" />
    </div>
    <div class="setting">
      <label for="line-height-range">行距 <span id="line-height-label"></span></label>
      <input type="range" id="line-height-range" min="1.3" max="2.1" step="0.05" value="1.65" />
    </div>
    <div class="setting">
      <label>字体</label>
      <div class="chips" id="font-family-choices">
        <button data-font="sans" class="chip active">无衬线</button>
        <button data-font="serif" class="chip">衬线</button>
        <button data-font="dyslexic" class="chip">易读</button>
      </div>
    </div>
    <div class="setting">
      <label>主题</label>
      <div class="chips" id="theme-choices">
        <button data-theme="auto" class="chip active">跟随系统</button>
        <button data-theme="light" class="chip">原色</button>
        <button data-theme="eyecare" class="chip">护眼</button>
      </div>
    </div>
    <div class="setting">
      <label>朗读</label>
      <div class="chips" id="tts-toggle-chips">
        <button data-tts="show" class="chip">开启朗读</button>
        <button data-tts="hide" class="chip active">隐藏朗读</button>
      </div>
    </div>
    <div class="setting">
      <label>应用</label>
      <div class="chips">
        <button id="btn-app-update" class="chip" type="button" style="display:none;">检查更新</button>
        <a id="btn-download-apk" class="chip" href="#" target="_blank" rel="noopener" style="display:none;">下载 APK</a>
        <button id="btn-install-pwa" class="chip" type="button" style="display:none;">安装 PWA</button>
        <button id="btn-cache-info" class="chip" type="button" style="display:none;">刷新缓存</button>
        <button id="btn-clear-cache" class="chip" type="button" style="display:none;">清理缓存</button>
      </div>
      <div id="cache-status-box" style="margin-top:8px;display:none;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
          <span id="cache-info" style="font-size:.8rem;color:var(--c-fg-soft);">缓存状态：未查询</span>
          <span id="cache-pct" style="font-size:.8rem;font-weight:600;color:var(--c-accent);"></span>
        </div>
        <div style="height:6px;border-radius:4px;background:var(--c-surface);border:1px solid var(--c-border);overflow:hidden;">
          <div id="cache-progress-fill" style="height:100%;background:var(--c-accent);border-radius:4px;width:0%;transition:width .4s ease;"></div>
        </div>
      </div>
    </div>
    <button id="close-settings" class="close-btn">完成</button>
  </div>
</aside>"""

    def _tts_dock_html(self)->str:
        return """<div class="tts-dock" id="tts-dock" data-visible="false">
  <div class="tts-dock-main">
    <button class="dock-btn play" id="tts-btn-play" title="播放 / 暂停">▶️</button>
    <div class="tts-rate-wrap" id="tts-rate-wrap" title="朗读倍率">
      <button class="tts-rate-btn" id="tts-rate-btn">1.0×</button>
      <ul class="tts-rate-menu" id="tts-rate-menu" data-open="false">
        <li data-val="2">2.0×</li>
        <li data-val="1.5">1.5×</li>
        <li data-val="1.25">1.25×</li>
        <li data-val="1" class="active">1.0×</li>
        <li data-val="0.8">0.8×</li>
        <li data-val="0.5">0.5×</li>
      </ul>
    </div>
    <button class="dock-btn small" id="tts-btn-close" title="隐藏朗读">✕</button>
  </div>
  <div class="tts-progress-row">
    <div class="tts-progress-bar" id="tts-progress-bar">
      <div class="tts-progress-fill" id="tts-progress-fill"></div>
      <div class="tts-progress-handle" id="tts-progress-handle"></div>
    </div>
    <div class="tts-progress-text" id="tts-progress-text">0 / 0</div>
  </div>
</div>"""

    def _pwa_actions_html(self) -> str:
        return """<section id="app-actions" style="margin:24px 0 8px; padding:14px; border:1px solid var(--c-border); border-radius:12px; background:var(--c-surface);">
    <h3 style="margin:0 0 10px; font-size:1rem;">应用与缓存</h3>
    <div style="display:flex; flex-wrap:wrap; gap:10px; margin-bottom:10px;">
        <button id="btn-app-update" class="nav-btn" type="button" style="display:none;">检查更新</button>
        <a id="btn-download-apk" class="nav-btn" href="#" target="_blank" rel="noopener" style="display:none;">下载 APK</a>
        <button id="btn-install-pwa" class="nav-btn" type="button" style="display:none;">安装 PWA</button>
        <button id="btn-cache-info" class="nav-btn" type="button" style="display:none;">刷新缓存</button>
        <button id="btn-clear-cache" class="nav-btn" type="button" style="display:none;">清理缓存</button>
    </div>
    <div id="cache-status-box">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
        <span id="cache-info" class="hint" style="margin:0;">缓存状态：未查询</span>
        <span id="cache-pct" style="font-size:.8rem;font-weight:600;color:var(--c-accent);"></span>
      </div>
      <div style="height:6px;border-radius:4px;background:var(--c-surface);border:1px solid var(--c-border);overflow:hidden;">
        <div id="cache-progress-fill" style="height:100%;background:var(--c-accent);border-radius:4px;width:0%;transition:width .4s ease;"></div>
      </div>
    </div>
</section>"""

    def _pwa_actions_script(self) -> str:
        return """<script>
let __pwaInstallPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    __pwaInstallPrompt = e;
    const btn = document.getElementById('btn-install-pwa');
    if (btn) btn.style.display = 'inline-flex';
});

window.addEventListener('appinstalled', () => {
    const btn = document.getElementById('btn-install-pwa');
    if (btn) btn.style.display = 'none';
});

async function cxCacheInfo() {
    const reg = await navigator.serviceWorker.getRegistration();
    if (!reg || !reg.active) return { available: false };
    return new Promise((resolve) => {
        const channel = new MessageChannel();
        channel.port1.onmessage = (event) => resolve(event.data || {});
        reg.active.postMessage({ type: 'CACHE_INFO' }, [channel.port2]);
    });
}

async function cxClearCache() {
    const reg = await navigator.serviceWorker.getRegistration();
    if (!reg || !reg.active) return false;
    return new Promise((resolve) => {
        const channel = new MessageChannel();
        channel.port1.onmessage = (event) => resolve(Boolean(event.data && event.data.ok));
        reg.active.postMessage({ type: 'CLEAR_CACHE' }, [channel.port2]);
    });
}

function isCapacitorApp() {
    if (window.Capacitor && typeof window.Capacitor.isNativePlatform === 'function') {
        return window.Capacitor.isNativePlatform();
    }
    const ua = navigator.userAgent || '';
    return /; wv\\)|\\bwv\\b|capacitor/i.test(ua);
}

function isStandalonePWA() {
    return window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true;
}

function isAndroidBrowser() {
    return /Android/i.test(navigator.userAgent || '');
}

async function setupAdaptiveActions() {
    const updateBtn = document.getElementById('btn-app-update');
    const downloadBtn = document.getElementById('btn-download-apk');
    const installBtn = document.getElementById('btn-install-pwa');
    const infoBtn = document.getElementById('btn-cache-info');
    const clearBtn = document.getElementById('btn-clear-cache');
    const infoBox = document.getElementById('cache-info');
    if (!updateBtn || !downloadBtn || !installBtn || !infoBtn || !clearBtn || !infoBox) return;

    const cap = isCapacitorApp();
    const installed = isStandalonePWA();
    const android = isAndroidBrowser();

    if (cap) {
        // APK 内无 Service Worker，不需要缓存/清缓存
        updateBtn.style.display = 'inline-flex';
    } else if (installed) {
        infoBtn.style.display = 'inline-flex';
        clearBtn.style.display = 'inline-flex';
    } else if (android) {
        downloadBtn.style.display = 'inline-flex';
        installBtn.style.display = 'inline-flex';
    }

    try {
        const vEndpoints = [
            './version.json',
            'https://smdj-gd.zhaozg.cloudns.org/version.json',
            'https://smdj-gd.07170501.xyz/version.json',
        ];
        let v = null;
        for (const ep of vEndpoints) {
            try { v = await fetch(ep, { cache: 'no-store' }).then((r) => r.ok ? r.json() : null); if (v) break; } catch (_) {}
        }
        if (v && v.apk_file) {
            downloadBtn.href = './' + v.apk_file;
            downloadBtn.setAttribute('download', '');
        }
    } catch (_) {
        downloadBtn.href = '#';
    }

    installBtn.addEventListener('click', async () => {
        if (!__pwaInstallPrompt) {
            infoBox.textContent = '当前环境暂不支持安装提示';
            return;
        }
        __pwaInstallPrompt.prompt();
        try { await __pwaInstallPrompt.userChoice; } catch (_) {}
        __pwaInstallPrompt = null;
    });

    infoBtn.addEventListener('click', async () => {
        const statusBox = document.getElementById('cache-status-box');
        const pctEl = document.getElementById('cache-pct');
        const fillEl = document.getElementById('cache-progress-fill');
        const infoBox = document.getElementById('cache-info');
        if (statusBox) statusBox.style.display = 'block';
        if (infoBox) infoBox.textContent = '查询中…';
        const info = await cxCacheInfo();
        if (!info.available) {
            if (infoBox) infoBox.textContent = 'Service Worker 未就绪';
            return;
        }
        const total = (info.pages?.total||0) + (info.statics?.total||0) + (info.others?.total||0);
        const cached = (info.pages?.cached||0) + (info.statics?.cached||0) + (info.others?.cached||0);
        const pct = total > 0 ? Math.min(100, Math.round(cached / total * 100)) : 0;
        if (infoBox) infoBox.textContent = `版本 ${info.version||'-'}  期望 ${total} 个  已缓存 ${cached} 个`;
        if (pctEl) pctEl.textContent = pct + '%';
        if (fillEl) fillEl.style.width = pct + '%';
    });

    clearBtn.addEventListener('click', async () => {
        if (!confirm('将清除本站所有缓存、本地设置与浏览记录，确认继续？')) return;
        const infoBox2 = document.getElementById('cache-info');
        const pctEl2 = document.getElementById('cache-pct');
        const fillEl2 = document.getElementById('cache-progress-fill');
        const statusBox2 = document.getElementById('cache-status-box');
        if (statusBox2) statusBox2.style.display = 'block';
        if (infoBox2) infoBox2.textContent = '清理中…';
        if (pctEl2) pctEl2.textContent = '0%';
        if (fillEl2) fillEl2.style.width = '0%';

        // 1. SW Cache Storage（让 SW 自行清并重新预缓存）
        const ok = await cxClearCache();

        // 2. localStorage 全清
        try { localStorage.clear(); } catch (_) {}

        // 3. sessionStorage 全清
        try { sessionStorage.clear(); } catch (_) {}

        // 4. IndexedDB 数据库枚举删除
        try {
            const dbs = await indexedDB.databases?.() || [];
            await Promise.all(dbs.map(d => new Promise((res, rej) => {
                const r = indexedDB.deleteDatabase(d.name);
                r.onsuccess = res; r.onerror = rej;
            })));
        } catch (_) {}

        if (!ok) { if (infoBox2) infoBox2.textContent = '清理完成（SW 清理失败，已清理本地数据）'; return; }
        if (infoBox2) infoBox2.textContent = '已全部清理，重新缓存中…';
        // 等 SW fullPrecache 完成后（cxClearCache 等它结束才返回），再刷新进度
        const info2 = await cxCacheInfo().catch(() => ({}));
        if (info2.available) {
            const total2 = (info2.pages?.total||0)+(info2.statics?.total||0)+(info2.others?.total||0);
            const cached2 = (info2.pages?.cached||0)+(info2.statics?.cached||0)+(info2.others?.cached||0);
            const pct2 = total2 > 0 ? Math.min(100, Math.round(cached2/total2*100)) : 0;
            if (infoBox2) infoBox2.textContent = `版本 ${info2.version||'-'}  期望 ${total2} 个  已缓存 ${cached2} 个`;
            if (pctEl2) pctEl2.textContent = pct2 + '%';
            if (fillEl2) fillEl2.style.width = pct2 + '%';
        }
    });

    updateBtn.addEventListener('click', async () => {
        if (!window.AppUpdate || typeof window.AppUpdate.checkForUpdates !== 'function') {
            infoBox.textContent = '更新模块未加载（仅 Capacitor 原生环境可用）';
            return;
        }
        try {
            infoBox.textContent = '正在检查更新...';
            await window.AppUpdate.checkForUpdates(false);
        } catch (e) {
            infoBox.textContent = '更新失败: ' + String(e && e.message ? e.message : e);
        }
    });
}

window.addEventListener('load', setupAdaptiveActions);
window.addEventListener('load', () => {
    // 页面加载后自动刷新缓存状态（延迟等 SW 就绪）
    setTimeout(async () => {
        const info = await cxCacheInfo().catch(() => ({}));
        if (!info.available) return;
        const infoBox = document.getElementById('cache-info');
        const pctEl = document.getElementById('cache-pct');
        const fillEl = document.getElementById('cache-progress-fill');
        const total = (info.pages?.total||0) + (info.statics?.total||0) + (info.others?.total||0);
        const cached = (info.pages?.cached||0) + (info.statics?.cached||0) + (info.others?.cached||0);
        const pct = total > 0 ? Math.min(100, Math.round(cached / total * 100)) : 0;
        if (infoBox) infoBox.textContent = `版本 ${info.version||'-'}  期望 ${total} 个  已缓存 ${cached} 个`;
        if (pctEl) pctEl.textContent = pct + '%';
        if (fillEl) fillEl.style.width = pct + '%';
    }, 1200);
});
window.addEventListener('load', () => {
    const from = new URLSearchParams(window.location.search).get('from');
    if (from === null) return;
    const idx = parseInt(from, 10);
    if (Number.isNaN(idx)) return;
    const target = document.getElementById('toc-item-' + String(idx).padStart(4, '0'));
    if (!target) return;
    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
});
</script>"""

    def _app_update_loader_script(self) -> str:
        return """<script>
(function(){
    try {
        if (window.Capacitor && typeof window.Capacitor.isNativePlatform === 'function' && window.Capacitor.isNativePlatform()) {
            var s = document.createElement('script');
            s.src = 'assets/js/app-update.js';
            s.defer = true;
            document.head.appendChild(s);
        }
    } catch (_) {}
})();
</script>"""

    def _generate_index_page(self):
        items=[]
        for item in self.toc_items:
            idx=self._find_spine_index(item['href'])
            if idx is not None:
                items.append(
                    f'<li id="toc-item-{idx:04d}"><a href="page_{idx:04d}.htm">{html.escape(item["title"] or "无标题")}</a></li>'
                )
        if not items:
            for i in range(len(self.spine_items)):
                items.append(f'<li><a href="page_{i:04d}.htm">第 {i+1} 页</a></li>')
        toc_html="\n      ".join(items)
        total=len(self.spine_items)
        today_btn=""
        if self.enable_today:
            today_btn=(f'<a class="nav-btn today-link" href="#" data-start-date="{self.auto_start_date_str}" '
                       f'data-start-index="{self.auto_start_page_index}" data-total="{total}">今日</a>')
        fonts_link='' if self.no_fonts_css else '<link rel="stylesheet" href="assets/css/fonts.css" />'
        index_html=f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="auto" data-font="sans">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
<title>目录</title>
<link rel="manifest" href="manifest.json" />
<meta name="theme-color" content="#ffffff" />
<link rel="stylesheet" href="assets/css/core.css" />
<link rel="stylesheet" href="assets/css/themes.css" />
<link rel="stylesheet" href="assets/css/extra.css" />
{fonts_link}
</head>
<body>
<header class="app-bar">
  <nav class="nav">
    <div class="nav-buttons">
      <a class="nav-btn disabled" data-nav="prev" aria-hidden="true">←</a>
      <a class="nav-btn" data-nav="toc" href="index.html">目录</a>
      {today_btn}
      <a class="nav-btn disabled" data-nav="next" aria-hidden="true">→</a>
    </div>
    <div class="nav-settings"><button class="nav-btn small" id="open-settings" title="设置">⚙️</button></div>
  </nav>
  <div class="top-progress" id="top-progress"></div>
</header>
<div class="app-bar-spacer"></div>
{self._settings_panel_html()}
<main id="reader-content" class="page-view" data-page-index="-1" data-presegment="{str(self.presegment_tts).lower()}">
  <h1>目录</h1>
  <ul class="toc-list">
      {toc_html}
  </ul>
  <p class="hint">共 {total} 页 · 今日功能: {self.enable_today} · 平滑翻页启用</p>
</main>
{self._tts_dock_html()}
<button id="back-top" class="fab-top" aria-label="回到顶部">↑</button>
<script>
window.PAGE_INFO={{current:-1,total:{total},prevPage:null,nextPage:null}};
window.APP_VERSION="{self.app_version}";
</script>
<script src="assets/js/tts.js" defer></script>
<script src="assets/js/reader.js" defer></script>
<script src="assets/js/sw-register.js" defer></script>
{self._app_update_loader_script()}
{self._pwa_actions_script()}
</body>
</html>"""
        (self.output_dir/"index.html").write_text(index_html,encoding="utf-8")
        print("📚 目录页完成")

    def _find_spine_index(self,href:str)->Optional[int]:
        for i,s in enumerate(self.spine_items):
            if s.endswith(href) or href.endswith(s):
                return i
        return None

    def _toc_title_by_index(self, idx: int) -> Optional[str]:
        for item in self.toc_items:
            href=item.get('href','')
            if self._find_spine_index(href) == idx:
                title=(item.get('title') or '').strip()
                if title:
                    return title
        return None

    def _copy_images(self):
        print("🖼️ 复制图片 ...")
        exts={'.jpg','.jpeg','.png','.gif','.bmp','.svg','.webp'}
        cnt=0
        for p in self.temp_dir.rglob('*'):
            if p.is_file() and p.suffix.lower() in exts:
                try:
                    shutil.copy2(p,self.images_dir/p.name)
                    cnt+=1
                except Exception as e:
                    print("⚠️ 图片复制失败:",p,e)
        print("🖼️ 已复制图片:",cnt)

    def _write_pwa(self):
        if not self.no_generate_icons:
            if self.icon_text_input:
                txt=self.icon_text_input.strip()
            else:
                txt="共读"
            print("🖍 图标文字:",txt)
            targets=[(self.icons_dir/"icon-192.png",192),(self.icons_dir/"icon-512.png",512)]
            for path,size in targets:
                if path.exists() and not self.force_regen_icons:
                    print(f"  ⏩ 跳过 {path.name}")
                    continue
                try:
                    generate_icon(
                        path=path,size=size,text=txt,
                        bg=self.icon_bg,fg=self.icon_fg,
                        base_font=self.icon_font_size if size==192 else int(self.icon_font_size*2.6),
                        radius=self.icon_radius if size==192 else int(self.icon_radius*(size/192)),
                        font_file=self.icon_font_file,
                        auto_scale=self.icon_auto_scale,
                        padding=int(self.icon_padding if size==192 else self.icon_padding*(size/192)),
                        center_mode=self.icon_center_mode,
                        optical=self.icon_optical_adjust
                    )
                    print("  ✅ 生成",path.name)
                except Exception as e:
                    print("  ⚠️ 生成失败占位:",path.name,e)
                    data=_safe_b64_decode(BASE64_ICON_192 if size==192 else BASE64_ICON_512)
                    path.write_bytes(data)
        else:
            print("🚫 跳过图标生成 (--no-generate-icons)")

        manifest={
            "name": "共读",
            "short_name": "共读",
            "description": "共读 离线阅读应用",
            "start_url": "./index.html",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#ffffff",
            "lang":"zh-CN",
            "icons":[
                {"src":"./icons/icon-192.png","sizes":"192x192","type":"image/png","purpose":"any maskable"},
                {"src":"./icons/icon-512.png","sizes":"512x512","type":"image/png","purpose":"any maskable"},
                {"src":"./icons/icon.svg","sizes":"any","type":"image/svg+xml","purpose":"any"}
            ]
        }
        manifest_json = json.dumps(manifest,ensure_ascii=False,indent=2)
        self.output_dir.joinpath("manifest.json").write_text(manifest_json,encoding="utf-8")
        # 兼容历史引用
        self.output_dir.joinpath("manifest.webmanifest").write_text(manifest_json,encoding="utf-8")

        # 生成简单 SVG 图标（避免缺少 scalable icon）
        icon_svg = """<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"512\" height=\"512\" viewBox=\"0 0 512 512\"><rect width=\"512\" height=\"512\" rx=\"96\" fill=\"#3366ff\"/><text x=\"50%\" y=\"56%\" text-anchor=\"middle\" font-size=\"180\" font-family=\"Microsoft YaHei, Noto Sans SC, PingFang SC, Arial, sans-serif\" fill=\"#ffffff\">共读</text></svg>"""
        self.icons_dir.joinpath("icon.svg").write_text(icon_svg, encoding="utf-8")

        cfg_path = Path(__file__).parent / "app_config.json"
        try:
            _app_ver = json.loads(cfg_path.read_text(encoding="utf-8")).get("version", "1.0.0")
        except Exception:
            _app_ver = "1.0.0"
        version_info = {
            "version": _app_ver,
            "apk_version": _app_ver,
            "apk_file": f"{self.epub_path.stem}-v{_app_ver}.apk",
        }
        self.output_dir.joinpath("version.json").write_text(
            json.dumps(version_info, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        headers_text = """/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY

/sw.js
  Cache-Control: no-cache, no-store, must-revalidate

/version.json
  Cache-Control: no-cache, no-store, must-revalidate
  Access-Control-Allow-Origin: *
"""
        self.output_dir.joinpath("_headers").write_text(headers_text, encoding="utf-8")

        self.output_dir.joinpath("offline.htm").write_text(OFFLINE_HTML,encoding="utf-8")
        page_files=[f"page_{i:04d}.htm" for i in range(len(self.spine_items))]

        # Build full local asset manifest for eager PWA precache.
        # Exclude SW itself, headers metadata, and large APK binaries.
        all_assets = []
        for p in sorted(self.output_dir.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(self.output_dir).as_posix()
            if rel in {"sw.js", "_headers"}:
                continue
            if rel.lower().endswith(".apk"):
                continue
            all_assets.append(f"./{rel}")

        sw_code=SERVICE_WORKER_JS_NEW.replace("/*__PAGE_DIRS__*/",json.dumps(page_files,ensure_ascii=False))
        sw_code=sw_code.replace("/*__ALL_ASSETS__*/",json.dumps(all_assets,ensure_ascii=False))
        sw_code=sw_code.replace("/*__SW_VERSION__*/",json.dumps(f"v{_app_ver}"))
        self.output_dir.joinpath("sw.js").write_text(sw_code,encoding="utf-8")
        print("📦 已写出 PWA (manifest/version/sw/offline/_headers)")
