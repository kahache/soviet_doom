"""F5 — Hybrid Stormtrooper and Reich hound, design sweeps on the 3D rig.

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_storm.py               (Windows)
    .venv/bin/python tools/art/gen_storm.py                       (macOS)
    ... gen_storm.py --stamp 2026-10-13_2230   fixes the sheet's timestamp
    ... gen_storm.py --sheet-only              rebuild the sheet from work/

What this is. D35 (CEO, 2026-10-13): the five most-seen enemies get drawings
of their own. After the Reich rifleman (D38, tools/art/gen_rig.py) come the
Hybrid Stormtrooper (`SD_Stormtrooper`, sprite `SDHS`, BESTIARY §5) and the
Reich hound (`SD_ReichHound`, sprite `SDHN`, BESTIARY §6). Before ~100
images are drawn the CEO sees ONE decision per enemy: what it looks like.
This script is that decision as a SWEEP (PIPELINE stage 2): five labelled
cells per enemy, a few rotations and one attack frame each, every cell at
1x beside its Freedoom placeholder on MAP01's walls. Nothing goes to assets/.

The sweep's dimensions (one row per cell; A is the BESTIARY brief taken
literally, every other cell changes one or two things from it):

  Stormtrooper  head                coat        emitter (his right arm)    extra
    A           crested helmet      greatcoat   forearm cannon             -
    B           crested helmet      greatcoat   shoulder coil + cannon     -
    C           crested helmet      greatcoat   shoulder coil + cannon     chrome pauldron, US patch, back hose
    D           crested + gas mask  tunic       forearm cannon             hose from the mask to the arm
    E           bare skull, chrome  greatcoat   forearm cannon             -
                plate on his right

  Hound         build               head                 extra
    A           long and low        flat, mostly jaw     -
    B           hyena: high front   flat, mostly jaw     withers hump
    C           long and low        flat, mostly jaw     black leather harness and collar (no insignia)
    D           long and low        long crocodile jaw   bony dorsal spines
    E           mastiff: short,     split jaw, open      -
                deep, heavy

How it is built. With gen_rig.py's machinery, imported and not edited: its
SDF primitives, two-bone IK, group transforms, sphere tracer, majority-vote
reduction, contour and rim passes, the D12 armband stamp, the light
stand-in and the lineup on MAP01's walls. The Stormtrooper starts from the
rifleman's own model (gen_rig.build_model): the rifle and his right arm are
taken away and the Legion graft is added in their place, so the Reich half
is literally the approved rifleman. The hound has no model to start from;
it is built here from the same primitives on a quadruped skeleton of its
own (four legs, the hind ones three-segment), which is the test of whether
the rig serves a quadruped (the sheet's section 7 answers it).

New materials (steel_blue chrome, the graft's flesh, hide, black belly,
bone, the bolt) are APPENDED to gen_rig's material table at import time,
so the rifleman's material ids never move (tests/test_gen_storm.py checks
it). Palette v1 has no pink ramp yet (BESTIARY §2.1 reserves it for v2):
the graft's "pink flesh at the seam" is drawn in `plaster_warm` with a
`rust_brown` raw edge, and says so on the sheet.

NO FONTS. The sprites carry no text and nothing here rasterises text; the
sheet is HTML (tools/art/sheetlib.py), like gen_rig.py's.

Outputs (work/ is gitignored):
    work/art/enemies/storm/SDHS_<cell>_<frame><rot>.png   RGBA, hard alpha,
    work/art/enemies/hound/SDHN_<cell>_<frame><rot>.png   palette colours, grAb
    work/art/enemies/{storm,hound}/lineup_*.png, metrics.json
    docs/art/previews/<stamp>_F5_storm-hound-sweep.html    (the sheet)

Light model: gen_enemy.py's stand-in (RGB x L/224, re-quantised). NOT
VERIFIED against GZDoom's light tables.
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
sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402
import gen_rig as rig  # noqa: E402
import sheetlib  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
STORM_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "storm"
HOUND_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "hound"
RIFLEMAN_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "rig"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
SDFLR1 = PROJECT_ROOT / "assets" / "flats" / "soviet_base" / "SDFLR1.png"

STORM_SPRITE = "SDHS"           # BESTIARY §5, MOD-SPEC §6.3
HOUND_SPRITE = "SDHN"           # BESTIARY §6
SEED = 35                       # D35; cloth grain only
V = rig.V
Canvas = rig.Canvas
ANKLE_Y = rig.ANKLE_Y

STORM_CV = Canvas(80, 72, 40, 68)    # the emitter reaches forward in profile
HOUND_CV = Canvas(112, 56, 56, 52)   # a long body lies across in profile
LEGION_MAX = 0.25               # BESTIARY §5: Legion material on <= 25 % of the body
HOUND_MAX_H = 40                # BESTIARY §6: a horizontal bar under 40 units tall
TOUCH_MARGIN = 0                # a sprite may not touch its canvas edge

# ================================================================ materials
M = flat.Material
NEW_MATERIALS: dict[str, flat.Material] = {
    "chrome": M("steel_blue", 3, 15),            # BESTIARY §2.1, Legion chrome 0-5 shadow, 11-15 light
    "chrome_dark": M("steel_blue", 0, 8, black_floor=True),
    "graft": M("plaster_warm", 7, 14),           # v1 stand-in for the reserved pink ramp (v2)
    "raw": M("rust_brown", 2, 7),                # the raw edge of the graft; the hound's gullet
    "patch": M("steel_blue", 4, 8),              # ground of the US patch (C), stamped over
    "bolt_out": M("steel_blue", 13, 15),         # SD_StormBolt: chrome-white ...
    "bolt_core": M("flag_red", 11, 15),          # ... with a red core (BESTIARY §5)
    "hide": M("khaki_olive", 1, 9),              # BESTIARY §6 says 4-10; see HIDE_NOTE
    "hide_dark": M("khaki_olive", 0, 5),
    "belly": M("khaki_olive", 0, 2, black_floor=True),   # black underbelly and muzzle (§10 rule 4)
    "bone": M("plaster_warm", 9, 14),            # teeth, spines
}
# BESTIARY §6 gives the hide as khaki_olive 4-10. The first render with it
# measured body luma 99 against SDSTEL1's 101 (gap 1 at light 112): the hound
# vanished on green steel. The hide is therefore drawn in khaki_olive 1-9 and
# low on the ramp, Reich-dark like the rifleman; the sheet says so.
HIDE_NOTE = "BESTIARY §6 hide khaki_olive 4-10 measured luma 99 vs SDSTEL1 101; drawn in 1-9, darker"
NEW_NO_SHIFT = set(NEW_MATERIALS)               # each keeps the value given here
NEW_FLAT = {"bolt_out", "bolt_core"}            # no contour, no rim: a glow
LEGION_MATERIALS = {"chrome", "chrome_dark", "graft", "raw", "patch"}


def register_materials() -> None:
    """Append the new materials to gen_rig's tables, in place, so its
    renderer knows them. Appending never moves an existing id."""
    for name, mat in NEW_MATERIALS.items():
        if name in rig.MATERIALS:
            continue
        rig.MATERIALS[name] = mat
        rig.MAT_ID[name] = len(rig.MAT_NAMES)
        rig.MAT_NAMES.append(name)
    rig.NO_SHIFT.update(NEW_NO_SHIFT)
    rig.FLAT_MATERIALS.update(NEW_FLAT)


register_materials()

# The US flag shoulder patch (BESTIARY §2.1, Legion accent): 6x5, hard pixels.
# B steel_blue canton, R flag_red, W plaster_warm.
US_PATCH = (
    "BBRRRR",
    "BBWWWW",
    "RRRRRR",
    "WWWWWW",
    "RRRRRR",
)
US_PATCH_COLOURS = {"B": ("steel_blue", 5), "R": ("flag_red", 11), "W": ("plaster_warm", 14)}
PATCH_MIN_PX = 6


# =============================================================== the cells
@dataclass(frozen=True)
class StormCell:
    key: str
    head: str          # "crest" | "mask" | "skull"
    coat: str          # "long" | "short"
    emitter: str       # "cannon" | "coil"
    pauldron: bool
    hunch: float       # degrees, the upper body forward about the waist
    tilt: float        # degrees, the chrome shoulder dragged down (he walks lopsided)
    title: str


STORM_CELLS = (
    StormCell("A", "crest", "long", "cannon", False, 14.0, 6.0,
              "Brief: crested helmet, greatcoat, forearm cannon"),
    StormCell("B", "crest", "long", "coil", False, 14.0, 8.0,
              "As A, a chrome coil on the shoulder"),
    StormCell("C", "crest", "long", "coil", True, 14.0, 8.0,
              "As B, chrome pauldron, US patch, back hose"),
    StormCell("D", "mask", "short", "cannon", False, 9.0, 5.0,
              "Gas mask hosed to the arm, tunic and breeches"),
    StormCell("E", "skull", "long", "cannon", False, 14.0, 6.0,
              "Bare skull, chrome plate on his right half"),
)
STORM = {c.key: c for c in STORM_CELLS}


@dataclass(frozen=True)
class HoundCell:
    key: str
    build: str         # "long" | "hyena" | "mastiff"
    jaw: str           # "flat" | "croc" | "split"
    harness: bool
    spines: bool
    title: str


HOUND_CELLS = (
    HoundCell("A", "long", "flat", False, False, "Brief: long, low, flat head that is mostly jaw"),
    HoundCell("B", "hyena", "flat", False, False, "Hyena: high front, sloping back, withers hump"),
    HoundCell("C", "long", "flat", True, False, "As A, black handler's harness and collar"),
    HoundCell("D", "long", "croc", False, True, "As A, crocodile jaw, bony dorsal spines"),
    HoundCell("E", "mastiff", "split", False, False, "Mastiff: short, deep, split jaw open"),
)
HOUND = {c.key: c for c in HOUND_CELLS}

# What is rendered per cell: (frame, rotation). Frame letters follow the
# BESTIARY layouts: SDHS A walk/idle, G the shot; SDHN A walk/idle, F the bite.
STORM_VIEWS = (("A", 1), ("A", 3), ("A", 7), ("G", 1))
HOUND_VIEWS = (("A", 1), ("A", 2), ("A", 3), ("F", 3))
VIEW_NAMES = {1: "front", 2: "front-left", 3: "its left side", 7: "its right side"}


# ============================================================ stormtrooper
STORM_FEET = dict(foot_l=(3.9, ANKLE_Y, 1.6), foot_r=(-4.3, ANKLE_Y, -1.8))
STORM_BOB = -0.9
RIGHT_SHOULDER = V(-(rig.SHOULDER_X + 0.2), 39.4 + STORM_BOB, -0.4)
CANNON_LEN = 13.0
EMITTER_AIM = {          # elbow offset from the shoulder, cannon direction
    "idle": (V(-1.8, -8.6, 2.0), V(0.10, -0.45, 1.0)),
    "attack": (V(-1.4, -6.4, 5.2), V(0.12, 0.10, 1.0)),
}


def _rifleman_body(cell: StormCell, pose: str) -> tuple[list[rig.Prim], dict]:
    """gen_rig's rifleman with the rifle and his right arm taken away."""
    head_up = cell.hunch * 0.7
    p = rig.Pose("A", "storm", **STORM_FEET, bob=STORM_BOB, carry="free", stride=0.3,
                 head_pitch=head_up, hand_l=(9.6, 27.2, 3.4), hand_r=(-9.0, 27.0, 3.0),
                 rifle_at=((-10.0, 20.0, 4.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), canvas=STORM_CV)
    prims, anchors = rig.build_model(p)
    keep = []
    for q in prims:
        if q.grp == "rifle":
            continue
        if q.grp == "arm" and q.bound()[0][0] < 0:      # his right arm (x < 0)
            continue
        if cell.coat == "short" and q.grp == "skirt":
            continue
        if cell.head == "skull" and q.grp == "helmet":
            continue
        keep.append(q)
    return keep, anchors


def _short_coat(P: list, add) -> None:
    """Tunic to the upper thigh, flared breeches (cell D)."""
    bob = STORM_BOB
    add("skirt", rig.ccone("coat", 0.50, 21.6 + bob, rig.WAIST_Y + bob, 8.0, rig.WAIST_R, kz=0.72))
    for side, foot in ((1, STORM_FEET["foot_l"]), (-1, STORM_FEET["foot_r"])):
        hip = V(side * 3.4, rig.HIP_Y + bob, 0.0)
        knee, _ = rig.two_bone(hip, foot, rig.THIGH, rig.SHIN, V(0, 0, 1))
        mid = hip + (knee - hip) * 0.45
        add("leg_l" if side > 0 else "leg_r",
            rig.ellipsoid("coat_dark", 0.42, tuple(mid + V(side * 0.9, 0, 0)), (3.5, 4.6, 3.2)))


def _head_parts(cell: StormCell, add) -> None:
    bob = STORM_BOB
    if cell.head == "mask":
        add("head", rig.ellipsoid("mask", 0.45, (0, 44.4 + bob, 3.6), (2.7, 2.5, 2.1)))      # snout
        add("head", rig.ellipsoid("void", 0.05, (-1.3, 47.5 + bob, 3.9), (1.05, 0.9, 0.6)))   # lenses
        add("head", rig.ellipsoid("void", 0.05, (1.3, 47.5 + bob, 3.9), (1.05, 0.9, 0.6)))
        add("head", rig.rcone("metal", 0.50, V(-0.6, 43.4 + bob, 5.2), V(-1.4, 41.8 + bob, 7.0), 1.35, 1.2))
    elif cell.head == "skull":
        c = V(0, 46.5 + bob, 1.0)
        add("head", rig.ellipsoid("flesh", 0.60, tuple(c + V(0, 1.6, -0.4)), (3.35, 4.1, 3.5)))   # the dome
        add("head", rig.ellipsoid("graft", 0.55, tuple(c + V(0, 1.6, -0.4)), (3.55, 4.3, 3.7),
                                  clip=[(V(1, 0, 0), 0.25), (V(-1, 0, 0), 0.75)]))                # the seam
        add("head", rig.ellipsoid("chrome", 0.80, tuple(c + V(-0.2, 1.7, -0.4)), (3.6, 4.35, 3.75),
                                  clip=[(V(1, 0, 0), -0.75)]))                                    # the plate


def _emitter(cell: StormCell, pose: str, add) -> np.ndarray:
    """His right arm: the Legion graft. Returns the muzzle point."""
    sh = RIGHT_SHOULDER
    off, d = EMITTER_AIM[pose]
    elbow = sh + off
    d = d / np.linalg.norm(d)
    muzzle = elbow + d * CANNON_LEN
    # the seam: raw edge, then pale flesh where the chrome is sunk into him
    add("arm", rig.ellipsoid("raw", 0.40, tuple(sh + V(0.4, -0.2, 0.0)), (3.0, 3.1, 3.2)))
    add("arm", rig.ellipsoid("graft", 0.60, tuple(sh + V(-0.3, -0.4, 0.0)), (3.0, 2.9, 3.0)))
    if cell.emitter == "coil":
        hub = sh + V(-1.6, 1.0, -0.4)
        add("arm", rig.ellipsoid("chrome", 0.80, tuple(hub), (5.0, 4.6, 4.9)))
        for k in (-1.6, 0.0, 1.6):                     # coil windings round the housing
            add("arm", rig.ellipsoid("chrome_dark", 0.40, tuple(hub + V(-0.2, k * 1.15, 0)), (5.3, 0.5, 5.2)))
        add("arm", rig.rcone("chrome", 0.70, hub + V(-0.6, -3.6, 0.4), elbow, 2.1, 2.0))
    else:
        add("arm", rig.rcone("chrome", 0.74, sh + V(-0.5, -2.0, 0.0), elbow, 2.9, 2.5))
    add("arm", rig.ellipsoid("chrome_dark", 0.45, tuple(elbow), (2.7, 2.7, 2.7)))
    add("arm", rig.rcone("chrome", 0.78, elbow, muzzle, 3.1, 2.3))                 # the cannon
    for t in (0.30, 0.55, 0.80):                                                     # cooling rings
        a = elbow + (muzzle - elbow) * t
        add("arm", rig.rcone("chrome_dark", 0.40, a - d * 0.35, a + d * 0.35, 3.4 - 0.7 * t))
    add("arm", rig.rcone("chrome_dark", 0.30, muzzle - d * 0.6, muzzle + d * 0.4, 2.5))   # muzzle ring
    if cell.pauldron:
        add("arm", rig.ellipsoid("chrome", 0.82, tuple(sh + V(-1.4, 2.9, -0.2)), (5.6, 3.0, 5.2),
                                 clip=[(V(0, -1, 0), -(sh[1] + 0.4))]))
        add("arm", rig.box("patch", 0.5, tuple(sh + V(-6.6, 0.4, 0.2)), (0.5, 2.0, 2.4), tag="patch"))
        add("arm", rig.rcone("chrome_dark", 0.35, V(-1.5, 37.0 + STORM_BOB, -5.6), sh + V(-0.6, 1.0, -3.2), 0.9))
    return muzzle


def storm_model(cell: StormCell, pose: str = "idle") -> list[rig.Prim]:
    """The Stormtrooper in model space (gen_rig's conventions: feet on y=0,
    facing +z, +x the figure's LEFT), hunched and lopsided."""
    P, _ = _rifleman_body(cell, pose)

    def add(grp, prim):
        prim.grp = grp
        P.append(prim)
        return prim

    if cell.coat == "short":
        _short_coat(P, add)
    _head_parts(cell, add)
    muzzle = _emitter(cell, pose, add)
    if cell.head == "mask":                     # the mask breathes through the graft
        start = V(-1.4, 41.8 + STORM_BOB, 7.0)
        mid = V(-5.0, 37.0 + STORM_BOB, 6.0)
        add("arm", rig.rcone("chrome_dark", 0.35, start, mid, 0.75))
        add("arm", rig.rcone("chrome_dark", 0.35, mid, RIGHT_SHOULDER + EMITTER_AIM[pose][0] * 0.6, 0.75))
    if pose == "attack":                        # the bolt leaving the cannon (SD_StormBolt)
        d = EMITTER_AIM[pose][1] / np.linalg.norm(EMITTER_AIM[pose][1])
        add("arm", rig.ellipsoid("bolt_out", 0.6, tuple(muzzle + d * 2.4), (2.9, 2.9, 2.9)))
        add("arm", rig.ellipsoid("bolt_core", 0.7, tuple(muzzle + d * 3.6), (1.5, 1.5, 1.5)))
    waist = V(0, rig.WAIST_Y + STORM_BOB, 0)
    upper = rig.UPPER
    rig.transform(P, {}, upper, rig.rot_x(-cell.hunch), waist)
    rig.transform(P, {}, {"skirt"}, rig.rot_x(-cell.hunch * 0.3), waist)
    rig.transform(P, {}, upper, rig.rot_z(-cell.tilt), waist)
    return P


# =================================================================== hound
@dataclass(frozen=True)
class Build:
    chest: tuple       # ribcage centre
    cage: tuple        # ribcage radii
    pelvis: tuple      # pelvis centre
    haunch: tuple      # haunch radii
    shoulder_y: float
    hip_y: float
    leg: float         # leg thickness factor
    head: tuple        # skull centre
    snout: float       # snout length
    head_s: float      # head size factor
    hump: bool = False


BUILDS = {
    "long": Build((0, 22.0, 6.0), (7.6, 8.0, 12.5), (0, 21.5, -17.0), (3.8, 5.6, 5.6),
                  24.5, 22.0, 1.35, (0, 26.5, 25.0), 13.0, 1.35),
    "hyena": Build((0, 24.0, 5.5), (8.0, 9.2, 11.5), (0, 18.5, -14.0), (3.5, 5.0, 5.0),
                   28.5, 18.5, 1.35, (0, 29.0, 22.5), 11.5, 1.4, hump=True),
    "mastiff": Build((0, 21.5, 5.0), (9.2, 9.6, 10.5), (0, 21.5, -11.5), (4.6, 6.4, 6.0),
                     24.5, 22.0, 1.7, (0, 26.0, 20.5), 10.0, 1.6),
}
HOUND_POSES = {          # jaw open (deg), head pitch down (deg), front paws +z, hind paws +z
    "idle": (0.0, 0.0, 0.0, 0.0),
    "bite": (34.0, 10.0, 5.0, -3.0),
}
FRONT_UPPER, FRONT_LOWER = 11.0, 10.5
HIND_FEMUR, HIND_TIBIA = 9.6, 9.6
HOCK_UP, HOCK_BACK = 6.2, 2.2       # metatarsus: the hock sits this far above and behind the paw
PAW_Y = 1.25


def three_bone_hind(hip, paw, femur: float = HIND_FEMUR, tibia: float = HIND_TIBIA):
    """A digitigrade hind leg: hip -> knee (forward) -> hock (back) -> paw.
    gen_rig has two-bone IK only; the metatarsus is held at a fixed offset
    from the paw and the two upper bones are solved towards the hock."""
    hip, paw = np.asarray(hip, float), np.asarray(paw, float)
    hock = paw + V(0, HOCK_UP, -HOCK_BACK)
    knee, hock_end = rig.two_bone(hip, hock, femur, tibia, V(0, 0, 1))
    return knee, hock_end, paw


def hound_model(cell: HoundCell, pose: str = "idle") -> list[rig.Prim]:
    """The hound in gen_rig's model space: paws on y=0, facing +z, +x its LEFT."""
    b = BUILDS[cell.build]
    jaw_open, pitch, front_dz, hind_dz = HOUND_POSES[pose]
    if cell.jaw == "split" and pose == "idle":
        jaw_open = 16.0
    P: list[rig.Prim] = []

    def add(grp, prim):
        prim.grp = grp
        P.append(prim)
        return prim

    cx, cy, cz = b.chest
    rx, ry, rz = b.cage
    px, py, pz = b.pelvis
    L = b.leg
    # ------------------------------------------------------------ the body
    add("body", rig.ellipsoid("hide", 0.32, b.chest, b.cage))
    for i in range(7):                              # ribs: hoops the banded light catches
        z = cz + rz * (-0.50 + 0.15 * i)
        s = float(np.sqrt(max(1 - ((z - cz) / rz) ** 2, 0.0)))
        add("body", rig.ellipsoid("hide", 0.46, (cx, cy, z), (rx * s + 0.45, ry * s + 0.45, 0.62),
                                  clip=[(V(0, -1, 0), -(cy - ry * 0.45))]))
    add("body", rig.ellipsoid("belly", 0.30, (cx, cy - ry * 0.52, cz - 1.5), (rx * 0.82, ry * 0.52, rz * 0.82)))
    add("body", rig.rcone("hide", 0.30, V(0, cy + 0.8, cz - rz * 0.45), V(0, py + 0.8, pz + 2.5), 5.0 * L ** 0.5,
                          4.4 * L ** 0.5))                                                # the tucked loin
    add("body", rig.rcone("belly", 0.25, V(0, cy - ry * 0.45, cz - rz * 0.4), V(0, py - 3.2, pz + 3.0),
                          3.4 * L ** 0.5, 2.4 * L ** 0.5))
    for side in (1, -1):
        add("body", rig.ellipsoid("hide", 0.34, (side * 2.9 * L ** 0.5, py, pz), b.haunch))
        add("body", rig.ellipsoid("hide", 0.37, (side * (rx * 0.62), b.shoulder_y - 2.5, cz + rz * 0.45),
                                  (2.8 * L, 5.4, 4.0)))
    for i in range(9):                              # vertebrae along the top line
        t = i / 8
        p = V(0, (py + b.haunch[1] * 0.75) * (1 - t) + (cy + ry * 0.92) * t, (pz) * (1 - t) + (cz + rz * 0.3) * t)
        add("body", rig.ellipsoid("hide_dark", 0.37, tuple(p), (1.0, 0.9, 1.3)))
        if cell.spines:
            add("body", rig.rcone("bone", 0.55, p, p + V(0, 3.4 - 1.2 * abs(t - 0.6), -1.2), 0.85, 0.2))
    if b.hump:
        add("body", rig.ellipsoid("hide", 0.38, (0, b.shoulder_y + 1.0, cz + rz * 0.35), (4.4, 3.8, 6.2)))
    add("body", rig.rcone("hide_dark", 0.27, V(0, py + 1.2, pz - 4.0), V(0, py - 5.0, pz - 11.5), 1.4, 0.45))  # tail
    # ------------------------------------------------------------ the legs
    for side in (1, -1):
        grp = "leg_l" if side > 0 else "leg_r"
        sx = side * rx * 0.62
        sh = V(sx, b.shoulder_y - 4.0, cz + rz * 0.48)
        paw = V(sx, PAW_Y, cz + rz * 0.62 + front_dz)
        elbow, wrist = rig.two_bone(sh, paw + V(0, 1.4, 0), FRONT_UPPER, FRONT_LOWER, V(0, 0, -1))
        add(grp, rig.rcone("hide", 0.34, sh, elbow, 2.4 * L, 1.7 * L))
        add(grp, rig.rcone("hide", 0.32, elbow, wrist, 1.6 * L, 1.15 * L))
        add(grp, rig.ellipsoid("belly", 0.35, tuple(paw + V(0, 0.0, 0.9)), (1.6 * L, 1.15, 2.3 * L)))
        hx = side * 2.9 * L ** 0.5
        hip = V(hx, py - 1.0, pz)
        hpaw = V(hx, PAW_Y, pz - 2.5 + hind_dz)
        knee, hock, hpaw = three_bone_hind(hip, hpaw)
        add(grp, rig.rcone("hide", 0.32, hip, knee, 3.0 * L, 1.9 * L))
        add(grp, rig.rcone("hide", 0.30, knee, hock, 1.8 * L, 1.15 * L))
        add(grp, rig.rcone("hide_dark", 0.27, hock, hpaw + V(0, 0.8, 0), 1.1 * L, 0.95 * L))
        add(grp, rig.ellipsoid("belly", 0.35, tuple(hpaw + V(0, 0.0, 1.0)), (1.5 * L, 1.1, 2.2 * L)))
    # ------------------------------------------------------------ the head
    hx0, hy, hz = b.head
    s = b.head_s
    snout = b.snout * (1.35 if cell.jaw == "croc" else 1.0)
    neck_root = V(0, cy + ry * 0.35, cz + rz * 0.6)
    add("neck", rig.rcone("hide", 0.34, neck_root, V(0, hy - 0.6, hz - 2.4 * s), 4.6 * L ** 0.5, 3.4 * s))
    add("head", rig.ellipsoid("hide", 0.40, (0, hy + 1.0, hz), (4.4 * s, 2.5 * s, 4.8 * s)))       # flat skull
    add("head", rig.rcone("hide", 0.38, V(0, hy + 0.6, hz + 1.0), V(0, hy + 0.2, hz + snout), 3.5 * s, 2.3 * s))
    add("head", rig.rcone("belly", 0.30, V(0, hy + 0.3, hz + snout * 0.55), V(0, hy + 0.1, hz + snout + 0.2),
                          2.95 * s, 2.4 * s))                                                    # black muzzle
    teeth_n = 6 if cell.jaw == "croc" else 4
    for side in (1, -1):
        for i in range(teeth_n):
            z = hz + 3.0 * s + i * (snout - 4.0 * s) / max(teeth_n - 1, 1)
            add("head", rig.ellipsoid("bone", 0.6, (side * 1.9 * s, hy - 1.2 * s, z), (0.45, 1.0 * s, 0.5)))
    jaw = [
        add("jaw", rig.rcone("belly", 0.32, V(0, hy - 1.9 * s, hz + 0.5), V(0, hy - 1.6 * s, hz + snout - 0.8),
                             2.6 * s, 1.8 * s)),
    ]
    for side in (1, -1):
        for i in range(teeth_n - 1):
            z = hz + 4.0 * s + i * (snout - 5.5 * s) / max(teeth_n - 2, 1)
            jaw.append(add("jaw", rig.ellipsoid("bone", 0.6, (side * 1.6 * s, hy - 0.6 * s, z), (0.4, 0.9 * s, 0.45))))
    if jaw_open:
        add("head", rig.ellipsoid("raw", 0.30, (0, hy - 1.3 * s, hz + snout * 0.45), (1.8 * s, 1.2 * s, snout * 0.4)))
        hinge = V(0, hy - 1.0 * s, hz - 1.2 * s)
        rig.transform(P, {}, {"jaw"}, rig.rot_x(-jaw_open), hinge)
    if cell.harness:
        for z in (cz + rz * 0.30, cz - rz * 0.25):
            s2 = float(np.sqrt(max(1 - ((z - cz) / rz) ** 2, 0.0)))
            add("body", rig.ellipsoid("leather", 0.45, (cx, cy, z), (rx * s2 + 0.9, ry * s2 + 0.9, 1.05)))
        add("body", rig.rcone("leather", 0.45, V(0, cy + ry * 0.95, cz + rz * 0.32), V(0, cy + ry * 0.9, cz - rz * 0.3),
                              1.1))
        mid = neck_root + (V(0, hy - 0.6, hz - 2.4 * s) - neck_root) * 0.55
        add("neck", rig.ellipsoid("leather", 0.45, tuple(mid), (4.6 * L ** 0.5, 4.6 * L ** 0.5, 1.6)))
        add("neck", rig.ellipsoid("metal", 0.65, tuple(mid + V(0, -4.2 * L ** 0.5, 0.6)), (0.9, 0.9, 0.7)))
    if pitch:
        rig.transform(P, {}, {"head", "jaw"}, rig.rot_x(-pitch), V(0, hy - 0.6, hz - 2.4 * s))
    return P


# ================================================================== render
def stamp_patch(rgba: np.ndarray, pid: np.ndarray, prims: list[rig.Prim], rotation: int) -> bool:
    """The US patch on the pauldron's visible centre when its outer face
    (the figure's right, model -x) is not turned away. Returns whether."""
    ids = [i for i, p in enumerate(prims) if p.tag == "patch"]
    if not ids:
        return False
    vis = np.isin(pid, ids)
    if vis.sum() < PATCH_MIN_PX:
        return False
    out = rig.yaw_matrix(rotation) @ (prims[ids[0]].xm @ V(-1, 0, 0))
    if out[2] < -0.05:
        return False
    h, w = pid.shape
    ys, xs = np.nonzero(vis)
    x0 = min(max(int(round(xs.mean() - 3.0)), 0), w - len(US_PATCH[0]))
    y0 = min(max(int(round(ys.mean() - 2.0)), 0), h - len(US_PATCH))
    for j, row in enumerate(US_PATCH):
        for i, ch in enumerate(row):
            ramp, k = US_PATCH_COLOURS[ch]
            rgba[y0 + j, x0 + i] = (*artlib.ramp(ramp)[k], 255)
    return True


def render_prims(prims: list[rig.Prim], rotation: int, cv: Canvas, seed: int = SEED):
    """One sprite: (RGBA, material-id map at 1x)."""
    buf = rig.raymarch(prims, rotation, cv, seed)
    mat, val, dep, pid = rig.reduce(buf, prims)
    rgba = rig.to_rgba(mat, val, dep)
    if any(p.tag == "armband" for p in prims):
        rig.stamp_symbol(rgba, pid, prims, rotation)
    stamp_patch(rgba, pid, prims, rotation)
    a = rgba[..., 3] > 0
    if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any():
        raise ValueError(f"rotation {rotation} touches the {cv.w}x{cv.h} canvas edge")
    return rgba, mat


def render_storm(key: str, frame: str, rotation: int, seed: int = SEED):
    return render_prims(storm_model(STORM[key], "attack" if frame == "G" else "idle"), rotation, STORM_CV, seed)


def render_hound(key: str, frame: str, rotation: int, seed: int = SEED):
    return render_prims(hound_model(HOUND[key], "bite" if frame == "F" else "idle"), rotation, HOUND_CV, seed)


def legion_fraction(mat: np.ndarray) -> float:
    """Share of the opaque pixels drawn in Legion material (BESTIARY §5's <= 25 %)."""
    ids = [rig.MAT_ID[m] for m in LEGION_MATERIALS] + [rig.MAT_ID[m] for m in NEW_FLAT]
    op = mat >= 0
    return float(np.isin(mat, ids).sum() / max(op.sum(), 1))


def belly_black_share(rgba: np.ndarray) -> float:
    """Share of the lowest opaque pixel of each column that is near-black:
    BESTIARY §10 rule 4, the hound's bottom edge must read over SDFLR1."""
    a = rgba[..., 3] > 0
    cols = np.nonzero(a.any(0))[0]
    dark = 0
    for x in cols:
        y = np.nonzero(a[:, x])[0].max()
        dark += flat.luma(rgba[y, x, :3][None])[0] < 40
    return float(dark / max(len(cols), 1))


def lump(sprite: str, key: str, frame: str, rot: int) -> str:
    return f"{sprite}_{key}_{frame}{rot}"


def grab(cv: Canvas) -> tuple[int, int]:
    return cv.cx, cv.foot_row - rig.FEET_SINK


def save(rgba: np.ndarray, path: Path, cv: Canvas) -> None:
    rig.save_sprite(rgba, path, cv)


def measure(rgba: np.ndarray) -> dict:
    return rig.measure(rgba)


def build_all(seed: int = SEED) -> dict:
    out = {"storm": {}, "hound": {}, "metrics": {"storm": {}, "hound": {}}}
    for c in STORM_CELLS:
        m = {}
        for frame, rot in STORM_VIEWS:
            rgba, mat = render_storm(c.key, frame, rot, seed)
            save(rgba, STORM_DIR / f"{lump(STORM_SPRITE, c.key, frame, rot)}.png", STORM_CV)
            out["storm"][(c.key, frame, rot)] = rgba
            m[f"legion_{frame}{rot}"] = round(legion_fraction(mat), 3)
            print(lump(STORM_SPRITE, c.key, frame, rot), flush=True)
        m.update(measure(out["storm"][(c.key, "A", 1)]))
        m["legion_max"] = max(v for k, v in m.items() if k.startswith("legion_A"))
        out["metrics"]["storm"][c.key] = m
    for c in HOUND_CELLS:
        m = {}
        for frame, rot in HOUND_VIEWS:
            rgba, _ = render_hound(c.key, frame, rot, seed)
            save(rgba, HOUND_DIR / f"{lump(HOUND_SPRITE, c.key, frame, rot)}.png", HOUND_CV)
            out["hound"][(c.key, frame, rot)] = rgba
            print(lump(HOUND_SPRITE, c.key, frame, rot), flush=True)
        side = out["hound"][(c.key, "A", 3)]
        m.update(measure(side))
        m["front_height_px"] = measure(out["hound"][(c.key, "A", 1)])["height_px"]
        m["black_bottom_edge"] = round(belly_black_share(side), 2)
        out["metrics"]["hound"][c.key] = m
    for name, d in (("storm", STORM_DIR), ("hound", HOUND_DIR)):
        (d / "metrics.json").write_text(json.dumps(out["metrics"][name], indent=2) + "\n", encoding="utf-8")
    return out


def load_all() -> dict:
    out = {"storm": {}, "hound": {}, "metrics": {}}
    for name, sprite, cells, views, d in (("storm", STORM_SPRITE, STORM_CELLS, STORM_VIEWS, STORM_DIR),
                                          ("hound", HOUND_SPRITE, HOUND_CELLS, HOUND_VIEWS, HOUND_DIR)):
        for c in cells:
            for frame, rot in views:
                with Image.open(d / f"{lump(sprite, c.key, frame, rot)}.png") as im:
                    out[name][(c.key, frame, rot)] = np.asarray(im.convert("RGBA")).copy()
        out["metrics"][name] = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    return out


# ================================================================== scenes
def floor_rgb(name: str) -> np.ndarray:
    if name == "SDFLR1":
        with Image.open(SDFLR1) as im:
            return np.asarray(im.convert("RGB"), dtype=np.uint8)
    return flat.host_rgb(name)


def lineup(figures, wall: str, light: int, width: int, floor: str = "SDFLR2") -> np.ndarray:
    """gen_rig.lineup with a choice of floor flat (the hound is judged over
    SDFLR1's lane line too, BESTIARY §10 rule 4)."""
    wall_h, floor_h = flat.WALL_H, flat.FLOOR_H
    w_rgb = flat.tile_to(flat.host_rgb(wall), width, wall_h)
    fl = flat.tile_to(floor_rgb(floor), width, floor_h * 3)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((width, floor_h), Image.Resampling.NEAREST))
    canvas = np.concatenate([w_rgb, fl], axis=0).copy()
    base = flat.FLOOR_LINE - rig.FEET_SINK
    slot = width / len(figures)
    for i, (spr, ox, oy) in enumerate(figures):
        x0 = int(round(slot * (i + 0.5))) - ox
        y0 = base - oy
        a = spr[..., 3] > 0
        ys, xs = np.nonzero(a)
        ys2, xs2 = ys + y0, xs + x0
        keep = (ys2 >= 0) & (ys2 < canvas.shape[0]) & (xs2 >= 0) & (xs2 < width)
        canvas[ys2[keep], xs2[keep]] = spr[ys[keep], xs[keep], :3]
    return flat.lit(canvas, light)


