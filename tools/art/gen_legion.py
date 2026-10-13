"""F5 — Liberty Legion trooper, design sweep on the 3D rig (front, three-quarter, profile, fire).

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_legion.py               (Windows)
    .venv/bin/python tools/art/gen_legion.py                       (macOS)
    ... gen_legion.py --stamp 2026-10-13_2215   fixes the sheet's timestamp
    ... gen_legion.py --no-sheet                sprites and metrics only

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

What the rig needed that gen_rig.py does not have (it is imported, not
edited; the full note is on the sheet, section 5):
  * a CHROME shading: banded Lambert turns chrome into grey plastic, so
    chrome here reflects a two-tone environment (bright sky, a dark horizon
    line, darker ground) with a hard specular dot, the 1970s airbrush-chrome
    convention, and skips the middle of the steel_blue ramp;
  * no VALUE_SHIFT: gen_rig darkens the Reich by 0.26; the Legion is the
    LIGHT faction (BESTIARY §2.1, body 0.72-0.80);
  * materials as a parameter (gen_rig's reduce/to_rgba read its own module
    MATERIALS), a flag stamp instead of the armband, a shotgun carry.
This file therefore carries its own trace/reduce/to_rgba, ~120 lines that
mirror gen_rig's with those three changes; everything else is gen_rig's.

Palette. BESTIARY §2.1 and ART-BIBLE §3 give the Legion's body mass to a
"reserved pink/flesh ramp, to be added to palette.json v2". Palette v1 has
no pink. This file does NOT edit docs/art/palette.json: it carries the
candidate ramp, FLESH_RAMP, 16 colours built with palette.py's own rule
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
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_enemy as flat  # noqa: E402  (light stand-in, far view, silhouette, flash)
import gen_rig as rig  # noqa: E402  (primitives, IK, rotations, camera, Freedoom reader)
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
FEET_SINK = rig.FEET_SINK
DOOM_HEIGHT = 56                # actor Height (BESTIARY §4) = px at 1:1
STAND, AIM = rig.STAND, rig.AIM
SS = rig.SS

# ================================================================== palette
# Candidate for palette v2 (ART-BIBLE §3, BESTIARY §2.1). Endpoints: a
# near-black with a red cast, so the dark end of the ramp still reads as
# flesh in sector light 96, and a pale salmon pink at luma ~200, light
# enough for the Legion's 0.72-0.80 body value.
FLESH = "flesh_pink"
FLESH_DARK = (24, 10, 10)
FLESH_LIGHT = (242, 190, 180)
FLESH_STEPS = palgen.RAMP_STEPS


def flesh_ramp() -> list[tuple[int, int, int]]:
    """The candidate ramp, built with palette.py's own interpolation."""
    return [tuple(palgen._lerp_gamma(FLESH_DARK[c], FLESH_LIGHT[c], i / (FLESH_STEPS - 1))
                  for c in range(3)) for i in range(FLESH_STEPS)]


def ramp(name: str) -> list[tuple[int, int, int]]:
    return flesh_ramp() if name == FLESH else artlib.ramp(name)


def palette_v1() -> list[tuple[int, int, int]]:
    return [tuple(c) for c in artlib.load_palette()["colours"]]


def palette_ext() -> list[tuple[int, int, int]]:
    """Palette v1 plus the candidate ramp: what the sheet's scenes use."""
    return palette_v1() + flesh_ramp()


def quantize_ext(rgb: np.ndarray) -> np.ndarray:
    cols = palette_ext()
    pimg = Image.new("P", (1, 1))
    pimg.putpalette([v for c in cols for v in c] + [0] * (3 * (256 - len(cols))))
    q = Image.fromarray(rgb, "RGB").quantize(palette=pimg, dither=Image.Dither.NONE)
    return np.asarray(q.convert("RGB"))


