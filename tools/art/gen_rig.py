"""F5 — Reich rifleman as a 3D rig, rendered at Doom's 8 rotations.

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_rig.py               (Windows)
    .venv/bin/python tools/art/gen_rig.py                       (macOS)
    ... gen_rig.py --stamp 2026-10-13_2100   fixes the sheet's timestamp
    ... gen_rig.py --no-sheet                sprites only
    ... gen_rig.py --only A1,H0              a few lumps, for a quick look

What this is. D38 (CEO, 2026-10-13): the rifleman is cell E of the design
sweep (crested helmet, eyeless, calf-length greatcoat, bolt rifle at the
hip), built with the art-director's method: "pose once, render many"
(BESTIARY §2.6). This renders the whole frame set of BESTIARY §3, which is
Doom's POSS layout: walk A-D, aim E, fire F, pain G at 8 rotations; death
H-L and gib M-U at rotation 0. 70 lumps. Draft for the CEO's gate; nothing
goes to assets/.

How it is built. The figure is ~50 primitives (ellipsoids, round cones,
capped cones, rounded boxes) placed on a small skeleton: hips, knees and
ankles solved by two-bone IK towards foot targets, shoulders, elbows and
wrists solved towards the rifle's grips (or free hand targets when he lets
go of it), so a pose is a handful of numbers. Every primitive belongs to a
GROUP (legs, skirt, upper body, arms, head, helmet, rifle) and carries a
rigid transform, so a pose can lean the upper body back, tip the head, roll
the whole figure onto the floor, or throw the helmet and the rifle on
ballistic arcs (the gib). Every primitive carries a MATERIAL (a slice of one
palette ramp, the same slices as gen_enemy.py) and a base value.

How it is rendered. Orthographic sphere tracing in numpy, 4 rays per pixel
side (16 per pixel), camera pitched PITCH_DEG down, as Doom sprites are
drawn from a little above eye level. Light is fixed to the camera (key from
the top left, as in gen_enemy.py), so every rotation is lit the same way.
Lambert is cut into LIGHT_BANDS bands (no smooth gradients), with a cheap
SDF ambient-occlusion term for the creases and a 3D integer-hash grain on
the cloth, seeded. Reduction to 1x is the majority vote per 4x4 block that
gen_enemy.py uses (every pixel is one primitive, one palette colour), then
two pixel-art passes: a dark contour where something sits in FRONT of a
pixel by more than DEPTH_EDGE units (occlusion edges, not part seams), and
a darker rim on the silhouette. The armband symbol (D12) is the same 7x7
hard stamp as the flat sweep, placed on the band's visible centroid. The
muzzle flash is gen_enemy.py's 2D burst at the projected muzzle, drawn
behind the figure when the muzzle is hidden by his body.

Rotations. Doom picks rotation k when the viewer is (k-1)*45 degrees round
the thing, counter-clockwise from its front: 1 front, 3 the thing's LEFT
side (it faces screen left), 5 back, 7 its right side. Verified against
r_things.c's `rot = (ang - thing->angle + ANG45/2*9) >> 29` by hand, NOT
against the engine. All 8 are rendered as separate lumps (SDRRA1..SDRRA8),
not the 5-drawing mirror pairs (A2A8): the figure is not symmetric (rifle on
the right hip, armband on the left arm) and a mirrored armband would show
the symbol reversed. Eight lumps cost nothing with a rig.

Blood and gore follow BESTIARY §2.1: the Reich bleeds dark olive
(`khaki_olive` 0-4), so the gib is olive, not red; the only red on him
stays the armband (ART-BIBLE §6.3).

NO FONTS. The sprites carry no text and nothing here calls ImageFont; the
sheet is HTML, whose labels are the browser's text, like every HTML preview
(tools/art/sheetlib.py). tests/test_gen_rig.py keeps it so.

Outputs (work/ is gitignored):
    work/art/enemies/rig/SDRR<frame><rot>.png  70 lumps, RGBA, hard alpha,
        palette.json colours only, grAb offsets (body axis, feet sunk
        FEET_SINK px). Standing frames share one 64x72 canvas; death and gib
        frames are wider, because a corpse lies across.
    work/art/enemies/rig/*.gif   walk, attack, pain, death, gib, turntable
    work/art/enemies/rig/metrics.json
    docs/art/previews/<stamp>_F5_reich-rifleman-rig.html   (the sheet)
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import io
import json
import struct
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402  (the approved cell E, its materials, scene helpers)
import sheetlib  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "rig"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"

SPRITE = "SDRR"                 # BESTIARY §3, MOD-SPEC §6.3
SEED = 38                       # D38; cloth grain and the gib's chunks
SS = 4                          # rays per pixel side
FEET_SINK = 4                   # as gen_enemy / Freedoom POSSA1 (57 high, top 53)
DOOM_HEIGHT = 56                # actor Height (BESTIARY §3) = px at 1:1
ROTATIONS = 8
TIC_MS = 1000 / 35              # Doom runs at 35 tics a second


@dataclass(frozen=True)
class Canvas:
    w: int
    h: int
    cx: int                     # body axis column (grAb x)
    foot_row: int               # the sole line, world y = 0


STAND = Canvas(64, 72, 32, 68)  # every standing frame: one canvas, one grAb
AIM = Canvas(96, 72, 48, 68)    # the aimed rifle reaches 40 px out in profile
DEATH = Canvas(96, 80, 48, 72)  # a corpse lies across; the dropped rifle lands nearer the camera
GIB = Canvas(96, 88, 48, 80)    # the helmet flies higher than his head; chunks land nearer the camera

PITCH_DEG = 9.0                 # camera looks this far down
T0 = 80.0                       # ray origin distance in front of the model
T_SPAN = 56.0                   # rays march T0 +- T_SPAN
MAX_STEPS = 110
HIT_EPS = 0.02
STEP_SCALE = 0.85               # under-relax: ellipsoids are not exact SDFs
CULL_MARGIN = 1.5               # bounding-sphere distance used when farther than this
NORMAL_H = 0.12
AO_DIST = 1.4
AO_WEIGHT = 0.35
LIGHT_BANDS = 5                 # Lambert quantised to this many bands
LIGHT = np.array([-0.72, 0.55, 0.45])     # world: x right, y up, z towards camera
LIGHT = LIGHT / np.linalg.norm(LIGHT)
SHADE_GAIN = 0.80               # value swing of the banded light
VERTICAL_FALLOFF = 0.10         # lower body a little darker
GRAIN = 0.02                    # cloth grain amplitude (value units)
GRAIN_CELL = 1.25               # world units per grain cell
VALUE_SHIFT = -0.26             # whole figure darker: the flat cell E's body luma (~65)
COVER_MIN = 7                   # of 16 sub-pixels, below this a pixel is transparent
DEPTH_EDGE = 1.4                # a neighbour this much nearer draws a contour on us
CONTOUR_STEPS = 2
RIM_STEPS = 3
ARMBAND_MIN_PX = 6              # visible band pixels needed before the symbol is stamped
FLASH_SIZE = 6.0                # as gen_enemy's rifle flash

# ================================================================ materials
M = flat.Material
MATERIALS: dict[str, flat.Material] = {
    **flat.MATERIALS,
    "band": M("flag_red", 4, 11),
    "gore": M("khaki_olive", 0, 4, black_floor=True),     # BESTIARY §2.1: olive blood
}
MAT_NAMES = list(MATERIALS)
MAT_ID = {n: i for i, n in enumerate(MAT_NAMES)}
FLAT_MATERIALS = {"flash_out", "flash_in", "flash_core", "button"}
NO_SHIFT = FLAT_MATERIALS | {"flesh", "crest", "band"}    # keep their own value: face and crest read
CLOTH = {"coat", "coat_dark", "helmet", "crest"}


# ============================================================ SDF primitives
def _len(v: np.ndarray) -> np.ndarray:
    return np.sqrt(np.einsum("ij,ij->i", v, v))


@dataclass
class Prim:
    kind: str                   # "ellipsoid" | "roundcone" | "cappedcone" | "box"
    mat: str
    base: float
    a: np.ndarray               # centre (ellipsoid, box, cappedcone) or start (roundcone)
    b: np.ndarray | None = None  # roundcone end
    r: np.ndarray | float = 1.0  # radii (ellipsoid), half extents (box)
    r1: float = 0.0
    r2: float = 0.0
    h: float = 0.0              # cappedcone half height
    scale: np.ndarray = field(default_factory=lambda: np.ones(3))  # cappedcone anisotropy
    rot: np.ndarray | None = None   # box/cappedcone local frame (columns = local axes)
    rnd: float = 0.0            # box rounding
    clip: list = field(default_factory=list)  # [(normal, offset)]: keep n.p <= offset
    cut: list = field(default_factory=list)   # boxes subtracted: [(centre, half)]
    tag: str = ""
    grp: str = ""               # rig group (module docstring)
    xm: np.ndarray = field(default_factory=lambda: np.eye(3))    # rigid transform:
    xt: np.ndarray = field(default_factory=lambda: np.zeros(3))  # world = xm @ local + xt

    def _local_bound(self) -> tuple[np.ndarray, float]:
        if self.kind == "roundcone":
            c = (self.a + self.b) / 2
            return c, float(np.linalg.norm(self.b - self.a) / 2 + max(self.r1, self.r2))
        if self.kind == "ellipsoid":
            return self.a, float(np.max(self.r))
        if self.kind == "cappedcone":
            return self.a, float(np.hypot(self.h, max(self.r1, self.r2)) * np.max(self.scale))
        return self.a, float(np.linalg.norm(self.r) + self.rnd)

    def bound(self) -> tuple[np.ndarray, float]:
        c, r = self._local_bound()
        return self.xm @ c + self.xt, r

    def sd(self, p: np.ndarray) -> np.ndarray:
        p = (p - self.xt) @ self.xm          # world -> local (xm is a rotation)
        k = self.kind
        if k == "ellipsoid":
            q = p - self.a
            k0 = _len(q / self.r)
            k1 = np.maximum(_len(q / (self.r * self.r)), 1e-9)
            d = k0 * (k0 - 1.0) / k1
        elif k == "roundcone":
            d = _sd_round_cone(p, self.a, self.b, self.r1, self.r2)
        elif k == "cappedcone":
            q = p - self.a
            if self.rot is not None:
                q = q @ self.rot
            q = q / self.scale
            d = _sd_capped_cone(q, self.h, self.r1, self.r2) * float(np.min(self.scale))
        else:
            q = p - self.a
            if self.rot is not None:
                q = q @ self.rot
            qq = np.abs(q) - (self.r - self.rnd)
            d = _len(np.maximum(qq, 0)) + np.minimum(qq.max(axis=1), 0) - self.rnd
        for n, off in self.clip:
            d = np.maximum(d, p @ n - off)
        for c, half in self.cut:
            qq = np.abs(p - c) - half
            dbox = _len(np.maximum(qq, 0)) + np.minimum(qq.max(axis=1), 0)
            d = np.maximum(d, -dbox)
        return d


def _sd_round_cone(p, a, b, r1, r2):
    """Inigo Quilez's exact round cone between a (r1) and b (r2)."""
    ba = b - a
    l2 = float(ba @ ba)
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    v = pa * l2 - np.outer(y, ba)
    x2 = np.einsum("ij,ij->i", v, v)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d_top = np.sqrt(x2 + z2) * il2 - r2
    d_bot = np.sqrt(x2 + y2) * il2 - r1
    d_mid = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1
    return np.where(np.sign(z) * a2 * z2 > k, d_top, np.where(np.sign(y) * a2 * y2 < k, d_bot, d_mid))


