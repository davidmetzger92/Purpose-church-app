#!/usr/bin/env python3
"""
Generate several styling variants of the Purpose QR code so we can pick one.

All variants encode https://app.purposearizona.com and are REAL, scannable QR
codes (each is decode-checked at the end). Outputs land in qr/variants/.

Variants:
  center-blue-white   blue modules on white, blue 'P' disc + white P in center
  center-black-white  black modules on white, black 'P' disc + white P in center
  center-navy-blue    navy modules on white, blue 'P' disc + white P in center
  woven-blue          dark modules forming a 'P' silhouette are brand-blue, the
                      rest are navy — the P is woven into the code itself
  integrated-blue     a large brand-blue 'P' glyph integrated over the code
  integrated-black    a large black 'P' glyph integrated over the code

    pip install segno pillow
    python3 scripts/generate-qr-variants.py
"""

import os

import segno
from PIL import Image, ImageDraw

URL = "https://app.purposearizona.com"

BLUE = (31, 93, 147)     # brand blue  #1f5d93
NAVY = (11, 15, 20)      # app bg navy #0b0f14
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

SCALE = 28               # px per module
BORDER = 4               # quiet-zone modules

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGO_PATH = os.path.join(ROOT, "logos", "logo-p.webp")
OUT_DIR = os.path.join(ROOT, "qr", "variants")


# ── Logo helpers ────────────────────────────────────────────────────────────
def _classify_logo():
    """Split the logo into three masks: P (white), circle (orange), bg (blue)."""
    src = Image.open(LOGO_PATH).convert("RGB")
    s = min(src.size)
    src = src.crop(((src.width - s) // 2, (src.height - s) // 2,
                    (src.width - s) // 2 + s, (src.height - s) // 2 + s))
    px = src.load()
    w, h = src.size
    p_mask = Image.new("L", (w, h), 0)
    circle_mask = Image.new("L", (w, h), 0)
    pm, cm = p_mask.load(), circle_mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if r > 180 and g > 180 and b > 180:        # white P
                pm[x, y] = 255
            elif r > 150 and g < 160 and b < 140:      # orange circle
                cm[x, y] = 255
    return src.size, p_mask, circle_mask


_LOGO_SIZE, _P_MASK, _CIRCLE_MASK = _classify_logo()


def p_glyph(height, color):
    """Return an RGBA image of just the 'P' letter in `color`, `height` px tall."""
    bbox = _P_MASK.getbbox()
    mask = _P_MASK.crop(bbox)
    scale = height / mask.height
    mask = mask.resize((max(1, round(mask.width * scale)), height), Image.LANCZOS)
    glyph = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    glyph.paste(Image.new("RGBA", mask.size, color + (255,)), (0, 0), mask)
    return glyph


def disc_logo(diameter, disc_color, p_color):
    """A disc (disc_color) with the 'P' (p_color) on a white rounded tile."""
    pad = max(2, int(diameter * 0.14))
    tile = diameter + pad * 2
    out = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    d.ellipse((0, 0, tile - 1, tile - 1), fill=WHITE + (255,))           # white backing
    d.ellipse((pad, pad, pad + diameter - 1, pad + diameter - 1),
              fill=disc_color + (255,))                                   # colored disc
    glyph = p_glyph(int(diameter * 0.58), p_color)
    out.alpha_composite(glyph, ((tile - glyph.width) // 2, (tile - glyph.height) // 2))
    return out


# ── QR rendering ────────────────────────────────────────────────────────────
def base_png(dark=NAVY, light=WHITE):
    qr = segno.make(URL, error="h")
    rows = [list(r) for r in qr.matrix]
    n = len(rows)
    total = n + 2 * BORDER
    img = Image.new("RGBA", (total * SCALE, total * SCALE), light + (255,))
    d = ImageDraw.Draw(img)
    for y, row in enumerate(rows):
        for x, v in enumerate(row):
            if v:
                px0 = (x + BORDER) * SCALE
                py0 = (y + BORDER) * SCALE
                d.rectangle((px0, py0, px0 + SCALE - 1, py0 + SCALE - 1), fill=dark + (255,))
    return img, rows, n, total


def center_variant(name, dark, disc_color, p_color):
    img, _, _, total = base_png(dark=dark)
    size = total * SCALE
    diameter = int(size * 0.22)
    logo = disc_logo(diameter, disc_color, p_color)
    img.alpha_composite(logo, ((size - logo.width) // 2, (size - logo.height) // 2))
    return _save(name, img)


def woven_variant(name, base_dark, p_dark):
    """Dark modules whose center falls inside the P silhouette use p_dark."""
    img, rows, n, total = base_png(dark=base_dark)
    size = total * SCALE
    # Build a full-canvas P silhouette, centered, ~58% of the code tall.
    glyph = p_glyph(int(size * 0.58), p_dark)
    canvas = Image.new("L", (size, size), 0)
    canvas.paste(glyph.split()[3], ((size - glyph.width) // 2, (size - glyph.height) // 2))
    cm = canvas.load()
    d = ImageDraw.Draw(img)
    for y, row in enumerate(rows):
        for x, v in enumerate(row):
            if not v:
                continue
            cx = int((x + BORDER + 0.5) * SCALE)
            cy = int((y + BORDER + 0.5) * SCALE)
            if cm[cx, cy] > 128:
                px0 = (x + BORDER) * SCALE
                py0 = (y + BORDER) * SCALE
                d.rectangle((px0, py0, px0 + SCALE - 1, py0 + SCALE - 1), fill=p_dark + (255,))
    return _save(name, img)


def integrated_variant(name, dark, p_color):
    img, _, _, total = base_png(dark=dark)
    size = total * SCALE
    glyph = p_glyph(int(size * 0.34), p_color)
    # White halo so the glyph reads cleanly over the modules.
    halo = Image.new("RGBA", (glyph.width + SCALE, glyph.height + SCALE), (0, 0, 0, 0))
    ImageDraw.Draw(halo).rounded_rectangle(
        (0, 0, halo.width - 1, halo.height - 1), radius=SCALE, fill=WHITE + (255,))
    halo.alpha_composite(glyph, (SCALE // 2, SCALE // 2))
    img.alpha_composite(halo, ((size - halo.width) // 2, (size - halo.height) // 2))
    return _save(name, img)


def _save(name, img):
    out = os.path.join(OUT_DIR, name + ".png")
    img.convert("RGB").save(out, "PNG", optimize=True)
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    outs = [
        center_variant("center-blue-white", BLUE, BLUE, WHITE),
        center_variant("center-black-white", BLACK, BLACK, WHITE),
        center_variant("center-navy-blue", NAVY, BLUE, WHITE),
        woven_variant("woven-blue", NAVY, BLUE),
        integrated_variant("integrated-blue", NAVY, BLUE),
        integrated_variant("integrated-black", NAVY, BLACK),
    ]
    # Decode-check every variant.
    import cv2
    det = cv2.QRCodeDetector()
    print("\nscan check:")
    for path in outs:
        data, _, _ = det.detectAndDecode(cv2.imread(path))
        ok = "OK  " if data == URL else "FAIL"
        print(f"  [{ok}] {os.path.basename(path)} -> {data!r}")


if __name__ == "__main__":
    main()
