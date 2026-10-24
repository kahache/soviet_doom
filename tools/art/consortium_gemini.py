"""The Consortium (SDCN, Episode 3's final boss) from the PM's Gemini sheets
(D112, D116, D119, D127): the steps gemini_enemy.py does not do for it, around its build.

    python tools/art/consortium_gemini.py fix       # Gemini's sheets -> gem_consortium_fix_<L>.png (work/, D77)
    python tools/art/consortium_gemini.py build     # fix + gemini_enemy.build(CONSORTIUM) -> work/art/enemies_gemini/consortium/
    python tools/art/consortium_gemini.py sheet     # the CEO's preview + the install patch (needs build)
    python tools/art/consortium_gemini.py all       # the three
    python tools/art/consortium_gemini.py gen-jobs  # D127: the Fooocus inpaint job for the holes Gemini never drew (GEN)
    python tools/art/consortium_gemini.py gen-pick NAME SEED   # the chosen inpaint, cached for the build

Why a fix stage. The Consortium is two bodies in one: the Reich half (grey-
green flesh, SS helmet, the armband, the rocket rack) and the Legion half
(chrome and pink, M1 helmet, the flag, the energy projector). The design
doc (docs/engine/2026-10-22_P4_ep3-final-boss.md section 2) puts the Reich
half on ITS LEFT: in a front view on the viewer's RIGHT; the actor fires
the rockets 32 units to its left and the orbs 32 to its right. Gemini drew
every sheet the other way round (the Reich half on its right), and in some
views gave an arm the other half's weapon, a third arm, or a cable skirt
where a leg goes. The pipeline mirrors a side view to face left and makes
rotations 6-8 by mirroring 4-2: for this body that would put the halves on
the wrong side in three rotations of eight. So, before gemini_enemy builds
the lumps, this module rewrites each sheet as eight canonical pictures:

  1. cut      - the figures of each Gemini sheet (gemini_enemy.figures; hand
                ownership polygons, OWN, where two figures touch)
  2. repair   - per view, in Gemini's own pixel coordinates (measured on x3/x4
                zooms): `drop` an extra or wrong arm, `lower` (everything under a
                row from another view of the same scale: the walk's legs, the
                firing frame's knot of cables and smoke), `paste` a part from
                another view, `graft` (the same, registered), `recolour` a part as
                another material, `hue` (a glow's blue <-> a flash's fire),
                `knot_fill` (the knot of cables made whole under an arm that hung
                over it), `drop_bright` (a rocket off the smoke), `gen` (D127: a
                hole Gemini never drew, from a cached Fooocus inpaint of the same
                view); REPAIRS_POST after the mirror; `keep` (front views whose arms Gemini drew
                on the right side for the right weapon but whose bodies are the
                wrong way round: the body is mirrored, the arms are not)
  3. mirror   - each repaired view mirrored about its axis: the Reich half on
                its left. Views 2-4 then face left: Doom's rotations 2-4.
  4. far side - rotations 6-8 show its right side, the Legion's: the repaired
                3/4 back, profile and 3/4 front NOT mirrored (they face right),
                with the two halves' materials exchanged (`swap`: grey-green
                flesh <-> pink by luminance percentile, the SS helmet <-> the M1
                in the helmets' rows, the rack's olive -> chrome, the armband ->
                a chrome band). Gemini drew no view of that side.
  5. scale    - every sheet to the rooted sheet's scale (figure height; the
                Breach's cable column squashed to the rooted skirt's length).
  6. compose  - eight figures per frame letter, rotation order, 40 px apart, on
                the magenta Gemini uses: gem_consortium_fix_<L>.png, read by
                gemini_enemy's CONSORTIUM spec as plain one-row sheets.

R (the core bright) is Q with the core's blue lifted towards white; D is B.
Nothing here writes outside work/ (gemini_enemy.guard_out); the preview goes
to docs/art/previews/ (an HTML page, no source image), the install patch to
work/art/enemies_gemini/consortium/, run by the PM on the CEO's OK.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402
import gemini_enemy as ge  # noqa: E402

ROOT = ge.ROOT
PREFIX = "gem_consortium_"
FIX_PREFIX = "gem_consortium_fix_"
SOURCES = {   # key: (file, figures, rows): the PM's Gemini sheets (work/, D77)
    "rooted": ("gem_consortium_rooted.png", 5, 1),    # phase 1, Q
    "turn": ("gem_consortium_turn.png", 5, 1),        # phase 2 standing, B/D
    "walk": ("gem_consortium_walk.png", 10, 2),       # A (top row) / C (bottom row)
    "aim": ("gem_consortium_aim.png", 10, 2),         # E orb tell (top) / F rocket tell (bottom)
    "fire": ("gem_consortium_fire.png", 5, 1),        # the discarded fire sheet: H (pain) and the knot for G
    "fire_v2": ("gem_consortium_fire_v2.png", 5, 1),  # G
    "breach": ("gem_consortium_breach.png", 5, 1),    # S
    "death": ("gem_consortium_death.png", 5, 1),      # I-O
}
REF_KEY = "rooted"
FRONT, Q34, PROFILE, BACK34, BACK = 0, 1, 2, 3, 4
VIEWS = 5
FAR_FROM = (BACK34, PROFILE, Q34)      # rotations 6, 7, 8: these views, not mirrored, halves swapped
LETTERS = {   # letter: (source, first view of its five)
    "Q": ("rooted", 0), "B": ("turn", 0), "A": ("walk", 0), "C": ("walk", 5),
    "E": ("aim", 0), "F": ("aim", 5), "G": ("fire_v2", 0), "H": ("fire", 0), "S": ("breach", 0),
}
DERIVED_LETTERS = {"R": "Q"}           # R: Q with the core bright
DEATH_KEY = "death"
SEP_GAP = 40           # px of background between the composed figures (gemini_enemy.ATTACH_PX is 12)
FIX_BG = (250, 6, 248)  # the composed sheets' background: Gemini's magenta
MIN_KEEP = 30          # px: after a repair, pieces smaller than this go (crumbs of a dropped arm)

# Scale: every sheet to the rooted sheet's. By the front view's height (head to
# floor) where the lower body is as long (aim, walk: half-size sheets); the
# Breach by its head-to-belt height, its cable column squashed (below).
SCALE_BY_HEIGHT = ("turn", "walk", "aim", "fire", "fire_v2", "death")
BELT_ROW = {"rooted": 212, "breach": 216}   # sheet rows of the belt's lower edge, front view (x4 zooms)
SCALE_ANCHOR_VIEW = 0


# ------------------------------------------------------------------ cutting
def poly_mask(shape: tuple[int, int], pts) -> np.ndarray:
    im = Image.new("1", (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([tuple(map(float, p)) for p in pts], fill=1)
    return np.array(im, bool)


def rect(x0, y0, x1, y1) -> tuple:
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


@dataclass
class View:
    """One figure on its sheet's full canvas (sheet coordinates)."""
    rgb: np.ndarray
    mask: np.ndarray

    def copy(self) -> "View":
        return View(self.rgb.copy(), self.mask.copy())

    def box(self) -> tuple[int, int, int, int]:
        ys, xs = np.nonzero(self.mask)
        return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


# OWN: (view, polygon) - everything of the sheet's foreground inside goes to that view
OWN: dict[str, tuple] = {}


PAD = 96   # px of empty canvas added left and right of every sheet: a mirror may reach past its edge


def sheet_mask(shape: tuple[int, int], pts) -> np.ndarray:
    """A polygon given in Gemini's sheet pixels, on the padded canvas."""
    return poly_mask(shape, [(x + PAD, y) for x, y in pts])


def cut(key: str, ref_dir: Path = ge.REF_DIR) -> list[View]:
    file, count, rows = SOURCES[key]
    rgb = ge.load_rgb(ref_dir / file)
    fg = ge.key_background(rgb, ge.estimate_background(rgb))
    masks = ge.figures(fg, count)
    if rows > 1:
        masks = ge.grid_order(masks, rows, rgb.shape[0])
    for k, pts in OWN.get(key, ()):
        p = poly_mask(fg.shape, pts) & fg
        masks = [m & ~p for m in masks]
        masks[k] = masks[k] | p
    rgb = np.pad(rgb, ((0, 0), (PAD, PAD), (0, 0)))
    return [View(rgb.copy(), np.pad(m, ((0, 0), (PAD, PAD)))) for m in masks]


# ---------------------------------------------------------------- materials
# Measured on the rooted sheet's front view (gem_consortium_rooted.png):
# Reich flesh ~(123,141,127), SS helmet ~(79,95,88), rack ~(66,69,56),
# M1 helmet ~(108,117,84), Legion flesh ~(169,80,107), chrome ~(171,189,206),
# armband ~(185,9,9), the core ~(109,192,250).
GREEN_OVER_RED = 6     # Reich grey-green: green this much over red ...
GREEN_OVER_BLUE = 3    # ... and over blue, blue not far under red (not olive)
PINK_OVER_GREEN = 30   # Legion flesh: red this much over green, blue not under green
OLIVE_BLUE_GAP = 8     # olive (rack, M1): blue this much under red and ...
OLIVE_BLUE_GAP_G = 12  # ... under green
CHROME_BLUE = (10, 60)  # chrome: blue over red by this much (more is a glow)
GLOW_BLUE = 40         # a glow (the core, an orb): blue this much over red ...
GLOW_MIN_B = 120       # ... and this bright
FIRE_RED = 150         # a flame: red this bright and ...
FIRE_GAP = 60          # ... this much over blue
WHITE_MIN = 205        # white-hot: every channel over this
RED_MIN = 90           # the armband: red over this, green and blue under RED_RATIO of it
RED_RATIO = 0.35
HELMET_ROWS = 40       # rows (rooted scale) under a figure's top that are its helmets
RAMP_BINS = 24
FIELD_LIGHT = 160      # swap: an armband field's pixel is this light in every channel ...
NEUTRAL_SPREAD = 60    # ... and this unsaturated (also the SS decal's grey)
BAND_REACH = 14        # px from the band's red that its field may lie
DECAL_LUM = 110        # swap: a neutral pixel this light in the helmets' rows is the SS decal
DECAL_DIM = 0.7        # ... painted the M1's olive this much darker
BRACER_Q = (0.55, 0.25)  # swap: the armband's chrome percentile, + this x its luminance (one light bracer)


