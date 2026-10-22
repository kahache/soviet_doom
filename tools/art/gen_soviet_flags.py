"""D119 — Soviet flags in place of the occupiers' banners SDFLAG1-4.

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_soviet_flags.py [--preview]
                            (macOS: .venv/bin/python tools/art/gen_soviet_flags.py)

The CEO's playtest (D119, 2026-10-23): the Reich's and the Legion's banners
"no pegan: no parece que sean del enemigo sino del entorno". Every one of
them becomes a Soviet flag. The lump names and sizes do not change (64x128
walls), so the nine maps change without being edited. The enemies keep
their own armbands and flags on their sprites (D108, D114): this script
draws walls only.

Four variants, so no pair repeats (the maps hang SDFLAG1 beside SDFLAG2 and
SDFLAG3 beside SDFLAG4):

  SDFLAG1  on SDBRCK1  the USSR state flag hung vertically from a rod: plain
                       red, 1:2 (50x100), the gold-bordered red star above
                       the gold hammer and sickle in the upper hoist corner.
  SDFLAG2  on SDBRCK1  a Red Army standard on a wooden staff (left) with a
                       gold spearhead: gold border and fringe, the big
                       gold-bordered star with the hammer and sickle inside,
                       a gold cord ending in a tassel.
  SDFLAG3  on SDKREM1  a parade gonfalon hung from a crossbar on a staff
                       (right): swallowtail foot with a gold fringe, the
                       hammer and sickle in a gold wreath under the star,
                       two tassels at the crossbar's ends.
  SDFLAG4  on SDKREM1  the state flag after the battle: torn and burnt
                       foot, bullet holes with charred rims (the brick shows
                       through), a tear, soot rising from the foot.

Method: procedural, one seed per lump (BATCH_SEED + offset), deterministic,
quantised without dither. The ground is the approved wall the old banner
hung on, rebuilt by its own generator (SDBRCK1: gen_factory; SDKREM1:
gen_moscow); every pixel the flag does not touch is that wall's approved
pixel, so a flag tile beside a wall tile continues the bond with no seam
(tests/test_gen_soviet_flags.py holds it). The emblem is the approved
geometry: gen_soviet_base.hammer_sickle (SDSTAR1, measured by the CEO) and
artlib.star_points. No text, so no font (D27).

Palette: the cloth and the gold are v1 (flag_red, hazard_yellow), the wood
rust_brown, the iron steel_blue, the char concrete_cold and rust_brown. v2
only through the brick (marble_red): new pixels snap to v1 + marble_red,
never mosaic_gold or flesh_pink; the wall keeps its approved pixels as they
are (SDBRCK1 carries one v2 colour of its own).

Writes PNGs to work/art/soviet_flags/ and, with --preview, the CEO's
before/after sheet docs/art/previews/2026-10-23_P4_soviet-flags.png (x4;
the "before" are the D66/D113 renders kept in work/art/soviet_flags/
before_d119/). Never assets/: the lumps are copied byte for byte from work/.
"""

from __future__ import annotations

import argparse
import functools
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import Overlay, fbm, grain, ramp_colour, shade, star_points, to_rgb  # noqa: E402
import ep2lib  # noqa: E402  (v1 + marble_red snapping)
import gen_factory  # noqa: E402  (SDBRCK1, our alphabet for the sheet labels)
import gen_metro  # noqa: E402  (quantize_version: the full v2 PLTE every v2 lump carries)
import gen_moscow  # noqa: E402  (SDKREM1)
import gen_soviet_base as base  # noqa: E402  (the approved hammer and sickle)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "work" / "art" / "soviet_flags"
BEFORE_DIR = OUT_DIR / "before_d119"          # the occupiers' banners as they were (D66, D113)
PREVIEW = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-23_P4_soviet-flags.png"
SCRIPT_REL = "tools/art/gen_soviet_flags.py"

