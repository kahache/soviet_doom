"""The D12 symbol painted INTO the armband at the Gemini sheet's resolution (D105, option 1).

    python tools/art/armband_symbol.py compare     # the CEO's comparison PNG (rifleman, 4 frames)

The CEO saw the first proposal (gemini_enemy.py `armband`) and judged a
symbol stamped at sprite size unnatural: "lo suyo seria editar bien con
Photoshop". This module is that edit, done by code, on the Gemini figure
BEFORE the pipeline reduces it, so the reduction integrates the symbol like
every other detail Gemini drew:

  1. find_fields     - the armband's white field (gemini_enemy.armband_fields;
                       a field seen edge-on, too grey for it, by a looser
                       white near the band's red)
  2. arm_frame       - the arm as a cylinder: its axis from the figure's
                       long axis (or a hint), its radius and centre from the
                       band's extent across it, the band's own edge (a
                       quadratic) for the tilt and the curve of the band
  3. coverage        - the symbol as a vector (ge.SYMBOL's 5x5 grid, the
                       approved sprite's handedness, never mirrored), tilted
                       TILT_DEG as the historical one, reaching SYMBOL_REACH
                       of the field's radius; every pixel super-sampled
                       SUPERSAMPLE x SUPERSAMPLE, its position round the arm
                       read as arcsin (the far side crowds together), clipped
                       to the field
  4. soften          - the coverage blurred to the edge softness Gemini's own
                       field edge has (edge_sigma, measured per figure)
  5. paint           - Gemini's own black (the figure's darkest decile) times
                       the field's luminance (multiply: the field's light and
                       folds stay), plus the grain Gemini's dark areas carry
                       (grain_sigma), seeded

Then the pipeline reduces the figure as usual (gemini_enemy.render).
Wired since D108 ("la mezcla"): gemini_enemy.source_picture calls
`apply_symbol` AFTER the mirror and before the black plate, the tilt and
the downscale, so a mirrored rotation (6-8) gets the symbol the right way
round; `select_fields` finds each enemy's fields (white, box, plain, ring);
`add_symbol_arg` gives its CLI `--symbol spec|none|warp` (default spec: the
Reich's EnemySpec.symbol is warp). Option 2 (Fooocus) for the close
pictures: `prepare_field` (the crop, its start drawn with this module's own
bent symbol, the mask, the template), `score_repaint`/`pick_seed` (the
objective pick), `patch_from`, `write_cache`, `apply_fooocus` (the build
reads the cache, never SDXL). Nothing here writes the overlay, the review
sheet or assets/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402
import gemini_enemy as ge  # noqa: E402

ROOT = artlib.PROJECT_ROOT
COMPARE_PNG = ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_armband-option1.png"
WORK_DIR = ROOT / "work" / "art" / "armband_test"
FOOOCUS_DIR = ROOT / "work" / "art" / "armband_fooocus"
FOOOCUS_CACHE = FOOOCUS_DIR / "cache"     # option 2's chosen repaints (gitignored work/, D77)

SYMBOL_MODES = ("none", "warp")
DEFAULT_SYMBOL = "none"      # apply_symbol's default: a picture is never painted unless asked
CLI_SYMBOL = ("spec",) + SYMBOL_MODES   # `spec`: each enemy's own (EnemySpec.symbol: warp on the Reich, D108)
TILT_DEG = 45.0              # the historical symbol stands on a point on its disc
SYMBOL_REACH = 0.82          # x the field's radius: how far the tips reach (corner of the tilted grid)
SUPERSAMPLE = 8              # sub-samples per pixel side: the vector's own antialiasing
BOX_SIGMA = 0.29             # the softness a 1-px box (the super-sampling) already gives
SIGMA_MIN, SIGMA_MAX = 0.35, 1.2   # the measured edge softness is clamped to this
EDGE_LO, EDGE_HI = 0.2, 0.8        # an edge pixel is between these of the red-to-white step
EDGE_SPAN_20_80 = 1.68             # a gaussian edge's 20-80 % width, in sigmas
GRAIN_DARK = 60              # luminance under which a figure pixel is "dark" (the grain sample)
GRAIN_MAX = 12.0             # the measured grain is clamped to this (in 0-255)
INK_DECILE = 10              # percentile of the figure's luminance that is Gemini's black
FIELD_REF_PCT = 90           # percentile of the field's luminance that is its full white
LOOSE_WHITE = 85             # an edge-on field (front view) is this grey in its darkest channel
LOOSE_SPREAD = 90            # ... and this unsaturated
FIELD_GROW = 3               # px the field grows into its greyer, shaded part
BAND_PAD = 3                 # px round the band box searched for the band's pixels
EDGE_MIN_COLS = 4            # bins across the band needed to fit its edge
CURVE_MAX = 0.08             # |quadratic| of the band's edge allowed (a bad fit is flattened)
SLOPE_MAX = 0.6              # |slope| of the band's edge allowed
CUT_FIELD = 1.8              # x the radius: a field narrower on the surface, reaching the arm's
SILHOUETTE_PX = 1.5          # ... edge (within this, px), is cut by the silhouette: part of it is behind
R_MIN = 2.0                  # px: the smallest arm radius
LUM = np.array([0.299, 0.587, 0.114])


# ------------------------------------------------------------------ CLI hook
def add_symbol_arg(ap: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """`--symbol spec|none|warp` for gemini_enemy's CLI; default spec (each enemy's own)."""
    ap.add_argument("--symbol", choices=CLI_SYMBOL, default="spec",
                    help="the D12 symbol on the armband: spec (default: each enemy's own, warp on the "
                         "Reich since D108), none (every enemy off) or warp (every enemy that has a field)")
    return ap


# --------------------------------------------------------------- 1. fields
def lum(rgb: np.ndarray) -> np.ndarray:
    return rgb.astype(np.float64) @ LUM


def _erode(mask: np.ndarray, r: int = 1) -> np.ndarray:
    for _ in range(r):
        mask = mask & ~ge.neighbours8(~mask)
    return mask


def _band_mask(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return (ge.red_mask(rgb, ge.MARKER_RED_MIN) | ge.white_mask(rgb, LOOSE_WHITE)) & mask


def find_fields(rgb: np.ndarray, mask: np.ndarray) -> list[np.ndarray]:
    """Bool masks of the armband's white fields. gemini_enemy's strict test
    first; with none, a looser white touching the band's red (a field seen
    edge-on at the arm's silhouette, greyer)."""
    boxes = ge.armband_fields(rgb, mask)
    white = mask & ge.white_mask(rgb)
    a = rgb.astype(np.int32)
    loose = mask & (a.min(axis=-1) > LOOSE_WHITE) & (a.max(axis=-1) - a.min(axis=-1) < LOOSE_SPREAD)
    if not boxes:
        white = loose
        near_red = ge._dilate(ge.red_mask(rgb) & mask, ge.ARMBAND_NEAR)
        lab, n = ge.label(ge._dilate(white, ge.FIELD_GAP))     # a sliver broken in pieces is one field
        boxes = []
        for i in range(1, n + 1):
            blob = (lab == i) & white
            if blob.sum() >= ge.MIN_FIELD and (blob & near_red).any():
                ys, xs = np.nonzero(blob)
                boxes.append((int(ys.min()), int(xs.min()), int(ys.max()) + 1, int(xs.max()) + 1))
    out = []
    for y0, x0, y1, x1 in boxes:
        f = np.zeros(mask.shape, bool)
        f[y0:y1, x0:x1] = white[y0:y1, x0:x1]
        for _ in range(FIELD_GROW):               # the field in the arm's shade is greyer: still the field
            f |= ge.neighbours8(f) & loose
        out.append(f)
    return out


