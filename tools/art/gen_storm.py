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
bone, the bolt) are registered on a COPY of gen_rig's material table
(rig_core.register_material: append-only), so the rifleman's material ids
never move and gen_rig's own table is not touched (tests/test_gen_storm.py
checks both). Since the rig_core refactor (2026-10-13) the Stormtrooper's
right arm is taken away by its label (limb "arm", side RIGHT), not by its
position, and the sprites go through core.render_layers; the refactor left
every PNG this script writes byte-identical. Palette v1 has no pink ramp yet (BESTIARY §2.1 reserves it for v2):
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
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
from PIL import Image

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402
import gen_rig as rig  # noqa: E402  (the rifleman: the Stormtrooper's body is his)
import rig_core as core  # noqa: E402  (the shared rig: primitives, IK, renderer, output)
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
M = core.Mat.on_ramp
NEW_MATERIALS: dict[str, core.Mat] = {      # each keeps the value given here (shift=False)
    "chrome": M("steel_blue", 3, 15, shift=False),            # BESTIARY §2.1, Legion chrome 0-5 shadow, 11-15 light
    "chrome_dark": M("steel_blue", 0, 8, black_floor=True, shift=False),
    "graft": M("plaster_warm", 7, 14, shift=False),           # v1 stand-in for the reserved pink ramp (v2)
    "raw": M("rust_brown", 2, 7, shift=False),                # the raw edge of the graft; the hound's gullet
    "patch": M("steel_blue", 4, 8, shift=False),              # ground of the US patch (C), stamped over
    "bolt_out": M("steel_blue", 13, 15, shift=False, flat=True),   # SD_StormBolt: chrome-white ...
    "bolt_core": M("flag_red", 11, 15, shift=False, flat=True),    # ... with a red core (BESTIARY §5); flat: a glow
    "hide": M("khaki_olive", 1, 9, shift=False),              # BESTIARY §6 says 4-10; see HIDE_NOTE
    "hide_dark": M("khaki_olive", 0, 5, shift=False),
    "belly": M("khaki_olive", 0, 2, black_floor=True, shift=False),   # black underbelly and muzzle (§10 rule 4)
    "bone": M("plaster_warm", 9, 14, shift=False),            # teeth, spines; the Stormtrooper's talons
    # The full set of cell E (D48). Appended after the sweep's: no id moves.
    # D49: blood is dark red for every faction, "rojo oscuro, nada de oliva" (supersedes BESTIARY §2.1's
    # olive). The same two definitions as gen_rig.py's D48 rifleman (flag_red 1-5 / 0-3 over black, flat: no
    # rim, so a drop stays red), so the two Reich bodies bleed alike; copied, not imported, so this table
    # does not follow a figure module's edits.
    "blood": M("flag_red", 1, 5, black_floor=True, shift=False, flat=True),    # drops, stains, runs, splats
    "pool": M("flag_red", 0, 3, black_floor=True, shift=False, flat=True),     # standing blood: darker
    "bolt_dim": M("steel_blue", 7, 12, shift=False, flat=True),      # SD_StormBolt's burst, fading
    "bolt_core_dim": M("flag_red", 6, 11, shift=False, flat=True),
}
# BESTIARY §6 gives the hide as khaki_olive 4-10. The first render with it
# measured body luma 99 against SDSTEL1's 101 (gap 1 at light 112): the hound
# vanished on green steel. The hide is therefore drawn in khaki_olive 1-9 and
# low on the ramp, Reich-dark like the rifleman; the sheet says so.
HIDE_NOTE = "BESTIARY §6 hide khaki_olive 4-10 measured luma 99 vs SDSTEL1 101; drawn in 1-9, darker"
NEW_FLAT = {n for n, m in NEW_MATERIALS.items() if m.flat}
LEGION_MATERIALS = {"chrome", "chrome_dark", "graft", "raw", "patch"}
BOLT_MATERIALS = {"bolt_out", "bolt_core", "bolt_dim", "bolt_core_dim"}   # Legion light: counted as Legion
# The rifleman's table, copied, with the new materials appended.
MATERIALS: dict[str, core.Mat] = dict(rig.MATERIALS)


def register_materials() -> None:
    """Append the new materials to this module's table (idempotent).
    Appending never moves an existing id."""
    for name, mat in NEW_MATERIALS.items():
        core.register_material(name, mat, MATERIALS)


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
        if q.limb == "arm" and q.side == core.RIGHT:    # his right arm, by its label
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


def _head_parts(cell: StormCell, add, bob: float = STORM_BOB) -> None:
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


def _emitter(cell: StormCell, pose: str, add, sh: np.ndarray | None = None,
             aim: tuple | None = None) -> np.ndarray:
    """His right arm: the Legion graft. Returns the muzzle point. The full
    set (D48) passes its own shoulder (the walk's bob) and aim (elbow offset,
    cannon direction); the sweep's defaults are unchanged."""
    sh = RIGHT_SHOULDER if sh is None else sh
    off, d = EMITTER_AIM[pose] if aim is None else aim
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
# The US patch as a core insignia: on the pauldron's visible centre when its
# outer face (the figure's right, model -x) is not turned away.
PATCH_INSIGNIA = core.Insignia("patch", (len(US_PATCH[0]), len(US_PATCH)),
                               core.pattern_drawer(US_PATCH, US_PATCH_COLOURS), outward=(-1.0, 0.0, 0.0),
                               min_px=PATCH_MIN_PX, anchor=(3.0, 2.0))


def stamp_patch(rgba: np.ndarray, pid: np.ndarray, prims: list[core.Prim], rotation: int) -> bool:
    """The US patch (PATCH_INSIGNIA). Returns whether it was stamped."""
    return core.stamp_insignia(rgba, pid, prims, rotation, PATCH_INSIGNIA)


def render_prims(prims: list[core.Prim], rotation: int, cv: Canvas, seed: int = SEED):
    """One sprite: (RGBA, material-id map at 1x). Reich-dark like the
    rifleman (his value shift); his armband, then the US patch."""
    lay = core.render_layers(prims, rotation, cv, MATERIALS, seed=seed, value_shift=rig.VALUE_SHIFT,
                             insignia=(core.ARMBAND, PATCH_INSIGNIA), what=f"rotation {rotation} ({cv.w}x{cv.h})")
    return lay.rgba, lay.mat


def render_storm(key: str, frame: str, rotation: int, seed: int = SEED):
    return render_prims(storm_model(STORM[key], "attack" if frame == "G" else "idle"), rotation, STORM_CV, seed)


def render_hound(key: str, frame: str, rotation: int, seed: int = SEED):
    return render_prims(hound_model(HOUND[key], "bite" if frame == "F" else "idle"), rotation, HOUND_CV, seed)


def legion_fraction(mat: np.ndarray) -> float:
    """Share of the opaque pixels drawn in Legion material (BESTIARY §5's <= 25 %)."""
    mid = core.material_ids(MATERIALS)
    ids = [mid[m] for m in LEGION_MATERIALS] + [mid[m] for m in BOLT_MATERIALS]
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
    """core.lineup with a choice of floor flat (the hound is judged over
    SDFLR1's lane line too, BESTIARY §10 rule 4)."""
    return core.lineup(figures, wall, light, width, floor, load=floor_rgb)


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


# ========================================================== gallop proof
# The quadruped skeleton of rig_core (spine chain, three-bone hind leg,
# QuadPose with gait phase) tried on the recommended hound, cell D (long
# build, crocodile jaw, dorsal spines): the walk frames A-D of BESTIARY §6
# as a transverse gallop, at rotations 1, 3 and 5, rotation 7 as the
# engine's mirror of 3. A capability proof for the CEO, not the set: the
# 46 lumps wait on his choice of cell (the sweep's sheet).
GALLOP_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "gallop"
GALLOP_BUILD = core.QuadBuild()
GALLOP_CV = Canvas(112, 64, 56, 56)  # the sweep's HOUND_CV is 56 high: a hind paw thrown back at rotation 5
                                     # projects below it (nearer the camera = lower on screen); the axis
                                     # stays centred, as mirror mode needs
GALLOP_FRAMES = {"A": 0.0, "B": 0.25, "C": 0.5, "D": 0.75}     # SDHN See: A B C D, phases of one stride
GALLOP_ROTS = (1, 3, 5)
GALLOP_TICS = 2                 # BESTIARY §6: See SDHN AABBCCDD, 2 tics a frame
GALLOP_SLOW_TICS = 8            # the same loop at a quarter speed, for the eye
HEAD_LEVEL = 16.0               # degrees added to the last neck bone so the head rides level
LEG_L = 1.35                    # the long build's leg thickness factor (BUILDS["long"].leg)
TAIL_DROOP = 28.0               # degrees the tail hangs below the pelvis line (the sweep's tail)
TAIL_WAG = 10.0                 # degrees it swings with the stride


