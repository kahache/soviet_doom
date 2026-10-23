#!/usr/bin/env python3
"""Soviet Doom V3 B1 - the operations map between levels (ADR 013).

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_ops_map.py                       # work/ only
    .venv/Scripts/python.exe tools/art/gen_ops_map.py --install             # + assets/ and src/lumps/SDOPSCR
    .venv/Scripts/python.exe tools/art/gen_ops_map.py --install --preview   # + the CEO's sheet

The stats screen between two maps is drawn over a stylised map of the USSR
on which a red arrow advances from operation to operation: Zarya-7 -> the
metro -> Tankograd -> the Trans-Siberian -> the Volga dam -> Red Square ->
Novaya Zemlya -> Severomorsk -> Tunguska. The engine does it on its own from
an INTERMISSION SCRIPT, the mechanism of Doom 1's episode maps (gzdoom.pk3
in_epi1.txt..in_epi3.txt; ADR 013 has the reading): every campaign map's
MAPINFO block names it as `exitpic` and `enterpic` ("$SDOPSCR").

What this script writes (one source of truth for the coordinates):

  graphics/SDOPMAP     320x200 background, indexed, palette v2: the USSR
                       (warped around the Urals so the four Ural operations
                       do not sit on one another), rivers, the
                       Trans-Siberian, a 10-degree graticule, the nine
                       operation sites as hollow rings, the state emblem
  graphics/SDOPR02..SDOPR09  the red arrow INTO each map from the one before,
                       RGBA, drawn at its box's top-left (grAb 0,0)
  graphics/SDOPSTAR    a taken site: a red star with a gold rim (grAb centre)
  graphics/SDOPCUR0/1  the pulse on the site just finished (2-frame Animation)
  graphics/SDOPYAH0    "you are here": the blinking gold ring on the next site
                       (the script's Pointer; the engine blinks it)
  SDOPSCR (root lump)  the intermission script itself, src/lumps/SDOPSCR

Text: none on any picture. The stats screen prints the map names and the
figures in the mod's own fonts, in the player's language, as before.

Geography: tools/art/opsmap_geo.py (own approximation, no downloaded data).
The state emblem is the approved geometry (gen_soviet_base.hammer_sickle's
constants, D48/SDSTAR1; artlib.star_points): no font, no system font (D27).
Deterministic: fixed seed, no dither, the same bytes on every machine.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ART_TOOLS = Path(__file__).resolve().parent
PROJECT_ROOT = ART_TOOLS.parents[1]
sys.path.insert(0, str(ART_TOOLS))

import opsmap_geo as geo  # noqa: E402
import palette  # noqa: E402
import v3lib  # noqa: E402

OUT_DIR = PROJECT_ROOT / "work" / "art" / "v3_opsmap"
ASSET_DIR = PROJECT_ROOT / "assets" / "graphics" / "opsmap"
SCRIPT_LUMP = "SDOPSCR"
SCRIPT_PATH = PROJECT_ROOT / "src" / "lumps" / SCRIPT_LUMP
PREVIEW = PROJECT_ROOT / "docs" / "art" / "previews" / "2026-10-23_V3_ops-map-medals.png"

# ------------------------------------------------------------- the screen
WIDTH, HEIGHT = 320, 200             # the intermission's 320x200 space (Screensize)
MAP_BOX = (5, 315, 30, 197)          # x0, x1, y0, y1 the outline is fitted into (the top 30 px
                                     # stay sea: the map name and "Entering" print there)
SEED = 1977                          # the invasion's year (D8), as batch 1
SUPERSAMPLE = 4

# The warp: a radial magnifier centred on the southern Urals, so MAP01-MAP04
# (Zarya-7, the metro, Tankograd, Sverdlovsk: ~400 km apart, 3 px at the
# map's scale) spread to ~12-15 px. Applied to EVERYTHING drawn, so the sites
# stay on their rivers and railway. r' = R * f(r/R), f a cubic with f(0)=0,
# f'(0)=WARP_GAIN, f(1)=1, f'(1)=1: continuous and monotonic (gain < 3).
WARP_CENTRE = (63.0, 55.0)           # deg E, deg N
WARP_GAIN = 2.9
WARP_RADIUS = 58.0                   # screen px

GRATICULE_LON = range(20, 191, 10)
GRATICULE_LAT = range(40, 81, 10)

# --------------------------------------------------------------- colours
_SEA = palette.ramp_colours("mosaic_cobalt")
_LAND = palette.ramp_colours("khaki_olive")
_RED = palette.ramp_colours("flag_red")
_GOLD = palette.ramp_colours("mosaic_gold")
_CREAM = palette.ramp_colours("cream_yellow")
_DARK = palette.ramp_colours("concrete_cold")

SEA_DEEP, SEA_SHELF = 1.2, 2.6       # mosaic_cobalt ramp positions: open sea, near the coast
LAND_LO, LAND_HI = 3.0, 6.0          # khaki_olive ramp positions: lowland relief range
COAST = _LAND[1]
GRID_SEA = _SEA[3]
GRID_LAND = _LAND[2]
RIVER = _SEA[4]
RAIL = _RED[2]
SITE_RING = _CREAM[11]
FRAME = _CREAM[9]
OUTLINE = _DARK[0]                   # near-black contour of every overlay
ROUTE = _RED[13]                     # the red arrow
ROUTE_LIGHT = _RED[15]
STAR_FILL = _RED[13]
STAR_RIM = _GOLD[13]
RING = _GOLD[14]
RING_LIGHT = _GOLD[15]

# ------------------------------------------------------------- overlays
ROUTE_WIDTH = 1.6                    # px, the arrow's red stroke (outline added)
ROUTE_BULGE = 0.18                   # the arrow bows sideways by this share of its length
ROUTE_STOP = 5.0                     # px: the arrowhead's tip stops this short of the site
ARROW_LEN, ARROW_HALF = 4.6, 3.0     # arrowhead length and half width, px
ROUTE_MARGIN = 3                     # px of transparent border round a segment's box
STAR_SIZE, STAR_R = 9, 4.3            # SDOPSTAR canvas and outer radius
RING_SIZE = 17                       # SDOPCUR*/SDOPYAH0 canvas (odd: a centre pixel)
RING_RADII = {"SDOPCUR0": 5.2, "SDOPCUR1": 6.6, "SDOPYAH0": 6.0}
RING_WIDTH = 1.4
CURRENT_PERIOD = 12                  # tics per frame of the pulse (Doom's anims use 11)
SITE_R = 2.6                         # the background's hollow ring per site
EMBLEM_BOX = (15.0, 18.0, 9.0)       # centre x, y and half size of the hammer and sickle
EMBLEM_STAR = (15.0, 6.5, 4.2)       # the star above it


# ------------------------------------------------------------ projection
def _fit():
    pts = [geo.project(*p) for p in geo.USSR]
    for ring in geo.ISLANDS.values():
        pts += [geo.project(*p) for p in ring]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    bx0, bx1, by0, by1 = MAP_BOX
    s = min((bx1 - bx0) / (x1 - x0), (by1 - by0) / (y1 - y0))
    ox = bx0 + ((bx1 - bx0) - (x1 - x0) * s) / 2
    oy = by1 - ((by1 - by0) - (y1 - y0) * s) / 2
    return x0, y0, s, ox, oy


_X0, _Y0, _S, _OX, _OY = _fit()


def _plain(lon: float, lat: float) -> tuple[float, float]:
    x, y = geo.project(lon, lat)
    return _OX + (x - _X0) * _S, _OY - (y - _Y0) * _S


_WCX, _WCY = _plain(*WARP_CENTRE)


def warp_radius(r: float) -> float:
    """The magnifier on a distance from the warp centre (screen px)."""
    if r >= WARP_RADIUS:
        return r
    u = r / WARP_RADIUS
    a = WARP_GAIN
    d = a - 1.0
    c = 1.0 - a - d
    return WARP_RADIUS * (a * u + c * u * u + d * u ** 3)


def to_screen(lon: float, lat: float) -> tuple[float, float]:
    """(lon, lat) -> the 320x200 screen, projection + fit + Ural magnifier."""
    x, y = _plain(lon, lat)
    dx, dy = x - _WCX, y - _WCY
    r = math.hypot(dx, dy)
    if r < 1e-9 or r >= WARP_RADIUS:
        return x, y
    k = warp_radius(r) / r
    return _WCX + dx * k, _WCY + dy * k


def sites() -> dict[str, tuple[int, int]]:
    """Map lump -> its site on the screen, whole pixels (the script's Spots)."""
    return {m: tuple(int(round(v)) for v in to_screen(lon, lat))
            for m, _, lon, lat in geo.OPERATIONS}


MAPS = tuple(m for m, *_ in geo.OPERATIONS)


def _densify(ring, step=0.5):
    """More vertices along each edge so the warp bends straight edges."""
    out = []
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        for j in range(k):
            t = j / k
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def _densify_line(line, step=0.5):
    """`_densify` for an open polyline (no closing edge)."""
    out = []
    for a, b in zip(line, line[1:]):
        k = max(1, int(math.hypot(b[0] - a[0], b[1] - a[1]) / step))
        out += [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k) for j in range(k)]
    return out + [line[-1]]


