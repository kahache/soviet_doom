"""F4 / D52 — the sergeant's hands DRAWN IN 2D, on the whole arsenal.

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_hands_2d.py            (Windows)
    .venv/bin/python tools/art/gen_hands_2d.py                    (macOS)
    ... --stamp 2026-10-14_1300      fixes the sheet's timestamp
    ... --no-sheet                   sprites only

Why. D48 approved hand style E (brown leather glove, green field sleeve, the
telnyashka at the wrist) but the 3D capsule hand read "deforme, no humana".
The 2D trial of 2026-10-14 11:05 (`..._F4_hand-2d-pixel.png`) won: D52, "Manos
1". D49 sets the animation reference: Blood (Monolith, 1997), STYLE ONLY, no
Blood asset or pixel: big readable hands, often both in shot, the weapon
low, an exaggerated kick, the off hand moving. D51 picks the hand Katyusha's
pass-3 variant B (six bare tubes in riveted bands).

How. Nothing is painted freehand: every shape is a polygon, an ellipse or a
round-ended bar authored in code, in a LOCAL 2D frame of the hand
(centimetres): `a` runs up the held shaft towards the business end, `w`
runs across it towards the wrist. The weapons are gen_weapon's own 3D
renders, re-rendered WITHOUT their hand (draw_grip is swapped for a recorder
for the length of one call; gen_weapon.py is never edited by this module),
and each recorded grip gives the screen point, the shaft's screen
direction, the wrist side and the scale. On each grip one DRAWING is laid by
a 2D affine map; which drawing, and how it is turned, is chosen PER FRAME
(GripDesign): the back of the fist, the fist seen from its fingers (palm
view: the fingers wrapped round the shaft and the thumb across them), the
back foreshortened (the wrist rolled, the knuckles to the eye), the wrist
cocked or flexed (the forearm turned off its line). That is what makes the
ice axe's wrist turn through the swing instead of one fist being skewed.

Shading is 2D: each shape carries a simple normal field (a bar is a
cylinder across its axis, the back of the hand a low dome), lit by
gen_weapon's key light and cut into only HAND_BANDS flat bands. Shapes are
rasterised at SS sub-pixels and reduced by majority vote (no anti-aliasing);
then two pixel passes: a crease where a shape sits on another and a dark
outline where the hand meets the weapon or the air. Colours are
gen_weapon's style-E materials (palette v1): every pixel is a palette.json
colour.

Poses. The approved weapon poses are kept, except where D52 says to raise
them (the TT-33 and the PPSh-41, whose hands fell under the screen's edge):
those are gen_weapon's poses moved by the named offsets below, so the 3D
sheets of 2026-10-13 stay reproducible. The TT-33's kick is exaggerated
(Blood). The Katyusha is pass 3 variant B.

Outputs (work/ is gitignored):
    work/art/weapons_2d/<weapon>/<LUMP>.png   every held and flash frame its
                                              .zs shows, final names (MOD-SPEC
                                              §6.3), grAb offsets in the file
    work/art/weapons_2d/<weapon>/metrics.json sizes, offsets, frame keys, the
                                              hand (for make_draft_overlay.py)
    work/art/weapons_2d/metrics.json          every frame, one file
    docs/art/previews/<stamp>_F4_hand-2d-arsenal.html   the sheet (HTML,
                                              self-contained, base64 PNGs,
                                              animations at game speed)

Freedoom: not used. Nothing here enters assets/.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import datetime as dt
import html
import io
import json
import re
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import gen_weapon as gw  # noqa: E402
import sheetlib  # noqa: E402

PROJECT_ROOT = gw.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "weapons_2d"
PREVIEW_DIR = gw.PREVIEW_DIR
ZS_DIR = PROJECT_ROOT / "src" / "zscript" / "weapons"
MAP01_CAPTURE = PROJECT_ROOT / "docs" / "qa" / "evidence" / "2026-10-13_2310_F4_draft-overlay-in-map01.png"

STYLE_KEY = "E"                 # D48: the approved style
SS = 4                          # sub-pixels per pixel side
COVER_MIN = 6                   # of SS*SS sub-pixels: below this, transparent
HAND_BANDS = 4                  # light bands: fewer than the 3D weapon's 6, on purpose
AMBIENT = 0.32
LAMBERT_MID = 0.55
CREASE_STEPS = 2                # ramp steps darker where a shape sits on another
RIM_STEPS = 3                   # ramp steps darker on the hand's outline
HAND_MIN_PX_PER_CM = 5.0        # a far hand is drawn no smaller than this (Doom and Blood exaggerate)
FORESHORTEN_MIN = 0.78          # a shaft into the screen still shows a whole fist

# Materials: gen_weapon's own, style E (palette v1 ramps).
GLOVE, SLEEVE, TEL_W, TEL_B, BUTTON = "glove_brown", "sleeve_field", "tel_white", "tel_blue", "button"
MAT_NAMES = (GLOVE, SLEEVE, TEL_W, TEL_B, BUTTON)
MAT_IDX = {m: i for i, m in enumerate(MAT_NAMES)}
HAND_MATERIALS = ("glove_brown", "glove_black", "skin", "sleeve_field", "sleeve_coat", "sleeve_quilt",
                  "tel_white", "tel_blue", "button")


# ============================================================ the drawings
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

# The palm view: the fist seen from its fingers' side. The heel of the palm
# sits on the wrist side; the four fingers cross the shaft in front of it,
# their tips pressed into the palm; the thumb comes off the thenar and lies
# across the index and middle fingers.
PALM_POLY = (
    (4.3, 1.0), (2.0, 1.9), (-0.4, 2.1), (-2.6, 2.0), (-4.1, 1.4), (-4.5, 3.4),
    (-4.0, 5.8), (-3.0, 8.4), (2.2, 8.4), (3.7, 6.4), (4.7, 4.0),
)
PALM_DOME = ((-0.2, 5.0), 6.0)
PALM_CREASE = (((-3.6, 3.4), (1.6, 3.0)), ((-3.2, 5.6), (0.4, 5.0)))
PALM_TIP_W = 2.7                # w of the fingertips, pressed into the palm
PALM_DIP = 1.15                 # cm behind the tip: the last joint's crease
PALM_PIP = 1.4                  # cm in from the outer curl: the middle joint's crease
PALM_THENAR = ((3.6, 4.9), (1.8, 2.5))
PALM_THUMB = (((4.2, 4.6), (3.2, 1.0), 1.25, 1.12), ((3.2, 1.0), (1.2, -0.9), 1.12, 0.95))

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
    """How one grip is drawn in one frame.

    view     "back": the back of the fist, knuckles, folded fingers;
             "palm": the fist from its fingers' side, thumb across them
    thumb    "front" | "behind" (only where the weapon is not) | "none"
    trigger  the index finger straight, onto a trigger (back view)
    reach    added to every finger's reach, cm (support hands: negative)
    roll     -1..1, the fist turned about the shaft. 0 is the drawing as
             made (three-quarter, from the back); towards +1 the back of the
             hand turns away and the folded fingers' fronts face the eye
             (the wrist side foreshortened, the knuckles and the fingers'
             fronts grow); towards -1 the back of the hand faces the eye
             (the back lengthens, the fingers wrap away and shorten)
    turn     degrees the forearm is turned off its computed line (the wrist
             cocked or flexed), positive towards the shaft's business end
    scale    the whole hand, against HAND_MIN_PX_PER_CM's floor (Blood: big)
    slide    cm the hand is moved along the shaft from where gen_weapon put
             it (a support hand brought into shot), re-projected
    """
    view: str = "back"
    thumb: str = "front"
    trigger: bool = False
    reach: float = 0.0
    roll: float = 0.0
    turn: float = 0.0
    scale: float = 1.0
    slide: float = 0.0


ROLL_KNUCKLE = 0.6              # knuckles grow by this share of the roll
ROLL_FINGER = 0.5               # and the folded fingers' fronts stand out this much more
ROLL_WRAP = 0.8                 # back to the eye: the fingers wrap away, ending this share of the shaft radius sooner


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
    side: str = "right"
    trigger: bool = False
    source: tuple = ()          # (rig, g, axis, elbow): the 3D call, to slide the hand along the shaft

    def slid(self, du: float) -> "Grip":
        """The same grip moved du cm along the shaft (towards its business
        end), re-projected: a hand moved further away is drawn smaller."""
        if not du or not self.source:
            return self
        rig, g, axis, elbow = self.source
        return grip_from_pose(rig, np.asarray(g, np.float64) + gw.unit(axis) * du, axis, elbow, self.shaft_r,
                              self.side, self.trigger)


def _unit2(v) -> np.ndarray:
    v = np.asarray(v, np.float64)
    n = float(np.hypot(*v))
    return v / n if n > 1e-9 else np.array([1.0, 0.0])


def _rot2(v, deg: float) -> np.ndarray:
    t = np.deg2rad(deg)
    c, s = np.cos(t), np.sin(t)
    return np.array([c * v[0] - s * v[1], s * v[0] + c * v[1]])


def grip_from_pose(rig, g, axis, elbow, shaft_r, side="right", trigger=False) -> Grip:
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
    return Grip(at, ea, ew, _unit2(pf - pw), float(s), fa, fw, float(shaft_r), side, bool(trigger),
                (rig, g, tuple(A), tuple(np.asarray(elbow, np.float64))))


@contextlib.contextmanager
def handless():
    """For the length of the block, gen_weapon draws no hand: draw_grip
    records where the hand would be and returns the keys callers read."""
    calls: list[Grip] = []
    original = gw.draw_grip

    def record(rig, style, g, axis, elbow, shaft_r, side="right", trigger=False, forearm=True):
        calls.append(grip_from_pose(rig, g, axis, elbow, shaft_r, side, trigger))
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
    """Local (a, w) cm -> screen px for one grip in one design. The roll
    foreshortens only the wrist side (w > 0): the fingers still close round
    the whole shaft."""

    def __init__(self, grip: Grip, design: GripDesign = GripDesign(), min_px: float = HAND_MIN_PX_PER_CM):
        self.g, self.d = grip, design
        k = max(grip.s, min_px) * design.scale
        self.A = grip.ea * k * grip.fa
        self.W = grip.ew * k * grip.fw
        self.k = k * (grip.fa + grip.fw) / 2      # px per cm for radii
        self.k_arm = k                            # the forearm is not foreshortened by the roll
        self.wk = 1.0 - 0.5 * design.roll         # the wrist side's foreshortening (or stretch)

    def _w(self, w):
        return w * self.wk if w > 0 else w

    def __call__(self, a, w) -> np.ndarray:
        return self.g.at + self.A * a + self.W * self._w(w)

    def vec(self, a, w) -> np.ndarray:
        return self.A * a + self.W * w


def draw_forearm(p: Painter2D, m: HandMap) -> None:
    """Sleeve, hem, telnyashka and glove cuff, from the elbow in to the wrist."""
    g = m.g
    start = m(*WRIST)
    d = _unit2(FOREARM_FROM_HAND * g.ew + (1.0 - FOREARM_FROM_HAND) * g.fore)
    if m.d.turn:
        # positive turns the forearm towards the business end of the shaft
        sgn = 1.0 if float(d[0] * g.ea[1] - d[1] * g.ea[0]) > 0 else -1.0
        d = _rot2(d, sgn * m.d.turn)
    n = np.array([-d[1], d[0]])
    k = m.k_arm

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
    p0 = m(ac, back)
    d = _unit2(m(ac, front) - p0)
    hw = r * float(np.hypot(*m.A))           # px: the finger runs along w, its width is along a
    crease = [(m(ac + r * 0.8, front + PIP_LINE), m(ac - r * 0.8, front + PIP_LINE), 0.5, 0.14)]
    p.poly([m(a, w) for a, w in pts], GLOVE, base, gain,
           ("tube", p0, d, lambda along, hw=hw: np.full_like(along, hw)), lines=crease)


def draw_fist(p: Painter2D, m: HandMap, design: GripDesign) -> None:
    """The back view: back of the hand, the four folded fingers (or three
    and the trigger finger), the knuckle ridge, the thumb."""
    g = m.g
    k = m.k
    base, gain = 0.62, 0.85
    far = -(g.shaft_r + design.reach)            # the far edge of the shaft, w
    kk = 1.0 + ROLL_KNUCKLE * design.roll
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
    back_group = p.group
    for name, ac, width, reach in FINGERS:
        if design.trigger and name == "index":
            continue
        p.ellipse(m(ac, KNUCKLE_W * m.wk), m.vec(KNUCKLE_R[0] * width / 2 * kk, 0), m.vec(0, KNUCKLE_R[1] * kk),
                  GLOVE, base + 0.08, gain, group=back_group)
    # the fingers, little first: each sits on the one below it
    for name, ac, width, reach in reversed(FINGERS):
        p.new_group()
        r = width / 2
        front = far - reach * (1.0 + ROLL_FINGER * design.roll) - ROLL_WRAP * min(design.roll, 0.0) * g.shaft_r
        if design.trigger and name == "index":
            for (a0, w0), (a1, w1), r0, r1 in TRIGGER_INDEX:
                p.bar(m(a0, w0), m(a1, w1), r0 * k, r1 * k, GLOVE, base, gain)
            continue
        if design.reach < 0:
            front = far - reach * 0.4
        finger_block(p, m, ac, r, (KNUCKLE_W + 0.4) * m.wk, front, base, gain)
    # the thumb, over the index
    if design.thumb == "front":
        p.new_group()
        (ta, tw), (sa, sw) = THENAR
        p.ellipse(m(ta, tw), m.vec(sa, 0), m.vec(0, sw * m.wk), GLOVE, base, gain)
        for (a0, w0), (a1, w1), r0, r1 in THUMB_FRONT:
            p.bar(m(a0, w0), m(a1, w1), r0 * k, r1 * k, GLOVE, base + 0.08, gain)


def palm_finger(p: Painter2D, m: HandMap, ac: float, r: float, outer: float, tip: float,
                base: float, gain: float) -> None:
    """One finger seen from the palm side, wrapped round the shaft: a bar
    from its outer curl (w = outer, past the far edge) to its tip pressed
    into the palm (w = tip), rounded at both ends, with the crease lines of
    its two joints."""
    p0, p1 = m(ac, outer + r * 0.5), m(ac, tip - r * 0.5)
    k = m.k
    lines = [(m(ac + r * 0.75, tip - PALM_DIP), m(ac - r * 0.75, tip - PALM_DIP), 0.5, 0.16),
             (m(ac + r * 0.75, outer + PALM_PIP), m(ac - r * 0.75, outer + PALM_PIP), 0.5, 0.12)]
    p.bar(p0, p1, r * k, r * k * 0.92, GLOVE, base, gain, lines=lines)


def draw_palm(p: Painter2D, m: HandMap, design: GripDesign) -> None:
    """The palm view: the heel of the palm, the fingers wrapped round the
    shaft in front of it, the thenar and the thumb across the fingers."""
    g = m.g
    k = m.k
    base, gain = 0.6, 0.85
    far = -(g.shaft_r + design.reach)
    p.new_group()
    (ca, cw), R = PALM_DOME
    creases = [(m(*s0), m(*s1), SEAM_PX, 0.16) for s0, s1 in PALM_CREASE]
    p.poly([m(a, w) for a, w in PALM_POLY], GLOVE, base - 0.04, gain, ("dome", m(ca, cw), R * k), lines=creases)
    for name, ac, width, reach in reversed(FINGERS):
        p.new_group()
        palm_finger(p, m, ac, width / 2, far - reach * 0.6, PALM_TIP_W, base, gain)
    if design.thumb != "none":
        p.new_group()
        (ta, tw), (sa, sw) = PALM_THENAR
        p.ellipse(m(ta, tw), m.vec(sa, 0), m.vec(0, sw * m.wk), GLOVE, base, gain)
        for (a0, w0), (a1, w1), r0, r1 in PALM_THUMB:
            p.bar(m(a0, w0), m(a1, w1), r0 * k, r1 * k, GLOVE, base + 0.08, gain)


def draw_hand(p: Painter2D, grip: Grip, design: GripDesign, min_px: float = HAND_MIN_PX_PER_CM) -> None:
    m = HandMap(grip.slid(design.slide), design, min_px)
    draw_forearm(p, m)
    if design.view == "palm":
        draw_palm(p, m, design)
    else:
        draw_fist(p, m, design)


# ================================================================ poses
def moved(pose, d_origin=(0.0, 0.0, 0.0), d_bore=(0.0, 0.0, 0.0), name: str | None = None):
    """gen_weapon's pose moved: origin by d_origin (camera cm), bore by
    d_bore (added before normalising). Same frame letter, same state."""
    o = tuple(float(a + b) for a, b in zip(pose.origin, d_origin))
    b = tuple(float(a + c) for a, c in zip(pose.bore, d_bore))
    return replace(pose, origin=o, bore=b, name=name or pose.name)


# D52: the TT-33's grip, and with it the hand, sat mostly under the screen's
# edge. Raised (the 11:05 trial's TT-1R, accepted as "Manos 1") and moved a
# little to the left; the kick exaggerated after Blood (D49): the muzzle
# thrown further up and the pistol pushed back into the hand.
TT_RAISE = (-1.0, -4.0, 0.0)            # camera cm: left, up, depth
TT_KICK = {"A": ((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
           "B": ((0.2, -0.8, -0.8), (0.0, -0.12, 0.0)),
           "C": ((0.3, -1.6, -1.2), (0.0, -0.20, 0.0))}   # extra (origin, bore) per frame
TT_POSES_2D = tuple(moved(p, np.add(TT_RAISE, TT_KICK[p.frame][0]), TT_KICK[p.frame][1],
                          f"{p.name}, raised") for p in gw.TT_POSES)

# D52: the PPSh-41's right hand projected under the screen (its grip at y 278
# of 200). The gun comes left, up and forward, so both hands are in shot and
# the muzzle still sits under and left of the crosshair.
PPSH_RAISE = (-5.0, -4.0, 8.0)
PPSH_POSES_2D = tuple(moved(p, PPSH_RAISE, name=f"{p.name}, raised") for p in gw.PPSH_POSES)

HK_VARIANT_2D = "B"             # D51: "de katiushka me flipa la B" ("for the Katyusha I love B")


# ================================================================ designs
TRIGGER = GripDesign(thumb="behind", trigger=True)
SUPPORT = GripDesign(thumb="behind", reach=SUPPORT_REACH)
# The IZh-58's left hand under the fore-end: at rest a little further out
# than gen_weapon put it (more of it above the status bar); through the
# reload it slides out along the barrels as the gun is broken and shut
# (Blood's off hand at work). cm along the shaft, per frame.
IZH_SLIDE = {"A": 4.0, "B": 4.0, "C": 8.0, "D": 10.0}
IZH_DESIGNS = {c: (TRIGGER, replace(SUPPORT, slide=v)) for c, v in IZH_SLIDE.items()}
# The RPG-7's left hand sat under the screen's edge (gen_weapon's
# RPG_LEFT_U, "at the edge of the view"): brought along the tube into shot.
RPG_SLIDE = 12.0
RPG_DESIGNS = {c: (replace(SUPPORT, slide=RPG_SLIDE),) for c in "AB"}
# The ice axe, frame by frame: the wrist turns about the shaft through the
# swing, palm, fingers' fronts, back, as a drawn animation would.
#   A  idle: the back of the fist, three-quarter, as approved
#   B  raised over the shoulder: the wrist cocked back, the fist seen from its
#      fingers (palm view), the forearm turned down behind it
#   C  coming down: rolled over, the folded fingers' fronts and the knuckles
#      to the eye, the back foreshortened
#   D  the pick in: the wrist flexed forward, the back of the hand to the eye
#      and the fingers wrapped away, the forearm turned to follow the blow
#   E  recovery: back to the fist, a little rolled (drawn; ice_axe.zs does not
#      show E today)
AXE_DESIGNS = {
    "A": (GripDesign(),),
    "B": (GripDesign(view="palm", turn=-18.0),),
    "C": (GripDesign(roll=0.9, turn=12.0),),
    "D": (GripDesign(roll=-0.7, turn=30.0),),
    "E": (GripDesign(roll=0.2, turn=-6.0),),
}


# ================================================================ the arsenal
@dataclass(frozen=True)
class Arm:
    """One weapon in 2D: its frames, its flash, its state machine."""
    key: str                    # work/art/weapons_2d/<key>/
    title: str
    label: str                  # frame keys: AX-1, TT-1 ...
    flash_label: str            # TF-1 ...
    sprite: str                 # held lumps, MOD-SPEC 6.3
    flash_sprite: str | None
    zs: str
    ph_held: str                # the placeholder the .zs names today
    ph_flash: str | None
    poses: tuple
    render: Callable            # (style, pose) -> (Frame, anchor)
    designs: dict               # letter -> tuple of GripDesign, one per grip in call order
    flash_on: dict = field(default_factory=dict)        # flash letter -> held letter it is drawn for
    flash: Callable | None = None                       # (letter, anchor, pose) -> Frame
    shots: int = 1              # Fire passes in the game-speed animation
    min_px: float = HAND_MIN_PX_PER_CM
    extra: str = ""             # held letters drawn although the .zs does not show them (reserved, approved)
    note: str = ""


def _axe(st, pose):
    return gw.render_axe_frame(st, pose), None


def _roks_flash(letter, anchor, pose):
    U, V, W, at = gw.gun_basis(pose.origin, pose.bore, pose.up)
    return gw.render_roks3_flash(letter, at(gw.ROKS_NOZZLE[1] + 0.4), U)


def _same(designs: tuple, letters: str) -> dict:
    return {c: designs for c in letters}


ARMS = {
    "ice_axe": Arm("ice_axe", "SLOT 1: THE ICE AXE", "AX", "", gw.AXE_SPRITE, None, "ice_axe.zs", "PUNG", None,
                   gw.AXE_POSES, _axe, AXE_DESIGNS, extra="E",
                   note="One drawing per frame: the wrist turns. MOD-SPEC reserves SDAX A-E; ice_axe.zs swings "
                        "B-C-D-C-B, so E (recovery) is drawn but not shown by the state machine today."),
    "tt33": Arm("tt33", "SLOT 2: THE TT-33 TOKAREV", "TT", "TF", gw.TT_SPRITE, gw.TT_FLASH, "tokarev.zs", "PISG",
                "PISF", TT_POSES_2D, lambda st, p: gw.render_tt33_frame(st, p), _same((TRIGGER,), "ABC"),
                {"A": "B"}, lambda c, a, p: gw.render_tt33_flash(c, a), shots=2,
                note="Pose raised 4 cm and 1 cm left (D52); the kick exaggerated after Blood."),
    "ppsh": Arm("ppsh", "SLOT 4: THE PPSH-41", "PP", "PF", gw.PPSH_SPRITE, gw.PPSH_FLASH, "ppsh.zs", "CHGG",
                "CHGF", PPSH_POSES_2D, lambda st, p: gw.render_ppsh_frame(st, p),
                _same((TRIGGER, GripDesign(reach=SUPPORT_REACH, thumb="behind")), "AB"),
                {"A": "A"}, lambda c, a, p: gw.render_ppsh_flash(c, a), shots=3,
                note="Pose moved 5 cm left, 4 cm up and 8 cm forward (D52): both hands in shot."),
    "izh": Arm("izh", "SLOT 3: THE IZH-58", "IZ", "IF", gw.IZH_SPRITE, gw.IZH_FLASH, "izh.zs", "SHTG", "SHTF",
               gw.IZH_POSES, lambda st, p: gw.render_izh_frame(st, p), IZH_DESIGNS,
               {"A": "A", "B": "A"}, lambda c, a, p: gw.render_izh_flash(c, a), shots=2,
               note="Approved poses kept. The left hand slides out along the barrels through the reload; the "
                    "right hand on the stock's wrist projects off the screen, as in the 3D set."),
    "rpg7": Arm("rpg7", "SLOT 5: THE RPG-7", "RL", "RF", gw.RPG_SPRITE, gw.RPG_FLASH, "rpg7.zs", "MISG", "MISF",
                tuple(p for p in gw.RPG_POSES if p.wired), lambda st, p: gw.render_rpg7_frame(st, p),
                RPG_DESIGNS, {"A": "B", "B": "B", "C": "B", "D": "B"},
                lambda c, a, p: gw.render_rpg7_flash(c, a),
                note="Approved poses kept. The left hand brought 12 cm along the tube into shot; the right hand is on "
                     "the grip behind the eye, as in the 3D set."),
    "roks3": Arm("roks3", "SLOT 6: THE ROKS-3 FLAMETHROWER", "RK", "KF", gw.ROKS_SPRITE, gw.ROKS_FLASH, "roks3.zs",
                 "PLSG", "PLSF", gw.ROKS_POSES, lambda st, p: gw.render_roks3_frame(st, p),
                 _same((TRIGGER, GripDesign(thumb="behind", reach=-0.4)), "AB"), {"A": "A"}, _roks_flash, shots=2,
                 note="Approved poses kept. The right hand on the stock's wrist sits low at the right edge."),
    "katyusha": Arm("katyusha", "SLOT 7: THE HAND KATYUSHA (PASS 3, VARIANT B)", "HK", "HF", gw.HK_SPRITE,
                    gw.HK_FLASH, "katyusha.zs", "BFGG", "BFGF", tuple(p for p in gw.HK_POSES if p.wired),
                    lambda st, p: gw.render_katyusha_frame(st, p, HK_VARIANT_2D),
                    _same((TRIGGER, GripDesign()), "AB"), {"A": "B", "B": "B"},
                    lambda c, a, p: gw.render_katyusha_flash(c, a),
                    note="Pass 3 variant B (D51), carried low at the hip with both hands (D49)."),
}
WEAPON_ORDER = ("ice_axe", "tt33", "izh", "ppsh", "rpg7", "roks3", "katyusha")


# ================================================================ frames
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
    key: str                    # e.g. "TT-1", "TF-1"
    lump: str
    weapon: str
    letter: str
    pose: str
    frame: gw.Frame             # the sprite as saved
    bare: gw.Frame | None = None        # held: the weapon without hand
    hand_px: int = 0
    hand_above_bar: int = 0     # hand pixels above the classic status bar
    flash: bool = False
    over: str | None = None     # flash: the held letter it is drawn for


WEAPON_RIM_STEPS = 3            # item 6 of the brief: the weapon's silhouette darkened this many ramp steps more


def harden(frame: gw.Frame, steps: int = WEAPON_RIM_STEPS) -> gw.Frame:
    """The weapon given the hand's hard contour: every opaque pixel on its
    silhouette (next to transparency) goes `steps` further down its own
    material's ramp, so steel and wood get the dark edge the 2D hand has.
    Flash materials are left alone. A new Frame; gen_weapon's is untouched."""
    if steps <= 0:
        return frame
    rgba, mat = frame.rgba.copy(), frame.mat
    a = rgba[..., 3] > 0
    P = np.pad(a, 1)
    h, w = a.shape
    edge = np.zeros_like(a)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        edge |= ~P[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
    edge &= a
    for name, i in gw.MAT_ID.items():
        if name in gw.FLAT:
            continue
        sel = edge & (mat == i)
        if not sel.any():
            continue
        cols = np.array(gw.MATERIALS[name].colours(), np.int16)
        px = rgba[sel, :3].astype(np.int16)
        idx = np.abs(px[:, None, :] - cols[None]).sum(-1).argmin(1)
        rgba[sel, :3] = cols[np.maximum(idx - steps, 0)].astype(np.uint8)
    return gw.Frame(rgba, mat, frame.left, frame.top, frame.hud)


def render_2d(weapon: str, pose, style=None) -> tuple[gw.Frame, gw.Frame, int, object]:
    """(the 2D-hand frame, the weapon without hand, hand pixel count, the
    renderer's anchor: muzzle, flash anchors, or None)."""
    arm = ARMS[weapon]
    style = style or gw.HAND[STYLE_KEY]
    with handless() as grips:
        bare, anchor = arm.render(style, pose)
    designs = arm.designs[pose.frame]
    if len(grips) != len(designs):
        raise ValueError(f"{weapon} {pose.frame}: {len(grips)} grips, {len(designs)} designs")
    bare = harden(bare)
    under = canvas_rgba(bare)
    p = Painter2D()
    for grip, design in zip(grips, designs):
        draw_hand(p, grip, design, arm.min_px)
    hand, mask = p.to_rgba(under)
    out = under.copy()
    out[mask] = hand[mask]
    return crop_frame(out), bare, int(mask.sum()), anchor


def hand_above_bar(frame2d: gw.Frame, bare: gw.Frame) -> int:
    """Pixels of the 2D frame that are hand (not the bare weapon) above the
    classic status bar."""
    a = canvas_rgba(frame2d)
    b = canvas_rgba(bare)
    hand = (a[..., 3] > 0) & ((b[..., 3] == 0) | np.any(a[..., :3] != b[..., :3], -1))
    top = gw.STATUSBAR_TOP - gw.CANVAS_Y0
    x0, x1 = -gw.CANVAS_X0, -gw.CANVAS_X0 + gw.SCREEN_W
    return int(hand[:top, x0:x1].sum())


def render_arm(weapon: str) -> list[Rendered]:
    """Every held frame the .zs shows, then every flash frame."""
    arm = ARMS[weapon]
    held_letters, flash_letters = zs_letters(arm)
    rows, anchors, poses = [], {}, {}
    for i, pose in enumerate(arm.poses):
        if pose.frame not in held_letters and pose.frame not in arm.extra:
            continue
        f2, bare, n, anchor = render_2d(weapon, pose)
        anchors[pose.frame], poses[pose.frame] = anchor, pose
        rows.append(Rendered(f"{arm.label}-{i + 1}", f"{arm.sprite}{pose.frame}0", weapon, pose.frame, pose.name,
                             f2, bare, n, hand_above_bar(f2, bare)))
    for j, letter in enumerate(sorted(flash_letters)):
        on = arm.flash_on[letter]
        fl = arm.flash(letter, anchors[on], poses[on])
        rows.append(Rendered(f"{arm.flash_label}-{j + 1}", f"{arm.flash_sprite}{letter}0", weapon, letter,
                             f"flash {letter}, drawn for {arm.sprite}{on}0", fl, flash=True, over=on))
    return rows


def render_all(weapons=WEAPON_ORDER) -> dict[str, list[Rendered]]:
    return {w: render_arm(w) for w in weapons}


# ======================================================= the state machines
STATE_RE = re.compile(r"^\s*([A-Z0-9_#-]{4})\s+([A-Z]+)\s+(-?\d+)\s*(.*?);?\s*$")
LABEL_RE = re.compile(r"^\s*([A-Za-z]\w*):\s*$")


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def zs_text(arm: Arm) -> str:
    return strip_comments((ZS_DIR / arm.zs).read_text(encoding="utf-8"))


def zs_states(text: str) -> dict[str, list]:
    """{label: [(sprite, letters, tics, action) | ("goto", label)]} of the
    first States block."""
    m = re.search(r"\bStates\s*\{", text)
    if not m:
        return {}
    out, cur = {}, None
    for line in text[m.end():].splitlines():
        if line.strip() == "}":
            break
        lm = LABEL_RE.match(line)
        if lm:
            cur = lm.group(1)
            out[cur] = []
            continue
        if cur is None:
            continue
        s = line.strip().rstrip(";")
        if s.startswith("Goto "):
            out[cur].append(("goto", s.split()[1]))
        elif s in ("Loop", "Stop"):
            out[cur].append(("goto", s))
        else:
            sm = STATE_RE.match(line)
            if sm:
                out[cur].append((sm.group(1), sm.group(2), int(sm.group(3)), sm.group(4).strip()))
    return out


def zs_letters(arm: Arm) -> tuple[set, set]:
    """The frame letters the .zs shows for the held and flash placeholders,
    or for our own names once installed (N17: the TT-33's PISG/PISF are
    SDTT/SDTF since 2026-10-15; the letters did not change)."""
    states = zs_states(zs_text(arm))
    held, flash = set(), set()
    for lines in states.values():
        for st in lines:
            if st[0] in (arm.ph_held, arm.sprite):
                held |= set(st[1])
            elif arm.ph_flash and st[0] in (arm.ph_flash, arm.flash_sprite):
                flash |= set(st[1])
    return held, flash


def flashing_actions(text: str) -> set:
    """A_GunFlash and every action function of the file that calls it."""
    names = {"A_GunFlash"}
    parts = re.split(r"\baction\s+void\s+", text)
    for part in parts[1:]:
        name = re.match(r"(\w+)", part).group(1)
        if "A_GunFlash" in part.split("action void")[0]:
            names.add(name)
    return names


READY_TICS = 18                 # tics of the ready frame between two loops of the animation
TIC_MS = 1000.0 / 35.0


def fire_timeline(arm: Arm, shots: int | None = None) -> list[tuple[str, str | None, int]]:
    """The Fire state played `shots` times (A_ReFire jumps back while shots
    remain; on the last one an A_JumpIf to another label is taken, the
    IZh's reload), then READY_TICS of the ready frame. Returns runs of
    (held letter, flash letter or None, tics), the flash psprite running
    from the moment an action calls A_GunFlash, as the engine does."""
    text = zs_text(arm)
    states = zs_states(text)
    flashers = flashing_actions(text)
    shots = arm.shots if shots is None else shots
    held: list[str] = []                    # one entry per tic
    flash_at: list[int] = []
    label, i, shot = "Fire", 0, 1
    guard = 0
    while guard < 400:
        guard += 1
        lines = states.get(label, [])
        if i >= len(lines):
            break
        st = lines[i]
        if st[0] == "goto":
            if label in ("Fire", "Reload") and st[1] == "Ready":
                break
            label, i = st[1], 0
            continue
        sprite, letters, tics, action = st
        jump = re.search(r'A_JumpIf\([^,]*,\s*"(\w+)"\)', action)
        if jump and shot == shots and jump.group(1) in states:
            label, i = jump.group(1), 0
            continue
        if "A_ReFire" in action and shot < shots:
            shot += 1
            label, i = "Fire", 0
            continue
        for k, letter in enumerate(letters):
            if k == 0 and any(re.search(rf"\b{re.escape(f)}\b", action) for f in flashers):
                flash_at.append(len(held))
            held += [letter] * max(tics, 0)
        i += 1
    held += ["A"] * READY_TICS
    flash_tics: list[str | None] = [None] * len(held)
    if arm.ph_flash:
        seq = [(c, t) for s, ls, t, _ in (x for x in states.get("Flash", []) if x[0] != "goto") for c in ls]
        for t0 in flash_at:
            t = t0
            for c, tics in seq:
                for _ in range(tics):
                    if t < len(flash_tics):
                        flash_tics[t] = c
                    t += 1
    runs: list[list] = []
    for h, f in zip(held, flash_tics):
        if runs and runs[-1][0] == h and runs[-1][1] == f:
            runs[-1][2] += 1
        else:
            runs.append([h, f, 1])
    return [tuple(r) for r in runs]


# ================================================================= saving
def save_all(out: dict[str, list[Rendered]], out_dir: Path = OUT_DIR) -> dict:
    allm = {}
    for weapon, rows in out.items():
        arm = ARMS[weapon]
        held, flash = zs_letters(arm)
        wm = {"_state_machine": {"file": f"src/zscript/weapons/{arm.zs}", "held_placeholder": arm.ph_held,
                                 "held_letters": "".join(sorted(held)), "flash_placeholder": arm.ph_flash,
                                 "flash_letters": "".join(sorted(flash)), "hand": STYLE_KEY, "hands": "2d"}}
        folder = out_dir / weapon
        for r in rows:
            gw.save_sprite(r.frame, folder / f"{r.lump}.png")
            entry = {"key": r.key, "pose": r.pose, "size": list(r.frame.rgba.shape[1::-1]),
                     "offsets": [int(v) for v in r.frame.offsets()]}
            if r.flash:
                entry["over"] = f"{arm.sprite}{r.over}0"
            else:
                entry["hand_px"] = r.hand_px
                entry["hand_px_above_bar"] = r.hand_above_bar
            wm[r.lump] = entry
            allm[r.key] = {"lump": r.lump, "weapon": weapon, **entry}
        if weapon == "katyusha":
            pk = gw.render_katyusha_pickup(HK_VARIANT_2D)
            gw.save_sprite(pk, folder / f"{gw.HK_PICKUP}A0.png")
            wm[f"{gw.HK_PICKUP}A0"] = {"key": "HP-1", "pose": f"pickup, pass 3 variant {HK_VARIANT_2D}",
                                       "size": list(pk.rgba.shape[1::-1]), "offsets": [int(v) for v in pk.offsets()]}
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "metrics.json").write_text(json.dumps(wm, indent=2) + "\n", encoding="utf-8")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(allm, indent=2) + "\n", encoding="utf-8")
    return allm


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