def hound_gallop_model(cell: HoundCell, qpose: core.QuadPose,
                       build: core.QuadBuild = GALLOP_BUILD) -> list[core.Prim]:
    """The hound on the quadruped skeleton: the sweep's shapes (gen_storm's
    hound_model, long build) hung on posed bones instead of fixed points."""
    b = BUILDS["long"]
    q = core.pose_quadruped(build, qpose)
    P: list[core.Prim] = []
    L = LEG_L

    def add(grp, prim, limb="", side=core.CENTRE):
        prim.grp, prim.limb, prim.side = grp, limb, side
        P.append(prim)
        return prim

    sacrum, withers = q.spine[0], q.spine[-1]
    pel_a, chest_a = q.spine_angles[0], q.spine_angles[-1]
    pel_R, chest_R = core.bone_frame(pel_a), core.bone_frame(chest_a)
    at_chest = lambda x, y, z: withers + chest_R @ V(x, y, z)  # noqa: E731
    at_pelvis = lambda x, y, z: sacrum + pel_R @ V(x, y, z)  # noqa: E731
    # ------------------------------------------------------------ ribcage, in the chest bone's frame
    rx, ry, rz = b.cage
    cz = -4.0
    cy = -7.4
    add("body", core.on_bone(core.ellipsoid("hide", 0.32, (0, cy, cz), b.cage), withers, chest_a))
    for i in range(7):
        z = cz + rz * (-0.50 + 0.15 * i)
        s = float(np.sqrt(max(1 - ((z - cz) / rz) ** 2, 0.0)))
        add("body", core.on_bone(core.ellipsoid("hide", 0.46, (0, cy, z), (rx * s + 0.45, ry * s + 0.45, 0.62),
                                                clip=[(V(0, -1, 0), -(cy - ry * 0.45))]), withers, chest_a))
    add("body", core.on_bone(core.ellipsoid("belly", 0.30, (0, cy - ry * 0.52, cz - 1.5),
                                            (rx * 0.82, ry * 0.52, rz * 0.82)), withers, chest_a))
    # ------------------------------------------------------------ loin, belly line, haunches
    add("body", core.rcone("hide", 0.30, at_chest(0, cy + 0.8, cz - rz * 0.45), at_pelvis(0, -2.7, 2.5),
                           5.0 * L ** 0.5, 4.4 * L ** 0.5))
    add("body", core.rcone("belly", 0.25, at_chest(0, cy - ry * 0.45, cz - rz * 0.4), at_pelvis(0, -6.7, 3.0),
                           3.4 * L ** 0.5, 2.4 * L ** 0.5))
    for side in (core.LEFT, core.RIGHT):
        hip = q.legs["hl" if side == core.LEFT else "hr"][0]
        add("body", core.on_bone(core.ellipsoid("hide", 0.34, (0, 1.0, 0), b.haunch), hip, pel_a))
        sh = q.legs["fl" if side == core.LEFT else "fr"][0]
        add("body", core.on_bone(core.ellipsoid("hide", 0.37, (0, 1.5, -0.4), (2.8 * L, 5.4, 4.0)), sh, chest_a))
    # ------------------------------------------------------------ the top line: vertebrae and spines
    pts = q.spine
    seg = [float(np.linalg.norm(pts[i + 1] - pts[i])) for i in range(len(pts) - 1)]
    total = sum(seg)
    for i in range(9):
        d, k = total * i / 8, 0
        while k < len(seg) - 1 and d > seg[k]:
            d -= seg[k]
            k += 1
        p = pts[k] + (pts[k + 1] - pts[k]) * min(d / seg[k], 1.0) + V(0, 0.7, 0)
        add("body", core.ellipsoid("hide_dark", 0.37, tuple(p), (1.0, 0.9, 1.3)))
        if cell.spines:
            t = i / 8
            add("body", core.rcone("bone", 0.55, p, p + V(0, 3.4 - 1.2 * abs(t - 0.6), -1.2), 0.85, 0.2))
    if b.hump:
        add("body", core.on_bone(core.ellipsoid("hide", 0.38, (0, 1.0, -1.5), (4.4, 3.8, 6.2)), withers, chest_a))
    wag = TAIL_WAG * np.sin(2 * np.pi * qpose.phase)
    tail_a = pel_a + TAIL_DROOP + wag             # the tail bone points back (-z) and down
    add("body", core.on_bone(core.rcone("hide_dark", 0.27, V(0, -2.3, -3.0), V(0, -2.3, -16.0), 1.4, 0.45),
                             sacrum, tail_a))
    # ------------------------------------------------------------ legs
    for leg in core.LEGS:
        side = core.LEFT if leg.endswith("l") else core.RIGHT
        grp = "leg_l" if side == core.LEFT else "leg_r"
        root, mid, low, paw = q.legs[leg]
        if leg.startswith("h"):
            add(grp, core.rcone("hide", 0.32, root, mid, 3.0 * L, 1.9 * L), "hindleg", side)
            add(grp, core.rcone("hide", 0.30, mid, low, 1.8 * L, 1.15 * L), "hindleg", side)
            add(grp, core.rcone("hide_dark", 0.27, low, paw + V(0, 0.8, 0), 1.1 * L, 0.95 * L), "hindleg", side)
            add(grp, core.ellipsoid("belly", 0.35, tuple(paw + V(0, 0.0, 1.0)), (1.5 * L, 1.1, 2.2 * L)),
                "hindleg", side)
        else:
            add(grp, core.rcone("hide", 0.34, root, mid, 2.4 * L, 1.7 * L), "foreleg", side)
            add(grp, core.rcone("hide", 0.32, mid, low, 1.6 * L, 1.15 * L), "foreleg", side)
            add(grp, core.ellipsoid("belly", 0.35, tuple(paw + V(0, 0.0, 0.9)), (1.6 * L, 1.15, 2.3 * L)),
                "foreleg", side)
    # ------------------------------------------------------------ neck and head (in the head's frame)
    s = b.head_s
    snout = b.snout * (1.35 if cell.jaw == "croc" else 1.0)
    neck_root = at_chest(0, -3.5, 2.5)
    add("neck", core.rcone("hide", 0.34, neck_root, q.neck[1], 4.6 * L ** 0.5, 4.0 * s))
    add("neck", core.rcone("hide", 0.34, q.neck[1], q.neck[2], 4.0 * s, 3.4 * s))
    head_a = q.neck_angles[-1] + HEAD_LEVEL - qpose.head_pitch
    o = 2.4 * s                                   # the sweep's skull sits this far ahead of the neck's end
    head = [
        core.ellipsoid("hide", 0.40, (0, 1.6, o), (4.4 * s, 2.5 * s, 4.8 * s)),                   # flat skull
        core.rcone("hide", 0.38, V(0, 1.2, 1.0 + o), V(0, 0.8, snout + o), 3.5 * s, 2.3 * s),
        core.rcone("belly", 0.30, V(0, 0.9, snout * 0.55 + o), V(0, 0.7, snout + 0.2 + o), 2.95 * s, 2.4 * s),
        core.rcone("belly", 0.32, V(0, 0.6 - 1.9 * s, 0.5 + o), V(0, 0.6 - 1.6 * s, snout - 0.8 + o),
                   2.6 * s, 1.8 * s),                                                              # the jaw, shut
    ]
    teeth_n = 6 if cell.jaw == "croc" else 4
    for side in (1, -1):
        for i in range(teeth_n):
            z = 3.0 * s + i * (snout - 4.0 * s) / max(teeth_n - 1, 1) + o
            head.append(core.ellipsoid("bone", 0.6, (side * 1.9 * s, 0.6 - 1.2 * s, z), (0.45, 1.0 * s, 0.5)))
        for i in range(teeth_n - 1):
            z = 4.0 * s + i * (snout - 5.5 * s) / max(teeth_n - 2, 1) + o
            head.append(core.ellipsoid("bone", 0.6, (side * 1.6 * s, 0.6 - 0.6 * s, z), (0.4, 0.9 * s, 0.45)))
    for prim in head:
        add("head", core.on_bone(prim, q.neck[-1], head_a))
    return P


def render_gallop(frame: str, rotation: int, cell_key: str = HOUND_RECOMMENDED, seed: int = SEED) -> np.ndarray:
    pose = core.QuadPose(frame, "gallop", GALLOP_FRAMES[frame])
    rgba, _ = render_prims(hound_gallop_model(HOUND[cell_key], pose), rotation, GALLOP_CV, seed)
    return rgba


