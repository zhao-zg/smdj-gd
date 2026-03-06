"""
Generate Android mipmap launcher icons from output/icons/icon-512.png.
Called by .github/workflows/android-release.yml during CI build.
"""
from PIL import Image
import os

ICON_SRC = "output/icons/icon-512.png"

SIZES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}

if not os.path.isfile(ICON_SRC):
    print("No icon-512.png found, skipping icon generation.")
else:
    src = Image.open(ICON_SRC).convert("RGBA")
    for density, size in SIZES.items():
        dst = "android/app/src/main/res/mipmap-{}/ic_launcher.png".format(density)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        img = src.resize((size, size), Image.LANCZOS)
        img.save(dst)
        print("Generated {} ({}x{})".format(dst, size, size))
    print("All Android launcher icons generated.")