# Own seed space: 6000 + 119 for D119. Clear of every other generator
# (1935, 1977, 2077, 3077, 4100, 5400-5900, 6000, 6010).
BATCH_SEED = 6119
SEED_OFFSET = {"SDFLAG1": 1, "SDFLAG2": 2, "SDFLAG3": 3, "SDFLAG4": 4}
LUMPS = tuple(SEED_OFFSET)
GROUND = {"SDFLAG1": "SDBRCK1", "SDFLAG2": "SDBRCK1", "SDFLAG3": "SDKREM1", "SDFLAG4": "SDKREM1"}
FOLDER = {"SDFLAG1": "factory", "SDFLAG2": "factory", "SDFLAG3": "moscow", "SDFLAG4": "moscow"}
WALL_W, WALL_H = 64, 128
EDGE = 1                         # columns 0 and 63 stay the wall's own pixels (the rod stops short)

# ---------------------------------------------------------------- inks
RED_TONE = 0.72                  # flag_red: kumach, as the old banners and SDBANR1
RED_TORN = 0.64                  # the battle flag, faded and dirty
GOLD = ("hazard_yellow", 0.88)   # SDBANR1's gold
GOLD_DARK = ("hazard_yellow", 0.55)
GOLD_FRINGE = (("hazard_yellow", 0.72), ("hazard_yellow", 0.48))
CONTOUR = ("flag_red", 0.30)     # SDBANR1's dark contour round the gold
STAR_RED = ("flag_red", 0.80)    # the star's red field inside its gold border
WOOD = ("rust_brown", 0.42)
WOOD_LIGHT = ("rust_brown", 0.62)
IRON = ("steel_blue", 0.22)
IRON_LIGHT = ("steel_blue", 0.55)
IRON_DARK = ("steel_blue", 0.12)
CHAR = ("concrete_cold", 0.05)
SCORCH = ("rust_brown", 0.22)

# ---------------------------------------------------------------- geometry
# SDFLAG1 / SDFLAG4: the state flag, 1:2 (the flag's height across, its
# length down), hung from a rod by a sleeve.
STATE_CLOTH = (7, 57, 10, 110)   # x0, x1, y0, y1: 50 x 100
ROD_Y0, ROD_Y1 = 6, 9
SLEEVE_H = 3
STATE_STAR = (21, 22, 6.5)       # cx, cy, r: the bordered star in the hoist corner
STATE_HS = (21, 40, 11.0)        # cx, cy, r: the hammer and sickle under it
STATE_FOLDS = 3
# SDFLAG2: the standard on a staff at the left.
STAFF2_X = (5, 9)                # x0, x1 of the staff
STAFF_TOP, STAFF_FOOT = 13, 124
STD_CLOTH = (9, 56, 18, 100)
STD_STAR = (33, 54, 19.0)        # the big bordered star ...
STD_HS = (33, 56, 8.5)           # ... with the hammer and sickle inside
FRINGE = 4
# SDFLAG3: the gonfalon on a crossbar, staff at the right.
STAFF3_X = (55, 59)
BAR_Y0, BAR_Y1 = 14, 17
GONF = (8, 54, 18, 92, 108)      # x0, x1, y0, y1 (sides), y_tail (the swallowtail's points)
GONF_STAR = (31, 30, 7.0)
GONF_HS = (31, 58, 11.0)
WREATH = (31, 58, 16.0, 7)       # cx, cy, radius, leaf pairs a side
WREATH_SWEEP = 140               # degrees each branch climbs from the foot (open at the top)
# SDFLAG4: the battle damage.
TORN_FOOT = 102                  # the ragged foot wanders round this row
TORN_NOTCHES = ((22, 15), (45, 11))   # (x, depth): two tongues burnt away
BULLETS = 5
TEAR = (43, 74, 90)              # x, y0, y1 of the slit


def rng_for(lump: str) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + SEED_OFFSET[lump])


def col(ink: tuple[str, float]) -> tuple[int, int, int]:
    return ramp_colour(*ink)


# ================================================================ grounds
def ground(name: str) -> np.ndarray:
    """The approved wall, as its own generator quantises it (the tests hold
    this equal to assets/). A fresh copy each call."""
    return _ground(name).copy()


@functools.lru_cache(maxsize=None)
def _ground(name: str) -> np.ndarray:
    if name == "SDBRCK1":
        return gen_factory.as_rgb(gen_factory.quantise("SDBRCK1", gen_factory.tex_brck1()))
    if name == "SDKREM1":
        return ep2lib.as_array(ep2lib.quantise(gen_moscow.tex_krem1(), 2))
    raise KeyError(name)