def build_gallop_proof(stamp: str, out_dir: Path = PREVIEW_DIR, work_dir: Path = GALLOP_DIR,
                       cell_key: str = HOUND_RECOMMENDED, seed: int = SEED) -> Path:
    """Render the proof (rotations 1, 3, 5 traced; 7 mirrored from 3), write
    the PNGs, GIFs and metrics to work_dir and the dated sheet to out_dir."""
    work_dir.mkdir(parents=True, exist_ok=True)
    cell = HOUND[cell_key]
    spr: dict = {}
    for f, ph in GALLOP_FRAMES.items():
        pose = core.QuadPose(f, "gallop", ph)
        turn = core.render_rotations(lambda: hound_gallop_model(cell, pose), GALLOP_CV, (*GALLOP_ROTS, 7),
                                     mirror=True, materials=MATERIALS, seed=seed, value_shift=rig.VALUE_SHIFT,
                                     what=f"gallop {f}")
        for r, rgba in turn.items():
            spr[(f, r)] = rgba
            name = f"{HOUND_SPRITE}_{cell_key}_gallop_{f}{r}" + ("_mirror_of_3" if r == 7 else "")
            save(rgba, work_dir / f"{name}.png", GALLOP_CV)
            print(name, flush=True)
        skel = core.skeleton_prims(core.pose_quadruped(GALLOP_BUILD, pose), "bone", "raw")
        spr[("skel", f)] = core.render(skel, 3, GALLOP_CV, MATERIALS, seed=seed)
        save(spr[("skel", f)], work_dir / f"skeleton_{f}3.png", GALLOP_CV)
    metrics = {}
    for (f, r), rgba in spr.items():
        if f == "skel":
            continue
        m = measure(rgba)
        metrics[f"{f}{r}"] = {k: m[k] for k in ("height_px", "width_px", "lowest_row", "body_luma", "worst_gap")}
    (work_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    t = lambda n: int(round(n * core.TIC_MS))  # noqa: E731
    gifs = {}
    for r in (*GALLOP_ROTS, 7):
        frames = [core.on_bg(spr[(f, r)], core.NEUTRAL) for f in GALLOP_FRAMES]
        gifs[r] = core.save_gif(frames, [t(GALLOP_TICS)] * 4, work_dir / f"gallop_rot{r}.gif")
        gifs[(r, "slow")] = core.save_gif(frames, [t(GALLOP_SLOW_TICS)] * 4, work_dir / f"gallop_rot{r}_slow.gif")
    skel_frames = [core.on_bg(spr[("skel", f)], core.NEUTRAL) for f in GALLOP_FRAMES]
    gifs["skel"] = core.save_gif(skel_frames, [t(GALLOP_SLOW_TICS)] * 4, work_dir / "skeleton_rot3_slow.gif")
    return gallop_sheet(spr, metrics, gifs, stamp, out_dir, cell_key, seed)


GALLOP_NOTES = [
    "WHAT THIS PROVES. The rig now has the three things the hound sweep said it lacked (its sheet, section 8): "
    "a spine chain (sacrum, loin, back, chest, then two neck bones, each angle relative to its parent), a "
    "three-bone digitigrade hind leg (hip, stifle, hock, paw, solved as a pantograph: femur and metatarsus "
    "stay parallel, every bone keeps its length, the stifle points forward and the hock back), and a "
    "quadruped pose with a gait phase (four paw targets, spine flex, bob and pitch from one number). The "
    "four frames are one transverse gallop: A gathered (hind paws reaching under the chest, back rounded), "
    "B the hind push, C stretched (forepaws reaching, back extended), D the forepaws landing.",
    "MIRROR MODE. The hound wears no insignia and is symmetric, so Doom's paired rotations are valid for "
    "him: rotation 7 here is not traced, it is rotation 3 flipped about the body axis, exactly what the "
    "engine draws for a lump named SDHNA3A7. Five drawings per frame instead of eight: the full set is "
    "BESTIARY 6's 46 images, not 70. The flip swaps the lead leg (his left side leads at 3, the right "
    "seems to lead at 7), as every Doom monster's walk does; the light also flips (key light from the "
    "right at 7). Both are the convention, visible only if you look for them.",
    "WHAT IS NOT DONE, HONESTLY. This is the recommended cell D's shapes moved onto the new skeleton, not a "
    "redesign; the body pieces are the sweep's ellipsoids hung on bones, so in the stretched frame C the "
    "loin and the ribcage show their seam, and the chest does not deform. The gait numbers (duty, stride, "
    "lift, flex) are chosen by eye for 4 frames at 2 tics, not taken from footage. Not rendered: the bite "
    "E-G, pain H, death I-N, and rotations 2, 4 (8 and 6 would be their mirrors). Rotation order and the "
    "flip are checked by hand against r_things.c, NOT in GZDoom.",
]


def gallop_sheet(spr: dict, metrics: dict, gifs: dict, stamp: str, out_dir: Path, cell_key: str,
                 seed: int) -> Path:
    def strip(items):
        return '<div class="strip">' + "".join(items) + "</div>"

    names = {1: "front", 3: "his left side", 5: "back", 7: "his right side (mirror of 3)"}
    S = []
    body = ""
    for r in GALLOP_ROTS:
        body += strip([core.gif_tile(gifs[r], 3, f"rotation {r}, game speed", f"{names[r]}, {GALLOP_TICS} tics a frame"),
                       core.gif_tile(gifs[(r, "slow")], 3, f"rotation {r}, quarter speed", "for the eye")]
                      + [core.sprite_tile(spr[(f, r)], 3, core.rotation_lump(HOUND_SPRITE, f, r, mirror=True),
                                          f"phase {GALLOP_FRAMES[f]:.2f}") for f in GALLOP_FRAMES])
    S.append(("1 · The gallop at rotations 1, 3 and 5",
              f"Cell {cell_key} (recommended in the sweep: long build, crocodile jaw, dorsal spines) on the new "
              "quadruped skeleton. Walk frames A-D of BESTIARY §6 (See: SDHN AABBCCDD, 2 tics a frame), "
              "animated at the speed the engine plays them and at a quarter of it, then the four stills at 3x "
              "on neutral grey.", body))
    body = strip([core.sprite_tile(spr[(f, 3)], 3, f"{HOUND_SPRITE}{f}3 traced") for f in GALLOP_FRAMES])
    body += strip([core.sprite_tile(spr[(f, 7)], 3, f"{HOUND_SPRITE}{f}7 = {f}3 flipped",
                                    core.rotation_lump(HOUND_SPRITE, f, 3, mirror=True)) for f in GALLOP_FRAMES]
                  + [core.gif_tile(gifs[7], 3, "rotation 7, game speed", "the engine's flip of 3")])
    S.append(("2 · Mirror mode: rotation 7 is rotation 3 flipped",
              "Top row traced at rotation 3; bottom row what the engine shows at rotation 7 for the paired "
              "lump (SDHNA3A7 and so on): the same image mirrored about the body axis. Not traced.", body))
    body = strip([core.gif_tile(gifs["skel"], 3, "skeleton, rotation 3", "quarter speed")]
                 + [core.sprite_tile(spr[("skel", f)], 3, f"skeleton {f}3", f"phase {GALLOP_FRAMES[f]:.2f}")
                    for f in GALLOP_FRAMES])
    S.append(("3 · The skeleton under it",
              "The same four poses with only the bones drawn (rotation 3): spine chain and neck along the top, "
              "the forelegs (shoulder, elbow, wrist) and the three-bone hind legs (hip, stifle, hock, paw). The "
              "hind leg's first and last bones stay parallel: that is the pantograph solve.", body))
    figs = [(spr[(f, 3)], *grab(GALLOP_CV)) for f in GALLOP_FRAMES]
    body = ""
    for key, wall, light, what in HOUND_SCENES[-1:] + flat.SCENES[2:3]:
        floor = "SDFLR1" if key == "S6" else "SDFLR2"
        sc = lineup(figs, wall, light, 96 * len(figs), floor)
        body += strip([core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 1, f"{key} 1x: {wall} at light {light}",
                                 what),
                       core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 2, f"{key} 2x")])
    S.append(("4 · At 1x on MAP01's walls", "Frames A-D at rotation 3, each standing by its own offsets. Light is "
              "gen_enemy.py's stand-in, NOT VERIFIED against GZDoom.", body))
    rows = [[f"{HOUND_SPRITE}{k}", f"{m['height_px']} x {m['width_px']}", m["lowest_row"], m["body_luma"],
             m["worst_gap"]] for k, m in metrics.items()]
    body = sheetlib.table(["frame", "h x w px", "lowest row", "body luma", "worst gap"], rows, 1)
    body += (f"<p class=\"lead\">Canvas {GALLOP_CV.w}x{GALLOP_CV.h}, sole line at row {GALLOP_CV.foot_row} (a paw "
             "in stance stands on it; a row above means every paw is in the air). BESTIARY §6: under 40 px "
             "tall.</p>")
    S.append(("5 · Numbers", "", body))
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in GALLOP_NOTES) + "</div>"
    body += ('<div class="ask"><b>For the CEO</b><ol><li>Nothing to approve here: it is a capability check. '
             "If the gallop reads, the hound's 46 lumps can be drawn on this skeleton once you pick the cell "
             "in the sweep (recommended D).</li></ol></div>")
    S.append(("6 · What this proves and what is left", "", body))
    intro = ("The quadruped skeleton added to the shared rig (<code>tools/art/rig_core.py</code>): a spine chain, "
             "a three-bone digitigrade hind leg, a quadruped pose with gait phase, and Doom's mirrored rotation "
             "pairs. One proof: the recommended hound cell galloping at rotations 1, 3 and 5, rotation 7 as the "
             f"mirror of 3. Palette v1 only, seed {seed}, no system fonts. Built by <code>tools/art/gen_storm.py "
             "--gallop-proof</code>. Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_storm.py on tools/art/rig_core.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), "
              "deterministic, no system fonts.")
    path = out_dir / f"{stamp}_F5_hound-gallop-proof.html"
    sheetlib.write_sheet(path, lang="en", title="Reich hound — gallop on the quadruped skeleton (F5)",
                         subtitle=f"SDHN · cell {cell_key} · rotations 1, 3, 5 and the mirror · capability proof",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", core.SHEET_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


# ================================================== the full set of cell E (D48)
# D48 (CEO, 2026-10-14): the Stormtrooper is cell E of the sweep, "queda muy
# macarra, me gusta" (bare skull with a chrome plate on his right half,
# greatcoat, forearm cannon), over BESTIARY §5's 25 % Legion share, accepted.
# This renders his whole frame set on the rig, as gen_rig.py did for the
# rifleman: the frames of src/zscript/monsters/stormtrooper.zs (TROO today,
# the same letters as SDHS, MOD-SPEC §6.3): walk A-D, attack E F G (shared by
# the claw and the bolt: one state, A_SD_MeleeOrMissile at G), pain H at 8
# rotations; death I-M and gib N-U at rotation 0; and SD_StormBolt's SDBL
# A-E at rotation 0. All 8 rotations are separate lumps, not mirrored pairs:
# the chrome is on his right and the armband on his left. Frame A at rotation
# 1, without the talons, is the sweep's cell E pixel for pixel (a test).
#
# The claw. The ZScript shows E F G for both attacks, so the claw has no
# frames of its own in the contract. Two PROPOSED frames, V (claw drawn back)
# and W (the slash), are drawn too, in proposed_melee/: they show only if
# mod-engineer splits Melee from Missile (a ZScript change, not a rename).
#
# Blood. D48 asked for "much more blood" in the rifleman's deaths and D49
# made it dark red for every faction ("rojo oscuro, nada de oliva"). The
# Stormtrooper gets both from the start: a spray from the chest, a wet stain
# spreading on the coat, splats where the drops land and a pool under him,
# in the rifleman's and the Legion's own red materials (`blood`, `pool`:
# flag_red 1-5 and 0-3 over black). The actor's BloodColor in
# stormtrooper.zs (the engine's hit puffs) is read at build time, not
# copied here (zscript_blood_color). Outputs: work/art/enemies/storm/full_E/.
FULL_KEY = "E"
FULL_DIR = STORM_DIR / "full_E"
MELEE_DIR = FULL_DIR / "proposed_melee"
BOLT_SPRITE = "SDBL"                # BESTIARY §5, MOD-SPEC §6.3
STORM_ZS = PROJECT_ROOT / "src" / "zscript" / "monsters" / "stormtrooper.zs"
STORM_DEATH_CV = Canvas(112, 80, 56, 72)    # he lies across, a pool round him
STORM_GIB_CV = Canvas(128, 96, 64, 88)      # the skull and the cannon arm fly
BOLT_CV = Canvas(32, 32, 16, 20)            # grAb (16, 16): centred, as BAL1 (8, 11 of 15x15)
BOLT_Y = BOLT_CV.foot_row - BOLT_CV.h // 2  # model height that projects to the canvas centre
RIFLE_AWAY = ((-10.0, 20.0, 4.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))   # the sweep's; the rifle is removed
RIGHT_HAND = (-9.0, 27.0, 3.0)              # the removed right arm's target (the sweep's)
BLOOD_RAMP = "flag_red"
BLOOD_MAX_INDEX = 5                         # as the rifleman's: no blood brighter than flag_red 5 (the armband is 4-11)
BLOOD_NOTE = ("dark red, D49: flag_red 1-5 over black for drops and stains, 0-3 for pools, the rifleman's and "
              "the Legion's own materials; the engine's hit puffs are the actor's BloodColor, read from "
              "stormtrooper.zs")

FULL_GROUPS = (
    ("walk", "ABCD", True),
    ("attack", "EFG", True),
    ("pain", "H", True),
    ("death", "IJKLM", False),
    ("gib", "NOPQRSTU", False),
)
MELEE_GROUP = (("claw (proposed)", "VW", True),)
BOLT_FRAMES = "ABCDE"


@dataclass(frozen=True)
class StormPose:
    key: str
    title: str
    foot_l: tuple = STORM_FEET["foot_l"]
    foot_r: tuple = STORM_FEET["foot_r"]
    bob: float = STORM_BOB
    stride: float = 0.3
    hand_l: tuple = (9.6, 27.2, 3.4)        # his Reich hand (the claw)
    elbow: tuple = tuple(EMITTER_AIM["idle"][0])   # cannon: elbow offset from the shoulder ...
    aim: tuple = tuple(EMITTER_AIM["idle"][1])     # ... and direction
    hunch: float | None = None              # None: the cell's
    tilt: float | None = None
    head_pitch: float | None = None         # None: hunch x 0.7, the sweep's
    lean: float = 0.0                       # upper body back (pain, death)
    roll: float = 0.0                       # degrees he falls to his RIGHT, the chrome side
    glow: str = ""                          # "" | "charge" | "core" | "bolt"
    claws: bool = True
    stain: float = 0.0                      # 0..1, the wet patch on his coat front
    burst: bool = False                     # the gib's first frame: the chest gives way
    canvas: Canvas = STORM_CV


_DOWN = dict(elbow=(-2.6, -8.4, -0.6), aim=(-0.25, -0.95, 0.2))     # the cannon hangs dead
STORM_POSES = {
    # walk: the sweep's stance is A; he limps on the chrome side (shorter right stride, the heavy
    # shoulder dips when the right foot takes the weight) and the cannon swings like a pendulum
    "A": StormPose("A", "the sweep's stance"),
    "B": StormPose("B", "left foot forward", (3.4, ANKLE_Y, 6.0), (-4.3, ANKLE_Y + 1.6, -4.6), -1.7, 1.0,
                   hand_l=(9.4, 27.6, -1.6), elbow=(-1.8, -8.6, 3.0), tilt=4.5),
    "C": StormPose("C", "right leg passing", (3.6, ANKLE_Y, 0.4), (-4.2, ANKLE_Y + 2.4, 1.0), -0.5, 0.3,
                   hand_l=(9.6, 27.0, 2.2), elbow=(-1.9, -8.6, 1.6), tilt=7.5),
    "D": StormPose("D", "right foot forward, the limp", (3.4, ANKLE_Y + 1.4, -4.8), (-4.3, ANKLE_Y, 4.0), -1.9,
                   0.9, hand_l=(9.8, 28.2, 7.0), elbow=(-1.6, -8.6, 0.6), tilt=9.5),
    # attack: the cannon comes up (E), its core lights (F), the bolt leaves with a recoil (G)
    "E": StormPose("E", "the cannon comes up", (3.9, ANKLE_Y, -1.2), (-4.3, ANKLE_Y, 2.4), -1.2, 0.5,
                   hand_l=(8.6, 30.5, 5.0), elbow=(-1.6, -7.2, 3.6), aim=(0.10, -0.15, 1.0), hunch=12.0,
                   glow="charge"),
    "F": StormPose("F", "aimed, the core lights", (3.9, ANKLE_Y, -1.2), (-4.3, ANKLE_Y, 2.4), -1.2, 0.5,
                   hand_l=(8.6, 30.5, 5.0), elbow=tuple(EMITTER_AIM["attack"][0]),
                   aim=tuple(EMITTER_AIM["attack"][1]), hunch=12.0, glow="core"),
    "G": StormPose("G", "the bolt leaves, recoil", (3.9, ANKLE_Y, -1.6), (-4.3, ANKLE_Y, 2.0), -1.4, 0.5,
                   hand_l=(8.6, 30.0, 4.0), elbow=(-1.4, -6.4, 3.8), aim=(0.12, 0.18, 1.0), hunch=9.0,
                   lean=4.0, glow="bolt"),
    "H": StormPose("H", "pain", (3.9, ANKLE_Y, 0.8), (-4.3, ANKLE_Y, -3.0), -1.2, 0.3,
                   hand_l=(10.6, 34.0, 2.0), elbow=(-3.4, -6.6, -1.6), aim=(-0.35, -0.75, 0.55),
                   lean=14.0, head_pitch=26.0, tilt=11.0),
    # proposed claw (not in today's states): his Reich hand drawn back, then the slash across
    "V": StormPose("V", "claw drawn back (proposed)", (3.9, ANKLE_Y, -1.6), (-4.3, ANKLE_Y, 2.4), -1.4, 0.6,
                   hand_l=(13.0, 50.0, 1.0), elbow=(-2.0, -8.0, 1.0), hunch=8.0, tilt=2.0),
    "W": StormPose("W", "the slash (proposed)", (3.6, ANKLE_Y, 4.0), (-4.3, ANKLE_Y, -2.6), -2.0, 0.9,
                   hand_l=(-3.0, 28.0, 13.0), elbow=(-1.8, -8.6, 2.0), hunch=22.0, tilt=10.0),
    # death, rotation 0: hit in the chest, knees go, he falls to his right (the heavy side)
    "I": StormPose("I", "hit", (3.9, ANKLE_Y, 1.2), (-4.3, ANKLE_Y, -3.6), -1.2, 0.4,
                   hand_l=(12.5, 45.0, 1.0), **_DOWN, hunch=6.0, lean=20.0, head_pitch=30.0, stain=0.4,
                   canvas=STORM_DEATH_CV),
    "J": StormPose("J", "knees go", (3.9, ANKLE_Y, 1.2), (-4.3, ANKLE_Y, -1.0), -7.0, 0.6,
                   hand_l=(12.0, 40.0, 2.0), **_DOWN, hunch=8.0, lean=22.0, head_pitch=26.0, roll=12.0,
                   stain=0.7, canvas=STORM_DEATH_CV),
    "K": StormPose("K", "falling to his right", (3.9, ANKLE_Y, 1.2), (-4.3, ANKLE_Y, 0.0), -11.0, 0.8,
                   hand_l=(13.0, 37.0, 1.0), **_DOWN, hunch=6.0, lean=14.0, head_pitch=20.0, roll=44.0,
                   stain=0.9, canvas=STORM_DEATH_CV),
    "L": StormPose("L", "hits the floor", (3.9, ANKLE_Y, 1.0), (-4.3, ANKLE_Y, 0.5), -9.0, 0.6,
                   hand_l=(12.0, 38.0, -1.0), **_DOWN, hunch=4.0, lean=6.0, head_pitch=8.0, roll=74.0,
                   stain=1.0, canvas=STORM_DEATH_CV),
    "M": StormPose("M", "dead, in his blood", (3.7, ANKLE_Y, 0.6), (-4.3, ANKLE_Y, 1.4), -2.0, 0.4,
                   hand_l=(10.0, 31.0, 4.0), **_DOWN, hunch=2.0, head_pitch=-10.0, roll=90.0,
                   stain=1.0, canvas=STORM_DEATH_CV),
    "N": StormPose("N", "the chest bursts", (3.9, ANKLE_Y, 0.8), (-4.3, ANKLE_Y, -3.0), -1.0, 0.3,
                   hand_l=(12.0, 41.0, 2.0), elbow=(-3.0, -6.8, -1.0), aim=(-0.3, -0.7, 0.6),
                   lean=10.0, head_pitch=20.0, stain=1.0, burst=True, canvas=STORM_GIB_CV),
}
# Seconds after the shot, for the blood in flight: about the middle of each
# frame's display (I 8, J 8, K 6, L 6 tics) and long after for the corpse.
DEATH_T = {"I": 0.12, "J": 0.36, "K": 0.56, "L": 0.74, "M": 2.0}
DEATH_POOL = {"L": 0.35, "M": 1.0}
GIB_T = {"N": 0.03, "O": 0.10, "P": 0.24, "Q": 0.38, "R": 0.55, "S": 0.75, "T": 1.0, "U": 1.6}
WOUND = V(-0.6, 33.0 + STORM_BOB, 3.0)    # the chest wound, model space, where the spray leaves
GRAVITY = rig.GRAVITY
FOUNTAIN_DROPS = 46
GIB_CHUNKS = 24
GIB_CHUNK_MATS = ("blood", "blood", "blood", "flesh", "coat", "blood", "coat_dark", "flesh", "coat", "raw")


def _talons(P: list, add) -> None:
    """Three long pale nails on his left (Reich) hand, along the forearm."""
    arm = core.select(P, limb="arm", side=core.LEFT)
    hand = [q for q in arm if q.mat == "flesh"]
    cuff = [q for q in arm if q.mat == "coat_dark"]
    if not hand or not cuff:
        return
    h = hand[0].a
    fd = cuff[0].b - cuff[0].a
    fd = fd / np.linalg.norm(fd)
    side = np.cross(fd, V(0, 1, 0))
    side = side / (np.linalg.norm(side) or 1.0)
    for k in (-1, 0, 1):
        base = h + fd * 0.8 + side * (0.75 * k)
        tip = base + fd * 2.9 + side * (0.6 * k) + V(0, -0.5, 0.4)
        prim = add("arm", rig.rcone("bone", 0.62, base, tip, 0.5, 0.18))
        prim.limb, prim.side = "arm", core.LEFT


def _stain(sp: StormPose, add, seed: int) -> None:
    """The wet patch on his coat front, the drips running down the skirt,
    and (the gib's first frame) the chest giving way."""
    rng = np.random.default_rng(seed + 10)
    if sp.stain > 0:
        n = int(round(8 * sp.stain))
        for i in range(8):
            x, y = rng.uniform(-3.4, 3.0), rng.uniform(30.5, 37.5)
            r = rng.uniform(1.3, 2.3, 3) * (0.7 + 0.5 * sp.stain)
            if i < n:
                add("upper", rig.ellipsoid("blood", 0.40, (x, y + sp.bob, 4.7), (r[0], r[1], 0.9)))
        for _ in range(int(round(4 * sp.stain))):
            x = rng.uniform(-3.0, 2.5)
            y0, y1 = 27.5, 27.5 - rng.uniform(5.0, 12.0) * sp.stain

            def z(y, x=x):
                rr = rig.coat_radius(y)
                return rig.SKIRT_KZ * np.sqrt(max(rr * rr - x * x, 0.0)) + 0.25
            add("skirt", rig.rcone("blood", 0.38, V(x, y0 + sp.bob, z(y0)), V(x, y1 + sp.bob, z(y1)), 0.75, 0.55))
    if sp.burst:
        for _ in range(7):
            c = (rng.uniform(-4.5, 3.5), rng.uniform(30, 38) + sp.bob, rng.uniform(4.8, 6.4))
            add("upper", rig.ellipsoid("blood", 0.40, c, tuple(rng.uniform(1.4, 2.6, 3))))


def storm_full_model(sp: StormPose, seed: int = SEED,
                     cell: StormCell | None = None) -> tuple[list[rig.Prim], dict]:
    """Cell E in pose `sp`, model space (gen_rig's conventions). The sweep's
    storm_model(E, "idle") is this with pose A, no talons and no stain.
    Returns the primitives and the anchors (chest, hip, seam, muzzle) that
    follow the body. The graft's primitives carry limb "graft"."""
    cell = STORM[FULL_KEY] if cell is None else cell
    hunch = cell.hunch if sp.hunch is None else sp.hunch
    tilt = cell.tilt if sp.tilt is None else sp.tilt
    head_up = hunch * 0.7 if sp.head_pitch is None else sp.head_pitch
    p = rig.Pose(sp.key, "storm", foot_l=sp.foot_l, foot_r=sp.foot_r, bob=sp.bob, carry="free",
                 stride=sp.stride, head_pitch=head_up, hand_l=sp.hand_l, hand_r=RIGHT_HAND,
                 rifle_at=RIFLE_AWAY, canvas=STORM_CV)
    prims, _ = rig.build_model(p)
    P = []
    for q in prims:
        if q.grp == "rifle" or (q.limb == "arm" and q.side == core.RIGHT):
            continue
        if cell.coat == "short" and q.grp == "skirt":
            continue
        if cell.head == "skull" and q.grp == "helmet":
            continue
        P.append(q)

    def add(grp, prim):
        prim.grp = grp
        P.append(prim)
        return prim

    _head_parts(cell, add, sp.bob)
    sh = V(-(rig.SHOULDER_X + 0.2), 39.4 + sp.bob, -0.4)
    start = len(P)
    d = V(*sp.aim)
    muzzle = _emitter(cell, "idle", add, sh=sh, aim=(V(*sp.elbow), d))
    d = d / np.linalg.norm(d)
    if sp.glow == "charge":                     # the core kindles inside the muzzle
        add("arm", rig.ellipsoid("bolt_core_dim", 0.7, tuple(muzzle + d * 0.2), (1.2, 1.2, 1.2)))
    elif sp.glow == "core":
        add("arm", rig.ellipsoid("bolt_core", 0.75, tuple(muzzle + d * 0.6), (1.7, 1.7, 1.7)))
    elif sp.glow == "bolt":                     # the sweep's G: chrome-white with a red core
        add("arm", rig.ellipsoid("bolt_out", 0.6, tuple(muzzle + d * 2.4), (2.9, 2.9, 2.9)))
        add("arm", rig.ellipsoid("bolt_core", 0.7, tuple(muzzle + d * 3.6), (1.5, 1.5, 1.5)))
    for q in P[start:]:
        q.limb, q.side = "graft", core.RIGHT
    if sp.claws:
        _talons(P, add)
    _stain(sp, add, seed)
    anchors = {"chest": (WOUND + V(0, sp.bob - STORM_BOB, 0), "upper"),
               "hip": (V(0, rig.HIP_Y + sp.bob, 0), "skirt"), "seam": (sh.copy(), "arm"),
               "muzzle": (muzzle, "arm")}
    waist = V(0, rig.WAIST_Y + sp.bob, 0)
    rig.transform(P, anchors, rig.UPPER, rig.rot_x(-hunch), waist)
    rig.transform(P, anchors, {"skirt"}, rig.rot_x(-hunch * 0.3), waist)
    rig.transform(P, anchors, rig.UPPER, rig.rot_z(-tilt), waist)
    if sp.lean:
        rig.transform(P, anchors, rig.UPPER, rig.rot_x(sp.lean), waist)
        rig.transform(P, anchors, {"skirt"}, rig.rot_x(sp.lean * 0.3), waist)
    if sp.roll:
        pivot = V(sp.foot_r[0], 0.0, 0.0)       # his right sole: he goes over the chrome side
        slide = V(rig.SLIDE * np.sin(np.deg2rad(sp.roll)), 0, 0)
        rig.transform(P, anchors, rig.ALL_BODY, rig.rot_z(-sp.roll), pivot, slide)
        rig.rest_on_floor(P, anchors, rig.ALL_BODY)
    return P, anchors


# ------------------------------------------------------------------ the gore
def spray(origin, t: float, seed: int, n: int, *, mat: str = "blood", vx=(-44.0, 44.0), vy=(12.0, 48.0),
          vz=(-10.0, 12.0), r=(1.2, 1.8), streak: float = 0.05, rest: float = 0.15) -> list[rig.Prim]:
    """Drops thrown from `origin` at t = 0, seen `t` seconds later: in flight
    a short streak along the velocity, landed a flat splat on the floor. The
    same seed throws the same drops, so the frames of one death agree."""
    rng = np.random.default_rng(seed)
    out = []
    origin = np.asarray(origin, float)
    for _ in range(n):
        v = V(rng.uniform(*vx), rng.uniform(*vy), rng.uniform(*vz))
        rs = rng.uniform(*r)
        jitter = V(*rng.uniform(-1.0, 1.0, 3))
        p, landed = rig._ballistic(origin + jitter, v, t, rest)
        if landed:
            out.append(rig.ellipsoid(mat, 0.34, (p[0], rest, p[2]), (rs * 2.2, 0.45, rs * 3.0), grp="spray"))
        else:
            vel = v + V(0, -GRAVITY * t, 0)
            out.append(rig.rcone(mat, 0.40, p - vel * streak, p, rs * 0.7, rs, grp="spray"))
    return out


POOL_AHEAD = 0.55                   # a pool's centre sits this share of its depth towards the viewer
POOL_DEPTH = 2.4                    # depth over width at full spread: the camera is only 9 degrees down,
                                    # so a true-depth pool is a line; Doom's corpses cheat the same way


def pool(centre, g: float, mat: str = "pool", rx: float = 6.0, rz: float = 3.0,
         grow: tuple = (12.0, 4.0)) -> list[rig.Prim]:
    """A pool on the floor that grows with g (0..1), spreading out from
    under the body towards the viewer, with a wetter lobe."""
    c = np.asarray(centre, float)
    ax, az = rx + grow[0] * g, (rz + grow[1] * g) * POOL_DEPTH
    z = c[2] + POOL_AHEAD * az
    return [rig.ellipsoid(mat, 0.26, (c[0], 0.2, z), (ax, 0.6, az), grp="pool"),
            rig.ellipsoid(mat, 0.40, (c[0] + 0.3 * ax, 0.3, z + 0.2 * az), (0.45 * ax, 0.62, 0.5 * az), grp="pool")]


def death_model(frame: str, seed: int = SEED) -> list[rig.Prim]:
    """Death I-M: the body, the spray from the chest, the splats and the pool."""
    P, anc = storm_full_model(STORM_POSES[frame], seed)
    t = DEATH_T[frame]
    P += spray(WOUND, t, seed + 20, 30)
    P += spray(WOUND + V(0, 1.0, 0), t, seed + 21, 12, vx=(-14.0, 14.0), vy=(14.0, 34.0), vz=(4.0, 14.0),
               r=(1.2, 1.8))                                     # the entry wound, towards the shooter
    if frame != "I":                                             # the seam tears after the hit
        P += spray(RIGHT_SHOULDER, max(t - 0.25, 0.0), seed + 22, 8, vx=(-26.0, -6.0),
                   vy=(2.0, 14.0), vz=(-4.0, 4.0), r=(0.9, 1.3))
    g = DEATH_POOL.get(frame, 0.0)
    if g:
        P += pool(anc["chest"][0], g)
        P += pool(anc["hip"][0], g * 0.8, rx=4.0, rz=2.5, grow=(8.0, 3.0))
        P += pool(anc["seam"][0], g, rx=1.5, rz=1.2, grow=(2.5, 1.0))
    return P


def _gib_chunks(t: float, seed: int) -> list[rig.Prim]:
    """The upper body as GIB_CHUNKS lumps; each one that lands leaves a splat."""
    rng = np.random.default_rng(seed + 31)
    out = []
    for i in range(GIB_CHUNKS):
        p0 = V(rng.uniform(-6, 6), rng.uniform(30, 44), rng.uniform(-3, 3))
        side = np.sign(p0[0]) or 1.0
        v = V(side * rng.uniform(6, 34), rng.uniform(8, 44), rng.uniform(-6, 5))
        r = V(rng.uniform(1.1, 2.8), rng.uniform(1.0, 2.2), rng.uniform(1.1, 2.6))
        mat = GIB_CHUNK_MATS[i % len(GIB_CHUNK_MATS)]
        rest = r[1] * 0.5
        p, landed = rig._ballistic(p0, v, t, rest)
        if landed:
            r = r * V(1.35, 0.5, 1.35)
            out.append(rig.ellipsoid("blood", 0.36, (p[0], 0.2, p[2]), (r[0] * 1.6, 0.3, r[2] * 1.3), grp="pool"))
        out.append(rig.ellipsoid(mat, 0.45 if mat != "flesh" else 0.40, tuple(p), tuple(r), grp="chunk"))
    return out


def gib_model(frame: str, seed: int = SEED) -> list[rig.Prim]:
    """XDeath N-U. N: the chest bursts, a fountain starts. Then the upper
    body is chunks on ballistic arcs, the chrome-plated skull and the cannon
    arm fly whole, the legs stand a moment and fall to his right, and the
    floor fills: splats where every drop lands, a pool under the stump."""
    t = GIB_T[frame]
    whole, anc_w = storm_full_model(STORM_POSES["N"], seed)
    fountain = spray(WOUND, t, seed + 40, FOUNTAIN_DROPS, vx=(-40.0, 40.0), vy=(16.0, 52.0), vz=(-10.0, 10.0),
                     r=(1.1, 1.8), streak=0.035)
    seam = spray(RIGHT_SHOULDER, t, seed + 41, 12, vx=(-24.0, -4.0), vy=(6.0, 26.0),
                  vz=(-5.0, 5.0), r=(0.9, 1.4))
    if frame == "N":
        return whole + fountain + seam
    k = float(np.clip((t - 0.2) / 0.6, 0, 1))      # the legs: stand, buckle, fall
    k = k * k * (3 - 2 * k)
    legs_pose = replace(STORM_POSES["N"], lean=0.0, head_pitch=0.0, bob=-1.0 - 10.0 * k, claws=False,
                        stain=0.0, burst=False)
    legs_all, _ = storm_full_model(legs_pose, seed)
    keep = [q for q in legs_all if q.grp in {"leg_l", "leg_r", "skirt"} or q.tag == "belt"]
    for q in keep:
        if q.tag == "belt":
            q.grp = "stump"
    bob = legs_pose.bob
    rng = np.random.default_rng(seed + 43)
    keep.append(rig.ellipsoid("blood", 0.30, (0, rig.WAIST_Y + bob + 0.8, 0), (6.6, 2.6, 4.6), grp="stump"))
    for _ in range(5):
        keep.append(rig.ellipsoid("blood", 0.42, (rng.uniform(-4, 4), rig.WAIST_Y + bob + rng.uniform(1.0, 3.6),
                                                  rng.uniform(-2, 2)), tuple(rng.uniform(1.2, 2.4, 3)), grp="stump"))
    legs = {"leg_l", "leg_r", "skirt", "stump"}
    anc = {"stump": (V(0, rig.WAIST_Y + bob, 0), "stump")}
    if k > 0:
        roll = 88.0 * k
        slide = V(rig.SLIDE * 0.45 * np.sin(np.deg2rad(roll)), 0, 0)
        rig.transform(keep, anc, legs, rig.rot_z(-roll), V(legs_pose.foot_r[0], 0, 0), slide)
        rig.rest_on_floor(keep, anc, legs)
    if t >= 0.38:                                   # the pool spreads from where the stump lies
        g = min((t - 0.38) / 0.9, 1.0)
        s = anc["stump"][0]
        keep += pool((s[0], 0, s[2] + 1.0), g, rx=6.0, rz=3.0, grow=(16.0, 5.0))
    keep += _gib_chunks(t, seed) + fountain + seam
    # the skull (chrome plate and all) and the cannon arm fly whole, spinning, and lie where they land
    head = [q for q in whole if q.grp == "head"]
    graft = core.select(whole, limb="graft")
    for name, parts, v, spin, rest in (("skull", head, V(-7.0, 50.0, 2.0), 420.0, 4.0),
                                       ("cannon", graft, V(-24.0, 28.0, 3.0), -300.0, 2.6)):
        for q in parts:
            q.grp = "fly"
        c0 = np.mean([q.bound()[0] for q in parts], axis=0)
        p, landed = rig._ballistic(c0, v, t, rest)
        R = rig.rot_z(spin * t)
        if landed:
            R = rig.rot_z(90.0)                     # the skull lies on its side
            if name == "cannon":                    # the cannon lies flat along the floor
                u = anc_w["muzzle"][0] - anc_w["seam"][0]
                R = rig.rot_z(np.degrees(np.arctan2(u[1], u[0])))
        rig.transform(parts, {}, {"fly"}, R, c0, p - c0)
        if landed:
            rig.rest_on_floor(parts, {}, {"fly"})
            keep += pool((p[0], 0, p[2]), 0.25, rx=2.0, rz=1.2,
                         grow=(3.0, 1.0))
        keep += parts
    return keep


# ------------------------------------------------------------------ the bolt
def bolt_model(frame: str) -> list[rig.Prim]:
    """SD_StormBolt, SDBL A-E at rotation 0: A-B the flying bolt (a
    chrome-white shell, a red core turned to the viewer, two sparks that
    swap), C-E the burst (BESTIARY §5). Rendered additively in the engine."""
    c = V(0, BOLT_Y, 0)
    E = rig.ellipsoid
    if frame in "AB":
        a = 0.0 if frame == "A" else 1.0
        P = [E("bolt_out", 0.70, tuple(c), (3.0 + 0.4 * a, 3.2 - 0.5 * a, 3.0)),
             E("bolt_core", 0.85, tuple(c + V(0.3 * a, 0.2 * a, 2.4)), (1.7, 1.7, 1.2))]
        for ang in ((40.0, 220.0) if frame == "A" else (130.0, 310.0)):
            q = np.deg2rad(ang)
            P.append(E("bolt_out", 0.75, tuple(c + V(5.0 * np.cos(q), 5.0 * np.sin(q), 1.0)), (1.1, 1.1, 1.1)))
        return P
    step = "CDE".index(frame)
    P = []
    if step < 2:
        P.append(E("bolt_out" if step == 0 else "bolt_dim", 0.65, tuple(c), (4.4 + 1.4 * step,) * 3))
        P.append(E("bolt_core" if step == 0 else "bolt_core_dim", 0.80, tuple(c + V(0, 0, 3.0 + step)),
                   (2.6 - 0.5 * step,) * 3))
    n = 6 + 2 * step
    for i in range(n):
        q = 2 * np.pi * (i + 0.5 * step) / n
        rad = 6.0 + 2.6 * step
        P.append(E("bolt_out" if step < 2 else "bolt_dim", 0.70,
                   tuple(c + V(rad * np.cos(q), rad * np.sin(q), 1.5)), (1.2 - 0.1 * step,) * 3))
    return P


# ------------------------------------------------------------------ render
def full_canvas(frame: str) -> Canvas:
    return STORM_POSES[frame].canvas if frame in STORM_POSES else STORM_GIB_CV


def full_prims(frame: str, seed: int = SEED) -> list[rig.Prim]:
    if frame in DEATH_T:
        return death_model(frame, seed)
    if frame in GIB_T:
        return gib_model(frame, seed)
    return storm_full_model(STORM_POSES[frame], seed)[0]


def render_full(frame: str, rotation: int, seed: int = SEED):
    """One lump of the full set: (RGBA, material-id map)."""
    return render_prims(full_prims(frame, seed), rotation, full_canvas(frame), seed)


def render_bolt(frame: str, seed: int = SEED) -> np.ndarray:
    return render_prims(bolt_model(frame), 0, BOLT_CV, seed)[0]


def full_plan() -> list[tuple[str, int]]:
    """The contract's lumps (MOD-SPEC §6.3: SDHS A-H at 8 rotations, I-U at 0)."""
    return core.frame_plan(FULL_GROUPS, mirror=False)


def melee_plan() -> list[tuple[str, int]]:
    return core.frame_plan(MELEE_GROUP, mirror=False)


def full_lump(frame: str, rot: int, sprite: str = STORM_SPRITE) -> str:
    return f"{sprite}{frame}{rot}"


def zscript_tics(path: Path = STORM_ZS) -> dict[str, dict[str, int]]:
    """Frame letters and tics per state, read from the actor's ZScript:
    {state: {letter: tics of its first state line}}. Today the actor names
    TROO; after the swap SDHS, with the same letters."""
    out: dict[str, dict[str, int]] = {}
    states: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.split("//")[0].strip()
        m = re.match(r"^([A-Za-z]+):$", s)
        if m:
            if not states or out.get(states[-1]):
                states = []
            states.append(m.group(1))
            for st in states:
                out.setdefault(st, {})
            continue
        m = re.match(r"^(?:TROO|SDHS)\s+([A-Z]+)\s+(-?\d+)", s)
        if m and states:
            for st in states:
                for ch in m.group(1):
                    out[st].setdefault(ch, int(m.group(2)))
    return {k: v for k, v in out.items() if v}


def zscript_blood_color(path: Path = STORM_ZS) -> tuple[int, int, int]:
    """The actor's BloodColor "RR GG BB" as written in its ZScript."""
    m = re.search(r'BloodColor\s+"([0-9A-Fa-f]{2}) ([0-9A-Fa-f]{2}) ([0-9A-Fa-f]{2})"',
                  path.read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"no BloodColor in {path.name}")
    return tuple(int(h, 16) for h in m.groups())


def blood_share(mat: np.ndarray) -> float:
    """Share of the opaque pixels drawn in blood (drops, stains, pools)."""
    mid = core.material_ids(MATERIALS)
    op = mat >= 0
    return float(np.isin(mat, [mid["blood"], mid["pool"]]).sum() / max(op.sum(), 1))


def build_full(out_dir: Path = FULL_DIR, seed: int = SEED) -> dict:
    """Render every lump of the full set to out_dir (and proposed_melee/),
    the GIFs and metrics.json. Returns {"sprites", "melee", "bolt", "metrics"}."""
    out_dir.mkdir(parents=True, exist_ok=True)
    mel_dir = out_dir / MELEE_DIR.name
    sprites, mats, melee, bolt = {}, {}, {}, {}
    for frame, rot in full_plan():
        rgba, mat = render_full(frame, rot, seed)
        save(rgba, out_dir / f"{full_lump(frame, rot)}.png", full_canvas(frame))
        sprites[(frame, rot)], mats[(frame, rot)] = rgba, mat
        print(full_lump(frame, rot), flush=True)
    for frame, rot in melee_plan():
        rgba, mat = render_full(frame, rot, seed)
        save(rgba, mel_dir / f"{full_lump(frame, rot)}.png", full_canvas(frame))
        melee[(frame, rot)], mats[(frame, rot)] = rgba, mat
        print("proposed", full_lump(frame, rot), flush=True)
    for f in BOLT_FRAMES:
        bolt[f] = render_bolt(f, seed)
        save(bolt[f], out_dir / f"{full_lump(f, 0, BOLT_SPRITE)}.png", BOLT_CV)
        print(full_lump(f, 0, BOLT_SPRITE), flush=True)
    metrics = {}
    for (f, r), rgba in {**sprites, **melee}.items():
        m = measure(rgba)
        m["legion_share"] = round(legion_fraction(mats[(f, r)]), 3)
        m["blood_share"] = round(blood_share(mats[(f, r)]), 3)
        metrics[full_lump(f, r)] = m
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    data = {"sprites": sprites, "melee": melee, "bolt": bolt, "metrics": metrics}
    write_full_gifs(data, out_dir)
    return data


def load_full(out_dir: Path = FULL_DIR) -> dict:
    def rd(p):
        with Image.open(p) as im:
            return np.asarray(im.convert("RGBA")).copy()
    return {"sprites": {(f, r): rd(out_dir / f"{full_lump(f, r)}.png") for f, r in full_plan()},
            "melee": {(f, r): rd(out_dir / MELEE_DIR.name / f"{full_lump(f, r)}.png") for f, r in melee_plan()},
            "bolt": {f: rd(out_dir / f"{full_lump(f, 0, BOLT_SPRITE)}.png") for f in BOLT_FRAMES},
            "metrics": json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))}


