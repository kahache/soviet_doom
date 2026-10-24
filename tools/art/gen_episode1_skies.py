"""Episode 1's two skies (P4, D113): MAPINFO sky1 of MAP01, MAP03 and RANGE.

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_episode1_skies.py
                            (macOS: .venv/bin/python tools/art/gen_episode1_skies.py)

Until now MAP01-03 and the practice range wore Freedoom's SKY1 (brown
daylight cloud), which fits none of them. Two night skies, made exactly like
SDSKY1-5 (tools/art/gen_episode2b.py and tools/art/gen_episode3_skies.py,
whose helpers and constants are imported and never edited):

  SDSKY6  MAP01 Zarya-7 (and RANGE): the cosmodrome on the steppe before a
          November dawn, 1977. A cold clear sky with stars, a thin dawn band
          low in the east, the flat steppe dusted with snow; far off, the
          launch pad: the service tower, a rocket on its pad in the
          floodlights, venting, the masts' beams; the base's blocks, its
          assembly hangar, a water tower, a radio mast with red lights, a
          tracking dish, a second (empty) pad, a road of lamps to the pad
  SDSKY7  MAP03 Tankograd: the tractor works that builds tanks, in the
          Urals at night. A low cloud deck lit orange from below by the
          blast furnaces, their gas flares and stoves, the slag pouring
          down a heap, chimneys and their smoke, the open-hearth shop's row
          of stacks, sawtooth halls with lit glazing, a cooling tower and
          its steam, gantry cranes, the gate tower's red star; the yard's
          dirty snow and rails catching the glow

MAP02 (the metro-bunker) has no sky sector (no F_SKY1 in src/maps/MAP02),
so it keeps Freedoom's SKY1, which nothing in it shows. The range takes
SDSKY6: it is a room of the Zarya-7 base (docs/levels/RANGE-practice-range.md
§5), and it has no sky sector either, so the choice is for coherence only.
Neither MAP01 nor MAP03 has a sky sector today: MAP01's strip of night sky
over the hangar is open with the CEO (docs/levels/MAP01-zarya-7.md §13
point 5), MAP03's works yard is roofed. The skies are ready for the day a
level-designer opens one.

MAP03's portal sits in a steel drum inside the closed shop (MAP03-factory.md
§1), so its cobalt glow cannot reach the clouds: SDSKY7 stays palette v1 (no
mosaic_cobalt, unlike SDSKY5).

Format (the SDSKY1-5 contract, ART-BIBLE §2, check_pk3 SKY_SIZES): 1024x128,
one 360-degree turn that wraps in x and never repeats inside the turn; the
horizon at row 100 (gen_episode2b.HORIZON), the ground below it.

Method: one seed per piece (BATCH_SEED 6010 + offset, clear of Episode 3's
6000-6003), tileable numpy fields (artlib.fbm, periodic sines), everything
measured with wrap_dist so the turn closes, quantised to docs/art/palette.json
v1 without dither.

No lettering, no system font (D27). PNGs go to work/art/episode1_skies/sky/,
the panorama preview to docs/art/previews/2026-10-22_P4_episode1-skies.png;
assets/ is never written (the install is a byte copy, D113).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import DIMENSION_MULTIPLE, fbm, tiling_seam_score, to_rgb  # noqa: E402
import ep2lib  # noqa: E402
from ep2lib import col, wrap_dist  # noqa: E402
import gen_episode2b as e2b  # noqa: E402  (the SDSKY1/2 method: size, horizon, helpers, quantiser)
import gen_episode3_skies as e3s  # noqa: E402  (the SDSKY3-5 helpers: blend, stars, the name rules)

PROJECT_ROOT = ep2lib.PROJECT_ROOT
WORK_ROOT = PROJECT_ROOT / "work" / "art" / "episode1_skies"
PREVIEW = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode1-skies.png"
SCRIPT_REL = "tools/art/gen_episode1_skies.py"
SET_NAME = "sky"

# Own seed space: 6010+ (Episode 3's skies took 6000 + 1..3).
BATCH_SEED = 6010
SKY_SIZE = e2b.SKY_SIZE
SKY_W, SKY_H = SKY_SIZE
HORIZON = e2b.HORIZON        # the same eye-level row as SDSKY1-5
# Which map wears which sky (MAPINFO sky1). MAP02 is absent on purpose: no sky sector.
MAP_SKIES = {"MAP01": "SDSKY6", "MAP03": "SDSKY7", "RANGE": "SDSKY6"}

clip01 = e2b.clip01
sky_coords = e2b.sky_coords
horizon_glow = e2b.horizon_glow
blend = e3s.blend
stars = e3s.stars


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


def put(rgb: np.ndarray, y: int, x: int, colour) -> None:
    """One pixel, x wrapped round the turn, y kept inside the texture."""
    if 0 <= y < SKY_H:
        rgb[y, x % SKY_W] = colour


def line(rgb: np.ndarray, x0: float, y0: float, x1: float, y1: float, colour, alpha: float = 1.0) -> None:
    """A 1 px line (x wraps), blended by `alpha`."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    c = np.asarray(colour, float)
    seen = set()
    for t in np.linspace(0, 1, n):
        x, y = int(round(x0 + (x1 - x0) * t)) % SKY_W, int(round(y0 + (y1 - y0) * t))
        if (x, y) in seen or not 0 <= y < SKY_H:
            continue
        seen.add((x, y))
        rgb[y, x] = rgb[y, x] * (1 - alpha) + c * alpha


