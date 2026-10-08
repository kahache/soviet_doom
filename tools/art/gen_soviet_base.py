"""Batch 1 — "Soviet base" texture set for MAP01 (Zarya-7 cosmodrome).

Run with the project venv:  .venv/bin/python tools/art/gen_soviet_base.py

Writes indexed PNGs to work/art/batch1/soviet_base/ (NOT assets/: only
CEO-approved textures are copied there) and a manifest JSON next to them
that tools/art/make_preview.py turns into the HTML sheet for the CEO.

Every texture is 100% procedural (origin (a) in docs/art/ART-BIBLE.md):
noise fields + vector overlays, quantised to docs/art/palette.json.
Rebuilding with the same seed gives the same bytes.

All sizes in texture pixels (= Doom map units on a wall).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import (  # noqa: E402
    FONT_POSTER, FONT_SMALL, Overlay, blend, fbm, grain, ramp_colour, save_indexed,
    shade, star_points, tiling_seam_score, to_rgb,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SET_NAME = "soviet_base"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "batch1" / SET_NAME
MANIFEST = PROJECT_ROOT / "work" / "art" / "batch1" / "manifest.json"
SCRIPT_REL = "tools/art/gen_soviet_base.py"

# One master seed for the batch; each texture derives its own (below) so a
# single texture can be re-rolled without touching the others.
BATCH_SEED = 1977  # the proposed year of the invasion (D8)

# Standard Doom sizes (ART-BIBLE §2).
WALL_W, WALL_H = 64, 128
WIDE_W = 128
FLAT = 64

# --- concrete -----------------------------------------------------------
# Mean ramp position of raw concrete. 0.58 ~ RGB 125: mid-grey, so sector
# light 128-160 lands it where Doom's own greys sit and enemies (darker
# silhouettes, red/chrome accents) stay readable against it.
CONCRETE_MID = 0.58
CONCRETE_BLOTCH = 0.30     # amplitude of the big fbm blotches
CONCRETE_GRAIN = 0.05      # per-pixel grain, breaks banding before quantise
CONCRETE_PIT_RATE = 0.025  # fraction of pixels that are aggregate pits
CONCRETE_PIT_DEPTH = 0.18  # how much darker a pit is
JOINT_DARK = 0.50          # groove shading factor (2 px)
JOINT_LIGHT = 1.18         # lit lip under a horizontal groove (1 px)
JOINT_STAIN_DEPTH = 0.22   # grime running down from a horizontal joint
JOINT_STAIN_LEN = 14.0     # px, exponential fall-off of that grime
DRIP_DEPTH = 0.10          # vertical water streak darkening
PANEL_H = 64               # prefab panel height: two panels per 128 wall
PANEL_OFFSET = 32          # running bond: lower panel row shifted by half

# --- red stripe (SDCONC2) ------------------------------------------------
STRIPE_Y0, STRIPE_Y1 = 58, 70     # centred on the panel joint at y=64
STRIPE_RED = 0.72                 # flag_red ramp position (painted, not fresh)
STRIPE_WEAR = 0.30                # fbm threshold below which the paint chipped

# --- emblem plaque (SDSTAR1) ---------------------------------------------
PLAQUE = (8, 20, 56, 92)          # x0,y0,x1,y1 of the painted panel
PLAQUE_BORDER = 2
STAR_CENTER, STAR_R = (32, 42), 15
HS_CENTER, HS_R = (32, 72), 12    # hammer & sickle bounding radius

# --- green steel (SDSTEL1) -----------------------------------------------
PLATE = 32                 # riveted plate size; 2x4 plates per wall
RIVET_INSET = 4            # rivet centre distance from plate edge
RIVET_R = 1.6
STEEL_GREEN_MID = 0.55
STEEL_CHIP_THRESHOLD = 0.75   # fbm above this -> paint chipped to bare steel
STEEL_SCRATCHES = 7

# --- bunker door (SDDOOR1) -----------------------------------------------
DOOR_FRAME = 10
DOOR_RIB_YS = (44, 84)     # horizontal reinforcing ribs
DOOR_RIB_H = 6
WHEEL_CENTER, WHEEL_R_OUT, WHEEL_R_IN = (64, 64), 17, 13
WHEEL_SPOKES = 4
DOOR_STENCIL = "7"         # Zarya-7
DOOR_STENCIL_SIZE = 26

# --- posters -------------------------------------------------------------
POSTER_RED = 0.78
POSTER_CREAM = 0.92
POSTER_AGE = 0.12          # multiplicative grime amplitude on paper
LENIN_TEXT_TOP, LENIN_TEXT_BOTTOM = "ЛЕНИН", "ЖИВ"
LENIN_TEXT_SIZE = 17
LENIN_CIRCLE_C, LENIN_CIRCLE_R = (32, 58), 27
COSMO_LINE1, COSMO_LINE2 = "СЛАВА СОВЕТСКОЙ", "КОСМОНАВТИКЕ"
COSMO_TEXT_SIZE = 17
COSMO_STARS = 14

# Lenin profile, facing right, in a 100x140 box (hand-placed points, then
# scaled). Bald dome, brow, nose, moustache, goatee: the four shapes that
# make the silhouette readable at 30 px.
LENIN_PROFILE = [
    (22, 140), (24, 105), (14, 80), (16, 50), (28, 24), (48, 10), (70, 16),
    (84, 34), (88, 48), (84, 56), (90, 64), (100, 76), (88, 82), (97, 87),
    (85, 92), (88, 98), (84, 104), (92, 120), (76, 124), (66, 118), (62, 140),
]

# --- flats ---------------------------------------------------------------
FLOOR_MID = 0.52           # floors a touch darker than walls (they take the dirt)
FLOOR_LINE_X0, FLOOR_LINE_X1 = 2, 9   # painted lane line, continuous when tiled
FLOOR_LINE_WEAR = 0.38
FLOOR_CRACKS = 2
CRACK_WIDTH = 1.0           # px; sub-pixel so the crack is a soft dark hairline
TILE = 16                  # 4x4 tiles per flat
TILE_GROUT = 1
CEIL_MID = 0.66            # ceilings lighter: they face the lamps
LAMP_HOUSING = (12, 25, 52, 39)
LAMP_TUBE = (14, 27, 50, 37)
LAMP_GLOW_R = 22.0


def rng_for(seed_offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + seed_offset)


# ======================================================== base materials
def concrete(w: int, h: int, rng: np.random.Generator, mid: float = CONCRETE_MID) -> np.ndarray:
    field = mid + (fbm(w, h, 4, 5, rng, 0.55) - 0.5) * CONCRETE_BLOTCH
    field += grain(w, h, rng, CONCRETE_GRAIN)
    pits = rng.random((h, w)) < CONCRETE_PIT_RATE
    field = np.where(pits, field - CONCRETE_PIT_DEPTH, field)
    field -= DRIP_DEPTH * (fbm(w, h, 8, 2, rng, aspect=8.0) - 0.5)
    return to_rgb(field, "concrete_cold")


def horizontal_joint(rgb: np.ndarray, y: int, rng: np.random.Generator) -> np.ndarray:
    """2 px groove at row y (wrapping), lit lip below, grime streaks under it."""
    h, w = rgb.shape[:2]
    f = np.ones((h, w))
    f[y % h] = JOINT_DARK
    f[(y + 1) % h] = JOINT_DARK * 1.2
    f[(y + 2) % h] = JOINT_LIGHT
    dy = (np.arange(h)[:, None] - (y + 3)) % h
    along = fbm(w, 1, 6, 2, rng)[0][None, :]
    stain = JOINT_STAIN_DEPTH * np.exp(-dy / JOINT_STAIN_LEN) * (0.4 + 0.6 * along)
    return shade(rgb, f * (1 - stain))


def vertical_joint(rgb: np.ndarray, x: int, y0: int, y1: int) -> np.ndarray:
    h, w = rgb.shape[:2]
    f = np.ones((h, w))
    f[y0:y1, x % w] = JOINT_DARK
    f[y0:y1, (x + 1) % w] = JOINT_LIGHT * 0.95
    return shade(rgb, f)


def prefab_wall(rng: np.random.Generator) -> np.ndarray:
    """Concrete with two panel rows in running bond. Joints sit on the
    texture edges so adjacent tiles continue the grid."""
    rgb = concrete(WALL_W, WALL_H, rng)
    rgb = horizontal_joint(rgb, 0, rng)
    rgb = horizontal_joint(rgb, PANEL_H, rng)
    rgb = vertical_joint(rgb, 0, 0, PANEL_H)
    rgb = vertical_joint(rgb, PANEL_OFFSET, PANEL_H, WALL_H)
    return rgb


# ============================================================== textures
def tex_conc1():
    rng = rng_for(1)
    return prefab_wall(rng)


def tex_conc2():
    rng = rng_for(2)
    rgb = concrete(WALL_W, WALL_H, rng)
    rgb = horizontal_joint(rgb, 0, rng)
    rgb = vertical_joint(rgb, 0, 0, WALL_H)
    lum = rgb.mean(axis=2) / 255.0
    band = np.zeros((WALL_H, WALL_W))
    band[STRIPE_Y0:STRIPE_Y1] = 1.0
    wear = fbm(WALL_W, WALL_H, 6, 3, rng) > STRIPE_WEAR
    band *= wear
    red = np.array(ramp_colour("flag_red", STRIPE_RED), dtype=np.float64)
    painted = np.clip(red[None, None, :] * (0.55 + 0.75 * lum)[..., None], 0, 255)
    rgb = np.where(band[..., None] > 0, painted, rgb).astype(np.uint8)
    # 1 px darker edge above and below the band (paint ridge shadow)
    f = np.ones((WALL_H, WALL_W))
    f[STRIPE_Y0 - 1] = 0.8
    f[STRIPE_Y1] = 0.8
    return shade(rgb, f)


def hammer_sickle(ov: Overlay, cx: float, cy: float, r: float, fill):
    """Stylised hammer and sickle inside radius r, as on the flag: the
    sickle's blade sweeps from a tip at the left over the top and down the
    right into a handle at the lower-right; the hammer's head sits upper-left
    (poking out of the crescent so it reads at 24 px) and its handle crosses
    the crescent down to the bottom centre, clearly apart from the sickle's."""
    # sickle blade: crescent open at the bottom (Pillow angles: 90 = down)
    ov.arc_ring(cx + 0.05 * r, cy - 0.15 * r, 0.80 * r, 0.58 * r, 165, 420, fill)
    # sickle tip: wedge continuing the blade at its left end, pointing down
    ov.polygon([(cx - 0.75 * r, cy + 0.03 * r), (cx - 0.53 * r, cy - 0.04 * r), (cx - 0.66 * r, cy + 0.42 * r)], fill)
    # sickle handle from the blade's right end down-right
    ov.line([(cx + 0.45 * r, cy + 0.38 * r), (cx + 0.80 * r, cy + 0.98 * r)], fill, width=0.22 * r)
    # hammer handle: from the head (upper-left) to the bottom centre
    ov.line([(cx - 0.55 * r, cy - 0.55 * r), (cx + 0.28 * r, cy + 0.95 * r)], fill, width=0.17 * r)
    # hammer head: a bar perpendicular to the handle, outside the crescent
    c = np.array([cx - 0.64 * r, cy - 0.64 * r])
    u = np.array([0.82, -0.57]) * 0.40 * r
    v = np.array([0.57, 0.82]) * 0.16 * r
    ov.polygon([tuple(c + u + v), tuple(c + u - v), tuple(c - u - v), tuple(c - u + v)], fill)


