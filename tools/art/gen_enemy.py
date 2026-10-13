"""F5 — Fourth Reich rifleman, design sweep (front view, idle and fire).

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_enemy.py              (Windows)
    .venv/bin/python tools/art/gen_enemy.py                      (macOS)
    ... gen_enemy.py --stamp 2026-10-13_1900   fixes the sheet's timestamp

What this is. D35 (CEO, 2026-10-13): the five most-seen enemies are drawn
from scratch with their own identity; MAP01 opens on the Reich, so the
rifleman (`SD_ReichRifleman`, sprite `SDRR`, docs/engine/BESTIARY.md §3) is
the first one. Before ~50 images are drawn the CEO sees ONE decision: what
the man looks like. This script is that decision as a SWEEP (PIPELINE stage
2): six labelled variants, rotation 1 only (facing the player), in the idle
pose (`SDRRA1`) and the firing pose with its flash (`SDRRF1`). Nothing is
written to assets/.

The sweep's dimensions (one row of the table per cell):

        helmet     face          coat               weapon
    A   Stahlhelm  eyeless       calf-length        bolt rifle across the hips
    B   Stahlhelm  eyeless       calf-length        bolt rifle at port arms
    C   Stahlhelm  eyeless       short tunic,       submachine gun at the hip
                                 breeches, jackboots
    D   Stahlhelm  gas mask      calf-length        bolt rifle across the hips
    E   crested    eyeless       calf-length        bolt rifle across the hips
    F   crested    gas mask      short tunic        submachine gun at the hip

A is BESTIARY §3's brief taken literally; every other cell changes one or
two things from it, so a cell can be read against A.

How it is drawn. Claude does not draw freehand. The figure is built from
shapes (polygons, ellipses, capsules) on a 4x canvas; every shape carries a
MATERIAL (a slice of one palette ramp) and a SHADING model (flat, cylinder
along an axis, sphere), lit from the top left. The 4x canvas is reduced to
1x by majority vote per 4x4 block (no blending across shapes, so every
pixel is exactly one palette colour), then two pixel-art passes run at 1x:
a dark contour where a shape sits in front of another, and a darker rim on
the outside of the silhouette. The swastika armband (D12) is a hard 7x7
stamp placed after the reduction, because no reduction keeps a 5-px symbol.

Faction contract (ART-BIBLE §6, BESTIARY §2.1): body in `khaki_olive`,
shadow and leather in true black + `khaki_olive` 0-4, helmet `khaki_olive`
1-6. No `military_green` anywhere (the test checks it). The only saturated
colour is the armband (`flag_red` + `plaster_warm` + black). Weapon metal is
dark `concrete_cold`, stock wood dark `rust_brown`; the muzzle flash of frame
F is `cream_yellow`/`hazard_yellow`/white and lives one frame.

NO FONTS. The sprites carry no text. The sheet's labels are set in the mod's
own installed small font (`assets/fonts/defsmallfont/`, D24) through
gen_menu.FolderFont, so the sheet is byte-identical on the Mac and on
Windows (CLAUDE.md, "Text-bearing assets do not reproduce"). Nothing here
calls ImageFont or Overlay.text, and tests/test_gen_enemy.py keeps it so.

Outputs (work/ is gitignored):
    work/art/enemies/reich_rifleman/SDRR_<cell>_A1.png, _F1.png
        RGBA, hard alpha, every opaque pixel a palette.json colour, grAb
        offsets (centre, feet). RGBA like the fonts (ART-BIBLE §2 exception)
        because this is a draft; the shipped format is decided with the
        mod-engineer when a cell is approved.
    work/art/enemies/reich_rifleman/metrics.json
    docs/art/previews/<stamp>_F5_reich-rifleman-sweep.png   (the sheet)

Light model, shared with gen_props.py's DIM_FACTOR and just as rough:
a scene at sector light L is the RGB multiplied by L / LIGHT_FULL,
re-quantised to the palette. NOT VERIFIED against GZDoom's light tables;
it stands for "the sprite and the wall in the same sector light".
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from PIL.PngImagePlugin import PngInfo

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "reich_rifleman"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
SMALLFONT_DIR = PROJECT_ROOT / "assets" / "fonts" / "defsmallfont"
IWAD = PROJECT_ROOT / "iwads" / "freedoom2.wad"
HOST_FILES = {
    "SDCONC1": PROJECT_ROOT / "assets" / "textures" / "soviet_base" / "SDCONC1.png",
    "SDSTEL1": PROJECT_ROOT / "assets" / "textures" / "soviet_base" / "SDSTEL1.png",
    "SDCRAT1": PROJECT_ROOT / "assets" / "textures" / "soviet_base" / "SDCRAT1.png",
    "SDFLR2": PROJECT_ROOT / "assets" / "flats" / "soviet_base" / "SDFLR2.png",
}

SPRITE = "SDRR"                 # BESTIARY §3
SEED = 35                       # D35; the only randomness is the coat's grain
SS = 4                          # supersample: shapes are drawn at 4x
W, H = 48, 64                   # sprite canvas, multiples of 8 (ART-BIBLE §2)
CX = 24.0                       # body axis
FOOT_Y = 60.0                   # sole line; helmet top at y=4 -> 56 px tall
DOOM_HEIGHT = 56                # actor Height (BESTIARY §3) = sprite px at 1:1
FEET_SINK = 4                   # Doom sprites stand a few px into the floor
                                # (Freedoom POSSA1: 57 high, top offset 53)

# Lighting of the shapes: key light from the top left, a little from the front.
LIGHT = np.array([-0.55, -0.60, 0.58])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
VERTICAL_FALLOFF = 0.10         # lower body darker: light comes from above
CONTOUR_STEPS = 2               # internal contour: shape behind darkens 2 ramp steps
RIM_STEPS = 3                   # outside rim darkens 3 ramp steps
COVER_MIN = 7                   # of 16 sub-pixels: below this a 1x pixel is transparent

# Scenes: sector light of MAP01 v2 (docs/levels/MAP01-zarya-7.md §16.3).
LIGHT_FULL = 224                # L / 224: 112 -> x0.5, the gen_props DIM_FACTOR anchor
SCENES = (
    # key, wall, light, what it stands for
    ("S1", "SDCONC1", 128, "corridor Z3/Z5"),
    ("S2", "SDSTEL1", 176, "hangar dado"),
    ("S3", "SDSTEL1", 112, "fuel bay, worst case"),
    ("S4", "SDCRAT1", 144, "crate cover, bay shadow"),
)
FIRE_SCENE = ("S5", "SDSTEL1", 176, "hangar dado, firing")
SCENE_W, WALL_H, FLOOR_H = 64, 72, 24   # 1x scene: wall band over a floor band
FLOOR_LINE = WALL_H + 8                 # the feet stand 8 px into the floor band
FAR_DIVISOR = 4                 # game distance: 56 px -> 14 px (ART-BIBLE §6.4 is 16)
SILHOUETTE_H = 16               # ART-BIBLE §6.4


# ================================================================ materials
@dataclass(frozen=True)
class Material:
    ramp: str
    lo: int
    hi: int
    black_floor: bool = False   # index "-1" is true black (leather, voids)

    def colours(self) -> list[tuple[int, int, int]]:
        cols = artlib.ramp(self.ramp)[self.lo:self.hi + 1]
        return ([(0, 0, 0)] + cols) if self.black_floor else cols


MATERIALS: dict[str, Material] = {
    "coat": Material("khaki_olive", 1, 9),
    "coat_dark": Material("khaki_olive", 0, 6),
    "helmet": Material("khaki_olive", 1, 7),
    "crest": Material("khaki_olive", 2, 9),
    "leather": Material("khaki_olive", 0, 4, black_floor=True),
    "void": Material("khaki_olive", 0, 1, black_floor=True),
    "flesh": Material("khaki_olive", 6, 13),
    "mask": Material("khaki_olive", 1, 6, black_floor=True),
    "button": Material("khaki_olive", 9, 12),
    "metal": Material("concrete_cold", 2, 12, black_floor=True),
    "wood": Material("rust_brown", 2, 8),
    "flash_out": Material("hazard_yellow", 9, 15),
    "flash_in": Material("cream_yellow", 12, 15),
    "flash_core": Material("cream_yellow", 15, 15),
}
MATERIAL_IDS = {name: i for i, name in enumerate(MATERIALS)}
FLAT_MATERIALS = {"flash_out", "flash_in", "flash_core", "button"}  # no contour, no rim

# The armband (D12). 7x7, hard pixels: R flag_red, W plaster_warm, K black.
# The 5x5 symbol is the smallest grid on which the hooked cross is drawn
# without ambiguity; at this scale it is about twice a real armband, on
# purpose (accent exclusivity, ART-BIBLE §6.3, needs it to read).
ARMBAND = (
    "RRRRRRR",
    "RK.KKKR",
    "RK.K..R",
    "RKKKKKR",
    "R..K.KR",
    "RKKK.KR",
    "RRRRRRR",
)
ARMBAND_COLOURS = {
    "R": ("flag_red", 11), "r": ("flag_red", 7),
    "K": None, ".": ("plaster_warm", 13),
}


# ================================================================== painter
class Painter:
    """A 4x canvas of material ids, values (ramp position 0..1) and shape
    ids. Later shapes cover earlier ones; nothing is blended."""

    def __init__(self, w: int = W, h: int = H, ss: int = SS):
        self.w, self.h, self.ss = w, h, ss
        self.mat = np.full((h * ss, w * ss), -1, np.int16)
        self.val = np.zeros((h * ss, w * ss), np.float64)
        self.shape = np.zeros((h * ss, w * ss), np.int16)
        self.flat = np.zeros((h * ss, w * ss), bool)
        yy, xx = np.mgrid[0:h * ss, 0:w * ss]
        self.X = (xx + 0.5) / ss
        self.Y = (yy + 0.5) / ss
        self.count = 0

    # --- masks (coordinates in sprite pixels, floats)
    def _canvas(self):
        img = Image.new("L", (self.w * self.ss, self.h * self.ss), 0)
        return img, ImageDraw.Draw(img)

    def poly_mask(self, pts) -> np.ndarray:
        img, d = self._canvas()
        d.polygon([(x * self.ss, y * self.ss) for x, y in pts], fill=255)
        return np.asarray(img) > 0

    def ellipse_mask(self, cx, cy, rx, ry) -> np.ndarray:
        return ((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2 <= 1.0

    def capsule_mask(self, p0, p1, r0, r1=None) -> np.ndarray:
        """Tapered capsule from p0 (radius r0) to p1 (radius r1)."""
        r1 = r0 if r1 is None else r1
        ax, ay = p1[0] - p0[0], p1[1] - p0[1]
        L2 = max(ax * ax + ay * ay, 1e-9)
        t = np.clip(((self.X - p0[0]) * ax + (self.Y - p0[1]) * ay) / L2, 0, 1)
        dx = self.X - (p0[0] + t * ax)
        dy = self.Y - (p0[1] + t * ay)
        return dx * dx + dy * dy <= (r0 + (r1 - r0) * t) ** 2

    # --- shading fields, each returns a value offset in about -0.5..+0.4
    def cyl(self, p0, p1, r) -> np.ndarray:
        ax, ay = p1[0] - p0[0], p1[1] - p0[1]
        n = np.hypot(ax, ay) or 1.0
        nx, ny = ay / n, -ax / n          # perpendicular
        if nx < 0:
            nx, ny = -nx, -ny             # points to the viewer's right
        u = np.clip(((self.X - p0[0]) * nx + (self.Y - p0[1]) * ny) / r, -1, 1)
        z = np.sqrt(np.clip(1 - u * u, 0, 1))
        lam = LIGHT[0] * u * nx + LIGHT[1] * u * ny + LIGHT[2] * z
        return 0.55 * (lam - 0.55)

    def sph(self, cx, cy, rx, ry) -> np.ndarray:
        u = np.clip((self.X - cx) / rx, -1, 1)
        v = np.clip((self.Y - cy) / ry, -1, 1)
        z = np.sqrt(np.clip(1 - u * u - v * v, 0, 1))
        lam = LIGHT[0] * u + LIGHT[1] * v + LIGHT[2] * z
        return 0.6 * (lam - 0.5)

    def paint(self, mask, material: str, base: float, shading=0.0) -> None:
        self.count += 1
        m = np.asarray(mask, bool)
        sh = shading if np.isscalar(shading) else np.asarray(shading)[m]
        self.mat[m] = MATERIAL_IDS[material]
        self.val[m] = np.clip(base + sh - VERTICAL_FALLOFF * (self.Y[m] / self.h - 0.5), 0, 1)
        self.shape[m] = self.count
        self.flat[m] = material in FLAT_MATERIALS

    # --- reduction to 1x
    def reduce(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Majority vote per ss x ss block. Returns (material id or -1,
        value, shape id, flat flag) at 1x."""
        ss, h, w = self.ss, self.h, self.w
        blk = lambda a: a.reshape(h, ss, w, ss).transpose(0, 2, 1, 3).reshape(h, w, ss * ss)
        shp, val, mat, flat = blk(self.shape), blk(self.val), blk(self.mat), blk(self.flat)
        out_m = np.full((h, w), -1, np.int16)
        out_v = np.zeros((h, w))
        out_s = np.zeros((h, w), np.int16)
        out_f = np.zeros((h, w), bool)
        covered = (shp > 0).sum(-1)
        for y, x in zip(*np.nonzero(covered >= COVER_MIN)):
            s = shp[y, x]
            ids, counts = np.unique(s[s > 0], return_counts=True)
            # ties go to the shape drawn last (the one in front)
            win = ids[np.lexsort((ids, counts))[-1]]
            sel = s == win
            out_s[y, x] = win
            out_m[y, x] = mat[y, x][sel][0]
            out_v[y, x] = val[y, x][sel].mean()
            out_f[y, x] = flat[y, x][sel][0]
        return out_m, out_v, out_s, out_f