FIELD_MODES = ("white", "box", "plain", "ring")
FIELD_MAX = 20               # source px: a field longer is not an armband's (smoke, a flash, a coat)
PLAIN_TOL = 0                # `plain`: a field pixel is ge.PATCH_RGB exactly (painted; the General's cream coat is close)
SYMBOL_MIN_PX = 10           # a field smaller holds no symbol (edge-on, a spark)
PURITY_MIN = 0.5             # a field's box this much white or red (a pale highlight is mostly something else)
RING_W = 3                   # `ring`: px of the white wall round the red patch the General's ring encloses
RING_WHITE = 0.5             # ... at least this much of that ring white
RING_MIN_PX = 40             # ... and the red patch this big (a medal's ribbon is smaller)
RING_PURE = 180              # ... painted the mean of its wall's pixels this white in every channel (not the pink rim)
BAND_RING = 2                # px round a field whose figure pixels ...
BAND_RED = 0.2               # ... are at least this much red: it sits ON the band (sparks, glows do not)
FLAG_WINDOW = 0.5            # `ring`: x the field's size, the margin searched for a flag's blue


def _box(f: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(f)
    return int(ys.min()), int(xs.min()), int(ys.max()) + 1, int(xs.max()) + 1


def _is_armband(rgb: np.ndarray, mask: np.ndarray, f: np.ndarray, field_max: int,
                window: float = 1.0, purity: bool = True) -> bool:
    """A field the symbol may go on: no longer than `field_max`, its box mostly
    white or red (ge.field_purity; not for a `white` field, whose grey edge-on
    part brings the coat into its box), BAND_RING px round it at least BAND_RED
    red (it sits on the band), no US flag's blue within `window` x its size round it."""
    if f.sum() < SYMBOL_MIN_PX:
        return False
    y0, x0, y1, x1 = _box(f)
    g = max(y1 - y0, x1 - x0)
    if g > field_max or (purity and ge.field_purity(rgb, mask, (y0, x0, y1, x1)) < PURITY_MIN):
        return False
    ring = ge._dilate(f, BAND_RING) & ~f & mask
    if not ring.any() or float((ge.red_mask(rgb, ge.MARKER_RED_MIN) & ring).sum()) < BAND_RED * float(ring.sum()):
        return False
    m = int(math.ceil(window * g))
    gy0, gx0 = max(0, y0 - m), max(0, x0 - m)
    return ge.blue_frac(rgb[gy0:y1 + m, gx0:x1 + m], mask[gy0:y1 + m, gx0:x1 + m]) < ge.PATCH_FLAG_BLUE


def _plain(rgb: np.ndarray, mask: np.ndarray) -> list[np.ndarray]:
    px = (np.abs(rgb.astype(np.int32) - np.array(ge.PATCH_RGB)).max(axis=-1) <= PLAIN_TOL) & mask
    lab, n = ge.label(px)
    return [f for f in (lab == i for i in range(1, n + 1)) if f.sum() >= ge.MIN_FIELD]


def _rings(rgb: np.ndarray, mask: np.ndarray, fmax: int) -> tuple[np.ndarray, list[np.ndarray]]:
    """`ring`: a red patch walled in by white (the General's square ring
    on his band: RING_WHITE of the RING_W-px ring round it is white) becomes
    one plain field with its wall, the red painted the wall's mean white.
    A cape's stripe or a flag's is walled by red or ends in the coat."""
    rgb = rgb.copy()
    light = (ge.white_mask(rgb) | ge.light_mask(rgb)) & mask
    lab, n = ge.label(ge.red_mask(rgb, ge.MARKER_RED_MIN) & mask)
    out = []
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() < RING_MIN_PX:
            continue
        y0, x0, y1, x1 = _box(comp)
        if max(y1 - y0, x1 - x0) > fmax:
            continue
        grown = ge._dilate(comp, RING_W)
        ring = grown & ~comp
        if float((ring & light).sum()) < RING_WHITE * float(ring.sum()):
            continue
        wall = ring & light
        pure = wall & (rgb.min(axis=-1) > RING_PURE)
        rgb[comp | wall] = rgb[pure].mean(axis=0).astype(rgb.dtype) if pure.any() else ge.PATCH_RGB
        out.append(comp | wall)
    return rgb, out


def select_fields(rgb: np.ndarray, mask: np.ndarray, how: str = "white",
                  field_max: int | None = None) -> tuple[np.ndarray, list[np.ndarray]]:
    """(picture, field masks) for one enemy's armband treatment (D108):
    `white` Gemini's own white field (find_fields, the rifleman's); `box`
    the field ge.blank_armband's box mode left (beige in shade, the
    stormtrooper's); `plain` the PATCH_RGB fields ge.patch_armband painted
    (the Panzermensch's armbands and back emblem); `ring` the General's: a
    white ring enclosing red made a plain field (the returned picture) and
    the PATCH_RGB fields painted by hand (Sheet.patch, his death frames).
    Every mode keeps only fields that pass _is_armband (no flag, no smoke, no coat)."""
    if how not in FIELD_MODES:
        raise ValueError(f"unknown field mode {how!r}")
    fmax = field_max or FIELD_MAX
    if how == "white":
        cands = find_fields(rgb, mask)
    elif how == "plain":
        cands = _plain(rgb, mask)
    elif how == "ring":
        rgb, cands = _rings(rgb, mask, fmax)
        cands += _plain(rgb, mask)
        return rgb, [f for f in cands if _is_armband(rgb, mask, f, fmax, FLAG_WINDOW)]
    else:   # box
        fmax = min(fmax, ge.FIELD_BOX_MAX)
        lab, n = ge.label(ge.white_mask(rgb, ge.BOX_WHITE_MIN) & mask)
        near_red = ge._dilate(ge.red_mask(rgb, ge.MARKER_RED_MIN) & mask, ge.ARMBAND_NEAR)
        cands = [f for f in (lab == i for i in range(1, n + 1)) if f.sum() >= ge.MIN_FIELD and (f & near_red).any()]
    return rgb, [f for f in cands if _is_armband(rgb, mask, f, fmax, purity=how != "white")]


# ------------------------------------------------------------- 2. the arm
@dataclass
class ArmFrame:
    origin: np.ndarray       # (x, y): the field's centre on screen
    around: np.ndarray       # unit, screen: across the arm (the symbol's right)
    along: np.ndarray        # unit, screen: up the arm, to the shoulder (the symbol's up)
    a_centre: float          # the cylinder's axis, as `around` offset from origin
    radius: float            # the arm's radius on screen (px)
    s_centre: float          # the symbol's centre round the arm, as arc length from the axis' front line
    t_centre: float          # the symbol's centre along the arm (px from origin)
    field_r: float           # the field's radius on the surface (px)
    curve: tuple             # (c1, c2): the band's edge, l = c1 * a + c2 * a^2 (a from the field)


def body_along(mask: np.ndarray, hint_deg: float | None = None) -> np.ndarray:
    """The arm's axis, pointing to the shoulder: `hint_deg` (screen degrees,
    0 right, 90 up) or the figure's long axis (PCA of its mask), pointing up
    (or right, for a lying figure: the corpse's head is on the right)."""
    if hint_deg is not None:
        r = math.radians(hint_deg)
        return np.array([math.cos(r), -math.sin(r)])
    ys, xs = np.nonzero(mask)
    pts = np.stack([xs, ys], axis=1).astype(np.float64)
    _, v = np.linalg.eigh(np.cov((pts - pts.mean(axis=0)).T))
    along = v[:, 1].copy()
    if along[1] > 0.3 or (abs(along[1]) <= 0.3 and along[0] < 0):
        along = -along
    return along / np.linalg.norm(along)


def _perp(along: np.ndarray) -> np.ndarray:
    """The right-handed `around` for `along` (along up -> around right): never a mirror."""
    return np.array([-along[1], along[0]])


def _fit_edge(a: np.ndarray, l: np.ndarray) -> tuple[float, float]:
    """(slope, curvature) of the band's edges in (a, l): per integer bin of
    a, the band's top and bottom l; the central 80 % of bins; clamped."""
    bins = np.round(a).astype(int)
    keys = np.unique(bins)
    if keys.size < EDGE_MIN_COLS:
        return 0.0, 0.0
    lo, hi = np.percentile(keys, 10), np.percentile(keys, 90)
    xs, tops, bots = [], [], []
    for k in keys:
        if lo <= k <= hi:
            sel = l[bins == k]
            if sel.size >= 3:
                xs.append(k)
                tops.append(sel.max())
                bots.append(sel.min())
    if len(xs) < EDGE_MIN_COLS:
        return 0.0, 0.0
    xs = np.array(xs, np.float64)
    c = [np.polyfit(xs, np.array(e), 2) for e in (tops, bots)]
    c2 = float(np.clip((c[0][0] + c[1][0]) / 2, -CURVE_MAX, CURVE_MAX))
    c1 = float(np.clip((c[0][1] + c[1][1]) / 2, -SLOPE_MAX, SLOPE_MAX))
    return c1, c2


def arm_frame(rgb: np.ndarray, mask: np.ndarray, field: np.ndarray,
              hint_deg: float | None = None) -> ArmFrame:
    """The cylinder the field sits on (see the module's step 2)."""
    along = body_along(mask, hint_deg)
    around = _perp(along)
    fy, fx = np.nonzero(field)
    origin = np.array([fx.mean(), fy.mean()])
    y0, y1, x0, x1 = fy.min(), fy.max() + 1, fx.min(), fx.max() + 1
    pad = max(y1 - y0, x1 - x0) + BAND_PAD
    sl = (slice(max(0, y0 - pad), y1 + pad), slice(max(0, x0 - pad), x1 + pad))
    band = np.zeros(mask.shape, bool)
    band[sl] = _band_mask(rgb[sl], mask[sl]) | field[sl]
    lab, n = ge.label(band)
    keep = np.unique(lab[field])
    band = np.isin(lab, keep[keep > 0])                   # the band piece holding the field
    by, bx = np.nonzero(band)
    d = np.stack([bx, by], axis=1) - origin
    a, l = d @ around, d @ along                          # l: + toward the shoulder
    a_lo, a_hi = np.percentile(a, 2), np.percentile(a, 98)
    radius = max(R_MIN, (a_hi - a_lo) / 2 + 0.5)
    a_centre = (a_lo + a_hi) / 2
    c1, c2 = _fit_edge(a, l)
    # the field on the surface: arc length round the arm, its along-arm extent unforeshortened
    df = np.stack([fx, fy], axis=1) - origin
    fa, fl = df @ around, df @ along
    s = radius * np.arcsin(np.clip((fa - a_centre) / radius, -1, 1))
    field_r = max(1.5, (fl.max() - fl.min() + 1) / 2)
    s_lo, s_hi = float(s.min()), float(s.max())
    cut_hi, cut_lo = fa.max() >= a_hi - SILHOUETTE_PX, fa.min() <= a_lo + SILHOUETTE_PX
    if s_hi - s_lo >= CUT_FIELD * field_r or cut_hi == cut_lo:
        s_c = (s_lo + s_hi) / 2
    elif cut_hi:                                          # the field turns away behind the arm's + edge
        s_c = s_lo + field_r
    else:
        s_c = s_hi - field_r
    t_c = float((fl - (c1 * fa + c2 * fa ** 2)).mean())
    return ArmFrame(origin, around, along, float(a_centre), float(radius), float(s_c), t_c,
                    float(field_r), (c1, c2))


# --------------------------------------------------------------- 3. vector
# the symbol's 17 black cells by part: C the centre, U L D R the four arms (each
# a bar from the centre and its hook); "." white. Same grid as ge.SYMBOL.
ARM_GRID = ("L.UUU",
            "L.U..",
            "LLCRR",
            "..D.R",
            "DDD.R")
PART_IDS = {"C": 1, "U": 2, "L": 3, "D": 4, "R": 5}
ARMS = (2, 3, 4, 5)


def _grid_lookup(x: np.ndarray, y: np.ndarray, grid: np.ndarray, tilt_deg: float, reach: float,
                 mirror: bool = False) -> np.ndarray:
    """grid's value at (x right, y up) in units of the field's radius: the
    5x5 grid (row 0 on top) rotated by `tilt_deg`, its corners at `reach`;
    0 outside. `mirror`: the grid's columns reversed (the WRONG handedness,
    for the repaint check only)."""
    r = math.radians(tilt_deg)
    c, s = math.cos(r), math.sin(r)
    u, v = c * x + s * y, -s * x + c * y          # the inverse rotation: screen -> pattern
    h = reach / math.sqrt(2.0)
    n = grid.shape[0]
    col = np.floor((u / h + 1) / 2 * n).astype(int)
    row = np.floor((1 - v / h) / 2 * n).astype(int)
    inside = (col >= 0) & (col < n) & (row >= 0) & (row < n)
    g = grid[:, ::-1] if mirror else grid
    out = np.zeros(x.shape, grid.dtype)
    out[inside] = g[row[inside], col[inside]]
    return out


def symbol_ink(x: np.ndarray, y: np.ndarray, tilt_deg: float = TILT_DEG,
               reach: float = SYMBOL_REACH) -> np.ndarray:
    """True where the symbol is black, at (x right, y up) in units of the
    field's radius. ge.SYMBOL's 5x5 grid (the approved sprite's, row 0 on
    top), rotated by `tilt_deg`, its corners reaching `reach`."""
    black = np.array([[ch == "K" for ch in r_] for r_ in ge.SYMBOL])
    return _grid_lookup(x, y, black, tilt_deg, reach)


def symbol_parts(x: np.ndarray, y: np.ndarray, tilt_deg: float = TILT_DEG,
                 reach: float = SYMBOL_REACH, mirror: bool = False) -> np.ndarray:
    """PART_IDS of the symbol's cell at (x, y) (0: white or outside)."""
    grid = np.array([[PART_IDS.get(ch, 0) for ch in r_] for r_ in ARM_GRID], np.int32)
    return _grid_lookup(x, y, grid, tilt_deg, reach, mirror)


def _surface(gx: np.ndarray, gy: np.ndarray, frame: ArmFrame) -> tuple[np.ndarray, np.ndarray]:
    """Screen points -> the symbol's (x, y) on the arm's surface, in field radii."""
    c1, c2 = frame.curve
    d = np.stack([gx - frame.origin[0], gy - frame.origin[1]], axis=-1)
    a, l = d @ frame.around, d @ frame.along
    q = np.clip((a - frame.a_centre) / frame.radius, -1, 1)
    s = frame.radius * np.arcsin(q)
    t = l - (c1 * a + c2 * a ** 2)
    return (s - frame.s_centre) / frame.field_r, (t - frame.t_centre) / frame.field_r


def coverage(shape: tuple[int, int], frame: ArmFrame, clip: np.ndarray,
             tilt_deg: float = TILT_DEG, ss: int = SUPERSAMPLE) -> np.ndarray:
    """Fraction of each pixel the symbol covers, bent round the arm, in the
    box of `clip` (the field) only."""
    out = np.zeros(shape, np.float64)
    ys, xs = np.nonzero(clip)
    if not ys.size:
        return out
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    off = (np.arange(ss) + 0.5) / ss - 0.5
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    acc = np.zeros(gy.shape)
    for oy in off:
        for ox in off:
            acc += symbol_ink(*_surface(gx + ox, gy + oy, frame), tilt_deg)
    out[y0:y1, x0:x1] = acc / (ss * ss)
    return out * clip


def part_map(shape: tuple[int, int], frame: ArmFrame, clip: np.ndarray,
             tilt_deg: float = TILT_DEG, mirror: bool = False) -> np.ndarray:
    """PART_IDS at each pixel's centre, bent round the arm, inside `clip`."""
    out = np.zeros(shape, np.int32)
    ys, xs = np.nonzero(clip)
    if ys.size:
        gy, gx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float64)
        out[ys, xs] = symbol_parts(*_surface(gx[ys, xs], gy[ys, xs], frame), tilt_deg, mirror=mirror)
    return out


