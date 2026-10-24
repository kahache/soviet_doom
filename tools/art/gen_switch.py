"""Batch 2, priority 1 — the switch texture (SDSWT1 off / SDSWT2 on).

Run with the project venv:  .venv/bin/python tools/art/gen_switch.py

Asked for by `level-designer` as blocking item A3: MAP01 has three switches
and is currently texturing them with SDDOOR1, which reads as a door. The
player must tell a switch from a wall at a glance, and the lit state from
the unlit one from across a room.

This script produces a SWEEP: four variants, each in both states, each shown
on the two walls it will actually sit on (SDCONC1 concrete and SDSTEL1 green
steel), at 1x, at 4x and point-sampled down to 16 px tall. The CEO picks one
variant; only then does a lump called SDSWT1/SDSWT2 exist. Nothing is written
to assets/.

Outputs (work/ is gitignored):
  work/art/batch2/switch/*.png          variants, contexts, far views
  work/art/batch2/switch/manifest.json  measurements quoted on the sheet
  work/art/batch2/2026-..-.._....._F2_batch2-switch-sweep.html      (EN)
  work/art/batch2/ru/2026-..-.._....._F2_batch2-switch-sweep.html   (RU, D7)

Art direction behind the four variants (ART-BIBLE §5, §6):

  What survives Doom's sector lighting is VALUE, not hue. Measured on the
  approved hosts: SDCONC1 mean luma 147, SDSTEL1 mean luma 101. The top of
  the flag_red ramp is luma 104 - the same value as the green steel - so a
  red lever or a red button is INVISIBLE on SDSTEL1 once the sector light
  drops. Every variant therefore carries its identity in value and keeps red
  decorative at most:
    - panel: dark (steel_blue low, luma ~60) -> 87 below concrete, 41 below
      steel, so the switch is a dark mass on either host;
    - state: a lamp lens going from luma ~45 to ~235, over an area big
      enough to survive an 8x point-sample (the "16 px tall" test);
    - accent: hazard_yellow (ramp top luma 201), which ART-BIBLE §3 already
      assigns to industrial accents, leaving flag_red to mean *meaning*
      (stripes, plaques, posters) as §6.3 requires.
  The 3 px border of every variant is a flat dark recess, not wall material:
  that is what makes one texture sit correctly on concrete AND on steel.

All sizes in texture pixels (= Doom map units on a wall).
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import (  # noqa: E402
    FONT_POSTER, Overlay, blend, fbm, grain, load_palette, ramp_colour,
    save_indexed, shade, to_rgb,
)
import sheetlib  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "work" / "art" / "batch2" / "switch"
SHEET_DIR = PROJECT_ROOT / "work" / "art" / "batch2"
MANIFEST = OUT_DIR / "manifest.json"
SCRIPT_REL = "tools/art/gen_switch.py"

# Own seed space, far from gen_soviet_base's BATCH_SEED 1977 (whose offsets
# 1..12 are taken) so the two batches can never collide on a seed.
BATCH_SEED = 2077
SEED_OFFSET = {"A": 1, "B": 2, "C": 3, "D": 4}

W, H = 64, 128          # a switch is one 64-grid wall segment: drops straight in

# The two approved walls the switch has to sing against (level-designer).
HOSTS = {
    "SDCONC1": PROJECT_ROOT / "assets" / "textures" / "soviet_base" / "SDCONC1.png",
    "SDSTEL1": PROJECT_ROOT / "assets" / "textures" / "soviet_base" / "SDSTEL1.png",
}
CONTEXT_TILES = 3       # host | switch | host, so the switch is seen framed

# The "16 px tall and from far away" test: Doom's software renderer point-
# samples, so the honest far view is a NEAREST decimation, not a smooth
# thumbnail. 128 / 8 = 16 px tall, exactly what level-designer asked for.
FAR_DIVISOR = 8

# --- panel armature, shared by every variant ----------------------------
RECESS = 3              # flat dark border: reads as a recess on any host wall
RECESS_TONE = 0.10      # concrete_cold ramp position of that border
BEVEL = 2               # lit top/left, dark bottom/right: the box sits proud
BEVEL_LIGHT, BEVEL_DARK = 1.45, 0.55
PLATE_MID = 0.17        # steel_blue ramp: luma ~62, dark against both hosts
PLATE_BLOTCH = 0.10
PLATE_GRAIN = 0.03
BOLT_R = 1.7
BOLT_INSET = 6

# --- lamp lens (the state cue in variants B, C, D) ----------------------
LENS_OFF = 0.10         # khaki_olive: a dead lens is dark olive glass, not black
LENS_ON = 0.97          # cream_yellow top: luma ~230
LENS_CORE = 0.62        # fraction of the lens radius painted pure white when lit
GLOW_GAIN = 0.55        # how much the lit lens spills onto the plate
GLOW_R = 20.0           # px, spill radius
BEZEL_W = 2.0
BEZEL_TONE = 0.52       # steel_blue: the ring catches light in both states

# --- hazard chevrons (variant D's identity, present in both states) -----
CHEVRON_W = 5           # band width inside the panel
CHEVRON_PITCH = 7       # px along the diagonal
CHEVRON_LIGHT, CHEVRON_DARK = 0.88, 0.08   # hazard_yellow / near black

# --- lever and slider ---------------------------------------------------
LEVER_TONE = 0.78       # hazard_yellow: luma ~181, the brightest mass when unlit
SLOT_TONE = 0.05        # recessed slot, concrete_cold low
HANDLE_RED = 0.90       # flag_red, variant A only (the literal rubilnik grip)

# --- lettering ----------------------------------------------------------
STENCIL = "ПУСК"        # "START", the label painted next to a Soviet starter
STENCIL_SIZE = 13
STENCIL_TONE = 0.80     # cream_yellow

VARIANT_IDS = ("A", "B", "C", "D")
RECOMMENDED = "D"


def rng_for(key: str) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + SEED_OFFSET[key])


def luma(rgb: np.ndarray) -> np.ndarray:
    a = rgb.astype(np.float64)
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


# ====================================================== shared armature
def plate(rng: np.random.Generator) -> np.ndarray:
    """Dark steel panel inside a flat recess border.

    The border is deliberately NOT wall material: one texture has to sit on
    concrete (luma 147) and on green steel (luma 101), and a flat dark gap
    reads as a shadow against both, where a concrete border would read as a
    patch on the steel wall.
    """
    field = PLATE_MID + (fbm(W, H, 3, 4, rng, 0.5) - 0.5) * PLATE_BLOTCH
    field += grain(W, H, rng, PLATE_GRAIN)
    rgb = to_rgb(field, "steel_blue")

    # recess border
    border = np.zeros((H, W), bool)
    border[:RECESS, :] = border[-RECESS:, :] = True
    border[:, :RECESS] = border[:, -RECESS:] = True
    rgb = np.where(border[..., None], np.array(ramp_colour("concrete_cold", RECESS_TONE)), rgb)

    # bevel: the panel is a box screwed onto the wall, lit from the top left
    f = np.ones((H, W))
    f[RECESS:RECESS + BEVEL, RECESS:-RECESS] = BEVEL_LIGHT
    f[RECESS:-RECESS, RECESS:RECESS + BEVEL] = BEVEL_LIGHT
    f[-RECESS - BEVEL:-RECESS, RECESS:-RECESS] = BEVEL_DARK
    f[RECESS:-RECESS, -RECESS - BEVEL:-RECESS] = BEVEL_DARK
    return shade(rgb, f)


def bolts(ov: Overlay, rng: np.random.Generator) -> None:
    """Four hex bolts holding the panel on, at the panel corners."""
    hi = ramp_colour("steel_blue", 0.80)
    lo = ramp_colour("steel_blue", 0.08)
    for cx in (RECESS + BOLT_INSET, W - RECESS - BOLT_INSET):
        for cy in (RECESS + BOLT_INSET, H - RECESS - BOLT_INSET):
            ov.ellipse(cx - BOLT_R, cy - BOLT_R, cx + BOLT_R, cy + BOLT_R, fill=lo)
            ov.ellipse(cx - BOLT_R + 0.5, cy - BOLT_R + 0.5, cx + BOLT_R - 0.6, cy + BOLT_R - 0.6, fill=hi)


def glow(rgb: np.ndarray, cx: float, cy: float, radius: float = GLOW_R,
         gain: float = GLOW_GAIN) -> np.ndarray:
    """Spill a lit lens onto the surrounding plate.

    This is what makes the ON state survive the 8x point-sample: the lens
    itself may be only a few pixels wide once decimated, but the halo lifts
    the whole neighbourhood, so the switch reads as "lit" as a mass.
    """
    ys = np.arange(H)[:, None] - cy
    xs = np.arange(W)[None, :] - cx
    d = np.sqrt(xs ** 2 + ys ** 2)
    mask = gain * np.exp(-(d / radius) ** 2)
    return blend(rgb, ramp_colour("cream_yellow", 0.88), np.clip(mask, 0, 1))


def lens(ov: Overlay, cx: float, cy: float, r: float, on: bool) -> None:
    """Round indicator lens with a steel bezel. Dark olive glass when dead,
    cream with a white core when lit."""
    ov.ellipse(cx - r - BEZEL_W, cy - r - BEZEL_W, cx + r + BEZEL_W, cy + r + BEZEL_W,
               fill=ramp_colour("steel_blue", BEZEL_TONE))
    ov.ellipse(cx - r - BEZEL_W, cy - r - BEZEL_W, cx + r + BEZEL_W, cy + r + BEZEL_W,
               outline=ramp_colour("steel_blue", 0.05), width=1.0)
    if on:
        ov.ellipse(cx - r, cy - r, cx + r, cy + r, fill=ramp_colour("cream_yellow", LENS_ON))
        rc = r * LENS_CORE
        ov.ellipse(cx - rc, cy - rc, cx + rc, cy + rc, fill=(255, 255, 255))
    else:
        ov.ellipse(cx - r, cy - r, cx + r, cy + r, fill=ramp_colour("khaki_olive", LENS_OFF))
        # a dead lens still catches a highlight on its upper left: glass, not a hole
        ov.ellipse(cx - r * 0.7, cy - r * 0.7, cx - r * 0.1, cy - r * 0.1,
                   fill=ramp_colour("khaki_olive", 0.34))


def lens_bar(ov: Overlay, x0: float, y0: float, x1: float, y1: float, on: bool) -> None:
    """Rectangular lit panel (variant D): more lit area than a round lens,
    which is what reads best when the wall is 16 px tall."""
    ov.rect(x0 - BEZEL_W, y0 - BEZEL_W, x1 + BEZEL_W, y1 + BEZEL_W,
            fill=ramp_colour("steel_blue", BEZEL_TONE), outline=ramp_colour("steel_blue", 0.05))
    if on:
        ov.rect(x0, y0, x1, y1, fill=ramp_colour("cream_yellow", LENS_ON))
        inset = (y1 - y0) * (1 - LENS_CORE) / 2
        ov.rect(x0 + inset, y0 + inset, x1 - inset, y1 - inset, fill=(255, 255, 255))
    else:
        ov.rect(x0, y0, x1, y1, fill=ramp_colour("khaki_olive", LENS_OFF))
        ov.rect(x0, y0, x1, y0 + 2, fill=ramp_colour("khaki_olive", 0.30))


def slot(ov: Overlay, x0: float, y0: float, x1: float, y1: float) -> None:
    ov.rect(x0, y0, x1, y1, fill=ramp_colour("concrete_cold", SLOT_TONE))
    ov.rect(x0, y0, x1, y0 + 1, fill=ramp_colour("concrete_cold", 0.30))


def lever_block(ov: Overlay, x0: float, y0: float, x1: float, y1: float,
                tone: float = LEVER_TONE, ramp_name: str = "hazard_yellow") -> None:
    """The moving mass: a painted metal handle. Drawn with its own highlight
    and shadow so it keeps a shape, not a flat blob, once quantised."""
    base = ramp_colour(ramp_name, tone)
    ov.rect(x0, y0, x1, y1, fill=base)
    ov.rect(x0, y0, x1, y0 + 1.5, fill=ramp_colour(ramp_name, min(1.0, tone + 0.18)))
    ov.rect(x0, y1 - 1.5, x1, y1, fill=ramp_colour(ramp_name, max(0.0, tone - 0.30)))
    ov.rect(x0, y0, x1, y1, outline=ramp_colour("concrete_cold", 0.04), width=1.0)


def chevrons(rgb: np.ndarray) -> np.ndarray:
    """Hazard band around the panel (variant D).

    Unlike a lamp this is present in BOTH states, so the surface says
    "machinery, not wall" even when the switch is dead - which is the
    level-designer's actual complaint about using SDDOOR1 as a stand-in.
    """
    ys = np.arange(H)[:, None]
    xs = np.arange(W)[None, :]
    stripe = ((xs + ys) % CHEVRON_PITCH) < (CHEVRON_PITCH // 2)
    band = np.zeros((H, W), bool)
    i0, i1 = RECESS, RECESS + CHEVRON_W
    band[i0:-i0, i0:i1] = band[i0:-i0, -i1:-i0] = True
    band[i0:i1, i0:-i0] = band[-i1:-i0, i0:-i0] = True
    light = np.array(ramp_colour("hazard_yellow", CHEVRON_LIGHT))
    dark = np.array(ramp_colour("concrete_cold", CHEVRON_DARK))
    painted = np.where(stripe[..., None], light, dark)
    return np.where(band[..., None], painted, rgb).astype(np.uint8)


def stencil(ov: Overlay, cy: float, text: str = STENCIL) -> None:
    ov.text(W / 2, cy, text, STENCIL_SIZE, ramp_colour("cream_yellow", STENCIL_TONE),
            font=FONT_POSTER, max_width=W - 2 * (RECESS + 4))


# ============================================================= variants
# Each builder takes the state and returns an (H,W,3) uint8 array. Both
# states of a variant are built from the same seed, so the panel's grain,
# bolts and wear are identical and only the switch moves: when the engine
# swaps SDSWT1 for SDSWT2 the player must see the switch change, not the
# wall change.

# Variant A's lower zone is the one place in the batch where three separate
# elements share a 64 px column, and the first pass overlapped two of them:
# the stencil spanned y 90-104 and the lamp y 99-113, so the lamp sat on the
# word, and the board's bottom edge at y 90 touched the top of the same word.
# The CEO saw it immediately ("se pisan unas cosas a otras", "things step on one another"). The fix is not
# nudging pixels until it looks right: the three boxes are laid out from the
# bottom up with declared gaps, and _check_var_a_layout() below refuses to
# import if they ever touch again.
VAR_A_BOARD = (10, 14, 54, 82)      # bakelite board
VAR_A_JAW_Y = 24
VAR_A_PIVOT = (20, 72)
VAR_A_BLADE_W = 5.0
VAR_A_LAMP = (32, 112, 6)           # cx, cy, r
VAR_A_STENCIL_Y = 92
VAR_A_MIN_GAP = 3                   # px of plate that must show between them


def var_a_boxes() -> dict:
    """The three stacked elements as (top, bottom) in texture pixels."""
    return {
        "board": (VAR_A_BOARD[1], VAR_A_BOARD[3]),
        "stencil": (VAR_A_STENCIL_Y - STENCIL_SIZE / 2, VAR_A_STENCIL_Y + STENCIL_SIZE / 2),
        "lamp": (VAR_A_LAMP[1] - VAR_A_LAMP[2], VAR_A_LAMP[1] + VAR_A_LAMP[2]),
    }


def _check_var_a_layout() -> None:
    order = ["board", "stencil", "lamp"]
    boxes = var_a_boxes()
    for upper, lower in zip(order, order[1:]):
        gap = boxes[lower][0] - boxes[upper][1]
        if gap < VAR_A_MIN_GAP:
            raise ValueError(
                f"variant A layout: {upper} ends at {boxes[upper][1]} and {lower} "
                f"starts at {boxes[lower][0]}, gap {gap} < {VAR_A_MIN_GAP}")
    if boxes["lamp"][1] > H - RECESS - BEVEL - 1:
        raise ValueError("variant A layout: the lamp runs into the plate border")


_check_var_a_layout()


def variant_a(on: bool, rng: np.random.Generator) -> np.ndarray:
    """A - "rubilnik": knife switch on a bakelite board.

    The literal object: a cream phenolic board, two brass jaws, a blade with
    a red grip, pivoted at the bottom. Historically the most correct of the
    four. Its weakness is measured on the sheet: the lit area is small and
    the board is light in both states, so the far view changes least.
    """
    rgb = plate(rng)
    ov = Overlay(W, H)
    x0, y0, x1, y1 = VAR_A_BOARD
    ov.rect(x0, y0, x1, y1, fill=ramp_colour("plaster_warm", 0.80))
    ov.rect(x0, y0, x1, y1, outline=ramp_colour("rust_brown", 0.25), width=1.0)
    # two jaws (brass) the blade closes into
    for jx in (x0 + 8, x1 - 13):
        ov.rect(jx, VAR_A_JAW_Y - 4, jx + 5, VAR_A_JAW_Y + 4,
                fill=ramp_colour("hazard_yellow", 0.55))
    px, py = VAR_A_PIVOT
    ov.ellipse(px - 3, py - 3, px + 3, py + 3, fill=ramp_colour("steel_blue", 0.30))
    # blade: closed (up into the jaws) when on, swung down-right when off
    tip = (x1 - 11, VAR_A_JAW_Y) if on else (x1 - 6, py - 4)  # stays inside the board
    g = ov.group(outline=ramp_colour("concrete_cold", 0.04), outline_width=1.0)
    g.line([(px, py), tip], ramp_colour("steel_blue", 0.62), VAR_A_BLADE_W)
    ov.end_group(g)
    gx, gy = tip
    ov.ellipse(gx - 4, gy - 4, gx + 4, gy + 4, fill=ramp_colour("flag_red", HANDLE_RED))
    stencil(ov, VAR_A_STENCIL_Y)
    lx, ly, lr = VAR_A_LAMP
    lens(ov, lx, ly, lr, on)
    bolts(ov, rng)
    rgb = ov.composite(rgb)
    if on:
        rgb = glow(rgb, lx, ly, radius=12.0, gain=0.35)
    return rgb


VAR_B_CENTER, VAR_B_R = (32, 56), 17
VAR_B_STENCIL_Y = 100


def variant_b(on: bool, rng: np.random.Generator) -> np.ndarray:
    """B - lit push button.

    One big illuminated mushroom button. The largest state change of the
    four and therefore the best far read, at the cost of being the least
    specifically Soviet: it could belong to any industrial set.
    """
    rgb = plate(rng)
    ov = Overlay(W, H)
    cx, cy = VAR_B_CENTER
    r = VAR_B_R
    # bezel the button is recessed into
    ov.ellipse(cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5,
               fill=ramp_colour("steel_blue", 0.34))
    ov.ellipse(cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5,
               outline=ramp_colour("steel_blue", 0.70), width=1.0)
    ov.ellipse(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2,
               fill=ramp_colour("concrete_cold", 0.08))
    if on:
        ov.ellipse(cx - r, cy - r, cx + r, cy + r, fill=ramp_colour("cream_yellow", LENS_ON))
        rc = r * LENS_CORE
        ov.ellipse(cx - rc, cy - rc, cx + rc, cy + rc, fill=(255, 255, 255))
    else:
        ov.ellipse(cx - r, cy - r, cx + r, cy + r, fill=ramp_colour("flag_red", 0.42))
        ov.ellipse(cx - r * 0.75, cy - r * 0.8, cx + r * 0.15, cy - r * 0.1,
                   fill=ramp_colour("flag_red", 0.62))
        ov.ellipse(cx - r, cy - r, cx + r, cy + r,
                   outline=ramp_colour("flag_red", 0.12), width=1.5)
    stencil(ov, VAR_B_STENCIL_Y)
    bolts(ov, rng)
    rgb = ov.composite(rgb)
    if on:
        rgb = glow(rgb, cx, cy, radius=26.0, gain=0.50)
    return rgb


VAR_C_LENS = (32, 26, 12)           # cx, cy, r
VAR_C_STENCIL_Y = 50
VAR_C_SLOT = (24, 62, 40, 118)
VAR_C_BLOCK_H = 18


def variant_c(on: bool, rng: np.random.Generator) -> np.ndarray:
    """C - indicator lens over a sliding lever.

    Two cues at two reading distances: the lens carries the state across the
    room, the lever block carries it close up (and tells the player the thing
    is operable). Balanced; the panel stays calm enough to live next to a
    poster.
    """
    rgb = plate(rng)
    ov = Overlay(W, H)
    sx0, sy0, sx1, sy1 = VAR_C_SLOT
    slot(ov, sx0, sy0, sx1, sy1)
    by = sy0 + 2 if on else sy1 - VAR_C_BLOCK_H - 2
    lever_block(ov, sx0 + 2, by, sx1 - 2, by + VAR_C_BLOCK_H)
    stencil(ov, VAR_C_STENCIL_Y)
    lx, ly, lr = VAR_C_LENS
    lens(ov, lx, ly, lr, on)
    bolts(ov, rng)
    rgb = ov.composite(rgb)
    if on:
        rgb = glow(rgb, lx, ly, radius=22.0, gain=0.52)
    return rgb


VAR_D_LENS = (15, 19, 49, 37)       # x0,y0,x1,y1 of the lit bar
VAR_D_SLOT = (14, 58, 50, 78)
VAR_D_HANDLE_W = 14
VAR_D_STENCIL_Y = 98


def variant_d(on: bool, rng: np.random.Generator) -> np.ndarray:
    """D - hazard-framed master switch (recommended).

    The chevron band is painted on in both states, so the surface says
    "machinery" even when the switch is dead: that is exactly what the
    level-designer is missing from the SDDOOR1 stand-in. The state then
    rides on a wide lit bar (the biggest lit area after variant B) plus a
    handle that slides left to right.
    """
    rgb = chevrons(plate(rng))
    ov = Overlay(W, H)
    sx0, sy0, sx1, sy1 = VAR_D_SLOT
    slot(ov, sx0, sy0, sx1, sy1)
    hx = sx1 - VAR_D_HANDLE_W - 2 if on else sx0 + 2
    lever_block(ov, hx, sy0 + 2, hx + VAR_D_HANDLE_W, sy1 - 2)
    lens_bar(ov, *VAR_D_LENS, on)
    stencil(ov, VAR_D_STENCIL_Y)
    bolts(ov, rng)
    rgb = ov.composite(rgb)
    if on:
        lx = (VAR_D_LENS[0] + VAR_D_LENS[2]) / 2
        ly = (VAR_D_LENS[1] + VAR_D_LENS[3]) / 2
        rgb = glow(rgb, lx, ly, radius=24.0, gain=0.50)
    return rgb


VARIANTS = {
    "A": (variant_a, "Rubilnik: knife switch on a bakelite board",
          "Рубильник: ножевой выключатель на бакелитовой плате"),
    "B": (variant_b, "Lit push button in a steel bezel",
          "Светящаяся кнопка в стальной обойме"),
    "C": (variant_c, "Indicator lens over a sliding lever",
          "Сигнальная линза над скользящим рычагом"),
    "D": (variant_d, "Hazard-framed master switch with a lit bar",
          "Главный выключатель в сигнальной рамке со светящейся полосой"),
}


# ====================================================== context + metrics
def host_rgb(name: str) -> np.ndarray:
    with Image.open(HOSTS[name]) as im:
        return np.asarray(im.convert("RGB"), dtype=np.uint8)


def context(switch: np.ndarray, host: str) -> np.ndarray:
    """host | switch | host, so the switch is judged framed by its wall and
    not on a neutral background (which always flatters a texture)."""
    wall = host_rgb(host)
    hh, hw = wall.shape[:2]
    reps = int(np.ceil(H / hh))
    column = np.tile(wall, (reps, 1, 1))[:H]
    tiles = [column] * CONTEXT_TILES
    tiles[CONTEXT_TILES // 2] = switch
    return np.concatenate(tiles, axis=1)


def far(rgb: np.ndarray) -> np.ndarray:
    """Point-sampled decimation: what the software renderer actually shows
    when the wall is 16 px tall on screen."""
    h, w = rgb.shape[:2]
    return np.asarray(Image.fromarray(rgb, "RGB").resize(
        (w // FAR_DIVISOR, h // FAR_DIVISOR), Image.Resampling.NEAREST), dtype=np.uint8)


def measure(off: np.ndarray, on: np.ndarray) -> dict:
    """Numbers the sheet quotes instead of adjectives.

    - `vs_SDCONC1` / `vs_SDSTEL1`: |mean luma of the switch - mean luma of
      the host|. Bigger = the switch separates from the wall by value, which
      is what survives sector light (ART-BIBLE §5).
    - `state_far_max` / `state_far_mean`: per-pixel luma change between the
      two states AFTER the 8x point-sample, i.e. at 16 px tall. This is the
      "visible from far away" requirement, measured.
    - `lit_far_px`: how many of the 8x16 far-view pixels get more than 40
      luma brighter. One or two pixels is a glint; six or more is a lamp.
    """
    lo, hi = luma(off), luma(on)
    f_lo, f_hi = luma(far(off)), luma(far(on))
    d = f_hi - f_lo
    out = {
        "mean_luma_off": round(float(lo.mean()), 1),
        "mean_luma_on": round(float(hi.mean()), 1),
        "state_delta_mean": round(float((hi - lo).mean()), 1),
        "state_far_mean": round(float(d.mean()), 1),
        "state_far_max": round(float(d.max()), 1),
        "lit_far_px": int((d > 40).sum()),
        "far_px_total": int(d.size),
    }
    for name in HOSTS:
        host = float(luma(host_rgb(name)).mean())
        out[f"vs_{name}"] = round(abs(float(lo.mean()) - host), 1)
        out[f"host_luma_{name}"] = round(host, 1)
    return out


# ================================================================ sheet
INTRO_EN = (
    "<b>Four variants of the switch texture, both states each.</b> One sweep, one verdict: "
    "pick a letter (and say if you want a detail changed) and that variant becomes "
    "<code>SDSWT1</code> (off) and <code>SDSWT2</code> (on) so <code>mod-engineer</code> can declare "
    "them in <code>SWITCHES</code>/<code>ANIMDEFS</code> and <code>level-designer</code> can stop using the "
    "bunker door as a stand-in on MAP01's three switches. Every variant is 64&times;128, "
    "one wall segment on the 64 grid. Read each card left to right: the two states at 4&times;, "
    "then the switch set into the two walls it will really sit on, then the same thing "
    "point-sampled down to <b>16 px tall</b> &mdash; that last strip is the "
    "“does it read from across the room” test, and it is where the variants differ most.")

INTRO_RU = (
    "<b>Четыре варианта текстуры выключателя, каждый в двух состояниях.</b> Один лист, один вердикт: "
    "выберите букву (и скажите, если нужно поправить деталь) &mdash; этот вариант станет "
    "<code>SDSWT1</code> (выключен) и <code>SDSWT2</code> (включён), чтобы <code>mod-engineer</code> объявил их "
    "в <code>SWITCHES</code>/<code>ANIMDEFS</code>, а <code>level-designer</code> перестал подставлять дверь "
    "бункера на трёх выключателях MAP01. Все варианты 64&times;128 &mdash; один сегмент стены по сетке 64. "
    "Карточку читайте слева направо: два состояния при 4&times;, затем выключатель, вставленный в две "
    "стены, на которых он реально будет, затем то же самое, уменьшенное точечной выборкой до "
    "<b>16 px по высоте</b> &mdash; последняя полоса и есть проверка «читается ли через комнату», "
    "и именно там варианты расходятся сильнее всего.")

LEAD_EN = (
    "Measured, not argued. <b>Value</b> is what survives Doom's sector lighting, so the number that "
    "matters is how far the switch sits from its wall in luma, and how much the two states differ "
    "<i>after</i> being shrunk to 16 px. Note the trap in the palette: the brightest flag red is luma "
    "104 and the green steel wall is luma 101 &mdash; a red lever on <code>SDSTEL1</code> disappears as "
    "soon as the sector light drops, which is why the state cue is a cream lamp and the accent is "
    "hazard yellow (ART-BIBLE &sect;5, &sect;6.3).")

LEAD_RU = (
    "Измерено, а не заявлено. При освещении по секторам в Doom выживает <b>яркость</b>, поэтому важны "
    "два числа: насколько выключатель отстоит от своей стены по яркости и насколько различаются "
    "состояния <i>после</i> уменьшения до 16 px. Ловушка палитры: самый яркий красный флага имеет "
    "яркость 104, а зелёная стальная стена &mdash; 101: красный рычаг на <code>SDSTEL1</code> исчезает, "
    "едва падает освещение сектора. Поэтому состояние показывает кремовая лампа, а акцент &mdash; "
    "сигнальный жёлтый (ART-BIBLE &sect;5, &sect;6.3).")

RECO_EN = (
    "<b>Recommendation: D.</b> It is the only variant whose identity does not depend on the lamp: the "
    "hazard chevrons are painted on in both states, so even a dead switch reads as machinery rather "
    "than as wall &mdash; which is the actual complaint about the <code>SDDOOR1</code> stand-in. Its lit "
    "bar is wide, so it holds up at 16 px (see the table), and the sliding handle gives a close-up "
    "cue as well. <b>B</b> is the strongest far read if you want the loudest possible switch; "
    "<b>C</b> is the calmest and the easiest to put next to a poster; <b>A</b> is the most "
    "historically literal object and the weakest at distance, and it is the only one where I had to "
    "spend red on a handle &mdash; which on the green steel wall is worth almost nothing in value.")

RECO_RU = (
    "<b>Рекомендация: D.</b> Это единственный вариант, опознаваемость которого не зависит от лампы: "
    "сигнальные шевроны нарисованы в обоих состояниях, поэтому даже погасший выключатель читается "
    "как механизм, а не как стена, &mdash; а это и есть претензия к подставной <code>SDDOOR1</code>. "
    "Светящаяся полоса широкая и держится на 16 px (см. таблицу), а скользящая ручка даёт признак "
    "вблизи. <b>B</b> &mdash; самое сильное чтение издалека, если нужен самый громкий выключатель; "
    "<b>C</b> &mdash; самый спокойный, его легче поставить рядом с плакатом; <b>A</b> &mdash; самый "
    "исторически буквальный предмет и самый слабый на расстоянии, и единственный, где пришлось "
    "потратить красный на ручку, что на зелёной стальной стене почти ничего не даёт по яркости.")

ASK_EN = ("What I need from you:<ol>"
          "<li><b>Pick a variant</b> (A, B, C or D) &mdash; that is the blocker for MAP01.</li>"
          "<li>Say whether the painted label should stay <b>ПУСК</b> (“start”) or become something "
          "else (ВКЛ / ПУСК НАСОСА / a number).</li>"
          "<li>One bug fix needs a one-line nod: <code>SDFLR1</code>'s hairline cracks used to stop dead "
          "at the tile border and now carry across it. 44 pixels of an approved texture changed; the "
          "before/after is at the bottom of this sheet.</li></ol>")

ASK_RU = ("Что нужно от вас:<ol>"
          "<li><b>Выберите вариант</b> (A, B, C или D) &mdash; это блокирует MAP01.</li>"
          "<li>Скажите, остаётся ли надпись <b>ПУСК</b> или меняется на другую (ВКЛ / ПУСК НАСОСА / номер).</li>"
          "<li>Одно исправление ошибки требует короткого «да»: волосяные трещины <code>SDFLR1</code> "
          "раньше обрывались на границе плитки, а теперь переходят через неё. Изменились 44 пикселя "
          "уже одобренной текстуры; сравнение «до/после» внизу листа.</li></ol>")

LABELS = {
    "en": dict(off="off (SDSWT1)", on="on (SDSWT2)", at1="1x", at4="4x",
               far=f"16 px tall ({FAR_DIVISOR}x point-sampled)",
               on_conc="on SDCONC1 concrete", on_stel="on SDSTEL1 green steel",
               recommended="recommended",
               h_variant="Variant", h_sep_conc="Luma gap vs SDCONC1 (147)",
               h_sep_stel="Luma gap vs SDSTEL1 (101)", h_far="State change at 16 px (mean / max)",
               h_lit="Lit far-view pixels (of 128)",
               sec_cards="The four variants", sec_table="Measurements",
               sec_reco="Reading and recommendation", sec_bug="Bug fix needing a nod: BUG-ART-001",
               sec_pal="Palette used (ratified v1, untouched)", sec_ask="Verdict",
               bug_before="SDFLR1 before (in assets/)", bug_after="SDFLR1 after the fix",
               bug_tile="2x2 tile, after",
               footer="Origin (a): procedural, {script}, seed {seed}+offset. Palette docs/art/palette.json v1. "
                      "Licence: own work, CC BY-NC-SA 4.0 (D15). Nothing here is in assets/ yet."),
    "ru": dict(off="выключен (SDSWT1)", on="включён (SDSWT2)", at1="1x", at4="4x",
               far=f"высота 16 px (точечная выборка {FAR_DIVISOR}x)",
               on_conc="на бетоне SDCONC1", on_stel="на зелёной стали SDSTEL1",
               recommended="рекомендуется",
               h_variant="Вариант", h_sep_conc="Разрыв яркости с SDCONC1 (147)",
               h_sep_stel="Разрыв яркости с SDSTEL1 (101)", h_far="Смена состояния на 16 px (сред. / макс.)",
               h_lit="Светлых пикселей дальнего вида (из 128)",
               sec_cards="Четыре варианта", sec_table="Измерения",
               sec_reco="Чтение и рекомендация", sec_bug="Исправление, требующее согласия: BUG-ART-001",
               sec_pal="Использованная палитра (утверждённая v1, не изменялась)", sec_ask="Вердикт",
               bug_before="SDFLR1 до (в assets/)", bug_after="SDFLR1 после исправления",
               bug_tile="плитка 2x2, после",
               footer="Происхождение (a): процедурно, {script}, зерно {seed}+смещение. Палитра docs/art/palette.json v1. "
                      "Лицензия: собственная работа, CC BY-NC-SA 4.0 (D15). Ничего из этого пока нет в assets/."),
}


def card(vid: str, lang: str, files: dict, metrics: dict) -> str:
    L = LABELS[lang]
    builder, desc_en, desc_ru = VARIANTS[vid]
    desc = desc_en if lang == "en" else desc_ru
    doc = (builder.__doc__ or "").strip().split("\n\n")
    detail = " ".join(l.strip() for l in doc[1:]) if lang == "en" and len(doc) > 1 else ""
    rec = ' class="card rec"' if vid == RECOMMENDED else ' class="card"'
    tag = f'<div class="tag">{L["recommended"]}</div>' if vid == RECOMMENDED else ""
    m = metrics[vid]
    rows = sheetlib.view(f'{L["off"]} — {L["at4"]}', files[f"{vid}_off"], sheetlib.ZOOM, (W, H)) + \
        sheetlib.view(f'{L["on"]} — {L["at4"]}', files[f"{vid}_on"], sheetlib.ZOOM, (W, H)) + \
        sheetlib.view(f'{L["off"]} — {L["at1"]}', files[f"{vid}_off"], 1, (W, H)) + \
        sheetlib.view(f'{L["on"]} — {L["at1"]}', files[f"{vid}_on"], 1, (W, H))
    cw = W * CONTEXT_TILES
    ctx = ""
    for host, lab in (("SDCONC1", L["on_conc"]), ("SDSTEL1", L["on_stel"])):
        ctx += sheetlib.view(f'{lab} — {L["off"]}', files[f"{vid}_{host}_off"], 2, (cw, H))
        ctx += sheetlib.view(f'{lab} — {L["on"]}', files[f"{vid}_{host}_on"], 2, (cw, H))
    fw, fh = cw // FAR_DIVISOR, H // FAR_DIVISOR
    farv = ""
    for host, lab in (("SDCONC1", L["on_conc"]), ("SDSTEL1", L["on_stel"])):
        farv += sheetlib.view(f'{lab} — {L["off"]} — {L["far"]}',
                              files[f"{vid}_{host}_off_far"], sheetlib.FAR_ZOOM, (fw, fh))
        farv += sheetlib.view(f'{lab} — {L["on"]} — {L["far"]}',
                              files[f"{vid}_{host}_on_far"], sheetlib.FAR_ZOOM, (fw, fh))
    return (f'<div{rec}>{tag}<h3>{vid} — SDSWT1 / SDSWT2</h3>'
            f'<p class="desc">{desc}{(" " + detail) if detail else ""}</p>'
            f'<div class="row">{rows}</div><div class="row">{ctx}</div>'
            f'<div class="row">{farv}</div>'
            f'<dl><dt>{L["h_sep_conc"]}</dt><dd>{m["vs_SDCONC1"]}</dd>'
            f'<dt>{L["h_sep_stel"]}</dt><dd>{m["vs_SDSTEL1"]}</dd>'
            f'<dt>{L["h_far"]}</dt><dd>{m["state_far_mean"]} / {m["state_far_max"]}</dd>'
            f'<dt>{L["h_lit"]}</dt><dd>{m["lit_far_px"]} / {m["far_px_total"]}</dd></dl></div>')


def build_sheet(lang: str, files: dict, metrics: dict, stamp: str) -> Path:
    L = LABELS[lang]
    cards = "".join(card(v, lang, files, metrics) for v in VARIANT_IDS)
    rows = [[v, metrics[v]["vs_SDCONC1"], metrics[v]["vs_SDSTEL1"],
             f'{metrics[v]["state_far_mean"]} / {metrics[v]["state_far_max"]}',
             metrics[v]["lit_far_px"]] for v in VARIANT_IDS]
    tbl = sheetlib.table([L["h_variant"], L["h_sep_conc"], L["h_sep_stel"], L["h_far"], L["h_lit"]], rows)
    sections = [
        (L["sec_cards"], LEAD_EN if lang == "en" else LEAD_RU, f'<div class="grid">{cards}</div>'),
        (L["sec_table"], "", tbl),
        (L["sec_reco"], "", f'<p class="lead">{RECO_EN if lang == "en" else RECO_RU}</p>'),
    ]
    # The BUG-ART-001 before/after needs the batch-1 render under work/ next
    # to the file in assets/. flr1_before_after() only fills those keys when
    # that render exists, so on a clean clone (work/ is gitignored) the
    # section is left out rather than the sheet dying with a KeyError.
    if all(k in files for k in FLR1_KEYS):
        bug = (sheetlib.view(L["bug_before"], files["flr1_before"], sheetlib.ZOOM, (64, 64))
               + sheetlib.view(L["bug_after"], files["flr1_after"], sheetlib.ZOOM, (64, 64))
               + sheetlib.view(L["bug_tile"], files["flr1_tile"], 2, (128, 128)))
        sections.append((L["sec_bug"], "", f'<div class="row">{bug}</div>'))
    sections += [
        (L["sec_pal"], "", sheetlib.palette_ramps(load_palette())),
        (L["sec_ask"], "", f'<div class="ask">{ASK_EN if lang == "en" else ASK_RU}</div>'),
    ]
    name = f"{stamp}_F2_batch2-switch-sweep.html"
    out = (SHEET_DIR / name) if lang == "en" else (SHEET_DIR / "ru" / name)
    title = ("Soviet Doom — switch sweep (SDSWT1 / SDSWT2), batch 2"
             if lang == "en" else
             "Soviet Doom — лист выключателя (SDSWT1 / SDSWT2), партия 2")
    sub = ("F2 · 4 variants × 2 states · proposal, nothing in assets/ yet"
           if lang == "en" else
           "F2 · 4 варианта × 2 состояния · предложение, в assets/ пока ничего")
    return sheetlib.write_sheet(
        out, lang=lang, title=title, subtitle=sub,
        intro=INTRO_EN if lang == "en" else INTRO_RU, sections=sections,
        footer=L["footer"].format(script=SCRIPT_REL, seed=BATCH_SEED))


# ================================================================= main
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files: dict[str, Path] = {}
    metrics: dict[str, dict] = {}

    for vid in VARIANT_IDS:
        builder = VARIANTS[vid][0]
        states = {}
        for state, on in (("off", False), ("on", True)):
            # Same seed for both states: only the switch may move, never the panel.
            rgb = builder(on, rng_for(vid))
            states[state] = rgb
            files[f"{vid}_{state}"] = save_path(OUT_DIR / f"SDSWT_{vid}_{state}.png", rgb)
            for host in HOSTS:
                ctx = context(rgb, host)
                files[f"{vid}_{host}_{state}"] = save_path(
                    OUT_DIR / f"CTX_{vid}_{host}_{state}.png", ctx)
                files[f"{vid}_{host}_{state}_far"] = save_path(
                    OUT_DIR / f"FAR_{vid}_{host}_{state}.png", far(ctx))
        metrics[vid] = measure(states["off"], states["on"])
        m = metrics[vid]
        print(f"{vid}  vs concrete {m['vs_SDCONC1']:5.1f}  vs steel {m['vs_SDSTEL1']:5.1f}  "
              f"far state mean {m['state_far_mean']:5.1f} max {m['state_far_max']:5.1f}  "
              f"lit far px {m['lit_far_px']:3d}/{m['far_px_total']}")

    files |= flr1_before_after()

    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    en = build_sheet("en", files, metrics, stamp)
    ru = build_sheet("ru", files, metrics, stamp)
    MANIFEST.write_text(json.dumps({
        "batch": 2, "phase": "F2", "item": "switch", "script": SCRIPT_REL,
        "batch_seed": BATCH_SEED, "seed_offset": SEED_OFFSET, "size": [W, H],
        "hosts": list(HOSTS), "far_divisor": FAR_DIVISOR,
        "recommended": RECOMMENDED,
        "variants": {v: {"description_en": VARIANTS[v][1], "description_ru": VARIANTS[v][2],
                         "metrics": metrics[v]} for v in VARIANT_IDS},
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"sheet EN: {en}\nsheet RU: {ru}\nmanifest: {MANIFEST}")


def save_path(path: Path, rgb: np.ndarray) -> Path:
    save_indexed(rgb, path)
    return path


FLR1_KEYS = ("flr1_before", "flr1_after", "flr1_tile")


def flr1_before_after() -> dict[str, Path]:
    """The one approved texture whose bytes the BUG-ART-001 fix changed.

    Written when assets/ still held the pre-fix file and work/ the fixed one,
    so the two could be shown side by side and the CEO could confirm a
    44-pixel bugfix in the same look as the sweep. The repair entered assets/
    on 2026-10-13 (commit 5c9bb1d), so today both files are the same; the
    section is only built when the batch-1 render exists under work/ (all of
    FLR1_KEYS present), and build_sheet() skips it otherwise.
    """
    before = PROJECT_ROOT / "assets" / "flats" / "soviet_base" / "SDFLR1.png"
    after = PROJECT_ROOT / "work" / "art" / "batch1" / "soviet_base" / "SDFLR1.png"
    out = {}
    if before.is_file():
        out["flr1_before"] = before
    if after.is_file():
        out["flr1_after"] = after
        with Image.open(after) as im:
            a = np.asarray(im.convert("RGB"), dtype=np.uint8)
        tile = np.tile(a, (2, 2, 1))
        out["flr1_tile"] = save_path(OUT_DIR / "FLR1_tile2x2.png", tile)
    return out


if __name__ == "__main__":
    main()
