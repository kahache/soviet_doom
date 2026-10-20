#!/usr/bin/env python3
"""Soviet Doom - backlog M2e: a design SWEEP for the status bar and the face.
Nothing here writes to assets/: the output is work/art/hud/ and, with
--stamp, one preview sheet (HTML + PNG) in docs/art/previews/.

What the player sees today (M2 audit, docs/qa/2026-10-14_2357_M2-freedoom-audit.md,
section 6, row H1) is Freedoom's bar: STBAR, STARMS, the 42 faces STF*, the
big numbers STTNUM*/STTMINUS/STTPRCNT and the small STYSNUM*/STGNUM*. This
module proposes ours, at exactly the sizes and offsets of the Freedoom 0.13.0
lumps they would replace (FD_LUMPS, checked against the IWAD by the tests).

1. The bar (STBAR 320x32 + STARMS 38x32), three options, each with an
   English and a Russian label set (ICEBOX: the Cyrillic labels idea):
     A  olive-drab instrument panel: riveted 4BO green plate, stencilled cream labels
     B  worn steel dashboard: brushed steel, screws, engraved labels; also a
        bilingual variant "BI" (RU over EN on one picture, no localisation)
     C  propaganda band: flag-red ground, black wells framed in cream, a
        constructivist wedge, gold stars
2. The face (STF*, Doom's mugshot): Sergeant Ramon Vilanova (LORE, D14), three
   headgear options drawn straight - A ushanka, B steel helmet SSh-68,
   C VDV beret with the telnyashka - and the recommended one in all 42
   lumps (5 pain levels x 3 straight glances + turn left + turn right + ouch
   + evil grin + rampage, then god mode and dead).
3. The numbers: N1 keep Freedoom's digits (no lump), N2 stencil-segment
   digits, N3 slanted GOST 2.304 drafting digits (the Soviet engineering
   lettering); each with the small yellow/grey arms digits.

How the face is drawn (the honest part)
---------------------------------------
A face at 24x29 cannot be traced from anything (D78/D79: no copied pixels),
so it is built: a head is a set of analytic shapes (cranium ellipse, square
jaw, neck, collar, headgear) rendered 8x supersampled with a height field
(a per-row dome plus Gaussian bumps for brow ridge, eye sockets, nose,
cheekbones, lips and chin) lit from the upper left, averaged down and snapped
to the palette. The parts that must stay crisp - eyes, brows, nostrils,
mouth, the badge - are hand-placed pixel stamps drawn at 1x on top. Turning
the head (STFTL/STFTR) warps every layer round its own vertical axis (each
row treated as a cylinder), which moves the features without changing the
silhouette, so every turned frame fits the Freedoom lump's box. Pain is
painted into the albedo before the warp (bruise, cuts, blood streaks), so it
turns with the head.

Every output picture uses palette v2 colours only (docs/art/palette.json,
`colours_v2`; the beret and telnyashka need `mosaic_cobalt`, the skin
mixes `flesh_pink` and `rust_brown`). Opaque lumps (STBAR, STARMS) are
indexed PNGs; lumps drawn over something (faces, digits) are RGBA with hard
alpha (ART-BIBLE 2 exception). Faces and STTMINUS carry a grAb chunk with the
Freedoom offsets. No system font is used anywhere: every letter is bitmap
data in this file (FONT5), so the output is byte-identical on the Mac and on
the Windows PC (CLAUDE.md, "Text-bearing assets do not reproduce").

Usage
-----
    .venv/Scripts/python.exe tools/art/gen_hud.py                          # work/art/hud/
    .venv/Scripts/python.exe tools/art/gen_hud.py --stamp 2026-10-20_1200  # + docs/art/previews/
"""
from __future__ import annotations

import argparse
import base64
import functools
import html
import io
import json
import math
import struct
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ART_TOOLS = Path(__file__).resolve().parent
PROJECT_ROOT = ART_TOOLS.parents[1]
sys.path.insert(0, str(ART_TOOLS))

import palette  # noqa: E402
import sheetlib  # noqa: E402

SCRIPT_REL = "tools/art/gen_hud.py"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "hud"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
# A clean engine screenshot of MAP01 on this PC (smoke run, 464x281): its 3D
# view is the backdrop of the mocks.
GAME_SHOT = PROJECT_ROOT / "docs" / "qa" / "evidence" / "2026-10-13_1448_F3_smoke-map01-windows.png"
KEYS_DIR = PROJECT_ROOT / "assets" / "graphics" / "hud"      # STKEYS*, read only
PALETTE_VERSION = 2

# ------------------------------------------------------------ engine facts
# Freedoom 0.13.0 (iwads/freedoom2.wad): name -> (width, height, left, top
# offset). Measured from the patch headers 2026-10-20; the tests re-read the
# IWAD when it is present. Our lumps must match these exactly.
FD_LUMPS: dict[str, tuple[int, int, int, int]] = {
    "STBAR": (320, 32, 0, 0), "STARMS": (38, 32, 0, 0),
    "STTMINUS": (13, 16, 4, 0), "STTPRCNT": (13, 16, 0, 0),
    **{f"STTNUM{d}": (13, 16, 0, 0) for d in range(10)},
    **{f"STYSNUM{d}": (4, 6, 0, 0) for d in range(10)},
    **{f"STGNUM{d}": (4, 6, 0, 0) for d in range(10)},
    "STFST00": (24, 29, -5, -2), "STFST01": (24, 29, -5, -2), "STFST02": (24, 29, -5, -2),
    "STFST10": (24, 29, -5, -2), "STFST11": (24, 29, -5, -2), "STFST12": (24, 29, -5, -2),
    "STFST20": (24, 30, -5, -2), "STFST21": (24, 30, -5, -2), "STFST22": (24, 30, -5, -2),
    "STFST30": (24, 31, -5, -1), "STFST31": (24, 31, -5, -1), "STFST32": (24, 31, -5, -1),
    "STFST40": (24, 31, -5, -1), "STFST41": (24, 31, -5, -1), "STFST42": (24, 31, -5, -1),
    "STFTL00": (26, 30, -5, -1), "STFTL10": (26, 30, -5, -2), "STFTL20": (27, 30, -4, -1),
    "STFTL30": (29, 31, -2, -1), "STFTL40": (30, 31, -1, -1),
    "STFTR00": (26, 30, -3, -2), "STFTR10": (26, 30, -3, -2), "STFTR20": (27, 30, -4, -1),
    "STFTR30": (28, 30, -3, -2), "STFTR40": (28, 30, -3, -2),
    **{f"STFOUCH{p}": (24, 31, -5, -1) for p in range(5)},
    **{f"STFEVL{p}": (24, 30, -5, -2) for p in range(5)},
    **{f"STFKILL{p}": (24, 30, -5, -2) for p in range(5)},
    "STFGOD0": (24, 29, -5, -2), "STFDEAD0": (24, 31, -5, -1),
}
FACE_LUMPS = [n for n in FD_LUMPS if n.startswith("STF")]   # the 42

# gzdoom.pk3 g4.14.2 zscript/ui/statusbar/doom_sbar.zs, DrawMainBar: where
# every piece lands on the 320x200 screen (the bar's top is y = 168).
BAR_Y = 168
POS_AMMO, POS_HEALTH, POS_ARMOR = 44, 90, 221     # right edge of 3 big digits, y 171
POS_BIG_Y = 171
POS_PERCENT = ((90, 171), (221, 171))
POS_ARMS = (104, 168)
ARMS_DIGITS = {2: (111, 172), 3: (123, 172), 4: (135, 172), 5: (111, 182), 6: (123, 182), 7: (135, 182)}
POS_FACE = (143, 168)
POS_KEYS = ((239, 171), (239, 181), (239, 191))
TABLE_Y = (173, 179, 185, 191)                    # Clip, Shell, RocketAmmo, Cell
TABLE_X = (288, 314)                              # right edges: amount, max
BIG_CELL, SMALL_CELL = 13, 4                      # mono cell = width of "0"

# The bar's own layout (bar coordinates, x0, y0, x1, y1 exclusive).
WELL = {"ammo": (3, 2, 47, 20), "health": (49, 2, 104, 20), "armor": (179, 2, 236, 20)}
ARMS_BOX = (104, 0, 142, 32)
FACE_BOX = (143, 0, 178, 32)
KEY_SLOTS = [(237, 2, 248, 10), (237, 12, 248, 20), (237, 22, 248, 30)]
TABLE_BOX = (250, 2, 318, 30)
LABEL_Y = 22
LABEL_CX = {"ammo": 25, "health": 76, "arms": 123, "armor": 207}

LABELS = {
    "en": {"ammo": "AMMO", "health": "HEALTH", "arms": "ARMS", "armor": "ARMOR"},
    # The words of the Russian Doom ports' status bar: patrons, health, weapons, armour.
    "ru": {"ammo": "ПАТРОНЫ", "health": "ЗДОРОВЬЕ", "arms": "ОРУЖИЕ", "armor": "БРОНЯ"},
}
BAR_OPTIONS = ("A", "B", "C")
FACE_OPTIONS = ("A", "B", "C")
DIGIT_OPTIONS = ("N1", "N2", "N3")
RECOMMENDED = {"bar": "A", "face": "A", "digits": "N2"}

# ------------------------------------------------------------ palette
_PAL = np.array(palette.colours(PALETTE_VERSION), dtype=np.float64)
_WEIGHTS = np.array([2.0, 4.0, 3.0])


def ramp(name: str, i: int) -> tuple[int, int, int]:
    """Colour i (0 = darkest) of a palette ramp, clamped."""
    cols = palette.ramp_colours(name)
    return cols[max(0, min(len(cols) - 1, i))]


# Skin is snapped to the warm ramps only: the nearest-colour rule on the whole
# palette sends olive-tan mid-tones to khaki_olive, a sick green face.
SKIN_RAMPS = ("flesh_pink", "rust_brown", "marble_red", "flag_red", "plaster_warm")
_SKIN_PAL = np.array([c for r in SKIN_RAMPS for c in palette.ramp_colours(r)] + [(0, 0, 0)], float)


def snap(rgb: np.ndarray, pal: np.ndarray | None = None) -> np.ndarray:
    """Nearest palette-v2 colour per pixel (weighted RGB), no dithering;
    `pal` restricts the choice to a subset of palette v2."""
    pal = _PAL if pal is None else pal
    flat = np.asarray(rgb, dtype=np.float64).reshape(-1, 3)
    out = np.empty(flat.shape, np.uint8)
    for s in range(0, len(flat), 4096):
        chunk = flat[s:s + 4096]
        d = (((chunk[:, None, :] - pal[None, :, :]) ** 2) * _WEIGHTS).sum(-1)
        out[s:s + 4096] = pal[d.argmin(1)].astype(np.uint8)
    return out.reshape(np.asarray(rgb).shape[:-1] + (3,))


def snap1(c) -> tuple[int, int, int]:
    return tuple(int(v) for v in snap(np.array([[c]], float))[0, 0])