def scale_frame(frame: ArmFrame, k: float, shift: tuple[float, float]) -> ArmFrame:
    """The same arm in a crop's pixels: source (x, y) -> (x - shift_x + 0.5) * k - 0.5
    (a crop starting at `shift`, enlarged k times). The edge's curve keeps its shape."""
    o = (frame.origin - np.asarray(shift, np.float64) + 0.5) * k - 0.5
    c1, c2 = frame.curve
    return replace(frame, origin=o, a_centre=frame.a_centre * k, radius=frame.radius * k,
                   s_centre=frame.s_centre * k, t_centre=frame.t_centre * k, field_r=frame.field_r * k,
                   curve=(c1, c2 / k))


# ---------------------------------------------------------- 4-5. the paint
def gaussian_blur(img: np.ndarray, sigma: float) -> np.ndarray:
    if sigma <= 0.05:
        return img
    r = max(1, int(math.ceil(3 * sigma)))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    p = np.pad(img, r, mode="constant")
    p = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, p)
    p = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, p)
    return p[r:-r, r:-r]


def edge_sigma(rgb: np.ndarray, mask: np.ndarray, field: np.ndarray) -> float:
    """Gemini's edge softness at this scale, from the field's own edge on the
    red: the pixels between EDGE_LO and EDGE_HI of the red-to-white step per
    pixel of the field's outline is the 20-80 % width; in sigmas, clamped."""
    L = lum(rgb)
    inner = _erode(field, 1)
    ring = ge._dilate(field, 1) & ~inner & mask
    red = ge.red_mask(rgb, ge.MARKER_RED_MIN) & mask & ge._dilate(field, 3) & ~field
    if not inner.any() or not red.any() or not ring.any():
        return SIGMA_MIN
    lo, hi = float(np.median(L[red])), float(np.median(L[inner]))
    if hi - lo < 20:
        return SIGMA_MIN
    t = (L - lo) / (hi - lo)
    mid = int((ring & (t > EDGE_LO) & (t < EDGE_HI)).sum())
    outline = max(1, int((field & ~inner).sum()))
    return float(np.clip(mid / outline / EDGE_SPAN_20_80, SIGMA_MIN, SIGMA_MAX))


