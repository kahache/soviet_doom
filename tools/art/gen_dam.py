"""Episode 2, MAP05 — the dam set: the Volga hydroelectric station at Zhiguli (D104, P4).

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_dam.py
The whole episode and the CEO's sheet: tools/art/gen_episode2.py.

DRAFTS for the CEO: PNGs to work/art/episode2/dam/, never to assets/.
Palette v1 throughout (ep2lib). No text at all except pixel "labels" that
say nothing and 3x5 pixel digits: the control panel's plates read as text
at 1x and are illegible by construction, no font involved.

The water (SDWATR1-4) is four frames for ANIMDEFS, like SDMOLT: a ripple
field that turns through a full phase while it drifts one tile, so frame 4
leads back into frame 1. It is steel_blue on purpose: the cobalt of palette
v2 belongs to the portal and nothing in the world may share it (D66).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import Overlay, fbm, grain, shade, to_rgb  # noqa: E402
import ep2lib  # noqa: E402
from ep2lib import FRAMES, Piece, col, rivet  # noqa: E402

SET_NAME = "dam"
SCRIPT_REL = "tools/art/gen_dam.py"
BATCH_SEED = 5500
WALL_W, WALL_H, WIDE, FLAT = 64, 128, 128, 64


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


# ================================================================ dam concrete
DAM_TONE = 0.58              # concrete_cold: the pale mass concrete of a dam
BOARD_H = 8                  # formwork boards 8 px high
LIFT = 64                    # a lift (pour) joint every 64 px
TIE_XS, TIE_YS = (16, 48), (12, 44, 76, 108)   # form-tie holes


def dam_concrete(w: int, h: int, rng: np.random.Generator) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    board = yy // BOARD_H
    bt = rng.uniform(-0.025, 0.025, h // BOARD_H + 1)
    wood = fbm(w, h, 16, 3, rng, 0.5, aspect=0.15)
    field = DAM_TONE + bt[board] + (wood - 0.5) * 0.06 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.16 + grain(w, h, rng, 0.03)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    f = np.ones((h, w))
    f[yy % BOARD_H == 0] *= 0.90
    f *= 1 - np.clip(fbm(w, h, 3, 4, rng, 0.55) - 0.55, 0, 1) * 0.6
    f[yy % LIFT == LIFT - 1] *= 0.62
    f[yy % LIFT == 0] *= 1.10
    f[:, 0] *= 0.94
    f *= 1 - np.clip(fbm(w, h, 8, 3, rng, aspect=8.0) - 0.5, 0, 1) * 0.5
    rgb = shade(rgb, f)
    for tx in TIE_XS:
        for ty in TIE_YS:
            rgb[ty:ty + 2, tx:tx + 2] = col("concrete_cold", 0.14)
            rgb[ty + 2, tx:tx + 2] = col("concrete_cold", 0.72)
            ln = int(rng.integers(3, 12))
            for k in range(ln):
                if rng.random() < 0.8:
                    y = (ty + 3 + k) % h
                    rgb[y, tx + (k // 7) % 2] = col("plaster_warm", 0.80) if k < ln * 0.5 else col("concrete_cold", 0.70)
    return rgb


def tex_dam1() -> np.ndarray:
    """Mass concrete of the dam: board-marked formwork, lift joints every
    64 px, form-tie holes weeping white calcite."""
    return dam_concrete(WALL_W, WALL_H, rng_for(1))


TIDE_Y = 72                  # SDDAM2: the waterline
ALGAE_T = 0.45


def tex_dam2() -> np.ndarray:
    """The same concrete at the waterline: dark and wet below a ragged tide
    mark, green slime low down."""
    rng = rng_for(2)
    w, h = WALL_W, WALL_H
    rgb = dam_concrete(w, h, rng)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = TIDE_Y + (fbm(w, 1, 8, 3, rng)[0] - 0.5) * 8
    wet = yy >= edge[None, :]
    rgb = np.where(wet[..., None], shade(rgb, 0.52), rgb)
    line = (yy >= edge[None, :] - 1) & (yy < edge[None, :] + 1)
    rgb = np.where(line[..., None], np.array(col("rust_brown", 0.30), np.uint8), rgb)
    depth = np.clip((yy - edge[None, :]) / (h - TIDE_Y), 0, 1)
    algae_f = fbm(w, h, 6, 3, rng, aspect=1.2)
    algae = wet & (algae_f + depth * 0.5 > ALGAE_T + 0.35)
    green = to_rgb(np.clip(0.22 + (algae_f - 0.5) * 0.2, 0, 1), "military_green")
    rgb = np.where(algae[..., None], green, rgb)
    return rgb


# ================================================================ turbine housing
TURB_GREEN = 0.46            # military_green: the 4BO paint of Soviet machinery
FLANGES = ((18, 26), (104, 112))
RIBS = (0, 64)
NAMEPLATE = (10, 40, 56, 62)
HATCH = (74, 36, 118, 96)


def tex_turb1() -> np.ndarray:
    """Generator / turbine housing: painted green steel, stiffener ribs, two
    bolted flanges, a brass maker's plate (illegible pixel text, a 3x5 year),
    a bolted inspection hatch, oil weeping from the flange, a concrete
    plinth."""
    rng = rng_for(3)
    w, h = WIDE, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    field = TURB_GREEN + (fbm(w, h, 4, 4, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.02)
    rgb = to_rgb(np.clip(field, 0, 1), "military_green")
    f = np.ones((h, w))
    for rx in RIBS:
        for k, t in enumerate((1.30, 1.12, 0.95, 0.80, 0.60)):
            f[:, (rx - 2 + k) % w] *= t
    for a, b in FLANGES:
        f[a:b] *= 1.08
        f[a, :] *= 1.30
        f[b - 1, :] *= 0.70
        f[b, :] *= 0.55
    rgb = shade(rgb, f)
    for a, b in FLANGES:
        for x in range(3, w, 8):
            rivet(rgb, x, (a + b) // 2 - 1, "steel_blue", 0.50)
    # chipped paint on the flange edges, steel showing
    chips = (fbm(w, h, 16, 2, rng) > 0.70) & np.isin(yy, [FLANGES[0][0], FLANGES[1][0], FLANGES[0][0] + 1])
    rgb[chips] = col("steel_blue", 0.62)
    # oil weeping down from the upper flange
    run = np.clip(fbm(w, h, 16, 2, rng, aspect=10.0) - 0.60, 0, 1) * 2.0
    below = (yy > FLANGES[0][1]) & (yy < FLANGES[0][1] + 40)
    rgb = np.where(below[..., None], shade(rgb, 1 - run * (1 - (yy - FLANGES[0][1]) / 40)), rgb)
    # maker's plate
    x0, y0, x1, y1 = NAMEPLATE
    rgb[y0:y1, x0:x1] = col("hazard_yellow", 0.52)
    rgb[y0, x0:x1] = col("hazard_yellow", 0.80)
    rgb[y1 - 1, x0:x1] = col("hazard_yellow", 0.25)
    rgb[y0:y1, x0] = col("hazard_yellow", 0.70)
    rgb[y0:y1, x1 - 1] = col("hazard_yellow", 0.30)
    ink = col("rust_brown", 0.12)
    ep2lib.illegible_label(rgb, x0 + 4, y0 + 4, x1 - x0 - 8, ink, rng, rows=3)
    ep2lib.stamp(rgb, ep2lib.digits_mask("1957"), x0 + 4, y0 + 12, ink)
    ep2lib.illegible_label(rgb, x0 + 22, y0 + 13, x1 - x0 - 26, ink, rng, rows=2)
    for cx, cy in ((x0 + 2, y0 + 2), (x1 - 4, y0 + 2), (x0 + 2, y1 - 4), (x1 - 4, y1 - 4)):
        rivet(rgb, cx, cy, "steel_blue", 0.45)
    # inspection hatch
    x0, y0, x1, y1 = HATCH
    ov = Overlay(w, h)
    ov.rect(x0 + 1, y0 + 1, x1 + 1, y1 + 1, fill=col("military_green", 0.12) + (170,))
    ov.rect(x0, y0, x1, y1, fill=col("military_green", 0.50))
    ov.rect(x0, y0, x1, y0 + 1, fill=col("military_green", 0.75))
    ov.rect(x0, y0, x0 + 1, y1, fill=col("military_green", 0.68))
    ov.rect(x0 + 6, y0 + 26, x1 - 6, y0 + 32, fill=col("steel_blue", 0.30))
    ov.rect(x0 + 6, y0 + 26, x1 - 6, y0 + 27, fill=col("steel_blue", 0.58))
    rgb = ov.composite(rgb)
    for x in range(x0 + 3, x1 - 2, 8):
        rivet(rgb, x, y0 + 3, "steel_blue", 0.45)
        rivet(rgb, x, y1 - 5, "steel_blue", 0.45)
    for y in range(y0 + 11, y1 - 6, 8):
        rivet(rgb, x0 + 3, y, "steel_blue", 0.45)
        rivet(rgb, x1 - 5, y, "steel_blue", 0.45)
    # plinth
    plinth = to_rgb(np.clip(0.34 + (fbm(w, h, 8, 2, rng) - 0.5) * 0.1, 0, 1), "concrete_cold")
    rgb = np.where((yy >= 118)[..., None], plinth, rgb)
    rgb[118, :] = col("concrete_cold", 0.55)
    rgb[117, :] = col("military_green", 0.10)
    return rgb


# ================================================================ control panel
PANEL_TONE = 0.64            # concrete_cold: the light grey of Soviet switchboards
SECTION = 64
DIAL_XS, DIAL_Y, DIAL_R = (18, 46), 21, 10
LAMP_Y = 46
DESK_Y0, DESK_Y1 = 64, 120
BUS_Y = 72


def dial(ov: Overlay, cx: float, cy: float, r: float, angle: float) -> None:
    ov.ellipse(cx - r - 1, cy - r - 1, cx + r + 1, cy + r + 1, fill=col("concrete_cold", 0.08))
    ov.ellipse(cx - r, cy - r, cx + r, cy + r, fill=col("plaster_warm", 0.95))
    ov.arc_ring(cx, cy, r - 1, r - 3, -30, 30, col("flag_red", 0.70))
    for k in range(9):
        a = np.deg2rad(150 + k * 30)
        if 150 + k * 30 > 390:
            break
        p0 = (cx + (r - 1) * np.cos(a), cy + (r - 1) * np.sin(a))
        p1 = (cx + (r - 3.5) * np.cos(a), cy + (r - 3.5) * np.sin(a))
        ov.line([p0, p1], col("concrete_cold", 0.10), 0.9)
    a = np.deg2rad(angle)
    ov.line([(cx, cy), (cx + (r - 2) * np.cos(a), cy + (r - 2) * np.sin(a))], (0, 0, 0), 1.1)
    ov.ellipse(cx - 1.2, cy - 1.2, cx + 1.2, cy + 1.2, fill=(0, 0, 0))


def tex_ctrl1() -> np.ndarray:
    """Soviet switchboard: light grey panels, round dials with a red zone,
    a row of indicator lamps (some lit), label plates that only look like
    text, a mimic diagram of busbars and breakers on the desk, toggle
    switches, the dark kick plate. Sections of 64 px: it tiles as a long
    board."""
    rng = rng_for(4)
    w, h = WIDE, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    field = PANEL_TONE + (fbm(w, h, 4, 3, rng) - 0.5) * 0.05 + grain(w, h, rng, 0.015)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    desk = (yy >= DESK_Y0) & (yy < DESK_Y1)
    rgb = np.where(desk[..., None], shade(rgb, 1.08), rgb)
    f = np.ones((h, w))
    for sx in range(0, w, SECTION):
        f[:, sx] *= 0.45
        f[:, (sx + 1) % w] *= 1.15
    f[DESK_Y0 - 4:DESK_Y0] *= 0.55
    f[DESK_Y0 - 4] *= 1.6
    f[DESK_Y0] *= 1.2
    rgb = shade(rgb, f)
    ov = Overlay(w, h)
    lamp_cols = (("flag_red", 1.0), ("military_green", 1.0), ("hazard_yellow", 1.0), ("cream_yellow", 1.0))
    for sx in range(0, w, SECTION):
        for dx in DIAL_XS:
            dial(ov, sx + dx, DIAL_Y, DIAL_R, rng.uniform(170, 330))
            ov.rect(sx + dx - 8, DIAL_Y + DIAL_R + 3, sx + dx + 8, DIAL_Y + DIAL_R + 8, fill=col("concrete_cold", 0.10))
        for i, lx in enumerate(range(sx + 9, sx + 58, 10)):
            ramp_name, top = lamp_cols[int(rng.integers(0, len(lamp_cols)))]
            on = rng.random() < 0.5
            if on:
                ov.ellipse(lx - 3.5, LAMP_Y - 3.5, lx + 3.5, LAMP_Y + 3.5, fill=col(ramp_name, 0.7) + (90,))
            ov.ellipse(lx - 2.5, LAMP_Y - 2.5, lx + 2.5, LAMP_Y + 2.5, fill=col("concrete_cold", 0.12))
            ov.ellipse(lx - 1.6, LAMP_Y - 1.6, lx + 1.6, LAMP_Y + 1.6,
                       fill=col(ramp_name, top if on else 0.30))
            if on:
                ov.rect(lx - 0.5, LAMP_Y - 1, lx + 0.5, LAMP_Y, fill=(255, 255, 255))
        # mimic diagram on the desk: drops from the busbar to breakers
        for bx in range(sx + 8, sx + 60, 12):
            ov.rect(bx, BUS_Y, bx + 1, BUS_Y + 12, fill=col("plaster_warm", 0.92))
            closed = rng.random() < 0.6
            ov.rect(bx - 2, BUS_Y + 12, bx + 3, BUS_Y + 17, fill=col("military_green" if closed else "flag_red", 0.7))
            ov.rect(bx, BUS_Y + 17, bx + 1, BUS_Y + 22, fill=col("plaster_warm", 0.92))
        # toggle switches with their label plates
        for tx in range(sx + 7, sx + 60, 8):
            ov.ellipse(tx - 2, 101, tx + 2, 105, fill=col("steel_blue", 0.75))
            up = rng.random() < 0.5
            ov.rect(tx - 0.5, 96 if up else 103, tx + 1, 103 if up else 109, fill=col("concrete_cold", 0.05))
            ov.rect(tx - 3, 111, tx + 3, 115, fill=col("concrete_cold", 0.10))
    ov.rect(0, BUS_Y - 1, w, BUS_Y + 1, fill=col("hazard_yellow", 0.82))
    rgb = ov.composite(rgb)
    for sx in range(0, w, SECTION):
        for dx in DIAL_XS:
            ep2lib.illegible_label(rgb, sx + dx - 7, DIAL_Y + DIAL_R + 5, 14, col("plaster_warm", 0.90), rng)
        for tx in range(sx + 7, sx + 60, 8):
            ep2lib.illegible_label(rgb, tx - 2, 113, 5, col("plaster_warm", 0.85), rng)
        ep2lib.illegible_label(rgb, sx + 6, 58, 30, col("concrete_cold", 0.15), rng)
    kick = to_rgb(np.clip(0.12 + grain(w, h, rng, 0.02), 0, 1), "concrete_cold")
    rgb = np.where((yy >= DESK_Y1)[..., None], kick, rgb)
    rgb[DESK_Y1, :] = col("concrete_cold", 0.40)
    return rgb


# ================================================================ spillway rack
BAR_PITCH, BAR_W = 8, 3
STIFF_Y, STIFF_H = 28, 5     # a horizontal stiffener every 64 px from here
STIFF_PITCH = 64


def tex_spil1() -> np.ndarray:
    """Spillway trash rack: rusty vertical bars and stiffeners in front of
    rushing water, foam catching the light between the bars."""
    rng = rng_for(5)
    w, h = WALL_W, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    rush = fbm(w, h, 8, 4, rng, 0.55, aspect=10.0)
    foam = fbm(w, h, 16, 2, rng, aspect=6.0)
    water = to_rgb(np.clip(0.14 + rush * 0.35, 0, 1), "steel_blue")
    froth = (rush + foam * 0.5) > 1.02
    water = np.where(froth[..., None], to_rgb(np.clip(0.78 + foam * 0.2, 0, 1), "steel_blue"), water)
    lx = xx % BAR_PITCH
    bar = lx < BAR_W
    tone = np.choose(np.clip(lx, 0, 2), [0.50, 0.38, 0.22])
    steel = to_rgb(np.clip(tone + grain(w, h, rng, 0.02), 0, 1), "steel_blue")
    rust = to_rgb(np.clip(tone * 0.9 + grain(w, h, rng, 0.03), 0, 1), "rust_brown")
    rusty = fbm(w, h, 8, 3, rng, aspect=4.0) > 0.52
    bars = np.where(rusty[..., None], rust, steel)
    rgb = np.where(bar[..., None], bars, water)
    # bar shadow on the water
    rgb = np.where((lx == BAR_W)[..., None], shade(rgb, 0.5), rgb)
    sy = (yy - STIFF_Y) % STIFF_PITCH
    stiff = sy < STIFF_H
    st = to_rgb(np.clip(0.32 + grain(w, h, rng, 0.02), 0, 1), "steel_blue")
    st = np.where((sy == 0)[..., None], np.array(col("steel_blue", 0.62), np.uint8), st)
    st = np.where((sy == STIFF_H - 1)[..., None], np.array(col("steel_blue", 0.12), np.uint8), st)
    rgb = np.where(stiff[..., None], st, rgb)
    rgb = np.where((sy == STIFF_H)[..., None], shade(rgb, 0.45), rgb)
    for y0 in range(STIFF_Y, h, STIFF_PITCH):
        for x in range(0, w, BAR_PITCH):
            rivet(rgb, x, y0 + 1, "steel_blue", 0.42)
    return rgb


# ================================================================ water
WATER_TONE = (0.16, 0.40)    # steel_blue: Volga water, grey-blue, never cobalt
CREST_T = 0.90
DRIFT = FLAT // FRAMES       # px the field drifts per frame: one tile per loop


def water_frames() -> list[np.ndarray]:
    """Four frames of river water: a slow body, ripple ridges that turn
    through a full phase, the whole drifting 16 px a frame (64 px over the
    loop, so frame 4 leads back into frame 1)."""
    rng = rng_for(6)
    w = h = FLAT
    body = fbm(w, h, 3, 3, rng, 0.5)
    a, b = fbm(w, h, 4, 4, rng, 0.55), fbm(w, h, 4, 4, rng, 0.55)
    g = grain(w, h, rng, 0.015)
    frames = []
    for k in range(FRAMES):
        phi = 2 * np.pi * k / FRAMES
        rip = 0.5 + (a - 0.5) * np.cos(phi) + (b - 0.5) * np.sin(phi)
        ridge = 1 - np.abs(2 * rip - 1)
        t = WATER_TONE[0] + (WATER_TONE[1] - WATER_TONE[0]) * body + (ridge - 0.5) * 0.12 + g
        rgb = to_rgb(np.clip(t, 0, 1), "steel_blue")
        crest = ridge > CREST_T
        rgb = np.where(crest[..., None], np.array(col("steel_blue", 0.74), np.uint8), rgb)
        rgb = np.where((ridge > CREST_T + 0.07)[..., None], np.array(col("steel_blue", 0.92), np.uint8), rgb)
        frames.append(np.roll(rgb, (k * DRIFT, k * DRIFT // 2), axis=(0, 1)))
    return frames


# ================================================================ insulator
ARM_H = 8                    # the steel crossarm along the top
DISC_N, DISC_PITCH, DISC_Y0 = 8, 10, 18
DISC_RX, DISC_RY = 13, 3.4
CABLE_Y = 108


def insulator_rgba() -> np.ndarray:
    """High-voltage suspension string, MASKED: crossarm, clevis, eight
    brown glazed porcelain discs, the clamp and the conductor. Crossarm
    and conductor run off both sides, so a row of strings tiles in x."""
    rng = rng_for(7)
    w, h = WALL_W, WALL_H
    ov = Overlay(w, h)
    ov.rect(0, 0, w, ARM_H, fill=col("steel_blue", 0.30))
    ov.rect(0, 0, w, 1, fill=col("steel_blue", 0.62))
    ov.rect(0, ARM_H - 1, w, ARM_H, fill=col("steel_blue", 0.10))
    for x in range(4, w, 8):
        ov.rect(x, 3, x + 2, 5, fill=col("steel_blue", 0.55))
    ov.rect(29, ARM_H, 35, DISC_Y0 - 2, fill=col("steel_blue", 0.40))
    ov.rect(29, ARM_H, 30, DISC_Y0 - 2, fill=col("steel_blue", 0.65))
    cx = 32
    for i in range(DISC_N):
        cy = DISC_Y0 + i * DISC_PITCH
        ov.rect(cx - 2, cy - 4, cx + 2, cy + 1, fill=col("steel_blue", 0.45))
        ov.ellipse(cx - DISC_RX, cy - DISC_RY + 1, cx + DISC_RX, cy + DISC_RY + 3, fill=col("rust_brown", 0.18))
        ov.ellipse(cx - DISC_RX, cy - DISC_RY, cx + DISC_RX, cy + DISC_RY, fill=col("rust_brown", 0.52))
        ov.ellipse(cx - DISC_RX + 2, cy - DISC_RY, cx + DISC_RX - 4, cy + 0.5, fill=col("rust_brown", 0.72))
        ov.ellipse(cx - 6, cy - DISC_RY + 0.3, cx - 1, cy - 1.2, fill=col("cream_yellow", 0.85))
    yb = DISC_Y0 + DISC_N * DISC_PITCH - 4
    ov.rect(cx - 2, yb, cx + 2, CABLE_Y - 3, fill=col("steel_blue", 0.45))
    ov.rect(cx - 6, CABLE_Y - 4, cx + 6, CABLE_Y + 6, fill=col("steel_blue", 0.35))
    ov.rect(cx - 6, CABLE_Y - 4, cx + 6, CABLE_Y - 3, fill=col("steel_blue", 0.70))
    ov.rect(0, CABLE_Y, w, CABLE_Y + 4, fill=col("steel_blue", 0.40))
    ov.rect(0, CABLE_Y, w, CABLE_Y + 1, fill=col("steel_blue", 0.80))
    ov.rect(0, CABLE_Y + 3, w, CABLE_Y + 4, fill=col("steel_blue", 0.15))
    # Pillow box-filters RGBA with premultiplied alpha, so edge pixels keep
    # their own colour instead of fading to black
    small = np.asarray(ov.img.resize((w, h), Image.Resampling.BOX), dtype=np.uint8).copy()
    out = np.dstack([small[..., :3], np.where(small[..., 3] >= ep2lib.ALPHA_CUT, 255, 0).astype(np.uint8)])
    # strand lay on the conductor: a dither of lighter pixels
    for x in range(0, w, 3):
        out[CABLE_Y + 2, x, :3] = col("steel_blue", 0.60)
    out[..., :3] = np.where(out[..., 3:4] > 0, shade(out[..., :3], 1 + grain(w, h, rng, 0.03)), 0)
    return out


def tex_insl1() -> np.ndarray:
    return insulator_rgba()


# ================================================================ mesh floor
MESH_P = (16, 8)             # diamond lattice period (x, y)
MESH_OPEN = (6.2, 2.6)       # half-diagonals of an opening


def tex_grat2() -> np.ndarray:
    """Galvanised expanded-metal mesh floor over the dark (water glints far
    below), a few rust patches. No frame: it tiles seamlessly, unlike the
    factory's SDGRAT1 panels."""
    rng = rng_for(8)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w] + 0.5
    px, py = MESH_P
    best = np.full((h, w), 9.0)
    for cx0, cy0 in ((0, 0), (px / 2, py / 2)):
        dx = np.abs(ep2lib.wrap_dist(xx - cx0, px))
        dy = np.abs(ep2lib.wrap_dist(yy - cy0, py))
        best = np.minimum(best, dx / MESH_OPEN[0] + dy / MESH_OPEN[1])
    hole = best < 1.0
    below = to_rgb(np.clip(0.06 + (fbm(w, h, 4, 3, rng) > 0.68) * 0.18 + grain(w, h, rng, 0.02), 0, 1), "steel_blue")
    field = 0.58 + (fbm(w, h, 4, 3, rng) - 0.5) * 0.12 + grain(w, h, rng, 0.03)
    metal = to_rgb(np.clip(field, 0, 1), "steel_blue")
    rust = to_rgb(np.clip(field * 0.75, 0, 1), "rust_brown")
    metal = np.where((fbm(w, h, 6, 3, rng) > 0.72)[..., None], rust, metal)
    # the strand's upper edge (just below a hole) catches the light
    lit = ~hole & np.roll(hole, 1, axis=0)
    dark = ~hole & np.roll(hole, -1, axis=0)
    f = np.ones((h, w))
    f[lit] = 1.25
    f[dark] = 0.62
    metal = shade(metal, f)
    return np.where(hole[..., None], below, metal)


