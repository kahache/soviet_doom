"""Batch 3 — props: crates and lockers (level-designer request A5, MAP01 v2).

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_props.py              (Windows)
    .venv/bin/python tools/art/gen_props.py                      (macOS)
    ... gen_props.py --publish     also copies the two sheets to docs/

Asked for in `docs/levels/MAP01-zarya-7.md` §10 (A5) and §15: "the dorm, the
guard post and the hangar bays want a crate face; today they are SDSTEL1
boxes", and v2 adds parapets and detail. This script produces a SWEEP, the
unit of visual review (docs/PIPELINE.md stage 2): rows are pieces, columns
are variants, every cell labelled so the CEO points at one ("R2-C").
Nothing is written to assets/.

The four pieces, sized from the map, not from taste:

  R1  SDCRAT1   crate face       64x64   wall   one 64-grid cell, one tile on a
                                                64-high crate sector (the map is
                                                floor-pegged, §6), stacks in 64s;
                                                also the END of the long case
  R2  SDCRAT2   long case face   128x64  wall   two cells: the parapet / low-cover
                                                unit of the hangar bays
  R3  SDCRTOP1  crate top        64x64   flat   the floor of every crate sector:
                                                what the catwalk (floor 96) sees
  R4  SDLOCK1   barracks locker  64x128  wall   one cell wide, floor to ceiling in
                                                the 128-high dorm; tiles into a row

The four columns sweep VALUE, because value is what survives Doom's sector
light and hue is not (ART-BIBLE §5; the switch batch measured it, LICENSES.md
batch 2). Material follows value, so a column is one coherent family:

  A  dark   4BO-green painted planks           body luma ~70
  B  mid    green pressed-steel case            body luma ~96  (= SDSTEL1: the trap)
  C  light  khaki planks, braced                body luma ~125
  D  pale   bare pine, black steel straps       body luma ~175

Hosts measured on the approved files: SDCONC1 146.6, SDSTEL1 101.2,
SDFLR2 139.5, SDFLR3 132.3.

NO FONTS. Every mark on these textures (crate numbers, "this side up"
arrows, locker plates) is drawn as hard pixels from segment data in this
file, the way gen_font.py draws glyphs from strokes. Impact rasterises
differently on Windows and on the Mac (CLAUDE.md, measured 2026-10-13), so
any lump rendered with it can only ever be regenerated on the machine that
made it; a lump that uses no font is byte-identical on both. Nothing here
calls ImageFont or Overlay.text, and tests/test_gen_props.py keeps it so.

All sizes in texture pixels (= Doom map units on a wall).
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import (  # noqa: E402
    blend, fbm, grain, load_palette, quantize, ramp_colour, save_indexed,
    shade, to_rgb,
)
import sheetlib  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "work" / "art" / "batch3" / "props"
SHEET_DIR = PROJECT_ROOT / "work" / "art" / "batch3"
MANIFEST = OUT_DIR / "manifest.json"
PUBLISH_EN = PROJECT_ROOT / "docs" / "art" / "previews"
PUBLISH_RU = PROJECT_ROOT / "docs" / "ru" / "art" / "previews"
SHEET_SLUG = "F3_batch3-props-sweep"
SCRIPT_REL = "tools/art/gen_props.py"

# Own seed space: batch 1 is 1977+, the switches 2077+. Seed of a cell =
# BATCH_SEED + 10 * row number + variant number (R2-C = 3077 + 20 + 3).
BATCH_SEED = 3077
GRID = 64               # the level designer's grid (MAP01 §3)

ASSET_DIR = PROJECT_ROOT / "assets"
HOST_FILES = {
    "SDCONC1": ASSET_DIR / "textures" / "soviet_base" / "SDCONC1.png",
    "SDSTEL1": ASSET_DIR / "textures" / "soviet_base" / "SDSTEL1.png",
    "SDFLR2": ASSET_DIR / "flats" / "soviet_base" / "SDFLR2.png",
    "SDFLR3": ASSET_DIR / "flats" / "soviet_base" / "SDFLR3.png",
}

# Point-sampled far view, same divisor as the switch sweep: a 128-high wall
# is 16 px tall on screen, so a 64-high crate is 8 px. NEAREST, not smooth.
FAR_DIVISOR = 8
# Rough stand-in for sector light ~112 seen from mid-distance: RGB x 0.5,
# re-quantised to the palette (which is roughly what a COLORMAP does), then
# shown as luma only. NOT VERIFIED against GZDoom's own light tables; it is
# here to show which cells keep their edge when only value is left.
DIM_FACTOR = 0.5


@dataclass(frozen=True)
class Piece:
    row: str
    lump: str
    kind: str           # "wall" or "flat"
    w: int
    h: int
    name_en: str
    name_ru: str
    where_en: str
    where_ru: str


PIECES = (
    Piece("R1", "SDCRAT1", "wall", 64, 64, "Crate face", "Сторона ящика",
          "hangar stacks, guard post, dorm; also the two ends of the long case",
          "штабеля в ангаре, караульное помещение, казарма; также торцы длинного ящика"),
    Piece("R2", "SDCRAT2", "wall", 128, 64, "Long case face", "Длинный ящик",
          "the parapet / low-cover unit of the hangar bays, two grid cells long",
          "бруствер, низкое укрытие в отсеках ангара, длиной в две клетки сетки"),
    Piece("R3", "SDCRTOP1", "flat", 64, 64, "Crate top", "Крышка ящика",
          "floor of every crate and case sector: what the catwalk looks down on",
          "пол каждого сектора-ящика: то, что видно сверху с мостков"),
    Piece("R4", "SDLOCK1", "wall", 64, 128, "Barracks locker", "Шкафчик казармы",
          "rows along the dorm walls (Z1, 128 high) and the locker closet S1",
          "ряды вдоль стен казармы (Z1, высота 128) и шкафная S1"),
)
PIECE = {p.row: p for p in PIECES}


@dataclass(frozen=True)
class Material:
    vid: str
    ramp: str
    mid: float          # ramp position of the body
    blotch: float
    grain: float
    finish: str         # "planks" or "steel"
    batten_gain: float  # battens lighter (>1) or darker (<1) than the body
    ink: tuple[str, float]
    en: str
    ru: str


MATERIALS = {
    "A": Material("A", "military_green", 0.24, 0.10, 0.025, "planks", 1.20,
                  ("cream_yellow", 0.80), "dark 4BO-green painted planks",
                  "тёмно-зелёные крашеные доски (4БО)"),
    "B": Material("B", "military_green", 0.47, 0.06, 0.020, "steel", 1.16,
                  ("cream_yellow", 0.85), "green pressed-steel case, ribs and latches",
                  "зелёный штампованный стальной ящик, рёбра и защёлки"),
    "C": Material("C", "khaki_olive", 0.58, 0.10, 0.030, "planks", 1.10,
                  ("concrete_cold", 0.08), "khaki planks, braced",
                  "доски цвета хаки, с раскосом"),
    "D": Material("D", "plaster_warm", 0.80, 0.10, 0.030, "planks", 0.90,
                  ("concrete_cold", 0.08), "bare pine, black steel straps",
                  "некрашеная сосна, чёрные стальные ленты"),
}
VARIANT_IDS = ("A", "B", "C", "D")

# --- shared crate armature -----------------------------------------------
FRAME = {"A": 6, "B": 4, "C": 6, "D": 5}   # batten / rim width per material
OUTLINE_TONE = 0.45     # outermost 1 px: the gap between stacked crates
PLANK_PITCH = 11        # px between plank joints
PLANK_STREAK = 0.14     # wood grain strength
JOINT_DARK, JOINT_LIGHT = 0.55, 1.10
RIB_PITCH = 8           # pressed ribs on the steel case
RIB_LIGHT, RIB_DARK = 1.18, 0.70
SHADOW = 0.62           # under / right of a batten (light from the top left)
HIGHLIGHT = 1.14        # top / left edge of a batten
BRACE_W = 7.0
STRAP_TONE = 0.20       # steel_blue: black-ish steel straps
STRAP_W = 3
NAIL_PITCH = 8
METAL_TONE = 0.55       # latches, corner plates, handles (steel_blue)
INK_ALPHA = 0.90
WEAR = 0.16             # fraction of stencil pixels knocked out by wear

# --- stencil glyphs: seven segments, hard pixels, no font ---------------
# a top, b upper right, c lower right, d bottom, e lower left, f upper left,
# g middle. Verticals run unbroken; a horizontal stops `gap` px short of any
# vertical it meets, and that 1 px break is the stencil bridge. Plates are
# too small for bridges and use gap 0.
SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc",
    "5": "afgcd", "6": "afgedc", "7": "abc", "8": "abcdefg", "9": "abcdfg",
    "-": "g",
}
CRATE_CAP, CRATE_STEM, CRATE_GAP = 13, 2, 1
CASE_CAP = 11
PLATE_CAP, PLATE_STEM = 7, 1
GLYPH_SPACING = 2
ARROW_W, ARROW_H, ARROW_STEM, ARROW_SPACING = 7, 9, 2, 3
BAR_GAP, BAR_H = 1, 2
STACK_GAP = 4           # between the arrows and the number when stacked

CRATE_NUMBER = "07"     # Zarya-7
CASE_NUMBER = "7-04"
LOCKER_NUMBERS = ("12", "13")


def glyph_width(ch: str, cap: int, stem: int) -> int:
    if ch == "-":
        return max(stem * 2 + 1, round(cap * 0.4))
    return max(stem * 2 + 2, round(cap * 0.6))


def glyph_mask(ch: str, cap: int, stem: int, gap: int) -> np.ndarray:
    wd = glyph_width(ch, cap, stem)
    m = np.zeros((cap, wd), bool)
    mid = (cap - stem) // 2
    segs = SEGMENTS[ch]
    # horizontal segment -> (rows, verticals it meets on the left, on the right)
    horizontals = {"a": ((0, stem), "f", "b"), "g": ((mid, mid + stem), "fe", "bc"),
                   "d": ((cap - stem, cap), "e", "c")}
    for seg, ((y0, y1), left, right) in horizontals.items():
        if seg in segs:
            x0 = stem + gap if any(v in segs for v in left) else 0
            x1 = wd - stem - gap if any(v in segs for v in right) else wd
            m[y0:y1, x0:x1] = True
    if "f" in segs:
        m[0:mid + stem, 0:stem] = True
    if "b" in segs:
        m[0:mid + stem, wd - stem:wd] = True
    if "e" in segs:
        m[mid:cap, 0:stem] = True
    if "c" in segs:
        m[mid:cap, wd - stem:wd] = True
    return m


def text_mask(text: str, cap: int, stem: int, gap: int) -> np.ndarray:
    parts = [glyph_mask(c, cap, stem, gap) for c in text]
    out = []
    for i, p in enumerate(parts):
        if i:
            out.append(np.zeros((cap, GLYPH_SPACING), bool))
        out.append(p)
    return np.concatenate(out, axis=1)


def arrow_mask() -> np.ndarray:
    """Upward arrow: a stepped triangular head over a stem."""
    m = np.zeros((ARROW_H, ARROW_W), bool)
    c = ARROW_W // 2
    head = c + 1
    for r in range(head):
        m[r, c - r:c + r + 1] = True
    s0 = (ARROW_W - ARROW_STEM) // 2
    m[head:, s0:s0 + ARROW_STEM] = True
    return m


def this_side_up_mask() -> np.ndarray:
    """Two arrows over a bar: the shipping mark, no lettering needed."""
    a = arrow_mask()
    pair = np.concatenate([a, np.zeros((ARROW_H, ARROW_SPACING), bool), a], axis=1)
    bar = np.ones((BAR_H, pair.shape[1]), bool)
    return np.concatenate([pair, np.zeros((BAR_GAP, pair.shape[1]), bool), bar], axis=0)


def stencil_mask(kind: str) -> np.ndarray:
    if kind == "arrows":
        return this_side_up_mask()
    if kind == "crate":
        return text_mask(CRATE_NUMBER, CRATE_CAP, CRATE_STEM, CRATE_GAP)
    if kind == "case":
        return text_mask(CASE_NUMBER, CASE_CAP, CRATE_STEM, CRATE_GAP)
    if kind.startswith("plate:"):
        return text_mask(kind[6:], PLATE_CAP, PLATE_STEM, 0)
    raise KeyError(kind)


# ================================================================ layout
# Declared as data, then painted, so tests/test_gen_props.py can check from
# the outside that nothing overlaps (the lesson of switch variant A, whose
# board, word and lamp were found touching by eye).
Rect = tuple[int, int, int, int]   # x0, y0, x1, y1 (exclusive)


def center_in(region: Rect, size: tuple[int, int]) -> Rect:
    x0, y0, x1, y1 = region
    w, h = size
    x = x0 + (x1 - x0 - w) // 2
    y = y0 + (y1 - y0 - h) // 2
    return (x, y, x + w, y + h)


def stack_in(region: Rect, kinds: list[str]) -> list[tuple[str, Rect]]:
    """Centre several stencil marks in a region, stacked vertically."""
    sizes = [stencil_mask(k).shape[::-1] for k in kinds]
    total_h = sum(s[1] for s in sizes) + STACK_GAP * (len(kinds) - 1)
    total_w = max(s[0] for s in sizes)
    x0, y0, _, _ = center_in(region, (total_w, total_h))
    out, y = [], y0
    for k, (w, h) in zip(kinds, sizes):
        x = x0 + (total_w - w) // 2
        out.append((k, (x, y, x + w, y + h)))
        y += h + STACK_GAP
    return out


def crate_layout(row: str, vid: str) -> dict:
    """Structure of a crate-family piece (R1, R2, R3) as rectangles.

    battens  wood (or rim) rectangles, painted lighter/darker than the body
    straps   black steel bands with nails
    metal    latches, corner plates, handles
    brace    a diagonal batten: (x0, y0, x1, y1) centre line, width BRACE_W
    stencil  [(kind, rect)] marks, each centred in a clear region
    """
    p = PIECE[row]
    w, h, fr = p.w, p.h, FRAME[vid]
    lay = {"battens": [(0, 0, w, fr), (0, h - fr, w, h), (0, 0, fr, h), (w - fr, 0, w, h)],
           "straps": [], "metal": [], "brace": None, "stencil": []}
    inner = (fr, fr, w - fr, h - fr)

    if row == "R1":
        if vid == "B":
            lay["metal"] += [(14, 1, 22, 8), (42, 1, 50, 8)]            # two latches on the rim
            lay["metal"] += [(0, 0, 8, 8), (w - 8, 0, w, 8), (0, h - 8, 8, h), (w - 8, h - 8, w, h)]
            lay["stencil"] = stack_in((fr, 10, w - fr, h - fr), ["arrows", "crate"])
        elif vid == "C":
            lay["brace"] = (fr, h - fr, w - fr, fr)                      # Z brace, bottom left to top right
            lay["stencil"] = stack_in((fr + 2, fr + 2, fr + 22, fr + 17), ["crate"])
        elif vid == "D":
            lay["straps"] = [(14, 0, 14 + STRAP_W, h), (47, 0, 47 + STRAP_W, h)]
            lay["stencil"] = stack_in((17, fr, 47, h - fr), ["arrows", "crate"])
        else:
            lay["stencil"] = stack_in(inner, ["arrows", "crate"])
    elif row == "R2":
        if vid == "A":
            lay["battens"].append((61, 0, 67, h))
            bays = [(fr, fr, 61, h - fr), (67, fr, w - fr, h - fr)]
        elif vid == "B":
            lay["metal"] += [(18, 1, 26, 8), (54, 1, 74, 8), (102, 1, 110, 8)]   # latches + lifting lug
            lay["metal"] += [(0, 0, 8, 8), (w - 8, 0, w, 8), (0, h - 8, 8, h), (w - 8, h - 8, w, h)]
            bays = [(fr, 10, 64, h - fr), (64, 10, w - fr, h - fr)]
        elif vid == "C":
            lay["battens"] += [(36, 0, 42, h), (86, 0, 92, h)]
            bays = [(fr, fr, 36, h - fr), (42, fr, 86, h - fr)]
        else:
            lay["straps"] = [(30, 0, 30 + STRAP_W, h), (94, 0, 94 + STRAP_W, h)]
            bays = [(fr, fr, 30, h - fr), (33, fr, 94, h - fr)]
        lay["stencil"] = stack_in(bays[0], ["arrows"]) + stack_in(bays[1], ["case"])
    elif row == "R3":
        if vid == "B":
            lay["metal"] += [(22, 44, 42, 48)]                          # carrying handle
            lay["metal"] += [(0, 0, 8, 8), (w - 8, 0, w, 8), (0, h - 8, 8, h), (w - 8, h - 8, w, h)]
            lay["stencil"] = stack_in((fr, 10, w - fr, 42), ["crate"])
        elif vid == "C":
            lay["battens"].append((0, 29, w, 35))                       # cross batten of the lid
            lay["stencil"] = stack_in((fr, fr, w - fr, 29), ["crate"])
        elif vid == "D":
            lay["straps"] = [(0, 14, w, 14 + STRAP_W), (0, 47, w, 47 + STRAP_W)]
            lay["stencil"] = stack_in((fr, 17, w - fr, 47), ["crate"])
        else:
            lay["stencil"] = stack_in(inner, ["crate"])
    else:
        raise KeyError(row)
    return lay


# Locker: the elements are stacked top to bottom with declared rows, two
# doors side by side. Every variant shares the frame; B is two narrow
# lockers, C is a wooden wardrobe (panels instead of louvres), D adds name
# card slots.
LOCKER_LIP = (0, 4)
LOCKER_PLINTH = (120, 128)
LOCKER_SEAM = 32        # x of the joint between the two doors
LOCKER_MIN_GAP = 2      # px between stacked elements (test-enforced)


def locker_layout(vid: str) -> dict:
    p = PIECE["R4"]
    w = p.w
    rows = {"lip": LOCKER_LIP, "plate": (8, 17)}
    if vid == "D":
        rows["card"] = (19, 23)
    if vid == "C":
        rows["panel_top"] = (25, 56)
        rows["handle"] = (62, 66)
        rows["panel_low"] = (74, 114)
    else:
        rows["louvre_top"] = (26, 42)
        rows["handle"] = (58, 70)
        rows["louvre_low"] = (98, 110)
    rows["plinth"] = LOCKER_PLINTH
    doors = [(1, LOCKER_SEAM), (LOCKER_SEAM, w - 1)]
    if vid == "B":
        handles_x = [(26, 28), (58, 60)]            # each narrow locker opens on its right
    elif vid == "C":
        handles_x = [(27, 30), (34, 37)]            # two knobs either side of the seam
    else:
        handles_x = [(27, 29), (35, 37)]            # double door: handles meet at the seam
    plates = []
    for (dx0, dx1), num in zip(doors, LOCKER_NUMBERS):
        mw, mh = stencil_mask("plate:" + num).shape[::-1]
        pw = mw + 5
        px = dx0 + (dx1 - dx0 - pw) // 2
        y0, y1 = rows["plate"]
        plates.append(((px, y0, px + pw, y1), ("plate:" + num, center_in((px, y0, px + pw, y1), (mw, mh)))))
    return {"rows": rows, "doors": doors, "handles_x": handles_x, "plates": plates}


# ================================================================ paint
def rng_for(row: str, vid: str) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + 10 * int(row[1:]) + VARIANT_IDS.index(vid) + 1)


def luma(rgb: np.ndarray) -> np.ndarray:
    a = rgb.astype(np.float64)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def rect_mask(shape: tuple[int, int], rects: list[Rect]) -> np.ndarray:
    m = np.zeros(shape, bool)
    for x0, y0, x1, y1 in rects:
        m[y0:y1, x0:x1] = True
    return m


def brace_mask(shape: tuple[int, int], line, width: float = BRACE_W) -> np.ndarray:
    h, w = shape
    x0, y0, x1, y1 = line
    ys, xs = np.mgrid[0:h, 0:w] + 0.5
    dx, dy = x1 - x0, y1 - y0
    n = np.hypot(dx, dy)
    dist = np.abs(dy * (xs - x0) - dx * (ys - y0)) / n
    return dist <= width / 2


def body(w: int, h: int, mat: Material, rng: np.random.Generator, grain_dir: str) -> np.ndarray:
    f = mat.mid + (fbm(w, h, 2, 4, rng) - 0.5) * mat.blotch + grain(w, h, rng, mat.grain)
    if mat.finish == "planks":
        if grain_dir == "h":
            streak = fbm(h, w, 8, 3, rng, 0.6, aspect=8).T
        else:
            streak = fbm(w, h, 8, 3, rng, 0.6, aspect=8)
        f = f + (streak - 0.5) * PLANK_STREAK
    return to_rgb(f, mat.ramp)


def edge_shading(mask: np.ndarray) -> np.ndarray:
    """Highlight on the top/left edge of a raised mask, shadow just below and
    right of it. Light comes from the top left, as on the switches."""
    f = np.ones(mask.shape)
    up = np.zeros_like(mask)
    up[1:] = mask[:-1]
    left = np.zeros_like(mask)
    left[:, 1:] = mask[:, :-1]
    f[mask & ~(up & left)] = HIGHLIGHT
    f[~mask & (up | left)] = SHADOW
    return f


def outline(f: np.ndarray) -> np.ndarray:
    f = f.copy()
    f[0, :] *= OUTLINE_TONE
    f[-1, :] *= OUTLINE_TONE
    f[:, 0] *= OUTLINE_TONE
    f[:, -1] *= OUTLINE_TONE
    return f


def paint_stencil(rgb: np.ndarray, items, ink: tuple[str, float], rng: np.random.Generator,
                  wear: float = WEAR) -> np.ndarray:
    col = ramp_colour(*ink)
    full = np.zeros(rgb.shape[:2], bool)
    for kind, (x0, y0, x1, y1) in items:
        full[y0:y1, x0:x1] |= stencil_mask(kind)
    keep = rng.random(full.shape) >= wear
    return blend(rgb, col, (full & keep) * INK_ALPHA)


def joints(shape: tuple[int, int], pitch: int, axis: str, dark: float, light: float,
           offset: int = 3) -> np.ndarray:
    h, w = shape
    f = np.ones(shape)
    n = h if axis == "h" else w
    for i in range(offset, n, pitch):
        if axis == "h":
            f[i, :] = dark
            if i + 1 < h:
                f[i + 1, :] = light
        else:
            f[:, i] = dark
            if i + 1 < w:
                f[:, i + 1] = light
    return f


def crate_piece(row: str, vid: str) -> np.ndarray:
    """R1, R2 and R3: same armature, the layout decides the rest."""
    p, mat, rng = PIECE[row], MATERIALS[vid], rng_for(row, vid)
    w, h = p.w, p.h
    lay = crate_layout(row, vid)
    grain_dir = "v" if vid == "D" else "h"
    other = "h" if grain_dir == "v" else "v"

    planks = body(w, h, mat, rng, grain_dir)
    if mat.finish == "planks":
        planks = shade(planks, joints((h, w), PLANK_PITCH, grain_dir, JOINT_DARK, JOINT_LIGHT))
    else:
        planks = shade(planks, joints((h, w), RIB_PITCH, "h", RIB_DARK, RIB_LIGHT, offset=6))
    battens_rgb = shade(body(w, h, mat, rng, other), mat.batten_gain)

    bmask = rect_mask((h, w), lay["battens"])
    if lay["brace"] is not None:
        bmask |= brace_mask((h, w), lay["brace"])
    rgb = np.where(bmask[..., None], battens_rgb, planks)
    rgb = shade(rgb, edge_shading(bmask))

    if lay["straps"]:
        smask = rect_mask((h, w), lay["straps"])
        rgb = np.where(smask[..., None], np.array(ramp_colour("steel_blue", STRAP_TONE), np.uint8), rgb)
        nails = np.zeros((h, w), bool)
        for x0, y0, x1, y1 in lay["straps"]:
            cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
            if x1 - x0 < y1 - y0:
                nails[NAIL_PITCH // 2::NAIL_PITCH, cx] = True
            else:
                nails[cy, NAIL_PITCH // 2::NAIL_PITCH] = True
        nails &= smask
        rgb = np.where(nails[..., None], np.array(ramp_colour("steel_blue", 0.70), np.uint8), rgb)
    if lay["metal"]:
        mmask = rect_mask((h, w), lay["metal"])
        metal = to_rgb(METAL_TONE + grain(w, h, rng, 0.04), "steel_blue")
        rgb = np.where(mmask[..., None], metal, rgb)
        rgb = shade(rgb, edge_shading(mmask))

    rgb = paint_stencil(rgb, lay["stencil"], mat.ink, rng)
    return shade(rgb, outline(np.ones((h, w))))


LOCKER_MAT = {
    # locker bodies are painted sheet metal, except C (plywood wardrobe)
    "A": ("military_green", 0.24, "steel"),
    "B": ("military_green", 0.47, "steel"),
    "C": ("khaki_olive", 0.58, "planks"),
    "D": ("plaster_warm", 0.80, "steel"),
}
LOUVRE_PITCH = 4
LOUVRE_INSET = 6


def locker_piece(vid: str) -> np.ndarray:
    p, rng = PIECE["R4"], rng_for("R4", vid)
    w, h = p.w, p.h
    ramp_name, mid, finish = LOCKER_MAT[vid]
    mat = Material(vid, ramp_name, mid, 0.08, 0.02, finish, 1.0, MATERIALS[vid].ink, "", "")
    lay = locker_layout(vid)
    rows = lay["rows"]
    rgb = body(w, h, mat, rng, "v")
    f = np.ones((h, w))

    # lip and plinth
    f[rows["lip"][0]:rows["lip"][1], :] = 1.15
    f[rows["lip"][1] - 1, :] = 0.6
    f[rows["plinth"][0]:rows["plinth"][1], :] = 0.42
    # doors: lit left edge, dark right edge, dark seam between them
    for dx0, dx1 in lay["doors"]:
        f[rows["lip"][1]:rows["plinth"][0], dx0] *= 1.18
        f[rows["lip"][1]:rows["plinth"][0], dx1 - 1] *= 0.62
    seam_w = 2 if vid == "B" else 1
    f[rows["lip"][1]:rows["plinth"][0], LOCKER_SEAM - seam_w:LOCKER_SEAM] *= 0.45
    # louvres or panels
    for key in ("louvre_top", "louvre_low"):
        if key in rows:
            y0, y1 = rows[key]
            for dx0, dx1 in lay["doors"]:
                for y in range(y0, y1, LOUVRE_PITCH):
                    f[y, dx0 + LOUVRE_INSET:dx1 - LOUVRE_INSET] *= 0.40
                    f[y + 1, dx0 + LOUVRE_INSET:dx1 - LOUVRE_INSET] *= 1.20
    for key in ("panel_top", "panel_low"):
        if key in rows:
            y0, y1 = rows[key]
            for dx0, dx1 in lay["doors"]:
                x0, x1 = dx0 + 5, dx1 - 5
                m = rect_mask((h, w), [(x0, y0, x1, y1)])
                f *= edge_shading(m) ** -1          # sunken panel: shadow top/left, light bottom/right
    rgb = shade(rgb, f)
    # handles
    y0, y1 = rows["handle"]
    metal = ramp_colour("steel_blue", METAL_TONE + 0.15)
    hmask = rect_mask((h, w), [(x0, y0, x1, y1) for x0, x1 in lay["handles_x"]])
    rgb = np.where(hmask[..., None], np.array(metal, np.uint8), rgb)
    rgb = shade(rgb, edge_shading(hmask))
    # number plates (and D's name card slots)
    plate_col = ramp_colour("cream_yellow", 0.72) if vid in ("A", "B") else ramp_colour("steel_blue", 0.30)
    plate_ink = ("concrete_cold", 0.08) if vid in ("A", "B") else ("cream_yellow", 0.85)
    pmask = rect_mask((h, w), [pr for pr, _ in lay["plates"]])
    rgb = np.where(pmask[..., None], np.array(plate_col, np.uint8), rgb)
    rgb = shade(rgb, edge_shading(pmask))
    rgb = paint_stencil(rgb, [st for _, st in lay["plates"]], plate_ink, rng, wear=0.0)
    if "card" in rows:
        y0, y1 = rows["card"]
        cards = [(px0 + 1, y0, px1 - 1, y1) for (px0, _, px1, _), _ in lay["plates"]]
        cmask = rect_mask((h, w), cards)
        rgb = np.where(cmask[..., None], np.array(ramp_colour("plaster_warm", 0.95), np.uint8), rgb)
        rgb = shade(rgb, edge_shading(cmask) ** -1)
    return shade(rgb, outline(np.ones((h, w))))


def build(row: str, vid: str) -> np.ndarray:
    return locker_piece(vid) if row == "R4" else crate_piece(row, vid)


# ======================================================= context + metrics
ELEV_W, WALL_H, FLOOR_H = 256, 128, 16
PLAN_W, PLAN_H = 256, 192
ELEV_PLACEMENTS = {
    # (x, y_bottom) of each copy in a 256 x 128 wall, floor-pegged like the map
    "R1": [(64, 128), (128, 128), (64, 64)],
    "R2": [(32, 128), (64, 64)],
    "R4": [(64, 128), (128, 128)],
}
PLAN_PLACEMENTS = [(64, 64), (128, 64), (64, 128)]   # an L of three crates seen from above
WALL_HOSTS = {
    # wall host -> floor in front of it, as in MAP01 §6
    "R1": [("SDCONC1", "SDFLR2"), ("SDSTEL1", "SDFLR2")],
    "R2": [("SDCONC1", "SDFLR2"), ("SDSTEL1", "SDFLR2")],
    "R4": [("SDCONC1", "SDFLR3"), ("SDSTEL1", "SDFLR2")],
}


def host_rgb(name: str) -> np.ndarray:
    with Image.open(HOST_FILES[name]) as im:
        return np.asarray(im.convert("RGB"), dtype=np.uint8)


def tile_to(rgb: np.ndarray, w: int, h: int) -> np.ndarray:
    hh, hw = rgb.shape[:2]
    return np.tile(rgb, (-(-h // hh), -(-w // hw), 1))[:h, :w]


def elevation(row: str, piece: np.ndarray, wall: str, floor: str) -> np.ndarray:
    """The prop standing against its wall, floor band foreshortened below.
    No contact shadow is faked: Doom draws none."""
    canvas = tile_to(host_rgb(wall), ELEV_W, WALL_H).copy()
    ph, pw = piece.shape[:2]
    for x, yb in ELEV_PLACEMENTS[row]:
        canvas[yb - ph:yb, x:x + pw] = piece
    fl = tile_to(host_rgb(floor), ELEV_W, GRID)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((ELEV_W, FLOOR_H), Image.Resampling.NEAREST))
    return np.concatenate([canvas, fl], axis=0)


def plan(piece: np.ndarray) -> np.ndarray:
    canvas = tile_to(host_rgb("SDFLR2"), PLAN_W, PLAN_H).copy()
    for x, y in PLAN_PLACEMENTS:
        canvas[y:y + GRID, x:x + GRID] = piece
    return canvas


def far(rgb: np.ndarray) -> np.ndarray:
    h, w = rgb.shape[:2]
    return np.asarray(Image.fromarray(rgb, "RGB").resize(
        (w // FAR_DIVISOR, h // FAR_DIVISOR), Image.Resampling.NEAREST), dtype=np.uint8)


def dim_value(rgb: np.ndarray) -> np.ndarray:
    """Far view at low sector light, value only (see DIM_FACTOR)."""
    darker = quantize(Image.fromarray(shade(far(rgb), DIM_FACTOR), "RGB")).convert("RGB")
    return np.clip(luma(np.asarray(darker)), 0, 255).astype(np.uint8)


def host_luma(name: str) -> float:
    return float(luma(host_rgb(name)).mean())


def measure(row: str, rgb: np.ndarray) -> dict:
    """Numbers quoted on the sheet.

    gap_<host>   |mean luma of the piece - mean luma of the host|: how far
                 the prop stands from what is behind (or around) it by value
    worst_gap    the smaller of those: the host on which the prop reads worst
    far_sigma    luma spread of the piece itself after the 8x point-sample:
                 how much of its structure (battens, plates, stencil) is
                 left when it is 8-16 px tall. ~0 means a flat blob.
    """
    lm = float(luma(rgb).mean())
    hosts = ["SDFLR2"] if PIECE[row].kind == "flat" else ["SDCONC1", "SDSTEL1"]
    out = {"mean_luma": round(lm, 1), "far_sigma": round(float(luma(far(rgb)).std()), 1)}
    for hst in hosts:
        out[f"gap_{hst}"] = round(abs(lm - host_luma(hst)), 1)
    out["worst_gap"] = min(out[f"gap_{hst}"] for hst in hosts)
    return out


def save_rgb(path: Path, rgb: np.ndarray) -> Path:
    save_indexed(rgb, path)
    return path


def save_plain(path: Path, rgb: np.ndarray) -> Path:
    """Sheet illustrations that are not textures (far views): already palette
    pixels, but not bound by the multiple-of-8 rule of save_indexed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb, "RGB").save(path, optimize=True)
    return path


