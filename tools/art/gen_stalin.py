#!/usr/bin/env python3
"""Stalin propaganda poster, 128x256 - the twin of SDPOSTR1 (Lenin).

CEO, 2026-10-14: "exactamente como el que hicimos con Lenin, pero con Stalin".
So this is gen_lenin.py v4 pointed at another photograph, nothing more:

  same format   128x256, cream printed border, gold rule, 46 px slogan band
  same method   a public-domain photograph posterised to N flat inks of
                palette v1, cuts at PERCENTILES of the crop
  same review   a 15-cell sweep (2/3/4 inks x 5 cut points); the CEO points
                at a cell, as he picked 4C for Lenin

The lesson of Lenin v3 stands: the likeness lives in the PHOTOGRAPH, so
nothing here is hand-traced. The only hand-set numbers are the crop, the ink
count and the cut bias. The 1930 crop was set on the downloaded plate
(2026-10-14); the other candidates' crops are still PROVISIONAL guesses.

Reuse, not copy: the posterisation, the frame and the inks are gen_lenin's
own functions, run with this photograph's path and crop patched in for the
duration of the call (`_lenin_pipeline`). gen_lenin.py is not edited. The one
thing added here is a slogan stamp that takes two or three lines, because the
period Stalin slogans do not fit one line at Lenin's size (19 px Impact
measured on Windows: «СЛАВА ВЕЛИКОМУ СТАЛИНУ!» is 218 px wide on a 122 px
band). The stamp keeps Lenin's rule: glyphs rendered to a mask, cut hard,
flat cream pasted through it - no antialiased in-between colours.

Sources and legal reasoning: docs/product/2026-10-14_1556_F2_stalin-poster-sourcing.md.
Nothing is downloaded by this script. The photograph is fetched once, by
hand, with the CEO's permission, into work/art/reference/ (gitignored, never
shipped), and recorded in docs/art/LICENSES.md, as was done for Lenin.

Run with the project venv (Windows: .venv/Scripts/python.exe):
  python tools/art/gen_stalin.py --sweep              # 15-cell sheet, default candidate
  python tools/art/gen_stalin.py --sweep --candidate 1942
  python tools/art/gen_stalin.py --slogans            # slogan options, needs no photo
  python tools/art/gen_stalin.py --preview            # sweep + the slogans on full posters
  python tools/art/gen_stalin.py --bias 0 --inks 4    # the lump, once a cell is chosen

Text-bearing asset (CLAUDE.md, D27): the slogan is rasterised by this
machine's Impact. Whatever the CEO approves is regenerated only on the
machine that rendered it.
"""

from __future__ import annotations

import argparse
import contextlib
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_lenin as lenin  # noqa: E402
from artlib import FONT_POSTER, FONT_SMALL, ramp_colour  # noqa: E402

PROJECT_ROOT = lenin.PROJECT_ROOT
REFERENCE_DIR = PROJECT_ROOT / "work" / "art" / "reference"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "stalin"

# The format is Lenin's, by commission: imported, never restated.
WIDTH, HEIGHT = lenin.WIDTH, lenin.HEIGHT
SLOGAN_BAND, BORDER = lenin.SLOGAN_BAND, lenin.BORDER
BODY = HEIGHT - SLOGAN_BAND
inks = lenin.inks


# --- the photograph -----------------------------------------------------
@dataclass(frozen=True)
class Candidate:
    """One public-domain photograph on Wikimedia Commons.

    crop is (centre_x, top, bottom) as fractions of the plate; the width is
    derived from it so the crop has exactly the portrait's aspect
    (WIDTH:BODY) and the face is not stretched. Only 1930's was set on the
    photograph itself; the others are PROVISIONAL, guessed from the Commons
    description (nothing downloaded), to be set after a first look."""
    key: str
    commons_file: str
    plate: tuple[int, int]            # width, height on Commons (API, 2026-10-14)
    crop: tuple[float, float, float]  # centre_x, top, bottom
    note: str

    @property
    def photo(self) -> Path:
        return REFERENCE_DIR / f"stalin_{self.key}.jpg"


