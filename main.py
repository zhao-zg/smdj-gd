#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPUB -> HTML 多页阅读器生成器
入口文件：负责参数解析与批量扫描 resource 目录
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

from converter import EPUBToHTMLConverter


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="EPUB -> HTML + TTS + PWA 阅读器 (v3.6.7)")
    p.add_argument("epub_file", nargs="?", default=None, help="单个 EPUB 文件路径 (留空则扫描 resource 文件夹)")
    p.add_argument("-o", "--output", help="输出目录；不传则默认输出到 output")
    p.add_argument("--resource-dir", default="resource", help="扫描 EPUB 的文件夹 (默认 resource)")
    p.add_argument("--auto-start-date")
    p.add_argument("--auto-start-page", type=int, default=0)
    p.add_argument("--light-ui", action="store_true")
    p.add_argument("--presegment-tts", action="store_true")
    p.add_argument("--mobile-font-bump", type=int, default=1)
    p.add_argument("--no-fonts-css", action="store_true")
    p.add_argument("--keep-epub-toc", action="store_true", help="保留 EPUB 内部 TOC 页面 (默认重定向到主目录)")

    # 图标
    p.add_argument("--icon-text")
    p.add_argument("--icon-bg", default="#3366ff")
    p.add_argument("--icon-fg", default="#ffffff")
    p.add_argument("--icon-font-size", type=int, default=96)
    p.add_argument("--icon-radius", type=int, default=32)
    p.add_argument("--no-generate-icons", action="store_true")
    p.add_argument("--force-regenerate-icons", "--force-regen-icons", dest="force_regen_icons", action="store_true")
    p.add_argument("--icon-font-file")
    p.add_argument("--icon-padding", type=int, default=8)
    p.add_argument("--no-icon-auto-scale", action="store_true")
    p.add_argument("--icon-center-mode", choices=["bbox", "anchor"], default="bbox")
    p.add_argument("--icon-optical-adjust", type=float, default=0.02)
    return p


def collect_epub_files(args) -> list[str]:
    if args.epub_file:
        if not os.path.exists(args.epub_file):
            print(" EPUB 文件不存在")
            sys.exit(1)
        if not args.epub_file.lower().endswith(".epub"):
            print(" 仅支持 .epub")
            sys.exit(1)
        return [args.epub_file]

    script_dir = Path(__file__).resolve().parent
    res_dir = script_dir / args.resource_dir
    if not res_dir.is_dir():
        print(f" resource 文件夹不存在: {res_dir}")
        sys.exit(1)

    epub_files = sorted(str(f) for f in res_dir.glob("*.epub"))
    if not epub_files:
        print(f" 在 {res_dir} 中未找到任何 .epub 文件")
        sys.exit(1)

    print(f" 扫描到 {len(epub_files)} 个 EPUB 文件:")
    for ef in epub_files:
        print(f"    {os.path.basename(ef)}")
    return epub_files


def main() -> None:
    args = build_parser().parse_args()

    # 执行时可交互输入开始日期（格式: YYYY-MM-DD）
    if not args.auto_start_date:
        user_input = input("请输入开始日期(YYYY-MM-DD，回车跳过): ").strip()
        if user_input:
            try:
                datetime.strptime(user_input, "%Y-%m-%d")
            except ValueError:
                print("❌ 日期格式错误，请使用 YYYY-MM-DD")
                sys.exit(1)
            args.auto_start_date = user_input

    epub_files = collect_epub_files(args)
    default_output_root = Path("output")

    for epub_file in epub_files:
        if args.output:
            output_dir = args.output
        else:
            # 默认输出到 output；批量转换时按书名建子目录防止覆盖
            if len(epub_files) == 1:
                output_dir = str(default_output_root)
            else:
                output_dir = str(default_output_root / Path(epub_file).stem)
        conv = EPUBToHTMLConverter(
            epub_path=epub_file,
            output_dir=output_dir,
            auto_start_date=args.auto_start_date,
            auto_start_page=args.auto_start_page,
            light_ui=args.light_ui,
            presegment_tts=args.presegment_tts,
            mobile_font_bump=args.mobile_font_bump,
            no_fonts_css=args.no_fonts_css,
            keep_epub_toc=args.keep_epub_toc,
            icon_text=args.icon_text,
            icon_bg=args.icon_bg,
            icon_fg=args.icon_fg,
            icon_font_size=args.icon_font_size,
            icon_radius=args.icon_radius,
            no_generate_icons=args.no_generate_icons,
            force_regen_icons=args.force_regen_icons,
            icon_font_file=args.icon_font_file,
            icon_auto_scale=not args.no_icon_auto_scale,
            icon_padding=args.icon_padding,
            icon_center_mode=args.icon_center_mode,
            icon_optical_adjust=args.icon_optical_adjust,
        )
        conv.convert()


if __name__ == "__main__":
    main()