# ================================================================ helpers
def poly_mask(pts, w: int = WALL_W, h: int = WALL_H) -> np.ndarray:
    ov = Overlay(w, h)
    ov.polygon(pts, (255, 255, 255))
    a = np.asarray(ov.img.resize((w, h), Image.Resampling.BOX))[..., 3]
    return a >= 128


def rect_mask(x0, x1, y0, y1) -> np.ndarray:
    yy, xx = np.mgrid[0:WALL_H, 0:WALL_W]
    return (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)


def red_field(rng: np.random.Generator, tone: float = RED_TONE) -> np.ndarray:
    return to_rgb(np.clip(tone + grain(WALL_W, WALL_H, rng, 0.02), 0, 1), "flag_red")


def bordered_star(ov: Overlay, cx: float, cy: float, r: float, border: float = 1.6) -> None:
    """The flag's star: red, a gold border, a dark contour outside it."""
    g = ov.group(outline=col(CONTOUR), outline_width=1.0)
    g.polygon(star_points(cx, cy, r), col(GOLD))
    ov.end_group(g)
    ov.polygon(star_points(cx, cy, r - border), col(STAR_RED))


def emblem(ov: Overlay, star, hs) -> None:
    bordered_star(ov, *star)
    base.hammer_sickle(ov, hs[0], hs[1], hs[2], col(GOLD), col(CONTOUR))


def folds(x0: int, x1: int, n: int, rng: np.random.Generator, amp: float = 0.10, phase: float = 0.0) -> np.ndarray:
    yy, xx = np.mgrid[0:WALL_H, 0:WALL_W]
    f = 1 + amp * np.sin(2 * np.pi * n * (xx - x0) / (x1 - x0) + phase)
    return f * (1 + 0.04 * (fbm(WALL_W, WALL_H, 4, 2, rng, aspect=4.0) - 0.5))


