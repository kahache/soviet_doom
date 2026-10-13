"""F5 — the shared core of the 3D sprite rig: primitives, skeletons, renderer.

What this is. D38 approved "pose once, render many" (BESTIARY §2.6) for the
Reich rifleman (gen_rig.py). The Legion trooper (gen_legion.py), the
Stormtrooper and the hound (gen_storm.py) were then drawn on the same rig,
and both sweeps reported what a second figure needs from it (their sheets,
"the rig" sections). This module is that machinery, figure-free: every
enemy is a figure module (its model, poses, frame plan and sheet) on top of
it, and nothing here knows a rifleman from a dog.

What it offers:
  * SDF primitives (ellipsoid, round cone, capped cone, rounded box) with a
    rigid transform, a rig GROUP, and a LIMB and SIDE label, so a figure
    module can pick "his right arm" by name instead of by position;
  * two-bone IK, rigid group transforms, resting a group on the floor;
  * the quadruped skeleton: a spine chain, the three-bone digitigrade leg,
    a quadruped Pose with gait phase (section "quadruped" below);
  * the renderer: orthographic sphere tracing at Doom's 8 rotations,
    banded Lambert or two-tone CHROME shading, majority vote to 1x, the
    occlusion contour and the silhouette rim; `render(prims, rot, canvas)`;
  * MATERIALS as a parameter: a material table is a plain dict, built with
    `register_material` (append-only, so ids never move), and handed to
    `raymarch`, `reduce`, `to_rgba` and `render`;
  * extra palette ramps (`register_ramp`) for candidates not yet in
    palette.json (the Legion's pink), and `lit(..., palette=)` that
    re-quantises a scene to an extended palette instead of to v1;
  * a parametric insignia stamp (`Insignia`): the rifleman's armband, the
    Legion's flag, the Stormtrooper's patch are three parameter sets;
  * a MIRROR mode for symmetric figures: Doom's paired rotations (2&8, 3&7,
    4&6) share one image, so a frame costs 5 drawings, not 8;
  * output helpers: grAb offsets, PNG, lossless GIF, the lineup on MAP01's
    walls, the Freedoom reader (scale only), the sheet's tiles.

The numbers (camera pitch, bands, value gains, cover threshold, contour
steps) are the ones D38 approved for the rifleman; changing one here
changes every enemy's look, so tests/test_gen_rig.py and its siblings are
the tripwire. The refactor that created this module was checked to leave
every PNG of gen_rig, gen_legion and gen_storm byte-identical.

Rotations. Doom picks rotation k when the viewer is (k-1)*45 degrees round
the thing, counter-clockwise from its front: 1 front, 3 the thing's LEFT
side (it faces screen left), 5 back, 7 its right side. Verified against
r_things.c's `rot = (ang - thing->angle + ANG45/2*9) >> 29` by hand, NOT
against the engine. Mirrored pairs: the engine draws rotation 8 as rotation
2 flipped about the sprite's x offset (r_things.c, `flip`), so a mirrored
figure needs its body axis at the canvas centre (Canvas.cx * 2 == w).

NO FONTS. Nothing here rasterises text (tests/test_rig_core.py keeps it so).
"""

from __future__ import annotations

import base64
import html
import io
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, NamedTuple

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

ART_TOOLS = Path(__file__).resolve().parent
if str(ART_TOOLS) not in sys.path:
    sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402  (base materials, armband, flash painter, light stand-in, scenes)

PROJECT_ROOT = artlib.PROJECT_ROOT

SS = 4                          # rays per pixel side
FEET_SINK = 4                   # as gen_enemy / Freedoom POSSA1 (57 high, top 53)
DOOM_HEIGHT = 56                # a humanoid actor's Height = px at 1:1; the light's vertical falloff scale
ROTATIONS = 8
TIC_MS = 1000 / 35              # Doom runs at 35 tics a second


@dataclass(frozen=True)
class Canvas:
    w: int
    h: int
    cx: int                     # body axis column (grAb x)
    foot_row: int               # the sole line, world y = 0


STAND = Canvas(64, 72, 32, 68)  # a standing humanoid: one canvas, one grAb
AIM = Canvas(96, 72, 48, 68)    # an aimed long gun reaches 40 px out in profile

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
COVER_MIN = 7                   # of 16 sub-pixels, below this a pixel is transparent
DEPTH_EDGE = 1.4                # a neighbour this much nearer draws a contour on us
CONTOUR_STEPS = 2
RIM_STEPS = 3
FLASH_SIZE = 6.0                # as gen_enemy's rifle flash
FLOOR_STEP = 1.0                # grid of the upward rays that find a body's lowest point


