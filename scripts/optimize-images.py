#!/usr/bin/env python3
"""
Optimize photos in /photos for fast web delivery.

The app displays images in a max-480px-wide layout (74px bands, ~200px hero),
but the CMS uploads full-resolution camera files (some 20+ MB / 4600px+). This
script downscales and re-compresses them in place so the page loads fast.

What it does (format-preserving, in place):
  - Downscale so the longest edge is at most MAX_EDGE px (never upscales)
  - Re-encode JPEG at quality QUALITY, progressive, with metadata stripped
  - Re-encode PNG with optimize (kept as PNG)

Format is preserved on purpose: the CMS writes the uploaded filename into
content.json, so keeping .jpg/.png means no path rewrites and the CMS
round-trip keeps working. Resizing + stripping metadata captures ~95% of the
savings; container format is a minor factor.

Usage:
    pip install pillow
    python3 scripts/optimize-images.py [DIR]   # DIR defaults to ./photos

Idempotent: re-running on already-optimized files makes (almost) no change,
which is what lets the CI workflow skip a commit when nothing changed.
"""

import os
import sys

from PIL import Image, ImageOps

MAX_EDGE = 1600      # longest-edge cap in px
QUALITY = 82         # JPEG quality
SKIP_UNDER = 60 * 1024  # don't bother re-encoding files already under ~60 KB

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DIR = os.path.join(ROOT, "photos")

JPEG_EXTS = {".jpg", ".jpeg"}
PNG_EXTS = {".png"}


def optimize_file(path):
    """Return True if the file was rewritten smaller, else False."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in JPEG_EXTS and ext not in PNG_EXTS:
        return False

    before = os.path.getsize(path)
    try:
        img = Image.open(path)
    except Exception as e:  # noqa: BLE001
        print(f"  skip {os.path.basename(path)} (cannot open: {e})")
        return False

    # Honor EXIF orientation before we strip metadata.
    img = ImageOps.exif_transpose(img)
    w, h = img.size
    long_edge = max(w, h)

    needs_resize = long_edge > MAX_EDGE
    # Tiny files that are already small and don't need resizing: leave alone.
    if not needs_resize and before < SKIP_UNDER:
        return False

    if needs_resize:
        scale = MAX_EDGE / long_edge
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)

    tmp = path + ".opt-tmp"
    if ext in JPEG_EXTS:
        rgb = img.convert("RGB")
        rgb.save(tmp, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    else:  # PNG
        img.save(tmp, "PNG", optimize=True)

    after = os.path.getsize(tmp)
    # Only replace if we actually saved space (keeps the script idempotent).
    if after < before:
        os.replace(tmp, path)
        print(f"  {os.path.basename(path)}: {before // 1024} KB -> {after // 1024} KB")
        return True
    os.remove(tmp)
    return False


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DIR
    if not os.path.isdir(target):
        print(f"not a directory: {target}")
        sys.exit(1)

    changed = 0
    for name in sorted(os.listdir(target)):
        path = os.path.join(target, name)
        if os.path.isfile(path) and optimize_file(path):
            changed += 1

    print(f"optimized {changed} file(s)")
    # Exit 0 always; the CI workflow detects changes via git, not exit code.


if __name__ == "__main__":
    main()