# ================================================================ SDSKY6, MAP01
STEPPE_ZENITH, STEPPE_LOW = 0.04, 0.20      # steel_blue, top of the sky and just above the horizon
DAWN_X = 760                 # where the sun will rise (the sky turns; it promises no bearing)
DAWN_SPREAD = (240.0, 30.0)  # the dawn's half-width (px round the turn) and rise above the horizon
DAWN_WARM = (170.0, 13.0)    # the warm band: narrower and lower
STEPPE_STAR_P = 0.009
PAD_X = 300                  # the launch pad: rocket centre column
ROCKET_TIP = HORIZON - 31
BOOSTER_TOP = HORIZON - 14   # where the four strap-on boosters' noses start
INTERSTAGE = ROCKET_TIP + 9  # the dark lattice ring under the third stage
TOWER_X, TOWER_W, TOWER_TOP = PAD_X + 5, 5, HORIZON - 36   # the service tower east of the rocket
SERVICE_ARMS = (HORIZON - 26, HORIZON - 17)
FLOOD_MASTS = (PAD_X - 34, PAD_X - 20, PAD_X + 22, PAD_X + 37)
FLOOD_TOP = HORIZON - 24
SECOND_PAD_X = 560           # an older pad, empty tonight
DISH_X = 655                 # a tracking antenna
BASE_SPANS = ((52, 236), (905, 1012))      # the base's blocks round the turn (x0, x1)
HANGAR = (150, 198, 9)       # the assembly hangar (MIK): x0, x1, height
WATER_TOWER_X = 84
MAST_X = 226
ROAD_X = PAD_X - 12          # the road from the base straight out to the pad (it runs away from us)
BASE_GLOWS = ((140, 0.60), (PAD_X, 0.95), (SECOND_PAD_X, 0.30), (960, 0.45))


def lattice(rgb, x0: int, width: int, top: int, base: int, colour, lit=None) -> None:
    """A lattice tower: solid edges, X bracing every 4 rows; `lit` paints the
    bracing's nodes, as floodlights catch them."""
    for y in range(top, base):
        for k in range(width):
            edge = k in (0, width - 1)
            node = (y - top + k) % 4 == 0 or (y - top - k) % 4 == 0
            if edge or node:
                put(rgb, y, x0 + k, colour)
            if lit is not None and node and not edge and (y - top) % 4 == 0:
                put(rgb, y, x0 + k, lit)
    for k in range(width):
        put(rgb, top, x0 + k, colour)


def rocket(rgb) -> None:
    """A Soyuz-type rocket on its pad, floodlit from the west: the core
    stage, the third stage and fairing, the interstage ring, four boosters
    flaring to the base, the support arms round its foot."""
    lit, shaded = col("concrete_cold", 0.80), col("concrete_cold", 0.48)
    booster_lit, booster_shaded = col("concrete_cold", 0.70), col("concrete_cold", 0.40)
    for y in range(ROCKET_TIP, HORIZON + 1):
        h = y - ROCKET_TIP
        half = 0 if h < 2 else 1
        for dx in range(-half, half + 1):
            put(rgb, y, PAD_X + dx, lit if dx <= 0 else shaded)
        if y >= BOOSTER_TOP:
            reach = 2 + int((y - BOOSTER_TOP) * 2.4 / (HORIZON - BOOSTER_TOP))
            for dx in range(2, reach + 1):
                put(rgb, y, PAD_X - dx, booster_lit)
                put(rgb, y, PAD_X + dx, booster_shaded)
    put(rgb, INTERSTAGE, PAD_X - 1, col("concrete_cold", 0.20))
    put(rgb, INTERSTAGE, PAD_X, col("concrete_cold", 0.24))
    put(rgb, INTERSTAGE, PAD_X + 1, col("concrete_cold", 0.14))
    for dx in (-6, -5, 5, 6):                                  # the support arms (the "tulip")
        for y in range(HORIZON - 4, HORIZON + 1):
            if abs(dx) == 6 or y <= HORIZON - 3:
                put(rgb, y, PAD_X + dx, col("concrete_cold", 0.07))


