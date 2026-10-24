#!/usr/bin/env python3
"""Marx and Engels: a PAIR of propaganda posters, 128x256 each (SDPOSTR4, SDPOSTR5).

CEO, 2026-10-22: "quiero más cuadros comunistas; siguiendo los de Lenin y
Stalin que quedaron muy bien, haz uno con Marx y Engels" ("I want more
communist pictures; following the Lenin and Stalin ones, which came out very
well, make one with Marx and Engels"). Format approved the same day (phase 2 of the commission): two posters the size and style of
SDPOSTR1/3, heads at their scale (~85-95 px wide), Marx on the left carrying
«ПРОЛЕТАРИИ / ВСЕХ СТРАН,», Engels on the right carrying «СОЕДИНЯЙТЕСЬ!», so
that hung together they read the closing line of the Communist Manifesto and
each one still works alone.

APPROVED (D117, 2026-10-22): Marx cell 4D (four inks, cut +9), Engels cell 4C
(four inks, cut +0) MIRRORED so he looks at Marx, the `short` split at 17 px,
Engels's word on the row of Marx's second line (`pair`). Installed as
SDPOSTR4 (Marx) and SDPOSTR5 (Engels) in assets/textures/soviet_base/, each
copied byte for byte from work/art/marx_engels/SDPOSTR4.png / SDPOSTR5.png,
the default output of a plain run.

So each poster is gen_stalin's twin of Lenin, nothing more:

  same format   128x256, cream printed border, gold rule, 46 px slogan band
  same method   a public-domain photograph posterised to N flat inks of
                palette v1, cuts at PERCENTILES of the crop
  same review   a 15-cell sweep per portrait (2/3/4 inks x 5 cut points); the
                CEO points at a cell, as he picked 4C for Lenin and Stalin

What the pair adds: one slogan size for both bands (the largest at which
every line of both fits), and the lines laid on a shared grid, so Engels's
word sits on the row of Marx's second line and the sentence runs across the
two posters.

Orientation (seen on the plates, 2026-10-22): Marx faces the viewer, his body
turned towards the left edge; Engels is a three-quarter view looking towards
the RIGHT edge, i.e. away from Marx once hung on his right. MIRROR_ENGELS
flips Engels's portrait so the two face each other. A flip changes the
likeness (hair parting, beard); the CEO approved it (D117) on a sheet that
showed the pair both ways.

Reuse, not copy: the posterisation and the frame are gen_lenin.poster, run
through gen_stalin's patch-and-restore pipeline with each photograph's path,
crop and ink count; the aspect-true crop is gen_stalin.fit_crop; the
indexed-PNG writer is gen_stalin.to_lump. Neither file is edited.

The photographs are NOT downloaded by this script. They were fetched once,
by the PM with the CEO's permission (2026-10-22), into work/art/reference/
(gitignored, never shipped). If one is missing the script stops and names
the Commons page. Sources, hashes and legal reasoning:
docs/product/2026-10-22_P4_marx-engels-poster-sourcing.md.

Run with the project venv (Windows: .venv/Scripts/python.exe):
  python tools/art/gen_marx_engels.py --preview   # the CEO's sheet (two sweeps + the pair)
  python tools/art/gen_marx_engels.py --sweep     # one sweep sheet per portrait
  python tools/art/gen_marx_engels.py --slogans   # the two bands, needs no photo
  python tools/art/gen_marx_engels.py             # SDPOSTR4 + SDPOSTR5 (D117) -> work/art/marx_engels/
  options: --inks 4 --bias 0 --engels-as-photographed --split ceo|short --align pair|centre

Only the approved parameters write files named after the lumps (as gen_stalin
does for D55): any option that changes a pixel writes
marx_engels_<person>_poster.png instead, because tests/test_art.py matches
assets/ to work/ by name. Nothing here writes to assets/; installing is a
byte-for-byte copy.

Text-bearing asset (CLAUDE.md, D27): the slogan is rasterised by this
machine's Impact. SDPOSTR4/5 were rendered on the CEO's WINDOWS PC, so they
are regenerated ONLY ON WINDOWS; tests/test_gen_marx_engels.py holds the
generator to the installed lumps there and skips on the Mac.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_lenin as lenin  # noqa: E402
import gen_stalin as stalin  # noqa: E402
from artlib import FONT_POSTER, FONT_SMALL, ramp_colour  # noqa: E402

PROJECT_ROOT = lenin.PROJECT_ROOT
REFERENCE_DIR = PROJECT_ROOT / "work" / "art" / "reference"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "marx_engels"
PREVIEW_PATH = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_marx-engels-sweep.png"
SOURCING_DOC = "docs/product/2026-10-22_P4_marx-engels-poster-sourcing.md"

# The format is Lenin's, by commission: imported, never restated.
WIDTH, HEIGHT = lenin.WIDTH, lenin.HEIGHT
SLOGAN_BAND, BORDER = lenin.SLOGAN_BAND, lenin.BORDER
BODY = HEIGHT - SLOGAN_BAND
inks = lenin.inks


def gold() -> tuple[int, int, int]:
    return ramp_colour("hazard_yellow", 0.86)   # the rule of SDPOSTR1/3


# --- the photographs ------------------------------------------------------
@dataclass(frozen=True)
class Candidate:
    """One public-domain photograph on Wikimedia Commons.

    crop is (centre_x, top, bottom) as fractions of the plate; the width is
    derived by gen_stalin.fit_crop so the crop has the portrait's aspect.
    The two downloaded plates' crops were set on the photographs; the
    fallbacks' are PROVISIONAL guesses (never downloaded)."""
    person: str                       # "marx" or "engels"
    key: str
    filename: str                     # under work/art/reference/
    commons_file: str
    plate: tuple[int, int]            # width, height on Commons (API, 2026-10-22)
    bytes: int
    crop: tuple[float, float, float]  # centre_x, top, bottom
    note: str = ""

    @property
    def photo(self) -> Path:
        return REFERENCE_DIR / self.filename

    @property
    def commons_url(self) -> str:
        return "https://commons.wikimedia.org/wiki/" + self.commons_file.replace(" ", "_")


