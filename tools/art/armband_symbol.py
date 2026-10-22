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

Then the pipeline reduces the figure as usual (gemini_enemy.render). The
pipeline wiring, for later: `add_symbol_arg(parser)` adds `--symbol
none|warp` (default none: OFF), and `apply_symbol(rgb, mask, mode)` goes in
gemini_enemy.render AFTER the mirror and before the tilt and the downscale,
so a mirrored rotation (6-8) gets the symbol drawn the right way round.
Nothing here writes the overlay, the review sheet or assets/.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402
import gemini_enemy as ge  # noqa: E402

ROOT = artlib.PROJECT_ROOT
COMPARE_PNG = ROOT / "docs" / "art" / "previews" / "2026-10-22_P4_armband-option1.png"
WORK_DIR = ROOT / "work" / "art" / "armband_test"

SYMBOL_MODES = ("none", "warp")
DEFAULT_SYMBOL = "none"      # OFF until the CEO approves (D105)
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
    """`--symbol none|warp` for gemini_enemy's CLI; default none (OFF)."""
    ap.add_argument("--symbol", choices=SYMBOL_MODES, default=DEFAULT_SYMBOL,
                    help="the D12 symbol on the armband: none (default) or warp (painted at the "
                         "Gemini sheet's resolution before the reduction; NOT approved)")
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
def symbol_ink(x: np.ndarray, y: np.ndarray, tilt_deg: float = TILT_DEG,
               reach: float = SYMBOL_REACH) -> np.ndarray:
    """True where the symbol is black, at (x right, y up) in units of the
    field's radius. ge.SYMBOL's 5x5 grid (the approved sprite's, row 0 on
    top), rotated by `tilt_deg`, its corners reaching `reach`."""
    r = math.radians(tilt_deg)
    c, s = math.cos(r), math.sin(r)
    u, v = c * x + s * y, -s * x + c * y          # the inverse rotation: screen -> pattern
    h = reach / math.sqrt(2.0)
    n = len(ge.SYMBOL)
    col = np.floor((u / h + 1) / 2 * n).astype(int)
    row = np.floor((1 - v / h) / 2 * n).astype(int)
    inside = (col >= 0) & (col < n) & (row >= 0) & (row < n)
    black = np.array([[ch == "K" for ch in r_] for r_ in ge.SYMBOL])
    out = np.zeros(x.shape, bool)
    out[inside] = black[row[inside], col[inside]]
    return out


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
    c1, c2 = frame.curve
    for oy in off:
        for ox in off:
            d = np.stack([gx + ox - frame.origin[0], gy + oy - frame.origin[1]], axis=-1)
            a, l = d @ frame.around, d @ frame.along
            q = np.clip((a - frame.a_centre) / frame.radius, -1, 1)
            s = frame.radius * np.arcsin(q)
            t = l - (c1 * a + c2 * a ** 2)
            acc += symbol_ink((s - frame.s_centre) / frame.field_r, (t - frame.t_centre) / frame.field_r, tilt_deg)
    out[y0:y1, x0:x1] = acc / (ss * ss)
    return out * clip


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
                 grain: float | None = None) -> tuple[np.ndarray, Painted]:
    """The symbol painted into every armband field of one Gemini figure."""
    out = rgb.astype(np.float64)
    fields = find_fields(rgb, mask)
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
                 hint_deg: float | None = None, seed: int = 0) -> np.ndarray:
    """The pipeline's hook: `none` returns the picture untouched; `warp`
    paints the symbol. Call it AFTER any mirror (never mirror a painted symbol)."""
    if mode not in SYMBOL_MODES:
        raise ValueError(f"unknown symbol mode {mode!r}")
    if mode == "none":
        return rgb
    return paint_symbol(rgb, mask, hint_deg, seed=seed)[0]


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