def materials(rgb: np.ndarray) -> dict[str, np.ndarray]:
    x = rgb.astype(np.int32)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    red = (r > RED_MIN) & (g < RED_RATIO * r) & (b < RED_RATIO * r)
    glow = (b > r + GLOW_BLUE) & (b > GLOW_MIN_B)
    fire = (r > FIRE_RED) & (r > b + FIRE_GAP) & (g > b) & ~red
    white = x.min(axis=-1) > WHITE_MIN
    pink = (r > g + PINK_OVER_GREEN) & (b > g - 8) & ~red & ~fire
    green = (g > r + GREEN_OVER_RED) & (g > b + GREEN_OVER_BLUE) & (b >= r - 8)
    olive = (g >= r - 4) & (b < r - OLIVE_BLUE_GAP) & (b < g - OLIVE_BLUE_GAP_G) & ~green & ~fire
    chrome = (b > r + CHROME_BLUE[0]) & (b <= r + CHROME_BLUE[1]) & (b >= g - 2) & ~pink & ~glow
    return {"red": red, "glow": glow, "fire": fire, "white": white, "pink": pink, "green": green,
            "olive": olive, "chrome": chrome}


def luminance(rgb: np.ndarray) -> np.ndarray:
    return rgb.astype(np.float64) @ np.array([0.299, 0.587, 0.114])


@dataclass
class Ramp:
    """A material's colours by luminance percentile."""
    lums: np.ndarray       # sorted luminances of its pixels
    colours: np.ndarray    # RAMP_BINS x 3: the mean colour of each percentile bin

    @classmethod
    def of(cls, rgb: np.ndarray, sel: np.ndarray) -> "Ramp":
        px = rgb[sel].astype(np.float64)
        if len(px) < RAMP_BINS:
            raise ValueError("a material ramp needs more pixels")
        order = np.argsort(luminance(px))
        px = px[order]
        bins = np.array_split(np.arange(len(px)), RAMP_BINS)
        return cls(np.sort(luminance(rgb[sel])), np.array([px[i].mean(axis=0) for i in bins]))

    def percentile(self, lum: np.ndarray) -> np.ndarray:
        return np.searchsorted(self.lums, lum) / max(1, len(self.lums))

    def at_lum(self, lum: np.ndarray) -> np.ndarray:
        """The colour of the ramp at the same luminance (shading kept as drawn);
        past the ramp's ends its end colour scaled to that luminance."""
        bl = luminance(self.colours)
        out = np.stack([np.interp(lum, bl, self.colours[:, c]) for c in range(3)], axis=1)
        k = np.where(lum > bl[-1], lum / max(bl[-1], 1.0), np.where(lum < bl[0], lum / max(bl[0], 1.0), 1.0))
        return out * k[:, None]

    def at(self, q: np.ndarray) -> np.ndarray:
        k = np.clip(q * RAMP_BINS - 0.5, 0, RAMP_BINS - 1)
        lo = np.floor(k).astype(int)
        hi = np.minimum(lo + 1, RAMP_BINS - 1)
        t = (k - lo)[:, None]
        return self.colours[lo] * (1 - t) + self.colours[hi] * t


def gradient(stops) -> Ramp:
    """An analytic ramp (a flash's fire, an orb's blue) from (luminance, rgb) stops."""
    ls = np.linspace(0, 255, 256)
    cols = np.array([[np.interp(v, [s[0] for s in stops], [s[1][c] for s in stops]) for c in range(3)] for v in ls])
    bins = np.array_split(np.arange(256), RAMP_BINS)
    return Ramp(ls, np.array([cols[i].mean(axis=0) for i in bins]))


FIRE_RAMP = ((0, (60, 8, 4)), (90, (190, 50, 12)), (150, (245, 135, 30)), (200, (255, 210, 90)),
             (255, (255, 250, 225)))
BLUE_RAMP = ((0, (10, 16, 70)), (90, (30, 80, 220)), (150, (90, 160, 255)), (200, (175, 215, 255)),
             (255, (245, 250, 255)))
LAMP_RAMP = ((0, (40, 40, 36)), (120, (150, 146, 120)), (200, (235, 228, 170)), (255, (255, 252, 225)))
DARK_RAMP = ((0, (8, 8, 8)), (128, (40, 38, 34)), (255, (90, 88, 80)))      # a muzzle's dark mouth


_RAMPS: dict[str, Ramp] = {}


def ramps(ref_dir: Path = ge.REF_DIR) -> dict[str, Ramp]:
    """The materials' ramps, from the rooted front view; analytic fire/blue/lamp/dark."""
    if not _RAMPS:
        v = cut(REF_KEY, ref_dir)[FRONT]
        x0, y0, x1, y1 = v.box()
        mats = materials(v.rgb)
        rows = np.arange(v.mask.shape[0])[:, None]
        head = v.mask & (rows < y0 + HELMET_ROWS)
        body = v.mask & ~head
        _RAMPS.update({
            "gflesh": Ramp.of(v.rgb, mats["green"] & body), "pink": Ramp.of(v.rgb, mats["pink"] & body),
            "stahl": Ramp.of(v.rgb, mats["green"] & head), "m1": Ramp.of(v.rgb, mats["olive"] & head),
            "rack": Ramp.of(v.rgb, mats["olive"] & body), "chrome": Ramp.of(v.rgb, mats["chrome"] & body),
            "fire": gradient(FIRE_RAMP), "blue": gradient(BLUE_RAMP), "lamp": gradient(LAMP_RAMP),
            "dark": gradient(DARK_RAMP),
        })
    return _RAMPS


CLASS_RAMP = {"green": "gflesh", "pink": "pink", "olive": "rack", "chrome": "chrome", "glow": "blue",
              "fire": "fire", "red": "chrome", "white": "chrome"}


def remap(rgb: np.ndarray, sel: np.ndarray, src: str, dst: str, by: str = "pct") -> None:
    """Pixels `sel` (of ramp `src`'s material) take ramp `dst`'s colour, in place:
    at their percentile in `src` (`pct`), or at their own luminance (`lum`: the
    drawn shading kept, for flesh and helmets of like brightness)."""
    if not sel.any():
        return
    R = ramps()
    lum = luminance(rgb[sel])
    if by == "lum":
        rgb[sel] = np.clip(R[dst].at_lum(lum), 0, 255).astype(np.uint8)
        return
    q = R[src].percentile(lum) if src in R else lum / 255.0
    rgb[sel] = np.clip(R[dst].at(q), 0, 255).astype(np.uint8)


def swap_halves(v: View, helmet_rows: int) -> View:
    """The other side's picture of a side view (rotations 6-8): the two halves'
    materials exchanged. In the helmets' rows the SS helmet's grey-green and
    the M1's olive trade places; below them the flesh, and the near arm's
    rack and armband become the Legion's chrome."""
    out = v.copy()
    mats = materials(v.rgb)
    x0, y0, x1, y1 = v.box()
    rows = np.arange(v.mask.shape[0])[:, None]
    head = v.mask & (rows < y0 + helmet_rows)
    body = v.mask & ~head
    x = v.rgb.astype(np.int32)
    spread = x.max(axis=-1) - x.min(axis=-1)
    lum = luminance(v.rgb)
    light = (x.min(axis=-1) > FIELD_LIGHT) & (spread < NEUTRAL_SPREAD)
    band = ge._dilate(mats["red"] & v.mask, BAND_REACH) & body & (mats["red"] | mats["white"] | light)
    decal = head & ~mats["pink"] & (lum > DECAL_LUM) & (spread < NEUTRAL_SPREAD)
    for cls, zone, src, dst in (
            ("green", head, "stahl", "m1"), ("olive", head, "m1", "stahl"), ("pink", head, "pink", "gflesh"),
            ("green", body, "gflesh", "pink"), ("pink", body, "pink", "gflesh"), ("olive", body, "rack", "chrome")):
        remap(out.rgb, mats[cls] & zone & ~band & ~decal, src, dst, "pct" if src == "rack" else "lum")
    # the armband (its red and its field) becomes a chrome bracer; the SS decal goes under the M1's olive
    q = BRACER_Q[0] + BRACER_Q[1] * lum[band] / 255.0
    out.rgb[band] = np.clip(ramps()["chrome"].at(q), 0, 255).astype(np.uint8)
    out.rgb[decal] = np.clip(ramps()["m1"].at_lum(lum[decal] * DECAL_DIM), 0, 255).astype(np.uint8)
    return out


# ------------------------------------------------------------------ repairs
def op_drop(v: View, pts) -> None:
    v.mask &= ~sheet_mask(v.mask.shape, pts)


def op_recolour(v: View, pts, cls: str, src: str, dst: str, by: str = "pct") -> None:
    """Pixels of material `cls` ("any": all) inside the polygon take ramp `dst`
    (from `src`'s percentile, or at their own luminance: remap)."""
    sel = sheet_mask(v.mask.shape, pts) & v.mask
    if cls != "any":
        sel &= materials(v.rgb)[cls]
    remap(v.rgb, sel, src, dst, by)


def op_hue(v: View, pts, to: str) -> None:
    """A glow's blue becomes a flash's fire (`fire`), a flash's fire an orb's blue
    (`blue`), a glow a plain lamp (`lamp`): by luminance, white-hot included."""
    m = sheet_mask(v.mask.shape, pts) & v.mask
    mats = materials(v.rgb)
    src = {"fire": ("glow", "white"), "blue": ("fire", "white", "red"), "lamp": ("glow", "white"),
           "dark": ("glow", "white")}[to]
    sel = m & np.logical_or.reduce([mats[c] for c in src])
    remap(v.rgb, sel, "-", to)