def to_rgba(mat: np.ndarray, val: np.ndarray, shape: np.ndarray, flat: np.ndarray) -> np.ndarray:
    """Material + value -> palette RGBA, with the contour and rim passes."""
    h, w = mat.shape
    names = list(MATERIALS)
    idx = np.zeros((h, w), np.int16)
    for i, name in enumerate(names):
        n = len(MATERIALS[name].colours())
        sel = mat == i
        idx[sel] = np.rint(val[sel] * (n - 1)).astype(np.int16)
    opaque = mat >= 0
    dark = np.zeros((h, w), np.int16)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nb_shape = np.roll(np.roll(shape, dy, 0), dx, 1)
        nb_op = np.roll(np.roll(opaque, dy, 0), dx, 1)
        nb_flat = np.roll(np.roll(flat, dy, 0), dx, 1)
        # rolled-in borders count as outside
        if dy == -1: nb_op[-1, :] = False
        if dy == 1: nb_op[0, :] = False
        if dx == -1: nb_op[:, -1] = False
        if dx == 1: nb_op[:, 0] = False
        behind = opaque & nb_op & (nb_shape > shape) & ~nb_flat & ~flat
        dark = np.where(behind, np.maximum(dark, CONTOUR_STEPS), dark)
        rim = opaque & ~nb_op & ~flat
        dark = np.where(rim, np.maximum(dark, RIM_STEPS), dark)
    idx = np.maximum(idx - dark, 0)
    rgba = np.zeros((h, w, 4), np.uint8)
    for i, name in enumerate(names):
        cols = np.array(MATERIALS[name].colours(), np.uint8)
        sel = mat == i
        rgba[sel, :3] = cols[np.clip(idx[sel], 0, len(cols) - 1)]
    rgba[opaque, 3] = 255
    return rgba


