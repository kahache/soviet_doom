"""Episode 3, MAP09 — the taiga and alien set: the invaders' portal at Tunguska (D112, P4).

Run with the project venv:  .venv/Scripts/python.exe tools/art/gen_taiga.py
The whole episode and the CEO's sheet: tools/art/gen_episode3.py.

DRAFTS for the CEO: PNGs to work/art/episode3/taiga/, never to assets/.
Palette v1 for the taiga and for the invaders' metal; the portal rim
SDPRTE1 alone asks for v2's mosaic_cobalt, on the D66 precedent (the portal
SDPORT1-4 is cobalt with white filaments and nothing in the world may share
its colour), so the rim reads as part of the portal and of nothing else.

The acid (SDACID1-4) is four frames for ANIMDEFS like SDWATR and SDMOLT:
a ripple field that turns through a full phase while it drifts one tile,
and bubbles whose life is a whole loop, so frame 4 leads back into frame 1.
v1 has no saturated green: the acid is military_green with hazard_yellow
crests (the sheet asks the CEO about it).

The invaders' glyphs on SDGLYP1 are built from rings, arcs, ticks and dots
by a fixed grammar (no stroke ever crosses a ring top to bottom, no ring is
left bare), so they are no alphabet, real or ours; no font involved.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from artlib import Overlay, blend, fbm, grain, shade, to_rgb  # noqa: E402
import ep3lib  # noqa: E402
from ep3lib import FRAMES, Piece, col  # noqa: E402

SET_NAME = "taiga"
SCRIPT_REL = "tools/art/gen_taiga.py"
BATCH_SEED = 5900
FLAT = 64


def rng_for(offset: int) -> np.random.Generator:
    return np.random.default_rng(BATCH_SEED + offset)


# ================================================================ birch bark
BIRCH_TONE = 0.80            # plaster_warm: the chalk white of birch bark
LENTICELS = 70


def tex_bark1() -> np.ndarray:
    """Birch trunk: chalk-white bark, horizontal lenticels, black fissured
    patches and the dark chevron scars of fallen branches, a curl of bark
    peeling to its orange underside."""
    rng = rng_for(1)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    field = BIRCH_TONE + (fbm(w, h, 4, 3, rng, aspect=0.5) - 0.5) * 0.10 + grain(w, h, rng, 0.015)
    rgb = to_rgb(np.clip(field, 0, 1), "plaster_warm")
    grey = fbm(w, h, 3, 3, rng) > 0.66
    rgb = np.where(grey[..., None], blend(rgb, col("concrete_cold", 0.72), np.full((h, w), 0.45)), rgb)
    for _ in range(LENTICELS):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        ln = int(rng.integers(3, 11))
        th = 2 if rng.random() < 0.25 else 1
        for k in range(ln):
            for t in range(th):
                rgb[(y + t) % h, (x + k) % w] = col("concrete_cold", 0.22 if t == 0 else 0.40)
        rgb[(y - 1) % h, x % w:(x % w) + 1] = col("plaster_warm", 0.92)
    black = fbm(w, h, 4, 3, rng, aspect=0.3)
    patch = black > 0.72
    dark = to_rgb(np.clip(0.10 + (fbm(w, h, 16, 2, rng) - 0.5) * 0.14, 0, 1), "concrete_cold")
    rgb = np.where(patch[..., None], dark, rgb)
    crack = patch & (ep3lib.ridged(fbm(w, h, 8, 2, rng, aspect=0.4)) > 0.90)
    rgb[crack] = col("concrete_cold", 0.36)
    ov = Overlay(w, h)
    for cx, cy, s in ((20, 30, 9), (48, 92, 7)):
        ov.line_tiled([(cx - s * 1.8, cy - s * 0.4), (cx, cy + s * 0.5), (cx + s * 1.8, cy - s * 0.4)],
                      col("concrete_cold", 0.10), 2.6)
        ov.ellipse(cx - 2, cy - 1, cx + 2, cy + 2, fill=col("concrete_cold", 0.12))
    ov.polygon([(40, 52), (52, 50), (51, 56), (41, 57)], fill=col("rust_brown", 0.62))
    ov.line([(40, 51.5), (52, 49.5)], col("plaster_warm", 0.96), 1.0)
    return ov.composite(rgb)


# ================================================================ charred larch
def tex_bark2() -> np.ndarray:
    """Larch trunk after the fire: deep vertical fissures, bark plates
    charred to charcoal with an alligator crackle, reddish bark surviving in
    the fissures' lee, grey ash on the plates."""
    rng = rng_for(2)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    ridge = fbm(w, h, 6, 3, rng, aspect=6.0)
    fissure = ridge < 0.40
    field = 0.30 + (ridge - 0.5) * 0.2 + grain(w, h, rng, 0.03)
    bark = to_rgb(np.clip(field, 0, 1), "rust_brown")
    charred = fbm(w, h, 4, 3, rng) > 0.36
    f1, f2, ident, ox, oy = ep3lib.cells_voronoi(w, h, 8, rng, 0.8)
    coal_t = 0.16 + rng.uniform(-0.04, 0.04, ident.max() + 1)[ident] - oy / 8 * 0.05
    coal = to_rgb(np.clip(coal_t + grain(w, h, rng, 0.02), 0, 1), "concrete_cold")
    coal = np.where(((f2 - f1) < 0.9)[..., None], np.array(col("concrete_cold", 0.04), np.uint8), coal)
    rgb = np.where((charred & ~fissure)[..., None], coal, bark)
    ash = (fbm(w, h, 8, 2, rng) > 0.66) & charred & ~fissure
    rgb = np.where(ash[..., None], blend(rgb, col("concrete_cold", 0.55), np.full((h, w), 0.6)), rgb)
    f = np.where(fissure, 0.20 + ridge * 0.5, 1.0)
    f = f * (1 + (ridge - np.roll(ridge, 1, axis=1)) * 6)
    return shade(rgb, np.clip(f, 0.2, 1.4))


