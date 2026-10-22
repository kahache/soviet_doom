"""F5 — the Reich hound redrawn as a German shepherd (D48), on rig_core's quadruped skeleton.

HISTORICAL since D109 (2026-10-22) for the hound's rig set (`SDHN`, D50, D55).
The hound that ships is redrawn from Google Gemini images by
tools/art/gemini_enemy.py (hound); this generator is kept so the approved F5
renders stay reproducible, but its output no longer matches assets/.

Why. The CEO's art gate of 2026-10-14 (D48, docs/PRD.md) rejected every cell
of the first hound sweep (gen_storm.py, "muy feo en todas") and asked for a
German shepherd, brown, drawn from a real one's anatomy. D48 supersedes
D45's darker khaki hide. This module is that redraw; gen_storm.py and
rig_core.py are imported and NOT edited (another figure uses them).

The breed, as built (from the standard anatomy of the German shepherd, no
reference image downloaded):
  * head: a WEDGE seen from above and from the side, skull and muzzle about
    equal in length, a marked STOP (the forehead steps down to the muzzle),
    black nose, dark mask over the muzzle and round the eyes, tan "pips"
    over the eyes, a dark line down the top of the skull;
  * ears: large, ERECT, triangular, set high, opening forward;
  * neck: strong, carried forward at about 45 degrees standing, lower in the
    gallop, with a RUFF (gorguera) of longer hair at the throat;
  * body: deep chest down to the elbow, tucked belly, the withers the high
    point and the top line SLOPING down to the croup;
  * hind leg: strong ANGULATION, the paw set well behind the hip (the
    stance of the breed), broad thighs with "breeches" of longer hair;
  * tail: long, bushy, hung low in a SABRE curve, lifted in the run;
  * coat: medium length (the cloth grain of the rig stands in for it);
    BLACK AND TAN: the black blanket (saddle) over the back and down the
    flanks, the black mask, the rest tan/fire with a paler cream underside.

The Reich touch (D48 brief, BESTIARY §6): a dog wears no armband and the
hound carries no faction red; it gets a black leather COLLAR with a steel
TAG at the throat, in every cell. Cell D adds a minimal graft: a riveted
steel plate on the skull and a stapled scar on each thigh (both symmetric,
so Doom's mirrored rotation pairs stay valid). The only red anywhere is the
inside of the open mouth in the bite frames.

Cells (colour variations of the same dog and build):
    A  classic black and tan: fire tan, saddle to mid-flank, cream points
    B  "red and black": deeper red tan, a larger blanket back
    C  light tan (sable-pale, working line): khaki tan, small saddle
    D  as A, plus the Reich graft (skull plate, stapled thigh scars)

How it is drawn. rig_core's QuadBuild/pose_quadruped give the posed bones
(spine chain, three-bone hind leg, transverse gallop, D48 asks for it);
the shapes are new, hung on those bones. Rotations 1-5 are traced and 6-8
are their mirrors (rig_core's mirror mode). Colours: palette v1 only
(rust_brown, khaki_olive, black; flag_red inside the mouth; steel in
concrete_cold), so nothing waits on palette v2.

NO FONTS. Nothing here rasterises text; the sheet is HTML (sheetlib).

Outputs (work/ is gitignored):
    work/art/enemies/hound_gsd/SDHN_<cell>_<frame><rot>.png  RGBA, hard alpha, grAb
    work/art/enemies/hound_gsd/*.gif, lineup_*.png, metrics.json
    docs/art/previews/<stamp>_F5_hound-gsd-sweep.html        (the sheet)
  --full (D50, cell A's whole set, section "the full set" below):
    work/art/enemies/hound_gsd/full_A/SDHN<frame><rot>[<frame><rot>].png   46 lumps, grAb
    work/art/enemies/hound_gsd/full_A/*.gif, lineup_*.png, metrics.json
    docs/art/previews/<stamp>_F5_reich-hound-A-full-set.html

Light model: gen_enemy.py's stand-in (RGB x L/224, re-quantised). NOT
VERIFIED against GZDoom's light tables. Rotation order checked by hand
against r_things.c (rig_core's docstring), NOT in the engine.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from PIL import Image

ART_TOOLS = Path(__file__).resolve().parent
if str(ART_TOOLS) not in sys.path:
    sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402  (light stand-in, scenes, luma)
import rig_core as core  # noqa: E402  (primitives, quadruped skeleton, renderer, output)
import sheetlib  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "hound_gsd"
RIFLEMAN_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "rig"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
SDFLR1 = PROJECT_ROOT / "assets" / "flats" / "soviet_base" / "SDFLR1.png"

SPRITE = "SDHN"                 # BESTIARY §6
SEED = 48                       # D48; coat grain only
V = core.V
Canvas = core.Canvas
CV = Canvas(112, 64, 56, 56)    # gen_storm's gallop canvas: a long body across, axis centred for mirroring
MAX_H = 40                      # BESTIARY §6: a horizontal bar under 40 px tall
ROTS = (1, 3, 5)                # traced; 7 is the mirror of 3 (rig_core.MIRROR_PAIRS)
WALK = {"A": 0.0, "B": 0.25, "C": 0.5, "D": 0.75}   # See: SDHN AABBCCDD, one gallop stride
WALK_TICS = 2                   # BESTIARY §6
SLOW_TICS = 8                   # a quarter of game speed, for the eye
BITE_TICS = 8                   # BESTIARY §6: Melee E F 8, G 8

# ================================================================ skeleton
# Proportions of a German shepherd at Doom scale (1 unit = 1 px at 1x):
# withers about 24 above the paws, body (forechest to buttock) about 1.15x
# that, head about 0.42x. The withers are the high point; the top line
# slopes down to the sacrum and on down the croup to the tail set.
GSD_BUILD = core.QuadBuild(
    pelvis=(0.0, 20.5, -13.5),  # sacrum: lower than the withers (the sloping back)
    spine=(8.2, 8.2, 8.2),      # loin, back, chest
    spine_bends=(9.0, 1.0, -1.5),
    neck=(5.0, 4.6),
    neck_bends=(26.0, 6.0),     # a strong neck carried forward and up
    hip_x=3.3,
    shoulder_x=3.4,
    hip_drop=4.6,
    shoulder_drop=8.6,
    femur=8.8,
    tibia=9.6,
    meta=5.6,                   # a short, upright metatarsus: the hock low
    upper=7.2,
    lower=7.8,
    pastern=1.6,
    paw_y=1.25,
    fore_reach=2.2,
    hind_reach=-5.5,            # the breed's angulation: the hind paw well behind the hip
)
HEAD_ANGLE = -16.0              # the skull's axis, degrees, nose below level (running carriage)
HEAD_FOLLOW = 0.5               # share of the body's pitch the head follows
TAIL_ANGLE = -38.0              # first tail bone, degrees below level in the gallop (sabre, lifted)
TAIL_WAG = 8.0                  # degrees it swings with the stride
EAR_HALF = 2.0                  # half the ear's height: large and erect, the tips under MAX_H
SADDLE_VALUE = 0.22             # the blanket's base value: near black, not dark brown
COLLAR_PROUD = 0.8              # the collar stands this far off the neck, so it reads at 1x


@dataclass(frozen=True)
class Bite:
    """A melee frame: where in the stride the body is, the jaw, the head."""
    phase: float                # gallop phase of the legs and spine
    jaw: float                  # degrees open
    head: float                 # degrees added to HEAD_ANGLE (positive: nose up)


BITE = {                        # BESTIARY §6: Melee E F (A_FaceTarget), G (attack)
    "E": Bite(0.0, 14.0, 10.0),     # gathered, head up, the mouth opening
    "F": Bite(0.5, 38.0, -4.0),     # the lunge: stretched, jaws wide
    "G": Bite(0.5, 6.0, -10.0),     # the snap: jaws nearly shut, head driven down
}


# ================================================================ cells
@dataclass(frozen=True)
class Cell:
    key: str
    title: str
    tan: tuple                  # (ramp, lo, hi): the fire/tan coat
    cream: tuple                # (ramp, lo, hi): the paler underside and points
    saddle_low: float           # how far down the flank the black blanket reaches (ribcage radii below its centre)
    saddle_front: float         # how far forward it reaches (ribcage radii ahead of its centre)
    graft: bool = False


CELLS = (
    Cell("A", "Classic black and tan: fire tan, saddle to mid-flank, cream points",
         ("rust_brown", 7, 15), ("khaki_olive", 9, 15), -0.05, 0.25),
    Cell("B", "Brown and black: a darker, browner tan, a large blanket back",
         ("rust_brown", 4, 12), ("rust_brown", 8, 14), -0.45, 0.45),
    Cell("C", "Light tan (pale working line): khaki tan, a small saddle",
         ("khaki_olive", 7, 15), ("khaki_olive", 11, 15), 0.22, 0.05),
    Cell("D", "As A, with the Reich graft: riveted skull plate, stapled thigh scars",
         ("rust_brown", 7, 15), ("khaki_olive", 9, 15), -0.05, 0.25, graft=True),
)
CELL = {c.key: c for c in CELLS}
RECOMMENDED = "A"

# ================================================================ materials
M = core.Mat.on_ramp
FIXED_MATERIALS: dict[str, core.Mat] = {    # the same in every cell; keep their own value (shift=False)
    "saddle": M("rust_brown", 0, 2, black_floor=True, cloth=True, shift=False),   # black hair, brown-black highlights
    "gsd_mask": M("rust_brown", 0, 3, black_floor=True, shift=False),             # muzzle and mask
    "nose": core.Mat((("black",), ("concrete_cold", 0, 6)), shift=False),
    "teeth": M("plaster_warm", 10, 15, shift=False),
    "mouth": M("flag_red", 2, 8, shift=False),                                     # the one red: inside the mouth
    "collar": M("rust_brown", 1, 5, black_floor=True, shift=False),               # black leather
    "steel": M("concrete_cold", 8, 24, shift=False),                               # the tag, the graft's plate
    "scar": M("rust_brown", 1, 4, black_floor=True, shift=False),                  # the stitched seam
}
CELL_MATERIALS = ("tan", "cream")           # per cell (Cell.tan, Cell.cream), cloth: the medium coat
RED_MATERIALS = {"mouth"}


def materials_for(cell: Cell) -> dict[str, core.Mat]:
    """The cell's material table: rig_core's base table COPIED (no id of it
    moves; rig_core.MATERIALS itself is never touched), then this module's."""
    table = dict(core.MATERIALS)
    for name, mat in FIXED_MATERIALS.items():
        core.register_material(name, mat, table)
    core.register_material("tan", M(*cell.tan, cloth=True, shift=False), table)
    core.register_material("cream", M(*cell.cream, cloth=True, shift=False), table)
    return table


# ================================================================ model
def _yz_clip_below(a, b, drop: float):
    """A clip (normal, offset) keeping what lies ABOVE the line a->b in the
    figure's mid-plane, lowered by `drop`: the lower edge of the saddle on a
    body piece that spans two bones."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    d = d / np.linalg.norm(d)
    n = V(0.0, -d[2], d[1])                     # perpendicular in y-z, pointing down
    if n[1] > 0:
        n = -n
    p = a - V(0.0, drop, 0.0)
    return (n, float(n @ p))


def body_pitch_of(q: core.QuadRig) -> float:
    """How far the posed spine is pitched from the build's rest curve, degrees."""
    return float(np.mean(q.spine_angles)) - float(np.mean(core.spine_chain(
        V(*GSD_BUILD.pelvis), GSD_BUILD.spine, GSD_BUILD.spine_bends)[1]))


def gsd_model(cell: Cell, frame: str) -> list[core.Prim]:
    """The German shepherd for one frame of the sweep (A-D gallop, E-G bite),
    model space: paws on y = 0, facing +z, +x its LEFT."""
    bite = BITE.get(frame)
    phase = bite.phase if bite else WALK[frame]
    jaw_open = bite.jaw if bite else 0.0
    q = core.pose_quadruped(GSD_BUILD, core.QuadPose(frame, frame, phase))
    body_pitch = body_pitch_of(q)
    wag = TAIL_WAG * np.sin(2 * np.pi * phase)
    return dog(cell, q, jaw_open=jaw_open,
               head_a=HEAD_ANGLE + (bite.head if bite else 0.0) + HEAD_FOLLOW * body_pitch,
               tail_a=TAIL_ANGLE + 0.5 * body_pitch + wag)