def _sd_capped_cone(p, h, r1, r2):
    """Quilez's capped cone along y, from -h (radius r1) to +h (radius r2)."""
    qx = np.hypot(p[:, 0], p[:, 2])
    qy = p[:, 1]
    k1 = np.array([r2, h])
    k2 = np.array([r2 - r1, 2 * h])
    cax = qx - np.minimum(qx, np.where(qy < 0, r1, r2))
    cay = np.abs(qy) - h
    t = np.clip(((k1[0] - qx) * k2[0] + (k1[1] - qy) * k2[1]) / float(k2 @ k2), 0, 1)
    cbx = qx - k1[0] + k2[0] * t
    cby = qy - k1[1] + k2[1] * t
    s = np.where((cbx < 0) & (cay < 0), -1.0, 1.0)
    return s * np.sqrt(np.minimum(cax * cax + cay * cay, cbx * cbx + cby * cby))


def V(*xs) -> np.ndarray:
    return np.array(xs, dtype=np.float64)


def ellipsoid(mat, base, c, r, **kw) -> Prim:
    return Prim("ellipsoid", mat, base, V(*c), r=V(*r), **kw)


def rcone(mat, base, a, b, r1, r2=None, **kw) -> Prim:
    return Prim("roundcone", mat, base, np.asarray(a, float), b=np.asarray(b, float),
                r1=r1, r2=r1 if r2 is None else r2, **kw)


def ccone(mat, base, y0, y1, r0, r1, kz=1.0, x=0.0, z=0.0, **kw) -> Prim:
    """Vertical capped cone from y0 (radius r0) to y1 (radius r1), depth
    squeezed by kz (an elliptic section: wider than deep)."""
    return Prim("cappedcone", mat, base, V(x, (y0 + y1) / 2, z), h=(y1 - y0) / 2, r1=r0, r2=r1,
                scale=V(1.0, 1.0, kz), **kw)


def box(mat, base, c, half, rnd=0.0, rot=None, **kw) -> Prim:
    return Prim("box", mat, base, V(*c), r=V(*half), rnd=rnd, rot=rot, **kw)


def rot_x(deg: float) -> np.ndarray:
    """Positive tips the top of the figure BACK (towards -z)."""
    a = np.deg2rad(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, s], [0, -s, c]])


def rot_z(deg: float) -> np.ndarray:
    """Positive tips the top towards +x: the figure's LEFT, screen right at rotation 1."""
    a = np.deg2rad(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])


def rot_y(deg: float) -> np.ndarray:
    """Positive turns +x towards +z (towards the camera at rotation 1)."""
    a = np.deg2rad(deg)
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])


def transform(prims: list[Prim], anchors: dict, groups: set[str], R: np.ndarray,
              pivot, offset=(0.0, 0.0, 0.0)) -> None:
    """Rotate the given groups by R about pivot, then move them by offset.
    Anchors are (point, group) pairs and follow their group."""
    pivot = np.asarray(pivot, float)
    offset = np.asarray(offset, float)
    for p in prims:
        if p.grp in groups:
            p.xm = R @ p.xm
            p.xt = R @ (p.xt - pivot) + pivot + offset
    for k, (pt, g) in list(anchors.items()):
        if g in groups:
            anchors[k] = (R @ (pt - pivot) + pivot + offset, g)


# ==================================================================== rig
def two_bone(root, target, a, b, pole) -> tuple[np.ndarray, np.ndarray]:
    """Joint and end of a two-bone chain reaching for `target`, bending
    towards `pole`. Returns (joint, end); the end falls short if out of reach."""
    root, target, pole = (np.asarray(v, float) for v in (root, target, pole))
    d = target - root
    L = float(np.linalg.norm(d))
    n = d / L
    L = min(max(L, abs(a - b) + 1e-3), a + b - 1e-3)
    x = (a * a - b * b + L * L) / (2 * L)
    hgt = np.sqrt(max(a * a - x * x, 0.0))
    pp = pole - (pole @ n) * n
    pp = pp / (np.linalg.norm(pp) or 1.0)
    joint = root + n * x + pp * hgt
    return joint, root + n * L


ANKLE_Y = 2.2


@dataclass(frozen=True)
class Pose:
    key: str
    title: str
    foot_l: tuple = (3.5, ANKLE_Y, 0.4)   # ankle targets, model space (x = figure's LEFT, z = forward)
    foot_r: tuple = (-3.5, ANKLE_Y, 0.0)
    bob: float = 0.0             # pelvis and everything above it
    carry: str = "hip"           # "hip" | "aim" | "free" (he has let go of the rifle)
    stride: float = 0.0          # 0..1, opens the coat skirt
    rifle_tilt: float = 0.0      # small per-frame wobble of the carried rifle
    lean: float = 0.0            # degrees, upper body back about the waist
    head_pitch: float = 0.0      # degrees, chin up about the neck
    hand_l: tuple | None = None  # carry "free": hand targets, before lean
    hand_r: tuple | None = None
    rifle_at: tuple | None = None  # carry "free": (butt, along, up), final model space
    roll: float = 0.0            # degrees, the whole figure falls to his left about ROLL_PIVOT
    flash: bool = False
    canvas: Canvas = STAND


STEP = dict(foot_l=(3.5, ANKLE_Y, 0.4), foot_r=(-3.5, ANKLE_Y, 0.0))
AIMING = dict(foot_l=(3.8, ANKLE_Y, -1.6), foot_r=(-3.6, ANKLE_Y, 2.2), bob=-0.4, carry="aim", stride=0.4,
              canvas=AIM)