def register(dst: View, src: View, rows: tuple[int, int], guess: tuple[int, int], r: int) -> tuple[int, int]:
    """(dx, dy) moving `src` onto `dst`: the least mean colour difference over dst's
    figure in `rows` where the moved src is figure too."""
    a = dst.rgb.astype(np.int32)
    band = np.zeros_like(dst.mask)
    band[rows[0]:rows[1]] = True
    band &= dst.mask
    best = None
    for dy in range(guess[1] - r, guess[1] + r + 1):
        for dx in range(guess[0] - r, guess[0] + r + 1):
            sm = ge.shifted(src.mask, dy, dx, False) & band
            if sm.sum() < 0.5 * band.sum():
                continue
            d = float(np.abs(a - ge.shifted(src.rgb, dy, dx).astype(np.int32))[sm].mean())
            if best is None or d < best[0]:
                best = (d, dx, dy)
    if best is None:
        raise ValueError("register: no overlap")
    return best[1], best[2]


LOWER_BAND = 50   # rows over the cut whose colours register the other view
LOWER_SEARCH = 6


def op_lower(v: View, src: View, y_cut: int, guess: tuple[int, int], excl=()) -> tuple[int, int]:
    """Every row from `y_cut` down taken from `src` (registered on the rows above
    the cut); `excl` (src sheet polygons) left out: its hanging arms."""
    dx, dy = register(v, src, (y_cut - LOWER_BAND, y_cut), guess, LOWER_SEARCH)
    sm = src.mask.copy()
    for pts in excl:
        sm &= ~sheet_mask(sm.shape, pts)
    sm, srgb = ge.shifted(sm, dy, dx, False), ge.shifted(src.rgb, dy, dx)
    v.mask[y_cut:] = sm[y_cut:]
    low = v.rgb[y_cut:]
    low[sm[y_cut:]] = srgb[y_cut:][sm[y_cut:]]
    return dx, dy


def op_paste(v: View, src: View, pts, dx: int, dy: int, scale: float = 1.0, flip: bool = False) -> None:
    """The part of `src` inside the polygon (src sheet pixels), optionally
    mirrored and scaled about its box's top-left, its top-left moved by (dx, dy)."""
    sel = sheet_mask(src.mask.shape, pts) & src.mask
    ys, xs = np.nonzero(sel)
    y0, x0, y1, x1 = ys.min(), xs.min(), ys.max() + 1, xs.max() + 1
    rgb, m = src.rgb[y0:y1, x0:x1], sel[y0:y1, x0:x1]
    if flip:
        rgb, m = rgb[:, ::-1], m[:, ::-1]
    if scale != 1.0:
        w, h = max(1, round((x1 - x0) * scale)), max(1, round((y1 - y0) * scale))
        rgb = np.asarray(Image.fromarray(np.ascontiguousarray(rgb)).resize((w, h), Image.NEAREST))
        m = np.asarray(Image.fromarray(np.ascontiguousarray(m)).resize((w, h), Image.NEAREST))
    ty, tx = y0 + dy, x0 + dx
    H, W = v.mask.shape
    h, w = m.shape
    sy, sx = max(0, -ty), max(0, -tx)
    ey, ex = min(h, H - ty), min(w, W - tx)
    mm = m[sy:ey, sx:ex]
    sub_rgb = v.rgb[ty + sy:ty + ey, tx + sx:tx + ex]
    sub_rgb[mm] = rgb[sy:ey, sx:ex][mm]
    v.mask[ty + sy:ty + ey, tx + sx:tx + ex] |= mm


def op_fill(v: View, pts, axis: float) -> None:
    """The polygon (sheet pixels) made figure from the same figure's pixels
    mirrored about the column `axis`: a hole in the knot of cables, filled
    with its other side."""
    reg = sheet_mask(v.mask.shape, pts)
    ys, xs = np.nonzero(reg)
    sx = np.round(2 * (axis + PAD) - xs).astype(int)
    ok = (sx >= 0) & (sx < v.mask.shape[1])
    ys, xs, sx = ys[ok], xs[ok], sx[ok]
    got = v.mask[ys, sx] & ~reg[ys, sx]
    v.rgb[ys[got], xs[got]] = v.rgb[ys[got], sx[got]]
    v.mask[ys[got], xs[got]] = True


def op_graft(v: View, src: View, pts, guess: tuple[int, int], rows: tuple[int, int], holes_only: bool = False,
             search: int = 10) -> tuple[int, int]:
    """The part of `src` inside the polygon (src sheet pixels), moved to where
    `src` registers on this view over `rows`; `holes_only`: only where this
    view has no figure (a body healed under a part that was taken away)."""
    dx, dy = register(v, src, rows, guess, search)
    if holes_only:
        before = v.mask.copy()
        rgb0 = v.rgb.copy()
        op_paste(v, src, pts, dx, dy)
        v.rgb[before] = rgb0[before]
    else:
        op_paste(v, src, pts, dx, dy)
    return dx, dy


def op_fill_shift(v: View, pts, shifts) -> None:
    """Holes in the polygon (sheet pixels) made figure from the same figure
    `(dx, dy)` away, the first shift whose pixel is figure outside the polygon:
    the knot of cables carried on over a part that was taken away."""
    reg = sheet_mask(v.mask.shape, pts)
    H, W = v.mask.shape
    cols = np.arange(W)[None, :]
    has = v.mask.any(axis=1)
    first = np.where(has, v.mask.argmax(axis=1), W)[:, None]
    last = np.where(has, W - 1 - v.mask[:, ::-1].argmax(axis=1), -1)[:, None]
    inside = (cols >= first) & (cols <= last)       # within each row's outline: holes, not new silhouette
    todo = reg & inside & ~v.mask
    for dx, dy in shifts:
        ys, xs = np.nonzero(todo)
        sy, sx = ys + dy, xs + dx
        ok = (sy >= 0) & (sy < H) & (sx >= 0) & (sx < W)
        ys, xs, sy, sx = ys[ok], xs[ok], sy[ok], sx[ok]
        got = v.mask[sy, sx] & ~reg[sy, sx]
        v.rgb[ys[got], xs[got]] = v.rgb[sy[got], sx[got]]
        v.mask[ys[got], xs[got]] = True
        todo[ys[got], xs[got]] = False


def hull(points: np.ndarray) -> list[tuple[float, float]]:
    """Convex hull (monotone chain) of (x, y) points."""
    pts = sorted(set(map(tuple, points.tolist())))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def op_knot_fill(v: View, y_cut: int, shifts) -> None:
    """The knot of cables under `y_cut` made whole where an arm hung over it:
    its convex hull (the belt's corners to the knot's foot), the holes filled
    from the knot itself, `shifts` away (op_fill_shift's donors)."""
    H, W = v.mask.shape
    low = v.mask.copy()
    low[:y_cut] = False
    ys = np.flatnonzero(low.any(axis=1))
    if len(ys) == 0:
        return
    firsts = low[ys].argmax(axis=1)
    lasts = W - 1 - low[ys][:, ::-1].argmax(axis=1)
    pts = np.concatenate([np.stack([firsts, ys], 1), np.stack([lasts, ys], 1)])
    poly = poly_mask(v.mask.shape, hull(pts))
    poly[:y_cut] = False
    todo = poly & ~v.mask
    for dx, dy in shifts:
        yy, xx = np.nonzero(todo)
        sy, sx = yy + dy, xx + dx
        ok = (sy >= y_cut) & (sy < H) & (sx >= 0) & (sx < W)
        yy, xx, sy, sx = yy[ok], xx[ok], sy[ok], sx[ok]
        got = v.mask[sy, sx] & ~todo[sy, sx]
        v.rgb[yy[got], xx[got]] = v.rgb[sy[got], sx[got]]
        v.mask[yy[got], xx[got]] = True
        todo[yy[got], xx[got]] = False


BRIGHT_SPREAD = 80     # drop_bright: a light pixel this unsaturated is a rocket's body


def op_drop_bright(v: View, pts, lum_min: float) -> None:
    """Inside the polygon, only what is fire, red, or light and unsaturated goes:
    a rocket and its flame in front of the smoke, the smoke kept."""
    m = sheet_mask(v.mask.shape, pts) & v.mask
    mats = materials(v.rgb)
    x = v.rgb.astype(np.int32)
    light = (luminance(v.rgb) > lum_min) & (x.max(axis=-1) - x.min(axis=-1) < BRIGHT_SPREAD)
    v.mask &= ~(m & (mats["fire"] | mats["red"] | mats["pink"] | light))


GEN_DIR = ROOT / "work" / "art" / "enemies_gemini" / "consortium" / "fooocus"
GEN_MISSING: list[str] = []


def op_gen(v: View, name: str, pts) -> None:
    """D127: a hole Gemini never drew (the hip under a hanging arm) from Fooocus'
    inpaint of this very view, chosen by eye and cached as GEN_DIR/<name>.png
    (the padded view's canvas); the build never runs SDXL. Missing: left as is."""
    p = GEN_DIR / f"{name}.png"
    if not p.exists():
        GEN_MISSING.append(name)
        return
    with Image.open(p) as im:
        rgba = np.asarray(im.convert("RGBA"))
    reg = sheet_mask(v.mask.shape, pts) & (rgba[..., 3] > 127)
    v.rgb[reg] = rgba[..., :3][reg]
    v.mask |= reg


