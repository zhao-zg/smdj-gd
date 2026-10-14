import html
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from datetime import datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import tinycss2

from converter import EPUBToHTMLConverter


def css_urls(tokens):
    for token in tokens:
        if token.type == "url":
            yield token.value
        elif token.type == "function" and token.lower_name == "url":
            yield tinycss2.serialize(token.arguments).strip().strip("\"'")
        else:
            for attribute in ("prelude", "content", "arguments"):
                children = getattr(token, attribute, None)
                if children:
                    yield from css_urls(children)


def usable_font(path):
    if path.suffix.lower() not in {".ttf", ".otf", ".woff", ".woff2"}:
        return True
    with path.open("rb") as font:
        return font.read(4) in {b"\x00\x01\x00\x00", b"OTTO", b"ttcf", b"wOFF", b"wOF2", b"true", b"typ1"}


def filtered_css(source, root):
    rules = tinycss2.parse_stylesheet(source.read_text(encoding="utf-8"), skip_comments=True)
    kept = []
    for rule in rules:
        missing = []
        for url in css_urls([rule]):
            parts = urlsplit(url)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            target = (source.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(root.resolve()) or not target.is_file() or not usable_font(target):
                missing.append(url)
        if missing:
            if rule.type == "at-rule" and rule.lower_at_keyword == "font-face":
                print("跳过不可用字体:", source.name, ", ".join(missing))
                continue
            raise ValueError(f"CSS 资源缺失: {source.name} / {', '.join(missing)}")
        if rule.type == "error":
            raise ValueError(f"CSS 解析失败: {source}")
        kept.append(rule)
    return tinycss2.serialize(kept)


class BodyRewriter(HTMLParser):
    def __init__(self, rewrite_url):
        super().__init__(convert_charrefs=False)
        self.rewrite_url = rewrite_url
        self.parts = []

    def write_tag(self, tag, attrs, closed=False):
        if tag == "body":
            tag = "div"
            attrs = [(name, value) for name, value in attrs if name in {"class", "id", "style", "dir", "lang", "xml:lang"}]
        attributes = []
        for name, value in attrs:
            if value is not None and name == "style":
                value = self.rewrite_style(value)
            if value is not None and name in {"src", "href", "poster", "xlink:href"}:
                value = self.rewrite_url(value, tag == "a" and name == "href")
            if value is None:
                attributes.append(name)
            else:
                attributes.append(f'{name}="{html.escape(value, quote=True)}"')
        suffix = " /" if closed else ""
        spacing = " " if attributes else ""
        self.parts.append(f"<{tag}{spacing}{' '.join(attributes)}{suffix}>")

    def rewrite_style(self, value):
        def rewrite_tokens(tokens):
            for token in tokens:
                if token.type == "url":
                    token.value = self.rewrite_url(token.value, False)
                    token.representation = 'url("' + tinycss2.serializer.serialize_string_value(token.value) + '")'
                elif token.type == "function" and token.lower_name == "url":
                    url = tinycss2.serialize(token.arguments).strip().strip("\"'")
                    rewritten = self.rewrite_url(url, False)
                    token.arguments = tinycss2.parse_component_value_list('"' + tinycss2.serializer.serialize_string_value(rewritten) + '"')
                else:
                    children = getattr(token, "arguments", getattr(token, "content", None))
                    if children:
                        rewrite_tokens(children)

        tokens = tinycss2.parse_component_value_list(value)
        rewrite_tokens(tokens)
        return tinycss2.serialize(tokens)

    def handle_starttag(self, tag, attrs):
        self.write_tag(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self.write_tag(tag, attrs, True)

    def handle_endtag(self, tag):
        if tag == "body":
            tag = "div"
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def handle_comment(self, data):
        self.parts.append(f"<!--{data}-->")


class MergedEPUBConverter(EPUBToHTMLConverter):
    def __init__(self, epub_paths, **options):
        super().__init__(epub_path=epub_paths[0], **options)
        self.epub_paths = [Path(path) for path in epub_paths]
        self.books = []
        self.page_books = []
        self.redirect_pages = set()
        self.active_index = 0
        self.date_map = {}
        self.reading_days = {}

    def convert(self):
        destination = self.output_dir
        with tempfile.TemporaryDirectory(prefix="merged_reader_") as staging:
            self.output_dir = Path(staging)
            self.images_dir = self.output_dir / "images"
            self.assets_css_dir = self.output_dir / "assets" / "css"
            self.assets_js_dir = self.output_dir / "assets" / "js"
            self.icons_dir = self.output_dir / "icons"
            if (destination / "icons").is_dir():
                shutil.copytree(destination / "icons", self.icons_dir)
            super().convert()
            manifest = json.loads((self.output_dir / "books-manifest.json").read_text(encoding="utf-8"))
            old_manifest = destination / "books-manifest.json"
            if old_manifest.exists():
                previous = json.loads(old_manifest.read_text(encoding="utf-8"))
                old_books = previous.get("books", [])
                if manifest["books"][:len(old_books)] != old_books:
                    raise ValueError("已有书籍被删除、替换或重编号；请使用新的输出目录，避免旧阅读进度错位")
                if previous.get("start_date") != manifest["start_date"]:
                    raise ValueError("开始日期与上次生成不同；请沿用原日期或使用新的输出目录")
            destination.mkdir(parents=True, exist_ok=True)
            for book in self.books:
                resources = destination / "assets" / "books" / book["id"]
                if resources.is_dir():
                    shutil.rmtree(resources)
            for source in self.output_dir.iterdir():
                target = destination / source.name
                if source.is_dir():
                    shutil.copytree(source, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(source, target)
        self.output_dir = destination
        print("合并阅读器已生成:", destination)

    def _validate(self):
        super()._validate()
        for path in self.epub_paths:
            if not path.is_file():
                raise FileNotFoundError(str(path))

    def _extract(self):
        for path in self.epub_paths:
            number, title = path.stem.split("_", 1)
            book_id = f"book_{int(number):03d}"
            root = self.temp_dir / book_id
            root.mkdir()
            with zipfile.ZipFile(path) as archive:
                for entry in archive.infolist():
                    target = (root / entry.filename).resolve()
                    if not target.is_relative_to(root.resolve()):
                        raise ValueError(f"不安全的 EPUB 路径: {entry.filename}")
                archive.extractall(root)
            self.books.append({"id": book_id, "title": title.strip(), "path": path, "root": root})

    def _parse_structure(self):
        self.opf_dir = self.temp_dir
        day_offset = 0
        first_day_number = None
        for book in self.books:
            parser = EPUBToHTMLConverter(str(book["path"]))
            parser.temp_dir = book["root"]
            parser._parse_structure()
            book["opf_dir"] = parser.opf_dir
            book["offset"] = len(self.spine_items)
            book["page_count"] = len(parser.spine_items)
            if not parser.spine_items:
                raise ValueError(f"EPUB 无正文: {book['title']}")
            for href in parser.spine_items:
                source = (parser.opf_dir / unquote(urlsplit(href).path)).resolve()
                if not source.is_relative_to(book["root"].resolve()) or not source.is_file():
                    raise ValueError(f"正文文件缺失或越界: {book['title']} / {href}")
                self.spine_items.append(source.relative_to(self.temp_dir).as_posix())
                self.page_books.append(book)
            day_numbers = []
            for item in parser.toc_items:
                source = (parser.opf_dir / unquote(urlsplit(item["href"]).path)).resolve()
                if not source.is_relative_to(book["root"].resolve()):
                    raise ValueError(f"目录链接越界: {item['href']}")
                href = source.relative_to(self.temp_dir).as_posix()
                if href not in self.spine_items:
                    raise ValueError(f"目录目标不在正文中: {book['title']} / {item['href']}")
                index = self.spine_items.index(href)
                self.toc_items.append({"title": item["title"], "href": href, "book_id": book["id"]})
                if item["title"].strip() == "目录" and not self.keep_epub_toc:
                    self.redirect_pages.add(index)
                match = re.search(r"第\s*(\d+)\s*天", item["title"])
                if match:
                    day_numbers.append(int(match.group(1)))
            for index in range(book["offset"], len(self.spine_items)):
                if Path(self.spine_items[index]).name.lower() in self._toc_filename_set and not self.keep_epub_toc:
                    self.redirect_pages.add(index)
            if not day_numbers and self.auto_start_date_str:
                raise ValueError(f"无法识别每日研读条目: {book['title']}；不配置开始日期仍可生成普通阅读器")
            if day_numbers:
                if first_day_number is None:
                    first_day_number = min(day_numbers)
                self._schedule_book(book, sorted(set(day_numbers)), day_offset, first_day_number)
                day_offset += len(set(day_numbers))
        self.readable_indices = []
        for book in self.books:
            indices = [index for index in range(book["offset"], book["offset"] + book["page_count"]) if index not in self.redirect_pages]
            study_indices = iter(sorted((index for index in indices if index in self.reading_days), key=lambda index: (self.reading_days[index], index)))
            self.readable_indices.extend(next(study_indices) if index in self.reading_days else index for index in indices)
        study_positions = [position for position, item in enumerate(self.toc_items) if self.spine_items.index(item["href"]) in self.reading_days]
        ordered_items = sorted((self.toc_items[position] for position in study_positions), key=lambda item: self.reading_days[self.spine_items.index(item["href"])])
        for position, item in zip(study_positions, ordered_items):
            self.toc_items[position] = item
        self.navigation = {}
        for position, index in enumerate(self.readable_indices):
            self.navigation[index] = (
                self.readable_indices[position - 1] if position else None,
                self.readable_indices[position + 1] if position + 1 < len(self.readable_indices) else None,
            )
        print("合并正文页数:", len(self.spine_items))

    def _schedule_book(self, book, source_days, offset, first_day_number):
        start = datetime.strptime(self.auto_start_date_str, "%Y-%m-%d").date() if self.auto_start_date_str else None
        day_positions = {number: position for position, number in enumerate(source_days)}
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "主日"]
        for item in self.toc_items:
            if item["book_id"] != book["id"]:
                continue
            match = re.search(r"第\s*(\d+)\s*天", item["title"])
            if not match:
                continue
            day_position = offset + day_positions[int(match.group(1))]
            day_number = first_day_number + day_position
            index = self.spine_items.index(item["href"])
            self.reading_days[index] = day_number
            if start is None:
                item["title"] = re.sub(r"第\s*\d+\s*天", f"第{day_number}天", item["title"], count=1)
                continue
            date = start + timedelta(days=day_position)
            title = re.sub(r"-?\s*[（(\[]?\d{4}-\d{2}-\d{2}[）)\]]?", "", item["title"])
            title = re.sub(r"第\s*\d+\s*天", f"第{day_number}天({date.isoformat()})", title, count=1)
            item["title"] = re.sub(r"周[一二三四五六日天]|主日", weekdays[date.weekday()], title, count=1)
            self.date_map[date.isoformat()] = min(index, self.date_map.get(date.isoformat(), index))

    def _build_link_map(self):
        self._link_map = {href: index for index, href in enumerate(self.spine_items)}

    def _find_spine_index(self, href):
        return self._link_map.get(href)

    def _build_title_date_page_map(self):
        return self.date_map

    def _merge_epub_css(self):
        self.assets_css_dir.joinpath("extra.css").write_text("", encoding="utf-8")

    def _rewrite_url(self, url, is_link=False):
        parts = urlsplit(url)
        if parts.scheme or parts.netloc or not parts.path:
            return url
        book = self.page_books[self.active_index]
        source = self.temp_dir / self.spine_items[self.active_index]
        target = (source.parent / unquote(parts.path)).resolve()
        if not target.is_relative_to(book["root"].resolve()) or not target.is_file():
            raise ValueError(f"资源或链接缺失: {book['title']} / {source.name} / {url}")
        relative = target.relative_to(self.temp_dir).as_posix()
        if is_link and relative in self._link_map:
            index = self._link_map[relative]
            if index in self.redirect_pages:
                return f"index.html?from={self.active_index}"
            rewritten = f"page_{index:04d}.htm"
        else:
            if target.suffix.lower() in {".html", ".htm", ".xhtml"}:
                raise ValueError(f"链接目标不在正文中: {url}")
            rewritten = "assets/books/" + quote(relative, safe="/")
        if parts.query:
            rewritten += "?" + parts.query
        if parts.fragment:
            rewritten += "#" + parts.fragment
        return rewritten

    def _extract_body(self, content):
        body = re.search(r"<body\b[^>]*>.*?</body>", content, flags=re.I | re.S)
        return body.group(0) if body else content

    def _clean_body(self, body, is_content):
        parser = BodyRewriter(self._rewrite_url)
        parser.feed(body)
        parser.close()
        book = self.page_books[self.active_index]
        return f'<div class="epub-book" data-book-id="{book["id"]}">' + "".join(parser.parts) + "</div>"

    def _build_redirect_page(self, idx, total):
        return super()._build_redirect_page(idx, total).replace("index.html", f"index.html?from={idx}")

    def _replace_first_heading(self, body, title):
        if self.active_index not in self.reading_days:
            return body
        heading = re.search(r"(<h[123]\b[^>]*>)(.*?)(</h[123]>)", body, flags=re.I | re.S)
        if not heading:
            return body
        anchors = re.findall(r'\bid="([^"]+)"', heading.group(2))
        content = "".join(f'<span id="{html.escape(anchor, quote=True)}"></span>' for anchor in anchors)
        replacement = heading.group(1) + content + html.escape(title) + heading.group(3)
        return body[:heading.start()] + replacement + body[heading.end():]

    def _generate_content_pages(self):
        total = len(self.spine_items)
        for index, href in enumerate(self.spine_items):
            self.active_index = index
            if index in self.redirect_pages:
                rendered = self._build_redirect_page(index, total)
            else:
                raw = (self.temp_dir / href).read_text(encoding="utf-8")
                body = self._clean_body(self._extract_body(raw), True)
                rendered = self._build_content_page(body, index, total)
                parser = BodyRewriter(self._rewrite_url)
                head = re.search(r"<head\b[^>]*>(.*?)</head>", raw, re.I | re.S)
                styles = []
                if head:
                    parser.feed(head.group(1))
                    for tag in re.findall(r"<link\b[^>]*>", "".join(parser.parts), re.I):
                        if re.search(r'rel="stylesheet"', tag, re.I):
                            styles.append(tag.replace("<link", '<link data-book-style="1"', 1))
                rendered = rendered.replace('<link rel="stylesheet" href="assets/css/extra.css" />', "\n".join(styles))
                rendered = self._add_reader_metadata(rendered)
            (self.output_dir / f"page_{index:04d}.htm").write_text(rendered, encoding="utf-8")

    def _page_neighbors(self, idx, total):
        previous, following = self.navigation[idx]
        return (
            f"page_{previous:04d}.htm" if previous is not None else None,
            f"page_{following:04d}.htm" if following is not None else None,
        )

    def _generate_index_page(self):
        super()._generate_index_page()
        path = self.output_dir / "index.html"
        text = path.read_text(encoding="utf-8")
        sections = []
        for book in self.books:
            items = []
            seen = set()
            for item in self.toc_items:
                if item["book_id"] != book["id"]:
                    continue
                index = self._find_spine_index(item["href"])
                if index in seen or index in self.redirect_pages:
                    continue
                seen.add(index)
                items.append(f'<li id="toc-item-{index:04d}"><a href="page_{index:04d}.htm">{html.escape(item["title"])}</a></li>')
            sections.append(f'<section data-book-id="{book["id"]}"><h2>{html.escape(book["title"])}</h2><ul class="toc-list">' + "\n".join(items) + "</ul></section>")
        text = re.sub(r'<ul class="toc-list">.*?</ul>', lambda match: "\n".join(sections), text, count=1, flags=re.S)
        path.write_text(self._add_reader_metadata(text), encoding="utf-8")

    def _add_reader_metadata(self, rendered):
        metadata = json.dumps(sorted(self.redirect_pages))
        return rendered.replace('<script src="assets/js/reader.js" defer></script>', f'<script>window.READER_REDIRECT_PAGES={metadata};</script>\n<script src="assets/js/reader.js" defer></script>')

    def _copy_images(self):
        for book in self.books:
            for source in book["root"].rglob("*"):
                if not source.is_file() or source.suffix.lower() in {".xhtml", ".html", ".htm", ".opf", ".ncx"}:
                    continue
                if not usable_font(source):
                    continue
                target = self.output_dir / "assets" / "books" / source.relative_to(self.temp_dir)
                target.parent.mkdir(parents=True, exist_ok=True)
                if source.suffix.lower() == ".css":
                    target.write_text(filtered_css(source, book["root"]), encoding="utf-8")
                else:
                    shutil.copy2(source, target)

    def _write_pwa(self):
        manifest = {
            "start_date": self.auto_start_date_str,
            "books": [{"id": book["id"], "sha256": hashlib.sha256(book["path"].read_bytes()).hexdigest(), "pages": book["page_count"]} for book in self.books],
        }
        (self.output_dir / "books-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        super()._write_pwa()