# ------------------------------------------------------------ bitmap font
# 5 rows, variable width; '#' is ink. Latin caps, digits, the Cyrillic the
# labels need. Data, not a system font (D27).
FONT5 = {
    "A": ".#.|#.#|###|#.#|#.#", "B": "##.|#.#|##.|#.#|##.", "C": ".##|#..|#..|#..|.##",
    "D": "##.|#.#|#.#|#.#|##.", "E": "###|#..|##.|#..|###", "F": "###|#..|##.|#..|#..",
    "G": ".##|#..|#.#|#.#|.##", "H": "#.#|#.#|###|#.#|#.#", "I": "###|.#.|.#.|.#.|###",
    "J": "..#|..#|..#|#.#|.#.", "K": "#.#|#.#|##.|#.#|#.#", "L": "#..|#..|#..|#..|###",
    "M": "#...#|##.##|#.#.#|#...#|#...#", "N": "#..#|##.#|#.##|#..#|#..#",
    "O": ".#.|#.#|#.#|#.#|.#.", "P": "##.|#.#|##.|#..|#..", "Q": ".#.|#.#|#.#|##.|.##",
    "R": "##.|#.#|##.|#.#|#.#", "S": ".##|#..|.#.|..#|##.", "T": "###|.#.|.#.|.#.|.#.",
    "U": "#.#|#.#|#.#|#.#|###", "V": "#.#|#.#|#.#|#.#|.#.", "W": "#...#|#...#|#.#.#|##.##|#...#",
    "X": "#.#|#.#|.#.|#.#|#.#", "Y": "#.#|#.#|.#.|.#.|.#.", "Z": "###|..#|.#.|#..|###",
    "0": "###|#.#|#.#|#.#|###", "1": ".#.|##.|.#.|.#.|###", "2": "##.|..#|.#.|#..|###",
    "3": "##.|..#|.#.|..#|##.", "4": "#.#|#.#|###|..#|..#", "5": "###|#..|##.|..#|##.",
    "6": ".##|#..|###|#.#|###", "7": "###|..#|.#.|.#.|.#.", "8": "###|#.#|###|#.#|###",
    "9": "###|#.#|###|..#|##.", " ": "..|..|..|..|..", "-": "...|...|###|...|...",
    "/": "..#|..#|.#.|#..|#..", ".": ".|.|.|.|#", ":": ".|#|.|#|.", "%": "#.#|..#|.#.|#..|#.#",
    "А": ".#.|#.#|###|#.#|#.#", "Б": "###|#..|##.|#.#|##.", "В": "##.|#.#|##.|#.#|##.",
    "Д": ".###.|.#.#.|.#.#.|#####|#...#", "Е": "###|#..|##.|#..|###",
    "Ж": "#.#.#|#.#.#|.###.|#.#.#|#.#.#", "З": "##.|..#|.#.|..#|##.",
    "И": "#..#|#..#|#.##|##.#|#..#", "Н": "#.#|#.#|###|#.#|#.#", "О": ".#.|#.#|#.#|#.#|.#.",
    "П": "###|#.#|#.#|#.#|#.#", "Р": "##.|#.#|##.|#..|#..", "Т": "###|.#.|.#.|.#.|.#.",
    "У": "#.#|#.#|.##|..#|##.", "Ы": "#...#|#...#|##..#|#.#.#|##..#",
    "Ь": "#..|#..|##.|#.#|##.", "Я": ".##|#.#|.##|#.#|#.#",
}


def glyph(ch: str) -> np.ndarray:
    rows = FONT5[ch].split("|")
    return np.array([[c == "#" for c in r] for r in rows], bool)


def text_mask(text: str, spacing: int = 1) -> np.ndarray:
    gl = [glyph(c) for c in text]
    w = sum(g.shape[1] for g in gl) + spacing * (len(gl) - 1)
    out = np.zeros((5, max(w, 1)), bool)
    x = 0
    for g in gl:
        out[:, x:x + g.shape[1]] |= g
        x += g.shape[1] + spacing
    return out


def stamp_mask(img: np.ndarray, mask: np.ndarray, x: int, y: int, colour) -> None:
    h, w = mask.shape
    sub = img[y:y + h, x:x + w]
    sub[mask[:sub.shape[0], :sub.shape[1]]] = colour


def put_text(img, text, cx, y, ink, shadow=None, outline=None, dx=1, dy=1) -> tuple[int, int]:
    """Centre `text` on column cx. Returns (x0, x1) of the ink."""
    m = text_mask(text)
    x = int(round(cx - m.shape[1] / 2))
    if outline is not None:
        for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            stamp_mask(img, m, x + ox, y + oy, outline)
    if shadow is not None:
        stamp_mask(img, m, x + dx, y + dy, shadow)
    stamp_mask(img, m, x, y, ink)
    return x, x + m.shape[1]


# ------------------------------------------------------------ PNG writers
def _png_with_grab(img: Image.Image, grab: tuple[int, int] | None) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    if grab is None:
        return data
    body = b"grAb" + struct.pack(">ii", *grab)
    chunk = struct.pack(">I", 8) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
    return data[:33] + chunk + data[33:]          # right after IHDR


def save_rgba(rgba: np.ndarray, path: Path, grab=None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_png_with_grab(Image.fromarray(rgba, "RGBA"), grab))
    return path


def save_opaque(rgb: np.ndarray, path: Path) -> Path:
    """Indexed PNG whose palette is palette v2 (the lump is opaque)."""
    pal_img = Image.new("P", (1, 1))
    flat = [int(v) for c in _PAL.astype(int) for v in c]
    pal_img.putpalette(flat + [0] * (768 - len(flat)))
    img = Image.fromarray(rgb, "RGB").quantize(palette=pal_img, dither=Image.Dither.NONE)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return path


def grab_of(name: str) -> tuple[int, int] | None:
    w, h, lo, to = FD_LUMPS[name]
    return None if (lo, to) == (0, 0) else (lo, to)


# ======================================================================
# 1. THE BAR
# ======================================================================
def _noise(h, w, cells, rng, aspect=1.0):
    from artlib import fbm
    return fbm(w, h, cells, 3, rng, aspect=aspect)


def _rect(img, box, colour):
    x0, y0, x1, y1 = box
    img[y0:y1, x0:x1] = colour


def _frame(img, box, tl, br, inset=True):
    """1-px bevel: inset (a well) = dark top-left, light bottom-right."""
    x0, y0, x1, y1 = box
    a, b = (tl, br) if not inset else (br, tl)
    img[y0, x0:x1] = a
    img[y0:y1, x0] = a
    img[y1 - 1, x0:x1] = b
    img[y0:y1, x1 - 1] = b


def _rivet(img, x, y, hi, mid, lo):
    img[y, x] = hi
    img[y, x + 1] = mid
    img[y + 1, x] = mid
    img[y + 1, x + 1] = lo


def _screw(img, x, y, hi, mid, lo):
    """3x3 slotted screw head."""
    img[y:y + 3, x:x + 3] = mid
    img[y, x:x + 2] = hi
    img[y + 2, x + 1:x + 3] = lo
    img[y + 1, x:x + 3] = lo                       # the slot


def _star5(img, cx, cy, fill, hi=None, lo=None):
    pat = ["..#..", ".###.", "#####", ".###.", ".#.#."]
    for j, row in enumerate(pat):
        for i, ch in enumerate(row):
            if ch == "#":
                img[cy - 2 + j, cx - 2 + i] = fill
    if hi is not None:
        img[cy - 1, cx - 1] = hi
    if lo is not None:
        img[cy + 1, cx + 1] = lo


def _ammo_icons(img, x, kind):
    """Four 3-px pictograms for the ammo table rows: 7.62x25 round, 12-gauge
    shell, PG-7V rocket, ROKS-3 fuel bottle (the four Doom ammo pools)."""
    brass = [ramp("hazard_yellow", i) for i in (6, 10, 13)]
    copper = [ramp("rust_brown", i) for i in (7, 11, 14)]
    red = [ramp("flag_red", i) for i in (5, 9, 12)]
    green = [ramp("military_green", i) for i in (5, 9, 13)]
    steel = [ramp("steel_blue", i) for i in (5, 9, 13)]
    for row, y in enumerate(TABLE_Y):
        yy = y - BAR_Y + 1
        if row == 0:          # cartridge: casing then bullet
            img[yy:yy + 3, x:x + 6] = brass[1]
            img[yy, x:x + 6] = brass[2]
            img[yy + 2, x:x + 6] = brass[0]
            img[yy:yy + 3, x + 6:x + 8] = copper[1]
            img[yy + 1, x + 8] = copper[1]
            img[yy, x + 6] = copper[2]
        elif row == 1:        # shell: red hull, brass head
            img[yy:yy + 3, x:x + 2] = brass[1]
            img[yy:yy + 3, x + 2:x + 8] = red[1]
            img[yy, x + 2:x + 8] = red[2]
            img[yy + 2, x:x + 8] = red[0]
        elif row == 2:        # rocket: fins, body, cone
            img[yy, x] = green[0]
            img[yy + 2, x] = green[0]
            img[yy:yy + 3, x + 1:x + 6] = green[1]
            img[yy, x + 1:x + 6] = green[2]
            img[yy:yy + 3, x + 6:x + 8] = green[2]
            img[yy + 1, x + 8:x + 10] = green[1]
        else:                 # fuel bottle: steel tank, red band
            img[yy:yy + 3, x:x + 7] = steel[1]
            img[yy, x:x + 7] = steel[2]
            img[yy:yy + 3, x + 3] = red[1]
            img[yy + 1, x + 7:x + 9] = steel[0]