def dog(cell: Cell, q: core.QuadRig, *, jaw_open: float, head_a: float, tail_a: float,
        tail_bends: tuple = (22.0, 34.0)) -> list[core.Prim]:
    """The shepherd's shapes hung on a posed skeleton `q` (from pose_quadruped
    or a death rig), in the skeleton's frame: the skull at `head_a` degrees,
    the jaw `jaw_open` degrees below it, the first tail bone at `tail_a` and
    the next two bent by `tail_bends` (down, then the sabre's upturn)."""
    P: list[core.Prim] = []

    def add(grp, prim, limb="", side=core.CENTRE, tag=""):
        prim.grp, prim.limb, prim.side = grp, limb, side
        if tag:
            prim.tag = tag
        P.append(prim)
        return prim

    sacrum, withers = q.spine[0], q.spine[-1]
    pel_a, chest_a = q.spine_angles[0], q.spine_angles[-1]
    pel_R, chest_R = core.bone_frame(pel_a), core.bone_frame(chest_a)
    at_chest = lambda x, y, z: withers + chest_R @ V(x, y, z)  # noqa: E731
    at_pelvis = lambda x, y, z: sacrum + pel_R @ V(x, y, z)  # noqa: E731

    # ------------------------------------------------------------ chest (chest bone frame)
    cy, cz = -7.2, -3.6
    cage = (5.4, 7.0, 9.4)                       # deep, not barrel: the brisket reaches the elbow
    add("body", core.on_bone(core.ellipsoid("tan", 0.50, (0, cy, cz), cage), withers, chest_a))
    add("body", core.on_bone(core.ellipsoid(
        "saddle", SADDLE_VALUE, (0, cy, cz), (cage[0] + 0.35, cage[1] + 0.35, cage[2] + 0.35),
        clip=[(V(0, -1, 0), -(cy + cage[1] * cell.saddle_low)),
              (V(0, 0, 1), cz + cage[2] * cell.saddle_front)]), withers, chest_a))
    add("body", core.on_bone(core.ellipsoid("cream", 0.45, (0, cy - cage[1] * 0.55, cz + 0.5),
                                            (cage[0] * 0.78, cage[1] * 0.5, cage[2] * 0.78)), withers, chest_a))
    # the forechest and the ruff (gorguera): longer, paler hair from throat to brisket
    add("body", core.on_bone(core.ellipsoid("tan", 0.55, (0, -6.2, 4.6), (4.2, 5.2, 3.6)), withers, chest_a))
    for i, (y, z, r) in enumerate(((-3.6, 6.6, 3.0), (-6.0, 7.4, 3.2), (-8.6, 6.6, 3.0))):
        add("body", core.on_bone(core.ellipsoid("cream", 0.62 - 0.03 * i, (0, y, z), (r + 0.4, r, r * 0.8)),
                                 withers, chest_a))
    # shoulder blades: laid back, from the withers down to the point of shoulder
    for side in (core.LEFT, core.RIGHT):
        sh = q.legs["fl" if side == core.LEFT else "fr"][0]
        top = at_chest(side * 2.6, -1.6, -2.2)
        add("body", core.rcone("tan", 0.52, top, sh + V(0, 0.6, 0), 2.5, 2.6), "foreleg", side)
    # ------------------------------------------------------------ loin, belly, croup
    loin_a, loin_b = at_chest(0, -4.6, cz - cage[2] * 0.55), at_pelvis(0, -3.0, 1.5)
    add("body", core.rcone("tan", 0.50, loin_a, loin_b, 4.6, 4.1))
    top_a, top_b = at_chest(0, 0.0, cz - cage[2] * 0.55), at_pelvis(0, 1.0, 1.5)
    add("body", core.rcone("saddle", SADDLE_VALUE, loin_a, loin_b, 4.95, 4.45,
                           clip=[_yz_clip_below(top_a, top_b, 4.6 * (1.0 - cell.saddle_low))]))
    add("body", core.rcone("cream", 0.45, at_chest(0, cy - cage[1] * 0.55, cz - cage[2] * 0.3),
                           at_pelvis(0, -7.0, 2.0), 3.0, 2.0))          # the tucked underline
    add("body", core.on_bone(core.ellipsoid("tan", 0.50, (0, -2.4, -2.2), (3.9, 3.6, 5.2)), sacrum, pel_a))
    add("body", core.on_bone(core.ellipsoid(
        "saddle", SADDLE_VALUE, (0, -2.4, -2.2), (4.25, 3.95, 5.55),
        clip=[(V(0, -1, 0), -(-2.4 + 3.95 * cell.saddle_low))]), sacrum, pel_a))
    # ------------------------------------------------------------ the neck, its crest and the collar
    neck_axis = [at_chest(0, -3.4, 2.4), q.neck[1] + V(0, -2.6, 0.4), q.neck[2] + V(0, -2.3, 0.6)]
    radii = (4.4, 3.7, 3.1)
    for (a, b), (r1, r2) in zip(zip(neck_axis[:-1], neck_axis[1:]), zip(radii[:-1], radii[1:])):
        add("neck", core.rcone("tan", 0.52, a, b, r1, r2))
    crest = [at_chest(0, -0.2, 0.0), q.neck[1] + V(0, -0.4, 0), q.neck[2] + V(0, -0.5, 0.2)]
    add("neck", core.rcone("saddle", SADDLE_VALUE, crest[0], crest[1], 2.2, 1.9))
    add("neck", core.rcone("saddle", SADDLE_VALUE, crest[1], crest[2], 1.9, 1.6))
    for z, r in ((0.6, 3.4), (2.0, 3.0)):                            # throat ruff
        add("neck", core.ellipsoid("cream", 0.6, tuple(neck_axis[1] + V(0, -1.6, z - 0.6)), (r, r * 0.9, r * 0.8)))
    c0 = neck_axis[1] + (neck_axis[2] - neck_axis[1]) * 0.35
    c1 = neck_axis[1] + (neck_axis[2] - neck_axis[1]) * 0.62
    rc = radii[1] - (radii[1] - radii[2]) * 0.5 + COLLAR_PROUD
    add("neck", core.rcone("collar", 0.45, c0, c1, rc, rc - 0.1), tag="collar")
    d = (c1 - c0) / np.linalg.norm(c1 - c0)
    down = V(0, -1, 0) - (V(0, -1, 0) @ d) * d
    down = down / np.linalg.norm(down)
    tag_c = (c0 + c1) / 2 + down * (rc + 0.9) + V(0, 0, 0.4)
    add("neck", core.box("steel", 0.72, tuple(tag_c), (0.85, 1.0, 0.3), rnd=0.25), tag="tag")
    # ------------------------------------------------------------ the tail: long, bushy, sabre
    root = at_pelvis(0, -0.8, -6.6)
    t1 = np.deg2rad(tail_a)
    k1 = root + 6.0 * V(0, np.sin(t1), -np.cos(t1))
    t2 = t1 - np.deg2rad(tail_bends[0])
    k2 = k1 + 6.0 * V(0, np.sin(t2), -np.cos(t2))
    t3 = t2 + np.deg2rad(tail_bends[1])           # the sabre's upturned tip
    k3 = k2 + 3.6 * V(0, np.sin(t3), -np.cos(t3))
    for (a, b), (r1, r2) in zip(((root, k1), (k1, k2), (k2, k3)), ((1.3, 1.7), (1.7, 1.5), (1.5, 0.7))):
        add("tail", core.rcone("saddle", SADDLE_VALUE, a, b, r1, r2))
        add("tail", core.rcone("tan", 0.48, a + V(0, -0.7, 0), b + V(0, -0.7, 0), r1 * 0.85, r2 * 0.85))
    # ------------------------------------------------------------ legs
    for leg in core.LEGS:
        side = core.LEFT if leg.endswith("l") else core.RIGHT
        grp = "leg_l" if side == core.LEFT else "leg_r"
        root_j, mid, low, paw = q.legs[leg]
        if leg.startswith("h"):
            limb = "hindleg"
            # the broad thigh, its black top under the saddle, the "breeches" of longer hair behind
            add(grp, core.rcone("tan", 0.50, root_j + V(0, 1.2, 0), mid, 3.5, 2.0), limb, side)
            add(grp, core.rcone("cream", 0.55, root_j + V(0, -0.8, -2.4), mid + V(0, 0.3, -1.6), 2.3, 1.3),
                limb, side)
            add(grp, core.rcone("tan", 0.48, mid, low, 1.9, 1.15), limb, side)
            add(grp, core.rcone("tan", 0.46, low, paw + V(0, 0.7, 0), 1.15, 0.95), limb, side)
            add(grp, core.ellipsoid("cream", 0.5, tuple(paw + V(0, 0.0, 0.9)), (1.25, 1.05, 1.8)), limb, side)
            if cell.graft:
                c = root_j + (mid - root_j) * 0.45 + V(side * 2.9, 0.4, 0)
                add(grp, core.rcone("scar", 0.30, c + V(0, 1.6, -1.2), c + V(0, -1.4, 1.2), 0.32), limb, side)
                for t in (-0.6, 0.6):
                    add(grp, core.ellipsoid("steel", 0.75, tuple(c + V(side * 0.15, -0.9 * t, 0.7 * t)),
                                            (0.35, 0.35, 0.6)), limb, side)
        else:
            limb = "foreleg"
            add(grp, core.rcone("tan", 0.50, root_j, mid, 2.3, 1.5), limb, side)
            add(grp, core.rcone("tan", 0.48, mid, low, 1.35, 1.0), limb, side)
            add(grp, core.rcone("cream", 0.52, mid + V(0, 0, -0.6), low + V(0, 0, -0.4), 0.9, 0.7), limb, side)
            add(grp, core.ellipsoid("cream", 0.5, tuple(paw + V(0, 0.0, 0.8)), (1.3, 1.05, 1.8)), limb, side)
    # ------------------------------------------------------------ the head (head frame: origin the occiput)
    occ = q.neck[-1] + V(0, -0.6, 0.6)
    head: list[core.Prim] = [
        core.ellipsoid("tan", 0.55, (0, -0.8, 2.6), (2.8, 2.5, 3.2)),                # cranium
        core.ellipsoid("tan", 0.50, (0, -1.7, 3.6), (2.5, 1.9, 2.4)),                # cheeks: the wedge's back
        core.rcone("saddle", SADDLE_VALUE, V(0, 1.4, 0.8), V(0, 0.5, 4.6), 0.9, 0.7),        # dark line on the skull
        core.rcone("gsd_mask", 0.45, V(0, -1.5, 5.0), V(0, -2.0, 10.0), 1.75, 0.95),  # the muzzle, below the stop
        core.ellipsoid("nose", 0.35, (0, -1.75, 10.3), (0.95, 0.8, 0.75)),
    ]
    for side in (1, -1):
        head += [
            core.ellipsoid("gsd_mask", 0.40, (side * 1.55, -0.7, 4.6), (1.0, 0.95, 1.1)),   # mask round the eye
            core.ellipsoid("cream", 0.70, (side * 1.25, 0.55, 4.3), (0.55, 0.45, 0.55)),   # the tan pip
        ]
        R = core.rot_z(side * 14.0) @ core.rot_x(14.0)   # tips out and back
        h = EAR_HALF
        base = V(side * 1.45, 1.0, 1.4)
        head.append(core.Prim("cappedcone", "saddle", 0.42, base + R @ V(0, h, 0), h=h, r1=1.75, r2=0.12,
                              scale=V(1.0, 1.0, 0.7), rot=R))                     # erect triangular ear
    if cell.graft:
        head.append(core.ellipsoid("steel", 0.62, (0, 1.05, 2.4), (1.5, 0.75, 1.9)))  # riveted skull plate
        for side in (1, -1):
            head.append(core.ellipsoid("scar", 0.3, (side * 1.5, 0.75, 2.4), (0.3, 0.3, 0.3)))
    jaw: list[core.Prim] = [core.rcone("gsd_mask", 0.40, V(0, -0.5, 0.6), V(0, -0.7, 5.6), 1.15, 0.7)]
    if jaw_open > 4.0:
        head.append(core.ellipsoid("mouth", 0.40, (0, -2.9, 6.8), (1.2, 0.8, 3.0)))
        for side in (1, -1):                        # canines and the upper row
            head.append(core.rcone("teeth", 0.7, V(side * 0.95, -2.7, 9.0), V(side * 0.9, -3.7, 9.1), 0.32, 0.12))
            head.append(core.ellipsoid("teeth", 0.7, (side * 1.3, -2.8, 7.2), (0.3, 0.45, 0.9)))
            jaw.append(core.rcone("teeth", 0.7, V(side * 0.75, -0.1, 5.2), V(side * 0.7, 0.8, 5.3), 0.3, 0.1))
    for prim in head:
        add("head", core.on_bone(prim, occ, head_a), tag=prim.tag)
    hinge = occ + core.bone_frame(head_a) @ V(0, -2.4, 3.6)
    for prim in jaw:
        add("jaw", core.on_bone(prim, hinge, head_a - jaw_open))
    return P