# (key, view): the repairs, in order (REPAIR_NOTES says why, for the CEO's sheet)
REPAIRS: dict[tuple[str, int], tuple] = {}
REPAIR_NOTES: dict[tuple[str, int], tuple[str, str]] = {}
# (key, view): repairs after the mirror, in canonical sheet coordinates (the
# canonical of a 0-based sheet column x is x0 + x1 - 1 - x over the figure's box, or 2 axis - x with KEEP)
REPAIRS_POST: dict[tuple[str, int], tuple] = {}
# (key, view): (body axis column, polygons kept where they are) - the body mirrored, the arms not
KEEP: dict[tuple[str, int], tuple[float, tuple]] = {}


def apply_ops(v: View, ops, cuts) -> View:
    for op in ops:
        kind, args = op[0], op[1:]
        if kind == "drop":
            op_drop(v, *args)
        elif kind == "recolour":
            op_recolour(v, *args)
        elif kind == "hue":
            op_hue(v, *args)
        elif kind == "lower":
            src_key, src_view, y_cut, guess, *excl = args
            op_lower(v, cuts[src_key][src_view], y_cut, guess, excl[0] if excl else ())
        elif kind == "paste":
            src_key, src_view, pts, dx, dy, *rest = args
            op_paste(v, cuts[src_key][src_view], pts, dx, dy, *rest)
        elif kind == "fill":
            op_fill(v, *args)
        elif kind == "fill_shift":
            op_fill_shift(v, *args)
        elif kind == "knot_fill":
            op_knot_fill(v, *args)
        elif kind == "drop_bright":
            op_drop_bright(v, *args)
        elif kind == "graft":
            src_key, src_view, pts, guess, rows, *rest = args
            op_graft(v, cuts[src_key][src_view], pts, guess, rows, *rest)
        elif kind == "gen":
            op_gen(v, *args)
        else:
            raise ValueError(f"unknown repair {kind!r}")
    if ops:
        v.mask = ge._drop_crumbs(v.mask)
        lab, n = ge.label(v.mask)
        if n > 1:
            sizes = np.bincount(lab.ravel(), minlength=n + 1)
            v.mask &= np.isin(lab, [i for i in range(1, n + 1) if sizes[i] >= MIN_KEEP])
    return v


class CanonCuts:
    """cuts[key][view] seen through canonical(): the sources of REPAIRS_POST."""
    def __init__(self, cuts: dict):
        self.cuts = cuts

    def __getitem__(self, key: str) -> list[View]:
        return [canonical(v, (key, i)) for i, v in enumerate(self.cuts[key])]


def repaired(key: str, view: int, cuts: dict) -> View:
    """The view after REPAIRS, in Gemini's orientation."""
    return apply_ops(cuts[key][view].copy(), REPAIRS.get((key, view), ()), cuts)


def canonical_fixed(key: str, view: int, fixed: View, cuts: dict) -> View:
    """canonical(repaired view), then REPAIRS_POST in canonical sheet coordinates."""
    return apply_ops(canonical(fixed, (key, view)), REPAIRS_POST.get((key, view), ()), CanonCuts(cuts))


def canonical(v: View, key: tuple[str, int] | None = None) -> View:
    """The view mirrored: the Reich half on its left. About its box's centre,
    or (KEEP) about the body's axis with the kept polygons left in place."""
    axis, keep = KEEP.get(key, (None, ())) if key else (None, ())
    H, W = v.mask.shape
    kept = np.zeros_like(v.mask)
    for pts in keep:
        kept |= sheet_mask(v.mask.shape, pts)
    kept &= v.mask
    if axis is None:
        x0, _, x1, _ = v.box()
        s = x0 + x1 - 1
    else:
        s = int(round(2 * (axis + PAD)))
    out = View(np.zeros_like(v.rgb), np.zeros_like(v.mask))
    ys, xs = np.nonzero(v.mask & ~kept)
    tx = s - xs
    ok = (tx >= 0) & (tx < W)
    out.rgb[ys[ok], tx[ok]] = v.rgb[ys[ok], xs[ok]]
    out.mask[ys[ok], tx[ok]] = True
    out.rgb[kept] = v.rgb[kept]
    out.mask |= kept
    return out


# ------------------------------------------------------- the repairs table
# Every polygon in Gemini's sheet pixels, read off x3-x5 zooms of the sheet.
# Gemini's orientation: the Reich half on ITS right (front view: viewer's left).
BELT_CUT = 228          # fire_v2 / fire: the row under the belt where the knot of cables starts
WALK_CUT = (126, 124)   # walk: the front view's belt (A0), the 3/4 back's and back's (A3, A4)
WALK_ROW = 210          # walk: the bottom row's figures stand this much lower on the sheet
AIM_ROW = 213           # aim: likewise
FIRE_ARMS = {           # fire.png: its hanging arms, out of the knot that G borrows
    0: (rect(14, 180, 70, 395), rect(190, 178, 244, 348)),
    1: (rect(255, 190, 334, 392), rect(404, 180, 472, 338)),
    2: (((503, 188), (565, 188), (566, 250), (596, 312), (612, 380), (560, 380), (530, 318), (503, 255)),),
    3: (rect(622, 185, 664, 325), rect(708, 190, 796, 385)),
    4: (rect(798, 188, 844, 338), rect(952, 188, 1010, 330)),
}
# the knot's hole where fire.png's arm hung over it: carried on from the knot below / beside
H_LIGHT = 100           # fire.png: under the rack's mouth, anything lighter than this (and unsaturated) is the rocket
F2_HIP = 306            # aim F profile: under the elbow the hip the hanging rack hid, made of the knot
AIM_KNOT = 338          # aim, bottom row: the row under the belt where the knot starts
KNOT_SHIFTS_AIM = ((0, 35), (0, 50), (-15, 20), (15, 20), (0, 65), (-30, 0), (30, 0), (0, -20))
KNOT_SHIFTS = ((0, 70), (0, 100), (-30, 40), (30, 40), (0, 130), (-60, 0), (60, 0), (0, -40), (0, -70))

OWN["fire_v2"] = (
    # the profile's levelled rack, its barrels and their flame cross the 3/4 back view's shoulders
    (2, ((585, 90), (706, 90), (715, 96), (715, 129), (706, 137), (585, 138))),
)

OWN["death"] = (
    # frame 3's pauldron and chrome forearm reach past frame 4's rack; frame 5's wreck under frame 4's arm
    (2, rect(638, 82, 681, 142)),
    (2, ((630, 235), (664, 250), (673, 280), (671, 303), (645, 306), (630, 300))),
    (4, rect(840, 330, 872, 432)),
)

FV2_ORB_ARM = ((8, 58), (64, 58), (82, 78), (82, 140), (8, 140))          # front: Reich arm, an orb in its fist
FV2_RACK_ARM = ((189, 20), (272, 20), (272, 100), (252, 152), (200, 158), (189, 140))   # front: Legion arm, the rack
E3_ARM = ((700, 80), (724, 80), (731, 98), (731, 165), (722, 186), (690, 186), (690, 98))   # the Legion arm hanging
E4_ARM = ((878, 82), (902, 82), (907, 100), (907, 168), (900, 190), (874, 190), (874, 100))
GRAFT_SEARCH = 3        # the aim sheet's rows differ in the arms: a wide search finds a wrong match
# rooted front, canonical: the Legion arm under the pauldron (x' = 261 - x), for the F front view
ROOTED_ARM_C = ((63, 118), (21, 118), (19, 325), (68, 325), (68, 190), (63, 150))
AIM_PER_ROOTED = 0.5086   # the aim sheet's scale to the rooted one (front heights 203 / 399)
F0_RING = ((134, 259), (160, 259), (169, 270), (169, 293), (160, 303), (134, 303), (125, 293), (125, 270))

