"""F5 — Reich rifleman as a 3D rig, rendered at Doom's 8 rotations.

HISTORICAL since D109 (2026-10-22) for the rifleman's rig set (`SDRR`,
D38-D55). The rifleman that ships is redrawn from Google Gemini images by
tools/art/gemini_enemy.py (rifleman); this generator is kept so the approved F5
renders stay reproducible, but its output no longer matches assets/. Still
current as a library: its materials and body are imported by other generators.

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_rig.py               (Windows)
    .venv/bin/python tools/art/gen_rig.py                       (macOS)
    ... gen_rig.py --stamp 2026-10-13_2100   fixes the sheet's timestamp
    ... gen_rig.py --no-sheet                sprites only
    ... gen_rig.py --only A1,H0              a few lumps, for a quick look
    ... gen_rig.py --blood-sheet             D48's death-and-gib sheet, not the full one

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

Blood and gore. D38 drew them in BESTIARY §2.1's dark olive. D48 (CEO,
2026-10-14) asked for "much more blood in the deaths" and then chose the
colour, "rojo oscuro, nada de oliva": the death H-L and the gib M-U now
bleed dark red (flag_red 0-5 and black, palette v1), section "blood" below.
Walk, aim, fire and pain (A-G) are untouched by it, byte for byte. The
D38 olive death is still one argument away (render(..., blood=False)), for
the before/after sheet. BESTIARY §2.1's olive row is to be amended.

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
    work/art/enemies/rig/{death,gib}[_d38]_floor_S{1,2}.gif   (--blood-sheet:
        the death and gib at game speed on MAP01's floor, D48 and D38)
    docs/art/previews/<stamp>_F5_reich-rifleman-rig.html   (the sheet)
    docs/art/previews/<stamp>_F5_reich-rifleman-blood.html (--blood-sheet)
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
core.register_material("gore", Mat.on_ramp("khaki_olive", 0, 4, black_floor=True), MATERIALS)  # D38's olive (blood=False)
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
GIB_LEGS = {"leg_l", "leg_r", "skirt", "stump"}   # what stays of him and falls
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


def chunks(t: float, seed: int = SEED, n: int = N_CHUNKS, mats: tuple = CHUNK_MATS) -> list[Prim]:
    """The upper body as `n` lumps of coat, flesh and gore,
    `t` seconds after the burst; landed ones flatten on the floor. The first
    N_CHUNKS lumps are the same whatever `n` is (one random stream)."""
    rng = np.random.default_rng(seed + 1)
    out = []
    for i in range(n):
        p0 = V(rng.uniform(-6, 6), rng.uniform(30, 46), rng.uniform(-3, 3))
        side = np.sign(p0[0]) or 1.0
        v = V(side * rng.uniform(6, 30), rng.uniform(8, 42), rng.uniform(-6, 3))
        r = V(rng.uniform(1.1, 2.8), rng.uniform(1.0, 2.2), rng.uniform(1.1, 2.6))
        mat = mats[i % len(mats)]
        rest = r[1] * 0.5
        p, landed = _ballistic(p0, v, t, rest)
        if landed:
            r = r * V(1.35, 0.5, 1.35)
        out.append(ellipsoid(mat, 0.45 if mat != "flesh" else 0.40, tuple(p), tuple(r), grp="chunk"))
    return out


def build_gib(frame: str, seed: int = SEED, blood: bool = True) -> tuple[list[Prim], dict]:
    """Frame M-U of the XDeath. With `blood` (D48, the default) the burst,
    the stump's jets, the pool and N_CHUNKS_BLOODY chunks of gib_blood, the
    gore drawn red by MATERIALS_BLOOD; without it, the D38 gib as it was."""
    if frame == "M":
        prims, anchors = build_model(GIB_POSE)
        # the chest gives way: gore pushing out of the coat front
        rng = np.random.default_rng(seed + 2)
        extra = []
        for _ in range(6):
            p = V(rng.uniform(-4.5, 4.5), rng.uniform(31, 39) + GIB_POSE.bob, rng.uniform(4.6, 5.8))
            r = V(*rng.uniform(1.2, 2.4, 3))
            extra.append(ellipsoid("gore", 0.35, tuple(p), tuple(r), grp="upper"))
        prims.extend(extra)
        waist = V(0, WAIST_Y + GIB_POSE.bob, 0)
        transform(extra, {}, {"upper"}, rot_x(GIB_POSE.lean), waist)
        if blood:
            prims.extend(gib_blood(frame, 0.0, prims, seed))
        return prims, anchors
    t = GIB_T[frame]
    k = float(np.clip((t - 0.25) / 0.55, 0, 1))          # the legs: stand, buckle, fall
    k = k * k * (3 - 2 * k)
    if blood:       # D48: they buckle, then go down onto their back and lie flat (as the death's L)
        legs = replace(GIB_POSE, lean=0.0, head_pitch=0.0, bob=-0.8 - 10.0 * np.sin(np.pi * k), roll=0.0,
                       foot_l=(3.6 + 1.0 * k, ANKLE_Y, 0.8 - 4.1 * k), foot_r=(-3.4 - 0.8 * k, ANKLE_Y, -3.0),
                       stride=0.3 + (FLAT_STRIDE - 0.3) * k)
    else:
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
        roll = (90.0 if blood else 88.0) * k
        slide = V(-SLIDE * 0.45 * np.sin(np.deg2rad(roll)), 0, 0)
        if blood:
            transform(keep, {}, GIB_LEGS, rot_y(90.0 * k), V(0, 0, 0))
        transform(keep, {}, GIB_LEGS, rot_z(roll), ROLL_PIVOT, slide)
        rest_on_floor(keep, {}, GIB_LEGS)
    if blood:
        keep += gib_blood(frame, t, keep, seed)
        keep += chunks(t, seed, N_CHUNKS_BLOODY, CHUNK_MATS_BLOODY)
    else:
        if t >= 0.62:                                      # a pool spreads under him
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
            if blood:                       # D48: level, not propped on its butt
                h = R @ u
                R = _level(h) @ R
            p[2] = -2.0
        transform(parts, anc, {grp}, R, c0, p - c0)
        if landed and blood:                # D48: on the floor, not sunk into it
            rest_on_floor(parts, anc, {grp})
        keep += parts
    return keep, anchors



# =================================================================== blood
# D48 (CEO, 2026-10-14): the rifleman is OK "with much more blood in the
# deaths", and the colour is "rojo oscuro, nada de oliva": dark red, which
# overrides BESTIARY §2.1's olive Reich blood (that row is to be amended,
# and mod-engineer sets the actor's BloodColor to match). Every colour is
# palette v1's flag_red (dark end) plus true black: no v2 colour, so the
# sprites stay valid in v1 and v2 alike. The armband (flag_red 4-11, no
# shift) keeps the brightest reds; blood stops at flag_red 5.
#
# Death H-L: the round bursts out of his chest at H (droplets on ballistic
# arcs, some in front of him), the coat front soaks a wider stain each
# frame, blood runs from the mouth and down the coat, the droplets land as
# floor splats, and a pool spreads under the chest on K and grows on L.
# Gib M-U: the same burst, bigger, then three pulsing jets from the stump
# while the legs stand, more chunks, splats where things land, and a wide
# pool under the legs.
BLOOD_GRAVITY = 400.0           # units / s^2: droplets land within the death's 4 x 5 tics
GORE_LIFT = 0.18                # the gib's red gore a little lighter than the D38 olive's
MATERIALS_BLOOD: dict[str, core.Mat] = dict(MATERIALS)    # same ids; gore turns red, two added
MATERIALS_BLOOD["gore"] = Mat.on_ramp("flag_red", 0, 4, black_floor=True, lift=GORE_LIFT)
core.register_material("blood", Mat.on_ramp("flag_red", 1, 5, black_floor=True, shift=False, flat=True),
                       MATERIALS_BLOOD)                  # droplets, stains, runs: no rim, so a drop stays red
core.register_material("pool", Mat.on_ramp("flag_red", 0, 3, black_floor=True, shift=False, flat=True),
                       MATERIALS_BLOOD)                  # standing blood: darker than the spray
BLOOD_RAMP = "flag_red"
BLOOD_MAX_INDEX = 5             # no blood colour brighter than flag_red 5

DEATH_T = {"H": 0.08, "I": 0.19, "J": 0.31, "K": 0.46, "L": 3.0}   # s after the hit, 5 tics a frame
N_SPRAY = 36                    # death burst droplets
N_GIB_SPRAY = 56                # gib burst droplets
N_CHUNKS_BLOODY = 30            # D38 had 18
CHUNK_MATS_BLOODY = ("gore", "gore", "gore", "flesh", "gore", "coat", "flesh", "coat_dark", "gore", "coat")
STAIN_R = {"H": 2.4, "I": 3.4, "J": 4.2, "K": 4.9, "L": 5.6}       # chest stain half width
POOL = {"K": (8.0, 7.0), "L": (20.0, 13.0)}                          # (x, z) radii under the chest
POOL_Z = 7.0                    # pool centre in front of the body: a floor pool is seen
                                # 9 degrees from above, so its depth is what shows
SPRAY_X = 40.0                  # landed splats stay inside the canvases (check_edges)


def _torso_front(x: float, y: float, bob: float) -> float:
    """z of the coat front at (x, y), upright model space (build_model's torso_z)."""
    ty0, ty1 = 28.8 + bob, 40.0 + bob
    r = TORSO_R0 + (TORSO_R1 - TORSO_R0) * (y - ty0) / (ty1 - ty0)
    return TORSO_KZ * np.sqrt(max(r * r - x * x, 0.0)) - 0.2


def _skirt_front(y: float, stride: float) -> float:
    return coat_radius(y) * SKIRT_KZ * (1.0 + 0.16 * stride)


def _attached(prim: Prim, to: Prim) -> Prim:
    """`prim`, given in upright model space, rides `to`'s rigid transform."""
    prim.xm, prim.xt, prim.grp = to.xm.copy(), to.xt.copy(), "blood"
    return prim


def _tagged(prims: list[Prim], tag: str) -> Prim:
    return next(p for p in prims if p.tag == tag)


def _droplet(p0, v, t: float, r: float, grav: float = BLOOD_GRAVITY) -> Prim:
    """A blood droplet `t` s after leaving p0 at v: a drop in the air, a
    flat splat once it has landed."""
    rest = r * 0.3
    tl = (v[1] + np.sqrt(v[1] ** 2 + 2 * grav * max(p0[1] - rest, 0.0))) / grav
    tt = min(t, tl)
    p = p0 + v * tt + V(0, -0.5 * grav * tt * tt, 0)
    if t >= tl:
        x = float(np.clip(p[0], -SPRAY_X, SPRAY_X))
        return ellipsoid("blood", 0.42, (x, 0.2, p[2]), (r * 2.0, 0.35, r * 1.5), grp="splat")
    return ellipsoid("blood", 0.62, tuple(p), (r, r * 1.15, r), grp="spray")


def burst(origin, t: float, n: int, rng, speed=(30.0, 90.0)) -> list[Prim]:
    """A round's spray: n droplets thrown from `origin` mostly sideways, up
    and away from the camera (the exit), some towards it (the entry), and
    every sixth a heavy gout that drops close by."""
    out = []
    for i in range(n):
        d = V(rng.uniform(-1, 1), rng.uniform(-0.25, 1.0), rng.uniform(-1.0, 0.45))
        d /= np.linalg.norm(d)
        gout = i % 6 == 0
        sp = rng.uniform(6, 22) if gout else rng.uniform(*speed)
        r = rng.uniform(1.3, 1.8) if gout else rng.uniform(0.65, 1.15)
        out.append(_droplet(V(*origin), d * sp, t, r))
    return out


def pool(cx: float, cz: float, rx: float, rz: float, rng) -> list[Prim]:
    """A pool on the floor: one flat ellipse and three lobes, so its edge is
    not a perfect oval."""
    out = [ellipsoid("pool", 0.55, (cx, 0.3, cz), (rx, 0.55, rz), grp="pool")]
    for _ in range(3):
        ox, oz = rng.uniform(-0.7, 0.7) * rx, rng.uniform(-0.3, 0.6) * rz
        out.append(ellipsoid("pool", 0.62, (cx + ox, 0.32, cz + oz),
                             (rx * rng.uniform(0.35, 0.55), 0.6, rz * rng.uniform(0.4, 0.6)), grp="pool"))
    return out


def death_blood(frame: str, prims: list[Prim], seed: int = SEED) -> list[Prim]:
    """The blood of death frame H-L, for the posed `prims` of that frame."""
    pose = FALL_POSES[frame]
    t = DEATH_T[frame]
    bob = pose.bob
    torso = _tagged(prims, "torso")
    out: list[Prim] = []
    # the wound and its stain, soaking wider each frame (rides the torso)
    sx, sy = 0.8, 35.0 + bob
    zf = _torso_front(sx, sy, bob)
    s = STAIN_R[frame]
    out.append(_attached(ellipsoid("blood", 0.50, (sx, sy - s * 0.25, zf - 0.3), (s, s * 1.2, 1.1)), torso))
    out.append(_attached(ellipsoid("blood", 0.24, (sx, sy, zf + 0.15), (1.0, 1.0, 0.8)), torso))   # the hole
    if frame in "JKL":                    # it runs down the coat front
        skirt = _tagged(prims, "skirt")
        k = "JKL".index(frame)
        y0, y1 = WAIST_Y - 1.0, WAIST_Y - 6.0 - 3.0 * k
        out.append(_attached(rcone("blood", 0.40, (1.2, y0 + bob, _skirt_front(y0, pose.stride) + 0.2),
                                   (1.8, y1 + bob, _skirt_front(y1, pose.stride) + 0.2), 1.3, 0.9), skirt))
    # from the mouth (rides the head)
    mouth = min((p for p in prims if p.grp == "head" and p.mat == "void"), key=lambda p: float(np.max(p.r)))
    if frame in "IJKL":
        m = mouth.a
        run = 2.0 + 1.2 * "IJKL".index(frame)
        out.append(_attached(rcone("blood", 0.45, m + V(0.3, -0.3, 0.2), m + V(0.6, -run, -0.2), 0.75, 0.55),
                             mouth))
    # the burst left his chest at H; where those droplets are now
    p_h, _ = build_model(POSES["H"])
    th = _tagged(p_h, "torso")
    origin = th.xm @ V(sx, 35.0 + POSES["H"].bob, _torso_front(sx, 35.0, 0.0)) + th.xt
    out += burst(origin, t, N_SPRAY, np.random.default_rng(seed + 11), speed=(40.0, 120.0))
    # the wound bleeds while he falls: a short dribble under the hole
    wound = torso.xm @ V(sx, sy, zf + 0.4) + torso.xt
    if frame in "IJ":
        rng = np.random.default_rng(seed + 12 + "IJ".index(frame))
        for k in range(5):
            age = 0.02 + 0.03 * k
            out.append(_droplet(wound, V(rng.uniform(-3, 3), rng.uniform(-4, 2), rng.uniform(6, 14)), age,
                                rng.uniform(0.6, 0.9)))
    if frame in POOL:                     # the pool under the chest, growing K -> L
        rx, rz = POOL[frame]
        out += pool(float(wound[0]) - 1.0, POOL_Z, rx, rz, np.random.default_rng(seed + 14))
        head = mouth.xm @ mouth.a + mouth.xt
        out += pool(float(head[0]), POOL_Z - 2.0, 3.0 + 1.5 * (frame == "L"), 4.0, np.random.default_rng(seed + 15))
    return out


GIB_JETS = ((V(-16.0, 104.0, 6.0), 0.00), (V(3.0, 118.0, 9.0), 0.04), (V(19.0, 98.0, 4.0), 0.02))
JET_STEP = 0.022                # s between two drops of a jet
JET_PULSE = 0.13                # s, the heart's beat in the jet
JET_END = 0.75                  # the jets stop when the legs are down


def gib_blood(frame: str, t: float, prims: list[Prim], seed: int = SEED) -> list[Prim]:
    """The blood of gib frame M-U, `t` s after the burst, for `prims`."""
    out: list[Prim] = []
    base, _ = build_model(GIB_POSE)
    tb = _tagged(base, "torso")
    origin = tb.xm @ V(0.0, 35.0 + GIB_POSE.bob, _torso_front(0.0, 35.0, 0.0)) + tb.xt
    out += burst(origin, max(t, 0.04), N_GIB_SPRAY, np.random.default_rng(seed + 21), speed=(35.0, 105.0))
    if frame == "M":
        return out
    stump = [p for p in prims if p.grp == "stump" and p.mat == "gore"]
    top = stump[0].bound()[0] + V(0, 1.5, 0) if stump else origin
    rng = np.random.default_rng(seed + 22)
    for v, lag in GIB_JETS:
        s = lag
        while s <= min(t, JET_END):
            pulse = 0.72 + 0.28 * np.cos(2 * np.pi * (s - lag) / JET_PULSE)
            fade = max(0.0, 1.0 - s / JET_END)
            vv = v * pulse * (0.45 + 0.55 * fade) + V(*rng.uniform(-4, 4, 3))
            out.append(_droplet(top, vv, t - s, rng.uniform(0.7, 1.05)))
            s += JET_STEP
    if t >= 0.46:                         # the pool under him, growing until U
        g = min((t - 0.46) / 0.7, 1.0)
        out += pool(0.0, POOL_Z, 9.0 + 15.0 * g, 6.0 + 7.0 * g, np.random.default_rng(seed + 23))
    return out



# ================================================================ the fall
# D48 follow-up (CEO, on the Legion's corpse from the same rig: "parece que
# se apoye en el hombro; debería quedar un tumbado más natural y real").
# D38's corpse lay on his left side, propped on his left shoulder and arm
# with the crested helmet under his head. The D48 fall keeps H and I (the
# hit, the knees), and from J he falls to his left AND turns onto his back:
# each frame is the upright figure turned about his own vertical axis
# (`twist`, front towards the ceiling at 90) and then rolled to his left
# (`roll`, about the floor line under his left sole, as Pose.roll). At K
# the Stahlhelm comes off and rolls away; at L he lies flat on his back:
# shoulders, hips, legs and the bare head on the floor, the coat skirt
# spread flat (a negative stride squashes it), arms loose on the floor, the
# rifle on the floor in front of him.
@dataclass(frozen=True)
class Lie:
    roll: float                 # degrees, to his left about ROLL_PIVOT (Pose.roll)
    twist: float                # degrees about his own vertical axis first: 90 = on his back
    slide: float                # x shift, so the corpse lies across the axis
    helmet: tuple | None = None  # (dx past the head, z, lie degrees): off and on the floor; None = worn


FLAT_STRIDE = -1.5              # the greatcoat's skirt flattened on the floor (open_kz x 0.76)
FALL_RIFLE = ((-20.0, 1.0, 13.0), (1.0, 0.0, -0.08), (0.0, 0.0, -1.0))   # on the floor, in front of him
FALL_POSES = {
    "H": POSES["H"],
    "I": POSES["I"],
    "J": Pose("J", "falling, turning", (3.6, ANKLE_Y, 1.2), (-3.4, ANKLE_Y, 0.0), -9.0, "free", 0.2,
              lean=14.0, head_pitch=18.0, hand_l=(13.0, 36.0, -1.0), hand_r=(-9.0, 30.0, 6.0),
              rifle_at=((-16.0, 2.5, 6.0), (0.99, -0.15, 0.0), (0.0, 1.0, 0.0)), canvas=DEATH),
    # down, rolling onto his back: the left arm comes over his front (not under
    # him), the right leg not down yet
    "K": Pose("K", "hits the floor, onto his back", (4.0, ANKLE_Y, -2.5), (-3.8, ANKLE_Y, -2.0), -3.0, "free",
              FLAT_STRIDE * 0.6, lean=4.0, head_pitch=25.0, hand_l=(9.0, 22.0, 5.0),
              hand_r=(-14.0, 30.0, -2.0), rifle_at=FALL_RIFLE, canvas=DEATH),
    # flat: the heels back to the plane of his shoulder blades (feet z), the arms
    # out straight at that plane, the chin up until the bare head meets the floor
    "L": Pose("L", "dead, flat on his back", (4.6, ANKLE_Y, -3.3), (-4.2, ANKLE_Y, -3.0), 0.0, "free",
              FLAT_STRIDE, head_pitch=38.0, hand_l=(17.0, 24.0, -3.0), hand_r=(-17.0, 25.0, -3.0),
              rifle_at=FALL_RIFLE, canvas=DEATH),
}
LIES = {
    "H": None, "I": None,                               # still on his feet: POSES' own roll
    "J": Lie(42.0, 28.0, SLIDE * 0.67),
    "K": Lie(90.0, 70.0, SLIDE, helmet=(7.0, 1.0, 60.0)),
    "L": Lie(90.0, 90.0, SLIDE, helmet=(13.0, -3.0, 180.0)),
}
FLAT_TOL = 1.2                  # units: a part this close to the floor rests on it
FLAT_PARTS = ("upper", "skirt", "leg_l", "leg_r", "head")   # what must rest on the floor at L


def _level(u: np.ndarray) -> np.ndarray:
    """The rotation about z that takes u (in the xy plane) to horizontal."""
    for sign in (1.0, -1.0):
        R = rot_z(sign * np.degrees(np.arctan2(u[1], u[0])))
        if abs((R @ u)[1]) < 1e-9:
            return R
    raise ValueError("no level rotation")   # pragma: no cover


def build_fall(frame: str) -> tuple[list[Prim], dict]:
    """Death frame H-L of D48: posed, turned, rolled and resting on the floor."""
    pose = FALL_POSES[frame]
    lie = LIES[frame]
    if lie is None:
        return build_model(pose)
    prims, anchors = build_model(replace(pose, roll=0.0))
    slide = V(-lie.slide * np.sin(np.deg2rad(lie.roll)), 0, 0)
    transform(prims, anchors, ALL_BODY, rot_y(lie.twist), V(0, 0, 0))
    transform(prims, anchors, ALL_BODY, rot_z(lie.roll), ROLL_PIVOT, slide)
    rest_on_floor(prims, anchors, ALL_BODY - ({"helmet"} if lie.helmet is not None else set()))
    if lie.helmet is not None:              # off, on its side on the floor past his head
        dx, z, deg = lie.helmet
        hel = [p for p in prims if p.grp == "helmet"]
        c0 = np.mean([p.bound()[0] for p in hel], axis=0)
        head = anchors["head"][0]
        target = V(head[0] + dx, c0[1], z)
        transform(prims, anchors, {"helmet"}, rot_x(deg), c0, target - c0)
        rest_on_floor(prims, anchors, {"helmet"})
    if pose.rifle_at == FALL_RIFLE:         # dropped: on the floor, not sunk into it
        rest_on_floor(prims, anchors, {"rifle"})
    return prims, anchors


def resting(prims: list[Prim], parts=FLAT_PARTS) -> dict[str, float]:
    """How high each part's lowest point is above the floor (units)."""
    return {g: lowest_y([p for p in prims if p.grp == g]) for g in parts}


# ================================================================ renderer
def stamp_symbol(rgba: np.ndarray, pid: np.ndarray, prims: list[Prim], rotation: int) -> bool:
    """The D12 armband symbol on the band's visible centre, when the band's
    outer face is not turned away. Returns whether it was stamped."""
    return core.stamp_insignia(rgba, pid, prims, rotation, ARMBAND)


def frame_canvas(frame: str) -> Canvas:
    return GIB if frame in GIB_FRAMES else POSES[frame].canvas


BLOODY_FRAMES = "HIJKL" + GIB_FRAMES   # D48: the frames that bleed; A-G never change


def build_frame(frame: str, seed: int = SEED, blood: bool = True) -> tuple[list[Prim], dict, dict]:
    """The posed primitives of one frame, its anchors and its material
    table. `blood` (D48, the default) only touches H-U; A-G build exactly
    as D38 approved them, on MATERIALS."""
    blood = blood and frame in BLOODY_FRAMES
    if frame in GIB_FRAMES:
        prims, anchors = build_gib(frame, seed, blood)
    else:
        prims, anchors = build_fall(frame) if blood else build_model(POSES[frame])
        if blood:
            prims = prims + death_blood(frame, prims, seed)
    return prims, anchors, (MATERIALS_BLOOD if blood else MATERIALS)


def render(frame: str, rotation: int, seed: int = SEED, blood: bool = True) -> np.ndarray:
    """One sprite, RGBA (h, w, 4). blood=False is the D38 death and gib."""
    cv = frame_canvas(frame)
    prims, anchors, table = build_frame(frame, seed, blood)
    flash = frame in POSES and POSES[frame].flash
    return core.render(prims, rotation, cv, table, seed=seed, value_shift=VALUE_SHIFT, insignia=(ARMBAND,),
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
    "the symbol on a band seen edge-on, a convention. The gib's chunks are blobs, and some land up to 3 px "
    "below the sole line (the dropped rifle of the death, 2 px). Since D48 the death and gib bleed dark "
    "red, generously; the olive blood of D38 read weakly on a dark floor (the D48 blood sheet).",
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
    "Answered since: the blood. D48 approved him with much more blood in the deaths, in dark red, not "
    "olive; the D48 blood sheet shows it.",
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
                 + [sprite_tile(sprites[(f, 0)], 3, lump_name(f, 0), FALL_POSES[f].title) for f in "HIJKL"])
    body += strip([gif_tile(gif_dir / "gib.gif", 4, "gib (XDeath)", "M-T 5 tics, U stays")])
    body += strip([sprite_tile(sprites[(f, 0)], 2, lump_name(f, 0)) for f in GIB_FRAMES])
    S.append(("5 · Death H-L and gib M-U (rotation 0: one image for every angle)",
              "Death: hit, knees go, he falls to his left, rolls onto his back and lies flat (D48). Gib: the chest gives way, the "
              "upper body goes up in chunks, the crested helmet and the rifle fly whole and land, the legs "
              "stand a moment and fall. Blood and gore are dark red since D48 (\"rojo oscuro, nada de "
              "oliva\"), flag_red 0-5 and black, darker than the armband (flag_red 4-11).", body))

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


# ============================================================ blood sheet
# D48's preview: the death and the gib with the dark-red blood, animated at
# game speed at 1x on MAP01's floor, beside D38's olive version.
FLOOR_SCENES = (("S1", "SDCONC1", 128, "corridor Z3/Z5"), ("S2", "SDSTEL1", 176, "hangar dado"))
DEATH_TICS = (20, 5, 5, 5, 5, 70)          # A (still standing), H I J K 5 tics (BESTIARY §3), L held
GIB_TICS = (20,) + (5,) * 8 + (70,)        # A, M-T 5 tics, U held


def floor_frames(sprites: dict, frames: str, cv: Canvas, wall: str, light: int) -> list[np.ndarray]:
    """Frame A1 then `frames` at rotation 0, each placed by its own offsets
    on a MAP01 wall over SDFLR2, in the scene's light (the lineup stand-in)."""
    out = []
    for f in "A" + frames:
        spr = pad_to(sprites[("A", 1)], STAND, cv) if f == "A" else sprites[(f, 0)]
        out.append(lineup([(spr, cv.cx, cv.foot_row - FEET_SINK)], wall, light, cv.w))
    return out


def write_floor_gifs(sprites: dict, out_dir: Path = OUT_DIR, tag: str = "") -> dict[str, Path]:
    """death_floor_<scene>.gif and gib_floor_<scene>.gif, at game speed
    (`tag` names a variant, e.g. "_d38")."""
    t = lambda n: int(round(n * TIC_MS))  # noqa: E731
    out = {}
    for key, wall, light, _ in FLOOR_SCENES:
        out[f"death_{key}"] = save_gif(floor_frames(sprites, "HIJKL", DEATH, wall, light),
                                       [t(n) for n in DEATH_TICS], out_dir / f"death{tag}_floor_{key}.gif")
        out[f"gib_{key}"] = save_gif(floor_frames(sprites, GIB_FRAMES, GIB, wall, light),
                                     [t(n) for n in GIB_TICS], out_dir / f"gib{tag}_floor_{key}.gif")
    return out


def blood_colours() -> set[tuple[int, int, int]]:
    """Every colour the D48 blood can paint: flag_red 0..BLOOD_MAX_INDEX."""
    return {tuple(c) for c in core.ramp(BLOOD_RAMP)[:BLOOD_MAX_INDEX + 1]}


def red_pixels(rgba: np.ndarray) -> int:
    """Opaque pixels in blood_colours() (the armband's darkest shades count too)."""
    reds = blood_colours()
    px = rgba[rgba[..., 3] > 0][:, :3]
    return sum(1 for c in map(tuple, px.tolist()) if c in reds)


def _swatch(cols, label: str) -> str:
    sw = "".join(f'<i style="background:rgb({c[0]},{c[1]},{c[2]})"></i>' for c in cols)
    return f'<div class="ramp"><span class="n">{html.escape(label)}</span><span class="sw">{sw}</span></div>'


BLOOD_VERDICT = [
    "THE FALL. D38's corpse lay on his left side, propped on his left shoulder and arm with the helmet "
    "under his head (the complaint the Legion's corpse got: \"parece que se apoye en el hombro\"). Now "
    "H and I are as approved, and from J he falls to his left while turning onto his back; at K he is "
    "down with the right leg still coming over and the Stahlhelm off; at L he lies flat on his back: "
    "shoulders, hips, both legs and the bare head on the floor (each within FLAT_TOL = 1.2 units, "
    "tested), the coat skirt flattened, the arms loose on the floor, the rifle and the helmet beside him "
    "on the floor, not sunk into it. The corpse is 20 px tall instead of 38. In the gib, the legs that "
    "stay now go down onto their back too and lie flat (U), and the helmet and the rifle rest on the "
    "floor level (D38 sank them up to 4 units and left the rifle propped on its butt).",
    "WHAT IT DOES. Death: at H the round bursts out of his chest (36 droplets on ballistic arcs, a third "
    "thrown towards you) and the wound opens on the coat; the stain soaks wider every frame (half width "
    "2.4 to 5.6 px), blood runs from the mouth (I-L) and down the coat front (J-L), the droplets land as "
    "splats around him, and a pool spreads under his chest on K and grows on L, with a smaller one under "
    "the head. Gib: a bigger burst (56 droplets), three pulsing jets from the stump while the legs stand "
    "(N-R), 30 chunks instead of 18, red gore, splats, and a pool that grows under the legs until U. "
    "Every blood colour is flag_red 0-5 and black from palette v1, darker than the armband (flag_red 4-11 "
    "unshaded), so the symbol still reads and nothing needs palette v2.",
    "WHAT DOES NOT, HONESTLY. Doom draws a floor pool on a sprite, and our camera looks down only 9 "
    "degrees, so the pool is a band 3 to 5 px deep in front of the body, not a puddle seen from above; "
    "it is pushed forward of the body (POOL_Z) to show at all. For the same reason a man flat on his "
    "back shows his side, so the chest wound reads as a red line along his top edge on L, not a "
    "patch. At 1x the droplets are 1-2 px dots: they "
    "read as spray in motion, as Doom's own do, and as noise on a still. Frame H holds the burst for 5 "
    "tics only, so the strongest read of the hit is GZDoom's own blood puff, not this sprite (next "
    "paragraph). The light stand-in is NOT VERIFIED against GZDoom.",
    "THE REST OF THE GAME. Today GZDoom sprays Freedoom's blood when you hit him (BLUD, red; the 2026-10-13 "
    "23:10 overlay evidence shows it), because SD_ReichRifleman sets no BloodColor. That red is a pure, "
    "more saturated red of about the same darkness (BLUD averages RGB 115, 0, 0; our mid tone is 97, 22, "
    "19; section 3), so the dark-red death sits in the same family and does not fight it, where an olive "
    "death would have clashed with a red hit puff. To make hit and death one colour, "
    "mod-engineer can set BloodColor on SD_ReichRifleman to a dark red near flag_red 3, RGB (97, 22, "
    "19); BloodColor recolours the stock blood (BESTIARY §2.1 says so; the syntax and the on-screen "
    "result are NOT VERIFIED here, and are mod-engineer's and the PM's engine pass). BESTIARY §2.1 "
    "(\"Blood: dark olive\") and §3 (\"Olive blood\") must be amended to dark red for the Reich.",
]
BLOOD_ASK = [
    "Approve the death H-L and gib M-U as drawn: with A-G (byte-identical to the 2026-10-13 rig you "
    "approved) the 70 SDRR lumps are ready for assets/sprites/ and mod-engineer's POSS-to-SDRR swap.",
    "Or name the dose: more or fewer droplets, a bigger pool, longer jets; each is one constant in "
    "gen_rig.py (N_SPRAY, POOL, GIB_JETS), one more render.",
]


def build_blood_sheet(sprites: dict, stamp: str, out_dir: Path = PREVIEW_DIR, seed: int = SEED,
                      gif_dir: Path = OUT_DIR) -> Path:
    """The D48 sheet. `sprites` holds the D48 renders (at least A1 and H-U at 0)."""
    S = []
    old = {("A", 1): sprites[("A", 1)]}
    for f in BLOODY_FRAMES:
        old[(f, 0)] = render(f, 0, seed, blood=False)
    now_gifs = write_floor_gifs(sprites, gif_dir)
    old_gifs = write_floor_gifs(old, gif_dir, "_d38")

    def strip(items):
        return '<div class="strip">' + "".join(items) + "</div>"

    # 1. animated on MAP01's floor
    body = ""
    for key, wall, light, what in FLOOR_SCENES:
        sub = f"{wall} over SDFLR2, light {light}"
        body += strip([gif_tile(now_gifs[f"death_{key}"], 1, f"death, 1x, {key}", sub),
                       gif_tile(now_gifs[f"gib_{key}"], 1, f"gib, 1x, {key}", sub),
                       gif_tile(now_gifs[f"death_{key}"], 3, f"death, 3x, {key}", what),
                       gif_tile(now_gifs[f"gib_{key}"], 3, f"gib, 3x, {key}", what)])
    body += strip([gif_tile(old_gifs["death_S1"], 1, "D38 death, 1x", "before: olive, no pool"),
                   gif_tile(old_gifs["gib_S1"], 1, "D38 gib, 1x", "before"),
                   gif_tile(old_gifs["death_S1"], 3, "D38 death, 3x", "before"),
                   gif_tile(old_gifs["gib_S1"], 3, "D38 gib, 3x", "before")])
    S.append(("1 · At game speed, on MAP01's floor",
              "Each loop starts on frame A1 (he is standing, 20 tics), then the state as the engine plays "
              "it: Death H I J K at 5 tics and L held; XDeath M to T at 5 tics and U held (BESTIARY §3, 35 "
              "tics a second). The 1x tiles are the size the sprite is drawn on a 320x200 screen at 1:1 "
              "distance. Last row: the D38 version (olive, no pool, propped on his shoulder), for comparison.",
              body))

    # 2. frame by frame
    body = strip([sprite_tile(sprites[(f, 0)], 4, lump_name(f, 0), FALL_POSES[f].title) for f in "HIJKL"])
    body += strip([sprite_tile(sprites[(f, 0)], 3, lump_name(f, 0)) for f in GIB_FRAMES])
    body += strip([sprite_tile(old[(f, 0)], 2, lump_name(f, 0), "D38") for f in "HIJKL" + GIB_FRAMES])
    S.append(("2 · Frame by frame (rotation 0: one image for every angle)",
              "Death at 4x, gib at 3x, on neutral grey; the D38 frames at 2x below.", body))

    # 3. the colour, against the rest of the game
    cols_blood = MATERIALS_BLOOD["blood"].colours()
    body = ('<div class="ramps">'
            + _swatch(cols_blood, "blood (spray, stain)")
            + _swatch(MATERIALS_BLOOD["pool"].colours(), "pool")
            + _swatch(MATERIALS_BLOOD["gore"].colours(), "gore (gib)")
            + _swatch(MATERIALS["band"].colours(), "armband (D12)")
            + _swatch(MATERIALS["gore"].colours(), "D38 olive (retired)")
            + "</div>")
    refs = []
    blud = [b for b in (freedoom_sprite(n) for n in ("BLUDA0", "BLUDB0", "BLUDC0")) if b]
    for n, b in zip(("BLUDA0", "BLUDB0", "BLUDC0"), blud):
        refs.append(sprite_tile(b[0], 6, n, "Freedoom blood"))
    poss = freedoom_sprite("POSSL0")
    if poss:
        refs.append(sprite_tile(poss[0], 3, "POSSL0", "Freedoom zombieman, dead"))
    refs.append(sprite_tile(sprites[("L", 0)], 3, "SDRRL0", "ours, dead"))
    body += strip(refs)
    note = ""
    if blud:
        px = np.concatenate([b[0][b[0][..., 3] > 0][:, :3] for b in blud])
        mean = tuple(int(v) for v in px.mean(axis=0))
        note = f" Freedoom's BLUD pixels average RGB {mean}; our blood's mid tone is {cols_blood[3]}."
    S.append(("3 · The colour, and the blood the game already shows",
              "flag_red 0-5 and black, all palette v1. Freedoom's blood (BLUD) is what GZDoom sprays when "
              "you hit him today; shown for comparison only (freedoom2.wad 0.13.0, BSD-3)." + html.escape(note),
              body))

    # 4. numbers
    rows = []
    for f in BLOODY_FRAMES:
        m, o = measure(sprites[(f, 0)]), measure(old[(f, 0)])
        rows.append([lump_name(f, 0), red_pixels(old[(f, 0)]), red_pixels(sprites[(f, 0)]),
                     f"{m['height_px']} x {m['width_px']}", m["lowest_row"] - frame_canvas(f).foot_row,
                     o["lowest_row"] - frame_canvas(f).foot_row])
    body = sheetlib.table(["lump", "red px D38", "red px D48", "h x w px D48", "below sole D48",
                           "below sole D38"], rows)
    body += ("<p class=\"lead\">Red px counts opaque pixels in flag_red 0-5, the blood's colours; the "
             "armband's darker shades would count too, and the D38 column shows they add none. Below sole: "
             "rows under the sole line; the "
             "pool lies in front of the body on the floor, so it sits a few rows lower, as a Doom corpse's "
             f"pool does. Canvas: death {DEATH.w}x{DEATH.h}, gib {GIB.w}x{GIB.h}, unchanged.</p>")
    S.append(("4 · Numbers", "", body))

    # 5. verdict and the ask
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in BLOOD_VERDICT) + "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in BLOOD_ASK) \
            + "</ol></div>"
    S.append(("5 · Honest verdict and what you decide", "", body))

    intro = ("D48: the rig's rifleman is approved \"with much more blood in the deaths\", and the colour is "
             "\"rojo oscuro, nada de oliva\"; and a corpse must lie flat, not propped on a shoulder (the "
             "CEO on the Legion's corpse, same rig). This redoes the death H-L and the gib M-U only; walk, aim, fire "
             "and pain (A-G, 56 lumps) are byte-identical to the approved rig. Built by "
             "<code>tools/art/gen_rig.py</code>, section \"blood\", seed " + str(seed) +
             ". Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_rig.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic, no "
              "system fonts. Freedoom sprites shown for comparison only, from freedoom2.wad 0.13.0, "
              "BSD-3-Clause (© the Freedoom contributors), not used as a source.")
    path = out_dir / f"{stamp}_F5_reich-rifleman-blood.html"
    sheetlib.write_sheet(path, lang="en", title="Reich rifleman — death and gib with blood (F5, D48)",
                         subtitle="SDRR H-U · dark red · draft for the CEO's gate",
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
    ap.add_argument("--blood-sheet", action="store_true",
                    help="write D48's death-and-gib blood sheet instead of the full rig sheet")
    args = ap.parse_args()
    only = {s.strip().upper() for s in args.only.split(",") if s.strip()} or None
    if args.sheet_only:
        sprites = load_sprites()
    else:
        sprites = build_all(seed=args.seed, only=only)
    if only or args.no_sheet:
        return
    if args.blood_sheet:
        path = build_blood_sheet(sprites, args.stamp, seed=args.seed)
    else:
        path = build_sheet(sprites, args.stamp, seed=args.seed)
    print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
