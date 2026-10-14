"""F4 / D48 — the sergeant's hand DRAWN IN 2D, the classic way, over our
rendered weapons. A trial against the 3D capsule hand of gen_weapon.py.

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_hands_2d.py            (Windows)
    .venv/bin/python tools/art/gen_hands_2d.py                    (macOS)
    ... --stamp 2026-10-14_1100      fixes the sheet's timestamp

Why. D48: the CEO approved hand style E (brown leather glove, green field
sleeve, the telnyashka at the wrist) but finds the 3D hand "deforme, no
humana": capsules for fingers read as sausages, the fist as a pile of
blobs. A second agent tries a more anatomical 3D hand; this module tries
the opposite road, the one Doom, Wolfenstein and Blood took: a hand DRAWN
as flat 2D shapes at the native 320x200, banded shading, clean contours.

How. Nothing is painted freehand: every shape is a polygon, an ellipse or a
round-ended bar authored in code, in a LOCAL 2D frame of the hand
(centimetres): `a` runs up the held shaft towards the business end, `w`
runs across it towards the wrist. One drawing, a fist in three-quarter
view (four stacked finger bars, the knuckle ridge, the back of the glove
with its seams, the thumb across the index), is laid on each grip of each
weapon frame by a 2D affine map. The map comes from the weapon's own pose:
the TT-33, PPSh-41 and ice axe are re-rendered by gen_weapon WITHOUT their
hand (draw_grip is swapped for a recorder for the length of one call, the
file is never edited), and each recorded grip gives its screen point, the
shaft's screen direction, the wrist side and the scale (px per cm at that
depth). The forearm (glove cuff, telnyashka, sleeve hem, sleeve) is a run
of quads from the wrist towards the projected elbow.

Shading is 2D: each shape carries a simple normal field (a bar is a
cylinder across its axis, the back of the hand a low dome), lit by the same
key light as gen_weapon and cut into only HAND_BANDS flat bands, so the
hand reads as a few deliberate tones, the way a sprite artist would block
it. Shapes are rasterised at SS sub-pixels and reduced by majority vote
(no anti-aliasing); then two pixel passes: a crease where a shape sits on
top of another (finger over finger, thumb over index) and a dark outline
where the hand meets the weapon or the air. Colours are gen_weapon's own
style-E materials (palette v1), so every pixel is a palette.json colour.

Freedoom. iwads/freedoom2.wad (BSD-3) is read ONLY to place Freedoom's
PISGA0, CHGGA0 and PUNGA0 beside ours on the sheet, as gen_weapon does; no
Freedoom pixel enters a sprite (the tests check the palette, which
Freedoom's skin tones are not in).

Outputs (work/ is gitignored):
    work/art/weapons_2d/<weapon>/<LUMP>.png   held frames, same lump names
                                              and grAb convention as work/art/weapons/
    work/art/weapons_2d/metrics.json
    docs/art/previews/<stamp>_F4_hand-2d-pixel.png   the comparison sheet
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import gen_weapon as gw  # noqa: E402

PROJECT_ROOT = gw.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "weapons_2d"
PREVIEW_DIR = gw.PREVIEW_DIR
MAP01_CAPTURE = PROJECT_ROOT / "docs" / "qa" / "evidence" / "2026-10-13_2310_F4_draft-overlay-in-map01.png"

STYLE_KEY = "E"                 # D48: the approved style
SS = 4                          # sub-pixels per pixel side
COVER_MIN = 6                   # of SS*SS sub-pixels: below this, transparent
HAND_BANDS = 4                  # light bands: fewer than the 3D hand's 6, on purpose
AMBIENT = 0.32
LAMBERT_MID = 0.55
CREASE_STEPS = 2                # ramp steps darker where a shape sits on another
RIM_STEPS = 3                   # ramp steps darker on the hand's outline
HAND_SCALE = 1.0                # the drawing, against true size at the grip's depth
HAND_MIN_PX_PER_CM = 5.0        # a far hand is drawn no smaller than this (Doom and Blood exaggerate)
FORESHORTEN_MIN = 0.78          # a shaft into the screen still shows a whole fist

# Materials: gen_weapon's own, style E (palette v1 ramps).
GLOVE, SLEEVE, TEL_W, TEL_B, BUTTON = "glove_brown", "sleeve_field", "tel_white", "tel_blue", "button"
MAT_NAMES = (GLOVE, SLEEVE, TEL_W, TEL_B, BUTTON)
MAT_IDX = {m: i for i, m in enumerate(MAT_NAMES)}


# ============================================================ the drawing
# Local frame, centimetres. a: up the shaft (towards the head, the muzzle);
# w: across it, towards the wrist. The shaft's axis is w = 0.
# One finger: (a of its centre, width, how far its folded front reaches past
# the shaft's far edge). The middle finger stands proudest, as in a real fist.
FINGERS = (
    ("index", 2.95, 2.25, 0.75),
    ("middle", 0.95, 2.3, 1.05),
    ("ring", -1.05, 2.2, 0.85),
    ("little", -2.85, 1.85, 0.45),
)
KNUCKLE_W = 1.75                # the knuckle ridge (MCP joints), w
KNUCKLE_R = (0.95, 0.7)         # share of the finger's half width along a; cm along w
FINGER_TIP = 0.62               # the folded front's corner radius, share of the half width
PIP_LINE = 0.95                 # cm behind the front: the joint's crease line
BACK_POLY = (                   # the back of the glove, knuckles to wrist
    (4.0, 1.6), (2.0, 1.3), (-0.2, 1.35), (-2.2, 1.45), (-3.9, 1.9), (-4.3, 3.0),
    (-4.1, 4.6), (-3.3, 6.6), (-2.5, 8.6), (1.9, 8.6), (3.2, 6.4), (4.4, 4.2), (4.6, 2.6),
)
BACK_DOME = ((0.3, 4.2), 6.5)   # dome centre (a, w) and radius: the shading field
SEAMS = (((1.9, 3.0), (1.6, 6.6)), ((-0.15, 3.0), (-0.3, 6.8)), ((-2.1, 3.0), (-1.9, 6.4)))
SEAM_PX = 0.55                  # half width of a seam line, px
SEAM_DV = 0.22
WRIST = (-0.3, 8.0)             # where the forearm starts
THENAR = ((4.1, 4.0), (1.5, 2.1))       # the thumb's pad: centre, semi-axes (a, w)
THUMB_FRONT = (((4.7, 3.4), (3.9, 0.6), 1.2, 1.12), ((3.9, 0.6), (1.4, -1.2), 1.12, 0.98))
THUMB_BEHIND = (((4.2, 3.0), (4.6, 0.2), 1.15, 1.05), ((4.6, 0.2), (4.1, -1.9), 1.05, 0.95))
TRIGGER_INDEX = (((3.0, 1.9), (3.5, -2.3), 1.0, 0.95), ((3.5, -2.3), (3.0, -3.8), 0.95, 0.85))
SUPPORT_REACH = -1.1            # support hand: fingertips end on the near face, cm

# The forearm: (name, from cm, to cm, half width at start, at end, material)
# measured from the wrist towards the elbow.
FOREARM = (
    ("sleeve", 8.4, 60.0, 4.15, 5.6, SLEEVE),
    ("hem", 5.9, 8.9, 4.35, 4.4, SLEEVE),
    ("tel", 2.5, 6.4, 3.35, 3.6, TEL_W),
    ("cuff", -0.6, 2.9, 2.6, 3.3, GLOVE),
)
FOREARM_FROM_HAND = 0.3          # the forearm leaves along this much of the hand's own axis, the rest towards the elbow
TEL_STRIPE = 0.82               # cm per stripe (white, blue, white...)
CUFF_STITCH = 2.3               # cm from the wrist: the cuff's stitched edge
BUTTON_AT = (7.3, 0.78)         # cm along, share of the half width (outer side)


@dataclass(frozen=True)
class GripDesign:
    """How one grip is drawn: which thumb, trigger finger, finger reach."""
    thumb: str = "front"        # "front" | "behind" (only where the weapon is not)
    trigger: bool = False
    reach: float = 0.0          # added to every finger's reach, cm


# Per weapon, one design per draw_grip call, in call order.
DESIGNS = {
    "tt33": (GripDesign(thumb="behind", trigger=True),),
    "ppsh": (GripDesign(thumb="front", trigger=True), GripDesign(thumb="behind", reach=SUPPORT_REACH)),
    "axe": (GripDesign(thumb="front"),),
}


# ========================================================== the recorder
@dataclass
class Grip:
    """One grip as the 3D pose places it, reduced to the screen."""
    at: np.ndarray              # screen px of the grip point (the shaft axis)
    ea: np.ndarray              # screen unit vector up the shaft
    ew: np.ndarray              # screen unit vector across it, to the wrist
    fore: np.ndarray            # screen unit vector wrist -> elbow
    s: float                    # px per cm at the grip's depth
    fa: float                   # foreshortening along the shaft, 0..1
    fw: float                   # and across it
    shaft_r: float              # cm


def _unit2(v) -> np.ndarray:
    v = np.asarray(v, np.float64)
    n = float(np.hypot(*v))
    return v / n if n > 1e-9 else np.array([1.0, 0.0])


def grip_from_pose(rig, g, axis, elbow, shaft_r) -> Grip:
    g = np.asarray(g, np.float64)
    A = gw.unit(axis)
    x, y, s = rig.project(g)
    at = np.array([x, y])
    pa = np.array(rig.project(g + A * 3.0)[:2])
    to_el = gw.unit(np.asarray(elbow, np.float64) - g)
    pe = np.array(rig.project(g + to_el * 6.0)[:2])
    ea = _unit2(pa - at)
    d_el = pe - at
    ew = _unit2(d_el - np.dot(d_el, ea) * ea)
    wrist3 = g + to_el * 8.0
    pw = np.array(rig.project(wrist3)[:2])
    pf = np.array(rig.project(wrist3 + to_el * 20.0)[:2])
    fa = float(np.clip(np.hypot(*(pa - at)) / (3.0 * s), FORESHORTEN_MIN, 1.0))
    fw = float(np.clip(np.hypot(*d_el) / (6.0 * s), FORESHORTEN_MIN, 1.0))
    return Grip(at, ea, ew, _unit2(pf - pw), float(s), fa, fw, float(shaft_r))


@contextlib.contextmanager
def handless():
    """For the length of the block, gen_weapon draws no hand: draw_grip
    records where the hand would be and returns the keys callers read."""
    calls: list[Grip] = []
    original = gw.draw_grip

    def record(rig, style, g, axis, elbow, shaft_r, side="right", trigger=False, forearm=True):
        calls.append(grip_from_pose(rig, g, axis, elbow, shaft_r))
        A = gw.unit(axis)
        return {"wrist": np.asarray(g, np.float64), "K": A, "A": A, "Dw": A, "tips": []}

    gw.draw_grip = record
    try:
        yield calls
    finally:
        gw.draw_grip = original


# ============================================================ the painter
@dataclass
class Shape:
    group: int
    behind: bool


class Painter2D:
    """Sub-pixel canvas of shape ids, materials and values over gen_weapon's
    authoring canvas (screen px, x from -64, y from 0). Later shapes cover
    earlier ones; nothing is blended."""

    def __init__(self, x0=gw.CANVAS_X0, y0=gw.CANVAS_Y0, w=gw.CANVAS_W, h=gw.CANVAS_H, ss=SS):
        self.x0, self.y0, self.w, self.h, self.ss = x0, y0, w, h, ss
        shape = (h * ss, w * ss)
        self.sid = np.zeros(shape, np.int32)
        self.mat = np.full(shape, -1, np.int16)
        self.val = np.zeros(shape)
        self.shapes: list[Shape] = [Shape(0, False)]
        self.group = 0

    def new_group(self) -> int:
        self.group += 1
        return self.group

    def _window(self, xmin, ymin, xmax, ymax):
        ss = self.ss
        i0 = max(0, int(np.floor((ymin - self.y0) * ss)))
        i1 = min(self.h * ss, int(np.ceil((ymax - self.y0) * ss)) + 1)
        j0 = max(0, int(np.floor((xmin - self.x0) * ss)))
        j1 = min(self.w * ss, int(np.ceil((xmax - self.x0) * ss)) + 1)
        if i0 >= i1 or j0 >= j1:
            return None
        ys = self.y0 + (np.arange(i0, i1) + 0.5) / ss
        xs = self.x0 + (np.arange(j0, j1) + 0.5) / ss
        Y, X = np.meshgrid(ys, xs, indexing="ij")
        return (slice(i0, i1), slice(j0, j1)), X, Y, (self.x0 + j0 / ss, self.y0 + i0 / ss)

    @staticmethod
    def light(nx, ny, nz, base, gain) -> np.ndarray:
        L = gw.LIGHT
        lam = AMBIENT + (1.0 - AMBIENT) * np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0.0, 1.0)
        lam = np.floor(lam * HAND_BANDS + 0.5) / HAND_BANDS
        return base + gain * (lam - LAMBERT_MID)

    def _commit(self, sl, inside, val, mat, behind=False, group=None) -> None:
        self.shapes.append(Shape(self.group if group is None else group, behind))
        k = len(self.shapes) - 1
        self.sid[sl][inside] = k
        self.val[sl][inside] = np.clip(val[inside], 0.0, 1.0)
        m = np.broadcast_to(np.asarray(mat, np.int16), inside.shape)
        self.mat[sl][inside] = m[inside]

    @staticmethod
    def _lines(X, Y, val, lines):
        for p0, p1, hw, dv in lines or ():
            p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
            d = p1 - p0
            L2 = float(d @ d)
            t = np.clip(((X - p0[0]) * d[0] + (Y - p0[1]) * d[1]) / max(L2, 1e-9), 0, 1)
            dist = np.hypot(X - (p0[0] + t * d[0]), Y - (p0[1] + t * d[1]))
            val = np.where(dist <= hw, val - dv, val)
        return val

    # --- primitives, screen px
    def bar(self, p0, p1, r0, r1, material, base, gain, behind=False, lines=None) -> None:
        """A round-ended bar (a finger, a thumb): lit as a cylinder across
        its axis, as a sphere past its ends."""
        p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
        R = max(r0, r1)
        win = self._window(min(p0[0], p1[0]) - R, min(p0[1], p1[1]) - R,
                           max(p0[0], p1[0]) + R, max(p0[1], p1[1]) + R)
        if win is None:
            return
        sl, X, Y, _ = win
        d = p1 - p0
        L2 = float(d @ d)
        t = np.clip(((X - p0[0]) * d[0] + (Y - p0[1]) * d[1]) / max(L2, 1e-9), 0, 1)
        dx, dy = X - (p0[0] + t * d[0]), Y - (p0[1] + t * d[1])
        Rt = r0 + (r1 - r0) * t
        rho2 = (dx * dx + dy * dy) / (Rt * Rt)
        inside = rho2 <= 1.0
        nz = -np.sqrt(np.clip(1.0 - rho2, 0, None))
        val = self.light(dx / Rt, dy / Rt, nz, base, gain)
        val = self._lines(X, Y, val, lines)
        self._commit(sl, inside, val, MAT_IDX[material], behind)

    def ellipse(self, c, e1, e2, material, base, gain, behind=False, group=None) -> None:
        """An ellipse with semi-axis VECTORS e1, e2 (px), lit as a dome."""
        c = np.asarray(c, np.float64)
        M = np.column_stack([e1, e2])
        Minv = np.linalg.inv(M)
        ex = float(np.hypot(e1[0], e2[0]))
        ey = float(np.hypot(e1[1], e2[1]))
        win = self._window(c[0] - ex, c[1] - ey, c[0] + ex, c[1] + ey)
        if win is None:
            return
        sl, X, Y, _ = win
        u = Minv[0, 0] * (X - c[0]) + Minv[0, 1] * (Y - c[1])
        v = Minv[1, 0] * (X - c[0]) + Minv[1, 1] * (Y - c[1])
        rho2 = u * u + v * v
        inside = rho2 <= 1.0
        a1, a2 = _unit2(e1), _unit2(e2)
        nx, ny = u * a1[0] + v * a2[0], u * a1[1] + v * a2[1]
        nz = -np.sqrt(np.clip(1.0 - rho2, 0, None))
        self._commit(sl, inside, self.light(nx, ny, nz, base, gain), MAT_IDX[material], behind, group)

    def poly(self, pts, material, base, gain, field, behind=False, lines=None, mat_fn=None) -> None:
        """A polygon. field: ("dome", centre, radius) or ("tube", p0, dir,
        half_width_fn) gives its normals. mat_fn(X, Y) -> material ids
        overrides the material per sub-pixel (the telnyashka's stripes)."""
        pts = [tuple(map(float, p)) for p in pts]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        win = self._window(min(xs), min(ys), max(xs), max(ys))
        if win is None:
            return
        sl, X, Y, origin = win
        img = Image.new("L", (X.shape[1], X.shape[0]), 0)
        ox, oy = origin
        ImageDraw.Draw(img).polygon([((x - ox) * self.ss, (y - oy) * self.ss) for x, y in pts], fill=255)
        inside = np.asarray(img) > 0
        if field[0] == "dome":
            _, c, R = field
            nx, ny = (X - c[0]) / R, (Y - c[1]) / R
            rho2 = np.clip(nx * nx + ny * ny, 0, 0.92)
            k = np.sqrt(rho2 / np.maximum(nx * nx + ny * ny, 1e-9))
            nx, ny = nx * k, ny * k
            nz = -np.sqrt(1.0 - rho2)
        else:
            _, p0, d, hw_fn = field
            n = np.array([-d[1], d[0]])
            along = (X - p0[0]) * d[0] + (Y - p0[1]) * d[1]
            across = ((X - p0[0]) * n[0] + (Y - p0[1]) * n[1]) / hw_fn(along)
            across = np.clip(across, -0.97, 0.97)
            nx, ny = across * n[0], across * n[1]
            nz = -np.sqrt(1.0 - across * across)
        val = self._lines(X, Y, self.light(nx, ny, nz, base, gain), lines)
        mat = MAT_IDX[material] if mat_fn is None else mat_fn(X, Y)
        self._commit(sl, inside, val, mat, behind)

    # --- reduction and the pixel passes
    def reduce(self):
        """Majority vote per SSxSS block, ties to the later shape. Returns
        shape id (0 = empty), material id and value at 1x."""
        ss, h, w = self.ss, self.h, self.w
        blk = lambda a: a.reshape(h, ss, w, ss).transpose(0, 2, 1, 3).reshape(h, w, ss * ss)
        sid, mat, val = blk(self.sid), blk(self.mat), blk(self.val)
        eq = (sid[..., :, None] == sid[..., None, :]) & (sid[..., :, None] > 0)
        counts = eq.sum(-1)
        score = counts * 100000 + sid           # ties: the later (front) shape
        k = np.argmax(score, -1)
        take = lambda a: np.take_along_axis(a, k[..., None], -1)[..., 0]
        win = take(sid)
        covered = (sid > 0).sum(-1)
        sel = sid == win[..., None]
        out_val = (val * sel).sum(-1) / np.maximum(sel.sum(-1), 1)
        ok = (covered >= COVER_MIN) & (win > 0)
        return np.where(ok, win, 0), np.where(ok, take(mat), -1).astype(np.int16), out_val

    def to_rgba(self, under: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
        """The hand at 1x, RGBA over the canvas, after the crease and rim
        passes. `under` is the weapon's RGBA on the same canvas: a shape
        flagged `behind` shows only where the weapon is transparent.
        Returns (rgba, hand mask)."""
        sid, mat, val = self.reduce()
        h, w = sid.shape
        behind = np.array([s.behind for s in self.shapes])[sid]
        if under is not None:
            sid = np.where(behind & (under[..., 3] > 0), 0, sid)
            mat = np.where(sid > 0, mat, -1).astype(np.int16)
        group = np.array([s.group for s in self.shapes])[sid]
        opaque = sid > 0
        idx = np.zeros((h, w), np.int16)
        cols = [gw.MATERIALS[m].colours() for m in MAT_NAMES]
        for i, cl in enumerate(cols):
            sel = mat == i
            idx[sel] = np.rint(val[sel] * (len(cl) - 1)).astype(np.int16)
        dark = np.zeros((h, w), np.int16)
        P_sid, P_grp = np.pad(sid, 1), np.pad(group, 1)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nb_sid = P_sid[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
            nb_grp = P_grp[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
            crease = opaque & (nb_sid > 0) & (nb_grp != group) & (nb_sid > sid)
            rim = opaque & (nb_sid == 0)
            dark = np.maximum(dark, np.where(crease, CREASE_STEPS, 0))
            dark = np.maximum(dark, np.where(rim, RIM_STEPS, 0))
        idx = np.maximum(idx - dark, 0)
        rgba = np.zeros((h, w, 4), np.uint8)
        for i, cl in enumerate(cols):
            sel = mat == i
            arr = np.array(cl, np.uint8)
            rgba[sel, :3] = arr[np.clip(idx[sel], 0, len(arr) - 1)]
        rgba[opaque, 3] = 255
        return rgba, opaque


# ========================================================== the hand itself
class HandMap:
    """Local (a, w) cm -> screen px for one grip."""

    def __init__(self, grip: Grip):
        self.g = grip
        k = max(grip.s, HAND_MIN_PX_PER_CM) * HAND_SCALE
        self.A = grip.ea * k * grip.fa
        self.W = grip.ew * k * grip.fw
        self.k = k * (grip.fa + grip.fw) / 2      # px per cm for radii

    def __call__(self, a, w) -> np.ndarray:
        return self.g.at + self.A * a + self.W * w

    def vec(self, a, w) -> np.ndarray:
        return self.A * a + self.W * w


def draw_forearm(p: Painter2D, m: HandMap) -> None:
    """Sleeve, hem, telnyashka and glove cuff, from the elbow in to the wrist."""
    g = m.g
    start = m(*WRIST)
    d = _unit2(FOREARM_FROM_HAND * g.ew + (1.0 - FOREARM_FROM_HAND) * g.fore)
    n = np.array([-d[1], d[0]])
    k = m.k

    def quad(t0, t1, hw0, hw1):
        a, b = start + d * t0 * k, start + d * t1 * k
        return [a + n * hw0 * k, b + n * hw1 * k, b - n * hw1 * k, a - n * hw0 * k]

    for name, t0, t1, hw0, hw1, material in FOREARM:
        hw_fn = (lambda t0=t0, t1=t1, hw0=hw0, hw1=hw1:
                 (lambda along: np.maximum((hw0 + (hw1 - hw0) * np.clip((along / k - t0) / (t1 - t0), 0, 1)) * k, 1e-6)))()
        field = ("tube", start, d, hw_fn)
        p.new_group()
        if name == "tel":
            def stripes(X, Y):
                along = ((X - start[0]) * d[0] + (Y - start[1]) * d[1]) / k
                odd = (np.floor((along - t0) / TEL_STRIPE) % 2) == 1
                return np.where(odd, MAT_IDX[TEL_B], MAT_IDX[TEL_W]).astype(np.int16)
            p.poly(quad(t0, t1, hw0, hw1), TEL_W, 0.62, 0.7, field, mat_fn=stripes)
        elif name == "cuff":
            a0 = start + d * CUFF_STITCH * k
            p.poly(quad(t0, t1, hw0, hw1), GLOVE, 0.54, 0.85, field,
                   lines=[(a0 + n * 3.4 * k, a0 - n * 3.4 * k, 0.5, 0.2)])
        elif name == "hem":
            p.poly(quad(t0, t1, hw0, hw1), SLEEVE, 0.6, 0.85, field)
        else:
            p.poly(quad(t0, t1, hw0, hw1), SLEEVE, 0.55, 0.85, field)
    # the hem's button, on the outer (lit) side
    side = 1.0 if (n @ np.array(gw.LIGHT[:2])) > 0 else -1.0
    c = start + d * BUTTON_AT[0] * k + n * side * BUTTON_AT[1] * 4.35 * k
    r = max(1.2, 0.45 * k)
    p.ellipse(c, d * r, n * r, BUTTON, 0.55, 0.8)


def finger_block(p: Painter2D, m: HandMap, ac: float, r: float, back: float, front: float,
                 base: float, gain: float) -> None:
    """One folded finger seen from outside: a bar of half width r (cm) from
    `back` to `front` (w), square at the back (the knuckle covers it) and
    rounded at the front corners (the middle joint), lit as a cylinder
    across its width, with the joint's crease line behind the front."""
    rc = FINGER_TIP * r
    pts = [(ac + r, back)]
    for i in range(7):                               # front corners, +a side then -a side
        t = np.deg2rad(90.0 * i / 6)
        pts.append((ac + r - rc + rc * np.cos(t), front + rc - rc * np.sin(t)))
    for i in range(7):
        t = np.deg2rad(90.0 + 90.0 * i / 6)
        pts.append((ac - r + rc + rc * np.cos(t), front + rc - rc * np.sin(t)))
    pts.append((ac - r, back))
    k = m.k
    p0 = m(ac, back)
    d = _unit2(m(ac, front) - p0)
    hw = r * float(np.hypot(*m.A))           # px: the finger runs along w, its width is along a
    crease = [(m(ac + r * 0.8, front + PIP_LINE), m(ac - r * 0.8, front + PIP_LINE), 0.5, 0.14)]
    p.poly([m(a, w) for a, w in pts], GLOVE, base, gain,
           ("tube", p0, d, lambda along, hw=hw: np.full_like(along, hw)), lines=crease)


def draw_fist(p: Painter2D, m: HandMap, design: GripDesign) -> None:
    """The gloved hand round the shaft: back of the hand, the four folded
    fingers (or three and the trigger finger), the knuckle ridge, the thumb."""
    g = m.g
    k = m.k
    base, gain = 0.62, 0.85
    far = -(g.shaft_r + design.reach)            # the far edge of the shaft, w
    # thumb behind: drawn first, then hidden wherever the weapon is
    if design.thumb == "behind":
        p.new_group()
        for (a0, w0), (a1, w1), r0, r1 in THUMB_BEHIND:
            p.bar(m(a0, w0), m(a1, w1 + (far + g.shaft_r)), r0 * k, r1 * k, GLOVE, base, gain, behind=True)
    # the back of the glove, with its three seams and the wrist crease
    p.new_group()
    (ca, cw), R = BACK_DOME
    seams = [(m(*s0), m(*s1), SEAM_PX, SEAM_DV) for s0, s1 in SEAMS]
    p.poly([m(a, w) for a, w in BACK_POLY], GLOVE, base, gain, ("dome", m(ca, cw), R * k), lines=seams)
    # the knuckle ridge, part of the back: the fingers' roots overlap it
    fingers = list(FINGERS)
    back_group = p.group
    for name, ac, width, reach in fingers:
        if design.trigger and name == "index":
            continue
        p.ellipse(m(ac, KNUCKLE_W), m.vec(KNUCKLE_R[0] * width / 2, 0), m.vec(0, KNUCKLE_R[1]),
                  GLOVE, base + 0.08, gain, group=back_group)
    # the fingers, little first: each sits on the one below it
    for name, ac, width, reach in reversed(fingers):
        p.new_group()
        r = width / 2
        front = far - reach
        if design.trigger and name == "index":
            for (a0, w0), (a1, w1), r0, r1 in TRIGGER_INDEX:
                p.bar(m(a0, w0), m(a1, w1), r0 * k, r1 * k, GLOVE, base, gain)
            continue
        if design.reach < 0:
            front = far - reach * 0.4
        finger_block(p, m, ac, r, KNUCKLE_W + 0.4, front, base, gain)
    # the thumb, over the index
    if design.thumb == "front":
        p.new_group()
        (ta, tw), (sa, sw) = THENAR
        p.ellipse(m(ta, tw), m.vec(sa, 0), m.vec(0, sw), GLOVE, base, gain)
        for (a0, w0), (a1, w1), r0, r1 in THUMB_FRONT:
            p.bar(m(a0, w0), m(a1, w1), r0 * k, r1 * k, GLOVE, base + 0.08, gain)


def draw_hand(p: Painter2D, grip: Grip, design: GripDesign) -> None:
    m = HandMap(grip)
    draw_forearm(p, m)
    draw_fist(p, m, design)


# ================================================================ frames
WEAPONS = {
    # key: (sprite, poses, render function, design key, label)
    "tt33": ("SDTT", gw.TT_POSES, lambda st, pose: gw.render_tt33_frame(st, pose)[0], "tt33", "TT"),
    "ppsh": ("SDPP", gw.PPSH_POSES, lambda st, pose: gw.render_ppsh_frame(st, pose)[0], "ppsh", "PP"),
    "ice_axe": ("SDAX", gw.AXE_POSES, gw.render_axe_frame, "axe", "AX"),
}


def canvas_rgba(frame: gw.Frame) -> np.ndarray:
    """A HUD frame placed on gen_weapon's authoring canvas."""
    out = np.zeros((gw.CANVAS_H, gw.CANVAS_W, 4), np.uint8)
    h, w = frame.rgba.shape[:2]
    x, y = frame.left - gw.CANVAS_X0, frame.top - gw.CANVAS_Y0
    out[y:y + h, x:x + w] = frame.rgba
    return out


def crop_frame(rgba: np.ndarray) -> gw.Frame:
    a = rgba[..., 3] > 0
    ys, xs = np.nonzero(a)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    crop = rgba[y0:y1, x0:x1].copy()
    return gw.Frame(crop, np.zeros(crop.shape[:2], np.int16),
                    int(gw.CANVAS_X0 + x0), int(gw.CANVAS_Y0 + y0), True)


@dataclass
class Rendered:
    key: str                    # e.g. "TT-1"
    lump: str
    pose: str
    frame3d: gw.Frame
    frame2d: gw.Frame
    handless: gw.Frame
    hand_px: int = 0
    extra: dict = field(default_factory=dict)


def render_2d(weapon: str, pose) -> tuple[gw.Frame, gw.Frame, int]:
    """(the 2D-hand frame, the weapon without hand, hand pixel count)."""
    sprite, _, fn, dkey, _ = WEAPONS[weapon]
    style = gw.HAND[STYLE_KEY]
    with handless() as grips:
        bare = fn(style, pose)
    designs = DESIGNS[dkey]
    if len(grips) != len(designs):
        raise ValueError(f"{weapon}: {len(grips)} grips, {len(designs)} designs")
    under = canvas_rgba(bare)
    p = Painter2D()
    for grip, design in zip(grips, designs):
        draw_hand(p, grip, design)
    hand, mask = p.to_rgba(under)
    out = under.copy()
    out[mask] = hand[mask]
    return crop_frame(out), bare, int(mask.sum())


# A PROPOSAL, not a frame of the approved set: the TT-33's ready pose sits so
# low that its grip, and so the hand, is mostly under the screen's edge;
# Freedoom's pistol (PISGA0) shows the whole hand. Same pose raised.
TT_RAISE_CM = 4.0               # camera cm up: about 30 px at the grip's depth


def proposals() -> list[tuple[str, str, str, object]]:
    a = gw.TT_POSES[0]
    raised = gw.ArmsPose(a.frame, f"{a.name}, raised {TT_RAISE_CM:g} cm (proposal)",
                         (a.origin[0], a.origin[1] - TT_RAISE_CM, a.origin[2]), a.bore, a.up,
                         a.state, a.amount, wired=False)
    return [("tt33", "TT-1R", "SDTTA0_raised_proposed", raised)]


def render_all() -> list[Rendered]:
    style = gw.HAND[STYLE_KEY]
    rows = []
    for weapon, (sprite, poses, fn, _, label) in WEAPONS.items():
        for i, pose in enumerate(poses):
            f3 = fn(style, pose)
            f2, bare, n = render_2d(weapon, pose)
            rows.append(Rendered(f"{label}-{i + 1}", f"{sprite}{pose.frame}0", pose.name, f3, f2, bare, n,
                                 {"weapon": weapon}))
        for w, key, lump, pose in proposals():
            if w == weapon:
                f2, bare, n = render_2d(weapon, pose)
                rows.append(Rendered(key, lump, pose.name, fn(style, pose), f2, bare, n,
                                     {"weapon": weapon, "proposal": True}))
    return rows


# ================================================================= sheet
STATUSBAR_TOP_CAPTURE = 187     # px of 200: the capture's scaled status bar starts here
CAPTURE_TILES = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))   # same camera, weapons elsewhere
CAPTURE_TILE = (480, 300)
CAPTURE_AGREE = 24              # summed RGB distance under which two tiles agree
# Patches of the cleaned capture still holding a weapon or text: copy the
# mirror image across the (symmetric) room. (x0, y0, x1, y1) in tile px.
CAPTURE_MIRROR = ((255, 186, 380, 279), (0, 0, 150, 14))


def map01_backdrop() -> np.ndarray | None:
    """MAP01's dorm without a weapon, 320x200: six engine captures of the
    same view with different weapons (QA evidence, 2026-10-13 23:10),
    reduced per pixel to the value most of them agree on, so each weapon
    drops out; the few pixels no tile shows clean are mirrored."""
    if not MAP01_CAPTURE.is_file():
        return None
    im = np.asarray(Image.open(MAP01_CAPTURE).convert("RGB")).astype(np.int32)
    tw, th = CAPTURE_TILE
    tiles = np.stack([im[r * th:(r + 1) * th, c * tw:(c + 1) * tw] for r, c in CAPTURE_TILES])
    agree = (np.abs(tiles[:, None] - tiles[None]).sum(-1) < CAPTURE_AGREE).sum(1)
    k = np.argmax(agree, 0)
    clean = np.take_along_axis(tiles, k[None, ..., None], 0)[0]
    for x0, y0, x1, y1 in CAPTURE_MIRROR:
        clean[y0:y1, x0:x1] = clean[y0:y1, tw - x1:tw - x0][:, ::-1]
    small = Image.fromarray(clean.astype(np.uint8)).resize((gw.SCREEN_W, gw.SCREEN_H), Image.Resampling.BOX)
    return np.asarray(small)


def on_capture(frames, backdrop: np.ndarray) -> np.ndarray:
    """Frames over the capture, then the capture's status bar back on top,
    as the engine draws it."""
    scr = gw.on_screen(frames, backdrop, statusbar_line=False)
    scr[STATUSBAR_TOP_CAPTURE:] = backdrop[STATUSBAR_TOP_CAPTURE:]
    return scr


FREEDOOM_REFS = (("FD-1", "PISGA0", "pistol"), ("FD-2", "CHGGA0", "chaingun"), ("FD-3", "PUNGA0", "fist"),
                 ("FD-4", "PUNGC0", "punch"))

VERDICT = [
    "WHAT THIS IS. D48 trial, the road opposite the anatomical 3D hand: the same style E (brown glove, field "
    "sleeve, telnyashka) DRAWN as flat 2D shapes at 320x200 and laid on our rendered weapons, which are "
    "re-rendered by gen_weapon without their hand. Four light bands instead of six, a crease where a shape sits "
    "on another, a dark outline on the hand. Palette v1, no system font, nothing in assets/.",
    "HOW TO READ A ROW. Left to right: the current 3D hand at 2x, the 2D hand at 2x, then both at 1x, the size "
    "the game shows them. All over a MAP01 capture (the dorm, rebuilt without its weapon from six engine "
    "captures of the same view); the capture's own status bar is pasted back on top, as the engine draws it. "
    "Positions follow Doom's arithmetic and are NOT VERIFIED in GZDoom (D26).",
]


def build_sheet(rows: list[Rendered], stamp: str, verdict: list[str], preview_dir: Path = PREVIEW_DIR) -> Path:
    backdrop = map01_backdrop()
    if backdrop is None:
        backdrop = gw.view_backdrop()
    S = gw.Sheet(2040, "SOVIET DOOM  ·  F4  ·  THE HAND, DRAWN IN 2D  ·  TRIAL (D48)", stamp)
    for v in VERDICT:
        S.para(v)
    S.y += 8
    gap = 16
    x2d = S.pad + 640 + gap
    x1 = x2d + 640 + gap
    heads = ((S.pad, "3D HAND TODAY, 2X"), (x2d, "2D HAND, 2X"), (x1, "3D, 1X"), (x1 + 320 + gap, "2D, 1X"))
    for x, t in heads:
        S.label((x, S.y), t, S.gold)
    S.y += S.T.line_h() + 4
    for r in rows:
        S.label((S.pad, S.y), f"{r.key}   {r.lump}   {r.pose.upper()}", S.red)
        S.y += S.T.line_h() + 2
        s3 = on_capture([r.frame3d], backdrop)
        s2 = on_capture([r.frame2d], backdrop)
        S.paste(s3, (S.pad, S.y), 2)
        S.paste(s2, (x2d, S.y), 2)
        S.paste(s3, (x1, S.y), 1)
        S.paste(s2, (x1 + 320 + gap, S.y), 1)
        S.label((x1, S.y + 200 + 8), f"{r.key}  3D", S.dim)
        S.label((x1 + 320 + gap, S.y + 200 + 8), f"{r.key}  2D", S.dim)
        S.y += 400 + 14
    # Freedoom, for proportion and framing only
    S.label((S.pad, S.y), "REFERENCE: FREEDOOM 0.13.0 (BSD-3), HOW DOOM FRAMES A HAND. COMPARISON ONLY, NO PIXEL "
            "OF IT IS IN ANY SPRITE OF OURS. 2X AND 1X.", S.gold)
    S.y += S.T.line_h() + 4
    x = S.pad
    row_h = 0
    for key, lump, what in FREEDOOM_REFS:
        fd = gw.freedoom_sprite(lump)
        if fd is None:
            continue
        scr = on_capture([fd], backdrop)
        crop = scr[60:200, 60:300]
        w2, h2 = S.paste(crop, (x, S.y + S.T.line_h()), 2)
        S.label((x, S.y), f"{key}   {lump}   {what.upper()}", S.red)
        S.paste(crop, (x, S.y + S.T.line_h() + h2 + 6), 1)
        x += w2 + gap
        row_h = max(row_h, S.T.line_h() + h2 + 6 + crop.shape[0])
    S.y += row_h + 18
    S.label((S.pad, S.y), "SELF-ASSESSMENT", S.red)
    S.y += S.T.line_h() + 2
    for v in verdict:
        S.para(v)
    return S.save(preview_dir / f"{stamp}_F4_hand-2d-pixel.png")


SELF_ASSESSMENT = [
    "DOES IT READ HUMAN AT 1X? Mostly yes, and better than the 3D hand. Where the fist is on screen (AX-1 to "
    "AX-5, PP-1, PP-2, TT-1R) the eye finds the parts a hand is recognised by: four fingers as separate bars, the "
    "knuckle ridge, a thumb crossing the index, the glove's cuff, then the stripes and the sleeve. The 3D hand "
    "at the same size merges into one brown mass of rounded blobs, which is the CEO's complaint. What the 2D hand "
    "does NOT fix: in the approved TT-33 pose (TT-1 to TT-3) the grip, and so the hand, is mostly below the "
    "screen's edge, so either hand reads as a brown wedge under the pistol. TT-1R is the same pose raised 4 cm "
    "(a proposal, not a frame of the set): there the 2D hand reads plainly as a gloved hand with its finger on "
    "the trigger. And the PPSh-41's right hand sits off screen (its grip projects at y 278 of 200), so its 2D "
    "frames show the left hand only; the 3D frames show a sliver of the right.",
    "DOES IT FIT THE 3D WEAPONS? Reasonably at 1x, less at 2x. The hand uses the weapons' own key light and "
    "palette ramps, so it does not look pasted in; but it is flatter (four bands) and more strongly outlined "
    "than the rendered steel and wood, and at 2x that difference shows, most on the PPSh where the dark-edged "
    "fingers sit on a softly lit fore-end. A sprite artist would close the gap from the other side, by giving "
    "the weapons the same hard outline; that is a gen_weapon change and is not made here.",
    "ITS LIMITS. It is ONE drawing laid on each grip by a 2D map, so every frame shows the same side of the "
    "same fist: in the swing (AX-2 to AX-4) the wrist does not turn as a drawn animation would, and the forearm "
    "leaves at a compromise angle between the hand and the projected elbow. Per-frame drawings (an open hand, "
    "the fist seen from the knuckles) are the next step if this road is chosen. The MAP01 backdrop is rebuilt "
    "from six engine captures and still shows faint traces of the enemies near the door.",
    "HOW CLOSE TO BLOOD (the CEO's reference, style only, no Blood asset or pixel used). The hand language is "
    "there: big gloved hands, visible knuckles, a readable thumb, a cuff and a sleeve. The rest of the Blood "
    "feel is not, because it lives in the poses, not in the hand: here the weapons keep their approved poses, "
    "so there is one hand on the pistol and the axe, the PPSh's right hand is off screen, the weapon is not low "
    "in the frame and the recoil is the 3D one (a few px). Getting there means new poses and more frames in "
    "gen_weapon (both hands in shot, weapon lower, a bigger kick, the off hand moving in reloads and swings), "
    "drawn with this hand. Freedoom-pixel road: not recommended. Its hands are bare skin and posed for its own "
    "weapons, so they would need repainting into the glove and still would not fit our grips; licence-wise it "
    "is allowed (BSD-3: keep the copyright notice and credit the Freedoom project in LICENSES.md and the "
    "credits) but it buys little.",
]


def save_all(rows: list[Rendered], out_dir: Path = OUT_DIR) -> dict:
    metrics = {}
    for r in rows:
        weapon = r.extra["weapon"]
        gw.save_sprite(r.frame2d, out_dir / weapon / f"{r.lump}.png")
        metrics[r.key] = {"lump": r.lump, "weapon": weapon, "pose": r.pose,
                          "size": list(r.frame2d.rgba.shape[1::-1]), "offsets": list(r.frame2d.offsets()),
                          "hand_px": r.hand_px}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return metrics


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    ap.add_argument("--no-sheet", action="store_true", help="sprites only")
    args = ap.parse_args(argv)
    rows = render_all()
    metrics = save_all(rows)
    for k, m in metrics.items():
        print(k, m)
    if not args.no_sheet:
        path = build_sheet(rows, args.stamp, SELF_ASSESSMENT)
        print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
