"""The ice axe's held frame derived from the CEO's reference photos (N14 / N4
round 3): a sweep for review, no asset.

    python tools/art/hand_ref.py            # cells -> work/art/hand_ref/, sheet + HTML -> docs/art/previews/

Why: drawn hands failed the CEO again and again ("dedos como salchichas",
"el antebrazo un palo larguísimo"); what worked for likeness was deriving
from a source image (the Lenin and Stalin posters). The CEO made reference
images with Fooocus (SDXL) in work/art/reference/ ("orientativas"). Here
the hand, wrist and sleeve are taken from one of them, not redrawn:

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
4. the axe: our own (gen_weapon.draw_ice_axe_head, wood_ash shaft, the D40
   design) rendered along the photo's shaft axis, the head up the axis and
   farther (smaller), the shaft continuing below the fist; then the hand on
   top, so thumb and fingertips lie over the shaft and the shaft shows above
   and below the fist through the hole the photo's shaft left.

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
from dataclasses import dataclass, field
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
    note: str = ""


REFS = {
    "R1": RefSpec(
        "R1", "hand grabbing mirrored.png", "hand around the haft, thumb over the fingers (CEO's best)",
        lasso=((0, 402), (135, 370), (300, 335), (395, 302), (520, 185), (735, 185), (770, 260), (768, 520), (720, 560),
               (600, 560), (520, 640), (420, 790), (360, 896), (0, 896)),
        axis=((641.0, 180.0), (703.0, 500.0)), shaft_half=40.0, fist=(205.0, 470.0),
        palm=((700.0, 222.0), (745.0, 455.0)), seed=(500.0, 400.0), turn=32.0, sleeve_seed=(100.0, 600.0),
        note="first person, the right hand round a wooden haft, knuckles and thumb over the fingers, "
             "olive sleeve from the left"),
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
    with Image.open(REF_DIR / spec.file) as im:
        return np.asarray(im.convert("RGB"), np.float32) / 255.0


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
HEAD_Z = 115.0             # cm: the head, five times farther than the fist: smaller, a piece of shaft shows under it
HEAD_RISE = 1.1            # head top above the grip, in palm breadths (R1: 245 photo px over a 235 px palm)
HEAD_K = 1.1               # head scale (round 2's frame A)
HEAD_FLAT = 0.8            # the head's axis: depth part over screen part
WOOD_RAMP = "cream_yellow"  # gen_weapon's wood_ash material
FIST_SHADE = 5             # ramp steps darker: the shaft inside the fist, in the hand's shadow
SHAFT_BELOW_PX = 90.0      # px of shaft drawn below the grip, down the photo's axis (ends under the bar)
HEAD_SHAFT_K = 2.0         # the shaft under the head over the fist's radius: perspective alone makes a pencil
HEAD_ROLL = 30.0           # degrees: the head turned about the shaft, so the adze shows its face


def _gw():
    return hs._gw()


def render_axe(grip_xy, up, rise_px: float, shaft_half_px: float, head_z: float = None,
               flat: float = None, roll: float = None, k: float = None):
    """Our ice axe (D40 head, wood_ash shaft) along the screen direction
    `up` from the grip at grip_xy (weapon px, depth GRIP_Z); the head's top
    rise_px up that line at head_z, farther and so smaller. The shaft is
    shaft_half_px wide (half) at the fist, like the photo's, and runs on
    below the fist at the fist's depth, off the bottom of the view (Doom's
    grammar: drawn to read, not to measure). Returns gen_weapon's Frame."""
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
    P0 = gw.unit([A[1], -A[0], 0.0])                     # A turned 90 on screen: the pick to the left
    P = gw.unit(P0 * math.cos(math.radians(roll)) + np.cross(A, P0) * math.sin(math.radians(roll)))
    r_grip = shaft_half_px * GRIP_Z / gw.FOCAL
    r_head = r_grip * HEAD_SHAFT_K
    rig = gw.Rig()
    shaft_top = gw.draw_ice_axe_head(rig, top, A, P, k, r_head)
    rig.capsule(G, shaft_top - A * 3.0 * k, r_grip, r_head, "wood_ash", 0.55, 0.8)
    low = gw.screen_to_cam(gx - up[0] * SHAFT_BELOW_PX, gy - up[1] * SHAFT_BELOW_PX, GRIP_Z)
    rig.capsule(G, low, r_grip, r_grip, "wood_ash", 0.55, 0.8)
    return gw.finish(rig)


# ------------------------------------------------------------------ cells
@dataclass(frozen=True)
class Cell:
    key: str
    ref: str
    tones: int
    size: float               # palm breadth over the TT-33 hand's
    grip_x: float             # weapon px: the column the grip sits on
    why: str