# ================================================================ palette
EXTRA_RAMPS: dict[str, list[tuple[int, int, int]]] = {}


def register_ramp(name: str, colours: list[tuple[int, int, int]]) -> None:
    """A candidate ramp that palette.json does not have yet (it is never
    written there: adding a ramp is a palette version, the CEO's call)."""
    if name in EXTRA_RAMPS and EXTRA_RAMPS[name] != list(colours):
        raise ValueError(f"ramp {name} is already registered with other colours")
    EXTRA_RAMPS[name] = [tuple(c) for c in colours]


def ramp(name: str) -> list[tuple[int, int, int]]:
    return list(EXTRA_RAMPS[name]) if name in EXTRA_RAMPS else artlib.ramp(name)


def quantize_to(rgb: np.ndarray, colours: list[tuple[int, int, int]]) -> np.ndarray:
    """Nearest colour of `colours` (at most 256), no dither."""
    pimg = Image.new("P", (1, 1))
    pimg.putpalette([v for c in colours for v in c] + [0] * (3 * (256 - len(colours))))
    q = Image.fromarray(rgb, "RGB").quantize(palette=pimg, dither=Image.Dither.NONE)
    return np.asarray(q.convert("RGB"))


def lit(rgb: np.ndarray, light: int, palette: list[tuple[int, int, int]] | None = None) -> np.ndarray:
    """gen_enemy's sector-light stand-in (RGB x L/224). With no palette it is
    gen_enemy.lit (re-quantised to palette v1); with an extended palette
    (v1 plus a candidate ramp) it re-quantises to THAT, so the candidate's
    colours survive. NOT VERIFIED against GZDoom's light tables."""
    if palette is None:
        return flat.lit(rgb, light)
    f = min(1.0, light / flat.LIGHT_FULL)
    return quantize_to(np.clip(rgb.astype(np.float64) * f, 0, 255).astype(np.uint8), palette)


# ================================================================ materials
@dataclass(frozen=True)
class Mat:
    """A run of palette colours, darkest first, and how the renderer treats
    it. A span is (ramp, lo, hi), or ("black",) / ("white",)."""
    spans: tuple
    shading: str = "lambert"    # "lambert" | "chrome" (reflects CHROME's environment)
    cloth: bool = False         # takes the cloth grain
    lift: float = 0.0           # value added to every primitive of this material
    shift: bool = True          # takes the figure's value shift (render's value_shift)
    flat: bool = False          # no contour, no rim: a glow, a flash, a button

    @classmethod
    def on_ramp(cls, name: str, lo: int, hi: int, black_floor: bool = False, **kw) -> "Mat":
        """gen_enemy.Material's form: a slice of one ramp, optionally with
        true black below it."""
        spans = ((("black",), (name, lo, hi)) if black_floor else ((name, lo, hi),))
        return cls(spans, **kw)

    @classmethod
    def of(cls, m: "flat.Material", **kw) -> "Mat":
        return cls.on_ramp(m.ramp, m.lo, m.hi, m.black_floor, **kw)

    def colours(self) -> list[tuple[int, int, int]]:
        out: list[tuple[int, int, int]] = []
        for s in self.spans:
            if s[0] == "black":
                out.append((0, 0, 0))
            elif s[0] == "white":
                out.append((255, 255, 255))
            else:
                out += ramp(s[0])[s[1]:s[2] + 1]
        return out

    @property
    def ramps(self) -> set[str]:
        return {s[0] for s in self.spans if s[0] not in ("black", "white")}


def register_material(name: str, mat: Mat, table: dict[str, Mat] | None = None) -> int:
    """Add a material to a table (MATERIALS when none is given) and return
    its id. Append-only: an existing name keeps its id, and registering it
    again with a different definition is an error, so no figure can move or
    repaint another figure's materials."""
    table = MATERIALS if table is None else table
    if name in table:
        if table[name] != mat:
            raise ValueError(f"material {name} is already registered differently")
    else:
        table[name] = mat
    return list(table).index(name)


def material_ids(table: dict[str, Mat]) -> dict[str, int]:
    return {n: i for i, n in enumerate(table)}


# The base table: gen_enemy's materials (cell E, D38) with the traits the
# rifleman's render gave them. A figure copies it (dict(MATERIALS)) and
# registers its own on the copy.
BASE_FLAT = {"flash_out", "flash_in", "flash_core", "button"}
BASE_NO_SHIFT = BASE_FLAT | {"flesh", "crest"}     # keep their own value: face and crest read
BASE_CLOTH = {"coat", "coat_dark", "helmet", "crest"}
MATERIALS: dict[str, Mat] = {}
for _name, _m in flat.MATERIALS.items():
    register_material(_name, Mat.of(_m, cloth=_name in BASE_CLOTH, shift=_name not in BASE_NO_SHIFT,
                                    flat=_name in BASE_FLAT))