def lit(rgb: np.ndarray, light: int) -> np.ndarray:
    """gen_enemy's light stand-in, re-quantised to v1 + the candidate ramp."""
    f = min(1.0, light / flat.LIGHT_FULL)
    return quantize_ext(np.clip(rgb.astype(np.float64) * f, 0, 255).astype(np.uint8))


# ================================================================ materials
@dataclass(frozen=True)
class Mat:
    """A run of palette colours, darkest first. A span is (ramp, lo, hi),
    or ("black",) / ("white",) for the two extras."""
    spans: tuple
    shading: str = "lambert"    # "lambert" | "chrome"
    cloth: bool = False         # takes the cloth grain
    lift: float = 0.0           # value added to every primitive of this material

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

# Chrome environment (world y up): reflection rays above HORIZON see sky,
# below it ground, darkest right under the horizon line.
HORIZON = -0.60                 # front plates, even tipped down a little, reflect sky
SKY_LO, SKY_HI = 0.80, 1.0      # sky value at the horizon and straight up: bright, so chrome clears concrete
GROUND_LO, GROUND_SPAN, GROUND_FADE = 0.04, 0.30, 0.8
SPEC_COS = 0.90                 # reflection this close to the key light: a white dot
CHROME_KEY = 0.22               # how much the key light's side darkens chrome
CHROME_AO = 0.5                 # chrome takes half the occlusion of cloth
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
    carry: str          # "high" (across the chest) | "aim"
    flash: bool
    canvas: rig.Canvas


ANKLE_Y = rig.ANKLE_Y
POSES = {
    "A": Pose("A", "stand", (3.9, ANKLE_Y, 0.4), (-3.9, ANKLE_Y, 0.0), 0.0, "high", False, STAND),
    "F": Pose("F", "fire", (4.1, ANKLE_Y, -1.6), (-3.9, ANKLE_Y, 2.2), -0.4, "aim", True, AIM),
}
VIEWS = (("A", 1), ("A", 2), ("A", 3), ("F", 1), ("F", 3))   # what each cell shows

# Body. Heavier than the rifleman (BESTIARY §4: "wider at the shoulders").
HIP_Y = rig.HIP_Y
THIGH, SHIN = rig.THIGH, rig.SHIN
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