def stamp_armband(rgba: np.ndarray, x0: int, y0: int) -> None:
    for j, row in enumerate(ARMBAND):
        for i, ch in enumerate(row):
            spec = ARMBAND_COLOURS[ch]
            col = (0, 0, 0) if spec is None else artlib.ramp(spec[0])[spec[1]]
            # the right column of the band sits in the arm's shade
            if ch == "R" and i == len(row) - 1:
                col = artlib.ramp("flag_red")[7]
            rgba[y0 + j, x0 + i] = (*col, 255)


# =================================================================== design
@dataclass(frozen=True)
class Cell:
    key: str
    helmet: str        # "stahl" | "crest"
    face: str          # "bare" | "mask"
    coat: str          # "long" | "short"
    weapon: str        # "rifle_hip" | "rifle_port" | "smg"
    title: str


CELLS = (
    Cell("A", "stahl", "bare", "long", "rifle_hip", "Brief: Stahlhelm, greatcoat, rifle across hips"),
    Cell("B", "stahl", "bare", "long", "rifle_port", "As A, rifle at port arms"),
    Cell("C", "stahl", "bare", "short", "smg", "Tunic, breeches, jackboots, SMG"),
    Cell("D", "stahl", "mask", "long", "rifle_hip", "As A, gas mask"),
    Cell("E", "crest", "bare", "long", "rifle_hip", "As A, crested alien helmet"),
    Cell("F", "crest", "mask", "short", "smg", "Crested helmet, gas mask, tunic, SMG"),
)
CELL = {c.key: c for c in CELLS}

SHOULDER_L, SHOULDER_R = (17.6, 19.6), (30.4, 19.6)
ARM_R = 2.7                      # coat sleeve radius
HAND_R = 1.5

# Arm poses (viewer's left arm = the figure's right): shoulder, elbow, hand.
ARMS = {
    ("rifle_hip", "idle"): ((SHOULDER_L, (15.0, 27.0), (17.6, 33.0)),
                            (SHOULDER_R, (33.4, 27.0), (31.6, 33.6))),
    ("rifle_port", "idle"): ((SHOULDER_L, (15.2, 28.0), (19.0, 35.0)),
                             (SHOULDER_R, (32.6, 25.8), (27.4, 24.4))),
    ("smg", "idle"): ((SHOULDER_L, (15.4, 27.2), (19.8, 34.4)),
                      (SHOULDER_R, (33.0, 27.2), (28.2, 34.6))),
    ("rifle", "fire"): ((SHOULDER_L, (12.6, 23.4), (19.8, 22.6)),
                        (SHOULDER_R, (30.6, 27.6), (23.6, 25.6))),
    ("smg", "fire"): ((SHOULDER_L, (15.8, 27.4), (21.0, 32.6)),
                      (SHOULDER_R, (32.4, 27.4), (26.8, 32.4))),
}


def arm_pose(cell: Cell, pose: str):
    if pose == "fire":
        return ARMS[("smg" if cell.weapon == "smg" else "rifle", "fire")]
    return ARMS[(cell.weapon, "idle")]


def draw_legs(p: Painter, cell: Cell, pose: str) -> None:
    spread = 0.8 if pose == "fire" else 0.0
    if cell.coat == "long":
        for sx in (-1, 1):
            x0 = CX + sx * (3.6 + spread)
            p.paint(p.poly_mask([(x0 - 2.3, 47.0), (x0 + 2.3, 47.0), (x0 + 2.2, FOOT_Y - 1.2),
                                 (x0 - 2.4, FOOT_Y - 1.2)]),
                    "leather", 0.55, p.cyl((x0, 47), (x0, FOOT_Y), 2.4))
            p.paint(p.poly_mask([(x0 - 2.7, FOOT_Y - 1.6), (x0 + 2.6, FOOT_Y - 1.6),
                                 (x0 + 2.8, FOOT_Y + 0.4), (x0 - 2.9, FOOT_Y + 0.4)]), "leather", 0.15)
    else:
        for sx in (-1, 1):
            x0 = CX + sx * (3.7 + spread)
            # breeches: the jodhpur flare is the shape that says "1940s" at 16 px
            p.paint(p.poly_mask([(CX + sx * 0.4, 36.4), (x0 + sx * 3.9, 37.0), (x0 + sx * 4.4, 40.5),
                                 (x0 + sx * 2.4, 45.6), (x0 - sx * 1.9, 45.6), (CX + sx * 0.2, 40.0)]),
                    "coat", 0.40, p.cyl((x0, 36), (x0, 46), 3.8))
            p.paint(p.poly_mask([(x0 - 2.5, 44.6), (x0 + 2.5, 44.6), (x0 + 2.2, FOOT_Y - 1.2),
                                 (x0 - 2.3, FOOT_Y - 1.2)]),
                    "leather", 0.7, p.cyl((x0, 44), (x0, FOOT_Y), 2.5))
            p.paint(p.poly_mask([(x0 - 2.7, FOOT_Y - 1.6), (x0 + 2.6, FOOT_Y - 1.6),
                                 (x0 + 2.8, FOOT_Y + 0.4), (x0 - 2.9, FOOT_Y + 0.4)]), "leather", 0.15)