def additive(rgba: np.ndarray, under: np.ndarray) -> np.ndarray:
    """RenderStyle "Add" (the bolt): the sprite's colour added to what is
    behind it. A stand-in, NOT VERIFIED against GZDoom's blending."""
    out = under.astype(np.int32).copy()
    a = rgba[..., 3] > 0
    out[a] += rgba[..., :3][a]
    return np.clip(out, 0, 255).astype(np.uint8)


def write_full_gifs(data: dict, out_dir: Path = FULL_DIR) -> dict:
    """At game speed, from the tics in stormtrooper.zs (35 tics a second)."""
    tics = zscript_tics()
    t = lambda n: int(round(n * core.TIC_MS))  # noqa: E731
    spr, mel = data["sprites"], data["melee"]
    walk_t = 2 * tics["See"]["A"]                       # AABBCCDD: each drawing shows for two state lines

    def seq(src, frames, r):
        return [core.on_bg(src[(f, r)], core.NEUTRAL) for f in frames]

    out = {}
    for r in range(1, core.ROTATIONS + 1):
        out[f"walk_{r}"] = core.save_gif(seq(spr, "ABCD", r), [t(walk_t)] * 4, out_dir / f"walk_rot{r}.gif")
        out[f"attack_{r}"] = core.save_gif(seq(spr, "AEFG", r), [t(walk_t * 2)] + [t(tics["Missile"][f]) for f in "EFG"],
                                           out_dir / f"attack_rot{r}.gif")
        out[f"pain_{r}"] = core.save_gif(seq(spr, "AHHA", r), [t(20), t(tics["Pain"]["H"]), t(tics["Pain"]["H"]), t(20)],
                                         out_dir / f"pain_rot{r}.gif")
        if mel:
            out[f"claw_{r}"] = core.save_gif(seq({**spr, **mel}, "AVWA", r), [t(walk_t * 2), t(8), t(6), t(10)],
                                             out_dir / f"claw_rot{r}_proposed.gif")
    out["turn"] = core.save_gif([core.on_bg(spr[("A", r)], core.NEUTRAL) for r in range(1, 9)], [t(12)] * 8,
                                out_dir / "turntable.gif")
    death = [core.on_bg(core.pad_to(spr[("A", 1)], STORM_CV, STORM_DEATH_CV), core.NEUTRAL)] + \
            [core.on_bg(spr[(f, 0)], core.NEUTRAL) for f in "IJKLM"]
    out["death"] = core.save_gif(death, [t(20)] + [t(tics["Death"][f]) for f in "IJKL"] + [t(70)],
                                 out_dir / "death.gif")
    gib = [core.on_bg(core.pad_to(spr[("A", 1)], STORM_CV, STORM_GIB_CV), core.NEUTRAL)] + \
          [core.on_bg(spr[(f, 0)], core.NEUTRAL) for f in "NOPQRSTU"]
    out["gib"] = core.save_gif(gib, [t(20)] + [t(tics["XDeath"][f]) for f in "NOPQRST"] + [t(70)],
                               out_dir / "gib.gif")
    wall = flat.tile_to(flat.host_rgb("SDCONC1"), BOLT_CV.w, BOLT_CV.h)
    out["bolt_fly"] = core.save_gif([additive(data["bolt"][f], wall) for f in "AB"], [t(4)] * 2,
                                    out_dir / "bolt_flight.gif")
    out["bolt_burst"] = core.save_gif([additive(data["bolt"][f], wall) for f in "CDE"] + [wall],
                                      [t(6)] * 3 + [t(20)], out_dir / "bolt_burst.gif")
    return out