CANDIDATES: dict[str, Candidate] = {c.key: c for c in (
    # 1930, set on the plate 2026-10-14: the head spans x 630-1110, y 50-690
    # of 1313x2100; centred on it, top of the hair to the collar points, which
    # leaves out the second man at the left edge (x < ~200) and the hand at
    # the bottom left (y > ~1650). Crop in pixels: x 528-1213, y 10-1134.
    Candidate("1930", "File:Stalin-Joseph-1930.jpg", (1313, 2100), (0.663, 0.005, 0.540),
              "frontispiece, The Life of Stalin: A Symposium, New York 1930 - RECOMMENDED"),
    Candidate("1942", "File:JStalin Secretary general CCCP 1942.jpg", (3000, 4151), (0.50, 0.03, 0.60),
              "anonymous Soviet portrait, Library of Congress (OWI), c. 1942"),
    Candidate("1943", "File:CroppedStalin1943.jpg", (1511, 1984), (0.50, 0.02, 0.62),
              "U.S. Army Signal Corps, Tehran Conference, 28 Nov 1943"),
    Candidate("1929", "File:Stalin before 1929.jpg", (2124, 2968), (0.50, 0.04, 0.62),
              "anonymous portrait, Nationaal Archief (NL), dated 'before 1929'"),
)}
DEFAULT_CANDIDATE = "1930"

# --- separation: Lenin's 4C until the CEO points at a Stalin cell ----------
INK_COUNT = 4
CUT_BIAS = 0
SWEEP_INKS = (2, 3, 4)                # rows of the sheet
SWEEP_BIASES = (-18, -9, 0, 9, 18)    # columns, the same as Lenin's sheet

# --- slogan -------------------------------------------------------------
# Lines are separated by "\n" (on the command line "|" works too).
SLOGANS = {
    "za_rodinu": "ЗА РОДИНУ!\nЗА СТАЛИНА!",          # wartime battle cry, 1941-45
    "slava": "СЛАВА ВЕЛИКОМУ\nСТАЛИНУ!",              # cult formula, 1930s-1953
    "slava_short": "СЛАВА\nСТАЛИНУ!",                 # the same, at Lenin's size
    "spasibo": "СПАСИБО\nТОВАРИЩУ\nСТАЛИНУ!",         # 1936 slogan, shortened
}
SLOGAN = SLOGANS["za_rodinu"]   # proposal; the CEO chooses (sourcing doc §2)
SLOGAN_SIZE = lenin.SLOGAN_SIZE  # 19 px, Lenin's: the stamp starts here...
SLOGAN_MIN_SIZE = 12             # ...and shrinks a pixel at a time to fit
SLOGAN_SIDE_PAD = 3              # px of red between the letters and the border
SLOGAN_V_PAD = 3                 # px above (under the gold rule) and below
SLOGAN_LINE_GAP = 3              # px between cap lines
SLOGAN_MASK_CUT = lenin.SLOGAN_MASK_CUT
SLOGAN_MAX_WIDTH = WIDTH - 2 * (BORDER + SLOGAN_SIDE_PAD)
SLOGAN_MAX_HEIGHT = SLOGAN_BAND - 1 - 2 * SLOGAN_V_PAD   # row 0 is the gold rule
CAP_REFERENCE = "Н"              # no ascender, no descender: the cap height


def fit_crop(plate: tuple[int, int], crop: tuple[float, float, float],
             aspect: float = WIDTH / BODY) -> tuple[float, float, float, float]:
    """(centre_x, top, bottom) -> gen_lenin's CROP (left, top, right, bottom)
    with width/height == aspect in PIXELS, so the resize to WIDTH x BODY does
    not stretch the face. If the derived width does not fit the plate it is
    clamped and the bottom raised to keep the aspect."""
    pw, ph = plate
    cx, top, bottom = crop
    if not (0 <= top < bottom <= 1 and 0 <= cx <= 1):
        raise ValueError(f"crop out of the plate: {crop}")
    h_px = (bottom - top) * ph
    w_px = h_px * aspect
    if w_px > pw:
        w_px = pw
        bottom = top + (w_px / aspect) / ph
    left = min(max(cx * pw - w_px / 2, 0), pw - w_px)
    return (left / pw, top, (left + w_px) / pw, bottom)