REPAIRS.update({
    # ---- E (aim, top row): the orb tell, the Legion projector levelled
    ("aim", 1): (   # the Reich arm levelled a chrome projector, glowing: it is the rack, its mouth dark
        ("recolour", rect(203, 42, 252, 88), "chrome", "chrome", "rack"),
        ("hue", rect(203, 42, 252, 88), "dark")),
    ("aim", 3): (("drop", ((690, 98), (731, 98), (731, 165), (722, 186), (690, 186))),),   # a third arm
    ("aim", 4): (("drop", ((874, 100), (907, 100), (907, 168), (900, 190), (874, 190))),),  # the levelled arm, hanging too
    # ---- F (aim, bottom row): the rocket tell, the Reich rack raised
    ("aim", 5): (   # front: the rack (end-on) held up by the Legion arm, a second rack hanging from the Reich one
        ("recolour", F0_RING, "chrome", "chrome", "rack"),
        ("drop", rect(26, 302, 56, 390)),
        ("fill", rect(38, 330, 58, 392), 92)),
    ("aim", 7): (   # profile: a chrome projector pointing backwards; the Legion fist on the rack; the rack hanging too
        ("drop", rect(438, 258, 505, 294)),
        ("recolour", rect(548, 266, 567, 290), "pink", "pink", "gflesh", "lum"),
        ("drop", ((505, 312), (546, 312), (553, 335), (562, 375), (556, 386), (527, 386), (515, 355), (505, 345))),
        ("knot_fill", F2_HIP, KNOT_SHIFTS_AIM)),
    ("aim", 8): (   # 3/4 back: the Legion arm levelled backwards; the rack also hanging
        ("drop", rect(670, 258, 712, 296)),
        ("graft", "aim", 3, E3_ARM, (3, AIM_ROW), (238, 330), False, GRAFT_SEARCH),
        ("drop", rect(789, 318, 822, 390)),
        ("knot_fill", AIM_KNOT, KNOT_SHIFTS_AIM)),
    ("aim", 9): (   # back: likewise
        ("drop", rect(862, 258, 902, 298)),
        ("graft", "aim", 4, E4_ARM, (3, AIM_ROW - 3), (238, 330), False, GRAFT_SEARCH),
        ("drop", rect(968, 316, 1004, 392)),
        ("knot_fill", AIM_KNOT, KNOT_SHIFTS_AIM)),
    # ---- A (walk, top row): a cable skirt where the Reich leg goes; the bottom row's legs instead
    ("walk", 0): (("lower", "walk", 5, WALK_CUT[0], (0, -WALK_ROW)),),
    ("walk", 3): (("lower", "walk", 8, WALK_CUT[1], (0, -WALK_ROW)),),
    ("walk", 4): (("lower", "walk", 9, WALK_CUT[1], (0, -WALK_ROW)),),
    # ---- G (fire_v2): both arms firing; the legs replaced by fire.png's knot of cables and smoke
    ("fire_v2", 0): (   # front: each weapon in the other half's hand (the body is mirrored, the arms are not: KEEP)
        ("recolour", FV2_ORB_ARM, "green", "gflesh", "pink", "lum"),
        ("recolour", FV2_ORB_ARM, "red", "-", "chrome"),
        ("recolour", FV2_RACK_ARM, "pink", "pink", "gflesh", "lum"),
        ("lower", "fire", 0, BELT_CUT, (0, 0), FIRE_ARMS[0]),
        ("knot_fill", BELT_CUT, KNOT_SHIFTS)),
    ("fire_v2", 1): (   # 3/4 front: an orb at the rack's mouth, a rocket from the Legion arm's rack
        ("hue", rect(372, 86, 430, 132), "fire"),
        ("drop", ((450, 42), (492, 42), (492, 74), (463, 82), (450, 74))),
        ("hue", rect(426, 56, 478, 102), "blue"),
        ("recolour", rect(418, 68, 472, 132), "olive", "rack", "chrome"),
        ("lower", "fire", 1, BELT_CUT, (0, 0), FIRE_ARMS[1]),
        ("knot_fill", BELT_CUT, KNOT_SHIFTS)),
    ("fire_v2", 2): (   # profile: the rack and its flame are its own (OWN); the knot under the hanging rack
        ("lower", "fire", 2, BELT_CUT, (0, 0), FIRE_ARMS[2]),
        ("knot_fill", BELT_CUT, KNOT_SHIFTS)),
    ("fire_v2", 3): (   # 3/4 back: an orb from the Reich arm, a rocket fired backwards by the Legion one
        ("drop", rect(711, 97, 731, 127)),
        ("drop", ((540, 160), (632, 160), (632, 166), (664, 166), (664, 193), (540, 193))),
        ("hue", rect(724, 84, 774, 138), "fire"),
        ("graft", "turn", 3, rect(646, 88, 734, 140), (0, 0), (140, 200), True),
        ("lower", "fire", 3, BELT_CUT, (0, 0), FIRE_ARMS[3]),
        ("knot_fill", BELT_CUT, KNOT_SHIFTS)),
    ("fire_v2", 4): (
        ("lower", "fire", 4, BELT_CUT, (0, 0), FIRE_ARMS[4]),
        ("knot_fill", BELT_CUT, KNOT_SHIFTS)),
    # ---- H (fire.png, the discarded firing sheet): pain, its rockets and flashes taken away (smoke kept)
    ("fire", 0): (("drop_bright", rect(15, 310, 75, 395), H_LIGHT), ("hue", rect(192, 295, 242, 345), "lamp")),
    ("fire", 1): (("drop_bright", rect(280, 300, 335, 392), H_LIGHT), ("hue", rect(430, 290, 475, 335), "lamp")),
    ("fire", 2): (("drop_bright", rect(552, 300, 612, 380), H_LIGHT),),
    ("fire", 3): (("drop_bright", rect(752, 312, 800, 386), H_LIGHT),),
    ("fire", 4): (("hue", rect(802, 305, 842, 338), "lamp"),),
})
REPAIRS_POST.update({
    # F front: the Legion arm, now on the viewer's left, hangs: the rooted front's, scaled (canonical x' = 184 - x)
    ("aim", 5): (("drop", rect(0, 246, 32, 276)),     # a sliver of the end-on gun's rim, mirrored
                 ("paste", "rooted", 0, ROOTED_ARM_C, 26, 163, AIM_PER_ROOTED)),
})
KEEP.update({
    ("fire_v2", 0): (133, (FV2_ORB_ARM, FV2_RACK_ARM)),
    ("aim", 5): (92, (F0_RING,)),
})


# -------------------------------------------------------------------- scale
def front_height(views: list[View]) -> int:
    _, y0, _, y1 = views[SCALE_ANCHOR_VIEW].box()
    return y1 - y0


def sheet_scales(cuts: dict) -> dict[str, tuple[float, float | None]]:
    """key -> (scale to the rooted sheet, squash of the rows under the belt or None)."""
    ref_h = front_height(cuts[REF_KEY])
    out: dict[str, tuple[float, float | None]] = {REF_KEY: (1.0, None)}
    for k in SOURCES:
        if k in SCALE_BY_HEIGHT:
            out[k] = (ref_h / front_height(cuts[k]), None)
    _, rt, _, rb = cuts[REF_KEY][SCALE_ANCHOR_VIEW].box()
    _, bt, _, bb = cuts["breach"][SCALE_ANCHOR_VIEW].box()
    k = (BELT_ROW[REF_KEY] - rt) / (BELT_ROW["breach"] - bt)
    out["breach"] = (k, (rb - BELT_ROW[REF_KEY]) / ((bb - BELT_ROW["breach"]) * k))
    return out


def _resize(a: np.ndarray, w: int, h: int) -> np.ndarray:
    return np.asarray(Image.fromarray(np.ascontiguousarray(a)).resize((max(1, w), max(1, h)), Image.NEAREST))