def gun_frame(pose: Pose):
    if pose.carry == "high":
        butt = rig.V(*GUN_HIGH_BUTT) + rig.V(0, pose.bob, 0)
        u = rig.V(*GUN_HIGH_DIR)
    else:
        butt = rig.V(*GUN_AIM_BUTT) + rig.V(0, pose.bob, 0)
        u = rig.V(0.06, np.tan(np.deg2rad(rig.PITCH_DEG)), 1.0)
    u = u / np.linalg.norm(u)
    up = rig.V(0, 1, 0)
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

    E, RC, CC, BX = rig.ellipsoid, rig.rcone, rig.ccone, rig.box

    # ---------------------------------------------------------------- legs
    for side, foot, grp in ((1, pose.foot_l, "leg_l"), (-1, pose.foot_r, "leg_r")):
        hip = rig.V(side * 3.5, HIP_Y + bob, 0.0)
        knee, ankle = rig.two_bone(hip, foot, THIGH, SHIN, rig.V(0, 0, 1))
        add(grp, RC("trouser", 0.62, hip, knee, 3.0, 2.6))
        add(grp, RC("trouser", 0.58, knee, ankle + rig.V(0, 3.4, 0), 2.6, 2.3))
        add(grp, E("trouser", 0.56, tuple(ankle + rig.V(0, 4.4, 0.1)), (2.7, 1.3, 2.6)))   # bloused over the boot
        add(grp, RC("boot", 0.55, ankle + rig.V(0, 4.0, 0), ankle, 2.25, 2.1))
        add(grp, BX("boot", 0.35, (ankle[0], ankle[1] - 1.15, ankle[2] + 1.4), (1.75, 1.1, 3.1), rnd=0.6))
    add("upper", E("trouser", 0.60, (0, HIP_Y + 1.0 + bob, -0.2), (6.6, 3.6, 4.3)))     # seat

    # ---------------------------------------------------------------- torso
    belt_z = (TORSO_R0 + 0.4) * 0.74
    add("upper", CC("belt", 0.45, 26.9 + bob, 28.9 + bob, TORSO_R0 + 0.4, TORSO_R0 + 0.35, kz=0.74))
    add("upper", BX("chrome", 0.6, (0, 27.9 + bob, belt_z + 0.15), (1.2, 0.9, 0.35)))      # buckle
    ty0, ty1 = WAIST_Y + bob, CHEST_Y + bob
    torso_mat = "chrome" if cell.torso == "cuirass" else "flesh"
    add("upper", rig.Prim("cappedcone", torso_mat, 0.66, rig.V(0, (ty0 + ty1) / 2, -0.2), h=(ty1 - ty0) / 2,
                          r1=TORSO_R0, r2=TORSO_R1, scale=rig.V(1.0, 1.0, TORSO_KZ), tag="torso"))

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
                           clip=[(rig.V(1, 0, 0), cut_x), (rig.V(0, 0, -1), 0.6)], tag="patch"))

    # ---------------------------------------------------------------- head
    head_off = rig.V(0, bob, 0)
    if pose.carry == "aim":
        head_off = head_off + rig.V(-1.2, -0.7, 0.7)     # cheek down on the stock
    hp = lambda x, y, z: tuple(rig.V(x, y, z) + head_off)  # noqa: E731
    add("head", RC("flesh", 0.55, rig.V(0, 40.0 + bob, -0.4), rig.V(0, 44.3, 0.2) + head_off, 2.7, 2.4))   # bull neck
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
        add("head", E("chrome", 0.7, hp(0, 47.7, 1.0), (3.75, 1.2, 3.65), clip=[(rig.V(0, 0, -1), 0.4)]))
        add("head", E("void", 0.4, hp(0, 44.3, 3.95), (1.2, 0.25, 0.4)))
    # M1 "pot": a round bowl with an even lip, BESTIARY §4's 16-px tell
    hy = head_off[1]
    c = rig.V(*hp(0, 0, 0))
    add("helmet", E("chrome", 0.7, hp(0, 49.6, 0.6), (5.0, 6.3, 5.4), clip=[(rig.V(0, -1, 0), -(48.9 + hy))]))
    add("helmet", CC("chrome", 0.55, 48.5 + hy, 49.3 + hy, 5.9, 5.4, x=c[0], z=0.6 + c[2]))
    for sx in (1, -1):          # chin strap
        add("helmet", RC("belt", 0.4, hp(sx * 3.9, 48.6, 1.4), hp(sx * 2.3, 43.6, 2.2), 0.32))
    anchors["head"] = (c + rig.V(0, 47, 1), "head")

    # ---------------------------------------------------------------- shotgun
    butt, u, v, w = gun_frame(pose)
    at = lambda s, hh=0.0, k=0.0: butt + u * s + v * hh + w * k  # noqa: E731
    add("gun", RC("wood", 0.5, at(0.6, -0.4), at(8.5, 0.15), 1.35, 0.8))                 # stock
    add("gun", RC("gunmetal", 0.5, at(8.0, 0.25), at(13.0, 0.25), 0.95, 0.9))           # receiver
    add("gun", RC("gunmetal", 0.55, at(12.5, 0.45), at(GUN_LEN, 0.45), 0.5, 0.45))      # barrel
    add("gun", RC("gunmetal", 0.4, at(13.0, -0.45), at(GUN_LEN - 3.0, -0.45), 0.42))    # magazine tube
    add("gun", RC("wood", 0.55, at(15.5, -0.5), at(20.5, -0.5), 0.95))                  # the pump
    anchors["muzzle"] = (at(GUN_LEN + 0.4, 0.45), "gun")

    # ---------------------------------------------------------------- arms
    grips = {-1: at(GRIP_R, -0.6), 1: at(GRIP_L, -1.0)}
    for side in (1, -1):
        sh = rig.V(side * (SHOULDER_X + 0.2), SHOULDER_Y + bob, -0.4)
        pole = rig.V(side * 1.0, -0.4, -0.7)
        elbow, wrist = rig.two_bone(sh, grips[side], UPPER_ARM, FOREARM, pole)
        add("arm", RC("flesh", 0.66, sh, elbow, 2.75, 2.35))
        add("arm", RC("flesh", 0.62, elbow, wrist, 2.35, 2.0))
        fd = (wrist - elbow) / np.linalg.norm(wrist - elbow)
        if cell.torso == "bare":
            add("arm", RC("chrome", 0.65, wrist - fd * 3.4, wrist - fd * 0.8, 2.25, 2.15))   # bracers
        add("arm", E("flesh", 0.62, tuple(wrist + fd * 0.9 - v * 0.2), (1.4, 1.55, 1.4)))
    return P, anchors