def rifleman() -> tuple[np.ndarray, int, int] | None:
    """The approved-draft rifleman (D38) from gen_rig's own output, for scale."""
    path = RIFLEMAN_DIR / "SDRRA1.png"
    if not path.is_file():
        return None
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGBA")).copy()
    return arr, *rig.grab_offsets(rig.STAND)


HOUND_SCENES = (*flat.SCENES, ("S6", "SDCONC1", 128, "corridor over the SDFLR1 lane line"))


# =================================================================== sheet
STORM_RECOMMENDED = "B"
HOUND_RECOMMENDED = "D"
# Written after looking at the sweep once (PIPELINE stage 2).
STORM_VERDICT = [
    "RECOMMENDED: B. The chrome coil on his right shoulder is the silhouette BESTIARY 5 asks for: one "
    "shoulder a bright blob, the other a dark slope, the only unbalanced humanoid in the bestiary. A's "
    "forearm cannon alone is a thin pale stick that at 1x reads as a rifleman holding something; C adds "
    "a pauldron, a US patch and a hose and goes over the 25 % rule (27 % on his right side) for detail "
    "that is invisible at 1x; E's chrome skull plate is striking up close but puts him at 33 % and makes "
    "his head the brightest thing on him, which fights the shoulder tell.",
    "THE HONEST PROBLEM: at 1x, B still reads as a rifleman with a silver arm. Same crested helmet, same "
    "greatcoat, same value (body luma 70-74 against the rifleman's 63-75). D is the cell that separates "
    "best from the rifleman at range: the tunic shows his legs and the gas mask changes the head, so the "
    "two Reich humanoids stop sharing a silhouette. Suggestion if you want him further from the rifleman: "
    "B's coil on D's body (tunic, breeches, gas mask). It is a combination, not a new cell: ask for it.",
    "MEASURED. B's Legion share is 17 % from the front and 26 % from his right side: half a point over the "
    "rule, fixed by trimming the coil housing about 10 % in the next round. Worst value gap 15 on SDSTEL1 "
    "at light 112, the rifleman's own range. Palette v1 has no pink ramp (v2 reserves it), so the 'pink "
    "flesh at the seam' is plaster_warm with a rust_brown raw edge; at 1x it is a pale pixel or two. "
    "The armband stays on his Reich (left) arm; BESTIARY 5 does not mention it, and it is the faction tell.",
]
HOUND_VERDICT = [
    "RECOMMENDED: D. The crocodile jaw and the bony dorsal spines are what stop him being a hairless "
    "greyhound: A, the brief taken literally, reads as an Earth dog, which BESTIARY 6 says he is not. The "
    "spines break the top line of the horizontal bar, so he is named at range even in the dark. B (hyena) "
    "and E (mastiff) are the most alien builds; B's sloped back with D's head and spines is a valid "
    "combination. C's harness ties him to the Reich without insignia but adds nothing at 1x.",
    "MEASURED. Profile 33 px tall (rule: under 40) and 58-75 px long, a horizontal bar beside the "
    "Freedoom placeholder's vertical worm. Black bottom edge on 75-83 % of the columns, so the belly line "
    "reads over SDFLR1's lane (S6, BESTIARY 10 rule 4). Worst gap 13-15 on SDSTEL1 at 112: the 'caution' "
    "of BESTIARY 10, same as the rifleman.",
    "A DEVIATION, STATED. BESTIARY 6 gives the hide as khaki_olive 4-10. The first render in that range "
    "measured body luma 99 against SDSTEL1's 101: a gap of 1, the hound vanished on green steel. Every "
    "cell here uses khaki_olive 1-9, low on the ramp, Reich-dark like the rifleman (body luma 70-75). No "
    "red anywhere, as BESTIARY 6 asks; teeth and spines are plaster_warm, the gullet rust_brown.",
    "FREEDOOM, LOOKED AT. BESTIARY 5 and 6 left it NOT VERIFIED: TROO is a tentacled serpentine creature, "
    "not a humanoid, and SARG is a worm, not a quadruped. Neither is a base for these two; both are drawn "
    "from scratch, and the placeholders are shown for scale only.",
]
RIG_VERDICT = [
    "THE STORMTROOPER: YES, AS IS. He is the rifleman's own rig model with the rifle and his right arm "
    "taken away and the graft added, so the 53 lumps of BESTIARY 5 are the rifleman's pipeline with new "
    "poses. Two small things would make it clean rather than clever: gen_rig tags no limb by side (the "
    "right arm is found here by its position, x < 0), and its material table is closed (the new "
    "materials are appended to it at import time). Both are a few lines in gen_rig.py, reported, not done.",
    "THE HOUND: THE RENDERER YES, THE SKELETON NO. Everything that draws (primitives, sphere tracer, banded "
    "light, majority vote, contour and rim, palette, lineup on MAP01) served a quadruped unchanged. What a "
    "quadruped needs and the rig does not have: (1) a skeleton with a hierarchy: a spine chain pelvis-chest-"
    "neck-head that bends and carries the legs; gen_rig rotates groups about one pivot each and has no "
    "parent-child bones; (2) a three-bone leg: the hind leg is digitigrade (hip, knee, hock, paw); gen_rig "
    "solves two bones only, and this sweep holds the metatarsus at a fixed angle, which is fine standing "
    "and wrong in a gallop; (3) a quadruped pose: four paw targets with gait phase, spine flex and body "
    "pitch per frame, where gen_rig's Pose is two feet and a rifle; (4) its own canvas and falls: gen_rig's "
    "canvases are a standing man's and its death rolls a biped to his left, a hound falls on its side "
    "along its length; (5) a generic render(prims, rotation, canvas): gen_rig's render() is wired to the "
    "rifleman, gen_storm.py carries its own.",
    "AND ONE SAVING. The hound has no insignia and is symmetric, so Doom's mirrored rotation pairs (5 "
    "drawings per frame, BESTIARY 6's count of 46) are valid for him; gen_rig always renders all 8, which "
    "the rifleman and the Stormtrooper need (their armband) and the hound does not. A mirror mode saves "
    "about a third of his lumps.",
]
CEO_ASK = [
    "Stormtrooper: approve B (recommended), or B's coil on D's tunic-and-mask body if you want him further "
    "from the rifleman at range. Then the full frame set is drawn on the rig (53 lumps and the bolt), with "
    "the coil trimmed under the 25 % rule, for your gate.",
    "Hound: approve D (recommended), or name another cell or combination (D's head and spines on B's "
    "hyena build). Before the 46 lumps, the rig needs the quadruped skeleton of section 8: that is a "
    "change to gen_rig.py, which this sweep did not touch.",
    "One deviation to ratify: the hound's hide in khaki_olive 1-9 (darker) instead of BESTIARY 6's 4-10, "
    "which measured invisible on green steel. Recommendation: ratify; mod-engineer updates BESTIARY 6.",
]