def draw_torso(p: Painter, cell: Cell, rng: np.random.Generator) -> None:
    body_axis = ((CX, 18), (CX, 50))
    grain = rng.normal(0, 0.035, (p.h * p.ss, p.w * p.ss))
    if cell.coat == "long":
        coat = p.poly_mask([(18.0, 18.4), (30.0, 18.4), (32.0, 20.4), (31.2, 30.6), (32.4, 39.0),
                            (33.8, 48.6), (24.0, 49.6), (14.2, 48.6), (15.6, 39.0), (16.8, 30.6),
                            (16.0, 20.4)])
        p.paint(coat, "coat", 0.48, p.cyl(*body_axis, 9.0) + grain)
        # front opening below the belt, and the shade between the legs
        p.paint(p.poly_mask([(23.7, 32.2), (24.3, 32.2), (24.6, 49.4), (23.4, 49.4)]), "coat_dark", 0.25)
        p.paint(p.poly_mask([(24.6, 40.0), (25.6, 40.0), (26.6, 49.0), (24.8, 49.0)]), "coat_dark", 0.45)
        buttons_y = (21.5, 24.5, 27.5, 35.0, 38.5)
    else:
        coat = p.poly_mask([(18.0, 18.4), (30.0, 18.4), (32.0, 20.4), (31.2, 30.6), (32.0, 37.6),
                            (24.0, 38.2), (16.0, 37.6), (16.8, 30.6), (16.0, 20.4)])
        p.paint(coat, "coat", 0.48, p.cyl(*body_axis, 9.0) + grain)
        p.paint(p.poly_mask([(23.7, 32.2), (24.3, 32.2), (24.4, 38.0), (23.6, 38.0)]), "coat_dark", 0.25)
        buttons_y = (21.5, 24.5, 27.5, 35.0)
    # raised greatcoat collar
    p.paint(p.poly_mask([(19.4, 16.4), (28.6, 16.4), (30.6, 19.4), (24.0, 21.4), (17.4, 19.4)]),
            "coat", 0.42, p.cyl((CX, 16), (CX, 21), 6.0))
    for y in buttons_y:
        for x in (21.6, 26.4):
            p.paint(p.ellipse_mask(x, y, 0.55, 0.55), "button", 0.35)
    # Y-straps and belt (black leather: the "black undercoat" of BESTIARY §10.1)
    p.paint(p.capsule_mask((20.0, 19.0), (21.8, 30.8), 0.6), "leather", 0.4)
    p.paint(p.capsule_mask((28.0, 19.0), (26.2, 30.8), 0.6), "leather", 0.4)
    p.paint(p.poly_mask([(16.7, 30.4), (31.3, 30.4), (31.4, 32.6), (16.6, 32.6)]), "leather", 0.45,
            p.cyl(*body_axis, 8.0))
    p.paint(p.poly_mask([(23.0, 30.5), (25.0, 30.5), (25.0, 32.5), (23.0, 32.5)]), "metal", 0.55)
    for x0 in (18.2, 27.2):         # ammunition pouches
        p.paint(p.poly_mask([(x0, 32.4), (x0 + 2.6, 32.4), (x0 + 2.5, 35.2), (x0 + 0.1, 35.2)]),
                "leather", 0.5)


def draw_head(p: Painter, cell: Cell, dx: float = 0.0) -> None:
    hx = CX + dx
    # neck in the collar's shadow
    p.paint(p.poly_mask([(hx - 1.7, 14.6), (hx + 1.7, 14.6), (hx + 1.6, 17.4), (hx - 1.6, 17.4)]),
            "flesh", 0.15)
    if cell.face == "bare":
        # gaunt, eyeless: the brim's shadow is where eyes should be
        p.paint(p.poly_mask([(hx - 3.4, 10.6), (hx + 3.4, 10.6), (hx + 3.2, 14.0), (hx + 1.6, 16.6),
                             (hx - 1.6, 16.6), (hx - 3.2, 14.0)]),
                "flesh", 0.55, p.sph(hx, 13.2, 3.6, 4.0))
        p.paint(p.poly_mask([(hx - 3.0, 10.6), (hx + 3.0, 10.6), (hx + 2.8, 12.9), (hx + 0.5, 12.4),
                             (hx - 0.5, 12.4), (hx - 2.8, 12.9)]), "void", 0.0)
        p.paint(p.poly_mask([(hx + 1.4, 13.4), (hx + 3.0, 13.4), (hx + 2.4, 15.4), (hx + 1.6, 15.2)]),
                "flesh", 0.2)       # hollow cheek on the shaded side
        p.paint(p.poly_mask([(hx - 1.3, 15.0), (hx + 1.3, 15.0), (hx + 1.2, 15.7), (hx - 1.2, 15.7)]),
                "void", 0.4)
    else:
        # gas mask: two dead lenses and a filter snout
        p.paint(p.poly_mask([(hx - 3.6, 10.6), (hx + 3.6, 10.6), (hx + 3.4, 14.6), (hx + 1.9, 17.2),
                             (hx - 1.9, 17.2), (hx - 3.4, 14.6)]),
                "mask", 0.55, p.sph(hx, 13.4, 3.8, 4.2))
        for sx in (-1, 1):
            p.paint(p.ellipse_mask(hx + sx * 1.75, 12.6, 1.25, 1.15), "void", 0.0)
        p.paint(p.ellipse_mask(hx - 2.05, 12.3, 0.35, 0.35), "metal", 0.75)  # one dull glint
        p.paint(p.ellipse_mask(hx, 15.9, 1.55, 1.35), "metal", 0.35, p.sph(hx, 15.9, 1.6, 1.4))
        p.paint(p.ellipse_mask(hx, 16.0, 0.6, 0.5), "void", 0.0)
    if cell.helmet == "stahl":
        # M35 seen from the front: dome, low front brim, side skirts flaring
        # out over the ears. The flare is BESTIARY §3's 16-px tell.
        dome = p.ellipse_mask(hx, 9.4, 5.3, 5.4) & (p.Y <= 11.0)
        p.paint(dome, "helmet", 0.55, p.sph(hx, 8.6, 5.3, 5.2))
        for sx in (-1, 1):
            p.paint(p.poly_mask([(hx + sx * 3.6, 9.0), (hx + sx * 5.4, 9.2), (hx + sx * 6.8, 14.4),
                                 (hx + sx * 4.4, 14.0), (hx + sx * 3.4, 11.4)]),
                    "helmet", 0.42 if sx < 0 else 0.22)
        p.paint(p.poly_mask([(hx - 4.6, 10.2), (hx + 4.6, 10.2), (hx + 4.2, 11.4), (hx - 4.2, 11.4)]),
                "helmet", 0.38, p.cyl((hx, 10), (hx, 12), 1.0))
    else:
        # the crested helmet: a taller ogive with a ridge, its skirt swept
        # down into two blades framing the jaw. "Alien Reich", not a costume.
        dome = p.poly_mask([(hx, 2.2), (hx + 2.6, 3.6), (hx + 5.0, 7.4), (hx + 5.6, 11.0),
                            (hx - 5.6, 11.0), (hx - 5.0, 7.4), (hx - 2.6, 3.6)])
        p.paint(dome, "helmet", 0.55, p.sph(hx, 8.0, 5.6, 6.2))
        p.paint(p.poly_mask([(hx - 0.6, 2.6), (hx + 0.6, 2.6), (hx + 0.7, 10.6), (hx - 0.7, 10.6)]),
                "crest", 0.75, p.cyl((hx, 2), (hx, 11), 0.7))
        for sx in (-1, 1):
            p.paint(p.poly_mask([(hx + sx * 4.2, 8.6), (hx + sx * 5.8, 9.2), (hx + sx * 7.4, 17.6),
                                 (hx + sx * 4.6, 14.2), (hx + sx * 3.6, 11.6)]),
                    "helmet", 0.40 if sx < 0 else 0.20)
        p.paint(p.poly_mask([(hx - 4.8, 10.4), (hx + 4.8, 10.4), (hx + 4.2, 11.8), (hx, 12.6),
                             (hx - 4.2, 11.8)]), "helmet", 0.30, p.cyl((hx, 10), (hx, 12.6), 1.2))


