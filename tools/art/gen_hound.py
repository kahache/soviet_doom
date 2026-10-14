"""F5 — the Reich hound redrawn as a German shepherd (D48), on rig_core's quadruped skeleton.

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

Light model: gen_enemy.py's stand-in (RGB x L/224, re-quantised). NOT
VERIFIED against GZDoom's light tables. Rotation order checked by hand
against r_things.c (rig_core's docstring), NOT in the engine.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import sys
from dataclasses import dataclass
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


def gsd_model(cell: Cell, frame: str) -> list[core.Prim]:
    """The German shepherd for one frame (A-D gallop, E-G bite), model space:
    paws on y = 0, facing +z, +x its LEFT."""
    bite = BITE.get(frame)
    phase = bite.phase if bite else WALK[frame]
    jaw_open = bite.jaw if bite else 0.0
    q = core.pose_quadruped(GSD_BUILD, core.QuadPose(frame, frame, phase))
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
    body_pitch = float(np.mean(q.spine_angles)) - float(np.mean(core.spine_chain(
        V(*GSD_BUILD.pelvis), GSD_BUILD.spine, GSD_BUILD.spine_bends)[1]))

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
    wag = TAIL_WAG * np.sin(2 * np.pi * phase)
    root = at_pelvis(0, -0.8, -6.6)
    t1 = np.deg2rad(TAIL_ANGLE + 0.5 * body_pitch + wag)
    k1 = root + 6.0 * V(0, np.sin(t1), -np.cos(t1))
    t2 = t1 - np.deg2rad(22)
    k2 = k1 + 6.0 * V(0, np.sin(t2), -np.cos(t2))
    t3 = t2 + np.deg2rad(34)                      # the sabre's upturned tip
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
    head_a = HEAD_ANGLE + (bite.head if bite else 0.0) + HEAD_FOLLOW * body_pitch
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    ap.add_argument("--no-sheet", action="store_true", help="sprites, GIFs, lineups and metrics only")
    ap.add_argument("--sheet-only", action="store_true",
                    help="rebuild the lineups and the sheet from the sprites already in work/art/enemies/hound_gsd/")
    args = ap.parse_args()
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