def _sil_tile(rgba: np.ndarray) -> str:
    sil = flat.silhouette(rgba)
    sil_rgb = np.where(sil[..., None], 0, 235).astype(np.uint8).repeat(3, -1)
    return rig.tile(rig.png_uri(sil_rgb), sil_rgb.shape[1], sil_rgb.shape[0], 4, "16 px")


def _cells_section(name, sprite, cells, views, sprites, metrics, cv, recommended, extra_cols):
    out = []
    for c in cells:
        m = metrics[c.key]
        rec = c.key == recommended
        tiles = []
        for frame, rot in views:
            label = f"{sprite}{frame}{rot}"
            sub = VIEW_NAMES.get(rot, "") if frame == "A" else ("the shot" if name == "storm" else "the bite")
            tiles.append(rig.sprite_tile(sprites[(c.key, frame, rot)], 3, label, sub))
        tiles.append(_sil_tile(sprites[(c.key, "A", 1 if name == "storm" else 3)]))
        facts = " · ".join(f"{k} {v}" for k, v in extra_cols(m))
        head = f'<h3>{c.key} · {html.escape(c.title)}</h3>'
        tag = '<span class="tag">recommended</span>' if rec else ""
        out.append(f'<div class="card{" rec" if rec else ""}">{tag}{head}'
                   f'<p class="desc">{html.escape(facts)}</p>'
                   f'<div class="strip">{"".join(tiles)}</div></div>')
    return '<div class="cards">' + "".join(out) + "</div>"