MARX: dict[str, Candidate] = {c.key: c for c in (
    # Set on the plate 2026-10-22: the head (mane to beard) spans x 0.42-0.78,
    # y 0.17-0.43 of 1428x2048; centred on it with a little headroom, down to
    # the hand in the waistcoat. Crop x ~0.34-0.86, y 0.11-0.66.
    Candidate("marx", "1875", "marx_1875.jpg", "File:Karl Marx 001.jpg", (1428, 2048), 380_651,
              (0.60, 0.11, 0.66), "J. J. E. Mayall, London 1875, IISH scan - DOWNLOADED"),
    Candidate("marx", "1875s", "marx_1875s.png",
              "File:Karl Marx by John Jabez Edwin Mayall 1875 - Restored (cropped).png", (1481, 1976),
              1_376_570, (0.55, 0.02, 0.59), "the same sitting, Staedel print - PROVISIONAL crop"),
)}
ENGELS: dict[str, Candidate] = {c.key: c for c in (
    # Set on the plate 2026-10-22: the head (hair to beard tip) spans x 0.33-0.72,
    # y 0.19-0.52 of 945x1437, inside the print's oval vignette; the crop
    # stays inside the oval, so no cream card shows in the corners.
    Candidate("engels", "1877", "engels_1877.jpg", "File:Friedrich Engels portrait.jpg", (945, 1437), 514_277,
              (0.53, 0.16, 0.66), "William Hall, May 1877 - DOWNLOADED"),
    Candidate("engels", "1891", "engels_1891.jpg", "File:Friedrich Engels (1891).jpg", (993, 1163), 207_124,
              (0.50, 0.02, 0.77), "W. E. Debenham, London 1891 - PROVISIONAL crop"),
)}
DEFAULT_MARX, DEFAULT_ENGELS = "1875", "1877"
MIRROR_ENGELS = True                  # APPROVED (D117): flipped so the two face each other

