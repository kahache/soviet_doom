"""Episode 3, MAP07 — the Arctic set: the radar station on Novaya Zemlya (D112, P4).

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_arctic.py
The whole episode and the CEO's sheet: tools/art/gen_episode3.py.

DRAFTS for the CEO: PNGs to work/art/episode3/arctic/, never to assets/.
Palette v1 throughout (ep3lib): snow and frost are the top of concrete_cold
(already a cold, slightly blue white), ice is steel_blue kept under 0.5 in
large areas (ART-BIBLE §6.2: bright steel_blue is the Legion's chrome), the
radar's phosphor is military_green with a cream_yellow beam. No lettering:
label plates are pixel "words" that say nothing.

The radar screen (SDRADR1-4) is four frames for ANIMDEFS, like SDMOLT: the
beam turns 90 degrees a frame, so frame 4 leads back into frame 1.
SDRWY2 replays SDRWY1's seed on purpose: the same slabs, with the painted
centre line on top.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import Overlay, blend, fbm, grain, shade, to_rgb  # noqa: E402
import ep3lib  # noqa: E402
from ep3lib import FRAMES, Piece, col, rivet  # noqa: E402

SET_NAME = "arctic"
SCRIPT_REL = "tools/art/gen_arctic.py"
BATCH_SEED = 5700
FLAT = 64


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


# ================================================================ snow
SNOW_TONE = 0.84             # concrete_cold: wind-packed snow, the brightest floor of the mod
SPARKLE = 0.006              # share of pixels that glint white


def tex_snow1() -> np.ndarray:
    """Wind-packed snow: long sastrugi ridges across the tile, lit on the
    faces that look up the tile, blue-grey in their lee, a few glints."""
    rng = rng_for(1)
    w = h = FLAT
    drift = fbm(w, h, 2, 3, rng, 0.5, aspect=0.35)
    fine = fbm(w, h, 8, 3, rng)
    field = SNOW_TONE + (drift - 0.5) * 0.10 + (fine - 0.5) * 0.05 + grain(w, h, rng, 0.012)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    slope = drift - np.roll(drift, 1, axis=0)
    slope = slope / (slope.std() + 1e-9)
    f = 1 + np.clip(slope * 0.06, -0.18, 0.10)
    rgb = shade(rgb, f)
    glint = (rng.random((h, w)) < SPARKLE) & (field > SNOW_TONE)
    rgb[glint] = (255, 255, 255)
    return rgb


# ================================================================ ice
ICE_TONE = 0.44              # steel_blue: clear sea ice over dark water
ICE_CELL = 16


def tex_ice1() -> np.ndarray:
    """Sea ice, a floor: refrozen floes of slightly different blue, white
    pressure cracks along their borders, frosted haze, strings of trapped
    bubbles."""
    rng = rng_for(2)
    w = h = FLAT
    f1, f2, ident, ox, oy = ep3lib.cells_voronoi(w, h, ICE_CELL, rng, 0.9)
    tone = rng.uniform(-0.05, 0.05, ident.max() + 1)[ident]
    depth = fbm(w, h, 3, 3, rng)
    field = ICE_TONE + tone + (depth - 0.5) * 0.18 + grain(w, h, rng, 0.010)
    rgb = to_rgb(np.clip(field, 0, 1), "steel_blue")
    haze = fbm(w, h, 4, 3, rng)
    rgb = blend(rgb, col("concrete_cold", 0.70), np.clip((haze - 0.58) * 2.0, 0, 0.55))
    gap = f2 - f1
    open_crack = fbm(w, h, 4, 2, rng) > 0.56
    rgb = np.where(((gap >= 1.0) & (gap < 2.2) & open_crack)[..., None], shade(rgb, 0.84), rgb)
    rgb[(gap < 1.0) & open_crack] = col("concrete_cold", 0.86)
    rgb = np.where(((gap < 1.0) & ~open_crack)[..., None], shade(rgb, 0.88), rgb)
    fr = ep3lib.ridged(fbm(w, h, 3, 2, rng)) > 0.975
    rgb[fr & (gap >= 1.0)] = col("concrete_cold", 0.70)
    for _ in range(7):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        for k in range(int(rng.integers(3, 7))):
            rgb[(y + k) % h, (x + (k * 2) // 3) % w] = col("concrete_cold", 0.92)
    return rgb


STRATA = 32                  # SDICE2: one light layer every 32 px
GRIT_Y = 92                  # the moraine grit layer


def tex_ice2() -> np.ndarray:
    """Glacier ice, a wall: wavy annual layers, bubbly white strata, one
    thin layer of moraine grit, vertical melt runs, conchoidal facets."""
    rng = rng_for(3)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    wave = 3.0 * np.sin(2 * np.pi * xx / w) + 1.6 * np.sin(4 * np.pi * xx / w + 1.3)
    band = np.sin(2 * np.pi * (yy + wave) / STRATA)
    field = 0.42 + band * 0.05 + (fbm(w, h, 4, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.010)
    rgb = to_rgb(np.clip(field, 0, 1), "steel_blue")
    bubbly = (band > 0.80) & (fbm(w, h, 8, 2, rng) > 0.45)
    rgb = blend(rgb, col("concrete_cold", 0.74), bubbly * (band - 0.80) * 3.0)
    grit = np.abs(ep3lib.wrap_dist(yy + wave - GRIT_Y, h)) < 1.1
    gfield = fbm(w, h, 16, 2, rng)
    rgb = np.where((grit & (gfield > 0.35))[..., None], shade(rgb, 0.62), rgb)
    rgb = np.where((grit & (gfield > 0.62))[..., None], np.array(col("rust_brown", 0.26), np.uint8), rgb)
    f1, f2, ident, ox, oy = ep3lib.cells_voronoi(w, h, 32, rng, 0.9)
    f = 1 - (ox * 0.5 + oy * 0.8) / 32 * 0.07
    melt = np.clip(fbm(w, h, 8, 3, rng, aspect=10.0) - 0.58, 0, 1) * 1.6
    f *= 1 + melt * 0.5
    return shade(rgb, f)


# ================================================================ radome
RADOME_ROW = 32              # triangle rows of 32 px; triangle base 32 px
RADOME_UP, RADOME_DOWN = 0.84, 0.72   # concrete_cold: the two facet families of a geodesic dome
BOLT_PITCH = 6


def tex_radm1() -> np.ndarray:
    """Radome skin: off-white fibreglass panels of a geodesic dome
    (triangles in staggered rows, the two facet families lit differently),
    flanged seams with bolts, rime lodged on the horizontal flanges, faint
    grime runs."""
    rng = rng_for(4)
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    row = yy // RADOME_ROW
    v = (yy % RADOME_ROW + 0.5) / RADOME_ROW
    o = (row % 2) * 16
    d = ep3lib.wrap_dist(xx + 0.5 - o, 32)
    up = np.abs(d) < 16 * v
    k_up = np.floor((xx + 0.5 - o + 16) / 32).astype(int) % 4
    k_dn = np.floor((xx + 0.5 - o) / 32).astype(int) % 4
    pid = row * 8 + np.where(up, 2 * k_up, 2 * k_dn + 1)
    jitter = rng.uniform(-0.035, 0.035, 32)[pid]
    field = np.where(up, RADOME_UP, RADOME_DOWN) + jitter + (fbm(w, h, 4, 3, rng) - 0.5) * 0.04 \
        + grain(w, h, rng, 0.010)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    # pillow: each panel a little lighter towards its top
    f = 1.04 - 0.08 * v
    edist = np.abs(np.abs(d) - 16 * v) * 0.894
    f = np.where(edist < 0.9, 0.62, f)
    f = np.where((edist >= 0.9) & (edist < 1.8), f * 1.06, f)
    ly = yy % RADOME_ROW
    f = np.where(ly == 0, 0.58, f)
    f = np.where(ly == 1, f * 1.10, f)
    grime = np.clip(fbm(w, h, 8, 3, rng, aspect=8.0) - 0.55, 0, 1) * 0.5
    rgb = shade(rgb, f * (1 - grime))
    bolt = col("concrete_cold", 0.42)
    for y in range(h):
        lyy = y % RADOME_ROW
        if lyy == 3:
            for x in range(4, w, 8):
                rgb[y, x] = bolt
        if lyy % BOLT_PITCH == 4:
            vv = (lyy + 0.5) / RADOME_ROW
            oo = ((y // RADOME_ROW) % 2) * 16
            for kx in range(4):
                for s in (-1, 1):
                    x = int(round(32 * kx + oo + s * 16 * vv + s * 1.5)) % w
                    rgb[y, x] = bolt
    rime_zone = (ly >= RADOME_ROW - 3)
    rime = rime_zone & (fbm(w, h, 16, 2, rng) + (ly - (RADOME_ROW - 3)) * 0.12 > 0.62)
    rgb[rime] = col("concrete_cold", 0.96)
    rgb[rime & (rng.random((h, w)) < 0.25)] = (255, 255, 255)
    return rgb


# ================================================================ corrugated hut
HUT_PITCH = 8                # corrugation period
HUT_GREEN = 0.50             # military_green, faded
LAP_Y = 60                   # the horizontal lap seam
DRIFT_Y = 110                # mean top of the snow drift at the foot


def tex_hut1() -> np.ndarray:
    """Barracks wall of corrugated sheet in faded 4BO green: a riveted lap
    seam, rust at the seam and the foot, hoarfrost feathering the ridges
    (thicker low down), a snow drift against the base, icicles under the
    eave."""
    rng = rng_for(5)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    slope = np.cos(2 * np.pi * (xx + 0.5) / HUT_PITCH)
    field = HUT_GREEN + (fbm(w, h, 4, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.02)
    paint = to_rgb(np.clip(field, 0, 1), "military_green")
    faded = fbm(w, h, 3, 3, rng) > 0.62
    paint = np.where(faded[..., None], to_rgb(np.clip(field * 0.9 + 0.12, 0, 1), "khaki_olive"), paint)
    near = np.clip(1 - np.abs(yy - LAP_Y) / 10, 0, 1) + np.clip((yy - 96) / 32, 0, 1)
    rusty = (fbm(w, h, 8, 3, rng) + near * 0.35) > 0.82
    paint = np.where(rusty[..., None], to_rgb(np.clip(field * 0.8, 0, 1), "rust_brown"), paint)
    f = 1 + 0.24 * slope
    f[yy == LAP_Y] = 0.45
    f[yy == LAP_Y + 1] *= 1.25
    f[:4] *= np.array([0.35, 0.5, 0.65, 0.8])[:, None]
    rgb = shade(paint, f)
    for x in range(2, w, HUT_PITCH):
        rivet(rgb, x, LAP_Y + 3, "steel_blue", 0.40)
        ln = int(rng.integers(4, 14))
        for k in range(ln):
            if rng.random() < 0.8:
                rgb[LAP_Y + 6 + k, x + (k // 6) % 2] = col("rust_brown", 0.40 - k * 0.012)
    # hoarfrost: on the lit flanks, denser towards the foot and under the eave
    amt = np.clip((yy - 40) / 80, 0, 1) * 0.55 + np.clip(1 - yy / 20, 0, 1) * 0.4
    clump = fbm(w, h, 16, 3, rng, 0.6)
    frost = (clump + amt + (slope > 0.2) * 0.10) > 1.02
    rgb[frost] = col("concrete_cold", 0.86)
    rgb[frost & (clump + amt > 1.12)] = col("concrete_cold", 0.96)
    rgb[frost & (rng.random((h, w)) < 0.06)] = (255, 255, 255)
    # snow drift
    top = DRIFT_Y + (fbm(w, 1, 4, 3, rng)[0] - 0.5) * 12
    snow = yy >= top[None, :]
    snow_rgb = to_rgb(np.clip(SNOW_TONE + (fbm(w, h, 8, 2, rng) - 0.5) * 0.08 - (yy - top[None, :]) * 0.004, 0, 1),
                      "concrete_cold")
    rgb = np.where(snow[..., None], snow_rgb, rgb)
    lip = (yy >= top[None, :]) & (yy < top[None, :] + 1.5)
    rgb[lip] = col("concrete_cold", 0.96)
    shadow = (yy >= top[None, :] - 2) & (yy < top[None, :])
    rgb = np.where(shadow[..., None], shade(rgb, 0.7), rgb)
    # icicles under the eave
    ov = Overlay(w, h)
    for x in (5, 13, 22, 29, 37, 46, 54, 61):
        ln = rng.uniform(4, 15)
        ov.polygon([(x - 1.4, 3), (x + 1.4, 3), (x + 0.1, 3 + ln)], fill=col("concrete_cold", 0.80))
        ov.line([(x - 0.6, 3), (x - 0.1, 3 + ln * 0.7)], col("concrete_cold", 0.97), 0.7)
    return ov.composite(rgb)


# ================================================================ radar console
CAB_TONE = 0.40              # steel_blue hammertone enamel, under 0.5 (ART-BIBLE §6.2)
SCOPE_C, SCOPE_R = (64, 44), 33
RINGS = (11, 22)
BLIPS = ((40, 18), (115, 27), (200, 12), (250, 29), (305, 21))   # (bearing deg, range px)
TRAIL = 70.0                 # degrees of afterglow
SWEEP0 = 20.0
DESK_Y = 90


def console_base(rng: np.random.Generator) -> np.ndarray:
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    field = CAB_TONE + (fbm(w, h, 16, 2, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.02)
    rgb = to_rgb(np.clip(field, 0, 1), "steel_blue")
    f = np.ones((h, w))
    f[:, 0] = 0.45
    f[:, 1] *= 1.2
    f[DESK_Y] *= 1.35
    f[DESK_Y + 1:DESK_Y + 4] *= 0.75
    rgb = shade(rgb, f)
    ov = Overlay(w, h)
    cx, cy = SCOPE_C
    ov.rect(cx - 40, 3, cx + 40, 86, fill=col("steel_blue", 0.22))
    ov.rect(cx - 40, 3, cx + 40, 4, fill=col("steel_blue", 0.55))
    ov.rect(cx - 40, 3, cx - 39, 86, fill=col("steel_blue", 0.48))
    ov.ellipse(cx - SCOPE_R - 4, cy - SCOPE_R - 4, cx + SCOPE_R + 4, cy + SCOPE_R + 4, fill=col("concrete_cold", 0.05))
    ov.arc_ring(cx, cy, SCOPE_R + 3, SCOPE_R + 1, 200, 340, col("steel_blue", 0.60))
    for sx in (cx - 36, cx + 34):
        for sy in (7, 81):
            ov.ellipse(sx - 1.5, sy - 1.5, sx + 1.5, sy + 1.5, fill=col("steel_blue", 0.58))
    # side strips: knobs and lamps
    for sx in (11, 117):
        for i, sy in enumerate((16, 36, 56)):
            ov.ellipse(sx - 5, sy - 5, sx + 5, sy + 5, fill=col("concrete_cold", 0.08))
            ov.ellipse(sx - 4, sy - 4, sx + 4, sy + 4, fill=col("concrete_cold", 0.20))
            a = np.deg2rad(rng.uniform(200, 340))
            ov.line([(sx, sy), (sx + 3.5 * np.cos(a), sy + 3.5 * np.sin(a))], col("plaster_warm", 0.9), 1.0)
        ov.ellipse(sx - 2.5, 72, sx + 2.5, 77, fill=col("flag_red" if sx < 64 else "hazard_yellow", 0.85))
        ov.rect(sx - 0.5, 73, sx + 0.5, 74, fill=(255, 255, 255))
    # desk: a row of knobs, toggles, the kick plate
    for i, kx in enumerate(range(12, 124, 14)):
        ov.ellipse(kx - 4, 99, kx + 4, 107, fill=col("concrete_cold", 0.08))
        ov.ellipse(kx - 3, 100, kx + 3, 106, fill=col("concrete_cold", 0.22))
        ov.rect(kx - 0.5, 99, kx + 0.5, 102, fill=col("plaster_warm", 0.9))
    rgb = ov.composite(rgb)
    for sx in (11, 117):
        for sy in (16, 36, 56):
            ep3lib.illegible_label(rgb, sx - 5, sy + 7, 10, col("plaster_warm", 0.85), rng)
    for kx in range(12, 124, 14):
        ep3lib.illegible_label(rgb, kx - 5, 110, 10, col("plaster_warm", 0.82), rng)
    ep3lib.illegible_label(rgb, cx - 20, 92, 40, col("plaster_warm", 0.80), rng)
    kick = to_rgb(np.clip(0.12 + grain(w, h, rng, 0.02), 0, 1), "concrete_cold")
    rgb = np.where((yy >= 118)[..., None], kick, rgb)
    rgb[118, :] = col("concrete_cold", 0.40)
    return rgb


def radar_frames() -> list[np.ndarray]:
    """Radar console with a round PPI scope, four frames: the beam turns
    90 degrees a frame, leaving a green afterglow; range rings, a bearing
    cross, five echoes that flare when the beam passes and fade. Hammertone
    cabinet, knobs, lamps, label plates that say nothing."""
    rng = rng_for(6)
    base = console_base(rng)
    h, w = base.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w] + 0.5
    cx, cy = SCOPE_C
    dx, dy = xx - cx, yy - cy
    rad = np.hypot(dx, dy)
    ang = np.degrees(np.arctan2(dy, dx)) % 360
    inside = rad < SCOPE_R
    noise = grain(w, h, rng, 0.03)
    frames = []
    for k in range(FRAMES):
        sweep = (SWEEP0 + 90 * k) % 360
        behind = (sweep - ang) % 360
        glow = np.exp(-behind / TRAIL)
        t = 0.10 + 0.50 * glow + noise
        for r in RINGS:
            t = np.where(np.abs(rad - r) < 0.55, t + 0.16, t)
        t = np.where((np.abs(dx) < 0.55) | (np.abs(dy) < 0.55), t + 0.10, t)
        t = np.where(np.abs(rad - SCOPE_R + 1) < 0.7, t + 0.12, t)
        for bearing, rng_px in BLIPS:
            bx = cx + rng_px * np.cos(np.deg2rad(bearing))
            by = cy + rng_px * np.sin(np.deg2rad(bearing))
            since = (sweep - bearing) % 360
            flare = np.exp(-since / 160.0)
            blob = np.hypot(xx - bx, yy - by) < 1.6
            t = np.where(blob, np.maximum(t, 0.35 + 0.62 * flare), t)
        screen = to_rgb(np.clip(t, 0, 1), "military_green")
        beam = behind < 3.5
        screen = np.where(beam[..., None], np.array(col("cream_yellow", 0.92), np.uint8), screen)
        screen = np.where((behind < 1.2)[..., None] & (rad < SCOPE_R - 2)[..., None],
                          np.array((255, 255, 255), np.uint8), screen)
        frame = np.where(inside[..., None], screen, base)
        # glass glint
        glint = inside & (np.abs(rad - (SCOPE_R - 6)) < 0.8) & (ang > 200) & (ang < 235)
        frame[glint] = col("concrete_cold", 0.70)
        frames.append(frame)
    return frames


# ================================================================ frosted blast door
FRAME_BOX = (8, 6, 120, 128)
LEAF_BOX = (18, 14, 110, 128)
DOOR_GREEN = 0.42
LEVER_YS = (46, 92)


def tex_herm1() -> np.ndarray:
    """Hermetic blast door, frosted: a steel frame painted in hazard
    stripes, a thick 4BO-green leaf with a rubber gasket, two heavy
    lever handles, two hinges, a label plate; rime creeping in from every
    edge and thicker low down, icicles off the lintel. A picture, not a
    surface: it does not tile."""
    rng = rng_for(7)
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    wall = to_rgb(np.clip(0.48 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.12 + grain(w, h, rng, 0.02), 0, 1), "concrete_cold")
    fx0, fy0, fx1, fy1 = FRAME_BOX
    lx0, ly0, lx1, ly1 = LEAF_BOX
    frame = (xx >= fx0) & (xx < fx1) & (yy >= fy0) & (yy < fy1)
    leaf = (xx >= lx0) & (xx < lx1) & (yy >= ly0) & (yy < ly1)
    stripe = ((xx + yy) // 8) % 2 == 0
    hz = np.where(stripe[..., None], np.array(col("hazard_yellow", 0.70), np.uint8),
                  np.array(col("concrete_cold", 0.10), np.uint8))
    hz = shade(hz, 1 + grain(w, h, rng, 0.06))
    rgb = np.where(frame[..., None], hz, wall)
    gfield = DOOR_GREEN + (fbm(w, h, 3, 4, rng) - 0.5) * 0.14 + grain(w, h, rng, 0.02)
    green = to_rgb(np.clip(gfield, 0, 1), "military_green")
    chips = fbm(w, h, 12, 3, rng) > 0.72
    green = np.where(chips[..., None], to_rgb(np.clip(gfield * 0.8, 0, 1), "steel_blue"), green)
    rgb = np.where(leaf[..., None], green, rgb)
    f = np.ones((h, w))
    ep3lib.ep2lib.bevel(f, fx0, fy0, fx1, fy1 + 1, 1.2, 0.6, 2)
    f[ly0 - 2:ly0, lx0 - 2:lx1 + 2] = 0.30            # gasket
    f[ly0:ly1, lx0 - 2:lx0] = 0.30
    f[ly0:ly1, lx1:lx1 + 2] = 0.30
    ep3lib.ep2lib.bevel(f, lx0, ly0, lx1, ly1 + 1, 1.25, 0.65, 2)
    ep3lib.ep2lib.bevel(f, lx0 + 8, ly0 + 8, lx1 - 8, ly1 - 6, 0.75, 1.2, 1)   # recessed panel
    rgb = shade(rgb, f)
    ov = Overlay(w, h)
    for ly in LEVER_YS:
        ov.ellipse(26, ly - 6, 38, ly + 6, fill=col("steel_blue", 0.18))
        ov.ellipse(27, ly - 5, 37, ly + 5, fill=col("steel_blue", 0.40))
        ov.line([(32, ly), (60, ly - 3)], col("steel_blue", 0.15), 4.6)
        ov.line([(32, ly - 1), (60, ly - 4)], col("steel_blue", 0.45), 2.4)
        ov.ellipse(57, ly - 8, 65, ly, fill=col("flag_red", 0.45))
        ov.ellipse(58, ly - 7, 61, ly - 4, fill=col("flag_red", 0.75))
    for hy in (26, 100):
        ov.rect(106, hy, 115, hy + 16, fill=col("steel_blue", 0.20))
        ov.rect(107, hy, 114, hy + 16, fill=col("steel_blue", 0.38))
        ov.rect(108, hy, 109, hy + 16, fill=col("steel_blue", 0.58))
    ov.rect(72, 24, 98, 34, fill=col("concrete_cold", 0.10))
    ov.rect(73, 25, 97, 33, fill=col("plaster_warm", 0.86))
    rgb = ov.composite(rgb)
    ep3lib.illegible_label(rgb, 75, 27, 20, col("flag_red", 0.40), rng, rows=3)
    for x in range(lx0 + 4, lx1 - 2, 10):
        rivet(rgb, x, ly0 + 3, "military_green", 0.45)
    # rime: from every edge of the leaf and the frame, thicker low down
    edge_d = np.minimum.reduce([np.abs(xx - lx0), np.abs(xx - lx1), np.abs(yy - ly0),
                                np.abs(xx - fx0), np.abs(xx - fx1), np.abs(yy - fy0)]).astype(float)
    amt = np.clip(1 - edge_d / 9, 0, 1) * 0.55 + np.clip((yy - 70) / 58, 0, 1) * 0.45
    clump = fbm(w, h, 16, 3, rng, 0.6)
    rime = (clump + amt) > 1.0
    rgb[rime] = col("concrete_cold", 0.86)
    rgb[rime & (clump + amt > 1.1)] = col("concrete_cold", 0.97)
    snow_top = 120 + (fbm(w, 1, 4, 3, rng)[0] - 0.5) * 6
    snow = yy >= snow_top[None, :]
    rgb = np.where(snow[..., None], to_rgb(np.clip(SNOW_TONE + grain(w, h, rng, 0.02), 0, 1), "concrete_cold"), rgb)
    ov = Overlay(w, h)
    for x in range(12, 118, 7):
        ln = rng.uniform(3, 14) if rng.random() < 0.8 else rng.uniform(14, 22)
        x = x + rng.uniform(-2, 2)
        ov.polygon([(x - 1.6, fy0 + 2), (x + 1.6, fy0 + 2), (x + 0.2, fy0 + 2 + ln)], fill=col("concrete_cold", 0.82))
        ov.line([(x - 0.7, fy0 + 2), (x - 0.1, fy0 + 2 + ln * 0.7)], col("concrete_cold", 0.98), 0.7)
    return ov.composite(rgb)


# ================================================================ runway slabs
SLAB_W, SLAB_H = 64, 32      # aerodrome slabs, staggered half a slab per row
SLAB_TONE = 0.50
DIMPLE = (6, 4)              # PAG-type anti-skid dimples: pitch in x, y
STRIPE_X = (27, 37)          # SDRWY2: the painted centre line
STRIPE_ON = 40               # dash length per 64 px


def runway(rng: np.random.Generator) -> np.ndarray:
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    row = yy // SLAB_H
    jx = (row % 2) * (SLAB_W // 2)
    lx = (xx - jx) % SLAB_W
    ly = yy % SLAB_H
    slab = row * 2 + ((xx - jx) // SLAB_W) % 2
    tone = rng.uniform(-0.04, 0.04, 8)[slab % 8]
    field = SLAB_TONE + tone + (fbm(w, h, 4, 3, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.02)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    f = np.ones((h, w))
    inner = (lx >= 3) & (lx <= SLAB_W - 4) & (ly >= 3) & (ly <= SLAB_H - 4)
    dimple = inner & (lx % DIMPLE[0] < 2) & (ly % DIMPLE[1] == 1)
    f[dimple] = 0.78
    f[inner & (lx % DIMPLE[0] < 2) & (ly % DIMPLE[1] == 2)] = 1.06
    joint = (lx == 0) | (ly == 0)
    f[joint] = 0.45
    f[(lx == 1) | (ly == 1)] *= 1.12
    tyre = np.clip(fbm(w, h, 4, 3, rng, aspect=10.0) - 0.60, 0, 1) * 1.2
    f *= 1 - tyre
    rgb = shade(rgb, f)
    packed = joint & (fbm(w, h, 16, 2, rng) > 0.45)
    rgb[packed] = col("concrete_cold", 0.86)
    powder = fbm(w, h, 3, 3, rng, aspect=0.3)
    rgb = blend(rgb, col("concrete_cold", 0.86), np.clip((powder - 0.58) * 3.0, 0, 0.85))
    return rgb


def tex_rwy1() -> np.ndarray:
    """Airfield slabs: staggered concrete plates with rows of anti-skid
    dimples (the Soviet PAG pattern), snow packed in the joints, powder
    snow blowing across, dark tyre streaks along the runway (y)."""
    return runway(rng_for(8))


def tex_rwy2() -> np.ndarray:
    """SDRWY1's slabs (same seed) with the white centre-line dash,
    40 px on, 24 off, worn so the dimples show through."""
    rng = rng_for(8)
    rgb = runway(rng)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w]
    x0, x1 = STRIPE_X
    paint = (xx >= x0) & (xx < x1) & (yy < STRIPE_ON)
    worn = (rng.random((h, w)) < 0.10) | (fbm(w, h, 8, 2, rng) > 0.70)
    lum = rgb.astype(float).mean(-1)
    t = np.clip(0.80 + (lum - lum.mean()) / 255 * 0.8, 0, 1)
    white = to_rgb(np.clip(t + 0.10, 0, 1), "concrete_cold")
    return np.where((paint & ~worn)[..., None], white, rgb)


# ================================================================ pieces
PIECES = [
    Piece("SDSNOW1", tex_snow1, "flat", (64, 64), ["SDSNOW1"], 1, "xy",
          "Nieve",
          "Nieve compactada por el viento: crestas largas de sastrugi a lo ancho, iluminadas en la cara que mira "
          "hacia arriba de la loseta, azuladas a sotavento, algún destello.",
          rec_why="El suelo de todo el exterior. Es el suelo más claro del mod: ver la pregunta 2 sobre la luz."),
    Piece("SDICE1", tex_ice1, "flat", (64, 64), ["SDICE1"], 2, "xy",
          "Hielo (suelo)",
          "Hielo marino: témpanos recongelados de azules distintos, grietas de presión blancas en sus bordes, "
          "escarcha en velos, hileras de burbujas atrapadas.",
          rec_why="Azul de steel_blue por debajo de 0.5 (el cromo de la Legión queda arriba, ART-BIBLE §6.2)."),
    Piece("SDICE2", tex_ice2, "wall", (64, 128), ["SDICE2"], 3, "xy",
          "Hielo de glaciar (pared)",
          "Pared de hielo de glaciar: estratos anuales ondulados, capas blancas de burbujas, una veta fina de "
          "grava de morrena, regueros verticales de deshielo y facetas de fractura.",
          rec_why="Para los cortes del glaciar junto a la estación; tila en los dos ejes."),
    Piece("SDRADM1", tex_radm1, "wall", (128, 128), ["SDRADM1"], 4, "xy",
          "Placas del radomo",
          "Piel del radomo: paneles de fibra blanca de una cúpula geodésica (triángulos en filas al tresbolillo, "
          "las dos familias de caras con luz distinta), juntas con pestaña y pernos, escarcha en las pestañas "
          "horizontales, chorretes de suciedad.",
          rec_why="La pieza que dice «radar de la Guerra Fría» desde lejos. En una pared curva (varias líneas en "
                  "arco) los triángulos venden la cúpula."),
    Piece("SDHUT1", tex_hut1, "wall", (64, 128), ["SDHUT1"], 5, "x",
          "Barracón de chapa con escarcha",
          "Pared de barracón de chapa ondulada en verde 4BO desvaído: junta solapada remachada, óxido en la junta "
          "y al pie, escarcha en plumas sobre las crestas (más abajo, más), ventisquero contra la base y "
          "carámbanos bajo el alero.",
          rec_why="Pariente del SDRUST1 de la fábrica pero helado y pintado. Alero arriba y nieve abajo: tila solo en x."),
    Piece("SDRADR", radar_frames, "wall", (128, 128), [f"SDRADR{i}" for i in range(1, FRAMES + 1)], 6, "x",
          "Consola de radar (animada, 4 fotogramas)",
          "Consola con la pantalla redonda (PPI) del radar: el haz gira 90° por fotograma dejando un rastro verde, "
          "anillos de distancia, cruz de rumbo y cinco ecos que se encienden al pasar el haz y se apagan. Mueble "
          "de esmalte martelé gris-azul, mandos, pilotos y placas que parecen texto y no dicen nada.",
          rec_why="Necesita ANIMDEFS (mod-engineer); propongo 12 tics por fotograma para que el barrido no "
                  "parezca un ventilador. Se tila en x como una fila de consolas.",
          scene={"floor": "SDFLR1", "ceil": "SDCEIL1"}),
    Piece("SDHERM1", tex_herm1, "wall", (128, 128), ["SDHERM1"], 7, "no",
          "Puerta blindada con escarcha",
          "Puerta hermética («гермодверь»): marco de acero con franjas de peligro, hoja gruesa verde 4BO con junta "
          "de goma, dos palancas de cierre, dos bisagras, una placa; escarcha que entra desde todos los bordes y "
          "más gruesa abajo, carámbanos colgando del dintel.",
          rec_why="El verde y las bisagras atan con SDDOOR1 de la base. Pieza única: no tila."),
    Piece("SDRWY1", tex_rwy1, "flat", (64, 64), ["SDRWY1"], 8, "xy",
          "Pista: losas de aeródromo",
          "Losas de pista al tresbolillo con las filas de hoyuelos antideslizantes de las placas PAG soviéticas, "
          "nieve prensada en las juntas, nieve en polvo cruzando y marcas oscuras de neumático a lo largo de y.",
          rec_why="El dibujo de hoyuelos es el detalle que hace soviética la pista."),
    Piece("SDRWY2", tex_rwy2, "flat", (64, 64), ["SDRWY2"], 8, "y",
          "Pista: línea central",
          "Las mismas losas (misma semilla) con el trazo blanco de la línea central, 40 px pintados y 24 sin "
          "pintar, gastado de modo que los hoyuelos se ven a través.",
          rec_why="Una fila de SDRWY2 entre filas de SDRWY1. Tila en y; en x no (es una sola línea)."),
]
SHARED_SEED = {"SDRWY2": "SDRWY1"}
PAINT_BOX = {"SDRWY2": (STRIPE_X[0], 0, STRIPE_X[1], STRIPE_ON)}   # x0, y0, x1, y1 of the paint over the twin

ROOM = {"wall": "SDHUT1", "floor": "SDSNOW1", "ceil": None, "light": 0.95, "sky": "day"}
OVERVIEWS = [
    ("La estación, fuera", {"left": "SDRADM1", "right": "SDHUT1", "back": "SDHERM1", "floor": "SDSNOW1", "ceil": None}),
    ("La sala del radar", {"left": "SDRADR1", "right": "SDCONC1", "back": "SDRADR1", "floor": "SDFLR1",
                           "ceil": "SDCEIL1"}),
    ("La pista junto al glaciar", {"left": "SDICE2", "right": "SDICE2", "back": "SDRADM1", "floor": "SDRWY2",
                                   "ceil": None}),
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