@contextlib.contextmanager
def _lenin_pipeline(candidate: Candidate, ink_count: int):
    """Run gen_lenin's portrait/poster on this photograph: patch its three
    module-level inputs, always restore them (gen_lenin's own tests and the
    Lenin lump must never see a Stalin crop)."""
    saved = lenin.PHOTO, lenin.CROP, lenin.INK_COUNT
    try:
        with Image.open(candidate.photo) as im:
            plate = im.size
        lenin.PHOTO = candidate.photo
        lenin.CROP = fit_crop(plate, candidate.crop)
        lenin.INK_COUNT = ink_count
        yield
    finally:
        lenin.PHOTO, lenin.CROP, lenin.INK_COUNT = saved


def candidate(key: str | None = None) -> Candidate:
    key = key or DEFAULT_CANDIDATE
    if key not in CANDIDATES:
        raise SystemExit(f"unknown candidate {key!r}; one of {', '.join(CANDIDATES)}")
    c = CANDIDATES[key]
    if not c.photo.is_file():
        shown = c.photo.relative_to(PROJECT_ROOT) if c.photo.is_relative_to(PROJECT_ROOT) else c.photo
        raise SystemExit(
            f"reference photograph absent: {shown}\n"
            f"It is downloaded once, by hand, with the CEO's permission, from\n"
            f"https://commons.wikimedia.org/wiki/{c.commons_file.replace(' ', '_')}\n"
            f"(see docs/product/2026-10-14_1556_F2_stalin-poster-sourcing.md).")
    return c


def portrait(bias: int = CUT_BIAS, key: str | None = None, ink_count: int = INK_COUNT) -> np.ndarray:
    with _lenin_pipeline(candidate(key), ink_count):
        return lenin.portrait(bias)


# --- the slogan stamp ----------------------------------------------------
def slogan_lines(slogan: str) -> list[str]:
    return [ln.strip() for ln in slogan.replace("|", "\n").split("\n") if ln.strip()]


