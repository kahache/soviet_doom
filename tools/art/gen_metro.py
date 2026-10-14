"""Batch 2, priority 2 — first pieces of the "metro" set (MAP02).

Run with the project venv:  .venv/bin/python tools/art/gen_metro.py
                    (fill-out drafts: .venv/bin/python tools/art/gen_metro.py --fill)
                    (palette v2 proposals, D45: .venv/bin/python tools/art/gen_metro.py --v2)
                    (the superseded v1 mosaic, history: .venv/bin/python tools/art/gen_metro.py --mosaic-v1)

D56 (CEO, 2026-10-14, "mosaico V2"): SDMOSA1 is approved in palette v2,
cobalt and gold, and the default run builds it so; the v1 panel it replaced
(D42) stays reachable as history with --mosaic-v1. Every other piece,
SDMARB1 included, is still palette v1 and comes out byte for byte as before.

Exploratory, deliberately small: six pieces, just enough for the set to
exist and for the CEO to say whether this is the right underground. The set
is NOT closed here - no corner pieces, no doors, no signage, no escalator.

ART-BIBLE §4 gives the metro its materials: glazed tile, red marble,
mosaic, brass, light 96-128 with bright islands at 160. What it also says
(§3) is that the palette reserves, but does not yet contain, a **marble red**
and **mosaic blues and golds** for exactly this set. The palette v1 was
ratified by the CEO and this script does not touch it, so these six pieces
are built from the ramps that exist:

  marble red   -> flag_red low + rust_brown veining + plaster_warm veining
  mosaic blue  -> steel_blue low  (the only blue in v1; it is a grey-blue,
                  so the mosaic reads slate rather than cobalt)
  mosaic gold  -> hazard_yellow high
  brass        -> hazard_yellow mid with rust_brown in the shadows
  glazed tile  -> plaster_warm high

The honest consequence is on the sheet: the marble and the mosaic are the
two pieces a palette v2 would visibly improve, and v2 is a CEO decision
because it means a new palette version number. Everything else (tile, dado,
brass, granite) sits comfortably inside v1.

Outputs (work/ is gitignored, nothing goes to assets/):
  work/art/batch2/metro/*.png + manifest.json
  work/art/batch2/<stamp>_F2_batch2-metro-first-pieces.html     (EN)
  work/art/batch2/ru/<stamp>_F2_batch2-metro-first-pieces.html  (RU, D7)
"""

from __future__ import annotations

import datetime as dt
import html
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import (  # noqa: E402
    DIMENSION_MULTIPLE, Overlay, blend, fbm, grain, load_palette, quantize, ramp_colour, save_indexed, shade,
    star_points, tiling_seam_score, to_rgb,
)
import palette as palgen  # noqa: E402  (palette versions: v2 ramps for the proposals)
import sheetlib  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SET_NAME = "metro"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "batch2" / SET_NAME
SHEET_DIR = PROJECT_ROOT / "work" / "art" / "batch2"
MANIFEST = OUT_DIR / "manifest.json"
SCRIPT_REL = "tools/art/gen_metro.py"

# Own seed space (gen_soviet_base owns 1977+1..12, gen_switch 2077+1..4).
BATCH_SEED = 1935        # the year the Moscow metro opened: the set's reference
SEED_OFFSET = {"SDTILE1": 1, "SDTILE2": 2, "SDMARB1": 3,
               "SDMOSA1": 4, "SDBRAS1": 5, "SDMFLR1": 6}

WALL_W, WALL_H = 64, 128
WIDE_W = 128
FLAT = 64

# --- glazed tile --------------------------------------------------------
# 8 px tiles: at Doom's scale a wall tile is about a hand's width, and 8
# divides both 64 and 128 so the grid never breaks across a tiling seam.
TILE = 8
TILE_GROUT = 1
TILE_MID = 0.84              # plaster_warm: glazed cream, the metro's light
TILE_JITTER = 0.05           # per-tile tone variation: hand-laid, not printed
TILE_GLAZE = 0.16            # strength of the diagonal glaze highlight
TILE_GROUT_TONE = 0.30       # rust_brown: grout greys to a warm dirt
TILE_CHIP_RATE = 0.016       # fraction of tiles chipped to the bedding mortar
TILE_CHIP_TONE = 0.46        # how far a chipped tile goes towards the mortar:
                             # at 1.0 the chips read as loud brown polka dots
DADO_Y0, DADO_Y1 = 86, 128   # SDTILE2: oil-painted dado, the Soviet corridor
DADO_GREEN = 0.42            # military_green
DADO_RULE = 2                # dark rule separating dado from tile

# --- red marble ---------------------------------------------------------
MARB_BASE = 0.30             # flag_red: deep ox-blood, not signage red
MARB_MOTTLE = 0.16
MARB_VEINS = 7
MARB_VEIN_W = 1.0
MARB_TURB = 0.7              # how much the veins wander
MARB_POLISH = 0.10           # soft vertical sheen of a polished slab
MARB_SLAB_H = 64             # cladding slab height -> joint at mid wall

# --- mosaic -------------------------------------------------------------
TESS = 4                     # tessera size in px; 128/4 = 32 tesserae across
TESS_GROUT = 1
MOSA_GROUND = 0.16           # steel_blue low: the slate-blue ground
MOSA_GOLD = 0.86             # hazard_yellow: the gold of the motif
MOSA_CREAM = 0.88            # cream_yellow: the inner ring and the rays' tips
MOSA_JITTER = 0.07           # per-tessera tone: a mosaic is never flat
MOSA_CENTER = (64, 58)
# The star has to survive being resolved on a 4 px tessera grid: at radius
# 26 with 16 rays around it the whole thing read as a dandelion, not as a
# five-pointed star. Bigger star, fewer and shorter rays, and a clear gap
# between the two so the silhouette closes.
MOSA_STAR_R = 38
MOSA_RAYS = 10
MOSA_RAY_R0, MOSA_RAY_R1 = 48, 60
MOSA_BORDER = 6              # cream border band, top and bottom

# --- brass pilaster -----------------------------------------------------
BRASS_MID = 0.44             # hazard_yellow held down: at 0.60 the pilaster
                             # read as a bar of gold, not as tarnished brass
BRASS_FLUTES = 5
BRASS_FLUTE_DEPTH = 0.30
BRASS_CAP_H = 10
GRILLE_Y0, GRILLE_Y1 = 44, 92
GRILLE_SLATS = 8
GRILLE_DARK = 0.05

# --- granite floor ------------------------------------------------------
GRAN_MID = 0.42              # concrete_cold: darker than the base-set floors
GRAN_SPECKLE = 0.11          # fraction of pixels that are a grain of feldspar
GRAN_SPECKLE_AMP = 0.26
GRAN_SLAB = 32               # polished slabs, joint every 32 px
GRAN_JOINT = 0.55


def rng_for(lump: str) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + SEED_OFFSET[lump])


# ------------------------------------------------- palette version helpers
# artlib reads palette v1 (palette.json's top-level view, on purpose: the
# approved art must never drift into a later version). A v2 ramp is read
# through palette.py, and only the v2 proposals use one.
def any_to_rgb(field: np.ndarray, ramp_name: str) -> np.ndarray:
    """artlib.to_rgb for a ramp of any palette version (v1 goes to artlib
    itself, so the approved builders are untouched)."""
    if palgen.ramp_version(ramp_name) == 1:
        return to_rgb(field, ramp_name)
    cols = np.array(palgen.ramp_colours(ramp_name), dtype=np.float64)
    idx = np.clip(field, 0, 1) * (len(cols) - 1)
    lo = np.floor(idx).astype(int)
    hi = np.minimum(lo + 1, len(cols) - 1)
    t = (idx - lo)[..., None]
    return np.clip(cols[lo] * (1 - t) + cols[hi] * t, 0, 255).astype(np.uint8)


def any_ramp_colour(ramp_name: str, t: float) -> tuple[int, int, int]:
    """artlib.ramp_colour for a ramp of any palette version."""
    if palgen.ramp_version(ramp_name) == 1:
        return ramp_colour(ramp_name, t)
    cols = palgen.ramp_colours(ramp_name)
    return cols[int(round(max(0.0, min(1.0, t)) * (len(cols) - 1)))]


def quantize_version(rgb: np.ndarray, version: int) -> Image.Image:
    """Snap to one palette version, no dither (artlib.quantize is v1)."""
    if version == 1:
        return quantize(Image.fromarray(rgb, "RGB"))
    cols = palgen.colours(version)
    pimg = Image.new("P", (1, 1))
    pimg.putpalette([v for c in cols for v in c])
    return Image.fromarray(rgb, "RGB").quantize(palette=pimg, dither=Image.Dither.NONE)