# ================================================================ render
def render(cell: Cell, frame: str, rotation: int, seed: int = SEED) -> np.ndarray:
    """One sprite, RGBA; rotations 6-8 are the mirrors of 4-2, as the engine draws them."""
    mats = materials_for(cell)
    src = core.MIRRORED.get(rotation)
    r = src if src is not None else rotation
    rgba = core.render(gsd_model(cell, frame), r, CV, mats, seed=seed, what=f"SDHN {cell.key} {frame}{r}")
    return core.mirror_sprite(rgba, CV) if src is not None else rgba


def lump(cell_key: str, frame: str, rotation: int) -> str:
    return f"{SPRITE}_{cell_key}_{frame}{rotation}"


def grab() -> tuple[int, int]:
    return core.grab_offsets(CV)


WALK_FRAMES = tuple(WALK)       # A B C D
BITE_FRAMES = tuple(BITE)       # E F G
SIDE_FRAME = "C"                # the stretched stride: the profile the sweep compares
LEGIBLE_DELTA = 16              # luma units under the scene's light: a body pixel this far from the wall's mean reads


def frame_plan() -> list[tuple[str, int]]:
    """Every (frame, rotation) traced per cell: the gallop and the bite at 1, 3, 5."""
    return [(f, r) for f in (*WALK_FRAMES, *BITE_FRAMES) for r in ROTS]


# ================================================================ metrics
def load_rgb(name: str) -> np.ndarray:
    """A MAP01 wall or flat by lump name (SDFLR1 too, for the lane-line scene)."""
    if name == "SDFLR1":
        with Image.open(SDFLR1) as im:
            return np.asarray(im.convert("RGB"), dtype=np.uint8)
    return flat.host_rgb(name)


SCENES = (*flat.SCENES, ("S6", "SDCONC1", 128, "corridor over the SDFLR1 lane line"))


def share(mat: np.ndarray, table: dict[str, core.Mat], names) -> float:
    ids = [core.material_ids(table)[n] for n in names]
    op = mat >= 0
    return float(np.isin(mat, ids).sum() / max(op.sum(), 1))


def legible_share(rgba: np.ndarray, wall: str, light: int) -> float:
    """Share of the body's pixels whose luma, under the scene's light, sits at
    least LEGIBLE_DELTA from the wall's mean: the black blanket and the tan
    read even where the MEAN body luma is close to the wall's."""
    f = min(1.0, light / flat.LIGHT_FULL)
    a = rgba[..., 3] > 0
    body = flat.luma(rgba[..., :3])[a] * f
    wall_l = float(flat.luma(load_rgb(wall)).mean()) * f
    return float((np.abs(body - wall_l) >= LEGIBLE_DELTA).mean())


def metrics_for(cell: Cell, spr: dict) -> dict:
    side = spr[(SIDE_FRAME, 3)]
    m = core.measure(side, SCENES, load_rgb)
    mats = materials_for(cell)
    lay = core.render_layers(gsd_model(cell, SIDE_FRAME), 3, CV, mats, seed=SEED)
    m["tan_share"] = round(share(lay.mat, mats, ("tan", "cream")), 3)
    m["saddle_share"] = round(share(lay.mat, mats, ("saddle",)), 3)
    for key, wall, light, _ in SCENES:
        m[f"legible_{key}"] = round(legible_share(side, wall, light), 3)
    m["max_height_px"] = max(int(np.ptp(np.nonzero(v[..., 3] > 0)[0]) + 1) for v in spr.values())
    m["front_height_px"] = core.measure(spr[("A", 1)], SCENES, load_rgb)["height_px"]
    return m


# ================================================================ build
def build_all(out_dir: Path = OUT_DIR, seed: int = SEED, cells=CELLS) -> dict:
    """Trace every cell's frame plan, save the PNGs (grAb), the GIFs and metrics.json."""
    out_dir.mkdir(parents=True, exist_ok=True)
    data = {"sprites": {}, "metrics": {}, "gifs": {}}
    t = lambda n: int(round(n * core.TIC_MS))  # noqa: E731
    for cell in cells:
        spr = {}
        for f, r in frame_plan():
            spr[(f, r)] = render(cell, f, r, seed)
            core.save_sprite(spr[(f, r)], out_dir / f"{lump(cell.key, f, r)}.png", CV)
            print(lump(cell.key, f, r), flush=True)
        for f in WALK_FRAMES + BITE_FRAMES:          # rotation 7: the engine's flip of 3 (SDHNx3x7)
            spr[(f, 7)] = core.mirror_sprite(spr[(f, 3)], CV)
        data["sprites"][cell.key] = spr
        data["metrics"][cell.key] = metrics_for(cell, spr)
        for r in (*ROTS, 7):
            frames = [core.on_bg(spr[(f, r)], core.NEUTRAL) for f in WALK_FRAMES]
            data["gifs"][(cell.key, r)] = core.save_gif(frames, [t(WALK_TICS)] * 4,
                                                        out_dir / f"{SPRITE}_{cell.key}_gallop_rot{r}.gif")
            data["gifs"][(cell.key, r, "slow")] = core.save_gif(
                frames, [t(SLOW_TICS)] * 4, out_dir / f"{SPRITE}_{cell.key}_gallop_rot{r}_slow.gif")
        frames = [core.on_bg(spr[(f, 3)], core.NEUTRAL) for f in ("A", *BITE_FRAMES)]
        data["gifs"][(cell.key, "bite")] = core.save_gif(frames, [t(BITE_TICS)] * 4,
                                                         out_dir / f"{SPRITE}_{cell.key}_bite_rot3.gif")
    (out_dir / "metrics.json").write_text(json.dumps(data["metrics"], indent=2) + "\n", encoding="utf-8")
    return data


def load_all(out_dir: Path = OUT_DIR) -> dict:
    """What build_all wrote, read back (for --sheet-only)."""
    data = {"sprites": {}, "gifs": {},
            "metrics": json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))}
    for cell in CELLS:
        spr = {}
        for f, r in frame_plan():
            with Image.open(out_dir / f"{lump(cell.key, f, r)}.png") as im:
                spr[(f, r)] = np.asarray(im.convert("RGBA")).copy()
        for f in WALK_FRAMES + BITE_FRAMES:
            spr[(f, 7)] = core.mirror_sprite(spr[(f, 3)], CV)
        data["sprites"][cell.key] = spr
        for r in (*ROTS, 7):
            data["gifs"][(cell.key, r)] = out_dir / f"{SPRITE}_{cell.key}_gallop_rot{r}.gif"
            data["gifs"][(cell.key, r, "slow")] = out_dir / f"{SPRITE}_{cell.key}_gallop_rot{r}_slow.gif"
        data["gifs"][(cell.key, "bite")] = out_dir / f"{SPRITE}_{cell.key}_bite_rot3.gif"
    return data


# ================================================================ scenes
def rifleman() -> tuple[np.ndarray, int, int] | None:
    """The rifleman drafted from the rig (D38, OK'd in D48), for scale."""
    path = RIFLEMAN_DIR / "SDRRA1.png"
    if not path.is_file():
        return None
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGBA")).copy()
    return arr, *core.grab_offsets(core.STAND)


def companions() -> tuple[list, list[str]]:
    """The figures the hound stands beside: Freedoom's placeholders (scale
    only, BSD-3, iwads/ is not in git so each is optional) and the rifleman."""
    figs, labels = [], []
    for name, label in (("POSSA1", "POSS placeholder"), ("SARGA1", "SARG placeholder, front"),
                        ("SARGA3A7", "SARG placeholder, side")):
        got = core.freedoom_sprite(name)
        if got is not None:
            figs.append(got)
            labels.append(label)
    rr = rifleman()
    if rr is not None:
        figs.insert(1 if figs else 0, rr)
        labels.insert(1 if labels else 0, "SDRR rifleman (D38)")
    return figs, labels


SLOT_W = 72                     # lineup slot: a 61-px profile with air on both sides
TURN = (("A", 1), ("C", 3), ("A", 5), ("F", 3), ("C", 7))


def lineups(data: dict, out_dir: Path = OUT_DIR) -> dict:
    """Per scene: the companions, then every cell in profile; and, on the
    worst case S3, the recommended cell turning and biting."""
    figs, labels = companions()
    out = {}
    g = grab()
    for key, wall, light, what in SCENES:
        row = figs + [(data["sprites"][c.key][(SIDE_FRAME, 3)], *g) for c in CELLS]
        floor = "SDFLR1" if key == "S6" else "SDFLR2"
        sc = core.lineup(row, wall, light, SLOT_W * len(row), floor, load=load_rgb)
        Image.fromarray(sc).save(out_dir / f"lineup_{key}.png")
        out[key] = (sc, labels + [f"SDHN {c.key} side" for c in CELLS], wall, light, what)
    rec = data["sprites"][RECOMMENDED]
    row = figs[:2] + [(rec[fr], *g) for fr in TURN]
    sc = core.lineup(row, "SDSTEL1", 112, SLOT_W * len(row), "SDFLR2", load=load_rgb)
    Image.fromarray(sc).save(out_dir / "lineup_S3_turn.png")
    out["turn"] = (sc, labels[:2] + [f"SDHN {RECOMMENDED} {f}{r}" for f, r in TURN],
                   "SDSTEL1", 112, "fuel bay, worst case: the recommended cell turning")
    return out