def tex_sky6() -> np.ndarray:
    """The Zarya-7 cosmodrome before a November dawn (MAP01): a cold clear sky
    full of stars over the flat steppe, a thin dawn band in the east under
    streaks of cloud, the launch pad far off with a rocket in its
    floodlights, the base's lights, the snow-dusted steppe."""
    rng = rng_for(1)
    w, h = SKY_W, SKY_H
    yy, xx = sky_coords()
    t = clip01(yy / HORIZON)
    up = np.clip(HORIZON - yy, 0, None)
    ddx = wrap_dist(xx - DAWN_X, w)
    dawn = np.exp(-(ddx / DAWN_SPREAD[0]) ** 2) * np.exp(-up / DAWN_SPREAD[1])
    warm_band = np.exp(-(ddx / DAWN_WARM[0]) ** 2) * np.exp(-up / DAWN_WARM[1]) * (yy <= HORIZON)
    sky_t = STEPPE_ZENITH + (STEPPE_LOW - STEPPE_ZENITH) * t ** 1.8 + 0.12 * dawn
    sky_t = sky_t + (fbm(w, h, 32, 3, rng, 0.5, aspect=4.0) - 0.5) * 0.02
    rgb = to_rgb(clip01(sky_t), "steel_blue").astype(float)
    rgb = blend(rgb, to_rgb(clip01(0.24 + 0.42 * warm_band), "rust_brown").astype(float), clip01(warm_band * 1.3 - 0.10))
    rgb[(warm_band > 0.88) & (up < 1)] = col("plaster_warm", 0.55)   # the first light on the edge of the steppe
    # thin streaks of stratus: dark against the stars, lit from below by the dawn
    streak = fbm(w, h, 8, 4, rng, 0.5, aspect=0.25)
    band = np.exp(-((yy - 74) / 16.0) ** 2)
    cloud = clip01((streak - 0.56) / 0.10) * band
    dawn_c = np.exp(-(ddx / 200.0) ** 2)
    cloud_rgb = to_rgb(clip01(0.07 + 0.04 * t), "steel_blue").astype(float)
    cloud_rgb = blend(cloud_rgb, to_rgb(clip01(0.30 + 0.22 * dawn_c), "rust_brown").astype(float), 0.85 * dawn_c)
    rgb = blend(rgb, cloud_rgb, cloud * 0.85)
    stars(rgb, rng, STEPPE_STAR_P, (yy < 80) & (cloud < 0.08) & (dawn < 0.22))
    # the pad's floodlit haze, and the masts' beams converging on the rocket
    pdx = wrap_dist(xx - PAD_X, w)
    haze = np.exp(-(pdx / 30.0) ** 2) * np.exp(-(up / 24.0) ** 2) * (yy <= HORIZON)
    rgb = blend(rgb, col("plaster_warm", 0.40), haze * 0.55)
    for mx in FLOOD_MASTS:
        aim_y = HORIZON - 12 if abs(mx - PAD_X) < 25 else HORIZON - 20
        line(rgb, mx, FLOOD_TOP, PAD_X + (1 if mx > PAD_X else -1), aim_y, col("plaster_warm", 0.55), 0.30)
    # the steppe: almost flat, frozen, dusted with snow, the dawn on the snow
    ground = yy > HORIZON
    depth = clip01((yy - HORIZON) / (h - HORIZON))
    soil_t = 0.06 + 0.06 * depth + (fbm(w, h, 32, 3, rng, 0.5, aspect=0.5) - 0.5) * 0.05
    soil = to_rgb(clip01(soil_t), "khaki_olive").astype(float)
    snow_f = fbm(w, h, 16, 4, rng, 0.55, aspect=0.25)
    snow_m = clip01((snow_f - 0.50 + 0.10 * depth) / 0.08)
    snow = to_rgb(clip01(0.18 + 0.14 * depth + 0.08 * dawn_c), "steel_blue").astype(float)
    snow = blend(snow, col("rust_brown", 0.42), 0.35 * dawn_c * (1 - depth))
    land = blend(soil, snow, snow_m)
    rgb = np.where(ground[..., None], land, rgb)
    rise = np.round(1.5 * (fbm(w, 1, 24, 3, rng)[0] - 0.5)).astype(int)   # a swell of a pixel or so, no more
    for x in range(w):
        if rise[x] > 0:
            rgb[HORIZON - rise[x] + 1:HORIZON + 1, x] = to_rgb(np.array([[0.05]]), "khaki_olive")[0, 0]
    rgb[HORIZON, :] = blend(rgb[HORIZON, :][None], col("khaki_olive", 0.04), np.full((1, w), 0.7))[0]
    # the road out to the pad, its lamps closer and wider apart towards us
    for y in range(HORIZON + 1, h):
        k = y - HORIZON
        half = 0.5 + k * 0.12
        x0, x1 = int(np.floor(ROAD_X - half)), int(np.ceil(ROAD_X + half))
        for x in range(x0, x1 + 1):
            put(rgb, y, x, col("concrete_cold", 0.07))
    for k in (1, 3, 6, 10, 15, 21):
        y = HORIZON + k
        for side in (-1, 1):
            put(rgb, y, int(round(ROAD_X + side * (2 + k * 0.14))), col("hazard_yellow", 0.85))
        if y + 1 < h:
            put(rgb, y + 1, int(round(ROAD_X - (2 + k * 0.14))), col("hazard_yellow", 0.35))
    # the base: low blocks with lit windows, the assembly hangar, a water tower, a mast
    dark = col("concrete_cold", 0.04)
    for x0, x1 in BASE_SPANS:
        x = x0
        while x < x1:
            bw = int(rng.integers(5, 15))
            bh = int(rng.integers(2, 6))
            for k in range(bw):
                rgb[HORIZON - bh:HORIZON + 1, (x + k) % w] = dark
            for y0 in range(HORIZON - bh + 1, HORIZON, 2):
                for k in range(1, bw - 1, 2):
                    if rng.random() < 0.14:
                        put(rgb, y0, x + k, col("cream_yellow", float(rng.uniform(0.55, 0.85))))
            x += bw + int(rng.integers(0, 6))
    hx0, hx1, hh = HANGAR
    for x in range(hx0, hx1):
        u = (x - hx0) / (hx1 - hx0 - 1)
        top = HORIZON - hh - int(round(2 * np.sin(np.pi * u)))     # the arched roof
        rgb[top:HORIZON + 1, x] = col("concrete_cold", 0.06)
    rgb[HORIZON - 4:HORIZON, hx0 + 18:hx0 + 30] = col("cream_yellow", 0.72)   # the hangar's gate, open and lit
    rgb[HORIZON - 4, hx0 + 18:hx0 + 30] = col("cream_yellow", 0.90)
    rgb[HORIZON - 15:HORIZON + 1, WATER_TOWER_X] = col("concrete_cold", 0.06)
    rgb[HORIZON - 19:HORIZON - 15, WATER_TOWER_X - 2:WATER_TOWER_X + 3] = col("concrete_cold", 0.06)
    put(rgb, HORIZON - 20, WATER_TOWER_X, col("flag_red", 1.0))
    e2b.lattice_mast(rgb, MAST_X, HORIZON - 42, HORIZON, (HORIZON - 41, HORIZON - 28, HORIZON - 15))
    gcol = horizon_glow(np.arange(w, dtype=float)[None, :], np.full((1, w), float(HORIZON)), BASE_GLOWS, 60.0, 30.0)[0]
    e2b.lights(rgb, rng, (HORIZON - 1, HORIZON + 3), 0.002 + 0.06 * gcol,
               (col("cream_yellow", 0.80), col("hazard_yellow", 0.75), col("cream_yellow", 0.60)))
    # the tracking dish on its pedestal, turned up to the sky
    rgb[HORIZON - 6:HORIZON + 1, DISH_X] = col("concrete_cold", 0.06)
    for a in np.linspace(np.deg2rad(200), np.deg2rad(340), 14):
        put(rgb, int(round(HORIZON - 10 + 5 * np.sin(a) * 0.6 + 3)), int(round(DISH_X + 5 * np.cos(a))),
            col("concrete_cold", 0.08))
    line(rgb, DISH_X, HORIZON - 7, DISH_X + 2, HORIZON - 12, col("concrete_cold", 0.08))
    # the empty second pad: a short tower, two floodlights, a red light
    lattice(rgb, SECOND_PAD_X, 3, HORIZON - 17, HORIZON + 1, col("concrete_cold", 0.05))
    put(rgb, HORIZON - 18, SECOND_PAD_X + 1, col("flag_red", 1.0))
    for fx in (SECOND_PAD_X - 9, SECOND_PAD_X + 11):
        rgb[HORIZON - 10:HORIZON + 1, fx] = col("concrete_cold", 0.07)
        put(rgb, HORIZON - 11, fx, col("cream_yellow", 0.92))
    # the launch pad: floodlight masts, the service tower, the rocket, its vapour
    for mx in FLOOD_MASTS:
        rgb[FLOOD_TOP:HORIZON + 1, mx % w] = col("concrete_cold", 0.07)
        for k in (-1, 0, 1):
            put(rgb, FLOOD_TOP - 1, mx + k, col("cream_yellow", 0.95))
        put(rgb, FLOOD_TOP - 1, mx, (255, 255, 255))
    lattice(rgb, TOWER_X, TOWER_W, TOWER_TOP, HORIZON + 1, col("concrete_cold", 0.05), lit=col("hazard_yellow", 0.45))
    for ay in SERVICE_ARMS:
        line(rgb, PAD_X + 2, ay, TOWER_X, ay, col("concrete_cold", 0.06))
    rocket(rgb)
    for k in (1, 2, 3):                                           # the tower's red obstruction lights
        put(rgb, TOWER_TOP - 1, TOWER_X + k, col("flag_red", 1.0 if k == 2 else 0.60))
    put(rgb, TOWER_TOP + 12, TOWER_X + TOWER_W - 1, col("flag_red", 1.0))
    e2b.smoke(rgb, rng, PAD_X + 2, HORIZON - 19, 22, col("steel_blue", 0.66))   # oxygen boiling off, drifting east
    put(rgb, ROCKET_TIP - 1, PAD_X, col("flag_red", 0.95))
    return np.clip(rgb, 0, 255).astype(np.uint8)


