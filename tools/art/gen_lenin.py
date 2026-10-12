#!/usr/bin/env python3
"""SDPOSTR1 - the Lenin propaganda poster, 128x256.

Run with the project venv:
  .venv/bin/python tools/art/gen_lenin.py            # -> work/art/lenin/SDPOSTR1.png
  .venv/bin/python tools/art/gen_lenin.py --sweep    # -> the parameter sweep sheet

History, because it cost four rounds and the lesson is worth keeping:

  v1  constructivist silhouette               CEO: rejected, wanted something realistic
  v2  naive global threshold on the photo     PM: no readable face
  v3  hand-drawn silhouette + hand-drawn      CEO: "no se parece a el EN NADA"
      feature regions
  v4  back to the photograph, four flat inks  CEO: picked cell 4C from a 15-cell sweep

The lesson of v3: the likeness lives in the PHOTOGRAPH. The moment the outline
and the features were hand-traced the portrait became a generic bald man. So
everything here is derived from the negative; the only hand-set numbers are the
crop, the ink count and where the cuts fall.

The sweep (--sweep) is the review tool: one sheet of fifteen posterisations
instead of five rounds of three finished drawings. The CEO points at a cell.

Source: work/art/reference/lenin_1920_zhukov.jpg - portrait of Lenin, July 1920,
by Pavel Zhukov (1870-1942). Public domain in Russia (author died 1942) and in
the United States (published before 1 January 1931); recorded with its origin in
docs/art/LICENSES.md. No Soviet poster is copied - only the technique, which is
not protected. See docs/product/2026-10-12_2000_F2_pm-soviet-art-copyright.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import ramp_colour  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHOTO = PROJECT_ROOT / "work" / "art" / "reference" / "lenin_1920_zhukov.jpg"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "lenin"

# --- format -------------------------------------------------------------
# 128x256: two tiles tall, the proportion of a real poster on a wall. At the
# 64x128 of the other walls the head was 70x105 px and unreadable (PM, v2).
WIDTH, HEIGHT = 128, 256
SLOGAN_BAND = 46          # bottom strip left flat for the Cyrillic line
BORDER = 3                # printed cream edge of the paper

# Crop of the negative, as fractions of the plate: head and shoulders, 1:2.
CROP = (0.235, 0.020, 0.765, 0.745)

# --- separation ---------------------------------------------------------
# Four flat inks. The cuts are PERCENTILES of the cropped image, not absolute
# grey values: a percentile cannot make a feature vanish, because "the darkest
# quarter of this portrait" is always a quarter of it whatever the exposure.
INK_COUNT = 4
CUT_BIAS = 0              # cell 4C of the sweep, chosen by the CEO 2026-10-12
GRAIN_FILTER = 3          # median px; flattens the 1920 negative's grain
AUTOCONTRAST_CUTOFF = 1   # per cent clipped at each end before cutting

SLOGAN = "ЛЕНИН ЖИВ"      # "Lenin lives" - after Mayakovsky (d. 1930), free
SLOGAN_SIZE = 19
SLOGAN_MASK_CUT = 128     # glyph coverage above this is ink, below is ground
FONT_BOLD = "/System/Library/Fonts/Supplemental/Impact.ttf"


def inks():
    """Dark to light. Darkest is the ground, so the head looks printed on it."""
    return [ramp_colour("flag_red", 0.20), ramp_colour("flag_red", 0.62),
            ramp_colour("cream_yellow", 0.60), ramp_colour("cream_yellow", 0.88)]


def portrait(bias: int = CUT_BIAS, height: int | None = None) -> np.ndarray:
    h = height if height is not None else HEIGHT - SLOGAN_BAND
    src = Image.open(PHOTO).convert("L")
    pw, ph = src.size
    box = (int(CROP[0] * pw), int(CROP[1] * ph), int(CROP[2] * pw), int(CROP[3] * ph))
    # Downscale BEFORE cutting: posterising a big image and shrinking it speckles.
    img = src.crop(box).resize((WIDTH, h), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=AUTOCONTRAST_CUTOFF)
    img = img.filter(ImageFilter.MedianFilter(GRAIN_FILTER))
    base = np.array(img, dtype=float)
    cuts = [np.percentile(base, min(max(100 * i / INK_COUNT + bias, 2), 98))
            for i in range(1, INK_COUNT)]
    idx = np.zeros_like(base, dtype=int)
    for c in cuts:
        idx += (base > c).astype(int)
    out = np.zeros((h, WIDTH, 3), dtype=np.uint8)
    for i, colour in enumerate(inks()):
        out[idx == i] = colour
    return out


def poster(bias: int = CUT_BIAS, slogan: str = SLOGAN) -> Image.Image:
    dark, red, _, cream = inks()
    gold = ramp_colour("hazard_yellow", 0.86)
    body = HEIGHT - SLOGAN_BAND
    img = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    img[:body] = portrait(bias)
    img[body:] = red
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    for i in range(BORDER):
        d.rectangle([i, i, WIDTH - 1 - i, HEIGHT - 1 - i], outline=cream)
    d.line([(BORDER, body), (WIDTH - 1 - BORDER, body)], fill=gold, width=1)
    if slogan:
        # Pillow antialiases text, which blends ink with ground and invents
        # colours outside the palette - check_pk3 rejected 95 of them on the
        # first build. Render the glyphs to a mask, cut it hard, and paste the
        # flat ink through it: screen-printed letters, exactly N inks.
        f = ImageFont.truetype(FONT_BOLD, SLOGAN_SIZE)
        mask = Image.new("L", (WIDTH, SLOGAN_BAND), 0)
        md = ImageDraw.Draw(mask)
        bb = md.textbbox((0, 0), slogan, font=f)
        md.text(((WIDTH - (bb[2] - bb[0])) // 2 - bb[0],
                 (SLOGAN_BAND - (bb[3] - bb[1])) // 2 - bb[1] - 1),
                slogan, font=f, fill=255)
        hard = mask.point(lambda v: 255 if v >= SLOGAN_MASK_CUT else 0, mode="1")
        im.paste(Image.new("RGB", (WIDTH, SLOGAN_BAND), cream), (0, body), hard)
    return im


def sweep(path: Path) -> None:
    """The review sheet: 3 ink counts x 5 cut points, one pass."""
    global INK_COUNT
    biases, zoom, label, gap = [-18, -9, 0, 9, 18], 2, 22, 8
    saved = INK_COUNT
    body = HEIGHT - SLOGAN_BAND
    sheet = Image.new("RGB", (len(biases) * (WIDTH * zoom + gap) + gap,
                              3 * (body * zoom + label + gap) + gap + 24), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 15)
    fs = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 12)
    d.text((gap, 6), "Lenin - posterisation sweep. Point at one cell (e.g. 4C).",
           font=f, fill=(255, 230, 120))
    for r, n in enumerate([2, 3, 4]):
        INK_COUNT = n
        for c, b in enumerate(biases):
            im = Image.fromarray(portrait(b)).resize((WIDTH * zoom, body * zoom), Image.NEAREST)
            x, y = gap + c * (WIDTH * zoom + gap), 24 + gap + r * (body * zoom + label + gap)
            sheet.paste(im, (x, y + label))
            d.text((x + 2, y + 3), f"{n}{chr(65 + c)}  {n} inks  cut {b:+d}", font=fs, fill=(235,) * 3)
    INK_COUNT = saved
    sheet.save(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sweep", action="store_true", help="write the review sheet instead of the lump")
    ap.add_argument("--bias", type=int, default=CUT_BIAS, help="shift every cut point (sweep cell)")
    ap.add_argument("--slogan", default=SLOGAN, help='Cyrillic line, "" for none')
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.sweep:
        out = OUT_DIR / "lenin_sweep.png"
        sweep(out)
    else:
        out = OUT_DIR / "SDPOSTR1.png"
        im = poster(args.bias, args.slogan)
        used = len({tuple(p) for p in np.array(im).reshape(-1, 3)})
        im.convert("P", palette=Image.ADAPTIVE, colors=max(used, 2)).save(out)
        print(f"SDPOSTR1  {im.width}x{im.height}  colours={used}  bias={args.bias:+d}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
