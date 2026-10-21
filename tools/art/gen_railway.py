"""Episode 2, MAP04 — the railway set: the Sverdlovsk marshalling yard, 1977 (D104, P4).

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_railway.py
                            (macOS: .venv/bin/python tools/art/gen_railway.py)
The whole episode and the CEO's sheet: tools/art/gen_episode2.py.

DRAFTS for the CEO: the PNGs go to work/art/episode2/railway/, never to
assets/. Method and palette rule: tools/art/ep2lib.py (v1; v2 only for the
fired-clay brick, as SDBRCK1 was approved, D66). No system font: the wagon
number is drawn with our 3x5 pixel digits, the tank car's «НЕФТЬ» and the
warehouse's «СКЛАД» come from our own alphabet (bigfont, D24).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import Overlay, fbm, grain, shade, star_points, to_rgb  # noqa: E402
import ep2lib  # noqa: E402
from ep2lib import Piece, bevel, col, rivet  # noqa: E402
import gen_factory  # noqa: E402  (the approved brick recipe)

SET_NAME = "railway"
SCRIPT_REL = "tools/art/gen_railway.py"
# Own seed space: 5400 for MAP04 (Episode 2 uses 5400/5500/5600, clear of
# 1935+, 1977+, 2077+, 3077+ and 4100+).
BATCH_SEED = 5400
WALL_W, WALL_H, WIDE, FLAT = 64, 128, 128, 64


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


# ================================================================ ballast
STONE_CELL = 4               # one crushed stone per ~4 px
BALLAST_TONE = 0.40          # concrete_cold: grey granite chippings
BALLAST_WARM = 0.22          # share of warmer (plaster_warm) stones
RUST_DUST = 0.55             # fbm above this: rust and oil dust from the wagons


def ballast(w: int, h: int, rng: np.random.Generator, tone: float = BALLAST_TONE) -> np.ndarray:
    f1, f2, ident, ox, oy = ep2lib.cells_voronoi(w, h, STONE_CELL, rng, 0.95)
    n = ident.max() + 1
    jitter = rng.uniform(-0.12, 0.12, n)
    warm = rng.random(n) < BALLAST_WARM
    edge = np.clip((f2 - f1) / 1.6, 0, 1)
    facet = 1 + 0.30 * np.clip(-oy / 2.5, -1, 1) + 0.10 * np.clip(-ox / 2.5, -1, 1)
    field = np.clip(tone + jitter[ident] + grain(w, h, rng, 0.03), 0, 1)
    rgb = np.where(warm[ident][..., None], to_rgb(field * 0.95, "plaster_warm"), to_rgb(field, "concrete_cold"))
    rgb = shade(rgb, facet * (0.35 + 0.65 * edge))
    dust = np.clip((fbm(w, h, 4, 3, rng) - RUST_DUST) * 2.4, 0, 0.55)
    rust = to_rgb(np.clip(field * 0.8, 0, 1), "rust_brown")
    rgb = (rgb * (1 - dust[..., None]) + rust * dust[..., None]).astype(np.uint8)
    return rgb


def tex_blst1() -> np.ndarray:
    """Plain track ballast: crushed granite, rust and oil dust."""
    return ballast(FLAT, FLAT, rng_for(1))


# ================================================================ track
SLEEPER_PITCH = 16           # one sleeper per 16 px along y (4 per flat)
SLEEPER_W = 7                # its width along y
SLEEPER_X = (3, 61)          # its ends: ballast shows at the tile edges, so tracks tile side by side
SLEEPER_TONE = 0.56          # concrete_cold: Soviet prestressed concrete sleepers
RAILS_X = (12, 49)           # left column of each 4 px rail
RAIL_W = 4
TIE_PLATE = 2                # tie plate overhang beyond the rail foot
OIL_TONE = 0.35              # how much the four-foot (between the rails) is darkened by drips


def tex_trak1() -> np.ndarray:
    """Yard track from above: ballast, concrete sleepers, tie plates and
    clips, two rails with a polished head and rusty sides. The rails run
    along y; side by side the tiles make parallel tracks."""
    rng = rng_for(2)
    w = h = FLAT
    rgb = ballast(w, h, rng)
    yy, xx = np.mgrid[0:h, 0:w]
    # oil and grease between the rails
    four_foot = (xx > RAILS_X[0] + RAIL_W) & (xx < RAILS_X[1])
    oil = np.clip(fbm(w, h, 4, 3, rng, aspect=3.0) - 0.35, 0, 1) * OIL_TONE * 2
    rgb = np.where(four_foot[..., None], shade(rgb, 1 - oil), rgb)
    # sleepers
    ly = yy % SLEEPER_PITCH
    sleeper = (ly < SLEEPER_W) & (xx >= SLEEPER_X[0]) & (xx < SLEEPER_X[1])
    # ballast heaped over the sleeper ends in places
    heap = fbm(w, h, 8, 2, rng) > 0.62
    end_zone = (xx < SLEEPER_X[0] + 5) | (xx >= SLEEPER_X[1] - 5)
    sleeper &= ~(heap & end_zone)
    sfield = SLEEPER_TONE + (fbm(w, h, 8, 3, rng) - 0.5) * 0.12 + grain(w, h, rng, 0.03)
    srgb = to_rgb(np.clip(sfield, 0, 1), "concrete_cold")
    f = np.ones((h, w))
    f[ly == 0] = 1.20
    f[ly == SLEEPER_W - 1] = 0.70
    srgb = shade(srgb, f)
    rgb = np.where(sleeper[..., None], srgb, rgb)
    # shadow of each sleeper on the ballast
    sh = (ly == SLEEPER_W) & (xx >= SLEEPER_X[0]) & (xx < SLEEPER_X[1])
    rgb = np.where(sh[..., None], shade(rgb, 0.55), rgb)
    # tie plates and clips on every sleeper, then the rails over them
    plate = col("steel_blue", 0.18)
    clip = col("steel_blue", 0.40)
    for x0 in RAILS_X:
        for s in range(0, h, SLEEPER_PITCH):
            rgb[s + 1:s + SLEEPER_W - 1, x0 - TIE_PLATE:x0 + RAIL_W + TIE_PLATE] = plate
            for cx in (x0 - TIE_PLATE, x0 + RAIL_W + TIE_PLATE - 1):
                rgb[s + 2:s + 5, cx] = clip
                rgb[s + 2, cx] = col("steel_blue", 0.62)
        # the rail: foot shadow, rusty web, polished head
        rgb[:, x0 - 1] = shade(rgb[:, x0 - 1], 0.55)
        rgb[:, x0 + RAIL_W] = shade(rgb[:, x0 + RAIL_W], 0.45)
        rust = np.clip(0.38 + (fbm(1, h, 1, 1, rng)[:, 0] - 0.5) * 0.2, 0, 1)
        for y in range(h):
            rgb[y, x0] = col("rust_brown", rust[y])
            rgb[y, x0 + RAIL_W - 1] = col("rust_brown", rust[y] * 0.75)
            rgb[y, x0 + 1] = col("steel_blue", 0.86 if (y + x0) % 9 else 0.95)
            rgb[y, x0 + 2] = col("steel_blue", 0.72)
    return rgb


# ================================================================ boxcar
PLANK_H = 6
BOX_TOP = 6                  # top chord (steel angle) rows 0..5
BOX_BOTTOM = 104             # sole bar from here
SOLE_H = 8
POST_PITCH = 32              # vertical steel posts every 32 px
POST_W = 4
OXIDE_TONE = 0.50            # rust_brown: red-oxide paint ("сурик")
NUMBER = "24180637"          # an 8-digit MPS wagon number, invented
WEAR_T = 0.74                # fbm above this: paint worn to grey wood


def tex_wagn1() -> np.ndarray:
    """Soviet covered goods wagon, side: red-oxide planking on a steel
    frame, posts and braces, sole bar, the dark under-frame, a stencilled
    eight-digit number."""
    rng = rng_for(3)
    w, h = WIDE, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    plank = (yy - BOX_TOP) // PLANK_H
    n = (BOX_BOTTOM - BOX_TOP) // PLANK_H + 2
    ptone = OXIDE_TONE + rng.uniform(-0.05, 0.05, n)
    grain_f = fbm(w, h, 16, 3, rng, 0.5, aspect=0.2)
    field = ptone[np.clip(plank, 0, n - 1)] + (grain_f - 0.5) * 0.14 + grain(w, h, rng, 0.025)
    rgb = to_rgb(np.clip(field, 0, 1), "rust_brown")
    wear = fbm(w, h, 6, 4, rng) > WEAR_T
    wood = to_rgb(np.clip(0.42 + (grain_f - 0.5) * 0.3, 0, 1), "plaster_warm")
    rgb = np.where(wear[..., None], wood, rgb)
    f = np.ones((h, w))
    gap = ((yy - BOX_TOP) % PLANK_H == 0)
    f[gap] = 0.45
    f[(yy - BOX_TOP) % PLANK_H == 1] *= 1.10
    # rain streaks down the planks
    f *= 1 - np.clip(fbm(w, h, 12, 2, rng, aspect=8.0) - 0.55, 0, 1) * 0.6
    rgb = shade(rgb, f)
    # braces in the right half (two panels), drawn as steel straps
    ov = Overlay(w, h)
    steel = col("rust_brown", 0.32)
    steel_hi = col("rust_brown", 0.55)
    for x0, flip in ((64, False), (96, True)):
        a, b = (x0 + 3, BOX_BOTTOM - 2), (x0 + POST_PITCH - 3, BOX_TOP + 2)
        if flip:
            a, b = (x0 + 3, BOX_TOP + 2), (x0 + POST_PITCH - 3, BOX_BOTTOM - 2)
        ov.line([a, b], steel, 3.2)
        ov.line([(a[0], a[1] - 1), (b[0], b[1] - 1)], steel_hi, 1.0)
    rgb = ov.composite(rgb)
    # posts (wrap at the tile edge), top chord, sole bar
    for px in range(0, w, POST_PITCH):
        for k in range(POST_W):
            x = (px - POST_W // 2 + k) % w
            tone = (0.62, 0.48, 0.40, 0.24)[k]
            rgb[BOX_TOP:BOX_BOTTOM, x] = col("rust_brown", tone)
        for y in range(BOX_TOP + 4, BOX_BOTTOM - 2, 8):
            rivet(rgb, (px - 1) % w, y, "rust_brown", 0.42)
    rgb[0:BOX_TOP] = col("rust_brown", 0.36)
    rgb[0, :] = col("concrete_cold", 0.04)
    rgb[1, :] = col("rust_brown", 0.60)
    rgb[BOX_TOP - 1, :] = col("rust_brown", 0.18)
    rgb[BOX_BOTTOM:BOX_BOTTOM + SOLE_H] = col("rust_brown", 0.30)
    rgb[BOX_BOTTOM, :] = col("rust_brown", 0.55)
    rgb[BOX_BOTTOM + SOLE_H - 1, :] = col("rust_brown", 0.14)
    for x in range(4, w, 8):
        rivet(rgb, x, BOX_BOTTOM + 3, "rust_brown", 0.36)
    # under-frame: dark, a brake pipe, a hint of the bogie spring
    under = to_rgb(np.clip(0.06 + fbm(w, h, 8, 2, rng) * 0.06, 0, 1), "concrete_cold")
    low = yy >= BOX_BOTTOM + SOLE_H
    rgb = np.where(low[..., None], under, rgb)
    rgb[BOX_BOTTOM + SOLE_H + 4, :] = col("steel_blue", 0.22)
    rgb[BOX_BOTTOM + SOLE_H + 5, :] = col("steel_blue", 0.10)
    # the stencil: 8 digits, 3x5 at 2x, cream, a little worn
    m = ep2lib.digits_mask(NUMBER)
    m = np.repeat(np.repeat(m, 2, 0), 2, 1)
    worn = rng.random(m.shape) < 0.10
    y0, x0 = 66, 2 + (60 - m.shape[1]) // 2 + 1
    region = rgb[y0:y0 + m.shape[0], x0:x0 + m.shape[1]]
    region[m & ~worn] = col("plaster_warm", 0.86)
    # the small stencil block above it: capacity and tare, illegible at 4x
    ep2lib.illegible_label(rgb, 8, 50, 22, col("plaster_warm", 0.78), rng, rows=3)
    return rgb


# ================================================================ tank wagon
BARREL_TOP, BARREL_BOT = 2, 100
SHELL_TONE = (0.04, 0.34)     # concrete_cold: black paint, shadow to light
SPEC_TONE = 0.62
RING_SEAMS = (32, 96)         # riveted ring seams of the shell
STRAPS = (14, 114)            # the anchor straps around the barrel
WORD = "НЕФТЬ"                # "oil", stencilled on Soviet tank wagons


def tex_tank1() -> np.ndarray:
    """Soviet four-axle tank wagon, side: a black cylinder lit from above,
    riveted ring seams, anchor straps, oil run down from the dome, the word
    «НЕФТЬ» (oil) in cream from our alphabet, the frame and the shadow
    beneath."""
    rng = rng_for(4)
    w, h = WIDE, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    r = (BARREL_BOT - BARREL_TOP) / 2
    cy = BARREL_TOP + r
    s = np.clip((yy + 0.5 - cy) / r, -1, 1)
    theta = np.arcsin(s)
    light = np.clip(np.cos(theta + np.deg2rad(35)), 0, 1)
    spec = np.clip(np.cos(theta + np.deg2rad(52)), 0, 1) ** 24
    field = SHELL_TONE[0] + (SHELL_TONE[1] - SHELL_TONE[0]) * light
    field += (fbm(w, h, 8, 3, rng) - 0.5) * 0.06 + grain(w, h, rng, 0.02)
    field = np.maximum(field, spec * SPEC_TONE)
    # oil run: glossy darker streaks from the top, densest under the dome (x=64)
    runs = np.clip(fbm(w, h, 16, 2, rng, aspect=10.0) - 0.52, 0, 1) * 2.0
    near_dome = np.exp(-((xx - 64) / 30.0) ** 2)
    field *= 1 - np.clip(runs * (0.4 + 0.6 * near_dome), 0, 0.6)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    # ring seams: a 2 px rib with rivets every 6 px
    for sx in RING_SEAMS:
        rib_l = shade(rgb[:, sx], 1.6)
        rib_r = shade(rgb[:, sx + 1], 0.5)
        rgb[BARREL_TOP:BARREL_BOT, sx] = rib_l[BARREL_TOP:BARREL_BOT]
        rgb[BARREL_TOP:BARREL_BOT, sx + 1] = rib_r[BARREL_TOP:BARREL_BOT]
        for y in range(BARREL_TOP + 4, BARREL_BOT - 3, 6):
            rgb[y, sx - 2] = col("concrete_cold", min(1, field[y, sx] + 0.25))
            rgb[y, sx + 3] = col("concrete_cold", min(1, field[y, sx] + 0.18))
    # anchor straps
    for sx in STRAPS:
        for k, t in enumerate((0.30, 0.18, 0.08)):
            rgb[BARREL_TOP + 40:BARREL_BOT, sx + k] = col("steel_blue", t)
    # the word, cream, slightly worn
    body, shadow = ep2lib.glyph_masks(WORD)
    worn = rng.random(body.shape) < 0.08
    canvas = rgb.copy()
    ep2lib.paste_mask(canvas, body & ~worn, col("plaster_warm", 0.84), 64, 50)
    rgb = canvas
    # frame: sole bar and shadow
    rgb[BARREL_BOT:BARREL_BOT + 2] = col("concrete_cold", 0.02)
    rgb[BARREL_BOT + 2:BARREL_BOT + 10] = col("steel_blue", 0.20)
    rgb[BARREL_BOT + 2, :] = col("steel_blue", 0.45)
    for x in range(4, w, 8):
        rivet(rgb, x, BARREL_BOT + 5, "steel_blue", 0.30)
    under = to_rgb(np.clip(0.05 + fbm(w, h, 8, 2, rng) * 0.05, 0, 1), "concrete_cold")
    rgb = np.where((yy >= BARREL_BOT + 10)[..., None], under, rgb)
    rgb[BARREL_BOT + 15, :] = col("steel_blue", 0.22)
    rgb[0:BARREL_TOP] = col("concrete_cold", 0.03)
    return rgb


# ================================================================ armoured train
PLATE = 64                   # armour plates 64x64
ARMOUR_TONE = 0.46           # military_green
FADE_T = 0.68                # fbm above this: sun-faded to khaki
RIVET_STEP = 8
STAR_C, STAR_R = (64, 62), 30


def armour(w: int, h: int, rng: np.random.Generator) -> np.ndarray:
    yy, xx = np.mgrid[0:h, 0:w]
    px, py = xx // PLATE, yy // PLATE
    n = rng.uniform(-0.04, 0.04, (h // PLATE + 1, w // PLATE + 1))
    lx, ly = xx % PLATE, yy % PLATE
    bulge = 1 + 0.06 * np.cos(np.pi * (ly - PLATE / 2) / PLATE) - 0.03
    field = ARMOUR_TONE + n[py, px] + (fbm(w, h, 6, 4, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.025)
    green = to_rgb(np.clip(field, 0, 1), "military_green")
    khaki = to_rgb(np.clip(field + 0.02, 0, 1), "khaki_olive")
    fade = fbm(w, h, 4, 3, rng) > FADE_T
    rgb = np.where(fade[..., None], khaki, green)
    f = bulge.copy()
    f[ly == 0] *= 1.30
    f[ly == 1] *= 1.10
    f[ly == PLATE - 1] *= 0.50
    f[lx == 0] *= 1.20
    f[lx == PLATE - 1] *= 0.55
    rgb = shade(rgb, f)
    # rivets along every seam, both sides
    for y0 in range(0, h, PLATE):
        for x in range(4, w, RIVET_STEP):
            rivet(rgb, x, y0 + 3, "military_green", 0.50)
            rivet(rgb, x, y0 + PLATE - 6, "military_green", 0.50)
    for x0 in range(0, w, PLATE):
        for y in range(12, h, RIVET_STEP * 2):
            for yy0 in (y,):
                if (yy0 % PLATE) < 9 or (yy0 % PLATE) > PLATE - 10:
                    continue
                rivet(rgb, x0 + 3, yy0, "military_green", 0.50)
                rivet(rgb, x0 + PLATE - 6, yy0, "military_green", 0.50)
    # battle: bright scrapes and bullet splashes, rust under some rivets
    ov = Overlay(w, h)
    for _ in range(3):
        x0, y0 = rng.uniform(0, w), rng.uniform(0, h)
        ang, ln = rng.uniform(-0.4, 0.4), rng.uniform(8, 18)
        ov.line_tiled([(x0, y0), (x0 + ln * np.cos(ang), y0 + ln * np.sin(ang))], col("steel_blue", 0.70) + (200,), 1.0)
    rgb = ov.composite(rgb)
    for _ in range(5):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        rgb[y % h, x % w] = col("concrete_cold", 0.05)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rgb[(y + dy) % h, (x + dx) % w] = col("steel_blue", 0.62)
    streak = np.clip(fbm(w, h, 16, 2, rng, aspect=8.0) - 0.62, 0, 1) * 1.6
    rust = to_rgb(np.clip(0.35 + grain(w, h, rng, 0.03), 0, 1), "rust_brown")
    rgb = (rgb * (1 - streak[..., None]) + rust * streak[..., None]).astype(np.uint8)
    return rgb


def tex_armr1() -> np.ndarray:
    """Armoured-train plate, olive, riveted, with the red star."""
    rng = rng_for(5)
    w, h = WIDE, WALL_H
    rgb = armour(w, h, rng)
    ov = Overlay(w, h)
    g = ov.group(outline=col("flag_red", 0.12), outline_width=1.0)
    g.polygon(star_points(STAR_C[0], STAR_C[1], STAR_R + 2), col("plaster_warm", 0.80))
    ov.end_group(g)
    ov.polygon(star_points(STAR_C[0], STAR_C[1], STAR_R - 1), col("flag_red", 0.68))
    # the lit facet of each arm: half of every point a step brighter
    pts = star_points(STAR_C[0], STAR_C[1], STAR_R - 1)
    for i in range(0, 10, 2):
        tip, inner = pts[i], pts[(i + 1) % 10]
        ov.polygon([STAR_C, tip, inner], col("flag_red", 0.80))
    rgb = ov.composite(rgb)
    # the paint is chipped: a few olive pixels show through the red
    chip = (fbm(w, h, 16, 2, rng) > 0.74) & (rng.random((h, w)) < 0.5)
    olive = armour(w, h, rng_for(5))
    rgb = np.where(chip[..., None], olive, rgb)
    return rgb


def tex_armr2() -> np.ndarray:
    """The same plating without the star: the filler between star panels.
    Rolled half a plate so the vertical plate joint falls inside the tile:
    beside SDARMR1 the joints then alternate instead of doubling up."""
    return np.roll(armour(WALL_W, WALL_H, rng_for(6)), WALL_W // 2, axis=1)


# ================================================================ signal
PLATE_BOX = (10, 8, 54, 98)  # the black target plate
LENS_YS = (26, 52, 78)
LENS_R = 8
LIT = 2                      # index of the lit lens: red (stop)
LENS_RAMPS = (("military_green", 1.0), ("hazard_yellow", 0.95), ("flag_red", 1.0))
SIGNAL_NAME = "М2"           # the designation plate: М for a shunting signal (our alphabet)


def tex_sigl1() -> np.ndarray:
    """Colour-light signal on its mast, against a concrete pillar: black
    target plate, three lenses under hoods (green, yellow, red; the red is
    lit), the designation plate «М2» below."""
    rng = rng_for(7)
    w, h = WALL_W, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    conc = to_rgb(np.clip(0.50 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.14 + grain(w, h, rng, 0.03), 0, 1), "concrete_cold")
    rgb = conc
    # mast, behind the plate
    mast = (xx >= 27) & (xx < 37)
    mast_rgb = np.zeros_like(rgb)
    for k in range(10):
        mast_rgb[:, 27 + k] = col("steel_blue", (0.50, 0.46, 0.42, 0.38, 0.34, 0.30, 0.26, 0.22, 0.18, 0.12)[k])
    rgb = np.where(mast[..., None], mast_rgb, rgb)
    rgb[:, 26] = shade(rgb[:, 26], 0.6)
    rgb[:, 37] = shade(rgb[:, 37], 0.5)
    ov = Overlay(w, h)
    x0, y0, x1, y1 = PLATE_BOX
    ov.rect(x0 + 1, y0 + 1, x1 + 1, y1 + 1, fill=col("concrete_cold", 0.08) + (160,))
    ov.rect(x0, y0, x1, y1, fill=col("concrete_cold", 0.07))
    ov.rect(x0, y0, x1, y0 + 1, fill=col("concrete_cold", 0.30))
    for i, ly in enumerate(LENS_YS):
        ramp_name, top = LENS_RAMPS[i]
        if i == LIT:
            ov.ellipse(32 - LENS_R - 5, ly - LENS_R - 5, 32 + LENS_R + 5, ly + LENS_R + 5,
                       fill=col("flag_red", 0.45) + (110,))
        ov.ellipse(32 - LENS_R - 2, ly - LENS_R - 2, 32 + LENS_R + 2, ly + LENS_R + 2, fill=col("concrete_cold", 0.20))
        if i == LIT:
            ov.ellipse(32 - LENS_R, ly - LENS_R, 32 + LENS_R, ly + LENS_R, fill=col(ramp_name, top))
            ov.ellipse(32 - 4, ly - 4, 32 + 4, ly + 4, fill=col("cream_yellow", 1.0))
            ov.ellipse(32 - 2, ly - 2, 32 + 2, ly + 2, fill=(255, 255, 255))
        else:
            ov.ellipse(32 - LENS_R, ly - LENS_R, 32 + LENS_R, ly + LENS_R, fill=col(ramp_name, 0.20))
            ov.ellipse(32 - LENS_R + 2, ly - LENS_R + 2, 32 - 1, ly - 1, fill=col(ramp_name, 0.42))
        # hood: a dark visor over the top half
        ov.arc_ring(32, ly, LENS_R + 4, LENS_R + 1, 190, 350, col("concrete_cold", 0.12))
        ov.arc_ring(32, ly, LENS_R + 4, LENS_R + 3, 200, 340, col("concrete_cold", 0.30))
    # the designation plate: white, black letters
    ov.rect(20, 103, 44, 119, fill=col("concrete_cold", 0.05))
    ov.rect(21, 104, 43, 118, fill=col("plaster_warm", 0.92))
    rgb = ov.composite(rgb)
    body, shadow = ep2lib.glyph_masks(SIGNAL_NAME)
    ep2lib.paste_mask(rgb, body, col("concrete_cold", 0.04), 32, 111)
    # grime on the concrete under the plate
    return rgb


# ================================================================ roundhouse brick
FRIEZE = ((0, 8, "course"), (8, 16, "saw"), (16, 24, "course"))
RH_BRIGHTEN = 1.08           # the roundhouse brick is a little lighter than the works'


def tex_brck3() -> np.ndarray:
    """Roundhouse brick: the approved factory brick recipe (lighter, less
    soot) with a decorative frieze on top: a projecting course, a
    sawtooth course (bricks laid corner-out), another projecting course."""
    rng = rng_for(8)
    w, h = WALL_W, WALL_H
    rgb = shade(gen_factory.brick_field(w, h, rng, 0.20), RH_BRIGHTEN)
    yy, xx = np.mgrid[0:h, 0:w]
    f = np.ones((h, w))
    for y0, y1, kind in FRIEZE:
        band = (yy >= y0) & (yy < y1)
        if kind == "course":
            f[band] *= 1.10
            f[y1 - 1, :] *= 0.80
            f[y1, :] *= 0.55
        else:
            lx, ly = xx % 8, yy - y0
            tooth = band & (ly < 8 - np.abs(lx - 3.5) * 2)
            f[band & ~tooth] *= 0.40
            f[tooth & (lx < 4)] *= 1.18
            f[tooth & (lx >= 4)] *= 0.72
    return shade(rgb, f)


# ================================================================ warehouse door
DOOR_X0, DOOR_X1 = 4, 124
DOOR_Y0, DOOR_Y1 = 12, 124
LEDGES = ((22, 28), (104, 110))
WOOD_PAINT = 0.40            # rust_brown: old red-brown paint
DOOR_WORD = "СКЛАД"          # "warehouse"
DOOR_NUMBER = "3"


def tex_gate2() -> np.ndarray:
    """Goods-shed sliding door: planks under old red-brown paint flaking to
    grey wood, two ledges and a brace, a steel edge, the hanging rail with
    two rollers, hasp and padlock, a white plate «СКЛАД» and a big painted 3."""
    rng = rng_for(9)
    w, h = WIDE, WALL_H
    yy, xx = np.mgrid[0:h, 0:w]
    gr = fbm(w, h, 4, 3, rng, 0.5, aspect=6.0)
    wall = to_rgb(np.clip(0.32 + (fbm(w, h, 4, 3, rng) - 0.5) * 0.1, 0, 1), "concrete_cold")
    plank = xx // 8
    ptone = WOOD_PAINT + rng.uniform(-0.05, 0.05, w // 8 + 1)
    field = ptone[plank] + (gr - 0.5) * 0.16 + grain(w, h, rng, 0.025)
    paint = to_rgb(np.clip(field, 0, 1), "rust_brown")
    wood = to_rgb(np.clip(0.50 + (gr - 0.5) * 0.3, 0, 1), "plaster_warm")
    flake = fbm(w, h, 8, 3, rng) > 0.71
    leaf_rgb = np.where(flake[..., None], wood, paint)
    f = np.ones((h, w))
    f[:, ::8] = 0.45
    f[:, 1::8] *= 1.10
    for a, b in LEDGES:
        f[a:b] *= 1.12
        f[a, :] *= 1.15
        f[b - 1, :] *= 0.75
        f[b, :] *= 0.55
    leaf_rgb = shade(leaf_rgb, f)
    ov = Overlay(w, h)
    ov.line([(DOOR_X0 + 6, LEDGES[1][0] - 1), (DOOR_X1 - 6, LEDGES[0][1] + 1)], col("rust_brown", 0.30), 7.0)
    ov.line([(DOOR_X0 + 6, LEDGES[1][0] - 3), (DOOR_X1 - 6, LEDGES[0][1] - 1)], col("rust_brown", 0.48), 2.0)
    leaf_rgb = ov.composite(leaf_rgb)
    leaf = (xx >= DOOR_X0) & (xx < DOOR_X1) & (yy >= DOOR_Y0) & (yy < DOOR_Y1)
    rgb = np.where(leaf[..., None], leaf_rgb, wall)
    # steel edge with bolts
    edge = leaf & ((xx < DOOR_X0 + 2) | (xx >= DOOR_X1 - 2) | (yy < DOOR_Y0 + 2) | (yy >= DOOR_Y1 - 2))
    rgb[edge] = col("steel_blue", 0.26)
    rgb[DOOR_Y0, DOOR_X0:DOOR_X1] = col("steel_blue", 0.50)
    for y in range(DOOR_Y0 + 6, DOOR_Y1 - 4, 12):
        rivet(rgb, DOOR_X0, y, "steel_blue", 0.40)
        rivet(rgb, DOOR_X1 - 2, y, "steel_blue", 0.40)
    # hanging rail, rollers and hangers
    rgb[2:9, :] = col("steel_blue", 0.22)
    rgb[2, :] = col("steel_blue", 0.55)
    rgb[8, :] = col("steel_blue", 0.10)
    ov = Overlay(w, h)
    for rx in (26, 102):
        ov.rect(rx - 2, 6, rx + 3, DOOR_Y0 + 6, fill=col("steel_blue", 0.30))
        ov.ellipse(rx - 5, 0, rx + 6, 11, fill=col("steel_blue", 0.38))
        ov.ellipse(rx - 2, 3, rx + 3, 8, fill=col("steel_blue", 0.14))
    # hasp and padlock
    ov.rect(108, 58, 122, 62, fill=col("steel_blue", 0.40))
    ov.ellipse(111, 59, 119, 67, outline=col("steel_blue", 0.55), width=1.2)
    ov.rect(110, 64, 120, 73, fill=col("steel_blue", 0.30))
    ov.rect(110, 64, 120, 65, fill=col("steel_blue", 0.60))
    # the plate
    ov.rect(31, 34, 97, 50, fill=col("concrete_cold", 0.08))
    ov.rect(32, 35, 96, 49, fill=col("plaster_warm", 0.90))
    rgb = ov.composite(rgb)
    body, shadow = ep2lib.glyph_masks(DOOR_WORD)
    ep2lib.paste_mask(rgb, body | shadow, col("concrete_cold", 0.06), 64, 42)
    # big painted number, whitewash, brushed (worn)
    body, _ = ep2lib.glyph_masks(DOOR_NUMBER)
    big = np.repeat(np.repeat(body, 2, 0), 2, 1)
    worn = rng.random(big.shape) < 0.12
    canvas = rgb.copy()
    ep2lib.paste_mask(canvas, big & ~worn, col("plaster_warm", 0.82), 64, 78)
    rgb = canvas
    rgb[DOOR_Y1:, :] = col("concrete_cold", 0.10)
    rgb[DOOR_Y1, :] = col("concrete_cold", 0.03)
    return rgb


# ================================================================ pieces
PIECES = [
    Piece("SDTRAK1", tex_trak1, "flat", (64, 64), ["SDTRAK1"], 2, "xy",
          "Vía sobre balasto",
          "Vía de la playa vista desde arriba: balasto de granito, traviesas de hormigón soviéticas cada 16 px, "
          "placas de asiento y clips, dos carriles con la cabeza pulida y los lados oxidados. Los carriles van a lo "
          "largo de y; en x las losetas forman vías paralelas.",
          rec_why="La pieza que dice «estación de clasificación» desde el suelo. Traviesas de hormigón, no de madera "
                  "como SDRAIL1 del metro: otra época, otro sitio, y se distinguen a simple vista."),
    Piece("SDBLST1", tex_blst1, "flat", (64, 64), ["SDBLST1"], 1, "xy",
          "Balasto",
          "Balasto suelto entre vías: piedra de granito machacada, polvo de óxido y aceite de los vagones.",
          rec_why="El relleno de la playa entre vías y andenes; tila sin costura (Voronoi envuelto)."),
    Piece("SDWAGN1", tex_wagn1, "wall", (128, 128), ["SDWAGN1"], 3, "x",
          "Vagón de mercancías (lateral)",
          "Vagón cubierto soviético: tablazón en minio rojo-óxido gastado hasta la madera gris, postes y riostras "
          "de acero, larguero, el bastidor oscuro debajo y un número de 8 cifras estarcido (dígitos de píxel "
          "propios).",
          rec_why="Un tren de vagones sale de repetirlo en x. A 1x se lee como vagón; el número es inventado."),
    Piece("SDTANK1", tex_tank1, "wall", (128, 128), ["SDTANK1"], 4, "x",
          "Vagón cisterna (lateral)",
          "Cisterna negra de cuatro ejes: cilindro iluminado desde arriba, costuras de virolas remachadas, "
          "cinchas, chorreones de aceite bajo la cúpula y «НЕФТЬ» (petróleo) en crema con nuestro alfabeto.",
          rec_why="El negro brillante contrasta con el rojo-óxido del vagón: dos tipos de tren de un vistazo."),
    Piece("SDARMR1", tex_armr1, "wall", (128, 128), ["SDARMR1"], 5, "x",
          "Tren blindado, con estrella",
          "Chapa del tren blindado: verde oliva desvaído a caqui por el sol, placas de 64 px remachadas, "
          "arañazos y impactos, óxido bajo los remaches, estrella roja con filete crema.",
          rec_why="El panel de identidad del tren blindado; alternar con SDARMR2 para que la estrella no se repita "
                  "cada 128 px."),
    Piece("SDARMR2", tex_armr2, "wall", (64, 128), ["SDARMR2"], 6, "xy",
          "Tren blindado, liso",
          "La misma chapa sin estrella, para rellenar entre paneles.",
          rec_why="Relleno; tila en los dos ejes."),
    Piece("SDSIGL1", tex_sigl1, "wall", (64, 128), ["SDSIGL1"], 7, "no",
          "Señal luminosa",
          "Señal de colores sobre su mástil, contra un pilar de hormigón: pantalla negra, tres lentes con visera "
          "(verde, amarillo, rojo encendido) y la placa «М2» (señal de maniobras) con nuestro alfabeto.",
          rec_why="Pieza de decoración, no tila. Con el rojo encendido sirve de «pare» junto a una puerta cerrada.",
          scene={"left": "SDBRCK3", "right": "SDBRCK3"}),
    Piece("SDBRCK3", tex_brck3, "wall", (64, 128), ["SDBRCK3"], 8, "xy",
          "Ladrillo de la rotonda",
          "Ladrillo de la rotonda de locomotoras: la receta aprobada del ladrillo de la fábrica, algo más claro y "
          "con menos hollín, con un friso arriba (hilada saliente, hilada en diente de sierra, hilada saliente).",
          palette=2,
          why_v2="v2 solo por marble_red, igual que SDBRCK1 aprobado (D66): v1 no tiene rojo de ladrillo cocido.",
          rec_why="Mismo ladrillo que Tankogrado (coherencia de juego) pero se distingue por el friso, típico de la "
                  "arquitectura ferroviaria rusa."),
    Piece("SDGATE2", tex_gate2, "wall", (128, 128), ["SDGATE2"], 9, "x",
          "Puerta corredera de almacén",
          "Puerta corredera del almacén de mercancías: tablas con pintura rojo-pardo levantada hasta la madera, "
          "dos peinazos y una riostra, canto de acero, carril con dos roldanas, aldaba y candado, placa «СКЛАД» "
          "(almacén) y un 3 grande pintado.",
          rec_why="Distinta de SDGATE1 (chapa verde de fábrica): madera y rojo ferroviario."),
]

# Sample room defaults for this set: exterior, sky above.
ROOM = {"wall": "SDBRCK3", "floor": "SDTRAK1", "ceil": None, "light": 1.0}
OVERVIEWS = [
    ("La playa de vías", {"left": "SDWAGN1", "right": "SDTANK1", "back": "SDARMR1", "floor": "SDTRAK1"}),
    ("Rotonda y almacén", {"left": "SDBRCK3", "right": "SDBRCK3", "back": "SDGATE2", "floor": "SDBLST1"}),
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