def tex_star1():
    rng = rng_for(3)
    rgb = prefab_wall(rng)
    x0, y0, x1, y1 = PLAQUE
    ov = Overlay(WALL_W, WALL_H)
    cream = ramp_colour("cream_yellow", 0.85)
    red = ramp_colour("flag_red", 0.70)
    gold = ramp_colour("hazard_yellow", 0.88)
    dark = ramp_colour("flag_red", 0.35)
    ov.rect(x0, y0, x1, y1, fill=cream)
    ov.rect(x0 + PLAQUE_BORDER, y0 + PLAQUE_BORDER, x1 - PLAQUE_BORDER, y1 - PLAQUE_BORDER, fill=red)
    # inner shadow line for depth
    ov.line([(x0 + PLAQUE_BORDER, y1 - PLAQUE_BORDER - 0.5), (x1 - PLAQUE_BORDER, y1 - PLAQUE_BORDER - 0.5)], dark, 1)
    ov.polygon(star_points(STAR_CENTER[0], STAR_CENTER[1] + 1, STAR_R), dark)      # drop shadow
    ov.polygon(star_points(STAR_CENTER[0], STAR_CENTER[1], STAR_R), gold)
    hammer_sickle(ov, HS_CENTER[0], HS_CENTER[1] + 1, HS_R, dark)
    hammer_sickle(ov, HS_CENTER[0], HS_CENTER[1], HS_R, gold)
    rgb = ov.composite(rgb)
    # paint grime over the plaque so it belongs to the wall
    g = 1 - 0.10 * (fbm(WALL_W, WALL_H, 5, 3, rng) - 0.5)
    return shade(rgb, g)


