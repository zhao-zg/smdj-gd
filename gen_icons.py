"""
Generate Android mipmap launcher icons from output/icons/icon-512.png.
Called by .github/workflows/android-release.yml during CI build.

Strategy:
- Write ic_launcher.png + ic_launcher_round.png for legacy densities
- Write ic_launcher_foreground.png padded to adaptive icon size (108dp equiv)
- Overwrite mipmap-anydpi-v26 XMLs to use foreground + background color
"""
from PIL import Image
import os

ICON_SRC = "output/icons/icon-512.png"
RES_DIR = "android/app/src/main/res"

# Legacy icon sizes (dp -> px at each density)
LEGACY_SIZES = {
    "mdpi":    48,
    "hdpi":    72,
    "xhdpi":   96,
    "xxhdpi":  144,
    "xxxhdpi": 192,
}

# Adaptive foreground sizes: 108dp equivalent at each density
ADAPTIVE_SIZES = {
    "mdpi":    108,
    "hdpi":    162,
    "xhdpi":   216,
    "xxhdpi":  324,
    "xxxhdpi": 432,
}

ADAPTIVE_XML = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
"""

COLOR_XML = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ic_launcher_background">#3366FF</color>
</resources>
"""

BRAND_BG = (0x33, 0x66, 0xFF, 255)  # #3366FF opaque


if not os.path.isfile(ICON_SRC):
    print("No icon-512.png found, skipping icon generation.")
else:
    src = Image.open(ICON_SRC).convert("RGBA")

    # 1. Legacy ic_launcher.png and ic_launcher_round.png
    # Composite onto solid brand-color background so transparent/white content is visible
    for density, size in LEGACY_SIZES.items():
        mipmap_dir = os.path.join(RES_DIR, "mipmap-{}".format(density))
        os.makedirs(mipmap_dir, exist_ok=True)
        bg = Image.new("RGBA", (size, size), BRAND_BG)
        icon = src.resize((size, size), Image.LANCZOS)
        bg.paste(icon, (0, 0), icon)
        img = bg.convert("RGB")
        for name in ("ic_launcher.png", "ic_launcher_round.png"):
            dst = os.path.join(mipmap_dir, name)
            img.save(dst)
            print("Generated {}".format(dst))

    # 2. ic_launcher_foreground.png — icon centered in 108dp canvas with padding
    for density, fg_size in ADAPTIVE_SIZES.items():
        mipmap_dir = os.path.join(RES_DIR, "mipmap-{}".format(density))
        os.makedirs(mipmap_dir, exist_ok=True)
        # Safe zone is 72/108 of the foreground canvas
        icon_size = round(fg_size * 72 / 108)
        padding = (fg_size - icon_size) // 2
        canvas = Image.new("RGBA", (fg_size, fg_size), (0, 0, 0, 0))
        icon = src.resize((icon_size, icon_size), Image.LANCZOS)
        canvas.paste(icon, (padding, padding), icon)
        dst = os.path.join(mipmap_dir, "ic_launcher_foreground.png")
        canvas.save(dst)
        print("Generated {}".format(dst))

    # 3. Adaptive icon XMLs in mipmap-anydpi-v26
    anydpi_dir = os.path.join(RES_DIR, "mipmap-anydpi-v26")
    os.makedirs(anydpi_dir, exist_ok=True)
    for xml_name in ("ic_launcher.xml", "ic_launcher_round.xml"):
        with open(os.path.join(anydpi_dir, xml_name), "w") as f:
            f.write(ADAPTIVE_XML)
    print("Written adaptive icon XMLs to {}".format(anydpi_dir))

    # 4. Background color resource
    values_dir = os.path.join(RES_DIR, "values")
    os.makedirs(values_dir, exist_ok=True)
    color_file = os.path.join(values_dir, "ic_launcher_background.xml")
    colors_file = os.path.join(values_dir, "colors.xml")
    already_declared = (
        os.path.isfile(colors_file) and "ic_launcher_background" in open(colors_file).read()
    )
    if not already_declared and not os.path.isfile(color_file):
        with open(color_file, "w") as f:
            f.write(COLOR_XML)
        print("Written ic_launcher_background color resource.")

    print("All Android launcher icons generated successfully.")