# ================================================================ SDSKY7, MAP03
# (x, strength): what lights the cloud from below. The blast furnaces, the
# slag heap, the open-hearth shop, the rolling mill; dimmer to the east,
# where the goods spur comes in from the dark of the metro.
WORKS_GLOWS = ((215, 1.0), (262, 0.85), (420, 1.0), (520, 0.75), (650, 1.0), (30, 0.55), (900, 0.40))
FURNACES = ((215, 1.0), (262, 0.85), (650, 1.10))   # (x, scale): blast furnaces
OPEN_HEARTH = (488, 6, 9, 3)  # first stack x, count, spacing, width: the open-hearth shop's row of stacks
CHIMNEYS = ((40, 50, 3), (140, 56, 2), (322, 44, 3), (598, 58, 2), (712, 40, 4), (842, 60, 2), (1004, 52, 3))
SLAG_X = 420                 # the slag heap, molten slag pouring down its flank
COOLING_X = 880              # a cooling tower and its steam
CRANES = (760, 792)
GATE_X = 352                 # the works' gate tower with its red star
SPUR_X = 975                 # the goods spur's rails, coming at us
CLOUD_T = 0.44


def blast_furnace(rgb, x: int, s: float) -> tuple[int, int]:
    """A blast furnace in silhouette: the tapering shaft, the top frame and
    its uptakes, the inclined skip bridge, the downcomer, three hot-blast
    stoves; returns where its gas flare burns (x, y)."""
    dark = col("concrete_cold", 0.03)
    top = HORIZON - int(round(38 * s))
    for y in range(top, HORIZON + 1):
        half = 2 + int(3 * (y - top) / (HORIZON - top))
        for k in range(-half, half + 1):
            put(rgb, y, x + k, dark)
    for y in range(top - 8, top):
        for k in (-1, 0, 1):
            put(rgb, y, x + k, dark)
    line(rgb, x - 1, top - 7, x - 4, top - 1, dark)               # the uptakes
    line(rgb, x + 1, top - 7, x + 4, top - 1, dark)
    for k in (0, 1):                                                # the skip bridge
        line(rgb, x - 28 + k, HORIZON, x - 2 + k, top + 1, dark)
    line(rgb, x + 2, top - 5, x + 12, HORIZON - int(18 * s), dark)  # the downcomer to the dust catcher
    for k, sx in enumerate((x + 10, x + 16, x + 22)):              # the stoves: domed cylinders
        st = HORIZON - int(round((24 + 2 * k) * s))
        for y in range(st, HORIZON + 1):
            for d in range(-2, 3):
                if y > st or abs(d) < 2:
                    put(rgb, y, sx + d, dark)
    return x, top - 9


