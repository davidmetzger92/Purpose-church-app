#!/usr/bin/env python3
"""
Generate the branded Purpose Church QR code for the app home page.

Encodes https://app.purposearizona.com as a high error-correction (H) QR so the
center can carry the round Purpose "P" mark without breaking scannability.

Outputs (committed to /qr):
  - qr/purpose-qr.png  high-res raster for print / slides
  - qr/purpose-qr.svg  vector, infinitely scalable

This script is a one-time/build-time generator. It is NOT a runtime dependency
of the app. Run it locally after changing the URL, colors, or logo:

    pip install segno pillow
    python3 scripts/generate-qr.py

Optional validation (decodes the PNG to confirm the URL):
    pip install opencv-python-headless
"""

import base64
import io
import os

import segno
from PIL import Image, ImageDraw

# ── Config ────────────────────────────────────────────────────────────────
URL = "https://app.purposearizona.com"
DARK = "#0b0f14"          # brand near-black navy (QR modules)
LIGHT = "#ffffff"         # quiet zone / background
PNG_SIZE = 2048           # output PNG width/height in px
LOGO_FRACTION = 0.22      # logo diameter as a fraction of the QR width
LOGO_PAD_FRACTION = 0.14  # white gutter around the logo, as a fraction of logo size

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOGO_PATH = os.path.join(ROOT, "logos", "logo-p.webp")
OUT_DIR = os.path.join(ROOT, "qr")


def circular_logo(diameter):
    """Return an RGBA image of just the orange 'P' circle (blue corners removed),
    sitting on a white rounded backing tile, sized to `diameter` px."""
    src = Image.open(LOGO_PATH).convert("RGBA")
    s = min(src.size)
    # Center-crop to a square, then mask to a circle to drop the blue corners.
    src = src.crop(((src.width - s) // 2, (src.height - s) // 2,
                    (src.width - s) // 2 + s, (src.height - s) // 2 + s))

    pad = max(2, int(diameter * LOGO_PAD_FRACTION))
    tile = diameter + pad * 2

    # White backing tile (a circle a touch larger than the logo) so the mark
    # reads clearly against the QR modules.
    backing = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
    bd = ImageDraw.Draw(backing)
    bd.ellipse((0, 0, tile - 1, tile - 1), fill=LIGHT)

    # Circular crop of the logo (the orange circle).
    logo = src.resize((diameter, diameter), Image.LANCZOS)
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter - 1, diameter - 1), fill=255)
    backing.paste(logo, (pad, pad), mask)
    return backing


def make_png():
    qr = segno.make(URL, error="h")
    buf = io.BytesIO()
    # border=4 modules is the standard quiet zone; scale up to PNG_SIZE below.
    qr.save(buf, kind="png", scale=20, border=4, dark=DARK, light=LIGHT)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA").resize((PNG_SIZE, PNG_SIZE), Image.NEAREST)

    diameter = int(PNG_SIZE * LOGO_FRACTION)
    logo = circular_logo(diameter)
    pos = ((PNG_SIZE - logo.width) // 2, (PNG_SIZE - logo.height) // 2)
    img.alpha_composite(logo, pos)

    out = os.path.join(OUT_DIR, "purpose-qr.png")
    img.convert("RGB").save(out, "PNG", optimize=True)
    print(f"wrote {out} ({PNG_SIZE}x{PNG_SIZE})")
    return out


def make_svg():
    qr = segno.make(URL, error="h")
    scale = 20
    border = 4
    width, height = qr.symbol_size(scale=scale, border=border)

    buf = io.BytesIO()
    qr.save(buf, kind="svg", scale=scale, border=border, dark=DARK, light=LIGHT,
            xmldecl=False, svgns=True, nl=False)
    svg = buf.getvalue().decode("utf-8")

    # Embed the circular logo as a base64 PNG centered in the QR.
    diameter = int(width * LOGO_FRACTION)
    logo = circular_logo(diameter)
    lbuf = io.BytesIO()
    logo.save(lbuf, "PNG")
    b64 = base64.b64encode(lbuf.getvalue()).decode("ascii")
    lx = (width - logo.width) / 2
    ly = (height - logo.height) / 2
    overlay = (
        f'<image x="{lx:.2f}" y="{ly:.2f}" width="{logo.width}" '
        f'height="{logo.height}" '
        f'xlink:href="data:image/png;base64,{b64}"/>'
    )
    # Ensure the xlink namespace is present, then inject the overlay before </svg>.
    if "xmlns:xlink" not in svg:
        svg = svg.replace("<svg ", '<svg xmlns:xlink="http://www.w3.org/1999/xlink" ', 1)
    svg = svg.replace("</svg>", overlay + "</svg>")

    out = os.path.join(OUT_DIR, "purpose-qr.svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write(svg)
    print(f"wrote {out} ({width}x{height})")
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    make_png()
    make_svg()


if __name__ == "__main__":
    main()