@dataclass(frozen=True)
class Chrome:
    """Two-tone airbrush chrome (the Legion's): reflection rays above the
    horizon see sky, below it ground, a hard specular dot near the key."""
    horizon: float = -0.60      # front plates, even tipped down a little, reflect sky
    sky_lo: float = 0.80        # sky value at the horizon ...
    sky_hi: float = 1.0         # ... and straight up: bright, so chrome clears concrete
    ground_lo: float = 0.04
    ground_span: float = 0.30
    ground_fade: float = 0.8
    spec_cos: float = 0.90      # reflection this close to the key light: a white dot
    key: float = 0.22           # how much the key light's side darkens chrome
    ao: float = 0.5             # chrome takes this share of the cloth's occlusion


CHROME = Chrome()


# ============================================================ SDF primitives
def _len(v: np.ndarray) -> np.ndarray:
    return np.sqrt(np.einsum("ij,ij->i", v, v))


LEFT, RIGHT, CENTRE = 1, -1, 0  # sides: +x is the figure's LEFT


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
    grp: str = ""               # rig group: what moves together
    xm: np.ndarray = field(default_factory=lambda: np.eye(3))    # rigid transform:
    xt: np.ndarray = field(default_factory=lambda: np.zeros(3))  # world = xm @ local + xt
    limb: str = ""              # "arm" | "leg" | "foreleg" | "hindleg" | ... ("" = torso, head, props)
    side: int = CENTRE          # LEFT (+1, the figure's left), RIGHT (-1), CENTRE (0)

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


def select(prims: list[Prim], *, limb: str | None = None, side: int | None = None,
           grp: str | None = None, tag: str | None = None) -> list[Prim]:
    """The primitives matching every label given: `select(P, limb="arm",
    side=RIGHT)` is his right arm, wherever the pose has put it."""
    return [p for p in prims if (limb is None or p.limb == limb) and (side is None or p.side == side)
            and (grp is None or p.grp == grp) and (tag is None or p.tag == tag)]


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


# The humanoid leg every infantry figure stands on (the rifleman's, D38).
ANKLE_Y = 2.2
HIP_Y = 26.2
THIGH, SHIN = 12.6, 11.6


# ============================================================== quadruped
# The hound sweep (gen_storm.py, sheet section 8) found what a four-legged
# figure needs that a biped does not: (1) a spine CHAIN, pelvis to head,
# each bone's angle relative to its parent, that bends and carries the
# legs; (2) a three-bone DIGITIGRADE hind leg (hip, stifle, hock, paw);
# (3) a quadruped Pose with a GAIT PHASE (four paw targets, spine flex and
# bob per frame). Model space as for every figure: paws on y = 0, facing
# +z, +x the figure's LEFT.

def spine_chain(root, lengths, bends, pitch: float = 0.0) -> tuple[list[np.ndarray], list[float]]:
    """Forward kinematics of a chain in the figure's mid-plane (x = 0): from
    `root`, bone i is lengths[i] long and points forward (+z) tipped up by
    pitch + bends[0] + ... + bends[i] degrees (positive = nose up), so each
    bend is relative to the parent bone. Returns (joints, absolute angles):
    len(lengths) + 1 joints, one angle per bone."""
    joints = [np.asarray(root, float)]
    angles: list[float] = []
    a = pitch
    for L, b in zip(lengths, bends):
        a += b
        angles.append(a)
        r = np.deg2rad(a)
        joints.append(joints[-1] + L * V(0.0, np.sin(r), np.cos(r)))
    return joints, angles


def bone_frame(angle: float) -> np.ndarray:
    """Rotation taking the local forward axis (+z) to a chain bone tipped up
    by `angle` degrees (spine_chain's convention): attach primitives in the
    bone's frame with it."""
    return rot_x(angle)