# ------------------------------------------------------------ background
def land_mask():
    """(H, W) float coverage of the land at 1x (supersampled polygons)."""
    import numpy as np
    from PIL import Image, ImageDraw
    s = SUPERSAMPLE
    im = Image.new("L", (WIDTH * s, HEIGHT * s), 0)
    d = ImageDraw.Draw(im)
    for ring in [geo.USSR] + list(geo.ISLANDS.values()):
        d.polygon([(x * s, y * s) for x, y in (to_screen(*p) for p in _densify(ring))], fill=255)
    for ring in geo.LAKES.values():
        d.polygon([(x * s, y * s) for x, y in (to_screen(*p) for p in _densify(ring))], fill=0)
    small = im.resize((WIDTH, HEIGHT), Image.Resampling.BOX)
    return np.asarray(small, dtype=np.float64) / 255.0


def _stroke_mask(lines, width=1.0, dash=None):
    """(H, W) bool of 1x strokes along lon/lat polylines (optionally dashed:
    dash = (on, off) in px along the line)."""
    import numpy as np
    from PIL import Image, ImageDraw
    s = SUPERSAMPLE
    im = Image.new("L", (WIDTH * s, HEIGHT * s), 0)
    d = ImageDraw.Draw(im)
    for line in lines:
        pts = [to_screen(*p) for p in _densify_line(list(line), 0.25)]
        if dash is None:
            d.line([(x * s, y * s) for x, y in pts], fill=255, width=max(1, int(width * s)))
            continue
        on, off = dash
        run = 0.0
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            seg = math.hypot(xb - xa, yb - ya)
            if (run % (on + off)) < on:
                d.line([(xa * s, ya * s), (xb * s, yb * s)], fill=255, width=max(1, int(width * s)))
            run += seg
    small = im.resize((WIDTH, HEIGHT), Image.Resampling.BOX)
    return np.asarray(small, dtype=np.float64) >= 255 * 0.45