# ================================================================ sheet
VERDICT = [
    "WHAT CHANGED. The first sweep drew an alien: a hairless olive hide over ribs, a flat head that was mostly "
    "jaw, spines down the back. D48 asked for a German shepherd, and everything is new except the bones: the "
    "skeleton is rig_core's (spine chain, three-bone hind leg, transverse gallop), re-proportioned to the "
    "breed: the withers the high point and the top line sloping to the croup, a deep chest to the elbow and a "
    "tucked belly, the hind paw set well behind the hip. On it: a wedge head with a marked stop, skull and "
    "muzzle about equal, black nose and mask, tan pips over the eyes; large erect triangular ears; a strong "
    "neck with a pale ruff; broad thighs with breeches; a long bushy tail in a sabre, lifted in the run; the "
    "black blanket over the back and flanks, the rest fire tan with a paler underside.",
    "HOW IT READS, HONESTLY. In profile at 1x it reads as a German shepherd at first glance, on every wall: the "
    "ears, the black saddle on tan and the sabre tail carry it. From the front (rotation 1) it is a narrow tan "
    "column, 14 px wide, with two ear points and a dark muzzle: a dog, a shepherd if you know to look. From "
    "behind (rotation 5) the black back and the tail dominate. That is the limit of a figure this small; "
    "Doom's own pinky has it too. The coat is suggested by the rig's grain and the ruff, not drawn hair by "
    "hair: at 3x the dog looks smooth-coated, at 1x nobody can tell. The gallop is rig_core's gait numbers, "
    "chosen by eye, not taken from footage.",
    "THE GREEN STEEL (S3, SDSTEL1 at light 112), MEASURED. Cell A's MEAN body luma (88) sits close to the "
    "wall's, so the first sweep's measure gives a gap of only 6.7 at S3, smaller than the rejected cell D's "
    "12.6. But the dog is not one value: 57 % of its pixels clear the wall by 16 luma or more (the black "
    "blanket below it, the cream above it), and the tan is orange on green, the complementary hue. On the "
    "1x strip it is the most visible figure on S3, more than the rifleman. Cell B (browner, more black) has "
    "the best mean gap (17.3). The mean-luma measure underrates a two-tone animal; the hue split is NOT "
    "VERIFIED under GZDoom's light, which darkens with distance. BESTIARY §10 rule 1 (no Reich ambush in "
    "SDSTEL1 at light 112 or less) should stand until the engine pass. Rule 4's fallback, a true-black "
    "underbelly, is gone: a shepherd's underside is pale, so the map-side half of rule 4 (no lane line "
    "through a hound ambush) must hold on its own.",
    "THE REICH TOUCH. A black leather collar with a steel tag at the throat, on every cell; at 1x the tag "
    "is one light pixel under the chin, seen from the front. Cell D adds the graft: a riveted steel plate on "
    "the skull and a stapled scar on each thigh, symmetric so the mirrored rotations stay legal. At 1x the "
    "plate is a light dot between the ears and the scars barely register: the most the dog can wear and "
    "still read as a shepherd first. No faction red: the only red is inside the open mouth (bite E and F).",
    "HEIGHT. Side and front stay under BESTIARY §6's 40 px (34 and 31). Seen from behind, the camera's "
    "9-degree pitch lifts the far head and drops the near hind paws, so the back view measures 40-42 px, as "
    "the first gallop proof's did (40). It still reads as a horizontal animal.",
    "RECOMMENDATION: cell A, the classic black and tan, with the collar. It is the shepherd everyone "
    "pictures, its tan is the brown the CEO asked for, and its saddle gives the silhouette a dark top edge. "
    "If the CEO wants it browner, B is the same dog darker, and it measures better on green steel; C is the "
    "pale working line, the weakest on concrete (37 % legible) and on green steel by the mean (gap 4.8); D is A "
    "with the graft, for a Reich mark on "
    "the dog itself.",
]


def _strip(items) -> str:
    return '<div class="strip">' + "".join(items) + "</div>"


ROT_NAMES = {1: "front", 3: "its left side", 5: "back", 7: "its right side (mirror of 3)"}