def _lineups(figs, labels, scenes, out_dir: Path, prefix: str, width_per: int) -> str:
    body = ""
    for key, wall, light, what in scenes:
        floor = "SDFLR1" if key == "S6" else "SDFLR2"
        sc = lineup(figs, wall, light, width_per * len(figs), floor)
        Image.fromarray(sc, "RGB").save(out_dir / f"{prefix}_{key}.png", optimize=True)
        body += '<div class="strip">' + rig.tile(rig.png_uri(sc), sc.shape[1], sc.shape[0], 1,
                                                 f"{key} 1x: {wall} at light {light}", what) \
            + rig.tile(rig.png_uri(sc), sc.shape[1], sc.shape[0], 2, f"{key} 2x, for the eye") + "</div>"
    far = flat.far(lineup(figs, "SDSTEL1", 112, width_per * len(figs)))
    body += '<div class="strip">' + rig.tile(rig.png_uri(far), far.shape[1], far.shape[0], 5,
                                             "game distance, S3 (worst case), /4") + "</div>"
    body += "<p class=\"lead\">Left to right: " + html.escape(" · ".join(labels)) + \
            ". Each sprite stands by its own offsets, as the engine places it.</p>"
    return body


def build_sheet(data: dict, stamp: str, out_dir: Path = PREVIEW_DIR) -> Path:
    S = []
    st, hd, met = data["storm"], data["hound"], data["metrics"]
    names = {"crest": "crested helmet (the rifleman's)", "mask": "crested helmet + gas mask",
             "skull": "bare skull, chrome plate", "long": "greatcoat", "short": "tunic, breeches",
             "cannon": "forearm cannon", "coil": "shoulder coil + cannon"}
    rows = [[c.key, names[c.head], names[c.coat], names[c.emitter],
             "pauldron, US patch, hose" if c.pauldron else ("mask hose" if c.head == "mask" else "-"),
             f"{c.hunch:.0f} / {c.tilt:.0f}"] for c in STORM_CELLS]
    body = sheetlib.table(["cell", "head", "coat", "his right arm", "extra", "hunch / tilt deg"], rows, 99)
    S.append(("1 · Stormtrooper (SDHS): the five cells",
              "BESTIARY §5: a Reich body with Legion hardware grafted in; the only actor that wears both "
              "palettes, and only if the Legion material stays on one limb (at most 25 % of the body) and the "
              "body mass stays Reich-dark. The Reich half is the rifleman's own rig model (D38): the rifle and "
              "his right arm are removed and the graft is put in their place.", body))

    def storm_cols(m):
        return [("h x w", f"{m['height_px']} x {m['width_px']} px"), ("body luma", m["body_luma"]),
                ("Legion share front/left/right", f"{m['legion_A1']:.0%} / {m['legion_A3']:.0%} / {m['legion_A7']:.0%}"),
                ("worst gap", m["worst_gap"])]
    S.append(("2 · Stormtrooper cells at 3x",
              "Rotation 1 (front), 3 (his left: the Reich side, armband), 7 (his right: the chrome side), "
              "and G1, the shot leaving the cannon (SD_StormBolt: chrome-white, red core). Then the 16-px "
              "black silhouette (ART-BIBLE §6.4). Legion share is the fraction of opaque pixels in chrome, "
              "graft or patch material; the rule is 25 %.",
              _cells_section("storm", STORM_SPRITE, STORM_CELLS, STORM_VIEWS, st, met["storm"], STORM_CV,
                             STORM_RECOMMENDED, storm_cols)))

    figs = [(st[(c.key, "A", 1)], *grab(STORM_CV)) for c in STORM_CELLS]
    labels = [f"SDHS {c.key}" for c in STORM_CELLS]
    troo = rig.freedoom_sprite("TROOA1")
    if troo:
        figs.append(troo)
        labels.append("TROOA1 (Freedoom, today's placeholder)")
    rr = rifleman()
    if rr:
        figs.append(rr)
        labels.append("SDRRA1 (the rifleman rig, D38: must not read the same)")
    S.append(("3 · Stormtrooper at 1x on MAP01's walls, beside the placeholder and the rifleman",
              "The four scenes of the rifleman's sweep: corridor, hangar dado, the fuel bay at light 112 (worst "
              "case), crate cover. Light is gen_enemy.py's stand-in (RGB x L/224, re-quantised), NOT VERIFIED "
              "against GZDoom.", _lineups(figs, labels, flat.SCENES, STORM_DIR, "lineup", 64)))

    rows = [[c.key, c.build, {"flat": "flat, mostly jaw", "croc": "long crocodile jaw",
                              "split": "split, open"}[c.jaw],
             "harness and collar" if c.harness else ("dorsal spines" if c.spines else "-")] for c in HOUND_CELLS]
    body = sheetlib.table(["cell", "build", "head", "extra"], rows, 99)
    S.append(("4 · Reich hound (SDHN): the five cells",
              "BESTIARY §6: a low, long quadruped the size of a large dog, hairless olive hide over visible "
              "ribs, a flat head that is mostly jaw, no eyes, spine low. khaki_olive 4-10 hide, black "
              "underbelly, muzzle and claws, no red at all (no insignia: a dog wears no armband). Built here "
              "from the rig's primitives on a quadruped skeleton of its own.", body))

    def hound_cols(m):
        return [("profile h x w", f"{m['height_px']} x {m['width_px']} px"),
                ("front h", f"{m['front_height_px']} px"), ("body luma", m["body_luma"]),
                ("worst gap", m["worst_gap"]), ("black bottom edge", f"{m['black_bottom_edge']:.0%}")]
    S.append(("5 · Hound cells at 3x",
              "Rotation 1 (front), 2 (three-quarter), 3 (profile: the horizontal bar), and F3, the bite. "
              "Then the 16-px silhouette of the profile. 'Black bottom edge' is the share of columns whose "
              "lowest pixel is near-black (BESTIARY §10 rule 4: the bottom edge must read over SDFLR1's lane).",
              _cells_section("hound", HOUND_SPRITE, HOUND_CELLS, HOUND_VIEWS, hd, met["hound"], HOUND_CV,
                             HOUND_RECOMMENDED, hound_cols)))

    figs = [(hd[(c.key, "A", 3)], *grab(HOUND_CV)) for c in HOUND_CELLS]
    labels = [f"SDHN {c.key} (profile)" for c in HOUND_CELLS]
    sarg = rig.freedoom_sprite("SARGA3A7")
    if sarg:
        figs.append(sarg)
        labels.append("SARGA3A7 (Freedoom, today's placeholder, its profile)")
    if rr:
        figs.append(rr)
        labels.append("SDRRA1 (the rifleman, for scale)")
    body = _lineups(figs, labels, HOUND_SCENES, HOUND_DIR, "lineup", 96)
    figs1 = [(hd[(c.key, "A", 1)], *grab(HOUND_CV)) for c in HOUND_CELLS]
    sarg1 = rig.freedoom_sprite("SARGA1")
    if sarg1:
        figs1.append(sarg1)
    sc = lineup(figs1, "SDCONC1", 128, 64 * len(figs1), "SDFLR1")
    body += '<div class="strip">' + rig.tile(rig.png_uri(sc), sc.shape[1], sc.shape[0], 1, "front views, 1x",
                                             "S6 corridor, SDFLR1 floor") \
        + rig.tile(rig.png_uri(sc), sc.shape[1], sc.shape[0], 2, "front views, 2x",
                   "cells A-E, then SARGA1") + "</div>"
    S.append(("6 · Hound at 1x on MAP01's walls, beside the placeholder",
              "The same four scenes plus S6, the corridor over SDFLR1's yellow lane line (BESTIARY §10 rule 4). "
              "Light stand-in NOT VERIFIED against GZDoom.", body))

    rows = []
    for c in STORM_CELLS:
        m = met["storm"][c.key]
        rows.append([f"SDHS {c.key}", f"{m['height_px']} x {m['width_px']}", m["body_luma"], m["gap_S1"],
                     m["gap_S2"], m["gap_S3"], m["gap_S4"], f"{m['legion_max']:.0%}"])
    for c in HOUND_CELLS:
        m = met["hound"][c.key]
        rows.append([f"SDHN {c.key}", f"{m['height_px']} x {m['width_px']}", m["body_luma"], m["gap_S1"],
                     m["gap_S2"], m["gap_S3"], m["gap_S4"], f"bottom {m['black_bottom_edge']:.0%}"])
    body = sheetlib.table(["cell", "h x w px", "body luma", "gap S1", "gap S2", "gap S3", "gap S4",
                           "Legion max / black edge"], rows)
    body += ("<p class=\"lead\">Body luma: mean over opaque pixels (Stormtrooper front, hound profile). Gap: "
             "|body - wall| under the scene's light (gen_rig.measure). The rifleman rig measured 63-75 and a "
             "worst gap of 13-19 on S3. Walls: SDCONC1 about 147, SDSTEL1 101.</p>")
    S.append(("7 · Numbers", "", body))

    body = '<div class="verdict">'
    for title, paras in (("Stormtrooper", STORM_VERDICT), ("Hound", HOUND_VERDICT),
                         ("The rig and the quadruped", RIG_VERDICT)):
        body += f"<h3>{html.escape(title)}</h3>" + "".join(f"<p>{html.escape(v)}</p>" for v in paras)
    body += "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in CEO_ASK) \
            + "</ol></div>"
    S.append(("8 · Recommendation, the rig, and what you decide", "", body))

    intro = ("D35: the Hybrid Stormtrooper (BESTIARY §5) and the Reich hound (§6), drawn on the 3D rig of the "
             "Reich rifleman (D38). One decision per enemy before ~100 images: what it looks like. Five cells "
             "each, a few rotations and one attack frame, every cell at 1x beside its Freedoom placeholder on "
             f"MAP01's walls. Palette v1 only, seed {SEED}, no system fonts. Built by "
             "<code>tools/art/gen_storm.py</code>, which imports <code>gen_rig.py</code> and does not change "
             "it. Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_storm.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic, no "
              "system fonts. Freedoom sprites shown for scale only, from freedoom2.wad 0.13.0, BSD-3-Clause "
              "(© the Freedoom contributors), not used as a source.")
    path = out_dir / f"{stamp}_F5_storm-hound-sweep.html"
    sheetlib.write_sheet(path, lang="en", title="Stormtrooper and Reich hound — design sweeps (F5, D35)",
                         subtitle="SDHS · SDHN · 5 + 5 cells · draft for the CEO's gate",
                         intro=intro, sections=S, footer=footer)
    css = rig.EXTRA_CSS + ".cards{display:flex;flex-direction:column;gap:14px}"
    text = path.read_text(encoding="utf-8").replace("</style>", css + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    ap.add_argument("--sheet-only", action="store_true",
                    help="rebuild the sheet from the sprites already in work/art/enemies/{storm,hound}/")
    ap.add_argument("--no-sheet", action="store_true", help="sprites only")
    args = ap.parse_args()
    STORM_DIR.mkdir(parents=True, exist_ok=True)
    HOUND_DIR.mkdir(parents=True, exist_ok=True)
    data = load_all() if args.sheet_only else build_all()
    for name in ("storm", "hound"):
        for k, m in data["metrics"][name].items():
            print(name, k, m)
    if args.no_sheet:
        return
    path = build_sheet(data, args.stamp)
    print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