def _ramp_pick(ramp, pos):
    """Colour array for float ramp positions (rounded)."""
    import numpy as np
    arr = np.array(ramp, dtype=np.float64)
    return arr[np.clip(np.round(pos).astype(int), 0, len(ramp) - 1)]


def _blur(a, radius):
    import numpy as np
    from PIL import Image, ImageFilter
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "L")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float64) / 255.0


def emblem_layer():
    """The state emblem, top left over the Norwegian Sea: the approved
    hammer and sickle in gold under a red star. RGBA PIL, 1x size."""
    from PIL import Image, ImageDraw
    import gen_soviet_base as g
    s = 8
    big = Image.new("RGBA", (WIDTH * s, HEIGHT * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy, r = EMBLEM_BOX
    x0, y0, side = cx - r, cy - r, 2 * r

    def P(pt):
        return ((x0 + pt[0] * side) * s, (y0 + pt[1] * side) * s)

    def arc(c, rad, a0, a1, steps=48):
        return [(c[0] + rad * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
                 c[1] + rad * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]

    def bar(p0, p1, w):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = math.hypot(dx, dy)
        nx, ny = -dy / n * w / 2, dx / n * w / 2
        return [(p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny), (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)]

    gold = _GOLD[13] + (255,)
    blade = [tuple(g.SICKLE_TIP)] + arc(g.SICKLE_OUTER_C, g.SICKLE_OUTER_R, g.SICKLE_TIP_OUTER_DEG, g.SICKLE_BASE_DEG) \
        + arc(g.SICKLE_INNER_C, g.SICKLE_INNER_R, g.SICKLE_TIP_INNER_DEG, g.SICKLE_BASE_DEG)[::-1]
    d.polygon([P(p) for p in blade], fill=gold)
    d.polygon([P(p) for p in bar(*g.SICKLE_HANDLE, g.SICKLE_HANDLE_W)], fill=gold)
    hs, he = g.HAMMER_HANDLE
    d.polygon([P(p) for p in bar(hs, he, g.HAMMER_HANDLE_W)], fill=gold)
    dx, dy = he[0] - hs[0], he[1] - hs[1]
    n = math.hypot(dx, dy)
    hd = (dx / n, dy / n)
    hn = (-hd[1], hd[0])
    c, hl, hw = g.HAMMER_HEAD_C, g.HAMMER_HEAD_L / 2, g.HAMMER_HEAD_W / 2
    head = [(c[0] + sa * hn[0] * hl + sb * hd[0] * hw, c[1] + sa * hn[1] * hl + sb * hd[1] * hw)
            for sa, sb in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    d.polygon([P(p) for p in head], fill=gold)
    sx, sy, sr = EMBLEM_STAR
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = sr if i % 2 == 0 else sr * 0.382
        pts.append(((sx + rr * math.cos(a)) * s, (sy + rr * math.sin(a)) * s))
    d.polygon(pts, fill=_RED[13] + (255,))
    return v3lib.sprite_from_rgba(big, (WIDTH, HEIGHT))


def render_background():
    """-> (H, W, 3) uint8 in palette v2: the map without any overlay."""
    import numpy as np
    rng = np.random.default_rng(SEED)
    land = land_mask()
    is_land = land >= 0.5
    # value noise for the relief and the sea's swell (smooth: upsampled)
    from PIL import Image

    def noise(cells_x, cells_y):
        base = rng.random((cells_y, cells_x))
        im = Image.fromarray((base * 255).astype(np.uint8), "L").resize((WIDTH, HEIGHT), Image.Resampling.BICUBIC)
        return np.asarray(im, dtype=np.float64) / 255.0

    relief = 0.6 * noise(20, 13) + 0.4 * noise(48, 30)
    swell = noise(16, 10)
    shelf = _blur(land, 3.0)                                  # brighter water near the coasts
    sea_pos = SEA_DEEP + (SEA_SHELF - SEA_DEEP) * np.clip(shelf * 1.6, 0, 1) + 0.6 * (swell - 0.5)
    land_pos = LAND_LO + (LAND_HI - LAND_LO) * relief
    rgb = np.where(is_land[..., None], _ramp_pick(_LAND, land_pos), _ramp_pick(_SEA, sea_pos))

    # graticule: dotted, every 10 degrees
    lines = [[(lon, lat / 2.0) for lat in range(70, 165)] for lon in GRATICULE_LON]
    lines += [[(lon / 2.0, lat) for lon in range(30, 385)] for lat in GRATICULE_LAT]
    grid = _stroke_mask(lines, 1.0, dash=(1.0, 2.0))
    rgb[grid & ~is_land] = GRID_SEA
    rgb[grid & is_land] = GRID_LAND
    # rivers, then the railway (dashed: sleepers)
    rivers = _stroke_mask(list(geo.RIVERS.values()), 1.0) & is_land
    rgb[rivers] = RIVER
    rail = _stroke_mask([geo.TRANS_SIBERIAN], 1.0, dash=(3.0, 1.0)) & is_land
    rgb[rail] = RAIL
    # the coast: one dark pixel on the land side of every land/sea edge
    edge = np.zeros_like(is_land)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        edge |= is_land & ~np.roll(np.roll(is_land, dy, axis=0), dx, axis=1)
    rgb[edge] = COAST
    # the nine sites: hollow cream rings with a dark core
    s = sites()
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    for (x, y) in s.values():
        r = np.hypot(xx - x, yy - y)
        rgb[(r <= SITE_R + 0.9)] = OUTLINE
        rgb[(r >= SITE_R - 0.6) & (r <= SITE_R + 0.3)] = SITE_RING
    # a frame: a cream line 1 px in from the dark edge
    rgb[0, :] = rgb[-1, :] = OUTLINE
    rgb[:, 0] = rgb[:, -1] = OUTLINE
    rgb[1, 1:-1] = rgb[-2, 1:-1] = FRAME
    rgb[1:-1, 1] = rgb[1:-1, -2] = FRAME
    # the emblem
    em = np.asarray(emblem_layer())
    on = em[..., 3] == 255
    grown = on.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            grown |= np.roll(np.roll(on, dy, axis=0), dx, axis=1)
    rgb[grown & ~on] = OUTLINE
    rgb[on] = em[on, :3]
    return v3lib.snap(rgb.astype(np.uint8))


def background_png() -> bytes:
    """The background as an indexed PNG (mode P, the palette's own order)."""
    import numpy as np
    from PIL import Image
    rgb = render_background()
    pal = [tuple(c) for c in palette.colours(v3lib.PALETTE_VERSION)]
    index = {c: i for i, c in enumerate(pal)}
    idx = np.vectorize(lambda r, g, b: index[(r, g, b)], otypes=[np.uint8])(rgb[..., 0], rgb[..., 1], rgb[..., 2])
    img = Image.fromarray(idx, "P")
    flat = [v for c in pal for v in c]
    img.putpalette(flat + [0] * (768 - len(flat)))
    return v3lib.png_bytes(img)


# --------------------------------------------------------------- overlays
def _contour(img):
    """Add a 1 px OUTLINE ring round the opaque pixels of an RGBA image."""
    import numpy as np
    from PIL import Image
    arr = np.asarray(img).copy()
    on = arr[..., 3] == 255
    grown = on.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            grown |= np.roll(np.roll(on, dy, axis=0), dx, axis=1)
    ring = grown & ~on
    arr[ring, :3] = OUTLINE
    arr[ring, 3] = 255
    return Image.fromarray(arr, "RGBA")


def route_curve(a, b, steps=48):
    """The arrow's centre line from site a to site b: a quadratic bow, ending
    ROUTE_STOP short of b. Returns screen points."""
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length                       # bow to the left of travel
    cx, cy = (ax + bx) / 2 + nx * length * ROUTE_BULGE, (ay + by) / 2 + ny * length * ROUTE_BULGE
    pts = []
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * ax + 2 * (1 - t) * t * cx + t * t * bx
        y = (1 - t) ** 2 * ay + 2 * (1 - t) * t * cy + t * t * by
        pts.append((x, y))
    # trim the start (leave the site's star visible) and the end (the head)
    start_gap = STAR_R + 0.5
    out = [p for p in pts if math.hypot(p[0] - ax, p[1] - ay) >= start_gap
           and math.hypot(p[0] - bx, p[1] - by) >= ROUTE_STOP]
    return out


def route_segment(a, b):
    """-> (RGBA PIL image, (left, top)): the arrow into site b from site a."""
    from PIL import Image, ImageDraw
    pts = route_curve(a, b)
    tip_dir = (pts[-1][0] - pts[-4][0], pts[-1][1] - pts[-4][1])
    n = math.hypot(*tip_dir)
    ux, uy = tip_dir[0] / n, tip_dir[1] / n
    tx, ty = pts[-1][0] + ux * (ARROW_LEN * 0.55), pts[-1][1] + uy * (ARROW_LEN * 0.55)
    bx_, by_ = tx - ux * ARROW_LEN, ty - uy * ARROW_LEN
    head = [(tx, ty), (bx_ - uy * ARROW_HALF, by_ + ux * ARROW_HALF), (bx_ + uy * ARROW_HALF, by_ - ux * ARROW_HALF)]
    xs = [p[0] for p in pts + head]
    ys = [p[1] for p in pts + head]
    left = int(math.floor(min(xs))) - ROUTE_MARGIN
    top = int(math.floor(min(ys))) - ROUTE_MARGIN
    w = int(math.ceil(max(xs))) + ROUTE_MARGIN - left + 1
    h = int(math.ceil(max(ys))) + ROUTE_MARGIN - top + 1
    s = SUPERSAMPLE * 2
    big = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    P = [((x - left) * s, (y - top) * s) for x, y in pts]
    d.line(P, fill=ROUTE + (255,), width=int(ROUTE_WIDTH * s), joint="curve")
    d.polygon([((x - left) * s, (y - top) * s) for x, y in head], fill=ROUTE + (255,))
    img = _contour(v3lib.sprite_from_rgba(big, (w, h)))
    return img, (left, top)


def star_marker():
    from PIL import Image, ImageDraw
    s = SUPERSAMPLE * 2
    c = STAR_SIZE / 2
    big = Image.new("RGBA", (STAR_SIZE * s, STAR_SIZE * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)

    def pts(r):
        out = []
        for i in range(10):
            a = math.radians(-90 + i * 36)
            rr = r if i % 2 == 0 else r * 0.42
            out.append(((c + rr * math.cos(a)) * s, (c + rr * math.sin(a)) * s))
        return out
    d.polygon(pts(STAR_R), fill=STAR_RIM + (255,))
    d.polygon(pts(STAR_R - 1.3), fill=STAR_FILL + (255,))
    img = v3lib.sprite_from_rgba(big, (STAR_SIZE, STAR_SIZE))
    return _contour(img), (STAR_SIZE // 2, STAR_SIZE // 2)


def ring_marker(radius):
    from PIL import Image, ImageDraw
    s = SUPERSAMPLE * 2
    c = RING_SIZE / 2
    big = Image.new("RGBA", (RING_SIZE * s, RING_SIZE * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    ro, ri = radius + RING_WIDTH / 2, radius - RING_WIDTH / 2
    d.ellipse([(c - ro) * s, (c - ro) * s, (c + ro) * s, (c + ro) * s], fill=RING + (255,))
    d.ellipse([(c - ri) * s, (c - ri) * s, (c + ri) * s, (c + ri) * s], fill=(0, 0, 0, 0))
    img = v3lib.sprite_from_rgba(big, (RING_SIZE, RING_SIZE))
    return _contour(img), (RING_SIZE // 2, RING_SIZE // 2)


def overlays() -> dict[str, tuple[object, tuple[int, int], tuple[int, int] | None]]:
    """lump -> (RGBA image, position on screen or None, grAb)."""
    s = sites()
    out = {}
    for i in range(1, len(MAPS)):
        img, (left, top) = route_segment(s[MAPS[i - 1]], s[MAPS[i]])
        out[route_lump(MAPS[i])] = (img, (left, top), (0, 0))
    img, grab = star_marker()
    out["SDOPSTAR"] = (img, None, grab)
    for lump, radius in RING_RADII.items():
        img, grab = ring_marker(radius)
        out[lump] = (img, None, grab)
    return out


def route_lump(map_name: str) -> str:
    return "SDOPR" + map_name[-2:]


# ----------------------------------------------------------- the script
def script_text() -> str:
    """The intermission script (the in_epi*.txt language of gzdoom.pk3).

    State semantics (DInterBackground::drawBackground, ADR 013):
      IfLeaving M   drawn on the STATS page when the map just finished is M
      IfEntering M  drawn on the ENTERING page when the next map is M
    The two never overlap ("mutually exclusive", in_epi2.txt), so every
    picture that must show on both pages is listed twice. Progress is told
    by the map being left or entered, never by the engine's "visited" flag:
    a player who starts episode 2 from New Game still sees the road from
    Zarya-7 as travelled, which is the story.
    """
    s = sites()
    ov = overlays()
    lines = [
        "// SDOPSCR - the operations map between levels (V3 B1, ADR 013).",
        "// GENERATED by tools/art/gen_ops_map.py: do not edit by hand, run it",
        "// with --install. Named by every campaign map's exitpic/enterpic in",
        "// MAPINFO; the language is gzdoom.pk3's in_epi1.txt..in_epi3.txt.",
        "",
        "Background SDOPMAP",
        "Screensize %d %d" % (WIDTH, HEIGHT),
        "// The engine draws the splat on every VISITED site of the entering",
        "// page; ours is the same red star the script draws, so it adds nothing",
        "// but keeps the engine from drawing a missing picture.",
        "Splat SDOPSTAR",
        "Pointer SDOPYAH0",
        "",
        "Spots",
        "{",
    ]
    lines += ["\t%s %d %d" % (m, *s[m]) for m in MAPS]
    lines += ["}", "", "// The red arrow into each map: on the stats page of that map and every",
              "// later one, and on the entering page of that map and every later one."]
    for i in range(1, len(MAPS)):
        lump = route_lump(MAPS[i])
        _, (left, top), _ = ov[lump]
        for later in MAPS[i:]:
            lines.append("IfLeaving %s Pic %d %d %s" % (later, left, top, lump))
        for later in MAPS[i:]:
            lines.append("IfEntering %s Pic %d %d %s" % (later, left, top, lump))
    lines += ["", "// A taken site: from the stats page of its own map on, and on the",
              "// entering page of every later map."]
    for i, m in enumerate(MAPS):
        x, y = s[m]
        for later in MAPS[i:]:
            lines.append("IfLeaving %s Pic %d %d SDOPSTAR" % (later, x, y))
        for later in MAPS[i + 1:]:
            lines.append("IfEntering %s Pic %d %d SDOPSTAR" % (later, x, y))
    lines += ["", "// Where the player is: the gold pulse on the site just finished.",
              "// (On the entering page the engine blinks the Pointer on the next one.)"]
    for m in MAPS:
        x, y = s[m]
        lines.append("IfLeaving %s Animation %d %d %d" % (m, x, y, CURRENT_PERIOD))
        lines.append("{")
        lines.append("\tSDOPCUR0")
        lines.append("\tSDOPCUR1")
        lines.append("}")
    return "\n".join(lines) + "\n"


# ------------------------------------------------- reading a script back
def parse_script(text: str) -> dict:
    """The subset of the intermission-script language gzdoom's
    DInterBackground::LoadBackground reads that this project uses:
    Background, Screensize, Splat, Pointer, Spots { MAP x y }, and
    [IfLeaving|IfEntering|IfVisited M] Pic x y LUMP / Animation x y period
    [ONCE] { frames }. -> dict with keys background, size, splat, pointer,
    spots {map: (x, y)}, anims [(condition, map, kind, x, y, [frames])]."""
    import re
    body = re.sub(r"//[^\n]*", "", text)
    tok = re.findall(r"\{|\}|[^\s{}]+", body)
    out = {"background": None, "size": None, "splat": None, "pointer": [], "spots": {}, "anims": []}
    i = 0

    def take():
        nonlocal i
        i += 1
        return tok[i - 1]
    while i < len(tok):
        word = take()
        low = word.lower()
        if low == "background":
            out["background"] = take()
        elif low == "screensize":
            out["size"] = (int(take()), int(take()))
        elif low == "splat":
            out["splat"] = take()
        elif low == "pointer":
            while i < len(tok) and tok[i].lower() not in KEYWORDS:
                out["pointer"].append(take())
        elif low == "spots":
            assert take() == "{"
            while tok[i] != "}":
                m = take()
                out["spots"][m.upper()] = (int(take()), int(take()))
            take()
        elif low in ("ifleaving", "ifentering", "ifvisited", "pic", "animation"):
            cond, cmap = None, None
            if low.startswith("if"):
                cond, cmap = low, take().upper()
                low = take().lower()
            x, y = int(take()), int(take())
            if low == "pic":
                out["anims"].append((cond, cmap, "pic", x, y, [take()]))
            elif low == "animation":
                take()                                   # period
                if tok[i].lower() == "once":
                    take()
                assert take() == "{"
                frames = []
                while tok[i] != "}":
                    frames.append(take())
                take()
                out["anims"].append((cond, cmap, "animation", x, y, frames))
            else:
                raise ValueError("Pic or Animation expected after a condition, got %r" % low)
        else:
            raise ValueError("unknown intermission script word %r" % word)
    return out


KEYWORDS = {"background", "screensize", "splat", "pointer", "spots", "ifleaving", "ifentering",
            "ifvisited", "ifnotvisited", "ifnotleaving", "ifnotentering", "iftravelling",
            "ifnottravelling", "animation", "pic", "noautostartmap", "tilebackground"}


def visible(parsed: dict, page: str, current: str, nxt: str, visited=(), pointer_on=True, frame=0):
    """What the engine draws, in order, as [(lump, x, y)] (positions before
    the picture's offsets). page: "stats" (the engine's StatCount) or
    "entering" (ShowNextLoc). Mirrors drawBackground: the anims in file
    order, then on the entering page the splat on every visited site and
    the pointer on the next one."""
    out = [(parsed["background"], 0, 0)]
    for cond, cmap, kind, x, y, frames in parsed["anims"]:
        if cond == "ifleaving" and (page != "stats" or cmap != current):
            continue
        if cond == "ifentering" and (page == "stats" or cmap != nxt):
            continue
        if cond == "ifvisited" and cmap not in visited:
            continue
        out.append((frames[frame % len(frames)] if kind == "animation" else frames[0], x, y))
    if page == "entering":
        for m in visited:
            if m in parsed["spots"]:
                out.append((parsed["splat"], *parsed["spots"][m]))
        if pointer_on and nxt in parsed["spots"]:
            out.append((parsed["pointer"][0], *parsed["spots"][nxt]))
    return out


# ------------------------------------------------------------- building
def build(out_dir: Path = OUT_DIR) -> dict[str, bytes]:
    """Write every lump to out_dir; -> {file name: bytes} (PNGs and the script)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    blobs = {"SDOPMAP.png": background_png()}
    for lump, (img, _, grab) in overlays().items():
        blobs[f"{lump}.png"] = v3lib.png_bytes(img, grab)
    blobs[SCRIPT_LUMP] = script_text().encode("ascii")
    for name, blob in blobs.items():
        (out_dir / name).write_bytes(blob)
    return blobs


def install(blobs: dict[str, bytes], asset_dir: Path = ASSET_DIR, script_path: Path = SCRIPT_PATH) -> None:
    asset_dir.mkdir(parents=True, exist_ok=True)
    for name, blob in blobs.items():
        if name == SCRIPT_LUMP:
            script_path.write_bytes(blob)
        else:
            (asset_dir / name).write_bytes(blob)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--install", action="store_true",
                    help="also copy the pictures to assets/graphics/opsmap/ and the script to src/lumps/")
    ap.add_argument("--preview", action="store_true", help="also write the CEO's sheet in docs/art/previews/")
    args = ap.parse_args()
    blobs = build()
    print(f"wrote {len(blobs)} files to {OUT_DIR}")
    if args.install:
        install(blobs)
        print(f"installed into {ASSET_DIR} and {SCRIPT_PATH}")
    if args.preview:
        import opsmap_preview
        opsmap_preview.write_sheet(PREVIEW)
        print(f"wrote {PREVIEW}")


if __name__ == "__main__":
    main()