def build_sheet(data: dict, scenes: dict, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    S = []
    met = data["metrics"]
    rows = [[c.key + (" (recommended)" if c.key == RECOMMENDED else ""), c.title,
             f"{c.tan[0]} {c.tan[1]}-{c.tan[2]}", f"{c.cream[0]} {c.cream[1]}-{c.cream[2]}",
             "collar, tag" + (", skull plate, thigh scars" if c.graft else "")] for c in CELLS]
    body = sheetlib.table(["cell", "what", "tan", "cream", "Reich touch"], rows, 9)
    body += ("<p class=\"lead\">Every cell: the same dog and skeleton; the blanket in black and "
             "<code>rust_brown</code> 0-2, the mask and nose black, the collar black leather, the tag in "
             "<code>concrete_cold</code> steel, the teeth <code>plaster_warm</code>, the inside of the mouth "
             "<code>flag_red</code> (bite frames only). Palette v1.</p>")
    S.append(("1 · The four cells", f"Colour variations of one German shepherd (D48). {RECOMMENDED} is "
              "recommended.", body))
    body = ""
    for c in CELLS:
        spr = data["sprites"][c.key]
        body += f"<h3>{html.escape(c.key)} · {html.escape(c.title)}</h3>"
        body += _strip([core.sprite_tile(spr[(f, r)], 3, f"{SPRITE}{f}{r}",
                                         ROT_NAMES[r] + (", bite" if f == "F" else ""))
                        for f, r in (("A", 1), ("C", 3), ("A", 5), ("F", 3))]
                       + [core.gif_tile(data["gifs"][(c.key, 3)], 3, "gallop, game speed", "rotation 3")])
    S.append(("2 · Each cell at 3x: front, side, back, the bite",
              "Rotations 1, 3 and 5 of the gallop (rotation 3 in its stretched frame C), the bite F at "
              "rotation 3, and the gallop animated at game speed (See: SDHN AABBCCDD, 2 tics). Neutral grey.",
              body))
    rec = data["sprites"][RECOMMENDED]
    body = ""
    for r in ROTS:
        body += _strip([core.gif_tile(data["gifs"][(RECOMMENDED, r)], 3, f"rotation {r}, game speed",
                                      ROT_NAMES[r]),
                        core.gif_tile(data["gifs"][(RECOMMENDED, r, "slow")], 3, f"rotation {r}, quarter speed")]
                       + [core.sprite_tile(rec[(f, r)], 3, core.rotation_lump(SPRITE, f, r, mirror=True),
                                           f"phase {WALK[f]:.2f}") for f in WALK_FRAMES])
    body += _strip([core.sprite_tile(rec[(f, 7)], 3, f"{SPRITE}{f}7 = {f}3 flipped") for f in WALK_FRAMES]
                   + [core.gif_tile(data["gifs"][(RECOMMENDED, 7)], 3, "rotation 7, game speed",
                                    "the engine's flip of 3")])
    S.append((f"3 · The gallop, cell {RECOMMENDED}",
              "rig_core's transverse gallop on the shepherd's proportions: A gathered, B the hind push, C "
              "stretched, D the forepaws landing. Rotation 7 is not traced: it is rotation 3 flipped, as the "
              "engine draws the paired lump.", body))
    body = ""
    for r in ROTS:
        body += _strip([core.sprite_tile(rec[(f, r)], 3, f"{SPRITE}{f}{r}", n) for f, n in
                        (("E", "wind-up, head up"), ("F", "the lunge, jaws wide"), ("G", "the snap"))])
    body += _strip([core.gif_tile(data["gifs"][(RECOMMENDED, "bite")], 3, "A then E F G, rotation 3",
                                  f"{BITE_TICS} tics a frame")])
    S.append((f"4 · The attack, cell {RECOMMENDED}",
              "BESTIARY §6 Melee: E F (A_FaceTarget), G (the bite), at rotations 1, 3 and 5. The open mouth is "
              "the only red on the dog.", body))
    body = ""
    for key in [k for k, *_ in SCENES] + ["turn"]:
        sc, labels, wall, light, what = scenes[key]
        body += _strip([core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 1,
                                  f"{key} 1x: {wall} at light {light}", what),
                        core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 2, f"{key} 2x",
                                  " · ".join(labels))])
    S.append(("5 · At 1x on MAP01's walls, beside the rifleman and the placeholders",
              "Left to right: Freedoom's zombieman (POSS, the rifleman's placeholder), our rifleman (D38), "
              "Freedoom's demon (SARG, the hound's placeholder) front and side, then the four cells in profile, "
              "each standing by its own offsets. S3 is the old problem: SDSTEL1 green steel at light 112. S6 "
              "runs over SDFLR1's lane line. The last strip turns the recommended cell on S3 (front, side, back, "
              "bite, the mirrored side). Light is gen_enemy.py's stand-in, NOT VERIFIED against GZDoom.", body))
    rows = []
    for c in CELLS:
        m = met[c.key]
        rows.append([c.key, f"{m['height_px']} x {m['width_px']}", m["max_height_px"], m["front_height_px"],
                     m["body_luma"], m["gap_S3"], m["worst_gap"],
                     " / ".join(f"{m[f'legible_{k}']:.2f}" for k, *_ in SCENES),
                     m["tan_share"], m["saddle_share"]])
    body = sheetlib.table(["cell", "side h x w", "tallest frame", "front h", "body luma", "gap S3",
                           "worst gap", "legible S1/S2/S3/S4/S6", "tan+cream", "saddle"], rows, 1)
    body += ("<p class=\"lead\">Side = frame C at rotation 3. Tallest frame: over every frame traced "
             f"(BESTIARY §6: under {MAX_H}). Body luma: mean over opaque pixels. Gap: |body - wall| luma under "
             "the scene's light (the first sweep's measure). Legible: share of body pixels at least "
             f"{LEGIBLE_DELTA} luma from the wall's mean under the light (new here, a heuristic). Tan+cream "
             "and saddle: shares of the side view's pixels.</p>")
    S.append(("6 · Numbers", "", body))
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in VERDICT) + "</div>"
    body += ('<div class="ask"><b>For the CEO</b><ol>'
             f"<li>Approve cell <b>{RECOMMENDED}</b> (recommended), or name another (B browner, C pale, D with "
             "the Reich graft).</li>"
             "<li>Collar and tag on every cell: keep, or drop for a bare dog.</li>"
             "<li>On approval the 46 lumps of BESTIARY §6 are drawn on this model (pain H and death I-N are "
             "not rendered yet).</li></ol></div>")
    S.append(("7 · How it reads, and the recommendation", "", body))
    intro = ("D48: the CEO rejected every cell of the first hound sweep and asked for a German shepherd, brown, "
             "from a real one's anatomy; this replaces D45's darker khaki hide. Four colour cells of one dog, "
             "built on rig_core's quadruped skeleton and gallop, rotations 1, 3, 5 traced (7 mirrored), the "
             f"bite E-G, and every cell at 1x on MAP01's walls. Palette v1, seed {SEED}, no system fonts. Built "
             "by <code>tools/art/gen_hound.py</code>. Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_hound.py on tools/art/rig_core.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), "
              "deterministic, no system fonts. Freedoom 0.13.0 sprites shown for scale only (BSD-3).")
    path = out_dir / f"{stamp}_F5_hound-gsd-sweep.html"
    sheetlib.write_sheet(path, lang="en", title="Reich hound as a German shepherd — sweep (F5, D48)",
                         subtitle="SDHN · four cells · rotations 1, 3, 5, the mirror and the bite · draft",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", core.SHEET_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


# ================================================================ the full set (D50)
# D50 (CEO, 2026-10-14): "Perro A". Cell A as drawn, collar and tag
# included, gets every frame SD_ReichHound's states name
# (src/zscript/monsters/reich_hound.zs, today on Freedoom's SARG; BESTIARY
# §6, MOD-SPEC §6.3 reserves SDHN): the gallop A-D (Spawn uses A B), the
# bite E-G and the pain H at 8 rotations, drawn 1-5 in mirror mode (the
# dog is symmetric and wears no insignia, so the engine flips 2-4 into
# 8-6); the death I-N at rotation 0. No XDeath: the class has none
# (BESTIARY §6, the engine falls back to Death), so there is no gib.
#
# Blood (D49): dark red, abundant, flag_red 0-5 and black, as the rifleman's
# and the Legion's: a round opens the left side of the neck at I, the burst
# lands as splats, the coat soaks, blood runs from the mouth, and a pool
# spreads under the neck and chest from L to N.
#
# The corpse (the CEO on the Legion's first L0: "parece que se apoye en el
# hombro"): N lies flat on its right side, the whole body on the floor, the
# legs relaxed, the head on the floor, in its pool. It is not posed by eye:
# the body is rolled onto its side and put on the floor, then the neck and
# head, the tail and the two upper legs are each let FALL about their root
# (bisection on the angle, rig_core.lowest_y) until they touch the floor.
# lying_report() measures it and tests/test_gen_hound.py holds it.
FULL_CELL = CELL["A"]           # D50
FULL_DIR = OUT_DIR / "full_A"
ZS = PROJECT_ROOT / "src" / "zscript" / "monsters" / "reich_hound.zs"
FULL_ROTS = core.drawn_rotations(mirror=True)      # 1-5 traced; 6-8 are the engine's flips
PAIN_FRAMES = ("H",)
DEATH_FRAMES = ("I", "J", "K", "L", "M", "N")
ROTATED_FRAMES = WALK_FRAMES + BITE_FRAMES + PAIN_FRAMES
FULL_GROUPS = (("gallop", WALK_FRAMES, True), ("bite", BITE_FRAMES, True),
               ("pain", PAIN_FRAMES, True), ("death", DEATH_FRAMES, False))
DEATH_CV = Canvas(128, 88, 64, 62)  # a dog lying across, its pool, the burst's splats; axis centred

# ---------------------------------------------------------------- blood materials
BLOOD_MATERIALS: dict[str, core.Mat] = {
    "blood": M("flag_red", 1, 5, black_floor=True, shift=False, flat=True),   # spray, splats, stains, runs
    "pool": M("flag_red", 0, 3, black_floor=True, shift=False, flat=True),    # standing blood: darker
}
BLOOD_RAMP = "flag_red"
BLOOD_MAX_INDEX = 5             # D49: no blood colour brighter than flag_red 5


def full_materials(cell: Cell = FULL_CELL) -> dict[str, core.Mat]:
    """The cell's table (materials_for) with the two blood materials appended."""
    table = materials_for(cell)
    for name, mat in BLOOD_MATERIALS.items():
        core.register_material(name, mat, table)
    return table


# ---------------------------------------------------------------- the states, read from the actor
def zs_states(path: Path = ZS) -> dict[str, list[tuple[str, int]]]:
    """SD_ReichHound's state labels and their (frame letter, tics), in order,
    read from the ZScript file (the sprite name is ignored: it is SARG today)."""
    out: dict[str, list[tuple[str, int]]] = {}
    label = None
    in_states = False
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.split("//")[0].rstrip()
        if s.strip() == "States":
            in_states = True
            continue
        if not in_states:
            continue
        m = re.match(r"^\s*([A-Za-z]+):\s*$", s)
        if m:
            label = m.group(1)
            out[label] = []
            continue
        m = re.match(r"^\s*([A-Z0-9]{4})\s+([A-Z]+)\s+(-?\d+)\b", s)
        if m and label:
            out[label] += [(ch, int(m.group(3))) for ch in m.group(2)]
    return out


# ---------------------------------------------------------------- pain (H)
PAIN_PHASE = 0.75               # the forepaws landing: it checks its run
PAIN_CROUCH = 5.0               # units the body sinks: the hindquarters drop, a cringe
PAIN_HEAD = 6.0                 # degrees: the head pulled in, level (the bite E holds it up)
PAIN_JAW = 24.0                 # a yelp
PAIN_REAR = -3.0                # degrees: the forehand dips, about the hind paws
PAIN_TUCK = -40.0               # the tail tucked (degrees added to the gallop's)
PAIN_TAIL = -18.0               # the death's I and J: the tail clamped down


def _rigid(prims: list[core.Prim], R: np.ndarray, pivot, offset=(0.0, 0.0, 0.0)) -> None:
    """Rotate primitives by R about pivot, then move them by offset."""
    pivot, offset = np.asarray(pivot, float), np.asarray(offset, float)
    for p in prims:
        p.xm = R @ p.xm
        p.xt = R @ (p.xt - pivot) + pivot + offset


def _on_floor(prims: list[core.Prim]) -> None:
    _rigid(prims, np.eye(3), V(0, 0, 0), V(0, -core.lowest_y(prims), 0))


def pain_model(cell: Cell = FULL_CELL) -> list[core.Prim]:
    """H: hit while running, the dog cringes: it checks its stride, the
    body sinks on its haunches, the head pulled in, the mouth open in a
    yelp, the tail tucked. Built to read apart from the bite's head-up E."""
    b = GSD_BUILD
    build = replace(b, pelvis=(b.pelvis[0], b.pelvis[1] - PAIN_CROUCH, b.pelvis[2]))
    q = core.pose_quadruped(build, core.QuadPose("H", "pain", PAIN_PHASE))
    bp = body_pitch_of(q)
    P = dog(cell, q, jaw_open=PAIN_JAW, head_a=HEAD_ANGLE + PAIN_HEAD + HEAD_FOLLOW * bp,
            tail_a=TAIL_ANGLE + PAIN_TUCK + 0.5 * bp)
    _rigid(P, core.rot_x(PAIN_REAR), (q.legs["hl"][3] + q.legs["hr"][3]) / 2)
    _on_floor(P)
    return P


# ---------------------------------------------------------------- death (I-N)
def axis_rot(axis, deg: float) -> np.ndarray:
    """Rotation by `deg` about `axis` (right hand), Rodrigues."""
    k = np.asarray(axis, float)
    k = k / np.linalg.norm(k)
    a = np.deg2rad(deg)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * (K @ K)


@dataclass(frozen=True)
class Fall:
    """One death frame. Standing frames (I, J) pose the gallop skeleton;
    lying frames (K-N) build the death rig with the legs given by angles."""
    t: float                    # s after the hit (blood: how far the burst has flown)
    roll: float                 # degrees onto its right side (90: flat on it)
    jaw: float
    head: float                 # degrees added to the skull's angle (standing: the gallop's; lying: the neck's)
    legs: str = ""              # lying frames: a key of DEATH_LEGS
    settle: tuple = ()          # what is let fall to the floor: keys of SETTLE_PARTS
    pool: float = 0.0           # share of the full pool (0: none yet)
    stain: float = 2.0          # half height of the soaked coat round the wound
    rear: float = 0.0           # standing: forehand lifted (degrees)
    crouch: float = 0.0         # standing: how far the body sinks on buckling legs (units)


# Leg angles of the death rig, degrees from the body's own "down" (+ towards
# the head), per bone (hind: femur, tibia, metatarsus; fore: upper arm,
# forearm, pastern), and a lateral lean (x per unit length; - leans to the
# floor side once it lies on its right). r = the right (lower) legs, l = the upper.
DEATH_LEGS = {
    "stiff": {"fr": ((40, 55, 60), 0.0), "fl": ((48, 62, 66), 0.05),        # the death throe: legs thrown out
              "hr": ((-35, -50, -55), 0.0), "hl": ((-28, -45, -50), 0.05)},
    "falling": {"fr": ((10, 30, 45), 0.0), "fl": ((18, 38, 50), 0.0),
                "hr": ((30, -30, -15), 0.0), "hl": ((35, -22, -10), 0.0)},
    "easing": {"fr": ((10, 45, 55), 0.0), "fl": ((25, 52, 60), -0.05),
               "hr": ((-10, -40, -35), 0.0), "hl": ((0, -32, -28), -0.05)},
    "relaxed": {"fr": ((-12, 22, 48), 0.0), "fl": ((4, 36, 58), -0.08),     # the corpse: a little flexed, scissored
                "hr": ((18, -38, -22), 0.0), "hl": ((30, -24, -8), -0.08)},
}
LYING_SPINE = (3.0, 0.5, -1.0)  # the top line relaxes: no slope, no arch
LYING_NECK = (10.0, 2.0)        # the neck stretched out along the back
LYING_TAIL = (-14.0, (6.0, 2.0))    # first bone, then (down, upturn): limp, no sabre
LYING_HIP_X = 2.6               # the lower hip, pressed in: its thigh lies level with the ribs
LYING_SHOULDER_X = 3.0
ROLL_PIVOT_X = 4.0              # it rolls over the line of its right paws
DEATH_YAW = 90.0                # rotation 0 is seen from the front: turned, it lies across, head screen left
SETTLE_MAX = 75.0               # degrees a part may fall
SETTLE_STEPS = 14               # bisection steps

SETTLE_PARTS = {                # what falls: (groups, limb, side, proximal prims kept, the pivot, the tip)
    "neck": (("neck", "head", "jaw"), "", 0, 0, "withers", "nose"),
    "tail": (("tail",), "", 0, 0, "tail_root", "tail_tip"),
    "fl": (("leg_l",), "foreleg", core.LEFT, 0, "shoulder_l", "paw_fl"),     # the upper legs fall whole
    "hl": (("leg_l",), "hindleg", core.LEFT, 0, "hip_l", "paw_hl"),
    "fr": (("leg_r",), "foreleg", core.RIGHT, 1, "elbow_r", "paw_fr"),       # the lower ones lie under the
    "hr": (("leg_r",), "hindleg", core.RIGHT, 2, "knee_r", "paw_hr"),        # body: the thigh stays, the shank falls
}
SETTLE_ALL = ("neck", "tail", "fr", "hr", "fl", "hl")   # the corpse: everything that hangs comes to rest

FALLS = {                       # reich_hound.zs Death: I J 8, K L M 4, N -1 (A_Scream on J, A_NoBlocking on L)
    "I": Fall(0.05, 8.0, 30.0, 30.0, stain=2.0, rear=10.0),
    "J": Fall(0.28, 32.0, 18.0, 4.0, stain=3.2, crouch=7.0),
    "K": Fall(0.51, 62.0, 14.0, -4.0, legs="falling", stain=4.2),
    "L": Fall(0.63, 90.0, 12.0, -6.0, legs="stiff", settle=("neck", "tail"), pool=0.35, stain=4.8),
    "M": Fall(0.74, 90.0, 8.0, -6.0, legs="easing", settle=SETTLE_ALL, pool=0.65, stain=5.2),
    "N": Fall(3.0, 90.0, 6.0, -6.0, legs="relaxed", settle=SETTLE_ALL, pool=1.0, stain=4.8),
}
WOUND = (4.9, -2.6, 3.4)        # chest bone frame: the left side of the neck's root, where the round went in


def death_rig(fall: Fall) -> core.QuadRig:
    """The skeleton of a lying frame, in the dog's own frame (as if it
    stood): spine and neck by spine_chain, the legs by DEATH_LEGS' angles."""
    b = GSD_BUILD
    pelvis = V(*b.pelvis)
    spine, s_ang = core.spine_chain(pelvis, b.spine, LYING_SPINE)
    withers = spine[-1]
    neck, n_ang = core.spine_chain(withers, b.neck, LYING_NECK, pitch=s_ang[-1])
    legs = {}
    for leg in core.LEGS:
        side = core.LEFT if leg.endswith("l") else core.RIGHT
        angles, lean = DEATH_LEGS[fall.legs][leg]
        if leg.startswith("h"):
            hx = b.hip_x if side == core.LEFT else LYING_HIP_X
            root = pelvis + core.bone_frame(s_ang[0]) @ V(side * hx, -b.hip_drop, 0.0)
            lengths = (b.femur, b.tibia, b.meta)
        else:
            sx = b.shoulder_x if side == core.LEFT else LYING_SHOULDER_X
            root = withers + core.bone_frame(s_ang[-1]) @ V(side * sx, -b.shoulder_drop, 0.0)
            lengths = (b.upper, b.lower, b.pastern + 1.2)
        joints = [root]
        for L, a in zip(lengths, angles):
            r = np.deg2rad(a)
            d = V(lean, -np.cos(r), np.sin(r))
            joints.append(joints[-1] + L * d / np.linalg.norm(d))
        legs[leg] = tuple(joints)
    return core.QuadRig(spine, s_ang, neck, n_ang, legs, {k: v[-1] for k, v in legs.items()})


def settle_part(part: list[core.Prim], pivot: np.ndarray, tip: np.ndarray) -> float:
    """Let `part` fall about `pivot` (the tip swinging down) until its lowest
    point touches the floor; returns the angle. Bisection on rig_core.lowest_y."""
    v = tip - pivot
    v = v / np.linalg.norm(v)
    axis = np.cross(v, V(0, -1, 0))
    if np.linalg.norm(axis) < 1e-6 or core.lowest_y(part) <= 0.0:
        return 0.0
    keep = [(p.xm, p.xt) for p in part]

    def low_at(deg):
        _rigid(part, axis_rot(axis, deg), pivot)
        y = core.lowest_y(part)
        for p, (xm, xt) in zip(part, keep):
            p.xm, p.xt = xm, xt
        return y

    lo, hi = 0.0, SETTLE_MAX
    if low_at(hi) > 0.0:
        lo = hi
    else:
        for _ in range(SETTLE_STEPS):
            mid = (lo + hi) / 2
            if low_at(mid) > 0.0:
                lo = mid
            else:
                hi = mid
    _rigid(part, axis_rot(axis, lo), pivot)
    return lo


def settle_prims(P: list[core.Prim], what: str) -> list[core.Prim]:
    """The primitives of one part that falls (SETTLE_PARTS)."""
    groups, limb, side, kept, _, _ = SETTLE_PARTS[what]
    if limb:
        return [p for p in P if p.grp in groups and p.limb == limb and p.side == side][kept:]
    return [p for p in P if p.grp in groups]


def death_model(frame: str, cell: Cell = FULL_CELL) -> tuple[list[core.Prim], dict]:
    """The dog of death frame I-N in model space (floor y = 0; rotation 0
    looks at it from +z), without the floor's blood; and its anchors (the
    wound, the mouth, the withers, ..., model space)."""
    fall = FALLS[frame]
    if fall.legs:                                           # lying: the death rig
        q = death_rig(fall)
        P = dog(cell, q, jaw_open=fall.jaw, head_a=q.neck_angles[-1] + fall.head,
                tail_a=LYING_TAIL[0], tail_bends=LYING_TAIL[1])
    else:                                                   # still on its paws: the gallop's skeleton
        b = GSD_BUILD
        build = replace(b, pelvis=(b.pelvis[0], b.pelvis[1] - fall.crouch, b.pelvis[2]))
        q = core.pose_quadruped(build, core.QuadPose(frame, "death", 0.0))
        bp = body_pitch_of(q)
        P = dog(cell, q, jaw_open=fall.jaw, head_a=HEAD_ANGLE + fall.head + HEAD_FOLLOW * bp,
                tail_a=TAIL_ANGLE + PAIN_TAIL + 0.5 * bp)
        if fall.rear:
            _rigid(P, core.rot_x(fall.rear), (q.legs["hl"][3] + q.legs["hr"][3]) / 2)
    withers, sacrum = q.spine[-1], q.spine[0]
    # the coat soaks round the wound (rides the chest), on the side the round went in
    s = fall.stain
    for c, r, base in (((WOUND[0] + 0.35, WOUND[1] - s * 0.3, WOUND[2] - 0.4), (1.2, s, s * 1.1), 0.45),
                       ((WOUND[0] + 0.9, WOUND[1], WOUND[2]), (0.8, 0.9, 0.9), 0.22)):
        P.append(core.on_bone(core.ellipsoid("blood", base, c, r, grp="body"), withers, q.spine_angles[-1]))
    nose = next(p for p in P if p.mat == "nose")
    tail_ends = [p.xm @ p.b + p.xt for p in P if p.grp == "tail" and p.kind == "roundcone"]
    anchors = {"wound": withers + core.bone_frame(q.spine_angles[-1]) @ V(*WOUND),
               "withers": withers.copy(), "sacrum": sacrum.copy(),
               "tail_root": sacrum + core.bone_frame(q.spine_angles[0]) @ V(0, -0.8, -6.6),
               "tail_tip": min(tail_ends, key=lambda x: x[2]),
               "nose": nose.xm @ nose.a + nose.xt,
               **{f"hip_{s}": q.legs[f"h{s}"][0].copy() for s in "lr"},
               **{f"shoulder_{s}": q.legs[f"f{s}"][0].copy() for s in "lr"},
               "knee_r": q.legs["hr"][1].copy(), "elbow_r": q.legs["fr"][1].copy(),
               **{f"paw_{k}": q.legs[k][3].copy() for k in core.LEGS}}
    # ------------------------------------------------ roll onto its right side, turn it across the screen
    R = core.rot_y(DEATH_YAW) @ core.rot_z(-fall.roll)
    pivot = V(-ROLL_PIVOT_X, 0.0, 0.0)
    _rigid(P, R, pivot)
    anchors = {k: R @ (v - pivot) + pivot for k, v in anchors.items()}
    cs = np.array([p.bound()[0] for p in P if p.grp == "body"])
    centre = (cs.min(axis=0) + cs.max(axis=0)) / 2
    falling = {id(p) for w in fall.settle for p in settle_prims(P, w)}
    resting = [p for p in P if id(p) not in falling]
    shift = V(-centre[0], -core.lowest_y(resting), -centre[2])
    _rigid(P, np.eye(3), V(0, 0, 0), shift)
    anchors = {k: v + shift for k, v in anchors.items()}
    # ------------------------------------------------ let what hangs fall to the floor
    for what in fall.settle:
        *_, root, tip = SETTLE_PARTS[what]
        part = settle_prims(P, what)
        deg = settle_part(part, anchors[root], anchors[tip])
        if what == "neck":                                  # the nose and the mouth fall with the head
            v = anchors["nose"] - anchors["withers"]
            Rn = axis_rot(np.cross(v / np.linalg.norm(v), V(0, -1, 0)), deg)
            anchors["nose"] = Rn @ (anchors["nose"] - anchors["withers"]) + anchors["withers"]
    anchors["mouth"] = np.mean([p.bound()[0] for p in P if p.grp == "jaw"], axis=0)
    return P, anchors


# ---------------------------------------------------------------- blood on the floor
BLOOD_GRAVITY = 400.0           # units / s^2: the burst lands within the death's first frames
N_SPRAY = 34                    # droplets of the burst
SPRAY_X = 52.0                  # landed splats stay inside DEATH_CV (check_edges)
SPRAY_Z = (-20.0, 24.0)
AIR_Y = 50.0                    # and so do the ones in the air
POOL_FULL = (21.0, 11.0)        # (x, z) radii of N's pool under the neck and chest
POOL_FORWARD = 4.0              # its centre this far towards the camera: a floor pool is seen at 9 degrees


def droplet(p0, v, t: float, r: float, grav: float = BLOOD_GRAVITY) -> core.Prim:
    """A drop `t` s after leaving p0 at v: in the air, or a flat splat once landed."""
    p0, v = np.asarray(p0, float), np.asarray(v, float)
    rest = r * 0.3
    tl = (v[1] + np.sqrt(v[1] ** 2 + 2 * grav * max(p0[1] - rest, 0.0))) / grav
    tt = min(t, tl)
    p = p0 + v * tt + V(0, -0.5 * grav * tt * tt, 0)
    x = float(np.clip(p[0], -SPRAY_X, SPRAY_X))
    z = float(np.clip(p[2], *SPRAY_Z))
    if t >= tl:
        return core.ellipsoid("blood", 0.42, (x, 0.2, z), (r * 2.0, 0.35, r * 1.5), grp="splat")
    return core.ellipsoid("blood", 0.62, (x, min(float(p[1]), AIR_Y), z), (r, r * 1.15, r), grp="spray")


def burst(origin, t: float, rng) -> list[core.Prim]:
    """The round's spray from the wound: sideways, up, mostly towards the
    camera (the wound's side faces it at I), every fifth a heavy gout."""
    out = []
    for i in range(N_SPRAY):
        d = V(rng.uniform(-1, 1), rng.uniform(-0.1, 1.0), rng.uniform(-0.3, 1.0))
        d /= np.linalg.norm(d)
        gout = i % 5 == 0
        sp = rng.uniform(8, 24) if gout else rng.uniform(30, 85)
        r = rng.uniform(1.2, 1.7) if gout else rng.uniform(0.6, 1.05)
        out.append(droplet(origin, d * sp, t, r))
    return out


def pool(cx: float, cz: float, rx: float, rz: float, rng) -> list[core.Prim]:
    """A pool on the floor: one flat ellipse and three lobes."""
    out = [core.ellipsoid("pool", 0.55, (cx, 0.3, cz), (rx, 0.55, rz), grp="pool")]
    for _ in range(3):
        ox, oz = rng.uniform(-0.7, 0.7) * rx, rng.uniform(-0.3, 0.6) * rz
        out.append(core.ellipsoid("pool", 0.62, (cx + ox, 0.32, cz + oz),
                                  (rx * rng.uniform(0.35, 0.55), 0.6, rz * rng.uniform(0.4, 0.6)), grp="pool"))
    return out


_WOUND_AT_I: dict = {}


def wound_at_hit(cell: Cell = FULL_CELL) -> np.ndarray:
    """Where the wound was when the round hit (frame I): the burst's origin."""
    if cell.key not in _WOUND_AT_I:
        _WOUND_AT_I[cell.key] = death_model("I", cell)[1]["wound"]
    return _WOUND_AT_I[cell.key]


def death_blood(frame: str, anchors: dict, cell: Cell = FULL_CELL, seed: int = SEED) -> list[core.Prim]:
    """The blood off the body for death frame I-N: the burst, the mouth's
    run, the pool."""
    fall = FALLS[frame]
    out = burst(wound_at_hit(cell), fall.t, np.random.default_rng(seed + 11))
    if frame in "KLMN":                                     # it runs from the mouth
        m = anchors["mouth"]
        k = "KLMN".index(frame)
        out.append(core.rcone("blood", 0.45, m + V(0, 0.4, 0.6), V(m[0] - 0.5, max(m[1] - 2.0 - k, 0.4), m[2] + 1.0),
                              0.7, 0.55, grp="spray"))
    if fall.pool:
        g = fall.pool
        w, m = anchors["withers"], anchors["mouth"]
        out += pool(float(w[0]) - 2.0, POOL_FORWARD + 2.0 * g, POOL_FULL[0] * g, POOL_FULL[1] * (0.4 + 0.6 * g),
                    np.random.default_rng(seed + 14))
        out += pool(float(m[0]), POOL_FORWARD - 1.0, 4.0 + 3.0 * g, 4.0 + 2.0 * g, np.random.default_rng(seed + 15))
    return out


# The death frames are rotation 0 and lie on the floor, where the player
# always looks DOWN at them (eye 41 units up: about 25-30 degrees at 64-96
# units). Seen from the rig's 9 degrees a dog on its side is a tan tube, its
# legs foreshortened towards the camera and its saddle hidden. So the death
# frames are drawn from higher: the whole scene, floor blood included, is
# tipped towards the camera by DEATH_TILT more degrees, ramping in as it
# falls so I (still standing) matches the gallop. Only the render is
# tipped; the model the lying test measures stays on its floor.
DEATH_TILT = {"I": 0.0, "J": 8.0, "K": 18.0, "L": 28.0, "M": 28.0, "N": 28.0}


def full_model(frame: str, cell: Cell = FULL_CELL, seed: int = SEED, tilt: bool = True) -> list[core.Prim]:
    """Every primitive of one lump of the full set, model space (death
    frames tipped by DEATH_TILT unless `tilt` is False)."""
    if frame in DEATH_FRAMES:
        P, anchors = death_model(frame, cell)
        P = P + death_blood(frame, anchors, cell, seed)
        if tilt and DEATH_TILT[frame]:
            _rigid(P, core.rot_x(-DEATH_TILT[frame]), V(0, 0, 0))
        return P
    if frame in PAIN_FRAMES:
        return pain_model(cell)
    return gsd_model(cell, frame)


def full_canvas(frame: str) -> Canvas:
    return DEATH_CV if frame in DEATH_FRAMES else CV


def render_full_layers(frame: str, rotation: int, cell: Cell = FULL_CELL, seed: int = SEED) -> core.Layers:
    return core.render_layers(full_model(frame, cell, seed), rotation, full_canvas(frame), full_materials(cell),
                              seed=seed, what=f"{SPRITE}{frame}{rotation}")


def render_full(frame: str, rotation: int, cell: Cell = FULL_CELL, seed: int = SEED) -> np.ndarray:
    """One lump of the full set, RGBA: 6-8 are the flips of 4-2, as the engine draws them."""
    src = core.MIRRORED.get(rotation)
    rgba = render_full_layers(frame, src if src is not None else rotation, cell, seed).rgba
    return core.mirror_sprite(rgba, full_canvas(frame)) if src is not None else rgba


def full_plan() -> list[tuple[str, int]]:
    """(frame, rotation) of every lump drawn: A-H at 1-5 (mirror mode), I-N at 0."""
    return core.frame_plan(FULL_GROUPS, mirror=True)


def full_lump(frame: str, rotation: int) -> str:
    """The lump name (file stem): SDHNA1, SDHNA2A8, ..., SDHNN0."""
    return core.rotation_lump(SPRITE, frame, rotation, mirror=True)


# ---------------------------------------------------------------- the corpse, measured
LYING_MAX = 1.0                 # units: a part this far above the floor still lies on it
LYING_TOP = 15.0                # nothing of the body (blood aside) higher than this: nothing propped up
LYING_SPAN = 40.0               # the parts on the floor spread at least this far along the body


def corpse_parts(P: list[core.Prim]) -> dict[str, list[core.Prim]]:
    """The lying dog's parts by name: what must rest on the floor."""
    torso = [p for p in P if p.grp == "body" and p.mat != "blood" and p.limb == ""]
    out = {"chest": [p for p in torso if p.kind == "ellipsoid" and float(np.max(p.r)) > 9.0],
           "croup": [p for p in torso if p.kind == "ellipsoid" and abs(float(p.r[2]) - 5.2) < 1e-6]
           + [p for p in P if p.limb == "hindleg" and p.side == core.RIGHT and p.grp != "body"][:1],
           "neck": [p for p in P if p.grp == "neck"],
           "head": [p for p in P if p.grp in ("head", "jaw")],
           "tail": [p for p in P if p.grp == "tail"]}
    for name, limb, side in (("fore_right", "foreleg", core.RIGHT), ("fore_left", "foreleg", core.LEFT),
                             ("hind_right", "hindleg", core.RIGHT), ("hind_left", "hindleg", core.LEFT)):
        out[f"paw_{name}"] = [p for p in P if p.limb == limb and p.side == side and p.grp != "body"][-1:]
    return out


def lying_report(P: list[core.Prim]) -> dict[str, float]:
    """Each part's lowest point above the floor, in units (rig_core.lowest_y)."""
    return {k: round(core.lowest_y(v), 2) for k, v in corpse_parts(P).items() if v}


def highest_y(prims: list[core.Prim]) -> float:
    """The highest surface point: rig_core.lowest_y on the primitives mirrored in y."""
    F = np.diag([1.0, -1.0, 1.0])
    flipped = [replace(p, xm=F @ p.xm, xt=F @ p.xt) for p in prims]
    return -core.lowest_y(flipped)


def leg_bends(P: list[core.Prim]) -> dict[str, list[float]]:
    """Each leg's joint angles in degrees (0: straight), from its bone cones
    as posed: hind thigh-shank-metatarsus, fore upper arm-forearm."""
    out = {}
    for name, limb, side, bones in (("fore_right", "foreleg", core.RIGHT, (0, 1)),
                                    ("fore_left", "foreleg", core.LEFT, (0, 1)),
                                    ("hind_right", "hindleg", core.RIGHT, (0, 2, 3)),
                                    ("hind_left", "hindleg", core.LEFT, (0, 2, 3))):
        lp = [p for p in P if p.limb == limb and p.side == side and p.grp != "body"]
        dirs = []
        for i in bones:
            d = lp[i].xm @ (lp[i].b - lp[i].a)
            dirs.append(d / np.linalg.norm(d))
        out[name] = [round(float(np.degrees(np.arccos(np.clip(a @ b, -1, 1)))), 1)
                     for a, b in zip(dirs[:-1], dirs[1:])]
    return out


def corpse_metrics(frame: str = "N") -> dict:
    """The lying checks on one death frame's model (untilted): parts above the
    floor, the highest point, how far the supports spread, the roll, the legs."""
    P, anchors = death_model(frame)
    body = [p for p in P if p.mat != "blood"]
    parts = corpse_parts(P)
    rep = {k: round(core.lowest_y(v), 2) for k, v in parts.items() if v}
    xs = [float(np.mean([p.bound()[0][0] for p in parts[k]])) for k, v in rep.items() if v <= LYING_MAX]
    chest = parts["chest"][0]
    return {"lowest": rep, "top": round(highest_y(body), 2), "span": round(max(xs) - min(xs), 1),
            "back_up": round(float((chest.xm @ V(0, 1, 0))[1]), 3),     # 0: the spine's "up" lies level
            "spine_drop": round(float(abs(anchors["withers"][1] - anchors["sacrum"][1])), 2),
            "legs": leg_bends(P)}


def crop_common(arrs: list[np.ndarray], pad: int = 2) -> list[np.ndarray]:
    """The same window cut from every array: the union of their opaque
    pixels plus `pad`, so a strip or a GIF keeps its frames aligned and
    drops the empty canvas (the sheet only; the lumps keep their canvas)."""
    a = np.zeros(arrs[0].shape[:2], bool)
    for x in arrs:
        a |= x[..., 3] > 0
    ys, xs = np.nonzero(a)
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad + 1, a.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad + 1, a.shape[1])
    return [x[y0:y1, x0:x1] for x in arrs]