def tex_stel1():
    rng = rng_for(4)
    w, h = WALL_W, WALL_H
    field = STEEL_GREEN_MID + (fbm(w, h, 3, 5, rng, 0.5) - 0.5) * 0.22 + grain(w, h, rng, 0.03)
    rgb = to_rgb(field, "military_green")
    # plate bevels: dark line on the plate's right/bottom edge, light on left/top
    f = np.ones((h, w))
    for x in range(0, w, PLATE):
        f[:, x] *= 1.15
        f[:, (x - 1) % w] *= 0.6
    for y in range(0, h, PLATE):
        f[y, :] *= 1.15
        f[(y - 1) % h, :] *= 0.6
    rgb = shade(rgb, f)
    # chipped paint -> bare steel, more likely near plate edges
    chip = fbm(w, h, 10, 3, rng) > STEEL_CHIP_THRESHOLD
    steel_f = 0.38 + 0.22 * fbm(w, h, 12, 2, rng)
    steel = to_rgb(steel_f, "steel_blue")
    rgb = np.where(chip[..., None], steel, rgb)
    # scratches: thin lighter lines
    ov = Overlay(w, h)
    light = ramp_colour("military_green", 0.85)
    for _ in range(STEEL_SCRATCHES):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        dx, dy = rng.uniform(-10, 10), rng.uniform(-4, 4)
        ov.line([(x, y), (x + dx, y + dy)], light + (120,), 0.5)
    # rivets at plate corners (inset) with rust streak under each
    rust_mask = np.zeros((h, w))
    hi = ramp_colour("military_green", 0.95)
    lo = ramp_colour("military_green", 0.15)
    for py in range(0, h, PLATE):
        for px in range(0, w, PLATE):
            for cx, cy in ((px + RIVET_INSET, py + RIVET_INSET), (px + PLATE - RIVET_INSET, py + RIVET_INSET),
                           (px + RIVET_INSET, py + PLATE - RIVET_INSET), (px + PLATE - RIVET_INSET, py + PLATE - RIVET_INSET)):
                ov.ellipse(cx - RIVET_R, cy - RIVET_R, cx + RIVET_R, cy + RIVET_R, fill=lo)
                ov.ellipse(cx - RIVET_R + 0.6, cy - RIVET_R + 0.6, cx + RIVET_R - 0.4, cy + RIVET_R - 0.4, fill=hi)
                ys = np.arange(h)[:, None]
                dyy = (ys - cy) % h
                col = np.exp(-((np.arange(w)[None, :] - cx) ** 2) / 1.2)
                rust_mask += 0.35 * np.exp(-dyy / 7.0) * (dyy > RIVET_R) * col * rng.uniform(0.3, 1.0)
    rgb = ov.composite(rgb)
    rgb = blend(rgb, ramp_colour("rust_brown", 0.45), np.clip(rust_mask, 0, 0.6))
    return rgb


