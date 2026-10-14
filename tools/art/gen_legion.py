"""F5 — Liberty Legion trooper on the 3D rig: the D35 design sweep, and cell C's full frame set (D48).

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_legion.py               (Windows)
    .venv/bin/python tools/art/gen_legion.py                       (macOS)
    ... gen_legion.py --stamp 2026-10-13_2215   fixes the sheet's timestamp
    ... gen_legion.py --no-sheet                sprites and metrics only
    ... gen_legion.py --full                    D48: cell C's 70 SDLT lumps, GIFs and their sheet
    ... gen_legion.py --full --only SDLTL0      a few lumps, for a quick look (no sheet)
    ... gen_legion.py --full --sheet-only       the full set's sheet from the lumps on disk

Since D48 (CEO, 2026-10-14: cell C) and D45 (palette v2) two things changed
here, both described in their sections below: the pink is palette v2's
official `flesh_pink` (checked identical to the sweep's candidate, so the
sweep still reproduces byte for byte), and section "the full set" renders
cell C's whole frame set with the dark-red blood of D48/D49 into
work/art/enemies/legion/full_C/ (SDLT<frame><rot>.png, GIFs, metrics.json,
pair_*.png lineups) and docs/art/previews/<stamp>_F5_legion-trooper-C-full-set.html.
What follows is the sweep's original description.

What this is. D35: the five most-seen enemies get drawings of their own.
The Liberty Legion trooper (`SD_LegionTrooper`, sprite `SDLT`,
docs/engine/BESTIARY.md §4) is the second infantry and the force holding
MAP01's hangar. Before ~49 images exist, the CEO makes ONE decision, as he
did with the Reich rifleman (cell E, D38): what the man looks like. This is
that decision as a SWEEP (PIPELINE stage 2): six labelled cells, each shown
standing (frame A) at rotations 1, 2 and 3 and firing (frame F) at
rotations 1 and 3, then at 1x beside the Freedoom placeholders on MAP01's
walls. Nothing is written to assets/.

Unlike the rifleman's flat sweep (gen_enemy.py), the cells are built on the
rig D38 approved as the method (gen_rig.py: primitives, two-bone IK, Doom's
rotations, majority vote to 1x, contour and rim). So the cell the CEO picks
is already in the final method; no second translation step.

The sweep's dimensions (one row per cell; every cell carries the BESTIARY §4
constants: chrome M1 helmet, pink flesh, pale trousers, pump shotgun held
high across the chest, US-flag patch on the right shoulder):

        face                         torso                 shoulders
    A   smooth, eyeless              chrome muscle cuirass  small chrome pauldrons
    B   grin: eye pits, white teeth  chrome muscle cuirass  small chrome pauldrons
    C   smooth, eyeless              chrome muscle cuirass  chrome football pads
    D   chrome visor over the eyes   chrome muscle cuirass  small chrome pauldrons
    E   smooth, eyeless              bare pink, chrome harness  small chrome pauldrons
    F   grin                         chrome muscle cuirass  chrome football pads

A is the brief taken literally; every other cell changes one or two things
from it, so a cell can be read against A.

What the rig needed that gen_rig.py did not have when this sweep was made
(the full note is on the sheet, section 5): a CHROME shading (banded
Lambert turns chrome into grey plastic, so chrome here reflects a two-tone
environment, bright sky, a dark horizon line, darker ground, with a hard
specular dot, the 1970s airbrush-chrome convention, and skips the middle of
the steel_blue ramp); no VALUE_SHIFT (gen_rig darkens the Reich by 0.26; the
Legion is the LIGHT faction, BESTIARY §2.1, body 0.72-0.80); materials as a
parameter; a flag stamp instead of the armband; a shotgun carry. The first
version carried its own copy of the renderer for that. Since the rig_core
refactor (2026-10-13) all of it is in tools/art/rig_core.py: chrome is a
material shading (core.Chrome), the materials are a table handed to the
renderer, the flag is a core.Insignia, lit() takes the extended palette.
This file is the trooper's figure, cells and sheet only; the refactor left
every PNG it writes byte-identical.

Palette. BESTIARY §2.1 and ART-BIBLE §3 give the Legion's body mass to a
"reserved pink/flesh ramp, to be added to palette.json v2". Palette v1 has
no pink. This file never edits docs/art/palette.json. The sweep carried a
candidate ramp (since D45 it is palette v2's flesh_pink, read from
palette.json; section "palette"), 16 colours built with palette.py's own rule
(gamma 1.8 between two endpoints) for 16 of the 94 reserved slots. Every
v1 colour stays as it is (ART-BIBLE §3: later sets only ADD ramps). Every
opaque pixel is a palette.json v1 colour or a FLESH_RAMP colour, and the
sheet shows the recommended cell with v1 only (plaster_warm standing in for
flesh), so the CEO sees what v2 buys. Scenes are re-quantised to v1 plus
the candidate ramp, so the pink survives the light stand-in.

Faction contract (ART-BIBLE §6, BESTIARY §2.1): chrome in steel_blue (0-5
shadow, 11-15 highlight, white specular dot), flesh in the candidate pink,
no military_green (the world's) and no khaki_olive (the Reich's); the only
flag_red on him is the US-flag patch (D12). Trousers are plaster_warm (pale
"suntan" khaki) so the body stays the light mass the value plan needs.

NO FONTS. The sprites carry no text and nothing here calls ImageFont; the
sheet is HTML, its labels are the browser's text (tools/art/sheetlib.py).
tests/test_gen_legion.py keeps it so.

Outputs (work/ is gitignored):
    work/art/enemies/legion/SDLT_<cell>_<frame><rot>.png   RGBA, hard alpha,
        grAb offsets as gen_rig (body axis, feet sunk FEET_SINK px)
    work/art/enemies/legion/SDLT_<rec>_A1_v1only.png       the palette question
    work/art/enemies/legion/lineup_<cell>_<scene>.png      1x, MAP01 walls
    work/art/enemies/legion/metrics.json
    work/art/enemies/legion/flesh_ramp_candidate.json
    docs/art/previews/<stamp>_F5_legion-trooper-sweep.html  (the sheet)

Light model: gen_enemy.py's stand-in (RGB x L/224, re-quantised). NOT
VERIFIED against GZDoom's light tables. Rotation order and grAb offsets are
gen_rig's, checked by hand against r_things.c, NOT in the engine.
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
import gen_enemy as flat  # noqa: E402  (light stand-in, far view, silhouette, flash)
import rig_core as core  # noqa: E402  (the shared rig: primitives, IK, renderer, output)
import palette as palgen  # noqa: E402  (the ramp rule, for the candidate flesh ramp)
import sheetlib  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "legion"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
RIG_DIR = PROJECT_ROOT / "work" / "art" / "enemies" / "rig"     # the Reich rifleman, read only
TEXTURES = PROJECT_ROOT / "assets" / "textures" / "soviet_base"
FLATS = PROJECT_ROOT / "assets" / "flats" / "soviet_base"

SPRITE = "SDLT"                 # BESTIARY §4, MOD-SPEC §6.3
SEED = 101                      # DoomEdNum 21101; only the trousers' grain uses it
FEET_SINK = core.FEET_SINK
DOOM_HEIGHT = 56                # actor Height (BESTIARY §4) = px at 1:1
STAND, AIM = core.STAND, core.AIM
SS = core.SS

# ================================================================== palette
# The Legion's pink is palette v2's `flesh_pink` (D45, CEO 2026-10-14),
# read from docs/art/palette.json through palette.ramp_colours(). The sweep
# drew it as a local CANDIDATE with these endpoints (a near-black with a red
# cast, so the dark end still reads as flesh in sector light 96, and a pale
# salmon pink at luma ~200 for the Legion's 0.72-0.80 body value); D45 took
# them unchanged into palette.py. They stay here only to prove the official
# ramp is the candidate the CEO saw, colour for colour: if palette.json ever
# disagreed, every sweep PNG would stop being reproducible, so the module
# refuses to load (tests/test_gen_legion.py checks the same).
FLESH = "flesh_pink"
FLESH_DARK = (24, 10, 10)
FLESH_LIGHT = (242, 190, 180)
FLESH_STEPS = palgen.RAMP_STEPS


def candidate_ramp() -> list[tuple[int, int, int]]:
    """The sweep's candidate, rebuilt with palette.py's one ramp rule."""
    return [tuple(c) for c in palgen.ramp_rule(FLESH_DARK, FLESH_LIGHT, FLESH_STEPS)]


def flesh_ramp() -> list[tuple[int, int, int]]:
    """The official palette v2 ramp `flesh_pink` (D45), darkest first."""
    return palgen.ramp_colours(FLESH)


if flesh_ramp() != candidate_ramp():        # pragma: no cover - a palette.json regression
    raise RuntimeError("palette v2 flesh_pink differs from the Legion sweep's candidate ramp")

core.register_ramp(FLESH, flesh_ramp())     # the core's materials can name it (core.ramp reads v1 only)


def ramp(name: str) -> list[tuple[int, int, int]]:
    return core.ramp(name)


def palette_v1() -> list[tuple[int, int, int]]:
    return [tuple(c) for c in artlib.load_palette()["colours"]]


def palette_ext() -> list[tuple[int, int, int]]:
    """Palette v1 plus flesh_pink: what the SWEEP's scenes were quantised to
    (kept, so the sweep reproduces byte for byte). The full set's scenes use
    palette v2 whole (palette_v2)."""
    return palette_v1() + flesh_ramp()


def palette_v2() -> list[tuple[int, int, int]]:
    """Palette v2, 226 colours (D45): v1 as its exact prefix, then the four added ramps."""
    return palgen.colours(2)


def quantize_ext(rgb: np.ndarray) -> np.ndarray:
    return core.quantize_to(rgb, palette_ext())


def lit(rgb: np.ndarray, light: int) -> np.ndarray:
    """gen_enemy's light stand-in, re-quantised to v1 + the candidate ramp."""
    return core.lit(rgb, light, palette_ext())


# ================================================================ materials
Mat = core.Mat                  # spans, shading ("lambert" | "chrome"), cloth, lift


# The Legion is the light faction (BESTIARY §2.1: body 0.72-0.80): flesh and
# cloth sit this much above the rig's base values, which were set for the Reich.
FLESH_LIFT = 0.14
TROUSER_LIFT = 0.10

# Chrome skips the middle of steel_blue on purpose: BESTIARY §2.1 gives the
# shadow 0-5 and the highlight 11-15, and the jump is what reads as polish.
MATERIALS: dict[str, Mat] = {
    "chrome": Mat((("steel_blue", 0, 5), ("steel_blue", 11, 15), ("white",)), "chrome"),
    "flesh": Mat(((FLESH, 3, 15),), lift=FLESH_LIFT),
    "void": Mat((("black",), (FLESH, 0, 2))),
    "teeth": Mat((("plaster_warm", 9, 15), ("white",))),
    "trouser": Mat((("plaster_warm", 5, 15),), cloth=True, lift=TROUSER_LIFT),
    "boot": Mat((("black",), ("steel_blue", 0, 4))),
    "belt": Mat((("black",), ("steel_blue", 1, 6))),
    "gunmetal": Mat((("black",), ("steel_blue", 1, 8))),
    "wood": Mat((("rust_brown", 3, 10),)),
    "band": Mat((("flag_red", 5, 11),)),
}
# The palette question: the same figure with v1 only, plaster_warm standing
# in for the flesh it does not have.
MATERIALS_V1 = {**MATERIALS,
                "flesh": Mat((("plaster_warm", 3, 15),), lift=FLESH_LIFT),
                "void": Mat((("black",), ("plaster_warm", 0, 2)))}

# Chrome environment (world y up): reflection rays above the horizon see
# sky, below it ground, darkest right under the horizon line. This sweep's
# values became the core's default (rig_core.Chrome); named here so a
# Legion round can tune them without touching another enemy.
CHROME = core.Chrome(horizon=-0.60, sky_lo=0.80, sky_hi=1.0, ground_lo=0.04, ground_span=0.30,
                     ground_fade=0.8, spec_cos=0.90, key=0.22, ao=0.5)
VALUE_SHIFT = 0.0               # gen_rig darkens the Reich by 0.26; the Legion is light


# ================================================================== the cells
@dataclass(frozen=True)
class Cell:
    key: str
    face: str           # "smooth" | "grin" | "visor"
    torso: str          # "cuirass" | "bare"
    shoulders: str      # "pauldron" | "pads"
    title: str


CELLS = (
    Cell("A", "smooth", "cuirass", "pauldron", "Brief: M1, smooth eyeless face, muscle cuirass, bare arms"),
    Cell("B", "grin", "cuirass", "pauldron", "As A, a grin: eye pits and white teeth"),
    Cell("C", "smooth", "cuirass", "pads", "As A, chrome football pads: the broad shoulders"),
    Cell("D", "visor", "cuirass", "pauldron", "As A, a chrome visor over the eyes"),
    Cell("E", "smooth", "bare", "pauldron", "As A, no cuirass: bare pink torso, chrome harness"),
    Cell("F", "grin", "cuirass", "pads", "C and B: football pads and the grin"),
)
CELL = {c.key: c for c in CELLS}


