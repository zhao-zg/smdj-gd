import contextlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from main import build_parser, collect_epub_files, numbered_epub_files
from merged_converter import MergedEPUBConverter


def make_epub(path, marker, days=(1, 2), frontmatter=False):
    front_manifest = '<item id="notes" href="notes.xhtml" media-type="application/xhtml+xml"/><item id="method" href="method.xhtml" media-type="application/xhtml+xml"/>' if frontmatter else ""
    front_spine = '<itemref idref="notes"/><itemref idref="method"/>' if frontmatter else ""
    front_toc = '<navPoint><navLabel><text>说明</text></navLabel><content src="notes.xhtml"/></navPoint><navPoint><navLabel><text>使用生命读经信息研读圣经的方法</text></navLabel><content src="method.xhtml"/></navPoint>' if frontmatter else ""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("META-INF/container.xml", '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OPS/book.opf"/></rootfiles></container>')
        archive.writestr("OPS/book.opf", f'<package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="toc" href="toc.xhtml" media-type="application/xhtml+xml"/>{front_manifest}<item id="first" href="chapter.xhtml" media-type="application/xhtml+xml"/><item id="last" href="end.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="toc"/>{front_spine}<itemref idref="first"/><itemref idref="last"/></spine></package>')
        archive.writestr("OPS/book.ncx", f'<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/"><navMap><navPoint><navLabel><text>目录</text></navLabel><content src="toc.xhtml"/></navPoint>{front_toc}<navPoint><navLabel><text>第{days[0]}天-2020-01-01-周一</text></navLabel><content src="chapter.xhtml"/></navPoint><navPoint><navLabel><text>第{days[1]}天-周二</text></navLabel><content src="end.xhtml"/></navPoint></navMap></ncx>')
        archive.writestr("OPS/toc.xhtml", '<html><body><h1>目录</h1></body></html>')
        if frontmatter:
            archive.writestr("OPS/notes.xhtml", '<html><body><h1>说明</h1></body></html>')
            archive.writestr("OPS/method.xhtml", '<html><body><h1>使用生命读经信息研读圣经的方法</h1></body></html>')
        for name in ["chapter.xhtml", "end.xhtml"]:
            archive.writestr(f"OPS/{name}", f'<html><head><link rel="stylesheet" href="css/book.css"/></head><body><div style="white-space:pre-wrap; line-break:strict;"><h1 class="p1" style="color:green" data-source="heading"><span id="anchor"></span>{marker}</h1><p style="text-indent:2em; background-image:url(images/shared.png)">{marker}</p><img src="images/shared.png"/><a href="chapter.xhtml#anchor">first</a><a href="end.xhtml#anchor">last</a><a href="toc.xhtml#anchor">toc</a><a href="https://example.com">external</a></div></body></html>')
        archive.writestr("OPS/css/book.css", 'p{color:red} .image{background:url("../images/shared.png")} @font-face{font-family:Missing;src:url(../fonts/missing.ttf)} @font-face{font-family:Invalid;src:url(../fonts/invalid.ttf)}')
        archive.writestr("OPS/fonts/invalid.ttf", b"invalid font")
        archive.writestr("OPS/images/shared.png", marker.encode())


class NumberedFilesTests(unittest.TestCase):
    def test_numeric_order_and_gaps(self):
        self.assertEqual(
            numbered_epub_files(["10_ten.epub", "002_two.EPUB", "001_one.epub"]),
            ["001_one.epub", "002_two.EPUB", "10_ten.epub"],
        )

    def test_duplicate_numbers(self):
        with self.assertRaisesRegex(ValueError, "1"):
            numbered_epub_files(["1_one.epub", "001_other.epub"])

    def test_invalid_names(self):
        for filename in ["book.epub", "0_book.epub", "001_ .epub", "-1_book.epub"]:
            with self.subTest(filename=filename), self.assertRaises(ValueError):
                numbered_epub_files([filename])

    def test_scan_case_insensitive_and_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for filename in ["10_ten.EPUB", "002_two.epub", "notes.txt"]:
                (root / filename).touch()
            args = build_parser().parse_args(["--resource-dir", directory])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual([Path(path).name for path in collect_epub_files(args)], ["002_two.epub", "10_ten.EPUB"])
                (root / "unnumbered.epub").touch()
                with self.assertRaises(SystemExit):
                    collect_epub_files(args)
                args.separate = True
                self.assertEqual(len(collect_epub_files(args)), 3)


class MergedReaderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.paths = [self.root / "001_first.epub", self.root / "002_second.epub"]
        make_epub(self.paths[0], "FIRST", days=(1, 3))
        make_epub(self.paths[1], "SECOND")
        self.output = self.root / "reader"

    def convert(self, paths=None, start_date="2026-01-01"):
        converter = MergedEPUBConverter([str(path) for path in (paths or self.paths)], output_dir=str(self.output), auto_start_date=start_date, no_generate_icons=True)
        with contextlib.redirect_stdout(io.StringIO()):
            converter.convert()
        return converter

    def test_cross_book_navigation_links_dates_and_resources(self):
        converter = self.convert()
        self.assertEqual(len(converter.spine_items), 6)
        self.assertEqual(converter.navigation[2], (1, 4))
        self.assertEqual(converter.navigation[4], (2, 5))
        self.assertEqual(converter.date_map, {"2026-01-01": 1, "2026-01-02": 2, "2026-01-03": 4, "2026-01-04": 5})
        first = (self.output / "page_0002.htm").read_text(encoding="utf-8")
        second = (self.output / "page_0004.htm").read_text(encoding="utf-8")
        self.assertIn('nextPage:"page_0004.htm"', first)
        self.assertIn('href="page_0001.htm#anchor"', first)
        self.assertIn('href="page_0002.htm#anchor"', first)
        self.assertIn('href="page_0004.htm#anchor"', second)
        self.assertIn('id="anchor"', second)
        self.assertIn('href="https://example.com"', second)
        self.assertIn('href="index.html?from=4"', second)
        self.assertIn('data-book-style="1"', second)
        self.assertNotIn("2020-01-01", second)
        self.assertNotIn("--周", second)
        self.assertEqual((self.output / "assets/books/book_001/OPS/images/shared.png").read_bytes(), b"FIRST")
        self.assertEqual((self.output / "assets/books/book_002/OPS/images/shared.png").read_bytes(), b"SECOND")
        stylesheet = (self.output / "assets/books/book_002/OPS/css/book.css").read_text(encoding="utf-8")
        self.assertNotIn("missing.ttf", stylesheet)
        self.assertNotIn("invalid.ttf", stylesheet)
        self.assertFalse((self.output / "assets/books/book_002/OPS/fonts/invalid.ttf").exists())
        self.assertIn("../images/shared.png", stylesheet)
        index = (self.output / "index.html").read_text(encoding="utf-8")
        self.assertLess(index.index("<h2>first</h2>"), index.index("<h2>second</h2>"))
        self.assertIn("assets/books/book_002/OPS/images/shared.png", (self.output / "sw.js").read_text(encoding="utf-8"))
        self.assertIn("await runFullPrecacheOnce('install')", (self.output / "sw.js").read_text(encoding="utf-8"))

    def test_source_inline_styles_and_heading_attributes_survive(self):
        self.convert()
        page = (self.output / "page_0004.htm").read_text(encoding="utf-8")
        self.assertIn('style="white-space:pre-wrap; line-break:strict;"', page)
        self.assertIn('class="p1" style="color:green" data-source="heading"', page)
        self.assertIn('id="anchor"', page)
        self.assertIn('text-indent:2em;', page)
        self.assertIn('第3天(2026-01-03)', page)
        self.assertIn('url(&quot;assets/books/book_002/OPS/images/shared.png&quot;)', page)

    def test_body_attributes_are_kept_inside_reader_content(self):
        converter = MergedEPUBConverter(self.paths, output_dir=str(self.output), no_generate_icons=True)
        converter.page_books = [{"id": "book_001"}]
        source = '<html><body class="cover" dir="ltr" style="background-color:black;" onload="Body_onLoad()"><p>cover</p></body></html>'
        body = converter._clean_body(converter._extract_body(source), True)
        self.assertIn('<div class="cover" dir="ltr" style="background-color:black;">', body)
        self.assertNotIn("onload", body)
        self.assertNotIn("<body", body)
        self.assertTrue(body.endswith("</div></div>"))
        heading = '<h1 class="p1">notes<span style="width:100%;"><img src="line.png"/></span></h1>'
        self.assertEqual(converter._replace_first_heading(heading, "notes"), heading)

    def test_append_third_book_preserves_existing_indices_and_dates(self):
        before = self.convert()
        stale_font = self.output / "assets/books/book_001/OPS/fonts/stale.ttf"
        stale_font.parent.mkdir(parents=True, exist_ok=True)
        stale_font.write_bytes(b"obsolete")
        third = self.root / "010_third.epub"
        make_epub(third, "THIRD")
        after = self.convert(self.paths + [third])
        self.assertFalse(stale_font.exists())
        self.assertEqual(after.spine_items[:6], before.spine_items)
        self.assertEqual({date: after.date_map[date] for date in before.date_map}, before.date_map)
        self.assertEqual(after.navigation[5], (4, 7))
        self.assertEqual(len(json.loads((self.output / "books-manifest.json").read_text())["books"]), 3)

    def test_failed_input_does_not_overwrite_existing_output(self):
        self.convert()
        original = (self.output / "index.html").read_bytes()
        broken = self.root / "003_broken.epub"
        broken.write_bytes(b"not an epub")
        with self.assertRaises(zipfile.BadZipFile):
            self.convert(self.paths + [broken])
        self.assertEqual((self.output / "index.html").read_bytes(), original)

    def test_existing_book_changes_are_rejected(self):
        self.convert()
        original = (self.output / "index.html").read_bytes()
        make_epub(self.paths[0], "REPLACED")
        with self.assertRaises(ValueError):
            self.convert()
        self.assertEqual((self.output / "index.html").read_bytes(), original)

    def test_no_start_date_generates_reader_without_day_mapping(self):
        converter = self.convert(start_date=None)
        self.assertFalse(converter.date_map)

    def test_schedule_crosses_year_boundary(self):
        converter = self.convert(start_date="2026-12-30")
        self.assertEqual(converter.date_map, {"2026-12-30": 1, "2026-12-31": 2, "2027-01-01": 4, "2027-01-02": 5})

    def test_multiple_chapters_on_same_day(self):
        make_epub(self.paths[0], "FIRST", days=(1, 1))
        converter = self.convert()
        self.assertEqual(converter.date_map, {"2026-01-01": 1, "2026-01-02": 4, "2026-01-03": 5})

    def test_reading_order_follows_days_not_misordered_spine(self):
        make_epub(self.paths[0], "FIRST", days=(670, 669))
        make_epub(self.paths[1], "SECOND", days=(673, 674))
        converter = self.convert()
        self.assertEqual(converter.navigation[2][1], 1)
        self.assertEqual(converter.date_map["2026-01-01"], 2)
        self.assertEqual(converter.date_map["2026-01-02"], 1)
        self.assertEqual(converter.date_map["2026-01-03"], 4)
        self.assertIn("第671天(2026-01-03)", converter._toc_title_by_index(4))

    def test_notes_and_study_method_do_not_consume_days(self):
        make_epub(self.paths[0], "FIRST", days=(669, 670), frontmatter=True)
        make_epub(self.paths[1], "SECOND", days=(673, 674), frontmatter=True)
        converter = self.convert()
        self.assertEqual(len(converter.spine_items), 10)
        self.assertEqual(converter.date_map, {"2026-01-01": 3, "2026-01-02": 4, "2026-01-03": 8, "2026-01-04": 9})
        self.assertEqual(converter.reading_days, {3: 669, 4: 670, 8: 671, 9: 672})
        for index in (1, 2, 6, 7):
            self.assertNotIn(index, converter.reading_days)
            self.assertNotIn("第", converter._toc_title_by_index(index))

    def test_start_date_changes_do_not_overwrite_output(self):
        self.convert()
        original = (self.output / "index.html").read_bytes()
        with self.assertRaises(ValueError):
            self.convert(start_date="2026-02-01")
        self.assertEqual((self.output / "index.html").read_bytes(), original)


if __name__ == "__main__":
    unittest.main()