def tex_door1():
    rng = rng_for(5)
    w, h = WIDE_W, WALL_H
    steel_f = 0.40 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.2 + grain(w, h, rng, 0.03)
    rgb = to_rgb(steel_f, "steel_blue")
    # painted leaf
    leaf = np.zeros((h, w), dtype=bool)
    leaf[DOOR_FRAME:h - DOOR_FRAME, DOOR_FRAME:w - DOOR_FRAME] = True
    green_f = STEEL_GREEN_MID + (fbm(w, h, 3, 5, rng, 0.5) - 0.5) * 0.25 + grain(w, h, rng, 0.03)
    green = to_rgb(green_f, "military_green")
    chip = fbm(w, h, 9, 3, rng) > 0.74
    rgb = np.where((leaf & ~chip)[..., None], green, rgb)
    # frame bevel: light outer-top/left, dark inner
    f = np.ones((h, w))
    f[DOOR_FRAME - 1, DOOR_FRAME - 1:w - DOOR_FRAME + 1] = 0.5
    f[DOOR_FRAME:h - DOOR_FRAME, DOOR_FRAME - 1] = 0.5
    f[h - DOOR_FRAME, DOOR_FRAME - 1:w - DOOR_FRAME + 1] = 1.3
    f[DOOR_FRAME:h - DOOR_FRAME, w - DOOR_FRAME] = 1.3
    f[DOOR_FRAME, DOOR_FRAME:w - DOOR_FRAME] = 0.75   # leaf recessed: shadow under frame
    f[1, :] *= 1.25
    f[:, 1] *= 1.25
    f[0, :] *= 0.55
    f[:, 0] *= 0.55
    f[h - 1, :] *= 0.55
    f[:, w - 1] *= 0.55
    # reinforcing ribs
    for ry in DOOR_RIB_YS:
        f[ry, DOOR_FRAME:w - DOOR_FRAME] *= 1.3
        f[ry + 1:ry + DOOR_RIB_H - 1, DOOR_FRAME:w - DOOR_FRAME] *= 1.08
        f[ry + DOOR_RIB_H - 1, DOOR_FRAME:w - DOOR_FRAME] *= 0.5
        f[ry + DOOR_RIB_H, DOOR_FRAME:w - DOOR_FRAME] *= 0.75
    rgb = shade(rgb, f)
    ov = Overlay(w, h)
    hi = ramp_colour("steel_blue", 0.95)
    lo = ramp_colour("steel_blue", 0.12)
    mid = ramp_colour("steel_blue", 0.70)
    # frame rivets every 16 px
    for i in range(0, w, 16):
        for cx, cy in ((i + 8, DOOR_FRAME / 2), (i + 8, h - DOOR_FRAME / 2)):
            ov.ellipse(cx - RIVET_R, cy - RIVET_R, cx + RIVET_R, cy + RIVET_R, fill=lo)
            ov.ellipse(cx - RIVET_R + 0.6, cy - RIVET_R + 0.6, cx + RIVET_R - 0.4, cy + RIVET_R - 0.4, fill=hi)
    for j in range(DOOR_FRAME, h - DOOR_FRAME, 16):
        for cx, cy in ((DOOR_FRAME / 2, j + 8), (w - DOOR_FRAME / 2, j + 8)):
            ov.ellipse(cx - RIVET_R, cy - RIVET_R, cx + RIVET_R, cy + RIVET_R, fill=lo)
            ov.ellipse(cx - RIVET_R + 0.6, cy - RIVET_R + 0.6, cx + RIVET_R - 0.4, cy + RIVET_R - 0.4, fill=hi)
    # locking wheel
    cx, cy = WHEEL_CENTER
    ov.ellipse(cx - WHEEL_R_OUT, cy - WHEEL_R_OUT + 1, cx + WHEEL_R_OUT, cy + WHEEL_R_OUT + 1, fill=lo)  # shadow
    ov.arc_ring(cx, cy, WHEEL_R_OUT, WHEEL_R_IN, 0, 360, mid)
    ov.arc_ring(cx, cy, WHEEL_R_OUT - 1, WHEEL_R_IN + 1, 200, 340, hi)  # top highlight
    for k in range(WHEEL_SPOKES):
        ang = np.deg2rad(k * 180 / WHEEL_SPOKES)
        dx, dy = np.cos(ang) * WHEEL_R_IN, np.sin(ang) * WHEEL_R_IN
        ov.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], mid, 2.2)
    ov.ellipse(cx - 4, cy - 4, cx + 4, cy + 4, fill=lo)
    ov.ellipse(cx - 3, cy - 3, cx + 3, cy + 3, fill=hi)
    # faded stencils: red star left, "7" right
    red = ramp_colour("flag_red", 0.62) + (170,)
    ov.polygon(star_points(30, 30, 9), red)
    cream = ramp_colour("cream_yellow", 0.88) + (180,)
    ov.text(100, 30, DOOR_STENCIL, DOOR_STENCIL_SIZE, cream, font=FONT_POSTER)
    rgb = ov.composite(rgb)
    # hazard stripe along the bottom of the leaf
    stripe = np.zeros((h, w))
    ys, xs = np.mgrid[0:h, 0:w]
    band = (ys >= h - DOOR_FRAME - 8) & (ys < h - DOOR_FRAME - 2) & leaf
    diag = ((xs + ys) // 6) % 2 == 0
    stripe[band & diag] = 1.0
    rgb = blend(rgb, ramp_colour("hazard_yellow", 0.8), stripe * 0.85)
    rgb = blend(rgb, (0, 0, 0), (band & ~diag) * 0.6)
    return rgb


def paper(w, h, rng, base_rgb):
    """Age a flat colour like printed paper: fibre grain + grime blotches."""
    age = 1 - POSTER_AGE * (fbm(w, h, 3, 4, rng) - 0.3) + grain(w, h, rng, 0.03)
    base = np.tile(np.array(base_rgb, dtype=np.float64)[None, None, :], (h, w, 1))
    return shade(base, age)


def tex_postr1():
    rng = rng_for(6)
    w, h = WALL_W, WALL_H
    rgb = paper(w, h, rng, ramp_colour("flag_red", POSTER_RED))
    ov = Overlay(w, h)
    cream = ramp_colour("cream_yellow", POSTER_CREAM)
    black = (0, 0, 0)
    # constructivist black wedge at the bottom
    ov.polygon([(0, h), (w, h), (w, 94), (0, 102)], black)
    # thin cream frame = poster edge
    ov.rect(0, 0, w, h, outline=cream, width=1)
    # portrait medallion
    cx, cy = LENIN_CIRCLE_C
    ov.ellipse(cx - LENIN_CIRCLE_R, cy - LENIN_CIRCLE_R, cx + LENIN_CIRCLE_R, cy + LENIN_CIRCLE_R, fill=cream)
    scale = (LENIN_CIRCLE_R * 2 * 0.78) / 140.0
    px0 = cx - 50 * scale + 2
    py0 = cy - 70 * scale + 4
    pts = [(px0 + x * scale, py0 + y * scale) for x, y in LENIN_PROFILE]
    ov.polygon(pts, black)
    # a red ray crossing behind the medallion for dynamism
    ov.polygon([(0, 30), (w, 20), (w, 24), (0, 34)], black)
    ov.text(w / 2, 14, LENIN_TEXT_TOP, LENIN_TEXT_SIZE, cream, max_width=w - 6)
    ov.text(w / 2, 112, LENIN_TEXT_BOTTOM, LENIN_TEXT_SIZE, cream, max_width=w - 6)
    rgb = ov.composite(rgb)
    return shade(rgb, 1 - 0.08 * (fbm(w, h, 4, 3, rng) - 0.5))


def rot(points, angle_deg, cx, cy):
    a = np.deg2rad(angle_deg)
    c, s = np.cos(a), np.sin(a)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in points]