# --- separation: the cells the CEO approved (D117) ---------------------------
# Marx 4D: at 4C the light studio wall left of his head turns into a cream
# field; one column darker it drops to red and the mane and beard stand out.
# Engels 4C, Lenin's and Stalin's cell: 4D speckles his face with red.
INK_COUNT = {"marx": 4, "engels": 4}
CUT_BIAS = {"marx": 9, "engels": 0}
SWEEP_INKS = stalin.SWEEP_INKS        # rows: 2, 3, 4 inks
SWEEP_BIASES = stalin.SWEEP_BIASES    # columns: -18 .. +18

# --- slogan: one sentence over two posters ------------------------------------
# Each split is (Marx's lines, Engels's lines). "ceo" is the split the CEO
# first asked for (15 px); "short" breaks Marx's text earlier so the pair
# stamps 2 px larger (17 px): the one APPROVED (D117).
SPLITS = {
    "ceo": (("ПРОЛЕТАРИИ ВСЕХ", "СТРАН,"), ("СОЕДИНЯЙТЕСЬ!",)),
    "short": (("ПРОЛЕТАРИИ", "ВСЕХ СТРАН,"), ("СОЕДИНЯЙТЕСЬ!",)),
}
DEFAULT_SPLIT = "short"                # D117
# "pair": Engels's word on the row of Marx's LAST line, so the sentence runs
# across; "centre": each band centred on its own.
ALIGNS = ("pair", "centre")
DEFAULT_ALIGN = "pair"                 # D117
SLOGAN_SIZE = lenin.SLOGAN_SIZE       # 19 px, Lenin's: the stamp starts here...
SLOGAN_MIN_SIZE = stalin.SLOGAN_MIN_SIZE   # ...and shrinks a pixel at a time to 12
SLOGAN_SIDE_PAD = stalin.SLOGAN_SIDE_PAD
SLOGAN_V_PAD = stalin.SLOGAN_V_PAD
SLOGAN_LINE_GAP = stalin.SLOGAN_LINE_GAP
SLOGAN_MASK_CUT = lenin.SLOGAN_MASK_CUT
SLOGAN_MAX_WIDTH = WIDTH - 2 * (BORDER + SLOGAN_SIDE_PAD)
SLOGAN_MAX_HEIGHT = SLOGAN_BAND - 1 - 2 * SLOGAN_V_PAD   # row 0 is the gold rule
CAP_REFERENCE = stalin.CAP_REFERENCE

# --- the lumps (approved, D117) ------------------------------------------------
LUMPS = {"marx": "SDPOSTR4", "engels": "SDPOSTR5"}
PEOPLE = ("marx", "engels")           # hanging order, left to right
# The files copied byte for byte into assets/ (the plain run's output) and
# where they are installed.
LUMP_PATHS = {p: OUT_DIR / f"{name}.png" for p, name in LUMPS.items()}
ASSET_PATHS = {p: PROJECT_ROOT / "assets" / "textures" / "soviet_base" / f"{name}.png"
               for p, name in LUMPS.items()}


def poster_file(person: str) -> str:
    """The name of a NON-approved render: never a lump's name, because
    test_art matches assets/ to work/ by name."""
    return f"marx_engels_{person}_poster.png"


# --- photographs: lookup and the missing-file message ----------------------
def _shown(p: Path) -> str:
    try:
        return p.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(p)


def pair(marx: str | None = None, engels: str | None = None) -> dict[str, Candidate]:
    """Both candidates, on disk; SystemExit naming EVERY missing file and its
    Commons page otherwise (one message, not a traceback)."""
    marx, engels = marx or DEFAULT_MARX, engels or DEFAULT_ENGELS
    if marx not in MARX:
        raise SystemExit(f"unknown Marx candidate {marx!r}; one of {', '.join(MARX)}")
    if engels not in ENGELS:
        raise SystemExit(f"unknown Engels candidate {engels!r}; one of {', '.join(ENGELS)}")
    chosen = {"marx": MARX[marx], "engels": ENGELS[engels]}
    missing = [c for c in chosen.values() if not c.photo.is_file()]
    if missing:
        lines = ["reference photograph(s) absent:"]
        for c in missing:
            lines += [f"  {_shown(c.photo)}", f"    from {c.commons_url}"]
        lines += ["They are downloaded once, by hand, with the CEO's permission",
                  f"(see {SOURCING_DOC}). This script never downloads."]
        raise SystemExit("\n".join(lines))
    return chosen


