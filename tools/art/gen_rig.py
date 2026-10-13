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

Since the rig_core refactor (2026-10-13) that machinery (primitives, IK,
tracer, majority vote, contour and rim, the insignia stamp, the flash,
grAb, GIFs, lineups, the Freedoom reader, sheet tiles) lives in
tools/art/rig_core.py, shared by every enemy on the rig; this module is the
rifleman's FIGURE: his materials, proportions, poses, gib, frame plan, GIFs
and sheet. It re-exports the core's names (gen_rig.V, gen_rig.two_bone,
gen_rig.save_sprite ... still work). The refactor was checked to leave every
PNG this script writes byte-identical.

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
import datetime as dt
import html
import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from PIL import Image

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402  (the approved cell E, its materials, scene helpers)
import rig_core as core  # noqa: E402  (the shared rig: primitives, IK, renderer, output)
import sheetlib  # noqa: E402
from rig_core import (  # noqa: E402,F401  re-exported: the rifleman's module keeps its names
    AIM, ANKLE_Y, AO_DIST, AO_WEIGHT, CENTRE, CONTOUR_STEPS, COVER_MIN, CULL_MARGIN, DEPTH_EDGE,
    DOOM_HEIGHT, FEET_SINK, FLASH_SIZE, FLOOR_STEP, GRAIN, GRAIN_CELL, HIP_Y, HIT_EPS, LEFT, LIGHT,
    LIGHT_BANDS, MAX_STEPS, NEUTRAL, NORMAL_H, PITCH_DEG, RIGHT, RIM_STEPS, ROTATIONS, SHADE_GAIN, SHIN,
    SS, STAND, STEP_SCALE, T0, T_SPAN, THIGH, TIC_MS, VERTICAL_FALLOFF, Canvas, Prim, Scene, V, add_flash,
    box, camera, ccone, ellipsoid, freedoom_sprite, gif_tile, grab_offsets, hash3, lineup, lowest_y,
    measure, on_bg, pad_to, png_uri, project, rcone, read_grab, rest_on_floor, rot_x, rot_y, rot_z,
    save_gif, save_sprite, sprite_tile, tile, transform, two_bone, yaw_matrix)

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "rig"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"

SPRITE = "SDRR"                 # BESTIARY §3, MOD-SPEC §6.3
SEED = 38                       # D38; cloth grain and the gib's chunks

# STAND (64x72) and AIM (96x72) are the core's humanoid canvases.
DEATH = Canvas(96, 80, 48, 72)  # a corpse lies across; the dropped rifle lands nearer the camera
GIB = Canvas(96, 88, 48, 80)    # the helmet flies higher than his head; chunks land nearer the camera

VALUE_SHIFT = -0.26             # whole figure darker: the flat cell E's body luma (~65)

# ================================================================ materials
# gen_enemy's materials (core.MATERIALS, with their cloth / no-shift / flat
# traits) plus the armband and the olive gore, appended so no id moves.
Mat = core.Mat
MATERIALS: dict[str, core.Mat] = dict(core.MATERIALS)
core.register_material("band", Mat.on_ramp("flag_red", 4, 11, shift=False), MATERIALS)
core.register_material("gore", Mat.on_ramp("khaki_olive", 0, 4, black_floor=True), MATERIALS)  # BESTIARY §2.1: olive blood
ARMBAND = core.ARMBAND          # the D12 armband: 7x7, on the band's outer face, never mirrored


# ==================================================================== rig
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
    def label(start: int, limb: str, side: int) -> None:
        """Tag what was added since `start` as one limb of one side."""
        for prim in P[start:]:
            prim.limb, prim.side = limb, side

    for side, foot, grp in ((LEFT, pose.foot_l, "leg_l"), (RIGHT, pose.foot_r, "leg_r")):
        start = len(P)
        hip = V(side * 3.4, HIP_Y + bob, 0.0)
        knee, ankle = two_bone(hip, foot, THIGH, SHIN, V(0, 0, 1))
        add(grp, rcone("coat_dark", 0.35, hip, knee, 2.7, 2.3))           # breeches, mostly hidden
        add(grp, rcone("leather", 0.55, knee, ankle, 2.4, 2.05))          # jackboot shaft
        add(grp, box("leather", 0.30, (ankle[0], ankle[1] - 1.15, ankle[2] + 1.3),
                     (1.6, 1.1, 3.0), rnd=0.6))                           # foot
        label(start, "leg", side)

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
    for side in (LEFT, RIGHT):
        start = len(P)
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
        label(start, "arm", side)

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
def stamp_symbol(rgba: np.ndarray, pid: np.ndarray, prims: list[Prim], rotation: int) -> bool:
    """The D12 armband symbol on the band's visible centre, when the band's
    outer face is not turned away. Returns whether it was stamped."""
    return core.stamp_insignia(rgba, pid, prims, rotation, ARMBAND)


def frame_canvas(frame: str) -> Canvas:
    return GIB if frame in GIB_FRAMES else POSES[frame].canvas


def render(frame: str, rotation: int, seed: int = SEED) -> np.ndarray:
    """One sprite, RGBA (h, w, 4)."""
    cv = frame_canvas(frame)
    if frame in GIB_FRAMES:
        prims, anchors = build_gib(frame, seed)
    else:
        prims, anchors = build_model(POSES[frame])
    flash = frame in POSES and POSES[frame].flash
    return core.render(prims, rotation, cv, MATERIALS, seed=seed, value_shift=VALUE_SHIFT, insignia=(ARMBAND,),
                       muzzle=anchors["muzzle"][0] if flash else None, what=f"{frame}{rotation}")


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
    """All 8 rotations, not the mirrored pairs: the armband is on his left
    arm and the rifle on his right hip (module docstring)."""
    return core.frame_plan(FRAME_GROUPS, mirror=False)


def lump_name(frame: str, rotation: int) -> str:
    return f"{SPRITE}{frame}{rotation}"



# ============================================================ GIFs, scenes
def scene_rgb(sprite: np.ndarray, cv: Canvas, wall: str, light: int) -> np.ndarray:
    """The figure before a MAP01 wall over SDFLR2, both in the same light
    (gen_enemy's stand-in), soles on the flat sweep's floor line."""
    return lineup([(sprite, cv.cx, cv.foot_row - FEET_SINK)], wall, light, sprite.shape[1])


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
EXTRA_CSS = core.SHEET_CSS


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