def tex_postr2():
    rng = rng_for(7)
    w, h = WIDE_W, WALL_H
    rgb = paper(w, h, rng, ramp_colour("flag_red", POSTER_RED))
    ov = Overlay(w, h)
    cream = ramp_colour("cream_yellow", POSTER_CREAM)
    black = (0, 0, 0)
    gold = ramp_colour("hazard_yellow", 0.9)
    # radiating cream rays from the lower-left corner
    for k in range(5):
        a0 = -8 - k * 14
        ov.polygon(rot([(0, 0), (190, -3), (190, 3)], a0, 6, 96), cream + (90,))
    # stars
    for _ in range(COSMO_STARS):
        sx, sy = rng.uniform(4, w - 4), rng.uniform(4, 86)
        r = rng.uniform(0.8, 2.2)
        ov.polygon(star_points(sx, sy, r), cream)
    # rocket: body along +x, rotated 45 degrees up-right
    body = [(-30, -5), (18, -5), (30, 0), (18, 5), (-30, 5)]
    fin_top = [(-30, -5), (-22, -5), (-16, -12), (-30, -12)]
    fin_bot = [(-30, 5), (-22, 5), (-16, 12), (-30, 12)]
    flame = [(-30, -3), (-48, 0), (-30, 3)]
    rcx, rcy = 60, 50
    ov.polygon(rot(flame, -45, rcx, rcy), gold)
    ov.polygon(rot([(-30, -2), (-40, 0), (-30, 2)], -45, rcx, rcy), cream)
    ov.polygon(rot(fin_top, -45, rcx, rcy), black)
    ov.polygon(rot(fin_bot, -45, rcx, rcy), black)
    ov.polygon(rot(body, -45, rcx, rcy), cream)
    ov.polygon(rot([(-30, 0), (18, 0), (30, 0), (18, 5), (-30, 5)], -45, rcx, rcy), black + (90,))
    ov.polygon(rot([(18, -5), (30, 0), (18, 0)], -45, rcx, rcy), black)
    # big ground star behind text
    ov.polygon(star_points(16, 104, 13), gold)
    # text block on a black band
    ov.polygon([(0, 92), (w, 92), (w, h), (0, h)], black + (200,))
    ov.text(w / 2 + 6, 101, COSMO_LINE1, COSMO_TEXT_SIZE, cream, max_width=w - 34)
    ov.text(w / 2 + 6, 118, COSMO_LINE2, COSMO_TEXT_SIZE, cream, max_width=w - 34)
    ov.rect(0, 0, w, h, outline=cream, width=1)
    rgb = ov.composite(rgb)
    return shade(rgb, 1 - 0.08 * (fbm(w, h, 4, 3, rng) - 0.5))