def flare(rgb, rng, x: int, y: int) -> None:
    """A gas flare on a furnace top: a flame a few pixels high, white at the root."""
    put(rgb, y + 1, x, (255, 255, 255))
    put(rgb, y, x, col("cream_yellow", 1.0))
    for k in range(1, 5):
        dx = int(rng.choice((-1, 0, 0, 1)))
        put(rgb, y - k, x + dx, col("hazard_yellow", 0.95 - 0.12 * k))
    put(rgb, y, x - 1, col("hazard_yellow", 0.80))
    put(rgb, y, x + 1, col("hazard_yellow", 0.80))


def red_star(rgb, cx: int, top: int) -> None:
    """A five-pixel lit red star (the works' gate)."""
    for dy, row in enumerate((("..X.."), ("XXXXX"), (".XXX."), (".X.X."))):
        for dx, c in enumerate(row):
            if c == "X":
                put(rgb, top + dy, cx - 2 + dx, col("flag_red", 1.0 if dy < 2 else 0.80))


def tex_sky7() -> np.ndarray:
    """Tankograd at night (MAP03): a low overcast lit orange from below by the
    furnaces, colder and darker at the zenith; smoke, flares, the slag pour,
    the works' skyline in black against the glow; the yard's dirty snow and
    rails catching it."""
    rng = rng_for(2)
    w, h = SKY_W, SKY_H
    yy, xx = sky_coords()
    t = clip01(yy / HORIZON)
    up = np.clip(HORIZON - yy, 0, None)
    glow = horizon_glow(xx, yy, WORKS_GLOWS, 150.0, 58.0)
    deck = fbm(w, h, 16, 5, rng, 0.55, aspect=2.5)
    cover = clip01((deck + 0.12 * t - CLOUD_T) / 0.14)
    detail = fbm(w, h, 64, 3, rng, 0.5, aspect=2.0)
    cold = to_rgb(clip01(0.05 + 0.07 * t), "steel_blue").astype(float)
    underside = cover * (1 - cover) * 4 * 0.5 + cover * 0.5          # the cloud's belly catches most
    warm_t = 0.08 + 0.14 * t ** 1.4 + 0.34 * glow * (0.55 + 0.45 * underside) + (detail - 0.5) * 0.08
    warm = to_rgb(clip01(warm_t), "rust_brown").astype(float)
    a = clip01(cover * (0.35 + 0.65 * (t ** 0.8)) + 0.55 * glow)
    rgb = blend(cold, warm, a)
    hot = clip01(glow - 0.45) * np.exp(-up / 22.0)                    # the brightest belly over the furnaces
    rgb = blend(rgb, to_rgb(clip01(0.45 + 0.30 * hot), "hazard_yellow").astype(float), hot * 0.9)
    stars(rgb, rng, 0.0015, (cover < 0.04) & (yy < 40) & (glow < 0.08))
    # smoke: from every stack and the furnace tops, drifting east, lit or dark
    stacks = list(CHIMNEYS)
    x0, n, step, sw = OPEN_HEARTH
    stacks += [(x0 + k * step, 50 + (k * 3) % 7, sw) for k in range(n)]
    gx = horizon_glow(np.arange(w, dtype=float)[None, :], np.full((1, w), float(HORIZON)), WORKS_GLOWS, 150.0, 58.0)[0]
    for x, top, sw_ in stacks:
        tone = col("rust_brown", 0.30) if gx[x % w] > 0.5 else col("concrete_cold", 0.09)
        e2b.smoke(rgb, rng, x + sw_ // 2, top, 40, tone)
    for fx, s in FURNACES:
        e2b.smoke(rgb, rng, fx, HORIZON - int(38 * s) - 10, 30, col("rust_brown", 0.40))
    # the cooling tower's steam: a white column, lit warm underneath
    cdx = wrap_dist(xx - COOLING_X, w)
    rise_c = np.clip(HORIZON - 26 - yy, 0, None)
    steam = np.exp(-((cdx - rise_c * 0.25) / (7 + rise_c * 0.35)) ** 2) * np.exp(-rise_c / 55.0) * (yy < HORIZON - 24)
    steam = steam * (0.55 + 0.45 * fbm(w, h, 32, 3, rng, 0.5))
    steam_rgb = blend(to_rgb(clip01(0.38 + 0.0 * t), "steel_blue").astype(float), col("rust_brown", 0.45),
                      np.full((h, w), 0.35))
    rgb = blend(rgb, steam_rgb, clip01(steam * 1.2))
    # the far halls: sawtooth roofs with lit glazing, flat sheds, lit windows
    dark = col("concrete_cold", 0.035)
    x = 0
    while x < w:
        hw = int(rng.integers(18, 64))
        hh = int(rng.integers(4, 11))
        saw = rng.random() < 0.6
        for k in range(hw):
            p = k % 7
            top = HORIZON - hh - (p // 2 if saw else 0)
            rgb[top:HORIZON + 1, (x + k) % w] = dark
            if saw and p == 6 and rng.random() < 0.75:
                for yg in range(top, top + 3):
                    put(rgb, yg, x + k, col("hazard_yellow", float(rng.uniform(0.55, 0.85))))
        for y0 in range(HORIZON - hh + 2, HORIZON, 3):
            for k in range(1, hw - 1, 2):
                if rng.random() < 0.10:
                    put(rgb, y0, x + k, col("cream_yellow", float(rng.uniform(0.50, 0.80))))
        x += hw + int(rng.integers(0, 12))
    # the slag heap, molten slag running down its flank
    sdx = wrap_dist(np.arange(w, dtype=float) - SLAG_X, w)
    heap = HORIZON - 10 * np.exp(-(sdx / 24.0) ** 2)
    for xc in np.flatnonzero(heap < HORIZON - 0.5):
        rgb[int(np.ceil(heap[xc])):HORIZON + 1, xc] = col("concrete_cold", 0.04)
    pour = [(SLAG_X - 3 - k, int(np.ceil(heap[(SLAG_X - 3 - k) % w])) + (k > 6)) for k in range(14)]
    for k, (px, py) in enumerate(pour):
        put(rgb, py, px, col("cream_yellow", 1.0) if k < 3 else col("hazard_yellow", 0.95 - 0.03 * k))
        put(rgb, py + 1, px, col("rust_brown", 0.80))
    # the blast furnaces, their flares
    flames = [blast_furnace(rgb, fx, s) for fx, s in FURNACES]
    for fx, fy in flames:
        flare(rgb, rng, fx, fy)
    # chimneys (brick, slightly tapered) with red obstruction lights
    for x, top, sw_ in stacks:
        for y in range(top, HORIZON + 1):
            extra = 1 if y > top + (HORIZON - top) * 0.6 else 0
            for k in range(-extra, sw_ + extra):
                put(rgb, y, x + k, col("concrete_cold", 0.05))
        put(rgb, top, x + sw_ // 2, col("flag_red", 1.0))
        put(rgb, top + (HORIZON - top) // 2, x + sw_ // 2, col("flag_red", 0.85))
    # the cooling tower: a hyperboloid, its glow-lit flank
    ctop = HORIZON - 26
    for y in range(ctop, HORIZON + 1):
        u = (y - ctop) / (HORIZON - ctop)
        half = 6 + 7 * (u - 0.3) ** 2 / 0.49
        for k in range(-int(half), int(half) + 1):
            put(rgb, y, COOLING_X + k, col("concrete_cold", 0.09 if k < -half * 0.5 else 0.045))
    # gantry cranes over the stockyard
    for cx in CRANES:
        ctop_ = HORIZON - 21
        for lx in (cx, cx + 9):
            rgb[ctop_:HORIZON + 1, lx % w] = col("concrete_cold", 0.05)
        line(rgb, cx - 4, ctop_, cx + 14, ctop_, col("concrete_cold", 0.05))
        line(rgb, cx - 4, ctop_ + 1, cx + 14, ctop_ + 1, col("concrete_cold", 0.05))
        put(rgb, ctop_ - 1, cx + 14, col("flag_red", 1.0))
    # the gate tower and its red star
    for y in range(HORIZON - 16, HORIZON + 1):
        for k in range(-3, 4):
            put(rgb, y, GATE_X + k, col("concrete_cold", 0.05))
    rgb[HORIZON - 16, (GATE_X - 4) % w:(GATE_X + 5) % w] = col("concrete_cold", 0.05)
    rgb[HORIZON - 23:HORIZON - 16, GATE_X % w] = col("concrete_cold", 0.07)
    red_star(rgb, GATE_X, HORIZON - 27)
    for k in (-2, 0, 2):
        put(rgb, HORIZON - 9, GATE_X + k, col("cream_yellow", 0.75))
    # the yard: frozen mud, dirty snow, rails, the glow on all of it
    ground = yy > HORIZON
    depth = clip01((yy - HORIZON) / (h - HORIZON))
    g_col = gx[None, :] * (1 - 0.55 * depth)
    mud = to_rgb(clip01(0.025 + 0.025 * fbm(w, h, 32, 3, rng, 0.5, aspect=0.5)), "concrete_cold").astype(float)
    snow_m = clip01((fbm(w, h, 16, 4, rng, 0.55, aspect=0.3) - 0.52) / 0.08)
    snow = to_rgb(clip01(0.10 + 0.06 * depth), "concrete_cold").astype(float)
    yard = blend(mud, snow, snow_m)
    yard = blend(yard, to_rgb(clip01(0.22 + 0.30 * g_col), "rust_brown").astype(float), 0.55 * g_col)
    rgb = np.where(ground[..., None], yard, rgb)
    for ry in (HORIZON + 5, HORIZON + 6, HORIZON + 15, HORIZON + 16):   # rails across the yard, their sheen
        sheen = (rng.random(w) < 0.22) & (gx > 0.45)
        rgb[ry, sheen] = blend(rgb[ry, sheen][None], col("hazard_yellow", 0.45), np.full((1, int(sheen.sum())), 0.5))[0]
    for y in range(HORIZON + 1, h):                                  # the spur's rails, coming at us
        k = y - HORIZON
        for side in (-1, 1):
            put(rgb, y, int(round(SPUR_X + side * (1 + k * 0.28))), col("concrete_cold", 0.30))
    for fx, fy in flames + [(SLAG_X - 6, HORIZON)]:                  # their reflections in the wet yard
        for k in range(2, 14):
            if rng.random() < 0.7:
                put(rgb, HORIZON + k, fx + int(rng.choice((-1, 0, 0, 1))), col("hazard_yellow", 0.62 - 0.02 * k))
    return np.clip(rgb, 0, 255).astype(np.uint8)


# ================================================================ pieces
Piece = e2b.Piece2
PIECES = [
    Piece("SDSKY6", tex_sky6, "sky", SKY_SIZE, ["SDSKY6"], 1, "x",
          "Zarya-7 cosmodrome at dawn (MAP01 and range sky)",
          "The cosmodrome on the steppe before a November 1977 dawn: a cold, clear sky with stars, a low "
          "band of daybreak in the east under streaks of cloud, the flat snowy steppe; in the distance the "
          "pad with its service tower and a Soyuz-type rocket lit by floodlights, venting oxygen, the base's "
          "blocks, the assembly hangar, a water tower, a mast with red lights, a tracking antenna, a second "
          "empty pad and the lamp-lit road up to the pad.",
          set_name=SET_NAME,
          rec_why="The rocket and the dawn orient the player without a word; the range is a room of the same base."),
    Piece("SDSKY7", tex_sky7, "sky", SKY_SIZE, ["SDSKY7"], 2, "x",
          "Tankograd at night (MAP03 sky)",
          "The tractor-and-tank works in the Urals at night: low clouds stained orange by the blast "
          "furnaces, their gas flares and stoves, molten slag pouring down the tip, smoking chimneys with "
          "red lights, the steelworks' row of stacks, saw-tooth halls with lit glazing, a cooling tower "
          "and its steam, gantry cranes, the red star on the gate tower; below, the yard with dirty snow "
          "and rails catching the glow.",
          set_name=SET_NAME,
          rec_why="No portal glow: in MAP03 it is inside the drum of the closed hall, and the cobalt would "
                  "force palette v2."),
]


def all_lumps() -> list[str]:
    return [l for p in PIECES for l in p.lumps]


def allowed_colours() -> list[tuple[int, int, int]]:
    return e2b.allowed_colours(())


def build_all(out_root: Path | None = None) -> tuple[list[dict], dict]:
    """Render the two skies into work/art/episode1_skies/sky/ (or
    out_root/sky). Returns (manifest entries, quantised arrays by lump)."""
    out_dir = (out_root or WORK_ROOT) / SET_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    entries, arrays = [], {}
    for p in PIECES:
        rgb = p.builder()
        lump = p.lumps[0]
        hh, ww = rgb.shape[:2]
        assert (ww, hh) == p.size == SKY_SIZE, (lump, ww, hh)
        assert ww % DIMENSION_MULTIPLE == 0 and hh % DIMENSION_MULTIPLE == 0, lump
        img = e2b.quantise(rgb)
        img.save(out_dir / f"{lump}.png", optimize=True)
        a = ep2lib.as_array(img)
        arrays[lump] = a
        colours = {tuple(int(v) for v in c) for c in a[..., :3].reshape(-1, 3)}
        entries.append({
            "piece": p.key, "lumps": p.lumps, "kind": p.kind, "set": SET_NAME, "width": ww, "height": hh,
            "palette_version": p.palette, "v2_ramps": list(p.ramps), "tiles": p.tiles, "script": SCRIPT_REL,
            "seed": BATCH_SEED + p.offset, "files": [f"work/art/episode1_skies/{SET_NAME}/{lump}.png"],
            "maps": sorted(m for m, s in MAP_SKIES.items() if s == lump),
            "colours_used": len(colours), "mean_luma": round(ep2lib.mean_luma(a), 1),
            "seam_score": round(tiling_seam_score(a[..., :3]), 2),
            "title_es": p.title, "description_es": p.desc, "status": "approved under D113's standing approval",
        })
    return entries, arrays


# ================================================================ preview
PREVIEW_SCALE = 2
PREVIEW_GAP = 8
SEAM_COLS = 192              # columns either side of the wrap in the seam strip
VIEW_YAWS = {"SDSKY6": (105, 267), "SDSKY7": (81, 309)}   # SDSKY6: the pad, the dawn; SDSKY7: the furnaces, the cooling tower
VIEW_SCALE = 2


def screen_view(sky: np.ndarray, yaw_deg: float) -> np.ndarray:
    """What a 320-wide screen shows of the sky at a yaw (gen_episode2b's
    mapping, 1024 columns per turn; NOT VERIFIED against GZDoom), the 128 rows."""
    return e2b.sky_screen(sky, yaw_deg)[:SKY_H]


def build_preview(A: dict, out: Path = PREVIEW) -> Path:
    """One PNG, the layout of Episode 3's sky preview: per sky, the full turn
    at 2x, then the wrap seam (the last and first SEAM_COLS columns side by
    side, 2x) and two screen views (2x). No lettering (D27): SDSKY6 above,
    SDSKY7 below."""
    s = PREVIEW_SCALE
    width = SKY_W * s
    bg = np.array(col("concrete_cold", 0.30), np.uint8)
    blocks = []
    for lump in all_lumps():
        a = A[lump][..., :3]
        pano = np.kron(a, np.ones((s, s, 1), np.uint8))
        seam = np.hstack([a[:, -SEAM_COLS:], np.full((SKY_H, 1, 3), 255, np.uint8), a[:, :SEAM_COLS]])
        seam = np.kron(seam, np.ones((s, s, 1), np.uint8))
        views = [np.kron(screen_view(a, y), np.ones((VIEW_SCALE, VIEW_SCALE, 1), np.uint8)) for y in VIEW_YAWS[lump]]
        row = [seam]
        for v in views:
            row += [np.tile(bg, (SKY_H * s, PREVIEW_GAP, 1)), v]
        row = np.hstack(row)
        pad = width - row.shape[1]
        row = np.hstack([row, np.tile(bg, (row.shape[0], pad, 1))]) if pad > 0 else row[:, :width]
        blocks += [pano, np.tile(bg, (PREVIEW_GAP // 2, width, 1)), row, np.tile(bg, (PREVIEW_GAP * 3, width, 1))]
    sheet = np.vstack(blocks[:-1])
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(sheet, "RGB").save(out, optimize=True)
    return out


# ================================================================ names
def sky_siblings() -> set[str]:
    """SDSKY1-5 (gen_episode2b, gen_episode3_skies): the same family. They do
    not make SDSK a sprite prefix (wall-namespace skies, not sprite frames),
    but they are taken names."""
    return e3s.sky_siblings() | set(e3s.all_lumps())


def existing_lumps() -> set[str]:
    """Every lump name in use elsewhere: files under assets/ and work/ and the
    SD names in TEXTURE-INDEX.md, this generator's own skies aside (their
    drafts in work/art/episode1_skies/, their installed copies in
    assets/textures/sky/ and their own index rows)."""
    own = frozenset(all_lumps())
    names = set()
    for root in (PROJECT_ROOT / "assets", PROJECT_ROOT / "work"):
        if not root.is_dir():
            continue
        for path in root.rglob("*.png"):
            if path.is_relative_to(WORK_ROOT):
                continue
            if path.stem.upper() in own and path.parent == PROJECT_ROOT / "assets" / "textures" / SET_NAME:
                continue
            names.add(path.stem.upper())
    index = e2b.gen_episode2.TEXTURE_INDEX
    if index.is_file():
        names |= set(re.findall(r"SD[A-Z0-9]{1,6}", index.read_text(encoding="utf-8"))) - own
    return names


def name_problems() -> list[str]:
    lumps = all_lumps()
    siblings = sky_siblings()
    out = e2b.gen_episode2.name_problems(lumps, existing_lumps() - siblings)
    return out + [f"{l}: already in use" for l in lumps if l in siblings]


def main() -> None:
    problems = name_problems()
    entries, A = build_all()
    (WORK_ROOT / SET_NAME / "manifest.json").write_text(json.dumps({
        "episode": 1, "phase": "P4", "decision": "D113", "set": SET_NAME, "script": SCRIPT_REL,
        "batch_seed": BATCH_SEED, "maps": MAP_SKIES,
        "preview": PREVIEW.relative_to(PROJECT_ROOT).as_posix(), "pieces": entries,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    for e in entries:
        print(f'{e["piece"]:8s} {e["width"]:4d}x{e["height"]:3d} v{e["palette_version"]} '
              f'colours={e["colours_used"]:3d} luma={e["mean_luma"]:6.1f} seam={e["seam_score"]}')
    out = build_preview(A)
    print("name problems:", problems or "none")
    print(f"preview: {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