# --- the portrait -----------------------------------------------------------
def plain_poster(c: Candidate, bias: int, ink_count: int, mirror: bool = False) -> Image.Image:
    """gen_lenin.poster on this photograph with no slogan: portrait, border,
    gold rule, red band. The frame is symmetric, so mirroring the portrait
    rows mirrors the portrait alone."""
    with stalin._lenin_pipeline(c, ink_count):
        im = lenin.poster(bias, slogan="")
    if mirror:
        a = np.array(im)
        a[:BODY] = a[:BODY, ::-1]
        im = Image.fromarray(a)
    return im


def portrait(c: Candidate, bias: int, ink_count: int, mirror: bool = False) -> np.ndarray:
    """The portrait rows of the plain poster, printed border included."""
    return np.asarray(plain_poster(c, bias, ink_count, mirror))[:BODY]


# --- the shared slogan grid -------------------------------------------------
LINE_MARGIN = 12   # px kept above the cap top on the scratch line: room for Й's breve


def _line_mask(text: str, font: ImageFont.FreeTypeFont, cap_top: int) -> Image.Image:
    """One line, hard-cut, on a scratch canvas whose row LINE_MARGIN is the cap top."""
    scratch = Image.new("L", (WIDTH * 3, SLOGAN_BAND * 2), 0)
    d = ImageDraw.Draw(scratch)
    bb = d.textbbox((0, 0), text, font=font)
    d.text(((scratch.width - (bb[2] - bb[0])) // 2 - bb[0], LINE_MARGIN - cap_top),
           text, font=font, fill=255)
    return scratch.point(lambda v: 255 if v >= SLOGAN_MASK_CUT else 0)


def _compose(person: str, split: str, align: str, size: int) -> Image.Image:
    """This person's lines on the pair's grid, as an L mask of the band. The
    grid is centred in the band as if it held the pair's tallest part; with
    align="pair" a shorter part sits on the LAST rows, level with the other
    poster's last line. Raises ValueError if any ink would leave the band."""
    if align not in ALIGNS:
        raise ValueError(f"align is one of {ALIGNS}")
    lines = SPLITS[split][PEOPLE.index(person)]
    f = ImageFont.truetype(FONT_POSTER, size)
    cap_top, cap_bottom = f.getbbox(CAP_REFERENCE)[1::2]
    cap = cap_bottom - cap_top
    pitch = cap + SLOGAN_LINE_GAP
    rows = max(len(part) for part in SPLITS[split]) if align == "pair" else len(lines)
    block = rows * cap + (rows - 1) * SLOGAN_LINE_GAP
    top = 1 + SLOGAN_V_PAD + (SLOGAN_MAX_HEIGHT - block) // 2
    first_row = rows - len(lines)
    mask = Image.new("L", (WIDTH, SLOGAN_BAND), 0)
    for i, line in enumerate(lines):
        m = _line_mask(line, f, cap_top)
        box = m.getbbox()
        if box is None:
            continue
        w = box[2] - box[0]
        y = top + (first_row + i) * pitch + (box[1] - LINE_MARGIN)
        if w > SLOGAN_MAX_WIDTH or y < 1 or y + (box[3] - box[1]) > SLOGAN_BAND - BORDER:
            raise ValueError(f"{line!r} does not fit the band at {size} px")
        glyphs = m.crop(box)
        mask.paste(glyphs, ((WIDTH - w) // 2, y), glyphs)
    return mask


def pair_size(split: str = DEFAULT_SPLIT) -> int:
    """The one size both bands stamp at: the largest from SLOGAN_SIZE down at
    which every line of both posters fits in either alignment; ValueError if
    none does."""
    for size in range(SLOGAN_SIZE, SLOGAN_MIN_SIZE - 1, -1):
        try:
            for person in PEOPLE:
                for align in ALIGNS:
                    _compose(person, split, align, size)
        except ValueError:
            continue
        return size
    raise ValueError(f"split {split!r} does not fit even at {SLOGAN_MIN_SIZE} px")


def slogan_mask(person: str, split: str = DEFAULT_SPLIT, align: str = DEFAULT_ALIGN,
                size: int | None = None) -> tuple[Image.Image, int]:
    """Hard 1-bit mask of this person's part of the sentence, WIDTH x
    SLOGAN_BAND, at the pair's shared size; and that size."""
    size = size or pair_size(split)
    return _compose(person, split, align, size).convert("1", dither=Image.Dither.NONE), size


def stamp(im: Image.Image, person: str, split: str = DEFAULT_SPLIT, align: str = DEFAULT_ALIGN) -> int:
    """Flat cream through the hard mask into the band. Returns the size."""
    mask, size = slogan_mask(person, split, align)
    im.paste(Image.new("RGB", mask.size, inks()[3]), (0, BODY), mask)
    return size


def slogan_band(person: str, split: str = DEFAULT_SPLIT, align: str = DEFAULT_ALIGN) -> Image.Image:
    """The bottom band alone, framed as on the poster; needs no photograph."""
    _, red, _, cream = inks()
    band = Image.new("RGB", (WIDTH, HEIGHT), red)
    d = ImageDraw.Draw(band)
    for i in range(BORDER):
        d.rectangle([i, i, WIDTH - 1 - i, HEIGHT - 1 - i], outline=cream)
    d.line([(BORDER, BODY), (WIDTH - 1 - BORDER, BODY)], fill=gold(), width=1)
    stamp(band, person, split, align)
    return band.crop((0, BODY, WIDTH, HEIGHT))


# --- the posters ------------------------------------------------------------
def poster(person: str, bias: int | None = None, ink_count: int | None = None,
           mirror: bool | None = None, split: str = DEFAULT_SPLIT, align: str = DEFAULT_ALIGN,
           marx: str | None = None, engels: str | None = None, slogan: bool = True) -> Image.Image:
    c = pair(marx, engels)[person]
    bias = CUT_BIAS[person] if bias is None else bias
    ink_count = INK_COUNT[person] if ink_count is None else ink_count
    mirror = (MIRROR_ENGELS and person == "engels") if mirror is None else mirror
    im = plain_poster(c, bias, ink_count, mirror)
    if slogan:
        stamp(im, person, split, align)
    return im


def posters(**kw) -> dict[str, Image.Image]:
    """Both, at their approved cells; keyword arguments go to poster()."""
    return {p: poster(p, **kw) for p in PEOPLE}


def mounted(left: Image.Image, right: Image.Image, gap: int = 0) -> Image.Image:
    """The pair hung side by side, Marx on the left."""
    out = Image.new("RGB", (left.width + gap + right.width, HEIGHT), (22, 22, 22))
    out.paste(left, (0, 0))
    out.paste(right, (left.width + gap, 0))
    return out


to_lump = stalin.to_lump   # RGB -> indexed PNG, an adaptive palette exactly the inks used


def lump(person: str) -> Image.Image:
    """SDPOSTR4 (marx) or SDPOSTR5 (engels) as approved (D117): the default
    photographs, cells, mirror, split and alignment."""
    return to_lump(poster(person))


# --- review sheets ----------------------------------------------------------
SHEET_BG = (22, 22, 22)
TITLE_INK, LABEL_INK, NOTE_INK = (255, 230, 120), (235, 235, 235), (255, 150, 120)


def cell_name(ink_count: int, bias: int) -> str:
    col = chr(65 + SWEEP_BIASES.index(bias)) if bias in SWEEP_BIASES else "?"
    return f"{ink_count}{col}"


def sweep_sheet(person: str, c: Candidate, mirror: bool, zoom: int = 2) -> Image.Image:
    """3 ink counts x 5 cut points of one portrait, Lenin's layout and labels."""
    label, gap, head = 22, 8, 26
    cw, ch = WIDTH * zoom, BODY * zoom
    sheet = Image.new("RGB", (len(SWEEP_BIASES) * (cw + gap) + gap,
                              len(SWEEP_INKS) * (ch + label + gap) + gap + head), SHEET_BG)
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT_SMALL, 15)    # sheet labels only, not the poster
    fs = ImageFont.truetype(FONT_SMALL, 12)
    flip = "  (mirrored)" if mirror else ""
    d.text((gap, 6), f"{LUMPS[person]} {person.capitalize()} ({c.key}){flip} - sweep. Point at a cell.",
           font=f, fill=TITLE_INK)
    for r, n in enumerate(SWEEP_INKS):
        for col, b in enumerate(SWEEP_BIASES):
            im = Image.fromarray(portrait(c, b, n, mirror)).resize((cw, ch), Image.NEAREST)
            x, y = gap + col * (cw + gap), head + gap + r * (ch + label + gap)
            sheet.paste(im, (x, y + label))
            d.text((x + 2, y + 3), f"{cell_name(n, b)}  {n} inks  cut {b:+d}", font=fs, fill=LABEL_INK)
    return sheet


def sweep(out_dir: Path, marx: str | None = None, engels: str | None = None,
          mirror_engels: bool = MIRROR_ENGELS) -> list[Path]:
    chosen = pair(marx, engels)
    paths = []
    for p in PEOPLE:
        path = out_dir / f"marx_engels_{p}_{chosen[p].key}_sweep.png"
        sweep_sheet(p, chosen[p], p == "engels" and mirror_engels).save(path)
        paths.append(path)
    return paths


def slogan_sheet(path: Path, zoom: int = 3) -> None:
    """Both bands, side by side as hung, for each split and alignment; no photograph."""
    gap, label = 10, 18
    combos = [(s, a) for s in SPLITS for a in ALIGNS]
    pw = 2 * WIDTH * zoom
    sheet = Image.new("RGB", (gap + pw + gap, 24 + len(combos) * (SLOGAN_BAND * zoom + label + gap) + gap),
                      SHEET_BG)
    d = ImageDraw.Draw(sheet)
    fs = ImageFont.truetype(FONT_SMALL, 12)
    d.text((gap, 6), f"Marx | Engels bands, as hung ({zoom}x)", font=fs, fill=TITLE_INK)
    for i, (s, a) in enumerate(combos):
        y = 24 + i * (SLOGAN_BAND * zoom + label + gap)
        star = "  (approved)" if (s, a) == (DEFAULT_SPLIT, DEFAULT_ALIGN) else ""
        d.text((gap, y), f"split {s}, align {a}: {pair_size(s)} px (Lenin's is {SLOGAN_SIZE}){star}",
               font=fs, fill=LABEL_INK)
        bands = mounted(slogan_band("marx", s, a), slogan_band("engels", s, a)).crop((0, 0, 2 * WIDTH, SLOGAN_BAND))
        sheet.paste(bands.resize((pw, SLOGAN_BAND * zoom), Image.NEAREST), (gap, y + label))
    sheet.save(path)


def preview(path: Path, marx: str | None = None, engels: str | None = None, zoom: int = 2) -> None:
    """The CEO's sheet: Marx's 15 cells and Engels's 15 cells side by side,
    then the pair hung together at the approved cells: as approved, with
    Engels as photographed, with the short split, and centred bands."""
    chosen = pair(marx, engels)
    sweeps = [sweep_sheet(p, chosen[p], p == "engels" and MIRROR_ENGELS, zoom) for p in PEOPLE]
    kw = {"marx": chosen["marx"].key, "engels": chosen["engels"].key}
    other = next(s for s in SPLITS if s != DEFAULT_SPLIT)
    variants = [
        ("APPROVED (D117): Engels mirrored (faces Marx)", {}),
        ("Engels as photographed (looks away)", {"mirror": False}),
        (f"split '{other}' ({pair_size(other)} px)", {"split": other}),
        ("bands centred, each on its own", {"align": "centre"}),
    ]
    mounts = []
    for text, extra in variants:
        m = poster("marx", **kw, **{k: v for k, v in extra.items() if k != "mirror"})
        e = poster("engels", **kw, **extra)
        mounts.append((text, mounted(m, e)))
    gap, label = 12, 22
    sw = sum(s.width for s in sweeps) + gap
    mw = gap + sum(im.width * zoom + 3 * gap for _, im in mounts)
    top_h = max(s.height for s in sweeps)
    sheet = Image.new("RGB", (max(sw, mw), top_h + 40 + label + HEIGHT * zoom + gap + 22), SHEET_BG)
    x = 0
    for s in sweeps:
        sheet.paste(s, (x, 0))
        x += s.width + gap
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(FONT_SMALL, 15)
    fs = ImageFont.truetype(FONT_SMALL, 12)
    y = top_h + 8
    d.text((gap, y), f"The pair as hung, Marx left (Marx {cell_name(INK_COUNT['marx'], CUT_BIAS['marx'])}, "
           f"Engels {cell_name(INK_COUNT['engels'], CUT_BIAS['engels'])}, {zoom}x). "
           f"Split '{DEFAULT_SPLIT}' {pair_size()} px.", font=f, fill=TITLE_INK)
    x = gap
    for text, im in mounts:
        d.text((x + 2, y + 24), text, font=fs, fill=LABEL_INK)
        sheet.paste(im.resize((im.width * zoom, HEIGHT * zoom), Image.NEAREST), (x, y + 24 + label))
        x += im.width * zoom + 3 * gap
    d.text((gap, sheet.height - 20), "Mirroring Engels changes the likeness (hair parting, beard): "
           "the CEO decides.", font=fs, fill=NOTE_INK)
    sheet.save(path)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--marx", default=DEFAULT_MARX, choices=sorted(MARX))
    ap.add_argument("--engels", default=DEFAULT_ENGELS, choices=sorted(ENGELS))
    ap.add_argument("--sweep", action="store_true", help="one 15-cell sheet per portrait")
    ap.add_argument("--slogans", action="store_true", help="the bands as hung (no photo needed)")
    ap.add_argument("--preview", nargs="?", const=PREVIEW_PATH, type=Path, default=None,
                    help=f"the CEO's sheet (default {_shown(PREVIEW_PATH)})")
    ap.add_argument("--inks", type=int, default=None, choices=SWEEP_INKS, help="both posters' ink count")
    ap.add_argument("--bias", type=int, default=None, help="both posters' cut bias")
    ap.add_argument("--engels-as-photographed", action="store_true", help="do not mirror Engels")
    ap.add_argument("--split", default=DEFAULT_SPLIT, choices=sorted(SPLITS))
    ap.add_argument("--align", default=DEFAULT_ALIGN, choices=ALIGNS)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args(argv)
    if args.slogans:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        out = args.out_dir / "marx_engels_slogans.png"
        slogan_sheet(out)
        print(f"wrote {out}")
        return 0
    chosen = pair(args.marx, args.engels)   # stops here, cleanly, if a photograph is missing
    if args.preview is not None:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        preview(args.preview, chosen["marx"].key, chosen["engels"].key)
        print(f"wrote {args.preview}")
        return 0
    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.sweep:
        for p in sweep(args.out_dir, chosen["marx"].key, chosen["engels"].key,
                       MIRROR_ENGELS and not args.engels_as_photographed):
            print(f"wrote {p}")
        return 0
    # Only the approved parameters may write a file named after a lump:
    # test_art matches assets/SDPOSTR4.png and SDPOSTR5.png to work/ by name.
    approved = (args.bias is None and args.inks is None and not args.engels_as_photographed
                and (args.split, args.align) == (DEFAULT_SPLIT, DEFAULT_ALIGN)
                and (args.marx, args.engels) == (DEFAULT_MARX, DEFAULT_ENGELS))
    for p in PEOPLE:
        mirror = False if args.engels_as_photographed else None
        im = poster(p, args.bias, args.inks, mirror, args.split, args.align,
                    chosen["marx"].key, chosen["engels"].key)
        used = len({tuple(px) for px in np.array(im).reshape(-1, 3)})
        out = args.out_dir / (f"{LUMPS[p]}.png" if approved else poster_file(p))
        to_lump(im).save(out)
        print(f"{LUMPS[p] if approved else 'proposal'} {p} {chosen[p].key}  {im.width}x{im.height}  "
              f"colours={used}")
        print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
