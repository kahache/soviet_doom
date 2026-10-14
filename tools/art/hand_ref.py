"""The ice axe's held frame derived from the CEO's reference photos (N14 / N4
round 3): a sweep for review, no asset. Round 3b (after the CEO's "cámbialo
a diestro" and the PM's polish notes): reference 1 mirrored to a right hand,
the haft toned as wood, the head given weight.

    python tools/art/hand_ref.py            # cells -> work/art/hand_ref/, sheet + HTML -> docs/art/previews/
    python tools/art/hand_ref.py silhouettes   # D75: 3x3 axe sizes on C3's hand, flat silhouettes
    python tools/art/hand_ref.py silhouette-final   # D76: the pick, its shaft as wide as L1.0's
    python tools/art/hand_ref.py ppsh       # D77: PPSh-41 silhouettes from the CEO's Gemini render

Why: drawn hands failed the CEO again and again ("dedos como salchichas",
"el antebrazo un palo larguísimo"); what worked for likeness was deriving
from a source image (the Lenin and Stalin posters). The CEO made reference
images with Fooocus (SDXL) in work/art/reference/ ("orientativas"). Here
the hand, wrist and sleeve are taken from one of them, not redrawn:

0. orient: the files are named "mirrored" because Fooocus drew them
   flipped; a spec with mirror=True flips the photo left-right first
   (oriented() moves its measured points), so the right arm comes in from
   the bottom right like Doom's fist, chainsaw and our TT-33 hands;
1. segment: a rough lasso around hand and sleeve (photo px), then the
   photo's own colours decide the edge (sky and snow out; skin warm;
   sleeve dark olive); the photo's shaft is cut out along its axis
   (everywhere outside the fist; inside it only its saturated wood, so the
   fingertips and the thumb that lie over it stay);
2. turn and scale: a camera roll about the grip (so the sleeve leaves the
   view through the bottom, behind the status bar, not cut mid-screen) and
   a scale that makes the knuckle span (palm breadth) a set fraction of
   the TT-33 hands' (work/art/weapons_fd/tt33/SDTTA0.png, approved D61);
   area-averaged, so no pixel is invented;
3. tone: each pixel's luminance rank is matched to the TT-33 hands'
   skin (or sleeve) luminances, then posterized to N tones picked from the
   same ramps (palette v2 flesh_pink 1-15, military_green 1-12), so the
   hand sits next to the TT-33's; outline and the skin/sleeve seam in the
   ramps' darkest tone;
4. the axe: our own (the D40 head after gen_weapon.draw_ice_axe_head, its
   pick deepened and adze widened so it reads at 1x; the haft re-toned as
   round grained wood with a dark rim) rendered along the photo's shaft
   axis, the head up the axis and farther (smaller), the shaft continuing
   below the fist; then the hand on top, so thumb and fingertips lie over
   the shaft and the shaft shows above and below the fist through the hole
   the photo's shaft left, darker inside the fist.

The whole frame is placed so its top stands where the TT-33's does (D57,
56 px above the status bar), the grip at a chosen column. Read-only
imports: hand_study (screen model, WAD, backdrop), gen_weapon (the axe).
Licence: the references are the CEO's own Fooocus/SDXL generations.
"""

from __future__ import annotations

import base64
import functools
import html
import io
import json
import math
import sys
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import artlib  # noqa: E402
import hand_study as hs  # noqa: E402

ROOT = artlib.PROJECT_ROOT
REF_DIR = ROOT / "work" / "art" / "reference"
OUT_DIR = ROOT / "work" / "art" / "hand_ref"
PREVIEW_DIR = ROOT / "docs" / "art" / "previews"
TT33_A = hs.TT_OUT_DIR / "SDTTA0.png"         # the approved TT-33 ready frame (D61)

WEAPONTOP = hs.WEAPONTOP
BAR_LIFT = hs.BAR_LIFT
SCREEN_W, SCREEN_H = hs.SCREEN_W, hs.SCREEN_H
SKIN = hs.R3_SKIN                             # flesh_pink 1-15, the TT-33 hands' skin
SLEEVE = hs.R3_SLEEVE                         # military_green 1-12, their sleeve

# ------------------------------------------------------------- segmentation
SKY_BLUE = 0.03            # b - r above this: sky or blue shadow on snow
SNOW_V, SNOW_S = 0.70, 0.12    # bright and grey: snow (R1's lit sleeve is v 0.55, s 0.17)
SKIN_S, SKIN_H = 0.18, 40.0    # warm enough and red-to-orange
DARK_V, DARK_S = 0.66, 0.50    # sleeve candidates: not bright, not saturated
WOOD_S, WOOD_H = (0.47, (18.0, 42.0))   # the photo's wooden shaft inside the fist
CLEAN_R = 3                # photo px: open/close radius of the masks
PAD = 500                  # photo px of empty border before the turn
COVER = 0.5                # a sprite pixel is opaque when this much of it is hand
SLEEVE_SOFT = 2            # sprite px: box blur of the sleeve's luminance before its tones
CREASE_BLUR = 0.7          # sprite px: the neighbourhood a crease is measured against
CREASE_SHARE = 0.08        # at most this share of the skin pixels becomes crease lines
CREASE_MIN = 0.02          # ... and only where the photo is this much darker than around it


@dataclass(frozen=True)
class RefSpec:
    """One reference photo, with the few numbers measured on it (photo px)."""
    key: str
    file: str
    title: str
    lasso: tuple               # polygon around hand + sleeve (rough: the colours make the edge)
    axis: tuple                # two points on the photo's shaft axis, the upper first
    shaft_half: float          # the photo shaft's half width
    fist: tuple                # (top, bottom) rows where thumb and fingers lie over the shaft
    palm: tuple                # two points: index knuckle-row top to little finger bottom (palm breadth)
    seed: tuple                # a point inside the hand
    turn: float                # degrees counter-clockwise on screen, about the grip
    sleeve_from: tuple | None = None   # bare forearm: (point, direction) of a cuff line; right of it is sleeve
    wood_s: float = WOOD_S     # saturation above which a pixel in the fist's band is the photo's wood
                               # (0: the whole band is shaft, nothing lies over it)
    sleeve_seed: tuple | None = None   # a point inside the sleeve: only that part of it is sleeve
    mirror: bool = False       # flip the photo left-right before the cut-out (numbers above stay in
                               # the file's own pixels; oriented() moves them)
    flipped: bool = False      # set by oriented(): the numbers are already in the flipped photo's pixels
    note: str = ""


PHOTO_W = 1152                 # every reference is 1152x896 (Fooocus); checked when a photo is loaded


def oriented(spec: RefSpec) -> RefSpec:
    """The spec in the pixels of the photo as it is used: mirrored specs get
    every x moved to PHOTO_W - 1 - x (and the cuff direction turned)."""
    if not spec.mirror or spec.flipped:
        return spec
    fx = lambda p: (PHOTO_W - 1 - float(p[0]), float(p[1]))     # noqa: E731
    cuff = None
    if spec.sleeve_from is not None:
        (px, py), (dx, dy) = spec.sleeve_from
        cuff = (fx((px, py)), (dx, -dy))                         # a mirror keeps the "right of it" side
    return replace(
        spec, lasso=tuple(fx(p) for p in spec.lasso), axis=tuple(fx(p) for p in spec.axis),
        palm=tuple(fx(p) for p in spec.palm), seed=fx(spec.seed),
        sleeve_seed=None if spec.sleeve_seed is None else fx(spec.sleeve_seed),
        sleeve_from=cuff, flipped=True)


R1_TURN = -24.0                # clockwise: the mirrored forearm leaves through the bottom right

REFS = {
    "R1": RefSpec(
        "R1", "hand grabbing mirrored.png", "right hand round the haft, thumb over the fingers (CEO's best)",
        lasso=((0, 402), (135, 370), (300, 335), (395, 302), (520, 185), (735, 185), (770, 260), (768, 520), (720, 560),
               (600, 560), (520, 640), (420, 790), (360, 896), (0, 896)),
        axis=((641.0, 180.0), (703.0, 500.0)), shaft_half=40.0, fist=(205.0, 470.0),
        palm=((700.0, 222.0), (745.0, 455.0)), seed=(500.0, 400.0), turn=R1_TURN, sleeve_seed=(100.0, 600.0),
        mirror=True,
        note="first person, a hand round a wooden haft, knuckles and thumb over the fingers, olive sleeve. "
             "Fooocus drew it flipped (a left arm from the left): it is mirrored back, so the right arm comes "
             "in from the bottom right as Doom's fist, chainsaw and our TT-33 hands do (CEO: 'cámbialo a "
             "diestro'). Numbers below are in the file's own pixels."),
    "R2": RefSpec(
        "R2", "both hands grabbing something.png", "fist from behind, forearm from the bottom",
        lasso=((700, 330), (830, 290), (905, 300), (960, 380), (975, 520), (990, 700), (870, 690),
               (825, 715), (775, 850), (770, 896), (430, 896), (560, 700), (700, 560)),
        axis=((905.0, 320.0), (965.0, 690.0)), shaft_half=38.0, fist=(360.0, 600.0),
        palm=((935.0, 385.0), (900.0, 640.0)), seed=(800.0, 520.0), turn=0.0,
        sleeve_from=((560.0, 800.0), (0.85, -0.53)),
        note="the right fist from behind round a haft, the bare forearm coming up from the bottom "
             "(recoloured to sleeve below a cuff line)"),
    "R3": RefSpec(
        "R3", "hand grabbing mirrored 3.png", "hand from below, thumb up the handle",
        lasso=((0, 896), (0, 790), (150, 750), (330, 745), (420, 600), (560, 520), (600, 470), (660, 470),
               (700, 600), (700, 860), (640, 896)),
        axis=((632.0, 450.0), (585.0, 810.0)), shaft_half=26.0, fist=(480.0, 850.0),
        palm=((650.0, 570.0), (640.0, 840.0)), seed=(470.0, 700.0), turn=0.0, wood_s=0.0,
        sleeve_seed=(100.0, 860.0),
        note="the hand seen from below gripping a handle, the thumb up along it, sleeve at the "
             "bottom left"),
}