def _table_slashes(img, colour):
    for y in TABLE_Y:
        yy = y - BAR_Y
        for j in range(6):
            img[yy + j, 293 - j // 2] = colour


def render_bar(option: str, lang: str) -> np.ndarray:
    """STBAR (320x32 RGB) of one option in one language ('en', 'ru' or 'bi')."""
    return _render_bar(option, lang).copy()


@functools.lru_cache(maxsize=None)
def _render_bar(option: str, lang: str) -> np.ndarray:
    rng = np.random.default_rng({"A": 101, "B": 202, "C": 303}[option])
    h, w = FD_LUMPS["STBAR"][1], FD_LUMPS["STBAR"][0]
    if option == "A":
        n = _noise(h, w, 24, rng) * 0.7 + rng.random((h, w)) * 0.3
        img = np.zeros((h, w, 3))
        base = np.array([ramp("military_green", i) for i in range(16)], float)
        idx = np.clip(7 + (n - 0.5) * 4.0, 0, 15).astype(int)
        img[:] = base[idx]
        hi, lo = ramp("military_green", 12), ramp("military_green", 2)
        well_c, well_hi, well_lo = ramp("military_green", 1), ramp("military_green", 6), (0, 0, 0)
        ink, ink_sh = ramp("cream_yellow", 12), ramp("military_green", 2)
        # raised panels: one per section, bevelled
        sections = [(0, 0, 48, 32), (48, 0, 104, 32), (104, 0, 142, 32), (142, 0, 179, 32),
                    (179, 0, 236, 32), (236, 0, 249, 32), (249, 0, 320, 32)]
        for s in sections:
            _frame(img, s, hi, lo, inset=False)
        for (x0, y0, x1, y1) in sections:
            for rx, ry in ((x0 + 2, y0 + 2), (x1 - 4, y0 + 2), (x0 + 2, y1 - 4), (x1 - 4, y1 - 4)):
                if (x1 - x0) > 12:
                    _rivet(img, rx, ry, ramp("military_green", 14), ramp("military_green", 9),
                           ramp("military_green", 1))
    elif option == "B":
        streak = _noise(h, w, 4, rng, aspect=0.12)
        n = streak * 0.6 + rng.random((h, w)) * 0.4
        base = np.array([ramp("steel_blue", i) for i in range(16)], float)
        idx = np.clip(8 + (n - 0.5) * 5.0, 0, 15).astype(int)
        img = base[idx].astype(float)
        for _ in range(40):                       # scratches
            x, y = int(rng.integers(0, w - 6)), int(rng.integers(0, h))
            ln = int(rng.integers(2, 6))
            for k in range(ln):
                yy = y + (k // 2 if rng.random() < 0.5 else 0)
                if 0 <= yy < h:
                    img[yy, x + k] = ramp("steel_blue", 13)
        for _ in range(14):                       # worn dark spots
            x, y = int(rng.integers(0, w - 3)), int(rng.integers(0, h - 2))
            img[y:y + 2, x:x + 3] = ramp("steel_blue", 4)
        hi, lo = ramp("steel_blue", 14), ramp("steel_blue", 2)
        well_c, well_hi, well_lo = ramp("concrete_cold", 1), ramp("steel_blue", 12), (0, 0, 0)
        ink, ink_sh = ramp("steel_blue", 0), ramp("steel_blue", 15)    # engraved
        _frame(img, (0, 0, 320, 32), hi, lo, inset=False)
        for sx in (48, 104, 142, 179, 236, 249):
            img[1:31, sx - 1] = lo
            img[1:31, sx] = hi
        for (x0, x1) in ((0, 48), (48, 104), (179, 236), (249, 320)):
            for sx, sy in ((x0 + 2, 27), (x1 - 5, 27)):
                _screw(img, sx, sy, ramp("steel_blue", 15), ramp("steel_blue", 9), ramp("steel_blue", 3))
    else:  # C
        n = rng.random((h, w))
        base = np.array([ramp("flag_red", i) for i in range(16)], float)
        img = base[np.where(n < 0.12, 9, np.where(n > 0.93, 11, 10))].astype(float)
        black = ramp("concrete_cold", 0)
        # constructivist wedge: a black diagonal band behind the arms panel and
        # the key column, cream thin rule on its edge
        # constructivist wedge: one black diagonal band in the key column's foot
        yy, xx = np.mgrid[0:h, 0:w]
        band = (xx + yy * 0.6 >= 250) & (xx + yy * 0.6 < 256) & (xx < 250)
        img[band] = black
        hi, lo = ramp("flag_red", 14), ramp("flag_red", 4)
        well_c, well_hi, well_lo = black, ramp("cream_yellow", 13), ramp("cream_yellow", 13)
        ink, ink_sh = ramp("cream_yellow", 14), ramp("flag_red", 3)
        _frame(img, (0, 0, 320, 32), ramp("flag_red", 13), ramp("flag_red", 3), inset=False)

    # number wells
    for key, box in WELL.items():
        _rect(img, box, well_c)
        if option == "C":
            x0, y0, x1, y1 = box
            _frame(img, (x0 - 1, y0 - 1, x1 + 1, y1 + 1), well_hi, well_hi, inset=False)
        else:
            _frame(img, box, well_lo, well_hi, inset=True)
            img[box[1] + 1, box[0] + 1:box[2] - 1] = np.array(well_c) * 0.5   # inner shadow
    # face recess
    fx0, fy0, fx1, fy1 = FACE_BOX
    _rect(img, (fx0 + 1, 1, fx1 - 1, 31), well_c if option != "C" else ramp("flag_red", 3))
    _frame(img, (fx0 + 1, 1, fx1 - 1, 31), well_lo if option != "C" else black,
           well_hi if option != "C" else ramp("flag_red", 6), inset=True)
    # key slots
    for box in KEY_SLOTS:
        _rect(img, box, well_c)
        _frame(img, box, well_lo, well_hi, inset=True) if option != "C" else \
            _frame(img, box, well_hi, well_hi, inset=False)
    # ammo table
    _rect(img, TABLE_BOX, well_c)
    _frame(img, TABLE_BOX, well_lo, well_hi, inset=True) if option != "C" else \
        _frame(img, TABLE_BOX, well_hi, well_hi, inset=False)
    for y in TABLE_Y[1:]:
        img[y - BAR_Y - 1, TABLE_BOX[0] + 1:TABLE_BOX[2] - 1] = (
            ramp("military_green", 3) if option == "A" else ramp("steel_blue", 3) if option == "B"
            else ramp("flag_red", 5))
    _ammo_icons(img, 253, option)
    _table_slashes(img, ramp("cream_yellow", 11) if option != "B" else ramp("steel_blue", 12))
    # arms panel: six cells for the slot digits
    for (dx, dy) in ARMS_DIGITS.values():
        x, y = dx - 3, dy - BAR_Y - 2
        _rect(img, (x, y, x + 10, y + 10), well_c)
        if option == "C":
            _frame(img, (x, y, x + 10, y + 10), well_hi, well_hi, inset=False)
        else:
            _frame(img, (x, y, x + 10, y + 10), well_lo, well_hi, inset=True)
    if option == "C":   # gold stars at the two ends of the label row
        for cx in (5, 231):
            _star5(img, cx, 25, ramp("hazard_yellow", 13), ramp("hazard_yellow", 15), ramp("hazard_yellow", 7))
    # labels
    if lang == "bi":
        for key in ("ammo", "health", "arms", "armor"):
            put_text(img, LABELS["ru"][key], LABEL_CX[key], 21, ink)
            put_text(img, LABELS["en"][key], LABEL_CX[key], 26, ink)
    else:
        for key, word in LABELS[lang].items():
            put_text(img, word, LABEL_CX[key], LABEL_Y + 1, ink, shadow=ink_sh)
    return snap(img)


def render_arms(option: str, lang: str) -> np.ndarray:
    """STARMS = the arms section of the same bar (it is drawn over STBAR at
    x = 104 in single player, so the two must agree pixel for pixel)."""
    x0, _, x1, _ = ARMS_BOX
    return render_bar(option, lang)[:, x0:x1].copy()


# ======================================================================
# 2. THE NUMBERS
# ======================================================================
SS = 8   # supersampling of the vector digits

# seven segments in a 13x16 cell: a b c d e f g
_SEG = {
    "a": [(3.0, 1.0), (10.0, 1.0), (8.6, 3.8), (4.4, 3.8)],
    "b": [(10.6, 1.6), (11.8, 3.0), (11.8, 7.0), (10.6, 7.6), (9.0, 6.6), (9.0, 4.4)],
    "c": [(10.6, 8.4), (11.8, 9.0), (11.8, 13.0), (10.6, 14.4), (9.0, 11.6), (9.0, 9.4)],
    "d": [(4.4, 12.2), (8.6, 12.2), (10.0, 15.0), (3.0, 15.0)],
    "e": [(2.4, 8.4), (4.0, 9.4), (4.0, 11.6), (2.4, 14.4), (1.2, 13.0), (1.2, 9.0)],
    "f": [(2.4, 1.6), (4.0, 4.4), (4.0, 6.6), (2.4, 7.6), (1.2, 7.0), (1.2, 3.0)],
    "g": [(3.4, 8.0), (4.6, 6.6), (8.4, 6.6), (9.6, 8.0), (8.4, 9.4), (4.6, 9.4)],
}
_DIGIT_SEGS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd",
               "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g"}

# GOST 2.304 type B drafting digits: skeleton polylines in a 6x10 box,
# slanted 75 degrees (the standard's slant).
def _oval(cx, cy, rx, ry, n=20, a0=0.0, a1=360.0):
    return [(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
            for a in np.linspace(a0, a1, n)]


_GOST = {
    "0": [_oval(3, 5, 2.9, 4.9)],
    "1": [[(0.6, 2.8), (3.8, 0.0), (3.8, 10.0)]],
    "2": [[(0.3, 2.4)] + _oval(3, 2.6, 2.7, 2.5, 10, 190, 360)[1:] + [(5.4, 4.6), (0.0, 10.0), (6.0, 10.0)]],
    "3": [[(0.2, 1.4), (2.6, 0.0), (5.0, 0.6), (5.6, 2.4), (4.4, 4.3), (2.2, 4.8)],
          [(2.2, 4.8), (4.8, 5.4), (6.0, 7.6), (5.2, 9.4), (3.0, 10.0), (0.8, 9.5), (0.0, 8.4)]],
    "4": [[(4.8, 10.0), (4.8, 0.0), (0.0, 7.0), (6.3, 7.0)]],
    "5": [[(5.6, 0.0), (1.0, 0.0), (0.5, 4.6), (2.6, 3.8), (4.8, 4.2), (6.0, 6.4),
           (5.6, 8.8), (3.2, 10.0), (1.0, 9.5), (0.0, 8.2)]],
    "6": [[(5.4, 0.8), (3.2, 0.0), (1.2, 0.9), (0.2, 3.6), (0.0, 6.8), (0.6, 9.0), (3.0, 10.0),
           (5.2, 9.2), (6.0, 7.2), (5.2, 5.1), (3.0, 4.4), (1.0, 5.2), (0.1, 6.8)]],
    "7": [[(0.0, 0.0), (6.0, 0.0), (1.8, 10.0)]],
    "8": [_oval(3, 2.45, 2.4, 2.35), _oval(3, 7.35, 2.95, 2.6)],
    "-": [[(1.0, 5.4), (5.0, 5.4)]],
}
_GOST["9"] = [[(6 - x, 10 - y) for x, y in _GOST["6"][0]]]


def _shade_glyph(mask: np.ndarray, ramp_name: str, body=11, light=14, dark=5, edge=1) -> np.ndarray:
    """RGBA from a boolean glyph: body colour, light top-left, dark bottom-right,
    and a 1-px dark outline inside the cell."""
    h, w = mask.shape
    out = np.zeros((h, w, 4), np.uint8)
    pad = np.pad(mask, 1)
    up, left = pad[:-2, 1:-1], pad[1:-1, :-2]
    down, right = pad[2:, 1:-1], pad[1:-1, 2:]
    col = np.zeros((h, w, 3), np.uint8)
    col[:] = ramp(ramp_name, body)
    col[mask & (~up | ~left)] = ramp(ramp_name, light)
    col[mask & (~down | ~right)] = ramp(ramp_name, dark)
    out[mask, :3] = col[mask]
    out[mask, 3] = 255
    grown = mask.copy()
    grown[1:] |= mask[:-1]
    grown[:-1] |= mask[1:]
    grown[:, 1:] |= mask[:, :-1]
    grown[:, :-1] |= mask[:, 1:]
    ring = grown & ~mask
    out[ring, :3] = ramp(ramp_name, edge)
    out[ring, 3] = 255
    return out


def _poly_mask(polys, size, lines=None, width=0.0) -> np.ndarray:
    w, h = size
    im = Image.new("L", (w * SS, h * SS), 0)
    d = ImageDraw.Draw(im)
    for p in polys:
        d.polygon([(x * SS, y * SS) for x, y in p], fill=255)
    for line in (lines or []):
        pts = [(x * SS, y * SS) for x, y in line]
        d.line(pts, fill=255, width=int(width * SS))
        r = width * SS / 2
        for x, y in pts:
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    a = np.asarray(im, np.float64).reshape(h, SS, w, SS).mean((1, 3))
    return a >= 128


def big_digit(option: str, ch: str) -> np.ndarray:
    """STTNUMd / STTMINUS / STTPRCNT (13x16 RGBA) of option N2 or N3."""
    size = (13, 16)
    if ch == "%":
        if option == "N2":
            polys = [[(1.5, 1.5), (5.0, 1.5), (5.0, 5.5), (1.5, 5.5)],
                     [(8.0, 10.5), (11.5, 10.5), (11.5, 14.5), (8.0, 14.5)],
                     [(9.2, 1.0), (11.8, 1.0), (3.8, 15.0), (1.2, 15.0)]]
            m = _poly_mask(polys, size)
        else:
            sl = lambda pts: [(1.6 + x * 1.45 + (10 - y) * 0.27, 0.8 + y * 1.42) for x, y in pts]
            m = _poly_mask([], size, [sl(_oval(1.6, 1.8, 1.2, 1.6, 12)), sl(_oval(4.6, 8.2, 1.2, 1.6, 12)),
                                      sl([(5.4, 0.0), (0.6, 10.0)])], width=1.9)
        return _shade_glyph(m, "flag_red")
    if option == "N2":
        polys = [_SEG[s] for s in _DIGIT_SEGS[ch]]
        if ch == "1":
            polys = [[(x - 1.5, y) for x, y in _SEG[s]] for s in "bc"]
        m = _poly_mask(polys, size)
    else:
        sl = lambda pts: [(1.5 + x * 1.45 + (10 - y) * 0.27, 0.8 + y * 1.42) for x, y in pts]
        m = _poly_mask([], size, [sl(p) for p in _GOST[ch]], width=2.7)
    return _shade_glyph(m, "flag_red")


def small_digit(option: str, d: str, lit: bool) -> np.ndarray:
    """STYSNUMd (yellow, slot owned / ammo table) or STGNUMd (grey), 4x6 RGBA:
    a 3x5 glyph plus a 1-px shadow right and down."""
    g = glyph(d)
    out = np.zeros((6, 4, 4), np.uint8)
    name = "hazard_yellow" if lit else "concrete_cold"
    ink = ramp(name, 13 if lit else 18)
    sh = ramp(name, 2 if lit else 3)
    for (yy, xx) in zip(*np.nonzero(g)):
        out[yy + 1, xx + 1, :3] = sh
        out[yy + 1, xx + 1, 3] = 255
    for (yy, xx) in zip(*np.nonzero(g)):
        out[yy, xx, :3] = ink
        if option == "N3" and yy == 0:
            out[yy, xx, :3] = ramp(name, 15 if lit else 24)
        out[yy, xx, 3] = 255
    return out


def digit_set(option: str) -> dict[str, np.ndarray]:
    """Every number lump of one option (N1 -> the Freedoom lumps, read from
    the IWAD for the mocks, or {} without it)."""
    if option == "N1":
        fd = freedoom_lumps()
        return {k: v for k, v in fd.items() if k.startswith(("STTNUM", "STTMINUS", "STTPRCNT",
                                                             "STYSNUM", "STGNUM"))}
    out = {f"STTNUM{d}": big_digit(option, str(d)) for d in range(10)}
    out["STTMINUS"] = big_digit(option, "-")
    out["STTPRCNT"] = big_digit(option, "%")
    for d in range(10):
        out[f"STYSNUM{d}"] = small_digit(option, str(d), True)
        out[f"STGNUM{d}"] = small_digit(option, str(d), False)
    return out


# ======================================================================
# 3. THE FACE
# ======================================================================
FS = 8                          # supersampling of the face
FW, FH = 35, 32                 # face canvas = bar x 143..177, y 0..31
CX = 17.0                       # the face's vertical axis (between px 16 and 17)
TURN = math.radians(30)         # STFTL / STFTR yaw
LIGHT = np.array([-0.5, -0.65, 0.75]) / np.linalg.norm([-0.5, -0.65, 0.75])
SKIN = np.array([186, 122, 90], float)          # olive-tan albedo (snapped later)
STUBBLE = np.array([96, 70, 52], float)
HAIR = np.array([34, 26, 22], float)

_Xh = (np.arange(FW * FS) + 0.5) / FS
_Yh = (np.arange(FH * FS) + 0.5) / FS
GX, GY = np.meshgrid(_Xh, _Yh)


def _g(x, y, sx, sy=None):
    sy = sx if sy is None else sy
    return np.exp(-(((GX - x) / sx) ** 2 + ((GY - y) / sy) ** 2) / 2)


def _seg_dist(p, q):
    (x1, y1), (x2, y2) = p, q
    dx, dy = x2 - x1, y2 - y1
    t = np.clip(((GX - x1) * dx + (GY - y1) * dy) / max(dx * dx + dy * dy, 1e-9), 0, 1)
    return np.hypot(GX - (x1 + t * dx), GY - (y1 + t * dy))


def _streak(points, width):
    d = np.full(GX.shape, 1e9)
    for p, q in zip(points[:-1], points[1:]):
        d = np.minimum(d, _seg_dist(p, q))
    return d < width / 2


class Layer:
    def __init__(self, alpha, albedo, bump=None, vertical=(15.0, 14.0), depth=0.9):
        self.alpha = alpha
        self.albedo = albedo
        self.bump = np.zeros(alpha.shape) if bump is None else bump
        self.vertical = vertical
        self.depth = depth


def _extents(alpha):
    has = alpha.any(1)
    w = alpha.shape[1]
    xl = np.argmax(alpha, 1)
    xr = w - 1 - np.argmax(alpha[:, ::-1], 1)
    c = (xl + xr) / 2.0
    half = np.maximum((xr - xl) / 2.0 + 0.5, 0.5)
    return has, c, half


def _dome(layer: Layer) -> np.ndarray:
    has, c, half = _extents(layer.alpha)
    xs = np.arange(layer.alpha.shape[1])[None, :]
    u = np.clip((xs - c[:, None]) / half[:, None], -1, 1)
    z = np.sqrt(1 - u ** 2) * half[:, None] / FS * layer.depth
    cy, ry = layer.vertical
    z = z * np.sqrt(np.clip(1 - ((GY - cy) / ry) ** 2, 0.05, 1))
    return np.where(layer.alpha, z, 0)


def _warp(layer: Layer, phi: float) -> Layer:
    if phi == 0:
        return layer
    has, c, half = _extents(layer.alpha)
    xs = np.arange(layer.alpha.shape[1])[None, :].astype(float)
    u = np.clip((xs - c[:, None]) / half[:, None], -1, 1)
    th = np.clip(np.arcsin(u) - phi, -np.pi / 2, np.pi / 2)
    src = np.rint(c[:, None] + half[:, None] * np.sin(th) - 0.0).astype(int)
    src = np.clip(src, 0, layer.alpha.shape[1] - 1)
    rows = np.arange(layer.alpha.shape[0])[:, None]
    inside = layer.alpha
    albedo = np.where(inside[..., None], layer.albedo[rows, src], layer.albedo)
    bump = np.where(inside, layer.bump[rows, src], layer.bump)
    return Layer(layer.alpha, albedo, bump, layer.vertical, layer.depth)


def warp_x(layer_alpha, x: float, y: float, phi: float) -> float:
    """Where a straight-frame point (x, y) of a layer lands after the yaw."""
    if phi == 0:
        return x
    has, c, half = _extents(layer_alpha)
    r = int(min(max(y * FS, 0), layer_alpha.shape[0] - 1))
    cc, hh = c[r] / FS + 0.5 / FS, half[r] / FS
    u = max(-1.0, min(1.0, (x - cc) / hh))
    return cc + hh * math.sin(max(-math.pi / 2, min(math.pi / 2, math.asin(u) + phi)))


def _shade(layer: Layer) -> np.ndarray:
    z = _dome(layer) + layer.bump
    gy, gx = np.gradient(z, 1.0 / FS)
    gx, gy = np.clip(gx, -3, 3), np.clip(gy, -3, 3)
    n = np.stack([-gx, -gy, np.ones_like(z)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    lam = np.clip(n @ LIGHT, 0, 1)
    inten = 0.28 + 0.92 * lam
    col = layer.albedo * inten[..., None]
    warm = (1 - np.clip(inten, 0, 1))[..., None] * np.array([0.10, -0.02, -0.06]) * layer.albedo
    return np.clip(col + warm, 0, 255)


def _jaw_half(y):
    return 7.7 * np.sqrt(np.clip(1 - ((y - 19.0) / 7.7) ** 4, 0, 1))


def head_alpha(ears: bool):
    cran = ((GX - CX) / 8.6) ** 2 + ((GY - 13.4) / 11.8) ** 2 < 1
    jaw = (GY >= 17) & (GY <= 26.7) & (np.abs(GX - CX) < _jaw_half(GY))
    a = cran | jaw
    if ears:
        for ex in (8.4, 25.6):
            a |= ((GX - ex) / 1.5) ** 2 + ((GY - 15.8) / 2.5) ** 2 < 1
    return a


# ---- pain overlays, painted into the head's albedo (straight frame)
BLOOD = np.array([150, 18, 14], float)
BLOOD_DK = np.array([92, 10, 8], float)
BRUISE = np.array([96, 58, 62], float)


def _paint(albedo, mask, colour, strength=1.0):
    albedo[mask] = albedo[mask] * (1 - strength) + colour * strength


def pain_paint(albedo, level: int, dead: bool = False):
    if level >= 1:
        _paint(albedo, _g(11.6, 16.2, 1.3) > 0.45, BRUISE, 0.55)          # bruised cheekbone
        _paint(albedo, _streak([(21.6, 11.0), (23.4, 11.6)], 0.9), BLOOD)  # cut brow
    if level >= 2:
        _paint(albedo, _streak([(16.2, 18.3), (16.0, 20.2), (15.6, 21.8)], 0.9), BLOOD)  # nosebleed
        _paint(albedo, _streak([(19.5, 9.9), (20.4, 10.8), (20.6, 12.0)], 0.9), BLOOD)   # forehead cut
        _paint(albedo, _g(19.8, 21.8, 0.7) > 0.5, BLOOD_DK)                              # split lip
    if level >= 3:
        _paint(albedo, _streak([(23.0, 11.6), (23.2, 13.2), (23.4, 16.8)], 1.1), BLOOD)  # over the eye
        _paint(albedo, _g(11.8, 16.0, 1.9) > 0.4, BRUISE, 0.75)
        _paint(albedo, _streak([(14.8, 22.0), (14.6, 24.8)], 0.9), BLOOD)               # mouth corner
        _paint(albedo, _g(13.8, 12.6, 1.4) > 0.5, BRUISE, 0.6)                           # swelling
    if level >= 4:
        _paint(albedo, _streak([(18.0, 10.4), (22.4, 10.6)], 1.6), BLOOD)                # brow gash
        _paint(albedo, _streak([(18.4, 11.0), (18.8, 16.0), (19.6, 19.8)], 1.0), BLOOD)
        _paint(albedo, _streak([(11.0, 17.5), (11.4, 21.0), (12.6, 24.0)], 1.0), BLOOD_DK)
        _paint(albedo, _g(16.8, 25.0, 1.6) > 0.5, BLOOD)                                  # chin
        albedo[:] = albedo * 0.88 + albedo.mean(-1, keepdims=True) * 0.12                 # pale
    if dead:
        _paint(albedo, _streak([(13.0, 9.8), (14.0, 14.0), (13.6, 19.0)], 1.4), BLOOD)
        _paint(albedo, _streak([(20.6, 13.0), (21.0, 18.0), (20.0, 24.0)], 1.4), BLOOD_DK)
        _paint(albedo, _g(17.0, 22.6, 2.0) > 0.5, BLOOD_DK)
        albedo[:] = albedo * 0.8 + np.array([70, 76, 64]) * 0.2                           # grey-green


# ---- the head
def build_head(option: str, level: int, dead: bool) -> Layer:
    ears = option in ("B", "C")
    a = head_alpha(ears)
    alb = np.empty(a.shape + (3,))
    alb[:] = SKIN
    # stubble: jaw, chin, upper lip, lower cheeks
    face_off = np.abs(GX - CX)
    stub = a & (((GY > 18.9) & (face_off < 8)) | ((GY > 17.2) & (face_off > 4.6))) \
        & ~((np.abs(GY - 21.4) < 0.9) & (face_off < 2.8))
    alb[stub] = alb[stub] * 0.55 + STUBBLE * 0.45
    # lips
    lips = (np.abs(GY - 21.6) < 0.8) & (face_off < 2.6)
    alb[lips] = alb[lips] * 0.6 + np.array([150, 82, 70]) * 0.4
    if ears:
        for ex in (8.4, 25.6):
            ear = ((GX - ex) / 1.5) ** 2 + ((GY - 15.8) / 2.5) ** 2 < 1
            alb[ear & ~(((GX - CX) / 8.6) ** 2 + ((GY - 13.4) / 11.8) ** 2 < 1)] *= np.array([1.0, 0.86, 0.84])
    # hair: a short military cut, seen at the temples and as sideburns
    hairline = 8.6 + 1.2 * ((GX - CX) / 8.6) ** 2
    hair = a & (GY < hairline)
    side = a & (face_off > 6.9) & (GY < 14.2) & (GY > 7.5) & ears     # under the flaps: none
    alb[hair | side] = HAIR
    pain_paint(alb, level, dead)
    bump = (0.9 * _g(CX, 11.7, 4.5, 0.9)                                       # brow ridge
            - 1.3 * (_g(13.8, 13.7, 1.7, 1.1) + _g(20.2, 13.7, 1.7, 1.1))     # eye sockets
            + 1.6 * np.exp(-((GX - CX) / 0.9) ** 2 / 2) * np.clip((GY - 12.0) / 5.6, 0, 1)
            * (GY < 18.2)                                                       # nose ridge
            + 1.6 * _g(CX, 17.4, 1.15)                                          # nose tip
            + 0.6 * (_g(15.5, 17.9, 0.8) + _g(18.5, 17.9, 0.8))                 # nose wings
            + 0.9 * (_g(11.0, 15.6, 1.6) + _g(23.0, 15.6, 1.6))                 # cheekbones
            - 0.5 * (_g(13.6, 19.6, 0.8) + _g(20.4, 19.6, 0.8))                 # nasolabial
            + 0.4 * _g(CX, 20.4, 2.0, 0.6) + 0.6 * _g(CX, 22.1, 1.8, 0.6)       # lips
            - 0.5 * _g(CX, 21.3, 2.3, 0.35)
            - 0.4 * _g(CX, 23.2, 1.6, 0.5) + 1.0 * _g(CX, 24.6, 2.1, 1.2))      # chin
    if level >= 3 and not dead:
        bump += 0.8 * _g(13.8, 12.6, 1.3)                                       # swollen brow
    return Layer(a, alb, bump * a, vertical=(15.0, 14.5))


def build_body(option: str) -> Layer:
    neck = (np.abs(GX - CX) < 4.7) & (GY > 21.5)
    shoulders = (GY > 27.0) & (np.abs(GX - CX) < 6.2 + (GY - 27.0) * 1.2) & (GY < 31.0)
    vopen = np.abs(GX - CX) < np.clip(3.0 - (GY - 27.0) * 0.7, 0, 3)
    a = (neck & (GY < 31.0)) | shoulders
    alb = np.empty(a.shape + (3,))
    alb[:] = SKIN * 0.86
    alb[GY < 25.5] = SKIN * 0.5                                    # under the jaw
    cloth = np.array(ramp("khaki_olive", 8), float) if option != "B" else np.array(ramp("military_green", 8), float)
    m = shoulders & ~vopen
    alb[m] = cloth
    edge = shoulders & ~vopen & (np.abs(np.abs(GX - CX) - np.clip(3.0 - (GY - 27.0) * 0.7, 0, 3)) < 0.6)
    alb[edge] = cloth * 0.55
    if option == "C":                                              # telnyashka in the V
        stripes = vopen & shoulders & (np.floor(GY).astype(int) % 2 == 0)
        alb[stripes] = np.array(palette.ramp_colours("mosaic_cobalt")[8], float)
        alb[vopen & shoulders & ~stripes] = np.array([235, 232, 222], float)
    return Layer(a, alb, None, vertical=(26.0, 8.0), depth=0.6)


def build_hat(option: str, rng) -> Layer:
    if option == "A":                                   # ushanka, flaps down
        crown = ((GX - CX) / 10.2) ** 2 + ((GY - 8.0) / 5.8) ** 2 < 1
        crown &= GY < 8.0
        band = (np.abs(GX - CX) < 11.4 - np.clip(5.6 - GY, 0, 3) ** 2 * 0.5) & (GY >= 4.6) & (GY < 9.8)
        flaps = (np.abs(np.abs(GX - CX) - 9.8) < 2.0) & (GY >= 8.0) & (GY < 19.6 - (np.abs(GX - CX) - 9.8) * 0.6)
        a = crown | band | flaps
        fur = _fur_hi(rng)
        dark = np.array(ramp("plaster_warm", 3), float)
        light = np.array(ramp("plaster_warm", 11), float)
        alb = dark[None, None, :] + (light - dark)[None, None, :] * fur[..., None]
        cloth = crown & ~band                               # the crown is cloth, darker
        alb[cloth] = np.array(ramp("khaki_olive", 4), float) * (0.9 + 0.2 * fur[cloth, None])
        alb[flaps & ~band] *= 0.8
        alb[flaps & ~band & (GY > 18.2 - (np.abs(GX - CX) - 9.8) * 0.6)] *= 0.6   # flap hem
        seam = band & (np.abs(GY - 9.5) < 0.35)             # shadow line under the folded brim
        alb[seam] *= 0.45
        bump = 1.4 * np.sin(np.clip((GY - 4.6) / 5.2, 0, 1) * np.pi) * band \
            + 0.6 * (fur - 0.5) + 0.8 * np.clip((np.abs(GX - CX) - 8.6) / 2.0, 0, 1) * flaps
        return Layer(a, alb, bump * a, vertical=(12.0, 14.0), depth=0.7)
    if option == "B":                                   # SSh-68 steel helmet
        dome = ((GX - CX) / 10.6) ** 2 + ((GY - 10.0) / 7.8) ** 2 < 1
        dome &= GY < 10.0
        rim = (np.abs(GX - CX) < 11.6) & (GY >= 8.8) & (GY < 10.6)
        a = dome | rim
        g = _noise_hi(rng, 6.0)
        base = np.array(ramp("military_green", 9), float)
        alb = base[None, None, :] * (0.88 + 0.24 * g[..., None])
        chips = (_noise_hi(rng, 14.0) > 0.82) & dome
        alb[chips] = np.array(ramp("military_green", 4), float)
        alb[rim] *= 0.85
        bump = 0.5 * rim
        return Layer(a, alb, bump * a, vertical=(9.5, 9.5), depth=0.85)
    # C: VDV beret, pulled to the wearer's right (viewer's left)
    top = 2.3 + 0.06 * (GX - 13.0) ** 2 * (GX < 13.0) + 0.012 * (GX - 13.0) ** 2 * (GX >= 13.0)
    bottom = 8.9 - (GX - 7.0) * 0.12
    a = (GY > top) & (GY < bottom) & (GX > 5.2) & (GX < 27.4) & (GY < 10.4)
    a &= ~((GX > 25.0) & (GY < 5.0 + (GX - 25.0) * 0.8))
    base = np.array(palette.ramp_colours("mosaic_cobalt")[9], float)
    g = _noise_hi(rng, 5.0)
    alb = base[None, None, :] * (0.9 + 0.2 * g[..., None])
    band = a & (GY > bottom - 1.0)
    alb[band] = np.array(ramp("rust_brown", 2), float)              # leather band
    bump = 1.2 * np.clip((GY - top) / 3.0, 0, 1) * np.clip((bottom - GY) / 2.0, 0, 1) \
        + 0.8 * _g(9.0, 7.0, 2.5)
    return Layer(a, alb, bump * a, vertical=(6.0, 6.0), depth=0.6)


def _fur_hi(rng) -> np.ndarray:
    """Fur: vertical strands (long thin cells) over fine speckle, in [0,1]."""
    from artlib import value_noise
    h, w = GX.shape
    n = value_noise(w, h, FW * 2, max(2, FH // 3), rng) * 0.65 + rng.random((h, w)) * 0.35
    return np.clip((n - 0.5) * 1.6 + 0.5, 0, 1)


def _noise_hi(rng, cells: float) -> np.ndarray:
    from artlib import value_noise
    h, w = GX.shape
    n = value_noise(w, h, max(2, int(cells * FW / 10)), max(2, int(cells * FH / 10)), rng) * 0.6
    n += rng.random((h, w)) * 0.4
    return n


def _down(rgb, alpha):
    h, w = FH, FW
    a = alpha.astype(float)
    num = (rgb * a[..., None]).reshape(h, FS, w, FS, 3).sum((1, 3))
    cov = a.reshape(h, FS, w, FS).mean((1, 3))
    den = np.maximum(cov * FS * FS, 1e-9)
    return num / den[..., None], cov


# ---- the crisp parts: pixel stamps (key -> colour)
def _key_colours(god=False):
    return {
        "k": snap1((40, 22, 16)), "b": snap1((30, 22, 18)), "w": snap1((205, 196, 182)),
        "i": snap1((74, 44, 26)), "t": snap1((226, 218, 200)), "m": snap1((70, 14, 12)),
        "r": snap1(BLOOD), "y": snap1((250, 208, 40)), "u": snap1(BRUISE),
    }


EYES = {   # 4x2 (or 4x3); 'I' marks the 2 iris columns, placed by the gaze
    "open": ["kkkk", "wIIw"],
    "wide": ["kkkk", "wIIw", "wwww"],
    "narrow": ["....", "kIIk"],
    "closed": ["....", "kkkk"],
    "swollen": ["uuuu", "kkIu"],
    "shut": ["uuuu", "ukku"],
}
BROWS = {   # 5x2, viewer-left brow; the right one is mirrored
    "neutral": [".bbbb", "b...."],
    "furrow": ["bbb..", "..bbb"],
    "angry": ["bb...", "..bbb"],
    "raised": ["..bbb", "bb..."],
    "slack": [".....", "bbbbb"],
}
MOUTHS = {  # centred under the nose
    "neutral": [".kkkk.", "......"],
    "tight": ["kkkkkk", "......"],
    "grimace": [".kkkk.", "k....k"],
    "open": [".kkkkkk.", "kttttttk", "kmmmmmmk", ".kmmmmk."],
    "grin": ["k......k", "kttttttk", ".kkkkkk."],
    "clench": ["kkkkkkkk", "ktktktkk", "kkkkkkkk"],
    "smirk": ["......k.", ".kkkkk..", "......."],
    "slack": ["..kkkk..", ".kmmmmk.", "..kmmk.."],
}
EYE_Y, BROW_Y, NOSTRIL_Y, MOUTH_Y = 13, 11, 18, 20


def expression(kind: str, level: int):
    """(eyes, brows, mouth, swollen-left) for a frame kind and pain level."""
    brows = ["neutral", "neutral", "furrow", "furrow", "angry"][level]
    mouth = ["neutral", "neutral", "tight", "grimace", "grimace"][level]
    eye = "open"
    if kind == "ouch":
        return "wide", "raised", "open", level >= 3
    if kind == "evl":
        return "narrow", "angry", "grin", level >= 4
    if kind == "kill":
        return "narrow", "angry", "clench", level >= 4
    if kind == "god":
        return "open", "neutral", "smirk", False
    if kind == "dead":
        return "closed", "slack", "slack", False
    return eye, brows, mouth, level >= 3


def _put(canvas, mask, rows, x0, y0, cols, iris_cols=(1, 2), iris_key="i", mirror=False):
    for j, row in enumerate(rows):
        r = row[::-1] if mirror else row
        for i, ch in enumerate(r):
            if ch == ".":
                continue
            key = iris_key if ch == "I" else ch
            if ch == "I":
                continue
            x, y = x0 + i, y0 + j
            if 0 <= y < canvas.shape[0] and 0 <= x < canvas.shape[1] and mask[y, x]:
                canvas[y, x] = cols[key]
    # iris pixels (drawn after, so the gaze can move them)
    for j, row in enumerate(rows):
        if "I" in row:
            for i in iris_cols:
                x, y = x0 + i, y0 + j
                if 0 <= x < canvas.shape[1] and mask[y, x]:
                    canvas[y, x] = cols[iris_key]
            for i in range(len(row)):
                if row[i] == "I" and i not in iris_cols:
                    x, y = x0 + i, y0 + j
                    if mask[y, x]:
                        canvas[y, x] = cols["w"]


def render_face(option: str, level: int = 0, kind: str = "st", gaze: int = 0) -> np.ndarray:
    """One face on the 35x32 face canvas (RGBA uint8).
    kind: st, tl, tr, ouch, evl, kill, god, dead. gaze: -1, 0, 1 (straight frames).
    Pure function of its arguments (seeded), so it is cached."""
    return _render_face(option, level, kind, gaze).copy()


@functools.lru_cache(maxsize=None)
def _body_hat(option: str) -> tuple[Layer, Layer]:
    return build_body(option), build_hat(option, np.random.default_rng(7 + "ABC".index(option)))


@functools.lru_cache(maxsize=None)
def _layers(option: str, level: int, dead: bool) -> tuple[Layer, Layer, Layer]:
    """The three straight-frame layers of one face (cached: a turn or an
    expression only warps them and stamps on top; nothing mutates them)."""
    body, hat = _body_hat(option)
    head = build_head(option, level, dead)
    # contact shadow under the headgear on the forehead and the cheeks
    hat_low = np.where(hat.alpha, GY, 0).max(0)
    below = np.clip(GY - hat_low[None, :], 0, None)
    shadow = 1 - 0.5 * np.exp(-below / 1.1) * (hat_low[None, :] > 0) * (GY > hat_low[None, :])
    head.albedo *= shadow[..., None]
    if option == "A":   # the flaps shade the cheeks beside them
        head.albedo *= (1 - 0.35 * np.exp(-np.clip(8.9 - np.abs(GX - CX), 0, None) / 1.0)
                        * (np.abs(GX - CX) < 8.9))[..., None]
    return body, head, hat


@functools.lru_cache(maxsize=None)
def _render_face(option: str, level: int, kind: str, gaze: int) -> np.ndarray:
    dead = kind == "dead"
    phi = {"tl": -TURN, "tr": TURN}.get(kind, 0.0)
    body, head, hat = _layers(option, 4 if dead else level, dead)
    layers = [_warp(body, phi * 0.3), _warp(head, phi), _warp(hat, phi)]
    rgb = np.zeros(GX.shape + (3,))
    alpha = np.zeros(GX.shape, bool)
    for L in layers:
        rgb = np.where(L.alpha[..., None], _shade(L), rgb)
        alpha |= L.alpha
    if dead:
        rgb *= 0.86
    col, cov = _down(rgb, alpha)
    opaque = cov >= 0.5
    # which pixels are skin: the head (minus hair) or the bare neck, uncovered
    skinish = (layers[1].alpha & ~layers[2].alpha & (layers[1].albedo.sum(-1) > HAIR.sum() * 1.5)) |         (layers[0].alpha & ~layers[1].alpha & ~layers[2].alpha & (GY < 27.0))
    skin_cov = skinish.reshape(FH, FS, FW, FS).mean((1, 3)) >= 0.5
    out = np.zeros((FH, FW, 4), np.uint8)
    out[..., :3] = snap(col)
    out[skin_cov, :3] = snap(col[skin_cov][None], _SKIN_PAL)[0]
    out[..., 3] = np.where(opaque, 255, 0)
    out[~opaque, :3] = 0

    # stubble speckle (1x): a third of the stubble pixels one shade darker
    face_off = np.abs(_Xf - CX)
    srng = np.random.default_rng(31 + level)
    stub = (((_Yf > 19.4) & (face_off < 6.4)) | ((_Yf > 17.6) & (face_off > 4.8) & (face_off < 7.2))) \
        & (_Yf < 25.4) & opaque
    stub &= srng.random(stub.shape) < 0.33
    out[stub, :3] = snap(out[stub, :3].astype(float)[None] * 0.8, _SKIN_PAL)[0]

    # crisp features, placed where the yaw moved them
    cols = _key_colours()
    head_a = head.alpha
    mask = opaque & (out[..., 3] > 0)
    eyes, brows, mouth, swollen = expression(kind, 4 if dead else level)
    def wx(x, y):
        return warp_x(head_a, x, y, phi)
    look = {"tl": -1, "tr": 1}.get(kind, gaze)
    iris = {-1: (0, 1), 0: (1, 2), 1: (2, 3)}[look]
    for side, ex in ((-1, 14.0), (1, 20.0)):
        x0 = int(math.floor(wx(ex, EYE_Y + 1) - 2 + 0.5))
        kind_eye = eyes
        if side == -1 and swollen:
            kind_eye = "shut" if level >= 4 or kind == "evl" else "swollen"
        rows = EYES[kind_eye]
        _put(out[..., :3], mask, rows, x0, EYE_Y, cols, iris_cols=iris,
             iris_key="y" if kind == "god" else "i")
    for side, bx in ((-1, 13.0), (1, 21.0)):
        x0 = int(math.floor(wx(bx, BROW_Y) - 2.5 + 0.5))
        _put(out[..., :3], mask, BROWS[brows], x0, BROW_Y, cols, mirror=(side == 1))
    nose_x = int(math.floor(wx(CX + 1.0, 15.5)))
    for y in range(14, 18):                               # shadow side of the nose (light is upper left)
        if mask[y, nose_x]:
            out[y, nose_x, :3] = snap(out[y, nose_x, :3][None, None].astype(float) * 0.78, _SKIN_PAL)[0, 0]
    for nx in (15.5, 18.5):
        x = int(math.floor(wx(nx, NOSTRIL_Y)))
        out[NOSTRIL_Y, x, :3] = snap(out[NOSTRIL_Y, x, :3][None, None].astype(float) * 0.55)[0, 0]
    m = MOUTHS[mouth]
    x0 = int(math.floor(wx(CX, MOUTH_Y + 1) - len(m[0]) / 2 + 0.5))
    _put(out[..., :3], mask, m, x0, MOUTH_Y, cols)
    # headgear badge
    if option in ("A", "B"):
        by = 7 if option == "A" else 5
        bx = int(math.floor(warp_x(hat.alpha, CX, by, phi) + 0.5))
        red, red_hi, gold = snap1(ramp("flag_red", 12)), snap1(ramp("flag_red", 15)), snap1(ramp("hazard_yellow", 13))
        _star(out[..., :3], mask, bx, by, red, red_hi, gold if option == "A" else None)
    else:
        bx = int(math.floor(warp_x(hat.alpha, 21.0, 5.0, phi)))
        gold, red = snap1(ramp("hazard_yellow", 12)), snap1(ramp("flag_red", 12))
        for (dx, dy, c) in ((0, 0, gold), (2, 0, gold), (1, 0, red), (0, 1, gold), (2, 1, gold),
                            (1, 1, red), (1, 2, gold)):
            if mask[4 + dy, bx + dx]:
                out[4 + dy, bx + dx, :3] = c
    if option == "B":                                      # chin strap
        strap = snap1(ramp("rust_brown", 3))
        for side in (-1, 1):
            for y in range(11, 21):
                x = int(math.floor(wx(CX + side * (7.6 - (y - 11) * 0.06), y)))
                if mask[y, x]:
                    out[y, x, :3] = strap
    return out


def _star(img, mask, cx, cy, fill, hi, ring=None):
    pat = ["..#..", ".###.", "#####", ".#.#."]
    for j, row in enumerate(pat):
        for i, ch in enumerate(row):
            x, y = cx - 2 + i, cy - 2 + j
            if ch == "#" and mask[y, x]:
                img[y, x] = fill
    img[cy - 1, cx] = hi
    if ring is not None:
        img[cy, cx] = ring


_Xf, _Yf = np.meshgrid(np.arange(FW) + 0.5, np.arange(FH) + 0.5)

FRAME_KINDS = ("st0", "st1", "st2", "tr", "tl", "ouch", "evl", "kill")


def face_lump_spec(name: str) -> tuple[int, str, int]:
    """Lump name -> (pain level, kind, gaze)."""
    if name == "STFGOD0":
        return 0, "god", 0
    if name == "STFDEAD0":
        return 4, "dead", 0
    for prefix, kind in (("STFOUCH", "ouch"), ("STFEVL", "evl"), ("STFKILL", "kill")):
        if name.startswith(prefix):
            return int(name[len(prefix):]), kind, 0
    if name.startswith("STFST"):
        return int(name[5]), "st", int(name[6]) - 1
    if name.startswith("STFTL"):
        return int(name[5]), "tl", 0
    if name.startswith("STFTR"):
        return int(name[5]), "tr", 0
    raise KeyError(name)


def crop_face(canvas: np.ndarray, name: str) -> np.ndarray:
    """Cut a lump's box out of the 35x32 canvas: the canvas is the bar's face
    area (x 143), and DI_ITEM_OFFSETS draws a lump at 143 - left, 168 - top."""
    w, h, lo, to = FD_LUMPS[name]
    x0, y0 = -lo, -to
    return canvas[y0:y0 + h, x0:x0 + w].copy()


def face_lumps(option: str) -> dict[str, np.ndarray]:
    return {n: crop_face(render_face(option, *face_lump_spec(n)), n) for n in FACE_LUMPS}


# ======================================================================
# 4. FREEDOOM (read only, for N1 and the honest "today" mock)
# ======================================================================
_FD_CACHE: dict | None = None


def freedoom_lumps() -> dict[str, np.ndarray]:
    """{name: RGBA} of the Freedoom status-bar lumps, {} without the IWAD."""
    global _FD_CACHE
    if _FD_CACHE is not None:
        return _FD_CACHE
    if not IWAD.is_file():
        _FD_CACHE = {}
        return _FD_CACHE
    data = IWAD.read_bytes()
    n, off = struct.unpack_from("<4xii", data, 0)
    lumps = {}
    for i in range(n):
        pos, size, name = struct.unpack_from("<ii8s", data, off + 16 * i)
        lumps[name.rstrip(b"\0").decode("ascii", "replace")] = (pos, size)
    pp = lumps["PLAYPAL"][0]
    pal = np.frombuffer(data[pp:pp + 768], np.uint8).reshape(256, 3)
    out = {}
    for name in list(FD_LUMPS) + [f"STKEYS{i}" for i in range(9)]:
        if name not in lumps:
            continue
        p0 = lumps[name][0]
        w, h, lo, to = struct.unpack_from("<hhhh", data, p0)
        img = np.zeros((h, w, 4), np.uint8)
        for col in range(w):
            q = p0 + struct.unpack_from("<I", data, p0 + 8 + 4 * col)[0]
            while data[q] != 0xFF:
                top, length = data[q], data[q + 1]
                for j in range(length):
                    if top + j < h:
                        img[top + j, col, :3] = pal[data[q + 3 + j]]
                        img[top + j, col, 3] = 255
                q += length + 4
        out[name] = img
        out["__off_" + name] = (lo, to)
    _FD_CACHE = out
    return out


def freedoom_header(name: str):
    fd = freedoom_lumps()
    if name not in fd:
        return None
    h, w = fd[name].shape[:2]
    return (w, h) + tuple(fd["__off_" + name])


# ======================================================================
# 5. MOCKS
# ======================================================================
STATES = {
    # MAP01 start (src/zscript/sd/player.zs: TT-33 and SD_START_CLIP = 50).
    "start": {"ammo": 50, "health": 100, "armor": 0, "arms": {2}, "table": [(50, 200), (0, 50), (0, 50), (0, 300)],
              "keys": [], "face": (0, "st", 0)},
    # Mid MAP01, illustrative: PPSh and IZh found, hurt, blue pass held.
    "fight": {"ammo": 137, "health": 34, "armor": 47, "arms": {2, 3, 4}, "table": [(137, 200), (12, 50), (0, 50), (0, 300)],
              "keys": [0], "face": (3, "tr", 0)},
}


def backdrop() -> np.ndarray:
    """MAP01's 3D view (320x168) from the smoke screenshot, or flat grey."""
    if GAME_SHOT.is_file():
        im = Image.open(GAME_SHOT).convert("RGB")
        sc = im.height / 200
        bw = int(round(320 * sc))
        x0 = (im.width - bw) // 2
        view = im.crop((x0, 0, x0 + bw, int(round(168 * sc)))).resize((320, 168), Image.NEAREST)
        return np.asarray(view).copy()
    out = np.zeros((168, 320, 3), np.uint8)
    out[:] = (70, 72, 76)
    return out


def _blit(screen, rgba, x, y):
    h, w = rgba.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, screen.shape[1]), min(y + h, screen.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    if src.shape[-1] == 3:
        screen[y0:y1, x0:x1] = src
        return
    m = src[..., 3] > 0
    screen[y0:y1, x0:x1][m] = src[..., :3][m]


def _number(screen, digits, value, right, y, cell, prefix):
    s = str(value)
    x = right - cell * len(s)
    for ch in s:
        g = digits.get(f"{prefix}{ch}")
        if g is not None:
            _blit(screen, g, x, y)
        x += cell


def keys_images() -> dict[int, np.ndarray]:
    out = {}
    for i in range(9):
        p = KEYS_DIR / f"STKEYS{i}.png"
        if p.is_file():
            out[i] = np.asarray(Image.open(p).convert("RGBA"))
        elif f"STKEYS{i}" in freedoom_lumps():
            out[i] = freedoom_lumps()[f"STKEYS{i}"]
    return out


def mock(bar: np.ndarray, arms: np.ndarray, digits: dict, face_canvas: np.ndarray | None,
         state: str = "start", face_rgba=None, face_off=None) -> np.ndarray:
    """A 320x200 screen drawn the way DoomStatusBar.DrawMainBar draws it."""
    st = STATES[state]
    scr = np.zeros((200, 320, 3), np.uint8)
    scr[:168] = backdrop()
    _blit(scr, bar, 0, BAR_Y)
    for (x, y) in POS_PERCENT:
        if "STTPRCNT" in digits:
            _blit(scr, digits["STTPRCNT"], x, y)
    _number(scr, digits, st["ammo"], POS_AMMO, POS_BIG_Y, BIG_CELL, "STTNUM")
    _number(scr, digits, st["health"], POS_HEALTH, POS_BIG_Y, BIG_CELL, "STTNUM")
    _number(scr, digits, st["armor"], POS_ARMOR, POS_BIG_Y, BIG_CELL, "STTNUM")
    _blit(scr, arms, *POS_ARMS)
    for slot, (x, y) in ARMS_DIGITS.items():
        g = digits.get(("STYSNUM" if slot in st["arms"] else "STGNUM") + str(slot))
        if g is not None:
            _blit(scr, g, x, y)
    if face_canvas is not None:
        _blit(scr, face_canvas, *POS_FACE)
    elif face_rgba is not None:
        _blit(scr, face_rgba, POS_FACE[0] - face_off[0], POS_FACE[1] - face_off[1])
    keys = keys_images()
    for k in st["keys"]:
        if k in keys:
            _blit(scr, keys[k], *POS_KEYS[k % 3])
    for (amt, mx), y in zip(st["table"], TABLE_Y):
        _number(scr, digits, amt, TABLE_X[0], y, SMALL_CELL, "STYSNUM")
        _number(scr, digits, mx, TABLE_X[1], y, SMALL_CELL, "STYSNUM")
    return scr


def face_for_state(option: str, state: str) -> np.ndarray:
    lvl, kind, gaze = STATES[state]["face"]
    return render_face(option, lvl, kind, gaze)


# ======================================================================
# 6. BUILD
# ======================================================================
def build(out_dir: Path = OUT_DIR) -> dict:
    """Write every proposal lump under out_dir; return a manifest."""
    out_dir = Path(out_dir)
    man: dict = {"script": SCRIPT_REL, "palette_version": PALETTE_VERSION, "files": {}}

    def rec(path: Path, name: str):
        man["files"][str(path.relative_to(out_dir)).replace("\\", "/")] = name

    for opt in BAR_OPTIONS:
        for lang in ("en", "ru") + (("bi",) if opt == "B" else ()):
            bar = render_bar(opt, lang)
            rec(save_opaque(bar, out_dir / "bar" / opt / lang / "STBAR.png"), "STBAR")
            rec(save_opaque(bar[:, ARMS_BOX[0]:ARMS_BOX[2]].copy(), out_dir / "bar" / opt / lang / "STARMS.png"),
                "STARMS")
    for opt in ("N2", "N3"):
        for name, rgba in digit_set(opt).items():
            rec(save_rgba(rgba, out_dir / "digits" / opt / f"{name}.png", grab_of(name)), name)
    for opt in FACE_OPTIONS:
        for name in ("STFST01",):
            rgba = crop_face(render_face(opt, *face_lump_spec(name)), name)
            rec(save_rgba(rgba, out_dir / "face" / opt / f"{name}.png", grab_of(name)), name)
    rec_opt = RECOMMENDED["face"]
    for name, rgba in face_lumps(rec_opt).items():
        rec(save_rgba(rgba, out_dir / "face" / rec_opt / "full" / f"{name}.png", grab_of(name)), name)
    (out_dir / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False), encoding="utf-8")
    return man


# ======================================================================
# 7. PREVIEW
# ======================================================================
def _png_uri(arr: np.ndarray) -> str:
    mode = "RGBA" if arr.shape[-1] == 4 else "RGB"
    buf = io.BytesIO()
    Image.fromarray(arr, mode).save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _img(arr, zoom, title="", bg="#000"):
    h, w = arr.shape[:2]
    return (f'<img class="px" style="background:{bg}" src="{_png_uri(arr)}" width="{w * zoom}" '
            f'height="{h * zoom}" alt="{html.escape(title)}" title="{html.escape(title)}">')


def _v(label, arr, zoom, bg="#000"):
    return f'<div class="v"><b>{html.escape(label)}</b>{_img(arr, zoom, label, bg)}</div>'


def _upscale(arr, z):
    return np.repeat(np.repeat(arr, z, 0), z, 1)


def _canvas_on(face_canvas, bg=(40, 40, 44)):
    out = np.zeros(face_canvas.shape[:2] + (3,), np.uint8)
    out[:] = bg
    m = face_canvas[..., 3] > 0
    out[m] = face_canvas[..., :3][m]
    return out


def gemini_prompt() -> str:
    return (
        "Pixel-art sprite sheet, a 5 x 8 grid of portraits of the same man on a flat pure magenta "
        "background (#FF00FF), no gaps, no text, no borders. Each cell is a head-and-shoulders portrait "
        "in the style of the 1993 DOOM status-bar face: front-lit, painted, 24 x 29 pixel look, chunky "
        "pixels, limited palette. The man: a Soviet Spetsnaz sergeant in 1977, Spanish (Catalan) by birth, "
        "about 46 years old, olive-tan skin, short black hair, thick dark eyebrows, dark brown eyes, a "
        "straight strong nose, square jaw, dark three-day stubble, no moustache. He wears a grey fur "
        "ushanka with the ear flaps DOWN and a small red star cockade on the front, and a khaki "
        "gymnastyorka collar. Rows = health from top to bottom: 1 unhurt, 2 a bruise on the cheekbone and "
        "a cut eyebrow, 3 bleeding nose and forehead cut, 4 one eye swollen, blood running over the face, "
        "5 face covered in blood, near collapse. Columns, the same in every row: 1 looking straight, eyes "
        "left; 2 looking straight, eyes centre; 3 looking straight, eyes right; 4 head turned 20 degrees to "
        "the viewer's right; 5 head turned 20 degrees to the viewer's left; 6 shocked, eyes wide, mouth "
        "open in a shout; 7 evil grin showing teeth, eyes narrowed; 8 furious, teeth clenched, brows down. "
        "Same head size and position in every cell, head fills the cell, hard pixel edges, no "
        "anti-aliasing against the magenta. Second image, same style and man: two cells, A golden glowing "
        "eyes with a faint smirk (invulnerable), B dead: eyes closed, head slumped, face bloodied.")


def sheet(stamp: str, out_dir: Path = OUT_DIR, preview_dir: Path = PREVIEW_DIR) -> tuple[Path, Path]:
    digits = {o: digit_set(o) for o in DIGIT_OPTIONS}
    rd = RECOMMENDED["digits"]
    face_rec = {s: face_for_state(RECOMMENDED["face"], s) for s in STATES}
    fd = freedoom_lumps()
    bars = {(o, l): render_bar(o, l) for o in BAR_OPTIONS for l in ("en", "ru")}
    bars[("B", "bi")] = render_bar("B", "bi")
    mocks = {}
    secs = []

    # --- today
    today = ""
    if fd:
        fdbar = fd["STBAR"][..., :3].copy()
        fdarms = fd["STARMS"][..., :3].copy()
        lo, to = fd["__off_STFST01"]
        scr = mock(fdbar, fdarms, digits["N1"], None, "start", fd["STFST01"], (lo, to))
        today = _v("Freedoom today, MAP01 start, 3x", scr, 3)
    secs.append(("0. Today", "What the player sees now: Freedoom's bar, numbers and face. The 3D view "
                 "is MAP01 from the 2026-10-13 smoke screenshot; every mock below is drawn with the same "
                 "positions as GZDoom's <code>DoomStatusBar.DrawMainBar</code> (g4.14.2).",
                 f'<div class="row">{today}</div>'))

    # --- bars
    desc = {
        "A": ("Olive-drab instrument panel",
              "4BO green plate (the doors' and crates' green), one raised riveted panel per section, "
              "recessed black-green wells, labels stencilled in cream like the crate numbers. Reads as "
              "military hardware; quiet enough that the red numbers and the face lead."),
        "B": ("Worn steel dashboard",
              "Brushed steel_blue plate with scratches and wear, slotted screws, engraved labels. "
              "Variant BI puts Russian over English on ONE picture, so it needs no localisation code "
              "(at the price of 5-px words stacked with no gap)."),
        "C": ("Propaganda band",
              "Flag-red ground, black wells framed in cream, a black constructivist wedge behind the arms "
              "panel and the keys. The loudest: red is the world's 'meaning' colour (ART-BIBLE 4), so a "
              "red bar competes with the red digits and with the posters."),
    }
    cards = []
    for o in BAR_OPTIONS:
        title, d = desc[o]
        arms_en = bars[(o, "en")][:, ARMS_BOX[0]:ARMS_BOX[2]]
        s1 = mock(bars[(o, "en")], arms_en, digits[rd], face_rec["start"], "start")
        s2 = mock(bars[(o, "en")], arms_en, digits[rd], face_rec["fight"], "fight")
        mocks[o] = s1
        ru = bars[(o, "ru")]
        s_ru = mock(ru, ru[:, ARMS_BOX[0]:ARMS_BOX[2]], digits[rd], face_rec["start"], "start")
        extra = ""
        if o == "B":
            bi = bars[("B", "bi")]
            extra = _v("BI: one bilingual picture, 3x", bi, 3)
        rec = ' rec' if o == RECOMMENDED["bar"] else ''
        tag = '<span class="tag">recommended</span>' if rec else ''
        cards.append(
            f'<div class="card{rec}">{tag}<h3>Bar {o}: {html.escape(title)}</h3><p class="desc">{d}</p>'
            f'<div class="row">{_v("MAP01 start, 1x", s1, 1)}{_v("MAP01 start, 3x", s1, 3)}</div>'
            f'<div class="row">{_v("mid-fight (illustrative numbers), 3x", s2, 3)}</div>'
            f'<div class="row">{_v("Russian labels, MAP01 start, 3x", s_ru, 3)}</div>'
            f'<div class="row">{_v("STBAR EN, 3x", bars[(o, "en")], 3)}</div>'
            f'<div class="row">{_v("STBAR RU, 3x", ru, 3)}</div>'
            f'<div class="row">{extra}</div></div>')
    secs.append(("1. The status bar (STBAR 320x32 + STARMS 38x32)",
                 "Three options, each in English and Russian. Numbers: the recommended N2; face: the "
                 "recommended A. Start numbers are the real MAP01 spawn (TT-33, 50 rounds of SD_START_CLIP, "
                 "100 %, 0 % armour, slot 2 lit; maxima 200/50/50/300 as in the smoke screenshot). The "
                 "mid-fight state is illustrative: 34 % health (pain level 3, face turned right), 47 % armour, "
                 "PPSh and IZh found, the blue pass held (the key icon is whatever is installed in "
                 "assets/graphics/hud/, read only).",
                 '<div class="grid">' + "".join(cards) + "</div>"))

    # --- faces
    fcards = []
    fdesc = {
        "A": ("Ushanka, flaps down",
              "Grey fur ushanka with the red-star cockade; the flaps frame the face and hide the ears, "
              "which is what makes the silhouette read as 'Soviet soldier' at 24 px. MAP01 is the Urals in "
              "November 1977 (LORE): it is the season's hat."),
        "B": ("Steel helmet SSh-68",
              "Green steel helmet with a painted star and a chin strap. Most military, but the rim "
              "shades the brows and eyes, which are what the face's expressions live on."),
        "C": ("VDV beret and telnyashka",
              "Sky-blue airborne beret pulled to the wearer's right, badge on the front, the striped "
              "telnyashka in the collar: the 1970s Spetsnaz look (GRU units wore VDV kit). Shows the most "
              "of the face; the blue is palette v2 mosaic_cobalt."),
    }
    for o in FACE_OPTIONS:
        t, d = fdesc[o]
        c = render_face(o, 0, "st", 0)
        lump = crop_face(c, "STFST01")
        hurt = crop_face(render_face(o, 3, "st", 0), "STFST31")
        bar = bars[(RECOMMENDED["bar"], "en")]
        scr = mock(bar, bar[:, ARMS_BOX[0]:ARMS_BOX[2]], digits[rd], c, "start")
        crop = scr[160:200, 96:224]
        rec = ' rec' if o == RECOMMENDED["face"] else ''
        tag = '<span class="tag">recommended</span>' if rec else ''
        fcards.append(
            f'<div class="card{rec}">{tag}<h3>Face {o}: {html.escape(t)}</h3><p class="desc">{d}</p>'
            f'<div class="row">{_v("STFST01 1x", lump, 1, "#333")}{_v("4x", lump, 4, "#333")}'
            f'{_v("8x", lump, 8, "#333")}{_v("pain 3, 4x", hurt, 4, "#333")}</div>'
            f'<div class="row">{_v("in bar A, 3x", crop, 3)}</div></div>')
    if fd:
        fdcmp = _v("Freedoom STFST01, 8x (for scale)", fd["STFST01"], 8, "#333")
    else:
        fdcmp = ""
    secs.append(("2. The face: three headgear options (straight, STFST01)",
                 "Sergeant Ramon Vilanova (D14): Barcelona-born, olive-tan skin, thick dark brows, dark "
                 "eyes, strong nose, square stubbled jaw. Each drawn at exactly the Freedoom lump's size "
                 "and offsets.", '<div class="grid">' + "".join(fcards) + f'</div><div class="row">{fdcmp}</div>'))

    # --- ladder
    fo = RECOMMENDED["face"]
    lumps = face_lumps(fo)
    rows_html = ['<table class="ladder"><tr><th>pain</th>' + "".join(
        f"<th>{k}</th>" for k in ("ST x0", "ST x1", "ST x2", "TR", "TL", "OUCH", "EVL", "KILL")) + "</tr>"]
    for p in range(5):
        names = [f"STFST{p}0", f"STFST{p}1", f"STFST{p}2", f"STFTR{p}0", f"STFTL{p}0",
                 f"STFOUCH{p}", f"STFEVL{p}", f"STFKILL{p}"]
        cells = "".join(f'<td>{_img(lumps[n], 4, n, "#333")}<br><code>{n}</code></td>' for n in names)
        rows_html.append(f"<tr><th>{p}<br>{['100-80', '79-60', '59-40', '39-20', '19-0'][p]} %</th>{cells}</tr>")
    rows_html.append("</table>")
    special = (f'<div class="row">{_v("STFGOD0, 4x", lumps["STFGOD0"], 4, "#333")}'
               f'{_v("STFDEAD0, 4x", lumps["STFDEAD0"], 4, "#333")}</div>')
    ladder_lead = ("All 42 lumps of the recommended face, each cut to its Freedoom box (sizes and grAb offsets "
                   "identical). The turn frames rotate every layer round its own axis, so the silhouette never "
                   "leaves the box. Pain rows follow Doom's formula: level = (100 - health) x 5 / 101.")
    secs.append((f"3. The full ladder of face {fo}, 4x", ladder_lead, "".join(rows_html) + special))

    # --- digits
    dcards = []
    ddesc = {
        "N1": ("Keep Freedoom's", "No lumps, no risk. Freedoom's red digits are rounded and generic; "
               "nothing in them says USSR."),
        "N2": ("Stencil segments", "Chamfered segments with stencil bridges, flag red with a light top-left "
               "edge, like the crate stencils (batch 3) and an instrument readout. Same 13x16 cell."),
        "N3": ("GOST 2.304 drafting", "Slanted Soviet engineering-drawing digits (the lettering of every "
               "Soviet blueprint and nameplate). The most specific, the least Doom-like at 1x."),
    }
    for o in DIGIT_OPTIONS:
        t, d = ddesc[o]
        ds = digits[o]
        if not ds:
            continue
        row_big = np.zeros((16, 13 * 12 + 11, 4), np.uint8)
        for i, n in enumerate([f"STTNUM{k}" for k in range(10)] + ["STTMINUS", "STTPRCNT"]):
            _blit_rgba(row_big, ds[n], i * 14, 0)
        row_small = np.zeros((6, 5 * 20, 4), np.uint8)
        for i in range(10):
            _blit_rgba(row_small, ds[f"STYSNUM{i}"], i * 5, 0)
            _blit_rgba(row_small, ds[f"STGNUM{i}"], 50 + i * 5, 0)
        bar = bars[(RECOMMENDED["bar"], "en")]
        scr = mock(bar, bar[:, ARMS_BOX[0]:ARMS_BOX[2]], ds, face_rec["fight"], "fight")
        rec = ' rec' if o == RECOMMENDED["digits"] else ''
        tag = '<span class="tag">recommended</span>' if rec else ''
        dcards.append(
            f'<div class="card{rec}">{tag}<h3>{o}: {html.escape(t)}</h3><p class="desc">{d}</p>'
            f'<div class="row">{_v("STTNUM0-9, STTMINUS, STTPRCNT, 4x", row_big, 4, "#222")}</div>'
            f'<div class="row">{_v("STYSNUM0-9 and STGNUM0-9, 4x", row_small, 4, "#222")}</div>'
            f'<div class="row">{_v("in bar A, mid-fight, 3x", scr[160:200], 3)}</div></div>')
    secs.append(("4. The numbers", "Big numbers 13x16 (the font HUDFONT_DOOM is built from these lumps), "
                 "small 4x6 yellow (owned slot, ammo table) and grey (empty slot).",
                 '<div class="grid">' + "".join(dcards) + "</div>"))

    # --- notes
    notes = f"""
<div class="ask"><b>The honest assessment of the face.</b> The method (shaded height field 8x supersampled,
crisp eyes/brows/mouth stamped at 1x) reaches a readable, consistent face that turns, bleeds and
grins in all 42 frames from one definition, and it reproduces byte for byte. It does NOT reach the
painted likeness of Doom's or Freedoom's face (those are digitised from a sculpt and hand-retouched):
ours reads as a soldier in a hat with a stubbled face, not yet as a specific man. If the CEO wants a
portrait with character, Plan B is the D79 route: the CEO generates a face sheet in Gemini on magenta,
and the frames are cut, scaled to these exact boxes and palette-snapped (the same pipeline as
<code>tools/art/gemini_frames.py</code>). The prompt, ready to paste:
<pre style="white-space:pre-wrap;font-size:12px">{html.escape(gemini_prompt())}</pre></div>
<div class="ask"><b>Install notes (mod-engineer, after approval).</b><ol>
<li>English: <code>graphics/STBAR.png</code>, <code>STARMS.png</code>, the 42 <code>STF*</code>,
<code>STTNUM0-9</code>, <code>STTMINUS</code>, <code>STTPRCNT</code>, <code>STYSNUM0-9</code>, <code>STGNUM0-9</code>
replace Freedoom's by name. Faces and STTMINUS carry grAb offsets equal to Freedoom's.</li>
<li>Russian: the localized-texture swap is commented out in g4.14.2 (ADR 010), so
<code>localized/textures/STBAR.ru.png</code> alone would never be drawn. Route: <code>SD_StatusBar</code>
overrides <code>DrawMainBar</code> (or only the two <code>DrawImage</code> calls of STBAR/STARMS) to take the
picture names from LANGUAGE ids, as <code>DrawPaused</code> already does for the pause sign. That copies
engine code (debt like T14). Bar B-BI avoids it entirely.</li>
<li>Palette v2 (mosaic_cobalt for face C, flesh_pink/rust in the skin): <code>check_pk3.py</code>'s
PALETTE_V2_LUMPS and <code>tests/test_palette_v2.py</code>'s APPROVED_IN_V2 must list them.</li>
<li>LICENSES.md: one row (our generator, seed list in this module), no foreign pixels. Engine pass pending (D26).</li>
</ol></div>"""
    secs.append(("5. Assessment, Plan B and install", "", notes))

    preview_dir = Path(preview_dir)
    path = preview_dir / f"{stamp}_M4_hud-face-sweep.html"
    css = sheetlib.CSS + (".ladder td,.ladder th{border:1px solid var(--line);padding:4px;text-align:center;"
                          "font-size:11px}.ladder code{font-size:10px;color:var(--mute)}code{font-family:Menlo,monospace}")
    body = "\n".join(f'<section><h2>{html.escape(h)}</h2>' + (f'<p class="lead">{lead}</p>' if lead else "")
                     + inner + "</section>" for h, lead, inner in secs)
    doc = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Soviet Doom - HUD and face sweep '
           f'(M2e)</title><style>{css}</style></head><body><header><h1>Status bar and face sweep (backlog M2e)</h1>'
           f'<div class="meta">art-director &middot; {html.escape(stamp)} &middot; generated by {SCRIPT_REL} &middot; '
           f'palette v{PALETTE_VERSION} &middot; nothing installed</div><p class="intro">Recommendation: bar '
           f'<b>{RECOMMENDED["bar"]}</b>, face <b>{RECOMMENDED["face"]}</b>, numbers <b>{RECOMMENDED["digits"]}</b>. '
           f'The CEO picks one per section (and a language route for the labels).</p></header>{body}'
           f'<footer>Proposals only; output in work/art/hud/. Sizes and offsets equal the Freedoom 0.13.0 lumps '
           f'(tests/test_gen_hud.py).</footer></body></html>')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")

    # --- the PNG companion: three bar mocks, the three faces, the ladder
    tiles = []
    for o in BAR_OPTIONS:
        tiles.append(_upscale(mocks[o], 2))
    strip = np.concatenate(tiles, 1)
    faces = [_upscale(_canvas_on(render_face(o, 0, "st", 0)), 8) for o in FACE_OPTIONS]
    gap = np.full((faces[0].shape[0], 16, 3), 40, np.uint8)
    frow = np.concatenate(sum([[f, gap] for f in faces], [])[:-1], 1)
    lad_rows = []
    for p in range(5):
        names = [f"STFST{p}0", f"STFST{p}1", f"STFST{p}2", f"STFTR{p}0", f"STFTL{p}0",
                 f"STFOUCH{p}", f"STFEVL{p}", f"STFKILL{p}"]
        cells = [_upscale(_canvas_on(render_face(fo, *face_lump_spec(n))), 4) for n in names]
        lad_rows.append(np.concatenate(cells, 1))
    lad_rows.append(np.concatenate([_upscale(_canvas_on(render_face(fo, *face_lump_spec(n))), 4)
                                    for n in ("STFGOD0", "STFDEAD0")] +
                                   [np.full((FH * 4, FW * 4 * 6, 3), 40, np.uint8)], 1))
    ladder = np.concatenate(lad_rows, 0)
    right = np.full((max(frow.shape[0], 0) + 16 + ladder.shape[0], max(frow.shape[1], ladder.shape[1]), 3), 40,
                    np.uint8)
    right[:frow.shape[0], :frow.shape[1]] = frow
    right[frow.shape[0] + 16:, :ladder.shape[1]] = ladder
    W = max(strip.shape[1], right.shape[1])
    png = np.full((strip.shape[0] + 16 + right.shape[0], W, 3), 40, np.uint8)
    png[:strip.shape[0], :strip.shape[1]] = strip
    png[strip.shape[0] + 16:, :right.shape[1]] = right
    png_path = path.with_suffix(".png")
    Image.fromarray(png, "RGB").save(png_path, optimize=True)
    return path, png_path


def _blit_rgba(dst, src, x, y):
    h, w = src.shape[:2]
    m = src[..., 3] > 0
    dst[y:y + h, x:x + w][m] = src[m]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stamp", help="YYYY-MM-DD_HHMM: also write the preview sheet")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args(argv)
    man = build(args.out)
    print(f"wrote {len(man['files'])} lumps under {args.out}")
    if args.stamp:
        h, p = sheet(args.stamp, args.out)
        print(f"wrote {h}\nwrote {p}")


if __name__ == "__main__":
    main()