@dataclass(frozen=True)
class Pose:
    key: str
    title: str
    foot_l: tuple       # ankle targets, model space (x = figure's LEFT, z = forward)
    foot_r: tuple
    bob: float
    carry: str          # "high" (across the chest) | "aim" | "free" (he has let go of the shotgun)
    flash: bool
    canvas: core.Canvas
    # The full set's posing (D48); every default leaves the sweep's figure as it was.
    gun_tilt: float = 0.0        # small per-frame wobble of the carried shotgun (walk, pain)
    lean: float = 0.0            # degrees, upper body back about the waist
    head_pitch: float = 0.0      # degrees, chin up about the neck
    hand_l: tuple | None = None  # carry "free": hand targets, before lean
    hand_r: tuple | None = None
    gun_at: tuple | None = None  # carry "free": (butt, along, up), final model space
    roll: float = 0.0            # degrees, the whole figure falls to his left about ROLL_PIVOT


ANKLE_Y = core.ANKLE_Y
POSES = {
    "A": Pose("A", "stand", (3.9, ANKLE_Y, 0.4), (-3.9, ANKLE_Y, 0.0), 0.0, "high", False, STAND),
    "F": Pose("F", "fire", (4.1, ANKLE_Y, -1.6), (-3.9, ANKLE_Y, 2.2), -0.4, "aim", True, AIM),
}
VIEWS = (("A", 1), ("A", 2), ("A", 3), ("F", 1), ("F", 3))   # what each cell shows

# Body. Heavier than the rifleman (BESTIARY §4: "wider at the shoulders").
HIP_Y = core.HIP_Y
THIGH, SHIN = core.THIGH, core.SHIN
UPPER_ARM, FOREARM = 9.4, 8.8
SHOULDER_X, SHOULDER_Y = 8.0, 40.4
WAIST_Y, CHEST_Y = 28.8, 41.0
TORSO_R0, TORSO_R1, TORSO_KZ = 7.2, 8.8, 0.70
PAULDRON = ((0.4, 40.8), (3.4, 2.3, 3.3))       # (x offset from SHOULDER_X, y), radii
PAD = ((1.2, 41.4), (5.0, 2.6, 4.8))
PAD_FLAP = ((2.6, 39.0), (3.0, 2.6, 4.0))

# Pump shotgun, BESTIARY §4: "a short pump shotgun held high across the chest".
GUN_LEN = 27.0
GUN_HIGH_BUTT = (-8.4, 33.2, 3.4)
GUN_HIGH_DIR = (0.90, 0.26, 0.36)               # rises to his left, a little forward
GUN_AIM_BUTT = (-4.6, 39.2, 3.8)
GRIP_R, GRIP_L = 6.5, 18.0                      # stock wrist, pump (along the gun)
FLASH_SIZE = 7.0                                # a shotgun's flash, a little over the rifle's 6

# Posing (the full set, D48): the pivots and groups gen_rig.py uses for the
# rifleman, on the trooper's proportions.
NECK = core.V(0.0, 42.0, -0.4)                  # chin pivot: the bull neck's middle
UPPER = {"upper", "arm", "head", "helmet"}      # what leans with the torso
ALL_BODY = UPPER | {"leg_l", "leg_r", "seat", "stump"}
ROLL_PIVOT = core.V(3.9, 0.0, 0.0)              # his left sole: he falls to his left over it
SLIDE = 30.0                                    # x shift at a full fall, so the corpse lies across the axis


def gun_frame(pose: Pose):
    up = core.V(0, 1, 0)
    if pose.carry == "high":
        butt = core.V(*GUN_HIGH_BUTT) + core.V(0, pose.bob, 0)
        u = core.V(*GUN_HIGH_DIR) + core.V(0, pose.gun_tilt, 0)
    elif pose.carry == "aim":
        butt = core.V(*GUN_AIM_BUTT) + core.V(0, pose.bob, 0)
        u = core.V(0.06, np.tan(np.deg2rad(core.PITCH_DEG)), 1.0)
    else:                       # "free": he has let go, the shotgun falls on its own
        butt, u, up = (np.asarray(x, float) for x in pose.gun_at)
    u = u / np.linalg.norm(u)
    v = up - (up @ u) * u
    v = v / np.linalg.norm(v)
    return butt, u, v, np.cross(u, v)


def build_model(cell: Cell, pose: Pose) -> tuple[list, dict]:
    """The trooper as gen_rig primitives in model space (feet on y=0,
    facing +z, +x the figure's LEFT), posed. Returns (prims, anchors)."""
    P: list = []
    anchors: dict = {}
    bob = pose.bob

    def add(grp, prim):
        prim.grp = grp
        P.append(prim)
        return prim

    E, RC, CC, BX = core.ellipsoid, core.rcone, core.ccone, core.box

    def label(start: int, limb: str, side: int) -> None:
        """Tag what was added since `start` as one limb of one side (render-neutral)."""
        for prim in P[start:]:
            prim.limb, prim.side = limb, side

    # ---------------------------------------------------------------- legs
    for side, foot, grp in ((1, pose.foot_l, "leg_l"), (-1, pose.foot_r, "leg_r")):
        start = len(P)
        hip = core.V(side * 3.5, HIP_Y + bob, 0.0)
        knee, ankle = core.two_bone(hip, foot, THIGH, SHIN, core.V(0, 0, 1))
        add(grp, RC("trouser", 0.62, hip, knee, 3.0, 2.6))
        add(grp, RC("trouser", 0.58, knee, ankle + core.V(0, 3.4, 0), 2.6, 2.3))
        add(grp, E("trouser", 0.56, tuple(ankle + core.V(0, 4.4, 0.1)), (2.7, 1.3, 2.6)))   # bloused over the boot
        add(grp, RC("boot", 0.55, ankle + core.V(0, 4.0, 0), ankle, 2.25, 2.1))
        add(grp, BX("boot", 0.35, (ankle[0], ankle[1] - 1.15, ankle[2] + 1.4), (1.75, 1.1, 3.1), rnd=0.6))
        label(start, "leg", side)
    add("seat", E("trouser", 0.60, (0, HIP_Y + 1.0 + bob, -0.2), (6.6, 3.6, 4.3), tag="seat"))

    # ---------------------------------------------------------------- torso
    belt_z = (TORSO_R0 + 0.4) * 0.74
    add("upper", CC("belt", 0.45, 26.9 + bob, 28.9 + bob, TORSO_R0 + 0.4, TORSO_R0 + 0.35, kz=0.74, tag="belt"))
    add("upper", BX("chrome", 0.6, (0, 27.9 + bob, belt_z + 0.15), (1.2, 0.9, 0.35), tag="belt"))      # buckle
    ty0, ty1 = WAIST_Y + bob, CHEST_Y + bob
    torso_mat = "chrome" if cell.torso == "cuirass" else "flesh"
    add("upper", core.Prim("cappedcone", torso_mat, 0.66, core.V(0, (ty0 + ty1) / 2, -0.2), h=(ty1 - ty0) / 2,
                          r1=TORSO_R0, r2=TORSO_R1, scale=core.V(1.0, 1.0, TORSO_KZ), tag="torso"))

    def torso_z(x, y):
        r = TORSO_R0 + (TORSO_R1 - TORSO_R0) * (y - ty0) / (ty1 - ty0)
        return TORSO_KZ * np.sqrt(max(r * r - x * x, 0.0)) - 0.2

    for side in (1, -1):        # pectorals: the muscle cuirass (or the muscle)
        add("upper", E(torso_mat, 0.70, (side * 3.5, 37.4 + bob, torso_z(side * 3.5, 37.4 + bob) - 1.0),
                       (3.7, 2.7, 2.0)))
    for y in (33.4, 31.0):      # abdominal plates
        for side in (1, -1):
            add("upper", E(torso_mat, 0.64, (side * 1.7, y + bob, torso_z(side * 1.7, y + bob) - 0.55),
                           (1.8, 1.15, 0.9)))
    if cell.torso == "cuirass":
        add("upper", CC("chrome", 0.58, 28.4 + bob, 30.0 + bob, TORSO_R0 + 0.9, TORSO_R0 + 0.2, kz=0.74))  # flared lip
    else:   # chrome harness crossing the bare chest
        for side in (1, -1):
            a = (side * 5.6, 40.6 + bob)
            b = (-side * 3.4, 29.6 + bob)
            add("upper", RC("chrome", 0.6, (a[0], a[1], torso_z(*a) + 0.4), (b[0], b[1], torso_z(*b) + 0.45), 0.55))
        add("upper", E("chrome", 0.7, (0, 34.8 + bob, torso_z(0, 34.8 + bob) + 0.5), (1.1, 1.1, 0.5)))

    # --------------------------------------------------------- shoulders
    for side in (1, -1):
        if cell.shoulders == "pads":
            (dx, y), r = PAD
            add("upper", E("chrome", 0.7, (side * (SHOULDER_X + dx), y + bob, -0.3), r))
            (dx2, y2), r2 = PAD_FLAP
            add("upper", E("chrome", 0.66, (side * (SHOULDER_X + dx2), y2 + bob, -0.3), r2))
            out_c, out_r = (side * (SHOULDER_X + dx2), y2 + bob, -0.3), r2
        else:
            (dx, y), r = PAULDRON
            add("upper", E("chrome", 0.7, (side * (SHOULDER_X + dx), y + bob, -0.3), r))
            out_c, out_r = (side * (SHOULDER_X + dx), y + bob, -0.3), r
        if side == -1:          # the US-flag patch (D12): his RIGHT shoulder, as the US Army wears it
            cut_x = out_c[0] - 0.3 * out_r[0]           # keep the outer third of the shell
            add("upper", E("band", 0.6, out_c, tuple(np.asarray(out_r) + 0.18),
                           clip=[(core.V(1, 0, 0), cut_x), (core.V(0, 0, -1), 0.6)], tag="patch"))

    # ---------------------------------------------------------------- head
    head_off = core.V(0, bob, 0)
    if pose.carry == "aim":
        head_off = head_off + core.V(-1.2, -0.7, 0.7)     # cheek down on the stock
    hp = lambda x, y, z: tuple(core.V(x, y, z) + head_off)  # noqa: E731
    add("head", RC("flesh", 0.55, core.V(0, 40.0 + bob, -0.4), core.V(0, 44.3, 0.2) + head_off, 2.7, 2.4))   # bull neck
    add("head", E("flesh", 0.72, hp(0, 47.4, 0.8), (3.3, 3.8, 3.4)))           # skull
    add("head", E("flesh", 0.66, hp(0, 44.6, 1.6), (2.8, 2.0, 2.5)))           # lantern jaw
    if cell.face == "smooth":
        add("head", E("flesh", 0.80, hp(0, 48.3, 3.3), (2.8, 0.7, 0.9)))      # a brow and no eyes under it
        add("head", E("void", 0.4, hp(0, 44.3, 3.95), (1.2, 0.25, 0.4)))      # a line of a mouth
    elif cell.face == "grin":
        for sx in (1, -1):
            add("head", E("void", 0.0, hp(sx * 1.25, 47.6, 3.6), (0.8, 0.65, 0.55)))   # eye pits
        add("head", E("void", 0.1, hp(0, 44.5, 3.7), (2.3, 1.05, 0.9)))       # the open grin
        add("head", E("teeth", 0.9, hp(0, 44.7, 4.05), (2.1, 0.6, 0.6)))      # one row of white teeth
    else:   # visor: a chrome band round the face, over the eyes
        add("head", E("chrome", 0.7, hp(0, 47.7, 1.0), (3.75, 1.2, 3.65), clip=[(core.V(0, 0, -1), 0.4)]))
        add("head", E("void", 0.4, hp(0, 44.3, 3.95), (1.2, 0.25, 0.4)))
    # M1 "pot": a round bowl with an even lip, BESTIARY §4's 16-px tell
    hy = head_off[1]
    c = core.V(*hp(0, 0, 0))
    add("helmet", E("chrome", 0.7, hp(0, 49.6, 0.6), (5.0, 6.3, 5.4), clip=[(core.V(0, -1, 0), -(48.9 + hy))]))
    add("helmet", CC("chrome", 0.55, 48.5 + hy, 49.3 + hy, 5.9, 5.4, x=c[0], z=0.6 + c[2]))
    for sx in (1, -1):          # chin strap
        add("helmet", RC("belt", 0.4, hp(sx * 3.9, 48.6, 1.4), hp(sx * 2.3, 43.6, 2.2), 0.32))
    anchors["head"] = (c + core.V(0, 47, 1), "head")
    anchors["helmet"] = (c + core.V(0, 49.6, 0.6), "helmet")

    # ---------------------------------------------------------------- shotgun
    butt, u, v, w = gun_frame(pose)
    at = lambda s, hh=0.0, k=0.0: butt + u * s + v * hh + w * k  # noqa: E731
    add("gun", RC("wood", 0.5, at(0.6, -0.4), at(8.5, 0.15), 1.35, 0.8))                 # stock
    add("gun", RC("gunmetal", 0.5, at(8.0, 0.25), at(13.0, 0.25), 0.95, 0.9))           # receiver
    add("gun", RC("gunmetal", 0.55, at(12.5, 0.45), at(GUN_LEN, 0.45), 0.5, 0.45))      # barrel
    add("gun", RC("gunmetal", 0.4, at(13.0, -0.45), at(GUN_LEN - 3.0, -0.45), 0.42))    # magazine tube
    add("gun", RC("wood", 0.55, at(15.5, -0.5), at(20.5, -0.5), 0.95))                  # the pump
    anchors["muzzle"] = (at(GUN_LEN + 0.4, 0.45), "gun")
    anchors["gun"] = (at(GUN_LEN / 2, 0.0), "gun")

    # ---------------------------------------------------------------- arms
    if pose.carry == "free":
        grips = {1: core.V(*pose.hand_l), -1: core.V(*pose.hand_r)}
    else:
        grips = {-1: at(GRIP_R, -0.6), 1: at(GRIP_L, -1.0)}
    for side in (1, -1):
        start = len(P)
        sh = core.V(side * (SHOULDER_X + 0.2), SHOULDER_Y + bob, -0.4)
        pole = core.V(side * 1.0, -0.4, -0.7)
        elbow, wrist = core.two_bone(sh, grips[side], UPPER_ARM, FOREARM, pole)
        add("arm", RC("flesh", 0.66, sh, elbow, 2.75, 2.35))
        add("arm", RC("flesh", 0.62, elbow, wrist, 2.35, 2.0))
        fd = (wrist - elbow) / np.linalg.norm(wrist - elbow)
        if cell.torso == "bare":
            add("arm", RC("chrome", 0.65, wrist - fd * 3.4, wrist - fd * 0.8, 2.25, 2.15))   # bracers
        add("arm", E("flesh", 0.62, tuple(wrist + fd * 0.9 - v * 0.2), (1.4, 1.55, 1.4)))
        label(start, "arm", side)

    # ------------------------------------------------------------- posing
    # The full set's poses (gen_rig's order): chin, then the lean about the
    # waist, then the fall. The sweep's two poses take none of these.
    if pose.head_pitch:
        core.transform(P, anchors, {"head", "helmet"}, core.rot_x(pose.head_pitch), NECK + core.V(0, bob, 0))
    if pose.lean:
        waist = core.V(0, WAIST_Y + bob, 0)
        carried = {"gun"} if pose.carry != "free" else set()
        core.transform(P, anchors, UPPER | carried, core.rot_x(pose.lean), waist)
    if pose.roll:
        body = ALL_BODY | ({"gun"} if pose.carry != "free" else set())
        slide = core.V(-SLIDE * np.sin(np.deg2rad(pose.roll)), 0, 0)
        core.transform(P, anchors, body, core.rot_z(pose.roll), ROLL_PIVOT, slide)
        core.rest_on_floor(P, anchors, body)
    return P, anchors