# ------------------------------------------------------------------ sheet
FULL_VERDICT = [
    "WHAT IS HERE. Cell E as the CEO chose it, on the rig, for every frame the actor's states name: 77 SDHS lumps "
    "(walk A-D, attack E-G and pain H at 8 rotations, death I-M and gib N-U at one), the 5 SDBL lumps of his bolt, "
    "and 16 proposed claw lumps (V, W) that no state shows yet. Frame A at rotation 1 is the sweep's cell E, "
    "unchanged (a test checks it pixel for pixel without the talons). All 8 rotations are separate lumps: the "
    "chrome is on his right and the armband on his left, so Doom's mirrored pairs would put the plate on the "
    "wrong side.",
    "HOW HE MOVES. He limps on the chrome side: the right stride is shorter and the heavy shoulder dips when the "
    "right foot takes his weight (tilt 4.5 to 9.5 degrees through the cycle), and the cannon swings like a dead "
    "weight. The attack is one sequence for both attacks because the ZScript plays E F G for the claw and for "
    "the bolt: the cannon comes up (E), its core lights red (F), the bolt leaves with a recoil (G). He dies "
    "falling to his right, over the cannon, where the rifleman falls to his left: the two Reich corpses do not "
    "lie the same way.",
    "BLOOD. Much more of it than the rifleman's D38 deaths, as D48 asked, and dark red as D49 decided (\"rojo "
    "oscuro, nada de oliva\"): a spray from the chest that lands as splats, a second jet from the entry wound "
    "towards the shooter, a wet patch that spreads down the coat and drips, the seam of the graft tearing, and a "
    "pool under the chest and the hip. The gib throws a fountain of 46 drops and 24 chunks, and the floor fills as "
    "they land. The red is the rifleman's own: flag_red 1-5 over black for drops and stains, 0-3 for pools, both "
    "darker than the armband (flag_red 4-11).",
    "WHAT DOES NOT, HONESTLY. The talons on his left hand are two or three pale pixels at 1x. From the front "
    "(rotation 1) the raised cannon foreshortens to a disc, as the rifleman's rifle does. His chrome side "
    "(rotation 7) measures the lowest value gap of the set on green steel at light 112 (section 9): the cell's own "
    "33 % chrome on that side, accepted in D48, not new here. Rotation order, grAb offsets and the additive bolt are checked by hand and in "
    "a stand-in, NOT in GZDoom.",
]
FULL_ASK = [
    "Approve the set as drawn (recommended): the 77 SDHS and 5 SDBL lumps go to assets/sprites/ and mod-engineer "
    "swaps TROO for SDHS and BAL1 for SDBL (MOD-SPEC 6.3, a rename), to be judged in GZDoom on MAP01.",
    "The claw: keep E F G for both attacks (today's states, recommended: it is Doom's imp, and nothing has to "
    "change in code), or ask mod-engineer to split Melee from Missile so the proposed V W claw frames play "
    "(a ZScript change, not a rename).",
    "Blood: look at section 7 beside the rifleman's red deaths. Both use the same red materials (and the "
    "Legion's), so they should read alike; if they do not, say which one is right and the other follows. The "
    "colour itself is D49's, and the actor's BloodColor already follows it (section 7's swatch).",
]