def slogan_mask(slogan: str) -> tuple[Image.Image, int]:
    """Hard 1-bit mask of the slogan, SLOGAN_BAND tall, centred in the band
    below the gold rule; and the font size it fitted at. Largest size from
    SLOGAN_SIZE down that fits; ValueError if not even SLOGAN_MIN_SIZE does."""
    lines = slogan_lines(slogan)
    if not lines:
        return Image.new("1", (WIDTH, SLOGAN_BAND), 0), 0
    for size in range(SLOGAN_SIZE, SLOGAN_MIN_SIZE - 1, -1):
        f = ImageFont.truetype(FONT_POSTER, size)
        cap_top, cap_bottom = f.getbbox(CAP_REFERENCE)[1::2]
        pitch = (cap_bottom - cap_top) + SLOGAN_LINE_GAP
        # draw on a generous scratch canvas, then measure what was inked
        scratch = Image.new("L", (WIDTH * 3, SLOGAN_BAND * 3), 0)
        d = ImageDraw.Draw(scratch)
        for i, line in enumerate(lines):
            bb = d.textbbox((0, 0), line, font=f)
            x = (scratch.width - (bb[2] - bb[0])) // 2 - bb[0]
            d.text((x, SLOGAN_BAND + i * pitch - cap_top), line, font=f, fill=255)
        hard = scratch.point(lambda v: 255 if v >= SLOGAN_MASK_CUT else 0)
        box = hard.getbbox()
        if box is None:
            continue
        w, h = box[2] - box[0], box[3] - box[1]
        if w <= SLOGAN_MAX_WIDTH and h <= SLOGAN_MAX_HEIGHT:
            mask = Image.new("L", (WIDTH, SLOGAN_BAND), 0)
            top = 1 + SLOGAN_V_PAD + (SLOGAN_MAX_HEIGHT - h) // 2
            mask.paste(hard.crop(box), ((WIDTH - w) // 2, top))
            return mask.convert("1", dither=Image.Dither.NONE), size
    raise ValueError(f"slogan does not fit the band even at {SLOGAN_MIN_SIZE} px: {lines}")


def stamp_slogan(im: Image.Image, slogan: str, top: int = BODY) -> int:
    """Paste flat cream through the hard mask into the band starting at row
    `top`. Returns the font size used (0 for no slogan)."""
    mask, size = slogan_mask(slogan)
    if size:
        cream = inks()[3]
        im.paste(Image.new("RGB", mask.size, cream), (0, top), mask)
    return size


def slogan_band(slogan: str) -> Image.Image:
    """The bottom band alone, framed exactly as on the poster: needs no
    photograph, so the slogan can be reviewed (and tested) before the
    download."""
    _, red, _, cream = inks()
    gold = ramp_colour("hazard_yellow", 0.86)
    band = Image.new("RGB", (WIDTH, SLOGAN_BAND), red)
    d = ImageDraw.Draw(band)
    for i in range(BORDER):   # the poster's border: sides and bottom
        d.line([(i, 0), (i, SLOGAN_BAND - 1)], fill=cream)
        d.line([(WIDTH - 1 - i, 0), (WIDTH - 1 - i, SLOGAN_BAND - 1)], fill=cream)
        d.line([(0, SLOGAN_BAND - 1 - i), (WIDTH - 1, SLOGAN_BAND - 1 - i)], fill=cream)
    d.line([(BORDER, 0), (WIDTH - 1 - BORDER, 0)], fill=gold, width=1)
    stamp_slogan(band, slogan, top=0)
    return band


def poster(bias: int = CUT_BIAS, slogan: str = SLOGAN, key: str | None = None,
           ink_count: int = INK_COUNT) -> Image.Image:
    """gen_lenin.poster, unchanged, with no slogan; then the multi-line stamp."""
    with _lenin_pipeline(candidate(key), ink_count):
        im = lenin.poster(bias, slogan="")
    stamp_slogan(im, slogan)
    return im


# --- review sheets --------------------------------------------------------
def sweep(path: Path, key: str | None = None) -> None:
    """3 ink counts x 5 cut points, the layout of Lenin's sheet; the CEO
    points at one cell (e.g. 4C)."""
    c = candidate(key)
    zoom, label, gap = 2, 22, 8
    sheet = Image.new("RGB", (len(SWEEP_BIASES) * (WIDTH * zoom + gap) + gap,
                              len(SWEEP_INKS) * (BODY * zoom + label + gap) + gap + 24), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT_SMALL, 15)    # sheet labels only, not the poster
    fs = ImageFont.truetype(FONT_SMALL, 12)
    d.text((gap, 6), f"Stalin ({c.key}) - posterisation sweep. Point at one cell (e.g. 4C).",
           font=f, fill=(255, 230, 120))
    for r, n in enumerate(SWEEP_INKS):
        for col, b in enumerate(SWEEP_BIASES):
            im = Image.fromarray(portrait(b, c.key, n)).resize((WIDTH * zoom, BODY * zoom), Image.NEAREST)
            x, y = gap + col * (WIDTH * zoom + gap), 24 + gap + r * (BODY * zoom + label + gap)
            sheet.paste(im, (x, y + label))
            d.text((x + 2, y + 3), f"{n}{chr(65 + col)}  {n} inks  cut {b:+d}", font=fs, fill=(235,) * 3)
    sheet.save(path)


def slogan_sheet(path: Path, zoom: int = 3) -> None:
    """Every slogan option in its band at 1x and `zoom`x; no photograph."""
    gap, label = 10, 18
    keys = list(SLOGANS)
    sheet = Image.new("RGB", (gap + WIDTH + gap + WIDTH * zoom + gap,
                              24 + len(keys) * (SLOGAN_BAND * zoom + label + gap) + gap), (22, 22, 22))
    d = ImageDraw.Draw(sheet)
    fs = ImageFont.truetype(FONT_SMALL, 12)
    d.text((gap, 6), "Stalin poster - slogan options (1x and 3x)", font=fs, fill=(255, 230, 120))
    for i, k in enumerate(keys):
        band = slogan_band(SLOGANS[k])
        _, size = slogan_mask(SLOGANS[k])
        y = 24 + i * (SLOGAN_BAND * zoom + label + gap)
        d.text((gap, y), f"{k}  ({size} px; Lenin's is {SLOGAN_SIZE})", font=fs, fill=(235,) * 3)
        sheet.paste(band, (gap, y + label))
        sheet.paste(band.resize((WIDTH * zoom, SLOGAN_BAND * zoom), Image.NEAREST),
                    (gap + WIDTH + gap, y + label))
    sheet.save(path)


def preview(path: Path, key: str | None = None, bias: int = CUT_BIAS,
            ink_count: int = INK_COUNT, zoom: int = 2) -> None:
    """The CEO's sheet: the 15-cell sweep on top, then the poster at the
    current cell with every slogan option, at `zoom`x. One file to look at."""
    c = candidate(key)
    tmp = path.with_name(path.stem + "_sweep_part.png")
    sweep(tmp, c.key)
    with Image.open(tmp) as top_img:
        top = top_img.copy()
    tmp.unlink()
    gap, label = 8, 22
    pw, ph = WIDTH * zoom, HEIGHT * zoom
    sheet = Image.new("RGB", (max(top.width, gap + len(SLOGANS) * (pw + gap)),
                              top.height + 24 + label + ph + gap), (22, 22, 22))
    sheet.paste(top, (0, 0))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT_SMALL, 15)
    fs = ImageFont.truetype(FONT_SMALL, 12)
    y = top.height + 4
    d.text((gap, y), f"Slogan options on the full poster (cell {ink_count}"
           f"{chr(65 + SWEEP_BIASES.index(bias)) if bias in SWEEP_BIASES else '?'}, {zoom}x)",
           font=f, fill=(255, 230, 120))
    for i, (k, text) in enumerate(SLOGANS.items()):
        x = gap + i * (pw + gap)
        d.text((x + 2, y + 22), f"{k}  ({slogan_mask(text)[1]} px)", font=fs, fill=(235,) * 3)
        im = poster(bias, text, c.key, ink_count).resize((pw, ph), Image.NEAREST)
        sheet.paste(im, (x, y + 20 + label))
    sheet.save(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidate", default=DEFAULT_CANDIDATE, choices=sorted(CANDIDATES))
    ap.add_argument("--sweep", action="store_true", help="write the 15-cell review sheet")
    ap.add_argument("--slogans", action="store_true", help="write the slogan sheet (no photo needed)")
    ap.add_argument("--preview", action="store_true", help="sweep + slogan options on full posters")
    ap.add_argument("--bias", type=int, default=CUT_BIAS, help="shift every cut point (sweep column)")
    ap.add_argument("--inks", type=int, default=INK_COUNT, choices=SWEEP_INKS, help="ink count (sweep row)")
    ap.add_argument("--slogan", default=SLOGAN, help='lines separated by "|"; a key of SLOGANS; "" for none')
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.preview:
        out = args.out_dir / f"stalin_{args.candidate}_preview.png"
        preview(out, args.candidate, args.bias, args.inks)
    elif args.slogans:
        out = args.out_dir / "stalin_slogans.png"
        slogan_sheet(out)
    elif args.sweep:
        out = args.out_dir / f"stalin_{args.candidate}_sweep.png"
        sweep(out, args.candidate)
    else:
        out = args.out_dir / "stalin_poster.png"   # lump name is the PM's/level-designer's call
        slogan = SLOGANS.get(args.slogan, args.slogan)
        im = poster(args.bias, slogan, args.candidate, args.inks)
        used = len({tuple(p) for p in np.array(im).reshape(-1, 3)})
        im.convert("P", palette=Image.ADAPTIVE, colors=max(used, 2)).save(out)
        print(f"stalin {args.candidate}  {im.width}x{im.height}  colours={used}  "
              f"inks={args.inks}  bias={args.bias:+d}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
