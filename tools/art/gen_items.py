"""M2a (audit B3, B5, H2) — our own pickups for everything the campaign
still places in Freedoom's clothes: health, armour, the area map, the
backpack, the yellow and red keycards and the hand Katyusha's world pickup.

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_items.py              (Windows)
    .venv/bin/python tools/art/gen_items.py                      (macOS)
    ... --stamp 2026-10-19_2300      fixes the preview's timestamp

What this is. `docs/qa/2026-10-14_2357_M2-freedoom-audit.md` §3 counts 113
Freedoom pickups placed in the campaign on skill 3 (B5) and the Katyusha's
BFUG (B3). This is a SWEEP (PIPELINE stage 2): three options per object
against the Freedoom lump it replaces, and the FULL SET of the recommended
option (every animation frame Doom's class plays), so the install follows
the CEO's choice without another render.

    item       lump  frames  Doom class    Freedoom   options
    stim       SDBN  A       Stimpack      STIM       A IPP dressing packet, B AI-2 kit, C bandage roll
    medikit    SDMD  A       Medikit       MEDI       A enamel first-aid box, B medic's satchel, C field chest
    hbonus     SDHB  A-D     HealthBonus   BON1       A glucose ampoule, B zelyonka bottle, C iodine bottle
    abonus     SDAB  A-D     ArmorBonus    BON2       A SSh-68 helmet, B armour plate, C tank crew helmet
    garmor     SDAG  A-B     GreenArmor    ARM1       A flak vest, B SN-42 breastplate, C vest and helmet
    barmor     SDAH  A-B     BlueArmor     ARM2       A heavy vest in cobalt (v2), B the same in steel blue (v1),
                                                      C bare-steel SN-42 and helmet
    allmap     SDMP  A-D     Allmap        PMAP       A officer's map case (planshet), B folded map, C rolled plan
    backpack   SDBP  A       Backpack      BPAK       A veshmeshok, B RD-54 pack, C veshmeshok with greatcoat roll
    ykey       SDKY  A-B     YellowCard    YKEY       A SDKB's card in yellow, B cream card with a yellow band,
                                                      C a yellow booklet
    rkey       SDKK  A-B     RedCard       RKEY       the same three in red (K: красный; SDKR is the Katyusha's rocket)
    katyusha   SDHP  A       BFG9000       BFUG       A the D51 draft as rendered, B the same smaller, C side-on

SDHP is the name MOD-SPEC §6.3 already reserves for the Katyusha's pickup;
the other ten are PROPOSALS, checked free of every SD sprite prefix in
assets/, MOD-SPEC, the other generators and the IWAD
(tests/test_gen_items.py). The yellow and red passes are the blue pass's
family (SDKB, option B of tools/art/gen_pickups.py, D63): option A is that
card's own geometry, line for line, in another ground colour.

How it is drawn. Exactly as the approved pickups (D48, D63): small 3D scenes
on gen_weapon's Rig seen from PICKUP_PITCH, lit by the fixed key light in
flat bands, reduced to 1x by majority vote and outlined by the contour,
crease and rim passes; gen_pickups' Box, cylinder and disc primitives. One
primitive is new here, `dome`: the upper half of an ellipsoid (a helmet, a
padded crown), which the Rig cannot draw because it has no clipping plane.
No fonts anywhere in a sprite (they would not reproduce across machines).

Animation. Where Doom's class animates, the frames differ only by light:
HealthBonus and ArmorBonus (`ABCDCB 6`) and Allmap (`ABCDCB 6 Bright`) move
a glint across the object, the armours (`A 6; B 7 bright` / `B 6 bright`)
and the keys (`A 10; B 10 bright`) brighten in frame B as SDKB does. Each
frame has exactly the size and offsets of frame A, so nothing jumps.

Colour. Palette v1 for everything except the heavy armour's option A, in
palette v2's `mosaic_cobalt` (D45) for the reason the blue pass is: Doom's
blue armour must read BLUE, and v1's only blue is a grey (option B shows it).
Sprites are RGBA with hard alpha, as every shipped sprite. The medical
cross is the first-aid sign since D80, a white cross on a green field (ISO
7010 E003), not the protected red-cross emblem: CROSS_MATERIAL and
FIELD_MATERIAL.

Install (D80, `--install`). The CEO's choice per object is CHOSEN: the
recommended option except SDAG C, SDAH C and SDBP B. `--install` renders
every frame of each chosen option into work/art/items/<item>/<option>/ and
the key icons into work/art/items/hud/, plus a check sheet
(work/art/items/sheet/install_D80.png); it writes nothing in docs/ or
assets/: the mod-engineer copies the files (MOD-SPEC 6.3, "The campaign
pickups, installed by D80").

Outputs (work/ is gitignored):
    work/art/items/<item>/<option>/<LUMP><F>0.png   frame A of every option, every frame of the recommended
    work/art/items/hud/STKEYS0-2.png                proposed key icons (indexed, palette v2)
    work/art/items/sheet/*.png, *.gif               scenes and animations the preview embeds
    work/art/items/metrics.json                     sizes, offsets, luma, contrast on two floors
    docs/art/previews/<stamp>_F5_campaign-pickups.html and .png
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import datetime as dt
import html
import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_pickups as gp  # noqa: E402
import gen_weapon as gw  # noqa: E402
import palette as palette_mod  # noqa: E402
import sheetlib  # noqa: E402
from gen_enemy import Material, luma  # noqa: E402
from gen_pickups import BOX_YAW, DECAL_LIFT, Box, centre, cylinder, disc, rect, star_poly, yawed  # noqa: E402
from gen_weapon import Frame, Rig, floor_basis, perp, unit  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "items"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
SHEET_SLUG = "F5_campaign-pickups"
SDKB_DIR = PROJECT_ROOT / "assets" / "sprites" / "pickups"

# (item, lump, frames, Doom class, Freedoom sprite). The contract with the
# mod-engineer; tests/test_gen_items.py reads this table as text.
NAMES = (
    ("stim", "SDBN", "A", "Stimpack", "STIM"),
    ("medikit", "SDMD", "A", "Medikit", "MEDI"),
    ("hbonus", "SDHB", "ABCD", "HealthBonus", "BON1"),
    ("abonus", "SDAB", "ABCD", "ArmorBonus", "BON2"),
    ("garmor", "SDAG", "AB", "GreenArmor", "ARM1"),
    ("barmor", "SDAH", "AB", "BlueArmor", "ARM2"),
    ("allmap", "SDMP", "ABCD", "Allmap", "PMAP"),
    ("backpack", "SDBP", "A", "Backpack", "BPAK"),
    ("ykey", "SDKY", "AB", "YellowCard", "YKEY"),
    ("rkey", "SDKK", "AB", "RedCard", "RKEY"),
    ("katyusha", "SDHP", "A", "BFG9000", "BFUG"),
)

# Each Doom class's Spawn state, read from gzdoom.pk3 g4.14.2
# (zscript/actors/doom/doomhealth.zs, doomarmor.zs, doomartifacts.zs,
# doomkeys.zs, doomammo.zs, weaponbfg.zs): (frame, tics, bright). Tics -1
# is a still sprite. Ours keep them line for line, only the name changes.
SPAWN: dict[str, tuple[tuple[str, int, bool], ...]] = {
    "Stimpack": (("A", -1, False),),
    "Medikit": (("A", -1, False),),
    "HealthBonus": tuple((f, 6, False) for f in "ABCDCB"),
    "ArmorBonus": tuple((f, 6, False) for f in "ABCDCB"),
    "GreenArmor": (("A", 6, False), ("B", 7, True)),
    "BlueArmor": (("A", 6, False), ("B", 6, True)),
    "Allmap": tuple((f, 6, True) for f in "ABCDCB"),
    "Backpack": (("A", -1, False),),
    "YellowCard": (("A", 10, False), ("B", 10, True)),
    "RedCard": (("A", 10, False), ("B", 10, True)),
    "BFG9000": (("A", -1, False),),
}
TIC_MS = 1000.0 / 35.0

# =============================================================== materials
ITEM_MATERIALS: dict[str, Material] = {
    "enamel": Material("concrete_cold", 10, 31),                      # white enamelled steel
    "canvas": Material("military_green", 0, 12, black_floor=True),    # tarpaulin, webbing, kit bags
    "leather": Material("rust_brown", 1, 10, black_floor=True),       # the map case
    "orange": Material("rust_brown", 7, 15),                          # the AI-2's plastic
    "glass": Material("steel_blue", 7, 15),                           # clear glass above a liquid
    "glucose": Material("cream_yellow", 6, 15),                       # an ampoule's contents
    "zelyonka": Material("military_green", 4, 15, black_floor=True),  # brilliant green
    "amber_glass": Material("rust_brown", 2, 12, black_floor=True),   # an iodine bottle
    "pass_yellow": Material("hazard_yellow", 3, 15, black_floor=True),
    "pass_red": Material("flag_red", 3, 15, black_floor=True),
    "steel_cloth": Material("steel_blue", 1, 13, black_floor=True),   # a blue-grey cover, not metal
    "greatcoat": Material("plaster_warm", 1, 9, black_floor=True),    # the rolled shinel
    "aid_green": Material("military_green", 5, 15),                   # the first-aid sign's field (D80)
}
V2_MATERIALS = frozenset({"cobalt"})
GLINT = "flash_core"            # gen_weapon's flat cream: no light, no contour
# The medical cross (D80): not the protected red-cross emblem but the
# international first-aid sign, a white cross on a green field (ISO 7010
# E003). Palette v1's only green is military_green, so the field is its upper
# ramp (the zelyonka's), not ISO's signal green. Until D80 the cross was
# "hull_red" at 0.62 on a white ground.
CROSS_MATERIAL, CROSS_BASE = "tel_white", 0.80
FIELD_MATERIAL, FIELD_BASE = "aid_green", 0.56
FIELD_MARGIN = 0.15             # the green square's half side over the cross's half length
FRAME_GAIN = 0.16               # frame B of the armours: value added all over (the pass uses gp.GLINT_GAIN)


@contextlib.contextmanager
def item_materials():
    """gen_weapon's tables with gen_pickups' extras and ours appended, so
    every earlier id keeps its number; restored on the way out."""
    saved = (gw.MATERIALS, gw.MAT_ID, gw.METALS, gw.FLAT)
    mats = dict(gw.MATERIALS)
    mats.update(gp.EXTRA_MATERIALS)
    mats.update(ITEM_MATERIALS)
    gw.MATERIALS = mats
    gw.MAT_ID = {name: i for i, name in enumerate(mats)}
    gw.METALS = set(saved[2])
    try:
        yield
    finally:
        gw.MATERIALS, gw.MAT_ID, gw.METALS, gw.FLAT = saved


# ============================================================ primitives
def dome(rig: Rig, c, axes, material: str, base: float, gain: float = 0.8, seams=None) -> None:
    """The upper half of an ellipsoid (local coordinate along axes[2] >= 0):
    a helmet resting on its rim. Rig.ellipsoid's ray cast, plus the cut.
    Seen from above, a ray whose first hit is below the rim only goes lower,
    so the cut pixels are simply empty: the hemisphere is exact."""
    c = np.asarray(c, np.float64)
    cx, cy, s = rig.project(c)
    M = np.column_stack([np.asarray(a, np.float64) for a in axes]) * s
    Minv = np.linalg.inv(M)
    ex = float(np.sqrt((M[0] ** 2).sum()))
    ey = float(np.sqrt((M[1] ** 2).sum()))
    win = rig._window(cx - ex, cy - ey, cx + ex, cy + ey)
    if win is None:
        return
    sl, X, Y, _ = win
    o = np.stack([X - cx, Y - cy, np.zeros_like(X)], -1)
    p = o @ Minv.T
    q = Minv[:, 2]
    a = float(q @ q)
    b = 2.0 * (p @ q)
    cc = (p * p).sum(-1) - 1.0
    disc_ = b * b - 4 * a * cc
    t = (-b - np.sqrt(np.clip(disc_, 0, None))) / (2 * a)
    loc = p + t[..., None] * q
    inside = (disc_ >= 0) & (loc[..., 2] >= 0.0)
    n = loc @ Minv
    n = n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
    depth = c[2] + t / s
    val = rig.shade(n, base, gain, material)
    for axis, pos, width, dv in (seams or ()):
        val = np.where(np.abs(loc[..., axis] - pos) < width, val - dv, val)
    rig._commit(sl, inside, depth, val, gw.MAT_ID[material])


def on_dome(c, X, Y, Z, r, az: float, el: float):
    """A point on a dome of semi-axes r=(rx, ry, rz) at azimuth az (0 = the
    front, towards the eye; positive to the right) and elevation el, both
    degrees; with its surface normal."""
    a, e = np.deg2rad(az), np.deg2rad(el)
    d = np.array([np.cos(e) * np.sin(a), -np.cos(e) * np.cos(a), np.sin(e)])
    rx, ry, rz = r
    p = np.asarray(c, np.float64) + X * rx * d[0] + Y * ry * d[1] + Z * rz * d[2]
    n = unit(X * d[0] / rx + Y * d[1] / ry + Z * d[2] / rz)
    return p, n


def decal_at(rig: Rig, p, n, Zref, poly, material: str, base: float, gain: float = 0.6,
             lift: float = 0.25) -> None:
    """A flat marking tangent at p (normal n), poly in (across, up) cm."""
    V = perp(Zref, n)
    U = unit(np.cross(V, n))
    o = np.asarray(p, np.float64) + n * lift
    rig._plane([o + U * s + V * t for s, t in poly], material, base, gain)


def cross_poly(cs: float, ct: float, arm: float, bar: float):
    """The medical cross, one twelve-point outline (arm: half length, bar:
    half width)."""
    pts = ((-bar, arm), (bar, arm), (bar, bar), (arm, bar), (arm, -bar), (bar, -bar), (bar, -arm),
           (-bar, -arm), (-bar, -bar), (-arm, -bar), (-arm, bar), (-bar, bar))
    return [(cs + s, ct + t) for s, t in pts]


def field_poly(cs: float, ct: float, arm: float):
    """The first-aid sign's green square behind a cross of half length arm."""
    a = arm * (1.0 + FIELD_MARGIN)
    return [(cs - a, ct - a), (cs + a, ct - a), (cs + a, ct + a), (cs - a, ct + a)]


