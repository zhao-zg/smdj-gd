# -*- coding: utf-8 -*-
"""
图标生成工具
"""

import base64
from pathlib import Path
from typing import Optional
from io import BytesIO

# ================== 可选 Pillow ==================
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# ================== 内嵌占位字体 (最小子集) ==================
EMBED_FONT_BASE64 = (
    "AAEAAAALAIAAAwAwT1MvMg8SBWkAAAC8AAAAYGNtYXB5nJr5AAABHAAAAExnYXNwAAAAEAAAAXgA"
    "AABIZ2x5ZlpWcJgAAAGwAAABhGhlYWQJ3h2ZAAACWAAAADZoaGVhB0cDpwAAAmwAAAAkaG10eBIA"
    "AAAAAAJ4AAAAIGxvY2EACgB4AAACiAAAABptYXhwAA0AOAAAArwAAAAgbmFtZf9fAFIAAALQAAAB"
    "eXBvc3QAAwAAAAADCAAAACAAAwP4AZAABQAAAgQCBgAAAAEAAAAAzD2IZwAAAADMPaHbAAAAAMw9"
    "iPk=+"
)

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


def _safe_b64_decode(data: str) -> bytes:
    data = data.strip().replace("\n","")
    pad = (-len(data)) % 4
    if pad:
        data += "=" * pad
    return base64.b64decode(data)


def _hex_to_rgb(s: str):
    s=s.strip()
    if s.startswith("#"): s=s[1:]
    if len(s)==3: s="".join(c*2 for c in s)
    if len(s)!=6: raise ValueError("颜色必须为 #RGB 或 #RRGGBB")
    return tuple(int(s[i:i+2],16) for i in (0,2,4))


def _load_font(font_file: Optional[str], size: int):
    if font_file:
        try: return ImageFont.truetype(font_file,size)
        except Exception: pass
    candidates=[
        # Ubuntu / Debian system paths
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        # Windows
        "NotoSansSC-Regular.otf","SourceHanSansSC-Regular.otf","NotoSansCJK-Regular.ttc",
        "msyh.ttc","MicrosoftYaHei.ttc","Arial.ttf","Arial Unicode.ttf",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for fp in candidates:
        try: return ImageFont.truetype(fp,size)
        except Exception: continue
    try:
        return ImageFont.truetype(BytesIO(_safe_b64_decode(EMBED_FONT_BASE64)),size)
    except Exception:
        return ImageFont.load_default()


def _measure(draw,font,text):
    try:
        box=draw.textbbox((0,0),text,font=font)
        w=box[2]-box[0];h=box[3]-box[1];return w,h,box
    except Exception: pass
    try:
        box=font.getbbox(text);w=box[2]-box[0];h=box[3]-box[1];return w,h,box
    except Exception: pass
    try:
        mask=font.getmask(text);w,h=mask.size;return w,h,(0,0,w,h)
    except Exception: pass
    est=getattr(font,'size',64);return int(est*0.6*len(text)), est,(0,0,int(est*0.6*len(text)),est)


def generate_icon(path: Path,size:int,text:str,bg:str,fg:str,base_font:int,radius:int,font_file:Optional[str],
                  auto_scale:bool,padding:int,center_mode:str,optical:float):
    if not PIL_AVAILABLE:
        data=_safe_b64_decode(BASE64_ICON_192 if size==192 else BASE64_ICON_512)
        path.write_bytes(data); return
    bg_rgb=_hex_to_rgb(bg); fg_rgb=_hex_to_rgb(fg)
    img=Image.new("RGBA",(size,size),bg_rgb+(255,))
    draw=ImageDraw.Draw(img)
    r=max(0,min(radius,size//2)); pad=max(0,min(padding,size//3))
    if r>0:
        mask=Image.new("L",(size,size),0)
        mdraw=ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([0,0,size,size],r,fill=255)
        bg_layer=Image.new("RGBA",(size,size),bg_rgb+(255,))
        img=Image.composite(bg_layer,img,mask)
        draw=ImageDraw.Draw(img)
    else:
        draw.rectangle([0,0,size,size],fill=bg_rgb)
    font=_load_font(font_file,base_font)
    if auto_scale:
        target=size-2*pad
        w,h,_=_measure(draw,font,text)
        if h<target*0.7:
            for s in range(base_font+2,base_font*3+1,2):
                f2=_load_font(font_file,s); w2,h2,_=_measure(draw,f2,text)
                if w2>target or h2>target: break
                font=f2; w,h=w2,h2
        if w>target or h>target:
            low,high=8,font.size
            while low<=high:
                mid=(low+high)//2
                f2=_load_font(font_file,mid)
                w2,h2,_=_measure(draw,f2,text)
                if w2<=target and h2<=target:
                    font=f2; w,h=w2,h2; low=mid+1
                else:
                    high=mid-1
    w,h,box=_measure(draw,font,text)
    x0,y0,x1,y1=box
    constX=(size-w)/2 - x0
    constY=(size-h)/2 - y0 - h*optical
    if center_mode=='anchor':
        try:
            draw.text((size/2,size/2 - h*optical),text,font=font,fill=fg_rgb+(255,),anchor='mm')
        except Exception:
            draw.text((constX,constY),text,font=font,fill=fg_rgb+(255,))
    else:
        draw.text((constX,constY),text,font=font,fill=fg_rgb+(255,))
    img.save(path,"PNG")