def hsv(rgb: np.ndarray):
    """Hue (degrees), saturation, value of float RGB in 0..1."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = np.maximum(mx - mn, 1e-6)
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    return h, s, mx


def polygon_mask(shape, pts) -> np.ndarray:
    img = Image.new("L", (shape[1], shape[0]), 0)
    ImageDraw.Draw(img).polygon([tuple(map(float, p)) for p in pts], fill=255)
    return np.asarray(img) > 0


def morph(mask: np.ndarray, r: int, op: str) -> np.ndarray:
    """Binary open ("open") or close ("close") with a (2r+1) square."""
    img = Image.fromarray((mask * 255).astype(np.uint8))
    size = 2 * r + 1
    a, b = (ImageFilter.MinFilter(size), ImageFilter.MaxFilter(size))
    if op == "close":
        a, b = b, a
    return np.asarray(img.filter(a).filter(b)) > 127


def component(mask: np.ndarray, seed) -> np.ndarray:
    """The 4-connected part of mask that holds seed (x, y)."""
    img = Image.fromarray(np.where(mask, 255, 0).astype(np.uint8)).copy()   # fromarray may share read-only memory
    x, y = int(seed[0]), int(seed[1])
    if not mask[y, x]:
        raise ValueError(f"seed {seed} is not inside the hand mask")
    ImageDraw.floodfill(img, (x, y), 128)
    return np.asarray(img) == 128


def axis_frame(spec: RefSpec):
    """Unit vector down the photo's shaft axis and a function giving, for
    photo coordinates, (along, across) from the upper axis point."""
    (x0, y0), (x1, y1) = spec.axis
    u = np.array([x1 - x0, y1 - y0], float)
    u /= np.linalg.norm(u)

    def coords(X, Y):
        dx, dy = X - x0, Y - y0
        return dx * u[0] + dy * u[1], -dx * u[1] + dy * u[0]
    return u, coords


def segment(spec: RefSpec, photo: np.ndarray | None = None) -> dict:
    """Masks on the photo: hand (skin + sleeve, the photo's shaft cut out),
    sleeve, and the photo's shaft hole. photo: float RGB 0..1."""
    spec = oriented(spec)
    if photo is None:
        photo = load_photo(spec)
    h, w = photo.shape[:2]
    hue, sat, val = hsv(photo)
    r, g, b = photo[..., 0], photo[..., 1], photo[..., 2]
    blue = b > r + SKY_BLUE
    snow = (val > SNOW_V) & (sat < SNOW_S)
    skin = (r > g) & (g >= b - 0.02) & (sat > SKIN_S) & ((hue < SKIN_H) | (hue > 340)) & (val > 0.08)
    dark = (val < DARK_V) & (sat < DARK_S) & ~blue & ~skin
    lasso = polygon_mask((h, w), spec.lasso)
    Y, X = np.mgrid[0:h, 0:w].astype(float)
    _, coords = axis_frame(spec)
    along, across = coords(X, Y)
    band = np.abs(across) <= spec.shaft_half
    (ax0, ay0), _ = spec.axis
    u, _ = axis_frame(spec)
    # rows of the fist as positions along the axis
    t_top = (spec.fist[0] - ay0) / u[1]
    t_bot = (spec.fist[1] - ay0) / u[1]
    in_fist = (along >= t_top) & (along <= t_bot)
    wood = band & in_fist & (sat > spec.wood_s) & (hue > WOOD_H[0]) & (hue < WOOD_H[1])
    wood = morph(morph(wood, CLEAN_R, "close"), CLEAN_R, "open")
    hole = band & (~in_fist | wood) if spec.wood_s > 0 else band
    hand = lasso & ~blue & ~snow & (skin | dark) & ~hole
    hand = morph(morph(hand, CLEAN_R, "open"), CLEAN_R, "close") & ~hole & lasso
    hand = component(hand, spec.seed)
    sleeve = hand & ~skin
    sleeve = morph(morph(sleeve, CLEAN_R + 2, "open"), CLEAN_R + 2, "close") & hand
    if spec.sleeve_seed is not None:
        sleeve = component(sleeve, spec.sleeve_seed)
    if spec.sleeve_from is not None:
        (px, py), (dx, dy) = spec.sleeve_from
        sleeve |= hand & ((X - px) * dy - (Y - py) * dx < 0)
    return {"hand": hand, "sleeve": sleeve, "hole": hole & lasso, "fist_hole": hole & lasso & in_fist,
            "photo": photo}


def load_photo(spec: RefSpec) -> np.ndarray:
    """The reference as float RGB 0..1, mirrored left-right when the spec says so."""
    with Image.open(REF_DIR / spec.file) as im:
        if spec.mirror and im.width != PHOTO_W:
            raise ValueError(f"{spec.file} is {im.width} px wide; mirrored specs assume {PHOTO_W}")
        a = np.asarray(im.convert("RGB"), np.float32) / 255.0
    return a[:, ::-1].copy() if spec.mirror else a


# ------------------------------------------------------------- transform
def luminance(rgb: np.ndarray) -> np.ndarray:
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def grip_point(spec: RefSpec) -> np.ndarray:
    """Where the shaft is held: on the axis, at the middle of the fist rows."""
    (x0, y0), _ = spec.axis
    u, _ = axis_frame(spec)
    t = ((spec.fist[0] + spec.fist[1]) / 2 - y0) / u[1]
    return np.array([x0, y0]) + u * t


def palm_len(spec: RefSpec) -> float:
    (x0, y0), (x1, y1) = spec.palm
    return float(math.hypot(x1 - x0, y1 - y0))


def to_sprite(seg: dict, spec: RefSpec, scale: float) -> dict:
    """Turn the photo layers about the grip and area-average them down by
    `scale`. Returns float layers at sprite size and the grip in sprite px,
    plus the screen direction of the shaft (unit, pointing up the axis)."""
    photo = seg["photo"]
    lum = luminance(photo)
    h, w = lum.shape
    border = np.zeros((h, w), bool)
    border[:3], border[-3:], border[:, :3], border[:, -3:] = True, True, True, True
    # creases: how much darker than its neighbourhood a pixel is (finger
    # separations, knuckle folds), measured on the photo before it shrinks
    blur_r = max(1.0, CREASE_BLUR / scale)
    soft = np.asarray(Image.fromarray(np.clip(lum * 255, 0, 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(blur_r)), np.float32) / 255.0
    crease = np.clip(soft - lum, 0.0, None)
    layers = {
        "crease": (crease * seg["hand"]).astype(np.float32),
        "hand": seg["hand"].astype(np.float32),
        "sleeve": (seg["sleeve"] & seg["hand"]).astype(np.float32),
        "lum": (lum * seg["hand"]).astype(np.float32),
        "border": (border & seg["hand"]).astype(np.float32),
        "hole": seg["hole"].astype(np.float32),
        "fist_hole": seg["fist_hole"].astype(np.float32),
    }
    gx, gy = grip_point(spec) + PAD
    out = {}
    for name, a in layers.items():
        big = np.zeros((h + 2 * PAD, w + 2 * PAD), np.float32)
        big[PAD:PAD + h, PAD:PAD + w] = a
        img = Image.fromarray(big, "F").rotate(spec.turn, resample=Image.Resampling.BILINEAR,
                                                center=(gx, gy))
        nw, nh = max(1, round(img.width * scale)), max(1, round(img.height * scale))
        out[name] = np.asarray(img.resize((nw, nh), Image.Resampling.BOX), np.float32)
    # the grip and the shaft direction after the turn (PIL turns counter-clockwise on screen)
    th = math.radians(spec.turn)
    (ax0, ay0), (ax1, ay1) = spec.axis
    d = np.array([ax0 - ax1, ay0 - ay1], float)          # up the axis
    d /= np.linalg.norm(d)
    rd = np.array([d[0] * math.cos(th) + d[1] * math.sin(th), -d[0] * math.sin(th) + d[1] * math.cos(th)])
    grip = np.array([gx * nw / big.shape[1], gy * nh / big.shape[0]])
    return {"layers": out, "grip": grip, "up": rd}


# ------------------------------------------------------------------- tone
def ref_lums() -> dict[str, np.ndarray]:
    """Luminances of the TT-33 hands' skin and sleeve pixels (SDTTA0)."""
    spr, _ = hs.read_png_sprite(TT33_A)
    a = spr[..., 3] > 0
    rgb = spr[..., :3]
    out = {}
    for name, spec in (("skin", SKIN), ("sleeve", SLEEVE)):
        cols = np.array(hs.ramp_cols(spec), np.uint8)
        m = a & (rgb[..., None, :] == cols[None, None]).all(-1).any(-1)
        out[name] = np.sort(luminance(rgb[m].astype(np.float32)))
    return out


def tone_set(spec, ref: np.ndarray, n: int) -> np.ndarray:
    """n ramp colours, dark to light, at the middles of n equal slices of
    the reference luminances (duplicates step to the next free colour)."""
    cols = np.array(hs.ramp_cols(spec), np.uint8)
    col_l = luminance(cols.astype(np.float32))
    picks: list[int] = []
    for i in range(n):
        t = float(np.quantile(ref, (i + 0.5) / n))
        order = np.argsort(np.abs(col_l - t))
        idx = next(int(j) for j in order if int(j) not in picks)
        picks.append(idx)
    picks.sort()
    return cols[picks]


def posterize(values: np.ndarray, ref: np.ndarray, tones: np.ndarray) -> np.ndarray:
    """Rank-match values onto the reference luminances, then the nearest of
    the tones by luminance. Returns an index into tones per value."""
    if values.size == 0:
        return np.zeros(0, int)
    order = np.argsort(values, kind="stable")
    pct = np.empty(values.size)
    pct[order] = (np.arange(values.size) + 0.5) / values.size
    target = np.quantile(ref, pct)
    tl = luminance(tones.astype(np.float32))
    return np.argmin(np.abs(target[:, None] - tl[None, :]), axis=1)


def masked_box(a: np.ndarray, mask: np.ndarray, r: int) -> np.ndarray:
    """Mean of `a` over the (2r+1) square around each pixel, counting only
    pixels inside mask (so the sleeve is not darkened by the skin)."""
    if r <= 0:
        return a
    num = np.zeros_like(a, dtype=np.float64)
    den = np.zeros_like(a, dtype=np.float64)
    av = np.where(mask, a, 0.0)
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            num += hs.shift(av, dy, dx, 0.0)
            den += hs.shift(mask.astype(np.float64), dy, dx, 0.0)
    return np.where(den > 0, num / np.maximum(den, 1e-9), a)


def edge(mask: np.ndarray, of: np.ndarray | None = None) -> np.ndarray:
    """Pixels of mask with a 4-neighbour outside it (or inside `of`)."""
    other = ~mask if of is None else of
    p = np.pad(other, 1, constant_values=of is None)
    nb = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return mask & nb


def hand_sprite(fl: dict, n_tones: int, refs: dict) -> dict:
    """The posterized RGBA hand from the float layers."""
    L = fl["layers"]
    cover = L["hand"]
    opaque = cover >= COVER
    with np.errstate(invalid="ignore", divide="ignore"):
        lum = np.where(cover > 0, L["lum"] / np.maximum(cover, 1e-6), 0.0)
        sl = np.where(cover > 0, L["sleeve"] / np.maximum(cover, 1e-6), 0.0)
        cr = np.where(cover > 0, L["crease"] / np.maximum(cover, 1e-6), 0.0)
    sleeve = opaque & (sl >= 0.5)
    skin = opaque & ~sleeve
    rgba = np.zeros(cover.shape + (4,), np.uint8)
    skin_t = tone_set(SKIN, refs["skin"], n_tones)
    sleeve_t = tone_set(SLEEVE, refs["sleeve"], max(3, n_tones - 1))
    rgba[skin, :3] = skin_t[posterize(lum[skin], refs["skin"], skin_t)]
    # the sleeve's folds softened first: at this size a deep fold reads as a stain
    soft = masked_box(lum, sleeve, SLEEVE_SOFT)
    rgba[sleeve, :3] = sleeve_t[posterize(soft[sleeve], refs["sleeve"], sleeve_t)]
    rgba[opaque, 3] = 255
    outline_skin = np.array(hs.ramp_cols(SKIN)[0], np.uint8)
    outline_sleeve = np.array(hs.ramp_cols(SLEEVE)[0], np.uint8)
    rgba[edge(skin, ~skin & ~sleeve) | edge(skin, sleeve), :3] = outline_skin
    rgba[edge(sleeve, ~skin & ~sleeve), :3] = outline_sleeve
    # the photo's creases in the darkest tone: the lines that make fingers read at 1x
    if skin.any():
        thr = max(CREASE_MIN, float(np.quantile(cr[skin], 1.0 - CREASE_SHARE)))
        rgba[skin & (cr >= thr), :3] = skin_t[0]
    border = opaque & (L["border"] > 0.05)
    fist_hole = ~opaque & (L["fist_hole"] > 0.3)
    return {"rgba": rgba, "skin": skin, "sleeve": sleeve, "border": border, "fist_hole": fist_hole,
            "tones": {"skin": skin_t.tolist(), "sleeve": sleeve_t.tolist()}}


# ------------------------------------------------------------------- axe
GRIP_Z = 22.0              # cm: the fist's depth (gen_weapon.AXE_FD_GRIP_Z)
HEAD_Z = 120.0             # cm: the head, five and a half times farther than the fist: small, so the hand leads
HEAD_RISE = 1.15           # head top above the grip, in palm breadths (R1: 245 photo px over a 235 px palm)
HEAD_K = 1.25              # head scale (round 2's frame A had 1.1; the PM found the head wispy)
HEAD_FLAT = 0.35           # the head's axis: depth part over screen part (low: the T seen in profile)
HEAD_ROLL = 10.0           # degrees: the head turned about the shaft (0: the pick in pure profile)
# Weight for the head at 1x (PM, round 3b: "reads as a sickle"): the pick's
# blade is deepened under its upper edge and the adze widened. Doom's
# grammar again (cf. gen_weapon.PICKUP_HEAD_SCALE): exaggerated to read,
# the D40 outline kept.
PICK_DEEPEN = 1.6          # cm added under the pick's upper edge at its root, tapering to 0 at the tip
PICK_TIP_U = 18.6          # gen_weapon.PICK_POLY's tip
ADZE_WIDEN = 1.45          # the adze's width (across) times this
ADZE_LONGER = 1.1          # ... and its length
ADZE_THICK = 1.3           # cm: the adze plate's thickness (D40: 0.55); seen from the side it is the adze's depth
HEAD_RIM = ("steel_blue", 1)   # a dark rim round the head, so it holds against the floor at 1x
# The ash shaft (PM: "a flat pale yellow that reads as a ruler"): turned to
# a round, grained, varnished haft. Palette v2 has no mid-saturation tan,
# so the shaft's tones come from three ramps, dark to light: the warm rust
# for the shadow side and the rim, khaki for the body, cream for the lit side.
WOOD_TONES = (("rust_brown", 3), ("rust_brown", 7), ("rust_brown", 10), ("khaki_olive", 10),
              ("cream_yellow", 10), ("cream_yellow", 13))
WOOD_RIM, WOOD_SHADOW, WOOD_SHADE, WOOD_BODY, WOOD_LIT, WOOD_SHINE = range(6)
WOOD_LIGHT = (-0.6, -0.8)  # screen direction the light comes from (upper left, as on the TT-33)
WOOD_GRAIN = 3             # px: period of the dashed grain line along the shaft
FIST_SHADE = 2             # wood tones darker: the shaft inside the fist, in the hand's shadow
SHAFT_BELOW_PX = 90.0      # px of shaft drawn below the grip, down the photo's axis (ends under the bar)
HEAD_SHAFT_K = 2.0         # the shaft under the head over the fist's radius: perspective alone makes a pencil


def _gw():
    return hs._gw()


def wood_cols() -> np.ndarray:
    return np.array([artlib.ramp(r)[i] for r, i in WOOD_TONES], np.uint8)


def draw_head(rig, top, A, P, k: float, r: float) -> np.ndarray:
    """gen_weapon.draw_ice_axe_head (the D40 collar, pick and adze) with the
    pick's blade deepened and the adze widened (PICK_DEEPEN, ADZE_*).
    Returns the shaft's top."""
    gw = _gw()
    A, P = gw.unit(A), gw.perp(P, gw.unit(A))
    N = gw.unit(np.cross(A, P))
    top = np.asarray(top, np.float64)
    shaft_top = top - A * 5.2 * k
    rig.capsule(shaft_top + A * 0.2, shaft_top - A * 3.4 * k, r * 1.14, r * 1.1, "steel", 0.48, 0.8)
    pick = []
    upper = True
    for u, v in gw.PICK_POLY:
        if (u, v) == (18.6, -6.4):
            upper = False                     # the tip: from here on the toothed lower edge
        elif not upper and u > 2.3:
            v -= PICK_DEEPEN * max(0.0, 1.0 - u / PICK_TIP_U)
        pick.append((u * k, v * k))
    rig.plate(top, P, A, pick, gw.AXE_PLATE * k, "steel", 0.52, 0.85, grad=(A, 0.012 / k))
    adze_dir = gw.unit(-P - A * gw.ADZE_DROOP)
    adze = [(u * k * ADZE_LONGER, w * k * ADZE_WIDEN) for u, w in gw.ADZE_POLY]
    rig.plate(top - (A * 1.5 + P * 1.8) * k, adze_dir, N, adze, ADZE_THICK * k, "steel", 0.5, 0.85)
    return shaft_top


def tone_shaft(rgba: np.ndarray, wood: np.ndarray, grip, up) -> np.ndarray:
    """The shaft's pixels re-toned as a round, grained ash haft: across the
    shaft lit side / body / shadow side from the light's side, a dark rim on
    its edge, a dashed grain line down its body, a shine on the lit edge.
    grip and up in this array's pixels. Returns the WOOD_TONES index map
    (-1 off the shaft)."""
    h, w = wood.shape
    ys, xs = np.nonzero(wood)
    idx = np.full((h, w), -1, int)
    if ys.size == 0:
        return idx
    n = np.array([-up[1], up[0]])
    t = (xs - grip[0]) * up[0] + (ys - grip[1]) * up[1]
    a = (xs - grip[0]) * n[0] + (ys - grip[1]) * n[1]
    # the shaft's half width at each step along it (it narrows with depth)
    tb = np.round(t).astype(int)
    half = {}
    for k_, aa in zip(tb, np.abs(a)):
        half[k_] = max(half.get(k_, 0.0), aa)
    hw = np.array([max(1.0, max(half.get(k_ + d, 0.0) for d in (-1, 0, 1))) for k_ in tb])
    sgn = 1.0 if (n @ np.array(WOOD_LIGHT)) > 0 else -1.0
    lit = sgn * a / hw                                  # +1 on the lit edge, -1 on the shadow edge
    tone = np.where(lit > 0.45, WOOD_LIT, np.where(lit > -0.2, WOOD_BODY, np.where(lit > -0.6, WOOD_SHADE,
                                                                                   WOOD_SHADOW)))
    grain = (np.abs(lit + 0.05) < 0.2) & ((tb // WOOD_GRAIN) % 3 != 0) & (hw >= 2.5)
    tone = np.where(grain & (tone == WOOD_BODY), WOOD_SHADE, tone)
    shine = (lit > 0.45) & (lit < 0.8) & ((tb // WOOD_GRAIN) % 2 == 0) & (hw >= 3.0)
    tone = np.where(shine, WOOD_SHINE, tone)
    idx[ys, xs] = tone
    rim = edge(wood)
    idx[rim] = WOOD_RIM
    cols = wood_cols()
    rgba[wood, :3] = cols[idx[wood]]
    return idx


def render_axe(grip_xy, up, rise_px: float, shaft_half_px: float, head_z: float = None,
               flat: float = None, roll: float = None, k: float = None, shaft_w: float = 1.0,
               straight: bool = False):
    """Our ice axe (D40 head, weighted for 1x; ash shaft) along the screen
    direction `up` from the grip at grip_xy (weapon px, depth GRIP_Z); the
    head's top rise_px up that line at head_z, farther and so smaller. The
    shaft is shaft_half_px wide (half) at the fist, like the photo's, and
    runs on below the fist at the fist's depth, off the bottom of the view
    (Doom's grammar: drawn to read, not to measure). Returns gen_weapon's
    Frame with the shaft re-toned (tone_shaft) and the head rimmed."""
    gw = _gw()
    head_z = HEAD_Z if head_z is None else head_z
    flat = HEAD_FLAT if flat is None else flat
    k = HEAD_K if k is None else k
    gx, gy = grip_xy
    hx, hy = gx + up[0] * rise_px, gy + up[1] * rise_px
    G = gw.screen_to_cam(gx, gy, GRIP_Z)
    top = gw.screen_to_cam(hx, hy, head_z)
    ds = np.array([hx - gx, hy - gy])
    A = gw.unit([ds[0], ds[1], flat * float(np.hypot(*ds))])
    roll = HEAD_ROLL if roll is None else roll
    P0 = gw.unit([A[1], -A[0], 0.0])                     # A turned 90 on screen: the pick towards the centre
    if P0[0] > 0:                                        # (a right hand: the pick points left, inwards)
        P0 = -P0
    P = gw.unit(P0 * math.cos(math.radians(roll)) + np.cross(A, P0) * math.sin(math.radians(roll)))
    r_grip = shaft_half_px * GRIP_Z / gw.FOCAL
    r_head = r_grip * HEAD_SHAFT_K * shaft_w
    if straight:
        return straight_axe(grip_xy, up, top, A, P, k, r_head, shaft_half_px)
    rig = gw.Rig()
    shaft_top = draw_head(rig, top, A, P, k, r_head)
    rig.capsule(G, shaft_top - A * 3.0 * k, r_grip, r_head, "wood_ash", 0.55, 0.8)
    low = gw.screen_to_cam(gx - up[0] * SHAFT_BELOW_PX, gy - up[1] * SHAFT_BELOW_PX, GRIP_Z)
    rig.capsule(G, low, r_grip, r_grip, "wood_ash", 0.55, 0.8)
    f = gw.finish(rig)
    wood = (f.rgba[..., 3] > 0) & (f.mat == gw.MAT_ID["wood_ash"])
    tone_shaft(f.rgba, wood, (gx - f.left, gy - f.top), up)
    steel = (f.rgba[..., 3] > 0) & ~wood
    f.rgba[edge(steel, ~(f.rgba[..., 3] > 0)), :3] = artlib.ramp(HEAD_RIM[0])[HEAD_RIM[1]]
    return f


def straight_axe(grip_xy, up, top, A, P, k: float, r_head: float, half_px: float):
    """D76 (CEO: "hazlo recto"): the shaft as one straight rigid bar on the
    screen, constant width 2 * half_px, from SHAFT_BELOW_PX under the grip
    through the grip to the head's collar; the head moved so its collar
    sits square on that axis, then drawn over the bar's top end."""
    gw = _gw()
    gx, gy = grip_xy
    up = np.asarray(up, float)
    n = np.array([-up[1], up[0]])
    for _ in range(2):                                  # put the collar on the axis
        rig = gw.Rig()
        shaft_top = draw_head(rig, top, A, P, k, r_head)
        cx, cy, _ = rig.project(shaft_top)
        off = (cx - gx) * n[0] + (cy - gy) * n[1]        # px off the axis, across it
        top = top - np.array([n[0], n[1], 0.0]) * off * shaft_top[2] / gw.FOCAL
    head = gw.finish(rig)
    t_top = (cx - gx) * up[0] + (cy - gy) * up[1]
    ends = [(gx - up[0] * SHAFT_BELOW_PX, gy - up[1] * SHAFT_BELOW_PX), (gx + up[0] * t_top, gy + up[1] * t_top)]
    x0 = int(math.floor(min(e[0] for e in ends) - half_px - 1))
    x1 = int(math.ceil(max(e[0] for e in ends) + half_px + 1))
    y0 = int(math.floor(min(e[1] for e in ends) - half_px - 1))
    y1 = int(math.ceil(max(e[1] for e in ends) + half_px + 1))
    L, T = min(x0, head.left), min(y0, head.top)
    R = max(x1, head.left + head.rgba.shape[1])
    B = max(y1, head.top + head.rgba.shape[0])
    rgba = np.zeros((B - T, R - L, 4), np.uint8)
    mat = np.full((B - T, R - L), -1, np.int16)
    yy, xx = np.mgrid[T:B, L:R] + 0.5
    t = (xx - gx) * up[0] + (yy - gy) * up[1]
    a = (xx - gx) * n[0] + (yy - gy) * n[1]
    wood = (np.abs(a) < half_px) & (t >= -SHAFT_BELOW_PX) & (t <= t_top)
    rgba[wood] = (200, 190, 141, 255)
    mat[wood] = gw.MAT_ID["wood_ash"]
    tone_shaft(rgba, wood, (gx - L, gy - T), up)
    hm = head.rgba[..., 3] > 0
    sub = rgba[head.top - T:head.top - T + hm.shape[0], head.left - L:head.left - L + hm.shape[1]]
    sub[hm] = head.rgba[hm]
    mat[head.top - T:head.top - T + hm.shape[0], head.left - L:head.left - L + hm.shape[1]][hm] = head.mat[hm]
    steel = hm & (head.mat != gw.MAT_ID["wood_ash"])
    edge_ = edge(steel, ~hm)
    sub[edge_, :3] = artlib.ramp(HEAD_RIM[0])[HEAD_RIM[1]]
    return gw.Frame(rgba, mat, L, T, True)


# ------------------------------------------------------------------ cells
@dataclass(frozen=True)
class Cell:
    key: str
    ref: str
    tones: int
    size: float               # palm breadth over the TT-33 hand's
    grip_x: float             # weapon px: the column the grip sits on
    why: str
    shaft_k: float = 1.0      # D75: the shaft above the fist this much longer (the head that much higher)
    head_k: float = 1.0       # D75: the head this much bigger
    grip_y: float | None = None   # weapon px of the grip row; None: searched so the top meets the TT-33's
    shaft_w: float = 1.0      # D76: the shaft's radius under the head times this (keeps a long shaft thick)
    straight: bool = False    # D76b: the shaft drawn as one straight bar of constant width (straight_axe)


# Round 3b (CEO on 2026-10-14_2252: "cámbialo a diestro"; PM: the shaft reads
# as a ruler, the head as a sickle): only the three cells that passed round
# 3a, R1 mirrored to a right hand, the axe polished. Round 3a's six cells
# (R1 left-handed, R2 and R3 dropped) are in its dated preview; R2 and R3
# stay in REFS as data, unused.
CELLS = (
    Cell("C1", "R1", 4, 1.00, 185.0, "the base: R1 as a right hand, 4 skin tones, the TT-33's hand scale, centre-right"),
    Cell("C3", "R1", 4, 1.15, 185.0, "C1 at 115 %"),
    Cell("C4", "R1", 3, 1.00, 200.0, "C1 with 3 skin tones, 15 px further right"),
)


def tt33_palm_px() -> float:
    """The TT-33 hands' palm breadth in px: half the widest skin row of
    SDTTA0 (two hands side by side, seen from behind)."""
    spr, _ = hs.read_png_sprite(TT33_A)
    cols = np.array(hs.ramp_cols(SKIN), np.uint8)
    skin = (spr[..., 3] > 0) & (spr[..., None, :3] == cols[None, None]).all(-1).any(-1)
    return float(skin.sum(1).max()) / 2.0


@functools.lru_cache(maxsize=1)
def tt33_skin_visible() -> int:
    """SDTTA0's skin pixels above the status bar (both hands)."""
    spr, off = hs.read_png_sprite(TT33_A)
    cols = np.array(hs.ramp_cols(SKIN), np.uint8)
    skin = (spr[..., 3] > 0) & (spr[..., None, :3] == cols[None, None]).all(-1).any(-1)
    _, y0 = hs.place(spr, off, bar=True)
    rows = np.arange(spr.shape[0])[:, None] + y0
    return int((skin & (rows < hs.VIEW_H)).sum())


def tt33_top() -> int:
    """SDTTA0's top row on the screen, status bar on."""
    spr, off = hs.read_png_sprite(TT33_A)
    return hs.measure(spr, off)["top"]


def shade_wood(cols: np.ndarray, steps: int) -> np.ndarray:
    """Shaft colours (WOOD_TONES) moved `steps` tones darker, never onto the
    rim's; any other colour is left as it is."""
    tones = wood_cols()
    out = cols.copy()
    for i, c in enumerate(cols):
        hit = np.flatnonzero((tones == c).all(1))
        if hit.size and int(hit[0]) != WOOD_RIM:
            out[i] = tones[max(WOOD_SHADOW, int(hit[0]) - steps)]
    return out


def compose(axe, hand: dict, hand_xy) -> tuple[np.ndarray, tuple[int, int], np.ndarray]:
    """The axe, then the hand on top. Returns (rgba, offsets, axe-only mask
    in the same canvas)."""
    hx, hy = hand_xy
    hr = hand["rgba"]
    x0, y0 = min(axe.left, hx), min(axe.top, hy)
    x1 = max(axe.left + axe.rgba.shape[1], hx + hr.shape[1])
    y1 = max(axe.top + axe.rgba.shape[0], hy + hr.shape[0])
    canvas = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
    axe_m = np.zeros(canvas.shape[:2], bool)
    sub = canvas[axe.top - y0:axe.top - y0 + axe.rgba.shape[0], axe.left - x0:axe.left - x0 + axe.rgba.shape[1]]
    m = (axe.rgba[..., 3] > 0) & (axe.mat == _gw().MAT_ID["wood_ash"])    # the shaft only
    sub[axe.rgba[..., 3] > 0] = axe.rgba[axe.rgba[..., 3] > 0]
    axe_m[axe.top - y0:axe.top - y0 + axe.rgba.shape[0], axe.left - x0:axe.left - x0 + axe.rgba.shape[1]] = m
    sub = canvas[hy - y0:hy - y0 + hr.shape[0], hx - x0:hx - x0 + hr.shape[1]]
    shade = hand["fist_hole"] & (sub[..., 3] > 0)          # the shaft inside the fist, in its shadow
    if shade.any():
        sub[shade, :3] = shade_wood(sub[shade, :3], FIST_SHADE)
    m = hr[..., 3] > 0
    sub[m] = hr[m]
    # crop to what the screen can show (weapon space 0..320 x 0..200)
    cx0, cy0 = max(x0, 0), max(y0, 0)
    cx1, cy1 = min(x1, SCREEN_W), min(y1, SCREEN_H)
    canvas = canvas[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    axe_m = axe_m[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    return canvas, (-cx0, WEAPONTOP - cy0), axe_m       # axe_m: where the shaft was drawn


def build_cell(cell: Cell, cache: dict | None = None) -> dict:
    """One cell: the hand from its reference, the axe, the frame on screen."""
    cache = {} if cache is None else cache
    spec = oriented(REFS[cell.ref])
    if ("seg", spec.key) not in cache:
        cache[("seg", spec.key)] = segment(spec)
    if "refs" not in cache:
        cache["refs"] = ref_lums()
        cache["palm"] = tt33_palm_px()
        cache["top"] = tt33_top()
    seg = cache[("seg", spec.key)]
    palm_px = cache["palm"] * cell.size
    scale = palm_px / palm_len(spec)
    fl = to_sprite(seg, spec, scale)
    hand = hand_sprite(fl, cell.tones, cache["refs"])
    up = fl["up"]
    shaft_half = spec.shaft_half * scale
    rise = HEAD_RISE * palm_px * cell.shaft_k
    target_top = cache["top"]               # status bar on

    def frame_at(gy: float):
        gxy = (cell.grip_x, gy)
        axe = render_axe(gxy, up, rise, shaft_half, k=HEAD_K * cell.head_k, shaft_w=cell.shaft_w,
                         straight=cell.straight)
        hxy = (int(round(cell.grip_x - fl["grip"][0])), int(round(gy - fl["grip"][1])))
        rgba, off, axe_m = compose(axe, hand, hxy)
        return rgba, off, axe_m, hxy
    lo, hi = 100.0, 199.0                    # weapon px searched for the grip row
    for _ in range(0 if cell.grip_y is not None else 14):
        mid = (lo + hi) / 2
        rgba, off, _, _ = frame_at(mid)
        if hs.measure(rgba, off)["top"] < target_top:
            lo = mid
        else:
            hi = mid
    gy = cell.grip_y if cell.grip_y is not None else round((lo + hi) / 2, 2)
    rgba, off, axe_m, hxy = frame_at(gy)
    return {"cell": cell, "spec": spec, "sprite": rgba, "offsets": off, "axe_mask": axe_m, "up": up,
            "hand": hand, "hand_xy": hxy, "grip": (cell.grip_x, gy), "scale": scale,
            "palm_px": palm_px, "metrics": metrics(rgba, off, axe_m, hand, hxy, (cell.grip_x, gy), up, palm_px)}


def metrics(rgba, off, axe_m, hand, hxy, grip=None, up=None, palm_px: float = 0.0) -> dict:
    """Measured facts for the self-gate (status bar on unless said)."""
    m = hs.measure(rgba, off)
    x0, y0 = hs.place(rgba, off, bar=False)            # weapon-space top-left
    # where the photo's border shows on screen (a cut sleeve)
    ys, xs = np.nonzero(hand["border"])
    sx, sy = xs + hxy[0], ys + hxy[1]
    vis_full = (sx >= 0) & (sx < SCREEN_W) & (sy >= 0) & (sy < SCREEN_H)
    vis_bar = vis_full & (sy - BAR_LIFT < hs.VIEW_H)
    # the shaft outside the fist: shaft pixels the hand leaves visible above
    # the status bar, beyond half a palm from the grip up or down the axis
    above = below = 0
    if grip is not None:
        vis = axe_m & ~_hand_mask(rgba.shape[:2], hand, hxy, x0, y0)
        ys, xs = np.nonzero(vis)
        on = (ys + y0 - BAR_LIFT) < hs.VIEW_H
        t = (xs + x0 - grip[0]) * up[0] + (ys + y0 - grip[1]) * up[1]
        above = int((on & (t > palm_px / 2)).sum())
        below = int((on & (t < -palm_px / 2)).sum())
    skin_scr = _hand_mask(rgba.shape[:2], hand, hxy, x0, y0, "skin")
    rows = np.arange(rgba.shape[0])[:, None] + y0 - BAR_LIFT
    return {
        "height_above_bar": m["height"], "top": m["top"], "bbox_bar_on": m["bbox"],
        "size": [int(rgba.shape[1]), int(rgba.shape[0])], "offsets": list(off),
        "skin_px": int(hand["skin"].sum()), "sleeve_px": int(hand["sleeve"].sum()),
        "skin_px_visible": int((skin_scr & (rows < hs.VIEW_H)).sum()),
        "photo_border_visible_full": int(vis_full.sum()), "photo_border_visible_bar": int(vis_bar.sum()),
        "shaft_px_above_fist": above, "shaft_px_below_fist": below,
    }


def _hand_mask(shape, hand, hxy, x0, y0, which: str = "all") -> np.ndarray:
    """The hand sprite's mask (or its skin) in a frame canvas at (x0, y0)."""
    out = np.zeros(shape, bool)
    src = hand["rgba"][..., 3] > 0 if which == "all" else hand[which]
    hx, hy = hxy[0] - x0, hxy[1] - y0
    ys, xs = np.nonzero(src)
    ys, xs = ys + hy, xs + hx
    ok = (ys >= 0) & (ys < shape[0]) & (xs >= 0) & (xs < shape[1])
    out[ys[ok], xs[ok]] = True
    return out


def palette_set() -> set[tuple[int, int, int]]:
    return {tuple(c) for c in artlib.load_palette()["colours_v2"]}


# ------------------------------------------------------------------ sheet
# The self-gate, written after looking at every cell at 1x, 2x, 3x and 4x
# (art-director, 2026-10-14). "pass" cells go to the CEO; "drop" cells are
# shown small at the end with the reason, so they are not proposed again.
VERDICTS: dict[str, tuple[str, str]] = {
    "C1": ("pass", "A right hand from the player's eye: the sleeve comes in from the bottom right, the back of "
                   "the hand faces right, the thumb closes over the top of the haft and the four knuckles curl "
                   "round it on the left, towards the centre. The haft is wood now (rust shadow side, khaki body, "
                   "cream lit side, a dashed grain, a dark rim), darker inside the fist, showing under the head "
                   "and below the fist; the head has weight (deeper pick, wider and thicker adze, a dark rim) and "
                   "reads as the D40 ice axe, not a sickle. Same top as the TT-33; about 920 skin px above the "
                   "bar against its 999. At 1x the fingers are a knuckle row; at 2x, fingers."),
    "C3": ("pass", "C1 at 115 %: the fist leads (about 1010 skin px above the bar, the TT-33's 999), the "
                   "knuckles are clearer and more haft shows above the fist; the frame is no taller or wider than "
                   "C1's (x 165-225)."),
    "C4": ("pass", "C1 with three skin tones (flatter, closer to Freedoom's chunky modelling) and the grip 15 px "
                   "further right (x 181-241, still left of the chainsaw's 253). Same hand and axe as C1, so it "
                   "passes for the same reasons; it is here to choose tones and column."),
}
RECOMMENDED = "C3"

PREVIEW_SLUG = "F4_ice-axe-right-hand"     # round 3a's was F4_ice-axe-from-reference (2026-10-14_2252)
NEUTRAL = (96, 96, 100)
SHEET_ZOOM = 3
HAND_CROP = (100, 92, 260, 168)       # screen box (bar on) shown at 4x: the hands, the TT-33's and ours


def png_uri(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def on_neutral(rgba: np.ndarray, pad: int = 4) -> np.ndarray:
    out = np.zeros((rgba.shape[0] + 2 * pad, rgba.shape[1] + 2 * pad, 3), np.uint8)
    out[:] = NEUTRAL
    m = rgba[..., 3] > 0
    out[pad:pad + rgba.shape[0], pad:pad + rgba.shape[1]][m] = rgba[m, :3]
    return out


def visible_part(c: dict) -> np.ndarray:
    """The frame's pixels that show above the status bar, cropped to them."""
    spr, off = c["sprite"], c["offsets"]
    _, y0 = hs.place(spr, off, bar=True)
    rows = np.arange(spr.shape[0]) + y0
    part = spr[rows < hs.VIEW_H]
    a = part[..., 3] > 0
    r, q = np.flatnonzero(a.any(1)), np.flatnonzero(a.any(0))
    return part[r[0]:r[-1] + 1, q[0]:q[-1] + 1]


def zoom(arr: np.ndarray, k: int) -> np.ndarray:
    return np.asarray(Image.fromarray(arr).resize((arr.shape[1] * k, arr.shape[0] * k), Image.Resampling.NEAREST))


def screens(cells: dict) -> dict:
    """Each cell on the MAP01 mock (status bar on), and the TT-33's."""
    bg = hs.map01_backdrop()
    tt, toff = hs.read_png_sprite(TT33_A)
    out = {"TT33": hs.draw_on_screen(bg, tt, toff)}
    for k, c in cells.items():
        out[k] = hs.draw_on_screen(bg, c["sprite"], c["offsets"])
    return out


def derivation(spec: RefSpec, seg: dict, width: int = 420) -> np.ndarray:
    """The photo dimmed outside the hand, the sleeve tinted, the shaft
    cut out in blue, the lasso in yellow, the knuckle span in red."""
    ph = (seg["photo"] * 255).astype(np.uint8)
    ov = ph.copy()
    ov[~seg["hand"]] = (ov[~seg["hand"]] * 0.3).astype(np.uint8)
    tint = seg["sleeve"]
    ov[tint] = (ov[tint] * 0.6 + np.array([0, 90, 0]) * 0.4).astype(np.uint8)
    ov[seg["hole"]] = (ov[seg["hole"]] * 0.4 + np.array([30, 60, 220]) * 0.6).astype(np.uint8)
    img = Image.fromarray(ov)
    d = ImageDraw.Draw(img)
    d.line([tuple(map(float, p)) for p in spec.lasso] + [tuple(map(float, spec.lasso[0]))],
           fill=(240, 200, 40), width=3)
    d.line([tuple(map(float, p)) for p in spec.palm], fill=(240, 60, 60), width=6)
    h = round(img.height * width / img.width)
    return np.asarray(img.resize((width, h), Image.Resampling.BOX))


def facts_html(c: dict) -> str:
    cl, m = c["cell"], c["metrics"]
    return (f"<dl><dt>reference</dt><dd>{cl.ref}: {html.escape(c['spec'].file)}</dd>"
            f"<dt>skin tones</dt><dd>{cl.tones} (sleeve {max(3, cl.tones - 1)})</dd>"
            f"<dt>size</dt><dd>{round(cl.size * 100)} % of the TT-33 hand (palm {c['palm_px']:.1f} px)</dd>"
            f"<dt>grip column</dt><dd>x {cl.grip_x:.0f} (TT-33 centre 162, Freedoom chainsaw 216)</dd>"
            f"<dt>height above bar</dt><dd>{m['height_above_bar']} px (TT-33 56)</dd>"
            f"<dt>on screen</dt><dd>x {m['bbox_bar_on'][0]}-{m['bbox_bar_on'][2]}</dd>"
            f"<dt>shaft px visible above / below the fist</dt><dd>{m['shaft_px_above_fist']} / "
            f"{m['shaft_px_below_fist']}</dd>"
            f"<dt>skin px above the bar</dt><dd>{m['skin_px_visible']} (TT-33 {tt33_skin_visible()})</dd>"
            f"<dt>photo edge on screen</dt><dd>{m['photo_border_visible_full']} px full-screen, "
            f"{m['photo_border_visible_bar']} px with the bar</dd></dl>")


def build_sheet(cells: dict, stamp: str, cache: dict) -> tuple[Path, Path]:
    """The HTML preview and the PNG contact sheet."""
    import sheetlib
    scr = screens(cells)
    x0, y0, x1, y1 = HAND_CROP
    tt_scr = scr["TT33"]
    passed = [k for k in cells if VERDICTS.get(k, ("pass", ""))[0] == "pass"]
    dropped = [k for k in cells if k not in passed]
    refs_html = '<div class="strip">' + "".join(
        f'<div class="tile"><img class="px" src="{png_uri(derivation(oriented(spec), cache[("seg", key)]))}">'
        f'<div class="cap"><b>{key}</b> {html.escape(spec.file)}<br>{html.escape(spec.title)}</div></div>'
        for key, spec in REFS.items() if ("seg", key) in cache) + "</div>"

    def card(k: str, small: bool = False) -> str:
        c = cells[k]
        verdict = VERDICTS.get(k, ("pass", "(not yet judged)"))
        rec = k == RECOMMENDED
        imgs = [("alone, 3x (what shows above the bar)", zoom(on_neutral(visible_part(c)), SHEET_ZOOM))]
        if small:
            imgs += [("MAP01 mock, 2x", zoom(scr[k], 2)), ("the hand, 4x", zoom(scr[k][y0:y1, x0:x1], 4))]
        else:
            imgs += [("MAP01 mock, 1x", scr[k]), ("approved TT-33, 1x", tt_scr),
                     ("MAP01 mock, 2x", zoom(scr[k], 2)), ("approved TT-33, 2x", zoom(tt_scr, 2)),
                     ("the hands, 4x: ours", zoom(scr[k][y0:y1, x0:x1], 4)),
                     ("the hands, 4x: TT-33", zoom(tt_scr[y0:y1, x0:x1], 4))]
        tiles = "".join(f'<div class="tile"><img class="px" src="{png_uri(a)}"><div class="cap">'
                        f'{html.escape(t)}</div></div>' for t, a in imgs)
        return (f'<div class="card{" rec" if rec else ""}">' + ('<span class="tag">recommended</span>' if rec else "")
                + f'<h3>{k} &middot; {html.escape(c["cell"].why)}</h3>'
                + f'<p class="desc"><b>{verdict[0].upper()}</b>: {html.escape(verdict[1])}</p>'
                + f'<div class="strip">{tiles}</div>{facts_html(c)}</div>')
    sections = [
        ("What was taken from the reference",
         "The CEO's Fooocus image 1, mirrored back to a right hand, dimmed outside what was kept: hand and sleeve as segmented (sleeve tinted "
         "green), the photo's shaft cut out (blue; ours goes in its place), the rough lasso (yellow) and the "
         "knuckle span that sets the scale (red). The photo's own axes and knives are not used.",
         refs_html),
        ("Cells that pass the self-gate",
         "Each: the frame alone at 3x; on a MAP01 mock with our status bar at 1x and 2x, next to the approved "
         "TT-33 ready frame (SDTTA0, D61) on the same mock; and the hands region at 4x, ours against the TT-33's.",
         '<div class="cards">' + "".join(card(k) for k in passed) + "</div>"),
    ]
    if dropped:
        sections.append(("Dropped by the self-gate (not proposed)",
                         "Kept here small, with the reason, so they are not proposed again.",
                         '<div class="cards">' + "".join(card(k, True) for k in dropped) + "</div>"))
    intro = (
        "N14 / N4 round 3b: the ice axe's held frame (ready), the hand <b>derived</b> from the CEO's reference "
        "image 1, now <b>as a right hand</b> (the file is mirrored on purpose; flipped back before the cut-out, "
        "so the arm comes in from the bottom right like Doom's fist and chainsaw and our TT-33 hands): "
        "segmented from the photo, turned and scaled to the TT-33 hands' scale, toned onto the same skin and "
        "sleeve ramps (palette v2 flesh_pink, military_green). Polished after the PM's notes: the haft is "
        "toned as wood (shadow side, body, lit side, grain, a dark rim; darker inside the fist) instead of a "
        "flat pale ruler, and the head has weight (a deeper pick, a wider and thicker adze, a dark rim) so it "
        "reads as the D40 ice axe at 1x, not a sickle. Every frame stands as high as the TT-33 (56 px above "
        "the bar, D57). Round 3a (left-handed, 2026-10-14_2252) stays as it was. Pick a cell, or none; the "
        "swing frames follow from the chosen one. Nothing here is installed.")
    html_path = sheetlib.write_sheet(
        PREVIEW_DIR / f"{stamp}_{PREVIEW_SLUG}.html", lang="en",
        title="Ice axe, right hand, from the CEO's reference: held frame (N14 / N4 round 3b)",
        subtitle="F4 arsenal - tools/art/hand_ref.py - drafts in work/art/hand_ref/", intro=intro,
        sections=sections,
        footer="Sources: the hand, wrist and sleeve from the CEO's own Fooocus (SDXL) generations in "
               "work/art/reference/ (a licence row goes to LICENSES.md if a cell is approved); the axe is ours "
               "(gen_weapon.draw_ice_axe_head, D40); skin and sleeve ramps from palette v2. The TT-33 frame shown "
               "for scale is the approved draft (Freedoom BSD-3 hands, D61). No pixel of a commercial game. "
               "Engine pass pending (D26): agents do not start GZDoom.")
    # ---- PNG contact sheet
    f_t, f_b, f_s = hs.font(22), hs.font(15), hs.font(12)
    pad, gap, alone_w = 16, 12, 300
    row_h = 2 * SCREEN_H + 40
    W = pad * 2 + alone_w + gap + SCREEN_W + gap + 2 * SCREEN_W + gap + 2 * SCREEN_W
    H = 70 + row_h * (len(passed) + 1) + (60 + 160 if dropped else 0)
    sheet = Image.new("RGB", (W, H), hs.SHEET_BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 12), "Ice axe held frame, right hand, from the CEO's reference 1 (N14 / N4 round 3b): the cells that pass",
           font=f_t, fill=hs.INK)
    d.text((pad, 42), "alone 3x  |  MAP01 mock 1x  |  MAP01 mock 2x  |  approved TT-33 on the same mock, 2x",
           font=f_s, fill=hs.DIM)
    y = 70
    for k in passed + ["TT33"]:
        x = pad
        if k == "TT33":
            d.text((x, y), "TT-33 SDTTA0 (approved, D61), for scale", font=f_b, fill=hs.GOLD)
            alone = zoom(on_neutral(hs.read_png_sprite(TT33_A)[0]), SHEET_ZOOM)
            s1 = tt_scr
        else:
            c = cells[k]
            tag = "   (recommended)" if k == RECOMMENDED else ""
            d.text((x, y), f"{k}: {c['cell'].why}{tag}", font=f_b, fill=hs.GOLD)
            alone = zoom(on_neutral(visible_part(c)), SHEET_ZOOM)
            s1 = scr[k]
        yy = y + 22
        a = Image.fromarray(alone)
        if a.width > alone_w:
            a = a.resize((alone_w, round(a.height * alone_w / a.width)), Image.Resampling.NEAREST)
        sheet.paste(a, (x, yy))
        x += alone_w + gap
        sheet.paste(Image.fromarray(s1), (x, yy))
        x += SCREEN_W + gap
        sheet.paste(Image.fromarray(zoom(s1, 2)), (x, yy))
        x += 2 * SCREEN_W + gap
        sheet.paste(Image.fromarray(zoom(tt_scr, 2)), (x, yy))
        y += row_h
    if dropped:
        d.text((pad, y), "Dropped by the self-gate (reasons in the HTML): " + ", ".join(dropped),
               font=f_b, fill=hs.RED)
        x = pad
        for k in dropped:
            sheet.paste(Image.fromarray(scr[k]).resize((256, 160), Image.Resampling.NEAREST), (x, y + 26))
            d.text((x, y + 190), k, font=f_s, fill=hs.DIM)
            x += 270
    png_path = PREVIEW_DIR / f"{stamp}_{PREVIEW_SLUG}.png"
    sheet.save(png_path, optimize=True)
    return html_path, png_path


# ------------------------------------------------- D75 silhouettes (cheap review)
# The CEO approved C3's hand (D75) and allows a bigger axe than Freedoom's
# envelope; he asked for the cheapest review: flat silhouettes on a
# transparent sheet. C3's hand stays where it is (its grip row is kept);
# only the shaft above the fist and the head grow.
SIL_SHAFT = (1.0, 1.35, 1.7)
SIL_HEAD = (1.0, 1.4, 1.8)
SIL_INK = (24, 24, 24, 255)
SIL_LINE = (150, 150, 150, 160)
SIL_BOX = (110, 20, 290, 200)        # screen box (status bar on) shown per variant
SIL_SLUG = "F4_ice-axe-silhouettes"


def shaft_width_above_fist(c: dict) -> float:
    """Median on-screen width (px, across the axis) of the shaft visible
    above the fist, status bar on."""
    spr, off = c["sprite"], c["offsets"]
    x0, y0 = hs.place(spr, off, bar=False)
    vis = c["axe_mask"] & ~_hand_mask(spr.shape[:2], c["hand"], c["hand_xy"], x0, y0)
    ys, xs = np.nonzero(vis)
    gx, gy = c["grip"]
    up = c["up"]
    n = np.array([-up[1], up[0]])
    t = (xs + x0 - gx) * up[0] + (ys + y0 - gy) * up[1]
    a = (xs + x0 - gx) * n[0] + (ys + y0 - gy) * n[1]
    keep = t > c["palm_px"] / 2
    widths = [np.ptp(a[keep & (np.round(t) == k)]) + 1 for k in np.unique(np.round(t[keep]))]
    return float(np.median(widths)) if widths else 0.0


# D76: the CEO's pick, L1.7 H1.8, with the shaft as wide as L1.0 H1.8's. In
# L1.0 the shaft is 10 px wide at the fist and the head sits on it; the
# longer shaft runs up into depth and perspective thins it to 4 px. Making
# its radius under the head HEAD_Z / GRIP_Z times the fist's (no taper on
# screen) keeps the 10 px all the way up (measured: 10 px at every step).
NO_TAPER = HEAD_Z / GRIP_Z / HEAD_SHAFT_K
D76_WIDE = {"shaft_k": 1.7, "head_k": 1.8, "shaft_w": NO_TAPER}
# D76b, the CEO on the widened one: "Longitud OK, pero te ha salido torcido.
# Haz el arma recta": the 3D shaft's two capsules drift apart on screen, so
# the final shaft is a straight bar (straight_axe), 10 px, the head square on it.
D76_PICK = {"shaft_k": 1.7, "head_k": 1.8, "straight": True}


def silhouette_tile(cell: Cell, cache: dict) -> np.ndarray:
    """One variant as a flat silhouette, what shows above the status bar, at 2x."""
    c = build_cell(cell, cache)
    x0, y0, x1, y1 = SIL_BOX
    scr = np.zeros((SCREEN_H, SCREEN_W, 4), np.uint8)
    spr = c["sprite"]
    px, py = hs.place(spr, c["offsets"], bar=True)
    ys, xs = np.nonzero(spr[..., 3] > 0)
    ys, xs = ys + py, xs + px
    ok = (ys >= 0) & (ys < hs.VIEW_H) & (xs >= 0) & (xs < SCREEN_W)   # the status bar hides the rest
    scr[ys[ok], xs[ok]] = SIL_INK
    return np.asarray(Image.fromarray(scr[y0:y1, x0:x1], "RGBA").resize((2 * (x1 - x0), 2 * (y1 - y0)),
                                                                           Image.Resampling.NEAREST))


def silhouette_sheet(variants: list, path: Path, cols: int, out_dir: Path | None = None) -> Path:
    """variants: [(label, Cell)]; a transparent sheet, `cols` per row, each tile
    with the TT-33's top and the status bar's top as thin grey lines."""
    cache: dict = {}
    x0, y0, x1, y1 = SIL_BOX
    tw, th = 2 * (x1 - x0), 2 * (y1 - y0)
    rows = -(-len(variants) // cols)
    f = hs.font(14)
    sheet = Image.new("RGBA", (cols * (tw + 10) + 10, rows * (th + 24) + 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheet)
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
    for n, (label, cell) in enumerate(variants):
        tile = silhouette_tile(cell, cache)
        if out_dir is not None:
            Image.fromarray(tile, "RGBA").save(out_dir / f"{label.replace(' ', '_')}.png")
        ox, oy = 10 + (n % cols) * (tw + 10), 5 + (n // cols) * (th + 24)
        sheet.alpha_composite(Image.fromarray(tile, "RGBA"), (ox, oy))
        for yy in (hs.VIEW_H, tt33_top()):          # status bar top, TT-33's top
            d.line([(ox, oy + 2 * (yy - y0)), (ox + tw, oy + 2 * (yy - y0))], fill=SIL_LINE, width=1)
        d.text((ox, oy + th + 3), label, font=f, fill=(128, 128, 128, 255))
    sheet.save(path, optimize=True)
    return path


def c3_grip_row(cache: dict | None = None) -> tuple[Cell, float]:
    base = next(c for c in CELLS if c.key == "C3")
    return base, build_cell(base, {} if cache is None else cache)["grip"][1]


def build_silhouettes(stamp: str, out_dir: Path = OUT_DIR / "silhouettes") -> Path:
    """D75: the 3x3 grid of shaft length x head size on C3's hand."""
    base, gy = c3_grip_row()
    variants = [(f"L{sk} H{hk}", replace(base, key=f"L{sk}_H{hk}", shaft_k=sk, head_k=hk, grip_y=gy))
                for hk in SIL_HEAD for sk in SIL_SHAFT]
    return silhouette_sheet(variants, PREVIEW_DIR / f"{stamp}_{SIL_SLUG}.png", 3, out_dir)


def build_silhouette_final(stamp: str, out_dir: Path = OUT_DIR / "silhouettes") -> Path:
    """D76: the pick (L1.7 H1.8, the shaft as wide as L1.0's) between L1.0 H1.8 and the original L1.7 H1.8."""
    base, gy = c3_grip_row()
    variants = [("L1.0 H1.8", replace(base, head_k=1.8, grip_y=gy)),
                ("L1.7 H1.8", replace(base, shaft_k=1.7, head_k=1.8, grip_y=gy)),
                ("L1.7 H1.8 wide (D76)", replace(base, key="D76", grip_y=gy, **D76_WIDE))]
    return silhouette_sheet(variants, PREVIEW_DIR / f"{stamp}_F4_ice-axe-silhouette-final.png", 3, out_dir)


def build_silhouette_straight(stamp: str, out_dir: Path = OUT_DIR / "silhouettes") -> Path:
    """D76b: the straight shaft next to the previous widened one."""
    base, gy = c3_grip_row()
    variants = [("L1.7 H1.8 wide (D76)", replace(base, key="D76", grip_y=gy, **D76_WIDE)),
                ("L1.7 H1.8 straight (D76b)", replace(base, key="D76b", grip_y=gy, **D76_PICK))]
    return silhouette_sheet(variants, PREVIEW_DIR / f"{stamp}_F4_ice-axe-silhouette-straight.png", 2, out_dir)


# ======================================================= PPSh-41 (D77)
# The CEO's Gemini render (work/art/reference/gemini_ppsh41.jpg, gitignored,
# never shipped): a first-person PPSh-41 in two bare hands, the left under
# the barrel jacket, the right on the stock, olive sleeves. Step 1 is the
# silhouette only: the outline of guns, hands and sleeves traced on the
# render (PPSH_OUTLINE, render px), the snow seen through it (the trigger
# guard, the gaps) taken out by colour, then shrunk by area to Doom's scale.
# The render's own first-person camera is kept. Its HUD's top (PPSH_HUD_Y)
# is our status bar's line and its right edge, where the right sleeve
# leaves, the screen's right edge: both sleeves leave the view as in the
# render. Sizes: Freedoom's chaingun height above the bar (CHGGA0) x1,
# x1.3, x1.6 (the CEO allowed oversize for the ice axe, D75).
PPSH_REF = REF_DIR / "gemini_ppsh41.jpg"
PPSH_HUD_Y = 652                  # render px: first row of the render's status bar
PPSH_W = 1408                     # the render's width
# The render's right sleeve leaves through its right edge, level; a Doom
# frame does not fill the screen and a level forearm continued to the edge
# reads as a long stick (the CEO's old complaint), so past the wrist the
# sleeve turns down and leaves under the status bar, as Doom's arms do.
PPSH_SLEEVE_END = 1340            # render px: where the sleeve's top edge meets the bar
PPSH_CENTRE_X = 200               # screen px: the gun's (render-width part) centre, centre-right
PPSH_OUTLINE = (
    (232, 282), (318, 262), (336, 270), (420, 296), (510, 320), (522, 311), (560, 314), (600, 330),
    (625, 347), (700, 362), (788, 372), (830, 368), (840, 396), (872, 405), (886, 400), (960, 420),
    (985, 440), (992, 470), (1020, 483), (1080, 490), (1120, 503), (1180, 525), (1200, 522), (1262, 548),
    (PPSH_SLEEVE_END, 652), (1060, 652), (960, 648), (935, 625), (930, 590), (900, 598), (835, 580), (785, 548),
    (785, 505), (725, 480), (720, 560), (700, 620), (650, 648), (600, 652), (553, 652), (287, 652),
    (353, 583), (420, 517), (440, 503), (433, 417), (440, 350), (420, 363), (227, 303), (226, 290),
)
PPSH_SNOW_V, PPSH_SNOW_S = 0.72, 0.15
PPSH_SIZES = (1.0, 1.3, 1.6)
PPSH_REF_LUMP = "CHGGA0"          # Freedoom's chaingun: the envelope (35 px above the bar)
PPSH_SLUG = "F4_ppsh-silhouettes"


def ppsh_mask() -> np.ndarray:
    """The render's guns + hands + sleeves as a bool mask (render px)."""
    with Image.open(PPSH_REF) as im:
        rgb = np.asarray(im.convert("RGB"), np.float32) / 255.0
    _, sat, val = hsv(rgb)
    h, w = rgb.shape[:2]
    m = polygon_mask((h, max(w, PPSH_SLEEVE_END + 2)), PPSH_OUTLINE)
    m[:, :w] &= ~((val > PPSH_SNOW_V) & (sat < PPSH_SNOW_S))
    m = morph(morph(m, 2, "open"), 2, "close")
    m[PPSH_HUD_Y:] = False
    return m


def ppsh_height_above_bar() -> int:
    lumps, pal = hs.read_wad()
    spr, off = hs.decode_patch(lumps[PPSH_REF_LUMP], pal)
    return hs.measure(spr, off)["height"]


def ppsh_screen(mask: np.ndarray, height_px: float) -> np.ndarray:
    """The mask scaled so it stands height_px above the status bar, its
    bottom on the bar and the gun's centre (the render-width part) on
    PPSH_CENTRE_X; bool 168x320 (the view)."""
    rows = np.flatnonzero(mask.any(1))
    cols = np.flatnonzero(mask[:, :PPSH_W].any(0))
    s_ = height_px / (PPSH_HUD_Y - rows[0])
    w, h = mask.shape[1], PPSH_HUD_Y
    img = Image.fromarray(mask[:h].astype(np.float32), "F")
    nw, nh = max(1, round(w * s_)), max(1, round(h * s_))
    small = np.asarray(img.resize((nw, nh), Image.Resampling.BOX)) >= COVER
    out = np.zeros((hs.VIEW_H, SCREEN_W), bool)
    ox = round(PPSH_CENTRE_X - (cols[0] + cols[-1]) / 2 * nw / w)
    oy = hs.VIEW_H - nh
    ys, xs = np.nonzero(small)
    ys, xs = ys + oy, xs + ox
    ok = (ys >= 0) & (ys < hs.VIEW_H) & (xs >= 0) & (xs < SCREEN_W)
    out[ys[ok], xs[ok]] = True
    return out


def build_ppsh_silhouettes(stamp: str, out_dir: Path = OUT_DIR / "ppsh") -> Path:
    mask = ppsh_mask()
    base_h = ppsh_height_above_bar()
    y_top = 40                                   # screen rows shown: 40..168 (the view above the bar)
    tw, th = 2 * SCREEN_W, 2 * (hs.VIEW_H - y_top) + 8
    f = hs.font(14)
    sheet = Image.new("RGBA", (len(PPSH_SIZES) * (tw + 10) + 10, th + 30), (0, 0, 0, 0))
    d = ImageDraw.Draw(sheet)
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, k in enumerate(PPSH_SIZES):
        scr = ppsh_screen(mask, base_h * k)
        rgba = np.zeros(scr.shape + (4,), np.uint8)
        rgba[scr] = SIL_INK
        tile = np.asarray(Image.fromarray(rgba[y_top:], "RGBA").resize((tw, th - 8), Image.Resampling.NEAREST))
        Image.fromarray(tile, "RGBA").save(out_dir / f"PPSh_x{k}.png")
        ox = 10 + i * (tw + 10)
        sheet.alpha_composite(Image.fromarray(tile, "RGBA"), (ox, 5))
        for yy in (hs.VIEW_H, tt33_top()):
            d.line([(ox, 5 + 2 * (yy - y_top) - (1 if yy == hs.VIEW_H else 0)),
                    (ox + tw, 5 + 2 * (yy - y_top) - (1 if yy == hs.VIEW_H else 0))], fill=SIL_LINE, width=1)
        cols = np.flatnonzero(scr.any(0))
        d.text((ox, th + 8), f"PPSh x{k} ({PPSH_REF_LUMP} height {base_h} px x{k}; x {cols[0]}-{cols[-1] + 1})",
               font=f, fill=(128, 128, 128, 255))
    path = PREVIEW_DIR / f"{stamp}_{PPSH_SLUG}.png"
    sheet.save(path, optimize=True)
    return path


def build_all(out_dir: Path | None = OUT_DIR, cache: dict | None = None) -> dict:
    """Every cell; written with grAb to out_dir (None: not written)."""
    cache = {} if cache is None else cache
    cells = {c.key: build_cell(c, cache) for c in CELLS}
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        meta = {"_source": "tools/art/hand_ref.py", "_tt33_palm_px": cache["palm"], "_tt33_top": cache["top"]}
        for k, c in cells.items():
            hs.write_sprite(out_dir / f"{k}_SDAXA0.png", c["sprite"], c["offsets"])
            cl = c["cell"]
            meta[k] = {"ref": cl.ref, "file": c["spec"].file, "tones": cl.tones, "size": cl.size,
                       "grip": list(c["grip"]), "scale": round(c["scale"], 4), "palm_px": c["palm_px"],
                       "tone_colours": c["hand"]["tones"],
                       "verdict": list(VERDICTS.get(k, ("pass", "")))} | c["metrics"]
        (out_dir / "metrics.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return cells


def main() -> None:
    sil = {"silhouettes": build_silhouettes, "silhouette-final": build_silhouette_final,
           "silhouette-straight": build_silhouette_straight, "ppsh": build_ppsh_silhouettes}
    if len(sys.argv) > 1 and sys.argv[1] in sil:
        fn = sil[sys.argv[1]]
        print("wrote", fn(datetime.now().strftime("%Y-%m-%d_%H%M")))
        return
    stamp = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d_%H%M")
    cache: dict = {}
    cells = build_all(OUT_DIR, cache)
    for k, c in cells.items():
        print(k, json.dumps(c["metrics"]))
    for p in build_sheet(cells, stamp, cache):
        print("wrote", p)


if __name__ == "__main__":
    main()