# ================================================================== render
def trace(prims: list, rotation: int, cv: rig.Canvas, mats: dict, seed: int = SEED) -> dict:
    """gen_rig.raymarch with the Legion's shading (module docstring): the
    same march and buffers, chrome by reflection, no value shift."""
    scene = rig.Scene(prims)
    Rm = rig.yaw_matrix(rotation)
    fwd, right, up = rig.camera()
    cols, rows = [], []
    for c, R in scene.bounds:
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
    o = ((sx.reshape(-1, 1) * right + sy.reshape(-1, 1) * up) - fwd * rig.T0) @ Rm
    d = fwd @ Rm
    n = len(o)
    t = np.full(n, rig.T0 - rig.T_SPAN)
    alive = np.ones(n, bool)
    hit = np.zeros(n, bool)
    for _ in range(rig.MAX_STEPS):
        idx = np.nonzero(alive)[0]
        if not len(idx):
            break
        dist = scene.sdf(o[idx] + np.outer(t[idx], d))
        got = dist < rig.HIT_EPS
        hit[idx[got]] = True
        t[idx] += np.where(got, 0.0, np.maximum(dist * rig.STEP_SCALE, rig.HIT_EPS * 0.5))
        alive[idx[got | (t[idx] > rig.T0 + rig.T_SPAN)]] = False
    hidx = np.nonzero(hit)[0]
    ph = o[hidx] + np.outer(t[hidx], d)
    _, ids = scene.sdf(ph, want_id=True)
    nrm = np.zeros_like(ph)
    for k in range(3):
        e = np.zeros(3)
        e[k] = rig.NORMAL_H
        nrm[:, k] = scene.sdf(ph + e) - scene.sdf(ph - e)
    nrm /= np.maximum(rig._len(nrm), 1e-9)[:, None]
    nw = nrm @ Rm.T                                     # world normals
    lam = nw @ rig.LIGHT
    lam_b = np.floor((lam * 0.5 + 0.5) * rig.LIGHT_BANDS).clip(0, rig.LIGHT_BANDS - 1) / (rig.LIGHT_BANDS - 1)
    ao = np.clip(scene.sdf(ph + nrm * rig.AO_DIST) / rig.AO_DIST, 0, 1)
    m = [mats[prims[i].mat] for i in ids]
    base = np.array([prims[i].base + mats[prims[i].mat].lift for i in ids])
    chrome = np.array([mm.shading == "chrome" for mm in m], bool)
    cloth = np.array([mm.cloth for mm in m], bool)
    grain = (rig.hash3(np.floor(ph / rig.GRAIN_CELL), seed) - 0.5) * 2 * rig.GRAIN * cloth
    fall = rig.VERTICAL_FALLOFF * (0.5 - ph[:, 1] / DOOM_HEIGHT)
    v = (base + VALUE_SHIFT + rig.SHADE_GAIN * (lam_b - 0.5) - rig.AO_WEIGHT * (1 - ao) - fall + grain)
    # chrome: what the surface reflects, not how much light it takes
    r = fwd[None, :] - 2.0 * (nw @ fwd)[:, None] * nw
    ry = r[:, 1]
    sky = SKY_LO + (SKY_HI - SKY_LO) * np.sqrt(np.clip((ry - HORIZON) / (1.0 - HORIZON), 0, 1))
    ground = GROUND_LO + GROUND_SPAN * np.clip((HORIZON - ry) / GROUND_FADE, 0, 1)
    env = np.where(ry > HORIZON, sky, ground)
    vc = env - CHROME_KEY * (1 - lam_b) - CHROME_AO * rig.AO_WEIGHT * (1 - ao) - fall
    vc = np.where(r @ rig.LIGHT > SPEC_COS, 1.0, vc)
    v = np.where(chrome, vc, v)
    rr = yy.reshape(-1)[hidx]
    cc = xx.reshape(-1)[hidx]
    pid[rr, cc] = ids
    val[rr, cc] = np.clip(v, 0, 1)
    depth[rr, cc] = t[hidx]
    return {"pid": pid, "val": val, "depth": depth}