def png_uri(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


class Images:
    """Every screen of the sheet embedded ONCE (a frame shows at 2x, at 1x
    and in its animation): <img data-ref> tags take their src from IMG."""

    def __init__(self):
        self.uris: list[str] = []
        self.index: dict[str, str] = {}

    def add(self, arr: np.ndarray) -> str:
        uri = png_uri(arr)
        if uri not in self.index:
            self.index[uri] = f"i{len(self.uris)}"
            self.uris.append(uri)
        return self.index[uri]

    def script(self) -> str:
        table = ",".join(f'"{self.index[u]}":"{u}"' for u in self.uris)
        return ("<script>var IMG={" + table + "};document.querySelectorAll('img[data-ref]').forEach("
                "function(i){i.src=IMG[i.dataset.ref];});</script>")


def screen_img(ref: str, k: int, title: str) -> str:
    w, h = gw.SCREEN_W * k, gw.SCREEN_H * k
    return (f'<img class="px" data-ref="{ref}" width="{w}" height="{h}" alt="{html.escape(title)}" '
            f'title="{html.escape(title)}">')


SHEET_CSS = """
.frames{display:flex;flex-wrap:wrap;gap:18px;align-items:flex-start}
.fr{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:10px}
.fr .k{font:600 15px Menlo,monospace;color:var(--warn)}.fr .l{font:12px Menlo,monospace;color:var(--ink)}
.fr .p{font-size:12px;color:var(--mute);margin-bottom:6px}
.pair{display:flex;gap:10px;align-items:flex-end}
.anim{display:flex;gap:18px;align-items:flex-start;flex-wrap:wrap;margin:14px 0 6px}
.anim .seq{font:12px Menlo,monospace;color:var(--mute);max-width:560px}
.anim button{background:var(--card);color:var(--ink);border:1px solid var(--line);border-radius:4px;padding:3px 10px;cursor:pointer}
.verdict p{max-width:1000px;margin:6px 0}.verdict b{color:var(--warn)}
.before{opacity:.95}
"""

ANIM_JS = """
<script>
(function(){
  var TIC = 1000/35;
  document.querySelectorAll('img.anim-player').forEach(function(img){
    var frames = JSON.parse(img.dataset.frames).map(function(r){ return IMG[r]; }), seq = JSON.parse(img.dataset.seq);
    var i = 0, playing = true, t0 = performance.now(), acc = 0;
    var label = document.getElementById(img.dataset.label);
    function show(){ img.src = frames[seq[i][0]]; if (label) label.textContent = seq[i][1] + '  (' + seq[i][2] + ' tics)'; }
    function step(now){
      if (playing){
        acc += now - t0;
        while (acc >= seq[i][2] * TIC){ acc -= seq[i][2] * TIC; i = (i + 1) % seq.length; show(); }
      }
      t0 = now; requestAnimationFrame(step);
    }
    var btn = document.getElementById(img.dataset.btn);
    if (btn) btn.onclick = function(){ playing = !playing; btn.textContent = playing ? 'pause' : 'play'; };
    show(); requestAnimationFrame(step);
  });
})();
</script>
"""


def animation_html(weapon: str, rows: list[Rendered], backdrop: np.ndarray, imgs: Images, k: int = 2) -> str:
    arm = ARMS[weapon]
    held = {r.letter: r.frame for r in rows if not r.flash}
    flash = {r.letter: r.frame for r in rows if r.flash}
    keys = {r.letter: r.key for r in rows if not r.flash}
    fkeys = {r.letter: r.key for r in rows if r.flash}
    runs = fire_timeline(arm)
    combos, seq = [], []
    for h, f, t in runs:
        c = (h, f)
        if c not in combos:
            combos.append(c)
        lab = keys.get(h, h) + (f" + {fkeys.get(f, f)}" if f else "")
        seq.append([combos.index(c), lab, t])
    refs = [imgs.add(on_capture([held[h], flash.get(f) if f else None], backdrop)) for h, f in combos]
    total = sum(t for _, _, t in runs)
    text = " ".join(f"{lab}:{t}" for _, lab, t in seq)
    uid = f"a_{weapon}"
    attr = lambda v: html.escape(json.dumps(v), quote=True)
    player = (f'<img class="px anim-player" data-ref="{refs[0]}" width="{gw.SCREEN_W * k}" height="{gw.SCREEN_H * k}" '
              f'alt="animation" data-frames="{attr(refs)}" data-seq="{attr(seq)}" data-label="{uid}_l" '
              f'data-btn="{uid}_b">')
    return (f'<div class="anim"><div>{player}'
            f'<div class="cap"><button id="{uid}_b">pause</button> <span id="{uid}_l"></span></div></div>'
            f'<div class="seq"><b>At game speed (35 tics/s), from {html.escape(arm.zs)}:</b> '
            f'{html.escape(arm.title.split(": ", 1)[-1].lower())}, {arm.shots} shot(s) of Fire'
            f'{" then the reload" if weapon == "izh" else ""}, then {READY_TICS} tics at rest; '
            f'{total} tics = {total / 35:.2f} s a loop. Frame:tics &mdash; {html.escape(text)}. '
            f'Weapon bob not shown. NOT VERIFIED in GZDoom (D26).</div></div>')


def frame_card(r: Rendered, rows: list[Rendered], backdrop: np.ndarray, imgs: Images) -> str:
    if r.flash:
        under = next(x.frame for x in rows if not x.flash and x.letter == r.over)
        scr = on_capture([under, r.frame], backdrop)
        what = f"over {ARMS[r.weapon].sprite}{r.over}0"
    else:
        scr = on_capture([r.frame], backdrop)
        what = f"hand {r.hand_above_bar} px above the bar"
    uri = imgs.add(scr)
    lo, to = r.frame.offsets()
    return (f'<div class="fr"><div class="k">{html.escape(r.key)} <span class="l">{html.escape(r.lump)}'
            f' &middot; grAb {lo},{to} &middot; {r.frame.rgba.shape[1]}x{r.frame.rgba.shape[0]}</span></div>'
            f'<div class="p">{html.escape(r.pose)} &middot; {html.escape(what)}</div>'
            f'<div class="pair">{screen_img(uri, 2, r.key + " 2x")}{screen_img(uri, 1, r.key + " 1x")}</div></div>')


def before_card(weapon: str, backdrop: np.ndarray, imgs: Images) -> str:
    """The approved pose with the 2D hand, for the weapons whose pose moved."""
    arm = ARMS[weapon]
    old = {"tt33": gw.TT_POSES, "ppsh": gw.PPSH_POSES}.get(weapon)
    if not old:
        return ""
    f2, _, _, _ = render_2d(weapon, old[0])
    uri = imgs.add(on_capture([f2], backdrop))
    return (f'<div class="fr before"><div class="k">BEFORE <span class="l">{arm.sprite}A0 in the approved pose'
            f'</span></div><div class="p">the pose of 2026-10-13, 2D hand: for comparison, not a sprite</div>'
            f'<div class="pair">{screen_img(uri, 1, "before 1x")}</div></div>')


SHEET_INTRO = (
    "D52 (“Manos 1”): the sergeant's hand drawn in 2D pixel art, style E (brown leather glove, field "
    "sleeve, telnyashka), now on every weapon, with every held and flash frame its state machine shows "
    "(read from <code>src/zscript/weapons/*.zs</code>, never edited). The weapons are gen_weapon's own 3D "
    "renders without their hand; the hand is drawn per frame on each grip. Animation reference: Blood (D49), "
    "style only, nothing of Blood copied. Every frame is numbered (AX-1, TT-1, &hellip;; the flash frames TF-1, "
    "&hellip;) and shown at 2x and 1x over MAP01 as GZDoom drew it (the dorm, rebuilt without its weapon from "
    "six engine captures of the same view; the capture's own status bar on top). Positions follow Doom's "
    "arithmetic and are NOT VERIFIED in GZDoom (D26): the engine pass is the PM's. Sprites: "
    "<code>work/art/weapons_2d/&lt;weapon&gt;/</code>, final names (MOD-SPEC &sect;6.3) with grAb, ready for "
    "the draft overlay. Nothing is in <code>assets/</code>; the installed pickups are untouched.")


def build_sheet(out: dict[str, list[Rendered]], stamp: str, verdicts: dict, preview_dir: Path = PREVIEW_DIR) -> Path:
    backdrop = map01_backdrop()
    if backdrop is None:
        backdrop = gw.view_backdrop()
    sections = []
    imgs = Images()
    n_held = sum(1 for rows in out.values() for r in rows if not r.flash)
    n_flash = sum(1 for rows in out.values() for r in rows if r.flash)
    for weapon, rows in out.items():
        arm = ARMS[weapon]
        cards = [before_card(weapon, backdrop, imgs)] + [frame_card(r, rows, backdrop, imgs) for r in rows]
        v = "".join(f"<p>{p}</p>" for p in verdicts.get(weapon, []))
        body = (animation_html(weapon, rows, backdrop, imgs) + f'<div class="frames">{"".join(cards)}</div>'
                + f'<div class="verdict"><h2 style="margin-top:14px">Self-assessment</h2>{v}</div>')
        sections.append((arm.title, html.escape(arm.note), body))
    general = "".join(f"<p>{p}</p>" for p in verdicts.get("_all", []))
    sections.append(("The whole arsenal: self-assessment", "", f'<div class="verdict">{general}</div>'))
    title = "The 2D hand on the whole arsenal (F4, D52)"
    sec_html = "\n".join(f'<section><h2>{html.escape(h)}</h2>' + (f'<p class="lead">{lead}</p>' if lead else "")
                         + f"{inner}</section>" for h, lead, inner in sections)
    doc = (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<title>{html.escape(title)}</title>'
           f'<style>{sheetlib.CSS}{SHEET_CSS}</style></head><body>\n'
           f'<header><h1>{html.escape(title)}</h1><div class="meta">SDAX &middot; SDTT/SDTF &middot; SDIZ/SDIF '
           f'&middot; SDPP/SDPF &middot; SDRL/SDRF &middot; SDRK/SDKF &middot; SDHK/SDHF &middot; {n_held} held + '
           f'{n_flash} flash frames &middot; draft &middot; {html.escape(stamp)}</div>'
           f'<p class="intro">{SHEET_INTRO}</p></header>\n{sec_html}\n'
           f'<footer>tools/art/gen_hands_2d.py &middot; palette v1 &middot; no Freedoom or Blood pixel in any '
           f'sprite &middot; generated {html.escape(stamp)}</footer>{imgs.script()}{ANIM_JS}</body></html>\n')
    path = preview_dir / f"{stamp}_F4_hand-2d-arsenal.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc, encoding="utf-8")
    return path


SELF_ASSESSMENT: dict[str, list[str]] = {
    "ice_axe": [
        "<b>The wrist turns.</b> Each frame has its own drawing on the grip, chosen by hand: AX-1 the back of the "
        "fist (as approved), AX-2 the fist seen from its fingers with the thumb across them (the wrist cocked back "
        "over the shoulder), AX-3 rolled over, the folded fingers and the knuckles to the eye, AX-4 the back of the "
        "hand to the eye with the fingers wrapped away (the wrist flexed into the blow), AX-5 nearly back to rest. "
        "Played at game speed (B-C-D-C-B, as ice_axe.zs swings) the fist visibly turns over instead of one fist "
        "being skewed, which was the 11:05 trial's flaw.",
        "<b>Weak.</b> AX-3 to AX-5 are still the one back-of-fist drawing turned and foreshortened, not drawn from "
        "scratch as AX-2 is; at 1x the turn reads mostly through the knuckles and the forearm's angle. AX-4, the "
        "pick going in, shows the least hand (about 1 500 px above the status bar). AX-5 (SDAXE0) is drawn because "
        "MOD-SPEC reserves A-E, but ice_axe.zs never shows it today.",
    ],
    "tt33": [
        "<b>The hand is in shot now.</b> The pose is the approved one raised 4 cm and moved 1 cm left (D52, the "
        "11:05 TT-1R): the glove, three folded fingers, the index on the trigger, the cuff and the telnyashka all "
        "read at 1x, as Doom's own pistol frames a hand. The kick is exaggerated after Blood: on TT-2 the slide "
        "goes back and the muzzle climbs, on TT-3 the pistol and hand ride up about 25 px; TF-1 sits on TT-2's "
        "muzzle.",
        "<b>Weak.</b> One hand only (Doom's grammar, not Blood's two-handed one). The pistol is small, so the glove "
        "is half the sprite and the folded fingers read as stacked bars rather than as fingers wrapped round a "
        "grip. The serrations and the star medallion stay one or two pixels at 1x.",
    ],
    "izh": [
        "<b>As approved, with the 2D hand.</b> The left hand under the fore-end is the hand you see; it sits 4 cm "
        "further out than the 3D one so more of it clears the status bar, and through the reload (IZ-4 broken open, "
        "IZ-3, IZ-2) it slides out along the barrels: the off hand moves, as in Blood. IF-1 and IF-2 are gen_weapon's "
        "flashes at the same muzzle.",
        "<b>Weak.</b> The right hand on the stock's wrist projects off the screen, so this is a one-hand view of a "
        "two-hand gun; on IZ-4 only the fingers clear the bar (about 400 px). The PPSh treatment (the gun moved in and "
        "up) would bring the right hand in, but the IZh's pose is approved and D52 names only the TT-33 and the "
        "PPSh: a proposal for the CEO, not done here.",
    ],
    "ppsh": [
        "<b>Both hands in shot.</b> The gun is moved 5 cm left, 4 cm up and 8 cm forward (D52): the left hand "
        "wraps the fore-end ahead of the drum, the right hand grips the stock's wrist with the index on the trigger, "
        "and the muzzle stays under and left of the crosshair. Two frames, as ppsh.zs alternates them; PF-1 is the "
        "one flash both rounds show (the state machine has only CHGF A), so on PP-2 it sits a few px off the "
        "kicked-back muzzle, as it will in the engine.",
        "<b>Weak.</b> The right glove lies on the birch stock, and both are slices of the same rust-brown ramp: the "
        "hand separates from the wood only by its dark outline, the lowest contrast in the arsenal. Fixing it means "
        "a darker glove or a different wood, and both are approved materials, so it is left for the CEO's eye.",
    ],
    "rpg7": [
        "<b>A hand where there was none.</b> In the approved pose the left hand sat under the screen's edge (the 3D "
        "frames showed a sliver, the 2D ones nothing). It is brought 12 cm along the tube, re-projected (smaller as "
        "it goes further), so a gloved fist holds the tube on RL-1 and RL-2. RF-1 to RF-4 are gen_weapon's blast and "
        "smoke at the muzzle.",
        "<b>Weak, the weakest of the set.</b> The tube recedes straight into the middle of the screen, small, the "
        "right hand is on the grip behind the eye, and only one fist shows (300 to 800 px above the bar). Against "
        "Blood this is the frame that most needs a new pose: the launcher lower and turned across the view so both "
        "hands and the warhead read. The pose is approved, so that is a proposal for the CEO, not done here.",
    ],
    "roks3": [
        "<b>As approved, both hands.</b> The left hand closes round the fuel tube, the right hand grips the stock's "
        "wrist low on the right; KF-1 is the jet, drawn for RK-1 as roks3.zs shows it.",
        "<b>Weak.</b> The right hand is partly under the status bar, so of it mostly the knuckles and the cuff show; "
        "the hose and the stock are the same dark mass as in the 3D set.",
    ],
    "katyusha": [
        "<b>Variant B with both hands (D51, D49).</b> Six bare tubes in riveted bands carried low at the hip, the "
        "right hand on the pistol grip with the index on the trigger, the left on the forward handle, both sleeves "
        "running out to the corners. HK-2 is the salvo with the exaggerated kick; HF-1 lights the six motors and the "
        "backblast, HF-2 is their smoke. The hands are drawn at the 5 px/cm floor while the launcher sits at about "
        "3.4 px/cm, so they are half again life size: Blood's big hands, on purpose.",
        "<b>Weak.</b> That scale is a judgement call; if the CEO finds the gloves too big for the launcher, it is "
        "one number (Arm.min_px). HK-2's sprite is 384 px wide, the forearms reaching both edges of the screen: "
        "fine in the 320 columns, to be checked in widescreen in the engine. The pickup (SDHPA0, variant B) is "
        "gen_weapon's own render, copied into the folder so the overlay finds a complete set.",
    ],
    "_all": [
        "<b>3D weapon and 2D hand together.</b> At 1x they sit well: same palette ramps, same key light, a dark "
        "outline on both. At 2x the difference shows: the hand is four flat bands with creases, the weapon six bands "
        "with soft contours. Item 6 of the brief is applied lightly: every held frame's weapon gets the hand's hard "
        "silhouette (its outer pixels three ramp steps darker, WEAPON_RIM_STEPS), in the 2D frames only; the "
        "installed pickups and every PNG in work/art/weapons/ are untouched. The effect is small, because the 3D "
        "render already darkened its rim; the honest remaining gap is the banding, which would mean re-lighting the "
        "approved weapons.",
        "<b>What is not done.</b> Nothing has been seen in GZDoom (D26): positions follow Doom's arithmetic. The "
        "animations are built from the .zs state lines (tics, A_GunFlash, A_ReFire, the IZh's reload) at 35 tics a "
        "second, without the weapon bob. Poses changed only where D52 says (TT-33, PPSh-41); the RPG-7 and the "
        "IZh-58 would gain most from Blood-style poses next, and that needs the CEO.",
    ],
}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    ap.add_argument("--no-sheet", action="store_true", help="sprites only")
    ap.add_argument("--only", choices=WEAPON_ORDER, action="append", help="render only these weapons")
    args = ap.parse_args(argv)
    out = render_all(tuple(args.only) if args.only else WEAPON_ORDER)
    metrics = save_all(out)
    for k, m in metrics.items():
        print(k, m["lump"], m["size"], m["offsets"], m.get("hand_px_above_bar", ""))
    if not args.no_sheet:
        path = build_sheet(out, args.stamp, SELF_ASSESSMENT)
        print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