def hang(wall: np.ndarray, cloth: np.ndarray, mask: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """The cloth on the wall: its cast shadow (2 px down-right), the cloth
    itself with a little grain."""
    sh = np.roll(np.roll(mask, 2, axis=0), 2, axis=1) & ~mask
    rgb = np.where(sh[..., None], shade(wall, 0.50), wall)
    cloth = shade(cloth, 1 + grain(WALL_W, WALL_H, rng, 0.03))
    return np.where(mask[..., None], cloth, rgb)


def fringe(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Gold thread: every other column bright, a solid band at the top."""
    yy, xx = np.mgrid[0:WALL_H, 0:WALL_W]
    thread = np.where((xx % 2 == 0)[..., None], np.array(col(GOLD_FRINGE[0]), np.uint8),
                      np.array(col(GOLD_FRINGE[1]), np.uint8))
    return np.where(mask[..., None], thread, rgb)


def rod(ov: Overlay) -> None:
    """The iron rod across the wall, its two brackets and gold end knobs."""
    ov.rect(2, ROD_Y0, WALL_W - 2, ROD_Y1, fill=col(IRON))
    ov.rect(2, ROD_Y0, WALL_W - 2, ROD_Y0 + 1, fill=col(IRON_LIGHT))
    for bx in (4, WALL_W - 6):
        ov.rect(bx, ROD_Y0 - 3, bx + 2, ROD_Y1 + 3, fill=col(IRON_DARK))
    for kx in (2, WALL_W - 4):
        ov.ellipse(kx - 0.5, ROD_Y0 - 1, kx + 2.5, ROD_Y1 + 1, fill=col(GOLD))


def staff(ov: Overlay, x0: int, x1: int) -> None:
    """A wooden staff with a gold spearhead, an iron ferrule and two wall
    clamps."""
    cx = (x0 + x1) / 2
    ov.rect(x0, STAFF_TOP, x1, STAFF_FOOT, fill=col(WOOD))
    ov.rect(x0 + 1, STAFF_TOP, x0 + 2, STAFF_FOOT, fill=col(WOOD_LIGHT))
    g = ov.group(outline=col(IRON_DARK), outline_width=0.8)
    g.polygon([(cx, 1.5), (cx + 3.2, 7.5), (cx + 1.2, 11.5), (cx - 1.2, 11.5), (cx - 3.2, 7.5)], col(GOLD))
    g.ellipse(cx - 2.6, 10.5, cx + 2.6, 14.5, fill=col(GOLD))
    ov.end_group(g)
    ov.line([(cx, 3.5), (cx, 10)], col(GOLD_DARK), 0.8)
    ov.rect(x0 - 0.5, STAFF_FOOT - 4, x1 + 0.5, STAFF_FOOT, fill=col(IRON))
    for cy in (30, 112):
        ov.rect(x0 - 2, cy, x1 + 2, cy + 3, fill=col(IRON_DARK))
        ov.rect(x0 - 2, cy, x1 + 2, cy + 1, fill=col(IRON_LIGHT))


def tassel(ov: Overlay, x: float, y: float, length: float = 11.0) -> None:
    """A gold knot and a tassel of threads hanging from it."""
    ov.ellipse(x - 2, y - 2, x + 2, y + 2, fill=col(GOLD))
    ov.polygon([(x - 1.5, y + 1.5), (x + 1.5, y + 1.5), (x + 3, y + length), (x - 3, y + length)], col(GOLD_DARK))
    for dx in (-2, -0.6, 0.8, 2.2):
        ov.line([(x + dx * 0.4, y + 2), (x + dx, y + length)], col(GOLD), 0.6)


def distance_inside(mask: np.ndarray, steps: int) -> np.ndarray:
    """Chebyshev distance (in px, capped at `steps`) from each cloth pixel
    to the nearest pixel outside the cloth, by repeated erosion."""
    d = np.full(mask.shape, steps, np.int32)
    cur = mask.copy()
    for k in range(steps):
        er = cur.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                er &= np.roll(np.roll(cur, dy, axis=0), dx, axis=1)
        d[cur & ~er] = k
        cur = er
    d[~mask] = -1
    return d


# ================================================================ the four flags
def tex_flag1() -> np.ndarray:
    """The USSR state flag hung vertically from a rod on SDBRCK1."""
    rng = rng_for("SDFLAG1")
    wall = ground(GROUND["SDFLAG1"])
    x0, x1, y0, y1 = STATE_CLOTH
    ov = Overlay(WALL_W, WALL_H)
    emblem(ov, STATE_STAR, STATE_HS)
    cloth = ov.composite(red_field(rng))
    f = folds(x0, x1, STATE_FOLDS, rng)
    f[y0:y0 + SLEEVE_H] *= 0.86              # the sleeve round the rod
    f[y0 + SLEEVE_H] *= 0.70
    f[y1 - 2:y1] *= 0.82                     # the hem
    cloth = shade(cloth, f)
    rgb = hang(wall, cloth, rect_mask(x0, x1, y0, y1), rng)
    top = Overlay(WALL_W, WALL_H)
    rod(top)
    return top.composite(rgb)


def tex_flag2() -> np.ndarray:
    """A Red Army standard on a staff, on SDBRCK1."""
    rng = rng_for("SDFLAG2")
    wall = ground(GROUND["SDFLAG2"])
    x0, x1, y0, y1 = STD_CLOTH
    ov = Overlay(WALL_W, WALL_H)
    ov.rect(x0 + 3, y0 + 3, x1 - 3, y1 - 3, outline=col(GOLD), width=1.0)
    sx, sy, sr = STD_STAR
    g = ov.group(outline=col(CONTOUR), outline_width=1.0)
    g.polygon(star_points(sx, sy, sr), col(GOLD))
    ov.end_group(g)
    ov.polygon(star_points(sx, sy, sr - 2.0), col(STAR_RED))
    base.hammer_sickle(ov, STD_HS[0], STD_HS[1], STD_HS[2], col(GOLD), col(CONTOUR))
    cloth = ov.composite(red_field(rng))
    cloth = shade(cloth, folds(x0, x1, 2, rng, amp=0.08, phase=0.6))
    mask = rect_mask(x0, x1, y0, y1)
    rgb = hang(wall, cloth, mask, rng)
    rgb = fringe(rgb, rect_mask(x0, x1 + FRINGE, y1, y1 + FRINGE) | rect_mask(x1, x1 + FRINGE, y0, y1))
    top = Overlay(WALL_W, WALL_H)
    staff(top, *STAFF2_X)
    for ry in range(y0 + 2, y1, 12):         # the rings that hold the cloth to the staff
        top.ellipse(STAFF2_X[1] - 1.2, ry - 1.2, STAFF2_X[1] + 1.2, ry + 1.2, fill=col(GOLD_DARK))
    cx = (STAFF2_X[0] + STAFF2_X[1]) / 2
    top.line([(cx + 1, 15), (cx + 4, 40), (cx + 6, 70), (cx + 7, 98)], col(GOLD), 1.0)
    tassel(top, cx + 7, 99, 12)
    return top.composite(rgb)


def wreath(ov: Overlay, cx: float, cy: float, r: float, n: int) -> None:
    """Two gold branches of leaves up the sides of a circle, open at the top
    and tied with a red ribbon at the foot (the state emblem's wreath, as
    far as 64 px allows)."""
    for side in (-1, 1):
        stem = [(cx + r * np.cos(np.deg2rad(90 + side * a)), cy + r * np.sin(np.deg2rad(90 + side * a)))
                for a in np.linspace(14, WREATH_SWEEP, 12)]
        ov.line(stem, col(GOLD_DARK), 0.8)
        for i in range(n):
            t = i / (n - 1)
            ang = np.deg2rad(90 + side * (20 + (WREATH_SWEEP - 20) * t))
            p = np.array([cx + r * np.cos(ang), cy + r * np.sin(ang)])
            up = np.array([np.sin(ang), -np.cos(ang)]) * side        # along the branch, towards its tip
            out = np.array([np.cos(ang), np.sin(ang)])
            for k, lean in ((0, 1.0), (1, -1.0)):                    # a leaf each side of the stem
                d = up + out * lean * 0.9
                d = d / np.linalg.norm(d)
                nrm = np.array([-d[1], d[0]])
                c = p + d * 1.6
                L, W = 2.2 - 0.5 * t, 1.1 - 0.2 * t
                pts = [tuple(c - d * L), tuple(c + nrm * W), tuple(c + d * L), tuple(c - nrm * W)]
                ov.polygon(pts, col(GOLD) if k == 0 else col(GOLD_DARK))
    ov.polygon([(cx - 3.5, cy + r - 0.5), (cx + 3.5, cy + r - 0.5), (cx + 2, cy + r + 3), (cx - 2, cy + r + 3)],
               col(STAR_RED))
    ov.polygon([(cx - 1.5, cy + r - 1), (cx + 1.5, cy + r - 1), (cx + 1.5, cy + r + 2), (cx - 1.5, cy + r + 2)],
               col(GOLD))


def tex_flag3() -> np.ndarray:
    """A parade gonfalon on a crossbar, the staff at the right, on SDKREM1."""
    rng = rng_for("SDFLAG3")
    wall = ground(GROUND["SDFLAG3"])
    x0, x1, y0, y1, yt = GONF
    mid = (x0 + x1) / 2
    shape = [(x0, y0), (x1, y0), (x1, yt), (mid + 4, y1), (mid - 4, y1), (x0, yt)]
    mask = poly_mask(shape)
    ov = Overlay(WALL_W, WALL_H)
    emblem(ov, GONF_STAR, GONF_HS)
    wreath(ov, *WREATH)
    cloth = ov.composite(red_field(rng))
    cloth = shade(cloth, folds(x0, x1, 2, rng, amp=0.09, phase=1.9))
    rgb = hang(wall, cloth, mask, rng)
    # the gold fringe follows the swallowtail
    foot = [(x1, yt), (mid + 4, y1), (mid - 4, y1), (x0, yt)]
    below = [(x, y + FRINGE) for x, y in foot]
    rim = poly_mask(foot + below[::-1]) & ~mask
    rgb = fringe(rgb, rim)
    top = Overlay(WALL_W, WALL_H)
    staff(top, *STAFF3_X)
    top.rect(x0 - 2, BAR_Y0, STAFF3_X[0], BAR_Y1, fill=col(WOOD))
    top.rect(x0 - 2, BAR_Y0, STAFF3_X[0], BAR_Y0 + 1, fill=col(WOOD_LIGHT))
    top.ellipse(x0 - 4, BAR_Y0 - 0.5, x0 - 0.5, BAR_Y1 + 0.5, fill=col(GOLD))
    tassel(top, x0 - 2, BAR_Y1 + 3, 10)
    tassel(top, STAFF3_X[0] - 2, BAR_Y1 + 3, 10)
    return top.composite(rgb)


def tex_flag4() -> np.ndarray:
    """The state flag after the battle, on SDKREM1: the foot torn and burnt,
    bullet holes, a tear, soot."""
    rng = rng_for("SDFLAG4")
    wall = ground(GROUND["SDFLAG4"])
    x0, x1, y0, _ = STATE_CLOTH
    yy, xx = np.mgrid[0:WALL_H, 0:WALL_W]
    # the ragged foot: a random walk round TORN_FOOT, two tongues burnt away
    foot = np.full(WALL_W, float(TORN_FOOT))
    walk = np.cumsum(rng.normal(0, 1.6, WALL_W))
    foot += walk - walk.mean()
    for nx, depth in TORN_NOTCHES:
        foot -= depth * np.clip(1 - np.abs(np.arange(WALL_W) - nx) / 4.5, 0, 1)
    foot = np.clip(foot, 78, 112)
    mask = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < foot[None, :])
    # the hoist corner (the emblem) is spared: holes and tear stay below it
    holes = np.zeros_like(mask)
    rims = np.zeros_like(mask)
    placed = 0
    while placed < BULLETS:
        hx, hy = rng.uniform(x0 + 6, x1 - 5), rng.uniform(56, 92)
        r = rng.uniform(1.4, 2.3)
        d2 = (xx + 0.5 - hx) ** 2 + (yy + 0.5 - hy) ** 2
        if ((d2 <= (r + 1.6) ** 2) & ~mask).any():
            continue
        holes |= d2 <= r * r
        rims |= (d2 <= (r + 1.2) ** 2)
        placed += 1
    tx, ty0, ty1 = TEAR
    tear = (xx == tx) & (yy >= ty0) & (yy < np.minimum(ty1, foot[tx] + 1))
    mask &= ~holes & ~tear
    ov = Overlay(WALL_W, WALL_H)
    emblem(ov, STATE_STAR, STATE_HS)
    cloth = ov.composite(red_field(rng, RED_TORN))
    f = folds(x0, x1, STATE_FOLDS, rng, amp=0.13, phase=0.9)
    f[y0:y0 + SLEEVE_H] *= 0.86
    f[y0 + SLEEVE_H] *= 0.70
    # soot rising from the burnt foot, patchy
    rise = np.clip((yy - (foot[None, :] - 30)) / 30.0, 0, 1)
    patch = fbm(WALL_W, WALL_H, 5, 3, rng)
    f *= 1 - 0.55 * rise * (0.5 + patch)
    cloth = shade(cloth, np.clip(f, 0.2, 1.5))
    # char: the last two pixels before every burnt edge (foot, holes)
    d = distance_inside(mask | tear, 3)
    burnt_edge = (yy >= foot[None, :] - 4) | rims
    cloth = np.where(((d == 0) & burnt_edge & mask)[..., None], np.array(col(CHAR), np.uint8), cloth)
    cloth = np.where(((d == 1) & burnt_edge & mask)[..., None], np.array(col(SCORCH), np.uint8), cloth)
    rgb = hang(wall, cloth, mask, rng)
    # the tear's lips: a dark line where the cloth parts
    rgb = np.where((tear & (yy < foot[None, :]))[..., None], shade(wall, 0.35), rgb)
    top = Overlay(WALL_W, WALL_H)
    rod(top)
    return top.composite(rgb)


BUILDERS = {"SDFLAG1": tex_flag1, "SDFLAG2": tex_flag2, "SDFLAG3": tex_flag3, "SDFLAG4": tex_flag4}


# ================================================================ quantise
def quantise(lump: str, rgb: np.ndarray) -> Image.Image:
    """No dither. The wall's untouched pixels keep their approved colour;
    every pixel the flag drew snaps to v1 + marble_red (ep2lib), never
    gold or flesh. The image carries the full v2 PLTE (226 entries), like
    every other v2 lump."""
    wall = ground(GROUND[lump])
    snapped = ep2lib.as_array(ep2lib.quantise(rgb, 2))
    untouched = (rgb == wall).all(-1)
    out = np.where(untouched[..., None], wall, snapped).astype(np.uint8)
    return gen_metro.quantize_version(np.ascontiguousarray(out), 2)


def as_rgb(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("RGB"))


def build(out_dir: Path = OUT_DIR) -> dict[str, np.ndarray]:
    """Render the four lumps into out_dir; returns their RGB arrays."""
    out_dir.mkdir(parents=True, exist_ok=True)
    arrays = {}
    for lump in LUMPS:
        rgb = BUILDERS[lump]()
        assert rgb.shape == (WALL_H, WALL_W, 3), (lump, rgb.shape)
        img = quantise(lump, rgb)
        img.save(out_dir / f"{lump}.png", optimize=True)
        arrays[lump] = as_rgb(img)
        print(f"{lump} on {GROUND[lump]}  colours={len(np.unique(arrays[lump].reshape(-1, 3), axis=0))}")
    return arrays


# ================================================================ the CEO's sheet
ZOOM = 4
GAP = 8
LABEL_SCALE = 1
SHEET_BG = ("concrete_cold", 0.10)
LABEL_INK = ("cream_yellow", 0.94)


def label(text: str) -> np.ndarray:
    """A label set in our own alphabet (bigfont, D24): no system font."""
    body, shadow = gen_factory.glyph_masks(text)
    out = np.zeros(body.shape + (4,), np.uint8)
    out[shadow] = (*col(("concrete_cold", 0.02)), 255)
    out[body] = (*col(LABEL_INK), 255)
    return out


def paste(canvas: np.ndarray, tile: np.ndarray, x: int, y: int) -> None:
    h, w = tile.shape[:2]
    if tile.shape[2] == 4:
        a = tile[..., 3:4] > 0
        canvas[y:y + h, x:x + w] = np.where(a, tile[..., :3], canvas[y:y + h, x:x + w])
    else:
        canvas[y:y + h, x:x + w] = tile


def preview(after: dict[str, np.ndarray], before_dir: Path = BEFORE_DIR, path: Path = PREVIEW) -> Path:
    """Before (top) and after (bottom), each flag between two tiles of its
    wall as the maps hang it, every pixel x4 (nearest neighbour)."""
    walls = {name: ground(name) for name in set(GROUND.values())}
    rows = []
    for title, source in (("ANTES", "before"), ("DESPUÉS", "after")):
        tiles = []
        for lump in LUMPS:
            if source == "after":
                img = after[lump]
            else:
                with Image.open(before_dir / f"{lump}_D119_before.png") as im:
                    img = np.asarray(im.convert("RGB"))
            w = walls[GROUND[lump]]
            tiles.append(np.hstack([w, img, w]))
        rows.append((title, tiles))
    cell_w = 3 * WALL_W
    width = GAP + len(LUMPS) * (cell_w + GAP)
    lab_h = 20
    height = GAP + 2 * (lab_h + WALL_H + lab_h + GAP)
    canvas = np.zeros((height, width, 3), np.uint8)
    canvas[:] = col(SHEET_BG)
    y = GAP
    for title, tiles in rows:
        paste(canvas, label(title), GAP, y)
        y += lab_h
        for i, tile in enumerate(tiles):
            x = GAP + i * (cell_w + GAP)
            paste(canvas, tile, x, y)
            name = label(LUMPS[i])
            paste(canvas, name, x + (cell_w - name.shape[1]) // 2, y + WALL_H + 3)
        y += WALL_H + lab_h + GAP
    big = Image.fromarray(canvas).resize((width * ZOOM, height * ZOOM), Image.Resampling.NEAREST)
    path.parent.mkdir(parents=True, exist_ok=True)
    big.save(path, optimize=True)
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--preview", action="store_true", help="also write the CEO's before/after sheet")
    args = ap.parse_args()
    arrays = build()
    if args.preview:
        print("sheet:", preview(arrays).relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