def ellipse_poly(rx: float, ry: float, n: int = 28):
    return [(rx * np.cos(2 * np.pi * k / n), ry * np.sin(2 * np.pi * k / n)) for k in range(n)]


def chain(rig: Rig, pts, r: float, material: str, base: float, gain: float = 0.7) -> None:
    for a, b in zip(pts[:-1], pts[1:]):
        rig.capsule(np.asarray(a, np.float64), np.asarray(b, np.float64), r, r, material, base, gain)


def face_fn(base, X, Zc, Y, th: float):
    """(s, t, k) -> a point on the front face of a leaning flat object."""
    return lambda s, t, k=1: base - Y * (th / 2 + DECAL_LIFT * k) + X * s + Zc * t


def frame_index(frame: str) -> int:
    return "ABCD".index(frame)


def finish(rig: Rig) -> Frame:
    return gw.finish(rig, hud=False)


# ========================================================= health, small
STIM_PX = 1.6                   # STIMA0 is 19x10
IPP = (11.0, 8.0, 3.6)          # w, d, h: the individual dressing packet (ИПП), exaggerated
AI2 = (9.0, 10.5, 2.4)          # w, h, thickness of the AI-2 kit (1970s, orange plastic)
ROLL_R, ROLL_L = 3.2, 7.0


def render_stim_a(frame: str = "A") -> Frame:
    """A: the individual dressing packet (ИПП-1), rubberised khaki, the
    first-aid sign on top (a white cross on a green field, D80), the tear
    strip round its face."""
    rig = gp.rig_for(STIM_PX)
    X, Y, Z = yawed(BOX_YAW)
    w, d, h = IPP
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    b.draw(rig, "canvas", 0.52)
    b.decal(rig, "top", -w * 0.34, -d * 0.40, w * 0.34, d * 0.40, FIELD_MATERIAL, FIELD_BASE)
    b.decal_poly(rig, "top", cross_poly(0.0, 0.0, d * 0.32, d * 0.11), CROSS_MATERIAL, CROSS_BASE,
                 lift=DECAL_LIFT * 2)
    b.decal(rig, "front", -w / 2, h * 0.55, w / 2, h * 0.80, "tel_white", 0.58)
    b.decal(rig, "left", -d / 2, h * 0.55, d / 2, h * 0.80, "tel_white", 0.50)
    return finish(rig)


def render_stim_b(frame: str = "A") -> Frame:
    """B: the AI-2 personal kit standing on its edge, orange plastic, its
    lid seam and a cream label (no cross: the real one had none)."""
    rig = gp.rig_for(STIM_PX * 1.05)
    X, Zc, Y = gp.pass_axes(18.0)
    w, h, th = AI2
    base = centre() - Zc * h / 2
    rig.plate(base + Zc * h / 2, X, Zc, rect(w, h, -h / 2), th, "orange", 0.58, 0.75)
    face = face_fn(base, X, Zc, Y, th)
    rig._plane([face(s, t) for s, t in rect(w, 0.45, h * 0.72)], "orange", 0.30, 0.6)
    rig._plane([face(s, t, 2) for s, t in rect(w * 0.56, h * 0.26, h * 0.30)], "tel_white", 0.66, 0.6)
    rig._plane([face(s, t, 2) for s, t in rect(1.4, 1.0, h * 0.80)], "rubber", 0.30, 0.6)
    return finish(rig)


def render_stim_c(frame: str = "A") -> Frame:
    """C: a roll of bandage lying, its loose end run out towards the eye
    with the first-aid sign printed on it."""
    rig = gp.rig_for(STIM_PX)
    X, Y, Z = yawed(-18.0)
    c = centre() - Z * ROLL_R
    p0, p1 = c - X * ROLL_L / 2 + Z * ROLL_R, c + X * ROLL_L / 2 + Z * ROLL_R
    cylinder(rig, p0, p1, ROLL_R, "tel_white", 0.60, 0.8, caps=(0.74, 0.74))
    tail = [c + X * (-ROLL_L * 0.45) - Y * ROLL_R * 0.5, c + X * (ROLL_L * 0.45) - Y * ROLL_R * 0.5,
            c + X * (ROLL_L * 0.40) - Y * (ROLL_R + 7.5), c + X * (-ROLL_L * 0.50) - Y * (ROLL_R + 7.5)]
    rig._plane([p + Z * 0.05 for p in tail], "tel_white", 0.68, 0.6)
    mid = c - Y * (ROLL_R + 4.2) + Z * 0.1
    rig._plane([mid + X * s - Y * t for s, t in field_poly(0.0, 0.0, 2.4)], FIELD_MATERIAL, FIELD_BASE, 0.6)
    rig._plane([mid + X * s - Y * t + Z * 0.05 for s, t in cross_poly(0.0, 0.0, 2.4, 0.8)], CROSS_MATERIAL,
               CROSS_BASE, 0.6)
    return finish(rig)


# ========================================================= health, large
MED_PX = 1.0                    # MEDIA0 is 29x20
MED_BOX = (30.0, 12.0, 21.0)
SATCHEL = (28.0, 10.0, 19.0)
CHEST = (34.0, 18.0, 18.0)


def render_medi_a(frame: str = "A") -> Frame:
    """A: the white enamelled first-aid box (аптечка) of every Soviet
    workshop, standing: the first-aid sign (D80) big on its face and small on
    its end, the lid seam, a steel handle and latch."""
    rig = gp.rig_for(MED_PX)
    X, Y, Z = yawed(22.0)
    w, d, h = MED_BOX
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    b.draw(rig, "enamel", 0.58)
    b.decal(rig, "front", -w / 2, h - 4.4, w / 2, h - 3.8, "enamel", 0.22)
    b.decal(rig, "left", -d / 2, h - 4.4, d / 2, h - 3.8, "enamel", 0.18)
    b.decal_poly(rig, "front", field_poly(0.0, h * 0.42, 6.4), FIELD_MATERIAL, FIELD_BASE, lift=DECAL_LIFT * 2)
    b.decal_poly(rig, "front", cross_poly(0.0, h * 0.42, 6.4, 2.2), CROSS_MATERIAL, CROSS_BASE, lift=DECAL_LIFT * 3)
    b.decal_poly(rig, "left", field_poly(0.0, h * 0.42, 3.4), FIELD_MATERIAL, FIELD_BASE - 0.06,
                 lift=DECAL_LIFT * 2)
    b.decal_poly(rig, "left", cross_poly(0.0, h * 0.42, 3.4, 1.2), CROSS_MATERIAL, CROSS_BASE - 0.06,
                 lift=DECAL_LIFT * 3)
    b.decal(rig, "front", -1.4, h - 4.6, 1.4, h - 2.0, "steel", 0.62, lift=DECAL_LIFT * 3)
    p0, p1 = b.pt("top", -6.0, 0.0, 0.0), b.pt("top", 6.0, 0.0, 0.0)
    chain(rig, [p0, p0 + Z * 2.6, p1 + Z * 2.6, p1], 0.7, "steel", 0.55, 0.85)
    return finish(rig)


def render_medi_b(frame: str = "A") -> Frame:
    """B: the medic's satchel (сумка санитарная): khaki canvas, the flap over
    two thirds of the face with a green disc and the white cross, two steel
    buckles, the strap lying in a loop in front."""
    rig = gp.rig_for(MED_PX)
    X, Y, Z = yawed(18.0)
    w, d, h = SATCHEL
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    b.draw(rig, "canvas", 0.50)
    Box(b.c + Z * (h - 0.4), X, Y, Z, w + 0.6, d + 0.6, 0.9).draw(rig, "canvas", 0.58)
    b.decal(rig, "front", -w / 2 - 0.3, h * 0.30, w / 2 + 0.3, h + 0.4, "canvas", 0.60, lift=0.35)
    disc(rig, b.pt("front", 0.0, h * 0.64, 0.5), -Y, 4.8, FIELD_MATERIAL, FIELD_BASE)
    b.decal_poly(rig, "front", cross_poly(0.0, h * 0.64, 3.4, 1.15), CROSS_MATERIAL, CROSS_BASE, lift=0.65)
    for s in (-w * 0.32, w * 0.32):
        b.decal(rig, "front", s - 1.2, h * 0.30 - 1.6, s + 1.2, h * 0.30 + 1.0, "steel", 0.62, lift=0.6)
    pl, pr = b.pt("left", -d * 0.1, h - 2.0, 0.8), b.pt("right", -d * 0.1, h - 2.0, 0.8)
    fl = b.c - X * (w / 2 + 2.0) - Y * (d / 2 + 2.0) + Z * 0.9
    fr = b.c + X * (w / 2 + 1.0) - Y * (d / 2 + 3.0) + Z * 0.9
    front = b.c - Y * (d / 2 + 7.0) + Z * 0.9
    chain(rig, [pl, fl, front, fr, pr], 0.9, "canvas", 0.34)
    return finish(rig)


def render_medi_c(frame: str = "A") -> Frame:
    """C: a green wooden field medical chest, planked like the ammunition
    crates, a green panel with the white cross on its face and end, a rope
    handle."""
    px = MED_PX * 0.9
    rig = gp.rig_for(px)
    X, Y, Z = yawed(BOX_YAW)
    w, d, h = CHEST
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    b.draw(rig, "olive_paint", 0.56)
    for s in (-w / 2 + 2.5, w / 2 - 2.5):
        Box(b.pt("top", s, 0.0, 0.0), X, Y, Z, 3.0, d, 1.2).draw(rig, "olive_paint", 0.62)
    gp.crate_planks(rig, b, px_per_cm=px)
    b.decal(rig, "front", -7.5, 3.0, 7.5, 15.0, FIELD_MATERIAL, FIELD_BASE, lift=DECAL_LIFT * 2)
    b.decal_poly(rig, "front", cross_poly(0.0, 9.0, 4.6, 1.6), CROSS_MATERIAL, CROSS_BASE, lift=DECAL_LIFT * 3)
    b.decal(rig, "left", -5.0, 4.0, 5.0, 14.0, FIELD_MATERIAL, FIELD_BASE - 0.06, lift=DECAL_LIFT * 2)
    b.decal_poly(rig, "left", cross_poly(0.0, 9.0, 3.2, 1.1), CROSS_MATERIAL, CROSS_BASE - 0.06, lift=DECAL_LIFT * 3)
    return finish(rig)


# ========================================================= health bonus
HB_PX = 2.2                     # BON1A0 is 11x15
AMP_R = 2.2                     # the ampoule, exaggerated about twice
BOTTLE_R = 2.4


GLINT_W, GLINT_H = 0.9, 2.0     # cm: the flash on a bottle, big enough to survive the 1x vote


def bonus_glint(rig: Rig, c, X, Y, Z, r: float, k: int, z0: float, z1: float) -> None:
    """A vertical flash on a glass body that climbs it, frame by frame."""
    t = z0 + (z1 - z0 - GLINT_H) * k / 3
    p = c - Y * (r * 1.02) - X * r * 0.55
    rig._plane([p + Z * t, p + X * GLINT_W + Z * t, p + X * GLINT_W + Z * (t + GLINT_H), p + Z * (t + GLINT_H)],
               GLINT, 1.0, 0.0)