def three_bone(root, target, a: float, b: float, c: float, pole) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A digitigrade leg reaching for `target`: root -> knee (a) -> hock (b)
    -> end (c), solved as a PANTOGRAPH: the first and the last bone stay
    parallel, so the chain is the two-bone problem (a + c, b) and every
    bone keeps its length. The knee bends towards `pole` (forward, +z, for a
    hound's stifle); the hock then sits behind and above the paw. Returns
    (knee, hock, end); the end falls short when out of reach."""
    root = np.asarray(root, float)
    j, end = two_bone(root, target, a + c, b, pole)
    u = (j - root) / np.linalg.norm(j - root)
    return root + u * a, end - u * c, end


@dataclass(frozen=True)
class Gait:
    """A quadruped gait: per-leg phase offsets (fl, fr, hl, hr), the share
    of the cycle a paw is on the ground, and how far the body moves."""
    name: str
    offsets: dict               # leg -> phase offset, 0..1
    duty: float                 # share of the cycle each paw is on the ground
    stride: float               # paw travel along z during stance, units
    lift: float                 # swing height, units
    flex: float                 # spine flex amplitude, degrees (gathered +, stretched -)
    bob: float                  # pelvis and chest bob, units
    pitch: float                # whole-body pitch amplitude, degrees


GAITS = {
    # Walk: lateral sequence, three paws down most of the time.
    "walk": Gait("walk", {"hl": 0.0, "fl": 0.25, "hr": 0.5, "fr": 0.75}, 0.65, 9.0, 2.2, 3.0, 0.5, 1.0),
    # Transverse gallop, as a greyhound runs: the hind pair lands, then the
    # fore pair half a cycle later; the spine gathers when the hind paws
    # reach forward and stretches when they push off.
    "gallop": Gait("gallop", {"hl": 0.0, "hr": 0.1, "fl": 0.5, "fr": 0.6}, 0.32, 18.0, 4.5, 12.0, 1.6, 5.0),
}
LEGS = ("fl", "fr", "hl", "hr")


@dataclass(frozen=True)
class QuadBuild:
    """Proportions of a quadruped skeleton (defaults: the Reich hound's
    long build of the gen_storm sweep, cell A/D)."""
    pelvis: tuple = (0.0, 25.0, -17.0)  # sacrum: the spine's root, on the top line
    spine: tuple = (9.0, 9.0, 9.0)       # loin, back, chest: sacrum -> withers
    spine_bends: tuple = (12.0, -6.0, -2.0)  # rest curve: the top line rises to the withers
    neck: tuple = (6.0, 5.0)             # two neck bones, withers -> skull base
    neck_bends: tuple = (-10.0, -10.0)   # head carried low and forward (BESTIARY §6: spine low)
    hip_x: float = 3.6                   # half the hip width
    shoulder_x: float = 4.7              # half the shoulder width
    hip_drop: float = 4.5                # hip joint below the sacrum
    shoulder_drop: float = 8.0           # shoulder joint below the withers
    femur: float = 9.6
    tibia: float = 9.6
    meta: float = 6.6                    # metatarsus: hock -> paw
    upper: float = 11.0                  # foreleg: shoulder -> elbow
    lower: float = 10.5                  # elbow -> wrist
    pastern: float = 1.4                 # wrist sits this far above the paw
    paw_y: float = 1.25
    fore_reach: float = 2.0              # neutral forepaw this far ahead of the shoulder
    hind_reach: float = -2.5             # neutral hindpaw this far behind the hip


@dataclass(frozen=True)
class QuadPose:
    """A quadruped frame: the gait and where in its cycle (0..1, periodic)."""
    key: str
    title: str
    phase: float
    gait: str = "gallop"
    head_pitch: float = 0.0     # degrees, nose down
    jaw_open: float = 0.0       # degrees


@dataclass
class QuadRig:
    """The posed skeleton: joint positions, model space."""
    spine: list                 # pelvis ... withers
    spine_angles: list
    neck: list                  # withers ... skull base
    neck_angles: list
    legs: dict                  # leg -> (root, mid, low, paw); hind: hip, knee, hock, paw; fore: shoulder, elbow, wrist, paw
    paws: dict                  # leg -> target the IK reached for


def paw_offset(gait: Gait, leg: str, phase: float, build: QuadBuild) -> tuple[float, float]:
    """(z offset from the paw's neutral spot, height) for one leg: on the
    ground moving back during stance, an arc forward during swing."""
    p = (phase - gait.offsets[leg]) % 1.0
    if p < gait.duty:
        s = p / gait.duty
        return gait.stride * (0.5 - s), build.paw_y
    s = (p - gait.duty) / (1.0 - gait.duty)
    s2 = s * s * (3 - 2 * s)                     # ease in and out of the swing
    return gait.stride * (s2 - 0.5), build.paw_y + gait.lift * np.sin(np.pi * s)


def pose_quadruped(build: QuadBuild, pose: QuadPose) -> QuadRig:
    """Solve the skeleton for one frame: spine flex and bob from the phase,
    the spine chain from the pelvis, the neck from the withers, the hind
    legs by three_bone (pantograph) and the forelegs by two_bone, each paw
    on its gait target."""
    g = GAITS[pose.gait]
    w = 2 * np.pi * pose.phase
    flex = g.flex * np.cos(w)                    # + gathered (hind paws forward), - stretched
    bob = g.bob * np.cos(2 * w)
    pitch = g.pitch * np.sin(w)
    bends = list(build.spine_bends)
    bends[0] += flex * 0.5                       # the loin rounds, the back follows
    bends[1] -= flex * 0.25
    pelvis = V(*build.pelvis) + V(0.0, bob, 0.0)
    spine, s_ang = spine_chain(pelvis, build.spine, bends, pitch=pitch - flex * 0.25)
    withers = spine[-1]
    nb = list(build.neck_bends)
    nb[-1] -= pose.head_pitch
    neck, n_ang = spine_chain(withers, build.neck, nb, pitch=s_ang[-1])
    legs, paws = {}, {}
    pelvis_frame = bone_frame(s_ang[0])
    chest_frame = bone_frame(s_ang[-1])
    for leg in LEGS:
        side = LEFT if leg.endswith("l") else RIGHT
        dz, y = paw_offset(g, leg, pose.phase, build)
        if leg.startswith("h"):
            root = pelvis + pelvis_frame @ V(side * build.hip_x, -build.hip_drop, 0.0)
            target = V(root[0], y, build.pelvis[2] + build.hind_reach + dz)
            knee, hock, paw = three_bone(root, target, build.femur, build.tibia, build.meta, V(0, 0, 1))
            legs[leg] = (root, knee, hock, paw)
        else:
            root = withers + chest_frame @ V(side * build.shoulder_x, -build.shoulder_drop, 0.0)
            target = V(root[0], y, withers[2] + build.fore_reach + dz)
            elbow, wrist = two_bone(root, target + V(0, build.pastern, 0), build.upper, build.lower, V(0, 0, -1))
            legs[leg] = (root, elbow, wrist, wrist - V(0, build.pastern, 0))
        paws[leg] = target
    return QuadRig(spine, s_ang, neck, n_ang, legs, paws)


def on_bone(prim: Prim, origin, angle: float) -> Prim:
    """Place a primitive built in a bone's local frame (origin at the joint,
    +z along the bone) on a chain bone tipped up by `angle` degrees."""
    prim.xm = bone_frame(angle)
    prim.xt = np.asarray(origin, float).copy()
    return prim


def skeleton_prims(rig: QuadRig, bone_mat: str, joint_mat: str, r: float = 0.55) -> list[Prim]:
    """The posed skeleton as thin bones and joint knobs: for a sheet that
    shows the IK, not for a sprite."""
    out: list[Prim] = []
    chains = [rig.spine, rig.neck] + [list(rig.legs[k]) for k in LEGS]
    for chain in chains:
        for a, b in zip(chain[:-1], chain[1:]):
            out.append(rcone(bone_mat, 0.7, a, b, r))
        for j in chain:
            out.append(ellipsoid(joint_mat, 0.6, tuple(j), (r * 1.7,) * 3))
    return out


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


def raymarch(prims: list[Prim], rotation: int, cv: Canvas, materials: dict[str, Mat] | None = None,
             seed: int = 0, value_shift: float = 0.0, chrome: Chrome = CHROME) -> dict:
    """Trace the posed primitives at one rotation. Returns 4x buffers: prim
    id (-1 empty), value 0..1, depth. `value_shift` moves every material
    whose `shift` is set (the Reich is drawn 0.26 darker than its base
    values; the Legion not at all)."""
    materials = MATERIALS if materials is None else materials
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
    nw = nrm @ Rm.T                       # world normals
    lam = nw @ LIGHT
    lam_b = np.floor((lam * 0.5 + 0.5) * LIGHT_BANDS).clip(0, LIGHT_BANDS - 1) / (LIGHT_BANDS - 1)
    ao = np.clip(scene.sdf(ph + nrm * AO_DIST) / AO_DIST, 0, 1)
    m = [materials[prims[i].mat] for i in ids]
    base = np.array([prims[i].base + materials[prims[i].mat].lift for i in ids])
    shift = np.array([value_shift if mm.shift else 0.0 for mm in m])
    cloth = np.array([mm.cloth for mm in m], bool)
    grain = (hash3(np.floor(ph / GRAIN_CELL), seed) - 0.5) * 2 * GRAIN * cloth
    fall = VERTICAL_FALLOFF * (0.5 - ph[:, 1] / DOOM_HEIGHT)
    v = (base + shift + SHADE_GAIN * (lam_b - 0.5) - AO_WEIGHT * (1 - ao) - fall + grain)
    is_chrome = np.array([mm.shading == "chrome" for mm in m], bool)
    if is_chrome.any():                   # what the surface reflects, not how much light it takes
        r = fwd[None, :] - 2.0 * (nw @ fwd)[:, None] * nw
        ry = r[:, 1]
        sky = chrome.sky_lo + (chrome.sky_hi - chrome.sky_lo) * np.sqrt(
            np.clip((ry - chrome.horizon) / (1.0 - chrome.horizon), 0, 1))
        ground = chrome.ground_lo + chrome.ground_span * np.clip((chrome.horizon - ry) / chrome.ground_fade, 0, 1)
        env = np.where(ry > chrome.horizon, sky, ground)
        vc = env - chrome.key * (1 - lam_b) - chrome.ao * AO_WEIGHT * (1 - ao) - fall
        vc = np.where(r @ LIGHT > chrome.spec_cos, 1.0, vc)
        v = np.where(is_chrome, vc, v)
    rr = yy.reshape(-1)[hidx]
    cc = xx.reshape(-1)[hidx]
    pid[rr, cc] = ids
    val[rr, cc] = np.clip(v, 0, 1)
    depth[rr, cc] = t[hidx]
    return {"pid": pid, "val": val, "depth": depth}


def reduce(buf: dict, prims: list[Prim], materials: dict[str, Mat] | None = None):
    """Majority vote per SS x SS block -> (material id or -1, value, depth,
    prim id). Material ids index `materials` in its insertion order."""
    materials = MATERIALS if materials is None else materials
    mid = material_ids(materials)
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
        mat[y, x] = mid[prims[win].mat]
        out_v[y, x] = Vv[y, x][sel].mean()
        out_d[y, x] = D[y, x][sel].mean()
    return mat, out_v, out_d, out_p


def to_rgba(mat, val, depth, materials: dict[str, Mat] | None = None) -> np.ndarray:
    """Material + value -> palette RGBA, with the contour and rim passes
    (both skipped on `flat` materials)."""
    materials = MATERIALS if materials is None else materials
    names = list(materials)
    h, w = mat.shape
    opaque = mat >= 0
    flatm = np.isin(mat, [i for i, n in enumerate(names) if materials[n].flat])
    idx = np.zeros((h, w), np.int16)
    for i, name in enumerate(names):
        sel = mat == i
        n = len(materials[name].colours())
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
    for i, name in enumerate(names):
        cols = np.array(materials[name].colours(), np.uint8)
        sel = mat == i
        rgba[sel, :3] = cols[np.clip(idx[sel], 0, len(cols) - 1)]
    rgba[opaque, 3] = 255
    return rgba


# ================================================================ insignia
@dataclass(frozen=True)
class Insignia:
    """A hard-pixel stamp on a tagged primitive's visible centre: the D12
    armband, the Legion's flag, the Stormtrooper's patch. Stamped when at
    least `min_px` pixels of the tagged primitives are visible and their
    `outward` face (in the first tagged primitive's own frame, so it turns
    with the limb) is not turned away from the camera."""
    tag: str
    size: tuple[int, int]                           # (w, h) px
    draw: Callable[[np.ndarray, int, int, bool], None]  # (rgba, x0, y0, mirrored)
    outward: tuple = (1.0, 0.0, 0.0)
    min_px: int = 6
    anchor: tuple | None = None     # px subtracted from the visible centroid; default the stamp's centre
    search: int = 0                 # px the stamp may slide to sit on opaque pixels
    mirror_facing_right: bool = False   # flipped when the figure faces screen right (a flag's canton leads)
    turned_away: float = -0.05      # world z of `outward` below this: not stamped


def pattern_drawer(pattern: tuple[str, ...], colours: dict) -> Callable[[np.ndarray, int, int, bool], None]:
    """A `draw` for Insignia from rows of characters; colours maps a
    character to (ramp, index) or to an RGB triple."""
    def draw(rgba: np.ndarray, x0: int, y0: int, mirror: bool) -> None:
        for j, row in enumerate(pattern):
            for i, ch in enumerate(row[::-1] if mirror else row):
                spec = colours[ch]
                col = ramp(spec[0])[spec[1]] if isinstance(spec[0], str) else tuple(spec)
                rgba[y0 + j, x0 + i] = (*col, 255)
    return draw


def armband_draw(rgba: np.ndarray, x0: int, y0: int, mirror: bool) -> None:
    """gen_enemy's 7x7 D12 armband (never mirrored: a reversed symbol is wrong)."""
    flat.stamp_armband(rgba, x0, y0)


ARMBAND = Insignia("armband", (7, 7), armband_draw, outward=(1.0, 0.0, 0.0), min_px=6)


def stamp_insignia(rgba: np.ndarray, pid: np.ndarray, prims: list[Prim], rotation: int, ins: Insignia) -> bool:
    """Stamp `ins` in place. Returns whether it was stamped."""
    ids = [i for i, p in enumerate(prims) if p.tag == ins.tag]
    if not ids:
        return False
    vis = np.isin(pid, ids)
    if vis.sum() < ins.min_px:
        return False
    out_w = yaw_matrix(rotation) @ (prims[ids[0]].xm @ V(*ins.outward))
    if out_w[2] < ins.turned_away:
        return False
    mirror = bool(ins.mirror_facing_right and (yaw_matrix(rotation) @ V(0, 0, 1))[0] > 0.3)
    fw, fh = ins.size
    ax, ay = ins.anchor if ins.anchor is not None else ((fw - 1) / 2, (fh - 1) / 2)
    h, w = pid.shape
    ys, xs = np.nonzero(vis)
    cx, cy = xs.mean() - ax, ys.mean() - ay
    opaque = rgba[..., 3] > 0
    best = None
    for dy in range(-ins.search, ins.search + 1):
        for dx in range(-ins.search, ins.search + 1):
            x0 = min(max(int(round(cx + dx)), 0), w - fw)
            y0 = min(max(int(round(cy + dy)), 0), h - fh)
            score = (int(opaque[y0:y0 + fh, x0:x0 + fw].sum()), -(dx * dx + dy * dy))
            if best is None or score > best[0]:
                best = (score, x0, y0)
    _, x0, y0 = best
    ins.draw(rgba, x0, y0, mirror)
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


# ================================================================== render
class Layers(NamedTuple):
    rgba: np.ndarray            # (h, w, 4) palette colours, hard alpha
    mat: np.ndarray             # material id per pixel, -1 empty
    depth: np.ndarray
    pid: np.ndarray             # primitive index per pixel, -1 empty


def check_edges(rgba: np.ndarray, what: str = "sprite") -> None:
    a = rgba[..., 3] > 0
    if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any():
        raise ValueError(f"{what} touches the canvas edge: enlarge its Canvas")


def render_layers(prims: list[Prim], rotation: int, cv: Canvas, materials: dict[str, Mat] | None = None, *,
                  seed: int = 0, value_shift: float = 0.0, insignia: tuple[Insignia, ...] = (),
                  muzzle: np.ndarray | None = None, flash_size: float = FLASH_SIZE,
                  chrome: Chrome = CHROME, what: str = "sprite") -> Layers:
    """The whole pipeline for one posed figure at one rotation: trace,
    majority vote, palette with contour and rim, insignia in order, the
    muzzle flash when a muzzle point is given, and the edge check."""
    materials = MATERIALS if materials is None else materials
    buf = raymarch(prims, rotation, cv, materials, seed, value_shift, chrome)
    mat, val, dep, pid = reduce(buf, prims, materials)
    rgba = to_rgba(mat, val, dep, materials)
    for ins in insignia:
        stamp_insignia(rgba, pid, prims, rotation, ins)
    if muzzle is not None:
        add_flash(rgba, dep, muzzle, rotation, cv, flash_size)
    check_edges(rgba, what)
    return Layers(rgba, mat, dep, pid)


def render(prims: list[Prim], rotation: int, cv: Canvas, materials: dict[str, Mat] | None = None,
           **kw) -> np.ndarray:
    """One sprite, RGBA (h, w, 4): `render_layers(...).rgba`."""
    return render_layers(prims, rotation, cv, materials, **kw).rgba


# ================================================================== mirror
# Doom's paired rotations: the engine draws the second of each pair as the
# first one flipped, so a lump named SDHNA2A8 serves both (5 drawings per
# frame instead of 8). Valid only for a figure with no handed detail: an
# armband or a flag would show reversed.
MIRROR_PAIRS = {2: 8, 3: 7, 4: 6}
MIRRORED = {v: k for k, v in MIRROR_PAIRS.items()}


def drawn_rotations(mirror: bool) -> tuple[int, ...]:
    """The rotations that are actually rendered: 1-5 mirrored, 1-8 not."""
    return tuple(range(1, 6)) if mirror else tuple(range(1, ROTATIONS + 1))


def rotation_lump(sprite: str, frame: str, rotation: int, mirror: bool = False) -> str:
    """Doom's lump name: SDHNA1, or SDHNA2A8 for a mirrored pair."""
    if mirror and rotation in MIRROR_PAIRS:
        return f"{sprite}{frame}{rotation}{frame}{MIRROR_PAIRS[rotation]}"
    return f"{sprite}{frame}{rotation}"


def mirror_sprite(rgba: np.ndarray, cv: Canvas) -> np.ndarray:
    """What the engine shows for the flipped half of a pair: the image
    mirrored about the body axis. Needs the axis at the canvas centre."""
    if cv.cx * 2 != cv.w:
        raise ValueError(f"mirror mode needs the axis at the canvas centre ({cv.cx} of {cv.w})")
    return rgba[:, ::-1].copy()


def render_rotations(build: Callable[[], list[Prim]], cv: Canvas, rotations=None, *, mirror: bool = False,
                     materials: dict[str, Mat] | None = None, **kw) -> dict[int, np.ndarray]:
    """One frame at several rotations (all 8 by default). In mirror mode
    only 1-5 are traced and 6-8 are their flips, exactly as the engine will
    draw them. `build()` returns fresh primitives (posing mutates them)."""
    want = tuple(range(1, ROTATIONS + 1)) if rotations is None else tuple(rotations)
    out: dict[int, np.ndarray] = {}
    for r in want:
        src = MIRRORED.get(r) if mirror else None
        if src is not None:
            if src not in out:
                out[src] = render(build(), src, cv, materials, **kw)
            out[r] = mirror_sprite(out[src], cv)
        elif r not in out:
            out[r] = render(build(), r, cv, materials, **kw)
    return {r: out[r] for r in want}


def frame_plan(groups, mirror: bool = False) -> list[tuple[str, int]]:
    """(frame, rotation) for every lump to draw. groups: (name, frames,
    rotated); rotation 0 is one image for every angle."""
    plan = []
    for _, frames, rotated in groups:
        for f in frames:
            plan += [(f, r) for r in drawn_rotations(mirror)] if rotated else [(f, 0)]
    return plan


# ================================================================== output
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


def measure(sprite: np.ndarray, scenes=None, load: Callable[[str], np.ndarray] | None = None) -> dict:
    """Size and value. gap_<scene> is |body - wall| under that scene's light
    (gen_enemy's light stand-in; by default the flat sweep's scenes)."""
    scenes = flat.SCENES if scenes is None else scenes
    load = flat.host_rgb if load is None else load
    a = sprite[..., 3] > 0
    ys, xs = np.nonzero(a)
    body = flat.luma(sprite[..., :3])[a]
    out = {"height_px": int(ys.max() - ys.min() + 1), "width_px": int(xs.max() - xs.min() + 1),
           "lowest_row": int(ys.max()), "body_luma": round(float(body.mean()), 1)}
    f = lambda L: min(1.0, L / flat.LIGHT_FULL)  # noqa: E731
    for key, wall, light, _ in scenes:
        out[f"gap_{key}"] = round(abs(float(body.mean()) - float(flat.luma(load(wall)).mean())) * f(light), 1)
    out["worst_gap"] = min(out[f"gap_{k}"] for k, *_ in scenes)
    return out


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
    """Lossless GIF: the frames carry palette colours only (< 256), so one
    exact shared palette holds them all."""
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


def lineup(figures: list[tuple[np.ndarray, int, int]], wall: str, light: int, width: int,
           floor: str = "SDFLR2", load: Callable[[str], np.ndarray] | None = None,
           palette: list[tuple[int, int, int]] | None = None) -> np.ndarray:
    """Several sprites side by side, each placed by its own offsets (x, top),
    Doom's way: the actor stands at its slot centre, the sprite's top is
    `top` px above the floor. A MAP01 wall over a floor flat (foreshortened
    3:1), then the light, re-quantised to `palette` (v1 when None). `load`
    reads a wall or flat by lump name (gen_enemy.host_rgb by default)."""
    load = flat.host_rgb if load is None else load
    wall_h, floor_h = flat.WALL_H, flat.FLOOR_H
    w_rgb = flat.tile_to(load(wall), width, wall_h)
    fl = flat.tile_to(load(floor), width, floor_h * 3)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((width, floor_h), Image.Resampling.NEAREST))
    canvas = np.concatenate([w_rgb, fl], axis=0).copy()
    base = flat.FLOOR_LINE - FEET_SINK          # where a sprite's offset origin sits
    slot = width / len(figures)
    for i, (spr, ox, oy) in enumerate(figures):
        x0 = int(round(slot * (i + 0.5))) - ox
        y0 = base - oy
        a = spr[..., 3] > 0
        ys, xs = np.nonzero(a)
        ys2, xs2 = ys + y0, xs + x0
        keep = (ys2 >= 0) & (ys2 < canvas.shape[0]) & (xs2 >= 0) & (xs2 < width)
        canvas[ys2[keep], xs2[keep]] = spr[ys[keep], xs[keep], :3]
    return lit(canvas, light, palette)


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


# =================================================================== sheet
NEUTRAL = artlib.ramp("concrete_cold")[16]
SHEET_CSS = """
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
