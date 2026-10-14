"""Batch 4 — the factory set «Танкоград» (MAP04, BACKLOG N6).

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_factory.py
                            (macOS: .venv/bin/python tools/art/gen_factory.py)

The thirteen industrial pieces of docs/levels/MAP04-factory.md §7.2, as
drafts for the CEO. Nothing here is approved and nothing is written into
assets/: the PNGs go to work/art/batch4/factory/ and the sheet to
docs/art/previews/<stamp>_F3_batch4-factory.html.

Method, the metro's (tools/art/gen_metro.py): every piece is procedural,
one seed per piece (BATCH_SEED + offset), deterministic, quantised without
dither. Two exceptions to "one seed of its own", both on purpose:

  - SDDOORY and SDDOORR start from SDDOOR1's own seed (gen_soviet_base,
    1977 + 5) and replay its first random draws, so their steel, paint and
    chips are SDDOOR1's pixel for pixel; only the trim, the pass plate and
    the hazard band differ (tests/test_gen_factory.py holds them to the
    approved file outside those areas). The trim's wear has its own seed.
  - SDFLAG1 and SDFLAG2 hang on SDBRCK1's exact pixels, so a flag tile next
    to a brick tile continues the bond with no seam.

No system font (D27): the only lettering, the works banner SDSLOG1 and the
pass plates on the two doors, is set from our own alphabet, read from
assets/fonts/bigfont/ (D24), and scaled with nearest neighbour. Those
pieces therefore reproduce byte for byte on the Mac and on Windows.

Palette: v1 unless a piece says otherwise in PALETTE_VERSION, where the
reason is written next to it. Masked pieces (the chain) are RGBA with hard
0/255 alpha and every opaque pixel a palette colour, the ART-BIBLE §2
exception for assets drawn over something else.
"""

from __future__ import annotations

import datetime as dt
import html
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import (  # noqa: E402
    DIMENSION_MULTIPLE, Overlay, blend, fbm, grain, quantize, ramp_colour, shade, tiling_seam_score, to_rgb,
)
import gen_metro  # noqa: E402  (palette-version helpers: any_to_rgb, any_ramp_colour, quantize_version)
import gen_soviet_base as base  # noqa: E402  (SDDOOR1's recipe constants and seed)
import palette as palgen  # noqa: E402
import sheetlib  # noqa: E402

any_to_rgb = gen_metro.any_to_rgb
any_ramp_colour = gen_metro.any_ramp_colour
quantize_version = gen_metro.quantize_version

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SET_NAME = "factory"
OUT_DIR = PROJECT_ROOT / "work" / "art" / "batch4" / SET_NAME
VIEW_DIR = OUT_DIR / "views"            # sheet-only views (tiles, light, far, scenes)
MANIFEST = OUT_DIR / "manifest.json"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
SCRIPT_REL = "tools/art/gen_factory.py"
BIGFONT_DIR = PROJECT_ROOT / "assets" / "fonts" / "bigfont"
ASSET_WALLS = PROJECT_ROOT / "assets" / "textures"
ASSET_FLATS = PROJECT_ROOT / "assets" / "flats"

# Own seed space: batch 4, and 41 for 1941, the year the Chelyabinsk works
# became «Танкоград». Clear of gen_metro (1935+1..16), gen_soviet_base
# (1977+), gen_switch (2077+) and gen_props (3077+).
BATCH_SEED = 4100
SEED_OFFSET = {
    "SDBRCK1": 1, "SDBRCK2": 2, "SDRUST1": 3, "SDCHAN1": 4, "SDFLR4": 5, "SDGRAT1": 6,
    "SDMOLT": 7,                      # one piece, four frames, one seed
    "SDDOORY": 8, "SDDOORR": 9,       # the trim's wear only; the leaf is SDDOOR1's seed
    "SDPORT": 10, "SDGATE1": 11, "SDWIND1": 12, "SDSLOG1": 13, "SDFLAG1": 14, "SDFLAG2": 15,
}
DOOR1_SEED = base.BATCH_SEED + 5      # gen_soviet_base.tex_door1: rng_for(5)

WALL_W, WALL_H = 64, 128
WIDE_W = 128
FLAT = 64
FRAMES = 4                            # animated pieces: SDMOLT1-4, SDPORT1-4

# Which palette each piece is quantised to, and why when it is not v1.
PALETTE_VERSION = {
    "SDBRCK1": 2, "SDBRCK2": 2, "SDFLAG1": 2, "SDFLAG2": 2, "SDPORT": 2,
}
PALETTE_WHY = {
    "SDBRCK1": "v2 for marble_red: v1 has no brick red. flag_red is signage red and reads as paint; "
               "rust_brown alone gives a brown, Doom-generic brick. marble_red is a fired-clay red, with "
               "rust_brown kept for the browner bricks of the bond.",
    "SDBRCK2": "v2: the same brick as SDBRCK1 above the whitewash.",
    "SDFLAG1": "v2 only because it hangs on SDBRCK1's pixels; the banner itself is v1 (flag_red, plaster_warm, black).",
    "SDFLAG2": "v2: the canton is mosaic_cobalt. v1's only blue is steel_blue, a grey that makes the US "
               "canton read as slate at banner size (the 7x5 shoulder patch gets away with it, a 28x40 "
               "canton does not). Also hangs on SDBRCK1's pixels.",
    "SDPORT": "v2 for mosaic_cobalt: the portal must not look like anything in the world, and every v1 "
              "ramp belongs to the world (concrete, paint, rust, signage). A true cobalt does not.",
}


def rng_for(piece: str) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + SEED_OFFSET[piece])


def palette_of(piece: str) -> int:
    return PALETTE_VERSION.get(piece, 1)


# ============================================================ brick
BRICK_W, BRICK_H = 16, 8     # 4 bricks across 64, 16 courses up 128: a Doom-sized brick
MORTAR = 1
BRICK_MID = 0.52             # marble_red: fired clay, not ox-blood
BRICK_JITTER = 0.08          # per-brick tone: every brick its own firing
BRICK_BROWN = 0.20           # share of bricks fired browner (rust_brown)
BRICK_DARK = 0.08            # share of overfired, near-purple bricks
MORTAR_TONE = 0.38           # plaster_warm: lime mortar gone grey with soot
SOOT = 0.42                  # SDBRCK1: how far the soot darkens the brick at most (a multiply)