def render_hbonus_a(frame: str = "A") -> Frame:
    """A: an ampoule of glucose standing, amber to its shoulder, the clear
    neck and the sealed tip; a flash climbs the glass."""
    k = frame_index(frame)
    rig = gp.rig_for(HB_PX)
    X, Y, Z = yawed(0.0)
    c = centre() - Z * 4.0
    cylinder(rig, c, c + Z * 4.4, AMP_R, "glucose", 0.48 + 0.05 * k, 0.8)
    cylinder(rig, c + Z * 4.4, c + Z * 5.0, AMP_R, "glass", 0.58, 0.8)
    rig.capsule(c + Z * 5.0, c + Z * 6.0, AMP_R, AMP_R * 0.42, "glass", 0.62, 0.8, open_ends=True)
    rig.capsule(c + Z * 6.0, c + Z * 6.5, AMP_R * 0.42, AMP_R * 0.42, "hull_red", 0.55, 0.8, open_ends=True)
    rig.capsule(c + Z * 6.5, c + Z * 8.4, AMP_R * 0.62, AMP_R * 0.18, "glass", 0.66, 0.8)
    bonus_glint(rig, c, X, Y, Z, AMP_R, k, 1.4, 4.4)
    return finish(rig)


def draw_bottle(rig: Rig, c, X, Y, Z, body: str, cap: str, k: int, label: str | None = "tel_white") -> None:
    cylinder(rig, c, c + Z * 4.0, BOTTLE_R, body, 0.44 + 0.05 * k, 0.8)
    if label is not None:
        rig.capsule(c + Z * 1.5, c + Z * 2.7, BOTTLE_R * 1.03, BOTTLE_R * 1.03, label, 0.62, 0.8, open_ends=True)
    rig.capsule(c + Z * 4.0, c + Z * 5.0, BOTTLE_R, BOTTLE_R * 0.45, body, 0.50 + 0.05 * k, 0.8, open_ends=True)
    cylinder(rig, c + Z * 5.0, c + Z * 5.5, BOTTLE_R * 0.45, "glass", 0.6, 0.8)
    cylinder(rig, c + Z * 5.5, c + Z * 6.8, BOTTLE_R * 0.62, cap, 0.42, 0.8, caps=(None, 0.52))
    bonus_glint(rig, c, X, Y, Z, BOTTLE_R, k, 1.4, 4.0)


def render_hbonus_b(frame: str = "A") -> Frame:
    """B: a bottle of zelyonka (brilliant green, the Soviet antiseptic) and
    its rubber stopper; no label, so the green is all of it."""
    rig = gp.rig_for(HB_PX)
    X, Y, Z = yawed(0.0)
    draw_bottle(rig, centre() - Z * 3.4, X, Y, Z, "zelyonka", "rubber", frame_index(frame), label=None)
    return finish(rig)


def render_hbonus_c(frame: str = "A") -> Frame:
    """C: a bottle of iodine, brown glass, a white cap and label."""
    rig = gp.rig_for(HB_PX)
    X, Y, Z = yawed(0.0)
    draw_bottle(rig, centre() - Z * 3.4, X, Y, Z, "amber_glass", "tel_white", frame_index(frame))
    return finish(rig)


# ========================================================= armour bonus
AB_PX = 0.72                    # BON2A0 is 13x19
HELMET = (11.5, 13.0, 12.5)     # SSh-68: half width, half depth, height, cm
GLINT_AZ = (-50.0, -18.0, 14.0, 46.0)   # frames A-D: where the flash sits on a crown
CROWN_GLINT = (4.0, 2.4)        # cm: the flash's size on a crown (about 3x2 px at AB_PX)


def draw_helmet(rig: Rig, c, X, Y, Z, material: str = "olive_paint", base: float = 0.52,
                star: bool = True, k: int | None = None) -> None:
    """The SSh-68 resting on its rim: the dome, the flared skirt, a red
    star stencilled on the front; k (0-3) puts a flash on the crown."""
    rx, ry, rz = HELMET
    c = np.asarray(c, np.float64)
    rig.plate(c + Z * 0.6, X, Y, ellipse_poly(rx * 1.09, ry * 1.10), 1.2, material, base - 0.10, 0.8)
    dome(rig, c, (X * rx, Y * ry, Z * rz), material, base, 0.8)
    if star:
        p, n = on_dome(c, X, Y, Z, HELMET, 0.0, 30.0)
        decal_at(rig, p, n, Z, star_poly(0.0, 0.0, 2.6), "hull_red", 0.58)
    if k is not None:
        p, n = on_dome(c, X, Y, Z, HELMET, GLINT_AZ[k], 58.0)
        decal_at(rig, p, n, Z, rect(*CROWN_GLINT, -CROWN_GLINT[1] / 2), GLINT, 1.0, 0.0, lift=0.35)


def render_abonus_a(frame: str = "A") -> Frame:
    """A: the SSh-68 steel helmet (1968), Soviet green, a red star; a flash
    runs across its crown."""
    rig = gp.rig_for(AB_PX)
    X, Y, Z = yawed(16.0)
    draw_helmet(rig, centre() - Z * 6.0, X, Y, Z, k=frame_index(frame))
    return finish(rig)


PLATE = (17.0, 23.0, 1.2)


def render_abonus_b(frame: str = "A") -> Frame:
    """B: one armour plate standing on its edge, bare steel in a green
    webbing strap, a small red star; a flash slides across it."""
    k = frame_index(frame)
    rig = gp.rig_for(AB_PX * 1.05)
    X, Zc, Y = gp.pass_axes(20.0)
    w, h, th = PLATE
    base = centre() - Zc * h / 2
    poly = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h - 3.5), (w / 2 - 3.5, h), (-w / 2 + 3.5, h), (-w / 2, h - 3.5)]
    rig.plate(base, X, Zc, poly, th, "steel", 0.46, 0.85)
    face = face_fn(base, X, Zc, Y, th)
    rig._plane([face(s, t, 4) for s, t in rect(w + 0.6, 3.2, h * 0.40)], "canvas", 0.46, 0.6)
    rig._plane([face(s, t, 4) for s, t in star_poly(0.0, h * 0.76, 2.3)], "hull_red", 0.58, 0.6)
    s0 = -w / 2 + 1.0 + (w - 4.0) * k / 3
    rig._plane([face(s0, 2.0, 6), face(s0 + 1.4, 2.0, 6), face(s0 + 3.0, h - 2.0, 6), face(s0 + 1.6, h - 2.0, 6)],
               GLINT, 1.0, 0.0)
    return finish(rig)


def render_abonus_c(frame: str = "A") -> Frame:
    """C: the tank crew's padded helmet (шлемофон), black leather in three
    ribs, the ear pieces, the intercom lead on the floor; a flash on the
    crown."""
    k = frame_index(frame)
    rig = gp.rig_for(AB_PX)
    X, Y, Z = yawed(16.0)
    c = centre() - Z * 6.0
    rx, ry, rz = HELMET[0] * 0.95, HELMET[1], HELMET[2] * 0.95
    dome(rig, c, (X * rx, Y * ry, Z * rz), "rubber", 0.46, 0.8,
         seams=[(0, -0.36, 0.05, 0.16), (0, 0.36, 0.05, 0.16)])
    for sx in (-1, 1):
        rig.ellipsoid(c + X * sx * rx * 0.96 + Z * 3.6 - Y * 1.0, (X * 1.6, Y * 4.2, Z * 4.4), "rubber", 0.38, 0.8)
    plug = c - X * (rx + 3.0) - Y * (ry * 0.6) + Z * 0.6
    chain(rig, [c - X * rx * 0.98 + Z * 1.2 - Y * 1.0, c - X * (rx + 1.5) - Y * 3.0 + Z * 0.6, plug], 0.55,
          "rubber", 0.40)
    cylinder(rig, plug, plug - Y * 2.6, 0.9, "steel", 0.55, 0.85, caps=(None, 0.6))
    p, n = on_dome(c, X, Y, Z, (rx, ry, rz), GLINT_AZ[k], 58.0)
    decal_at(rig, p, n, Z, rect(*CROWN_GLINT, -CROWN_GLINT[1] / 2), GLINT, 1.0, 0.0, lift=0.35)
    return finish(rig)


# ================================================================ armour
ARMOUR_PX = 1.0                 # ARM1A0 is 37x28, ARM2A0 37x25
VEST_POLY = ((-16.0, 0.0), (16.0, 0.0), (17.0, 5.0), (16.0, 21.0), (12.0, 25.0), (12.0, 32.0), (6.0, 33.0),
             (3.5, 28.5), (-3.5, 28.5), (-6.0, 33.0), (-12.0, 32.0), (-12.0, 25.0), (-16.0, 21.0), (-17.0, 5.0))
VEST_TH = 5.0
VEST_K = 0.86                   # the vest's heights squashed: Doom's armour is wider than tall
VEST_YAW = -14.0
QUILT_ROWS = (5.5, 10.5, 15.5, 20.5)


def vest_axes(yaw: float = VEST_YAW):
    return gp.pass_axes(yaw)


def draw_vest(rig: Rig, c, X, Zc, Y, material: str, base: float, heavy: bool = False, gain_b: float = 0.0) -> None:
    """A Soviet flak vest standing as Doom stands its armour: the quilted
    front in rows, the padded collar, the zip, side buckles. heavy adds the
    raised chest plate, shoulder pads and a taller collar."""
    v = base + gain_b
    K = VEST_K
    th = VEST_TH * (1.3 if heavy else 1.0)
    rig.plate(c, X, Zc, [(s, t * K) for s, t in VEST_POLY], th, material, v, 0.8)
    face = face_fn(c, X, Zc, Y, th)
    for t in QUILT_ROWS:
        rig._plane([face(s, tt) for s, tt in rect(30.0, 0.8, t * K)], material, v - 0.18, 0.6)
    rig._plane([face(s, t, 2) for s, t in rect(0.9, 16.0 * K, 12.5 * K)], "rubber", 0.30 + gain_b, 0.6)
    collar_r = 2.4 if heavy else 1.6
    chain(rig, [face(-6.0, 32.6 * K, 20), face(-3.5, 28.8 * K, 20), face(3.5, 28.8 * K, 20), face(6.0, 32.6 * K, 20)],
          collar_r, material, v + 0.06, 0.8)
    for s in (-15.6, 15.6):
        for t in (7.0, 14.0):
            rig._plane([face(s + ds, t * K + dt, 3) for ds, dt in rect(2.0, 1.3, 0.0)], "steel", 0.58 + gain_b, 0.6)
    if heavy:
        rig.plate(c - Y * (th / 2 + 0.6) + Zc * 18.0 * K, X, Zc, rect(18.0, 13.0 * K, -6.5 * K), 1.2, material,
                  v + 0.08, 0.8)
        for s in (-9.0, 9.0):
            rig.capsule(face(s - 3.0, 32.0 * K, 30), face(s + 3.0, 32.6 * K, 30), 2.4, 2.4, material, v + 0.04, 0.8)


def armour_glint(rig: Rig, face) -> None:
    """Frame B's flash: a bright notch on the left shoulder, as the pass's."""
    K = VEST_K
    rig._plane([face(-11.5, 31.5 * K, 40), face(-8.0, 32.4 * K, 40), face(-11.0, 27.5 * K, 40)], GLINT, 1.0, 0.0)


def draw_cuirass(rig: Rig, c, X, Zc, Y, material: str, base: float, gain_b: float = 0.0) -> None:
    """The SN-42 steel breastplate (1942, still in stores in the 1970s): the
    chest plate over the abdomen plate, shaded across as if curved, rivets
    at the strap points and the canvas shoulder straps."""
    v = base + gain_b
    chest = ((-15.0, 14.0), (15.0, 14.0), (16.0, 22.0), (14.0, 31.0), (8.0, 34.0), (4.0, 30.0), (-4.0, 30.0),
             (-8.0, 34.0), (-14.0, 31.0), (-16.0, 22.0))
    belly = ((-13.5, 0.0), (13.5, 0.0), (14.5, 9.0), (14.0, 16.0), (-14.0, 16.0), (-14.5, 9.0))
    rig.plate(c + Y * 0.8, X, Zc, belly, 1.4, material, v - 0.04, 0.85, grad=(X, 0.012))
    rig.plate(c, X, Zc, chest, 1.4, material, v, 0.85, grad=(X, 0.012))
    face = face_fn(c, X, Zc, Y, 1.4)
    for s, t in ((-12.0, 29.0), (12.0, 29.0), (-12.5, 17.0), (12.5, 17.0), (-11.5, 3.0), (11.5, 3.0)):
        disc(rig, face(s, t, 6), -Y, 0.8, "steel", 0.66 + gain_b)
    for s in (-8.5, 8.5):
        chain(rig, [face(s, 33.0, 10), face(s * 0.97, 34.4, 10) + Y * 1.6, face(s * 1.05, 32.0, 10) + Y * 3.4], 1.1,
              "canvas", 0.40 + gain_b)


def render_garmor_a(frame: str = "A") -> Frame:
    """A: the flak vest, Soviet green, standing."""
    rig = gp.rig_for(ARMOUR_PX)
    X, Zc, Y = vest_axes()
    c = centre() - Zc * 16.0
    g = FRAME_GAIN if frame == "B" else 0.0
    draw_vest(rig, c, X, Zc, Y, "olive_paint", 0.50, gain_b=g)
    if frame == "B":
        armour_glint(rig, face_fn(c, X, Zc, Y, VEST_TH))
    return finish(rig)


