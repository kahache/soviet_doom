"""Batch 2, priority 2 — first pieces of the "metro" set (MAP02).

Run with the project venv:  .venv/bin/python tools/art/gen_metro.py

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
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import (  # noqa: E402
    Overlay, blend, fbm, grain, load_palette, ramp_colour, save_indexed, shade,
    star_points, tiling_seam_score, to_rgb,
)
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
    rng = rng_for("SDMARB1")
    w, h = WALL_W, WALL_H
    field = MARB_BASE + (fbm(w, h, 3, 5, rng, 0.6) - 0.5) * MARB_MOTTLE
    field += grain(w, h, rng, 0.02)
    rgb = to_rgb(np.clip(field, 0, 1), "flag_red")
    # darker clouding, so the stone has depth before the veins go on
    cloud = np.clip(fbm(w, h, 2, 4, rng) - 0.5, 0, 1) * 1.6
    rgb = blend(rgb, ramp_colour("rust_brown", 0.12), np.clip(cloud, 0, 0.45))

    ov = Overlay(w, h)
    pale = ramp_colour("plaster_warm", 0.78)
    dark = ramp_colour("rust_brown", 0.10)
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


def tex_mosa1() -> np.ndarray:
    """Mosaic panel 128x128: a star with rays, gold on slate blue.

    Built the way a mosaic is: the motif is resolved on the TESSERA grid
    (32x32 cells), not on the pixel grid, so every edge steps in whole
    tesserae and the panel reads as set stones rather than as a drawing with
    a grid on top. No tile is a pure palette colour - each gets its own tone
    jitter, which is what makes a real mosaic shimmer.
    """
    rng = rng_for("SDMOSA1")
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
    for value, (ramp_name, base) in enumerate((("steel_blue", MOSA_GROUND),
                                               ("hazard_yellow", MOSA_GOLD),
                                               ("cream_yellow", MOSA_CREAM))):
        m = motif == value
        if m.any():
            out[m] = to_rgb(np.clip(base + tone, 0, 1), ramp_name)[m]

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
     "Mosaic panel 128x128: gold star and rays on a slate-blue ground, cream border, resolved on the tessera grid.",
     "Мозаичное панно 128x128: золотая звезда с лучами на сланцево-синем фоне, кремовый бордюр, набрано по сетке смальты."),
    ("SDBRAS1", tex_bras1, "wall",
     "Fluted brass pilaster with a ventilation grille and caps on the wrap edges.",
     "Каннелированный латунный пилястр с вентиляционной решёткой и капителями на краях повтора."),
    ("SDMFLR1", tex_mflr1, "flat",
     "Polished grey granite floor, 32 px slabs, feldspar speckle.",
     "Полированный пол из серого гранита, плиты 32 px, вкрапления полевого шпата."),
]

# Pieces the palette v1 visibly limits; quoted on the sheet so the CEO can
# decide whether a palette v2 is worth a new version number.
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
    if lump in PALETTE_LIMITED:
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


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    assert set(SEED_OFFSET) == {t[0] for t in TEXTURES}, "SEED_OFFSET and TEXTURES disagree"
    assert len(set(SEED_OFFSET.values())) == len(SEED_OFFSET), "two pieces share a seed"
    entries, files = [], {}
    for lump, builder, kind, desc_en, desc_ru in TEXTURES:
        assert len(lump) <= 8 and lump.isupper() and lump.startswith("SD"), lump
        rgb = builder()
        h, w = rgb.shape[:2]
        path = OUT_DIR / f"{lump}.png"
        img = save_indexed(rgb, path)
        files[lump] = path
        tile_path = OUT_DIR / f"{lump}_tile2x2.png"
        save_indexed(np.tile(rgb, (2, 2, 1)), tile_path)
        files[lump + "_tile"] = tile_path
        entries.append({
            "lump": lump, "kind": kind, "set": SET_NAME, "width": w, "height": h,
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
