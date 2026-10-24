"""Episode 3's three skies (P4, D113): MAPINFO sky1 of MAP07-09.

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_episode3_skies.py
                            (macOS: .venv/bin/python tools/art/gen_episode3_skies.py)

Until now MAP07-09 wore Freedoom's SKY1 (brown daylight cloud), which fits
none of them. Three night skies, made exactly like SDSKY1/SDSKY2
(tools/art/gen_episode2b.py, whose helpers and constants are imported and
never edited):

  SDSKY3  MAP07 Novaya Zemlya: the polar night, clear and full of stars,
          with curtains of aurora; the island's glaciated range and the
          sea ice at the horizon
  SDSKY4  MAP08 Severomorsk: the Kola fjord at night under a low overcast;
          black cliffs all round, the far shore with the base's lights and
          cranes, the fjord's mouth open to the Barents Sea, a lighthouse
          on the headland with its beam in the mist
  SDSKY5  MAP09 Tunguska: the taiga at night, the invaders' portal glowing
          cobalt on the horizon under the clouds it lights, the dead forest
          of 1908 (stripped trunks still standing, the rest felled) black
          against the glow

Format (the same contract as SDSKY1/2, ART-BIBLE §2, check_pk3 SKY_SIZES):
1024x128, one 360-degree turn that wraps in x and never repeats inside the
turn; the horizon at row 100 (gen_episode2b.HORIZON), the ground below it.

Method: one seed per piece (BATCH_SEED 6000 + offset, the clear space the
TEXTURE-INDEX seed note asks for after 5700 was shared), tileable numpy
fields (artlib.fbm, periodic sines), everything measured with wrap_dist so
the turn closes, quantised to docs/art/palette.json without dither.

Palette: v1, closest available. SDSKY3's aurora has no green-teal ramp to
use: v1's only green is military_green (olive) and v2's cobalt belongs to
the portal (D66), so the curtains are military_green fading into
steel_blue. A true aurora green would be a new ramp; it is NOT opened here.
SDSKY5 adds v2's mosaic_cobalt on the D66 precedent (the portal SDPORT1-4
and its rim SDPRTE1 are cobalt and nothing in the world may share it): the
cobalt is the portal's light, so only pixels the portal lights may take it
(PORTAL_CUT); the rest of SDSKY5 is quantised to v1.

No lettering, no system font (D27). PNGs go to work/art/episode3_skies/sky/,
the panorama preview to docs/art/previews/2026-10-22_P4_episode3-skies.png;
assets/ is never written (the PM installs, D113).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import DIMENSION_MULTIPLE, fbm, quantize, tiling_seam_score, to_rgb  # noqa: E402
import ep2lib  # noqa: E402
from ep2lib import col, wrap_dist  # noqa: E402
import gen_episode2b as e2b  # noqa: E402  (the SDSKY1/2 method: size, horizon, helpers, quantiser)
import gen_metro  # noqa: E402  (palette-version helpers)
import palette as palgen  # noqa: E402

PROJECT_ROOT = ep2lib.PROJECT_ROOT
WORK_ROOT = PROJECT_ROOT / "work" / "art" / "episode3_skies"
PREVIEW = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_episode3-skies.png"
SCRIPT_REL = "tools/art/gen_episode3_skies.py"
SET_NAME = "sky"

# Own seed space (TEXTURE-INDEX seed note: gen_episode2b and gen_arctic both
# used 5700 + offset; the next batch takes 6000+).
BATCH_SEED = 6000
SKY_SIZE = e2b.SKY_SIZE
SKY_W, SKY_H = SKY_SIZE
HORIZON = e2b.HORIZON        # the same eye-level row as SDSKY1/2
TAU = 2 * np.pi

clip01 = e2b.clip01
sky_coords = e2b.sky_coords
ridge_row = e2b.ridge_row
horizon_glow = e2b.horizon_glow


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


def blend(rgb: np.ndarray, colour, alpha: np.ndarray) -> np.ndarray:
    """rgb (float) towards `colour` (one RGB or an (h, w, 3) field) by alpha (h, w)."""
    a = np.clip(alpha, 0, 1)[..., None]
    return rgb * (1 - a) + np.asarray(colour, float) * a


def periodic(xx: np.ndarray, terms) -> np.ndarray:
    """A sum of sines that closes on the turn: (cycles per turn, amplitude, phase)."""
    out = np.zeros_like(xx, dtype=float)
    for k, amp, ph in terms:
        out = out + amp * np.sin(TAU * k * xx / SKY_W + ph)
    return out


def stars(rgb, rng, p: float, allowed: np.ndarray) -> np.ndarray:
    """Single-pixel stars where `allowed`; a quarter bright, a few cream. Returns the mask."""
    h, w = allowed.shape
    s = (rng.random((h, w)) < p) & allowed
    tier = rng.random((h, w))
    rgb[s] = col("steel_blue", 0.62)
    rgb[s & (tier < 0.45)] = col("steel_blue", 0.82)
    rgb[s & (tier < 0.12)] = col("cream_yellow", 0.96)
    rgb[s & (tier < 0.04)] = (255, 255, 255)
    return s


# ================================================================ SDSKY3, MAP07
# (centre x, half-width, lower-edge row, ray height above it, strength)
AURORA_CURTAINS = ((150, 125, 56, 24, 1.00),
                   (520, 85, 48, 20, 0.72),
                   (830, 100, 62, 18, 0.90))
AURORA_GREEN, AURORA_BLUE = "military_green", "steel_blue"   # closest available: no teal ramp (see the module doc)
POLAR_ZENITH, POLAR_LOW = 0.05, 0.16                        # steel_blue, top of the sky and the low sky
POLAR_STAR_P = 0.011
RANGE_ROWS = (5, 17)         # the island's range: lift and height above the horizon (px)
PRESSURE_RIDGES = 34         # broken ridges across the sea ice


def aurora_field(rng, xx, yy) -> tuple[np.ndarray, np.ndarray]:
    """(intensity, height share) of the curtains: a waving lower edge with a
    bright seam, rays rising from it and fading upwards. Every term closes
    on the turn."""
    w = SKY_W
    rays = fbm(w, SKY_H, 128, 2, rng, 0.5, aspect=48.0)          # vertical striations, ~8 px apart
    rays = clip01((rays - 0.28) / 0.50)
    total = np.zeros_like(xx)
    share = np.ones_like(xx)
    for i, (cx, hw, base, height, s) in enumerate(AURORA_CURTAINS):
        env = s * np.exp(-(wrap_dist(xx - cx, w) / hw) ** 4)     # flat-topped, soft ends
        edge = base + periodic(xx, ((2 + i, 9.0, 0.7 + i), (6 + i, 3.0, 1.9 * i), (15, 1.0, 0.3 * i)))
        d = edge - yy                                            # > 0 above the lower edge
        vert = np.where(d >= 0, np.exp(-d / height), np.exp(d / 1.2))
        seam = 0.55 * np.exp(-(d / 1.8) ** 2)
        inten = env * (vert * (0.25 + 0.75 * rays) + seam)
        take = inten > total
        total = np.where(take, inten, total)
        share = np.where(take, clip01(d / (height * 1.8)), share)
    return clip01(total), share


def tex_sky3() -> np.ndarray:
    """The polar night over Novaya Zemlya (MAP07): a clear black sky full of
    stars, three curtains of aurora (green at the lower edge, grey-blue
    higher up), the island's glaciated range catching their light and the
    sea ice to the horizon with its pressure ridges."""
    rng = rng_for(1)
    w, h = SKY_W, SKY_H
    yy, xx = sky_coords()
    t = clip01(yy / HORIZON)
    sky_t = POLAR_ZENITH + (POLAR_LOW - POLAR_ZENITH) * t ** 2.0
    sky_t = sky_t + (fbm(w, h, 32, 3, rng, 0.5, aspect=4.0) - 0.5) * 0.015
    rgb = to_rgb(clip01(sky_t), "steel_blue").astype(float)
    aur, share = aurora_field(rng, xx, yy)
    star_mask = stars(rgb, rng, POLAR_STAR_P, (yy < HORIZON - 6) & (aur < 0.20))
    green = to_rgb(clip01(0.40 + 0.60 * aur), AURORA_GREEN).astype(float)
    blue = to_rgb(clip01(0.25 + 0.45 * aur), AURORA_BLUE).astype(float)
    curtain = green * (1 - share[..., None]) + blue * share[..., None]
    rgb = blend(rgb, curtain, aur * (1.5 - 1.1 * share))
    rgb[star_mask & (aur >= 0.08) & (aur < 0.30)] = col("steel_blue", 0.66)   # a star or two through the thin veil
    lit = aur[30:HORIZON].max(0)                                   # the aurora's light, per column
    # the island's range: glaciated peaks, pale against the sky
    lift, amp = RANGE_ROWS
    f = fbm(w, 1, 9, 5, rng, 0.55)[0]
    f = (f - f.min()) / (f.max() - f.min())
    top = HORIZON - (lift + amp * f ** 1.6)
    slope = np.gradient(top)                                        # < 0: the ridge climbs eastwards
    face = np.clip(-slope * 1.5, -1, 1)                             # the flanks that face west catch the light
    under = clip01((yy - top[None, :]) / 12.0)
    gully = clip01((fbm(w, h, 128, 3, rng, 0.5, aspect=32.0) - 0.50) / 0.20)   # couloirs down from the crests
    snow_t = 0.31 + 0.09 * face[None, :] - 0.08 * under - 0.09 * gully + 0.10 * lit[None, :]
    steep = (np.abs(slope)[None, :] > 1.1) & (under < 0.5)
    snow_t = np.where(steep, 0.12, snow_t)                          # bare rock where it is too steep to hold snow
    snow = to_rgb(clip01(snow_t), "steel_blue").astype(float)
    snow = blend(snow, col(AURORA_GREEN, 0.50), 0.30 * lit[None, :] * (1 - under))
    mountain = yy >= top[None, :]
    rgb = np.where(mountain[..., None], snow, rgb)
    rgb[(yy == np.ceil(top)[None, :]) & (face[None, :] > 0.15)] = col("concrete_cold", 0.62)  # the lit crest
    # the sea ice from the horizon down: lighter towards us
    ice_band = yy >= HORIZON
    depth = clip01((yy - HORIZON) / (h - HORIZON))
    ice_t = 0.22 + 0.12 * depth + (fbm(w, h, 32, 3, rng, 0.5, aspect=1.0) - 0.5) * 0.08
    ice = to_rgb(clip01(ice_t), "concrete_cold").astype(float)
    ice = blend(ice, col(AURORA_GREEN, 0.45), 0.25 * lit[None, :] * (1 - depth))  # the aurora on the ice
    rgb = np.where(ice_band[..., None], ice, rgb)
    rgb[HORIZON, :] = col("concrete_cold", 0.16)                    # the shore line under the range
    for _ in range(PRESSURE_RIDGES):                                 # broken pressure ridges, longer near us
        y = int(rng.integers(HORIZON + 3, h - 2))
        near = (y - HORIZON) / (h - HORIZON)
        x0, length = int(rng.integers(0, w)), int(10 + 70 * near * rng.random())
        xs = (x0 + np.arange(length)) % w
        ys = np.clip(y + np.round(np.sin(np.arange(length) * 0.21 + x0) * near * 1.2).astype(int), 0, h - 2)
        rgb[ys, xs] = col("concrete_cold", 0.50 + 0.10 * near)
        rgb[ys + 1, xs] = col("steel_blue", 0.16)
    return np.clip(rgb, 0, 255).astype(np.uint8)


# ================================================================ SDSKY4, MAP08
FJORD_MOUTH = (700, 880)     # x span where the fjord opens to the Barents Sea (water to the horizon)
FAR_SHORE = (250, 700)       # the far side of the fjord: lower cliffs, the base's lights at their foot
SHORE_SOFT = 70              # px over which the near cliffs fall to the far shore
LIGHTHOUSE_X = 712           # on the headland at the mouth's west side
LIGHTHOUSE_TOP = 80
BASE_GLOWS = ((330, 0.85), (470, 1.0), (610, 0.70))   # the piers' sodium under the cloud
CLOUD_BASE = 46              # the overcast's lower edge (rows): it swallows the cliff tops
CRANES = (350, 395, 458, 520, 590)
SUBMARINES = ((420, 20), (548, 16))                    # (x, length): two boats at the piers
SNOW_LEDGES = 110


def window(x: np.ndarray, a: float, b: float, soft: float) -> np.ndarray:
    return clip01((x - a) / soft + 0.5) * clip01((b - x) / soft + 0.5)


def cliff_profile(rng) -> tuple[np.ndarray, np.ndarray]:
    """The skyline round the fjord, per column, and the far-shore weight:
    high black cliffs on our side, a lower far shore, the open mouth (water
    to the horizon) with a low headland either side of it."""
    x = np.arange(SKY_W, dtype=float)
    near = 30 + 26 * fbm(SKY_W, 1, 12, 5, rng, 0.6)[0]
    far = 74 + 10 * fbm(SKY_W, 1, 24, 4, rng)[0]
    m0, m1 = FJORD_MOUTH
    w_far = window(x, FAR_SHORE[0], FAR_SHORE[1], SHORE_SOFT)
    top = near * (1 - w_far) + far * w_far
    head = window(x, m0 - 40, m1 + 50, 40)
    headland = HORIZON - 16 + 5 * fbm(SKY_W, 1, 32, 3, rng)[0]
    top = top * (1 - head) + np.maximum(np.minimum(top, HORIZON), headland) * head
    mouth = window(x, m0 + 22, m1 - 10, 22)
    top = top * (1 - mouth) + (HORIZON + 1.0) * mouth
    return top, w_far


def tex_sky4() -> np.ndarray:
    """The Kola fjord at Severomorsk at night (MAP08): a low overcast lit
    from below by the base's sodium, black gneiss cliffs with snow on their
    ledges, the far shore with the piers' lights, cranes and their red
    lights and two submarines, the fjord's mouth open to the sea and a
    lighthouse on the headland, its beam crossing the mist; the black water
    reflects it all."""
    rng = rng_for(2)
    w, h = SKY_W, SKY_H
    yy, xx = sky_coords()
    t = clip01(yy / HORIZON)
    deck = fbm(w, h, 16, 5, rng, 0.55, aspect=2.5)
    glow = horizon_glow(xx, yy, BASE_GLOWS, 120.0, 46.0)
    sky_t = 0.07 + 0.09 * t + (deck - 0.5) * 0.08
    rgb = to_rgb(clip01(sky_t), "steel_blue").astype(float)
    warm = to_rgb(clip01(0.14 + 0.22 * glow + (deck - 0.5) * 0.08), "rust_brown").astype(float)
    rgb = blend(rgb, warm, glow * 0.65)
    # the lighthouse's beam in the mist, pointing out to sea (east, +x)
    lx, ly = LIGHTHOUSE_X, LIGHTHOUSE_TOP - 2
    dx = wrap_dist(xx - lx, w)
    spread = 2.0 + np.abs(dx) * 0.09
    beam = clip01(dx / 6.0) * np.exp(-((yy - ly + dx * 0.035) / spread) ** 2) * np.exp(-np.clip(dx, 0, None) / 150.0)
    beam = beam * (dx > 0) * (0.75 + 0.25 * deck)
    lamp_halo = np.exp(-(np.hypot(dx, yy - ly) / 14.0) ** 2)
    rgb = blend(rgb, col("plaster_warm", 0.78), clip01(beam * 0.75 + lamp_halo * 0.55))
    # cliffs: near ones black, the far shore greyer through the haze
    top, w_far = cliff_profile(rng)
    # the night ramps are coarse at the dark end (steel_blue jumps from 8 to
    # 40), so the rock is set in a few chosen tones, not a field
    facets = fbm(w, h, 64, 4, rng, 0.55, aspect=24.0)              # tall facets of the gneiss
    near_rock = np.where((facets > 0.60)[..., None], np.array(col("concrete_cold", 0.035), float),
                         np.array(col("steel_blue", 0.0), float))
    far_rock = np.where((facets < 0.42)[..., None], np.array(col("concrete_cold", 0.035), float),
                        np.array(col("steel_blue", 0.067), float))
    far_pick = w_far[None, :] > fbm(w, h, 16, 3, rng, 0.5, aspect=2.0)   # an organic edge between the two
    rock = np.where(far_pick[..., None], far_rock, near_rock)
    rock_t = 0.02 + 0.05 * w_far[None, :] + 0.04 * glow           # the crest's tone, a step above the rock
    foot = (HORIZON + np.round((1 - w_far) * (3 + 3 * fbm(w, 1, 16, 2, rng)[0]))).astype(int)
    cliff = (yy >= top[None, :]) & (yy <= foot[None, :])
    rgb = np.where(cliff[..., None], rock, rgb)
    crest = (yy == np.ceil(top)[None, :]) & cliff
    rgb[crest] = to_rgb(clip01(rock_t + 0.06), "steel_blue")[crest]   # the crest catches the cloud's light
    for _ in range(SNOW_LEDGES):                                      # snow lying on the ledges
        x0 = int(rng.integers(0, w))
        y0 = int(rng.integers(int(top[x0]) + 2, HORIZON + 2)) if top[x0] + 2 < HORIZON + 2 else HORIZON
        length = int(rng.integers(2, 5))
        xs = (x0 + np.arange(length)) % w
        ok = cliff[y0, xs]
        tone = 0.12 + 0.07 * (1 - w_far[x0]) * float(rng.random())
        rgb[y0, xs[ok]] = col("concrete_cold", tone)
    # the overcast hangs over the cliff tops: torn cloud in front of them
    tatter = fbm(w, h, 32, 4, rng, 0.55, aspect=2.0)
    low = clip01((tatter - 0.50) / 0.14) * np.exp(-(np.clip(yy - CLOUD_BASE, 0, None) / 8.0) ** 2) * (yy > 20)
    cloud = to_rgb(clip01(0.10 + 0.05 * tatter + 0.12 * glow), "steel_blue").astype(float)
    rgb = blend(rgb, cloud, low * 0.70 * (yy < top[None, :] + 6) * (1 - w_far[None, :] * 0.6))
    # the water below the horizon: black, rippled, the beam and the lights on it
    water = yy > foot[None, :]
    ripple = fbm(w, h, 128, 2, rng, 0.5, aspect=2.0)
    water_t = 0.035 + 0.035 * ripple + 0.05 * glow
    rgb = np.where(water[..., None], to_rgb(clip01(water_t), "steel_blue").astype(float), rgb)
    lit_water = np.exp(-(np.clip(dx, 0, None) / 120.0)) * (dx > -6) * (dx < 200)
    sheen = water & (ripple > 0.66) & (lit_water > 0.25) & (yy < HORIZON + 14)
    rgb[sheen] = col("plaster_warm", 0.40)
    # the base along the far shore: piers, lights, cranes with red tops, two boats
    lights_ = []
    x1d = np.arange(w, dtype=float)
    gcol = horizon_glow(x1d[None, :], np.full((1, w), float(HORIZON)), BASE_GLOWS, 120.0, 46.0)[0]
    for x in range(FAR_SHORE[0] + 20, FAR_SHORE[1] - 30):
        rgb[HORIZON - 1:HORIZON + 1, x] = col("concrete_cold", 0.05)  # the piers' line
        if rng.random() < 0.04 + 0.22 * gcol[x]:
            y = HORIZON - int(rng.integers(0, 4))
            c = col("hazard_yellow", 0.80) if rng.random() < 0.6 else col("cream_yellow", 0.90)
            rgb[y, x] = c
            lights_.append((x, y, c))
    for sx, length in SUBMARINES:
        rgb[HORIZON + 1, sx:sx + length] = col("concrete_cold", 0.02)
        rgb[HORIZON - 2:HORIZON + 1, sx + length // 3:sx + length // 3 + 3] = col("concrete_cold", 0.02)
    for cx in CRANES:
        ctop = HORIZON - int(rng.integers(15, 22))
        rgb[ctop:HORIZON, cx] = col("concrete_cold", 0.07)
        jib = int(rng.integers(8, 13)) * (1 if rng.random() < 0.5 else -1)
        xs = np.arange(min(cx, cx + jib), max(cx, cx + jib) + 1) % w
        rgb[ctop, xs] = col("concrete_cold", 0.07)
        rgb[ctop - 1, cx] = col("flag_red", 1.0)
        rgb[ctop, (cx + jib) % w] = col("flag_red", 0.85)
    # a radio mast on the near cliff behind us, red lights
    mast_x = 120
    mtop = int(top[mast_x]) - 22
    e2b.lattice_mast(rgb, mast_x, mtop, int(top[mast_x]) + 1, (mtop + 1, mtop + 9, mtop + 17))
    # the lighthouse: a white tower with a red band, its lamp
    base_y = int(top[LIGHTHOUSE_X])
    rgb[LIGHTHOUSE_TOP:base_y + 1, LIGHTHOUSE_X - 1:LIGHTHOUSE_X + 1] = col("concrete_cold", 0.62)
    rgb[LIGHTHOUSE_TOP + 4:LIGHTHOUSE_TOP + 7, LIGHTHOUSE_X - 1:LIGHTHOUSE_X + 1] = col("flag_red", 0.70)
    rgb[LIGHTHOUSE_TOP - 1, LIGHTHOUSE_X - 2:LIGHTHOUSE_X + 2] = col("concrete_cold", 0.20)
    rgb[ly - 1:ly + 1, LIGHTHOUSE_X - 1:LIGHTHOUSE_X + 1] = (255, 255, 255)
    rgb[ly - 1:ly + 1, LIGHTHOUSE_X + 1] = col("cream_yellow", 0.95)
    # reflections: short broken streaks under each light
    for x, y, c in lights_:
        for k in range(2, 2 + int(rng.integers(3, 9))):
            yr = HORIZON + k
            if yr < h and water[yr, x] and rng.random() < 0.65:
                rgb[yr, x] = np.asarray(c, float) * 0.55 + rgb[yr, x] * 0.45
    return np.clip(rgb, 0, 255).astype(np.uint8)


# ================================================================ SDSKY5, MAP09
PORTAL_X = 600               # where the portal stands on the horizon (the sky turns; nothing promises the map's bearing)
PORTAL_SPREAD = (150.0, 40.0)  # the glow's half-width in x and its rise above the horizon (px)
PORTAL_CUT = 0.015           # portal light above this may take v2's cobalt; below it, v1 only
PORTAL_REACH = 300           # no cobalt farther than this from the portal (px round the turn)
PILLAR_W = 3.0
FELLED_LOGS = 120
CLEAR_AT_PORTAL = 10         # px either side of the portal kept clear of trunks, mostly


def portal_light(xx, yy) -> np.ndarray:
    """How much of the portal's light reaches a pixel: the dome on the
    horizon plus the pillar it throws into the clouds; nothing beyond
    PORTAL_REACH."""
    dx = wrap_dist(xx - PORTAL_X, SKY_W)
    sx, rise = PORTAL_SPREAD
    up = np.clip(HORIZON - yy, 0, None)
    dome = np.exp(-(dx / sx) ** 2) * np.exp(-(up / rise) ** 1.2)
    pillar = np.exp(-(dx / (PILLAR_W + up * 0.04)) ** 2) * np.exp(-up / 70.0) * (yy <= HORIZON)
    return clip01(dome + 0.8 * pillar) * (np.abs(dx) < PORTAL_REACH)


def tex_sky5() -> np.ndarray:
    """The taiga at Tunguska at night (MAP09): torn cloud lit cobalt from
    below by the portal on the horizon, a pillar of its light into the
    overcast with white filaments at its foot, the far living taiga's line
    and, in front, the dead forest of 1908: stripped trunks still standing,
    broken tops, felled logs, black against the glow and rimmed with it."""
    rng = rng_for(3)
    w, h = SKY_W, SKY_H
    yy, xx = sky_coords()
    t = clip01(yy / HORIZON)
    light = portal_light(xx, yy)
    c = fbm(w, h, 16, 5, rng, 0.55, aspect=2.0) + (t - 0.5) * 0.12
    cover = clip01((c - 0.46) / 0.14)
    sky_t = 0.05 + 0.08 * t ** 1.6 + (fbm(w, h, 32, 3, rng, 0.5, aspect=4.0) - 0.5) * 0.02
    cloud_t = 0.07 + 0.06 * t + (fbm(w, h, 64, 3, rng, 0.5, aspect=2.0) - 0.5) * 0.05
    rgb = to_rgb(clip01(sky_t * (1 - cover) + cloud_t * cover), "steel_blue").astype(float)
    stars(rgb, rng, 0.004, (cover < 0.10) & (yy < 70) & (light < 0.05))
    # the portal's light: the cloud undersides catch it most
    under = cover * (1 - cover) * 4 * (1 - t * 0.3) + cover * 0.35
    glow_t = clip01(0.10 + 0.85 * light * (0.60 + 0.40 * under))
    glow_rgb = gen_metro.any_to_rgb(glow_t, "mosaic_cobalt").astype(float)
    jitter = (rng.random((h, w)) - 0.5) * 0.16 * (light > 0.01)    # breaks the glow's edge, no dither (artlib.grain's idea)
    rgb = blend(rgb, glow_rgb, clip01(light * 1.3 + jitter))
    # filaments at the pillar's foot: thin white zigzags (the look of SDPORT1-4)
    for _ in range(5):
        x = PORTAL_X + float(rng.uniform(-8, 8))
        for y in range(HORIZON - 1, HORIZON - int(rng.integers(16, 36)), -1):
            x += float(rng.choice((-1, 0, 0, 1)))
            rgb[y, int(round(x)) % w] = (255, 255, 255) if rng.random() < 0.5 else gen_metro.any_ramp_colour("mosaic_cobalt", 0.95)
    # the core on the horizon
    adx = np.abs(wrap_dist(xx - PORTAL_X, w))
    core = (adx < 7 - (HORIZON - yy) * 0.9) & (yy <= HORIZON) & (yy > HORIZON - 7)
    rgb[core] = gen_metro.any_ramp_colour("mosaic_cobalt", 1.0)
    rgb[core & (adx < 2)] = (255, 255, 255)
    # the far taiga: a line of conifer tips, living, beyond the blast's reach
    tips = ridge_row(rng, 3, 4, 32) - (rng.random(w) < 0.55) * rng.integers(1, 5, w)
    lit_col = light[HORIZON - 2]
    far_t = 0.04 + 0.03 * lit_col[None, :] + 0 * yy
    rgb = np.where((yy >= tips[None, :])[..., None], to_rgb(clip01(far_t), "steel_blue").astype(float), rgb)
    rim_far = (yy == np.ceil(tips)[None, :]) & (lit_col[None, :] > 0.30)
    rgb[rim_far] = gen_metro.any_ramp_colour("mosaic_cobalt", 0.50)
    # the burnt ground from the horizon down, felled logs all lying one way
    ground = yy >= HORIZON
    depth = clip01((yy - HORIZON) / (h - HORIZON))
    gnd_t = 0.02 + 0.025 * fbm(w, h, 64, 3, rng, 0.5, aspect=4.0) + 0.05 * light[HORIZON - 1][None, :] * (1 - depth)
    rgb = np.where(ground[..., None], to_rgb(clip01(gnd_t), "concrete_cold").astype(float), rgb)
    for _ in range(FELLED_LOGS):
        x0 = float(rng.uniform(0, w))
        y0 = float(rng.uniform(HORIZON + 2, h - 1))
        length = 3 + (y0 - HORIZON) * 0.7 * float(rng.uniform(0.6, 1.4))
        side = 1 if wrap_dist(np.array(x0 - PORTAL_X), w) > 0 else -1     # felled away from the epicentre
        for k in range(int(length)):
            xk = int(x0 + side * k) % w
            yk = int(y0 + k * 0.08)
            if yk < h:
                rgb[yk, xk] = col("concrete_cold", 0.01)
                if yk - 1 >= HORIZON and light[HORIZON - 1, xk] > 0.45:
                    rgb[yk - 1, xk] = gen_metro.any_ramp_colour("mosaic_cobalt", 0.30)
    # the dead forest standing: stripped trunks, broken tops, stubs of branches
    x = 0
    while x < w:
        x += int(rng.integers(4, 14))
        if x >= w:
            break
        if abs(float(wrap_dist(np.array(x - PORTAL_X), w))) < CLEAR_AT_PORTAL and rng.random() < 0.85:
            continue
        top = HORIZON - int(8 + 50 * float(rng.random()) ** 2.0)
        width = 2 if rng.random() < 0.25 else 1
        cols_ = [(x + k) % w for k in range(width)]
        rgb[top:HORIZON + 3, cols_] = col("concrete_cold", 0.02)
        if rng.random() < 0.6:                       # a snapped top: a jag to one side
            jag = int(rng.choice((-1, 1)))
            rgb[top - 1:top + 1, (x + jag) % w] = col("concrete_cold", 0.02)
        for _ in range(int(rng.integers(0, 4))):     # stubs of branches, pointing down and out
            by = int(rng.integers(top + 3, HORIZON - 4)) if HORIZON - 4 > top + 3 else top + 3
            bl = int(rng.integers(2, 6))
            sd = int(rng.choice((-1, 1)))
            for k in range(1, bl):
                rgb[min(by + k // 2, h - 1), (x + (width - 1 if sd > 0 else 0) + sd * k) % w] = col("concrete_cold", 0.02)
        lit = float(light[top:HORIZON, x % w].mean()) if top < HORIZON else 0.0
        if lit > 0.22:                               # the glow rims the trunk on its portal side
            side = (x + (width if wrap_dist(np.array(PORTAL_X - x), w) > 0 else -1)) % w
            rim_rows = np.arange(top, HORIZON)
            rim_rows = rim_rows[rng.random(len(rim_rows)) < 0.8]
            rgb[rim_rows, side] = gen_metro.any_ramp_colour("mosaic_cobalt", float(min(0.70, 0.20 + 0.6 * lit)))
    return np.clip(rgb, 0, 255).astype(np.uint8)


# ================================================================ pieces
Piece = e2b.Piece2
PIECES = [
    Piece("SDSKY3", tex_sky3, "sky", SKY_SIZE, ["SDSKY3"], 1, "x",
          "Polar night with aurora (MAP07 sky)",
          "Polar night over Novaya Zemlya: a black, clear sky full of stars, three curtains of the northern "
          "lights (green on the lower edge, blue-grey above, with vertical rays), the island's glacier range lit "
          "by them and the pack ice out to the horizon with its pressure ridges.",
          set_name=SET_NAME,
          rec_why="The palette has no blue-green: the aurora comes out in military_green (olive) melting into "
                  "steel_blue. An aurora-green ramp would be new; I do not open one."),
    Piece("SDSKY4", tex_sky4, "sky", SKY_SIZE, ["SDSKY4"], 2, "x",
          "Kola fjord at night (MAP08 sky)",
          "The Kola fjord at Severomorsk at night: low clouds lit from below by the base's sodium lamps, black "
          "gneiss cliffs with snow on the ledges, the far shore with the lights of the piers and cranes with red "
          "lights, the fjord's mouth open to the Barents Sea and a lighthouse on the cape with its beam crossing "
          "the fog; the black water reflects it all.",
          set_name=SET_NAME,
          rec_why="The cliffs close almost the whole turn: MAP08 is a base in a fjord, and the open horizon is "
                  "only at the mouth, towards the sea, where the lighthouse points."),
    Piece("SDSKY5", tex_sky5, "sky", SKY_SIZE, ["SDSKY5"], 3, "x",
          "Tunguska taiga with the portal (MAP09 sky)",
          "The Tunguska taiga at night: broken clouds lit cobalt from below by the portal on the horizon, a "
          "column of its light up to the clouds with white filaments at its foot, the far line of the living "
          "taiga and, in front, the dead forest of 1908: bare standing trunks, snapped crowns and felled trunks, "
          "black against the glow and outlined by it.",
          set_name=SET_NAME, ramps=("mosaic_cobalt",),
          why_v2="mosaic_cobalt from v2, with D66 as the precedent: the cobalt is the portal's (SDPORT1-4, "
                 "SDPRTE1) and here only the pixels the portal lights take it; the rest of the sky is v1.",
          rec_why="The portal is what MAP09 is about finding: its glow on the horizon orients the player (though "
                  "the sky turns 360° and does not promise the portal's real bearing on the map)."),
]


def all_lumps() -> list[str]:
    return [l for p in PIECES for l in p.lumps]


def allowed_colours(ramps: tuple = ()) -> list[tuple[int, int, int]]:
    return e2b.allowed_colours(ramps)


def quantise_piece(p, rgb: np.ndarray) -> Image.Image:
    """SDSKY3/4: v1, as SDSKY1/2. SDSKY5: v1 everywhere but where the portal's
    light reaches (PORTAL_CUT), where v2's cobalt is allowed too; written on
    the v2 PLTE like every other v2 piece."""
    if not p.ramps:
        return e2b.quantise(rgb)
    v1 = np.asarray(quantize(Image.fromarray(np.ascontiguousarray(rgb), "RGB")).convert("RGB"))
    v2 = np.asarray(e2b.quantise_rgb(rgb, p.ramps).convert("RGB"))
    yy, xx = sky_coords()
    lit = portal_light(xx, yy) >= PORTAL_CUT
    # the white filaments and the core are pure white in v1 too; the cobalt only where lit
    snapped = np.where(lit[..., None], v2, v1).astype(np.uint8)
    return gen_metro.quantize_version(snapped, 2)


def build_all(out_root: Path | None = None) -> tuple[list[dict], dict]:
    """Render the three skies into work/art/episode3_skies/sky/ (or
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
        img = quantise_piece(p, rgb)
        img.save(out_dir / f"{lump}.png", optimize=True)
        a = ep2lib.as_array(img)
        arrays[lump] = a
        colours = {tuple(int(v) for v in c) for c in a[..., :3].reshape(-1, 3)}
        entries.append({
            "piece": p.key, "lumps": p.lumps, "kind": p.kind, "set": SET_NAME, "width": ww, "height": hh,
            "palette_version": p.palette, "v2_ramps": list(p.ramps), "tiles": p.tiles, "script": SCRIPT_REL,
            "seed": BATCH_SEED + p.offset, "files": [f"work/art/episode3_skies/{SET_NAME}/{lump}.png"],
            "colours_used": len(colours), "mean_luma": round(ep2lib.mean_luma(a), 1),
            "seam_score": round(tiling_seam_score(a[..., :3]), 2),
            "title_es": p.title, "description_es": p.desc, "status": "approved under D113's standing approval",
        })
    return entries, arrays


# ================================================================ preview
PREVIEW_SCALE = 2
PREVIEW_GAP = 8
SEAM_COLS = 192              # columns either side of the wrap in the seam strip
VIEW_YAWS = {"SDSKY3": (50, 200), "SDSKY4": (250, 300), "SDSKY5": (211, 30)}   # yaws for the two screen views
VIEW_SCALE = 2


def screen_view(sky: np.ndarray, yaw_deg: float) -> np.ndarray:
    """What a 320-wide screen shows of the sky at a yaw (gen_episode2b's
    mapping, 1024 columns per turn; NOT VERIFIED against GZDoom), the 128 rows."""
    return e2b.sky_screen(sky, yaw_deg)[:SKY_H]


def build_preview(A: dict, out: Path = PREVIEW) -> Path:
    """One PNG: per sky, the full turn at 2x, then the wrap seam (the last
    and first SEAM_COLS columns side by side, 2x) and two screen views (2x).
    No lettering (D27): the order is SDSKY3, SDSKY4, SDSKY5, top to bottom."""
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


def main() -> None:
    problems = name_problems()
    entries, A = build_all()
    (WORK_ROOT / SET_NAME / "manifest.json").write_text(json.dumps({
        "episode": 3, "phase": "P4", "decision": "D113", "set": SET_NAME, "script": SCRIPT_REL,
        "batch_seed": BATCH_SEED, "preview": PREVIEW.relative_to(PROJECT_ROOT).as_posix(), "pieces": entries,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    for e in entries:
        print(f'{e["piece"]:8s} {e["width"]:4d}x{e["height"]:3d} v{e["palette_version"]} '
              f'colours={e["colours_used"]:3d} luma={e["mean_luma"]:6.1f} seam={e["seam_score"]}')
    out = build_preview(A)
    print("name problems:", problems or "none")
    print(f"preview: {out} ({out.stat().st_size // 1024} KB)")


def sky_siblings() -> set[str]:
    """SDSKY1/SDSKY2 (gen_episode2b): the same family, the reason the SD-SK
    prefix exists at all."""
    return {l for p in e2b.PIECES if p.kind == "sky" for l in p.lumps}


def name_problems() -> list[str]:
    """gen_episode2's checks, except that the siblings SDSKY1/2 do not make
    SDSK a sprite prefix (they are wall-namespace skies, not sprite frames;
    no SDSK sprite exists). They still count as taken names."""
    lumps = all_lumps()
    taken = existing_lumps()
    siblings = sky_siblings()
    out = e2b.gen_episode2.name_problems(lumps, taken - siblings)
    return out + [f"{l}: already in use" for l in lumps if l in siblings]


def existing_lumps() -> set[str]:
    """Every lump name in use elsewhere: files under assets/ and work/ and the
    SD names in TEXTURE-INDEX.md, this generator's own skies aside (their
    drafts in work/art/episode3_skies/, their installed copies in
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
        import re
        names |= set(re.findall(r"SD[A-Z0-9]{1,6}", index.read_text(encoding="utf-8"))) - own
    return names


if __name__ == "__main__":
    main()