def render_garmor_b(frame: str = "A") -> Frame:
    """B: the SN-42 breastplate in green paint, standing."""
    rig = gp.rig_for(ARMOUR_PX)
    X, Zc, Y = vest_axes()
    c = centre() - Zc * 16.0
    g = FRAME_GAIN if frame == "B" else 0.0
    draw_cuirass(rig, c, X, Zc, Y, "olive_paint", 0.52, gain_b=g)
    if frame == "B":
        armour_glint(rig, face_fn(c, X, Zc, Y, 1.4))
    return finish(rig)


def render_garmor_c(frame: str = "A") -> Frame:
    """C: the vest with the SSh-68 at its foot."""
    rig = gp.rig_for(ARMOUR_PX * 0.92)
    X, Zc, Y = vest_axes()
    c = centre() - Zc * 16.0
    g = FRAME_GAIN if frame == "B" else 0.0
    draw_vest(rig, c, X, Zc, Y, "olive_paint", 0.50, gain_b=g)
    Xh, Yh, Zh = yawed(30.0)
    draw_helmet(rig, c + X * 14.0 - Y * 14.0, Xh, Yh, Zh, base=0.50 + g, star=True)
    if frame == "B":
        armour_glint(rig, face_fn(c, X, Zc, Y, VEST_TH))
    return finish(rig)


def render_barmor_a(frame: str = "A") -> Frame:
    """A: the heavy vest (a ZhZT-71-type MVD armour, NOT VERIFIED as to its
    cover's colour) in palette v2's cobalt, so it reads BLUE at 1x: a
    raised chest plate, shoulder pads, a tall collar."""
    rig = gp.rig_for(ARMOUR_PX)
    X, Zc, Y = vest_axes(-10.0)
    c = centre() - Zc * 16.0
    g = FRAME_GAIN if frame == "B" else 0.0
    draw_vest(rig, c, X, Zc, Y, "cobalt", 0.52, heavy=True, gain_b=g)
    if frame == "B":
        armour_glint(rig, face_fn(c, X, Zc, Y, VEST_TH * 1.3))
    return finish(rig)


def render_barmor_b(frame: str = "A") -> Frame:
    """B: the same heavy vest in a v1 blue-grey cover (steel_blue): the
    test of whether v1 alone can say 'blue armour'."""
    rig = gp.rig_for(ARMOUR_PX)
    X, Zc, Y = vest_axes(-10.0)
    c = centre() - Zc * 16.0
    g = FRAME_GAIN if frame == "B" else 0.0
    draw_vest(rig, c, X, Zc, Y, "steel_cloth", 0.56, heavy=True, gain_b=g)
    if frame == "B":
        armour_glint(rig, face_fn(c, X, Zc, Y, VEST_TH * 1.3))
    return finish(rig)


def render_barmor_c(frame: str = "A") -> Frame:
    """C: the SN-42 in bare steel with a bare SSh-68 at its foot."""
    rig = gp.rig_for(ARMOUR_PX * 0.92)
    X, Zc, Y = vest_axes()
    c = centre() - Zc * 16.0
    g = FRAME_GAIN if frame == "B" else 0.0
    draw_cuirass(rig, c, X, Zc, Y, "steel", 0.50, gain_b=g)
    Xh, Yh, Zh = yawed(30.0)
    draw_helmet(rig, c + X * 13.0 - Y * 14.0, Xh, Yh, Zh, material="steel", base=0.48 + g, star=False)
    if frame == "B":
        armour_glint(rig, face_fn(c, X, Zc, Y, 1.4))
    return finish(rig)


# ============================================================== area map
MAP_PX = 1.0                    # PMAPA0 is 32x28
PLANSHET = (24.0, 30.0, 2.0)


def map_print(rig: Rig, face, s0: float, s1: float, t0: float, t1: float, k0: int = 2) -> None:
    """A 1:50 000 sheet at a glance: forest in green, a river in blue-grey,
    a fold line, the red arrow of the attack and a red circle."""
    W, H = s1 - s0, t1 - t0
    at = lambda u, v: (s0 + u * W, t0 + v * H)
    for blob in (((0.05, 0.55), (0.30, 0.70), (0.38, 0.95), (0.08, 0.92)),
                 ((0.60, 0.08), (0.92, 0.12), (0.95, 0.40), (0.70, 0.36))):
        rig._plane([face(*at(u, v), k0) for u, v in blob], "olive_paint", 0.50, 0.5)
    river = ((0.0, 0.30), (0.25, 0.42), (0.50, 0.36), (0.75, 0.55), (1.0, 0.50))
    for (u0, v0), (u1, v1) in zip(river[:-1], river[1:]):
        rig._plane([face(*at(u0, v0), k0 + 1), face(*at(u1, v1), k0 + 1), face(*at(u1, v1 + 0.06), k0 + 1),
                    face(*at(u0, v0 + 0.06), k0 + 1)], "steel", 0.42, 0.5)
    rig._plane([face(*at(0.5, 0.0), k0 + 1), face(*at(0.5 + 0.025, 0.0), k0 + 1), face(*at(0.5 + 0.025, 1.0), k0 + 1),
                face(*at(0.5, 1.0), k0 + 1)], "tel_white", 0.36, 0.5)
    arrow = ((0.18, 0.12), (0.52, 0.62), (0.46, 0.66), (0.66, 0.80), (0.62, 0.56), (0.57, 0.60), (0.24, 0.08))
    rig._plane([face(*at(u, v), k0 + 2) for u, v in arrow], "hull_red", 0.58, 0.5)
    for u, v in ((0.78, 0.74),):
        cs, ct = at(u, v)
        rig._plane([face(cs + 1.6 * np.cos(a), ct + 1.6 * np.sin(a), k0 + 2) for a in np.linspace(0, 2 * np.pi, 12,
                                                                                                    endpoint=False)],
                   "hull_red", 0.50, 0.5)


def map_glint(rig: Rig, face, s0: float, s1: float, t0: float, t1: float, k: int, kk: int = 9) -> None:
    """The flash crossing a sheet (or its celluloid) diagonally, by frame."""
    u = 0.05 + 0.27 * k
    W = s1 - s0
    a, b = s0 + u * W, s0 + (u + 0.10) * W
    sl = 0.18 * W
    rig._plane([face(a, t0 + 0.4, kk), face(b, t0 + 0.4, kk), face(b + sl, t1 - 0.4, kk), face(a + sl, t1 - 0.4, kk)],
               GLINT, 1.0, 0.0)


def render_allmap_a(frame: str = "A") -> Frame:
    """A: the officer's map case (планшет) standing, brown leather: the
    sheet under its celluloid window, the pencil loops, the strap run out
    to the floor; a flash crosses the celluloid."""
    k = frame_index(frame)
    rig = gp.rig_for(MAP_PX)
    X, Zc, Y = gp.pass_axes(-18.0)
    w, h, th = PLANSHET
    base = centre() - Zc * h / 2
    rig.plate(base + Zc * h / 2, X, Zc, rect(w, h, -h / 2), th, "leather", 0.50, 0.75)
    face = face_fn(base, X, Zc, Y, th)
    s0, s1, t0, t1 = -w / 2 + 2.0, w / 2 - 2.0, h * 0.34, h - 2.0
    rig._plane([face(s0, t0), face(s1, t0), face(s1, t1), face(s0, t1)], "tel_white", 0.64, 0.6)
    map_print(rig, face, s0 + 0.6, s1 - 0.6, t0 + 0.6, t1 - 0.6)
    for i, (s, mat) in enumerate(((-7.0, "hull_red"), (-5.2, "olive_paint"), (-3.4, "rubber"))):
        rig._plane([face(s + ds, t, 6) for ds, t in rect(1.0, 6.0, 2.4)], mat, 0.55, 0.6)
    rig._plane([face(s, t, 5) for s, t in rect(8.0, 1.6, 4.2)], "leather", 0.30, 0.6)
    rig._plane([face(s + 6.0, t, 5) for s, t in rect(2.4, h * 0.30, 0.6)], "leather", 0.38, 0.6)
    rig._plane([face(s + 6.0, t, 7) for s, t in rect(2.0, 1.6, h * 0.24)], "steel", 0.62, 0.6)
    top = face(-w / 2 + 1.0, h - 1.0, 4)
    chain(rig, [top, top - X * 4.0 + Zc * 2.0, base - X * (w / 2 + 6.0) - Y * 5.0, base - X * 2.0 - Y * 8.0], 0.8,
          "leather", 0.36)
    map_glint(rig, face, s0, s1, t0, t1, k)
    return finish(rig)


def render_allmap_b(frame: str = "A") -> Frame:
    """B: a topographic sheet folded in two and standing as a tent, its
    print on the face to the eye; a flash crosses it."""
    k = frame_index(frame)
    rig = gp.rig_for(MAP_PX)
    X, Y, Z = yawed(12.0, 30.0)
    c = centre() - Z * 6.0
    w, foot, ridge = 32.0, 8.0, 13.0
    back = [c + Y * foot - X * w / 2, c + Y * foot + X * w / 2, c + Z * ridge + X * w / 2, c + Z * ridge - X * w / 2]
    front = [c - Y * foot - X * w / 2, c - Y * foot + X * w / 2, c + Z * ridge + X * w / 2, c + Z * ridge - X * w / 2]
    rig._plane(back, "tel_white", 0.50, 0.7)
    rig._plane(front, "tel_white", 0.64, 0.7)
    up = Z * ridge + Y * foot
    L = float(np.linalg.norm(up))
    V = up / L
    n = unit(np.cross(X, V))
    n = n if n[2] < 0 else -n
    o = c - Y * foot

    def face(s, t, kk=1):
        return o + X * s + V * t + n * DECAL_LIFT * kk

    map_print(rig, face, -w / 2 + 1.0, w / 2 - 1.0, 1.0, L - 1.0)
    for s in (-w / 4, w / 4):
        rig._plane([face(s, 0.2, 2), face(s + 0.4, 0.2, 2), face(s + 0.4, L - 0.2, 2), face(s, L - 0.2, 2)],
                   "tel_white", 0.40, 0.5)
    map_glint(rig, face, -w / 2, w / 2, 0.0, L, k)
    return finish(rig)


def render_allmap_c(frame: str = "A") -> Frame:
    """C: the site plan rolled and tied with red tape, its last sheet run
    out on the floor towards the eye; a flash on the sheet."""
    k = frame_index(frame)
    rig = gp.rig_for(MAP_PX * 0.95)
    X, Y, Z = yawed(-8.0, 36.0)
    r, L = 3.6, 30.0
    c = centre() - Z * 2.0 + Y * 6.0
    cylinder(rig, c - X * L / 2 + Z * r, c + X * L / 2 + Z * r, r, "tel_white", 0.60, 0.8, caps=(0.72, 0.72))
    for s in (-L * 0.3, L * 0.3):
        rig.capsule(c + X * (s - 0.8) + Z * r, c + X * (s + 0.8) + Z * r, r * 1.04, r * 1.04, "hull_red", 0.55, 0.8,
                    open_ends=True)
    depth = 15.0
    o = c - Y * r * 0.9 + Z * 0.05

    def face(s, t, kk=1):
        return o + X * s - Y * (depth - t) + Z * (0.05 + 0.01 * kk)

    rig._plane([face(-L * 0.46, 0.0), face(L * 0.46, 0.0), face(L * 0.46, depth), face(-L * 0.46, depth)],
               "tel_white", 0.66, 0.6)
    map_print(rig, face, -L * 0.44, L * 0.44, 0.6, depth - 0.6)
    map_glint(rig, face, -L * 0.46, L * 0.46, 0.0, depth, k)
    return finish(rig)


# ============================================================== backpack
PACK_PX = 0.8                   # BPAKA0 is 26x30
SACK = (15.0, 11.0, 15.5)       # the veshmeshok's body, semi-axes, cm


def draw_sack(rig: Rig, c, X, Y, Z) -> None:
    """The veshmeshok (вещмешок, the 'sidor'): a round-bottomed canvas sack,
    its neck gathered and tied by the cord that runs down its face to the
    bottom corners, as the real one is slung."""
    rx, ry, rz = SACK
    body = c + Z * rz
    rig.ellipsoid(body, (X * rx, Y * ry, Z * rz), "canvas", 0.52, 0.8, seams=[(2, 0.45, 0.04, 0.14)])
    rig.capsule(c + Z * (2 * rz - 3.0), c + Z * (2 * rz + 5.0), 7.5, 3.4, "canvas", 0.50, 0.8)
    rig.ellipsoid(c + Z * (2 * rz + 7.0), (X * 4.8, Y * 4.0, Z * 3.4), "canvas", 0.58, 0.8)
    ring = [c + Z * (2 * rz + 3.2) + X * 5.2 * np.cos(a) - Y * 4.4 * np.sin(a)
            for a in np.linspace(np.pi * 0.05, np.pi * 0.95, 7)]
    chain(rig, ring, 0.9, "kraft", 0.50)
    for sx in (-1, 1):
        pts = []
        for el in (62.0, 40.0, 15.0, -10.0, -35.0, -55.0):
            az = sx * (24.0 + (62.0 - el) * 0.25)
            p, n = on_dome(body, X, Y, Z, (rx, ry, rz), az, el)
            pts.append(p + n * 0.5)
        chain(rig, [ring[0 if sx > 0 else -1]] + pts, 1.1, "kraft", 0.42)
        rig.ellipsoid(pts[-1], (X * 1.6, Y * 1.6, Z * 1.4), "kraft", 0.40, 0.8)