# ================================================================ pieces
PIECES = [
    Piece("SDDAM1", tex_dam1, "wall", (64, 128), ["SDDAM1"], 1, "xy",
          "Dam concrete",
          "The dam's mass concrete: formwork board marks, a lift joint every 64 px, form-tie holes with white "
          "calcite streaks.",
          rec_why="The map's canvas: light, cold, huge; the streaks give scale without dirtying it."),
    Piece("SDDAM2", tex_dam2, "wall", (64, 128), ["SDDAM2"], 2, "x",
          "Concrete at the waterline",
          "The same concrete at the waterline: dark and wet below an uneven mark, green algae at the bottom.",
          rec_why="For the spillway channel and the reservoir walls; the mark sits 72 px below the texture's top "
                  "(align in UDMF)."),
    Piece("SDTURB1", tex_turb1, "wall", (128, 128), ["SDTURB1"], 3, "x",
          "Turbine / generator casing",
          "The turbine-generator set's casing: steel painted 4BO green, ribs, two bolted flanges, a brass maker's "
          "plate (unreadable pixel text and the year 1957), a bolted inspection hatch, oil seeping under the "
          "flange, a concrete plinth.",
          rec_why="Palette v1 has no machinery «grey-green»: I use the doors' 4BO green, which also ties in with "
                  "the base. A true grey-green needs palette v3 (question below)."),
    Piece("SDCTRL1", tex_ctrl1, "wall", (128, 128), ["SDCTRL1"], 4, "x",
          "Control panel",
          "A Soviet control board: light grey panels, round gauges with a red zone, a row of pilot lamps (some "
          "lit), plates that look like text and say nothing, a mimic diagram of busbars and switches on the "
          "desk, lever switches and a dark plinth. 64 px sections: it tiles as one long board.",
          rec_why="The most «Doom» piece of the set (the 1993 computer panels) yet unmistakably Soviet."),
    Piece("SDSPIL1", tex_spil1, "wall", (64, 128), ["SDSPIL1"], 5, "xy",
          "Spillway grille",
          "The spillway's trash rack: rusty vertical bars and stiffeners in front of running water, with foam "
          "between the bars.",
          rec_why="Tiles on both axes; in front of an animated water sector it sells the dam."),
    Piece("SDWATR", water_frames, "flat", (64, 64), [f"SDWATR{i}" for i in range(1, FRAMES + 1)], 6, "xy",
          "Volga water (animated, 4 frames)",
          "River water in four frames for ANIMDEFS, like Doom's water: a slow body, crests that turn one full "
          "phase and a drift of one tile per loop (frame 4 links back to 1). steel_blue grey-blue, never the "
          "portal's cobalt.",
          rec_why="8 tics per frame like SDMOLT (mod-engineer's decision). It reads as water, not as a portal."),
    Piece("SDINSL1", tex_insl1, "wall", (64, 128), ["SDINSL1"], 7, "x",
          "High-voltage insulator (masked)",
          "A suspension insulator string, MASKED (transparent background, for the middle texture of a two-sided "
          "line): crossarm, clevis, eight glazed brown porcelain discs, clamp and conductor. Crossarm and cable "
          "cross the tile: a row of strings tiles in x.",
          masked=True,
          rec_why="Same RGBA exception as SDCHAN1 (approved and installed). Against the sky or the substation's "
                  "wall.",
          scene={"left": "SDDAM1", "right": "SDDAM1", "ceil": None}),
    Piece("SDGRAT2", tex_grat2, "flat", (64, 64), ["SDGRAT2"], 8, "xy",
          "Expanded-metal floor",
          "Galvanised expanded metal over a drop (glints of water below), a patch of rust here and there. No "
          "frame: it tiles seamlessly, unlike the factory's SDGRAT1 panels.",
          rec_why="Walkways over the turbines and the spillway; tells from SDGRAT1 at a glance (diamonds, not bars)."),
]

ROOM = {"wall": "SDDAM1", "floor": "SDGRAT2", "ceil": "SDCEIL1", "light": 0.92}
OVERVIEWS = [
    ("Turbine hall", {"left": "SDTURB1", "right": "SDCTRL1", "back": "SDTURB1", "floor": "SDGRAT2",
                          "ceil": "SDCEIL1"}),
    ("The spillway", {"left": "SDDAM2", "right": "SDDAM2", "back": "SDSPIL1", "floor": "SDWATR1", "ceil": None}),
]


def build(out_dir: Path | None = None):
    return ep2lib.build_set(SET_NAME, PIECES, BATCH_SEED, SCRIPT_REL, out_dir)


def main() -> None:
    entries, _ = build()
    for e in entries:
        print(f'{e["piece"]:8s} {e["width"]:3d}x{e["height"]:3d} v{e["palette_version"]} '
              f'colours={e["colours_used"]:3d} luma={e["mean_luma"]:6.1f} seam={e["seam_score"]}')


if __name__ == "__main__":
    main()