def grain_sigma(rgb: np.ndarray, mask: np.ndarray) -> float:
    """The grain of Gemini's dark areas: the std of luminance minus its 3x3
    mean, over the figure's dark interior pixels; clamped."""
    L = lum(rgb)
    p = np.pad(L, 1, mode="edge")
    mean3 = sum(p[1 + dy:1 + dy + L.shape[0], 1 + dx:1 + dx + L.shape[1]]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9.0
    sel = _erode(mask, 1) & (L < GRAIN_DARK)
    if sel.sum() < 16:
        return 0.0
    return float(np.clip(np.std((L - mean3)[sel]), 0, GRAIN_MAX))


def ink_colour(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Gemini's black on this figure: the median colour of its darkest decile."""
    L = lum(rgb)
    sel = mask & (L <= np.percentile(L[mask], INK_DECILE))
    return np.median(rgb[sel].astype(np.float64), axis=0)


@dataclass
class Painted:
    fields: int
    ink_px: float            # sum of the coverage (px of full ink)
    sigma: float
    grain: float
    frames: list


def paint_symbol(rgb: np.ndarray, mask: np.ndarray, hint_deg: float | None = None,
                 tilt_deg: float = TILT_DEG, seed: int = 0, sigma: float | None = None,
                 grain: float | None = None, fields: list | None = None) -> tuple[np.ndarray, Painted]:
    """The symbol painted into every armband field of one Gemini figure
    (`fields`: those of select_fields; None: find_fields')."""
    out = rgb.astype(np.float64)
    fields = find_fields(rgb, mask) if fields is None else fields
    info = Painted(len(fields), 0.0, 0.0, 0.0, [])
    if not fields:
        return rgb.copy(), info
    ink = ink_colour(rgb, mask)
    g = grain_sigma(rgb, mask) if grain is None else grain
    rng = np.random.default_rng(seed)
    L = lum(rgb)
    for f in fields:
        frame = arm_frame(rgb, mask, f, hint_deg)
        sg = edge_sigma(rgb, mask, f) if sigma is None else sigma
        cov = coverage(mask.shape, frame, f, tilt_deg)
        cov = np.clip(gaussian_blur(cov, math.sqrt(max(0.0, sg ** 2 - BOX_SIGMA ** 2))), 0, 1) * f
        ref = max(1.0, float(np.percentile(L[f], FIELD_REF_PCT)))
        shade = np.clip(L / ref, 0, 1.15)[..., None]           # the field's light and folds
        noise = rng.normal(0.0, g, mask.shape)[..., None] if g > 0 else 0.0
        inked = ink[None, None, :] * shade + noise
        a = cov[..., None]
        out = out * (1 - a) + inked * a
        info.ink_px += float(cov.sum())
        info.sigma, info.grain = sg, g
        info.frames.append(frame)
    return np.clip(np.round(out), 0, 255).astype(np.uint8), info


def apply_symbol(rgb: np.ndarray, mask: np.ndarray, mode: str = DEFAULT_SYMBOL,
                 hint_deg: float | None = None, seed: int = 0, fields: list | None = None) -> np.ndarray:
    """The pipeline's hook: `none` returns the picture untouched; `warp`
    paints the symbol. Call it AFTER any mirror (never mirror a painted symbol)."""
    if mode not in SYMBOL_MODES:
        raise ValueError(f"unknown symbol mode {mode!r}")
    if mode == "none":
        return rgb
    return paint_symbol(rgb, mask, hint_deg, seed=seed, fields=fields)[0]


# ------------------------------------------- option 2: Fooocus (D108)
# The CEO's "mix" (D108): option 1 on every frame of the Reich, and on the
# frames seen closest (the corpses, the profiles) a repaint by SDXL (Fooocus,
# local, no downloads) on top. The repaint is made out of process
# (work/art/armband_fooocus/run_d108.py): here are the pure parts, the crop
# and its start (the symbol of option 1, drawn crisp at the crop's size),
# the objective pick of a seed, and the cache that makes the build
# reproducible without generating again.
UP = 1024                    # px a crop is enlarged to for SDXL
CROP_MIN = 48                # source px: the smallest crop round a field
CROP_FIELD = 3.0             # x the field's size: the crop round it
CROP_BG = (118, 118, 118)    # outside the figure in the crop: neutral grey
CROP_SOFT = 3.0              # the enlarged crop is blurred by its scale / this (no hard Gemini pixels)
INIT_BLUR = 1.5              # px: the crisp start symbol softened
INIT_INK = (18, 16, 14)      # the start symbol's black
MASK_GROW_SRC = 1.5          # source px the inpaint mask grows past the field (the model redraws its edge)
INIT_SS = 2                  # super-sampling of the start symbol at crop size
DENOISE_BY_SIDE = ((12, 0.65), (9, 0.58), (0, 0.5))   # field's short side (source px) -> denoise
SCORE_RES = 256              # px the repaint is judged at
INK_MAX = 90                 # a judged pixel is ink when its brightest channel is under this
INK_TOL_SRC = 0.6            # source px of slack round the template before ink counts as extra
IOU_MIN = 0.60               # the repaint's ink against the bent template (intersection over union)
ARM_MIN = 0.45               # every one of the four arms at least this much drawn
HAND_MARGIN = 0.15           # the template must beat its mirror image by this much (the right handedness)
EXTRA_MAX = 0.35             # ink inside the disc off the template, x the template's area (extra arms, blots)
OUTSIDE_MAX = 0.15           # new ink outside the disc, x the template's area (the symbol leaving its field)
PATCH_ALPHA = 1.5            # the pasted repaint's alpha: the inpaint mask's coverage x this, clipped


def picture_key(rgb: np.ndarray, mask: np.ndarray) -> str:
    """The cache key of a picture (before any symbol): its pixels and mask."""
    h = hashlib.sha1()
    h.update(np.asarray(rgb.shape, np.int64).tobytes())
    h.update(np.ascontiguousarray(rgb, np.uint8).tobytes())
    h.update(np.packbits(np.ascontiguousarray(mask, bool)).tobytes())
    return h.hexdigest()[:16]


def picture_seed(key: str) -> int:
    """Option 1's grain seed for a picture: from its key, not from the build order."""
    return int(key[:8], 16) % (2 ** 31)


def denoise_for(field: np.ndarray) -> float:
    """SDXL's denoise by the field's size: a small disc keeps more of the
    start (0.65 broke the symbol on 6-8 px discs, 2026-10-22)."""
    y0, x0, y1, x1 = _box(field)
    side = min(y1 - y0, x1 - x0)
    return next(d for lo, d in DENOISE_BY_SIDE if side >= lo)


def crop_box(field: np.ndarray) -> tuple[int, int, int]:
    """(ty, tx, n): the square crop of n source px round a field."""
    y0, x0, y1, x1 = _box(field)
    n = max(CROP_MIN, int(math.ceil(CROP_FIELD * max(y1 - y0, x1 - x0) / 8.0)) * 8)
    cy, cx = (y0 + y1) / 2, (x0 + x1) / 2
    return int(round(cy - n / 2)), int(round(cx - n / 2)), n


def _cut_square(img: np.ndarray, ty: int, tx: int, n: int, fill) -> np.ndarray:
    """img[ty:ty+n, tx:tx+n], padded with `fill` where it leaves the picture."""
    out = np.empty((n, n) + img.shape[2:], img.dtype)
    out[...] = fill
    H, W = img.shape[:2]
    ys, xs = slice(max(0, ty), min(H, ty + n)), slice(max(0, tx), min(W, tx + n))
    out[ys.start - ty:ys.stop - ty, xs.start - tx:xs.stop - tx] = img[ys, xs]
    return out


def _grow(m: np.ndarray, r: float) -> np.ndarray:
    k = int(round(r))
    if k <= 0:
        return m
    return np.asarray(Image.fromarray(m.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(2 * k + 1))) > 127


@dataclass
class Prepared:
    """One field's crop for SDXL, all at UP x UP."""
    crop: tuple              # (ty, tx, n) in the source picture
    base: np.ndarray         # the plain crop (the field white), enlarged
    init: np.ndarray         # the start: base + option 1's symbol drawn crisp
    inpaint: np.ndarray      # bool: what SDXL may repaint (the field, grown, on the figure)
    clip: np.ndarray         # bool: the field
    parts: np.ndarray        # PART_IDS of the template (the bent symbol)
    parts_m: np.ndarray      # ... of its mirror image (the wrong handedness)
    denoise: float


def prepare_field(rgb: np.ndarray, mask: np.ndarray, field: np.ndarray, hint_deg: float | None = None,
                  up: int = UP) -> Prepared:
    """The crop round one field, its start and its mask: the arm's cylinder
    (arm_frame) measured on the source, enlarged to the crop (scale_frame), so
    the start symbol is option 1's own, bent the same way, never mirrored."""
    ty, tx, n = crop_box(field)
    k = up / n
    flat = rgb.copy()
    flat[~mask] = CROP_BG
    sub = _cut_square(flat, ty, tx, n, CROP_BG)
    base = np.asarray(Image.fromarray(sub).resize((up, up), Image.LANCZOS)
                      .filter(ImageFilter.GaussianBlur(k / CROP_SOFT)))
    fig = np.asarray(Image.fromarray(_cut_square(mask, ty, tx, n, False).astype(np.uint8) * 255)
                     .resize((up, up), Image.NEAREST)) > 127
    soft = np.asarray(Image.fromarray(_cut_square(field, ty, tx, n, False).astype(np.uint8) * 255)
                      .resize((up, up), Image.BILINEAR)) > 127
    clip = soft & fig
    frame = scale_frame(arm_frame(rgb, mask, field, hint_deg), k, (tx, ty))
    cov = coverage((up, up), frame, clip, ss=INIT_SS)[..., None]
    init = base.astype(np.float64) * (1 - cov) + np.array(INIT_INK, np.float64) * cov
    init = np.asarray(Image.fromarray(np.clip(init + 0.5, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(INIT_BLUR)))
    inpaint = _grow(clip, MASK_GROW_SRC * k) & fig
    return Prepared((ty, tx, n), base, init, inpaint, clip, part_map((up, up), frame, clip),
                    part_map((up, up), frame, clip, mirror=True), denoise_for(field))


@dataclass
class RepaintScore:
    iou: float
    iou_mirror: float
    arm_min: float
    extra: float
    outside: float
    passed: bool
    why: str


def _down(a: np.ndarray, res: int) -> np.ndarray:
    if a.ndim == 2:            # masks and labels: the nearest sample
        return np.asarray(Image.fromarray(a.astype(np.int32)).resize((res, res), Image.NEAREST)).astype(a.dtype)
    return np.asarray(Image.fromarray(a).resize((res, res), Image.BOX))


def score_repaint(result: np.ndarray, prep: Prepared, res: int = SCORE_RES) -> RepaintScore:
    """The objective pick (D108): SDXL's ink (dark pixels) against the bent
    template: their overlap (iou), the same against the mirror image (the
    template must win by HAND_MARGIN: the right handedness), each of the four
    arms drawn (arm_min: no arm missing), ink in the disc off the template
    (extra: no extra arm, no blot) and new ink outside the disc that touches
    the symbol (outside: the symbol leaving its field; a dark rim SDXL draws
    round the disc, apart from the symbol, is not counted)."""
    ink = _down(result, res).max(axis=-1) < INK_MAX
    was = _down(prep.base, res).max(axis=-1) < INK_MAX
    clip, parts, parts_m = _down(prep.clip, res), _down(prep.parts, res), _down(prep.parts_m, res)
    ink &= _down(prep.inpaint, res) | clip
    inside = ink & clip                  # the symbol is judged in the disc; outside it, only new ink counts
    T, Tm = parts > 0, parts_m > 0
    area = max(1, int(T.sum()))

    def iou(a, b):
        return float((a & b).sum()) / max(1, int((a | b).sum()))
    i, im = iou(inside, T), iou(inside, Tm)
    arms = [float((inside & (parts == a)).sum()) / max(1, int((parts == a).sum())) for a in ARMS]
    tol = INK_TOL_SRC * res / prep.crop[2]
    extra = float((inside & ~_grow(T, max(1.0, tol))).sum()) / area
    new = ink & ~was                     # outside the disc, the new ink that is the symbol's: touching it
    lab, n = ge.label(new)
    touch = np.unique(lab[new & _grow(T, max(1.0, 2 * tol))])
    bleed = np.isin(lab, touch[touch > 0]) & ~clip
    outside = float(bleed.sum()) / area
    why = [w for w, bad in (("iou", i < IOU_MIN), ("arm", min(arms) < ARM_MIN),
                            ("mirror", i - im < HAND_MARGIN), ("extra", extra > EXTRA_MAX),
                            ("outside", outside > OUTSIDE_MAX)) if bad]
    return RepaintScore(round(i, 3), round(im, 3), round(min(arms), 3), round(extra, 3), round(outside, 3),
                        not why, ",".join(why))


def pick_seed(results: dict, prep: Prepared) -> tuple[object, dict]:
    """(the best passing candidate's name or None, {name: score}): the
    highest iou among the candidates that pass every check."""
    scores = {name: score_repaint(img, prep) for name, img in results.items()}
    ok = [n for n, s in scores.items() if s.passed]
    return (max(ok, key=lambda n: (scores[n].iou, str(n))) if ok else None), scores


def patch_from(result: np.ndarray, prep: Prepared) -> np.ndarray:
    """The chosen repaint back at source size: RGBA n x n, the alpha the
    inpaint mask's coverage x PATCH_ALPHA (a soft edge one source px wide)."""
    n = prep.crop[2]
    rgb = np.asarray(Image.fromarray(result).resize((n, n), Image.LANCZOS))
    a = np.asarray(Image.fromarray(prep.inpaint.astype(np.uint8) * 255).resize((n, n), Image.BOX)) / 255.0
    alpha = np.clip(a * PATCH_ALPHA, 0, 1)
    return np.dstack([rgb, np.round(alpha * 255).astype(np.uint8)])


def paste_patch(rgb: np.ndarray, mask: np.ndarray, patch: np.ndarray, crop: tuple) -> np.ndarray:
    """A cached patch over the picture, inside the figure only."""
    ty, tx, n = crop
    out = rgb.astype(np.float64)
    H, W = mask.shape
    ys, xs = slice(max(0, ty), min(H, ty + n)), slice(max(0, tx), min(W, tx + n))
    p = patch[ys.start - ty:ys.stop - ty, xs.start - tx:xs.stop - tx].astype(np.float64)
    a = p[..., 3:] / 255.0 * mask[ys, xs][..., None]
    out[ys, xs] = out[ys, xs] * (1 - a) + p[..., :3] * a
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def cache_entry_path(key: str, cache_dir: Path = FOOOCUS_CACHE) -> Path:
    return Path(cache_dir) / f"{key}.json"


def write_cache(key: str, entry: dict, patches: dict, cache_dir: Path = FOOOCUS_CACHE) -> Path:
    """entry: {"label", "fields": [{"k", "status": "fooocus"|"fallback", "crop", ...}]};
    patches: k -> RGBA patch (the fooocus fields only)."""
    cache_dir = Path(cache_dir)
    ge.guard_out(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    for k, patch in patches.items():
        Image.fromarray(patch, "RGBA").save(cache_dir / f"{key}_f{k}.png")
    path = cache_entry_path(key, cache_dir)
    path.write_text(json.dumps(dict(entry, key=key), indent=1), encoding="utf-8")
    return path


def apply_fooocus(rgb: np.ndarray, mask: np.ndarray, key: str,
                  cache_dir: Path = FOOOCUS_CACHE) -> tuple[np.ndarray, str]:
    """Option 2 over option 1 from the cache: (picture, status). `fooocus`
    every field repainted; `partial` some; `fallback` none passed the pick
    (option 1 stays); `missing` never generated for this picture (option 1)."""
    path = cache_entry_path(key, cache_dir)
    if not path.exists():
        return rgb, "missing"
    entry = json.loads(path.read_text(encoding="utf-8"))
    fields = entry.get("fields", [])
    done = 0
    for f in fields:
        if f.get("status") != "fooocus":
            continue
        with Image.open(Path(cache_dir) / f"{key}_f{f['k']}.png") as im:
            patch = np.asarray(im.convert("RGBA"))
        rgb = paste_patch(rgb, mask, patch, tuple(f["crop"]))
        done += 1
    return rgb, ("fooocus" if fields and done == len(fields) else "partial" if done else "fallback")


# ----------------------------------------------------------- comparison
COMPARE_VIEWS = (   # (label, sheet, view, arm-axis hint in screen degrees or None)
    ("frente (B1)", "turn", 0, None),
    ("3/4 (B2)", "turn", 1, None),
    ("perfil (B3)", "turn", 2, None),
    ("cadáver (L)", "death2", 2, 0.0),     # lying, the shoulder to the right
)
CROP_PAD = 16          # source px round the field in column (a)
CROP_ZOOM = 3
SPRITE_ZOOM = 6
GAME_GREY = (92, 92, 92)
CROP_BG = (120, 112, 120)   # column (a): the keyed background, neutral
BG = (58, 60, 66)
INK = (240, 236, 228)


def _font(size: int):
    try:
        return ImageFont.truetype(artlib.FONT_SMALL, size)
    except OSError:  # pragma: no cover - no system font
        return ImageFont.load_default()


def _crop_box(field: np.ndarray, shape) -> tuple[int, int, int, int]:
    ys, xs = np.nonzero(field)
    cy, cx = (ys.min() + ys.max()) // 2, (xs.min() + xs.max()) // 2
    h = max(ys.max() - ys.min(), xs.max() - xs.min()) // 2 + CROP_PAD
    return max(0, cy - h), max(0, cx - h), min(shape[0], cy + h), min(shape[1], cx + h)


def _rgba_img(rgb: np.ndarray, mask: np.ndarray, bg) -> Image.Image:
    im = np.empty(rgb.shape, np.uint8)
    im[:] = bg
    im[mask] = rgb[mask]
    return Image.fromarray(im)


def compare(spec=ge.RIFLEMAN, out: Path = COMPARE_PNG, ref_dir: Path = ge.REF_DIR,
            work: Path = WORK_DIR) -> tuple[Path, list]:
    """The CEO's PNG: per view, (a) the arm at Gemini resolution before and
    after, x CROP_ZOOM; (b) the final sprite x SPRITE_ZOOM; (c) the final
    sprite x1 and x2 on grey, with Doom's 1.2 pixel aspect, as in game."""
    pal = ge.palette_rgb()
    cuts = ge.plan(spec, ref_dir)
    base = spec.target_height / cuts[spec.ref_sheet].figs[spec.ref_view].mask.shape[0]
    rows, report = [], []
    for k, (label_txt, sheet, view, hint) in enumerate(COMPARE_VIEWS):
        cut = cuts[sheet].figs[view]
        painted, info = paint_symbol(cut.rgb, cut.mask, hint, seed=1050 + k)
        sc = base * cuts[sheet].scale
        sprite = ge.render(replace(cut, rgb=painted), sc, pal)
        rgba = ge.to_rgba(sprite, pal)
        fields = find_fields(cut.rgb, cut.mask)
        if fields:
            y0, x0, y1, x1 = _crop_box(max(fields, key=lambda f: int(f.sum())), cut.mask.shape)
        else:
            y0, x0, y1, x1 = 0, 0, cut.mask.shape[0], cut.mask.shape[1]
        crops = [_rgba_img(im[y0:y1, x0:x1], cut.mask[y0:y1, x0:x1], CROP_BG) for im in (cut.rgb, painted)]
        if work is not None:
            ge.guard_out(work)
            work.mkdir(parents=True, exist_ok=True)
            Image.fromarray(painted).save(work / f"{sheet}{view}_painted_source.png")
            ge.save_sprite(rgba, (0, 0), work / f"{sheet}{view}_sprite.png")
        rows.append((label_txt, crops, rgba))
        report.append({"view": label_txt, "fields": info.fields, "ink_px": round(info.ink_px, 1),
                       "sigma": round(info.sigma, 2), "grain": round(info.grain, 2),
                       "field_r": [round(f.field_r, 1) for f in info.frames],
                       "radius": [round(f.radius, 1) for f in info.frames],
                       "theta0_deg": [round(math.degrees(f.s_centre / f.radius), 0) for f in info.frames]})
    return _draw(rows, out, spec.sprite), report


NOTES = (
    "Como un editor en Photoshop, por código, en la hoja de Gemini ANTES de reducir: se localiza el campo blanco del brazalete; el brazo",
    "se modela como un cilindro (eje = eje largo de la figura, radio = ancho del brazalete, inclinación y curva = el borde del brazalete);",
    "la esvástica vectorial (la del sprite aprobado, mismo sentido de giro, inclinada 45 grados como la histórica) se dobla sobre él",
    "(arcoseno: escorzo hacia el borde del brazo), se recorta por el campo, se suaviza como el borde del propio campo de Gemini, se",
    "multiplica por la luz del campo (pliegues y sombra siguen) y lleva el grano de los negros de Gemini. Luego el pipeline normal reduce",
    "la figura entera. NO instalado: ni overlay ni hoja de revisión. Columna (a): izquierda antes, derecha después, píxeles de Gemini x3.",
    "Frente: el campo está de canto (a ~88 grados, en la silueta del brazo); el símbolo queda detrás: no se ve, como en una foto.",
    "En la hoja de Gemini el campo mide 6-17 px (no 20-40); en el sprite, 3-4 px: se lee como una marca negra en el disco blanco.",
    "La insignia 7x7 del set actual es la misma cruz (mismo sentido de giro) pero recta: a 5x5 px no cabe inclinada.",
)


def _draw(rows, out: Path, sprite: str) -> Path:
    ge.guard_out(out)
    font, small = _font(15), _font(13)
    z, cz = SPRITE_ZOOM, CROP_ZOOM
    a_w = max(2 * c[0].width * cz + 12 for _, c, _ in rows)
    b_w = max(r.shape[1] * z for _, _, r in rows)
    c_w = max(r.shape[1] * 3 + 24 for _, _, r in rows) + 24
    label_w, head_h, gap, col_gap = 130, 70, 22, 28
    row_h = [max(c[0].height * cz, r.shape[0] * z) + gap for _, c, r in rows]
    W = label_w + a_w + b_w + c_w + 3 * col_gap
    H = head_h + sum(row_h) + 21 * len(NOTES) + 26
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    dr.text((10, 8), f"{sprite}: brazalete, opción 1 (editado a la resolución de Gemini, luego reducido). "
                     "NO instalado: el CEO decide.", fill=INK, font=font)
    xa, xb = label_w, label_w + a_w + col_gap
    xc = xb + b_w + col_gap
    dr.text((xa, 40), f"(a) Gemini, brazo x{cz}: antes | después", fill=(220, 214, 200), font=small)
    dr.text((xb, 40), f"(b) sprite final x{z}", fill=(220, 214, 200), font=small)
    dr.text((xc, 40), "(c) x1 y x2 sobre gris, aspecto 1.2", fill=(220, 214, 200), font=small)
    y = head_h
    for (label_txt, crops, rgba), rh in zip(rows, row_h):
        dr.text((10, y + 8), label_txt, fill=INK, font=font)
        x = xa
        for c in crops:
            big = c.resize((c.width * cz, c.height * cz), Image.NEAREST)
            img.paste(big, (x, y))
            x += big.width + 12
        sp = Image.fromarray(rgba, "RGBA")
        big = sp.resize((sp.width * z, sp.height * z), Image.NEAREST)
        img.paste(big, (xb, y), big)
        panel_h = rh - gap
        dr.rectangle([xc, y, xc + c_w - 24, y + panel_h], fill=GAME_GREY)
        x = xc + 8
        for k in (1, 2):
            s = sp.resize((sp.width * k, round(sp.height * k * ge.PIXEL_ASPECT)), Image.NEAREST)
            img.paste(s, (x, y + panel_h - s.height - 6), s)
            x += s.width + 12
        y += rh
    for i, line in enumerate(NOTES):
        dr.text((10, y + 6 + 21 * i), line, fill=(214, 208, 196), font=small)
    ge.guard_out(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", choices=("compare",), help="compare: the CEO's PNG (rifleman, four frames)")
    args = ap.parse_args(argv)
    if args.what == "compare":
        out, report = compare()
        for r in report:
            print(r)
        print(f"armband_symbol: wrote {out.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