def reduce(buf: dict, prims: list, mats: dict):
    """gen_rig.reduce with the materials as a parameter."""
    names = list(mats)
    mid = {n: i for i, n in enumerate(names)}
    pid, val, dep = buf["pid"], buf["val"], buf["depth"]
    h, w = pid.shape[0] // SS, pid.shape[1] // SS
    blk = lambda a: a.reshape(h, SS, w, SS).transpose(0, 2, 1, 3).reshape(h, w, SS * SS)  # noqa: E731
    Pb, Vb, Db = blk(pid), blk(val), blk(dep)
    mat = np.full((h, w), -1, np.int16)
    out_v = np.zeros((h, w))
    out_d = np.full((h, w), np.inf)
    out_p = np.full((h, w), -1, np.int32)
    covered = (Pb >= 0).sum(-1)
    for y, x in zip(*np.nonzero(covered >= rig.COVER_MIN)):
        s = Pb[y, x]
        ids, counts = np.unique(s[s >= 0], return_counts=True)
        near = np.array([Db[y, x][s == i].mean() for i in ids])
        win = ids[np.lexsort((near, -counts))[0]]
        sel = s == win
        out_p[y, x] = win
        mat[y, x] = mid[prims[win].mat]
        out_v[y, x] = Vb[y, x][sel].mean()
        out_d[y, x] = Db[y, x][sel].mean()
    return mat, out_v, out_d, out_p