def draw_arm(p: Painter, arm, upper_only: bool = False, forearm_only: bool = False) -> None:
    sh, el, ha = arm
    if not forearm_only:
        p.paint(p.capsule_mask(sh, el, ARM_R, ARM_R * 0.9), "coat", 0.5, p.cyl(sh, el, ARM_R))
    if not upper_only:
        p.paint(p.capsule_mask(el, ha, ARM_R * 0.9, ARM_R * 0.75), "coat", 0.46,
                p.cyl(el, ha, ARM_R * 0.9))


def draw_hand(p: Painter, arm) -> None:
    hx, hy = arm[2]
    p.paint(p.ellipse_mask(hx, hy, HAND_R, HAND_R * 1.1), "flesh", 0.4, p.sph(hx, hy, HAND_R, HAND_R))


def draw_rifle_horizontal(p: Painter) -> None:
    """Bolt rifle across the hips, butt behind the right hip (viewer's left),
    muzzle past the left elbow: BESTIARY §3's 'horizontal bar at waist'."""
    y = 33.4
    p.paint(p.poly_mask([(11.2, y - 1.6), (17.0, y - 0.8), (17.0, y + 1.0), (11.4, y + 2.4)]), "wood", 0.5,
            p.cyl((11, y), (17, y), 1.8))
    p.paint(p.poly_mask([(17.0, y - 0.8), (34.0, y - 0.6), (34.0, y + 0.9), (17.0, y + 1.0)]), "wood", 0.55,
            p.cyl((17, y), (34, y), 0.9))
    p.paint(p.poly_mask([(19.0, y - 1.4), (42.6, y - 1.0), (42.6, y - 0.2), (19.0, y - 0.3)]), "metal", 0.45)
    p.paint(p.ellipse_mask(21.2, y - 2.2, 0.8, 0.8), "metal", 0.6)          # bolt knob
    p.paint(p.poly_mask([(42.0, y - 1.9), (42.8, y - 1.9), (42.8, y - 0.9), (42.0, y - 0.9)]), "metal", 0.4)