def render_backpack_a(frame: str = "A") -> Frame:
    """A: the veshmeshok standing slumped, khaki-green canvas and its cord."""
    rig = gp.rig_for(PACK_PX)
    X, Y, Z = yawed(20.0)
    draw_sack(rig, centre() - Z * 19.0, X, Y, Z)
    return finish(rig)


def render_backpack_b(frame: str = "A") -> Frame:
    """B: the RD-54 paratrooper's pack: a square canvas body, the flap over
    its top, two front pockets, straps and buckles."""
    rig = gp.rig_for(PACK_PX)
    X, Y, Z = yawed(20.0)
    w, d, h = 28.0, 13.0, 34.0
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    b.draw(rig, "canvas", 0.50)
    Box(b.c + Z * (h - 0.6), X, Y, Z, w + 0.8, d + 0.8, 1.2).draw(rig, "canvas", 0.58)
    b.decal(rig, "front", -w / 2 - 0.4, h - 10.0, w / 2 + 0.4, h + 0.6, "canvas", 0.60, lift=0.45)
    for s in (-7.0, 7.0):
        Box(b.c - Y * (d / 2 + 2.4) + X * s + Z * 1.5, X, Y, Z, 11.0, 4.8, 12.0).draw(rig, "canvas", 0.55)
        b.decal(rig, "front", s - 1.2, h - 14.0, s + 1.2, h - 2.0, "canvas", 0.34, lift=0.7)
        b.decal(rig, "front", s - 1.4, h - 12.0, s + 1.4, h - 10.2, "steel", 0.62, lift=0.9)
    return finish(rig)


def render_backpack_c(frame: str = "A") -> Frame:
    """C: the veshmeshok with the rolled greatcoat (скатка) over it as a
    soldier carries it, tied in three places."""
    rig = gp.rig_for(PACK_PX * 0.92)
    X, Y, Z = yawed(20.0)
    c = centre() - Z * 19.0
    draw_sack(rig, c, X, Y, Z)
    rx, ry, rz = SACK
    arc = [c - Y * (ry * 0.2) + X * (rx + 2.0) * np.cos(a) + Z * (rz * 0.35 + (2 * rz + 2.0) * np.sin(a))
           for a in np.linspace(0.0, np.pi, 11)]
    chain(rig, arc, 3.6, "greatcoat", 0.52, 0.8)
    for i in (2, 5, 8):
        rig.capsule(arc[i] - (arc[i + 1] - arc[i - 1]) * 0.08, arc[i] + (arc[i + 1] - arc[i - 1]) * 0.08, 3.8, 3.8,
                    "rubber", 0.36, 0.7, open_ends=True)
    return finish(rig)


# ================================================================ passes
def render_card(ground: str, gbase: float, stamp: str, sbase: float, frame: str = "A") -> Frame:
    """SDKB's laminated card (gen_pickups.render_pass_b) line for line, the
    ground and the stamp as arguments: the blue pass's family."""
    rig = gp.rig_for(gp.PASS_PX_PER_CM)
    X, Zc, Y = gp.pass_axes(-16.0)
    w, h, th = gp.CARD
    g = gp.GLINT_GAIN if frame == "B" else 0.0
    base = centre() - Zc * h / 2
    rig.plate(base + Zc * h / 2, X, Zc, rect(w, h, -h / 2), th, ground, gbase + g, 0.75)
    face = lambda s, t, k=1: base - Y * (th / 2 + DECAL_LIFT * k) + X * s + Zc * t
    rig._plane([face(s, t) for s, t in rect(w - 1.6, 5.6, h - 7.0)], "tel_white", 0.66 + g, 0.6)
    rig._plane([face(s, t, 2) for s, t in rect(3.4, 4.2, h - 6.3)], "dummy", 0.30 + g, 0.6)
    rig._plane([face(s, t, 3) for s, t in rect(1.4, 1.6, h - 5.0)], "dummy", 0.62 + g, 0.6)
    rig._plane([face(s + 2.0, t, 4) for s, t in star_poly(0.0, h - 6.6, 1.5, 0.75)], stamp, sbase + g, 0.6)
    for t in (2.2, 3.6):
        rig._plane([face(s, tt, 1) for s, tt in rect(w - 2.4, 0.55, t)], "tel_white", 0.62 + g, 0.6)
    if frame == "B":
        rig._plane([face(s, t, 5) for s, t in ((w / 2 - 2.4, h - 0.6), (w / 2 - 0.6, h - 0.6),
                                               (w / 2 - 0.6, h - 2.2))], "tel_white", 0.95, 0.4)
    return finish(rig)


def render_band_card(colour: str, cbase: float, frame: str = "A") -> Frame:
    """B: a cream card crossed by a broad diagonal band in the key's colour
    (the all-areas stripe of a works pass), the photograph and two lines."""
    rig = gp.rig_for(gp.PASS_PX_PER_CM)
    X, Zc, Y = gp.pass_axes(-16.0)
    w, h, th = gp.CARD
    g = gp.GLINT_GAIN if frame == "B" else 0.0
    base = centre() - Zc * h / 2
    rig.plate(base + Zc * h / 2, X, Zc, rect(w, h, -h / 2), th, "tel_white", 0.60 + g, 0.75)
    face = lambda s, t, k=1: base - Y * (th / 2 + DECAL_LIFT * k) + X * s + Zc * t
    bw = 2.6
    rig._plane([face(-w / 2, 0.4 - bw), face(-w / 2, 0.4 + bw), face(w / 2, h * 0.70 + bw), face(w / 2, h * 0.70 - bw)],
               colour, cbase + g, 0.6)
    rig._plane([face(s - 2.0, t, 2) for s, t in rect(3.4, 4.2, h - 5.6)], "dummy", 0.30 + g, 0.6)
    rig._plane([face(s - 2.0, t, 3) for s, t in rect(1.4, 1.6, h - 4.3)], "dummy", 0.62 + g, 0.6)
    for t in (h - 3.0, h - 4.4):
        rig._plane([face(s + 2.6, tt, 2) for s, tt in rect(3.0, 0.55, t)], "rubber", 0.40 + g, 0.6)
    if frame == "B":
        rig._plane([face(s, t, 5) for s, t in ((w / 2 - 2.4, h - 0.6), (w / 2 - 0.6, h - 0.6),
                                               (w / 2 - 0.6, h - 2.2))], "tel_white", 0.95, 0.4)
    return finish(rig)


def render_booklet(cover: str, cbase: float, star: str, frame: str = "A") -> Frame:
    """C: SDKB's rejected option A (the closed пропуск booklet,
    gen_pickups.render_pass_a) in the key's colour."""
    rig = gp.rig_for(gp.PASS_PX_PER_CM)
    X, Zc, Y = gp.pass_axes(24.0)
    w, h, th = gp.BOOKLET
    g = gp.GLINT_GAIN if frame == "B" else 0.0
    base = centre() - Zc * h / 2
    rig.plate(base + Zc * h / 2, X, Zc, rect(w, h, -h / 2), th, cover, cbase + g, 0.75)
    rig.plate(base + Zc * h / 2 + X * 0.25, X, Zc, rect(w - 0.4, h - 0.5, -(h - 0.5) / 2), th * 0.75,
              "tel_white", 0.62 + g, 0.75)
    face = lambda s, t: base - Y * (th / 2 + DECAL_LIFT) + X * s + Zc * t
    rig._plane([face(s, t) for s, t in star_poly(0.0, h * 0.62, 2.3)], star, 0.66 + g, 0.6)
    rig._plane([face(s, t) for s, t in rect(5.6, 1.2, h * 0.28)], star, 0.60 + g, 0.6)
    if frame == "B":
        rig._plane([face(s, t) for s, t in ((-w / 2 + 0.6, h - 1.2), (-w / 2 + 2.2, h - 0.6),
                                            (-w / 2 + 0.6, h - 0.6))], "tel_white", 0.95, 0.4)
    return finish(rig)


KEY_STYLE = {   # ground material, ground value, stamp material, stamp value (option A)
    "ykey": ("pass_yellow", 0.56, "hull_red", 0.55),
    "rkey": ("pass_red", 0.54, "brass", 0.72),
}


def key_options(slug: str):
    ground, gb, stamp, sb = KEY_STYLE[slug]
    booklet_star = "hull_red" if slug == "ykey" else "brass"
    return (lambda fr: render_card(ground, gb, stamp, sb, fr),
            lambda fr: render_band_card(ground, gb, fr),
            lambda fr: render_booklet(ground, gb, booklet_star, fr))


# ============================================================ Katyusha
HK_VARIANT = "B"                # D51: "de katiushka me flipa la B"
HK_SMALL = 0.82                 # option B: the D51 pose at Freedoom's footprint
HK_SIDE = (1.05, (1.0, 0.10), -12.0, 3.0)   # option C: px/cm, turn, roll, tilt


def katyusha_pose(px: float, turn, roll: float, tilt: float) -> Frame:
    """gen_weapon.render_katyusha_pickup with its pose as arguments."""
    rig = gw.gun_pickup_rig(px, gw.PICKUP_W, 56)
    right, away, up = floor_basis()
    U = unit(right * turn[0] - away * turn[1])
    t = np.deg2rad(roll)
    side = unit(np.cross(U, up))
    roll_up = unit(up * np.cos(t) + side * np.sin(t))
    k = np.deg2rad(tilt)
    U, roll_up = unit(U * np.cos(k) - up * np.sin(k)), perp(roll_up, unit(U * np.cos(k) - up * np.sin(k)))
    gw.draw_katyusha3(rig, np.array([0.0, 0.0, gw.PICKUP_DIST]) - U * 26.0, U, roll_up, gw.HK3_VARIANT[HK_VARIANT],
                      handle=False, sling_to=None)
    return finish(rig)


def render_katyusha_a(frame: str = "A") -> Frame:
    """A: the D51 draft exactly (work/art/weapons_2d/katyusha/SDHPA0.png)."""
    return gw.render_katyusha_pickup(HK_VARIANT)


def render_katyusha_b(frame: str = "A") -> Frame:
    return katyusha_pose(gw.HK3_PICKUP_PX_PER_CM * HK_SMALL, gw.HK3_PICKUP_TURN, gw.HK3_PICKUP_ROLL,
                         gw.HK3_PICKUP_TILT)


def render_katyusha_c(frame: str = "A") -> Frame:
    px, turn, roll, tilt = HK_SIDE
    return katyusha_pose(px, turn, roll, tilt)


# ================================================================ catalogue
@dataclass(frozen=True)
class Option:
    key: str
    title: str
    render: Callable[[str], Frame]
    msg_en: str
    msg_ru: str
    palette: int = 1            # 2: uses a v2 ramp (cobalt)


@dataclass(frozen=True)
class Item:
    slug: str
    lump: str
    frames: str
    doom: str                   # the Doom class it replaces
    placeholder: str            # the Freedoom sprite it wears today
    actor: str                  # the class the install adds (proposal)
    name: str
    options: tuple[Option, ...]
    recommended: str
    why: str
    msg_id: str
    owners: tuple[str, ...] = field(default=())   # words a MOD-SPEC line naming the lump must carry

    def option(self, key: str) -> Option:
        return next(o for o in self.options if o.key == key)