def floor_concrete(rng, mid=FLOOR_MID):
    rgb = concrete(FLAT, FLAT, rng, mid)
    # oil / wear blotches
    rgb = shade(rgb, 1 - 0.18 * np.clip(fbm(FLAT, FLAT, 2, 3, rng) - 0.55, 0, 1) * 4)
    return rgb


def cracks(rgb, rng, n):
    """Thin dark cracks: polylines whose heading drifts a little per step."""
    h, w = rgb.shape[:2]
    ov = Overlay(w, h)
    dark = ramp_colour("concrete_cold", 0.18) + (200,)
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        ang = rng.uniform(0, 2 * np.pi)
        pts = [(x, y)]
        for _ in range(rng.integers(5, 9)):
            ang += rng.uniform(-0.7, 0.7)
            step = rng.uniform(3, 6)
            x, y = x + np.cos(ang) * step, y + np.sin(ang) * step
            pts.append((x, y))
        ov.line(pts, dark, CRACK_WIDTH)
    return ov.composite(rgb)


def tex_flr1():
    rng = rng_for(8)
    rgb = cracks(floor_concrete(rng), rng, FLOOR_CRACKS)
    lum = rgb.mean(axis=2) / 255.0
    mask = np.zeros((FLAT, FLAT))
    mask[:, FLOOR_LINE_X0:FLOOR_LINE_X1] = 1.0
    mask *= fbm(FLAT, FLAT, 4, 3, rng) > FLOOR_LINE_WEAR
    yellow = np.array(ramp_colour("hazard_yellow", 0.82), dtype=np.float64)
    painted = np.clip(yellow[None, None, :] * (0.6 + 0.8 * lum)[..., None], 0, 255)
    return np.where(mask[..., None] > 0, painted, rgb).astype(np.uint8)