def to_rgba(mat, val, depth, mats: dict) -> np.ndarray:
    """gen_rig.to_rgba with the materials as a parameter: palette colour,
    then the occlusion contour and the silhouette rim."""
    names = list(mats)
    h, w = mat.shape
    opaque = mat >= 0
    idx = np.zeros((h, w), np.int16)
    for i, name in enumerate(names):
        sel = mat == i
        idx[sel] = np.rint(val[sel] * (len(mats[name].colours()) - 1)).astype(np.int16)
    dark = np.zeros((h, w), np.int16)
    pad_op = np.pad(opaque, 1)
    pad_d = np.pad(depth, 1, constant_values=np.inf)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nb_op = pad_op[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        nb_d = pad_d[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        dark = np.where(opaque & nb_op & (nb_d < depth - rig.DEPTH_EDGE), np.maximum(dark, rig.CONTOUR_STEPS), dark)
        dark = np.where(opaque & ~nb_op, np.maximum(dark, rig.RIM_STEPS), dark)
    idx = np.maximum(idx - dark, 0)
    rgba = np.zeros((h, w, 4), np.uint8)
    for i, name in enumerate(names):
        cols = np.array(mats[name].colours(), np.uint8)
        sel = mat == i
        rgba[sel, :3] = cols[np.clip(idx[sel], 0, len(cols) - 1)]
    rgba[opaque, 3] = 255
    return rgba


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


def stamp_flag(rgba: np.ndarray, pid: np.ndarray, prims: list, rotation: int) -> bool:
    """The flag on the patch's visible centre, slid up to PATCH_SEARCH px so
    it sits on opaque pixels, when the patch faces the camera at all."""
    tagged = [i for i, p in enumerate(prims) if p.tag == "patch"]
    vis = np.isin(pid, tagged)
    if vis.sum() < PATCH_MIN_PX:
        return False
    out_w = rig.yaw_matrix(rotation) @ rig.V(-1, 0, 0)      # his right side, in world
    if out_w[2] < -0.05:
        return False
    fwd_w = rig.yaw_matrix(rotation) @ rig.V(0, 0, 1)
    pix = flag_pixels(mirror=fwd_w[0] > 0.3)
    fh, fw = len(FLAG), len(FLAG[0])
    h, w = pid.shape
    ys, xs = np.nonzero(vis)
    cx, cy = xs.mean() - (fw - 1) / 2, ys.mean() - (fh - 1) / 2
    opaque = rgba[..., 3] > 0
    best = None
    for dy in range(-PATCH_SEARCH, PATCH_SEARCH + 1):
        for dx in range(-PATCH_SEARCH, PATCH_SEARCH + 1):
            x0 = min(max(int(round(cx + dx)), 0), w - fw)
            y0 = min(max(int(round(cy + dy)), 0), h - fh)
            score = (int(opaque[y0:y0 + fh, x0:x0 + fw].sum()), -(dx * dx + dy * dy))
            if best is None or score > best[0]:
                best = (score, x0, y0)
    _, x0, y0 = best
    for i, j, col in pix:
        rgba[y0 + j, x0 + i] = (*col, 255)
    return True


def render(cell: Cell, frame: str, rotation: int, mats: dict | None = None, seed: int = SEED) -> np.ndarray:
    """One sprite, RGBA (h, w, 4)."""
    mats = MATERIALS if mats is None else mats
    pose = POSES[frame]
    cv = pose.canvas
    prims, anchors = build_model(cell, pose)
    buf = trace(prims, rotation, cv, mats, seed)
    mat, val, dep, pid = reduce(buf, prims, mats)
    rgba = to_rgba(mat, val, dep, mats)
    stamp_flag(rgba, pid, prims, rotation)
    if pose.flash:
        rig.add_flash(rgba, dep, anchors["muzzle"][0], rotation, cv, FLASH_SIZE)
    a = rgba[..., 3] > 0
    if a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any():
        raise ValueError(f"{cell.key} {frame}{rotation} touches the canvas edge")
    return rgba


# ================================================================== output
def lump_name(cell: Cell, frame: str, rotation: int) -> str:
    """Draft file name: SDLT_<cell>_<frame><rot> (the lump is SDLT<frame><rot>)."""
    return f"{SPRITE}_{cell.key}_{frame}{rotation}"


def save_sprite(rgba: np.ndarray, path: Path, cv: rig.Canvas) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    info = PngInfo()
    info.add(b"grAb", struct.pack(">ii", *rig.grab_offsets(cv)))
    Image.fromarray(rgba, "RGBA").save(path, pnginfo=info, optimize=True)
    return path


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
    """gen_rig.lineup with this file's quantiser (v1 + the candidate ramp):
    sprites side by side by their own offsets, MAP01 wall over SDFLR2."""
    wall_h, floor_h = flat.WALL_H, flat.FLOOR_H
    w_rgb = flat.tile_to(wall_rgb(wall), width, wall_h)
    fl = flat.tile_to(wall_rgb("SDFLR2"), width, floor_h * 3)
    fl = np.asarray(Image.fromarray(fl, "RGB").resize((width, floor_h), Image.Resampling.NEAREST))
    canvas = np.concatenate([w_rgb, fl], axis=0).copy()
    floor = flat.FLOOR_LINE - FEET_SINK
    slot = width / len(figures)
    for i, (spr, ox, oy) in enumerate(figures):
        x0 = int(round(slot * (i + 0.5))) - ox
        y0 = floor - oy
        a = spr[..., 3] > 0
        ys, xs = np.nonzero(a)
        ys2, xs2 = ys + y0, xs + x0
        keep = (ys2 >= 0) & (ys2 < canvas.shape[0]) & (xs2 >= 0) & (xs2 < width)
        canvas[ys2[keep], xs2[keep]] = spr[ys[keep], xs[keep], :3]
    return lit(canvas, light)


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
    gx, gy = rig.read_grab(path)
    return arr, gx, gy


def comparison_figures(sprite: np.ndarray) -> tuple[list, list[str]]:
    figs = [(sprite, *rig.grab_offsets(STAND))]
    labels = ["SDLTA1 (this cell)"]
    for name, label in (("SPOSA1", "SPOSA1, Freedoom shotgun guy: today's placeholder"),
                        ("POSSA1", "POSSA1, Freedoom zombieman: the rifleman's placeholder")):
        fd = rig.freedoom_sprite(name)
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
         "gamma": palgen.RAMP_GAMMA, "status": "candidate for palette v2, NOT in palette.json",
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
    return rig.tile(src, w, h, zoom, cap, sub)


def sprite_tile(arr: np.ndarray, zoom: int, cap: str, sub: str = "") -> str:
    return tile(rig.png_uri(rig.on_bg(arr, NEUTRAL)), arr.shape[1], arr.shape[0], zoom, cap, sub)


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
    rr_luma = f"{rig.measure(rr[0])['body_luma']:.0f}" if rr else "n/a"
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
            lines.append(tile(rig.png_uri(sc), sc.shape[1], sc.shape[0], 1, f"{key} 1x", f"{wall} @{light}"))
        with Image.open(lineup_dir / f"lineup_{c.key}_{WORST}.png") as im:
            worst = np.asarray(im.convert("RGB"))
        big = tile(rig.png_uri(worst), worst.shape[1], worst.shape[0], 2, f"{WORST} at 2x for the eye",
                   "left to right: this cell, SPOSA1, POSSA1, SDRRA1")
        farv = flat.far(worst)
        sil = silhouette_rgb(sprites[(c.key, "A", 1)])
        extra = [tile(rig.png_uri(farv), farv.shape[1], farv.shape[0], 4, f"{WORST} at game distance /4", "shown 4x"),
                 tile(rig.png_uri(sil), sil.shape[1], sil.shape[0], 4, "16 px silhouette", "shown 4x")]
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
    sils = [tile(rig.png_uri(silhouette_rgb(sprites[(c.key, "A", 1)])), *silhouette_rgb(sprites[(c.key, "A", 1)]).shape[1::-1],
                 5, c.key) for c in CELLS]
    if rr:
        s = silhouette_rgb(rr[0])
        sils.append(tile(rig.png_uri(s), s.shape[1], s.shape[0], 5, "SDRR", "the Reich rifleman"))
    pair = []
    for key, wall, light, _ in (SCENES[1], SCENES[0]):
        figs = [(sprites[(RECOMMENDED, "A", 1)], *rig.grab_offsets(STAND))] + ([rr] if rr else [])
        sc = lineup(figs, wall, light, 64 * len(figs))
        fv = flat.far(sc)
        val = np.repeat(flat.luma(fv)[..., None].clip(0, 255).astype(np.uint8), 3, -1)
        pair += [tile(rig.png_uri(fv), fv.shape[1], fv.shape[0], 5, f"{key} /4", f"{RECOMMENDED} and SDRR"),
                 tile(rig.png_uri(val), val.shape[1], val.shape[0], 5, f"{key} /4, value only")]
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"),
                    help="YYYY-MM-DD_HHMM for the sheet's file name")
    ap.add_argument("--no-sheet", action="store_true", help="sprites and metrics only")
    ap.add_argument("--sheet-only", action="store_true",
                    help="rebuild the sheet from the sprites already in work/art/enemies/legion/")
    args = ap.parse_args()
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