def _read_sprite(path: Path) -> tuple[np.ndarray, int, int] | None:
    if not path.is_file():
        return None
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGBA")).copy()
    return (arr, *core.read_grab(path))


def build_full_sheet(data: dict, stamp: str, out_dir: Path = PREVIEW_DIR, gif_dir: Path = FULL_DIR) -> Path:
    spr, mel, bolt, met = data["sprites"], data["melee"], data["bolt"], data["metrics"]
    tics = zscript_tics()
    rot_names = {1: "front", 2: "front-left", 3: "his left (Reich)", 4: "back-left", 5: "back",
                 6: "back-right", 7: "his right (chrome)", 8: "front-right"}
    T, G = core.sprite_tile, core.gif_tile

    def strip(items):
        return '<div class="strip">' + "".join(items) + "</div>"

    S = []
    body = strip([T(spr[("A", r)], 4, full_lump("A", r), rot_names[r]) for r in range(1, 9)])
    body += strip([T(spr[("A", r)], 1, full_lump("A", r)) for r in range(1, 9)]
                  + [G(gif_dir / "turntable.gif", 4, "turntable", "animated")])
    S.append(("1 · Turnaround: frame A at Doom's 8 rotations",
              "4x on neutral grey, then true 1x. Eight separate lumps, not mirrored pairs: the chrome plate and the "
              "cannon are on his right, the armband on his left.", body))

    walk_t = 2 * tics["See"]["A"]
    body = strip([G(gif_dir / f"walk_rot{r}.gif", 4, f"walk, rotation {r}", rot_names[r]) for r in range(1, 9)])
    for r in (1, 3, 7):
        body += strip([T(spr[(f, r)], 4, full_lump(f, r), STORM_POSES[f].title) for f in "ABCD"])
    S.append(("2 · Walk A-B-C-D at game speed",
              f"See: SDHS AABBCCDD, {tics['See']['A']} tics a line (stormtrooper.zs), so each drawing shows for "
              f"{walk_t} tics at 35 a second. He limps on the chrome side. Stills of rotations 1, 3 and 7 below.",
              body))

    att = " ".join(f"{f} {tics['Missile'][f]}" for f in "EFG")
    body = strip([G(gif_dir / f"attack_rot{r}.gif", 4, f"attack, rotation {r}", att) for r in (1, 2, 3, 7, 8)])
    for f in "EFG":
        body += strip([T(spr[(f, r)], 3, full_lump(f, r), STORM_POSES[f].title if r == 1 else "")
                       for r in range(1, 9)])
    wall = flat.tile_to(flat.host_rgb("SDCONC1"), BOLT_CV.w, BOLT_CV.h)
    body += strip([T(bolt[f], 4, full_lump(f, 0, BOLT_SPRITE), "flight" if f in "AB" else "burst") for f in BOLT_FRAMES]
                  + [core.tile(core.png_uri(additive(bolt[f], wall)), BOLT_CV.w, BOLT_CV.h, 4,
                               f"{full_lump(f, 0, BOLT_SPRITE)} added", "on SDCONC1") for f in "AC"]
                  + [G(gif_dir / "bolt_flight.gif", 4, "SDBL A B, 4 tics", "additive on SDCONC1"),
                     G(gif_dir / "bolt_burst.gif", 4, "SDBL C D E, 6 tics", "additive on SDCONC1")])
    S.append(("3 · Attack E-F-G and the bolt (SD_StormBolt, SDBL A-E)",
              f"Missile and Melee share one state: {att} tics, A_SD_MeleeOrMissile at G, so these frames serve the "
              "claw and the bolt. The cannon comes up, its core lights, the bolt leaves with a recoil. The bolt: a "
              "chrome-white shell with a red core, two sparks that swap (A B), then the burst (C D E), rotation 0, "
              "shown alone and added onto a wall as RenderStyle \"Add\" draws it (stand-in, NOT VERIFIED in GZDoom).",
              body))

    body = strip([G(gif_dir / f"claw_rot{r}_proposed.gif", 4, f"claw, rotation {r}", "A, V 8, W 6, A")
                  for r in (1, 2, 3, 7)])
    for f in "VW":
        body += strip([T(mel[(f, r)], 3, full_lump(f, r), STORM_POSES[f].title if r == 1 else "")
                       for r in range(1, 9)])
    S.append(("4 · The claw: V-W, PROPOSED (no state shows them today)",
              "His left hand is still the Reich's, and it has talons (the three pale nails). Drawn back over his "
              "shoulder (V), then a slash across (W). They play only if mod-engineer splits Melee from Missile in "
              "stormtrooper.zs; until then the claw uses E F G, like Doom's imp. Kept in proposed_melee/, outside "
              "the contract's lumps; tics 8 and 6 are a suggestion.", body))

    p = tics["Pain"]["H"]
    body = strip([G(gif_dir / f"pain_rot{r}.gif", 4, f"pain, rotation {r}", f"A, H {p}, H {p}, A") for r in (1, 3, 7)]
                 + [T(spr[("H", r)], 3, full_lump("H", r)) for r in range(1, 9)])
    S.append(("5 · Pain H", "He recoils: upper body back 14 degrees, skull up, the cannon flung out and down.", body))

    dts = ", ".join(f"{f} {tics['Death'][f]}" for f in "IJKL")
    body = strip([G(gif_dir / "death.gif", 4, "death, game speed", f"{dts} tics, M stays")]
                 + [T(spr[(f, 0)], 3, full_lump(f, 0), STORM_POSES[f].title) for f in "IJKLM"])
    xts = ", ".join(f"{f} {tics['XDeath'][f]}" for f in "NOPQRST")
    body += strip([G(gif_dir / "gib.gif", 4, "gib (XDeath), game speed", f"{xts} tics, U stays")])
    body += strip([T(spr[(f, 0)], 2, full_lump(f, 0)) for f in "NOPQRSTU"])
    S.append(("6 · Death I-M and gib N-U, with the blood (rotation 0)",
              "Death: hit in the chest, the knees go, he falls to his right over the cannon and lies in his blood. "
              "Gib: the chest bursts, a fountain, the upper body in chunks, the chrome-plated skull and the cannon "
              "arm fly whole and land, the legs stand a moment and fall, and the floor fills. Olive blood "
              f"({html.escape(BLOOD_NOTE)}).", body))

    # 7. the colour note, with the rifleman
    figs = [(spr[("M", 0)], *grab(STORM_DEATH_CV)), (spr[("U", 0)], *grab(STORM_GIB_CV))]
    labels = ["SDHSM0 (ours, dead)", "SDHSU0 (ours, gibbed)"]
    for lumpn in ("SDRRL0", "SDRRU0"):
        got = _read_sprite(RIFLEMAN_DIR / f"{lumpn}.png")
        if got:
            figs.append(got)
            labels.append(f"{lumpn} (the rifleman's D48/D49 redo, as on disk at this build)")
    body = ""
    for floor, wall_n, light in (("SDFLR2", "SDCONC1", 160), ("SDFLR1", "SDCONC1", 128), ("SDFLR2", "SDSTEL1", 112)):
        sc = lineup(figs, wall_n, light, 128 * len(figs), floor)
        Image.fromarray(sc, "RGB").save(gif_dir / f"blood_{floor}_{light}.png", optimize=True)
        body += strip([core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 1, f"1x: {floor} at light {light}", wall_n),
                       core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 2, "2x, for the eye")])
    blood_cols = MATERIALS["blood"].colours()
    pool_cols = MATERIALS["pool"].colours()
    band = core.ramp("flag_red")[4:12]
    zs_blood = zscript_blood_color()
    cols = blood_cols + [(255, 255, 255)] + pool_cols + [(255, 255, 255)] + band + [(255, 255, 255), zs_blood]
    sw = np.zeros((12, 12 * len(cols), 3), np.uint8)
    for i, c in enumerate(cols):
        sw[:, i * 12:(i + 1) * 12] = c
    body += strip([core.tile(core.png_uri(sw), sw.shape[1], sw.shape[0], 3, "blood | pool | armband | BloodColor",
                             "black + flag_red 1-5 | black + flag_red 0-3 | flag_red 4-11 | "
                             + " ".join(f"{v:02X}" for v in zs_blood) + " (stormtrooper.zs, the engine's hit puffs)")])
    rows = []
    for lumpn in ("SDHSI0", "SDHSL0", "SDHSM0", "SDHSN0", "SDHSR0", "SDHSU0"):
        m = met[lumpn]
        rows.append([lumpn, f"{m['height_px']} x {m['width_px']}", f"{m['blood_share']:.0%}", m["body_luma"]])
    bl = float(np.mean(flat.luma(np.array(blood_cols[2:6], np.uint8))))
    fl = {f: float(flat.luma(floor_rgb(f)).mean()) for f in ("SDFLR1", "SDFLR2")}
    body += sheetlib.table(["lump", "h x w px", "blood share", "body luma"], rows)
    body += (f"<p class=\"lead\">Blood luma (flag_red 1-4, the lit drops) about {bl:.0f}; floor luma SDFLR2 "
             f"{fl['SDFLR2']:.0f}, SDFLR1 {fl['SDFLR1']:.0f}: on the floor the pool is a strong dark shape at every "
             "light, and on his olive coat the red stain reads by hue as well as value. The rifleman's corpses "
             "beside ours are his D48/D49 redo as it stood on disk when this sheet was built (another session is "
             "working on it): review the two side by side.</p>")
    S.append(("7 · Colour note: the blood, beside the rifleman's corpses",
              "D48 asked for much more blood in the rifleman's deaths and D49 made it dark red; this is the same "
              "on the Stormtrooper, in the rifleman's materials. Both corpses on MAP01's floor flats at three lights (gen_enemy's "
              "stand-in, NOT VERIFIED against GZDoom), the swatches, and the numbers.", body))

    # 8. at 1x on MAP01
    figs = [(spr[("A", 1)], *grab(STORM_CV)), (spr[("G", 3)], *grab(STORM_CV))]
    labels = ["SDHSA1 (ours)", "SDHSG3 (ours, firing, his left)"]
    rr = rifleman()
    if rr:
        figs.append(rr)
        labels.append("SDRRA1 (the approved rifleman, D48)")
    troo = rig.freedoom_sprite("TROOA1")
    if troo:
        figs.append(troo)
        labels.append("TROOA1 (Freedoom, today's placeholder)")
    figs.append((spr[("A", 7)], *grab(STORM_CV)))
    labels.append("SDHSA7 (ours, his chrome side)")
    body = ""
    for key, wall_n, light, what in flat.SCENES:
        sc = lineup(figs, wall_n, light, 64 * len(figs))
        Image.fromarray(sc, "RGB").save(gif_dir / f"lineup_{key}.png", optimize=True)
        body += strip([core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 1, f"{key} 1x: {wall_n} at light {light}",
                                 what),
                       core.tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 3, f"{key} 3x")])
    far = flat.far(lineup(figs, "SDSTEL1", 112, 64 * len(figs)))
    body += strip([core.tile(core.png_uri(far), far.shape[1], far.shape[0], 5, "game distance, S3 (worst case), /4"),
                   _sil_tile(spr[("A", 1)])])
    body += "<p class=\"lead\">Left to right: " + html.escape(" · ".join(labels)) + \
            ". Each sprite stands by its own offsets, as the engine places it.</p>"
    S.append(("8 · At 1x on MAP01, beside the approved rifleman",
              "The four scenes of the sweeps: corridor, hangar dado, the fuel bay at light 112 (worst case), crate "
              "cover. Light is gen_enemy.py's stand-in, NOT VERIFIED against GZDoom.", body))

    rows = []
    for f, r in [(f, r) for f in "ABCDEFGH" for r in (1, 3, 5, 7)]:
        m = met[full_lump(f, r)]
        rows.append([full_lump(f, r), f"{m['height_px']} x {m['width_px']}", m["body_luma"], m["gap_S1"],
                     m["gap_S2"], m["gap_S3"], m["gap_S4"], f"{m['legion_share']:.0%}"])
    body = sheetlib.table(["lump", "h x w px", "body luma", "gap S1", "gap S2", "gap S3", "gap S4", "Legion share"],
                          rows)
    walk = [met[full_lump(f, r)]["legion_share"] for f in "ABCD" for r in range(1, 9)]
    body += (f"<p class=\"lead\">Legion share (chrome, graft, raw seam, the bolt) over the walk: {min(walk):.0%} to "
             f"{max(walk):.0%}; the sweep measured cell E at 17 / 10 / 33 % (front / left / right), over BESTIARY "
             "§5's 25 %, which D48 accepted. Canvases: standing "
             f"{STORM_CV.w}x{STORM_CV.h} grAb {grab(STORM_CV)}, death {STORM_DEATH_CV.w}x{STORM_DEATH_CV.h}, gib "
             f"{STORM_GIB_CV.w}x{STORM_GIB_CV.h}, bolt {BOLT_CV.w}x{BOLT_CV.h} grAb {grab(BOLT_CV)} (centred). "
             f"{len(full_plan())} SDHS lumps + {len(BOLT_FRAMES)} SDBL + {len(melee_plan())} proposed.</p>")
    S.append(("9 · Numbers", "", body))

    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in FULL_VERDICT) + "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in FULL_ASK) \
            + "</ol></div>"
    S.append(("10 · Honest verdict and what you decide", "", body))
    intro = ("D48: the CEO chose cell E of the Stormtrooper sweep (bare skull with a chrome plate on his right half, "
             "greatcoat, forearm cannon: \"queda muy macarra, me gusta\"). This is his whole frame set on the rig, as "
             "the rifleman's was (D38): every frame stormtrooper.zs names, his bolt, a proposed claw, and much more "
             f"blood in the deaths. Palette v1 only, seed {SEED}, no system fonts. Lump names are MOD-SPEC §6.3's "
             "reserved SDHS and SDBL, the names §5.1's TROO and BAL1 placeholders stand in for. Built by "
             "<code>tools/art/gen_storm.py --full</code>. Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_storm.py on tools/art/rig_core.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), "
              "deterministic, no system fonts. Freedoom sprites shown for scale only, from freedoom2.wad 0.13.0, "
              "BSD-3-Clause (© the Freedoom contributors), not used as a source.")
    path = out_dir / f"{stamp}_F5_stormtrooper-E-full-set.html"
    sheetlib.write_sheet(path, lang="en", title="Hybrid Stormtrooper — cell E, full frame set (F5, D48)",
                         subtitle=f"SDHS · SDBL · {len(full_plan())} + {len(BOLT_FRAMES)} lumps, "
                                  f"{len(melee_plan())} proposed · draft for the CEO's gate",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", core.SHEET_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    ap.add_argument("--sheet-only", action="store_true",
                    help="rebuild the sheet from the sprites already in work/art/enemies/{storm,hound}/")
    ap.add_argument("--no-sheet", action="store_true", help="sprites only")
    ap.add_argument("--gallop-proof", action="store_true",
                    help="only the hound's gallop on the quadruped skeleton (work/art/enemies/gallop/ and its sheet)")
    ap.add_argument("--full", action="store_true",
                    help="cell E's full frame set (D48): work/art/enemies/storm/full_E/ and its sheet")
    ap.add_argument("--full-sheet-only", action="store_true",
                    help="rebuild the full set's sheet from work/art/enemies/storm/full_E/")
    args = ap.parse_args()
    if args.full or args.full_sheet_only:
        data = load_full() if args.full_sheet_only else build_full()
        if args.no_sheet:
            return
        path = build_full_sheet(data, args.stamp)
        print("sheet:", path.relative_to(PROJECT_ROOT))
        return
    if args.gallop_proof:
        path = build_gallop_proof(args.stamp)
        print("sheet:", path.relative_to(PROJECT_ROOT))
        return
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