def tex_flr2():
    rng = rng_for(9)
    return cracks(floor_concrete(rng), rng, FLOOR_CRACKS + 1)


def tex_flr3():
    rng = rng_for(10)
    w = h = FLAT
    n = FLAT // TILE
    tones = 0.50 + rng.uniform(-0.07, 0.07, (n, n))
    field = np.repeat(np.repeat(tones, TILE, 0), TILE, 1)
    field += (fbm(w, h, 8, 3, rng) - 0.5) * 0.12 + grain(w, h, rng, 0.03)
    rgb = to_rgb(field, "concrete_cold")
    # some tiles are the warm beige variant (two-tone Soviet floors)
    warm = rng.random((n, n)) < 0.3
    warm_mask = np.repeat(np.repeat(warm, TILE, 0), TILE, 1)
    rgb = np.where(warm_mask[..., None], to_rgb(field + 0.05, "plaster_warm"), rgb)
    f = np.ones((h, w))
    for k in range(0, w, TILE):
        f[:, k:k + TILE_GROUT] = 0.45          # grout
        f[:, (k + TILE_GROUT) % w] *= 1.12     # lit tile edge
        f[k:k + TILE_GROUT, :] = 0.45
        f[(k + TILE_GROUT) % h, :] *= 1.12
        f[(k - 1) % h, :] *= 0.8               # shadow edge
        f[:, (k - 1) % w] *= 0.8
    rgb = shade(rgb, f)
    return cracks(rgb, rng, 1)


def ceiling_panel(rng):
    rgb = concrete(FLAT, FLAT, rng, CEIL_MID)
    f = np.ones((FLAT, FLAT))
    f[0, :] = JOINT_DARK
    f[1, :] = 0.8
    f[:, 0] = JOINT_DARK
    f[:, 1] = 0.8
    f[FLAT - 1, :] *= 1.1
    f[:, FLAT - 1] *= 1.1
    return shade(rgb, f)


def tex_ceil1():
    rng = rng_for(11)
    rgb = ceiling_panel(rng)
    x0, y0, x1, y1 = LAMP_HOUSING
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    ys, xs = np.mgrid[0:FLAT, 0:FLAT]
    d = np.sqrt(((xs - cx) / 1.6) ** 2 + (ys - cy) ** 2)
    glow = np.clip(1 - d / LAMP_GLOW_R, 0, 1) ** 1.5 * 0.45
    rgb = blend(rgb, ramp_colour("cream_yellow", 0.9), glow)
    ov = Overlay(FLAT, FLAT)
    ov.rect(x0, y0, x1, y1, fill=ramp_colour("steel_blue", 0.35))
    ov.rect(x0, y0, x1, y0 + 1, fill=ramp_colour("steel_blue", 0.6))
    tx0, ty0, tx1, ty1 = LAMP_TUBE
    ov.rect(tx0, ty0, tx1, ty1, fill=ramp_colour("cream_yellow", 0.97))
    ov.rect(tx0 + 1, ty0 + 3, tx1 - 1, ty1 - 3, fill=(255, 255, 255))
    ov.rect(tx0, ty1 - 1, tx1, ty1, fill=ramp_colour("cream_yellow", 0.7))
    return ov.composite(rgb)


def tex_ceil2():
    rng = rng_for(12)
    rgb = ceiling_panel(rng)
    stain = np.clip(fbm(FLAT, FLAT, 2, 4, rng) - 0.58, 0, 1) * 2.2
    return blend(rgb, ramp_colour("rust_brown", 0.3), np.clip(stain, 0, 0.5))