_Y = key_options("ykey")
_R = key_options("rkey")
ITEMS: tuple[Item, ...] = (
    Item("stim", "SDBN", "A", "Stimpack", "STIM", "SD_Stimpack", "Stimpack (+10)",
         (Option("A", "Field dressing packet (ИПП)", render_stim_a, "A field dressing.", "Перевязочный пакет."),
          Option("B", "AI-2 personal kit, orange", render_stim_b, "A personal first-aid kit.",
                 "Аптечка индивидуальная."),
          Option("C", "Bandage roll", render_stim_c, "A bandage.", "Бинт.")),
         "A", "the first-aid sign on khaki reads 'first aid' from above, and its size says 'small'; "
              "the AI-2 is the most 1970s object but at 1x an orange tile reads as a box of something, not as health; "
              "the bandage is a white smudge on a light floor",
         "SD_GOT_STIMPACK"),
    Item("medikit", "SDMD", "A", "Medikit", "MEDI", "SD_Medikit", "Medikit (+25)",
         (Option("A", "Enamelled first-aid box (аптечка)", render_medi_a, "A first-aid box.", "Аптечка."),
          Option("B", "Medic's satchel (сумка санитарная)", render_medi_b, "A medic's satchel.", "Санитарная сумка."),
          Option("C", "Green field medical chest", render_medi_c, "A field medical chest.",
                 "Полевой медицинский ящик.")),
         "A", "white and red is the one colour pair in the campaign that means health, and the box is the shape every "
              "Soviet workshop hung on its wall; the satchel is right for a soldier but khaki on khaki floors halves "
              "its read; the green chest is one more crate among the ammunition crates",
         "SD_GOT_MEDIKIT"),
    Item("hbonus", "SDHB", "ABCD", "HealthBonus", "BON1", "SD_HealthBonus", "Health bonus (+1)",
         (Option("A", "Ampoule of glucose", render_hbonus_a, "An ampoule of glucose.", "Ампула глюкозы."),
          Option("B", "Bottle of zelyonka", render_hbonus_b, "Zelyonka.", "Зелёнка."),
          Option("C", "Bottle of iodine", render_hbonus_c, "Iodine.", "Йод.")),
         "B", "zelyonka is the antiseptic every Soviet child knows, and its green keeps the bonus Freedoom's colour, "
              "so a player who learnt 'small green bottle = +1' keeps that; the ampoule is too thin to read at 1x; "
              "iodine brown sinks into the floors",
         "SD_GOT_HEALTHBONUS"),
    Item("abonus", "SDAB", "ABCD", "ArmorBonus", "BON2", "SD_ArmorBonus", "Armour bonus (+1)",
         (Option("A", "SSh-68 steel helmet", render_abonus_a, "A steel helmet.", "Стальная каска."),
          Option("B", "Armour plate in webbing", render_abonus_b, "An armour plate.", "Бронепластина."),
          Option("C", "Tank crew helmet (шлемофон)", render_abonus_c, "A tank crew helmet.", "Шлемофон.")),
         "A", "Doom's armour bonus is a helmet and the SSh-68 is THE Soviet helmet of 1977: its dome and flared skirt "
              "are a silhouette nothing else on the floor has; the plate is a grey card; the tank helmet is a black "
              "blob on dark floors (fine for Tankograd, lost in the metro)",
         "SD_GOT_ARMORBONUS"),
    Item("garmor", "SDAG", "AB", "GreenArmor", "ARM1", "SD_GreenArmor", "Green armour (100)",
         (Option("A", "Flak vest, quilted", render_garmor_a, "A flak vest.", "Бронежилет."),
          Option("B", "SN-42 breastplate, painted", render_garmor_b, "A steel breastplate, SN-42.",
                 "Стальной нагрудник СН-42."),
          Option("C", "Flak vest and helmet", render_garmor_c, "A flak vest and a helmet.", "Бронежилет и каска.")),
         "A", "it stands as Doom stands its armour, green as the class it is, the quilting and the collar say 'vest'; "
              "the SN-42 is a better story but reads as a shield; vest and helmet together repeat the armour bonus",
         "SD_GOT_ARMOR"),
    Item("barmor", "SDAH", "AB", "BlueArmor", "ARM2", "SD_BlueArmor", "Blue armour (200)",
         (Option("A", "Heavy vest, cobalt cover (palette v2)", render_barmor_a, "Heavy body armour!",
                 "Тяжёлый бронежилет!", palette=2),
          Option("B", "Heavy vest, blue-grey cover (v1)", render_barmor_b, "Heavy body armour!",
                 "Тяжёлый бронежилет!"),
          Option("C", "Bare-steel SN-42 and helmet", render_barmor_c, "A steel breastplate and helmet!",
                 "Стальной нагрудник и каска!")),
         "A", "the class is told by its colour, and only v2's cobalt reads blue at 1x (B is the proof: v1's steel blue "
              "reads grey, a dirty green vest's twin); same cut as the green vest, heavier, so the pair reads as one "
              "family",
         "SD_GOT_MEGAARMOR"),
    Item("allmap", "SDMP", "ABCD", "Allmap", "PMAP", "SD_Allmap", "Computer area map",
         (Option("A", "Officer's map case (планшет)", render_allmap_a,
                 "A commander's map case. The whole area is on it.", "Командирский планшет. На карте — вся местность."),
          Option("B", "Topographic sheet, folded, standing", render_allmap_b, "A survey map of the area.",
                 "Топографическая карта местности."),
          Option("C", "Site plan, rolled", render_allmap_c, "The site plan.", "План объекта.")),
         "A", "the planshet is the most Soviet object in the set and stands like Doom's map, its window lit by the "
              "flash; the folded sheet is a white tent at 1x; the roll reads as a pipe",
         "SD_GOT_MAP"),
    Item("backpack", "SDBP", "A", "Backpack", "BPAK", "SD_Backpack", "Backpack",
         (Option("A", "Veshmeshok (вещмешок)", render_backpack_a, "Quartermaster's kitbag. Everything you can carry!",
                 "Вещмешок старшины. Всё, что унесёшь!"),
          Option("B", "RD-54 paratrooper pack", render_backpack_b, "A paratrooper's pack. Everything you can carry!",
                 "Ранец десантника. Всё, что унесёшь!"),
          Option("C", "Veshmeshok with the greatcoat roll", render_backpack_c,
                 "Quartermaster's kitbag. Everything you can carry!", "Вещмешок старшины. Всё, что унесёшь!")),
         "A", "the line already in LANGUAGE says вещмешок; its round body and tied neck read as a sack at any size; "
              "the RD-54 is a green box, and the greatcoat roll turns the sack into a horseshoe",
         "SD_GOT_BACKPACK"),
    Item("ykey", "SDKY", "AB", "YellowCard", "YKEY", "SD_YellowPass", "The yellow pass (пропуск)",
         (Option("A", "SDKB's card in yellow", _Y[0], "Yellow pass.", "Жёлтый пропуск."),
          Option("B", "Cream card, yellow band", _Y[1], "Yellow pass.", "Жёлтый пропуск."),
          Option("C", "Yellow booklet", _Y[2], "Yellow pass.", "Жёлтый пропуск.")),
         "A", "the blue pass's own card (D63), so the three passes are one family and differ only in the colour that "
              "names the door; the band card is half cream, and the booklet is the design the CEO did not choose",
         "SD_PICKUP_YELLOWPASS"),
    Item("rkey", "SDKK", "AB", "RedCard", "RKEY", "SD_RedPass", "The red pass (пропуск)",
         (Option("A", "SDKB's card in red, gold stamp", _R[0], "Red pass.", "Красный пропуск."),
          Option("B", "Cream card, red band", _R[1], "Red pass.", "Красный пропуск."),
          Option("C", "Red booklet, gold star", _R[2], "Red pass.", "Красный пропуск.")),
         "A", "as the yellow: SDKB's card; on red the stamp turns gold, a red star would vanish",
         "SD_PICKUP_REDPASS"),
    Item("katyusha", "SDHP", "A", "BFG9000", "BFUG", "SD_HandKatyusha", "The hand Katyusha on the floor",
         (Option("A", "D51 variant B, as drafted", render_katyusha_a,
                 "You got the hand Katyusha. Prototype. Do not drop it.",
                 "Вы подобрали ручную «Катюшу». Опытный образец. Не ронять."),
          Option("B", "The same at Freedoom's footprint", render_katyusha_b,
                 "You got the hand Katyusha. Prototype. Do not drop it.",
                 "Вы подобрали ручную «Катюшу». Опытный образец. Не ронять."),
          Option("C", "Side-on, the six tubes in profile", render_katyusha_c,
                 "You got the hand Katyusha. Prototype. Do not drop it.",
                 "Вы подобрали ручную «Катюшу». Опытный образец. Не ронять.")),
         "A", "the draft is good: grey tubes in green bands, olive warheads with red rings and the grip read as a "
              "weapon and as THIS weapon; it is a secret's reward (D68) and may be bigger than the other guns. B is "
              "the fallback if it looks too big in the engine; C hides the six tubes behind each other",
         "SD_PICKUP_KATYUSHA", owners=("Hand Katyusha", "SD_HandKatyusha", "BFG9000")),
)
ITEM = {i.slug: i for i in ITEMS}
ITEM_LUMPS = tuple(row[1] for row in NAMES)

# D80 (2026-10-20): the CEO's choice, "todos los que tú recomiendas por
# defecto, salvo SDAG C, SDAH C, SDBP B"; the Katyusha at its drafted size
# (A). These are the options installed in assets/sprites/pickups/.
CHOSEN = {"stim": "A", "medikit": "A", "hbonus": "B", "abonus": "A", "garmor": "C", "barmor": "C",
          "allmap": "A", "backpack": "B", "ykey": "A", "rkey": "A", "katyusha": "A"}

# Freedoom's sprites (frame A), measured on freedoom2.wad 0.13.0: the size
# an option is held against (tests/test_gen_items.py, SIZE_RANGE).
PLACEHOLDER_SIZE = {"STIM": (19, 10), "MEDI": (29, 20), "BON1": (11, 15), "BON2": (13, 19), "ARM1": (37, 28),
                    "ARM2": (37, 25), "PMAP": (32, 28), "BPAK": (26, 30), "YKEY": (14, 21), "RKEY": (14, 21),
                    "BFUG": (56, 24)}
SIZE_RANGE = (0.6, 1.9)         # as gen_pickups' test: larger side over the placeholder's
KEY_RAMP = {"ykey": "hazard_yellow", "rkey": "flag_red"}
KEY_SHARE_MIN = 0.40            # a key must be at least this share of its colour (SDKB's cobalt test)


def render_option(item: Item, opt: Option, frame: str = "A") -> Frame:
    with item_materials():
        return opt.render(frame)


def lump_name(item: Item, frame: str) -> str:
    return f"{item.lump}{frame}0"


# ================================================================ HUD keys
# The fullscreen HUD draws a key's Inventory.Icon, which for Doom's cards is
# the status bar's own STKEYS0-2 (gzdoom.pk3 g4.14.2 doom_sbar.zs: the bar
# names STKEYS* directly, the fullscreen loop draws i.Icon). Shipping our
# STKEYS0-2 under those names changes both at once. 7x5 like Freedoom's.
KEY_ICON = ("OOOOOOO",
            "OWWGGGO",
            "OWPGSGO",
            "OGGGGGO",
            "OOOOOOO")
KEY_ICON_COLOURS = {     # lump: (ground ramp, stamp (ramp, step))
    "STKEYS0": ("mosaic_cobalt", ("flag_red", 11)),
    "STKEYS1": ("hazard_yellow", ("flag_red", 11)),
    "STKEYS2": ("flag_red", ("hazard_yellow", 13)),
}


def key_icon(lump: str) -> np.ndarray:
    ground, (sr, si) = KEY_ICON_COLOURS[lump]
    g = palette_mod.ramp_colours(ground)
    cols = {"O": g[4], "G": g[10], "W": palette_mod.ramp_colours("plaster_warm")[13],
            "P": palette_mod.ramp_colours("concrete_cold")[9], "S": palette_mod.ramp_colours(sr)[si]}
    return np.array([[cols[ch] for ch in row] for row in KEY_ICON], np.uint8)


def save_indexed_v2(rgb: np.ndarray, path: Path) -> Path:
    """An indexed PNG on palette v2 (graphics/ must be indexed, check_pk3)."""
    pal = palette_mod.colours(2)
    lut = {tuple(c): i for i, c in enumerate(pal)}
    idx = np.array([[lut[tuple(int(v) for v in px)] for px in row] for row in rgb], np.uint8)
    im = Image.fromarray(idx, "P")
    im.putpalette([v for c in pal for v in c])
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=False)
    return path


# ================================================================== scenes
FLOORS = {   # scene: (wall, floor, sector light, what it stands for)
    "map01": (gw.TEX / "SDCONC1.png", gw.FLATS / "SDFLR2.png", 144, "MAP01 Zarya-7: SDFLR2 before SDCONC1, light 144"),
    "map03": (PROJECT_ROOT / "assets" / "textures" / "factory" / "SDBRCK1.png",
              PROJECT_ROOT / "assets" / "flats" / "factory" / "SDFLR4.png", 160,
              "MAP03 Tankograd: SDFLR4 chequer plate before SDBRCK1, light 160"),
}
SCENE_GAP = 12
SCENE_FLOOR_H = 26
SCENE_FLOOR_LINE = 13
SCENE_HEADROOM = 8