def _gif_runs(seq: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Consecutive (letter, tics) merged: SDHN AABBCCDD 2 is A 4, B 4, C 4, D 4."""
    out: list[tuple[str, int]] = []
    for f, t in seq:
        if out and out[-1][0] == f:
            out[-1] = (f, out[-1][1] + t)
        else:
            out.append((f, t))
    return out


HOLD_MS = 1600                  # a -1 frame (the corpse) held this long before the GIF loops
LINEUP_FRAMES = (("A", 1), ("C", 3), ("F", 3), ("H", 3), ("C", 7))
CORPSE_SLOT = 120               # lineup slot of a corpse: the dog lies 70 px across


def build_full(out_dir: Path = FULL_DIR, seed: int = SEED) -> dict:
    """Every lump of the full set (PNG with grAb), the GIFs at game speed
    (tics read from reich_hound.zs), the 1x lineups, metrics.json."""
    out_dir.mkdir(parents=True, exist_ok=True)
    spr: dict = {}
    for f, r in full_plan():
        spr[(f, r)] = render_full(f, r, seed=seed)
        core.save_sprite(spr[(f, r)], out_dir / f"{full_lump(f, r)}.png", full_canvas(f))
        print(full_lump(f, r), flush=True)
    return finish_full({"sprites": _with_mirrors(spr)}, out_dir)


def _with_mirrors(spr: dict) -> dict:
    for f in ROTATED_FRAMES:
        for r, src in core.MIRRORED.items():
            spr[(f, r)] = core.mirror_sprite(spr[(f, src)], CV)
    return spr


def load_full(out_dir: Path = FULL_DIR) -> dict:
    spr = {}
    for f, r in full_plan():
        with Image.open(out_dir / f"{full_lump(f, r)}.png") as im:
            spr[(f, r)] = np.asarray(im.convert("RGBA")).copy()
    return finish_full({"sprites": _with_mirrors(spr)}, out_dir)


def finish_full(data: dict, out_dir: Path = FULL_DIR) -> dict:
    """GIFs, lineups and metrics from the sprites."""
    spr = data["sprites"]
    st = zs_states()
    ms = lambda n: int(round(n * core.TIC_MS))  # noqa: E731
    gifs = {}

    def gif(name, seq, rot, bg=core.NEUTRAL):
        frames = [core.on_bg(x, bg) for x in crop_common([spr[(f, rot)] for f, _ in seq])]
        durs = [HOLD_MS if t < 0 else ms(t) for _, t in seq]
        gifs[name] = core.save_gif(frames, durs, out_dir / f"{SPRITE}_{name}.gif")

    see = _gif_runs(st["See"])
    for r in range(1, core.ROTATIONS + 1):
        gif(f"see_rot{r}", see, r)
    gif("spawn_rot1", _gif_runs(st["Spawn"]), 1)
    for r in (1, 3, 5):
        gif(f"melee_rot{r}", see + _gif_runs(st["Melee"]), r)
        gif(f"pain_rot{r}", see + _gif_runs(st["Pain"]) + see, r)
    gif("death", _gif_runs(st["Death"]), 0)
    data["gifs"] = gifs
    # ---------------------------------------------- at 1x on MAP01, beside the rifleman
    rr = rifleman()
    rr_side = _rifleman_lump("SDRRA3.png", core.STAND)
    rr_dead = _rifleman_lump("SDRRL0.png", None)
    g = grab()
    gd = core.grab_offsets(DEATH_CV)
    scenes = {}
    for key, wall, light, what in SCENES:
        floor = "SDFLR1" if key == "S6" else "SDFLR2"
        row = [x for x in (rr, rr_side) if x is not None] + [(spr[fr], *g) for fr in LINEUP_FRAMES]
        sc = core.lineup(row, wall, light, SLOT_W * len(row), floor, load=load_rgb)
        dead = [x for x in (rr_dead,) if x is not None] + [(spr[("N", 0)], *gd)]
        sd = core.lineup(dead, wall, light, CORPSE_SLOT * len(dead), floor, load=load_rgb)
        Image.fromarray(sc).save(out_dir / f"lineup_{key}.png")
        Image.fromarray(sd).save(out_dir / f"lineup_{key}_dead.png")
        labels = (["SDRR A1", "SDRR A3"][:len(row) - len(LINEUP_FRAMES)]
                  + [f"{SPRITE} {f}{r}" for f, r in LINEUP_FRAMES])
        scenes[key] = (sc, sd, labels, ["SDRR L0"][:len(dead) - 1] + [f"{SPRITE} N0"], wall, light, what)
    # the death at game speed on the worst wall, the rifleman standing by
    key, wall, light, _ = SCENES[2]
    frames, durs = [], []
    for f, t in _gif_runs(st["Death"]):
        row = [x for x in (rr,) if x is not None] + [(spr[(f, 0)], *gd)]
        frames.append(core.lineup(row, wall, light, CORPSE_SLOT * len(row), "SDFLR2", load=load_rgb))
        durs.append(HOLD_MS if t < 0 else ms(t))
    gifs["death_S3"] = core.save_gif(frames, durs, out_dir / f"{SPRITE}_death_S3.gif")
    frames = []
    for f, t in see:
        row = [x for x in (rr,) if x is not None] + [(spr[(f, 3)], *g)]
        frames.append(core.lineup(row, wall, light, SLOT_W * len(row), "SDFLR2", load=load_rgb))
    gifs["see_S3"] = core.save_gif(frames, [ms(t) for _, t in see], out_dir / f"{SPRITE}_see_S3.gif")
    data["scenes"] = scenes
    # ---------------------------------------------- numbers
    m = metrics_for(FULL_CELL, spr)
    m["corpse"] = corpse_metrics("N")
    tab = full_materials()
    ids = core.material_ids(tab)
    blood_ids = [ids["blood"], ids["pool"]]
    m["blood_share"] = {}
    for f in DEATH_FRAMES:
        lay = render_full_layers(f, 0)
        m["blood_share"][f] = round(float(np.isin(lay.mat, blood_ids).sum() / max((lay.mat >= 0).sum(), 1)), 3)
    m["heights"] = {f"{f}{r}": int(np.ptp(np.nonzero(spr[(f, r)][..., 3] > 0)[0]) + 1) for f, r in full_plan()}
    data["metrics"] = m
    (out_dir / "metrics.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    return data


def _rifleman_lump(name: str, cv) -> tuple | None:
    path = RIFLEMAN_DIR / name
    if not path.is_file():
        return None
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGBA")).copy()
    return (arr, *(core.grab_offsets(cv) if cv is not None else core.read_grab(path)))


FULL_VERDICT = [
    "WHAT THIS IS. D50: the CEO chose the German shepherd, cell A, with the collar as drawn. This is its whole "
    "frame set, every letter SD_ReichHound's states name (src/zscript/monsters/reich_hound.zs, read by the "
    "generator for the timings): the gallop A-D (Spawn idles on A B), the bite E-G, the pain H, all at 8 "
    "rotations, and the death I-N at rotation 0. 46 lumps, MOD-SPEC 6.3's reserved SDHN. Mirror mode: the dog "
    "is symmetric and wears no insignia, so 2-4 are traced and the engine flips them into 8-6 (SDHNA2A8, ...). "
    "No gib: the class has no XDeath (BESTIARY 6) and the engine falls back to Death.",
    "THE CORPSE. N lies on its right side, the whole length of it on the floor: chest, croup, neck, head and "
    "tail, all four paws. It is not posed by eye: the body is rolled onto its side and set on the floor, then "
    "the neck and head, the tail and each leg are let fall about their root until they touch it (the lower "
    "legs from the knee and elbow, the upper ones from the hip and shoulder, which is what leaves them "
    "scissored and loose). The test measures every part (section 6) and fails if any is propped up, the "
    "Legion's L0 fault.",
    "THE VIEW OF THE DEATH. The rig's camera looks 9 degrees down, which is right for a standing figure; a "
    "dog lying on its side, seen from there, is a tan tube with its legs end-on. A player looks down at a "
    "corpse (eye 41 units up, 25-30 degrees at 64-96 units), so the death is drawn from 37 degrees, ramped in "
    "as it falls (I at 9, matching the gallop). The model the test measures is not tipped, only the render.",
    "BLOOD (D49). Dark red, flag_red 0-5 and black only, as the rifleman and the Legion: the round opens the "
    "left side of the neck at I, the burst flies and lands as splats, the coat soaks, blood runs from the "
    "mouth, the pool spreads from L and is widest under N. The open mouth (bite, pain, the death's I-K) "
    "keeps the sweep's flag_red 2-8: it is the inside of a mouth, not blood.",
    "SPEED. The GIFs run at the actor's tics: See is SDHN AABBCCDD at 2 tics, so each picture holds 4 tics "
    "(114 ms). The sweep's gallop GIF showed each picture 2 tics, twice as fast as the game.",
    "NOT VERIFIED. All of it is rendered outside the engine (D26): the light is gen_enemy's stand-in, the "
    "rotation order is rig_core's reading of r_things.c, and the corpse's grAb follows the rifleman's (the "
    "near paws sit up to 11 px below the anchor; GZDoom's sprite clipping may lift it). The PM's engine pass "
    "is pending, with the draft overlay (MOD-SPEC 6.9).",
]


def build_full_sheet(data: dict, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    S = []
    spr, gifs, met = data["sprites"], data["gifs"], data["metrics"]
    st = zs_states()
    rows = []
    for label, frames, rot in (("Spawn", "AB", "1-8"), ("See", "ABCD", "1-8"), ("Melee", "EFG", "1-8"),
                               ("Pain", "H", "1-8"), ("Death", "IJKLMN", "0"), ("Raise", "NMLKJI", "0")):
        seq = " ".join(f"{f} {t}" for f, t in _gif_runs(st[label]))
        n = len(set(frames)) * (5 if rot == "1-8" else 1)
        rows.append([label, seq, rot, "reuses A-D" if label in ("Spawn", "Raise") else n])
    body = sheetlib.table(["state", "frames and tics (reich_hound.zs)", "rotations", "lumps"], rows, 3)
    body += (f"<p class=\"lead\">{len(full_plan())} lumps in <code>work/art/enemies/hound_gsd/full_A/</code>, "
             "named as the engine reads them: <code>SDHNA1</code>, <code>SDHNA2A8</code> (2 drawn, 8 its flip), "
             "<code>SDHNA3A7</code>, <code>SDHNA4A6</code>, <code>SDHNA5</code>, ... <code>SDHNI0</code>-"
             "<code>SDHNN0</code>. Each PNG carries its grAb offsets. No XDeath state, so no gib.</p>")
    S.append(("1 · The set", "Every frame SD_ReichHound names, for cell A as approved (D50).", body))
    # turnaround
    names = {1: "front", 2: "", 3: "its left", 4: "", 5: "back", 6: "", 7: "its right", 8: ""}
    body = ""
    for f in ("A", "C"):
        cut = dict(zip(range(1, 9), crop_common([spr[(f, r)] for r in range(1, 9)])))
        body += _strip([core.sprite_tile(cut[r], 3, core.rotation_lump(SPRITE, f, r, mirror=r in (2, 3, 4)
                                                                                 ) if r <= 5 else
                                         f"{SPRITE}{f}{r} = {f}{core.MIRRORED[r]} flipped", names[r])
                        for r in range(1, 9)])
    body += _strip([core.gif_tile(gifs[f"see_rot{r}"], 3, f"rotation {r}", "See, game speed") for r in range(1, 9)])
    S.append(("2 · The turnaround",
              "Frames A (gathered) and C (stretched) at the eight rotations, 3x, then the gallop at each rotation "
              "at game speed. 6, 7 and 8 are not drawn: they are 4, 3 and 2 flipped, as the engine shows them.",
              body))
    # cycles
    body = ""
    for r in (1, 3, 5):
        body += _strip([core.gif_tile(gifs[f"see_rot{r}"], 3, f"See, rotation {r}", "A B C D, 4 tics each"),
                        core.gif_tile(gifs[f"melee_rot{r}"], 3, f"Melee, rotation {r}", "the gallop, then E F G 8"),
                        core.gif_tile(gifs[f"pain_rot{r}"], 3, f"Pain, rotation {r}", "gallop, H 4, gallop")]
                       + [core.sprite_tile(x, 3, core.rotation_lump(SPRITE, f, r, mirror=True)) for f, x in
                          zip(BITE_FRAMES + PAIN_FRAMES, crop_common([spr[(f, r)] for f in BITE_FRAMES + PAIN_FRAMES]))])
    body += _strip([core.gif_tile(gifs["spawn_rot1"], 3, "Spawn, rotation 1", "A B, 10 tics: the idle")])
    S.append(("3 · The cycles at game speed",
              "Every GIF runs at the tics in reich_hound.zs (35 tics a second). The bite opens the mouth, the "
              "only red on the living dog; the pain jerks the head up in a yelp and clamps the tail.", body))
    # death
    body = _strip([core.sprite_tile(x, 3, f"{SPRITE}{f}0", n) for f, n, x in
                   zip(DEATH_FRAMES, ("hit: rears", "buckles", "tips over", "down: the throe", "eases", "dead"),
                       crop_common([spr[(f, 0)] for f in DEATH_FRAMES]))])
    body += _strip([core.gif_tile(gifs["death"], 3, "Death, game speed", "I J 8, K L M 4, N held"),
                    core.sprite_tile(crop_common([spr[("N", 0)]])[0], 5, f"{SPRITE}N0 at 5x", "the corpse")])
    cm = met["corpse"]
    rows = [[k, v] for k, v in cm["lowest"].items()]
    body += sheetlib.table(["part of N", "lowest point above the floor (units)"], rows, 1)
    body += (f"<p class=\"lead\">Highest point of the body {cm['top']} units (the test: under {LYING_TOP}); the parts "
             f"on the floor spread {cm['span']} units along it (at least {LYING_SPAN}); the spine's up axis has "
             f"a vertical component of {cm['back_up']} (0: lying exactly on its side); withers and sacrum "
             f"{cm['spine_drop']} units apart in height. Leg joints (degrees from straight): "
             + "; ".join(f"{k} {', '.join(str(a) for a in v)}" for k, v in cm["legs"].items())
             + ". Blood (share of the opaque pixels, blood and pool materials): "
             + ", ".join(f"{f} {v:.0%}" for f, v in met["blood_share"].items()) + ".</p>")
    S.append(("4 · The death",
              "Rotation 0, one picture for every angle, seen from 37 degrees once it is down (the verdict "
              "says why). Dark red only, flag_red 0-5 and black (D49).", body))
    # lineups
    body = ""
    for key, wall, light, what in SCENES:
        sc, sd, labels, dlabels, *_ = data["scenes"][key]
        body += _strip([core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 1, f"{key} 1x: {wall} at {light}", what),
                        core.tile(core.png_uri(sd), sd.shape[1], sd.shape[0], 1, f"{key} 1x, dead",
                                  " · ".join(dlabels)),
                        core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 2, f"{key} 2x", " · ".join(labels))])
    body += _strip([core.gif_tile(gifs["see_S3"], 1, "S3 1x: the gallop", "SDSTEL1 at 112, rotation 3"),
                    core.gif_tile(gifs["see_S3"], 2, "S3 2x"),
                    core.gif_tile(gifs["death_S3"], 1, "S3 1x: the death", "game speed, the rifleman standing by"),
                    core.gif_tile(gifs["death_S3"], 2, "S3 2x")])
    S.append(("5 · At 1x on MAP01, beside the rifleman",
              "Our rifleman (D38, front and side) then the hound: front, side, bite, pain, the mirrored side; "
              "and the two corpses side by side, each standing on its own offsets. S3 is the worst case, "
              "SDSTEL1 green steel at light 112; S6 runs over SDFLR1's lane line. Light is gen_enemy.py's "
              "stand-in, NOT VERIFIED against GZDoom.", body))
    rows = [[k, v] for k, v in met["heights"].items()]
    body = sheetlib.table(["lump", "height px"], rows, 1)
    body += sheetlib.table(["measure", "value"], [
        ["side h x w (C3)", f"{met['height_px']} x {met['width_px']}"], ["body luma", met["body_luma"]],
        ["gap S3 (mean luma)", met["gap_S3"]],
        ["legible S1/S2/S3/S4/S6", " / ".join(f"{met[f'legible_{k}']:.2f}" for k, *_ in SCENES)],
        ["tan+cream / saddle", f"{met['tan_share']} / {met['saddle_share']}"]], 1)
    S.append(("6 · Numbers", "Heights of every lump drawn (BESTIARY 6: the living dog under 40 px), and the "
              "sweep's legibility measures on this set.", body))
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in FULL_VERDICT) + "</div>"
    body += ('<div class="ask"><b>For the CEO</b><ol>'
             "<li>Approve the set as drawn, or name the frames to redo (the corpse N above all: is it lying "
             "naturally?).</li>"
             "<li>The death seen from above (37 degrees) while the rest is at the rig's 9: keep, or draw it "
             "at 9 like the rifleman's.</li>"
             "<li>On approval: mod-engineer renames SARG to SDHN in reich_hound.zs (the frame letters already "
             "match) and the lumps go to assets/sprites/; the PM's engine pass first.</li></ol></div>")
    S.append(("7 · How it reads, and what is left", "", body))
    intro = ("D50: \"Perro A\". The German shepherd of the sweep's cell A, collar and steel tag as drawn, with every "
             "frame of SD_ReichHound: gallop, bite, pain at 8 rotations (5 drawn, mirror mode), the death at "
             "rotation 0 with D49's dark red blood, and a corpse that lies flat on its side. Built by "
             "<code>tools/art/gen_hound.py --full</code> on rig_core. Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_hound.py on tools/art/rig_core.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), "
              "deterministic, palette v1, no system fonts. MAP01 walls and flats are the mod's own.")
    path = out_dir / f"{stamp}_F5_reich-hound-A-full-set.html"
    sheetlib.write_sheet(path, lang="en", title="Reich hound, German shepherd A — full set (F5, D50)",
                         subtitle="SDHN · 46 lumps · gallop, bite, pain at 8 rotations · death with blood · draft",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", core.SHEET_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    ap.add_argument("--no-sheet", action="store_true", help="sprites, GIFs, lineups and metrics only")
    ap.add_argument("--sheet-only", action="store_true",
                    help="rebuild the lineups and the sheet from the sprites already written")
    ap.add_argument("--full", action="store_true",
                    help="D50: cell A's full frame set into work/art/enemies/hound_gsd/full_A/ (not the sweep)")
    args = ap.parse_args()
    if args.full:
        data = load_full() if args.sheet_only else build_full()
        print(json.dumps(data["metrics"]["corpse"]))
        if not args.no_sheet:
            print("sheet:", build_full_sheet(data, args.stamp).relative_to(PROJECT_ROOT))
        return
    data = load_all() if args.sheet_only else build_all()
    for k, m in data["metrics"].items():
        print(k, m)
    scenes = lineups(data)
    if args.no_sheet:
        return
    path = build_sheet(data, scenes, args.stamp)
    print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