# ================================================================== render
# The US flag (D12), 7x5 hard pixels: B canton, * star, R red, W white.
# Drawn canton-left; mirrored when he faces screen right, so the canton
# always leads, as on a US right-shoulder flag.
FLAG = (
    "BBBRRRR",
    "B*BWWWW",
    "BBBRRRR",
    "WWWWWWW",
    "RRRRRRR",
)
FLAG_COLOURS = {"B": ("steel_blue", 3), "*": ("plaster_warm", 15), "R": ("flag_red", 11),
                "W": ("plaster_warm", 14)}
PATCH_MIN_PX = 4                # visible patch pixels needed before the flag is stamped
PATCH_SEARCH = 5                # px the stamp may slide to sit on the figure


def flag_pixels(mirror: bool) -> list[tuple[int, int, tuple[int, int, int]]]:
    out = []
    for j, row in enumerate(FLAG):
        for i, ch in enumerate(row[::-1] if mirror else row):
            name, k = FLAG_COLOURS[ch]
            out.append((i, j, artlib.ramp(name)[k]))
    return out


def flag_draw(rgba: np.ndarray, x0: int, y0: int, mirror: bool) -> None:
    for i, j, col in flag_pixels(mirror):
        rgba[y0 + j, x0 + i] = (*col, 255)


# The flag as a core insignia: on the patch's visible centre, slid up to
# PATCH_SEARCH px so it sits on opaque pixels, when his right side (model
# -x) is not turned away; mirrored when he faces screen right.
FLAG_INSIGNIA = core.Insignia("patch", (len(FLAG[0]), len(FLAG)), flag_draw, outward=(-1.0, 0.0, 0.0),
                              min_px=PATCH_MIN_PX, search=PATCH_SEARCH, mirror_facing_right=True)


def stamp_flag(rgba: np.ndarray, pid: np.ndarray, prims: list, rotation: int) -> bool:
    """The flag on the patch (FLAG_INSIGNIA). Returns whether it was stamped."""
    return core.stamp_insignia(rgba, pid, prims, rotation, FLAG_INSIGNIA)


def render(cell: Cell, frame: str, rotation: int, mats: dict | None = None, seed: int = SEED) -> np.ndarray:
    """One sprite, RGBA (h, w, 4)."""
    mats = MATERIALS if mats is None else mats
    pose = POSES[frame]
    prims, anchors = build_model(cell, pose)
    return core.render(prims, rotation, pose.canvas, mats, seed=seed, value_shift=VALUE_SHIFT,
                       insignia=(FLAG_INSIGNIA,), muzzle=anchors["muzzle"][0] if pose.flash else None,
                       flash_size=FLASH_SIZE, chrome=CHROME, what=f"{cell.key} {frame}{rotation}")


# ================================================================== output
def lump_name(cell: Cell, frame: str, rotation: int) -> str:
    """Draft file name: SDLT_<cell>_<frame><rot> (the lump is SDLT<frame><rot>)."""
    return f"{SPRITE}_{cell.key}_{frame}{rotation}"


def save_sprite(rgba: np.ndarray, path: Path, cv: core.Canvas) -> Path:
    return core.save_sprite(rgba, path, cv)


def wall_rgb(lump: str) -> np.ndarray:
    path = TEXTURES / f"{lump}.png"
    if not path.is_file():
        path = FLATS / f"{lump}.png"
    with Image.open(path) as im:
        return np.asarray(im.convert("RGB"), dtype=np.uint8)


# Scenes: where MAP01 puts the Legion (docs/levels/MAP01-zarya-7.md: the
# Legion is first met in the hangar, Z6). Hangar walls are SDCONC1 with
# SDCONC2 framing D4 and the bay mouth; light 176, 192 under lamps, 144 in
# the bay shadows and under the catwalk.
SCENES = (
    # key, wall, light, what it stands for
    ("L1", "SDCONC1", 176, "hangar wall"),
    ("L2", "SDCONC1", 144, "bay shadow, under the catwalk (worst case)"),
    ("L3", "SDCONC2", 176, "red stripe framing D4"),
    ("L4", "SDSTEL1", 176, "catwalk front, cradle flank"),
    ("L5", "SDCRAT1", 144, "crate cover"),
)
WORST = "L2"


def lineup(figures: list[tuple[np.ndarray, int, int]], wall: str, light: int, width: int) -> np.ndarray:
    """core.lineup with this file's walls (assets/) and quantiser (v1 + the
    candidate ramp): sprites side by side by their own offsets, MAP01 wall
    over SDFLR2."""
    return core.lineup(figures, wall, light, width, load=wall_rgb, palette=palette_ext())


def measure(sprite: np.ndarray) -> dict:
    """Size and value; gap_<scene> is |body - wall| luma under that scene's
    light (the stand-in), as gen_enemy and gen_rig measure the rifleman.
    mass_luma is the median: the light mass without the black boots."""
    a = sprite[..., 3] > 0
    ys, xs = np.nonzero(a)
    body = flat.luma(sprite[..., :3])[a]
    out = {"height_px": int(ys.max() - ys.min() + 1), "width_px": int(xs.max() - xs.min() + 1),
           "body_luma": round(float(body.mean()), 1), "mass_luma": round(float(np.median(body)), 1)}
    f = lambda L: min(1.0, L / flat.LIGHT_FULL)  # noqa: E731
    for key, wall, light, _ in SCENES:
        out[f"gap_{key}"] = round(abs(float(body.mean()) - float(flat.luma(wall_rgb(wall)).mean())) * f(light), 1)
    out["worst_gap"] = min(out[f"gap_{k}"] for k, *_ in SCENES)
    return out


def rifleman() -> tuple[np.ndarray, int, int] | None:
    """The Reich rifleman's rig frame A1 (D38), if gen_rig has been run."""
    path = RIG_DIR / "SDRRA1.png"
    if not path.is_file():
        return None
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGBA")).copy()
    gx, gy = core.read_grab(path)
    return arr, gx, gy


def comparison_figures(sprite: np.ndarray) -> tuple[list, list[str]]:
    figs = [(sprite, *core.grab_offsets(STAND))]
    labels = ["SDLTA1 (this cell)"]
    for name, label in (("SPOSA1", "SPOSA1, Freedoom shotgun guy: today's placeholder"),
                        ("POSSA1", "POSSA1, Freedoom zombieman: the rifleman's placeholder")):
        fd = core.freedoom_sprite(name)
        if fd:
            figs.append(fd)
            labels.append(label)
    rr = rifleman()
    if rr:
        figs.append(rr)
        labels.append("SDRRA1, our Reich rifleman (rig, D38)")
    return figs, labels


