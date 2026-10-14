"""T8 and T23 — the floor pickups that still wear Freedoom: ammunition, the
blue pass of MAP03 and the radio.

Run with the project venv:
    .venv/Scripts/python.exe tools/art/gen_pickups.py              (Windows)
    .venv/bin/python tools/art/gen_pickups.py                      (macOS)
    ... --stamp 2026-10-14_1930      fixes the preview's timestamp

What this is. Every pickup the player walks over in MAP01 is ours since D48
except these: the eight ammunition pickups of zscript/sd/ammo.zs (MOD-SPEC
§6.4, debt T8: "the ammunition has no three-dimensional look"), the blue
key card MAP03 uses as the station duty officer's pass (MAP03-metro.md §5,
"a keycard in 1977 is a paper pass with a photo and a stamp") and the
diegetic radio's `SDRD` A (MOD-SPEC §6.7, debt T23). This is a SWEEP
(PIPELINE stage 2): two options per object, side by side with the
Freedoom placeholder, for the CEO to choose.

    SD_Clip        SDCL A0   7,62x25: A a PPSh-41 box magazine, B a torn paper packet of rounds
    SD_ClipBox     SDCB A0   A a green wooden ammunition crate, B an opened zinc (цинк) of rounds
    SD_Shell       SDSL A0   12 gauge: A four shells lying, B four shells standing
    SD_ShellBox    SDSB A0   A a closed cardboard box, B the box open, twenty shells in it
    SD_RocketAmmo  SDRA A0   PG-7V: A one round standing on its tail, B one round lying
    SD_RocketBox   SDRB A0   A an open crate with two rounds, B three rounds stacked loose
    SD_Cell        SDFU A0   fuel: A a 10-litre jerrycan, B a spare ROKS-3 tank
    SD_CellPack    SDFB A0   A two jerrycans, B two ROKS-3 tanks in their back frame
    BlueCard       SDKB A0/B0  the pass: A a closed пропуск booklet, B a laminated card;
                             frame B is the blink (Doom's key cards alternate A and B)
    SD_Radio       SDRD A0   on a tabouret: A a VEF-206, B an Okean-209

The names but SDRD are PROPOSALS: MOD-SPEC §6.3 reserves only SDRD; the
mod-engineer reserves the others (or renames them) when the CEO chooses.
Each was checked free of every SD name the spec reserves and of the IWAD
(no Freedoom lump starts with SD). tests/test_gen_pickups.py holds both.

How it is drawn. Exactly as the approved weapon pickups (D48): small 3D
scenes on gen_weapon's Rig, seen from PICKUP_PITCH above the floor, lit by
the same fixed key light in flat bands, reduced to 1x by majority vote and
outlined by the contour, crease and rim passes. Everything here is rigid
(boxes, tins, cylinders, cards), which is what the procedural rig does well.
Boxes are turned BOX_YAW about the vertical so the top and two sides show:
that is the three-dimensional look T8 asks for. Markings are decals,
polygons lifted DECAL_LIFT off a face; there is no text anywhere, only
stencil blocks and bands (NO FONTS: the sprites reproduce byte for byte on
the Mac and on Windows).

Scale. Each pickup is drawn at roughly the footprint of the Freedoom
sprite it replaces (sizes measured on freedoom2.wad 0.13.0, in the comment
of each *_PX_PER_CM), with the small parts exaggerated as the weapon
pickups were (a 7,62 round is 3.5 cm; at Doom's scale it would be one
pixel). The radio is drawn standing on a tabouret: its body is +SOLID,
radius 16 and 28 high (MOD-SPEC §6.7), a waist-high obstacle, and a bare
transistor set 32 units wide would be a metre across.

Colour. Palette v1 for every object but the pass, which is mosaic_cobalt,
palette v2 (D45): Doom's blue key must read BLUE at 1x, and v1's only blue,
steel_blue, is a grey (ART-BIBLE §3). The precedent is the Legion's SDLT
set, approved in v2 (D54); on approval SDKB goes into APPROVED_IN_V2 in
tests/test_palette_v2.py. Sprites are RGBA with hard alpha, like every
shipped sprite (ART-BIBLE §2 exception).

The materials. gen_weapon's renderer keeps its material table in module
globals (MATERIALS, MAT_ID, METALS, FLAT). This tool adds three materials
of its own for the length of a render (`pickup_materials`) and restores the
tables afterwards, so gen_weapon's ids, and so its renders, never move.
gen_weapon.py itself is not edited.

Outputs (work/ is gitignored):
    work/art/pickups/<object>/<option>/<LUMP>.png   every option, named as it would ship
    work/art/pickups/sheet/*.png                    the 1x scenes the preview shows
    work/art/pickups/metrics.json                   size, offsets, luma, contrast on the floor
    docs/art/previews/<stamp>_F4_pickups-sweep.html the CEO's sheet
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import html
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

ART_TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(ART_TOOLS))

import artlib  # noqa: E402
import gen_weapon as gw  # noqa: E402
import palette as palette_mod  # noqa: E402
import sheetlib  # noqa: E402
from gen_enemy import Material, luma  # noqa: E402
from gen_weapon import Frame, Rig, floor_basis, perp, unit  # noqa: E402

PROJECT_ROOT = artlib.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / "work" / "art" / "pickups"
PREVIEW_DIR = PROJECT_ROOT / "docs" / "art" / "previews"
SHEET_SLUG = "F4_pickups-sweep"

# ------------------------------------------------------------------ camera
CANVAS = (112, 80)              # px: authoring canvas, cropped to the content afterwards
SS = 4                          # sub-pixels per pixel side (as the weapon pickups)
BOX_YAW = 28.0                  # degrees: a box turned so its top and two sides show
DECAL_LIFT = 0.04               # cm: a marking floats this far off its face
DISC_N = 24                     # vertices of a disc (a can's lid, a shell's head)
OPEN_PITCH = 40.0               # degrees: an open box is seen from higher up than the weapons' 25


# =============================================================== materials
class PaletteV2Material(Material):
    """A material on one of the palette's v2 ramps (D45): gen_enemy's
    Material reads the v1 ramps only."""

    def colours(self) -> list[tuple[int, int, int]]:
        cols = palette_mod.ramp_colours(self.ramp)[self.lo:self.hi + 1]
        return ([(0, 0, 0)] + cols) if self.black_floor else cols


EXTRA_MATERIALS: dict[str, Material] = {
    "kraft": Material("rust_brown", 4, 14, black_floor=True),           # brown cardboard and packet paper
    "cobalt": PaletteV2Material("mosaic_cobalt", 1, 15, black_floor=True),   # the pass (v2)
    "dial": Material("cream_yellow", 8, 15),                            # a radio's lit dial
}
EXTRA_METALS: frozenset[str] = frozenset()
V2_MATERIALS = frozenset({"cobalt"})


@contextlib.contextmanager
def pickup_materials():
    """gen_weapon's material tables with EXTRA_MATERIALS appended (so every
    gen_weapon id keeps its number), restored on the way out."""
    saved = (gw.MATERIALS, gw.MAT_ID, gw.METALS, gw.FLAT)
    mats = dict(gw.MATERIALS)
    mats.update(EXTRA_MATERIALS)
    gw.MATERIALS = mats
    gw.MAT_ID = {name: i for i, name in enumerate(mats)}
    gw.METALS = set(saved[2]) | set(EXTRA_METALS)
    try:
        yield
    finally:
        gw.MATERIALS, gw.MAT_ID, gw.METALS, gw.FLAT = saved


def rig_for(px_per_cm: float) -> Rig:
    w, h = CANVAS
    return Rig(0, 0, w, h, ss=SS, focal=px_per_cm * gw.PICKUP_DIST, centre=(w / 2, h / 2))


def centre() -> np.ndarray:
    return np.array([0.0, 0.0, gw.PICKUP_DIST])


def yawed(yaw_deg: float, pitch: float = gw.PICKUP_PITCH):
    """Floor axes turned yaw_deg about the vertical: X (the object's width),
    Y (its depth, away from the eye) and Z (up). A positive yaw shows the
    left face and the front face; the key light comes from the left. An
    open container is seen from OPEN_PITCH, so what is in it shows."""
    right, away, up = floor_basis(pitch)
    a = np.deg2rad(yaw_deg)
    X = unit(right * np.cos(a) + away * np.sin(a))
    Y = unit(-right * np.sin(a) + away * np.cos(a))
    return X, Y, up


# ============================================================ primitives
def rect(w: float, h: float, t0: float = 0.0):
    return ((-w / 2, t0), (w / 2, t0), (w / 2, t0 + h), (-w / 2, t0 + h))


@dataclass
class Box:
    """A rectangular solid standing on the floor: c is the centre of its
    bottom face, X Y Z its axes, w d h its size in cm."""
    c: np.ndarray
    X: np.ndarray
    Y: np.ndarray
    Z: np.ndarray
    w: float
    d: float
    h: float

    def draw(self, rig: Rig, material: str, base: float, gain: float = 0.8) -> None:
        rig.plate(self.c + self.Z * self.h / 2, self.X, self.Z, rect(self.w, self.h, -self.h / 2),
                  self.d, material, base, gain)

    def pt(self, face: str, s: float, t: float, lift: float = DECAL_LIFT) -> np.ndarray:
        """A point on a face: s across it, t up it (on the top face, t runs
        along the depth, -d/2 at the front)."""
        c, X, Y, Z = self.c, self.X, self.Y, self.Z
        if face == "front":
            return c - Y * (self.d / 2 + lift) + X * s + Z * t
        if face == "back":
            return c + Y * (self.d / 2 + lift) + X * s + Z * t
        if face == "left":
            return c - X * (self.w / 2 + lift) + Y * s + Z * t
        if face == "right":
            return c + X * (self.w / 2 + lift) + Y * s + Z * t
        if face == "top":
            return c + Z * (self.h + lift) + X * s + Y * t
        raise ValueError(face)

    def decal(self, rig: Rig, face: str, s0: float, t0: float, s1: float, t1: float, material: str,
              base: float, gain: float = 0.8, lift: float = DECAL_LIFT) -> None:
        pts = [self.pt(face, s0, t0, lift), self.pt(face, s1, t0, lift), self.pt(face, s1, t1, lift),
               self.pt(face, s0, t1, lift)]
        rig._plane(pts, material, base, gain)

    def decal_poly(self, rig: Rig, face: str, poly, material: str, base: float, gain: float = 0.8,
                   lift: float = DECAL_LIFT) -> None:
        rig._plane([self.pt(face, s, t, lift) for s, t in poly], material, base, gain)


def open_box(rig: Rig, b: Box, wall: float, material: str, base: float, inner: float) -> Box:
    """A box with no lid: floor and four walls of thickness `wall`. Returns
    the inside as a Box (its c on the inner floor), to put things in."""
    X, Y, Z = b.X, b.Y, b.Z
    Box(b.c, X, Y, Z, b.w, b.d, wall).draw(rig, material, inner)
    for sx in (-1, 1):
        Box(b.c + X * sx * (b.w - wall) / 2, X, Y, Z, wall, b.d, b.h).draw(rig, material, base)
    for sy in (-1, 1):
        Box(b.c + Y * sy * (b.d - wall) / 2, X, Y, Z, b.w - 2 * wall, wall, b.h).draw(rig, material, base)
    return Box(b.c + Z * wall, X, Y, Z, b.w - 2 * wall, b.d - 2 * wall, b.h - wall)


def disc(rig: Rig, at, axis, r: float, material: str, base: float, gain: float = 0.8, n: int = DISC_N) -> None:
    """A flat disc across `axis` (a lid, a shell's head, a knob)."""
    a = unit(axis)
    u = perp(np.array([0.3, 0.7, 0.2]), a)
    v = np.cross(a, u)
    at = np.asarray(at, np.float64)
    rig._plane([at + r * (np.cos(2 * np.pi * k / n) * u + np.sin(2 * np.pi * k / n) * v) for k in range(n)],
               material, base, gain)


def cylinder(rig: Rig, p0, p1, r: float, material: str, base: float, gain: float = 0.8,
             caps: tuple[float | None, float | None] = (None, None), cap_material: str | None = None) -> None:
    """A straight tube with flat ends: caps=(value at p0, value at p1), None
    for an end the eye cannot see."""
    p0, p1 = np.asarray(p0, np.float64), np.asarray(p1, np.float64)
    rig.capsule(p0, p1, r, r, material, base, gain, open_ends=True)
    axis = p1 - p0
    for end, val, sign in ((p0, caps[0], -1.0), (p1, caps[1], 1.0)):
        if val is not None:
            disc(rig, end + unit(axis) * sign * 0.01, axis, r, cap_material or material, val, gain)


# ============================================================ 7,62 x 25
CLIP_PX_PER_CM = 0.62           # CLIPA0 is 7x12; a 25 cm magazine -> ~13 px
CLIPBOX_PX_PER_CM = 0.50        # AMMOA0 is 17x16
ROUND_LEN, ROUND_R = 3.5, 0.55  # the 7,62x25 cartridge, cm
BULLET_LEN = 1.3

# The PPSh-41's 35-round box magazine (1942), in profile: (s forwards, t up),
# cm, from the floor plate up to the feed lips, curving forwards. Thickness
# exaggerated MAG_FAT times, as the pickups exaggerate small parts.
PPSH_MAG_PROFILE = ((-2.4, 0.0), (2.6, 0.0), (3.6, 7.0), (4.4, 14.0), (4.6, 21.0), (1.0, 22.5),
                    (0.4, 15.0), (-0.6, 7.5))
MAG_FAT = 2.1
MAG_THICK = 2.4


def draw_round(rig: Rig, base, axis, k: float = 1.0) -> None:
    """One 7,62x25 cartridge: a brass case and its bullet, from the case head."""
    a = unit(axis)
    b = np.asarray(base, np.float64)
    tip = b + a * ROUND_LEN * k
    neck = tip - a * BULLET_LEN * k
    rig.capsule(b, neck, ROUND_R * k, ROUND_R * k * 0.9, "brass", 0.62, 0.8, open_ends=True)
    rig.capsule(neck, tip, ROUND_R * k * 0.78, ROUND_R * k * 0.3, "wood_birch", 0.66, 0.8)   # copper-washed steel


def render_clip_a() -> Frame:
    """A: the PPSh-41 box magazine standing on its floor plate, the top
    round showing brass at the lips."""
    rig = rig_for(CLIP_PX_PER_CM)
    X, Y, Z = yawed(64.0)
    base = centre() - Z * 11.0
    poly = [(s * MAG_FAT, t) for s, t in PPSH_MAG_PROFILE]
    rig.plate(base, Y * -1.0, Z, poly, MAG_THICK * MAG_FAT, "gunmetal", 0.50, 0.85)
    # the floor plate, a lip of steel all round the foot
    rig.plate(base - Z * 0.2, Y * -1.0, Z, ((-3.0 * MAG_FAT, 0.0), (3.2 * MAG_FAT, 0.0),
                                             (3.2 * MAG_FAT, 1.2), (-3.0 * MAG_FAT, 1.2)),
              MAG_THICK * MAG_FAT + 0.8, "steel", 0.45, 0.85)
    top = base + Z * 22.0 - Y * (2.6 * MAG_FAT)
    draw_round(rig, top + Y * 1.4, -Y + Z * 0.15, k=1.9)
    return gw.finish(rig, hud=False)


PACKET = (7.6, 3.4, 8.0)        # w, d, h of the paper packet, cm
CLIP_B_PX_PER_CM = 1.05


def render_clip_b() -> Frame:
    """B: a brown paper packet of rounds, its top torn off, one row of
    bullets standing proud, a black stencil band round it and one loose
    round in front."""
    rig = rig_for(CLIP_B_PX_PER_CM)
    X, Y, Z = yawed(BOX_YAW)
    w, d, h = PACKET
    b = Box(centre() - Z * 4.0, X, Y, Z, w, d, h)
    b.draw(rig, "kraft", 0.40)
    for f, span in (("front", w), ("left", d)):
        b.decal(rig, f, -span / 2, h * 0.30, span / 2, h * 0.52, "rubber", 0.20)     # the stencil band
    for s in np.linspace(-w / 2 + 1.1, w / 2 - 1.1, 4):
        draw_round(rig, b.pt("top", s, 0.0, 0.0) - Z * 1.6, Z, k=1.25)
    draw_round(rig, b.c - Y * (d / 2 + 2.6) - X * 1.6 + Z * ROUND_R * 1.3, X + Y * 0.2, k=1.3)
    return gw.finish(rig, hud=False)


CRATE_762 = (34.0, 22.0, 20.0)  # w, d, h of the small ammunition crate, cm


def crate_planks(rig: Rig, b: Box, faces=("front", "left"), n: int = 3, groove_px: float = 1.0,
                 px_per_cm: float = 0.5) -> None:
    """Dark grooves between the planks of a wooden face."""
    g = groove_px / px_per_cm / 2
    for f in faces:
        span = b.w if f in ("front", "back") else b.d
        for i in range(1, n):
            t = b.h * i / n
            b.decal(rig, f, -span / 2, t - g / 2, span / 2, t + g / 2, "olive_paint", 0.22)


def rope_handle(rig: Rig, b: Box, face: str, t: float, half: float, r: float = 0.9) -> None:
    """A rope handle in two cleats on a side face."""
    p0 = b.pt(face, -half, t, r)
    p1 = b.pt(face, half, t, r)
    mid = (p0 + p1) / 2 + b.Z * -1.6 - (b.X if face == "left" else -b.X if face == "right" else b.Y) * 1.2
    rig.capsule(p0, mid, r, r, "rubber", 0.40, 0.7)
    rig.capsule(mid, p1, r, r, "rubber", 0.40, 0.7)


def render_clipbox_a() -> Frame:
    """A: the green wooden crate a zinc travels in: planks, a black
    stencil block, rope handles on the ends."""
    px = CLIPBOX_PX_PER_CM
    rig = rig_for(px)
    X, Y, Z = yawed(BOX_YAW)
    w, d, h = CRATE_762
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    b.draw(rig, "olive_paint", 0.56)
    # the lid's battens, proud of the top
    for s in (-w / 2 + 2.5, w / 2 - 2.5):
        Box(b.pt("top", s, 0.0, 0.0), X, Y, Z, 3.0, d, 1.2).draw(rig, "olive_paint", 0.62)
    crate_planks(rig, b, px_per_cm=px)
    b.decal(rig, "front", -8.0, 8.6, 8.0, 11.4, "rubber", 0.24)            # the stencil, between grooves
    b.decal(rig, "front", w / 2 - 6.0, 2.6, w / 2 - 2.0, 6.6, "tel_white", 0.55)   # the lot's white square
    rope_handle(rig, b, "left", 13.5, 4.5)
    return gw.finish(rig, hud=False)


ZINC = (30.0, 16.0, 14.0)


def render_clipbox_b() -> Frame:
    """B: the zinc (цинк), its lid cut open and peeled back, rows of rounds
    standing bullet up: the brass is what reads at 1x."""
    px = CLIPBOX_PX_PER_CM
    rig = rig_for(px)
    X, Y, Z = yawed(BOX_YAW, OPEN_PITCH)
    w, d, h = ZINC
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    inside = open_box(rig, b, 0.6, "button", 0.34, 0.14)
    # the peeled lid, folded back over the far edge
    lid0 = b.pt("top", 0.0, d / 2, 0.0)
    rig.plate(lid0 + Y * 2.0 + Z * 4.0, X, unit(Y * 0.4 + Z), rect(w, 9.0, -4.5), 0.4, "button", 0.56, 0.85)
    # the rounds, packed in rows, the bullets standing proud of the rim
    n_s, n_t = 7, 4
    k = 2.0
    for s in np.linspace(-inside.w / 2 + 1.6, inside.w / 2 - 1.6, n_s):
        for t in np.linspace(-inside.d / 2 + 1.6, inside.d / 2 - 1.6, n_t):
            p = inside.c + X * s + Y * t + Z * (inside.h - ROUND_LEN * k + 2.2)
            draw_round(rig, p, Z, k=k)
    b.decal(rig, "front", -w / 2 + 0.6, h * 0.45, w / 2 - 0.6, h * 0.62, "rubber", 0.20)   # the seam band
    return gw.finish(rig, hud=False)


# ================================================================ 12 gauge
SHELL_PX_PER_CM = 1.45          # SHELA0 is 14x10
SHELLBOX_PX_PER_CM = 1.10       # SBOXA0 is 34x13
SHELL_LEN, SHELL_R = 7.0, 1.08  # a 12-gauge paper shell, cm
SHELL_HEAD = 1.4                # the brass head


def draw_shell(rig: Rig, head, axis, crimp_visible: bool = True, head_visible: bool = True) -> None:
    """A 12-gauge shell from the face of its brass head along `axis`."""
    a = unit(axis)
    h = np.asarray(head, np.float64)
    neck = h + a * SHELL_HEAD
    end = h + a * SHELL_LEN
    cylinder(rig, h, neck, SHELL_R * 1.06, "brass", 0.62, 0.8, caps=(0.70 if head_visible else None, None))
    cylinder(rig, neck, end, SHELL_R, "hull_red", 0.58, 0.8, caps=(None, 0.42 if crimp_visible else None))
    if head_visible:
        disc(rig, h - a * 0.03, a, SHELL_R * 0.32, "brass", 0.35)              # the primer


def render_shell_a() -> Frame:
    """A: four shells lying in a loose row, heads to the left, as Doom
    lays its shells."""
    rig = rig_for(SHELL_PX_PER_CM)
    X, Y, Z = yawed(10.0)
    c = centre() - Z * 1.0
    for i, (dx, dy) in enumerate(((-0.4, 2.4), (0.6, 0.0), (-0.2, -2.4), (0.8, -4.8))):
        head = c + X * (-SHELL_LEN / 2 + dx) + Y * dy + Z * SHELL_R
        draw_shell(rig, head, X + Y * 0.08 * (i - 1.5))
    return gw.finish(rig, hud=False)


def render_shell_b() -> Frame:
    """B: four shells standing on their heads in a little arc, crimps up."""
    rig = rig_for(SHELL_PX_PER_CM)
    X, Y, Z = yawed(0.0)
    c = centre() - Z * SHELL_LEN / 2
    for dx, dy in ((-3.4, 1.4), (-1.1, -0.6), (1.2, 0.8), (3.5, -1.0)):
        draw_shell(rig, c + X * dx + Y * dy, Z, head_visible=False)
    return gw.finish(rig, hud=False)


SHELLBOX = (24.0, 8.4, 7.6)     # ten shells side by side, lying, cm
SHELLBOX_OPEN = (23.6, 5.2, 5.0)   # the tray of twenty standing: 2 rows of 10, heads above the rim


def render_shellbox_a() -> Frame:
    """A: the cardboard box shut: kraft, a cream label round its middle with
    a red band (the hunter's box of the 1970s, no words at 1x)."""
    rig = rig_for(SHELLBOX_PX_PER_CM)
    X, Y, Z = yawed(14.0)
    w, d, h = SHELLBOX
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    b.draw(rig, "kraft", 0.40)
    Box(b.c + Z * (h - 2.2), X, Y, Z, w + 0.5, d + 0.5, 2.4).draw(rig, "kraft", 0.46)   # the lid, over the box
    b.decal(rig, "front", -w * 0.24, 0.9, w * 0.24, h - 3.1, "tel_white", 0.60)      # the label
    b.decal(rig, "front", -w * 0.24, h * 0.28, w * 0.24, h * 0.42, "hull_red", 0.55, lift=DECAL_LIFT * 2)
    return gw.finish(rig, hud=False)


def render_shellbox_b() -> Frame:
    """B: the box open, its lid tucked under: twenty shells standing in two
    rows, their brass heads up and proud of the tray, the red hulls
    showing over the rim."""
    rig = rig_for(SHELLBOX_PX_PER_CM)
    X, Y, Z = yawed(14.0, OPEN_PITCH)
    w, d, h = SHELLBOX_OPEN
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    inside = open_box(rig, b, 0.35, "kraft", 0.40, 0.20)
    for f, span in (("front", w), ("left", d)):
        b.decal(rig, f, -span * 0.22, 0.6, span * 0.22, h - 0.6, "tel_white", 0.60)
        b.decal(rig, f, -span * 0.22, h * 0.36, span * 0.22, h * 0.62, "hull_red", 0.55, lift=DECAL_LIFT * 2)
    # twenty shells packed upright, brass heads up, standing proud of the tray
    for s in np.linspace(-inside.w / 2 + SHELL_R, inside.w / 2 - SHELL_R, 10):
        for t in (-inside.d / 4, inside.d / 4):
            crimp = inside.c + X * s + Y * t
            draw_shell(rig, crimp + Z * SHELL_LEN, -Z, crimp_visible=False)
    return gw.finish(rig, hud=False)


# ================================================================== PG-7V
ROCKET_PX_PER_CM = 0.56         # ROCKA0 is 10x24
ROCKETBOX_PX_PER_CM = 0.46      # BROKA0 is 52x20
# The PG-7V round, u from the end of the tail along the axis, cm (gen_weapon's
# PG7_* with the booster charge PG-7P screwed on behind). PG7_RAD exaggerates
# the radii: at Doom's scale an 8.5 cm warhead is four pixels across.
PG7_CHARGE = (0.0, 12.0, 2.2)
PG7_TAIL = (12.0, 24.0, 1.4)
PG7_BODY = (24.0, 31.0, 4.25)
PG7_CONE = (31.0, 48.0, 4.25, 0.9)
PG7_FUSE = (48.0, 51.0, 0.7)
PG7_FINS = (12.0, 15.5, 3.6)    # u from, u to, span: the folded fins at the tail's foot
PG7_RAD = 1.35
ROCKET_STAND_RAD = 1.75         # standing, the round is drawn fatter: ROCKA0 is 10 px wide


def draw_pg7v(rig: Rig, base, axis, k: float = 1.0, rad: float = PG7_RAD) -> None:
    U = unit(axis)
    b = np.asarray(base, np.float64)
    at = lambda u: b + U * u * k
    r = lambda x: x * k * rad
    c0, c1, cr = PG7_CHARGE
    cylinder(rig, at(c0), at(c1), r(cr), "olive_paint", 0.38, 0.8, caps=(0.30, None))      # the booster
    rig.capsule(at(c1 - 0.6), at(c1), r(cr) * 1.08, r(cr) * 1.08, "steel", 0.40, 0.8, open_ends=True)
    t0, t1, tr = PG7_TAIL
    rig.capsule(at(t0), at(t1), r(tr), r(tr), "steel", 0.45, 0.85, open_ends=True)
    f0, f1, fs = PG7_FINS
    side = perp(np.array([1.0, 0.0, 0.3]), U)
    rig.plate(at((f0 + f1) / 2), U, side, ((-(f1 - f0) * k / 2, -r(fs)), ((f1 - f0) * k / 2, -r(fs)),
                                         ((f1 - f0) * k / 2, r(fs)), (-(f1 - f0) * k / 2, r(fs))),
              0.5, "steel", 0.40, 0.85)
    b0, b1, br = PG7_BODY
    rig.capsule(at(b0), at(b1), r(br) * 0.9, r(br), "olive_paint", 0.55, 0.8, open_ends=True)
    o0, o1, orr, orr1 = PG7_CONE
    rig.capsule(at(o0), at(o1), r(orr), r(orr1), "olive_paint", 0.62, 0.8)
    u0, u1, ur = PG7_FUSE
    rig.capsule(at(u0), at(u1), r(ur), r(ur) * 0.6, "steel", 0.55, 0.8)
    rig.capsule(at(b0 + 0.4), at(b0 + 1.6), r(br) * 0.93, r(br) * 0.95, "rubber", 0.25, 0.7, open_ends=True)  # the band


def render_rocket_a() -> Frame:
    """A: one round standing on its booster, nose up, as Doom stands its
    rocket."""
    rig = rig_for(ROCKET_PX_PER_CM)
    X, Y, Z = yawed(0.0)
    draw_pg7v(rig, centre() - Z * 26.0, Z + X * 0.04, rad=ROCKET_STAND_RAD)
    return gw.finish(rig, hud=False)


def render_rocket_b() -> Frame:
    """B: the round lying on its side, nose to the right, turned a little."""
    rig = rig_for(ROCKET_PX_PER_CM)
    X, Y, Z = yawed(-14.0)
    draw_pg7v(rig, centre() - X * 26.0 + Z * 2.0, X)
    return gw.finish(rig, hud=False)


ROCKET_CRATE = (104.0, 34.0, 14.0)
ROCKET_CRADLE_H = 6.0


def render_rocketbox_a() -> Frame:
    """A: the long green crate open, two rounds in their cradles."""
    px = ROCKETBOX_PX_PER_CM
    rig = rig_for(px)
    X, Y, Z = yawed(12.0, OPEN_PITCH)
    w, d, h = ROCKET_CRATE
    b = Box(centre() - Z * h / 2, X, Y, Z, w, d, h)
    inside = open_box(rig, b, 1.6, "olive_paint", 0.50, 0.18)
    for s in (-w / 2 + 16.0, w / 2 - 16.0):                     # the cradles
        Box(inside.c + X * s, X, Y, Z, 3.0, inside.d, ROCKET_CRADLE_H).draw(rig, "olive_paint", 0.36)
    rad = 1.25
    for t in (-inside.d / 4, inside.d / 4):
        draw_pg7v(rig, inside.c - X * 49.0 + Y * t + Z * (ROCKET_CRADLE_H + PG7_BODY[2] * rad * 0.8), X,
                  k=1.0, rad=rad)
    b.decal(rig, "front", -12.0, 4.0, 12.0, 8.0, "rubber", 0.20)
    rope_handle(rig, b, "left", 9.0, 7.0)
    return gw.finish(rig, hud=False)


ROCKET_STACK_PX_PER_CM = 0.70  # three rounds are shorter than the crate: drawn larger to fill BROKA0's 52


def render_rocketbox_b() -> Frame:
    """B: three rounds stacked loose, two below and one on top, no crate."""
    rig = rig_for(ROCKET_STACK_PX_PER_CM)
    X, Y, Z = yawed(10.0)
    r = PG7_BODY[2] * PG7_RAD
    c = centre() - X * 25.0
    for dy, dz, dx in ((r * 1.05, r, 0.0), (-r * 1.05, r, 2.5), (0.0, r * 2.75, 1.0)):
        draw_pg7v(rig, c + X * dx + Y * dy + Z * dz - Z * 4.0, X)
    return gw.finish(rig, hud=False)


# ==================================================================== fuel
FUEL_PX_PER_CM = 0.55           # CELLA0 is 19x12
FUELPACK_PX_PER_CM = 0.55       # CELPA0 is 32x20
JERRY = (17.0, 30.0, 27.0)      # a 10-litre jerrycan: w (narrow side), d, h
JERRY_X = (0.32, 0.38)          # the pressed X on its broad side: arm half-width, inset (shares)


JERRY_VALUE = 0.60              # the red sits high on its ramp: at light 144 a lower red goes maroon


def draw_jerrycan(rig: Rig, c, X, Y, Z, material: str = "hull_red", base: float = JERRY_VALUE) -> Box:
    """A jerrycan standing, its broad side on the -X face (the caller turns
    it to the eye). Three handles on top, the spout on the front corner,
    the pressed X on the broad side."""
    w, d, h = JERRY
    b = Box(np.asarray(c, np.float64), X, Y, Z, w, d, h)
    b.draw(rig, material, base)
    # the pressed X on the broad (left) side: two diagonal ribs
    ax, ins = JERRY_X
    s0, s1 = -d / 2 + d * 0.12, d / 2 - d * 0.12
    t0, t1 = h * 0.12, h * 0.80
    for (sa, ta), (sb, tb) in (((s0, t0), (s1, t1)), ((s0, t1), (s1, t0))):
        n = np.array([tb - ta, -(sb - sa)])
        n = n / np.linalg.norm(n) * 1.2
        b.decal_poly(rig, "left", [(sa - n[0], ta - n[1]), (sb - n[0], tb - n[1]), (sb + n[0], tb + n[1]),
                                   (sa + n[0], ta + n[1])], material, base - 0.18, lift=0.3)
    # handles: three bars across the top, from the back
    for i, s in enumerate((-0.30, 0.0, 0.30)):
        p = b.pt("top", 0.0, s * d + d * 0.08, 0.0)
        rig.capsule(p - X * w * 0.30 + Z * 2.6, p + X * w * 0.30 + Z * 2.6, 0.9, 0.9, material, base + 0.06, 0.8)
        for sx in (-1, 1):
            rig.capsule(p + X * sx * w * 0.30, p + X * sx * w * 0.30 + Z * 2.6, 0.8, 0.8, material, base, 0.8)
    # the spout, front corner, its cap closed
    sp = b.pt("top", 0.0, -d / 2 + 3.2, 0.0)
    cylinder(rig, sp, sp + Z * 3.2 - Y * 1.2, 2.0, "steel", 0.50, 0.85, caps=(None, 0.62))
    return b


def render_fuel_a() -> Frame:
    """A: a 10-litre jerrycan in red, the broad side with its X to the eye."""
    rig = rig_for(FUEL_PX_PER_CM)
    X, Y, Z = yawed(62.0)
    draw_jerrycan(rig, centre() - Z * 14.0, X, Y, Z)
    return gw.finish(rig, hud=False)


TANK_LEN, TANK_R = 42.0, 9.0    # the ROKS-3's tank, as on the weapon pickup (SDKPA0)


def draw_tank(rig: Rig, c, axis, Z) -> None:
    """The ROKS-3 tank lying: olive cylinder with domed ends, its valve and
    a red band (the fuel)."""
    A = unit(axis)
    c = np.asarray(c, np.float64)
    rig.capsule(c - A * TANK_LEN / 2, c + A * TANK_LEN / 2, TANK_R, TANK_R, "olive_paint", 0.52, 0.8)
    rig.capsule(c - A * 4.0, c + A * 1.0, TANK_R * 1.03, TANK_R * 1.03, "hull_red", 0.55, 0.8, open_ends=True)
    v = c + A * (TANK_LEN / 2 + TANK_R * 0.6)
    rig.capsule(v, v + A * 3.0, 2.0, 1.6, "steel", 0.50, 0.85)
    rig.capsule(v + A * 2.0, v + A * 2.0 + Z * 3.0, 0.9, 0.9, "steel", 0.55, 0.85)


def render_fuel_b() -> Frame:
    """B: a spare ROKS-3 tank lying, the valve to the right: the same tank
    the weapon pickup carries, so the player connects the two."""
    rig = rig_for(FUEL_PX_PER_CM * 1.05)
    X, Y, Z = yawed(-10.0)
    draw_tank(rig, centre() - X * 2.0, X, Z)
    return gw.finish(rig, hud=False)


def render_fuelpack_a() -> Frame:
    """A: two jerrycans side by side, the second a step behind."""
    rig = rig_for(FUELPACK_PX_PER_CM)
    X, Y, Z = yawed(62.0)
    right, away, up = floor_basis()
    draw_jerrycan(rig, centre() - Z * 14.0 + right * 13.0 + away * 14.0, X, Y, Z)
    draw_jerrycan(rig, centre() - Z * 14.0 - right * 10.0, X, Y, Z)
    return gw.finish(rig, hud=False)


def render_fuelpack_b() -> Frame:
    """B: two ROKS-3 tanks standing in their back frame, the strap across."""
    rig = rig_for(FUELPACK_PX_PER_CM)
    X, Y, Z = yawed(18.0)
    c = centre() - Z * 22.0
    for sx in (-1, 1):
        p = c + X * sx * (TANK_R + 0.4)
        rig.capsule(p + Z * TANK_R, p + Z * (TANK_LEN - TANK_R + 6.0), TANK_R, TANK_R, "olive_paint", 0.52, 0.8)
        rig.capsule(p + Z * 20.0, p + Z * 25.0, TANK_R * 1.03, TANK_R * 1.03, "hull_red", 0.55, 0.8,
                    open_ends=True)
        rig.capsule(p + Z * (TANK_LEN + 3.5), p + Z * (TANK_LEN + 7.5), 1.8, 1.4, "steel", 0.50, 0.85)
    # the frame: two steel rails behind, a strap in front
    for t in (8.0, 36.0):
        Box(c + Z * t - Y * (TANK_R + 0.3), X, Y, Z, 4 * TANK_R + 2.0, 1.2, 2.4).draw(rig, "rubber", 0.40)
    for sx in (-1, 1):
        rig.capsule(c + X * sx * (2 * TANK_R + 1.0) + Y * 2.0, c + X * sx * (2 * TANK_R + 1.0) + Y * 2.0
                    + Z * (TANK_LEN + 2.0), 1.0, 1.0, "steel", 0.42, 0.85)
    return gw.finish(rig, hud=False)


# ================================================================ the pass
PASS_PX_PER_CM = 1.45           # BKEYA0 is 14x21
PASS_LEAN = 12.0                # degrees back from upright
BOOKLET = (9.5, 13.0, 1.0)      # w, h, thickness: the closed пропуск
CARD = (9.0, 12.5, 0.35)
GLINT_GAIN = 0.24               # frame B: the blink, value added all over
PASS_FRAMES = ("A", "B")
PASS_SLUG = "pass"


def pass_axes(yaw: float):
    """Card axes: X across, Z up its face leaning PASS_LEAN back, N its
    face normal (towards the eye)."""
    X, Y, Z = yawed(yaw)
    t = np.deg2rad(PASS_LEAN)
    Zc = unit(Z * np.cos(t) + Y * np.sin(t))
    return X, Zc, Y


def star_poly(cs, ct, r: float, inner: float = 0.42):
    pts = []
    for i in range(10):
        a = np.deg2rad(90.0 + i * 36.0)
        rr = r if i % 2 == 0 else r * inner
        pts.append((cs + rr * np.cos(a), ct + rr * np.sin(a)))
    return pts


def render_pass_a(frame: str = "A") -> Frame:
    """A: the closed пропуск, an ID booklet in cobalt cloth standing on its
    edge: a gold star and a gold title bar on the cover, the cream page
    edges on the side. Frame B lights it up (the blink)."""
    rig = rig_for(PASS_PX_PER_CM)
    X, Zc, Y = pass_axes(24.0)
    w, h, th = BOOKLET
    g = GLINT_GAIN if frame == "B" else 0.0
    base = centre() - Zc * h / 2
    rig.plate(base + Zc * h / 2, X, Zc, rect(w, h, -h / 2), th, "cobalt", 0.50 + g, 0.75)
    # the page block, cream, set in from the cover on the open (right) side
    rig.plate(base + Zc * h / 2 + X * 0.25, X, Zc, rect(w - 0.4, h - 0.5, -(h - 0.5) / 2), th * 0.75,
              "tel_white", 0.62 + g, 0.75)
    face = lambda s, t: base - Y * (th / 2 + DECAL_LIFT) + X * s + Zc * t
    rig._plane([face(s, t) for s, t in star_poly(0.0, h * 0.62, 2.3)], "brass", 0.72 + g, 0.6)
    rig._plane([face(s, t) for s, t in rect(5.6, 1.2, h * 0.28)], "brass", 0.66 + g, 0.6)
    if frame == "B":
        rig._plane([face(s, t) for s, t in ((-w / 2 + 0.6, h - 1.2), (-w / 2 + 2.2, h - 0.6),
                                            (-w / 2 + 0.6, h - 0.6))], "tel_white", 0.95, 0.4)
    return gw.finish(rig, hud=False)


def render_pass_b(frame: str = "A") -> Frame:
    """B: a laminated pass card in cobalt: a cream window with the holder's
    photograph, a red stamp over its corner, two white lines of entries.
    Frame B lights it up (the blink)."""
    rig = rig_for(PASS_PX_PER_CM)
    X, Zc, Y = pass_axes(-16.0)
    w, h, th = CARD
    g = GLINT_GAIN if frame == "B" else 0.0
    base = centre() - Zc * h / 2
    rig.plate(base + Zc * h / 2, X, Zc, rect(w, h, -h / 2), th, "cobalt", 0.56 + g, 0.75)
    face = lambda s, t, k=1: base - Y * (th / 2 + DECAL_LIFT * k) + X * s + Zc * t
    rig._plane([face(s, t) for s, t in rect(w - 1.6, 5.6, h - 7.0)], "tel_white", 0.66 + g, 0.6)  # window
    rig._plane([face(s, t, 2) for s, t in rect(3.4, 4.2, h - 6.3)], "dummy", 0.30 + g, 0.6)      # photo
    rig._plane([face(s, t, 3) for s, t in rect(1.4, 1.6, h - 5.0)], "dummy", 0.62 + g, 0.6)      # the face in it
    rig._plane([face(s + 2.0, t, 4) for s, t in star_poly(0.0, h - 6.6, 1.5, 0.75)], "hull_red", 0.55 + g, 0.6)
    for t in (2.2, 3.6):
        rig._plane([face(s, tt, 1) for s, tt in rect(w - 2.4, 0.55, t)], "tel_white", 0.62 + g, 0.6)
    if frame == "B":
        rig._plane([face(s, t, 5) for s, t in ((w / 2 - 2.4, h - 0.6), (w / 2 - 0.6, h - 0.6),
                                               (w / 2 - 0.6, h - 2.2))], "tel_white", 0.95, 0.4)
    return gw.finish(rig, hud=False)


# =============================================================== the radio
RADIO_PX_PER_CM = 0.34          # PMAPA0 is 32x28; the body is 32 wide and 28 high (MOD-SPEC 6.7)
RADIO_K = 1.9                   # the set exaggerated on its stool, so it reads at 1x
STOOL = (40.0, 40.0, 40.0, 3.0, 3.8)   # seat w, d, height, seat thickness, leg side
AERIAL = 18.0                   # cm (times RADIO_K): the telescopic aerial, half drawn out


def draw_tabouret(rig: Rig, c, X, Y, Z) -> Box:
    """The Soviet tabouret: a square pine seat on four square legs with
    stretchers. Returns the seat (things stand on its top)."""
    w, d, h, st, leg = STOOL
    c = np.asarray(c, np.float64)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = c + X * sx * (w / 2 - leg / 2 - 1.0) + Y * sy * (d / 2 - leg / 2 - 1.0)
            Box(p, X, Y, Z, leg, leg, h - st).draw(rig, "wood_ash", 0.46)
    for sy in (-1, 1):
        Box(c + Y * sy * (d / 2 - leg / 2 - 1.0) + Z * 12.0, X, Y, Z, w - 4.0, 1.8, 3.0).draw(rig, "wood_ash", 0.40)
    seat = Box(c + Z * (h - st), X, Y, Z, w, d, st)
    seat.draw(rig, "wood_ash", 0.56)
    return seat


VEF = (30.0, 9.0, 19.0)         # w, d, h of the VEF-206, cm


def draw_vef(rig: Rig, c, X, Y, Z, k: float) -> None:
    """VEF-206 (Riga, 1970s): a black case, a satin metal grille across two
    thirds of the front, the dial strip above it, two knobs, the strap
    handle and the telescopic aerial up."""
    w, d, h = (v * k for v in VEF)
    b = Box(np.asarray(c, np.float64), X, Y, Z, w, d, h)
    b.draw(rig, "rubber", 0.40)
    b.decal(rig, "front", -w / 2 + 1.0 * k, 1.2 * k, w / 2 - 9.0 * k, h - 5.0 * k, "button", 0.52)   # grille
    for t in np.arange(2.6 * k, h - 5.4 * k, 1.6 * k):
        b.decal(rig, "front", -w / 2 + 1.6 * k, t, w / 2 - 9.6 * k, t + 0.5 * k, "button", 0.30, lift=DECAL_LIFT * 2)
    b.decal(rig, "front", -w / 2 + 1.0 * k, h - 4.0 * k, w / 2 - 1.0 * k, h - 1.4 * k, "dial", 0.55)  # dial
    b.decal(rig, "front", -2.0 * k, h - 3.9 * k, -1.4 * k, h - 1.5 * k, "hull_red", 0.6, lift=DECAL_LIFT * 2)
    for t in (4.0 * k, 9.5 * k):
        disc(rig, b.pt("front", w / 2 - 4.6 * k, t, 0.4 * k), Y, 1.8 * k, "button", 0.62)
    # the strap handle: an arch over the top
    p0, p1 = b.pt("top", -w / 2 + 3.0 * k, 0.0, 0.0), b.pt("top", w / 2 - 3.0 * k, 0.0, 0.0)
    top = (p0 + p1) / 2 + Z * 4.0 * k
    for a, bb in ((p0, p0 + Z * 3.0 * k), (p0 + Z * 3.0 * k, top), (top, p1 + Z * 3.0 * k), (p1 + Z * 3.0 * k, p1)):
        rig.capsule(a, bb, 0.8 * k, 0.8 * k, "rubber", 0.30, 0.7)
    # the aerial, out of the right shoulder, leaning left
    a0 = b.pt("top", w / 2 - 1.5 * k, d / 4, 0.0)
    rig.capsule(a0, a0 + unit(Z - X * 0.45 + Y * 0.2) * AERIAL * k, 0.45 * k, 0.3 * k, "steel", 0.62, 0.85)


OKEAN = (37.0, 12.0, 24.0)


def draw_okean(rig: Rig, c, X, Y, Z, k: float) -> None:
    """Okean-209 (Grodno, 1970s): a black case with a brushed aluminium
    front, the wide dial window on the upper half with its colour bands,
    the speaker grille and knobs below, the chrome handle and the aerial."""
    w, d, h = (v * k for v in OKEAN)
    b = Box(np.asarray(c, np.float64), X, Y, Z, w, d, h)
    b.draw(rig, "rubber", 0.38)
    b.decal(rig, "front", -w / 2 + 0.8 * k, 0.8 * k, w / 2 - 0.8 * k, h - 0.8 * k, "button", 0.58)    # alu front
    b.decal(rig, "front", -w / 2 + 2.0 * k, h * 0.52, w / 2 - 2.0 * k, h - 2.0 * k, "rubber", 0.22,
            lift=DECAL_LIFT * 2)                                                                     # dial window
    for i, t in enumerate(np.linspace(h * 0.58, h - 3.4 * k, 4)):
        b.decal(rig, "front", -w / 2 + 3.0 * k, t, w / 2 - 3.0 * k, t + 0.6 * k,
                ("dial", "hull_red", "dial", "dial")[i], 0.55, lift=DECAL_LIFT * 3)
    b.decal(rig, "front", -w / 2 + 2.0 * k, 2.0 * k, w * 0.12, h * 0.44, "button", 0.36,
            lift=DECAL_LIFT * 2)                                                                     # grille
    for t in np.arange(2.8 * k, h * 0.44 - 0.6 * k, 1.5 * k):
        b.decal(rig, "front", -w / 2 + 2.4 * k, t, w * 0.12 - 0.4 * k, t + 0.5 * k, "rubber", 0.26,
                lift=DECAL_LIFT * 3)
    for s in (w * 0.24, w * 0.40):
        disc(rig, b.pt("front", s, h * 0.24, 0.5 * k), Y, 2.0 * k, "rubber", 0.30)
    p0, p1 = b.pt("top", -w / 2 + 4.0 * k, 0.0, 0.0), b.pt("top", w / 2 - 4.0 * k, 0.0, 0.0)
    for a, bb in ((p0, p0 + Z * 3.4 * k), (p0 + Z * 3.4 * k, p1 + Z * 3.4 * k), (p1 + Z * 3.4 * k, p1)):
        rig.capsule(a, bb, 0.8 * k, 0.8 * k, "button", 0.62, 0.85)
    a0 = b.pt("top", w / 2 - 1.5 * k, d / 4, 0.0)
    rig.capsule(a0, a0 + unit(Z - X * 0.45 + Y * 0.2) * AERIAL * k, 0.45 * k, 0.3 * k, "steel", 0.62, 0.85)


def render_radio(which: str) -> Frame:
    rig = rig_for(RADIO_PX_PER_CM)
    X, Y, Z = yawed(BOX_YAW * 0.6)
    c = centre() - Z * 30.0
    seat = draw_tabouret(rig, c, X, Y, Z)
    on = seat.pt("top", 0.0, 0.0, 0.0)
    (draw_vef if which == "A" else draw_okean)(rig, on, X, Y, Z, RADIO_K)
    return gw.finish(rig, hud=False)


# ================================================================ catalogue
@dataclass(frozen=True)
class Option:
    key: str
    title: str
    render: Callable[[], Frame]


@dataclass(frozen=True)
class Pickup:
    slug: str
    lump: str                   # four letters; frames below
    frames: tuple[str, ...]
    actor: str                  # the class that would show it
    placeholder: str            # the Freedoom sprite worn today (frame A)
    name: str
    options: tuple[Option, ...]
    recommended: str
    why: str
    proposed: bool = True       # False: the name is reserved in MOD-SPEC 6.3


PICKUPS: tuple[Pickup, ...] = (
    Pickup("clip", "SDCL", ("A",), "SD_Clip", "CLIP", "7,62x25 rounds, small",
           (Option("A", "PPSh-41 box magazine", render_clip_a),
            Option("B", "Paper packet, torn open", render_clip_b)),
           "B", "the brass tips read as ammunition from across a room; the magazine is a dark sliver on any floor"),
    Pickup("clipbox", "SDCB", ("A",), "SD_ClipBox", "AMMO", "7,62x25 rounds, box",
           (Option("A", "Green ammunition crate", render_clipbox_a),
            Option("B", "Opened zinc (цинк)", render_clipbox_b)),
           "B", "the zinc is the Soviet ammunition box, and the rows of brass say what is in it; the closed "
                "crate is a small cousin of the hangar's crates and could be mistaken for scenery"),
    Pickup("shell", "SDSL", ("A",), "SD_Shell", "SHEL", "12-gauge shells, small",
           (Option("A", "Four shells lying", render_shell_a),
            Option("B", "Four shells standing", render_shell_b)),
           "B", "standing, four red hulls on brass feet read at once; lying, the four merge into one red and "
                "yellow lump at 1x"),
    Pickup("shellbox", "SDSB", ("A",), "SD_ShellBox", "SBOX", "12-gauge shells, box",
           (Option("A", "Cardboard box, closed", render_shellbox_a),
            Option("B", "Box open, twenty shells", render_shellbox_b)),
           "B", "twenty brass heads over red hulls say shells; shut, the box is a brown brick with a label "
                "too small to read at 1x. B is still the weakest piece of the set: at 3x it can read as a "
                "red and yellow bar"),
    Pickup("rocket", "SDRA", ("A",), "SD_RocketAmmo", "ROCK", "PG-7V round, one",
           (Option("A", "Standing on its booster", render_rocket_a),
            Option("B", "Lying on its side", render_rocket_b)),
           "A", "standing, the cone is a silhouette nothing else in the base has; lying, it looks like the "
                "launcher's pickup without the launcher"),
    Pickup("rocketbox", "SDRB", ("A",), "SD_RocketBox", "BROK", "PG-7V rounds, crate",
           (Option("A", "Open crate, two rounds", render_rocketbox_a),
            Option("B", "Three rounds, stacked", render_rocketbox_b)),
           "A", "the crate says 'stores' and the two olive cones say what kind; the loose stack is busier"),
    Pickup("fuel", "SDFU", ("A",), "SD_Cell", "CELL", "Fuel, small",
           (Option("A", "10-litre jerrycan, red", render_fuel_a),
            Option("B", "Spare ROKS-3 tank", render_fuel_b)),
           "A", "a red jerrycan is fuel in any language; the tank is right for the ROKS-3 but at 1x it is an "
                "olive sausage"),
    Pickup("fuelpack", "SDFB", ("A",), "SD_CellPack", "CELP", "Fuel, large",
           (Option("A", "Two jerrycans", render_fuelpack_a),
            Option("B", "Two ROKS-3 tanks in their frame", render_fuelpack_b)),
           "A", "goes with the small pickup's choice: two of what the small one is one of"),
    Pickup("pass", "SDKB", PASS_FRAMES, "BlueCard (MAP03)", "BKEY", "The blue pass (пропуск)",
           (Option("A", "Closed booklet, gold star", render_pass_a),
            Option("B", "Laminated card, photo and stamp", render_pass_b)),
           "A", "the booklet is a 1977 пропуск at a glance and reads all cobalt; the card is a modern ID "
                "and its cream window halves the blue that tells the player which door it opens"),
    Pickup("radio", "SDRD", ("A",), "SD_Radio", "PMAP", "The radio on its tabouret",
           (Option("A", "VEF-206", lambda: render_radio("A")),
            Option("B", "Okean-209", lambda: render_radio("B"))),
           "B", "the Okean's wide dial with its colour lines is a radio's face even at 1x; the VEF's grille "
                "reads as a grey panel, which could be any box",
           proposed=False),
)
PICKUP = {p.slug: p for p in PICKUPS}


def render_option(p: Pickup, opt: Option, frame: str = "A") -> Frame:
    with pickup_materials():
        if p.slug == "pass":
            return opt.render(frame)
        return opt.render()


def lump_name(p: Pickup, frame: str) -> str:
    return f"{p.lump}{frame}0"


# ================================================================== scenes
SCENE_LIGHT = 144               # MAP01's dorm and corridors
SCENE_WALL = "SDCONC1"
SCENE_FLOOR = "SDFLR2"
SCENE_GAP = 14                  # px between the pickups on the strip
SCENE_FLOOR_H = 26              # rows of floor under the wall
SCENE_FLOOR_LINE = 13           # px into the floor band: where the pickups stand
SCENE_HEADROOM = 8              # px of wall above the tallest pickup


def placeholder(name: str) -> Frame | None:
    """The Freedoom sprite as the engine places it on the floor (its own
    offsets). Comparison only: nothing of it enters a sprite."""
    f = gw.freedoom_sprite(f"{name}A0")
    if f is None:
        return None
    lo, to = f.offsets()
    return Frame(f.rgba, f.mat, lo, to, False)


def scene(frames: list[Frame | None], light: int = SCENE_LIGHT, version: int = 1) -> np.ndarray:
    """The pickups in a row on SCENE_FLOOR before SCENE_WALL, each placed by
    its own grAb offsets, all in the same sector light."""
    real = [f for f in frames if f is not None]
    widths = [f.rgba.shape[1] if f is not None else 16 for f in frames]
    above = max([f.offsets()[1] for f in real] + [16])
    wall_h = above - SCENE_FLOOR_LINE + SCENE_HEADROOM
    wall_h = max(24, wall_h)
    W = sum(widths) + SCENE_GAP * (len(frames) + 1)
    wall = gw.texture(gw.TEX / f"{SCENE_WALL}.png")
    floor = gw.texture(gw.FLATS / f"{SCENE_FLOOR}.png")
    reps = (-(-wall_h // wall.shape[0]), -(-W // wall.shape[1]), 1)
    wl = np.tile(wall, reps)[wall.shape[0] * reps[0] - wall_h:, :W]
    fl = np.tile(floor, (3, -(-W // floor.shape[1]), 1))[:SCENE_FLOOR_H * 3, :W]
    fl = np.asarray(Image.fromarray(np.ascontiguousarray(fl), "RGB").resize((W, SCENE_FLOOR_H),
                                                                            Image.Resampling.NEAREST))
    canvas = np.concatenate([wl, fl], 0).copy()
    x = SCENE_GAP
    for f, wd in zip(frames, widths):
        if f is not None:
            gx, gy = f.offsets()
            x0 = x + wd // 2 - gx
            y0 = wall_h + SCENE_FLOOR_LINE - gy
            h, w = f.rgba.shape[:2]
            a = f.rgba[..., 3] > 0
            ys, xs = np.nonzero(a)
            cy, cx = ys + y0, xs + x0
            ok = (cy >= 0) & (cy < canvas.shape[0]) & (cx >= 0) & (cx < W)
            canvas[cy[ok], cx[ok]] = f.rgba[ys[ok], xs[ok], :3]
        x += wd + SCENE_GAP
    return light_scene(canvas, light, version)


def light_scene(rgb: np.ndarray, light: int, version: int = 1) -> np.ndarray:
    """gen_weapon's sector-light stand-in (RGB x L/224), re-quantised to
    palette `version`: a v2 sprite (the pass) quantised to v1 would turn
    from cobalt to grey on the sheet. NOT VERIFIED against GZDoom."""
    if version == 1:
        return gw.light_rgb(rgb, light)
    f = min(1.0, light / gw.LIGHT_FULL)
    out = np.clip(rgb.astype(np.float64) * f, 0, 255).astype(np.uint8)
    pal = Image.new("P", (1, 1))
    pal.putpalette([c for rgb_ in palette_mod.colours(version) for c in rgb_])
    q = Image.fromarray(out, "RGB").quantize(palette=pal, dither=Image.Dither.NONE)
    return np.asarray(q.convert("RGB"))


def floor_luma(light: int = SCENE_LIGHT) -> float:
    floor = gw.texture(gw.FLATS / f"{SCENE_FLOOR}.png")
    return float(luma(gw.light_rgb(floor, light)).mean())


def metrics(f: Frame, floor_l: float) -> dict:
    a = f.rgba[..., 3] > 0
    lum = luma(f.rgba[..., :3])[a]
    return {"size": [int(f.rgba.shape[1]), int(f.rgba.shape[0])], "offsets": [int(v) for v in f.offsets()],
            "luma": round(float(lum.mean()), 1), "luma_p90": round(float(np.percentile(lum, 90)), 1),
            "contrast_on_floor": round(float(abs(lum.mean() - floor_l)), 1)}


# ================================================================== build
INTRO = (
    "Debt <b>T8</b> (MOD-SPEC 6.3): the ammunition still wears Freedoom's flat pickups (&ldquo;the ammunition has "
    "no three-dimensional look&rdquo;), MAP03's blue key is still Freedoom's keycard (MAP03-metro.md §5 asks for a "
    "1977 пропуск), and the radio still wears the computer map's picture (<b>T23</b>, <code>SDRD</code> A). "
    "Two options per object, drawn exactly as the approved weapon pickups (D48): small 3D scenes on "
    "<code>gen_weapon</code>'s rig, the same pitch, key light, bands and outline, boxes turned so the top and two "
    "sides show. Each row: the Freedoom placeholder, option A, option B, standing by their own offsets on "
    "<code>SDFLR2</code> before <code>SDCONC1</code> at sector light 144 (MAP01's dorm), first at 1x and then the "
    "same strip at 3x. Built by <code>tools/art/gen_pickups.py</code>. Draft: nothing in <code>assets/</code>.")


def build(stamp: str, out_dir: Path = OUT_DIR, preview_dir: Path = PREVIEW_DIR) -> tuple[Path, dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet_dir = out_dir / "sheet"
    floor_l = floor_luma()
    all_metrics: dict = {"floor_luma": round(floor_l, 1), "light": SCENE_LIGHT, "pickups": {}}
    cards = []
    lineup: list[Frame | None] = []
    for p in PICKUPS:
        ph = placeholder(p.placeholder)
        rendered: dict[str, dict[str, Frame]] = {}
        pm: dict = {"lump": p.lump, "actor": p.actor, "placeholder": f"{p.placeholder}A0",
                    "recommended": p.recommended, "proposed_name": p.proposed, "options": {}}
        for opt in p.options:
            rendered[opt.key] = {}
            for fr in p.frames:
                f = render_option(p, opt, fr)
                rendered[opt.key][fr] = f
                gw.save_sprite(f, out_dir / p.slug / opt.key / f"{lump_name(p, fr)}.png")
            pm["options"][opt.key] = {fr: metrics(f, floor_l) for fr, f in rendered[opt.key].items()}
        if ph is not None:
            pm["placeholder_size"] = [int(ph.rgba.shape[1]), int(ph.rgba.shape[0])]
        all_metrics["pickups"][p.slug] = pm
        strips = [ph] + [rendered[o.key]["A"] for o in p.options]
        if len(p.frames) > 1:
            strips += [rendered[o.key][fr] for o in p.options for fr in p.frames[1:]]
        img = scene(strips, version=2 if p.slug == PASS_SLUG else 1)
        path = sheet_dir / f"{p.slug}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(img, "RGB").save(path, optimize=True)
        cards.append(card_html(p, path, img.shape[1::-1], pm))
        lineup.append(rendered[p.recommended]["A"])
    line_img = scene(lineup, version=2)
    line_path = sheet_dir / "lineup_recommended.png"
    Image.fromarray(line_img, "RGB").save(line_path, optimize=True)
    ph_line = scene([placeholder(p.placeholder) for p in PICKUPS], version=2)
    ph_path = sheet_dir / "lineup_freedoom.png"
    Image.fromarray(ph_line, "RGB").save(ph_path, optimize=True)
    (out_dir / "metrics.json").write_text(json.dumps(all_metrics, indent=1, ensure_ascii=False), encoding="utf-8")

    lineup_html = (
        '<div class="row">'
        + sheetlib.view("Freedoom today, 1x", ph_path, 1, ph_line.shape[1::-1])
        + sheetlib.view("Recommended set, 1x", line_path, 1, line_img.shape[1::-1]) + "</div>"
        + '<div class="row">'
        + sheetlib.view("Freedoom today, 3x", ph_path, 3, ph_line.shape[1::-1]) + "</div>"
        + '<div class="row">'
        + sheetlib.view("Recommended set, 3x", line_path, 3, line_img.shape[1::-1]) + "</div>")
    ask = (
        '<div class="ask"><b>For the CEO</b><ol>'
        "<li>Choose A or B per object (the recommendation is marked on each card), or ask for a redo.</li>"
        "<li>The pass in palette v2 (cobalt, D45), as the Legion is: yes or no. In v1 the only blue is "
        "<code>steel_blue</code>, a grey.</li>"
        "<li>The radio on a tabouret: the actor is 32 wide and 28 high, a waist-high body, so the set stands on "
        "a stool rather than being drawn a metre wide. Yes, or another piece of furniture.</li>"
        "<li>On approval: the mod-engineer reserves the names in MOD-SPEC 6.3 (only <code>SDRD</code> is reserved "
        "today), changes each <code>Spawn</code> state in <code>zscript/sd/ammo.zs</code> and "
        "<code>radio.zs</code>, and gives MAP03's pass a <code>BlueCard</code> subclass with frames A and B; the "
        "PM's engine pass first. The backpack (<code>BPAK</code>) is not in this sweep.</li></ol></div>")
    sections = [
        ("The set together", "Left: every placeholder of this sweep as Freedoom draws it. Right: the recommended "
         "option of each, in the order of the cards below (7,62 small and box, shells small and box, PG-7V one "
         "and crate, fuel small and large, the pass, the radio).", lineup_html),
        ("The objects", "", '<div class="grid">' + "".join(cards) + "</div>"),
        ("Decisions", "", ask),
    ]
    footer = ("Origin: (a) procedural, <code>tools/art/gen_pickups.py</code> on <code>gen_weapon</code>'s rig, "
              "deterministic, no seed, no font. Freedoom placeholders are read from <code>iwads/freedoom2.wad</code> "
              "0.13.0 (BSD-3) for comparison only. Sector light is gen_weapon's stand-in (RGB x L/224, "
              "re-quantised), NOT VERIFIED against GZDoom.")
    preview = preview_dir / f"{stamp}_{SHEET_SLUG}.html"
    sheetlib.write_sheet(preview, lang="en", title="Floor pickups: ammunition, the blue pass, the radio (T8, T23)",
                         subtitle="Sweep, two options per object, against the Freedoom placeholders",
                         intro=INTRO, sections=sections, footer=footer)
    return preview, all_metrics


def card_html(p: Pickup, path: Path, size: tuple[int, int], pm: dict) -> str:
    opts = " &middot; ".join(f"<b>{o.key}</b> {html.escape(o.title)}" for o in p.options)
    order = "Freedoom, A, B" + (", then A and B in frame B (the blink)" if len(p.frames) > 1 else "")
    rows = []
    for o in p.options:
        for fr, m in pm["options"][o.key].items():
            rows.append([f"{o.key} {lump_name(p, fr)}", f"{m['size'][0]}x{m['size'][1]}",
                         f"{m['offsets'][0]}, {m['offsets'][1]}", m["luma"], m["contrast_on_floor"]])
    ph = pm.get("placeholder_size")
    name_note = ("reserved in MOD-SPEC 6.3" if not p.proposed
                 else "proposed (MOD-SPEC 6.3 reserves it on approval)")
    return (
        f'<div class="card rec"><span class="tag">recommended: {p.recommended}</span>'
        f"<h3>{p.lump} &mdash; {html.escape(p.name)}</h3>"
        f'<p class="desc">{opts}.<br><b>Recommendation {p.recommended}:</b> {html.escape(p.why)}.</p>'
        f'<div class="row">{sheetlib.view(f"1x: {order}", path, 1, size)}</div>'
        f'<div class="row">{sheetlib.view("3x", path, 3, size)}</div>'
        + sheetlib.table(["option, lump", "size", "grAb", "luma", "vs floor"], rows)
        + f"<dl><dt>actor</dt><dd>{html.escape(p.actor)}</dd>"
        f"<dt>placeholder</dt><dd>{p.placeholder}A0" + (f" ({ph[0]}x{ph[1]})" if ph else " (IWAD absent)")
        + f"</dd><dt>name</dt><dd>{name_note}</dd></dl></div>")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stamp", default=dt.datetime.now().strftime("%Y-%m-%d_%H%M"))
    args = ap.parse_args(argv)
    preview, m = build(args.stamp)
    print(f"wrote {preview}")
    for slug, pm in m["pickups"].items():
        sizes = ", ".join(f"{k} {v['A']['size'][0]}x{v['A']['size'][1]}" for k, v in pm["options"].items())
        print(f"  {pm['lump']:5s} {slug:10s} {sizes}  (Freedoom {pm.get('placeholder_size')})")


if __name__ == "__main__":
    main()