def brick_courses(w: int, h: int):
    """Geometry of the running bond: course index, brick index (wrapping),
    and the position inside the brick, per pixel. The bond divides 64 and
    128, so a brick wall tiles in both axes."""
    yy, xx = np.mgrid[0:h, 0:w]
    row = yy // BRICK_H
    off = (row % 2) * (BRICK_W // 2)
    col = ((xx + off) // BRICK_W) % (w // BRICK_W)
    lx = (xx + off) % BRICK_W
    ly = yy % BRICK_H
    return row, col, lx, ly


def brick_field(w: int, h: int, rng: np.random.Generator, soot: float) -> np.ndarray:
    ny, nx = h // BRICK_H, w // BRICK_W
    row, col, lx, ly = brick_courses(w, h)
    tone = BRICK_MID + rng.uniform(-BRICK_JITTER, BRICK_JITTER, (ny, nx))
    kind = rng.random((ny, nx))
    field = tone[row, col] + (fbm(w, h, 8, 3, rng, 0.5) - 0.5) * 0.16 + grain(w, h, rng, 0.035)
    red = any_to_rgb(np.clip(field, 0, 1), "marble_red")
    brown = to_rgb(np.clip(field - 0.02, 0, 1), "rust_brown")
    dark = any_to_rgb(np.clip(field - 0.20, 0, 1), "marble_red")
    k = kind[row, col][..., None]
    rgb = np.where(k < BRICK_BROWN, brown, np.where(k > 1 - BRICK_DARK, dark, red))
    # lime mortar, recessed
    mortar = (lx < MORTAR) | (ly < MORTAR)
    mfield = MORTAR_TONE + (fbm(w, h, 6, 2, rng) - 0.5) * 0.12 + grain(w, h, rng, 0.03)
    rgb = np.where(mortar[..., None], to_rgb(np.clip(mfield, 0, 1), "plaster_warm"), rgb)
    # light from above: lit top and left lip on each brick, shadow under it
    f = np.ones((h, w))
    f[(ly == MORTAR) & ~mortar] = 1.16
    f[(lx == MORTAR) & ~mortar] *= 1.06
    f[ly == BRICK_H - 1] *= 0.74
    f[(lx == BRICK_W - 1) & ~mortar] *= 0.86
    rgb = shade(rgb, f)
    # spalled faces: a few bricks lost their skin
    spall = (fbm(w, h, 16, 2, rng) > 0.70) & ~mortar
    rgb = np.where(spall[..., None], shade(rgb, 0.80), rgb)
    if soot > 0:
        # soot: clouds plus streaks down from the joints, tileable (no
        # vertical gradient, which would show a seam on a wall over 128)
        cloud = np.clip(fbm(w, h, 3, 4, rng, 0.55) - 0.36, 0, 1) * 2.2
        streak = np.clip(fbm(w, h, 8, 3, rng, 0.5, aspect=6.0) - 0.48, 0, 1) * 1.7
        # a multiply, not a blend towards a grey: blended, the soot went olive on red
        rgb = shade(rgb, 1 - np.clip((cloud + streak) * soot, 0, soot))
    return rgb


def tex_brck1() -> np.ndarray:
    """Soot-stained red factory brick, Stalin-era works."""
    return brick_field(WALL_W, WALL_H, rng_for("SDBRCK1"), SOOT)


WASH_Y0 = 64                 # SDBRCK2: whitewash from here down to the floor
WASH_TONE = 0.86             # plaster_warm
WASH_FLAKE = 0.58            # fbm above this: the lime worn thin, brick showing through
RULE_H = 3                   # the dark rule painted along the whitewash's top
RULE_TONE = 0.10             # concrete_cold


def tex_brck2() -> np.ndarray:
    """The same brick, whitewashed to 64 with a dark rule: the works' dado.
    The bond still shows through the lime as a relief, and the lime has
    flaked where carts and shoulders rubbed it."""
    rng = rng_for("SDBRCK2")
    w, h = WALL_W, WALL_H
    rgb = brick_field(w, h, rng, SOOT * 0.6)
    _, _, lx, ly = brick_courses(w, h)
    mortar = (lx < MORTAR) | (ly < MORTAR)
    field = WASH_TONE + (fbm(w, h, 4, 4, rng, 0.5) - 0.5) * 0.10 + grain(w, h, rng, 0.02)
    wash = to_rgb(np.clip(field, 0, 1), "plaster_warm")
    relief = np.ones((h, w))
    relief[mortar] = 0.86
    relief[ly == BRICK_H - 1] *= 0.94
    wash = shade(wash, relief)
    rows = np.arange(h)[:, None] * np.ones((1, w))
    band = rows >= WASH_Y0
    # Flaking: a few broad, soft patches where the lime has worn thin, the
    # brick showing through it dulled and pale. Small sharp red flakes on
    # white read as blood at 1x (first draft); never do that.
    flake = np.clip((fbm(w, h, 3, 3, rng, 0.5) - WASH_FLAKE) * 4.0, 0, 1) * band
    thin = blend(rgb, ramp_colour("plaster_warm", 0.62), 0.55 * np.ones((h, w)))
    rgb = np.where(band[..., None], wash, rgb)
    rgb = (rgb * (1 - flake[..., None] * 0.8) + thin * (flake[..., None] * 0.8)).astype(np.uint8)
    # grime rubbed in at hand height, darker towards the floor line
    rub = np.clip(fbm(w, h, 6, 3, rng, 0.5, aspect=0.3) - 0.55, 0, 1) * 1.2 * band
    rgb = blend(rgb, ramp_colour("plaster_warm", 0.40), np.clip(rub, 0, 0.35))
    # the dark rule
    rule = (rows >= WASH_Y0) & (rows < WASH_Y0 + RULE_H)
    rgb = np.where(rule[..., None], to_rgb(np.clip(RULE_TONE + grain(w, h, rng, 0.02), 0, 1), "concrete_cold"), rgb)
    f = np.ones((h, w))
    f[WASH_Y0 + RULE_H, :] = 0.80
    return shade(rgb, f)


# ============================================================ corrugated
CORR_PERIOD = 8              # one corrugation per 8 px: 8 across a 64 tile
CORR_DEPTH = 0.32            # light/shadow swing across a corrugation
RUST_MID = 0.42              # rust_brown
GALV_TONE = 0.40             # steel_blue: what is left of the galvanising
GALV_SHARE = 0.60            # fbm above this keeps its zinc
HOLE_T = 0.86                # fbm above this: rusted through
LAP_BOLT_Y = 4               # bolts along the lap seam at the top of each sheet


def corrugation(w: int, h: int, phase: float = 0.0) -> np.ndarray:
    """Shading factor of a vertical corrugation lit from the left."""
    xs = np.arange(w)[None, :]
    return np.repeat(1 + CORR_DEPTH * np.sin(2 * np.pi * (xs + phase) / CORR_PERIOD), h, axis=0)


def tex_rust1() -> np.ndarray:
    """Rusted corrugated sheet: galvanising surviving in patches, rust
    streaks running down the troughs, a lap seam with bolts, a couple of
    holes rusted clean through."""
    rng = rng_for("SDRUST1")
    w, h = WALL_W, WALL_H
    field = RUST_MID + (fbm(w, h, 4, 5, rng, 0.55) - 0.5) * 0.24 + grain(w, h, rng, 0.03)
    rgb = to_rgb(np.clip(field, 0, 1), "rust_brown")
    galv_f = GALV_TONE + (fbm(w, h, 6, 3, rng) - 0.5) * 0.16 + grain(w, h, rng, 0.02)
    galv = to_rgb(np.clip(galv_f, 0, 1), "steel_blue")
    keep = fbm(w, h, 4, 4, rng, 0.5) > GALV_SHARE
    rgb = np.where(keep[..., None], galv, rgb)
    streak = np.clip(fbm(w, h, 8, 3, rng, 0.5, aspect=7.0) - 0.48, 0, 1) * 2.2
    rgb = blend(rgb, ramp_colour("rust_brown", 0.22), np.clip(streak, 0, 0.7))
    rgb = shade(rgb, corrugation(w, h))
    # rust-through holes: near black, a bright orange lip
    hole_f = fbm(w, h, 16, 2, rng)
    hole = hole_f > HOLE_T
    lip = (hole_f > HOLE_T - 0.035) & ~hole
    rgb = np.where(lip[..., None], np.array(ramp_colour("rust_brown", 0.78), np.uint8), rgb)
    rgb = np.where(hole[..., None], np.array(ramp_colour("rust_brown", 0.04), np.uint8), rgb)
    # lap seam at the top of the sheet, bolts on every crest
    f = np.ones((h, w))
    f[0, :], f[1, :], f[2, :] = 0.50, 0.70, 1.18
    rgb = shade(rgb, f)
    ov = Overlay(w, h)
    for x in range(CORR_PERIOD // 4, w, CORR_PERIOD):
        ov.ellipse(x - 1.3, LAP_BOLT_Y - 1.3, x + 1.3, LAP_BOLT_Y + 1.3, fill=ramp_colour("steel_blue", 0.20))
        ov.ellipse(x - 0.8, LAP_BOLT_Y - 1.0, x + 0.6, LAP_BOLT_Y + 0.4, fill=ramp_colour("steel_blue", 0.62))
    return ov.composite(rgb)


# ============================================================ chain (masked)
CHAIN_X = 32
LINK_L, LINK_W = 14, 10      # a link 14 long, 10 across
LINK_PITCH = 10              # links interlock: 4 px of overlap
LINK_BAR = 2.8               # wire thickness
CHAIN_END = 86               # the last link's top; the hook hangs below it
HOOK_R_OUT, HOOK_R_IN = 11.0, 5.5
ALPHA_CUT = 128              # hard alpha: >= this is opaque


def chain_rgba() -> np.ndarray:
    """A hanging chain and its crane hook on a transparent ground, for a
    two-sided line's mid-texture. Links alternate face-on (a ring) and
    edge-on (a bar). Returns (h, w, 4) uint8 with alpha 0 or 255."""
    rng = rng_for("SDCHAN1")
    w, h = WALL_W, WALL_H
    ov = Overlay(w, h)
    dark = ramp_colour("steel_blue", 0.14)
    body = ramp_colour("steel_blue", 0.36)
    hi = ramp_colour("steel_blue", 0.72)
    x0, x1 = CHAIN_X - LINK_W / 2, CHAIN_X + LINK_W / 2
    ys = list(range(-LINK_L + 2, CHAIN_END + 1, LINK_PITCH))
    for i, y in enumerate(ys):
        if i % 2 == 0:            # face-on ring: outline only, the eye stays open
            ov.ellipse(x0, y, x1, y + LINK_L, outline=dark, width=LINK_BAR + 0.8)
            ov.ellipse(x0 + 0.4, y + 0.4, x1 - 0.4, y + LINK_L - 0.4, outline=body, width=LINK_BAR)
            ov.arc_ring(CHAIN_X, y + LINK_L / 2, LINK_W / 2 - 0.3, LINK_W / 2 - 1.1, 150, 230, hi)
        else:                     # edge-on: a bar with a lit edge
            ov.rect(CHAIN_X - 1.6, y, CHAIN_X + 1.6, y + LINK_L, fill=dark)
            ov.rect(CHAIN_X - 1.1, y + 0.5, CHAIN_X + 1.1, y + LINK_L - 0.5, fill=body)
            ov.rect(CHAIN_X - 1.1, y + 1, CHAIN_X - 0.3, y + LINK_L - 1, fill=hi)
    # the hook: an eye, a shank, and the bend with its point turned up
    eye_y = ys[-1] + LINK_PITCH
    ov.ellipse(x0 - 1, eye_y, x1 + 1, eye_y + LINK_L, outline=dark, width=LINK_BAR + 1.2)
    ov.ellipse(x0 - 0.6, eye_y + 0.4, x1 + 0.6, eye_y + LINK_L - 0.4, outline=body, width=LINK_BAR + 0.4)
    shank_y0, shank_y1 = eye_y + LINK_L - 1, eye_y + LINK_L + 8
    ov.rect(CHAIN_X - 2.6, shank_y0, CHAIN_X + 2.6, shank_y1 + 1, fill=dark)
    ov.rect(CHAIN_X - 2.0, shank_y0, CHAIN_X + 2.0, shank_y1 + 1, fill=body)
    bend_cx = CHAIN_X + (HOOK_R_OUT + HOOK_R_IN) / 2 - 2.3
    bend_cy = shank_y1
    ov.arc_ring(bend_cx, bend_cy, HOOK_R_OUT + 0.6, HOOK_R_IN - 0.6, 0, 180, dark)
    ov.arc_ring(bend_cx, bend_cy, HOOK_R_OUT, HOOK_R_IN, 0, 180, body)
    ov.arc_ring(bend_cx, bend_cy, HOOK_R_OUT - 0.5, HOOK_R_OUT - 1.6, 95, 175, hi)
    tip_x0, tip_x1 = bend_cx + HOOK_R_IN - 0.6, bend_cx + HOOK_R_OUT + 0.6
    ov.polygon([(tip_x0, bend_cy + 0.5), (tip_x1, bend_cy + 0.5), (tip_x0 + 1.2, bend_cy - 7)], dark)
    ov.polygon([(tip_x0 + 0.6, bend_cy + 0.5), (tip_x1 - 0.6, bend_cy + 0.5), (tip_x0 + 1.4, bend_cy - 5.5)], body)
    small = np.asarray(ov.img.resize((w, h), Image.Resampling.BOX), dtype=np.float64)
    alpha = small[..., 3]
    opaque = alpha >= ALPHA_CUT
    rgb = np.zeros((h, w, 3))
    a = np.maximum(alpha, 1)[..., None] / 255.0
    rgb = np.clip(small[..., :3] / a, 0, 255)
    # rust gathered on the links, more towards the hook
    rust = np.clip(fbm(w, h, 8, 3, rng) - 0.55, 0, 1) * 2.0 * np.linspace(0.5, 1.2, h)[:, None]
    rgb = blend(rgb.astype(np.uint8), ramp_colour("rust_brown", 0.36), np.clip(rust, 0, 0.6))
    out = np.zeros((h, w, 4), np.uint8)
    out[..., :3] = rgb
    out[..., 3] = np.where(opaque, 255, 0)
    return out


def tex_chan1() -> np.ndarray:
    return chain_rgba()


# ============================================================ flats
PLATE = 32                   # SDFLR4: cast plates, 2x2 per flat
LOZ_CELL = 8                 # one raised lozenge per 8 px cell
LOZ_R = 3.0                  # lozenge half-length along its diagonal
LOZ_W = 0.95                 # lozenge half-width across it
IRON_MID = 0.26              # steel_blue: cast iron
IRON_WEAR = 0.60             # polished tops where boots go


def tex_flr4() -> np.ndarray:
    """Cast-iron chequer plate: 32 px plates, raised lozenges lit from above
    and polished by boots, rust in the low ground between them."""
    rng = rng_for("SDFLR4")
    w = h = FLAT
    field = IRON_MID + (fbm(w, h, 4, 4, rng, 0.5) - 0.5) * 0.12 + grain(w, h, rng, 0.03)
    yy, xx = np.mgrid[0:h, 0:w]
    cx = (xx % LOZ_CELL) - (LOZ_CELL - 1) / 2
    cy = (yy % LOZ_CELL) - (LOZ_CELL - 1) / 2
    # long lozenges on the diagonals, alternating cell by cell (the tread
    # pattern); a first draft with short lozenges read as rows of crosses
    flip = ((xx // LOZ_CELL) + (yy // LOZ_CELL)) % 2 == 1
    across = np.where(flip, np.abs(cx - cy), np.abs(cx + cy)) / np.sqrt(2)
    along = np.where(flip, np.abs(cx + cy), np.abs(cx - cy)) / np.sqrt(2)
    raised = (across <= LOZ_W) & (along <= LOZ_R)
    field = np.where(raised, field + 0.12, field)
    rgb = to_rgb(np.clip(field, 0, 1), "steel_blue")
    up = np.roll(raised, 1, axis=0)
    down = np.roll(raised, -1, axis=0)
    f = np.ones((h, w))
    f[raised & ~up] = 1.30                 # lit top edge
    f[raised & ~down] = 0.62               # shadowed lower edge
    f[~raised & up] *= 0.75                # cast shadow below a lozenge
    # plate joints
    for k in range(0, w, PLATE):
        f[:, k] = 0.45
        f[:, (k + 1) % w] *= 1.12
        f[k, :] = 0.45
        f[(k + 1) % h, :] *= 1.12
    rgb = shade(rgb, f)
    wear = (fbm(w, h, 3, 3, rng) > 0.48) & raised
    rgb = np.where(wear[..., None], to_rgb(np.clip(IRON_WEAR + grain(w, h, rng, 0.04), 0, 1), "steel_blue"), rgb)
    rust = np.clip(fbm(w, h, 6, 3, rng) - 0.50, 0, 1) * 2.0 * ~raised
    return blend(rgb, ramp_colour("rust_brown", 0.28), np.clip(rust, 0, 0.55))


GRATE_PERIOD = 8             # SDGRAT1: bearing bars every 8 px (along y)
GRATE_BAR = 2
GRATE_CROSS = 16             # cross bars every 16 px
GRATE_FRAME = 3              # the panel's frame on the tile edges
GRATE_BAR_TONE = 0.44        # steel_blue
GRATE_DEPTH_TONE = 0.10      # concrete_cold: the floor far below, not flat black


def tex_grat1() -> np.ndarray:
    """Steel bar grating: bearing bars along y, cross bars every 16 px, a
    frame on the panel's edges. The holes show the dark below, with a faint
    floor in it so no hole is a flat black blob (ART-BIBLE §5)."""
    rng = rng_for("SDGRAT1")
    w = h = FLAT
    depth = GRATE_DEPTH_TONE + (fbm(w, h, 4, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.02)
    rgb = to_rgb(np.clip(depth, 0, 1), "concrete_cold")
    yy, xx = np.mgrid[0:h, 0:w]
    bar = (xx % GRATE_PERIOD) < GRATE_BAR
    cross = (yy % GRATE_CROSS) < 1
    frame = (xx < GRATE_FRAME) | (yy < GRATE_FRAME)
    metal = bar | cross | frame
    steel = to_rgb(np.clip(GRATE_BAR_TONE + (fbm(w, h, 4, 3, rng) - 0.5) * 0.14 + grain(w, h, rng, 0.03), 0, 1),
                   "steel_blue")
    rgb = np.where(metal[..., None], steel, rgb)
    f = np.ones((h, w))
    f[bar & ((xx % GRATE_PERIOD) == 0)] = 1.25          # lit edge of each bar
    f[~metal & np.roll(metal, 1, axis=1)] = 0.55        # shadow beside a bar
    f[~metal & np.roll(metal, 1, axis=0)] *= 0.70       # and below a cross bar
    f[frame & ((xx == 0) | (yy == 0))] = 1.30
    f[(xx == GRATE_FRAME - 1) | (yy == GRATE_FRAME - 1)] *= 0.70
    rgb = shade(rgb, f)
    rust = np.clip(fbm(w, h, 8, 3, rng) - 0.55, 0, 1) * 2.2 * metal
    return blend(rgb, ramp_colour("rust_brown", 0.30), np.clip(rust, 0, 0.6))


# ============================================================ molten metal
# Heat stops, coolest first: (heat, ramp, tone). The orange in the middle
# is rust_brown's top, v1's nearest thing to an orange.
HEAT_STOPS = (
    (0.00, "flag_red", 0.22),
    (0.30, "flag_red", 0.70),
    (0.52, "rust_brown", 1.00),
    (0.72, "hazard_yellow", 0.92),
    (0.88, "cream_yellow", 1.00),
    (1.00, None, None),               # white
)
CRUST_T = 0.40               # crust where the slow field is under this
CRUST_RIM = 0.10             # metal cools to red over this much of the field near a plate
CRUST_TONE = 0.14            # concrete_cold: cooled slag
CRACK_T = 0.80               # ridge above this: a crack in the slag, glowing
MOLT_SWING = 0.28            # share of the field that moves between frames: the rest is still,
                             # so the metal boils in place instead of flickering (first draft: 1.0)


def heat_rgb(heat: np.ndarray) -> np.ndarray:
    cols = []
    for _, ramp_name, tone in HEAT_STOPS:
        cols.append((255, 255, 255) if ramp_name is None else ramp_colour(ramp_name, tone))
    xs = np.array([s[0] for s in HEAT_STOPS])
    cols = np.array(cols, dtype=np.float64)
    out = np.zeros(heat.shape + (3,))
    hc = np.clip(heat, 0, 1)
    for c in range(3):
        out[..., c] = np.interp(hc, xs, cols[:, c])
    return out.astype(np.uint8)


def periodic(a: np.ndarray, b: np.ndarray, frame: int) -> np.ndarray:
    """Blend of two noise fields at phase frame/FRAMES of a full turn: the
    animation's last frame leads back into its first, and every frame has
    the same contrast (cos^2 + sin^2 = 1)."""
    phi = 2 * np.pi * frame / FRAMES
    return 0.5 + (a - 0.5) * np.cos(phi) + (b - 0.5) * np.sin(phi)


def molten_frames() -> list[np.ndarray]:
    """Molten metal in four frames: a heat field from red to white under
    plates of slag; the metal cools to red against each plate and the slag
    has glowing cracks. Most of both fields is still and a part of them
    turns through a full phase over the four frames, so the metal boils in
    place and frame 4 leads back into frame 1."""
    rng = rng_for("SDMOLT")
    w = h = FLAT
    base_heat, a, b = (fbm(w, h, 4, 4, rng, 0.55) for _ in range(3))
    base_slow, c, d = (fbm(w, h, 3, 3, rng, 0.5) for _ in range(3))
    crack_n = fbm(w, h, 8, 3, rng, 0.5)
    g = grain(w, h, rng, 0.03)
    slag = to_rgb(np.clip(CRUST_TONE + (crack_n - 0.5) * 0.14 + g, 0, 1), "concrete_cold")
    ridge = 1 - np.abs(2 * crack_n - 1)
    frames = []
    for k in range(FRAMES):
        moving = periodic(a, b, k)
        heat = 0.74 + ((1 - MOLT_SWING) * (base_heat - 0.5) + MOLT_SWING * (moving - 0.5)) * 2.0 + g
        slow = 0.5 + (1 - MOLT_SWING) * (base_slow - 0.5) + MOLT_SWING * (periodic(c, d, k) - 0.5)
        near = np.clip(1 - (slow - CRUST_T) / CRUST_RIM, 0, 1)
        heat = heat - 0.45 * near
        rgb = heat_rgb(heat)
        crust = slow < CRUST_T
        crust_rgb = np.where((ridge > CRACK_T)[..., None], heat_rgb(np.full((h, w), 0.38) + g), slag)
        rgb = np.where(crust[..., None], crust_rgb, rgb)
        frames.append(rgb)
    return frames


# ============================================================ key doors
KEY_INKS = {   # door -> (trim ramp, tone, plate text colour (ramp, tone) or black, band tone)
    "SDDOORY": ("hazard_yellow", 0.86, ("concrete_cold", 0.04)),
    "SDDOORR": ("flag_red", 0.74, ("cream_yellow", 0.92)),
}
TRIM_WEAR = 0.80             # fbm above this: the trim paint is chipped to steel
PLATE_BOX = (16, 17, 112, 39)   # the pass plate on the leaf, over SDDOOR1's star and "7"
PASS_WORD = "ПРОПУСК"           # "pass": the doors open to a pass (MAP04 open point 3)
BAND_Y0, BAND_Y1 = WALL_H - base.DOOR_FRAME - 8, WALL_H - base.DOOR_FRAME - 2


def door_masks():
    """Where a key door differs from SDDOOR1: the frame, the two ribs, the
    plate and the hazard band. Everything else is SDDOOR1's pixels."""
    w = h = WIDE_W
    fr = base.DOOR_FRAME
    yy, xx = np.mgrid[0:h, 0:w]
    leaf = (yy >= fr) & (yy < h - fr) & (xx >= fr) & (xx < w - fr)
    frame = ~leaf
    ribs = np.zeros((h, w), bool)
    for ry in base.DOOR_RIB_YS:
        ribs |= (yy >= ry) & (yy < ry + base.DOOR_RIB_H) & leaf
    x0, y0, x1, y1 = PLATE_BOX
    plate = (yy >= y0) & (yy < y1) & (xx >= x0) & (xx < x1)
    band = (yy >= BAND_Y0) & (yy < BAND_Y1) & leaf
    return leaf, frame, ribs, plate, band


def glyph_masks(text: str, folder: Path = BIGFONT_DIR) -> tuple[np.ndarray, np.ndarray]:
    """Our alphabet (D24), read from the installed folder font: (body,
    shadow) boolean masks of `text` set on one line. The brighter glyph
    colour is the body, the darker the 1 px shadow. Raises if a glyph is
    missing rather than dropping a letter."""
    glyphs = []
    for ch in text:
        p = folder / f"{ord(ch.upper()):04X}.png"
        if not p.is_file():
            raise FileNotFoundError(f"no glyph for {ch!r} in {folder}")
        with Image.open(p) as im:
            glyphs.append(np.asarray(im.convert("RGBA")))
    h = max(g.shape[0] for g in glyphs)
    w = sum(g.shape[1] for g in glyphs)
    body = np.zeros((h, w), bool)
    shadow = np.zeros((h, w), bool)
    x = 0
    for g in glyphs:
        on = g[..., 3] > 0
        lum = g[..., :3].astype(int).sum(-1)
        bright = on & (lum >= lum[on].max() * 0.5) if on.any() else on
        gh, gw = on.shape
        body[:gh, x:x + gw] |= bright
        shadow[:gh, x:x + gw] |= on & ~bright
        x += gw
    return body, shadow


def paste_mask(canvas: np.ndarray, mask: np.ndarray, colour, cx: float, cy: float, scale: int = 1) -> None:
    """Paint `colour` where `mask` (scaled by nearest neighbour) is True,
    centred on (cx, cy), clipped to the canvas."""
    m = np.repeat(np.repeat(mask, scale, 0), scale, 1)
    mh, mw = m.shape
    x0, y0 = int(round(cx - mw / 2)), int(round(cy - mh / 2))
    H, W = canvas.shape[:2]
    ys, xs = slice(max(0, y0), min(H, y0 + mh)), slice(max(0, x0), min(W, x0 + mw))
    sub = m[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
    canvas[ys, xs][sub] = colour


def door_leaf_rgb() -> tuple[np.ndarray, np.ndarray]:
    """SDDOOR1's recipe (gen_soviet_base.tex_door1) up to its bevels, with
    the same seed and the same random draws, so the steel and the paint are
    SDDOOR1's. Returns (rgb after the bevels, leaf mask)."""
    rng = np.random.default_rng(DOOR1_SEED)
    w, h = WIDE_W, WALL_H
    fr = base.DOOR_FRAME
    steel_f = 0.40 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.2 + grain(w, h, rng, 0.03)
    rgb = to_rgb(steel_f, "steel_blue")
    leaf = np.zeros((h, w), dtype=bool)
    leaf[fr:h - fr, fr:w - fr] = True
    green_f = base.STEEL_GREEN_MID + (fbm(w, h, 3, 5, rng, 0.5) - 0.5) * 0.25 + grain(w, h, rng, 0.03)
    green = to_rgb(green_f, "military_green")
    chip = fbm(w, h, 9, 3, rng) > 0.74
    rgb = np.where((leaf & ~chip)[..., None], green, rgb)
    f = np.ones((h, w))
    f[fr - 1, fr - 1:w - fr + 1] = 0.5
    f[fr:h - fr, fr - 1] = 0.5
    f[h - fr, fr - 1:w - fr + 1] = 1.3
    f[fr:h - fr, w - fr] = 1.3
    f[fr, fr:w - fr] = 0.75
    f[1, :] *= 1.25
    f[:, 1] *= 1.25
    f[0, :] *= 0.55
    f[:, 0] *= 0.55
    f[h - 1, :] *= 0.55
    f[:, w - 1] *= 0.55
    for ry in base.DOOR_RIB_YS:
        f[ry, fr:w - fr] *= 1.3
        f[ry + 1:ry + base.DOOR_RIB_H - 1, fr:w - fr] *= 1.08
        f[ry + base.DOOR_RIB_H - 1, fr:w - fr] *= 0.5
        f[ry + base.DOOR_RIB_H, fr:w - fr] *= 0.75
    return shade(rgb, f), leaf


def paint_over(rgb: np.ndarray, mask: np.ndarray, colour) -> np.ndarray:
    """Paint a flat colour over metal, keeping the metal's light and shade
    (bevels, ribs) as the stripe on SDCONC2 does."""
    lum = rgb.astype(np.float64).mean(axis=2)
    ref = lum[mask].mean() if mask.any() else 1.0
    k = np.clip(0.45 + 0.55 * lum / max(ref, 1.0), 0.45, 1.35)
    painted = np.clip(np.array(colour, np.float64)[None, None, :] * k[..., None], 0, 255).astype(np.uint8)
    return np.where(mask[..., None], painted, rgb)


def key_door(lump: str) -> np.ndarray:
    """SDDOOR1 with its frame, ribs and hazard band painted in the key's
    colour and a pass plate where SDDOOR1 has its star and "7".

    Legibility from afar is the brief: value survives sector light, hue
    does not (the switch sweep, LICENSES.md), so the key colour goes on
    the largest continuous areas the door has, the frame and the ribs, and
    the yellow door's yellow is a high value against the green leaf while
    the red door's red is a low one. Measured on the sheet (far view)."""
    ramp_name, tone, (txt_ramp, txt_tone) = KEY_INKS[lump]
    key = ramp_colour(ramp_name, tone)
    rgb, leaf = door_leaf_rgb()
    _, frame, ribs, plate, band = door_masks()
    wear_rng = rng_for(lump)
    worn = fbm(WIDE_W, WALL_H, 10, 3, wear_rng) > TRIM_WEAR
    rgb = paint_over(rgb, (frame | ribs) & ~worn, key)
    w, h = WIDE_W, WALL_H
    ov = Overlay(w, h)
    hi = ramp_colour("steel_blue", 0.95)
    lo = ramp_colour("steel_blue", 0.12)
    mid = ramp_colour("steel_blue", 0.70)
    R = base.RIVET_R
    fr = base.DOOR_FRAME
    for i in range(0, w, 16):
        for cx, cy in ((i + 8, fr / 2), (i + 8, h - fr / 2)):
            ov.ellipse(cx - R, cy - R, cx + R, cy + R, fill=lo)
            ov.ellipse(cx - R + 0.6, cy - R + 0.6, cx + R - 0.4, cy + R - 0.4, fill=hi)
    for j in range(fr, h - fr, 16):
        for cx, cy in ((fr / 2, j + 8), (w - fr / 2, j + 8)):
            ov.ellipse(cx - R, cy - R, cx + R, cy + R, fill=lo)
            ov.ellipse(cx - R + 0.6, cy - R + 0.6, cx + R - 0.4, cy + R - 0.4, fill=hi)
    cx, cy = base.WHEEL_CENTER
    ro, ri = base.WHEEL_R_OUT, base.WHEEL_R_IN
    ov.ellipse(cx - ro, cy - ro + 1, cx + ro, cy + ro + 1, fill=lo)
    ov.arc_ring(cx, cy, ro, ri, 0, 360, mid)
    ov.arc_ring(cx, cy, ro - 1, ri + 1, 200, 340, hi)
    for k in range(base.WHEEL_SPOKES):
        ang = np.deg2rad(k * 180 / base.WHEEL_SPOKES)
        dx, dy = np.cos(ang) * ri, np.sin(ang) * ri
        ov.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], mid, 2.2)
    ov.ellipse(cx - 4, cy - 4, cx + 4, cy + 4, fill=lo)
    ov.ellipse(cx - 3, cy - 3, cx + 3, cy + 3, fill=hi)
    # the pass plate: key colour, a dark border, four screws
    x0, y0, x1, y1 = PLATE_BOX
    ov.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, fill=ramp_colour("concrete_cold", 0.06))
    ov.rect(x0, y0, x1, y1, fill=key)
    for sx, sy in ((x0 + 3, y0 + 3), (x1 - 3, y0 + 3), (x0 + 3, y1 - 3), (x1 - 3, y1 - 3)):
        ov.ellipse(sx - 1, sy - 1, sx + 1, sy + 1, fill=lo)
    rgb = ov.composite(rgb)
    body, _ = glyph_masks(PASS_WORD)
    paste_mask(rgb, body, ramp_colour(txt_ramp, txt_tone), (x0 + x1) / 2, (y0 + y1) / 2 + 0.5)
    # the hazard band in the key's colour and black
    ys, xs = np.mgrid[0:h, 0:w]
    diag = ((xs + ys) // 6) % 2 == 0
    rgb = blend(rgb, key, (band & diag) * 0.85)
    rgb = blend(rgb, (0, 0, 0), (band & ~diag) * 0.6)
    return rgb


def tex_dooryy() -> np.ndarray:
    return key_door("SDDOORY")


def tex_doorr() -> np.ndarray:
    return key_door("SDDOORR")


# ============================================================ portal
PORT_W = 128
PORT_WARP = 14.0             # px of domain warp: how much the field swirls
PORT_GROUND = 0.30           # mosaic_cobalt: the body of the surface
PORT_FIL_POW = 7             # sharpness of the bright filaments


def portal_frames() -> list[np.ndarray]:
    """The portal's surface, four frames, tileable so it fills an opening
    of any size: a cobalt field warped on itself, with white filaments.
    Shows no 'other side' (MAP04 open point 6: the sheet asks)."""
    rng = rng_for("SDPORT")
    w = h = PORT_W
    n = fbm(w, h, 4, 5, rng, 0.55)
    wa, wb = fbm(w, h, 2, 3, rng), fbm(w, h, 2, 3, rng)
    wc, wd = fbm(w, h, 2, 3, rng), fbm(w, h, 2, 3, rng)
    pa, pb = fbm(w, h, 6, 3, rng), fbm(w, h, 6, 3, rng)
    g = grain(w, h, rng, 0.02)
    yy, xx = np.mgrid[0:h, 0:w]
    frames = []
    for k in range(FRAMES):
        dx = (periodic(wa, wb, k) - 0.5) * 2 * PORT_WARP
        dy = (periodic(wc, wd, k) - 0.5) * 2 * PORT_WARP
        sx = (xx + np.round(dx).astype(int)) % w
        sy = (yy + np.round(dy).astype(int)) % h
        f = n[sy, sx]
        f = 0.5 + (f - 0.5) * 0.7 + (periodic(pa, pb, k) - 0.5) * 0.5
        ridge = (1 - np.abs(2 * f - 1)) ** PORT_FIL_POW
        field = PORT_GROUND + (f - 0.5) * 0.35 + ridge * 0.75 + g
        rgb = any_to_rgb(np.clip(field, 0, 1), "mosaic_cobalt")
        rgb = blend(rgb, (255, 255, 255), np.clip((ridge - 0.55) * 2.2, 0, 1))
        frames.append(rgb)
    return frames


# ============================================================ factory gate
GATE_RAIL_TOP, GATE_RAIL_BOT, GATE_STILE, GATE_MID = 9, 7, 6, 64
GATE_GREEN = 0.50
GATE_BRACE_W = 4.0
ROLLERS_X = (24, 104)


def tex_gate1() -> np.ndarray:
    """Sliding factory gate, 128x128: green-painted corrugated sheet in a
    steel frame, a mid rail and a diagonal brace in each half, the roller
    track on top, a pull handle. Shut; set dressing."""
    rng = rng_for("SDGATE1")
    w = h = WIDE_W
    field = GATE_GREEN + (fbm(w, h, 3, 5, rng, 0.5) - 0.5) * 0.22 + grain(w, h, rng, 0.03)
    rgb = to_rgb(np.clip(field, 0, 1), "military_green")
    chip = fbm(w, h, 8, 3, rng) > 0.70
    rust = to_rgb(np.clip(0.36 + grain(w, h, rng, 0.05), 0, 1), "rust_brown")
    rgb = np.where(chip[..., None], rust, rgb)
    rgb = shade(rgb, corrugation(w, h))
    # grime and rust bleeding up from the ground
    rows = np.arange(h)[:, None] / h
    grime = np.clip((rows - 0.70) * 3.0, 0, 1) * fbm(w, h, 6, 3, rng)
    rgb = blend(rgb, ramp_colour("rust_brown", 0.18), np.clip(grime, 0, 0.6))
    ov = Overlay(w, h)
    steel = ramp_colour("steel_blue", 0.34)
    steel_hi = ramp_colour("steel_blue", 0.62)
    steel_lo = ramp_colour("steel_blue", 0.10)
    for y0, y1 in ((0, GATE_RAIL_TOP), (h - GATE_RAIL_BOT, h), (GATE_MID - 3, GATE_MID + 3)):
        ov.rect(0, y0, w, y1, fill=steel)
        ov.rect(0, y0, w, y0 + 1, fill=steel_hi)
        ov.rect(0, y1 - 1, w, y1, fill=steel_lo)
    for x0 in (0, w - GATE_STILE):
        ov.rect(x0, 0, x0 + GATE_STILE, h, fill=steel)
        ov.rect(x0, 0, x0 + 1, h, fill=steel_hi)
        ov.rect(x0 + GATE_STILE - 1, 0, x0 + GATE_STILE, h, fill=steel_lo)
    for ya, yb in ((GATE_RAIL_TOP, GATE_MID - 3), (GATE_MID + 3, h - GATE_RAIL_BOT)):
        ov.line([(GATE_STILE, yb), (w - GATE_STILE, ya)], steel_lo, GATE_BRACE_W + 1)
        ov.line([(GATE_STILE, yb), (w - GATE_STILE, ya)], steel, GATE_BRACE_W)
    for rx in ROLLERS_X:
        ov.ellipse(rx - 4, 0.5, rx + 4, 8.5, fill=steel_lo)
        ov.ellipse(rx - 2.5, 2, rx + 2.5, 7, fill=steel_hi)
    ov.rect(108, 54, 112, 76, fill=steel_lo)
    ov.rect(108.5, 55, 111, 75, fill=steel_hi)
    rgb = ov.composite(rgb)
    bleed = np.clip(fbm(w, h, 8, 3, rng, 0.5, aspect=6.0) - 0.55, 0, 1) * 2.0
    return blend(rgb, ramp_colour("rust_brown", 0.30), np.clip(bleed, 0, 0.5))


# ============================================================ glazing
PANE = 16                    # 4 x 8 panes in a 64 x 128 tile
SASH = 2                     # bar width, centred on the pane boundary
GLASS_TONE = 0.16            # steel_blue: night through dirty glass
BROKEN = ((3, 6),)          # (column, row) of the broken pane: one, or a band of
                             # windows shows the same holes in a row (first draft had two)
BOARDED = ((0, 5),)          # a pane boarded with plywood


def tex_wind1() -> np.ndarray:
    """Industrial glazing, 64x128, night outside: small panes in a steel
    sash, every pane its own dirt and reflection, two broken, one boarded."""
    rng = rng_for("SDWIND1")
    w, h = WALL_W, WALL_H
    ny, nx = h // PANE, w // PANE
    yy, xx = np.mgrid[0:h, 0:w]
    px, py = xx // PANE, yy // PANE
    tone = GLASS_TONE + rng.uniform(-0.05, 0.07, (ny, nx))
    field = tone[py, px] + (fbm(w, h, 4, 3, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.02)
    # a reflection: a soft diagonal band inside each pane
    lx, ly = xx % PANE, yy % PANE
    refl = np.exp(-(((lx - ly) - 2) ** 2) / 6.0) * 0.10
    field = field + refl
    rgb = to_rgb(np.clip(field, 0, 1), "steel_blue")
    soot = np.clip(fbm(w, h, 3, 4, rng) - 0.45, 0, 1) * 1.4
    rgb = blend(rgb, ramp_colour("khaki_olive", 0.12), np.clip(soot, 0, 0.55))
    for c, r in BROKEN:
        hole = (px == c) & (py == r) & ((lx + (PANE - ly)) > 7 + rng.integers(0, 4))
        hole &= ~((lx > 11) & (ly > 9))                       # a shard left in the corner
        dark = to_rgb(np.clip(0.03 + grain(w, h, rng, 0.02), 0, 1), "concrete_cold")
        rgb = np.where(hole[..., None], dark, rgb)
    for c, r in BOARDED:
        ply = (px == c) & (py == r)
        wood = to_rgb(np.clip(0.40 + (fbm(w, h, 2, 3, rng, 0.5, aspect=0.15) - 0.5) * 0.2, 0, 1), "rust_brown")
        rgb = np.where(ply[..., None], wood, rgb)
    sash = ((xx + SASH // 2) % PANE < SASH) | ((yy + SASH // 2) % PANE < SASH)
    paint = to_rgb(np.clip(0.30 + grain(w, h, rng, 0.03), 0, 1), "military_green")
    rgb = np.where(sash[..., None], paint, rgb)
    f = np.ones((h, w))
    f[sash & ((yy + SASH // 2) % PANE == 0)] = 1.25
    f[~sash & (((yy + SASH // 2) % PANE) == SASH)] = 0.70      # sash shadow on the glass
    return shade(rgb, f)


# ============================================================ works banner
SLOG_W, SLOG_H = 256, 64
SLOG_LINES = ("ТРАКТОРЫ —", "КОЛХОЗАМ!")    # "Tractors for the collective farms!" (MAP04 §7.2)
SLOG_SCALE = 2               # bigfont is 12 px; 2x nearest keeps our pixels whole
SLOG_RED = 0.70              # flag_red: kumach
SLOG_HEM = 3
SLOG_FOLD = 32               # one soft fold every 32 px (divides 256)


def tex_slog1() -> np.ndarray:
    """A works banner, 256x64: kumach stretched on the wall, two lines in
    our own alphabet (bigfont, D24) at 2x in cream, its 1 px shadow in deep
    red. Tiles along x as cloth; the words are meant to be seen once."""
    rng = rng_for("SDSLOG1")
    w, h = SLOG_W, SLOG_H
    xs = np.arange(w)[None, :]
    field = SLOG_RED + (fbm(w, h, 8, 3, rng, 0.5) - 0.5) * 0.08 + grain(w, h, rng, 0.025)
    rgb = to_rgb(np.clip(field, 0, 1), "flag_red")
    fold = 1 + 0.09 * np.sin(2 * np.pi * xs / SLOG_FOLD + 0.8 * (fbm(w, 1, 8, 2, rng)[0][None, :] - 0.5))
    rgb = shade(rgb, np.repeat(fold, h, axis=0))
    hem = to_rgb(np.full((h, w), 0.42), "flag_red")
    rows = np.arange(h)[:, None] * np.ones((1, w))
    rgb = np.where(((rows < SLOG_HEM) | (rows >= h - SLOG_HEM))[..., None], hem, rgb)
    f = np.ones((h, w))
    f[SLOG_HEM, :], f[h - SLOG_HEM - 1, :] = 0.70, 0.80
    rgb = shade(rgb, f)
    cream = ramp_colour("cream_yellow", 0.94)
    shadow = ramp_colour("flag_red", 0.22)
    line_h = 12 * SLOG_SCALE
    gap = (h - 2 * SLOG_HEM - 2 * line_h) / 3
    for i, line in enumerate(SLOG_LINES):
        body, shad = glyph_masks(line)
        cy = SLOG_HEM + gap * (i + 1) + line_h * i + line_h / 2
        paste_mask(rgb, shad, shadow, w / 2, cy, SLOG_SCALE)
        paste_mask(rgb, body, cream, w / 2, cy, SLOG_SCALE)
    # the paint cracked a little where the cloth folds
    crack = (fbm(w, h, 16, 2, rng) > 0.78)
    letters = (np.abs(rgb.astype(int) - np.array(cream)).sum(-1) == 0)
    return np.where((crack & letters)[..., None], np.array(ramp_colour("cream_yellow", 0.70), np.uint8), rgb)


# ============================================================ banners
CLOTH_X0, CLOTH_X1 = 6, 58   # 52 px: 13 stripes of 4 for the Legion
CLOTH_Y0, CLOTH_Y1 = 10, 110
ROD_Y0, ROD_Y1 = 6, 9
FRINGE_H = 4
CLOTH_FOLDS = 3              # soft vertical folds across the banner
DISC_C, DISC_R = (32, 48), 19
SWAS_CELL = 4.6              # one cell of the 5x5 hooked cross, px
# The hooked cross on the same 5x5 grid as the Reich's armband
# (gen_enemy.ARMBAND, D12): K is black.
SWASTIKA = ("K.KKK",
            "K.K..",
            "KKKKK",
            "..K.K",
            "KKK.K")
STRIPES = 13
STRIPE_W = 4
CANTON_W, CANTON_H = 7 * STRIPE_W, 40
STAR_STEP = (4, 5)           # stars on a 4 x 5 px lattice in the canton


def banner_ground() -> np.ndarray:
    """SDBRCK1's pixels: a banner tile beside a brick tile continues the bond."""
    return tex_brck1()


def cloth_mask(w: int = WALL_W, h: int = WALL_H) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    return (xx >= CLOTH_X0) & (xx < CLOTH_X1) & (yy >= CLOTH_Y0) & (yy < CLOTH_Y1)


def hang(rgb_wall: np.ndarray, cloth: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Put a banner (cloth RGB, same size as the wall, only its cloth area
    used) on the wall: shadow on the brick, folds, a rod and brackets, a
    gold fringe."""
    w, h = WALL_W, WALL_H
    m = cloth_mask()
    yy, xx = np.mgrid[0:h, 0:w]
    sh = np.roll(np.roll(m, 2, axis=0), 2, axis=1) & ~m
    rgb = np.where(sh[..., None], shade(rgb_wall, 0.50), rgb_wall)
    span = CLOTH_X1 - CLOTH_X0
    fold = 1 + 0.10 * np.sin(2 * np.pi * CLOTH_FOLDS * (xx - CLOTH_X0) / span)
    fold *= 1 + 0.04 * (fbm(w, h, 4, 2, rng, aspect=4.0) - 0.5)
    cloth = shade(cloth, fold)
    cloth = shade(cloth, 1 + grain(w, h, rng, 0.03))
    rgb = np.where(m[..., None], cloth, rgb)
    fringe = (xx >= CLOTH_X0) & (xx < CLOTH_X1) & (yy >= CLOTH_Y1) & (yy < CLOTH_Y1 + FRINGE_H)
    thread = np.where((xx % 2 == 0)[..., None], np.array(ramp_colour("hazard_yellow", 0.72), np.uint8),
                      np.array(ramp_colour("hazard_yellow", 0.48), np.uint8))
    rgb = np.where((fringe & ((xx % 2 == 0) | (yy < CLOTH_Y1 + 2)))[..., None], thread, rgb)
    ov = Overlay(w, h)
    ov.rect(1, ROD_Y0, w - 1, ROD_Y1, fill=ramp_colour("steel_blue", 0.22))
    ov.rect(1, ROD_Y0, w - 1, ROD_Y0 + 1, fill=ramp_colour("steel_blue", 0.55))
    for bx in (3, w - 5):
        ov.rect(bx, ROD_Y0 - 3, bx + 2, ROD_Y1 + 3, fill=ramp_colour("steel_blue", 0.12))
    return ov.composite(rgb)


def tex_flag1() -> np.ndarray:
    """The Fourth Reich's banner (D12): red, a white disc, the black hooked
    cross turned 45 degrees, on SDBRCK1."""
    rng = rng_for("SDFLAG1")
    w, h = WALL_W, WALL_H
    red = to_rgb(np.clip(0.72 + grain(w, h, rng, 0.02), 0, 1), "flag_red")
    ov = Overlay(w, h)
    cx, cy = DISC_C
    ov.ellipse(cx - DISC_R, cy - DISC_R, cx + DISC_R, cy + DISC_R, fill=ramp_colour("plaster_warm", 0.95))
    c45, s45 = np.cos(np.pi / 4), np.sin(np.pi / 4)
    for j, rowtxt in enumerate(SWASTIKA):
        for i, ch in enumerate(rowtxt):
            if ch != "K":
                continue
            corners = [(i - 2.5, j - 2.5), (i - 1.5, j - 2.5), (i - 1.5, j - 1.5), (i - 2.5, j - 1.5)]
            pts = [(cx + SWAS_CELL * (u * c45 - v * s45), cy + SWAS_CELL * (u * s45 + v * c45)) for u, v in corners]
            ov.polygon(pts, (0, 0, 0))
    cloth = ov.composite(red)
    return hang(banner_ground(), cloth, rng)


def tex_flag2() -> np.ndarray:
    """The Liberty Legion's banner (D12): the US flag hung vertically,
    thirteen stripes, the canton top left as the flag code hangs it, on
    SDBRCK1. Same inks as the Legion's shoulder patch except the canton
    (mosaic_cobalt instead of steel_blue, PALETTE_WHY)."""
    rng = rng_for("SDFLAG2")
    w, h = WALL_W, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    stripe = ((xx - CLOTH_X0) // STRIPE_W) % 2 == 0
    red = to_rgb(np.clip(0.72 + grain(w, h, rng, 0.02), 0, 1), "flag_red")
    white = to_rgb(np.clip(0.93 + grain(w, h, rng, 0.02), 0, 1), "plaster_warm")
    cloth = np.where(stripe[..., None], red, white)
    canton = (xx >= CLOTH_X0) & (xx < CLOTH_X0 + CANTON_W) & (yy >= CLOTH_Y0) & (yy < CLOTH_Y0 + CANTON_H)
    blue = any_to_rgb(np.clip(0.20 + grain(w, h, rng, 0.02), 0, 1), "mosaic_cobalt")
    cloth = np.where(canton[..., None], blue, cloth)
    sx, sy = STAR_STEP
    lx, ly = xx - CLOTH_X0, yy - CLOTH_Y0
    star = canton & (lx % sx == 2) & (ly % sy == 2) & (lx < CANTON_W - 1) & (ly < CANTON_H - 2)
    star &= ((lx // sx + ly // sy) % 2 == 0)
    cloth = np.where(star[..., None], np.array(ramp_colour("plaster_warm", 1.0), np.uint8), cloth)
    return hang(banner_ground(), cloth, rng)


# ================================================================ registry
# piece, builder, kind, (w, h), lumps, tiles, masked, description
PIECES = [
    ("SDBRCK1", tex_brck1, "wall", (64, 128), ["SDBRCK1"], True, False,
     "Soot-stained red factory brick, Stalin-era works: 16x8 bricks in running bond, lime mortar, "
     "some bricks browner or overfired, soot clouds and streaks."),
    ("SDBRCK2", tex_brck2, "wall", (64, 128), ["SDBRCK2"], True, False,
     "The same brick whitewashed to 64 (the works' dado), a dark rule on top, the bond showing "
     "through the lime, flaked where it was rubbed."),
    ("SDRUST1", tex_rust1, "wall", (64, 128), ["SDRUST1"], True, False,
     "Rusted corrugated sheet: galvanising surviving in patches, rust streaks in the troughs, a "
     "bolted lap seam, two small rust-through holes."),
    ("SDCHAN1", tex_chan1, "wall", (64, 128), ["SDCHAN1"], False, True,
     "Hanging chain and crane hook, MASKED (transparent ground) for a two-sided line's mid-texture. "
     "RGBA, hard alpha."),
    ("SDFLR4", tex_flr4, "flat", (64, 64), ["SDFLR4"], True, False,
     "Cast-iron chequer plate: 32 px plates, raised lozenges polished by boots, rust between them."),
    ("SDGRAT1", tex_grat1, "flat", (64, 64), ["SDGRAT1"], True, False,
     "Steel bar grating for the catwalks: bearing bars, cross bars, a panel frame, the dark below."),
    ("SDMOLT", molten_frames, "flat", (64, 64), [f"SDMOLT{i}" for i in range(1, FRAMES + 1)], True, False,
     "Molten metal, four frames for ANIMDEFS: a boiling heat field from red to white under plates "
     "of slag with glowing rims. The loop is seamless (frame 4 leads into frame 1)."),
    ("SDDOORY", tex_dooryy, "wall", (128, 128), ["SDDOORY"], False, False,
     "SDDOOR1 for the yellow lock: frame, ribs and hazard band in yellow, a yellow pass plate "
     "«ПРОПУСК» (pass) where SDDOOR1 has its star and «7»."),
    ("SDDOORR", tex_doorr, "wall", (128, 128), ["SDDOORR"], False, False,
     "SDDOOR1 for the red lock: frame, ribs and hazard band in red, a red pass plate «ПРОПУСК»."),
    ("SDPORT", portal_frames, "wall", (128, 128), [f"SDPORT{i}" for i in range(1, FRAMES + 1)], True, False,
     "The portal's surface, four frames: a cobalt field warped on itself with white filaments, "
     "tileable so it fills an opening of any size."),
    ("SDGATE1", tex_gate1, "wall", (128, 128), ["SDGATE1"], True, False,
     "Sliding factory gate: green-painted corrugated sheet in a steel frame, braces, the roller "
     "track on top, a pull handle. Shut."),
    ("SDWIND1", tex_wind1, "wall", (64, 128), ["SDWIND1"], True, False,
     "Industrial glazing, night outside: 4x8 small panes in a steel sash, dirt and reflections per "
     "pane, two broken, one boarded."),
    ("SDSLOG1", tex_slog1, "wall", (256, 64), ["SDSLOG1"], False, False,
     "Works banner «ТРАКТОРЫ — КОЛХОЗАМ!» (\"Tractors for the collective farms!\"), cream on "
     "kumach, set in our own alphabet (bigfont, D24) at 2x."),
    ("SDFLAG1", tex_flag1, "wall", (64, 128), ["SDFLAG1"], True, False,
     "The Fourth Reich's banner (D12) hung on SDBRCK1: red, white disc, black hooked cross."),
    ("SDFLAG2", tex_flag2, "wall", (64, 128), ["SDFLAG2"], True, False,
     "The Liberty Legion's banner (D12) hung on SDBRCK1: the US flag hung vertically."),
]

# piece -> (verdict, why). Written after looking at the sheet, PM gate.
RECOMMEND = {
    "SDBRCK1": ("yes", "The set's canvas. Reads as brick at 1x and at ~light 128; the soot keeps it from "
                "looking new without going to black. Mean luma sits under SDSTEL1's: a dark factory, "
                "which is the brief (light 80-128), but see the §6 note in the ask."),
    "SDBRCK2": ("yes", "The dado gives the hall a waist line, as SDTILE2 does in the offices; the whitewash "
                "is the brightest wall in the set, so it is where enemies will read best."),
    "SDRUST1": ("yes", "Distinct from the brick at a glance (grey-orange, vertical rhythm). The holes are "
                "small on purpose: at 4x they are a detail, at 1x a speck."),
    "SDCHAN1": ("yes, pending engine", "Reads as a chain and hook at 1x. Masked: RGBA mid-textures are "
                "standard GZDoom practice but NOT VERIFIED in our engine runs; one look in MAP04 settles it."),
    "SDFLR4": ("yes", "Cast iron, not steel: darker and rougher than any floor in the base set, so the tank "
               "line and the foundry read as heavy industry from the floor alone."),
    "SDGRAT1": ("yes", "Reads as see-through at 1x. The holes are near-black with a faint floor in them, "
                "never flat black (ART-BIBLE §5)."),
    "SDMOLT": ("yes", "The brightest surface in the game, as it should be. Four frames boil rather than "
               "flow; suggested ANIMDEFS rate 8 tics per frame (mod-engineer's call)."),
    "SDDOORY": ("yes", "From afar the door is a yellow frame round a green leaf: it reads as 'the yellow "
                "door' at 1/8 size and at ~light 128 (key-door section). Same leaf as SDDOOR1, pixel for "
                "pixel."),
    "SDDOORR": ("yes", "Red is the weaker of the two in value (a dark red beside dark green), so the red "
                "door leans on hue plus the plate and band; it still separates from SDDOOR1 and from the "
                "yellow door at 1/8 size. MAP04's red light at the portal does the rest."),
    "SDPORT": ("yes, colour is your call", "Cobalt-white is the one colour nothing else in the game uses, "
               "and it is the opposite of the foundry's heat, which makes the last room feel like another "
               "place. Alternatives on request: a sick green, or a red-black."),
    "SDGATE1": ("yes", "Reads as a gate, not a door: corrugation, braces, rollers. Green on purpose: it is "
                "the works' own paint, like SDDOOR1."),
    "SDWIND1": ("yes", "Dark as a night window must be; the sash grid carries it. Use it high (the "
                "clerestory), where its darkness is sky, not a hole in the wall."),
    "SDSLOG1": ("yes", "Our alphabet at 2x reads from across the hall, and the pixels match the menu and "
                "the HUD text. 256x64 is a new wall size (ART-BIBLE §2 lists up to 128x256): one row to add."),
    "SDFLAG1": ("yes", "Hang high (above 128): a banner behind an enemy's chest would break ART-BIBLE §6.3 "
                "(the armband must be the only red-white-black near a Reich soldier)."),
    "SDFLAG2": ("yes", "Same rule: high. Beside SDFLAG1 the two read as two allied flags at one glance, "
                "which is what LORE asks of the hall."),
}


# ================================================================== build
def quantise(piece: str, rgb: np.ndarray) -> Image.Image:
    """Quantise to the piece's palette version, no dither. RGBA in, RGBA
    out (hard alpha); RGB in, indexed out."""
    version = palette_of(piece)
    if rgb.shape[2] == 4:
        q = quantize_version(np.ascontiguousarray(rgb[..., :3]), version).convert("RGB")
        a = np.asarray(q).copy()
        a[rgb[..., 3] == 0] = 0
        out = np.dstack([a, rgb[..., 3]])
        return Image.fromarray(out.astype(np.uint8), "RGBA")
    if version == 1:
        return quantize(Image.fromarray(rgb, "RGB"))
    return quantize_version(rgb, version)


def frames_of(piece: str, builder) -> list[np.ndarray]:
    out = builder()
    return out if isinstance(out, list) else [out]


def save_rgb(rgb: np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "RGBA" if rgb.shape[2] == 4 else "RGB"
    Image.fromarray(rgb.astype(np.uint8), mode).save(path, optimize=True)
    return path


def as_rgb(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("RGBA" if img.mode == "RGBA" else "RGB"))


def mean_luma(rgb: np.ndarray) -> float:
    a = rgb[..., :3].astype(np.float64)
    if rgb.shape[2] == 4:
        m = rgb[..., 3] > 0
        a = a[m]
    return float((0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]).mean())


def build(out_dir: Path = OUT_DIR) -> tuple[list[dict], dict]:
    """Render every piece into out_dir. Returns (manifest entries, quantised
    RGB(A) arrays by lump)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    entries, arrays = [], {}
    for piece, builder, kind, size, lumps, tiles, masked, desc in PIECES:
        frames = frames_of(piece, builder)
        assert len(frames) == len(lumps), piece
        for lump, rgb in zip(lumps, frames):
            assert len(lump) <= 8 and lump.isupper() and lump.startswith("SD"), lump
            h, w = rgb.shape[:2]
            assert (w, h) == size, (lump, w, h)
            assert w % DIMENSION_MULTIPLE == 0 and h % DIMENSION_MULTIPLE == 0, lump
            img = quantise(piece, rgb)
            img.save(out_dir / f"{lump}.png", optimize=True)
            arrays[lump] = as_rgb(img)
        first = arrays[lumps[0]]
        colours = {tuple(int(v) for v in c) for c in first[..., :3].reshape(-1, 3)}
        entries.append({
            "piece": piece, "lumps": lumps, "kind": kind, "set": SET_NAME, "width": size[0], "height": size[1],
            "palette_version": palette_of(piece), "masked": masked, "tiles": tiles,
            "files": [f"work/art/batch4/{SET_NAME}/{lump}.png" for lump in lumps],
            "script": SCRIPT_REL, "seed": BATCH_SEED + SEED_OFFSET[piece],
            "colours_used": len(colours), "mean_luma": round(mean_luma(first), 1),
            "seam_score": round(tiling_seam_score(first[..., :3]), 2) if not masked else None,
            "description_en": desc, "status": "draft, proposed",
        })
        print(f"{piece:8s} {size[0]:3d}x{size[1]:3d} {kind:4s} v{palette_of(piece)} "
              f"colours={entries[-1]['colours_used']:3d} luma={entries[-1]['mean_luma']:6.1f} "
              f"seam={entries[-1]['seam_score']}")
    return entries, arrays


# ================================================================== views
LIGHT_128 = 0.5              # sheet view only: a flat multiply, NOT the engine's colormap
FAR_DIV = 8                  # far view: an 8x box average, what a mip level keeps
GIF_MS = 229                 # 8 tics at 35 Hz


def approved(lump: str) -> np.ndarray:
    for base_dir in (ASSET_WALLS, ASSET_FLATS):
        for p in base_dir.glob(f"*/{lump}.png"):
            with Image.open(p) as im:
                return np.asarray(im.convert("RGB"))
    raise FileNotFoundError(lump)


def far_view(rgb: np.ndarray, div: int = FAR_DIV) -> np.ndarray:
    """Box-average down by div, blown back up: the colour that survives
    distance. Not palette colours (sheet only)."""
    h, w = rgb.shape[:2]
    small = rgb[..., :3].astype(np.float64).reshape(h // div, div, w // div, div, 3).mean(axis=(1, 3))
    return np.repeat(np.repeat(small, div, 0), div, 1).astype(np.uint8)


def over(wall: np.ndarray, masked: np.ndarray) -> np.ndarray:
    a = (masked[..., 3:4] > 0)
    return np.where(a, masked[..., :3], wall).astype(np.uint8)


def row(tiles: list[np.ndarray]) -> np.ndarray:
    hmax = max(t.shape[0] for t in tiles)
    padded = [t if t.shape[0] == hmax else np.vstack([t, np.zeros((hmax - t.shape[0], t.shape[1], 3), np.uint8)])
              for t in tiles]
    return np.concatenate(padded, axis=1)


def context(piece: str, A: dict) -> np.ndarray:
    """The piece in its place, beside approved soviet-base and metro walls
    (or on approved floors), for the coherence check the PM asked for."""
    g = lambda n: A[n][..., :3] if n in A else approved(n)  # noqa: E731
    if piece == "SDBRCK1":
        return row([g("SDCONC1"), g("SDBRCK1"), g("SDBRCK1"), g("SDDOOR1"), g("SDBRCK1"), g("SDSTEL1")])
    if piece == "SDBRCK2":
        return row([g("SDTILE2"), g("SDBRCK2"), g("SDBRCK2"), g("SDSW1B"), g("SDBRCK2"), g("SDCONC1")])
    if piece == "SDRUST1":
        return row([g("SDSTEL1"), g("SDRUST1"), g("SDRUST1"), g("SDRUST1"), g("SDCONC1"), g("SDBRCK1")])
    if piece == "SDCHAN1":
        ch = A["SDCHAN1"]
        return row([over(g("SDBRCK1"), ch), over(g("SDRUST1"), ch), over(g("SDSTEL1"), ch), over(g("SDCONC1"), ch)])
    if piece == "SDFLR4":
        return np.vstack([row([g("SDFLR2"), g("SDFLR4"), g("SDFLR4"), g("SDFLR1")]),
                          row([g("SDFLR4"), g("SDFLR4"), g("SDFLR4"), g("SDMFLR1")])])
    if piece == "SDGRAT1":
        return np.vstack([row([g("SDFLR4"), g("SDGRAT1"), g("SDGRAT1"), g("SDFLR4")]),
                          row([g("SDFLR4"), g("SDGRAT1"), g("SDGRAT1"), g("SDFLR4")])])
    if piece == "SDMOLT":
        return np.vstack([row([g("SDFLR4")] * 4), row([g("SDMOLT1")] * 4), row([g("SDFLR4"), g("SDGRAT1"),
                                                                             g("SDGRAT1"), g("SDFLR4")])])
    if piece in ("SDDOORY", "SDDOORR"):      # the lock portal as MAP04 builds it
        return row([g("SDBRCK1"), g("SDSTAR1"), g(piece), g("SDSTAR1"), g("SDBRCK1")])
    if piece == "SDPORT":
        return row([g("SDSTEL1"), g("SDPORT1"), g("SDPORT1"), g("SDSTEL1"), g("SDCONC1")])
    if piece == "SDGATE1":
        return row([g("SDBRCK1"), g("SDGATE1"), g("SDGATE1"), g("SDBRCK1"), g("SDTUBB1")])
    if piece == "SDWIND1":
        return row([g("SDBRCK1"), g("SDWIND1"), g("SDWIND1"), g("SDWIND1"), g("SDBRCK1"), g("SDCONC1")])
    if piece == "SDSLOG1":
        top = row([g("SDBRCK1")[:64], g("SDSLOG1"), g("SDBRCK1")[:64]])
        return np.vstack([top, row([g("SDBRCK2")] * 6)])
    if piece in ("SDFLAG1", "SDFLAG2"):
        return row([g("SDBRCK1"), g("SDFLAG1"), g("SDFLAG2"), g("SDBRCK1"), g("SDCONC1")])
    raise KeyError(piece)


def scenes(A: dict) -> dict[str, np.ndarray]:
    """Two elevations and a floor strip, each 768 px wide, mixing the
    drafts with approved soviet-base and metro pieces."""
    g = lambda n: A[n][..., :3] if n in A else approved(n)  # noqa: E731
    B1 = g("SDBRCK1")
    clere = row([B1, g("SDWIND1"), g("SDWIND1"), g("SDWIND1"), B1, g("SDFLAG1"), g("SDFLAG2"), B1,
                 g("SDWIND1"), g("SDWIND1"), g("SDWIND1"), B1])
    band = row([B1[:64], B1[:64], B1[:64], B1[:64], g("SDSLOG1"), B1[:64], B1[:64], B1[:64], B1[:64]])
    ground = row([g("SDBRCK2"), g("SDBRCK2"), g("SDBRCK2"), g("SDBRCK2"), g("SDSTAR1"), g("SDDOORY"),
                  g("SDSTAR1"), g("SDRUST1"), over(g("SDBRCK2"), A["SDCHAN1"])])
    hall = np.vstack([clere, band, ground])
    portal = np.vstack([
        row([g("SDTUBB1"), g("SDGATE1"), g("SDBRCK1"), g("SDBRCK1"), g("SDTUBB1"), g("SDSTEL1"),
             g("SDCONC1"), g("SDCONC1"), g("SDTUNL1")]),
        row([g("SDSTEL1"), g("SDPORT1"), g("SDPORT1"), g("SDSTEL1"), g("SDSTAR1"), g("SDDOORR"), g("SDSTAR1")]),
    ])
    floor = row([g("SDFLR2"), g("SDFLR1"), g("SDFLR4"), g("SDGRAT1"), g("SDMOLT1"), g("SDMOLT1"),
                 g("SDGRAT1"), g("SDFLR4"), g("SDRAIL1"), g("SDMFLR2"), g("SDFLR2"), g("SDFLR3")])
    return {"hall": hall, "portal": portal, "floor": floor}


SCENE_LEGEND = {
    "hall": ("Assembly hall (elevation). Top: clerestory SDWIND1 between SDBRCK1 piers, the two banners "
             "side by side high on the middle pier (where I recommend they hang). Middle: SDSLOG1 on SDBRCK1. "
             "Bottom: the SDBRCK2 dado, the yellow lock (approved SDSTAR1 | SDDOORY | SDSTAR1, as MAP04 "
             "builds it), SDRUST1, and SDCHAN1 hanging in front of SDBRCK2."),
    "portal": ("Portal hall (elevation). Top: approved SDTUBB1 and SDTUNL1 (metro), SDGATE1, SDBRCK1, approved "
               "SDSTEL1 and SDCONC1. Bottom: the drum (approved SDSTEL1) round SDPORT1, then the red lock "
               "(approved SDSTAR1 | SDDOORR | SDSTAR1)."),
    "floor": ("Floors from above, left to right: approved SDFLR2, SDFLR1 (lane); SDFLR4, SDGRAT1, SDMOLT1 x2, "
              "SDGRAT1, SDFLR4; approved SDRAIL1, SDMFLR2 (metro), SDFLR2, SDFLR3."),
}


def write_gif(frames: list[np.ndarray], piece: str, path: Path) -> Path:
    imgs = [quantise(piece, f) for f in frames]
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=GIF_MS, loop=0, optimize=False)
    return path


def gif_tag(label: str, path: Path, zoom: int, size: tuple[int, int]) -> str:
    import base64
    data = "data:image/gif;base64," + base64.b64encode(path.read_bytes()).decode("ascii")
    w, h = size
    return (f'<div class="v"><b>{html.escape(label)}</b><img class="px" src="{data}" width="{w * zoom}" '
            f'height="{h * zoom}" alt="{html.escape(label)}"></div>')


def make_views(entries: list[dict], A: dict, view_dir: Path = VIEW_DIR) -> dict:
    """Every sheet-only image: tiles, light, far, context, scenes, GIFs."""
    view_dir.mkdir(parents=True, exist_ok=True)
    V = {}
    for e in entries:
        piece, lumps = e["piece"], e["lumps"]
        first = A[lumps[0]]
        rgb = first[..., :3] if first.shape[2] == 3 else over(np.full(first.shape[:2] + (3,), 40, np.uint8), first)
        V[piece + "_tile"] = save_rgb(np.tile(first, (2, 2, 1)), view_dir / f"{piece}_tile2x2.png")
        V[piece + "_dark"] = save_rgb(shade(rgb, LIGHT_128), view_dir / f"{piece}_light128.png")
        ctx = context(piece, A)
        V[piece + "_ctx"] = save_rgb(ctx, view_dir / f"{piece}_context.png")
        V[piece + "_ctx_dark"] = save_rgb(shade(ctx, LIGHT_128), view_dir / f"{piece}_context_light128.png")
        if len(lumps) > 1:
            builder = next(p[1] for p in PIECES if p[0] == piece)
            V[piece + "_gif"] = write_gif(builder(), piece, view_dir / f"{piece}_anim.gif")
            V[piece + "_strip"] = save_rgb(np.concatenate([A[l][..., :3] for l in lumps], axis=1),
                                           view_dir / f"{piece}_frames.png")
    for name, sc in scenes(A).items():
        V["scene_" + name] = save_rgb(sc, view_dir / f"scene_{name}.png")
        V["scene_" + name + "_dark"] = save_rgb(shade(sc, LIGHT_128), view_dir / f"scene_{name}_light128.png")
    doors = [approved("SDDOOR1"), A["SDDOORY"], A["SDDOORR"]]
    strip = row(doors)
    V["doors"] = save_rgb(strip, view_dir / "doors.png")
    V["doors_far"] = save_rgb(far_view(strip), view_dir / "doors_far.png")
    V["doors_far_dark"] = save_rgb(shade(far_view(strip), LIGHT_128), view_dir / "doors_far_light128.png")
    portals = row([approved("SDSTAR1"), A["SDDOORY"], approved("SDSTAR1"), approved("SDSTAR1"), A["SDDOORR"],
                   approved("SDSTAR1")])
    V["portals_far"] = save_rgb(far_view(portals), view_dir / "portals_far.png")
    V["portals_far_dark"] = save_rgb(shade(far_view(portals), LIGHT_128), view_dir / "portals_far_light128.png")
    return V


def door_far_colours(A: dict) -> dict[str, tuple[int, int, int]]:
    """Mean colour of each door at the far view: the number the key-door
    section quotes and the test holds."""
    out = {}
    for lump, rgb in (("SDDOOR1", approved("SDDOOR1")), ("SDDOORY", A["SDDOORY"]), ("SDDOORR", A["SDDOORR"])):
        out[lump] = tuple(int(v) for v in rgb[..., :3].reshape(-1, 3).mean(axis=0).round())
    return out


# ================================================================== sheet
INTRO = (
    "<b>Batch 4, the factory «Танкоград» (MAP04, BACKLOG N6): the thirteen industrial pieces of "
    "MAP04-factory §7.2, as drafts.</b> Brick and its whitewashed dado, rusted corrugated sheet, a "
    "chain and hook, cast-iron and grating floors, molten metal (4 frames), the two key doors, the "
    "portal (4 frames), a sliding gate, night glazing, the works banner and the two enemy banners. "
    "All procedural, one seed per piece, as the metro. The only lettering (the banner, the pass "
    "plates) is set in <b>our own alphabet</b> from <code>assets/fonts/bigfont/</code> (D24, D27), so "
    "every piece reproduces byte for byte on both machines. Five pieces use <b>palette v2</b> and say "
    "why on their card. Each card shows the piece at 4x, 1x, tiled 2x2, at ~light 128 and in place "
    "beside approved soviet-base and metro walls; the first section shows the factory assembled. "
    "Nothing here is in <code>assets/</code>.")

ASK = (
    "<ol>"
    "<li><b>Yes / no per piece.</b> Each card is independent; my verdict is on each one.</li>"
    "<li><b>The key doors</b> (section 2): do the yellow and the red door read as theirs from across the "
    "hall? The pass plate says «ПРОПУСК» (pass), which ties the keys to MAP04's open point 3 (keys as "
    "passes).</li>"
    "<li><b>A finding for the level designer, not a texture question:</b> MAP04 flanks both locks with the "
    "red SDSTAR1 plaques. At the yellow lock that frames the door; at the red lock it makes three red "
    "blocks in a row, and from afar the red door reads as the green leaf <i>between</i> reds rather than "
    "as the red one (section 2, the portals at 1/8). I would take the plaques off the red lock, or move "
    "them a tile out, and keep them at the yellow one. Your call with level-designer.</li>"
    "<li><b>Palette v2 for brick, the Legion's canton and the portal</b> (no new version, D45's ramps): "
    "ok? The alternative brick in v1 is browner (rust_brown) and reads less as a Soviet works.</li>"
    "<li><b>The portal's colour</b> (MAP04 open point 6): cobalt-white, not showing the other side. "
    "Keep, or ask for green / red-black.</li>"
    "<li><b>Value note (ART-BIBLE §6.1)</b>: brick, rust and the night glazing sit darker than the "
    "0.45-0.70 wall band the bible asks for (a factory at light 80-128 is a dark place). The Reich's "
    "dark uniforms will separate less against SDBRCK1 than against concrete. The fix, if the walk "
    "shows it, is light and SDBRCK2's whitewash at fighting height, not a paler brick. Your call "
    "whether to accept it now or judge it in the map.</li>"
    "</ol>")


def card(e: dict, V: dict, A: dict) -> str:
    piece, lumps = e["piece"], e["lumps"]
    size = (e["width"], e["height"])
    tile = (size[0] * 2, size[1] * 2)
    first = OUT_DIR / f"{lumps[0]}.png"
    views = (sheetlib.view("4x", first, sheetlib.ZOOM, size) + sheetlib.view("1x", first, 1, size)
             + sheetlib.view("2x2 tile (2x)", V[piece + "_tile"], 2, tile)
             + sheetlib.view("~light 128 (2x)", V[piece + "_dark"], 2, size))
    anim = ""
    if len(lumps) > 1:
        anim = ('<div class="row">' + gif_tag(f"animated, {GIF_MS} ms/frame (4x)", V[piece + "_gif"], 4, size)
                + sheetlib.view(f"frames {lumps[0]}-{lumps[-1]} (2x)", V[piece + "_strip"], 2,
                                (size[0] * len(lumps), size[1])) + "</div>")
    with Image.open(V[piece + "_ctx"]) as im:
        csize = im.size
    ctx = ('<div class="row">' + sheetlib.view("in place, with approved pieces (2x)", V[piece + "_ctx"], 2, csize)
           + "</div><div class=\"row\">"
           + sheetlib.view("in place, ~light 128 (2x)", V[piece + "_ctx_dark"], 2, csize) + "</div>")
    verdict, why = RECOMMEND[piece]
    pal = f'v{e["palette_version"]}'
    pal_why = ""
    if piece in PALETTE_WHY:
        pal_why = f'<dt>Why v2</dt><dd style="white-space:normal;font-family:inherit">{html.escape(PALETTE_WHY[piece])}</dd>'
    names = ", ".join(lumps)
    return (f'<div class="card rec"><span class="tag">recommended: {html.escape(verdict)}</span>'
            f'<h3>{html.escape(names)}</h3><p class="desc">{html.escape(e["description_en"])}</p>'
            f'<div class="row">{views}</div>{anim}{ctx}'
            f'<dl><dt>Kind</dt><dd>{e["kind"]}{" (masked, RGBA)" if e["masked"] else ""}</dd>'
            f'<dt>Size</dt><dd>{e["width"]}&times;{e["height"]}</dd>'
            f'<dt>Palette</dt><dd>{pal}</dd>{pal_why}'
            f'<dt>Colours used</dt><dd>{e["colours_used"]}</dd>'
            f'<dt>Mean luma</dt><dd>{e["mean_luma"]}</dd>'
            f'<dt>Seam ratio</dt><dd>{e["seam_score"] if e["seam_score"] is not None else "n/a (masked)"}'
            f'{"" if e["tiles"] else " (not meant to tile)"}</dd>'
            f'<dt>Origin</dt><dd>(a) {SCRIPT_REL}, seed {e["seed"]}'
            f'{" + SDDOOR1 seed " + str(DOOR1_SEED) if piece in KEY_INKS else ""}</dd>'
            f'<dt>Status</dt><dd>draft, proposed</dd>'
            f'<dt>Verdict</dt><dd style="white-space:normal;font-family:inherit">{html.escape(why)}</dd></dl></div>')


def reference_strip() -> str:
    """The approved walls the set has to sit beside, for the eye's reference."""
    names = ["SDCONC1", "SDCONC2", "SDSTEL1", "SDDOOR1", "SDTILE2", "SDMARB1", "SDTUBB1", "SDTUNL1"]
    paths = []
    for n in names:
        for base_dir in (ASSET_WALLS,):
            p = next(iter(base_dir.glob(f"*/{n}.png")), None)
            if p:
                paths.append((n, p))
    out = '<div class="row" style="align-items:flex-end">'
    for n, p in paths:
        with Image.open(p) as im:
            out += sheetlib.view(f"{n} ✓", p, 2, im.size)
    return out + "</div>"


def build_sheet(entries: list[dict], V: dict, A: dict, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    far = door_far_colours(A)
    def sc(name, w=768):
        with Image.open(V["scene_" + name]) as im:
            size = im.size
        return ('<div class="row">' + sheetlib.view(f"{name} (2x)", V["scene_" + name], 2, size) + "</div>"
                + '<div class="row">' + sheetlib.view(f"{name}, ~light 128 (2x)", V["scene_" + name + "_dark"], 2, size)
                + "</div>" + f'<p class="lead">{html.escape(SCENE_LEGEND[name])}</p>')
    scenes_html = sc("hall") + sc("portal") + sc("floor")
    doors_html = (
        '<div class="row">' + sheetlib.view("SDDOOR1 ✓ | SDDOORY | SDDOORR (2x)", V["doors"], 2, (384, 128)) + "</div>"
        + '<div class="row">' + sheetlib.view("the same at 1/8 size: an 8x box average, blown up (2x)",
                                              V["doors_far"], 2, (384, 128))
        + sheetlib.view("1/8 size, ~light 128 (2x)", V["doors_far_dark"], 2, (384, 128)) + "</div>"
        + '<div class="row">' + sheetlib.view("the two lock portals (SDSTAR1 either side) at 1/8 size (1x)",
                                              V["portals_far"], 1, (768, 128))
        + sheetlib.view("the same, ~light 128 (1x)", V["portals_far_dark"], 1, (768, 128)) + "</div>"
        + sheetlib.table(["door", "mean colour (R, G, B)"],
                         [[k, ", ".join(str(c) for c in v)] for k, v in far.items()], numeric_from=1))
    cards = "".join(card(e, V, A) for e in entries)
    sections = [
        ("1. The factory assembled",
         "Drafts and approved pieces (soviet base, metro) side by side in two elevations and a floor strip, so "
         "the set can be judged as the same game. A coherence check, not a mockup of MAP04's rooms.",
         scenes_html),
        ("2. The key doors from afar",
         "The brief: the locked doors must read by colour from across the hall. Shown beside SDDOOR1 (✓) and "
         "averaged down to 1/8 size, which is about what a mip level keeps at the far end of the assembly hall. "
         "Yellow is a high value on green and holds even at ~light 128; red is a hue more than a value, so its "
         "door has the plate and the band to help, and MAP04 lights the red portal red (NOT VERIFIED in engine: K4).",
         doors_html),
        ("3. The thirteen pieces", "", f'<div class="grid">{cards}</div>'),
        ("4. What I need from you", "", f'<div class="ask">{ASK}</div>'),
        ("5. Approved walls for reference (2x)", "", reference_strip()),
        ("6. Palette", "", gen_metro.palette_v2_swatches()),
    ]
    out = out_dir / f"{stamp}_F3_batch4-factory.html"
    return sheetlib.write_sheet(
        out, lang="en", title="Soviet Doom — factory set «Танкоград», batch 4 (MAP04)",
        subtitle="F3 · MAP04 · BACKLOG N6 · drafts for the CEO, nothing here is in assets/",
        intro=INTRO, sections=sections,
        footer=(f"Origin (a): procedural, {SCRIPT_REL}, seed {BATCH_SEED}+offset (1-15); SDDOORY and SDDOORR "
                f"replay SDDOOR1's seed {DOOR1_SEED}. Palette docs/art/palette.json v1, and v2 (D45) where a "
                "card says so; not modified. Lettering from assets/fonts/bigfont (D24), no system font (D27). "
                "Licence: own work, CC BY-NC-SA 4.0 (D15). The '~light 128' view is a flat x0.5 multiply and the "
                "far view an 8x box average, both for orientation, not the engine's colormap or mipmaps (NOT "
                "VERIFIED in GZDoom). The animated pieces need ANIMDEFS (mod-engineer); the masked chain is "
                "an RGBA mid-texture, NOT VERIFIED in our engine runs."))


def main() -> None:
    assert {p[0] for p in PIECES} == set(SEED_OFFSET), "SEED_OFFSET and PIECES disagree"
    assert len(set(SEED_OFFSET.values())) == len(SEED_OFFSET), "two pieces share a seed"
    entries, arrays = build()
    V = make_views(entries, arrays)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    sheet = build_sheet(entries, V, arrays, stamp)
    MANIFEST.write_text(json.dumps({
        "batch": 4, "phase": "F3", "set": SET_NAME, "script": SCRIPT_REL, "batch_seed": BATCH_SEED,
        "status": "drafts for the CEO; nothing in assets/", "backlog": "N6", "map": "MAP04 §7.2",
        "door_far_colours": door_far_colours(arrays), "preview": str(sheet.relative_to(PROJECT_ROOT).as_posix()),
        "pieces": entries,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"sheet: {sheet}\nmanifest: {MANIFEST}")


if __name__ == "__main__":
    main()