def scaled(v: View, k: float, squash: tuple[int, float] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """(rgb, mask) of the figure's box, x k (nearest); with `squash` (belt row,
    factor) the rows under the belt are compressed by that factor too."""
    x0, y0, x1, y1 = v.box()
    rgb, m = v.rgb[y0:y1, x0:x1], v.mask[y0:y1, x0:x1]
    w, h = round((x1 - x0) * k), round((y1 - y0) * k)
    if squash is None:
        return _resize(rgb, w, h), _resize(m, w, h)
    belt = max(0, min(y1 - y0, squash[0] - y0))
    hb = round(belt * k)
    hl = round((y1 - y0 - belt) * k * squash[1])
    return (np.concatenate([_resize(rgb[:belt], w, hb), _resize(rgb[belt:], w, hl)]),
            np.concatenate([_resize(m[:belt], w, hb), _resize(m[belt:], w, hl)]))


# ------------------------------------------------------------------ compose
CORE_LIFT = 0.5        # R: the core's glow this far towards white (it breathes)


def lift_core(rgb: np.ndarray, mask: np.ndarray, k: float = CORE_LIFT) -> np.ndarray:
    out = rgb.copy()
    sel = mask & materials(rgb)["glow"]
    out[sel] = np.clip(rgb[sel] + (255 - rgb[sel].astype(np.float64)) * k, 0, 255).astype(np.uint8)
    return out


FRINGE_GAP = 40        # a pixel this much redder AND bluer than green is Gemini's magenta showing between cables
FRINGE_FROM = 0.55     # ... looked for under this fraction of the picture's height: the knot, not the flesh's shading


def defringe(rgb: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """The background's magenta left inside the figure (between the knot's
    cables, round the sparks) made a neutral dark grey of its luminance: the
    palette would turn it into red specks. Pink flesh (blue barely over
    green), the glows (red under green) and everything above the belt (the
    pink's magenta shadows) are not touched."""
    x = rgb.astype(np.int32)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    low = np.zeros_like(mask)
    low[int(FRINGE_FROM * mask.shape[0]):] = True
    sel = mask & low & (r > g + FRINGE_GAP) & (b > g + FRINGE_GAP)
    out = rgb.copy()
    v = np.clip(luminance(rgb[sel]) * 0.5, 0, 255).astype(np.uint8)
    out[sel] = np.stack([v, v, v], axis=1)
    return out


def compose(pics: list[tuple[np.ndarray, np.ndarray]], gap: int = SEP_GAP, bg=FIX_BG) -> np.ndarray:
    """The pictures in a row, feet on one line, `gap` px apart, on Gemini's magenta."""
    H = max(m.shape[0] for _, m in pics) + 2 * gap
    W = sum(m.shape[1] for _, m in pics) + gap * (len(pics) + 1)
    out = np.empty((H, W, 3), np.uint8)
    out[:] = np.array(bg, np.uint8)
    x = gap
    for rgb, m in pics:
        h, w = m.shape
        y = H - gap - h
        sub = out[y:y + h, x:x + w]
        sub[m] = rgb[m]
        x += w + gap
    return out


def letter_pictures(letter: str, cuts: dict, scales: dict) -> list[tuple[np.ndarray, np.ndarray]]:
    """Rotations 1-8 of a frame letter at the rooted scale."""
    key, first = LETTERS[letter]
    k, squash = scales[key]
    sq = (BELT_ROW[key], squash) if squash else None
    fixed = [repaired(key, first + i, cuts) for i in range(VIEWS)]
    pics = [scaled(canonical_fixed(key, first + i, fixed[i], cuts), k, sq) for i in range(VIEWS)]
    helmet = round(HELMET_ROWS / k)
    pics += [scaled(swap_halves(fixed[i], helmet), k, sq) for i in FAR_FROM]
    return pics


def death_pictures(cuts: dict, scales: dict) -> list[tuple[np.ndarray, np.ndarray]]:
    k, _ = scales[DEATH_KEY]
    return [scaled(canonical_fixed(DEATH_KEY, i, repaired(DEATH_KEY, i, cuts), cuts), k) for i in range(VIEWS)]


def fix_sheets(ref_dir: Path = ge.REF_DIR) -> dict[str, Path]:
    """Writes gem_consortium_fix_<L>.png for every rotated letter and the death sheet."""
    cuts = {k: cut(k, ref_dir) for k in SOURCES}
    scales = sheet_scales(cuts)
    out = {}
    sheets = {L: letter_pictures(L, cuts, scales) for L in LETTERS}
    for L, base in DERIVED_LETTERS.items():
        sheets[L] = [(lift_core(rgb, m), m) for rgb, m in sheets[base]]
    sheets["death"] = death_pictures(cuts, scales)
    for name, pics in sheets.items():
        pics = [(defringe(rgb, m), m) for rgb, m in pics]
        p = ref_dir / f"{FIX_PREFIX}{name}.png"
        ge.guard_out(p)
        Image.fromarray(compose(pics), "RGB").save(p)
        out[name] = p
    return out


# ------------------------------------------------- D127: Fooocus, as a helper
# Only where Gemini never drew what a repair uncovers (the hip under an arm
# that hung over it), and only as an inpaint of that very view: the job's
# init is the repaired view, the mask the hole. `gen-jobs` writes the job for
# work/art/armband_fooocus/fooocus_inpaint.py (Fooocus' own python, no
# downloads: it refuses any model not on disk); `gen-pick NAME SEED` keys the
# chosen output and caches it as GEN_DIR/NAME.png for op_gen. The build reads
# the cache and never runs SDXL.
FOOOCUS_ROOT = Path(r"Z:\Fooocus\Fooocus_win64_2-5-0\Fooocus_win64_2-5-0")
FOOOCUS_DIR = FOOOCUS_ROOT / "Fooocus"
FOOOCUS_PY = FOOOCUS_ROOT / "python_embeded" / "python.exe"
FOOOCUS_MODEL = "juggernautXL_v8Rundiffusion.safetensors"
INPAINT_SCRIPT = ROOT / "work" / "art" / "armband_fooocus" / "fooocus_inpaint.py"
GEN_SEEDS = (11, 23, 37, 41)
GEN_GROW = 2            # px the inpaint mask grows past the hole (the model redraws its edge)
GEN_INIT = (58, 58, 56)  # the hole's start colour: the knot's dark grey
GEN_UP = 4              # the crop is enlarged this much (nearest) before SDXL: it works near 1024 px
GEN_NEG = ("arm, hand, weapon, gun, rocket launcher, armband, text, letters, watermark, blurry, photo, 3d render, "
           "extra limbs, legs, feet, magenta, pink")
GEN: dict[str, tuple] = {
    # name: (key, view, crop (sheet x0, y0, x1, y1), prompt). Tried 2026-10-24 on the F profile's hip
    # ("aim_7_hip", denoise 0.9, seeds 11/23/37/41): SDXL painted green legs and skulls, nothing of the
    # knot; rejected for the knot carried on from below (op_knot_fill). Kept for the next hole.
}


def _gen_spec(name: str) -> tuple[str, int, tuple, tuple]:
    key, view, crop, prompt = GEN[name]
    hole = next(op[2] for op in REPAIRS[(key, view)] if op[0] == "gen" and op[1] == name)
    return key, view, crop, hole


def gen_jobs(ref_dir: Path = ge.REF_DIR) -> Path:
    """Writes each GEN entry's init and mask (the repaired view, the hole) and job.json."""
    GEN_DIR.mkdir(parents=True, exist_ok=True)
    ge.guard_out(GEN_DIR)
    cuts = {k: cut(k, ref_dir) for k in SOURCES}
    runs = []
    for name, (key, view, crop, prompt) in GEN.items():
        _, _, _, hole_pts = _gen_spec(name)
        v = apply_ops(cuts[key][view].copy(), [op for op in REPAIRS[(key, view)] if op[0] != "gen"], cuts)
        x0, y0, x1, y1 = crop
        sl = (slice(y0, y1), slice(x0 + PAD, x1 + PAD))
        hole = sheet_mask(v.mask.shape, hole_pts) & ~v.mask
        img = np.empty_like(v.rgb[sl])
        img[:] = np.array(FIX_BG, np.uint8)
        img[v.mask[sl]] = v.rgb[sl][v.mask[sl]]
        img[hole[sl]] = GEN_INIT
        msk = ge._dilate(hole, GEN_GROW)[sl]
        up = lambda a, mode: Image.fromarray(a).resize((a.shape[1] * GEN_UP, a.shape[0] * GEN_UP), mode)
        up(img, Image.NEAREST).save(GEN_DIR / f"{name}_init.png")
        up((msk * 255).astype(np.uint8), Image.NEAREST).save(GEN_DIR / f"{name}_mask.png")
        runs.append({"name": name, "image": str(GEN_DIR / f"{name}_init.png"), "mask": str(GEN_DIR / f"{name}_mask.png"),
                     "prompt": prompt, "negative": GEN_NEG, "denoise": 0.9, "seeds": list(GEN_SEEDS),
                     "steps": 30, "cfg": 5.0})
    job = GEN_DIR / "job.json"
    job.write_text(json.dumps({"fooocus": str(FOOOCUS_DIR), "model": FOOOCUS_MODEL, "out": str(GEN_DIR / "out"),
                               "runs": runs}, indent=1), encoding="utf-8")
    return job


def gen_pick(name: str, seed: int, ref_dir: Path = ge.REF_DIR) -> Path:
    """The chosen output, reduced to the sheet's pixels, keyed, cached for op_gen."""
    key, view, crop, hole_pts = _gen_spec(name)
    x0, y0, x1, y1 = crop
    with Image.open(GEN_DIR / "out" / f"{name}_s{seed}.png") as im:
        out = np.asarray(im.convert("RGB").resize((x1 - x0, y1 - y0), Image.BOX))
    shape = cut(key, ref_dir)[view].mask.shape
    canvas = np.zeros(shape + (4,), np.uint8)
    keep = ge.key_background(out, np.array(FIX_BG, np.float64))
    sub = canvas[y0:y1, x0 + PAD:x1 + PAD]
    sub[..., :3] = out
    sub[..., 3] = keep * 255
    p = GEN_DIR / f"{name}.png"
    ge.guard_out(p)
    Image.fromarray(canvas, "RGBA").save(p)
    return p


# ------------------------------------------------------------ the CEO's sheet
SHEET_HTML = ROOT / "docs" / "art" / "previews" / "2026-10-24_P4_consortium-gemini.html"
ACTOR = ROOT / "src" / "zscript" / "monsters" / "consortium.zs"
PROV_FOLDER, PROV_SPRITE, PROV_SCALE = "panzermensch", "SDPS", 1.75   # what it wears today (PROVISIONAL-D116)
# consortium.zs: Translation "0:255=%[0.04,0.02,0.12]:[1.10,1.40,2.00]", imitated for the comparison only
# (NOT VERIFIED against the engine's palettised tint)
PROV_RAMP = ((0.04, 0.02, 0.12), (1.10, 1.40, 2.00))
LINEUP_ZOOM = 2
LINEUP = (   # (label, lump, folder or "new"/"prov")
    ("provisional today (SDPS x1.75 cobalt)", "SDPSA1", "prov"), ("new Q1 (phase 1)", "SDCNQ1", "new"),
    ("new B1 (phase 2)", "SDCNB1", "new"), ("Colossus SDLC B1", "SDLCB1", "colossus"),
    ("The General SDGN B1", "SDGNB1", "general"), ("Panzermensch Schwer", "SDPSA1", "panzermensch"),
    ("new E1 (orbs)", "SDCNE1", "new"), ("new F1 (rockets)", "SDCNF1", "new"),
    ("new G1 (fires)", "SDCNG1", "new"), ("new S1 (breach)", "SDCNS1", "new"),
)
# (key, view): (lump, what was wrong and what was done) - the before/after panel
REPAIR_NOTES.update({
    ("aim", 1): ("E2 (and E8)", "the Reich arm raised a glowing chrome projector: repainted as the "
                                 "rocket launcher, dark muzzle"),
    ("aim", 3): ("E4 (and E6)", "a third arm (the Legion's, raised and also hanging): the hanging one removed"),
    ("aim", 4): ("E5", "from the back, the raised arm also hung: removed"),
    ("aim", 5): ("F1", "the muzzle-on launcher was raised by the Legion arm and another hung from the Reich one: body "
                       "mirrored, the launcher stays (olive) on the Reich arm; the Legion arm hangs with "
                       "its projector (from rooted)"),
    ("aim", 7): ("F3 (and F7)", "a projector pointing backwards (removed), the pink fist on the launcher (grey-"
                                "green), the launcher hanging (removed); the hip it covered, with the cable knot itself"),
    ("aim", 8): ("F4 (and F6)", "the Legion arm raised backwards: hanging (from E4); the repeated "
                                "launcher hanging: removed"),
    ("aim", 9): ("F5", "the same from the back"),
    ("walk", 0): ("A1", "the cable skirt instead of the Reich leg: legs from C1"),
    ("walk", 3): ("A4 (and A6)", "the cable skirt instead of a leg: legs from C4"),
    ("walk", 4): ("A5", "the cable skirt instead of a leg: legs from C5"),
    ("fire_v2", 0): ("G1", "orb in the Reich fist and rocket in the Legion hand: body mirrored, arms in their "
                           "place, skin repainted; legs -> cable knot and smoke"),
    ("fire_v2", 1): ("G2 (and G8)", "the orb came out of the launcher's muzzle and the rocket from the Legion: orange "
                                    "flash / blue discharge on chrome; legs -> knot"),
    ("fire_v2", 2): ("G3 (and G7)", "the launcher crossed the neighbouring figure (parted by hand); legs -> knot"),
    ("fire_v2", 3): ("G4 (and G6)", "orb from the Reich arm (flash) and a rocket fired backwards (removed); "
                                    "legs -> knot"),
    ("fire_v2", 4): ("G5", "legs -> cable knot and smoke"),
    ("fire", 0): ("H1", "the discarded sheet: rocket and flash removed"),
    ("fire", 1): ("H2 (and H8)", "rocket and flash removed"),
    ("fire", 2): ("H3 (and H7)", "rocket removed"),
    ("fire", 3): ("H4 (and H6)", "rocket removed"),
    ("fire", 4): ("H5", "flash removed"),
})
PANEL_ZOOM = 2


def sprite_picture(v: View, k: float, base: float, pal: np.ndarray, sq=None) -> np.ndarray:
    """A view at the lumps' size (rooted scale k, the build's base scale), RGBA."""
    rgb, m = scaled(v, k, sq)
    idx = ge.outline(ge.downscale(rgb, m, base * ge.PIXEL_ASPECT, base, pal), pal)
    return ge.to_rgba(idx, pal)


def repair_panel(base: float, ref_dir: Path = ge.REF_DIR) -> Image.Image:
    """Before (Gemini's view, only mirrored) and after (repaired) at the lumps' size, x PANEL_ZOOM,
    one pair per repaired view, and the far side's pair (a mirror vs the swapped halves)."""
    pal = ge.palette_rgb()
    cuts = {k: cut(k, ref_dir) for k in SOURCES}
    scales = sheet_scales(cuts)
    pairs = []
    for (key, view), (lump, note) in REPAIR_NOTES.items():
        k, squash = scales[key]
        raw = cuts[key][view]
        before = sprite_picture(canonical(raw), k, base, pal)
        after = sprite_picture(canonical_fixed(key, view, repaired(key, view, cuts), cuts), k, base, pal)
        pairs.append((lump, note, before, after))
    key, first = LETTERS["Q"]
    prof = repaired(key, first + PROFILE, cuts)
    mirror = canonical(prof)
    mirror = View(mirror.rgb[:, ::-1].copy(), mirror.mask[:, ::-1].copy())
    pairs.append(("Q7 (and all of 6-8)", "the other side: a mirror would put the armband on the Legion arm; "
                  "the two halves' materials are swapped instead",
                  sprite_picture(mirror, 1.0, base, pal), sprite_picture(swap_halves(prof, HELMET_ROWS), 1.0, base, pal)))
    z = PANEL_ZOOM
    try:
        font = ImageFont.truetype(artlib.FONT_SMALL, 13)
    except OSError:  # pragma: no cover - no system font
        font = ImageFont.load_default()
    cell_w = max(b.shape[1] + a.shape[1] for _, _, b, a in pairs) * z + 30
    cell_h = max(max(b.shape[0], a.shape[0]) for _, _, b, a in pairs) * z + 64
    cols = 4
    rows = (len(pairs) + cols - 1) // cols
    img = Image.new("RGB", (cols * cell_w, rows * cell_h), (59, 61, 66))
    dr = ImageDraw.Draw(img)
    for i, (lump, note, before, after) in enumerate(pairs):
        cx, cy = (i % cols) * cell_w, (i // cols) * cell_h
        x = cx + 8
        for pic, tag in ((before, "Gemini"), (after, "fixed")):
            im = Image.fromarray(pic, "RGBA")
            im = im.resize((im.width * z, im.height * z), Image.NEAREST)
            y = cy + cell_h - 58 - im.height
            img.paste(im, (x, y), im)
            dr.text((x, cy + cell_h - 56), tag, fill=(214, 208, 196), font=font)
            x += im.width + 12
        dr.text((cx + 8, cy + 4), lump, fill=(240, 236, 228), font=font)
        words, line, ly = note.split(), "", cy + cell_h - 40
        for w in words:
            if len(line) + len(w) > cell_w // 7:
                dr.text((cx + 8, ly), line, fill=(200, 196, 186), font=font)
                ly += 14
                line = ""
            line += w + " "
        if line and ly < cy + cell_h - 4:
            dr.text((cx + 8, ly), line, fill=(200, 196, 186), font=font)
    return img


def provisional_frames(spec, sprites_dir: Path = ge.SPRITES_DIR) -> dict:
    """What the actor wears today (SDPS, tinted, x1.75) under the new letters, for the 'current' strips:
    rooted Q/R and B/D show its A/B; E-H its E-H; S its H; death I-O its I-O; A/C its A/C."""
    import colossus_gemini as cgz
    src = {}
    for p in sorted((sprites_dir / PROV_FOLDER).glob(f"{PROV_SPRITE}*.png")):
        with Image.open(p) as im:
            rgba, g = cgz.scaled(cgz.tint_provisional(np.asarray(im.convert("RGBA")), PROV_RAMP),
                                 ge.read_grab(p) or (0, 0), PROV_SCALE)
        img = Image.fromarray(rgba, "RGBA")
        src[p.stem.upper()[len(PROV_SPRITE):]] = {"src": ge._b64(img), "w": img.width, "h": img.height,
                                                   "left": g[0], "top": g[1]}
    letter_map = {"Q": "A", "R": "B", "S": "H"}
    out = {}
    for rest, f in src.items():
        out[spec.sprite + rest] = f
    for new, old in letter_map.items():
        for rest, f in src.items():
            if rest.startswith(old):
                out[spec.sprite + new + rest[1:].replace(old, new)] = f
    return out


def lineup(new_dir: Path, sprites_dir: Path = ge.SPRITES_DIR, z: int = LINEUP_ZOOM) -> Image.Image:
    """The scale check on one floor line: provisional, new, the Colossus, the General, the Schwer, the attacks."""
    import colossus_gemini as cgz
    pics = []
    for label_txt, lump, kind in LINEUP:
        folder = PROV_FOLDER if kind == "prov" else kind
        p = new_dir / f"{lump}.png" if kind == "new" else sprites_dir / folder / f"{lump}.png"
        with Image.open(p) as im:
            rgba = np.asarray(im.convert("RGBA"))
        grab = ge.read_grab(p) or (0, 0)
        if kind == "prov":
            rgba, grab = cgz.scaled(cgz.tint_provisional(rgba, PROV_RAMP), grab, PROV_SCALE)
        rows = np.flatnonzero((rgba[..., 3] > 0).any(axis=1))
        pics.append((f"{label_txt}: {rows[-1] - rows[0] + 1} px", rgba, grab))
    above = max(g[1] for _, _, g in pics)
    below = max(a.shape[0] - g[1] for _, a, g in pics)
    cell = max(max(g[0], a.shape[1] - g[0]) for _, a, g in pics) * 2 * z + 12
    head, foot = 10, 44
    img = Image.new("RGB", (cell * len(pics), head + (above + below) * z + foot), (59, 61, 66))
    dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(artlib.FONT_SMALL, 12)
    except OSError:  # pragma: no cover - no system font
        font = ImageFont.load_default()
    floor = head + above * z
    dr.line([(0, floor), (img.width, floor)], fill=(110, 112, 118))
    for i, (label_txt, rgba, (left, top)) in enumerate(pics):
        big = Image.fromarray(rgba, "RGBA").resize((rgba.shape[1] * z, rgba.shape[0] * z), Image.NEAREST)
        img.paste(big, (i * cell + cell // 2 - left * z, floor - top * z), big)
        y = floor + below * z + 6
        for part in label_txt.split(": "):
            dr.text((i * cell + 6, y), part, fill=(230, 226, 218), font=font)
            y += 15
    return img


INTRO = (
    "<p>The <b>Consortium</b> (<code>SD_Consortium</code>, Episode 3's final boss, sprite <code>SDCN</code>, "
    "95 lumps: design <code>docs/engine/2026-10-22_P4_ep3-final-boss.md</code> §5), taken from Gemini's 8 sheets "
    "(<code>rooted</code>, <code>turn</code>, <code>walk</code>, <code>aim</code>, the discarded <code>fire</code>, "
    "<code>fire_v2</code>, <code>breach</code>, <code>death</code>). <b>Current</b> = what it wears today: the Panzermensch "
    "Schwer <code>SDPS</code> ×1.75 tinted cobalt (D116; the tint here is an imitation, NOT VERIFIED). "
    "<b>New</b> = SDCN at final-boss scale: 140 px tall (2× the Panzermensch; the Colossus is 128), no "
    "<code>Scale</code> and no tint. Everything ×3 without smoothing on its floor line with the real offsets.</p>"
    "<p><b>The sides</b> (doc §2): the Reich half on <b>its left</b>: from the front, on the viewer's <b>right</b> "
    "(the rockets leave 32 units to its left and the orbs to its right, as in the actor). Gemini "
    "drew every sheet the wrong way round: they are mirrored. <b>Rotations 6-8</b> (its right side, the Legion's) "
    "were not drawn by Gemini: they are the 3/4, the profile and the 3/4 back not mirrored, with the two halves' materials "
    "swapped in code (the armband never changes arm). <b>The arms</b>: what I fixed by hand, without "
    "Gemini, is in the «Gemini / fixed» panel and in each frame's list; the hip of F's profile, which "
    "Gemini never drew (the launcher covered it), is filled with the cable knot itself (I tried local Fooocus on the sheet itself, D127: it painted green legs and skulls, discarded). "
    "Armband: <code>armband_symbol.py</code>'s symbol (option 1, D108/D114). Nothing installed: lumps in "
    "<code>work/art/enemies_gemini/consortium/</code> with <code>install.sh</code> and the actor patch (removes the provisional tint "
    "and scale; rooted Q R, breach S). Mark OK / NO / ? per row and press <b>Copy result</b>.</p>")


def consortium_sheet(spec, out: Path = SHEET_HTML, out_root: Path = ge.OUT_ROOT,
                     sprites_dir: Path = ge.SPRITES_DIR, ref_dir: Path = ge.REF_DIR) -> Path:
    new_dir = out_root / spec.name
    metrics = json.loads((new_dir / "metrics.json").read_text(encoding="utf-8"))
    item = {
        "id": spec.name, "sprite": spec.sprite, "letters": sorted(spec.rotated),
        "anims": [{"label": a[0], "seq": [list(s) for s in a[1]]} for a in spec.anims],
        "cur": provisional_frames(spec, sprites_dir), "new": ge._frames_json(new_dir, spec.sprite),
        "derived": list(spec.derived), "notes": spec.notes,
        "gate": metrics.get("gate", []) + [f"no Fooocus fill yet: {n}" for n in sorted(set(GEN_MISSING))],
        "reask": metrics.get("reask", []), "symbol": ge.symbol_summary(metrics),
        "sheets": {k: [f["facing"] for f in v["figures"]] for k, v in metrics["sheets"].items()},
    }
    panel = repair_panel(metrics["base_scale"], ref_dir)
    intro = INTRO + (
        f'<h3>Scale: provisional, new, the Colossus, the General and the Schwer (×{LINEUP_ZOOM})</h3><p><img alt="Scale '
        f'line-up" style="max-width:100%;image-rendering:pixelated" src="{ge._b64(lineup(new_dir, sprites_dir))}"></p>'
        f'<h3>Fixed by hand, without Gemini (×{PANEL_ZOOM}; «Gemini» = its view only mirrored)</h3><p><img alt="Before and '
        f'after" style="max-width:100%;image-rendering:pixelated" src="{ge._b64(panel)}"></p>')
    html = ge.SHEET_TEMPLATE
    for old, new in (
            ("<title>Gemini Enemies</title>", "<title>Gemini Consortium</title>"),
            ("Soviet Doom · Enemies redrawn with Gemini (draft)",
             "Soviet Doom · The Consortium, final boss, with Gemini (draft)"),
            ('const KEY = "sd-2026-10-22_P4_enemies-gemini";', 'const KEY = "sd-2026-10-24_P4_consortium-gemini";'),
            ("Gemini enemies (2026-10-22_P4, D104/D105)", "Gemini Consortium (2026-10-24_P4, D112/D127)")):
        if html.count(old) != 1:
            raise ValueError(f"consortium_sheet: the review template changed ({old!r})")
        html = html.replace(old, new)
    i0 = html.index("<p>Each enemy")
    i1 = html.index("</p>", i0) + len("</p>")
    html = html[:i0] + intro + html[i1:]
    html = html.replace("/*ITEMS*/[]", json.dumps([item]))
    ge.guard_out(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


# ------------------------------------------------------------- the install
PROVISIONAL_HEADER_START = "// PROVISIONAL LOOK (D116):"
PROVISIONAL_HEADER_END = "// show S instead of H (MOD-SPEC 6.12; tests/test_ep3_boss.py pins it).\n"
INSTALLED_HEADER = (
    "// LOOK: SDCN, its own 95 lumps drawn from the CEO's Gemini sheets by\n"
    "// tools/art/consortium_gemini.py (gemini_enemy.py's CONSORTIUM), in\n"
    "// assets/sprites/consortium/ (design doc section 5), at full size: no\n"
    "// Scale, no tint. Eight rotations of its own (the halves are not mirror\n"
    "// images). Rooted it shows Q R (Spawn, See), free A-D (Walk); E the\n"
    "// Legion arm's tell, F the Reich arm's, G firing, H pain, S the Breach's\n"
    "// first frames, I-O death.\n")
TEXT_FIXES = (
    ("// section 12 (row 11). In the mod since D116 (2026-10-22), on a provisional\n"
     "// sprite; placed in no map yet (MAP09's boss swap is level-designer's).",
     "// section 12 (row 11). In the mod since D116 (2026-10-22), on its own\n"
     "// sprite (SDCN) since the CEO's OK; placed in no map yet (MAP09's boss\n"
     "// swap is level-designer's)."),
)
STATE_EDITS = (   # (line after the rename, the line it becomes): design doc 7 step 2
    ("\t\tSDCN AB 10 A_Look;", "\t\tSDCN QR 10 A_Look;"),
    ("\t\tSDCN A 0 A_JumpIf(unbound, \"Walk\");", "\t\tSDCN Q 0 A_JumpIf(unbound, \"Walk\");"),
    ("\t\tSDCN A 6 A_SD_ConsortiumChase;", "\t\tSDCN Q 6 A_SD_ConsortiumChase;"),
    ("\t\tSDCN B 6 A_SD_ConsortiumChase;", "\t\tSDCN R 6 A_SD_ConsortiumChase;"),
    ("\t\tSDCN H 10 A_SD_ConsortiumBreach;        // invulnerable; the ground shakes; the line",
     "\t\tSDCN S 10 A_SD_ConsortiumBreach;        // invulnerable; the ground shakes; the line"),
    ("\t\tSDCN H 10;\n\t\tSDCN E 20 Bright A_SD_ConsortiumWave;", "\t\tSDCN S 10;\n\t\tSDCN E 20 Bright A_SD_ConsortiumWave;"),
)


def installed_actor(text: str, old: str = "SDPS", new: str = "SDCN") -> str:
    """consortium.zs once SDCN is installed: the header's documented swap (the
    sprite renamed at the start of each state line, every PROVISIONAL-D116
    code line deleted with the comment lines right above it), the two state
    edits the drawing adds (rooted Q R; the Breach's first frames S), the
    provisional paragraph replaced by what it wears."""
    i0 = text.index(PROVISIONAL_HEADER_START)
    i1 = text.index(PROVISIONAL_HEADER_END, i0) + len(PROVISIONAL_HEADER_END)
    text = text[:i0] + INSTALLED_HEADER + text[i1:]
    for a, b in TEXT_FIXES:
        if text.count(a) != 1:
            raise ValueError(f"installed_actor: consortium.zs changed ({a[:40]!r}...)")
        text = text.replace(a, b)
    out: list[str] = []
    for line in text.splitlines():
        st = line.strip()
        if "PROVISIONAL-D116" in line and st and not st.startswith("/"):
            while out and out[-1].strip().startswith("//") and out[-1].startswith("\t"):
                out.pop()
            continue
        out.append(re.sub(rf"^(\s*){old} ", rf"\g<1>{new} ", line))
    text = "\n".join(out) + "\n"
    for a, b in STATE_EDITS:
        if text.count(a) != 1:
            raise ValueError(f"installed_actor: consortium.zs changed ({a.strip()[:40]!r}...)")
        text = text.replace(a, b)
    return text


def install_patch(spec, actor: Path = ACTOR, out_root: Path = ge.OUT_ROOT) -> list[Path]:
    """In work/art/enemies_gemini/consortium/: consortium.zs.patch (git apply)
    and install.sh (copies the lumps, applies it). Writes nothing outside work/."""
    d = out_root / spec.name
    ge.guard_out(d)
    have = sorted(p.stem.upper() for p in d.glob(f"{spec.sprite}*.png"))
    if have != ge.lump_names(spec):
        raise SystemExit(f"consortium_gemini: build {spec.name} first (its lumps differ from the spec)")
    text = actor.read_text(encoding="utf-8")
    rel = actor.relative_to(ROOT).as_posix()
    diff = difflib.unified_diff(text.splitlines(keepends=True), installed_actor(text).splitlines(keepends=True),
                                f"a/{rel}", f"b/{rel}")
    patch = d / "consortium.zs.patch"
    patch.write_text("".join(diff), encoding="utf-8", newline="\n")
    sh = d / "install.sh"
    sh.write_text(
        "#!/usr/bin/env bash\n"
        "# Install the Consortium's SDCN set ONLY after the CEO's OK on\n"
        f"# {SHEET_HTML.relative_to(ROOT).as_posix()}. Run from the repo root.\n"
        "# Also at install, by hand (mod-engineer / PM): the licence rows in\n"
        "# docs/art/LICENSES.md (as the colossus's: sources gem_consortium_*.png,\n"
        "# processed by tools/art/consortium_gemini.py; the F profile's hip a local\n"
        "# Fooocus inpaint over the Gemini sheet, D127); tests/test_ep3_boss.py's\n"
        "# test_provisional_look_and_its_documented_swap flips (it is red once\n"
        "# SDCN exists, by design: pin SDCN, Q R and S instead); MOD-SPEC 6.3/6.12\n"
        "# and the design doc's 'Provisional sprite' row; a test_consortium_sprites\n"
        "# pin as for every installed enemy (design doc 7 step 7).\n"
        "set -euo pipefail\n"
        f"mkdir -p assets/sprites/{spec.folder}\n"
        f"cp work/art/enemies_gemini/{spec.name}/{spec.sprite}*.png assets/sprites/{spec.folder}/\n"
        f"git apply work/art/enemies_gemini/{spec.name}/consortium.zs.patch\n"
        f"echo \"installed {len(have)} lumps in assets/sprites/{spec.folder}/ and patched {rel}\"\n",
        encoding="utf-8", newline="\n")
    return [patch, sh]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", choices=("fix", "build", "sheet", "all", "gen-jobs", "gen-pick"))
    ap.add_argument("args", nargs="*", help="gen-pick: NAME SEED")
    a = ap.parse_args(argv)
    spec = ge.PENDING["consortium"]
    if a.what == "gen-jobs":
        print(f"consortium_gemini: wrote {gen_jobs()} (run it with Fooocus' python: see GEN)")
        return 0
    if a.what == "gen-pick":
        name, seed = a.args
        print(f"consortium_gemini: wrote {gen_pick(name, int(seed))}")
        return 0
    if a.what in ("fix", "build", "all"):
        for name, p in fix_sheets().items():
            print(f"consortium_gemini: wrote {p.relative_to(ROOT).as_posix()}")
        if GEN_MISSING:
            print(f"consortium_gemini: no Fooocus fill cached yet for {sorted(set(GEN_MISSING))} (hole left)")
    if a.what in ("build", "all"):
        m = ge.build(spec)
        print(f"consortium_gemini: {m['lumps']} lumps -> work/art/enemies_gemini/{spec.name}/ "
              f"(base scale {m['base_scale']}), {len(m['gate'])} gate notes")
    if a.what in ("sheet", "all"):
        print(f"consortium_gemini: wrote {consortium_sheet(spec).relative_to(ROOT).as_posix()}")
        for f in install_patch(spec):
            print(f"consortium_gemini: wrote {f.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