def draw_rifle_port(p: Painter) -> None:
    """Port arms: diagonal across the chest, muzzle over the left shoulder."""
    a, b = (15.0, 41.0), (37.0, 6.0)
    def at(t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    p.paint(p.capsule_mask(at(0.0), at(0.22), 1.9, 1.0), "wood", 0.5, p.cyl(at(0), at(0.22), 1.9))
    p.paint(p.capsule_mask(at(0.2), at(0.72), 1.0), "wood", 0.55, p.cyl(at(0.2), at(0.72), 1.0))
    p.paint(p.capsule_mask(at(0.3), at(1.0), 0.55), "metal", 0.5)
    bx, by = at(0.33)
    p.paint(p.ellipse_mask(bx + 1.6, by + 0.4, 0.8, 0.8), "metal", 0.6)


def draw_smg_horizontal(p: Painter) -> None:
    y = 33.2
    p.paint(p.poly_mask([(13.6, y - 0.4), (19.0, y - 0.4), (19.0, y + 0.3), (13.6, y + 0.3)]), "metal", 0.35)
    p.paint(p.poly_mask([(13.2, y - 1.2), (14.2, y - 1.2), (14.2, y + 1.2), (13.2, y + 1.2)]), "metal", 0.3)
    p.paint(p.poly_mask([(18.6, y - 1.3), (33.6, y - 1.0), (33.6, y + 0.7), (18.6, y + 1.1)]), "metal", 0.45,
            p.cyl((18, y), (34, y), 1.2))
    p.paint(p.poly_mask([(33.4, y - 0.5), (37.6, y - 0.4), (37.6, y + 0.3), (33.4, y + 0.3)]), "metal", 0.4)
    p.paint(p.poly_mask([(26.9, y + 0.8), (28.7, y + 0.8), (28.9, y + 7.0), (27.1, y + 7.0)]), "metal", 0.3)
    p.paint(p.poly_mask([(19.2, y + 0.8), (20.8, y + 0.8), (20.6, y + 3.6), (19.0, y + 3.6)]), "leather", 0.4)


def draw_rifle_aimed(p: Painter, head_dx: float) -> tuple[float, float]:
    """Shouldered and pointed at the player: the rifle is foreshortened to
    its fore-end and muzzle, under the cheek. Returns the muzzle."""
    mx, my = CX - 3.0 + head_dx, 22.0
    p.paint(p.poly_mask([(mx - 2.4, my - 1.4), (mx + 2.0, my - 1.6), (mx + 2.6, my + 3.6),
                         (mx - 1.6, my + 4.0)]), "wood", 0.45, p.cyl((mx, my - 2), (mx, my + 4), 2.4))
    p.paint(p.ellipse_mask(mx, my, 1.25, 1.25), "metal", 0.55, p.sph(mx, my, 1.3, 1.3))
    p.paint(p.ellipse_mask(mx, my, 0.55, 0.55), "void", 0.0)
    return mx, my


def draw_smg_aimed(p: Painter) -> tuple[float, float]:
    mx, my = CX - 0.4, 31.0
    p.paint(p.poly_mask([(mx - 2.6, my - 1.6), (mx + 2.6, my - 1.6), (mx + 2.8, my + 2.0),
                         (mx - 2.8, my + 2.0)]), "metal", 0.35, p.sph(mx, my, 2.8, 2.0))
    p.paint(p.poly_mask([(mx - 0.8, my + 1.8), (mx + 0.8, my + 1.8), (mx + 0.9, my + 7.6),
                         (mx - 0.7, my + 7.6)]), "metal", 0.3)          # magazine, seen end-on
    p.paint(p.ellipse_mask(mx, my, 1.0, 1.0), "metal", 0.6)
    p.paint(p.ellipse_mask(mx, my, 0.45, 0.45), "void", 0.0)
    return mx, my


def draw_flash(p: Painter, mx: float, my: float, size: float) -> None:
    """Frame F's muzzle flash: a hard, eight-point burst (Doom's own grammar)."""
    def burst(r_out, r_in, rot):
        pts = []
        for i in range(16):
            ang = np.deg2rad(rot + i * 22.5)
            r = r_out if i % 2 == 0 else r_in
            pts.append((mx + r * np.cos(ang), my + r * np.sin(ang)))
        return pts
    p.paint(p.poly_mask(burst(size, size * 0.42, 11.0)), "flash_out", 0.5)
    p.paint(p.poly_mask(burst(size * 0.62, size * 0.32, 0.0)), "flash_in", 0.5)
    p.paint(p.ellipse_mask(mx, my, size * 0.22, size * 0.22), "flash_core", 1.0)


def armband_anchor(arm) -> tuple[int, int]:
    """Top-left of the 7x7 stamp: on the upper arm, just under the shoulder."""
    sh, el, _ = arm
    t = 0.45
    x = sh[0] + (el[0] - sh[0]) * t
    y = sh[1] + (el[1] - sh[1]) * t
    return int(round(x - 3.5)), int(round(y - 3.5))


def render(cell: Cell, pose: str) -> np.ndarray:
    """One sprite, RGBA (h, w, 4)."""
    rng = np.random.default_rng(SEED)
    p = Painter()
    arm_l, arm_r = arm_pose(cell, pose)
    draw_legs(p, cell, pose)
    draw_torso(p, cell, rng)
    head_dx = -0.8 if (pose == "fire" and cell.weapon != "smg") else 0.0
    muzzle = None
    if pose == "idle":
        draw_head(p, cell)
        if cell.weapon == "rifle_port":
            draw_arm(p, arm_l)
            draw_arm(p, arm_r)
            draw_rifle_port(p)
        else:
            draw_arm(p, arm_l)
            draw_arm(p, arm_r)
            (draw_smg_horizontal if cell.weapon == "smg" else draw_rifle_horizontal)(p)
    else:
        if cell.weapon == "smg":
            draw_head(p, cell)
            draw_arm(p, arm_l)
            draw_arm(p, arm_r)
            muzzle = draw_smg_aimed(p)
        else:
            draw_arm(p, arm_r, upper_only=True)
            draw_arm(p, arm_l)            # raised, elbow out
            draw_head(p, cell, head_dx)
            muzzle = draw_rifle_aimed(p, head_dx)
            draw_arm(p, arm_r, forearm_only=True)   # support arm across the chest
    draw_hand(p, arm_l)
    draw_hand(p, arm_r)
    if muzzle is not None:
        draw_flash(p, *muzzle, size=5.2 if cell.weapon == "smg" else 6.0)
    rgba = to_rgba(*p.reduce())
    x0, y0 = armband_anchor(arm_r)
    stamp_armband(rgba, x0, y0)
    return rgba


# ================================================================== output
def grab_offsets(rgba: np.ndarray) -> tuple[int, int]:
    """Doom offsets: x = horizontal centre, y = how far the sprite reaches
    above the floor (the soles sink FEET_SINK px into it, like Freedoom's)."""
    return W // 2, int(FOOT_Y) - FEET_SINK


def save_sprite(rgba: np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    gx, gy = grab_offsets(rgba)
    info.add(b"grAb", struct.pack(">ii", gx, gy))
    Image.fromarray(rgba, "RGBA").save(path, pnginfo=info, optimize=True)
    return path


def luma(rgb: np.ndarray) -> np.ndarray:
    a = rgb.astype(np.float64)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def host_rgb(name: str) -> np.ndarray:
    with Image.open(HOST_FILES[name]) as im:
        return np.asarray(im.convert("RGB"), dtype=np.uint8)


def tile_to(rgb: np.ndarray, w: int, h: int) -> np.ndarray:
    hh, hw = rgb.shape[:2]
    return np.tile(rgb, (-(-h // hh), -(-w // hw), 1))[:h, :w]


def lit(rgb: np.ndarray, light: int) -> np.ndarray:
    """Sector light stand-in (module docstring), re-quantised to the palette."""
    f = min(1.0, light / LIGHT_FULL)
    out = np.clip(rgb.astype(np.float64) * f, 0, 255).astype(np.uint8)
    return np.asarray(artlib.quantize(Image.fromarray(out, "RGB")).convert("RGB"))


def scene(sprite: np.ndarray, wall: str, light: int) -> np.ndarray:
    """The figure standing in front of a wall, on SDFLR2, both in the same
    sector light. The floor band is the flat foreshortened 3:1."""
    w_rgb = tile_to(host_rgb(wall), SCENE_W, WALL_H)
    fl = tile_to(host_rgb("SDFLR2"), SCENE_W, FLOOR_H * 3)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((SCENE_W, FLOOR_H), Image.Resampling.NEAREST))
    canvas = np.concatenate([w_rgb, fl], axis=0).copy()
    x0 = (SCENE_W - W) // 2
    y0 = FLOOR_LINE - int(FOOT_Y)
    a = sprite[..., 3] > 0
    region = canvas[y0:y0 + H, x0:x0 + W]
    region[a] = sprite[..., :3][a]
    return lit(canvas, light)


def far(rgb: np.ndarray, divisor: int = FAR_DIVISOR) -> np.ndarray:
    h, w = rgb.shape[:2]
    return np.asarray(Image.fromarray(rgb, "RGB").resize((w // divisor, h // divisor),
                                                         Image.Resampling.NEAREST))


def silhouette(sprite: np.ndarray, height: int = SILHOUETTE_H) -> np.ndarray:
    """ART-BIBLE §6.4: the figure as a black shape `height` px tall."""
    a = sprite[..., 3] > 0
    ys, xs = np.nonzero(a)
    crop = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    ch, cw = crop.shape
    nw = max(1, int(round(cw * height / ch)))
    small = Image.fromarray((crop * 255).astype(np.uint8), "L").resize((nw, height), Image.Resampling.BOX)
    return np.asarray(small) >= 128


def measure(sprite: np.ndarray) -> dict:
    """Numbers quoted on the sheet. Body luma is the mean over every opaque
    pixel except the armband and the flash; gap_<scene> is |body - wall|
    under that scene's light (both through the same light stand-in)."""
    a = sprite[..., 3] > 0
    ys, xs = np.nonzero(a)
    body = luma(sprite[..., :3])[a]
    out = {"height_px": int(ys.max() - ys.min() + 1), "width_px": int(xs.max() - xs.min() + 1),
           "body_luma": round(float(body.mean()), 1)}
    f = lambda L: min(1.0, L / LIGHT_FULL)
    for key, wall, light, _ in SCENES:
        out[f"gap_{key}"] = round(abs(float(body.mean()) * f(light) - float(luma(host_rgb(wall)).mean()) * f(light)), 1)
    out["worst_gap"] = min(out[f"gap_{k}"] for k, *_ in SCENES)
    return out


# ==================================================================== sheet
class Text:
    """Labels in the mod's own small font (D24), scaled 2x nearest."""

    def __init__(self, scale: int = 2):
        from gen_menu import FolderFont
        self.font = FolderFont(SMALLFONT_DIR)
        self.scale = scale

    def render(self, text: str, colour) -> Image.Image:
        img = self.font.render(text, colour, (0, 0, 0))
        return img.resize((img.width * self.scale, img.height * self.scale), Image.Resampling.NEAREST)

    def line_h(self) -> int:
        return 7 * self.scale + 4

    def width(self, text: str) -> int:
        return self.font.width(text) * self.scale

    def put(self, sheet: Image.Image, xy, text: str, colour) -> int:
        img = self.render(text, colour)
        sheet.alpha_composite(img, (int(xy[0]), int(xy[1])))
        return img.width

    def para(self, sheet: Image.Image, xy, text: str, colour, max_w: int) -> int:
        """Word-wrapped paragraph; returns the y below it."""
        x, y = xy
        line = ""
        for word in text.split():
            trial = (line + " " + word).strip()
            if self.width(trial) > max_w and line:
                self.put(sheet, (x, y), line, colour)
                y += self.line_h()
                line = word
            else:
                line = trial
        if line:
            self.put(sheet, (x, y), line, colour)
            y += self.line_h()
        return y


def zoom(rgb_or_rgba: np.ndarray, k: int) -> Image.Image:
    mode = "RGBA" if rgb_or_rgba.shape[-1] == 4 else "RGB"
    im = Image.fromarray(rgb_or_rgba, mode)
    return im.resize((im.width * k, im.height * k), Image.Resampling.NEAREST)


def on_backdrop(sprite: np.ndarray, colour) -> np.ndarray:
    bg = np.zeros((H, W, 3), np.uint8)
    bg[:] = colour
    a = sprite[..., 3] > 0
    bg[a] = sprite[..., :3][a]
    return bg


def freedoom_reference() -> np.ndarray | None:
    """Freedoom's POSSA1 for SCALE ONLY (BSD-3, iwads/ is not in git, so
    this is optional). Decoded from the Doom picture format."""
    if not IWAD.is_file():
        return None
    wad = IWAD.read_bytes()
    _, n, off = struct.unpack("<4sii", wad[:12])
    lumps = {}
    for i in range(n):
        pos, size, name = struct.unpack("<ii8s", wad[off + 16 * i:off + 16 * i + 16])
        lumps[name.rstrip(b"\0").decode("ascii", "replace")] = (pos, size)
    if "POSSA1" not in lumps or "PLAYPAL" not in lumps:
        return None
    pp = lumps["PLAYPAL"][0]
    pal = np.frombuffer(wad[pp:pp + 768], np.uint8).reshape(256, 3)
    pos, size = lumps["POSSA1"]
    d = wad[pos:pos + size]
    w, h, _, _ = struct.unpack("<hhhh", d[:8])
    img = np.zeros((h, w, 4), np.uint8)
    for x, c in enumerate(struct.unpack(f"<{w}i", d[8:8 + 4 * w])):
        while d[c] != 255:
            top, ln = d[c], d[c + 1]
            for j in range(ln):
                img[top + j, x, :3] = pal[d[c + 3 + j]]
                img[top + j, x, 3] = 255
            c += ln + 4
    return img


RECOMMENDED = "E"
# Written after looking at the sweep once (PIPELINE stage 2).
VERDICT = [
    "WHY E. The crested helmet is the one change that makes him OURS rather than a Wehrmacht "
    "re-enactor: it reads as the alien Reich of the lore (D9), which also keeps the swastika in a "
    "plainly fictional figure (D12) and the tone serious (D11). The greatcoat's bell and the rifle "
    "across the hips keep BESTIARY 3's tells (flared head, horizontal bar at the waist), which the "
    "Legion trooper's shotgun-high-across-the-chest must not share; B's port-arms diagonal comes "
    "close to that line, so not B. The gas mask (D, F) is a good alternative face, if you want him "
    "more inhuman: E's helmet with D's mask is a valid combination, ask for it.",
    "WHAT WORKS. Proportions match Doom's 56-unit actor (Freedoom shown for scale). The faction "
    "contract holds: khaki_olive and black only, no military_green, the armband the only saturated "
    "thing. Value is measured, not argued: body luma about 65, darker than BESTIARY 2.1's estimate (97) "
    "on purpose, so he clears SDSTEL1 (101) as well as concrete (147); worst gap 17 on SDSTEL1 at "
    "light 112, 27-30 on the hangar dado, 36-39 on the crates (the ART-BIBLE 6.2 watch item: he does "
    "not melt into them). At 1x and at game distance he reads as a helmeted soldier with a red armband.",
    "WHAT DOES NOT, HONESTLY. At 4x, which is how big he is when he is three metres from you, this "
    "is a paper doll: symmetrical, stiff, cloth without folds or weight, shading that is correct "
    "but mechanical. Freedoom's and id's sprites are painted pixel by pixel, and this does not reach "
    "that close-up quality. The firing pose differs from idle mostly by its flash: a rifle "
    "pointed at you is hard to foreshorten with flat shapes. The armband is 7x7, about twice a real "
    "one, because a 5-px symbol is the smallest that reads. At 16 px every cell is the same block "
    "with legs: the helmet tells are about 2 px, as BESTIARY 10 predicted; value does the work.",
    "THE 50-IMAGE RISK. A 2D shape layout has to be re-authored by hand for every rotation (5 drawings "
    "per frame) and every walk frame, about 35 layouts that will drift from each other. Proposal: "
    "keep this as the design spec, and build the remaining images as a 3D rig (the same shapes as "
    "3D capsules and ellipsoids, the same banded light and palette, rendered at 8 angles: BESTIARY "
    "2.6 'pose once, render many'). That gives consistent rotations at this same quality. If you want "
    "close-up quality beyond this, the honest route is (c): a concept or a pixel artist's pass on "
    "the front frames, with the rig doing the rest. Editing Freedoom's POSS would be fastest but "
    "would read as Freedoom (BESTIARY Q6); D35 keeps it for deaths and gibs only.",
]


def build_sheet(sprites: dict, metrics: dict, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    T = Text(2)
    bg = artlib.ramp("concrete_cold")[3]
    ink = artlib.ramp("cream_yellow")[14]
    dim = artlib.ramp("concrete_cold")[22]
    gold = artlib.ramp("hazard_yellow")[13]
    red = artlib.ramp("flag_red")[14]
    neutral = artlib.ramp("concrete_cold")[16]
    pad, gap = 24, 16
    Z4 = 4
    SZ = 2                          # the scenes, 2x for the eye (1x copies beside)
    head_h = 460
    row_h = H * Z4 + 3 * T.line_h() + 26
    width = 1980
    verdict_lines = sum(T.width(v) // (width - 2 * pad) + 2 for v in VERDICT)
    foot_h = 200 + verdict_lines * T.line_h() + 200
    height = head_h + row_h * len(CELLS) + foot_h
    sheet = Image.new("RGBA", (width, height), (*bg, 255))

    y = pad
    T.put(sheet, (pad, y), "SOVIET DOOM  ·  F5  ·  FOURTH REICH RIFLEMAN (SDRR)  ·  DESIGN SWEEP, FRONT VIEW", gold)
    T.put(sheet, (width - pad - T.width(stamp), y), stamp, dim)
    y += T.line_h() + 4
    y = T.para(sheet, (pad, y),
               "D35: drawn from scratch. One decision before ~50 images: what the man looks like. "
               "Rotation 1 only (facing you), idle SDRRA1 and firing SDRRF1. Draft, nothing in assets/. "
               "Built by tools/art/gen_enemy.py from shapes on a 4x canvas, reduced by majority vote, "
               "palette v1 only, seed 35, no system fonts.", ink, width - 2 * pad - 340)
    y += 4
    y = T.para(sheet, (pad, y),
               "Each row: the sprite at 4x (idle, fire) on neutral grey; the 1x sprite in four MAP01 v2 "
               "scenes and firing in a fifth, wall over SDFLR2 floor, both in the scene's sector light "
               "(shown 2x for the eye, true 1x copies under them); then game distance (/4, about 14 px "
               "tall) on the worst wall, value only, and the 16-px black silhouette (ART-BIBLE 6.4). "
               "Light stand-in: RGB x L/224, re-quantised; NOT VERIFIED against GZDoom.", dim, width - 2 * pad - 340)
    # Freedoom scale reference, top right
    ref = freedoom_reference()
    rx = width - pad - 300
    ry = pad + T.line_h() + 10
    if ref is not None:
        a_idle = sprites["A"]["idle"]
        T.put(sheet, (rx, ry), "SCALE ONLY, 2X:", dim)
        sheet.alpha_composite(zoom(ref, 2), (rx, ry + T.line_h()))
        sheet.alpha_composite(zoom(a_idle, 2), (rx + ref.shape[1] * 2 + 20, ry + T.line_h() - 14))
        T.put(sheet, (rx, ry + T.line_h() + 2 * ref.shape[0] + 6), "FREEDOOM POSSA1  ·  A", dim)
        T.put(sheet, (rx, ry + 2 * T.line_h() + 2 * ref.shape[0] + 6), "(BSD-3, NOT A SOURCE)", dim)
    # dimension table
    y = max(y + 12, pad + 8 * T.line_h())
    cols = (pad, pad + 100, pad + 400, pad + 600, pad + 1040)
    for x, h in zip(cols, ("CELL", "HELMET", "FACE", "COAT", "WEAPON")):
        T.put(sheet, (x, y), h, gold)
    y += T.line_h()
    names = {"stahl": "STAHLHELM", "crest": "CRESTED (ALIEN)", "bare": "EYELESS", "mask": "GAS MASK",
             "long": "CALF-LENGTH GREATCOAT", "short": "TUNIC, BREECHES, BOOTS",
             "rifle_hip": "BOLT RIFLE ACROSS THE HIPS", "rifle_port": "BOLT RIFLE AT PORT ARMS",
             "smg": "SUBMACHINE GUN AT THE HIP"}
    for c in CELLS:
        for x, v in zip(cols, (c.key, names[c.helmet], names[c.face], names[c.coat], names[c.weapon])):
            T.put(sheet, (x, y), v, red if c.key == RECOMMENDED and x == cols[0] else ink)
        y += T.line_h()

    y += 16
    for c in CELLS:
        s = sprites[c.key]
        m = metrics[c.key]
        tag = f"{c.key}  ·  {c.title.upper()}"
        if c.key == RECOMMENDED:
            tag += "   <<< RECOMMENDED"
        T.put(sheet, (pad, y), tag, red if c.key == RECOMMENDED else gold)
        T.put(sheet, (pad + 1000, y),
              f"{m['height_px']} X {m['width_px']} PX  ·  BODY LUMA {m['body_luma']:.0f}  ·  "
              f"GAP S1 {m['gap_S1']:.0f} S2 {m['gap_S2']:.0f} S3 {m['gap_S3']:.0f} S4 {m['gap_S4']:.0f}", dim)
        yy = y + T.line_h() + 4
        x = pad
        for pose in ("idle", "fire"):
            sheet.alpha_composite(zoom(on_backdrop(s[pose], neutral), Z4).convert("RGBA"), (x, yy))
            x += W * Z4 + 8
        x += gap
        for key, wall, light, what in (*SCENES, FIRE_SCENE):
            sc = s["scenes"][key]
            sheet.alpha_composite(zoom(sc, SZ).convert("RGBA"), (x, yy))
            small_y = yy + sc.shape[0] * SZ + 4
            sheet.alpha_composite(Image.fromarray(sc, "RGB").convert("RGBA"), (x, small_y))
            T.put(sheet, (x + SCENE_W + 6, small_y), key, ink)
            T.put(sheet, (x + SCENE_W + 6, small_y + T.line_h()), str(light), dim)
            x += SCENE_W * SZ + 12
        x += gap - 8
        # far, worst case, colour and value; then the 16-px silhouette
        fr = far(s["scenes"]["S3"])
        fv = np.repeat(luma(fr)[..., None].clip(0, 255).astype(np.uint8), 3, -1)
        FZ = 5
        sheet.alpha_composite(zoom(fr, FZ).convert("RGBA"), (x, yy))
        sheet.alpha_composite(zoom(fv, FZ).convert("RGBA"), (x + fr.shape[1] * FZ + 8, yy))
        sheet.alpha_composite(Image.fromarray(fr, "RGB").convert("RGBA"), (x, yy + fr.shape[0] * FZ + 8))
        T.put(sheet, (x + fr.shape[1] + 8, yy + fr.shape[0] * FZ + 8), "S3 /4", dim)
        sil = silhouette(s["idle"])
        sil_rgb = np.where(sil[..., None], 0, 235).astype(np.uint8).repeat(3, -1)
        sx = x + 2 * (fr.shape[1] * FZ + 8)
        sheet.alpha_composite(zoom(sil_rgb, FZ).convert("RGBA"), (sx, yy))
        sheet.alpha_composite(Image.fromarray(sil_rgb, "RGB").convert("RGBA"),
                              (sx, yy + SILHOUETTE_H * FZ + 8))
        T.put(sheet, (sx + sil.shape[1] + 8, yy + SILHOUETTE_H * FZ + 8), "16 PX", dim)
        y += row_h
    # legend of the scenes
    legend = "  ·  ".join(f"{key} {wall} @{light} {what.upper()}" for key, wall, light, what in (*SCENES, FIRE_SCENE))
    y = T.para(sheet, (pad, y), "SCENES: " + legend, dim, width - 2 * pad)
    y = T.para(sheet, (pad, y), "FAR COLUMNS: S3 AT /4 IN COLOUR AND VALUE ONLY (5X) AND TRUE SIZE; THE IDLE "
               "SILHOUETTE 16 PX TALL (5X) AND TRUE SIZE. GAP = |BODY - WALL| LUMA UNDER THE SAME LIGHT. "
               "FREEDOOM IS SHOWN FOR SCALE ONLY; NO PIXEL OF IT IS USED.", dim, width - 2 * pad)
    y += 14
    T.put(sheet, (pad, y), f"RECOMMENDATION: {RECOMMENDED}.  HONEST VERDICT ON THE METHOD:", red)
    y += T.line_h() + 2
    for v in VERDICT:
        y = T.para(sheet, (pad, y), v, ink, width - 2 * pad) + 4
    sheet = sheet.crop((0, 0, width, y + pad))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{stamp}_F5_reich-rifleman-sweep.png"
    sheet.convert("RGB").save(path, optimize=True)
    return path


def build_all(out_dir: Path = OUT_DIR) -> tuple[dict, dict]:
    sprites, metrics = {}, {}
    for c in CELLS:
        idle, fire = render(c, "idle"), render(c, "fire")
        save_sprite(idle, out_dir / f"{SPRITE}_{c.key}_A1.png")
        save_sprite(fire, out_dir / f"{SPRITE}_{c.key}_F1.png")
        scenes = {key: scene(idle, wall, light) for key, wall, light, _ in SCENES}
        k, wall, light, _ = FIRE_SCENE
        scenes[k] = scene(fire, wall, light)
        for key, sc in scenes.items():
            Image.fromarray(sc, "RGB").save(out_dir / f"scene_{c.key}_{key}.png", optimize=True)
        sprites[c.key] = {"idle": idle, "fire": fire, "scenes": scenes}
        metrics[c.key] = measure(idle)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return sprites, metrics


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    args = ap.parse_args()
    sprites, metrics = build_all()
    path = build_sheet(sprites, metrics, args.stamp)
    for k, m in metrics.items():
        print(k, m)
    print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