def scene(frames: list[Frame | None], where: str = "map01") -> np.ndarray:
    """gen_pickups.scene with the wall and floor as arguments: each sprite
    placed by its own grAb on the floor band, all in the same light."""
    wall_p, floor_p, light, _ = FLOORS[where]
    real = [f for f in frames if f is not None]
    widths = [f.rgba.shape[1] if f is not None else 16 for f in frames]
    above = max([int(f.offsets()[1]) for f in real] + [16])
    wall_h = max(24, above - SCENE_FLOOR_LINE + SCENE_HEADROOM)
    W = sum(widths) + SCENE_GAP * (len(frames) + 1)
    wall, floor = gw.texture(wall_p), gw.texture(floor_p)
    reps = (-(-wall_h // wall.shape[0]), -(-W // wall.shape[1]), 1)
    wl = np.tile(wall, reps)[wall.shape[0] * reps[0] - wall_h:, :W]
    fl = np.tile(floor, (3, -(-W // floor.shape[1]), 1))[:SCENE_FLOOR_H * 3, :W]
    fl = np.asarray(Image.fromarray(np.ascontiguousarray(fl), "RGB").resize((W, SCENE_FLOOR_H),
                                                                            Image.Resampling.NEAREST))
    canvas = np.concatenate([wl, fl], 0).copy()
    x = SCENE_GAP
    for f, wd in zip(frames, widths):
        if f is not None:
            gx, gy = (int(v) for v in f.offsets())
            x0, y0 = x + wd // 2 - gx, wall_h + SCENE_FLOOR_LINE - gy
            ys, xs = np.nonzero(f.rgba[..., 3] > 0)
            cy, cx = ys + y0, xs + x0
            ok = (cy >= 0) & (cy < canvas.shape[0]) & (cx >= 0) & (cx < W)
            canvas[cy[ok], cx[ok]] = f.rgba[ys[ok], xs[ok], :3]
        x += wd + SCENE_GAP
    return gp.light_scene(canvas, light, 2)


def floor_luma(where: str) -> float:
    _, floor_p, light, _ = FLOORS[where]
    return float(luma(gw.light_rgb(gw.texture(floor_p), light)).mean())


def freedoom(name: str, frame: str = "A") -> Frame | None:
    f = gw.freedoom_sprite(f"{name}{frame}0")
    if f is None:
        return None
    lo, to = f.offsets()
    return Frame(f.rgba, f.mat, lo, to, False)


def sdkb(frame: str = "A") -> Frame | None:
    """The installed blue pass, for the family comparison."""
    p = SDKB_DIR / f"SDKB{frame}0.png"
    if not p.is_file():
        return None
    with Image.open(p) as im:
        a = np.asarray(im.convert("RGBA")).copy()
    return Frame(a, np.zeros(a.shape[:2], np.int16), a.shape[1] // 2, a.shape[0], False)


def metrics(f: Frame, floors: dict[str, float]) -> dict:
    a = f.rgba[..., 3] > 0
    lum = luma(f.rgba[..., :3])[a]
    m = {"size": [int(f.rgba.shape[1]), int(f.rgba.shape[0])], "offsets": [int(v) for v in f.offsets()],
         "luma": round(float(lum.mean()), 1)}
    for k, fl in floors.items():
        m[f"contrast_{k}"] = round(float(abs(lum.mean() - fl)), 1)
    return m


def colour_share(f: Frame, ramp: str) -> float:
    cols = set(map(tuple, palette_mod.ramp_colours(ramp)))
    px = f.rgba[f.rgba[..., 3] > 0][:, :3]
    return float(np.mean([tuple(int(v) for v in p) in cols for p in px]))


# ================================================================ pixel font
# A 3x5 font of our own for the PNG sheet's labels: no system font, so the
# sheet reproduces on both machines (CLAUDE.md, text-bearing assets).
GLYPHS = {
    "A": "010101111101101", "B": "110101110101110", "C": "011100100100011", "D": "110101101101110",
    "E": "111100110100111", "F": "111100110100100", "G": "011100101101011", "H": "101101111101101",
    "I": "111010010010111", "J": "001001001101010", "K": "101101110101101", "L": "100100100100111",
    "M": "101111111101101", "N": "110101101101101", "O": "010101101101010", "P": "110101110100100",
    "Q": "010101101110011", "R": "110101110101101", "S": "011100010001110", "T": "111010010010010",
    "U": "101101101101111", "V": "101101101101010", "W": "101101111111101", "X": "101101010101101",
    "Y": "101101010010010", "Z": "111001010100111", "0": "111101101101111", "1": "010110010010111",
    "2": "110001010100111", "3": "110001010001110", "4": "101101111001001", "5": "111100110001110",
    "6": "011100111101111", "7": "111001010010010", "8": "111101111101111", "9": "111101111001110",
    "-": "000000111000000", ".": "000000000000010", ":": "000010000010000", "/": "001001010100100",
    "(": "010100100100010", ")": "010001001001010", ",": "000000000010100", "+": "000010111010000",
    " ": "000000000000000",
}
LABEL_SCALE = 2
SHEET_BG = (28, 28, 32)
SHEET_INK = (214, 208, 190)


def label(text: str, scale: int = LABEL_SCALE) -> np.ndarray:
    text = text.upper()
    w = (4 * len(text) - 1) * scale if text else scale
    out = np.zeros((5 * scale, max(w, 1), 3), np.uint8)
    out[:] = SHEET_BG
    for i, ch in enumerate(text):
        bits = GLYPHS.get(ch, GLYPHS[" "])
        for r in range(5):
            for c in range(3):
                if bits[r * 3 + c] == "1":
                    y, x = r * scale, (i * 4 + c) * scale
                    out[y:y + scale, x:x + scale] = SHEET_INK
    return out


def zoom(img: np.ndarray, k: int) -> np.ndarray:
    return np.repeat(np.repeat(img, k, 0), k, 1)


def stack(blocks: list[np.ndarray], pad: int = 10) -> np.ndarray:
    W = max(b.shape[1] for b in blocks) + 2 * pad
    rows = []
    for b in blocks:
        row = np.zeros((b.shape[0], W, 3), np.uint8)
        row[:] = SHEET_BG
        row[:, pad:pad + b.shape[1]] = b
        rows.append(row)
        gap = np.zeros((pad, W, 3), np.uint8)
        gap[:] = SHEET_BG
        rows.append(gap)
    return np.concatenate(rows[:-1], 0)


# ================================================================== build
def anim_frames(item: Item) -> list[tuple[str, int]]:
    """(frame, ms) in Doom's order for the GIF."""
    return [(f, int(round(t * TIC_MS / 10.0)) * 10) for f, t, _ in SPAWN[item.doom] if t > 0]


def gif_bytes(frames: list[np.ndarray], durations: list[int]) -> bytes:
    ims = [Image.fromarray(f, "RGB") for f in frames]
    buf = io.BytesIO()
    ims[0].save(buf, "GIF", save_all=True, append_images=ims[1:], duration=durations, loop=0, optimize=False)
    return buf.getvalue()


def img_tag(data: bytes, mime: str, w: int, h: int, alt: str) -> str:
    src = f"data:{mime};base64," + base64.b64encode(data).decode("ascii")
    return f'<img class="px" src="{src}" width="{w}" height="{h}" alt="{html.escape(alt)}" title="{html.escape(alt)}">'


def png_bytes(img: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(img, "RGB").save(buf, "PNG", optimize=True)
    return buf.getvalue()


def view(label_: str, img: np.ndarray, k: int) -> str:
    h, w = img.shape[:2]
    tag = img_tag(png_bytes(img), "image/png", w * k, h * k, label_)
    return f'<div class="v"><b>{html.escape(label_)}</b>{tag}</div>'


def render_all(items=ITEMS) -> dict[str, dict[str, dict[str, Frame]]]:
    """Frame A of every option and every frame of the recommended and the
    chosen one (D80)."""
    out: dict = {}
    for it in items:
        out[it.slug] = {}
        for o in it.options:
            frames = it.frames if o.key in (it.recommended, CHOSEN[it.slug]) else "A"
            out[it.slug][o.key] = {fr: render_option(it, o, fr) for fr in frames}
    return out


def render_chosen(items=ITEMS) -> dict[str, dict[str, Frame]]:
    """Every frame of the option the CEO chose for each object (D80)."""
    return {it.slug: {fr: render_option(it, it.option(CHOSEN[it.slug]), fr) for fr in it.frames} for it in items}


def install(out_dir: Path = OUT_DIR) -> list[Path]:
    """--install: the chosen sets and the key icons into work/, and a check
    sheet of the set on both floors and its animations at 4x. Nothing in
    docs/ or assets/."""
    written = []
    chosen = render_chosen()
    for it in ITEMS:
        for fr, f in chosen[it.slug].items():
            written.append(gw.save_sprite(f, out_dir / it.slug / CHOSEN[it.slug] / f"{lump_name(it, fr)}.png"))
    for lump in KEY_ICON_COLOURS:
        written.append(save_indexed_v2(key_icon(lump), out_dir / "hud" / f"{lump}.png"))
    rec = [chosen[it.slug]["A"] for it in ITEMS]
    rec_k = rec[:10] + [sdkb()] + rec[10:]
    blocks = []
    for where in FLOORS:
        img = scene(rec_k, where)
        blocks += [label(f"d80 chosen set 1x and 3x - {where}"), img, zoom(img, 3)]
    for it in ITEMS:
        if len(it.frames) > 1:
            blocks += [label(f"{it.lump} {CHOSEN[it.slug]} frames {' '.join(it.frames)} 4x"),
                       np.concatenate([np.pad(zoom(scene([chosen[it.slug][fr]], "map01"), 4),
                                              ((0, 0), (0, 8), (0, 0)), constant_values=0) for fr in it.frames], 1)]
    sheet = out_dir / "sheet" / "install_D80.png"
    sheet.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(stack(blocks), "RGB").save(sheet, optimize=True)
    written.append(sheet)
    return written


def build(stamp: str, out_dir: Path = OUT_DIR, preview_dir: Path = PREVIEW_DIR) -> tuple[Path, dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet_dir = out_dir / "sheet"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    floors = {k: floor_luma(k) for k in FLOORS}
    rendered = render_all()
    allm: dict = {"floors": {k: {"luma": round(v, 1), "light": FLOORS[k][2]} for k, v in floors.items()}, "items": {}}
    cards, png_blocks = [], []
    for it in ITEMS:
        im: dict = {"lump": it.lump, "doom": it.doom, "actor": it.actor, "placeholder": f"{it.placeholder}A0",
                    "recommended": it.recommended, "frames": it.frames, "options": {}}
        for o in it.options:
            for fr, f in rendered[it.slug][o.key].items():
                gw.save_sprite(f, out_dir / it.slug / o.key / f"{lump_name(it, fr)}.png")
            im["options"][o.key] = {fr: metrics(f, floors) for fr, f in rendered[it.slug][o.key].items()}
            if it.slug in KEY_RAMP:
                im["options"][o.key]["A"]["colour_share"] = round(colour_share(rendered[it.slug][o.key]["A"],
                                                                               KEY_RAMP[it.slug]), 2)
        allm["items"][it.slug] = im
        strip = [freedoom(it.placeholder)] + [rendered[it.slug][o.key]["A"] for o in it.options]
        if it.slug in KEY_RAMP:
            strip.append(sdkb())
        s1 = scene(strip, "map01")
        Image.fromarray(s1, "RGB").save(sheet_dir / f"{it.slug}.png", optimize=True)
        order = "Freedoom " + it.placeholder + ", A, B, C" + (", and SDKB (installed) for the family"
                                                               if it.slug in KEY_RAMP else "")
        png_blocks += [label(f"{it.lump} {it.name.split('(')[0].strip()} - {order.replace(',', ' ')} - rec {it.recommended}"),
                       zoom(s1, 3)]
        cards.append(card_html(it, s1, order, im))
    # the recommended set, together, on both floors
    rec = [rendered[it.slug][it.recommended]["A"] for it in ITEMS]
    rec_k = rec[:10] + [sdkb()] + rec[10:]
    fd = [freedoom(it.placeholder) for it in ITEMS]
    fd_k = fd[:10] + [freedoom("BKEY")] + fd[10:]
    lineups = {}
    for where in FLOORS:
        lineups[where] = (scene(fd_k, where), scene(rec_k, where))
        Image.fromarray(lineups[where][1], "RGB").save(sheet_dir / f"lineup_{where}.png", optimize=True)
    for where in FLOORS:
        png_blocks += [label(f"recommended set 1x and 3x - {where}"), lineups[where][1], zoom(lineups[where][1], 3)]
    png_blocks += [label("freedoom today 3x - map01"), zoom(lineups["map01"][0], 3)]
    # animations
    gifs = []
    for it in ITEMS:
        if len(it.frames) < 2:
            continue
        seq = anim_frames(it)
        fr_imgs = {fr: zoom(scene([rendered[it.slug][it.recommended][fr]], "map01"), 4) for fr in it.frames}
        data = gif_bytes([fr_imgs[f] for f, _ in seq], [ms for _, ms in seq])
        (sheet_dir / f"{it.slug}.gif").write_bytes(data)
        h, w = next(iter(fr_imgs.values())).shape[:2]
        spawn = "; ".join(f"{f} {t}{' bright' if b else ''}" for f, t, b in SPAWN[it.doom])
        gifs.append(f'<div class="v"><b>{it.lump} {it.recommended}: {html.escape(spawn)}</b>'
                    f'{img_tag(data, "image/gif", w, h, it.lump)}</div>')
        png_blocks += [label(f"{it.lump} frames {' '.join(it.frames)} 4x"),
                       np.concatenate([np.pad(fr_imgs[fr], ((0, 0), (0, 8), (0, 0)), constant_values=0)
                                       for fr in it.frames], 1)]
    # HUD key icons
    hud_dir = out_dir / "hud"
    icons_html = []
    icon_imgs = []
    for lump in KEY_ICON_COLOURS:
        rgb = key_icon(lump)
        save_indexed_v2(rgb, hud_dir / f"{lump}.png")
        fdk = gw.freedoom_sprite(lump)
        fd_rgb = None if fdk is None else fdk.rgba[..., :3]
        icon_imgs.append(zoom(rgb, 8))
        icons_html.append(view(f"{lump} ours, 1x", rgb, 1) + view(f"{lump} ours, 8x", rgb, 8)
                          + (view(f"{lump} Freedoom, 8x", fd_rgb, 8) if fd_rgb is not None else ""))
    png_blocks += [label("hud key icons stkeys0-2 8x"),
                   np.concatenate([np.pad(i, ((0, 0), (0, 16), (0, 0)), constant_values=0) for i in icon_imgs], 1)]
    (out_dir / "metrics.json").write_text(json.dumps(allm, indent=1, ensure_ascii=False), encoding="utf-8")

    sheet_png = preview_dir / f"{stamp}_{SHEET_SLUG}.png"
    sheet_png.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(stack(png_blocks), "RGB").save(sheet_png, optimize=True)
    preview = preview_dir / f"{stamp}_{SHEET_SLUG}.html"
    write_preview(preview, cards, lineups, gifs, icons_html, sheet_png)
    return preview, allm


def card_html(it: Item, s1: np.ndarray, order: str, im: dict) -> str:
    rows = []
    for o in it.options:
        for fr, m in im["options"][o.key].items():
            rows.append([f"{o.key} {lump_name(it, fr)}", f"{m['size'][0]}x{m['size'][1]}",
                         f"{m['offsets'][0]}, {m['offsets'][1]}", m["luma"], m["contrast_map01"],
                         m["contrast_map03"]] + ([m.get("colour_share", "")] if it.slug in KEY_RAMP else []))
    head = ["option, lump", "size", "grAb", "luma", "vs MAP01 floor", "vs MAP03 floor"]
    if it.slug in KEY_RAMP:
        head.append("key colour share")
    opts = "".join(f"<li><b>{o.key}</b> {html.escape(o.title)}" + (" <i>(palette v2)</i>" if o.palette == 2 else "")
                   + f" &mdash; &laquo;{html.escape(o.msg_en)}&raquo; / &laquo;{html.escape(o.msg_ru)}&raquo;</li>"
                   for o in it.options)
    spawn = "; ".join(f"{f} {t}{' bright' if b else ''}" for f, t, b in SPAWN[it.doom])
    ph = PLACEHOLDER_SIZE[it.placeholder]
    return (
        f'<div class="card rec"><span class="tag">recommended: {it.recommended}</span>'
        f"<h3>{it.lump} &mdash; {html.escape(it.name)}</h3>"
        f'<ul class="desc">{opts}</ul>'
        f'<p class="desc"><b>Recommendation {it.recommended}:</b> {html.escape(it.why)}.</p>'
        f'<div class="row">{view("3x: " + order, s1, 3)}</div>'
        f'<div class="row">{view("1x", s1, 1)}</div>'
        + sheetlib.table(head, rows)
        + f"<dl><dt>replaces</dt><dd><code>{it.doom}</code> (Freedoom <code>{it.placeholder}</code>, {ph[0]}x{ph[1]})"
        f"</dd><dt>install</dt><dd><code>{html.escape(it.actor)}</code>, Spawn <code>{spawn}</code> on "
        f"<code>{it.lump}</code>; line <code>{it.msg_id}</code></dd></dl></div>")


INTRO = (
    "Backlog <b>M2a</b>, audit items <b>B5</b> (113 Freedoom pickups placed in the campaign on skill 3: health, "
    "armour, the area map, the backpack, the yellow and red keycards) and <b>B3</b> (the hand Katyusha's floor "
    "pickup, still <code>BFUG</code>). Three options per object, drawn exactly as the approved pickups (D48, D63): "
    "small 3D scenes on <code>gen_weapon</code>'s rig, the same pitch, key light, bands and outline. Each card: "
    "Freedoom's sprite, then A, B, C, standing by their own offsets on MAP01's floor at light 144, at 3x and at 1x "
    "(1x is the verdict). The recommended option of every object is rendered complete, every animation frame, so "
    "the install needs no second render. Built by <code>tools/art/gen_items.py</code>. Draft: nothing in "
    "<code>assets/</code>.")


def write_preview(path: Path, cards, lineups, gifs, icons_html, sheet_png: Path) -> None:
    lu = ""
    for where, (fd_img, rec_img) in lineups.items():
        lu += (f"<h3>{html.escape(FLOORS[where][3])}</h3>"
               f'<div class="row">{view("Freedoom today, 1x", fd_img, 1)}{view("Recommended, 1x", rec_img, 1)}</div>'
               f'<div class="row">{view("Recommended, 3x", rec_img, 3)}</div>')
    lu += '<div class="row">' + view("Freedoom today on MAP01, 3x", lineups["map01"][0], 3) + "</div>"
    msgs = sheetlib.table(
        ["id", "class", "English [enu default]", "Russian [ru]"],
        [[it.msg_id, it.actor, it.option(it.recommended).msg_en, it.option(it.recommended).msg_ru] for it in ITEMS]
        + [["PD_YELLOWC / PD_YELLOWCO", "lock 3",
            "You need a yellow pass to open this door / ... to activate this object",
            "Для открытия нужен жёлтый пропуск / Для применения нужен жёлтый пропуск"],
           ["PD_REDC / PD_REDCO", "lock 1",
            "You need a red pass to open this door / ... to activate this object",
            "Для открытия нужен красный пропуск / Для применения нужен красный пропуск"]], numeric_from=99)
    install = (
        '<div class="ask"><b>What the install needs (mod-engineer, after the CEO; the PM\'s engine pass first)</b><ol>'
        "<li>Reserve the names in MOD-SPEC 6.3: <code>SDBN SDMD SDHB SDAB SDAG SDAH SDMP SDBP SDKY SDKK</code> "
        "(<code>SDHP</code> is already the Katyusha's). Copy the chosen option's PNGs from "
        "<code>work/art/items/&lt;item&gt;/&lt;option&gt;/</code> to <code>assets/sprites/pickups/</code>.</li>"
        "<li>One thin class per object, <code>SD_X : X replaces X</code>, as <code>ammo.zs</code> does, each with a "
        "<code>Spawn</code> state that is Doom's line for line under our name (shown on every card) and "
        "<code>Inventory.PickupMessage \"$SD_GOT_*\"</code> (Freedoom's DEHACKED beats LANGUAGE for the engine's "
        "own ids, ADR 003). <code>SD_Backpack</code> exists: only its <code>Spawn</code> changes. "
        "<code>SD_HandKatyusha</code> exists: its <code>Spawn</code> becomes <code>SDHP A -1</code>.</li>"
        "<li>The two keys copy <code>SD_BluePass</code>: <code>SD_YellowPass : YellowCard replaces YellowCard</code> "
        "with <code>Species \"YellowCard\"</code>, <code>SD_RedPass : RedCard replaces RedCard</code> with "
        "<code>Species \"RedCard\"</code> (locks 3 and 1 match by exact class or Species, never by parentage, "
        "keys.zs).</li>"
        "<li>HUD (H2): the armours' <code>Inventory.Icon</code> to <code>SDAGA0</code> / <code>SDAHA0</code>; the "
        "fullscreen HUD's health icon is the literal <code>MEDIA0</code> (doom_sbar.zs), so either "
        "<code>SD_StatusBar</code> overrides <code>DrawFullScreenStuff</code> or a copy of our medikit ships as "
        "<code>MEDIA0</code> (the cheaper; NOT VERIFIED). Keys: ship the three icons below as "
        "<code>graphics/STKEYS0-2.png</code> (indexed, palette v2: <code>STKEYS0</code> joins "
        "<code>PALETTE_V2_LUMPS</code>), which the status bar and the fullscreen HUD both draw. NOT VERIFIED in "
        "the engine.</li>"
        "<li>Palette v2: <code>SDAH</code> (option A) into <code>APPROVED_IN_V2</code> in "
        "<code>tests/test_palette_v2.py</code>, as <code>SDKB</code>. Everything else is v1.</li>"
        "<li>LANGUAGE: the lines above in <code>[enu default]</code> and <code>[ru]</code> in the same task (D21); "
        "the backpack's English line is a proposal to say kitbag, not satchel, as the Russian says вещмешок.</li>"
        "<li>The ammunition HUD icons (<code>CLIPA0</code>&hellip;) are H2 too and need only "
        "<code>Inventory.Icon</code> lines on the eight ammo classes: no art.</li></ol></div>")
    ask = (
        '<div class="ask"><b>For the CEO</b><ol>'
        "<li>Choose A, B or C per object (the recommendation is on each card), or ask for a redo of one.</li>"
        "<li>The heavy armour in palette v2's cobalt, as the blue pass: yes or no (B shows v1's best blue).</li>"
        "<li>The red cross on the medical items. The art bible says nothing about it (checked); the emblem is "
        "protected by the Geneva Conventions and the ICRC has asked game makers not to use it on health pickups. "
        "Period-true for 1977 and common in mods; a swap (a white cross on red, or a red crescent) is one constant "
        "in the generator and a re-render. Keep the red cross, or swap.</li>"
        "<li>The Katyusha's pickup at its drafted size (A, 70x37 against Freedoom's 56x24) or at the footprint "
        "(B).</li></ol></div>")
    sections = [
        ("The set together", "The recommended option of every object, in card order (stimpack, medikit, the two "
         "bonuses, the two armours, the map, the backpack, the yellow and red passes, then SDKB, the installed blue "
         "pass, for the family, and the Katyusha), against Freedoom's sprites, on a MAP01 floor and on a MAP03 "
         "floor. Sector light is gen_weapon's stand-in, NOT VERIFIED against GZDoom; MAP03 lights its keys yellow "
         "and red (lightcolor), which is not simulated.", lu),
        ("Animations", "The recommended option of every object Doom animates, in Doom's own frame order and tics, "
         "4x on MAP01's floor.", '<div class="row">' + "".join(gifs) + "</div>"),
        ("The objects", "", '<div class="grid">' + "".join(cards) + "</div>"),
        ("Key icons (status bar and fullscreen HUD)", "Freedoom's STKEYS0-2 are 7x5; ours are the pass's card "
         "at that size: the ground colour, the cream window with the photograph, the stamp.",
         '<div class="row">' + "".join(icons_html) + "</div>"),
        ("Pickup lines (draft, not in LANGUAGE)", "For the recommended options; the other options' lines are on "
         "their cards. Style of the lines already shipped (<code>SD_GOT_CLIP</code> &laquo;A magazine. "
         "7.62x25.&raquo;, <code>SD_PICKUP_BLUEPASS</code> &laquo;Blue pass.&raquo;). The lock lines are the "
         "engine's ids, overridden as <code>PD_BLUEC</code>/<code>PD_BLUECO</code> already are.", msgs),
        ("Install", "", install),
        ("Decisions", "", ask),
    ]
    footer = (f"Origin: (a) procedural, <code>tools/art/gen_items.py</code> on <code>gen_weapon</code>'s rig and "
              f"<code>gen_pickups</code>' primitives, deterministic, no seed, no font (the PNG sheet "
              f"<code>{html.escape(sheet_png.name)}</code> labels with a 3x5 pixel font of its own). Freedoom sprites "
              f"are read from <code>iwads/freedoom2.wad</code> 0.13.0 (BSD-3) for comparison only. Spawn states read "
              f"from <code>gzdoom.pk3</code> g4.14.2.")
    sheetlib.write_sheet(path, lang="en", title="Campaign pickups: health, armour, map, backpack, passes, Katyusha (M2a)",
                         subtitle="Sweep, three options per object, and the recommended set complete",
                         intro=INTRO, sections=sections, footer=footer)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"))
    ap.add_argument("--install", action="store_true",
                    help="render only the CEO's chosen sets (D80) and the key icons into work/art/items/")
    args = ap.parse_args(argv)
    if args.install:
        for p in install():
            print(f"wrote {p.relative_to(PROJECT_ROOT)}")
        return
    preview, m = build(args.stamp)
    print(f"wrote {preview}")
    for slug, im in m["items"].items():
        sizes = ", ".join(f"{k} {v['A']['size'][0]}x{v['A']['size'][1]}" for k, v in im["options"].items())
        print(f"  {im['lump']:5s} {slug:9s} {sizes}  (Freedoom {PLACEHOLDER_SIZE[im['placeholder'][:4]]})")


if __name__ == "__main__":
    main()