def save_grey(path: Path, l8: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(l8, "L").save(path, optimize=True)
    return path


# ================================================================ sheet
RECOMMENDED = {"R1": "C", "R2": "C", "R3": "C", "R4": "D"}

INTRO_EN = (
    "<b>Crates and lockers for MAP01 v2 &mdash; request A5 of <code>level-designer</code>.</b> "
    "A cheap sweep, not finished art: <b>rows are pieces, columns are variants</b>, and every cell "
    "has a label (<b>R2-C</b>) so you can point at one. Four pieces, sized from the map rather than "
    "from taste: a 64&times;64 crate face (one grid cell, one tile on a 64-high crate), a 128&times;64 "
    "long case (the parapet unit of the hangar bays), the 64&times;64 crate top (what the catwalk "
    "looks down on) and a 64&times;128 barracks locker (floor to ceiling in the 128-high dorm). "
    "The four columns sweep <b>value</b>, dark to pale, because value is what survives Doom's "
    "sector light and hue does not; the material follows the value, so each column is one "
    "coherent family. You can still pick a different column per row. Nothing here is in "
    "<code>assets/</code>.")

INTRO_RU = (
    "<b>Ящики и шкафчики для MAP01 v2 &mdash; запрос A5 от <code>level-designer</code>.</b> "
    "Дешёвый лист вариантов, а не готовая графика: <b>строки &mdash; предметы, столбцы &mdash; "
    "варианты</b>, у каждой ячейки есть метка (<b>R2-C</b>), чтобы можно было указать на одну. "
    "Четыре предмета, размеры взяты из карты, а не из вкуса: сторона ящика 64&times;64 (одна клетка "
    "сетки, одна плитка на ящике высотой 64), длинный ящик 128&times;64 (единица бруствера в отсеках "
    "ангара), крышка ящика 64&times;64 (то, что видно с мостков) и шкафчик казармы 64&times;128 (от "
    "пола до потолка в казарме высотой 128). Четыре столбца перебирают <b>яркость</b>, от тёмного к "
    "светлому, потому что при освещении по секторам в Doom выживает яркость, а не оттенок; материал "
    "следует за яркостью, так что каждый столбец &mdash; одно согласованное семейство. Для каждой "
    "строки можно выбрать свой столбец. Ничего из этого нет в <code>assets/</code>.")

LEAD_EN = (
    "Each cell at 2&times;. The piece names are working names until you choose; if you take more "
    "than one variant of a row, they get a letter suffix like the switches "
    "(<code>SDCRAT1A</code>&hellip;).")
LEAD_RU = (
    "Каждая ячейка при 2&times;. Имена предметов рабочие, пока вы не выберете; если возьмёте "
    "несколько вариантов одной строки, они получат буквенный суффикс, как выключатели "
    "(<code>SDCRAT1A</code>&hellip;).")

DETAIL_LEAD_EN = (
    "Each card: the piece at 4&times; and 1&times;; then the piece in place on the walls it will "
    "really stand against, floor-pegged like the map, with the floor of that room foreshortened "
    "below (no shadow is painted in: Doom draws none); then the same scene point-sampled down by "
    "{d} (a 64-high crate is 8 px tall), in colour and as <b>value only at low light</b> "
    "(RGB &times;{f}, re-quantised to the palette, then luma &mdash; an approximation of sector light "
    "~112, NOT VERIFIED against GZDoom's light tables). The last strip is where the columns differ.")
DETAIL_LEAD_RU = (
    "В каждой карточке: предмет при 4&times; и 1&times;; затем предмет на месте, у тех стен, у которых "
    "он действительно будет стоять, с привязкой к полу, как на карте, и с полом этой комнаты в "
    "перспективе снизу (тень не нарисована: Doom её не рисует); затем та же сцена, уменьшенная "
    "точечной выборкой в {d} раз (ящик высотой 64 становится 8 px), в цвете и <b>только яркостью при "
    "слабом свете</b> (RGB &times;{f}, повторно приведено к палитре, затем яркость &mdash; приближение "
    "освещения сектора ~112, НЕ ПРОВЕРЕНО по таблицам света GZDoom). Последняя полоса &mdash; то место, "
    "где столбцы расходятся.")

LETTERING_EN = (
    "<b>No font is used anywhere in these textures.</b> The crate numbers (<code>07</code>, "
    "<code>7-04</code>), the &ldquo;this side up&rdquo; arrows and the locker plates "
    "(<code>12</code>, <code>13</code>) are drawn as hard pixels from seven-segment data in "
    "<code>tools/art/gen_props.py</code>, the way <code>tools/art/gen_font.py</code> draws the mod's "
    "alphabet from strokes; the 1-px breaks where the strokes meet are the stencil bridges. Reason: "
    "Impact rasterises differently on this Windows PC and on the Mac (measured 2026-10-13: the "
    "switches differ by ~180 px, all inside the painted word), so a lump lettered with it can only "
    "ever be regenerated on the machine that rendered it. A lump with no font is byte-identical on "
    "both machines, and the mod's new detail textures should not depend on which computer drew "
    "them. A side effect worth having: no Cyrillic or Latin word to translate or to get wrong, "
    "and numbers and arrows are exactly what a real crate carries.")
LETTERING_RU = (
    "<b>Ни в одной из этих текстур не используется шрифт.</b> Номера ящиков (<code>07</code>, "
    "<code>7-04</code>), стрелки «верх» и таблички шкафчиков (<code>12</code>, <code>13</code>) "
    "нарисованы жёсткими пикселями из семисегментных данных в <code>tools/art/gen_props.py</code>, так "
    "же, как <code>tools/art/gen_font.py</code> рисует алфавит мода из штрихов; разрывы в 1 px на стыках "
    "штрихов &mdash; это перемычки трафарета. Причина: Impact растеризуется по-разному на этом ПК с "
    "Windows и на Mac (измерено 2026-10-13: выключатели отличаются примерно на 180 px, все внутри "
    "нарисованного слова), поэтому текстуру с надписью этим шрифтом можно пересобрать только на той "
    "машине, где она была создана. Текстура без шрифта побайтно одинакова на обеих машинах, и новые "
    "текстуры деталей мода не должны зависеть от того, какой компьютер их нарисовал. Полезный побочный "
    "эффект: нет ни кириллического, ни латинского слова, которое надо переводить или в котором можно "
    "ошибиться, а цифры и стрелки &mdash; ровно то, что несёт настоящий ящик.")

SCOPE_EN = (
    "<b>Why these four and not more.</b> MAP01 §10 (A5) and §15 ask for a crate face for the dorm, "
    "the guard post and the hangar bays, and v2 adds parapets and detail. A crate needs a face "
    "<i>and</i> a top: the catwalk (floor 96) looks down on every stack in the hangar, so a crate "
    "sector with a plain concrete floor on top would give itself away. The parapet is the long case: "
    "one sector two cells long, its ends wearing the crate face (same height, same material, same "
    "column). The locker is 64 wide so it tiles into a row and 128 high because the dorm is exactly "
    "128 floor to ceiling. <b>Left out on purpose:</b> the fuel drums of the fuel bay (round props "
    "are sprites, not wall textures; Freedoom's barrel or our own sprite in F4/F5), the hangar's "
    "green steel dado (a wall texture, a separate request in §15), and the catwalk's parapet, which "
    "§6 already gives to <code>SDSTEL1</code>.")
SCOPE_RU = (
    "<b>Почему эти четыре и не больше.</b> MAP01 §10 (A5) и §15 просят сторону ящика для казармы, "
    "караульного помещения и отсеков ангара, а v2 добавляет брустверы и детали. Ящику нужна сторона "
    "<i>и</i> крышка: с мостков (пол 96) видны все штабеля в ангаре, и сектор-ящик с простым бетонным "
    "полом сверху выдал бы себя. Бруствер &mdash; это длинный ящик: один сектор длиной в две клетки, "
    "его торцы носят сторону ящика (та же высота, тот же материал, тот же столбец). Шкафчик шириной "
    "64, чтобы складываться в ряд, и высотой 128, потому что в казарме от пола до потолка ровно 128. "
    "<b>Намеренно не включено:</b> бочки с топливом в топливном отсеке (круглые предметы &mdash; это "
    "спрайты, а не текстуры стен; бочка Freedoom или наш спрайт в F4/F5), зелёная стальная панель "
    "ангара (текстура стены, отдельный запрос в §15) и парапет мостков, который §6 уже отдаёт "
    "<code>SDSTEL1</code>.")

# Written after the art director's single look at the rendered sweep
# (PIPELINE stage 2) and the measurement table; the numbers quoted are the
# ones main() prints.
RECO_EN = (
    "<b>Recommendation: column C for the three crate pieces (R1-C, R2-C, R3-C) and D for the locker "
    "(R4-D).</b> What the sweep shows: <b>column B disappears on the green steel wall</b> (gap 0.4 for "
    "the crate, 2.4 for the case: the same trap the switches found, mid green on mid green), so it is "
    "only safe on concrete and the v2 hangar is meant to get a steel dado. <b>Column A reads on both "
    "walls</b> (gaps 31 and 76) but it is the darkest mass in the base, luma ~70, below the 0.45-0.70 "
    "band ART-BIBLE &sect;6.1 keeps walls in so the Fourth Reich's dark uniforms still separate; a "
    "hangar full of it would be the worst backdrop in the map for F5. <b>Column C</b> sits in the "
    "middle of that band (luma ~123, 22 from concrete, 22 from steel) and carries the one shape that "
    "survives the 8x point-sample on both walls: the diagonal brace. R2-C (three bays) and R3-C "
    "(cross batten) belong to the same family, and the long case's ends wear R1-C. <b>One caveat I "
    "want you to see:</b> C is drawn in <code>khaki_olive</code>, which ART-BIBLE &sect;3/&sect;6.2 "
    "reserve for Reich flesh. If that reservation holds, the approved version repaints C in "
    "<code>rust_brown</code> wood at the same value (one constant, the value and therefore the read "
    "unchanged) and comes back to you as a single image. <b>Locker: D</b>, cream-painted sheet metal "
    "(luma ~168): 21 above the dorm's concrete and 67 above the steel of the locker closet S1, the "
    "only column that is clearly apart from both rooms it lives in; cream is the base's own whitewash "
    "(<code>plaster_warm</code>), and it is nowhere near chrome. R4-C is the fallback if you want "
    "wood in the barracks. <b>What does not work yet:</b> the stencil numbers read as stencil marks at "
    "4x, but the 7 with its bridge can pass for a 1, and at 1x <code>07</code> is texture, not a "
    "number. That is acceptable for a crate (nobody reads it in play); say so if you want the marks "
    "bigger or gone.")
RECO_RU = (
    "<b>Рекомендация: столбец C для трёх частей ящика (R1-C, R2-C, R3-C) и D для шкафчика "
    "(R4-D).</b> Что показывает лист: <b>столбец B пропадает на зелёной стальной стене</b> (разрыв 0,4 "
    "у ящика, 2,4 у длинного ящика: та же ловушка, что нашли выключатели, средний зелёный на среднем "
    "зелёном), поэтому он безопасен только на бетоне, а в ангаре v2 должна появиться стальная панель. "
    "<b>Столбец A читается на обеих стенах</b> (разрывы 31 и 76), но это самая тёмная масса на базе, "
    "яркость ~70, ниже полосы 0,45-0,70, в которой ART-BIBLE &sect;6.1 держит стены, чтобы тёмная форма "
    "Четвёртого рейха отделялась от фона; ангар, полный таких ящиков, стал бы худшим фоном карты для "
    "F5. <b>Столбец C</b> стоит посередине этой полосы (яркость ~123, 22 от бетона, 22 от стали) и "
    "несёт единственную форму, которая переживает точечную выборку 8x на обеих стенах: диагональный "
    "раскос. R2-C (три секции) и R3-C (поперечная планка) из той же семьи, а торцы длинного ящика носят "
    "R1-C. <b>Одна оговорка, которую вам стоит увидеть:</b> C нарисован в <code>khaki_olive</code>, "
    "которую ART-BIBLE &sect;3/&sect;6.2 резервирует для плоти рейха. Если резерв остаётся в силе, "
    "одобренная версия перекрашивает C в дерево <code>rust_brown</code> той же яркости (одна константа, "
    "яркость, а значит и читаемость, не меняются) и возвращается к вам одной картинкой. <b>Шкафчик: "
    "D</b>, листовой металл кремовой окраски (яркость ~168): на 21 светлее бетона казармы и на 67 "
    "светлее стали шкафной S1, единственный столбец, который явно отделяется от обеих комнат, где он "
    "стоит; кремовый &mdash; это собственная побелка базы (<code>plaster_warm</code>), и до хрома ему "
    "далеко. R4-C &mdash; запасной вариант, если в казарме нужно дерево. <b>Что пока не работает:</b> "
    "трафаретные номера читаются как трафарет при 4x, но 7 с перемычкой можно принять за 1, а при 1x "
    "<code>07</code> &mdash; это фактура, а не число. Для ящика это допустимо (в игре его никто не "
    "читает); скажите, если нужны знаки крупнее или без них.")

ASK_EN = ("What I need from you:<ol>"
          "<li><b>One cell per row</b> (e.g. R1-C, R2-A, R3-C, R4-D), or a whole column if you want the "
          "four to match. Taking two variants of a row is fine: they get a letter suffix.</li>"
          "<li>Whether the numbers stay (<code>07</code>, <code>7-04</code>, locker <code>12</code> / "
          "<code>13</code>) or the crates go blank.</li></ol>")
ASK_RU = ("Что нужно от вас:<ol>"
          "<li><b>По одной ячейке на строку</b> (например, R1-C, R2-A, R3-C, R4-D) или целый столбец, если "
          "хотите, чтобы все четыре совпадали. Можно взять два варианта одной строки: они получат буквенный "
          "суффикс.</li>"
          "<li>Оставить ли номера (<code>07</code>, <code>7-04</code>, шкафчики <code>12</code> / "
          "<code>13</code>) или ящики будут без надписей.</li></ol>")

LABELS = {
    "en": dict(at1="1x", at4="4x", far=f"/{FAR_DIVISOR} point-sampled", dim="value at low light",
               on="on", plan="from above, among SDFLR2", recommended="recommended",
               h_cell="Cell", h_mean="Mean luma", h_conc="Gap vs SDCONC1 (147)",
               h_stel="Gap vs SDSTEL1 (101)", h_flr="Gap vs SDFLR2 (140)", h_worst="Worst-host gap",
               h_sigma="Structure left at far view (σ)", h_seed="Seed", piece="Piece", variant="Variant",
               sec_sweep="The sweep", sec_rows="Row {row} — {name} ({lump}, {w}×{h} {kind})",
               sec_table="Measurements", sec_letter="Lettering: none from a font",
               sec_scope="Scope", sec_reco="Reading and recommendation",
               sec_pal="Palette used (ratified v1, untouched)", sec_ask="Verdict",
               wall="wall", flat="flat", where="Where it lives",
               footer="Origin (a): procedural, {script}, seed {seed} + 10·row + variant. Palette "
                      "docs/art/palette.json v1, nothing added. No font. Licence: own work, "
                      "CC BY-NC-SA 4.0 (D15). Draft: nothing here is in assets/."),
    "ru": dict(at1="1x", at4="4x", far=f"точечная выборка /{FAR_DIVISOR}", dim="яркость при слабом свете",
               on="на", plan="сверху, среди SDFLR2", recommended="рекомендуется",
               h_cell="Ячейка", h_mean="Средняя яркость", h_conc="Разрыв с SDCONC1 (147)",
               h_stel="Разрыв с SDSTEL1 (101)", h_flr="Разрыв с SDFLR2 (140)",
               h_worst="Разрыв с худшим фоном", h_sigma="Структура в дальнем виде (σ)", h_seed="Зерно",
               piece="Предмет", variant="Вариант",
               sec_sweep="Лист вариантов", sec_rows="Строка {row} — {name} ({lump}, {w}×{h}, {kind})",
               sec_table="Измерения", sec_letter="Надписи: ни одной из шрифта",
               sec_scope="Объём", sec_reco="Чтение и рекомендация",
               sec_pal="Использованная палитра (утверждённая v1, не изменялась)", sec_ask="Вердикт",
               wall="стена", flat="плоскость", where="Где стоит",
               footer="Происхождение (a): процедурно, {script}, зерно {seed} + 10·строка + вариант. "
                      "Палитра docs/art/palette.json v1, ничего не добавлено. Шрифт не используется. "
                      "Лицензия: собственная работа, CC BY-NC-SA 4.0 (D15). Черновик: ничего из этого нет в assets/."),
}


def cell_id(row: str, vid: str) -> str:
    return f"{row}-{vid}"


def seed_of(row: str, vid: str) -> int:
    return BATCH_SEED + 10 * int(row[1:]) + VARIANT_IDS.index(vid) + 1


def sweep_grid(lang: str, files: dict) -> str:
    L = LABELS[lang]
    cell = 'style="border:1px solid #3a3d44;padding:8px;vertical-align:bottom;text-align:center"'
    head = f'<th {cell}></th>' + "".join(
        f'<th {cell}><b>{v}</b><br><span style="color:#9a9892;font-weight:400">'
        f'{html.escape(MATERIALS[v].en if lang == "en" else MATERIALS[v].ru)}</span></th>'
        for v in VARIANT_IDS)
    body = ""
    for p in PIECES:
        name = p.name_en if lang == "en" else p.name_ru
        th = cell.replace("text-align:center", "text-align:left")
        tds = (f'<th {th}><b>{p.row}</b><br>{html.escape(name)}<br>'
               f'<code>{p.lump}</code> {p.w}×{p.h} {L[p.kind]}</th>')
        for v in VARIANT_IDS:
            rec = ' outline:2px solid #c9a227;' if RECOMMENDED.get(p.row) == v else ""
            tds += (f'<td {cell[:-1]};{rec}">'
                    f'{sheetlib.img(files[(p.row, v, "piece")], 2, (p.w, p.h), cell_id(p.row, v))}'
                    f'<div style="font:600 13px Menlo,monospace;margin-top:4px">{cell_id(p.row, v)}</div></td>')
        body += f"<tr>{tds}</tr>"
    return f'<table style="border-collapse:collapse">{"<tr>" + head + "</tr>"}{body}</table>'


def detail_card(lang: str, p: Piece, vid: str, files: dict, m: dict) -> str:
    L = LABELS[lang]
    rec = RECOMMENDED.get(p.row) == vid
    mat = MATERIALS[vid].en if lang == "en" else MATERIALS[vid].ru
    head = (f'<div class="card{" rec" if rec else ""}">'
            + (f'<div class="tag">{L["recommended"]}</div>' if rec else "")
            + f'<h3>{cell_id(p.row, vid)}</h3><p class="desc">{html.escape(mat)}</p>')
    row1 = (sheetlib.view(L["at4"], files[(p.row, vid, "piece")], sheetlib.ZOOM, (p.w, p.h))
            + sheetlib.view(L["at1"], files[(p.row, vid, "piece")], 1, (p.w, p.h)))
    ctx, farv = "", ""
    for key, host, size in files[(p.row, vid, "contexts")]:
        label = L["plan"] if key == "plan" else f'{L["on"]} {host}'
        ctx += sheetlib.view(label, files[(p.row, vid, key)], 2, size)
        fsize = (size[0] // FAR_DIVISOR, size[1] // FAR_DIVISOR)
        farv += sheetlib.view(f'{label} — {L["far"]}', files[(p.row, vid, key + "_far")], sheetlib.FAR_ZOOM, fsize)
        farv += sheetlib.view(f'{label} — {L["dim"]}', files[(p.row, vid, key + "_dim")], sheetlib.FAR_ZOOM, fsize)
    dl = f'<dl><dt>{L["h_mean"]}</dt><dd>{m["mean_luma"]}</dd>'
    for hst, lab in (("SDCONC1", "h_conc"), ("SDSTEL1", "h_stel"), ("SDFLR2", "h_flr")):
        if f"gap_{hst}" in m:
            dl += f'<dt>{L[lab]}</dt><dd>{m[f"gap_{hst}"]}</dd>'
    dl += (f'<dt>{L["h_sigma"]}</dt><dd>{m["far_sigma"]}</dd>'
           f'<dt>{L["h_seed"]}</dt><dd>{seed_of(p.row, vid)}</dd></dl>')
    return (head + f'<div class="row">{row1}</div><div class="row">{ctx}</div>'
            f'<div class="row">{farv}</div>{dl}</div>')


def build_sheet(lang: str, files: dict, metrics: dict, stamp: str, reco: tuple[str, str]) -> Path:
    L = LABELS[lang]
    en = lang == "en"
    sections = [(L["sec_sweep"], LEAD_EN if en else LEAD_RU, sweep_grid(lang, files))]
    for p in PIECES:
        cards = "".join(detail_card(lang, p, v, files, metrics[(p.row, v)]) for v in VARIANT_IDS)
        where = p.where_en if en else p.where_ru
        lead = (f'<b>{L["where"]}:</b> {html.escape(where)}. '
                + (DETAIL_LEAD_EN if en else DETAIL_LEAD_RU).format(d=FAR_DIVISOR, f=DIM_FACTOR))
        title = L["sec_rows"].format(row=p.row, name=p.name_en if en else p.name_ru, lump=p.lump,
                                     w=p.w, h=p.h, kind=L[p.kind])
        sections.append((title, lead, f'<div class="grid">{cards}</div>'))
    rows = []
    for p in PIECES:
        for v in VARIANT_IDS:
            m = metrics[(p.row, v)]
            rows.append([cell_id(p.row, v), m["mean_luma"], m.get("gap_SDCONC1", "—"),
                         m.get("gap_SDSTEL1", "—"), m.get("gap_SDFLR2", "—"), m["worst_gap"], m["far_sigma"]])
    tbl = sheetlib.table([L["h_cell"], L["h_mean"], L["h_conc"], L["h_stel"], L["h_flr"],
                          L["h_worst"], L["h_sigma"]], rows)
    sections += [
        (L["sec_table"], "", tbl),
        (L["sec_reco"], "", f'<p class="lead">{reco[0] if en else reco[1]}</p>'),
        (L["sec_letter"], "", f'<p class="lead">{LETTERING_EN if en else LETTERING_RU}</p>'),
        (L["sec_scope"], "", f'<p class="lead">{SCOPE_EN if en else SCOPE_RU}</p>'),
        (L["sec_pal"], "", sheetlib.palette_ramps(load_palette())),
        (L["sec_ask"], "", f'<div class="ask">{ASK_EN if en else ASK_RU}</div>'),
    ]
    name = f"{stamp}_{SHEET_SLUG}.html"
    out = (SHEET_DIR / name) if en else (SHEET_DIR / "ru" / name)
    title = ("Soviet Doom — crates and lockers sweep, batch 3 (MAP01 A5)" if en else
             "Soviet Doom — лист ящиков и шкафчиков, партия 3 (MAP01 A5)")
    sub = ("F3 · 4 pieces × 4 variants · draft, nothing in assets/" if en else
           "F3 · 4 предмета × 4 варианта · черновик, в assets/ ничего нет")
    return sheetlib.write_sheet(out, lang=lang, title=title, subtitle=sub,
                                intro=INTRO_EN if en else INTRO_RU, sections=sections,
                                footer=L["footer"].format(script=SCRIPT_REL, seed=BATCH_SEED))


# ================================================================= main
def render_all() -> tuple[dict, dict]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files: dict = {}
    metrics: dict = {}
    for p in PIECES:
        for v in VARIANT_IDS:
            rgb = build(p.row, v)
            files[(p.row, v, "piece")] = save_rgb(OUT_DIR / f"{p.row}{v}_{p.lump}.png", rgb)
            # re-read the indexed file so contexts and metrics see the real palette pixels
            with Image.open(files[(p.row, v, "piece")]) as im:
                rgb = np.asarray(im.convert("RGB"), dtype=np.uint8)
            metrics[(p.row, v)] = measure(p.row, rgb)
            ctxs = []
            if p.kind == "flat":
                scenes = [("plan", "SDFLR2", plan(rgb), (PLAN_W, PLAN_H))]
            else:
                scenes = [(f"on_{wall}", wall, elevation(p.row, rgb, wall, floor), (ELEV_W, WALL_H + FLOOR_H))
                          for wall, floor in WALL_HOSTS[p.row]]
            for key, host, scene, size in scenes:
                files[(p.row, v, key)] = save_rgb(OUT_DIR / f"CTX_{p.row}{v}_{key}.png", scene)
                files[(p.row, v, key + "_far")] = save_plain(OUT_DIR / f"FAR_{p.row}{v}_{key}.png", far(scene))
                files[(p.row, v, key + "_dim")] = save_grey(OUT_DIR / f"DIM_{p.row}{v}_{key}.png", dim_value(scene))
                ctxs.append((key, host, size))
            files[(p.row, v, "contexts")] = ctxs
            m = metrics[(p.row, v)]
            print(f"{cell_id(p.row, v)}  mean {m['mean_luma']:6.1f}  worst gap {m['worst_gap']:5.1f}  "
                  f"far sigma {m['far_sigma']:5.1f}")
    return files, metrics


def contact(files: dict) -> Path:
    """One unlabelled PNG for the art director's single look (PIPELINE stage
    2): per cell, the scenes at 1x and the low-light value views at 4x.
    Rows R1..R4, within each the variants A..D; A,B on the left, C,D right."""
    pad = 6
    blocks = []
    for p in PIECES:
        cells = []
        for v in VARIANT_IDS:
            parts = []
            for key, _, _ in files[(p.row, v, "contexts")]:
                with Image.open(files[(p.row, v, key)]) as im:
                    parts.append(np.asarray(im.convert("RGB")))
                with Image.open(files[(p.row, v, key + "_dim")]) as im:
                    d = im.convert("RGB").resize((im.width * 4, im.height * 4), Image.Resampling.NEAREST)
                    parts.append(np.asarray(d))
            hmax = max(a.shape[0] for a in parts)
            row = []
            for a in parts:
                padded = np.full((hmax, a.shape[1] + pad, 3), 30, np.uint8)
                padded[:a.shape[0], :a.shape[1]] = a
                row.append(padded)
            cells.append(np.concatenate(row, axis=1))
        wmax = max(c.shape[1] for c in cells)

        def padw(a):
            out = np.full((a.shape[0] + pad, wmax, 3), 30, np.uint8)
            out[:a.shape[0], :a.shape[1]] = a
            return out
        left = np.concatenate([padw(cells[0]), padw(cells[1])], axis=0)
        right = np.concatenate([padw(cells[2]), padw(cells[3])], axis=0)
        blocks.append(np.concatenate([left, right], axis=1))
    wall = max(b.shape[1] for b in blocks)
    sheet = np.concatenate([np.pad(b, ((0, pad * 2), (0, wall - b.shape[1]), (0, 0)), constant_values=80)
                            for b in blocks], axis=0)
    path = OUT_DIR / "CONTACT_props_sweep.png"
    Image.fromarray(sheet, "RGB").save(path, optimize=True)
    return path


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--publish", action="store_true",
                    help="also copy the EN/RU sheets to docs/art/previews and docs/ru/art/previews")
    args = ap.parse_args(argv)

    files, metrics = render_all()
    cpath = contact(files)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    reco = (RECO_EN, RECO_RU)
    en = build_sheet("en", files, metrics, stamp, reco)
    ru = build_sheet("ru", files, metrics, stamp, reco)
    MANIFEST.write_text(json.dumps({
        "batch": 3, "phase": "F3", "item": "props (MAP01 request A5)", "script": SCRIPT_REL,
        "batch_seed": BATCH_SEED, "seed_rule": "BATCH_SEED + 10*row + variant(A=1..D=4)",
        "far_divisor": FAR_DIVISOR, "dim_factor": DIM_FACTOR, "recommended": RECOMMENDED,
        "pieces": {p.row: {"lump": p.lump, "kind": p.kind, "size": [p.w, p.h]} for p in PIECES},
        "cells": {cell_id(r, v): {"seed": seed_of(r, v), **m} for (r, v), m in metrics.items()},
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"contact: {cpath}\nsheet EN: {en}\nsheet RU: {ru}\nmanifest: {MANIFEST}")
    if args.publish:
        PUBLISH_EN.mkdir(parents=True, exist_ok=True)
        PUBLISH_RU.mkdir(parents=True, exist_ok=True)
        print("published:", shutil.copy2(en, PUBLISH_EN / en.name))
        print("published:", shutil.copy2(ru, PUBLISH_RU / ru.name))


if __name__ == "__main__":
    main()