FLOOR_RIFLE = ((-17.0, 1.5, 3.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
POSES = {
    "A": Pose("A", "idle / walk contact", **STEP),
    "B": Pose("B", "left foot forward", (3.3, ANKLE_Y, 6.0), (-3.4, ANKLE_Y + 1.6, -5.2), -0.9,
              "hip", 1.0, 0.03),
    "C": Pose("C", "right leg passing", (3.5, ANKLE_Y, 0.2), (-3.6, ANKLE_Y + 2.6, 1.2), 0.4,
              "hip", 0.3, 0.0),
    "D": Pose("D", "right foot forward", (3.4, ANKLE_Y + 1.6, -5.2), (-3.3, ANKLE_Y, 6.0), -0.9,
              "hip", 1.0, -0.03),
    "E": Pose("E", "aim", **AIMING),
    "F": Pose("F", "fire", **AIMING, flash=True),
    "G": Pose("G", "pain", (3.6, ANKLE_Y, 0.8), (-3.4, ANKLE_Y, -3.0), -0.8, "hip", 0.3, 0.22,
              lean=13.0, head_pitch=22.0),
    "H": Pose("H", "hit", (3.6, ANKLE_Y, 1.2), (-3.4, ANKLE_Y, -3.6), -1.0, "free", 0.4,
              lean=22.0, head_pitch=32.0, hand_l=(12.0, 46.0, 2.0), hand_r=(-11.0, 33.0, 5.0),
              rifle_at=((-8.0, 22.0, 6.0), (0.85, -0.35, 0.4), (0.0, 1.0, 0.0)), canvas=DEATH),
    "I": Pose("I", "knees go", (3.6, ANKLE_Y, 1.2), (-3.4, ANKLE_Y, -1.0), -7.0, "free", 0.6,
              lean=26.0, head_pitch=30.0, hand_l=(12.0, 42.0, 1.0), hand_r=(-9.0, 30.0, 7.0),
              rifle_at=((-12.0, 9.0, 7.0), (0.94, -0.25, 0.2), (0.0, 1.0, 0.0)), roll=14.0, canvas=DEATH),
    "J": Pose("J", "falling", (3.6, ANKLE_Y, 1.2), (-3.4, ANKLE_Y, 0.0), -11.0, "free", 0.8,
              lean=18.0, head_pitch=25.0, hand_l=(13.0, 38.0, 0.0), hand_r=(-7.0, 28.0, 8.0),
              rifle_at=((-16.0, 2.5, 3.0), (0.99, -0.15, 0.0), (0.0, 1.0, 0.0)), roll=42.0, canvas=DEATH),
    "K": Pose("K", "hits the floor", (3.6, ANKLE_Y, 1.0), (-3.4, ANKLE_Y, 0.5), -9.0, "free", 0.6,
              lean=8.0, head_pitch=10.0, hand_l=(12.0, 40.0, -2.0), hand_r=(-6.0, 30.0, 8.0),
              rifle_at=FLOOR_RIFLE, roll=74.0, canvas=DEATH),
    "L": Pose("L", "dead", (3.4, ANKLE_Y, 0.6), (-3.6, ANKLE_Y, 1.4), -2.0, "free", 0.4,
              head_pitch=-10.0, hand_l=(10.0, 30.0, 3.0), hand_r=(-9.0, 30.0, 6.0),
              rifle_at=FLOOR_RIFLE, roll=90.0, canvas=DEATH),
}
ROLL_PIVOT = V(3.5, 0.0, 0.0)   # his left sole: he falls to his left over it
SLIDE = 30.0                    # x shift at a full fall, so the corpse lies across the axis
FLOOR_STEP = 1.0                # grid of the upward rays that find the body's lowest point

HIP_Y = 26.2
THIGH, SHIN = 12.6, 11.6
UPPER_ARM, FOREARM = 9.6, 9.0
RIFLE_LEN = 34.0
HEM_Y, WAIST_Y = 11.2, 29.0
HEM_R, WAIST_R = 9.9, 7.2
SKIRT_KZ = 0.72
TORSO_KZ = 0.66
TORSO_R0, TORSO_R1 = 7.3, 7.9     # waist and chest half widths
SHOULDER_X = 7.0
NECK = V(0.0, 41.5, -0.4)

UPPER = {"upper", "arm", "head", "helmet"}       # what leans with the torso
ALL_BODY = UPPER | {"leg_l", "leg_r", "skirt", "stump"}


def coat_radius(y: float) -> float:
    """The greatcoat skirt's half width at height y (between hem and waist)."""
    t = (y - HEM_Y) / (WAIST_Y - HEM_Y)
    return HEM_R + (WAIST_R - HEM_R) * t


def rifle_frame(pose: Pose, up: np.ndarray):
    """Butt position and unit axes (along, up, side) of the rifle."""
    if pose.carry == "hip":
        butt = V(-10.6, 26.2 + pose.bob, 2.8)
        u = V(0.89, 0.04 + pose.rifle_tilt, 0.45)
    elif pose.carry == "aim":
        butt = V(-4.8, 39.0 + pose.bob, 3.8)
        u = V(0.06, np.tan(np.deg2rad(PITCH_DEG)), 1.0)   # at the viewer's eye
    else:
        butt, u, up = (np.asarray(x, float) for x in pose.rifle_at)
    u = u / np.linalg.norm(u)
    v = up - (up @ u) * u
    v = v / np.linalg.norm(v)
    w = np.cross(u, v)
    return butt, u, v, w


def build_model(pose: Pose) -> tuple[list[Prim], dict]:
    """The rifleman as primitives in model space (feet on y=0, facing +z,
    +x the figure's LEFT), posed. Returns (prims, anchors)."""
    P: list[Prim] = []
    bob = pose.bob
    up = V(0, 1, 0)
    anchors: dict = {}

    def add(grp: str, prim: Prim) -> Prim:
        prim.grp = grp
        P.append(prim)
        return prim

    # ---------------------------------------------------------------- legs
    for side, foot, grp in ((1, pose.foot_l, "leg_l"), (-1, pose.foot_r, "leg_r")):
        hip = V(side * 3.4, HIP_Y + bob, 0.0)
        knee, ankle = two_bone(hip, foot, THIGH, SHIN, V(0, 0, 1))
        add(grp, rcone("coat_dark", 0.35, hip, knee, 2.7, 2.3))           # breeches, mostly hidden
        add(grp, rcone("leather", 0.55, knee, ankle, 2.4, 2.05))          # jackboot shaft
        add(grp, box("leather", 0.30, (ankle[0], ankle[1] - 1.15, ankle[2] + 1.3),
                     (1.6, 1.1, 3.0), rnd=0.6))                           # foot

    # ---------------------------------------------------------------- coat
    open_kz = SKIRT_KZ * (1.0 + 0.16 * pose.stride)
    hem = HEM_Y + 0.2 * pose.stride + min(bob, 0.0) * 0.35   # a crouch bunches the skirt down
    add("skirt", ccone("coat", 0.50, hem, WAIST_Y + bob, HEM_R, WAIST_R, kz=open_kz, tag="skirt"))
    # greatcoat folds: shallow ridges on the skirt, so the banded light has
    # something to catch (angle round the body from the front, in degrees)
    for ang in (-62, -28, 28, 62, 150, 210):
        a = np.deg2rad(ang)

        def on_skirt(y, out=0.25, a=a):
            r = coat_radius(y)
            return V(np.sin(a) * (r + out), y, np.cos(a) * (r + out) * open_kz)
        add("skirt", rcone("coat", 0.46, on_skirt(hem + 0.9, -0.2), on_skirt(WAIST_Y - 5.0 + bob, -0.9),
                           1.15, 0.5))
    for zs in (1, -1):    # front opening and back pleat: dark seams on the skirt
        z0 = zs * coat_radius(hem + 0.6) * open_kz
        z1 = zs * coat_radius(WAIST_Y - 1.4) * open_kz
        add("skirt", rcone("coat_dark", 0.15, (0, hem + 0.7, z0 + zs * 0.05),
                           (0, WAIST_Y - 1.2 + bob, z1 + zs * 0.05), 0.45))
    for y in (24.0, 19.5):
        r = coat_radius(y) * open_kz
        for side in (1, -1):
            x = side * 2.6
            add("skirt", ellipsoid("button", 0.35, (x, y + bob * 0.5, r * np.sqrt(1 - (x / coat_radius(y)) ** 2) + 0.2),
                                   (0.5, 0.5, 0.4)))
    # torso: a capped cone squashed in depth, broad at the chest
    ty0, ty1 = 28.8 + bob, 40.0 + bob
    add("upper", Prim("cappedcone", "coat", 0.52, V(0, (ty0 + ty1) / 2, -0.2), h=(ty1 - ty0) / 2,
                      r1=TORSO_R0, r2=TORSO_R1, scale=V(1.0, 1.0, TORSO_KZ), tag="torso"))
    add("upper", ellipsoid("coat", 0.50, (0, 39.6 + bob, -0.3), (8.6, 2.7, 4.8)))      # shoulder line
    for side in (1, -1):
        add("upper", ellipsoid("coat", 0.54, (side * SHOULDER_X, 39.4 + bob, -0.3), (3.1, 2.7, 3.2)))
        add("upper", ellipsoid("coat_dark", 0.40, (side * (SHOULDER_X - 1.2), 41.6 + bob, -0.3),
                               (2.4, 0.7, 2.6)))                                     # shoulder strap
    add("upper", ccone("coat", 0.44, 39.6 + bob, 43.6 + bob, 5.6, 4.6, kz=0.9, z=-0.4,
                       cut=[(V(0, 43.4 + bob, 5.0), V(1.5, 2.4, 3.0))]))             # raised collar
    # belt, buckle, pouches, Y-straps, buttons
    add("upper", ccone("leather", 0.45, 27.9 + bob, 29.9 + bob, TORSO_R0 + 0.3, TORSO_R0 + 0.25, kz=0.74,
                       tag="belt"))
    belt_z = (TORSO_R0 + 0.3) * 0.74
    add("upper", box("metal", 0.55, (0, 28.9 + bob, belt_z + 0.1), (1.0, 0.95, 0.35), tag="belt"))
    for side in (1, -1):
        add("upper", box("leather", 0.50, (side * 3.6, 27.0 + bob, belt_z - 0.2), (1.4, 1.6, 0.9), rnd=0.3,
                         tag="belt"))

    def torso_z(x, y):
        r = TORSO_R0 + (TORSO_R1 - TORSO_R0) * (y - ty0) / (ty1 - ty0)
        return TORSO_KZ * np.sqrt(max(r * r - x * x, 0.0)) - 0.2

    for side in (1, -1):
        a = (side * 3.8, 39.2 + bob)
        b = (side * 2.4, 30.2 + bob)
        add("upper", rcone("leather", 0.40, (a[0], a[1], torso_z(*a) + 0.35), (b[0], b[1], torso_z(*b) + 0.3), 0.5))
        add("upper", rcone("leather", 0.35, (a[0], a[1], -torso_z(*a) - 0.15),
                           (0.0, 31.0 + bob, -torso_z(0, 31.0 + bob) - 0.3), 0.5))
        for y in (32.0, 35.0):
            add("upper", ellipsoid("button", 0.35, (side * 2.6, y + bob, torso_z(side * 2.6, y + bob) + 0.25),
                                   (0.5, 0.5, 0.4)))

    # ---------------------------------------------------------------- head
    head_off = V(0, bob, 0)
    if pose.carry == "aim":
        head_off = head_off + V(-1.2, -0.7, 0.7)     # cheek down on the stock
    hp = lambda x, y, z: tuple(V(x, y, z) + head_off)  # noqa: E731
    add("head", rcone("flesh", 0.30, V(0, 41.0 + bob, -0.4), V(0, 45.0, 0.2) + head_off, 1.8, 1.6))
    add("head", ellipsoid("flesh", 0.62, hp(0, 46.5, 1.0), (3.2, 3.9, 3.3)))           # skull and cheeks
    add("head", ellipsoid("flesh", 0.52, hp(0, 44.0, 1.7), (2.2, 2.0, 2.4)))           # narrow jaw
    add("head", ellipsoid("void", 0.0, hp(0, 47.9, 3.55), (2.9, 0.95, 1.1)))           # no eyes: a slot of dark
    add("head", ellipsoid("void", 0.35, hp(0, 44.3, 3.75), (1.1, 0.33, 0.5)))          # mouth
    # crested helmet (cell E): a tall narrow ogive with a light ridge, a ledge
    # where it meets the skirt, and the skirt flaring out and down into two
    # blades that frame the jaw. The flare is BESTIARY §3's 16-px tell.
    c = V(*hp(0, 0, 0))
    hy = head_off[1]
    add("helmet", ellipsoid("helmet", 0.62, hp(0, 50.0, -0.3), (5.0, 7.9, 5.6),
                            clip=[(V(0, -1, 0), -(49.6 + hy))]))
    add("helmet", ellipsoid("crest", 0.72, hp(0, 51.4, -0.9), (1.05, 7.1, 6.8),
                            clip=[(V(0, -1, 0), -(50.4 + hy))]))
    add("helmet", ccone("helmet", 0.42, 49.2 + hy, 50.4 + hy, 6.6, 6.2, kz=1.0, x=c[0], z=-0.4 + c[2],
                        clip=[(V(0, 0, 1), 4.6 + c[2])]))                              # the ledge
    add("helmet", ccone("helmet", 0.30, 43.6 + hy, 49.4 + hy, 9.2, 6.3, kz=0.98, x=c[0], z=-0.7 + c[2],
                        clip=[(V(0, 0, 1), 3.0 + c[2])],
                        cut=[(c + V(0, 45.6, 5.5), V(4.4, 4.8, 4.2))]))               # skirt and blades
    add("helmet", ellipsoid("helmet", 0.40, hp(0, 49.5, 4.3), (4.6, 0.8, 2.3)))       # brim over the eyes
    anchors["head"] = (c + V(0, 47, 1), "head")
    anchors["helmet"] = (c + V(0, 49, -0.4), "helmet")

    # ---------------------------------------------------------------- rifle
    butt, u, v, w = rifle_frame(pose, up)
    at = lambda s, hh=0.0, k=0.0: butt + u * s + v * hh + w * k  # noqa: E731
    add("rifle", rcone("wood", 0.48, at(0.6, -0.5), at(10.0, 0.1), 1.45, 0.85))          # stock
    add("rifle", rcone("wood", 0.55, at(10.0, 0.1), at(26.0, 0.0), 0.85, 0.75))          # fore-end
    add("rifle", rcone("metal", 0.50, at(8.8, 0.55), at(RIFLE_LEN, 0.45), 0.55, 0.42))  # barrel and receiver
    add("rifle", rcone("metal", 0.45, at(9.0, 0.5), at(14.0, 0.5), 0.78, 0.7))
    add("rifle", ellipsoid("metal", 0.65, tuple(at(11.2, 0.5, -1.7)), (0.65, 0.65, 0.65)))   # bolt knob
    anchors["muzzle"] = (at(RIFLE_LEN + 0.4, 0.45), "rifle")
    anchors["rifle"] = (at(RIFLE_LEN / 2, 0.0), "rifle")

    # ---------------------------------------------------------------- arms
    if pose.carry == "free":
        grips = {1: V(*pose.hand_l), -1: V(*pose.hand_r)}
    else:
        grips = {-1: at(6.0 if pose.carry == "hip" else 5.6, -0.6),     # right hand: wrist of the stock
                 1: at(19.0 if pose.carry == "hip" else 15.0, -0.6)}     # left hand: under the fore-end
    for side in (1, -1):
        sh = V(side * (SHOULDER_X + 0.2), 39.4 + bob, -0.4)
        pole = V(side * 1.0, -0.4, -0.7)
        elbow, wrist = two_bone(sh, grips[side], UPPER_ARM, FOREARM, pole)
        add("arm", rcone("coat", 0.52, sh, elbow, 2.65, 2.3))
        add("arm", rcone("coat", 0.48, elbow, wrist, 2.3, 2.0))
        fd = (wrist - elbow) / np.linalg.norm(wrist - elbow)
        add("arm", rcone("coat_dark", 0.40, wrist - fd * 2.4, wrist - fd * 0.9, 2.25, 2.15))  # turned-back cuff
        add("arm", ellipsoid("flesh", 0.50, tuple(wrist + fd * 0.9 - v * 0.2), (1.25, 1.45, 1.25)))
        if side == 1:                  # armband: the figure's LEFT upper arm (D12)
            add("arm", rcone("band", 0.55, sh + (elbow - sh) * 0.30, sh + (elbow - sh) * 0.62, 2.78, 2.65,
                             tag="armband"))

    # ------------------------------------------------------------- posing
    neck = NECK + V(0, bob, 0)
    if pose.head_pitch:
        transform(P, anchors, {"head", "helmet"}, rot_x(pose.head_pitch), neck)
    if pose.lean:
        waist = V(0, WAIST_Y + bob, 0)
        carried = {"rifle"} if pose.carry != "free" else set()
        transform(P, anchors, UPPER | carried, rot_x(pose.lean), waist)
        transform(P, anchors, {"skirt"}, rot_x(pose.lean * 0.3), waist)
    if pose.roll:
        body = ALL_BODY | ({"rifle"} if pose.carry != "free" else set())
        slide = V(-SLIDE * np.sin(np.deg2rad(pose.roll)), 0, 0)
        transform(P, anchors, body, rot_z(pose.roll), ROLL_PIVOT, slide)
        rest_on_floor(P, anchors, body)
    return P, anchors


def lowest_y(prims: list[Prim]) -> float:
    """The lowest surface point of the primitives, found by sphere tracing
    straight up from below on a FLOOR_STEP grid."""
    scene = Scene(prims)
    lo = np.min([c - R for c, R in scene.bounds], axis=0)
    hi = np.max([c + R for c, R in scene.bounds], axis=0)
    xs = np.arange(lo[0], hi[0] + FLOOR_STEP, FLOOR_STEP)
    zs = np.arange(lo[2], hi[2] + FLOOR_STEP, FLOOR_STEP)
    gx, gz = np.meshgrid(xs, zs)
    o = np.stack([gx.ravel(), np.full(gx.size, lo[1] - 1.0), gz.ravel()], axis=1)
    y = o[:, 1].copy()
    alive = np.ones(len(o), bool)
    best = np.inf
    for _ in range(MAX_STEPS):
        idx = np.nonzero(alive)[0]
        if not len(idx):
            break
        d = scene.sdf(np.stack([o[idx, 0], y[idx], o[idx, 2]], axis=1))
        got = d < HIT_EPS
        if got.any():
            best = min(best, float(y[idx[got]].min()))
        y[idx] += np.maximum(d * STEP_SCALE, HIT_EPS * 0.5)
        alive[idx[got | (y[idx] > hi[1] + 1.0)]] = False
    return best


def rest_on_floor(prims: list[Prim], anchors: dict, groups: set[str]) -> None:
    """Lift (or drop) the given groups so their lowest point touches y = 0."""
    part = [p for p in prims if p.grp in groups]
    transform(prims, anchors, groups, np.eye(3), V(0, 0, 0), V(0, -lowest_y(part), 0))


# ===================================================================== gib
# XDeath, frames M-U (BESTIARY §3). M is the body still whole with the
# chest giving way; from N the upper body is a cloud of chunks on ballistic
# arcs, the helmet and the rifle fly whole, and the legs stand, buckle and
# fall. Times are seconds after the burst, chosen so the chunks land on S-T.
GIB_FRAMES = "MNOPQRSTU"
GIB_T = {"N": 0.05, "O": 0.18, "P": 0.32, "Q": 0.46, "R": 0.62, "S": 0.80, "T": 1.0, "U": 1.4}
GRAVITY = 160.0                 # units / s^2, picked for the landing frames, not physics
N_CHUNKS = 18
CHUNK_MATS = ("gore", "gore", "gore", "flesh", "flesh", "coat", "coat", "coat_dark")
GIB_POSE = Pose("M", "chest bursts", (3.6, ANKLE_Y, 0.8), (-3.4, ANKLE_Y, -3.0), -0.8, "hip", 0.3, 0.2,
                lean=10.0, head_pitch=18.0, canvas=GIB)


def _land_time(y0: float, vy: float, rest: float) -> float:
    """When a body thrown up at vy from y0 comes down to height `rest`."""
    return (vy + np.sqrt(vy * vy + 2 * GRAVITY * max(y0 - rest, 0.0))) / GRAVITY


def _ballistic(p0: np.ndarray, v: np.ndarray, t: float, rest: float) -> tuple[np.ndarray, bool]:
    tl = _land_time(p0[1], v[1], rest)
    tt = min(t, tl)
    p = p0 + v * tt + V(0, -0.5 * GRAVITY * tt * tt, 0)
    if t >= tl:
        p[1] = rest
    return p, t >= tl


def chunks(t: float, seed: int = SEED) -> list[Prim]:
    """The upper body as N_CHUNKS lumps of coat, flesh and olive gore,
    `t` seconds after the burst; landed ones flatten on the floor."""
    rng = np.random.default_rng(seed + 1)
    out = []
    for i in range(N_CHUNKS):
        p0 = V(rng.uniform(-6, 6), rng.uniform(30, 46), rng.uniform(-3, 3))
        side = np.sign(p0[0]) or 1.0
        v = V(side * rng.uniform(6, 30), rng.uniform(8, 42), rng.uniform(-6, 3))
        r = V(rng.uniform(1.1, 2.8), rng.uniform(1.0, 2.2), rng.uniform(1.1, 2.6))
        mat = CHUNK_MATS[i % len(CHUNK_MATS)]
        rest = r[1] * 0.5
        p, landed = _ballistic(p0, v, t, rest)
        if landed:
            r = r * V(1.35, 0.5, 1.35)
        out.append(ellipsoid(mat, 0.45 if mat != "flesh" else 0.40, tuple(p), tuple(r), grp="chunk"))
    return out


def build_gib(frame: str, seed: int = SEED) -> tuple[list[Prim], dict]:
    if frame == "M":
        prims, anchors = build_model(GIB_POSE)
        # the chest gives way: olive gore pushing out of the coat front
        rng = np.random.default_rng(seed + 2)
        extra = []
        for _ in range(6):
            p = V(rng.uniform(-4.5, 4.5), rng.uniform(31, 39) + GIB_POSE.bob, rng.uniform(4.6, 5.8))
            r = V(*rng.uniform(1.2, 2.4, 3))
            extra.append(ellipsoid("gore", 0.35, tuple(p), tuple(r), grp="upper"))
        prims.extend(extra)
        waist = V(0, WAIST_Y + GIB_POSE.bob, 0)
        transform(extra, {}, {"upper"}, rot_x(GIB_POSE.lean), waist)
        return prims, anchors
    t = GIB_T[frame]
    k = float(np.clip((t - 0.25) / 0.55, 0, 1))          # the legs: stand, buckle, fall
    k = k * k * (3 - 2 * k)
    legs = replace(GIB_POSE, lean=0.0, head_pitch=0.0, bob=-0.8 - 10.0 * k, roll=0.0)
    prims, anchors = build_model(legs)
    base, _ = build_model(GIB_POSE)
    keep = [p for p in prims if p.grp in {"leg_l", "leg_r", "skirt"} or p.tag == "belt"]
    for p in keep:
        if p.tag == "belt":
            p.grp = "stump"
    bob = legs.bob
    rng = np.random.default_rng(seed + 3)
    stump = [ellipsoid("gore", 0.30, (0, WAIST_Y + bob + 0.8, 0), (6.4, 2.4, 4.4), grp="stump")]
    for _ in range(4):
        stump.append(ellipsoid("gore", 0.40, (rng.uniform(-4, 4), WAIST_Y + bob + rng.uniform(1.0, 3.2),
                                              rng.uniform(-2, 2)), tuple(rng.uniform(1.2, 2.2, 3)), grp="stump"))
    keep += stump
    if k > 0:
        roll = 88.0 * k
        slide = V(-SLIDE * 0.45 * np.sin(np.deg2rad(roll)), 0, 0)
        transform(keep, {}, {"leg_l", "leg_r", "skirt", "stump"}, rot_z(roll), ROLL_PIVOT, slide)
        rest_on_floor(keep, {}, {"leg_l", "leg_r", "skirt", "stump"})
    if t >= 0.62:                                          # a pool spreads under him
        g = min((t - 0.62) / 0.6, 1.0)
        keep.append(ellipsoid("gore", 0.20, (2.0, 0.25, 1.5), (8.0 + 10.0 * g, 0.4, 3.0 + 2.0 * g), grp="pool"))
    keep += chunks(t, seed)
    # the helmet and the rifle fly whole, spinning, and lie where they land
    anc = {}
    for grp, v, spin, rest, lie in (("helmet", V(9.0, 52.0, 0.0), -420.0, 4.6, -100.0),
                                    ("rifle", V(-14.0, 26.0, 0.0), 260.0, 1.6, 0.0)):
        parts = [p for p in base if p.grp == grp]
        pts = [b[0] for b in (q.bound() for q in parts)]
        c0 = np.mean(pts, axis=0)
        p, landed = _ballistic(c0, v, t, rest)
        ang = lie if landed else spin * t
        R = rot_z(ang)
        if landed and grp == "rifle":       # it lies flat along the floor, behind the legs
            u = parts[0].b - parts[0].a
            R = rot_y(-np.degrees(np.arctan2(u[2], u[0])))
            p[2] = -2.0
        transform(parts, anc, {grp}, R, c0, p - c0)
        keep += parts
    return keep, anchors


# ================================================================ renderer
def yaw_matrix(rotation: int) -> np.ndarray:
    """Model -> world rotation for Doom rotation 1..8 (module docstring);
    rotation 0 (one image for every angle) is drawn from the front."""
    theta = np.deg2rad((max(rotation, 1) - 1) * 45.0)
    phi = -theta
    c, s = np.cos(phi), np.sin(phi)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def camera() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p = np.deg2rad(PITCH_DEG)
    fwd = V(0, -np.sin(p), -np.cos(p))
    right = V(1, 0, 0)
    up = V(0, np.cos(p), -np.sin(p))
    return fwd, right, up


def project(point_model: np.ndarray, rotation: int, cv: Canvas = STAND) -> tuple[float, float, float]:
    """Model point -> (column, row, ray depth t) on the 1x canvas."""
    fwd, right, up = camera()
    pw = yaw_matrix(rotation) @ point_model
    return cv.cx + float(pw @ right), cv.foot_row - float(pw @ up), T0 + float(pw @ fwd)


class Scene:
    def __init__(self, prims: list[Prim]):
        self.prims = prims
        self.bounds = [p.bound() for p in prims]

    def sdf(self, p: np.ndarray, want_id: bool = False):
        best = np.full(len(p), np.inf)
        bid = np.full(len(p), -1, np.int32)
        for i, (prim, (c, R)) in enumerate(zip(self.prims, self.bounds)):
            dc = _len(p - c) - R
            near = dc < CULL_MARGIN
            d = dc.copy()
            if near.any():
                d[near] = prim.sd(p[near])
            better = d < best
            best = np.where(better, d, best)
            if want_id:
                bid[better] = i
        return (best, bid) if want_id else best


def hash3(cells: np.ndarray, seed: int) -> np.ndarray:
    """Integer hash of 3D cells -> [0,1): platform-independent grain."""
    c = cells.astype(np.int64) & 0xFFFF
    h = (c[:, 0] * 73856093) ^ (c[:, 1] * 19349663) ^ (c[:, 2] * 83492791) ^ (seed * 2654435761)
    h = h & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return (h & 0xFFFF) / 65536.0


def raymarch(prims: list[Prim], rotation: int, cv: Canvas, seed: int = SEED) -> dict:
    """Trace the posed primitives at one rotation. Returns 4x buffers: prim
    id (-1 empty), value 0..1, depth."""
    scene = Scene(prims)
    Rm = yaw_matrix(rotation)             # model -> world
    fwd, right, up = camera()
    cols, rows = [], []
    for c, R in scene.bounds:             # screen rectangle that can hold the figure
        pw = Rm @ c
        cols += [cv.cx + pw @ right - R, cv.cx + pw @ right + R]
        rows += [cv.foot_row - pw @ up - R, cv.foot_row - pw @ up + R]
    c0, c1 = max(0, int(np.floor(min(cols)))), min(cv.w, int(np.ceil(max(cols))) + 1)
    r0, r1 = max(0, int(np.floor(min(rows)))), min(cv.h, int(np.ceil(max(rows))) + 1)
    hs, ws = cv.h * SS, cv.w * SS
    pid = np.full((hs, ws), -1, np.int32)
    val = np.zeros((hs, ws))
    depth = np.full((hs, ws), np.inf)
    yy, xx = np.mgrid[r0 * SS:r1 * SS, c0 * SS:c1 * SS]
    sx = (xx + 0.5) / SS - cv.cx
    sy = cv.foot_row - (yy + 0.5) / SS
    origin_w = (sx.reshape(-1, 1) * right + sy.reshape(-1, 1) * up) - fwd * T0
    o = origin_w @ Rm                      # world -> model is Rm^T: row-vector form
    d = fwd @ Rm
    n = len(o)
    t = np.full(n, T0 - T_SPAN)
    alive = np.ones(n, bool)
    hit = np.zeros(n, bool)
    for _ in range(MAX_STEPS):
        idx = np.nonzero(alive)[0]
        if not len(idx):
            break
        dist = scene.sdf(o[idx] + np.outer(t[idx], d))
        got = dist < HIT_EPS
        hit[idx[got]] = True
        t[idx] += np.where(got, 0.0, np.maximum(dist * STEP_SCALE, HIT_EPS * 0.5))
        gone = t[idx] > T0 + T_SPAN
        alive[idx[got | gone]] = False
    hidx = np.nonzero(hit)[0]
    ph = o[hidx] + np.outer(t[hidx], d)
    _, ids = scene.sdf(ph, want_id=True)
    nrm = np.zeros_like(ph)               # normals, central differences (model space)
    for k in range(3):
        e = np.zeros(3)
        e[k] = NORMAL_H
        nrm[:, k] = scene.sdf(ph + e) - scene.sdf(ph - e)
    nrm /= np.maximum(_len(nrm), 1e-9)[:, None]
    lam = (nrm @ Rm.T) @ LIGHT
    lam_b = np.floor((lam * 0.5 + 0.5) * LIGHT_BANDS).clip(0, LIGHT_BANDS - 1) / (LIGHT_BANDS - 1)
    ao = np.clip(scene.sdf(ph + nrm * AO_DIST) / AO_DIST, 0, 1)
    mats = [prims[i].mat for i in ids]
    base = np.array([prims[i].base for i in ids])
    is_cloth = np.array([m in CLOTH for m in mats])
    shift = np.array([0.0 if m in NO_SHIFT else VALUE_SHIFT for m in mats])
    grain = (hash3(np.floor(ph / GRAIN_CELL), seed) - 0.5) * 2 * GRAIN * is_cloth
    v = (base + shift + SHADE_GAIN * (lam_b - 0.5) - AO_WEIGHT * (1 - ao)
         - VERTICAL_FALLOFF * (0.5 - ph[:, 1] / DOOM_HEIGHT) + grain)
    rr = yy.reshape(-1)[hidx]
    cc = xx.reshape(-1)[hidx]
    pid[rr, cc] = ids
    val[rr, cc] = np.clip(v, 0, 1)
    depth[rr, cc] = t[hidx]
    return {"pid": pid, "val": val, "depth": depth}


def reduce(buf: dict, prims: list[Prim]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Majority vote per SS x SS block -> (material id or -1, value, depth, prim id)."""
    pid, val, dep = buf["pid"], buf["val"], buf["depth"]
    h, w = pid.shape[0] // SS, pid.shape[1] // SS
    blk = lambda a: a.reshape(h, SS, w, SS).transpose(0, 2, 1, 3).reshape(h, w, SS * SS)  # noqa: E731
    P, Vv, D = blk(pid), blk(val), blk(dep)
    mat = np.full((h, w), -1, np.int16)
    out_v = np.zeros((h, w))
    out_d = np.full((h, w), np.inf)
    out_p = np.full((h, w), -1, np.int32)
    covered = (P >= 0).sum(-1)
    for y, x in zip(*np.nonzero(covered >= COVER_MIN)):
        s = P[y, x]
        ids, counts = np.unique(s[s >= 0], return_counts=True)
        near = np.array([D[y, x][s == i].mean() for i in ids])   # ties go to the nearest
        win = ids[np.lexsort((near, -counts))[0]]
        sel = s == win
        out_p[y, x] = win
        mat[y, x] = MAT_ID[prims[win].mat]
        out_v[y, x] = Vv[y, x][sel].mean()
        out_d[y, x] = D[y, x][sel].mean()
    return mat, out_v, out_d, out_p


def to_rgba(mat, val, depth) -> np.ndarray:
    """Material + value -> palette RGBA, with the contour and rim passes."""
    h, w = mat.shape
    opaque = mat >= 0
    flatm = np.isin(mat, [MAT_ID[m] for m in FLAT_MATERIALS])
    idx = np.zeros((h, w), np.int16)
    for i, name in enumerate(MAT_NAMES):
        sel = mat == i
        n = len(MATERIALS[name].colours())
        idx[sel] = np.rint(val[sel] * (n - 1)).astype(np.int16)
    dark = np.zeros((h, w), np.int16)
    pad_op = np.pad(opaque, 1)
    pad_d = np.pad(depth, 1, constant_values=np.inf)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nb_op = pad_op[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        nb_d = pad_d[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        behind = opaque & nb_op & (nb_d < depth - DEPTH_EDGE) & ~flatm
        dark = np.where(behind, np.maximum(dark, CONTOUR_STEPS), dark)
        rim = opaque & ~nb_op & ~flatm
        dark = np.where(rim, np.maximum(dark, RIM_STEPS), dark)
    idx = np.maximum(idx - dark, 0)
    rgba = np.zeros((h, w, 4), np.uint8)
    for i, name in enumerate(MAT_NAMES):
        cols = np.array(MATERIALS[name].colours(), np.uint8)
        sel = mat == i
        rgba[sel, :3] = cols[np.clip(idx[sel], 0, len(cols) - 1)]
    rgba[opaque, 3] = 255
    return rgba


def stamp_symbol(rgba: np.ndarray, pid: np.ndarray, prims: list[Prim], rotation: int) -> bool:
    """The D12 armband symbol on the band's visible centre, when the band's
    outer face is not turned away. Returns whether it was stamped."""
    band = [i for i, p in enumerate(prims) if p.tag == "armband"]
    vis = np.isin(pid, band)
    if vis.sum() < ARMBAND_MIN_PX:
        return False
    out = next(p for p in prims if p.tag == "armband").xm @ V(1, 0, 0)
    out_w = yaw_matrix(rotation) @ out          # the arm's outer side, in world
    if out_w[2] < -0.05:
        return False
    h, w = pid.shape
    ys, xs = np.nonzero(vis)
    x0 = min(max(int(round(xs.mean() - 3.0)), 0), w - 7)
    y0 = min(max(int(round(ys.mean() - 3.0)), 0), h - 7)
    flat.stamp_armband(rgba, x0, y0)
    return True


def add_flash(rgba: np.ndarray, depth: np.ndarray, muzzle_model: np.ndarray, rotation: int,
              cv: Canvas, size: float = FLASH_SIZE) -> bool:
    """gen_enemy's 2D burst at the projected muzzle. In front of the figure
    when the muzzle is visible, behind it (empty pixels only) when his body
    hides the muzzle. Returns whether it was drawn in front."""
    mx, my, mt = project(muzzle_model, rotation, cv)
    p = flat.Painter(cv.w, cv.h)
    flat.draw_flash(p, mx, my, size)
    over = flat.to_rgba(*p.reduce())
    a = over[..., 3] > 0
    ix, iy = int(np.clip(round(mx), 0, cv.w - 1)), int(np.clip(round(my), 0, cv.h - 1))
    hidden = rgba[iy, ix, 3] > 0 and depth[iy, ix] < mt - 1.0
    if hidden:
        a &= rgba[..., 3] == 0
    rgba[a] = over[a]
    return not hidden


def frame_canvas(frame: str) -> Canvas:
    return GIB if frame in GIB_FRAMES else POSES[frame].canvas


def render(frame: str, rotation: int, seed: int = SEED) -> np.ndarray:
    """One sprite, RGBA (h, w, 4)."""
    cv = frame_canvas(frame)
    if frame in GIB_FRAMES:
        prims, anchors = build_gib(frame, seed)
    else:
        prims, anchors = build_model(POSES[frame])
    buf = raymarch(prims, rotation, cv, seed)
    mat, val, dep, pid = reduce(buf, prims)
    rgba = to_rgba(mat, val, dep)
    stamp_symbol(rgba, pid, prims, rotation)
    if frame in POSES and POSES[frame].flash:
        add_flash(rgba, dep, anchors["muzzle"][0], rotation, cv)
    a = rgba[..., 3] > 0
    if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any():
        raise ValueError(f"{frame}{rotation} touches the canvas edge: enlarge its Canvas")
    return rgba


# ================================================================== frames
# BESTIARY §3: the POSS layout. Rotation 0 = one image for every angle.
FRAME_GROUPS = (
    ("walk", "ABCD", True),
    ("attack", "EF", True),
    ("pain", "G", True),
    ("death", "HIJKL", False),
    ("gib", GIB_FRAMES, False),
)


def frame_plan() -> list[tuple[str, int]]:
    plan = []
    for _, frames, rotated in FRAME_GROUPS:
        for f in frames:
            plan += [(f, r) for r in range(1, ROTATIONS + 1)] if rotated else [(f, 0)]
    return plan


def lump_name(frame: str, rotation: int) -> str:
    return f"{SPRITE}{frame}{rotation}"


def grab_offsets(cv: Canvas = STAND) -> tuple[int, int]:
    """x = the body axis, y = how far the sprite reaches above the floor."""
    return cv.cx, cv.foot_row - FEET_SINK


def save_sprite(rgba: np.ndarray, path: Path, cv: Canvas = STAND) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", *grab_offsets(cv)))
    Image.fromarray(rgba, "RGBA").save(path, pnginfo=info, optimize=True)
    return path


def read_grab(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    i = data.index(b"grAb")
    return struct.unpack(">ii", data[i + 4:i + 12])


def measure(sprite: np.ndarray) -> dict:
    """Size and value. gap_<scene> is |body - wall| under that scene's light
    (gen_enemy's light stand-in, the same scenes as the flat sweep)."""
    a = sprite[..., 3] > 0
    ys, xs = np.nonzero(a)
    body = flat.luma(sprite[..., :3])[a]
    out = {"height_px": int(ys.max() - ys.min() + 1), "width_px": int(xs.max() - xs.min() + 1),
           "lowest_row": int(ys.max()), "body_luma": round(float(body.mean()), 1)}
    f = lambda L: min(1.0, L / flat.LIGHT_FULL)  # noqa: E731
    for key, wall, light, _ in flat.SCENES:
        out[f"gap_{key}"] = round(abs(float(body.mean()) - float(flat.luma(flat.host_rgb(wall)).mean())) * f(light), 1)
    out["worst_gap"] = min(out[f"gap_{k}"] for k, *_ in flat.SCENES)
    return out


# ============================================================ GIFs, scenes
def on_bg(rgba: np.ndarray, colour) -> np.ndarray:
    bg = np.zeros((rgba.shape[0], rgba.shape[1], 3), np.uint8)
    bg[:] = colour
    a = rgba[..., 3] > 0
    bg[a] = rgba[..., :3][a]
    return bg


def pad_to(rgba: np.ndarray, cv: Canvas, target: Canvas) -> np.ndarray:
    """Place a sprite on a larger canvas, axis and sole line kept."""
    out = np.zeros((target.h, target.w, 4), np.uint8)
    x0, y0 = target.cx - cv.cx, target.foot_row - cv.foot_row
    out[y0:y0 + cv.h, x0:x0 + cv.w] = rgba
    return out


def save_gif(frames_rgb: list[np.ndarray], durations_ms: list[int], path: Path) -> Path:
    """Lossless GIF: the frames carry palette.json colours only (< 256), so
    one exact shared palette holds them all."""
    stack = np.stack(frames_rgb)
    cols, inv = np.unique(stack.reshape(-1, 3), axis=0, return_inverse=True)
    if len(cols) > 256:
        raise ValueError(f"{path.name}: {len(cols)} colours, a GIF holds 256")
    pal = cols.astype(np.uint8).reshape(-1).tolist()
    idx = inv.reshape(stack.shape[:3]).astype(np.uint8)
    ims = []
    for f in idx:
        im = Image.fromarray(f, "P")
        im.putpalette(pal)
        ims.append(im)
    path.parent.mkdir(parents=True, exist_ok=True)
    ims[0].save(path, save_all=True, append_images=ims[1:], duration=durations_ms, loop=0,
                optimize=False, disposal=1)
    return path


def scene_rgb(sprite: np.ndarray, cv: Canvas, wall: str, light: int) -> np.ndarray:
    """The figure before a MAP01 wall over SDFLR2, both in the same light
    (gen_enemy's stand-in), soles on the flat sweep's floor line."""
    return lineup([(sprite, cv.cx, cv.foot_row - FEET_SINK)], wall, light, sprite.shape[1])


def lineup(figures: list[tuple[np.ndarray, int, int]], wall: str, light: int, width: int) -> np.ndarray:
    """Several sprites side by side, each placed by its own offsets (x, top),
    Doom's way: the actor stands at its slot centre, the sprite's top is
    `top` px above the floor. MAP01 wall over SDFLR2, then the light."""
    wall_h, floor_h = flat.WALL_H, flat.FLOOR_H
    w_rgb = flat.tile_to(flat.host_rgb(wall), width, wall_h)
    fl = flat.tile_to(flat.host_rgb("SDFLR2"), width, floor_h * 3)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((width, floor_h), Image.Resampling.NEAREST))
    canvas = np.concatenate([w_rgb, fl], axis=0).copy()
    floor = flat.FLOOR_LINE - FEET_SINK          # where a sprite's offset origin sits
    slot = width / len(figures)
    for i, (spr, ox, oy) in enumerate(figures):
        x0 = int(round(slot * (i + 0.5))) - ox
        y0 = floor - oy
        a = spr[..., 3] > 0
        ys, xs = np.nonzero(a)
        ys2, xs2 = ys + y0, xs + x0
        keep = (ys2 >= 0) & (ys2 < canvas.shape[0]) & (xs2 >= 0) & (xs2 < width)
        canvas[ys2[keep], xs2[keep]] = spr[ys[keep], xs[keep], :3]
    return flat.lit(canvas, light)


_WAD: dict | None = None


def freedoom_sprite(name: str) -> tuple[np.ndarray, int, int] | None:
    """A Freedoom 0.13.0 sprite (BSD-3, for SCALE ONLY: iwads/ is not in
    git, so this is optional): RGBA and its (left, top) offsets."""
    global _WAD
    if not flat.IWAD.is_file():
        return None
    if _WAD is None:
        wad = flat.IWAD.read_bytes()
        _, n, off = struct.unpack("<4sii", wad[:12])
        lumps = {}
        for i in range(n):
            pos, size, nm = struct.unpack("<ii8s", wad[off + 16 * i:off + 16 * i + 16])
            lumps[nm.rstrip(b"\0").decode("ascii", "replace")] = (pos, size)
        pp = lumps["PLAYPAL"][0]
        _WAD = {"data": wad, "lumps": lumps, "pal": np.frombuffer(wad[pp:pp + 768], np.uint8).reshape(256, 3)}
    if name not in _WAD["lumps"]:
        return None
    pos, size = _WAD["lumps"][name]
    d = _WAD["data"][pos:pos + size]
    w, h, left, top = struct.unpack("<hhhh", d[:8])
    img = np.zeros((h, w, 4), np.uint8)
    for x, c in enumerate(struct.unpack(f"<{w}i", d[8:8 + 4 * w])):
        while d[c] != 255:
            y0, ln = d[c], d[c + 1]
            for j in range(ln):
                img[y0 + j, x, :3] = _WAD["pal"][d[c + 3 + j]]
                img[y0 + j, x, 3] = 255
            c += ln + 4
    return img, left, top


# ================================================================== build
def build_all(out_dir: Path = OUT_DIR, seed: int = SEED, only: set[str] | None = None) -> dict:
    sprites = {}
    for frame, rot in frame_plan():
        name = lump_name(frame, rot)
        if only and name not in only:
            continue
        rgba = render(frame, rot, seed)
        save_sprite(rgba, out_dir / f"{name}.png", frame_canvas(frame))
        sprites[(frame, rot)] = rgba
        print(name, flush=True)
    if only:
        return sprites
    metrics = {lump_name(f, r): measure(s) for (f, r), s in sprites.items()}
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    write_gifs(sprites, out_dir)
    return sprites


def load_sprites(out_dir: Path = OUT_DIR) -> dict:
    """The lumps a previous run left in out_dir."""
    out = {}
    for frame, rot in frame_plan():
        with Image.open(out_dir / f"{lump_name(frame, rot)}.png") as im:
            out[(frame, rot)] = np.asarray(im.convert("RGBA")).copy()
    return out


NEUTRAL = artlib.ramp("concrete_cold")[16]


def _seq(sprites, frames, rot, cv=STAND):
    return [on_bg(pad_to(sprites[(f, rot)], frame_canvas(f), cv), NEUTRAL) for f in frames]


def write_gifs(sprites: dict, out_dir: Path = OUT_DIR) -> dict[str, Path]:
    """Real speed (35 tics a second, the tics of BESTIARY §3)."""
    t = lambda n: int(round(n * TIC_MS))  # noqa: E731
    out = {}
    for r in range(1, ROTATIONS + 1):
        out[f"walk_{r}"] = save_gif(_seq(sprites, "ABCD", r), [t(4)] * 4, out_dir / f"walk_rot{r}.gif")
        out[f"attack_{r}"] = save_gif(_seq(sprites, "AEFE", r, AIM), [t(20), t(10), t(8), t(8)],
                                      out_dir / f"attack_rot{r}.gif")
    out["turn"] = save_gif([on_bg(sprites[("A", r)], NEUTRAL) for r in range(1, ROTATIONS + 1)],
                           [t(12)] * 8, out_dir / "turntable.gif")
    out["pain"] = save_gif([on_bg(sprites[(f, 1)], NEUTRAL) for f in "AGGA"], [t(20), t(3), t(3), t(20)],
                           out_dir / "pain_rot1.gif")
    death = [on_bg(pad_to(sprites[("A", 1)], STAND, DEATH), NEUTRAL)] + \
            [on_bg(sprites[(f, 0)], NEUTRAL) for f in "HIJKL"]
    out["death"] = save_gif(death, [t(20)] + [t(5)] * 4 + [t(70)], out_dir / "death.gif")
    gib = [on_bg(pad_to(sprites[("A", 1)], STAND, GIB), NEUTRAL)] + \
          [on_bg(sprites[(f, 0)], NEUTRAL) for f in GIB_FRAMES]
    out["gib"] = save_gif(gib, [t(20)] + [t(5)] * 8 + [t(70)], out_dir / "gib.gif")
    return out


# ==================================================================== sheet
# Written after looking at the renders once (PIPELINE stage 2).
VERDICT = [
    "WHAT WORKS. The method does what it promised: 70 lumps from one figure, and every rotation, every "
    "walk frame and the death agree with each other, which 35 hand layouts would not. The legs stride "
    "under the coat in profile (rotations 3 and 7), the aimed rifle is a true profile at 3 and 7 and a "
    "three-quarter at 2, 4, 6, 8, and the fall reads: hit, knees, falling to his left, lying across. "
    "Value holds the faction contract: khaki_olive and black only, no military_green, the armband the "
    "only saturated thing; walking body luma 63 to 75 against the flat cell E's 65, worst gap 13 to 19 "
    "on SDSTEL1 at light 112 against E's 17 (11 on the firing frames, whose flash is counted; section 7). Beside Freedoom's zombieman and shotgun guy "
    "(section 6) he is the same height, reads at 1x and at game distance as a helmeted soldier with a "
    "red armband, and does not look like either placeholder.",
    "WHAT DOES NOT, HONESTLY. Up close (4x) he is a rendered mannequin, not a painted sprite: smooth "
    "rounded forms, no hand-placed highlights, the coat folds faint. The eyeless face is a plain light "
    "oval under the brim, which reads more as a mask than a face. From the front the fired rifle "
    "foreshortens to almost nothing and the flash sits on his chest (the flat sweep had the same "
    "problem). The walk at rotation 1 moves little, because the greatcoat hides the legs. Rotations 6 to "
    "8 show the red band without the symbol (the band's outer face is turned away), and 4 and 5 show "
    "the symbol on a band seen edge-on, a convention. The gib reads weakest: the Reich's olive blood "
    "(BESTIARY 2.1) is dark on a dark floor, the chunks are blobs, and some land up to 3 px below the "
    "sole line (the dropped rifle of the death, 2 px).",
    "NOT VERIFIED. Rotation order and grAb offsets are checked by hand against r_things.c, not in "
    "GZDoom; the sprites are RGBA PNG with hard alpha, like the fonts (ART-BIBLE 2 exception), and the "
    "shipped format is mod-engineer's call. The scene light is gen_enemy.py's stand-in.",
]
CEO_ASK = [
    "Approve the rig as drawn (recommended): the 70 SDRR lumps go to assets/sprites/, mod-engineer swaps "
    "POSS for SDRR in SD_ReichRifleman (BESTIARY 2.7, a rename), and you judge him in GZDoom on MAP01, "
    "which is where an enemy is really judged.",
    "Or name fixes before that, each a parameter in the rig, one more round: a darker eye slot or "
    "cell D's gas mask on the face; stronger coat folds; a different death fall.",
    "One question either way: the gib in olive (the faction contract) reads weakly. Keep it olive, or "
    "allow a dark rust_brown for the insides of the gib only? Recommendation: keep olive; the gib "
    "plays for a quarter of a second.",
]
EXTRA_CSS = """
.strip{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;margin-bottom:10px}
.cap{font:11px Menlo,monospace;color:var(--mute);text-align:center;margin-top:3px}
.cap b{color:var(--ink)}
img.px{background:transparent;border:none}
.tile{display:flex;flex-direction:column;align-items:center}
.verdict p{max-width:980px;margin:6px 0}
"""


def _uri(data: bytes, kind: str) -> str:
    return f"data:image/{kind};base64," + base64.b64encode(data).decode("ascii")


def png_uri(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr, "RGBA" if arr.shape[-1] == 4 else "RGB").save(buf, "PNG", optimize=True)
    return _uri(buf.getvalue(), "png")


def tile(src: str, w: int, h: int, zoom: int, cap: str, sub: str = "") -> str:
    sub_html = f"<br>{html.escape(sub)}" if sub else ""
    return (f'<div class="tile"><img class="px" src="{src}" width="{w * zoom}" height="{h * zoom}" '
            f'alt="{html.escape(cap)}"><div class="cap"><b>{html.escape(cap)}</b>{sub_html}</div></div>')


def sprite_tile(arr: np.ndarray, zoom: int, cap: str, sub: str = "", bg=NEUTRAL) -> str:
    return tile(png_uri(on_bg(arr, bg)), arr.shape[1], arr.shape[0], zoom, cap, sub)


def gif_tile(path: Path, zoom: int, cap: str, sub: str = "") -> str:
    with Image.open(path) as im:
        w, h = im.size
    return tile(_uri(path.read_bytes(), "gif"), w, h, zoom, cap, sub)


def build_sheet(sprites: dict, stamp: str, out_dir: Path = PREVIEW_DIR, seed: int = SEED,
                gif_dir: Path = OUT_DIR) -> Path:
    S = []
    rot_names = {1: "front", 2: "front-left", 3: "his left", 4: "back-left", 5: "back",
                 6: "back-right", 7: "his right", 8: "front-right"}

    def strip(items):
        return '<div class="strip">' + "".join(items) + "</div>"

    # 1. turnaround
    body = strip([sprite_tile(sprites[("A", r)], 4, lump_name("A", r), rot_names[r]) for r in range(1, 9)])
    body += strip([sprite_tile(sprites[("A", r)], 1, lump_name("A", r)) for r in range(1, 9)]
                  + [gif_tile(gif_dir / "turntable.gif", 4, "turntable", "animated")])
    S.append(("1 · Turnaround: frame A at Doom's 8 rotations",
              "4x on neutral grey, then true 1x. Rotation 1 faces you, 3 shows his left side, 5 his back, "
              "7 his right. All eight are separate lumps, not Doom's mirrored pairs: the rifle is on his "
              "right hip and the armband on his left arm, and a mirrored armband would show the symbol "
              "reversed.", body))

    # 2. walk
    body = strip([gif_tile(gif_dir / f"walk_rot{r}.gif", 4, f"walk, rotation {r}", rot_names[r])
                  for r in range(1, 9)])
    for r in (1, 3):
        body += strip([sprite_tile(sprites[(f, r)], 4, lump_name(f, r), POSES[f].title) for f in "ABCD"])
    S.append(("2 · Walk cycle A-B-C-D, animated at game speed",
              "SEE state SDRR AABBCCDD, 4 tics a frame at 35 tics a second (BESTIARY §3). Every rotation "
              "loops here at the speed the engine plays it. Stills of rotations 1 and 3 below.", body))

    # 3. attack
    body = strip([gif_tile(gif_dir / f"attack_rot{r}.gif", 4, f"attack, rotation {r}", "A, E 10, F 8, E 8 tics")
                  for r in (1, 2, 3, 7)])
    for f in "EF":
        body += strip([sprite_tile(sprites[(f, r)], 3, lump_name(f, r)) for r in range(1, 9)])
    S.append(("3 · Attack: E aims, F fires",
              "Missile state E 10, F 8, E 8. The rifle comes up to the shoulder and points along his line of "
              "sight, so from the side (3, 7) it is a profile and from the front a foreshortened barrel. "
              "The flash is drawn behind him when his body hides the muzzle (back rotations).", body))

    # 4. pain
    body = strip([gif_tile(gif_dir / "pain_rot1.gif", 4, "pain, rotation 1", "A, G 3, G 3, A")]
                 + [sprite_tile(sprites[("G", r)], 3, lump_name("G", r)) for r in range(1, 9)])
    S.append(("4 · Pain: G", "He recoils: upper body back 13 degrees, chin up, the rifle muzzle rising.", body))

    # 5. death and gib
    body = strip([gif_tile(gif_dir / "death.gif", 4, "death", "H I J K 5 tics, L stays")]
                 + [sprite_tile(sprites[(f, 0)], 3, lump_name(f, 0), POSES[f].title) for f in "HIJKL"])
    body += strip([gif_tile(gif_dir / "gib.gif", 4, "gib (XDeath)", "M-T 5 tics, U stays")])
    body += strip([sprite_tile(sprites[(f, 0)], 2, lump_name(f, 0)) for f in GIB_FRAMES])
    S.append(("5 · Death H-L and gib M-U (rotation 0: one image for every angle)",
              "Death: hit, knees go, he falls to his left and lies across. Gib: the chest gives way, the "
              "upper body goes up in chunks, the crested helmet and the rifle fly whole and land, the legs "
              "stand a moment and fall. Blood and gore are the Reich's dark olive (BESTIARY §2.1), not red: "
              "the armband stays the only red on him (ART-BIBLE §6.3).", body))

    # 6. in the game, next to Freedoom
    poss = freedoom_sprite("POSSA1")
    spos = freedoom_sprite("SPOSA1")
    figs = [(sprites[("A", 1)], *grab_offsets(STAND))]
    labels = ["SDRRA1 (ours)"]
    if poss:
        figs.append(poss)
        labels.append("POSSA1 (Freedoom zombieman, today's placeholder)")
    if spos:
        figs.append(spos)
        labels.append("SPOSA1 (Freedoom, the Legion trooper's placeholder)")
    figs.append((sprites[("F", 3)], *grab_offsets(STAND)))
    labels.append("SDRRF3 (ours, firing, side)")
    body = ""
    for key, wall, light, what in flat.SCENES:
        sc = lineup(figs, wall, light, 64 * len(figs))
        Image.fromarray(sc, "RGB").save(gif_dir / f"lineup_{key}.png", optimize=True)
        body += strip([tile(png_uri(sc), sc.shape[1], sc.shape[0], 3, f"{key}: {wall} at light {light}", what),
                       tile(png_uri(sc), sc.shape[1], sc.shape[0], 1, "1x")])
    far = flat.far(lineup(figs, "SDSTEL1", 112, 64 * len(figs)))
    sil = flat.silhouette(sprites[("A", 1)])
    sil_rgb = np.where(sil[..., None], 0, 235).astype(np.uint8).repeat(3, -1)
    body += strip([tile(png_uri(far), far.shape[1], far.shape[0], 5, "game distance, S3 (worst case), /4"),
                   tile(png_uri(sil_rgb), sil_rgb.shape[1], sil_rgb.shape[0], 5, "16 px silhouette")])
    body += "<p class=\"lead\">Left to right: " + html.escape(" · ".join(labels)) + ". Each sprite stands by its own " \
            "offsets, as the engine places it. Light is gen_enemy.py's stand-in (RGB x L/224, re-quantised); " \
            "NOT VERIFIED against GZDoom.</p>"
    S.append(("6 · At Doom's scale, beside the Freedoom placeholders, on MAP01's walls",
              "The same four scenes as the design sweep: corridor, hangar dado, the fuel bay at light 112 "
              "(worst case), crate cover.", body))

    # 7. numbers
    rows = []
    for f, r in [(f, r) for f in "ABCDEFG" for r in (1, 3, 5, 7)] + [(f, 0) for f in "HL"] + [("U", 0)]:
        m = measure(sprites[(f, r)])
        rows.append([lump_name(f, r), f"{m['height_px']} x {m['width_px']}", m["body_luma"],
                     m["gap_S1"], m["gap_S2"], m["gap_S3"], m["gap_S4"]])
    body = sheetlib.table(["lump", "h x w px", "body luma", "gap S1", "gap S2", "gap S3", "gap S4"], rows)
    body += ("<p class=\"lead\">Body luma is the mean over every opaque pixel; gap is |body - wall| under "
             "the scene's light. The flat cell E measured 65 and a worst gap of 17 (S3). "
             f"Canvas: standing {STAND.w}x{STAND.h}, grAb {grab_offsets(STAND)}; death {DEATH.w}x{DEATH.h}; "
             f"gib {GIB.w}x{GIB.h}. {len(frame_plan())} lumps in all.</p>")
    S.append(("7 · Numbers", "", body))

    # 8. verdict and the ask
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in VERDICT) + "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in CEO_ASK) \
            + "</ol></div>"
    S.append(("8 · Honest verdict and what you decide", "", body))

    intro = ("D38: cell E (crested helmet, eyeless, calf-length greatcoat, bolt rifle at the hip) built as a 3D "
             "rig and rendered for the whole frame set Doom needs: walk, aim, fire and pain at 8 rotations, "
             f"death and gib at one. About 50 primitives on a skeleton with IK legs and arms, sphere-traced in "
             f"numpy at 16 rays a pixel, camera {PITCH_DEG:.0f} degrees down, light fixed to the camera and cut "
             f"into {LIGHT_BANDS} bands, majority vote to 1x, palette v1 only, seed {seed}. "
             "Built by <code>tools/art/gen_rig.py</code>. Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_rig.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic, no "
              "system fonts. Freedoom sprites shown for scale only, from freedoom2.wad 0.13.0, BSD-3-Clause "
              "(© the Freedoom contributors), not used as a source.")
    path = out_dir / f"{stamp}_F5_reich-rifleman-rig.html"
    sheetlib.write_sheet(path, lang="en", title="Reich rifleman — 3D rig, full frame set (F5, D38)",
                         subtitle=f"SDRR · {len(frame_plan())} lumps · draft for the CEO's gate",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", EXTRA_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    ap.add_argument("--seed", type=int, default=SEED, help="cloth grain and gib seed")
    ap.add_argument("--no-sheet", action="store_true", help="sprites only")
    ap.add_argument("--only", default="", help="comma-separated lumps, e.g. SDRRA1,SDRRH0 (no sheet)")
    ap.add_argument("--sheet-only", action="store_true",
                    help="rebuild the sheet from the sprites and GIFs already in work/art/enemies/rig/")
    args = ap.parse_args()
    only = {s.strip().upper() for s in args.only.split(",") if s.strip()} or None
    if args.sheet_only:
        sprites = load_sprites()
    else:
        sprites = build_all(seed=args.seed, only=only)
    if only or args.no_sheet:
        return
    path = build_sheet(sprites, args.stamp, seed=args.seed)
    print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