# ============================================================== manifest
# lump, builder, kind, description EN, description RU, extra notes EN/RU
TEXTURES = [
    ("SDCONC1", tex_conc1, "wall",
     "Prefab concrete wall panels in running bond, grime under the joints.",
     "Стеновые панели из сборного железобетона вперевязку, грязь под швами."),
    ("SDCONC2", tex_conc2, "wall",
     "Same concrete with a worn painted red stripe at mid height (barracks corridors).",
     "Тот же бетон с потёртой красной полосой на середине высоты (коридоры казарм)."),
    ("SDSTAR1", tex_star1, "wall",
     "Concrete with a painted plaque: gold star and hammer and sickle on red.",
     "Бетон с нарисованной табличкой: золотая звезда и серп и молот на красном."),
    ("SDSTEL1", tex_stel1, "wall",
     "Military-green riveted steel plates, chipped paint, rust under rivets (hangar).",
     "Клёпаные стальные листы военно-зелёного цвета, сколы краски, ржавчина под заклёпками (ангар)."),
    ("SDDOOR1", tex_door1, "wall",
     "Bunker steel door: riveted frame, green leaf, locking wheel, faded star and '7' stencil, hazard stripe.",
     "Стальная дверь бункера: клёпаная рама, зелёное полотно, запорное колесо, выцветшие трафареты звезды и «7», сигнальная полоса."),
    ("SDPOSTR1", tex_postr1, "wall",
     "Propaganda poster: constructivist Lenin profile in a cream medallion on red, text ЛЕНИН ЖИВ.",
     "Агитплакат: конструктивистский профиль Ленина в кремовом медальоне на красном, текст ЛЕНИН ЖИВ."),
    ("SDPOSTR2", tex_postr2, "wall",
     "Cosmonautics mural: rocket over red with cream rays and stars, text СЛАВА СОВЕТСКОЙ КОСМОНАВТИКЕ.",
     "Панно о космонавтике: ракета на красном с кремовыми лучами и звёздами, текст СЛАВА СОВЕТСКОЙ КОСМОНАВТИКЕ."),
    ("SDFLR1", tex_flr1, "flat",
     "Hangar concrete floor with a worn yellow lane line (continuous when tiled).",
     "Бетонный пол ангара с потёртой жёлтой разметкой (непрерывной при повторе)."),
    ("SDFLR2", tex_flr2, "flat",
     "Plain hangar concrete floor with cracks and oil wear.",
     "Простой бетонный пол ангара с трещинами и масляными пятнами."),
    ("SDFLR3", tex_flr3, "flat",
     "Grey Soviet floor tiles, two-tone, dark grout (barracks).",
     "Серая советская напольная плитка, двухцветная, тёмные швы (казармы)."),
    ("SDCEIL1", tex_ceil1, "flat",
     "Concrete ceiling panel with a fluorescent lamp in a steel housing.",
     "Бетонная потолочная панель с люминесцентной лампой в стальном корпусе."),
    ("SDCEIL2", tex_ceil2, "flat",
     "Plain concrete ceiling panel with a damp stain.",
     "Простая бетонная потолочная панель с пятном сырости."),
]

FONT_NOTE_EN = ("Cyrillic text rendered with macOS system fonts: Impact.ttf (poster headlines, "
                "a condensed grotesque close to Soviet poster lettering) and Arial Narrow Bold.ttf "
                "(small text). Both are system fonts, not redistributed: only the rasterised pixels ship.")
FONT_NOTE_RU = ("Кириллический текст набран системными шрифтами macOS: Impact.ttf (заголовки плакатов, "
                "узкий гротеск, близкий к советскому плакатному шрифту) и Arial Narrow Bold.ttf "
                "(мелкий текст). Шрифты не распространяются: в игру попадают только растровые пиксели.")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for i, (lump, builder, kind, desc_en, desc_ru) in enumerate(TEXTURES, start=1):
        assert len(lump) <= 8 and lump.isupper() and lump.startswith("SD"), lump
        rgb = builder()
        h, w = rgb.shape[:2]
        path = OUT_DIR / f"{lump}.png"
        img = save_indexed(rgb, path)
        colours = len(set(img.get_flattened_data()))
        entries.append({
            "lump": lump, "kind": kind, "set": SET_NAME, "width": w, "height": h,
            "file": str(path.relative_to(PROJECT_ROOT)),
            "script": SCRIPT_REL, "seed": BATCH_SEED + i, "seed_offset": i,
            "colours_used": colours,
            "seam_score": round(tiling_seam_score(rgb), 2),
            "description_en": desc_en, "description_ru": desc_ru,
            "uses_font": builder in (tex_postr1, tex_postr2, tex_door1),
        })
        print(f"{lump:9s} {w:3d}x{h:3d} {kind:4s} colours={colours:3d} seam={entries[-1]['seam_score']:5.2f}")
    manifest = {
        "batch": 1, "phase": "F2", "set": SET_NAME, "script": SCRIPT_REL,
        "batch_seed": BATCH_SEED, "font_note_en": FONT_NOTE_EN, "font_note_ru": FONT_NOTE_RU,
        "fonts": [FONT_POSTER, FONT_SMALL], "textures": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
