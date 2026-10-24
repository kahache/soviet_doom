"""Episode 3, MAP08 — the naval set: the Northern Fleet submarine base at Severomorsk (D112, P4).

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_naval.py
The whole episode and the CEO's sheet: tools/art/gen_episode3.py.

DRAFTS for the CEO: PNGs to work/art/episode3/naval/, never to assets/.
Palette v1 throughout (ep3lib). The black of the hull is the bottom of
concrete_cold, never flat black (ART-BIBLE §5). Lettering only from our own
alphabet (bigfont, D24): the hull's tactical number «471» and the
container's «ММФ» (the Ministry of the Merchant Fleet); every other plate is
pixel "words" that say nothing.

Two pieces replay a twin's seed on purpose: SDHULL2 is SDHULL1 with the
number painted on, SDRUBR2 is SDRUBR1 with the hatch set in.
The water of the basin is the approved SDWATR1-4 (D107): not redrawn.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import Overlay, blend, fbm, grain, shade, to_rgb  # noqa: E402
import ep3lib  # noqa: E402
from ep3lib import Piece, col, rivet  # noqa: E402

SET_NAME = "naval"
SCRIPT_REL = "tools/art/gen_naval.py"
BATCH_SEED = 5800
FLAT = 64


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


# ================================================================ hull
RUBBER_TONE = 0.11           # concrete_cold: the black anechoic rubber of the hull
HULL_TILE = (16, 15)         # anechoic tiles, on a square grid like the real boats'
CASING_Y = 8                 # the top edge of the casing
FLOOD_Y0, FLOOD_Y1 = 94, 110 # the row of free-flooding slots
FLOOD_PITCH, FLOOD_W = 16, 5
NUMBER = "471"
NUMBER_BOX = (10, 32, 118, 72)   # x0, y0, x1, y1 of the paint on SDHULL2


def hull(rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """The hull side, 128x128: returns (rgb, tile-face mask)."""
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    tw, th = HULL_TILE
    row = (yy - CASING_Y) // th
    lx = xx % tw
    ly = (yy - CASING_Y) % th
    tid = (row * (w // tw) + xx // tw) % 97
    jitter = rng.uniform(-0.018, 0.018, 97)[tid]
    field = RUBBER_TONE + jitter + (fbm(w, h, 8, 3, rng) - 0.5) * 0.05 + grain(w, h, rng, 0.012)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    missing = rng.random(97)[tid] < 0.035
    primer = to_rgb(np.clip(0.15 + (fbm(w, h, 16, 2, rng) - 0.5) * 0.08, 0, 1), "rust_brown")
    rgb = np.where(missing[..., None], primer, rgb)
    f = np.ones((h, w))
    f[(lx == 0) | (ly == 0)] = 0.62
    f[((lx == 1) | (ly == 1)) & ~missing] *= 1.10
    f *= 1.25 - 0.40 * yy / h                          # the hull curves away below
    rgb = shade(rgb, f)
    face = (lx > 0) & (ly > 0) & ~missing & (yy >= CASING_Y)
    # the casing's top edge, catching the sky
    rgb[:CASING_Y] = col("concrete_cold", 0.20)
    rgb[0] = col("concrete_cold", 0.42)
    rgb[1] = col("concrete_cold", 0.32)
    rgb[CASING_Y - 1] = col("concrete_cold", 0.05)
    # free-flooding slots: rounded, dark inside, a lit lower lip
    ov = Overlay(w, h)
    for x in range(6, w, FLOOD_PITCH):
        ov.rect(x - 1, FLOOD_Y0 - 1, x + FLOOD_W + 1, FLOOD_Y1 + 1, fill=col("concrete_cold", 0.28))
        ov.ellipse(x, FLOOD_Y0, x + FLOOD_W, FLOOD_Y0 + FLOOD_W, fill=col("concrete_cold", 0.02))
        ov.rect(x, FLOOD_Y0 + FLOOD_W / 2, x + FLOOD_W, FLOOD_Y1 - FLOOD_W / 2, fill=col("concrete_cold", 0.02))
        ov.ellipse(x, FLOOD_Y1 - FLOOD_W, x + FLOOD_W, FLOOD_Y1, fill=col("concrete_cold", 0.02))
    rgb = ov.composite(rgb)
    # salt crust weeping down from the slots and the casing
    salt = np.clip(fbm(w, h, 16, 2, rng, aspect=8.0) - 0.62, 0, 1) * 2.5
    below = np.clip(1 - np.abs(yy - FLOOD_Y1 - 8) / 12, 0, 1) + np.clip(1 - (yy - CASING_Y) / 14, 0, 1) * 0.6
    rgb = blend(rgb, col("concrete_cold", 0.55), np.clip(salt * below, 0, 0.6))
    return rgb, face


def tex_hull1() -> np.ndarray:
    """Submarine hull side: black anechoic rubber tiles (a few missing,
    red-brown primer showing), the casing's edge against the sky, the row of
    free-flooding slots of a Soviet boat, salt weeping down."""
    return hull(rng_for(1))[0]


def tex_hull2() -> np.ndarray:
    """SDHULL1 (same seed) with the white tactical number «471» painted
    across the tiles, worn where tiles have shifted."""
    rng = rng_for(1)
    rgb, face = hull(rng)
    body, _ = ep3lib.glyph_masks(NUMBER)
    big = np.repeat(np.repeat(body, 3, 0), 3, 1)
    canvas = np.zeros(rgb.shape[:2], bool)
    x0, y0, x1, y1 = NUMBER_BOX
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    mh, mw = big.shape
    bx, by = int(round(cx - mw / 2)), int(round(cy - mh / 2))
    canvas[by:by + mh, bx:bx + mw] = big
    worn = (rng.random(canvas.shape) < 0.07) | (fbm(128, 128, 8, 2, rng) > 0.74)
    paint = canvas & face & ~worn
    lum = rgb.astype(float).mean(-1)
    white = to_rgb(np.clip(0.80 + (lum - 40) / 255, 0, 1), "plaster_warm")
    out = np.where(paint[..., None], white, rgb)
    assert canvas[:y0].sum() == 0 and canvas[y1:].sum() == 0 and canvas[:, :x0].sum() == 0
    return out


# ================================================================ rubber deck
DECK_TILE = (16, 16)
DECK_TONE = 0.14
HATCH_C, HATCH_R = (32, 32), 17
HATCH_BOX = (10, 9, 55, 55)


def deck(rng: np.random.Generator) -> np.ndarray:
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    tw, th = DECK_TILE
    row = yy // th
    lx = xx % tw
    ly = yy % th
    tid = (row * 4 + (xx // tw) % 4) % 32
    jitter = rng.uniform(-0.02, 0.02, 32)[tid]
    wear = fbm(w, h, 2, 3, rng, aspect=4.0)
    field = DECK_TONE + jitter + (wear - 0.5) * 0.10 + grain(w, h, rng, 0.03)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    missing = rng.random(32)[tid] < 0.07
    steel = to_rgb(np.clip(0.22 + (fbm(w, h, 8, 2, rng) - 0.5) * 0.2, 0, 1), "rust_brown")
    rgb = np.where(missing[..., None], steel, rgb)
    f = np.ones((h, w))
    f[(lx == 0) | (ly == 0)] = 0.60
    f[((lx == 1) | (ly == 1)) & ~missing] *= 1.10
    rgb = shade(rgb, f)
    salt = fbm(w, h, 8, 3, rng) > 0.70
    rgb = np.where(salt[..., None], blend(rgb, col("concrete_cold", 0.55), np.full((h, w), 0.4)), rgb)
    return rgb


def tex_rubr1() -> np.ndarray:
    """Submarine deck from above: black anti-acoustic rubber tiles,
    staggered, a path worn lighter along y, a few tiles gone (rusty steel),
    salt bloom."""
    return deck(rng_for(2))


def tex_rubr2() -> np.ndarray:
    """SDRUBR1 (same seed) with a round escape hatch set flush in the deck:
    steel coaming, a rubber-clad lid, its hinge and a small handwheel. A
    single piece, it does not tile."""
    rng = rng_for(2)
    rgb = deck(rng)
    cx, cy = HATCH_C
    r = HATCH_R
    ov = Overlay(FLAT, FLAT)
    ov.ellipse(cx - r - 2, cy - r - 2, cx + r + 2, cy + r + 2, fill=col("steel_blue", 0.18))
    ov.ellipse(cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1, fill=col("steel_blue", 0.42))
    ov.arc_ring(cx, cy, r + 1, r - 0.5, 180, 300, col("steel_blue", 0.62))
    ov.ellipse(cx - r + 1, cy - r + 1, cx + r - 1, cy + r - 1, fill=col("concrete_cold", 0.04))
    ov.ellipse(cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2, fill=col("concrete_cold", 0.17))
    for a in range(0, 360, 45):
        t = np.deg2rad(a)
        ov.line([(cx + 6 * np.cos(t), cy + 6 * np.sin(t)), (cx + (r - 3) * np.cos(t), cy + (r - 3) * np.sin(t))],
                col("concrete_cold", 0.10), 1.0)
    ov.rect(cx - 6, cy - r - 4, cx + 6, cy - r + 2, fill=col("steel_blue", 0.30))
    ov.rect(cx - 6, cy - r - 4, cx + 6, cy - r - 3, fill=col("steel_blue", 0.58))
    ov.ellipse(cx - 6, cy - 6, cx + 6, cy + 6, outline=col("steel_blue", 0.50), width=1.4)
    ov.line([(cx - 5, cy), (cx + 5, cy)], col("steel_blue", 0.45), 1.0)
    ov.line([(cx, cy - 5), (cx, cy + 5)], col("steel_blue", 0.45), 1.0)
    ov.ellipse(cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5, fill=col("steel_blue", 0.60))
    out = ov.composite(rgb)
    for a in range(0, 360, 30):
        t = np.deg2rad(a)
        x, y = int(round(cx + (r + 0.5) * np.cos(t))), int(round(cy + (r + 0.5) * np.sin(t)))
        out[y, x] = col("steel_blue", 0.66)
    return out


# ================================================================ living rock
ROCK_TONE = 0.36             # concrete_cold: dark Kola gneiss
ROCK_CELL = 16
DRILL_XS = (20, 52)          # half-barrels of the perimeter drill holes


def rock(rng: np.random.Generator, w: int, h: int) -> np.ndarray:
    f1, f2, ident, ox, oy = ep3lib.cells_voronoi(w, h, ROCK_CELL, rng, 0.9)
    tone = rng.uniform(-0.05, 0.05, ident.max() + 1)[ident]
    field = ROCK_TONE + tone + (fbm(w, h, 4, 4, rng) - 0.5) * 0.14 + grain(w, h, rng, 0.03)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    feld = (rng.random((h, w)) < 0.05) & (fbm(w, h, 8, 2, rng) > 0.45)
    rgb[feld] = col("rust_brown", 0.42)
    vein = ep3lib.ridged(fbm(w, h, 3, 3, rng)) > 0.975
    rgb[vein] = col("concrete_cold", 0.62)
    f = 1 - (ox * 0.6 + oy * 0.8) / ROCK_CELL * 0.26
    crack = ((f2 - f1) < 1.1) & (fbm(w, h, 4, 2, rng) > 0.45)
    f = np.where(crack, 0.55, f)
    f *= 0.80 + 0.40 * fbm(w, h, 2, 2, rng)
    wet = np.clip(fbm(w, h, 8, 3, rng, aspect=10.0) - 0.56, 0, 1) * 1.4
    f *= 1 - wet
    return shade(rgb, f)


def bolt_plate(rgb: np.ndarray, x: int, y: int) -> None:
    rgb[y:y + 6, x:x + 6] = col("steel_blue", 0.30)
    rgb[y, x:x + 6] = col("steel_blue", 0.52)
    rgb[y:y + 6, x] = col("steel_blue", 0.46)
    rgb[y + 5, x:x + 6] = col("steel_blue", 0.12)
    rivet(rgb, x + 2, y + 2, "steel_blue", 0.40)
    for k in range(1, 9):
        if y + 6 + k < rgb.shape[0]:
            rgb[y + 6 + k, x + 3] = col("rust_brown", max(0.12, 0.40 - k * 0.03))


def tex_rock1() -> np.ndarray:
    """Living rock of the excavated pens: dark gneiss in blast facets lit
    from the top left, pink feldspar specks, white quartz veins, seepage
    darkening it in runs, the half-barrels of the perimeter drill holes,
    a rock bolt."""
    rng = rng_for(3)
    w, h = 64, 128
    rgb = rock(rng, w, h)
    yy = np.arange(h)
    broken = fbm(1, h, 1, 3, rng, aspect=1 / 16)[:, 0] > 0.35
    for x in DRILL_XS:
        rgb[broken, x] = col("concrete_cold", 0.08)
        rgb[broken, x + 1] = col("concrete_cold", 0.16)
        rgb[broken, x + 2] = col("concrete_cold", 0.48)
    bolt_plate(rgb, 36, 70)
    return rgb


def tex_rock2() -> np.ndarray:
    """The same rock overhead, a flat: wider facets, drips, two rock-bolt
    plates on the 32 px grid, a calcite bloom."""
    rng = rng_for(4)
    rgb = rock(rng, FLAT, FLAT)
    drip = (fbm(FLAT, FLAT, 8, 2, rng) > 0.72)
    rgb = np.where(drip[..., None], shade(rgb, 0.65), rgb)
    calc = fbm(FLAT, FLAT, 6, 3, rng) > 0.74
    rgb = blend(rgb, col("plaster_warm", 0.78), calc * 0.6)
    bolt_plate(rgb, 13, 13)
    bolt_plate(rgb, 45, 45)
    return rgb


# ================================================================ watertight door
BULK_TONE = 0.56             # concrete_cold: the "ball grey" of Soviet naval paint
DOOR_C, DOOR_R, COAMING_R = (64, 66), 42, 49
DOGS = 6


def tex_bulk1() -> np.ndarray:
    """Round watertight door in a bulkhead: grey plate with seams and
    rivets, the bare-steel coaming, the door with its stiffening ring, six
    dogs with levers, two hinges, a red handwheel, the compartment's red
    numeral (bigfont), oil and scuffs low down. A picture, not a surface."""
    rng = rng_for(5)
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    field = BULK_TONE + (fbm(w, h, 4, 4, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.015)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    f = np.ones((h, w))
    f[:, 0] = 0.55
    f[:, 1] *= 1.15
    f[0] = 0.55
    f[1] *= 1.15
    f *= 1 - np.clip((yy - 104) / 24, 0, 1) * 0.25 * (fbm(w, h, 8, 2, rng) > 0.45)
    rgb = shade(rgb, f)
    for y in (4, 123):
        for x in range(4, w, 8):
            rivet(rgb, x, y, "concrete_cold", 0.62)
    cx, cy = DOOR_C
    ov = Overlay(w, h)
    ov.ellipse(cx - COAMING_R - 2, cy - COAMING_R, cx + COAMING_R + 2, cy + COAMING_R + 3,
               fill=col("concrete_cold", 0.20) + (200,))
    ov.ellipse(cx - COAMING_R, cy - COAMING_R, cx + COAMING_R, cy + COAMING_R, fill=col("steel_blue", 0.36))
    ov.arc_ring(cx, cy, COAMING_R, COAMING_R - 2, 190, 290, col("steel_blue", 0.58))
    ov.ellipse(cx - DOOR_R - 2, cy - DOOR_R - 2, cx + DOOR_R + 2, cy + DOOR_R + 2, fill=col("concrete_cold", 0.06))
    ov.ellipse(cx - DOOR_R, cy - DOOR_R, cx + DOOR_R, cy + DOOR_R, fill=col("concrete_cold", 0.62))
    ov.arc_ring(cx, cy, DOOR_R, DOOR_R - 1.5, 190, 300, col("concrete_cold", 0.78))
    ov.arc_ring(cx, cy, DOOR_R, DOOR_R - 1.5, 10, 120, col("concrete_cold", 0.40))
    ov.arc_ring(cx, cy, 28, 25, 0, 360, col("concrete_cold", 0.48))
    ov.arc_ring(cx, cy, 25, 24, 190, 300, col("concrete_cold", 0.74))
    for k in range(DOGS):
        a = np.deg2rad(30 + k * 360 / DOGS)
        px, py = cx + (COAMING_R - 3) * np.cos(a), cy + (COAMING_R - 3) * np.sin(a)
        qx, qy = cx + (DOOR_R - 9) * np.cos(a), cy + (DOOR_R - 9) * np.sin(a)
        ov.ellipse(px - 3.5, py - 3.5, px + 3.5, py + 3.5, fill=col("steel_blue", 0.22))
        ov.ellipse(px - 2.5, py - 2.5, px + 2.5, py + 2.5, fill=col("steel_blue", 0.45))
        ov.line([(px, py), (qx, qy)], col("steel_blue", 0.18), 3.2)
        ov.line([(px, py), (qx, qy)], col("steel_blue", 0.48), 1.5)
    for hy in (cy - 30, cy + 22):
        ov.rect(cx + DOOR_R - 4, hy, cx + COAMING_R + 6, hy + 9, fill=col("steel_blue", 0.20))
        ov.rect(cx + DOOR_R - 4, hy, cx + COAMING_R + 6, hy + 2, fill=col("steel_blue", 0.50))
        ov.ellipse(cx + COAMING_R + 1, hy - 1, cx + COAMING_R + 9, hy + 10, fill=col("steel_blue", 0.34))
    wr = 13
    ov.ellipse(cx - wr - 1, cy - wr + 1, cx + wr + 1, cy + wr + 3, fill=col("concrete_cold", 0.10) + (170,))
    ov.arc_ring(cx, cy, wr, wr - 3, 0, 360, col("flag_red", 0.52))
    ov.arc_ring(cx, cy, wr, wr - 1.2, 190, 300, col("flag_red", 0.80))
    for a in range(0, 360, 60):
        t = np.deg2rad(a + 15)
        ov.line([(cx, cy), (cx + (wr - 2) * np.cos(t), cy + (wr - 2) * np.sin(t))], col("flag_red", 0.48), 2.0)
    ov.ellipse(cx - 4, cy - 4, cx + 4, cy + 4, fill=col("steel_blue", 0.40))
    ov.ellipse(cx - 2, cy - 3, cx + 1, cy, fill=col("steel_blue", 0.66))
    rgb = ov.composite(rgb)
    body, shadow = ep3lib.glyph_masks("3")
    ep3lib.paste_mask(rgb, body | shadow, col("flag_red", 0.62), 18, 16)
    rgb[30:33, 8:28] = col("flag_red", 0.55)
    oil = np.clip(fbm(w, h, 16, 2, rng, aspect=8.0) - 0.6, 0, 1) * 2.0
    under = (yy > cy + 20) & (np.hypot(xx - cx, yy - cy) < DOOR_R)
    rgb = np.where(under[..., None], shade(rgb, 1 - oil * 0.5), rgb)
    return rgb


# ================================================================ naval control panel
NAVC_TONE = 0.56             # military_green: the light grey-green of Soviet boats' consoles
GAUGE_Y, GAUGE_R = 19, 12
MIMIC = (8, 40, 120, 74)     # x0, y0, x1, y1 of the compartment mimic
TABLO_Y = (80, 92)           # two rows of backlit indicator tiles
KICK_Y = 112


def tex_navc1() -> np.ndarray:
    """Control-room panel of a submarine: grey-green steel, four black-faced
    depth and pressure gauges, a mimic of the boat's compartments with their
    lamps, two rows of backlit indicator tiles (some lit, their labels pixel
    dashes), a row of toggles, the kick plate. 128 px wide: it tiles as a
    long board."""
    rng = rng_for(6)
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    field = NAVC_TONE + (fbm(w, h, 4, 3, rng) - 0.5) * 0.06 + grain(w, h, rng, 0.015)
    rgb = to_rgb(np.clip(field, 0, 1), "military_green")
    f = np.ones((h, w))
    for sx in (0, 64):
        f[:, sx] = 0.45
        f[:, sx + 1] *= 1.15
    rgb = shade(rgb, f)
    ov = Overlay(w, h)
    for gx in (16, 48, 80, 112):
        ov.ellipse(gx - GAUGE_R - 1.5, GAUGE_Y - GAUGE_R - 1.5, gx + GAUGE_R + 1.5, GAUGE_Y + GAUGE_R + 1.5,
                   fill=col("steel_blue", 0.50))
        ov.ellipse(gx - GAUGE_R, GAUGE_Y - GAUGE_R, gx + GAUGE_R, GAUGE_Y + GAUGE_R, fill=col("concrete_cold", 0.07))
        ov.arc_ring(gx, GAUGE_Y, GAUGE_R - 1, GAUGE_R - 3, 10, 50, col("flag_red", 0.62))
        for k in range(10):
            a = np.deg2rad(135 + k * 30)
            if 135 + k * 30 > 405:
                break
            ov.line([(gx + (GAUGE_R - 1) * np.cos(a), GAUGE_Y + (GAUGE_R - 1) * np.sin(a)),
                     (gx + (GAUGE_R - 3.5) * np.cos(a), GAUGE_Y + (GAUGE_R - 3.5) * np.sin(a))],
                    col("plaster_warm", 0.90), 0.9)
        a = np.deg2rad(rng.uniform(150, 390))
        ov.line([(gx, GAUGE_Y), (gx + (GAUGE_R - 2.5) * np.cos(a), GAUGE_Y + (GAUGE_R - 2.5) * np.sin(a))],
                col("cream_yellow", 0.95), 1.1)
        ov.ellipse(gx - 1.3, GAUGE_Y - 1.3, gx + 1.3, GAUGE_Y + 1.3, fill=col("steel_blue", 0.55))
    # the mimic: dark glass, the boat in outline, its compartments
    x0, y0, x1, y1 = MIMIC
    ov.rect(x0 - 1, y0 - 1, x1 + 1, y1 + 1, fill=col("steel_blue", 0.45))
    ov.rect(x0, y0, x1, y1, fill=col("concrete_cold", 0.10))
    mid = (y0 + y1) / 2 + 3
    ov.ellipse(x0 + 6, mid - 7, x1 - 6, mid + 7, outline=col("plaster_warm", 0.86), width=1.0)
    ov.rect(52, mid - 13, 70, mid - 6.5, outline=col("plaster_warm", 0.86), width=1.0)
    lamp_cols = ("military_green", "flag_red", "hazard_yellow")
    comps = np.linspace(x0 + 14, x1 - 14, 8)
    for i in range(7):
        ov.line([(comps[i] + 6.5, mid - 6), (comps[i] + 6.5, mid + 6)], col("plaster_warm", 0.60), 0.8)
    for i in range(8):
        cxl = comps[i] - (0 if i < 7 else 3)
        name = lamp_cols[0] if rng.random() < 0.7 else lamp_cols[int(rng.integers(1, 3))]
        ov.ellipse(cxl - 1.8, mid - 1.8, cxl + 1.8, mid + 1.8, fill=col(name, 0.92))
    # indicator tiles
    lit_cols = (("cream_yellow", 0.92), ("flag_red", 0.85), ("hazard_yellow", 0.88))
    lit_boxes = []
    for ty in TABLO_Y:
        for tx in range(6, w - 6, 12):
            on = rng.random() < 0.4
            ov.rect(tx - 1, ty - 1, tx + 11, ty + 8, fill=col("concrete_cold", 0.08))
            if on:
                name, t = lit_cols[int(rng.integers(0, 3))]
                ov.rect(tx, ty, tx + 10, ty + 7, fill=col(name, t))
                lit_boxes.append((tx, ty))
            else:
                ov.rect(tx, ty, tx + 10, ty + 7, fill=col("plaster_warm", 0.35))
    for tx in range(7, w - 4, 8):
        ov.ellipse(tx - 2, 104, tx + 2, 108, fill=col("steel_blue", 0.70))
        ov.rect(tx - 0.5, 100, tx + 1, 106, fill=col("concrete_cold", 0.05))
    rgb = ov.composite(rgb)
    for tx, ty in lit_boxes:
        ep3lib.illegible_label(rgb, tx + 1, ty + 2, 8, col("concrete_cold", 0.15), rng, rows=2)
    for gx in (16, 48, 80, 112):
        ep3lib.illegible_label(rgb, gx - 7, 34, 14, col("concrete_cold", 0.15), rng)
    kick = to_rgb(np.clip(0.14 + grain(w, h, rng, 0.02), 0, 1), "concrete_cold")
    rgb = np.where((yy >= KICK_Y)[..., None], kick, rgb)
    rgb[KICK_Y, :] = col("concrete_cold", 0.42)
    return rgb


# ================================================================ shipping container
CONT_RED = 0.40              # flag_red: the faded oxide red of a merchant-fleet box
RIB_PITCH = 16
RIB_SHADE = np.array([1.30, 1.22, 1.12, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.80, 0.68, 0.60, 0.72, 0.78, 0.86])
RAIL_TOP, RAIL_BOT = 8, 118
POST_W = 6
STENCIL = "ММФ"
SERIAL = "4730216"


def tex_cont1() -> np.ndarray:
    """Shipping container, long side: trapezoidal corrugation in faded red,
    top and bottom rails, corner posts with their castings, rust bleeding
    from the rails and dents, «ММФ» stencilled in white (bigfont), the box
    number in 3x5 digits, a data plate. Containers stacked end to end tile
    in x."""
    rng = rng_for(7)
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    field = CONT_RED + (fbm(w, h, 4, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.02)
    faded = fbm(w, h, 3, 3, rng)
    field = field + np.clip(faded - 0.6, 0, 1) * 0.2
    rgb = to_rgb(np.clip(field, 0, 1), "flag_red")
    rust_near = np.clip(1 - (yy - RAIL_TOP) / 18, 0, 1) + np.clip((yy - RAIL_BOT + 22) / 22, 0, 1)
    rust = (fbm(w, h, 8, 3, rng) + rust_near * 0.35 + np.clip(fbm(w, h, 16, 2, rng, aspect=6.0) - 0.6, 0, 1)) > 0.78
    rgb = np.where(rust[..., None], to_rgb(np.clip(field * 0.95, 0, 1), "rust_brown"), rgb)
    f = RIB_SHADE[(xx + 4) % RIB_PITCH]
    dents = fbm(w, h, 4, 2, rng)
    f = f * (1 + (dents - np.roll(dents, 2, axis=1)) * 0.6)
    rgb = shade(rgb, f)
    # stencil and number, painted over the ribs (the paint takes their light)
    canvas = np.zeros((h, w), bool)
    body, _ = ep3lib.glyph_masks(STENCIL)
    big = np.repeat(np.repeat(body, 2, 0), 2, 1)
    mh, mw = big.shape
    bx, by = int(round(64 - mw / 2)), 30
    canvas[by:by + mh, bx:bx + mw] = big
    dm = ep3lib.digits_mask(SERIAL)
    dmh, dmw = dm.shape
    canvas[64:64 + dmh * 2, 20:20 + dmw * 2] = np.repeat(np.repeat(dm, 2, 0), 2, 1)
    worn = (rng.random((h, w)) < 0.08) | (fbm(w, h, 8, 2, rng) > 0.80)
    white = shade(np.broadcast_to(np.array(col("plaster_warm", 0.84), np.uint8), (h, w, 3)).copy(), f)
    rgb = np.where((canvas & ~worn)[..., None], white, rgb)
    # rails and corner posts
    steel = to_rgb(np.clip(CONT_RED * 0.85 + grain(w, h, rng, 0.02), 0, 1), "flag_red")
    rails = (yy < RAIL_TOP) | (yy >= RAIL_BOT) | (xx < POST_W) | (xx >= w - POST_W)
    rgb = np.where(rails[..., None], steel, rgb)
    fr = np.ones((h, w))
    fr[0] = 1.4
    fr[RAIL_TOP - 1] = 0.5
    fr[RAIL_TOP] = 0.55
    fr[RAIL_BOT] = 1.3
    fr[h - 1] = 0.5
    fr[:, 0] = 0.40
    fr[:, 1] *= 1.3
    fr[:, w - POST_W] = 0.55
    fr[:, POST_W] = 0.55
    rgb = shade(rgb, fr)
    for cx0 in (0, w - POST_W):
        for cy0 in (0, h - 9):
            rgb[cy0 + 1:cy0 + 8, cx0 + 1:cx0 + POST_W - 1] = col("rust_brown", 0.30)
            rgb[cy0 + 3:cy0 + 6, cx0 + 2:cx0 + POST_W - 2] = col("concrete_cold", 0.04)
    rgb[96:106, 100:118] = col("concrete_cold", 0.62)
    rgb[96, 100:118] = col("concrete_cold", 0.80)
    rgb[105, 100:118] = col("concrete_cold", 0.30)
    ep3lib.illegible_label(rgb, 102, 98, 14, col("concrete_cold", 0.12), rng, rows=3)
    return rgb


# ================================================================ crane lattice
CHORDS = ((3, 9), (55, 61))
BAY = 64
CRANE_PAINT = 0.62           # hazard_yellow, faded


def tex_cran1() -> np.ndarray:
    """Lattice of a quay crane's jib, MASKED: two angle-iron chords,
    battens every 64 px, zig-zag diagonals with gusset plates and rivets,
    faded yellow paint with rust. Tiles in both axes as an endless boom."""
    rng = rng_for(8)
    w, h = 64, 128
    ov = Overlay(w, h)
    paint = col("hazard_yellow", CRANE_PAINT)
    dark = col("hazard_yellow", 0.34)
    for y0 in range(0, h, BAY):
        ov.rect(0, y0, w, y0 + 4, fill=paint)
        ov.rect(0, y0 + 3, w, y0 + 4, fill=dark)
        a, b = (CHORDS[0][1] - 1, y0 + 4), (CHORDS[1][0] + 1, y0 + BAY // 2)
        c = (CHORDS[0][1] - 1, y0 + BAY)
        for p, q in ((a, b), (b, c)):
            ov.line([(p[0], p[1] + 1), (q[0], q[1] + 1)], dark, 3.2)
            ov.line([p, q], paint, 2.4)
        for gx, gy in (a, b, (c[0], y0)):
            ov.polygon([(gx - 3, gy - 3), (gx + 5, gy), (gx - 3, gy + 6)] if gx < 32 else
                       [(gx + 3, gy - 4), (gx - 5, gy), (gx + 3, gy + 5)], fill=col("hazard_yellow", 0.50))
    for x0, x1 in CHORDS:
        ov.rect(x0, 0, x1, h, fill=paint)
        ov.rect(x0, 0, x0 + 1.5, h, fill=col("hazard_yellow", 0.82))
        ov.rect(x1 - 1.5, 0, x1, h, fill=dark)
    rgba = ep3lib.overlay_to_rgba(ov)
    rgb = rgba[..., :3].copy()
    opaque = rgba[..., 3] > 0
    rust = (fbm(w, h, 8, 3, rng, aspect=3.0) > 0.60) & opaque
    lum = rgb.astype(float).mean(-1)
    rgb = np.where(rust[..., None], to_rgb(np.clip(lum / 255 * 0.9, 0, 1), "rust_brown"), rgb)
    rgb = np.where(opaque[..., None], shade(rgb, 1 + grain(w, h, rng, 0.04)), 0).astype(np.uint8)
    for x0, x1 in CHORDS:
        for y in range(5, h, 8):
            rivet(rgb, x0 + 2, y, "hazard_yellow", 0.45)
    rgb[~opaque] = 0
    return np.dstack([rgb, rgba[..., 3]])


# ================================================================ quay
QUAY_TONE = 0.50
EDGE_Y = 52                  # the coping: hazard stripes, then the steel edge
BOLLARD_C, BOLLARD_R = (32, 24), 8


def tex_pier1() -> np.ndarray:
    """Concrete quay from above: slabs with oil stains, a cast-iron
    mooring bollard on its base plate with a hawser running to the edge, the
    coping in yellow and black, the steel edge angle over the water side
    (bottom of the tile). Tiles in x along the quay."""
    rng = rng_for(9)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    field = QUAY_TONE + (fbm(w, h, 4, 4, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.03)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    f = np.ones((h, w))
    f[:, 0] = 0.55
    f[:, 1] *= 1.10
    f[0] = 0.55
    f[1] *= 1.10
    oil = np.clip(fbm(w, h, 4, 3, rng) - 0.62, 0, 1) * 2.4
    f *= 1 - oil
    rgb = shade(rgb, f)
    stripe = ((xx + yy) // 8) % 2 == 0
    coping = (yy >= EDGE_Y - 8) & (yy < EDGE_Y)
    hz = np.where(stripe[..., None], np.array(col("hazard_yellow", 0.66), np.uint8),
                  np.array(col("concrete_cold", 0.12), np.uint8))
    hz = shade(hz, 1 + grain(w, h, rng, 0.06) - (fbm(w, h, 8, 2, rng) > 0.6) * 0.25)
    rgb = np.where(coping[..., None], hz, rgb)
    edge = yy >= EDGE_Y
    steel = to_rgb(np.clip(0.30 + grain(w, h, rng, 0.03) + (fbm(w, h, 8, 2, rng) > 0.6) * 0.05, 0, 1), "steel_blue")
    rust = fbm(w, h, 8, 2, rng) > 0.55
    steel = np.where(rust[..., None], to_rgb(np.clip(0.32 + grain(w, h, rng, 0.03), 0, 1), "rust_brown"), steel)
    rgb = np.where(edge[..., None], steel, rgb)
    rgb[EDGE_Y] = col("steel_blue", 0.55)
    rgb[h - 1] = col("steel_blue", 0.08)
    cx, cy = BOLLARD_C
    ov = Overlay(w, h)
    ov.line([(cx + 2, cy + 6), (cx + 8, EDGE_Y - 4), (cx + 10, h)], col("rust_brown", 0.18), 3.4)
    ov.line([(cx + 2, cy + 5), (cx + 8, EDGE_Y - 5), (cx + 10, h)], col("plaster_warm", 0.48), 2.0)
    ov.rect(cx - 12, cy - 11, cx + 12, cy + 12, fill=col("concrete_cold", 0.15))
    ov.rect(cx - 11, cy - 11, cx + 11, cy + 11, fill=col("concrete_cold", 0.26))
    for bx, by in ((-9, -9), (8, -9), (-9, 8), (8, 8)):
        ov.ellipse(cx + bx - 1, cy + by - 1, cx + bx + 2, cy + by + 2, fill=col("concrete_cold", 0.48))
    ov.ellipse(cx - BOLLARD_R + 1, cy - BOLLARD_R + 2, cx + BOLLARD_R + 1, cy + BOLLARD_R + 2,
               fill=col("concrete_cold", 0.04))
    ov.ellipse(cx - BOLLARD_R, cy - BOLLARD_R, cx + BOLLARD_R, cy + BOLLARD_R, fill=col("concrete_cold", 0.14))
    ov.ellipse(cx - BOLLARD_R + 2, cy - BOLLARD_R + 2, cx + BOLLARD_R - 2, cy + BOLLARD_R - 2,
               fill=col("concrete_cold", 0.22))
    ov.arc_ring(cx, cy, BOLLARD_R, BOLLARD_R - 1.5, 190, 290, col("concrete_cold", 0.48))
    ov.ellipse(cx - 3, cy - 4, cx, cy - 1, fill=col("concrete_cold", 0.40))
    ov.arc_ring(cx, cy, BOLLARD_R + 1.5, BOLLARD_R - 0.5, 20, 160, col("plaster_warm", 0.50))
    return ov.composite(rgb)


# ================================================================ pieces
PIECES = [
    Piece("SDHULL1", tex_hull1, "wall", (128, 128), ["SDHULL1"], 1, "x",
          "Submarine hull",
          "The side of the hull: staggered black anechoic rubber tiles (a few missing, showing the "
          "reddish primer), the deck edge against the sky, the row of flood ports of "
          "a Soviet submarine and streaks of salt.",
          rec_why="concrete_cold's black, never flat black (ART-BIBLE §5). Tiles in x for long hulls."),
    Piece("SDHULL2", tex_hull2, "wall", (128, 128), ["SDHULL2"], 1, "no",
          "Hull with number",
          "The same hull (same seed) with the tactical number «471» painted in white over the tiles, "
          "worn where the tiles have shifted. Digits from our own alphabet (bigfont, D24).",
          rec_why="Once per submarine, between runs of SDHULL1."),
    Piece("SDRUBR1", tex_rubr1, "flat", (64, 64), ["SDRUBR1"], 2, "xy",
          "Anechoic rubber deck",
          "The submarine's deck seen from above: staggered black anechoic rubber tiles, a path "
          "worn along y, a few tiles gone (rusty steel), salt bloom.",
          rec_why="The deck floor; tiles in both axes."),
    Piece("SDRUBR2", tex_rubr2, "flat", (64, 64), ["SDRUBR2"], 2, "no",
          "Deck with hatch",
          "The same deck (same seed) with a flush round escape hatch: a steel coaming, a rubber-clad "
          "lid, a hinge and a small handwheel. A single piece.",
          rec_why="One per hatch; it links to the SDBULK1 hatch inside."),
    Piece("SDROCK1", tex_rock1, "wall", (64, 128), ["SDROCK1"], 3, "xy",
          "Excavated bedrock (wall)",
          "The bedrock of the excavated shelters: dark gneiss in blasted facets lit from the top "
          "left, flecks of pink feldspar, quartz veins, seepage streaks, the half-barrels of the "
          "perimeter blast holes and a rock bolt.",
          rec_why="The vertical half-barrels say «blasted out», not «cave»."),
    Piece("SDROCK2", tex_rock2, "flat", (64, 64), ["SDROCK2"], 4, "xy",
          "Excavated bedrock (ceiling)",
          "The same rock on the ceiling: facets, drips, two bolt plates on the 32 px grid and "
          "calcite bloom.",
          rec_why="Ceiling of the shelters and tunnels; tiles in both axes."),
    Piece("SDBULK1", tex_bulk1, "wall", (128, 128), ["SDBULK1"], 5, "no",
          "Round watertight hatch",
          "A round watertight door in a «шаровый» grey bulkhead: a bare steel coaming, a leaf with a "
          "stiffening ring, six lever dogs, two hinges, a red handwheel, the compartment number «3» in "
          "red (bigfont), oil and scuffs at the bottom.",
          rec_why="The icon of the submarine's interior. A single piece: it does not tile.",
          scene={"left": "SDNAVC1", "right": "SDNAVC1", "floor": "SDRUBR1", "ceil": "SDCEIL2"}),
    Piece("SDNAVC1", tex_navc1, "wall", (128, 128), ["SDNAVC1"], 6, "x",
          "Control room panel",
          "A control room panel: grey-green steel, four black-faced gauges (depth and "
          "pressure), the mimic diagram of the submarine's compartments with its pilot lamps, two rows of "
          "annunciator lights (some lit, their labels are dashes) and a row of switches.",
          rec_why="Distinct from the dam's SDCTRL1 at a glance (black dials, green, the boat's mimic diagram).",
          scene={"floor": "SDRUBR1", "ceil": "SDCEIL2"}),
    Piece("SDCONT1", tex_cont1, "wall", (128, 128), ["SDCONT1"], 7, "x",
          "Shipping container",
          "The side of a container: trapezoidal corrugation in faded red, rails top and bottom, corner "
          "posts with their castings, rust bleeding from the rails, «ММФ» (Merchant Fleet) in white in "
          "our own alphabet, the box number in 3×5 digits and a plate.",
          rec_why="Containers in a row tile in x; for stacks, one line per container."),
    Piece("SDCRAN1", tex_cran1, "wall", (64, 128), ["SDCRAN1"], 8, "xy",
          "Crane lattice (masked)",
          "The lattice of a dock crane's jib, MASKED (transparent background, a mid texture on a two-sided "
          "line): two angle-iron chords, batten plates every 64 px, zigzag diagonals with gussets and "
          "rivets, faded yellow paint and rust.",
          masked=True,
          rec_why="The same RGBA exception as SDCHAN1 and SDINSL1. Against the sky it is the crane; tiles in both axes "
                  "as an endless jib.",
          scene={"left": "SDCRAN1", "right": "SDCRAN1", "back": "SDCRAN1", "floor": "SDPIER1", "ceil": None}),
    Piece("SDPIER1", tex_pier1, "flat", (64, 64), ["SDPIER1"], 9, "x",
          "Concrete pier with bollard",
          "A concrete pier seen from above: oil-stained slabs, a cast-iron bollard on its "
          "plate with a mooring line to the edge, the quay edge in yellow and black and the steel angle over the water "
          "(at the bottom of the flat). Tiles in x along the pier.",
          rec_why="The water's edge is at the bottom of the flat: align it in UDMF. With the approved water SDWATR1-4."),
]
SHARED_SEED = {"SDHULL2": "SDHULL1", "SDRUBR2": "SDRUBR1"}
PAINT_BOX = {"SDHULL2": NUMBER_BOX, "SDRUBR2": HATCH_BOX}
REUSED = [("SDWATR1", "The Volga's animated water (approved, D107): it serves the harbour basin, not redrawn."),
          ("SDDAM2", "Concrete at the waterline (approved, D107): the pier's face seen from the water.")]

ROOM = {"wall": "SDROCK1", "floor": "SDPIER1", "ceil": "SDROCK2", "light": 0.92, "sky": "day"}
OVERVIEWS = [
    ("The excavated shelter", {"left": "SDHULL2", "right": "SDROCK1", "back": "SDHULL1", "floor": "SDPIER1",
                             "ceil": "SDROCK2"}),
    ("Inside the submarine", {"left": "SDNAVC1", "right": "SDNAVC1", "back": "SDBULK1", "floor": "SDRUBR1",
                              "ceil": "SDCEIL2"}),
    ("The harbour basin", {"left": "SDCONT1", "right": "SDDAM2", "back": "SDCRAN1", "floor": "SDWATR1", "ceil": None}),
]


def build(out_dir: Path | None = None):
    return ep3lib.build_set(SET_NAME, PIECES, BATCH_SEED, SCRIPT_REL, out_dir)


def main() -> None:
    entries, _ = build()
    for e in entries:
        print(f'{e["piece"]:8s} {e["width"]:3d}x{e["height"]:3d} v{e["palette_version"]} '
              f'colours={e["colours_used"]:3d} luma={e["mean_luma"]:6.1f} seam={e["seam_score"]}')


if __name__ == "__main__":
    main()