def build_all(out_dir: Path = OUT_DIR, seed: int = SEED) -> tuple[dict, dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sprites, metrics = {}, {}
    for c in CELLS:
        for frame, rot in VIEWS:
            rgba = render(c, frame, rot, seed=seed)
            save_sprite(rgba, out_dir / f"{lump_name(c, frame, rot)}.png", POSES[frame].canvas)
            sprites[(c.key, frame, rot)] = rgba
            print(lump_name(c, frame, rot), flush=True)
        metrics[c.key] = measure(sprites[(c.key, "A", 1)])
        figs, _ = comparison_figures(sprites[(c.key, "A", 1)])
        for key, wall, light, _ in SCENES:
            sc = lineup(figs, wall, light, 64 * len(figs))
            Image.fromarray(sc, "RGB").save(out_dir / f"lineup_{c.key}_{key}.png", optimize=True)
    rec = CELL[RECOMMENDED]
    v1 = render(rec, "A", 1, MATERIALS_V1, seed)
    save_sprite(v1, out_dir / f"{lump_name(rec, 'A', 1)}_v1only.png", STAND)
    sprites[("v1", "A", 1)] = v1
    metrics["v1only_" + rec.key] = measure(v1)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    (out_dir / "flesh_ramp_candidate.json").write_text(json.dumps(
        {"name": FLESH, "dark": FLESH_DARK, "light": FLESH_LIGHT, "steps": FLESH_STEPS,
         "gamma": palgen.RAMP_GAMMA,
         "status": "the sweep's candidate; since D45 it is palette v2's flesh_pink, colour for colour",
         "colours": [list(c) for c in flesh_ramp()]}, indent=1) + "\n", encoding="utf-8")
    return sprites, metrics


# ==================================================================== sheet
RECOMMENDED = "C"
# Written after looking at the sweep once (PIPELINE stage 2).
VERDICT = [
    "WHY C. The chrome football pads are the one change that makes him read as the Liberty Legion at "
    "every distance: they give BESTIARY 4's tell (wider at the shoulders than the rifleman) to the shape, "
    "not only to the colour, and they are American without a word or a symbol. Under them he keeps the "
    "brief: chrome M1 pot, chrome muscle cuirass (a Roman legion's armour for a 'Legion' of 'Liberty'), "
    "bare pink arms, the shotgun high across the chest. The smooth eyeless face pairs him with the eyeless "
    "rifleman: both factions are alien, neither has eyes you can meet. F (the same pads with the grin) is "
    "the valid alternative if you want him more inhuman; the grin reads at 1x, but it sits close to a "
    "cartoon and D11 asks for serious, so not as the default. D's visor is barely a band at 1x; E (bare "
    "torso) is the pinkest and the least armoured, closest to a man in trousers; A and B are C and F with "
    "smaller shoulders.",
    "WHAT WORKS. Value, the faction plan: the light mass (median luma about 181 in every cell, khaki "
    "trousers 187, chrome about 180, flesh about 182) sits well above SDCONC1 (147) and far above our Reich "
    "rifleman (about 70): the two infantries cannot be confused, and at 16 px the trooper is a T (wide "
    "shoulders, legs apart) where the rifleman is a bell (the greatcoat). The faction contract holds: "
    "steel_blue chrome with its middle skipped, pink flesh, no military_green, no khaki_olive, the flag "
    "the only flag_red. Beside Freedoom's placeholders he is the same height and reads as a figure of his "
    "own.",
    "WHAT DOES NOT, HONESTLY. He is slimmer than Freedoom's shotgun guy even with the pads; 'heavy' is "
    "more a promise than a fact, and a wider rig (bigger thighs, a thicker waist) is one parameter round. "
    "The mean body luma (about 164, the black boots and the gun pull it down) gives a worst gap of about "
    "11 on SDCONC1 at light 144, lower than the rifleman's 13 to 19 on SDSTEL1: he separates by being "
    "lighter than a light wall, which is the narrower margin; under the hangar's 176 to 192 the gap grows. "
    "The flag is 7x5, larger than a real patch and partly off the shoulder in the front view, on purpose so "
    "it reads (the rifleman's armband has the same convention). The firing frame from the front hides the "
    "face behind the flash, as the rifleman's does. Up close (4x) it is the rig's rendered-mannequin look, "
    "the same quality the CEO accepted for the rifleman.",
    "THE PALETTE. Palette v1 has no pink; the sweep uses a candidate ramp for 16 reserved slots (section "
    "4). In v1 only, plaster_warm stands in: he becomes a cream-skinned man, the flesh and the trousers "
    "merge, and 'pink flesh' (LORE, BESTIARY 2.1) is lost. Recommendation: add the ramp as palette v2.",
]
RIG_NOTE = [
    "YES, THE METHOD SERVES HIM, AND THESE SIX CELLS PROVE IT: every cell here is gen_rig.py's primitives "
    "(ellipsoids, round cones, capped cones, boxes), its two-bone IK for legs and arms, its rotations, "
    "camera, Freedoom reader, grAb convention and canvases, imported unchanged. Doom's SPOS layout is the "
    "same 21 frames as POSS (BESTIARY 4: same budget, 49 images), so gen_rig's frame plan, death fall and "
    "gib machinery carry over as they are.",
    "WHAT GEN_RIG.PY LACKS (to be generalised before the full set, not edited in this task): (1) a chrome "
    "shading. Its banded Lambert makes chrome grey plastic; this sweep reflects a sky/horizon/ground "
    "environment with a hard specular dot, about 15 lines. (2) Materials as a parameter: its reduce() and "
    "to_rgba() read gen_rig's own MATERIALS, so a second figure cannot use them; this file carries copies "
    "that take the materials. (3) VALUE_SHIFT -0.26 and the NO_SHIFT/CLOTH sets are the Reich's; the "
    "Legion is the light faction and needs none. (4) build_model() is the rifleman; the figure should be a "
    "per-enemy function on a shared skeleton. (5) The armband stamp is hard-wired (stamp_symbol calls "
    "gen_enemy.stamp_armband); the Legion needs the US flag, mirrored so the canton leads. (6) The carry: "
    "rifle_frame knows hip and aim, the trooper needs 'high across the chest' and a pump. (7) The gib's "
    "CHUNK_MATS are olive; the Legion bleeds pale plaster_warm 10-14 (BESTIARY 2.1). (8) Tics: SPOS walks "
    "at 3 tics a frame and fires 10/10/10 (BESTIARY 4), the GIFs hard-code POSS's 4 and 10/8/8. (9) "
    "gen_enemy.lit() re-quantises scenes to v1, which would erase the pink until palette v2 exists.",
    "PROPOSAL: once a cell is chosen, split gen_rig.py into a shared core (march, reduce, rgba, stamps, "
    "frame plan, GIFs, sheet) and one figure module per enemy, so the Legion's 49 lumps and the next three "
    "enemies of D35 are figure modules only. That is a refactor of an approved tool, so it is the PM's to "
    "commission, with tests/test_gen_rig.py as its tripwire.",
]
CEO_ASK = [
    "Pick a cell (recommended C; F if you want him more inhuman). Fixes can be named on top, each a "
    "parameter: a heavier build, a different face on C's body, the flag smaller or on the chest.",
    "Approve the pink: the candidate flesh ramp becomes palette v2 (16 of the 94 reserved slots, no v1 "
    "colour changes). Without it the Legion is cream, not pink.",
    "Then the full set (walk, aim, fire, pain at 8 rotations; death and gib) is rendered on the rig, as the "
    "rifleman's was, for your gate in GZDoom.",
]
EXTRA_CSS = """
.strip{display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;margin-bottom:10px}
.cap{font:11px Menlo,monospace;color:var(--mute);text-align:center;margin-top:3px}
.cap b{color:var(--ink)}
img.px{background:transparent;border:none}
.tile{display:flex;flex-direction:column;align-items:center}
.cell{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:14px;margin:0 0 18px}
.cell.rec{border-color:var(--warn);box-shadow:0 0 0 2px var(--warn) inset}
.cell h3 .tag{font:12px Menlo,monospace;color:var(--warn);margin-left:10px}
.num{font:12px Menlo,monospace;color:var(--mute);margin:0 0 10px}
.verdict p{max-width:980px;margin:6px 0}
.swatch{display:inline-block;width:22px;height:22px;border:1px solid var(--line)}
"""
NEUTRAL = artlib.ramp("concrete_cold")[16]


def tile(src: str, w: int, h: int, zoom: int, cap: str, sub: str = "") -> str:
    return core.tile(src, w, h, zoom, cap, sub)


def sprite_tile(arr: np.ndarray, zoom: int, cap: str, sub: str = "") -> str:
    return tile(core.png_uri(core.on_bg(arr, NEUTRAL)), arr.shape[1], arr.shape[0], zoom, cap, sub)


def strip(items) -> str:
    return '<div class="strip">' + "".join(items) + "</div>"


def silhouette_rgb(sprite: np.ndarray) -> np.ndarray:
    sil = flat.silhouette(sprite)
    return np.where(sil[..., None], 0, 235).astype(np.uint8).repeat(3, -1)


ROT_NAMES = {1: "front", 2: "three-quarter", 3: "his left side"}
NAMES = {"smooth": "smooth, eyeless", "grin": "grin: eye pits, white teeth", "visor": "chrome visor",
         "cuirass": "chrome muscle cuirass", "bare": "bare pink, chrome harness",
         "pauldron": "small chrome pauldrons", "pads": "chrome football pads"}


def build_sheet(sprites: dict, metrics: dict, stamp: str, out_dir: Path = PREVIEW_DIR,
                lineup_dir: Path = OUT_DIR) -> Path:
    S = []
    # 1. the table
    rows = []
    for c in CELLS:
        m = metrics[c.key]
        rows.append([c.key + (" (rec.)" if c.key == RECOMMENDED else ""), NAMES[c.face], NAMES[c.torso],
                     NAMES[c.shoulders], f"{m['height_px']} x {m['width_px']}", m["body_luma"],
                     m["gap_L1"], m["gap_L2"], m["gap_L3"], m["gap_L4"], m["gap_L5"]])
    body = sheetlib.table(["cell", "face", "torso", "shoulders", "h x w px", "body luma",
                           "gap L1", "gap L2", "gap L3", "gap L4", "gap L5"], rows, numeric_from=4)
    conc = float(flat.luma(wall_rgb("SDCONC1")).mean())
    rr = rifleman()
    rr_luma = f"{core.measure(rr[0])['body_luma']:.0f}" if rr else "n/a"
    body += ("<p class=\"lead\">Every cell keeps BESTIARY §4's constants: chrome M1 helmet, pink flesh, pale "
             "trousers and dark boots, a pump shotgun held high across the chest, the US flag on his right "
             f"shoulder. Body luma is the mean over every opaque pixel of frame A1 (SDCONC1 measures {conc:.0f}, "
             f"our Reich rifleman {rr_luma}); gap is |body - wall| under the scene's light. Scenes: "
             + html.escape(" · ".join(f"{k} {w} at {L}, {what}" for k, w, L, what in SCENES)) + ".</p>")
    S.append(("1 · Six cells, one decision: what the Legion trooper looks like", "", body))

    # 2. the cells
    figs_labels = comparison_figures(sprites[(CELLS[0].key, "A", 1)])[1]
    body = ""
    for c in CELLS:
        m = metrics[c.key]
        rec = c.key == RECOMMENDED
        views = [sprite_tile(sprites[(c.key, f, r)], 4 if POSES[f].canvas is STAND else 3,
                             f"{SPRITE}{f}{r}", ("firing, " if f == "F" else "") + ROT_NAMES[r]) for f, r in VIEWS]
        views += [sprite_tile(sprites[(c.key, "A", r)], 1, f"{SPRITE}A{r} 1x") for r in (1, 2, 3)]
        lines = []
        for key, wall, light, what in SCENES:
            with Image.open(lineup_dir / f"lineup_{c.key}_{key}.png") as im:
                sc = np.asarray(im.convert("RGB"))
            lines.append(tile(core.png_uri(sc), sc.shape[1], sc.shape[0], 1, f"{key} 1x", f"{wall} @{light}"))
        with Image.open(lineup_dir / f"lineup_{c.key}_{WORST}.png") as im:
            worst = np.asarray(im.convert("RGB"))
        big = tile(core.png_uri(worst), worst.shape[1], worst.shape[0], 2, f"{WORST} at 2x for the eye",
                   "left to right: this cell, SPOSA1, POSSA1, SDRRA1")
        farv = flat.far(worst)
        sil = silhouette_rgb(sprites[(c.key, "A", 1)])
        extra = [tile(core.png_uri(farv), farv.shape[1], farv.shape[0], 4, f"{WORST} at game distance /4", "shown 4x"),
                 tile(core.png_uri(sil), sil.shape[1], sil.shape[0], 4, "16 px silhouette", "shown 4x")]
        body += (f'<div class="cell{" rec" if rec else ""}"><h3>{c.key} · {html.escape(c.title)}'
                 + ('<span class="tag">RECOMMENDED</span>' if rec else "") + "</h3>"
                 + f'<p class="num">{m["height_px"]} x {m["width_px"]} px · body luma {m["body_luma"]:.0f} · '
                 + " ".join(f"gap {k} {m['gap_' + k]:.0f}" for k, *_ in SCENES) + "</p>"
                 + strip(views) + strip(lines) + strip([big] + extra) + "</div>")
    S.append(("2 · The cells: frame A at rotations 1, 2, 3 and frame F (fire) at 1 and 3; then at 1x on MAP01's walls",
              "Sprites at 4x (fire at 3x) on neutral grey, then true 1x. The lineups are true 1x: this cell, "
              "then " + html.escape(", then ".join(figs_labels[1:])) + ", each standing by its own offsets as "
              "the engine places it, wall over SDFLR2, both in the scene's light (gen_enemy's stand-in, NOT "
              "VERIFIED against GZDoom). Freedoom is shown for scale only; no pixel of it is used.", body))

    # 3. the faction tell
    sils = [tile(core.png_uri(silhouette_rgb(sprites[(c.key, "A", 1)])), *silhouette_rgb(sprites[(c.key, "A", 1)]).shape[1::-1],
                 5, c.key) for c in CELLS]
    if rr:
        s = silhouette_rgb(rr[0])
        sils.append(tile(core.png_uri(s), s.shape[1], s.shape[0], 5, "SDRR", "the Reich rifleman"))
    pair = []
    for key, wall, light, _ in (SCENES[1], SCENES[0]):
        figs = [(sprites[(RECOMMENDED, "A", 1)], *core.grab_offsets(STAND))] + ([rr] if rr else [])
        sc = lineup(figs, wall, light, 64 * len(figs))
        fv = flat.far(sc)
        val = np.repeat(flat.luma(fv)[..., None].clip(0, 255).astype(np.uint8), 3, -1)
        pair += [tile(core.png_uri(fv), fv.shape[1], fv.shape[0], 5, f"{key} /4", f"{RECOMMENDED} and SDRR"),
                 tile(core.png_uri(val), val.shape[1], val.shape[0], 5, f"{key} /4, value only")]
    S.append(("3 · The faction tell (BESTIARY §10, the one real silhouette collision)",
              "At 16 px the six cells and the rifleman, then the recommended cell beside the rifleman at game "
              "distance in colour and in value only. BESTIARY §10: the two infantries are told apart by value "
              "first, then the weapon line and the shoulders, not by the helmet.",
              strip(sils) + strip(pair)))

    # 4. palette question
    sw = "".join(f'<span class="swatch" title="{c}" style="background:rgb{c}"></span>' for c in flesh_ramp())
    v1 = sprites[("v1", "A", 1)]
    mv1 = metrics["v1only_" + RECOMMENDED]
    mrec = metrics[RECOMMENDED]
    body = (f"<p>{sw}</p><p class=\"lead\">Candidate ramp <code>{FLESH}</code>, 16 colours from "
            f"{FLESH_DARK} to {FLESH_LIGHT}, gamma {palgen.RAMP_GAMMA} like every ramp of palette v1, for 16 of the "
            "94 reserved slots. Not written to <code>docs/art/palette.json</code>: adding it is palette v2, "
            "your call. Every v1 colour stays as it is.</p>")
    body += strip([sprite_tile(sprites[(RECOMMENDED, "A", 1)], 4, f"{RECOMMENDED}, v1 + pink",
                               f"body luma {mrec['body_luma']:.0f}"),
                   sprite_tile(v1, 4, f"{RECOMMENDED}, v1 only", f"plaster_warm as flesh, luma {mv1['body_luma']:.0f}"),
                   sprite_tile(sprites[(RECOMMENDED, "A", 1)], 1, "1x"), sprite_tile(v1, 1, "1x")])
    S.append(("4 · The palette question: the Legion's pink is not in palette v1", "", body))

    # 5. the rig
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in RIG_NOTE) + "</div>"
    S.append(("5 · Does gen_rig.py serve him? What it would need", "", body))

    # 6. verdict and ask
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in VERDICT) + "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in CEO_ASK) \
            + "</ol></div>"
    S.append((f"6 · Recommendation: {RECOMMENDED}. Honest verdict and what you decide", "", body))

    intro = ("D35: the five most-seen enemies are drawn from scratch. The Liberty Legion trooper "
             "(<code>SD_LegionTrooper</code>, sprite <code>SDLT</code>, BESTIARY §4) holds MAP01's hangar. "
             "One decision before ~49 images, as with the rifleman's cell E (D38): what the man looks like. "
             "Six cells built directly on the 3D rig D38 approved, so the chosen cell is already in the final "
             "method. Built by <code>tools/art/gen_legion.py</code> on <code>tools/art/gen_rig.py</code>'s "
             f"primitives, seed {SEED}, palette v1 plus one candidate flesh ramp (section 4), no system fonts. "
             "Draft: nothing in <code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_legion.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic, no "
              "system fonts. Freedoom sprites shown for scale only, from freedoom2.wad 0.13.0, BSD-3-Clause "
              "(© the Freedoom contributors), not used as a source.")
    path = out_dir / f"{stamp}_F5_legion-trooper-sweep.html"
    sheetlib.write_sheet(path, lang="en", title="Liberty Legion trooper — design sweep (F5, D35)",
                         subtitle=f"SDLT · {len(CELLS)} cells on the rig · draft for the CEO's gate",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", EXTRA_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


def load_sprites(out_dir: Path = OUT_DIR) -> dict:
    out = {}
    for c in CELLS:
        for frame, rot in VIEWS:
            with Image.open(out_dir / f"{lump_name(c, frame, rot)}.png") as im:
                out[(c.key, frame, rot)] = np.asarray(im.convert("RGBA")).copy()
    with Image.open(out_dir / f"{lump_name(CELL[RECOMMENDED], 'A', 1)}_v1only.png") as im:
        out[("v1", "A", 1)] = np.asarray(im.convert("RGBA")).copy()
    return out


# ============================================================ the full set
# D48 (CEO, 2026-10-14): "the Legion trooper cell C". This renders cell C's
# whole frame set, as gen_rig.py does for the rifleman: walk A-D, aim E,
# fire F, pain G at 8 rotations; death H-L and gib M-U at rotation 0. The
# letters are the ones src/zscript/monsters/legion_trooper.zs plays today on
# Freedoom's SPOS (Spawn A B, See A-D at 3 tics, Missile E F E at 10/10/10,
# Pain G G, Death H-K 5 and L held, XDeath M-T 5 and U held, Raise L K J I
# H), so the swap is the rename SPOS -> SDLT (BESTIARY §2.7). The lump name
# is MOD-SPEC §6.3's reserved `SDLT`.
#
# All 8 rotations are separate lumps, not Doom's mirrored pairs (BESTIARY
# §4 budgets 49 images with mirroring): the figure is handed, the US flag on
# his RIGHT shoulder and the shotgun rising to his left, and a mirrored
# flag would put it on the wrong shoulder. 70 lumps, as the rifleman's.
#
# A1-A3, F1 and F3 are the sweep's own cell C, byte for byte (E is F
# without the flash); the CEO chose THOSE pixels.
#
# Blood (D48, D49): "much blood in the deaths, dark red", as the rifleman's
# D48 deaths in gen_rig.py, section "blood": flag_red 0-5 and true black
# (palette v1, so valid in v1 and v2), the round's burst, a stain that
# soaks wider on the chrome, a run from the mouth and down the cuirass,
# splats, a pool that grows K -> L; the gib's bigger burst, three pulsing
# jets from the stump, 30 chunks (chrome shards among them) and a wide
# pool. The burst, droplet, pool and chunk helpers below are COPIES of
# gen_rig.py's (same constants), not imports: gen_rig.py is being edited by
# another agent today, and these should move to rig_core.py once it is free
# (noted for the PM). The flag stays brighter than any blood (flag_red 11).
FULL_KEY = "C"                  # D48
FULL_DIR = OUT_DIR / "full_C"
FULL_CELL = CELL[FULL_KEY]
DEATH = core.Canvas(96, 80, 48, 72)     # gen_rig's: a corpse lies across
GIB = core.Canvas(96, 88, 48, 80)       # gen_rig's: the helmet flies higher than his head

GIB_FRAMES = "MNOPQRSTU"
FULL_GROUPS = (
    ("walk", "ABCD", True),
    ("attack", "EF", True),
    ("pain", "G", True),
    ("death", "HIJKL", False),
    ("gib", GIB_FRAMES, False),
)
# legion_trooper.zs (and BESTIARY §4: ShotgunGuy parity), in tics
WALK_TICS = 3
ATTACK_TICS = (20, 10, 10, 10)          # A (held, for the loop), E, F, E
PAIN_TICS = (20, 3, 3, 20)
DEATH_TICS = (20, 5, 5, 5, 5, 70)       # A, H I J K 5 tics, L held
GIB_TICS = (20,) + (5,) * 8 + (70,)     # A, M-T 5 tics, U held

FLOOR_GUN = ((-15.0, 1.4, 3.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))   # the shotgun lies on its side
_FIRE = POSES["F"]
FULL_POSES: dict[str, Pose] = {
    "A": replace(POSES["A"], title="idle / walk contact"),
    "B": Pose("B", "left foot forward", (3.7, ANKLE_Y, 6.0), (-3.8, ANKLE_Y + 1.6, -5.2), -0.9, "high", False,
              STAND, gun_tilt=0.03),
    "C": Pose("C", "right leg passing", (3.9, ANKLE_Y, 0.2), (-4.0, ANKLE_Y + 2.6, 1.2), 0.4, "high", False, STAND),
    "D": Pose("D", "right foot forward", (3.8, ANKLE_Y + 1.6, -5.2), (-3.7, ANKLE_Y, 6.0), -0.9, "high", False,
              STAND, gun_tilt=-0.03),
    "E": replace(_FIRE, key="E", title="aim", flash=False),
    "F": replace(_FIRE, title="fire"),
    "G": Pose("G", "pain", (4.0, ANKLE_Y, 0.8), (-3.8, ANKLE_Y, -3.0), -0.8, "high", False, STAND,
              gun_tilt=0.22, lean=13.0, head_pitch=22.0),
    "H": Pose("H", "hit", (3.8, ANKLE_Y, 1.2), (-3.6, ANKLE_Y, -3.6), -1.0, "free", False, DEATH,
              lean=22.0, head_pitch=32.0, hand_l=(13.0, 47.0, 2.0), hand_r=(-12.0, 34.0, 5.0),
              gun_at=((-8.0, 22.0, 6.0), (0.85, -0.35, 0.4), (0.0, 1.0, 0.0))),
    "I": Pose("I", "knees go", (3.8, ANKLE_Y, 1.2), (-3.6, ANKLE_Y, -1.0), -7.0, "free", False, DEATH,
              lean=26.0, head_pitch=30.0, hand_l=(13.0, 43.0, 1.0), hand_r=(-10.0, 31.0, 7.0),
              gun_at=((-12.0, 9.0, 7.0), (0.94, -0.25, 0.2), (0.0, 1.0, 0.0)), roll=14.0),
    "J": Pose("J", "falling", (3.8, ANKLE_Y, 1.2), (-3.6, ANKLE_Y, 0.0), -11.0, "free", False, DEATH,
              lean=18.0, head_pitch=25.0, hand_l=(14.0, 39.0, 0.0), hand_r=(-8.0, 29.0, 8.0),
              gun_at=((-16.0, 2.5, 3.0), (0.99, -0.15, 0.0), (0.0, 1.0, 0.0)), roll=42.0),
    "K": Pose("K", "hits the floor", (3.8, ANKLE_Y, 1.0), (-3.6, ANKLE_Y, 0.5), -9.0, "free", False, DEATH,
              lean=8.0, head_pitch=10.0, hand_l=(13.0, 41.0, -2.0), hand_r=(-7.0, 31.0, 8.0),
              gun_at=FLOOR_GUN, roll=74.0),
    "L": Pose("L", "dead", (3.6, ANKLE_Y, 0.6), (-3.8, ANKLE_Y, 1.4), -2.0, "free", False, DEATH,
              head_pitch=-10.0, hand_l=(11.0, 31.0, 3.0), hand_r=(-10.0, 31.0, 6.0), gun_at=FLOOR_GUN, roll=90.0),
}
GIB_POSE = Pose("M", "chest bursts", (3.8, ANKLE_Y, 0.8), (-3.6, ANKLE_Y, -3.0), -0.8, "high", False, GIB,
                gun_tilt=0.2, lean=10.0, head_pitch=18.0)
GIB_TITLES = {"M": "chest bursts", "N": "burst", "O": "chunks fly", "P": "jets", "Q": "legs buckle",
              "R": "falling", "S": "landing", "T": "down", "U": "dead"}

# ------------------------------------------------------------------ blood
BLOOD_RAMP = "flag_red"
BLOOD_MAX_INDEX = 5             # no blood colour brighter than flag_red 5 (the flag is flag_red 11)
# The gore's value: the rifleman's gore sits at base + 0.18 lift - 0.26 shift;
# the Legion takes no shift, so the same rendered value is a -0.08 lift.
GORE_LIFT = -0.08
MATERIALS_BLOOD: dict[str, Mat] = dict(MATERIALS)   # same ids as the sweep's table; three appended
core.register_material("gore", Mat.on_ramp(BLOOD_RAMP, 0, 4, black_floor=True, lift=GORE_LIFT), MATERIALS_BLOOD)
core.register_material("blood", Mat.on_ramp(BLOOD_RAMP, 1, BLOOD_MAX_INDEX, black_floor=True, flat=True),
                       MATERIALS_BLOOD)                 # droplets, stains, runs: no rim, so a drop stays red
core.register_material("pool", Mat.on_ramp(BLOOD_RAMP, 0, 3, black_floor=True, flat=True),
                       MATERIALS_BLOOD)                 # standing blood: darker than the spray

# gen_rig.py's D48 constants, unchanged, so the two infantries bleed alike.
GRAVITY = 160.0                 # units / s^2, the gib's big pieces
BLOOD_GRAVITY = 400.0           # droplets land within the death's 4 x 5 tics
DEATH_T = {"H": 0.08, "I": 0.19, "J": 0.31, "K": 0.46, "L": 3.0}   # s after the hit, 5 tics a frame
GIB_T = {"N": 0.05, "O": 0.18, "P": 0.32, "Q": 0.46, "R": 0.62, "S": 0.80, "T": 1.0, "U": 1.4}
N_SPRAY = 36                    # death burst droplets
N_GIB_SPRAY = 56                # gib burst droplets
N_CHUNKS = 30                   # gen_rig's N_CHUNKS_BLOODY
# chrome shards of the cuirass and the pads fly with the meat
CHUNK_MATS = ("gore", "gore", "gore", "flesh", "gore", "chrome", "flesh", "trouser", "gore", "chrome")
STAIN_R = {"H": 2.4, "I": 3.4, "J": 4.2, "K": 4.9, "L": 5.6}       # chest stain half width
POOL = {"K": (8.0, 7.0), "L": (20.0, 13.0)}                          # (x, z) radii under the chest
POOL_Z = 7.0                    # pool centre in front of the body (the camera is only 9 degrees down)
SPRAY_X = 40.0                  # landed splats stay inside the canvases (check_edges)
SPRAY_Z = 24.0                  # ... and no farther in front than this: a splat 9 degrees below the
                                # camera drops 0.16 px per unit forward, and seed 101 threw some past
                                # the canvas' floor band (gen_rig's seed 38 happens not to)
GIB_JETS = ((core.V(-16.0, 104.0, 6.0), 0.00), (core.V(3.0, 118.0, 9.0), 0.04), (core.V(19.0, 98.0, 4.0), 0.02))
JET_STEP = 0.022                # s between two drops of a jet
JET_PULSE = 0.13                # s, the heart's beat in the jet
JET_END = 0.75                  # the jets stop when the legs are down
WOUND = (0.8, 35.0)             # (x, y) of the round's hole on the cuirass, upright, before bob


def _torso_front(x: float, y: float, bob: float) -> float:
    """z of the cuirass front at (x, y), upright model space (build_model's torso_z)."""
    ty0, ty1 = WAIST_Y + bob, CHEST_Y + bob
    r = TORSO_R0 + (TORSO_R1 - TORSO_R0) * (y - ty0) / (ty1 - ty0)
    return TORSO_KZ * np.sqrt(max(r * r - x * x, 0.0)) - 0.2


def _attached(prim: core.Prim, to: core.Prim) -> core.Prim:
    """`prim`, given in upright model space, rides `to`'s rigid transform."""
    prim.xm, prim.xt, prim.grp = to.xm.copy(), to.xt.copy(), "blood"
    return prim


def _tagged(prims: list, tag: str) -> core.Prim:
    return next(p for p in prims if p.tag == tag)


def _land_time(y0: float, vy: float, rest: float, grav: float = GRAVITY) -> float:
    """When a body thrown up at vy from y0 comes down to height `rest`."""
    return (vy + np.sqrt(vy * vy + 2 * grav * max(y0 - rest, 0.0))) / grav


def _ballistic(p0: np.ndarray, v: np.ndarray, t: float, rest: float) -> tuple[np.ndarray, bool]:
    tl = _land_time(p0[1], v[1], rest)
    tt = min(t, tl)
    p = p0 + v * tt + core.V(0, -0.5 * GRAVITY * tt * tt, 0)
    if t >= tl:
        p[1] = rest
    return p, t >= tl


def droplet(p0, v, t: float, r: float) -> core.Prim:
    """A blood droplet `t` s after leaving p0 at v: a drop in the air, a flat
    splat once it has landed (gen_rig._droplet)."""
    rest = r * 0.3
    tl = _land_time(p0[1], v[1], rest, BLOOD_GRAVITY)
    tt = min(t, tl)
    p = p0 + v * tt + core.V(0, -0.5 * BLOOD_GRAVITY * tt * tt, 0)
    if t >= tl:
        x = float(np.clip(p[0], -SPRAY_X, SPRAY_X))
        z = float(min(p[2], SPRAY_Z))
        return core.ellipsoid("blood", 0.42, (x, 0.2, z), (r * 2.0, 0.35, r * 1.5), grp="splat")
    return core.ellipsoid("blood", 0.62, tuple(p), (r, r * 1.15, r), grp="spray")


def burst(origin, t: float, n: int, rng, speed=(30.0, 90.0)) -> list:
    """A round's spray (gen_rig.burst): n droplets thrown mostly sideways, up
    and away from the camera, some towards it, every sixth a heavy gout."""
    out = []
    for i in range(n):
        d = core.V(rng.uniform(-1, 1), rng.uniform(-0.25, 1.0), rng.uniform(-1.0, 0.45))
        d /= np.linalg.norm(d)
        gout = i % 6 == 0
        sp = rng.uniform(6, 22) if gout else rng.uniform(*speed)
        r = rng.uniform(1.3, 1.8) if gout else rng.uniform(0.65, 1.15)
        out.append(droplet(core.V(*origin), d * sp, t, r))
    return out


def pool(cx: float, cz: float, rx: float, rz: float, rng) -> list:
    """A pool on the floor: one flat ellipse and three lobes (gen_rig.pool)."""
    out = [core.ellipsoid("pool", 0.55, (cx, 0.3, cz), (rx, 0.55, rz), grp="pool")]
    for _ in range(3):
        ox, oz = rng.uniform(-0.7, 0.7) * rx, rng.uniform(-0.3, 0.6) * rz
        out.append(core.ellipsoid("pool", 0.62, (cx + ox, 0.32, cz + oz),
                                  (rx * rng.uniform(0.35, 0.55), 0.6, rz * rng.uniform(0.4, 0.6)), grp="pool"))
    return out


def chunks(t: float, seed: int = SEED, n: int = N_CHUNKS, mats: tuple = CHUNK_MATS) -> list:
    """The upper body as `n` lumps of gore, flesh, chrome and cloth, `t` s
    after the burst; landed ones flatten on the floor (gen_rig.chunks)."""
    rng = np.random.default_rng(seed + 1)
    out = []
    for i in range(n):
        p0 = core.V(rng.uniform(-6, 6), rng.uniform(30, 46), rng.uniform(-3, 3))
        side = np.sign(p0[0]) or 1.0
        v = core.V(side * rng.uniform(6, 30), rng.uniform(8, 42), rng.uniform(-6, 3))
        r = core.V(rng.uniform(1.1, 2.8), rng.uniform(1.0, 2.2), rng.uniform(1.1, 2.6))
        mat = mats[i % len(mats)]
        rest = r[1] * 0.5
        p, landed = _ballistic(p0, v, t, rest)
        if landed:
            r = r * core.V(1.35, 0.5, 1.35)
        out.append(core.ellipsoid(mat, 0.45 if mat != "flesh" else 0.40, tuple(p), tuple(r), grp="chunk"))
    return out


def death_blood(frame: str, prims: list, seed: int = SEED) -> list:
    """The blood of death frame H-L, for the posed `prims` of that frame."""
    pose = FULL_POSES[frame]
    t = DEATH_T[frame]
    bob = pose.bob
    torso = _tagged(prims, "torso")
    out: list = []
    sx, sy = WOUND[0], WOUND[1] + bob
    zf = _torso_front(sx, sy, bob)
    s = STAIN_R[frame]
    # the wound and its stain on the chrome, soaking wider each frame (rides the torso)
    out.append(_attached(core.ellipsoid("blood", 0.50, (sx, sy - s * 0.25, zf - 0.3), (s, s * 1.2, 1.5)), torso))
    out.append(_attached(core.ellipsoid("blood", 0.24, (sx, sy, zf + 0.45), (1.0, 1.0, 0.8)), torso))   # the hole
    if frame in "JKL":                    # it runs down the cuirass to the belt and the trousers
        k = "JKL".index(frame)
        y0, y1 = sy - 2.0, WAIST_Y - 2.0 - 2.5 * k + bob
        out.append(_attached(core.rcone("blood", 0.40, (1.2, y0, _torso_front(1.2, y0, bob) + 0.5),
                                        (1.8, y1, _torso_front(1.8, WAIST_Y + bob, bob) + 0.9), 1.3, 0.9), torso))
    # from the mouth (rides the head): the smooth face's one line of a mouth
    mouth = min((p for p in prims if p.grp == "head" and p.mat == "void"), key=lambda p: float(np.max(p.r)))
    if frame in "IJKL":
        m = mouth.a
        run = 2.0 + 1.2 * "IJKL".index(frame)
        out.append(_attached(core.rcone("blood", 0.45, m + core.V(0.3, -0.3, 0.2), m + core.V(0.6, -run, -0.2),
                                        0.75, 0.55), mouth))
    # the burst left his chest at H; where those droplets are now
    p_h, _ = build_model(FULL_CELL, FULL_POSES["H"])
    th = _tagged(p_h, "torso")
    hb = FULL_POSES["H"].bob
    origin = th.xm @ core.V(sx, WOUND[1] + hb, _torso_front(sx, WOUND[1] + hb, hb)) + th.xt
    out += burst(origin, t, N_SPRAY, np.random.default_rng(seed + 11), speed=(40.0, 120.0))
    # the wound bleeds while he falls: a short dribble under the hole
    wound = torso.xm @ core.V(sx, sy, zf + 0.4) + torso.xt
    if frame in "IJ":
        rng = np.random.default_rng(seed + 12 + "IJ".index(frame))
        for k in range(5):
            age = 0.02 + 0.03 * k
            out.append(droplet(wound, core.V(rng.uniform(-3, 3), rng.uniform(-4, 2), rng.uniform(6, 14)), age,
                               rng.uniform(0.6, 0.9)))
    if frame in POOL:                     # the pool under the chest, growing K -> L
        rx, rz = POOL[frame]
        out += pool(float(wound[0]) - 1.0, POOL_Z, rx, rz, np.random.default_rng(seed + 14))
        head = mouth.xm @ mouth.a + mouth.xt
        out += pool(float(head[0]), POOL_Z - 2.0, 3.0 + 1.5 * (frame == "L"), 4.0, np.random.default_rng(seed + 15))
    return out


def gib_blood(frame: str, t: float, prims: list, seed: int = SEED) -> list:
    """The blood of gib frame M-U, `t` s after the burst, for `prims`."""
    out: list = []
    base, _ = build_model(FULL_CELL, GIB_POSE)
    tb = _tagged(base, "torso")
    gb = GIB_POSE.bob
    origin = tb.xm @ core.V(0.0, WOUND[1] + gb, _torso_front(0.0, WOUND[1] + gb, gb)) + tb.xt
    out += burst(origin, max(t, 0.04), N_GIB_SPRAY, np.random.default_rng(seed + 21), speed=(35.0, 105.0))
    if frame == "M":
        return out
    stump = [p for p in prims if p.grp == "stump" and p.mat == "gore"]
    top = stump[0].bound()[0] + core.V(0, 1.5, 0) if stump else origin
    rng = np.random.default_rng(seed + 22)
    for v, lag in GIB_JETS:
        s = lag
        while s <= min(t, JET_END):
            pulse = 0.72 + 0.28 * np.cos(2 * np.pi * (s - lag) / JET_PULSE)
            fade = max(0.0, 1.0 - s / JET_END)
            vv = v * pulse * (0.45 + 0.55 * fade) + core.V(*rng.uniform(-4, 4, 3))
            out.append(droplet(top, vv, t - s, rng.uniform(0.7, 1.05)))
            s += JET_STEP
    if t >= 0.46:                         # the pool under him, growing until U
        g = min((t - 0.46) / 0.7, 1.0)
        out += pool(0.0, POOL_Z, 9.0 + 15.0 * g, 6.0 + 7.0 * g, np.random.default_rng(seed + 23))
    return out


def build_gib(frame: str, seed: int = SEED) -> tuple[list, dict]:
    """XDeath frame M-U. M: the chest gives way through the cuirass; from N
    the upper body is chunks (meat and chrome shards) on ballistic arcs, the
    M1 and the shotgun fly whole, the legs stand, buckle and fall, and he
    bleeds as the rifleman does (D48)."""
    cell = FULL_CELL
    if frame == "M":
        prims, anchors = build_model(cell, GIB_POSE)
        rng = np.random.default_rng(seed + 2)
        extra = []
        for _ in range(6):                # gore pushing out through the cuirass front
            y = rng.uniform(31, 39) + GIB_POSE.bob
            x = rng.uniform(-4.5, 4.5)
            p = core.V(x, y, _torso_front(x, y, GIB_POSE.bob) + rng.uniform(0.0, 1.0))
            extra.append(core.ellipsoid("gore", 0.35, tuple(p), tuple(rng.uniform(1.2, 2.4, 3)), grp="upper"))
        core.transform(extra, {}, {"upper"}, core.rot_x(GIB_POSE.lean), core.V(0, WAIST_Y + GIB_POSE.bob, 0))
        prims = prims + extra + gib_blood(frame, 0.0, prims, seed)
        return prims, anchors
    t = GIB_T[frame]
    k = float(np.clip((t - 0.25) / 0.55, 0, 1))          # the legs: stand, buckle, fall
    k = k * k * (3 - 2 * k)
    legs = replace(GIB_POSE, lean=0.0, head_pitch=0.0, bob=-0.8 - 10.0 * k, roll=0.0)
    prims, anchors = build_model(cell, legs)
    base, _ = build_model(cell, GIB_POSE)
    keep = [p for p in prims if p.grp in {"leg_l", "leg_r", "seat"} or p.tag == "belt"]
    for p in keep:
        if p.tag == "belt":
            p.grp = "stump"
    bob = legs.bob
    rng = np.random.default_rng(seed + 3)
    stump = [core.ellipsoid("gore", 0.30, (0, WAIST_Y + bob + 0.8, 0), (7.0, 2.4, 5.0), grp="stump")]
    for _ in range(4):
        stump.append(core.ellipsoid("gore", 0.40, (rng.uniform(-4, 4), WAIST_Y + bob + rng.uniform(1.0, 3.2),
                                                   rng.uniform(-2, 2)), tuple(rng.uniform(1.2, 2.2, 3)), grp="stump"))
    keep += stump
    groups = {"leg_l", "leg_r", "seat", "stump"}
    if k > 0:
        roll = 88.0 * k
        slide = core.V(-SLIDE * 0.45 * np.sin(np.deg2rad(roll)), 0, 0)
        core.transform(keep, {}, groups, core.rot_z(roll), ROLL_PIVOT, slide)
        core.rest_on_floor(keep, {}, groups)
    keep += gib_blood(frame, t, keep, seed)
    keep += chunks(t, seed)
    # the M1 and the shotgun fly whole, spinning, and lie where they land
    for grp, v, spin, rest, lie in (("helmet", core.V(9.0, 52.0, 0.0), -420.0, 3.6, -100.0),
                                    ("gun", core.V(-14.0, 26.0, 0.0), 260.0, 1.4, 0.0)):
        parts = [p for p in base if p.grp == grp]
        c0 = np.mean([q.bound()[0] for q in parts], axis=0)
        p, landed = _ballistic(c0, v, t, rest)
        R = core.rot_z(lie if landed else spin * t)
        if landed and grp == "gun":         # it lies flat along the floor, behind the legs
            u = parts[0].b - parts[0].a
            R = core.rot_y(-np.degrees(np.arctan2(u[2], u[0])))
            p[2] = -2.0
        core.transform(parts, {}, {grp}, R, c0, p - c0)
        if landed:                          # lying: its lowest point on the floor, not in it
            core.rest_on_floor(parts, {}, {grp})
        keep += parts
    return keep, anchors


BLOODY_FRAMES = "HIJKL" + GIB_FRAMES   # the frames that bleed; A-G are the sweep's figure


def full_canvas(frame: str) -> core.Canvas:
    return GIB if frame in GIB_FRAMES else FULL_POSES[frame].canvas


def build_frame(frame: str, seed: int = SEED) -> tuple[list, dict, dict]:
    """The posed primitives of one frame, its anchors and its material table
    (the sweep's MATERIALS for A-G, MATERIALS_BLOOD for H-U)."""
    if frame in GIB_FRAMES:
        prims, anchors = build_gib(frame, seed)
        return prims, anchors, MATERIALS_BLOOD
    prims, anchors = build_model(FULL_CELL, FULL_POSES[frame])
    if frame in BLOODY_FRAMES:
        return prims + death_blood(frame, prims, seed), anchors, MATERIALS_BLOOD
    return prims, anchors, MATERIALS


def render_full(frame: str, rotation: int, seed: int = SEED) -> np.ndarray:
    """One lump of the full set, RGBA (h, w, 4)."""
    prims, anchors, table = build_frame(frame, seed)
    flash = frame in FULL_POSES and FULL_POSES[frame].flash
    return core.render(prims, rotation, full_canvas(frame), table, seed=seed, value_shift=VALUE_SHIFT,
                       insignia=(FLAG_INSIGNIA,), muzzle=anchors["muzzle"][0] if flash else None,
                       flash_size=FLASH_SIZE, chrome=CHROME, what=f"{SPRITE}{frame}{rotation}")


def full_plan() -> list[tuple[str, int]]:
    """All 8 rotations for A-G (handed figure: no mirrored pairs), 0 for H-U."""
    return core.frame_plan(FULL_GROUPS, mirror=False)


def full_lump(frame: str, rotation: int) -> str:
    """The real lump name, MOD-SPEC §6.3: SDLT + frame + rotation."""
    return f"{SPRITE}{frame}{rotation}"


def blood_colours() -> set[tuple[int, int, int]]:
    """Every colour the blood can paint: flag_red 0..BLOOD_MAX_INDEX."""
    return {tuple(c) for c in core.ramp(BLOOD_RAMP)[:BLOOD_MAX_INDEX + 1]}


def red_pixels(rgba: np.ndarray) -> int:
    """Opaque pixels in blood_colours() (the flag is flag_red 11: never counted)."""
    reds = blood_colours()
    px = rgba[rgba[..., 3] > 0][:, :3]
    return sum(1 for c in map(tuple, px.tolist()) if c in reds)


def lineup_v2(figures: list, wall: str, light: int, width: int) -> np.ndarray:
    """The full set's lineups: MAP01 wall over SDFLR2, re-quantised to palette v2 (D45)."""
    return core.lineup(figures, wall, light, width, load=wall_rgb, palette=palette_v2())


def measure_full(sprite: np.ndarray) -> dict:
    m = measure(sprite)
    a = sprite[..., 3] > 0
    m["lowest_row"] = int(np.nonzero(a)[0].max())
    m["red_px"] = red_pixels(sprite)
    return m


def _seq(sprites: dict, frames: str, rot, cv: core.Canvas) -> list[np.ndarray]:
    out = []
    for f in frames:
        r = 0 if f in BLOODY_FRAMES else rot
        out.append(core.on_bg(core.pad_to(sprites[(f, r)], full_canvas(f), cv), NEUTRAL))
    return out


FLOOR_SCENES = (("F1", "SDCONC1", 176, "hangar wall"), ("F2", "SDCONC1", 144, "bay shadow, under the catwalk"))


def floor_frames(sprites: dict, frames: str, cv: core.Canvas, wall: str, light: int) -> list[np.ndarray]:
    """Frame A1 then `frames` at rotation 0, each by its own offsets on a
    MAP01 wall over SDFLR2, in the scene's light."""
    out = []
    for f in "A" + frames:
        spr = core.pad_to(sprites[("A", 1)], STAND, cv) if f == "A" else sprites[(f, 0)]
        out.append(lineup_v2([(spr, cv.cx, cv.foot_row - FEET_SINK)], wall, light, cv.w))
    return out


def write_full_gifs(sprites: dict, out_dir: Path = FULL_DIR) -> dict[str, Path]:
    """At game speed (35 tics a second, legion_trooper.zs's tics)."""
    t = lambda n: int(round(n * core.TIC_MS))  # noqa: E731
    out = {}
    for r in range(1, core.ROTATIONS + 1):
        out[f"walk_{r}"] = core.save_gif(_seq(sprites, "ABCD", r, STAND), [t(WALK_TICS)] * 4,
                                         out_dir / f"walk_rot{r}.gif")
        out[f"attack_{r}"] = core.save_gif(_seq(sprites, "AEFE", r, AIM), [t(n) for n in ATTACK_TICS],
                                           out_dir / f"attack_rot{r}.gif")
    out["turn"] = core.save_gif([core.on_bg(sprites[("A", r)], NEUTRAL) for r in range(1, 9)], [t(12)] * 8,
                                out_dir / "turntable.gif")
    out["pain"] = core.save_gif(_seq(sprites, "AGGA", 1, STAND), [t(n) for n in PAIN_TICS], out_dir / "pain_rot1.gif")
    out["death"] = core.save_gif(_seq(sprites, "AHIJKL", 1, DEATH), [t(n) for n in DEATH_TICS], out_dir / "death.gif")
    out["gib"] = core.save_gif(_seq(sprites, "A" + GIB_FRAMES, 1, GIB), [t(n) for n in GIB_TICS],
                               out_dir / "gib.gif")
    for key, wall, light, _ in FLOOR_SCENES:
        out[f"death_{key}"] = core.save_gif(floor_frames(sprites, "HIJKL", DEATH, wall, light),
                                            [t(n) for n in DEATH_TICS], out_dir / f"death_floor_{key}.gif")
        out[f"gib_{key}"] = core.save_gif(floor_frames(sprites, GIB_FRAMES, GIB, wall, light),
                                          [t(n) for n in GIB_TICS], out_dir / f"gib_floor_{key}.gif")
    return out


def build_full(out_dir: Path = FULL_DIR, seed: int = SEED, only: set[str] | None = None) -> dict:
    """Render the 70 lumps to out_dir (with grAb), then metrics and GIFs."""
    out_dir.mkdir(parents=True, exist_ok=True)
    sprites = {}
    for frame, rot in full_plan():
        name = full_lump(frame, rot)
        if only and name not in only:
            continue
        rgba = render_full(frame, rot, seed)
        save_sprite(rgba, out_dir / f"{name}.png", full_canvas(frame))
        sprites[(frame, rot)] = rgba
        print(name, flush=True)
    if only:
        return sprites
    metrics = {full_lump(f, r): measure_full(s) for (f, r), s in sprites.items()}
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    write_full_gifs(sprites, out_dir)
    return sprites


def load_full(out_dir: Path = FULL_DIR) -> dict:
    out = {}
    for frame, rot in full_plan():
        with Image.open(out_dir / f"{full_lump(frame, rot)}.png") as im:
            out[(frame, rot)] = np.asarray(im.convert("RGBA")).copy()
    return out


# ============================================================ full sheet
def rig_sprite(name: str) -> tuple[np.ndarray, int, int] | None:
    """One of the Reich rifleman's rig lumps (gen_rig.py's output, read only)
    with its grAb offsets, if it is on disk."""
    path = RIG_DIR / f"{name}.png"
    if not path.is_file():
        return None
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGBA")).copy()
    return (arr, *core.read_grab(path))


def sweep_identity(sprites: dict, sweep_dir: Path = OUT_DIR) -> dict[str, bool | None]:
    """Whether the full set's A1-A3, F1, F3 are the sweep's cell C pixels
    (None where the sweep's PNG is not on disk)."""
    out: dict[str, bool | None] = {}
    for f, r in VIEWS:
        path = sweep_dir / f"{lump_name(FULL_CELL, f, r)}.png"
        if not path.is_file():
            out[full_lump(f, r)] = None
            continue
        with Image.open(path) as im:
            out[full_lump(f, r)] = bool(np.array_equal(np.asarray(im.convert("RGBA")), sprites[(f, r)]))
    return out


FULL_ROT_NAMES = {1: "front", 2: "front-left", 3: "his left", 4: "back-left", 5: "back",
                  6: "back-right", 7: "his right", 8: "front-right"}
FULL_VERDICT = [
    "WHAT WORKS. Cell C as you chose it, now in every frame Doom asks for: the front, three-quarter and "
    "side views and the firing frame are the sweep's pixels, byte for byte, and everything else is the same "
    "figure posed, so the 70 lumps agree with each other. The chrome football pads, the round M1 and the "
    "shotgun high across the chest read at every rotation; from behind (4 to 6) he is a chrome back under "
    "a chrome bowl, still a T. He walks faster than the rifleman (3 tics a frame, ShotgunGuy parity) and the "
    "legs show because there is no greatcoat over them. Beside the rifleman on MAP01 the two infantries "
    "cannot be confused: light and broad against dark and narrow, chest gun against hip rifle.",
    "THE BLOOD (D48, D49). The deaths bleed as the rifleman's: dark red, flag_red 0-5 and black, a burst "
    "out of the chest at H, a stain soaking wider on the chrome, blood from the mouth and down the cuirass, "
    "splats, a pool that grows on K and L; the gib bursts through the cuirass, jets from the stump while the "
    "legs stand, throws 30 chunks of meat and chrome shards, the M1 and the shotgun fly whole, and the floor "
    "fills. On the Legion the red reads better than on the rifleman: dark red on chrome and pale khaki is "
    "the strongest contrast he has. The flag stays the brightest red on him (flag_red 11).",
    "WHAT DOES NOT, HONESTLY. The 'heavy' of BESTIARY 4 is still more promise than fact: he is slimmer than "
    "Freedoom's shotgun guy even with the pads (the sweep said so; you chose C as drawn, so the build was not "
    "touched). Up close (4x) he is the rig's rendered mannequin, as the rifleman. The firing frame from the "
    "front hides the face behind the flash. The pain frame is a lean back, not a flinch of the arms. The pool "
    "is a band a few pixels deep in front of the body, not a puddle seen from above (the camera looks down "
    "9 degrees), and at 1x the droplets are 1-2 px dots: spray in motion, noise on a still. In the gib the "
    "flag goes with the chunks: the legs that stay carry no insignia.",
    "NOT VERIFIED. Rotation order and grAb offsets are gen_rig's, checked by hand against r_things.c, not in "
    "GZDoom; the scene light is gen_enemy.py's stand-in, re-quantised to palette v2; the lumps are RGBA PNG "
    "with hard alpha like the rifleman's, and the shipped format is mod-engineer's call.",
]
FULL_ASK = [
    "Approve the 70 SDLT lumps as drawn (recommended): they go to assets/sprites/, mod-engineer renames SPOS "
    "to SDLT in SD_LegionTrooper's states (BESTIARY 2.7: the letters already match), and you judge him in "
    "GZDoom on MAP01's hangar, with the draft overlay first if you want to play him before approving.",
    "Or name fixes, each a parameter and one more render: a heavier build (thighs, waist), a different pain "
    "pose, more or less blood (N_SPRAY, POOL, GIB_JETS, the same constants as the rifleman's).",
]


def build_full_sheet(sprites: dict, stamp: str, out_dir: Path = PREVIEW_DIR, gif_dir: Path = FULL_DIR) -> Path:
    S = []
    T = core.tile

    def st(arr, zoom, cap, sub=""):
        return core.sprite_tile(arr, zoom, cap, sub, bg=NEUTRAL)

    def gt(name, zoom, cap, sub=""):
        return core.gif_tile(gif_dir / name, zoom, cap, sub)

    # 1. turnaround
    body = strip([st(sprites[("A", r)], 4, full_lump("A", r), FULL_ROT_NAMES[r]) for r in range(1, 9)])
    body += strip([st(sprites[("A", r)], 1, full_lump("A", r)) for r in range(1, 9)]
                  + [gt("turntable.gif", 4, "turntable", "animated")])
    ident = sweep_identity(sprites)
    same = [k for k, v in ident.items() if v]
    S.append(("1 · Turnaround: frame A at Doom's 8 rotations",
              "4x on neutral grey, then true 1x. Rotation 1 faces you, 3 shows his left side, 5 his back, 7 his "
              "right. Eight separate lumps, not mirrored pairs: the US flag is on his right shoulder and the "
              "shotgun rises to his left, so a mirror would move the flag. Identical, byte for byte, to the "
              f"sweep's cell C you chose: {', '.join(same) if same else 'none (sweep PNGs not on disk)'}.", body))

    # 2. walk
    body = strip([gt(f"walk_rot{r}.gif", 4, f"walk, rotation {r}", FULL_ROT_NAMES[r]) for r in range(1, 9)])
    for r in (1, 3):
        body += strip([st(sprites[(f, r)], 4, full_lump(f, r), FULL_POSES[f].title) for f in "ABCD"])
    S.append(("2 · Walk A-B-C-D, animated at game speed",
              f"See state SDLT AABBCCDD at {WALK_TICS} tics a frame (legion_trooper.zs, ShotgunGuy parity), 35 tics "
              "a second, every rotation. Stills of rotations 1 and 3 below. Spawn (idle) plays A B.", body))

    # 3. attack
    body = strip([gt(f"attack_rot{r}.gif", 4, f"attack, rotation {r}", "A, E 10, F 10, E 10 tics")
                  for r in (1, 2, 3, 7)])
    for f in "EF":
        body += strip([st(sprites[(f, r)], 3, full_lump(f, r)) for r in range(1, 9)])
    S.append(("3 · Attack: E aims, F fires (three pellets)",
              "Missile state E 10, F 10 (Bright), E 10. The shotgun comes from across the chest to the shoulder; "
              "the flash is a little larger than the rifle's and drawn behind him when his body hides the muzzle.",
              body))

    # 4. pain
    body = strip([gt("pain_rot1.gif", 4, "pain, rotation 1", "A, G 3, G 3, A")]
                 + [st(sprites[("G", r)], 3, full_lump("G", r)) for r in range(1, 9)])
    S.append(("4 · Pain: G", "He recoils: upper body back 13 degrees, chin up, the shotgun muzzle rising.", body))

    # 5. death and gib
    body = ""
    for key, wall, light, what in FLOOR_SCENES:
        sub = f"{wall} over SDFLR2, light {light}"
        body += strip([gt(f"death_floor_{key}.gif", 1, f"death, 1x, {key}", sub),
                       gt(f"gib_floor_{key}.gif", 1, f"gib, 1x, {key}", sub),
                       gt(f"death_floor_{key}.gif", 3, f"death, 3x, {key}", what),
                       gt(f"gib_floor_{key}.gif", 3, f"gib, 3x, {key}", what)])
    body += strip([st(sprites[(f, 0)], 3, full_lump(f, 0), FULL_POSES[f].title) for f in "HIJKL"])
    body += strip([st(sprites[(f, 0)], 2, full_lump(f, 0), GIB_TITLES[f]) for f in GIB_FRAMES])
    S.append(("5 · Death H-L and gib M-U, with the blood (rotation 0)",
              "At game speed on MAP01's hangar floor: each loop starts on A1 (20 tics), then Death H I J K at 5 "
              "tics and L held, or XDeath M to T at 5 tics and U held. Then frame by frame on neutral grey. Dark "
              "red, flag_red 0-5 and black, the rifleman's D48 blood (D49: every faction's deaths).", body))

    # 6. at 1x, beside the rifleman, on MAP01
    rr = {n: rig_sprite(n) for n in ("SDRRA1", "SDRRF3", "SDRRL0", "SDRRU0")}
    figs = [(sprites[("A", 1)], *core.grab_offsets(STAND))]
    labels = ["SDLTA1"]
    if rr["SDRRA1"]:
        figs.append(rr["SDRRA1"])
        labels.append("SDRRA1, the rifleman")
    figs.append((sprites[("F", 3)], *core.grab_offsets(AIM)))
    labels.append("SDLTF3, firing")
    if rr["SDRRF3"]:
        figs.append(rr["SDRRF3"])
        labels.append("SDRRF3, the rifleman firing")
    body = ""
    for key, wall, light, what in SCENES[:3]:
        sc = lineup_v2(figs, wall, light, 64 * len(figs))
        Image.fromarray(sc, "RGB").save(gif_dir / f"pair_{key}.png", optimize=True)
        body += strip([T(core.png_uri(sc), sc.shape[1], sc.shape[0], 1, f"{key} 1x", f"{wall} @{light}"),
                       T(core.png_uri(sc), sc.shape[1], sc.shape[0], 3, f"{key} at 3x for the eye", what)])
    dead = [(sprites[("L", 0)], *core.grab_offsets(DEATH))]
    dead_labels = ["SDLTL0"]
    for n in ("SDRRL0",):
        if rr[n]:
            dead.append(rr[n])
            dead_labels.append(n + ", the rifleman")
    dead.append((sprites[("U", 0)], *core.grab_offsets(GIB)))
    dead_labels.append("SDLTU0, gibbed")
    if rr["SDRRU0"]:
        dead.append(rr["SDRRU0"])
        dead_labels.append("SDRRU0, the rifleman gibbed")
    sc = lineup_v2(dead, "SDCONC1", 176, 96 * len(dead))
    Image.fromarray(sc, "RGB").save(gif_dir / "pair_dead.png", optimize=True)
    body += strip([T(core.png_uri(sc), sc.shape[1], sc.shape[0], 1, "the dead, 1x", "SDCONC1 @176"),
                   T(core.png_uri(sc), sc.shape[1], sc.shape[0], 2, "the dead at 2x")])
    far = flat.far(lineup_v2(figs, SCENES[1][1], SCENES[1][2], 64 * len(figs)))
    val = np.repeat(flat.luma(far)[..., None].clip(0, 255).astype(np.uint8), 3, -1)
    body += strip([T(core.png_uri(far), far.shape[1], far.shape[0], 5, f"{SCENES[1][0]} at game distance /4"),
                   T(core.png_uri(val), val.shape[1], val.shape[0], 5, "value only")])
    body += ("<p class=\"lead\">Standing and firing, left to right: " + html.escape(" · ".join(labels))
             + ". The dead: " + html.escape(" · ".join(dead_labels)) + ". Each sprite stands by its own grAb "
             "offsets, as the engine places it, in the hangar's light (gen_enemy's stand-in, re-quantised to "
             "palette v2; NOT VERIFIED against GZDoom). The rifleman's lumps are read from "
             "work/art/enemies/rig/ as they are on disk today.</p>")
    S.append(("6 · At 1x beside the Reich rifleman, on MAP01's hangar walls",
              "Where MAP01 puts the Legion (Z6, the hangar): SDCONC1 at 176 and at 144 under the catwalk, the "
              "red stripe framing D4. Then both dead on the hangar floor.", body))

    # 7. palette
    sw = "".join(f'<span class="swatch" title="{c}" style="background:rgb{c}"></span>' for c in flesh_ramp())
    bl = "".join(f'<span class="swatch" title="{c}" style="background:rgb{c}"></span>'
                 for c in MATERIALS_BLOOD["blood"].colours())
    lo, hi = palgen.load()["added_index"][FLESH]
    body = (f"<p>{sw}</p><p class=\"lead\">The pink is palette v2's <code>{FLESH}</code> (D45), slots {lo}-{hi}, "
            "read from <code>docs/art/palette.json</code>. The sweep's local candidate is gone; it was checked "
            f"identical to the official ramp, colour for colour ({FLESH_DARK} to {FLESH_LIGHT}, gamma "
            f"{palgen.RAMP_GAMMA}), so every pink pixel is the one you approved in the sweep.</p>"
            f"<p>{bl}</p><p class=\"lead\">Blood: flag_red 1-{BLOOD_MAX_INDEX} and black (pool 0-3, gore 0-4), "
            "palette v1, the rifleman's D48 colours. Every opaque pixel of the 70 lumps is palette v2.</p>")
    S.append(("7 · The palette: flesh_pink is official (v2), the blood is the rifleman's", "", body))

    # 8. numbers
    rows = []
    for f, r in [(f, r) for f in "ABCDEFG" for r in (1, 3, 5, 7)] + [(f, 0) for f in "HIJKL"] + [("P", 0), ("U", 0)]:
        m = measure_full(sprites[(f, r)])
        rows.append([full_lump(f, r), f"{m['height_px']} x {m['width_px']}", m["body_luma"], m["mass_luma"],
                     m["gap_L1"], m["gap_L2"], m["red_px"], m["lowest_row"] - full_canvas(f).foot_row])
    body = sheetlib.table(["lump", "h x w px", "body luma", "mass luma", "gap L1", "gap L2", "red px",
                           "below sole"], rows)
    body += ("<p class=\"lead\">Body luma is the mean over every opaque pixel, mass luma the median; gap is "
             "|body - wall| under the scene's light; red px counts blood colours (flag_red 0-5). Below sole: rows "
             "under the sole line (a pool lies in front of the body, so a few rows lower). Canvas: standing "
             f"{STAND.w}x{STAND.h}, aiming {AIM.w}x{AIM.h}, death {DEATH.w}x{DEATH.h}, gib {GIB.w}x{GIB.h}; "
             f"{len(full_plan())} lumps in all.</p>")
    S.append(("8 · Numbers", "", body))

    # 9. verdict and the ask
    body = '<div class="verdict">' + "".join(f"<p>{html.escape(v)}</p>" for v in FULL_VERDICT) + "</div>"
    body += '<div class="ask"><b>For the CEO</b><ol>' + "".join(f"<li>{html.escape(a)}</li>" for a in FULL_ASK) \
            + "</ol></div>"
    S.append(("9 · Honest verdict and what you decide", "", body))

    intro = ("D48: you chose the Liberty Legion trooper's cell C (chrome football pads). This is cell C's whole "
             "frame set on the rig, as the rifleman's: walk, aim, fire and pain at 8 rotations, death and gib at "
             f"one, {len(full_plan())} lumps named <code>SDLT</code> (MOD-SPEC §6.3), with the letters "
             "<code>legion_trooper.zs</code> already plays on Freedoom's SPOS. Pink from palette v2's "
             "<code>flesh_pink</code> (D45); much blood in the deaths, dark red (D48, D49). Built by "
             f"<code>tools/art/gen_legion.py --full</code>, seed {SEED}, no system fonts. Draft: nothing in "
             "<code>assets/</code>.")
    footer = ("Sprites: tools/art/gen_legion.py (GPL-3.0 code; art CC BY-NC-SA 4.0, D15), deterministic, no "
              "system fonts. The Reich rifleman's lumps are tools/art/gen_rig.py's (ours).")
    path = out_dir / f"{stamp}_F5_legion-trooper-C-full-set.html"
    sheetlib.write_sheet(path, lang="en", title="Liberty Legion trooper — cell C, full frame set (F5, D48)",
                         subtitle=f"SDLT · {len(full_plan())} lumps · draft for the CEO's gate",
                         intro=intro, sections=S, footer=footer)
    text = path.read_text(encoding="utf-8").replace("</style>", EXTRA_CSS + "</style>", 1)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    ap.add_argument("--no-sheet", action="store_true", help="sprites and metrics only")
    ap.add_argument("--sheet-only", action="store_true",
                    help="rebuild the sheet from the sprites already on disk")
    ap.add_argument("--full", action="store_true",
                    help="cell C's full frame set (D48): work/art/enemies/legion/full_C/ and its sheet")
    ap.add_argument("--only", default="", help="with --full: comma-separated lumps, e.g. SDLTH0,SDLTU0 (no sheet)")
    args = ap.parse_args()
    if args.full:
        only = {s.strip().upper() for s in args.only.split(",") if s.strip()} or None
        sprites = load_full() if args.sheet_only else build_full(only=only)
        if only or args.no_sheet:
            return
        path = build_full_sheet(sprites, args.stamp)
        print("sheet:", path.relative_to(PROJECT_ROOT))
        return
    if args.sheet_only:
        sprites = load_sprites()
        metrics = json.loads((OUT_DIR / "metrics.json").read_text(encoding="utf-8"))
    else:
        sprites, metrics = build_all()
    for k, m in metrics.items():
        print(k, m)
    if args.no_sheet:
        return
    path = build_sheet(sprites, metrics, args.stamp)
    print("sheet:", path.relative_to(PROJECT_ROOT))


if __name__ == "__main__":
    main()