CELLS = (
    Cell("C1", "R1", 4, 1.00, 200.0, "the base: R1, 4 skin tones, the TT-33's hand scale, centre-right"),
    Cell("C2", "R1", 4, 0.85, 200.0, "C1 at 85 %"),
    Cell("C3", "R1", 4, 1.15, 200.0, "C1 at 115 %"),
    Cell("C4", "R1", 3, 1.00, 214.0, "C1 with 3 tones, further right (the chainsaw's column)"),
    Cell("C5", "R2", 4, 1.00, 200.0, "R2: fist from behind, forearm from the bottom"),
    Cell("C6", "R3", 4, 1.00, 200.0, "R3: hand from below, thumb up"),
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
    """Colours of the wood_ash ramp (cream_yellow) moved `steps` darker;
    any other colour is left as it is."""
    ramp = np.array(artlib.ramp(WOOD_RAMP), np.uint8)
    out = cols.copy()
    for i, c in enumerate(cols):
        hit = np.flatnonzero((ramp == c).all(1))
        if hit.size:
            out[i] = ramp[max(0, int(hit[0]) - steps)]
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
    spec = REFS[cell.ref]
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
    rise = HEAD_RISE * palm_px
    target_top = cache["top"]               # status bar on

    def frame_at(gy: float):
        gxy = (cell.grip_x, gy)
        axe = render_axe(gxy, up, rise, shaft_half)
        hxy = (int(round(cell.grip_x - fl["grip"][0])), int(round(gy - fl["grip"][1])))
        rgba, off, axe_m = compose(axe, hand, hxy)
        return rgba, off, axe_m, hxy
    lo, hi = 100.0, 199.0                    # weapon px searched for the grip row
    for _ in range(14):
        mid = (lo + hi) / 2
        rgba, off, _, _ = frame_at(mid)
        if hs.measure(rgba, off)["top"] < target_top:
            lo = mid
        else:
            hi = mid
    gy = round((lo + hi) / 2, 2)
    rgba, off, axe_m, hxy = frame_at(gy)
    return {"cell": cell, "spec": spec, "sprite": rgba, "offsets": off, "axe_mask": axe_m,
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
    "C1": ("pass", "A right hand, not a drawing of one: back of the hand, the thumb closed over the top of the "
                   "shaft, the four knuckles curling round its right side, the shaft darker inside the fist and "
                   "showing above it (under the head) and below it (down to the bar). The sleeve is the photo's: "
                   "broad at the bottom left, narrowing to the wrist, no stick and no tube. Same visible skin as "
                   "the TT-33 hands (about 1015 px against 999) and the same top (56 px above the bar). At 1x the "
                   "fingers read as a row of knuckles; at 2x as fingers."),
    "C2": ("drop", "At 85 % the fingers shrink to two-pixel knobs that merge into one dark edge at 1x, and the head "
                   "looks big for the hand; 6 px of the photo's cut edge also show at the very bottom when the "
                   "status bar is off."),
    "C3": ("pass", "C1 at 115 %: the hand reads more (about 1230 skin px above the bar against the TT-33's 999), "
                   "fingers clearer; the frame is no taller (the top is held at the TT-33's), the extra size goes "
                   "into the fist and the wrist."),
    "C4": ("pass", "C1 with three skin tones (harder, flatter modelling, closer to Freedoom's chunky look) and the "
                   "grip 14 px further right, on the chainsaw's column. Same hand, so it passes for the same "
                   "reasons as C1; it is here to choose tones and column."),
    "C5": ("drop", "R2 seen from behind: the shaft runs beside the fist, not through it (the photo's fingers close "
                   "on the far side, behind the shaft), so nothing lies over the shaft but the thumb, which reads "
                   "as a spike; the hand reads as a mitten."),
    "C6": ("drop", "R3 from below: the photo's handle lies in front of the fingers, so the shaft covers them "
                   "instead of the fingers covering it; the thumb is a cone, and the photo's sleeve ends inside "
                   "the view (its cut edge shows on screen)."),
}
RECOMMENDED = "C1"

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
        f'<div class="tile"><img class="px" src="{png_uri(derivation(spec, cache[("seg", key)]))}">'
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
        ("What was taken from the references",
         "The CEO's Fooocus images, dimmed outside what was kept: hand and sleeve as segmented (sleeve tinted "
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
        "N14 / N4 round 3: the ice axe's held frame (ready), the hand <b>derived</b> from the CEO's reference "
        "images instead of drawn: segmented from the photo, turned and scaled to the TT-33 hands' scale, toned "
        "onto the same skin and sleeve ramps as the approved TT-33 hands (palette v2 flesh_pink, "
        "military_green), with our own ice axe (the D40 head, ash shaft) put through the fist: thumb and "
        "fingertips over the shaft, the shaft showing above and below the fist, darker inside it. Every frame "
        "stands as high as the TT-33 (56 px above the bar, D57). A sweep: pick a cell, or none; the swing "
        "frames follow from the chosen one. Nothing here is installed.")
    html_path = sheetlib.write_sheet(
        PREVIEW_DIR / f"{stamp}_F4_ice-axe-from-reference.html", lang="en",
        title="Ice axe from the CEO's references: held frame sweep (N14 / N4 round 3)",
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
    d.text((pad, 12), "Ice axe held frame from the CEO's references (N14 / N4 round 3): the cells that pass",
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
    png_path = PREVIEW_DIR / f"{stamp}_F4_ice-axe-from-reference.png"
    sheet.save(png_path, optimize=True)
    return html_path, png_path


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
    stamp = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d_%H%M")
    cache: dict = {}
    cells = build_all(OUT_DIR, cache)
    for k, c in cells.items():
        print(k, json.dumps(c["metrics"]))
    for p in build_sheet(cells, stamp, cache):
        print("wrote", p)


if __name__ == "__main__":
    main()