# ========================================================== materials
def tile_field(w: int, h: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Glazed tile wall. Returns (rgb, chipped mask).

    The glaze is what separates this from the base set's concrete: every
    tile carries the same diagonal highlight, so a lit corridor gets a
    regular sparkle instead of blotches. Tiles are kept to a narrow value
    band - a metro is bright, and ART-BIBLE §6 needs the wall to stay above
    the enemies' body value.
    """
    ny, nx = h // TILE, w // TILE
    tones = TILE_MID + rng.uniform(-TILE_JITTER, TILE_JITTER, (ny, nx))
    field = np.repeat(np.repeat(tones, TILE, 0), TILE, 1)

    # diagonal glaze: same gradient inside every tile
    yy, xx = np.meshgrid(np.arange(h) % TILE, np.arange(w) % TILE, indexing="ij")
    glaze = 1.0 - (xx + yy) / (2 * (TILE - 1))
    field += (glaze - 0.5) * TILE_GLAZE
    field += grain(w, h, rng, 0.02)
    rgb = to_rgb(np.clip(field, 0, 1), "plaster_warm")

    # chipped tiles: the glaze gone, warm mortar underneath
    chip = rng.random((ny, nx)) < TILE_CHIP_RATE
    chip_mask = np.repeat(np.repeat(chip, TILE, 0), TILE, 1)
    mortar = to_rgb(np.clip(field - 0.30, 0, 1), "rust_brown")
    chipped = (rgb * (1 - TILE_CHIP_TONE) + mortar * TILE_CHIP_TONE).astype(np.uint8)
    rgb = np.where(chip_mask[..., None], chipped, rgb)

    # grout, with a lit lip under each line so the grid has depth
    f = np.ones((h, w))
    grout = np.array(ramp_colour("rust_brown", TILE_GROUT_TONE))
    g = np.zeros((h, w), bool)
    for k in range(0, w, TILE):
        g[:, k:k + TILE_GROUT] = True
        f[:, (k + TILE_GROUT) % w] *= 1.10
    for k in range(0, h, TILE):
        g[k:k + TILE_GROUT, :] = True
        f[(k + TILE_GROUT) % h, :] *= 1.10
    rgb = shade(rgb, f)
    rgb = np.where(g[..., None], grout, rgb).astype(np.uint8)
    # grime gathering in the lower third, as it does on every tiled wall
    dirt = np.clip((np.arange(h)[:, None] / h - 0.55) * 1.6, 0, 1) * fbm(w, h, 3, 3, rng)
    return blend(rgb, ramp_colour("rust_brown", 0.18), np.clip(dirt * 0.45, 0, 0.45)), chip_mask


def tex_tile1() -> np.ndarray:
    """Plain glazed tile wall, floor to ceiling."""
    rgb, _ = tile_field(WALL_W, WALL_H, rng_for("SDTILE1"))
    return rgb


def tex_tile2() -> np.ndarray:
    """Tile above, oil-painted green dado below: the single most Soviet
    interior move there is, and the reason the set needs its own wall rather
    than reusing the base concrete."""
    rng = rng_for("SDTILE2")
    rgb, _ = tile_field(WALL_W, WALL_H, rng)
    h, w = rgb.shape[:2]
    field = DADO_GREEN + (fbm(w, h, 3, 4, rng, 0.5) - 0.5) * 0.12 + grain(w, h, rng, 0.02)
    paint = to_rgb(field, "military_green")
    band = np.zeros((h, w), bool)
    band[DADO_Y0:DADO_Y1, :] = True
    rgb = np.where(band[..., None], paint, rgb).astype(np.uint8)
    # brush wear along the top edge of the paint, and the dark rule above it
    f = np.ones((h, w))
    f[DADO_Y0:DADO_Y0 + DADO_RULE, :] = 0.45
    f[DADO_Y0 + DADO_RULE, :] = 1.25
    rgb = shade(rgb, f)
    scuff = np.clip(fbm(w, h, 6, 3, rng) - 0.62, 0, 1) * 3 * band
    return blend(rgb, ramp_colour("military_green", 0.72), np.clip(scuff, 0, 0.5))


def tex_marb1() -> np.ndarray:
    """Polished red marble cladding.

    Veins are drawn with `line_tiled` so they continue across the tiling
    seam; a vein dying at a slab edge is the one thing that makes fake
    marble obvious. Flagged on the sheet: flag_red is a *signage* red, so
    this stone is more ox-blood than the warm Shrosha marble of the real
    stations. A palette v2 marble ramp is what would fix it.
    """
    return marble_field(WALL_W, WALL_H, rng_for("SDMARB1"))


# The stone's inks: (base ramp, base tone, (cloud ramp, t), (pale vein
# ramp, t), (dark vein ramp, t)). STONE_V1 is the approved SDMARB1 (D42);
# STONE_V2 is the palette-v2 proposal (D45), same seed and same veins.
STONE_V1 = ("flag_red", MARB_BASE, ("rust_brown", 0.12), ("plaster_warm", 0.78), ("rust_brown", 0.10))


def marble_field(w: int, h: int, rng: np.random.Generator, stone=STONE_V1) -> np.ndarray:
    """The SDMARB1 stone at any size (the approved lump is 64x128; D42).
    Factored out unchanged so the station wall SDMARB2 can reuse it;
    tests/test_gen_metro.py holds SDMARB1 to the approved pixels.
    `stone` swaps the inks only: every rng draw is the same, so the v2
    proposal has exactly the v1 veins and differs in colour alone."""
    base_ramp, base, (cloud_ramp, cloud_t), (pale_ramp, pale_t), (dark_ramp, dark_t) = stone
    field = base + (fbm(w, h, 3, 5, rng, 0.6) - 0.5) * MARB_MOTTLE
    field += grain(w, h, rng, 0.02)
    rgb = any_to_rgb(np.clip(field, 0, 1), base_ramp)
    # darker clouding, so the stone has depth before the veins go on
    cloud = np.clip(fbm(w, h, 2, 4, rng) - 0.5, 0, 1) * 1.6
    rgb = blend(rgb, any_ramp_colour(cloud_ramp, cloud_t), np.clip(cloud, 0, 0.45))

    ov = Overlay(w, h)
    pale = any_ramp_colour(pale_ramp, pale_t)
    dark = any_ramp_colour(dark_ramp, dark_t)
    for i in range(MARB_VEINS):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        ang = rng.uniform(-1.0, 1.0) + (np.pi / 2 if i % 2 else 0.0)
        pts = [(x, y)]
        for _ in range(rng.integers(6, 10)):
            ang += rng.uniform(-MARB_TURB, MARB_TURB)
            step = rng.uniform(5, 9)
            x, y = x + np.cos(ang) * step, y + np.sin(ang) * step
            pts.append((x, y))
        colour = pale if i % 3 else dark
        alpha = int(rng.uniform(90, 170))
        ov.line_tiled(pts, colour + (alpha,), MARB_VEIN_W)
    rgb = ov.composite(rgb)

    # polish: a soft sheen down the slab, and the slab joint
    sheen = 1 + MARB_POLISH * np.cos((np.arange(w) / w) * 2 * np.pi)[None, :]
    rgb = shade(rgb, np.repeat(sheen, h, axis=0))
    f = np.ones((h, w))
    for y in (0, MARB_SLAB_H):
        f[y % h] = 0.45
        f[(y + 1) % h] = 1.22
    return shade(rgb, f)


# The mosaic's inks, in motif order (0 ground, 1 gold, 2 cream): (ramp, tone).
# v1 is the panel approved in D42 (slate ground, paint yellow), history since D56.
MOSA_INKS_V1 = (("steel_blue", MOSA_GROUND), ("hazard_yellow", MOSA_GOLD), ("cream_yellow", MOSA_CREAM))

# v2 (proposed under D45, approved in D56): cobalt ground instead of slate,
# smalt gold instead of paint yellow; the cream ring and border stay
# cream_yellow (a v1 ramp). The cobalt ground sits higher on its ramp than
# steel_blue did (0.16): the grout multiply (x0.40) and the sector light
# darken it further, and below ~0.25 cobalt goes black before it reads blue.
MOSA_GROUND_V2 = 0.32
MOSA_GOLD_V2 = 0.88
MOSA_INKS_V2 = (("mosaic_cobalt", MOSA_GROUND_V2), ("mosaic_gold", MOSA_GOLD_V2), ("cream_yellow", MOSA_CREAM))


def tex_mosa1() -> np.ndarray:
    """Mosaic panel 128x128: a star with rays, smalt gold on cobalt (palette
    v2, approved in D56; the star itself is D47's, "as drawn").

    Built the way a mosaic is: the motif is resolved on the TESSERA grid
    (32x32 cells), not on the pixel grid, so every edge steps in whole
    tesserae and the panel reads as set stones rather than as a drawing with
    a grid on top. No tile is a pure palette colour - each gets its own tone
    jitter, which is what makes a real mosaic shimmer.
    """
    return mosaic_panel(rng_for("SDMOSA1"), MOSA_INKS_V2)


def tex_mosa1_v1() -> np.ndarray:
    """History: the same panel in palette v1, gold on slate blue, as approved
    in D42 and replaced by its v2 rendering in D56. Built by --mosaic-v1 and
    for the --v2 sheet's "v1" view; never installed again."""
    return mosaic_panel(rng_for("SDMOSA1"), MOSA_INKS_V1)


def mosaic_panel(rng: np.random.Generator, inks) -> np.ndarray:
    """The SDMOSA1 star panel with the given inks. Same rng draws whatever
    the inks, so the v2 proposal sets the same tesserae as the approved v1
    (the CEO chose this star on 2026-10-14) and differs in colour alone."""
    w = h = WIDE_W
    nx, ny = w // TESS, h // TESS
    cx, cy = MOSA_CENTER[0] / TESS, MOSA_CENTER[1] / TESS
    gy, gx = np.mgrid[0:ny, 0:nx]
    px, py = gx + 0.5, gy + 0.5
    d = np.hypot(px - cx, py - cy)
    ang = np.arctan2(py - cy, px - cx)

    # 0 ground, 1 gold, 2 cream
    motif = np.zeros((ny, nx), int)
    rays = (np.cos(ang * MOSA_RAYS) > 0.25) & (d > MOSA_RAY_R0 / TESS) & (d < MOSA_RAY_R1 / TESS)
    motif[rays] = 1
    star = Image.new("L", (nx, ny), 0)
    ImageDraw.Draw(star).polygon(star_points(cx, cy, MOSA_STAR_R / TESS), fill=255)
    motif[np.asarray(star) > 127] = 1
    ring = (d > (MOSA_STAR_R + 4) / TESS) & (d < (MOSA_STAR_R + 8) / TESS)
    motif[ring] = 2
    motif[:MOSA_BORDER // TESS + 1, :] = 2
    motif[-(MOSA_BORDER // TESS + 1):, :] = 2

    tone = rng.uniform(-MOSA_JITTER, MOSA_JITTER, (ny, nx))
    out = np.zeros((ny, nx, 3), np.uint8)
    for value, (ramp_name, base) in enumerate(inks):
        m = motif == value
        if m.any():
            out[m] = any_to_rgb(np.clip(base + tone, 0, 1), ramp_name)[m]

    rgb = np.repeat(np.repeat(out, TESS, 0), TESS, 1)
    # grout between tesserae, plus a chip of light on each stone's top edge
    f = np.ones((h, w))
    for k in range(0, w, TESS):
        f[:, k:k + TESS_GROUT] = 0.40
        f[:, (k + TESS_GROUT) % w] *= 1.14
    for k in range(0, h, TESS):
        f[k:k + TESS_GROUT, :] = 0.40
        f[(k + TESS_GROUT) % h, :] *= 1.14
    rgb = shade(rgb, f)
    return shade(rgb, 1 - 0.07 * (fbm(w, h, 3, 3, rng) - 0.5))


def tex_bras1() -> np.ndarray:
    """Brass pilaster with a ventilation grille.

    The set's vertical punctuation: fluted brass with a dark grille in the
    middle. Brass is hazard_yellow held low enough that it does not compete
    with the switch's hazard chevrons or with SDFLR1's lane line.
    """
    rng = rng_for("SDBRAS1")
    w, h = WALL_W, WALL_H
    xs = np.arange(w)[None, :]
    flute = np.cos(xs / w * BRASS_FLUTES * 2 * np.pi)
    field = BRASS_MID + flute * BRASS_FLUTE_DEPTH * 0.5
    field = np.repeat(field, h, axis=0)
    field += (fbm(w, h, 3, 4, rng, 0.5) - 0.5) * 0.10 + grain(w, h, rng, 0.02)
    rgb = to_rgb(np.clip(field, 0, 1), "hazard_yellow")
    # tarnish gathering in the flute valleys
    tarnish = np.clip(-flute, 0, 1) * 0.62
    rgb = blend(rgb, ramp_colour("rust_brown", 0.22), np.repeat(tarnish, h, axis=0))

    ov = Overlay(w, h)
    dark = ramp_colour("concrete_cold", GRILLE_DARK)
    ov.rect(2, GRILLE_Y0, w - 2, GRILLE_Y1, fill=dark)
    slat_h = (GRILLE_Y1 - GRILLE_Y0) / GRILLE_SLATS
    for i in range(GRILLE_SLATS):
        y = GRILLE_Y0 + i * slat_h
        ov.rect(3, y + 1, w - 3, y + slat_h * 0.45,
                fill=ramp_colour("hazard_yellow", 0.34))
    for y in (GRILLE_Y0, GRILLE_Y1 - 2):
        ov.rect(1, y - 2, w - 1, y + 2, fill=ramp_colour("hazard_yellow", 0.56))
    # caps: the pilaster is a repeating vertical element, so the caps sit on
    # the wrap edges and a stack of them reads as one continuous column
    for y in (0, h - BRASS_CAP_H):
        ov.rect(0, y, w, y + BRASS_CAP_H, fill=ramp_colour("hazard_yellow", 0.38))
        ov.rect(0, y, w, y + 2, fill=ramp_colour("hazard_yellow", 0.64))
    return ov.composite(rgb)


def tex_mflr1() -> np.ndarray:
    """Polished grey granite floor, 32 px slabs.

    Darker than the base set's hangar floors (ART-BIBLE §5 keeps floors a
    notch under the walls, and a metro's walls are the bright surface), so a
    station reads as a bright box over a dark ground.
    """
    rng = rng_for("SDMFLR1")
    w = h = FLAT
    field = GRAN_MID + (fbm(w, h, 4, 4, rng, 0.5) - 0.5) * 0.10 + grain(w, h, rng, 0.03)
    speckle = rng.random((h, w))
    field = np.where(speckle < GRAN_SPECKLE / 2, field + GRAN_SPECKLE_AMP, field)
    field = np.where(speckle > 1 - GRAN_SPECKLE / 2, field - GRAN_SPECKLE_AMP, field)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    # a few warm grains: granite is not grey all the way down
    warm = rng.random((h, w)) < 0.012
    rgb = np.where(warm[..., None], to_rgb(np.clip(field + 0.1, 0, 1), "rust_brown"), rgb)
    f = np.ones((h, w))
    for k in range(0, w, GRAN_SLAB):
        f[:, k] = GRAN_JOINT
        f[:, (k + 1) % w] *= 1.12
        f[k, :] = GRAN_JOINT
        f[(k + 1) % h, :] *= 1.12
    return shade(rgb, f)


# lump, builder, kind, description EN, description RU
TEXTURES = [
    ("SDTILE1", tex_tile1, "wall",
     "Glazed cream tile wall, 8 px tiles, warm grout, a few chipped tiles, grime low down.",
     "Стена из глазурованной кремовой плитки 8 px, тёплые швы, несколько сколотых плиток, грязь внизу."),
    ("SDTILE2", tex_tile2, "wall",
     "Same tile with an oil-painted military-green dado below a dark rule.",
     "Та же плитка с панелью, окрашенной военно-зелёной масляной краской, под тёмной линией."),
    ("SDMARB1", tex_marb1, "wall",
     "Polished red marble cladding, pale and dark veins that cross the tiling seam, slab joint at mid height.",
     "Полированная облицовка из красного мрамора, светлые и тёмные прожилки, переходящие через шов, стык плит на середине высоты."),
    ("SDMOSA1", tex_mosa1, "wall",
     "Mosaic panel 128x128: smalt-gold star and rays on a cobalt ground, cream border, resolved on the "
     "tessera grid. Palette v2 (D56).",
     "Мозаичное панно 128x128: звезда с лучами из золотой смальты на кобальтовом фоне, кремовый бордюр, "
     "набрано по сетке смальты. Палитра v2 (D56)."),
    ("SDBRAS1", tex_bras1, "wall",
     "Fluted brass pilaster with a ventilation grille and caps on the wrap edges.",
     "Каннелированный латунный пилястр с вентиляционной решёткой и капителями на краях повтора."),
    ("SDMFLR1", tex_mflr1, "flat",
     "Polished grey granite floor, 32 px slabs, feldspar speckle.",
     "Полированный пол из серого гранита, плиты 32 px, вкрапления полевого шпата."),
]

# Palette version each approved lump is quantised to; absent = v1. Only the
# CEO moves a lump to v2 (D56: SDMOSA1, "mosaico V2"; SDMARB1 stays v1).
LUMP_PALETTE = {"SDMOSA1": 2}


def palette_version(lump: str) -> int:
    return LUMP_PALETTE.get(lump, 1)


def quantize_lump(lump: str, rgb: np.ndarray) -> Image.Image:
    """Quantise a lump to the palette version it was approved in. For a v1
    lump this is artlib.quantize, so its bytes are what save_indexed wrote."""
    return quantize_version(rgb, palette_version(lump))


def save_lump(lump: str, rgb: np.ndarray, path: Path) -> Image.Image:
    """artlib.save_indexed, in the lump's own palette version."""
    h, w = rgb.shape[:2]
    assert w % DIMENSION_MULTIPLE == 0 and h % DIMENSION_MULTIPLE == 0, (w, h)
    img = quantize_lump(lump, rgb)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)
    return img


# Pieces the palette v1 visibly limits; quoted on the sheet so the CEO can
# decide whether a palette v2 is worth a new version number (D45). SDMOSA1
# went to v2 in D56, so its card no longer prints the note.
PALETTE_LIMITED = {
    "SDMARB1": ("flag_red is a signage red, so this stone is ox-blood rather than the warm "
                "Shrosha marble of the real stations; a v2 'marble red' ramp would fix it",
                "flag_red — красный вывесок, поэтому камень получился цвета бычьей крови, а не тёплого "
                "шрошинского мрамора настоящих станций; помогла бы рампа «мраморный красный» в v2"),
    "SDMOSA1": ("steel_blue is the only blue in v1 and it is a grey-blue, so the ground reads slate "
                "instead of cobalt; a v2 'mosaic blue' ramp would fix it",
                "steel_blue — единственный синий в v1, и он серо-синий, поэтому фон читается как сланец, "
                "а не кобальт; помогла бы рампа «мозаичный синий» в v2"),
}


# ===================================================== fill-out (drafts)
# The CEO approved the direction and the six pieces above (D42). What
# follows fills the set out for the next gate, still inside palette v1:
# palette v2 (marble red, cobalt, gold) and the mosaic motif (star or
# figure) are open with the CEO, so nothing here depends on either. No
# piece carries a star, a figure or a word.
#
# Seeds continue the D42 offsets (7..16), so the six approved seeds never
# move. Outputs go to their own folder, FILL_DIR, so a --fill run never
# rewrites the approved drafts in OUT_DIR.
FILL_DIR = PROJECT_ROOT / "work" / "art" / "batch2" / "metro_fill"
FILL_MANIFEST = FILL_DIR / "manifest.json"
FILL_SEED_OFFSET = {"SDMFLR2": 7, "SDMFLR3": 8, "SDMEDG1": 9, "SDTUNL1": 10,
                    "SDTUBB1": 11, "SDRAIL1": 12, "SDMCEIL1": 13, "SDMCEIL2": 14,
                    "SDMARB2": 15, "SDTILE3": 16}
SEED_OFFSET.update(FILL_SEED_OFFSET)
SHORT_H = 64                 # SDMEDG1: a platform face is lower than a wall

# --- granite, shared by the new floors (SDMFLR1 keeps its own code) ------
GRAN_PALE = 0.66             # the pale slab of the checker / the coping stone
CHECK_SLAB = 32              # SDMFLR2: one slab of each tone per half-tile

# --- platform edge (SDMFLR3 top, SDMEDG1 face) ---------------------------
# Rows of the edge flat, from the platform (row 0) to the lip (row 63):
# dark granite, the painted warning line, then pale coping slabs.
EDGE_LINE_Y0, EDGE_LINE_Y1 = 36, 42      # painted line, 6 px
EDGE_COPING_Y0 = 46                      # pale coping from here to the lip
EDGE_LIP = 2                             # dark chamfer on the lip itself
EDGE_LINE_TONE = 0.80                    # hazard_yellow: worn paint, not new
EDGE_WEAR = 0.35                         # how much of the line is scuffed
FACE_COPING_H = 6                        # SDMEDG1: the coping's front edge
FACE_SHADOW_H = 3                        # its shadow on the face below
FACE_STRIPE_Y0, FACE_STRIPE_Y1 = 12, 24  # chevron band on the face
STRIPE_PERIOD = 16                       # divides 64: the chevrons tile
FACE_TONE = 0.30                         # concrete_cold: the face is dark

# --- tunnel concrete -----------------------------------------------------
TUNL_MID = 0.40              # darker than any station surface
TUNL_BOARD = 16              # formwork board height, the cast's own lines
TUNL_STREAKS = 0.22          # strength of the damp streaks
CABLE_RUNS = ((38, 3), (58, 2))          # (top y, cables) of each bundle
CABLE_D = 3                  # cable diameter in px
BRACKET_EVERY = 32           # one bracket per 32 px, two per tile
BRACKET_W = 3

# --- tubbing (cast-iron lining rings) -----------------------------------
TUBB_W, TUBB_H = 128, 128
TUBB_RING = 64               # ring width -> one vertical flange per 64 px
TUBB_SEG = 64                # segment height -> one horizontal joint per 64 px
TUBB_FLANGE = 4
TUBB_RIBS = 2                # stiffening ribs inside each segment
TUBB_BOLT_EVERY = 16
TUBB_MID = 0.26              # steel_blue low: cast iron, ART-BIBLE §6.2 keeps
                             # large steel_blue areas under 0.5
TUBB_RUST = 0.45

# --- track bed ----------------------------------------------------------
RAIL_X = ((7, 11), (53, 57))             # rail heads, 4 px wide; one track
                                         # per 64 px tile, gauge ~46 px
SLEEPER_PERIOD = 16          # divides 64
SLEEPER_W = 7
BED_MID = 0.26               # concrete_cold: oily concrete track bed
SLEEPER_TONE = 0.30          # rust_brown: creosoted wood

# --- coffered ceiling ---------------------------------------------------
COFFER_BEAM = 6              # the beam between coffers (half on each edge)
COFFER_STEPS = (4, 4)        # two stepped reveals towards the panel
COFFER_TONES = (0.86, 0.72, 0.64, 0.70)  # beam, step 1, step 2, panel
LAMP_R_RING, LAMP_R_GLASS, LAMP_R_CORE = 15, 11, 5
LAMP_BRASS = 0.44            # same brass as SDBRAS1

# --- station walls ------------------------------------------------------
MARB2_SPLIT = 64             # SDMARB2: tile above, marble below
MARB2_RAIL = 4               # brass rail capping the marble
FRIEZE_Y0, FRIEZE_Y1 = 16, 32            # SDTILE3: ceramic frieze band
FRIEZE_PERIOD = 16
FRIEZE_GREEN = 0.38
FRIEZE_CREAM = 0.86


def granite_field(w: int, h: int, mid: float, rng: np.random.Generator) -> np.ndarray:
    """The SDMFLR1 granite recipe at any tone, as an RGB array without joints."""
    field = mid + (fbm(w, h, 4, 4, rng, 0.5) - 0.5) * 0.10 + grain(w, h, rng, 0.03)
    speckle = rng.random((h, w))
    field = np.where(speckle < GRAN_SPECKLE / 2, field + GRAN_SPECKLE_AMP, field)
    field = np.where(speckle > 1 - GRAN_SPECKLE / 2, field - GRAN_SPECKLE_AMP, field)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    warm = rng.random((h, w)) < 0.012
    return np.where(warm[..., None], to_rgb(np.clip(field + 0.1, 0, 1), "rust_brown"), rgb)


def slab_joints(h: int, w: int, every_x: int | None, every_y: int | None) -> np.ndarray:
    """Shading factor for slab joints: a dark line and a lit line after it."""
    f = np.ones((h, w))
    if every_x:
        for k in range(0, w, every_x):
            f[:, k] = GRAN_JOINT
            f[:, (k + 1) % w] *= 1.12
    if every_y:
        for k in range(0, h, every_y):
            f[k, :] = GRAN_JOINT
            f[(k + 1) % h, :] *= 1.12
    return f


def tex_mflr2() -> np.ndarray:
    """Station hall floor: pale and dark granite in a 32 px checker.

    The hall's floor carries a pattern where the service floor (SDMFLR1)
    is plain, so the two read as two kinds of room. Still darker on
    average than the tile walls (ART-BIBLE §5)."""
    rng = rng_for("SDMFLR2")
    w = h = FLAT
    dark = granite_field(w, h, GRAN_MID, rng)
    pale = granite_field(w, h, GRAN_PALE, rng)
    yy, xx = np.mgrid[0:h, 0:w]
    check = ((yy // CHECK_SLAB) + (xx // CHECK_SLAB)) % 2 == 1
    rgb = np.where(check[..., None], pale, dark)
    return shade(rgb, slab_joints(h, w, CHECK_SLAB, CHECK_SLAB))


def tex_mflr3() -> np.ndarray:
    """Platform edge, seen from above: dark granite, a worn painted warning
    line, pale coping slabs and the dark lip. Tiles along x only; row 63 is
    the edge over the track (rotate the flat in UDMF for other headings)."""
    rng = rng_for("SDMFLR3")
    w = h = FLAT
    rgb = granite_field(w, h, GRAN_MID, rng)
    pale = granite_field(w, h, GRAN_PALE, rng)
    rows = np.arange(h)[:, None] * np.ones((1, w))
    rgb = np.where((rows >= EDGE_COPING_Y0)[..., None], pale, rgb)
    # the painted line: hazard yellow worn through to the stone in patches
    wear = fbm(w, h, 8, 3, rng) < EDGE_WEAR + 0.25
    line = (rows >= EDGE_LINE_Y0) & (rows < EDGE_LINE_Y1)
    paint = to_rgb(np.full((h, w), EDGE_LINE_TONE) + grain(w, h, rng, 0.04), "hazard_yellow")
    rgb = np.where((line & ~wear)[..., None], paint, rgb)
    rgb = np.where((line & wear)[..., None], blend(rgb, ramp_colour("hazard_yellow", 0.55), 0.5 * np.ones((h, w))), rgb)
    # coping slab joints every 32 px, and the lip
    f = np.ones((h, w))
    f[EDGE_COPING_Y0, :] = GRAN_JOINT
    for k in range(0, w, GRAN_SLAB):
        f[EDGE_COPING_Y0:, k] = GRAN_JOINT
        f[EDGE_COPING_Y0:, (k + 1) % w] *= 1.12
    f[h - EDGE_LIP:, :] = 0.55
    return shade(rgb, f)


def chevrons(w: int, h: int, y0: int, y1: int) -> np.ndarray:
    """Mask of 45-degree hazard stripes in rows y0..y1, period STRIPE_PERIOD."""
    yy, xx = np.mgrid[0:h, 0:w]
    m = ((xx + yy) % STRIPE_PERIOD) < STRIPE_PERIOD // 2
    return m & (yy >= y0) & (yy < y1)


def tex_medg1() -> np.ndarray:
    """Platform face (64x64), the wall below the coping that faces the
    track: pale coping edge, its shadow, a black-and-yellow chevron band,
    then dark damp concrete down to the track bed."""
    rng = rng_for("SDMEDG1")
    w, h = WALL_W, SHORT_H
    field = FACE_TONE + (fbm(w, h, 3, 4, rng, 0.55) - 0.5) * 0.12 + grain(w, h, rng, 0.025)
    damp = np.clip(fbm(w, h, 6, 3, rng, 0.5, aspect=4.0) - 0.55, 0, 1) * 0.6
    rgb = to_rgb(np.clip(field - damp, 0, 1), "concrete_cold")
    coping = granite_field(w, h, GRAN_PALE, rng)
    rows = np.arange(h)[:, None] * np.ones((1, w))
    rgb = np.where((rows < FACE_COPING_H)[..., None], coping, rgb)
    yellow = to_rgb(np.full((h, w), EDGE_LINE_TONE) + grain(w, h, rng, 0.04), "hazard_yellow")
    black = to_rgb(np.full((h, w), 0.06) + grain(w, h, rng, 0.02), "concrete_cold")
    band = (rows >= FACE_STRIPE_Y0) & (rows < FACE_STRIPE_Y1)
    stripe = chevrons(w, h, FACE_STRIPE_Y0, FACE_STRIPE_Y1)
    rgb = np.where((band & stripe)[..., None], yellow, rgb)
    rgb = np.where((band & ~stripe)[..., None], black, rgb)
    # scuffs on the paint, from boots and brooms
    scuff = np.clip(fbm(w, h, 8, 3, rng) - 0.66, 0, 1) * 2.5 * band
    rgb = blend(rgb, ramp_colour("concrete_cold", 0.40), np.clip(scuff, 0, 0.6))
    f = np.ones((h, w))
    f[FACE_COPING_H - 1, :] = 0.55
    f[FACE_COPING_H:FACE_COPING_H + FACE_SHADOW_H, :] = 0.62
    f[0, :] = 1.15
    for k in range(0, w, GRAN_SLAB):
        f[:FACE_COPING_H, k] = GRAN_JOINT
    return shade(rgb, f)


def tex_tunl1() -> np.ndarray:
    """Running-tunnel concrete: cast in boards, damp streaks running down,
    two cable bundles on brackets. The cables run along x, so a tunnel wall
    of any length is one continuous run."""
    rng = rng_for("SDTUNL1")
    w, h = WALL_W, WALL_H
    field = TUNL_MID + (fbm(w, h, 3, 5, rng, 0.55) - 0.5) * 0.14 + grain(w, h, rng, 0.03)
    streaks = np.clip(fbm(w, h, 8, 3, rng, 0.5, aspect=6.0) - 0.5, 0, 1) * TUNL_STREAKS * 2
    field -= streaks * np.linspace(0.4, 1.0, h)[:, None]
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    f = np.ones((h, w))
    for k in range(0, h, TUNL_BOARD):
        f[k, :] *= 0.86                      # board joint, faint: cast, not built
    rgb = shade(rgb, f)
    ov = Overlay(w, h)
    rust = ramp_colour("rust_brown", 0.30)
    for top, n in CABLE_RUNS:
        bottom = top + n * CABLE_D + 1
        for bx in range(BRACKET_EVERY // 2, w, BRACKET_EVERY):
            ov.rect(bx - 1, top - 2, bx - 1 + BRACKET_W, bottom + 2, fill=rust)
            ov.rect(bx - 1, bottom + 1, bx - 1 + BRACKET_W, bottom + 2,
                    fill=ramp_colour("rust_brown", 0.12))
        for i in range(n):
            y = top + i * CABLE_D
            ov.rect(0, y, w, y + CABLE_D, fill=ramp_colour("steel_blue", 0.10))
            ov.rect(0, y, w, y + 1, fill=ramp_colour("steel_blue", 0.30))
        ov.rect(0, bottom, w, bottom + 1, fill=ramp_colour("concrete_cold", 0.12))
    return ov.composite(rgb)


def tex_tubb1() -> np.ndarray:
    """Cast-iron tubbing, 128x128: two rings by two segments. Flanges are
    lit on their upper and left faces, the recess holds two ribs, bolts sit
    along every flange. Rust bleeds from the joints."""
    rng = rng_for("SDTUBB1")
    w, h = TUBB_W, TUBB_H
    field = TUBB_MID + (fbm(w, h, 4, 4, rng, 0.5) - 0.5) * 0.10 + grain(w, h, rng, 0.025)
    yy, xx = np.mgrid[0:h, 0:w]
    lx, ly = xx % TUBB_RING, yy % TUBB_SEG
    flange = (lx < TUBB_FLANGE) | (ly < TUBB_FLANGE)
    rib_rows = [TUBB_SEG * (i + 1) // (TUBB_RIBS + 1) for i in range(TUBB_RIBS)]
    rib = np.zeros((h, w), bool)
    for r in rib_rows:
        rib |= (ly >= r - 1) & (ly < r + 1) & ~flange
    field = np.where(flange, field + 0.16, field)
    field = np.where(rib, field + 0.10, field)
    rgb = to_rgb(np.clip(field, 0, 1), "steel_blue")
    # light from above-left: lit lip on top/left of each raised part, shadow below/right
    f = np.ones((h, w))
    f[(ly == 0) | (lx == 0)] = 1.25
    f[(ly == TUBB_FLANGE) & (lx >= TUBB_FLANGE)] = 0.55
    f[(lx == TUBB_FLANGE) & (ly >= TUBB_FLANGE)] = 0.62
    for r in rib_rows:
        f[(ly == r - 1) & ~flange] = 1.18
        f[(ly == r + 1) & ~flange] = 0.62
    rgb = shade(rgb, f)
    # rust streaks bleeding down from the joints
    bleed = np.clip(fbm(w, h, 8, 3, rng, 0.5, aspect=5.0) - 0.52, 0, 1) * 2.2
    near = np.clip(1 - (ly - TUBB_FLANGE) / 26, 0, 1)
    rgb = blend(rgb, ramp_colour("rust_brown", 0.34), np.clip(bleed * near * TUBB_RUST * 2, 0, 0.6))
    ov = Overlay(w, h)
    head = ramp_colour("steel_blue", 0.46)
    for x0 in range(0, w, TUBB_RING):
        for y in range(TUBB_BOLT_EVERY // 2, h, TUBB_BOLT_EVERY):
            if y % TUBB_SEG < TUBB_FLANGE + 2:
                continue
            ov.ellipse(x0 + 0.5, y - 1.5, x0 + 3.5, y + 1.5, fill=head)
    for y0 in range(0, h, TUBB_SEG):
        for x in range(TUBB_BOLT_EVERY // 2, w, TUBB_BOLT_EVERY):
            if x % TUBB_RING < TUBB_FLANGE + 2:
                continue
            ov.ellipse(x - 1.5, y0 + 0.5, x + 1.5, y0 + 3.5, fill=head)
    return ov.composite(rgb)


def tex_rail1() -> np.ndarray:
    """Track bed, one track per 64 px tile, rails along y: oily concrete,
    creosoted sleepers every 16 px, steel tie plates, rails with a polished
    running edge. No contact rail: that is a separate piece if the level
    designer wants live current as a hazard."""
    rng = rng_for("SDRAIL1")
    w = h = FLAT
    field = BED_MID + (fbm(w, h, 4, 4, rng, 0.55) - 0.5) * 0.14 + grain(w, h, rng, 0.04)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    oil = np.clip(fbm(w, h, 4, 3, rng) - 0.55, 0, 1) * 2
    centre = np.zeros((h, w))
    centre[:, RAIL_X[0][1]:RAIL_X[1][0]] = 1.0
    rgb = blend(rgb, ramp_colour("rust_brown", 0.10), np.clip(oil * centre * 0.7, 0, 0.6))
    yy = np.arange(h)[:, None] * np.ones((1, w))
    sleeper = (yy % SLEEPER_PERIOD) < SLEEPER_W
    wood = to_rgb(np.clip(SLEEPER_TONE + (fbm(w, h, 2, 3, rng, 0.5, aspect=0.2) - 0.5) * 0.16
                          + grain(w, h, rng, 0.03), 0, 1), "rust_brown")
    rgb = np.where(sleeper[..., None], wood, rgb)
    f = np.ones((h, w))
    f[(yy % SLEEPER_PERIOD) == SLEEPER_W] = 0.55          # sleeper's shadow
    f[(yy % SLEEPER_PERIOD) == 0] = 1.12                  # its lit edge
    rgb = shade(rgb, f)
    ov = Overlay(w, h)
    for x0, x1 in RAIL_X:
        for y in range(0, h, SLEEPER_PERIOD):            # tie plates
            ov.rect(x0 - 2, y + 1, x1 + 2, y + SLEEPER_W - 1, fill=ramp_colour("steel_blue", 0.14))
        ov.rect(x0 - 1, 0, x1 + 1, h, fill=ramp_colour("steel_blue", 0.20))   # foot
        ov.rect(x0, 0, x1, h, fill=ramp_colour("steel_blue", 0.42))           # web/head
        ov.rect(x0 + 1, 0, x1 - 1, h, fill=ramp_colour("steel_blue", 0.80))   # running edge
    return ov.composite(rgb)


def coffer_field(rng: np.random.Generator) -> np.ndarray:
    """One whitewashed coffer per 64 px flat, beam shared with neighbours."""
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    # distance inward from the nearest beam centre line (the tile edge)
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    half_beam = COFFER_BEAM // 2
    s1 = half_beam + COFFER_STEPS[0]
    s2 = s1 + COFFER_STEPS[1]
    tone = np.select([d < half_beam, d < s1, d < s2],
                     list(COFFER_TONES[:3]), default=COFFER_TONES[3])
    field = tone + (fbm(w, h, 3, 4, rng, 0.5) - 0.5) * 0.06 + grain(w, h, rng, 0.015)
    rgb = to_rgb(np.clip(field, 0, 1), "plaster_warm")
    f = np.ones((h, w))
    for edge in (half_beam, s1, s2):
        f[d == edge] = 0.80                  # a crisp line at every step
    return shade(rgb, f)


def tex_mceil1() -> np.ndarray:
    """Coffered ceiling, whitewashed plaster, two stepped reveals."""
    return coffer_field(rng_for("SDMCEIL1"))


def tex_mceil2() -> np.ndarray:
    """The coffer with a brass ring lamp and an opal glass disc: the
    station's light source, as SDCEIL1 is the base's."""
    rgb = coffer_field(rng_for("SDMCEIL2"))
    c = FLAT / 2
    ov = Overlay(FLAT, FLAT)
    ov.ellipse(c - LAMP_R_RING - 2, c - LAMP_R_RING - 2, c + LAMP_R_RING + 2, c + LAMP_R_RING + 2,
               fill=ramp_colour("plaster_warm", 0.50))                     # soot halo
    ov.ellipse(c - LAMP_R_RING, c - LAMP_R_RING, c + LAMP_R_RING, c + LAMP_R_RING,
               fill=ramp_colour("hazard_yellow", LAMP_BRASS))
    ov.ellipse(c - LAMP_R_RING + 1, c - LAMP_R_RING + 1, c + LAMP_R_RING - 1, c + LAMP_R_RING - 1,
               outline=ramp_colour("hazard_yellow", 0.66), width=1)
    ov.ellipse(c - LAMP_R_GLASS, c - LAMP_R_GLASS, c + LAMP_R_GLASS, c + LAMP_R_GLASS,
               fill=ramp_colour("cream_yellow", 0.92))
    ov.ellipse(c - LAMP_R_CORE, c - LAMP_R_CORE, c + LAMP_R_CORE, c + LAMP_R_CORE,
               fill=(255, 255, 255))
    for k in range(8):                                                   # ring rivets
        a = k * np.pi / 4
        x, y = c + np.cos(a) * (LAMP_R_RING - 2), c + np.sin(a) * (LAMP_R_RING - 2)
        ov.ellipse(x - 1, y - 1, x + 1, y + 1, fill=ramp_colour("rust_brown", 0.20))
    return ov.composite(rgb)


def tex_marb2() -> np.ndarray:
    """Station wall: glazed tile above, red marble below, a brass rail
    capping the marble. The hall's long walls, with SDBRAS1 between bays."""
    rng = rng_for("SDMARB2")
    rgb, _ = tile_field(WALL_W, WALL_H, rng)
    marble = marble_field(WALL_W, WALL_H - MARB2_SPLIT, rng)
    rgb[MARB2_SPLIT:] = marble
    y0 = MARB2_SPLIT - MARB2_RAIL // 2
    ov = Overlay(WALL_W, WALL_H)
    ov.rect(0, y0, WALL_W, y0 + MARB2_RAIL, fill=ramp_colour("hazard_yellow", BRASS_MID))
    ov.rect(0, y0, WALL_W, y0 + 1, fill=ramp_colour("hazard_yellow", 0.66))
    ov.rect(0, y0 + MARB2_RAIL, WALL_W, y0 + MARB2_RAIL + 1, fill=ramp_colour("rust_brown", 0.10))
    return ov.composite(rgb)


def tex_tile3() -> np.ndarray:
    """Tile wall with a ceramic frieze near the top: a chain of cream
    lozenges on green between two dark rules. Geometric on purpose: the
    motif question (star or figure) belongs to the mosaic and stays open."""
    rng = rng_for("SDTILE3")
    rgb, _ = tile_field(WALL_W, WALL_H, rng)
    h, w = rgb.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    band = (yy >= FRIEZE_Y0) & (yy < FRIEZE_Y1)
    cy = (FRIEZE_Y0 + FRIEZE_Y1 - 1) / 2
    lx = (xx % FRIEZE_PERIOD) - (FRIEZE_PERIOD - 1) / 2
    lozenge = (np.abs(lx) + np.abs(yy - cy)) <= (FRIEZE_Y1 - FRIEZE_Y0) / 2 - 1.5
    inner = (np.abs(lx) + np.abs(yy - cy)) <= 2.5
    green = to_rgb(np.clip(FRIEZE_GREEN + grain(w, h, rng, 0.03), 0, 1), "military_green")
    cream = to_rgb(np.clip(FRIEZE_CREAM + grain(w, h, rng, 0.03), 0, 1), "cream_yellow")
    dot = to_rgb(np.full((h, w), 0.30), "flag_red")
    rgb = np.where((band & ~lozenge)[..., None], green, rgb)
    rgb = np.where((band & lozenge & ~inner)[..., None], cream, rgb)
    rgb = np.where((band & inner)[..., None], dot, rgb)
    f = np.ones((h, w))
    for y in (FRIEZE_Y0 - 2, FRIEZE_Y0 - 1, FRIEZE_Y1, FRIEZE_Y1 + 1):
        f[y, :] = 0.40
    f[FRIEZE_Y1 + 2, :] = 1.20
    return shade(rgb, f)


# lump, builder, kind, description
FILL_TEXTURES = [
    ("SDMFLR2", tex_mflr2, "flat",
     "Station hall floor: pale and dark granite in a 32 px checker."),
    ("SDMFLR3", tex_mflr3, "flat",
     "Platform edge from above: dark granite, a worn painted warning line, pale coping, "
     "dark lip on row 63. Tiles along x only."),
    ("SDMEDG1", tex_medg1, "wall",
     "Platform face 64x64 towards the track: coping edge, black-and-yellow chevron band, "
     "dark damp concrete."),
    ("SDTUNL1", tex_tunl1, "wall",
     "Running-tunnel concrete cast in boards, damp streaks, two cable bundles on brackets."),
    ("SDTUBB1", tex_tubb1, "wall",
     "Cast-iron tubbing 128x128: two rings by two segments, flanges, ribs, bolts, rust "
     "bleeding from the joints."),
    ("SDRAIL1", tex_rail1, "flat",
     "Track bed, one track per tile along y: oily concrete, creosoted sleepers every 16 px, "
     "tie plates, rails with a polished running edge."),
    ("SDMCEIL1", tex_mceil1, "flat",
     "Coffered ceiling, whitewashed plaster, two stepped reveals."),
    ("SDMCEIL2", tex_mceil2, "flat",
     "The same coffer with a brass ring lamp and an opal glass disc: the station's light source."),
    ("SDMARB2", tex_marb2, "wall",
     "Station wall: glazed tile above, red marble below, a brass rail on the marble."),
    ("SDTILE3", tex_tile3, "wall",
     "Tile wall with a ceramic frieze: cream lozenges on green between two dark rules."),
]

FILL_FAMILIES = {"MEDG": "metro platform edge", "TUNL": "tunnel lining",
                 "TUBB": "cast-iron tubbing", "RAIL": "track bed",
                 "MCEIL": "metro ceiling"}


# ================================================================= sheet
INTRO_EN = (
    "<b>First six pieces of the metro set (MAP02). Exploration, not a closed set.</b> "
    "The question here is not “approve these six”, it is <b>“is this the right underground?”</b> "
    "&mdash; glazed tile and green dado for the service corridors, red marble and a mosaic for the "
    "station hall, brass for the vertical accents, dark granite underfoot. Say yes to the direction "
    "and I fill it out; say no and we have spent one sheet, not a batch. Two pieces are held back by "
    "the palette and say so on their card: v1 has no true marble red and no cobalt, and v1 is "
    "ratified, so widening it is your call, not mine.")

INTRO_RU = (
    "<b>Первые шесть элементов набора «метро» (MAP02). Разведка, а не закрытый набор.</b> "
    "Вопрос не «одобрить эти шесть», а <b>«то ли это подземелье?»</b>: глазурованная плитка и зелёная "
    "панель для служебных коридоров, красный мрамор и мозаика для зала станции, латунь для "
    "вертикальных акцентов, тёмный гранит под ногами. Скажете «да» направлению — я его дополню; "
    "скажете «нет» — потрачен один лист, а не партия. Два элемента ограничены палитрой, о чём "
    "сказано на их карточках: в v1 нет настоящего мраморного красного и нет кобальта, а v1 "
    "утверждена, поэтому расширять её — ваше решение, не моё.")

LABELS = {
    "en": dict(at1="1x", at4="4x", tile="2x2 tile (2x)", kind="Kind", wall="wall", flat="flat",
               size="Size", seam="Seam ratio", colours="Colours used", origin="Origin",
               limited="Palette v1 limit",
               sec_cards="The six pieces", sec_pal="Palette (ratified v1, untouched)",
               sec_ask="What I need from you",
               ask="<ol><li><b>Direction:</b> is this the metro you had in mind? Tile + dado + marble "
                   "+ mosaic + brass + granite.</li><li><b>Palette v2:</b> do you want a marble red "
                   "and a cobalt/gold mosaic ramp added in the reserved slots? It is a new palette "
                   "version; approved textures keep their colours and are not requantised.</li>"
                   "<li><b>The mosaic motif</b> is a star with rays. The alternative is a cosmonaut "
                   "or a worker figure, which is a bigger piece of work and probably its own "
                   "commission, like the Lenin.</li></ol>",
               footer="Origin (a): procedural, {script}, seed {seed}+offset. Palette docs/art/palette.json v1, "
                      "not modified. Licence: own work, CC BY-NC-SA 4.0 (D15). Nothing here is in assets/."),
    "ru": dict(at1="1x", at4="4x", tile="плитка 2x2 (2x)", kind="Тип", wall="стена", flat="флэт",
               size="Размер", seam="Коэф. шва", colours="Использовано цветов", origin="Происхождение",
               limited="Ограничение палитры v1",
               sec_cards="Шесть элементов", sec_pal="Палитра (утверждённая v1, не изменялась)",
               sec_ask="Что нужно от вас",
               ask="<ol><li><b>Направление:</b> это то метро, которое вы имели в виду? Плитка + панель "
                   "+ мрамор + мозаика + латунь + гранит.</li><li><b>Палитра v2:</b> добавить "
                   "мраморный красный и кобальт с золотом для мозаики в зарезервированные ячейки? "
                   "Это новая версия палитры; одобренные текстуры сохраняют свои цвета и не "
                   "переквантуются.</li><li><b>Сюжет мозаики</b> — звезда с лучами. Альтернатива — "
                   "космонавт или фигура рабочего, но это работа большего объёма и, вероятно, "
                   "отдельный заказ, как Ленин.</li></ol>",
               footer="Происхождение (a): процедурно, {script}, зерно {seed}+смещение. Палитра "
                      "docs/art/palette.json v1, не изменялась. Лицензия: собственная работа, "
                      "CC BY-NC-SA 4.0 (D15). Ничего из этого нет в assets/."),
}


def card(entry: dict, lang: str, files: dict) -> str:
    L = LABELS[lang]
    lump = entry["lump"]
    desc = entry["description_en"] if lang == "en" else entry["description_ru"]
    size = (entry["width"], entry["height"])
    tile_size = (entry["width"] * 2, entry["height"] * 2)
    views = (sheetlib.view(L["at4"], files[lump], sheetlib.ZOOM, size)
             + sheetlib.view(L["at1"], files[lump], 1, size)
             + sheetlib.view(L["tile"], files[lump + "_tile"], 2, tile_size))
    limit = ""
    if lump in PALETTE_LIMITED and palette_version(lump) == 1:
        txt = PALETTE_LIMITED[lump][0 if lang == "en" else 1]
        limit = f'<dt>{L["limited"]}</dt><dd style="white-space:normal;font-family:inherit">{txt}</dd>'
    return (f'<div class="card"><h3>{lump}</h3><p class="desc">{desc}</p>'
            f'<div class="row">{views}</div>'
            f'<dl><dt>{L["kind"]}</dt><dd>{L[entry["kind"]]}</dd>'
            f'<dt>{L["size"]}</dt><dd>{entry["width"]}&times;{entry["height"]}</dd>'
            f'<dt>{L["colours"]}</dt><dd>{entry["colours_used"]}</dd>'
            f'<dt>{L["seam"]}</dt><dd>{entry["seam_score"]}</dd>'
            f'<dt>{L["origin"]}</dt><dd>(a) seed {entry["seed"]}</dd>{limit}</dl></div>')


def build_sheet(lang: str, entries: list[dict], files: dict, stamp: str) -> Path:
    L = LABELS[lang]
    cards = "".join(card(e, lang, files) for e in entries)
    sections = [
        (L["sec_cards"], "", f'<div class="grid">{cards}</div>'),
        (L["sec_pal"], "", sheetlib.palette_ramps(load_palette())),
        (L["sec_ask"], "", f'<div class="ask">{L["ask"]}</div>'),
    ]
    name = f"{stamp}_F2_batch2-metro-first-pieces.html"
    out = (SHEET_DIR / name) if lang == "en" else (SHEET_DIR / "ru" / name)
    title = ("Soviet Doom — metro set, first pieces (batch 2)" if lang == "en"
             else "Soviet Doom — набор «метро», первые элементы (партия 2)")
    sub = ("F2 · MAP02 · exploration, nothing in assets/ yet" if lang == "en"
           else "F2 · MAP02 · разведка, в assets/ пока ничего")
    return sheetlib.write_sheet(
        out, lang=lang, title=title, subtitle=sub,
        intro=INTRO_EN if lang == "en" else INTRO_RU, sections=sections,
        footer=L["footer"].format(script=SCRIPT_REL, seed=BATCH_SEED))


LIGHT_128 = 0.5             # sheet view only: a flat multiply, NOT the engine's colormap

FILL_INTRO = (
    "<b>Metro set, the fill-out: ten drafts for the next gate.</b> You approved the direction and "
    "the first six pieces as drawn in palette v1 (D42: «OK a las 6 piezas de metro»); they are in "
    "<code>assets/</code> now. These ten complete the set a level needs: a station hall floor, the "
    "platform edge (top and face) with its warning stripe, the running tunnel in concrete and in "
    "cast-iron tubbing, the track bed, a coffered ceiling with and without its brass lamp, and two "
    "station walls without any sign. <b>All of it stays inside palette v1</b> and none of it depends "
    "on the two questions still open with you: palette v2 (marble red, cobalt, gold) and the "
    "mosaic's motif (star or figure). No piece carries a star, a figure or a word.")

FILL_ASK = (
    "<ol><li><b>Yes / no per piece.</b> Each card is independent; a no costs one card, not the set.</li>"
    "<li><b>The tunnel:</b> concrete (<code>SDTUNL1</code>), tubbing (<code>SDTUBB1</code>), or both "
    "(tubbing for the deep stretches, concrete near the stations). My recommendation: both.</li>"
    "<li><b>The platform edge:</b> the painted line on <code>SDMFLR3</code> is period-plausible but "
    "the chevrons on <code>SDMEDG1</code> are an industrial idiom, not a 1970s metro one. They are "
    "there for gameplay (the edge must read from the track in the dark). Keep, or plain dark "
    "face?</li></ol>")


def light_view(rgb: np.ndarray, path: Path) -> Path:
    """The quantised texture darkened to about sector light 128, as an RGB
    PNG for the sheet only. Approximate on purpose and labelled so."""
    img = quantize(Image.fromarray(rgb, "RGB")).convert("RGB")
    dark = shade(np.asarray(img), LIGHT_128)
    Image.fromarray(dark, "RGB").save(path, optimize=True)
    return path


def fill_card(entry: dict, files: dict) -> str:
    lump = entry["lump"]
    size = (entry["width"], entry["height"])
    tile_size = (entry["width"] * 2, entry["height"] * 2)
    views = (sheetlib.view("4x", files[lump], sheetlib.ZOOM, size)
             + sheetlib.view("1x", files[lump], 1, size)
             + sheetlib.view("2x2 tile (2x)", files[lump + "_tile"], 2, tile_size)
             + sheetlib.view("~light 128 (2x)", files[lump + "_dark"], 2, size))
    return (f'<div class="card"><h3>{lump}</h3><p class="desc">{html.escape(entry["description_en"])}</p>'
            f'<div class="row">{views}</div>'
            f'<dl><dt>Kind</dt><dd>{entry["kind"]}</dd>'
            f'<dt>Size</dt><dd>{entry["width"]}&times;{entry["height"]}</dd>'
            f'<dt>Colours used</dt><dd>{entry["colours_used"]}</dd>'
            f'<dt>Seam ratio</dt><dd>{entry["seam_score"]}</dd>'
            f'<dt>Origin</dt><dd>(a) seed {entry["seed"]}</dd>'
            f'<dt>Status</dt><dd>draft, proposed</dd></dl></div>')


def set_strip(approved: dict, fill: dict, sizes: dict) -> str:
    """Every metro piece side by side at 2x, walls then flats, approved
    first: a coherence check (same grain, same light), not a mockup."""
    def row(names):
        return '<div class="row" style="align-items:flex-end">' + "".join(
            sheetlib.view(f"{n}{' ✓' if n in approved else ''}",
                          approved.get(n) or fill[n], 2, sizes[n]) for n in names) + "</div>"
    walls = [n for n in list(approved) + list(fill) if sizes[n][1] != FLAT or n in WALL_LUMPS_64]
    flats = [n for n in list(approved) + list(fill) if n not in walls]
    return row(walls) + row(flats)


WALL_LUMPS_64 = {"SDMEDG1"}  # the one wall as short as a flat


def build_fill_sheet(entries: list[dict], files: dict, stamp: str) -> Path:
    cards = "".join(fill_card(e, files) for e in entries)
    approved = {lump: OUT_DIR / f"{lump}.png" for lump, *_ in TEXTURES}
    sizes = {}
    for lump, path in approved.items():
        with Image.open(path) as im:
            sizes[lump] = im.size
    for e in entries:
        sizes[e["lump"]] = (e["width"], e["height"])
    fill = {e["lump"]: files[e["lump"]] for e in entries}
    sections = [
        ("The ten drafts", "", f'<div class="grid">{cards}</div>'),
        ("The whole set together (2x)",
         "The six approved pieces (✓, D42) next to the ten drafts, walls then flats. A coherence "
         "check, not a mockup of a station.", set_strip(approved, fill, sizes)),
        ("What I need from you", "", f'<div class="ask">{FILL_ASK}</div>'),
        ("Palette (ratified v1, untouched)", "", sheetlib.palette_ramps(load_palette())),
    ]
    out = SHEET_DIR / f"{stamp}_F3_batch2-metro-fill.html"
    return sheetlib.write_sheet(
        out, lang="en", title="Soviet Doom — metro set, fill-out drafts (batch 2)",
        subtitle="F3 · metro set · drafts for the CEO, nothing here is in assets/",
        intro=FILL_INTRO, sections=sections,
        footer=(f"Origin (a): procedural, {SCRIPT_REL} --fill, seed {BATCH_SEED}+offset (7-16). "
                "Palette docs/art/palette.json v1, not modified. Licence: own work, CC BY-NC-SA 4.0 "
                "(D15). The '~light 128' view is a flat ×0.5 multiply for orientation, not the "
                "engine's colormap (NOT VERIFIED in GZDoom)."))


def build_fill(textures=None) -> tuple[list[dict], dict]:
    """Render the fill-out drafts into FILL_DIR; returns (entries, files)."""
    FILL_DIR.mkdir(parents=True, exist_ok=True)
    entries, files = [], {}
    for lump, builder, kind, desc in (textures or FILL_TEXTURES):
        assert len(lump) <= 8 and lump.isupper() and lump.startswith("SD"), lump
        rgb = builder()
        h, w = rgb.shape[:2]
        path = FILL_DIR / f"{lump}.png"
        img = save_indexed(rgb, path)
        files[lump] = path
        tile_path = FILL_DIR / f"{lump}_tile2x2.png"
        save_indexed(np.tile(rgb, (2, 2, 1)), tile_path)
        files[lump + "_tile"] = tile_path
        files[lump + "_dark"] = light_view(rgb, FILL_DIR / f"{lump}_light128.png")
        entries.append({
            "lump": lump, "kind": kind, "set": SET_NAME, "width": w, "height": h,
            "file": str(path.relative_to(PROJECT_ROOT)), "script": SCRIPT_REL,
            "seed": BATCH_SEED + SEED_OFFSET[lump], "seed_offset": SEED_OFFSET[lump],
            "colours_used": len(set(img.get_flattened_data())),
            "seam_score": round(tiling_seam_score(rgb), 2),
            "description_en": desc,
        })
        print(f"{lump:9s} {w:3d}x{h:3d} {kind:4s} colours={entries[-1]['colours_used']:3d} "
              f"seam={entries[-1]['seam_score']:5.2f}")
    return entries, files


def main_fill() -> None:
    assert set(FILL_SEED_OFFSET) == {t[0] for t in FILL_TEXTURES}, "FILL_SEED_OFFSET and FILL_TEXTURES disagree"
    assert len(set(SEED_OFFSET.values())) == len(SEED_OFFSET), "two pieces share a seed"
    assert not set(FILL_SEED_OFFSET) & {t[0] for t in TEXTURES}, "a draft reuses an approved name"
    entries, files = build_fill()
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    sheet = build_fill_sheet(entries, files, stamp)
    FILL_MANIFEST.write_text(json.dumps({
        "batch": 2, "phase": "F3", "set": SET_NAME, "script": SCRIPT_REL + " --fill",
        "batch_seed": BATCH_SEED, "status": "drafts for the CEO, palette v1, no motif, no text",
        "new_families": FILL_FAMILIES, "textures": entries,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"sheet EN: {sheet}\nmanifest: {FILL_MANIFEST}")


# ============================================== palette v2 proposals (D45)
# The CEO approved palette v2 (D45, 2026-10-14) and chose the mosaic motif:
# the current star with rays ("Ok a la imagen que has puesto del mosaico").
# The two pieces v1 held back are redrawn in v2 as PROPOSALS, same seed,
# same geometry, new inks only. The approved v1 files stay in assets/ as
# they are (D42); a v2 piece replaces its v1 only after the CEO says so.
# D56 (2026-10-14, "mosaico V2"): the CEO took SDMOSA1_v2, now the approved
# SDMOSA1 that the default run builds; SDMARB1 stays v1. This mode is kept
# to rebuild the proposal sheet as it was asked.
# Outputs go to V2_DIR, never to OUT_DIR, and are never named like an
# approved lump (tests/test_art.py finds assets' sources in work/ by name).
V2_DIR = PROJECT_ROOT / "work" / "art" / "batch2" / "metro_v2"
V2_MANIFEST = V2_DIR / "manifest.json"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
V2_SUFFIX = "_v2"
V2_PALETTE = 2

# Marble: the v1 stone was flag_red 0.30, an ox-blood. marble_red is less
# saturated and warmer, so the same tone sits a little higher on its ramp to
# land on the warm mid-red of the station halls. Veins keep their v1 inks:
# cream veins are what the real stone has, and dark veins go to the
# marble's own low end instead of rust.
MARB_BASE_V2 = 0.32
STONE_V2 = ("marble_red", MARB_BASE_V2, ("marble_red", 0.10), ("plaster_warm", 0.78), ("marble_red", 0.06))

# Mosaic: its v2 inks (MOSA_INKS_V2) sit with the mosaic above, since D56
# made them the approved ones.


def tex_marb1_v2() -> np.ndarray:
    return marble_field(WALL_W, WALL_H, rng_for("SDMARB1"), STONE_V2)


def tex_mosa1_v2() -> np.ndarray:
    """The D45 proposal that D56 approved: the same panel tex_mosa1 builds."""
    return mosaic_panel(rng_for("SDMOSA1"), MOSA_INKS_V2)


# approved lump, its v2 builder, why
V2_TEXTURES = [
    ("SDMARB1", tex_marb1_v2,
     "The approved marble with the same veins, in marble_red: warm red stone instead of flag_red's ox-blood."),
    ("SDMOSA1", tex_mosa1_v2,
     "The approved star with rays, same tesserae, on a cobalt ground with smalt gold instead of slate and paint yellow."),
]


# Lumps whose approved v1 file was replaced by its v2 rendering, with the
# builder of that v1 (history). assets/ no longer holds it, so the --v2
# sheet's "v1" view and --mosaic-v1 render it.
SUPERSEDED_V1 = {"SDMOSA1": tex_mosa1_v1}
HIST_DIR = PROJECT_ROOT / "work" / "art" / "batch2" / "metro_history"
HIST_SUFFIX = "_v1"


def write_v1_history(lump: str, out_dir: Path) -> Path:
    """Render a superseded lump's v1 into out_dir as <LUMP>_v1.png, never
    under the lump's own name (tests/test_art.py finds assets' sources in
    work/ by name). Same quantiser and encoder as the D42 run, so the file
    is byte for byte the v1 that was installed."""
    path = out_dir / f"{lump}{HIST_SUFFIX}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    quantize_version(SUPERSEDED_V1[lump](), 1).save(path, optimize=True)
    return path


def v1_reference(lump: str, out_dir: Path) -> Path:
    """The v1 file a v2 piece is shown against: the installed lump while it
    is still v1, its rendered history once v2 replaced it."""
    if lump in SUPERSEDED_V1:
        return write_v1_history(lump, out_dir)
    return approved_file(lump)


def approved_file(lump: str) -> Path:
    for base in (PROJECT_ROOT / "assets" / "textures" / SET_NAME, PROJECT_ROOT / "assets" / "flats" / SET_NAME):
        if (base / f"{lump}.png").is_file():
            return base / f"{lump}.png"
    raise FileNotFoundError(lump)


def mean_luma(rgb: np.ndarray) -> float:
    r, g, b = (rgb[..., i].astype(np.float64) for i in range(3))
    return float((0.299 * r + 0.587 * g + 0.114 * b).mean())


def save_rgb(rgb: np.ndarray, path: Path) -> Path:
    """A sheet-only view as a plain RGB PNG (its colours are already palette
    colours, or a flat multiply of them for the light view)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgb, "RGB").save(path, optimize=True)
    return path


def rel_path(path: Path) -> str:
    """Repo-relative POSIX path when inside the repo, else the path itself."""
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def build_v2() -> tuple[list[dict], dict]:
    """Render the v2 proposals and their v1 references into V2_DIR. Since
    D56 SDMOSA1's v1 reference is its rendered history, not assets/."""
    V2_DIR.mkdir(parents=True, exist_ok=True)
    v1_set = set(palgen.colours(1))
    entries, files = [], {}
    for lump, builder, why in V2_TEXTURES:
        name = lump + V2_SUFFIX
        q = quantize_version(builder(), V2_PALETTE)
        path = V2_DIR / f"{name}.png"
        q.save(path, optimize=True)
        v2 = np.asarray(q.convert("RGB"))
        v1_path = v1_reference(lump, V2_DIR)
        with Image.open(v1_path) as im:
            v1 = np.asarray(im.convert("RGB"))
        h, w = v2.shape[:2]
        for tag, rgb in (("v1", v1), ("v2", v2)):
            files[f"{lump}_{tag}"] = path if tag == "v2" else v1_path
            files[f"{lump}_{tag}_tile"] = save_rgb(np.tile(rgb, (2, 2, 1)), V2_DIR / f"{lump}_{tag}_tile2x2.png")
            files[f"{lump}_{tag}_dark"] = save_rgb(shade(rgb, LIGHT_128), V2_DIR / f"{lump}_{tag}_light128.png")
        used = {tuple(int(x) for x in c) for c in v2.reshape(-1, 3)}
        entries.append({
            "proposal": name, "replaces": lump, "palette_version": V2_PALETTE, "kind": "wall",
            "width": w, "height": h, "file": rel_path(path),
            "script": SCRIPT_REL + " --v2", "seed": BATCH_SEED + SEED_OFFSET[lump],
            "colours_used": len(used), "v2_colours_used": len(used - v1_set),
            "colours_used_v1": len({tuple(int(x) for x in c) for c in v1.reshape(-1, 3)}),
            "mean_luma_v1": round(mean_luma(v1), 1), "mean_luma_v2": round(mean_luma(v2), 1),
            "seam_score": round(tiling_seam_score(v2), 2), "description_en": why,
        })
        print(f"{name:11s} {w:3d}x{h:3d} colours={len(used):3d} (v2-only {len(used - v1_set):3d}) "
              f"luma v1 {entries[-1]['mean_luma_v1']} -> v2 {entries[-1]['mean_luma_v2']}")
    # in place: marble | mosaic | marble, the way a station bay is clad
    for tag in ("v1", "v2"):
        def rgb_of(lump):
            with Image.open(files[f"{lump}_{tag}"]) as im:
                return np.asarray(im.convert("RGB"))
        marble, mosaic = rgb_of("SDMARB1"), rgb_of("SDMOSA1")
        bay = np.concatenate([marble, mosaic, marble], axis=1)
        files[f"bay_{tag}"] = save_rgb(bay, V2_DIR / f"bay_{tag}.png")
        files[f"bay_{tag}_dark"] = save_rgb(shade(bay, LIGHT_128), V2_DIR / f"bay_{tag}_light128.png")
    return entries, files


V2_INTRO = (
    "<b>Palette v2 (D45) on the two metro pieces it was made for.</b> You approved v2 &mdash; marble red, "
    "mosaic cobalt and gold, Legion pink in the reserved slots &mdash; and chose the mosaic's motif: the "
    "star with rays as it is. Here are <code>SDMARB1</code> and <code>SDMOSA1</code> redrawn in v2: "
    "<b>same seed, same veins, same tesserae; only the inks change.</b> On the left of every pair is the "
    "approved v1 file exactly as it sits in <code>assets/</code> (D42); on the right the v2 proposal. "
    "Nothing in <code>assets/</code> has changed. Pick per piece: keep v1, or replace it with v2.")


def pair_card(entry: dict, files: dict) -> str:
    lump = entry["replaces"]
    size = (entry["width"], entry["height"])
    tile = (size[0] * 2, size[1] * 2)
    views = ""
    for label, key, zoom, sz in (("4x", "", sheetlib.ZOOM, size), ("1x", "", 1, size),
                                 ("2x2 tile (2x)", "_tile", 2, tile), ("~light 128 (2x)", "_dark", 2, size)):
        views += ('<div class="row">'
                  + sheetlib.view(f"v1 approved · {label}", files[f"{lump}_v1{key}"], zoom, sz if key != "_tile" else tile)
                  + sheetlib.view(f"v2 proposal · {label}", files[f"{lump}_v2{key}"], zoom, sz if key != "_tile" else tile)
                  + "</div>")
    rec = V2_RECOMMEND[lump]
    return (f'<div class="card rec"><span class="tag">recommended: {html.escape(rec[0])}</span>'
            f'<h3>{lump} &rarr; {entry["proposal"]}</h3>'
            f'<p class="desc">{html.escape(entry["description_en"])}</p>{views}'
            f'<dl><dt>Size</dt><dd>{entry["width"]}&times;{entry["height"]}</dd>'
            f'<dt>Colours used</dt><dd>v1 {entry["colours_used_v1"]} &middot; v2 {entry["colours_used"]} '
            f'({entry["v2_colours_used"]} of them new in v2)</dd>'
            f'<dt>Mean luma</dt><dd>v1 {entry["mean_luma_v1"]} &middot; v2 {entry["mean_luma_v2"]}</dd>'
            f'<dt>Seam ratio (v2)</dt><dd>{entry["seam_score"]}</dd>'
            f'<dt>Origin</dt><dd>(a) {SCRIPT_REL} --v2, seed {entry["seed"]} (the approved seed)</dd>'
            f'<dt>Why</dt><dd style="white-space:normal;font-family:inherit">{html.escape(rec[1])}</dd></dl></div>')


# lump -> (what I recommend, why). Written after looking at the sheet once.
V2_RECOMMEND = {
    "SDMARB1": ("v2, by a small margin", "v1 is the bolder red, but it is flag_red, the red of the stripe and "
                "the stars, so the wall reads as painted. v2 is a warmer, browner red that reads as stone, "
                "and it sits better next to the cobalt mosaic. It is also lighter (mean luma 71 against 53), "
                "which keeps more of the veins at low light. Honest caveat: the gain is modest; if you "
                "prefer v1's punch, keeping it costs nothing."),
    "SDMOSA1": ("v2, clearly", "Same star, same tesserae. On v1's slate ground the star floats on grey; on "
                "cobalt it reads as a Soviet smalt mosaic, which is what the panel was meant to be. The "
                "gold holds at ~light 128 as well as v1's yellow did. This is the piece v2 was for."),
}


def palette_v2_swatches() -> str:
    pal = palgen.load()
    v1 = sheetlib.palette_ramps({"ramps": pal["ramps"]})
    added = sheetlib.palette_ramps({"ramps": [
        {"name": f'{r["name"]} (v2)', "colours": r["colours"]} for r in pal["added_ramps"]]})
    return (f'<p class="lead">v1, frozen (162 colours, slots 0-161):</p>{v1}'
            f'<p class="lead" style="margin-top:12px">Added in v2 (64 colours, slots 162-225; 30 slots '
            f'stay reserved). <code>flesh_pink</code> is the Legion drafts\' candidate ramp, unchanged:</p>{added}')


def build_v2_sheet(entries: list[dict], files: dict, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    cards = "".join(pair_card(e, files) for e in entries)
    bay = ('<div class="row">'
           + sheetlib.view("v1 approved (2x)", files["bay_v1"], 2, (256, 128))
           + sheetlib.view("v2 proposal (2x)", files["bay_v2"], 2, (256, 128)) + "</div>"
           + '<div class="row">'
           + sheetlib.view("v1 · ~light 128 (2x)", files["bay_v1_dark"], 2, (256, 128))
           + sheetlib.view("v2 · ~light 128 (2x)", files["bay_v2_dark"], 2, (256, 128)) + "</div>")
    ask = ("<ol><li><b>SDMARB1:</b> keep v1, or replace it with <code>SDMARB1_v2</code>? I recommend v2.</li>"
           "<li><b>SDMOSA1:</b> keep v1, or replace it with <code>SDMOSA1_v2</code>? I recommend v2.</li>"
           "<li>If you take either: the file replaces the approved one under the same lump name, so no map "
           "changes. <code>SDMARB2</code> (a fill-out draft that reuses the marble) would follow the "
           "marble you choose.</li></ol>")
    sections = [
        ("The two pieces, v1 approved next to v2 proposed", "", f'<div class="grid">{cards}</div>'),
        ("In place: marble | mosaic | marble",
         "A station bay clad the way the set is meant to be used, v1 against v2. A coherence check, not a "
         "mockup.", bay),
        ("What I need from you", "", f'<div class="ask">{ask}</div>'),
        ("Palette v2", "", palette_v2_swatches()),
    ]
    out = out_dir / f"{stamp}_F3_metro-palette-v2.html"
    return sheetlib.write_sheet(
        out, lang="en", title="Soviet Doom — metro, palette v2 proposals (SDMARB1, SDMOSA1)",
        subtitle="F3 · metro set · D45 · proposals for the CEO, nothing here is in assets/",
        intro=V2_INTRO, sections=sections,
        footer=(f"Origin (a): procedural, {SCRIPT_REL} --v2, the approved seeds {BATCH_SEED}+3 and +4. "
                "Palette docs/art/palette.json v2 (D45, 2026-10-14); the v1 views are the approved files "
                "from assets/, unmodified. Licence: own work, CC BY-NC-SA 4.0 (D15). The '~light 128' "
                "view is a flat x0.5 multiply for orientation, not the engine's colormap (NOT VERIFIED "
                "in GZDoom)."))


def main_v2() -> None:
    entries, files = build_v2()
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    sheet = build_v2_sheet(entries, files, stamp)
    V2_MANIFEST.write_text(json.dumps({
        "batch": 2, "phase": "F3", "set": SET_NAME, "script": SCRIPT_REL + " --v2",
        "batch_seed": BATCH_SEED, "palette_version": V2_PALETTE, "decision": "D45",
        "status": "proposals for the CEO; the approved v1 files stay in assets/ (D42)",
        "textures": entries,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"sheet: {sheet}\nmanifest: {V2_MANIFEST}")


def main_mosaic_v1() -> None:
    """History: the D42 mosaic in palette v1, superseded by D56."""
    path = write_v1_history("SDMOSA1", HIST_DIR)
    print(f"SDMOSA1 v1 (D42, superseded by D56): {path}")


def main() -> None:
    if "--fill" in sys.argv[1:]:
        main_fill()
        return
    if "--mosaic-v1" in sys.argv[1:]:
        main_mosaic_v1()
        return
    if "--v2" in sys.argv[1:]:
        main_v2()
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    approved_offsets = {k: v for k, v in SEED_OFFSET.items() if k not in FILL_SEED_OFFSET}
    assert set(approved_offsets) == {t[0] for t in TEXTURES}, "SEED_OFFSET and TEXTURES disagree"
    assert len(set(SEED_OFFSET.values())) == len(SEED_OFFSET), "two pieces share a seed"
    entries, files = [], {}
    for lump, builder, kind, desc_en, desc_ru in TEXTURES:
        assert len(lump) <= 8 and lump.isupper() and lump.startswith("SD"), lump
        rgb = builder()
        h, w = rgb.shape[:2]
        path = OUT_DIR / f"{lump}.png"
        img = save_lump(lump, rgb, path)
        files[lump] = path
        tile_path = OUT_DIR / f"{lump}_tile2x2.png"
        save_lump(lump, np.tile(rgb, (2, 2, 1)), tile_path)
        files[lump + "_tile"] = tile_path
        entries.append({
            "lump": lump, "kind": kind, "set": SET_NAME, "width": w, "height": h,
            "palette_version": palette_version(lump),
            "file": str(path.relative_to(PROJECT_ROOT)), "script": SCRIPT_REL,
            "seed": BATCH_SEED + SEED_OFFSET[lump], "seed_offset": SEED_OFFSET[lump],
            "colours_used": len(set(img.get_flattened_data())),
            "seam_score": round(tiling_seam_score(rgb), 2),
            "description_en": desc_en, "description_ru": desc_ru,
        })
        print(f"{lump:9s} {w:3d}x{h:3d} {kind:4s} colours={entries[-1]['colours_used']:3d} "
              f"seam={entries[-1]['seam_score']:5.2f}")

    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    en = build_sheet("en", entries, files, stamp)
    ru = build_sheet("ru", entries, files, stamp)
    MANIFEST.write_text(json.dumps({
        "batch": 2, "phase": "F2", "set": SET_NAME, "script": SCRIPT_REL,
        "batch_seed": BATCH_SEED, "status": "exploration, not a closed set",
        "palette_limited": {k: v[0] for k, v in PALETTE_LIMITED.items()},
        "textures": entries,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"sheet EN: {en}\nsheet RU: {ru}\nmanifest: {MANIFEST}")


if __name__ == "__main__":
    main()
