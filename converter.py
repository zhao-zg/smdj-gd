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
from datetime import datetime

from templates import (
    CORE_CSS_FULL, CORE_CSS_LIGHT, THEMES_CSS, FONTS_CSS_TEMPLATE,
    READER_JS, TTS_JS, SW_REGISTER_JS, SERVICE_WORKER_JS_NEW, OFFLINE_HTML,
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
                        print("📚 TOC (HTML NAV)", len(self.toc_items))
                        return
                except Exception as e:
                    print("⚠️ TOC HTML 解析失败:", e)
        if not self.toc_items:
            for i,h in enumerate(self.spine_items,1):
                self.toc_items.append({"title":f"第 {i} 部分","href":h})
            print("🪄 TOC 回退: 使用 spine 顺序")

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
        reader_js=READER_JS.replace("/*__DELAY_SEGMENT__*/","false" if self.presegment_tts else "true")
        self.assets_js_dir.joinpath("reader.js").write_text(reader_js,encoding="utf-8")
        self.assets_js_dir.joinpath("tts.js").write_text(TTS_JS,encoding="utf-8")
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

    def _clean_body(self, body: str, is_content: bool) -> str:
        prefix='../' if is_content else ''
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
            if re.match(r'(\.\./)?page_\d{4}/',url):
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
            new_href=f'{prefix}page_{target:04d}/'
            if frag: new_href+=f'#{frag}'
            return f'{pre}{new_href}{suf}'
        body=link_pattern.sub(repl_link,body)
        return body

    def _generate_content_pages(self):
        print("📝 生成正文页 ...")
        total=len(self.spine_items)
        for idx,href in enumerate(self.spine_items):
            src=self.opf_dir/href
            page_dir=self.output_dir/f"page_{idx:04d}"
            page_dir.mkdir(parents=True,exist_ok=True)
            filename=href.lower().split('/')[-1]
            if (filename in self._toc_filename_set) and not self.keep_epub_toc:
                redirect_html=self._build_redirect_page(idx,total)
                (page_dir/"index.html").write_text(redirect_html,encoding="utf-8")
                print(f"➡️ TOC 重定向 page_{idx:04d}")
                continue
            if not src.exists():
                print("⚠️ 缺失:",href);continue
            raw=src.read_text(encoding="utf-8",errors="ignore")
            body=self._extract_body(raw)
            body=self._clean_body(body,True)
            html_out=self._build_content_page(body,idx,total)
            html_out=re.sub(r"page_(\d{4})\.html",r"page_\1/",html_out)
            (page_dir/"index.html").write_text(html_out,encoding="utf-8")
            print(f"✅ page_{idx:04d}/index.html")

    def _build_redirect_page(self,idx:int,total:int)->str:
        return f"""<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="utf-8"/>
<title>目录重定向</title>
<meta http-equiv="refresh" content="0;url=../index.html">
<script>location.replace('../index.html');</script>
<link rel="stylesheet" href="../assets/css/core.css">
<link rel="stylesheet" href="../assets/css/themes.css">
<link rel="stylesheet" href="../assets/css/extra.css">
</head><body>
<p>跳转到目录... <a href="../index.html">若未跳转点击</a></p>
</body></html>"""

    def _build_content_page(self,body:str,idx:int,total:int)->str:
        prev=f"page_{idx-1:04d}/" if idx>0 else None
        next=f"page_{idx+1:04d}/" if idx<total-1 else None
        today_btn=""
        if self.enable_today:
            today_btn=(f'<a class="nav-btn today-link" href="#" data-start-date="{self.auto_start_date_str}" '
                       f'data-start-index="{self.auto_start_page_index}" data-total="{total}">今日</a>')
        prefetch=[]
        if prev: prefetch.append(f'<link rel="prefetch" href="../{prev}" as="document">')
        if next: prefetch.append(f'<link rel="prefetch" href="../{next}" as="document">')
        prefetch_html="\n".join(prefetch)
        fonts_link='' if self.no_fonts_css else '<link rel="stylesheet" href="../assets/css/fonts.css" />'
        prev_btn=(f'<a class="nav-btn" data-nav="prev" href="../{prev}">←</a>'
                  if prev else '<a class="nav-btn disabled" data-nav="prev" aria-hidden="true">←</a>')
        next_btn=(f'<a class="nav-btn" data-nav="next" href="../{next}">→</a>'
                  if next else '<a class="nav-btn disabled" data-nav="next" aria-hidden="true">→</a>')
        return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="auto" data-font="sans">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
<title>第 {idx+1} 页</title>
<link rel="manifest" href="../manifest.webmanifest" />
<meta name="theme-color" content="#3366ff" />
<link rel="stylesheet" href="../assets/css/core.css" />
<link rel="stylesheet" href="../assets/css/themes.css" />
<link rel="stylesheet" href="../assets/css/extra.css" />
{fonts_link}
{prefetch_html}
</head>
<body>
<header class="app-bar">
  <nav class="nav">
    <div class="nav-buttons">
      {prev_btn}
      <a class="nav-btn" data-nav="toc" href="../index.html">目录</a>
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
window.PAGE_INFO={{current:{idx},total:{total},prevPage:{f'"../{prev}"' if prev else 'null'},nextPage:{f'"../{next}"' if next else 'null'}}};
</script>
<script src="../assets/js/tts.js" defer></script>
<script src="../assets/js/reader.js" defer></script>
<script src="../assets/js/sw-register.js" defer></script>
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
        <button data-font="sans" class="chip active">Sans</button>
        <button data-font="serif" class="chip">Serif</button>
        <button data-font="dyslexic" class="chip">Dyslexic</button>
      </div>
    </div>
    <div class="setting">
      <label>主题</label>
      <div class="chips" id="theme-choices">
        <button data-theme="auto" class="chip active">Auto</button>
        <button data-theme="light" class="chip">Light</button>
        <button data-theme="dark" class="chip">Dark</button>
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
      <div class="chips"><button id="install-app-btn" class="chip" style="display:none;">安装应用</button></div>
    </div>
    <button id="close-settings" class="close-btn">完成</button>
  </div>
</aside>"""

    def _tts_dock_html(self)->str:
        return """<div class="tts-dock" id="tts-dock" data-visible="false">
  <div class="tts-dock-main">
    <button class="dock-btn" id="tts-btn-prev" title="上一句">⏮️</button>
    <button class="dock-btn play" id="tts-btn-play" title="播放 / 暂停">▶️</button>
    <button class="dock-btn" id="tts-btn-next" title="下一句">⏭️</button>
    <button class="dock-btn" id="tts-btn-stop" title="停止">■</button>
    <button class="dock-btn" id="tts-btn-mode" title="连续/单页">🔂</button>
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

    def _generate_index_page(self):
        items=[]
        for item in self.toc_items:
            idx=self._find_spine_index(item['href'])
            if idx is not None:
                items.append(f'<li><a href="page_{idx:04d}/">{html.escape(item["title"] or "无标题")}</a></li>')
        if not items:
            for i in range(len(self.spine_items)):
                items.append(f'<li><a href="page_{i:04d}/">第 {i+1} 页</a></li>')
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
<link rel="manifest" href="manifest.webmanifest" />
<meta name="theme-color" content="#3366ff" />
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
</script>
<script src="assets/js/tts.js" defer></script>
<script src="assets/js/reader.js" defer></script>
<script src="assets/js/sw-register.js" defer></script>
</body>
</html>"""
        (self.output_dir/"index.html").write_text(index_html,encoding="utf-8")
        print("📚 目录页完成")

    def _find_spine_index(self,href:str)->Optional[int]:
        for i,s in enumerate(self.spine_items):
            if s.endswith(href) or href.endswith(s):
                return i
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
                stem=self.epub_path.stem.strip()
                txt=next((c for c in stem if c.isalpha()),"R").upper()
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
            "name": f"{self.epub_path.stem} 阅读器",
            "short_name": self.epub_path.stem[:12],
            "start_url": "./index.html",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#3366ff",
            "lang":"zh-CN",
            "icons":[
                {"src":"icons/icon-192.png","sizes":"192x192","type":"image/png"},
                {"src":"icons/icon-512.png","sizes":"512x512","type":"image/png"}
            ]
        }
        self.output_dir.joinpath("manifest.webmanifest").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
        self.output_dir.joinpath("offline.html").write_text(OFFLINE_HTML,encoding="utf-8")
        page_dirs=[f"page_{i:04d}/" for i in range(len(self.spine_items))]
        sw_code=SERVICE_WORKER_JS_NEW.replace("/*__PAGE_DIRS__*/",json.dumps(page_dirs,ensure_ascii=False))
        self.output_dir.joinpath("sw.js").write_text(sw_code,encoding="utf-8")
        print("📦 已写出 PWA (manifest / sw.js / offline.html)")