# ================================================================ log cabin
LOG_H = 16
LOG_TONE = 0.46              # plaster_warm: weathered silver-grey timber
KNOTS = ((30, 2), (92, 5))   # (x, log index)


def tex_logw1() -> np.ndarray:
    """Log-cabin wall: round logs 16 px high, weathered to silver-grey
    with a brown core in the checks, moss chinking between them, two
    knots. Tiles in both axes."""
    rng = rng_for(3)
    w, h = 128, 128
    yy, xx = np.mgrid[0:h, 0:w]
    log = yy // LOG_H
    ly = yy % LOG_H
    tone = rng.uniform(-0.04, 0.04, h // LOG_H)[log]
    grainf = fbm(w, h, 4, 3, rng, aspect=0.1)
    field = LOG_TONE + tone + (grainf - 0.5) * 0.16 + grain(w, h, rng, 0.02)
    wood = to_rgb(np.clip(field, 0, 1), "plaster_warm")
    brown = fbm(w, h, 4, 3, rng, aspect=0.2) > 0.58
    wood = np.where(brown[..., None], to_rgb(np.clip(field * 0.62, 0, 1), "rust_brown"), wood)
    f = ep3lib.cylinder((ly - 1) / 12.0)
    check = (ep3lib.ridged(fbm(w, h, 8, 2, rng, aspect=0.08)) > 0.93) & (ly > 3) & (ly < 12)
    f = np.where(check, 0.40, f)
    rgb = shade(wood, f)
    chink = ly >= 13
    moss_t = 0.30 + (fbm(w, h, 16, 2, rng) - 0.5) * 0.25
    moss = to_rgb(np.clip(moss_t, 0, 1), "military_green")
    moss = np.where((fbm(w, h, 8, 2, rng) > 0.55)[..., None], to_rgb(np.clip(moss_t + 0.05, 0, 1), "khaki_olive"), moss)
    moss = shade(moss, np.where(ly == 13, 0.55, 1.0))
    rgb = np.where(chink[..., None], moss, rgb)
    rgb[ly == 0] = shade(rgb[ly == 0], 0.55)
    for kx, li in KNOTS:
        ky = li * LOG_H + 7
        d = np.hypot((xx - kx) / 3.2, (yy - ky) / 2.2)
        rgb[d < 1] = col("rust_brown", 0.16)
        ring = (d >= 1) & (d < 1.8)
        rgb[ring] = col("rust_brown", 0.40)
    return rgb


# ================================================================ peat
PEAT_TONE = 0.22


def tex_peat1() -> np.ndarray:
    """Peat bog: dark brown fibrous peat, tufts of sphagnum, black pools
    holding a little sky."""
    rng = rng_for(4)
    w = h = FLAT
    field = PEAT_TONE + (fbm(w, h, 4, 3, rng) - 0.5) * 0.12 + grain(w, h, rng, 0.03)
    rgb = to_rgb(np.clip(field, 0, 1), "rust_brown")
    for _ in range(140):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(-0.6, 0.6) + (np.pi / 2 if rng.random() < 0.3 else 0)
        ln = rng.uniform(3, 8)
        tone = 0.34 if rng.random() < 0.6 else 0.10
        for k in range(int(ln)):
            rgb[int(y + k * np.sin(a)) % h, int(x + k * np.cos(a)) % w] = col("rust_brown", tone)
    moss_f = fbm(w, h, 6, 3, rng)
    tuft = (moss_f > 0.60) & (rng.random((h, w)) < 0.75)
    moss = to_rgb(np.clip(0.36 + (moss_f - 0.6) * 1.2 + grain(w, h, rng, 0.05), 0, 1), "khaki_olive")
    rgb = np.where(tuft[..., None], moss, rgb)
    pool_f = fbm(w, h, 3, 3, rng)
    pool = pool_f < 0.30
    water = to_rgb(np.clip(0.10 + (0.30 - pool_f) * 0.6 + grain(w, h, rng, 0.02), 0, 1), "steel_blue")
    rgb = np.where(pool[..., None], water, rgb)
    rim = ~pool & (np.roll(pool, 1, 0) | np.roll(pool, -1, 0) | np.roll(pool, 1, 1) | np.roll(pool, -1, 1))
    rgb[rim] = col("rust_brown", 0.08)
    glint = pool & (rng.random((h, w)) < 0.02)
    rgb[glint] = col("steel_blue", 0.45)
    return rgb


# ================================================================ burnt earth
TRUNKS = (((4, 12), (58, 32)), ((36, 44), (90, 64)))   # the fallen, charred trunks, all one way (Tunguska)


def tex_burn1() -> np.ndarray:
    """Scorched earth: grey ash over black char, patches of burnt red
    soil, and charred trunks lying all the same way, as the blast laid
    them down."""
    rng = rng_for(5)
    w = h = FLAT
    field = 0.22 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.18 + grain(w, h, rng, 0.03)
    rgb = to_rgb(np.clip(field, 0, 1), "concrete_cold")
    soil = fbm(w, h, 3, 3, rng) > 0.64
    rgb = np.where(soil[..., None], to_rgb(np.clip(field + 0.08, 0, 1), "rust_brown"), rgb)
    ash = fbm(w, h, 8, 2, rng) > 0.62
    rgb = blend(rgb, col("concrete_cold", 0.50), ash * 0.6)
    char = (rng.random((h, w)) < 0.06)
    rgb[char] = col("concrete_cold", 0.05)
    ov = Overlay(w, h)
    for (x0, y0), (x1, y1) in TRUNKS:
        ov.line_tiled([(x0, y0 + 2), (x1, y1 + 2)], col("concrete_cold", 0.03) + (160,), 6.0)
        ov.line_tiled([(x0, y0), (x1, y1)], col("concrete_cold", 0.08), 5.0)
        ov.line_tiled([(x0, y0 - 1.6), (x1, y1 - 1.6)], col("concrete_cold", 0.30), 1.2)
        for t in np.linspace(0.12, 0.88, 6):
            px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            ov.line_tiled([(px - 0.8, py - 2), (px + 0.8, py + 2)], col("concrete_cold", 0.02), 0.8)
    return ov.composite(rgb)


# ================================================================ moss and lichen
def tex_moss1() -> np.ndarray:
    """Taiga floor: cushions of moss, pale reindeer lichen, a few red
    lingonberries."""
    rng = rng_for(6)
    w = h = FLAT
    f1, f2, ident, ox, oy = ep3lib.cells_voronoi(w, h, 8, rng, 0.9)
    tone = rng.uniform(-0.06, 0.06, ident.max() + 1)[ident]
    kind = rng.random(ident.max() + 1)[ident] < 0.35
    t = 0.38 + tone + grain(w, h, rng, 0.05)
    moss = np.where(kind[..., None], to_rgb(np.clip(t, 0, 1), "khaki_olive"), to_rgb(np.clip(t, 0, 1), "military_green"))
    dome = 1.15 - f1 / 8 * 0.5 - (ox + oy) / 8 * 0.15
    dome = np.where(((f2 - f1) < 1.0) & (fbm(w, h, 4, 2, rng) > 0.4), 0.62, dome)
    dome = dome * (0.85 + 0.3 * fbm(w, h, 2, 2, rng))
    rgb = shade(moss, np.clip(dome, 0.3, 1.3))
    lichen_f = fbm(w, h, 4, 3, rng)
    lichen = (lichen_f > 0.58) & (rng.random((h, w)) < 0.8)
    pale = to_rgb(np.clip(0.66 + (lichen_f - 0.58) * 0.8 + grain(w, h, rng, 0.06), 0, 1), "khaki_olive")
    pale = np.where((rng.random((h, w)) < 0.3)[..., None], to_rgb(np.full((h, w), 0.72), "concrete_cold"), pale)
    rgb = np.where(lichen[..., None], pale, rgb)
    for _ in range(7):
        x, y = int(rng.integers(0, w - 1)), int(rng.integers(0, h - 1))
        rgb[y, x] = col("flag_red", 0.72)
        rgb[y, x + 1] = col("flag_red", 0.50)
        rgb[y + 1, x] = col("flag_red", 0.40)
    return rgb


# ================================================================ alien metal
RIB_PITCH, RIB_HALF = 32, 5
RIB_SWAY = 6.0               # px the ribs sway over the tile height
CABLE_X, CABLE_SWAY, CABLE_R = 64, 9.0, 5.0   # the twisted pair of tubes
ALIEN_TONE = 0.20            # steel_blue: the invaders' dark metal


def tex_alnm1() -> np.ndarray:
    """The invaders' organic metal: a dark membrane sagging between
    vertebral ribs (every 32 px, swaying, knotted every 16 px), veins in it
    faintly lit acid green, and a pair of fleshy tubes twisted round each
    other running down the middle, glowing at their joints."""
    rng = rng_for(7)
    w = h = 128
    yy, xx = np.mgrid[0:h, 0:w]
    mem = ALIEN_TONE + (fbm(w, h, 4, 4, rng) - 0.5) * 0.12 + grain(w, h, rng, 0.02)
    rgb = to_rgb(np.clip(mem, 0, 1), "steel_blue")
    flesh = fbm(w, h, 3, 3, rng) > 0.66
    rgb = np.where(flesh[..., None], to_rgb(np.clip(mem * 0.9, 0, 1), "rust_brown"), rgb)
    vein = ep3lib.ridged(fbm(w, h, 6, 3, rng, aspect=2.5))
    rgb[vein > 0.92] = col("military_green", 0.40)
    rgb[vein > 0.98] = col("military_green", 0.72)
    # the membrane sags between ribs: darker in the middle of each bay
    bay = ep3lib.wrap_dist(xx - 16 - RIB_SWAY * np.sin(2 * np.pi * yy / h), RIB_PITCH) / (RIB_PITCH / 2)
    rgb = shade(rgb, 0.70 + 0.45 * np.abs(bay))
    for k in range(w // RIB_PITCH):
        cx = 16 + RIB_PITCH * k + RIB_SWAY * np.sin(2 * np.pi * yy / h + k * 0.7)
        knot = np.exp(-(ep3lib.wrap_dist(yy + k * 5, 16) ** 2) / 5)
        half = RIB_HALF + 2.2 * knot
        t = ep3lib.wrap_dist(xx - cx, w) / (2 * half) + 0.5
        on = (t >= 0) & (t <= 1)
        rib_t = 0.42 + (fbm(w, h, 8, 2, rng) - 0.5) * 0.08 + grain(w, h, rng, 0.02)
        rib = to_rgb(np.clip(rib_t, 0, 1), "steel_blue")
        rib = np.where((fbm(w, h, 6, 2, rng, aspect=3) > 0.62)[..., None], to_rgb(np.clip(rib_t * 0.9, 0, 1), "rust_brown"), rib)
        rib = shade(rib, ep3lib.cylinder(t) * (1 - 0.35 * (np.abs(ep3lib.wrap_dist(yy + k * 5 - 8, 16)) < 0.8)))
        rgb = np.where(on[..., None], rib, rgb)
        rgb[on & ((t < 0.07) | (t > 0.93))] = col("steel_blue", 0.06)
    for ph in (0.0, np.pi):
        cx = CABLE_X + CABLE_SWAY * np.sin(2 * np.pi * yy / 64 + ph)
        front = np.cos(2 * np.pi * yy / 64 + ph) > 0
        t = (xx - cx + CABLE_R) / (2 * CABLE_R)
        on = (t >= 0) & (t <= 1)
        if ph:
            on &= front | ~prev_on
        shadow = (xx > cx + CABLE_R) & (xx < cx + CABLE_R + 3)
        rgb = np.where((shadow & ~on)[..., None], shade(rgb, 0.55), rgb)
        tube = to_rgb(np.clip(0.30 + grain(w, h, rng, 0.03), 0, 1), "rust_brown")
        tube = shade(tube, ep3lib.cylinder(t, 0.45, 1.35))
        joint = np.abs(ep3lib.wrap_dist(yy + ph * 4, 16)) < 1.0
        tube = np.where(joint[..., None], shade(tube, 0.55), tube)
        rgb = np.where(on[..., None], tube, rgb)
        glow = on & (np.abs(ep3lib.wrap_dist(yy + ph * 4, 32)) < 1.0) & (np.abs(t - 0.45) < 0.3)
        rgb[glow] = col("military_green", 0.90)
        rgb[glow & (np.abs(t - 0.45) < 0.12)] = col("cream_yellow", 0.95)
        prev_on = on
    return rgb


# ================================================================ acid
ACID_TONE = (0.36, 0.62)     # military_green: v1's only green
BUBBLES = 9
DRIFT = FLAT // FRAMES


def acid_frames() -> list[np.ndarray]:
    """Four frames of the invaders' acid: a sluggish green body, crests
    turning hazard yellow, bubbles that swell over the loop and burst, the
    whole drifting one tile per loop (frame 4 leads into frame 1)."""
    rng = rng_for(8)
    w = h = FLAT
    yy, xx = np.mgrid[0:h, 0:w] + 0.5
    body = fbm(w, h, 3, 3, rng, 0.5)
    a, b = fbm(w, h, 4, 4, rng, 0.55), fbm(w, h, 4, 4, rng, 0.55)
    g = grain(w, h, rng, 0.015)
    bubbles = [(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(0, 1), rng.uniform(2.0, 3.6)) for _ in range(BUBBLES)]
    frames = []
    for k in range(FRAMES):
        phi = 2 * np.pi * k / FRAMES
        rip = 0.5 + (a - 0.5) * np.cos(phi) + (b - 0.5) * np.sin(phi)
        ridge = ep3lib.ridged(rip)
        t = ACID_TONE[0] + (ACID_TONE[1] - ACID_TONE[0]) * body + (ridge - 0.5) * 0.14 + g
        rgb = to_rgb(np.clip(t, 0, 1), "military_green")
        rgb = np.where((ridge > 0.94)[..., None], np.array(col("hazard_yellow", 0.62), np.uint8), rgb)
        rgb = np.where((ridge > 0.985)[..., None], np.array(col("cream_yellow", 0.90), np.uint8), rgb)
        for bx, by, ph, rmax in bubbles:
            life = (ph + k / FRAMES) % 1.0
            d = np.hypot(ep3lib.wrap_dist(xx - bx, w), ep3lib.wrap_dist(yy - by, h))
            if life < 0.75:
                r = 0.8 + rmax * life / 0.75
                inside = d < r
                rgb[inside] = shade(rgb[inside], 1.12)
                rgb[(d >= r - 0.9) & (d < r)] = col("military_green", 0.22)
                hx = np.hypot(ep3lib.wrap_dist(xx - bx + r * 0.4, w), ep3lib.wrap_dist(yy - by + r * 0.4, h))
                rgb[hx < 0.75] = col("cream_yellow", 0.96)
            else:
                rr = rmax + 1.2
                rgb[(d >= rr - 0.8) & (d < rr)] = col("hazard_yellow", 0.80)
        frames.append(np.roll(rgb, (k * DRIFT, k * DRIFT // 2), axis=(0, 1)))
    return frames


# ================================================================ glyph plate
GLYPH_YS = (12, 32, 52)      # three glyphs per 64 px panel, clear of its bevels
GLYPH_COLS = (20, 44)
GLYPH_R = 5.0
GLOW = ("military_green", 0.86)


def glyph(ov: Overlay, cx: float, cy: float, rng: np.random.Generator, colour, width: float) -> None:
    """One invader glyph, by a fixed grammar: always a closed ring; inside
    it a dot, a pair of dots or a small ring; two or three ticks on the
    diagonals or the horizontal (never straight up or down, never two
    opposite ones, so no stroke crosses the ring as in Ф or Θ and no ring is
    left open as in C or Э); sometimes a crescent cap above. No letter of
    any alphabet is a closed ring with ticks on the diagonals."""
    r = GLYPH_R
    ov.ellipse(cx - r, cy - r, cx + r, cy + r, outline=colour, width=width)
    inner = int(rng.integers(0, 3))
    if inner == 0:
        ov.ellipse(cx - 1.3, cy - 1.3, cx + 1.3, cy + 1.3, fill=colour)
    elif inner == 1:
        ov.ellipse(cx - 2.8, cy - 0.9, cx - 0.9, cy + 1.0, fill=colour)
        ov.ellipse(cx + 0.9, cy - 0.9, cx + 2.8, cy + 1.0, fill=colour)
    else:
        ov.ellipse(cx - 2.2, cy - 2.2, cx + 2.2, cy + 2.2, outline=colour, width=width * 0.8)
    bearings = [0, 45, 135, 180, 225, 315]
    picks = []
    n_ticks = int(rng.integers(2, 4))
    for bearing in rng.permutation(bearings):
        if len(picks) == n_ticks:
            break
        if any(abs((int(bearing) - p) % 360 - 180) < 1 for p in picks):
            continue
        picks.append(int(bearing))
    for bearing in picks:
        a = np.deg2rad(bearing)
        ov.line([(cx + r * np.cos(a), cy + r * np.sin(a)), (cx + (r + 2.6) * np.cos(a), cy + (r + 2.6) * np.sin(a))],
                colour, width)
    if rng.random() < 0.4:
        ov.arc_ring(cx, cy, r + 3.2, r + 2.0, 220, 320, colour)


def tex_glyp1() -> np.ndarray:
    """A plate of the invaders' technology: dark mottled metal in bevelled
    panels, two columns of glyphs cut into it and glowing acid green (each
    with its engraved shadow), lit channels down both sides. The glyphs are
    a made-up grammar of rings and ticks, not letters."""
    rng = rng_for(9)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    field = ALIEN_TONE + 0.04 + (fbm(w, h, 4, 4, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.02)
    rgb = to_rgb(np.clip(field, 0, 1), "steel_blue")
    mott = fbm(w, h, 6, 3, rng) > 0.70
    rgb = np.where(mott[..., None], to_rgb(np.clip(field * 0.9, 0, 1), "rust_brown"), rgb)
    f = np.ones((h, w))
    f[:, 0] = 0.40
    f[:, 1] *= 1.30
    f[0] = 0.40
    f[1] *= 1.30
    f[64] = 0.40
    f[65] *= 1.30
    for x in (8, 55):
        f[:, x] = 0.45
        f[:, x + 1] *= 1.2
    rgb = shade(rgb, f)
    rgb[4:61, 8] = col("military_green", 0.55)
    rgb[68:125, 8] = col("military_green", 0.55)
    rgb[4:61, 55] = col("military_green", 0.55)
    rgb[68:125, 55] = col("military_green", 0.55)
    shadow = Overlay(w, h)
    glow = Overlay(w, h)
    for gx in GLYPH_COLS:
        for gy in [panel + y for panel in (0, 64) for y in GLYPH_YS]:
            seed = int(rng.integers(0, 2 ** 31))
            glyph(shadow, gx + 1, gy + 1, np.random.default_rng(seed), col("concrete_cold", 0.02), 1.5)
            glyph(glow, gx, gy, np.random.default_rng(seed), col(*GLOW), 1.2)
    rgb = shadow.composite(rgb)
    rgb = glow.composite(rgb)
    lum = rgb.astype(int).sum(-1)
    hot = (lum > np.percentile(lum, 98.5))
    rgb[hot] = col("cream_yellow", 0.92)
    return rgb


# ================================================================ portal rim
CHANNEL = (24, 40)           # the cobalt channel down the middle of the rim
RIM_SEG = 16


def tex_prte1() -> np.ndarray:
    """The portal's rim: a pillar of the invaders' metal in 16 px
    segments, split down the middle by a channel of the portal's cobalt
    with white filaments (SDPORT1-4's look), the glow spilling onto the
    metal and filaments cracking out across it. Symmetric, so it frames
    either side; tiles in y."""
    rng = rng_for(10)
    w, h = 64, 128
    yy, xx = np.mgrid[0:h, 0:w]
    metal_t = 0.30 + (fbm(w, h, 4, 3, rng) - 0.5) * 0.10 + grain(w, h, rng, 0.02)
    metal = to_rgb(np.clip(metal_t, 0, 1), "steel_blue")
    metal = np.where((fbm(w, h, 6, 3, rng) > 0.70)[..., None], to_rgb(np.clip(metal_t * 0.9, 0, 1), "rust_brown"), metal)
    across = np.where(xx < CHANNEL[0], (xx + 0.5) / CHANNEL[0], (xx - CHANNEL[1] + 0.5) / (w - CHANNEL[1]))
    f = ep3lib.cylinder(across)
    seg = yy % RIM_SEG
    f = np.where(seg == 0, 0.45, f)
    f = np.where(seg == 1, f * 1.25, f)
    f = f * (1 - 0.18 * np.exp(-((seg - 8) ** 2) / 10.0))
    rgb = shade(metal, f)
    # the channel: cobalt field with white filaments
    c0, c1 = CHANNEL
    chan = (xx >= c0) & (xx < c1)
    n = fbm(w, h, 4, 4, rng, 0.55, aspect=2.0)
    ct = 0.45 + (n - 0.5) * 0.5
    cobalt = ep3lib.any_to_rgb(np.clip(ct, 0, 1), "mosaic_cobalt")
    fil = ep3lib.ridged(fbm(w, h, 4, 4, rng, 0.6, aspect=3.0))
    cobalt = np.where((fil > 0.90)[..., None], ep3lib.any_to_rgb(np.full((h, w), 0.92), "mosaic_cobalt"), cobalt)
    cobalt = np.where((fil > 0.96)[..., None], np.array((255, 255, 255), np.uint8), cobalt)
    rgb = np.where(chan[..., None], cobalt, rgb)
    # lips of the channel and the glow spilling onto the metal
    dist = np.where(xx < c0, c0 - xx, np.where(xx >= c1, xx - c1 + 1, 0)).astype(float)
    spill = np.clip(1 - dist / 7, 0, 1) * (~chan)
    glowc = ep3lib.any_to_rgb(np.clip(0.30 + spill * 0.35, 0, 1), "mosaic_cobalt")
    rgb = np.where((spill > 0.55)[..., None], glowc, rgb)
    rgb[:, c0 - 1] = ep3lib.any_to_rgb(np.full((h,), 0.85)[:, None], "mosaic_cobalt")[:, 0]
    rgb[:, c1] = ep3lib.any_to_rgb(np.full((h,), 0.85)[:, None], "mosaic_cobalt")[:, 0]
    # filaments cracking out across the metal
    crack_f = ep3lib.ridged(fbm(w, h, 6, 3, rng, 0.6))
    crack = (crack_f > 0.95) & (dist > 0) & (dist < 18) & (fbm(w, h, 4, 2, rng) > 0.45)
    rgb[crack] = ep3lib.any_to_rgb(np.full((h, w), 0.80), "mosaic_cobalt")[crack]
    rgb[crack & (crack_f > 0.985)] = (255, 255, 255)
    for x in (4, 58):
        for y in range(5, h, RIM_SEG):
            ep3lib.rivet(rgb, x, y, "steel_blue", 0.40)
    return rgb


# ================================================================ pieces
PIECES = [
    Piece("SDBARK1", tex_bark1, "wall", (64, 128), ["SDBARK1"], 1, "xy",
          "Birch bark",
          "Birch trunk: chalk-white bark, horizontal lenticels, black cracked patches and the chevron "
          "scars of fallen branches, a strip of bark peeling back to its orange underside.",
          rec_why="Trunks as octagonal sectors with this texture; with SDBARK2 all around, the surviving "
                  "birch stands out."),
    Piece("SDBARK2", tex_bark2, "wall", (64, 128), ["SDBARK2"], 2, "xy",
          "Burnt larch bark",
          "Larch trunk after the fire: deep vertical fissures, plates charred to charcoal with an "
          "alligator crackle, reddish bark surviving in the fissures, grey ash.",
          rec_why="The Tunguska forest is burnt poles: the most repeated texture on the map."),
    Piece("SDLOGW1", tex_logw1, "wall", (128, 128), ["SDLOGW1"], 3, "xy",
          "Log cabin",
          "Cabin wall: round logs 16 px high, weathered to silver-grey with brown showing in the "
          "checks, moss chinking between them and two knots. Tiles in both axes.",
          rec_why="The Kulik expedition's cabin; with SDMOSS1 at its foot."),
    Piece("SDPEAT1", tex_peat1, "flat", (64, 64), ["SDPEAT1"], 4, "xy",
          "Peat",
          "Peat bog: dark brown fibrous peat, tufts of sphagnum and black pools holding a little sky.",
          rec_why="The floor of the epicentre's bog (Tunguska is swamp)."),
    Piece("SDBURN1", tex_burn1, "flat", (64, 64), ["SDBURN1"], 5, "xy",
          "Scorched earth",
          "Scorched earth: grey ash over black char, patches of burnt red soil and charred trunks "
          "all lying the same way, as the blast left them.",
          rec_why="The parallel trunks are the Tunguska detail; align the flat so they point at the portal."),
    Piece("SDMOSS1", tex_moss1, "flat", (64, 64), ["SDMOSS1"], 6, "xy",
          "Moss and lichen",
          "Taiga floor: cushions of moss, pale reindeer lichen and a few red lingonberries.",
          rec_why="For the taiga the blast did not reach; the contrast with SDBURN1 marks the radius."),
    Piece("SDALNM1", tex_alnm1, "wall", (128, 128), ["SDALNM1"], 7, "xy",
          "Organic alien metal",
          "The invaders' organic metal: a dark membrane with veins lit acid green, swaying vertebral ribs "
          "every 32 px and two fleshy tubes crossing them with glowing joints.",
          rec_why="Palette v1 (dark steel_blue, rust, green); neither the portal's cobalt nor the Legion's pink."),
    Piece("SDACID", acid_frames, "flat", (64, 64), [f"SDACID{i}" for i in range(1, FRAMES + 1)], 8, "xy",
          "Green acid (animated, 4 frames)",
          "The invaders' acid in four frames for ANIMDEFS, like SDWATR: a thick green body, crests "
          "turning yellow, bubbles that swell over the loop and burst, a drift of one flat per "
          "loop (frame 4 leads into frame 1).",
          rec_why="8 tics per frame like SDMOLT. v1 has no saturated green: see question 1.",
          scene={"left": "SDALNM1", "right": "SDALNM1", "back": "SDPORT1"}),
    Piece("SDGLYP1", tex_glyp1, "wall", (64, 128), ["SDGLYP1"], 9, "xy",
          "Plate with invader glyphs",
          "A plate of invader technology: dark mottled metal in bevelled panels, two columns of engraved "
          "glyphs glowing acid green (each with its engraved shadow) and lit channels down the sides. The "
          "glyphs are a made-up grammar of rings and ticks: they are not letters.",
          rec_why="64 px panels: tiles in both axes like a wall of plates."),
    Piece("SDPRTE1", tex_prte1, "wall", (64, 128), ["SDPRTE1"], 10, "y",
          "Portal rim",
          "The portal's frame: a pillar of invader metal in 16 px segments split by a channel of the "
          "portal's cobalt with white filaments (SDPORT1-4's look), the glow spilling onto the "
          "metal and filaments cracking it. Symmetric, so it serves either side; tiles in y.",
          palette=2, v2_ramps=("mosaic_cobalt",),
          why_v2="v2's mosaic_cobalt, on the D66 precedent (the portal SDPORT1-4 is cobalt and nothing in the "
                 "world may share its colour): the rim is part of the portal.",
          rec_why="For the lintel, SDALNM1. Set against SDPORT1-4 (approved) it frames it without competing.",
          scene={"left": "SDPRTE1", "right": "SDPRTE1", "back": "SDPORT1", "floor": "SDBURN1", "ceil": None}),
]
SHARED_SEED: dict = {}
PAINT_BOX: dict = {}

ROOM = {"wall": "SDLOGW1", "floor": "SDBURN1", "ceil": None, "light": 0.90, "sky": "night"}
OVERVIEWS = [
    ("The burnt forest", {"left": "SDBARK2", "right": "SDBARK2", "back": "SDBARK1", "floor": "SDBURN1", "ceil": None}),
    ("The cabin in the bog", {"left": "SDLOGW1", "right": "SDLOGW1", "back": "SDLOGW1", "floor": "SDPEAT1",
                                  "ceil": None}),
    ("Before the portal", {"left": "SDALNM1", "right": "SDGLYP1", "back": "SDPORT1", "floor": "SDACID1", "ceil": None}),
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
